/* Host fixtures for the input reader, independent of move and guard policy. */
#include <assert.h>
#include <stdio.h>
#include "../inc/duel_commands.h"

#define D MOF_DUEL_DOWN
#define L MOF_DUEL_LEFT
#define R MOF_DUEL_RIGHT
#define U MOF_DUEL_UP
#define A MOF_DUEL_ONE
#define B MOF_DUEL_TWO
#define BOTH (A | B)
#define LOW MOF_INPUT_CROUCHING
#define AIR MOF_INPUT_AIRBORNE
#define STAND MOF_INPUT_STANDING
#define SHORT_2_LOW MOF_INPUT_NORMAL(LOW, MOF_INPUT_SHORT_TWO)
#define BOTH_SHORT_LOW (MOF_INPUT_NORMAL(LOW, MOF_INPUT_SHORT_ONE) | SHORT_2_LOW)

static void compare_chords(uint8_t staggered)
{
    const MofDuelCommandProfile profile = {{6u,8u}, staggered};
    MofDuelCommands input;
    uint8_t first;

    mof_duel_commands_reset(&input, 0u);
    assert(mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1u) == MOF_INPUT_TAUNT);
    assert(!mof_duel_commands_read(&input, &profile, D, LOW, 1u));

    for (first = A; first <= B; first *= 2u) {
        uint8_t second = BOTH ^ first;
        uint16_t actual;
        mof_duel_commands_reset(&input, 0u);
        assert(!mof_duel_commands_read(&input, &profile, D | first, LOW, 1));
        actual = mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1);
        assert(actual == (staggered ? MOF_INPUT_TAUNT : 0u));
        if (staggered) {
            assert(!mof_duel_commands_read(&input, &profile, D | second, LOW, 1));
            assert(!mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1));
            assert(!mof_duel_commands_read(&input, &profile, D | first, LOW, 1));
            assert(!mof_duel_commands_read(&input, &profile, D, LOW, 1));
            assert(mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1) == MOF_INPUT_TAUNT);
        } else {
            assert(mof_duel_commands_read(&input, &profile, D, LOW, 1) == BOTH_SHORT_LOW);
        }
        mof_duel_commands_reset(&input, 0u);
        assert(!mof_duel_commands_read(&input, &profile, D | first, LOW, 1));
        assert(!mof_duel_commands_read(&input, &profile, D | first, LOW, 1));
        assert(!mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1));
        assert(mof_duel_commands_read(&input, &profile, D, LOW, 1) == BOTH_SHORT_LOW);
    }
}

static void test_pure_down_constraints(uint8_t staggered)
{
    const MofDuelCommandProfile profile = {{6u,8u}, staggered};
    const uint8_t direction[] = {0, L, R, U, L | R};
    MofDuelCommands input;
    unsigned int i;
    for (i = 0u; i < sizeof(direction); ++i) {
        mof_duel_commands_reset(&input, 0u);
        assert(!mof_duel_commands_read(&input, &profile, direction[i] | BOTH, LOW, 1u));
        mof_duel_commands_reset(&input, 0u);
        if (direction[i]) {
            assert(!mof_duel_commands_read(&input, &profile, D | direction[i] | BOTH, LOW, 1u));
        }
        /* Down first appearing with the second edge does not qualify. */
        mof_duel_commands_reset(&input, 0u);
        assert(!mof_duel_commands_read(&input, &profile, direction[i] | A, LOW, 1u));
        assert(!mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1u));
    }
    mof_duel_commands_reset(&input, 0u);
    assert(!mof_duel_commands_read(&input, &profile, D | B, LOW, 1u));
    /* Regression: the same one-poll anticipation must preserve a tap on 2. */
    assert(mof_duel_commands_read(&input, &profile, D, LOW, 1u) == SHORT_2_LOW);
    assert(!mof_duel_commands_read(&input, &profile, D, LOW, 1u));
}

static void test_thresholds_and_eligibility(uint8_t staggered)
{
    uint8_t hold, posture, button, tick;
    MofDuelCommands input;
    for (hold = 6u; hold <= 8u; hold += 2u) {
        const MofDuelCommandProfile profile = {{hold, hold}, staggered};
        for (posture = STAND; posture <= AIR; ++posture) {
            for (button = A; button <= B; button *= 2u) {
                uint8_t command = button == A ? MOF_INPUT_LONG_ONE : MOF_INPUT_LONG_TWO;
                mof_duel_commands_reset(&input, 0u);
                for (tick = 1u; tick < hold; ++tick)
                    assert(!mof_duel_commands_read(&input, &profile, button, posture, 1u));
                assert(mof_duel_commands_read(&input, &profile, button, posture, 1u) ==
                       MOF_INPUT_NORMAL(posture, command));
                for (tick = 0u; tick < 16u; ++tick)
                    assert(!mof_duel_commands_read(&input, &profile, button, posture, 1u));
                assert(!mof_duel_commands_read(&input, &profile, 0u, posture, 1u));
                assert(!mof_duel_commands_read(&input, &profile, button, posture, 1u));
                assert(mof_duel_commands_read(&input, &profile, 0u, posture, 1u) ==
                       MOF_INPUT_NORMAL(posture, command - 1u));
            }
        }
        mof_duel_commands_reset(&input, 0u);
        assert(!mof_duel_commands_read(&input, &profile, D | BOTH, AIR, 1u));
        assert(!mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1u));
        assert(!mof_duel_commands_read(&input, &profile, D, LOW, 1u));
        mof_duel_commands_reset(&input, 0u);
        assert(!mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 0u));
        assert(!mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1u));
        assert(!mof_duel_commands_read(&input, &profile, D, LOW, 1u));
        assert(mof_duel_commands_read(&input, &profile, D | BOTH, LOW, 1u) == MOF_INPUT_TAUNT);

        mof_duel_commands_reset(&input, B);
        assert(!mof_duel_commands_read(&input, &profile, D | B, LOW, 1u));
        assert(!mof_duel_commands_read(&input, &profile, D, LOW, 1u));
        assert(!mof_duel_commands_read(&input, &profile, D | B, LOW, 1u));
        assert(mof_duel_commands_read(&input, &profile, D, LOW, 1u) == SHORT_2_LOW);

        /* A genuinely new ground press is allowed on the first ground poll. */
        mof_duel_commands_reset(&input, 0u);
        assert(!mof_duel_commands_read(&input, &profile, A, AIR, 1u));
        assert(!mof_duel_commands_read(&input, &profile, B, STAND, 1u));
        assert(mof_duel_commands_read(&input, &profile, 0u, STAND, 1u) ==
               MOF_INPUT_NORMAL(STAND, MOF_INPUT_SHORT_TWO));
    }
}

int main(void)
{
    uint8_t mode;
    for (mode = 0u; mode < 2u; ++mode) {
        compare_chords(mode);
        test_pure_down_constraints(mode);
        test_thresholds_and_eligibility(mode);
    }
    puts("PASS strict and one-poll taunt, both button orders, solo tap on release,");
    puts("     simultaneous normals, hold 6/8, lockout, landing and release/rearm.");
    return 0;
}
