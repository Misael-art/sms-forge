/* input_tier.c — ver inc/input_tier.h. Uma chamada por tick, O(1). */
#include "input_tier.h"

static unsigned char cnt[2];     /* ticks de pressao consecutivos (satura em 255) */
static unsigned char fired[2];   /* forte ja emitido nesta pressao */

void input_tier_init(void) {
    cnt[0] = cnt[1] = 0;
    fired[0] = fired[1] = 0;
}

unsigned char input_tier_step(unsigned char down) {
    unsigned char ev = 0, k;
    for (k = 0; k < 2; k++) {
        if (down & (unsigned char)(1u << k)) {
            if (cnt[k] != 255) cnt[k]++;
            if (cnt[k] == INPUT_TIER_T && !fired[k]) {
                ev |= (unsigned char)(k ? TIER_K2_STRONG : TIER_K1_STRONG);
                fired[k] = 1;
            }
        } else {
            if (cnt[k] && !fired[k])
                ev |= (unsigned char)(k ? TIER_K2_LIGHT : TIER_K1_LIGHT);
            cnt[k] = 0;
            fired[k] = 0;
        }
    }
    return ev;
}
