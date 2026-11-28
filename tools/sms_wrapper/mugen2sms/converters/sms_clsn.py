"""Caixas Clsn MUGEN -> tabelas de int16 por frame (colisao em software Z80, sem custo de VDP).

Coordenadas MUGEN permanecem cruas (x relativo ao eixo, y positivo para cima);
a conversao para pixels de tela e do runtime (Plano 2).
"""
from __future__ import annotations

CLSN_SENTINEL = -32767
# The runtime indexes int16 words with a byte. Each frame has two section
# terminators and uses four words per box across both sections.
MAX_CLSN_BOXES = (256 - 2) // 4


def to_clsn_tables(anims: dict) -> dict[int, list[tuple[list[int], list[int]]]]:
    """{anim: [(hit_flats, hurt_flats) por frame]} — cada lista em quádruplas x1,y1,x2,y2."""
    out: dict[int, list[tuple[list[int], list[int]]]] = {}
    for n, action in anims.items():
        frames = []
        for index, fr in enumerate(action.frames):
            count = len(fr.clsn1) + len(fr.clsn2)
            if count > MAX_CLSN_BOXES:
                raise ValueError(
                    f"anim {n}, frame {index}: {count} CLSN boxes exceed "
                    f"the byte cursor limit of {MAX_CLSN_BOXES}"
                )
            hit = [v for box in fr.clsn1 for v in box]
            hurt = [v for box in fr.clsn2 for v in box]
            for v in hit + hurt:
                if not (-32768 <= v <= 32767):
                    raise ValueError(f"anim {n}, frame {index}: caixa fora de int16 ({v})")
                if v == CLSN_SENTINEL:
                    raise ValueError(f"anim {n}, frame {index}: coordinate {v} is the CLSN terminator")
            frames.append((hit, hurt))
        out[n] = frames
    return out
