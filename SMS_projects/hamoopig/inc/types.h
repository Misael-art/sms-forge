#ifndef HAMOOPIG_TYPES_H
#define HAMOOPIG_TYPES_H

/* IDs de cena preservam os valores da origem (sonda / telemetria). */
#define SCENE_OPENING       0u
#define SCENE_TITLE         1u
#define SCENE_SELECT        2u
#define SCENE_FIGHT        10u
#define SCENE_AFTER_MATCH  11u
#define SCENE_NONE        255u

/* FSM numerica herdada do subset HAMOOPIG. */
#define ST_IDLE     100u
#define ST_PUNCH    101u
#define ST_KICK     104u
#define ST_GUARD    107u
#define ST_CROUCH   200u
#define ST_JUMP     300u
#define ST_WALK_B   410u
#define ST_WALK_F   420u
#define ST_HIT      501u
#define ST_KO       570u
#define ST_WIN      611u
#define ST_THROW    113u
#define ST_SPECIAL  700u

#define KEY_FREE     0u
#define KEY_PRESSED  1u
#define KEY_HOLD     2u
#define KEY_RELEASED 3u

#define CONTROL_HUMAN  0u
#define CONTROL_CPU    1u
#define CONTROL_DUMMY  2u
#define CONTROL_REPLAY 3
#define CONTROL_BLOCK  4u

#define FID_RYO    1u
#define FID_KEN    2u
#define FID_MUSGO  3u

#define HP_MAX          64u
#define SP_MAX          32u
#define SP_COST         32u
#define GROUND_Y        112
#define FIGHTER_W       32
#define FIGHTER_H       64
#define STAGE_X_MIN     8
#define STAGE_X_MAX     216
#define PUSH_W          20
#define ROUNDS_TO_WIN   2u
#define CLOCK_START     99u
#define HITSTOP_FRAMES  6u

#define INP_UP     0u
#define INP_DOWN   1u
#define INP_LEFT   2u
#define INP_RIGHT  3u
#define INP_B1     4u
#define INP_B2     5u
#define INP_COUNT  6u

#define CE_HIT    0u
#define CE_GUARD  1u
#define CE_THROW  2u
#define CE_CAP    4u

#define POSE_IDLE    0u
#define POSE_WALK    1u
#define POSE_PUNCH   2u
#define POSE_SPECIAL 3u
#define POSE_HIT     4u
#define POSE_KO      5u
#define POSE_CROUCH  6u
#define POSE_JUMP    7u
#define ANIM_FR_MAX  6u

typedef struct {
    unsigned char n;
    unsigned char loop;
    unsigned char dur[6];
} AnimDef;

#define TILE_FONT       1u
#define TILE_FLOOR      48u
#define TILE_BAR_HP     49u
#define TILE_BAR_SP     50u
#define TILE_BAR_EMPTY  51u
#define TILE_P1A        96u
#define TILE_P1B        128u
#define TILE_P2A        160u
#define TILE_P2B        192u
#define TILE_FB         224u
#define TILE_FB_L       228u
#define TILE_STAGE      256u

#define MF_LOW   0x01u
#define MF_AIR   0x02u
#define MF_PROJ  0x04u
#define MF_THROW 0x08u

typedef struct {
    signed char x, y, w, h;
} Box;

typedef struct {
    unsigned char startup, active, recovery;
    unsigned char damage;
    unsigned char hitstun, blockstun;
    signed char knockback;
    unsigned char flags;
    Box hit;
} MoveDef;

typedef struct {
    unsigned char id;
    unsigned char walk_spd;
    unsigned char jump_imp;
    unsigned char grav;
    const MoveDef *punch;
    const MoveDef *kick;
    const MoveDef *special;
} FighterDef;

typedef struct {
    signed int x, y;
    signed char vy;
    unsigned char facing;
    unsigned char hp, sp;
    unsigned int state;
    unsigned char timer;
    unsigned char pose;
    unsigned char anim_i;
    unsigned char anim_t;
    unsigned char hit_used;
    unsigned char guard;
    unsigned char rounds;
    unsigned char id;
    unsigned char control;
    unsigned char attack_inst;
    unsigned char stun;
    unsigned char keys[INP_COUNT];
    unsigned char hist[8];
    unsigned char hist_i;
    unsigned char fire_on;
    signed int fx, fy;
    signed char fvx;
} Fighter;

typedef struct {
    unsigned char attacker;
    unsigned char defender;
    unsigned char kind;
    unsigned char inst;
    unsigned char damage;
    unsigned int state;
} Contact;

#endif
