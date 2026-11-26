#include "../inc/duel_rules.h"

#if defined(MOF_DUEL_PILOT) || defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)

#define DUEL_VITALITY 100u
#define DUEL_BLOCK_TICKS 3u
#define DUEL_HIT_TICKS 8u
#define DUEL_GROUND_Y 144

/* Mirror fighters read moves from their own record; earlier scenes share
   one table indexed by fighter id. */
#if defined(MOF_DUEL_SCENE_MIRROR)
#define HAS_MOVES(d, f) ((void)(d), (f)->def != 0)
#define MOVE(d, f, id) (&(f)->def->moves[id])
#elif defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
#define HAS_MOVES(d, f) ((d)->standing_normals != 0)
#define MOVE(d, f, id) (&(d)->standing_normals[(f)->fighter][id])
#endif

#if defined(MOF_DUEL_SCENE_POSTURES)
#include "../inc/duel_commands.h"

#define ALIS_JUMP_RELEASE_GRACE 4u

#if defined(MOF_DUEL_SCENE_CROSSOVER)
#define ALIS_JUMP_VELOCITY 234u
#define ALIS_JUMP_GRAVITY 24
#endif

/* The fixed-point arc and diagonal momentum use the shared motion module.
   Mirror fighters carry their own profile in their roster record. */
#if defined(MOF_DUEL_SCENE_MIRROR)
#define MOTION_PROFILE(fighter) (&(fighter)->def->motion)
#else
static const MofDuelMotionProfile alis_profile = {
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    0u, 0u, 0u, 0u, 0u, 0u, 96u, ALIS_JUMP_VELOCITY, ALIS_JUMP_GRAVITY, 0u, 0u, 0u
#else
    0u, 0u, 0u, 0u, 0u, 0u, 32u, 56u, 4u, 0u, 0u, 0u
#endif
};
#define MOTION_PROFILE(fighter) (&alis_profile)
#endif

#if !defined(MOF_DUEL_SCENE_MIRROR)
static uint8_t alis_player(const MofDuel *duel)
{
    return duel->fighters[0].fighter ^ MOF_DUEL_ALIS;
}
#endif

#if !defined(MOF_DUEL_SCENE_MIRROR) || defined(MOF_DUEL_HOST_TEST)
uint8_t mof_duel_alis_standing_input(const MofDuel *duel, uint8_t player, uint8_t keys)
{
    const MofDuelBody *state = &duel->body[player];
    return !(keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)) && !state->jump_pending &&
           state->motion.mode != MOF_MOTION_AIR;
}

uint8_t mof_duel_alis_air_guard(const MofDuel *duel, uint8_t player)
{
    const MofDuelFighter *alis = &duel->fighters[player];
    return alis->state == MOF_DUEL_BLOCK || alis->guarding == MOF_GUARD_AIRBORNE;
}
#endif

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

static void body_step(MofDuel *duel, uint8_t player, uint8_t keys)
{
    const MofDuelFighter *alis = &duel->fighters[player];
    MofDuelBody *state = &duel->body[player];
    MofDuelMotion *motion = &state->motion;
    uint8_t prior = motion->mode, event, launch = 0u;
    int8_t prior_offset = state->y_offset;
    state->air_step = 0;
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (alis->state >= MOF_DUEL_DOWNED ||
        (prior == MOF_MOTION_IDLE && !(keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)) &&
         !state->jump_pending && !state->jump_buffer && !state->transition)) return;
#endif
    uint8_t up = (keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)) == MOF_DUEL_UP;
    uint8_t round_over = alis->state == MOF_DUEL_KO ||
        duel->fighters[1u - player].state == MOF_DUEL_KO;
    uint8_t free = alis->state == MOF_DUEL_READY && !round_over;
    /* Fighter keys still hold the previous physical reading here. The
       shared motion module receives only a committed launch edge. */
    if (round_over || (keys & MOF_DUEL_DOWN)) {
        state->jump_buffer = 0u;
    } else if (up && !(alis->keys & MOF_DUEL_UP)) {
        state->jump_buffer = keys & (MOF_DUEL_UP | MOF_DUEL_LEFT | MOF_DUEL_RIGHT);
        state->jump_grace = ALIS_JUMP_RELEASE_GRACE;
    } else if (!up && state->jump_buffer && !--state->jump_grace) {
        state->jump_buffer = 0u;
    }
    if (state->transition && !--state->transition)
        duel->tested_hurt_x[player] = INT16_MIN;
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (!free && prior != MOF_MOTION_AIR && !state->jump_pending) return;
    if (prior == MOF_MOTION_CROUCH && (keys & MOF_DUEL_DOWN) && !state->jump_pending)
        return;
#endif
    if (state->jump_pending) {
        if (free && state->transition) return;
        if (free) launch = state->jump_pending;
        state->jump_pending = 0u;
    } else if (free && prior != MOF_MOTION_AIR && state->jump_buffer) {
        /* Compress on the floor before committing the latched launch vector. */
        state->jump_pending = state->jump_buffer;
        state->jump_buffer = 0u;
        state->transition = 2u;
        duel->tested_hurt_x[player] = INT16_MIN;
        return;
    }
    if (prior == MOF_MOTION_IDLE && !launch && !(keys & MOF_DUEL_DOWN)) return;
    if (prior != MOF_MOTION_AIR && alis->state == MOF_DUEL_BLOCK) return;
    keys = launch ? launch : keys & (uint8_t)~MOF_DUEL_UP;
    motion->previous_up = 0u;
    motion->x = alis->x * MOF_MOTION_UNIT;
    /* Ground walking still goes through the existing two-body solver. */
    if (prior != MOF_MOTION_AIR && !(keys & (MOF_DUEL_UP | MOF_DUEL_DOWN)))
        keys &= (uint8_t)~(MOF_DUEL_LEFT | MOF_DUEL_RIGHT);
    event = mof_duel_motion_read(motion, MOTION_PROFILE(alis), keys, alis->face_right, free,
                                 duel->left_wall * MOF_MOTION_UNIT, duel->right_wall * MOF_MOTION_UNIT);
    if (motion->mode == MOF_MOTION_AIR || (event & MOF_MOTION_LANDED))
        state->air_step = (int8_t)((motion->x >> 4) - alis->x);
    if (event & MOF_MOTION_LAUNCHED) {
        state->transition = 0;
        state->air_age = 0;
    }
    if (motion->mode == MOF_MOTION_AIR) ++state->air_age;
    if ((event & MOF_MOTION_LANDED) ||
        ((prior == MOF_MOTION_CROUCH) != (motion->mode == MOF_MOTION_CROUCH)))
        state->transition = 3u;
    state->y_offset = (int8_t)-(int16_t)((-motion->y) >> 4);
    if (prior_offset != state->y_offset || prior != motion->mode)
        duel->tested_hurt_x[player] = INT16_MIN;
}
#endif

static const uint8_t first_active[2] = {9u, 5u};
static const uint8_t attack_length[2] = {25u, 18u};
static const uint8_t damage[2] = {12u, 10u};
static const uint8_t hayato_pose_end[6] = {8u,9u,11u,18u,20u,25u};
static const uint8_t alis_pose_end[3] = {5u,7u,18u};

static uint8_t box_valid(const MofDuelBox *box)
{
    return box->left >= -256 && box->right <= 256 &&
        box->top >= -192 && box->bottom <= 192 &&
        box->left < box->right && box->top < box->bottom;
}

static void world_box(const MofDuelFighter *fighter, const MofDuelBox *local,
                      MofDuelBox *world)
{
    world->left = fighter->x + (fighter->face_right ? local->left : -local->right);
    world->right = fighter->x + (fighter->face_right ? local->right : -local->left);
    world->top = DUEL_GROUND_Y + local->top;
    world->bottom = DUEL_GROUND_Y + local->bottom;
}

uint16_t mof_duel_age(const MofDuel *duel, const MofDuelFighter *fighter)
{
    return (uint16_t)(duel->tick - fighter->state_since);
}

static void face_opponent(MofDuel *duel)
{
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    if (duel->fighters[0].x == duel->fighters[1].x) return;
#endif
    uint8_t p1_right = duel->fighters[0].x < duel->fighters[1].x;
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    if (duel->fighters[0].state != MOF_DUEL_ATTACK
#if defined(MOF_DUEL_SCENE_MIRROR)
        && duel->fighters[0].state != MOF_DUEL_CAUGHT
#endif
    )
        duel->fighters[0].face_right = p1_right;
    if (duel->fighters[1].state != MOF_DUEL_ATTACK
#if defined(MOF_DUEL_SCENE_MIRROR)
        && duel->fighters[1].state != MOF_DUEL_CAUGHT
#endif
    )
        duel->fighters[1].face_right = !p1_right;
#else
    duel->fighters[0].face_right = p1_right;
    duel->fighters[1].face_right = !p1_right;
#endif
}

uint8_t mof_duel_init_pair(MofDuel *duel, const MofDuelGeometry geometry[2],
                           uint8_t hold_ticks, uint8_t p1_fighter, uint8_t p2_fighter,
                      int16_t p1_x, int16_t p2_x,
                      int16_t left_wall, int16_t right_wall, int16_t minimum_gap)
{
    uint8_t player;
    int16_t gap;
    if (!geometry || (hold_ticks != 6u && hold_ticks != 8u) || p1_fighter > MOF_DUEL_ALIS ||
        p2_fighter > MOF_DUEL_ALIS ||
        left_wall < 0 || right_wall > 255 || left_wall >= right_wall ||
        p1_x < left_wall || p1_x > right_wall || p2_x < left_wall || p2_x > right_wall ||
        minimum_gap <= 0) {
        return 0u;
    }
    gap = p1_x < p2_x ? p2_x - p1_x : p1_x - p2_x;
    if (gap < minimum_gap) return 0u;
    for (player = 0u; player < 2u; ++player) {
        if (!box_valid(&geometry[player].hurt) || !box_valid(&geometry[player].active[0]) ||
            !box_valid(&geometry[player].active[1])) {
            return 0u;
        }
    }
    duel->tick = UINT16_MAX;
    duel->left_wall = left_wall;
    duel->right_wall = right_wall;
    duel->minimum_gap = minimum_gap;
    duel->hold_ticks = hold_ticks;
    duel->geometry = geometry;
#if (defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)) && !defined(MOF_DUEL_SCENE_MIRROR)
    duel->standing_normals = 0;
#endif
    for (player = 0u; player < 2u; ++player) {
        MofDuelFighter *fighter = &duel->fighters[player];
        fighter->x = player ? p2_x : p1_x;
        fighter->fighter = player ? p2_fighter : p1_fighter;
        fighter->life = DUEL_VITALITY;
        fighter->state = MOF_DUEL_READY;
        fighter->face_right = 0u;
        fighter->state_since = fighter->free_since = 0u;
        fighter->keys = fighter->held = fighter->latched = 0u;
        fighter->spent = fighter->contact = fighter->guarding = 0u;
#if defined(MOF_DUEL_SCENE_MIRROR)
        fighter->def = 0;
        fighter->reaction = MOF_REACT_BODY;
        fighter->thrown = 0u;
        fighter->hit_duration = DUEL_HIT_TICKS;
#endif
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
        fighter->standing_normal = MOF_DUEL_NO_NORMAL;
#endif
        duel->tested_active[player] = duel->tested_pose[player] = 0u;
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
        duel->tested_hurt_x[player] = INT16_MIN;
#endif
    }
#if defined(MOF_DUEL_SCENE_MIRROR)
    duel->hitstop = duel->hitstop_target = 0u;
#endif
    face_opponent(duel);
#if defined(MOF_DUEL_SCENE_POSTURES)
    for (player = 0u; player < 2u; ++player) {
        MofDuelBody *state = &duel->body[player];
        mof_duel_motion_reset(&state->motion, duel->fighters[player].x * MOF_MOTION_UNIT,
                              duel->fighters[player].face_right);
        state->y_offset = state->air_step = 0;
        state->transition = state->air_age = 0u;
        state->jump_pending = state->jump_buffer = state->jump_grace = 0u;
    }
#endif
    return 1u;
}

#if !defined(MOF_DUEL_SCENE_MIRROR) || defined(MOF_DUEL_HOST_TEST)
uint8_t mof_duel_init(MofDuel *duel, const MofDuelGeometry geometry[2],
                      uint8_t hold_ticks, uint8_t p1_fighter,
                      int16_t p1_x, int16_t p2_x,
                      int16_t left_wall, int16_t right_wall, int16_t minimum_gap)
{
    return mof_duel_init_pair(duel, geometry, hold_ticks, p1_fighter, p1_fighter ^ 1u,
                              p1_x, p2_x, left_wall, right_wall, minimum_gap);
}
#endif

static void enter(MofDuel *duel, MofDuelFighter *fighter, uint8_t state)
{
    fighter->state = state;
    fighter->state_since = duel->tick;
    if (state == MOF_DUEL_READY) {
        fighter->free_since = duel->tick;
    }
}

static int16_t clamp_x(const MofDuel *duel, int16_t x)
{
    if (x < duel->left_wall) return duel->left_wall;
    if (x > duel->right_wall) return duel->right_wall;
    return x;
}

static uint8_t expired(const MofDuel *duel, const MofDuelFighter *fighter, uint16_t age)
{
    uint8_t duration = attack_length[fighter->fighter];
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
    if (HAS_MOVES(duel, fighter) && fighter->standing_normal < MOF_DUEL_NORMALS_PER_FIGHTER)
        duration = MOVE(duel, fighter, fighter->standing_normal)->duration;
#else
    (void)duel;
#endif
    return (fighter->state == MOF_DUEL_ATTACK && age >= duration) ||
        (fighter->state == MOF_DUEL_BLOCK && age >= DUEL_BLOCK_TICKS) ||
        (fighter->state == MOF_DUEL_HIT && age >=
#if defined(MOF_DUEL_SCENE_MIRROR)
         fighter->hit_duration
#else
         DUEL_HIT_TICKS
#endif
        );
}

#if defined(MOF_DUEL_SCENE_MIRROR)
static uint8_t aerial_attack_lands(const MofDuel *duel, uint8_t player)
{
    const MofDuelFighter *fighter = &duel->fighters[player];
    const MofDuelMotion *motion = &duel->body[player].motion;
    return fighter->state == MOF_DUEL_ATTACK &&
        fighter->standing_normal >= MOF_DUEL_AIR_NORMALS &&
        fighter->standing_normal < MOF_DUEL_SPECIAL &&
        motion->mode == MOF_MOTION_AIR && motion->y + motion->vy >= 0;
}
#endif

static void expire_state(MofDuel *duel, uint8_t player)
{
    MofDuelFighter *fighter = &duel->fighters[player];
#if defined(MOF_DUEL_SCENE_MIRROR)
    uint16_t age = mof_duel_age(duel, fighter);
    if (aerial_attack_lands(duel, player)) {
        /* Unlock before motion reads the grounded posture and new command. */
        enter(duel, fighter, MOF_DUEL_READY);
    } else if (fighter->state == MOF_DUEL_HIT && fighter->thrown) {
        if (age >= MOF_THROW_STAGGER_TICKS) {
            enter(duel, fighter, MOF_DUEL_FALL);
        } else {
            /* Two grounded recovery steps. A wall can absorb the displacement. */
            int16_t step = age < 6u ? 2 : 1;
            fighter->x = clamp_x(duel, fighter->x + (fighter->face_right ? -step : step));
        }
    } else if (fighter->state == MOF_DUEL_FALL && !duel->body[player].y_offset &&
               (!fighter->thrown || age >= 5u)) {
        enter(duel, fighter, MOF_DUEL_DOWNED);
    } else if (fighter->state == MOF_DUEL_DOWNED && age >= 18u) {
        enter(duel, fighter, fighter->life ? MOF_DUEL_GETUP : MOF_DUEL_KO);
    } else if (fighter->state == MOF_DUEL_GETUP && age >= 7u) {
        fighter->thrown = 0u;
        enter(duel, fighter, MOF_DUEL_READY);
    } else
#endif
    if (expired(duel, fighter, mof_duel_age(duel, fighter))) {
        enter(duel, fighter, MOF_DUEL_READY);
    }
}

static void consume_input(MofDuel *duel, uint8_t player, uint8_t keys, uint8_t normal)
{
    MofDuelFighter *fighter = &duel->fighters[player];
    uint8_t direction = keys & (MOF_DUEL_LEFT | MOF_DUEL_RIGHT);
    uint8_t back = fighter->face_right ? MOF_DUEL_LEFT : MOF_DUEL_RIGHT;
    fighter->keys = keys & 0x3Fu;
    fighter->contact = MOF_DUEL_NO_CONTACT;
    fighter->guarding = 0u;
    if (!(keys & MOF_DUEL_ONE)) {
        fighter->held = fighter->latched = 0u;
    }
    if (fighter->state != MOF_DUEL_READY) {
        fighter->held = 0u;
        return;
    }
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
    if (HAS_MOVES(duel, fighter)) {
#if defined(MOF_DUEL_SCENE_POSTURES)
#if defined(MOF_DUEL_SCENE_MIRROR)
        if (duel->fighters[1u - player].state == MOF_DUEL_KO) return;
        if (normal == MOF_DUEL_NO_NORMAL && direction != back) return;
#endif
        if (fighter->fighter == MOF_DUEL_ALIS) {
#if defined(MOF_DUEL_SCENE_MIRROR)
            uint8_t posture = mof_duel_motion_posture(&duel->body[player].motion);
            if (duel->body[player].jump_pending ||
                (normal < MOF_DUEL_SPECIAL && normal >> 2 != posture) ||
                (normal >= MOF_DUEL_SPECIAL && posture != MOF_INPUT_STANDING) ||
                !duel->fighters[1u - player].life)
                normal = MOF_DUEL_NO_NORMAL;
            if (direction == back)
                fighter->guarding = posture + 1u;
#else
            if (normal < MOF_DUEL_NORMALS_PER_FIGHTER && !mof_duel_alis_standing_input(duel, player, keys))
                normal = MOF_DUEL_NO_NORMAL;
            if (direction == back)
                fighter->guarding = mof_duel_guard(keys, fighter->face_right,
                                                  mof_duel_motion_posture(&duel->body[player].motion), 1u);
#endif
        } else
#endif
        {
            fighter->guarding = direction == back;
        }
        if (normal < MOF_DUEL_NORMALS_PER_FIGHTER) {
            fighter->guarding = 0u;
            fighter->standing_normal = normal;
            fighter->spent = 0u;
            enter(duel, fighter, MOF_DUEL_ATTACK);
        }
        return;
    }
#else
    (void)normal;
#endif
    if ((keys & MOF_DUEL_ONE) && !fighter->latched) {
        ++fighter->held;
        if (fighter->held == duel->hold_ticks) {
            fighter->latched = 1u;
            fighter->spent = 0u;
            enter(duel, fighter, MOF_DUEL_ATTACK);
            return;
        }
    }
    fighter->guarding = (direction == back);
}

static uint8_t active_bounds(const MofDuel *duel, const MofDuelFighter *fighter,
                             const MofDuelBox **boxes, uint8_t *first)
{
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
    if (HAS_MOVES(duel, fighter) && fighter->standing_normal < MOF_DUEL_NORMALS_PER_FIGHTER) {
        const MofDuelStandingNormal *normal = MOVE(duel, fighter, fighter->standing_normal);
        *boxes = normal->active_boxes;
        *first = normal->first_active;
        return normal->active_ticks;
    }
#endif
    *boxes = duel->geometry[fighter->fighter].active;
    *first = first_active[fighter->fighter];
    return 2u;
}

#if !defined(MOF_DUEL_SCENE_MIRROR) || defined(MOF_DUEL_HOST_TEST)
uint8_t mof_duel_attack_box(const MofDuel *duel, uint8_t player, MofDuelBox *box)
{
    const MofDuelFighter *fighter = &duel->fighters[player];
    uint16_t age;
    const MofDuelBox *boxes;
    uint8_t first, count;
    if (fighter->state != MOF_DUEL_ATTACK || fighter->spent) return 0u;
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (fighter->standing_normal == MOF_DUEL_THROW) return 0u;
#endif
    age = mof_duel_age(duel, fighter);
    count = active_bounds(duel, fighter, &boxes, &first);
    if (age < first || age >= (uint16_t)first + count) return 0u;
#if defined(MOF_DUEL_SCENE_MIRROR)
    /* Each compact mirror normal shares its declared box over its active hold. */
    world_box(fighter, boxes, box);
    box->top += duel->body[player].y_offset;
    box->bottom += duel->body[player].y_offset;
#else
    world_box(fighter, &boxes[age-first], box);
#endif
    return 1u;
}
#endif

void mof_duel_hurt_box(const MofDuel *duel, uint8_t player, MofDuelBox *box)
{
    const MofDuelFighter *fighter = &duel->fighters[player];
#if defined(MOF_DUEL_SCENE_MIRROR)
    const MofFighterDef *def = fighter->def;
    const MofDuelBody *body = &duel->body[player];
    if (body->motion.mode == MOF_MOTION_AIR) {
        world_box(fighter, fighter->guarding == MOF_GUARD_AIRBORNE ||
                  fighter->state == MOF_DUEL_BLOCK ? &def->air_braced : &def->air, box);
        box->top += body->y_offset;
        box->bottom += body->y_offset;
    } else if (body->motion.mode == MOF_MOTION_CROUCH || body->transition) {
        world_box(fighter, body->transition ? &def->folding : &def->crouch, box);
    } else {
        world_box(fighter, &def->stand, box);
    }
#else
#if defined(MOF_DUEL_SCENE_POSTURES)
    if (fighter->fighter == MOF_DUEL_ALIS) {
        static const MofDuelBox crouch = {1,-33,23,-2};
        static const MofDuelBox folding = {-3,-40,23,-2};
        static const MofDuelBox air = {0,-46,23,-4};
        static const MofDuelBox air_braced = {0,-46,23,-15};
        if (duel->body[player].motion.mode == MOF_MOTION_AIR) {
            world_box(fighter, fighter->guarding == MOF_GUARD_AIRBORNE ||
                      fighter->state == MOF_DUEL_BLOCK ? &air_braced : &air, box);
            box->top += duel->body[player].y_offset;
            box->bottom += duel->body[player].y_offset;
            return;
        }
        if (duel->body[player].motion.mode == MOF_MOTION_CROUCH || duel->body[player].transition) {
            world_box(fighter, duel->body[player].transition ? &folding : &crouch, box);
            return;
        }
    }
#endif
    world_box(fighter, &duel->geometry[fighter->fighter].hurt, box);
#endif
}

static uint8_t contact(const MofDuel *duel, uint8_t attacker)
{
    const MofDuelFighter *source = &duel->fighters[attacker];
    const MofDuelFighter *target = &duel->fighters[1u-attacker];
    const MofDuelBox *active = &duel->tested_attack[attacker];
    const MofDuelBox *hurt = &duel->tested_hurt[1u-attacker];
    if (target->state == MOF_DUEL_KO || !duel->tested_active[attacker]) {
        return MOF_DUEL_NO_CONTACT;
    }
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (target->state >= MOF_DUEL_FALL || !target->life) return MOF_DUEL_NO_CONTACT;
#endif
    if (active->left < hurt->right && active->right > hurt->left &&
        active->top < hurt->bottom && active->bottom > hurt->top) {
#if defined(MOF_DUEL_SCENE_POSTURES)
        if (target->fighter == MOF_DUEL_ALIS)
#if defined(MOF_DUEL_SCENE_MIRROR)
            return mof_duel_guard_blocks(target->guarding,
                       MOVE(duel, source, source->standing_normal)->height,
                       (MOVE(duel, source, source->standing_normal)->flags &
                        MOF_MOVE_AIR_BLOCKABLE) != 0u,
                       (MOVE(duel, source, source->standing_normal)->flags &
                        MOF_MOVE_ANTI_AIR) != 0u)
#else
            return mof_duel_guard_blocks(target->guarding, MOF_HEIGHT_MIDDLE,
                        source->standing_normal <= MOF_INPUT_LONG_ONE, 0u)
#endif
                ? MOF_DUEL_GUARDED : MOF_DUEL_LANDED;
#endif
        return target->guarding ? MOF_DUEL_GUARDED : MOF_DUEL_LANDED;
    }
    {
        const MofDuelBox *boxes;
        uint8_t first;
        uint8_t count = active_bounds(duel, source, &boxes, &first);
        return (mof_duel_age(duel, source) == (uint16_t)first + count - 1u)
        ? MOF_DUEL_MISSED : MOF_DUEL_NO_CONTACT;
    }
}

#if defined(MOF_DUEL_SCENE_CROSSOVER)
/* The sole clears Hayato's standing head before horizontal overlap.
   From the edge, advancing 6 px per tick needs at most eight further
   ticks to clear the 48 px corridor. Check those ticks before entry. */
#define ALIS_CROSS_HEIGHT (65 * MOF_MOTION_UNIT)
#define ALIS_CROSS_TICKS 8

static void move_alis_across(MofDuel *duel, uint8_t player)
{
    MofDuelFighter *alis = &duel->fighters[player];
    const MofDuelFighter *rival = &duel->fighters[1u - player];
    const MofDuelMotion *motion = &duel->body[player].motion;
    int16_t left = rival->x - duel->minimum_gap, right = rival->x + duel->minimum_gap;
    int16_t next = clamp_x(duel, alis->x + duel->body[player].air_step);
    uint8_t on_left;
#if defined(MOF_DUEL_SCENE_MIRROR)
    const MofDuelMotion *other = &duel->body[1u - player].motion;
    int16_t height_delta = motion->y - other->y;
    int16_t speed_delta = motion->vy - other->vy;
    int16_t projected_gravity = other->mode == MOF_MOTION_AIR ? 0 :
        (int16_t)alis->def->motion.gravity * (ALIS_CROSS_TICKS * (ALIS_CROSS_TICKS - 1) / 2);
#else
    int16_t height_delta = motion->y, speed_delta = motion->vy;
    const int16_t projected_gravity = ALIS_JUMP_GRAVITY * (ALIS_CROSS_TICKS * (ALIS_CROSS_TICKS - 1) / 2);
#endif
    if (next <= left || next >= right || alis->x == next) {
        alis->x = next;
        return;
    }
    on_left = alis->x < rival->x || (alis->x == rival->x && alis->face_right);
    if (alis->x > left && alis->x < right) {
        if (height_delta <= -ALIS_CROSS_HEIGHT || height_delta >= ALIS_CROSS_HEIGHT) {
            alis->x = next;
            return;
        }
        /* Resolve overlap on descent, including an interrupted crossing. */
    } else if (height_delta <= -ALIS_CROSS_HEIGHT &&
               (on_left ? right <= duel->right_wall : left >= duel->left_wall) &&
               height_delta + speed_delta * ALIS_CROSS_TICKS + projected_gravity <= -ALIS_CROSS_HEIGHT) {
        alis->x = next;
        return;
    }
    if (left < duel->left_wall) on_left = 0u;
    if (right > duel->right_wall) on_left = 1u;
    alis->x = on_left ? left : right;
}
#endif

#if defined(MOF_DUEL_SCENE_MIRROR)
/* The attacker's move record says whether a contact is heavy. The
   strongest contact of a step owns the freeze. */
static uint8_t heavy_impact(const MofDuelFighter *source)
{
    return (source->def->moves[source->standing_normal].flags & MOF_MOVE_HEAVY) != 0u;
}

static void freeze_impact(MofDuel *duel, uint8_t victim, uint8_t heavy, uint8_t shake)
{
    uint8_t stop = heavy ? MOF_DUEL_HEAVY_HITSTOP : MOF_DUEL_LIGHT_HITSTOP;
    if (stop < duel->hitstop) return;
    duel->hitstop = stop;
    duel->hitstop_target = victim | (heavy && shake ? MOF_DUEL_HITSTOP_SHAKE : 0u);
}

static void begin_fall(MofDuel *duel, uint8_t player)
{
    MofDuelBody *state = &duel->body[player];
    if (!state->y_offset) {
        state->motion.y = -4 * MOF_MOTION_UNIT;
        state->y_offset = -4;
    }
    state->motion.vy = -32;
    state->motion.vx = 0;
    state->motion.mode = MOF_MOTION_AIR;
    state->transition = state->jump_buffer = state->jump_pending = 0u;
    enter(duel, &duel->fighters[player], MOF_DUEL_FALL);
}

/* Pull the grounded rival into shield range. Release into stagger before
   loss of footing, with one impact even when the rival touches a wall. */
static void advance_throw(MofDuel *duel, uint8_t owner)
{
    uint8_t other = 1u - owner;
    MofDuelFighter *source = &duel->fighters[owner];
    MofDuelFighter *target = &duel->fighters[other];
    MofDuelBody *motion = &duel->body[other];
    uint8_t age, amount;
    int16_t reach, direction;
    if (source->state != MOF_DUEL_ATTACK || source->standing_normal != MOF_DUEL_THROW) {
        if (target->state == MOF_DUEL_CAUGHT) enter(duel, target, MOF_DUEL_READY);
        return;
    }
    age = (uint8_t)mof_duel_age(duel, source);
    direction = source->face_right ? 1 : -1;
    reach = (target->x - source->x) * direction;
    if (age == MOF_THROW_CAPTURE_TICK) {
        if (reach < duel->minimum_gap || reach > source->def->throw_reach ||
            (target->state != MOF_DUEL_READY && target->state != MOF_DUEL_BLOCK) ||
            motion->motion.mode == MOF_MOTION_AIR || motion->jump_pending) {
            source->contact = MOF_DUEL_MISSED;
            return;
        }
        target->face_right = !source->face_right;
        target->guarding = target->held = 0u;
        enter(duel, target, MOF_DUEL_CAUGHT);
        motion->transition = motion->jump_buffer = motion->jump_pending = 0u;
        motion->motion.mode = MOF_MOTION_IDLE;
        return;
    }
    if (target->state != MOF_DUEL_CAUGHT) return;
    if (age < MOF_THROW_RELEASE_TICK) {
        if (age >= MOF_THROW_REACH_END_TICK && reach > duel->minimum_gap)
            target->x -= direction * (reach - duel->minimum_gap >= 2 ? 2 : 1);
        return;
    }
    amount = source->def->moves[MOF_DUEL_THROW].damage;
    target->life = target->life > amount ? (uint8_t)(target->life - amount) : 0u;
    source->contact = MOF_DUEL_LANDED;
    target->thrown = 1u;
    enter(duel, target, MOF_DUEL_HIT);
    freeze_impact(duel, other, 1u, 1u);
}
#endif

static void apply_contact(MofDuel *duel, uint8_t attacker, uint8_t result)
{
    MofDuelFighter *source = &duel->fighters[attacker];
    MofDuelFighter *target = &duel->fighters[1u-attacker];
    int16_t push;
    if (result == MOF_DUEL_NO_CONTACT) return;
    source->contact = result;
    source->spent = 1u;
    if (result == MOF_DUEL_MISSED) return;
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (result == MOF_DUEL_GUARDED) {
        target->reaction = MOF_REACT_GUARD_STAND + target->guarding - 1u;
    } else if (duel->body[1u - attacker].motion.mode == MOF_MOTION_CROUCH) {
        target->reaction = MOF_REACT_LOW;
    } else {
        /* A contact spanning both regions is a head hit if its overlap
           reaches above the neck line of the current vertical pivot. */
        target->reaction = duel->tested_attack[attacker].top <
            DUEL_GROUND_Y + duel->body[1u - attacker].y_offset - target->def->neck
            ? MOF_REACT_HEAD : MOF_REACT_BODY;
    }
    target->thrown = 0u;
    {
        uint8_t heavy = heavy_impact(source);
        target->hit_duration = heavy ? MOF_DUEL_HEAVY_HITSTUN : MOF_DUEL_LIGHT_HITSTUN;
        freeze_impact(duel, 1u - attacker, heavy, result == MOF_DUEL_LANDED);
    }
#endif
    target->held = target->guarding = 0u;
    if (result == MOF_DUEL_LANDED) {
        uint8_t amount = damage[source->fighter];
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
        if (HAS_MOVES(duel, source) && source->standing_normal < MOF_DUEL_NORMALS_PER_FIGHTER)
            amount = MOVE(duel, source, source->standing_normal)->damage;
#endif
        target->life = target->life > amount ? (uint8_t)(target->life - amount) : 0u;
#if defined(MOF_DUEL_SCENE_MIRROR)
        if (!target->life || (HAS_MOVES(duel, source) &&
            source->standing_normal < MOF_DUEL_NORMALS_PER_FIGHTER &&
            MOVE(duel, source, source->standing_normal)->knockdown))
            begin_fall(duel, 1u - attacker);
        else
#endif
        enter(duel, target, target->life ? MOF_DUEL_HIT : MOF_DUEL_KO);
#if defined(MOF_DUEL_SCENE_MIRROR)
        push = MOVE(duel, source, source->standing_normal)->push;
#else
        push = 4;
#endif
    } else {
        enter(duel, target, MOF_DUEL_BLOCK);
        push = 3;
    }
    target->x = clamp_x(duel, target->x + (source->face_right ? push : -push));
}

static int16_t movement(const MofDuel *duel, uint8_t player)
{
    const MofDuelFighter *fighter = &duel->fighters[player];
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (!(fighter->keys & (MOF_DUEL_LEFT | MOF_DUEL_RIGHT)) || fighter->state != MOF_DUEL_READY ||
        duel->fighters[1u - player].state == MOF_DUEL_KO)
        return 0;
#endif
#if defined(MOF_DUEL_SCENE_POSTURES)
    if (fighter->fighter == MOF_DUEL_ALIS) {
#if defined(MOF_DUEL_SCENE_CROSSOVER)
        if (duel->body[player].motion.mode == MOF_MOTION_AIR || duel->body[player].air_step) return 0;
#else
        if (duel->body[player].motion.mode == MOF_MOTION_AIR || duel->body[player].air_step)
            return duel->body[player].air_step;
#endif
        if (duel->body[player].motion.mode == MOF_MOTION_CROUCH || duel->body[player].jump_pending ||
            (fighter->keys & MOF_DUEL_DOWN)) return 0;
    }
#else
    (void)duel;
#endif
    if (fighter->state != MOF_DUEL_READY || (fighter->keys & MOF_DUEL_ONE)) return 0;
    switch (fighter->keys & (MOF_DUEL_LEFT | MOF_DUEL_RIGHT)) {
        case MOF_DUEL_LEFT: return -1;
        case MOF_DUEL_RIGHT: return 1;
        default: return 0;
    }
}

#if defined(MOF_DUEL_SCENE_SPECIALS)
static uint8_t special_advance(const MofDuel *duel, const MofDuelFighter *fighter)
{
    uint16_t age;
    if (fighter->state != MOF_DUEL_ATTACK || fighter->standing_normal != MOF_DUEL_SPECIAL)
        return 0u;
    age = mof_duel_age(duel, fighter);
#if defined(MOF_DUEL_SCENE_MIRROR)
    return age >= fighter->def->special_from && age < fighter->def->special_until
        ? fighter->def->special_step : 0u;
#else
    if (fighter->fighter == MOF_DUEL_HAYATO) return age >= 3u && age < 9u ? 2u : 0u;
    return age >= 2u && age < 7u ? 2u : 0u;
#endif
}

static void advance_specials(MofDuel *duel)
{
    MofDuelFighter *a = &duel->fighters[0], *b = &duel->fighters[1];
    uint8_t p1 = special_advance(duel, a), p2 = special_advance(duel, b);
    int16_t clear;
    if (!(p1 | p2)) return;
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    {
        uint8_t p1_left = a->x < b->x;
        if (a->face_right != p1_left) p1 = 0u;
        if (b->face_right == p1_left) p2 = 0u;
        clear = (p1_left ? b->x - a->x : a->x - b->x) - duel->minimum_gap;
    }
#else
    clear = (a->face_right ? b->x - a->x : a->x - b->x) - duel->minimum_gap;
#endif
    if (clear <= 0) return;
    if (p1 + p2 > clear) {
        if (p1 && p2) p1 = p2 = (uint8_t)clear >> 1;
        else if (p1) p1 = (uint8_t)clear;
        else p2 = (uint8_t)clear;
    }
    a->x += a->face_right ? (int16_t)p1 : -(int16_t)p1;
    b->x += b->face_right ? (int16_t)p2 : -(int16_t)p2;
}
#endif

static void step_duel(MofDuel *duel, uint8_t p1_keys, uint8_t p2_keys,
                       uint8_t p1_normal, uint8_t p2_normal)
{
    uint8_t player, p1_contact, p2_contact;
    int16_t p1_x, p2_x, gap;
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (duel->hitstop) {
        /* Hold the clock, poses, positions and buffered keys. A contact
           result belongs to its own step and cannot repeat its events. */
        --duel->hitstop;
        duel->fighters[0].contact = duel->fighters[1].contact = MOF_DUEL_NO_CONTACT;
        return;
    }
#endif
    ++duel->tick;
    face_opponent(duel);
    if (duel->fighters[0].state != MOF_DUEL_READY) expire_state(duel, 0u);
    if (duel->fighters[1].state != MOF_DUEL_READY) expire_state(duel, 1u);
#if defined(MOF_DUEL_SCENE_POSTURES)
#if defined(MOF_DUEL_SCENE_MIRROR)
    body_step(duel, 0u, p1_keys);
    body_step(duel, 1u, p2_keys);
    if (duel->body[0].air_step || duel->body[1].air_step) {
        if (duel->body[0].air_step) move_alis_across(duel, 0u);
        if (duel->body[1].air_step) move_alis_across(duel, 1u);
        face_opponent(duel);
    }
#else
    player = alis_player(duel);
    body_step(duel, player, player ? p2_keys : p1_keys);
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    if (duel->body[player].air_step) {
        move_alis_across(duel, player);
        face_opponent(duel);
    }
#endif
#endif
#endif
    consume_input(duel, 0u, p1_keys, p1_normal);
    consume_input(duel, 1u, p2_keys, p2_normal);
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (duel->fighters[0].state == MOF_DUEL_CAUGHT || duel->fighters[1].standing_normal == MOF_DUEL_THROW)
        advance_throw(duel, 1u);
    if (duel->fighters[1].state == MOF_DUEL_CAUGHT || duel->fighters[0].standing_normal == MOF_DUEL_THROW)
        advance_throw(duel, 0u);
#endif
#if defined(MOF_DUEL_SCENE_SPECIALS)
#if defined(MOF_DUEL_SCENE_MIRROR)
    if ((duel->fighters[0].state == MOF_DUEL_ATTACK && duel->fighters[0].standing_normal == MOF_DUEL_SPECIAL) ||
        (duel->fighters[1].state == MOF_DUEL_ATTACK && duel->fighters[1].standing_normal == MOF_DUEL_SPECIAL))
#else
    if (duel->fighters[0].state == MOF_DUEL_ATTACK || duel->fighters[1].state == MOF_DUEL_ATTACK)
#endif
        advance_specials(duel);
#endif
    /* Resolve the two results from the same pre-reaction positions and poses. */
    for (player = 0u; player < 2u; ++player) {
        const MofDuelFighter *fighter = &duel->fighters[player];
        duel->tested_pose[player] = duel->tested_active[player] = 0u;
        if (fighter->state == MOF_DUEL_ATTACK) {
#if defined(MOF_DUEL_SCENE_MIRROR)
#if defined(MOF_DUEL_HOST_TEST)
            if (!HAS_MOVES(duel, fighter) || fighter->standing_normal >= MOF_DUEL_NORMALS_PER_FIGHTER) {
                duel->tested_pose[player] = mof_duel_action_pose(duel, player);
                duel->tested_active[player] = mof_duel_attack_box(duel, player,
                                                                 &duel->tested_attack[player]);
            } else
#endif
            {
            const MofDuelStandingNormal *normal = MOVE(duel, fighter, fighter->standing_normal);
            uint8_t age = (uint8_t)(duel->tick - fighter->state_since);
            uint8_t phase = 0u;
            while (age >= normal->pose_ends[phase]) ++phase;
            duel->tested_pose[player] = phase + 1u;
            if (fighter->standing_normal != MOF_DUEL_THROW && !fighter->spent &&
                (fighter->standing_normal < MOF_DUEL_AIR_NORMALS ||
                 fighter->standing_normal >= MOF_DUEL_SPECIAL ||
                 duel->body[player].motion.mode == MOF_MOTION_AIR) &&
                (uint8_t)(age - normal->first_active) < normal->active_ticks) {
                MofDuelBox *box = &duel->tested_attack[player];
                int8_t offset = duel->body[player].y_offset;
                world_box(fighter, normal->active_boxes, box);
                box->top += offset;
                box->bottom += offset;
                duel->tested_active[player] = 1u;
            }
            }
#else
            duel->tested_pose[player] = mof_duel_action_pose(duel, player);
            duel->tested_active[player] = mof_duel_attack_box(duel, player,
                                                             &duel->tested_attack[player]);
#endif
        }
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
        if (duel->tested_hurt_x[player] != fighter->x ||
            duel->tested_hurt_facing[player] != fighter->face_right
#if defined(MOF_DUEL_SCENE_POSTURES)
            || (fighter->fighter == MOF_DUEL_ALIS && duel->body[player].motion.mode == MOF_MOTION_AIR)
#endif
        ) {
#if defined(MOF_DUEL_SCENE_MIRROR)
            if (duel->tested_hurt_x[player] != INT16_MIN &&
                duel->tested_hurt_facing[player] == fighter->face_right &&
                duel->body[player].motion.mode != MOF_MOTION_AIR) {
                int16_t delta = fighter->x - duel->tested_hurt_x[player];
                duel->tested_hurt[player].left += delta;
                duel->tested_hurt[player].right += delta;
            } else
#endif
            mof_duel_hurt_box(duel, player, &duel->tested_hurt[player]);
            duel->tested_hurt_x[player] = fighter->x;
            duel->tested_hurt_facing[player] = fighter->face_right;
        }
#else
        mof_duel_hurt_box(duel, player, &duel->tested_hurt[player]);
#endif
    }
    p1_contact = duel->tested_active[0] ? contact(duel, 0u) : MOF_DUEL_NO_CONTACT;
    p2_contact = duel->tested_active[1] ? contact(duel, 1u) : MOF_DUEL_NO_CONTACT;
    if (p1_contact) apply_contact(duel, 0u, p1_contact);
    if (p2_contact) apply_contact(duel, 1u, p2_contact);
    if (!((p1_keys | p2_keys) & (MOF_DUEL_LEFT | MOF_DUEL_RIGHT))
#if defined(MOF_DUEL_SCENE_POSTURES) && !defined(MOF_DUEL_SCENE_CROSSOVER)
        && !duel->body[alis_player(duel)].air_step
#endif
    ) return;
#if defined(MOF_DUEL_SCENE_CROSSOVER) && !defined(MOF_DUEL_SCENE_MIRROR)
    player = alis_player(duel);
    /* The air solver already moved Alis. The ground solver only has a job
       here if Hayato actually pressed a horizontal direction. */
    if ((duel->body[player].motion.mode == MOF_MOTION_AIR || duel->body[player].air_step) &&
        !((duel->fighters[0].fighter == MOF_DUEL_ALIS ? p2_keys : p1_keys) &
          (MOF_DUEL_LEFT | MOF_DUEL_RIGHT))) return;
#endif
    p1_x = clamp_x(duel, duel->fighters[0].x + movement(duel, 0u));
    p2_x = clamp_x(duel, duel->fighters[1].x + movement(duel, 1u));
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    gap = duel->fighters[0].x <= duel->fighters[1].x ? p2_x-p1_x : p1_x-p2_x;
#else
    gap = duel->fighters[0].face_right ? p2_x-p1_x : p1_x-p2_x;
#endif
    if (gap >= duel->minimum_gap) {
        duel->fighters[0].x = p1_x;
        duel->fighters[1].x = p2_x;
    }
}

#if !defined(MOF_DUEL_SCENE_MIRROR) || defined(MOF_DUEL_HOST_TEST)
void mof_duel_step(MofDuel *duel, uint8_t p1_keys, uint8_t p2_keys)
{
    step_duel(duel, p1_keys, p2_keys, UINT8_MAX, UINT8_MAX);
}

uint8_t mof_duel_action_pose(const MofDuel *duel, uint8_t player)
{
    const MofDuelFighter *fighter = &duel->fighters[player];
    uint16_t age = mof_duel_age(duel, fighter);
    uint8_t count, pose;
    const uint8_t *ends;
    if (fighter->state != MOF_DUEL_ATTACK) return 0u;
    ends = fighter->fighter == MOF_DUEL_HAYATO ? hayato_pose_end : alis_pose_end;
    count = fighter->fighter == MOF_DUEL_HAYATO ? 6u : 3u;
#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
    if (HAS_MOVES(duel, fighter) && fighter->standing_normal < MOF_DUEL_NORMALS_PER_FIGHTER) {
        const MofDuelStandingNormal *normal = MOVE(duel, fighter, fighter->standing_normal);
        ends = normal->pose_ends;
        count = normal->pose_count;
    }
#endif
    for (pose = 0u; pose < count; ++pose) {
        if (age < ends[pose]) return pose+1u;
    }
    return 0u;
}
#endif

#if defined(MOF_DUEL_REPERTOIRE) || defined(MOF_DUEL_HOST_TEST)
static uint8_t moves_valid(const MofDuelStandingNormal *moves)
{
    uint8_t id, frame;
    for (id = 0u; id < MOF_DUEL_NORMALS_PER_FIGHTER; ++id) {
        const MofDuelStandingNormal *normal = &moves[id];
        if (!normal->pose_ends || !normal->pose_count || !normal->active_boxes ||
            !normal->active_ticks || !normal->damage ||
            (uint16_t)normal->first_active + normal->active_ticks > normal->duration ||
            normal->pose_ends[normal->pose_count - 1u] != normal->duration) {
            return 0u;
        }
#if defined(MOF_DUEL_SCENE_MIRROR)
        if (!box_valid(normal->active_boxes) || !normal->push) return 0u;
#else
        for (frame = 0u; frame < normal->active_ticks; ++frame) {
            if (!box_valid(&normal->active_boxes[frame])) return 0u;
        }
#endif
        if (!normal->pose_ends[0]) return 0u;
        for (frame = 1u; frame < normal->pose_count; ++frame) {
            if (normal->pose_ends[frame] <= normal->pose_ends[frame - 1u]) return 0u;
        }
    }
    return 1u;
}

#if defined(MOF_DUEL_SCENE_MIRROR)
uint8_t mof_duel_set_roster(MofDuel *duel,
    const MofFighterDef *const roster[MOF_DUEL_FIGHTER_IDS])
{
    uint8_t player;
    if (!roster || duel->fighters[0].def || duel->tick != UINT16_MAX) return 0u;
    for (player = 0u; player < 2u; ++player) {
        const MofFighterDef *def = roster[duel->fighters[player].fighter];
        if (!def || !def->moves || !moves_valid(def->moves) ||
            !box_valid(&def->stand) || !box_valid(&def->crouch) ||
            !box_valid(&def->folding) || !box_valid(&def->air) ||
            !box_valid(&def->air_braced) || !def->motion.gravity ||
            def->special_from >= def->special_until) {
            return 0u;
        }
    }
    for (player = 0u; player < 2u; ++player)
        duel->fighters[player].def = roster[duel->fighters[player].fighter];
    return 1u;
}
#else
uint8_t mof_duel_set_standing_normals(MofDuel *duel,
    const MofDuelStandingNormal normals[2][MOF_DUEL_NORMALS_PER_FIGHTER])
{
    uint8_t fighter;
    if (!normals || duel->standing_normals || duel->tick != UINT16_MAX) return 0u;
    for (fighter = 0u; fighter < 2u; ++fighter) {
        if (!moves_valid(normals[fighter])) return 0u;
    }
    duel->standing_normals = normals;
    return 1u;
}
#endif

uint8_t mof_duel_next_tick_free(const MofDuel *duel, uint8_t player)
{
    const MofDuelFighter *fighter = &duel->fighters[player];
    return fighter->state == MOF_DUEL_READY ||
#if defined(MOF_DUEL_SCENE_MIRROR)
        aerial_attack_lands(duel, player) ||
#endif
        expired(duel, fighter, (uint16_t)(duel->tick + 1u - fighter->state_since));
}

void mof_duel_step_normal(MofDuel *duel, uint8_t p1_keys, uint8_t p2_keys,
                          uint8_t p1_normal, uint8_t p2_normal)
{
    step_duel(duel, p1_keys, p2_keys, p1_normal, p2_normal);
}
#endif

#endif
