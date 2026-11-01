"""Storyboard nativo da cena 10. Layout, não budget e não comando.

O texto usa os glifos já desenhados da conversa, mais os dígitos 1 e 2.
Não há lutador colado, não há quarto de lua e não há ROM.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

import compose_conversa07_sms_v1 as sms

HERE = Path(__file__).resolve().parent
OUT = HERE / "preview" / "cena10_storyboard_v1.png"
NOTE = HERE / "proposals" / "cena10_storyboard_v1.json"

DIGITS = {
    "1": [0x00, 0x18, 0x38, 0x18, 0x18, 0x18, 0x3C, 0x00],
    "2": [0x00, 0x3C, 0x42, 0x04, 0x18, 0x20, 0x7E, 0x00],
}


def blit(image: Image.Image, origin: tuple[int, int], text: str, ink: int, paper: int) -> None:
    glyphs = {**sms.GLYPHS, **DIGITS}
    pixels = image.load()
    x, y = origin
    for char in text:
        for row, bits in enumerate(glyphs[char]):
            for col in range(8):
                pixels[x + col, y + row] = ink if bits & (1 << (7 - col)) else paper
        x += 8


def rect(pixels, box, ink) -> None:
    x0, y0, x1, y1 = box
    for x in range(x0, x1):
        pixels[x, y0] = pixels[x, y1 - 1] = ink
    for y in range(y0, y1):
        pixels[x0, y] = pixels[x1 - 1, y] = ink


def fill(pixels, box, color) -> None:
    x0, y0, x1, y1 = box
    for y in range(y0, y1):
        for x in range(x0, x1):
            pixels[x, y] = color


def circle(pixels, cx, cy, radius, color) -> None:
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                pixels[x, y] = color


def pad(pixels) -> None:
    fill(pixels, (4, 132, 124, 188), 7)
    rect(pixels, (4, 132, 124, 188), 1)
    fill(pixels, (28, 144, 40, 176), 6)
    fill(pixels, (16, 156, 52, 164), 6)
    rect(pixels, (28, 144, 40, 176), 1)
    rect(pixels, (16, 156, 52, 164), 1)
    circle(pixels, 78, 154, 11, 1)
    circle(pixels, 104, 166, 11, 1)
    circle(pixels, 78, 154, 9, 6)
    circle(pixels, 104, 166, 9, 6)


def main() -> None:
    image = Image.new("P", (256, 192))
    image.putpalette([channel for color in sms.PALETTE for channel in color])
    pixels = image.load()
    fill(pixels, (0, 0, 256, 192), sms.BACKDROP)
    fill(pixels, (0, 0, 256, 24), 1)
    blit(image, (48, 4), "comando em definição", sms.GOLD, 1)
    blit(image, (72, 14), "nome pendente", sms.PAPER_TEXT, 1)
    fill(pixels, (8, 32, 248, 124), 0)
    rect(pixels, (8, 32, 248, 124), sms.GOLD)
    fill(pixels, (8, 112, 248, 124), sms.FLOOR)
    pad(pixels)
    # Os números ficam no corpo do botão, sem espelhar.
    blit(image, (74, 150), "1", 1, 6)
    blit(image, (100, 162), "2", 1, 6)
    blit(image, (132, 136), "em definição", sms.GOLD, sms.BACKDROP)
    steps = ((132, 152, 156, 184), (164, 152, 188, 184), (196, 152, 220, 184))
    for index, box in enumerate(steps):
        fill(pixels, box, 7 if index else 3)
        rect(pixels, box, 2 if index else 1)
        if index == 0:
            rect(pixels, (box[0] + 2, box[1] + 2, box[2] - 2, box[3] - 2), 1)
    image.save(OUT, transparency=0, bits=8)
    zoom = image.resize((512, 384), Image.Resampling.NEAREST)
    zoom_path = OUT.with_name("cena10_storyboard_v1_2x.png")
    zoom.save(zoom_path)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    NOTE.write_text(json.dumps({
        "not_a_budget": True,
        "not_a_command": True,
        "not_a_rom": True,
        "file": OUT.name,
        "sha256": digest,
        "native_px": [256, 192],
        "text": ["comando em definição", "nome pendente", "em definição"],
        "control": "direcional à esquerda, botões 1 e 2 à direita, sem Start e sem quarto botão",
        "stage": "vão do lutador e chão; nenhum sprite de luta foi colado",
        "active_step": "primeiro retângulo com contorno duplo, além da cor",
        "proposal": "doc/dr_social_two_button_proposal_v1.json",
    }, indent=2) + "\n")
    print(digest)


if __name__ == "__main__":
    main()
