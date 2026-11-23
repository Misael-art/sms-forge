#!/usr/bin/env python3
"""Mark pixel support intervals on an existing offline comparison, not on art."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "out/diagnostics/alis_strong_thrust_round1"
PREVIEW = BASE / "converted_grounded_preview"


def supports(path):
    image = Image.open(path).convert("RGBA")
    if image.size != (128, 96):
        raise ValueError("unexpected canvas")
    xs = [x for x in range(128)
          if any(image.getpixel((x, y))[3] >= 128 for y in (77, 78, 79))]
    groups = []
    for x in xs:
        if not groups or x - groups[-1][-1] > 3:
            groups.append([x])
        else:
            groups[-1].append(x)
    if len(groups) != 2:
        raise ValueError(f"expected two footprint groups in {path}, got {groups}")
    return [[group[0], group[-1]] for group in groups]


def main():
    source = PREVIEW / "keyposes_1x.png"
    sheet = Image.open(source).convert("RGB")
    if sheet.size != (512, 384):
        raise ValueError("unexpected sheet size")
    draw = ImageDraw.Draw(sheet)
    rows = {}
    for row, face in enumerate(("right", "left")):
        actor_x = 0 if face == "right" else 112
        target_x = 60 if face == "right" else 52
        inputs = BASE / ("sequence_grounded96_" + face + "_probe")
        target = supports(inputs / "reference.png")
        for col, pose in enumerate(("idle", "thrust")):
            actor = supports(inputs / (pose + ".png"))
            shift_x, shift_y = col * 256, row * 192
            for intervals, origin, color, y in ((actor, actor_x, (255, 224, 80), 150),
                                                  (target, target_x, (100, 255, 210), 153)):
                for lo, hi in intervals:
                    draw.line((shift_x + origin + lo, shift_y + y,
                               shift_x + origin + hi, shift_y + y), fill=color)
            rows[face + "_" + pose] = {"actor_origin": actor_x, "target_origin": target_x,
                                       "actor_foot_intervals": actor,
                                       "target_foot_intervals": target,
                                       "actor_canvas_pivot": [64, 80],
                                       "target_canvas_pivot": [64, 80],
                                       "additional_actor_advance": 0}
    one = PREVIEW / "keyposes_supports_1x.png"
    four = PREVIEW / "keyposes_supports_4x.png"
    receipt = PREVIEW / "keyposes_supports_receipt.json"
    if any(p.exists() for p in (one, four, receipt)):
        raise FileExistsError("preserve existing study")
    sheet.save(one)
    sheet.resize((2048, 1536), Image.Resampling.NEAREST).save(four)
    report = {"status": "offline_diagnostic_not_art_approval", "poses": rows,
              "method": "union of opaque x coordinates on canvas rows 77-79, grouped with max gap 3; intervals are pixel footprint, not anatomical or dynamic contact",
              "legend": "existing pink/cyan dots mark actor/target declared pivot; yellow/cyan bars mark their footprint intervals below floor",
              "one_sha256": hashlib.sha256(one.read_bytes()).hexdigest(),
              "four_sha256": hashlib.sha256(four.read_bytes()).hexdigest(),
              "limits": "sequence_01, neutral body scale not demonstrated, stationary advance is provisional, no emulator or motion validation"}
    receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
