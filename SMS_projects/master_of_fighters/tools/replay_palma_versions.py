"""Verify the Versus selector through controller input and native framebuffers."""
import argparse
import json
import re
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops
from replay_alis_chapter import PROJECT, capture_session, isolated
from replay_palma_horizon import reference, scroll


def same_frame(observed,expected):
    return observed.size==expected.size and ImageChops.difference(
        observed.convert('RGB'),expected.convert('RGB')).getbbox() is None


def stage_coverage(actual,expected,dx):
    # Only static concourse in this region. Both portraits, the HUD,
    # the actors, the scanner and the blinking tower lie outside.
    want=np.roll(expected,dx,axis=1)[58:76,40:188]
    pixels=np.all(actual[58:76,40:188]==want,axis=2)
    return int(pixels.sum()),pixels.size


def self_check():
    tile=Image.new('RGB',(2,2),(85,0,0))
    altered=tile.copy()
    altered.putpixel((1,1),(0,0,85))
    assert same_frame(tile,tile.copy()) and not same_frame(tile,altered)
    assert not same_frame(tile,tile.resize((1,1)))
    source=np.zeros((192,256,3),np.uint8)
    source[:,::5]=85
    moved=np.roll(source,7,axis=1)
    hits,total=stage_coverage(moved,source,7)
    assert hits==total==2664
    moved[58,40]=255
    assert stage_coverage(moved,source,7)==(2663,total)
    assert stage_coverage(moved,source,4)[0]<.98*total
    print('Identidade de cartão, dimensões e correspondência da pista verificadas.')


def verify(build, assets, out, version, capture_battle=False):
    receipt=json.loads((build/'build_record.json').read_text())
    rom=PROJECT/receipt['rom_path']
    assert isolated.sha(rom)==receipt['rom_sha256']
    symbols=(build/'obj/master_of_fighters.map').read_text()
    def addr(name):
        return int(re.search(r'^\s*([0-9A-F]{8})\s+_'+name+r'\s+',symbols,re.M)[1],16)
    choice,index,chapter,audio,spills=map(addr,('mof_stage_choice','mof_pan_index','chapter','mof_battle_backend','mof_pan_spills'))
    fighters=PROJECT/json.loads((assets/'chapter.json').read_text())['toolchain']['include_dirs'][0]
    out.mkdir(parents=True,exist_ok=False)
    isolated.DEFAULT_ROOT=PROJECT.parents[1]/'.runtime/qa'
    session=isolated.start(rom,sms_fm=True)
    log=dict(session_id=session.name,rom_sha256=receipt['rom_sha256'],version=version,choices=[])
    def pad(keys,frames):
        isolated.sequence(session,[dict(p1=keys,p2=0,frames=frames)])
    def press(key):
        pad(key,4);pad(0,14)
    def read(address,count=1):
        return isolated.request(session,'read',address,count)['ram']
    def shot(name):
        data=isolated.capture(session,name+'.png')
        path=Path(data['path'])
        for ext in ('.png','.json'):
            shutil.copyfile(path.with_suffix(ext),out/(name+ext))
        return (out/(name+'.png'))
    def check_card(name,n):
        selected=read(choice)[0]+1
        pos=read(index)[0]
        assert selected==n and read(spills)[0]==0,(name,selected,pos)
        file=shot(name)
        golden=assets/f'v{n}'/('versus.png' if pos==0 else f'versus-{pos:02}.png')
        with Image.open(file) as screen,Image.open(golden) as stamp:
            assert same_frame(screen,stamp),(name,pos)
        log['choices'].append(dict(name=name,version=n,pan=pos,sha256=isolated.sha(file)))
    try:
        pad(0,170);check_card('abertura',3)
        press(16);press(2);press(16)
        check_card('entrada',3)
        # Hold through an entire pan and the old automatic deadline. It must
        # stay on the chosen card until confirmation, with just one edge.
        key=1 if version==2 else 2
        pad(key,190);pad(0,20)
        check_card('toque',2 if version==2 else 1)
        if version==1:
            for n in (2,3,1):
                press(2)
                check_card(f'baixo_{n}',n)
        elif version==2:
            for n in (1,3,2):
                press(1)
                check_card(f'cima_{n}',n)
        else:
            press(1);pad(0,145)
            check_card('volta',3)
        assert read(audio)[0]==2
        press(16);pad(0,230)
        state=read(chapter,16)
        assert state[0]==0 and state[5]==2 and read(audio)[0]==2,state
        screen=shot('luta')
        with Image.open(screen) as picture:
            actual=np.asarray(picture.convert('RGB'))
        expected=reference(assets/f'v{version}',fighters)
        dx=scroll(actual,expected,58,76)
        log['stage_match_pixels'],log['stage_pixels']=stage_coverage(actual,expected,dx)
        assert log['stage_match_pixels']>=log['stage_pixels']*.98
        if version==3:
            clip=isolated.video(session,96,'terminal')
            shutil.copyfile(clip['path'],out/'terminal.mp4')
            shutil.copyfile(Path(clip['path']).with_suffix('.json'),out/'terminal.json')
            last=shot('vento')
            with Image.open(last) as picture:
                breeze=np.asarray(picture.convert('RGB'))
            a=scroll(actual,expected,34,46);b=scroll(breeze,expected,34,46)
            assert (a-b)%256==12
            log['cloud_px_per_96_vdp']=12
        if capture_battle:
            assert capture_session(session,5,'battle')==0
            for name in ('battle.wav','battle.audio.json'):
                shutil.copyfile(session/name,out/name)
            log['battle_wav_sha256']=isolated.sha(out/'battle.wav')
        log['passed']=True
    finally:
        isolated.close_session(session)
        log['closed']=isolated.load(session)[1]['state']
        shutil.copyfile(session/'commands.jsonl',out/'commands.jsonl')
        isolated.atomic(out/'observations.json',log)


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--self-check',action='store_true')
    cli.add_argument('--audio',action='store_true',help='Capture Battle on the private FM session')
    for arg in ('build','assets','out'):
        cli.add_argument(arg,type=Path,nargs='?')
    cli.add_argument('version',type=int,choices=[1,2,3],nargs='?')
    args=cli.parse_args()
    if args.self_check:
        self_check()
    elif all((args.build,args.assets,args.out,args.version)):
        verify(args.build,args.assets,args.out,args.version,args.audio)
    else:
        cli.error('Informe build, assets, out e versão.')
