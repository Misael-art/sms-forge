/* mapper_vblank_copy — probe de laboratorio (SMSForge, M1 do O3)
 *
 * Pergunta (README, registrada antes do codigo): a copia de um bloco bancado
 * de 1856 B (bank 2 em 0x8000 -> VRAM 0x0000) logo apos SMS_waitForVBlank
 * completa dentro da janela do VBlank (VRAM == ROM no prefixo), mantendo o
 * loop a 60 Hz NTSC, com SMS_mapROMBank provado por leitura?
 *
 * Marcador em 0xC7D0 (corredor do laboratorio; L009 volatile).
 */
#include "SMSlib.h"

#define COPY_BYTES   1856
#define BANK_PATTERN 2
#define BANK_PROOF   3

SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "mapper_vblank_copy",
                                "probe: copia bancada -> VRAM no VBlank");

/* [0..3]='MVC1' [4..5]=frames LE [6]=vcount antes [7]=vcount depois
 * [8]=byte0 do bank2 [9]=byte0 do bank3 [10]=banco vivo apos restaurar
 * [11]=copias mod 256 [12..13]=copias LE [14..15]=reserva */
volatile unsigned char __at(0xC7D0) mvc_marker[16];

static const unsigned char mvc_pal[16] = {
    0x00, 0x04, 0x08, 0x0C, 0x10, 0x14, 0x18, 0x1C,
    0x20, 0x24, 0x28, 0x2C, 0x30, 0x34, 0x38, 0x3C };

void main(void)
{
    unsigned int frames = 0;
    unsigned int copies = 0;
    unsigned char r, c;

    SMS_init();
    SMS_loadBGPalette(mvc_pal);

    /* linhas de BG 8 e 9 mostram os tiles 0..63; a copia cobre os tiles 0..57
     * (1856 B). O resto do mapa usa o tile 63 (nunca copiado). */
    for (r = 0; r < 28; r++) {
        SMS_setNextTileatXY(0, r);
        for (c = 0; c < 32; c++) {
            unsigned int t = 63;
            if (r == 8u) t = c;
            if (r == 9u) t = 32u + c;
            SMS_setTile(t);
        }
    }

    SMS_displayOn();

    mvc_marker[0] = 'M';
    mvc_marker[1] = 'V';
    mvc_marker[2] = 'C';
    mvc_marker[3] = '1';

    for (;;) {
        SMS_waitForVBlank();
        mvc_marker[6] = SMS_getVCount();

        /* prova de mapper: slot 2 muda de conteudo com SMS_mapROMBank */
        SMS_mapROMBank(BANK_PATTERN);
        mvc_marker[8] = *(volatile unsigned char *)0x8000;
        SMS_mapROMBank(BANK_PROOF);
        mvc_marker[9] = *(volatile unsigned char *)0x8000;
        SMS_mapROMBank(BANK_PATTERN);
        mvc_marker[10] = SMS_getROMBank();

        /* copia o bloco bancado inteiro para o tile 0 (VRAM 0x0000) */
        SMS_VRAMmemcpy(0x0000, (const void *)0x8000, COPY_BYTES);

        mvc_marker[7] = SMS_getVCount();
        frames++;
        copies++;
        mvc_marker[4] = (unsigned char)(frames & 0xFFu);
        mvc_marker[5] = (unsigned char)(frames >> 8);
        mvc_marker[11] = (unsigned char)copies;
        mvc_marker[12] = (unsigned char)(copies & 0xFFu);
        mvc_marker[13] = (unsigned char)(copies >> 8);
    }
}
