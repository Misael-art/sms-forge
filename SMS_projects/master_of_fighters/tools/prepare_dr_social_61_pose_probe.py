#!/usr/bin/env python3
"""Convert the owner-designated 61-pose source into an SMS inspection ROM.

This is a conversion/diagnostic path, not a sprite-art generator or production
promoter. It keeps the supplied atlas intact, extracts the nine declared
sequences, maps to Dr. Social's approved 12-color SMS study palette, and builds
a banked ROM which lets a reviewer inspect all 61 poses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "SMS_projects" / "master_of_fighters"
WRAPPER = ROOT / "tools" / "sms_wrapper"
sys.path.insert(0, str(WRAPPER))

from pack_sms_metasprite import (  # noqa: E402
    pack_poses, safe_sprite_pattern_capacity,
)
from png_io import read_indexed_png, write_indexed_png  # noqa: E402

# Historical replay only: these paths reproduce diagnostics of archived v01.
# They must not be used as visual inputs for the current animation-source v02.
DEFAULT_SOURCE = (
    PROJECT / "data/source_art/sprite_studies/dr_social/historical_approved/"
    "basic_sequences_61f_owner_source_v1/"
    "dr_social_basic_sequences_61f_owner_source_v1.png"
)
SOURCE_LINEAGE = (
    PROJECT / "data/source_art/sprite_studies/dr_social/historical_approved/"
    "basic_sequences_61f_owner_source_v1/"
    "dr_social_basic_sequences_61f_owner_source_v1.json"
)
CONTRACT = PROJECT / "doc/dr_social_animation_contract_v1.json"
PALETTE_SOURCE = (
    PROJECT / "data/source_art/sprite_studies/dr_social/"
    "dr_social_idle_guard_12f_sms_96px_v9_clean.png"
)
EXPECTED_SEQUENCE_COUNTS = [4, 8, 8, 8, 5, 8, 8, 8, 4]
ALPHA_THRESHOLD = 250
MIN_COMPONENT_AREA = 3000
SOURCE_SCALE_Y = 0.5
FRAME_W = FRAME_H = 80
SCREEN_X, SCREEN_Y = 88, 56
ROM_BANK_BYTES = 16 * 1024
DATA_BANK_FIRST = 2
SPRITE_TILE_BASE = 1
PALETTE_INDEX_COUNT = 13
FABRIC_BLUE_RAMP_RGB = ((0, 85, 85), (0, 170, 170), (85, 170, 255))
SPRITE_PATTERN_BASE_ADDRESS = 0x2000
BG_NAME_TABLE_BASE_ADDRESS = 0x3800
SPRITE_VRAM_TILE_BASE = SPRITE_PATTERN_BASE_ADDRESS // 32 + SPRITE_TILE_BASE
MAX_RESIDENT_SPRITE_PATTERNS = safe_sprite_pattern_capacity(
    SPRITE_TILE_BASE, SPRITE_PATTERN_BASE_ADDRESS, BG_NAME_TABLE_BASE_ADDRESS
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_owner_source(source: Path) -> tuple[Path, str]:
    """Require the exact owner-approved animation source and recorded SHA."""
    lineage = json.loads(SOURCE_LINEAGE.read_text())
    approved = lineage["source"]
    expected_path = (SOURCE_LINEAGE.parent / approved["file"]).resolve()
    actual_path = source.resolve()
    if actual_path != expected_path:
        raise ValueError(
            "source role mismatch: use the owner-approved 61-pose animation "
            f"source from lineage {SOURCE_LINEAGE}; received {actual_path}"
        )
    if not actual_path.is_file():
        raise FileNotFoundError(actual_path)
    actual_sha = sha256(actual_path)
    if actual_sha != approved["sha256"]:
        raise ValueError(
            "approved animation source SHA mismatch: "
            f"expected {approved['sha256']}, got {actual_sha}; update the "
            "approval lineage before converting a replacement"
        )
    if lineage.get("status") != "owner_approved_art_source_for_production_conversion":
        raise ValueError("lineage source is not marked owner-approved")
    return actual_path, actual_sha


def self_check() -> None:
    approved_path, approved_sha = validate_owner_source(DEFAULT_SOURCE)
    if approved_path != DEFAULT_SOURCE.resolve() or len(approved_sha) != 64:
        raise AssertionError("approved source lineage self-check failed")
    proof_only = PROJECT / "data/source_art/asset_conversion_proofs/dr_social/"
    proof_only = proof_only / "dr_social_sms_keypose_proof_v4.png"
    try:
        validate_owner_source(proof_only)
    except ValueError as exc:
        if "source role mismatch" not in str(exc):
            raise
    else:
        raise AssertionError("two-pose technical proof was accepted as animation source")
    print("[SELF-CHECK OK] owner-approved 61-pose source role and SHA")

    colors, _codes = palette_from_approved_study(PALETTE_SOURCE)
    source_indices = np.asarray([
        [1, 5, 5, 5], [5, 5, 5, 5],
        [4, 4, 4, 4], [4, 4, 4, 4],
    ], dtype=np.uint8)
    source_mask = np.ones((4, 4), dtype=bool)
    source_rgb = np.asarray(colors, dtype=np.uint8)[source_indices]
    scaled = np.array(
        Image.fromarray(source_indices, mode="L").resize(
            (2, 2), Image.Resampling.NEAREST
        ),
        dtype=np.uint8,
    )
    cohere_fabric_blue_ramp(
        source_rgb, source_mask, source_indices, scaled, colors
    )
    if not np.array_equal(scaled, np.asarray([[5, 5], [4, 4]], dtype=np.uint8)):
        raise AssertionError("blue cloth area sample failed or changed a non-fabric index")
    print("[SELF-CHECK OK] cloth ramp area coherence changes only existing blue material indices")


def c_array(name: str, values: list[int], c_type: str = "unsigned char",
            width: int = 16) -> str:
    rows = []
    for start in range(0, len(values), width):
        rows.append("    " + ", ".join(str(v) for v in values[start:start + width]))
    body = ",\n".join(rows)
    return f"const {c_type} {name}[{len(values)}] = {{\n{body}\n}};\n"


def group_components(source: np.ndarray) -> tuple[list[list[dict]], np.ndarray]:
    alpha = source[:, :, 3]
    mask = (alpha >= ALPHA_THRESHOLD).astype(np.uint8)
    count, labels, stats, centers = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )
    components = []
    for label in range(1, count):
        x, y, w, h, area = map(int, stats[label])
        if area < MIN_COMPONENT_AREA:
            continue
        components.append({
            "label": label, "x": x, "y": y, "w": w, "h": h, "area": area,
            "cx": float(centers[label][0]), "cy": float(centers[label][1]),
        })
    components.sort(key=lambda c: c["cy"])
    rows: list[list[dict]] = []
    for component in components:
        if not rows or component["cy"] - np.mean(
            [part["cy"] for part in rows[-1]]
        ) > 58:
            rows.append([component])
        else:
            rows[-1].append(component)
    counts = [len(row) for row in rows]
    if counts != EXPECTED_SEQUENCE_COUNTS:
        raise ValueError(
            f"layout da fonte divergiu; esperadas {EXPECTED_SEQUENCE_COUNTS}, "
            f"detectadas {counts}"
        )
    for row in rows:
        row.sort(key=lambda c: c["x"])
    return rows, labels


def palette_from_approved_study(path: Path) -> tuple[list[tuple[int, int, int]], list[int]]:
    image = Image.open(path)
    if image.mode != "P":
        raise ValueError(f"paleta aprovada precisa ser indexada: {path}")
    indices = sorted(set(image.tobytes()))
    if indices != list(range(PALETTE_INDEX_COUNT)):
        raise ValueError(f"estudo de paleta mudou: índices usados {indices}")
    raw = image.getpalette()
    colors = [
        tuple(raw[i * 3:i * 3 + 3]) for i in range(PALETTE_INDEX_COUNT)
    ]
    if image.info.get("transparency") not in (0, b"\x00"):
        raise ValueError("índice transparente esperado: 0")
    for color in colors[1:]:
        if any(channel not in (0, 85, 170, 255) for channel in color):
            raise ValueError(f"cor fora da CRAM SMS no estudo: {color}")
    codes = [0] * 16
    for index, (r, g, b) in enumerate(colors[1:], start=1):
        codes[index] = (r // 85) | ((g // 85) << 2) | ((b // 85) << 4)
    return colors, codes


def quantize_component(source: np.ndarray, component: dict,
                       sms_colors: list[tuple[int, int, int]],
                       labels: np.ndarray) -> tuple[np.ndarray, dict]:
    x, y, w, h = (component[k] for k in ("x", "y", "w", "h"))
    # Keep only this connected character component. Other disconnected
    # artifacts inside its bounding rectangle are not character pixels.
    mask = labels[y:y + h, x:x + w] == component["label"]
    rgb = source[y:y + h, x:x + w, :3]
    # RGB channel deltas can exceed 181; int16 squaring wraps and picks wrong
    # colors (notably mapping SMS blue to pink). Keep distances in int32.
    palette = np.asarray(sms_colors[1:], dtype=np.int32)
    flat = rgb.reshape((-1, 3)).astype(np.int32)
    distances = ((flat[:, None, :] - palette[None, :, :]) ** 2).sum(axis=2)
    indices = np.argmin(distances, axis=1).astype(np.uint8) + 1
    indices[~mask.reshape(-1)] = 0
    return indices.reshape((h, w)), {
        "bbox_source_px": [x, y, w, h],
        "opaque_pixels_before_scale": int(mask.sum()),
        "component_area_from_source": component["area"],
        "alpha_threshold": ALPHA_THRESHOLD,
    }


def cohere_fabric_blue_ramp(source_rgb: np.ndarray, source_mask: np.ndarray,
                            source_indices: np.ndarray,
                            scaled_indices: np.ndarray,
                            sms_colors: list[tuple[int, int, int]]) -> int:
    """Resolve subpixel blue-tone alternation before it reaches the tile art.

    Geometry and every non-fabric color remain the existing nearest-neighbor
    conversion. Only pixels already classified as the suit's three blue/teal
    material colors are reconsidered. Their source RGB is averaged inside the
    destination pixel footprint, then quantized to the same SMS ramp. This
    keeps hard pixel edges while preventing high-resolution color variation
    from scattering adjacent cloth tones after the 0.5x conversion.
    """
    ramp_indices = [
        i for i, color in enumerate(sms_colors)
        if tuple(color) in FABRIC_BLUE_RAMP_RGB
    ]
    if len(ramp_indices) != len(FABRIC_BLUE_RAMP_RGB):
        raise ValueError("paleta SMS não contém a rampa azul/teal do traje")

    blue_source_mask = source_mask & np.isin(source_indices, ramp_indices)
    if not np.any(blue_source_mask):
        return 0

    target_height, target_width = scaled_indices.shape
    weights = cv2.resize(
        blue_source_mask.astype(np.float32), (target_width, target_height),
        interpolation=cv2.INTER_AREA,
    )
    weighted_rgb = source_rgb.astype(np.float32) * blue_source_mask[:, :, None]
    sums = cv2.resize(
        weighted_rgb, (target_width, target_height),
        interpolation=cv2.INTER_AREA,
    )
    # The nearest-neighbor mask owns geometry; area weights only choose among
    # existing fabric tones, so no color can bleed across the silhouette.
    nearest_blue_mask = np.asarray(
        Image.fromarray(blue_source_mask.astype(np.uint8) * 255, mode="L")
        .resize((target_width, target_height), Image.Resampling.NEAREST)
    ) > 0
    eligible = nearest_blue_mask & (weights > 0)
    averages = np.zeros_like(sums, dtype=np.int32)
    averages[eligible] = np.rint(
        sums[eligible] / weights[eligible][:, None]
    ).astype(np.int32)
    ramp = np.asarray([sms_colors[i] for i in ramp_indices], dtype=np.float32)
    pixels = averages[eligible].astype(np.float32)
    luma_weights = np.asarray([0.2126, 0.7152, 0.0722], dtype=np.float32)
    pixel_luma = pixels @ luma_weights
    ramp_luma = ramp @ luma_weights
    distances = np.abs(pixel_luma[:, None] - ramp_luma[None, :])
    remapped = np.asarray(ramp_indices, dtype=np.uint8)[np.argmin(distances, axis=1)]
    changed = int(np.count_nonzero(scaled_indices[eligible] != remapped))
    scaled_indices[eligible] = remapped
    return changed


def convert_component(source: np.ndarray, component: dict,
                      sms_colors: list[tuple[int, int, int]],
                      labels: np.ndarray) -> tuple[np.ndarray, dict]:
    indexed, report = quantize_component(source, component, sms_colors, labels)
    x, y, w, h = (component[k] for k in ("x", "y", "w", "h"))
    source_mask = labels[y:y + h, x:x + w] == component["label"]
    source_rgb = source[y:y + h, x:x + w, :3]
    base_width = max(1, int(round(indexed.shape[1] * SOURCE_SCALE_Y)))
    target_height = max(1, int(round(indexed.shape[0] * SOURCE_SCALE_Y)))
    minimum_width = max(8, int(math.floor(base_width * 0.72)))
    for width in range(base_width, minimum_width - 1, -1):
        scaled = np.array(
            Image.fromarray(indexed, mode="L").resize(
                (width, target_height), Image.Resampling.NEAREST
            ),
            dtype=np.uint8,
        )
        shade_reassignments = cohere_fabric_blue_ramp(
            source_rgb, source_mask, indexed, scaled, sms_colors
        )
        canvas, metrics = place_scaled_frame(scaled, width)
        if metrics["peak_objects_per_scanline"] <= 8:
            report.update(metrics)
            report["base_width_at_uniform_half_scale_px"] = base_width
            report["hardware_fit_width_px"] = width
            report["horizontal_fit_ratio"] = round(width / base_width, 4)
            report["horizontal_fit_applied"] = width != base_width
            report["fabric_blue_cluster_reassignments"] = shade_reassignments
            report["fabric_blue_ramp_rgb"] = [list(color) for color in FABRIC_BLUE_RAMP_RGB]
            report["fabric_blue_cluster_method"] = "area-average existing ramp inside nearest-neighbor cloth mask; choose existing shade by luminance; hard indexed output"
            report["sms_palette_indices_used"] = sorted(
                int(value) for value in np.unique(canvas)
            )
            return canvas, report
    raise ValueError(
        f"pose não cabe no limite 8/scanline sem reduzir largura além de 28%: "
        f"bbox={report['bbox_source_px']}"
    )


def place_scaled_frame(scaled: np.ndarray, target_width: int) -> tuple[np.ndarray, dict]:
    """Place an already nearest-scaled, palette-closed pose on the SMS canvas."""
    target_height = scaled.shape[0]
    if scaled.shape[1] != target_width:
        raise ValueError("largura escalada divergiu do canvas de pose")
    canvas = np.zeros((FRAME_H, FRAME_W), dtype=np.uint8)
    x0 = (FRAME_W - target_width) // 2
    y0 = FRAME_H - target_height - 1
    if x0 < 1 or x0 + target_width > FRAME_W - 1:
        raise ValueError("margem horizontal menor que 1 pixel")
    if y0 < 1 or y0 + target_height > FRAME_H - 1:
        raise ValueError("margem vertical menor que 1 pixel")
    canvas[y0:y0 + target_height, x0:x0 + target_width] = scaled
    cell_rows = [
        sum(bool(np.any(canvas[ty * 8:(ty + 1) * 8, tx * 8:(tx + 1) * 8]))
            for tx in range(FRAME_W // 8))
        for ty in range(FRAME_H // 8)
    ]
    opaque_y, opaque_x = np.where(canvas != 0)
    return canvas, {
        "output_bbox_px": [
            int(opaque_x.min()), int(opaque_y.min()),
            int(opaque_x.max() - opaque_x.min() + 1),
            int(opaque_y.max() - opaque_y.min() + 1),
        ],
        "scaled_raster_size_px": [target_width, target_height],
        "objects_per_8px_row": cell_rows,
        "peak_objects_per_scanline": max(cell_rows, default=0),
        "hardware_objects": int(sum(cell_rows)),
        "transparent_margin_px": {
            "left": int(opaque_x.min()), "top": int(opaque_y.min()),
            "right": int(FRAME_W - 1 - opaque_x.max()),
            "bottom": int(FRAME_H - 1 - opaque_y.max()),
        },
    }


def write_pose_png(path: Path, pixels: np.ndarray,
                   colors: list[tuple[int, int, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [bytes(row.tolist()) for row in pixels]
    write_indexed_png(
        str(path), FRAME_W, FRAME_H, colors,
        rows, trns=(0,)
    )
    check = read_indexed_png(str(path))
    if check["w"] != FRAME_W or check["h"] != FRAME_H:
        raise AssertionError(f"{path}: canvas de saída inesperado")
    if 0 not in check["trns"] or check["trns"] - {0}:
        raise AssertionError(f"{path}: transparência diferente do índice 0")
    used = {v for row in check["pixels"] for v in row}
    if not used.issubset(set(range(PALETTE_INDEX_COUNT))):
        raise AssertionError(f"{path}: paleta excede o estudo SMS")


def make_preview(path: Path, rows: list[list[dict]], frames: list[dict],
                 colors: list[tuple[int, int, int]]) -> None:
    scale = 4
    cell = FRAME_W * scale
    label_h, gap = 26, 10
    cols = max(len(row) for row in rows)
    width = cols * (cell + gap) + gap
    height = len(rows) * (label_h + cell + gap) + gap
    page = Image.new("RGB", (width, height), (45, 49, 56))
    draw = ImageDraw.Draw(page)
    font = ImageFont.load_default()
    frame_index = 0
    for ri, row in enumerate(rows):
        y = gap + ri * (label_h + cell + gap)
        seq_name = frames[frame_index]["sequence_title"]
        draw.text((gap, y + 5), f"{ri + 1:02d}  {seq_name}", fill=(230, 233, 238), font=font)
        for ci, _component in enumerate(row):
            frame = frames[frame_index]
            pose = Image.open(frame["png_path"]).convert("RGBA")
            bg = Image.new("RGBA", pose.size, (20, 22, 28, 255))
            bg.alpha_composite(pose)
            zoom = bg.resize((cell, cell), Image.Resampling.NEAREST)
            x = gap + ci * (cell + gap)
            y0 = y + label_h
            page.paste(zoom.convert("RGB"), (x, y0))
            draw.text((x + 4, y0 + 4), frame["frame_id"], fill=(245, 245, 245), font=font)
            frame_index += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    page.save(path)


def _store_banked_block(blob: bytearray, block: bytes) -> tuple[int, int]:
    if not block or len(block) > ROM_BANK_BYTES:
        raise ValueError(f"bloco de padrões precisa caber em um banco: {len(block)} B")
    offset = len(blob) % ROM_BANK_BYTES
    if offset + len(block) > ROM_BANK_BYTES:
        blob.extend(b"\xFF" * (ROM_BANK_BYTES - offset))
        offset = 0
    bank_index = len(blob) // ROM_BANK_BYTES
    blob.extend(block)
    return DATA_BANK_FIRST + bank_index, offset


def build_project(output: Path, source: Path, source_sha: str,
                  rows: list[list[dict]], frames: list[dict],
                  colors: list[tuple[int, int, int]], palette_codes: list[int],
                  contract: dict) -> dict:
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"output já existe e foi preservado: {output}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "src").mkdir()
    (output / "inc").mkdir()
    (output / "doc").mkdir()
    (output / "rascunho").mkdir()
    (output / "res/sprites").mkdir(parents=True)
    (output / "assets").mkdir()
    source_copy = output / "rascunho" / source.name
    shutil.copy2(source, source_copy)

    sequence_specs = contract["sequences"][:9]
    if [seq["id"] for seq in sequence_specs] != [
        "idle", "walk_forward", "walk_backward", "jump", "crouch",
        "dash_run", "knockdown_fall", "tech_roll_getup", "guard"
    ]:
        raise ValueError("as nove primeiras sequências do contrato mudaram")
    if [seq["source_pose_count"] for seq in sequence_specs] != EXPECTED_SEQUENCE_COUNTS:
        raise ValueError("as contagens do contrato já não somam as 61 poses")

    by_sequence: dict[str, list[dict]] = {}
    for frame in frames:
        by_sequence.setdefault(frame["sequence_id"], []).append(frame)

    packed_sequences = []
    bank_blob = bytearray()
    meta_blob: list[int] = []
    frame_lookup = []
    sequence_metadata = []
    provenance_assets = []
    manifest_rows = []
    for seq_index, seq in enumerate(sequence_specs):
        seq_frames = by_sequence[seq["id"]]
        png_specs = [(frame["frame_id"], Path(frame["png_path"])) for frame in seq_frames]
        pooled = True
        pool_failure = ""
        try:
            packed = pack_poses(
                png_specs, tile_base=SPRITE_TILE_BASE,
                max_patterns=MAX_RESIDENT_SPRITE_PATTERNS,
            )
            sequence_bank, sequence_offset = _store_banked_block(
                bank_blob, packed["tile_bytes"]
            )
            sequence_tile_bytes = len(packed["tile_bytes"])
        except ValueError as exc:
            if "janela" not in str(exc):
                raise
            pooled = False
            packed = None
            sequence_bank, sequence_offset, sequence_tile_bytes = 0, 0, 0
            pool_failure = str(exc)

        if pooled:
            sequence_metadata.append({
                "id": seq["id"], "title": seq["title"],
                "bank": sequence_bank, "offset": sequence_offset,
                "tile_bytes": sequence_tile_bytes,
                "patterns": sequence_tile_bytes // 32,
                "pool_mode": "sequence_shared_pool",
                "loop": bool(seq["loop"]),
            })
            pose_packs = packed["poses"]
        else:
            sequence_metadata.append({
                "id": seq["id"], "title": seq["title"],
                "bank": 0, "offset": 0, "tile_bytes": 0, "patterns": 0,
                "pool_mode": "pose_step_pool_required",
                "loop": bool(seq["loop"]),
                "pool_failure": pool_failure,
            })
            pose_packs = []
            for frame in seq_frames:
                one = pack_poses(
                    [(frame["frame_id"], Path(frame["png_path"]))],
                    tile_base=SPRITE_TILE_BASE,
                    max_patterns=MAX_RESIDENT_SPRITE_PATTERNS,
                )
                bank, offset = _store_banked_block(bank_blob, one["tile_bytes"])
                frame["bank"] = bank
                frame["bank_offset"] = offset
                frame["tile_bytes"] = len(one["tile_bytes"])
                pose_packs.append(one["poses"][0])

        for frame, pose_pack in zip(seq_frames, pose_packs):
            frame["meta_offset"] = len(meta_blob)
            frame["meta"] = pose_pack["meta"]
            meta_blob.extend(pose_pack["meta"])
            frame["objects"] = len(pose_pack["objects"])
            frame["peak_objects_per_scanline"] = pose_pack["peak_scanline"]
            frame["sequence_index"] = seq_index
            frame["duration_ticks"] = int(seq["duration_ticks"][
                len([v for v in seq_frames if v["frame_id"] < frame["frame_id"]])
            ])
            if pooled:
                frame["bank"] = sequence_bank
                frame["bank_offset"] = sequence_offset
                frame["tile_bytes"] = sequence_tile_bytes
            else:
                pass
            rel_png = f"res/sprites/{frame['file_name']}"
            copy_png = output / rel_png
            shutil.copy2(frame["png_path"], copy_png)
            frame["res_path"] = rel_png
            relative_origin = f"rascunho/{source.name}"
            provenance_assets.append({
                "file": rel_png, "origin": relative_origin,
                "author": "Imagem de animação indicada pelo proprietário; conversão determinística SMS",
                "tool": "prepare_dr_social_61_pose_probe.py",
                "role": "pixel_sprite_candidate",
                "sha256": source_sha,
            })
            pose_manifest = {
                "schema": "sprite_scene_manifest_v1",
                "sprite_size": "8x8",
                "zoomed": False,
                "screen_h": 192,
                "sprites": [
                    {"x": SCREEN_X + obj["x"], "y": SCREEN_Y + obj["y"],
                     "tile": obj["tile"]}
                    for obj in pose_pack["objects"]
                ],
            }
            manifest_path = output / "doc" / f"sprite_scene_{frame['frame_id']}.json"
            manifest_path.write_text(json.dumps(pose_manifest, indent=2) + "\n")
            manifest_rows.append({
                "frame_id": frame["frame_id"],
                "sequence_id": frame["sequence_id"],
                "path": str(manifest_path),
            })
            packed_sequences.append({
                "sequence_id": seq["id"],
                "frame_id": frame["frame_id"],
                "objects": frame["objects"],
                "peak_objects_per_scanline": frame["peak_objects_per_scanline"],
                "tile_patterns_for_pose": len(set(
                    pose_pack["tile_map"]
                ) - {None}),
                "tile_bytes_loaded_for_sequence_or_pose": frame["tile_bytes"],
            })

    if len(frames) != 61 or len(frame_lookup) > 61:
        raise AssertionError("a conversão deixou de cobrir exatamente 61 poses")
    bank_file = output / "assets/dr_social_61_sequence_tiles.bin"
    if not bank_blob:
        raise AssertionError("ROM sem dados de tiles")
    if len(bank_blob) % ROM_BANK_BYTES:
        bank_blob.extend(b"\xFF" * (ROM_BANK_BYTES - len(bank_blob) % ROM_BANK_BYTES))
    bank_file.write_bytes(bank_blob)
    bank_count = len(bank_blob) // ROM_BANK_BYTES

    for frame in frames:
        frame_lookup.append(frame)
    seq_start = []
    seq_count = []
    duration_by_global = []
    global_seq = []
    ids_bytes = []
    id_offsets = []
    for seq_index, seq in enumerate(sequence_specs):
        seq_frames = by_sequence[seq["id"]]
        seq_start.append(len(duration_by_global))
        seq_count.append(len(seq_frames))
        for frame in seq_frames:
            duration_by_global.append(frame["duration_ticks"])
            global_seq.append(seq_index)
            id_offsets.append(len(ids_bytes))
            ids_bytes.extend(frame["frame_id"].encode("ascii") + b"\0")
    title_bytes = []
    title_offsets = []
    for seq in sequence_specs:
        title_offsets.append(len(title_bytes))
        title_bytes.extend(seq["title"].upper().encode("ascii", "replace") + b"\0")

    arrays = [
        c_array("ds_sequence_bank", [item["bank"] for item in sequence_metadata]),
        c_array("ds_sequence_offset", [item["offset"] for item in sequence_metadata],
                "unsigned int", 8),
        c_array("ds_sequence_bytes", [item["tile_bytes"] for item in sequence_metadata],
                "unsigned int", 8),
        c_array("ds_sequence_mode", [
            0 if item["pool_mode"] == "sequence_shared_pool" else 1
            for item in sequence_metadata
        ]),
        c_array("ds_sequence_start", seq_start),
        c_array("ds_sequence_count", seq_count),
        c_array("ds_sequence_loop", [1 if item["loop"] else 0 for item in sequence_metadata]),
        c_array("ds_frame_sequence", global_seq),
        c_array("ds_frame_duration", duration_by_global),
        c_array("ds_frame_meta_offset", [int(frame["meta_offset"]) for frame in frame_lookup],
                "unsigned int", 8),
        c_array("ds_frame_id_offset", id_offsets, "unsigned int", 8),
        c_array("ds_frame_id_text", list(ids_bytes)),
        c_array("ds_sequence_title_offset", title_offsets, "unsigned int", 8),
        c_array("ds_sequence_title_text", list(title_bytes)),
        c_array("ds_frame_meta", meta_blob),
        c_array("ds_sprite_palette", palette_codes),
    ]
    arrays.extend([
        c_array("ds_frame_bank", [int(frame["bank"]) for frame in frame_lookup]),
        c_array("ds_frame_bank_offset", [
            int(frame["bank_offset"]) for frame in frame_lookup
        ], "unsigned int", 8),
        c_array("ds_frame_tile_bytes", [
            int(frame["tile_bytes"]) for frame in frame_lookup
        ], "unsigned int", 8),
    ])
    header = [
        "#ifndef DR_SOCIAL_61_POSE_DATA_H",
        "#define DR_SOCIAL_61_POSE_DATA_H",
        "#define DS_SEQUENCE_COUNT 9u",
        "#define DS_FRAME_COUNT 61u",
        "#define DS_SCREEN_X 88u",
        "#define DS_SCREEN_Y 56u",
        "#define DS_TILE_BASE 257u",
        *arrays,
        "#endif",
        "",
    ]
    (output / "inc/dr_social_61_pose_data.h").write_text("\n".join(header))

    main_source = r'''#include "SMSlib.h"
#include "dr_social_61_pose_data.h"

SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER(0, 1, 2026, 10, 10,
                      "SMSForge", "DrSocialReview", "Dr Social 61 pose review v7");

static const unsigned char bg_palette[16] = {
    0x00, 0x3F, 0x15, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};
static unsigned char sequence_index;
static unsigned char pose_index;
static unsigned char loaded_sequence = 0xFF;
static unsigned char loaded_pose = 0xFF;
static unsigned char auto_play;
static unsigned char elapsed_ticks;
static unsigned char status_line[11] = "POSE 00/00";

static void print_status(void) {
    unsigned char global = ds_sequence_start[sequence_index] + pose_index;
    unsigned char count = ds_sequence_count[sequence_index];
    const unsigned char *title =
        ds_sequence_title_text + ds_sequence_title_offset[sequence_index];
    const unsigned char *frame_id = ds_frame_id_text + ds_frame_id_offset[global];
    status_line[5] = (unsigned char)('0' + ((pose_index + 1) / 10));
    status_line[6] = (unsigned char)('0' + ((pose_index + 1) % 10));
    status_line[8] = (unsigned char)('0' + (count / 10));
    status_line[9] = (unsigned char)('0' + (count % 10));
    SMS_printatXY(1, 2, (const unsigned char *)"                                ");
    SMS_printatXY(1, 3, (const unsigned char *)"                                ");
    SMS_printatXY(1, 21, (const unsigned char *)"                                ");
    SMS_printatXY(1, 22, (const unsigned char *)"                                ");
    SMS_printatXY(1, 1, (const unsigned char *)"DR SOCIAL 61 POSE REVIEW");
    SMS_printatXY(1, 2, title);
    SMS_printatXY(1, 3, status_line);
    SMS_printatXY(13, 3, frame_id);
    SMS_printatXY(1, 21, (const unsigned char *)"LEFT/RIGHT=POSE UP/DOWN=SEQ");
    if (ds_sequence_mode[sequence_index]) {
        SMS_printatXY(1, 22, (const unsigned char *)"STEP ONLY: TILE POOL > 191");
    } else if (auto_play) {
        SMS_printatXY(1, 22, (const unsigned char *)"1 PAUSE 2 RESET");
    } else {
        SMS_printatXY(1, 22, (const unsigned char *)"1 PLAY/PAUSE 2 RESET");
    }
}

static void load_pose_data(unsigned char global) {
    unsigned int source_address;
    unsigned char bank;
    unsigned int offset;
    unsigned int bytes;
    if (ds_sequence_mode[sequence_index]) {
        bank = ds_frame_bank[global];
        offset = ds_frame_bank_offset[global];
        bytes = ds_frame_tile_bytes[global];
    } else {
        bank = ds_sequence_bank[sequence_index];
        offset = ds_sequence_offset[sequence_index];
        bytes = ds_sequence_bytes[sequence_index];
    }
    SMS_mapROMBank(bank);
    source_address = 0x8000u + offset;
    SMS_loadTiles((const unsigned char *)source_address, DS_TILE_BASE, bytes);
}

static void render_pose(void) {
    unsigned char global = ds_sequence_start[sequence_index] + pose_index;
    unsigned char must_load;
    if (ds_sequence_mode[sequence_index])
        must_load = (loaded_pose != global);
    else
        must_load = (loaded_sequence != sequence_index);
    if (must_load) {
        SMS_displayOff();
        load_pose_data(global);
    }
    SMS_initSprites();
    SMS_addMetaSprite(DS_SCREEN_X, DS_SCREEN_Y,
                      (void *)(ds_frame_meta + ds_frame_meta_offset[global]));
    SMS_copySpritestoSAT();
    print_status();
    if (must_load) {
        loaded_sequence = sequence_index;
        loaded_pose = global;
        SMS_displayOn();
    }
}

void main(void) {
    unsigned char row, col;
    unsigned int keys;
    SMS_init();
    SMS_displayOff();
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    SMS_useFirstHalfTilesforSprites(0);
    SMS_autoSetUpTextRenderer();
    SMS_loadBGPalette(bg_palette);
    SMS_loadSpritePalette(ds_sprite_palette);
    SMS_setBackdropColor(0);
    for (row = 0; row < 24; ++row)
        for (col = 0; col < 32; ++col)
            SMS_setTileatXY(col, row, 0);
    sequence_index = 0;
    pose_index = 0;
    auto_play = 0;
    elapsed_ticks = 0;
    render_pose();
    for (;;) {
        SMS_waitForVBlank();
        keys = SMS_getKeysPressed();
        if (keys & PORT_A_KEY_LEFT) {
            auto_play = 0;
            elapsed_ticks = 0;
            if (pose_index > 0) --pose_index;
            render_pose();
        } else if (keys & PORT_A_KEY_RIGHT) {
            auto_play = 0;
            elapsed_ticks = 0;
            if (pose_index + 1 < ds_sequence_count[sequence_index]) ++pose_index;
            render_pose();
        } else if (keys & PORT_A_KEY_UP) {
            auto_play = 0;
            elapsed_ticks = 0;
            sequence_index = (sequence_index == 0)
                ? DS_SEQUENCE_COUNT - 1 : sequence_index - 1;
            pose_index = 0;
            render_pose();
        } else if (keys & PORT_A_KEY_DOWN) {
            auto_play = 0;
            elapsed_ticks = 0;
            sequence_index = (sequence_index + 1) % DS_SEQUENCE_COUNT;
            pose_index = 0;
            render_pose();
        } else if (keys & PORT_A_KEY_2) {
            auto_play = 0;
            elapsed_ticks = 0;
            pose_index = 0;
            render_pose();
        } else if ((keys & PORT_A_KEY_1)
                   && !ds_sequence_mode[sequence_index]) {
            auto_play = !auto_play;
            elapsed_ticks = 0;
            print_status();
        }
        if (auto_play && !ds_sequence_mode[sequence_index]) {
            unsigned char global = ds_sequence_start[sequence_index] + pose_index;
            if (++elapsed_ticks >= ds_frame_duration[global]) {
                elapsed_ticks = 0;
                if (pose_index + 1 < ds_sequence_count[sequence_index]) {
                    ++pose_index;
                    render_pose();
                } else if (ds_sequence_loop[sequence_index]) {
                    pose_index = 0;
                    render_pose();
                } else {
                    auto_play = 0;
                    print_status();
                }
            }
        }
    }
}
'''
    (output / "src/main.c").write_text(main_source)

    (output / ".mddev").mkdir()
    project_manifest = {
        "name": "dr_social_61_pose_review_v7",
        "platform": "sega_master_system",
        "region_target": ["NTSC", "PAL"],
        "toolchain": {
            "compiler": "sdcc>=4.2", "sdk": "devkitSMS",
            "libs": ["SMSlib", "PSGlib"],
            "makesms_extra": [
                "-mbank",
                f"assets/{bank_file.name}:0:{bank_count}:{DATA_BANK_FIRST}",
            ],
        },
        "skeleton_version": 1,
        "specialization": "fighting",
    }
    (output / ".mddev/project.json").write_text(
        json.dumps(project_manifest, indent=2) + "\n"
    )
    shutil.copy2(PROJECT / "doc/palettes_manifest.json", output / "doc/palettes_manifest.json")
    (output / "doc/asset_provenance_manifest.json").write_text(
        json.dumps({"assets": provenance_assets}, indent=2) + "\n"
    )

    report = {
        "schema": "dr_social_sms_61_pose_rom_review_v7",
        "status": "diagnostic_candidate_not_production",
        "project": "master_of_fighters",
        "source_path": str(source.relative_to(PROJECT)),
        "source_sha256": source_sha,
        "source_dimensions_px": list(Image.open(source).size),
        "source_role": "owner_designated_approved_61_pose_animation_source",
        "sequences": sequence_metadata,
        "frames": [
            {
                "frame_id": frame["frame_id"],
                "sequence_id": frame["sequence_id"],
                "res_path": frame["res_path"],
                "source_bbox_px": frame["conversion"]["bbox_source_px"],
                "output_bbox_px": frame["conversion"]["output_bbox_px"],
                "scale_source_to_native_sms": {
                    "vertical": SOURCE_SCALE_Y,
                    "horizontal_fit_ratio": frame["conversion"]["horizontal_fit_ratio"],
                },
                "objects_per_8px_row": frame["conversion"]["objects_per_8px_row"],
                "hardware_objects": frame["conversion"]["hardware_objects"],
                "peak_objects_per_scanline": frame["conversion"]["peak_objects_per_scanline"],
                "fabric_blue_cluster_reassignments": frame["conversion"]["fabric_blue_cluster_reassignments"],
                "tile_bytes_for_pool_or_pose": frame["tile_bytes"],
            }
            for frame in frames
        ],
        "palette": {
            "source_study": str(PALETTE_SOURCE.relative_to(PROJECT)),
            "rgb": [list(color) for color in colors],
            "useful_color_count": len(colors) - 1,
            "runtime_scope": "single-character diagnostic P1; roster mapping remains pending",
        },
        "material_cluster_conversion": {
            "scope": "only pixels already classified as the blue/teal cloth ramp",
            "ramp_rgb_dark_to_light": [list(color) for color in FABRIC_BLUE_RAMP_RGB],
            "method": "area-average source RGB within each destination cloth-pixel footprint, then assign the existing SMS ramp tone by luminance order; nearest-neighbor silhouette and all non-blue palette indices stay unchanged",
            "total_reassigned_pixels": sum(
                frame["conversion"]["fabric_blue_cluster_reassignments"]
                for frame in frames
            ),
            "output_edges": "hard indexed pixels; no blur, dithering, or new colors",
        },
        "rom_storage": {
            "bank_file": f"assets/{bank_file.name}",
            "bank_bytes": ROM_BANK_BYTES,
            "first_data_bank": DATA_BANK_FIRST,
            "data_bank_count": bank_count,
            "raw_tile_data_bytes": len(bank_blob),
            "metadata_bytes": len(meta_blob),
            "sprite_pattern_window": {
                "sprite_pattern_base_address_hex": hex(SPRITE_PATTERN_BASE_ADDRESS),
                "bg_name_table_base_address_hex": hex(BG_NAME_TABLE_BASE_ADDRESS),
                "loaded_tile_base": SPRITE_VRAM_TILE_BASE,
                "max_resident_unique_patterns": MAX_RESIDENT_SPRITE_PATTERNS,
                "overflow_policy": "load one pose at a time; never write into BG name table",
            },
            "sequence_pool_modes": {
                item["pool_mode"]: sum(
                    1 for row in sequence_metadata if row["pool_mode"] == item["pool_mode"]
                )
                for item in sequence_metadata
            },
        },
        "controls": {
            "left_right": "pose anterior/posterior da sequência",
            "up_down": "sequência anterior/posterior",
            "button_1": "reproduz/pausa timing proposto, apenas quando pool cabe na janela VRAM SMS",
            "button_2": "volta à primeira pose e pausa",
        },
        "pending": [
            "revisão visual independente dos 61 quadros convertidos, com foco na continuidade direcional da sombra azul do tecido",
            "aprovação humana da conversão pixel por pixel",
            "mapeamento da paleta P1 única para todo o elenco",
            "custo de upload VBlank e residência em cena de produção",
            "integração de gameplay, FPS, áudio e vínculo asset→ROM de produção",
        ],
    }
    (output / "doc/conversion_report_61_pose_v7.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    (output / "doc/frame_manifest_61_pose_v7.json").write_text(
        json.dumps(manifest_rows, indent=2, ensure_ascii=False) + "\n"
    )
    return report


def prepare(source: Path, output: Path) -> dict:
    source, source_sha = validate_owner_source(source)
    contract = json.loads(CONTRACT.read_text())
    colors, palette_codes = palette_from_approved_study(PALETTE_SOURCE)
    source_rgba = np.asarray(Image.open(source).convert("RGBA"))
    rows, labels = group_components(source_rgba)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise FileExistsError(f"output já existe e foi preservado: {output}")

    frames = []
    sequence_specs = contract["sequences"][:9]
    for row_index, (row, seq) in enumerate(zip(rows, sequence_specs)):
        if len(row) != seq["source_pose_count"]:
            raise ValueError(f"{seq['id']}: contagem da fonte divergiu do contrato")
        for pose_index, component in enumerate(row):
            frame_id = seq["frame_ids"][pose_index]
            frame_pixels, conversion = convert_component(
                source_rgba, component, colors, labels
            )
            file_name = f"dr_social_{seq['id']}_{frame_id.lower()}_sms_80px.png"
            png_path = output / "project" / "res/sprites" / file_name
            write_pose_png(png_path, frame_pixels, colors)
            frames.append({
                "global_index": len(frames),
                "sequence_id": seq["id"],
                "sequence_title": seq["title"],
                "frame_id": frame_id,
                "file_name": file_name,
                "png_path": str(png_path),
                "conversion": conversion,
            })
    if len(frames) != 61:
        raise AssertionError(f"saíram {len(frames)} poses, esperadas 61")
    # The first stage writes PNGs. build_project expects an empty project root,
    # so move these already-validated resources into its canonical location.
    prepared_pngs = {frame["frame_id"]: Path(frame["png_path"]) for frame in frames}
    temp_frames = output / "prepared_frames"
    temp_frames.mkdir()
    for frame in frames:
        source_png = prepared_pngs[frame["frame_id"]]
        dest_png = temp_frames / source_png.name
        shutil.move(source_png, dest_png)
        frame["png_path"] = str(dest_png)
    shutil.rmtree(output / "project")
    project = output / "project"
    report = build_project(
        project, source, source_sha, rows, frames, colors, palette_codes, contract
    )
    for frame in frames:
        frame["png_path"] = str(project / frame["res_path"])
    make_preview(output / "dr_social_61_pose_converted_preview_4x.png",
                 rows, frames, colors)
    (output / "conversion_report_61_pose_v7.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE,
                        help="must match the exact owner-approved source path and SHA")
    parser.add_argument(
        "--output", type=Path,
        default=PROJECT / "out/diagnostics/dr_social_61_pose_review_v7",
    )
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    source = args.source.resolve()
    output = args.output.resolve()
    report = prepare(source, output)
    print(json.dumps({
        "status": report["status"],
        "source_sha256": report["source_sha256"],
        "poses": len(report["frames"]),
        "sequence_modes": [
            {"id": row["id"], "mode": row["pool_mode"],
             "patterns": row["patterns"]}
            for row in report["sequences"]
        ],
        "data_banks": report["rom_storage"]["data_bank_count"],
        "data_bytes": report["rom_storage"]["raw_tile_data_bytes"],
        "preview": str(output / "dr_social_61_pose_converted_preview_4x.png"),
        "project": str(output / "project"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
