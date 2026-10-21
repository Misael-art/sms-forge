#!/usr/bin/env python3
"""Check that Dr. Social's fabric-ramp correction preserves other pixels.

This audit checks conversion invariants (mask, alpha, and allowed RGB changes).
It does not decide whether the resulting shade flow is artistically correct.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

from PIL import Image


RAMP = {(0, 85, 85), (0, 170, 170), (85, 170, 255)}


class AuditError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compare_frames(before_path: Path, after_path: Path) -> dict:
    before = Image.open(before_path).convert("RGBA")
    after = Image.open(after_path).convert("RGBA")
    if before.size != after.size:
        raise AuditError(f"canvas changed: {before_path.name}: {before.size} -> {after.size}")

    changed = 0
    alpha_changed = 0
    out_of_ramp = 0
    partial_alpha = 0
    transitions: Counter[tuple[tuple[int, int, int], tuple[int, int, int]]] = Counter()
    for old, new in zip(before.get_flattened_data(), after.get_flattened_data()):
        if old[3] not in (0, 255) or new[3] not in (0, 255):
            partial_alpha += 1
        if old[3] != new[3]:
            alpha_changed += 1
            continue
        if old[3] == 0 or old[:3] == new[:3]:
            continue
        changed += 1
        transitions[(old[:3], new[:3])] += 1
        if old[:3] not in RAMP or new[:3] not in RAMP:
            out_of_ramp += 1

    if alpha_changed:
        raise AuditError(f"alpha/silhouette changed in {before_path.name}: {alpha_changed} pixels")
    if partial_alpha:
        raise AuditError(f"non-binary alpha in {before_path.name}: {partial_alpha} pixels")
    if out_of_ramp:
        raise AuditError(f"changes outside the declared cloth ramp in {before_path.name}: {out_of_ramp}")

    return {
        "frame": before_path.stem,
        "before_sha256": sha256_file(before_path),
        "after_sha256": sha256_file(after_path),
        "dimensions_px": list(before.size),
        "changed_pixels": changed,
        "alpha_changed_pixels": alpha_changed,
        "out_of_ramp_changes": out_of_ramp,
        "rgb_transitions": [
            {"from": list(old), "to": list(new), "pixels": count}
            for (old, new), count in sorted(transitions.items())
        ],
    }


def audit_directories(before_dir: Path, after_dir: Path,
                      expected_frames: int) -> dict:
    before_files = {p.name: p for p in before_dir.glob("*.png")}
    after_files = {p.name: p for p in after_dir.glob("*.png")}
    if len(before_files) != expected_frames or len(after_files) != expected_frames:
        raise AuditError(
            f"expected {expected_frames} PNGs in each directory; got "
            f"{len(before_files)} before and {len(after_files)} after"
        )
    if set(before_files) != set(after_files):
        missing_after = sorted(set(before_files) - set(after_files))
        missing_before = sorted(set(after_files) - set(before_files))
        raise AuditError(f"frame set mismatch: missing_after={missing_after}, missing_before={missing_before}")

    frames = [compare_frames(before_files[name], after_files[name])
              for name in sorted(before_files)]
    return {
        "schema": "dr_social_fabric_ramp_delta_audit_v1",
        "status": "pass",
        "before_dir": str(before_dir),
        "after_dir": str(after_dir),
        "expected_frames": expected_frames,
        "checked_frames": len(frames),
        "ramp_rgb": [list(color) for color in sorted(RAMP)],
        "changed_pixels": sum(frame["changed_pixels"] for frame in frames),
        "alpha_changed_pixels": sum(frame["alpha_changed_pixels"] for frame in frames),
        "out_of_ramp_changes": sum(frame["out_of_ramp_changes"] for frame in frames),
        "frames": frames,
        "limits": (
            "Checks that only opaque RGB values in the declared fabric ramp changed, "
            "that alpha/silhouette stayed fixed, and that frame canvases/IDs match. "
            "Does not judge artistic shade-flow coherence."
        ),
    }


def self_check() -> None:
    with tempfile.TemporaryDirectory(prefix="dr-social-ramp-audit-") as temp:
        root = Path(temp)
        old = Image.new("RGBA", (2, 2), (0, 170, 170, 255))
        old.putpixel((1, 1), (0, 0, 0, 0))
        valid = old.copy()
        valid.putpixel((0, 0), (0, 85, 85, 255))
        before_path, valid_path = root / "old.png", root / "valid.png"
        old.save(before_path)
        valid.save(valid_path)
        result = compare_frames(before_path, valid_path)
        assert result["changed_pixels"] == 1 and result["alpha_changed_pixels"] == 0

        invalid = old.copy()
        invalid.putpixel((0, 0), (85, 0, 0, 255))
        invalid_path = root / "invalid.png"
        invalid.save(invalid_path)
        try:
            compare_frames(before_path, invalid_path)
        except AuditError as exc:
            assert "outside the declared cloth ramp" in str(exc)
        else:
            raise AssertionError("audit accepted an out-of-ramp pixel change")

    print("[SELF-CHECK OK] fabric ramp delta audit preserves alpha and rejects unrelated color changes")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, help="previous indexed sprite directory")
    parser.add_argument("--after", type=Path, help="corrected indexed sprite directory")
    parser.add_argument("--expected-frames", type=int, default=61)
    parser.add_argument("--out", type=Path, help="write JSON report")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        self_check()
        return 0
    if not args.before or not args.after:
        parser.error("--before and --after are required unless --self-check is used")
    try:
        report = audit_directories(args.before, args.after, args.expected_frames)
    except (OSError, AuditError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    print("[PASS] conversion delta stays inside the declared fabric ramp; art judgment remains human")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
