#!/usr/bin/env python3
"""Annotate approximate sword endpoints on the exploratory sequence."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "data/source_art/sprite_studies/alis/strong_thrust_round1/sequence_01.png"
OUT = PROJECT / "out/diagnostics/alis_strong_thrust_round1/weapon_landmarks_01"
POSES = {
    "guard": {"hand": [185, 355], "base": [205, 342], "tip": [291, 210], "crop": [0, 150, 367, 460]},
    "prepare": {"hand": [481, 378], "base": [469, 399], "tip": [405, 490], "crop": [360, 180, 755, 525]},
    "thrust": {"hand": [1178, 300], "base": [1203, 300], "tip": [1332, 300], "crop": [930, 180, 1360, 440]},
    "recover": {"hand": [1570, 325], "base": [1595, 305], "tip": [1705, 245], "crop": [1360, 160, 1760, 420]},
}


def main():
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != "afddbb42ac9358606d46780032a997e15e392182aa71e675fe6967029e782eb2":
        raise ValueError("sequence source changed")
    if OUT.exists():
        raise FileExistsError("preserve prior study")
    image = Image.open(SOURCE).convert("RGBA")
    OUT.mkdir()
    values = {}
    for pose, points in POSES.items():
        canvas = Image.new("RGBA", image.size, (245, 245, 245, 255))
        canvas.alpha_composite(image)
        draw = ImageDraw.Draw(canvas)
        draw.line((*points["base"], *points["tip"]), fill=(0, 200, 190, 255), width=3)
        for name in ("hand", "base", "tip"):
            x, y = points[name]
            draw.ellipse((x-5, y-5, x+5, y+5), fill=(255, 35, 90, 255))
            draw.text((x+7, y+4), name, fill=(0, 0, 0, 255), stroke_width=1, stroke_fill=(255, 255, 255, 255))
        canvas.crop(points["crop"]).convert("RGB").save(OUT / (pose + "_annotated.png"))
        values[pose] = {"hand_raw": points["hand"], "base_raw": points["base"],
                        "tip_raw": points["tip"],
                        "blade_length_approx_screen_px": math.dist(points["base"], points["tip"]) * 4 / 35}
    report = {"status": "estimated_not_art_or_scale_approval", "source_sha256": digest,
              "nominal_source_to_screen": "4/35; horizontal precompensated, before pixel rounding",
              "poses": values, "neutral_profile_reference_blade_px": math.dist((1074, 533), (1312, 818)) * 68 / 924,
              "limits": "Manual marks, same drawing plane assumed; neutral and animated source perspectives differ. No same-angle katana comparison, calibrated reach, or ROM evidence."}
    (OUT / "measurements.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
