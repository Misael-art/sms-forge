#ifndef MOF_DUEL_PROBE_H
#define MOF_DUEL_PROBE_H

#include <stdint.h>

#define MOF_DUEL_PROBE_BYTES 74u

#define MOF_DUEL_PROBE_FACES_RIGHT 0x01u
#define MOF_DUEL_PROBE_CAN_ACT     0x02u
#define MOF_DUEL_PROBE_HAS_ATTACK  0x04u
#define MOF_DUEL_PROBE_HAS_HURT    0x08u
#define MOF_DUEL_PROBE_PRESENTED_FACE  0x10u
#define MOF_DUEL_PROBE_PRESENTED_RIGHT 0x20u

typedef struct {
    int16_t left, top, right, bottom;
} MofDuelProbeBox;

typedef struct {
    uint8_t fighter, keys, state, action_tick;
    uint8_t pose_requested, pose_resident, pose_presented;
    uint8_t contact, life, flags;
    int16_t pivot_x, pivot_y;
    MofDuelProbeBox attack, hurt;
    uint16_t free_since;
    uint8_t tested_pose;
} MofDuelProbeActor;

/*
 * GD05 diagnostic record. The caller owns the backing RAM, samples logic
 * and records publication separately, then calls this after the SAT swap
 * outside the VBlank upload budget. Actor order is controller P1, P2.
 * Start with zeroed backing RAM. Odd stamp means publication in progress.
 * IDs are scene data. Integers are serialized explicitly for the host.
 */
static void mof_duel_probe_word(volatile uint8_t *out, uint16_t value)
{
    out[0] = (uint8_t)value;
    out[1] = (uint8_t)(value >> 8);
}

static void mof_duel_probe_box(volatile uint8_t *out, const MofDuelProbeBox *box)
{
    mof_duel_probe_word(out,      (uint16_t)box->left);
    mof_duel_probe_word(out + 2u, (uint16_t)box->top);
    mof_duel_probe_word(out + 4u, (uint16_t)box->right);
    mof_duel_probe_word(out + 6u, (uint16_t)box->bottom);
}

static void mof_duel_probe_actor(volatile uint8_t *out, const MofDuelProbeActor *actor)
{
    out[0] = actor->fighter;
    out[1] = actor->keys;
    out[2] = actor->state;
    out[3] = actor->action_tick;
    out[4] = actor->pose_requested;
    out[5] = actor->pose_resident;
    out[6] = actor->pose_presented;
    out[7] = actor->contact;
    out[8] = actor->life;
    out[9] = actor->flags;
    mof_duel_probe_word(out + 10u, (uint16_t)actor->pivot_x);
    mof_duel_probe_word(out + 12u, (uint16_t)actor->pivot_y);
    mof_duel_probe_box(out + 14u, &actor->attack);
    mof_duel_probe_box(out + 22u, &actor->hurt);
    mof_duel_probe_word(out + 30u, actor->free_since);
    out[32] = actor->tested_pose;
}

static void mof_duel_probe_publish(volatile uint8_t *out, uint16_t logic_tick,
                                   const MofDuelProbeActor actors[2])
{
    uint8_t writing = (uint8_t)(out[4] | 1u);

    out[4] = writing;
    out[0] = 'M';
    out[1] = 'F';
    out[2] = 'D';
    out[3] = '1';
    out[5] = MOF_DUEL_PROBE_BYTES;
    mof_duel_probe_word(out + 6u, logic_tick);
    mof_duel_probe_actor(out + 8u, &actors[0]);
    mof_duel_probe_actor(out + 41u, &actors[1]);
    out[4] = (uint8_t)(writing + 1u);
}

#endif
