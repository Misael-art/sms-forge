/* Static VDP proof for the 80 px source-art scale pilot.
 * This diagnostic ROM shows one idle pose per fighter. It does not exercise
 * the fight stream, animation timing, HUD, sound, or the final flicker policy.
 */
#include "SMSlib.h"
#include "luta.h"
#include "stream.h"
#include "versus_scene_runtime.h"

/* Keep the diagnostic ROM bootable on export Master System hardware. */
SMS_EMBED_SEGA_ROM_HEADER(0, 0);

#define PILOT_FLOOR 160
#define PILOT_PATTERN_BYTES 8192u
#define PILOT_SPRITES_PER_LINE 8u

typedef struct {
    signed int x;
    signed int y;
    unsigned int priority;
    unsigned char tile;
    unsigned char owner;
} PilotSprite;

static PilotSprite sprites[64];
static unsigned char sprite_count;
static unsigned char line_count[192];
static unsigned int animation_phase;

static unsigned int abs_int(signed int value) {
    return value < 0 ? (unsigned int)(-value) : (unsigned int)value;
}

static void load_pose(const PoseRef *pose, unsigned char tile_base) {
    unsigned int offset = 0;
    unsigned int vram = (unsigned int)tile_base << 5;
    const unsigned char *source;
    unsigned int count;
    SMS_saveROMBank();
    SMS_mapROMBank(pose->bank);
    while (offset < pose->size) {
        count = pose->size - offset;
        if (count > 128u) count = 128u;
        source = (const unsigned char *)(0x8000u + pose->off + offset);
        SMS_VRAMmemcpy_brief(vram + offset, source, (unsigned char)count);
        offset += count;
    }
    SMS_restoreROMBank();
}

static void collect_meta(const Frame *frame, unsigned char facing,
                         unsigned char owner, unsigned char tile_base,
                         unsigned char center_x) {
    signed int axis_x = (signed int)((unsigned int)frame->axis[0] |
                            ((unsigned int)frame->axis[1] << 8));
    signed int axis_y = (signed int)((unsigned int)frame->axis[2] |
                            ((unsigned int)frame->axis[3] << 8));
    signed int origin_x;
    signed int origin_y = PILOT_FLOOR + axis_y;
    const unsigned char *meta_data;
    const signed char *meta;
    signed int dx, dy, screen_x, screen_y;
    unsigned char tile;
    if (owner) {
        meta_data = facing ? frame->metal_p2 : frame->meta_p2;
        if (!meta_data) {
            /* A P2 diagnostic must not silently display P1 tile indices. */
            for (;;) SMS_waitForVBlank();
        }
    } else {
        meta_data = facing ? frame->metal : frame->meta;
    }
    meta = (const signed char *)meta_data;
    if (!facing) origin_x = (signed int)center_x + axis_x;
    else origin_x = FIGHTER_MIRRORED_ORIGIN_X(center_x, axis_x, frame->width);
    while (meta[0] != (signed char)METASPRITE_END && sprite_count < 64u) {
        dx = meta[0];
        dy = meta[1];
        tile = (unsigned char)meta[2] + tile_base;
        screen_x = origin_x + dx;
        screen_y = origin_y + dy;
        if (screen_x >= 0 && screen_x < 256 && screen_y >= 0 && screen_y < 192) {
            sprites[sprite_count].x = screen_x;
            sprites[sprite_count].y = screen_y;
            sprites[sprite_count].tile = tile;
            sprites[sprite_count].owner = owner;
            sprites[sprite_count].priority =
                abs_int(screen_x + 4 - center_x) * 64u +
                abs_int(screen_y + 8 - (PILOT_FLOOR - 40)) * 4u + owner;
            sprite_count++;
        }
        meta += 3;
    }
}

static void sort_by_body_priority(void) {
    unsigned char i, j;
    PilotSprite key;
    for (i = 1; i < sprite_count; i++) {
        key = sprites[i];
        j = i;
        while (j && sprites[j - 1].priority > key.priority) {
            sprites[j] = sprites[j - 1];
            j--;
        }
        sprites[j] = key;
    }
}

static unsigned char fits_line_budget(const PilotSprite *sprite) {
    signed int line;
    for (line = sprite->y; line < sprite->y + 16; line++) {
        if (line >= 0 && line < 192 && line_count[line] >= PILOT_SPRITES_PER_LINE)
            return 0;
    }
    return 1;
}

static void render_budgeted_idle(void) {
    unsigned char pass, i, index, chosen[64];
    unsigned char selected = 0;
    unsigned char first = (unsigned char)(animation_phase % sprite_count);
    for (i = 0; i < 192; i++) line_count[i] = 0;
    for (i = 0; i < 64; i++) chosen[i] = 0;

    /* Keep the torso/center first, then rotate equal-priority omissions so
       competing edge cells do not vanish on every frame. */
    for (pass = 0; pass < sprite_count; pass++) {
        index = (unsigned char)((first + pass) % sprite_count);
        if (!fits_line_budget(&sprites[index])) continue;
        SMS_addSprite((unsigned char)sprites[index].x,
                      (unsigned char)sprites[index].y,
                      sprites[index].tile);
        chosen[index] = 1;
        selected++;
        {
            signed int line;
            for (line = sprites[index].y; line < sprites[index].y + 16; line++)
                if (line >= 0 && line < 192) line_count[line]++;
        }
    }
    (void)selected;
    SMS_copySpritestoSAT();
    animation_phase += 7u;
}

void main(void) {
    const Frame *ken = &ken_anims[0].frames[0];
    const Frame *ryu = &ryu_anims[0].frames[0];
    const PoseRef *ken_pose = &versus_poses[KEN_POSE_BASE + ken->pose];
    const PoseRef *ryu_pose = &versus_poses[RYU_POSE_BASE + ryu->pose];
    unsigned int ken_tiles = (ken_pose->size + 31u) >> 5;
    unsigned char ryu_base;

    if (ken_tiles & 1u) ken_tiles++;
    ryu_base = (unsigned char)ken_tiles;
    if (((ken_tiles << 5) + ryu_pose->size) > PILOT_PATTERN_BYTES) {
        for (;;) SMS_waitForVBlank();
    }

    SMS_displayOff();
    SMS_init();
    /* SMS_init resets VDP registers and SAT, but VRAM can retain power-on
       contents. Clear it, reserve tile 255 as a blank BG tile, and paint the
       name table so the capture measures fighter pixels rather than noise. */
    SMS_VRAMmemsetW(0x0000u, 0x0000u, 16384u);
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setBGPaletteColor(0, RGB(0, 0, 0));
    SMS_loadSpritePalette(versus_sprite_palette);
    load_pose(ken_pose, 0);
    load_pose(ryu_pose, ryu_base);
    SMS_VRAMmemsetW(0x3800u, 0x00ffu, 1536u);
    collect_meta(ken, 0, 0, 0, 96);
    collect_meta(ryu, 1, 1, ryu_base, 160);
    sort_by_body_priority();
    SMS_displayOn();

    for (;;) {
        SMS_initSprites();
        render_budgeted_idle();
        SMS_waitForVBlank();
    }
}
