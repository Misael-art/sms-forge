/* gerado por tools/gen_pnt_rows.py — NAO EDITAR.
 * Imagem de templates PNT em RAM (64 B/linha = 32 palavras
 * little-endian [tile, flag 0x00]), montada no BOOT. ROM 16 K
 * cheia (medido) — a receita vive aqui como operacoes
 * parametrizadas sobre helpers; o runtime so copia/commita.
 * Espelha os writers antigos de main.c; a forma da tela mora
 * AQUI (fonte unica). */
#ifndef PNT_ROWS_H
#define PNT_ROWS_H

#define PID_SEA_FIRST 13u
#define PID_BAR_ICE 21u
#define PID_BAR_SKY 22u
#define PID_DARK        1u
#define PID_SKY         2u
#define PID_ICE         3u
#define PID_ICE_HILL    4u
#define PID_WORD_E      5u
#define PID_WORD_O      6u
#define PID_HILLS       7u
#define PID_FRONT       8u
#define PID_PROMPT      9u
#define PID_METER_T    10u
#define PID_CLOUD_A    11u
#define PID_CLOUD_B    12u

static unsigned char pnt_tpl_img[23][64];

static const unsigned char tpl_pts_8[] = {2u, 3u, 7u, 8u, 13u, 14u, 19u, 20u, 26u, 27u, 0u};

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
        if ((unsigned char)(((col * 7u + r * 13u) % 29u) < 3u)) pnt_tpl_img[idx][col << 1] = 3u;
}

static void pnt_tpl_build(void) {   /* so no BOOT — loops nao sao budget */
    unsigned char r;
    tpl_fill(1u, 0u);   /* PID_DARK */
    tpl_fill(2u, 1u);   /* PID_SKY */
    tpl_fill(3u, 2u);   /* PID_ICE */
    tpl_fill(4u, 2u); pnt_tpl_img[4u][0u] = 4u;   /* PID_ICE_HILL */
    tpl_fill(5u, 1u); tpl_band(5u, 5u, 26u, 2u); tpl_stripe(5u, 5u, 26u, 2u, 1u, 3u);   /* PID_WORD_E */
    tpl_fill(6u, 1u); tpl_band(6u, 5u, 26u, 2u); tpl_stripe(6u, 5u, 26u, 2u, 0u, 3u);   /* PID_WORD_O */
    tpl_fill(7u, 2u); tpl_stripe(7u, 0u, 32u, 8u, 5u, 4u);   /* PID_HILLS */
    tpl_fill(8u, 0u); tpl_pts(8u, 3u, tpl_pts_8);   /* PID_FRONT */
    tpl_fill(9u, 0u); tpl_band(9u, 13u, 19u, 3u);   /* PID_PROMPT */
    tpl_fill(10u, 0u); tpl_band(10u, 2u, 6u, 2u);   /* PID_METER_T */
    tpl_fill(11u, 1u); tpl_stripe(11u, 0u, 32u, 4u, 0u, 2u);   /* PID_CLOUD_A */
    tpl_fill(12u, 1u); tpl_stripe(12u, 0u, 32u, 4u, 1u, 2u);   /* PID_CLOUD_B */
    for (r = 12u; r < 20u; r++) tpl_sea((unsigned char)(13u + (r - 12u)), r);   /* PID_SEA_12..19 */
    tpl_fill(21u, 0u); tpl_band(21u, 6u, 26u, 2u); tpl_stripe(21u, 6u, 26u, 4u, 1u, 0u);   /* PID_BAR_ICE */
    tpl_fill(22u, 0u); tpl_band(22u, 6u, 26u, 1u); tpl_stripe(22u, 6u, 26u, 4u, 1u, 0u);   /* PID_BAR_SKY */
}

#endif
