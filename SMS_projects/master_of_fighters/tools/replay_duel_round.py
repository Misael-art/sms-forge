"""Record a new private Emulicious session in continuous time using a round trace."""

import json
from pathlib import Path
import shutil
import struct
import subprocess
import time

from capture_audio import RATE, _peak
from capture_video import evaluate_video, probe_video
from duel_probe import RECORD_BYTES, decode
from measure_runtime_probe import target_fps_verdict
from record_duel_repertoire import MFD1
from session_bridge import isolated

FRAME_STAMP = struct.Struct(">q")
CAPTURE_RECORD_BYTES = FRAME_STAMP.size + RECORD_BYTES


def make_timeline(trace):
    start = trace["recording"]["first_frame"]
    count = trace["recording"]["recorded_frames"]
    if not 60 <= count <= 1800:
        raise ValueError("The replay must fit a single native capture")
    previous = start
    fixed = bytearray(count * 2)
    for event in trace["samples"]:
        shown = event["frame"]
        if not previous <= shown <= start + count:
            raise ValueError("Trace crossed the original capture bounds")
        fixed[(previous - start) * 2:(shown - start) * 2] = bytes(event["inputs"]) * (shown - previous)
        previous = shown
    return fixed


def observed_round(raw):
    if not raw or len(raw) % CAPTURE_RECORD_BYTES:
        raise ValueError("Frame probe has an incomplete record")
    observed, contacts, elapsed = [], [], []
    origin = FRAME_STAMP.unpack_from(raw)[0]
    previous = origin - 1
    for index, start in enumerate(range(0, len(raw), CAPTURE_RECORD_BYTES)):
        stamp = FRAME_STAMP.unpack_from(raw, start)[0]
        if stamp <= previous:
            raise ValueError("Native frame timestamps must increase monotonically")
        previous = stamp
        elapsed.append(stamp - origin)
        try:
            event = decode(raw[start + FRAME_STAMP.size:start + CAPTURE_RECORD_BYTES])
        except ValueError:
            continue
        if observed and event["logic_tick"] == observed[-1]["logic_tick"]:
            continue
        observed.append({"video_frame": index, "elapsed_ns": elapsed[-1], **event})
        for player, rival in (("p1", "p2"), ("p2", "p1")):
            actor = event[player]
            if actor["contact"] == 1:
                contacts.append({"player": player, "video_frame": index, "logic_tick": event["logic_tick"],
                                 "requested": actor["pose_requested"], "resident": actor["pose_resident"],
                                 "presented": actor["pose_presented"], "life": event[rival]["life"]})
    return observed, contacts, elapsed


def fight_cadence(samples, hz):
    windows = []
    active = [event for event in samples if event["p1"]["state"] == 1 or event["p2"]["state"] == 1]
    if active and active[-1]["video_frame"] - active[0]["video_frame"] >= 240:
        for offset in (active[0]["video_frame"], active[-1]["video_frame"] - 120):
            begin, end = (next(event for event in samples if event["video_frame"] >= frame)
                          for frame in (offset, offset + 120))
            span = end["video_frame"] - begin["video_frame"]
            elapsed = end["elapsed_ns"] - begin["elapsed_ns"]
            delta = (end["logic_tick"] - begin["logic_tick"]) & 65535
            windows.append({"start_frame": begin["video_frame"], "end_frame": end["video_frame"],
                            "logic_ticks": delta, "elapsed_ns": elapsed,
                            "logical_updates_per_nominal_second": delta * hz / span,
                            "logical_updates_per_wall_second": delta * 1e9 / elapsed})
    region = "NTSC" if 58 <= hz <= 61 else "PAL" if 49 <= hz <= 51 else None
    nominal = target_fps_verdict([row["logical_updates_per_nominal_second"] for row in windows], region)
    wall = target_fps_verdict([row["logical_updates_per_wall_second"] for row in windows], region)
    return {"windows": windows, "nominal_verdict": nominal, "wall_verdict": wall,
            "passed": nominal["passed"] and wall["passed"]}


def frame_timing_filter(elapsed):
    """Use the recorded frame times as video PTS, in integer microseconds."""
    pts = [value // 1000 for value in elapsed]
    if not pts or pts[0] or any(before >= after for before, after in zip(pts, pts[1:])):
        raise ValueError("Captured video timestamps must increase from zero")

    def expression(begin, end):
        if end - begin == 1:
            return str(pts[begin])
        mid = (begin + end) // 2
        return f"if(lt(N,{mid}),{expression(begin, mid)},{expression(mid, end)})"

    return f"trim=end_frame={len(pts)},settb=1/1000000,setpts='{expression(0, len(pts))}'"


def sample_state(root):
    ack = isolated.request(root, "read", MFD1, RECORD_BYTES)
    raw = bytes(ack["ram"])
    if raw[:4] == b"MFD1" and raw[4] & 1:
        isolated.request(root, "sample-commit", MFD1 + 4, (raw[4] + 1) & 255)
        ack = isolated.request(root, "read", MFD1, RECORD_BYTES)
    return ack, decode(bytes(ack["ram"]))


def snapshot_sat(root):
    head = isolated.request(root, "read-vram", 0x3F00, 256)
    base = head["sat_address"]
    if base != 0x3F00:
        head = isolated.request(root, "read-vram", base, 256)
    sprites = head["vram"]
    count = next((i for i, value in enumerate(sprites[:64]) if value == 0xD0), 64)
    patterns = isolated.request(root, "read-vram", 0, 0x2000)["vram"]
    height = [0] * 192
    objects = []
    for i in range(count):
        x, slot = sprites[128 + 2*i:130 + 2*i]
        y = (sprites[i] + 1) & 255
        data = patterns[slot*32:(slot+1)*32]
        for line in range(y, min(y + 8, 192)):
            height[line] += 1
        objects.append({"x": x, "y": y, "slot": slot, "nonzero_pattern": any(data)})
    return {"vdp_frame": head["frame"], "address": base, "entries": count,
            "max_per_scanline": max(height), "objects": objects, "sat_bytes": sprites}


def record_replay(session, trace_path, destination):
    trace = json.loads(trace_path.read_bytes())
    root, meta = isolated.load(session)
    if trace["rom_sha256"] != meta["rom_sha256"] or not trace["samples"]:
        raise ValueError("Replay requires inputs exercised on this exact ROM")
    fresh, state = sample_state(root)
    if fresh["frame"] != trace["recording"]["first_frame"]:
        raise ValueError("Fresh boot is on a different VDP frame than the recorded input")
    if any(state[player]["life"] != 100 or state[player]["state"] != 0 for player in ("p1", "p2")):
        raise ValueError("Continuous capture must start with a fresh round")
    if not fresh["audio_enabled"] or not meta.get("audio_route") or not isolated.verify_audio_route(meta):
        raise RuntimeError("Unverified private audio route for continuous capture")
    inputs = make_timeline(trace)
    count = len(inputs) // 2
    if shutil.disk_usage(root).free < (count + 72) * 256 * 192 * 3 + 10 * 1024**3:
        raise RuntimeError("Continuous capture would use the reserved disk space")

    name = "round-continuo"
    spool = root / "evidence"
    initial_sat = snapshot_sat(root)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "boot-sat.json").write_text(json.dumps({"session_id": meta["session_id"],
        "rom_sha256": meta["rom_sha256"], **initial_sat}, indent=2) + "\n", encoding="utf-8")
    (spool / f"{name}.inputs").write_bytes(inputs)
    pcm = spool / f"{name}.pcm"
    with pcm.open("xb") as audio_file:
        recorder = subprocess.Popen(["parec", "-d", f"{meta['audio_sink']}.monitor", "--raw",
                                     "--format=s16le", f"--rate={RATE}", "--channels=1",
                                     "--latency-msec=30"], stdout=audio_file, stderr=subprocess.PIPE)
        try:
            time.sleep(0.4)
            audio_deadline = time.monotonic() + 3
            while not pcm.stat().st_size:
                if recorder.poll() is not None:
                    detail = recorder.stderr.read().decode(errors="replace").strip()
                    raise RuntimeError(f"Private monitor failed: {detail}")
                if time.monotonic() >= audio_deadline:
                    raise RuntimeError("Private monitor did not produce PCM before capture")
                time.sleep(0.04)
            if recorder.poll() is not None:
                raise RuntimeError("Private monitor stopped before capture")
            audio_lead = pcm.stat().st_size / (2 * RATE)
            started = isolated.request(root, "record-start", name, "vdp-replay", MFD1, RECORD_BYTES)
            try:
                first = started["first_frame"]
                deadline = time.monotonic() + 90
                while isolated.request(root, "status")["frame"] < first + count:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Continuous run reached its capture deadline")
                    time.sleep(0.25)
            finally:
                stopped = isolated.request(root, "record-stop")
                (destination / "record-stop.json").write_text(json.dumps({
                    "rom_sha256": meta["rom_sha256"], "target_frames": count, **stopped,
                }, indent=2) + "\n", encoding="utf-8")
        finally:
            if recorder.poll() is None:
                recorder.terminate()
                try:
                    recorder.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    recorder.kill()
                    recorder.wait(timeout=3)
            recorder.stderr.close()

    if not isolated.verify_audio_route(meta):
        raise RuntimeError("Private audio route changed during the round")
    raw_video = spool / f"{name}.rgb"
    frames = stopped["recorded_frames"]
    vdp_frames = stopped["frame"] - first
    rgb_bytes = raw_video.stat().st_size
    # Stopping can land between rendering a frame and the pad's VDP callback.
    # Both streams must cover the whole scripted round before trimming the tail.
    if min(frames, vdp_frames) < count or abs(vdp_frames - frames) > 1 or rgb_bytes != frames * 256 * 192 * 3:
        raise RuntimeError("Native RGB capture is missing VDP frames")
    hz = stopped["nominal_hz"]
    raw = (spool / f"{name}.commits").read_bytes()
    if len(raw) != count * CAPTURE_RECORD_BYTES:
        raise RuntimeError("Continuous probe is missing native frame samples")
    samples, contacts, elapsed = observed_round(raw)
    last_packet_us = round(1e6 / hz)
    duration = (elapsed[-1] // 1000 + last_packet_us) / 1e6
    audio_pcm = pcm.read_bytes()[int(audio_lead * RATE) * 2:int((audio_lead + duration) * RATE) * 2]
    if len(audio_pcm) / (RATE * 2) < duration - 0.15 or not _peak(audio_pcm):
        raise RuntimeError("The private monitor has incomplete or silent PCM")
    _, finish = sample_state(root)
    expected_hits = [(move["player"], move["requested_at_hit"], move["opponent_life"])
                     for move in trace["moves"]]
    shown = [(hit["player"], hit["requested"], hit["life"]) for hit in contacts]
    guards = [
        dict(player=player, video_frame=row["video_frame"], logic_tick=row["logic_tick"],
             request=row[player]["pose_requested"], display=row[player]["pose_presented"],
             opponent_life=row[rival]["life"])
        for row in samples for player, rival in (("p1", "p2"), ("p2", "p1"))
        if row[player]["contact"] == 2
    ]
    expected_guards = [
        (player, row[player]["pose_requested"], row[rival]["life"])
        for row in trace["samples"] for player, rival in (("p1", "p2"), ("p2", "p1"))
        if row[player]["contact"] == 2
    ]
    walks = [{**walk, "observed_in_replay": sorted({event[walk["player"]]["pose_presented"] for event in samples}
                                                 & set(walk["requested_frames"]))} for walk in trace.get("walks", [])]
    cadence = fight_cadence(samples, hz)

    video = destination / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "rawvideo", "-pixel_format", "rgb24",
                    "-video_size", "256x192", "-framerate", str(hz), "-i", str(raw_video), "-ss",
                    str(audio_lead), "-f", "s16le", "-ar", str(RATE), "-ac", "1", "-i", str(pcm),
                    "-vf", frame_timing_filter(elapsed), "-filter_threads", "1", "-fps_mode", "passthrough",
                    "-enc_time_base:v", "1:1000000", "-video_track_timescale", "1000000",
                    "-bsf:v", f"setts=duration='if(eq(N,{count - 1}),{last_packet_us},DURATION)'",
                    "-c:v", "libx264rgb", "-crf", "0", "-threads", "1", "-c:a", "aac", "-b:a", "128k",
                    "-t", str(duration), str(video)], check=True, timeout=90)
    ok, video_info = probe_video(str(video))
    if not ok or not evaluate_video(video_info)[0] or video_info["frames"] != count or not video_info["has_audio"]:
        raise RuntimeError("Continuous MP4 failed the native video gate")
    (destination / "probe.json").write_text(json.dumps(samples, indent=2) + "\n", encoding="utf-8")
    saved_pcm = destination / f"{name}.pcm"
    shutil.copyfile(pcm, saved_pcm)
    receipt = {"session_id": meta["session_id"], "rom_sha256": meta["rom_sha256"],
               "source_session": trace["session_id"], "input_sha256": isolated.sha(spool / f"{name}.inputs"),
               "video_sha256": isolated.sha(video), "video": video_info, "scoped_audio_peak": _peak(audio_pcm),
               "pcm": {"file": saved_pcm.name, "sha256": isolated.sha(saved_pcm),
                       "format": "s16le", "rate": RATE, "channels": 1},
               "first_vdp_frame": first, "last_vdp_frame": stopped["frame"], "playback_hz": hz,
               "capture_elapsed_ns": stopped["capture_elapsed_ns"], "target_duration_s": duration,
               "captured_vdp_frames": vdp_frames, "captured_rgb_frames": frames,
               "audio_lead_seconds": audio_lead, "actual_contacts": contacts, "expected_contacts": expected_hits,
               "guards": guards, "same_guards": [
                   (row["player"], row["request"], row["opponent_life"]) for row in guards] == expected_guards,
               "walks": walks, "ntsc_windows": cadence["windows"], "cadence": cadence,
               "knockout": bool(samples and samples[-1]["p2"]["state"] == finish["p2"]["state"] == 4),
               "same_contacts": shown == expected_hits}
    (destination / f"{name}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt
