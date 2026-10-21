/* kage_matsuri — fatia rua de festival (ninja + samurai).
 * Sem float, sem malloc. API = SMSlib.h / PSGlib.h.
 * Sprites 8x16 (SPRITEMODE_TALL): 16x32 = 4 SAT entries. */
#include "SMSlib.h"
#include "PSGlib.h"
#include "stage_tiles.h"
#include "stage_map.h"
#include "kage_right_tiles.h"
#include "kage_left_tiles.h"
#include "kage_ext_right_tiles.h"
#include "kage_ext_left_tiles.h"
#include "samurai_tiles.h"
#include "samurai_left_tiles.h"
#include "palette_bg.h"
#include "palette_sprite.h"
#include "music_kage.h"
#include "sfx_slash.h"

SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_16KB(1, 0, 2026, 9, 19, "SMSForge", "kage_matsuri",
                           "rua matsuri");

#define GROUND_Y      128
#define GRAV          1
#define JUMP_V        (-7)
#define RUN           2
#define COYOTE        4
#define JUMP_BUF      4
#define SLASH1_F      12
#define SLASH2_F      14
#define TILE_KAGE_R   128
#define TILE_KAGE_L   160
#define TILE_SAM_R    192
#define TILE_SAM_L    208
#define TILE_KAGE_EXT_R 224
#define TILE_KAGE_EXT_L 240
#define ST_PLAY       0
#define ST_WIN        1
#define HUD_Y_HP      8
#define HUD_Y_GOAL    24

/* 8x16: cada entrada usa tiles N e N+1. 16x32 = 4 sprites. */
#define META16(b) \
    0,0,(b), 8,0,(b)+2, 0,16,(b)+4, 8,16,(b)+6, METASPRITE_END

static const signed char meta_kr[6][13] = {
    { META16(TILE_KAGE_R) },        /* 0: idle */
    { META16(TILE_KAGE_R + 8) },    /* 1: walk0 */
    { META16(TILE_KAGE_R + 16) },   /* 2: walk1 */
    { META16(TILE_KAGE_R + 24) },   /* 3: slash1 */
    { META16(TILE_KAGE_EXT_R) },     /* 4: slash2 */
    { META16(TILE_KAGE_EXT_R + 8) }, /* 5: jump */
};
static const signed char meta_kl[6][13] = {
    { META16(TILE_KAGE_L) },        /* 0: idle */
    { META16(TILE_KAGE_L + 8) },    /* 1: walk0 */
    { META16(TILE_KAGE_L + 16) },   /* 2: walk1 */
    { META16(TILE_KAGE_L + 24) },   /* 3: slash1 */
    { META16(TILE_KAGE_EXT_L) },     /* 4: slash2 */
    { META16(TILE_KAGE_EXT_L + 8) }, /* 5: jump */
};
static const signed char meta_sr[2][13] = {
    { META16(TILE_SAM_R) },
    { META16(TILE_SAM_R + 8) },
};
static const signed char meta_sl[2][13] = {
    { META16(TILE_SAM_L) },
    { META16(TILE_SAM_L + 8) },
};

volatile unsigned char __at(0xC7E0) probe_magic0;
volatile unsigned char __at(0xC7E1) probe_magic1;
volatile unsigned char __at(0xC7E2) probe_magic2;
volatile unsigned char __at(0xC7E3) probe_magic3;
volatile unsigned char __at(0xC7E4) probe_schema;
/* Esquema canônico do probe SMRT (molde MSSF2T, L061): vline em 0xC7EA,
 * contador de derrame como WORD em 0xC7EB e phase em 0xC7ED — o layout
 * antigo punha s0_x/s1_x em 0xC7EC/0xC7ED, exatamente onde
 * measure_worst_frame.py lê o byte alto da word e a fase: as duas
 * ferramentas liam a mesma RAM com mapas diferentes (L071). */
volatile unsigned char __at(0xC7EA) probe_vline;
volatile unsigned int  __at(0xC7EB) probe_vovf;
volatile unsigned char __at(0xC7ED) probe_phase;
volatile unsigned char __at(0xC7EE) probe_s0_x;
volatile unsigned char __at(0xC7EF) probe_s1_x;

volatile unsigned int  __at(0xC7F0) probe_frame;
volatile unsigned char __at(0xC7F2) probe_hp;
volatile unsigned char __at(0xC7F4) probe_kills;
volatile unsigned char __at(0xC7F6) probe_state;
volatile unsigned char __at(0xC7F8) probe_keys;
volatile unsigned char __at(0xC7F9) probe_pose;
volatile unsigned char __at(0xC7FA) probe_px;
volatile unsigned char __at(0xC7FB) probe_py;
volatile unsigned char __at(0xC7FC) probe_s0_hp;
volatile unsigned char __at(0xC7FD) probe_s0_alive;
volatile unsigned char __at(0xC7FE) probe_s1_hp;
volatile unsigned char __at(0xC7FF) probe_s1_alive;

static unsigned char g_state;
static unsigned char px, py;
static signed char pvy;
static unsigned char facing;     /* 0=dir 1=esq */
static unsigned char pose;       /* 0 idle 1 walk0 2 walk1 3 slash */
static unsigned char anim;
static unsigned char hp;
static unsigned char coyote;
static unsigned char jbuf;
static unsigned char slash_t;
static unsigned char slash_n;
static unsigned char slash_age;
static unsigned char attack_id;
static unsigned char prev_b1;
static unsigned char kills;
static unsigned char win_flash;

typedef struct {
    unsigned char x, y, alive, hp, anim, dir, hit_cd, last_attack;
} Samurai;
static Samurai S[2];

static void load_stage(void) {
    unsigned char x, y;
    const unsigned char *m = stage_map;
    SMS_loadTiles(stage_tiles, 0, STAGE_TILES_SIZE);
    SMS_loadTiles(kage_right_tiles, TILE_KAGE_R, KAGE_RIGHT_TILES_SIZE);
    SMS_loadTiles(kage_left_tiles, TILE_KAGE_L, KAGE_LEFT_TILES_SIZE);
    SMS_loadTiles(samurai_tiles, TILE_SAM_R, SAMURAI_TILES_SIZE);
    SMS_loadTiles(samurai_left_tiles, TILE_SAM_L, SAMURAI_LEFT_TILES_SIZE);
    SMS_loadTiles(kage_ext_right_tiles, TILE_KAGE_EXT_R, KAGE_EXT_RIGHT_TILES_SIZE);
    SMS_loadTiles(kage_ext_left_tiles, TILE_KAGE_EXT_L, KAGE_EXT_LEFT_TILES_SIZE);
    SMS_loadBGPalette(palette_bg);
    SMS_loadSpritePalette(palette_sprite);
    for (y = 0; y < 24; y++) {
        SMS_setNextTileatXY(0, y);
        for (x = 0; x < 32; x++)
            SMS_setTile(*m++);
    }
}

static void reset_game(void) {
    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 1;
    px = 56; py = GROUND_Y; pvy = 0;
    facing = 0; pose = 0; anim = 0; hp = 3;
    coyote = 0; jbuf = 0; slash_t = 0; slash_n = 0; prev_b1 = 0;
    slash_age = 0; attack_id = 0;
    kills = 0; g_state = ST_PLAY; win_flash = 0;
    probe_frame = 0;
    /* vline/phase sao reescritos a cada frame; o acumulador vovf so
     * precisa de um init no boot (ficar aqui dentro de reset_game faria
     * um win->restart diminuir o contador no meio da janela de medida). */
    S[0].x = 140; S[0].y = GROUND_Y; S[0].alive = 1; S[0].hp = 2;
    S[0].anim = 0; S[0].dir = 1; S[0].hit_cd = 0; S[0].last_attack = 0;
    S[1].x = 176; S[1].y = GROUND_Y; S[1].alive = 1; S[1].hp = 2;
    S[1].anim = 0; S[1].dir = 1; S[1].hit_cd = 0; S[1].last_attack = 0;
}

static unsigned char airborne(void) {
    return py < GROUND_Y;
}

static void apply_gravity(void) {
    if (airborne()) {
        pvy += GRAV;
        if (pvy > 6) pvy = 6;
        py += pvy;
        if (py >= GROUND_Y) { py = GROUND_Y; pvy = 0; }
    } else {
        py = GROUND_Y;
        if (pvy > 0) pvy = 0;
    }
}

static unsigned char hit_slash(unsigned char sx, unsigned char sy) {
    unsigned char x0, x1;
    if (!slash_t) return 0;
    if (facing == 0) { x0 = px + 8; x1 = px + 16 + (slash_n == 2 ? 18 : 6); }
    else { x1 = px + 8; x0 = px - (slash_n == 2 ? 18 : 6); }
    return (sx + 8 >= x0 && sx <= x1 && sy + 16 >= py && sy <= py + 32);
}

static void update_player(unsigned int keys) {
    unsigned char b1, want_jump, on_ground;
    b1 = (keys & PORT_A_KEY_1) ? 1 : 0;
    on_ground = !airborne();
    if (on_ground) coyote = COYOTE;
    else if (coyote) coyote--;
    if ((keys & PORT_A_KEY_UP) || (keys & PORT_A_KEY_2)) jbuf = JUMP_BUF;
    else if (jbuf) jbuf--;

    if (slash_t) {
        if (slash_age < 0xFF) slash_age++;
        /* slash_age is the visible SLASH1 frame number (1..12). */
        if (slash_n == 1 && b1 && !prev_b1 &&
            slash_age >= 6 && slash_age <= 12) {
            slash_n = 2;
            slash_t = SLASH2_F - 1;
            slash_age = 1;
            attack_id++;
            pose = 4;
            PSGSFXPlay((void *)sfx_slash, SFX_CHANNEL3);
        }
        slash_t--;
        pose = (slash_n == 2) ? 4 : 3;
    } else {
        if ((keys & PORT_A_KEY_LEFT) && px > 8) {
            px -= RUN; facing = 1; anim++; pose = (anim & 4) ? 2 : 1;
        } else if ((keys & PORT_A_KEY_RIGHT) && px < 232) {
            px += RUN; facing = 0; anim++; pose = (anim & 4) ? 2 : 1;
        } else {
            pose = 0;
        }
        if (b1 && !prev_b1) {
            slash_n = 1; slash_t = SLASH1_F - 1; slash_age = 1;
            attack_id++;
            pose = 3;
            PSGSFXPlay((void *)sfx_slash, SFX_CHANNEL3);
        }
    }
    want_jump = jbuf && coyote;
    if (want_jump) {
        pvy = JUMP_V; py -= 1; coyote = 0; jbuf = 0;
    }
    apply_gravity();
    if (!slash_t && airborne()) {
        pose = 5;
    }
    prev_b1 = b1;
}

static void update_samurai(void) {
    unsigned char i, hit_one;
    hit_one = 0;
    for (i = 0; i < 2; i++) {
        if (!S[i].alive) continue;
        S[i].anim++;
        if (S[i].hit_cd) S[i].hit_cd--;
        if (!S[i].hit_cd) {
            if (S[i].dir) {
                if (S[i].x > 40) S[i].x--;
                else S[i].dir = 0;
            } else {
                if (S[i].x < 220) S[i].x++;
                else S[i].dir = 1;
            }
        }
        if (!hit_one && hit_slash(S[i].x, S[i].y) && !S[i].hit_cd &&
            S[i].last_attack != attack_id) {
            hit_one = 1;
            S[i].last_attack = attack_id;
            if (S[i].hp) S[i].hp--;
            S[i].hit_cd = 4;
            if (!S[i].hp) {
                S[i].alive = 0;
                kills++;
            } else if (facing == 0) {
                if (S[i].x < 220) S[i].x += 12;
            } else if (S[i].x > 16) {
                S[i].x -= 12;
            }
        }
    }
    if (kills >= 2 && px > 200) g_state = ST_WIN;
}

static void draw(void) {
    const signed char *mk;
    unsigned char i, sp;
    SMS_initSprites();
    mk = facing ? meta_kl[pose] : meta_kr[pose];
    SMS_addMetaSprite(px, py, (void *)mk);
    for (i = 0; i < 2; i++) {
        if (!S[i].alive) continue;
        if (S[i].hit_cd && (S[i].hit_cd & 1)) continue;
        sp = (S[i].anim >> 2) & 1;
        mk = S[i].dir ? meta_sl[sp] : meta_sr[sp];
        SMS_addMetaSprite(S[i].x, S[i].y, (void *)mk);
    }
    /* HUD sem tile novo: pips = cabeca do Kage (tiles 128/130),
     * objetivo = samurai idle (tiles 192/194), ambos ja na VRAM. */
    for (i = 0; i < hp; i++) {
        SMS_addSprite(8 + (i << 4), HUD_Y_HP, TILE_KAGE_R);
        SMS_addSprite(16 + (i << 4), HUD_Y_HP, TILE_KAGE_R + 2);
    }
    for (i = kills; i < 2; i++) {
        SMS_addSprite(200 + ((i - kills) << 4), HUD_Y_GOAL, TILE_SAM_R);
        SMS_addSprite(208 + ((i - kills) << 4), HUD_Y_GOAL, TILE_SAM_R + 2);
    }
    SMS_copySpritestoSAT();
}

static void probe(unsigned int keys) {
    probe_frame++;
    probe_hp = hp;
    probe_kills = kills;
    probe_state = g_state;
    probe_keys = (unsigned char)(keys & 0xFF);
    probe_pose = (unsigned char)(pose | (facing ? 0x80 : 0));
    probe_px = px;
    probe_py = py;
    probe_s0_hp = S[0].hp;
    probe_s0_alive = S[0].alive;
    probe_s1_hp = S[1].hp;
    probe_s1_alive = S[1].alive;
    probe_s0_x = S[0].x;
    probe_s1_x = S[1].x;
    probe_vline = SMS_getVCount();
    if (probe_vline >= 0xC0)
        probe_vovf++;        /* word: nao perde a contagem em 255 */
}

void main(void) {
    unsigned int keys;
    SMS_displayOff();
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_useFirstHalfTilesforSprites(1);
    load_stage();
    reset_game();
    SMS_displayOn();
    PSGPlay((void *)music_kage);
    probe_vovf = 0;
    for (;;) {
        SMS_waitForVBlank();
        probe_phase = 1;
        PSGFrame();
        PSGSFXFrame();
        keys = SMS_getKeysStatus();
        if (g_state == ST_PLAY) {
            update_player(keys);
            update_samurai();
        } else {
            win_flash++;
            SMS_setBackdropColor((win_flash & 8) ? 8 : 0);
            /* Victory reset is edge-triggered: holding B1 through the last
             * hit must leave the torii result visible until release/repress. */
            if ((keys & PORT_A_KEY_1) && !prev_b1) {
                reset_game();
                prev_b1 = 1;
            } else {
                prev_b1 = (keys & PORT_A_KEY_1) ? 1 : 0;
            }
        }
        probe_phase = 2;
        draw();
        probe_phase = 3;
        probe(keys);
    }
}
