#!/usr/bin/env python3
"""probe_read.py — leitura mecanica da captura do probe pnt_16bit.

Nao depende de conhecimento externo sobre formato de pattern table nem sobre
qual bit de cor e R/G/B: extrai de cada celula 8x8 a MAQUERA de pixels acesos
e a cor dominante, e testa predicados relacionais entre celulas:

  flipX:  B == espelhoX(A)          flipY:  C == espelhoY(A)
  forma:  E == A (controle)          H == A (TILE_PRIORITY nao altera render BG)
  subpal: D == A em forma, D != A em cor dominante
  >255:   F == G (tile 300 renderiza, listras) e F != A
  fundo:  celula vazia toda apagada

Uso: probe_read.py <frame.png> [--json saida.json]
Exit: 0 confirmado | 1 refutado | 2 entrada invalida
"""
import sys, os, json, argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "..", "tools", "sms_wrapper"))
from png_io import read_png_rgb, png_size, PngError

CELLS = {  # nome -> (coluna, linha) em tiles de 8px
    "A": (4, 8), "B": (6, 8), "C": (8, 8), "D": (10, 8), "E": (12, 8),
    "F": (4, 10), "G": (6, 10), "H": (8, 10), "BG": (20, 4),
}
LIT_THRESHOLD = 96  # qualquer canal acima disso = pixel aceso


def cell_data(rows, name):
    x, y = CELLS[name]
    mask, colors = [], {}
    for r in range(8):
        line = []
        for c in range(8):
            rgb = rows[y * 8 + r][x * 8 + c]
            line.append(1 if max(rgb) > LIT_THRESHOLD else 0)
            if max(rgb) > LIT_THRESHOLD:
                colors[rgb] = colors.get(rgb, 0) + 1
        mask.append(tuple(line))
    dom = max(colors, key=colors.get) if colors else None
    return tuple(mask), dom


def mirror_x(mask):
    return tuple(tuple(reversed(row)) for row in mask)


def mirror_y(mask):
    return tuple(reversed(mask))


def analyze(path):
    w, h = png_size(path)
    if (w, h) != (256, 192):
        return None, "captura %dx%d nao e a canvas do VDP (256x192)" % (w, h)
    _, _, rows = read_png_rgb(path)
    m, d = {}, {}
    for name in CELLS:
        m[name], d[name] = cell_data(rows, name)

    checks = [
        ("flipX_renderiza",   m["B"] == mirror_x(m["A"]) and m["B"] != m["A"]),
        ("flipY_renderiza",   m["C"] == mirror_y(m["A"]) and m["C"] != m["A"]),
        ("controle_E_igual_A", m["E"] == m["A"]),
        ("priority_inocuo_BG", m["H"] == m["A"]),
        ("sprite_palette_cor", m["D"] == m["A"] and d["D"] is not None
                               and d["D"] != d["A"]),
        ("tile300_renderiza",  m["F"] == m["G"] and m["F"] != m["A"]
                               and sum(sum(r) for r in m["F"]) > 0),
        ("fundo_apagado",      not any(any(r) for r in m["BG"])),
        ("cor_BG_estavel",     d["A"] == d["B"] == d["C"] == d["E"] == d["H"]),
    ]
    return dict(checks), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("png")
    ap.add_argument("--json")
    a = ap.parse_args()
    try:
        checks, err = analyze(a.png)
    except (PngError, OSError) as e:
        print("[FAIL] %s" % e)
        return 2
    if err:
        print("[FAIL] %s" % err)
        return 2
    ok = all(checks.values())
    for k, v in checks.items():
        print("%-22s %s" % (k, "PASS" if v else "FAIL"))
    if a.json:
        with open(a.json, "w") as f:
            json.dump({"png": a.png, "checks": checks,
                       "verdict": "confirmado" if ok else "refutado"}, f, indent=1)
    print("[%s] probe pnt_16bit: name table 16-bit com flags %s" %
          ("CONFIRMADO" if ok else "REFUTADO",
           "PROVADO no framebuffer do emulador" if ok else "NAO provado"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
