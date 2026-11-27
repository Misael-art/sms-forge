static int16_t velocity(uint8_t direction, uint8_t speed)
{
    if (direction == MOF_DUEL_LEFT) return -(int16_t)speed;
    return direction == MOF_DUEL_RIGHT ? (int16_t)speed : 0;
}

static uint8_t move_air(MofDuelMotion *motion, uint8_t gravity)
{
    int16_t previous_vy = motion->vy;
    motion->y += motion->vy;
    motion->vy += gravity;
    if (motion->y >= 0) {
        motion->y = motion->vy = 0;
        motion->mode = MOF_MOTION_IDLE;
        return MOF_MOTION_LANDED;
    }
    return previous_vy < 0 && motion->vy >= 0 ? MOF_MOTION_APEX : 0u;
}

static void brake(MofDuelMotion *motion, uint8_t step)
{
    if (motion->vx > step) motion->vx -= step;
    else if (motion->vx < -(int16_t)step) motion->vx += step;
    else {
        motion->vx = 0;
        motion->mode = MOF_MOTION_IDLE;
    }
}

uint8_t mof_duel_motion_read(MofDuelMotion *motion, const MofDuelMotionProfile *profile,
                              uint8_t keys, uint8_t face_right, uint8_t free_in_round,
                              int16_t left, int16_t right)
{
    uint8_t direction = horizontal(keys);
    uint8_t forward = face_right ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t up = (keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)) == MOF_DUEL_UP;
    uint8_t rising_up = up && !motion->previous_up;
    uint8_t rising_direction = direction && !motion->previous_horizontal;
    uint8_t event = 0u;
    int16_t position;

    motion->previous_horizontal = direction;
    motion->previous_up = up;
    if (motion->previous_face != face_right) motion->tap_left = 0u;
    motion->previous_face = face_right;
    if (motion->tap_left) --motion->tap_left;

    if (motion->mode == MOF_MOTION_AIR) {
        event = move_air(motion, profile->gravity);
    } else if (!free_in_round) {
        motion->mode = MOF_MOTION_IDLE;
        motion->tap_left = motion->ticks_left = 0u;
        motion->vx = 0;
    } else if (motion->mode == MOF_MOTION_RUN || motion->mode == MOF_MOTION_BRAKE) {
        if (motion->mode == MOF_MOTION_RUN && direction == forward &&
            velocity(direction, profile->run_speed) == motion->vx) {
            /* Keep run velocity while the same physical direction is held. */
        } else {
            motion->mode = MOF_MOTION_BRAKE;
            brake(motion, profile->brake_step);
        }
    } else if (motion->ticks_left) {
        --motion->ticks_left;
    } else if (motion->mode == MOF_MOTION_DASH &&
               direction == forward && velocity(direction, profile->dash_speed) == motion->vx) {
        motion->mode = MOF_MOTION_RUN;
        motion->vx = velocity(direction, profile->run_speed);
    } else if (motion->mode == MOF_MOTION_BACKSTEP) {
        motion->mode = MOF_MOTION_IDLE;
        motion->vx = 0;
    } else if (rising_up && profile->jump_vertical && profile->gravity) {
        motion->mode = MOF_MOTION_AIR;
        motion->tap_left = 0u;
        motion->vx = velocity(direction, profile->jump_horizontal);
        motion->vy = -(int16_t)profile->jump_vertical;
        event = MOF_MOTION_LAUNCHED | move_air(motion, profile->gravity);
    } else if (keys & MOF_DUEL_DOWN) {
        motion->mode = MOF_MOTION_CROUCH;
        motion->tap_left = 0u;
        motion->vx = 0;
    } else if (rising_direction && motion->tap_left && motion->tap_key == direction &&
               ((direction == forward && profile->dash_ticks) ||
                (direction != forward && profile->backstep_ticks))) {
        uint8_t advancing = direction == forward;
        motion->mode = advancing ? MOF_MOTION_DASH : MOF_MOTION_BACKSTEP;
        motion->ticks_left = (advancing ? profile->dash_ticks : profile->backstep_ticks) - 1u;
        motion->vx = velocity(direction, advancing ? profile->dash_speed : profile->backstep_speed);
        motion->tap_left = 0u;
    } else {
        if (rising_direction) {
            motion->tap_key = direction;
            motion->tap_left = profile->tap_window < UINT8_MAX ? profile->tap_window + 1u : UINT8_MAX;
        }
        motion->mode = direction ? MOF_MOTION_WALK : MOF_MOTION_IDLE;
        motion->vx = velocity(direction, direction == forward ? profile->walk_forward : profile->walk_back);
    }

    position = motion->x + motion->vx;
    if (position < left) position = left;
    if (position > right) position = right;
    motion->x = position;
    if (event & MOF_MOTION_LANDED) {
        motion->vx = 0;
        if (free_in_round && (keys & MOF_DUEL_DOWN)) motion->mode = MOF_MOTION_CROUCH;
    }
    return event;
}
