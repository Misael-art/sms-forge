"""Candidato reversível de layout da conversa, cena 07.

Compõe o busto autoral dentro de retângulos alinhados a tiles de 8 px.
O texto é desenhado aqui, fora dos pixels do retrato. Não quantiza o busto
para a paleta do SMS e não aprova cena, crop nem expressão.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "originals" / "bust_neutral_attempt2.jpg"
FONT_BOLD = Path("/usr/share/fonts/liberation/LiberationSans-Bold.ttf")
FONT_REGULAR = Path("/usr/share/fonts/liberation/LiberationSans-Regular.ttf")
SCREEN = (256, 192)
BACKDROP = (0, 0, 85)
NAME_COLOR = (170, 170, 0)
STAGE_FILL = (0, 85, 85)
TEXT_FILL = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
CROP_DISTANCE = 36

# Retângulos [x0, y0, x1, y1), alinhados a 8.
PORTRAIT = (8, 8, 96, 120)
NAME = (104, 8, 248, 24)
STAGE = (104, 32, 248, 120)
SPEECH = (8, 128, 248, 184)
LINE = "Ainda falta uma peça."


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def content_bbox(image: Image.Image, background: tuple[int, int, int], distance: int) -> tuple[int, int, int, int]:
    pixels = image.load()
    width, height = image.size
    min_x, min_y, max_x, max_y = width, height, 0, 0
    limit = distance * distance
    for y in range(height):
        for x in range(width):
            red, green, blue = pixels[x, y]
            delta = (red - background[0]) ** 2 + (green - background[1]) ** 2 + (blue - background[2]) ** 2
            if delta > limit:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x + 1)
                max_y = max(max_y, y + 1)
    if max_x <= min_x or max_y <= min_y:
        raise SystemExit("recorte vazio")
    return (min_x, min_y, max_x, max_y)


def fit_inside(image: Image.Image, box: tuple[int, int, int, int]) -> tuple[Image.Image, tuple[int, int]]:
    x0, y0, x1, y1 = box
    # 1 px de margem interna para a borda do retângulo não comer o rosto.
    inner_w = (x1 - x0) - 2
    inner_h = (y1 - y0) - 2
    scale = min(inner_w / image.width, inner_h / image.height)
    resized = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    origin = (x0 + 1 + (inner_w - resized.width) // 2, y0 + 1 + (inner_h - resized.height) // 2)
    return resized, origin


def text_size(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    left, top, right, bottom = font.getbbox(text)
    return right - left, bottom - top


def main() -> None:
    source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ORIGINAL
    if not source_path.is_absolute():
        source_path = ROOT / source_path
    line = sys.argv[2] if len(sys.argv) > 2 else LINE
    stem = sys.argv[3] if len(sys.argv) > 3 else "conversa07_layout_candidate"
    crop_path = ROOT / "logical" / f"{stem}_crop.png"
    out_png = ROOT / "preview" / f"{stem}_256.png"
    out_4x = ROOT / "preview" / f"{stem}_4x.png"
    out_json = ROOT / "preview" / f"{stem}_v1.json"
    source = Image.open(source_path).convert("RGB")
    background = source.getpixel((2, 2))
    box = content_bbox(source, background, CROP_DISTANCE)
    crop = source.crop(box)
    crop.save(crop_path)

    plate = Image.new("RGB", SCREEN, BACKDROP)
    fitted, origin = fit_inside(crop, PORTRAIT)
    plate.paste(fitted, origin)

    draw = ImageDraw.Draw(plate)
    draw.rectangle((PORTRAIT[0], PORTRAIT[1], PORTRAIT[2] - 1, PORTRAIT[3] - 1), outline=NAME_COLOR)
    draw.rectangle((STAGE[0], STAGE[1], STAGE[2] - 1, STAGE[3] - 1), fill=STAGE_FILL, outline=NAME_COLOR)
    draw.rectangle((SPEECH[0], SPEECH[1], SPEECH[2] - 1, SPEECH[3] - 1), fill=TEXT_FILL, outline=NAME_COLOR)

    name_font = ImageFont.truetype(str(FONT_BOLD), 11)
    body_font = ImageFont.truetype(str(FONT_REGULAR), 11)
    if "ç" not in line or body_font.getbbox("ç")[2] <= 0:
        raise SystemExit("a fonte não desenha ç")

    name = "DR. SOCIAL"
    name_w, name_h = text_size(name_font, name)
    name_box_w = NAME[2] - NAME[0]
    name_box_h = NAME[3] - NAME[1]
    if name_w > name_box_w - 4 or name_h > name_box_h - 2:
        raise SystemExit(f"nome não cabe: {name_w}x{name_h}")
    name_xy = (NAME[0] + 4, NAME[1] + (name_box_h - name_h) // 2 - 1)
    draw.text(name_xy, name, font=name_font, fill=NAME_COLOR)

    line_w, line_h = text_size(body_font, line)
    speech_w = SPEECH[2] - SPEECH[0]
    speech_h = SPEECH[3] - SPEECH[1]
    if line_w > speech_w - 8 or line_h > speech_h - 8:
        raise SystemExit(f"fala não cabe: {line_w}x{line_h}")
    line_xy = (SPEECH[0] + 6, SPEECH[1] + 6)
    draw.text(line_xy, line, font=body_font, fill=TEXT_COLOR)

    for label, rect in (("nome", (name_xy[0], name_xy[1], name_xy[0] + name_w, name_xy[1] + name_h)),
                        ("fala", (line_xy[0], line_xy[1], line_xy[0] + line_w, line_xy[1] + line_h))):
        if not (rect[2] <= PORTRAIT[0] or rect[0] >= PORTRAIT[2] or rect[3] <= PORTRAIT[1] or rect[1] >= PORTRAIT[3]):
            raise SystemExit(f"{label} invade o retrato")

    plate.save(out_png)
    plate.resize((SCREEN[0] * 4, SCREEN[1] * 4), Image.Resampling.NEAREST).save(out_4x)

    record = {
        "schema": "conversa07_layout_candidate_v1",
        "status": "candidato_reversivel",
        "not_an_approval": True,
        "role": "prova de crop da conversa, cena 07; distinto de versus e de seleção",
        "source_bust": {
            "path": str(source_path.relative_to(ROOT)),
            "sha256": sha256(source_path),
            "size": list(source.size),
            "note": "JPEG recebido do gerador, copiado sem reencode. Não é paleta SMS.",
        },
        "crop": {
            "path": str(crop_path.relative_to(ROOT)),
            "sha256": sha256(crop_path),
            "box_px": list(box),
            "size": list(crop.size),
            "background_rgb": list(background),
            "distance": CROP_DISTANCE,
            "resample_into_window": "LANCZOS, proporção preservada, sem esticar um eixo",
        },
        "screen_px": list(SCREEN),
        "tile_px": 8,
        "rects_px_half_open": {
            "portrait": list(PORTRAIT),
            "name": list(NAME),
            "stage_placeholder": list(STAGE),
            "speech": list(SPEECH),
        },
        "rects_tiles_half_open": {
            "portrait": [PORTRAIT[0] // 8, PORTRAIT[1] // 8, PORTRAIT[2] // 8, PORTRAIT[3] // 8],
            "name": [NAME[0] // 8, NAME[1] // 8, NAME[2] // 8, NAME[3] // 8],
            "stage_placeholder": [STAGE[0] // 8, STAGE[1] // 8, STAGE[2] // 8, STAGE[3] // 8],
            "speech": [SPEECH[0] // 8, SPEECH[1] // 8, SPEECH[2] // 8, SPEECH[3] // 8],
        },
        "colors_rgb": {
            "backdrop": list(BACKDROP),
            "name_and_frame": list(NAME_COLOR),
            "stage_placeholder": list(STAGE_FILL),
            "speech_fill": list(TEXT_FILL),
            "speech_text": list(TEXT_COLOR),
        },
        "cram_candidate_chrome_only": {
            "backdrop_0x10": "RGB 0,0,85",
            "gold_0x2A": "RGB 170,170,0",
            "teal_0x30": "RGB 0,85,85",
            "white_0x3F": "RGB 255,255,255",
            "black_visible_needs_nonzero_bg_index": "RGB 0,0,0",
        },
        "text": {
            "name": name,
            "line": line,
            "font_bold": str(FONT_BOLD),
            "font_regular": str(FONT_REGULAR),
            "drawn_by": "PIL, fora dos pixels do retrato",
            "not_baked_into_bust": True,
        },
        "portrait_paste_origin": list(origin),
        "portrait_fitted_size": list(fitted.size),
        "stage_note": "Retângulo teal é marcador de palco. Não há cenário desenhado.",
        "tile_count": "Não medido. O busto continua ilustração; o cromado não foi convertido em tiles.",
        "plates": {
            "native": str(out_png.relative_to(ROOT)),
            "nearest_4x": str(out_4x.relative_to(ROOT)),
        },
    }
    out_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    record["plates_sha256"] = {"native": sha256(out_png), "nearest_4x": sha256(out_4x)}
    out_json.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(stem, "crop", crop.size, "box", box, "fitted", fitted.size, "at", origin)
    print("name", name_w, name_h, "line", line_w, line_h)
    print(sha256(out_png))


if __name__ == "__main__":
    main()
