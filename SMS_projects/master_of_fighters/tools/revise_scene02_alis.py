"""Register the authored Alis poses to the banked Scene 02 guard."""

import argparse
import json
from pathlib import Path

from make_duel_scene02_assets import digest, pixels
from plan_scene02_repertoire import arena_crossover, make_plan


def raster(frame, palette):
    result = {(x, y): color for x, y, color in frame["background_pixels"]}
    for left, top, pattern in frame["sprite_cells"]:
        for offset, index in enumerate(pixels(bytes.fromhex(pattern))):
            if index:
                result[left + offset % 8, top + offset // 8] = palette[index]
    return result


def hip_center(pose):
    # The first complete leg row below the tunic establishes the join.
    row = [x for x, y in pose if y == 124]
    if not row:
        raise ValueError("Missing leg registration row")
    return (min(row) + max(row)) / 2


# Contact, compression, passing, next contact. Values are horizontal lean,
# hip height offset, sword tip offset, shield X/Y and planted sole X.
WALK_KEYS = {
    "forward": ((0, 0, 0, 0, 0, 0), (1, 2, -1, 1, 1, 0), (1, -2, 2, 0, 1, 6), (0, 0, 1, -1, -1, 0)),
    "back": ((0, 0, 1, 0, 0, 0), (-1, 2, 2, -1, 1, 0), (-1, -2, 0, 0, 1, 4), (0, 0, -1, 1, -1, 0)),
}


def shield_raster(guard, offset=0):
    shield_left = (21, 20, 20, 20, 19, 20, 20, 20, 20, 20, 19, 19, 19, 19, 19, 19, 21, 21)
    return {(x, y): color for (x, y), color in guard.items()
            if 106 <= y <= 123 and x >= shield_left[y - 106] + offset}


def walk_pose(guard, pose, key, offset):
    sway, bob, tip, shield_x, shield_y, support_x = key
    shift = round(hip_center(guard) - hip_center(pose)) + sway

    # Resample from the moving hip to the fixed sole row. At passing,
    # counter the four-pixel change of pivot so the support stays in place
    # between the compression and passing keys.
    legs = {}
    leg_rows = {y: [] for y in range(122, 144)}
    for (x, y), color in pose.items():
        if y in leg_rows:
            leg_rows[y].append((x + shift, color))
    for y in range(122 + bob, 144):
        weight = (y - 122 - bob) / (21 - bob)
        source_y = 122 + round(weight * 21)
        sole_shift = round(weight * support_x)
        legs.update({(x + sole_shift, y): color for x, color in leg_rows[source_y]})

    # These row marks follow the blade above its grip at Y111. Bend its
    # projection around that grip while the shield follows the support.
    blade_rows = ((23, 24), (22, 24), (21, 23), (21, 23), (20, 22), (19, 22),
                  (19, 21), (18, 20), (17, 19), (16, 19), (15, 18), (16, 18),
                  (14, 16), (14, 16))
    blade = {(x, 98 + n): guard[x, 98 + n]
             for n, (lo, hi) in enumerate(blade_rows)
             for x in range(lo + offset, hi + offset + 1) if (x, 98 + n) in guard}
    shield = shield_raster(guard, offset)
    legs.update({(x + sway, y + bob): color for (x, y), color in guard.items()
                 if y <= 123 and (x, y) not in blade and (x, y) not in shield})
    legs.update({(x + sway + round((111 - y) * tip / 13), y + bob): color
                 for (x, y), color in blade.items()})
    legs.update({(x + sway + shield_x, y + bob + shield_y): color
                 for (x, y), color in shield.items()})
    return legs


def jab_poses(guard, contact):
    # These marks follow the exposed shield border in the guard raster,
    # leaving the sword and its hand on the torso side of the cut.
    shield = shield_raster(guard)
    body = {point: color for point, color in guard.items() if point not in shield}
    arm = {(x - 5, y + 4): color for (x, y), color in contact.items()
           if 24 <= x <= 32 and 106 <= y <= 110}
    for phase, (lean, dx, dy) in enumerate(((-1, -3, 1), (2, 4, -1), (1, 2, 0)), 1):
        # Lean into the shield while keeping the stance and head dimensions.
        result = {(x + (lean if y <= 121 else 0), y): color for (x, y), color in body.items()}
        if phase == 2:
            result.update(arm)
        result.update({(x + dx, y + dy): color for (x, y), color in shield.items()})
        yield f"alis_pe_1_curto_{phase}", result


def strong_pose(guard, pose, key, face):
    # Register the guard's face and hair to the neck of each existing pose.
    # Preserve the authored reach, feet, sword and shield.
    dx, dy, cut, edge = {"prepare": (6, 3, 110, 29),
                         "thrust": (10, 3, 111, 30),
                         "recover": (2, 2, 109, 24)}[key]
    head = {(x, y): color for (x, y), color in guard.items()
            if (y <= 97) or (98 <= y <= 103 and x <= 19) or (104 <= y <= 109 and x <= 14)}
    result = {(x, y): color for (x, y), color in pose.items()
              if y >= cut or x > edge or (key == "thrust" and y >= 107 and x >= 28)}
    result.update({(x + dx, y + dy): color for (x, y), color in head.items()})
    # Remove detached navy residue left by the head cut near the neckline.
    for (x, y), color in tuple(result.items()):
        if color == 0x10 and 100 <= y <= 111 and not any(
            (x + a, y + b) in result for a, b in
            ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1))
        ):
            del result[x, y]
    if face == "left":
        # The left-facing source has a distinct blade ramp. Remove the
        # three-pixel fragments exposed at the two registered neckline cuts.
        fragments = {"prepare": ((25, 105), (25, 106), (24, 106)),
                     "recover": ((21, 104), (21, 105), (20, 105))}
        for point in fragments.get(key, ()):
            if result.pop(point, None) not in (0x10, 0x38):
                raise ValueError(f"Blade fringe changed in {key}/{face} at {point}")
    return result


def arena_margin(frames):
    backwards, forwards = [], []
    for frame in frames:
        # Include the entire width of an emitted sprite, including padding.
        lefts = [x for x, _, _ in frame["sprite_cells"] + frame["background_pixels"]]
        rights = [x + 7 for x, _, _ in frame["sprite_cells"]]
        rights.extend(x for x, _, _ in frame["background_pixels"])
        lo, hi = min(lefts), max(rights)
        if frame["direction"] == "right":
            backwards.append(-lo)
            forwards.append(hi)
        else:
            backwards.append(hi)
            forwards.append(-lo)
    # Fighters face inward and keep a separation of at least 24 px.
    return max(32, max(backwards), max(forwards) - 24)


def revise(source, output):
    plan = json.loads(source.read_bytes())
    sprite, bg = plan["sprite_palette"], plan["background_palette"]
    originals = {(row["pose"], row["direction"]): raster(row, sprite)
                 for row in plan["frames"] if row["actor"] == "alis"}
    changed = []
    for face in ("right", "left"):
        original = {key: pose for (key, direction), pose in originals.items() if direction == face}
        if face == "left":
            original = {key: {(-x - 1, y): color for (x, y), color in pose.items()}
                        for key, pose in original.items()}
        guard = original["idle"]
        updates = {key: walk_pose(guard, pose, WALK_KEYS[key.split("_")[-2]][int(key[-1]) - 1],
                                  -1 if face == "left" else 0) for key, pose in original.items()
                   if key.startswith("alis_walk_")}
        updates.update(jab_poses(guard, original["alis_pe_1_curto_2"]))
        updates.update({key: strong_pose(guard, original[key], key, face)
                        for key in ("prepare", "thrust", "recover")})
        for row in plan["frames"]:
            key = row["pose"]
            if row["actor"] != "alis" or row["direction"] != face or key not in updates:
                continue
            pose = updates[key]
            if face == "left":
                pose = {(-x - 1, y): color for (x, y), color in pose.items()}
            result = make_plan(pose, sprite, bg, max_objects=32)
            if result is None:
                raise ValueError(f"No legal composition for {key}/{face}")
            objects, spill, phases = result
            if key.startswith("alis_walk_") and spill:
                raise ValueError(f"Walk requires a complete sprite layout: {key}/{face}")
            row.update(sprite_count=len(objects),
                       sprite_cells=[[x, y, tile.hex()] for x, y, tile in objects],
                       background_pixels=[[x, y, color] for (x, y), color in sorted(spill.items())],
                       background_cells_by_phase=[sorted(cells) for cells in phases])
            changed.append([key, face])
    margin = arena_margin(plan["frames"])
    if margin >= 63:
        raise ValueError("Revised arena offers no additional retreat distance")
    plan.update(revision_source_sha256=digest(source), revised_alis_poses=changed, arena_margin=margin,
                walk_keys={"fields": ["lean", "hip_y", "tip_x", "shield_x", "shield_y", "support_x"], **WALK_KEYS})
    plan["crossover"] = arena_crossover(plan["frames"], margin)
    plan["max_sat"] = plan["crossover"]["max_sat"]
    output.write_text(json.dumps(plan, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"changed": len(changed), "margin": margin, "crossover": plan["crossover"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    revise(args.source, args.output)
