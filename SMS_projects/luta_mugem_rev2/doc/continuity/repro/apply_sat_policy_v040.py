#!/usr/bin/env python3
"""B.2b-3b — politica de SAT do fallback sprite-only.

Delta unico sobre o fonte v036 (main.c.p1c8blank_probe):
  alterna a ordem de emissao P1/P2 a cada frame (`frames & 1`), 30 Hz.
  A ordem interna de cada metasprite nao muda; nao ha nova sonda e nao ha
  mudanca de arte, escala, FX ou orcamento.

Uso:
  python3 apply_sat_policy_v040.py --dry-run <src> <dst>
  python3 apply_sat_policy_v040.py --apply   <src> <dst>
"""
import sys
from pathlib import Path

LOCALS_OLD = """static void sprites_build(const Frame *fn[2], const unsigned int poses_req[2]) {
    unsigned char side;
    unsigned int sat_om1_before, sat_om2_before;   /* B.2b: delta por frame */
"""

LOCALS_NEW = """static void sprites_build(const Frame *fn[2], const unsigned int poses_req[2]) {
    unsigned char side;
    unsigned char slot;      /* B.2b-3b: ordem alternada P1/P2 por frame */
    unsigned int sat_om1_before, sat_om2_before;   /* B.2b: delta por frame */
"""

LOOP_OLD = """    sat_om1_before = probe_sat_om_p1;   /* B.2b: deltas por frame */
    sat_om2_before = probe_sat_om_p2;
    for (side = 0; side < 2u; side++) {
"""

LOOP_NEW = """    sat_om1_before = probe_sat_om_p1;   /* B.2b: deltas por frame */
    sat_om2_before = probe_sat_om_p2;
    /* B.2b-3b: a SAT-64 nao comporta as ~70 pecas dos dois corpos. Alternar
     * a ordem de emissao a cada frame distribui a cauda omitida entre P1 e
     * P2 (30 Hz), em vez de omitir sempre o P2. A ordem DENTRO de cada
     * metasprite (prioridade de sobreposicao) permanece intacta. */
    for (slot = 0; slot < 2u; slot++) {
        side = (unsigned char)(slot ^ (unsigned char)(frames & 1u));
"""

EDITS = [("locals", LOCALS_OLD, LOCALS_NEW), ("loop", LOOP_OLD, LOOP_NEW)]
MARKERS = ["probe_sat_policy", "slot ^ (unsigned char)(frames & 1u)"]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    apply_ = "--apply" in sys.argv
    if not dry and not apply_:
        print("uso: --dry-run | --apply <src> <dst>")
        return 2
    if len(args) != 2:
        print("uso: --dry-run | --apply <src> <dst>")
        return 2
    src, dst = Path(args[0]), Path(args[1])
    text = src.read_text()
    if any(m in text for m in MARKERS):
        print("[FAIL] politica ja aplicada")
        return 2
    faltas = [n for n, old, _ in EDITS if text.count(old) != 1]
    if faltas:
        print("[FAIL] ancoras ausentes/ambiguas: %s" % faltas)
        return 2
    if dry:
        print("[DRY] 2 ancoras ok; nada escrito")
        return 0
    for name, old, new in EDITS:
        text = text.replace(old, new, 1)
    dst.write_text(text)
    print("[OK] %s -> %s" % (src, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
