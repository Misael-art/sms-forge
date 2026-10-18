"""Orcamento do VDP do Master System — todo numero com fonte citada (L001: proibido numero de
outro console virar lei do SMS). Nada aqui vem do Mega Drive."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SmsLimits:
    # 8 sprites por scanline — limite fisico do processador de sprites do VDP SMS
    # (doutrina AGENTS.md; aplicado por audit_sprite_line_sim.py).
    sprites_per_line: int = 8
    # Capacidade da SAT = MAXSPRITES: sdk/devkitSMS-upstream/SMSlib/src/SMSlib_common.c:21
    # `#define MAXSPRITES 64`; SMSlib.h:199 — SMS_addSprite_f retorna -1 quando esgota.
    sat_max: int = 64
    # Name table visivel: 256x192 px / tile 8x8 = 32x24 = 768 tiles (SMSlib.h secao "Tiles").
    tiles_visible_per_frame: int = 768
    # Tile = 8x8 a 4bpp = 32 B: SMSlib.h:130 `SMS_loadTiles(src,tilefrom,size) ... (tilefrom)*32`.
    tile_bytes: int = 32
    # 4bpp = 16 indices por subpaleta; indice 0 transparente nas duas subpaletas
    # (SMSlib.h:131 SMS_load1bppTiles com color0/color1; AGENTS.md "indice 0 e transparente").
    subpalette_colors: int = 15
    # VRAM do VDP = 16 KB (regioes tile/PNT/SAT/CRAM; SMSlib.h TILEtoADDR endereca ate 0x4000*4).
    vram_bytes: int = 16384
    # RAM do Z80 = 8 KB (AGENTS.md; sdk/README.md).
    ram_bytes: int = 8192


def tiles_cover(w: int, h: int) -> int:
    """Tiles 8x8 necessarios para cobrir um retangulo w x h (borda incompleta ocupa tile inteiro)."""
    return math.ceil(w / 8) * math.ceil(h / 8)


def columns(w: int) -> int:
    """Largura em colunas de sprite (cada coluna de 8 px custa 1 entrada da SAT por faixa de Y)."""
    return math.ceil(w / 8)


def sat_entries(w: int, h: int, tall: bool = True) -> int:
    """Entradas de sprite para desenhar a pose inteira.

    Em SPRITEMODE_TALL (SMSlib.h:57) o sprite cobre 8x16, entao cada coluna gasta
    ceil(h/16) entradas; em modo normal cada tile 8x8 e uma entrada.
    """
    return columns(w) * (math.ceil(h / 16) if tall else math.ceil(h / 8))


def _tile_at(sp, tx: int, ty: int) -> bytes:
    """Recorta um tile 8x8 do sprite indexado, completando borda com indice 0 (transparente)."""
    out = bytearray(64)
    for row in range(8):
        y = ty * 8 + row
        if y >= sp.height:
            break
        base = y * sp.width + tx * 8
        chunk = sp.pixels[base:base + 8]
        out[row * 8:row * 8 + len(chunk)] = chunk
    return bytes(out)


def dedup_tiles(sprites) -> tuple[int, int]:
    """(tiles unicos, tiles totais) sobre a grade 8x8 de cada sprite — custo real de VRAM."""
    seen: set[bytes] = set()
    total = 0
    for sp in sprites:
        for ty in range(math.ceil(sp.height / 8)):
            for tx in range(math.ceil(sp.width / 8)):
                total += 1
                seen.add(_tile_at(sp, tx, ty))
    return len(seen), total


def used_colors(sp) -> int:
    """Indices nao-transparentes presentes no sprite (indice 0 = transparente)."""
    return len(set(p for p in sp.pixels if p))
