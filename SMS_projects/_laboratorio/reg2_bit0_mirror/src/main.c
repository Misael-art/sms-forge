/* reg2_bit0_mirror — probe de laboratorio (SMSForge)
 *
 * Pergunta (README, registrada antes do codigo): com reg2 bit0=0, o modelo
 * sms1 do BlastEm espelha as linhas visiveis 16..23 nas 0..7 (lei Tier-1
 * TilemapMirroring.txt / L130/§121), e o modelo sms2 nao espelha?
 *
 * Tecnicas: o probe escreve reg2=0xFE DIRETO na porta de controle — a
 * escrita que audit_tilemap_mirror.py veda por padrao. Isso e o alvo do
 * probe, nao um engano: o campaign roda o gate na fonte e grava a reprovacao
 * como evidencia do gate em codigo vivo. Botao 1 ativa a escrita uma unica
 * vez; sessoes sem clique servem de controle (reg2 fica no padrao 0xFF da
 * SMSlib). Bandas: linhas 0..7 solidas claras, 8..15 solidas escuras,
 * 16..23 listradas. Espelhando, a banda inferior vira solida clara.
 */
#include "SMSlib.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "reg2_bit0_mirror",
                                     "probe: SMS1 mirror com reg2 bit0=0");

/* Porta de controle com o nome nu: e a forma que audit_tilemap_mirror.py
 * --source reconhece. O unico sfr que a SMSlib expoe e SMS_VDPControlPort
 * (prefixado), e a forma prefixada ESCAPA do padrao de adjacencia do gate —
 * achado deste probe, registrado no veredito. */
__sfr __at (0xbf) VDPControlPort;

volatile unsigned char __at(0xC7D0) smi_marker[8];
/* [0..3]='SIM1' [4]=reg2 vivo (0xFF/0xFE) [5]=cliques [6..7]=frame L/H */

static const unsigned char tile_blank[32] = {
    0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0,
    0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0 };
/* tile 1: solido claro (cor 15) */
static const unsigned char tile_lite[32] = {
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF, 0xFF,0xFF,0xFF,0xFF };
/* tile 2: solido escuro (cor 1) */
static const unsigned char tile_dark[32] = {
    1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0,
    1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0 };
/* tile 3: colunas alternadas (0xAA em todos os planos) */
static const unsigned char tile_cols[32] = {
    0xAA,0xAA,0xAA,0xAA, 0xAA,0xAA,0xAA,0xAA,
    0xAA,0xAA,0xAA,0xAA, 0xAA,0xAA,0xAA,0xAA,
    0xAA,0xAA,0xAA,0xAA, 0xAA,0xAA,0xAA,0xAA,
    0xAA,0xAA,0xAA,0xAA, 0xAA,0xAA,0xAA,0xAA };
static const unsigned char pal_bg[16] = {0x00, 0x02,
    0,0,0,0,0,0,0,0,0,0,0,0,0, 0x0F};

void main(void) {
    unsigned int frame;
    unsigned char r, c, clicks;

    SMS_init();
    SMS_loadBGPalette(pal_bg);
    SMS_loadTiles(tile_blank, 0, 32);
    SMS_loadTiles(tile_lite,  1, 32);
    SMS_loadTiles(tile_dark,  2, 32);
    SMS_loadTiles(tile_cols,  3, 32);

    for (r = 0; r < 28; r++) {
        SMS_setNextTileatXY(0, r);
        for (c = 0; c < 32; c++)
            SMS_setTile(r < 8 ? 0x0001 : (r < 16 ? 0x0002 : 0x0003));
    }

    smi_marker[0] = 'S'; smi_marker[1] = 'I';
    smi_marker[2] = 'M'; smi_marker[3] = '1';
    smi_marker[4] = 0xFF; smi_marker[5] = 0;
    smi_marker[6] = 0; smi_marker[7] = 0;
    SMS_displayOn();

    frame = 0; clicks = 0;
    for (;;) {
        SMS_waitForVBlank();
        frame++;
        if (SMS_getKeysPressed() & PORT_A_KEY_1) {
            if (clicks == 0) {
                /* A escrita proibida: par, bit0=0, base $3800 preservada. */
                VDPControlPort = 0xFE;
                VDPControlPort = 0x82;
                smi_marker[4] = 0xFE;
            }
            clicks++;
        }
        smi_marker[5] = clicks;
        smi_marker[6] = (unsigned char)(frame & 0xFF);
        smi_marker[7] = (unsigned char)(frame >> 8);
    }
}
