#include "SMSlib.h"
#include "stage.h"
#include "stage_rom.h"
#include "stage_data.inc"

void stage_load(void) {
    SMS_loadBGPalette(stage_palette);
    SMS_loadTiles(stage_tiles, STAGE_TILE_BASE, sizeof(stage_tiles));
    SMS_VRAMmemcpy(0x3800u, stage_nametable, 1536u);
}
