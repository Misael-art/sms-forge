#!/usr/bin/env python3
"""B.2b-3b — cap de 8 sprites por scanline no emissor (v041).

Base: main.c.satpolicy_v040 (ordem alternada P1/P2 por frame).
Delta declarado:
  1. line_count[192] em DATA (contagem por linha visivel);
  2. clear no inicio de sprites_build;
  3. emit_frame so adiciona a celula se TODAS as suas linhas visiveis
     tiverem < 8 entradas. A celula e' omitida inteira (a SAT nao pode
     conter a 9a entrada: o VDP a descartaria e o gate §119/L129 reprova).
Nao muda arte, escala, metasprite, FX ou o teto de 64. A ordem alternada
permanece; a prioridade de cada frame decide qual corpo ocupa as 8 linhas.

Uso:
  python3 apply_linecap_v041.py --dry-run <src> <dst>
  python3 apply_linecap_v041.py --apply   <src> <dst>
"""
import sys
from pathlib import Path

STATIC_OLD = """static unsigned int frames;
"""
STATIC_NEW = """static unsigned int frames;
/* B.2b-3b: orcamento compartilhado de 8 sprites por scanline (SMS_GLOBAL
 * §119/L129 e §129/L137). line_count[] e' a ocupacao corrente do frame;
 * emit_frame nao coloca na SAT uma celula que seria a 9a entrada. */
static unsigned char line_count[192];
"""
LOCAL_OLD = """    unsigned char side;
    unsigned char slot;      /* B.2b-3b: ordem alternada P1/P2 por frame */
"""
LOCAL_NEW = """    unsigned char side;
    unsigned char slot;      /* B.2b-3b: ordem alternada P1/P2 por frame */
    unsigned char li;        /* B.2b-3b: clear do orcamento por scanline */
"""
CLEAR_OLD = """    probe_phase = 4u;       /* preparacao de metasprites em RAM */
    SMS_initSprites();
"""
CLEAR_NEW = """    probe_phase = 4u;       /* preparacao de metasprites em RAM */
    SMS_initSprites();
    for (li = 0u; li < 192u; li++)
        line_count[li] = 0u;
"""
EMIT_OLD = """        if (sx >= 0 && sx < 256 && sy >= 0 && sy < 192) {
            /* Lote B.2b: demanda SAT (1 tentativa por celula em tela). */
            if (side == 0u) probe_add_cur_p1++;
            else            probe_add_cur_p2++;
#if LUTA_DIAG_CLIP_PLAIN
            /* wave-4m (gate b'): SMS_addSprite e o macro do header (SMSlib.h:189)
             * que expandse SMS_addSprite_f (asm naked). Sem NO_SPRITE_CHECKS o
             * header (SMSlib.h:199) declara retorno signed char: -1 SAT cheia,
             * -2 Y invalido (0xD1, inalcanca com sy<192). Rejeicao por recorte
             * exclusiva do clip exige janela fora de [0,255]x[0,191] ou
             * coordenada fora do pre-guard — ambos inalcanaveis aqui. */
            add = SMS_addSprite(sx, sy, tile);
#else
            add = SMS_addSpriteClipping(sx, sy, tile);
#endif
            if (add < 0) {
                probe_omitted_sat++;
                if (side == 0u) probe_sat_om_p1++;
                else            probe_sat_om_p2++;
            }
#if LUTA_DIAG_TELEMETRY
            else if (sy < (signed int)DIAG_FLOOR) {
                /* wave-4c: array de diferencas no lugar do loop de 16 linhas
                 * por sprite (2.67 flancos/iter na fase 3). Duas escritas por
                 * sprite; a varredura unary ocorre uma vez por frame no loop
                 * principal, com semantica identica: probe_over8_events conta
                 * linhas com contagem final >= 9 (cada linha cruza o 9 uma
                 * unica vez, incrementos monotonicos) e probe_max_line e o
                 * maximo final. sy ja esta clipado em [0,192) acima. */
                line_diff[(unsigned char)sy]++;
                if ((sy + 16) < (signed int)DIAG_FLOOR)
                    line_diff[(unsigned char)(sy + 16)]--;
            }
#endif
        }
"""
EMIT_NEW = """        if (sx >= 0 && sx < 256 && sy >= 0 && sy < 192) {
            /* Lote B.2b: demanda SAT (1 tentativa por celula em tela). */
            if (side == 0u) probe_add_cur_p1++;
            else            probe_add_cur_p2++;
            last = (unsigned char)(sy + 16);
            if (last > 192u)
                last = 192u;
            full = 0u;
            for (l = (unsigned char)sy; l < last; l++) {
                if (line_count[l] >= 8u) {
                    full = 1u;
                    break;
                }
            }
            if (full) {
                /* A 9a entrada seria descartada pelo VDP; omitir a celula
                 * inteira e' a unica forma de manter a SAT legal e medivel. */
                probe_omitted_sat++;
                if (side == 0u) probe_sat_om_p1++;
                else            probe_sat_om_p2++;
            } else {
#if LUTA_DIAG_CLIP_PLAIN
                /* wave-4m (gate b'): SMS_addSprite e o macro do header (SMSlib.h:189)
                 * que expandse SMS_addSprite_f (asm naked). Sem NO_SPRITE_CHECKS o
                 * header (SMSlib.h:199) declara retorno signed char: -1 SAT cheia,
                 * -2 Y invalido (0xD1, inalcanca com sy<192). Rejeicao por recorte
                 * exclusiva do clip exige janela fora de [0,255]x[0,191] ou
                 * coordenada fora do pre-guard — ambos inalcanaveis aqui. */
                add = SMS_addSprite(sx, sy, tile);
#else
                add = SMS_addSpriteClipping(sx, sy, tile);
#endif
                if (add < 0) {
                    probe_omitted_sat++;
                    if (side == 0u) probe_sat_om_p1++;
                    else            probe_sat_om_p2++;
                } else {
                    for (l = (unsigned char)sy; l < last; l++)
                        line_count[l]++;
#if LUTA_DIAG_TELEMETRY
                    if (sy < (signed int)DIAG_FLOOR) {
                        /* Telemetria historica (desligada no perfil). */
                        line_diff[(unsigned char)sy]++;
                        if ((sy + 16) < (signed int)DIAG_FLOOR)
                            line_diff[(unsigned char)(sy + 16)]--;
                    }
#endif
                }
            }
        }
"""

EDITS = [
    ("static", STATIC_OLD, STATIC_NEW),
    ("local", LOCAL_OLD, LOCAL_NEW),
    ("clear", CLEAR_OLD, CLEAR_NEW),
    ("emitlocals", """    unsigned char tile_base, tile;
    signed int add;
""", """    unsigned char tile_base, tile;
    unsigned char l, last, full;  /* B.2b-3b: cap por scanline */
    signed int add;
"""),
    ("emit", EMIT_OLD, EMIT_NEW),
]
MARKERS = ["line_count[192]", "B.2b-3b: orcamento compartilhado"]


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
        print("[FAIL] cap ja aplicado")
        return 2
    faltas = [n for n, old, _ in EDITS if text.count(old) != 1]
    if faltas:
        print("[FAIL] ancoras ausentes/ambiguas: %s" % faltas)
        return 2
    if dry:
        print("[DRY] %d ancoras ok; nada escrito" % len(EDITS))
        return 0
    for name, old, new in EDITS:
        text = text.replace(old, new, 1)
    dst.write_text(text)
    print("[OK] %s -> %s" % (src, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
