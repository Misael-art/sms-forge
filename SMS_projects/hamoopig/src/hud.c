#include "engine.h"

static unsigned char last_bn = 255;

void hud_enter_fight(void)
{
    last_bn = 255;
    text_at(1, 0, "P1");
    text_at(28, 0, "P2");
    text_at(12, 2, "ROUND");
}

static void bars(unsigned char col, unsigned char hp, unsigned char sp, unsigned char flip)
{
    unsigned char i, n, m;
    n = (unsigned char)(hp >> 3);
    if (n > 8) {
        n = 8;
    }
    m = (unsigned char)(sp >> 3);
    if (m > 4) {
        m = 4;
    }
    if (!flip) {
        SMS_setNextTileatXY(col, 1);
        for (i = 0; i < 8; i++) {
            SMS_setTile(i < n ? TILE_BAR_HP : TILE_BAR_EMPTY);
        }
        SMS_setNextTileatXY(col, 2);
        for (i = 0; i < 4; i++) {
            SMS_setTile(i < m ? TILE_BAR_SP : TILE_BAR_EMPTY);
        }
    } else {
        SMS_setNextTileatXY((unsigned char)(col - 7), 1);
        for (i = 0; i < 8; i++) {
            SMS_setTile((unsigned char)(7 - i) < n ? TILE_BAR_HP : TILE_BAR_EMPTY);
        }
        SMS_setNextTileatXY((unsigned char)(col - 3), 2);
        for (i = 0; i < 4; i++) {
            SMS_setTile((unsigned char)(3 - i) < m ? TILE_BAR_SP : TILE_BAR_EMPTY);
        }
    }
}

void hud_draw(void)
{
    bars(3, P[0].hp, P[0].sp, 0);
    bars(28, P[1].hp, P[1].sp, 1);
    text_num(14, 0, g_clock);
    text_num(1, 2, P[0].rounds);
    text_num(29, 2, P[1].rounds);
    if (last_bn != g_banner_id) {
        last_bn = g_banner_id;
        text_clear(10, 11, 12);
        switch (g_banner_id) {
        case BN_ROUND:
            text_at(12, 11, "ROUND");
            text_num(18, 11, g_round);
            break;
        case BN_FIGHT:
            text_at(13, 11, "FIGHT");
            break;
        case BN_KO:
            text_at(14, 11, "K.O.");
            break;
        case BN_DRAW:
            text_at(14, 11, "DRAW");
            break;
        case BN_TIME:
            text_at(11, 11, "TIME OVER");
            break;
        case BN_P1WIN:
            text_at(12, 11, "P1 WINS");
            break;
        case BN_P2WIN:
            text_at(12, 11, "P2 WINS");
            break;
        default:
            break;
        }
    }
}
