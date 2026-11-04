"""Registra o assentamento corrigido e a subida da mão.

Não desenha anatomia. A autoria está nos JPEG locais conferidos por SHA-256.
Três ou quatro pixels soltos no canto da borda, fora do
corpo, voltam à cor do canto antes da chave. O corpo usa a mesma razão
da guarda e não é esmagado.
"""

from __future__ import annotations

from PIL import Image

import register_taunt_cycle_v2 as base


def clean_border(image: Image.Image) -> list[list[int]]:
    pixels = image.load()
    width, height = image.size
    corner = pixels[4, 4]
    limit = base.CORNER_LIMIT * base.CORNER_LIMIT

    def background(x: int, y: int) -> bool:
        red, green, blue = pixels[x, y]
        return ((red - corner[0]) ** 2 + (green - corner[1]) ** 2
                + (blue - corner[2]) ** 2) <= limit

    specks = []
    for y in range(height):
        for x in range(width):
            if x < 8 or y < 8 or x >= width - 8 or y >= height - 8:
                if not background(x, y):
                    specks.append((x, y))
    if len(specks) > 8:
        raise SystemExit(f"borda com figura de verdade: {len(specks)}")
    for x, y in specks:
        pixels[x, y] = corner
    return [[x, y] for x, y in specks]


if __name__ == "__main__":
    base.replay(3, clean_border)
