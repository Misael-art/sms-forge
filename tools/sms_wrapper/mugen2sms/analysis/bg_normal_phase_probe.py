"""Generate a phase-specific BG normal diagnostic from character IR.

The one-way walking choreography releases walking-only slots on arrival.
This is not a renderer for arbitrary movement, simultaneous actors or delivery.
Run with PYTHONPATH=tools/sms_wrapper python3 -m mugen2sms.analysis.bg_normal_phase_probe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from mugen2sms import character
from mugen2sms.source import Source
from mugen2sms.converters.sms_scale import scale_character
from mugen2sms.analysis import bg_probe_tiles as tile
from mugen2sms.analysis import control_adapter

CAPACITY = 448
BANK_SIZE = 16384


def distance_contract(original, action: int) -> dict:
    """Recognize the ordered idle near/far normal subset; preserve source units.

    Cancellation, airborne state, Width controllers and other CMD predicates
    require the complete engine. This contract covers standing mirrored idle.
    """
    candidates = original.raw_states[-1].controllers
    selected = next(c for c in candidates if c.type == 'changestate' and c.params.get('value') == str(action))
    command = next(t for t in selected.triggerall if re.fullmatch(r'command\s*=\s*"[a-z]+"',t,re.I))
    direct = next((t for t in selected.triggerall if re.match(r'p2bodydist\s+x',t,re.I)),None)
    previous = candidates[:candidates.index(selected)]
    preceding = [c for c in previous if c.type == 'changestate' and command in c.triggerall
                 and any(re.match(r'p2bodydist\s+x',t,re.I) for t in c.triggerall)]
    condition = direct or (next(t for t in preceding[-1].triggerall if re.match(r'p2bodydist\s+x',t,re.I)) if preceding else None)
    match = re.fullmatch(r'p2bodydist\s+x\s*<\s*(\d+)',condition or '',re.I)
    if not match:
        raise ValueError('CMD distance subset unsupported; do not silently use axis gap')
    front = int(original.constants['size']['ground.front'])
    threshold = int(match.group(1))
    return dict(command=command,threshold_source=threshold,comparison='lt' if direct else 'ge',
                front_p1_source=front,front_p2_source=front,scale_numerator=72,scale_denominator=107,
                source_condition=condition,source_line=selected.line,
                standing_mirror_axis_gap_first_far_px=((threshold+2*front)*72+106)//107,
                scope='standing mirror idle only; preceding near rule determines far fallback')


def body_distance_num(axis_gap: int, contract: dict) -> int:
    return (axis_gap*contract['scale_denominator'] -
            (contract['front_p1_source']+contract['front_p2_source'])*contract['scale_numerator'])


def distance_matches(axis_gap: int, contract: dict) -> bool:
    value=body_distance_num(axis_gap,contract)
    threshold=contract['threshold_source']*contract['scale_numerator']
    return value < threshold if contract['comparison']=='lt' else value >= threshold


def allocate(initial: set[bytes], final: set[bytes], protected: set[bytes],
             capacity: int = CAPACITY) -> tuple[dict, dict]:
    if not protected <= initial or not protected <= final:
        raise ValueError("protected patterns absent from a phase")
    if max(len(initial), len(final)) > capacity:
        raise ValueError("phase exceeds physical capacity")
    zero = bytes(64)
    ordered = [zero] + sorted(initial - {zero})
    first = {p: i for i, p in enumerate(ordered)}
    last = {p: first[p] for p in initial & final}
    free = list(range(len(first), capacity))
    free += sorted(first[p] for p in initial - final)
    for pattern, slot in zip(sorted(final - initial), free):
        last[pattern] = slot
    if len(last) != len(final):
        raise ValueError("incomplete phase allocation")
    if any(first[p] != last[p] for p in protected):
        raise ValueError("protected slot changed")
    return first, last


def verify_cache(plan: dict) -> None:
    memory = bytearray(plan['cache'])
    protected = {plan['first'][p] for p in plan['protected']}
    for tick in plan['ticks']:
        if sum(w['bytes'] for w in tick) > 224:
            raise ValueError('preload tick exceeds candidate schedule')
        for w in tick:
            dest, source, size = w['destination'], w['source_offset'], w['bytes']
            if (size <= 0 or dest % 32 or source % 32 or size % 32 or
                    dest < 0 or dest + size > len(memory) or
                    source < 0 or source + size > len(plan['stream'])):
                raise ValueError('invalid stream span')
            if protected & set(range(dest // 32, (dest + size) // 32)):
                raise ValueError('preload overwrites visible/protected pattern')
            memory[dest:dest+size] = plan['stream'][source:source+size]
    for p, slot in plan['last'].items():
        if memory[slot*32:(slot+1)*32] != tile.encode_sms_tile(p):
            raise ValueError('final simulated cache mismatch')


def self_check() -> dict:
    z = bytes(64)
    p = [bytes([i]) * 64 for i in range(1, 7)]
    first, last = allocate({z, *p[:3]}, {z, p[0], *p[3:6]}, {z, p[0]}, 5)
    checks = {
        "physical_reuse": len(set(first.values()) | set(last.values())) == 5,
        "protected_slots_stable": first[z] == last[z] and first[p[0]] == last[p[0]],
        "final_slots_unique": len(last) == len(set(last.values())),
    }
    for key, initial, final, protected in [
        ("reject_over_capacity", {z, *p}, {z}, {z}),
        ("reject_missing_protected", {z, p[0]}, {z}, {z, p[0]}),
    ]:
        try:
            allocate(initial, final, protected, 5)
        except ValueError:
            checks[key] = True
        else:
            checks[key] = False
    import copy
    cache = bytearray(5*32)
    for pattern, slot in first.items():
        cache[slot*32:(slot+1)*32] = tile.encode_sms_tile(pattern)
    missing = sorted((last[pattern], pattern) for pattern in last.keys()-first.keys())
    stream = b''.join(tile.encode_sms_tile(pattern) for _, pattern in missing)
    plan = dict(cache=bytes(cache), first=first, last=last, protected={z,p[0]}, stream=stream,
                ticks=[[dict(destination=slot*32, source_offset=i*32, bytes=32)
                        for i,(slot,_) in enumerate(missing)]])
    verify_cache(plan)
    checks['simulated_phase_matches_final_tiles'] = True
    for key, field, value in [('reject_visible_overwrite','destination',first[p[0]]*32),
                              ('reject_outside_stream','source_offset',len(stream)),
                              ('reject_unaligned_span','bytes',31)]:
        bad = copy.deepcopy(plan)
        bad['ticks'][0][0][field] = value
        try:
            verify_cache(bad)
        except ValueError:
            checks[key] = True
        else:
            checks[key] = False
    bad = copy.deepcopy(plan)
    bad['ticks'][0].pop()
    try:
        verify_cache(bad)
    except ValueError:
        checks['reject_missing_upload'] = True
    else:
        checks['reject_missing_upload'] = False
    near=dict(scale_numerator=72,scale_denominator=107,threshold_source=32,
              front_p1_source=18,front_p2_source=18,comparison='lt')
    far={**near,'comparison':'ge'}
    checks['axis_gap_32_is_source_near'] = distance_matches(32,near) and not distance_matches(32,far)
    checks['source_boundary_45_near_46_far'] = (
        distance_matches(45,near) and not distance_matches(45,far) and
        not distance_matches(46,near) and distance_matches(46,far))
    checks['rational_equality_is_far'] = distance_matches(68,{**far,'scale_numerator':1,'scale_denominator':1})
    checks.update({"control_profile_"+k: v
                   for k, v in control_adapter.self_check()["checks"].items()})
    return {"checks": checks, "passed": all(checks.values())}


def build_plan(args) -> dict:
    archive = args.source.resolve()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != args.source_sha:
        raise ValueError("source hash differs from requested source")
    original = character.load(Source(archive))
    distance = distance_contract(original,args.action)
    command_match = re.fullmatch(r'command\s*=\s*"([a-z]+)"', distance['command'], re.I)
    if not command_match:
        raise ValueError('source command name is outside the supported profile subset')
    control = control_adapter.load_trigger(
        args.control_profile, digest, command_match.group(1).lower())
    if not distance_matches(args.p2_anchor-104,distance):
        raise ValueError(f'requested action conflicts with source body distance: axis gap {args.p2_anchor-104}; {distance}')
    scaled = scale_character(original, {0, 20, args.action}, 72, 107)
    sprites = {(s.group, s.image): s for s in scaled.sprites}
    indices = sorted(set().union(*(
        set(sprites[(f.group, f.image)].pixels) - {0}
        for a in (0, 20, args.action) for f in scaled.anims[a].frames)))
    if len(indices) > 15:
        raise ValueError("source palette exceeds 15 opaque indices")
    slots = {v: i + 1 for i, v in enumerate(indices)}
    palettes = {name.lower(): colors for name, colors in original.palettes}
    p1 = [0] + [tile.sms_word(palettes[args.palette1.lower()][i]) for i in indices]
    p2 = [0] + [tile.sms_word(palettes[args.palette2.lower()][i]) for i in indices]
    mixed = {v: min(range(1, len(p1)), key=lambda k: (
        sum((a-b)**2 for a,b in zip(tile.word_rgb(p2[slots[v]]), tile.word_rgb(p1[k]))), k))
        for v in indices}
    opponent = tile.source_frame(scaled, 0, 0, args.p2_anchor, slots, True)
    frames = scaled.anims[args.action].frames
    if not 2 <= len(frames) <= 5:
        raise ValueError('probe telemetry supports only 2 through 5 AIR elements')
    images = {}
    for name, action, index, anchor in [
        ("idle84", 0, 0, 84),
        *[(f"walk{i}", 20, i, x) for i,x in enumerate((84,88,92,96,100,104))],
        ("idle104", 0, 0, 104),
        *[(f"normal_frame{i}", args.action, i, 104) for i in range(len(frames))],
    ]:
        actor = tile.source_frame(scaled, action, index, anchor, slots)
        images[name] = tile.compose(actor, opponent, slots, mixed)
    marker = bytearray(64)
    for y in (3,4):
        for x in (3,4):
            marker[y*8+x] = 7
    marker_pattern, flags = tile.canonical(bytes(marker))
    if flags:
        raise ValueError("marker flip")
    pattern_sets = {n: {p for p,_ in im.values()} for n,im in images.items()}
    permanent = {bytes(64), marker_pattern} | pattern_sets['idle104']
    initial = permanent | set().union(*(pattern_sets[n] for n in images if n.startswith(('idle','walk')))) | pattern_sets['normal_frame0']
    final = permanent | set().union(*(pattern_sets[n] for n in images if n.startswith('normal')))
    protected = permanent | pattern_sets['normal_frame0']
    # If the exact union fits, pay uploads once at boot and keep input immediate.
    # Phase reuse is needed only when the measured union exceeds VRAM capacity.
    if len(initial | final) <= CAPACITY:
        initial |= final
    first, last = allocate(initial, final, protected)
    maps = {}
    for name, image in images.items():
        ids = last if name.startswith('normal') else first
        words = [0] * 768
        for (x,y),(pattern,flags) in image.items():
            if not (0 <= x < 32 and 0 <= y < 24):
                raise ValueError('map outside VDP canvas')
            words[y*32+x] = ids[pattern] | flags
        maps[name] = words
    names = list(images)
    transitions = list(zip(names[:7],names[1:8]))
    transitions += [('idle104','normal_frame0')]
    transitions += [(f'normal_frame{i}',f'normal_frame{i+1}') for i in range(len(frames)-1)]
    transitions += [(f'normal_frame{len(frames)-1}','idle104')]
    pnt = bytearray(b''.join(w.to_bytes(2,'little') for w in maps['idle84']))
    pnt_rows = []
    for before,after in transitions:
        writes,metrics = tile.pnt_transition(maps[before],maps[after],pnt)
        pnt_rows.append(dict(before=names.index(before),after=names.index(after),writes=writes,metrics=metrics))
    uploads = sorted((last[p],p) for p in final-initial)
    stream = b''.join(tile.encode_sms_tile(p) for _,p in uploads)
    ticks = []
    for offset in range(0,len(uploads),7):
        writes = []
        for i,(slot,pattern) in enumerate(uploads[offset:offset+7],offset):
            if writes and writes[-1]['destination']+writes[-1]['bytes'] == slot*32:
                writes[-1]['bytes'] += 32
            else:
                writes.append(dict(destination=slot*32,source_offset=i*32,bytes=32))
        ticks.append(writes)
    cache = bytearray(CAPACITY*32)
    for pattern,slot in first.items():
        cache[slot*32:(slot+1)*32] = tile.encode_sms_tile(pattern)
    hits = []
    for controller in scaled.states[args.action].controllers:
        if controller.type != 'hitdef':
            continue
        damage = next((p.const for p in controller.params if p.name == 'damage[0]'),None)
        if not controller.tgate or controller.tgate[0] != 2 or damage is None:
            raise ValueError('HitDef requires a constant AnimElem gate and damage')
        index = int(controller.tgate[1])-1
        if not 0 <= index < len(frames) or not 0 <= int(damage) <= 255:
            raise ValueError('HitDef frame/damage outside diagnostic descriptor range')
        hits.append(dict(frame=index,damage=int(damage),boxes=frames[index].clsn1))
    if not hits or len(hits)>2 or any(not h['boxes'] for h in hits):
        raise ValueError('unsupported hit count/empty boxes')
    report = dict(schema='sms_bg_normal_phase_probe_v1',measurement_class='static_generated_plan_not_runtime',
        action=args.action,source_archive=str(archive),source_sha256=digest,p1_anchor=104,p2_anchor=args.p2_anchor,
        control_binding=control,
        palette_indices=indices,scale_ratio=[72,107],distance_contract=distance,
        body_distance_numerator=body_distance_num(args.p2_anchor-104,distance),
        capacity=CAPACITY,initial_patterns=len(initial),combat_patterns=len(final),
        all_phases_union=len(initial|final),reused_walk_slots=sum(slot<len(first) for slot,_ in uploads),
        preload_ticks=len(ticks),preload_bytes=len(stream),max_preload_tick_bytes=max((sum(w['bytes'] for w in t) for t in ticks),default=0),
        air_ticks=[int(f.time) for f in frames],hits=hits,pnt_payload_bytes=len(pnt),
        max_pnt_bytes_with_address=max(r['metrics']['bytes_with_vdp_address'] for r in pnt_rows),
        limitations=['one-way walk runtime; walking-only slots released when phase reuse is required',
            'stationary P2; source motion/hitstop/reaction/guard/AI/audio/PAL outside probe',
            'mixed BG cells approximate P2 colors with P1 palette; no delivery fidelity claim'])
    return dict(report=report,control_binding=control,images=images,first=first,last=last,protected=protected,marker=bytes(marker),
        marker_slot=first[marker_pattern],palettes=(p1,p2),cache=bytes(cache),pnt=bytes(pnt),stream=stream,
        transitions=pnt_rows,ticks=ticks,hurt=scaled.anims[0].frames[0].clsn2)


def header(plan: dict) -> str:
    r=plan['report'];h=r['hits'];out=['/* Generated phase-specific normal probe; no delivery claim. */',
        '#ifndef NORMAL_PHASE_PLAN_H','#define NORMAL_PHASE_PLAN_H',
        '#define GLOBAL_CACHE_PATTERN_COUNT 448u','#define GLOBAL_CACHE_RESIDENT_COUNT 448u',
        f'#define GLOBAL_CACHE_INITIAL_PATTERN_COUNT {r["initial_patterns"]}u',
        '#define GLOBAL_CACHE_DYNAMIC_BASE 448u','#define GLOBAL_CACHE_DYNAMIC_SLOT_COUNT 0u',
        '#define GLOBAL_CACHE_EMPTY_TILE 0u','#define GLOBAL_CACHE_BANK 42u','#define GLOBAL_PNT_BANK 43u',
        '#define GLOBAL_STREAM_BANK 44u','#define GLOBAL_CACHE_TILE_LIMIT 448u',
        '#define GLOBAL_CACHE_PROFILE_FRAMES 15u',f'#define GLOBAL_CACHE_FRAME_MARKER_TILE_ON {plan["marker_slot"]}u',
        '#define GLOBAL_CACHE_FRAME_MARKER_COL 29u','#define GLOBAL_CACHE_FRAME_MARKER_ROW 0u',
        '#define GLOBAL_CACHE_FRAME_MARKER_PERIOD 384u','#define GLOBAL_CACHE_PNT_BASE 0x3800u',
        '#define GLOBAL_MAP_IDLE84_OFFSET 0u',f'#define GLOBAL_PNT_TRANSITION_COUNT {len(plan["transitions"])}u',
        f'#define NORMAL_P2_ANCHOR_X {r["p2_anchor"]}u',f'#define NORMAL_SOURCE_ACTION {r["action"]}u',
        f'#define NORMAL_TRIGGER_BUTTON {plan["control_binding"]["physical_button"]}u',
        f'#define NORMAL_TRIGGER_HOLD_MODE {1 if plan["control_binding"]["activation"]=="hold" else 0}u',
        f'#define NORMAL_TRIGGER_THRESHOLD {plan["control_binding"]["threshold_frames"]}u',
        f'#define NORMAL_SCALE_DENOM {r["distance_contract"]["scale_denominator"]}',
        f'#define NORMAL_FRONT_TOTAL_NUM {(r["distance_contract"]["front_p1_source"]+r["distance_contract"]["front_p2_source"])*r["distance_contract"]["scale_numerator"]}',
        f'#define NORMAL_BODY_THRESHOLD_NUM {r["distance_contract"]["threshold_source"]*r["distance_contract"]["scale_numerator"]}',
        f'#define NORMAL_BODY_COMPARE_NEAR {1 if r["distance_contract"]["comparison"]=="lt" else 0}u',
        f'#define NORMAL_FRAME_COUNT {len(r["air_ticks"])}u',f'#define NORMAL_HIT_COUNT {len(h)}u',
        'typedef struct { signed int l,t,r,b; } NormalRect;',
        'typedef struct { unsigned char frame,damage,box_count; const NormalRect *boxes; } NormalHitEvent;',
        'typedef struct { unsigned int index,count,source_offset; } GlobalPntWrite;',
        'typedef struct { unsigned char source_map,target_map,run_count; const GlobalPntWrite *writes; } GlobalPntTransition;',
        'typedef struct { unsigned int destination,source_offset,bytes; } NormalStreamWrite;',
        'typedef struct { unsigned char write_count; const NormalStreamWrite *writes; } NormalStreamTick;']
    for name,values in zip(('global_cache_bg_palette','global_cache_sprite_palette'),plan['palettes']):
        values=values+[0]*(16-len(values));out.append(f'static const unsigned char {name}[16] = {{'+','.join(f'{v}u' for v in values)+'};')
    out += [f'#define NORMAL_IDLE_HURT_COUNT {len(plan["hurt"])}u',
        'static const NormalRect normal_idle_hurt[NORMAL_IDLE_HURT_COUNT] = {']
    out += ['{'+','.join(map(str,b))+'},' for b in plan['hurt']];out.append('};')
    for i,event in enumerate(h):
        out.append(f'static const NormalRect normal_hit_boxes_{i}[{len(event["boxes"])}] = {{')
        out += ['{'+','.join(map(str,b))+'},' for b in event['boxes']];out.append('};')
    out.append('static const NormalHitEvent normal_hit_events[NORMAL_HIT_COUNT] = {')
    out += [f'{{{e["frame"]}u,{e["damage"]}u,{len(e["boxes"])}u,normal_hit_boxes_{i}}},' for i,e in enumerate(h)];out.append('};')
    for i,row in enumerate(plan['transitions']):
        out.append(f'static const GlobalPntWrite global_pnt_writes_{i}[{max(1,len(row["writes"]))}] = {{')
        out += [f'{{{w["index"]}u,{w["count"]}u,{w["source_offset"]}u}},' for w in row['writes']] or ['{0u,0u,0u},'];out.append('};')
    out.append('static const GlobalPntTransition global_pnt_transitions[GLOBAL_PNT_TRANSITION_COUNT] = {')
    out += [f'{{{r["before"]}u,{r["after"]}u,{len(r["writes"])}u,global_pnt_writes_{i}}},' for i,r in enumerate(plan['transitions'])];out.append('};')
    out.append(f'#define NORMAL_IDLE_PREFETCH_TICK_COUNT {len(plan["ticks"])}u')
    for i,writes in enumerate(plan['ticks']):
        out.append(f'static const NormalStreamWrite normal_preload_{i}[{len(writes)}] = {{')
        out += [f'{{{w["destination"]}u,{w["source_offset"]}u,{w["bytes"]}u}},' for w in writes];out.append('};')
    out.append(f'static const NormalStreamTick normal_idle_prefetch[{max(1,len(plan["ticks"]))}] = {{')
    out += [f'{{{len(w)}u,normal_preload_{i}}},' for i,w in enumerate(plan['ticks'])] or ['{0u,0},'];out.append('};')
    out.append('static const unsigned char normal_air_ticks[NORMAL_FRAME_COUNT] = {'+','.join(f'{v}u' for v in plan['report']['air_ticks'])+'};')
    out.append('#endif');return '\n'.join(out)+'\n'


def write_plan(plan: dict, project: Path) -> None:
    # Simulate all preload writes against the initial VRAM before emitting.
    verify_cache(plan)
    bank_path=project/'assets/banks/versus_scene_banks_02.bin';prefix=bank_path.read_bytes()[:40*BANK_SIZE]
    if len(prefix)!=40*BANK_SIZE:
        raise ValueError('legacy bank prefix truncated')
    pages=[]
    for payload in (plan['cache'],plan['pnt'],plan['stream']):
        if len(payload)>BANK_SIZE:
            raise ValueError('payload exceeds bank')
        pages.append(payload+bytes([255])*(BANK_SIZE-len(payload)))
    bank_path.write_bytes(prefix+b''.join(pages))
    config_path=project/'.mddev/project.json';config=json.loads(config_path.read_text())
    config['name']=project.name.removeprefix('rom_')
    config['toolchain']['makesms_extra']=[('assets/banks/versus_scene_banks_02.bin:0:43:2' if x.startswith('assets/banks/versus_scene_banks_02.bin:') else x) for x in config['toolchain']['makesms_extra']]
    config_path.write_text(json.dumps(config,indent=2)+'\n')
    text=header(plan);(project/'inc/normal_phase_plan.h').write_text(text)
    expected=project/'out/normal_phase_expected';expected.mkdir(parents=True,exist_ok=True)
    for name,image in plan['images'].items():
        tile.save_expected(name,image,*plan['palettes'],plan['marker'],expected)
    report=plan['report'];report['plan_header_sha256']=hashlib.sha256(text.encode()).hexdigest()
    report['simulated_cache_verified']=True
    report['bank_hashes']={str(i+42):hashlib.sha256(p).hexdigest() for i,p in enumerate(pages)}
    evidence=project/'out/evidence';evidence.mkdir(parents=True,exist_ok=True)
    (evidence/'normal_phase_plan_20261005.json').write_text(json.dumps(report,indent=2)+'\n')


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-check',action='store_true')
    parser.add_argument('--source',type=Path);parser.add_argument('--source-sha')
    parser.add_argument('--project',type=Path);parser.add_argument('--action',type=int)
    parser.add_argument('--control-profile',type=Path)
    parser.add_argument('--p2-anchor',type=int,default=150)
    parser.add_argument('--palette1',default='ffspryo_4');parser.add_argument('--palette2',default='ffspryo_5')
    args=parser.parse_args()
    if args.self_check:
        result=self_check();print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
    if any(v is None for v in (args.source,args.source_sha,args.project,args.action,args.control_profile)):
        parser.error('source/source-sha/project/action/control-profile required')
    plan=build_plan(args);write_plan(plan,args.project.resolve());print(json.dumps(plan['report'],indent=2));return 0


if __name__=='__main__':
    raise SystemExit(main())
