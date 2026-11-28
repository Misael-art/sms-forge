#!/usr/bin/env python3
"""Sample round-1 probes while stepping an existing private Emulicious session.

This tool does not start or close sessions, and stepping is not FPS evidence.
Use a fresh Alis diagnostic ROM session and validate its probe corridor first.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/sms_wrapper"))
from session_bridge import isolated  # noqa: E402

BASE = 0xC7F0
LENGTH = 15


def decode(ram):
    if len(ram) != LENGTH or any(type(v) is not int or not 0 <= v <= 255 for v in ram):
        raise ValueError("invalid probe read")
    return {"loop_frame": ram[0] | ram[1] << 8, "pose": ram[6], "keys": ram[8],
            "pose_elapsed": ram[9], "latch": ram[10], "triggers": ram[11],
            "pressure": ram[12], "flags": ram[13], "distance": ram[14]}


def self_check():
    fixture = [0] * LENGTH
    fixture[0:2] = [0x34, 0x12]
    fixture[6], fixture[9], fixture[10], fixture[11], fixture[12] = 3, 5, 1, 7, 12
    observed = decode(fixture)
    assert observed["loop_frame"] == 0x1234 and observed["pose"] == 3
    assert observed["pose_elapsed"] == 5 and observed["latch"] == 1
    assert observed["triggers"] == 7 and observed["pressure"] == 12
    try:
        decode([0] * (LENGTH - 1))
    except ValueError:
        pass
    else:
        raise AssertionError("short probe read accepted")
    print("[SELF-CHECK OK] probe offsets and malformed sample rejection")


def run(session, expected_sha, mode, hold_frames, output, capture_frames):
    root, meta = isolated.load(session)
    if meta["rom_sha256"] != expected_sha:
        raise ValueError("session ROM SHA does not match requested SHA")
    if output.exists():
        raise FileExistsError("preserve prior trace")
    samples = []

    def read(label):
        result = isolated.request(root, "read", BASE, LENGTH)
        sample = {"label": label, "vdp_frame": result["frame"], **decode(result["ram"])}
        if capture_frames:
            name = f"alis_trace_{mode}_{len(samples):03}.png"
            if (root / "evidence" / name).exists() or (root / "evidence" / name).with_suffix(".json").exists():
                raise FileExistsError("preserve prior capture; use a fresh session")
            capture = isolated.capture(root, name)
            sample["framebuffer"] = {"path": capture["path"], "sha256": capture["sha256"],
                                     "frame": capture["frame"]}
        samples.append(sample)
        return sample

    def step(label):
        isolated.request(root, "step", 1)
        return read(label)

    baseline = read("baseline")
    if baseline["pose"] != 0 or baseline["pressure"] != 0 or baseline["latch"] != 0:
        raise ValueError("baseline is not released guard")
    outcome = "incomplete"
    try:
        isolated.request(root, "input", 16, 0, 0)
        if mode == "press":
            for _ in range(hold_frames):
                step("pressed")
        else:
            for _ in range(32):
                current = step("first_press")
                if current["triggers"] != baseline["triggers"]:
                    break
            else:
                raise RuntimeError("first trigger not observed within 32 VDP frames")
            isolated.request(root, "input", 0, 0, 0)
            current = step("release_during_action")
            for _ in range(32):
                if current["pose"] == 1 and current["pose_elapsed"] == 3:
                    break
                if current["pose"] == 0:
                    raise RuntimeError("guard returned before timing setup")
                current = step("wait_until_pose1_elapsed3")
            else:
                raise RuntimeError("timing setup not observed")
            isolated.request(root, "input", 16, 0, 0)
            for _ in range(16):
                step("repress_last_recovery_attempt")
        isolated.request(root, "input", 0, 0, 0)
        step("released")
        outcome = "collected_requires_interpretation"
    finally:
        try:
            isolated.request(root, "input", 0, 0, 0)
        finally:
            result = {"status": outcome, "session_id": meta["session_id"],
                      "rom_sha256": meta["rom_sha256"], "mode": mode,
                      "samples": samples,
                      "limits": "VDP-step trace only; no FPS, autonomous collision, physical input, or visual quality verdict. Verify last recovery boundary and presented framebuffer separately."}
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": outcome, "samples": len(samples), "output": str(output)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--session")
    parser.add_argument("--rom-sha256")
    parser.add_argument("--mode", choices=("press", "last_recovery"), default="press")
    parser.add_argument("--hold-frames", type=int, default=12)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--capture-frames", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return
    if not args.session or not args.rom_sha256 or len(args.rom_sha256) != 64 or not args.output:
        parser.error("session, exact ROM SHA-256 and output are required")
    if not 1 <= args.hold_frames <= 300:
        parser.error("hold-frames must be between 1 and 300")
    run(args.session, args.rom_sha256, args.mode, args.hold_frames, args.output, args.capture_frames)


if __name__ == "__main__":
    main()
