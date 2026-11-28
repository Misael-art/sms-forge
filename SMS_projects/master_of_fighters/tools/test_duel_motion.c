#include <assert.h>
#include <stdio.h>
#include "../inc/duel_motion.h"
#include "../inc/duel_commands.h"

#define PX(n) ((n) * MOF_MOTION_UNIT)
#define LOW MOF_DUEL_DOWN

static const MofDuelMotionProfile trial[] = {
    {16,12,40,44,11,28,16,54,6,5,4,8},
    {14,14,36,40,20,32,15,54,6,5,4,8}
};

static uint8_t read_motion(MofDuelMotion *motion, const MofDuelMotionProfile *profile,
                           uint8_t keys, uint8_t face_right, uint8_t free_in_round)
{
    return mof_duel_motion_read(motion, profile, keys, face_right, free_in_round, PX(24), PX(232));
}

static unsigned int walk_32(const MofDuelMotionProfile *p, uint8_t face, uint8_t toward)
{
    MofDuelMotion m;
    unsigned int count = 0u;
    uint8_t key = face == toward ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    int16_t target = key == MOF_DUEL_RIGHT ? PX(152) : PX(88);
    mof_duel_motion_reset(&m, PX(120), face);
    while ((key == MOF_DUEL_RIGHT ? m.x < target : m.x > target) && count < 128u) {
        read_motion(&m, p, key, face, 1u);
        assert(mof_duel_motion_can_act(&m));
        ++count;
    }
    assert(count < 128u);
    return count;
}

static void test_double_tap(const MofDuelMotionProfile *p, uint8_t face)
{
    MofDuelMotion m;
    unsigned int i, brake;
    uint8_t forward = face ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t back = face ? MOF_DUEL_LEFT : MOF_DUEL_RIGHT;
    int16_t start;
    int16_t sign = face ? 1 : -1;

    mof_duel_motion_reset(&m, PX(120), face);
    read_motion(&m, p, forward, face, 1u);
    for (i = 1u; i < p->tap_window; ++i) read_motion(&m, p, 0u, face, 1u);
    start = m.x;
    read_motion(&m, p, forward, face, 1u);
    assert(m.mode == MOF_MOTION_DASH);
    for (i = 1u; i < p->dash_ticks; ++i) read_motion(&m, p, forward, face, 1u);
    assert(m.x - start == sign * p->dash_ticks * p->dash_speed);
    read_motion(&m, p, forward, face, 1u);
    assert(m.mode == MOF_MOTION_RUN && m.vx == sign * p->run_speed);
    for (brake = 0u; !mof_duel_motion_can_act(&m) && brake < 16u; ++brake) {
        read_motion(&m, p, 0u, face, 1u);
    }
    assert(brake == (unsigned int)(p->run_speed + p->brake_step - 1u) / p->brake_step);
    assert(m.vx == 0);

    mof_duel_motion_reset(&m, PX(120), face);
    read_motion(&m, p, forward, face, 1u);
    for (i = 0u; i < p->tap_window; ++i) read_motion(&m, p, 0u, face, 1u);
    read_motion(&m, p, forward, face, 1u);
    assert(m.mode == MOF_MOTION_WALK);
    read_motion(&m, p, 0u, face, 1u);
    read_motion(&m, p, forward, !face, 1u);
    assert(m.mode == MOF_MOTION_WALK); /* A tap from the previous face cannot complete an edge. */

    mof_duel_motion_reset(&m, PX(120), face);
    read_motion(&m, p, back, face, 1u);
    read_motion(&m, p, 0u, face, 1u);
    start = m.x;
    read_motion(&m, p, back, face, 1u);
    assert(m.mode == MOF_MOTION_BACKSTEP);
    for (i = 1u; i < p->backstep_ticks; ++i) read_motion(&m, p, 0u, face, 1u);
    assert(m.x - start == -sign * p->backstep_ticks * p->backstep_speed);
    read_motion(&m, p, 0u, face, 1u);
    assert(m.mode == MOF_MOTION_IDLE && mof_duel_motion_can_act(&m));
}

static void test_jump(const MofDuelMotionProfile *p, uint8_t face, uint8_t direction)
{
    MofDuelMotion m;
    uint8_t back = face ? MOF_DUEL_LEFT : MOF_DUEL_RIGHT;
    uint8_t event, apex = 0u, landed = 0u;
    unsigned int tick;
    mof_duel_motion_reset(&m, PX(120), face);
    event = read_motion(&m, p, MOF_DUEL_UP | direction, face, 1u);
    assert(event == MOF_MOTION_LAUNCHED && m.y < 0);
    for (tick = 1u; tick < 64u; ++tick) {
        event = read_motion(&m, p, MOF_DUEL_UP | back, face, 1u);
        if (event == MOF_MOTION_APEX) {
            assert(mof_duel_guard(back, face, mof_duel_motion_posture(&m), 1u) ==
                   MOF_GUARD_AIRBORNE);
            assert(mof_duel_guard(back, !face, mof_duel_motion_posture(&m), 1u) ==
                   MOF_GUARD_OPEN);
            ++apex;
        }
        if (event == MOF_MOTION_LANDED) {
            assert(mof_duel_guard(back, face, mof_duel_motion_posture(&m), 1u) ==
                   MOF_GUARD_STANDING);
            assert(mof_duel_motion_can_act(&m));
            ++landed;
            break;
        }
    }
    assert(apex == 1u && landed == 1u);
    assert(direction == 0u ? m.x == PX(120) :
           (direction == MOF_DUEL_LEFT ? m.x < PX(120) : m.x > PX(120)));
    assert(read_motion(&m, p, MOF_DUEL_UP, face, 1u) == 0u);
}

static void test_guards(void)
{
    assert(mof_duel_guard(LOW | MOF_DUEL_LEFT, 1u, MOF_INPUT_CROUCHING, 1u) == MOF_GUARD_CROUCHING);
    assert(mof_duel_guard(LOW | MOF_DUEL_RIGHT, 0u, MOF_INPUT_CROUCHING, 1u) == MOF_GUARD_CROUCHING);
    assert(mof_duel_guard(LOW | MOF_DUEL_LEFT | MOF_DUEL_RIGHT, 0u, MOF_INPUT_CROUCHING, 1u) == MOF_GUARD_OPEN);
    assert(mof_duel_guard(MOF_DUEL_RIGHT, 0u, MOF_INPUT_AIRBORNE, 0u) == MOF_GUARD_OPEN);
    assert(mof_duel_guard_blocks(MOF_GUARD_STANDING, MOF_HEIGHT_MIDDLE, 0u, 0u));
    assert(mof_duel_guard_blocks(MOF_GUARD_STANDING, MOF_HEIGHT_OVERHEAD, 0u, 0u));
    assert(!mof_duel_guard_blocks(MOF_GUARD_STANDING, MOF_HEIGHT_LOW, 0u, 0u));
    assert(mof_duel_guard_blocks(MOF_GUARD_CROUCHING, MOF_HEIGHT_LOW, 0u, 0u));
    assert(!mof_duel_guard_blocks(MOF_GUARD_CROUCHING, MOF_HEIGHT_OVERHEAD, 0u, 0u));
    assert(!mof_duel_guard_blocks(MOF_GUARD_CROUCHING, MOF_HEIGHT_THROW, 1u, 0u));
    assert(mof_duel_guard_blocks(MOF_GUARD_AIRBORNE, MOF_HEIGHT_MIDDLE, 1u, 0u));
    assert(!mof_duel_guard_blocks(MOF_GUARD_AIRBORNE, MOF_HEIGHT_MIDDLE, 1u, 1u));
    assert(!mof_duel_guard_blocks(MOF_GUARD_AIRBORNE, MOF_HEIGHT_MIDDLE, 0u, 0u));
}

static void test_low_guard_on_landing(void)
{
    MofDuelMotion m;
    unsigned int tick;
    mof_duel_motion_reset(&m, PX(120), 1u);
    read_motion(&m, &trial[0], MOF_DUEL_UP, 1u, 1u);
    for (tick = 0u; tick < 64u; ++tick) {
        if (read_motion(&m, &trial[0], LOW | MOF_DUEL_LEFT, 1u, 1u) != MOF_MOTION_LANDED)
            continue;
        assert(mof_duel_guard(LOW | MOF_DUEL_LEFT, 1u, mof_duel_motion_posture(&m), 1u) ==
               MOF_GUARD_CROUCHING);
        return;
    }
    assert(0 && "Jump failed to reach the first grounded tick");
}

int main(void)
{
    unsigned int f, face;
    test_guards();
    test_low_guard_on_landing();
    for (f = 0u; f < 2u; ++f) {
        const MofDuelMotionProfile *p = &trial[f];
        unsigned int advance = walk_32(p, 1u, 1u);
        unsigned int retreat = walk_32(p, 1u, 0u);
        assert(advance == (f ? 37u : 32u));
        assert(retreat == (f ? 37u : 43u));
        assert(walk_32(p, 0u, 1u) == advance && walk_32(p, 0u, 0u) == retreat);
        for (face = 0u; face < 2u; ++face) {
            test_double_tap(p, (uint8_t)face);
            test_jump(p, (uint8_t)face, 0u);
            test_jump(p, (uint8_t)face, MOF_DUEL_LEFT);
            test_jump(p, (uint8_t)face, MOF_DUEL_RIGHT);
        }
        printf("%s 32px forward=%u ticks back=%u ticks; dash=%u/16 px; run=%u/16 px/tick; brake=%u ticks\n",
               f ? "Alis" : "Hayato", advance, retreat, p->dash_ticks * p->dash_speed, p->run_speed,
               (p->run_speed + p->brake_step - 1u) / p->brake_step);
    }
    puts("PASS mirrored movement, dash expiry, brake, backstep, apex and first grounded guard.");
    return 0;
}
