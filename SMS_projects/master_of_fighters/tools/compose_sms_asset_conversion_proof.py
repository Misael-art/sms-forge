#!/usr/bin/env python3
"""HISTORICAL, REJECTED v1 compositor. Do not use for new proof boards.

The v1 board drew an 8x8 grid over the sprite preview and is invalid for visual
review. Use compose_sms_keypose_proof.py and audit_asset_proof_sheet.py.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


SMS_CHANNELS = {0, 85, 170, 255}
KEY_CANDIDATES = {
    "magenta": (255, 0, 255),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
}
PAPER = (245, 242, 234)
CARD = (255, 253, 248)
NAVY = (12, 18, 69)
INK = (40, 45, 59)
MUTED = (102, 109, 121)
LINE = (210, 207, 197)
ACCENT = (0, 117, 145)
ALERT = (171, 49, 35)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def project_path(root: Path, raw: str | None) -> Path | None:
    if raw is None:
        return None
    path = Path(raw)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_paragraph(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] = INK,
    max_width: int = 600,
    line_gap: int = 8,
) -> int:
    x, y = xy
    for line in wrap_text(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_gap
    return y


def rounded_card(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    fill: tuple[int, int, int] = CARD,
    outline: tuple[int, int, int] = LINE,
    radius: int = 22,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def palette_data(indexed: Image.Image, rgba: Image.Image, transparent_indices: set[int]) -> tuple[list[dict[str, Any]], dict[int, int]]:
    used = set()
    if indexed.mode == "P":
        raw = indexed.load()
        alpha = rgba.load()
        for y in range(indexed.height):
            for x in range(indexed.width):
                if alpha[x, y][3] > 0:
                    used.add(raw[x, y])
        raw_palette = indexed.getpalette() or []
        index_to_code = {index: code for code, index in enumerate(sorted(used), start=1)}
        entries = []
        for index in sorted(used):
            start = index * 3
            color = tuple(raw_palette[start:start + 3])
            entries.append({"index": int(index), "rgb": list(color), "useful": True})
        return entries, index_to_code

    colors = sorted({pixel[:3] for pixel in rgba.get_flattened_data() if pixel[3] > 0})
    color_to_code = {color: code for code, color in enumerate(colors, start=1)}
    entries = [
        {"index": color_to_code[color], "rgb": list(color), "useful": True}
        for color in colors
    ]
    return entries, color_to_code


def source_code_at(
    indexed: Image.Image,
    rgba: Image.Image,
    x: int,
    y: int,
    index_to_code: dict[int, int],
    color_to_code: dict[tuple[int, int, int], int],
) -> int:
    rgba_pixel = rgba.getpixel((x, y))
    if rgba_pixel[3] == 0:
        return 0
    if indexed.mode == "P":
        return index_to_code[indexed.getpixel((x, y))]
    return color_to_code[rgba_pixel[:3]]


def frame_metrics(
    indexed: Image.Image,
    rgba: Image.Image,
    frame_x: int,
    frame_y: int,
    frame_w: int,
    frame_h: int,
    tile_px: int,
    index_to_code: dict[int, int],
    color_to_code: dict[tuple[int, int, int], int],
) -> dict[str, Any]:
    frame = rgba.crop((frame_x, frame_y, frame_x + frame_w, frame_y + frame_h))
    alpha = frame.getchannel("A")
    bbox = alpha.getbbox()
    occupied: list[list[int]] = []
    patterns: set[bytes] = set()
    for tile_y in range(frame_h // tile_px):
        for tile_x in range(frame_w // tile_px):
            codes = bytearray()
            has_opaque = False
            for py in range(tile_px):
                for px in range(tile_px):
                    code = source_code_at(
                        indexed,
                        rgba,
                        frame_x + tile_x * tile_px + px,
                        frame_y + tile_y * tile_px + py,
                        index_to_code,
                        color_to_code,
                    )
                    codes.append(code)
                    has_opaque = has_opaque or code != 0
            if has_opaque:
                occupied.append([tile_x, tile_y])
                patterns.add(bytes(codes))
    visible_bbox = list(bbox) if bbox else None
    return {
        "bbox_xyxy_exclusive": visible_bbox,
        "visible_bbox_px_including_equipment": [
            bbox[2] - bbox[0],
            bbox[3] - bbox[1],
        ] if bbox else [0, 0],
        "occupied_tile_cells": len(occupied),
        "unique_tile_patterns": len(patterns),
        "occupied_tile_coordinates_xy": occupied,
        "patterns": patterns,
    }


def choose_key(palette_rgb: list[tuple[int, int, int]]) -> tuple[str, tuple[int, int, int], dict[str, Any]]:
    scored = []
    for name, key in KEY_CANDIDATES.items():
        distances = [
            math.sqrt(sum((color[i] - key[i]) ** 2 for i in range(3)))
            for color in palette_rgb
        ]
        score = sum(distances) / len(distances) if distances else 0.0
        min_distance = min(distances) if distances else 0.0
        collision = key in palette_rgb
        scored.append((score, min_distance, name, key, collision))
    score, min_distance, name, key, collision = max(scored, key=lambda item: (item[0], item[1], not item[4]))
    return name, key, {
        "selection_metric": "maximum mean Euclidean RGB distance to used opaque colors",
        "mean_nearest_rgb_distance": round(score, 2),
        "minimum_nearest_rgb_distance": round(min_distance, 2),
        "key_matches_opaque_asset_color": collision,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Indexed or transparent PNG sprite sheet")
    parser.add_argument("--output", required=True, help="Output proof-board PNG")
    parser.add_argument("--report", required=True, help="Output measured JSON report")
    parser.add_argument("--concept", required=True, help="Approved concept/model sheet reference")
    parser.add_argument("--source-contract", required=True, help="Source sprite asset contract JSON")
    parser.add_argument("--palette-manifest", default="doc/palettes_manifest.json")
    parser.add_argument("--palette-character-key", default="dr_ferdinand_social")
    parser.add_argument("--asset-id", default="dr_social_sms_conversion_proof_v1")
    parser.add_argument("--display-name", default="Dr. Ferdinand Social")
    parser.add_argument("--style-reference-name", default="Concept model sheet #01 · CPS2-Alpha-Cel")
    parser.add_argument("--translation-target", default="Pixel art SMS · paleta Master of Darkness")
    parser.add_argument("--asset-type", default="character", choices=["character", "item", "prop", "stage_piece"])
    parser.add_argument("--frame-width", type=int, default=96)
    parser.add_argument("--frame-height", type=int, default=96)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--frame-index", type=int, default=8, help="Selected frame, zero-based")
    parser.add_argument("--tile-size", type=int, default=8)
    parser.add_argument("--target-low", type=int, default=78)
    parser.add_argument("--target-high", type=int, default=82)
    parser.add_argument("--target-center", type=int, default=80)
    parser.add_argument(
        "--reproduce-rejected-v1",
        action="store_true",
        help="explicitly reproduce the archived invalid v1 layout for historical comparison only",
    )
    args = parser.parse_args()
    if not args.reproduce_rejected_v1:
        parser.error("v1 is rejected: its tile grid crosses the sprite. Use compose_sms_keypose_proof.py.")

    root = Path(__file__).resolve().parents[1]
    source_path = project_path(root, args.source)
    output_path = project_path(root, args.output)
    report_path = project_path(root, args.report)
    concept_path = project_path(root, args.concept)
    contract_path = project_path(root, args.source_contract)
    palette_manifest_path = project_path(root, args.palette_manifest)
    assert source_path and output_path and report_path and concept_path and contract_path and palette_manifest_path
    for required in (source_path, concept_path, contract_path, palette_manifest_path):
        if not required.is_file():
            parser.error(f"required input does not exist: {required}")

    indexed = Image.open(source_path)
    rgba = indexed.convert("RGBA")
    if args.frame_width % args.tile_size or args.frame_height % args.tile_size:
        parser.error("frame dimensions must be divisible by the tile size")
    if indexed.width != args.frame_width * args.columns or indexed.height != args.frame_height * args.rows:
        parser.error(
            f"sheet dimensions {indexed.size} do not match "
            f"{args.columns}x{args.rows} cells of {args.frame_width}x{args.frame_height}"
        )
    frame_count = args.columns * args.rows
    if not 0 <= args.frame_index < frame_count:
        parser.error("selected frame index is outside the declared sheet")

    transparent_metadata = indexed.info.get("transparency", 0)
    if isinstance(transparent_metadata, int):
        transparent_indices = {transparent_metadata}
    elif isinstance(transparent_metadata, bytes):
        transparent_indices = {i for i, alpha in enumerate(transparent_metadata) if alpha == 0}
    else:
        transparent_indices = {0}

    entries, index_to_code = palette_data(indexed, rgba, transparent_indices)
    color_to_code: dict[tuple[int, int, int], int] = {}
    if indexed.mode != "P":
        color_to_code = {tuple(entry["rgb"]): int(entry["index"]) for entry in entries}

    palette_manifest = json.loads(palette_manifest_path.read_text(encoding="utf-8"))
    palette_character = palette_manifest["characters"][args.palette_character_key]
    role_by_rgb = {
        tuple(color["rgb"]): color["role"]
        for color in palette_character.get("colors", [])
    }
    for entry in entries:
        entry["role"] = role_by_rgb.get(tuple(entry["rgb"]), "unmapped_rgb")
    colors_rgb = [tuple(entry["rgb"]) for entry in entries]
    palette_6bit_pass = all(channel in SMS_CHANNELS for color in colors_rgb for channel in color)
    alpha_values = set(rgba.getchannel("A").get_flattened_data())
    alpha_binary = alpha_values <= {0, 255}
    frame_results: list[dict[str, Any]] = []
    all_patterns: set[bytes] = set()
    all_placements = 0
    for frame_index in range(frame_count):
        column = frame_index % args.columns
        row = frame_index // args.columns
        result = frame_metrics(
            indexed,
            rgba,
            column * args.frame_width,
            row * args.frame_height,
            args.frame_width,
            args.frame_height,
            args.tile_size,
            index_to_code,
            color_to_code,
        )
        all_patterns.update(result.pop("patterns"))
        all_placements += result["occupied_tile_cells"]
        frame_results.append({"frame_index_zero_based": frame_index, **result})

    selected = frame_results[args.frame_index]
    frame_col = args.frame_index % args.columns
    frame_row = args.frame_index // args.columns
    selected_xy = (
        frame_col * args.frame_width,
        frame_row * args.frame_height,
        (frame_col + 1) * args.frame_width,
        (frame_row + 1) * args.frame_height,
    )
    selected_image = rgba.crop(selected_xy)
    selected_w, selected_h = selected["visible_bbox_px_including_equipment"]
    visible_height = selected_h
    target_status = (
        "within_working_band_by_opaque_bbox"
        if args.target_low <= visible_height <= args.target_high
        else "outside_working_band_by_opaque_bbox"
    )
    used_palette = []
    indexed_counts = Counter(indexed.get_flattened_data()) if indexed.mode == "P" else Counter()
    for entry in entries:
        used_palette.append({
            "palette_index": entry["index"],
            "rgb": entry["rgb"],
            "hex": "#{:02X}{:02X}{:02X}".format(*entry["rgb"]),
            "role": entry["role"],
            "pixel_count": int(indexed_counts.get(entry["index"], 0)) if indexed.mode == "P" else None,
        })
    used_rgb = {tuple(entry["rgb"]) for entry in entries}
    manifest_colors_not_used = [
        {"role": color["role"], "rgb": color["rgb"]}
        for color in palette_character.get("colors", [])
        if tuple(color["rgb"]) not in used_rgb
    ]

    key_name, key_rgb, key_metrics = choose_key(colors_rgb)
    key_hex = "#{:02X}{:02X}{:02X}".format(*key_rgb)
    source_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    selected_patterns = selected["unique_tile_patterns"]
    slots = (args.frame_width // args.tile_size) * (args.frame_height // args.tile_size)
    all_pattern_count = len(all_patterns)
    report: dict[str, Any] = {
        "schema": "smsforge.asset_conversion_proof.v1",
        "status": "technical_candidate_visual_review_pending",
        "asset": {
            "asset_id": args.asset_id,
            "asset_type": args.asset_type,
            "display_name": args.display_name,
            "project": "master_of_fighters",
            "role": "source_art_technical_conversion_proof",
            "source_contract_status": source_contract.get("approval_scope", "not_declared"),
        },
        "style_reference": {
            "concept_style_name": args.style_reference_name,
            "translation_target": args.translation_target,
            "note": "concept style reference and SMS technical rendering are distinct review axes",
        },
        "references": {
            "approved_concept_or_scale_reference_path": str(concept_path.relative_to(root)),
            "approved_concept_or_scale_reference_sha256": sha256(concept_path),
            "source_asset_path": str(source_path.relative_to(root)),
            "source_asset_sha256": sha256(source_path),
            "source_asset_contract_path": str(contract_path.relative_to(root)),
            "source_asset_contract_sha256": sha256(contract_path),
            "palette_manifest_path": str(palette_manifest_path.relative_to(root)),
            "palette_manifest_sha256": sha256(palette_manifest_path),
            "concept_reference_role": "identity_and_relative_scale_context; not claimed as direct pixel-conversion input",
        },
        "target": {
            "platform": "Sega Master System",
            "medium": "indexed pixel art",
            "gdd_visible_height_range_px": [args.target_low, args.target_high],
            "gdd_working_center_px": args.target_center,
            "selected_frame_opaque_bbox_height_px_including_equipment": visible_height,
            "delta_to_working_center_px": visible_height - args.target_center,
            "scale_status": target_status,
            "body_only_height_status": "pending_human_masked_measurement",
            "bbox_measurement_note": "alpha bbox measures total opaque silhouette and may include weapon/equipment; it is not a body-only anatomy measure",
        },
        "geometry": {
            "source_image_dimensions_px": list(indexed.size),
            "frame_width_px": args.frame_width,
            "frame_height_px": args.frame_height,
            "columns": args.columns,
            "rows": args.rows,
            "frame_count": frame_count,
            "reading_order": "left-to-right, top-to-bottom",
            "tile_px": args.tile_size,
            "transparent_index": int(transparent_metadata) if isinstance(transparent_metadata, int) else 0,
            "selected_frame_index_zero_based": args.frame_index,
            "selected_frame_number_one_based": args.frame_index + 1,
            "selected_frame_opaque_bbox_xyxy_exclusive": selected["bbox_xyxy_exclusive"],
            "selected_frame_opaque_bbox_px_including_equipment": [selected_w, selected_h],
            "selected_frame_bbox_includes_equipment": True,
        },
        "palette": {
            "indexed_png": indexed.mode == "P",
            "transparent_palette_index": int(transparent_metadata) if isinstance(transparent_metadata, int) else 0,
            "useful_color_limit": 15,
            "useful_colors_used": len(entries),
            "sms_rgb_6bit_grid_pass": palette_6bit_pass,
            "alpha_binary_pass": alpha_binary,
            "palette_manifest_character_key": args.palette_character_key,
            "manifest_defined_useful_colors": palette_character.get("usable_colors"),
            "manifest_roles_not_used_in_source": manifest_colors_not_used,
            "entries": used_palette,
            "inspection_key_name": key_name,
            "inspection_key_rgb": list(key_rgb),
            "inspection_key_hex": key_hex,
            "inspection_key_is_asset_color": key_rgb in colors_rgb,
            "inspection_key_contrast_metric": key_metrics,
        },
        "tile_accounting": {
            "method": "exact indexed 8x8 patterns; omit empty transparent cells; no flip deduplication",
            "canvas_tile_slots_per_frame": slots,
            "selected_frame_occupied_tile_cells": selected["occupied_tile_cells"],
            "selected_frame_unique_tile_patterns": selected_patterns,
            "raw_4bpp_bytes_per_pattern": 32,
            "raw_4bpp_bytes_selected_frame": selected_patterns * 32,
            "occupied_tile_placements_all_frames": all_placements,
            "unique_tile_patterns_all_frames": all_pattern_count,
            "raw_4bpp_bytes_unique_sheet_patterns": all_pattern_count * 32,
            "runtime_vram_residency": "not_claimed; runtime tables, pools, banking, and frame-loading policy are unresolved",
            "frames": [
                {
                    "frame_index_zero_based": frame["frame_index_zero_based"],
                    "opaque_bbox_xyxy_exclusive": frame["bbox_xyxy_exclusive"],
                    "opaque_bbox_px_including_equipment": frame["visible_bbox_px_including_equipment"],
                    "occupied_tile_cells": frame["occupied_tile_cells"],
                    "unique_tile_patterns": frame["unique_tile_patterns"],
                    "raw_4bpp_bytes_if_frame_patterns_loaded": frame["unique_tile_patterns"] * 32,
                }
                for frame in frame_results
            ],
        },
        "proof_sheet": {
            "image_path": str(output_path.relative_to(root)),
            "image_sha256": None,
            "report_path": str(report_path.relative_to(root)),
            "display_scale": "native 1x plus nearest-neighbor enlarged views",
            "inspection_background_rule": "one of #FF00FF, #00FF00, #0000FF chosen by palette contrast; not included in asset palette",
        },
        "review": {
            "pixel_clusters": "pending",
            "face_detail_readability": "pending",
            "outline_and_cutout": "pending",
            "material_shading": "pending",
            "hand_weapon_attachment": "pending",
            "equipment_geometry": "pending",
            "frame_pose_integrity": "pending",
            "native_size_readability": "pending",
            "artist_reference_and_scope": "pending",
            "style_signature_and_distinction": "pending",
            "document_and_layout": "pending",
            "identity_and_palette": "pending",
            "scale_and_morphology": "pending",
            "anatomy_and_equipment": "pending",
            "clusters_and_cutout": "pending",
            "frame_integrity": "pending",
            "independent_review": "pending",
            "owner_decision": "pending",
        },
        "promotion": {
            "approved_for_res": False,
            "rom_asset_binding": "not_created",
            "emulator_validation": "not_performed",
        },
    }

    page = Image.new("RGB", (2800, 2070), PAPER)
    draw = ImageDraw.Draw(page)
    font_title = load_font(58, True)
    font_subtitle = load_font(27)
    font_heading = load_font(29, True)
    font_body = load_font(23)
    font_small = load_font(18)
    font_micro = load_font(15)
    font_number = load_font(31, True)

    draw.text((72, 45), "PROVA TÉCNICA DE CONVERSÃO", font=font_title, fill=NAVY)
    draw.text((75, 119), f"{args.display_name}  ·  SPRITE SMS  ·  8×8", font=font_subtitle, fill=ACCENT)
    draw.text((75, 162), f"{args.style_reference_name}  ·  {args.translation_target}  ·  escala, paleta e tiles", font=font_small, fill=MUTED)
    rounded_card(draw, (2175, 55, 2728, 145), fill=(240, 235, 224), outline=(199, 192, 178), radius=18)
    draw.text((2210, 79), "CANDIDATO TÉCNICO", font=load_font(25, True), fill=NAVY)
    draw.text((2210, 111), "revisão visual pendente", font=font_small, fill=ALERT)

    left = (70, 220, 1390, 1150)
    right = (1420, 220, 2730, 1150)
    bottom = (70, 1180, 2730, 1950)
    rounded_card(draw, left)
    rounded_card(draw, right)
    rounded_card(draw, bottom)

    draw.text((105, 250), f"QUADRO {args.frame_index + 1:02d}/{frame_count:02d}  ·  PIXELS-FONTE INTACTOS", font=font_heading, fill=NAVY)
    draw.text((105, 292), f"Ampliação {7}× nearest-neighbor  ·  grade de tile sobreposta para consulta", font=font_small, fill=MUTED)

    stage_x, stage_y, stage_w, stage_h = 120, 345, 760, 740
    draw.rectangle((stage_x, stage_y, stage_x + stage_w, stage_y + stage_h), fill=key_rgb)
    scale = 7
    zoomed = selected_image.resize((args.frame_width * scale, args.frame_height * scale), Image.Resampling.NEAREST)
    sprite_x = stage_x + (stage_w - zoomed.width) // 2
    sprite_y = stage_y + (stage_h - zoomed.height) // 2
    green_back = Image.new("RGBA", zoomed.size, (*key_rgb, 255))
    green_back.alpha_composite(zoomed)
    grid = Image.new("RGBA", zoomed.size, (0, 0, 0, 0))
    grid_draw = ImageDraw.Draw(grid)
    grid_color = (9, 15, 48, 105)
    for px in range(0, zoomed.width + 1, args.tile_size * scale):
        grid_draw.line((px, 0, px, zoomed.height), fill=grid_color, width=1)
    for py in range(0, zoomed.height + 1, args.tile_size * scale):
        grid_draw.line((0, py, zoomed.width, py), fill=grid_color, width=1)
    green_back.alpha_composite(grid)
    page.paste(green_back.convert("RGB"), (sprite_x, sprite_y))

    bbox = selected["bbox_xyxy_exclusive"]
    if bbox:
        box = (
            sprite_x + bbox[0] * scale,
            sprite_y + bbox[1] * scale,
            sprite_x + bbox[2] * scale - 1,
            sprite_y + bbox[3] * scale - 1,
        )
        draw.rectangle(box, outline=(255, 210, 0), width=4)
        baseline_y = sprite_y + bbox[3] * scale
        draw.line((stage_x + 12, baseline_y, stage_x + stage_w - 12, baseline_y), fill=(20, 18, 61), width=3)
        draw.text((stage_x + 18, baseline_y + 7), "limite inferior da bbox opaca", font=font_micro, fill=NAVY)

    ruler_x = stage_x + 8
    draw.line((ruler_x, sprite_y, ruler_x, sprite_y + zoomed.height), fill=NAVY, width=2)
    for source_y in range(0, args.frame_height + 1, 8):
        y = sprite_y + source_y * scale
        draw.line((ruler_x - 5, y, ruler_x + 7, y), fill=NAVY, width=2)
        if source_y % 16 == 0:
            draw.text((stage_x + 18, y - 13), str(source_y), font=font_micro, fill=NAVY)
    draw.text((stage_x + 18, stage_y + stage_h - 34), f"fundo de prova {key_hex} · fora da paleta do asset", font=font_micro, fill=NAVY)

    draw.text((920, 357), "MAPA DE CÉLULAS 8×8", font=font_heading, fill=NAVY)
    draw.text((920, 397), "12×12 posições possíveis no quadro", font=font_small, fill=MUTED)
    draw.text((1270, 320), "NATIVO 1×", font=font_micro, fill=NAVY)
    native_background = Image.new("RGBA", (args.frame_width, args.frame_height), (*key_rgb, 255))
    native_background.alpha_composite(selected_image)
    page.paste(native_background.convert("RGB"), (1270, 340))
    draw.rectangle((1270, 340, 1270 + args.frame_width, 340 + args.frame_height), outline=NAVY, width=2)
    map_x, map_y, cell = 950, 445, 28
    occupied_set = {tuple(coord) for coord in selected["occupied_tile_coordinates_xy"]}
    for tile_y in range(args.frame_height // args.tile_size):
        for tile_x in range(args.frame_width // args.tile_size):
            x0 = map_x + tile_x * cell
            y0 = map_y + tile_y * cell
            fill = NAVY if (tile_x, tile_y) in occupied_set else key_rgb
            outline = (242, 242, 233) if (tile_x, tile_y) in occupied_set else (0, 125, 0)
            draw.rectangle((x0, y0, x0 + cell - 1, y0 + cell - 1), fill=fill, outline=outline, width=1)
    metrics_y = map_y + 12 * cell + 30
    draw.text((920, metrics_y), f"{selected['occupied_tile_cells']} ocupados / {slots} células", font=font_body, fill=INK)
    draw.text((920, metrics_y + 40), f"{selected_patterns} padrões únicos no quadro", font=font_body, fill=INK)
    draw.text((920, metrics_y + 80), f"{selected_patterns * 32:,} bytes brutos 4bpp", font=font_body, fill=INK)
    draw.text((920, metrics_y + 126), "contagem por índices; sem dedupe por flip", font=font_micro, fill=MUTED)

    draw.text((1455, 250), "CONTRATO VISUAL DO ASSET", font=font_heading, fill=NAVY)
    draw.text((1455, 291), "Área de arte e geometria; runtime permanece em outro gate", font=font_small, fill=MUTED)

    rounded_card(draw, (1450, 330, 2070, 500), fill=(250, 248, 242), radius=16)
    rounded_card(draw, (2090, 330, 2700, 500), fill=(250, 248, 242), radius=16)
    draw.text((1475, 350), "RESOLUÇÃO E RECORTE", font=font_small, fill=ACCENT)
    draw.text((1475, 385), f"{args.frame_width}×{args.frame_height} px por quadro", font=font_number, fill=NAVY)
    draw.text((1475, 433), f"bbox opaca: {selected_w}×{selected_h} px · inclui equipamento", font=font_micro, fill=INK)
    draw.text((2115, 350), "CONSUMO GRÁFICO MEDIDO", font=font_small, fill=ACCENT)
    draw.text((2115, 385), f"{selected['occupied_tile_cells']} / {slots} tiles ocupados", font=font_number, fill=NAVY)
    draw.text((2115, 433), f"{selected_patterns} padrões · {selected_patterns * 32:,} bytes brutos 4bpp", font=font_micro, fill=INK)

    rounded_card(draw, (1450, 520, 2700, 655), fill=(250, 248, 242), radius=16)
    draw.text((1475, 540), "ESCALA DE TRABALHO", font=font_small, fill=ACCENT)
    draw.text((1475, 575), f"Faixa GDD: {args.target_low}–{args.target_high} px  ·  centro de trabalho: {args.target_center} px", font=font_body, fill=NAVY)
    scale_note = f"Caixa opaca medida: {visible_height}px ({visible_height - args.target_center:+d}px do centro); inclui equipamento; altura do corpo isolada: pendente."
    draw.text((1475, 615), scale_note, font=font_micro, fill=INK)

    rounded_card(draw, (1450, 675, 2700, 1115), fill=(250, 248, 242), radius=16)
    draw.text((1475, 695), f"PALETA INDEXADA · {len(entries)} CORES ÚTEIS + ÍNDICE 0 TRANSPARENTE", font=font_small, fill=ACCENT)
    draw.text((1475, 727), f"RGB 6-bit: {'PASS' if palette_6bit_pass else 'FAIL'}  ·  Alpha binário: {'PASS' if alpha_binary else 'FAIL'}  ·  limite SMS: 15 úteis", font=font_small, fill=INK)
    all_swatches = [{"palette_index": 0, "rgb": list(key_rgb), "hex": key_hex, "transparent": True}] + used_palette
    swatch_x0, swatch_y0 = 1475, 770
    swatch_w, swatch_h = 164, 128
    for i, entry in enumerate(all_swatches):
        row = i // 7
        col = i % 7
        x = swatch_x0 + col * swatch_w
        y = swatch_y0 + row * 152
        rgb = tuple(entry["rgb"])
        draw.rectangle((x, y, x + 56, y + 48), fill=rgb, outline=(67, 67, 75), width=2)
        if entry.get("transparent"):
            draw.line((x, y, x + 56, y + 48), fill=NAVY, width=2)
            draw.line((x + 56, y, x, y + 48), fill=NAVY, width=2)
            draw.text((x + 64, y + 2), "00 α=0", font=font_micro, fill=INK)
            draw.text((x + 64, y + 25), "transparente", font=font_micro, fill=INK)
        else:
            draw.text((x + 64, y + 2), f"{entry['palette_index']:02d} {entry['hex']}", font=font_micro, fill=INK)
            draw.text((x + 64, y + 25), entry["role"], font=font_micro, fill=INK)
    draw.text((1475, 1030), f"Manifesto: {palette_character.get('usable_colors')} cores declaradas · fora desta pose: {', '.join(item['role'] for item in manifest_colors_not_used)}", font=font_micro, fill=MUTED)
    draw.text((1475, 1070), f"Fundo escolhido: {key_name} {key_hex}; máximo contraste médio RGB entre as três chaves; não integra o asset.", font=font_micro, fill=MUTED)

    draw.text((105, 1208), "FOLHA COMPLETA · ORDEM DE LEITURA 4×3", font=font_heading, fill=NAVY)
    draw.text((105, 1245), "Cada quadro mantém canvas nativo 96×96; previews ×2 nearest-neighbor sobre o mesmo fundo de contraste.", font=font_small, fill=MUTED)
    thumb_scale = 2
    thumb_w = args.frame_width * thumb_scale
    thumb_h = args.frame_height * thumb_scale
    thumb_gap_x = 218
    thumb_gap_y = 218
    thumb_start_x = 100
    thumb_start_y = 1305
    for frame in frame_results:
        i = frame["frame_index_zero_based"]
        col = i % args.columns
        row = i // args.columns
        x = thumb_start_x + col * thumb_gap_x
        y = thumb_start_y + row * thumb_gap_y
        fr_x = col * args.frame_width
        fr_y = row * args.frame_height
        thumb = rgba.crop((fr_x, fr_y, fr_x + args.frame_width, fr_y + args.frame_height))
        thumb = thumb.resize((thumb_w, thumb_h), Image.Resampling.NEAREST)
        background = Image.new("RGBA", thumb.size, (*key_rgb, 255))
        background.alpha_composite(thumb)
        page.paste(background.convert("RGB"), (x, y))
        is_selected = i == args.frame_index
        draw.rectangle((x, y, x + thumb_w, y + thumb_h), outline=(255, 190, 0) if is_selected else (25, 36, 69), width=4 if is_selected else 2)
        draw.text((x, y - 22), f"F{i + 1:02d}  ·  {frame['occupied_tile_cells']} tiles", font=font_micro, fill=NAVY)

    notes_x = 1040
    draw.text((notes_x, 1305), "REFERÊNCIA E PROVENIÊNCIA", font=font_heading, fill=NAVY)
    draw_paragraph(
        draw,
        (notes_x, 1350),
        f"Model sheet de escala/identidade: {concept_path.name}.",
        font_body,
        INK,
        1570,
        7,
    )
    draw_paragraph(
        draw,
        (notes_x, 1410),
        f"Fonte pixelada: {source_path.name}; {args.columns}×{args.rows} quadros de {args.frame_width}×{args.frame_height}px.",
        font_body,
        INK,
        1570,
        7,
    )
    draw.text((notes_x, 1500), f"SHA fonte: {sha256(source_path)[:24]}…", font=font_small, fill=MUTED)
    draw.text((notes_x, 1540), f"SHA concept: {sha256(concept_path)[:24]}…", font=font_small, fill=MUTED)
    draw.text((notes_x, 1600), "SEQUÊNCIA COMPLETA · CONTABILIDADE DE PADRÕES", font=font_small, fill=ACCENT)
    draw.text((notes_x, 1640), f"{all_placements} colocações ocupadas · {all_pattern_count} padrões únicos", font=font_body, fill=NAVY)
    draw.text((notes_x, 1680), f"{all_pattern_count * 32:,} bytes brutos se todos os padrões únicos forem representados em 4bpp.", font=font_small, fill=INK)
    draw_paragraph(
        draw,
        (notes_x, 1725),
        "Isto não é orçamento de VRAM nem afirma residência simultânea. Pools, banking, formato das tabelas e carregamento dos quadros ainda precisam de decisão no TDD.",
        font_small,
        ALERT,
        1570,
        5,
    )
    draw.text((notes_x, 1848), "PROMOÇÃO: fora de res/ · sem ROM binding · sem validação em emulador", font=font_small, fill=ALERT)

    draw.line((70, 1980, 2730, 1980), fill=LINE, width=2)
    draw.text((75, 1997), "Dr. Social · prova de arte técnica · inspeção visual e decisão do dono pendentes", font=font_small, fill=MUTED)
    draw.text((2020, 1997), "Fonte: Master of Fighters · SMS", font=font_small, fill=MUTED)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    page.save(output_path, format="PNG", optimize=True)
    report["proof_sheet"]["image_sha256"] = sha256(output_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"proof={output_path}")
    print(f"report={report_path}")
    print(f"selected_frame={args.frame_index + 1}/{frame_count} bbox={selected['bbox_xyxy_exclusive']} visible={selected_w}x{selected_h}")
    print(f"selected_tiles={selected['occupied_tile_cells']}/{slots} unique={selected_patterns} raw4bpp={selected_patterns * 32} bytes")
    print(f"all_frames_placements={all_placements} unique_patterns={all_pattern_count} raw4bpp={all_pattern_count * 32} bytes")
    print(f"palette_useful={len(entries)} indexed={indexed.mode == 'P'} rgb6bit={palette_6bit_pass} alpha_binary={alpha_binary} key={key_hex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
