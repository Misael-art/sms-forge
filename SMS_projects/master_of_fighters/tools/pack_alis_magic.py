"""Pack the guardians' storyboard and transparent spell tiles over the actual Palma arena."""
import argparse
import json
import re
import struct
import subprocess
from alis_guardians_panels import pack_scenes
from pathlib import Path
from PIL import Image, ImageDraw
from make_duel_scene02_assets import PROJECT, array, c_values, digest, pixels, planar
from pack_alis_scenes import native, encode
from stage_alis_postures import rgb

ART = PROJECT/'data/source_art/scenes/alis_guardioes'
PAGE = 16384
NEAR = Image.Resampling.NEAREST


def stage_patterns(folder, fighters):
    defs = {k:int(v) for k,v in re.findall(r'#define MOF_(\w+) (\d+)u', (folder/'alis_pages.h').read_text())}
    data = (folder/'panels.bin').read_bytes()[-PAGE:]
    return decode_stage(data,defs,fighters)


def decode_stage(data,defs,fighters):
    vram = bytearray(448*32)
    base = bytes(c_values((fighters/'duel_mirror_assets.h').read_text(),'mof_duel_bg_stage'))
    vram[8192:8192+len(base)] = base
    offset = defs['ARENA_FIRST']*32
    size = defs['ARENA_BYTES']
    vram[offset:offset+size] = data[:size]
    for i in range(defs['ARENA_SPARE_COUNT']):
        slot, index = divmod(i, defs['ARENA_SPARE_WIDTH'])
        dst = (slot*32 + defs['ARENA_SPARE_FIRST'] + index)*32
        src = defs['ARENA_SPARE_ADDR']-0x8000 + i*32
        vram[dst:dst+32] = data[src:src+32]
    tilemap = struct.unpack_from('<768H',data,size)
    ids = list(dict.fromkeys(tilemap))
    pal = defs['PORT_PALETTE']-0x8000
    def oriented(entry):
        address = (entry & 0x1ff)*32
        tile = Image.frombytes('L',(8,8),bytes(pixels(vram[address:address+32])))
        if entry & 0x200:
            tile = tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if entry & 0x400:
            tile = tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        return tile.tobytes()
    return ids, [ids.index(t) for t in tilemap], [oriented(t) for t in ids], list(data[pal:pal+16])


def choreographed_effect(index):
    """Original effects drawn on the target pixel grid in the arena's colors."""
    if index == 0:
        size = (16, 16)
        shapes = (
            (3, [(0,3),(7,6),(4,1),(10,4),(14,5),(15,8),(13,11),(8,13),(2,15),(5,10),(0,11),(4,8)]),
            (11, [(3,5),(8,7),(8,3),(13,5),(15,8),(12,11),(6,12),(8,9),(2,10),(6,8)]),
            (27, [(7,7),(10,7),(10,5),(13,6),(14,8),(12,10),(8,10),(10,8)]),
            (63, [(10,7),(12,6),(14,8),(12,9),(10,9),(11,8)]),
        )
    elif index in (1, 9, 12):
        size = (24, 32) if index == 12 else (16, 24)
        height = 23
        edge, light = (11, 27) if index == 9 else (32, 60)
        shapes = (
            (edge, [(2,0),(10,3),(14,8),(15,height//2),(13,height-5),(8,height-2),(1,height),
                    (6,height-5),(10,height//2),(10,7),(6,3)]),
            (light, [(5,1),(11,4),(13,8),(14,height//2),(12,height-5),(6,height-2),
                     (9,height-6),(11,height//2),(11,7)]),
            (63, [(9,3),(12,6),(13,height//2),(11,height-6),(10,height-5),(12,height//2),(11,6)]),
        )
    elif index in (7, 10):
        size = (16, 8) if index == 7 else (8, 8)
        shapes = ((27, [(3,0),(4,2),(7,3),(4,4),(3,7),(2,4),(0,3),(2,2)]),
                  (63, [(3,2),(4,3),(3,4),(2,3)]))
        if index == 7:
            shapes += ((11, [(12,0),(13,2),(15,2),(13,4),(12,6),(11,4),(9,3),(11,2)]),
                       (63, [(12,2),(13,3),(12,4),(11,3)]))
    elif index == 11:
        size = (16, 8)
        shapes = ((21, [(0,7),(1,5),(4,4),(5,1),(8,3),(10,2),(11,4),(15,5),(15,7)]),
                  (42, [(2,6),(4,5),(6,2),(8,4),(11,4),(14,6),(10,5),(7,6)]))
    else:
        return None
    image = Image.new('RGBA', size)
    art = ImageDraw.Draw(image)
    for color, points in shapes:
        if index == 12:
            points=[(round(x*23/15),round(y*31/23)) for x,y in points]
        art.polygon(points, fill=(*rgb(color),255))
    return image


def glyph_stamps(palette, choreography=False, combat=False):
    glyphs=Image.open(ART/'magias.png').convert('RGBA')
    for i in range(13 if combat else 11 if choreography else 9):
        full=choreographed_effect(i) if choreography else None
        if full is None:
            x,y=i%3,i//3
            cel=glyphs.crop((x*glyphs.width//3,y*glyphs.height//3,(x+1)*glyphs.width//3,(y+1)*glyphs.height//3))
            alpha=cel.getchannel('A').point(lambda a:255 if a>=170 else 0)
            cel.putalpha(alpha);cel=cel.crop(alpha.getbbox())
            size=(24,16) if choreography and i==5 else (16,16) if i in (3,4,5) else (8,8)
            cel.thumbnail(size,Image.Resampling.LANCZOS)
            full=Image.new('RGBA',size);full.paste(cel,((full.width-cel.width)//2,(full.height-cel.height)//2))
        for flip in (False,True):
            oriented=full.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else full
            ink=native(oriented,oriented.size,palette)
            for yy in range(0,full.height,8):
                for xx in range(0,full.width,8):
                    bounds=xx,yy,xx+8,yy+8
                    alpha=oriented.getchannel('A').crop(bounds).tobytes()
                    color=ink.crop(bounds).tobytes()
                    yield i, flip, yy//8, alpha, color


def pack(base,out,choreography=False,combat=False):
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((base/'chapter.json').read_text())
    tc=manifest['toolchain']
    fighters=PROJECT/tc['include_dirs'][0]
    ids,map_index,backgrounds,palette=stage_patterns(base,fighters)
    if choreography:
        # The revised effects fit within rows 3..17. Omit the other arena
        # patterns from every pre-composited effect, including unused HUD tiles.
        first_row=8 if combat else 3
        used=list(dict.fromkeys(map_index[first_row*32:18*32]))
        index={old:new for new,old in enumerate(used)}
        ids=[ids[i] for i in used];backgrounds=[backgrounds[i] for i in used]
        map_index=[index.get(i,0) for i in map_index]
    magic_bank=tc['defines']['MOF_RULE_BANK']+1
    first=magic_bank+1
    voice=out/'algol.wav'
    subprocess.run(['espeak','-v','pt-br+f3','-s','160','-p','67','-w',str(voice),'Algol!'],check=True)
    pcm=subprocess.check_output(['ffmpeg','-v','error','-i',str(voice),'-ac','1','-ar','6000','-f','s16le','-'])
    samples=[a for a, in struct.iter_unpack('<h',pcm)]
    peak=max(map(abs,samples))
    active=[i for i,v in enumerate(samples) if abs(v)>peak//100]
    levels=[10**(-n/10) for n in range(15)]+[0]
    voice_pcm=bytes(0x90|min(range(16),key=lambda n:abs(levels[n]-(0.5+v/(2*peak)))) for v in samples[active[0]:active[-1]+1])
    banks,meta,voice_address,cut_tiles,cut_xy=pack_scenes(ART,out,voice_pcm,repair_mouth=choreography)
    cine='static const unsigned int magic_patch[][2] = {'+','.join('{%d,%d}'%tuple(r[:2]) for r in meta)+'};'
    cine+='\n'+array('magic_cycle',[v for row in meta for v in row[2:]])
    cine+='\n'+array('magic_cut_xy',cut_xy)
    header=[array('magic_map',map_index),
            'static const unsigned int magic_restore[] = {'+','.join(map(str,ids))+'};']
    locations=[]
    sprite_ids=[]
    offset=PAGE
    last=None
    strips={}
    if choreography:
        banks.extend(b'\xff'*(-len(banks)%PAGE))
    for glyph,flip,_,alpha,color in glyph_stamps(palette,choreography,combat):
        if (glyph,flip)!=last:
            sprite_ids.append(len(locations))
            last=(glyph,flip)
        strip=b''.join(planar([c if a>=100 else b for c,a,b in zip(color,alpha,tile)]) for tile in backgrounds)
        if choreography and strip in strips:
            locations.append(strips[strip])
            continue
        if choreography:
            bank,offset=divmod(len(banks),PAGE)
        elif offset+len(strip)>PAGE:
            banks.extend(b'\xff'*(-len(banks)%PAGE))
            offset=0
        locations.append((first+(bank if choreography else len(banks)//PAGE),0x8000+offset))
        strips[strip]=locations[-1]
        banks.extend(strip);offset+=len(strip)
    banks.extend(b'\xff'*(-len(banks)%PAGE))
    if first+len(banks)//PAGE>64: raise ValueError('Spell art exceeds the cartridge')
    header.extend([array('magic_glyph',sprite_ids),array('magic_bank',[b for b,_ in locations]),
                   'static const unsigned int magic_base[] = {'+','.join(str(a) for _,a in locations)+'};'])
    hud_source=bytes(c_values((fighters/'duel_mirror_assets.h').read_text(),'mof_duel_bg_stage'))
    full_bar=pixels(hud_source[5*32:6*32]);empty=pixels(hud_source[:32])
    red=palette.index(3)
    bars=b''.join(planar([red if v!=empty[i] and i%8 < n else empty[i] for i,v in enumerate(full_bar)]) for n in range(1,9))
    # Share one copy of these immutable patterns from the free tail of the
    # last reaction bank. The fixed 32 KiB also contain the duel renderer.
    tail=8*PAGE-len(cut_tiles)-len(bars)
    assert banks[tail:8*PAGE]==b'\xff'*(len(cut_tiles)+len(bars))
    banks[tail:8*PAGE]=cut_tiles+bars
    cine+=f'\n#define MAGIC_PATTERN_BANK {first+7}u\n#define MAGIC_CUT_ADDR {0x8000+tail%PAGE}u\n#define MAGIC_CUT_BYTES {len(cut_tiles)}u\n#define MAGIC_BARS_ADDR {0xC000-len(bars)}u\n'
    (out/'magic_cine.h').write_text(cine+
        f'\n#define MAGIC_VOICE_ADDR {voice_address}u\n#define MAGIC_VOICE_LEN {len(voice_pcm)}u\n')
    # Bind spell acting to the named poses of this fighter build. Avoid
    # linking a second copy of the renderer's large packet tables.
    pose_defs=re.findall(r'^#define MOF_MIRROR_\w+ \d+u$',(fighters/'duel_mirror_assets.h').read_text(),re.M)
    if choreography:
        (out/'magic_poses.h').write_text('\n'.join(pose_defs)+'\n')
    (out/'magic_art.h').write_text('\n'.join(pose_defs+header)+'\n')
    (out/'magic.bin').write_bytes(banks)
    tc['include_dirs'].append(out.relative_to(PROJECT).as_posix())
    tc['defines'].update(MOF_DUEL_SCENE_EFFECTS=1,MOF_ALIS_MAGIC=1,MOF_MAGIC_BANK=magic_bank,MOF_GUARDIANS_PAGE=first)
    if choreography:
        tc['defines']['MOF_ALIS_CHOREOGRAPHY']=1
    if combat:
        tc['defines']['MOF_ALIS_COMBAT']=1
    tc['mapper_code_banks']['SMSBANK_MAGIC']=magic_bank
    tc['makesms_extra']+=['-mbank',f'{(out/"magic.bin").relative_to(PROJECT)}:0:{len(banks)//PAGE}:{first}']
    (out/'chapter.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(len(ids),'background patterns,',len(locations),'effect tiles,',len(banks)//PAGE,'art banks',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('panels',type=Path);parser.add_argument('out',type=Path)
    parser.add_argument('--choreography',action='store_true')
    parser.add_argument('--combat',action='store_true')
    args=parser.parse_args()
    if args.combat and not args.choreography:
        parser.error('--combat requires --choreography')
    pack(args.panels.resolve(),args.out.resolve(),args.choreography,args.combat)
