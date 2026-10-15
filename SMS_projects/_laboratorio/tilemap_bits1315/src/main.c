/* tilemap_bits1315 — probe de laboratorio (SMSForge)
 *
 * Pergunta (README, registrada antes do codigo): o VDP preserva os bits
 * 13-15 na palavra de 16 bits da name table (dump vram.bin) e os IGNORA na
 * renderizacao (seis celulas identicas no screenshot)?
 *
 * Celulas na linha de tile 8, colunas 4..14: 60, 60|FL_13, 60|FL_14,
 * 60|FL_15, 60|FL_13|FL_14|FL_15, 60 (controle). O tile 60 e assimetrico em
 * X e Y: qualquer reinterpretacao do bit (flip, prioridade, indice) aparece
 * como diferenca visual contra o controle. As palavras flagadas sao
 * EXPRESSOES (60 | FL_xx): o gate de limites as reporta como nao provadas —
 * comportamento declarado, registrado no veredito.
 */
#include "SMSlib.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "tilemap_bits1315",
                                     "probe: preservacao e ignorancia dos bits 13-15");

#define FL_13 0x2000
#define FL_14 0x4000
#define FL_15 0x8000

volatile unsigned char __at(0xC7D0) smi_marker[8];
/* [0..3]='SI81' [4]=0xE0 mascara probeada [5]=0x3C indice base [6..7]=frame */

/* tile 60: linhas 0-3 = metade esquerda acesa; linhas 4-7 = linha inteira.
 * Assimetrico nos dois eixos (mesmo desenho do probe pnt_16bit). */
static const unsigned char tile_a[32] = {
    0xF0,0xF0,0xF0,0xF0, 0xF0,0xF0,0xF0,0xF0,
    0xF0,0xF0,0xF0,0xF0, 0xF0,0xF0,0xF0,0xF0,
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF };
static const unsigned char tile_blank[32] = {
    0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0,
    0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };
static const unsigned char pal_bg[16] = {0x00, 0x02,
    0,0,0,0,0,0,0,0,0,0,0,0,0, 0x0F};

void main(void) {
    unsigned int frame;
    unsigned char r, c;

    SMS_init();
    SMS_loadBGPalette(pal_bg);
    SMS_loadTiles(tile_blank, 0, 32);   /* fundo apagado, explicito */
    SMS_loadTiles(tile_a, 60, 32);

    for (r = 0; r < 28; r++) {
        SMS_setNextTileatXY(0, r);
        for (c = 0; c < 32; c++) SMS_setTile(0x0000);
    }

    SMS_setTileatXY(4, 8, 60);
    SMS_setTileatXY(6, 8, 60 | FL_13);
    SMS_setTileatXY(8, 8, 60 | FL_14);
    SMS_setTileatXY(10, 8, 60 | FL_15);
    SMS_setTileatXY(12, 8, 60 | FL_13 | FL_14 | FL_15);
    SMS_setTileatXY(14, 8, 60);

    smi_marker[0] = 'S'; smi_marker[1] = 'I';
    smi_marker[2] = '8'; smi_marker[3] = '1';
    smi_marker[4] = 0xE0; smi_marker[5] = 0x3C;
    smi_marker[6] = 0; smi_marker[7] = 0;
    SMS_displayOn();

    frame = 0;
    for (;;) {
        SMS_waitForVBlank();
        frame++;
        smi_marker[6] = (unsigned char)(frame & 0xFF);
        smi_marker[7] = (unsigned char)(frame >> 8);
    }
}
