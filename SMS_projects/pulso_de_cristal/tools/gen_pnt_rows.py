#!/usr/bin/env python3
"""Gera inc/pnt_rows.h — imagem de templates PNT em RAM, montada no BOOT.

Contexto medido (2026-10-13): os writers por linha de main.c gastavam ~13
linhas de blank em COMPUTE (loops C de 32 iteracoes, slots ix no main.lst)
contra ~8 linhas do custo fisico de escrita (64 B x 28 cyc/B — memcpy,
memset e memsetW medidos com o MESMO custo; throttle do VDP). A forma da
tela virou template de 64 B (palavra [tile, flag 0] por coluna). A ROM de
16 K esta cheia: a v1 do builder (22 loops independentes com expressao por
celula) estourou o Bank 0 no makesms. Entao a receita virou OPERACIONES
parametrizadas (fill/banda/stripe/pontos/sea) sobre helpers compartilhados:
mesma imagem de 32 celulas por linha, ~4x menos codigo.

Self-check: cada receita e espelhada em Python e comparada celula a celula
com a lambda historica do writer antigo; a expressao do mar (unica com %) e
reavaliada via c2py para as 8 linhas. Se a tela divergir, a correcao e AQUI
(fonte unica).
"""
from pathlib import Path

DARK, SKY, ICE, LIT, HILL = 0, 1, 2, 3, 4

SEA_EXPR = "(((col * 7u + r * 13u) % 29u) < 3u)"

def sea_cells(row):
    return [LIT if (c * 7 + row * 13) % 29 < 3 else ICE for c in range(32)]

# ops: ("fill", tile) ("band", lo, hi, tile) ("stripe", lo, hi, step, phase, tile)
#      ("pts", tile, [cols]) ("patch", col, tile)
# stripe marca col onde (col + phase) & (step - 1) == 0 — espelho tpl_stripe.
SPEC = [
    ("PID_DARK",     lambda c: DARK,
                     [("fill", DARK)]),
    ("PID_SKY",      lambda c: SKY,
                     [("fill", SKY)]),
    ("PID_ICE",      lambda c: ICE,
                     [("fill", ICE)]),
    ("PID_ICE_HILL", lambda c: HILL if c == 0 else ICE,
                     [("fill", ICE), ("patch", 0, HILL)]),
    ("PID_WORD_E",   lambda c: ((((c + 0) & 1) and LIT) or ICE) if 5 <= c < 26 else SKY,
                     [("fill", SKY), ("band", 5, 26, ICE), ("stripe", 5, 26, 2, 1, LIT)]),
    ("PID_WORD_O",   lambda c: ((((c + 1) & 1) and LIT) or ICE) if 5 <= c < 26 else SKY,
                     [("fill", SKY), ("band", 5, 26, ICE), ("stripe", 5, 26, 2, 0, LIT)]),
    ("PID_HILLS",    lambda c: HILL if c in (3, 11, 19, 27) else ICE,
                     [("fill", ICE), ("stripe", 0, 32, 8, 5, HILL)]),
    ("PID_FRONT",    lambda c: LIT if c in (2, 3, 7, 8, 13, 14, 19, 20, 26, 27) else DARK,
                     [("fill", DARK),
                      ("pts", LIT, [2, 3, 7, 8, 13, 14, 19, 20, 26, 27])]),
    ("PID_PROMPT",   lambda c: LIT if 13 <= c < 19 else DARK,
                     [("fill", DARK), ("band", 13, 19, LIT)]),
    ("PID_METER_T",  lambda c: ICE if 2 <= c < 6 else DARK,
                     [("fill", DARK), ("band", 2, 6, ICE)]),
    ("PID_CLOUD_A",  lambda c: ICE if (0 + c) & 3 == 0 else SKY,
                     [("fill", SKY), ("stripe", 0, 32, 4, 0, ICE)]),
    ("PID_CLOUD_B",  lambda c: ICE if (1 + c) & 3 == 0 else SKY,
                     [("fill", SKY), ("stripe", 0, 32, 4, 1, ICE)]),
]
for r in range(12, 20):
    SPEC.append((f"PID_SEA_{r}", lambda c, r=r: sea_cells(r)[c], "sea"))
SPEC.append(("PID_BAR_ICE", lambda c: ICE if 6 <= c < 26 and (c & 3) != 3 else DARK,
             [("fill", DARK), ("band", 6, 26, ICE), ("stripe", 6, 26, 4, 1, DARK)]))
SPEC.append(("PID_BAR_SKY", lambda c: SKY if 6 <= c < 26 and (c & 3) != 3 else DARK,
             [("fill", DARK), ("band", 6, 26, SKY), ("stripe", 6, 26, 4, 1, DARK)]))

N = len(SPEC) + 1  # indice 0 reservado (sem template)
SEA_FIRST_I = next(i for i, (pid, _, _) in enumerate(SPEC, 1) if pid == "PID_SEA_12")

def recipe_cells(ops):
    cells = [None] * 32
    for op in ops:
        k = op[0]
        if k == "fill":
            cells = [op[1]] * 32
        elif k == "band":
            for c in range(op[1], op[2]):
                cells[c] = op[3]
        elif k == "stripe":
            _, lo, hi, step, phase, tile = op
            for c in range(lo, hi):
                if (c + phase) & (step - 1) == 0:
                    cells[c] = tile
        elif k == "pts":
            for c in op[2]:
                cells[c] = op[1]
        elif k == "patch":
            cells[op[1]] = op[2]
    assert None not in cells
    return cells

def _strip_outer(s):
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        d = 0
        for i, ch in enumerate(s):
            if ch == "(":
                d += 1
            elif ch == ")":
                d -= 1
                if d == 0 and i != len(s) - 1:
                    return s
        s = s[1:-1].strip()
    return s

def c2py(s):
    """Converte a condicao C para Python, estruturalmente (sem parser
    completo): ternarios de topo viram conditional expressions, sufixos u
    caem, &&/|| viram and/or."""
    s = s.strip()
    s = _strip_outer(s)
    d = 0
    q = None
    for i, ch in enumerate(s):
        if ch == "(":
            d += 1
        elif ch == ")":
            d -= 1
        elif ch == "?" and d == 0:
            q = i
        elif ch == ":" and d == 0 and q is not None:
            return "(%s if %s else %s)" % (c2py(s[q + 1:i]), c2py(s[:q]), c2py(s[i + 1:]))
    return s.replace("&&", " and ").replace("||", " or ").replace("u", "")

def self_check():
    for i, (pid, fn, ops) in enumerate(SPEC, 1):
        if ops == "sea":
            cond = c2py(SEA_EXPR)
            r = i - SEA_FIRST_I + 12
            assert [LIT if eval(cond, {}, {"col": c, "r": r}) else ICE
                    for c in range(32)] == [fn(c) for c in range(32)], pid
        else:
            got = recipe_cells(ops)
            want = [fn(c) for c in range(32)]
            assert got == want, (pid, got, want)
    return True

HELPERS = """\
static void tpl_fill(unsigned char idx, unsigned char tile) {
    unsigned char col;
    for (col = 0u; col < 32u; col++) {
        pnt_tpl_img[idx][col << 1] = tile;
        pnt_tpl_img[idx][(col << 1) | 1u] = 0u;
    }
}
static void tpl_band(unsigned char idx, unsigned char lo, unsigned char hi,
                     unsigned char tile) {
    for (; lo < hi; lo++) pnt_tpl_img[idx][lo << 1] = tile;
}
/* stripe marca col onde (col + phase) & (step - 1) == 0; step potencia de 2 */
static void tpl_stripe(unsigned char idx, unsigned char lo, unsigned char hi,
                       unsigned char step, unsigned char phase, unsigned char tile) {
    for (; lo < hi; lo++)
        if ((unsigned char)((lo + phase) & (step - 1u)) == 0u)
            pnt_tpl_img[idx][lo << 1] = tile;
}
static void tpl_pts(unsigned char idx, unsigned char tile,
                    const unsigned char *cols) {
    unsigned char c;
    while ((c = *cols++)) pnt_tpl_img[idx][c << 1] = tile;
}
static void tpl_sea(unsigned char idx, unsigned char r) {
    unsigned char col;
    tpl_fill(idx, 2u);
    for (col = 0u; col < 32u; col++)
        if ((unsigned char)%s) pnt_tpl_img[idx][col << 1] = 3u;
}
""" % SEA_EXPR

def op_call(i, op):
    k = op[0]
    if k == "fill":
        return "tpl_fill(%du, %du);" % (i, op[1])
    if k == "patch":
        return "pnt_tpl_img[%du][%du] = %du;" % (i, op[1] * 2, op[2])
    if k == "band":
        return "tpl_band(%du, %du, %du, %du);" % (i, op[1], op[2], op[3])
    if k == "stripe":
        return "tpl_stripe(%du, %du, %du, %du, %du, %du);" % (i, op[1], op[2], op[3], op[4], op[5])
    if k == "pts":
        return "tpl_pts(%du, %du, tpl_pts_%d);" % (i, op[1], i)
    raise ValueError(k)

def emit():
    out = []
    out.append("/* gerado por tools/gen_pnt_rows.py — NAO EDITAR.")
    out.append(" * Imagem de templates PNT em RAM (64 B/linha = 32 palavras")
    out.append(" * little-endian [tile, flag 0x00]), montada no BOOT. ROM 16 K")
    out.append(" * cheia (medido) — a receita vive aqui como operacoes")
    out.append(" * parametrizadas sobre helpers; o runtime so copia/commita.")
    out.append(" * Espelha os writers antigos de main.c; a forma da tela mora")
    out.append(" * AQUI (fonte unica). */")
    out.append("#ifndef PNT_ROWS_H")
    out.append("#define PNT_ROWS_H")
    out.append("")
    out.append("#define PID_SEA_FIRST %du" % SEA_FIRST_I)
    out.append("#define PID_BAR_ICE %du" % (N - 2))
    out.append("#define PID_BAR_SKY %du" % (N - 1))
    for i, (pid, _, ops) in enumerate(SPEC, 1):
        if not pid.startswith("PID_SEA_") and pid not in ("PID_BAR_ICE", "PID_BAR_SKY"):
            out.append("#define %-14s %2du" % (pid, i))
    out.append("")
    out.append("static unsigned char pnt_tpl_img[%d][64];" % N)
    out.append("")
    pts_emitted = False
    for i, (pid, _, ops) in enumerate(SPEC, 1):
        if ops != "sea":
            for op in ops:
                if op[0] == "pts":
                    out.append("static const unsigned char tpl_pts_%d[] = {%s, 0u};"
                               % (i, ", ".join("%uu" % c for c in op[2])))
                    pts_emitted = True
    if pts_emitted:
        out.append("")
    out.append(HELPERS)
    out.append("static void pnt_tpl_build(void) {   /* so no BOOT — loops nao sao budget */")
    out.append("    unsigned char r;")
    for i, (pid, _, ops) in enumerate(SPEC, 1):
        if ops == "sea":
            if i == SEA_FIRST_I:
                out.append("    for (r = 12u; r < 20u; r++) tpl_sea((unsigned char)(%du + (r - 12u)), r);"
                           "   /* PID_SEA_12..19 */" % SEA_FIRST_I)
            continue
        calls = " ".join(op_call(i, op) for op in ops)
        out.append("    %s   /* %s */" % (calls, pid))
    out.append("}")
    out.append("")
    out.append("#endif")
    return "\n".join(out) + "\n"

if __name__ == "__main__":
    self_check()
    root = Path(__file__).resolve().parents[1]
    (root / "inc" / "pnt_rows.h").write_text(emit())
    print("inc/pnt_rows.h: %d templates via receitas parametrizadas (self-check ok)" % (N - 1))
