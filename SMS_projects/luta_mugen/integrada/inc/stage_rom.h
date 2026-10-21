/* gerado por luta_mugen_gen_stage_hud.py a partir de res/stage/arena_tecnica.png */
#ifndef STAGE_ROM_H
#define STAGE_ROM_H
#define STAGE_TILE_BASE 256u
#define STAGE_TILE_COUNT 29u
#define OFF_SKY 0u
#define OFF_FLOOR 1u
#define OFF_HORIZON 2u
#define OFF_BAR_ON 3u
#define OFF_BAR_OFF 4u
#define OFF_DIGIT 5u
#define OFF_LETTER 15u
#define OFF_LETTER_N (OFF_LETTER + 3u)
#define OFF_LETTER_I (OFF_LETTER + 6u)
#define OFF_LETTER_W (OFF_LETTER + 13u)
#define HUD_CELLS 25u
extern const unsigned char stage_palette[16];
extern const unsigned char stage_tiles[928];
extern const unsigned char hud_boot[25];
extern const unsigned char hud_banner[5][5];
#endif
