"""Exercise all standing normals and capture a full round from a private session."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from duel_probe import RECORD_BYTES, decode

MOVE_STARTS = ((7, 1, 10, 13), (20, 17, 23, 26))
SPECIAL_STARTS = (45, 48)
BUTTON_ONE = 16
BUTTON_TWO = 32
DOWN = 2
RIGHT = 8
LEFT = 4
MFD1 = 0xC770
RENDER_METRICS = 0xC7D2
RENDER_METRICS_BYTES = 32
MAX_TICKS = 850
MAX_VDP_FRAMES = 1680
FRAME_BYTES = 256 * 192 * 3
MAX_VDP_FRAMES_PER_COMMIT = 8


def observe_normal(segment, player, normal, initial_life, *, fighter=None):
    """Describe the contact and the presentation sampled at that game tick."""
    actor = f"p{player + 1}"
    opponent = f"p{2 - player}"
    fighter = player if fighter is None else fighter
    expected = SPECIAL_STARTS[fighter] if normal == 4 else MOVE_STARTS[fighter][normal]
    start = next((event for event in segment if event[actor]["state"] == 1
                  and event[actor]["action_tick"] == 0), None)
    if not start or start[actor]["pose_requested"] != expected:
        raise RuntimeError(f"{actor}: action {normal} did not start on its authored pose")
    previous_life = initial_life
    hits = []
    started = False
    for event in segment:
        if event is start:
            started = True
        life = event[opponent]["life"]
        landed = event[actor]["contact"] == 1
        if landed != (life < previous_life):
            raise RuntimeError(f"{actor}: contact and life disagree at tick {event['logic_tick']}")
        if landed:
            if not started:
                raise RuntimeError(f"{actor}: damage preceded standing normal {normal}")
            hits.append((event, previous_life))
        previous_life = life
    if len(hits) != 1:
        raise RuntimeError(f"{actor}: expected one damaging contact, observed {len(hits)}")
    hit, before_hit = hits[0]
    contact = hit[actor]
    local = contact["pose_used_for_contact"]
    if not local or expected + local - 1 != contact["pose_requested"]:
        raise RuntimeError(f"{actor}: contact pose {local} does not map to the requested art")
    if fighter == 0 and normal == 4 and (contact["action_tick"], local) not in ((10, 2), (11, 2)):
        raise RuntimeError("Hayato Saque contact did not use the authored active pose")
    return {"player": actor, "normal": normal, "first_pose": expected,
            "start_tick": start["logic_tick"], "hit_tick": hit["logic_tick"],
            "hit_vdp_frame": hit["frame"], "opponent_life_before": before_hit,
            "opponent_life": hit[opponent]["life"],
            "local_pose_at_hit": local, "requested_at_hit": contact["pose_requested"],
            "resident_at_hit": contact["pose_resident"], "presented_at_hit": contact["pose_presented"]}


def record_round(session, destination, hold, impact_only=False, actions_round=False, after_walks=False):
    from capture_video import _self_check, evaluate_video, probe_video
    from session_bridge import isolated

    if _self_check() != 0:
        raise RuntimeError("The canonical video gate did not pass its self-check")

    root, metadata = isolated.load(session)
    if shutil.disk_usage(root).free < (MAX_VDP_FRAMES * FRAME_BYTES + 10 * 1024**3):
        raise RuntimeError("Round capture would consume the private disk reserve")
    destination.mkdir(parents=True, exist_ok=False)
    trace = []
    moves = []
    walks = []
    failure_snapshot = None
    stopped = None
    initial = isolated.request(session, "read", MFD1, RECORD_BYTES)
    raw = bytes(initial["ram"])
    if raw[:4] == b"MFD1" and raw[4] & 1:
        isolated.request(session, "sample-commit", MFD1 + 4, (raw[4] + 1) & 255)
        raw = bytes(isolated.request(session, "read", MFD1, RECORD_BYTES)["ram"])
    current = decode(raw)
    fighters = [current[player]["fighter"] for player in ("p1", "p2")]
    if (sorted(fighters) != [0, 1] or current["p1"]["pivot"][0] >= current["p2"]["pivot"][0] or
            any(current[player]["life"] != 100 or current[player]["state"] for player in ("p1", "p2"))):
        raise ValueError("Full round requires both actors fresh at 100 life with P1 on the left")
    if impact_only and fighters[0] != 0:
        raise ValueError("The archived first-punch probe requires Hayato on P1")
    input_masks = None
    opened = isolated.request(session, "record-steps-start", "full-round")

    def tick(p1=0, p2=0):
        nonlocal current, failure_snapshot, input_masks
        if len(trace) >= MAX_TICKS:
            raise RuntimeError("Round exceeded its logical tick budget")
        if input_masks != (p1, p2):
            isolated.request(session, "input", p1, p2, 0)
            input_masks = p1, p2
        target = (current["stamp"] + 2) & 255
        try:
            # Keep recording slow frames for diagnosis. The verdict still sees each VDP gap.
            ack = isolated.request(session, "sample-commit", MFD1 + 4, target, MAX_VDP_FRAMES_PER_COMMIT)
        except RuntimeError:
            failure_snapshot = isolated.request(session, "read", RENDER_METRICS, RENDER_METRICS_BYTES)
            raise
        data = isolated.request(session, "read", MFD1, RENDER_METRICS + RENDER_METRICS_BYTES - MFD1)
        record = bytes(data["ram"][:RECORD_BYTES])
        metrics = data["ram"][RENDER_METRICS - MFD1:]
        state = decode(record)
        if state["stamp"] != target or state["logic_tick"] != ((current["logic_tick"] + 1) & 65535):
            raise RuntimeError("Round lost a committed game tick")
        if ack["frame"] != data["frame"] or data["frame"] - opened["first_frame"] > MAX_VDP_FRAMES:
            raise RuntimeError("Round exceeded its VDP capture budget")
        current = state
        trace.append({"frame": data["frame"], "inputs": [p1, p2],
                      "stage_vlines": metrics[2:6], "stage_extra": metrics[9:14],
                      "render_stage_vlines": data["ram"][0xC7C0 - MFD1:0xC7C4 - MFD1],
                      "vblank_payload": data["ram"][0xC7C4 - MFD1:0xC7C8 - MFD1],
                      "sample_cycles": ack["cycles_advanced"],
                      "raw_hex": record.hex(), **state})

    def ready():
        for _ in range(45):
            if any(current[player]["state"] == 4 for player in ("p1", "p2")):
                return False
            if all(current[player]["state"] == 0 for player in ("p1", "p2")):
                return True
            tick()
        raise RuntimeError("Actors did not return to control after an action")

    def attack(player, normal):
        if not ready():
            return False
        for _ in range(72):
            gap = current["p2"]["pivot"][0] - current["p1"]["pivot"][0]
            if gap <= 29:
                break
            tick(RIGHT, 0) if player == 0 else tick(0, LEFT)
        else:
            raise RuntimeError("Round could not approach striking distance")
        tick()
        tick()
        first = len(trace)
        opponent = f"p{2 - player}"
        initial_life = current[opponent]["life"]
        if normal == 4:
            forward = RIGHT if player == 0 else LEFT
            for mask in (DOWN, DOWN, forward | BUTTON_ONE, forward | BUTTON_ONE):
                tick(mask, 0) if player == 0 else tick(0, mask)
        else:
            button = BUTTON_ONE if normal < 2 else BUTTON_TWO
            for _ in range(hold + 1 if normal & 1 else 2):
                tick(button, 0) if player == 0 else tick(0, button)
        tick()
        actor = f"p{player + 1}"
        for _ in range(3):
            if any(event[actor]["state"] == 1 for event in trace[first:]):
                break
            tick()
        ended = ready()
        segment = trace[first:]
        observed = observe_normal(segment, player, normal, initial_life, fighter=fighters[player])
        moves.append(observed)
        print(f"[ROUND] {actor} normal {normal} hit at {observed['hit_tick']} "
              f"opponent life {observed['opponent_life']}", flush=True)
        return ended

    def walk(player, backward):
        actor = f"p{player + 1}"
        rightward = backward == (player == 1)
        direction = RIGHT if rightward else LEFT
        start = current[actor]["pivot"][0]
        first = len(trace)
        for _ in range(32):
            tick(direction, 0) if player == 0 else tick(0, direction)
        tick()
        tick()
        finish = current[actor]["pivot"][0]
        pose_start = 29 + fighters[player] * 8 + (4 if backward else 0)
        segment = trace[first:]
        displayed = sorted({event[actor]["pose_presented"] for event in segment}
                           & set(range(pose_start, pose_start + 4)))
        walks.append({"player": actor, "direction": "backward" if backward else "forward",
                      "start_x": start, "finish_x": finish, "displayed": displayed,
                      "requested_frames": list(range(pose_start, pose_start + 4)),
                      "first_vdp_frame": segment[0]["frame"],
                      "last_vdp_frame": segment[-1]["frame"]})
        print(f"[ROUND] {actor} walk {start}->{finish}, displayed {displayed}", flush=True)
        if finish - start != (32 if rightward else -32):
            raise RuntimeError(f"{actor}: commanded walk did not travel 32 px")

    try:
        for _ in range(22):
            tick()
        if actions_round or after_walks:
            for backward in (True, False):
                for player in (0, 1):
                    walk(player, backward)
        if impact_only:
            attack(0, 0)
            hit = next(e for e in trace if e["logic_tick"] == moves[0]["hit_tick"])
            if (hit["p1"]["pivot"][0], hit["p2"]["pivot"][0], hit["p2"]["life"]) != (116, 148, 94):
                raise RuntimeError("Hayato punch differs from the archived contact geometry or damage")
        else:
            for normal in range(4):
                for player in (0, 1):
                    if not attack(player, normal):
                        raise RuntimeError("Round ended before all eight standing normals")
            if actions_round:
                for player in (0, 1):
                    if not attack(player, 4):
                        raise RuntimeError("Round ended before both specials")
            for _ in range(12):
                if not attack(0, 1):
                    break
            if current["p2"]["state"] != 4 or current["p2"]["life"] != 0:
                raise RuntimeError("The ROM did not reach the final knockout")
        for _ in range(45):
            tick()
    finally:
        try:
            stopped = isolated.request(session, "record-steps-stop")
        finally:
            isolated.request(session, "input", 0, 0, 0)
            (destination / "round-trace.json").write_text(json.dumps({
                "session_id": metadata["session_id"], "rom_sha256": metadata["rom_sha256"],
                "hold": hold, "moves": moves, "walks": walks, "samples": trace,
                "failure_snapshot": failure_snapshot,
                "recording": stopped,
            }, indent=2) + "\n", encoding="utf-8")

    frames = root / "evidence" / "full-round"
    count = stopped["recorded_frames"]
    if count != stopped["frame"] - stopped["first_frame"] or len(list(frames.glob("*.png"))) != count:
        raise RuntimeError("A VDP framebuffer is missing from the full-round capture")
    sequence_hash = hashlib.sha256()
    for index in range(count):
        image = frames / f"{index:06d}.png"
        sequence_hash.update(bytes.fromhex(isolated.sha(image)))
    if actions_round:
        # Commit follows the VBlank upload. Visible scanout of that submission
        # is in the next framebuffer callback, even when the probe already
        # reports the new pose. Preserve both sides of that boundary.
        saque = next(move for move in moves if move["first_pose"] == SPECIAL_STARTS[0])
        boundary = saque["hit_vdp_frame"]
        pictures = []
        for frame in range(boundary - 1, boundary + 3):
            index = frame - stopped["first_frame"] - 1
            if not 0 <= index < count:
                raise RuntimeError("Saque framebuffer lies outside the recording")
            image = destination / f"hayato-saque-vdp-{frame}.png"
            shutil.copy2(frames / f"{index:06d}.png", image)
            pictures.append({"vdp_frame": frame, "file": image.name, "sha256": isolated.sha(image)})
        saque["boundary_framebuffers"] = pictures
    basename = "impacto-soco" if impact_only else "round-completo"
    output = destination / f"{basename}.mp4"
    hz = stopped["nominal_hz"]
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-framerate", str(hz),
                    "-threads", "1", "-i", str(frames / "%06d.png"),
                    "-an", "-c:v", "libx264rgb", "-crf", "0", "-threads", "1", str(output)],
                   timeout=90, check=True, capture_output=True)
    ok, video = probe_video(str(output))
    if not ok:
        raise RuntimeError(video)
    ok, detail = evaluate_video(video)
    if not ok or video["frames"] != count:
        raise RuntimeError(f"Invalid full-round video: {detail}; expected {count} frames")
    registers = isolated.request(session, "read", RENDER_METRICS, RENDER_METRICS_BYTES)["ram"]
    vdp_gaps = [second["frame"] - first["frame"] for first, second in zip(trace, trace[1:])]
    summary = {
        "session_id": metadata["session_id"], "rom_sha256": metadata["rom_sha256"],
        "hold": hold, "frames": count, "canvas": [256, 192], "video_probe": video,
        "first_vdp_frame": stopped["first_frame"], "last_vdp_frame": stopped["frame"],
        "sha256": isolated.sha(output), "png_sequence_sha256": sequence_hash.hexdigest(),
        "knockout": None if impact_only else "p2", "moves": moves, "walks": walks, "playback_hz": hz,
        "capture": "frame-stepped Emulicious framebuffer", "audio": "not recorded",
        "logic_gaps_other_than_one_vdp": sum(gap != 1 for gap in vdp_gaps),
        "worst_vdp_frames_per_tick": max(vdp_gaps),
        "logical_updates_per_nominal_second": len(vdp_gaps) * hz / sum(vdp_gaps),
        "min_vline": registers[0], "delayed_presentations": registers[6] | registers[7] << 8,
        "renderer_fault": registers[8], "max_vline": registers[10],
        "missed_vblank_epochs": registers[12] | registers[13] << 8,
        "overruns": registers[25] | registers[26] << 8,
    }
    (destination / f"{basename}.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                     encoding="utf-8")
    return summary
