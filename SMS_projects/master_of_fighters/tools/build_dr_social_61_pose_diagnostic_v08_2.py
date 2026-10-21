#!/usr/bin/env python3
"""Build a deterministic, banked SMS pose-viewer project from approved v08.2 art.

Only exact 80x80 indexed crops are made. No resampling, quantization,
interpolation, filters, or pixel recoloring are performed by this converter.
The generated ROM is a diagnostic viewer, not a gameplay build.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "SMS_projects/master_of_fighters"
sys.path.insert(0, str(ROOT / "tools/sms_wrapper"))
from png_to_sms_tiles import tile_bytes  # noqa: E402

SOURCE_REL = Path(
    "res/approved_art/dr_social/"
    "dr_social_basic_sequences_61f_cps2_alpha_cel_v08_2_approved.png"
)
SOURCE_SHA256 = "4e557095dcafd4f11a0369e6e993ad4fa99497ab529509dedd2445f83bcf89d8"
VIEWER_NAME = "dr_social_61_pose_review_v08_2"
OUT = PROJECT / "out/diagnostics" / VIEWER_NAME
BANK_BYTES = 16 * 1024
FIRST_DATA_BANK = 2
BG_TILE_BASE = 128
FRAME_W = FRAME_H = 80
SEQUENCES = [
    ("idle", "ID", "IDLE", 4, 1),
    ("walk_forward", "WF", "WALK FORWARD", 8, 1),
    ("walk_backward", "WB", "WALK BACKWARD", 8, 1),
    ("jump", "JU", "JUMP", 8, 0),
    ("crouch", "CR", "CROUCH", 5, 0),
    ("dash_run", "DA", "DASH", 8, 0),
    ("knockdown_fall", "KF", "KNOCKDOWN / FALL", 8, 0),
    ("tech_roll_getup", "TR", "ROLL / GET UP", 8, 0),
    ("guard", "GU", "GUARD", 4, 1),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def c_array(name: str, values: list[int], c_type: str = "unsigned char",
            width: int = 16) -> str:
    lines = ["    " + ", ".join(str(v) for v in values[i:i + width])
             for i in range(0, len(values), width)]
    return f"const {c_type} {name}[{len(values)}] = {{\n" + ",\n".join(lines) + "\n};\n"


def text_array(name: str, strings: list[str]) -> tuple[list[int], list[int]]:
    offsets: list[int] = []
    values: list[int] = []
    for value in strings:
        offsets.append(len(values))
        values.extend(value.encode("ascii"))
        values.append(0)
    return offsets, values


def build_header(frames: list[dict], palette: list[int]) -> str:
    sequence_starts: list[int] = []
    sequence_counts: list[int] = []
    sequence_loops: list[int] = []
    frame_sequence: list[int] = []
    frame_ids: list[str] = []
    titles: list[str] = []
    for seq_index, (_sid, prefix, title, count, loop) in enumerate(SEQUENCES):
        sequence_starts.append(len(frame_ids))
        sequence_counts.append(count)
        sequence_loops.append(loop)
        titles.append(title)
        for frame_number in range(1, count + 1):
            frame_ids.append(f"{prefix}{frame_number:02d}")
            frame_sequence.append(seq_index)

    frame_banks: list[int] = []
    frame_bank_offsets: list[int] = []
    frame_tile_bytes: list[int] = []
    for frame in frames:
        frame_banks.append(frame["bank"])
        frame_bank_offsets.append(frame["bank_offset"])
        frame_tile_bytes.append(frame["tile_bytes"])

    id_offsets, id_text = text_array("", frame_ids)
    title_offsets, title_text = text_array("", titles)
    parts = [
        "#ifndef DR_SOCIAL_61_POSE_DATA_H\n#define DR_SOCIAL_61_POSE_DATA_H\n",
        f"#define DS_SEQUENCE_COUNT {len(SEQUENCES)}u\n",
        f"#define DS_FRAME_COUNT {len(frames)}u\n",
        f"#define DS_BG_TILE_BASE {BG_TILE_BASE}u\n",
        c_array("ds_bg_palette", palette),
        c_array("ds_sequence_start", sequence_starts),
        c_array("ds_sequence_count", sequence_counts),
        c_array("ds_sequence_loop", sequence_loops),
        c_array("ds_frame_bank", frame_banks),
        c_array("ds_frame_bank_offset", frame_bank_offsets, "unsigned int"),
        c_array("ds_frame_tile_bytes", frame_tile_bytes, "unsigned int"),
        c_array("ds_frame_id_offset", id_offsets, "unsigned int"),
        c_array("ds_frame_id_text", id_text),
        c_array("ds_sequence_title_offset", title_offsets, "unsigned int"),
        c_array("ds_sequence_title_text", title_text),
        "#endif\n",
    ]
    return "\n".join(parts)


def validate_source(source: Path) -> tuple[Image.Image, list[tuple[int, int, int]]]:
    got_sha = sha256(source)
    if got_sha != SOURCE_SHA256:
        raise ValueError(f"SHA da arte aprovada divergiu: esperado {SOURCE_SHA256}, recebido {got_sha}")
    image = Image.open(source)
    if image.mode != "P" or image.size != (640, 720):
        raise ValueError(f"esperado PNG P 640x720, recebido {image.mode} {image.size}")
    if image.info.get("transparency") not in (0, b"\x00"):
        raise ValueError("índice 0 precisa continuar sendo a única transparência")
    used = set(image.tobytes())
    if 0 not in used or len(used - {0}) > 15 or max(used) > 15:
        raise ValueError(f"índices usados inválidos para P1 SMS: {sorted(used)}")
    raw = image.getpalette()
    palette = [tuple(raw[i:i + 3]) for i in range(0, min(len(raw), 768), 3)]
    if any(any(channel not in (0, 85, 170, 255) for channel in rgb)
           for index, rgb in enumerate(palette) if index in used and index != 0):
        raise ValueError("a fonte contém RGB fora dos quatro níveis por canal da CRAM SMS")
    active_by_row = []
    for row in range(9):
        active_by_row.append([])
        for col in range(8):
            crop = image.crop((col * FRAME_W, row * FRAME_H,
                               (col + 1) * FRAME_W, (row + 1) * FRAME_H))
            active_by_row[row].append(any(value != 0 for value in crop.tobytes()))
    expected_by_row = [
        [True] * 4 + [False] * 4,
        [True] * 8,
        [True] * 8,
        [True] * 8,
        [True] * 5 + [False] * 3,
        [True] * 8,
        [True] * 8,
        [True] * 8,
        [True] * 4 + [False] * 4,
    ]
    if active_by_row != expected_by_row:
        raise ValueError("grade 8x9 divergiu dos blocos sequenciais 4/8/8/8/5/8/8/8/4")
    return image, palette


def make_project(source: Path) -> dict:
    if OUT.exists():
        raise FileExistsError(f"preservando diagnóstico existente; saída já existe: {OUT}")
    image, source_palette = validate_source(source)
    diag = OUT / "project"
    frames_dir = diag / "res/frames/dr_social_v08_2"
    frames_dir.mkdir(parents=True)
    (diag / "src").mkdir()
    (diag / "inc").mkdir()
    (diag / "assets").mkdir()
    (diag / "doc").mkdir()
    (diag / "rascunho").mkdir()
    (diag / "out").mkdir()
    (diag / "changelog").mkdir()
    shutil.copyfile(source, diag / "rascunho" / source.name)
    shutil.copyfile(PROJECT / "tools/dr_social_61_pose_viewer_main_v08_2.c",
                    diag / "src/main.c")

    frame_specs: list[dict] = []
    frame_manifest: list[dict] = []
    sprite_audit: list[dict] = []
    sequence_start = 0
    blob = bytearray()
    palette_codes = [0] * 16
    for index, rgb in enumerate(source_palette[:16]):
        if index == 0:
            continue
        r, g, b = (channel // 85 for channel in rgb)
        palette_codes[index] = r | (g << 2) | (b << 4)
    scene_dir = diag / "doc/scenes"
    scene_dir.mkdir()

    for seq_index, (sequence_id, prefix, _title, count, _loop) in enumerate(SEQUENCES):
        for local_index in range(count):
            global_index = sequence_start + local_index
            frame_id = f"{prefix}{local_index + 1:02d}"
            col, row = local_index, seq_index
            crop = image.crop((col * FRAME_W, row * FRAME_H,
                               (col + 1) * FRAME_W, (row + 1) * FRAME_H))
            frame_rel = Path("res/frames/dr_social_v08_2") / f"{frame_id}.png"
            frame_path = diag / frame_rel
            crop.save(frame_path, format="PNG", transparency=0, optimize=False)
            reopened = Image.open(frame_path)
            if reopened.mode != "P" or reopened.size != (FRAME_W, FRAME_H):
                raise ValueError(f"corte inválido: {frame_id}")
            if reopened.tobytes() != crop.tobytes():
                raise ValueError(f"corte alterou pixels indexados: {frame_id}")

            crop_rows = [list(crop.tobytes()[y * FRAME_W:(y + 1) * FRAME_W])
                         for y in range(FRAME_H)]
            bg_bytes = bytearray(bytes(32))  # tile 0 is black/transparent-equivalent backdrop
            sprite_objects: list[dict] = []
            unique_tiles: set[bytes] = set()
            for tile_y in range(10):
                for tile_x in range(10):
                    tile = bytes(tile_bytes(crop_rows, tile_x, tile_y))
                    bg_bytes.extend(tile)
                    unique_tiles.add(tile)
                    if any(crop_rows[y][x] != 0
                           for y in range(tile_y * 8, tile_y * 8 + 8)
                           for x in range(tile_x * 8, tile_x * 8 + 8)):
                        sprite_objects.append({
                            "x": 88 + tile_x * 8, "y": 56 + tile_y * 8,
                            "tile": 1 + tile_y * 10 + tile_x,
                        })
            tile_blob = bytes(bg_bytes)
            if len(tile_blob) != 32 * 101:
                raise ValueError(f"tile atlas de fundo inesperado: {frame_id}")
            if len(tile_blob) >= BANK_BYTES:
                raise ValueError(f"dados da pose excedem janela ROM de 16 KiB: {frame_id}")
            scanline_counts = [sum(1 for obj in sprite_objects
                                   if obj["y"] <= line < obj["y"] + 8)
                               for line in range(192)]
            peak_scanline = max(scanline_counts, default=0)
            offset = len(blob) % BANK_BYTES
            if offset + len(tile_blob) > BANK_BYTES:
                blob.extend(bytes(BANK_BYTES - offset))
            absolute = len(blob)
            if absolute // BANK_BYTES >= 254:
                raise ValueError("o viewer excederia o espaço de bancos ROM suportado")
            blob.extend(tile_blob)
            bank = FIRST_DATA_BANK + absolute // BANK_BYTES
            bank_offset = absolute % BANK_BYTES
            frame_specs.append({
                "frame_id": frame_id, "sequence_id": sequence_id,
                "bank": bank, "bank_offset": bank_offset,
                "tile_bytes": len(tile_blob),
            })
            scene = {
                "schema": "sprite_scene_manifest_v1", "sprite_size": "8x8",
                "zoomed": False, "screen_h": 192,
                "sprites": sprite_objects,
            }
            scene_path = scene_dir / f"sprite_scene_{frame_id}.json"
            scene_path.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
            frame_manifest.append({
                "frame_id": frame_id, "sequence_id": sequence_id,
                "source_cell_row": row, "source_cell_column": col,
                "res_path": frame_rel.as_posix(),
                "scene_manifest": scene_path.relative_to(diag).as_posix(),
                "sha256": sha256(frame_path),
                "opaque_pixels": sum(1 for value in crop.tobytes() if value != 0),
                "hypothetical_8x8_hardware_objects": len(sprite_objects),
                "hypothetical_8x8_peak_sprites_per_scanline": peak_scanline,
                "hypothetical_8x8_sat_pass": len(sprite_objects) <= 64,
                "hypothetical_8x8_scanline_pass": peak_scanline <= 8,
                "unique_8x8_patterns_in_frame": len(unique_tiles),
                "background_tile_patterns_loaded": 101,
                "tile_bytes_4bpp": len(tile_blob),
                "rom_bank": bank, "rom_bank_offset": bank_offset,
            })
            sprite_audit.append({
                "frame_id": frame_id, "sequence_id": sequence_id,
                "manifest": scene_path.relative_to(diag).as_posix(),
                "hardware_objects": len(sprite_objects),
                "peak_sprites_per_scanline": peak_scanline,
                "sat_pass": len(sprite_objects) <= 64,
                "scanline_pass": peak_scanline <= 8,
            })
        sequence_start += count

    bank_count = math.ceil(len(blob) / BANK_BYTES)
    if bank_count < 1:
        raise ValueError("tile bank vazio")
    blob.extend(bytes(bank_count * BANK_BYTES - len(blob)))
    tile_bin = diag / "assets/dr_social_61_sequence_tiles.bin"
    tile_bin.write_bytes(blob)
    header = diag / "inc/dr_social_61_pose_data.h"
    assert palette_codes is not None
    header.write_text(build_header(frame_specs, palette_codes), encoding="utf-8")

    project_manifest = {
        "name": VIEWER_NAME,
        "platform": "sega_master_system",
        "region_target": ["NTSC", "PAL"],
        "toolchain": {
            "compiler": "sdcc>=4.2", "sdk": "devkitSMS",
            "libs": ["SMSlib", "PSGlib"],
            "makesms_extra": ["-mbank", f"assets/dr_social_61_sequence_tiles.bin:0:{bank_count}:{FIRST_DATA_BANK}"],
        },
        "skeleton_version": 1, "specialization": "fighting",
    }
    (diag / ".mddev").mkdir()
    (diag / ".mddev/project.json").write_text(
        json.dumps(project_manifest, indent=2) + "\n", encoding="utf-8")

    source_origin = f"rascunho/{source.name}"
    provenance = {"assets": [{
        "file": item["res_path"], "origin": source_origin,
        "author": "arte v08.2 aprovada pelo proprietário; recorte indexado exato",
        "tool": "exact_indexed_cell_crop_v1", "role": "personagem",
        "sha256": sha256(diag / source_origin),
        "resource_sha256": item["sha256"],
    } for item in frame_manifest]}
    (diag / "doc/asset_provenance_manifest.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (diag / "doc/frame_manifest_61_pose_v08_2.json").write_text(
        json.dumps(frame_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = {
        "schema": "dr_social_61_pose_conversion_v08_2_v1",
        "status": "converted_diagnostic_candidate",
        "source_path": SOURCE_REL.as_posix(), "source_sha256": sha256(source),
        "conversion": "exact 80x80 palette-indexed cell crops; no pixel edits",
        "source_canvas_px": [640, 720], "grid": [8, 9],
        "frame_canvas_px": [80, 80], "active_pose_count": len(frame_manifest),
        "sequence_counts": [sequence[3] for sequence in SEQUENCES],
        "transparent_index": 0,
        "sms_palette_codes_6bit": palette_codes,
        "diagnostic_render_plane": "background tiles using P1 colors; no SAT objects used by viewer",
        "background_tile_base": BG_TILE_BASE, "background_patterns_per_pose": 101,
        "data_bank_first": FIRST_DATA_BANK,
        "data_bank_count": bank_count, "bank_size_bytes": BANK_BYTES,
        "tile_blob_bytes_padded": len(blob),
        "max_hypothetical_8x8_objects_per_pose": max(item["hypothetical_8x8_hardware_objects"] for item in frame_manifest),
        "max_hypothetical_8x8_sprites_per_scanline": max(item["hypothetical_8x8_peak_sprites_per_scanline"] for item in frame_manifest),
        "hypothetical_8x8_sat_fail_pose_count": sum(not item["hypothetical_8x8_sat_pass"] for item in frame_manifest),
        "hypothetical_8x8_scanline_fail_pose_count": sum(not item["hypothetical_8x8_scanline_pass"] for item in frame_manifest),
        "hypothetical_8x8_scanline_fail_frames": [
            item["frame_id"] for item in frame_manifest
            if not item["hypothetical_8x8_scanline_pass"]
        ],
        "hypothetical_sprite_scene_audit": sprite_audit,
        "frames": frame_manifest,
        "claims": {
            "exact_source_pixel_crops": True,
            "sms_cram_rgb_levels": "pass by exact source palette contract",
            "viewer_framebuffer": "background-plane diagnostic; exact-pixel comparison required",
            "sat_64_per_pose": all(item["sat_pass"] for item in sprite_audit),
            "scanline_8_per_pose": all(item["scanline_pass"] for item in sprite_audit),
            "sprite_runtime_status": "fails if any hypothetical 8x8 scene exceeds VDP limits; this does not block BG diagnostic viewer",
            "combined_gameplay_vram_budget": "not measured",
            "continuous_animation_timing": "not tested; viewer advances manually",
            "gameplay": "not implemented by this diagnostic viewer",
        },
    }
    report_path = diag / "doc/conversion_report_61_pose_v08_2.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    binding = {
        "schema": "rom_asset_binding_v1", "rom_path": f"out/rom/{VIEWER_NAME}.sms",
        "rom_sha256": "pending_build", "rom_size_bytes": 0,
        "entries": [{
            "source": f"../../../../{SOURCE_REL.as_posix()}",
            "res_path": item["res_path"],
            "symbol": "ds_frame_bank/ds_frame_bank_offset/ds_frame_tile_bytes",
            "generated": "inc/dr_social_61_pose_data.h",
            "sha256": item["sha256"],
        } for item in frame_manifest],
    }
    (diag / "doc/rom_asset_binding.json").write_text(
        json.dumps(binding, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (diag / "README.md").write_text(
        f"# Dr. Social v08.2 — viewer de diagnóstico\n\n"
        f"Fonte aprovada: `{SOURCE_REL.as_posix()}`\n\n"
        f"SHA-256: `{sha256(source)}`\n\n"
        "A ROM navega os 61 quadros por tiles de fundo para provar fidelidade "
        "pixel a pixel sem mascarar limites da SAT. As imagens derivadas são "
        "recortes indexados exatos de 80×80. A simulação separada de metasprites "
        "8×8 registra SAT e scanlines por pose; qualquer excedente reprova a "
        "integração do quadro como sprites até uma revisão de escala/encenação. "
        "Este viewer não é a ROM de gameplay e não mede animação contínua, áudio, "
        "FPS ou orçamento simultâneo de cenário/HUD/elenco.\n",
        encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=PROJECT / SOURCE_REL)
    args = parser.parse_args()
    report = make_project(args.source.resolve())
    print(json.dumps({
        "status": report["status"], "diagnostic_project": str(OUT / "project"),
        "source_sha256": report["source_sha256"],
        "frames": report["active_pose_count"], "rom_data_banks": report["data_bank_count"],
        "max_hypothetical_8x8_objects_per_pose": report["max_hypothetical_8x8_objects_per_pose"],
        "max_hypothetical_8x8_sprites_per_scanline": report["max_hypothetical_8x8_sprites_per_scanline"],
        "hypothetical_8x8_scanline_fail_pose_count": report["hypothetical_8x8_scanline_fail_pose_count"],
        "conversion_report": str(OUT / "project/doc/conversion_report_61_pose_v08_2.json"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
