"""Calibrate original standing strips and measure a provisional 8x8 packing."""
import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import re
from PIL import Image


PROJECT = Path(__file__).resolve().parents[1]
STANDING = PROJECT / "data/source_art/sprite_studies/scene02_standing_20261119"
DIAGNOSTICS = PROJECT / "out/diagnostics"
SCENE = DIAGNOSTICS / "duel_execution_20261119"
CANVAS = (144, 104)
FLOOR = 96


def read_rgba(path):
    with Image.open(path) as source:
        if source.format != "PNG":
            raise ValueError(f"Expected PNG: {path}")
        return source.width, source.height, source.convert("RGBA").tobytes()


def coordinates(width, height, rgba, first, last):
    alpha = rgba[3::4]
    return [(x, y) for y in range(height) for x in range(first, last)
            if alpha[y * width + x] >= 160]


def bounds(points):
    return (min(x for x, _ in points), min(y for _, y in points),
            max(x for x, _ in points) + 1, max(y for _, y in points) + 1)


def old_guard_height(fighter):
    path = (
        DIAGNOSTICS / "hayato_short_cut_v2/timing_only_v7/converted_left/idle.png"
        if fighter == "hayato" else
        DIAGNOSTICS / "alis_strong_thrust_round1/sequence_grounded96_right_probe/idle.png"
    )
    w, h, rgba = read_rgba(path)
    _, top, _, bottom = bounds(coordinates(w, h, rgba, 0, w))
    return bottom - top


def palette(symbol):
    header = (SCENE / "generated/duel_scene02_assets.h").read_text("ascii")
    match = re.search(rf"{symbol}\[16\]\s*=\s*\{{([^}}]+)", header)
    if not match:
        raise ValueError(f"The pilot palette {symbol} is missing")
    codes = [int(value, 16) for value in re.findall(r"0x[0-9a-f]+", match[1])]
    if len(codes) != 16 or any(c > 63 for c in codes):
        raise ValueError("The pilot P1 palette must have 16 native color codes")
    return [(85 * (c & 3), 85 * ((c >> 2) & 3), 85 * ((c >> 4) & 3)) for c in codes]


def indexed_png(path, image, rgb):
    indexed = Image.frombytes("P", CANVAS, bytes(image))
    indexed.putpalette([value for color in rgb for value in color])
    indexed.save(path, transparency=0, bits=4)


def pack(points):
    best = None
    for phase in range(8):
        rows = {}
        for x, y in points:
            rows.setdefault(y - (y - phase) % 8, set()).add(x)
        objects = []
        for top, columns in sorted(rows.items()):
            end = -1
            for x in sorted(columns):
                if x >= end:
                    objects.append([x, top])
                    end = x + 8
        count = Counter(y for _, top in objects for y in range(top, top + 8))
        score = (max(count.values()), len(objects))
        if best is None or score < best[0]:
            best = score, count, objects
    return best


def background_offload(cases, bg, sprite):
    # Optimistic bound: move every color-compatible complete sprite to P0.
    # This does not charge tile alignment, raster occlusion, or VRAM traffic.
    extra = sorted(set(sprite[1:]) - bg)
    groups = ([row for row in cases if row["actor"] == actor] for actor in ("hayato", "alis"))
    hayato, alis = groups
    best = None
    for added in combinations(extra, min(len(extra), 16 - len(bg))):
        allowed = bg.union(added)
        remaining = {}
        for row in cases:
            occupied = Counter()
            for top, colors in row["object_colors"]:
                if not colors <= allowed:
                    occupied.update(range(top, top + 8))
            remaining[row["file"]] = occupied
        peaks = [max((remaining[h["file"]] + remaining[a["file"]]).values(), default=0)
                 for h in hayato for a in alis]
        score = (max(peaks), sum(peak > 8 for peak in peaks))
        if best is None or score < best[0]:
            best = score, added
    (peak, crossings), additions = best
    allowed = bg.union(additions)
    minimum_moves = []
    max_bg_tiles = 0
    for h in hayato:
        for a in alis:
            objects = h["object_colors"] + a["object_colors"]
            active = Counter(top + dy for top, _ in objects for dy in range(8))
            candidates = {}
            for row, pivot, facing in ((h, 111, 1), (a, 144, -1)):
                for (top, colors), pixels in zip(row["object_colors"], row["object_pixels"], strict=True):
                    if colors <= allowed:
                        candidates.setdefault(top, []).append((pivot, facing, pixels))
            removed = Counter()
            moved = []
            for line in sorted(active):
                for _ in range(max(0, active[line] - removed[line] - 8)):
                    top = next((t for t in range(line, line - 8, -1) if candidates.get(t)), None)
                    if top is None:
                        moved = None
                        break
                    moved.append(candidates[top].pop())
                    removed.update(range(top, top + 8))
                if moved is None:
                    break
            if moved is not None:
                minimum_moves.append(len(moved))
                for phase in range(8):
                    tiles = {((pivot + phase + facing * (x - 64)) // 8, (y + 144 - FLOOR) // 8)
                             for pivot, facing, pixels in moved for x, y in pixels}
                    max_bg_tiles = max(max_bg_tiles, len(tiles))
    return {"remaining_peak": peak, "crossings_over_eight": crossings, "added_rgb": additions,
            "max_minimum_objects_to_move": max(minimum_moves, default=None),
            "max_bg_grid_tiles_for_selected_objects": max_bg_tiles,
            "grid_basis": "33px separation on the pilot floor and eight shared horizontal phases. "
            "Greedy minimum-object selection, without optimizing tile sharing or overlap.",
            "assumptions": "Every complete 8x8 sprite compatible with P0 moves to BG. "
            "Excludes overlap, layout, tile reload and upload budget."}


def stage(dest):
    receipt = json.loads((STANDING / "generated-art-receipt.json").read_bytes())
    colors = palette("mof_duel_sprite_palette")
    heights = {f: old_guard_height(f) for f in ("hayato", "alis")}
    cases = []
    dest.mkdir(parents=True, exist_ok=False)
    for item in receipt["records"]:
        name = item["key"]
        source = STANDING / item["file"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"Source SHA differs: {source}")
        w, h, raw = read_rgba(source)
        if w % 3:
            raise ValueError(f"Need three equal cells: {source}")
        cells = [coordinates(w, h, raw, i * w // 3, (i + 1) * w // 3) for i in range(3)]
        boxes = [bounds(cell) for cell in cells]
        ruler = max(bottom - top for _, top, _, bottom in boxes)
        actor = name.split("_")[0]
        scale = heights[actor] / ruler
        for i, ((left, top, right, bottom), cell) in enumerate(zip(boxes, cells, strict=True)):
            first, end = i * w // 3, (i + 1) * w // 3
            if left == first or right == end:
                raise ValueError(f"Sprite crosses the cell boundary: {source} #{i}")
            feet = sorted(x for x, y in cell if y >= bottom - max(2, (bottom - top) // 36))
            support = feet[len(feet) // 5]
            shape = bytearray(CANVAS[0] * CANVAS[1])
            occupied = []
            for y in range(CANVAS[1]):
                sy = bottom - 1 + int(round((y - FLOOR + 1) / scale))
                if not top <= sy < bottom:
                    continue
                for x in range(CANVAS[0]):
                    sx = support + int(round((x - 64) / scale))
                    if not left <= sx < right:
                        continue
                    red, green, blue, alpha = raw[(sy * w + sx) * 4:(sy * w + sx) * 4 + 4]
                    if alpha < 160:
                        continue
                    index = min(range(1, len(colors)), key=lambda k: (
                        (colors[k][0] - red)**2 + (colors[k][1] - green)**2 + (colors[k][2] - blue)**2
                    ))
                    shape[y * CANVAS[0] + x] = index
                    occupied.append((x, y))
            if not occupied or any(x in (0, CANVAS[0] - 1) or y == 0 for x, y in occupied):
                raise ValueError(f"Scaled pose clips or is empty: {source} #{i}")
            output = dest / f"{name}_{i + 1}.png"
            indexed_png(output, shape, colors)
            score, count, objects = pack(occupied)
            object_pixels = [[(x, y)
                              for y in range(top, min(top + 8, CANVAS[1]))
                              for x in range(left, min(left + 8, CANVAS[0]))
                              if shape[y * CANVAS[0] + x]] for left, top in objects]
            object_colors = [(top, {colors[shape[y * CANVAS[0] + x]] for x, y in pixels})
                             for (_, top), pixels in zip(objects, object_pixels, strict=True)]
            cases.append({"actor": actor, "action": name, "frame": i + 1,
                          "file": output.name, "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                          "source_bbox": list(boxes[i]), "native_bbox": list(bounds(occupied)), "support_source_x": support,
                          "pilot_guard_height": heights[actor], "solo_peak": score[0], "sat": score[1],
                          "objects": objects, "profile": count, "object_colors": object_colors,
                          "object_pixels": object_pixels})
    pair_rows = []
    for h in (x for x in cases if x["actor"] == "hayato"):
        for a in (x for x in cases if x["actor"] == "alis"):
            peak = max(h["profile"][y] + a["profile"][y] for y in range(CANVAS[1] + 8))
            pair_rows.append({"hayato": h["file"], "alis": a["file"], "peak": peak, "sat": h["sat"] + a["sat"]})
    report = {
        "status": "draft calibration and unauthorised-for-ROM packing trial",
        "frames": [{k: v for k, v in row.items() if k not in ("profile", "object_colors", "object_pixels")}
                   for row in cases],
        "crossings": pair_rows,
        "peak_sprites_per_line": max(x["peak"] for x in pair_rows),
        "crossings_over_eight": sum(x["peak"] > 8 for x in pair_rows),
        "best_case_background_offload": background_offload(
            cases, set(palette("mof_duel_bg_palette")), colors),
        "limits": "Solo phase choices combined at the same floor. No joint SAT/P0 solution, streaming deadline, hitbox acceptance, or ROM proof.",
    }
    (dest / "staging-report.json").write_text(json.dumps(report, indent=2) + "\n", "utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("frames", "crossings")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    stage(parser.parse_args().destination)
