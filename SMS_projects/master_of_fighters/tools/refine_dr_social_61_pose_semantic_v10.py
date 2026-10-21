#!/usr/bin/env python3
"""Role-aware removal of isolated white pixels from the 61-pose candidate.

V10 starts from the v9 diagnostic candidate. It preserves long straight white/gray segments as cane-shaft candidates and
leaves all larger white clusters unchanged for human role review; it reassigns
white components of one or two pixels outside that shaft mask to the local
existing material color. Larger ambiguous clusters remain for human semantic review.
This creates a candidate only, never production art.
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
sys.path.insert(0, str(PROJECT / "tools"))

import prepare_dr_social_61_pose_probe as base  # noqa: E402
from png_io import read_indexed_png  # noqa: E402

BASE_V9 = PROJECT / "out/diagnostics/dr_social_61_pose_review_v9"
V10 = PROJECT / "out/diagnostics/dr_social_61_pose_review_v10"
K3 = np.ones((3, 3), np.uint8)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def color_index(colors: list[tuple[int, int, int]], rgb: tuple[int, int, int]) -> int:
    hits = [i for i, color in enumerate(colors) if tuple(color) == rgb]
    if len(hits) != 1:
        raise ValueError(f"cor esperada ausente/ambígua: {rgb}")
    return hits[0]


def line_ratio(mask: np.ndarray) -> float:
    ys, xs = np.where(mask)
    if len(xs) < 3:
        return 0.0
    xy = np.column_stack((xs, ys)).astype(float)
    eigenvalues = np.linalg.eigvalsh(np.cov(xy.T))
    return float(eigenvalues[-1] / max(eigenvalues[0], 1e-6))


def cane_shaft_mask(indices: np.ndarray, white: int, gray: int) -> np.ndarray:
    """Recognize long, straight cane segments, including diagonal shafts."""
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        np.isin(indices, [white, gray]).astype(np.uint8), connectivity=8
    )
    shaft = np.zeros(indices.shape, dtype=bool)
    for label in range(1, count):
        x, y, width, height, area = map(int, stats[label])
        component = labels == label
        if (area >= 7 and max(width, height) >= 8
                and line_ratio(component) >= 4.0):
            shaft |= component
    # Preserve a two-pixel terminal fragment where a shaft is interrupted by
    # its outline or pommel; this is geometry-aware cleanup, not a broad halo.
    return cv2.dilate(shaft.astype(np.uint8), K3).astype(bool)


def local_recolor(indices: np.ndarray, component: np.ndarray,
                  white: int, transparent: int = 0) -> tuple[np.ndarray, int]:
    """Replace leaked white using the immediate material ring; never add RGB."""
    result = indices.copy()
    ring = cv2.dilate(component.astype(np.uint8), K3).astype(bool) & ~component
    values = indices[ring]
    values = values[(values != white) & (values != transparent)]
    if values.size == 0:
        result[component] = transparent
        return result, int(np.count_nonzero(component))
    counts = Counter(values.tolist())
    fallback = min(counts, key=lambda value: (-counts[value], value))
    ys, xs = np.where(component)
    for y, x in zip(ys.tolist(), xs.tolist()):
        region = indices[max(0, y-1):min(indices.shape[0], y+2),
                         max(0, x-1):min(indices.shape[1], x+2)]
        valid = region[(region != white) & (region != transparent)]
        if valid.size:
            local_counts = Counter(valid.tolist())
            result[y, x] = min(local_counts, key=lambda value: (-local_counts[value], value))
        else:
            result[y, x] = fallback
    return result, 0


def clean_white_specks(indices: np.ndarray,
                       colors: list[tuple[int, int, int]]) -> tuple[np.ndarray, dict]:
    """Remove only isolated white specks outside gloves/cane; preserve other clusters for review."""
    if indices.shape != (base.FRAME_H, base.FRAME_W):
        raise ValueError(f"canvas inesperada: {indices.shape}")
    output = indices.astype(np.uint8, copy=True)
    white = color_index(colors, (255, 255, 255))
    gray = color_index(colors, (170, 170, 170))
    transparent = 0
    shaft = cane_shaft_mask(output, white, gray)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (output == white).astype(np.uint8), connectivity=8
    )
    changed = changed_components = alpha_removed = preserved_shaft = preserved_cluster = 0
    for label in range(1, count):
        component = labels == label
        area = int(stats[label, cv2.CC_STAT_AREA])
        if np.any(component & shaft):
            preserved_shaft += area
            continue
        # Leave larger clusters unchanged for visual role review. Isolated
        # singles and pairs cannot form a readable glove/collar, so treat them
        # as leaks unless the shaft detector anchored them to the cane.
        if area > 2:
            preserved_cluster += area
            continue
        recolored, removed = local_recolor(output, component, white, transparent)
        changed += area
        changed_components += 1
        alpha_removed += removed
        output[component] = recolored[component]
    alpha_delta = int(np.count_nonzero((output == transparent) != (indices == transparent)))
    if alpha_delta != alpha_removed:
        raise AssertionError("delta alfa diverge da remoção semântica branca")
    if not set(map(int, np.unique(output))).issubset(set(range(len(colors)))):
        raise AssertionError("limpeza criou índice fora da paleta")
    remaining_specks = 0
    final_count, final_labels, final_stats, _ = cv2.connectedComponentsWithStats(
        (output == white).astype(np.uint8), connectivity=8
    )
    final_shaft = cane_shaft_mask(output, white, gray)
    for label in range(1, final_count):
        component = final_labels == label
        area = int(final_stats[label, cv2.CC_STAT_AREA])
        if area <= 2 and not np.any(component & final_shaft):
            remaining_specks += area
    return output, {
        "white_pixels_reassigned_outside_cane_and_preserved_clusters": changed,
        "white_components_reassigned": changed_components,
        "white_pixels_preserved_on_cane_shaft": preserved_shaft,
        "white_pixels_preserved_in_larger_clusters_for_visual_review": preserved_cluster,
        "remaining_unanchored_white_singletons_or_pairs": remaining_specks,
        "alpha_changed_pixels": alpha_delta,
        "new_palette_colors": 0,
    }


def self_check(colors: list[tuple[int, int, int]]) -> None:
    white = color_index(colors, (255, 255, 255))
    gray = color_index(colors, (170, 170, 170))
    cyan = color_index(colors, (0, 170, 170))
    navy = color_index(colors, (0, 0, 85))
    maroon = color_index(colors, (85, 0, 0))
    test = np.full((80, 80), cyan, dtype=np.uint8)
    test[8:14, 8:14] = 0
    test[20:24, 20:24] = white  # glove cluster survives
    test[24:26, 20:24] = maroon
    test[10:35, 40] = white    # vertical cane shaft survives
    test[35:40, 40] = gray
    test[42:47, 40:45] = white # large non-shaft cluster remains for review
    test[55, 55] = white      # clothing singleton is recolored
    test[60, 60:62] = white   # clothing pair is recolored
    clean, report = clean_white_specks(test, colors)
    assert np.all(clean[20:24, 20:24] == white)
    assert np.all(clean[10:35, 40] == white)
    assert np.all(clean[42:47, 40:45] == white)
    assert clean[55, 55] != white and np.all(clean[60, 60:62] != white)
    assert report["white_pixels_reassigned_outside_cane_and_preserved_clusters"] == 3
    assert report["remaining_unanchored_white_singletons_or_pairs"] == 0
    assert report["alpha_changed_pixels"] == 0
    print("[SELF-CHECK OK] isolated white specks removed; shaft/large clusters preserved")


def build_candidate() -> dict:
    if V10.exists() and any(V10.iterdir()):
        raise FileExistsError(f"saída existente preservada: {V10}")
    v9_project = BASE_V9 / "project"
    v9_inner = json.loads((v9_project / "doc/conversion_report_61_pose_v9.json").read_text())
    v9_outer = json.loads((BASE_V9 / "conversion_report_61_pose_v9.json").read_text())
    colors, palette_codes = base.palette_from_approved_study(base.PALETTE_SOURCE)
    source, source_sha = base.validate_owner_source(base.DEFAULT_SOURCE)
    source_rgba = np.asarray(base.Image.open(source).convert("RGBA"))
    source_rows, labels = base.group_components(source_rgba)
    contract = json.loads(base.CONTRACT.read_text())
    V10.mkdir(parents=True)
    prepared = V10 / "prepared_frames"
    prepared.mkdir()
    project = V10 / "project"
    frames = []
    white_by_id = {}
    source_by_id = {}
    v9_by_id = {frame["frame_id"]: frame for frame in v9_inner["frames"]}
    for row, sequence in zip(source_rows, contract["sequences"][:9]):
        if len(row) != sequence["source_pose_count"]:
            raise ValueError(f"{sequence['id']}: sequência-fonte mudou de tamanho")
        for pose_index, component in enumerate(row):
            frame_id = sequence["frame_ids"][pose_index]
            filename = f"dr_social_{sequence['id']}_{frame_id.lower()}_sms_80px.png"
            source_path = v9_project / "res/sprites" / filename
            pixels = np.asarray([list(line) for line in read_indexed_png(str(source_path))["pixels"]], dtype=np.uint8)
            refined, white_report = clean_white_specks(pixels, colors)
            dest = prepared / filename
            base.write_pose_png(dest, refined, colors)
            _converted, conversion = base.convert_component(source_rgba, component, colors, labels)
            frames.append({
                "frame_id": frame_id, "sequence_id": sequence["id"],
                "sequence_title": sequence["title"], "file_name": filename,
                "png_path": str(dest), "conversion": conversion,
            })
            white_by_id[frame_id] = white_report
            source_by_id[frame_id] = source_path
    if len(frames) != 61:
        raise AssertionError("a nova candidata não contém exatamente 61 quadros")
    internal = base.build_project(project, source, source_sha, source_rows, frames, colors, palette_codes, contract)
    preview_path = V10 / "dr_social_61_pose_converted_preview_4x.png"
    base.make_preview(preview_path, [[{} for _ in row] for row in source_rows], frames, colors)
    project_file = project / ".mddev/project.json"
    project_data = json.loads(project_file.read_text())
    project_data["name"] = "dr_social_61_pose_review_v10"
    project_file.write_text(json.dumps(project_data, indent=2) + "\n")
    main_file = project / "src/main.c"
    main_file.write_text(main_file.read_text().replace("Dr Social 61 pose review v7", "Dr Social 61 pose review v10"))
    total_changed = 0
    frame_deltas = []
    for frame in internal["frames"]:
        source_png = source_by_id[frame["frame_id"]]
        output_png = project / frame["res_path"]
        before = np.asarray([list(x) for x in read_indexed_png(str(source_png))["pixels"]], dtype=np.uint8)
        after = np.asarray([list(x) for x in read_indexed_png(str(output_png))["pixels"]], dtype=np.uint8)
        count = int(np.count_nonzero(before != after))
        total_changed += count
        frame_deltas.append({"frame_id": frame["frame_id"], "changed_pixels": count})
        frame["semantic_white_cleanup"] = white_by_id[frame["frame_id"]]
    alpha_delta = sum(x["semantic_white_cleanup"]["alpha_changed_pixels"] for x in internal["frames"])
    if total_changed != sum(x["white_pixels_reassigned_outside_cane_and_preserved_clusters"] for x in white_by_id.values()):
        raise AssertionError("delta não fecha com as reatribuições brancas reportadas")
    if alpha_delta != 0:
        raise AssertionError("a limpeza branca alterou alpha inesperadamente")
    internal["schema"] = "dr_social_sms_61_pose_rom_review_v10"
    internal["rom"] = {"path": "pending build", "sha256": None, "bytes": None,
                       "build_status": "pending", "production_status": "diagnostic_candidate_only"}
    internal["framebuffer_verification"] = {"status": "pending rebuild and 61-frame exact capture",
                                              "exact_render_passes": 0, "exact_render_failures": 61}
    internal["white_semantic_refinement"] = {
        "base_candidate": "v9; yellow accents already reclassified by face/hair and glove/shaft anchors",
        "white_policy": "preserve long straight white/gray cane segments and larger glove/collar clusters; recolor isolated white singles/pairs outside the cane mask using immediate local material colors",
        "white_pixels_reassigned": total_changed,
        "alpha_changed_pixels": alpha_delta,
        "new_palette_colors": 0,
        "pose_geometry_changed": False,
        "ambiguous_clusters": "larger white clusters retained for independent visual review; semantic axis remains pending",
    }
    internal["owner_review"] = {"v7": "rejected_by_owner", "v8": "superseded", "v9": "superseded_after_white_leak_double_check",
                                "v10": "pending_independent_visual_review_and_owner_approval"}
    (project / "doc/conversion_report_61_pose_v7.json").rename(project / "doc/conversion_report_61_pose_v10.json")
    (project / "doc/frame_manifest_61_pose_v7.json").rename(project / "doc/frame_manifest_61_pose_v10.json")
    (project / "doc/conversion_report_61_pose_v10.json").write_text(json.dumps(internal, indent=2, ensure_ascii=False) + "\n")
    outer = v9_outer
    outer["schema"] = "dr_social_sms_61_pose_rom_review_v10"
    outer["status"] = "diagnostic_candidate_not_production"
    outer["project"] = str(project)
    outer["owner_review"] = internal["owner_review"]
    outer["rom"] = internal["rom"]
    outer["framebuffer_verification"] = internal["framebuffer_verification"]
    outer["white_semantic_refinement"] = internal["white_semantic_refinement"]
    for frame in outer["frames"]:
        frame["semantic_white_cleanup"] = white_by_id[frame["frame_id"]]
    outer["pending"] = list(dict.fromkeys(outer.get("pending", []) + [
        "dupla revisão visual independente de branco restante em luvas, gola e bengala em 61 poses",
        "rebuild e captura exata dos 61 quadros da candidata v10",
        "aprovação explícita do dono e revisão artística independente",
    ]))
    (V10 / "conversion_report_61_pose_v10.json").write_text(json.dumps(outer, indent=2, ensure_ascii=False) + "\n")
    delta = {
        "schema": "dr_social_white_semantic_delta_v9_v10", "status": "pass",
        "frames_checked": len(frame_deltas), "changed_pixels": total_changed,
        "alpha_changed_pixels": alpha_delta, "new_palette_colors": 0,
        "geometry_pose_ids_preserved": True, "frames": frame_deltas,
        "limit": "Only isolated white singles/pairs outside geometric cane mask were remapped; larger clusters still require human semantic review.",
    }
    (V10 / "dr_social_61_pose_white_semantic_delta_v9_v10.json").write_text(json.dumps(delta, indent=2, ensure_ascii=False) + "\n")
    summary = {
        "status": "diagnostic_candidate_pending_independent_art_review_and_owner_approval",
        "frames": 61, "white_pixels_reassigned": total_changed,
        "yellow_pixels_reassigned_v9": 249, "alpha_changed_pixels": alpha_delta,
        "preview": str(preview_path), "project": str(project),
        "rom_status": "pending build and exact 61-frame framebuffer review",
    }
    (V10 / "candidate_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    colors, _ = base.palette_from_approved_study(base.PALETTE_SOURCE)
    if args.self_check:
        self_check(colors)
        return 0
    print(json.dumps(build_candidate(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
