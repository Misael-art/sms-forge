#!/usr/bin/env python3
"""Remove bright accent pixels outside Dr. Social's semantic roles.

The v9 diagnostic starts from the reviewed v8 color-cluster candidate. It keeps
yellow only when the component belongs to the face/eye-glasses or the cane grip
at the gloved hand; isolated gold clothing marks and the cane's ground tip are
recolored from their local material. Geometry, alpha, pose IDs, and palette are
immutable. This tool creates a review candidate, not production art.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
sys.path.insert(0, str(PROJECT / "tools"))
sys.path.insert(0, str(ROOT / "tools/sms_wrapper"))

import prepare_dr_social_61_pose_probe as base  # noqa: E402
from png_io import read_indexed_png  # noqa: E402

V8 = PROJECT / "out/diagnostics/dr_social_61_pose_review_v8"
V9 = PROJECT / "out/diagnostics/dr_social_61_pose_review_v9"
K3 = np.ones((3, 3), np.uint8)
K5 = np.ones((5, 5), np.uint8)


def color_index(colors: list[tuple[int, int, int]], rgb: tuple[int, int, int]) -> int:
    hits = [i for i, color in enumerate(colors) if tuple(color) == rgb]
    if len(hits) != 1:
        raise ValueError(f"cor esperada ausente/ambígua: {rgb}")
    return hits[0]


def dilate(mask: np.ndarray, kernel: np.ndarray, iterations: int = 1) -> np.ndarray:
    return cv2.dilate(mask.astype(np.uint8), kernel, iterations=iterations).astype(bool)


def local_material(indices: np.ndarray, component: np.ndarray, yellow: int,
                   transparent: int) -> tuple[np.ndarray, int]:
    """Use the immediate neighboring cluster so a leak cannot become a new fleck."""
    replacements = indices.copy()
    component_dilated = dilate(component, K3)
    ring = component_dilated & ~component
    ring_values = indices[ring]
    ring_values = ring_values[(ring_values != yellow) & (ring_values != transparent)]
    if ring_values.size == 0:
        replacements[component] = transparent
        return replacements, int(np.count_nonzero(component))
    ring_counts = Counter(ring_values.tolist())
    fallback = min(ring_counts, key=lambda value: (-ring_counts[value], value))
    ys, xs = np.where(component)
    for y, x in zip(ys.tolist(), xs.tolist()):
        y0, y1 = max(0, y - 1), min(indices.shape[0], y + 2)
        x0, x1 = max(0, x - 1), min(indices.shape[1], x + 2)
        region = indices[y0:y1, x0:x1]
        local_component = component[y0:y1, x0:x1]
        valid = (region != yellow) & (region != transparent) & ~local_component
        values = region[valid].tolist()
        if not values:
            replacements[y, x] = fallback
            continue
        counts = Counter(values)
        replacements[y, x] = min(counts, key=lambda value: (-counts[value], value))
    return replacements, 0


def clean_yellow_roles(indices: np.ndarray,
                       colors: list[tuple[int, int, int]]) -> tuple[np.ndarray, dict]:
    """Keep yellow in face detail and cane pommel; recolor other components."""
    if indices.shape != (base.FRAME_H, base.FRAME_W):
        raise ValueError(f"canvas inesperada: {indices.shape}")
    output = indices.astype(np.uint8, copy=True)
    yellow = color_index(colors, (255, 255, 0))
    white = color_index(colors, (255, 255, 255))
    gray = color_index(colors, (170, 170, 170))
    hair = color_index(colors, (85, 85, 85))
    transparent = 0

    # Skin colors also occur on hands/feet, so they cannot anchor the face by
    # themselves. Use the largest gray-hair cluster for glasses/eye accents.
    # A compact white cluster marks the glove; a long, narrow white/gray
    # component marks the cane shaft. Preserve the pommel only where both meet.
    hair_count, hair_labels, hair_stats, _ = cv2.connectedComponentsWithStats(
        (output == hair).astype(np.uint8), connectivity=8
    )
    if hair_count <= 1:
        raise ValueError("não foi encontrado cluster de cabelo para fixar a região facial")
    hair_label = max(range(1, hair_count),
                     key=lambda label: int(hair_stats[label, cv2.CC_STAT_AREA]))
    hair_cluster = hair_labels == hair_label
    if int(np.count_nonzero(hair_cluster)) < 8:
        raise ValueError("cluster de cabelo demasiado pequeno para ancorar acentos faciais")
    face_neighborhood = dilate(hair_cluster, K5)
    white_mask = output == white
    white_count, white_labels, white_stats, _ = cv2.connectedComponentsWithStats(
        white_mask.astype(np.uint8), connectivity=8
    )
    glove_mask = np.zeros(output.shape, dtype=bool)
    for label in range(1, white_count):
        area = int(white_stats[label, cv2.CC_STAT_AREA])
        width = int(white_stats[label, cv2.CC_STAT_WIDTH])
        height = int(white_stats[label, cv2.CC_STAT_HEIGHT])
        if area >= 6 and width >= 3 and height >= 3 and max(width, height) <= 8:
            glove_mask |= white_labels == label
    glove_neighborhood = dilate(glove_mask, K5)

    neutral_mask = np.isin(output, [white, gray])
    neutral_count, neutral_labels, neutral_stats, _ = cv2.connectedComponentsWithStats(
        neutral_mask.astype(np.uint8), connectivity=8
    )
    shaft_mask = np.zeros(output.shape, dtype=bool)
    for label in range(1, neutral_count):
        area = int(neutral_stats[label, cv2.CC_STAT_AREA])
        width = int(neutral_stats[label, cv2.CC_STAT_WIDTH])
        height = int(neutral_stats[label, cv2.CC_STAT_HEIGHT])
        major, minor = max(width, height), min(width, height)
        if area >= 8 and major >= 8 and major >= minor * 3:
            shaft_mask |= neutral_labels == label
    shaft_neighborhood = dilate(shaft_mask, np.ones((9, 9), np.uint8))

    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (output == yellow).astype(np.uint8), connectivity=8
    )
    kept_face = kept_cane = changed_pixels = changed_components = alpha_removed = 0
    for label in range(1, count):
        component = labels == label
        if np.any(component & face_neighborhood):
            kept_face += int(stats[label, cv2.CC_STAT_AREA])
            continue
        if (np.any(component & glove_neighborhood)
                and np.any(component & shaft_neighborhood)):
            kept_cane += int(stats[label, cv2.CC_STAT_AREA])
            continue
        replacement, removed = local_material(output, component, yellow, transparent)
        changed_pixels += int(np.count_nonzero(component))
        changed_components += 1
        alpha_removed += removed
        output[component] = replacement[component]

    if np.any(output == yellow) and not np.array_equal(output == yellow, indices == yellow):
        pass
    alpha_delta = int(np.count_nonzero((output == transparent) != (indices == transparent)))
    if alpha_delta != alpha_removed:
        raise AssertionError("delta alfa diverge da remoção de acentos isolados")
    if not set(map(int, np.unique(output))).issubset(set(range(len(colors)))):
        raise AssertionError("a limpeza semântica criou índice fora da paleta")
    return output, {
        "yellow_pixels_reassigned_outside_face_and_cane_grip": changed_pixels,
        "yellow_components_reassigned": changed_components,
        "yellow_pixels_kept_as_face_detail": kept_face,
        "yellow_pixels_kept_as_cane_pommel": kept_cane,
        "alpha_changed_pixels": alpha_delta,
        "new_palette_colors": 0,
    }


def self_check(colors: list[tuple[int, int, int]]) -> None:
    yellow = color_index(colors, (255, 255, 0))
    white = color_index(colors, (255, 255, 255))
    hair = color_index(colors, (85, 85, 85))
    skin = color_index(colors, (255, 170, 170))
    gray = color_index(colors, (170, 170, 170))
    shadow = color_index(colors, (0, 85, 85))
    mid = color_index(colors, (0, 170, 170))
    test = np.full((80, 80), mid, dtype=np.uint8)
    test[10:14, 10:14] = hair
    test[13:15, 10:14] = skin
    test[11, 14] = yellow  # glasses/eye detail beside face
    test[35:40, 35:40] = white  # compact glove
    test[38:58, 40] = gray  # straight cane shaft
    test[39, 41] = yellow  # cane pommel at hand/shaft junction
    test[50, 50] = yellow  # isolated yellow on cloth
    test[58, 40] = yellow  # cane tip without a hand
    test[68:73, 68:73] = 0
    test[70, 70] = yellow  # disconnected contour speck
    clean, report = clean_yellow_roles(test, colors)
    assert clean[11, 14] == yellow, "face accent was removed"
    assert clean[39, 41] == yellow, "cane pommel was removed"
    assert clean[50, 50] != yellow, "cloth confetti remained"
    assert clean[58, 40] != yellow, "yellow cane tip remained"
    assert clean[70, 70] == 0, "disconnected contour speck remained visible"
    assert report["alpha_changed_pixels"] == 1
    assert np.all(clean[0] == mid)
    print("[SELF-CHECK OK] face/cane semantic accents kept; cloth/tip yellow removed")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_candidate() -> dict:
    if V9.exists() and any(V9.iterdir()):
        raise FileExistsError(f"saída existente preservada: {V9}")
    outer_v8 = json.loads((V8 / "conversion_report_61_pose_v8.json").read_text())
    internal_v8_path = V8 / "project/doc/conversion_report_61_pose_v8.json"
    internal_v8 = json.loads(internal_v8_path.read_text())
    colors, palette_codes = base.palette_from_approved_study(base.PALETTE_SOURCE)
    contract = json.loads(base.CONTRACT.read_text())
    source, source_sha = base.validate_owner_source(base.DEFAULT_SOURCE)
    source_rgba = np.asarray(base.Image.open(source).convert("RGBA"))
    source_rows, labels = base.group_components(source_rgba)
    V9.mkdir(parents=True)
    prepared = V9 / "prepared_frames"
    prepared.mkdir()
    project = V9 / "project"
    cleanup_by_id = {}
    frames = []
    source_by_id = {}
    for row, sequence in zip(source_rows, contract["sequences"][:9]):
        if len(row) != sequence["source_pose_count"]:
            raise ValueError(f"{sequence['id']}: sequência-fonte mudou de tamanho")
        for pose_index, component in enumerate(row):
            frame_id = sequence["frame_ids"][pose_index]
            filename = f"dr_social_{sequence['id']}_{frame_id.lower()}_sms_80px.png"
            source_path = V8 / "project/res/sprites" / filename
            source_png = read_indexed_png(str(source_path))
            pixels = np.asarray([list(line) for line in source_png["pixels"]], dtype=np.uint8)
            refined, cleanup = clean_yellow_roles(pixels, colors)
            dest = prepared / filename
            base.write_pose_png(dest, refined, colors)
            _converted, conversion = base.convert_component(
                source_rgba, component, colors, labels
            )
            frame = {
                "frame_id": frame_id,
                "sequence_id": sequence["id"],
                "sequence_title": sequence["title"],
                "file_name": filename,
                "png_path": str(dest),
                "conversion": conversion,
            }
            frames.append(frame)
            cleanup_by_id[frame_id] = cleanup
            source_by_id[frame_id] = source_path

    if len(frames) != 61:
        raise AssertionError("a nova candidata não contém exatamente 61 quadros")
    internal = base.build_project(
        project, source, source_sha, source_rows, frames, colors,
        palette_codes, contract
    )
    preview_rows = [[{} for _ in row] for row in source_rows]
    base.make_preview(V9 / "dr_social_61_pose_converted_preview_4x.png",
                      preview_rows, frames, colors)

    project_file = project / ".mddev/project.json"
    project_data = json.loads(project_file.read_text())
    project_data["name"] = "dr_social_61_pose_review_v9"
    project_file.write_text(json.dumps(project_data, indent=2) + "\n")
    main_file = project / "src/main.c"
    main_file.write_text(main_file.read_text().replace(
        "Dr Social 61 pose review v7", "Dr Social 61 pose review v9"
    ))

    delta_rows = []
    total_changed = 0
    for frame in internal["frames"]:
        name = Path(frame["res_path"]).name
        before = np.asarray([list(line) for line in read_indexed_png(
            str(source_by_id[frame["frame_id"]])
        )["pixels"]], dtype=np.uint8)
        after = np.asarray([list(line) for line in read_indexed_png(
            str(project / frame["res_path"])
        )["pixels"]], dtype=np.uint8)
        changed = int(np.count_nonzero(before != after))
        total_changed += changed
        delta_rows.append({"frame_id": frame["frame_id"], "changed_pixels": changed})
        frame["semantic_palette_cleanup"] = cleanup_by_id[frame["frame_id"]]
    if total_changed != sum(
            item["yellow_pixels_reassigned_outside_face_and_cane_grip"]
            for item in cleanup_by_id.values()):
        raise AssertionError("delta por quadro não fecha com o relatório semântico")

    palette_indices = set(map(int, np.unique(np.concatenate([
        np.asarray([list(line) for line in read_indexed_png(
            str(project / frame["res_path"])
        )["pixels"]], dtype=np.uint8).ravel()
        for frame in internal["frames"]
    ]))))
    if not palette_indices.issubset(set(range(len(colors)))):
        raise AssertionError("índice novo detectado no conjunto v9")

    internal["schema"] = "dr_social_sms_61_pose_rom_review_v9"
    internal["rom"] = {"path": "pending build", "sha256": None,
                       "bytes": None, "build_status": "pending",
                       "production_status": "diagnostic_candidate_only"}
    internal["framebuffer_verification"] = {"status": "pending rebuild and capture",
                                               "exact_render_passes": 0,
                                               "exact_render_failures": 61}
    yellow_reassigned = sum(
        entry["yellow_pixels_reassigned_outside_face_and_cane_grip"]
        for entry in cleanup_by_id.values()
    )
    alpha_removed = sum(entry["alpha_changed_pixels"]
                        for entry in cleanup_by_id.values())
    internal["material_cluster_conversion"] = {
        "base_candidate": "v8 contiguous hard-edged cloth planes",
        "v8_cluster_delta": {"changed_pixels": 927,
                             "cloth_tone_islands": 438,
                             "enclosed_navy_marks": 489},
        "refinement": "anchor face accents to the largest gray-hair cluster; preserve cane pommel only at the gloved hand/shaft junction; recolor out-of-role yellow components from immediate neighbors; remove detached yellow contour specks; no dithering or new colors",
        "yellow_pixels_reassigned_outside_face_and_cane_grip": yellow_reassigned,
        "white_pixels_reassigned": 0,
        "white_accent_review": "white cluster unchanged; inspect gloves, shirt/collar and cane shaft at 1x and nearest-neighbor 4x",
        "alpha_changed_pixels": alpha_removed,
        "new_palette_colors": 0,
        "pose_geometry_changed": False,
    }
    internal["owner_review"] = {"v7": "rejected_by_owner",
                                "v8": "superseded_by_v9_candidate",
                                "v9": "pending_independent_review_and_owner_approval"}
    old_report = project / "doc/conversion_report_61_pose_v7.json"
    old_manifest = project / "doc/frame_manifest_61_pose_v7.json"
    old_report.rename(
        project / "doc/conversion_report_61_pose_v9.json"
    )
    old_manifest.rename(
        project / "doc/frame_manifest_61_pose_v9.json"
    )
    (project / "doc/conversion_report_61_pose_v9.json").write_text(
        json.dumps(internal, indent=2, ensure_ascii=False) + "\n"
    )

    outer_v8["schema"] = "dr_social_sms_61_pose_rom_review_v9"
    outer_v8["status"] = "diagnostic_candidate_not_production"
    outer_v8["project"] = str(project)
    outer_v8["owner_review"] = internal["owner_review"]
    outer_v8["rom"] = internal["rom"]
    outer_v8["framebuffer_verification"] = internal["framebuffer_verification"]
    outer_v8["material_cluster_conversion"] = internal["material_cluster_conversion"]
    cleanup_by_frame = {frame_id: cleanup for frame_id, cleanup in cleanup_by_id.items()}
    for frame in outer_v8["frames"]:
        frame["semantic_palette_cleanup"] = cleanup_by_frame[frame["frame_id"]]
    outer_v8["pending"] = list(dict.fromkeys(outer_v8.get("pending", []) + [
        "revisão semântica independente dos acentos amarelos em 61 poses",
        "rebuild e captura exata de todos os 61 quadros da candidata v9",
        "aprovação do dono e revisão artística independente",
    ]))
    (V9 / "conversion_report_61_pose_v9.json").write_text(
        json.dumps(outer_v8, indent=2, ensure_ascii=False) + "\n"
    )
    delta = {
        "schema": "dr_social_semantic_accent_delta_v8_v9",
        "status": "pass",
        "frames_checked": len(delta_rows),
        "changed_pixels": total_changed,
        "alpha_changed_pixels": alpha_removed,
        "new_palette_colors": 0,
        "geometry_pose_ids_preserved": True,
        "frames": delta_rows,
        "limit": "Pixel invariants only; artistic role, anatomy and material review remain human gates.",
    }
    (V9 / "dr_social_61_pose_semantic_delta_v8_v9.json").write_text(
        json.dumps(delta, indent=2, ensure_ascii=False) + "\n"
    )
    summary = {
        "status": "diagnostic_candidate_pending_review",
        "frames": len(delta_rows),
        "changed_pixels": total_changed,
        "yellow_reassigned": internal["material_cluster_conversion"][
            "yellow_pixels_reassigned_outside_face_and_cane_grip"
        ],
        "preview": str(V9 / "dr_social_61_pose_converted_preview_4x.png"),
        "project": str(project),
        "rom_status": "pending build and 61-frame exact framebuffer review",
    }
    (V9 / "candidate_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    colors, _codes = base.palette_from_approved_study(base.PALETTE_SOURCE)
    if args.self_check:
        self_check(colors)
        return 0
    print(json.dumps(build_candidate(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
