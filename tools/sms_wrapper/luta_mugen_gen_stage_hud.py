#!/usr/bin/env python3
"""Gera o atlas de HUD e a paleta usados pelo piloto integrado.

A folha indexada continua sendo a fonte dos padrões e o build não redesenha
glifos. A planta 256×192 permanece como fixture histórica para
``--check-planta``; ela não é enviada à ROM. O runtime preenche a name table
com um único tile de cor sólida e grava o HUD sobre ele.

Contrato (GDD 2026-10-04):
  tiles 0–255  pool dos lutadores (primeira metade da VRAM)
  tiles 256+   tile sólido de fundo e glifos/barras do HUD
  name table   tile sólido em toda a PNT; HUD nas linhas 0–1
  HUD          25 células, no máximo 2 escritas por VBlank
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from png_io import read_indexed_png, write_indexed_png  # noqa: E402

DEFAULT_PROJECT = (Path(__file__).resolve().parents[2] / "SMS_projects" /
                   "luta_mugen")
LUTA = DEFAULT_PROJECT
SHEET = LUTA / "res" / "stage" / "arena_tecnica.png"
PLANTA = LUTA / "res" / "stage" / "planta_arena.png"

# SMS --bbggrr. RGB de contrato = canal * 85.
PALETTE_RGB = [
    (0, 0, 0),        # 0 preto
    (0, 85, 170),     # 1 céu
    (85, 170, 0),     # 2 piso
    (0, 0, 0),        # 3 não usado
    (0, 255, 0),      # 4 vida
    (85, 85, 85),     # 5 vida vazia
    (255, 255, 255),  # 6 texto
] + [(0, 0, 0)] * 9

SKY, FLOOR, BLACK, GREEN, GRAY, INK = 1, 2, 0, 4, 5, 6
OFF_SKY, OFF_FLOOR, OFF_HORIZON = 0, 1, 2
OFF_BAR_ON, OFF_BAR_OFF, OFF_DIGIT, OFF_LETTER = 3, 4, 5, 15
STAGE_TILE_BASE = 256
N_BASE = 5
LETTERS = "ROUNDFIGHTKMEW"
GLYPHS = {
    "0": [" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "    #", "  ## ", " #   ", "#    ", "#####"],
    "3": [" ### ", "#   #", "    #", " ### ", "    #", "#   #", " ### "],
    "4": ["#   #", "#   #", "#   #", "#####", "    #", "    #", "    #"],
    "5": ["#####", "#    ", "#    ", "#### ", "    #", "#   #", " ### "],
    "6": [" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "],
    "8": [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
    "9": [" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "],
    "R": ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "U": ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
    "I": [" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "G": [" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ### "],
    "H": ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
}

# 25 células: 0–7 barra P1, 8–15 barra P2, 16–17 timer, 18–19 placar, 20–24 banner.
CELLS = (
    [(1 + i, 0) for i in range(8)]
    + [(23 + i, 0) for i in range(8)]
    + [(15, 0), (16, 0), (2, 1), (29, 1)]
    + [(12 + i, 1) for i in range(5)]
)
BANNERS = (
    "     ",   # 0 vazio
    "ROUND",   # 1
    "FIGHT",   # 2
    "K O  ",   # 3 K.O. sem ponto: o tile de letra não tem o ponto
    "TIME ",   # 4
)


def _solid(idx: int) -> list[list[int]]:
    return [[idx] * 8 for _ in range(8)]


def _glyph(rows: list[str], ink: int = INK) -> list[list[int]]:
    tile = _solid(SKY)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#":
                tile[y][x + 1] = ink
    return tile


def _bar(idx: int) -> list[list[int]]:
    tile = _solid(idx)
    for x in range(8):
        tile[0][x] = BLACK
        tile[7][x] = BLACK
    for y in range(8):
        tile[y][0] = BLACK
        tile[y][7] = BLACK
    return tile


def _horizon() -> list[list[int]]:
    tile = _solid(SKY)
    for x in range(8):
        tile[3][x] = BLACK
    for y in range(4, 8):
        for x in range(8):
            tile[y][x] = FLOOR
    return tile


def authored_tiles() -> list[list[list[int]]]:
    tiles = [_solid(SKY), _solid(FLOOR), _horizon(), _bar(GREEN), _bar(GRAY)]
    for d in "0123456789":
        tiles.append(_glyph(GLYPHS[d]))
    for ch in LETTERS:
        tiles.append(_glyph(GLYPHS[ch]))
    return tiles


def letter_off(ch: str) -> int:
    if ch == " ":
        return OFF_SKY
    return OFF_LETTER + LETTERS.index(ch)


def boot_offsets() -> list[int]:
    offs = [OFF_BAR_ON] * 16
    offs += [OFF_DIGIT + 9, OFF_DIGIT + 9, OFF_DIGIT, OFF_DIGIT]
    offs += [letter_off(ch) for ch in BANNERS[1]]
    if len(offs) != 25:
        raise SystemExit(f"HUD boot tem {len(offs)} células")
    return offs


def banner_rows() -> list[list[int]]:
    return [[letter_off(ch) for ch in row] for row in BANNERS]


def _sheet_pixels(tiles: list[list[list[int]]]) -> tuple[int, int, list[bytes]]:
    cols = 8
    rows = (len(tiles) + cols - 1) // cols
    w, h = cols * 8, rows * 8
    canvas = [[SKY] * w for _ in range(h)]
    for i, tile in enumerate(tiles):
        x0, y0 = (i % cols) * 8, (i // cols) * 8
        for y in range(8):
            canvas[y0 + y][x0:x0 + 8] = tile[y]
    return w, h, [bytes(row) for row in canvas]


def _tile_from_sheet(pixels: list[bytes], index: int) -> list[list[int]]:
    x0, y0 = (index % 8) * 8, (index // 8) * 8
    return [list(pixels[y0 + y][x0:x0 + 8]) for y in range(8)]


def _encode_tile(tile: list[list[int]]) -> bytes:
    out = bytearray()
    for y in range(8):
        for plane in range(4):
            b = 0
            for x in range(8):
                if tile[y][x] & (1 << plane):
                    b |= 0x80 >> x
            out.append(b)
    return bytes(out)


def _nametable(tiles_n: int, boot: list[int]) -> bytearray:
    words = [STAGE_TILE_BASE + OFF_SKY] * (32 * 24)
    for x in range(32):
        words[15 * 32 + x] = STAGE_TILE_BASE + OFF_HORIZON
        for y in range(16, 24):
            words[y * 32 + x] = STAGE_TILE_BASE + OFF_FLOOR
    for i, (x, y) in enumerate(CELLS):
        words[y * 32 + x] = STAGE_TILE_BASE + boot[i]
    raw = bytearray()
    for w in words:
        if w < STAGE_TILE_BASE or w >= STAGE_TILE_BASE + tiles_n:
            raise SystemExit(f"tile {w} fora do conjunto")
        raw.append(w & 0xFF)
        raw.append((w >> 8) & 0xFF)
    if len(raw) != 1536:
        raise SystemExit("name table != 1536")
    return raw


def _planta_pixels(tiles: list[list[list[int]]], boot: list[int]) -> list[bytes]:
    canvas = [[SKY] * 256 for _ in range(192)]
    for y in range(15):
        for x in range(32):
            _blit(canvas, x, y, tiles[OFF_SKY])
    for x in range(32):
        _blit(canvas, x, 15, tiles[OFF_HORIZON])
        for y in range(16, 24):
            _blit(canvas, x, y, tiles[OFF_FLOOR])
    for i, (x, y) in enumerate(CELLS):
        _blit(canvas, x, y, tiles[boot[i]])
    return [bytes(row) for row in canvas]


def _blit(canvas: list[list[int]], tx: int, ty: int, tile: list[list[int]]) -> None:
    for y in range(8):
        canvas[ty * 8 + y][tx * 8:tx * 8 + 8] = tile[y]


def _c_bytes(name: str, data: bytes, per: int = 16) -> str:
    lines = [f"const unsigned char {name}[{len(data)}] = {{"]
    for i in range(0, len(data), per):
        chunk = ", ".join(f"0x{b:02X}" for b in data[i:i + per])
        lines.append(f"    {chunk},")
    lines.append("};")
    return "\n".join(lines)


def _emit(out_dir: Path, tiles: list[list[list[int]]]) -> None:
    boot = boot_offsets()
    encoded = b"".join(_encode_tile(t) for t in tiles)
    # Validate the old layout fixture, but do not put its static name table
    # in the ROM. The runtime fills the PNT with one solid background tile.
    _nametable(len(tiles), boot)
    pal = bytes([
        0x00, 0x24, 0x09, 0x00, 0x0C, 0x15, 0x3F, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ])
    banners = banner_rows()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stage_rom.h").write_text(
        "/* gerado por luta_mugen_gen_stage_hud.py a partir de res/stage/arena_tecnica.png */\n"
        "#ifndef STAGE_ROM_H\n#define STAGE_ROM_H\n"
        f"#define STAGE_TILE_BASE {STAGE_TILE_BASE}u\n"
        f"#define STAGE_TILE_COUNT {len(tiles)}u\n"
        "#define OFF_SKY 0u\n#define OFF_FLOOR 1u\n#define OFF_HORIZON 2u\n"
        "#define OFF_BAR_ON 3u\n#define OFF_BAR_OFF 4u\n"
        "#define OFF_DIGIT 5u\n#define OFF_LETTER 15u\n"
        f"#define OFF_LETTER_N (OFF_LETTER + {LETTERS.index('N')}u)\n"
        f"#define OFF_LETTER_I (OFF_LETTER + {LETTERS.index('I')}u)\n"
        f"#define OFF_LETTER_W (OFF_LETTER + {LETTERS.index('W')}u)\n"
        "#define HUD_CELLS 25u\n"
        "extern const unsigned char stage_palette[16];\n"
        f"extern const unsigned char stage_tiles[{len(encoded)}];\n"
        "extern const unsigned char hud_boot[25];\n"
        "extern const unsigned char hud_banner[5][5];\n"
        "#endif\n",
        encoding="utf-8")
    banner_body = ",\n".join(
        "    {" + ", ".join(str(v) for v in row) + "}" for row in banners)
    (out_dir / "stage_data.inc").write_text(
        "/* gerado por luta_mugen_gen_stage_hud.py; incluído só por stage.c */\n"
        + _c_bytes("stage_palette", pal) + "\n"
        + _c_bytes("stage_tiles", encoded) + "\n"
        + _c_bytes("hud_boot", bytes(boot)) + "\n"
        + "const unsigned char hud_banner[5][5] = {\n" + banner_body + "\n};\n",
        encoding="utf-8")
    cases = []
    for i, (x, y) in enumerate(CELLS):
        cases.append(
            f"    case {i}: SMS_setTileatXY({x}, {y}, tile); break;")
    words = ", ".join(f"0x{STAGE_TILE_BASE + i:04X}" for i in range(len(tiles)))
    (out_dir / "hud_put.inc").write_text(
        "/* gerado por luta_mugen_gen_stage_hud.py; coordenadas literais para o gate da PNT.\n"
        " * O índice vai para a name table como palavra pronta. Somar 256 a um\n"
        " * byte virava `inc d` no SDCC e, com D igual ao índice da célula, o\n"
        " * bit 8 caía nas células ímpares. */\n"
        f"static const unsigned int hud_tile_word[{len(tiles)}] = {{ {words} }};\n"
        "static void hud_put_cell(unsigned char i, unsigned char off) {\n"
        "    unsigned int tile = hud_tile_word[off];\n"
        "    switch (i) {\n"
        + "\n".join(cases) + "\n"
        "    default: break;\n"
        "    }\n"
        "}\n",
        encoding="utf-8")


def _load_tiles(path: Path) -> list[list[list[int]]]:
    img = read_indexed_png(str(path))
    if (img["w"], img["h"]) != (64, 32):
        raise SystemExit(f"{path} é {img['w']}×{img['h']}, esperado 64×32")
    pal = [tuple(c) for c in img["palette"][:7]]
    if pal != PALETTE_RGB[:7]:
        raise SystemExit(f"paleta do tileset divergiu: {pal}")
    n = N_BASE + 10 + len(LETTERS)
    return [_tile_from_sheet(img["pixels"], i) for i in range(n)]


def _check_planta(tiles: list[list[list[int]]]) -> None:
    img = read_indexed_png(str(PLANTA))
    if (img["w"], img["h"]) != (256, 192):
        raise SystemExit(f"planta {img['w']}×{img['h']}")
    want = _planta_pixels(tiles, boot_offsets())
    if img["pixels"] != want:
        raise SystemExit("planta_arena.png divergiu da name table de boot")


def _write_pngs() -> None:
    tiles = authored_tiles()
    w, h, rows = _sheet_pixels(tiles)
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    write_indexed_png(str(SHEET), w, h, PALETTE_RGB, rows, trns=(0,))
    planta = _planta_pixels(tiles, boot_offsets())
    write_indexed_png(str(PLANTA), 256, 192, PALETTE_RGB, planta, trns=(0,))
    for p in (SHEET, PLANTA):
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        print(f"{digest}  {p.relative_to(LUTA)}  {p.stat().st_size}")


def main() -> int:
    global LUTA, SHEET, PLANTA
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    ap.add_argument("--write-png", action="store_true")
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--check-planta", action="store_true")
    args = ap.parse_args()
    LUTA = args.project.resolve()
    SHEET = LUTA / "res" / "stage" / "arena_tecnica.png"
    PLANTA = LUTA / "res" / "stage" / "planta_arena.png"
    if args.write_png:
        _write_pngs()
    if args.out_dir:
        tiles = _load_tiles(SHEET)
        if args.check_planta:
            _check_planta(tiles)
        _emit(args.out_dir, tiles)
        print(f"[OK] stage_rom {len(tiles)} tiles -> {args.out_dir}")
    if not args.write_png and not args.out_dir:
        ap.error("informe --write-png e/ou --out-dir")
    return 0


if __name__ == "__main__":
    main()
