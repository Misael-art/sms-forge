#!/usr/bin/env python3
"""Provisional static reach/layering preview for the two-pose redraw."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
BASE = PROJECT / "out/diagnostics/alis_strong_thrust_round1"
PAIR = BASE / "keypose_pair_redraw_ground_probe_01"
SPLIT = BASE / "redraw_blade_bg_probe_01"
OUT = BASE / "redraw_reach_preview_01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError("preserve prior evidence")
    original = Image.open(PAIR / "thrust.png")
    actor = Image.open(SPLIT / "thrust_sat.png")
    blade = Image.open(SPLIT / "thrust_bg.png")
    target = Image.open(PAIR / "reference.png")
    if any(im.mode != "P" or im.size != (128, 88) or im.info.get("transparency") != 0
           for im in (original, actor, blade, target)):
        raise ValueError("indexed input contract changed")
    if any((a or b) != o or (a and b) for o, a, b in zip(original.tobytes(), actor.tobytes(), blade.tobytes())):
        raise ValueError("split reconstruction mismatch")
    row, actor_x = 45, 24
    tip = actor_x + max(x for x in range(128) if original.getpixel((x, row)))
    edge = min(x for x in range(128) if target.getpixel((x, row)))
    limit = tip - edge
    targets = [limit - 8, limit, limit + 8]
    fragments = [(x, y) for y in range(88) for x in range(128) if blade.getpixel((x, y))]
    sheet = Image.new("RGB", (768, 384))
    measurements = []
    for col, target_x in enumerate(targets):
        overlap = sum(0 <= actor_x + x - target_x < 128 and
                      target.getpixel((actor_x + x - target_x, y)) != 0 for x, y in fragments)
        scene = Image.new("RGBA", (256, 192), (30, 30, 30, 255))
        ImageDraw.Draw(scene).line((0, 144, 255, 144), fill=(120, 145, 132, 255))
        scene.alpha_composite(blade.convert("RGBA"), (actor_x, 64))
        scene.alpha_composite(target.convert("RGBA"), (target_x, 64))
        scene.alpha_composite(actor.convert("RGBA"), (actor_x, 64))
        draw = ImageDraw.Draw(scene)
        draw.point((actor_x + 40, 146), fill=(255, 100, 170, 255))
        draw.point((target_x + 40, 146), fill=(100, 255, 210, 255))
        right = scene.convert("RGB")
        sheet.paste(right, (col * 256, 0))
        sheet.paste(right.transpose(Image.Transpose.FLIP_LEFT_RIGHT), (col * 256, 192))
        measurements.append({"distance": ("near", "limit", "outside")[col],
                             "right_actor_origin": actor_x, "right_target_origin": target_x,
                             "edge_delta_px": tip - (target_x + edge),
                             "bg_blade_pixels_overlapping_target": overlap,
                             "left_actor_origin": 256 - actor_x - 128,
                             "left_target_origin": 256 - target_x - 128})
    if [m["edge_delta_px"] for m in measurements] != [8, 0, -8]:
        raise ValueError("unexpected geometric measurements")
    OUT.mkdir()
    one, four = OUT / "distances_1x.png", OUT / "distances_4x.png"
    sheet.save(one)
    sheet.resize((3072, 1536), Image.Resampling.NEAREST).save(four)
    report = {"status": "offline_projection_not_runtime_or_collision", "source_sha256": {
        "thrust": sha(PAIR / "thrust.png"), "target": sha(PAIR / "reference.png"),
        "sat": sha(SPLIT / "thrust_sat.png"), "bg": sha(SPLIT / "thrust_bg.png")},
        "canvas_row": row, "screen_y": row + 64, "tip_screen_x": tip,
        "target_edge_canvas_x": edge, "positions": measurements,
        "sheet_1x_sha256": sha(one), "sheet_4x_sha256": sha(four),
        "limits": "Left row mirrors the offline composite, not converted hardware assets. BG is drawn behind target; overlapping pixels can hide the blade. Scale, hit/block, PNT, timing and ROM remain unverified."}
    (OUT / "reach.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
