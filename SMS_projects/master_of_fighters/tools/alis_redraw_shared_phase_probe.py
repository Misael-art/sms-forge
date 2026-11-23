#!/usr/bin/env python3
"""Bounded 8x8 phase geometry search for the redraw and a shared rival."""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "out/diagnostics/alis_strong_thrust_round1"
INPUT = BASE / "keypose_pair_redraw_ground_probe_01"
OUT = BASE / "redraw_shared_phase_probe_01.json"


def phases(image, origin_x):
    coordinates = [(x, y) for y in range(image.height) for x in range(image.width)
                   if image.getpixel((x, y)) != 0]
    result = {}
    for py in range(8):
        for px in range(8):
            cells = {(8*((x+px)//8)-px, 8*((y+py)//8)-py) for x, y in coordinates}
            if not all(0 <= x < 128 and 0 <= y < 128 and
                       0 <= origin_x+x <= 248 and 64+y <= 184 for x, y in cells):
                continue
            counts = [0] * 192
            for x, y in cells:
                for row in range(64+y, 64+y+8):
                    counts[row] += 1
            result[(px, py)] = (len(cells), counts)
    return result


def maximum(a, b):
    return max(x+y for x, y in zip(a, b))


def main():
    if OUT.exists():
        raise FileExistsError("preserve prior report")
    paths = {n: INPUT / (n+".png") for n in ("idle", "thrust", "reference")}
    im = {n: Image.open(p) for n, p in paths.items()}
    guard, thrust, ref = phases(im["idle"], 24), phases(im["thrust"], 24), phases(im["reference"], 136)
    assert maximum(guard[(0, 0)][1], ref[(3, 5)][1]) == 8
    assert maximum(thrust[(0, 0)][1], ref[(3, 5)][1]) == 9
    solutions = []
    for ref_phase, (ref_count, ref_lines) in ref.items():
        g = [(p, count) for p, (count, lines) in guard.items()
             if count+ref_count <= 64 and maximum(lines, ref_lines) <= 8]
        t = [(p, count) for p, (count, lines) in thrust.items()
             if count+ref_count <= 64 and maximum(lines, ref_lines) <= 8]
        if g and t:
            solutions.append({"reference_phase": ref_phase,
                              "guard_phases": [p for p, _ in g],
                              "thrust_phases": [p for p, _ in t]})
    report = {"status": "diagnostic_requires_official_reconversion", "guard_phase_count": len(guard),
              "thrust_phase_count": len(thrust), "reference_phase_count": len(ref),
              "source_sha256": {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in paths.items()},
              "solutions": solutions,
              "limits": "8x8 geometry on one set of positions and facing; does not establish legal VRAM, all distances or runtime. Reconvert and use official scene simulation before any use."}
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
