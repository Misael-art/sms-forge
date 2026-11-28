#!/usr/bin/env python3
"""Probe a pixel-exact sprite/BG split; this does not generate a game ROM."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
sys.path.insert(0, str(REPO / "tools/sms_wrapper"))
from prepare_authored_sprite_sample import pack_registered_eight  # noqa: E402
from pack_sms_metasprite import safe_sprite_pattern_capacity, header_text, _c_array  # noqa: E402
from png_to_sms_tiles import tile_bytes  # noqa: E402
from mugen2sms.generators.runtime_format import decode_indices  # noqa: E402

BASE = PROJECT / "out/diagnostics/alis_strong_thrust_round1"
SOURCE = BASE / "keypose_pair_aspect_probe"
OUT = BASE / "keypose_blade_bg_probe"
EXPECTED = {
    "idle": "9ef02970766051868011770963eca6105b80c923ebea386e14b37d373fa0b329",
    "thrust": "bf42f9ad4acc567e3e0ce066530dbcb6def60a86e50a8e4528b36d65e48f9383",
    "reference": "1c8b4fd99189cc0e3bb596e2e3cd47bea1bb91808812824cf7f849ef36583b35",
}
SEQUENCE_EXPECTED = {
    "idle": "d9b0f8184707728f9b40f0202135a279674ff692a77a8d825e30eb830aadd13f",
    "prepare": "f3d87d62fe180b81f271245cc6fa43dc15f8e4000c66ca5b22fffe911b446193",
    "thrust": "9cee14e26faecc4cd7b5cdc84c822245bd69372338336f6067192c6469b8d9b5",
    "recover": "d6b59f2ceaac3c3fd28b211b3e470030f1004567f20cba2f433eb48460d07404",
    "reference": "1c8b4fd99189cc0e3bb596e2e3cd47bea1bb91808812824cf7f849ef36583b35",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sequence", action="store_true", help="measure all four source-study poses")
    group.add_argument("--both-faces", action="store_true", help="probe one shared pool for both orientations")
    group.add_argument("--redraw", action="store_true", help="probe the two-pose redraw study")
    parser.add_argument("--out", type=Path, help="new output below the round's diagnostic directory")
    parser.add_argument("--grounded", action="store_true", help="use 96px canvases with registered ground")
    args = parser.parse_args()
    if args.both_faces:
        out = args.out.resolve() if args.out else BASE / ("grounded_faces_assets_probe" if args.grounded else "both_faces_blade_bg_probe")
        if not out.is_relative_to(BASE.resolve()):
            raise ValueError("output must stay inside the diagnostic owner")
        return both_faces_probe(out, args.grounded)
    if args.redraw:
        if args.grounded:
            parser.error("--grounded is available only with --both-faces")
        out = args.out.resolve() if args.out else BASE / "redraw_blade_bg_probe_01"
        if not out.is_relative_to(BASE.resolve()):
            raise ValueError("output must stay inside the diagnostic owner")
        return redraw_probe(out)
    if args.out or args.grounded:
        parser.error("--out requires --both-faces or --redraw; --grounded requires --both-faces")
    if args.sequence:
        return sequence_probe()
    if OUT.exists():
        raise FileExistsError("preserve previous probe")
    for name, expected in EXPECTED.items():
        if sha(SOURCE / (name + ".png")) != expected:
            raise ValueError("source SHA changed: " + name)
    original = Image.open(SOURCE / "thrust.png")
    if original.mode != "P" or original.size != (128, 88) or original.info.get("transparency") != 0:
        raise ValueError("unexpected sprite format")
    raw = original.tobytes()
    sprite, blade = bytearray(raw), bytearray(len(raw))
    moved = []
    for y in range(40, 49):
        for x in range(87, 128):
            index = y * 128 + x
            if raw[index]:
                moved.append((x, y, raw[index]))
                blade[index], sprite[index] = raw[index], 0
    if not moved or any((sprite[i] or blade[i]) != raw[i] or (sprite[i] and blade[i])
                        for i in range(len(raw))):
        raise ValueError("split does not reconstruct source indices exactly")
    OUT.mkdir()
    for name, pixels in (("thrust_sat", sprite), ("thrust_bg", blade)):
        image = Image.frombytes("P", original.size, bytes(pixels))
        image.putpalette(original.getpalette())
        image.save(OUT / (name + ".png"), transparency=0, bits=8)
    paths = [("idle", SOURCE / "idle.png"), ("thrust", OUT / "thrust_sat.png"),
             ("reference", SOURCE / "reference.png")]
    phases = [[4, 7], [6, 0], [3, 5]]
    packed = pack_registered_eight(paths, phases, OUT,
                                   safe_sprite_pattern_capacity(0, 0x0000, 0x3800))
    reference = packed["poses"][-1]["objects"]
    scenes = []
    for pose in packed["poses"][:-1]:
        objects = ([{"x": 24 + o["x"], "y": 64 + o["y"], "tile": o["tile"]}
                    for o in pose["objects"]] +
                   [{"x": 136 + o["x"], "y": 64 + o["y"], "tile": o["tile"]}
                    for o in reference])
        manifest = {"schema": "sprite_scene_manifest_v1", "sprite_size": "8x8",
                    "zoomed": False, "screen_h": 192, "sprites": objects}
        path = OUT / ("scene_" + pose["name"] + ".json")
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        peak = max(sum(o["y"] <= y < o["y"] + 8 for o in objects) for y in range(192))
        scenes.append({"id": pose["name"], "sat": len(objects), "peak": peak,
                       "manifest": str(path.relative_to(PROJECT))})
    tiles = sorted({((24 + x) // 8, (64 + y) // 8) for x, y, _ in moved})
    report = {"status": "diagnostic_not_implemented_in_runtime",
              "source_png_sha256": EXPECTED, "split_box": [87, 40, 128, 49],
              "moved_pixels": len(moved), "reconstruction_index_mismatches": 0,
              "phases": phases, "sprite_patterns": packed["loaded_patterns"],
              "bg_cells_for_this_position": tiles, "bg_cells_count": len(tiles),
              "scenes": scenes,
              "limitations": "Requires runtime P0 palette, correct layer priority, both facings, three distances, asset binding and measured updates/worst frame; alpha/index equality is not framebuffer proof."}
    (OUT / "split_probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def redraw_probe(out):
    source = BASE / "keypose_pair_redraw_ground_probe_01"
    expected = {"idle": "9d2ebd6bd125ecfe818991ac1b37222fcdd5b5f590da8a2bb405c3d99936095e",
                "thrust": "b0626a7d4b252d78c37990b7239c73d9492e6ac6f33dd3ee095b9a230f30fcf4",
                "reference": "1c8b4fd99189cc0e3bb596e2e3cd47bea1bb91808812824cf7f849ef36583b35"}
    if out.exists():
        raise FileExistsError("preserve prior probe")
    for name, digest in expected.items():
        if sha(source / (name + ".png")) != digest:
            raise ValueError("converted source changed: " + name)
    image = Image.open(source / "thrust.png")
    if image.mode != "P" or image.size != (128, 88) or image.info.get("transparency") != 0:
        raise ValueError("unexpected indexed source")
    raw = image.tobytes()
    sprite, bg = bytearray(raw), bytearray(len(raw))
    box = (88, 44, 96, 48)
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            i = y * 128 + x
            bg[i], sprite[i] = raw[i], 0
    moved = sum(bool(x) for x in bg)
    if not moved or any((sprite[i] or bg[i]) != raw[i] or (sprite[i] and bg[i]) for i in range(len(raw))):
        raise ValueError("split does not reconstruct original pixels")
    out.mkdir()
    for name, data in (("thrust_sat", sprite), ("thrust_bg", bg)):
        result = Image.frombytes("P", image.size, bytes(data))
        result.putpalette(image.getpalette())
        result.save(out / (name + ".png"), transparency=0, bits=8)
    paths = [("idle", source / "idle.png"), ("thrust", out / "thrust_sat.png"),
             ("reference", source / "reference.png")]
    phases = [[0, 0], [0, 0], [3, 5]]
    packed = pack_registered_eight(paths, phases, out,
                                   safe_sprite_pattern_capacity(0, 0x0000, 0x3800))
    from audit_sprite_line_sim import simulate
    target = packed["poses"][-1]["objects"]
    cases = []
    for pose in packed["poses"][:-1]:
        objects = ([{"x": 24 + obj["x"], "y": 64 + obj["y"], "tile": obj["tile"]} for obj in pose["objects"]] +
                   [{"x": 136 + obj["x"], "y": 64 + obj["y"], "tile": obj["tile"]} for obj in target])
        scene = {"schema": "sprite_scene_manifest_v1", "sprite_size": "8x8", "zoomed": False,
                 "screen_h": 192, "sprites": objects}
        (out / ("scene_" + pose["name"] + ".json")).write_text(json.dumps(scene, indent=2) + "\n")
        result = simulate(scene)
        cases.append({"pose": pose["name"], "sat": result["sprites"],
                      "peak": result["peak_per_line"], "violations": result["violations"]})
    report = {"status": "diagnostic_only_not_runtime", "source_sha256": expected,
              "split_box": box, "moved_pixels": moved, "index_reconstruction_mismatches": 0,
              "phases": phases, "patterns": packed["loaded_patterns"], "scenes": cases,
              "limits": "Two still poses, one facing and position only; BG occlusion, tilemap updates, mirrored assets, animation, P1/P0, VBlank and emulator remain unverified."}
    (out / "split_probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def sequence_probe():
    source = BASE / "sequence_pair_aspect_probe"
    out = BASE / "sequence_blade_bg_probe"
    if out.exists():
        raise FileExistsError("preserve previous probe")
    for name, expected in SEQUENCE_EXPECTED.items():
        if sha(source / (name + ".png")) != expected:
            raise ValueError("source SHA changed: " + name)
    boxes = {"prepare": [0, 56, 43, 69], "thrust": [83, 40, 128, 50]}
    out.mkdir()
    split = {}
    for name, (x0, y0, x1, y1) in boxes.items():
        original = Image.open(source / (name + ".png"))
        if original.mode != "P" or original.size != (128, 88) or original.info.get("transparency") != 0:
            raise ValueError("unexpected sprite format")
        raw = original.tobytes()
        sprite, blade = bytearray(raw), bytearray(len(raw))
        moved = []
        for y in range(y0, y1):
            for x in range(x0, x1):
                index = y * 128 + x
                if raw[index]:
                    moved.append((x, y, raw[index]))
                    blade[index], sprite[index] = raw[index], 0
        if not moved or any((sprite[i] or blade[i]) != raw[i] or (sprite[i] and blade[i])
                            for i in range(len(raw))):
            raise ValueError("split does not reconstruct source indices exactly")
        for suffix, pixels in (("sat", sprite), ("bg", blade)):
            image = Image.frombytes("P", original.size, bytes(pixels))
            image.putpalette(original.getpalette())
            image.save(out / (name + "_" + suffix + ".png"), transparency=0, bits=8)
        cells = sorted({((24 + x) // 8, (64 + y) // 8) for x, y, _ in moved})
        split[name] = {"box": [x0, y0, x1, y1], "moved_pixels": len(moved),
                       "reconstruction_index_mismatches": 0, "bg_cells": cells,
                       "bg_cells_count": len(cells)}
    paths = [("idle", source / "idle.png"), ("prepare", out / "prepare_sat.png"),
             ("thrust", out / "thrust_sat.png"), ("recover", source / "recover.png"),
             ("reference", source / "reference.png")]
    phases = [[5, 4], [0, 7], [7, 7], [4, 0], [3, 5]]
    packed = pack_registered_eight(paths, phases, out,
                                   safe_sprite_pattern_capacity(0, 0x0000, 0x3800))
    reference = packed["poses"][-1]["objects"]
    scenes = []
    for pose in packed["poses"][:-1]:
        objects = ([{"x": 24 + o["x"], "y": 64 + o["y"], "tile": o["tile"]}
                    for o in pose["objects"]] +
                   [{"x": 136 + o["x"], "y": 64 + o["y"], "tile": o["tile"]}
                    for o in reference])
        manifest = {"schema": "sprite_scene_manifest_v1", "sprite_size": "8x8",
                    "zoomed": False, "screen_h": 192, "sprites": objects}
        path = out / ("scene_" + pose["name"] + ".json")
        path.write_text(json.dumps(manifest, indent=2) + "\n")
        peak = max(sum(o["y"] <= y < o["y"] + 8 for o in objects) for y in range(192))
        scenes.append({"id": pose["name"], "sat": len(objects), "peak": peak,
                       "manifest": str(path.relative_to(PROJECT))})
    report = {"status": "diagnostic_not_implemented_in_runtime",
              "source_png_sha256": SEQUENCE_EXPECTED, "split": split,
              "phases": phases, "sprite_patterns": packed["loaded_patterns"],
              "scenes": scenes,
              "limitations": "Bounding boxes need artistic review. Runtime P0 palette, layering, clearing, both facings, three distances, asset binding, PNT/VRAM and worst-frame remain unmeasured."}
    (out / "split_probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


def both_faces_probe(out, grounded=False):
    sources = {face: BASE / ("sequence_grounded96_" + face + "_probe" if grounded else "sequence_" + face + "_probe")
               for face in ("right", "left")}
    expected = {
        "right": {
            "idle": "22707fb3368b46db7e32d17890eb5d14068722e7f189e6751136312f9e127bd4",
            "prepare": "f74b910896d9bf419e8125797b238f160818dfee4dcf45ec6a610388ea6c6376",
            "thrust": "c2417fb5572e889588241701757c9d9681b87b1529d8ea2ba43d388e04d2bdc6",
            "recover": "d47c5fd97aac6822a60fe90fe06f17320e0bff58a4c308034c66a826fa80bbf4",
            "reference": "55333dc60215336a295cd95e23f5d64ae5574a01ee1925d9cab9762ffb16b04e"},
        "left": {
            "idle": "a4b7453f064beac2573708e54f9e181000d17f96a5ff73a2ddc363512de3d1f9",
            "prepare": "08a58469baf9d86dd10abd2ca178df5b67fe0ae1f34015d15ee2140a38742739",
            "thrust": "5d16f27c63dd9915b209ec1f642f2e1e50836b5c8f99d6216cb696292aa34ae0",
            "recover": "7471cbefa79ee0868cdf897378a4ece6db42d584defd8a2af659ffd18885919e",
            "reference": "0e204f7c16d67e62986ee66abab638f1ef9e20b360a92a70ac88acd74916d397"},
    }
    if grounded:
        expected = {
            "right": {
                "idle": "5848d1b310391f8c5a0dc55da5c70e279f8d45f8b56c7b3b12216ea468fa3442",
                "prepare": "f79442d12261badd8bb520aeac9d6d3a5198c999c27ccac6509c04792d69a4a5",
                "thrust": "7465c222e7df6eda573ebef32752f4814de02f0bdc9a0f8d100e43ecf8363c2e",
                "recover": "2cd8b533cbb5e3de66d4c2fd42e057cf29bffcd982d4dc0e87f3aa333e02a3a6",
                "reference": "7eb11f104f5ad2f95e699e7bcc475dafdaff8354d98848af1335d249db4e5824"},
            "left": {
                "idle": "3f5d2a6ede45cd73e13eaf5191b41a7ffcff288e9d4179ffdb786b88353ca498",
                "prepare": "ae71271c148f72a2c5ad2d56a180f3d4061565e920fd2f9d3b0f059b9eed2199",
                "thrust": "ea4a5517d0b2caab40423ac837d1c564b429042beda94613a476b1685f81b97a",
                "recover": "25c6d748cb1d90bd77c167026b69e0bd8aac570addbfc0c161d3e5d425089f6d",
                "reference": "719e63571aa4c0f030b38520f1f0cead349cd3205b6801cb2d771af13ec5895c"},
        }
    if out.exists():
        raise FileExistsError("preserve previous probe")
    for face, records in expected.items():
        for name, digest in records.items():
            if sha(sources[face] / (name + ".png")) != digest:
                raise ValueError("source SHA changed: " + face + "/" + name)
    out.mkdir()
    # Rectangles are mirrored about x=64, preserving every index. They are
    # provisional visual selections and do not prove foreground/BG layering.
    boxes = {"right": {"prepare": [24, 56, 67, 69], "thrust": [107, 40, 128, 50]},
             "left": {"prepare": [62, 56, 105, 69], "thrust": [0, 40, 22, 50]}}
    phases = {"right": [[5, 4], [0, 7], [7, 7], [4, 0], [3, 5]],
              "left": [[2, 4], [6, 7], [0, 7], [3, 0], [3, 4]]}
    if grounded:
        boxes = {"right": {"prepare": [24, 55, 67, 68], "thrust": [107, 39, 128, 49]},
                 "left": {"prepare": [62, 55, 105, 68], "thrust": [0, 39, 22, 49]}}
        phases = {"right": [[3, 0], [0, 0], [7, 0], [4, 0], [4, 0]],
                  "left": [[2, 6], [6, 0], [0, 0], [3, 0], [2, 0]]}
    paths, all_phases, split = [], [], {}
    names = ("idle", "prepare", "thrust", "recover", "reference")
    for face in ("right", "left"):
        for name, phase in zip(names, phases[face]):
            path = sources[face] / (name + ".png")
            if name in boxes[face]:
                image = Image.open(path)
                if image.mode != "P" or image.size != (128, 96 if grounded else 88) or image.info.get("transparency") != 0:
                    raise ValueError("unexpected indexed sprite")
                raw = image.tobytes()
                sat, bg = bytearray(raw), bytearray(len(raw))
                x0, y0, x1, y1 = boxes[face][name]
                for y in range(y0, y1):
                    for x in range(x0, x1):
                        i = y * 128 + x
                        if raw[i]:
                            sat[i], bg[i] = 0, raw[i]
                if not any(bg) or any((sat[i] or bg[i]) != raw[i] or (sat[i] and bg[i])
                                      for i in range(len(raw))):
                    raise ValueError("split does not exactly reconstruct source")
                for suffix, pixels in (("sat", sat), ("bg", bg)):
                    result = Image.frombytes("P", image.size, bytes(pixels))
                    result.putpalette(image.getpalette())
                    result.save(out / f"{face}_{name}_{suffix}.png", transparency=0, bits=8)
                path = out / f"{face}_{name}_sat.png"
                split[f"{face}_{name}"] = {"box": boxes[face][name],
                                             "moved_pixels": sum(bool(v) for v in bg),
                                             "reconstruction_index_mismatches": 0}
            paths.append((face + "_" + name, path))
            all_phases.append(phase)
    try:
        packed = pack_registered_eight(paths, all_phases, out,
                                       safe_sprite_pattern_capacity(0, 0x0000, 0x3800))
    except ValueError as error:
        (out / "split_probe.json").write_text(json.dumps({"status": "packing_failed", "error": str(error),
                                                          "source_png_sha256": expected, "split": split}, indent=2) + "\n")
        raise
    lookup = {p["name"]: p["objects"] for p in packed["poses"]}
    # Each BG fragment is encoded as actual SMS 4bpp tiles in the second VRAM
    # half. Source indices are checked by decoding each emitted tile.
    bg_tiles, bg_ids, bg_maps = [], {}, {}
    for face in ("right", "left"):
        actor_x = 0 if face == "right" else 112
        for pose in ("prepare", "thrust"):
            image = Image.open(out / f"{face}_{pose}_bg.png")
            raw = image.tobytes()
            rows = [[0] * 256 for _ in range(192)]
            cells = set()
            for i, value in enumerate(raw):
                if value:
                    x, y = actor_x + i % 128, 64 + i // 128
                    if not (0 <= x < 256 and 0 <= y < 192):
                        raise ValueError("BG fragment exceeds screen")
                    rows[y][x] = value
                    cells.add((x // 8, y // 8))
            mapping = []
            for x, y in sorted(cells, key=lambda cell: (cell[1], cell[0])):
                blob = bytes(tile_bytes(rows, x, y))
                expect = [rows[y * 8 + dy][x * 8 + dx] for dy in range(8) for dx in range(8)]
                if decode_indices(blob) != expect:
                    raise ValueError("BG tile encode/decode mismatch")
                if blob not in bg_ids:
                    bg_ids[blob] = len(bg_tiles)
                    bg_tiles.append(blob)
                mapping.extend([x, y, bg_ids[blob]])
            bg_maps[face + "_" + pose] = mapping + [255]
    if len(bg_tiles) + 1 > 192:
        raise ValueError("BG tiles exceed free second-half VRAM before PNT")
    # One extra solid index-15 tile is reserved for a prospective diagnostic HUD.
    bg_blob = b"".join(bg_tiles) + bytes([255] * 32)
    header = [header_text(packed, "alis_sample"),
              "#define ALIS_BG_TILE_BASE 256u",
              f"#define ALIS_BG_TILE_COUNT {len(bg_tiles)}u",
              f"#define ALIS_BG_TILE_BYTES {len(bg_blob)}u",
              "#define ALIS_HUD_TILE (ALIS_BG_TILE_BASE + ALIS_BG_TILE_COUNT)",
              _c_array("alis_bg_tiles", list(bg_blob))]
    for name, mapping in bg_maps.items():
        header.append(_c_array("alis_bg_" + name, mapping))
    for face in ("right", "left"):
        pose_names = ", ".join("alis_sample_" + face + "_" + name + "_meta" for name in names[:-1])
        header.append(f"const unsigned char * const alis_sample_{face}_poses[4] = {{{pose_names}}};")
    header_path = out / "both_faces_assets.h"
    header_path.write_text("\n".join(header) + "\n")
    scenes = []
    for face in ("right", "left"):
        actor_x = 0 if face == "right" else 112
        # Pivots 64 and 176; gap = 52, 60, 68. Geometric threshold is
        # provisional, derived from the current converted silhouette only.
        targets = [52, 60, 68] if face == "right" else [60, 52, 44]
        for label, target_x in zip(("near", "limit", "outside"), targets):
            for name in names[:-1]:
                objects = ([{"x": actor_x + o["x"], "y": 64 + o["y"], "tile": o["tile"]}
                            for o in lookup[face + "_" + name]] +
                           [{"x": target_x + o["x"], "y": 64 + o["y"], "tile": o["tile"]}
                            for o in lookup[face + "_reference"]])
                manifest = {"schema": "sprite_scene_manifest_v1", "sprite_size": "8x8",
                            "zoomed": False, "screen_h": 192, "sprites": objects}
                path = out / f"scene_{face}_{label}_{name}.json"
                path.write_text(json.dumps(manifest, indent=2) + "\n")
                peak = max(sum(o["y"] <= y < o["y"] + 8 for o in objects) for y in range(192))
                scenes.append({"face": face, "distance": label, "pose": name,
                               "sat": len(objects), "peak": peak,
                               "manifest": str(path.relative_to(PROJECT))})
    report = {"status": "diagnostic_not_implemented_in_runtime", "source_png_sha256": expected,
              "grounded": grounded,
              "split": split, "phases": phases, "sprite_patterns": packed["loaded_patterns"],
              "bg_patterns": len(bg_tiles), "bg_pattern_bytes_including_hud": len(bg_blob),
              "bg_maps": bg_maps, "bg_tile_reconstruction": "decoded indices match all selected cells",
              "header_sha256": sha(header_path),
              "scenes": scenes,
              "limits": "Static SAT only. Geometric distances, body-scale calibration, exact reach, P0 palette, layer priority, PNT, uploads, action timing and framebuffer need verification."}
    (out / "split_probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
