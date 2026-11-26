/* Impact freeze and hitstun by strength for the Scene 02 mirror rules.
   Build: cc -std=c99 -DMOF_DUEL_HOST_TEST -DMOF_DUEL_SCENE_POSTURES
          -DMOF_DUEL_SCENE_CROSSOVER -DMOF_DUEL_SCENE_SPECIALS
          -DMOF_DUEL_SCENE_MIRROR tools/test_duel_impact.c src/duel_rules.c
          src/duel_motion.c src/duel_commands.c
   The boxes and timings are synthetic; production values live in the ROM tables. */
#include <assert.h>
#include <stdio.h>
#include "../inc/duel_rules.h"

#define NONE MOF_DUEL_NO_NORMAL

static const MofDuelGeometry geometry[2] = {
    {{-11,-53,13,-3}, {{0,-40,30,-20},{0,-40,30,-20}}},
    {{-11,-53,13,-3}, {{0,-40,30,-20},{0,-40,30,-20}}}
};
static const MofDuelBox reach = {0,-40,30,-20};
static const uint8_t ends[] = {4u, 6u, 14u};

#define NORMAL(dmg) {&reach, ends, 4u, 2u, 14u, dmg, 3u, MOF_HEIGHT_MIDDLE, 0u}
static const MofDuelStandingNormal normals[2][MOF_DUEL_NORMALS_PER_FIGHTER] = {
    {{0}},
    {NORMAL(6), NORMAL(10), NORMAL(8), NORMAL(12), NORMAL(5), NORMAL(11), NORMAL(6),
     NORMAL(10), NORMAL(5), NORMAL(11), NORMAL(7), NORMAL(12), NORMAL(13), NORMAL(16)}
};

static void start(MofDuel *duel)
{
    assert(mof_duel_init_pair(duel, geometry, 6u, MOF_DUEL_ALIS, MOF_DUEL_ALIS,
                              100, 124, 16, 239, 24));
    assert(mof_duel_set_standing_normals(duel, normals));
    assert(duel->hitstop == 0u);
}

/* P1 starts `normal`; P2 holds `p2_keys`. Returns the step index of contact. */
static unsigned reach_contact(MofDuel *duel, uint8_t normal, uint8_t p2_keys)
{
    unsigned step;
    mof_duel_step_normal(duel, 0u, p2_keys, normal, NONE);
    for (step = 1u; step < 12u; ++step) {
        mof_duel_step_normal(duel, 0u, p2_keys, NONE, NONE);
        if (duel->fighters[0].contact) return step;
    }
    assert(!"no contact");
    return 0u;
}

static void check_freeze(MofDuel *duel, uint8_t stop, uint8_t target, uint8_t p2_keys)
{
    uint16_t tick = duel->tick;
    int16_t x0 = duel->fighters[0].x, x1 = duel->fighters[1].x;
    uint8_t state0 = duel->fighters[0].state, state1 = duel->fighters[1].state;
    uint8_t life = duel->fighters[1].life, i;
    assert(duel->hitstop == stop && duel->hitstop_target == target);
    for (i = 0u; i < stop; ++i) {
        /* A normal sent during the freeze is not accepted by the rules. */
        mof_duel_step_normal(duel, MOF_DUEL_RIGHT, p2_keys, 0u, 0u);
        assert(duel->tick == tick && duel->hitstop == (uint8_t)(stop - 1u - i));
        assert(duel->fighters[0].x == x0 && duel->fighters[1].x == x1);
        assert(duel->fighters[0].state == state0 && duel->fighters[1].state == state1);
        assert(duel->fighters[1].life == life);
        assert(!duel->fighters[0].contact && !duel->fighters[1].contact);
    }
}

/* Count the steps after the freeze until the defender is free again. */
static unsigned stun_left(MofDuel *duel, uint8_t p2_keys)
{
    unsigned steps = 0u;
    while (duel->fighters[1].state != MOF_DUEL_READY) {
        mof_duel_step_normal(duel, 0u, p2_keys, NONE, NONE);
        assert(++steps < 40u);
    }
    return steps;
}

static void hit(uint8_t normal, uint8_t stop, uint8_t target, unsigned stun, uint8_t damage)
{
    MofDuel duel;
    start(&duel);
    reach_contact(&duel, normal, 0u);
    assert(duel.fighters[0].contact == MOF_DUEL_LANDED);
    assert(duel.fighters[1].state == MOF_DUEL_HIT && duel.fighters[1].life == 100u - damage);
    check_freeze(&duel, stop, target, 0u);
    /* The contact step is age 0, so the defender recovers on age `stun`. */
    assert(stun_left(&duel, 0u) == stun);
}

static void guard_heavy(void)
{
    MofDuel duel;
    start(&duel);
    reach_contact(&duel, 1u, MOF_DUEL_RIGHT);
    assert(duel.fighters[0].contact == MOF_DUEL_GUARDED);
    assert(duel.fighters[1].state == MOF_DUEL_BLOCK && duel.fighters[1].life == 100u);
    check_freeze(&duel, MOF_DUEL_HEAVY_HITSTOP, 1u, MOF_DUEL_RIGHT);
    assert(stun_left(&duel, MOF_DUEL_RIGHT) == 3u);
}

static void resumes_after_freeze(void)
{
    MofDuel duel;
    uint16_t tick;
    start(&duel);
    reach_contact(&duel, 0u, 0u);
    check_freeze(&duel, MOF_DUEL_LIGHT_HITSTOP, 1u, 0u);
    tick = duel.tick;
    mof_duel_step_normal(&duel, 0u, 0u, NONE, NONE);
    assert(duel.tick == (uint16_t)(tick + 1u) && duel.hitstop == 0u);
}

int main(void)
{
    hit(0u, MOF_DUEL_LIGHT_HITSTOP, 1u, MOF_DUEL_LIGHT_HITSTUN, 6u);
    hit(2u, MOF_DUEL_LIGHT_HITSTOP, 1u, MOF_DUEL_LIGHT_HITSTUN, 8u);
    hit(1u, MOF_DUEL_HEAVY_HITSTOP, 1u | MOF_DUEL_HITSTOP_SHAKE, MOF_DUEL_HEAVY_HITSTUN, 10u);
    hit(3u, MOF_DUEL_HEAVY_HITSTOP, 1u | MOF_DUEL_HITSTOP_SHAKE, MOF_DUEL_HEAVY_HITSTUN, 12u);
    hit(MOF_DUEL_SPECIAL, MOF_DUEL_HEAVY_HITSTOP, 1u | MOF_DUEL_HITSTOP_SHAKE,
        MOF_DUEL_HEAVY_HITSTUN, 13u);
    guard_heavy();
    resumes_after_freeze();
    printf("PASS hitstop %u/%u and hitstun %u/%u by strength, guarded freeze without shake, "
           "held clock and positions, rejected normals, resume\n",
           MOF_DUEL_LIGHT_HITSTOP, MOF_DUEL_HEAVY_HITSTOP,
           MOF_DUEL_LIGHT_HITSTUN, MOF_DUEL_HEAVY_HITSTUN);
    return 0;
}
