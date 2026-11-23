#!/usr/bin/env python3
"""Register a generated arm study inside a declared source-art rectangle.

No artwork is invented by this operation. The new arm pixels come from the
hash-bound generated reference; everything outside the rectangle is copied
unchanged from the original. The seam and anatomy need artistic review.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "data/source_art/sprite_studies/alis/strong_thrust_round1"
SOURCE = DIR / "keyposes_01.png"
DRAFT = DIR / "keyposes_lower_thrust_generated.png"
RESULT = DIR / "keyposes_lower_thrust_masked.png"
MASK = DIR / "keyposes_lower_thrust_mask.png"
RECEIPT = DIR / "keyposes_lower_thrust_mask.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if digest(SOURCE) != "fb1ddcaf94154bcd9a01a1807d6b07c21ae989187ab37e3ad6979162277cf28b":
        raise ValueError("original changed")
    if digest(DRAFT) != "332044291cdb4539d325fb84470b2f46b5bec2b38b7caa58ff0af153d9f39e27":
        raise ValueError("generated draft changed")
    if any(p.exists() for p in (RESULT, MASK, RECEIPT)):
        raise FileExistsError("preserve previous output")
    source = Image.open(SOURCE).convert("RGBA")
    draft = Image.open(DRAFT).convert("RGBA")
    if source.size != (1774, 887) or draft.size != source.size:
        raise ValueError("canvas mismatch")
    box = (1090, 270, 1650, 490)
    before = source.tobytes()
    source.paste(draft.crop(box), box[:2])
    mask = Image.new("L", source.size, 0)
    mask.paste(255, box)
    after, marks = source.tobytes(), mask.tobytes()
    changed = sum(before[i:i + 4] != after[i:i + 4] for i in range(0, len(before), 4))
    outside = sum(before[i:i + 4] != after[i:i + 4] and not marks[i // 4]
                  for i in range(0, len(before), 4))
    if not changed or outside:
        raise ValueError("empty edit or pixels changed outside region")
    source.save(RESULT)
    mask.save(MASK)
    record = {"status": "unapproved_art_study", "source_sha256": digest(SOURCE),
              "draft_sha256": digest(DRAFT), "output_sha256": digest(RESULT),
              "mask_sha256": digest(MASK), "rect_exclusive": box,
              "changed_rgba_pixels": changed, "outside_mask_changed": outside,
              "limits": "Arm, shield, seams, pose, palette, scale and hardware require review."}
    RECEIPT.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
