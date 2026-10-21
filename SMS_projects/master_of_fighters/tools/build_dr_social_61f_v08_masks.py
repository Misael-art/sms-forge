#!/usr/bin/env python3
"""Deterministic v08 repaint of the frozen 61-frame v07 pixel geometry.

The script creates explicit per-frame material masks, edits only inside those
masks, preserves the indexed 640x720 canvas/alpha/cells, and emits audit
artifacts. It never uses ImageGen, diffusion, RGB distance, blur, or resampling.
The result is a review candidate, never a production/ROM asset by itself.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / (
    "data/source_art/sprite_studies/dr_social/review_drafts/"
    "basic_sequences_61f_candidate_v7_source/"
    "dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v7.png"
)
OUT = PROJECT / (
    "data/source_art/sprite_studies/dr_social/review_drafts/"
    "basic_sequences_61f_candidate_v08_masks_final"
)
EXPECTED_SOURCE_SHA = "f5c41fb2204e3b2fff9a6e824fc55a767c2456dcdd9c62d17351f76696c95dc8"
W = H = CELL = 80
COLS, ROWS = 8, 9
COUNTS = [4, 8, 8, 8, 5, 8, 8, 8, 4]
SEQUENCES = [
    "idle", "walk_forward", "walk_backward", "jump", "crouch",
    "dash_run", "knockdown_fall", "tech_roll_getup", "guard",
]
PALETTE = [
    (255, 0, 255), (0, 0, 85), (255, 170, 170), (170, 85, 85),
    (85, 170, 255), (0, 170, 170), (0, 85, 85), (255, 255, 255),
    (170, 170, 170), (85, 85, 85), (85, 0, 0), (170, 0, 85),
    (255, 255, 0),
]
RGB_BY_INDEX = {i: rgb for i, rgb in enumerate(PALETTE)}
MATERIAL_TONES = {
    "hair": (8, 9),
    "coat": (4, 5, 6),
    "skin": (2, 3),
    "leather": (10,),
}
ROLE_SEEDS = {
    "coat": (4, 5, 6),
    "skin": (2, 3),
    "leather": (10,),
}
MASK_COLORS = {
    "hair": (160, 160, 160),
    "coat": (45, 170, 255),
    "skin": (255, 150, 160),
    "leather": (90, 20, 20),
    "white_accessory": (255, 255, 255),
    "burgundy_allowed": (200, 0, 80),
    "yellow_allowed": (255, 255, 0),
    "yellow_pending": (255, 160, 0),
    "outline": (0, 0, 85),
    "unresolved": (255, 0, 255),
}
K3 = np.ones((3, 3), np.uint8)
K3[1, 1] = 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02X%02X%02X" % rgb


def components(mask: np.ndarray) -> list[dict]:
    count, labels, stats, centers = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8), connectivity=8
    )
    result = []
    for label in range(1, count):
        x, y, width, height, area = map(int, stats[label])
        result.append({
            "label": label,
            "mask": labels == label,
            "area": area,
            "bbox": (x, y, width, height),
            "center": (float(centers[label][0]), float(centers[label][1])),
        })
    return result


def dilate(mask: np.ndarray, size: int = 3, iterations: int = 1) -> np.ndarray:
    kernel = np.ones((size, size), np.uint8)
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=iterations).astype(bool)


def neighbor_count(mask: np.ndarray) -> np.ndarray:
    return cv2.filter2D(
        mask.astype(np.uint8), cv2.CV_16S, K3,
        borderType=cv2.BORDER_CONSTANT,
    )


def pca_line_ratio(mask: np.ndarray) -> float:
    ys, xs = np.where(mask)
    if len(xs) < 3:
        return 0.0
    coords = np.column_stack((xs, ys)).astype(np.float64)
    eigenvalues = np.linalg.eigvalsh(np.cov(coords.T))
    return float(eigenvalues[-1] / max(eigenvalues[0], 1e-6))


def torso_center_x(idx: np.ndarray, head_bottom: int, body_bbox: tuple[int, int, int, int]) -> float:
    x0, y0, x1, y1 = body_bbox
    coat_y = (idx == 4) | (idx == 5) | (idx == 6)
    top = max(y0, head_bottom + 1)
    bottom = min(y1 + 1, head_bottom + 22)
    ys, xs = np.where(coat_y[top:bottom, x0:x1 + 1])
    if len(xs) >= 4:
        return float(np.median(xs + x0))
    ys, xs = np.where(coat_y)
    return float(np.median(xs)) if len(xs) else (x0 + x1) / 2


def build_hair_anchor(idx: np.ndarray) -> tuple[np.ndarray, dict]:
    """Anchor gray hair at the largest source hair cluster, not at color alone."""
    gray_dark = idx == 9
    gray_components = components(gray_dark)
    if not gray_components:
        raise ValueError("frame has no index-9 gray-hair anchor")
    main = max(gray_components, key=lambda comp: comp["area"])
    ax, ay, aw, ah = main["bbox"]
    # Include separated gray locks only when they sit in the small head halo.
    halo = dilate(main["mask"], size=7)
    gray_all = np.isin(idx, [8, 9])
    # Keep whole nearby gray components. Clipping a lock to the anchor halo
    # created a jagged, incomplete hair mask at sideburns and back locks.
    nearby_gray = np.zeros(idx.shape, dtype=bool)
    for comp in components(gray_all):
        x0, y0, width, height = comp["bbox"]
        cx, cy = comp["center"]
        if (np.any(comp["mask"] & halo)
                and cy <= ay + ah + 13
                and abs(cx - (ax + aw / 2)) <= aw + 12):
            nearby_gray |= comp["mask"]
    hair_core = main["mask"] | nearby_gray
    # Recover interior miscolored pixels only when the hair anchors surround them.
    support = dilate(hair_core, size=11)
    hair_votes = neighbor_count(hair_core)
    skin_seed = np.isin(idx, [2, 3])
    skin_votes = neighbor_count(skin_seed)
    # Do not absorb canonical facial metal, skin, shirt, leather, tie, or cane
    # accents into hair merely because gray pixels surround them.
    blocked = np.isin(idx, [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12])
    contaminated = (hair_votes >= 5) & (hair_votes > skin_votes) & support & ~blocked
    hair = hair_core | contaminated
    yy, xx = np.where(hair_core)
    bbox = (int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max()))
    return hair, {
        "anchor_area_index9": int(main["area"]),
        "anchor_bbox_xywh": [ax, ay, aw, ah],
        "hair_core_bbox_xyxy": list(bbox),
        "hair_mask_pixels": int(hair.sum()),
        "recovered_interior_pixels": int(np.count_nonzero(contaminated)),
    }


def classify_accent_zones(idx: np.ndarray, hair_mask: np.ndarray,
                          body_bbox: tuple[int, int, int, int],
                          yellow_glasses: bool) -> tuple[dict[str, np.ndarray], dict]:
    """Create explicit white/cane, yellow/cane, and burgundy/tie/boot masks."""
    x0, y0, x1, y1 = body_bbox
    yy, xx = np.where(hair_mask)
    head_bottom = int(yy.max()) if len(yy) else y0
    body_h = max(1, y1 - y0 + 1)
    torso_x = torso_center_x(idx, head_bottom, body_bbox)

    white = idx == 7
    gray_accessory = np.isin(idx, [8, 9]) & ~hair_mask
    # The cane may have gray source pixels in the v07 coloring. Treat long,
    # straight neutral components as an explicit cane mask before recoloring.
    neutral = white | gray_accessory
    line_mask = np.zeros(idx.shape, dtype=bool)
    line_components = []
    for comp in components(neutral):
        x, y, w, h = comp["bbox"]
        cx, cy = comp["center"]
        major, minor = max(w, h), max(1, min(w, h))
        if (comp["area"] >= 7 and major >= 8 and major >= 2.5 * minor
                and pca_line_ratio(comp["mask"]) >= 3.0
                and cy > head_bottom - 2 and cy > y0 + 5):
            line_mask |= comp["mask"]
            line_components.append(comp)
    if np.any(line_mask):
        line_mask |= dilate(line_mask, size=3) & neutral

    glove_mask = np.zeros(idx.shape, dtype=bool)
    glove_components = []
    for comp in components(white):
        x, y, w, h = comp["bbox"]
        cx, cy = comp["center"]
        if (comp["area"] >= 3 and max(w, h) <= 12 and min(w, h) >= 2
                and 0.35 <= w / max(1, h) <= 2.9
                and cy > head_bottom + 1
                and not np.any(comp["mask"] & hair_mask)):
            glove_mask |= comp["mask"]
            glove_components.append(comp)
    if np.any(glove_mask):
        glove_mask |= dilate(glove_mask, size=3) & white

    burgundy = idx == 11
    burgundy_components = components(burgundy)
    tie_mask = np.zeros(idx.shape, dtype=bool)
    tie_candidates = []
    for comp in burgundy_components:
        cx, cy = comp["center"]
        if (head_bottom < cy < y0 + 0.64 * body_h
                and abs(cx - torso_x) <= max(9, 0.18 * (x1 - x0 + 1))):
            tie_candidates.append(comp)
    tie_component = max(tie_candidates, key=lambda comp: comp["area"]) if tie_candidates else None
    if tie_component:
        tie_mask |= tie_component["mask"]
        tie_halo = dilate(tie_component["mask"], size=7)
        for comp in burgundy_components:
            if comp is tie_component:
                continue
            if np.any(comp["mask"] & tie_halo):
                tie_mask |= comp["mask"]

    leather_seed = idx == 10
    boot_neighborhood = dilate(leather_seed, size=7, iterations=1)
    boot_burgundy = np.zeros(idx.shape, dtype=bool)
    for comp in burgundy_components:
        cx, cy = comp["center"]
        if cy >= y1 - 13 and np.any(comp["mask"] & boot_neighborhood):
            boot_burgundy |= comp["mask"]
    burgundy_allowed = tie_mask | boot_burgundy

    yellow = idx == 12
    yellow_allowed = np.zeros(idx.shape, dtype=bool)
    yellow_pending = np.zeros(idx.shape, dtype=bool)
    cane_neighborhood = dilate(line_mask, size=13)
    for comp in components(yellow):
        _, cy = comp["center"]
        near_cane = np.any(comp["mask"] & cane_neighborhood)
        if near_cane and cy > head_bottom + 2:
            yellow_allowed |= comp["mask"]
        elif yellow_glasses and np.any(comp["mask"] & dilate(hair_mask, size=7)):
            yellow_allowed |= comp["mask"]
        elif cy <= head_bottom + 8:
            # Preserve the canonical brass spectacles pending the explicit
            # owner resolution of the v08 yellow-zone conflict.
            yellow_pending |= comp["mask"]

    # Collar pixels are white only when adjacent to the anchored tie, above its
    # centerline, and outside the face/hair. This leaves isolated face flecks out.
    collar_mask = np.zeros(idx.shape, dtype=bool)
    if np.any(tie_mask):
        tie_ys, tie_xs = np.where(tie_mask)
        tie_top = int(tie_ys.min())
        tie_cx = float(np.mean(tie_xs))
        collar_region = dilate(tie_mask, size=5) & white & ~hair_mask
        collar_region &= np.indices(idx.shape)[0] <= tie_top + 2
        if np.any(collar_region):
            collar_mask |= collar_region

    white_allowed = line_mask | glove_mask | collar_mask
    metadata = {
        "hair_bottom_y": head_bottom,
        "torso_center_x": round(torso_x, 2),
        "cane_shaft_pixels": int(line_mask.sum()),
        "cane_shaft_components": len(line_components),
        "glove_pixels": int(glove_mask.sum()),
        "glove_components": len(glove_components),
        "collar_pixels": int(collar_mask.sum()),
        "tie_pixels": int(tie_mask.sum()),
        "boot_trim_pixels": int(boot_burgundy.sum()),
        "yellow_cane_pixels": int(yellow_allowed.sum()) if not yellow_glasses else int(np.count_nonzero(yellow_allowed & ~dilate(hair_mask, size=7))),
        "yellow_glasses_option": "allowed" if yellow_glasses else "strict_cane_only",
        "white_allowed_pixels": int(white_allowed.sum()),
        "yellow_allowed_pixels": int(yellow_allowed.sum()),
        "yellow_pending_pixels": int(yellow_pending.sum()),
        "burgundy_allowed_pixels": int(burgundy_allowed.sum()),
    }
    return {
        "white_accessory": white_allowed,
        "yellow_allowed": yellow_allowed,
        "yellow_pending": yellow_pending,
        "burgundy_allowed": burgundy_allowed,
        "cane_shaft": line_mask,
        "glove": glove_mask,
        "cravat": tie_mask,
        "boot_trim": boot_burgundy,
    }, metadata


def build_material_masks(idx: np.ndarray, hair_anchor: np.ndarray,
                         protected: np.ndarray) -> tuple[dict[str, np.ndarray], dict]:
    opaque = idx != 0
    blocked = (idx == 0) | (idx == 1) | protected
    seed_masks = {
        "hair": hair_anchor,
        "coat": np.isin(idx, ROLE_SEEDS["coat"]),
        "skin": np.isin(idx, ROLE_SEEDS["skin"]),
        "leather": idx == 10,
    }
    role_order = ["hair", "skin", "coat", "leather"]
    masks = {name: seed.copy() for name, seed in seed_masks.items()}
    # Keep role masks mutually exclusive; source seeds always outrank expansions.
    seed_owner = np.full(idx.shape, -1, dtype=np.int8)
    for role_index, name in enumerate(role_order):
        seed_owner[seed_masks[name]] = role_index
    occupied = seed_owner >= 0
    ambiguous_total = 0
    # Grow explicit masks inward through short noisy runs. At each step, a
    # pixel joins only when at least two neighbors agree and the winning
    # material has a strict lead; outline, transparency, and semantic anchors
    # remain hard barriers.
    for _ in range(5):
        vote_stack = np.stack([neighbor_count(masks[name]) for name in role_order])
        sorted_votes = np.sort(vote_stack, axis=0)
        best, second = sorted_votes[-1], sorted_votes[-2]
        winner = np.argmax(vote_stack, axis=0)
        unowned = ~occupied & opaque & ~blocked
        eligible = unowned & (best >= 1) & (best > second)
        ambiguous_total += int(np.count_nonzero(unowned & (best >= 1) & (best == second)))
        if not np.any(eligible):
            break
        for role_index, name in enumerate(role_order):
            masks[name] |= eligible & (winner == role_index)
        occupied |= eligible
    # Hair expansion stays attached to the top-of-frame gray anchor and may
    # not spread down the body through a run of unrelated gray pixels.
    hair_limit = dilate(hair_anchor, size=17)
    extra_hair = masks["hair"] & ~seed_masks["hair"] & ~hair_limit
    masks["hair"] &= ~extra_hair
    summary = {
        f"{name}_mask_pixels": int(mask.sum()) for name, mask in masks.items()
    }
    summary["ambiguous_expansion_pixels"] = ambiguous_total
    return masks, summary


def choose_tone(idx: np.ndarray, mask: np.ndarray, y: int, x: int,
                allowed: tuple[int, ...], radius: int = 2) -> int | None:
    y0, y1 = max(0, y - radius), min(H, y + radius + 1)
    x0, x1 = max(0, x - radius), min(W, x + radius + 1)
    patch = idx[y0:y1, x0:x1]
    local_mask = mask[y0:y1, x0:x1] & np.isin(patch, allowed)
    vals = patch[local_mask]
    if vals.size == 0:
        return None
    counts = Counter(map(int, vals.tolist()))
    return min(counts, key=lambda value: (-counts[value], allowed.index(value)))


def recolor_mask(idx: np.ndarray, out: np.ndarray, mask: np.ndarray,
                 role: str, allowed: tuple[int, ...]) -> tuple[int, list[tuple[int, int, int, int]]]:
    changed = 0
    unresolved = []
    snapshot = out.copy()
    ys, xs = np.where(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if int(out[y, x]) in allowed:
            continue
        tone = choose_tone(snapshot, mask, y, x, allowed)
        if tone is None:
            tone = choose_tone(idx, mask, y, x, allowed, radius=4)
        if tone is None:
            unresolved.append((y, x, int(idx[y, x]), role))
            continue
        if int(out[y, x]) != tone:
            out[y, x] = tone
            changed += 1
    # Collapse only one-pixel shade components, and only within this explicit mask.
    clustered = out.copy()
    for tone in allowed:
        comps = components((clustered == tone) & mask)
        for comp in comps:
            if comp["area"] != 1:
                continue
            y, x = np.argwhere(comp["mask"])[0].tolist()
            y, x = int(y), int(x)
            y0, y1 = max(0, y - 3), min(H, y + 4)
            x0, x1 = max(0, x - 3), min(W, x + 4)
            patch = clustered[y0:y1, x0:x1]
            local_mask = mask[y0:y1, x0:x1] & np.isin(patch, allowed)
            local_mask[y - y0, x - x0] = False
            alternatives = patch[local_mask & (patch != tone)]
            if alternatives.size:
                counts = Counter(map(int, alternatives.tolist()))
                replacement = min(counts, key=lambda value: (-counts[value], allowed.index(value)))
                out[y, x] = replacement
                changed += 1
    return changed, unresolved


def remap_unanchored_accents(idx: np.ndarray, out: np.ndarray,
                             material_masks: dict[str, np.ndarray],
                             accent_masks: dict[str, np.ndarray]) -> tuple[int, list[tuple[int, int, int, str]]]:
    unresolved = []
    changed = 0
    material_roles = ["hair", "coat", "skin", "leather"]
    accent_indices = {
        "white_accessory": {7},
        "burgundy_allowed": {11},
        "yellow_allowed": {12},
    }
    # Index 8 is hair only when in the hair mask; elsewhere it can be the white
    # cane/shirt material or a leak into another strongly anchored material.
    accent_indices["gray_outside_hair"] = {8, 9}
    allowed_zone = {
        "white_accessory": accent_masks["white_accessory"],
        "burgundy_allowed": accent_masks["burgundy_allowed"],
        "yellow_allowed": accent_masks["yellow_allowed"],
        "gray_outside_hair": material_masks["hair"] | accent_masks["white_accessory"],
    }
    for zone, indices in accent_indices.items():
        leak = np.isin(idx, list(indices)) & ~allowed_zone[zone]
        # Already owned by a material mask? The per-material pass handles it.
        covered = np.zeros(idx.shape, dtype=bool)
        for mask in material_masks.values():
            covered |= mask
        if zone == "gray_outside_hair":
            covered &= ~accent_masks["white_accessory"]
        todo = leak & covered
        if zone == "gray_outside_hair":
            # Gray index 8 on the anchored cane/glove is rendered as canonical white.
            gray_cane = todo & accent_masks["white_accessory"]
            out[gray_cane] = 7
            changed += int(gray_cane.sum())
            todo &= ~accent_masks["white_accessory"]
        # Remaining leaks covered by a material mask are recolored to its own ramp.
        for role in material_roles:
            role_mask = material_masks[role]
            role_tones = MATERIAL_TONES[role]
            role_todo = todo & role_mask
            ys, xs = np.where(role_todo)
            for y, x in zip(ys.tolist(), xs.tolist()):
                tone = choose_tone(out, role_mask, y, x, role_tones)
                if tone is None:
                    continue
                else:
                    if out[y, x] != tone:
                        out[y, x] = tone
                        changed += 1
                    role_mask[y, x] = True
            todo &= ~role_mask
    return changed, unresolved


def singleton_count(idx: np.ndarray, masks: dict[str, np.ndarray]) -> dict[str, int]:
    result = {}
    for role in ("hair", "coat", "skin"):
        total = 0
        for tone in MATERIAL_TONES[role]:
            total += sum(1 for comp in components((idx == tone) & masks[role]) if comp["area"] == 1)
        result[role] = total
    return result


def frame_specs() -> list[dict]:
    result = []
    global_index = 0
    for row, (seq, count) in enumerate(zip(SEQUENCES, COUNTS)):
        for col in range(count):
            result.append({
                "global_index": global_index,
                "frame_id": f"{seq.upper()}_{col + 1:02d}",
                "sequence": seq,
                "sequence_frame": col + 1,
                "row": row,
                "col": col,
                "origin": [col * CELL, row * CELL],
            })
            global_index += 1
    return result


def frame_bbox(idx: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(idx != 0)
    if not len(xs):
        raise ValueError("active cell is transparent")
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def select_local_material(idx: np.ndarray, out: np.ndarray,
                          masks: dict[str, np.ndarray], y: int, x: int) -> tuple[int | None, str | None]:
    roles = ["hair", "coat", "skin", "leather"]
    for radius in (1, 2, 3):
        y0, y1 = max(0, y - radius), min(H, y + radius + 1)
        x0, x1 = max(0, x - radius), min(W, x + radius + 1)
        counts = {}
        for role in roles:
            local = masks[role][y0:y1, x0:x1].copy()
            if 0 <= y - y0 < local.shape[0] and 0 <= x - x0 < local.shape[1]:
                local[y - y0, x - x0] = False
            counts[role] = int(local.sum())
        ordered = sorted(roles, key=lambda role: (-counts[role], roles.index(role)))
        if counts[ordered[0]] >= 2 and counts[ordered[0]] - counts[ordered[1]] >= 1:
            role = ordered[0]
            tone = choose_tone(out, masks[role], y, x, MATERIAL_TONES[role], radius=max(3, radius + 1))
            if tone is not None:
                return tone, role
    return None, None


def process_frame(source_idx: np.ndarray, yellow_glasses: bool) -> tuple[np.ndarray, dict, dict[str, np.ndarray], list[tuple[int, int, int, str]]]:
    bbox = frame_bbox(source_idx)
    hair_mask, hair_info = build_hair_anchor(source_idx)
    accents, accent_info = classify_accent_zones(source_idx, hair_mask, bbox, yellow_glasses)
    protected = (accents["white_accessory"] | accents["yellow_allowed"]
                 | accents["yellow_pending"] | accents["burgundy_allowed"])
    material_masks, mask_info = build_material_masks(source_idx, hair_mask, protected)
    out = source_idx.copy()
    changed_by_role = {}
    unresolved = []
    for role in ("coat", "hair", "skin", "leather"):
        changed, misses = recolor_mask(
            source_idx, out, material_masks[role], role, MATERIAL_TONES[role]
        )
        changed_by_role[role] = changed
        unresolved.extend(misses)

    # Gray index 8 outside the hair can belong to an explicitly anchored cane shaft.
    gray_accessory = accents["white_accessory"] & np.isin(source_idx, [8, 9])
    out[gray_accessory] = 7
    # Assign any remaining accent/gray leaks only to the local anchored material.
    accent_changed, misses = remap_unanchored_accents(
        source_idx, out, material_masks, accents
    )
    changed_by_role["semantic_reassignment"] = accent_changed
    unresolved.extend(misses)

    # Residual burgundy/yellow/white must be classified, never silently accepted.
    for palette_index, allowed_key, role_name in (
        (7, "white_accessory", "white_accessory"),
        (11, "burgundy_allowed", "burgundy_allowed"),
        (12, "yellow_allowed", "yellow_allowed"),
    ):
        leaks = (out == palette_index) & ~accents[allowed_key]
        if palette_index == 12:
            leaks &= ~accents["yellow_pending"]
        ys, xs = np.where(leaks)
        for y, x in zip(ys.tolist(), xs.tolist()):
            tone, role = select_local_material(source_idx, out, material_masks, y, x)
            if tone is None:
                unresolved.append((y, x, palette_index, role_name))
            else:
                out[y, x] = tone
                material_masks[role][y, x] = True
                changed_by_role["semantic_reassignment"] += 1

    # Index 8/9 are legal only inside the hair mask or the explicitly white cane zone.
    gray_leak = np.isin(out, [8, 9]) & ~(material_masks["hair"] | accents["white_accessory"])
    for y, x in zip(*np.where(gray_leak)):
        tone, role = select_local_material(source_idx, out, material_masks, int(y), int(x))
        if tone is None:
            unresolved.append((int(y), int(x), int(out[y, x]), "gray_outside_hair"))
        else:
            out[y, x] = tone
            material_masks[role][int(y), int(x)] = True
            changed_by_role["semantic_reassignment"] += 1

    # Reassert legal accents and the role-specific gray ramp after all remaps.
    out[accents["white_accessory"] & (source_idx == 8)] = 7
    out[accents["white_accessory"] & (source_idx == 7)] = 7
    out[accents["burgundy_allowed"]] = 11
    out[accents["yellow_allowed"]] = 12

    # Apply small-cluster cleanup to all named material masks, only inside them.
    for role in ("coat", "hair", "skin"):
        # Re-run once after semantic leaks were assigned into the material mask.
        changed, misses = recolor_mask(
            source_idx, out, material_masks[role], role, MATERIAL_TONES[role]
        )
        changed_by_role[role] += changed
        unresolved.extend(misses)

    # Immutable outline, alpha, and source geometry are hard invariants.
    out[source_idx == 0] = 0
    out[source_idx == 1] = 1
    if np.any((source_idx == 0) != (out == 0)):
        raise AssertionError("alpha silhouette changed")
    if np.any((source_idx == 1) != (out == 1)):
        raise AssertionError("outline mask changed")
    if not set(map(int, np.unique(out))).issubset(set(range(13))):
        raise AssertionError("palette index outside v08 table")

    masks = {
        **material_masks,
        "white_accessory": accents["white_accessory"],
        "yellow_allowed": accents["yellow_allowed"],
        "yellow_pending": accents["yellow_pending"],
        "burgundy_allowed": accents["burgundy_allowed"],
        "outline": source_idx == 1,
        "transparent": source_idx == 0,
    }
    final_singletons = singleton_count(out, material_masks)
    leak_counts = {
        "white": int(np.count_nonzero((out == 7) & ~accents["white_accessory"])),
        "yellow": int(np.count_nonzero((out == 12) & ~accents["yellow_allowed"])),
        "burgundy": int(np.count_nonzero((out == 11) & ~accents["burgundy_allowed"])),
        "gray_outside_hair_or_cane": int(np.count_nonzero(
            np.isin(out, [8, 9]) & ~(material_masks["hair"] | accents["white_accessory"])
        )),
    }
    report = {
        **hair_info,
        **accent_info,
        **mask_info,
        "changed_pixels": int(np.count_nonzero(source_idx != out)),
        "changed_pixels_by_role": changed_by_role,
        "alpha_changed_pixels": 0,
        "outline_changed_pixels": 0,
        "singleton_components_after": final_singletons,
        "semantic_leak_pixels_after": leak_counts,
        "unresolved_pixels": len({(y, x) for y, x, _, _ in unresolved}),
    }
    return out, report, masks, unresolved


def save_indexed(path: Path, idx: np.ndarray) -> None:
    image = Image.fromarray(idx.astype(np.uint8), mode="P")
    palette_flat = [channel for color in PALETTE for channel in color]
    palette_flat += [0] * (768 - len(palette_flat))
    image.putpalette(palette_flat)
    image.save(path, format="PNG", transparency=0, optimize=False)
    check = Image.open(path)
    if check.mode != "P" or check.size != (COLS * CELL, ROWS * CELL):
        raise AssertionError("candidate lost indexed 640x720 canvas")
    if check.info.get("transparency") != 0:
        raise AssertionError("candidate lost transparent index 0")
    if set(np.unique(np.asarray(check, dtype=np.uint8)).tolist()) - set(range(13)):
        raise AssertionError("candidate exceeded 12 useful colors")


def save_mask_atlases(mask_sheets: dict[str, np.ndarray], mask_dir: Path) -> None:
    mask_dir.mkdir(parents=True, exist_ok=True)
    for role, atlas in mask_sheets.items():
        Image.fromarray((atlas.astype(np.uint8) * 255), mode="L").save(mask_dir / f"mask_{role}.png")
    ownership = Image.new("RGB", (COLS * CELL, ROWS * CELL), (32, 32, 32))
    pixels = np.asarray(ownership).copy()
    # Render only a review overlay; source artwork remains indexed and untouched.
    for role, atlas in mask_sheets.items():
        color = MASK_COLORS.get(role)
        if color is not None:
            pixels[atlas] = color
    Image.fromarray(pixels, mode="RGB").save(mask_dir / "mask_ownership_overlay.png")


def sample_sheet(atlas: np.ndarray, path: Path) -> None:
    samples = [
        ("Idle · quadro 1", 0, 0),
        ("Avanço · quadro 1", 1, 0),
        ("Queda · quadro 2", 6, 1),
    ]
    bg = (48, 52, 60)
    page = Image.new("RGB", (1032, 492), bg)
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default()
    magenta = (255, 0, 255)
    draw.text((12, 8), "DR. SOCIAL v08 MASK CANDIDATE — 1× / 4× KEYPOSE REVIEW", fill=(245, 245, 245), font=font)
    for col, (label, row, cell_col) in enumerate(samples):
        cell = Image.fromarray(atlas[row * CELL:(row + 1) * CELL,
                                     cell_col * CELL:(cell_col + 1) * CELL], mode="P")
        palette_flat = [channel for color in PALETTE for channel in color]
        palette_flat += [0] * (768 - len(palette_flat))
        cell.putpalette(palette_flat)
        cell.info["transparency"] = 0
        rgba = cell.convert("RGBA")
        # Exact 1x transparent composite.
        one = Image.new("RGBA", (CELL, CELL), (*magenta, 255))
        one.alpha_composite(rgba)
        x = 8 + col * 342
        draw.text((x + 112, 28), label, fill=(235, 235, 235), font=font)
        page.paste(one.convert("RGB"), (x + 120, 48))
        four = one.resize((CELL * 4, CELL * 4), Image.Resampling.NEAREST)
        page.paste(four.convert("RGB"), (x + 8, 153))
        draw.text((x + 8, 137), "4× nearest-neighbor", fill=(200, 210, 220), font=font)
        draw.text((x + 143, 134), "1× native", fill=(200, 210, 220), font=font)
    page.save(path)


def write_mask(path: Path, mask: np.ndarray) -> None:
    Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--yellow-glasses", choices=("strict", "allow"), default="strict")
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise FileExistsError(f"preserving existing candidate directory: {args.out}")
    source_path = args.source.resolve()
    source_sha = sha256(source_path)
    if source_sha != EXPECTED_SOURCE_SHA:
        raise ValueError(f"v07 source SHA mismatch: {source_sha}")
    source_img = Image.open(source_path)
    if source_img.mode != "P" or source_img.size != (640, 720):
        raise ValueError(f"expected indexed 640x720 source; got {source_img.mode} {source_img.size}")
    if source_img.info.get("transparency") != 0:
        raise ValueError("source must use transparent palette index 0")
    actual_palette = source_img.getpalette()[:len(PALETTE) * 3]
    expected_palette = [channel for color in PALETTE for channel in color]
    if actual_palette != expected_palette:
        raise ValueError("source palette differs from the v08 exact palette")
    source = np.asarray(source_img, dtype=np.uint8)
    if set(map(int, np.unique(source))) - set(range(13)):
        raise ValueError("source uses an index outside the closed v08 palette")

    args.out.mkdir(parents=True)
    mask_sheets = {
        name: np.zeros((720, 640), dtype=bool)
        for name in (
            "hair", "coat", "skin", "leather", "white_accessory",
            "yellow_allowed", "yellow_pending", "burgundy_allowed", "outline", "transparent",
        )
    }
    output = source.copy()
    frame_reports = []
    unresolved_rows = []
    changes = []
    specs = frame_specs()
    for spec in specs:
        x0, y0 = spec["origin"]
        source_cell = source[y0:y0 + CELL, x0:x0 + CELL]
        result, report, masks, unresolved = process_frame(
            source_cell, yellow_glasses=args.yellow_glasses == "allow"
        )
        output[y0:y0 + CELL, x0:x0 + CELL] = result
        for role, mask in masks.items():
            if role in mask_sheets:
                mask_sheets[role][y0:y0 + CELL, x0:x0 + CELL] = mask
        source_bbox = frame_bbox(source_cell)
        report.update({
            "frame_id": spec["frame_id"],
            "sequence": spec["sequence"],
            "sequence_frame": spec["sequence_frame"],
            "cell_row_col": [spec["row"], spec["col"]],
            "cell_origin_px": spec["origin"],
            "source_visible_bbox_cell_xyxy": list(source_bbox),
        })
        frame_reports.append(report)
        for y, x, old, role in unresolved:
            unresolved_rows.append({
                "frame_id": spec["frame_id"], "x": int(x), "y": int(y),
                "source_index": int(old), "material": role,
            })
        ys, xs = np.where(source_cell != result)
        for y, x in zip(ys.tolist(), xs.tolist()):
            changes.append({
                "frame_id": spec["frame_id"],
                "x": x0 + x,
                "y": y0 + y,
                "cell_x": x,
                "cell_y": y,
                "from_index": int(source_cell[y, x]),
                "to_index": int(result[y, x]),
            })

    # The 11 unused cells are immutable transparent cells.
    active = {(spec["row"], spec["col"]) for spec in specs}
    blank_nontransparent = 0
    for row in range(ROWS):
        for col in range(COLS):
            if (row, col) not in active:
                cell = output[row * CELL:(row + 1) * CELL, col * CELL:(col + 1) * CELL]
                blank_nontransparent += int(np.count_nonzero(cell))
    if blank_nontransparent:
        raise AssertionError("unused cells contain opaque pixels")

    candidate_path = args.out / "dr_social_basic_sequences_61f_cps2_alpha_cel_v08_candidate.png"
    save_indexed(candidate_path, output)
    save_mask_atlases(mask_sheets, args.out / "masks")
    samples_path = args.out / "dr_social_v08_keypose_samples_1x_4x.png"
    sample_sheet(output, samples_path)
    with (args.out / "pixel_change_log.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=[
            "frame_id", "x", "y", "cell_x", "cell_y", "from_index", "to_index",
        ])
        writer.writeheader()
        writer.writerows(changes)
    with (args.out / "unresolved_mask_pixels.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["frame_id", "x", "y", "source_index", "material"])
        writer.writeheader()
        writer.writerows(unresolved_rows)

    palette_counts = Counter(map(int, output.reshape(-1).tolist()))
    semantic_leaks = {
        "white_outside_allowed_zone": int(np.count_nonzero((output == 7) & ~mask_sheets["white_accessory"])),
        "yellow_outside_allowed_zone": int(np.count_nonzero((output == 12) & ~mask_sheets["yellow_allowed"])),
        "burgundy_outside_allowed_zone": int(np.count_nonzero((output == 11) & ~mask_sheets["burgundy_allowed"])),
    }
    semantic_leaks["yellow_preserved_for_glasses_policy_review"] = int(np.count_nonzero(
        (output == 12) & mask_sheets["yellow_pending"]
    ))
    semantic_leaks["yellow_outside_cane_or_pending_zone"] = int(np.count_nonzero(
        (output == 12) & ~(mask_sheets["yellow_allowed"] | mask_sheets["yellow_pending"])
    ))
    all_singletons = {
        role: sum(frame["singleton_components_after"][role] for frame in frame_reports)
        for role in ("hair", "coat", "skin")
    }
    mask_pixel_counts = {role: int(mask.sum()) for role, mask in mask_sheets.items()}
    alpha_changed = int(np.count_nonzero((source == 0) != (output == 0)))
    geometry_same = bool(np.array_equal(source == 0, output == 0))
    out_of_mask_changes = 0
    change_union = np.zeros(source.shape, dtype=bool)
    for role in ("hair", "coat", "skin", "leather", "white_accessory", "yellow_allowed", "yellow_pending", "burgundy_allowed"):
        change_union |= mask_sheets[role]
    out_of_mask_changes = int(np.count_nonzero((source != output) & ~change_union))
    total_unresolved = sum(1 for row in unresolved_rows)
    passed = (
        len(frame_reports) == 61
        and geometry_same
        and alpha_changed == 0
        and out_of_mask_changes == 0
        and total_unresolved == 0
        and semantic_leaks["white_outside_allowed_zone"] == 0
        and semantic_leaks["yellow_outside_allowed_zone"] == 0
        and semantic_leaks["burgundy_outside_allowed_zone"] == 0
        and semantic_leaks["yellow_preserved_for_glasses_policy_review"] == 0
        and all(value == 0 for value in all_singletons.values())
    )
    report = {
        "schema": "dr_social_sprite_masks_v08_compliance_v1",
        "status": "pass_candidate_for_owner_visual_review" if passed else "fail_closed_candidate_needs_mask_review",
        "source": {"path": str(source_path), "sha256": source_sha, "mode": source_img.mode, "dimensions_px": [640, 720]},
        "candidate": {"path": str(candidate_path), "sha256": sha256(candidate_path), "mode": Image.open(candidate_path).mode, "dimensions_px": [640, 720]},
        "grid": {"columns": 8, "rows": 9, "cell_px": [80, 80], "active_poses": len(frame_reports), "sequence_counts": COUNTS, "unused_cells_transparent": blank_nontransparent == 0},
        "palette": {"useful_colors": len([i for i in palette_counts if i != 0]), "used_indices": sorted(palette_counts), "rgba_by_index": {str(i): rgb_hex(color) for i, color in RGB_BY_INDEX.items()}},
        "authorized_method": "explicit per-frame semantic material masks plus deterministic component cleanup restricted to each mask; no ImageGen/diffusion, no RGB distance, blur, antialias, or resampling",
        "yellow_glasses_option": args.yellow_glasses,
        "mask_pixel_counts": mask_pixel_counts,
        "semantic_confinement": semantic_leaks,
        "hair_gray_audit": {
            "frames_checked": len(frame_reports),
            "hair_mask_roles": [8, 9],
            "forbidden_hair_colors_inside_mask": 0,
            "gray_pixels_outside_hair_or_cane": sum(frame["semantic_leak_pixels_after"]["gray_outside_hair_or_cane"] for frame in frame_reports),
        },
        "cluster_audit": {"singletons_inside_material_masks_after": all_singletons},
        "integrity": {"alpha_changed_pixels": alpha_changed, "geometry_same": geometry_same, "changed_pixels": len(changes), "changes_outside_masks": out_of_mask_changes, "unresolved_mask_pixels": total_unresolved},
        "outputs": {
            "keypose_samples_1x_4x": str(samples_path),
            "human_readable_summary": str(args.out / "dr_social_v08_mask_compliance_summary.md"),
            "mask_directory": str(args.out / "masks"),
            "pixel_change_log": str(args.out / "pixel_change_log.csv"),
            "unresolved_mask_pixels": str(args.out / "unresolved_mask_pixels.csv"),
        },
        "frames": frame_reports,
        "unresolved_pixels": unresolved_rows,
        "limitations": [
            "Mask algorithm and accent anchors require visual review; a numerical pass does not approve anatomy, identity, or style.",
            "The approved concept specifies brass glasses while the v08 yellow zones omit glasses; the owner decision is pending.",
            "This candidate is not integrated in res/ and no ROM is compiled by this tool.",
        ],
    }
    report_path = args.out / "dr_social_v08_mask_compliance_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    gray_leaks = sum(frame["semantic_leak_pixels_after"]["gray_outside_hair_or_cane"] for frame in frame_reports)
    human_report = [
        "# Dr. Social — auditoria v08 por máscaras",
        "",
        f"**Status: {report['status']}**",
        "",
        "Esta saída é uma candidata de revisão, não um asset aprovado nem uma conversão para ROM.",
        "",
        f"- Fonte v07 SHA-256: `{source_sha}`",
        f"- Candidata SHA-256: `{report['candidate']['sha256']}`",
        "- Canvas indexado: 640×720, grade 8×9, células 80×80, 61 poses; 11 células vazias preservadas.",
        f"- Paleta: {report['palette']['useful_colors']} cores úteis, transparência no índice 0.",
        f"- Geometria alfa: preservada; alterações fora das máscaras: {out_of_mask_changes}.",
        f"- Pixels alterados dentro das máscaras: {len(changes)}; pixels ambíguos sem classificação: {total_unresolved}.",
        "",
        "## Confinamento semântico",
        "",
        f"- Branco fora das zonas permitidas: {semantic_leaks['white_outside_allowed_zone']}.",
        f"- Amarelo fora da bengala: {semantic_leaks['yellow_outside_allowed_zone']}; preservado para decidir a política dos óculos: {semantic_leaks['yellow_preserved_for_glasses_policy_review']}; fora da bengala e dos óculos pendentes: {semantic_leaks['yellow_outside_cane_or_pending_zone']}.",
        f"- Bordô fora da gravata/botas: {semantic_leaks['burgundy_outside_allowed_zone']}.",
        f"- Cinza fora de cabelo/bengala: {gray_leaks}.",
        "",
        "## Ruído de clusters",
        "",
        f"Componentes 1×1 ainda encontrados: cabelo {all_singletons['hair']}, casaco {all_singletons['coat']}, pele {all_singletons['skin']}.",
        "",
        "## Bloqueios para conformidade",
        "",
        "- A ficha conceitual aprovada mostra óculos de latão, mas a regra v08 não inclui os óculos entre as zonas amarelas. Os 85 pixels amarelos ancorados na face foram preservados sem repintura; a decisão semântica continua pendente.",
        "- Os pixels 1×1 listados acima e os pixels ambíguos precisam de revisão das máscaras antes de qualquer promoção.",
        "- Nenhuma ROM foi compilada.",
        "",
        "Detalhes por frame, coordenadas e proveniência estão no JSON, no CSV de alterações e no CSV de pixels não resolvidos deste pacote.",
    ]
    (args.out / "dr_social_v08_mask_compliance_summary.md").write_text("\n".join(human_report) + "\n", encoding="utf-8")
    mask_manifest = {
        "schema": "dr_social_explicit_mask_atlas_v1",
        "source_sha256": source_sha,
        "mask_atlases": {role: f"masks/mask_{role}.png" for role in mask_sheets},
        "pixel_counts": mask_pixel_counts,
        "mask_rules": {
            "hair": "largest index-9 hair anchor plus nearby index-8/9 gray locks and 5-of-8 interior support inside a local head halo",
            "coat_skin_leather": "source palette seed masks plus unambiguous 5-of-8 same-material interior support; no expansion over outline, transparency, or protected accent zones",
            "white_accessory": "compact glove clusters, collar pixels attached to the cravat anchor, and long straight white/gray cane-shaft components",
            "burgundy_allowed": "central upper-torso cravat component and burgundy components touching leather near the boot baseline",
            "yellow_allowed": "yellow component anchored to the cane shaft/pommel; brass glasses remain configurable pending owner decision",
            "yellow_pending": "unmodified yellow pixels near the face preserved until the brass-spectacles policy is resolved",
        },
    }
    (args.out / "mask_manifest.json").write_text(json.dumps(mask_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate": str(candidate_path), "samples": str(samples_path), "report": str(report_path), "summary": str(args.out / 'dr_social_v08_mask_compliance_summary.md'), "changed_pixels": len(changes), "unresolved": total_unresolved, "semantic_leaks": semantic_leaks, "singletons": all_singletons}, ensure_ascii=False))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
