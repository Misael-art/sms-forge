#include "../inc/duel_commands.h"

#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)

#define ATTACK_BUTTONS (MOF_DUEL_ONE | MOF_DUEL_TWO)
#define DIRECTION_KEYS (MOF_DUEL_UP | MOF_DUEL_DOWN | MOF_DUEL_LEFT | MOF_DUEL_RIGHT)

void mof_duel_commands_reset(MofDuelCommands *input, uint8_t initial_keys)
{
    input->last_buttons = initial_keys & ATTACK_BUTTONS;
    input->consumed = input->last_buttons;
    input->hold_age[0] = input->hold_age[1] = 0u;
    input->chord_first = input->chord_latched = 0u;
    input->previous_posture = MOF_INPUT_STANDING;
}

uint16_t mof_duel_commands_read(MofDuelCommands *input,
                                const MofDuelCommandProfile *profile,
                                uint8_t keys, uint8_t posture, uint8_t free_in_round)
{
    uint8_t buttons = keys & ATTACK_BUTTONS;
    uint8_t previous = input->last_buttons;
    uint8_t rising = buttons & (uint8_t)~previous;
    uint8_t chord_first = input->chord_first;
    uint8_t landing = input->previous_posture == MOF_INPUT_AIRBORNE &&
                      posture != MOF_INPUT_AIRBORNE;
    uint8_t pure_down = (keys & DIRECTION_KEYS) == MOF_DUEL_DOWN &&
                        posture == MOF_INPUT_CROUCHING;
    uint8_t i;
    uint16_t commands = 0u;

    input->last_buttons = buttons;
    input->previous_posture = posture;
    input->chord_first = 0u;
    if (input->chord_latched) {
        /* Staggered releases cannot turn the remainder of a chord into a kick. */
        input->chord_latched = buttons != 0u;
        input->consumed = buttons;
        return 0u;
    }
    if (!free_in_round || posture > MOF_INPUT_AIRBORNE) {
        input->consumed = buttons;
        input->hold_age[0] = input->hold_age[1] = 0u;
        return 0u;
    }
    if (landing) {
        /* Cancel the airborne attempt but preserve a fresh edge on landing. */
        input->consumed = previous & buttons;
        input->hold_age[0] = input->hold_age[1] = 0u;
        chord_first = 0u;
    }

    if (pure_down && buttons == ATTACK_BUTTONS &&
        (rising == ATTACK_BUTTONS ||
         (profile->staggered_chord && chord_first && rising &&
          (previous & chord_first) && !(input->consumed & chord_first)))) {
        input->consumed = ATTACK_BUTTONS;
        input->chord_latched = 1u;
        input->hold_age[0] = input->hold_age[1] = 0u;
        return MOF_INPUT_TAUNT;
    }
    if (pure_down && profile->staggered_chord && !previous &&
        (rising == MOF_DUEL_ONE || rising == MOF_DUEL_TWO)) {
        input->chord_first = rising;
    }

    for (i = 0u; i < 2u; ++i) {
        uint8_t button = i == 0u ? MOF_DUEL_ONE : MOF_DUEL_TWO;
        uint8_t command = i * 2u;
        if (!(buttons & button)) {
            if (input->hold_age[i] && !(input->consumed & button)) {
                commands |= MOF_INPUT_NORMAL(posture, command);
            }
            input->hold_age[i] = 0u;
            input->consumed &= (uint8_t)~button;
        } else if (!(input->consumed & button)) {
            if (input->hold_age[i] != UINT8_MAX) ++input->hold_age[i];
            if (profile->hold_ticks[i] && input->hold_age[i] >= profile->hold_ticks[i] &&
                !(input->chord_first & button)) {
                commands |= MOF_INPUT_NORMAL(posture, command + 1u);
                input->consumed |= button;
            }
        }
    }
    return commands;
}

#endif
