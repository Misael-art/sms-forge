#!/usr/bin/env python3
"""Static previews of the declared sprite/BG split, not emulator evidence."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
BASE = PROJECT / "out/diagnostics/alis_strong_thrust_round1"
ASSETS = BASE / "both_faces_assets_probe"
OUT = BASE / "converted_preview"
SOURCE_PREFIX = "sequence_"
TARGETS = {"right": [52, 60, 68], "left": [60, 52, 44]}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(face, pose, distance, color):
    source = BASE / (SOURCE_PREFIX + face + "_probe")
    actor_x = 0 if face == "right" else 112
    target_x = TARGETS[face][distance]
    scene = Image.new("RGBA", (256, 192), color + (255,))
    ImageDraw.Draw(scene).line((0, 144, 255, 144), fill=(120, 145, 132, 255))
    if pose in ("prepare", "thrust"):
        bg = Image.open(ASSETS / (face + "_" + pose + "_bg.png")).convert("RGBA")
        scene.alpha_composite(bg, (actor_x, 64))
    target = Image.open(source / "reference.png").convert("RGBA")
    scene.alpha_composite(target, (target_x, 64))
    actor_path = (ASSETS / (face + "_" + pose + "_sat.png") if pose in ("prepare", "thrust")
                  else source / (pose + ".png"))
    actor = Image.open(actor_path).convert("RGBA")
    scene.alpha_composite(actor, (actor_x, 64))
    # Indicators sit below the ground and are not part of the authored sprites.
    draw = ImageDraw.Draw(scene)
    draw.point((actor_x + 64, 146), fill=(255, 100, 170, 255))
    draw.point((target_x + 64, 146), fill=(100, 255, 210, 255))
    return scene.convert("RGB")


def main():
    global ASSETS, OUT, SOURCE_PREFIX
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grounded", action="store_true", help="use ground-registered assets")
    args = parser.parse_args()
    if args.grounded:
        ASSETS = BASE / "grounded_faces_assets_probe"
        OUT = BASE / "converted_grounded_preview"
        SOURCE_PREFIX = "sequence_grounded96_"
    if OUT.exists():
        raise FileExistsError("preserve existing preview")
    receipt = json.loads((ASSETS / "split_probe.json").read_text())
    for face, entries in receipt["source_png_sha256"].items():
        for name, expected in entries.items():
            if sha(BASE / (SOURCE_PREFIX + face + "_probe") / (name + ".png")) != expected:
                raise ValueError("source hash mismatch: " + face + "/" + name)
    OUT.mkdir()
    frames = []
    for face in ("right", "left"):
        for pose in ("idle", "prepare", "thrust", "recover"):
            path = OUT / (face + "_" + pose + "_limit.png")
            render(face, pose, 1, (30, 30, 30)).save(path)
            frames.append({"face": face, "pose": pose, "sha256": sha(path)})
    key_sheet = Image.new("RGB", (512, 384))
    for y, face in enumerate(("right", "left")):
        for x, pose in enumerate(("idle", "thrust")):
            key_sheet.paste(render(face, pose, 1, (30, 30, 30)), (x * 256, y * 192))
    key_sheet.save(OUT / "keyposes_1x.png")
    key_sheet.resize((2048, 1536), Image.Resampling.NEAREST).save(OUT / "keyposes_4x.png")
    distances = Image.new("RGB", (768, 384))
    for y, face in enumerate(("right", "left")):
        for x in range(3):
            distances.paste(render(face, "thrust", x, (30, 30, 30)), (x * 256, y * 192))
    distances.save(OUT / "distances_1x.png")
    # White background inspection reveals edge and P0 transparency problems.
    white = Image.new("RGB", (512, 192))
    for x, pose in enumerate(("idle", "thrust")):
        white.paste(render("right", pose, 1, (245, 245, 245)), (x * 256, 0))
    white.save(OUT / "keyposes_light_1x.png")
    report = {"status": "static_composite_not_emulator",
              "header_sha256": receipt["header_sha256"], "frames": frames,
              "keyposes_1x_sha256": sha(OUT / "keyposes_1x.png"),
              "keyposes_4x_sha256": sha(OUT / "keyposes_4x.png"),
              "distances_1x_sha256": sha(OUT / "distances_1x.png"),
              "limitations": "P0 assumed equal P1; BG under sprites; floor/markers are preview overlays; scale and artistic approval pending; not framebuffer."}
    (OUT / "preview_receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
