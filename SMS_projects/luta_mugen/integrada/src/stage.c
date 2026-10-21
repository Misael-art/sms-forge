#include "SMSlib.h"
#include "stage.h"
#include "stage_rom.h"
#include "stage_data.inc"

void stage_load(void) {
    SMS_loadBGPalette(stage_palette);
    SMS_loadTiles(stage_tiles, STAGE_TILE_BASE, sizeof(stage_tiles));
    /* O jogo não tem cenário: tile 256 é a amostra sólida de fundo usada
     * também atrás do texto do HUD. 768 palavras ocupam toda a PNT (1536 B). */
    SMS_VRAMmemsetW(0x3800u, 0x0100u, 1536u);
}
