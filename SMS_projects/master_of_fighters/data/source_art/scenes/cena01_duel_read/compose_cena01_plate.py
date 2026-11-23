#!/usr/bin/env python3
"""Placa diagnóstica da Cena 01 — leitura do duelo.

Não desenha personagem. Os lutadores continuam nos sprites aprovados de
J.J. fonte v6 / Social preservado. Esta placa só ocupa P0: faixa de HUD,
ar e chão, para a sola medida em Y143 pousar na linha de contato Y144.

Índice 0 é cor de backdrop visível, não transparência de sprite.
"""
import hashlib
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[os.pardir] * 5))
sys.path.insert(0, os.path.join(ROOT, "tools", "sms_wrapper"))
from png_io import write_indexed_png  # noqa: E402
from png_to_sms_tiles import tile_bytes  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 256, 192
TILE = 8
COLS, ROWS = W // TILE, H // TILE
TILE_BASE = 256

# RGB no contrato 6-bit e o byte CRAM correspondente (--bbggrr).
PALETTE = [
    (0, 0, 85),       # 0 backdrop
    (0, 85, 85),      # 1 chão
    (170, 170, 170),  # 2 aresta iluminada do chão
    (0, 0, 0),        # 3 HUD / linha de contato
    (170, 170, 0),    # 4 fio dourado
    (255, 255, 255),  # 6 texto — índice 5
    (0, 170, 0),      # 6 vida cheia
    (0, 85, 0),       # 7 trilho (reservado, não usado na placa cheia)
]
CRAM = [0x10, 0x14, 0x2A, 0x00, 0x0A, 0x3F, 0x08, 0x04]
INK = 5
HUD = 3
LIFE = 6
CONTACT = 3
EDGE = 2
FLOOR = 1
AIR = 0

GLYPHS = {
    "D": (
        "##    ",
        "##  # ",
        "##   #",
        "##   #",
        "##   #",
        "##  # ",
        "##    ",
    ),
    "R": (
        "####  ",
        "#   # ",
        "#   # ",
        "####  ",
        "# #   ",
        "#  #  ",
        "#   # ",
    ),
    "J": (
        "  ### ",
        "   #  ",
        "   #  ",
        "   #  ",
        "#  #  ",
        "#  #  ",
        " ##   ",
    ),
}


def blank():
    return [[AIR for _ in range(W)] for _ in range(H)]


def stamp_tile(px, col, row, rows8):
    y0, x0 = row * TILE, col * TILE
    for y, line in enumerate(rows8):
        for x, ch in enumerate(line):
            px[y0 + y][x0 + x] = ch


def solid(index):
    return [index] * TILE


def glyph_tile(ch):
    rows = []
    for line in GLYPHS[ch]:
        cells = [INK if c == "#" else HUD for c in line]
        cells += [HUD] * (TILE - len(cells))
        rows.append(cells[:TILE])
    while len(rows) < TILE:
        rows.append([HUD] * TILE)
    return rows


def life_tile(side):
    rows = []
    rows.append([HUD] * TILE)
    for _ in range(6):
        row = [LIFE] * TILE
        if side == "l":
            row[0] = HUD
        elif side == "r":
            row[7] = HUD
        rows.append(row)
    rows.append([HUD] * TILE)
    return rows


def contact_tile():
    """Última linha do ar: a sola de J.J. nesta face termina em Y142."""
    rows = [solid(AIR) for _ in range(7)]
    rows.append(solid(CONTACT))
    return rows


def edge_tile():
    rows = [solid(EDGE)]
    rows += [solid(FLOOR) for _ in range(7)]
    return rows


def hud_tile():
    return [solid(HUD) for _ in range(TILE)]


def rule_tile():
    rows = [solid(HUD) for _ in range(7)]
    rows.append(solid(4))
    return rows


def air_tile():
    return [solid(AIR) for _ in range(TILE)]


def floor_tile():
    return [solid(FLOOR) for _ in range(TILE)]


def build_pixels():
    px = blank()
    tiles = {
        "air": air_tile(),
        "floor": floor_tile(),
        "contact": contact_tile(),
        "edge": edge_tile(),
        "hud": hud_tile(),
        "rule": rule_tile(),
        "life_l": life_tile("l"),
        "life_m": life_tile("m"),
        "life_r": life_tile("r"),
        "D": glyph_tile("D"),
        "R": glyph_tile("R"),
        "J": glyph_tile("J"),
    }
    grid = [["air" for _ in range(COLS)] for _ in range(ROWS)]
    for x in range(COLS):
        grid[0][x] = "hud"
        grid[1][x] = "hud"
        grid[2][x] = "rule"
        grid[17][x] = "contact"
        grid[18][x] = "edge"
        for y in range(19, ROWS):
            grid[y][x] = "floor"
    # Social está à esquerda nesta face; J.J. à direita.
    grid[0][1] = "D"
    grid[0][2] = "R"
    grid[0][29] = "J"
    grid[0][30] = "J"
    for start in (1, 23):
        grid[1][start] = "life_l"
        for x in range(start + 1, start + 7):
            grid[1][x] = "life_m"
        grid[1][start + 7] = "life_r"
    for y in range(ROWS):
        for x in range(COLS):
            stamp_tile(px, x, y, tiles[grid[y][x]])
    return px, grid, tiles


def unique_tiles(tiles, grid):
    order = []
    index = {}
    for row in grid:
        for name in row:
            if name not in index:
                index[name] = len(order)
                order.append(name)
    return order, index


def emit(px, grid, tiles):
    rows = [bytes(row) for row in px]
    png_path = os.path.join(HERE, "cena01_plate_v1.png")
    write_indexed_png(png_path, W, H, PALETTE, rows, trns=())
    digest = hashlib.sha256(open(png_path, "rb").read()).hexdigest()
    big = []
    for row in px:
        wide = []
        for value in row:
            wide.extend([value, value, value, value])
        line = bytes(wide)
        big.extend([line, line, line, line])
    preview = os.path.join(HERE, "cena01_plate_v1_4x.png")
    write_indexed_png(preview, W * 4, H * 4, PALETTE, big, trns=())
    order, index = unique_tiles(tiles, grid)
    raw = bytearray()
    for name in order:
        block = tiles[name]
        # tile_bytes lê uma imagem; monta um PNG temporário de 8×8.
        tiny = os.path.join(HERE, "_tile.png")
        write_indexed_png(tiny, 8, 8, PALETTE, [bytes(r) for r in block], trns=())
        from png_io import read_indexed_png
        img = read_indexed_png(tiny)
        raw += tile_bytes(img["pixels"], 0, 0)
    os.remove(tiny)
    words = []
    for row in grid:
        for name in row:
            words.append(TILE_BASE + index[name])
    header = os.path.join(HERE, "cena01_bg.h")
    cram = ", ".join(f"0x{b:02X}" for b in CRAM + [0] * (16 - len(CRAM)))
    tile_csv = ", ".join(f"0x{b:02X}" for b in raw)
    map_csv = ", ".join(f"0x{w:04X}" for w in words)
    text = (
        "/* Placa Cena 01. Gerada por compose_cena01_plate.py. */\n"
        f"/* png_sha256 {digest} */\n"
        f"#define CENA01_TILE_BASE {TILE_BASE}u\n"
        f"#define CENA01_TILE_COUNT {len(order)}u\n"
        f"#define CENA01_TILE_BYTES {len(raw)}u\n"
        f"const unsigned char cena01_bg_palette[16] = {{{cram}}};\n"
        f"const unsigned char cena01_tiles[{len(raw)}] = {{\n{tile_csv}\n}};\n"
        f"const unsigned int cena01_map[{len(words)}] = {{\n{map_csv}\n}};\n"
    )
    open(header, "w", encoding="utf-8").write(text)
    print(f"[OK] {png_path} sha256={digest} tiles={len(order)} bytes={len(raw)}")
    return digest


def main():
    px, grid, tiles = build_pixels()
    # A sola medida termina em Y143; a linha de contato é o primeiro pixel de Y144.
    if px[142][16] != AIR or px[143][16] != CONTACT or px[144][16] != EDGE:
        raise SystemExit("contato do chão fora de Y143")
    if px[0][9] != INK or px[9][8] != HUD or px[9][9] != LIFE:
        raise SystemExit("nome ou barra fora da faixa de HUD")
    if px[9][16] != LIFE or px[9][71] != HUD or px[9][70] != LIFE:
        raise SystemExit("medidor esquerdo não é uma barra contínua")
    emit(px, grid, tiles)
    return 0


if __name__ == "__main__":
    sys.exit(main())
