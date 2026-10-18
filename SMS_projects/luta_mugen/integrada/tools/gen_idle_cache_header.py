#!/usr/bin/env python3
"""Emit the local ROM harness tables from scale_pilot.py's idle cache plan."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _animation_widths(header_path: Path, prefix: str, action: int,
                     frame_count: int) -> list[int]:
    text = header_path.read_text(encoding="utf-8")
    frame_name = f"{prefix}_frames_all"
    frame_block = re.search(
        rf"static const Frame {frame_name}\[.*?\] = \{{(.*?)\n\}};",
        text, re.S)
    anim_block = re.search(
        rf"static const Anim {prefix}_anims\[.*?\] = \{{(.*?)\n\}};",
        text, re.S)
    if not frame_block or not anim_block:
        raise ValueError(f"nao achei Frame/Anim para {prefix} em {header_path}")

    widths: list[int] = []
    for line in frame_block.group(1).splitlines():
        if not line.lstrip().startswith("{"):
            continue
        match = re.match(
            r"\s*\{\s*\d+\s*,\s*\d+\s*,.*?,\s*(\d+)\s*,\s*(\d+)\s*,",
            line)
        if not match:
            raise ValueError(f"linha Frame nao reconhecida: {line[:100]}")
        widths.append(int(match.group(1)))

    offset = None
    count = None
    for line in anim_block.group(1).splitlines():
        match = re.match(
            rf"\s*\{{\s*(\d+)\s*,\s*(\d+)\s*,\s*\d+\s*,\s*"
            rf"{frame_name}\s*\+\s*(\d+)\s*\}},", line)
        if match and int(match.group(1)) == action:
            count, offset = int(match.group(2)), int(match.group(3))
            break
    if offset is None or count != frame_count:
        raise ValueError(f"action {action} de {prefix}: count/offset inconsistente")
    result = widths[offset:offset + frame_count]
    if len(result) != frame_count:
        raise ValueError(f"dimensoes incompletas para {prefix} action {action}")
    return result


def _signed8(value: int) -> int:
    return value if value < 128 else value - 256


def _pose_sprites(meta: list[int], axis: list[int], width: int,
                  center_x: int, owner: int, facing_left: bool) -> list[tuple[int, ...]]:
    padded_width = (width + 7) & 0xFFF8
    origin_x = (center_x - (axis[0] + padded_width)
                if facing_left else center_x + axis[0])
    origin_y = 160 + axis[1]
    sprites = []
    for offset in range(0, len(meta) - 2, 3):
        if meta[offset] == 0x80:
            break
        x = origin_x + _signed8(meta[offset])
        y = origin_y + _signed8(meta[offset + 1])
        tile = meta[offset + 2]
        if 0 <= x < 256 and 0 <= y < 192:
            priority = abs(x + 4 - center_x) * 64 + abs(y + 8 - 120) * 4 + owner
            sprites.append((x, y, priority, tile, owner))
    ordered = sorted(sprites, key=lambda sprite: sprite[2])
    # Source id = owner * 64 + position in the actor's priority-sorted
    # cache, so the ROM can draw from per-actor caches without merging.
    return [sprite + (owner * 64 + i,) for i, sprite in enumerate(ordered)]


def _merge_sorted(ken: list[tuple[int, ...]],
                  ryu: list[tuple[int, ...]]) -> list[tuple[int, ...]]:
    out = []
    ki = ri = 0
    while ki < len(ken) or ri < len(ryu):
        if ri >= len(ryu) or (ki < len(ken) and ken[ki][2] <= ryu[ri][2]):
            out.append(ken[ki])
            ki += 1
        else:
            out.append(ryu[ri])
            ri += 1
    return out


def _schedule_variants(sprites: list[tuple[int, ...]], max_line: int,
                       variants: int) -> tuple[list[int], list[list[int]]]:
    starts, masks = [], []
    for variant in range(variants):
        start = variant * len(sprites) // variants
        starts.append(start)
        lines = [0] * 192
        selected = [0] * len(sprites)
        index = start
        for _ in sprites:
            x, y = sprites[index][0], sprites[index][1]
            if all(lines[line] < max_line for line in range(y, min(y + 16, 192))):
                selected[index] = 1
                for line in range(y, min(y + 16, 192)):
                    lines[line] += 1
            index += 1
            if index >= len(sprites):
                index = 0
        mask = [0] * 8
        for index, keep in enumerate(selected):
            if keep:
                mask[index >> 3] |= 1 << (index & 7)
        if max(lines, default=0) > max_line:
            raise ValueError("schedule excedeu o limite de sprites por linha")
        masks.append(mask)
    return starts, masks


def _schedule_tables(plans: dict, header_path: Path) -> tuple[list[list[int]], list[list[list[int]]], list[list[list[list[int]]]], int]:
    actors = {}
    for key, prefix, center, owner, facing_left in (
        ("ken_p1", "ken", 96, 0, False),
        ("ryu_p2", "ryu", 160, 1, True),
    ):
        plan = plans[key]
        count = plan["frame_count"]
        widths = _animation_widths(header_path, prefix, plan["action"], count)
        initial = plan["initial_pose"]
        metadata = [initial["metadata"]]
        axes = [initial["axis_signed_xy"]]
        next_meta = {row["to_frame"]: row["next_metadata"]
                     for row in plan["transitions"] if row["to_frame"] != 0}
        next_axis = {row["to_frame"]: row["next_axis_signed_xy"]
                     for row in plan["transitions"] if row["to_frame"] != 0}
        for frame in range(1, count):
            metadata.append(next_meta[frame])
            axes.append(next_axis[frame])
        actors[key] = [
            _pose_sprites(metadata[i], axes[i], widths[i], center, owner, facing_left)
            for i in range(count)
        ]

    ken_count = len(actors["ken_p1"])
    ryu_count = len(actors["ryu_p2"])
    variants = 8
    all_counts, all_draw_counts, all_draw_indices = [], [], []
    while variants <= 64:
        all_counts, all_draw_counts, all_draw_indices = [], [], []
        uncovered = False
        for ken in actors["ken_p1"]:
            row_counts, row_draw_counts, row_draw_indices = [], [], []
            for ryu in actors["ryu_p2"]:
                sprites = _merge_sorted(ken, ryu)
                if len(sprites) > 64:
                    raise ValueError("schedule excede 64 entradas SAT")
                starts, masks = _schedule_variants(sprites, 8, variants)
                draw_indices = []
                for start, mask in zip(starts, masks):
                    order = []
                    index = start
                    for _ in sprites:
                        if mask[index >> 3] & (1 << (index & 7)):
                            order.append(sprites[index][5])
                        index += 1
                        if index >= len(sprites):
                            index = 0
                    draw_indices.append(order)
                covered = [0] * len(sprites)
                for mask in masks:
                    for i in range(len(sprites)):
                        if mask[i >> 3] & (1 << (i & 7)):
                            covered[i] = 1
                if not all(covered):
                    uncovered = True
                row_counts.append(len(sprites))
                row_draw_counts.append([len(order) for order in draw_indices])
                row_draw_indices.append(draw_indices)
            all_counts.append(row_counts)
            all_draw_counts.append(row_draw_counts)
            all_draw_indices.append(row_draw_indices)
        if not uncovered:
            return all_counts, all_draw_counts, all_draw_indices, variants
        variants *= 2
    raise ValueError("ate 64 variantes, flicker nao cobre todos os sprites")


def emit(report_path: Path, output_path: Path, source_header_path: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    plans = report["selected_facing_pool"]["idle_cache_plan"]
    lines = [
        "/* Generated from scale_pilot_dedup_emulator_audit.json. */",
        "#ifndef PILOT_IDLE_CACHE_PLAN_H",
        "#define PILOT_IDLE_CACHE_PLAN_H",
        "typedef struct { unsigned char bank; unsigned int off;",
        "                 unsigned char slot; } PilotPairLoad;",
        "typedef struct { const unsigned char *meta; unsigned char meta_size;",
        "                 unsigned char air_ticks; signed int axis_x, axis_y;",
        "                 const PilotPairLoad *uploads; unsigned char upload_count;",
        "                 unsigned int upload_bytes; } PilotIdleFramePlan;",
    ]

    def c_array(name: str, values: list[int]) -> None:
        lines.append(f"static const unsigned char {name}[{len(values)}] = {{")
        for start in range(0, len(values), 12):
            lines.append("    " + ", ".join(f"0x{x:02x}" for x in values[start:start + 12]) + ",")
        lines.append("};")

    def load_array(name: str, loads: list[dict]) -> None:
        if not loads:
            lines.append(f"static const PilotPairLoad {name}[1] = {{{{0, 0, 0}}}};")
            return
        lines.append(f"static const PilotPairLoad {name}[{len(loads)}] = {{")
        # Group source reads by mapper bank so the frame streamer can map each
        # bank once per VBlank instead of once per 64-byte pair.
        for load in sorted(loads, key=lambda row: (row["source_bank"], row["source_off"])):
            lines.append("    {%d, %d, %d}," % (
                load["source_bank"], load["source_off"], load["target_pair_slot"]))
        lines.append("};")

    for key, prefix in (("ken_p1", "ken"), ("ryu_p2", "ryu")):
        plan = plans[key]
        frames = plan["transitions"]
        initial = plan["initial_pose"]
        lines.extend((
            f"#define {prefix.upper()}_IDLE_ACTION {plan['action']}u",
            f"#define {prefix.upper()}_IDLE_LOOP_START {plan['loop_start']}u",
            f"#define {prefix.upper()}_IDLE_FRAME_COUNT {plan['frame_count']}u",
        ))
        load_array(f"{prefix}_idle_initial_loads", initial["pattern_loads"])
        pose_metadata = [initial["metadata"]] + [
            next(row["next_metadata"] for row in frames if row["to_frame"] == i)
            for i in range(1, plan["frame_count"])]
        for i, metadata in enumerate(pose_metadata):
            c_array(f"{prefix}_idle_meta_{i}", metadata)
        for row in frames:
            load_array(f"{prefix}_idle_uploads_{row['from_frame']}", row["uploads"])
        lines.append(f"static const PilotIdleFramePlan {prefix}_idle_frames[{plan['frame_count']}] = {{")
        for row in frames:
            i = row["from_frame"]
            active_metadata = pose_metadata[i]
            # AIR and axis belong to the active frame, not its successor.
            active = initial if i == 0 else next(
                x for x in frames if x["to_frame"] == i)
            air = initial["air_ticks"] if i == 0 else active["next_air_ticks"]
            axis = initial["axis_signed_xy"] if i == 0 else active["next_axis_signed_xy"]
            loads = row["uploads"]
            lines.append("    {%s, %d, %d, %d, %d, %s, %d, %d}," % (
                f"{prefix}_idle_meta_{i}", len(active_metadata), air,
                axis[0], axis[1], f"{prefix}_idle_uploads_{i}", len(loads),
                row["upload_bytes"]))
        lines.append("};")
    counts, draw_counts, draw_indices, variants = _schedule_tables(plans, source_header_path)
    lines.append(f"#define PILOT_SCHEDULE_VARIANTS {variants}u")
    draw_capacity = max(value for ken_row in draw_counts
                        for ryu_row in ken_row for value in ryu_row)
    lines.append(f"#define PILOT_DRAW_LIST_CAPACITY {draw_capacity}u")
    lines.append("static const unsigned char idle_sprite_schedule_counts[KEN_IDLE_FRAME_COUNT][RYU_IDLE_FRAME_COUNT] = {")
    for row in counts:
        lines.append("    {" + ", ".join(str(value) for value in row) + "},")
    lines.append("};")
    lines.append("static const unsigned char idle_sprite_schedule_draw_counts[KEN_IDLE_FRAME_COUNT][RYU_IDLE_FRAME_COUNT][PILOT_SCHEDULE_VARIANTS] = {")
    for ken_row in draw_counts:
        lines.append("    {")
        for row in ken_row:
            lines.append("        {" + ", ".join(str(value) for value in row) + "},")
        lines.append("    },")
    lines.append("};")
    lines.append("static const unsigned char idle_sprite_schedule_indices[KEN_IDLE_FRAME_COUNT][RYU_IDLE_FRAME_COUNT][PILOT_SCHEDULE_VARIANTS][PILOT_DRAW_LIST_CAPACITY] = {")
    for ken_row in draw_indices:
        lines.append("    {")
        for ryu_row in ken_row:
            lines.append("        {")
            for order in ryu_row:
                lines.append("            {" + ", ".join(str(index) for index in order) + "},")
            lines.append("        },")
        lines.append("    },")
    lines.append("};")
    lines.extend(("#endif", ""))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source-header", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    emit(args.report, args.out, args.source_header)
    print(f"[EMITTED] {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
