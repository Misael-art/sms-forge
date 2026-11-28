"""Exercise the jump arc, side swaps and mirrored contact in a private SMS session."""

import argparse
import json
from pathlib import Path
import shutil
import sys

from PIL import Image

from replay_alis_postures import WORKSPACE, LEFT, ONE, RIGHT, UP, dump
from bind_scene02_repertoire import pose_order, verify_rom
from capture_video import _self_check
from duel_probe import RECORD_BYTES, decode
from replay_duel_round import MFD1, record_replay, sample_state
from revise_scene02_alis import raster
from session_bridge import isolated


def exercise(session, out, sha):
    _, current = sample_state(session)
    assert current["p1"]["fighter"] == 1 and current["p1"]["pivot"] == [111, 144]
    trace, jumps = [], {}
    pad = None

    def play(keys, ticks):
        nonlocal current, pad
        if pad != keys:
            isolated.request(session, "input", keys, 0, 0)
            pad = keys
        first = len(trace)
        for _ in range(ticks):
            stamp = (current["stamp"] + 2) & 255
            commit = isolated.request(session, "sample-commit", MFD1 + 4, stamp, 8)
            read = isolated.request(session, "read", MFD1, RECORD_BYTES)
            observed = decode(bytes(read["ram"]))
            assert read["frame"] == commit["frame"] and observed["stamp"] == stamp
            assert observed["logic_tick"] == (current["logic_tick"] + 1) & 65535
            current = observed
            trace.append(dict(frame=read["frame"], sample_cycles=commit["cycles_advanced"],
                              inputs=[keys, 0], **observed))
        return trace[first:]

    def jump(label, direction, crosses=False):
        origin = current["p1"]
        if direction:
            rows = play(UP | direction, 5) + play(0, 30)
        else:
            rows = play(UP, 36)
        start = next(i for i, event in enumerate(rows) if event["p1"]["pivot"][1] < 144)
        air_ticks = 20
        flight = rows[start:start + air_ticks]
        points = [row["p1"]["pivot"] for row in flight]
        assert len(points) == air_ticks and all(y < 144 for _, y in points)
        assert all(row["p1"]["pivot"][1] == 144 for row in rows[start + air_ticks:])
        assert [event["p1"]["pose_requested"] for event in rows[start - 2:start]] == [51, 51]
        heights = [144, *(y for _, y in points), 144]
        assert min(heights) == 66
        speed = [after - before for before, after in zip(heights, heights[1:])]
        assert speed == [-14, -13, -12, -10, -9, -7, -5, -5, -2, -1, 0,
                         2, 3, 5, 7, 7, 10, 11, 12, 14, 7], (label, speed)
        rival_x = current["p2"]["pivot"][0]
        for x, y in points:
            if abs(x - rival_x) < 24:
                assert y <= 79, (label, x, y)
        assert current["p1"]["facing_right"] == (origin["facing_right"] ^ crosses)
        assert current["p1"]["presented_facing_right"] == current["p1"]["facing_right"]
        if crosses:
            turned = next(row for row in flight if row["p1"]["facing_right"] != origin["facing_right"])
            assert turned["p1"]["pivot"][1] <= 79
            assert turned["p1"]["presented_facing_right"] == turned["p1"]["facing_right"]
            assert turned["p2"]["presented_facing_right"] == turned["p2"]["facing_right"]
        else:
            turned = None
        if not direction:
            assert {x for x, _ in points} == {origin["pivot"][0]}
        jumps[label] = dict(start=origin["pivot"], landing=current["p1"]["pivot"],
                            takeoff_tick=flight[0]["logic_tick"],
                            landing_tick=rows[start + air_ticks]["logic_tick"],
                            prepare_vdp=rows[start - 2]["frame"],
                            touchdown_vdp=rows[start + air_ticks]["frame"],
                            highest_y=66, airborne_ticks=len(points), vertical_delta=speed,
                            turn=turned, landed=rows[-1])

    def hit(press, pose, life, right):
        events = play(ONE, press) + play(0, 25)
        hits = [row for row in events if row["p1"]["contact"] == 1]
        assert len(hits) == 1 and hits[0]["p2"]["life"] == life, hits
        hit = hits[0]["p1"]
        assert hit["pose_requested"] == pose and hit["facing_right"] == right

    isolated.request(session, "record-steps-start", "crossing")
    try:
        play(0, 18)
        jump("vertical", 0)
        play(0, 6)
        jump("left_to_right", RIGHT, crosses=True)
        play(LEFT, 64)
        play(0, 4)
        hit(3, 21, 94, False)
        play(RIGHT, 6)
        play(0, 4)
        jump("right_to_left", LEFT, crosses=True)
        play(RIGHT, 55)
        play(0, 4)
        hit(8, 18, 84, True)
        play(LEFT, 90)
        play(0, 4)
        jump("late_approach", RIGHT)
        play(RIGHT, 80)
        play(0, 4)
        hit(3, 21, 78, True)
    finally:
        recording = isolated.request(session, "record-steps-stop")
        isolated.request(session, "input", 0, 0, 0)
        dump(out / "input.json", dict(rom_sha256=sha, session_id=session.name, recording=recording,
                                     jumps=jumps, samples=trace,
                                     moves=[dict(player="p1", requested_at_hit=row["p1"]["pose_requested"],
                                                 opponent_life=row["p2"]["life"])
                                            for row in trace if row["p1"]["contact"] == 1]))
    counters = isolated.request(session, "read", 0xC7D2, 32)["ram"]
    assert counters[8] == 0
    dump(out / "runtime.json", dict(rom_sha256=sha, session_id=session.name,
                                   worst_vdp_gap=max(b["frame"] - a["frame"]
                                                     for a, b in zip(trace, trace[1:])),
                                   active_area_endings=counters[25] | counters[26] << 8,
                                   fault=counters[8], missed_epochs=counters[12] | counters[13] << 8))
    return jumps, recording


def confirm_pixels(session, out, plan_path, jumps, recording, sha):
    plan = json.loads(plan_path.read_bytes())
    poses = [*pose_order(), *(tuple(pose) for pose in plan["added_poses"])]
    art = {(row["actor"], row["pose"], row["direction"]): raster(row, plan["sprite_palette"])
           for row in plan["frames"]}
    result = {}
    hud_coverage = {}
    raw = session / "evidence/crossing"
    for name, jump in jumps.items():
        start, end = jump["prepare_vdp"], jump["touchdown_vdp"] + 1
        previous_hud = None
        hud_coverage[name] = 0
        for frame in range(start, end + 1):
            path = raw / f"{frame - recording['first_frame'] - 1:06d}.png"
            with Image.open(path) as source:
                hud = source.convert("RGB").crop((0, 8, 256, 15)).tobytes()
            if previous_hud is not None:
                assert previous_hud == hud, (name, frame, "HUD changed during the jump")
            previous_hud = hud
            hud_coverage[name] += 1
        for phase in ("turn", "landed"):
            row = jump[phase]
            if row is None:
                continue
            colors = {}
            for actor in ("p1", "p2"):
                state = row[actor]
                assert state["facing_right"] == state["presented_facing_right"]
                direction = "right" if state["presented_facing_right"] else "left"
                x, y = state["pivot"]
                drawing = art[(*poses[state["pose_presented"]], direction)]
                for (u, v), color in drawing.items():
                    pixel = (x + u, y + v - 144)
                    colors[pixel] = None if pixel in colors else tuple((color >> shift & 3) * 85
                                                                      for shift in (0, 2, 4))
            visible = {pixel: value for pixel, value in colors.items() if value is not None}
            for frame in range(row["frame"], row["frame"] + 4):
                path = raw / f"{frame - recording['first_frame'] - 1:06d}.png"
                if not path.is_file():
                    continue
                with Image.open(path) as source:
                    pixels = source.convert("RGB")
                    if not all(pixels.getpixel(xy) == color for xy, color in visible.items()):
                        continue
                image = out / f"{name}-{phase}-vdp{frame}.png"
                shutil.copy2(path, image)
                result[f"{name}_{phase}"] = dict(pixels=len(visible), scanout=frame,
                                                 file=image.name, sha256=isolated.sha(image))
                break
    dump(out / "pixels.json", dict(rom_sha256=sha, session_id=session.name,
                                   frames=result, verified_hud_frames=hud_coverage))
    assert len(result) == 6, sorted(result)


def run(args):
    args.out.mkdir()
    sha = verify_rom(args.rom, args.banks)["rom_sha256"]
    assert _self_check() == 0
    with isolated.performance_reservation(), isolated.project_reservation(Path(__file__).resolve().parents[1]):
        isolated.DEFAULT_ROOT = WORKSPACE / ".runtime/s"
        session = isolated.start(args.rom, ttl=900)
        try:
            jumps, recording = exercise(session, args.out, sha)
        finally:
            isolated.close_session(session)
            _, meta = isolated.load(session)
            dump(args.out / "stepped-closed.json", meta)
            assert meta["state"] == "closed"
        confirm_pixels(session, args.out, args.plan, jumps, recording, sha)
        session = isolated.start(args.rom, ttl=900)
        try:
            result = record_replay(session, args.out / "input.json", args.out / "continuous")
            print(json.dumps(dict(same_contacts=result["same_contacts"], cadence=result["cadence"]), indent=2))
        finally:
            isolated.close_session(session)
            _, meta = isolated.load(session)
            dump(args.out / "continuous-closed.json", meta)
            assert meta["state"] == "closed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("rom", "banks", "plan", "out"):
        parser.add_argument(name, type=Path)
    run(parser.parse_args())
