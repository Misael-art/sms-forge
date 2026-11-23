#!/usr/bin/env python3
"""Composite an authored correction only inside the declared guard-face region."""
import hashlib
import json
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
ART = PROJECT / "data/source_art/sprite_studies/alis/strong_thrust_round1"
BASE = ART / "keyposes_01.png"
DRAFT = ART / "keyposes_gray_fringe_generated_01.png"
RESULT = ART / "keyposes_gray_fringe_masked_01.png"
MASK = ART / "keyposes_gray_fringe_mask_01.png"
RECEIPT = ART / "keyposes_gray_fringe_mask_01.json"
BOX = (460, 195, 505, 260)  # exclusive, face-to-sword gap, including edge


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if sha(BASE) != "fb1ddcaf94154bcd9a01a1807d6b07c21ae989187ab37e3ad6979162277cf28b":
        raise ValueError("original hash changed")
    if sha(DRAFT) != "05590f7bfdb8b53671ae18c0509f314a5a5947826f2f9b72822dd9648ecd927d":
        raise ValueError("draft hash changed")
    if any(path.exists() for path in (RESULT, MASK, RECEIPT)):
        raise FileExistsError("preserve previous result")
    original = Image.open(BASE).convert("RGBA")
    draft = Image.open(DRAFT).convert("RGBA")
    if original.size != (1774, 887) or draft.size != original.size:
        raise ValueError("canvas mismatch")
    corrected = original.copy()
    corrected.paste(draft.crop(BOX), BOX[:2])
    mask = Image.new("L", original.size, 0)
    mask.paste(255, BOX)
    before, after, selection = original.tobytes(), corrected.tobytes(), mask.tobytes()
    changed = sum(before[i:i+4] != after[i:i+4] for i in range(0, len(before), 4))
    outside = sum(before[i:i+4] != after[i:i+4] and not selection[i//4]
                  for i in range(0, len(before), 4))
    if changed == 0 or outside:
        raise ValueError("empty change or outside-mask change")
    corrected.save(RESULT)
    mask.save(MASK)
    report = {"status": "unapproved_art_study", "rectangle_exclusive": BOX,
              "source_sha256": sha(BASE), "draft_sha256": sha(DRAFT),
              "result_sha256": sha(RESULT), "mask_sha256": sha(MASK),
              "changed_pixels": changed, "outside_mask_changed": outside,
              "limits": "Converted impact, face/blade continuity and visual quality need separate review; not a runtime asset."}
    RECEIPT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
