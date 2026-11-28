#ifndef MOF_DUEL_MOTION_H
#define MOF_DUEL_MOTION_H

#include <stdint.h>

/* Signed Q12.4 positions and steps. Convert to pixels at publication. */
#define MOF_MOTION_UNIT 16

enum MofMotionMode {
    MOF_MOTION_IDLE, MOF_MOTION_WALK, MOF_MOTION_CROUCH, MOF_MOTION_DASH,
    MOF_MOTION_RUN, MOF_MOTION_BRAKE, MOF_MOTION_BACKSTEP, MOF_MOTION_AIR
};

enum MofMotionEvent {
    MOF_MOTION_LAUNCHED = 1, MOF_MOTION_APEX = 2, MOF_MOTION_LANDED = 4
};

enum MofGuard {
    MOF_GUARD_OPEN, MOF_GUARD_STANDING, MOF_GUARD_CROUCHING, MOF_GUARD_AIRBORNE
};

enum MofAttackHeight {
    MOF_HEIGHT_MIDDLE, MOF_HEIGHT_LOW, MOF_HEIGHT_OVERHEAD, MOF_HEIGHT_THROW
};

typedef struct {
    /* Positive Q12.4 magnitudes, except duration and double-tap fields. */
    uint8_t walk_forward, walk_back, dash_speed, run_speed, brake_step;
    uint8_t backstep_speed, jump_horizontal, jump_vertical, gravity;
    uint8_t dash_ticks, backstep_ticks, tap_window;
} MofDuelMotionProfile;

typedef struct {
    int16_t x, y, vx, vy;
    uint8_t mode, ticks_left, tap_left, tap_key;
    uint8_t previous_horizontal, previous_up, previous_face;
} MofDuelMotion;

void mof_duel_motion_reset(MofDuelMotion *motion, int16_t x, uint8_t face_right);
uint8_t mof_duel_motion_read(MofDuelMotion *motion, const MofDuelMotionProfile *profile,
                              uint8_t keys, uint8_t face_right, uint8_t free_in_round,
                              int16_t left, int16_t right);
uint8_t mof_duel_motion_posture(const MofDuelMotion *motion);
uint8_t mof_duel_motion_can_act(const MofDuelMotion *motion);
uint8_t mof_duel_guard(uint8_t keys, uint8_t face_right, uint8_t posture, uint8_t can_guard);
uint8_t mof_duel_guard_blocks(uint8_t guard, uint8_t height, uint8_t air_blockable,
                              uint8_t ground_anti_air);

#endif
