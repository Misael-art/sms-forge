#include <assert.h>
#include <stdio.h>
#include "../inc/duel_rules.h"

static const MofDuelGeometry geometry[2] = {
    {{-11,-57,12,-4}, {{9,-23,25,-2},{9,-23,25,-2}}},
    {{-11,-53,13,-3}, {{17,-37,55,-34},{17,-37,55,-34}}}
};

static void run_jump(int16_t start, int16_t rival, uint8_t direction, int expected_cross)
{
    MofDuel duel;
    int8_t apex = 0, previous = 0;
    uint8_t tick, airborne = 0, turned = 0;
    uint8_t start_right = start < rival;

    assert(mof_duel_init(&duel, geometry, 6, MOF_DUEL_ALIS, start, rival, 32, 223, 24));
    for (tick = 0; tick < 35; ++tick) {
        mof_duel_step(&duel, MOF_DUEL_UP | direction, 0);
        if (duel.body[0].y_offset < 0) {
            ++airborne;
            if (airborne <= 3) {
                static const int8_t impulse[] = {-14, -13, -12};
                assert(duel.body[0].y_offset - previous == impulse[airborne - 1]);
            }
            if (duel.body[0].y_offset < apex) apex = duel.body[0].y_offset;
        }
        if (duel.body[0].y_offset > -65)
            assert(duel.fighters[0].x <= rival - 24 || duel.fighters[0].x >= rival + 24);
        if (duel.fighters[0].face_right != start_right) turned = 1;
        assert(duel.fighters[0].x >= 32 && duel.fighters[0].x <= 223);
        previous = duel.body[0].y_offset;
    }
    assert(apex == -78 && airborne == 20 && duel.body[0].y_offset == 0);
    assert(turned == expected_cross);
    if (!direction) assert(duel.fighters[0].x == start);
    if (expected_cross) {
        assert(duel.fighters[0].face_right != start_right);
        assert(duel.fighters[1].face_right == start_right);
        if (start_right) assert(duel.fighters[0].x >= rival + 24);
        else assert(duel.fighters[0].x <= rival - 24);
    }
}

int main(void)
{
    run_jump(111, 144, 0, 0);
    run_jump(111, 144, MOF_DUEL_RIGHT, 1);
    run_jump(144, 111, MOF_DUEL_LEFT, 1);
    run_jump(69, 144, MOF_DUEL_RIGHT, 0);
    run_jump(181, 214, MOF_DUEL_RIGHT, 0);
    run_jump(74, 41, MOF_DUEL_LEFT, 0);
    puts("PASS impulse, apex, landing, crossing on both faces, late approach and walls");
    return 0;
}
