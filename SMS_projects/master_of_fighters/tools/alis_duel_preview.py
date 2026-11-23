#!/usr/bin/env python3
"""Make a provisional registered comparison, without modifying source pixels."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/source_art/sprite_studies/alis/strong_thrust_round1/keyposes_guard_masked_01.png"
HAYATO = ROOT / "out/diagnostics/hayato_short_cut_v2/timing_only_v7/converted_left/idle.png"
OUT = ROOT / "out/diagnostics/alis_strong_thrust_round1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if sha(SRC) != "2d358b12a0956f5b4f7e05ede25c9babe1a1a6116ccc1798b2f915d1404d0ef4":
        raise ValueError("Alis source SHA mismatch")
    source = Image.open(SRC).convert("RGBA")
    rival = Image.open(HAYATO).convert("RGBA").transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    if rival.size != (88, 88):
        raise ValueError("unexpected Hayato canvas")
    # Draft only: the original high-resolution drawing lacks a standing neutral
    # calibration. 1/10 is an explicit visual trial, not established body scale.
    panels = []
    for crop_box, rear_x, front_x in [((0, 0, 750, 887), 225, 525),
                                     ((750, 0, 1774, 887), 865, 1280)]:
        crop = source.crop(crop_box)
        crop = crop.resize((round(crop.width / 10), round(crop.height / 10)), Image.Resampling.NEAREST)
        panel = Image.new("RGBA", (256, 192), (28, 41, 39, 255))
        x = 70 - round((rear_x - crop_box[0]) / 10)
        y = 144 - round(766 / 10)
        panel.alpha_composite(crop, (x, y))
        # The original pivot is x=40; mirroring an 88px canvas gives x=47.
        panel.alpha_composite(rival, (175 - 47, 144 - 80))
        draw = ImageDraw.Draw(panel)
        draw.line((0, 144, 255, 144), fill=(160, 210, 190, 255))
        draw.point((70, 144), fill=(255, 102, 170, 255))
        draw.point((x + round((front_x - crop_box[0]) / 10), 144), fill=(255, 220, 90, 255))
        draw.point((175, 144), fill=(110, 255, 210, 255))
        panels.append(panel.convert("RGB"))
    sheet = Image.new("RGB", (256, 384))
    for n, panel in enumerate(panels):
        sheet.paste(panel, (0, n * 192))
    OUT.mkdir(parents=True, exist_ok=True)
    one = OUT / "duel_keyposes_provisional_1x.png"
    four = OUT / "duel_keyposes_provisional_4x.png"
    if one.exists() or four.exists():
        raise FileExistsError("preserve existing output")
    sheet.save(one)
    sheet.resize((1024, 1536), Image.Resampling.NEAREST).save(four)
    print(json.dumps({"alis_source_sha256": sha(SRC), "hayato_sha256": sha(HAYATO),
                      "scale_alis": "1/10 trial; standing calibration not demonstrated",
                      "hayato_canvas": [88, 88], "ground_y": 144,
                      "alis_rear_anchor_x_source": [225, 865],
                      "alis_front_support_x_source": [525, 1280],
                      "support_status": "visual estimates, not verified landmarks",
                      "sha256_1x": sha(one), "sha256_4x": sha(four)}, indent=2))


if __name__ == "__main__":
    main()
