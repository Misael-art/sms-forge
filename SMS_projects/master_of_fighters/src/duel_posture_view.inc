uint8_t mof_duel_posture_pose(const MofDuel *duel, uint8_t player)
{
    const MofDuelFighter *alis = &duel->fighters[player];
    const MofDuelBody *state = &duel->body[player];
    const MofDuelMotion *motion = &state->motion;
    uint8_t blocked = alis->state == MOF_DUEL_BLOCK;
    if (motion->mode == MOF_MOTION_AIR) {
        if (state->air_age <= MOF_ALIS_RISE_TICKS) return MOF_ALIS_JUMP_RISE;
        if ((blocked || alis->guarding == MOF_GUARD_AIRBORNE) &&
            motion->vy < MOF_ALIS_GUARD_UNFOLD_SPEED) return MOF_ALIS_JUMP_GUARD;
        if (motion->vy >= 24) return MOF_ALIS_JUMP_FALL;
        if (motion->vx && motion->vy < -12) return MOF_ALIS_JUMP_DIAGONAL;
        return MOF_ALIS_JUMP_APEX;
    }
    if (alis->state == MOF_DUEL_KO || alis->state == MOF_DUEL_ATTACK) return MOF_ALIS_NO_POSTURE;
    if (state->jump_pending) return MOF_ALIS_CROUCH_TRANSITION;
    if (motion->mode == MOF_MOTION_CROUCH) {
        if (blocked || alis->guarding == MOF_GUARD_CROUCHING) return MOF_ALIS_CROUCH_GUARD;
        return state->transition ? MOF_ALIS_CROUCH_TRANSITION : MOF_ALIS_CROUCH;
    }
    if (blocked || alis->guarding == MOF_GUARD_STANDING) return MOF_ALIS_STAND_GUARD;
    return state->transition ? MOF_ALIS_CROUCH_TRANSITION : MOF_ALIS_NO_POSTURE;
}
