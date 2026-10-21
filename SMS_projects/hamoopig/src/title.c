#include "engine.h"

static unsigned int s_local;

void opening_enter(void)
{
    s_local = 0;
    text_at(8, 6, "HAMOOPIG");
    text_at(5, 8, "SMS FIGHT ENGINE");
    text_at(4, 12, "GAMEDEVBOSS 2015");
    text_at(6, 14, "PORT SMSFORGE");
    text_at(8, 20, "SMSFORGE");
}

void opening_update(void)
{
    s_local++;
    if (s_local > 120 || input_pressed(0, INP_B1)) {
        scene_request(SCENE_TITLE);
    }
}

void title_enter(void)
{
    s_local = 0;
    audio_title();
    text_at(8, 4, "HAMOOPIG");
    text_at(6, 6, "MASTER SYSTEM");
    text_at(7, 10, "B1  START");
    text_at(7, 12, "PAUSE EXIT");
    text_at(4, 16, "P1 RYO  P2 MUSGO");
    text_at(6, 18, "DOJO ARENA");
}

void title_update(void)
{
    s_local++;
    if (input_pressed(0, INP_B1) || s_local > 180) {
        scene_request(SCENE_SELECT);
    }
}

void title_present(void)
{
    SMS_initSprites();
    SMS_copySpritestoSAT();
}

void select_present(void)
{
    stream_draw();
}

static void select_reload(void)
{
    unsigned char i;
    for (i = 0; i < 2; i++) {
        P[i].id = (i == 0) ? g_sel_p1 : g_sel_p2;
        P[i].x = i ? 176 : 40;
        P[i].y = 80;
        P[i].facing = (unsigned char)(i ? 0 : 1);
        P[i].pose = POSE_IDLE;
        P[i].anim_i = 0;
        P[i].fire_on = 0;
        stream_load_now(i, POSE_IDLE, 0, (unsigned char)(P[i].facing ? 0 : 1));
    }
}

void select_enter(void)
{
    s_local = 0;
    text_at(11, 1, "SELECT");
    text_at(4, 3, "P1");
    text_at(24, 3, "P2");
    text_at(3, 20, "LR ID  DOWN MODE");
    text_at(3, 21, "B1 FIGHT");
    text_at(16, 21, "DUMMY");
    g_sel_p1 = FID_RYO;
    g_sel_p2 = FID_MUSGO;
    g_control[0] = CONTROL_HUMAN;
    g_control[1] = CONTROL_DUMMY;
    stream_init();
    select_reload();
    text_at(3, 18, "RYO ");
    text_at(22, 18, "MUSGO");
}

void select_update(void)
{
    if (input_pressed(0, INP_LEFT) || input_pressed(0, INP_RIGHT)) {
        g_sel_p1 = (g_sel_p1 == FID_RYO) ? FID_MUSGO : FID_RYO;
        text_at(3, 18, (g_sel_p1 == FID_RYO) ? "RYO " : "MUSGO");
        select_reload();
    }
    if (input_pressed(1, INP_LEFT) || input_pressed(1, INP_RIGHT)) {
        g_sel_p2 = (g_sel_p2 == FID_MUSGO) ? FID_RYO : FID_MUSGO;
        text_at(22, 18, (g_sel_p2 == FID_RYO) ? "RYO " : "MUSGO");
        select_reload();
    }
    if (input_pressed(0, INP_UP)) {
        g_control[1] = CONTROL_DUMMY;
        text_at(16, 18, "DUMMY");
    }
    /* Down cicla DUMMY->BLOCK->CPU (B2 idem; Down e observavel). */
    if (input_pressed(0, INP_DOWN) || input_pressed(0, INP_B2)) {
        if (g_control[1] == CONTROL_DUMMY) {
            g_control[1] = CONTROL_BLOCK;
            text_at(16, 18, "BLOCK");
        } else if (g_control[1] == CONTROL_BLOCK) {
            g_control[1] = CONTROL_CPU;
            text_at(16, 18, "CPU  ");
        } else {
            g_control[1] = CONTROL_DUMMY;
            text_at(16, 18, "DUMMY");
        }
    }
    if (input_pressed(0, INP_B1)) {
        scene_request(SCENE_FIGHT);
    }
    s_local++;
}
