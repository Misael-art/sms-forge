#!/usr/bin/env python3
"""Compose one fighter's idle poses as background tiles (BG/sprite hybrid test).

Each pose is rasterised from the exact streamed patterns at the exact screen
positions the ROM uses for sprites (line_lower_bound.pose_pixels), then cut
into the 8x8 BG grid over a fixed region = union bbox of all poses. Pixels
keep their palette index (BG palette := sprite palette), so the image is the
same; only the layer changes. Blank cells use one shared blank tile.

Bank blob (slot 2 offsets): header per frame {tile_off u16, tile_count u8,
names_a_off u16, names_b_off u16} then tile data (32 B each, unique per
frame) and, per tile set, the region's name table entries (u16, row-major).
Pixel equality of the composition is asserted per frame before emitting.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gen_render_bank as rb  # noqa: E402
import line_lower_bound as llb  # noqa: E402

BANK_BYTES = 16384
BLANK = 0xFF
SET_BASES = (256, 320)  # BGF_SET_A / BGF_SET_B in main.c
BLANK_TILE = 384
TILE_USE_SPRITE_PALETTE = 0x0800


def encode_tile(pixels: list[list[int]]) -> bytes:
    out = bytearray()
    for row in pixels:
        for plane in range(4):
            out.append(sum(((row[x] >> plane) & 1) << (7 - x) for x in range(8)))
    return bytes(out)


def compose(frames_px: list[dict[tuple[int, int], int]]) -> tuple[dict, list]:
    xs = [x for f in frames_px for x, _ in f]
    ys = [y for f in frames_px for _, y in f]
    col0, row0 = min(xs) // 8, min(ys) // 8
    cols, rows = max(xs) // 8 - col0 + 1, max(ys) // 8 - row0 + 1
    frames = []
    for px in frames_px:
        tiles, names = [], []
        for r in range(rows):
            for c in range(cols):
                cell = [[px.get(((col0 + c) * 8 + x, (row0 + r) * 8 + y), 0) for x in range(8)]
                        for y in range(8)]
                if any(any(v for v in line) for line in cell):
                    names.append(len(tiles))
                    tiles.append(encode_tile(cell))
                else:
                    names.append(BLANK)
        # Assert: decoding the grid reproduces every opaque pixel exactly.
        back = {}
        for i, t in enumerate(names):
            if t == BLANK:
                continue
            r, c = divmod(i, cols)
            for y in range(8):
                b = tiles[t][y * 4:y * 4 + 4]
                for x in range(8):
                    v = sum(((b[p] >> (7 - x)) & 1) << p for p in range(4))
                    if v:
                        back[((col0 + c) * 8 + x, (row0 + r) * 8 + y)] = v
        if back != {k: v for k, v in px.items() if v}:
            raise AssertionError("composicao BG diverge dos pixels do sprite")
        frames.append({"tiles": tiles, "names": names})
    return {"col0": col0, "row0": row0, "cols": cols, "rows": rows}, frames


def pose_colors(sprites: list, slots: dict[int, bytes]) -> dict[tuple[int, int], int]:
    px = {}
    for x, y, _p, tile, _o, _s in sprites:
        for dy, row in enumerate(llb.decode_pair(slots[tile // 2])):
            for dx, v in enumerate(row):
                if v:
                    px[(x + dx, y + dy)] = v
    return px


def build(plans: dict, header: Path, banks: bytes, key: str) -> tuple[bytes, dict]:
    actors = rb._actors(plans, header)
    states = llb.actor_slot_states(plans[key], banks)
    frames_px = [pose_colors(actors[key][f], states[f]) for f in range(len(actors[key]))]
    region, frames = compose(frames_px)
    n = len(frames)
    blob = bytearray(n * 7)
    meta = {"region": region, "frames": []}
    for i, fr in enumerate(frames):
        tile_off = 0x8000 + len(blob)
        blob += b"".join(fr["tiles"])
        # Ready-to-copy name table entries for each tile set, so the ROM
        # does no per-cell work on a swap (building them cost ~48 lines).
        offs = []
        for base in SET_BASES:
            offs.append(0x8000 + len(blob))
            for t in fr["names"]:
                e = BLANK_TILE if t == BLANK else (base + t) | TILE_USE_SPRITE_PALETTE
                blob += bytes([e & 0xFF, e >> 8])
        blob[i * 7:i * 7 + 7] = bytes([tile_off & 0xFF, tile_off >> 8, len(fr["tiles"]),
                                       offs[0] & 0xFF, offs[0] >> 8, offs[1] & 0xFF, offs[1] >> 8])
        meta["frames"].append({"tiles": len(fr["tiles"]), "tile_bytes": 32 * len(fr["tiles"])})
    if len(blob) > BANK_BYTES:
        raise ValueError(f"bg bank {len(blob)} B > 16 KiB")
    return bytes(blob) + bytes(BANK_BYTES - len(blob)), meta


def self_check() -> None:
    px = {(9, 17): 3, (16, 17): 5}
    region, frames = compose([px])
    assert region == {"col0": 1, "row0": 2, "cols": 2, "rows": 1}
    assert frames[0]["names"] == [0, 1] and len(frames[0]["tiles"]) == 2
    t = encode_tile([[1] * 8] * 8)
    assert t[0] == 0xFF and t[1] == 0 and len(t) == 32
    print("[PASS] gen_bg_fighter self-check")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path)
    ap.add_argument("--source-header", type=Path)
    ap.add_argument("--banks", type=Path)
    ap.add_argument("--actor", default="ryu_p2")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--header-out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    plans = json.loads(a.report.read_text())["selected_facing_pool"]["idle_cache_plan"]
    blob, meta = build(plans, a.source_header, a.banks.read_bytes(), a.actor)
    a.out.write_bytes(blob)
    r = meta["region"]
    max_tiles = max(f["tiles"] for f in meta["frames"])
    a.header_out.write_text("\n".join([
        "/* Generated by tools/gen_bg_fighter.py -- BG layer fighter region. */",
        "#ifndef BG_FIGHTER_H", "#define BG_FIGHTER_H",
        f"#define BGF_COL0 {r['col0']}u", f"#define BGF_ROW0 {r['row0']}u",
        f"#define BGF_COLS {r['cols']}u", f"#define BGF_ROWS {r['rows']}u",
        f"#define BGF_FRAMES {len(meta['frames'])}u", f"#define BGF_MAX_TILES {max_tiles}u",
        "#endif", ""]))
    print(json.dumps(meta))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
