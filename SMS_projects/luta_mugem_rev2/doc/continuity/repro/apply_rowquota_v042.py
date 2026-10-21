#!/usr/bin/env python3
"""B.2b-3b — quota por linha de 16 px no emissor (v042).

Base: main.c.satpolicy_v040 (ordem alternada P1/P2).
Delta declarado:
  1. row_count[16] local de emit_frame, zerado por lado/frame;
  2. row = (unsigned char)dy >> 4 (banda de 16 px relativa a origem);
  3. quota 6 para o lado primario (primeiro emitido) e 2 para o secundario;
  4. celula acima da quota e' omitida inteira; a SAT nao recebe a 9a entrada.

Prova declarada: se cada metasprite usa bandas de 16 px contiguas (dy multiplo
de 16) e a banda de um lado cobre no maximo quota celulas, uma scanline esta
em exatamente uma banda por lado; total <= 6 + 2 = 8. A prova e'estatica do
contrato, nao do runtime: o gate audit_sprite_line_sim mede a SAT emitida.

Nao muda arte, escala, metasprite, FX ou o teto de 64. A ordem alternada
permanece; a prioridade de cada frame decide qual corpo recebe 6 e qual 2.

Uso:
  python3 apply_rowquota_v042.py --dry-run <src> <dst>
  python3 apply_rowquota_v042.py --apply   <src> <dst>
"""
import sys
from pathlib import Path

LOCAL_OLD = """    unsigned char tile_base, tile;
    signed int add;
"""
LOCAL_NEW = """    unsigned char tile_base, tile;
    /* B.2b-3b: quota por banda de 16 px (6 primario + 2 secundario = 8/linha).
     * row = dy >> 4; dy e' o offset relativo a origem do metasprite. */
    unsigned char row_count[16];
    unsigned char i, row, quota;
    signed int add;
"""
CLEAR_OLD = """    meta = (const signed char *)meta_data;
    while (meta[0] != (signed char)METASPRITE_END) {
"""
CLEAR_NEW = """    for (i = 0u; i < 16u; i++)
        row_count[i] = 0u;
    meta = (const signed char *)meta_data;
    while (meta[0] != (signed char)METASPRITE_END) {
"""
ROW_OLD = """        sx = origin_x + dx;
        sy = origin_y + dy;
        if (sx >= 0 && sx < 256 && sy >= 0 && sy < 192) {
"""
ROW_NEW = """        sx = origin_x + dx;
        sy = origin_y + dy;
        row = (unsigned char)dy >> 4;
        /* §129/L137: o orcamento de 8/linha e' compartilhado. O lado
         * primario (primeiro emitido, alternado por frames & 1) fica com 6
         * celulas por banda; o secundario com 2. Isto e' uma divisao
         * declarada, nao uma reducao silenciosa de arte. */
        quota = (side == (unsigned char)(frames & 1u)) ? 6u : 2u;
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
            if (row_count[row] >= quota) {
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
                    row_count[row]++;
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
MARKERS = ["row_count[16]", "quota = (side =="]


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
