#!/usr/bin/env python3
"""Apply one hash-bound, local alpha cleanup to the Alis keypose study."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root / "data/source_art/sprite_studies/alis/strong_thrust_round1"
    source = folder / "keyposes_01.png"
    out = folder / "keyposes_guard_masked_01.png"
    mask_path = folder / "keyposes_guard_mask_01.png"
    receipt = folder / "keyposes_guard_mask_01.json"
    if digest(source) != "fb1ddcaf94154bcd9a01a1807d6b07c21ae989187ab37e3ad6979162277cf28b":
        raise ValueError("source SHA changed")
    if any(p.exists() for p in (out, mask_path, receipt)):
        raise FileExistsError("preserve existing output")
    image = Image.open(source).convert("RGBA")
    before = image.tobytes()
    mask = Image.new("L", image.size, 0)
    pixels, marked = image.load(), mask.load()
    # Only faint partially transparent fringe inside the gap by the guard's
    # face/sword. No opaque drawing or equipment geometry is synthesized.
    box = (455, 190, 515, 290)
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            red, green, blue, alpha = pixels[x, y]
            if 0 < alpha <= 24:
                pixels[x, y] = red, green, blue, 0
                marked[x, y] = 255
    after = image.tobytes()
    marks = mask.tobytes()
    changed = sum(before[i:i+4] != after[i:i+4] for i in range(0, len(before), 4))
    outside = sum(before[i:i+4] != after[i:i+4] and not marks[i//4]
                  for i in range(0, len(before), 4))
    if not changed or outside:
        raise ValueError("empty mask or changes outside mask")
    image.save(out)
    mask.save(mask_path)
    receipt.write_text(json.dumps({
        "status": "diagnostic_candidate_art_review_pending",
        "source_sha256": digest(source), "output_sha256": digest(out),
        "mask_sha256": digest(mask_path), "bbox_exclusive": box,
        "rule": "alpha 1..24 to zero only within rectangle; RGB preserved",
        "changed_pixels": changed, "changed_outside_mask": outside,
        "limits": "Does not fix opaque contamination or establish scale, pivots, animation, SMS palette or provenance approval."
    }, indent=2) + "\n")
    print(receipt.read_text())


if __name__ == "__main__":
    sys.exit(main())
