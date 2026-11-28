/* Alis Landale's rules record for the mirror duel and the chapter.
   Boxes are half-open pixels, right-facing, relative to the ground pivot.
   The round owns poses, banks and sound effects; the rules read only
   mof_fighter_alis through the roster. */

#define ALIS_BOX(l,t,r,b) {(l)-12,t,(r)-12,b}
static const MofDuelBox alis_offense[MOF_DUEL_NORMALS_PER_FIGHTER] = {
    ALIS_BOX(9,-40,30,-25), ALIS_BOX(17,-37,55,-34),
    ALIS_BOX(11,-30,35,-16), ALIS_BOX(11,-46,39,-31),
    ALIS_BOX(9,-31,31,-18), ALIS_BOX(15,-51,41,-15),
    ALIS_BOX(11,-20,36,-5), ALIS_BOX(9,-14,40,-2),
    ALIS_BOX(22,-45,31,-31), ALIS_BOX(19,-28,31,-17),
    ALIS_BOX(20,-30,34,-22), ALIS_BOX(18,-16,31,0),
    ALIS_BOX(6,-41,35,-20), {10,-40,32,-16},
#if defined(MOF_ALIS_CHAPTER)
    {8,-35,40,-28},
#if defined(MOF_ALIS_RIPOSTE)
    {5,-36,27,-29},
#endif
#endif
};
#undef ALIS_BOX

static const uint8_t alis_ends[MOF_DUEL_NORMALS_PER_FIGHTER][5] = {
    {4,6,14}, {5,7,18}, {5,7,17}, {10,12,27},
    {4,6,14}, {7,9,22}, {4,6,15}, {8,11,25},
    {2,4,11}, {2,5,15}, {2,5,12}, {2,5,15},
    {7,9,23}, {MOF_THROW_REACH_END_TICK, MOF_THROW_BRACE_TICK, MOF_THROW_RELEASE_TICK,
               MOF_THROW_RECOVERY_TICK, MOF_THROW_END_TICK},
#if defined(MOF_ALIS_CHAPTER)
#ifdef MOF_ALIS_COMBAT
    {10,14,66},
#else
    {10,14,33},
#endif
#if defined(MOF_ALIS_RIPOSTE)
    {2,8,11,24},
#endif
#endif
};

/* Short presses are light. Holds, the special, the throw, the Super and
   the riposte are heavy. The shield and the blade sound their own hits. */
#define HEAVY MOF_MOVE_HEAVY
#define AIR MOF_MOVE_AIR_BLOCKABLE
#define SHIELD MOF_MATERIAL_SHIELD
#define BLADE MOF_MATERIAL_BLADE
#define BODY MOF_MATERIAL_BODY
#define ALIS_MOVE(id, first, length, end, damage, poses, height, down, flags, push, material) \
    {&alis_offense[id], &alis_ends[id][0], first, length, end, damage, poses, height, down, \
     flags, push, material}
static const MofDuelStandingNormal alis_moves[MOF_DUEL_NORMALS_PER_FIGHTER] = {
    ALIS_MOVE(0,4,2,14,6,3u,MOF_HEIGHT_MIDDLE,0,AIR,4,SHIELD),
    ALIS_MOVE(1,5,2,18,10,3u,MOF_HEIGHT_MIDDLE,0,HEAVY|AIR,4,BLADE),
    ALIS_MOVE(2,5,2,17,8,3u,MOF_HEIGHT_MIDDLE,0,0,4,BODY),
    ALIS_MOVE(3,10,2,27,12,3u,MOF_HEIGHT_MIDDLE,0,HEAVY,4,BODY),
    ALIS_MOVE(4,4,2,14,5,3u,MOF_HEIGHT_MIDDLE,0,0,4,SHIELD),
    ALIS_MOVE(5,7,2,22,11,3u,MOF_HEIGHT_MIDDLE,0,HEAVY|MOF_MOVE_ANTI_AIR,4,BLADE),
    ALIS_MOVE(6,4,2,15,6,3u,MOF_HEIGHT_LOW,0,0,4,BODY),
    ALIS_MOVE(7,8,3,25,10,3u,MOF_HEIGHT_LOW,1,HEAVY,4,BODY),
    ALIS_MOVE(8,2,2,11,5,3u,MOF_HEIGHT_OVERHEAD,0,AIR,4,SHIELD),
    ALIS_MOVE(9,2,3,15,11,3u,MOF_HEIGHT_OVERHEAD,0,HEAVY|AIR,4,BLADE),
    ALIS_MOVE(10,2,3,12,7,3u,MOF_HEIGHT_OVERHEAD,0,AIR,4,BODY),
    ALIS_MOVE(11,2,3,15,12,3u,MOF_HEIGHT_OVERHEAD,0,HEAVY|AIR,7,BODY),
    ALIS_MOVE(12,7,2,23,13,3u,MOF_HEIGHT_MIDDLE,0,HEAVY|AIR,
#ifdef MOF_ALIS_CHOREOGRAPHY
              10,
#else
              4,
#endif
              MOF_MATERIAL_SPECIAL),
    ALIS_MOVE(13,MOF_THROW_RELEASE_TICK,1,MOF_THROW_END_TICK,16,5u,MOF_HEIGHT_THROW,1,
              HEAVY|AIR,4,SHIELD),
#if defined(MOF_ALIS_CHAPTER)
#ifdef MOF_ALIS_COMBAT
    ALIS_MOVE(14,10,4,66,5,3u,MOF_HEIGHT_MIDDLE,0,HEAVY|AIR,4,MOF_MATERIAL_SUPER),
#elif defined(MOF_ALIS_CHOREOGRAPHY)
    ALIS_MOVE(14,10,4,33,5,3u,MOF_HEIGHT_MIDDLE,0,HEAVY|AIR,4,MOF_MATERIAL_SUPER),
#else
    ALIS_MOVE(14,10,4,33,25,3u,MOF_HEIGHT_MIDDLE,1,HEAVY|AIR,4,MOF_MATERIAL_SUPER),
#endif
#if defined(MOF_ALIS_RIPOSTE)
    ALIS_MOVE(15,8,3,24,15,4u,MOF_HEIGHT_MIDDLE,0,HEAVY|AIR|MOF_MOVE_PARRY,4,BODY),
#endif
#endif
};
#undef ALIS_MOVE
#undef HEAVY
#undef AIR
#undef SHIELD
#undef BLADE
#undef BODY

/* Command priority: Super, Shield Pull, riposte, special. */
static const MofCommand alis_commands[] = {
#if defined(MOF_ALIS_CHAPTER)
    {MOF_DUEL_SUPER, MOF_CMD_FORWARD | MOF_DUEL_ONE, MOF_CMD_GESTURE},
#endif
    {MOF_DUEL_THROW, MOF_CMD_FORWARD | MOF_DUEL_ONE | MOF_DUEL_TWO, MOF_CMD_NOW},
#if defined(MOF_ALIS_RIPOSTE)
    {MOF_DUEL_RIPOSTE, MOF_CMD_BACK | MOF_DUEL_ONE, MOF_CMD_AFTER_DOWN},
#endif
    {MOF_DUEL_SPECIAL, MOF_CMD_FORWARD | MOF_DUEL_ONE, MOF_CMD_AFTER_DOWN},
    {MOF_DUEL_NO_NORMAL, 0u, 0u}
};

#ifdef MOF_ALIS_MAGIC
#include "../inc/alis_magic.h"
/* Spell actions have their own namespace. The same motion can name a
   different action in the next fighter's record. STUN is universal. */
static const MofCommand alis_gestures[] = {
    {GUARDIANS, MOF_DUEL_TWO, G_DOUBLE_QCF},
    {SABER, MOF_DUEL_ONE, G_DP},
    {TWIN_FIRE, MOF_DUEL_ONE | MOF_DUEL_TWO, G_QCF},
    {SLASH, MOF_DUEL_ONE, G_QCF},
    {MYAU, MOF_DUEL_TWO, G_QCB},
    {MIRROR, MOF_DUEL_ONE, G_QCB},
    {FIRE_TAP, MOF_DUEL_ONE, G_DOWN_DOWN},
    {REST, MOF_DUEL_TWO, G_DOWN_DOWN},
    {CHAT, MOF_DUEL_TWO, G_BACK_BACK}
};
#endif

static const MofFighterDef mof_fighter_alis = {
    alis_moves,
    /* Jump arc only: walking still goes through the two-body solver. */
    {0u, 0u, 0u, 0u, 0u, 0u, 96u, 234u, 24u, 0u, 0u, 0u},
    /* stand, crouch, folding, air, air_braced */
    {-11,-53,13,-3}, {-11,-33,11,-2}, {-13,-40,11,-2}, {-12,-46,11,-4}, {-12,-46,11,-15},
    34u,           /* neck: head hits overlap above 34 px */
    32u,           /* throw capture reach */
    2u, 7u, 2u,    /* special advances 2 px per tick on ticks 2 to 6 */
    MOF_MOVES_ALL, MOF_DUEL_UP | MOF_DUEL_DOWN,
    2u, 8u,        /* the riposte catches a middle hit on ticks 2 to 7 */
    alis_commands,
#if defined(MOF_ALIS_MAGIC)
    alis_gestures, sizeof(alis_gestures)/sizeof(alis_gestures[0])
#elif defined(MOF_DUEL_SCENE_EFFECTS)
    0, 0
#endif
};
