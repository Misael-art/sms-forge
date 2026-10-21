#!/usr/bin/env python3
"""Confine burgundy to Dr. Social's cravat and cuffs in candidate v7.

This is a deterministic indexed-pixel refinement of the v6 candidate. It does
not redraw, move, resize, reorder, or add poses. The approved model sheet v4 is
the sole visual identity authority; v6 is used only as pixel input.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
import refine_dr_social_61_pose_sprite_candidate_v5 as v5  # noqa: E402

ART = PROJECT / "data/source_art/sprite_studies/dr_social"
V6_DIR = ART / "review_drafts/basic_sequences_61f_candidate_v6_source"
V7_DIR = ART / "review_drafts/basic_sequences_61f_candidate_v7_source"
INPUT = V6_DIR / "dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v6.png"
INPUT_REPORT = V6_DIR / "dr_social_basic_sequences_candidate_v6_processing_report.json"
OUTPUT = V7_DIR / "dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v7.png"
METADATA = V7_DIR / "dr_social_basic_sequences_61f_candidate_v7_metadata.json"
LINEAGE = V7_DIR / "dr_social_basic_sequences_61f_candidate_v7_lineage.json"
PROMPT_NOTE = V7_DIR / "dr_social_basic_sequences_61f_candidate_v7_prompt.txt"
REPORT = V7_DIR / "dr_social_basic_sequences_candidate_v7_processing_report.json"
PREVIEW = V7_DIR / "dr_social_basic_sequences_candidate_v7_preview_4x.png"

CELL = 80
COLS = 8
ROWS = 9
EXPECTED = [4, 8, 8, 8, 5, 8, 8, 8, 4]
BURGUNDY = 11
SUIT_ROLES = (4, 5, 6)
ANCHOR_ROLES = (2, 3, 7, 8)
REPLACEMENT_ROLES = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connected_face(frame: np.ndarray) -> tuple[np.ndarray, dict] | tuple[None, None]:
    """Find the skin cluster closest to a gray-hair cluster as the face anchor."""
    skin = np.isin(frame, [2, 3]).astype(np.uint8)
    hair = (frame == 9).astype(np.uint8)
    skin_n, skin_labels, skin_stats, _ = cv2.connectedComponentsWithStats(
        skin, connectivity=8
    )
    hair_n, _, _, _ = cv2.connectedComponentsWithStats(hair, connectivity=8)
    if skin_n <= 1 or hair_n <= 1:
        return None, None

    hair_distance = cv2.distanceTransform(
        (hair == 0).astype(np.uint8), cv2.DIST_L2, 3
    )
    candidates = []
    for label in range(1, skin_n):
        area = int(skin_stats[label, cv2.CC_STAT_AREA])
        if area >= 2:
            component = skin_labels == label
            candidates.append((float(hair_distance[component].min()), -area, label))
    if not candidates:
        return None, None

    distance, _negative_area, face_label = min(candidates)
    if distance > 5:
        return None, None
    face = skin_labels == face_label
    ys, xs = np.where(face)
    return face, {
        "face_to_hair_distance_px": round(distance, 3),
        "face_bbox_xywh": [
            int(xs.min()), int(ys.min()),
            int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1),
        ],
        "face_center_xy": [round(float(xs.mean()), 2), round(float(ys.mean()), 2)],
        "face_bottom_y": int(ys.max()),
    }


def burgundy_material_cleanup(frame: np.ndarray) -> tuple[np.ndarray, dict]:
    """Keep burgundy in the cravat/cuff zones and locally restore other roles.

    The tie zone follows the face-to-upper-torso axis, so a turn or crouch does
    not assume a fixed canvas coordinate. Cuffs must sit between a compact
    white/gray glove cluster and the blue sleeve. Tall narrow cane-shaft
    clusters are rejected as glove anchors. Every other burgundy pixel takes
    the nearest extant non-transparent palette role in that same frame.
    """
    out = frame.copy()
    original = frame.copy()
    red = original == BURGUNDY
    red_before = int(red.sum())
    if red_before == 0:
        return out, {"burgundy_before": 0, "burgundy_after": 0, "recolored_by_role": {}}

    face, face_info = connected_face(original)
    if face is None:
        raise ValueError("face/hair anchor missing; refuse automatic recolor")

    face_y, face_x = np.where(face)
    face_cx = float(face_x.mean())
    face_cy = float(face_y.mean())
    face_bottom = float(face_y.max())
    yy, xx = np.indices(original.shape)
    suit = np.isin(original, SUIT_ROLES)

    # Find the upper-torso center close to the face, excluding the wide coat tails.
    torso_window = (
        suit
        & (np.abs(xx - face_cx) <= 8)
        & (yy >= face_bottom - 1)
        & (yy <= min(CELL - 1, face_bottom + 24))
    )
    torso_y, torso_x = np.where(torso_window)
    if len(torso_x):
        torso_cx = float(np.median(torso_x))
        torso_cy = float(np.median(torso_y))
    else:
        torso_cx = face_cx
        torso_cy = face_bottom + 10

    # Cravat: burgundy follows the neck-to-upper-chest axis, outside the face.
    axis = np.array([torso_cx - face_cx, torso_cy - face_bottom], dtype=np.float32)
    axis_sq = float(axis @ axis)
    if axis_sq < 25:
        axis = np.array([0.0, 10.0], dtype=np.float32)
        axis_sq = 100.0
    tie_keep = np.zeros_like(original, dtype=bool)
    for py, px in zip(*np.where(red)):
        relative = np.array([px - face_cx, py - face_bottom], dtype=np.float32)
        t = float(relative @ axis / axis_sq)
        perpendicular = float(np.linalg.norm(relative - t * axis))
        if 0.05 <= t <= 0.78 and perpendicular <= 4.25:
            tie_keep[py, px] = True
    tie_keep &= ~face

    # Cuffs: retain only pixels between a compact glove and adjacent blue sleeve.
    white = np.isin(original, [7, 8]).astype(np.uint8)
    white_n, white_labels, white_stats, white_centers = cv2.connectedComponentsWithStats(
        white, connectivity=8
    )
    cuff_keep = np.zeros_like(original, dtype=bool)
    suit_distance = cv2.distanceTransform(
        (~suit).astype(np.uint8), cv2.DIST_L2, 3
    )
    kernel = np.ones((3, 3), dtype=np.uint8)
    for label in range(1, white_n):
        x, y, width, height, area = map(int, white_stats[label])
        if area < 5 or area > 65 or height == 0:
            continue
        aspect = width / height
        if not 0.38 <= aspect <= 2.8:
            continue
        glove_cx, glove_cy = map(float, white_centers[label])
        face_gap = float(np.hypot(glove_cx - face_cx, glove_cy - face_cy))
        if not 8 <= face_gap <= 42:
            continue

        glove = white_labels == label
        dilated_glove = cv2.dilate(
            glove.astype(np.uint8), kernel, iterations=2
        ).astype(bool)
        if not np.any(dilated_glove & suit):
            continue

        toward_torso = np.array([torso_cx - glove_cx, torso_cy - glove_cy])
        for py, px in zip(*np.where(red)):
            if not dilated_glove[py, px] or suit_distance[py, px] > 2.1:
                continue
            hand_to_pixel = np.array([px - glove_cx, py - glove_cy])
            if float(hand_to_pixel @ toward_torso) > 0:
                cuff_keep[py, px] = True

    keep = red & (tie_keep | cuff_keep)
    leak = red & ~keep
    recolored_by_role: Counter[str] = Counter()
    if np.any(leak):
        distance_maps = []
        role_labels = []
        for role in REPLACEMENT_ROLES:
            role_mask = (original == role).astype(np.uint8)
            if not np.any(role_mask):
                continue
            distance_maps.append(
                cv2.distanceTransform((1 - role_mask).astype(np.uint8), cv2.DIST_L2, 3)
            )
            role_labels.append(role)
        if not role_labels:
            raise ValueError("no local palette roles available for burgundy replacement")
        nearest = np.argmin(np.stack(distance_maps), axis=0)
        labels = np.asarray(role_labels, dtype=np.uint8)
        replacements = labels[nearest[leak]]
        leak_y, leak_x = np.where(leak)
        out[leak_y, leak_x] = replacements
        for role in replacements:
            recolored_by_role[v5.ROLE_NAMES[int(role)]] += 1

    return out, {
        **face_info,
        "torso_center_xy": [round(torso_cx, 2), round(torso_cy, 2)],
        "burgundy_before": red_before,
        "burgundy_kept_cravat": int((red & tie_keep).sum()),
        "burgundy_kept_cuffs": int((red & cuff_keep).sum()),
        "burgundy_after": int((out == BURGUNDY).sum()),
        "burgundy_recolored_by_role": dict(sorted(recolored_by_role.items())),
    }


def save_indexed(sheet: np.ndarray) -> None:
    image = Image.fromarray(sheet, mode="P")
    palette = [component for rgb in v5.ROLE_RGB for component in rgb]
    palette.extend([0] * (768 - len(palette)))
    image.putpalette(palette)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="PNG", transparency=0, optimize=False)
    check = Image.open(OUTPUT)
    if check.mode != "P" or check.size != (COLS * CELL, ROWS * CELL):
        raise AssertionError("v7 lost indexed mode or 640×720 dimensions")
    if check.info.get("transparency") != 0:
        raise AssertionError("v7 transparent palette index is not 0")


def rgba_frame(indices: np.ndarray) -> Image.Image:
    rgba = np.zeros((CELL, CELL, 4), dtype=np.uint8)
    for index, rgb in enumerate(v5.ROLE_RGB):
        rgba[indices == index, :3] = rgb
    rgba[indices != 0, 3] = 255
    return Image.fromarray(rgba, mode="RGBA")


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
            indices = sheet[row * CELL:(row + 1) * CELL,
                            col * CELL:(col + 1) * CELL]
            enlarged = rgba_frame(indices).resize(
                (cell_px, cell_px), Image.Resampling.NEAREST
            )
            page.paste(enlarged, (gap + col * (cell_px + gap), top + label_h), enlarged)
    page.save(PREVIEW)


def main() -> None:
    outputs = [OUTPUT, METADATA, LINEAGE, PROMPT_NOTE, REPORT, PREVIEW]
    if not INPUT.is_file() or not INPUT_REPORT.is_file():
        raise FileNotFoundError("archived v6 pixels or processing report are missing")
    if any(path.exists() for path in outputs):
        raise FileExistsError("a v7 reserved output already exists; preserve and inspect it")

    source_image = Image.open(INPUT)
    if source_image.mode != "P" or source_image.size != (COLS * CELL, ROWS * CELL):
        raise ValueError("input must be indexed v6 at 640×720")
    source = np.asarray(source_image, dtype=np.uint8).copy()
    sheet = source.copy()
    per_frame = []
    frame_counts = []
    for row in range(ROWS):
        for col in range(COLS):
            frame = sheet[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL]
            if not np.any(frame):
                continue
            cleaned, details = burgundy_material_cleanup(frame)
            frame[:] = cleaned
            per_frame.append({"row": row + 1, "column": col + 1, **details})
            frame_counts.append((row + 1, col + 1))

    if len(per_frame) != 61:
        raise AssertionError(f"expected 61 active frames, found {len(per_frame)}")
    if not np.array_equal(source != 0, sheet != 0):
        raise AssertionError("v7 changed alpha/cutout geometry")
    changed = source != sheet
    if np.any(changed & (source != BURGUNDY)):
        raise AssertionError("v7 modified pixels outside the burgundy role")

    row_counts = []
    for row, expected in enumerate(EXPECTED):
        active = sum(
            bool(np.any(sheet[row * CELL:(row + 1) * CELL,
                              col * CELL:(col + 1) * CELL]))
            for col in range(COLS)
        )
        row_counts.append(active)
        if active != expected:
            raise AssertionError(f"frame count changed in row {row + 1}: {active}")

    used = sorted(int(value) for value in np.unique(sheet))
    if used != list(range(13)):
        raise AssertionError(f"unexpected palette closure: {used}")
    edge_cells = []
    for row in range(ROWS):
        for col in range(COLS):
            frame = sheet[row * CELL:(row + 1) * CELL,
                          col * CELL:(col + 1) * CELL]
            if np.any(frame[[0, -1], :]) or np.any(frame[:, [0, -1]]):
                edge_cells.append([row + 1, col + 1])
    if edge_cells:
        raise AssertionError(f"opaque pixels touch cell edges: {edge_cells}")

    save_indexed(sheet)
    prior_report = json.loads(INPUT_REPORT.read_text())
    titles = list(prior_report["atlas"]["sequence_rows"].keys())
    save_preview(sheet, titles)

    output_hash = sha256(OUTPUT)
    input_hash = sha256(INPUT)
    script_hash = sha256(Path(__file__))
    report = {
        "schema": "mof_dr_social_61_pose_refinement_v7",
        "candidate_status": "candidate_only; independent review and owner approval pending",
        "pixel_source": {
            "path": "data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v6_source/dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v6.png",
            "sha256": input_hash,
            "role": "pixel-only input; not an identity reference",
        },
        "identity_reference": {
            "path": "data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png",
            "sha256": "ddce2f5a302dd679610c1b0eb915ce10718a5df852f80e4a78af18db33426644",
            "role": "sole visual identity reference",
        },
        "refinement": {
            "operation": "semantic burgundy confinement to the cravat and cuffs; all other burgundy pixels reassigned to the nearest extant non-transparent role in the same frame",
            "method": "face-to-upper-torso axis for cravat; compact glove and sleeve adjacency plus body-facing vector for cuffs; reject elongated staff/cane anchors",
            "geometry_or_order_changed": False,
            "script": "tools/refine_dr_social_61_pose_sprite_candidate_v7.py",
            "script_sha256": script_hash,
            "burgundy_before": int((source == BURGUNDY).sum()),
            "burgundy_after": int((sheet == BURGUNDY).sum()),
            "burgundy_recolored": int(changed.sum()),
            "recolored_by_role": dict(sorted(Counter({}).items())),
            "per_frame": per_frame,
        },
        "output": {
            "path": "data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v7_source/dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v7.png",
            "sha256": output_hash,
            "dimensions_px": [640, 720],
            "palette_indices_used": used,
            "useful_color_count": len(used) - 1,
            "transparent_index": 0,
        },
        "structural_checks": {
            "active_frames": len(per_frame),
            "blank_cells": 11,
            "row_counts": row_counts,
            "cell_px": [80, 80],
            "alpha_geometry_unchanged": True,
            "changed_pixels_were_burgundy_only": True,
            "opaque_pixels_touch_cell_edges": False,
        },
        "human_review_pending": [
            "visual confirmation that burgundy now appears only on cravat/cuffs and is absent from hair, suit, cane, and boots in all 61 frames",
            "anatomy, face readability, hand orientation, grip continuity, and cane terminal shape frame by frame",
            "cel-shaded shadow flow and pixel clusters at 1x and nearest-neighbor 4x",
            "sequence timing, pose order, and action readability",
        ],
        "not_claimed": [
            "owner approval", "independent art approval", "hardware resource budget",
            "ROM integration", "emulator validation", "production readiness",
        ],
    }
    # Aggregate correction destinations without relying on display colors.
    aggregate: Counter[str] = Counter()
    for frame in per_frame:
        aggregate.update(frame.get("burgundy_recolored_by_role", {}))
    report["refinement"]["recolored_by_role"] = dict(sorted(aggregate.items()))
    REPORT.write_text(json.dumps(report, indent=2) + "\n")

    metadata = json.loads(
        (V6_DIR / "dr_social_basic_sequences_61f_candidate_v6_metadata.json").read_text()
    )
    metadata["asset_id"] = "dr_social_animation_source_v07"
    metadata["asset"]["path"] = report["output"]["path"]
    metadata["asset"]["sha256"] = output_hash
    metadata["review"]["independent_review"] = "pending_assignment"
    metadata["review"]["owner_approval"] = False
    metadata["review"]["promotion"] = "candidate only; not approved, not in res/; no ROM validation"
    metadata["validation_summary"]["burgundy_material_role_confinement"] = "producer preflight; independent visual check pending"
    METADATA.write_text(json.dumps(metadata, indent=2) + "\n")

    lineage = json.loads(
        (V6_DIR / "dr_social_basic_sequences_61f_candidate_v6_lineage.json").read_text()
    )
    lineage["asset_id"] = "dr_social_animation_source_v07"
    lineage["generation_history"].append({
        "stage": "v7 burgundy material-role cleanup",
        "input": {
            "path": report["pixel_source"]["path"],
            "sha256": input_hash,
            "role": "pixel-only input",
        },
        "path": report["output"]["path"],
        "sha256": output_hash,
        "script": "tools/refine_dr_social_61_pose_sprite_candidate_v7.py",
        "script_sha256": script_hash,
        "geometry_or_order_changed": False,
        "status": "candidate; independent review and owner approval pending",
    })
    lineage["reference_boundary"]["v6_used_for_pixel_cleanup_only"] = True
    lineage["reference_boundary"]["v4_concept_is_identity_authority"] = True
    LINEAGE.write_text(json.dumps(lineage, indent=2) + "\n")
    PROMPT_NOTE.write_text(
        "No image-generation prompt was used for v7. This is a deterministic indexed-pixel refinement.\n"
        "Identity authority: approved Dr. Social model sheet CPS2-Alpha-Cel v4 only.\n"
        "Input v6 was used only as pixel data. The operation confines burgundy to the cravat and cuffs,\n"
        "then restores other burgundy pixels to the nearest local valid palette role. No frame is moved,\n"
        "redrawn, scaled, added, removed, or reordered. Candidate only; all artistic and owner reviews remain pending.\n"
    )

    print(f"candidate: {OUTPUT}")
    print(f"sha256: {output_hash}")
    print(f"burgundy pixels: {int((source == BURGUNDY).sum())} -> {int((sheet == BURGUNDY).sum())}")
    print(f"recolored pixels: {int(changed.sum())}")
    print(f"frames: {len(per_frame)}; row counts: {row_counts}; useful colors: {len(used)-1}")
    print(f"preview: {PREVIEW}")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
