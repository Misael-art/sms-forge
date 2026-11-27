"""Exercise the chapter through controller ports and collect SHA-bound native media."""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
WRAPPER = PROJECT.parents[1] / 'tools/sms_wrapper'
sys.path.insert(0, str(WRAPPER))
from session_bridge import isolated
from capture_audio import capture_session
from measure_worst_frame import analyze_snapshot
from duel_probe import decode, RECORD_BYTES
from replay_duel_round import snapshot_sat


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path, help='build directory with the ROM, record and map')
    parser.add_argument('out',type=Path)
    parser.add_argument('--case',choices=('story','versus','budget','worst','acting','port-versus','impact','combo'),
                        default='story')
    parser.add_argument('--fm',action='store_const',const=True,default=None,
                        help='Enable the FM unit in this private Emulicious session')
    args=parser.parse_args()
    build=args.candidate.resolve()
    record=json.loads((build/'build_record.json').read_text())
    rom=PROJECT/record['rom_path']
    if isolated.sha(rom)!=record['rom_sha256']:
        raise ValueError('Cartridge differs from build receipt')
    symbols=(build/'obj/master_of_fighters.map').read_text()
    addr=int(re.search(r'^\s*([0-9A-F]{8})\s+_chapter\s+alis_chapter',symbols,re.M)[1],16)
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=False)
    # The bridge accepts an absolute session directory. Keep videos, scratch
    # images and X credentials on the project disk, with the protocol's 0700.
    isolated.DEFAULT_ROOT=PROJECT.parents[1]/'.runtime/qa'
    session=isolated.start(rom,sms_fm=args.fm)
    log={'session_id':session.name,'rom_sha256':record['rom_sha256'],'case':args.case,'steps':[]}
    def save():
        isolated.atomic(out/'observations.json',log)
    def controls(*pairs):
        return isolated.sequence(session,[dict(p1=p1,p2=p2,frames=n) for p1,p2,n in pairs])
    def press(key,settle=20):
        controls((key,0,4),(0,0,settle))
    def ram(address,length):
        return bytes(isolated.request(session,'read',address,length)['ram'])
    def state():
        return list(ram(addr,16))
    def observe(name,frame=True):
        row={'id':name,'vdp_frame':isolated.request(session,'status')['frame'],'chapter':state()}
        raw=ram(0xc770,RECORD_BYTES)
        if row['chapter'][5] in (2,3) and int.from_bytes(ram(0xc7f0,2),'little') and raw[:4]==b'MFD1' and not raw[4]&1:
            row['duel']=decode(raw)
            row['action']=list(ram(0xc7ca,2))
            if frame and row['duel']['logic_tick'] and row['chapter'][5] in (2,3):
                row['sat']=snapshot_sat(session)
        sample=ram(0xc7d2,32)
        row['publish_probe_hex']=sample.hex()
        row['cadence_vcount']=list(sample[2:6])
        row['chapter_stage_vcount']=list(ram(0xc7cc,6))
        row['late_poses']=int.from_bytes(sample[6:8],'little')
        row['missed_vblanks']=int.from_bytes(sample[12:14],'little')
        row['published_frames']=int.from_bytes(sample[30:32],'little')
        if frame:
            shot=isolated.capture(session,name+'.png')
            for suffix in ('.png','.json'):
                shutil.copy2(Path(shot['path']).with_suffix(suffix),out/(name+suffix))
        log['steps'].append(row)
        save()
        print(name,row['vdp_frame'],row['chapter'],flush=True)
        return row
    def sound(name,secs):
        code=capture_session(session,secs,name)
        for suffix in ('.wav','.audio.json'):
            path=session/(name+suffix)
            if path.exists(): shutil.copy2(path,out/path.name)
        log.setdefault('audio',{})[name]=code
        save()
    try:
        controls((0,0,60))
        observe('titulo')
        if args.case=='story': sound('tema_titulo',6)
        press(16)
        observe('menu')
        if args.case=='story':
            press(1)
            press(16)
            observe('opcoes')
            press(2)
            press(8)
            press(32)
            press(2)
            press(16)
            for i in range(4):
                observe('dialogo_'+str(i+1))
                press(16,28 if i==3 else 20)
        else:
            if args.case in ('versus','worst','acting','port-versus','impact','combo'): press(2)
            press(16)
            if args.case=='budget': press(32,28)
        observe('apresentacao')
        if args.case not in ('story','budget') and '-DMOF_ALIS_MATCHUP=1' in record['compiler_defines']:
            press(16,4)  # capture the visible card before the arena load blanks the display
        for _ in range(40):
            phase=state()[5]
            if phase==1 and state()[6]>=5 and not any(row['id']=='fight' for row in log['steps']):
                observe('fight')
            if phase==2 and int.from_bytes(ram(0xc7f0,2),'little')>1:
                break
            controls((0,0,4))
        if state()[5]!=2:
            raise RuntimeError(f'Fight failed to reach gameplay: {state()}')
        arena_frame=observe('arena')
        if args.case=='combo':
            # Drive both fighters through their controller ports and inspect
            # the published duel state and visible HUD cells.
            def until(keys, predicate, limit):
                duel_state=None
                for _ in range(limit):
                    controls((*keys,1))
                    raw=ram(0xc770,RECORD_BYTES)
                    if raw[:4]==b'MFD1' and not raw[4]&1:
                        duel_state=decode(raw)
                        if predicate(duel_state):
                            return duel_state
                log['failed_input']={'keys':keys,'last_probe':duel_state,'hits':list(ram(addr+16,2))}
                save()
                raise AssertionError(('combo timeline',keys,duel_state))
            digit_header=next(k for k in record['input_sha256'] if k.endswith('/alis_pages.h'))
            digits=int(re.search(r'#define MOF_DIGIT_TILE (\d+)u',(PROJECT/digit_header).read_text())[1])
            for side in range(2):
                name='p'+str(side+1)
                rival='p'+str(2-side)
                def pad(key):
                    return (0,key) if side else (key,0)
                def hud():
                    column=23 if side else 7
                    values=isolated.request(session,'read-vram',0x3800+2*(64+column),4)['vram']
                    return [values[j]|(values[j+1]<<8) for j in (0,2)]
                at_range=until(pad(4 if side else 8),
                      lambda s: abs(s[name]['pivot'][0]-s[rival]['pivot'][0])==24,180)
                controls((0,0,3))
                until(pad(16),lambda s:s[name]['state']==1,30)
                first=until((0,0),lambda s:s[rival]['state']==3,30)
                assert first[rival]['life']==at_range[rival]['life']-10
                assert ram(addr+16+side,1)[0]==1
                # The port is sampled ahead of probe publication. A two-frame
                # tap here arrives on the transition to READY in the cartridge.
                until((0,0),lambda s:s[name]['state']==1 and s[name]['action_tick']==16,80)
                controls((*pad(16),2))
                second=until((0,0),lambda s:s[rival]['life']==first[rival]['life']-6,40)
                assert second[rival]['free_since']==first[rival]['free_since']
                until((0,0),lambda s:hud()==[digits+10,digits+2],8)
                row=observe(name+'_dois_hits');row['combo']=list(ram(addr+16,2))
                row['hud_tiles']=hud();row['first_hit']=first;row['second_hit']=second
                assert row['combo'][side]==2 and row['combo'][1-side]==0
                until((0,0),lambda s:s[rival]['can_act'] and not ram(addr+16+side,1)[0],60)
                until((0,0),lambda s:hud()==[digits+10,digits+10],8)
                observe(name+'_livre',False)
            save()
        elif args.case=='port-versus':
            if state()[0]:
                raise RuntimeError('Versus sequence entered the story mode')
            from PIL import Image, ImageChops
            from make_duel_scene02_assets import pixels
            from stage_alis_postures import rgb
            # Boot exposes the complete neutral pair. Check the visible SAT
            # against the packets in this exact cartridge, including overlaps.
            header=next(p for p in record['input_sha256'] if p.endswith('/duel_mirror_assets.h'))
            plan=json.loads((PROJECT/header).with_name('repertoire-pages.json').read_text())
            rom_data=rom.read_bytes()
            idle=[next(f for f in plan['frames'] if f['name']=='idle' and f['player']==i
                       and f['right']==(i==0)) for i in range(2)]
            vram=bytes(isolated.request(session,'read-vram',0,8192)['vram'])
            expected={}
            for obj in reversed(arena_frame['sat']['objects']):
                slot=obj['slot']
                pose=idle[slot//128]
                off=pose['bank']*16384+pose['address']-0x8000+17+2*pose['count']+32*(slot%32)
                packet=rom_data[off:off+32]
                if vram[slot*32:slot*32+32]!=packet:
                    raise ValueError(f'Idle sprite pattern in VRAM differs from cartridge at slot {slot}')
                for n,color in enumerate(pixels(packet)):
                    if color:
                        expected[obj['x']+n%8,obj['y']+n//8]=tuple(rgb(plan['palette'][color]))
            with Image.open(out/'arena.png') as shot:
                frame=shot.convert('RGB')
                mismatch=sum(frame.getpixel(xy)!=c for xy,c in expected.items())
            log['dupla_em_guarda']={'pixels':len(expected),'divergentes':mismatch}
            save()
            if mismatch:
                raise ValueError(f'{mismatch} fighter pixels differ from cartridge')
            for label, direction in (('oeste',4),('leste',8)):
                controls((direction,direction,90),(0,0,8))
                observe('pista_'+label)
            # Compare features away from the fighters at the two camera limits.
            with Image.open(out/'pista_oeste.png') as west, Image.open(out/'pista_leste.png') as east:
                shifts = {}
                for name, box in [('hud',(20,0,56,8)), ('nave',(41,58,75,79)),
                                  ('piso',(25,161,100,189))]:
                    x,y,r,b=box
                    feature=west.crop(box).convert('RGB')
                    if len(feature.getcolors(1024) or [])<2:
                        raise ValueError('No identifiable feature in '+name)
                    offsets = [dx for dx in range(-32,33) if x+dx>=8 and r+dx<=256
                               and ImageChops.difference(feature,east.crop((x+dx,y,r+dx,b)).convert('RGB')).getbbox() is None]
                    if len(offsets)!=1:
                        raise ValueError(f'Ambiguous raster displacement for {name}: {offsets}')
                    shifts[name]=offsets[0]
                log['deslocamento_px']=shifts
                save()
                if not (shifts['hud']==0 and shifts['piso']<shifts['nave']<0):
                    raise ValueError(f'Unexpected raster movement: {shifts}')
        elif args.case=='impact':
            # One VDP frame per step. Each new publication is one rules step,
            # so a freeze shows as publications that keep the same logic tick.
            def sample():
                # A pause can land inside the probe write. That sample is
                # skipped; the next VDP frame carries the finished record.
                raw=ram(0xc770,RECORD_BYTES)
                if raw[:4]!=b'MFD1' or raw[4]&1: return None
                duel=decode(raw)
                counters=ram(0xc7d2,32)
                return dict(vdp=isolated.request(session,'status')['frame'],
                            published=int.from_bytes(counters[30:32],'little'),
                            tick=duel['logic_tick'],chapter=state(),
                            p1={k:duel['p1'][k] for k in ('state','contact','life','pivot','action_tick')},
                            p2={k:duel['p2'][k] for k in ('state','contact','life','pivot','action_tick')})
            def both_ready():
                for _ in range(120):
                    row=sample()
                    if row and row['p1']['state']==0 and row['p2']['state']==0: return
                    controls((0,0,1))
                raise RuntimeError('Fighters did not recover')
            def close_in():
                both_ready()
                for _ in range(90):
                    row=sample()
                    if row and row['p2']['pivot'][0]-row['p1']['pivot'][0]<=25: break
                    controls((8,4,1))
                controls((0,0,6))
                both_ready()
            def exchange(name,p1_keys,p2_keys,video=False):
                close_in()
                meter_before=state()[9:11]
                if video: begin=isolated.request(session,'record-steps-start',name)
                rows=[]
                try:
                    for keys,frames in p1_keys:
                        for _ in range(frames):
                            controls((keys,p2_keys,1))
                            rows.append(sample())
                    for _ in range(90):
                        controls((0,p2_keys,1))
                        rows.append(sample())
                        valid=[r for r in rows if r]
                        if valid and valid[-1]['p2']['state']==0 and any(r['p1']['contact'] for r in valid): break
                finally:
                    if video: stop=isolated.request(session,'record-steps-stop')
                skipped=sum(1 for row in rows if not row)
                published=[]
                for row in filter(None,rows):
                    if not published or row['published']!=published[-1]['published']: published.append(row)
                log.setdefault('impact_trace',{})[name]=published
                save()
                # The contact flag lives for one step. The defender entering
                # hit or block confirms the same step when that sample is lost.
                hit=next((i for i,row in enumerate(published) if row['p1']['contact'] in (1,2) or
                          (i and row['p2']['state'] in (2,3) and published[i-1]['p2']['state']==0)),None)
                if hit is None: raise RuntimeError(f'{name}: no contact in {len(published)} publications')
                contact=published[hit]
                # Every free step advances the tick once per publication, so the
                # freeze is the growth of (publications - tick) across contact.
                # The mode ignores a sample read between counter and record.
                from collections import Counter
                def drift(rows):
                    return Counter(r['published']-r['tick'] for r in rows).most_common(1)[0][0]
                frozen=drift([r for r in published if r['tick']>contact['tick']])- \
                       drift([r for r in published if r['tick']<contact['tick']])
                free=next(row for row in published[hit+1:] if row['p2']['state']==0)
                xs=[row['p2']['pivot'][0] for row in published[hit:hit+frozen+1]]
                result=dict(contact=contact['p1']['contact'] or {3:1,2:2}.get(contact['p2']['state'],0),
                    contact_flag_seen=bool(contact['p1']['contact']),contact_tick=contact['tick'],
                    defender_state=contact['p2']['state'],damage=published[hit-1]['p2']['life']-contact['p2']['life'],
                    frozen_publications=frozen,stun_ticks=free['tick']-contact['tick'],
                    frozen_pivot_x=xs,repeated_contact=sum(1 for row in published[hit+1:hit+frozen+1] if row['p1']['contact']),
                    meter_before=meter_before,meter_after=state()[9:11],skipped_partial=skipped,
                    publications=published)
                if video:
                    clip=out/(name+'.mp4')
                    subprocess.run(['ffmpeg','-nostdin','-v','error','-framerate',str(stop['nominal_hz']),
                        '-i',str(session/f'evidence/{name}/%06d.png'),'-threads','1','-c:v','libx264rgb',
                        '-crf','0',str(clip)],check=True)
                    result['video']=dict(first=begin['first_frame'],last=stop['frame'],
                        frames=stop['recorded_frames'],sha256=isolated.sha(clip),method='stepped native framebuffer')
                log.setdefault('impact',{})[name]=result
                save()
                print(name,{k:v for k,v in result.items() if k!='publications'},flush=True)
                observe(name)
                return result
            # Light: a tap released before the six-tick hold. Heavy: a held 1.
            light=exchange('leve_acerto',[(16,3)],0)
            heavy=exchange('forte_acerto',[(16,16)],0,video=True)
            guard=exchange('forte_defendido',[(16,16)],8)
            checks={
                'leve': light['contact']==1 and light['frozen_publications']==4 and light['stun_ticks']==10,
                'forte': heavy['contact']==1 and heavy['frozen_publications']==11 and heavy['stun_ticks']==20,
                'defesa': guard['contact']==2 and guard['frozen_publications']==11 and guard['stun_ticks']==3,
                'tremor_forte': len(set(heavy['frozen_pivot_x']))>=2,
                'sem_tremor_leve': len(set(light['frozen_pivot_x']))==1,
                'sem_tremor_defesa': len(set(guard['frozen_pivot_x']))==1,
                'contato_unico': not (light['repeated_contact'] or heavy['repeated_contact'] or guard['repeated_contact']),
                'medidor_unico': all(r['meter_after'][0]-r['meter_before'][0]<=1 and r['meter_after'][1]-r['meter_before'][1]<=1
                                     for r in (light,heavy,guard)),
            }
            log['impact_checks']=checks
            save()
            if not all(checks.values()): raise RuntimeError(f'Impact checks failed: {checks}')
        elif args.case=='budget':
            isolated.request(session,'input',6,0,0)
            observe('guarda_inicio',False)
            cmd=[sys.executable,str(WRAPPER/'measure_runtime_probe.py'),'--session',str(session),
                 '--rom',str(rom),'--project',str(PROJECT),'--seconds','4','--janelas','3','--out','fps']
            log['fps_exit']=subprocess.run(cmd).returncode
            observe('guarda_fim',False)
            isolated.request(session,'input',0,0,0)
        elif args.case=='worst':
            # Start at contact, then exercise both complete render paths at range.
            controls((24,4,9),(0,0,19),(6,2,5),(0,20,7),(0,0,14))
            observe('contato')
            mixed_contact=[(8,4,14),(16,32,7),(0,0,10),(2,2,5),
                           (24,20,5),(0,0,19),(8,4,8),(32,16,4),
                           (0,0,13),(6,10,9),(8,4,8),(16,32,3),(0,0,15)]
            assert sum(row[2] for row in mixed_contact)==120
            for i in range(3):
                before=observe(f'carga_inicio_{i+1}',False)
                ack=controls(*mixed_contact)
                after=observe(f'carga_fim_{i+1}')
                elapsed=after['vdp_frame']-before['vdp_frame']
                if elapsed!=120: raise RuntimeError('VDP timeline mismatch')
                delta=(after['published_frames']-before['published_frames'])&65535
                log.setdefault('mixed_fps',[]).append(dict(vdp=elapsed,publications=delta,
                    nominal_hz=ack['nominal_hz'],fps=ack['nominal_hz']*delta/elapsed,
                    active=before['chapter'][5]==after['chapter'][5]==2))
                save()
            controls((4,8,42))
            mixed=[(1,1,4),(16,32,8),(0,0,24),(2,2,4),(24,20,8),
                   (0,0,27),(6,10,12),(16,32,8),(0,0,20)]
            for _ in range(65):
                controls(*mixed)
                if ram(0xc7ee,1)[0]==1: break
            # The seal is read from RAM. A round change can blank the display
            # at this instant, so the screenshot is not part of the verdict.
            try: observe('janela_selada')
            except RuntimeError: observe('janela_selada',False)
            counters=ram(0xc7d2,32)
            log['worst_window']={'done':counters[28], 'min_vcount':counters[0],
                'overruns':int.from_bytes(counters[25:27],'little'),
                'frames':int.from_bytes(counters[30:32],'little'),
                'session_id':session.name,'rom_sha256':record['rom_sha256']}
            log['worst_window']['first_overrun']={'start_upload_bg_sat':list(ram(0xc7c0,4)),
                'end_pnt':list(ram(0xc7dc,2))}
            log['worst_window']['judgment']=analyze_snapshot(
                counters[0],int.from_bytes(counters[25:27],'little'),counters[28],
                int.from_bytes(counters[30:32],'little'))
            save()
            if counters[28]!=1: raise RuntimeError('The 3,000-frame window did not seal')
        elif args.case=='acting':
            reached=set()
            for _ in range(300):
                controls((0,0,2))
                idle=state()[11]
                if idle<170: continue
                raw=ram(0xc770,RECORD_BYTES)
                if raw[4]&1: continue
                actor=decode(raw)['p1']
                pose=actor['pose_presented']
                if pose in (77,78,79) and pose not in reached:
                    observe('escuta_pose_'+str(pose))
                    reached.add(pose)
                if len(reached)==3: break
            if reached!={77,78,79}:
                raise RuntimeError(f'Long-idle poses seen: {sorted(reached)}')
            for _ in range(12):
                controls((4,0,1))
                raw=ram(0xc770,RECORD_BYTES)
                if not raw[4]&1 and decode(raw)['p1']['keys_consumed']==4:
                    observe('retomada_por_comando')
                    break
            else: raise RuntimeError('Directional input was not consumed')
        elif args.case=='versus':
            for _ in range(75):
                if 184<=state()[11]<204: break
                controls((0,0,8))
            if not 184<=state()[11]<204: raise RuntimeError('Listening idle not reached')
            observe('escuta')
            controls((8,4,12),(0,0,2))
            observe('comando_apos_escuta')
            for side in (0,1):
                forward=8 if not side else 4
                for name,keys in [('normal',[(16,8),(0,24)]),('especial',[(2,3),(forward|16,5),(0,32)]),
                                  ('resposta',[(2,3),((forward^12)|16,5),(0,32)])]:
                    for k,n in keys:
                        controls((k if not side else 0,k if side else 0,n))
                        observe(f'p{side+1}_{name}_{k}',False)
            observe('duelo_local')
            # Both players earn meter from ordinary, unguarded contact. Short
            # taps keep the defender alive for the two follow-up commands.
            for hit in range(22):
                if state()[9]==8 or state()[5]!=2: break
                controls((8,4,12),(16,0,3),(0,0,25))
            observe('medidores')
            for side,front in enumerate((8,4)):
                if state()[9+side]!=8 or state()[5]!=2: continue
                controls((0,0,38))
                for mask,length in ((2,3),(front,3),(2,3),(front|16,4)):
                    controls((mask if side==0 else 0,mask if side==1 else 0,length))
                observe(f'super_p{side+1}')
                controls((0,0,55))
        else:
            # Trace a reproducible exchange on both controller and CPU sides.
            start=isolated.request(session,'record-steps-start','troca')
            try:
                controls((8,0,6),(16,0,8),(0,0,13),(6,0,19),(2,0,3),
                         (24,0,4),(0,0,21),(32,0,8),(0,0,12),(6,0,18))
            finally:
                stop=isolated.request(session,'record-steps-stop')
            clip=out/'troca.mp4'
            frames=stop['recorded_frames']
            if frames!=stop['frame']-start['first_frame'] or frames!=112:
                raise ValueError(f'Timeline and recording disagree: {frames}')
            subprocess.run(['ffmpeg','-nostdin','-v','error','-framerate',str(stop['nominal_hz']),
                '-i',str(session/'evidence/troca/%06d.png'),'-threads','1','-c:v','libx264rgb',
                '-crf','0',str(clip)],check=True)
            log['video']=dict(first=start['first_frame'],last=stop['frame'],frames=frames,
                              sha256=isolated.sha(clip),method='stepped native framebuffer',audio='separate')
            # Locate the recorded arena cell from the exact header the compiler used.
            header,expected=next((name,sha) for name,sha in record['input_sha256'].items()
                                 if name.endswith('/alis_pages.h'))
            generated=PROJECT/header
            if isolated.sha(generated)!=expected:
                raise ValueError('Arena layout header differs from compilation')
            definitions=generated.read_text()
            px,py=(int(re.search(r'#define MOF_SIGN_'+axis+r' (\d+)u',definitions)[1])*8 for axis in ('X','Y'))
            pixels=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-threads','1','-i',str(clip),
                '-vf',f'crop=8:8:{px}:{py}', '-pix_fmt','rgb24','-f','rawvideo','-'])
            patches=[pixels[i:i+192] for i in range(0,len(pixels),192)]
            log['exit_light']={'cell':[px//8,py//8],'frames':len(patches),
                'exposures':len(set(patches)),'changed_on_frames':[i for i in range(1,len(patches)) if patches[i]!=patches[i-1]]}
            observe('troca')
            sound('musica_e_golpes',4)
            # Character state and frame determine the end, independent of host throughput.
            def finish_round(attack):
                for _ in range(125):
                    if state()[5]==3: break
                    if attack:
                        controls((8,0,14),(56,0,4),(0,0,18),(8,0,10),(24,0,9),(0,0,17))
                    else: controls((0,0,96))
                if state()[5]!=3: raise RuntimeError('Round did not resolve within 12,000 VDP frames')

            def result_page(prefix):
                for _ in range(35):
                    if state()[6]>=100: break
                    controls((0,0,12))
                controls((0,0,24))
                if state()[6]!=100: raise RuntimeError('Result interface not reached')
                if state()[13]==0:
                    observe(prefix+'dialogo_final_1')
                    press(16)
                    observe(prefix+'dialogo_final_2')
                    press(16)
                    observe(prefix+'vitoria')
                else: observe(prefix+'derrota')

            finish_round(True)
            observe('fim_round')
            result_page('')
            first_winner=state()[13]
            press(16,110)
            observe('revanche')
            finish_round(first_winner!=0)
            observe('fim_revanche')
            result_page('revanche_')
            press(32)
            observe('retorno_menu')
            from PIL import Image, ImageChops
            with Image.open(out/'menu.png') as initial, Image.open(out/'retorno_menu.png') as returned:
                if ImageChops.difference(initial.convert('RGB'),returned.convert('RGB')).getbbox():
                    raise RuntimeError('Returned screen differs from the known main menu')
        snap=isolated.capture(session,'final.png')
        bundle=isolated.publish(session,'final.png',out/'bundles')
        log['bundle']=str(bundle)
    finally:
        isolated.close_session(session)
        log['closed']=isolated.load(session)[1]['state']
        if (session/'commands.jsonl').exists():
            shutil.copy2(session/'commands.jsonl',out/'commands.jsonl')
        save()

if __name__=='__main__':
    main()
