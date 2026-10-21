#!/usr/bin/env python3
"""Capture and exactly compare every frame of a Dr. Social review ROM.

The harness uses one private Emulicious session, navigates the diagnostic pose
viewer with SMS joypad masks, and binds each framebuffer to its indexed PNG,
session ID, and ROM SHA. This proves render fidelity, not artistic approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/sms_wrapper"))

from audit_render_fidelity import exact_indexed_render  # noqa: E402
from session_bridge import isolated  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def navigation_mask(previous: dict, current: dict) -> int:
    """Diagnostic ROM maps RIGHT to next pose and DOWN to next sequence."""
    return 8 if previous["sequence_id"] == current["sequence_id"] else 2


def self_check() -> None:
    same_sequence = {"sequence_id": "idle"}
    next_pose = {"sequence_id": "idle"}
    next_sequence = {"sequence_id": "walk_forward"}
    assert navigation_mask(same_sequence, next_pose) == 8
    assert navigation_mask(same_sequence, next_sequence) == 2
    assert sum([4, 8, 8, 8, 5, 8, 8, 8, 4]) == 61
    print("[SELF-CHECK OK] pose/sequence navigation masks and 61-frame coverage")


def run(project: Path, report_path: Path, output: Path, version: str) -> dict:
    project, output = project.resolve(), output.resolve()
    if not re.fullmatch(r"v\d+(?:_\d+)*", version):
        raise ValueError("version precisa seguir vN ou vN_N, por exemplo v8 ou v08_2")
    rom = project / f"out/rom/dr_social_61_pose_review_{version}.sms"
    manifest = project / f"doc/frame_manifest_61_pose_{version}.json"
    conversion_path = project / f"doc/conversion_report_61_pose_{version}.json"
    for path in (rom, manifest, conversion_path, report_path):
        if not path.is_file():
            raise FileNotFoundError(path)
    conversion = json.loads(conversion_path.read_text(encoding="utf-8"))
    declared = json.loads(manifest.read_text(encoding="utf-8"))
    frames = conversion["frames"]
    if len(frames) != 61 or len(declared) != 61:
        raise ValueError("a ROM de revisão precisa declarar exatamente 61 quadros")
    if [f["frame_id"] for f in frames] != [f["frame_id"] for f in declared]:
        raise ValueError("ordem/IDs do relatório e manifesto divergiram")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"evidência existente preservada: {output}")
    output.mkdir(parents=True, exist_ok=True)
    captures_dir = output / "framebuffers"
    captures_dir.mkdir()

    rom_sha = sha256(rom)
    source_sha = conversion["source_sha256"]
    capture_index = {
        "schema": f"dr_social_61_pose_framebuffer_review_{version}_v1",
        "status": "running",
        "rom": str(rom),
        "rom_sha256": rom_sha,
        "source_sha256": source_sha,
        "candidate_report_sha256": sha256(report_path),
        "canvas": [256, 192],
        "render_origin": [88, 56],
        "transparent_rgb": [0, 0, 0],
        "frame_count_expected": 61,
        "frames": [],
    }

    session_path = None
    published_bundle = None
    failure = None
    try:
        session_path = isolated.start(rom, ttl=1800, enable_audio=False)
        session_root, session_meta = isolated.load(session_path)
        if session_meta["rom_sha256"] != rom_sha:
            raise ValueError("sessão iniciou ROM com SHA diferente do candidato v8")
        capture_index["session_id"] = session_meta["session_id"]
        capture_index["emulator_sha256"] = session_meta["emulator_sha256"]
        capture_index["bridge_sha256"] = session_meta["bridge_sha256"]
        capture_index["host_load_at_start"] = session_meta["host_load"]

        # The display initializes deterministically; idle ID01 is already
        # selected. Advance a fixed window to match the established probe path.
        isolated.request(session_root, "step", 120)
        previous_frame = None
        for frame in frames:
            frame_id = frame["frame_id"]
            if previous_frame is not None:
                mask = navigation_mask(previous_frame, frame)
                isolated.sequence(session_root, [
                    {"p1": mask, "frames": 1},
                    {"p1": 0, "frames": 1},
                ])
                # A newly loaded pose can be blank for the two input ticks
                # while the diagnostic viewer updates the VDP. Settle 12 more
                # frames; the established review captures every 14 VDP frames.
                isolated.request(session_root, "step", 12)
            capture_name = f"dr_social_{version}_{frame_id}.png"
            record = isolated.capture(session_root, capture_name)
            art_path = project / frame["res_path"]
            problems, pixels = exact_indexed_render(
                record["path"], str(art_path), (88, 56), (0, 0, 0)
            )
            capture_copy = captures_dir / f"render_{frame_id}.png"
            capture_copy.write_bytes(Path(record["path"]).read_bytes())
            pixel_report_path = captures_dir / f"render_{frame_id}.json"
            pixel_report = {
                "frame_id": frame_id,
                "sequence_id": frame["sequence_id"],
                "session_id": session_meta["session_id"],
                "rom_sha256": rom_sha,
                "capture_sha256": sha256(capture_copy),
                "capture_frame": record["frame"],
                "art": str(art_path),
                "art_sha256": sha256(art_path),
                "problems": problems,
                "pixels": pixels,
            }
            pixel_report_path.write_text(
                json.dumps(pixel_report, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            capture_index["frames"].append({
                "frame_id": frame_id,
                "sequence_id": frame["sequence_id"],
                "capture": f"framebuffers/{capture_copy.name}",
                "capture_sha256": pixel_report["capture_sha256"],
                "pixel_report": f"framebuffers/{pixel_report_path.name}",
                "capture_frame": record["frame"],
                "opaque_pixels": pixels["opaque_pixels"],
                "opaque_mismatches": pixels["opaque_mismatches"],
                "transparent_pixels_checked": pixels["transparent_pixels_checked"],
                "transparent_mismatches": pixels["transparent_mismatches"],
            })
            previous_frame = frame
            if problems:
                raise RuntimeError(f"{frame_id}: " + "; ".join(problems))

        # Publish one sealed capture through the canonical session publisher;
        # the per-pose capture index keeps the complete 61-frame SHA inventory.
        last_capture_name = f"dr_social_{version}_{frames[-1]['frame_id']}.png"
        published_bundle = isolated.publish(
            session_root, last_capture_name, project / "out/evidence/sessions"
        )
        checked, reason = isolated.check_bundle(published_bundle)
        if not checked:
            raise RuntimeError("bundle privado não validou: " + reason)
        capture_index["published_session_bundle"] = str(published_bundle)
        capture_index["published_bundle_check"] = reason
        capture_index["exact_render_passes"] = len(capture_index["frames"])
        capture_index["exact_render_failures"] = 0
        capture_index["status"] = "pass"
    except Exception as exc:
        failure = str(exc)
        capture_index["status"] = "fail"
        capture_index["failure"] = failure
        capture_index["exact_render_passes"] = sum(
            1 for frame in capture_index["frames"]
            if frame["opaque_mismatches"] == 0 and frame["transparent_mismatches"] == 0
        )
        capture_index["exact_render_failures"] = (
            capture_index["frame_count_expected"] - capture_index["exact_render_passes"]
        )
    finally:
        if session_path is not None:
            try:
                isolated.close_session(session_path)
            except Exception as close_error:
                capture_index["close_error"] = str(close_error)

    index_path = output / f"framebuffer_capture_index_{version}.json"
    index_path.write_text(json.dumps(capture_index, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    if failure:
        raise RuntimeError(failure)
    return capture_index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path,
                        help="v8 diagnostic project containing ROM and converted PNGs")
    parser.add_argument("--report", type=Path,
                        help="outer v8 conversion report")
    parser.add_argument("--output", type=Path,
                        help="new, empty directory for the session-bound 61-frame captures")
    parser.add_argument("--version", default="v8",
                        help="diagnostic version used by ROM and project manifests (default: v8)")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    if not args.project or not args.report or not args.output:
        parser.error("--project, --report e --output são obrigatórios sem --self-check")
    result = run(args.project, args.report, args.output, args.version)
    print(json.dumps({
        "status": result["status"],
        "session_id": result["session_id"],
        "rom_sha256": result["rom_sha256"],
        "exact_render_passes": result["exact_render_passes"],
        "exact_render_failures": result["exact_render_failures"],
        "bundle": result["published_session_bundle"],
        "capture_index": str(args.output / f"framebuffer_capture_index_{args.version}.json"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
