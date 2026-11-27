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


def check_portrait_costumes(image):
    # Same pre-fight cel, looking inward. The common region ends above
    # the frame's rule at y=84. Only the two costume inks may differ.
    from stage_alis_postures import rgb
    pixels=np.asarray(image.convert('RGB'))
    first=pixels[66:84,16:96]
    second=pixels[146:164,160:240][:,::-1]
    want=first.copy()
    totals={}
    for pink,green in ((39,24),(59,44)):
        cloth=np.all(first==rgb(pink),axis=2)
        totals[str(green)]=int(cloth.sum())
        assert totals[str(green)]>0,(pink,green)
        want[cloth]=rgb(green)
    assert np.array_equal(want,second),'Mirror portrait materials differ'
    return totals


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
    sky=(0,0,85)
    screen=np.full((192,256,3),sky,dtype=np.uint8)
    check_apron_frame(screen,sky)
    for x,y in ((15,8),(96,10),(136,13),(250,15),(200,48)):
        screen[y,x]=0
        try:
            check_apron_frame(screen,sky)
        except AssertionError:
            screen[y,x]=sky
        else:
            raise AssertionError(('Marca indevida aceita',x,y))
    left='luz sob o trem de pouso'
    far='baliza distante direita'
    fast=[0,2,0,1,0,2,0]
    slow=[0,0,0,1,1,0,0]
    stats=exposure_stats({left:fast,far:slow})
    assert stats[left]['quadros']==[1,2,3,4,5,6] and stats[far]['quadros']==[3,5]
    for invalid in ([0]*7,fast):
        try:
            exposure_stats({left:fast,far:invalid})
        except AssertionError:
            continue
        raise AssertionError('Aceitou uma baliza congelada ou luzes sincronizadas.')
    from stage_alis_postures import rgb
    pair=Image.new('RGB',(256,192))
    for x,shade,second in ((16,39,24),(17,59,44)):
        pair.putpixel((x,66),rgb(shade))
        pair.putpixel((255-x,146),rgb(second))
    assert check_portrait_costumes(pair)=={'24':1,'44':1}
    pair.putpixel((231,146),rgb(63))
    try:
        check_portrait_costumes(pair)
    except AssertionError:
        pass
    else:
        raise AssertionError('Aceitou recoloração de material protegido no retrato.')
    print('Cartão, pista, ritmos de iluminação e controles negativos conferidos.')


def exposure_stats(history):
    """A frozen scene and a single pulse applied to every lamp both fail."""
    stats={}
    for name,sequence in history.items():
        changes=[i for i in range(1,len(sequence)) if sequence[i]!=sequence[i-1]]
        assert min(sequence)==0 and max(sequence)>0 and len(changes)>=2,name
        stats[name]=dict(maximo_de_pixels_no_tom_alternado=max(sequence),mudancas=len(changes),quadros=changes)
    assert len({tuple(info['quadros']) for info in stats.values()})==len(stats)
    assert stats['luz sob o trem de pouso']['mudancas']>stats['baliza distante direita']['mudancas']
    if 'baliza próxima esquerda' in stats:
        assert stats['baliza próxima esquerda']['mudancas']>stats['baliza distante direita']['mudancas']
    return stats


def check_lighting(frames,expected,initial):
    from palma_lighting import EXPOSURES,STEADY
    from stage_alis_postures import rgb
    floor_dx=scroll(initial,expected,162,188)
    active={}
    for name,items in EXPOSURES.items():
        points={}
        for x,y,row,shade,peak,_,_ in items:
            sy=y*8+row
            for u in range(x*8,x*8+8):
                if tuple(expected[sy,u])==rgb(shade):
                    sx=(u+(floor_dx if sy>=160 else 0))%256
                    points[sy,sx]=(rgb(shade),rgb(peak))
        assert points,name
        active[name]=points
    history={name:[] for name in active}
    for file in sorted(frames.glob('*.png')):
        with Image.open(file) as picture:
            actual=np.asarray(picture.convert('RGB'))
        for name,points in active.items():
            bright=0
            for (y,x),(base,peak) in points.items():
                pixel=tuple(actual[y,x])
                assert pixel in (base,peak),(file.name,name,x,y,pixel)
                bright+=int(pixel==peak)
            history[name].append(bright)
        for x,y in STEADY:
            dx=floor_dx if y>=20 else 0
            want=expected[8*y:8*y+8,8*x:8*x+8]
            shown=actual[8*y:8*y+8][:,(np.arange(8*x,8*x+8)+dx)%256]
            assert np.array_equal(want,shown),(file.name,'steady',x,y)
    stats=exposure_stats(history)
    for name,items in EXPOSURES.items():
        stats[name]['cores_SMS_base_alternada']=sorted({(e[3],e[4]) for e in items})
    return dict(frames=len(next(iter(history.values()))),grupos=stats,celulas_estaveis=STEADY,deslocamento_pista=floor_dx)


def check_apron_frame(frame, sky):
    # X0..7 are hidden by the VDP left-column mask. Every other gutter
    # pixel belongs to the stage, as does the entire visible IRQ seam.
    for left,right in ((8,16),(96,120),(136,160),(240,256)):
        assert np.all(frame[8:16,left:right]==sky),('life gutter',left,right)
    assert np.all(frame[48,8:]==sky),'Aircraft ink in the scrolling sky'


def exercise_damage(session, out, shot, sky):
    from duel_probe import RECORD_BYTES, decode
    def advance(p1,p2,count):
        isolated.sequence(session,[dict(p1=p1,p2=p2,frames=count)])
    def actors():
        for _ in range(8):
            raw=bytes(isolated.request(session,'read',0xc770,RECORD_BYTES)['ram'])
            if not raw[4]&1:
                duel=decode(raw)
                return duel['p1'],duel['p2']
            advance(0,0,1)
        raise RuntimeError('No coherent combat publication')
    def capture(hp):
        path=shot(f'vida-{hp[0]}-{hp[1]}')
        with Image.open(path) as picture:
            frame=np.asarray(picture.convert('RGB'))
        check_apron_frame(frame,sky)
        # The track is black where depleted. Measure visible fill separately.
        return [int(np.any(frame[11,x:x+80]!=0,axis=1).sum()) for x in (16,160)]
    a,b=actors()
    gap=b['pivot'][0]-a['pivot'][0]
    hp=[a['life'],b['life']]
    assert hp==[100,100]
    samples=[dict(vida=hp,luz_na_barra=capture(hp))]
    isolated.request(session,'record-steps-start','dano')
    try:
        for _ in range(10):
            a,b=actors()
            for _ in range(30):
                if b['pivot'][0]-a['pivot'][0]<=gap: break
                advance(8,4,3)
                a,b=actors()
            advance(0,0,5)
            advance(2,2,4)
            advance(0,0,4)
            advance(18,18,16)
            advance(0,0,80)
            a,b=actors()
            new=[a['life'],b['life']]
            assert 0<new[0]<hp[0] and 0<new[1]<hp[1],(hp,new)
            hp=new
            samples.append(dict(vida=hp,luz_na_barra=capture(hp)))
            if max(hp)<=25: break
        assert max(hp)<=25
        advance(0,0,48)
    finally:
        movie=isolated.request(session,'record-steps-stop')
    assert all(end<start for start,end in zip(samples[0]['luz_na_barra'],samples[-1]['luz_na_barra']))
    files=sorted((session/'evidence/dano').glob('*.png'))
    assert len(files)==movie['recorded_frames'] and len(files)>48
    critical_colors=[set(),set()]
    for i,path in enumerate(files):
        with Image.open(path) as picture:
            frame=np.asarray(picture.convert('RGB'))
        check_apron_frame(frame,sky)
        if i>=len(files)-48:
            for side,x in enumerate((16,160)):
                critical_colors[side].add(tuple(int(v) for v in frame[11,x]))
    assert all(len(colors)>=2 for colors in critical_colors),critical_colors
    import subprocess
    subprocess.run(['ffmpeg','-v','error','-threads','1','-framerate','60','-i',
        str(session/'evidence/dano/%06d.png'),'-c:v','libx264','-threads','1','-crf','0',
        '-pix_fmt','yuv444p',str(out/'dano.mp4')],check=True)
    return dict(amostras=samples,quadros=len(files),pixels_visiveis_das_margens=576,
                cores_no_pisca_critico=[sorted(colors) for colors in critical_colors])


def verify(build, assets, out, version, capture_battle=False,lighting=False,apron=False):
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
            if lighting:
                log['tecido_retrato_p2']=check_portrait_costumes(screen)
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
            length=320 if lighting else 96
            clip=isolated.video(session,length,'terminal')
            shutil.copyfile(clip['path'],out/'terminal.mp4')
            shutil.copyfile(Path(clip['path']).with_suffix('.json'),out/'terminal.json')
            last=shot('vento')
            with Image.open(last) as picture:
                breeze=np.asarray(picture.convert('RGB'))
            a=scroll(actual,expected,34,46);b=scroll(breeze,expected,34,46)
            assert (a-b)%256==length//8
            log['cloud_motion']=dict(vdp=length,pixels=length//8)
            if length==96:
                log['cloud_px_per_96_vdp']=12
            if lighting:
                log['iluminacao']=check_lighting(session/'evidence/terminal',expected,actual)
        if apron:
            assert version==3 and lighting
            sky=expected[31,0]
            assert tuple(sky)==(0,0,85)
            fixed=np.roll(expected,dx,axis=1)[49:51,8:]
            for path in sorted((session/'evidence/terminal').glob('*.png')):
                with Image.open(path) as picture:
                    frame=np.asarray(picture.convert('RGB'))
                check_apron_frame(frame,sky)
                assert np.array_equal(frame[49:51,8:],fixed),'Apron shifted with clouds'
            log['dano']=exercise_damage(session,out,shot,sky)
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
    if not __debug__:
        raise RuntimeError('Execute a auditoria com as asserções do Python ativas.')
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--self-check',action='store_true')
    cli.add_argument('--lighting',action='store_true',help='Track each runway exposure over 320 native frames')
    cli.add_argument('--apron',action='store_true',help='Verify the V3 raster seam and both health bar gutters under damage')
    cli.add_argument('--audio',action='store_true',help='Capture Battle on the private FM session')
    for arg in ('build','assets','out'):
        cli.add_argument(arg,type=Path,nargs='?')
    cli.add_argument('version',type=int,choices=[1,2,3],nargs='?')
    args=cli.parse_args()
    if args.self_check:
        self_check()
    elif all((args.build,args.assets,args.out,args.version)):
        verify(args.build,args.assets,args.out,args.version,args.audio,args.lighting,args.apron)
    else:
        cli.error('Informe build, assets, out e versão.')
