"""Tradução candidata da conversa para tiles de 8×8.

Maioria de índices por bloco, sem suavização e sem dither. Os glifos são
um conjunto candidato de 1 tile por caractere. Não há ROM, então isto não
prova texto de runtime. A segunda linha é prova de acento e comprimento,
não fala canônica nova.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "preview"

PALETTE = [
    (0, 0, 85),
    (0, 0, 0),
    (255, 255, 255),
    (170, 170, 0),
    (0, 170, 255),
    (0, 85, 170),
    (170, 170, 170),
    (85, 85, 85),
    (255, 170, 85),
    (170, 85, 85),
    (170, 0, 85),
    (85, 0, 0),
    (0, 85, 85),
    (85, 85, 170),
    (255, 170, 0),
    (255, 255, 170),
]
BACKDROP, INK, PAPER_TEXT, GOLD = 0, 1, 2, 3
COLUMN, FLOOR, PAPER = 12, 13, 15

PORTRAIT = (8, 8, 96, 120)
NAME_XY = (104, 8)
SPEECH = (8, 128, 248, 184)
STAGE = (104, 32, 248, 120)
LINE_1 = "Ainda falta uma peça."
LINE_2 = "Não fecha o indício."
NAME = "DR. SOCIAL"

# 8 linhas, bit 7 à esquerda. Acentos na linha 0, cedilha na linha 7.
GLYPHS = {
    " ": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
    ".": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x18],
    "A": [0x00, 0x18, 0x24, 0x42, 0x7E, 0x42, 0x42, 0x00],
    "C": [0x00, 0x3C, 0x42, 0x40, 0x40, 0x42, 0x3C, 0x00],
    "D": [0x00, 0x78, 0x44, 0x42, 0x42, 0x44, 0x78, 0x00],
    "I": [0x00, 0x3C, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00],
    "L": [0x00, 0x40, 0x40, 0x40, 0x40, 0x40, 0x7E, 0x00],
    "N": [0x00, 0x42, 0x62, 0x52, 0x4A, 0x46, 0x42, 0x00],
    "O": [0x00, 0x3C, 0x42, 0x42, 0x42, 0x42, 0x3C, 0x00],
    "R": [0x00, 0x7C, 0x42, 0x42, 0x7C, 0x44, 0x42, 0x00],
    "S": [0x00, 0x3C, 0x42, 0x30, 0x0C, 0x42, 0x3C, 0x00],
    "a": [0x00, 0x00, 0x38, 0x04, 0x3C, 0x44, 0x3C, 0x00],
    "c": [0x00, 0x00, 0x3C, 0x40, 0x40, 0x40, 0x3C, 0x00],
    "d": [0x00, 0x04, 0x04, 0x3C, 0x44, 0x44, 0x3C, 0x00],
    "e": [0x00, 0x00, 0x38, 0x44, 0x7C, 0x40, 0x3C, 0x00],
    "f": [0x00, 0x0C, 0x10, 0x38, 0x10, 0x10, 0x10, 0x00],
    "h": [0x00, 0x40, 0x40, 0x78, 0x44, 0x44, 0x44, 0x00],
    "i": [0x00, 0x10, 0x00, 0x30, 0x10, 0x10, 0x38, 0x00],
    "l": [0x00, 0x30, 0x10, 0x10, 0x10, 0x10, 0x38, 0x00],
    "m": [0x00, 0x00, 0x68, 0x54, 0x54, 0x54, 0x54, 0x00],
    "n": [0x00, 0x00, 0x58, 0x64, 0x44, 0x44, 0x44, 0x00],
    "o": [0x00, 0x00, 0x38, 0x44, 0x44, 0x44, 0x38, 0x00],
    "p": [0x00, 0x00, 0x78, 0x44, 0x78, 0x40, 0x40, 0x00],
    "t": [0x00, 0x10, 0x38, 0x10, 0x10, 0x10, 0x0C, 0x00],
    "u": [0x00, 0x00, 0x44, 0x44, 0x44, 0x44, 0x3C, 0x00],
    "ç": [0x00, 0x00, 0x3C, 0x40, 0x40, 0x3C, 0x10, 0x20],
    "ã": [0x28, 0x10, 0x38, 0x04, 0x3C, 0x44, 0x3C, 0x00],
    "í": [0x10, 0x08, 0x00, 0x30, 0x10, 0x10, 0x38, 0x00],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nearest_index(rgb: tuple[int, int, int]) -> int:
    best_i, best_d = 0, 1 << 30
    for index, color in enumerate(PALETTE):
        distance = (rgb[0] - color[0]) ** 2 + (rgb[1] - color[1]) ** 2 + (rgb[2] - color[2]) ** 2
        if distance < best_d:
            best_i, best_d = index, distance
    return best_i


def quantize(image: Image.Image) -> Image.Image:
    rgb = image.convert("RGB")
    out = Image.new("P", rgb.size)
    out.putpalette([channel for color in PALETTE for channel in color])
    src, dst = rgb.load(), out.load()
    for y in range(rgb.size[1]):
        for x in range(rgb.size[0]):
            dst[x, y] = nearest_index(src[x, y])
    return out


def majority_fit(indexed: Image.Image, box: tuple[int, int, int, int]) -> tuple[Image.Image, tuple[int, int, int, int]]:
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    sw, sh = indexed.size
    scale = min(bw / sw, bh / sh)
    dw, dh = max(1, round(sw * scale)), max(1, round(sh * scale))
    fitted = Image.new("P", (dw, dh))
    fitted.putpalette(indexed.getpalette())
    src, dst = indexed.load(), fitted.load()
    for y in range(dh):
        sy0 = y * sh // dh
        sy1 = max(sy0 + 1, (y + 1) * sh // dh)
        for x in range(dw):
            sx0 = x * sw // dw
            sx1 = max(sx0 + 1, (x + 1) * sw // dw)
            counts: Counter[int] = Counter()
            for sy in range(sy0, sy1):
                for sx in range(sx0, sx1):
                    counts[src[sx, sy]] += 1
            dst[x, y] = counts.most_common(1)[0][0]
    origin = (x0 + (bw - dw) // 2, y0 + (bh - dh) // 2)
    return fitted, origin


def blit(image: Image.Image, origin: tuple[int, int], text: str, ink: int, paper: int) -> None:
    pixels = image.load()
    x, y = origin
    for char in text:
        rows = GLYPHS[char]
        for row, bits in enumerate(rows):
            for col in range(8):
                pixels[x + col, y + row] = ink if bits & (1 << (7 - col)) else paper
        x += 8


def paint(source: Path, stem: str) -> dict:
    crop_rgb = Image.open(source).convert("RGB")
    indexed = quantize(crop_rgb)
    plate = Image.new("P", (256, 192))
    plate.putpalette([channel for color in PALETTE for channel in color])
    plate.paste(BACKDROP, (0, 0, 256, 192))
    draw_px = plate.load()
    for y in range(STAGE[1], STAGE[3]):
        for x in range(STAGE[0], STAGE[2]):
            draw_px[x, y] = COLUMN if 160 <= x < 168 or 208 <= x < 216 else BACKDROP
            if y >= STAGE[3] - 16:
                draw_px[x, y] = FLOOR
    for y in range(SPEECH[1], SPEECH[3]):
        for x in range(SPEECH[0], SPEECH[2]):
            draw_px[x, y] = INK
    fitted, origin = majority_fit(indexed, PORTRAIT)
    plate.paste(fitted, origin)
    blit(plate, NAME_XY, NAME, GOLD, BACKDROP)
    blit(plate, (16, 136), LINE_1, PAPER_TEXT, INK)
    blit(plate, (16, 152), LINE_2, PAPER_TEXT, INK)

    tiles: dict[bytes, int] = {}
    nametable = []
    px = plate.load()
    for ty in range(24):
        row = []
        for tx in range(32):
            block = bytes(px[tx * 8 + x, ty * 8 + y] for y in range(8) for x in range(8))
            row.append(tiles.setdefault(block, len(tiles)))
        nametable.append(row)

    native = OUT / f"{stem}_256.png"
    zoom = OUT / f"{stem}_4x.png"
    plate.save(native)
    plate.resize((1024, 768), Image.Resampling.NEAREST).save(zoom)
    record = {
        "schema": "conversa07_sms_tile_candidate_v1",
        "status": "candidato_de_tiles",
        "not_an_approval": True,
        "not_runtime_text": "Glifos desenhados nesta receita, 1 tile por caractere. Nenhuma ROM carrega esta fonte.",
        "line_2_role": "Prova de acento e comprimento. Não é fala canônica além do rascunho da primeira linha.",
        "source": str(source.relative_to(ROOT)),
        "source_sha256": sha256(source),
        "reduction": "quantizar ao índice mais próximo, depois maioria do bloco. Sem Lanczos, sem dither.",
        "palette_rgb": PALETTE,
        "palette_roles": {
            "0": "fundo azul",
            "1": "caixa de fala",
            "2": "texto e camisa",
            "3": "nome e latão",
            "4": "casaco",
            "12": "coluna do palco-sonda",
            "13": "chão do palco-sonda",
            "15": "papel do retrato",
        },
        "stage": "Colunas e chão são sonda de contraste, não cenário de Kenseiden.",
        "rects_px_half_open": {
            "portrait": list(PORTRAIT),
            "stage": list(STAGE),
            "speech": list(SPEECH),
        },
        "text": {"name": NAME, "line_1": LINE_1, "line_2": LINE_2},
        "glyph_count": len({char for char in NAME + LINE_1 + LINE_2}),
        "unique_tiles": len(tiles),
        "vram_pattern_bytes_if_4bpp": len(tiles) * 32,
        "portrait_paste": {"origin": list(origin), "size": list(fitted.size)},
        "plates_sha256": {"native": sha256(native), "nearest_4x": sha256(zoom)},
    }
    (OUT / f"{stem}_v1.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(stem, "tiles", len(tiles), "bytes", len(tiles) * 32, record["plates_sha256"]["native"])
    return record


def main() -> None:
    missing = [char for char in NAME + LINE_1 + LINE_2 if char not in GLYPHS]
    if missing:
        raise SystemExit(f"glifos faltando: {sorted(set(missing))}")
    paint(ROOT / "logical" / "bust_neutral_crop_v1.png", "conversa07_sms_attention")
    paint(ROOT / "logical" / "conversa07_layout_speech_candidate_crop.png", "conversa07_sms_speech")


if __name__ == "__main__":
    main()
