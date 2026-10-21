#!/usr/bin/env python3
"""Prepare a pixel-exact, disposable SMS ROM probe from the Dr. Social v4 poses."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[7]
WRAPPER = ROOT / "tools" / "sms_wrapper"
sys.path.insert(0, str(WRAPPER))

from png_io import read_indexed_png, write_indexed_png  # noqa: E402
from png_to_sms_tiles import tile_bytes  # noqa: E402
from pack_sms_metasprite import pack_poses, header_text  # noqa: E402

SOURCE_DIR = Path(__file__).resolve().parent.parent / "poses_v4"
PROJECT = ROOT / "SMS_projects" / "master_of_fighters"
POSES = (
    ("idle", SOURCE_DIR / "dr_social_idle_keypose_v4.png"),
    ("action", SOURCE_DIR / "dr_social_action_keypose_v4.png"),
)
W = H = 80
COLS = ROWS = 10
SCREEN_X = 88
SCREEN_Y = 48


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sms_code(rgb: tuple[int, int, int]) -> int:
    if any(channel not in (0, 85, 170, 255) for channel in rgb):
        raise ValueError(f"RGB fora da grade SMS: {rgb}")
    r, g, b = (channel // 85 for channel in rgb)
    return r | (g << 2) | (b << 4)


def c_array(name: str, values: list[int], width: int = 16) -> str:
    rows = []
    for start in range(0, len(values), width):
        rows.append("    " + ", ".join(f"0x{v:02X}" for v in values[start:start + width]))
    return f"const unsigned char {name}[{len(values)}] = {{\n" + ",\n".join(rows) + "\n};\n"


def prepare_pose(name: str, source: Path, scratch: Path) -> tuple[dict, list[bytes]]:
    if not source.is_file():
        raise FileNotFoundError(source)
    image = Image.open(source)
    if image.mode != "P" or image.size != (W, H):
        raise ValueError(f"{source}: esperado PNG P {W}x{H}; veio {image.mode} {image.size}")
    transparency = image.info.get("transparency")
    if transparency not in (0, b"\x00"):
        raise ValueError(f"{source}: índice transparente inesperado: {transparency!r}")
    pixels_flat = image.tobytes()
    used = sorted(set(pixels_flat))
    if not used or used[0] != 0 or len(used) - 1 > 15:
        raise ValueError(f"{source}: índice 0 precisa ser transparente e cores úteis <=15; usados={used}")

    raw_palette = image.getpalette()
    palette = [tuple(raw_palette[i:i + 3]) for i in range(0, (max(used) + 1) * 3, 3)]
    for index in used:
        if index and any(channel not in (0, 85, 170, 255) for channel in palette[index]):
            raise ValueError(f"{source}: cor {index} não pertence à grade de 6 bits: {palette[index]}")

    scratch_source = scratch / "rascunho" / f"{name}_source_4bit.png"
    output_png = scratch / "res" / "sprites" / f"dr_social_{name}_keypose_v4.png"
    scratch_source.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, scratch_source)
    rows = [pixels_flat[y * W:(y + 1) * W] for y in range(H)]
    write_indexed_png(str(output_png), W, H, palette, rows, trns=(0,))

    normalized = read_indexed_png(str(output_png))
    if b"".join(normalized["pixels"]) != pixels_flat:
        raise AssertionError(f"{name}: normalização alterou índices de pixel")
    if normalized["palette"][:len(palette)] != palette or 0 not in normalized["trns"]:
        raise AssertionError(f"{name}: normalização alterou paleta/transparência")

    rows8 = normalized["pixels"]
    cells: list[bytes] = []
    cell_map: list[int] = []
    object_cells: list[dict] = []
    row_counts: list[int] = []
    for ty in range(ROWS):
        count = 0
        for tx in range(COLS):
            opaque = any(rows8[y][x] != 0
                         for y in range(ty * 8, ty * 8 + 8)
                         for x in range(tx * 8, tx * 8 + 8))
            pattern = bytes(tile_bytes(rows8, tx, ty))
            cells.append(pattern)
            if not opaque:
                cell_map.append(0xFF)
                continue
            count += 1
            object_cells.append({"x": SCREEN_X + tx * 8,
                                 "y": SCREEN_Y + ty * 8,
                                 "cell_x": tx, "cell_y": ty})
            cell_map.append(-1)  # replaced after cross-pose tile dedupe
        row_counts.append(count)
    return ({
        "name": name,
        "source_path": str(source.relative_to(PROJECT)),
        "source_sha256": sha256(source),
        "source_png_bit_depth": 4,
        "res_path": str(output_png.relative_to(scratch)),
        "res_sha256": sha256(output_png),
        "pixels_exact": True,
        "palette_rgb": [list(c) for c in palette],
        "used_indices": used,
        "transparent_index": 0,
        "cell_pattern_bytes": cells,
        "cell_map": cell_map,
        "object_cells": object_cells,
        "objects_per_8px_row": row_counts,
        "peak_objects_per_scanline": max(row_counts),
    }, cells)


def make_meta_array(name: str, cell_map: list[int]) -> list[int]:
    data = []
    for cell, tile in enumerate(cell_map):
        if tile == 0xFF:
            continue
        x, y = (cell % COLS) * 8, (cell // COLS) * 8
        data.extend((x, y, tile))
    data.append(0x80)  # METASPRITE_END; valid after the last x/y/tile triplet.
    return data


def emit_project(scratch: Path) -> dict:
    if scratch.exists() and any(scratch.iterdir()):
        raise FileExistsError(f"scratch não vazio; preservado sem sobrescrever: {scratch}")
    scratch.mkdir(parents=True, exist_ok=True)
    results = [prepare_pose(name, path, scratch) for name, path in POSES]
    pose_data = [item[0] for item in results]

    packed = pack_poses(
        [("idle", scratch / pose_data[0]["res_path"]),
         ("action", scratch / pose_data[1]["res_path"])],
        reserve_blank=True,
    )
    for pose, packed_pose in zip(pose_data, packed["poses"]):
        pose["cell_map"] = [0xFF if tile is None else tile for tile in packed_pose["tile_map"]]
        pose["object_cells"] = [
            {"x": SCREEN_X + obj["x"], "y": SCREEN_Y + obj["y"], "tile": obj["tile"]}
            for obj in packed_pose["objects"]
        ]
        pose["peak_objects_per_scanline"] = packed_pose["peak_scanline"]
        pose.pop("cell_pattern_bytes", None)
    palette_rgb = pose_data[0]["palette_rgb"]
    palette_codes = packed["palette_codes"]

    inc = scratch / "inc"
    src = scratch / "src"
    doc = scratch / "doc"
    inc.mkdir(parents=True, exist_ok=True)
    src.mkdir(parents=True, exist_ok=True)
    doc.mkdir(parents=True, exist_ok=True)
    tiles_flat = list(packed["tile_bytes"])
    unique_count = packed["unique_patterns"]
    loaded_pattern_count = packed["loaded_patterns"]
    (inc / "dr_social_tiles.h").write_text(header_text(packed, "dr_social"), encoding="utf-8")

    (src / "main.c").write_text(r'''#include "SMSlib.h"
#include "dr_social_tiles.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_16KB(0, 1, 2026, 10, 10,
                           "SMSForge", "SocialProbe", "Dr Social asset probe");

static const unsigned char probe_bg_palette[16] = {
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};
static unsigned char pose_action;

static void draw_pose(void) {
    const signed char *meta = pose_action
        ? (const signed char *)dr_social_action_meta
        : (const signed char *)dr_social_idle_meta;
    SMS_initSprites();
    SMS_addMetaSprite(88, 48, (void *)meta);
    SMS_copySpritestoSAT();
}

void main(void) {
    unsigned int keys;
    unsigned char row, col;
    SMS_init();
    SMS_displayOff();
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    SMS_useFirstHalfTilesforSprites(1);
    SMS_loadTiles(dr_social_tiles, DR_SOCIAL_TILE_BASE, DR_SOCIAL_TILE_BYTES);
    SMS_loadBGPalette(probe_bg_palette);
    SMS_loadSpritePalette(dr_social_palette);
    SMS_setBackdropColor(0);
    /* Tile 0 is reserved blank. Clear the visible PNT so reset-state VRAM
       cannot expose the loaded fighter patterns behind transparent pixels. */
    for (row = 0; row < 24; ++row)
        for (col = 0; col < 32; ++col)
            SMS_setTileatXY(col, row, 0);
    pose_action = 0;
    draw_pose();
    SMS_displayOn();

    for (;;) {
        SMS_waitForVBlank();
        keys = SMS_getKeysPressed();
        if (keys & PORT_A_KEY_1) pose_action = 0;
        if (keys & PORT_A_KEY_2) pose_action = 1;
        draw_pose();
    }
}
''', encoding="utf-8")

    (scratch / ".mddev").mkdir(parents=True, exist_ok=True)
    (scratch / ".mddev" / "project.json").write_text(json.dumps({
        "name": "dr_social_asset_probe_v3",
        "platform": "sega_master_system",
        "region_target": ["NTSC", "PAL"],
        "toolchain": {"compiler": "sdcc>=4.2", "sdk": "devkitSMS",
                      "libs": ["SMSlib", "PSGlib"]},
        "skeleton_version": 1,
        "specialization": "fighting",
    }, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(PROJECT / "doc" / "palettes_manifest.json", doc / "palettes_manifest.json")

    assets = []
    for pose in pose_data:
        source_name = Path(pose["source_path"]).name
        source_copy = scratch / "rascunho" / f"{pose['name']}_source_4bit.png"
        assets.append({
            "file": pose["res_path"],
            "origin": str(source_copy.relative_to(scratch)),
            "author": "Master of Fighters source-art lineage; lossless PNG normalization probe",
            "tool": "rom_probe_v1:lossless_indexed_8bit",
            "role": "pixel_sprite_candidate",
            "sha256": sha256(source_copy),
            "source_path": pose["source_path"],
            "source_sha256": pose["source_sha256"],
            "pixel_indices_preserved": True,
        })
    (doc / "asset_provenance_manifest.json").write_text(json.dumps({"assets": assets}, indent=2) + "\n", encoding="utf-8")

    for pose in pose_data:
        manifest = {
            "schema": "sprite_scene_manifest_v1",
            "sprite_size": "8x8",
            "zoomed": False,
            "screen_h": 192,
            "sprites": [{"x": s["x"], "y": s["y"], "tile": s["tile"]}
                        for s in pose["object_cells"]],
        }
        (doc / f"sprite_scene_{pose['name']}_v1.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    report = {
            "schema": "dr_social_sms_rom_probe_v3",
        "status": "diagnostic_candidate_not_production",
        "project": "master_of_fighters",
        "rom_project_path": str(scratch.relative_to(ROOT)),
        "source_pose_images": pose_data,
        "palette": {
            "use": "single-character diagnostic P1 only",
            "runtime_roster_mapping": "pending; not tested here",
            "palette_codes_6bit": palette_codes,
            "color_count_including_transparency": len(palette_rgb),
            "useful_color_count": len(palette_rgb) - 1,
        },
        "packing": {
            "object_geometry": "8x8 SAT objects grouped into SMSlib metasprites",
            "unique_patterns_shared_by_two_poses": unique_count,
            "loaded_patterns_including_reserved_blank": loaded_pattern_count,
            "tile_bytes_4bpp": len(tiles_flat),
            "pattern_window_limit": 256,
            "source_canvas_px": [W, H],
            "cell_grid": [COLS, ROWS],
            "input_position": [SCREEN_X, SCREEN_Y],
        },
        "animation_claim": "none; button selection changes between two static key poses",
        "pending": ["independent pixel-art review", "owner-specific pixel-asset approval",
                    "roster-wide P1 mapping", "animation timeline and frame semantics",
                    "scene RAM/ROM/VRAM/VBlank budgets", "delivery ROM binding"],
    }
    # Omit internal binary tile bytes from the JSON report; the C header is the generated source.
    for pose in report["source_pose_images"]:
        del pose["object_cells"]
    report_path = Path(__file__).resolve().parent / "conversion_report_v3.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scratch", required=True, help="empty, ignored diagnostic project directory")
    args = parser.parse_args()
    scratch = Path(args.scratch).resolve()
    report = emit_project(scratch)
    print(json.dumps({
        "scratch": str(scratch),
        "shared_unique_patterns": report["packing"]["unique_patterns_shared_by_two_poses"],
        "loaded_patterns_including_reserved_blank": report["packing"]["loaded_patterns_including_reserved_blank"],
        "tile_bytes": report["packing"]["tile_bytes_4bpp"],
        "poses": [{"name": p["name"], "objects": len(p.get("cell_map", [])) - p["cell_map"].count(0xFF),
                   "peak_scanline": p["peak_objects_per_scanline"]} for p in report["source_pose_images"]],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
