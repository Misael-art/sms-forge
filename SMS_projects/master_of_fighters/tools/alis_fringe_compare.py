#!/usr/bin/env python3
"""Compare the baseline and one masked edit after the SMS color conversion."""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "out/diagnostics/alis_strong_thrust_round1"
OLD = BASE / "keypose_pair_hayato_exact_probe"
NEW = BASE / "keypose_pair_fringe_material_01"
OUT = BASE / "fringe_converted_comparison_01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def footprints(image):
    groups = []
    for x in range(128):
        if not any(image.getpixel((x, y))[3] >= 128 for y in (77, 78, 79)):
            continue
        if not groups or x - groups[-1][-1] > 3:
            groups.append([x])
        else:
            groups[-1].append(x)
    if len(groups) != 2:
        raise ValueError("unexpected support groups")
    return [[group[0], group[-1]] for group in groups]


def load(folder, name):
    image = Image.open(folder / (name + ".png")).convert("RGBA")
    if image.size != (128, 88):
        raise ValueError("unexpected canvas")
    return image


def scene(actor, target, color):
    canvas = Image.new("RGBA", (256, 192), color + (255,))
    draw = ImageDraw.Draw(canvas)
    draw.line((0, 144, 255, 144), fill=(120, 145, 132, 255))
    canvas.alpha_composite(target, (136, 64))
    canvas.alpha_composite(actor, (24, 64))
    draw = ImageDraw.Draw(canvas)
    draw.point((64, 146), fill=(255, 100, 170, 255))
    draw.point((176, 146), fill=(100, 255, 210, 255))
    for image, origin, y, ink in ((actor, 24, 150, (255, 224, 80, 255)),
                                  (target, 136, 153, (100, 255, 210, 255))):
        for lo, hi in footprints(image):
            draw.line((origin + lo, y, origin + hi, y), fill=ink)
    return canvas.convert("RGB")


def main():
    if OUT.exists():
        raise FileExistsError("preserve comparison")
    images = {f"{label}_{pose}": load(folder, pose)
              for label, folder in (("before", OLD), ("after", NEW))
              for pose in ("idle", "thrust", "reference")}
    changes = {}
    for pose in ("idle", "thrust", "reference"):
        before, after = images["before_" + pose], images["after_" + pose]
        changes[pose] = [{"x": i % 128, "y": i // 128, "before": a, "after": b}
                         for i, (a, b) in enumerate(zip(before.getdata(), after.getdata()))
                         if a != b and (a[3] or b[3])]
    if len(changes["idle"]) != 1 or changes["thrust"] or changes["reference"]:
        raise ValueError("unexpected converted differences")
    OUT.mkdir()
    results = {}
    for name, color in (("dark", (30, 30, 30)), ("light", (245, 245, 245))):
        sheet = Image.new("RGB", (512, 384))
        for row, pose in enumerate(("idle", "thrust")):
            for col, label in enumerate(("before", "after")):
                sheet.paste(scene(images[label + "_" + pose], images[label + "_reference"], color),
                            (col * 256, row * 192))
        one, four = OUT / (name + "_1x.png"), OUT / (name + "_4x.png")
        sheet.save(one)
        sheet.resize((2048, 1536), Image.Resampling.NEAREST).save(four)
        results[name] = {"1x_sha256": sha(one), "4x_sha256": sha(four)}
    report = {"status": "diagnostic_not_runtime_or_art_approval", "changes": changes,
              "sheets": results, "layout": "columns before/after; rows guard/thrust; same ground and Hayato",
              "marks": "pink/cyan dots are declared pivots; yellow/cyan bars are opaque footprint intervals",
              "limits": "Keyposes use exploratory scale, not the sequence_01 currently bound to runtime; target layering, motion and 68px body remain unverified."}
    (OUT / "comparison.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
