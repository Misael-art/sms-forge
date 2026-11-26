"""Match both authored exposures and each CRAM phase to native emulator frames."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from alis_guardians_panels import NAMES
from stage_alis_postures import rgb

def screen_hash(im):return hashlib.sha256(im.convert('RGB').tobytes()).digest()

def palette_signatures(im,rotation):
    base=im.getpalette()
    for phase in range(3 if rotation else 1):
        pal=base.copy()
        for k in range(len(rotation)):pal[(13+k)*3:(14+k)*3]=rgb(rotation[(k+phase)%3])
        view=im.copy();view.putpalette(pal)
        yield screen_hash(view)

def self_check():
    im=Image.new('P',(8,8),1)
    pal=[0]*768;pal[3:6]=[85,170,255];im.putpalette(pal)
    im.putpixel((1,1),13)
    stamps=list(palette_signatures(im,[35,59,63]))
    assert len(set(stamps))==3
    assert next(palette_signatures(im,[]))==screen_hash(im)
    im.putpixel((1,1),1)
    assert len(set(palette_signatures(im,[35,59,63])))==1

def verify(package,evidence,session):
    report=json.loads((evidence/'observations.json').read_text())
    meta=json.loads((session/'session.json').read_text())
    assert report['closed']=='closed' and report['rom_sha256']==meta['rom_sha256'] and session.name==report['session_id']
    cells=json.loads((package/'camadas/contrato.json').read_text())
    signatures={};seen={}
    for i,name in enumerate(NAMES[:6]):
        rotation=cells['planos'][i]['ciclo']
        for pose in range(2):
            im=Image.open(package/'camadas'/name/f'sms-{pose}.png')
            for phase,signature in enumerate(palette_signatures(im,rotation)):
                key=(name,pose,phase)
                signatures[signature]=key;seen[key]=0
    paths=sorted((session/'evidence/guardioes').glob('*.png'))
    assert len(paths)==report['movie']['recorded_frames']
    for path in paths:
        with Image.open(path) as im:
            key=signatures.get(screen_hash(im))
            if key:seen[key]+=1
    result={name:[[seen.get((name,pose,phase),0) for phase in range(3 if cells['planos'][i]['ciclo'] else 1)] for pose in range(2)] for i,name in enumerate(NAMES[:6])}
    # The moving cut is an independent hardware overlay. Detect hot pink
    # (SMS 0x23) relative to the palette of the victim alone.
    bounds=[]
    for row in report['steps']:
        if row['label']=='plano_7':
            start=row['vdp']-report['movie']['first_frame']
            for path in paths[max(0,start):start+37]:
                with Image.open(path) as im:
                    im=im.convert('RGB')
                    pix=im.load();pts=[(x,y) for y in range(37,174) for x in range(25,233) if pix[x,y]==rgb(35)]
                    if pts:bounds.append([min(p[0] for p in pts),min(p[1] for p in pts)])
    distinct=len({tuple(p) for p in bounds})
    tracks_ok=all(sum(counts)>0 for values in result.values() for counts in values)
    cycles_ok=all(all(sum(a)>0 for a in zip(*result[name])) for name in ('odin','noah','myau'))
    manifest=dict(rom_sha256=report['rom_sha256'],session_id=session.name,native_frames=len(paths),
                  exact_frame_counts=result,esperado='por plano, exposição e fase de CRAM',
                  posicoes_do_corte=distinct,corte_inicio_fim=[bounds[0],bounds[-1]] if bounds else [],
                  duas_exposicoes=tracks_ok,tres_fases=cycles_ok)
    (evidence/'prova_camadas.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(manifest,ensure_ascii=False))
    return tracks_ok and cycles_ok and distinct>=6

if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--self-check']:
        self_check();print('Palette rotation and isolation passed');raise SystemExit(0)
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('package','evidence','session'):parser.add_argument(name,type=Path)
    a=parser.parse_args()
    self_check()
    raise SystemExit(0 if verify(a.package,a.evidence,a.session) else 1)
