#!/usr/bin/env python3
"""Compose the standard, readable layout around generated concept-sheet art.

This utility adds typography, the relative height ruler, and metadata cards.
It does not draw, recolor, crop, or retouch the character illustration.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CANVAS = (2400, 1440)
BACKGROUND = (247, 244, 237)
INK = (5, 12, 67)
MUTED = (88, 105, 119)
CARD = (252, 250, 246)
BORDER = (217, 213, 204)
FONT_DIR = Path("/usr/share/fonts/liberation")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / name), size=size)


def draw_card(draw: ImageDraw.ImageDraw, box, title: str, body: str,
              title_font, body_font, chips=()) -> None:
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=15, fill=CARD, outline=BORDER, width=2)
    draw.text((x0 + 17, y0 + 10), title.upper(), fill=INK, font=title_font)
    lines = body.split("\n")
    line_y = y0 + 40
    for line in lines:
        draw.text((x0 + 18, line_y), line, fill=(62, 68, 78), font=body_font)
        line_y += 24
    if chips:
        chip_y = y1 - 25
        chip_x = x0 + 18
        for color in chips:
            draw.rounded_rectangle((chip_x, chip_y, chip_x + 37, chip_y + 14),
                                   radius=3, fill=color, outline=(86, 86, 86), width=1)
            chip_x += 48


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--art", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    source = Image.open(args.art).convert("RGB")
    canvas = Image.new("RGB", CANVAS, BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    title_font = font("LiberationSans-Bold.ttf", 40)
    subtitle_font = font("LiberationSans-Regular.ttf", 23)
    panel_font = font("LiberationSans-Bold.ttf", 18)
    card_title_font = font("LiberationSans-Bold.ttf", 17)
    card_body_font = font("LiberationSans-Regular.ttf", 16)

    draw.text((56, 22), metadata["character"], fill=INK, font=title_font)
    draw.text((58, 68),
              f"MODEL SHEET {metadata['sequence']:02d}  ·  {metadata['style_id']}",
              fill=(49, 103, 134), font=subtitle_font)
    draw.text((58, 98),
              f"{metadata['franchise']}  ·  {metadata['platform_era']}",
              fill=MUTED, font=subtitle_font)

    badge = metadata.get("status_label", "CANDIDATE")
    draw.rounded_rectangle((2038, 35, 2337, 93), radius=12,
                           fill=(238, 234, 225), outline=BORDER, width=2)
    badge_w = draw.textbbox((0, 0), badge, font=panel_font)[2]
    draw.text((2187 - badge_w // 2, 52), badge, fill=INK, font=panel_font)

    # Preserve the generated art intact; the standard title/footer are overlays.
    art_x, art_y = 124, 128
    if source.width > 2000 or source.height > 800:
        scale = min(2000 / source.width, 800 / source.height)
        source = source.resize((round(source.width * scale), round(source.height * scale)),
                               Image.Resampling.LANCZOS)
    canvas.paste(source, (art_x, art_y))

    # Relative ruler: 0–7.5 H, aligned to the orthographic character baseline.
    ruler_top, ruler_bottom, ruler_x = 194, 844, 99
    draw.line((ruler_x, ruler_top, ruler_x, ruler_bottom), fill=(95, 111, 123), width=3)
    for unit in range(8):
        y = round(ruler_bottom - (ruler_bottom - ruler_top) * unit / 7.5)
        tick = 15 if unit in (0, 7) else 11
        draw.line((ruler_x - tick, y, ruler_x + tick, y), fill=(95, 111, 123), width=2)
        draw.text((33, y - 13), str(unit), fill=INK, font=panel_font)
    draw.line((ruler_x - 19, ruler_top, ruler_x + 19, ruler_top), fill=INK, width=3)
    draw.text((24, ruler_top - 30), "7.5H", fill=INK, font=panel_font)
    draw.line((136, ruler_bottom, 1090, ruler_bottom), fill=(192, 194, 191), width=2)
    draw.text((137, ruler_bottom + 4), "COMMON BASELINE GUIDE",
              fill=MUTED, font=font("LiberationSans-Bold.ttf", 15))

    grid_x = [50, 822, 1594]
    grid_y = [900, 1068, 1236]
    card_w, card_h = 756, 148
    cards = metadata["cards"]
    if len(cards) != 9:
        raise ValueError("The standard model sheet layout requires exactly 9 metadata cards")
    for index, card in enumerate(cards):
        row, col = divmod(index, 3)
        draw_card(draw,
                  (grid_x[col], grid_y[row], grid_x[col] + card_w, grid_y[row] + card_h),
                  card["title"], card["body"], card_title_font, card_body_font,
                  card.get("chips", ()))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, format="PNG", optimize=True)
    print(f"wrote {args.output} ({CANVAS[0]}x{CANVAS[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
