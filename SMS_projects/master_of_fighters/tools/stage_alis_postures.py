"""Convert the Scene 02 posture study based on the approved Alis reference."""

import argparse
import json
from pathlib import Path

from PIL import Image

from make_duel_scene02_assets import digest
from plan_scene02_repertoire import arena_crossover, make_plan
from revise_scene02_alis import arena_margin


# Row-major source grid with hip offsets from the ground reference.
# The aerial brace folds the boots up while the chest stays near the apex.
POSES = (
    ("alis_crouch_transition", 0, 0), ("alis_crouch", 0, 0), ("alis_crouch_guard", 0, 0),
    ("alis_stand_guard", 0, 0), ("alis_jump_rise", 0, 0), ("alis_jump_apex", 0, 0),
    ("alis_jump_fall", 0, 0), ("alis_jump_diagonal", -5, -5), ("alis_jump_guard", 0, -13),
)


def connected_pixels(raster):
    remaining = set(raster)
    bodies = []
    while remaining:
        start = remaining.pop()
        body = {start}
        frontier = [start]
        while frontier:
            x, y = frontier.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    pixel = (x + dx, y + dy)
                    if pixel in remaining:
                        frontier.append(pixel)
                        body.add(pixel)
                        remaining.remove(pixel)
        bodies.append(body)
    body = max(bodies, key=len)
    if len(raster) - len(body) > 12:
        raise ValueError("Disconnected artwork exceeds the antialias cleanup budget")
    return {xy: raster[xy] for xy in body}


def rgb(code):
    return tuple(((code >> shift) & 3) * 85 for shift in (0, 2, 4))


def convert(image, palette, x_adjust, y_adjust, divisor=6.0):
    bounds = image.getchannel("A").point(lambda alpha: 255 if alpha >= 160 else 0).getbbox()
    image = image.crop(bounds)
    # Apply the same scale to feet, body, head and equipment in every cell.
    width, height = round(image.width / divisor), round(image.height / divisor)
    image = image.resize((width, height), Image.Resampling.NEAREST)
    colors = [(code, rgb(code)) for code in palette[1:]]
    x_origin = 12 - width // 2 + x_adjust
    raster = {}
    for y in range(height):
        for x in range(width):
            r, g, b, alpha = image.getpixel((x, y))
            if alpha < 160:
                continue
            color, _ = min(colors, key=lambda entry: sum(
                (a - c) ** 2 for a, c in zip((r, g, b), entry[1])))
            raster[x + x_origin, 144 - height + y + y_adjust] = color
    return connected_pixels(raster)


def stage(source, control, destination):
    plan = json.loads(control.read_bytes())
    palette = plan["sprite_palette"]
    destination.mkdir(parents=True, exist_ok=False)
    entries = []
    with Image.open(source) as base:
        image = base.convert("RGBA")
        sheet = Image.new("RGBA", (3 * 64, 3 * 64))
        for index, (name, x_adjust, y_adjust) in enumerate(POSES):
            row, col = divmod(index, 3)
            cell = image.crop((col * image.width // 3, row * image.height // 3,
                               (col + 1) * image.width // 3, (row + 1) * image.height // 3))
            drawing = convert(cell, palette, x_adjust, y_adjust)
            for (x, y), code in drawing.items():
                sheet.putpixel((64 * col + 12 + x, 64 * row + y - 83), (*rgb(code), 255))
            for face in ("left", "right"):
                art = drawing if face == "right" else {(-x - 1, y): c for (x, y), c in drawing.items()}
                placement = make_plan(art, palette, (), max_objects=32)
                if placement is None:
                    raise ValueError(f"{name}/{face} exceeds four sprite cells per line")
                objects, spill, phases = placement
                if spill:
                    raise ValueError(f"{name}/{face} has background pixels")
                plan["frames"].append(dict(actor="alis", direction=face, pose=name,
                                           sprite_count=len(objects),
                                           sprite_cells=[[x, y, data.hex()] for x, y, data in objects],
                                           background_pixels=[],
                                           background_cells_by_phase=[sorted(cells) for cells in phases]))
                entries.append(dict(pose=name, face=face, sprites=len(objects),
                                    top=min(y for _, y in art), sole=max(y for _, y in art)))
    margin = arena_margin(plan["frames"])
    plan["arena_margin"] = margin
    plan["crossover"] = arena_crossover(plan["frames"], margin)
    plan["max_sat"] = plan["crossover"]["max_sat"]
    plan["added_poses"] += [["alis", name] for name, _, _ in POSES]
    plan["boot_sprite_priority"] = [
        ["hayato", "idle"], ["alis", "idle"], ["hayato", "hayato_pe_1_curto_1"],
        ["alis", "alis_stand_guard"], ["alis", "alis_crouch_transition"],
        ["alis", "alis_jump_rise"], ["alis", "alis_crouch_guard"],
        ["alis", "alis_jump_guard"], ["alis", "alis_crouch"],
        ["alis", "alis_jump_apex"], ["alis", "alis_jump_fall"],
        ["alis", "alis_jump_diagonal"],
    ]
    plan["postures_source_sha256"] = digest(source)
    sheet.save(destination / "postures-1x.png")
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.Resampling.NEAREST).save(
        destination / "postures-3x.png")
    (destination / "postures-plan.json").write_text(json.dumps(plan, separators=(",", ":")) + "\n")
    (destination / "art-receipt.json").write_text(json.dumps({
        "source_sha256": digest(source), "control_plan_sha256": digest(control),
        "fixed_scale_divisor": 6.0, "frames": entries, "arena_margin": margin,
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("control", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    stage(args.source, args.control, args.destination)
