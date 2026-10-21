#!/usr/bin/env python3
"""Refine the 61-pose Dr. Social sprite candidate without redrawing poses.

This is a deterministic indexed-pixel cleanup stage. It only uses the current
candidate and the already recorded conversion report. The approved v4 concept
sheet remains the sole identity/design reference; this output is still a
candidate and requires independent visual review and owner approval.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parents[1]
ART = PROJECT / "data/source_art/sprite_studies/dr_social"
V4_DIR = ART / "review_drafts/basic_sequences_61f_candidate_v4_source"
V5_DIR = ART / "review_drafts/basic_sequences_61f_candidate_v5_source"
INPUT = V4_DIR / "dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v4.png"
INPUT_REPORT = V4_DIR / "dr_social_basic_sequences_candidate_v4_processing_report.json"
OUTPUT = ART / "dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v5.png"
REPORT = V5_DIR / "dr_social_basic_sequences_candidate_v5_processing_report.json"
PREVIEW = V5_DIR / "dr_social_basic_sequences_candidate_v5_preview_4x.png"

CELL = 80
COLS = 8
ROWS = 9
EXPECTED = [4, 8, 8, 8, 5, 8, 8, 8, 4]
TRANSPARENT_RGB = (255, 0, 255)
KERNEL = np.ones((3, 3), dtype=np.uint8)

# Compact, hardware-oriented palette: effect red is deliberately absent.
# Index 0 is transparent; 1..12 are the approved character palette roles.
ROLE_RGB = [
    TRANSPARENT_RGB,
    (0, 0, 85),       # outline
    (255, 170, 170),  # skin_light
    (170, 85, 85),    # skin_mid
    (85, 170, 255),   # suit_light
    (0, 170, 170),    # suit_mid
    (0, 85, 85),      # suit_deep
    (255, 255, 255),  # shirt/glove light
    (170, 170, 170),  # shirt/glove shadow
    (85, 85, 85),     # hair_gray
    (85, 0, 0),       # boot_brown
    (170, 0, 85),     # tie_burgundy
    (255, 255, 0),    # brass_glasses / cane pommel
]
ROLE_NAMES = [
    "transparent", "outline", "skin_light", "skin_mid", "suit_light",
    "suit_mid", "suit_deep", "shirt_light", "shirt_shadow", "hair_gray",
    "boot_brown", "tie_burgundy", "brass_glasses",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mode(values: np.ndarray, old: int | None = None) -> int:
    counts = Counter(int(v) for v in values)
    if not counts:
        return 1
    luma = {4: 148, 5: 101, 6: 51}
    return min(
        counts,
        key=lambda v: (
            -counts[v],
            abs(luma.get(v, 0) - luma.get(old, 0)) if old is not None else 0,
            v,
        ),
    )


def recolor_accent_red(frame: np.ndarray) -> int:
    """Replace effect-only red with the neighboring actual material role."""
    original = frame.copy()
    ys, xs = np.where(original == 12)  # v4 index 12 = reserved bright red
    for y, x in zip(ys.tolist(), xs.tolist()):
        y0, y1 = max(0, y - 1), min(CELL, y + 2)
        x0, x1 = max(0, x - 1), min(CELL, x + 2)
        neighbors = original[y0:y1, x0:x1].ravel()
        neighbors = neighbors[~np.isin(neighbors, [0, 12, 13])]
        # Original index 13 is brass; output index 12 is brass.
        if neighbors.size:
            neighbors = np.where(neighbors == 13, 12, neighbors)
            frame[y, x] = mode(neighbors)
        else:
            frame[y, x] = 1
    return int(len(xs))


def fill_tiny_enclosed_alpha(frame: np.ndarray) -> int:
    """Fill only enclosed transparent pinholes of at most four pixels."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (frame == 0).astype(np.uint8), connectivity=8
    )
    filled = 0
    for label in range(1, count):
        x, y, w, h, area = map(int, stats[label])
        if area > 4 or x == 0 or y == 0 or x + w == CELL or y + h == CELL:
            continue
        component = labels == label
        ring = cv2.dilate(component.astype(np.uint8), KERNEL).astype(bool) & ~component
        values = frame[ring]
        values = values[values != 0]
        if values.size:
            frame[component] = mode(values)
            filled += area
    return filled


def clean_suit_ramp(frame: np.ndarray) -> int:
    """Remove 1–3 pixel suit-tone islands while preserving larger cel blocks."""
    changed = 0
    snapshot = frame.copy()
    for tone in (4, 5, 6):
        count, labels, stats, _ = cv2.connectedComponentsWithStats(
            (snapshot == tone).astype(np.uint8), connectivity=8
        )
        for label in range(1, count):
            area = int(stats[label, cv2.CC_STAT_AREA])
            if area > 3:
                continue
            component = labels == label
            ring = cv2.dilate(component.astype(np.uint8), KERNEL).astype(bool) & ~component
            neighbors = frame[ring]
            neighbors = neighbors[np.isin(neighbors, [4, 5, 6])]
            if neighbors.size < 3:
                continue
            frame[component] = mode(neighbors, old=tone)
            changed += area
    return changed


def clean_burgundy_edge_singletons(frame: np.ndarray) -> int:
    """Remove tiny burgundy fragments in hair/legs; retain tie and cuff areas."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (frame == 11).astype(np.uint8), connectivity=8
    )
    changed = 0
    for label in range(1, count):
        x, y, w, h, area = map(int, stats[label])
        # The cravat and cuffs occupy torso/arm height. A one/two-pixel
        # burgundy island above the head or below the waist is color leakage.
        if area > 2 or not (y < 16 or y > 45):
            continue
        component = labels == label
        ring = cv2.dilate(component.astype(np.uint8), KERNEL).astype(bool) & ~component
        neighbors = frame[ring]
        neighbors = neighbors[~np.isin(neighbors, [0, 11])]
        if neighbors.size:
            frame[component] = mode(neighbors)
            changed += area
    return changed


def remove_detached_singletons(frame: np.ndarray) -> int:
    """Drop detached 1-pixel skin-color artifacts outside the face area."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (frame != 0).astype(np.uint8), connectivity=8
    )
    removed = 0
    for label in range(1, count):
        if int(stats[label, cv2.CC_STAT_AREA]) != 1:
            continue
        component = labels == label
        y, x = np.argwhere(component)[0]
        if frame[y, x] in (2, 3) and y >= 18:
            frame[y, x] = 0
            removed += 1
    return removed


def rgba_frame(indices: np.ndarray) -> Image.Image:
    rgb = np.zeros((CELL, CELL, 4), dtype=np.uint8)
    for i, color in enumerate(ROLE_RGB):
        rgb[indices == i, :3] = color
    rgb[indices != 0, 3] = 255
    return Image.fromarray(rgb, mode="RGBA")


def save_indexed(sheet: np.ndarray) -> None:
    image = Image.fromarray(sheet, mode="P")
    flat_palette: list[int] = []
    for color in ROLE_RGB:
        flat_palette.extend(color)
    flat_palette.extend([0] * (768 - len(flat_palette)))
    image.putpalette(flat_palette)
    image.info["transparency"] = 0
    image.info["dpi"] = (72, 72)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="PNG", transparency=0, optimize=False)
    check = Image.open(OUTPUT)
    if check.mode != "P" or check.size != (COLS * CELL, ROWS * CELL):
        raise AssertionError("PNG de saída diverge do contrato indexed 8×9×80")
    if check.info.get("transparency") != 0:
        raise AssertionError("índice transparente da saída não é 0")


def save_preview(sheet: np.ndarray, titles: list[str]) -> None:
    scale = 4
    cell_px = CELL * scale
    gap, label_h = 8, 20
    page = Image.new(
        "RGB",
        (gap + COLS * (cell_px + gap), gap + ROWS * (cell_px + label_h + gap)),
        (45, 49, 56),
    )
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default()
    for row in range(ROWS):
        top = gap + row * (cell_px + label_h + gap)
        draw.text((gap, top + 3), f"{row + 1:02d}  {titles[row]}",
                  fill=(230, 233, 238), font=font)
        for col in range(COLS):
            frame = sheet[row * CELL:(row + 1) * CELL,
                          col * CELL:(col + 1) * CELL]
            scaled = rgba_frame(frame).resize(
                (cell_px, cell_px), Image.Resampling.NEAREST
            )
            page.paste(scaled, (gap + col * (cell_px + gap), top + label_h), scaled)
    V5_DIR.mkdir(parents=True, exist_ok=True)
    page.save(PREVIEW)


def main() -> None:
    if not INPUT.is_file() or not INPUT_REPORT.is_file():
        raise FileNotFoundError("candidata v4 arquivada ou relatório ausente")
    if OUTPUT.exists() or REPORT.exists() or PREVIEW.exists():
        raise FileExistsError("saída v5 preexistente preservada; não sobrescrever")

    source = Image.open(INPUT)
    if source.mode != "P" or source.size != (COLS * CELL, ROWS * CELL):
        raise ValueError("a fonte precisa ser o atlas indexado v4, 640×720")
    raw = np.asarray(source, dtype=np.uint8)
    sheet = raw.copy()
    edits = Counter()

    # Compact the v4 palette by remapping its red effect index 12 out and
    # brass index 13 into the 12-color movement palette index 12.
    for row in range(ROWS):
        for col in range(COLS):
            y, x = row * CELL, col * CELL
            frame = sheet[y:y + CELL, x:x + CELL]
            if not np.any(frame):
                continue
            edits["reserved_red_reassigned_pixels"] += recolor_accent_red(frame)
            frame[frame == 13] = 12
            edits["enclosed_alpha_pinhole_pixels_filled"] += fill_tiny_enclosed_alpha(frame)
            edits["blue_ramp_confetti_pixels_reassigned"] += clean_suit_ramp(frame)
            edits["off_material_burgundy_pixels_reassigned"] += clean_burgundy_edge_singletons(frame)
            edits["detached_skin_singletons_removed"] += remove_detached_singletons(frame)

    # Verify exact 61-pose layout, margins, palette closure, and per-cell cutout.
    cell_counts: list[int] = []
    per_cell: list[dict] = []
    for row in range(ROWS):
        active = 0
        for col in range(COLS):
            frame = sheet[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL]
            used = sorted(int(v) for v in np.unique(frame))
            if len(used) > 1:
                active += 1
                if np.any(frame[0, :]) or np.any(frame[-1, :]) \
                        or np.any(frame[:, 0]) or np.any(frame[:, -1]):
                    raise AssertionError(f"quadro toca a borda: row={row+1}, col={col+1}")
                n, labels, stats, _ = cv2.connectedComponentsWithStats(
                    (frame != 0).astype(np.uint8), connectivity=8
                )
                areas = sorted(int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, n))
                per_cell.append({
                    "row": row + 1,
                    "column": col + 1,
                    "opaque_indices": [v for v in used if v != 0],
                    "connected_components_8": len(areas),
                    "component_areas_px": areas,
                    "orphan_component_pixels_lt4": sum(v for v in areas if v < 4),
                })
        cell_counts.append(active)
    if cell_counts != EXPECTED or sum(cell_counts) != 61:
        raise AssertionError(f"grades ativas inesperadas: {cell_counts}")
    used_all = sorted(int(v) for v in np.unique(sheet))
    if 13 in used_all or 12 not in used_all:
        raise AssertionError("paleta final contém vermelho reservado ou perdeu o latão")
    if not set(used_all).issubset(set(range(13))):
        raise AssertionError("paleta final excede os 12 papéis úteis")

    save_indexed(sheet)
    previous = json.loads(INPUT_REPORT.read_text())
    titles = [
        previous["frames"][sum(EXPECTED[:i])]["sequence"]
        for i in range(ROWS)
    ]
    save_preview(sheet, titles)

    flat = sheet.ravel()
    report = {
        "schema": "mof_dr_social_61_pose_refinement_v5",
        "candidate_status": "candidate_only; independent review and owner approval pending",
        "design_reference": {
            "path": "data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png",
            "sha256": "ddce2f5a302dd679610c1b0eb915ce10718a5df852f80e4a78af18db33426644",
            "role": "sole visual identity/design reference",
        },
        "pixel_source": {
            "path": "data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v4_source/dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v4.png",
            "sha256": sha256(INPUT),
            "role": "prior palette-converted candidate refined in place at indexed-pixel level; no old approved sprite sheet used",
        },
        "refinement": {
            "operation": "palette-role cleanup and local cluster cleanup; no pose redraw or frame reordering",
            "changes": dict(edits),
            "reserved_effect_color": "accent_red excluded from basic movement; each occurrence reassigned to local material",
            "cel_shading": "1–3 pixel isolated clusters in the three suit tones merged into neighboring suit tone; larger hard-edged shade blocks preserved",
            "transparency": "only enclosed transparent pinholes up to 4 pixels filled; open gaps between limbs/equipment preserved",
            "other_artifact_cleanup": "detached 1-pixel skin artifacts outside the face area removed; tiny burgundy fragments outside torso/arm band reassigned",
            "new_rgb_colors": 0,
            "frame_geometry_changed": False,
        },
        "palette": {
            "source": "doc/palettes_manifest.json :: characters.dr_ferdinand_social",
            "useful_colors": 12,
            "transparent_index": 0,
            "roles_by_index": ROLE_NAMES,
            "rgb_by_index": [list(color) for color in ROLE_RGB],
            "accent_red_used": False,
            "arcane_violet_used": False,
        },
        "atlas": {
            "columns": COLS,
            "rows": ROWS,
            "cell_px": [CELL, CELL],
            "sheet_px": [COLS * CELL, ROWS * CELL],
            "active_poses": 61,
            "blank_cells": 11,
            "sequence_rows": dict(zip(titles, EXPECTED)),
        },
        "output": {
            "path": "data/source_art/sprite_studies/dr_social/dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v5.png",
            "sha256": sha256(OUTPUT),
            "mode": "P",
            "palette_indices_used": used_all,
            "opaque_indices_used": [i for i in used_all if i != 0],
            "transparent_pixels": int(np.count_nonzero(flat == 0)),
            "opaque_pixels": int(np.count_nonzero(flat != 0)),
            "cells_touching_edge": 0,
            "frames_with_components_lt4px": sum(
                x["orphan_component_pixels_lt4"] > 0 for x in per_cell
            ),
            "frames": per_cell,
        },
        "validation_scope": {
            "passed": [
                "exact 8×9 grid of 80×80 cells",
                "61 active poses distributed 4/8/8/8/5/8/8/8/4",
                "12-color closed basic-movement palette; no effect red/violet",
                "index 0 transparency; no partial alpha",
                "no opaque pixels touch cell edges",
                "tiny color clusters cleaned without changing pose geometry",
            ],
            "pending_human_review": [
                "anatomy and action readability across all 61 frames",
                "fidelity to approved concept v4, including cane, coat, face, and body type",
                "cel-shading and outline consistency at native 80×80 and nearest-neighbor enlargement",
                "animation timing/physics and sequence transitions",
            ],
            "not_claimed": [
                "owner approval",
                "ROM integration",
                "Master System runtime palette allocation",
                "resource/scanline budget validation",
                "emulator validation or production readiness",
            ],
        },
    }
    V5_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"candidate: {OUTPUT}")
    print(f"sha256: {report['output']['sha256']}")
    print(f"layout rows: {cell_counts}; colors: {len(report['output']['opaque_indices_used'])}")
    print(f"cleanup: {dict(edits)}")
    print(f"preview: {PREVIEW}")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
