"""Build an exact source-pixel split between the SMS SAT and arena tilemap."""

import argparse
from collections import defaultdict
from functools import cache
import json
from pathlib import Path

from PIL import Image

from make_duel_scene02_assets import blade_pixels, c_values, digest, pixels, planar

PROJECT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = PROJECT / "out/diagnostics"
PILOT = DIAGNOSTICS / "duel_execution_20261119"
LAYOUT = PILOT / "resident-layouts-hayato-priority.json"
BLADE = DIAGNOSTICS / "alis_strong_thrust_round1/grounded_faces_assets_probe/both_faces_assets.h"
PALETTES = PILOT / "generated/duel_scene02_assets.h"
PER_FIGHTER = 4


def sms_color(rgb):
    if len(rgb) != 3 or any(component not in (0, 85, 170, 255) for component in rgb):
        raise ValueError(f"Color outside native SMS palette: {rgb}")
    red, green, blue = (component // 85 for component in rgb)
    return red | (green << 2) | (blue << 4)


def pilot_rasters(sprite_palette):
    layout = json.loads(LAYOUT.read_bytes())["sides"]
    blade = BLADE.read_text("ascii")
    for side, facing in (("left", "left"), ("right", "right")):
        entry = layout[side]
        pool = [pixels(bytes.fromhex(pattern)) for pattern in entry["pool"]]
        origin = 176 if side == "left" else 64
        for actor in ("hayato", "alis"):
            direction = facing if actor == "alis" else ("right" if side == "left" else "left")
            for pose, art in entry[actor].items():
                raster = {}
                for left, top, pattern in art["sat_x_rel_y_tile"]:
                    for index, color in enumerate(pool[pattern]):
                        if color:
                            raster.setdefault((left + index % 8, top + index // 8), sprite_palette[color])
                if actor == "alis" and pose in ("prepare", "thrust"):
                    for position, color in blade_pixels(blade, direction, pose, origin).items():
                        raster.setdefault(position, color)
                    for x, y, color in art["extra_p0_pixels_x_rel_y_color"]:
                        raster.setdefault((x, y), color)
                yield actor, pose, direction, raster


def new_rasters(staged, receipt):
    for pose in receipt["frames"]:
        path = staged / pose["file"]
        if digest(path) != pose["sha256"]:
            raise ValueError(f"Staged art SHA changed: {path}")
        with Image.open(path) as image:
            palette = image.getpalette()
            indices = image.load()
            right = {(x - 64, y + 48): sms_color(palette[3 * indices[x, y]:3 * indices[x, y] + 3])
                     for y in range(image.height) for x in range(image.width) if indices[x, y]}
        tag = f"{pose['action']}_{pose['frame']}"
        yield pose["actor"], tag, "right", right
        yield pose["actor"], tag, "left", {(-x - 1, y): color for (x, y), color in right.items()}


def band_intervals(points, mandatory, slots_per_band):
    minimum = min(points) - 7
    maximum = max(points)
    weight = [0]
    for x in range(minimum, maximum + 9):
        weight.append(weight[-1] + points.get(x, 0))

    @cache
    def choose(x, slots):
        if x > maximum:
            return 0, ()
        options = []
        if x not in mandatory:
            following = choose(x + 1, slots)
            if following is not None:
                options.append(following)
        if slots and weight[x - minimum + 8] > weight[x - minimum]:
            following = choose(x + 8, slots - 1)
            if following is not None:
                score = weight[x - minimum + 8] - weight[x - minimum] + following[0]
                options.append((score, (x, *following[1])))
        return max(options, key=lambda item: (item[0], -len(item[1]))) if options else None

    best = choose(minimum, slots_per_band)
    return None if best is None else best[1]


def make_plan(raster, sprite, background, slots_per_band=PER_FIGHTER, max_objects=None):
    # Colors absent from P1 can only be placed on the tilemap.
    sprite_codes = set(sprite[1:])
    background_codes = set(background)
    if set(raster.values()) - (sprite_codes | background_codes):
        return None
    best = None
    for phase in range(8):
        bands = defaultdict(dict)
        for (x, y), color in raster.items():
            bands[y - (y - phase) % 8][x, y] = color
        objects = []
        spill = {}
        for top, band in sorted(bands.items()):
            if not 0 <= top <= 184:
                break
            mandatory = {x for (x, _), color in band.items() if color not in background_codes}
            weights = defaultdict(int)
            for (x, _), color in band.items():
                if color in sprite_codes:
                    weights[x] += 1
            intervals = band_intervals(weights or {next(iter(band))[0]: 0}, mandatory, slots_per_band)
            if intervals is None:
                break
            transfer = set()
            for left in intervals:
                tile = [0] * 64
                for (x, y), color in band.items():
                    if left <= x < left + 8 and color in sprite_codes:
                        tile[(y - top) * 8 + x - left] = sprite.index(color, 1)
                        transfer.add((x, y))
                if any(tile):
                    objects.append((left, top, planar(tile)))
            spill.update({key: color for key, color in band.items() if key not in transfer})
        else:
            if (set(spill.values()) - background_codes
                    or (max_objects is not None and len(objects) > max_objects)):
                continue
            phases = [{((x + shift) // 8, y // 8) for x, y in spill} for shift in range(8)]
            score = max(map(len, phases)), len(objects), len(spill)
            if best is None or score < best[0]:
                best = score, objects, spill, phases
    if best is None:
        return None
    _, objects, spill, phases = best
    reconstructed = spill.copy()
    for left, top, tile in objects:
        for offset, index in enumerate(pixels(tile)):
            if index:
                key = left + offset % 8, top + offset // 8
                if key in reconstructed:
                    raise ValueError("Planner produced overlapping source pixels")
                reconstructed[key] = sprite[index]
    if reconstructed != raster:
        raise ValueError("Planner changed source pixels")
    return objects, spill, phases


def arena_crossover(frames, margin=63):
    max_objects = max_cells = max_overlap = max_dirty_bytes = max_first = 0
    for h_direction, a_direction in (("right", "left"), ("left", "right")):
        hayato = [row for row in frames if row["actor"] == "hayato" and row["direction"] == h_direction]
        alis = [row for row in frames if row["actor"] == "alis" and row["direction"] == a_direction]
        first = {"idle", "R01", "prepare"}
        max_first = max(max_first, sum(
            row["sprite_count"] for row in hayato + alis
            if row["pose"] in first or row["pose"].endswith("_1")
        ))
        max_gap = 255 - 2 * margin
        shifts = range(24, max_gap + 1) if h_direction == "right" else range(-max_gap, -23)
        for gap in shifts:
            for h_phase in range(8):
                a_col, a_phase = divmod(h_phase + gap, 8)
                abc = [(a, {(x + a_col, y) for x, y in a["background_cells_by_phase"][a_phase]}) for a in alis]
                for h in hayato:
                    hbc = {tuple(cell) for cell in h["background_cells_by_phase"][h_phase]}
                    for a, cells in abc:
                        sat = h["sprite_count"] + a["sprite_count"]
                        total = len(hbc | cells)
                        max_objects = max(max_objects, sat)
                        max_cells = max(max_cells, total)
                        max_overlap = max(max_overlap, len(hbc & cells))
                        # Fresh BG patterns + PNT entries + visible SAT. Omits
                        # VDP command writes, clearing prior PNT, HUD and code.
                        max_dirty_bytes = max(max_dirty_bytes, total * 34 + sat * 3 + (sat < 64))
    return {
        "max_sat": max_objects,
        "max_background_cells": max_cells,
        "max_background_cells_to_merge": max_overlap,
        "peak_all_dirty_data_bytes": max_dirty_bytes,
        "startup_sprite_slots_disjoint": max_first,
        "spare_sprite_slots_with_all_startups": 256 - max_first,
        "arena_gap_pixels": [24, max_gap],
    }


def startup_residency(choices):
    # Each side has its own boot atlas so the choices may differ by orientation.
    tradeoffs = {}
    for hayato_face, alis_face in (("right", "left"), ("left", "right")):
        rows = {actor: [options for (owner, face, _), options in choices.items()
                        if owner == actor and face == direction]
                for actor, direction in (("hayato", hayato_face), ("alis", alis_face))}
        limits = {}
        for actor, poses in rows.items():
            for max_bg in range(26):
                fitting = [[tiles for bg, tiles in options if bg <= max_bg] for options in poses]
                limits[actor, max_bg] = sum(map(min, fitting)) if all(fitting) else None
        orientation = []
        for budget in (8, 12, 16, 20, 24, 25):
            fitting = []
            for h_limit in range(budget + 1):
                a_limit = budget - h_limit
                h_tiles, a_tiles = limits["hayato", h_limit], limits["alis", a_limit]
                if h_tiles is not None and a_tiles is not None:
                    fitting.append((h_tiles + a_tiles, h_limit, a_limit))
            if fitting:
                slots, h_limit, a_limit = min(fitting)
                orientation.append({"background_limit": budget, "startup_sprite_slots": slots,
                                    "unassigned_sprite_slots": 256 - slots,
                                    "hayato_background_limit": h_limit,
                                    "alis_background_limit": a_limit})
        tradeoffs[hayato_face] = orientation
    return tradeoffs


def generate(staged, destination):
    receipt = json.loads((staged / "staging-report.json").read_bytes())
    header = PALETTES.read_text("ascii")
    sprite = c_values(header, "mof_duel_sprite_palette")
    background = list(dict.fromkeys(c_values(header, "mof_duel_bg_palette")))
    for rgb in receipt["best_case_background_offload"]["added_rgb"]:
        color = sms_color(rgb)
        if color not in background:
            background.append(color)
    if len(background) > 16 or len(sprite) != 16:
        raise ValueError("Plan exceeds a native SMS palette")

    frames = []
    rejected = []
    startup_choices = {}
    for family in (pilot_rasters(sprite), new_rasters(staged, receipt)):
        for actor, pose, direction, raster in family:
            identity = {"actor": actor, "pose": pose, "direction": direction}
            result = make_plan(raster, sprite, background)
            if result is None:
                rejected.append(identity)
                continue
            objects, spill, phases = result
            frames.append({**identity, "sprite_count": len(objects),
                           "sprite_cells": [[x, y, tile.hex()] for x, y, tile in objects],
                           "background_pixels": [[x, y, color] for (x, y), color in sorted(spill.items())],
                           "background_cells_by_phase": [sorted(cells) for cells in phases]})
            if pose in {"idle", "R01", "prepare"} or pose.endswith("_1"):
                candidates = [(max(map(len, phases)), len(objects))]
                for cap in range(1, PER_FIGHTER):
                    alternate = make_plan(raster, sprite, background, cap)
                    if alternate:
                        alternate_objects, _, alternate_phases = alternate
                        candidates.append((max(map(len, alternate_phases)), len(alternate_objects)))
                startup_choices[actor, direction, pose] = candidates
    combinations = []
    for h_direction, a_direction in (("right", "left"), ("left", "right")):
        hayato = [row for row in frames if row["actor"] == "hayato" and row["direction"] == h_direction]
        alis = [row for row in frames if row["actor"] == "alis" and row["direction"] == a_direction]
        for h in hayato:
            for a in alis:
                count = max(map(len, h["background_cells_by_phase"])) + max(map(len, a["background_cells_by_phase"]))
                combinations.append(count)
    crossover = arena_crossover(frames)
    proof = {
        "kind": "exact independent source-layer decomposition",
        "inputs": {str(path.relative_to(PROJECT)): digest(path)
                   for path in (LAYOUT, BLADE, PALETTES, staged / "staging-report.json")},
        "sprite_palette": sprite, "background_palette": background,
        "planned_frames": len(frames), "rejected": rejected,
        "max_sprites_per_scanline": PER_FIGHTER * 2,
        "max_sat": crossover["max_sat"],
        "max_background_cells_before_overlap": max(combinations, default=0),
        "crossover": crossover,
        "startup_residency_tradeoffs": startup_residency(startup_choices),
        "limitations": "One fighter's sprite and tilemap pixels reconstruct exactly. "
        "Inter-fighter priority, slot residency, upload, VBlank and live presentation require separate checks.",
        "frames": frames,
    }
    destination.write_text(json.dumps(proof, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in proof.items() if key != "frames"}))
    return bool(frames) and not rejected and proof["max_sat"] <= 64


def extend_actions(base, stage_files, destination):
    plan = json.loads(base.read_bytes())
    if plan["rejected"] or len(plan["frames"]) != 58:
        raise ValueError("The action plan needs the verified B08 decomposition")
    plan["base_plan_sha256"] = digest(base)
    added = []
    for receipt in stage_files:
        rows = json.loads(receipt.read_bytes())
        for row in rows:
            added.append((row["actor"], f"{row['action']}_{row['frame']}"))
        for actor, pose, face, raster in new_rasters(receipt.parent, {"frames": rows}):
            identity = {"actor": actor, "pose": pose, "direction": face}
            result = None
            for slots in range(PER_FIGHTER, 0, -1):
                result = make_plan(raster, plan["sprite_palette"], plan["background_palette"],
                                   slots, max_objects=32)
                if result is not None:
                    break
            if result is None or not result[0]:
                plan["rejected"].append(identity)
                continue
            objects, spill, phases = result
            plan["frames"].append({**identity, "sprite_count": len(objects),
                                   "sprite_cells": [[x, y, tile.hex()] for x, y, tile in objects],
                                   "background_pixels": [[x, y, color] for (x, y), color in sorted(spill.items())],
                                   "background_cells_by_phase": [sorted(cells) for cells in phases]})
    plan["added_poses"] = added
    plan["planned_frames"] = len(plan["frames"])
    plan["crossover"] = arena_crossover(plan["frames"])
    plan["max_sat"] = plan["crossover"]["max_sat"]
    destination.write_text(json.dumps(plan, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"poses": plan["planned_frames"], "rejected": plan["rejected"],
                      "crossover": plan["crossover"]}))
    return not plan["rejected"] and plan["max_sat"] <= 64


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("staged", type=Path)
    cli.add_argument("out", type=Path)
    cli.add_argument("--extend", type=Path, action="append", metavar="STAGE_JSON",
                     help="Use the first argument as an existing plan and add these staged poses")
    args = cli.parse_args()
    if args.extend:
        raise SystemExit(0 if extend_actions(args.staged, args.extend, args.out) else 1)
    raise SystemExit(0 if generate(args.staged.resolve(), args.out.resolve()) else 1)
