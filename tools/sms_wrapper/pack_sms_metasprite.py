#!/usr/bin/env python3
"""Pack indexed SMS pose PNGs into deduplicated 4bpp tiles/metasprites.

This tool packs authored pixels; it does not draw, resize, quantize, or approve
them. Each input PNG is one pose on an 8x8-aligned canvas, using index 0 as
transparent and the same SMS-legal indexed palette as every other pose.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from png_io import PngError, read_indexed_png, write_indexed_png  # noqa: E402
from png_to_sms_tiles import tile_bytes  # noqa: E402

SMS_CHANNELS = {0, 85, 170, 255}
SAT_LIMIT = 64
SCANLINE_LIMIT = 8
SPRITE_PATTERN_LIMIT = 256
METASPRITE_END = 0x80


def safe_sprite_pattern_capacity(tile_base: int, sprite_pattern_base_address: int,
                                 name_table_base_address: int) -> int:
    """Return patterns that fit both the sprite index window and free VRAM.

    SMS sprite patterns have 8-bit indices, but the selected VRAM half can
    overlap the BG name table. The scene layout, not just the index range,
    determines how many patterns can be resident together.
    """
    if not 0 <= tile_base < SPRITE_PATTERN_LIMIT:
        raise ValueError("tile_base precisa estar entre 0 e 255")
    if sprite_pattern_base_address not in (0x0000, 0x2000):
        raise ValueError("base de padrões de sprite deve ser 0x0000 ou 0x2000")
    if not 0 <= name_table_base_address <= 0x4000:
        raise ValueError("base da name table precisa estar entre 0x0000 e 0x4000")
    first_pattern_address = sprite_pattern_base_address + tile_base * 32
    physical_capacity = (name_table_base_address - first_pattern_address) // 32
    return max(0, min(SPRITE_PATTERN_LIMIT - tile_base, physical_capacity))


def _sms_code(rgb: tuple[int, int, int]) -> int:
    if any(channel not in SMS_CHANNELS for channel in rgb):
        raise ValueError(f"RGB fora da grade de cor SMS: {rgb}")
    r, g, b = (channel // 85 for channel in rgb)
    return r | (g << 2) | (b << 4)


def _symbol(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not result or result[0].isdigit():
        result = "asset_" + result
    return result


def _c_array(name: str, values: list[int], width: int = 16) -> str:
    lines = []
    for start in range(0, len(values), width):
        lines.append("    " + ", ".join(f"0x{value:02X}" for value in values[start:start + width]))
    body = ",\n".join(lines)
    return f"const unsigned char {name}[{len(values)}] = {{\n{body}\n}};\n"


def pack_poses(pose_specs: list[tuple[str, Path]], tile_base: int = 0,
               reserve_blank: bool = False,
               max_patterns: int | None = None) -> dict:
    if not pose_specs:
        raise ValueError("informe pelo menos uma pose")
    if not 0 <= tile_base < SPRITE_PATTERN_LIMIT:
        raise ValueError("tile_base precisa estar entre 0 e 255")
    if max_patterns is not None and not 0 <= max_patterns <= SPRITE_PATTERN_LIMIT - tile_base:
        raise ValueError("max_patterns precisa caber na janela lógica do sprite")
    names = [_symbol(name) for name, _path in pose_specs]
    if len(set(names)) != len(names):
        raise ValueError("nomes de pose duplicados após normalização C")

    poses = []
    expected_size = None
    expected_palette = None
    for name, path in zip(names, (item[1] for item in pose_specs)):
        image = read_indexed_png(str(path))
        width, height = image["w"], image["h"]
        if width == 0 or height == 0 or width % 8 or height % 8:
            raise ValueError(f"{path}: canvas {width}x{height} não está alinhado a 8x8")
        if width > 128 or height > 128:
            raise ValueError(f"{path}: offsets do metasprite excedem signed char (máx. 128x128)")
        if 0 not in image["trns"] or image["trns"] - {0}:
            raise ValueError(f"{path}: índice 0 deve ser a única transparência")
        used = {index for row in image["pixels"] for index in row}
        if 0 not in used or max(used, default=0) > 15:
            raise ValueError(f"{path}: índices usados devem estar entre 0 e 15 e incluir 0")
        if any(index >= len(image["palette"]) for index in used):
            raise ValueError(f"{path}: índice de pixel sem entrada PLTE")
        for index in used - {0}:
            _sms_code(image["palette"][index])
        size = (width, height)
        if expected_size is None:
            expected_size = size
            expected_palette = image["palette"]
        elif size != expected_size:
            raise ValueError(f"{path}: dimensões diferem do primeiro frame {expected_size}")
        elif image["palette"] != expected_palette:
            raise ValueError(f"{path}: PLTE difere; mapear explicitamente a paleta comum antes do pack")

        objects = []
        map_cells = []
        for ty in range(height // 8):
            for tx in range(width // 8):
                opaque = any(image["pixels"][y][x] != 0
                             for y in range(ty * 8, ty * 8 + 8)
                             for x in range(tx * 8, tx * 8 + 8))
                map_cells.append(None if not opaque else bytes(tile_bytes(image["pixels"], tx, ty)))
                if opaque:
                    objects.append({"x": tx * 8, "y": ty * 8,
                                    "cell_x": tx, "cell_y": ty})
        if len(objects) > SAT_LIMIT:
            raise ValueError(f"{path}: {len(objects)} objetos excedem SAT={SAT_LIMIT}")
        counts = [sum(1 for item in objects if item["y"] <= y < item["y"] + 8)
                  for y in range(192)]
        peak = max(counts, default=0)
        if peak > SCANLINE_LIMIT:
            raise ValueError(f"{path}: pico {peak}/scanline excede SMS={SCANLINE_LIMIT}")
        if any(((item["y"] - 1) & 0xFF) == 0xD0 for item in objects):
            raise ValueError(f"{path}: sprite colide com o terminador SAT em Y=0xD0")
        poses.append({"name": name, "path": str(path), "image": image,
                      "map_cells": map_cells, "objects": objects,
                      "peak_scanline": peak, "counts": counts})

    blank = bytes(32)
    unique: list[bytes] = [blank] if reserve_blank else []
    pattern_ids: dict[bytes, int] = {blank: tile_base} if reserve_blank else {}
    for pose in poses:
        new_map = []
        for pattern in pose["map_cells"]:
            if pattern is None:
                new_map.append(None)
                continue
            if pattern not in pattern_ids:
                pattern_ids[pattern] = tile_base + len(unique)
                unique.append(pattern)
            new_map.append(pattern_ids[pattern])
        pose["tile_map"] = new_map
        for item in pose["objects"]:
            cell = item["cell_y"] * (expected_size[0] // 8) + item["cell_x"]
            item["tile"] = new_map[cell]
        meta = []
        for item in pose["objects"]:
            meta.extend((item["x"], item["y"], item["tile"]))
        meta.append(METASPRITE_END)
        pose["meta"] = meta
    if tile_base + len(unique) > SPRITE_PATTERN_LIMIT:
        raise ValueError(f"padrões {tile_base}..{tile_base + len(unique) - 1} excedem a janela 0..255")
    if max_patterns is not None and len(unique) > max_patterns:
        raise ValueError(
            f"{len(unique)} padrões excedem a janela física declarada de "
            f"{max_patterns} padrões antes da name table"
        )

    palette_codes = [0] * 16
    for index, rgb in enumerate(expected_palette[:16]):
        if index == 0:
            continue
        palette_codes[index] = _sms_code(rgb)
    width, height = expected_size
    return {"poses": poses, "width": width, "height": height,
            "palette_codes": palette_codes, "unique_patterns": len(unique) - (1 if reserve_blank else 0),
            "loaded_patterns": len(unique), "tile_bytes": b"".join(unique),
            "tile_base": tile_base, "reserve_blank": reserve_blank,
            "max_patterns": max_patterns}


def header_text(packed: dict, prefix: str) -> str:
    prefix = _symbol(prefix)
    flat_tiles = list(packed["tile_bytes"])
    rows = ["/* Generated by pack_sms_metasprite.py; source pixels are unchanged. */",
            f"#define {prefix.upper()}_TILE_BASE {packed['tile_base']}u",
            f"#define {prefix.upper()}_TILE_COUNT {packed['loaded_patterns']}u",
            f"#define {prefix.upper()}_TILE_BYTES {len(flat_tiles)}u",
            _c_array(f"{prefix}_tiles", flat_tiles),
            _c_array(f"{prefix}_palette", packed["palette_codes"])]
    for pose in packed["poses"]:
        map_values = [0xFF if value is None else value for value in pose["tile_map"]]
        rows.append(_c_array(f"{prefix}_{pose['name']}_map", map_values))
        rows.append(_c_array(f"{prefix}_{pose['name']}_meta", pose["meta"]))
    return "\n".join(rows)


def write_bundle(packed: dict, prefix: str, header_path: Path,
                 manifest_dir: Path) -> dict:
    header_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    header_path.write_text(header_text(packed, prefix), encoding="utf-8")
    manifests = []
    for pose in packed["poses"]:
        manifest = {"schema": "sprite_scene_manifest_v1", "sprite_size": "8x8",
                    "zoomed": False, "screen_h": 192,
                    "sprites": [{"x": item["x"], "y": item["y"], "tile": item["tile"]}
                                for item in pose["objects"]]}
        path = manifest_dir / f"sprite_scene_{pose['name']}.json"
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        manifests.append(str(path))
    report = {"schema": "sms_metasprite_pack_v1", "status": "packed_candidate",
              "header": str(header_path), "pose_manifests": manifests,
              "canvas_px": [packed["width"], packed["height"]],
              "tile_base": packed["tile_base"], "unique_patterns": packed["unique_patterns"],
              "loaded_patterns_including_reserved_blank": packed["loaded_patterns"],
              "max_resident_patterns": packed["max_patterns"],
              "pattern_window": packed.get("pattern_window"),
              "tile_bytes_4bpp": len(packed["tile_bytes"]),
              "reserve_blank_tile": packed["reserve_blank"],
              "poses": [{"name": pose["name"], "objects": len(pose["objects"]),
                         "peak_scanline": pose["peak_scanline"],
                         "occupied_cells": sum(value is not None for value in pose["tile_map"])}
                        for pose in packed["poses"]],
              "palette_codes_6bit": packed["palette_codes"]}
    report_path = header_path.with_suffix(".pack.json")
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def self_check() -> int:
    import tempfile
    import shutil
    root = Path(tempfile.mkdtemp(prefix="smsmeta_"))
    try:
        palette = [(0, 0, 0), (85, 0, 0)]
        rows = [bytes([1 if x == y else 0 for x in range(16)]) for y in range(8)]
        idle = root / "idle.png"
        action_rows = [bytes([0] * 8 + list(rows[y][:8])) for y in range(8)]
        action = root / "action.png"
        write_indexed_png(str(idle), 16, 8, palette, rows, trns=(0,))
        write_indexed_png(str(action), 16, 8, palette, action_rows, trns=(0,))
        packed = pack_poses([("idle", idle), ("action", action)], reserve_blank=True)
        assert packed["unique_patterns"] == 1 and packed["loaded_patterns"] == 2
        assert packed["tile_bytes"][:32] == bytes(32)
        assert packed["poses"][0]["meta"] == [0, 0, 1, METASPRITE_END]
        assert packed["poses"][1]["meta"] == [8, 0, 1, METASPRITE_END]
        assert safe_sprite_pattern_capacity(1, 0x2000, 0x3800) == 191
        assert safe_sprite_pattern_capacity(0, 0x0000, 0x3800) == 256
        try:
            pack_poses([("window", idle), ("window_action", action)],
                       reserve_blank=True, max_patterns=1)
        except ValueError as exc:
            assert "janela física" in str(exc)
        else:
            raise AssertionError("padrões acima da name table deveriam reprovar")
        bad_palette = root / "bad_palette.png"
        write_indexed_png(str(bad_palette), 16, 8, [(0, 0, 0), (0, 85, 0)],
                          action_rows, trns=(0,))
        try:
            pack_poses([("bad", idle), ("bad_palette", bad_palette)], reserve_blank=True)
        except ValueError:
            pass
        else:
            raise AssertionError("paleta incompatível deveria reprovar")
        crowded = root / "crowded.png"
        crowded_rows = [bytes([0] + [1] * 79) for _ in range(8)]
        write_indexed_png(str(crowded), 80, 8, palette, crowded_rows, trns=(0,))
        try:
            pack_poses([("crowded", crowded)], reserve_blank=True)
        except ValueError as exc:
            assert "scanline" in str(exc)
        else:
            raise AssertionError("mais de 8 objetos/scanline deveria reprovar")
        print("[SELF-CHECK OK] pack_sms_metasprite (dedupe, tile0 reservado, paleta e scanline)")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose", action="append", default=[], metavar="NOME=PNG")
    parser.add_argument("--prefix", default="actor")
    parser.add_argument("--tile-base", type=int, default=0)
    parser.add_argument("--reserve-blank", action="store_true")
    parser.add_argument("--sprite-pattern-base", type=lambda value: int(value, 0))
    parser.add_argument("--name-table-base", type=lambda value: int(value, 0))
    parser.add_argument("--header", type=Path)
    parser.add_argument("--manifest-dir", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        return self_check()
    if not args.header or not args.manifest_dir or not args.pose:
        parser.error("--pose, --header e --manifest-dir são obrigatórios")
    specs = []
    for item in args.pose:
        name, sep, path = item.partition("=")
        if not sep or not name or not path:
            parser.error("--pose deve usar NOME=PNG")
        specs.append((name, Path(path)))
    if (args.sprite_pattern_base is None) != (args.name_table_base is None):
        parser.error("--sprite-pattern-base e --name-table-base devem ser informados juntos")
    max_patterns = None
    pattern_window = None
    if args.sprite_pattern_base is not None:
        max_patterns = safe_sprite_pattern_capacity(
            args.tile_base, args.sprite_pattern_base, args.name_table_base
        )
        pattern_window = {
            "sprite_pattern_base_address": args.sprite_pattern_base,
            "name_table_base_address": args.name_table_base,
            "tile_base": args.tile_base,
            "max_resident_patterns": max_patterns,
        }
    try:
        packed = pack_poses(specs, tile_base=args.tile_base,
                            reserve_blank=args.reserve_blank,
                            max_patterns=max_patterns)
        packed["pattern_window"] = pattern_window
        report = write_bundle(packed, args.prefix, args.header, args.manifest_dir)
    except (OSError, PngError, ValueError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
