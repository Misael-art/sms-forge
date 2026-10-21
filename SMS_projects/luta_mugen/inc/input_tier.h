/* Classificador estatico de tier para familias de botoes do pad SMS. */
#ifndef INPUT_TIER_H
#define INPUT_TIER_H

#define INPUT_TIER_K1_LIGHT  0x01u
#define INPUT_TIER_K1_STRONG 0x02u
#define INPUT_TIER_K2_LIGHT  0x04u
#define INPUT_TIER_K2_STRONG 0x08u

typedef struct {
    unsigned char count[2];
    unsigned char fired[2];
    unsigned char threshold[2];
} InputTier;

void input_tier_init(InputTier *tier, unsigned char threshold_key1,
                     unsigned char threshold_key2);
unsigned char input_tier_step(InputTier *tier, unsigned char down);

#endif /* INPUT_TIER_H */
