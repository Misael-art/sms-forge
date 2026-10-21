#!/usr/bin/env python3
"""B.2b-3b — quota escalar 5/3 por linha de 16 px (v043).

Base: main.c.satpolicy_v040 (ordem alternada P1/P2).
Delta declarado:
  1. last_dy/row_n locais de emit_frame; a cada mudanca de dy, row_n=0;
  2. quota 5 para o lado primario e 3 para o secundario (5+3=8);
  3. celula acima da quota e' omitida inteira; a SAT nao recebe a 9a entrada;
  4. sem line_count[192] e sem varredura de 16 linhas por celula.

Prova declarada: se o metasprite e' ordenado por bandas de 16 px contiguas
(dy 0,16,32,...) e cada banda tem no maximo quota celulas, uma scanline esta
em exatamente uma banda por lado; total <= 5 + 3 = 8. A prova e'estatica do
contrato; o gate audit_sprite_line_sim mede a SAT emitida.

5/3 (nao 6/2) porque §129/L137 exige que o ataque do jogador tenha <=5
celulas nas linhas superiores e que o inimigo tenha >=2 nas linhas criticas
e >=5 no total; 5/3 satisfaz os dois lados em qualquer atribuicao P1/P2.

Nao muda arte, escala, metasprite, FX ou o teto de 64. A ordem alternada
permanece; a prioridade de cada frame decide qual corpo recebe 5 e qual 3.

Uso:
  python3 apply_rowquota_v043.py --dry-run <src> <dst>
  python3 apply_rowquota_v043.py --apply   <src> <dst>
"""
import sys
from pathlib import Path

LOCAL_OLD = """    unsigned char tile_base, tile;
    signed int add;
"""
LOCAL_NEW = """    unsigned char tile_base, tile;
    /* B.2b-3b: quota escalar por banda de 16 px (5 primario + 3 secundario).
     * last_dy e' sentinela 0x7F; o metasprite e' row-major (dy 0,16,32...). */
    signed char last_dy;
    unsigned char row_n, quota;
    signed int add;
"""
CLEAR_OLD = """    meta = (const signed char *)meta_data;
    while (meta[0] != (signed char)METASPRITE_END) {
"""
CLEAR_NEW = """    last_dy = (signed char)0x7F;
    row_n = 0u;
    quota = (side == (unsigned char)(frames & 1u)) ? 5u : 3u;
    meta = (const signed char *)meta_data;
    while (meta[0] != (signed char)METASPRITE_END) {
"""
ROW_OLD = """        sx = origin_x + dx;
        sy = origin_y + dy;
        if (sx >= 0 && sx < 256 && sy >= 0 && sy < 192) {
"""
ROW_NEW = """        sx = origin_x + dx;
        sy = origin_y + dy;
        if ((signed char)dy != last_dy) {
            last_dy = (signed char)dy;
            row_n = 0u;
        }
        if (sx >= 0 && sx < 256 && sy >= 0 && sy < 192) {
"""
EMIT_OLD = """            /* Lote B.2b: demanda SAT (1 tentativa por celula em tela). */
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
EMIT_NEW = """            /* Lote B.2b: demanda SAT (1 tentativa por celula em tela). */
            if (side == 0u) probe_add_cur_p1++;
            else            probe_add_cur_p2++;
            if (row_n >= quota) {
                /* O VDP so tem 8 entradas por scanline; a 9a seria descartada.
                 * Omitir a celula inteira mantem a SAT legal e medivel. */
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
                    row_n++;
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
    ("locals", LOCAL_OLD, LOCAL_NEW),
    ("clear", CLEAR_OLD, CLEAR_NEW),
    ("row", ROW_OLD, ROW_NEW),
    ("emit", EMIT_OLD, EMIT_NEW),
]
MARKERS = ["last_dy", "row_n"]


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
        print("[FAIL] quota ja aplicada")
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
