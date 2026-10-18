#!/usr/bin/env python3
"""Pose table for the integrated runtime: per fighter pose, the tile blob the
ROM streams from (Ken: P1 TILES; Ryu: P2 TILES, its own palette pool) and the
right/left metasprites with fully transparent 8x16 pieces removed.

Pruning is required: the worst idle/guard/punch pose pair needs 83 SAT
entries unpruned and 63 pruned (64 is the hardware table).

Checks (fail the build instead of emitting a wrong table):
  - every dy is a multiple of 16 (TALL rows) -- the runtime flicker scheduler
    works per metasprite row;
  - every piece's pair lies inside its blob;
  - pieces never exceed 64 per pose.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FIRST_BANK = 2
PAIR = 64
END = 0x80


def arr(text: str, name: str) -> list[int]:
    m = re.search(rf"const unsigned char {name}\[\d+\] = \{{(.*?)\}};", text, re.S)
    if not m:
        raise KeyError(name)
    return [int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]+", m.group(1))]


def define(text: str, name: str) -> int:
    return int(re.search(rf"#define {name} (\d+)", text).group(1))


def s8(v: int) -> int:
    return v - 256 if v > 127 else v


def prune(meta: list[int], blob: bytes) -> list[int]:
    if meta[-1] != END:
        raise ValueError("metasprite sem terminador")
    out = []
    for i in range(0, len(meta) - 1, 3):
        dx, dy, tile = meta[i:i + 3]
        if s8(dy) % 16:
            raise ValueError(f"dy {s8(dy)} fora da grade TALL")
        pair = blob[(tile // 2) * PAIR:(tile // 2 + 1) * PAIR]
        if len(pair) != PAIR:
            raise ValueError("par fora do blob")
        if pair != bytes(PAIR):
            out += [dx, dy, tile]
    if len(out) // 3 > 64:
        raise ValueError("pose com mais de 64 pecas")
    dys = [s8(v) for v in out[1::3]]
    if dys != sorted(dys):
        raise ValueError("pecas fora de ordem de linha (dy decrescente)")
    return out + [END]


def row_table(meta: list[int]) -> list[int]:
    """[count, dy0, n0, dy1, n1, ...] in metasprite order (rows contiguous)."""
    rows: list[list[int]] = []
    for dy in meta[1:-1:3]:
        if rows and rows[-1][0] == dy:
            rows[-1][1] += 1
        else:
            rows.append([dy, 1])
    return [len(rows)] + [v for r in rows for v in r]


def widest_row(meta: list[int]) -> int:
    dys = [s8(v) for v in meta[1:-1:3]]
    return max((dys.count(d) for d in set(dys)), default=0)


META_BANK = 37
BANK_BYTES = 16384


def build(text: str, banks: bytes) -> tuple[str, dict, bytes]:
    # Pruned metasprites live in ROM bank META_BANK (slot 2 window); the ROM
    # maps it while reading them. Fixed banks 0/1 overflowed otherwise.
    lines = ["/* gerado por tools/gen_pose_table.py - nao editar */",
             "#ifndef POSE_TABLE_H", "#define POSE_TABLE_H",
             f"#define POSE_META_BANK {META_BANK}u",
             "typedef struct { unsigned char bank; unsigned int off;",
             "                 const unsigned char *meta_r, *meta_l;",
             "                 const unsigned char *rows_r, *rows_l; } PoseTiles;",
             "/* rows_*: [row count, (dy, pieces) per row] -- same bank as meta_* */"]
    stats = {}
    meta_blob = bytearray()
    for who, p2 in (("ken", False), ("ryu", True)):
        blk = re.search(rf"static const Frame {who}_frames_all\[\w+\] = \{{(.*?)\n\}};", text, re.S).group(1)
        rows = [l for l in blk.splitlines() if l.strip().startswith("{")]
        entries, worst, max_pair = [], 0, 0
        for n, row in enumerate(rows):
            base = re.findall(r"(\w+)_META\b", row)[0]
            tiles = f"{base}_P2_TILES" if p2 else f"{base}_TILES"
            bank, off, size = (define(text, f"{tiles}_{k}") for k in ("BANK", "OFF", "SIZE"))
            start = (bank - FIRST_BANK) * 16384 + off
            blob = banks[start:start + size]
            metas, rowptrs = [], []
            for side in ("META", "METAL"):
                name = f"{base}_P2_{side}" if p2 else f"{base}_{side}"
                pruned = prune(arr(text, name), blob)
                worst = max(worst, (len(pruned) - 1) // 3)
                max_pair = max([max_pair] + [t // 2 for t in pruned[2:-1:3]])
                wide = widest_row(pruned)
                if wide > 8:
                    stats.setdefault("rows_over_8", []).append((who, n, side, wide))
                metas.append(f"(const unsigned char *)0x{0x8000 + len(meta_blob):04X}u")
                meta_blob += bytes(pruned)
                row_list = row_table(pruned)
                rowptrs.append(f"(const unsigned char *)0x{0x8000 + len(meta_blob):04X}u")
                meta_blob += bytes(row_list)
            entries.append(f"    {{ {bank}, {off}, {metas[0]}, {metas[1]}, {rowptrs[0]}, {rowptrs[1]} }},")
        lines.append(f"static const PoseTiles {who}_pose_tiles[{len(rows)}] = {{")
        lines += entries + ["};"]
        stats[who] = {"poses": len(rows), "max_pieces": worst, "max_pair_id": max_pair}
        lines.append(f"#define {who.upper()}_POSE_MAX_PIECES {worst}u")
        lines.append(f"#define {who.upper()}_POSE_PAIR_IDS {max_pair + 1}u")
    lines += ["#endif", ""]
    if len(meta_blob) > BANK_BYTES:
        raise ValueError(f"metas podadas {len(meta_blob)} B > 16 KiB")
    stats["meta_bank_bytes"] = len(meta_blob)
    return "\n".join(lines), stats, bytes(meta_blob) + bytes(BANK_BYTES - len(meta_blob))


def self_check() -> None:
    blob = bytes(PAIR) + bytes([1]) * PAIR
    assert prune([0, 0, 0, 8, 16, 2, END], blob) == [8, 16, 2, END]
    assert widest_row([0, 0, 2, 8, 0, 2, 0, 16, 2, END]) == 2
    assert row_table([0, 0, 2, 8, 0, 2, 0, 16, 2, END]) == [2, 0, 2, 16, 1]
    for bad in ([0, 8, 2, END], [0, 0, 6, END], [0, 16, 2, 8, 0, 2, END]):
        try:
            prune(bad, blob)
        except ValueError:
            continue
        raise AssertionError(f"{bad} deveria reprovar")
    print("[PASS] gen_pose_table self-check (poda, grade TALL, par fora do blob, ordem de linha)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--header", type=Path)
    ap.add_argument("--banks", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--bank-out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    text, stats, blob = build(a.header.read_text(), a.banks.read_bytes())
    a.out.write_text(text)
    a.bank_out.write_bytes(blob)
    print(stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
