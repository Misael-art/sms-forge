/* Scene 02 two-controller profile. Motion, hit resolution, HUD and bank
   packets stay in the shared duel modules. */

#define MIRROR_BOX(l,t,r,b) {(l)-12,t,(r)-12,b}
static const MofDuelBox mirror_offense[MOF_DUEL_NORMALS_PER_FIGHTER] = {
    MIRROR_BOX(9,-40,30,-25), MIRROR_BOX(17,-37,55,-34),
    MIRROR_BOX(11,-30,35,-16), MIRROR_BOX(11,-46,39,-31),
    MIRROR_BOX(9,-31,31,-18), MIRROR_BOX(15,-51,41,-15),
    MIRROR_BOX(11,-20,36,-5), MIRROR_BOX(9,-14,40,-2),
    MIRROR_BOX(22,-45,31,-31), MIRROR_BOX(19,-28,31,-17),
    MIRROR_BOX(20,-30,34,-22), MIRROR_BOX(18,-16,31,0),
    MIRROR_BOX(6,-41,35,-20), {10,-40,32,-16},
};
#undef MIRROR_BOX

static const uint8_t mirror_ends[MOF_DUEL_NORMALS_PER_FIGHTER][5] = {
    {4,6,14}, {5,7,18}, {5,7,17}, {10,12,27},
    {4,6,14}, {7,9,22}, {4,6,15}, {8,11,25},
    {2,4,11}, {2,5,15}, {2,5,12}, {2,5,15},
    {7,9,23}, {MOF_THROW_REACH_END_TICK, MOF_THROW_BRACE_TICK, MOF_THROW_RELEASE_TICK,
               MOF_THROW_RECOVERY_TICK, MOF_THROW_END_TICK},
};

#define MIRROR_NORMAL(id, first, length, end, damage, height, down) \
    {&mirror_offense[id], &mirror_ends[id][0], first, length, end, damage, 3u, height, down}
static const MofDuelStandingNormal mirror_normals[2][MOF_DUEL_NORMALS_PER_FIGHTER] = {
    {{0}},
    {
        MIRROR_NORMAL(0,4,2,14,6,MOF_HEIGHT_MIDDLE,0),
        MIRROR_NORMAL(1,5,2,18,10,MOF_HEIGHT_MIDDLE,0),
        MIRROR_NORMAL(2,5,2,17,8,MOF_HEIGHT_MIDDLE,0),
        MIRROR_NORMAL(3,10,2,27,12,MOF_HEIGHT_MIDDLE,0),
        MIRROR_NORMAL(4,4,2,14,5,MOF_HEIGHT_MIDDLE,0),
        MIRROR_NORMAL(5,7,2,22,11,MOF_HEIGHT_MIDDLE,0),
        MIRROR_NORMAL(6,4,2,15,6,MOF_HEIGHT_LOW,0),
        MIRROR_NORMAL(7,8,3,25,10,MOF_HEIGHT_LOW,1),
        MIRROR_NORMAL(8,2,2,11,5,MOF_HEIGHT_OVERHEAD,0),
        MIRROR_NORMAL(9,2,3,15,11,MOF_HEIGHT_OVERHEAD,0),
        MIRROR_NORMAL(10,2,3,12,7,MOF_HEIGHT_OVERHEAD,0),
        MIRROR_NORMAL(11,2,3,15,12,MOF_HEIGHT_OVERHEAD,0),
        MIRROR_NORMAL(12,7,2,23,13,MOF_HEIGHT_MIDDLE,0),
        {&mirror_offense[13],&mirror_ends[13][0],MOF_THROW_RELEASE_TICK,1,
         MOF_THROW_END_TICK,16,5,MOF_HEIGHT_THROW,1},
    },
};
#undef MIRROR_NORMAL

static MofDuelCommands mirror_commands[2];
static MofDuel mirror_initial_duel;
static const MofDuelCommandProfile mirror_profile = {{MOF_DUEL_HOLD, MOF_DUEL_HOLD}, 0u};
#define MIRROR_AIR_HOLD 4u
static const MofDuelCommandProfile mirror_air_profile = {{MIRROR_AIR_HOLD, MIRROR_AIR_HOLD}, 0u};
static uint8_t mirror_dir_window[2], mirror_dir_face[2];
static uint8_t mirror_walk_dir[2], mirror_walk_tick[2];
static uint8_t mirror_posture[2];
static uint8_t mirror_air_pending[2];
volatile unsigned char __at(0xC7C8) mof_mirror_reaction[2];
volatile unsigned char __at(0xC7CA) mof_mirror_action[2];

static uint8_t mirror_read(uint8_t player, uint8_t keys)
{
    const MofDuelFighter *actor = &duel.fighters[player];
    const MofAlisMotion *state = &duel.alis[player];
    MofDuelCommands *input = &mirror_commands[player];
    uint8_t posture = (keys & MOF_DUEL_DOWN) ? MOF_INPUT_CROUCHING : MOF_INPUT_STANDING;
    uint8_t buttons = keys & (MOF_DUEL_ONE | MOF_DUEL_TWO);
    uint8_t forward = actor->face_right ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t id, queued;
    uint16_t command;
    if (!((keys | input->last_buttons) & (MOF_DUEL_ONE | MOF_DUEL_TWO | MOF_DUEL_DOWN)) &&
        !mirror_dir_window[player] && !mirror_air_pending[player]) return MOF_DUEL_NO_NORMAL;
    uint8_t free = mof_duel_next_tick_free(&duel, player);

    if ((state->motion.mode == MOF_MOTION_AIR && state->motion.y + state->motion.vy < 0) ||
        (state->jump_pending && state->transition <= 1u))
        posture = MOF_INPUT_AIRBORNE;
    if (posture != mirror_posture[player]) {
        mof_duel_commands_reset(input, input->last_buttons);
        mirror_posture[player] = posture;
    }
    if (posture != MOF_INPUT_AIRBORNE && free &&
        (state->jump_pending || ((keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)) == MOF_DUEL_UP &&
                                  !(actor->keys & MOF_DUEL_UP)))) {
        /* Preserve a fresh attack through the two floor-compression ticks. */
        mirror_air_pending[player] |= buttons & (uint8_t)~input->last_buttons;
        mof_duel_commands_reset(input, keys);
        mirror_dir_window[player] = 0u;
        return MOF_DUEL_NO_NORMAL;
    }
    queued = mirror_air_pending[player];
    mirror_air_pending[player] = 0u;
    if (queued && free && posture == MOF_INPUT_AIRBORNE) {
        input->consumed &= (uint8_t)~queued;
        if (queued & MOF_DUEL_ONE) input->hold_age[0] = 1u;
        if (queued & MOF_DUEL_TWO) input->hold_age[1] = 1u;
    }
    if (!free || actor->face_right != mirror_dir_face[player]) {
        mirror_dir_window[player] = 0u;
        mirror_dir_face[player] = actor->face_right;
    }
    if (free && posture == MOF_INPUT_STANDING) {
        if (keys == (forward | MOF_DUEL_ONE | MOF_DUEL_TWO) && !input->last_buttons) {
            mof_duel_commands_reset(input, keys);
            mirror_dir_window[player] = 0u;
            return MOF_DUEL_THROW;
        }
        if (mirror_dir_window[player] && keys == (forward | MOF_DUEL_ONE) &&
            !(input->last_buttons & MOF_DUEL_ONE)) {
            mof_duel_commands_reset(input, keys);
            mirror_dir_window[player] = 0u;
            return MOF_DUEL_SPECIAL;
        }
    }
    if (free && keys == MOF_DUEL_DOWN && posture == MOF_INPUT_CROUCHING)
        mirror_dir_window[player] = 8u;
    else if (mirror_dir_window[player])
        --mirror_dir_window[player];
    if (!(buttons | input->last_buttons | queued)) return MOF_DUEL_NO_NORMAL;
    command = mof_duel_commands_read(input,
        posture == MOF_INPUT_AIRBORNE ? &mirror_air_profile : &mirror_profile,
        keys, posture, free);
    if (!command) return MOF_DUEL_NO_NORMAL;
    for (id = posture * 4u; id < posture * 4u + 4u; ++id)
        if (command & ((uint16_t)1u << id)) return id;
    return MOF_DUEL_NO_NORMAL;
}

static uint8_t mirror_reaction_pose(uint8_t player)
{
    const MofDuelFighter *actor = &duel.fighters[player];
    uint8_t age;
    switch (actor->state) {
        case MOF_DUEL_HIT:
            if (actor->thrown)
                return mof_duel_age(&duel, actor) < 5u ? MOF_MIRROR_CAUGHT_4 : MOF_MIRROR_CAUGHT_5;
            return MOF_MIRROR_HIT_HEAD + actor->reaction;
        case MOF_DUEL_BLOCK:
            return MOF_MIRROR_HIT_HEAD + actor->reaction;
        case MOF_DUEL_CAUGHT:
            age = (uint8_t)mof_duel_age(&duel, actor);
            return MOF_MIRROR_CAUGHT_1 + (age < 4u ? 0u : age < 9u ? 1u : 2u);
        case MOF_DUEL_FALL:
            return MOF_MIRROR_FALL;
        case MOF_DUEL_DOWNED:
        case MOF_DUEL_KO:
            return MOF_MIRROR_DOWNED;
        case MOF_DUEL_GETUP:
            return mof_duel_age(&duel, actor) < 3u ? MOF_MIRROR_GROUND_RISE : MOF_MIRROR_GETUP;
        default:
            return MIRROR_EMPTY;
    }
}

static uint8_t mirror_preview_normal(uint8_t player)
{
    const MofDuelCommands *input = &mirror_commands[player];
    const MofDuelFighter *actor = &duel.fighters[player];
    uint8_t buttons = input->last_buttons;
    uint8_t action;
    if (actor->state != MOF_DUEL_READY || duel.alis[player].jump_pending ||
        (buttons != MOF_DUEL_ONE && buttons != MOF_DUEL_TWO) || (input->consumed & buttons))
        return MOF_DUEL_NO_NORMAL;
    action = buttons == MOF_DUEL_ONE ? 0u : 2u;
    if (input->hold_age[action >> 1] >=
        (mirror_posture[player] == MOF_INPUT_AIRBORNE ? MIRROR_AIR_HOLD - 1u : MOF_DUEL_HOLD - 3u))
        ++action;
    return action + mirror_posture[player] * 4u;
}

static void mirror_frames_for(uint8_t player, MirrorView *view, uint8_t *next, uint8_t *later)
{
    const MofDuelFighter *actor = &duel.fighters[player];
    const MofAlisMotion *state = &duel.alis[player];
    uint8_t pose, phase, action, face = actor->face_right;
    uint8_t following = MIRROR_EMPTY, future = MIRROR_EMPTY;
    view->x = (uint8_t)actor->x;
    view->y = state->y_offset;
    pose = actor->state == MOF_DUEL_READY ? MIRROR_EMPTY : mirror_reaction_pose(player);
    if (duel.tested_active[player] && actor->contact == MOF_DUEL_LANDED &&
        actor->state != MOF_DUEL_ATTACK) {
        /* A trade resolves both hits from the two active poses. Publish
           those poses for the contact, then show each impact on the next tick. */
        action = actor->standing_normal;
        view->x = (uint8_t)duel.tested_hurt_x[player];
        view->y = (int8_t)(duel.tested_attack[player].top - 144 - mirror_offense[action].top);
        following = pose;
        pose = mirror_action_start[action] + duel.tested_pose[player] - 1u;
    } else if (actor->state == MOF_DUEL_ATTACK) {
        action = actor->standing_normal;
        phase = duel.tested_pose[player];
        if (action >= MOF_DUEL_AIR_NORMALS && action < MOF_DUEL_SPECIAL &&
            state->motion.mode != MOF_MOTION_AIR)
            phase = 3u;
        pose = mirror_action_start[action] + phase - 1u;
        if (phase < mirror_normals[MOF_DUEL_ALIS][action].pose_count)
            following = pose + 1u;
        if (phase + 1u < mirror_normals[MOF_DUEL_ALIS][action].pose_count)
            future = pose + 2u;
        if (phase == 1u && action >= MOF_DUEL_AIR_NORMALS && action < MOF_DUEL_SPECIAL)
            pose = mirror_action_start[action & 0xFEu];
    } else if (pose == MIRROR_EMPTY) {
        phase = !state->y_offset && !state->transition &&
            state->motion.mode == MOF_MOTION_IDLE && !actor->guarding
            ? MOF_ALIS_NO_POSTURE : mof_duel_alis_posture_pose(&duel, player);
        pose = phase ? MOF_MIRROR_ALIS_CROUCH_TRANSITION + phase - 1u : MOF_MIRROR_IDLE;
        if (mirror_walk_dir[player] && (phase == MOF_ALIS_NO_POSTURE || phase == MOF_ALIS_STAND_GUARD)) {
            uint8_t first = mirror_walk_dir[player] == 1u ? MOF_MIRROR_ALIS_WALK_FORWARD_1
                                                          : MOF_MIRROR_ALIS_WALK_BACK_1;
            pose = first + (mirror_walk_tick[player] >> 2);
            following = first + (((mirror_walk_tick[player] >> 2) + 1u) & 3u);
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
        action = mirror_preview_normal(player);
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
    view->frame = pose * 2u + face;
    *next = following == MIRROR_EMPTY ? following : following * 2u + face;
    *later = future == MIRROR_EMPTY ? future : future * 2u + face;
    /* A heavy contact shakes the defender by one pixel while the round is
       frozen. Spilled poses keep X so the shake never rebuilds the PNT. */
    if (duel.hitstop && duel.hitstop_target == (player | MOF_DUEL_HITSTOP_SHAKE) &&
        !mirror_frames[view->frame].spill)
        view->x += duel.hitstop & 1u ? 1u : (uint8_t)-1;
}

static void mirror_walk(uint8_t player, int16_t previous)
{
    const MofDuelFighter *actor = &duel.fighters[player];
    uint8_t direction;
    if (actor->state != MOF_DUEL_READY || actor->x == previous || duel.alis[player].y_offset ||
        duel.alis[player].air_step) {
        mirror_walk_dir[player] = 0u;
        return;
    }
    direction = ((actor->x > previous) == actor->face_right) ? 1u : 2u;
    mirror_walk_tick[player] = mirror_walk_dir[player] == direction ?
        (mirror_walk_tick[player] + 1u) & 15u : 0u;
    mirror_walk_dir[player] = direction;
}

static uint8_t mirror_predict_impact(uint8_t attacker)
{
    uint8_t victim = 1u - attacker, action, pose;
    const MofDuelFighter *source = &duel.fighters[attacker];
    const MofDuelFighter *target = &duel.fighters[victim];
    const MofDuelStandingNormal *normal;
    if (target->state != MOF_DUEL_READY) return MIRROR_EMPTY;
    action = source->state == MOF_DUEL_ATTACK ? source->standing_normal : mirror_preview_normal(attacker);
    if (action == MOF_DUEL_NO_NORMAL) return MIRROR_EMPTY;
    normal = &mirror_normals[MOF_DUEL_ALIS][action];
    if (source->state == MOF_DUEL_ATTACK && mof_duel_age(&duel, source) >=
        (action == MOF_DUEL_THROW ? MOF_THROW_CAPTURE_TICK : normal->first_active))
        return MIRROR_EMPTY;
    if (action == MOF_DUEL_THROW) {
        pose = MOF_MIRROR_CAUGHT_1;
    } else if (mof_duel_guard_blocks(target->guarding, normal->height,
                          action <= MOF_INPUT_LONG_ONE || action >= MOF_DUEL_AIR_NORMALS,
                          action == MOF_DUEL_LOW_NORMALS + MOF_INPUT_LONG_ONE)) {
        pose = MOF_MIRROR_IMPACT_STAND + target->guarding - 1u;
    } else if (normal->knockdown || target->life <= normal->damage) {
        pose = MOF_MIRROR_FALL;
    } else if (duel.alis[victim].motion.mode == MOF_MOTION_CROUCH) {
        pose = MOF_MIRROR_HIT_LOW;
    } else {
        pose = normal->active_boxes[0].top + duel.alis[attacker].y_offset <
            duel.alis[victim].y_offset - 34 ? MOF_MIRROR_HIT_HEAD : MOF_MIRROR_HIT_BODY;
    }
    return pose * 2u + target->face_right;
}

static void mirror_forecast_impact(uint8_t attacker, uint8_t *next, uint8_t *later)
{
    uint8_t impact = mirror_predict_impact(attacker);
    if (impact == MIRROR_EMPTY) return;
    if (*next != MIRROR_EMPTY) *later = *next;
    *next = impact;
}

static void mirror_write_actor(volatile uint8_t *out, uint8_t player, const MirrorView *want)
{
    const MofDuelFighter *actor = &duel.fighters[player];
    uint8_t flags = MOF_DUEL_PROBE_HAS_HURT | MOF_DUEL_PROBE_PRESENTED_FACE;
    uint8_t slot = mirror_find_slot(player, want->frame);
    if (actor->face_right) flags |= MOF_DUEL_PROBE_FACES_RIGHT;
    if (mirror_display[player].frame & 1u) flags |= MOF_DUEL_PROBE_PRESENTED_RIGHT;
    if (actor->state == MOF_DUEL_READY) flags |= MOF_DUEL_PROBE_CAN_ACT;
    if (duel.tested_active[player]) {
        flags |= MOF_DUEL_PROBE_HAS_ATTACK;
        memcpy((void *)(out + 14u), &duel.tested_attack[player], sizeof(MofDuelBox));
    }
    out[0] = actor->fighter;
    out[1] = actor->keys;
    out[2] = actor->state;
    out[3] = (uint8_t)(duel.tick - actor->state_since);
    out[4] = want->frame >> 1;
    out[5] = slot != MIRROR_EMPTY && mirror_cache[player][slot].loaded ==
        mirror_frames[want->frame].count ? out[4] : MIRROR_EMPTY;
    out[6] = mirror_display[player].frame >> 1;
    out[7] = actor->contact;
    out[8] = actor->life;
    out[9] = flags;
    out[10] = want->x;
    out[11] = 0u;
    out[12] = 144u + want->y;
    out[13] = 0u;
    memcpy((void *)(out + 22u), &duel.tested_hurt[player], sizeof(MofDuelBox));
    mof_duel_probe_word(out + 30u, actor->free_since);
    out[32] = duel.tested_pose[player];
    mof_mirror_reaction[player] = actor->reaction;
    mof_mirror_action[player] = actor->standing_normal;
}

static void mirror_write_probe(const MirrorView wanted[2])
{
    uint8_t stamp = mof_duel_trace[4] | 1u;
    mof_duel_trace[4] = stamp;
    mof_duel_probe_word(mof_duel_trace + 6u, duel.tick);
    mirror_write_actor(mof_duel_trace + 8u, 0u, &wanted[0]);
    mirror_write_actor(mof_duel_trace + 41u, 1u, &wanted[1]);
    mof_duel_trace[4] = stamp + 1u;
}

static void mirror_reset(void)
{
    uint8_t player;
    duel = mirror_initial_duel;
    for (player = 0u; player < 2u; ++player) {
        mof_duel_commands_reset(&mirror_commands[player], MOF_DUEL_ONE);
        mirror_walk_dir[player] = mirror_walk_tick[player] = 0u;
        mirror_dir_window[player] = mirror_posture[player] = mirror_air_pending[player] = 0u;
        mirror_dir_face[player] = duel.fighters[player].face_right;
    }
}

void main(void)
{
    MirrorView wanted[2];
    uint8_t next[2], later[2], n1, n2, submit_epoch, epoch, deadline, line, row, col, p1, p2;
    int16_t x1, x2;
    uint16_t pad;
    SMS_displayOff();
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    /* Validate the fixed profile once, with display off. Restart copies
       the same initial round in place while keeping the renderer live. */
    if (!mof_duel_init_pair(&mirror_initial_duel, scene_geometry, MOF_DUEL_HOLD,
                            MOF_DUEL_ALIS, MOF_DUEL_ALIS, 111, 144,
                            MOF_DUEL_ARENA_MARGIN, 255 - MOF_DUEL_ARENA_MARGIN, 24) ||
        !mof_duel_set_standing_normals(&mirror_initial_duel, mirror_normals))
        for (;;) SMS_waitForVBlank();
    mirror_reset();
    SMS_loadSpritePalette(mof_duel_sprite_palette);
    SMS_loadBGPalette(mof_duel_bg_palette);
    SMS_loadTiles(mof_duel_bg_stage, 256u, sizeof(mof_duel_bg_stage));
    load_hud_tiles();
    SMS_setNextTileatLoc(0u);
    for (row = 0u; row < 24u; ++row)
        for (col = 0u; col < 32u; ++col)
            SMS_setTile(256u + mof_duel_bg_rows[row]);
    mirror_render_boot();
    current_life[0] = current_life[1] = 255u;
    prepare_hud();
    publish_hud();
    mof_duel_trace[0] = 'M'; mof_duel_trace[1] = 'F';
    mof_duel_trace[2] = 'D'; mof_duel_trace[3] = '1';
    mof_duel_trace[4] = 0u;
    mof_duel_trace[5] = MOF_DUEL_PROBE_BYTES;
    mof_smrt_magic[0] = 'S'; mof_smrt_magic[1] = 'M';
    mof_smrt_magic[2] = 'R'; mof_smrt_magic[3] = 'T';
    mof_smrt_schema = 1u;
    mof_min_vline = 255u;
    mof_vblank_overrun = mof_presented_frame = mof_worst_done = 0u;
    mof_missed_epochs = mof_repertoire_delayed = mof_repertoire_fault = 0u;
    mof_duel_audio_init();
    SMS_setFrameInterruptHandler(count_vblank);
    submit_epoch = vblank_epoch;
    SMS_displayOn();
    for (;;) {
        mof_cadence_lines[0] = SMS_getVCount();
        pad = SMS_getKeysStatus();
        p1 = pad & 63u;
        p2 = (pad >> 6u) & 63u;
        if ((duel.fighters[0].state == MOF_DUEL_KO || duel.fighters[1].state == MOF_DUEL_KO) &&
            ((p1 & MOF_DUEL_ONE && !(duel.fighters[0].keys & MOF_DUEL_ONE)) ||
             (p2 & MOF_DUEL_ONE && !(duel.fighters[1].keys & MOF_DUEL_ONE)))) {
            mirror_reset();
        }
        /* Commands wait out the impact freeze. Their edges and hold ages
           resume from the last step, so a press made during it is kept. */
        n1 = n2 = MOF_DUEL_NO_NORMAL;
        if (!duel.hitstop) {
            n1 = mirror_read(0u, p1);
            n2 = mirror_read(1u, p2);
        }
#if defined(MOF_DUEL_MIRROR_FOUNDATION)
        if (n1 >= MOF_DUEL_LOW_NORMALS && n1 != MOF_DUEL_SPECIAL) n1 = MOF_DUEL_NO_NORMAL;
        if (n2 >= MOF_DUEL_LOW_NORMALS && n2 != MOF_DUEL_SPECIAL) n2 = MOF_DUEL_NO_NORMAL;
#endif
        x1 = duel.fighters[0].x;
        x2 = duel.fighters[1].x;
        mof_runtime_phase = 1u;
        mof_duel_step_normal(&duel, p1, p2, n1, n2);
        mirror_walk(0u, x1);
        mirror_walk(1u, x2);
        mof_cadence_lines[1] = SMS_getVCount();
        mirror_frames_for(0u, &wanted[0], &next[0], &later[0]);
        mirror_frames_for(1u, &wanted[1], &next[1], &later[1]);
        /* A defender may already have a jump or retreat pose queued.
           Keep its likely impact in the second lookahead slot. */
        if ((duel.fighters[1].state == MOF_DUEL_ATTACK || (p2 & (MOF_DUEL_ONE | MOF_DUEL_TWO))) &&
            (next[0] == MIRROR_EMPTY ||
             (later[0] == MIRROR_EMPTY && !(p1 & (MOF_DUEL_ONE | MOF_DUEL_TWO)))))
            mirror_forecast_impact(1u, &next[0], &later[0]);
        if ((duel.fighters[0].state == MOF_DUEL_ATTACK || (p1 & (MOF_DUEL_ONE | MOF_DUEL_TWO))) &&
            (next[1] == MIRROR_EMPTY ||
             (later[1] == MIRROR_EMPTY && !(p2 & (MOF_DUEL_ONE | MOF_DUEL_TWO)))))
            mirror_forecast_impact(0u, &next[1], &later[1]);
        mirror_prepare(wanted, next, later);
        prepare_hud();
        mof_cadence_lines[2] = SMS_getVCount();
        /* VCount is monotonic through D4. A small SAT-only payload
           can still finish in VBlank when its preparation runs late. */
        deadline = !mirror_bg_dirty && mirror_upload_tiles + mirror_bg_batch <= 2u &&
            !hud_count[0] && !hud_count[1] ? 0xCFu : 0xC4u;
        epoch = wait_to_publish(submit_epoch, deadline);
        mof_missed_epochs += (uint8_t)(epoch - submit_epoch) - 1u;
        submit_epoch = epoch;
        mof_vblank_start = SMS_getVCount();
        mof_runtime_phase = 2u;
        mirror_publish();
        publish_hud();
        line = SMS_getVCount();
        mof_cadence_lines[3] = mof_vline = line;
        if (line < 0xC0u) ++mof_vblank_overrun;
        if (line < mof_min_vline) mof_min_vline = line;
        ++mof_presented_frame;
        mof_runtime_phase = 3u;
        mirror_write_probe(wanted);
        mof_duel_audio_tick(&duel, 1u, mirror_normals[MOF_DUEL_ALIS]);
    }
}
