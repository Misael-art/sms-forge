/* Settled ground state of the arena duel. Transitions, crossings, normals
   and stale collision geometry fall through to the complete rules step. */
#include "../inc/duel_combat.h"

static inline uint8_t ground_settled(uint8_t p, uint8_t keys)
{
    const MofDuelBody *b=&duel.body[p];
    return !b->jump_buffer && !b->jump_pending && b->transition!=1u &&
        !(keys&MOF_DUEL_UP) && !b->y_offset &&
        b->motion.mode!=MOF_MOTION_AIR &&
        (duel.fighters[p].state!=MOF_DUEL_READY ||
         ((keys&MOF_DUEL_DOWN) ? b->motion.mode==MOF_MOTION_CROUCH : b->motion.mode==MOF_MOTION_IDLE)) &&
        duel.tested_hurt_x[p]!=INT16_MIN && duel.tested_hurt_facing[p]==duel.fighters[p].face_right;
}

/* Return FF when a contact or state transition needs the complete solver.
   Otherwise return the exact animation phase of the next tick. */
static uint8_t ground_phase(const MofDuelFighter *f)
{
    uint16_t elapsed;
    const MofDuelStandingNormal *move;
    uint8_t phase=0;
    if (f->state==MOF_DUEL_READY) return 0;
    elapsed=duel.tick+1u-f->state_since;
    if (f->state==MOF_DUEL_HIT && !f->thrown && elapsed<f->hit_duration) return 0;
    if (f->state==MOF_DUEL_BLOCK && elapsed<
#ifdef MOF_ALIS_COMBAT
        f->hit_duration
#else
        MOF_DUEL_BLOCK_TICKS
#endif
       ) return 0;
    if (f->state!=MOF_DUEL_ATTACK || f->standing_normal>=MOF_DUEL_AIR_NORMALS) return 255;
    move=&f->def->moves[f->standing_normal];
    if (elapsed>=move->duration || (!f->spent &&
        (uint8_t)((uint8_t)elapsed-move->first_active)<move->active_ticks)) return 255;
    while (phase+1u<move->pose_count && elapsed>=move->pose_ends[phase]) ++phase;
    return phase+1u;
}

static inline int16_t ground_player(uint8_t p, uint8_t keys,uint8_t phase)
{
    MofDuelFighter *f=&duel.fighters[p];
    uint8_t dir=keys&(MOF_DUEL_LEFT|MOF_DUEL_RIGHT);
    uint8_t back=f->face_right ? MOF_DUEL_LEFT : MOF_DUEL_RIGHT;
    int16_t x=f->x,delta=x-duel.tested_hurt_x[p];
    duel.body[p].air_step=0;
    if (duel.body[p].transition) --duel.body[p].transition;
    f->keys=keys;
    f->contact=MOF_DUEL_NO_CONTACT;
    if (!(keys&MOF_DUEL_ONE)) f->latched=f->held=0;
    if (f->state!=MOF_DUEL_READY) f->held=0;
    f->guarding=f->state==MOF_DUEL_READY && dir==back ? ((keys&MOF_DUEL_DOWN) ? MOF_GUARD_CROUCHING : MOF_GUARD_STANDING) : MOF_GUARD_OPEN;
    duel.tested_active[p]=0;duel.tested_pose[p]=phase;
    if (delta) {
        duel.tested_hurt[p].left+=delta;
        duel.tested_hurt[p].right+=delta;
        duel.tested_hurt_x[p]=x;
    }
    if (f->state==MOF_DUEL_READY && !(keys&(MOF_DUEL_DOWN|MOF_DUEL_ONE))) {
        if (dir==MOF_DUEL_LEFT && x>duel.left_wall) --x;
        if (dir==MOF_DUEL_RIGHT && x<duel.right_wall) ++x;
    }
    return x;
}

static uint8_t ground_step(uint8_t a,uint8_t b)
{
    int16_t x,y,gap;
    uint8_t phase_a,phase_b;
    uint8_t right=duel.fighters[0].face_right;
#ifdef MOF_ALIS_COMBAT
    if (mof_combat.slide[0] || mof_combat.slide[1] ||
        mof_combat.command_age[0] || mof_combat.command_age[1] ||
        mof_combat.guard_window[0] || mof_combat.guard_window[1] ||
        ((a^duel.fighters[0].keys)&(MOF_DUEL_LEFT|MOF_DUEL_RIGHT)) ||
        ((b^duel.fighters[1].keys)&(MOF_DUEL_LEFT|MOF_DUEL_RIGHT))) return 0;
#endif
    a &= duel.fighters[0].def->vertical | (uint8_t)~(MOF_DUEL_UP|MOF_DUEL_DOWN);
    b &= duel.fighters[1].def->vertical | (uint8_t)~(MOF_DUEL_UP|MOF_DUEL_DOWN);
    if (duel.hitstop || !ground_settled(0,a) || !ground_settled(1,b) ||
        duel.fighters[0].x==duel.fighters[1].x ||
        right!=(duel.fighters[0].x<duel.fighters[1].x) || right==duel.fighters[1].face_right)
        return 0;
    phase_a=ground_phase(&duel.fighters[0]);phase_b=ground_phase(&duel.fighters[1]);
    if (phase_a==255 || phase_b==255) return 0;
    ++duel.tick;
#ifdef MOF_ALIS_COMBAT
    mof_combat.spark[0]=mof_combat.spark[1]=0;
#endif
    x=ground_player(0,a,phase_a);
    y=ground_player(1,b,phase_b);
    gap=right ? y-x : x-y;
    if (gap>=duel.minimum_gap) {
        duel.fighters[0].x=x;
        duel.fighters[1].x=y;
    }
    return 1;
}
