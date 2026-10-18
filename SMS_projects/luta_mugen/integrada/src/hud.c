#include "SMSlib.h"
#include "hud.h"
#include "stage_rom.h"
#include "hud_put.inc"

static unsigned char want[25];
static unsigned char shown[25];
static unsigned char n_dirty;
static unsigned short life_shown[2];

static void hud_touch(unsigned char i, unsigned char tile) {
    if (want[i] == tile) return;
    if (want[i] == shown[i]) {
        if (tile != shown[i]) n_dirty++;
    } else if (tile == shown[i]) {
        n_dirty--;
    }
    want[i] = tile;
}

void hud_init(void) {
    unsigned char i;
    n_dirty = 0;
    life_shown[0] = life_shown[1] = 0;
    for (i = 0; i < HUD_CELLS; i++)
        want[i] = shown[i] = hud_boot[i];
}

void hud_set_life(unsigned char who, unsigned short life, unsigned short max_life) {
    unsigned char filled, i, on, tile;
    unsigned short scaled;
    if (who > 1u || !max_life) return;
    if (life == life_shown[who]) return;
    life_shown[who] = life;
    /* Subtracao: a divisao de biblioteca do SDCC nao cabe no quadro ocioso. */
    scaled = (unsigned short)(life << 3);
    filled = 0;
    while (filled < 8u && scaled >= max_life) {
        scaled = (unsigned short)(scaled - max_life);
        filled++;
    }
    for (i = 0; i < 8u; i++) {
        if (who)
            on = (unsigned char)(i >= (unsigned char)(8u - filled));
        else
            on = (unsigned char)(i < filled);
        tile = on ? OFF_BAR_ON : OFF_BAR_OFF;
        hud_touch((unsigned char)(who ? 8u + i : i), tile);
    }
}

void hud_set_timer(unsigned char seconds) {
    unsigned char tens = 0;
    if (seconds > 99u) seconds = 99u;
    while (seconds >= 10u) {
        seconds = (unsigned char)(seconds - 10u);
        tens++;
    }
    hud_touch(16, (unsigned char)(OFF_DIGIT + tens));
    hud_touch(17, (unsigned char)(OFF_DIGIT + seconds));
}

void hud_set_score(unsigned char who, unsigned char wins) {
    if (wins > 9u) wins = 9u;
    hud_touch(who ? 19u : 18u, (unsigned char)(OFF_DIGIT + wins));
}

void hud_set_banner(unsigned char kind) {
    unsigned char i;
    if (kind > BANNER_TIME) kind = BANNER_CLEAR;
    for (i = 0; i < 5u; i++)
        hud_touch((unsigned char)(20u + i), hud_banner[kind][i]);
}

void hud_set_winner(unsigned char who) {
    hud_touch(20, OFF_LETTER_W);
    hud_touch(21, OFF_LETTER_I);
    hud_touch(22, OFF_LETTER_N);
    hud_touch(23, OFF_SKY);
    hud_touch(24, (unsigned char)(OFF_DIGIT + (who ? 2u : 1u)));
}

void hud_flush(void) {
    unsigned char n = 0, i;
    if (!n_dirty) return;
    for (i = 0; i < HUD_CELLS && n < 2u; i++) {
        if (shown[i] != want[i]) {
            hud_put_cell(i, want[i]);
            shown[i] = want[i];
            n++;
            n_dirty--;
        }
    }
}

void hud_flush_all(void) {
    unsigned char i;
    for (i = 0; i < HUD_CELLS; i++) {
        if (shown[i] != want[i]) {
            hud_put_cell(i, want[i]);
            shown[i] = want[i];
        }
    }
    n_dirty = 0;
}
