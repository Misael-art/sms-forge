#!/usr/bin/env python3
"""Annotate a provisional, manually estimated anatomical comparison."""
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
REFERENCE = PROJECT / "data/source_art/roster_harmony_review/turnarounds/alis_turnaround.png"
SEQUENCE = PROJECT / "data/source_art/sprite_studies/alis/strong_thrust_round1/sequence_01.png"
OUT = PROJECT / "out/diagnostics/alis_strong_thrust_round1/scale_landmarks_01"

# Hand-estimated locations on the original rasters. The hip is obscured by
# clothing and joints are approximate; these are not approved rigging points.
POINTS = {
    "neutral_profile": {"shoulder": [1055, 220], "hip": [1105, 470],
                        "knee": [1072, 650], "ankle": [1027, 855]},
    "sequence_guard": {"shoulder": [168, 280], "hip": [225, 430],
                       "knee": [285, 477], "ankle": [270, 570]},
    "sequence_thrust": {"shoulder": [1040, 285], "hip": [1060, 430],
                        "knee": [1115, 471], "ankle": [1095, 570]},
}
SEGMENTS = (("torso", "shoulder", "hip"), ("upper_leg", "hip", "knee"),
            ("lower_leg", "knee", "ankle"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lengths(points, scale):
    return {name: math.dist(points[a], points[b]) * scale for name, a, b in SEGMENTS}


def annotated(image, points, crop, path):
    base = Image.new("RGBA", image.size, (245, 245, 245, 255))
    base.alpha_composite(image.convert("RGBA"))
    draw = ImageDraw.Draw(base)
    for _, a, b in SEGMENTS:
        draw.line((*points[a], *points[b]), fill=(0, 220, 220, 255), width=3)
    for name, (x, y) in points.items():
        draw.ellipse((x-5, y-5, x+5, y+5), fill=(255, 35, 90, 255))
        draw.text((x+8, y+4), name, fill=(0, 0, 0, 255), stroke_width=1, stroke_fill=(255, 255, 255, 255))
    base.crop(crop).convert("RGB").save(path)


def main():
    if sha(REFERENCE) != "c5e9f1c1d91fb13c2d75239523efce636ccdb02ba4b2b44c0720e9de8e579d35":
        raise ValueError("reference changed")
    if sha(SEQUENCE) != "afddbb42ac9358606d46780032a997e15e392182aa71e675fe6967029e782eb2":
        raise ValueError("sequence changed")
    if OUT.exists():
        raise FileExistsError("preserve prior study")
    OUT.mkdir()
    ref = Image.open(REFERENCE)
    seq = Image.open(SEQUENCE)
    annotated(ref, POINTS["neutral_profile"], (930, 0, 1230, 960), OUT / "neutral_profile_annotated.png")
    annotated(seq, POINTS["sequence_guard"], (0, 130, 367, 630), OUT / "guard_annotated.png")
    annotated(seq, POINTS["sequence_thrust"], (758, 130, 1360, 630), OUT / "thrust_annotated.png")
    scales = {"neutral_profile": 68 / 924, "sequence_guard": 4 / 35, "sequence_thrust": 4 / 35}
    measurements = {name: lengths(points, scales[name]) for name, points in POINTS.items()}
    ratios = {pose: {segment: measurements["neutral_profile"][segment] / measurements[pose][segment]
                     for segment, _, _ in SEGMENTS} for pose in ("sequence_guard", "sequence_thrust")}
    report = {"status": "manual_estimates_not_scale_approval", "source_sha256": sha(SEQUENCE),
              "reference_sha256": sha(REFERENCE), "points_raw_px": POINTS,
              "reference_scale": "68/924 (approved lineup height projected using turnaround)",
              "sequence_scale": "4/35 (1/5 extraction × 6/7 registration × 2/3 conversion; horizontal precompensated)",
              "segment_lengths_screen_px": measurements, "reference_over_sequence": ratios,
              "limits": "Landmarks are visual approximations; hip and shoulder joints are occluded, armor may not mark joints. Reference is concept neutral and poses are drawn independently. Ratios diagnose possible proportion or scale mismatch, not a calibrated model or verdict."}
    (OUT / "measurements.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
