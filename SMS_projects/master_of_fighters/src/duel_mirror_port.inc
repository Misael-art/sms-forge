/* Included once for each controller by duel_mirror_round.inc. */
static uint8_t MIRROR_READ(uint8_t keys)
{
    const MofDuelFighter *actor = &duel.fighters[MIRROR_PLAYER];
    const MofDuelBody *state = &duel.body[MIRROR_PLAYER];
    MofDuelCommands *input = &mirror_commands[MIRROR_PLAYER];
    uint8_t posture = (keys & MOF_DUEL_DOWN) ? MOF_INPUT_CROUCHING : MOF_INPUT_STANDING;
    uint8_t buttons = keys & (MOF_DUEL_ONE | MOF_DUEL_TWO);
    uint8_t forward = actor->face_right ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t id, queued;
    uint16_t command;
#if defined(MOF_ALIS_CHAPTER)
    uint8_t full=chapter.meter[MIRROR_PLAYER]==8u;
    if (!full && !((keys | input->last_buttons) & (MOF_DUEL_ONE | MOF_DUEL_TWO | MOF_DUEL_DOWN)) &&
        !mirror_dir_window[MIRROR_PLAYER] && !mirror_air_pending[MIRROR_PLAYER]) return MOF_DUEL_NO_NORMAL;
    uint8_t free=actor->state==MOF_DUEL_READY || mof_duel_next_tick_free(&duel,MIRROR_PLAYER);
    uint8_t super_ready=full && mof_chapter_super_input(MIRROR_PLAYER,keys,actor->face_right,free);
#else
    if (!((keys | input->last_buttons) & (MOF_DUEL_ONE | MOF_DUEL_TWO | MOF_DUEL_DOWN)) &&
        !mirror_dir_window[MIRROR_PLAYER] && !mirror_air_pending[MIRROR_PLAYER]) return MOF_DUEL_NO_NORMAL;
    uint8_t free = mof_duel_next_tick_free(&duel, MIRROR_PLAYER);

#endif
    if ((state->motion.mode == MOF_MOTION_AIR && state->motion.y + state->motion.vy < 0) ||
        (state->jump_pending && state->transition <= 1u))
        posture = MOF_INPUT_AIRBORNE;
    if (posture != mirror_posture[MIRROR_PLAYER]) {
        mof_duel_commands_reset(input, input->last_buttons);
        mirror_posture[MIRROR_PLAYER] = posture;
    }
    if (posture != MOF_INPUT_AIRBORNE && free &&
        (state->jump_pending || ((keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)) == MOF_DUEL_UP &&
                                  !(actor->keys & MOF_DUEL_UP)))) {
        /* Preserve a fresh attack through the two floor-compression ticks. */
        mirror_air_pending[MIRROR_PLAYER] |= buttons & (uint8_t)~input->last_buttons;
        mof_duel_commands_reset(input, keys);
        mirror_dir_window[MIRROR_PLAYER] = 0u;
        return MOF_DUEL_NO_NORMAL;
    }
    queued = mirror_air_pending[MIRROR_PLAYER];
    mirror_air_pending[MIRROR_PLAYER] = 0u;
    if (queued && free && posture == MOF_INPUT_AIRBORNE) {
        input->consumed &= (uint8_t)~queued;
        if (queued & MOF_DUEL_ONE) input->hold_age[0] = 1u;
        if (queued & MOF_DUEL_TWO) input->hold_age[1] = 1u;
    }
    if (!free || actor->face_right != mirror_dir_face[MIRROR_PLAYER]) {
        mirror_dir_window[MIRROR_PLAYER] = 0u;
        mirror_dir_face[MIRROR_PLAYER] = actor->face_right;
    }
    /* Every command needs a fresh button, so most frames skip the search. */
    if (free && posture == MOF_INPUT_STANDING &&
        (keys & (uint8_t)~input->last_buttons & (MOF_DUEL_ONE | MOF_DUEL_TWO))) {
        /* The fighter's record lists its commands in priority order. */
        id = mof_duel_command(actor, keys, input->last_buttons, mirror_dir_window[MIRROR_PLAYER],
#if defined(MOF_ALIS_CHAPTER)
                              super_ready);
#else
                              0u);
#endif
        if (id != MOF_DUEL_NO_NORMAL) {
            mof_duel_commands_reset(input, keys);
            mirror_dir_window[MIRROR_PLAYER] = 0u;
            return id;
        }
    }
    if (free && keys == MOF_DUEL_DOWN && posture == MOF_INPUT_CROUCHING)
        mirror_dir_window[MIRROR_PLAYER] = 8u;
    else if (mirror_dir_window[MIRROR_PLAYER])
        --mirror_dir_window[MIRROR_PLAYER];
    if (!(buttons | input->last_buttons | queued)) return MOF_DUEL_NO_NORMAL;
    command = mof_duel_commands_read(input,
        posture == MOF_INPUT_AIRBORNE ? &mirror_air_profile : &mirror_profile,
#ifdef MOF_ALIS_COMBAT
        keys, posture, free || actor->state<=MOF_DUEL_HIT || actor->state==MOF_DUEL_GETUP);
#else
        keys, posture, free);
#endif
    if (!command) return MOF_DUEL_NO_NORMAL;
    /* commands_read emits normals only for the requested posture. */
    id=posture*4u;
#ifdef MOF_ALIS_COMBAT
    if (command&0x888u) return id+3u;
    if (command&0x222u) return id+1u;
#endif
    if (command&0x111u) return id;
    if (command&0x222u) return id+1u;
    if (command&0x444u) return id+2u;
    if (command&0x888u) return id+3u;
    return MOF_DUEL_NO_NORMAL;
}

static void MIRROR_PLAN(void)
{
    MirrorView *view=&mirror_wanted[MIRROR_PLAYER];
    uint8_t *next=&mirror_next[MIRROR_PLAYER], *later=&mirror_later[MIRROR_PLAYER];
    const MofDuelFighter *actor = &duel.fighters[MIRROR_PLAYER];
    const MofDuelBody *state = &duel.body[MIRROR_PLAYER];
    uint8_t pose, phase, action, face = actor->face_right;
    uint8_t following = MIRROR_EMPTY, future = MIRROR_EMPTY;
    view->x = (uint8_t)actor->x;
    view->y = state->y_offset;
#ifdef MOF_ALIS_COMBAT
    if ((mof_combat.landing[0]|mof_combat.landing[1])&1u) view->y-=2;
#endif
#ifdef MOF_ALIS_MAGIC
#ifdef MOF_ALIS_CHOREOGRAPHY
    if (chapter.phase==MOF_PLAY && (mof_magic.caster[MIRROR_PLAYER].pose ||
        (actor->state==MOF_DUEL_READY && mof_magic.caster[MIRROR_PLAYER].dizzy))) {
#else
    if (chapter.phase==MOF_PLAY && actor->state==MOF_DUEL_READY &&
        (mof_magic.caster[MIRROR_PLAYER].pose || mof_magic.caster[MIRROR_PLAYER].dizzy)) {
#endif
        pose=mof_magic.caster[MIRROR_PLAYER].dizzy ? MOF_MIRROR_HIT_HEAD : mof_magic.caster[MIRROR_PLAYER].pose;
        goto encode_pose;
    }
#endif
    pose = actor->state == MOF_DUEL_READY ? MIRROR_EMPTY : mirror_reaction_pose(MIRROR_PLAYER);
    if (duel.tested_active[MIRROR_PLAYER] && actor->contact == MOF_DUEL_LANDED &&
        actor->state != MOF_DUEL_ATTACK) {
        /* A trade resolves both hits from the two active poses. Publish
           those poses for the contact, then show each impact on the next tick. */
        action = actor->standing_normal;
        view->x = (uint8_t)duel.tested_hurt_x[MIRROR_PLAYER];
        view->y = (int8_t)(duel.tested_attack[MIRROR_PLAYER].top - 144 - actor->def->moves[action].active_boxes->top);
        following = pose;
        pose = mirror_action_start[action] + duel.tested_pose[MIRROR_PLAYER] - 1u;
    } else if (actor->state == MOF_DUEL_ATTACK) {
        action = actor->standing_normal;
        phase = duel.tested_pose[MIRROR_PLAYER];
        if (action >= MOF_DUEL_AIR_NORMALS && action < MOF_DUEL_SPECIAL &&
            state->motion.mode != MOF_MOTION_AIR)
            phase = 3u;
        pose = mirror_action_start[action] + phase - 1u;
        if (phase < actor->def->moves[action].pose_count)
            following = pose + 1u;
        if (phase + 1u < actor->def->moves[action].pose_count)
            future = pose + 2u;
#if defined(MOF_ALIS_CHAPTER)
        /* The shield strike can outpace the tile stream on a miss. Finish
           presenting its active cel during recovery before requesting the
           last cel. Hit tests, recovery time and interrupts use duel state. */
        if (action == MOF_DUEL_SPECIAL && phase == 3u &&
            (view->frame >> 1) == MOF_MIRROR_ALIS_SPECIAL_2 &&
            (mirror_display[MIRROR_PLAYER].frame >> 1) != MOF_MIRROR_ALIS_SPECIAL_2) {
            pose = MOF_MIRROR_ALIS_SPECIAL_2;
            following = MOF_MIRROR_ALIS_SPECIAL_3;
        }
#endif
#if defined(MOF_ALIS_RIPOSTE)
        if (action==MOF_DUEL_RIPOSTE && !actor->riposte_armed && phase==3u)
            pose=MOF_MIRROR_RIPOSTE_4;
#endif
        if (phase == 1u && action >= MOF_DUEL_AIR_NORMALS && action < MOF_DUEL_SPECIAL)
            pose = mirror_action_start[action & 0xFEu];
    } else if (pose == MIRROR_EMPTY) {
        phase = !state->y_offset && !state->transition &&
            state->motion.mode == MOF_MOTION_IDLE && !state->jump_pending
            ? (actor->guarding == MOF_GUARD_STANDING ? MOF_ALIS_STAND_GUARD : MOF_ALIS_NO_POSTURE) : mof_duel_posture_pose(&duel, MIRROR_PLAYER);
        pose = phase ? MOF_MIRROR_ALIS_CROUCH_TRANSITION + phase - 1u : MOF_MIRROR_IDLE;
        if (mirror_walk_dir[MIRROR_PLAYER] && (phase == MOF_ALIS_NO_POSTURE || phase == MOF_ALIS_STAND_GUARD)) {
            uint8_t first = mirror_walk_dir[MIRROR_PLAYER] == 1u ? MOF_MIRROR_ALIS_WALK_FORWARD_1
                                                          : MOF_MIRROR_ALIS_WALK_BACK_1;
            pose = first + (mirror_walk_tick[MIRROR_PLAYER] >> 2);
            following = first + (((mirror_walk_tick[MIRROR_PLAYER] >> 2) + 1u) & 3u);
        } else if (state->jump_pending) {
            following = MOF_MIRROR_ALIS_JUMP_RISE;
            future = MOF_MIRROR_AIR_2_1;
        } else if (state->motion.mode == MOF_MOTION_AIR) {
            if (phase == MOF_ALIS_JUMP_RISE)
                following = actor->guarding ? MOF_MIRROR_ALIS_JUMP_GUARD :
                    state->motion.vx ? MOF_MIRROR_ALIS_JUMP_DIAGONAL : MOF_MIRROR_ALIS_JUMP_APEX;
            else if (phase == MOF_ALIS_JUMP_DIAGONAL) following = MOF_MIRROR_ALIS_JUMP_APEX;
            else if (phase == MOF_ALIS_JUMP_FALL) following = MOF_MIRROR_ALIS_CROUCH_TRANSITION;
            else following = MOF_MIRROR_ALIS_JUMP_FALL;
            future = MOF_MIRROR_AIR_0_1;
        }
        action = mirror_commands[MIRROR_PLAYER].last_buttons ? mirror_preview_normal(MIRROR_PLAYER) : MOF_DUEL_NO_NORMAL;
        if (action != MOF_DUEL_NO_NORMAL) {
#if defined(MOF_DUEL_MIRROR_FOUNDATION)
            if (action < MOF_DUEL_LOW_NORMALS)
#endif
            {
                following = mirror_action_start[action];
                future = following + 1u;
                if (action >= MOF_DUEL_AIR_NORMALS && state->motion.mode == MOF_MOTION_AIR) {
                    pose = mirror_action_start[action & 0xFEu];
                    following = future;
                    future = mirror_action_start[action ^ 1u] + 1u;
                }
            }
        }
    } else if (actor->state == MOF_DUEL_CAUGHT) {
        following = pose + 1u;
        future = pose == MOF_MIRROR_CAUGHT_3 ? MOF_MIRROR_CAUGHT_5 : pose + 2u;
    } else if (actor->state == MOF_DUEL_HIT && actor->thrown) {
        following = pose == MOF_MIRROR_CAUGHT_4 ? MOF_MIRROR_CAUGHT_5 : MOF_MIRROR_FALL;
        if (pose == MOF_MIRROR_CAUGHT_4) future = MOF_MIRROR_FALL;
    } else if (actor->state == MOF_DUEL_FALL) {
#ifdef MOF_ALIS_COMBAT
        /* The cinematic landing is already staged at the projected pivot. */
        if (!mof_combat.cutscene_return)
#endif
        following = MOF_MIRROR_DOWNED;
    } else if (actor->state == MOF_DUEL_DOWNED) {
        if (actor->life) {
            following = MOF_MIRROR_GROUND_RISE;
            future = MOF_MIRROR_GETUP;
        }
    } else if (actor->state == MOF_DUEL_GETUP) {
        following = pose == MOF_MIRROR_GROUND_RISE ? MOF_MIRROR_GETUP : MOF_MIRROR_IDLE;
        if (pose == MOF_MIRROR_GROUND_RISE) future = MOF_MIRROR_IDLE;
    }
#if defined(MOF_ALIS_CHAPTER)
    if (chapter.phase==MOF_RESULT && chapter.winner==MIRROR_PLAYER) {
        uint8_t step=chapter.age<24 ? 0 : chapter.age<54 ? 1 : 2;
        pose=mof_presentation->victory_pose+step;
        following=step<2 ? pose+1 : MIRROR_EMPTY;
        future=MIRROR_EMPTY;
    } else if (chapter.idle[MIRROR_PLAYER]>=180 && chapter.idle[MIRROR_PLAYER]<228 && pose==MOF_MIRROR_IDLE &&
               following==MIRROR_EMPTY) {
        pose=mof_presentation->listen_pose+((chapter.idle[MIRROR_PLAYER]-180)>>4);
        following=pose==mof_presentation->listen_pose+2u ? MOF_MIRROR_IDLE : pose+1;
    }
#endif
#if defined(MOF_ALIS_RIPOSTE)
    if (chapter.phase==MOF_PLAY && pose==MOF_MIRROR_IDLE && chapter.idle[MIRROR_PLAYER]>=12 &&
        following==MIRROR_EMPTY) {
        uint8_t beat=(chapter.idle[MIRROR_PLAYER]>>4)&3u;
        pose=MOF_MIRROR_BREATHE_1+beat;
        following=MOF_MIRROR_BREATHE_1+((beat+1u)&3u);
    }
#endif
#ifdef MOF_ALIS_MAGIC
encode_pose:
#endif
    view->frame = pose * 2u + face;
    *next = following == MIRROR_EMPTY ? following : following * 2u + face;
    *later = future == MIRROR_EMPTY ? future : future * 2u + face;
    /* A heavy contact shakes the defender by one pixel while the round is
       frozen. Spilled poses keep X so the shake never rebuilds the PNT. */
    if (duel.hitstop && (duel.hitstop_target == (MIRROR_PLAYER | MOF_DUEL_HITSTOP_SHAKE) ||
        duel.hitstop_target == (MOF_DUEL_HITSTOP_BOTH | MOF_DUEL_HITSTOP_SHAKE)) &&
        !mirror_frames[view->frame].spill)
        view->x += duel.hitstop & 1u ? 1u : (uint8_t)-1;
}
