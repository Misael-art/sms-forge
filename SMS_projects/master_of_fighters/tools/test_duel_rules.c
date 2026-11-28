/* Comparison fixtures for Scene 02. The boxes use synthetic coordinates. */
#include <assert.h>
#include <stdio.h>
#include "../inc/duel_rules.h"

static const MofDuelGeometry fixture[2] = {
    {{-8,-45,8,-2}, {{0,-20,25,-4},{0,-20,25,-4}}},
    {{-8,-45,8,-2}, {{0,-32,43,-24},{0,-32,43,-24}}}
};

static void step(MofDuel *duel, uint8_t h, uint8_t a)
{
    if (duel->fighters[0].fighter == MOF_DUEL_HAYATO) {
        mof_duel_step(duel, h, a);
    } else {
        mof_duel_step(duel, a, h);
    }
}

static void run(uint8_t threshold, uint8_t hayato_player, uint8_t hayato_left,
                int16_t gap, uint8_t guard, uint8_t corner)
{
    MofDuel duel;
    MofDuelFighter *h = &duel.fighters[hayato_player];
    MofDuelFighter *a = &duel.fighters[1u-hayato_player];
    uint8_t back = hayato_left ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t expected_hit = gap <= 32;
    uint16_t h_start, h_contact = UINT16_MAX, a_contact = UINT16_MAX;
    unsigned int i, h_landings = 0u, a_landings = 0u;
    int16_t hx = hayato_left ? 80 : 176;
    int16_t ax = hx + (hayato_left ? gap : -gap);
    if (corner) {
        ax = hayato_left ? 228 : 28;
        hx = ax + (hayato_left ? -gap : gap);
    }
    assert(mof_duel_init(&duel, fixture, threshold, hayato_player,
                         hayato_player ? ax : hx, hayato_player ? hx : ax, 28, 228, 20));
    for (i = 1u; i < threshold; ++i) {
        step(&duel, MOF_DUEL_ONE, 0u);
        assert(h->state == MOF_DUEL_READY);
    }
    step(&duel, MOF_DUEL_ONE, 0u);
    assert(h->state == MOF_DUEL_ATTACK);
    h_start = duel.tick;
    for (i = 1u; i <= 10u; ++i) {
        step(&duel, MOF_DUEL_ONE, guard && i == 9u ? back : 0u);
        if (h->contact != MOF_DUEL_NO_CONTACT) {
            assert(duel.tested_active[hayato_player]);
            assert(duel.tested_pose[hayato_player] == 3u);
            if (expected_hit) {
                assert(i == 9u);
                assert(h->contact == (guard ? MOF_DUEL_GUARDED : MOF_DUEL_LANDED));
            } else {
                assert(i == 10u && h->contact == MOF_DUEL_MISSED);
            }
            h_contact = duel.tick;
            ++h_landings;
        }
    }
    assert(h_landings == 1u);
    assert(a->life == (expected_hit && !guard ? 88u : 100u));
    assert(a->x == ax + (expected_hit && !corner ? (hayato_left ? 1 : -1)*(guard ? 3 : 4) : 0));
    if (guard || !expected_hit) {
        if (guard) step(&duel, MOF_DUEL_ONE, 0u);
        for (i = 0u; i < 20u; ++i) {
            step(&duel, MOF_DUEL_ONE, MOF_DUEL_ONE);
            if (a->contact == MOF_DUEL_LANDED) {
                ++a_landings;
                a_contact = duel.tick;
                assert(duel.tested_active[1u-hayato_player] && duel.tested_pose[1u-hayato_player] == 2u);
            }
        }
        assert(a_landings == 1u && h->life == 90u);
        if (guard) {
            assert(a_contact - h_start == (threshold == 6u ? 22 : 24));
            assert(a->free_since == h_start + 12u);
        } else {
            assert(a_contact - h_start == (threshold == 6u ? 21 : 23));
        }
        assert(a_contact < h_start + 25);
    } else {
        assert(a->state == MOF_DUEL_HIT);
        for (i = 0u; i < 20u; ++i) step(&duel, MOF_DUEL_ONE, 0u);
        assert(a->free_since == h_contact + 8u);
        assert(h->free_since == h_start + 25u && h->state == MOF_DUEL_READY);
    }
    for (i = 0u; i < 20u; ++i) step(&duel, MOF_DUEL_ONE, 0u);
    assert(h->state == MOF_DUEL_READY && h->latched);
    if (a_contact != UINT16_MAX) assert(h->free_since == a_contact + 8u);
    step(&duel, 0u, 0u);
    {
        int16_t previous = h->x;
        step(&duel, hayato_left ? MOF_DUEL_LEFT : MOF_DUEL_RIGHT, 0u);
        assert(h->x == previous + (hayato_left ? -1 : 1));
    }
    for (i = 0u; i < threshold; ++i) step(&duel, MOF_DUEL_ONE, 0u);
    assert(h->state == MOF_DUEL_ATTACK);
}

static void overlapping_attacks(uint8_t threshold)
{
    MofDuel duel;
    unsigned int delay, i;
    for (delay = 4u; delay <= 7u; delay += 3u) {
        assert(mof_duel_init(&duel, fixture, threshold, MOF_DUEL_HAYATO, 70, 130, 28, 228, 20));
        for (i = 0u; i < threshold + 9u; ++i)
            step(&duel, MOF_DUEL_ONE, i >= delay ? MOF_DUEL_ONE : 0u);
        assert(duel.tested_pose[0] == 3u);
        assert(duel.tested_pose[1] == (delay == 4u ? 2u : 1u));
    }
}

#if defined(MOF_DUEL_SCENE_CROSSOVER) && defined(MOF_DUEL_SCENE_POSTURES)
static void mixed_jump_input(void)
{
    MofDuel duel;
    const uint8_t retreat_jump = MOF_DUEL_ONE | MOF_DUEL_UP | MOF_DUEL_LEFT;
    const uint8_t sword = MOF_DUEL_ONE | MOF_DUEL_LEFT;
    unsigned int i, trial, takeoffs;
    uint8_t was_airborne, airborne, peak;
    for (trial = 0u; trial < 4u; ++trial) {
        assert(mof_duel_init(&duel, fixture, 6u, MOF_DUEL_ALIS, 160, 200, 32, 223, 24));
        for (i = 0u; i < 8u; ++i) step(&duel, 0u, sword);
        assert(duel.fighters[0].state == MOF_DUEL_ATTACK);
        takeoffs = was_airborne = peak = 0u;
        for (i = 0u; i < 49u; ++i) {
            uint8_t keys = retreat_jump;
            if (trial == 1u && i >= 3u) keys = sword;
            if (trial == 2u && i < 12u) keys = sword;
            if (trial == 2u && i >= 14u) keys = sword;
            if (trial == 3u && i >= 3u) keys = sword | MOF_DUEL_DOWN;
            step(&duel, 0u, keys);
            airborne = duel.body[0].motion.mode == MOF_MOTION_AIR;
            if (airborne && !was_airborne) {
                ++takeoffs;
                assert(duel.tick == duel.fighters[0].free_since + 2u);
                assert(duel.body[0].motion.vx == -96);
            }
            if (-duel.body[0].y_offset > peak) peak = (uint8_t)-duel.body[0].y_offset;
            was_airborne = airborne;
        }
        assert(takeoffs == (trial == 0u || trial == 2u));
        assert(peak == (takeoffs ? 78u : 0u) && !was_airborne);
        step(&duel, 0u, 0u);
        for (i = 0u; i < 3u; ++i) step(&duel, 0u, MOF_DUEL_UP);
        assert(duel.body[0].y_offset == -14 && duel.body[0].motion.vx == 0);
    }
    puts("PASS held, expired, buffered-release and cancelled jump edges during sword recovery");
}
#endif

int main(void)
{
    uint8_t threshold, player, side;
    unsigned int total = 0;
    for (threshold = 6u; threshold <= 8u; threshold += 2u) {
        overlapping_attacks(threshold);
        for (player = 0u; player < 2u; ++player) {
            for (side = 0u; side < 2u; ++side) {
                run(threshold,player,side,28,0u,0u);
                run(threshold,player,side,32,0u,0u);
                run(threshold,player,side,33,0u,0u);
                run(threshold,player,side,32,1u,0u);
                run(threshold,player,side,32,1u,1u);
                total += 5u;
            }
        }
    }
    printf("PASS %u combat fixtures and four simultaneous-pose fixtures (native C; synthetic geometry)\n", total);
#if defined(MOF_DUEL_SCENE_CROSSOVER) && defined(MOF_DUEL_SCENE_POSTURES)
    mixed_jump_input();
#endif
    return 0;
}
