#ifndef MOF_DUEL_COMMANDS_H
#define MOF_DUEL_COMMANDS_H

#include "duel_rules.h"

#define MOF_INPUT_STANDING  0u
#define MOF_INPUT_CROUCHING 1u
#define MOF_INPUT_AIRBORNE  2u

#define MOF_INPUT_SHORT_ONE 0u
#define MOF_INPUT_LONG_ONE  1u
#define MOF_INPUT_SHORT_TWO 2u
#define MOF_INPUT_LONG_TWO  3u
#define MOF_INPUT_TAUNT     0x1000u
#define MOF_INPUT_NORMAL(posture, command) \
    ((uint16_t)1u << ((posture) * 4u + (command)))

typedef struct {
    uint8_t last_buttons;
    uint8_t consumed;
    uint8_t hold_age[2];
    uint8_t chord_first;
    uint8_t chord_latched;
    uint8_t previous_posture;
} MofDuelCommands;

typedef struct {
    uint8_t hold_ticks[2];
    uint8_t staggered_chord;
} MofDuelCommandProfile;

void mof_duel_commands_reset(MofDuelCommands *input, uint8_t initial_keys);

/* Return candidate commands. A contact/round arbiter still owns acceptance. */
uint16_t mof_duel_commands_read(MofDuelCommands *input,
                                const MofDuelCommandProfile *profile,
                                uint8_t keys, uint8_t posture, uint8_t free_in_round);

#endif
