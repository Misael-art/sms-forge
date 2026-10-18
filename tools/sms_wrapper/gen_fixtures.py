#!/usr/bin/env python3
"""gen_fixtures.py — gera fixtures validas/invalidas para o self-test dos gates.

Fixtures sao geradas (nao commitadas): PNG indexados puros + manifests JSON.
Toda fixture invalida documenta QUAL gate deve reprová-la e POR QUE.
"""
import os, json
from png_io import write_indexed_png
import sms_palette as pal

C = pal.code_rgb

PALETTE16 = [(0, 0, 0)] + [C(c) for c in (
    (3, 3, 3), (3, 3, 0), (3, 0, 0), (0, 3, 0), (0, 0, 3),
    (3, 0, 3), (0, 3, 3), (2, 2, 2), (1, 1, 1), (2, 0, 0),
    (0, 2, 0), (0, 0, 2), (3, 2, 0), (2, 3, 0), (0, 3, 2))]

def _px(w, h, fn):
    return [bytes([fn(x, y) & 0x0F for x in range(w)]) for y in range(h)]

def generate(outdir):
    os.makedirs(outdir, exist_ok=True)
    f = {}
    # BG valido 256x192, grid alinhado, <=15 uteis, idx0 transparente
    p = os.path.join(outdir, "valid_bg.png")
    write_indexed_png(p, 256, 192, PALETTE16, _px(256, 192, lambda x, y: (x // 8 + y // 8) % 15 + 1))
    f["valid_bg"] = p
    # grid violado
    p = os.path.join(outdir, "bad_grid_bg.png")
    write_indexed_png(p, 250, 100, PALETTE16, _px(250, 100, lambda x, y: 1))
    f["bad_grid"] = p
    # cor fora do contrato
    palbad = list(PALETTE16); palbad[5] = (128, 128, 128)
    p = os.path.join(outdir, "bad_color_bg.png")
    write_indexed_png(p, 64, 64, palbad, _px(64, 64, lambda x, y: 5))
    f["bad_color"] = p
    # indice 0 opaco
    p = os.path.join(outdir, "opaque_idx0_bg.png")
    write_indexed_png(p, 32, 32, PALETTE16, _px(32, 32, lambda x, y: 1), trns=())
    f["opaque_idx0"] = p
    # sprites
    p = os.path.join(outdir, "valid_sprite16.png")
    write_indexed_png(p, 16, 16, PALETTE16, _px(16, 16, lambda x, y: (x > y) * 3 + 1))
    f["valid_sprite"] = p
    p = os.path.join(outdir, "bad_sprite12.png")
    write_indexed_png(p, 12, 12, PALETTE16, _px(12, 12, lambda x, y: 1))
    f["bad_sprite"] = p
    # cenas de sprites
    p = os.path.join(outdir, "scene_ok.json")
    json.dump({"sprite_size": "8x16", "zoomed": False, "screen_h": 192,
               "sprites": [{"y": 8 + i * 22, "x": 40 + i * 16, "tile": i}
                            for i in range(10)]}, open(p, "w"))
    f["scene_ok"] = p
    p = os.path.join(outdir, "scene_bad_line.json")
    json.dump({"sprite_size": "8x8", "screen_h": 192,
               "sprites": [{"y": 100, "x": 33 + i * 4, "tile": i} for i in range(9)]},
              open(p, "w"))
    f["scene_bad_line"] = p
    p = os.path.join(outdir, "scene_bad_sat.json")
    json.dump({"sprite_size": "8x8", "screen_h": 192,
               "sprites": [{"y": i % 190, "x": 40, "tile": i % 256} for i in range(65)]},
              open(p, "w"))
    f["scene_bad_sat"] = p
    p = os.path.join(outdir, "scene_bad_d0.json")
    json.dump({"sprite_size": "8x8", "screen_h": 192,
               "sprites": [{"y": 209, "x": 40, "tile": 0}]}, open(p, "w"))
    f["scene_bad_d0"] = p
    # L129/§119: stored = y - 1, entao y=207 grava 0xCE e nao e terminador.
    p = os.path.join(outdir, "scene_ok_y207.json")
    json.dump({"sprite_size": "8x8", "screen_h": 192,
               "sprites": [{"y": 207, "x": 40, "tile": 0}]}, open(p, "w"))
    f["scene_ok_y207"] = p
    # L129/§119: buffer de parsing conta entradas hidden; 8 delas derrubam o visivel.
    p = os.path.join(outdir, "scene_bad_hidden_overflow.json")
    json.dump({"sprite_size": "8x8", "screen_h": 192,
               "sprites": [{"y": 50, "x": 0, "tile": 0, "hidden": True} for _ in range(8)]
                          + [{"y": 50, "x": 120, "tile": 1}]}, open(p, "w"))
    f["scene_bad_hidden_overflow"] = p
    # L128/§118: o terminador 0xD0 so existe no modo 192 linhas.
    d0 = [{"y": 209, "x": 40, "tile": 0}]
    for name, extra in (("scene_ok_d0_224", {"screen_h": 224}),
                        ("scene_bad_trunc_224", {"screen_h": 224, "sat_terminated": True}),
                        ("scene_bad_screen_h", {"screen_h": 200})):
        p = os.path.join(outdir, name + ".json")
        json.dump({"sprite_size": "8x8", "sprites": d0, **extra}, open(p, "w"))
        f[name] = p
    # cenas de contraste
    p = os.path.join(outdir, "luma_ok.json")
    json.dump({"pairs": [{"fg": list(C((3, 3, 3))), "bg": list(C((0, 0, 0)))}]},
              open(p, "w"))
    f["luma_ok"] = p
    p = os.path.join(outdir, "luma_bad.json")
    json.dump({"pairs": [{"fg": list(C((1, 1, 0))), "bg": list(C((0, 1, 1))),
                          "note": "par de meia-luma quase igual: ilegivel"}]},
              open(p, "w"))
    f["luma_bad"] = p
    return f

if __name__ == "__main__":
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "fixtures", "generated")
    fs = generate(d)
    print(f"[OK] {len(fs)} fixtures geradas em {d}")
