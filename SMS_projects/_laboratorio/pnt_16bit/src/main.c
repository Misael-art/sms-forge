/* pnt_16bit — probe de laboratorio (SMSForge)
 *
 * Pergunta: a name table do SMS e de 16 bits com flags (flip X/Y, paleta de
 * sprite por tile) e indice de tile >255 e enderecavel?
 * Ver README.md: previsao registrada antes de rodar.
 *
 * Metodologia anti-interpretacao: os tiles usam apenas bytes 0x00/0x0F/0xF0/
 * 0xFF em TODOS os 4 bytes de cada linha. Assim, qualquer que seja a ordem dos
 * 4 bitplanes no formato planar do VDP, cada pixel sai cor 0 (apagado) ou 15
 * (aceso) — a FORMA observada na captura depende somente da geometria do flip,
 * nao de conhecimento externo sobre o layout de pattern table.
 *
 * Celdas (coluna x, linha y, em tiles de 8px):
 *   A(4,8)  tile 60 normal                     -> forma-base
 *   B(6,8)  tile 60 | TILE_FLIPPED_X           -> espelho horizontal de A
 *   C(8,8)  tile 60 | TILE_FLIPPED_Y           -> espelho vertical de A
 *   D(10,8) tile 60 | TILE_USE_SPRITE_PALETTE  -> mesma forma, outra subpaleta
 *   E(12,8) tile 60 normal (controle de forma)
 *   F(4,10) tile 300 listras horizontais       -> prova indice >255
 *   G(6,10) tile 300 normal (controle)
 *   H(10,10)tela vazia (fundo)                 -> controle de fundo
 */
#include "SMSlib.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "pnt_16bit",
                                     "probe: PNT 16-bit + flip + tile>255?");

/* tile 60: linhas 0-3 = metade esquerda acesa; linhas 4-7 = linha inteira
 * acesa. Forma assimetrica em X e em Y. */
static const unsigned char tile_a[32] = {
    0xF0,0xF0,0xF0,0xF0,
    0xF0,0xF0,0xF0,0xF0,
    0xF0,0xF0,0xF0,0xF0,
    0xF0,0xF0,0xF0,0xF0,
    0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF
};

/* tile 300: listras horizontais alternadas — forma unica, nao-clonavel
 * por flip de tile_a. */
static const unsigned char tile_s[32] = {
    0xFF,0xFF,0xFF,0xFF,
    0x00,0x00,0x00,0x00,
    0xFF,0xFF,0xFF,0xFF,
    0x00,0x00,0x00,0x00,
    0xFF,0xFF,0xFF,0xFF,
    0x00,0x00,0x00,0x00,
    0xFF,0xFF,0xFF,0xFF,
    0x00,0x00,0x00,0x00
};

/* paleta de teste nao usa tile 1 alem do blink; tile 1 = listras (tile_s,
 * recarregado no indice 1) para a faixa-piscante — incidental: passa o
 * guarda de tela congelada do capture_video; nao e objeto da leitura. */
static const unsigned char tile_blank[32] = {
    0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0,
    0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0
};

/* Paleta BG: cor 15 = 0x03, cor 14 = 0x0C, resto apagado (cor 0 = fundo).
 * Paleta de sprite: trocas em 14/15 — a leitura nao depende de saber qual
 * canal e R ou G; exige apenas que D difira de A em cor e que G (controlada
 * por indice, nao por flag) acompanhe A. */
static const unsigned char pal_bg[16]  = {0x00,0,0,0,0,0,0,0,
                                          0,0,0,0,0,0,0x0C,0x03};
static const unsigned char pal_sp[16]  = {0x00,0,0,0,0,0,0,0,
                                          0,0,0,0,0,0,0x03,0x0C};

void main(void) {
    unsigned char i;
    unsigned char blink;
    SMS_init();                       /* display OFF; NAO limpa VRAM (medido) */
    SMS_loadBGPalette(pal_bg);
    SMS_loadSpritePalette(pal_sp);
    /* VRAM nao e zerada: tile 0 precisa ser carregado apagado explicitamente,
     * senao o "fundo" mostra o lixo do power-on (visto na 1a captura). */
    SMS_loadTiles(tile_blank, 0, 32);
    SMS_loadTiles(tile_s, 1, 32);
    SMS_loadTiles(tile_a, 60, 32);
    SMS_loadTiles(tile_s, 300, 32);   /* >255: se houver wrap, cai no 44 */

    /* fundo: tudo em tile 0 (padrao zerado na VRAM apos SMS_init = apagado) */
    SMS_setAddr(SMS_PNTAddress);
    for (i = 0; i < 24; i++) {
        unsigned char j;
        for (j = 0; j < 32; j++) SMS_setTile(0x0000);
    }

    SMS_setTileatXY(4, 8,  60);
    SMS_setTileatXY(6, 8,  60 | TILE_FLIPPED_X);
    SMS_setTileatXY(8, 8,  60 | TILE_FLIPPED_Y);
    SMS_setTileatXY(10, 8, 60 | TILE_USE_SPRITE_PALETTE);
    SMS_setTileatXY(12, 8, 60);
    SMS_setTileatXY(4, 10, 300);
    SMS_setTileatXY(6, 10, 300);
    SMS_setTileatXY(8, 10, 60 | TILE_PRIORITY);  /* so registro: sprite-pal OFF */

    SMS_displayOn();
    blink = 0;
    for (;;) {
        SMS_waitForVBlank();          /* escrita dentro da janela de VBlank */
        blink ^= 1;
        for (i = 0; i < 32; i++)
            SMS_setTileatXY(i, 20, blink ? 1 : 0);
    }
}
