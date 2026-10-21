#!/usr/bin/env python3
"""Refine Dr. Social's SMS 61-pose candidate into clean cel-shaded clusters.

This is a palette-closed post-conversion step. It changes interior color
clusters only; sprite geometry, alpha, IDs, timing, and semantic accent regions
remain fixed. Output is a review candidate, never production art by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[1]
sys.path.insert(0, str(PROJECT / "tools"))

import prepare_dr_social_61_pose_probe as base  # noqa: E402

DEFAULT_BASE = PROJECT / "out/diagnostics/dr_social_61_pose_review_v7"
DEFAULT_OUTPUT = PROJECT / "out/diagnostics/dr_social_61_pose_review_v8"
FRAME_COUNT = 61
KERNEL_3 = np.ones((3, 3), np.uint8)
KERNEL_3[1, 1] = 0
KERNEL_5 = np.ones((5, 5), np.uint8)
KERNEL_5[2, 2] = 0


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def color_index(colors: list[tuple[int, int, int]], rgb: tuple[int, int, int]) -> int:
    matches = [i for i, color in enumerate(colors) if tuple(color) == rgb]
    if len(matches) != 1:
        raise ValueError(f"cor esperada ausente ou ambígua na paleta: {rgb}")
    return matches[0]


def _count_neighbors(mask: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    return cv2.filter2D(mask.astype(np.uint8), cv2.CV_16S, kernel,
                        borderType=cv2.BORDER_CONSTANT)


def _winner(counts: list[np.ndarray], candidates: list[int]) -> tuple[np.ndarray, np.ndarray]:
    if len(counts) != len(candidates):
        raise ValueError("contagens e índices de cores divergiram")
    stack = np.stack(counts, axis=0)
    winner_local = np.argmax(stack, axis=0)
    maximum = np.max(stack, axis=0)
    winner = np.asarray(candidates, dtype=np.uint8)[winner_local]
    return winner, maximum


def refine_indices(pixels: np.ndarray,
                   colors: list[tuple[int, int, int]]) -> tuple[np.ndarray, dict]:
    """Remove tiny interior color islands while preserving crisp plane edges."""
    if pixels.ndim != 2 or pixels.shape != (base.FRAME_H, base.FRAME_W):
        raise ValueError(f"quadro não é {base.FRAME_W}x{base.FRAME_H}: {pixels.shape}")
    indices = pixels.astype(np.uint8, copy=True)
    original = indices.copy()
    shadow = color_index(colors, (0, 85, 85))
    mid = color_index(colors, (0, 170, 170))
    highlight = color_index(colors, (85, 170, 255))
    navy = color_index(colors, (0, 0, 85))
    white = color_index(colors, (255, 255, 255))
    yellow = color_index(colors, (255, 255, 0))
    ramp = [shadow, mid, highlight]

    # A single-pixel highlight/shadow surrounded by the opposite cloth planes
    # reads as confetti. Recolor only well-inside cloth windows; boundary pixels
    # and deliberate narrow folds remain untouched.
    ramp_masks = [indices == value for value in range(len(colors))]
    ramp_neighbors = _count_neighbors(np.isin(indices, ramp), KERNEL_5)
    ramp_counts = [_count_neighbors(ramp_masks[index], KERNEL_5) for index in ramp]
    dominant, dominant_count = _winner(ramp_counts, ramp)
    cloth_island = (
        np.isin(indices, ramp)
        & (ramp_neighbors >= 18)
        & (dominant_count >= 15)
    )
    own_count = np.zeros(indices.shape, dtype=np.int16)
    for index in ramp:
        own_count[indices == index] = ramp_counts[ramp.index(index)][indices == index]
    cloth_island &= (dominant != indices) & (own_count <= 5)
    indices[cloth_island] = dominant[cloth_island]
    cloth_cluster_pixels = int(np.count_nonzero(cloth_island))

    # Very dark navy belongs to the outline/separation role. If a tiny navy
    # mark is fully enclosed by cloth, use the approved deep-teal shadow tone.
    # Continuous navy strokes and any contour touching transparency/material
    # boundaries are retained for separation and object readability.
    navy_components, labels, stats, _ = cv2.connectedComponentsWithStats(
        (indices == navy).astype(np.uint8), connectivity=8
    )
    navy_to_shadow = np.zeros(indices.shape, dtype=bool)
    for label in range(1, navy_components):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area > 3:
            continue
        component = labels == label
        dilated = cv2.dilate(component.astype(np.uint8), KERNEL_3, iterations=1).astype(bool)
        ring = dilated & ~component
        ring_values = indices[ring]
        if ring_values.size == 0 or np.any(ring_values == 0):
            continue
        if int(np.count_nonzero(np.isin(ring_values, ramp))) < int(ring_values.size * 0.85):
            continue
        navy_to_shadow |= component
    indices[navy_to_shadow] = shadow
    enclosed_navy_pixels = int(np.count_nonzero(navy_to_shadow))

    # Remove isolated white/yellow color leaks only when an entire singleton is
    # enclosed by cloth. Gloves, collar, glasses, eyes, and cane pommel retain
    # their proper semantic colors because their clusters/material boundaries
    # are not surrounded by blue cloth.
    semantic_cleanup_pixels = 0
    for semantic_index in (white, yellow):
        count, component_labels, component_stats, _ = cv2.connectedComponentsWithStats(
            (indices == semantic_index).astype(np.uint8), connectivity=8
        )
        for label in range(1, count):
            if int(component_stats[label, cv2.CC_STAT_AREA]) != 1:
                continue
            component = component_labels == label
            y, x = np.argwhere(component)[0]
            y0, y1 = max(0, y - 1), min(indices.shape[0], y + 2)
            x0, x1 = max(0, x - 1), min(indices.shape[1], x + 2)
            neighbors = indices[y0:y1, x0:x1].copy()
            center_y, center_x = y - y0, x - x0
            include = np.ones(neighbors.shape, dtype=bool)
            include[center_y, center_x] = False
            neighbor_values = neighbors[include]
            if (np.count_nonzero(np.isin(neighbor_values, ramp)) >= 6
                    and not np.any(neighbor_values == 0)):
                local = [int(np.count_nonzero(neighbor_values == role)) for role in ramp]
                indices[y, x] = ramp[int(np.argmax(local))]
                semantic_cleanup_pixels += 1

    alpha_changed = int(np.count_nonzero((original == 0) != (indices == 0)))
    if alpha_changed:
        raise AssertionError(f"refinamento alterou alpha em {alpha_changed} pixels")
    if not set(map(int, np.unique(indices))).issubset(set(range(len(colors)))):
        raise AssertionError("refinamento criou índice fora da paleta aprovada")
    changed = int(np.count_nonzero(original != indices))
    return indices, {
        "changed_pixels": changed,
        "cloth_tone_islands_reassigned": cloth_cluster_pixels,
        "enclosed_navy_confetti_to_deep_teal": enclosed_navy_pixels,
        "isolated_white_yellow_leaks_removed": semantic_cleanup_pixels,
        "alpha_changed_pixels": alpha_changed,
        "tone_indices": {"deep_teal_shadow": shadow, "cyan_base": mid,
                         "blue_light": highlight},
    }


def self_check(colors: list[tuple[int, int, int]]) -> None:
    shadow = color_index(colors, (0, 85, 85))
    mid = color_index(colors, (0, 170, 170))
    highlight = color_index(colors, (85, 170, 255))
    navy = color_index(colors, (0, 0, 85))
    white = color_index(colors, (255, 255, 255))
    yellow = color_index(colors, (255, 255, 0))
    test = np.full((base.FRAME_H, base.FRAME_W), mid, dtype=np.uint8)
    test[:, :20] = shadow
    test[20:45, 20:45] = highlight
    test[31, 32] = mid  # one-cell island inside a larger highlight plane
    test[40, 40] = navy  # enclosed dark confetti
    test[45, 45] = white  # enclosed semantic-color leak
    test[48, 48] = yellow
    test[:, 0] = 0  # transparent contour is immutable
    cleaned, report = refine_indices(test, colors)
    assert cleaned[31, 32] == highlight, "large plane interior was damaged"
    assert cleaned[40, 40] == shadow, "enclosed navy speck was not removed"
    assert cleaned[45, 45] in (shadow, mid, highlight), "white cloth leak remained"
    assert cleaned[48, 48] in (shadow, mid, highlight), "yellow cloth leak remained"
    assert np.all(cleaned[:, 0] == 0), "transparent edge changed"
    assert cleaned[25, 19] == shadow and cleaned[25, 20] == highlight, "hard material-tone boundary was blurred"
    assert report["alpha_changed_pixels"] == 0
    # A legitimate connected glove and cane pommel stay white/yellow.
    test2 = np.full((base.FRAME_H, base.FRAME_W), mid, dtype=np.uint8)
    test2[20:22, 20:23] = white
    test2[30:32, 30:33] = yellow
    retained, _ = refine_indices(test2, colors)
    assert np.all(retained[20:22, 20:23] == white)
    assert np.all(retained[30:32, 30:33] == yellow)
    # Clean cel planes retain hard boundaries: no new in-between colors.
    assert set(map(int, np.unique(cleaned))).issubset(set(range(len(colors))))
    print("[SELF-CHECK OK] cel clusters, semantic accents, hard edges, and alpha")


def build_candidate(base_dir: Path, output: Path) -> dict:
    source, source_sha = base.validate_owner_source(base.DEFAULT_SOURCE)
    if base_dir.resolve() == output.resolve():
        raise ValueError("base e saída devem ser diretórios distintos")
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"saída existente preservada: {output}")
    colors, palette_codes = base.palette_from_approved_study(base.PALETTE_SOURCE)
    contract = json.loads(base.CONTRACT.read_text(encoding="utf-8"))
    source_rgba = np.asarray(Image.open(source).convert("RGBA"))
    rows, labels = base.group_components(source_rgba)
    base_report_path = base_dir / "conversion_report_61_pose_v7.json"
    if not base_report_path.is_file():
        raise FileNotFoundError(base_report_path)
    base_report = json.loads(base_report_path.read_text(encoding="utf-8"))
    if base_report.get("source_sha256") != source_sha:
        raise ValueError("v7 não veio da fonte owner-approved atual")

    output.mkdir(parents=True)
    prepared = output / "prepared_frames"
    prepared.mkdir()
    frame_by_id = {frame["frame_id"]: frame for frame in base_report["frames"]}
    frames: list[dict] = []
    total_cleanup = {
        "changed_pixels": 0,
        "cloth_tone_islands_reassigned": 0,
        "enclosed_navy_confetti_to_deep_teal": 0,
        "isolated_white_yellow_leaks_removed": 0,
    }
    sequence_specs = contract["sequences"][:9]
    for row, seq in zip(rows, sequence_specs):
        for pose_index, component in enumerate(row):
            frame_id = seq["frame_ids"][pose_index]
            old_path = base_dir / "project" / "res/sprites" / frame_by_id[frame_id]["res_path"].split("res/sprites/", 1)[1]
            if not old_path.is_file():
                raise FileNotFoundError(old_path)
            old_pixels = np.asarray(Image.open(old_path).convert("P"), dtype=np.uint8)
            converted, conversion = base.convert_component(source_rgba, component, colors, labels)
            # Verify the conversion still reproduces the reviewed v7 baseline.
            if not np.array_equal(converted, old_pixels):
                raise ValueError(f"v7 baseline drift at {frame_id}; do not refine a different source")
            refined, cleanup = refine_indices(converted, colors)
            conversion["cel_cluster_refinement"] = cleanup
            for key in total_cleanup:
                total_cleanup[key] += int(cleanup[key])
            file_name = f"dr_social_{seq['id']}_{frame_id.lower()}_sms_80px.png"
            path = prepared / file_name
            base.write_pose_png(path, refined, colors)
            frames.append({
                "global_index": len(frames),
                "sequence_id": seq["id"],
                "sequence_title": seq["title"],
                "frame_id": frame_id,
                "file_name": file_name,
                "png_path": str(path),
                "conversion": conversion,
            })
    if len(frames) != FRAME_COUNT:
        raise AssertionError(f"esperadas 61 poses, produzidas {len(frames)}")

    project = output / "project"
    report = base.build_project(
        project, source, source_sha, rows, frames, colors, palette_codes, contract
    )
    # The shared project builder has a v7 label by default; this candidate is
    # isolated, so bind every generated diagnostic label to v8 before build.
    manifest_path = project / ".mddev/project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = "dr_social_61_pose_review_v8"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    main_path = project / "src/main.c"
    main_text = main_path.read_text(encoding="utf-8").replace(
        "Dr Social 61 pose review v7", "Dr Social 61 pose review v8"
    )
    main_path.write_text(main_text, encoding="utf-8")
    internal_report = project / "doc/conversion_report_61_pose_v7.json"
    if internal_report.exists():
        internal_report.rename(project / "doc/conversion_report_61_pose_v8.json")
    internal_manifest = project / "doc/frame_manifest_61_pose_v7.json"
    if internal_manifest.exists():
        internal_manifest.rename(project / "doc/frame_manifest_61_pose_v8.json")
    for frame in frames:
        frame["png_path"] = str(project / frame["res_path"])

    base.make_preview(output / "dr_social_61_pose_converted_preview_4x.png",
                      rows, frames, colors)
    report["schema"] = "dr_social_sms_61_pose_rom_review_v8"
    report["status"] = "diagnostic_candidate_not_production"
    report["material_cluster_conversion"] = {
        "base_candidate": "v7 lower-row palette-ramp conversion",
        "base_palette_ramp_rgb_dark_to_light": [list(color) for color in base.FABRIC_BLUE_RAMP_RGB],
        "refinement": "conservative 5x5 interior majority over existing cloth tones; enclosed navy confetti maps to deep teal; singleton white/yellow leaks are recolored only when fully surrounded by cloth; hard boundaries and semantic accent clusters stay intact",
        "changed_pixels_total": total_cleanup["changed_pixels"],
        "cloth_tone_islands_reassigned": total_cleanup["cloth_tone_islands_reassigned"],
        "enclosed_navy_confetti_to_deep_teal": total_cleanup["enclosed_navy_confetti_to_deep_teal"],
        "isolated_white_yellow_leaks_removed": total_cleanup["isolated_white_yellow_leaks_removed"],
        "alpha_changed_pixels": 0,
        "palette_new_colors": 0,
        "geometry_pose_timing_changed": False,
        "limits": "Computational invariants do not validate artistic judgment; all 61 poses remain pending independent and owner review.",
    }
    cleanup_by_id = {frame["frame_id"]: frame["conversion"]["cel_cluster_refinement"]
                     for frame in frames}
    report["frames"] = [
        {**frame, "cel_cluster_refinement": cleanup_by_id[frame["frame_id"]]}
        for frame in report["frames"]
    ]
    report["pending"] = [
        "revisão visual independente dos 61 quadros, incluindo cor por material e clusters em 1x/nearest-neighbor",
        "aprovação humana da conversão pixel por pixel",
        "mapeamento da paleta P1 única para todo o elenco",
        "custo de upload VBlank e residência em cena de produção",
        "integração de gameplay, FPS, áudio e vínculo asset→ROM de produção",
    ]
    (output / "conversion_report_61_pose_v8.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if internal_report.exists():
        internal = json.loads(internal_report.read_text(encoding="utf-8"))
        internal["schema"] = "dr_social_sms_61_pose_rom_review_v8"
        internal["material_cluster_conversion"] = report["material_cluster_conversion"]
        internal["frames"] = report["frames"]
        internal_report.write_text(json.dumps(internal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    audit = compare_all(base_dir / "project/res/sprites", project / "res/sprites")
    audit_path = output / "dr_social_61_pose_cel_cluster_delta_v7_v8.json"
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report["delta_audit"] = str(audit_path.relative_to(output))
    report["rom_sha256_pending_build"] = True
    (output / "conversion_report_61_pose_v8.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def compare_all(before_dir: Path, after_dir: Path) -> dict:
    before = {p.name: p for p in before_dir.glob("*.png")}
    after = {p.name: p for p in after_dir.glob("*.png")}
    if len(before) != FRAME_COUNT or len(after) != FRAME_COUNT or set(before) != set(after):
        raise ValueError(f"quadros divergentes: v7={len(before)}, v8={len(after)}")
    rows = []
    total_changed = total_alpha = total_new_colors = 0
    for name in sorted(before):
        old = np.asarray(Image.open(before[name]).convert("RGBA"))
        new = np.asarray(Image.open(after[name]).convert("RGBA"))
        if old.shape != new.shape:
            raise ValueError(f"canvas divergiu: {name}")
        old_alpha, new_alpha = old[:, :, 3], new[:, :, 3]
        alpha_changed = int(np.count_nonzero(old_alpha != new_alpha))
        changed = int(np.count_nonzero(np.any(old != new, axis=2)))
        old_colors = {tuple(row) for row in old.reshape(-1, 4) if row[3]}
        new_colors = {tuple(row) for row in new.reshape(-1, 4) if row[3]}
        new_only = sorted(new_colors - old_colors)
        if alpha_changed or new_only:
            raise ValueError(f"mudança proibida em {name}: alpha={alpha_changed}, cores_novas={new_only}")
        total_changed += changed
        total_alpha += alpha_changed
        total_new_colors += len(new_only)
        rows.append({"frame_id": name, "changed_pixels": changed,
                     "alpha_changed_pixels": alpha_changed,
                     "new_colors": len(new_only),
                     "before_sha256": sha256(before[name]),
                     "after_sha256": sha256(after[name])})
    return {
        "schema": "dr_social_cel_cluster_delta_v7_v8",
        "status": "pass",
        "checked_frames": len(rows),
        "changed_pixels": total_changed,
        "alpha_changed_pixels": total_alpha,
        "new_palette_colors": total_new_colors,
        "geometry_and_pose_ids_preserved": True,
        "frames": rows,
        "limit": "Pixel/palette/alpha invariants only; this report cannot approve cel-shading aesthetics.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    colors, _codes = base.palette_from_approved_study(base.PALETTE_SOURCE)
    if args.self_check:
        self_check(colors)
        return 0
    report = build_candidate(args.base.resolve(), args.output.resolve())
    print(json.dumps({
        "status": report["status"],
        "frames": len(report["frames"]),
        "refinement": report["material_cluster_conversion"],
        "preview": str(args.output.resolve() / "dr_social_61_pose_converted_preview_4x.png"),
        "project": str(args.output.resolve() / "project"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
