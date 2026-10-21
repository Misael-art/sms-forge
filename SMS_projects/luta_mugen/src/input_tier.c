/* O tier fraco dispara na soltura; o forte dispara no tick do limiar. */
#include "input_tier.h"

void input_tier_init(InputTier *tier, unsigned char threshold_key1,
                     unsigned char threshold_key2) {
    tier->count[0] = tier->count[1] = 0;
    tier->fired[0] = tier->fired[1] = 0;
    tier->threshold[0] = threshold_key1 < 2 ? 6 : threshold_key1;
    tier->threshold[1] = threshold_key2 < 2 ? 6 : threshold_key2;
}

unsigned char input_tier_step(InputTier *tier, unsigned char down) {
    unsigned char events = 0;
    unsigned char key;
    for (key = 0; key < 2; key++) {
        unsigned char mask = (unsigned char)(1u << key);
        unsigned char strong = key ? INPUT_TIER_K2_STRONG : INPUT_TIER_K1_STRONG;
        unsigned char light = key ? INPUT_TIER_K2_LIGHT : INPUT_TIER_K1_LIGHT;
        if (down & mask) {
            if (tier->count[key] != 255u) tier->count[key]++;
            if (tier->count[key] == tier->threshold[key] && !tier->fired[key]) {
                events |= strong;
                tier->fired[key] = 1;
            }
        } else {
            if (tier->count[key] && !tier->fired[key]) events |= light;
            tier->count[key] = 0;
            tier->fired[key] = 0;
        }
    }
    return events;
}
