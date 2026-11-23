/* End-to-end C fixtures for standing commands. New boxes and timing here
 * are synthetic; only the two pilot sequences repeat their recorded timing. */
#include <assert.h>
#include <stdio.h>
#include "../inc/duel_commands.h"

static const MofDuelGeometry geometry[2] = {
    {{-8,-45,8,-2}, {{0,-20,25,-4},{0,-20,25,-4}}},
    {{-8,-45,8,-2}, {{0,-32,43,-24},{0,-32,43,-24}}}
};
static const MofDuelBox fist[] = {{0,-30,14,-12}, {0,-30,14,-12}};
static const MofDuelBox light_kick[] = {{0,-24,20,-13}, {0,-24,20,-13}};
static const MofDuelBox heavy_kick[] = {{0,-29,29,-16}, {0,-29,29,-16}};
static const MofDuelBox cut[] = {{9,-23,25,-2}, {9,-23,25,-2}};
static const MofDuelBox thrust[] = {{17,-43,64,-33}, {17,-43,64,-33}};
static const uint8_t fist_ends[] = {4,6,14}, light_kick_ends[] = {5,7,17};
static const uint8_t heavy_kick_ends[] = {10,12,27};
static const uint8_t cut_ends[] = {8,9,11,18,20,25}, thrust_ends[] = {5,7,18};

#define SPEC(boxes, ends, start, length, dmg) {boxes,ends,start,2,length,dmg,sizeof(ends)}
static const MofDuelStandingNormal normals[2][4] = {
    {SPEC(fist,fist_ends,4,14,5),SPEC(cut,cut_ends,9,25,12),
     SPEC(light_kick,light_kick_ends,5,17,6),SPEC(heavy_kick,heavy_kick_ends,10,27,11)},
    {SPEC(fist,fist_ends,4,14,5),SPEC(thrust,thrust_ends,5,18,10),
     SPEC(light_kick,light_kick_ends,5,17,6),SPEC(heavy_kick,heavy_kick_ends,10,27,11)}
};

static uint8_t one_command(uint16_t flags)
{
    uint8_t i;
    for (i = 0u; i < 4u; ++i) {
        if (flags == MOF_INPUT_NORMAL(MOF_INPUT_STANDING, i)) return i;
    }
    assert(!flags);
    return MOF_DUEL_NO_NORMAL;
}

static void run(uint8_t f, uint8_t id, uint8_t slot, uint8_t face,
                uint8_t hold, uint8_t scenario)
{
    MofDuel duel;
    MofDuelCommands input;
    MofDuelCommandProfile profile = {{hold,hold},0};
    const MofDuelStandingNormal *normal = &normals[f][id];
    uint8_t key = id >= 2u ? MOF_DUEL_TWO : MOF_DUEL_ONE;
    uint8_t presses = (id & 1u) ? hold : 1u;
    int16_t gap = normal->active_boxes[0].right + 7;
    int16_t src = face ? 72 : 183, dst;
    uint16_t start;
    unsigned int i, commits = 0u;
    MofDuelFighter *attacker = &duel.fighters[slot], *defender = &duel.fighters[1u-slot];

    if (scenario == 0u) gap -= 2;
    if (scenario == 2u) ++gap;
    dst = src + (face ? gap : -gap);
    assert(mof_duel_init(&duel, geometry, hold, slot ? 1u-f : f,
                         slot ? dst : src, slot ? src : dst, 20, 235, 10));
    assert(mof_duel_set_standing_normals(&duel, normals));
    mof_duel_commands_reset(&input, 0u);

    for (i = 0u; i < (unsigned int)presses + 1u; ++i) {
        uint8_t keys = i < presses ? key : 0u;
        uint8_t cmd = one_command(mof_duel_commands_read(&input, &profile, keys,
                                                        MOF_INPUT_STANDING,
                                                        mof_duel_next_tick_free(&duel, slot)));
        if (cmd != MOF_DUEL_NO_NORMAL) {
            assert(cmd == id);
            assert(i == (unsigned int)((id & 1u) ? hold-1u : presses));
            ++commits;
        }
        if (slot) mof_duel_step_normal(&duel, 0u, keys, MOF_DUEL_NO_NORMAL, cmd);
        else mof_duel_step_normal(&duel, keys, 0u, cmd, MOF_DUEL_NO_NORMAL);
    }
    assert(commits == 1u && attacker->standing_normal == id);
    start = attacker->state_since;
    commits = 0u;
    for (i = mof_duel_age(&duel, attacker) + 1u; i <= normal->duration; ++i) {
        uint8_t back = scenario == 3u && i == normal->first_active ?
                       (face ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT) : 0u;
        if (slot) mof_duel_step_normal(&duel, back, 0u, MOF_DUEL_NO_NORMAL, MOF_DUEL_NO_NORMAL);
        else mof_duel_step_normal(&duel, 0u, back, MOF_DUEL_NO_NORMAL, MOF_DUEL_NO_NORMAL);
        if (!attacker->contact) continue;
        ++commits;
        assert(duel.tested_active[slot] && duel.tested_pose[slot] != 0u);
        if (scenario == 2u) {
            assert(attacker->contact == MOF_DUEL_MISSED && i == normal->first_active + 1u);
        } else if (scenario == 3u) {
            assert(attacker->contact == MOF_DUEL_GUARDED && i == normal->first_active);
        } else {
            assert(attacker->contact == MOF_DUEL_LANDED && i == normal->first_active);
        }
    }
    assert(commits == 1u && defender->life == (scenario < 2u ? 100u-normal->damage : 100u));
    assert(attacker->state == MOF_DUEL_READY && attacker->free_since == start+normal->duration);
}

int main(void)
{
    uint8_t f,id,slot,face,hold,scenario;
    unsigned int cases = 0u;
    for (f = 0; f < 2u; ++f)
        for (id = 0; id < 4u; ++id)
            for (slot = 0; slot < 2u; ++slot)
                for (face = 0; face < 2u; ++face)
                    for (hold = 6; hold <= 8u; hold += 2u)
                        for (scenario = 0; scenario < 4u; ++scenario) {
                            run(f,id,slot,face,hold,scenario);
                            ++cases;
                        }
    printf("PASS %u standing normal fixtures (synthetic boxes/pose data)\n", cases);
    return 0;
}
