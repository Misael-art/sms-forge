"""Pack the guardians' storyboard and transparent spell tiles over the actual Palma arena."""
import argparse
import json
import re
import struct
import subprocess
from alis_guardians_panels import pack_scenes
from pathlib import Path
from PIL import Image
from make_duel_scene02_assets import PROJECT, array, c_values, digest, pixels, planar
from pack_alis_scenes import native, encode
from stage_alis_postures import rgb

ART = PROJECT/'data/source_art/scenes/alis_guardioes'
PAGE = 16384
NEAR = Image.Resampling.NEAREST


def stage_patterns(folder, fighters):
    defs = {k:int(v) for k,v in re.findall(r'#define MOF_(\w+) (\d+)u', (folder/'alis_pages.h').read_text())}
    data = (folder/'panels.bin').read_bytes()[-PAGE:]
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


def pack(base,out):
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((base/'chapter.json').read_text())
    tc=manifest['toolchain']
    fighters=PROJECT/tc['include_dirs'][0]
    ids,map_index,backgrounds,palette=stage_patterns(base,fighters)
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
    banks,meta,voice_address,cut_tiles,cut_xy=pack_scenes(ART,out,voice_pcm)
    cine='static const unsigned int magic_patch[][2] = {'+','.join('{%d,%d}'%tuple(r[:2]) for r in meta)+'};'
    cine+='\n'+array('magic_cycle',[v for row in meta for v in row[2:]])
    cine+='\n'+array('magic_cut_xy',cut_xy)
    header=[array('magic_map',map_index),
            'static const unsigned int magic_restore[] = {'+','.join(map(str,ids))+'};']
    glyphs=Image.open(ART/'magias.png').convert('RGBA')
    locations=[]
    sprite_ids=[]
    offset=PAGE
    for i in range(9):
        x,y=i%3,i//3
        cel=glyphs.crop((x*glyphs.width//3,y*glyphs.height//3,(x+1)*glyphs.width//3,(y+1)*glyphs.height//3))
        alpha=cel.getchannel('A').point(lambda a:255 if a>=170 else 0)
        cel.putalpha(alpha);cel=cel.crop(alpha.getbbox())
        side=16 if i in (3,4,5) else 8
        cel.thumbnail((side,side),Image.Resampling.LANCZOS)
        full=Image.new('RGBA',(side,side));full.paste(cel,((side-cel.width)//2,(side-cel.height)//2))
        for flip in (False,True):
            sprite_ids.append(len(locations))
            oriented=full.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else full
            ink=native(oriented,oriented.size,palette)
            for yy in range(0,side,8):
                for xx in range(0,side,8):
                    bounds=xx,yy,xx+8,yy+8
                    alpha=oriented.getchannel('A').crop(bounds).tobytes()
                    color=ink.crop(bounds).tobytes()
                    strip=b''.join(planar([c if a>=100 else b for c,a,b in zip(color,alpha,tile)]) for tile in backgrounds)
                    if offset+len(strip)>PAGE:
                        banks.extend(b'\xff'*(-len(banks)%PAGE))
                        offset=0
                    locations.append((first+len(banks)//PAGE,0x8000+offset))
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
    (out/'magic_art.h').write_text('\n'.join(pose_defs+header)+'\n')
    (out/'magic.bin').write_bytes(banks)
    tc['include_dirs'].append(out.relative_to(PROJECT).as_posix())
    tc['defines'].update(MOF_DUEL_SCENE_EFFECTS=1,MOF_ALIS_MAGIC=1,MOF_MAGIC_BANK=magic_bank,MOF_GUARDIANS_PAGE=first)
    tc['mapper_code_banks']['SMSBANK_MAGIC']=magic_bank
    tc['makesms_extra']+=['-mbank',f'{(out/"magic.bin").relative_to(PROJECT)}:0:{len(banks)//PAGE}:{first}']
    (out/'chapter.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(len(ids),'background patterns,',len(locations),'effect tiles,',len(banks)//PAGE,'art banks',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('panels',type=Path);parser.add_argument('out',type=Path)
    args=parser.parse_args();pack(args.panels.resolve(),args.out.resolve())
