/* input_tier.c — ver inc/input_tier.h. Uma chamada por tick por ator, O(1). */
#include "input_tier.h"

void input_tier_init(InputTier *t) {
    t->cnt[0] = 0; t->cnt[1] = 0;
    t->fired[0] = 0; t->fired[1] = 0;
}

unsigned char input_tier_step(InputTier *t, unsigned char down) {
    unsigned char ev = 0, k;
    for (k = 0; k < 2; k++) {
        if (down & (unsigned char)(1u << k)) {
            if (t->cnt[k] != 255) t->cnt[k]++;
            if (t->cnt[k] == INPUT_TIER_T && !t->fired[k]) {
                ev |= (unsigned char)(k ? TIER_K2_STRONG : TIER_K1_STRONG);
                t->fired[k] = 1;
            }
        } else {
            if (t->cnt[k] && !t->fired[k])
                ev |= (unsigned char)(k ? TIER_K2_LIGHT : TIER_K1_LIGHT);
            t->cnt[k] = 0;
            t->fired[k] = 0;
        }
    }
    return ev;
}
