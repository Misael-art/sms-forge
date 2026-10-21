/* Generated from the two scene-cut manifests; do not hand-edit. */
#ifndef FIGHT_RUNTIME_DATA_H
#define FIGHT_RUNTIME_DATA_H
#define FIGHT_RUNTIME_DATA_SCHEMA 5
#define P1_CUT_META_MAX_BYTES 106
#define P2_CUT_META_MAX_BYTES 106
static const CommandDef p1_commands[] = {
    { P1_CUT_CMD_SPECIAL, FIGHT_CMD_SPECIAL_UNSUPPORTED },
    { P1_CUT_CMD_HP, FIGHT_CMD_HP },
    { P1_CUT_CMD_LP, FIGHT_CMD_LP },
    { P1_CUT_CMD_HK, FIGHT_CMD_HK },
    { P1_CUT_CMD_LK, FIGHT_CMD_LK },
};
static const CommandDef p2_commands[] = {
    { P2_CUT_CMD_SPECIAL, FIGHT_CMD_SPECIAL_UNSUPPORTED },
    { P2_CUT_CMD_HP, FIGHT_CMD_HP },
    { P2_CUT_CMD_LP, FIGHT_CMD_LP },
    { P2_CUT_CMD_HK, FIGHT_CMD_HK },
    { P2_CUT_CMD_LK, FIGHT_CMD_LK },
};
#ifndef FIGHT_SOURCE_ROUTE_DEF_DEFINED
#define FIGHT_SOURCE_ROUTE_DEF_DEFINED
typedef struct { const unsigned char *pattern; unsigned short source_state; unsigned short source_action; unsigned char action_anim; } FightSourceRouteDef;
#endif
#define P1_SOURCE_ROUTE_PATTERN_COUNT 13
static const FightSourceRouteDef p1_source_routes[] = {
    { P1_CUT_R_SPEC_834F878D_0, 1000, 1000, P1_CUT_ANIM_SPECIAL },
    { P1_CUT_R_STAN_E9900711_0, 200, 200, P1_CUT_ANIM_PUNCH },
    { P1_CUT_R_STAN_5F3F5843_0, 201, 201, P1_CUT_ANIM_PUNCH_FAR },
    { P1_CUT_R_STAN_FDB8E700_0, 220, 220, P1_CUT_ANIM_HP },
    { P1_CUT_R_STAN_34823DFA_0, 221, 221, P1_CUT_ANIM_HP_FAR },
    { P1_CUT_R_STAN_27EC3C54_0, 230, 230, P1_CUT_ANIM_KICK },
    { P1_CUT_R_STAN_09D0273D_0, 231, 231, P1_CUT_ANIM_KICK_FAR },
    { P1_CUT_R_STAN_FD83A8FC_0, 250, 250, P1_CUT_ANIM_HK },
    { P1_CUT_R_STAN_8E72B206_0, 251, 251, P1_CUT_ANIM_HK_FAR },
    { P1_CUT_R_AIR__6E24E634_0, 600, 600, P1_CUT_ANIM_AIR_LP },
    { P1_CUT_R_AIR__E1AE110C_0, 620, 620, P1_CUT_ANIM_AIR_HP },
    { P1_CUT_R_AIR__CCBC2C90_0, 630, 630, P1_CUT_ANIM_AIR_LK },
    { P1_CUT_R_AIR__72867306_0, 650, 650, P1_CUT_ANIM_AIR_HK },
};
#define P2_SOURCE_ROUTE_PATTERN_COUNT 13
static const FightSourceRouteDef p2_source_routes[] = {
    { P2_CUT_R_SPEC_834F878D_0, 1000, 1000, P2_CUT_ANIM_SPECIAL },
    { P2_CUT_R_STAN_E9900711_0, 200, 200, P2_CUT_ANIM_PUNCH },
    { P2_CUT_R_STAN_5F3F5843_0, 201, 201, P2_CUT_ANIM_PUNCH_FAR },
    { P2_CUT_R_STAN_FDB8E700_0, 220, 220, P2_CUT_ANIM_HP },
    { P2_CUT_R_STAN_34823DFA_0, 221, 221, P2_CUT_ANIM_HP_FAR },
    { P2_CUT_R_STAN_27EC3C54_0, 230, 230, P2_CUT_ANIM_KICK },
    { P2_CUT_R_STAN_09D0273D_0, 231, 231, P2_CUT_ANIM_KICK_FAR },
    { P2_CUT_R_STAN_FD83A8FC_0, 250, 250, P2_CUT_ANIM_HK },
    { P2_CUT_R_STAN_8E72B206_0, 251, 251, P2_CUT_ANIM_HK_FAR },
    { P2_CUT_R_AIR__6E24E634_0, 600, 600, P2_CUT_ANIM_AIR_LP },
    { P2_CUT_R_AIR__E1AE110C_0, 620, 620, P2_CUT_ANIM_AIR_HP },
    { P2_CUT_R_AIR__CCBC2C90_0, 630, 630, P2_CUT_ANIM_AIR_LK },
    { P2_CUT_R_AIR__72867306_0, 650, 650, P2_CUT_ANIM_AIR_HK },
};
static const unsigned short p1_close_distances_q8[AT_N] = { 0, 0, 0, 0 };
static const unsigned short p2_close_distances_q8[AT_N] = { 0, 0, 0, 0 };
static const unsigned short p1_far_distances_q8[AT_N] = { 5512, 5512, 5512, 5512 };
static const unsigned short p2_far_distances_q8[AT_N] = { 5512, 5512, 5512, 5512 };
static const StateDef p1_states[ST_N_STATES] = {
    { 65535, P1_CUT_ANIM_IDLE, S_CONTROL, 0, 0 },
    { 65535, P1_CUT_ANIM_WALK_F, S_CONTROL, 512, 0 },
    { 65535, P1_CUT_ANIM_WALK_B, S_CONTROL, -460, 0 },
    { 65535, P1_CUT_ANIM_JUMP, S_AIR, 0, 0 },
    { 65535, P1_CUT_ANIM_CROUCH, S_CONTROL | S_BLOCKABLE, 0, 0 },
    { 65535, P1_CUT_ANIM_GUARD, S_CONTROL | S_BLOCKABLE, 0, 0 },
    { 200, P1_CUT_ANIM_PUNCH, S_HIT, 0, 30 },
    { 220, P1_CUT_ANIM_HP, S_HIT, 0, 20 },
    { 1000, P1_CUT_ANIM_SPECIAL, 0, 0, 0 },
    { 5050, P1_CUT_ANIM_KO, 0, 0, 0 },
    { 230, P1_CUT_ANIM_KICK, S_HIT, 0, 35 },
    { 250, P1_CUT_ANIM_HK, S_HIT, 0, 80 },
    { 65535, P1_CUT_ANIM_PUNCH, 0, 0, 0 },
    { 65535, P1_CUT_ANIM_HP, 0, 0, 0 },
    { 65535, P1_CUT_ANIM_KICK, 0, 0, 0 },
    { 65535, P1_CUT_ANIM_HK, 0, 0, 0 },
    { 201, P1_CUT_ANIM_PUNCH_FAR, S_HIT, 0, 30 },
    { 221, P1_CUT_ANIM_HP_FAR, S_HIT, 0, 62 },
    { 231, P1_CUT_ANIM_KICK_FAR, S_HIT, 0, 35 },
    { 251, P1_CUT_ANIM_HK_FAR, S_HIT, 0, 80 },
};
static const StateDef p2_states[ST_N_STATES] = {
    { 65535, P2_CUT_ANIM_IDLE, S_CONTROL, 0, 0 },
    { 65535, P2_CUT_ANIM_WALK_F, S_CONTROL, 512, 0 },
    { 65535, P2_CUT_ANIM_WALK_B, S_CONTROL, -460, 0 },
    { 65535, P2_CUT_ANIM_JUMP, S_AIR, 0, 0 },
    { 65535, P2_CUT_ANIM_CROUCH, S_CONTROL | S_BLOCKABLE, 0, 0 },
    { 65535, P2_CUT_ANIM_GUARD, S_CONTROL | S_BLOCKABLE, 0, 0 },
    { 200, P2_CUT_ANIM_PUNCH, S_HIT, 0, 30 },
    { 220, P2_CUT_ANIM_HP, S_HIT, 0, 20 },
    { 1000, P2_CUT_ANIM_SPECIAL, 0, 0, 0 },
    { 5050, P2_CUT_ANIM_KO, 0, 0, 0 },
    { 230, P2_CUT_ANIM_KICK, S_HIT, 0, 35 },
    { 250, P2_CUT_ANIM_HK, S_HIT, 0, 80 },
    { 65535, P2_CUT_ANIM_PUNCH, 0, 0, 0 },
    { 65535, P2_CUT_ANIM_HP, 0, 0, 0 },
    { 65535, P2_CUT_ANIM_KICK, 0, 0, 0 },
    { 65535, P2_CUT_ANIM_HK, 0, 0, 0 },
    { 201, P2_CUT_ANIM_PUNCH_FAR, S_HIT, 0, 30 },
    { 221, P2_CUT_ANIM_HP_FAR, S_HIT, 0, 62 },
    { 231, P2_CUT_ANIM_KICK_FAR, S_HIT, 0, 35 },
    { 251, P2_CUT_ANIM_HK_FAR, S_HIT, 0, 80 },
};
static const CharacterData characters[2] = {
    { p1_frames_all, p1_anims, p1_states, p1_commands, 5, P1_CUT_POSE_COUNT, P1_POSE_BASE, 106, 1000, 2585, 110, 8, 3, 5, p1_close_distances_q8, p1_far_distances_q8, 3101 },
    { p2_frames_all, p2_anims, p2_states, p2_commands, 5, P2_CUT_POSE_COUNT, P2_POSE_BASE, 106, 1000, 2585, 110, 8, 3, 5, p2_close_distances_q8, p2_far_distances_q8, 3101 },
};
#endif /* FIGHT_RUNTIME_DATA_H */
