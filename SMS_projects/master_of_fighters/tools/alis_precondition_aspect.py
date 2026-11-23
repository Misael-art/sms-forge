#!/usr/bin/env python3
"""Diagnostic registration for the adapter's unequal framebuffer ratios.

Only resamples indexed source pixels with nearest-neighbor; no drawing. The
result is a candidate transform, not proof of body-scale or artistic approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "out/diagnostics/alis_strong_thrust_round1"
SOURCES = {
    "idle": "f92c95069824f6b120774e35ef0cee06e792fcce337ae6f533052c06bc4ab8c0",
    "thrust": "facd42909ba775a48040c5d9211de403d9ef0249663d192592058cfc95dbe8a8",
}
LOWER_SOURCES = {
    "idle": "f92c95069824f6b120774e35ef0cee06e792fcce337ae6f533052c06bc4ab8c0",
    "thrust": "7c0c369af7f89988dc0c4bb21e46bc31d06508dcdd57da647d7834c5b2190e5e",
}
SEQUENCE_SOURCES = {
    "idle": "7365fc83e842c1b0fd8a442f096adb827ac61ea574e6dc9a371555f69d4e9afa",
    "prepare": "df26f666ece688a74b8fa6f0e1d06a277eef6e406ab7ff51a54897587903e418",
    "thrust": "8706d3ed928246d9a99ce30bc9d458028cff7c837dea75b476e324690cd28dc7",
    "recover": "1a5a4e965e2ee8d38c417effcec1c886dc1a0a0dd15d405d599e2fe7d492b5fb",
}
REDRAW_SOURCES = {
    "idle": "1b7dbaa3bd10e4c5e763e884ef27b91b49718a2a92d88b9bfe7c65ab5a73db27",
    "thrust": "f7c1027c58af4a4458ae1ecd490b4ca7c2dbce550f1e8c97651f2081fb8fc588",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--lower", action="store_true", help="register the lower-thrust study")
    group.add_argument("--sequence", action="store_true", help="register the full sequence study")
    group.add_argument("--redraw", action="store_true", help="register the two-pose redraw study")
    args = parser.parse_args()
    sources = SEQUENCE_SOURCES if args.sequence else REDRAW_SOURCES if args.redraw else LOWER_SOURCES if args.lower else SOURCES
    source_dir = BASE / ("sequence_material/native" if args.sequence else "keypose_redraw_01/native" if args.redraw else "keypose_lower/native" if args.lower else "keypose_material/native")
    out = BASE / ("sequence_aspect/native" if args.sequence else "keypose_redraw_01_aspect/native" if args.redraw else "keypose_lower_aspect/native" if args.lower else "keypose_aspect/native")
    height = 160 if args.sequence else 128 if args.redraw else 144
    source_pivot = [70, 130] if args.sequence else [70, 96] if args.redraw else [65, 115]
    result_pivot = [90, 130] if args.sequence else [90, 96] if args.redraw else [84, 115]
    if out.exists():
        raise FileExistsError("preserve existing registered output")
    for name, expected in sources.items():
        if sha(source_dir / (name + ".png")) != expected:
            raise ValueError("native source SHA mismatch: " + name)
    out.mkdir(parents=True)
    records = []
    for name in sources:
        image = Image.open(source_dir / (name + ".png"))
        if image.mode != "P" or image.info.get("transparency") != 0 or image.size != (200, height):
            raise ValueError("unexpected native image contract")
        # Adapter x=2/3, y=6/7: multiplying source x by (6/7)/(2/3)=9/7
        # restores the same geometric factor in each axis, before rounding.
        registered = image.resize((257, height), Image.Resampling.NEAREST)
        path = out / (name + ".png")
        registered.save(path, transparency=0, bits=8)
        records.append({"id": name, "sha256": sha(path)})
    report = {"status": "diagnostic_unapproved", "source_sha256": sources,
              "input_size": [200, height], "output_size": [257, height],
              "requested_x_ratio": [9, 7], "actual_canvas_x_ratio": [257, 200],
              "method": "nearest-neighbor indexed; original palette and transparent index 0",
              "source_pivot": source_pivot, "registered_pivot": result_pivot,
              "limits": "Rounding and two sampling stages remain; no standing-body calibration or runtime proof.",
              "frames": records}
    (out.parent / "aspect_receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
