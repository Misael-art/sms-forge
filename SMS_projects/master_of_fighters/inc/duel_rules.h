#ifndef MOF_DUEL_RULES_H
#define MOF_DUEL_RULES_H

#include <stdint.h>
#if defined(MOF_DUEL_SCENE_POSTURES)
#include "duel_motion.h"
#endif

#define MOF_DUEL_UP    0x01u
#define MOF_DUEL_DOWN  0x02u
#define MOF_DUEL_LEFT  0x04u
#define MOF_DUEL_RIGHT 0x08u
#define MOF_DUEL_ONE   0x10u
#define MOF_DUEL_TWO   0x20u

#define MOF_DUEL_HAYATO 0u
#define MOF_DUEL_ALIS   1u
#define MOF_DUEL_FIGHTER_IDS 2u

#define MOF_DUEL_READY  0u
#define MOF_DUEL_ATTACK 1u
#define MOF_DUEL_BLOCK  2u
#define MOF_DUEL_HIT    3u
#define MOF_DUEL_KO     4u
#if defined(MOF_DUEL_SCENE_MIRROR)
#define MOF_DUEL_FALL   5u
#define MOF_DUEL_DOWNED 6u
#define MOF_DUEL_GETUP  7u
#define MOF_DUEL_CAUGHT 8u
#endif

#define MOF_DUEL_NO_CONTACT 0u
#define MOF_DUEL_LANDED     1u
#define MOF_DUEL_GUARDED    2u
#define MOF_DUEL_MISSED     3u

#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
#define MOF_DUEL_NO_NORMAL UINT8_MAX
#if defined(MOF_DUEL_SCENE_MIRROR)
#define MOF_DUEL_LOW_NORMALS 4u
#define MOF_DUEL_AIR_NORMALS 8u
#define MOF_DUEL_SPECIAL 12u
#define MOF_DUEL_THROW 13u
#define MOF_DUEL_NORMALS_PER_FIGHTER 14u
#define MOF_THROW_CAPTURE_TICK 8u
#define MOF_THROW_REACH_END_TICK 10u
#define MOF_THROW_BRACE_TICK 17u
#define MOF_THROW_RELEASE_TICK 22u
#define MOF_THROW_RECOVERY_TICK 28u
#define MOF_THROW_END_TICK 42u
#define MOF_THROW_STAGGER_TICKS 10u
#elif defined(MOF_DUEL_SCENE_SPECIALS)
#define MOF_DUEL_SPECIAL 4u
#define MOF_DUEL_NORMALS_PER_FIGHTER 5u
#else
#define MOF_DUEL_NORMALS_PER_FIGHTER 4u
#endif
#endif

/* Half-open boxes in pixels, right-facing, relative to the ground pivot. */
typedef struct {
    int16_t left, top, right, bottom;
} MofDuelBox;

typedef struct {
    MofDuelBox hurt;
    MofDuelBox active[2];  /* One authored box for each active tick. */
} MofDuelGeometry;

#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
typedef struct {
    const MofDuelBox *active_boxes;
    const uint8_t *pose_ends;
    uint8_t first_active, active_ticks, duration, damage, pose_count;
#if defined(MOF_DUEL_SCENE_MIRROR)
    uint8_t height, knockdown;
    /* Read by the rules instead of inferring them from the move id. */
    uint8_t flags, push, material;
#endif
} MofDuelStandingNormal;
#endif

#if defined(MOF_DUEL_SCENE_MIRROR)
#define MOF_MOVE_HEAVY         0x01u  /* long freeze and hitstun; a landed hit shakes */
#define MOF_MOVE_AIR_BLOCKABLE 0x02u  /* an airborne guard stops it */
#define MOF_MOVE_ANTI_AIR      0x04u  /* from the ground it beats an airborne guard */
/* Sound material. Shield and blade equal the button-one command ids. */
#define MOF_MATERIAL_SHIELD 0u
#define MOF_MATERIAL_BLADE  1u
#define MOF_MATERIAL_BODY   2u

/* One fighter's rules record. The rules read only this record, so a new
   fighter adds a record instead of new branches on its id. */
typedef struct {
    const MofDuelStandingNormal *moves;  /* MOF_DUEL_NORMALS_PER_FIGHTER entries */
    MofDuelMotionProfile motion;
    /* Hurt boxes by posture. Folding covers crouch and landing transitions. */
    MofDuelBox stand, crouch, folding, air, air_braced;
    uint8_t neck;         /* px above the pivot where head hits begin */
    uint8_t throw_reach;  /* farthest throw capture, px between pivots */
    uint8_t special_from, special_until, special_step;  /* ticks, px per tick */
} MofFighterDef;
#endif

typedef struct {
    uint16_t state_since, free_since;
    int16_t x;
    uint8_t fighter, face_right, state, life;
    uint8_t keys, held, latched, spent, contact, guarding;
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
    uint8_t standing_normal;
#endif
#if defined(MOF_DUEL_SCENE_MIRROR)
    const MofFighterDef *def;
    uint8_t reaction, thrown, hit_duration;
#endif
} MofDuelFighter;

#if defined(MOF_DUEL_SCENE_POSTURES)
#define MOF_ALIS_RISE_TICKS 4u
#if defined(MOF_DUEL_SCENE_CROSSOVER)
#define MOF_ALIS_GUARD_UNFOLD_SPEED 96
#else
#define MOF_ALIS_GUARD_UNFOLD_SPEED 16
#endif

enum MofAlisPose {
    MOF_ALIS_NO_POSTURE, MOF_ALIS_CROUCH_TRANSITION, MOF_ALIS_CROUCH,
    MOF_ALIS_CROUCH_GUARD, MOF_ALIS_STAND_GUARD, MOF_ALIS_JUMP_RISE,
    MOF_ALIS_JUMP_APEX, MOF_ALIS_JUMP_FALL, MOF_ALIS_JUMP_DIAGONAL,
    MOF_ALIS_JUMP_GUARD
};

typedef struct {
    MofDuelMotion motion;
    int8_t y_offset, air_step;
    uint8_t air_age, transition, jump_pending, jump_buffer, jump_grace;
} MofDuelBody;
#endif

#if defined(MOF_DUEL_SCENE_MIRROR)
enum MofDuelReaction {
    MOF_REACT_HEAD, MOF_REACT_BODY, MOF_REACT_LOW,
    MOF_REACT_GUARD_STAND, MOF_REACT_GUARD_LOW, MOF_REACT_GUARD_AIR
};
#endif

typedef struct {
    uint16_t tick;
    int16_t left_wall, right_wall, minimum_gap;
    uint8_t hold_ticks;
    const MofDuelGeometry *geometry;
    MofDuelFighter fighters[2];
    MofDuelBox tested_attack[2], tested_hurt[2];
    uint8_t tested_active[2], tested_pose[2];
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
#if !defined(MOF_DUEL_SCENE_MIRROR)
    const MofDuelStandingNormal (*standing_normals)[MOF_DUEL_NORMALS_PER_FIGHTER];
#endif
    int16_t tested_hurt_x[2];
    uint8_t tested_hurt_facing[2];
#endif
#if defined(MOF_DUEL_SCENE_POSTURES)
    MofDuelBody body[2];
#endif
#if defined(MOF_DUEL_SCENE_MIRROR)
    /* Impact freeze: steps left with both fighters held, and the defender
       of the strongest contact (bit 7 marks a heavy contact that shakes). */
    uint8_t hitstop, hitstop_target;
#endif
} MofDuel;

#if defined(MOF_DUEL_SCENE_MIRROR)
#define MOF_DUEL_LIGHT_HITSTOP 4u
#define MOF_DUEL_LIGHT_HITSTUN 10u
#define MOF_DUEL_HEAVY_HITSTOP 11u
#define MOF_DUEL_HEAVY_HITSTUN 20u
#define MOF_DUEL_HITSTOP_SHAKE 0x80u
#endif

uint8_t mof_duel_init_pair(MofDuel *duel, const MofDuelGeometry geometry[2],
                           uint8_t hold_ticks, uint8_t p1_fighter, uint8_t p2_fighter,
                           int16_t p1_x, int16_t p2_x,
                           int16_t left_wall, int16_t right_wall, int16_t minimum_gap);
#if !defined(MOF_DUEL_SCENE_MIRROR) || defined(MOF_DUEL_HOST_TEST)
uint8_t mof_duel_init(MofDuel *duel, const MofDuelGeometry geometry[2],
                      uint8_t hold_ticks, uint8_t p1_fighter,
                      int16_t p1_x, int16_t p2_x,
                      int16_t left_wall, int16_t right_wall, int16_t minimum_gap);
void mof_duel_step(MofDuel *duel, uint8_t p1_keys, uint8_t p2_keys);
uint8_t mof_duel_attack_box(const MofDuel *duel, uint8_t player, MofDuelBox *box);
uint8_t mof_duel_action_pose(const MofDuel *duel, uint8_t player);
#if defined(MOF_DUEL_SCENE_POSTURES)
uint8_t mof_duel_alis_air_guard(const MofDuel *duel, uint8_t player);
uint8_t mof_duel_alis_standing_input(const MofDuel *duel, uint8_t player, uint8_t keys);
#endif
#endif
uint16_t mof_duel_age(const MofDuel *duel, const MofDuelFighter *fighter);
void mof_duel_hurt_box(const MofDuel *duel, uint8_t player, MofDuelBox *box);
#if defined(MOF_DUEL_SCENE_POSTURES)
uint8_t mof_duel_posture_pose(const MofDuel *duel, uint8_t player);
#endif

#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
#if defined(MOF_DUEL_SCENE_MIRROR)
/* Give each player the record of its fighter id. Call once after init. */
uint8_t mof_duel_set_roster(MofDuel *duel,
    const MofFighterDef *const roster[MOF_DUEL_FIGHTER_IDS]);
#else
uint8_t mof_duel_set_standing_normals(MofDuel *duel,
    const MofDuelStandingNormal normals[2][MOF_DUEL_NORMALS_PER_FIGHTER]);
#endif
uint8_t mof_duel_next_tick_free(const MofDuel *duel, uint8_t player);
void mof_duel_step_normal(MofDuel *duel, uint8_t p1_keys, uint8_t p2_keys,
                          uint8_t p1_normal, uint8_t p2_normal);
#endif

#endif
