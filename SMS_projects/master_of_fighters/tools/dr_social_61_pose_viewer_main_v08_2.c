#include "SMSlib.h"
#include "dr_social_61_pose_data.h"

SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER(0, 1, 2026, 10, 12,
                      "SMSForge", "DrSocialReview", "Dr Social 61 poses v08.2");

static const unsigned char bg_palette[16] = {
    0x00, 0x3F, 0x15, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};
static unsigned char sequence_index;
static unsigned char pose_index;
static unsigned char loaded_pose = 0xFF;
static unsigned char status_line[11] = "POSE 00/00";

static void print_status(void) {
    unsigned char global = ds_sequence_start[sequence_index] + pose_index;
    unsigned char count = ds_sequence_count[sequence_index];
    const unsigned char *title =
        ds_sequence_title_text + ds_sequence_title_offset[sequence_index];
    const unsigned char *frame_id = ds_frame_id_text + ds_frame_id_offset[global];
    status_line[5] = (unsigned char)('0' + ((pose_index + 1) / 10));
    status_line[6] = (unsigned char)('0' + ((pose_index + 1) % 10));
    status_line[8] = (unsigned char)('0' + (count / 10));
    status_line[9] = (unsigned char)('0' + (count % 10));
    SMS_printatXY(1, 2, (const unsigned char *)"                                ");
    SMS_printatXY(1, 3, (const unsigned char *)"                                ");
    SMS_printatXY(1, 21, (const unsigned char *)"                                ");
    SMS_printatXY(1, 22, (const unsigned char *)"                                ");
    SMS_printatXY(1, 1, (const unsigned char *)"DR SOCIAL 61 POSES V08.2");
    SMS_printatXY(1, 2, title);
    SMS_printatXY(1, 3, status_line);
    SMS_printatXY(13, 3, frame_id);
    SMS_printatXY(1, 21, (const unsigned char *)"LEFT/RIGHT=POSE UP/DOWN=SEQ");
    SMS_printatXY(1, 22, (const unsigned char *)"DIAGNOSTIC: ONE FRAME PER LOAD");
}

static void load_pose_data(unsigned char global) {
    unsigned int source_address;
    SMS_mapROMBank(ds_frame_bank[global]);
    source_address = 0x8000u + ds_frame_bank_offset[global];
    SMS_loadTiles((const unsigned char *)source_address, DS_BG_TILE_BASE,
                  ds_frame_tile_bytes[global]);
}

static void map_art_tiles(void) {
    unsigned char row, col;
    for (row = 0; row < 10; ++row)
        for (col = 0; col < 10; ++col)
            SMS_setTileatXY((unsigned char)(11 + col), (unsigned char)(7 + row),
                            (unsigned int)(TILE_USE_SPRITE_PALETTE |
                                (DS_BG_TILE_BASE + 1 + row * 10 + col)));
}

static void render_pose(void) {
    unsigned char global = ds_sequence_start[sequence_index] + pose_index;
    if (loaded_pose != global) {
        SMS_displayOff();
        load_pose_data(global);
    }
    map_art_tiles();
    print_status();
    if (loaded_pose != global) {
        loaded_pose = global;
        SMS_displayOn();
    }
}

void main(void) {
    unsigned char row, col;
    unsigned int keys;
    SMS_init();
    SMS_displayOff();
    SMS_autoSetUpTextRenderer();
    SMS_loadBGPalette(bg_palette);
    SMS_loadSpritePalette(ds_bg_palette);
    SMS_setBackdropColor(0);
    for (row = 0; row < 24; ++row)
        for (col = 0; col < 32; ++col)
            SMS_setTileatXY(col, row, 0);
    sequence_index = 0;
    pose_index = 0;
    render_pose();
    for (;;) {
        SMS_waitForVBlank();
        keys = SMS_getKeysPressed();
        if (keys & PORT_A_KEY_LEFT) {
            if (pose_index > 0) --pose_index;
            render_pose();
        } else if (keys & PORT_A_KEY_RIGHT) {
            if (pose_index + 1 < ds_sequence_count[sequence_index]) ++pose_index;
            render_pose();
        } else if (keys & PORT_A_KEY_UP) {
            sequence_index = (sequence_index == 0)
                ? DS_SEQUENCE_COUNT - 1 : sequence_index - 1;
            pose_index = 0;
            render_pose();
        } else if (keys & PORT_A_KEY_DOWN) {
            sequence_index = (sequence_index + 1) % DS_SEQUENCE_COUNT;
            pose_index = 0;
            render_pose();
        } else if (keys & PORT_A_KEY_2) {
            pose_index = 0;
            render_pose();
        }
    }
}
