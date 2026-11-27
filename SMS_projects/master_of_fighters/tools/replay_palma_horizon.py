"""Measure independent sky, apron and pavement displacements in the actual SMS framebuffer."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from pack_alis_magic import stage_patterns
from replay_alis_chapter import PROJECT, isolated
from stage_alis_postures import rgb


def reference(panels, fighters):
    _, mapping, patterns, palette = stage_patterns(panels,fighters)
    cells = np.array([list(tile) for tile in patterns],dtype=np.uint8)
    indices = cells[mapping].reshape(24,32,8,8).transpose(0,2,1,3).reshape(192,256)
    return np.array([rgb(c) for c in palette],dtype=np.uint8)[indices]


def scroll(measured, source, top, bottom):
    # Exclude the VDP's blank left column, band switching lines and outer margin.
    # Retain a runner-up so a flat region cannot be reported as motion.
    sample = measured[top:bottom,8:248]
    results = []
    for dx in range(-128,128):
        expected = np.roll(source[top:bottom],dx,axis=1)[:,8:248]
        results.append((int(np.count_nonzero(np.any(sample!=expected,axis=2))),dx))
    results.sort()
    errors,shift = results[0]
    assert errors < sample.shape[0]*sample.shape[1]//12 and results[1][0]>errors,(top,results[:2])
    return shift


def wrap(delta):
    return (delta + 128) % 256 - 128


def wind_sequence(frames, gold, initial):
    """Check the exact cadence against every uncompressed VDP framebuffer."""
    sky = gold[34:46]
    previous = initial
    changes = []
    for index, path in enumerate(sorted(frames.glob('*.png')),1):
        with Image.open(path) as image:
            observed = np.asarray(image.convert('RGB'))[34:46,8:248]
        offsets = (previous, wrap(previous-1))
        errors = [np.count_nonzero(np.any(observed!=np.roll(sky,dx,axis=1)[:,8:248],axis=2))
                  for dx in offsets]
        assert min(errors) < observed.shape[0]*observed.shape[1]//12 and errors[0]!=errors[1], (index,errors)
        best = offsets[int(errors[1]<errors[0])]
        if best != previous:
            changes.append(index)
        previous = best
    assert len(changes)==16 and all(b-a==8 for a,b in zip(changes,changes[1:])),changes
    return changes


def run(build, panels, fighters, out):
    receipt = json.loads((build/'build_record.json').read_text())
    rom = PROJECT/receipt['rom_path']
    assert isolated.sha(rom)==receipt['rom_sha256']
    gold = reference(panels,fighters)
    out.mkdir(parents=True,exist_ok=False)
    isolated.DEFAULT_ROOT = PROJECT.parents[1]/'.runtime/qa'
    session = isolated.start(rom,sms_fm=True)
    log = dict(session=session.name,rom_sha256=receipt['rom_sha256'],samples=[])
    def pad(first,second,frames):
        return isolated.sequence(session,[dict(p1=first,p2=second,frames=frames)])
    def press(key):
        pad(key,0,4)
        pad(0,0,15)
    def grab(name):
        shot = isolated.capture(session,name+'.png')
        path = Path(shot['path'])
        for suffix in ('.png','.json'):
            shutil.copyfile(path.with_suffix(suffix),out/(name+suffix))
        with Image.open(path) as im:
            screen = np.asarray(im.convert('RGB'))
        cloud = scroll(screen,gold,34,46)
        apron = scroll(screen,gold,58,78)
        floor = scroll(screen,gold,163,189)
        # The central clock changes. Both ends of the life bars are invariant.
        hud = screen[1:15,16:56].tobytes()
        row = dict(name=name,vdp=shot['frame'],cloud=cloud,apron=apron,floor=floor,
                   hud=hashlib.sha256(hud).hexdigest())
        # Unscroll the strip behind the hangars. The absence of sprites and
        # animated glass here allows an exact comparison with the packed art.
        ridge = (slice(64,72),slice(88,181))
        actual = np.roll(screen,-apron,axis=1)[ridge]
        expected = gold[ridge]
        assert np.array_equal(actual,expected), 'The ridge differs from its ROM patterns'
        row['ridge_pixels'] = int(np.all(actual==rgb(53),axis=2).sum())
        log['samples'].append(row)
        return row
    try:
        pad(0,0,145)
        press(16)
        press(2)
        press(16)
        pad(0,0,230)
        start = grab('pista')
        clip = isolated.video(session,128,'nuvens')
        shutil.copyfile(clip['path'],out/'nuvens.mp4')
        shutil.copyfile(Path(clip['path']).with_suffix('.json'),out/'nuvens.json')
        log['wind_steps'] = wind_sequence(session/'evidence/nuvens',gold,start['cloud'])
        end = grab('vento')
        assert end['vdp']-start['vdp']==128
        assert wrap(end['cloud']-start['cloud'])==-16 and end['apron']==start['apron'] and end['floor']==start['floor']
        for name,key in [('oeste',4),('leste',8)]:
            pad(key,key,110)
            pad(0,0,8)
            grab(name)
        west,east = log['samples'][-2:]
        moved = west['apron']-east['apron']
        delta = east['vdp']-west['vdp']
        cloud_move = wrap(west['cloud']-east['cloud'])
        # Wind can be between two adjacent integer eighths at a capture boundary.
        assert moved>=4 and east['floor']<west['floor'] and abs(west['floor']-east['floor']-2*moved)<=1
        assert abs(cloud_move - delta/8 - moved/2)<=1.5
        assert len({s['hud'] for s in log['samples']})==1
        log['clip_sha256']=isolated.sha(out/'nuvens.mp4')
        log['passed']=True
    finally:
        isolated.close_session(session)
        log['closed']=isolated.load(session)[1]['state']
        shutil.copyfile(session/'commands.jsonl',out/'commands.jsonl')
        isolated.atomic(out/'observations.json',log)


def self_check():
    base = np.zeros((192,256,3),np.uint8)
    base[34:46,17:22]=85
    base[34:46,94:106]=170
    base[34:46,151:157]=255
    for offset in (-127,-8,0,1,37,127):
        assert scroll(np.roll(base,offset,axis=1),base,34,46)==offset
    try:
        scroll(base,base,50,58)
    except AssertionError:
        pass
    else:
        raise AssertionError("A blank band cannot measure displacement")
    assert wrap(128)==-128 and wrap(-129)==127
    print("Deslocamentos, wrap e rejeição de faixa ambígua conferidos.")


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--self-check',action='store_true')
    paths=('build','panels','fighters','out')
    for argument in paths:
        cli.add_argument(argument,type=Path,nargs='?')
    args=cli.parse_args()
    if args.self_check:
        self_check()
    elif all(getattr(args,p) is not None for p in paths):
        run(args.build,args.panels,args.fighters,args.out)
    else:
        cli.error('Informe build, panels, fighters e out.')
