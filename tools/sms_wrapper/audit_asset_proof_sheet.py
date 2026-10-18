#!/usr/bin/env python3
"""Check key-pose proof crops against indexed source pixels.

The gate verifies exact source-to-board rendering, palette limits, 8x8 tile
inventory, and required animation-principle/hardware declarations. It does not
judge anatomy, concept fidelity, animation quality, or runtime feasibility.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops


KEYS = {
    "magenta": (255, 0, 255),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
}
RGB6 = {0, 85, 170, 255}
PRINCIPLES = {
    "squash_stretch", "anticipation", "staging", "straight_ahead_pose_to_pose",
    "follow_through_overlap", "slow_in_slow_out", "arcs", "secondary_action",
    "timing", "exaggeration", "solid_drawing", "appeal",
}
REQUIRED_POSES = {"idle", "action"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def resolve(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def indexed_palette(image: Image.Image) -> list[tuple[int, int, int]]:
    raw = image.getpalette() or []
    return [tuple(raw[i:i + 3]) for i in range(0, min(len(raw), 768), 3)]


def effective_frame(image: Image.Image, background: tuple[int, int, int], scale: int) -> Image.Image:
    rgba = image.convert("RGBA")
    canvas = Image.new("RGBA", rgba.size, (*background, 255))
    canvas.alpha_composite(rgba)
    return canvas.convert("RGB").resize(
        (image.width * scale, image.height * scale), Image.Resampling.NEAREST
    )


def apply_source_transform(frame: Image.Image, transform: dict) -> Image.Image:
    method = transform.get("method", "identity")
    output_size = tuple(transform.get("output_px", frame.size))
    if method == "identity":
        if output_size != frame.size:
            raise ValueError("identity transform output dimensions differ from parent frame")
        return frame.copy()
    if method != "nearest_neighbor":
        raise ValueError(f"unsupported source transform method: {method}")
    return frame.resize(output_size, Image.Resampling.NEAREST)


def pose_metrics(image: Image.Image, transparent_index: int, tile: int) -> dict:
    if image.mode != "P":
        return {"error": "source pose must be an indexed PNG (mode P)"}
    if image.width % tile or image.height % tile:
        return {"error": "pose dimensions must be divisible by the tile size"}
    pixels = image.load()
    occupied = []
    patterns = set()
    for ty in range(image.height // tile):
        for tx in range(image.width // tile):
            pattern = bytes(
                0 if pixels[tx * tile + dx, ty * tile + dy] == transparent_index
                else pixels[tx * tile + dx, ty * tile + dy]
                for dy in range(tile) for dx in range(tile)
            )
            if any(pattern):
                occupied.append([tx, ty])
                patterns.add(pattern)
    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    edge_clearance = (
        [bbox[0], bbox[1], image.width - bbox[2], image.height - bbox[3]]
        if bbox else [0, 0, 0, 0]
    )
    remaining = {
        (x, y) for y in range(image.height) for x in range(image.width)
        if pixels[x, y] != transparent_index
    }
    component_sizes: list[int] = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            x, y = stack.pop()
            size += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    point = (x + dx, y + dy)
                    if (dx or dy) and point in remaining:
                        remaining.remove(point)
                        stack.append(point)
        component_sizes.append(size)
    return {
        "bbox_xyxy_exclusive": list(bbox) if bbox else None,
        "bbox_px": [bbox[2] - bbox[0], bbox[3] - bbox[1]] if bbox else [0, 0],
        "empty_border_px_left_top_right_bottom": edge_clearance,
        "occupied_tile_cells": len(occupied),
        "unique_tile_patterns": len(patterns),
        "occupied_tile_coordinates_xy": occupied,
        "raw_4bpp_bytes_for_unique_patterns": len(patterns) * 32,
        "opaque_component_count_8_connected": len(component_sizes),
        "opaque_component_sizes_px_desc": sorted(component_sizes, reverse=True),
        "pattern_bytes_for_union": patterns,
    }


def component_errors(role: str, metrics: dict, minimum_component: int) -> list[str]:
    small = sum(
        size < minimum_component
        for size in metrics.get("opaque_component_sizes_px_desc", [])
    )
    if not small:
        return []
    return [
        f"{role}: {small} opaque component(s) below "
        f"the {minimum_component}px cleanup minimum"
    ]


def frame_clearance_errors(role: str, metrics: dict, minimum_border: int) -> list[str]:
    margins = metrics.get("empty_border_px_left_top_right_bottom", [])
    if not isinstance(minimum_border, int) or minimum_border < 1:
        return ["framing_contract.minimum_empty_border_px must be an integer >= 1"]
    if len(margins) != 4:
        return [f"{role}: opaque bounding box missing edge-clearance measurements"]
    names = ("left", "top", "right", "bottom")
    return [
        f"{role}: opaque content leaves {margin}px at {edge} edge; minimum is {minimum_border}px"
        for edge, margin in zip(names, margins) if margin < minimum_border
    ]


def validate(manifest_path: Path, root: Path) -> tuple[list[str], dict]:
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"manifest unreadable: {exc}"], {}

    schema = manifest.get("schema")
    if schema not in {"smsforge.keypose_proof_sheet.v2", "smsforge.keypose_proof_sheet.v3", "smsforge.keypose_proof_sheet.v4"}:
        errors.append("schema must be smsforge.keypose_proof_sheet.v2, .v3, or .v4")
    if schema in {"smsforge.keypose_proof_sheet.v3", "smsforge.keypose_proof_sheet.v4"}:
        framing = manifest.get("framing_contract", {})
        if framing.get("fail_if_opaque_content_touches_canvas_edge") is not True:
            errors.append("v3/v4 must reject opaque content touching the canvas edge")
        if not isinstance(framing.get("minimum_empty_border_px"), int):
            errors.append("v3/v4 framing_contract must declare minimum_empty_border_px")
    refs = manifest.get("references", {})
    resolved_refs = {}
    reference_pairs = [
        ("approved_concept_path", "approved_concept_sha256"),
        ("source_parent_sheet_path", "source_parent_sheet_sha256"),
        ("source_contract_path", "source_contract_sha256"),
        ("palette_manifest_path", "palette_manifest_sha256"),
    ]
    if schema == "smsforge.keypose_proof_sheet.v4":
        reference_pairs.append(("palette_runtime_contract_path", "palette_runtime_contract_sha256"))
    for path_key, sha_key in reference_pairs:
        ref_path = resolve(root, refs.get(path_key, ""))
        if not ref_path.is_file():
            errors.append(f"reference missing: {path_key}")
        elif refs.get(sha_key) != digest(ref_path):
            errors.append(f"reference SHA-256 is stale or incorrect: {path_key}")
        else:
            resolved_refs[path_key] = ref_path
    palette_info = manifest.get("palette", {})
    hardware = manifest.get("sms_hardware", {})
    palette_key = palette_info.get("palette_character_key")
    allowed_rgb: set[tuple[int, int, int]] = set()
    role_by_rgb: dict[tuple[int, int, int], str] = {}
    palette_doc = {}
    palette_path = resolved_refs.get("palette_manifest_path")
    if palette_path:
        try:
            palette_doc = json.loads(palette_path.read_text(encoding="utf-8"))
            character = palette_doc["characters"][palette_key]
            role_by_rgb = {tuple(color["rgb"]): color["role"] for color in character.get("colors", [])}
            allowed_rgb = set(role_by_rgb)
        except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
            errors.append(f"palette manifest/character is invalid: {exc}")
    else:
        errors.append("palette manifest reference is required")
    if schema == "smsforge.keypose_proof_sheet.v4":
        runtime_path = resolved_refs.get("palette_runtime_contract_path")
        runtime_contract = {}
        if runtime_path:
            try:
                runtime_contract = json.loads(runtime_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, TypeError) as exc:
                errors.append(f"palette runtime contract is invalid: {exc}")
        if runtime_contract.get("schema") != "mof_sms_runtime_palette_contract_v1":
            errors.append("v4 requires mof_sms_runtime_palette_contract_v1")
        runtime_policy = runtime_contract.get("runtime_assignment", {}).get("fight", {})
        bg_table = runtime_policy.get("bg_table", {})
        sprite_table = runtime_policy.get("sprite_table", {})
        if bg_table.get("id") != "P0" or bg_table.get("users") != ["stage_background", "hud"]:
            errors.append("v4 runtime palette must assign P0 to stage background and HUD")
        if sprite_table.get("id") != "P1" or sprite_table.get("per_character_cram_table") is not False:
            errors.append("v4 runtime palette must use one shared P1 table, not per-character CRAM tables")
        if sprite_table.get("mapping_status") != "pending_roster_wide_mapping_to_15_useful_colors":
            errors.append("v4 must keep roster-wide P1 color mapping pending until the shared palette is locked")
        runtime_ref = refs.get("palette_runtime_contract_path")
        if palette_info.get("runtime_palette_policy_ref") != runtime_ref:
            errors.append("v4 palette.runtime_palette_policy_ref must match the hash-bound runtime contract")
        if palette_info.get("source_palette_scope") != "character color study only; not a standalone runtime CRAM allocation":
            errors.append("v4 must label the character palette as a source study, not a runtime allocation")
        if palette_info.get("runtime_sprite_palette_assignment") != "one shared sprite CRAM table for the complete active roster and effects":
            errors.append("v4 must state that all fighters/effects share the sprite CRAM table")
        if palette_info.get("runtime_sprite_palette_mapping_status") != sprite_table.get("mapping_status"):
            errors.append("v4 proof and palette runtime contract disagree on roster palette mapping status")
        source_useful_colors = palette_info.get("useful_colors_in_parent_sheet")
        if (palette_info.get("useful_color_limit_per_sprite_subpalette") != 15
                or not isinstance(source_useful_colors, int)
                or source_useful_colors > 15):
            errors.append("v4 source palette must respect the 15-useful-color per-sprite-table ceiling")
        cram_assignment = hardware.get("cram_assignment", {})
        bg_assignment = cram_assignment.get("background_palette")
        if not isinstance(bg_assignment, str) or not bg_assignment.startswith("P0;"):
            errors.append("v4 must assign BG and HUD to palette P0")
        sprite_assignment = cram_assignment.get("sprite_palette")
        if not isinstance(sprite_assignment, str) or not sprite_assignment.startswith("P1;"):
            errors.append("v4 must assign every sprite to the shared palette P1")
        if cram_assignment.get("sprite_palette_index_0") != "transparent for sprite pixels":
            errors.append("v4 must identify sprite P1 index 0 as transparent")
        if cram_assignment.get("background_tiles_may_select_sprite_palette") is not True:
            errors.append("v4 must record the SMS background tile palette-select capability")
        if cram_assignment.get("background_palette_select_define") != "TILE_USE_SPRITE_PALETTE":
            errors.append("v4 must cite the devkitSMS tile palette-select define")
        contract_hardware = runtime_contract.get("hardware", {})
        if (contract_hardware.get("palette_tables") != 2
                or contract_hardware.get("entries_per_table") != 16
                or contract_hardware.get("sprite_index_0") != "transparent for sprite pixels"
                or contract_hardware.get("background_index_0") != "visible backdrop color; not alpha"
                or contract_hardware.get("background_color_index_0") != "visible color for BG pixels in the selected table; BG pixels never become transparent because their color index is zero"
                or contract_hardware.get("background_tile_palette_define") != "TILE_USE_SPRITE_PALETTE"):
            errors.append("v4 runtime contract has an incorrect or incomplete SMS CRAM model")
        roster_rows = palette_doc.get("characters", {}) if isinstance(palette_doc, dict) else {}
        roster_rgb = {
            tuple(color.get("rgb", []))
            for character in roster_rows.values()
            for color in character.get("colors", [])
            if isinstance(color, dict) and color.get("index") != 0
        }
        if palette_info.get("roster_palette_source_manifest_count") != len(roster_rows):
            errors.append("v4 roster palette profile count does not match palettes_manifest.json")
        if palette_info.get("roster_distinct_source_rgb_count") != len(roster_rgb):
            errors.append("v4 distinct source RGB count does not match palettes_manifest.json")
        source_summary = runtime_contract.get("authoring_palette_manifests", {})
        if source_summary.get("profiles_count") != len(roster_rows) or source_summary.get("distinct_nontransparent_rgb_count") != len(roster_rgb):
            errors.append("palette runtime contract source-color summary is stale")
        terminal_review = manifest.get("review", {}).get("equipment_terminal_shape", {})
        if (terminal_review.get("status") not in {"pending", "pass", "fail"}
                or not terminal_review.get("expected_identity")
                or not terminal_review.get("evidence")):
            errors.append("v4 requires an explicit human review axis for equipment terminal shape and identity")
        height_review = manifest.get("review", {}).get("standing_body_height_vs_gdd", {})
        height_scope = height_review.get("measurement_scope")
        if (height_review.get("status") not in {"pending", "pass", "fail"}
                or not isinstance(height_scope, str)
                or "excluding handheld" not in height_scope
                or not height_review.get("expected_range_px")
                or not height_review.get("evidence")):
            errors.append("v4 requires standing anatomy height measured separately from handheld equipment")
    source_contract_path = resolved_refs.get("source_contract_path")
    cleanup_profile = {}
    if source_contract_path:
        try:
            source_contract = json.loads(source_contract_path.read_text(encoding="utf-8"))
            cleanup_profile = source_contract.get("pixel_cleanup_profile", {})
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            errors.append(f"source contract is invalid: {exc}")
    minimum_component = cleanup_profile.get("minimum_opaque_component_px")
    if not isinstance(minimum_component, int) or minimum_component < 1:
        errors.append("source contract must declare minimum_opaque_component_px >= 1")
        minimum_component = 1
    if cleanup_profile.get("connectivity") != 8:
        errors.append("source contract component check must declare 8-connectivity")
    if cleanup_profile.get("mode") not in {"components_only", "materials_and_components"}:
        errors.append("source contract must declare a supported pixel_cleanup_profile.mode")
    if (cleanup_profile.get("mode") == "components_only"
            and cleanup_profile.get("material_regions_status") != "pending"):
        errors.append("components_only must keep material_regions_status=pending")
    poses = manifest.get("poses")
    if not isinstance(poses, list) or len(poses) != 2:
        errors.append("proof sheet must contain exactly two key poses: idle and action")
        poses = poses if isinstance(poses, list) else []
    if {p.get("role") for p in poses if isinstance(p, dict)} != REQUIRED_POSES:
        errors.append("pose roles must be exactly idle and action")

    hardware = manifest.get("sms_hardware", {})
    expected_hardware = {
        "visible_canvas_px": [256, 192],
        "vram_bytes": 16384,
        "pattern_px": [8, 8],
        "pattern_bytes_4bpp": 32,
        "pattern_slots_total": 512,
        "sprite_pattern_window_slots": 256,
        "sat_entries_max": 64,
        "sprites_per_scanline_max": 8,
        "sprite_width_px": 8,
        "sprite_height_options_px": [8, 16],
        "cram_subpalettes": 2,
        "cram_entries_per_subpalette": 16,
        "transparent_index": 0,
        "useful_colors_per_subpalette_max": 15,
        "useful_colors_simultaneous_max": 30,
        "ram_bytes": 8192,
        "rom_no_mapper_bytes": 49152,
        "dma": False,
    }
    for key, value in expected_hardware.items():
        if hardware.get(key) != value:
            errors.append(f"SMS hardware declaration {key} must be {value!r}")
    if hardware.get("max_frames_per_sprite_sheet") is not None:
        errors.append("frame count per sheet is not a fixed SMS hardware constant; use null")
    if hardware.get("frame_count_policy") != "project_runtime_budget_required":
        errors.append("frame_count_policy must defer to a measured project runtime budget")

    animation = manifest.get("animation_principles")
    if not isinstance(animation, list):
        animation = []
    principle_ids = {item.get("id") for item in animation if isinstance(item, dict)}
    if principle_ids != PRINCIPLES or len(animation) != 12:
        errors.append("all 12 Disney animation principles must be declared exactly once")
    for item in animation:
        if not isinstance(item, dict):
            continue
        if item.get("status") not in {"pass", "fail", "pending", "not_applicable"}:
            errors.append(f"invalid animation principle status: {item.get('id')}")
        if not item.get("evidence"):
            errors.append(f"animation principle lacks evidence note: {item.get('id')}")

    runtime = manifest.get("runtime_budget", {})
    for key in ("vram_residency", "sat_and_scanline", "vblank_upload", "rom_banking", "sheet_frame_count"):
        if runtime.get(key) not in {"pending", "pass", "fail"}:
            errors.append(f"runtime_budget.{key} must be explicitly pending/pass/fail")

    board_path = resolve(root, manifest.get("proof_image", {}).get("path", ""))
    board_sha = manifest.get("proof_image", {}).get("sha256")
    if not board_path.is_file():
        errors.append(f"proof board missing: {board_path}")
        return errors, manifest
    if board_sha != digest(board_path):
        errors.append("proof board SHA-256 is stale or incorrect")
    try:
        board = Image.open(board_path).convert("RGB")
    except OSError as exc:
        errors.append(f"proof board cannot be decoded: {exc}")
        return errors, manifest
    if manifest.get("proof_image", {}).get("dimensions_px") != list(board.size):
        errors.append("proof_image dimensions are stale or incorrect")
    overlay_policy = manifest.get("proof_image", {}).get("overlay_policy", "")
    if "no line" not in overlay_policy or "intersects" not in overlay_policy:
        errors.append("proof image must declare that annotations do not intersect source previews")

    all_patterns = set()
    measured = []
    source_hashes = set()
    inspection_keys = set()
    for pose in poses:
        if not isinstance(pose, dict):
            continue
        role = pose.get("role", "unknown")
        source_path = resolve(root, pose.get("source_path", ""))
        if not source_path.is_file():
            errors.append(f"{role}: source pose missing: {source_path}")
            continue
        source_sha = digest(source_path)
        source_hashes.add(source_sha)
        if pose.get("source_sha256") != source_sha:
            errors.append(f"{role}: source pose SHA-256 is stale or incorrect")
        try:
            source = Image.open(source_path)
            if source.mode != "P":
                errors.append(f"{role}: source must remain indexed mode P")
                continue
            if source.size != tuple(pose.get("canvas_px", [])):
                errors.append(f"{role}: source canvas differs from manifest")
                continue
            parent_raw = pose.get("source_parent_sheet")
            parent_path = resolve(root, parent_raw) if isinstance(parent_raw, str) else root
            parent_grid = pose.get("source_parent_grid", {})
            parent_cols, parent_rows = parent_grid.get("columns"), parent_grid.get("rows")
            parent_frame = parent_grid.get("frame_px")
            parent_index = pose.get("source_frame_index_zero_based")
            transform = pose.get("source_transform") or {
                "method": "identity",
                "scale_ratio_numerator_denominator": [1, 1],
                "input_px": list(source.size),
                "output_px": list(source.size),
            }
            method = transform.get("method")
            ratio = transform.get("scale_ratio_numerator_denominator")
            transform_input = transform.get("input_px")
            transform_output = transform.get("output_px")
            if not parent_path.is_file():
                errors.append(f"{role}: parent source sheet missing")
            elif pose.get("source_parent_sha256") != digest(parent_path):
                errors.append(f"{role}: parent source sheet SHA-256 is stale or incorrect")
            elif (not isinstance(parent_cols, int) or not isinstance(parent_rows, int)
                  or not isinstance(parent_frame, list) or len(parent_frame) != 2
                  or not isinstance(transform_input, list) or transform_input != parent_frame
                  or not isinstance(transform_output, list) or transform_output != list(source.size)
                  or not isinstance(ratio, list) or len(ratio) != 2
                  or not all(isinstance(value, int) and value > 0 for value in ratio)
                  or not isinstance(parent_index, int)
                  or not 0 <= parent_index < parent_cols * parent_rows):
                errors.append(f"{role}: parent frame grid/index declaration is invalid")
            else:
                numerator, denominator = ratio
                expected_size = [
                    parent_frame[0] * numerator // denominator,
                    parent_frame[1] * numerator // denominator,
                ]
                exact_dimensions = (
                    parent_frame[0] * numerator % denominator == 0
                    and parent_frame[1] * numerator % denominator == 0
                )
                if (method not in {"identity", "nearest_neighbor"}
                        or not exact_dimensions or expected_size != list(source.size)
                        or (method == "identity" and ratio != [1, 1])
                        or (method == "nearest_neighbor" and transform.get("resampling")
                            not in {None, "Pillow Image.Resampling.NEAREST"})):
                    errors.append(f"{role}: source transform is not a uniform, reproducible nearest-neighbor mapping")
                parent = Image.open(parent_path)
                if parent.mode != "P" or parent.size != (parent_cols * parent_frame[0], parent_rows * parent_frame[1]):
                    errors.append(f"{role}: parent indexed sheet dimensions disagree with its declared grid")
                else:
                    px, py = parent_index % parent_cols, parent_index // parent_cols
                    source_frame = parent.crop((px * parent_frame[0], py * parent_frame[1],
                                                (px + 1) * parent_frame[0], (py + 1) * parent_frame[1]))
                    try:
                        expected_pose = apply_source_transform(source_frame, transform)
                    except (ValueError, TypeError) as exc:
                        errors.append(f"{role}: source transform invalid: {exc}")
                        expected_pose = source_frame
                    if expected_pose.tobytes() != source.tobytes() or expected_pose.getpalette() != source.getpalette():
                        errors.append(f"{role}: converted pose pixels/palette differ from declared parent frame transform")
                    if parent.info.get("transparency", 0) != source.info.get("transparency", 0):
                        errors.append(f"{role}: extracted pose transparency differs from parent source")
            if schema in {"smsforge.keypose_proof_sheet.v3", "smsforge.keypose_proof_sheet.v4"} and not pose.get("source_transform"):
                errors.append(f"{role}: v3/v4 pose requires an explicit source_transform")
            transparent = pose.get("transparent_index")
            info_transparent = source.info.get("transparency", 0)
            if transparent != 0 or info_transparent != transparent:
                errors.append(f"{role}: palette index 0 must be the PNG transparent index")
            palette = indexed_palette(source)
            used = set(source.get_flattened_data()) - {transparent}
            if len(used) > 15:
                errors.append(f"{role}: {len(used)} useful colors exceed the 15-color SMS sprite palette")
            used_rgb = [palette[i] for i in used if i < len(palette)]
            if any(channel not in RGB6 for color in used_rgb for channel in color):
                errors.append(f"{role}: RGB channel outside the 6-bit master grid")
            if allowed_rgb and not set(used_rgb) <= allowed_rgb:
                invalid = sorted(set(used_rgb) - allowed_rgb)
                errors.append(f"{role}: RGB values outside the character palette manifest: {invalid}")
            key_rgb = tuple(pose.get("inspection_background_rgb", []))
            inspection_keys.add(key_rgb)
            if key_rgb not in KEYS.values():
                errors.append(f"{role}: inspection background must be pure magenta, green, or blue")
            if key_rgb in used_rgb:
                errors.append(f"{role}: inspection background collides with an opaque asset color")
            alpha_values = set(source.convert("RGBA").getchannel("A").get_flattened_data())
            if alpha_values - {0, 255}:
                errors.append(f"{role}: alpha must be binary; antialiased edges are forbidden")
            metrics = pose_metrics(source, transparent, 8)
            if "error" in metrics:
                errors.append(f"{role}: {metrics['error']}")
                continue
            if schema in {"smsforge.keypose_proof_sheet.v3", "smsforge.keypose_proof_sheet.v4"}:
                errors.extend(frame_clearance_errors(
                    role, metrics, manifest.get("framing_contract", {}).get("minimum_empty_border_px")
                ))
            errors.extend(component_errors(role, metrics, minimum_component))
            patterns = metrics.pop("pattern_bytes_for_union")
            all_patterns.update(patterns)

            render = pose.get("sprite_preview", {})
            scale = render.get("scale")
            x, y = render.get("x"), render.get("y")
            if not isinstance(scale, int) or scale < 1 or not isinstance(x, int) or not isinstance(y, int):
                errors.append(f"{role}: sprite preview needs integer x/y/scale")
                continue
            expected = effective_frame(source, key_rgb, scale)
            actual = board.crop((x, y, x + expected.width, y + expected.height))
            if actual.size != expected.size or ImageChops.difference(actual, expected).getbbox():
                errors.append(f"{role}: preview pixels differ from source; overlay, resampling, or contamination detected")

            native = pose.get("native_preview", {})
            nx, ny = native.get("x"), native.get("y")
            if not isinstance(nx, int) or not isinstance(ny, int):
                errors.append(f"{role}: native 1x preview needs integer x/y")
            else:
                expected_native = effective_frame(source, key_rgb, 1)
                actual_native = board.crop((nx, ny, nx + source.width, ny + source.height))
                if actual_native.size != expected_native.size or ImageChops.difference(actual_native, expected_native).getbbox():
                    errors.append(f"{role}: native 1x preview differs from source pixels")
            metrics["role"] = role
            metrics["source_sha256"] = source_sha
            measured.append(metrics)
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"{role}: source validation failed: {exc}")

    if len(source_hashes) != 2:
        errors.append("idle/action source pose images must be distinct files/content")
    if len(inspection_keys) != 1:
        errors.append("both poses of the same character must use the same inspection background")
    palette_parent = resolved_refs.get("source_parent_sheet_path")
    if palette_parent and palette_parent.is_file():
        parent = Image.open(palette_parent)
        if parent.mode != "P":
            errors.append("parent source sheet must remain indexed mode P")
        else:
            transparent = manifest.get("sms_hardware", {}).get("transparent_index", 0)
            parent_used = set(parent.get_flattened_data()) - {transparent}
            if palette_info.get("useful_colors_in_parent_sheet") != len(parent_used):
                errors.append("palette useful-color count does not match the parent indexed PNG")
            declared_entries = {
                entry.get("index"): (tuple(entry.get("rgb", [])), entry.get("role"))
                for entry in palette_info.get("used_palette_indices_and_rgb", [])
                if isinstance(entry, dict)
            }
            parent_palette = indexed_palette(parent)
            for index in parent_used:
                actual_rgb = parent_palette[index] if index < len(parent_palette) else None
                if declared_entries.get(index) != (actual_rgb, role_by_rgb.get(actual_rgb)):
                    errors.append(f"palette entry {index} does not match source RGB/role")
    if palette_info.get("sms_rgb6_grid_pass") is not True:
        errors.append("palette must declare an SMS RGB 6-bit grid pass")
    if palette_info.get("alpha_binary_pass") is not True:
        errors.append("palette must declare a binary-alpha pass")
    manifest_metrics = manifest.get("measured", {})
    expected_poses = {row["role"]: row for row in measured}
    for role, row in expected_poses.items():
        declared = manifest_metrics.get("poses", {}).get(role, {})
        for key in ("bbox_xyxy_exclusive", "bbox_px", "empty_border_px_left_top_right_bottom", "occupied_tile_cells", "unique_tile_patterns", "raw_4bpp_bytes_for_unique_patterns", "opaque_component_count_8_connected", "opaque_component_sizes_px_desc"):
            if declared.get(key) != row.get(key):
                errors.append(f"{role}: stale or incorrect measured.{key}")
    if manifest_metrics.get("selected_pair_unique_patterns") != len(all_patterns):
        errors.append("selected_pair_unique_patterns does not match indexed source patterns")
    component_review = manifest.get("review", {}).get("component_integrity_gate", {})
    expected_small_components = sum(
        sum(size < minimum_component for size in row.get("opaque_component_sizes_px_desc", []))
        for row in expected_poses.values()
    )
    if component_review.get("mode") != cleanup_profile.get("mode"):
        errors.append("review.component_integrity_gate.mode differs from the source contract")
    if component_review.get("minimum_opaque_component_px") != minimum_component:
        errors.append("review.component_integrity_gate minimum differs from the source contract")
    if component_review.get("poses_with_island_below_minimum") != expected_small_components:
        errors.append("review.component_integrity_gate island count is stale or incorrect")
    if component_review.get("material_regions_status") != cleanup_profile.get("material_regions_status"):
        errors.append("review.component_integrity_gate material status differs from the source contract")

    promotion = manifest.get("promotion", {})
    if promotion.get("approved_for_res") is not False:
        errors.append("proof candidate must remain unapproved for res until all review/runtime gates pass")
    if promotion.get("aaa_claim") not in {False, None}:
        errors.append("technical proof must not claim automatic AAA certification")
    return errors, manifest


def self_check() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="sms_asset_proof_") as tmp:
        root = Path(tmp)
        palette = [0, 0, 0, 0, 0, 85, 0, 170, 255]
        palette += [0] * (768 - len(palette))
        sources = []
        poses = []
        board = Image.new("RGB", (100, 50), (245, 242, 234))
        original_frames = []
        for i, role in enumerate(("idle", "action")):
            original = Image.new("P", (16, 16), 0)
            original.putpalette(palette)
            original.info["transparency"] = 0
            original.putpixel((3 + i * 2, 5), 1)
            original.putpixel((5 + i * 2, 5), 2)
            original_frames.append(original)
            transform = {
                "method": "nearest_neighbor",
                "scale_ratio_numerator_denominator": [1, 2],
                "input_px": [16, 16],
                "output_px": [8, 8],
                "resampling": "Pillow Image.Resampling.NEAREST",
            }
            pose = apply_source_transform(original, transform)
            pose.info["transparency"] = 0
            source_path = root / f"{role}.png"
            pose.save(source_path, transparency=0)
            sources.append(source_path)
            bg = (0, 255, 0)
            expected = effective_frame(pose, bg, 2)
            x = 4 + i * 48
            y = 4
            board.paste(expected, (x, y))
            board.paste(effective_frame(pose, bg, 1), (x, 28))
            poses.append({
                "role": role,
                "source_path": source_path.name,
                "source_sha256": digest(source_path),
                "source_parent_sheet": "parent.png",
                "source_parent_sha256": None,
                "source_frame_index_zero_based": i,
                "source_parent_grid": {"columns": 2, "rows": 1, "frame_px": [16, 16]},
                "source_transform": transform,
                "canvas_px": [8, 8],
                "transparent_index": 0,
                "inspection_background_rgb": list(bg),
                "sprite_preview": {"x": x, "y": y, "scale": 2},
                "native_preview": {"x": x, "y": 28},
            })
        parent = Image.new("P", (32, 16), 0)
        parent.putpalette(palette)
        parent.info["transparency"] = 0
        parent.paste(original_frames[0], (0, 0))
        parent.paste(original_frames[1], (16, 0))
        parent_path = root / "parent.png"
        parent.save(parent_path, transparency=0)
        for pose in poses:
            pose["source_parent_sha256"] = digest(parent_path)

        board_path = root / "board.png"
        board.save(board_path)
        pair_union = set()
        for pose in poses:
            metrics = pose_metrics(Image.open(root / pose["source_path"]), 0, 8)
            pair_union.update(metrics.pop("pattern_bytes_for_union"))
        report = {
            "schema": "smsforge.keypose_proof_sheet.v3",
            "framing_contract": {
                "minimum_empty_border_px": 1,
                "fail_if_opaque_content_touches_canvas_edge": True,
            },
            "references": {
                "approved_concept_path": "concept.png",
                "approved_concept_sha256": None,
                "source_parent_sheet_path": "parent.png",
                "source_parent_sheet_sha256": None,
                "source_contract_path": "source_contract.json",
                "source_contract_sha256": None,
                "palette_manifest_path": "palette.json",
                "palette_manifest_sha256": None,
            },
            "palette": {
                "palette_character_key": "demo",
                "useful_colors_in_parent_sheet": 2,
                "used_palette_indices_and_rgb": [
                    {"index": 1, "rgb": [0, 0, 85], "role": "outline"},
                    {"index": 2, "rgb": [0, 170, 255], "role": "accent"},
                ],
                "sms_rgb6_grid_pass": True,
                "alpha_binary_pass": True,
            },
            "poses": poses,
            "sms_hardware": {
                "visible_canvas_px": [256, 192], "vram_bytes": 16384,
                "pattern_px": [8, 8], "pattern_bytes_4bpp": 32,
                "pattern_slots_total": 512, "sprite_pattern_window_slots": 256,
                "sat_entries_max": 64, "sprites_per_scanline_max": 8,
                "sprite_width_px": 8, "sprite_height_options_px": [8, 16],
                "cram_subpalettes": 2, "cram_entries_per_subpalette": 16,
                "transparent_index": 0, "useful_colors_per_subpalette_max": 15,
                "useful_colors_simultaneous_max": 30, "ram_bytes": 8192,
                "rom_no_mapper_bytes": 49152, "dma": False,
                "max_frames_per_sprite_sheet": None,
                "frame_count_policy": "project_runtime_budget_required",
            },
            "animation_principles": [
                {"id": name, "status": "pending", "evidence": "static key-pose fixture"}
                for name in sorted(PRINCIPLES)
            ],
            "runtime_budget": {key: "pending" for key in ("vram_residency", "sat_and_scanline", "vblank_upload", "rom_banking", "sheet_frame_count")},
            "review": {
                "component_integrity_gate": {
                    "mode": "components_only",
                    "minimum_opaque_component_px": 2,
                    "poses_with_island_below_minimum": 0,
                    "material_regions_status": "pending",
                    "tool": "audit_sprite_cutout.py",
                }
            },
            "proof_image": {
                "path": board_path.name,
                "sha256": digest(board_path),
                "dimensions_px": list(board.size),
                "overlay_policy": "no line, grid, label, or annotation intersects source previews",
            },
            "measured": {"poses": {}, "selected_pair_unique_patterns": len(pair_union)},
            "promotion": {"approved_for_res": False, "aaa_claim": False},
        }
        for pose in poses:
            image = Image.open(root / pose["source_path"])
            metrics = pose_metrics(image, 0, 8)
            metrics.pop("pattern_bytes_for_union")
            report["measured"]["poses"][pose["role"]] = metrics
        palette_doc = {
            "characters": {
                "demo": {
                    "colors": [
                        {"index": 1, "rgb": [0, 0, 85], "role": "outline"},
                        {"index": 2, "rgb": [0, 170, 255], "role": "accent"},
                    ]
                }
            }
        }
        source_contract = {
            "pixel_cleanup_profile": {
                "mode": "components_only",
                "minimum_opaque_component_px": 2,
                "connectivity": 8,
                "material_regions_status": "pending",
                "regions": [],
            }
        }
        for name, content in (("concept.png", b"concept"),):
            (root / name).write_bytes(content)
        (root / "source_contract.json").write_text(json.dumps(source_contract), encoding="utf-8")
        (root / "palette.json").write_text(json.dumps(palette_doc), encoding="utf-8")
        report["references"]["approved_concept_sha256"] = digest(root / "concept.png")
        report["references"]["source_parent_sheet_sha256"] = digest(parent_path)
        report["references"]["source_contract_sha256"] = digest(root / "source_contract.json")
        report["references"]["palette_manifest_sha256"] = digest(root / "palette.json")
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(report), encoding="utf-8")
        errors, _ = validate(manifest_path, root)
        assert not errors, f"clean fixture rejected: {errors}"

        # Exercise the v4 CRAM and semantic-terminal branch independently of
        # the general source-pixel fixture so the production path cannot go
        # untested when the base fixture remains v3.
        report_v4 = json.loads(json.dumps(report))
        report_v4["schema"] = "smsforge.keypose_proof_sheet.v4"
        runtime_contract = {
            "schema": "mof_sms_runtime_palette_contract_v1",
            "hardware": {
                "palette_tables": 2,
                "entries_per_table": 16,
                "sprite_index_0": "transparent for sprite pixels",
                "background_index_0": "visible backdrop color; not alpha",
                "background_color_index_0": "visible color for BG pixels in the selected table; BG pixels never become transparent because their color index is zero",
                "background_tile_palette_define": "TILE_USE_SPRITE_PALETTE",
            },
            "runtime_assignment": {"fight": {
                "bg_table": {"id": "P0", "users": ["stage_background", "hud"]},
                "sprite_table": {
                    "id": "P1",
                    "per_character_cram_table": False,
                    "mapping_status": "pending_roster_wide_mapping_to_15_useful_colors",
                },
            }},
            "authoring_palette_manifests": {
                "profiles_count": 1,
                "distinct_nontransparent_rgb_count": 2,
            },
        }
        runtime_path = root / "runtime_palette.json"
        runtime_path.write_text(json.dumps(runtime_contract), encoding="utf-8")
        report_v4["references"]["palette_runtime_contract_path"] = runtime_path.name
        report_v4["references"]["palette_runtime_contract_sha256"] = digest(runtime_path)
        report_v4["palette"].update({
            "useful_color_limit_per_sprite_subpalette": 15,
            "source_palette_scope": "character color study only; not a standalone runtime CRAM allocation",
            "runtime_palette_policy_ref": runtime_path.name,
            "runtime_sprite_palette_assignment": "one shared sprite CRAM table for the complete active roster and effects",
            "runtime_sprite_palette_mapping_status": "pending_roster_wide_mapping_to_15_useful_colors",
            "roster_palette_source_manifest_count": 1,
            "roster_distinct_source_rgb_count": 2,
        })
        report_v4["sms_hardware"]["cram_assignment"] = {
            "background_palette": "P0; stage and HUD; entry 0 reserved as visible backdrop color",
            "sprite_palette": "P1; one shared palette for all hardware sprites",
            "sprite_palette_index_0": "transparent for sprite pixels",
            "background_tiles_may_select_sprite_palette": True,
            "background_palette_select_define": "TILE_USE_SPRITE_PALETTE",
        }
        report_v4["review"]["equipment_terminal_shape"] = {
            "status": "pending",
            "expected_identity": "rounded cane terminal",
            "evidence": "native and nearest-neighbor inspection against the concept",
        }
        report_v4["review"]["standing_body_height_vs_gdd"] = {
            "status": "pending",
            "measurement_scope": "measure crown-to-sole anatomy excluding handheld cane/equipment",
            "expected_range_px": [66, 72],
            "evidence": "compare upright pose in native and nearest-neighbor views against GDD range",
        }
        manifest_v4_path = root / "manifest_v4.json"
        manifest_v4_path.write_text(json.dumps(report_v4), encoding="utf-8")
        errors, _ = validate(manifest_v4_path, root)
        assert not errors, f"valid v4 palette/terminal fixture rejected: {errors}"
        runtime_contract["runtime_assignment"]["fight"]["sprite_table"]["per_character_cram_table"] = True
        runtime_path.write_text(json.dumps(runtime_contract), encoding="utf-8")
        report_v4["references"]["palette_runtime_contract_sha256"] = digest(runtime_path)
        manifest_v4_path.write_text(json.dumps(report_v4), encoding="utf-8")
        errors, _ = validate(manifest_v4_path, root)
        assert any("one shared P1 table" in error for error in errors), \
            "v4 did not reject a per-character runtime sprite palette"

        assert frame_clearance_errors("fixture", {"empty_border_px_left_top_right_bottom": [0, 2, 2, 2]}, 1), \
            "opaque art on the canvas edge was not rejected"
        isolated = Image.open(root / "idle.png")
        isolated.putpixel((7, 7), 1)
        isolated_metrics = pose_metrics(isolated, 0, 8)
        assert min(isolated_metrics["opaque_component_sizes_px_desc"]) == 1, \
            "isolated source pixel was not identified as its own component"
        assert component_errors("idle", isolated_metrics, 2), \
            "isolated source pixel was not rejected below the cleanup minimum"
        board = Image.open(board_path).convert("RGB")
        board.putpixel((4, 4), (0, 0, 0))
        board.save(board_path)
        report["proof_image"]["sha256"] = digest(board_path)
        manifest_path.write_text(json.dumps(report), encoding="utf-8")
        errors, _ = validate(manifest_path, root)
        assert any("preview pixels differ" in error for error in errors), "overlay fixture was not rejected"
    print("[SELF-CHECK OK] deterministic transforms, v4 shared-CRAM/terminal coverage, edge clearance, isolated-pixel rejection, and overlay rejection pass")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", help="Versioned key-pose proof manifest")
    parser.add_argument("--project-root", help="Project root used to resolve manifest paths")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        try:
            return self_check()
        except (AssertionError, OSError, ValueError, TypeError) as exc:
            print(f"[SELF-CHECK FAIL] {exc}", file=sys.stderr)
            return 1
    if not args.manifest or not args.project_root:
        parser.error("--manifest and --project-root are required")
    errors, manifest = validate(Path(args.manifest), Path(args.project_root).resolve())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] source-exact two-key-pose proof, palette, hardware declarations, and animation-principle coverage")
    if manifest.get("review", {}).get("component_integrity_gate", {}).get("material_regions_status") == "pending":
        print("[PENDING] component scan passed; material-region color audit remains pending")
    print("[PENDING] human art review and project runtime budgets remain separate promotion gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
