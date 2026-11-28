"""Reproduce one controller, VDP and combat case per private Emulicious session."""
import shutil
import subprocess
import time
import wave
from session_bridge import isolated
from duel_probe import RECORD_BYTES, decode


def focus_in_scanout(directory, out, actor, native_frames):
    """Locate the last light cluster in the tile containing the displayed hand."""
    from PIL import Image
    pose=actor['pose_presented']
    anchors={9:(-3,17),10:(0,14),11:(0,14),21:(-9,26)}
    for n in range(77,80):anchors[n]=(-9,26)
    for n in range(83,86):anchors[n]=(-16,29)
    for n in range(86,90):anchors[n]=(-8,29)
    dx,height=anchors.get(pose,(2,30))
    x,y=actor['pivot']
    hand=(x+(dx if actor['presented_facing_right'] else -dx-1),y-height)
    u,v=(point//8*8 for point in hand)
    mask=(0,24,24,126,126,24,24,0)
    pixels=[(x,y) for y,row in enumerate(mask) for x in range(8) if row&(128>>x)]
    matches=[]
    for number in native_frames:
        f=directory/f'{number:06d}.png'
        if not f.is_file():continue
        with Image.open(f) as raw:
            im=raw.convert('RGB')
            colors={im.getpixel((u+x,v+y)) for x,y in pixels}
            background={im.getpixel((u+x,v+y)) for x,y in ((0,0),(7,0),(0,7),(7,7))}
            if colors=={(170,170,170)} and background-colors:
                matches.append(int(f.stem))
                if len(matches)==1:shutil.copyfile(f,out/'foco-na-mao.png')
    assert matches,(pose,hand)
    return dict(pose=pose,hand=hand,tile_origin=[u,v],native_frames=matches)


def verify_gain_frames(directory, out, timeline, kind, amount):
    """Find the four native glyphs at both heights in actual VDP scanouts."""
    from PIL import Image
    digits=((0,)*5,(2,6,2,2,7),(7,1,7,4,7),(7,1,7,1,7),
            (5,5,7,1,1),(7,4,7,1,7),(7,4,7,5,7))
    plus=(0,2,7,2,0)
    unit=(5,5,7,5,5) if kind=='gain-hp' else (5,7,7,5,5)
    letter_p=(6,5,6,4,4)
    rows=[(a<<13)|(b<<9)|(c<<5)|(d<<1)
          for a,b,c,d in zip(plus,digits[amount],unit,letter_p)]
    pixels=[(x,y) for x in range(16) for y in range(5) if rows[y]&(1<<(15-x))]
    pivot=next(r['p1']['pivot'] for r in timeline if r['fx'][6])
    low=(pivot[1]-64)//8*8+1
    hits=[]
    heights=set()
    for source in sorted(directory.glob('*.png')):
        with Image.open(source) as raw:
            image=raw.convert('RGB')
            for y in (low,low-8):
                for x in range(max(0,pivot[0]-24),min(240,pivot[0]+8)):
                    if all(image.getpixel((x+dx,y+dy))==(255,255,255) for dx,dy in pixels):
                        hits.append((int(source.stem),x,y))
                        if y not in heights:
                            heights.add(y)
                            shutil.copyfile(source,out/('numero-baixo.png' if y==low else 'numero-alto.png'))
    assert heights=={low,low-8},(kind,heights)
    assert max(n for n,x,y in hits if y==low)<min(n for n,x,y in hits if y==low-8)
    return dict(amostras=hits,pixels_dos_glifos=len(pixels))


def recovery_audio(session, out, kind):
    from capture_audio import RATE, _peak
    root,meta=isolated.load(session)
    assert isolated.verify_audio_route(meta)
    raw=root/'evidence'/(kind+'.pcm')
    with raw.open('xb') as sink:
        proc=subprocess.Popen(['parec','-d',meta['audio_sink']+'.monitor','--raw',
            '--format=s16le',f'--rate={RATE}','--channels=1','--latency-msec=20'],stdout=sink)
        try:
            end=time.monotonic()+3
            while raw.stat().st_size==0 and time.monotonic()<end:
                time.sleep(.03)
            assert proc.poll() is None and raw.stat().st_size>0
            start=raw.stat().st_size
            first=isolated.request(session,'run')['frame']
            try:
                end=time.monotonic()+5
                while isolated.request(session,'status')['frame']<first+88:
                    if time.monotonic()>end:raise RuntimeError('Audio replay stalled')
                    time.sleep(.08)
            finally:
                isolated.request(session,'pause')
            time.sleep(.12)
        finally:
            proc.terminate()
            proc.wait(timeout=4)
    pcm=raw.read_bytes()[start:]
    assert isolated.verify_audio_route(meta) and _peak(pcm)>200
    name=out/(kind+'.wav')
    with wave.open(str(name),'wb') as stream:
        stream.setparams((1,2,RATE,0,'NONE','not compressed'))
        stream.writeframes(pcm)
    return dict(peak=_peak(pcm),sha256=isolated.sha(name),private_sink=meta['audio_sink'])


def exercise(case, session, out, controls, ram, chapter, log, save):
    trace=log['timeline']=[]
    def step(one=0,two=0):
        ack=controls((one,two,1))
        raw=ram(0xc770,RECORD_BYTES)
        if raw[:4]!=b'MFD1' or raw[4]&1:
            return None
        duel=decode(raw)
        fx=ram(0xc800,12)
        ch=ram(chapter,18)
        row=dict(frame=ack['frame'], tick=duel['logic_tick'], inputs=[one,two],
                 meter=list(ch[9:11]),combo=list(ch[16:18]),clock=list(ch[7:9]),fx=list(fx))
        for key in ('p1','p2'):
            a=duel[key]
            row[key]={field:a[field] for field in ('pivot','state','life','action_tick','free_since','pose_requested','pose_presented','presented_facing_right','keys_consumed','contact')}
        trace.append(row)
        return row

    def until(one,two,predicate,limit=200):
        for _ in range(limit):
            row=step(one,two)
            if row and predicate(row):return row
        save()
        raise AssertionError((case,one,two,trace[-1]))

    def burst(*steps):
        controls(*steps)

    def gesture(which,dirs,button,hold=4):
        toward=(8,4)[which];away=12^toward
        axes={'f':toward,'b':away,'x':toward|2,'z':away|2,'d':2,'-':0}
        for n,direction in enumerate(dirs):
            key=axes[direction];end=n==len(dirs)-1
            if end:key|=button
            burst((key if not which else 0,key if which else 0,hold if end else 4))

    def shot(label):
        result=isolated.capture(session,label+'.png')
        shutil.copyfile(result['path'],out/(label+'.png'))

    def get_charge(cost):
        for _ in range(cost+1):
            before=ram(chapter+9,1)[0]
            if before>=cost:return
            gesture(0,'b-b',32)
            burst((0,0,180))
            assert ram(chapter+9,1)[0]==before+1
        raise AssertionError('insufficient Reiki')

    corner=case.startswith('corner-')
    if corner:
        side=int(case.endswith('left'))
        name,rival=('p2','p1') if side else ('p1','p2')
        direction=4 if side else 8
        # Move the defender against its wall, then approach to throw distance.
        burst((direction if side else 0,0 if side else direction,170),(0,0,6))
        initial=until(0,0,lambda r:True)
        wall=initial[rival]['pivot'][0]
        assert wall==(43 if side else 212), (case,wall)
        def pads(attack,defend):
            return (defend,attack) if side else (attack,defend)
        until(*pads(direction,0),lambda r:abs(r[name]['pivot'][0]-wall)==24)
        burst((0,0,4))
    elif case=='gain-hp':
        # The opponent's Fire costs no Reiki and gives Alis one point on hit.
        gesture(1,'d-d',16,16);burst((0,0,85));get_charge(2)
    elif case in ('pause-double','pause-myau','pause-palma'):
        get_charge(8 if case=='pause-palma' else 4)
    start=isolated.request(session,'record-steps-start',case)
    try:
        if corner:
            until(*pads(16,0),lambda r:r[name]['state']==1)
            first=until(0,0,lambda r:r[rival]['life']==90)
            until(*pads(0,direction),lambda r:r[name]['action_tick']==16 and r[name]['state']==1,90)
            burst((*pads(16,direction),2))
            second=until(*pads(0,direction),lambda r:r[rival]['life']==84,40)
            assert second[rival]['free_since']==first[rival]['free_since']
            assert second['combo'][side]==2, second
            shot('dois-hits')
            # Queue the next short press around the earliest recovery.
            until(*pads(0,direction),lambda r:r[name]['state']==1 and r[name]['action_tick']>=12,80)
            burst((*pads(16,direction),2))
            block=until(*pads(0,direction),lambda r:r[rival]['state']==2,55)
            assert block[rival]['life']==84 and block[rival]['keys_consumed']&direction
            assert block[rival]['free_since']>second[rival]['free_since']
            assert block[rival]['pivot'][0]==wall and block['combo'][side]==0
            shot('defesa-no-canto')
            log['corner']={'wall':wall,'attacker':name,'hit_ticks':[first['tick'],second['tick']],
                           'free':block[rival]['free_since'],'block_tick':block['tick'],'hp':84}
        else:
            before=until(0,0,lambda r:True)
            shot('antes')
            moves={'gain-hp':('d-d',32),'gain-mp':('b-b',32),'pause-double':('dxf',48),
                   'pause-myau':('dzb',32),'pause-palma':('dfdf',16)}
            dirs,button=moves[case]
            gesture(0,dirs,button,3)
            for i in range(90):
                row=step(0,8 if case=='pause-double' else 0)
                if not row:continue
                fx=row['fx']
                if fx[1] and 2<=fx[3]<fx[1]:
                    key='efeito' if fx[3]<fx[1]//2 else 'concentracao'
                    if not (out/(key+'.png')).exists():shot(key)
                elif 0<fx[6]<15:
                    key='efeito' if fx[6]>=8 else 'subida'
                    if not (out/(key+'.png')).exists():shot(key)
            if case.startswith('pause-'):
                ticks=[r for r in trace if r['fx'][0] and r['fx'][3]]
                duration={'pause-double':8,'pause-myau':8,'pause-palma':10}[case]
                assert ticks and all(r['fx'][1]==duration for r in ticks)
                from PIL import Image
                before_pixels=Image.open(out/'antes.png').convert('RGB').crop((12,154,244,173))
                dark_pixels=Image.open(out/'concentracao.png').convert('RGB').crop((12,154,244,173))
                darkened=sum(sum(a)>sum(b) for a,b in zip(before_pixels.getdata(),dark_pixels.getdata()))
                assert darkened>before_pixels.width*before_pixels.height//2, darkened
                assert len({r['tick'] for r in ticks})==len({tuple(r['clock']) for r in ticks})==1
                assert any(r['fx'][3]==duration and not r['fx'][1] and r['tick']>ticks[0]['tick'] for r in trace)
                if case=='pause-double':
                    resumed=next(r for r in trace if r['tick']>ticks[-1]['tick'] and not r['fx'][1])
                    assert resumed['p2']['keys_consumed']&8
                    log['guard_on_resume']=resumed['tick']
                log['pause']={'duration':duration,'sampled_phases':sorted({r['fx'][3] for r in ticks}),
                              'frozen_tick':ticks[0]['tick'],'darker_pixels_in_floor':darkened}
            else:
                gains=[r for r in trace if r['fx'][6] and r['fx'][4]==(1 if case=='gain-hp' else 2)]
                assert gains and len({r['fx'][8] for r in gains})==1
                value=gains[0]['fx'][8]
                if case=='gain-hp':
                    assert value==6 and gains[-1]['p1']['life']==before['p1']['life']+6
                else:assert value==1 and gains[-1]['meter'][0]==before['meter'][0]+1
                assert (out/'subida.png').is_file()
                log['gain']={'amount':value,'HP_before_after':[before['p1']['life'],gains[-1]['p1']['life']],
                             'MP_before_after':[before['meter'][0],gains[-1]['meter'][0]]}
            shot('depois')
    finally:
        movie=isolated.request(session,'record-steps-stop')
        log['movie']={'first':start['first_frame'],'frames':movie['recorded_frames']}
        save()
        subprocess.run(['ffmpeg','-v','error','-threads','1','-framerate','60','-i',
                        str(session/'evidence'/case/'%06d.png'),'-c:v','libx264','-threads','1',
                        '-pix_fmt','yuv420p',str(out/(case+'.mp4'))],check=True)
    if case.startswith('pause-'):
        from PIL import Image, ImageStat
        floor=(12,154,244,173)
        with Image.open(out/'antes.png') as initial, Image.open(out/'concentracao.png') as dark:
            normal=sum(ImageStat.Stat(initial.convert('RGB').crop(floor)).mean)
            dim=sum(ImageStat.Stat(dark.convert('RGB').crop(floor)).mean)
        assert normal>dim
        frames=[]
        for sample in sorted((session/'evidence'/case).glob('*.png')):
            with Image.open(sample) as frame:
                luminance=sum(ImageStat.Stat(frame.convert('RGB').crop(floor)).mean)
                if luminance<(normal+dim)/2:frames.append(int(sample.stem))
        log['pause']['foco']=focus_in_scanout(session/'evidence'/case,out,ticks[-1]['p1'],frames)
        log['pause']['native_tinted_frames']=frames
        save()
        assert len(frames)==duration and frames[-1]-frames[0]==duration-1,(case,frames)
    if case in ('gain-hp','gain-mp'):
        scan=verify_gain_frames(session/'evidence'/case,out,trace,case,value)
        scan.update(sha256_rom=log['rom_sha256'],sessao=session.name)
        isolated.atomic(out/'leitura-do-numero.json',scan)
        burst((0,0,190))
        if case=='gain-hp':get_charge(2)
        assert ram(chapter+1,1)[0]==0  # music disabled in Options
        old=ram(0xc80a,1)[0]
        gesture(0,dirs,button,4)
        log['isolated_sfx']=recovery_audio(session,out,case)
        assert ram(0xc80a,1)[0]==old+1
        save()
