#ifdef MOF_ALIS_COMBAT
#if defined(__SDCC)
#pragma codeseg SMSBANK_COMBAT
#endif
#include <limits.h>
#include "../inc/duel_combat.h"

#define ALIS_JUMP_RELEASE_GRACE 4u

#ifdef MOF_DUEL_HOST_TEST
MofCombat mof_combat;
void mof_combat_step_body(MofDuel *duel,uint8_t player,uint8_t keys)
{
    mof_combat_body(duel,player,keys);
}
#endif

static uint8_t horizontal(uint8_t keys)
{
    return keys & (MOF_DUEL_LEFT | MOF_DUEL_RIGHT);
}

#include "duel_motion_step.inc"

uint8_t mof_combat_landing_x(const MofDuel *duel,uint8_t player)
{
    const MofDuelFighter *fighter=&duel->fighters[player];
    MofDuelMotion motion=duel->body[player].motion;
    int16_t left=duel->left_wall*MOF_MOTION_UNIT;
    int16_t right=duel->right_wall*MOF_MOTION_UNIT;
    int16_t x=fighter->x;
    uint8_t event;
    do {
        /* The arena starts each motion step at the last whole-pixel pivot. */
        motion.x=x*MOF_MOTION_UNIT;
        event=mof_duel_motion_read(&motion,&fighter->def->motion,0,fighter->face_right,0,left,right);
        x=motion.x>>4;
    } while (!(event&MOF_MOTION_LANDED));
    return (uint8_t)x;
}

void mof_combat_body(MofDuel *duel, uint8_t player, uint8_t keys)
{
    const MofDuelFighter *alis = &duel->fighters[player];
    MofDuelBody *state = &duel->body[player];
    MofDuelMotion *motion = &state->motion;
    uint8_t prior=motion->mode,event,launch=0u,jump=0u;
    int8_t prior_offset = state->y_offset;
    uint8_t up = (keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)) == MOF_DUEL_UP;
    uint8_t round_over = alis->state == MOF_DUEL_KO ||
        duel->fighters[1u - player].state == MOF_DUEL_KO;
    uint8_t free = alis->state == MOF_DUEL_READY && !round_over;
    if (keys&MOF_DUEL_DOWN) mof_combat.jump_charge[player]=7;
    else if (!state->jump_pending && mof_combat.jump_charge[player])
        --mof_combat.jump_charge[player];
    /* Fighter keys still hold the previous physical reading here. The
       shared motion module receives only a committed launch edge. */
    if (round_over || (keys & MOF_DUEL_DOWN)) {
        state->jump_buffer = 0u;
    } else if (up && !(alis->keys & MOF_DUEL_UP)) {
        state->jump_buffer = keys & (MOF_DUEL_UP | MOF_DUEL_LEFT | MOF_DUEL_RIGHT);
        state->jump_grace = ALIS_JUMP_RELEASE_GRACE;
    } else if (!up && state->jump_buffer && !--state->jump_grace) {
        state->jump_buffer = 0u;
    }
    if (state->transition && !--state->transition)
        duel->tested_hurt_x[player] = INT16_MIN;
    if (!free && prior != MOF_MOTION_AIR && !state->jump_pending) return;
    if (prior == MOF_MOTION_CROUCH && (keys & MOF_DUEL_DOWN) && !state->jump_pending)
        return;
    if (state->jump_pending) {
        if (free && state->transition) return;
        if (free) {
            launch=state->jump_pending;
            jump=mof_combat.jump_charge[player] ? 2u : up ? 0u : 1u;
        }
        state->jump_pending = 0u;
        mof_combat.jump_charge[player]=0u;
    } else if (free && prior != MOF_MOTION_AIR && state->jump_buffer) {
        /* Compress on the floor before committing the latched launch vector. */
        state->jump_pending = state->jump_buffer;
        state->jump_buffer = 0u;
        state->transition = 3u;
        duel->tested_hurt_x[player] = INT16_MIN;
        return;
    }
    if (prior == MOF_MOTION_IDLE && !launch && !(keys & MOF_DUEL_DOWN)) return;
    if (prior != MOF_MOTION_AIR && alis->state == MOF_DUEL_BLOCK) return;
    keys = launch ? launch : keys & (uint8_t)~MOF_DUEL_UP;
    motion->previous_up = 0u;
    motion->x = alis->x * MOF_MOTION_UNIT;
    /* Ground walking still goes through the existing two-body solver. */
    if (prior != MOF_MOTION_AIR && !(keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)))
        keys &= (uint8_t)~(MOF_DUEL_LEFT | MOF_DUEL_RIGHT);
    event = mof_duel_motion_read(motion, &alis->def->motion, keys, alis->face_right, free,
                                 duel->left_wall * MOF_MOTION_UNIT, duel->right_wall * MOF_MOTION_UNIT);
    if (alis->state==MOF_DUEL_FALL && mof_combat.fall[player]==MOF_COMBAT_BOUNCE &&
        !(event&MOF_MOTION_LANDED))
        motion->vy+=8-alis->def->motion.gravity;
    if (motion->mode == MOF_MOTION_AIR || (event & MOF_MOTION_LANDED))
        state->air_step = (int8_t)((motion->x >> 4) - alis->x);
    if (event & MOF_MOTION_LAUNCHED) {
        if (jump==1u) motion->y=motion->vy=motion->y/2;
        if (jump==2u) {
            motion->y+=motion->y/4;
            motion->vy=motion->y+alis->def->motion.gravity;
            motion->vx+=motion->vx/2;
        }
        state->transition = 0;
        state->air_age = 0;
    }
    if (motion->mode == MOF_MOTION_AIR) ++state->air_age;
    if ((event & MOF_MOTION_LANDED) ||
        ((prior == MOF_MOTION_CROUCH) != (motion->mode == MOF_MOTION_CROUCH)))
        state->transition = 3u;
    state->y_offset = (int8_t)-(int16_t)((-motion->y) >> 4);
    if (prior_offset != state->y_offset || prior != motion->mode)
        duel->tested_hurt_x[player] = INT16_MIN;
}
#endif
