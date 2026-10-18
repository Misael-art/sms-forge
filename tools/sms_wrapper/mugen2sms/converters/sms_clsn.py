"""Caixas Clsn MUGEN -> tabelas de int16 por frame (colisao em software Z80, sem custo de VDP).

Coordenadas MUGEN permanecem cruas (x relativo ao eixo, y positivo para cima);
a conversao para pixels de tela e do runtime (Plano 2).
"""
from __future__ import annotations


def to_clsn_tables(anims: dict) -> dict[int, list[tuple[list[int], list[int]]]]:
    """{anim: [(hit_flats, hurt_flats) por frame]} — cada lista em quádruplas x1,y1,x2,y2."""
    out: dict[int, list[tuple[list[int], list[int]]]] = {}
    for n, action in anims.items():
        frames = []
        for fr in action.frames:
            hit = [v for box in fr.clsn1 for v in box]
            hurt = [v for box in fr.clsn2 for v in box]
            for v in hit + hurt:
                if not (-32768 <= v <= 32767):
                    raise ValueError(f"anim {n}: caixa fora de int16 ({v})")
            frames.append((hit, hurt))
        out[n] = frames
    return out
