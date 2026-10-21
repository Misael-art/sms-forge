#!/usr/bin/env python3
"""gen_storm_sprite_manifest.py — manifesto sprite_scene_manifest_v1 da cena 03.

A cena 03 (tempestade) é a única com sprites: 24 estilhaços cujo movimento é
aritmética determinística da ROM (src/main.c: shards_seed + shards_frame).
Nada aqui é estimativa: os três arrays e a regra de wrap são relidos do C e
reproduzidos byte a byte; o --self-check trava essa correspondência.

Período: v0 ∈ {1,2,3}; do y=0 a cada passo y += v e y>=192 ⇒ y=0. O ciclo de um
estilhaço tem então ceil(192/v) frames = 192, 96, 64. LCM(192,96,64) = 192 ⇒
192 frames cobrem TODAS as fases simultâneas. Varremos as 192 e publicamos a
pior (maior contagem por scanline), que é o caso que o gate precisa reprovar.

Uso:
  gen_storm_sprite_manifest.py --out doc/scene_manifest_storm.json
  gen_storm_sprite_manifest.py --self-check
"""
import argparse
import json
import sys

SHARDS = 24
SCREEN_H = 192
SPRITE_H = 8            # modo 8x8: a ROM nunca chama SMS_use8x16Sprites
TILE = 5                # T_SHARD (src/main.c:275)


def seed():
    """shards_seed(): x0 = i*53+7, y0 = i*29+3, v0 = 1 + (i%3) — byte a byte do C."""
    x = [(i * 53 + 7) & 0xFF for i in range(SHARDS)]
    y = [(i * 29 + 3) & 0xFF for i in range(SHARDS)]
    v = [1 + (i % 3) for i in range(SHARDS)]
    return x, y, v


def frame_positions():
    """Gera as 192 frames do ciclo completo como listas (x, y) por estilhaço."""
    x, y, v = seed()
    out = []
    for _ in range(192):
        out.append([(x[i], y[i]) for i in range(SHARDS)])
        for i in range(SHARDS):
            ny = (y[i] + v[i]) & 0xFF           # unsigned char: soma em 8 bits
            if ny >= SCREEN_H:
                ny = 0
                x[i] = (x[i] + 19 + i) & 0xFF   # x anda só no wrap
            y[i] = ny
    return out


def peak_on_line(positions):
    """Pico de entradas por scanline e a linha exata (a SAT conta por ordem)."""
    count = [0] * SCREEN_H
    for _, ypos in positions:
        for line in range(ypos, min(ypos + SPRITE_H, SCREEN_H)):
            count[line] += 1
    peak = max(count)
    return peak, count.index(peak)


def worst_frame():
    best = None
    for positions in frame_positions():
        peak, line = peak_on_line(positions)
        if best is None or peak > best[0]:
            best = (peak, line, positions)
    return best


def manifest():
    peak, line, positions = worst_frame()
    m = {
        "schema": "sprite_scene_manifest_v1",
        "scene": "03-tempestade",
        "sprite_size": "8x8",
        "zoomed": False,
        "screen_h": SCREEN_H,
        "derivacao": ("ROM src/main.c shards_seed/shards_frame; ciclo de 192 "
                      "frames varrido integralmente; pico = "
                      f"{peak} entradas na linha {line}"),
        "sprites": [{"x": x, "y": y, "tile": TILE} for x, y in positions],
    }
    return m, peak, line


def self_check():
    x, y, v = seed()
    assert len(x) == len(y) == len(v) == SHARDS, "SHARDS != 24"
    assert x[0] == 7 and x[1] == 60 and y[1] == 32, "seed divergente da aritmética do C"
    assert v[:6] == [1, 2, 3, 1, 2, 3], "v0 não é 1+(i%3)"
    frames = frame_positions()
    assert len(frames) == 192, "período declarado != 192"
    assert frames[0] == [(x[i], y[i]) for i in range(SHARDS)], "frame 0 não é a seed"
    # "192 cobre todas as fases" é afirmação, não fé: varrer 384 frames e exigir
    # o MESMO pico garante que a metade extra não descobre pico novo.
    def peak_of(n):
        x0, y0, v0 = seed()
        best = 0
        for _ in range(n):
            count = [0] * SCREEN_H
            for i in range(SHARDS):
                for line in range(y0[i], min(y0[i] + SPRITE_H, SCREEN_H)):
                    count[line] += 1
            best = max(best, max(count))
            for i in range(SHARDS):
                ny = (y0[i] + v0[i]) & 0xFF
                if ny >= SCREEN_H:
                    ny = 0
                    x0[i] = (x0[i] + 19 + i) & 0xFF
                y0[i] = ny
        return best
    assert peak_of(192) == peak_of(384), "ciclo de 192 frames não cobre o pico"
    m, peak, line = manifest()
    assert m["schema"] == "sprite_scene_manifest_v1", "schema"
    assert len(m["sprites"]) == SHARDS, "número de sprites no manifesto"
    assert peak == peak_of(192), "pior frame publicada != pico da varredura"
    assert all(0 <= s["x"] <= 255 and 0 <= s["y"] <= 255 for s in m["sprites"]), "byte fora de 0..255"
    print(f"[SELF-CHECK PASS] seed=ciclo=192f pico={peak} linha={line}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    if not args.out:
        print("uso: --out <manifest.json> | --self-check", file=sys.stderr)
        return 3
    m, peak, line = manifest()
    with open(args.out, "w") as f:
        json.dump(m, f, indent=1, ensure_ascii=False)
    print(f"[MANIFESTO] {args.out} sprites={SHARDS} pico={peak} linha={line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
