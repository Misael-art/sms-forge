"""Reproduce mixed jump, guard and sword inputs in a private SMS session."""

import argparse
from itertools import groupby
import json
from pathlib import Path
import signal

from PIL import Image

from bind_scene02_repertoire import pose_order, verify_rom
from capture_video import _self_check
from duel_probe import RECORD_BYTES, decode
from replay_alis_postures import DOWN, LEFT, ONE, RIGHT, UP, WORKSPACE, dump
from replay_duel_round import MFD1, record_replay, sample_state, snapshot_sat
from revise_scene02_alis import raster
from session_bridge import isolated

VERTICAL_DELTA = [-14, -13, -12, -10, -9, -7, -5, -5, -2, -1, 0,
                  2, 3, 5, 7, 7, 10, 11, 12, 14, 7]
PROBE_END = 0xC7F2


def exercise(session, out, sha, baseline):
    _, current = sample_state(session)
    assert current["p1"]["fighter"] == 1 and current["p1"]["pivot"] == [111, 144]
    trace, ranges, phase_sat = [], {}, {}
    pad = None

    def play(label, keys, ticks, observe_sat=True):
        nonlocal current, pad
        first = len(trace)
        if pad != keys:
            isolated.request(session, "input", keys, 0, 0)
            pad = keys
        for _ in range(ticks):
            stamp = (current["stamp"] + 2) & 255
            commit = isolated.request(session, "sample-commit", MFD1 + 4, stamp, 8)
            read = isolated.request(session, "read", MFD1, PROBE_END - MFD1)
            data = bytes(read["ram"])
            observed = decode(data[:RECORD_BYTES])
            assert read["frame"] == commit["frame"] and observed["stamp"] == stamp
            assert observed["logic_tick"] == (current["logic_tick"] + 1) & 65535
            current = observed
            trace.append(dict(frame=read["frame"], inputs=[keys, 0],
                              cadence_lines=list(data[0xC7D4-MFD1:0xC7D8-MFD1]),
                              render_stage_lines=list(data[0xC7C0-MFD1:0xC7C4-MFD1]),
                              probe_end_line=data[0xC7DD-MFD1], **current))
            alis = observed["p1"]
            pose = alis["pose_presented"]
            if observe_sat and pose == alis["pose_requested"] and pose in (17, 18, 19, 55, 56, 57, 58, 59):
                key = f"{pose}-{'right' if alis['presented_facing_right'] else 'left'}"
                if key not in phase_sat:
                    phase_sat[key] = snapshot_sat(session)
        ranges[label] = (first, len(trace))

    def toward(label):
        fighter, opponent = current["p1"], current["p2"]
        distance = abs(fighter["pivot"][0] - opponent["pivot"][0]) - 24
        advance = RIGHT if fighter["facing_right"] else LEFT
        if distance > 0:
            play(label, advance, distance + 3)

    isolated.request(session, "record-steps-start", "jump-mix")
    try:
        play("idle", 0, 18)
        play("sword_holding_back", LEFT | ONE, 8)
        play("queued_back_jump", LEFT | UP | ONE, 36)
        play("release", 0, 4)
        play("vertical", UP, 29)
        if baseline:
            play("recenter", RIGHT, 56)
        else:
            toward("recenter")
        play("forward_start", RIGHT | UP, 5)
        play("forward_continue", 0, 25)
        if not baseline:
            toward("approach_from_other_side")
            play("mirror_forward_start", LEFT | UP, 5)
            play("mirror_forward_continue", 0, 25)
            toward("return_to_range")
        back = LEFT if current["p1"]["facing_right"] else RIGHT
        play("held_air_guard", back | UP | ONE, 30)
        play("recover", 0, 4)
        back = LEFT if current["p1"]["facing_right"] else RIGHT
        play("guard_tap", back | UP | ONE, 5)
        play("release_guard", 0, 3)
        play("restore_guard_and_queue", back | UP | ONE, 46)
        play("settle", 0, 8)
        if not baseline:
            toward("approach_for_sword")
            back = LEFT if current["p1"]["facing_right"] else RIGHT
            play("sword_again", back | ONE, 8)
            play("sword_recovery", 0, 22)
            play("fresh_vertical", UP, 30)
    finally:
        recording = isolated.request(session, "record-steps-stop")
        isolated.request(session, "input", 0, 0, 0)
        dump(out / "input.json", dict(rom_sha256=sha, session_id=session.name, recording=recording,
                                     ranges=ranges, samples=trace,
                                     moves=[dict(player="p1", requested_at_hit=row["p1"]["pose_requested"],
                                                 opponent_life=row["p2"]["life"])
                                            for row in trace if row["p1"]["contact"] == 1]))
    counters = isolated.request(session, "read", 0xC7D2, 32)["ram"]
    metrics = {}
    for label, (first, end) in ranges.items():
        rows = [row["p1"] for row in trace[first:end]]
        airborne = [row for row in rows if row["pivot"][1] < 144]
        metrics[label] = dict(
            airborne=len(airborne),
            takeoffs=sum(trace[i - 1]["p1"]["pivot"][1] == 144 and
                         trace[i]["p1"]["pivot"][1] < 144 for i in range(max(1, first), end)),
            requested=list(dict.fromkeys(row["pose_requested"] for row in airborne)),
            presented=list(dict.fromkeys(row["pose_presented"] for row in airborne)),
            strikes=sum(row["contact"] == 1 for row in rows),
            apex=min(row["pivot"][1] for row in rows),
        )
    sat = snapshot_sat(session)
    runtime = dict(rom_sha256=sha, session_id=session.name, cases=metrics, sat=sat, phase_sat=phase_sat,
                   active_area_endings=counters[25] | counters[26] << 8, fault=counters[8],
                   worst_vdp_gap=max(b["frame"] - a["frame"] for a, b in zip(trace, trace[1:])))
    dump(out / "runtime.json", runtime)
    print(json.dumps(metrics, indent=2))
    if not baseline:
        first = len(trace)
        play("after_landing", 0, 5, observe_sat=False)
        play("shield_step_down", DOWN, 3, observe_sat=False)
        forward = RIGHT if current["p1"]["facing_right"] else LEFT
        play("shield_step_forward", forward | ONE, 3, observe_sat=False)
        play("shield_step_release", 0, 27, observe_sat=False)
        samples = trace[first:]
        dump(out / "special-regression.json", dict(rom_sha256=sha, session_id=session.name,
                                                    samples=samples))
        hits = [row for row in samples if row["p1"]["contact"] == 1]
        assert len(hits) == 1 and hits[0]["p1"]["pose_requested"] == 49, hits
    return trace, ranges, runtime, recording


def verify_flights(trace, ranges, runtime):
    def section(first, last=None):
        return trace[ranges[first][0]:ranges[last or first][1]]

    groups = [
        ("sword_to_jump", section("queued_back_jump", "release"), [55, 59, 57], -1),
        ("vertical", section("vertical"), [55, 56, 57], 0),
        ("cross_right", section("forward_start", "forward_continue"), [55, 58, 56, 57], 1),
        ("cross_left", section("mirror_forward_start", "mirror_forward_continue"), [55, 58, 56, 57], -1),
        ("held_guard", section("held_air_guard"), [55, 59, 57], None),
        ("guard_rearmed", section("guard_tap", "restore_guard_and_queue"), None, None),
        ("fresh_vertical", section("fresh_vertical"), [55, 56, 57], 0),
    ]
    selected, flights = {}, {}
    assert runtime["fault"] == runtime["active_area_endings"] == 0, runtime
    for sat in [runtime["sat"], *runtime["phase_sat"].values()]:
        assert sat["entries"] <= 64 and sat["max_per_scanline"] <= 8
    for name, rows, expected, direction in groups:
        for preceding, sample in zip(rows, rows[1:]):
            if sample["inputs"] == preceding["inputs"]:
                assert sample["p1"]["keys_consumed"] == sample["inputs"][0], (name, sample)
        flights[name] = []
        starts = [i for i in range(1, len(rows)) if rows[i - 1]["p1"]["pivot"][1] == 144 >
                  rows[i]["p1"]["pivot"][1]]
        assert len(starts) == (2 if name == "guard_rearmed" else 1), (name, starts)
        for index, start in enumerate(starts):
            assert start >= 2 and start + 20 < len(rows), (name, "incomplete flight")
            air = rows[start:start + 20]
            finish = rows[start + 20]
            positions = [row["p1"]["pivot"] for row in air]
            assert all(y < 144 for _, y in positions) and finish["p1"]["pivot"][1] == 144
            heights = [144, *(y for _, y in positions), 144]
            assert [b - a for a, b in zip(heights, heights[1:])] == VERTICAL_DELTA, name
            assert all(row["p1"]["pose_requested"] == 51 for row in rows[start - 2:start]), name
            if name == "sword_to_jump":
                p1 = air[0]["p1"]
                assert air[0]["logic_tick"] == (p1["free_since"] + 2) & 65535
            assert all(row["p1"]["state"] != 1 for row in air), name
            delta_x = finish["p1"]["pivot"][0] - rows[start - 1]["p1"]["pivot"][0]
            if direction is not None:
                assert (delta_x > 0) - (delta_x < 0) == direction, (name, delta_x)
            if name.startswith("cross_"):
                assert air[0]["p1"]["facing_right"] != finish["p1"]["facing_right"], name
            requested = [pose for pose, _ in groupby(row["p1"]["pose_requested"] for row in air)]
            presented = [pose for pose, _ in groupby(row["p1"]["pose_presented"] for row in air)]
            if expected is not None:
                assert requested == expected, (name, requested)
                # Compare phases in temporal order. A retained pre-takeoff
                # drawing during a transfer does not count as an exposure.
                assert [pose for pose in presented if pose in requested] == expected, (name, presented)
            else:
                assert all(pose in presented for pose in (55, 59, 57)), (name, presented)
            for pose in requested:
                matching = [row for row in air if row["p1"]["pose_presented"] ==
                            row["p1"]["pose_requested"] == pose and row["p1"]["facing_right"] ==
                            row["p1"]["presented_facing_right"]]
                if expected is not None:
                    assert matching, (name, pose, "phase was requested but never shown on time")
                if matching:
                    selected[f"{name}-{index + 1}-{pose}"] = matching
            flights[name].append(dict(requested=requested, presented=presented, dx=delta_x,
                                      apex=min(heights), airborne_ticks=len(air),
                                      takeoff_vdp=air[0]["frame"], landing_vdp=finish["frame"]))
    for label, rows, life in (
        ("cold_sword", section("sword_holding_back", "queued_back_jump"), 90),
        ("rearmed_sword", section("sword_again", "sword_recovery"), 80),
    ):
        attacking = [row for row in rows if row["p1"]["state"] == 1]
        hits = [row for row in attacking if row["p1"]["contact"] == 1]
        assert len(hits) == 1 and hits[0]["p2"]["life"] == life, (label, hits)
        hit = hits[0]["p1"]
        assert hit["pose_requested"] == hit["pose_resident"] == hit["pose_presented"] == 18, (label, hit)
        for pose in (17, 18, 19):
            shown = [row for row in attacking if row["p1"]["pose_presented"] ==
                     row["p1"]["pose_requested"] == pose]
            assert shown, (label, pose, "missing sword phase")
            selected[f"{label}-{pose}"] = hits if pose == 18 else shown
    return flights, selected


def verify_scanout(session, out, sha, plan_path, recording, flights, selected):
    plan = json.loads(plan_path.read_bytes())
    poses = [*pose_order(), *(tuple(pose) for pose in plan["added_poses"])]
    art = {(row["actor"], row["pose"], row["direction"]): raster(row, plan["sprite_palette"])
           for row in plan["frames"]}
    raw = session / "evidence/jump-mix"
    verified = {}
    for label, rows in selected.items():
        for row in rows:
            colors = {}
            for actor in ("p1", "p2"):
                state = row[actor]
                face = "right" if state["presented_facing_right"] else "left"
                pixels = art[(*poses[state["pose_presented"]], face)]
                x, y = state["pivot"]
                for (u, v), code in pixels.items():
                    point = x + u, y + v - 144
                    if 0 <= point[0] < 256 and 0 <= point[1] < 192:
                        colors[point] = None if point in colors else tuple(
                            (code >> shift & 3) * 85 for shift in (0, 2, 4))
            for frame in range(row["frame"], row["frame"] + 3):
                path = raw / f"{frame - recording['first_frame'] - 1:06d}.png"
                if not path.is_file():
                    continue
                with Image.open(path) as source:
                    screen = source.convert("RGB")
                if all(screen.getpixel(point) == color for point, color in colors.items() if color):
                    verified[label] = dict(scanout=frame, source_vdp=row["frame"],
                                           pixels=sum(color is not None for color in colors.values()),
                                           sha256=isolated.sha(path))
                    if label.startswith(("cross_right-", "held_guard-")):
                        screen.save(out / f"{label}.png")
                    break
            if label in verified:
                break
    hud_frames = 0
    for group in flights.values():
        for flight in group:
            last_hud = None
            for frame in range(flight["takeoff_vdp"], flight["landing_vdp"] + 1):
                path = raw / f"{frame - recording['first_frame'] - 1:06d}.png"
                with Image.open(path) as source:
                    hud = source.convert("RGB").crop((0, 8, 256, 15)).tobytes()
                if last_hud is not None:
                    assert hud == last_hud, (frame, "HUD pixels changed during flight")
                last_hud = hud
                hud_frames += 1
    dump(out / "pixels.json", dict(rom_sha256=sha, session_id=session.name,
                                  verified=verified, hud_frames=hud_frames))
    assert set(verified) == set(selected), sorted(set(selected) - set(verified))


def run(args):
    args.out.mkdir(parents=True)
    sha = verify_rom(args.rom, args.banks)["rom_sha256"]
    assert _self_check() == 0
    project = Path(__file__).resolve().parents[1]
    with isolated.performance_reservation(), isolated.project_reservation(project):
        isolated.DEFAULT_ROOT = WORKSPACE / ".runtime/s"
        session = isolated.start(args.rom, ttl=900)
        try:
            trace, ranges, runtime, recording = exercise(session, args.out, sha, args.baseline)
        finally:
            isolated.close_session(session)
            _, meta = isolated.load(session)
            dump(args.out / "stepped-closed.json", meta)
            assert meta["state"] == "closed"
        if not args.baseline:
            flights, selected = verify_flights(trace, ranges, runtime)
            dump(args.out / "flights.json", dict(rom_sha256=sha, session_id=session.name, flights=flights))
            verify_scanout(session, args.out, sha, args.plan, recording, flights, selected)
        if args.continuous:
            session = isolated.start(args.rom, ttl=900)
            try:
                result = record_replay(session, args.out / "input.json", args.out / "continuous")
                assert result["same_contacts"], result["actual_contacts"]
                if not args.baseline:
                    assert all(hit["requested"] == hit["resident"] == hit["presented"] == 18
                               for hit in result["actual_contacts"]), result["actual_contacts"]
            finally:
                isolated.close_session(session)
                _, meta = isolated.load(session)
                dump(args.out / "continuous-closed.json", meta)
                assert meta["state"] == "closed"
        return runtime


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("rom", "banks", "out"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--continuous", action="store_true")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--plan", type=Path)
    args = parser.parse_args()
    if not args.baseline and args.plan is None:
        parser.error("--plan is required for the scanout comparison")
    def terminate(_signal, _frame):
        raise SystemExit(143)

    signal.signal(signal.SIGTERM, terminate)
    run(args)
