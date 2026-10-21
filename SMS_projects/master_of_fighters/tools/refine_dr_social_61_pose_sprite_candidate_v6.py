#!/usr/bin/env python3
"""Correct material-role color contamination in the v5 Dr. Social atlas."""
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
V5_DIR = ART / "review_drafts/basic_sequences_61f_candidate_v5_source"
V6_DIR = ART / "review_drafts/basic_sequences_61f_candidate_v6_source"
INPUT = ART / "dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v5.png"
INPUT_REPORT = V5_DIR / "dr_social_basic_sequences_candidate_v5_processing_report.json"
OUTPUT = ART / "dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v6.png"
REPORT = V6_DIR / "dr_social_basic_sequences_candidate_v6_processing_report.json"
PREVIEW = V6_DIR / "dr_social_basic_sequences_candidate_v6_preview_4x.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head_region_cleanup(frame: np.ndarray) -> tuple[np.ndarray, dict]:
    """Use the face-to-hair relationship to correct palette-role leaks.

    The largest skin cluster nearest a gray-hair cluster anchors the face.
    Nearby hair clusters define a tight head box. Skin fragments, shirt gray,
    boot brown, and burgundy inside that box but outside the face are recolored
    to hair gray. The face, outline, white highlights, brass, and suit tones
    stay intact. No alpha or geometry changes are made.
    """
    out = frame.copy()
    skin = np.isin(out, [2, 3]).astype(np.uint8)
    hair = (out == 9).astype(np.uint8)
    skin_count, skin_labels, skin_stats, _ = cv2.connectedComponentsWithStats(
        skin, connectivity=8
    )
    hair_count, hair_labels, hair_stats, _ = cv2.connectedComponentsWithStats(
        hair, connectivity=8
    )
    if skin_count <= 1 or hair_count <= 1:
        return out, {"matched": False, "pixels_recolored": 0, "head_bbox": None}

    hair_distance = cv2.distanceTransform(
        (hair == 0).astype(np.uint8), cv2.DIST_L2, 3
    )
    candidates: list[tuple[float, int, int]] = []
    for sid in range(1, skin_count):
        area = int(skin_stats[sid, cv2.CC_STAT_AREA])
        if area < 2:
            continue
        face_component = skin_labels == sid
        distance = float(np.min(hair_distance[face_component]))
        candidates.append((distance, -area, sid))
    if not candidates:
        return out, {"matched": False, "pixels_recolored": 0, "head_bbox": None}

    distance, _negative_area, face_id = min(candidates)
    if distance > 5:
        return out, {"matched": False, "pixels_recolored": 0, "head_bbox": None}
    face = skin_labels == face_id
    face_distance = cv2.distanceTransform(
        (~face).astype(np.uint8), cv2.DIST_L2, 3
    )

    selected_hair = np.zeros_like(face)
    for hid in range(1, hair_count):
        component = hair_labels == hid
        if np.min(face_distance[component]) <= 6:
            selected_hair |= component
    if not np.any(selected_hair):
        return out, {"matched": False, "pixels_recolored": 0, "head_bbox": None}

    ys, xs = np.where(selected_hair | face)
    x0, x1 = max(0, int(xs.min()) - 1), min(80, int(xs.max()) + 2)
    y0, y1 = max(0, int(ys.min()) - 1), min(80, int(ys.max()) + 2)
    head_box = np.zeros_like(face)
    head_box[y0:y1, x0:x1] = True
    likely_leaks = np.isin(out, [2, 3, 8, 10, 11])
    recolor = head_box & ~face & likely_leaks
    count = int(np.count_nonzero(recolor))
    out[recolor] = 9
    return out, {
        "matched": True,
        "face_to_hair_distance_px": round(distance, 3),
        "pixels_recolored": count,
        "head_bbox": [x0, y0, x1 - x0, y1 - y0],
    }


def save_output(sheet: np.ndarray) -> None:
    image = Image.fromarray(sheet, mode="P")
    palette: list[int] = []
    for rgb in v5.ROLE_RGB:
        palette.extend(rgb)
    palette.extend([0] * (768 - len(palette)))
    image.putpalette(palette)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, format="PNG", transparency=0, optimize=False)
    check = Image.open(OUTPUT)
    if check.mode != "P" or check.size != (640, 720) or check.info.get("transparency") != 0:
        raise AssertionError("saída v6 perdeu modo, tamanho ou índice transparente")


def save_preview(sheet: np.ndarray, titles: list[str]) -> None:
    scale, cell, gap, label_h = 4, 320, 8, 20
    page = Image.new(
        "RGB", (8 + 8 * (cell + gap), 8 + 9 * (cell + label_h + gap)),
        (45, 49, 56),
    )
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default()
    for row in range(9):
        y = 8 + row * (cell + label_h + gap)
        draw.text((8, y + 3), f"{row + 1:02d}  {titles[row]}",
                  fill=(230, 233, 238), font=font)
        for col in range(8):
            indices = sheet[row * 80:(row + 1) * 80, col * 80:(col + 1) * 80]
            frame = v5.rgba_frame(indices).resize((cell, cell), Image.Resampling.NEAREST)
            page.paste(frame, (8 + col * (cell + gap), y + label_h), frame)
    V6_DIR.mkdir(parents=True, exist_ok=True)
    page.save(PREVIEW)


def main() -> None:
    if not INPUT.is_file() or not INPUT_REPORT.is_file():
        raise FileNotFoundError("candidata v5 ou relatório ausente")
    if OUTPUT.exists() or REPORT.exists() or PREVIEW.exists():
        raise FileExistsError("saída v6 existente preservada")
    source = Image.open(INPUT)
    if source.mode != "P" or source.size != (640, 720):
        raise ValueError("fonte precisa ser o atlas indexado v5 de 640×720")
    sheet = np.asarray(source, dtype=np.uint8).copy()
    corrections: list[dict] = []
    for row in range(9):
        for col in range(8):
            frame = sheet[row * 80:(row + 1) * 80, col * 80:(col + 1) * 80]
            if np.count_nonzero(frame) == 0:
                continue
            cleaned, details = head_region_cleanup(frame)
            frame[:] = cleaned
            corrections.append({"row": row + 1, "column": col + 1, **details})
    if len(corrections) != 61 or sum(x["matched"] for x in corrections) != 61:
        raise AssertionError("correção semântica não encontrou cabeça em todos os quadros")

    used = sorted(int(v) for v in np.unique(sheet))
    if used != list(range(13)):
        raise AssertionError(f"fechamento da paleta inesperado: {used}")
    for row in range(9):
        active = sum(
            bool(np.any(sheet[row * 80:(row + 1) * 80, col * 80:(col + 1) * 80]))
            for col in range(8)
        )
        if active != v5.EXPECTED[row]:
            raise AssertionError(f"sequência alterada na linha {row + 1}: {active}")
    save_output(sheet)

    previous = json.loads(INPUT_REPORT.read_text())
    titles = list(previous["atlas"]["sequence_rows"].keys())
    save_preview(sheet, titles)
    previous["schema"] = "mof_dr_social_61_pose_refinement_v6"
    previous["candidate_status"] = "candidate_only; independent review and owner approval pending"
    previous["pixel_source"] = {
        "path": "data/source_art/sprite_studies/dr_social/dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v5.png",
        "sha256": sha256(INPUT),
        "role": "intermediate palette-cleaned candidate; v4 concept remains sole identity/design reference",
    }
    previous["refinement"]["operation"] = "v5 cleanup plus head-region material-role correction; no pose redraw or frame reordering"
    previous["refinement"]["head_color_role_correction"] = {
        "rule": "identify the largest skin cluster nearest gray hair; preserve that face cluster and recolor adjacent off-material hair pixels inside a tight head box to hair_gray",
        "frames_matched": len(corrections),
        "pixels_recolored": sum(x["pixels_recolored"] for x in corrections),
        "per_frame": corrections,
    }
    previous["output"]["path"] = "data/source_art/sprite_studies/dr_social/dr_social_basic_sequences_61f_cps2_alpha_cel_candidate_v6.png"
    previous["output"]["sha256"] = sha256(OUTPUT)
    previous["output"]["palette_indices_used"] = used
    previous["output"]["opaque_indices_used"] = used[1:]
    previous["validation_scope"]["passed"].append(
        "head/hair palette-role cleanup matched and corrected all 61 frames"
    )
    previous["validation_scope"]["pending_human_review"] = [
        "anatomy and action readability across all 61 frames",
        "fidelity to approved concept v4, including cane, coat, face, and body type",
        "pixel clusters, hair/skin boundary, outlines, and cel shading at native 80×80 and nearest-neighbor enlargement",
        "animation timing/physics and sequence transitions",
    ]
    previous["validation_scope"]["not_claimed"] = [
        "owner approval", "ROM integration", "Master System runtime palette allocation",
        "resource/scanline budget validation", "emulator validation or production readiness",
    ]
    V6_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(previous, indent=2) + "\n")
    print(f"candidate: {OUTPUT}")
    print(f"sha256: {previous['output']['sha256']}")
    print("frames with head match: 61/61")
    print(f"head role corrections: {sum(x['pixels_recolored'] for x in corrections)} pixels")
    print(f"preview: {PREVIEW}")
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
