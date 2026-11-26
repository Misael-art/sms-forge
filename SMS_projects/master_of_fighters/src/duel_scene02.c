#if defined(MOF_DUEL_PILOT)

#include "SMSlib.h"
#include "../inc/duel_rules.h"
#include "../inc/duel_probe.h"
#if defined(MOF_DUEL_REPERTOIRE)
#if !defined(MOF_DUEL_FAST_SAT)
#error The bank-backed scene requires the VBlank submission path.
#endif
#include <string.h>
#include "../inc/duel_audio.h"
#include "../inc/duel_commands.h"
#if defined(MOF_DUEL_SCENE_MIRROR)
#include "duel_mirror_assets.h"
#elif defined(MOF_DUEL_REPERTOIRE_ASSETS)
#include "duel_repertoire_assets.h"
#elif defined(MOF_DUEL_SCENE_WALK) || defined(MOF_DUEL_SCENE_SPECIALS)
#include "../out/diagnostics/repertoire_20261119/scene02-actions-bound-v1/duel_repertoire_assets.h"
#elif defined(MOF_DUEL_REPERTOIRE_CONTIGUOUS_SPRITES)
#include "../out/diagnostics/repertoire_20261119/scene02-repertoire-bound-b05/duel_repertoire_assets.h"
#elif defined(MOF_DUEL_REPERTOIRE_PRECOMPOSED)
#include "../out/diagnostics/repertoire_20261119/scene02-repertoire-bound-b03/duel_repertoire_assets.h"
#else
#include "../out/diagnostics/repertoire_20261119/scene02-repertoire-bound/duel_repertoire_assets.h"
#endif
#else
#include "../out/diagnostics/duel_execution_20261119/generated/duel_scene02_assets.h"
#endif

#if MOF_DUEL_HOLD != 6 && MOF_DUEL_HOLD != 8
#error Choose the owner-approved duel comparison threshold, 6 or 8.
#endif

SMS_EMBED_SEGA_ROM_HEADER(0, 0);

/* Comparison geometry, in pixels relative to the authored ground pivots. */
static const MofDuelGeometry scene_geometry[2] = {
    {{-11,-57,12,-4}, {{9,-23,25,-2},{9,-23,25,-2}}},
#if defined(MOF_DUEL_REPERTOIRE)
    /* Thrust pose 18 reaches -55 px facing left and +55 facing right.
       Keep the shared half-open hitbox inside the blade on both faces. */
    {{-11,-53,13,-3}, {{17,-37,55,-34},{17,-37,55,-34}}},
#else
    {{-11,-53,13,-3}, {{17,-43,64,-33},{17,-43,64,-33}}},
#endif
};

volatile unsigned char __at(0xC770) mof_duel_trace[MOF_DUEL_PROBE_BYTES];
volatile unsigned char __at(0xC7D2) mof_min_vline;
volatile unsigned char __at(0xC7E0) mof_smrt_magic[4];
volatile unsigned char __at(0xC7E4) mof_smrt_schema;
volatile unsigned char __at(0xC7EA) mof_vline;
volatile unsigned int __at(0xC7EB) mof_vblank_overrun;
volatile unsigned char __at(0xC7ED) mof_runtime_phase;
volatile unsigned char __at(0xC7EE) mof_worst_done;
volatile unsigned int __at(0xC7F0) mof_presented_frame;

static MofDuel duel;
#if !defined(MOF_DUEL_REPERTOIRE)
static MofDuelProbeActor observations[2];
#endif
static uint8_t hayato_player, orientation;
static uint8_t current_life[2];
#if !defined(MOF_DUEL_REPERTOIRE)
__sfr __at(0x7F) mof_psg_port;
static uint8_t sound_left;
static uint8_t cached_overlay, old_patch_count;
static uint8_t old_patch_x[MOF_DUEL_BG_PATCH_MAX], old_patch_y[MOF_DUEL_BG_PATCH_MAX];
static const uint8_t *last_patch;
static uint8_t last_patch_x;
#endif

#if defined(MOF_DUEL_FAST_SAT)
#define DUEL_SAT_Y_ADDRESS  0x3F00u
#define DUEL_SAT_XT_ADDRESS 0x3F80u
static uint8_t sat_y[64], sat_xt[128], sat_count;
#if defined(MOF_DUEL_SCENE_CROSSOVER)
static uint8_t sat_y_first, sat_xt_first, sat_xt_dirty;
#endif
#if defined(MOF_DUEL_REPERTOIRE_ASSETS)
static uint8_t sat_y_dirty;
#endif
#if !defined(MOF_DUEL_REPERTOIRE)
static uint8_t last_h_x, last_a_x, last_h_pose, last_a_pose;
#endif
static volatile uint8_t vblank_epoch;
volatile unsigned char __at(0xC7D4) mof_cadence_lines[4];

static void count_vblank(void)
{
    ++vblank_epoch;
}

static uint8_t wait_to_publish(uint8_t after, uint8_t last_line)
{
    uint8_t next, line;
    for (;;) {
        do {
            next = vblank_epoch;
        } while (next == after);
        line = SMS_getVCount();
        if (line >= 0xC0u && line <= last_line) {
            return next;
        }
        after = next;
    }
}
#endif

#if !defined(MOF_DUEL_REPERTOIRE)
static void emit(const uint8_t *meta, uint8_t pivot)
{
    uint8_t count = *meta++;
    ++meta; /* Overlay ID is used by the scene before SAT publication. */
#if defined(MOF_DUEL_FAST_SAT)
    uint8_t *next_y = sat_y + sat_count;
    uint8_t *next_xt = sat_xt + (uint16_t)sat_count * 2u;
    sat_count += count;
    while (count--) {
        *next_xt++ = pivot + *meta++ - 128u;
        *next_y++ = *meta++ - 1u;
        *next_xt++ = *meta++;
    }
#else
    while (count--) {
        uint8_t x = pivot + meta[0] - 128u;
        SMS_addSprite(x, meta[1], meta[2]);
        meta += 3;
    }
#endif
}

#if defined(MOF_DUEL_FAST_SAT)
static uint8_t prepare_sat(const uint8_t *hayato, const uint8_t *alis,
                           uint8_t h_pose, uint8_t a_pose, uint8_t h_x, uint8_t a_x)
{
    if (h_x == last_h_x && a_x == last_a_x && h_pose == last_h_pose && a_pose == last_a_pose)
        return 0u;
    sat_count = 0u;
    emit(hayato, h_x);
    emit(alis, a_x);
    if (sat_count < 64u) sat_y[sat_count] = 0xD0u;
    last_h_x = h_x;
    last_a_x = a_x;
    last_h_pose = h_pose;
    last_a_pose = a_pose;
    return 1u;
}
#endif
#endif

#if defined(MOF_DUEL_FAST_SAT) && !defined(MOF_DUEL_SCENE_MIRROR)
static void copy_sat(void)
{
#if defined(MOF_DUEL_REPERTOIRE)
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    if (sat_y_dirty)
        UNSAFE_SMS_VRAMmemcpy(DUEL_SAT_Y_ADDRESS + sat_y_first, sat_y + sat_y_first,
                              sat_count - sat_y_first + (sat_count < 64u));
    if (sat_xt_dirty && sat_count)
        UNSAFE_SMS_VRAMmemcpy(DUEL_SAT_XT_ADDRESS + sat_xt_first, sat_xt + sat_xt_first,
                              (uint16_t)sat_count * 2u - sat_xt_first);
#else
#if defined(MOF_DUEL_REPERTOIRE_ASSETS)
    if (sat_y_dirty)
#endif
    UNSAFE_SMS_VRAMmemcpy(DUEL_SAT_Y_ADDRESS, sat_y, sat_count + (sat_count < 64u));
    if (sat_count)
        UNSAFE_SMS_VRAMmemcpy(DUEL_SAT_XT_ADDRESS, sat_xt, (uint16_t)sat_count * 2u);
#endif
#else
    SMS_VRAMmemcpy_brief(DUEL_SAT_Y_ADDRESS, sat_y, sat_count + (sat_count < 64u));
    if (sat_count)
        SMS_VRAMmemcpy_brief(DUEL_SAT_XT_ADDRESS, sat_xt, (uint8_t)(sat_count * 2u));
#endif
}
#endif

#if defined(MOF_DUEL_REPERTOIRE)
volatile unsigned int __at(0xC7D8) mof_repertoire_delayed;
volatile unsigned char __at(0xC7DA) mof_repertoire_fault;
volatile unsigned char __at(0xC7DB) mof_vblank_start;
volatile unsigned char __at(0xC7DC) mof_vblank_end_high;
volatile unsigned char __at(0xC7DD) mof_probe_end;
volatile unsigned int __at(0xC7DE) mof_missed_epochs;
volatile unsigned char __at(0xC7C0) mof_render_stage_lines[4];
volatile unsigned char __at(0xC7C4) mof_vblank_payload[4];
#include "duel_pnt_stream.inc"
#if defined(MOF_DUEL_SCENE_MIRROR)
#include "duel_mirror_render.inc"
#else
#include "duel_repertoire_render.inc"

static MofDuelCommands command_inputs[2];
static const MofDuelCommandProfile standing_profile = {{MOF_DUEL_HOLD, MOF_DUEL_HOLD}, 0u};
#if defined(MOF_DUEL_SCENE_SPECIALS)
#define H_SPECIAL_ID , MOF_HAYATO_SPECIAL
#define A_SPECIAL_ID , MOF_ALIS_SPECIAL
#else
#define H_SPECIAL_ID
#define A_SPECIAL_ID
#endif
static const uint8_t first_frame[2][MOF_DUEL_NORMALS_PER_FIGHTER] = {
    {7u,1u,10u,13u H_SPECIAL_ID}, {20u,17u,23u,26u A_SPECIAL_ID}
};
static const uint8_t fist_ends[3] = {4u,6u,14u};
static const uint8_t light_kick_ends[3] = {5u,7u,17u};
static const uint8_t heavy_kick_ends[3] = {10u,12u,27u};
static const uint8_t cut_ends[6] = {8u,9u,11u,18u,20u,25u};
static const uint8_t thrust_ends[3] = {5u,7u,18u};
static const MofDuelBox h_fist[2] = {{9,-54,33,-38},{9,-54,33,-38}};
static const MofDuelBox h_light[2] = {{12,-38,42,-24},{12,-38,42,-24}};
static const MofDuelBox h_heavy[2] = {{12,-42,47,-28},{12,-42,47,-28}};
static const MofDuelBox a_fist[2] = {{9,-40,30,-25},{9,-40,30,-25}};
static const MofDuelBox a_light[2] = {{11,-30,35,-16},{11,-30,35,-16}};
static const MofDuelBox a_heavy[2] = {{11,-46,39,-31},{11,-46,39,-31}};
#if defined(MOF_DUEL_SCENE_SPECIALS)
static const uint8_t h_special_ends[] = {10u,12u,30u}, a_special_ends[] = {7u,9u,23u};
static const MofDuelBox h_special[2] = {{19,-47,50,-37},{19,-47,50,-37}};
static const MofDuelBox a_special[2] = {{16,-48,34,-23},{16,-48,34,-23}};
#define H_SPECIAL_RULE , {h_special,h_special_ends,10u,2u,30u,16u,3u}
#define A_SPECIAL_RULE , {a_special,a_special_ends,7u,2u,23u,13u,3u}
#else
#define H_SPECIAL_RULE
#define A_SPECIAL_RULE
#endif
static const MofDuelStandingNormal repertoire_normals[2][MOF_DUEL_NORMALS_PER_FIGHTER] = {
    {{h_fist,fist_ends,4u,2u,14u,6u,3u}, {&scene_geometry[0].active[0],cut_ends,9u,2u,25u,12u,6u},
     {h_light,light_kick_ends,5u,2u,17u,8u,3u}, {h_heavy,heavy_kick_ends,10u,2u,27u,13u,3u} H_SPECIAL_RULE},
    {{a_fist,fist_ends,4u,2u,14u,6u,3u}, {&scene_geometry[1].active[0],thrust_ends,5u,2u,18u,10u,3u},
     {a_light,light_kick_ends,5u,2u,17u,8u,3u}, {a_heavy,heavy_kick_ends,10u,2u,27u,12u,3u} A_SPECIAL_RULE},
};

#if defined(MOF_DUEL_SCENE_SPECIALS)
static uint8_t special_window[2], special_face[2];

static uint8_t read_special(uint8_t player, uint8_t keys, uint8_t previous_buttons)
{
    uint8_t *window = &special_window[player];
    if (!*window && keys != MOF_DUEL_DOWN) return 0u;
    uint8_t face = duel.fighters[player].face_right;
    uint8_t forward = face ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t directions = keys & (MOF_DUEL_UP | MOF_DUEL_DOWN | MOF_DUEL_LEFT | MOF_DUEL_RIGHT);
    if (face != special_face[player] || !mof_duel_next_tick_free(&duel, player)) {
        *window = 0u;
        special_face[player] = face;
        if (duel.fighters[player].state != MOF_DUEL_READY) return 0u;
    }
    if (keys == MOF_DUEL_DOWN) {
        *window = 8u;
        return 0u;
    }
    if (*window && keys == (forward | MOF_DUEL_ONE) && !(previous_buttons & MOF_DUEL_ONE)) {
        *window = 0u;
        return 1u;
    }
    if (keys & (MOF_DUEL_ONE | MOF_DUEL_TWO) || (directions && directions != forward)) *window = 0u;
    else if (*window) --*window;
    return 0u;
}
#endif

static uint8_t read_normal(uint8_t player, uint8_t keys)
{
    MofDuelCommands *input = &command_inputs[player];
    uint16_t command;
#if defined(MOF_DUEL_SCENE_SPECIALS)
#if defined(MOF_DUEL_SCENE_POSTURES)
    if (player != hayato_player &&
        (duel.body[1u - hayato_player].motion.mode == MOF_MOTION_AIR || duel.body[1u - hayato_player].jump_pending))
        special_window[player] = 0u;
    else
#endif
    if (read_special(player, keys, input->last_buttons)) {
        mof_duel_commands_reset(input, keys);
        return MOF_DUEL_SPECIAL;
    }
#endif
#if defined(MOF_DUEL_SCENE_POSTURES)
    if (player != hayato_player && !mof_duel_alis_standing_input(&duel, player, keys)) {
        if ((keys | input->last_buttons) & (MOF_DUEL_ONE | MOF_DUEL_TWO))
            mof_duel_commands_reset(input, keys);
        return MOF_DUEL_NO_NORMAL;
    }
#endif
    if (!((keys | input->last_buttons) & (MOF_DUEL_ONE | MOF_DUEL_TWO)))
        return MOF_DUEL_NO_NORMAL;
    command = mof_duel_commands_read(input, &standing_profile,
        keys, MOF_INPUT_STANDING, mof_duel_next_tick_free(&duel, player));
    switch (command) {
        case 1u: return MOF_INPUT_SHORT_ONE;
        case 2u: return MOF_INPUT_LONG_ONE;
        case 4u: return MOF_INPUT_SHORT_TWO;
        case 8u: return MOF_INPUT_LONG_TWO;
        default: return MOF_DUEL_NO_NORMAL;
    }
}

typedef struct {
    uint16_t since;
    int16_t pivot;
    uint8_t state, pose;
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    uint8_t face_right;
#endif
} RepertoireForecastActor;

#if defined(MOF_DUEL_SCENE_WALK)
static const uint8_t walk_first[2][2] = {
    {MOF_HAYATO_WALK_FORWARD, MOF_HAYATO_WALK_BACK},
    {MOF_ALIS_WALK_FORWARD, MOF_ALIS_WALK_BACK}
};
static uint8_t walk_cycle[2], walk_distance[2];

static void update_walk(uint8_t player, int16_t previous_x)
{
    const MofDuelFighter *fighter = &duel.fighters[player];
    uint8_t direction;
    if (fighter->state != MOF_DUEL_READY || fighter->x == previous_x
#if defined(MOF_DUEL_SCENE_POSTURES)
        || (player != hayato_player &&
            (duel.body[1u - hayato_player].motion.mode == MOF_MOTION_AIR || duel.body[1u - hayato_player].air_step))
#endif
    ) {
        walk_cycle[player] = 0u;
        return;
    }
    direction = ((fighter->x > previous_x) == fighter->face_right) ? 1u : 2u;
    walk_distance[player] = direction == walk_cycle[player] ? (walk_distance[player] + 1u) & 15u : 0u;
    walk_cycle[player] = direction;
}
#endif

#if defined(MOF_DUEL_SCENE_POSTURES)
static uint8_t alis_posture_view;

static uint8_t alis_posture_frame(uint8_t local)
{
    return MOF_ALIS_POSTURE_START + local - 1u;
}

static void alis_posture_forecast(uint8_t *next, uint8_t *later)
{
    const MofDuelMotion *motion = &duel.body[1u - hayato_player].motion;
    *next = *later = REP_NO_FRAME;
    if (duel.body[1u - hayato_player].jump_pending) {
        *next = alis_posture_frame(MOF_ALIS_JUMP_RISE);
        if (duel.fighters[1u - hayato_player].guarding != MOF_GUARD_OPEN) {
            *later = alis_posture_frame(MOF_ALIS_JUMP_GUARD);
        } else if (duel.body[1u - hayato_player].jump_pending & (MOF_DUEL_LEFT | MOF_DUEL_RIGHT)) {
            *later = alis_posture_frame(MOF_ALIS_JUMP_DIAGONAL);
        }
    } else if (motion->mode == MOF_MOTION_AIR) {
        switch (alis_posture_view) {
            case MOF_ALIS_JUMP_RISE:
                if (mof_duel_alis_air_guard(&duel, 1u - hayato_player)) {
                    *next = alis_posture_frame(MOF_ALIS_JUMP_GUARD);
                    *later = alis_posture_frame(motion->vx ? MOF_ALIS_JUMP_DIAGONAL : MOF_ALIS_JUMP_APEX);
                } else {
                    *next = alis_posture_frame(motion->vx ? MOF_ALIS_JUMP_DIAGONAL : MOF_ALIS_JUMP_APEX);
                    *later = alis_posture_frame(MOF_ALIS_JUMP_GUARD);
                }
                break;
            case MOF_ALIS_JUMP_DIAGONAL:
                *next = alis_posture_frame(MOF_ALIS_JUMP_APEX);
                break;
            case MOF_ALIS_JUMP_FALL:
                *next = alis_posture_frame(MOF_ALIS_CROUCH_TRANSITION);
                if (motion->vy < MOF_ALIS_GUARD_UNFOLD_SPEED)
                    *later = alis_posture_frame(MOF_ALIS_JUMP_GUARD);
                break;
            case MOF_ALIS_JUMP_GUARD:
                *next = alis_posture_frame(MOF_ALIS_JUMP_FALL);
                if (motion->vy < 24) {
                    *later = alis_posture_frame(motion->vx && motion->vy < -12
                                                ? MOF_ALIS_JUMP_DIAGONAL : MOF_ALIS_JUMP_APEX);
                } else {
                    *later = alis_posture_frame(MOF_ALIS_CROUCH_TRANSITION);
                }
                break;
            default:
                *next = alis_posture_frame(MOF_ALIS_JUMP_FALL);
                *later = alis_posture_frame(MOF_ALIS_JUMP_GUARD);
                break;
        }
    } else if (alis_posture_view == MOF_ALIS_CROUCH_TRANSITION) {
        *next = motion->mode == MOF_MOTION_CROUCH ? alis_posture_frame(MOF_ALIS_CROUCH)
                                                : REP_ALIS_IDLE;
    }
}
#endif

static uint8_t repertoire_views_changed(void)
{
    static RepertoireForecastActor prior[2];
    static uint8_t valid;
    uint8_t i, same = valid;
    const MofDuelFighter *fighter;
    if (((duel.fighters[0].keys | duel.fighters[1].keys) & (MOF_DUEL_ONE | MOF_DUEL_TWO)) ||
#if defined(MOF_DUEL_SCENE_POSTURES)
        alis_posture_view || rep_logical_frame(rep_wanted.frame[1]) >= MOF_ALIS_POSTURE_START ||
#endif
#if defined(MOF_DUEL_SCENE_WALK)
        walk_cycle[0] || walk_cycle[1] ||
#endif
#if defined(MOF_DUEL_SCENE_SPECIALS)
        special_window[0] || special_window[1] ||
#endif
        (duel.fighters[0].state != MOF_DUEL_ATTACK && duel.fighters[1].state != MOF_DUEL_ATTACK)) {
        valid = 0u;
        return 1u;
    }
    for (i = 0u; i < 2u; ++i) {
        fighter = &duel.fighters[i];
        if (prior[i].pose != duel.tested_pose[i] || prior[i].state != fighter->state ||
#if defined(MOF_DUEL_SCENE_CROSSOVER)
            prior[i].face_right != fighter->face_right ||
#endif
            prior[i].pivot != fighter->x || prior[i].since != fighter->state_since) {
            same = 0u;
            prior[i].pose = duel.tested_pose[i];
            prior[i].state = fighter->state;
            prior[i].pivot = fighter->x;
            prior[i].since = fighter->state_since;
#if defined(MOF_DUEL_SCENE_CROSSOVER)
            prior[i].face_right = fighter->face_right;
#endif
        }
    }
    /* With buttons released, the two pose deadlines advance at the same rate. */
    valid = 1u;
    return !same;
}

#if defined(MOF_DUEL_SCENE_CROSSOVER)
static void repertoire_orient(RepertoireView *wanted, RepertoireView *forecast,
                               RepertoireView *later, uint8_t planned[4])
{
    uint8_t offset[2], i;
    offset[0] = duel.fighters[hayato_player].face_right ? 0u : MOF_REPERTOIRE_FRAMES;
    offset[1] = duel.fighters[1u - hayato_player].face_right ? MOF_REPERTOIRE_FRAMES : 0u;
    rep_side_offset = offset[0];
    for (i = 0u; i < 2u; ++i) {
        wanted->frame[i] += offset[i];
        forecast->frame[i] += offset[i];
        later->frame[i] += offset[i];
    }
    for (i = 0u; i < 4u; ++i) {
        if (planned[i] != REP_NO_FRAME) planned[i] += offset[mof_repertoire_actor[planned[i]]];
    }
}
#endif

static void repertoire_views(RepertoireView *wanted, RepertoireView *forecast,
                             RepertoireView *later, uint8_t planned[4])
{
    uint8_t actor, player, pose, idle, frame, button, normal_id, first, second;
    uint8_t delay[2], next[2], following[2], later_delay[2];
    uint8_t buttons = duel.fighters[0].keys | duel.fighters[1].keys;
    const MofDuelFighter *fighter;
    const MofDuelStandingNormal *normal;
#if defined(MOF_DUEL_SCENE_POSTURES)
    wanted->alis_y = duel.body[1u - hayato_player].y_offset;
    /* Held attack buttons cannot start standing normals during a jump.
       Keep the sprite-only forecast when Hayato is free of attack input. */
    if (wanted->alis_y || duel.body[1u - hayato_player].jump_pending)
        buttons = duel.fighters[hayato_player].keys;
#endif
#if defined(MOF_REPERTOIRE_SPRITE_WALK)
    rep_sprite_walk_view = 0u;
#endif
    if (duel.fighters[0].state != MOF_DUEL_ATTACK && duel.fighters[1].state != MOF_DUEL_ATTACK &&
#if defined(MOF_DUEL_SCENE_WALK) && !defined(MOF_REPERTOIRE_SPRITE_WALK)
        !walk_cycle[0] && !walk_cycle[1] &&
#endif
#if defined(MOF_DUEL_SCENE_SPECIALS)
        !special_window[0] && !special_window[1] &&
#endif
        !(buttons & (MOF_DUEL_ONE | MOF_DUEL_TWO))) {
        wanted->frame[0] = 0u;
        wanted->frame[1] = REP_ALIS_IDLE;
        wanted->pivot[0] = (uint8_t)duel.fighters[hayato_player].x;
        wanted->pivot[1] = (uint8_t)duel.fighters[1u - hayato_player].x;
        planned[0] = planned[1] = planned[2] = planned[3] = REP_NO_FRAME;
#if defined(MOF_REPERTOIRE_SPRITE_WALK)
        rep_sprite_walk_view = 1u;
        if (walk_cycle[0] || walk_cycle[1]) {
            first = (walk_distance[1u - hayato_player] & 3u) > (walk_distance[hayato_player] & 3u);
#if defined(MOF_DUEL_SCENE_POSTURES)
            if (alis_posture_view) first = 0u;
#endif
            for (actor = 0u; actor < 2u; ++actor) {
                player = actor ^ hayato_player;
#if defined(MOF_DUEL_SCENE_POSTURES)
                if (actor && alis_posture_view) continue;
#endif
                if (!walk_cycle[player]) continue;
                idle = walk_first[actor][walk_cycle[player] - 1u];
                frame = walk_distance[player] >> 2;
                wanted->frame[actor] = idle + frame;
                planned[actor ^ first] = idle + ((frame + 1u) & 3u);
                planned[2u + (actor ^ first)] = idle + ((frame + 2u) & 3u);
            }
        }
#endif
#if defined(MOF_DUEL_SCENE_POSTURES)
        if (alis_posture_view) {
            wanted->frame[1] = alis_posture_frame(alis_posture_view);
            alis_posture_forecast(&planned[1], &planned[3]);
        }
#endif
        *forecast = *wanted;
        *later = *wanted;
        return;
    }
    for (actor = 0u; actor < 2u; ++actor) {
        player = actor ? 1u - hayato_player : hayato_player;
        fighter = &duel.fighters[player];
        idle = actor ? REP_ALIS_IDLE : 0u;
        pose = fighter->state == MOF_DUEL_ATTACK ? duel.tested_pose[player] : 0u;
        wanted->pivot[actor] = (uint8_t)fighter->x;
        delay[actor] = later_delay[actor] = 255u;
        following[actor] = REP_NO_FRAME;
#if defined(MOF_DUEL_SCENE_POSTURES)
        if (actor && alis_posture_view) {
            idle = alis_posture_frame(alis_posture_view);
            if (alis_posture_view != MOF_ALIS_STAND_GUARD || fighter->state != MOF_DUEL_READY) {
                wanted->frame[actor] = idle;
                alis_posture_forecast(&next[actor], &following[actor]);
                if (next[actor] != REP_NO_FRAME) delay[actor] = 1u;
                else next[actor] = wanted->frame[actor];
                if (following[actor] != REP_NO_FRAME) later_delay[actor] = 2u;
                continue;
            }
            /* A held attack can still mature while the standing guard is
               visible. Warm its startup and contact from the same queue. */
        }
#endif
        if (!pose || fighter->standing_normal >= MOF_DUEL_NORMALS_PER_FIGHTER) {
            wanted->frame[actor] = next[actor] = idle;
#if defined(MOF_DUEL_SCENE_WALK)
            if (walk_cycle[player]) {
                uint8_t origin = walk_first[actor][walk_cycle[player] - 1u];
                uint8_t step = walk_distance[player] >> 2;
                wanted->frame[actor] = origin + step;
                next[actor] = origin + ((step + 1u) & 3u);
                delay[actor] = 4u - (walk_distance[player] & 3u);
                following[actor] = origin + ((step + 2u) & 3u);
                later_delay[actor] = delay[actor] + 4u;
            }
#endif
            button = fighter->keys & (MOF_DUEL_ONE | MOF_DUEL_TWO);
#if defined(MOF_DUEL_SCENE_SPECIALS)
            if (fighter->state == MOF_DUEL_READY && special_window[player]) {
                next[actor] = first_frame[actor][MOF_DUEL_SPECIAL];
                following[actor] = next[actor] + 1u;
                delay[actor] = 1u;
                later_delay[actor] = 1u + repertoire_normals[actor][MOF_DUEL_SPECIAL].pose_ends[0];
            }
#endif
            if (fighter->state == MOF_DUEL_READY &&
                (button == MOF_DUEL_ONE || button == MOF_DUEL_TWO)) {
                normal_id = button == MOF_DUEL_ONE ? 0u : 2u;
                if (command_inputs[player].hold_age[normal_id >> 1] >= MOF_DUEL_HOLD - 2u)
                    ++normal_id;
                next[actor] = first_frame[actor][normal_id];
                delay[actor] = 1u;
                following[actor] = next[actor] + 1u;
                later_delay[actor] = 1u + repertoire_normals[actor][normal_id].pose_ends[0];
            }
            continue;
        }
        normal = &repertoire_normals[actor][fighter->standing_normal];
        frame = first_frame[actor][fighter->standing_normal] + pose - 1u;
        wanted->frame[actor] = frame;
        next[actor] = pose < normal->pose_count ? frame + 1u : idle;
        delay[actor] = normal->pose_ends[pose - 1u] - (uint8_t)mof_duel_age(&duel, fighter);
        if (pose < normal->pose_count) {
            later_delay[actor] = delay[actor] + normal->pose_ends[pose] - normal->pose_ends[pose - 1u];
            following[actor] = pose + 1u < normal->pose_count ? frame + 2u : idle;
        }
    }
    first = delay[1] < delay[0] ? 1u : 0u;
    second = 1u - first;
    planned[0] = delay[first] < 255u ? next[first] : REP_NO_FRAME;
    planned[1] = delay[second] < 255u ? next[second] : REP_NO_FRAME;
    planned[2] = following[first];
    planned[3] = following[second];
    *forecast = *wanted;
    frame = delay[first];
    for (actor = 0u; actor < 2u; ++actor) {
        if (delay[actor] != frame) continue;
        forecast->frame[actor] = next[actor];
        next[actor] = following[actor];
        delay[actor] = later_delay[actor];
    }
    *later = *forecast;
    frame = delay[0] < delay[1] ? delay[0] : delay[1];
    for (actor = 0u; actor < 2u; ++actor)
        if (delay[actor] == frame && next[actor] != REP_NO_FRAME)
            later->frame[actor] = next[actor];
}
#endif /* MOF_DUEL_SCENE_MIRROR */
#else
static void upload_overlay(uint8_t bank)
{
    if (!bank || bank == cached_overlay) return;
    if (orientation) {
        SMS_loadTiles(mof_duel_overlays_1[bank], MOF_DUEL_STATIC_1, MOF_DUEL_OVERLAY_1 * 32u);
    } else {
        SMS_loadTiles(mof_duel_overlays_0[bank], MOF_DUEL_STATIC_0, MOF_DUEL_OVERLAY_0 * 32u);
    }
    cached_overlay = bank;
}

static const uint8_t *patch_for(uint8_t pose, uint8_t x)
{
    if (pose == 1u) {
        return orientation ? mof_duel_patch_1_prepare[x & 7u] : mof_duel_patch_0_prepare[x & 7u];
    }
    if (pose == 2u) {
        return orientation ? mof_duel_patch_1_thrust[x & 7u] : mof_duel_patch_0_thrust[x & 7u];
    }
    return 0;
}

static void publish_patch(const uint8_t *patch, uint8_t origin_col)
{
    uint8_t index, row, col;
    if (patch == last_patch && (!patch || origin_col == last_patch_x)) return;
    for (index = 0u; index < old_patch_count; ++index) {
        col = old_patch_x[index];
        row = old_patch_y[index];
        SMS_setTileatXY(col, row, 256u + mof_duel_bg_rows[row]);
    }
    old_patch_count = patch ? *patch++ : 0u;
    for (index = 0u; index < old_patch_count; ++index) {
        col = origin_col + patch[0] - 128u;
        row = patch[1];
        SMS_loadTiles(mof_duel_bg_patches + (unsigned int)patch[2] * 32u, 288u + index, 32u);
        SMS_setTileatXY(col, row, 288u + index);
        old_patch_x[index] = col;
        old_patch_y[index] = row;
        patch += 3;
    }
}
#endif

#define HUD_EMPTY_TILE 256u
#define HUD_FULL_TILE 261u
#define HUD_PARTIAL_BASE 272u
#define HUD_SEGMENTS 10u

static uint8_t hud_first[2], hud_count[2], hud_tiles[2][HUD_SEGMENTS];

typedef char HudTilesAfterStage[
    (sizeof(mof_duel_bg_stage) <= (HUD_PARTIAL_BASE - HUD_EMPTY_TILE) * 32u) ? 1 : -1];

static void load_hud_tiles(void)
{
    const uint8_t *empty = mof_duel_bg_stage;
    const uint8_t *full = mof_duel_bg_stage + (HUD_FULL_TILE - HUD_EMPTY_TILE) * 32u;
    uint8_t tile[32], pixels, plane, mask = 0u;
    for (pixels = 1u; pixels < 8u; ++pixels) {
        mask = (mask >> 1u) | 0x80u;
        for (plane = 0u; plane < sizeof(tile); ++plane)
            tile[plane] = (full[plane] & mask) | (empty[plane] & (uint8_t)~mask);
        SMS_loadTiles(tile, HUD_PARTIAL_BASE + pixels - 1u, sizeof(tile));
    }
}

static uint8_t health_tile(uint8_t life)
{
    static const uint8_t partial_pixels[10] = {0u, 1u, 2u, 3u, 4u, 4u, 5u, 6u, 7u, 7u};
    if (life >= 10u) return HUD_FULL_TILE - HUD_EMPTY_TILE;
    if (!life) return 0u;
    return HUD_PARTIAL_BASE - HUD_EMPTY_TILE + partial_pixels[life] - 1u;
}

static void prepare_hud(void)
{
    uint8_t player, index, life, previous_life, tile, count;
    uint8_t *tiles;
    for (player = 0u; player < 2u; ++player) {
        life = duel.fighters[player].life;
        previous_life = current_life[player];
        hud_count[player] = 0u;
        if (previous_life == life) continue;
        current_life[player] = life;
        /* At boot the stage already supplies empty tiles across both bars. */
        if (previous_life == 255u) previous_life = 0u;
        tiles = hud_tiles[player];
        count = 0u;
        for (index = 0u; index < HUD_SEGMENTS && life != previous_life; ++index) {
            tile = health_tile(life);
            if (count || tile != health_tile(previous_life)) {
                if (!count) hud_first[player] = index;
                tiles[count++] = tile;
            }
            life = life > 10u ? life - 10u : 0u;
            previous_life = previous_life > 10u ? previous_life - 10u : 0u;
        }
        hud_count[player] = count;
    }
}

static void publish_hud(void)
{
    uint8_t player, count;
    const uint8_t *tiles;
    for (player = 0u; player < 2u; ++player) {
        count = hud_count[player];
        if (!count) continue;
        SMS_setNextTileatLoc(32u + (player ? 20u : 2u) + hud_first[player]);
        tiles = hud_tiles[player];
        do {
            SMS_setTile(HUD_EMPTY_TILE | *tiles++);
        } while (--count);
    }
}

#if !defined(MOF_DUEL_REPERTOIRE)
static void update_audio(void)
{
    uint8_t hit = duel.fighters[0].contact == MOF_DUEL_LANDED ||
                  duel.fighters[1].contact == MOF_DUEL_LANDED;
    uint8_t guarded = duel.fighters[0].contact == MOF_DUEL_GUARDED ||
                      duel.fighters[1].contact == MOF_DUEL_GUARDED;
    if (hit || guarded) {
        mof_psg_port = hit ? 0xE4u : 0xE7u;
        mof_psg_port = 0xF5u;
        sound_left = hit ? 6u : 3u;
    } else if (sound_left && !--sound_left) {
        mof_psg_port = 0xFFu;
    }
}
#endif

#if defined(MOF_DUEL_SCENE_MIRROR)
#include "duel_mirror_round.inc"
#else
#if defined(MOF_DUEL_REPERTOIRE)
/* SDCC Z80 stores the four 16-bit coordinates in probe byte order. */
typedef char ProbeBoxLayout[(sizeof(MofDuelBox) == 8u) ? 1 : -1];

static void publish_probe_actor(volatile uint8_t *out, const MofDuelFighter *fighter,
                                uint8_t pose, uint8_t tested_pose, uint8_t active,
                                const MofDuelBox *attack, const MofDuelBox *hurt)
{
    uint8_t flags = MOF_DUEL_PROBE_HAS_HURT;
    out[0] = fighter->fighter;
    out[1] = fighter->keys;
    out[2] = fighter->state;
    out[3] = (uint8_t)(duel.tick - fighter->state_since);
    out[4] = rep_logical_frame(pose);
    out[5] = rep_loaded[pose] == rep_frames[pose].count ? out[4] : REP_NO_FRAME;
    out[6] = rep_logical_frame(rep_displayed.frame[fighter->fighter]);
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    if (rep_displayed.frame[fighter->fighter] != REP_NO_FRAME) {
        flags |= MOF_DUEL_PROBE_PRESENTED_FACE;
        if ((rep_displayed.frame[fighter->fighter] >= MOF_REPERTOIRE_FRAMES) == fighter->fighter)
            flags |= MOF_DUEL_PROBE_PRESENTED_RIGHT;
    }
#endif
    out[7] = fighter->contact;
    out[8] = fighter->life;
    if (fighter->face_right) flags |= MOF_DUEL_PROBE_FACES_RIGHT;
    if (fighter->state == MOF_DUEL_READY) flags |= MOF_DUEL_PROBE_CAN_ACT;
    if (active) {
        flags |= MOF_DUEL_PROBE_HAS_ATTACK;
        memcpy((void *)(out + 14u), attack, sizeof(*attack));
    }
    out[9] = flags;
    out[10] = (uint8_t)fighter->x;
    out[11] = 0u;
#if defined(MOF_DUEL_SCENE_POSTURES)
    out[12] = fighter->fighter == MOF_DUEL_ALIS ? 144u + duel.body[1u - hayato_player].y_offset : 144u;
#else
    out[12] = 144u;
#endif
    out[13] = 0u;
    memcpy((void *)(out + 22u), hurt, sizeof(*hurt));
    mof_duel_probe_word(out + 30u, fighter->free_since);
    out[32] = tested_pose;
}

static void publish_probe(const uint8_t poses[2])
{
    uint8_t writing = (uint8_t)(mof_duel_trace[4] | 1u);
    mof_duel_trace[4] = writing;
    if (writing == 1u) {
        mof_duel_trace[0] = 'M'; mof_duel_trace[1] = 'F';
        mof_duel_trace[2] = 'D'; mof_duel_trace[3] = '1';
        mof_duel_trace[5] = MOF_DUEL_PROBE_BYTES;
    }
    mof_duel_probe_word(mof_duel_trace + 6u, duel.tick);
    publish_probe_actor(mof_duel_trace + 8u, &duel.fighters[0], poses[0],
        duel.tested_pose[0], duel.tested_active[0], &duel.tested_attack[0], &duel.tested_hurt[0]);
    publish_probe_actor(mof_duel_trace + 41u, &duel.fighters[1], poses[1],
        duel.tested_pose[1], duel.tested_active[1], &duel.tested_attack[1], &duel.tested_hurt[1]);
    mof_duel_trace[4] = (uint8_t)(writing + 1u);
}
#else
static void copy_box(MofDuelProbeBox *out, const MofDuelBox *in)
{
    out->left = in->left;
    out->top = in->top;
    out->right = in->right;
    out->bottom = in->bottom;
}

static void publish_probe(const uint8_t poses[2])
{
    uint8_t i;
    for (i = 0u; i < 2u; ++i) {
        const MofDuelFighter *fighter = &duel.fighters[i];
        MofDuelProbeActor *record = &observations[i];
        record->fighter = fighter->fighter;
        record->keys = fighter->keys;
        record->state = fighter->state;
        record->action_tick = (uint8_t)mof_duel_age(&duel, fighter);
        record->pose_requested = poses[i];
        record->pose_resident = poses[i];
        record->pose_presented = poses[i];
        record->tested_pose = duel.tested_pose[i];
        record->contact = fighter->contact;
        record->life = fighter->life;
        record->flags = MOF_DUEL_PROBE_HAS_HURT;
        if (fighter->face_right) record->flags |= MOF_DUEL_PROBE_FACES_RIGHT;
        if (fighter->state == MOF_DUEL_READY) record->flags |= MOF_DUEL_PROBE_CAN_ACT;
        if (duel.tested_active[i]) {
            record->flags |= MOF_DUEL_PROBE_HAS_ATTACK;
            copy_box(&record->attack, &duel.tested_attack[i]);
        }
        copy_box(&record->hurt, &duel.tested_hurt[i]);
        record->pivot_x = fighter->x;
        record->pivot_y = 144;
        record->free_since = fighter->free_since;
    }
    mof_duel_probe_publish(mof_duel_trace, duel.tick, observations);
}
#endif

void main(void)
{
    uint8_t row, col, boot_selectors;
    uint8_t poses[2];
    uint16_t keys;
#if defined(MOF_DUEL_REPERTOIRE)
    RepertoireView wanted, forecast, later;
    uint8_t planned[4];
#else
    const uint8_t *const *hayato_meta;
    const uint8_t *const *alis_meta;
#endif
    int16_t hx, ax;
#if defined(MOF_DUEL_FAST_SAT)
    uint8_t submitted_epoch;
#endif
    SMS_displayOff();
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
    SMS_waitForVBlank();
    keys = SMS_getKeysStatus();
    boot_selectors = (uint8_t)(keys & (PORT_A_KEY_RIGHT | PORT_A_KEY_UP));
#if defined(MOF_DUEL_ALIS_P1)
    orientation = (keys & PORT_A_KEY_RIGHT) == 0u;
    hayato_player = (keys & PORT_A_KEY_UP) == 0u;
#else
    orientation = (keys & PORT_A_KEY_RIGHT) != 0u;
    hayato_player = (keys & PORT_A_KEY_UP) != 0u;
#endif
    hx = orientation ? 144 : 111;
    ax = orientation ? 111 : 144;
    if (!mof_duel_init(&duel, scene_geometry, MOF_DUEL_HOLD, hayato_player,
                       hayato_player ? ax : hx, hayato_player ? hx : ax,
                       MOF_DUEL_ARENA_MARGIN, 255 - MOF_DUEL_ARENA_MARGIN, 24)) {
        for (;;) SMS_waitForVBlank();
    }
    SMS_loadSpritePalette(mof_duel_sprite_palette);
    SMS_loadBGPalette(mof_duel_bg_palette);
    SMS_loadTiles(mof_duel_bg_stage, 256u, sizeof(mof_duel_bg_stage));
    load_hud_tiles();
#if defined(MOF_DUEL_REPERTOIRE)
    if (!mof_duel_set_standing_normals(&duel, repertoire_normals))
        for (;;) SMS_waitForVBlank();
    mof_duel_commands_reset(&command_inputs[0], 0u);
    mof_duel_commands_reset(&command_inputs[1], 0u);
    rep_init(orientation);
#else
    if (orientation) {
        SMS_loadTiles(mof_duel_atlas_1, 0u, sizeof(mof_duel_atlas_1));
        hayato_meta = mof_duel_hayato_poses_1;
        alis_meta = mof_duel_alis_poses_1;
    } else {
        SMS_loadTiles(mof_duel_atlas_0, 0u, sizeof(mof_duel_atlas_0));
        hayato_meta = mof_duel_hayato_poses_0;
        alis_meta = mof_duel_alis_poses_0;
    }
#endif
    SMS_setNextTileatLoc(0u);
    for (row = 0u; row < 24u; ++row) {
        for (col = 0u; col < 32u; ++col) SMS_setTile(256u + mof_duel_bg_rows[row]);
    }
    current_life[0] = current_life[1] = 255u;
    prepare_hud();
    publish_hud();
    mof_duel_trace[4] = 0u;
#if defined(MOF_DUEL_REPERTOIRE)
    mof_vblank_end_high = 0u;
    mof_missed_epochs = 0u;
#endif
    mof_smrt_magic[0] = 'S'; mof_smrt_magic[1] = 'M';
    mof_smrt_magic[2] = 'R'; mof_smrt_magic[3] = 'T';
    mof_smrt_schema = 1u;
    mof_min_vline = 255u;
    mof_vblank_overrun = mof_presented_frame = mof_worst_done = 0u;
#if defined(MOF_DUEL_REPERTOIRE)
    mof_duel_audio_init();
#else
    mof_psg_port = 0xFFu;
#endif
#if defined(MOF_DUEL_FAST_SAT)
#if !defined(MOF_DUEL_REPERTOIRE)
    last_h_x = 255u;
#endif
    SMS_setFrameInterruptHandler(count_vblank);
    submitted_epoch = vblank_epoch;
#endif
    SMS_displayOn();
    for (;;) {
#if defined(MOF_DUEL_REPERTOIRE)
        uint8_t p1, p2, n1, n2, vline, next_epoch, views_changed, submit_deadline;
#else
        uint8_t h_pose, a_pose, a_x, vline;
        const uint8_t *patch;
#endif
#if defined(MOF_DUEL_FAST_SAT)
#if !defined(MOF_DUEL_REPERTOIRE)
        uint8_t sat_changed;
#endif
        mof_cadence_lines[0] = SMS_getVCount();
#endif
        keys = SMS_getKeysStatus();
        if (boot_selectors) {
            /* Ignore each startup selector until it is released. Other
               directions and both controllers remain available. */
            boot_selectors &= (uint8_t)keys;
            keys &= (uint16_t)~boot_selectors;
        }
        mof_runtime_phase = 1u;
#if defined(MOF_DUEL_REPERTOIRE)
        p1 = (uint8_t)(keys & 63u);
        p2 = (uint8_t)((keys >> 6u) & 63u);
        n1 = read_normal(0u, p1);
        n2 = read_normal(1u, p2);
#if defined(MOF_DUEL_SCENE_WALK)
        {
            int16_t previous_x1 = duel.fighters[0].x, previous_x2 = duel.fighters[1].x;
            mof_duel_step_normal(&duel, p1, p2, n1, n2);
            update_walk(0u, previous_x1);
            update_walk(1u, previous_x2);
        }
#else
        mof_duel_step_normal(&duel, p1, p2, n1, n2);
#endif
#else
        mof_duel_step(&duel, (uint8_t)(keys & 63u), (uint8_t)((keys >> 6u) & 63u));
#endif
#if defined(MOF_DUEL_FAST_SAT)
        mof_cadence_lines[1] = SMS_getVCount();
#endif
#if defined(MOF_DUEL_REPERTOIRE)
#if defined(MOF_DUEL_SCENE_POSTURES)
        alis_posture_view = mof_duel_posture_pose(&duel, 1u - hayato_player);
        if (alis_posture_view == MOF_ALIS_STAND_GUARD &&
            duel.fighters[1u - hayato_player].state == MOF_DUEL_READY &&
            walk_cycle[1u - hayato_player])
            alis_posture_view = MOF_ALIS_NO_POSTURE;
#endif
        views_changed = repertoire_views_changed();
        if (views_changed) {
            repertoire_views(&wanted, &forecast, &later, planned);
#if defined(MOF_DUEL_SCENE_CROSSOVER)
            repertoire_orient(&wanted, &forecast, &later, planned);
#endif
        }
        mof_render_stage_lines[0] = SMS_getVCount();
        poses[hayato_player] = wanted.frame[0];
        poses[1u - hayato_player] = wanted.frame[1];
        rep_prepare(&wanted, &forecast, &later, planned, views_changed);
        mof_cadence_lines[2] = SMS_getVCount();
#else
        poses[0] = mof_duel_action_pose(&duel, 0u);
        poses[1] = mof_duel_action_pose(&duel, 1u);
        h_pose = poses[hayato_player];
        a_pose = poses[1u - hayato_player];
        a_x = (uint8_t)duel.fighters[1u - hayato_player].x;
        patch = patch_for(a_pose, a_x);
#if defined(MOF_DUEL_FAST_SAT)
        sat_changed = prepare_sat(hayato_meta[h_pose], alis_meta[a_pose], h_pose, a_pose,
                                  (uint8_t)duel.fighters[hayato_player].x, a_x);
        mof_cadence_lines[2] = SMS_getVCount();
#else
        SMS_initSprites();
        emit(hayato_meta[h_pose], (uint8_t)duel.fighters[hayato_player].x);
        emit(alis_meta[a_pose], a_x);
        SMS_finalizeSprites();
#endif
#endif
        prepare_hud();
#if defined(MOF_DUEL_REPERTOIRE)
        submit_deadline = 0xC4u;
#if defined(MOF_DUEL_REPERTOIRE_ASSETS)
        /* In the b11 trace the SAT-only route ended at most 23 counts
           after submission. For this route alone, 0xCD is still in the
           first monotonic VBlank segment, with room before VDP wrap. */
        if (!rep_upload_count && !rep_bg_batch && !rep_publish_bg && !hud_count[0] && !hud_count[1])
            submit_deadline = 0xCDu;
#endif
        next_epoch = wait_to_publish(submitted_epoch, submit_deadline);
        mof_vblank_start = SMS_getVCount();
        mof_missed_epochs += (uint8_t)(next_epoch - submitted_epoch) - 1u;
        submitted_epoch = next_epoch;
#elif defined(MOF_DUEL_FAST_SAT)
        submitted_epoch = wait_to_publish(submitted_epoch, 0xC4u);
#else
        SMS_waitForVBlank();
#endif
        mof_runtime_phase = 2u;
#if defined(MOF_DUEL_REPERTOIRE)
        rep_publish();
        publish_hud();
#else
        /* Overlay tiles are exclusive to the corresponding Alis pose. */
        upload_overlay(alis_meta[a_pose][1]);
        publish_patch(patch, a_x >> 3);
        last_patch = patch;
        last_patch_x = a_x >> 3;
        publish_hud();
#if defined(MOF_DUEL_FAST_SAT)
        if (sat_changed) copy_sat();
#else
        SMS_copySpritestoSAT();
#endif
#endif
        vline = SMS_getVCount();
#if defined(MOF_DUEL_FAST_SAT)
        mof_cadence_lines[3] = vline;
#endif
        if (mof_presented_frame < 3000u) {
            mof_vline = vline;
            if (vline < 0xC0u) ++mof_vblank_overrun;
            if (vline < mof_min_vline) mof_min_vline = vline;
#if defined(MOF_DUEL_REPERTOIRE)
            if (vline > mof_vblank_end_high) mof_vblank_end_high = vline;
#endif
        } else {
            mof_worst_done = 1u;
        }
        mof_runtime_phase = 3u;
        ++mof_presented_frame;
#if !defined(MOF_DUEL_REPERTOIRE)
        update_audio();
#endif
        publish_probe(poses);
#if defined(MOF_DUEL_REPERTOIRE)
        /* Commit the displayed pose and contact before decoding the PSG cue. */
        mof_duel_audio_tick(&duel, hayato_player, repertoire_normals[MOF_DUEL_ALIS]);
        mof_probe_end = SMS_getVCount();
#endif
    }
}

#endif /* MOF_DUEL_SCENE_MIRROR */
#endif /* MOF_DUEL_PILOT */
