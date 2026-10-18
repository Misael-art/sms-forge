/* vscroll_wrap224 — probe de laboratorio (SMSForge)
 *
 * Pergunta (README, registrada antes do codigo): reg9 > 223 no modo 192 e
 * tratado pelo VDP como valor-224 (240 == 16, 224 == 0, 255 == 31)?
 *
 * A tilemap inteira (28 linhas) recebe o padrao "barra": a linha r tem r
 * tiles claros e 32-r escuros. O comprimento da barra na linha superior do
 * screenshot decodifica o indice da linha; os pares de igualdade (0,224),
 * (16,240) e (31,255) sao comparados pixel a pixel offline. A fase avanca
 * sozinha a cada 60 frames VDP — o roteiro BlastEm decide em qual janela a
 * sessao termina; o marcador em RAM na ultima fronteira prova a fase viva.
 */
#include "SMSlib.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "vscroll_wrap224",
                                     "probe: wrap de reg9 em 224 (modo 192)");

/* L009: __at exige volatile; corredor de sondas 0xC7D0 (L089). */
volatile unsigned char __at(0xC7D0) smi_marker[8];
/* [0..3]='SIV1' [4]=fase [5]=valor cru escrito no reg9 [6..7]=frame L/H */

static const unsigned char PHASES[8] = {0, 16, 192, 224, 240, 255, 223, 31};

/* tile 0 apagado (SMSlib NAO limpa VRAM — licao pnt_16bit), 1 escuro
 * (cor 1), 2 claro (cor 15). */
static const unsigned char tile_blank[32] = {
    0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0,
    0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };
static const unsigned char tile_dark[32] = {
    1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0,
    1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0 };
static const unsigned char tile_lite[32] = {
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF };
static const unsigned char pal_bg[16] = {0x00, 0x02,
    0,0,0,0,0,0,0,0,0,0,0,0,0, 0x0F};

void main(void) {
    unsigned int frame;
    unsigned char phase, last, r, c;

    SMS_init();
    SMS_loadBGPalette(pal_bg);
    SMS_loadTiles(tile_blank, 0, 32);
    SMS_loadTiles(tile_dark,  1, 32);
    SMS_loadTiles(tile_lite,  2, 32);

    /* tilemap: 28 linhas; linha r = r tiles claros + resto escuro */
    for (r = 0; r < 28; r++) {
        SMS_setNextTileatXY(0, r);
        for (c = 0; c < 32; c++)
            SMS_setTile(c < r ? 0x0002 : 0x0001);
    }

    smi_marker[0] = 'S'; smi_marker[1] = 'I';
    smi_marker[2] = 'V'; smi_marker[3] = '1';
    phase = 0; last = 0;
    smi_marker[4] = 0; smi_marker[5] = PHASES[0]; smi_marker[6] = 0; smi_marker[7] = 0;
    SMS_setBGScrollY(PHASES[0]);
    SMS_displayOn();

    frame = 0;
    for (;;) {
        SMS_waitForVBlank();
        frame++;
        phase = (unsigned char)((frame / 60) & 7);
        if (phase != last) {
            SMS_setBGScrollY(PHASES[phase]);
            last = phase;
        }
        smi_marker[4] = phase;
        smi_marker[5] = PHASES[phase];
        smi_marker[6] = (unsigned char)(frame & 0xFF);
        smi_marker[7] = (unsigned char)(frame >> 8);
    }
}
