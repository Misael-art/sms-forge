/* HAMOOPIG SMS — reimplementacao da engine de luta para Master System.
 * Origem: HAMOOPIG/SGDK (GameDevBoss). Nao e copia de API SGDK.
 * Autoridade API: SMSlib.h / PSGlib.h.
 */
#include "engine.h"

SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER(0, 1, 2026, 9, 19, "SMSForge", "HAMOOPIG",
                      "HAMOOPIG fighting engine SMS port");

Fighter P[2];
unsigned char g_scene;
unsigned char g_scene_req;
unsigned int g_frame;
unsigned char g_clock;
unsigned char g_clock_div;
unsigned char g_hitstop;
unsigned char g_round;
unsigned char g_banner;
unsigned char g_banner_id;
unsigned char g_result;
unsigned char g_sel_p1;
unsigned char g_sel_p2;
unsigned char g_control[2];
unsigned int g_keys_raw;
unsigned char g_pause_armed;
unsigned char g_lock;

__sfr __at(0x7e) SMS_VCounterPort;

static void game_update(void)
{
    if (SMS_queryPauseRequested()) {
        SMS_resetPauseRequest();
        if (g_scene == SCENE_FIGHT || g_scene == SCENE_AFTER_MATCH) {
            scene_request(SCENE_TITLE);
        }
    }

    switch (g_scene) {
    case SCENE_OPENING:
        opening_update();
        break;
    case SCENE_TITLE:
        title_update();
        break;
    case SCENE_SELECT:
        select_update();
        break;
    case SCENE_FIGHT:
        fight_update();
        break;
    case SCENE_AFTER_MATCH:
        /* B1 revanche, pause ja volta ao titulo. */
        if (input_pressed(0, INP_B1)) {
            scene_request(SCENE_FIGHT);
        }
        break;
    default:
        scene_request(SCENE_TITLE);
        break;
    }
    scene_commit();
}

static void game_present(void)
{
    switch (g_scene) {
    case SCENE_OPENING:
    case SCENE_TITLE:
        title_present();
        break;
    case SCENE_SELECT:
        select_present();
        break;
    case SCENE_FIGHT:
    case SCENE_AFTER_MATCH:
        fight_present();
        break;
    default:
        break;
    }
}

void main(void)
{
    unsigned char v;

    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_displayOff();
    SMS_useFirstHalfTilesforSprites(1);
    gfx_boot();
    audio_boot();
    probe_init();
    g_sel_p1 = FID_RYO;
    g_sel_p2 = FID_MUSGO;
    g_control[0] = CONTROL_HUMAN;
    g_control[1] = CONTROL_DUMMY;
    g_scene_req = SCENE_NONE;
    g_frame = 0;
    scene_enter(SCENE_OPENING);
    SMS_displayOn();

    for (;;) {
        g_keys_raw = SMS_getKeysStatus();
        input_tick(g_keys_raw);
        probe_phase = 1;
        game_update();
        probe_phase = 2;
        stream_prepare();
        v = SMS_VCounterPort;
        probe_vline = v;
        probe_phase = 3;
        if (v >= 0xC0) {
            probe_vovf++;
            probe_missed++;
        }
        SMS_waitForVBlank();
        audio_tick();
        stream_upload();
        g_frame++;
        game_present();
        probe_phase = 4;
        probe_frame_end(g_keys_raw, v);
    }
}
