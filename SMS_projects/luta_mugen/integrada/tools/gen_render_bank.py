#!/usr/bin/env python3
"""Emit the per-actor metasprite draw lists into a dedicated ROM bank.

Per (Ken frame, Ryu frame, flicker variant) the schedule already selects which
pieces are drawn (gen_idle_cache_header.py). This tool splits each selection
into one SMSlib metasprite per fighter -- (dx, dy, tile) relative to a fixed
per-fighter anchor, 0x80 terminated -- so the ROM draws each fighter with one
SMS_addMetaSprite call instead of one SMS_addSprite call per piece.
Identical sublists are stored once. Bank layout: offset table first
(KEN_FRAMES*RYU_FRAMES*VARIANTS pairs of little-endian u16 slot-2 offsets,
Ken then Ryu), then the lists.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gen_idle_cache_header as gen  # noqa: E402

BANK_BYTES = 16384
META_END = 0x80
# Anchors = runtime centers (96, 160) and a mid-body y; dx/dy must fit s8.
ANCHORS = {"ken_p1": (96, 120), "ryu_p2": (160, 120)}


def _actors(plans: dict, header_path: Path) -> dict:
    actors = {}
    for key, prefix, center, owner, facing_left in (
        ("ken_p1", "ken", 96, 0, False),
        ("ryu_p2", "ryu", 160, 1, True),
    ):
        plan = plans[key]
        count = plan["frame_count"]
        widths = gen._animation_widths(header_path, prefix, plan["action"], count)
        initial = plan["initial_pose"]
        metadata = [initial["metadata"]]
        axes = [initial["axis_signed_xy"]]
        next_meta = {r["to_frame"]: r["next_metadata"] for r in plan["transitions"] if r["to_frame"]}
        next_axis = {r["to_frame"]: r["next_axis_signed_xy"] for r in plan["transitions"] if r["to_frame"]}
        for frame in range(1, count):
            metadata.append(next_meta[frame])
            axes.append(next_axis[frame])
        actors[key] = [gen._pose_sprites(metadata[i], axes[i], widths[i], center, owner, facing_left)
                       for i in range(count)]
    return actors


def _sublist(sprites: list, ids: list[int], anchor: tuple[int, int]) -> bytes:
    out = bytearray()
    for i in ids:
        x, y, _prio, tile, _owner, _sid = sprites[i]
        dx, dy = x - anchor[0], y - anchor[1]
        if not (-127 <= dx <= 127 and -128 <= dy <= 127):
            raise ValueError(f"dx/dy fora de s8: {dx},{dy}")
        out += bytes([dx & 0xFF, dy & 0xFF, tile])
    return bytes(out + bytes([META_END]))


def build(plans: dict, header_path: Path) -> tuple[bytes, int]:
    actors = _actors(plans, header_path)
    _counts, _draw_counts, draw_indices, variants = gen._schedule_tables(plans, header_path)
    table: list[tuple[bytes, bytes]] = []
    for kf, ken_row in enumerate(draw_indices):
        for rf, ryu_row in enumerate(ken_row):
            for order in ryu_row:
                ken_ids = [s for s in order if s < 64]
                ryu_ids = [s - 64 for s in order if s >= 64]
                table.append((_sublist(actors["ken_p1"][kf], ken_ids, ANCHORS["ken_p1"]),
                              _sublist(actors["ryu_p2"][rf], ryu_ids, ANCHORS["ryu_p2"])))
    blob = bytearray(len(table) * 4)
    where: dict[bytes, int] = {}
    for n, pair in enumerate(table):
        for half, data in enumerate(pair):
            if data not in where:
                where[data] = 0x8000 + len(blob)
                blob += data
            off = where[data]
            blob[n * 4 + half * 2:n * 4 + half * 2 + 2] = bytes([off & 0xFF, off >> 8])
    if len(blob) > BANK_BYTES:
        raise ValueError(f"render bank {len(blob)} B > 16 KiB")
    return bytes(blob) + bytes(BANK_BYTES - len(blob)), variants


def self_check() -> None:
    sprites = [(100, 110, 0, 4, 0, 0), (90, 130, 0, 6, 0, 1)]
    assert _sublist(sprites, [1, 0], (96, 120)) == bytes([0xFA, 10, 6, 4, 0xF6, 4, META_END])
    try:
        _sublist([(300, 0, 0, 0, 0, 0)], [0], (0, 0))
    except ValueError:
        pass
    else:
        raise AssertionError("dx fora de s8 nao reprovou")
    print("[PASS] gen_render_bank self-check")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path)
    ap.add_argument("--source-header", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        self_check()
        return 0
    report = json.loads(args.report.read_text(encoding="utf-8"))
    plans = report["selected_facing_pool"]["idle_cache_plan"]
    blob, variants = build(plans, args.source_header)
    args.out.write_bytes(blob)
    used = len(blob.rstrip(b"\0"))
    print(f"[EMITTED] {args.out} ~{used} B usados, {variants} variantes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
