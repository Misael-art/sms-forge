"""Verify Alis's new postures through private SMS input and native scanout."""

import argparse
import json
from pathlib import Path
import shutil
import sys

from PIL import Image

WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE / "tools/sms_wrapper"))
from bind_scene02_repertoire import ALIS_POSTURES, pose_order, verify_rom
from capture_video import _self_check
from duel_probe import RECORD_BYTES, decode
from replay_duel_round import MFD1, record_replay, sample_state, snapshot_sat
from revise_scene02_alis import raster
from session_bridge import isolated

UP, DOWN, LEFT, RIGHT, ONE, TWO = 1, 2, 4, 8, 16, 32
POSE_NAMES = {str(51 + index): item[1] for index, item in enumerate(ALIS_POSTURES)}


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def collect(session, out, sha):
    _, current = sample_state(session)
    assert current["p1"]["fighter"] == 1 and current["p1"]["facing_right"]
    assert current["p1"]["pivot"] == [111, 144] and current["p2"]["pivot"] == [144, 144]
    trace, cases, sat = [], {}, {}
    inputs = None

    def play(pad, ticks, second=0):
        nonlocal inputs, current
        if inputs != (pad, second):
            isolated.request(session, "input", pad, second, 0)
            inputs = pad, second
        first = len(trace)
        for _ in range(ticks):
            stamp = (current["stamp"] + 2) & 255
            commit = isolated.request(session, "sample-commit", MFD1 + 4, stamp, 8)
            read = isolated.request(session, "read", MFD1, RECORD_BYTES)
            observed = decode(bytes(read["ram"]))
            assert commit["frame"] == read["frame"] and stamp == observed["stamp"]
            assert observed["logic_tick"] == (current["logic_tick"] + 1) & 65535
            current = observed
            trace.append(dict(frame=read["frame"], sample_cycles=commit["cycles_advanced"],
                              inputs=[pad, second], **current))
        return trace[first:]

    def p1():
        return current["p1"]

    def take(label):
        sat[label] = snapshot_sat(session)
        assert sat[label]["max_per_scanline"] <= 8 and sat[label]["entries"] <= 64

    def trajectory(name, initial, samples):
        airborne = [row["p1"]["pivot"] for row in samples if row["p1"]["pivot"][1] < 144]
        liftoff = next(i for i, row in enumerate(samples) if row["p1"]["pivot"][1] < 144)
        preparation = samples[liftoff - 2:liftoff]
        assert len(preparation) == 2 and all(
            row["p1"]["pivot"] == initial and row["p1"]["pose_requested"] == 51
            and row["p1"]["pose_presented"] == 51 for row in preparation
        ), (name, preparation)
        transitions = sum(before["p1"]["pivot"][1] == 144 and after["p1"]["pivot"][1] < 144
                          for before, after in zip(samples, samples[1:]))
        if samples and samples[0]["p1"]["pivot"][1] < 144:
            transitions += 1
        assert transitions == 1 and len(airborne) == 28, (name, transitions, len(airborne))
        assert min(y for _, y in airborne) == 118 and p1()["pivot"][1] == 144
        cases[name] = {"start": initial, "finish": p1()["pivot"], "apex_y": 118,
                       "flight_ticks": len(airborne), "takeoffs": transitions,
                       "grounded_preparation": [row["logic_tick"] for row in preparation]}
        return airborne

    isolated.request(session, "record-steps-start", "posturas")
    try:
        play(LEFT, 88)
        assert p1()["pivot"] == [32, 144] and p1()["pose_presented"] == 54
        take("standing_guard_at_wall")
        play(RIGHT, 26)
        play(0, 4)
        base = p1()["pivot"]
        play(DOWN, 12)
        assert p1()["pivot"] == base and p1()["pose_presented"] == 52
        cases["crouch"] = {"pivot": p1()["pivot"], "hurt": p1()["boxes"]["hurt"]}
        play(DOWN | LEFT, 10)
        assert p1()["pivot"] == base and p1()["pose_presented"] == 53
        take("crouching_guard")
        play(0, 5)
        assert p1()["pose_presented"] == 16

        # Holding up through the landing must still give only one takeoff.
        neutral = play(UP | ONE, 43)
        assert {x for x, _ in trajectory("vertical", base, neutral)} == {base[0]}
        assert all(row["p1"]["state"] != 1 for row in neutral + play(0, 4))
        ascent = play(UP, 10)
        guarded = play(LEFT, 7)
        assert p1()["pose_presented"] == 59 and p1()["pivot"][1] == 118
        take("air_guard_at_apex")
        released = play(0, 5)
        assert p1()["pose_presented"] != 59 and p1()["pivot"][1] < 144
        resumed = play(LEFT, 5)
        assert p1()["pose_presented"] == 59 and p1()["pivot"][1] < 144
        end = play(0, 13)
        assert {x for x, _ in trajectory("vertical_air_guard", base,
                                        ascent + guarded + released + resumed + end)} == {base[0]}

        for name, direction, sign in (("diagonal_toward", RIGHT, 1),
                                      ("diagonal_away", LEFT, -1)):
            start = p1()["pivot"]
            samples = play(UP | direction, 7) + play(0, 30)
            path = trajectory(name, start, samples)
            assert all((b[0] - a[0]) * sign == 2 for a, b in zip(path, path[1:]))
            assert (p1()["pivot"][0] - start[0]) * sign == 58

        # The fight uses the same geometry for guards and unguarded contact.
        play(RIGHT, 80)
        play(0, 3)
        assert p1()["pivot"][0] == 120
        life = p1()["life"]
        attack = play(0, 3, ONE) + play(0, 3)
        attack += play(LEFT, 4)
        assert any(r["p2"]["contact"] == 2 and r["p1"]["pose_requested"] == r["p1"]["pose_presented"] == 54
                   for r in attack), ("standing guard", attack)
        assert p1()["life"] == life
        play(0, 14)
        play(RIGHT, 14)
        play(0, 3)
        attack = play(DOWN | LEFT, 4)
        attack += play(DOWN | LEFT, 3, TWO) + play(DOWN | LEFT, 18)
        assert any(r["p2"]["contact"] == 2 and r["p1"]["pose_requested"] == r["p1"]["pose_presented"] == 53
                   for r in attack), ("crouch guard", attack)
        assert p1()["life"] == life
        play(0, 8)
        play(RIGHT, 16)
        play(0, 3)
        attack = play(UP, 3, ONE) + play(LEFT, 13)
        assert any(r["p2"]["contact"] == 2 and 118 <= r["p1"]["pivot"][1] < 144
                   and r["p1"]["pose_requested"] == r["p1"]["pose_presented"] == 59
                   for r in attack), ("air guard", attack)
        assert p1()["life"] == life
        play(0, 29)
        play(RIGHT, 20)
        play(0, 5)

        for input_ticks, pose, hp in ((3, 21, 94), (8, 18, 84)):
            rows = play(ONE, input_ticks) + play(0, 30)
            assert any(r["p1"]["contact"] == 1 and r["p1"]["pose_presented"] == pose
                       and r["p2"]["life"] == hp for r in rows)
        special = play(DOWN, 3) + play(RIGHT | ONE, 3) + play(0, 30)
        assert any(r["p1"]["contact"] == 1 and r["p1"]["pose_presented"] == 49
                   and r["p2"]["life"] == 71 for r in special)
        play(0, 10)
    finally:
        recording = isolated.request(session, "record-steps-stop")
        isolated.request(session, "input", 0, 0, 0)
        dump(out / "input.json", dict(rom_sha256=sha, session_id=session.name, recording=recording,
                                     samples=trace, cases=cases, sat=sat,
                                     moves=[dict(player="p1", requested_at_hit=r["p1"]["pose_requested"],
                                                 opponent_life=r["p2"]["life"])
                                            for r in trace if r["p1"]["contact"] == 1]))
    runtime = isolated.request(session, "read", 0xC7D2, 32)["ram"]
    dump(out / "runtime.json", dict(rom_sha256=sha, session_id=session.name,
                                   max_vdp_gap=max(b["frame"] - a["frame"]
                                                   for a, b in zip(trace, trace[1:])),
                                   min_last_vblank_line=runtime[0],
                                   renderer_fault=runtime[8],
                                   missed_epochs=runtime[12] | runtime[13] << 8,
                                   active_area_endings=runtime[25] | runtime[26] << 8))
    assert runtime[8] == 0
    return trace, recording


def verify_pixels(session, trace, recording, plan_path, out, sha):
    plan = json.loads(plan_path.read_bytes())
    drawings = {frame["pose"]: raster(frame, plan["sprite_palette"])
                for frame in plan["frames"] if frame["actor"] == "alis" and frame["direction"] == "right"}
    matches = {}
    first = recording["first_frame"]
    for row in trace:
        actor = row["p1"]
        pose = str(actor["pose_presented"])
        if pose not in POSE_NAMES or pose in matches or int(pose) != actor["pose_requested"]:
            continue
        x, y = actor["pivot"]
        if x > 93:
            continue
        expected = [(u + x, v + y - 144, tuple(((c >> shift) & 3) * 85
                                               for shift in (0, 2, 4)))
                    for (u, v), c in drawings[POSE_NAMES[pose]].items()]
        for frame in range(row["frame"], row["frame"] + 4):
            path = session / "evidence/posturas" / f"{frame - first - 1:06d}.png"
            if not path.is_file():
                continue
            with Image.open(path) as capture:
                rgb = capture.convert("RGB")
                if not all(rgb.getpixel((u, v)) == color for u, v, color in expected):
                    continue
            target = out / f"pose-{pose}-vdp{frame}.png"
            shutil.copy2(path, target)
            matches[pose] = dict(name=POSE_NAMES[pose], vdp_frame=frame, pivot=[x, y],
                                 submit_sample_vdp=row["frame"], vdps_after_sample=frame - row["frame"],
                                 compared=len(expected), file=target.name, sha256=isolated.sha(target))
            break
    dump(out / "poses.json", dict(rom_sha256=sha, session_id=session.name, matches=matches,
                                 missing=sorted(set(POSE_NAMES) - set(matches))))
    assert set(matches) == set(POSE_NAMES), (sorted(matches), sorted(POSE_NAMES))


def verify_guard_contacts(session, trace, recording, plan_path, out, sha):
    plan = json.loads(plan_path.read_bytes())
    poses = [*pose_order(), *(tuple(pose) for pose in plan["added_poses"])]
    drawings = {(row["actor"], row["pose"], row["direction"]): raster(row, plan["sprite_palette"])
                for row in plan["frames"]}
    directory = session / "evidence/posturas"
    reports = []

    def project(actor):
        face = "right" if actor["facing_right"] else "left"
        x, y = actor["pivot"]
        return {(x + left, y + top - 144): tuple(((c >> shift) & 3) * 85 for shift in (0, 2, 4))
                for (left, top), c in drawings[(*poses[actor["pose_presented"]], face)].items()}

    for row in trace:
        if row["p2"]["contact"] != 2:
            continue
        defender, attacker = row["p1"], row["p2"]
        occluded = project(attacker)
        exposed = {xy: rgb for xy, rgb in project(defender).items() if xy not in occluded}
        assert exposed
        samples = []
        for frame in range(row["frame"], row["frame"] + 4):
            path = directory / f"{frame - recording['first_frame'] - 1:06d}.png"
            if path.is_file():
                with Image.open(path) as image:
                    rgb = image.convert("RGB")
                    samples.append((sum(rgb.getpixel(xy) == color for xy, color in exposed.items()),
                                    frame, path))
        matched, frame, path = max(samples, key=lambda sample: sample[0])
        file = out / f"block-{defender['pose_presented']}-vdp{frame}.png"
        shutil.copy2(path, file)
        reports.append(dict(pose=defender["pose_presented"], pivot=defender["pivot"],
                            logic_tick=row["logic_tick"], submit_sample_vdp=row["frame"],
                            scanout_vdp=frame, visible_pixels=len(exposed), matched_pixels=matched,
                            life=defender["life"], hurt=defender["boxes"]["hurt"],
                            attack=attacker["boxes"]["attack"], file=file.name, sha256=isolated.sha(file)))
    dump(out / "guard-contact-pixels.json", dict(rom_sha256=sha, session_id=session.name, blocks=reports))
    assert [row["pose"] for row in reports] == [54, 53, 59], reports
    assert all(row["matched_pixels"] == row["visible_pixels"] for row in reports), reports


def run(args):
    destination = args.out / ("continuous-retry" if args.replay_only else "continuous")
    if not args.replay_only:
        args.out.mkdir()
    sha = verify_rom(args.rom, args.banks)["rom_sha256"]
    assert _self_check() == 0
    with isolated.performance_reservation(), isolated.project_reservation(Path(__file__).resolve().parents[1]):
        isolated.DEFAULT_ROOT = WORKSPACE / ".runtime/s"
        if not args.replay_only:
            session = isolated.start(args.rom, ttl=900)
            try:
                trace, recording = collect(session, args.out, sha)
            finally:
                isolated.close_session(session)
                _, meta = isolated.load(session)
                dump(args.out / "stepped-closed.json", meta)
                assert meta["state"] == "closed"
            verify_pixels(session, trace, recording, args.plan, args.out, sha)
            verify_guard_contacts(session, trace, recording, args.plan, args.out, sha)
        session = isolated.start(args.rom, ttl=900)
        try:
            result = record_replay(session, args.out / "input.json", destination)
            observed = json.loads((destination / "probe.json").read_bytes())
            blocks = [dict(frame=row["video_frame"], elapsed_ns=row["elapsed_ns"],
                           alis=row["p1"], hayato=row["p2"]) for row in observed
                      if row["p2"]["contact"] == 2]
            dump(destination / "blocks.json", dict(rom_sha256=sha, session_id=session.name, blocks=blocks))
            print(json.dumps(dict(same_contacts=result["same_contacts"], cadence=result["cadence"]), indent=2))
        finally:
            isolated.close_session(session)
            _, meta = isolated.load(session)
            dump(args.out / f"{destination.name}-closed.json", meta)
            assert meta["state"] == "closed"


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("rom", type=Path)
    cli.add_argument("banks", type=Path)
    cli.add_argument("plan", type=Path)
    cli.add_argument("out", type=Path)
    cli.add_argument("--replay-only", action="store_true")
    run(cli.parse_args())
