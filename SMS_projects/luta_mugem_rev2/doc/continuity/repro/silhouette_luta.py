#!/usr/bin/env python3
"""Contagem §129/L137 para o luta_mugem a partir de um manifesto SAT shadow.

O audit_silhouette_integrity.py e' especifico do O3; aqui aplicamos os mesmos
pisos declarados na doutrina, por lado e por banda de 16 px, e declaramos a
limitacao: mede celulas emitidas, nao pixels nem a ROM.
"""
import json, sys
from collections import Counter

doc = json.load(open(sys.argv[1]))
sprites = doc["sprites"]
sides = {0: [s for s in sprites if s["x"] < 128],
         1: [s for s in sprites if s["x"] >= 128]}
out = {"scene": doc.get("scene"), "source": doc.get("source"), "sides": {}}
for side, ss in sides.items():
    if not ss:
        out["sides"][side] = {"cells": 0}
        continue
    ys = sorted(set(s["y"] for s in ss))
    # bandas de 16 px relativas ao topo do lado; cada celula 8x16 cobre 16 linhas
    bands = Counter((s["y"] - min(ys)) // 16 for s in ss)
    line = Counter()
    for s in ss:
        for y in range(s["y"], s["y"] + 16):
            if 0 <= y < 192:
                line[y] += 1
    out["sides"][side] = {
        "cells": len(ss),
        "bands": {str(k): v for k, v in sorted(bands.items())},
        "band_min": min(bands.values()),
        "band_max": max(bands.values()),
        "line_peak": max(line.values()) if line else 0,
        "line_overflow_8": sum(1 for v in line.values() if v > 8),
        "rows": ys,
    }
s0, s1 = out["sides"].get(0, {}), out["sides"].get(1, {})
# pisos §129: inimigo >=2 nas linhas criticas e >=5 total; jogador >=3;
# ataque do jogador <=5 nas linhas 1-2 (bandas superiores).
checks = {}
# A atribuicao de papel e' do contrato; verificamos as duas atribuicoes.
for player, enemy, label in ((0, 1, "p1_player"), (1, 0, "p2_player")):
    p, e = out["sides"].get(player, {}), out["sides"].get(enemy, {})
    checks[label] = {
        "enemy_critical_ge_2": bool(e.get("band_min", 0) >= 2),
        "enemy_total_ge_5": bool(e.get("cells", 0) >= 5),
        "player_ge_3": bool(p.get("band_min", 0) >= 3),
        "player_attack_upper_le_5": bool(p.get("band_max", 0) <= 5),
        "player_band_min": p.get("band_min"),
        "player_band_max": p.get("band_max"),
        "enemy_band_min": e.get("band_min"),
        "enemy_cells": e.get("cells"),
    }
out["checks"] = checks
out["pass_both_roles"] = all(
    all(v for k, v in c.items() if isinstance(v, bool)) for c in checks.values()
)
out["limitation"] = "mede celulas emitidas por banda/linha; nao julga pixels, anatomia ou a ROM"
print(json.dumps(out, indent=1))
