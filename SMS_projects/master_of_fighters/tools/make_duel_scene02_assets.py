"""Materialize the Scene 02 pilot layouts and bake the P0 blade overlays."""

import argparse
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import re


HAYATO = ("idle", "R01", "R02", "R03", "R04", "R05", "R06")
ALIS = ("idle", "prepare", "thrust", "recover")
PROJECT = Path(__file__).resolve().parents[1]


def c_values(text, name):
    data = re.search(rf"\b{name}\[\d+\]\s*=\s*\{{([^}}]*)\}}", text)
    if not data:
        raise ValueError(f"Missing C symbol {name}")
    return [int(value, 0) for value in re.findall(r"0x[0-9a-fA-F]+|\d+", data[1])]


def pixels(tile):
    return [
        sum(((tile[y * 4 + plane] >> (7 - x)) & 1) << plane for plane in range(4))
        for y, x in product(range(8), repeat=2)
    ]


def planar(tile):
    return bytes(
        sum(((tile[y * 8 + x] >> plane) & 1) << (7 - x) for x in range(8))
        for y, plane in product(range(8), range(4))
    )


def blocks(data):
    if len(data) % 32:
        raise ValueError("Incomplete pattern")
    return [bytes(data[n:n + 32]) for n in range(0, len(data), 32)]


def array(symbol, data):
    values = list(data)
    if any(not 0 <= value < 256 for value in values):
        raise ValueError(f"Value outside byte range in {symbol}")
    lines = [", ".join(f"0x{value:02x}" for value in values[n:n + 16])
             for n in range(0, len(values), 16)]
    return f"const unsigned char {symbol}[{len(values)}] = {{\n    " + ",\n    ".join(lines) + "\n};"


def tile_plan(side):
    patterns = [bytes.fromhex(value) for value in side["pool"]]
    frames = [(actor, name, data["sat_x_rel_y_tile"])
              for actor, poses in (("hayato", side["hayato"]), ("alis", side["alis"]))
              for name, data in poses.items()]
    by_frame = [{tile for _, _, tile in entries} for _, _, entries in frames]
    needed = max(0, len(patterns) - 256)
    exclusive = {}
    for i, (actor, pose, _) in enumerate(frames):
        if actor == "alis":
            other = set().union(*(ids for j, ids in enumerate(by_frame) if i != j))
            ids = sorted(by_frame[i] - other)
            if len(ids) >= needed:
                exclusive[pose] = ids[:needed]
    bank_pair = next(iter(combinations(exclusive, 2)), None) if needed else None
    if needed and not bank_pair:
        raise ValueError("Atlas exceeds 256 tiles without a disjoint Alis overlay pair")
    overlay = {pose: exclusive[pose] for pose in bank_pair} if bank_pair else {}
    dynamic = set().union(*overlay.values())
    base_ids = [i for i in range(len(patterns)) if i not in dynamic]
    remap = {tile: i for i, tile in enumerate(base_ids)}
    for ids in overlay.values():
        remap.update((tile, len(base_ids) + i) for i, tile in enumerate(ids))
    sprite_data = {}
    for actor, pose, entries in frames:
        bank = list(overlay).index(pose) + 1 if actor == "alis" and pose in overlay else 0
        encoded = [(x + 128, y, remap[tile]) for x, y, tile in entries]
        live_patterns = [patterns[i] for i in base_ids]
        if bank:
            live_patterns.extend(patterns[i] for i in overlay[pose])
        for new, old in zip(encoded, entries, strict=True):
            if live_patterns[new[2]] != patterns[old[2]]:
                raise ValueError("Tile residency changes image")
        sprite_data[actor, pose] = bank, encoded
    return [patterns[i] for i in base_ids], {
        pose: [patterns[i] for i in ids] for pose, ids in overlay.items()
    }, sprite_data


def blade_pixels(header, face, pose, origin):
    palette = c_values(header, "alis_sample_palette")
    patterns = blocks(c_values(header, "alis_bg_tiles"))
    values = c_values(header, f"alis_bg_{face}_{pose}")
    if values[-1] != 255:
        raise ValueError("Missing blade map terminator")
    result = {}
    for col, row, i in zip(values[:-1:3], values[1:-1:3], values[2:-1:3], strict=True):
        for n, index in enumerate(pixels(patterns[i])):
            if index:
                result[col * 8 + n % 8 - origin, row * 8 + n // 8] = palette[index]
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(layout, generated):
    receipt = json.loads(layout.read_bytes())
    bg_path = PROJECT / "data/source_art/scenes/cena01_duel_read/cena01_bg.h"
    alis_path = PROJECT / "out/diagnostics/alis_strong_thrust_round1/grounded_faces_assets_probe/both_faces_assets.h"
    stage = bg_path.read_text("ascii")
    blade_source = alis_path.read_text("ascii")
    stage_palette = c_values(stage, "cena01_bg_palette")
    stage_patterns = blocks(c_values(stage, "cena01_tiles"))
    stage_rows = [c_values(stage, "cena01_map")[row * 32:(row + 1) * 32] for row in range(24)]
    stage_rows[0] = stage_rows[1] = [256] * 32
    if any(len(set(row)) != 1 for row in stage_rows):
        raise ValueError("P0 baking expects the existing horizontally uniform arena rows")
    row_ids = [row[0] - 256 for row in stage_rows]
    stage_used = set(row_ids) | {5}
    colors = {stage_palette[index] for slot in stage_used for index in pixels(stage_patterns[slot])}
    decals = {}
    for side, values in receipt["sides"].items():
        if not values["pass"] or values["max_scanline"] > 8 or values["max_sat"] > 64:
            raise ValueError(f"Unsupported fixed SAT layout for {side}")
        for pose in ("prepare", "thrust"):
            facing, origin = ("left", 176) if side == "left" else ("right", 64)
            artwork = blade_pixels(blade_source, facing, pose, origin)
            for x, y, color in values["alis"][pose]["extra_p0_pixels_x_rel_y_color"]:
                if (x, y) in artwork:
                    raise ValueError("Alis SAT/BG artwork overlaps before recomposition")
                artwork[x, y] = color
            decals[side, pose] = artwork
            colors.update(artwork.values())
    p0 = [stage_palette[0], *sorted(colors - {stage_palette[0]})]
    if len(p0) > 16:
        raise ValueError("Exact scene and blade require more than the SMS P0 palette")
    p0.extend([0] * (16 - len(p0)))
    rebased = [
        [p0.index(stage_palette[idx]) for idx in pixels(tile)] if i in stage_used else [0] * 64
        for i, tile in enumerate(stage_patterns)
    ]
    chunks = ['/* Generated by make_duel_scene02_assets.py. */',
              array("mof_duel_bg_palette", p0),
              array("mof_duel_bg_stage", b"".join(map(planar, rebased))),
              array("mof_duel_bg_rows", row_ids)]
    patches = []
    max_cells = 0
    edge = 0
    measurements = {}
    for number, side in enumerate(("left", "right")):
        value = receipt["sides"][side]
        if number == 0:
            chunks.append(array("mof_duel_sprite_palette", value["p1_palette"]))
        elif value["p1_palette"] != receipt["sides"]["left"]["p1_palette"]:
            raise ValueError("Palettes must agree across faces")
        base, overlay, metas = tile_plan(value)
        chunks.append(array(f"mof_duel_atlas_{number}", b"".join(base)))
        banks = ["0"]
        for pose, bank in overlay.items():
            name = f"mof_duel_overlay_{number}_{pose}"
            chunks.append(array(name, b"".join(bank)))
            banks.append(name)
        for actor, poses in (("hayato", HAYATO), ("alis", ALIS)):
            pose_rows = []
            for pose in poses:
                bank, objects = metas[actor, pose]
                for x, _, _ in objects:
                    edge = max(edge, abs(x-128), abs(x-128+7))
                name = f"mof_duel_{actor}_{pose}_{number}"
                chunks.append(array(name, [len(objects), bank, *(v for entry in objects for v in entry)]))
                pose_rows.append(name)
            chunks.append(f"const unsigned char *const mof_duel_{actor}_poses_{number}[] = " +
                          "{" + ", ".join(pose_rows) + "};")
        chunks.append(f"const unsigned char *const mof_duel_overlays_{number}[] = " +
                      "{" + ", ".join(banks) + "};")
        measurements[side] = {"static_patterns": len(base), "overlay_patterns": max(map(len, overlay.values()), default=0)}
        for pose in ("prepare", "thrust"):
            frames = []
            for phase in range(8):
                cells = {}
                for (x, y), color in decals[side, pose].items():
                    edge = max(edge, abs(x))
                    col, row = (x + phase) // 8, y // 8
                    tile = cells.setdefault((col, row), list(rebased[row_ids[row]]))
                    tile[(y % 8) * 8 + (x + phase) % 8] = p0.index(color)
                row_data = []
                for (col, row), tile in sorted(cells.items()):
                    pattern = planar(tile)
                    if pattern not in patches:
                        patches.append(pattern)
                    row_data += [col + 128, row, patches.index(pattern)]
                max_cells = max(max_cells, len(cells))
                name = f"mof_duel_patch_{number}_{pose}_{phase}"
                chunks.append(array(name, [len(cells), *row_data]))
                frames.append(name)
            chunks.append(f"const unsigned char *const mof_duel_patch_{number}_{pose}[] = " +
                          "{" + ", ".join(frames) + "};")
    chunks += [array("mof_duel_bg_patches", b"".join(patches)),
               f"#define MOF_DUEL_BG_PATCH_MAX {max_cells}u",
               f"#define MOF_DUEL_ARENA_MARGIN {edge + 8}u"]
    for number, allocation in enumerate(measurements.values()):
        chunks += [
            f"#define MOF_DUEL_STATIC_{number} {allocation['static_patterns']}u",
            f"#define MOF_DUEL_OVERLAY_{number} {allocation['overlay_patterns']}u",
        ]
    generated.mkdir(parents=True, exist_ok=True)
    path = generated / "duel_scene02_assets.h"
    path.write_text("\n\n".join(chunks) + "\n", encoding="ascii")
    proof = {"scope": "Diagnostic assets; SAT layout, exact static tile remap, representative stage rows and baked blade patches",
             "inputs": {str(p.relative_to(PROJECT)): digest(p) for p in (layout, bg_path, alis_path)},
             "header_sha256": digest(path), "atlas": measurements, "p0": p0,
             "max_background_cells": max_cells, "patch_patterns": len(patches), "arena_margin": edge+8}
    (generated / "asset-report.json").write_text(json.dumps(proof, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(proof))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("generated", type=Path)
    args = parser.parse_args()
    generate(args.layout.resolve(), args.generated.resolve())
