#!/usr/bin/env python3
"""Audit per-frame cutout islands and declared material-color regions.

This gate catches disconnected pixel debris and attached pixels whose colors
do not belong in a declared material band. It does not judge full visual
fidelity; every frame still needs a native-size and nearest-neighbor review.

Usage: audit_sprite_cutout.py --image sheet.png --contract asset_contract.json
       audit_sprite_cutout.py --self-check
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from png_io import read_indexed_png, write_indexed_png, PngError


def _hex_rgb(value):
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        raise ValueError(f"RGB inválido: {value!r}")
    try:
        return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError as exc:
        raise ValueError(f"RGB inválido: {value!r}") from exc


def _components(mask, width, height, connectivity):
    seen = set()
    sizes = []
    neighbors = ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0),
                 (-1, 1), (0, 1), (1, 1))
    if connectivity == 4:
        neighbors = ((0, -1), (-1, 0), (1, 0), (0, 1))
    for y in range(height):
        for x in range(width):
            if not mask[y][x] or (x, y) in seen:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            size = 0
            while stack:
                px, py = stack.pop()
                size += 1
                for dx, dy in neighbors:
                    nx, ny = px + dx, py + dy
                    point = (nx, ny)
                    if (0 <= nx < width and 0 <= ny < height and
                            mask[ny][nx] and point not in seen):
                        seen.add(point)
                        stack.append(point)
            sizes.append(size)
    return sizes


def check_image(image_path, contract):
    errors = []
    try:
        image = read_indexed_png(image_path)
    except (OSError, PngError) as exc:
        return [str(exc)]

    sheet = contract.get("sheet") or {}
    cols, rows = sheet.get("columns"), sheet.get("rows")
    frame = sheet.get("frame_px")
    expected_sheet = sheet.get("sheet_px")
    if (not isinstance(cols, int) or not isinstance(rows, int) or
            not isinstance(frame, list) or len(frame) != 2 or
            not all(isinstance(v, int) and v > 0 for v in frame)):
        return ["contrato precisa declarar columns, rows e frame_px válidos"]
    fw, fh = frame
    if expected_sheet != [cols * fw, rows * fh]:
        errors.append("sheet_px do contrato diverge de columns × rows × frame_px")
    if (image["w"], image["h"]) != (cols * fw, rows * fh):
        errors.append(f"folha {image['w']}x{image['h']} diverge da grade {cols}x{rows} de {fw}x{fh}")
        return errors

    transparent = set(image["trns"])
    transparent_index = (contract.get("palette") or {}).get("transparent_index", 0)
    if transparent_index not in transparent:
        errors.append(f"índice transparente {transparent_index} ausente em tRNS")

    profile = contract.get("pixel_cleanup_profile") or {}
    mode = profile.get("mode", "materials_and_components")
    if mode not in {"materials_and_components", "components_only"}:
        errors.append("pixel_cleanup_profile.mode deve ser materials_and_components ou components_only")
    minimum = profile.get("minimum_opaque_component_px", 0)
    connectivity = profile.get("connectivity", 8)
    if not isinstance(minimum, int) or minimum < 1:
        errors.append("minimum_opaque_component_px deve ser inteiro >= 1")
        minimum = 1
    if connectivity not in (4, 8):
        errors.append("connectivity deve ser 4 ou 8")
        connectivity = 8

    regions = profile.get("regions") or []
    if mode == "materials_and_components" and not regions:
        errors.append("pixel_cleanup_profile precisa declarar ao menos uma região de cor por material")
    if mode == "components_only" and regions:
        errors.append("modo components_only não pode declarar regiões de material")
    if mode == "components_only" and profile.get("material_regions_status") != "pending":
        errors.append("components_only exige material_regions_status=pending; não pode promover o recorte completo")
    parsed_regions = []
    for region in regions:
        try:
            offset = region["offset_px"]
            size = region["size_px"]
            colors = {_hex_rgb(c) for c in region["allowed_rgb"]}
            if (region.get("anchor") != "visible_bbox_top" or
                    len(offset) != 2 or len(size) != 2 or
                    not all(isinstance(v, int) for v in offset + size) or
                    size[0] <= 0 or size[1] <= 0 or not colors):
                raise ValueError("região requer anchor visible_bbox_top, offset/size válidos e allowed_rgb")
            parsed_regions.append((region["name"], offset, size, colors))
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"pixel_cleanup_regions inválida: {exc}")

    pixels, palette = image["pixels"], image["palette"] or []
    for fy in range(rows):
        for fx in range(cols):
            x0, y0 = fx * fw, fy * fh
            mask = [[pixels[y0 + y][x0 + x] not in transparent for x in range(fw)]
                    for y in range(fh)]
            visible = [(x, y) for y in range(fh) for x in range(fw) if mask[y][x]]
            if not visible:
                errors.append(f"frame {fy * cols + fx:02d}: nenhum pixel opaco")
                continue
            top = min(y for _, y in visible)
            cell = fy * cols + fx
            if minimum:
                for component_size in _components(mask, fw, fh, connectivity):
                    if component_size < minimum:
                        errors.append(f"frame {cell:02d}: componente opaco de {component_size}px < {minimum}px")
            for name, (ox, oy), (rw, rh), allowed in parsed_regions:
                rx0, ry0 = ox, top + oy
                if rx0 < 0 or ry0 < 0 or rx0 + rw > fw or ry0 + rh > fh:
                    errors.append(f"frame {cell:02d} região {name}: fora do canvas")
                    continue
                for ry in range(ry0, ry0 + rh):
                    for rx in range(rx0, rx0 + rw):
                        index = pixels[y0 + ry][x0 + rx]
                        if index in transparent:
                            continue
                        if index >= len(palette):
                            errors.append(f"frame {cell:02d} região {name}: índice {index} sem cor de paleta")
                            continue
                        rgb = tuple(palette[index])
                        if rgb not in allowed:
                            errors.append(
                                f"frame {cell:02d} região {name}: RGB #{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X} "
                                f"fora do contrato em ({rx},{ry})")
    return errors


def self_check():
    palette = [(0, 0, 0), (0, 0, 85), (170, 85, 85)]
    rows = [bytearray(16) for _ in range(16)]
    for y in range(2, 6):
        for x in range(5, 9):
            rows[y][x] = 1
    good_path = "/tmp/audit_sprite_cutout_good.png"
    bad_region_path = "/tmp/audit_sprite_cutout_bad_region.png"
    bad_island_path = "/tmp/audit_sprite_cutout_bad_island.png"
    write_indexed_png(good_path, 16, 16, palette, [bytes(r) for r in rows], trns=(0,))
    bad_rows = [bytearray(r) for r in rows]
    bad_rows[2][4] = 2
    write_indexed_png(bad_region_path, 16, 16, palette, [bytes(r) for r in bad_rows], trns=(0,))
    island_rows = [bytearray(r) for r in rows]
    island_rows[14][14] = 1
    write_indexed_png(bad_island_path, 16, 16, palette, [bytes(r) for r in island_rows], trns=(0,))
    contract = {
        "sheet": {"columns": 1, "rows": 1, "frame_px": [16, 16], "sheet_px": [16, 16]},
        "palette": {"transparent_index": 0},
        "pixel_cleanup_profile": {
            "minimum_opaque_component_px": 4,
            "connectivity": 8,
            "regions": [{
                "name": "hair_top", "anchor": "visible_bbox_top",
                "offset_px": [0, 0], "size_px": [16, 6],
                "allowed_rgb": ["#000055"]
            }]
        }
    }
    good = check_image(good_path, contract)
    bad_region = check_image(bad_region_path, contract)
    bad_island = check_image(bad_island_path, contract)
    assert not good, f"self-check: folha limpa reprovada: {good}"
    assert any("fora do contrato" in error for error in bad_region), "self-check: região cromática inválida passou"
    assert any("componente opaco" in error for error in bad_island), "self-check: ilha opaca passou"
    components_only = {
        "sheet": {"columns": 1, "rows": 1, "frame_px": [16, 16], "sheet_px": [16, 16]},
        "palette": {"transparent_index": 0},
        "pixel_cleanup_profile": {
            "mode": "components_only",
            "minimum_opaque_component_px": 2,
            "connectivity": 8,
            "material_regions_status": "pending",
            "regions": [],
        },
    }
    assert not check_image(good_path, components_only), "self-check: clean component-only fixture reprovada"
    island_errors = check_image(bad_island_path, components_only)
    assert any("componente opaco" in error for error in island_errors), \
        "self-check: modo components_only deixou ilha opaca passar"
    print("[SELF-CHECK OK] sprite_cutout (ilhas opacas e cores incompatíveis por região)")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image")
    parser.add_argument("--contract")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        try:
            return self_check()
        except (AssertionError, OSError, PngError) as exc:
            print(f"[SELF-CHECK FAIL] sprite_cutout: {exc}", file=sys.stderr)
            return 1
    if not args.image or not args.contract:
        parser.error("--image e --contract são obrigatórios")
    try:
        with open(args.contract, encoding="utf-8") as handle:
            contract = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] contrato: {exc}", file=sys.stderr)
        return 3
    errors = check_image(args.image, contract)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    profile = contract.get("pixel_cleanup_profile") or {}
    if profile.get("mode") == "components_only":
        print("[PASS] componentes conectados: não há ilha opaca abaixo do mínimo declarado")
        print("[PENDING] regiões/cor por material não declaradas; promoção continua bloqueada")
        return 2
    print("[PASS] cutouts, componentes e regiões de cor no contrato")
    return 0


if __name__ == "__main__":
    sys.exit(main())
