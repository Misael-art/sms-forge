#!/usr/bin/env python3
"""Offline view of the rejected resource-budget study; never emulator proof."""
import hashlib
import json
from pathlib import Path
from PIL import Image
from alis_fringe_compare import load, scene

PROJECT = Path(__file__).resolve().parents[1]
BASE = PROJECT / "out/diagnostics/alis_strong_thrust_round1"
INPUT = BASE / "keypose_pair_redraw_ground_probe_01"
OUT = BASE / "redraw_comparison_01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError("preserve prior output")
    conversion = json.loads((INPUT / "conversion.json").read_text())
    if [(x["id"], x["peak"], x["legal"]) for x in conversion["compositions"]] != [("idle", 8, True), ("thrust", 9, False)]:
        raise ValueError("unexpected resource result")
    images = {name: load(INPUT, name) for name in ("idle", "thrust", "reference")}
    if any(im.getchannel("A").getbbox()[3] != 80 for im in images.values()):
        raise ValueError("ground alignment changed")
    OUT.mkdir()
    files = {}
    for shade, color in (("dark", (30, 30, 30)), ("light", (245, 245, 245))):
        sheet = Image.new("RGB", (512, 192))
        for i, pose in enumerate(("idle", "thrust")):
            sheet.paste(scene(images[pose], images["reference"], color), (256 * i, 0))
        one, four = OUT / (shade + "_1x.png"), OUT / (shade + "_4x.png")
        sheet.save(one)
        sheet.resize((2048, 768), Image.Resampling.NEAREST).save(four)
        files[shade] = {"1x_sha256": sha(one), "4x_sha256": sha(four)}
    report = {"status": "resource_gate_failed_do_not_build", "source_conversion_sha256": sha(INPUT / "conversion.json"),
              "peak_objects_per_scanline": {"idle": 8, "thrust": 9}, "files": files,
              "layout": "guard left, thrust right; both with Hayato and identical ground",
              "marks": "pink/cyan dots are declared pivots; yellow/cyan bars mark opaque foot intervals",
              "limits": "Offline draft; provisional scale and anatomy, no animated poses, no live emulator or VBlank evidence. Conversion rejected thrust's nine sprites per line."}
    (OUT / "preview.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
