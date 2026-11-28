#!/usr/bin/env python3
"""Screen 8x8 tile phases geometrically; official conversion remains required."""
import hashlib
import json
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
BASE = PROJECT / "out/diagnostics/alis_strong_thrust_round1"
INPUT = BASE / "keypose_pair_redraw_ground_probe_01"
OUT = BASE / "redraw_phase_probe_01.json"


def objects(im, phase):
    px, py = phase
    occupied = [(x + px, y + py) for y in range(im.height) for x in range(im.width)
                if im.getpixel((x, y)) != 0]
    cells = sorted({(x // 8 * 8 - px, y // 8 * 8 - py) for x, y in occupied})
    if any(not (0 <= x < 128 and 0 <= y < 128) for x, y in cells):
        return None
    return cells


def peak(actor, rival):
    placed = [(24+x, 64+y) for x, y in actor] + [(136+x, 64+y) for x, y in rival]
    visible = all(0 <= x <= 248 and 0 <= y <= 184 and y != 208 for x, y in placed)
    return max(sum(y <= line < y + 8 for _, y in placed) for line in range(192)), len(placed), visible


def main():
    if OUT.exists():
        raise FileExistsError("preserve prior report")
    paths = {n: INPUT / (n + ".png") for n in ("idle", "thrust", "reference")}
    images = {n: Image.open(p) for n, p in paths.items()}
    rival = objects(images["reference"], (3, 5))
    guard = objects(images["idle"], (0, 0))
    if not rival or not guard or peak(guard, rival) != (8, 52, True):
        raise ValueError("guard geometry differs from official converter")
    results = []
    for y in range(8):
        for x in range(8):
            actor = objects(images["thrust"], (x, y))
            if actor is None:
                continue
            row_peak, count, visible = peak(actor, rival)
            results.append({"phase": [x, y], "peak": row_peak, "sat": count, "visible": visible})
    baseline = next(item for item in results if item["phase"] == [0, 0])
    if (baseline["peak"], baseline["sat"], baseline["visible"]) != (9, 51, True):
        raise ValueError("thrust geometry differs from official converter")
    viable = [r for r in results if r["peak"] <= 8 and r["sat"] <= 64 and r["visible"]]
    report = {"status": "diagnostic_requires_official_reconversion", "phases_checked": len(results),
              "source_sha256": {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in paths.items()},
              "reference_phase": [3, 5], "guard_phase": [0, 0], "guard_peak": 8,
              "thrust_baseline": baseline, "viable": viable,
              "limits": "Geometry of fixed poses/positions only; not pattern residency, all distances, other facing, VBlank or emulator proof."}
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
