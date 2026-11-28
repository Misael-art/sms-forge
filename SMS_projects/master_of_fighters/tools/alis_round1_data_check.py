#!/usr/bin/env python3
"""Check static round-1 asset data; this is not a runtime or artistic verdict."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parents[1]
sys.path.insert(0, str(REPO / "tools/sms_wrapper"))
from audit_sprite_line_sim import simulate  # noqa: E402
from mugen2sms.generators.runtime_format import decode_indices  # noqa: E402
from png_to_sms_tiles import tile_bytes  # noqa: E402

BASE = PROJECT / "out/diagnostics/alis_strong_thrust_round1"


def array_from_header(text, name):
    match = re.search(r"const unsigned char " + re.escape(name) + r"\[(\d+)\] = \{(.*?)\};", text, re.S)
    if not match:
        raise ValueError("missing array: " + name)
    values = [int(v, 16) for v in re.findall(r"0x([0-9A-Fa-f]{2})", match.group(2))]
    if len(values) != int(match.group(1)):
        raise ValueError("array length mismatch: " + name)
    return values


def verify_map(mapping, blobs, expected):
    if not mapping or mapping[-1] != 255 or (len(mapping) - 1) % 3:
        raise ValueError("invalid BG map terminator or triples")
    result, seen = {}, set()
    for i in range(0, len(mapping) - 1, 3):
        tx, ty, tile = mapping[i:i + 3]
        if not (tx < 32 and ty < 24 and tile < len(blobs)) or (tx, ty) in seen:
            raise ValueError("BG map coordinate, tile or duplicate invalid")
        seen.add((tx, ty))
        for offset, value in enumerate(decode_indices(blobs[tile])):
            if value:
                result[(tx * 8 + offset % 8, ty * 8 + offset // 8)] = value
    if result != expected:
        raise ValueError("BG tile reconstruction differs from source")
    return len(seen)


def verify_sprite(meta, blobs, expected, height=88):
    if not meta or meta[-1] != 128 or (len(meta) - 1) % 3:
        raise ValueError("invalid metasprite terminator or triples")
    if len(expected) != 128 * height:
        raise ValueError("sprite source canvas size differs")
    result = bytearray(128 * height)
    for i in range(0, len(meta) - 1, 3):
        x, y, tile = meta[i:i + 3]
        if tile >= len(blobs):
            raise ValueError("sprite tile outside resident pool")
        for offset, value in enumerate(decode_indices(blobs[tile])):
            if value:
                px, py = x + offset % 8, y + offset // 8
                if px >= 128 or py >= height or result[py * 128 + px]:
                    raise ValueError("sprite pixel outside canvas or overlapping")
                result[py * 128 + px] = value
    if bytes(result) != expected:
        raise ValueError("sprite reconstruction differs from indexed source")
    return (len(meta) - 1) // 3


def self_check():
    rows = [[0] * 8 for _ in range(8)]
    rows[2][3] = 14
    blob = bytes(tile_bytes(rows, 0, 0))
    assert verify_map([1, 2, 0, 255], [blob], {(11, 18): 14}) == 1
    expected_sprite = bytearray(128 * 88)
    expected_sprite[18 * 128 + 11] = 14
    assert verify_sprite([8, 16, 0, 128], [blob], bytes(expected_sprite)) == 1
    for bad in ([8, 16, 1, 128], [127, 16, 0, 128], [8, 16, 0],
                [8, 16, 0, 8, 16, 0, 128]):
        try:
            verify_sprite(bad, [blob], bytes(expected_sprite))
        except ValueError:
            continue
        raise AssertionError("invalid sprite metadata accepted")
    try:
        verify_sprite([8, 16, 0, 128], [blob], bytes(128 * 88))
    except ValueError:
        pass
    else:
        raise AssertionError("wrong sprite reconstruction accepted")
    for bad in ([32, 2, 0, 255], [1, 2, 1, 255], [1, 2, 0], [1, 2, 0, 1, 2, 0, 255]):
        try:
            verify_map(bad, [blob], {(11, 18): 14})
        except ValueError:
            continue
        raise AssertionError("invalid BG map accepted")
    try:
        verify_map([1, 2, 0, 255], [blob], {(11, 18): 13})
    except ValueError:
        pass
    else:
        raise AssertionError("wrong pixel reconstruction accepted")
    print("[SELF-CHECK OK] Sprite and BG bounds, metadata, tiles and reconstruction")


def check(grounded=False):
    owner = BASE / ("grounded_faces_assets_probe" if grounded else "both_faces_assets_probe")
    height = 96 if grounded else 88
    row = 44 if grounded else 45
    receipt = json.loads((owner / "split_probe.json").read_text())
    header_path = owner / "both_faces_assets.h"
    header_bytes = header_path.read_bytes()
    if hashlib.sha256(header_bytes).hexdigest() != receipt["header_sha256"]:
        raise ValueError("header SHA differs from generated receipt")
    header = header_bytes.decode("ascii")
    data = array_from_header(header, "alis_bg_tiles")
    count = receipt["bg_patterns"]
    if len(data) != (count + 1) * 32 or count + 1 > 192:
        raise ValueError("BG pattern extent invalid")
    blobs = [bytes(data[i * 32:(i + 1) * 32]) for i in range(count)]
    if decode_indices(bytes(data[count * 32:(count + 1) * 32])) != [15] * 64:
        raise ValueError("HUD tile is not solid index 15")
    if receipt["sprite_patterns"] > 256:
        raise ValueError("sprite patterns exceed first VRAM half")
    sprite_data = array_from_header(header, "alis_sample_tiles")
    if len(sprite_data) != receipt["sprite_patterns"] * 32 or any(sprite_data[:32]):
        raise ValueError("sprite pool size or reserved blank tile invalid")
    sprite_blobs = [bytes(sprite_data[i * 32:(i + 1) * 32])
                    for i in range(receipt["sprite_patterns"])]
    palette = array_from_header(header, "alis_sample_palette")
    if len(palette) != 16 or any(value > 63 for value in palette):
        raise ValueError("shared palette is not SMS 6-bit")
    sprite_checks = {}
    for face in ("right", "left"):
        source = BASE / ("sequence_grounded96_" + face + "_probe" if grounded else "sequence_" + face + "_probe")
        for pose in ("idle", "prepare", "thrust", "recover", "reference"):
            key = face + "_" + pose
            path = (owner / (key + "_sat.png") if pose in ("prepare", "thrust")
                    else source / (pose + ".png"))
            image = Image.open(path)
            if image.mode != "P" or image.size != (128, height) or image.info.get("transparency") != 0:
                raise ValueError("unexpected sprite source contract")
            sprite_checks[key] = verify_sprite(array_from_header(header, "alis_sample_" + key + "_meta"),
                                               sprite_blobs, image.tobytes(), height)
    bg_checks = {}
    for face in ("right", "left"):
        origin = 0 if face == "right" else 112
        for pose in ("prepare", "thrust"):
            name = face + "_" + pose
            image = Image.open(owner / (name + "_bg.png"))
            pixels = image.tobytes()
            expected = {(origin + i % 128, 64 + i // 128): value
                        for i, value in enumerate(pixels) if value}
            mapping = array_from_header(header, "alis_bg_" + name)
            bg_checks[name] = {"cells": verify_map(mapping, blobs, expected), "pixels": len(expected)}
    scenes = sorted(owner.glob("scene_*.json"))
    if len(scenes) != 24:
        raise ValueError("expected 24 static scenes")
    reports = [simulate(json.loads(path.read_text())) for path in scenes]
    if any(report["violations"] for report in reports):
        raise ValueError("scene simulator found a violation")
    geometry, bg_overlap = {}, {}
    for face in ("right", "left"):
        images = BASE / ("sequence_grounded96_" + face + "_probe" if grounded else "sequence_" + face + "_probe")
        actor = Image.open(images / "thrust.png")
        target = Image.open(images / "reference.png")
        blade = Image.open(owner / (face + "_thrust_bg.png"))
        actor_x = 0 if face == "right" else 112
        targets = [52, 60, 68] if face == "right" else [60, 52, 44]
        actor_row = [x for x in range(128) if actor.getpixel((x, row))]
        target_row = [x for x in range(128) if target.getpixel((x, row))]
        if not actor_row or not target_row:
            raise ValueError("geometric measurement row is empty")
        tip = actor_x + (max(actor_row) if face == "right" else min(actor_row))
        fragments = [(x, y) for y in range(height) for x in range(128) if blade.getpixel((x, y))]
        values, overlaps = [], []
        for target_x in targets:
            edge = target_x + (min(target_row) if face == "right" else max(target_row))
            values.append(tip - edge if face == "right" else edge - tip)
            overlaps.append(sum(0 <= actor_x + x - target_x < 128 and
                                target.getpixel((actor_x + x - target_x, y)) != 0
                                for x, y in fragments))
        if values != [8, 0, -8]:
            raise ValueError("provisional geometric threshold changed: " + face)
        geometry[face] = values
        bg_overlap[face] = overlaps
    print(json.dumps({"status": "static_data_only", "grounded": grounded, "geometry_canvas_y": row, "header_sha256": receipt["header_sha256"],
                      "sprite_patterns": receipt["sprite_patterns"], "bg_patterns": count,
                      "bg_bytes_including_hud": len(data), "bg_maps": bg_checks,
                      "sprite_reconstructions": sprite_checks,
                      "scenes": len(scenes), "max_sat": max(r["sprites"] for r in reports),
                      "max_per_scanline": max(r["peak_per_line"] for r in reports),
                      "visible_edge_delta_near_limit_outside": geometry,
                      "blade_bg_overlap_with_target_near_limit_outside": bg_overlap,
                      "limitations": "Does not execute ROM, prove dynamic PNT writes, layering, visual quality, VBlank, input or FPS."}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--grounded", action="store_true")
    args = parser.parse_args()
    self_check() if args.self_check else check(args.grounded)
