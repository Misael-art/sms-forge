"""Parser de SFF v1 (sprites PCX 8-bit) e paletas .act.

SFF v2 e detectado e rejeitado com erro explicito (planejado para etapa posterior).
Layout v1: header 512 B; subheaders de 32 B encadeados; dados PCX com paleta opcional no fim.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from PIL import Image

SIG = b"ElecbyteSpr\0"


class SffError(ValueError):
    pass


@dataclass
class Sprite:
    group: int
    image: int
    axis_x: int
    axis_y: int
    width: int
    height: int
    pixels: bytes              # indices 8-bit, row-major; 0 = transparente
    palette: list[tuple[int, int, int]]  # 256 cores (propria ou herdada)
    same_palette: bool
    linked_from: int | None    # indice do sprite de origem, se era link
    index: int


def version(data: bytes) -> tuple[int, int, int, int]:
    if not data.startswith(SIG):
        raise SffError("assinatura ElecbyteSpr ausente")
    return (data[15], data[14], data[13], data[12])


def read_act(data: bytes) -> list[tuple[int, int, int]]:
    """ACT do MUGEN: 256 cores RGB gravadas em ordem invertida (cor 0 no fim)."""
    if len(data) < 768:
        raise SffError(f"ACT com {len(data)} bytes (esperado 768)")
    cols = [tuple(data[i * 3 : i * 3 + 3]) for i in range(256)]
    return list(reversed(cols))


def _decode_pcx(blob: bytes) -> tuple[int, int, bytes, list | None]:
    # Header PCX: 128 B; so aceitamos 8 bpp, 1 plano (o que o MUGEN gera)
    if len(blob) < 128:
        raise SffError("PCX truncado")
    bpp, xmin, ymin, xmax, ymax = blob[3], *struct.unpack_from("<4H", blob, 4)
    planes, bpl = blob[65], struct.unpack_from("<H", blob, 66)[0]
    if bpp != 8 or planes != 1:
        raise SffError(f"PCX {bpp}bpp/{planes} planos nao suportado")
    w, h = xmax - xmin + 1, ymax - ymin + 1
    out, pos, data = bytearray(), 128, blob
    total = bpl * h
    while len(out) < total and pos < len(data):
        b = data[pos]
        pos += 1
        if b >= 0xC0:
            n = b & 0x3F
            v = data[pos] if pos < len(data) else 0
            pos += 1
            out.extend(bytes([v]) * n)
        else:
            out.append(b)
    out = out[:total].ljust(total, b"\0")
    pix = b"".join(bytes(out[r * bpl : r * bpl + w]) for r in range(h))
    pal = None
    if len(data) >= 769 and data[-769] == 0x0C:
        p = data[-768:]
        pal = [tuple(p[i * 3 : i * 3 + 3]) for i in range(256)]
    return w, h, pix, pal


def parse(data: bytes) -> tuple[list[Sprite], list[str]]:
    ver = version(data)
    if ver[0] != 1:
        raise SffError(f"SFF v{'.'.join(map(str, ver))} ainda nao suportado (so v1)")
    n_images, first = struct.unpack_from("<II", data, 20)
    warnings: list[str] = []
    sprites: list[Sprite] = []
    by_index: dict[int, Sprite] = {}
    pos, prev_pal = first, [(0, 0, 0)] * 256
    for idx in range(n_images):
        if pos + 32 > len(data):
            warnings.append(f"sprite {idx}: subheader fora do arquivo; leitura interrompida")
            break
        nxt, length, ax, ay, grp, img, link, same = struct.unpack_from("<IIhhHHHB", data, pos)
        body = data[pos + 32 : pos + 32 + length]
        if length == 0:
            src = by_index.get(link)
            if src is None:
                warnings.append(f"sprite {grp},{img}: link para indice {link} inexistente")
                pos = nxt
                continue
            sprites.append(Sprite(grp, img, ax, ay, src.width, src.height, src.pixels,
                                  src.palette, src.same_palette, link, idx))
        else:
            try:
                w, h, pix, pal = _decode_pcx(body)
            except SffError as e:
                warnings.append(f"sprite {grp},{img}: {e}")
                pos = nxt
                continue
            use_prev = bool(same) or pal is None
            palette = prev_pal if use_prev else pal
            prev_pal = palette
            sprites.append(Sprite(grp, img, ax, ay, w, h, pix, palette, bool(same), None, idx))
        by_index[idx] = sprites[-1]
        if nxt == 0:
            break
        pos = nxt
    return sprites, warnings


def to_image(s: Sprite, palette=None) -> Image.Image:
    im = Image.frombytes("P", (s.width, s.height), s.pixels)
    pal = palette or s.palette
    im.putpalette([c for rgb in pal for c in rgb])
    return im

