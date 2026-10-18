#!/usr/bin/env python3
"""Legal idle frames for the integrated ROM's own SAT (L091 input).

Draws every Ken-idle x Ryu-idle pair the boot can show, from the pruned
metasprites and the tile banks the runtime streams. Placement follows
fight.c: anchor 96/152, floor 128, origin sx/sy, visible pixel at
(sx+dx, sy+dy). The SAT stores y-1 because the VDP draws one line lower.
Flicker subsets are not baked in: audit_render_glitch --mode flicker treats
a frame as a subset of one of these images.

This does not approve timing, input or a full move list.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools" / "sms_wrapper"))
from png_io import write_png_rgb  # noqa: E402

W, H = 256, 192
FLOOR = 128
PAIR = 64
ANCHOR = (96, 152)
FRAME_RE = re.compile(
    r"\{\s*\d+\s*,\s*(\d+)\s*,\s*0\s*,\s*0\s*,\s*(?:0|\w+)\s*,\s*(\w+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,"
)
AXIS_RE_TMPL = r"const unsigned char {name}\[4\] = \{{\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)\s*,\s*(0x[0-9A-Fa-f]+)"
POSE_RE = re.compile(
    r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*\(const unsigned char \*\)0x([0-9A-Fa-f]+)u\s*,\s*"
    r"\(const unsigned char \*\)0x([0-9A-Fa-f]+)u"
)
PAL_RE = re.compile(
    r"static const unsigned char versus_sprite_palette\[16\] = \{\s*([^}]+)\}"
)



def s8(v: int) -> int:
    return v - 256 if v > 127 else v


def s16(lo: int, hi: int) -> int:
    v = lo | (hi << 8)
    return v - 65536 if v >= 32768 else v


def sms_rgb(c: int) -> tuple[int, int, int]:
    return ((c & 3) * 85, ((c >> 2) & 3) * 85, ((c >> 4) & 3) * 85)


def decode_pair(blob: bytes) -> list[list[int]]:
    """8x16 indices, top tile then bottom tile, planar 4bpp."""
    if len(blob) != PAIR:
        raise ValueError("par de tiles incompleto")
    rows: list[list[int]] = []
    for base in (0, 32):
        for y in range(8):
            b0, b1, b2, b3 = blob[base + y * 4: base + y * 4 + 4]
            row = []
            for x in range(8):
                bit = 7 - x
                row.append(((b0 >> bit) & 1) | (((b1 >> bit) & 1) << 1) |
                            (((b2 >> bit) & 1) << 2) | (((b3 >> bit) & 1) << 3))
            rows.append(row)
    return rows


def origin_x(anchor: int, axis_x: int, width: int, facing_left: bool) -> int:
    if not facing_left:
        return anchor + axis_x
    rounded = (width + 7) & ~7
    return anchor - (axis_x + rounded)


def paint(canvas: list[list[int]], indices: list[list[int]], x: int, y: int) -> None:
    for row in range(16):
        sy = y + row
        if not (0 <= sy < H):
            continue
        for col in range(8):
            sx = x + col
            if not (0 <= sx < W):
                continue
            pix = indices[row][col]
            if pix and canvas[sy][sx] == 0:
                canvas[sy][sx] = pix


def pieces(meta: bytes) -> list[tuple[int, int, int]]:
    out = []
    i = 0
    while i < len(meta) and meta[i] != 0x80:
        out.append((s8(meta[i]), s8(meta[i + 1]), meta[i + 2]))
        i += 3
    return out


def self_check() -> None:
    tile = bytearray(PAIR)
    tile[0] = 0x80
    rows = decode_pair(bytes(tile))
    assert rows[0][0] == 1 and rows[0][1] == 0 and rows[8][0] == 0
    assert origin_x(152, -18, 40, True) == 130
    assert origin_x(96, -25, 51, False) == 71
    canvas = [[0] * 8 for _ in range(16)]
    # first sprite wins: a later index must not cover pixel 0
    paint(canvas, rows, 0, 0)
    other = decode_pair(bytes([0x80]) + bytes(PAIR - 1))
    other[0][0] = 4
    paint(canvas, other, 0, 0)
    assert canvas[0][0] == 1
    print("[PASS] render_legal_idle self-check")


def _axis(text: str, name: str) -> tuple[int, int]:
    m = re.search(AXIS_RE_TMPL.format(name=re.escape(name)), text)
    if not m:
        raise SystemExit(f"eixo ausente: {name}")
    vals = [int(g, 16) for g in m.groups()]
    return s16(vals[0], vals[1]), s16(vals[2], vals[3])


def _poses(text: str, who: str) -> list[tuple[int, int, int, int]]:
    blk = re.search(rf"static const PoseTiles {who}_pose_tiles\[\d+\] = \{{(.*?)\n\}};",
                    text, re.S)
    if not blk:
        raise SystemExit(f"tabela de poses ausente: {who}")
    out = []
    for bank, off, right, left in POSE_RE.findall(blk.group(1)):
        out.append((int(bank), int(off), int(right, 16), int(left, 16)))
    return out


def _frames(text: str, who: str) -> list[tuple[int, int, int, int]]:
    blk = re.search(rf"static const Frame {who}_frames_all\[\w+\] = \{{(.*?)\n\}};", text, re.S)
    if not blk:
        raise SystemExit(f"frames ausentes: {who}")
    frames = []
    for pose, axis, width, height in FRAME_RE.findall(blk.group(1)):
        ax, ay = _axis(text, axis)
        frames.append((int(pose), ax, ay, int(width)))
        if int(height) <= 0:
            raise SystemExit(f"altura invalida em {who} pose {pose}")
    m = re.search(rf"static const Anim {who}_anims\[\d+\] = \{{\s*\{{\s*\d+\s*,\s*(\d+)\s*,", text)
    if not m:
        raise SystemExit(f"anim idle ausente: {who}")
    idle_n = int(m.group(1))
    return frames[:idle_n]


def render_pair(banks: bytes, meta: bytes, palette: list[int],
                ken: tuple, ryu: tuple) -> tuple[list[list[tuple[int, int, int]]], int, int]:
    canvas = [[0 for _ in range(W)] for _ in range(H)]
    for spec, anchor, facing_left in (ken, ryu):
        bank, off, ptr, axis_x, axis_y, width = spec
        sx = origin_x(anchor, axis_x, width, facing_left) & 0xFF
        sy = (FLOOR + axis_y) & 0xFF
        base = (bank - 2) * 16384 + off
        raw = meta[ptr - 0x8000:]
        for dx, dy, tile in pieces(raw):
            pair = banks[base + (tile // 2) * PAIR: base + (tile // 2 + 1) * PAIR]
            x = (sx + dx) & 0xFF
            y = (sy + dy) & 0xFF
            paint(canvas, decode_pair(pair), x, y)
    colors = [sms_rgb(c) for c in palette]
    rgb = [[colors[pix] for pix in row] for row in canvas]
    lit_rows = [y for y, row in enumerate(canvas) if any(row)]
    height = (lit_rows[-1] - lit_rows[0] + 1) if lit_rows else 0
    return rgb, height, len(lit_rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scene", type=Path)
    ap.add_argument("--poses", type=Path)
    ap.add_argument("--banks", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        self_check()
        return 0
    if not all((args.scene, args.poses, args.banks, args.meta, args.out)):
        ap.error("faltam --scene --poses --banks --meta --out")
    scene = args.scene.read_text(encoding="utf-8", errors="replace")
    poses = args.poses.read_text(encoding="utf-8", errors="replace")
    banks = args.banks.read_bytes()
    meta = args.meta.read_bytes()
    pal_m = PAL_RE.search(scene)
    if not pal_m:
        raise SystemExit("versus_sprite_palette ausente")
    palette = [int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]+", pal_m.group(1))]
    if len(palette) != 16:
        raise SystemExit("paleta sem 16 entradas")
    ken_frames = _frames(scene, "ken")
    ryu_frames = _frames(scene, "ryu")
    ken_poses = _poses(poses, "ken")
    ryu_poses = _poses(poses, "ryu")
    args.out.mkdir(parents=True, exist_ok=True)
    heights = []
    for ki, (kp, kax, kay, kw) in enumerate(ken_frames):
        kb, ko, kr, kl = ken_poses[kp]
        ken = (kb, ko, kr, kax, kay, kw)
        for ri, (rp, rax, ray, rw) in enumerate(ryu_frames):
            rb, ro, rr, rl = ryu_poses[rp]
            ryu = (rb, ro, rl, rax, ray, rw)
            rgb, height, _rows = render_pair(banks, meta, palette, (ken, ANCHOR[0], False),
                                              (ryu, ANCHOR[1], True))
            write_png_rgb(args.out / f"ken{ki}_ryu{ri}.png", W, H, rgb)
            heights.append((ki, ri, height))
    ken0 = [h for k, _r, h in heights if k == 0]
    print(f"[PASS] {len(heights)} imagens legais em {args.out}")
    print(f"[IDLE] ken0 x ryu*: altura opaca das linhas acesas {ken0}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
