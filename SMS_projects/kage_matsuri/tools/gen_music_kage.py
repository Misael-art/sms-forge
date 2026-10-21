#!/usr/bin/env python3
"""Gera music_kage no piso L078+M7 com identidade de festival yo.

A versao anterior herdava o grid de 16 frames/compasso do gerador
compartilhado: semineas a 80 ms, loop de 2,6 s — o 'soa acelerada' que o
humano ouviu em 2026-09-25. Aqui a materia e o andamento sao do kage:

  - escala yo em Re (D F G A C — sem meio-tom) de ponta a ponta;
  - grid row=9 frames/semicolcheia: semineia = 36 frames (720 ms, ~83 BPM),
    respiracao de convite a danca, nao persegicao;
  - duas secoes com funcoes diferentes: A (compassos 0-3) e o canto do
    festival descendo a escala; B (4-7) e o taiko — melodia em staccato
    de colcheias respondendo ao bumbo;
  - baixo segue a cadencia Dm-C-F-D (quarta acima, nao dominante funcional:
    o sabor 'festa' vem de la).

Uso: gen_music_kage.py --emit | --self-check | --wav out.wav
Artefatos: res/audio/music_kage.psg + inc/music_kage.h (nao editar a mao).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.abspath(os.path.join(HERE, os.pardir))
WRAP = os.path.abspath(os.path.join(PROJ, os.pardir, os.pardir,
                                    "tools", "sms_wrapper"))
sys.path.insert(0, WRAP)

import make_psg_assets as mp  # noqa: E402  (o motor arrange/render)
import audit_psg_quality as aq  # noqa: E402

ROW = 9
_bar = mp._bar
_ch = mp._ch
TAIKO = ((0, 0, 2, 4), (4, 2, 7, 2), (6, 3, 3, 2), (8, 2, 7, 2),
         (10, 0, 3, 3), (12, 2, 7, 2), (14, 3, 5, 2))
# bumbo fundo, caixa, chimbal alternados — o padrao do taiko grande.

KAGE_BARS = [
    # --- secao A: o canto desce a escala ---------------------------------
    _bar(_ch('D4', 'F4', 'A4'),
         ((0, 'D5', 6), (6, 'A4', 4), (10, 'F5', 6)),
         ((0, 'D4', 8), (8, 'A3', 8)), ((0, 0, 2, 6), (8, 2, 8, 4))),
    _bar(_ch('C4', 'E4', 'G4'),
         ((0, 'C5', 6), (6, 'G4', 4), (10, 'A4', 6)),
         ((0, 'C4', 8), (8, 'E4', 8)), ()),
    _bar(_ch('F4', 'A4', 'C5'),
         ((0, 'A4', 4), (4, 'C5', 4), (8, 'F5', 8)),
         ((0, 'F4', 8), (8, 'C4', 8)), ((0, 2, 8, 4),)),
    _bar(_ch('D4', 'F4', 'A4'),
         ((0, 'D5', 4), (4, 'C5', 2), (6, 'A4', 2), (8, 'D5', 8)),
         ((0, 'D4', 8), (8, 'A3', 8)), ()),
    # --- secao B: o taiko chama a danca -----------------------------------
    _bar(_ch('D4', 'F4', 'A4'),
         ((0, 'D5', 2), (2, 'F5', 2), (4, 'A5', 2), (6, 'G5', 2),
          (8, 'F5', 4), (12, 'D5', 4)),
         ((0, 'D4', 4), (4, 'A3', 2), (6, 'D4', 2), (8, 'D4', 4),
          (12, 'A3', 2), (14, 'D4', 2)), TAIKO),
    _bar(_ch('C4', 'E4', 'G4'),
         ((0, 'C5', 2), (2, 'E5', 2), (4, 'G5', 2), (6, 'A5', 2),
          (8, 'G5', 4), (12, 'E5', 4)),
         ((0, 'C4', 4), (4, 'G4', 2), (6, 'C4', 2), (8, 'C4', 4),
          (12, 'G4', 2), (14, 'C4', 2)), TAIKO),
    _bar(_ch('F4', 'A4', 'C5'),
         ((0, 'F5', 2), (2, 'A5', 2), (4, 'C6', 4), (8, 'A5', 2),
          (10, 'F5', 2), (12, 'C5', 4)),
         ((0, 'F4', 4), (4, 'C4', 2), (6, 'F4', 2), (8, 'F4', 4),
          (12, 'C4', 2), (14, 'F4', 2)), TAIKO),
    _bar(_ch('D4', 'F4', 'A4'),
         ((0, 'D6', 4), (4, 'A5', 2), (6, 'G5', 2), (8, 'F5', 4),
          (12, 'D5', 4)),
         ((0, 'D4', 4), (4, 'A3', 2), (6, 'D4', 2), (8, 'D4', 4),
          (12, 'A3', 4)), ((0, 0, 2, 4), (4, 3, 3, 2), (6, 3, 5, 2),
                           (8, 0, 2, 6))),
]


def build():
    return mp.arrange(KAGE_BARS, ROW, lead_att=1, harm_att=7, bass_att=2)


def emit(data):
    raw = os.path.join(PROJ, "res", "audio")
    os.makedirs(raw, exist_ok=True)
    with open(os.path.join(raw, "music_kage.psg"), "wb") as f:
        f.write(data)
    with open(os.path.join(PROJ, "inc", "music_kage.h"), "w",
              encoding="utf-8") as f:
        f.write("/* gerado por tools/gen_music_kage.py; fluxo PSGlib, "
                "piso L078+M7 (yo em Re, duas secoes, ~83 BPM) */\n")
        f.write("#define MUSIC_KAGE_SIZE %d\n" % len(data))
        f.write("static const unsigned char music_kage[%d] = {\n" % len(data))
        f.write(",".join("0x%02X" % b for b in data))
        f.write("\n};\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--wav")
    args = ap.parse_args()

    data = build()
    ev, dur = aq.decode(data)
    viol, warn, m = aq.analyze(ev, dur)
    if args.self_check:
        assert not viol, f"piso L078/M7 reprovado: {viol}"
        assert not warn, f"mix incompleto: {warn}"
        assert dur >= aq.LOOP_MIN, f"loop curto: {dur}"
        print(f"[SELF-CHECK OK] gen_music_kage: {len(data)} B, "
              f"{dur} frames ({dur / 50:.1f}s), gaps {m['gap_medio']}")
        return 0
    print(f"stream: {len(data)} bytes, dur={dur} frames "
          f"({dur / 50:.1f}s), viol={viol}, warn={warn}")
    if args.wav:
        d = mp.render_wav(args.wav, data)
        print(f"wav: {args.wav} ({d:.1f}s)")
    if args.emit:
        assert not viol, "emitir so com piso verde"
        emit(data)
        print("emit: res/audio/music_kage.psg + inc/music_kage.h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
