"""Separate authored exposures and generate tile-map deltas and dedicated CRAM tracks."""
import json
import hashlib
import struct
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
from make_duel_scene02_assets import planar
from pack_alis_scenes import native
from stage_alis_postures import rgb

NEAR=Image.Resampling.NEAREST
NAVY=(0,0,85)
SIZE=(224,112)
NAMES=('alis','odin','noah','laerma','myau','laconiana','reacao_alis','reacao_hayato')
# These rectangular regions are measured on the supplied artwork at SMS resolution.
# Copy local ink to an alpha layer. Both exposures share the same anchor.
def piece(canvas,box,background):
    part=canvas.crop(box).convert('RGBA')
    mask=Image.new('L',part.size)
    mask.putdata([255 if c[:3]!=background else 0 for c in part.getdata()])
    part.putalpha(mask)
    return part

def stamp(canvas,part,xy):
    canvas.paste(part,xy,part)

def atlas_piece(atlas,box):
    im=atlas.crop(box)
    mask=im.getchannel('A').point(lambda n:255 if n>=170 else 0)
    im.putalpha(mask)
    return im.crop(mask.getbbox())

def palette_view(frame,colors):
    im=frame.convert('P')
    im.putpalette(bytes(v for c in colors for v in rgb(c)).ljust(768,b'\0'))
    return im

def make_layers(art,dest):
    dest.mkdir(parents=True,exist_ok=True)
    sheet=Image.open(art/'guardioes.png').convert('RGB')
    atlas=Image.open(art/'pecas.png').convert('RGBA')
    receipt=json.loads((art/'lineage.json').read_text())['revisao_visual_da_ficha']
    panel_hashes={row['arquivo']:row['sha256'] for row in receipt['arquivos']}
    # Use reference-image crop boundaries measured from the six original ink cells.
    panels=[]
    for n in range(6):
        if n in (0,1,5):
            # The sheet supplies an individual actor on a 256x192 proof
            # canvas. Only the original 224x112 viewport goes into the bank.
            path=art/'revisao_ficha'/(NAMES[n]+'.png')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=panel_hashes[path.relative_to(art).as_posix()]:
                raise ValueError(f'Artwork differs from cinematic receipt: {path}')
            with Image.open(path) as frame:
                if frame.size!=(256,192):
                    raise ValueError(f'Unexpected cinematic canvas: {path}')
                panels.append(frame.convert('RGB').crop((16,40,240,152)))
        else:
            col,row=n%2,n//2
            im=sheet.crop((col*sheet.width//2+2,row*sheet.height//3+2,
                           (col+1)*sheet.width//2-2,(row+1)*sheet.height//3-2))
            codes=native(im,SIZE,list(range(64)))
            panels.append(palette_view(codes,list(range(64))).convert('RGB'))
    parts={k:atlas_piece(atlas,b) for k,b in {
        'reacao_alis':(0,0,508,550),'reacao_hayato':(545,0,1006,550),
        'corte':(1032,0,1536,544),'asas':(18,654,575,964),
        'clarão':(624,650,966,903),'brilho':(1215,620,1418,772)}.items()}
    for key,im in parts.items(): im.save(dest/(key+'.png'))
    panels.extend(Image.new('RGB',SIZE,NAVY) for _ in range(2))
    scenes=[]
    for n,base in enumerate(panels):
        folder=dest/NAMES[n];folder.mkdir(exist_ok=True)
        variants=[base.copy(),base.copy()]
        if n in (0,2,3):
            # Mouth, separate hair tips or the Laerma fruit: vary only the cutouts.
            regions=(((111,51,118,58), (11,11,26,16),(4,35,17,40)) if n==0 else
                     ((70,37,77,45),(9,53,27,62)) if n==2 else ((84,65,101,77),(102,57,113,64)))
            for j,b in enumerate(regions):
                chip=base.crop(b)
                chip.save(folder/f'detalhe-{j}.png')
                if n in (0,2) and j==0:
                    fill=chip.getpixel((chip.width-1,chip.height-1))
                    ImageDraw.Draw(variants[1]).rectangle((b[0],b[1],b[2]-1,b[3]-1),fill=fill)
                    variants[1].paste(chip.resize((chip.width,max(2,chip.height//2)),NEAR),(b[0],b[1]+1))
                else:
                    variants[1].paste(chip.transpose(Image.Transpose.FLIP_TOP_BOTTOM) if n==3 else
                                      chip.resize((chip.width,max(2,chip.height-2)),NEAR),(b[0],b[1]+1))
            if n==0:
                glint=parts['brilho'].resize((9,9),NEAR)
                stamp(variants[1],glint,(165,19))
        elif n==1:
            # Keep exposure zero faithful to the approved gun and laser.
            # Change only the light beyond the muzzle for exposure one.
            beam_box=(166,0,224,72)
            beam=piece(base,beam_box,NAVY)
            base=base.copy()
            base.paste(NAVY,beam_box)
            variants=[base.copy(),base.copy()]
            stamp(variants[0],beam,(166,0))
            stamp(variants[1],beam.resize((48,50),NEAR),(166,12))
        elif n==4:
            # Separate white flight feathers from the gold torso by material and position.
            wing=Image.new('RGBA',SIZE)
            region=Image.new('1',SIZE)
            contour=ImageDraw.Draw(region)
            contour.polygon([(0,0),(99,0),(108,18),(112,31),(122,43),(115,55),(100,62),(80,58),(57,50),(31,40),(0,26)],fill=1)
            contour.polygon([(144,51),(158,41),(184,24),(222,14),(223,42),(185,61),(167,73),(148,74)],fill=1)
            for y in range(76):
                for x in range(224):
                    r,g,b=base.getpixel((x,y))
                    if region.getpixel((x,y)) and b>=85 and b>=r and (r or g):
                        wing.putpixel((x,y),(r,g,b,255))
            wing.save(folder/'asas-abertas.png')
            base.paste(NAVY,(0,0),wing.getchannel('A'))
            variants=[base.copy(),base.copy()]
            stamp(variants[0],wing,(0,0))
            folded=parts['asas'].resize((168,67),NEAR)
            stamp(variants[1],folded,(33,28))
            # Body and head must stay in front of the shoulder joints.
            body=piece(base,(0,0,*SIZE),NAVY)
            silhouette=Image.new('L',SIZE)
            ImageDraw.Draw(silhouette).polygon([(2,79),(4,56),(22,50),(52,56),(73,58),(100,50),(124,43),
                (141,34),(114,10),(136,15),(137,6),(161,25),(170,35),(166,49),(154,53),(147,64),
                (158,69),(170,78),(165,92),(150,87),(143,82),(140,89),(116,84),(110,76),(84,78),
                (66,98),(51,108),(36,110),(34,104),(48,81),(72,68),(47,69),(20,63)],fill=255)
            body.putalpha(ImageChops.darker(body.getchannel('A'),silhouette))
            stamp(variants[1],body,(0,0))
        elif n==5:
            # The Laconian drawing is already the solo attacker. The target
            # page and travelling SAT cut are selected later by the runtime.
            stamp(variants[1],parts['brilho'].resize((8,8),NEAR),(138,3))
        else:
            actor=parts[NAMES[n]].copy()
            actor.thumbnail((134,110),NEAR)
            # Both existing identities use the same reaction contract and index range.
            shade=native(actor,actor.size,[16,0,17,38,59])
            toned=palette_view(shade,[16,0,17,38,59]).convert('RGBA')
            toned.putalpha(actor.getchannel('A'))
            stamp(base,toned,(120-toned.width//2,112-toned.height))
            variants=[base.copy(),base.copy()]
        # Ship a clean plate and two registered RGBA overlays. Recomposition
        # from disk has to reproduce each RGB exposure exactly.
        union=ImageChops.lighter(*(ImageChops.difference(im,base).convert('L') for im in variants))
        union=union.point(lambda v:255 if v else 0)
        plate=base.copy()
        plate.paste(NAVY,(0,0,*SIZE),union)
        plate.save(folder/'base.png')
        for i,im in enumerate(variants):
            overlay=im.convert('RGBA');overlay.putalpha(union)
            overlay.save(folder/f'camada-{i}.png')
            composed=plate.copy();stamp(composed,overlay,(0,0))
            assert ImageChops.difference(composed,im).getbbox() is None
            im.save(folder/f'exposicao-{i}.png')
        scenes.append(variants)
    return scenes,parts['corte']

def palette_frames(n,variants):
    # Allocate three exclusive slots to the lightning, speed streaks or laser.
    tracks={1:[35,59,63],2:[34,15,63],4:[32,52,63]}
    cycle=tracks.get(n,[])
    masks=[]
    all_codes=[native(im,SIZE,list(range(64))) for im in variants]
    hist={}
    for codes in all_codes:
        mask=bytearray(224*112)
        for k,c in enumerate(codes.getdata()):
            x,y=k%224,k//224
            r,g,b=rgb(c)
            zone=((n==2 and x>88 and (y < 44 or x>170)) or
                  (n==4 and (y>72 or (x>176 and y<14))) or (n==1 and x>=160))
            if zone and c not in (0,16) and ((n==2 and (r>=170 or b>=170)) or
                        (n==4 and b>=170 and g>=85) or (n==1 and c in cycle)):
                mask[k]=1
            else:hist[c]=hist.get(c,0)+1
        masks.append(mask)
    colors=[0]+[c for c in sorted(hist,key=hist.get,reverse=True) if c!=0][:15-len(cycle)]
    normal=len(colors);colors=(colors+[0]*16)[:16-len(cycle)]+cycle
    frames=[]
    for im,mask in zip(variants,masks):
        raster=bytearray(native(im,SIZE,colors[:normal]).tobytes())
        if cycle:
            fx=native(im,SIZE,cycle).tobytes()
            for k,tag in enumerate(mask):
                if tag:raster[k]=13+fx[k]
        full=Image.new('L',(256,192));ink=Image.frombytes('L',SIZE,bytes(raster))
        if n==4: ink=ink.resize((192,96),NEAR)
        full.paste(ink,((256-ink.width)//2,(192-ink.height)//2))
        frames.append(full)
    return colors,cycle,frames

def add_lutz_tiara(art, frames, colors):
    # Only the forehead tiles select palette 1. Its gold stays fixed while
    # the lightning cycles slots 13..15 of palette 0 on the same scanlines.
    spec=json.loads((art/'lineage.json').read_text())['tiara_lutz']
    path=art/spec['arquivo']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=spec['sha256']:
        raise ValueError('Lutz tiara differs from its receipt')
    with Image.open(path) as source:
        jewel=source.convert('RGBA')
    alpha=jewel.getchannel('A').point(lambda a:255 if a>=170 else 0)
    jewel.putalpha(alpha)
    jewel=jewel.crop(alpha.getbbox()).resize(tuple(spec['tamanho']),NEAR)
    x,y=spec['posicao_na_tela']
    palette=colors[:13]+[6,11,15]
    metal=[0,13,14,15,2,7]
    ink=native(jewel,jewel.size,[palette[i] for i in metal])
    ink=ink.point(metal+[0]*(256-len(metal)))
    touched={((x+i)//8,(y+j)//8) for i in range(jewel.width) for j in range(jewel.height)
             if jewel.getpixel((i,j))[3]}
    for frame in frames:
        for tx,ty in touched:
            bounds=(tx*8,ty*8,tx*8+8,ty*8+8)
            tile=frame.crop(bounds)
            if tile.getextrema()[1]>=13:raise ValueError('Tiara overlaps the CRAM effect')
            frame.paste(tile.point(lambda c:c+16),bounds)
        frame.paste(ink.point(lambda c:c+16),(x,y),jewel.getchannel('A'))
    return colors+palette

def encode_pair(frames,colors):
    tiles={bytes(32):0}
    maps=[]
    for im in frames:
        ids=[]
        for y in range(0,192,8):
            for x in range(0,256,8):
                values=list(im.crop((x,y,x+8,y+8)).getdata())
                second=values[0]>=16
                if second:
                    if min(values)<16:raise ValueError('Mixed palettes within a VDP tile')
                    values=[c-16 for c in values]
                raw=planar(values)
                ids.append(tiles.setdefault(raw,len(tiles)) | (0x0800 if second else 0))
        maps.append(ids)
    if len(tiles)>448: raise ValueError(f'PNT overlap: {len(tiles)}')
    changes=[k for k,(a,b) in enumerate(zip(*maps)) if a!=b]
    # Each exposure uses row runs. Emit one VDP address for each contiguous run.
    runs=[]
    for cell in changes:
        if not runs or cell!=runs[-1][-1]+1 or cell//32!=runs[-1][0]//32:runs.append([])
        runs[-1].append(cell)
    tables=[]
    for ids in maps:
        table=bytearray()
        for run in runs:
            table.extend(struct.pack('<HB',run[0],len(run)))
            table.extend(struct.pack('<'+'H'*len(run),*(ids[c] for c in run)))
        tables.append(bytes(table)+b'\0\0\0')
    base=struct.pack('<H',len(tiles)*32)+bytes(colors[:16])+b''.join(tiles)+struct.pack('<768H',*maps[0])
    return base,tables,len(tiles),len(changes)

def export_cycle_layers(folder,stats):
    """Export the same exclusive CRAM indices as editable transparent layers."""
    for row in stats:
        if not row['ciclo']: continue
        dest=folder/row['plano']
        for pose in range(2):
            with Image.open(dest/f'sms-{pose}.png') as im:
                colors=im.convert('RGB')
                alpha=Image.frombytes('L',im.size,bytes(255 if 13<=v<16 else 0 for v in im.tobytes()))
                effect=colors.copy().convert('RGBA');effect.putalpha(alpha)
                plate=colors.copy();plate.paste(NAVY,(0,0,*im.size),alpha)
                plate.save(dest/f'sem-efeito-{pose}.png')
                effect.save(dest/f'efeito-3-cores-{pose}.png')
                stamp(plate,effect,(0,0))
                assert not ImageChops.difference(plate,colors).getbbox()

def pack_scenes(art,out,voice):
    scenes,slash=make_layers(art,out/'camadas')
    pages=bytearray();meta=[];stats=[]
    for n,pair in enumerate(scenes):
        colors,cycle,frames=palette_frames(n,pair)
        if NAMES[n]=='noah':
            colors=add_lutz_tiara(art,frames,colors)
        raw,tables,tiles,changed=encode_pair(frames,colors)
        row=[]
        for t in tables:
            row.append(0x8000+len(raw));raw+=t
        row+=cycle or [0,0,0]
        if n==0:
            voice_addr=0x8000+len(raw);raw+=voice
        tail=bytes(colors[16:])
        if len(raw)+len(tail)>16384:raise ValueError(f'{NAMES[n]} bank {len(raw)}')
        pages.extend(raw.ljust(16384-len(tail),b'\xff')+tail);meta.append(row)
        for i,frame in enumerate(frames):palette_view(frame,colors).save(out/'camadas'/NAMES[n]/f'sms-{i}.png')
        stats.append(dict(plano=NAMES[n],tiles=tiles,celulas_alternadas=changed,bytes_ocupados=len(raw)+len(tail),ciclo=cycle))
    # Diagonal of 64x64 reduced to non-empty 8x8 SAT cells. Orientations are in pixels.
    ink=slash.resize((64,64),NEAR)
    raster=native(ink,(64,64),[0,35,59,63])
    raw=bytearray();coords=[]
    for y in range(0,64,8):
        for x in range(0,64,8):
            chip=[raster.getpixel((x+j,y+i)) if ink.getpixel((x+j,y+i))[3]>=128 else 0 for i in range(8) for j in range(8)]
            if any(chip):coords.extend((x,y));raw.extend(planar(chip))
    peak=max(sum(y<=l<y+8 for y in coords[1::2]) for l in range(64))
    assert peak<=8 and len(coords)//2<=64
    # Reactions use the second sprite pattern half beginning at tile 256; prove disjoint.
    assert all(row['tiles']<=256 for row in stats[6:])
    (out/'camadas'/'contrato.json').write_text(json.dumps(dict(planos=stats,corte_tiles=len(raw)//32,corte_pico_scanline=peak),indent=2)+'\n')
    export_cycle_layers(out/'camadas',stats)
    return pages,meta,voice_addr,raw,coords
