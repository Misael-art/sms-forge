"""Compare the two Alis repertoires and verify their four packets per pose inside the ROM."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct

from PIL import Image, ImageDraw
from make_duel_scene02_assets import c_values
from pack_scene02_repertoire import verify_packet
from revise_scene02_alis import raster
from stage_alis_postures import rgb
from stage_alis_mirror import PELVIS_X, POSES, SOURCE, sheet_drawings

CLOTH=(39,59)
COSTUME={39:24,59:44}
REVIEW=(*range(30,42),43,46,*range(62,66),*range(67,71),76)


def verify_materials(before,after):
    assert before.keys()==after.keys()
    for point,c in before.items():
        if c in (19,35): valid=CLOTH
        elif c in (24,44): valid=(24,44)
        elif c==16: valid=(0,16,37)
        else: valid=(c,)
        assert after[point] in valid,(point,c,after[point])


def verify_cloth_mask(drawing,actual,player,right):
    """Compare registered shadow and highlight pixels to the reviewed cel."""
    inks={19:24,35:44} if player else {19:39,35:59}
    expected={}
    for (x,y),shade in drawing.items():
        if shade in inks:
            offset=x-PELVIS_X
            expected[offset if right else -offset-1,y]=inks[shade]
    shown={pos:shade for pos,shade in actual.items() if shade in inks.values()}
    if shown!=expected:
        raise ValueError('A posição da luz ou da sombra do tecido diverge da ficha.')
    return len(expected)


def check_atlas(folder,views):
    drawings=sheet_drawings(folder)
    compared=0
    for name,drawing in drawings.items():
        pose=POSES.index(name)
        for player in (0,1):
            for right in (False,True):
                compared+=verify_cloth_mask(drawing,views[pose,player,right],player,right)
    return dict(poses=len(drawings),variantes=4*len(drawings),pixels_de_tecido=compared,
                sha256=hashlib.sha256((folder/'poses.png').read_bytes()).hexdigest())


def self_check():
    before={(0,0):19,(1,0):27,(2,0):16}
    verify_materials(before,{(0,0):59,(1,0):27,(2,0):37})
    for bad in ({(0,0):59,(1,0):39,(2,0):37},{(0,0):59,(1,0):27}):
        try:
            verify_materials(before,bad)
        except AssertionError:
            continue
        raise AssertionError('Accepted a skin recolor or a missing silhouette pixel')
    drawing={(PELVIS_X,0):19,(PELVIS_X+1,0):35}
    assert verify_cloth_mask(drawing,{(-1,0):24,(-2,0):44},1,False)==2
    try:
        verify_cloth_mask(drawing,{(-1,0):44,(-2,0):24},1,False)
    except ValueError:
        pass
    else:
        raise AssertionError('Aceitou luz e sombra invertidas com histograma idêntico.')
    print('Silhueta, material protegido e posição do realce conferidos com controles negativos.')


def study(old,new):
    old_rows=old['frames']
    assert len(old_rows)==len(new['frames'])==376
    assert new['palette']==[{16:37,19:39,35:59}.get(c,c) for c in old['palette']]
    names=list(dict.fromkeys(f['name'] for f in old_rows))
    views={}; coverage=[]
    for a,b in zip(old_rows,new['frames']):
        assert all(a[k]==b[k] for k in ('name','right','player','bank','address','count','spill_tiles'))
        assert sorted(a['background_pixels'])==sorted(b['background_pixels'])
        before=raster(a,old['palette']);after=raster(b,new['palette'])
        verify_materials(before,after)
        assert [v[:2] for v in a['sprite_cells']]==[v[:2] for v in b['sprite_cells']]
        views[names.index(b['name']),b['player'],b['right']]=after
        if b['right'] and not b['player']:
            shades=Counter(after.values())
            coverage.append(dict(pose=names.index(b['name']),nome=b['name'],sombra=shades[39],
                                 luz=shades[59],luz_antes=Counter(before.values())[35],indigo=shades[37]))
    for pose in range(len(names)):
        for side in (True,False):
            assert {k:COSTUME.get(c,c) for k,c in views[pose,0,side].items()}==views[pose,1,side]
    for i in REVIEW:
        assert min(coverage[i]['luz'],coverage[i]['sombra'])>0,(i,coverage[i])
    return views,coverage


def verify_rom(folder,plan,build):
    record=json.loads((build/'build_record.json').read_text())
    rom=(build/'rom/master_of_fighters.sms').read_bytes()
    assert hashlib.sha256(rom).hexdigest()==record['rom_sha256']
    header=(folder/'duel_mirror_assets.h').read_text()
    bg=c_values(header,'mof_duel_bg_palette')
    raw=bytes(c_values(header,'mof_duel_bg_stage'))
    rows=[raw[i*32:(i+1)*32] for i in c_values(header,'mof_duel_bg_rows')]
    symbol=re.search(r'^DEF _mof_duel_sprite_palette (0x[0-9a-fA-F]+)$',
                     (build/'obj/master_of_fighters.noi').read_text(),re.M)
    off=int(symbol[1],16)
    assert off<32768 and rom[off:off+16]==bytes(plan['palette'])
    for f in plan['frames']:
        off=f['bank']*16384+f['address']-32768
        end=struct.unpack_from('<H',rom,off+15)[0]
        verify_packet(rom[off:off+end+1+42*rom[off+end]],f,bg,rows,True)
    return record['rom_sha256']


def save_study(out,views,old):
    ids=(10,30,34,37,42,43,44,45,46,47,65,66)
    old_views=[raster(f,old['palette']) for f in old['frames'] if not f['player'] and f['right']]
    paper=(232,236,236)
    sheet=Image.new('RGB',(len(ids)*82+88,3*132+24),paper); draw=ImageDraw.Draw(sheet)
    for n,i in enumerate(ids):
        draw.text((88+82*n+31,5),f'{i:02}',fill='black')
        for j,pose in enumerate((old_views[i],views[i,0,True],views[i,1,True])):
            x0=min(x for x,y in pose); x1=max(x for x,y in pose)
            for (x,y),c in pose.items():
                u=88+82*n+41+(2*x-x0-x1); v=24+(j+1)*132-2*(144-y)-4
                draw.rectangle((u,v,u+1,v+1),fill=rgb(c))
    for n,t in enumerate(('P1 anterior','P1 revista','P2 revista')):
        draw.text((4,85+132*n),t,fill='black')
    sheet.save(out/'comparacao-trajes.png')


if __name__=='__main__':
    if not __debug__:
        raise RuntimeError('Execute a auditoria com as asserções do Python ativas.')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--self-check',action='store_true')
    cli.add_argument('--atlas',type=Path,default=SOURCE.parent/'alis_revisao_ficha',
                     help='Diretório com poses.png e o respectivo revisao.json da compilação.')
    for name in ('old','new','build','out'): cli.add_argument(name,type=Path,nargs='?')
    a=cli.parse_args()
    if a.self_check:
        self_check()
        raise SystemExit(0)
    if not all((a.old,a.new,a.build,a.out)): cli.error('Informe old, new, build e out.')
    old=json.loads((a.old/'repertoire-pages.json').read_text());new=json.loads((a.new/'repertoire-pages.json').read_text())
    views,coverage=study(old,new)
    atlas=check_atlas(a.atlas,views)
    sha=verify_rom(a.new,new,a.build)
    a.out.mkdir(parents=True,exist_ok=True)
    save_study(a.out,views,old)
    (a.out/'cores.json').write_text(json.dumps(dict(rom_sha256=sha,poses=coverage,
        atlas=atlas,variantes_verificadas=376,poses_revisadas=REVIEW,desvios_de_silhueta=0,desvios_p2=0),
        ensure_ascii=False,indent=2)+'\n')
