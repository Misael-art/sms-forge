"""Placa candidata de versus, distinta da conversa da cena 07.

Reusa o busto de atenção já reduzido pelo mesmo critério: índice mais
próximo, depois maioria do bloco, sem Lanczos e sem dither. O lado direito
é um vão reservado, sem desenhar outro lutador. Os glifos são os mesmos
tiles de 8×8. Não há ROM, então o texto não é runtime.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

import compose_conversa07_sms_v1 as sms

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "preview"

sms.GLYPHS["V"] = [0x00, 0x42, 0x42, 0x42, 0x42, 0x24, 0x18, 0x00]

# Tiles: retrato x 1–13, y 3–20. Vão do rival x 18–30, mesma altura.
LEFT = (8, 24, 112, 168)
RIGHT = (144, 24, 248, 168)
NAME = "DR. SOCIAL"
SLOT = "RIVAL"
MARK = "VS"
NAME_Y = 176
MARK_XY = (120, 88)


def frame(image: Image.Image, box: tuple[int, int, int, int], ink: int, fill: int) -> None:
    x0, y0, x1, y1 = box
    pixels = image.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            edge = x < x0 + 8 or x >= x1 - 8 or y < y0 + 8 or y >= y1 - 8
            pixels[x, y] = ink if edge else fill


def crop_figure(source: Path, dest: Path, pad: int = 12) -> None:
    """Recorte no primeiro pixel que sai da cor do canto. PNG, sem reencode do JPEG."""
    image = Image.open(source).convert("RGB")
    pixels = image.load()
    width, height = image.size
    key = pixels[0, 0]

    def outside(x: int, y: int) -> bool:
        red, green, blue = pixels[x, y]
        return abs(red - key[0]) + abs(green - key[1]) + abs(blue - key[2]) > 48

    min_x, min_y, max_x, max_y = width, height, 0, 0
    for y in range(height):
        for x in range(width):
            if outside(x, y):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    if max_x < min_x:
        raise SystemExit(f"sem figura em {source.name}")
    box = (
        max(0, min_x - pad),
        max(0, min_y - pad),
        min(width, max_x + 1 + pad),
        min(height, max_y + 1 + pad),
    )
    image.crop(box).save(dest)


def paint(source: Path, stem: str, role: str) -> dict:
    indexed = sms.quantize(Image.open(source).convert("RGB"))
    plate = Image.new("P", (256, 192))
    plate.putpalette([channel for color in sms.PALETTE for channel in color])
    plate.paste(sms.BACKDROP, (0, 0, 256, 192))
    pixels = plate.load()
    for y in range(LEFT[1], LEFT[3]):
        for x in range(LEFT[0], LEFT[2]):
            pixels[x, y] = sms.PAPER
    frame(plate, RIGHT, sms.GOLD, sms.BACKDROP)
    fitted, origin = sms.majority_fit(indexed, LEFT)
    plate.paste(fitted, origin)
    sms.blit(plate, (8, NAME_Y), NAME, sms.GOLD, sms.BACKDROP)
    sms.blit(plate, (144, NAME_Y), SLOT, sms.GOLD, sms.BACKDROP)
    sms.blit(plate, MARK_XY, MARK, sms.PAPER_TEXT, sms.BACKDROP)

    tiles: dict[bytes, int] = {}
    px = plate.load()
    for ty in range(24):
        for tx in range(32):
            block = bytes(px[tx * 8 + x, ty * 8 + y] for y in range(8) for x in range(8))
            tiles.setdefault(block, len(tiles))

    native = OUT / f"{stem}_256.png"
    zoom = OUT / f"{stem}_4x.png"
    plate.save(native)
    plate.resize((1024, 768), Image.Resampling.NEAREST).save(zoom)
    record = {
        "schema": "versus_sms_tile_candidate_v1",
        "role": role,
        "status": "candidato_de_layout",
        "not_an_approval": True,
        "not_scene_07": "Sem caixa de fala e sem palco. O vão direito não é um lutador.",
        "not_runtime_text": "Glifos desta receita. Nenhuma ROM carrega esta fonte.",
        "source": str(source.relative_to(ROOT)),
        "source_sha256": sms.sha256(source),
        "reduction": "quantizar ao índice mais próximo, depois maioria do bloco. Sem Lanczos, sem dither.",
        "rects_px_half_open": {"social": list(LEFT), "reserved_opponent": list(RIGHT)},
        "text": {"name": NAME, "slot": SLOT, "mark": MARK},
        "name_capacity_glyphs": (LEFT[2] - LEFT[0]) // 8,
        "unique_tiles": len(tiles),
        "vram_pattern_bytes_if_4bpp": len(tiles) * 32,
        "portrait_paste": {"origin": list(origin), "size": list(fitted.size)},
        "plates_sha256": {"native": sms.sha256(native), "nearest_4x": sms.sha256(zoom)},
    }
    (OUT / f"{stem}_v1.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(stem, "tiles", len(tiles), "bytes", len(tiles) * 32, record["plates_sha256"]["native"])
    return record


def main() -> None:
    text = NAME + SLOT + MARK
    missing = [char for char in text if char not in sms.GLYPHS]
    if missing:
        raise SystemExit(f"glifos faltando: {sorted(set(missing))}")
    paint(ROOT / "logical" / "bust_neutral_crop_v1.png", "versus_neutral_sms", "versus_neutral")
    win = ROOT / "originals" / "bust_versus_win_attempt1.jpg"
    loss = ROOT / "originals" / "bust_versus_loss_attempt1.jpg"
    if win.exists():
        crop_figure(win, ROOT / "logical" / "bust_versus_win_crop_v1.png")
        paint(ROOT / "logical" / "bust_versus_win_crop_v1.png", "versus_win_sms", "versus_win")
    if loss.exists():
        crop_figure(loss, ROOT / "logical" / "bust_versus_loss_crop_v1.png")
        paint(ROOT / "logical" / "bust_versus_loss_crop_v1.png", "versus_loss_sms", "versus_loss")


if __name__ == "__main__":
    main()
