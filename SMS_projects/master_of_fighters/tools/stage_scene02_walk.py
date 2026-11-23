"""Convert authored walk strips to the Scene 02 floor, pivot and palette."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from stage_standing_drafts import CANVAS, FLOOR, indexed_png, old_guard_height, palette

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / "data/source_art/sprite_studies/scene02_walk_20261119"
SPECIALS = PROJECT / "data/source_art/sprite_studies/scene02_specials_20261119"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def convert_pose(cell, box, pivot, scale, colors, output, scale_x=None):
    left, top, right, bottom = box
    scale_x = scale if scale_x is None else scale_x
    pixels = cell.load()
    indices = bytearray(CANVAS[0] * CANVAS[1])
    for y in range(FLOOR):
        sy = bottom - 1 + round((y - FLOOR + 1) / scale)
        if not top <= sy < bottom:
            continue
        for x in range(CANVAS[0]):
            sx = pivot + round((x - 64) / scale_x)
            if not left <= sx < right:
                continue
            r, g, b, a = pixels[sx, sy]
            if a >= 160:
                indices[y * CANVAS[0] + x] = min(range(1, 16), key=lambda i: sum(
                    (target - actual) ** 2 for target, actual in zip(colors[i], (r, g, b))))
    stride = CANVAS[0]
    floor_adjustment = 0
    if not any(indices[(FLOOR - 1) * stride:FLOOR * stride]):
        # Horizontal reduction can miss the last toe pixel. Re-anchor the
        # sampled support instead of repainting the silhouette or lowering it in the ROM.
        if scale_x < scale:
            for offset in (1, 2):
                row = FLOOR - 1 - offset
                if any(indices[row * stride:(row + 1) * stride]):
                    floor_adjustment = offset
                    break
        if not floor_adjustment:
            raise ValueError(f"Contact with floor lost in {output.name}")
        shift = floor_adjustment * stride
        indices[:] = bytes(shift) + indices[:-shift]
    if scale_x * max(pivot - left, right - pivot) >= 63:
        raise ValueError(f"Pose can cross the native crop in {output.name}")
    indexed_png(output, indices, colors)
    return floor_adjustment


def stage(destination, hayato_sprite_only=False):
    receipt = json.loads((SOURCE / "source-receipt.json").read_bytes())
    colors = palette("mof_duel_sprite_palette")
    destination.mkdir(parents=True, exist_ok=False)
    poses = []
    for item in receipt["sheets"]:
        actor = item["actor"]
        sheet = SOURCE / item["file"]
        reference = PROJECT / item["reference"]
        if digest(sheet) != item["sha256"] or digest(reference) != item["reference_sha256"]:
            raise ValueError(f"Changed source for {actor}")
        with Image.open(sheet) as opened:
            source = opened.convert("RGBA")
        width, height = source.size
        if width % 4 or height % 2:
            raise ValueError(f"Invalid four-column, two-row strip: {sheet}")
        cells = []
        for row, direction in enumerate(("forward", "back")):
            edges = item.get("column_edges", {}).get(direction, [i * width // 4 for i in range(5)])
            if edges[0] != 0 or edges[-1] != width or len(edges) != 5 or edges != sorted(set(edges)):
                raise ValueError(f"Invalid cell boundaries for {actor}: {direction}")
            for col in range(4):
                cell = source.crop((edges[col], row * height // 2,
                                    edges[col + 1], (row + 1) * height // 2))
                mask = cell.getchannel("A").point(lambda a: 255 if a >= 160 else 0)
                box = mask.getbbox()
                if not box or box[0] == 0 or box[1] == 0 or box[2] == cell.width or box[3] == cell.height:
                    raise ValueError(f"Empty or clipped cell for {actor}: {direction} {col + 1}")
                cells.append((direction, col, cell, box, edges[col]))
        scale = old_guard_height(actor) / max(box[3] - box[1] for _, _, _, box, _ in cells)
        scale_x = scale
        if actor == "hayato" and hayato_sprite_only:
            # Reserve a complete four-sprite strip without shifting a moving P0 mask.
            scale_x = min(scale, 31 / max(box[2] - box[0] for _, _, _, box, _ in cells))
        for direction, col, cell, box, cell_x in cells:
            left, top, right, bottom = box
            pivot = item["hip_x"][0 if direction == "forward" else 1][col] + col * width // 4 - cell_x
            if not left < pivot < right:
                raise ValueError(f"Invalid annotated hip for {actor}: {direction} {col + 1}")
            filename = f"{actor}_walk_{direction}_{col + 1}.png"
            output = destination / filename
            floor_adjustment = convert_pose(cell, box, pivot, scale, colors, output, scale_x)
            poses.append({"actor": actor, "file": filename, "sha256": digest(output),
                          "action": f"{actor}_walk_{direction}",
                          "source_sha256": item["sha256"], "direction": direction,
                          "frame": col + 1, "hip_x_source": pivot, "bounds_source": box,
                          "pivot": [64, FLOOR], "scale": scale, "scale_x": scale_x,
                          "floor_adjustment_px": floor_adjustment})
    (destination / "walk-staging.json").write_text(json.dumps(poses, indent=2) + "\n", encoding="utf-8")


def stage_specials(destination):
    receipt = json.loads((SPECIALS / "source-receipt.json").read_bytes())
    colors = palette("mof_duel_sprite_palette")
    destination.mkdir(parents=True, exist_ok=False)
    poses = []
    for item in receipt["sheets"]:
        actor = item["actor"]
        sheet = SPECIALS / item["file"]
        if digest(sheet) != item["sha256"] or digest(PROJECT / item["reference"]) != item["reference_sha256"]:
            raise ValueError(f"Changed source for {actor}")
        with Image.open(sheet) as opened:
            source = opened.convert("RGBA")
        alpha = source.getchannel("A").point(lambda a: 255 if a >= 160 else 0)
        cells = []
        for seed in item["hip_points"]:
            point = tuple(seed)
            if alpha.getpixel(point) != 255:
                raise ValueError(f"Special pose lacks the annotated pivot: {actor} {seed}")
            component = alpha.copy()
            ImageDraw.floodfill(component, point, 128)
            mask = component.point(lambda a: 255 if a == 128 else 0)
            box = mask.getbbox()
            if any(mask.getpixel(tuple(other)) for other in item["hip_points"] if other != seed):
                raise ValueError(f"The source joins multiple poses: {actor}")
            cell = source.copy()
            cell.putalpha(mask)
            cells.append((cell, box, point[0]))
        scale = old_guard_height(actor) / max(box[3] - box[1] for _, box, _ in cells)
        for index, (cell, box, pivot) in enumerate(cells, 1):
            action = f"{actor}_special"
            output = destination / f"{action}_{index}.png"
            convert_pose(cell, box, pivot, scale, colors, output)
            poses.append({"actor": actor, "action": action, "frame": index, "file": output.name,
                          "sha256": digest(output), "source_sha256": item["sha256"],
                          "hip_x_source": pivot, "bounds_source": box, "pivot": [64, FLOOR], "scale": scale})
    (destination / "special-staging.json").write_text(json.dumps(poses, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("destination", type=Path)
    cli.add_argument("--specials", action="store_true")
    cli.add_argument("--hayato-sprite-only", action="store_true")
    args = cli.parse_args()
    if args.specials:
        if args.hayato_sprite_only:
            cli.error("--hayato-sprite-only applies to walk strips")
        stage_specials(args.destination)
    else:
        stage(args.destination, args.hayato_sprite_only)
