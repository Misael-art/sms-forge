"""Drive the revised sheet poses and compare the native Emulicious scanout to the art."""
import shutil
import subprocess
from itertools import groupby

from PIL import Image, ImageChops
from duel_probe import RECORD_BYTES, decode
from session_bridge import isolated
from stage_alis_mirror import PELVIS_X, POSES, SECOND_COSTUME, SOURCE, sheet_drawings
from stage_alis_postures import rgb


def proof_images():
    images = {}
    for name, drawing in sheet_drawings(SOURCE.parent / "alis_revisao_ficha").items():
        for player in (0, 1):
            for right in (False, True):
                points = {}
                for (x, y), color in drawing.items():
                    local_x = x - PELVIS_X
                    key = (local_x if right else -local_x-1, y-144)
                    points[key] = SECOND_COSTUME.get(color, color) if player else color
                xs, ys = zip(*points)
                left, top = min(xs), min(ys)
                im = Image.new("RGB", (max(xs)-left+1, max(ys)-top+1))
                mask = Image.new("L", im.size)
                for (x, y), color in points.items():
                    im.putpixel((x-left, y-top), rgb(color))
                    mask.putpixel((x-left, y-top), 255)
                images[POSES.index(name), player, right] = (left, top, im, mask)
    return images


def exercise(case, session, out, controls, ram, log, save):
    walk = case == 'walk-art'
    airborne = case == 'air-guard-art'
    wanted = {42,44,47,66} if airborne else set(range(1,9) if walk else range(54,57))
    shots = []
    misses = {}
    trace = []
    contacts = set()
    damage_events = []
    windows = log['cadencia'] = []
    first_frame = isolated.request(session,'status')['frame']
    first_count = int.from_bytes(ram(0xc7f0,2),'little')
    def sample(p1, p2, count):
        nonlocal first_frame, first_count
        for _ in range(count):
            ack = controls((p1,p2,1))
            frame = ack['frame']
            if frame-first_frame==60:
                total = int.from_bytes(ram(0xc7f0,2),'little')
                publications = (total-first_count)&65535
                windows.append(dict(vdp_inicio=first_frame,vdp_fim=frame,apresentacoes=publications,
                                    fps=ack['nominal_hz']*publications/(frame-first_frame)))
                first_frame, first_count = frame, total
            raw = ram(0xc770, RECORD_BYTES)
            if raw[:4] != b'MFD1' or raw[4] & 1:
                continue
            duel = decode(raw)
            action = ram(0xc7ca, 2)
            trace.append([frame, duel['logic_tick'], *[duel[p]['life'] for p in ('p1','p2')]])
            for player, key in enumerate(('p1','p2')):
                actor = duel[key]
                if actor['contact'] == 1 and action[player] == 12:
                    contacts.add(player)
                target_hp = 3-player
                if not walk and not airborne and len(trace)>1 and trace[-2][target_hp]!=trace[-1][target_hp]:
                    damage_events.append(dict(player=player+1,frame=frame,action=action[player],
                                              pose=actor['pose_requested'],contact=actor['contact'],
                                              damage=trace[-2][target_hp]-trace[-1][target_hp]))
                if actor['pose_presented'] in wanted:
                    shots.append((frame, player, actor['pose_presented'], actor['presented_facing_right'], *actor['pivot']))

    start = isolated.request(session,'record-steps-start',case)
    try:
        if walk:
            # Walk away from and back towards the opponent, retaining facing.
            for _ in range(3):
                sample(4,8,31)
                sample(8,4,31)
        elif airborne:
            sample(4,8,28)
            for a,b in ((1,0),(0,1)):
                for hold in (3,8):
                    sample(a,b,6)
                    sample(16*a,16*b,hold)
                    sample(0,0,45)
            sample(8,4,58)
            for a,b in ((1,0),(0,1)):
                # A low kick reaches the shorter crouching hurtbox.
                # Leave a step between the fighters so the attacking boot
                # does not cover the defender's outline in the native frame.
                sample(4*a,8*b,8)
                sample(2 if a else 6,10 if a else 2,10)
                sample(34 if a else 6,10 if a else 34,10)
                sample(0 if a else 6,10 if a else 0,64)
                sample(8,4,8)
                sample(0,0,6)
        else:
            sample(4,8,28)
            sample(0,0,4)
            # At range each costume is visible for the complete swing.
            for p1,p2 in ((1,0),(0,1)):
                start_shots = len(shots)
                sample(2*p1,2*p2,4)
                sample(24*p1,20*p2,4)
                sample(0,0,45)
                player = 0 if p1 else 1
                misses[player] = [pose for pose,_ in groupby(s[2] for s in shots[start_shots:] if s[1]==player)]
            sample(8,4,55)
            sample(0,0,4)
            for a,b in ((1,0),(0,1)):
                sample(2*a,2*b,4)
                sample(24*a,20*b,4)
                sample(0,0,82)
                sample(8,4,10)
                sample(0,0,4)
        sample(0,0,4)
    finally:
        end = isolated.request(session,'record-steps-stop')
    frames = session/'evidence'/case
    count = end['recorded_frames']
    assert count == end['frame'] - start['first_frame']
    log['movie'] = {'first_frame':start['first_frame'], 'frames':count}
    log['native_trace'] = trace
    log['pose_samples'] = shots
    log['shield_contact_players'] = sorted(contacts)
    if misses:
        log['shield_whiff_poses'] = misses
        log['shield_damage_events'] = damage_events
    save()
    subprocess.run(['ffmpeg','-v','error','-threads','1','-framerate','60','-i',str(frames/'%06d.png'),
                    '-c:v','libx264','-threads','1','-pix_fmt','yuv420p', str(out/(case+'.mp4'))], check=True)
    art = proof_images()
    seen = set()
    results = log['matches'] = []
    for frame, player, pose, right, px, py in shots:
        if (pose,player) in seen:
            continue
        dx, dy, ink, mask = art[pose,player,right]
        x, y = px+dx, py+dy
        for native in range(frame-1,frame+4):
            path = frames/f'{native-start["first_frame"]-1:06d}.png'
            if not path.exists():
                continue
            with Image.open(path) as shot:
                crop = shot.convert('RGB').crop((x,y,x+ink.width,y+ink.height))
            diff = ImageChops.difference(crop, ink)
            if any(ImageChops.multiply(band,mask).getbbox() for band in diff.split()):
                continue
            filename = f'p{player+1}-pose-{pose:02}.png'
            shutil.copyfile(path,out/filename)
            results.append(dict(pose=pose, player=player+1, frame=native, pivot=[px,py],
                                pixels=mask.histogram()[255], file=filename, sha256=isolated.sha(out/filename)))
            seen.add((pose,player))
            break
    save()
    missing = {(pose,p) for pose in wanted for p in (0,1)} - seen
    if missing:
        raise ValueError(f'Sheet cels missing from native scanout: {sorted(missing)}')
    if walk:
        for player in (0,1):
            sequence = [pose for pose,_ in groupby(s[2] for s in shots if s[1]==player)]
            for cycle in ([1,2,3,4],[5,6,7,8]):
                if not any(sequence[i:i+4]==cycle for i in range(len(sequence)-3)):
                    raise ValueError(f'Incomplete walk cycle on P{player+1}: {cycle}, {sequence}')
    elif misses:
        # A VDP sample can land between two completed probe publications.
        # HP is persistent. Attribute each actual loss to its attack and cel.
        if ([(e['player'], e['damage']) for e in damage_events] != [(1,13),(2,13)] or
                any(e['action'] != 12 or not 54 <= e['pose'] <= 56 for e in damage_events) or
                trace[-1][2:] != [87,87]):
            raise ValueError(f'Shield Step contacts or damage differ: {damage_events}, {trace[-1]}')
        if any(poses != [54,55,56] for poses in misses.values()):
            raise ValueError(f'Incomplete Shield Step on miss: {misses}')
