#include "../inc/duel_motion.h"
#include "../inc/duel_commands.h"
#ifdef MOF_ALIS_COMBAT
#include "../inc/duel_rules.h"
#include "duel_posture_view.inc"
#endif

#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)

static uint8_t horizontal(uint8_t keys)
{
    uint8_t direction = keys & (MOF_DUEL_LEFT | MOF_DUEL_RIGHT);
    return direction == (MOF_DUEL_LEFT | MOF_DUEL_RIGHT) ? 0u : direction;
}

void mof_duel_motion_reset(MofDuelMotion *motion, int16_t x, uint8_t face_right)
{
    motion->x = x;
    motion->y = motion->vx = motion->vy = 0;
    motion->mode = MOF_MOTION_IDLE;
    motion->ticks_left = motion->tap_left = motion->tap_key = 0u;
    motion->previous_horizontal = motion->previous_up = 0u;
    motion->previous_face = face_right;
}

#ifndef MOF_ALIS_COMBAT
#include "duel_motion_step.inc"
#endif

uint8_t mof_duel_motion_posture(const MofDuelMotion *motion)
{
    if (motion->mode == MOF_MOTION_AIR) return MOF_INPUT_AIRBORNE;
    return motion->mode == MOF_MOTION_CROUCH ? MOF_INPUT_CROUCHING : MOF_INPUT_STANDING;
}

uint8_t mof_duel_motion_can_act(const MofDuelMotion *motion)
{
    return motion->mode <= MOF_MOTION_CROUCH || motion->mode == MOF_MOTION_AIR;
}

uint8_t mof_duel_guard(uint8_t keys, uint8_t face_right, uint8_t posture, uint8_t can_guard)
{
    if (!can_guard || horizontal(keys) != (face_right ? MOF_DUEL_LEFT : MOF_DUEL_RIGHT))
        return MOF_GUARD_OPEN;
    if (posture == MOF_INPUT_AIRBORNE) return MOF_GUARD_AIRBORNE;
    return posture == MOF_INPUT_CROUCHING ? MOF_GUARD_CROUCHING : MOF_GUARD_STANDING;
}

uint8_t mof_duel_guard_blocks(uint8_t guard, uint8_t height, uint8_t air_blockable,
                              uint8_t ground_anti_air)
{
    if (height >= MOF_HEIGHT_THROW) return 0u;
    switch (guard) {
        case MOF_GUARD_STANDING: return height != MOF_HEIGHT_LOW;
        case MOF_GUARD_CROUCHING: return height != MOF_HEIGHT_OVERHEAD;
        case MOF_GUARD_AIRBORNE: return air_blockable && !ground_anti_air;
        default: return 0u;
    }
}

#endif
