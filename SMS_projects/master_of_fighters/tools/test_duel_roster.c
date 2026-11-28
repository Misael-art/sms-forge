/* Two different fighters through the roster in the mirror rules.
   Build: cc -std=c99 -DMOF_DUEL_HOST_TEST -DMOF_DUEL_SCENE_POSTURES
          -DMOF_DUEL_SCENE_CROSSOVER -DMOF_DUEL_SCENE_SPECIALS
          -DMOF_DUEL_SCENE_MIRROR tools/test_duel_roster.c src/duel_rules.c
          src/duel_motion.c src/duel_commands.c
   P2 uses Alis's production record. P1 uses a synthetic stand-only record
   under the Hayato id: no jump, no crouch, four standing normals and a
   special. Its numbers are fixtures, not Hayato's production data. */
#include <assert.h>
#include <stdio.h>
#include "../inc/duel_rules.h"
#include "../src/duel_roster.inc"

#define NONE MOF_DUEL_NO_NORMAL

static const MofDuelGeometry geometry[2] = {
    {{-11,-57,12,-4}, {{0,-40,30,-20},{0,-40,30,-20}}},
    {{-11,-53,13,-3}, {{0,-40,30,-20},{0,-40,30,-20}}}
};
static const MofDuelBox fist = {0,-50,30,-20};
static const MofDuelBox thrust = {12,-46,40,-30};
static const uint8_t short_ends[] = {4u, 6u, 14u}, special_ends[] = {10u, 12u, 30u};

#define MOVE_ROW(box, ends, first, end, dmg, flags) \
    {&box, ends, first, 2u, end, dmg, 3u, MOF_HEIGHT_MIDDLE, 0u, flags, 4u, MOF_MATERIAL_BODY}
static const MofDuelStandingNormal stand_moves[MOF_DUEL_NORMALS_PER_FIGHTER] = {
    MOVE_ROW(fist, short_ends, 4u, 14u, 9u, MOF_MOVE_HEAVY | MOF_MOVE_AIR_BLOCKABLE),
    MOVE_ROW(thrust, short_ends, 4u, 14u, 7u, 0u),
    MOVE_ROW(fist, short_ends, 4u, 14u, 5u, 0u),
    MOVE_ROW(thrust, short_ends, 4u, 14u, 8u, MOF_MOVE_HEAVY),
    [MOF_DUEL_SPECIAL] = MOVE_ROW(thrust, special_ends, 10u, 30u, 16u, MOF_MOVE_HEAVY),
};
#define STAND_OWNS (MOF_MOVE_BIT(0) | MOF_MOVE_BIT(1) | MOF_MOVE_BIT(2) | MOF_MOVE_BIT(3) | \
                    MOF_MOVE_BIT(MOF_DUEL_SPECIAL))
#define NO_BOX {0, 0, 0, 0}
static const MofCommand stand_commands[] = {
    {MOF_DUEL_SPECIAL, MOF_CMD_FORWARD | MOF_DUEL_ONE, MOF_CMD_AFTER_DOWN},
    {MOF_DUEL_NO_NORMAL, 0u, 0u}
};
static const MofFighterDef stand_only = {
    /* No jump impulse; gravity still brings a knocked-down body to the floor. */
    stand_moves, {0u, 0u, 0u, 0u, 0u, 0u, 0u, 0u, 24u, 0u, 0u, 0u},
    {-11,-57,12,-4}, NO_BOX, {-13,-44,12,-2}, {-12,-50,12,-4}, NO_BOX,
    38u, 0u, 3u, 9u, 2u, STAND_OWNS, 0u, 0u, 0u, stand_commands
};
static const MofFighterDef *const pair_roster[MOF_DUEL_FIGHTER_IDS] = {&stand_only, &mof_fighter_alis};

static void start(MofDuel *duel, int16_t p1_x, int16_t p2_x)
{
    assert(mof_duel_init_pair(duel, geometry, 6u, MOF_DUEL_HAYATO, MOF_DUEL_ALIS,
                              p1_x, p2_x, 16, 239, 24));
    assert(mof_duel_set_roster(duel, pair_roster));
}

static void refuses_missing_or_partial_records(void)
{
    MofDuel duel;
    MofFighterDef bad = stand_only;
    const MofFighterDef *const bad_roster[MOF_DUEL_FIGHTER_IDS] = {&bad, &mof_fighter_alis};
    assert(mof_duel_init_pair(&duel, geometry, 6u, MOF_DUEL_HAYATO, MOF_DUEL_ALIS,
                              100, 124, 16, 239, 24));
    assert(!mof_duel_set_roster(&duel, mof_roster));  /* no production Hayato record */
    bad.owned |= MOF_MOVE_BIT(MOF_DUEL_LOW_NORMALS);  /* owned move with an empty row */
    assert(!mof_duel_set_roster(&duel, bad_roster));
    bad = stand_only;
    bad.vertical = MOF_DUEL_DOWN;                     /* crouches without a crouch box */
    assert(!mof_duel_set_roster(&duel, bad_roster));
    bad = stand_only;
    bad.vertical = MOF_DUEL_ONE;                      /* not a direction */
    assert(!mof_duel_set_roster(&duel, bad_roster));
    bad = stand_only;
    bad.motion.gravity = 0u;                          /* a knockdown would never land */
    assert(!mof_duel_set_roster(&duel, bad_roster));
    start(&duel, 100, 124);
    assert(duel.fighters[0].def == &stand_only && duel.fighters[1].def == &mof_fighter_alis);
}

static void bodies_follow_their_records(void)
{
    MofDuel duel;
    uint8_t step, alis_flew = 0u;
    start(&duel, 60, 140);
    for (step = 0u; step < 30u; ++step) {
        mof_duel_step_normal(&duel, MOF_DUEL_UP, MOF_DUEL_UP, NONE, NONE);
        assert(duel.body[0].motion.mode != MOF_MOTION_AIR && duel.body[0].y_offset == 0);
        alis_flew |= duel.body[1].motion.mode == MOF_MOTION_AIR;
    }
    assert(alis_flew);

    start(&duel, 60, 140);
    for (step = 0u; step < 5u; ++step)
        mof_duel_step_normal(&duel, MOF_DUEL_DOWN | MOF_DUEL_RIGHT, MOF_DUEL_DOWN | MOF_DUEL_LEFT,
                             NONE, NONE);
    /* Down is no posture for P1, so it walks; Alis crouches in place. */
    assert(duel.body[0].motion.mode != MOF_MOTION_CROUCH && duel.fighters[0].x == 65);
    assert(duel.body[1].motion.mode == MOF_MOTION_CROUCH && duel.fighters[1].x == 140);
    assert(duel.tested_hurt[0].top == 144 - 57 && duel.tested_hurt[1].top == 144 - 33);
}

static void moves_belong_to_their_owner(void)
{
    MofDuel duel;
    start(&duel, 100, 124);
    mof_duel_step_normal(&duel, 0u, 0u, MOF_DUEL_THROW, MOF_DUEL_THROW);
    assert(duel.fighters[0].state == MOF_DUEL_READY);   /* P1 owns no throw */
    assert(duel.fighters[1].state == MOF_DUEL_ATTACK && duel.fighters[1].standing_normal == MOF_DUEL_THROW);
}

static void land(MofDuel *duel, uint8_t attacker, uint8_t normal)
{
    uint8_t step;
    mof_duel_step_normal(duel, 0u, 0u, attacker ? NONE : normal, attacker ? normal : NONE);
    for (step = 0u; step < 12u && duel->fighters[attacker].contact != MOF_DUEL_LANDED; ++step)
        mof_duel_step_normal(duel, 0u, 0u, NONE, NONE);
    assert(duel->fighters[attacker].contact == MOF_DUEL_LANDED);
}

static void contact_reads_the_attacker_record(void)
{
    MofDuel duel;
    start(&duel, 100, 124);
    land(&duel, 0u, 0u);   /* P1 fist: 9 damage and heavy in its record */
    assert(duel.fighters[1].life == 91u && duel.fighters[1].hit_duration == MOF_DUEL_HEAVY_HITSTUN);
    assert(duel.hitstop == MOF_DUEL_HEAVY_HITSTOP);
    start(&duel, 100, 124);
    land(&duel, 1u, 0u);   /* Alis's same move id: 6 damage and light */
    assert(duel.fighters[0].life == 94u && duel.fighters[0].hit_duration == MOF_DUEL_LIGHT_HITSTUN);
    assert(duel.hitstop == MOF_DUEL_LIGHT_HITSTOP);
}

static void specials_advance_by_record(void)
{
    MofDuel duel;
    uint8_t age;
    int16_t p1 = 60, p2 = 140;
    start(&duel, p1, p2);
    mof_duel_step_normal(&duel, 0u, 0u, MOF_DUEL_SPECIAL, MOF_DUEL_SPECIAL);
    for (age = 0u; age < 9u; ++age) {
        /* P1 advances from tick 3 to 8; Alis from tick 2 to 6. */
        int16_t want1 = 60 + 2 * (age >= 3u ? (age < 9u ? age - 2 : 6) : 0);
        int16_t want2 = 140 - 2 * (age >= 2u ? (age < 7u ? age - 1 : 5) : 0);
        assert(duel.fighters[0].x == want1 && duel.fighters[1].x == want2);
        mof_duel_step_normal(&duel, 0u, 0u, NONE, NONE);
    }
    (void)p1; (void)p2;
}

/* Seeded random play: the stand-only body never leaves its capabilities. */
static void random_play_keeps_capabilities(void)
{
    static const uint8_t keys[] = {0u, MOF_DUEL_LEFT, MOF_DUEL_RIGHT, MOF_DUEL_DOWN, MOF_DUEL_UP,
        MOF_DUEL_UP | MOF_DUEL_RIGHT, MOF_DUEL_DOWN | MOF_DUEL_LEFT, MOF_DUEL_ONE, MOF_DUEL_TWO};
    MofDuel duel;
    uint32_t seed = 2026u;
    unsigned step, attacks = 0u, hits = 0u;
    uint8_t k[2] = {0u, 0u}, n[2], p;
    start(&duel, 100, 140);
    for (step = 0u; step < 30000u; ++step) {
        if (step % 600u == 599u) start(&duel, 100, 140);
        for (p = 0u; p < 2u; ++p) {
            seed = seed * 1103515245u + 12345u;
            if (!((seed >> 16) % 6u)) k[p] = keys[(seed >> 20) % 9u];
            n[p] = (seed >> 8) % 3u ? NONE : (uint8_t)((seed >> 24) % MOF_DUEL_NORMALS_PER_FIGHTER);
        }
        mof_duel_step_normal(&duel, k[0], k[1], n[0], n[1]);
        /* Only a knockdown lifts the stand-only body, and it lands before rising. */
        if (duel.body[0].motion.mode == MOF_MOTION_AIR || duel.body[0].y_offset)
            assert(duel.fighters[0].state == MOF_DUEL_FALL);
        assert(duel.body[0].motion.mode != MOF_MOTION_CROUCH);
        if (duel.fighters[0].state == MOF_DUEL_ATTACK) {
            assert(STAND_OWNS & MOF_MOVE_BIT(duel.fighters[0].standing_normal));
            ++attacks;
        }
        hits += duel.fighters[0].contact == MOF_DUEL_LANDED;
        for (p = 0u; p < 2u; ++p)
            assert(duel.fighters[p].x >= 16 && duel.fighters[p].x <= 239);
    }
    assert(attacks > 1000u && hits > 20u);
}

/* Commands come from the record, in order, relative to facing. */
static void commands_come_from_the_record(void)
{
    static const MofCommand gesture_first[] = {
        {3u, MOF_CMD_FORWARD | MOF_DUEL_ONE, MOF_CMD_GESTURE},
        {MOF_DUEL_SPECIAL, MOF_CMD_FORWARD | MOF_DUEL_ONE, MOF_CMD_AFTER_DOWN},
        {MOF_DUEL_NO_NORMAL, 0u, 0u}
    };
    MofFighterDef gesture_record = stand_only;
    MofDuelFighter alis = {0}, stand = {0};
    const uint8_t r = MOF_DUEL_RIGHT, l = MOF_DUEL_LEFT, a = MOF_DUEL_ONE, b = MOF_DUEL_TWO;
    alis.def = &mof_fighter_alis; alis.face_right = 1u;
    stand.def = &stand_only; stand.face_right = 1u;
    assert(mof_duel_command(&alis, r | a | b, 0u, 0u, 0u) == MOF_DUEL_THROW);
    assert(mof_duel_command(&alis, r | a | b, a, 0u, 0u) == NONE);      /* stale button */
    assert(mof_duel_command(&alis, r | a, 0u, 1u, 0u) == MOF_DUEL_SPECIAL);
    assert(mof_duel_command(&alis, r | a, 0u, 0u, 0u) == NONE);         /* no down window */
    assert(mof_duel_command(&alis, l | a, 0u, 1u, 0u) == NONE);         /* back is not forward */
    alis.face_right = 0u;
    assert(mof_duel_command(&alis, l | a, 0u, 1u, 0u) == MOF_DUEL_SPECIAL);
    assert(mof_duel_command(&stand, r | a | b, 0u, 0u, 0u) == NONE);    /* no throw in its list */
    gesture_record.commands = gesture_first;
    stand.def = &gesture_record;
    assert(mof_duel_command(&stand, r | a, 0u, 1u, 1u) == 3u);          /* gesture wins first */
    assert(mof_duel_command(&stand, r | a, 0u, 1u, 0u) == MOF_DUEL_SPECIAL);
}

int main(void)
{
    refuses_missing_or_partial_records();
    bodies_follow_their_records();
    moves_belong_to_their_owner();
    contact_reads_the_attacker_record();
    specials_advance_by_record();
    random_play_keeps_capabilities();
    commands_come_from_the_record();
    puts("roster: two records, own bodies, own moves, own contacts, own specials, random play, own commands\n");
    return 0;
}
