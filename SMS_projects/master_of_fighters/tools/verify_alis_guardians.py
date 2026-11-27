"""Match both authored exposures and each CRAM phase to native emulator frames."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageChops
from make_duel_scene02_assets import c_values, pixels
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

def reaction_signatures(package, name):
    """Compose the roster plate and the independent moving SAT directly from packed tiles."""
    config = json.loads((package/'chapter.json').read_text())['toolchain']['defines']
    header = (package/'magic_cine.h').read_text()
    def number(symbol):
        return int(re.search(rf'^#define {symbol} (\d+)u$', header, re.M)[1])
    offset = (number('MAGIC_PATTERN_BANK') - config['MOF_GUARDIANS_PAGE']) * 16384 + number('MAGIC_CUT_ADDR') - 0x8000
    xy = c_values(header, 'magic_cut_xy')
    with (package/'magic.bin').open('rb') as fp:
        fp.seek(offset)
        tiles = fp.read(number('MAGIC_CUT_BYTES'))
    assert len(tiles) == len(xy)//2*32
    cut = Image.new('RGBA', (64,64))
    colors = (0,35,59,63)
    for i,(x,y) in enumerate(zip(xy[::2], xy[1::2])):
        for j,ink in enumerate(pixels(tiles[i*32:(i+1)*32])):
            if ink:
                cut.putpixel((x+j%8,y+j//8), (*rgb(colors[ink]),255))
    with Image.open(package/'camadas'/name/'sms-0.png') as im:
        background = im.convert('RGB')
    stamps = {}
    for tick in range(41):
        shift = (2 if tick%2 else -2) if 15<=tick<21 else 0
        frame = ImageChops.offset(background,shift,0)
        frame.paste(cut,(44+3*tick,107-tick),cut)
        stamps[screen_hash(frame)] = tick
    assert len(stamps)==41
    return stamps

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
    rom=Path(meta['source_rom']).read_bytes()
    assert hashlib.sha256(rom).hexdigest()==report['rom_sha256']
    base=json.loads((package/'chapter.json').read_text())['toolchain']['defines']['MOF_GUARDIANS_PAGE']*16384
    packed=(package/'magic.bin').read_bytes()
    assert rom[base:base+len(packed)]==packed
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
    # Identify the defender in the duel and verify entire VDP frames against
    # that fighter's artwork plus the traveling cut, including horizontal shake.
    victory = next(row for row in report['steps'] if row['label'] in ('vitoria','vitoria_p2'))
    defeated, = [p for p in ('p1','p2') if victory['duel'][p]['life']==0]
    victim = victory['duel'][defeated]['fighter']
    plate = {0:'reacao_hayato',1:'reacao_alis'}[victim]
    reaction = reaction_signatures(package,plate)
    observed = {}
    for path in paths:
        with Image.open(path) as im:
            tick = reaction.get(screen_hash(im))
        if tick is not None:
            observed.setdefault(tick,int(path.stem))
    ticks = sorted(observed)
    distinct = len(ticks)
    endpoints = []
    if ticks:
        for tick in (ticks[0],ticks[-1]):
            with Image.open(paths[observed[tick]]) as im:
                native=im.convert('RGB')
            pink=[(x,y) for y in range(37,174) for x in range(25,233) if native.getpixel((x,y))==rgb(35)]
            endpoints.append([min(x for x,y in pink),min(y for x,y in pink)])
    tracks_ok=all(sum(counts)>0 for values in result.values() for counts in values)
    cycles_ok=all(all(sum(a)>0 for a in zip(*result[name])) for name in ('odin','noah','myau'))
    manifest=dict(rom_sha256=report['rom_sha256'],session_id=session.name,native_frames=len(paths),
                  exact_frame_counts=result,esperado='por plano, exposição e fase de CRAM',
                  controle_da_vitima=defeated,reacao=plate,posicoes_do_corte=distinct,ticks_do_corte=ticks,
                  fotogramas_exatos_da_reacao=observed,corte_inicio_fim=endpoints,
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
