"""Exercise Alis specials in a normal local match on the exact candidate cartridge."""
import argparse
import json
import re
import shutil
import struct
import subprocess
import sys
import time
from pathlib import Path
from replay_alis_chapter import PROJECT, isolated, decode, RECORD_BYTES

D,F,B,ONE,TWO=2,8,4,16,32
NAMES=('none','fire_curto','fire_forte','chamas','myau','rest','onda','sabre','chat','espelho','tontura','guardioes')

def record_cinema(session,out):
    from capture_audio import RATE, _peak
    root,meta=isolated.load(session)
    if not isolated.verify_audio_route(meta):
        raise RuntimeError('Unverified private monitor')
    name='guardioes_com_som'
    pcm=root/'evidence'/(name+'.pcm')
    with pcm.open('xb') as audio:
        recorder=subprocess.Popen(['parec','-d',meta['audio_sink']+'.monitor','--raw','--format=s16le',
                            f'--rate={RATE}','--channels=1','--latency-msec=30'],stdout=audio)
        try:
            deadline=time.monotonic()+4
            while not pcm.stat().st_size:
                if recorder.poll() is not None or time.monotonic()>deadline:
                    raise RuntimeError('Private monitor unavailable')
                time.sleep(.04)
            lead=pcm.stat().st_size/(2*RATE)
            first=isolated.request(session,'record-start',name)['first_frame']
            try:
                deadline=time.monotonic()+15
                while isolated.request(session,'status')['frame']<first+435:
                    if time.monotonic()>deadline:raise RuntimeError('VDP stalled')
                    time.sleep(.12)
            finally: stopped=isolated.request(session,'record-stop')
        finally:
            recorder.terminate();recorder.wait(timeout=4)
    rgb=root/'evidence'/(name+'.rgb');frames=stopped['recorded_frames']
    elapsed=stopped['capture_elapsed_ns']/1e9
    assert isolated.verify_audio_route(meta) and rgb.stat().st_size==frames*256*192*3
    signal=pcm.read_bytes()[round(lead*RATE)*2:]
    assert len(signal)>=(elapsed-.15)*2*RATE and _peak(signal)>0
    path=out/(name+'.mp4')
    subprocess.run(['ffmpeg','-nostdin','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size','256x192',
                '-framerate',str(frames/elapsed),'-i',str(rgb),'-ss',str(lead),'-f','s16le','-ar',str(RATE),
                '-ac','1','-i',str(pcm),'-t',str(elapsed),'-c:v','libx264rgb','-crf','0','-threads','1',
                '-c:a','aac','-b:a','128k',str(path)],check=True)
    return dict(rom_sha256=meta['rom_sha256'],session_id=session.name,frames=frames,seconds=elapsed,
                peak_pcm=_peak(signal),sha256=isolated.sha(path),private_sink=meta['audio_sink'])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--story',action='store_true')
    parser.add_argument('--story-move',choices=NAMES[1:],help='Exercise one spell against the real campaign CPU')
    parser.add_argument('--p2-final',action='store_true')
    parser.add_argument('--trade',action='store_true',help='Read both sides of an equal-time projectile exchange')
    parser.add_argument('--range',action='store_true')
    parser.add_argument('--spell-budget',action='store_true')
    parser.add_argument('--sound',action='store_true',help='Capture the confirmed film and its private PSG output continuously')
    parser.add_argument('--fm',action='store_const',const=True,default=None,
                        help='Enable the FM unit in this private Emulicious session')
    args=parser.parse_args()
    if args.story_move: args.story=True
    build=args.build.resolve();out=args.output.resolve()
    record=json.loads((build/'build_record.json').read_text())
    rom=PROJECT/record['rom_path'];assert isolated.sha(rom)==record['rom_sha256']
    symbols=(build/'obj/master_of_fighters.map').read_text()
    addr=int(re.search(r'^\s*([0-9A-F]{8})\s+_chapter\s+alis_chapter',symbols,re.M)[1],16)
    assert int(re.search(r'^\s*([0-9A-F]{8})\s+_mof_magic\s',symbols,re.M)[1],16)==0xc900
    out.mkdir(parents=True,exist_ok=False)
    isolated.DEFAULT_ROOT=PROJECT.parents[1]/'.runtime/qa'
    session=isolated.start(rom,sms_fm=args.fm)
    log=dict(session_id=session.name,rom_sha256=record['rom_sha256'],steps=[])
    arena_return='-DMOF_ALIS_COMBAT=1' in record['compiler_defines']
    def save():isolated.atomic(out/'observations.json',log)
    def ctl(*pairs):
        return isolated.sequence(session,[dict(p1=a,p2=b,frames=n) for a,b,n in pairs])
    def wait(n):ctl((0,0,n))
    def press(k,n=18):ctl((k,0,5),(0,0,n))
    def ram(a,n):return bytes(isolated.request(session,'read',a,n)['ram'])
    def state():
        raw=ram(0xc770,RECORD_BYTES)
        for _ in range(4):
            if not raw[4]&1:break
            wait(1);raw=ram(0xc770,RECORD_BYTES)
        return decode(raw)
    def event():return ram(0xc900,122)
    def observe(label,screen=False):
        m=event();d=state();ch=list(ram(addr,16))
        timing=ram(0xc7d2,32);status=isolated.request(session,'status')
        row=dict(label=label,vdp=status['frame'],nominal_hz=status['nominal_hz'],
                 publications=int.from_bytes(timing[30:32],'little'),overruns=int.from_bytes(timing[25:27],'little'),
                 min_vcount=timing[0],sealed=timing[28],chapter=ch,duel=d,
                 casts=[list(m[88:100]),list(m[100:112])],hits=list(m[112:114]),guards=list(m[114:116]),
                 reflections=list(m[116:118]),edge=m[118],scene=m[84],dizzy=[m[13],m[32]],spell=[m[0],m[19]],
                 shots=[list(struct.unpack_from('<hb7B',m,38+i*10)) for i in range(4)])
        if screen:
            img=isolated.capture(session,label+'.png')
            for ext in ('.png','.json'):
                src=Path(img['path']).with_suffix(ext);shutil.copyfile(src,out/src.name)
        log['steps'].append(row);save()
        print(label,[d[k]['life'] for k in ('p1','p2')],ch[9:11],row['casts'],flush=True)
        return row
    def gesture(p,dirs,button,hold=4):
        actor=state()['p'+str(p+1)]
        forward=F if actor['facing_right'] else B;back=F^B^forward
        axis={'d':D,'f':forward,'b':back,'x':D|forward,'z':D|back,'-':0}
        steps=[]
        for i,k in enumerate(dirs):
            pad=axis[k] | (button if i==len(dirs)-1 else 0)
            steps.append((pad if p==0 else 0,pad if p else 0,hold if i==len(dirs)-1 else 4))
        ctl(*steps)
    def spell(p,id,dirs,button,hold=4,settle=78):
        before=event()[88+p*12+id];gesture(p,dirs,button,hold);wait(settle)
        row=observe(NAMES[id]+'_'+str(len(log['steps'])))
        if row['casts'][p][id]==before:raise ValueError(f'command not consumed: {p}/{NAMES[id]}')
        return row
    def tick(one=0,two=0):
        # Stop just after the next complete fighter publication. Natural
        # hitstop still consumes publications while its logical tick is held.
        isolated.request(session,'input',one,two,0)
        stamp=ram(0xc774,1)[0]
        isolated.request(session,'sample-commit',0xc774,((stamp|1)+1)&255,8)

    def capture_film(prefix):
        seen=set()
        for _ in range(160):
            wait(5);scene=event()[84]
            if scene and scene not in seen:
                # The first completed scan after display-on can still be blank.
                wait(2)
                if event()[84]==scene:
                    observe(prefix+str(scene),True)
                    seen.add(scene)
            if 7 in seen and not scene:break
        return seen

    def record_final(player):
        isolated.request(session,'record-steps-start','guardioes')
        try:
            gesture(player,'dxfdxf',TWO)
            if '-DMOF_ALIS_FEEDBACK=1' in record['compiler_defines']:
                samples=[]
                for _ in range(35):
                    left,duration,owners,presented=ram(0xc800,4)
                    samples.append(dict(vdp=isolated.request(session,'status')['frame'],left=left,
                        duration=duration,owners=owners,presented=presented,
                        tick=int.from_bytes(ram(0xc776,2),'little'),clock=list(ram(addr+7,2))))
                    if left and presented and not (out/'hiperpausa.png').exists():
                        focus_actor=state()['p'+str(player+1)]
                        result=isolated.capture(session,'hiperpausa.png')
                        shutil.copyfile(result['path'],out/'hiperpausa.png')
                    if not duration and presented==12:break
                    wait(1)
                active=[s for s in samples if s['duration']==12 and s['owners']==1<<player and s['presented']]
                log['guardians_pause']=samples
                save()
                assert active and len({s['tick'] for s in active})==1
                assert len({tuple(s['clock']) for s in active})==1
                assert samples[-1]['duration']==0 and samples[-1]['presented']==12
            seen=capture_film('plano_')
            if arena_return:
                target='p'+str(2-player)
                returned=[]
                for _ in range(105):
                    wait(1)
                    raw=ram(0xc770,RECORD_BYTES)
                    if raw[:4]!=b'MFD1' or raw[4]&1:
                        continue
                    d=decode(raw)
                    phase=ram(addr+5,1)[0]
                    actor=d[target]
                    returned.append(dict(phase=phase,state=actor['state'],pivot=actor['pivot'],
                                         vdp=isolated.request(session,'status')['frame']))
                    if phase==4 and actor['state']==5 and not (out/'retorno_arena.png').exists():
                        observe('retorno_arena',True)
                    if phase==3 and actor['state']==4:
                        break
                log['arena_return']=returned
                airborne=[row for row in returned if row['phase']==4 and row['state']==5]
                grounded=[row for row in returned if row['phase']==4 and row['state']==6]
                assert airborne and grounded and returned[-1]['phase']==3
                assert grounded[0]['pivot'][1]>airborne[0]['pivot'][1]
                assert grounded[0]['pivot'][0]!=airborne[0]['pivot'][0]
        finally:
            log['movie']=isolated.request(session,'record-steps-stop')
        if '-DMOF_ALIS_FEEDBACK=1' in record['compiler_defines']:
            from replay_alis_feedback import focus_in_scanout
            origin=log['movie']['first_frame']+1
            native_frames=range(samples[0]['vdp']-origin,samples[-1]['vdp']-origin+1)
            log['foco']=focus_in_scanout(session/'evidence/guardioes',out,focus_actor,native_frames)
        log['finisher_player']=player+1
        log['seen']=sorted(seen)
        save()
        subprocess.run(['ffmpeg','-v','error','-threads','1','-framerate','60','-i',
                        str(session/'evidence/guardioes/%06d.png'),'-c:v','libx264','-threads','1',
                        '-pix_fmt','yuv420p',str(out/'guardioes.mp4')],check=True)
        return seen

    def campaign_finish(name):
        # Both thresholds are earned against the campaign AI. Release the
        # direction on each wake-up and sample the next committed input.
        want_final=name=='guardioes'
        last_pair=None
        saw_stun=False
        for turn in range(3300):
            ch=ram(addr,16);m=event();d=state()
            one,two=d['p1'],d['p2']
            hp,foe=one['life'],two['life']
            forward=F if one['facing_right'] else B
            back=forward^F^B
            gap=abs(one['pivot'][0]-two['pivot'][0])
            if want_final and not saw_stun and m[98] and m[32]:
                observe('historia_tontura',True)
                saw_stun=True
            if m[88+(11 if want_final else 10)]:
                if want_final:
                    # The regular fighter record stops publishing during the film.
                    # Advance the VDP itself across the cut from the duel.
                    for _ in range(90):
                        if event()[83]==1 and life(1)==0:break
                        wait(2)
                    assert event()[83]==1 and life(1)==0
                row=observe('historia_'+name,True)
                if want_final:
                    seen=capture_film('historia_plano_')
                    # Scene 7 gives way to a display-off upload of the epilogue.
                    wait(48)
                    observe('historia_epilogo',True)
                    press(TWO,64)
                    result=observe('historia_final_confirmado',True)
                    assert seen==set(range(1,8)) and result['chapter'][3:5]==[1,0]
                else:assert row['dizzy'][1]
                return
            assert ch[0] and ch[5]==2 and hp,(name,turn,hp,foe)
            if (hp,foe)!=last_pair:
                observe('vida_'+str(turn))
                last_pair=(hp,foe)
            if one['state'] or m[0] or m[11]:
                # A held retreat covers the first actionable frame after a
                # knockdown; blocking low also protects against the CPU sweep.
                tick(back|D if one['state'] and hp<=35 else back)
                continue
            if foe>=25:
                if m[45] or two['pivot'][1]<104 or gap>82:
                    tick(forward if gap>82 else back)
                else:
                    for pad in (D,0,D|ONE):tick(pad)
                    # A strong Fire is selected after the real six-tick hold.
                    for _ in range(7):tick(D|ONE)
                continue
            if hp>25:
                # Standing close is sufficient to invite the next hit.
                tick(forward)
                continue
            if ch[9]<8:
                if m[15]:tick(back)
                else:
                    for pad in (back,0,back|TWO):tick(pad)
                continue
            if m[32] and want_final:
                gesture(0,'dxfdxf',TWO)
                wait(5)
                continue
            if two['state']==0 and two['pivot'][1]==144:
                for pad in (forward,back,forward|ONE):tick(pad)
            else:tick(back|D)
        raise RuntimeError('Campaign command window timed out: '+name)

    def story_move(name):
        move=NAMES.index(name)
        commands={1:('d-d',ONE,3),2:('d-d',ONE,16),3:('dxf',48,4),4:('dzb',TWO,4),
                  5:('d-d',TWO,4),6:('dxf',ONE,4),7:('fdx',ONE,4),8:('b-b',TWO,4),
                  9:('dzb',ONE,4),10:('fbf',ONE,4),11:('dxfdxf',TWO,4)}
        if move in (10,11):return campaign_finish(name)
        initial=event()[88+move]
        for attempt in range(650):
            ch=ram(addr,16);m=event();duel=state()
            hp=duel['p1']['life'];enemy=duel['p2']['life']
            assert ch[0] and ch[5]==2,(name,attempt,hp,enemy)
            if m[88+move]!=initial:
                row=observe('historia_'+name,True)
                return row
            if duel['p1']['state']!=0 or m[0] or m[11]:
                wait(3)
                continue
            choice=move
            if ch[9] < {3:4,4:4,5:2}.get(move,0):
                choice=8 if not m[15] else 2
            if choice==5 and hp==100:
                wait(4)
                continue
            gesture(0,*commands[choice])
            wait(6)
        raise RuntimeError('Campaign CPU: no cast of '+name)
    def life(p):return state()['p'+str(p+1)]['life']
    try:
        wait(60);press(ONE);press(1);press(ONE);press(D);press(F);press(TWO)
        if args.story:
            press(D);press(ONE);press(TWO,160)
        else:
            press(1);press(ONE,165)
        for _ in range(24):
            if ram(addr,16)[5]==2 and ram(0xc770,4)==b'MFD1':break
            wait(8)
        ch=list(ram(addr,16));assert ch[5]==2 and ch[2]==1 and bool(ch[0])==args.story,ch
        observe('arena',True)
        if args.story_move:
            story_move(args.story_move)
            return
        if args.story:
            spell(0,1,'d-d',ONE,3,32)
            observe('historia_fire',True);return
        if args.trade:
            before=observe('antes_da_troca')
            ctl((D,D,4),(0,0,4),(D|ONE,D|ONE,16))
            samples=[]
            for _ in range(110):
                wait(1)
                raw=ram(0xc770,RECORD_BYTES)
                if raw[4]&1:continue
                d=decode(raw)
                m=event()
                published=int.from_bytes(ram(0xc7f0,2),'little')
                if samples and samples[-1]['published']==published:continue
                samples.append(dict(published=published,tick=d['logic_tick'],
                    life=[d[k]['life'] for k in ('p1','p2')],
                    contacts=[d[k]['contact'] for k in ('p1','p2')],
                    hits=list(m[112:114]),meter=list(ram(addr+9,2)),
                    ages=[m[1],m[20]],shot_ages=[m[44],m[64]]))
                if samples[-1]['life']==[90,90] and len(samples)>40:break
            after=observe('depois_da_troca',True)
            log['troca']=samples
            save()
            both=next(r for r in samples if r['contacts']==[1,1])
            frozen=[r for r in samples if r['tick']==both['tick']]
            assert after['hits']==[1,1] and after['chapter'][9:11]==[2,2]
            assert before['chapter'][9:11]==[0,0] and both['life']==[90,90]
            resumed=next(r for r in samples if r['tick']==both['tick']+1)
            # A VDP stop may fall inside an odd seqlock record. Bracket the
            # complete freeze by the ROM's publication counter, even then.
            assert resumed['published']-both['published']-1==11 and len(frozen)>2
            assert all(r['contacts']==[0,0] and r['meter']==[2,2]
                and r['ages']==both['ages'] and r['shot_ages']==both['shot_ages'] for r in frozen[1:])
            return
        if args.p2_final:
            for p in (0,1):
                for _ in range(12):
                    if life(1-p)<25:break
                    spell(p,2,'d-d',ONE,16)
                assert 0<life(1-p)<25
            assert ram(addr,16)[10]==8
            ctl((B,F,45),(0,0,14))
            gesture(1,'fbf',ONE);wait(28)
            r=observe('p1_tonta',True);assert r['dizzy'][0]>0
            before=state()['p2']['pivot'][0]
            assert record_final(1)==set(range(1,8))
            r=observe('final_p2')
            assert r['chapter'][3:5]==[0,1] and r['duel']['p1']['life']==0 and r['duel']['p2']['pivot'][0]<before
            wait(420)
            observe('vitoria_p2',True);return
        if args.spell_budget:
            # Resource preparation is part of this ROM run. Both pads then cast
            # simultaneously; the long distance prevents their ordinary Fire from ending the match.
            for _ in range(4):
                spell(0,1,'d-d',ONE,3)
            ctl((B,F,168),(0,0,25))
            for n in range(65):
                before=observe('janela_'+str(n))
                flags=before['chapter'][9:11]
                if min(flags)>=4:
                    both=[(D,D,4),(D|F,D|B,4),(F|48,B|48,4)]
                elif n%3==0:
                    both=[(B,F,4),(0,0,4),(B|TWO,F|TWO,4)]
                else:
                    both=[(D,D,4),(0,0,4),(D|ONE,D|ONE,4)]
                ctl(*both,(B,F,100),(0,0,8))
                after=observe('fim_'+str(n))
                count=after['publications']-before['publications']
                elapsed=after['vdp']-before['vdp']
                log.setdefault('janelas_magias',[]).append(dict(fps=after['nominal_hz']*count/elapsed,
                            publicados=count,vdp=elapsed,derramamentos=after['overruns']-before['overruns'],
                            ativo=before['chapter'][5]==after['chapter'][5]==2))
                if after['sealed']:break
                assert after['chapter'][5]==2
            assert after['sealed'] and any(after['casts'][1][j] for j in (1,2,3)) and after['casts'][0][3]
            log['pior_quadro_magias']=dict(selado=after['sealed'],vcount_min=after['min_vcount'],overruns=after['overruns'])
            return
        if args.range:
            for _ in range(4):spell(0,2,'d-d',ONE,15)
            ctl((B,F,165),(0,0,18))
            r=observe('extremos')
            header=next(PROJECT/f for f in record['input_sha256'] if f.endswith('/duel_mirror_assets.h'))
            margin=int(re.search(r'#define MOF_DUEL_ARENA_MARGIN (\d+)u',header.read_text())[1])
            assert [r['duel'][k]['pivot'][0] for k in ('p1','p2')]==[margin,255-margin]
            gesture(0,'dxf',48)
            trace=[];jump=False
            for i in range(148):
                m=event()
                x0,y0=struct.unpack_from('<h',m,38)[0],m[41]
                x1,y1=struct.unpack_from('<h',m,48)[0],m[51]
                if m[45] and m[55]:
                    trace.append([x0,y0,x1,y1])
                    if len(trace)==15:observe('chamas_no_meio',True)
                if not jump and m[45] and x0>=r['duel']['p2']['pivot'][0]-53:
                    ctl((0,1,7));jump=True
                else:wait(1)
                if m[118]>=2:break
            log['curvas']=trace
            end=observe('saidas')
            assert end['edge']==2 and len({z[1] for z in trace})>=8 and any(z[1]!=z[3] for z in trace)
            return
        # No RAM injection. Negative attempt at full health, then build the two meters through play.
        gesture(0,'dxfdxf',TWO);wait(55)
        assert not event()[99]
        spell(0,8,'b-b',TWO)
        spell(0,1,'d-d',ONE,3)
        spell(1,2,'d-d',ONE,15)
        spell(0,5,'d-d',TWO)
        spell(1,6,'dxf',ONE)
        spell(0,7,'fdx',ONE,4,98)
        # Put space between the actors for a timed projectile reflection.
        for _ in range(60):
            pivots=state()
            if pivots['p2']['pivot'][0]-pivots['p1']['pivot'][0]>=72:break
            tick(B,F)
        wait(10)
        gesture(0,'dxf',ONE)
        for _ in range(40):
            m=event()
            x=struct.unpack_from('<h',m,38)[0]
            if m[45] and state()['p2']['pivot'][0]-x<=52:break
            tick()
        else:raise RuntimeError('The wave did not reach the reflection setup')
        for pad in (D,D,D|F,D|F,F|ONE,F|ONE):
            tick(0,pad)
        wait(84)
        assert observe('reflexao')['reflections'][1]>0
        # Bring the closest edges back into range for the animal and exchanges.
        ctl((F,B,35),(0,0,24))
        for _ in range(5):
            if ram(addr,16)[9]>=4:break
            spell(0,1,'d-d',ONE,3)
        ctl((B,F,32),(0,0,14))
        gesture(0,'dxf',48)
        for _ in range(35):
            wait(1)
            raw=event()
            if raw[45] and raw[55] and raw[38:40]!=b'\0\0':
                wait(3);break
        observe('duas_chamas',True);wait(106)
        ctl((F,B,34),(0,0,18))
        # Build Myau's cost with Chat or P2 hits, avoiding an early KO.
        for _ in range(5):
            if ram(addr,16)[9]>=4:break
            if life(0)>40:spell(1,2,'d-d',ONE,15)
            else:spell(0,8,'b-b',TWO,4,180)
        gesture(0,'dzb',TWO)
        for i in range(7):
            wait(8);observe('myau_'+str(i),True)
        wait(95)
        # Repeated midrange Fire is reproducible and the two strengths let us approach both thresholds.
        ctl((F,B,24),(0,0,10))
        for p in (1,0):
            for _ in range(16):
                if life(1-p)<25:break
                old=life(1-p);spell(p,2,'d-d',ONE,15)
                if life(1-p)==old:ctl((F,B,22),(0,0,14))
            assert 0<life(1-p)<25
        for _ in range(8):
            if ram(addr,16)[9]==8:break
            spell(0,8,'b-b',TWO,4,205)
        wait(48)
        assert event()[99]==0
        # Separate before the stun so the desperation lunge has to travel.
        ctl((B,F,40),(0,0,12))
        gesture(0,'fbf',ONE);wait(5);stun=observe('atordoamento',True)
        assert stun['dizzy'][1]>0
        wait(25)
        if args.sound:
            gesture(0,'dxfdxf',TWO)
            log['audiovisual']=record_cinema(session,out)
            observe('vitoria_com_som',True)
            return
        seen=record_final(0)
        wait(24)
        r=observe('vitoria',True)
        assert seen==set(range(1,8)) and r['chapter'][3:5]==[1,0] and r['duel']['p2']['life']==0
        press(ONE,148)
        for _ in range(45):
            if ram(addr,16)[5]==2 and ram(0xc770,4)==b'MFD1' and life(1)==100:break
            wait(4)
        r=observe('revanche',True);assert r['chapter'][5]==2 and r['duel']['p2']['life']==100
    finally:
        isolated.close_session(session);log['closed']=isolated.load(session)[1]['state']
        shutil.copyfile(session/'commands.jsonl',out/'commands.jsonl')
        save()

if __name__=='__main__':main()
