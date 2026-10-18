"""Sprite MUGEN (256 cores ACT) -> pose SMS: tiles 4bpp 8x8 com dedup + flip H/V.

Contratos citados:
- Tile SMS: 4 planos de bit, 4 bytes por linha, MSB-first, 32 B/tile
  (`png_to_sms_tiles.py` do workspace; `SMS_loadTiles` = `(tilefrom)*32`, SMSlib.h:130).
- Cor: paleta mestra 6-bit, canal x85 (`sms_palette.py` = verdade de cor do SMSForge);
  palavra CRAM = RGB(r,g,b) = r | g<<2 | b<<4, canais 0..3 (SMSlib.h secao "Colors").
- Indice 0 transparente (AGENTS.md; `SMS_load1bppTiles` color0, SMSlib.h:131).

Pose = grade de tiles cobrindo o bitmap; cada colocacao referencia um tile unico e
flags de flip — `SPRITEMODE_TALL` (SMSlib.h:57) e decisao do runtime, os tiles aqui
sao sempre 8x8.
"""
from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))       # tools/sms_wrapper
import sms_palette as _pal


@dataclass
class Placement:
    tile: int
    hflip: bool
    vflip: bool
    x: int                                  # px no grid da pose (multiplo de 8)
    y: int


@dataclass
class Pose:
    width: int
    height: int
    tiles: list[bytes] = field(default_factory=list)         # 32 B cada, ordem de aparição
    placements: list[Placement] = field(default_factory=list)
    palette: list[int] = field(default_factory=list)         # 16 palavras CRAM; [0]=0 transparente
    unique_tiles: int = 0
    flips_used: int = 0


def _subpalette(sp) -> tuple[list[int], dict[int, int]]:
    """(16 palavras CRAM com [0]=transparente, mapa pixel-index -> indice SMS)."""
    freq: Counter = Counter()
    for p in sp.pixels:
        if p:
            rgb = sp.palette[p] if p < len(sp.palette) else (0, 0, 0)
            freq[_pal.code_rgb(_pal.nearest_code(tuple(rgb)))] += 1
    colors = [c for c, _ in freq.most_common(16)][:15]
    words = [0] + [_pal_rgb_word(c) for c in colors]
    remap: dict[int, int] = {0: 0}
    for p in set(sp.pixels):
        if not p:
            continue
        rgb = _pal.code_rgb(_pal.nearest_code(tuple(sp.palette[p] if p < len(sp.palette) else (0, 0, 0))))
        if colors:
            best = min(range(len(colors)), key=lambda i: sum((colors[i][k] - rgb[k]) ** 2 for k in range(3)))
            remap[p] = best + 1
        else:
            remap[p] = 0
    return words, remap


def _pal_rgb_word(rgb) -> int:
    r, g, b = _pal.nearest_code(rgb)
    return r | (g << 2) | (b << 4)


def _tile_rows(sp, remap) -> list[list[int]]:
    """Bitmap -> linhas de indices SMS (borda direita/inferior completada com 0 transparente)."""
    tw, th = -(-sp.width // 8), -(-sp.height // 8)
    rows: list[list[int]] = []
    for ty in range(th):
        for tx in range(tw):
            tile = []
            for y in range(8):
                py = ty * 8 + y
                line = []
                for x in range(8):
                    px = tx * 8 + x
                    v = sp.pixels[py * sp.width + px] if py < sp.height and px < sp.width else 0
                    line.append(remap.get(v, 0))
                tile.append(line)
            rows.append(tile)
    return rows


def _flip_h(tile): return [row[::-1] for row in tile]
def _flip_v(tile): return tile[::-1]


def _encode_tile(tile) -> bytes:
    """8x8 indices 4bpp -> 32 B: por linha, 4 bytes = planos 0..3, MSB = pixel 0
    (identico a png_to_sms_tiles.tile_bytes do workspace)."""
    out = bytearray()
    for row in tile:
        planes = [0, 0, 0, 0]
        for x in range(8):
            c = row[x] & 15
            for p in range(4):
                planes[p] |= ((c >> p) & 1) << (7 - x)
        out += bytes(planes)
    return bytes(out)


def to_sms_pose(sp) -> Pose:
    words, remap = _subpalette(sp)
    tw = -(-sp.width // 8)
    pose = Pose(width=sp.width, height=sp.height, palette=(words + [0] * 16)[:16])
    seen: dict[tuple, tuple[int, bool, bool]] = {}
    rows = _tile_rows(sp, remap)
    for i, tile in enumerate(rows):
        key = tuple(map(tuple, tile))
        cands = [(key, False, False),
                 (tuple(map(tuple, _flip_h(tile))), True, False),
                 (tuple(map(tuple, _flip_v(tile))), False, True),
                 (tuple(map(tuple, _flip_h(_flip_v(tile)))), True, True)]
        cands.sort(key=lambda c: c[0])
        canon, hf, vf = cands[0]
        if canon not in seen:
            seen[canon] = len(pose.tiles)
            pose.tiles.append(_encode_tile([list(r) for r in canon]))
        pose.placements.append(Placement(seen[canon], hf, vf, (i % tw) * 8, (i // tw) * 8))
    pose.unique_tiles = len(pose.tiles)
    pose.flips_used = sum(1 for p in pose.placements if p.hflip or p.vflip)
    return pose
