#ifdef MOF_ALIS_FEEDBACK
#include "../inc/alis_feedback.h"
#endif
/* Scene 02 two-controller profile. Motion, hit resolution, HUD and bank
   packets stay in the shared duel modules. */

#if defined(MOF_ALIS_CHAPTER)
#include "../inc/alis_chapter.h"
#include "../inc/duel_combat.h"
#include "alis_pages.h"
#ifdef MOF_ALIS_MAGIC
#include "../inc/alis_magic.h"
#endif
#define WORST_FRAME_WINDOW 3000u
#define MIRROR_HOT inline
volatile uint8_t __at(0xC7CC) mof_chapter_lines[6];
#define CHAPTER_LINE(i) (mof_chapter_lines[i] = SMS_getVCount())
#include "PSGlib.h"
static const MofChapterPresentation alis_presentation = {
    MOF_PAGE_STORY0, 4, MOF_PAGE_STORY4, 2,
    {MOF_PAGE_WIN1, MOF_PAGE_WIN2}, MOF_PAGE_RETRY, MOF_ARENA_BANK,
    MOF_SONG_OPEN, MOF_SONG_BATTLE, MOF_SONG_WIN, MOF_MIRROR_LISTEN_1, MOF_MIRROR_BOW_1
};
#endif

#if !defined(MIRROR_HOT)
#define MIRROR_HOT
#define CHAPTER_LINE(i) ((void)0)
#endif

/* Fighter rules records: moves, boxes and the motion profile. */
#include "duel_roster.inc"

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
    if (actor->state != MOF_DUEL_READY || duel.body[player].jump_pending ||
        (buttons != MOF_DUEL_ONE && buttons != MOF_DUEL_TWO) || (input->consumed & buttons))
        return MOF_DUEL_NO_NORMAL;
    action = buttons == MOF_DUEL_ONE ? 0u : 2u;
    if (input->hold_age[action >> 1] >=
        (mirror_posture[player] == MOF_INPUT_AIRBORNE ? MIRROR_AIR_HOLD - 1u : MOF_DUEL_HOLD - 3u))
        ++action;
    return action + mirror_posture[player] * 4u;
}

static void mirror_walk(uint8_t player, int16_t previous)
{
    uint8_t direction = mof_duel_walk_direction(&duel, player, previous);
    if (!direction || mirror_walk_dir[player] != direction) mirror_walk_tick[player] = 0u;
    /* Two cold walk cycles can take more than four ticks to stream.
       Keep the last tick of this cel until it has reached the display. */
    else if ((mirror_walk_tick[player] & 3u) != 3u ||
             mirror_display[player].frame == mirror_wanted[player].frame)
        mirror_walk_tick[player] = (mirror_walk_tick[player] + 1u) & 15u;
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
    normal = &source->def->moves[action];
    if (source->state == MOF_DUEL_ATTACK && mof_duel_age(&duel, source) >=
        (action == MOF_DUEL_THROW ? MOF_THROW_CAPTURE_TICK : normal->first_active))
        return MIRROR_EMPTY;
    if (action == MOF_DUEL_THROW) {
        pose = MOF_MIRROR_CAUGHT_1;
    } else if (mof_duel_guard_blocks(target->guarding, normal->height,
                          (normal->flags & MOF_MOVE_AIR_BLOCKABLE) != 0u,
                          (normal->flags & MOF_MOVE_ANTI_AIR) != 0u)) {
        pose = MOF_MIRROR_IMPACT_STAND + target->guarding - 1u;
    } else if (normal->knockdown || target->life <= normal->damage) {
        pose = MOF_MIRROR_FALL;
    } else if (duel.body[victim].motion.mode == MOF_MOTION_CROUCH) {
        pose = MOF_MIRROR_HIT_LOW;
    } else {
        pose = normal->active_boxes[0].top + duel.body[attacker].y_offset <
            duel.body[victim].y_offset - target->def->neck ? MOF_MIRROR_HIT_HEAD : MOF_MIRROR_HIT_BODY;
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

static MIRROR_HOT void mirror_write_actor(volatile uint8_t *out, uint8_t player, const MirrorView *want)
{
    const MofDuelFighter *actor = &duel.fighters[player];
    uint8_t flags = MOF_DUEL_PROBE_HAS_HURT | MOF_DUEL_PROBE_PRESENTED_FACE;
#ifndef MOF_ALIS_MAGIC
    uint8_t slot = mirror_find_slot(player, want->frame);
#endif
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
#ifdef MOF_ALIS_MAGIC
    out[5] = (mirror_index.slots[player][want->frame]&0xfcu)==4u ? want->frame>>1 : MIRROR_EMPTY;
#else
    out[5] = slot != MIRROR_EMPTY && mirror_cache[player][slot].loaded ==
        mirror_frames[want->frame].count ? out[4] : MIRROR_EMPTY;
#endif
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

static void mirror_write_probe(void)
{
    uint8_t stamp = mof_duel_trace[4] | 1u;
    mof_duel_trace[4] = stamp;
    mof_duel_probe_word(mof_duel_trace + 6u, duel.tick);
    mirror_write_actor(mof_duel_trace + 8u, 0u, &mirror_wanted[0]);
    mirror_write_actor(mof_duel_trace + 41u, 1u, &mirror_wanted[1]);
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


/* Instantiate these two hot paths with constant owner offsets. SDCC also
   emits the unused addressable body of a static inline function. */
#define MIRROR_PLAYER 0u
#define MIRROR_READ mirror_read_p1
#define MIRROR_PLAN mirror_plan_p1
#include "duel_mirror_port.inc"
#undef MIRROR_PLAN
#undef MIRROR_READ
#undef MIRROR_PLAYER
#define MIRROR_PLAYER 1u
#define MIRROR_READ mirror_read_p2
#define MIRROR_PLAN mirror_plan_p2
#include "duel_mirror_port.inc"
#undef MIRROR_PLAN
#undef MIRROR_READ
#undef MIRROR_PLAYER

#ifdef MOF_ALIS_MAGIC
#include "alis_magic_presentation.inc"
#include "duel_ground.inc"
#endif

#ifdef MOF_ALIS_COMBAT
void mof_combat_step_body(MofDuel *d,uint8_t player,uint8_t keys)
{
    SMS_mapROMBank(MOF_COMBAT_BANK);
    mof_combat_body(d,player,keys);
    SMS_mapROMBank(MOF_RULE_BANK);
}

static uint8_t clean_directions(uint8_t keys)
{
    if ((keys&12u)==12u) keys&=(uint8_t)~12u;
    if ((keys&3u)==3u) keys&=(uint8_t)~3u;
    return keys;
}

static void guardians_arena(void)
{
    uint8_t loser=1u-chapter.winner, direction=duel.fighters[loser].face_right;
    MofDuelBody *body=&duel.body[loser];
    mof_magic_victory();
    duel.fighters[loser].state=MOF_DUEL_FALL;
    duel.fighters[loser].state_since=duel.tick;
    body->y_offset=-29;
    body->motion.y=-29*MOF_MOTION_UNIT;
    body->motion.vy=18;
    body->motion.vx=direction ? -40 : 40;
    body->motion.mode=MOF_MOTION_AIR;
    duel.tested_hurt_x[loser]=INT16_MIN;
    duel.hitstop=0;
    mof_combat.cutscene_return=1;
    mof_combat.fall[loser]=MOF_COMBAT_HARD;
    mof_magic.count=mof_magic.old_count=mof_magic.busy=0;
    chapter.phase=MOF_CINEMA_FALL;
    SMS_displayOff();
}
#endif

void main(void)
{
    uint8_t n1, n2, submit_epoch, epoch, deadline, line, row, col, p1, p2;
    int16_t x1, x2;
    uint16_t pad;
#if defined(MOF_ALIS_CHAPTER)
    uint8_t transition, banner, held[2];
#endif
    SMS_displayOff();
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    /* Validate the fixed profile once, with display off. Restart copies
       the same initial round in place while keeping the renderer live. */
#if defined(MOF_ALIS_CHAPTER)
    SMS_mapROMBank(MOF_RULE_BANK);
#endif
    if (!mof_duel_init_pair(&mirror_initial_duel, scene_geometry, MOF_DUEL_HOLD,
                            MOF_DUEL_ALIS, MOF_DUEL_ALIS, 111, 144,
                            MOF_DUEL_ARENA_MARGIN, 255 - MOF_DUEL_ARENA_MARGIN, 24) ||
        !mof_duel_set_roster(&mirror_initial_duel, mof_roster))
        for (;;) SMS_waitForVBlank();
#if defined(MOF_ALIS_CHAPTER)
    mof_min_vline = 255u;
    mof_vblank_overrun = mof_presented_frame = mof_worst_done = 0u;
    mof_chapter_select(&alis_presentation);
#ifdef MOF_ALIS_MATCHUP
    mof_chapter_pair(mirror_initial_duel.fighters[0].fighter,mirror_initial_duel.fighters[1].fighter);
    SMS_setFrameInterruptHandler(count_vblank);
#endif
    mof_duel_audio_init();
title:
    mof_chapter_menu();
new_match:
    mof_chapter_match();
new_round:
    mof_chapter_round();
#ifdef MOF_ALIS_COMBAT
    memset(&mof_combat,0,sizeof(mof_combat));
#endif
#ifdef MOF_ALIS_MAGIC
    SMS_mapROMBank(MOF_MAGIC_BANK);
    mof_magic_reset();
    magic_last_keys[0]=magic_last_keys[1]=255;
#endif
#ifdef MOF_PORT_SKY
    SMS_disableLineInterrupt();
#endif
    SMS_displayOff();
#endif
    mirror_reset();
#ifdef MOF_ALIS_COMBAT
restore_arena:
    SMS_setBGScrollY(0);
    mof_combat.scroll_y=0;
#endif
    SMS_loadSpritePalette(mof_duel_sprite_palette);
    SMS_loadBGPalette(mof_duel_bg_palette);
    SMS_loadTiles(mof_duel_bg_stage, 256u, sizeof(mof_duel_bg_stage));
    load_hud_tiles();
#if defined(MOF_ALIS_CHAPTER)
    mof_chapter_arena();
#else
    SMS_setNextTileatLoc(0u);
    for (row = 0u; row < 24u; ++row)
        for (col = 0u; col < 32u; ++col)
            SMS_setTile(256u + mof_duel_bg_rows[row]);
#endif
    mirror_render_boot();
    current_life[0] = current_life[1] = 255u;
    prepare_hud();
    publish_hud();
    mof_duel_trace[0] = 'M'; mof_duel_trace[1] = 'F';
    mof_duel_trace[2] = 'D'; mof_duel_trace[3] = '1';
    memset((void *)(mof_duel_trace+6),0,MOF_DUEL_PROBE_BYTES-6);
    mof_duel_trace[4] = 0u;
    mof_duel_trace[5] = MOF_DUEL_PROBE_BYTES;
    mof_smrt_magic[0] = 'S'; mof_smrt_magic[1] = 'M';
    mof_smrt_magic[2] = 'R'; mof_smrt_magic[3] = 'T';
    mof_smrt_schema = 1u;
#if !defined(MOF_ALIS_CHAPTER)
    mof_min_vline = 255u;
    mof_vblank_overrun = mof_presented_frame = mof_worst_done = 0u;
#endif
    mof_missed_epochs = mof_repertoire_delayed = mof_repertoire_fault = 0u;
#if defined(MOF_ALIS_CHAPTER)
    mof_chapter_hud(chapter.phase==MOF_CINEMA_FALL ? 255u : chapter.round-1u);
    held[0]=held[1]=0;
#else
    mof_duel_audio_init();
#endif
    SMS_setFrameInterruptHandler(count_vblank);
    submit_epoch = vblank_epoch;
#ifdef MOF_PORT_SKY
    /* Raster register writes disturb the VDP address latch. Enable them
       only after both costumes, the SAT, the HUD and the map are loaded. */
    SMS_waitForVBlank();
    mof_port_raster_start();
#endif
    SMS_displayOn();
    for (;;) {
        mof_cadence_lines[0] = SMS_getVCount();
        pad = SMS_getKeysStatus();
        p1 = pad & 63u;
        p2 = (pad >> 6u) & 63u;
#ifdef MOF_ALIS_COMBAT
        p1=clean_directions(p1);
        p2=clean_directions(p2);
#endif
#if defined(MOF_ALIS_CHAPTER)
        if (chapter.phase==MOF_ROUND || chapter.phase==MOF_FIGHT_CALL) {
            SMS_waitForVBlank();
            mof_chapter_hud(chapter.phase==MOF_ROUND ? chapter.round-1u : 3);
            if (++chapter.age >= (chapter.phase==MOF_ROUND ? 50u : 28u)) {
                ++chapter.phase;
                chapter.age=0;
                if (chapter.phase==MOF_PLAY) {
                    mof_chapter_hud(255);
                    held[0]=p1 & 48u;
                    held[1]=p2 & 48u;
                }
            }
            mof_chapter_music();
            submit_epoch=vblank_epoch;
            continue;
        }
        SMS_mapROMBank(MOF_RULE_BANK);
        if (chapter.phase==MOF_RESULT) {
#ifdef MOF_ALIS_COMBAT
            if (mof_magic.finisher && chapter.winner<2u) {
                guardians_arena();
                goto restore_arena;
            }
#endif
            if (++chapter.age>=100u) {
                PSGSFXStop();
                transition=mof_chapter_result();
                if (transition==MOF_NEXT_ROUND) goto new_round;
                if (transition==MOF_REMATCH) goto new_match;
                goto title;
            }
        } else {
#ifdef MOF_ALIS_COMBAT
            if (chapter.phase==MOF_CINEMA_FALL) {
                p1=p2=0;
                mof_duel_step_normal(&duel,0,0,MOF_DUEL_NO_NORMAL,MOF_DUEL_NO_NORMAL);
                if (duel.fighters[1u-chapter.winner].state==MOF_DUEL_KO) {
                    chapter.phase=MOF_RESULT;
                    chapter.age=mof_combat.cutscene_return=0;
                }
                goto plan_frame;
            }
            if (duel.hitstop) {
                mof_combat.frozen_buttons[0]|=p1&~duel.fighters[0].keys&48u;
                mof_combat.frozen_buttons[1]|=p2&~duel.fighters[1].keys&48u;
            } else {
                p1|=mof_combat.frozen_buttons[0];
                p2|=mof_combat.frozen_buttons[1];
                mof_combat.frozen_buttons[0]=mof_combat.frozen_buttons[1]=0;
            }
#endif
            held[0]&=p1; held[1]&=p2;
            p1 &= (uint8_t)~held[0]; p2 &= (uint8_t)~held[1];
            if (chapter.story) p2=mof_chapter_cpu(&duel);
#else
        if ((duel.fighters[0].state == MOF_DUEL_KO || duel.fighters[1].state == MOF_DUEL_KO) &&
            ((p1 & MOF_DUEL_ONE && !(duel.fighters[0].keys & MOF_DUEL_ONE)) ||
             (p2 & MOF_DUEL_ONE && !(duel.fighters[1].keys & MOF_DUEL_ONE)))) {
            mirror_reset();
        }
#endif
        /* Commands wait out the impact freeze. Their edges and hold ages
           resume from the last step, so a press made during it is kept. */
        n1 = n2 = MOF_DUEL_NO_NORMAL;
        if (!duel.hitstop) {
#ifdef MOF_ALIS_MAGIC
            if (!mof_magic.busy && p1==magic_last_keys[0] && p2==magic_last_keys[1] &&
                duel.fighters[0].face_right==mof_magic.caster[0].face &&
                duel.fighters[1].face_right==mof_magic.caster[1].face) {
                magic_wait_gesture(0);
                magic_wait_gesture(1);
            } else {
                magic_last_keys[0]=p1; magic_last_keys[1]=p2;
#ifdef MOF_ALIS_COMBAT
                SMS_mapROMBank(MOF_COMBAT_BANK);
#else
                SMS_mapROMBank(MOF_MAGIC_BANK);
#endif
                mof_magic_input(&duel,p1,p2);
                SMS_mapROMBank(MOF_RULE_BANK);
                p1=mof_magic.pad[0]; p2=mof_magic.pad[1];
            }
            if (mof_magic.locked[0]) mof_duel_commands_reset(&mirror_commands[0],magic_last_keys[0]);
            else
#endif
            n1 = mirror_read_p1(p1);
#ifdef MOF_ALIS_MAGIC
            if (mof_magic.locked[1]) mof_duel_commands_reset(&mirror_commands[1],magic_last_keys[1]);
            else
#endif
            n2 = mirror_read_p2(p2);
        }
#ifdef MOF_ALIS_MAGIC
        mof_magic.effect_mask=0;
        mof_magic.live_step=!duel.hitstop;
#endif
        CHAPTER_LINE(0);
#if defined(MOF_DUEL_MIRROR_FOUNDATION)
        if (n1 >= MOF_DUEL_LOW_NORMALS && n1 != MOF_DUEL_SPECIAL) n1 = MOF_DUEL_NO_NORMAL;
        if (n2 >= MOF_DUEL_LOW_NORMALS && n2 != MOF_DUEL_SPECIAL) n2 = MOF_DUEL_NO_NORMAL;
#endif
        x1 = duel.fighters[0].x;
        x2 = duel.fighters[1].x;
        mof_runtime_phase = 1u;
#ifdef MOF_ALIS_MAGIC
        if (n1!=MOF_DUEL_NO_NORMAL || n2!=MOF_DUEL_NO_NORMAL || !ground_step(p1,p2))
#endif
            mof_duel_step_normal(&duel, p1, p2, n1, n2);
        CHAPTER_LINE(1);
        mirror_walk(0u, x1);
        mirror_walk(1u, x2);
#if defined(MOF_ALIS_CHAPTER)
        if (n1==MOF_DUEL_SUPER && duel.fighters[0].state==MOF_DUEL_ATTACK &&
            duel.fighters[0].standing_normal==n1) mof_chapter_spend_super(0u);
        if (n2==MOF_DUEL_SUPER && duel.fighters[1].state==MOF_DUEL_ATTACK &&
            duel.fighters[1].standing_normal==n2) mof_chapter_spend_super(1u);
#ifdef MOF_ALIS_MAGIC
        if (mof_magic.busy) {
            SMS_mapROMBank(MOF_MAGIC_BANK);
            mof_magic_step(&duel);
            SMS_mapROMBank(MOF_RULE_BANK);
        } else if (mof_magic.live_step) {
            if (mof_magic.caster[0].chat_wait) --mof_magic.caster[0].chat_wait;
            if (mof_magic.caster[1].chat_wait) --mof_magic.caster[1].chat_wait;
        }
#endif
        mof_chapter_update(&duel);
#ifdef MOF_ALIS_MAGIC
        if (mof_magic.finisher && chapter.phase==MOF_RESULT) chapter.age=99;
#endif
        }
#endif
#ifdef MOF_ALIS_COMBAT
plan_frame:
#endif
        mof_cadence_lines[1] = SMS_getVCount();
        mirror_plan_p1();
        mirror_plan_p2();
        CHAPTER_LINE(2);
        /* A defender may already have a jump or retreat pose queued.
           Keep its likely impact in the second lookahead slot. */
        if ((duel.fighters[1].state == MOF_DUEL_ATTACK || (p2 & (MOF_DUEL_ONE | MOF_DUEL_TWO))) &&
            (mirror_next[0] == MIRROR_EMPTY ||
             (mirror_later[0] == MIRROR_EMPTY && !(p1 & (MOF_DUEL_ONE | MOF_DUEL_TWO)))))
            mirror_forecast_impact(1u, &mirror_next[0], &mirror_later[0]);
        if ((duel.fighters[0].state == MOF_DUEL_ATTACK || (p1 & (MOF_DUEL_ONE | MOF_DUEL_TWO))) &&
            (mirror_next[1] == MIRROR_EMPTY ||
             (mirror_later[1] == MIRROR_EMPTY && !(p2 & (MOF_DUEL_ONE | MOF_DUEL_TWO)))))
            mirror_forecast_impact(0u, &mirror_next[1], &mirror_later[1]);
        mirror_prepare();
        CHAPTER_LINE(3);
#ifdef MOF_ALIS_MAGIC
        if (!mof_magic.live_step && chapter.phase==MOF_PLAY && !mirror_bg_dirty) {
            /* Hitstop freezes both pivots and projectiles. Their existing
               VRAM cells already contain this exact composite. */
            mof_magic.count=mof_magic.old_count;
            memset(mof_magic.upload,0,mof_magic.count);
        } else {
        if (mof_magic.busy
#ifdef MOF_ALIS_COMBAT
            || (duel.hitstop && (mof_combat.spark[0] || mof_combat.spark[1])) ||
            mof_combat.landing[0] || mof_combat.landing[1]
#endif
           ) {
            SMS_mapROMBank(MOF_MAGIC_BANK);
            mof_magic_plan(&duel,16u-((duel.fighters[0].x+duel.fighters[1].x)>>4));
        } else mof_magic.count=0;
        if (mof_magic.count || mof_magic.old_count) {
            SMS_mapROMBank(MOF_MAGIC_BANK);
            mof_magic_tiles((const uint8_t *)(mirror_bg_dirty ? mirror_stage_cells : mirror_cells[mirror_bg_page]),
                            mirror_bg_dirty ? mirror_bg_count : mirror_old_bg_count,MOF_BANNER_TILE,mirror_bg_dirty);
        }
        }
#endif
        if (duel.fighters[0].life!=current_life[0] || duel.fighters[1].life!=current_life[1]) prepare_hud();
        else hud_count[0]=hud_count[1]=0;
#ifdef MOF_ALIS_MAGIC
        magic_prepare_life();
        mof_chapter_stage_hud();
#endif
        mof_cadence_lines[2] = SMS_getVCount();
        /* VCount is monotonic through D4. A small SAT-only payload
           can still finish in VBlank when its preparation runs late. */
        deadline =
#ifdef MOF_ALIS_MAGIC
            !mof_magic.count && !mof_magic.old_count &&
#endif
            !mirror_bg_dirty && mirror_upload_tiles + mirror_bg_batch <= 2u &&
            !hud_count[0] && !hud_count[1] ? 0xCFu : 0xC4u;
#ifdef MOF_ALIS_MAGIC
        /* Spend the remaining NTSC blank only when its payload is bounded.
           C0..FF may repeat D5..DA; subtracting from FF covers the later
           occurrence. Leave the original early deadline for compound swaps. */
        if (chapter.phase==MOF_PLAY && !mirror_bg_dirty && !mof_magic.count && !mof_magic.old_count &&
            !hud_count[0] && !hud_count[1] && mof_chapter_pnt.count<=4u) {
            uint8_t tiles=mirror_upload_tiles+mirror_bg_batch;
            uint8_t reserve=12u+3u*tiles+2u*mirror_upload_count+mof_chapter_pnt.count;
            if (mirror_sat_dirty) reserve+=4u+((mirror_sat_y_count+mirror_sat_xt_count+7u)>>3);
            if ((uint8_t)(255u-reserve)>deadline) deadline=255u-reserve;
        }
#endif
        epoch = wait_to_publish(submit_epoch, deadline);
        mof_missed_epochs += (uint8_t)(epoch - submit_epoch) - 1u;
        submit_epoch = epoch;
        mof_vblank_start = SMS_getVCount();
        mof_runtime_phase = 2u;
#ifdef MOF_ALIS_COMBAT
        line=(mof_combat.landing[0]|mof_combat.landing[1])&1u;
        if (line!=mof_combat.scroll_y) {
            if (line) SMS_setBGScrollY(2);
            else SMS_setBGScrollY(0);
            mof_combat.scroll_y=line;
        }
        if (mof_combat.landing[0]==8u || mof_combat.landing[1]==8u)
            mof_magic.audio=MOF_SFX_LANDING;
#endif
        mirror_publish();
        if (hud_count[0] || hud_count[1]) publish_hud();
#ifdef MOF_ALIS_MAGIC
        if (mof_magic.count || mof_magic.old_count) mof_magic_publish();
#endif
#if defined(MOF_ALIS_CHAPTER)
        banner=chapter.phase==MOF_RESULT ? (chapter.winner==2 ? 6 : chapter.expired ? 5 : 4) : 255;
#ifdef MOF_ALIS_MAGIC
        mof_chapter_publish_hud(banner);
#else
        mof_chapter_hud(banner);
#endif
#endif
#ifdef MOF_ALIS_FEEDBACK
        if (mof_feedback.label[0] || mof_feedback.label[1]) mof_feedback_present(&duel);
#endif
        line = SMS_getVCount();
        mof_cadence_lines[3] = mof_vline = line;
        mirror_commit();
#if defined(MOF_ALIS_CHAPTER)
        if (!mof_worst_done) {
#endif
            if (line < 0xC0u) {
#if defined(MOF_ALIS_CHAPTER)
                if (!mof_vblank_overrun) {
                    mof_render_stage_lines[0]=mof_vblank_start;
                    mof_render_stage_lines[1]=mof_vblank_payload[0];
                    mof_render_stage_lines[2]=mof_vblank_payload[1];
                    mof_render_stage_lines[3]=mof_vblank_payload[2];
                    mof_probe_end=mof_vblank_payload[3];
                    mof_vblank_end_high=line;
                }
#endif
                ++mof_vblank_overrun;
            }
            if (line < mof_min_vline) mof_min_vline = line;
#if defined(MOF_ALIS_CHAPTER)
            if (mof_presented_frame+1u==WORST_FRAME_WINDOW) mof_worst_done=1u;
        }
#endif
#ifdef MOF_ALIS_MAGIC
        if (mof_magic.count) memcpy(mof_magic.old,mof_magic.next,mof_magic.count*sizeof(MofMagicTile));
        mof_magic.old_count=mof_magic.count;
#endif
        ++mof_presented_frame;
        mof_runtime_phase = 3u;
        mirror_write_probe();
        CHAPTER_LINE(4);
#if defined(MOF_ALIS_CHAPTER)
        mof_chapter_music();
        SMS_mapROMBank(MOF_RULE_BANK);
#ifdef MOF_ALIS_MAGIC
        if (mof_magic.audio) { mof_magic_sound(); PSGSFXFrame(); }
        else
#endif
        if (chapter.phase==MOF_RESULT ||
            (!duel.fighters[0].contact && !duel.fighters[1].contact &&
             duel.fighters[0].state!=MOF_DUEL_ATTACK && duel.fighters[1].state!=MOF_DUEL_ATTACK))
            PSGSFXFrame();
        else
#endif
            mof_duel_audio_tick(&duel, 1u, duel.fighters[0].def->moves);
        CHAPTER_LINE(5);
#ifdef MOF_ALIS_FEEDBACK
        if (mof_feedback.duration) {
            mof_feedback.shown[0]=mirror_display[0].frame;
            mof_feedback.shown[1]=mirror_display[1].frame;
            mof_feedback_pause(&duel);
            submit_epoch=vblank_epoch;
        }
#endif
    }
}
