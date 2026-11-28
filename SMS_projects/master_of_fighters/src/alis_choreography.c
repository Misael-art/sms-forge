#ifdef MOF_ALIS_CHOREOGRAPHY
#pragma codeseg SMSBANK_CAMERA
#pragma constseg SMSBANK_CAMERA
#include "../inc/alis_magic.h"
#include "../inc/duel_combat.h"
#include "magic_poses.h"

static const uint8_t rise_height[]={0,2,5,9,14,18,23,27,30,31,30,28,24,19,13,6,0};

static void rising_arc(MofDuel *d,uint8_t p,uint8_t age,uint8_t high) {
    MofDuelFighter *f=&d->fighters[p];
    MofDuelBody *body=&d->body[p];
    int16_t gap=d->fighters[1-p].x-f->x;
    uint8_t height=age<sizeof(rise_height) ? rise_height[age] : 0;
    if (high) height += height>>2;
    if (height && gap>d->minimum_gap+1) f->x+=2;
    else if (height && gap<-(int16_t)(d->minimum_gap+1)) f->x-=2;
    body->y_offset=-(int8_t)height;
    body->motion.y=-(int16_t)height*MOF_MOTION_UNIT;
    body->motion.vx=body->motion.vy=0;
    body->motion.mode=height ? MOF_MOTION_AIR : MOF_MOTION_IDLE;
}

static void arc_hit(MofDuel *d,uint8_t p,uint8_t damage,uint8_t flags,uint8_t reach) {
    int16_t gap=d->fighters[1-p].x-d->fighters[p].x;
    int16_t height=d->body[1-p].y_offset-d->body[p].y_offset;
    if (gap>=-(int16_t)reach && gap<=reach && height>=-42 && height<=42) {
        mof_magic.impact_move[p]=SABER;
        mof_magic.impact_flags[p]=flags;
        mof_magic.impact_damage[p]=damage;
    }
}

#ifdef MOF_ALIS_COMBAT
static void palma_height(MofDuelBody *body,uint8_t height)
{
    body->y_offset=-(int8_t)height;
    body->motion.y=-(int16_t)height*MOF_MOTION_UNIT;
    body->motion.vx=body->motion.vy=0;
    body->motion.mode=height ? MOF_MOTION_AIR : MOF_MOTION_IDLE;
}

static void continue_palma(MofDuel *d,uint8_t p)
{
    uint8_t v=1u-p,age=mof_magic.palma[p];
    MofDuelFighter *f=&d->fighters[p],*target=&d->fighters[v];
    MofCaster *c=&mof_magic.caster[p];
    MofDuelBody *body=&d->body[p],*victim=&d->body[v];
    int16_t direction=f->face_right ? 1 : -1;
    uint8_t height,arc_age;
    if (!age) return;
    if (age==255) {
        if (f->contact==MOF_DUEL_LANDED) {
            mof_combat.palma_hits[p]=mof_magic.hits[p];
            mof_magic.palma[p]=1;
        } else if (f->state!=MOF_DUEL_ATTACK || f->contact>=MOF_DUEL_GUARDED)
            mof_magic.palma[p]=0;
        return;
    }
    if (f->state!=MOF_DUEL_ATTACK || age>=MOF_PALMA_END ||
        (age==MOF_PALMA_CHOP+1u && mof_magic.hits[p]==mof_combat.palma_hits[p])) {
        if (f->state==MOF_DUEL_ATTACK && body->motion.mode==MOF_MOTION_AIR)
            palma_height(body,0);
        c->pose=mof_magic.palma[p]=0;
        return;
    }
    ++mof_magic.palma[p];
    if (age<MOF_PALMA_RISE) {
        c->pose=age<=2 ? MOF_MIRROR_PALMA_2 :
            age>=MOF_PALMA_CHOP-5u && age<MOF_PALMA_CHOP ? MOF_MIRROR_CHOP_READY :
            age>=MOF_PALMA_CHOP && age<=MOF_PALMA_CHOP+3u ? MOF_MIRROR_CHOP_DOWN :
            MOF_MIRROR_BREATHE_1;
        if (age==MOF_PALMA_CHOP) {
            arc_hit(d,p,7,MOF_MOVE_HEAVY|MOF_EFFECT_CHIP,46);
            mof_combat.palma_hits[p]=mof_magic.hits[p];
        }
        return;
    }
    arc_age=age-MOF_PALMA_RISE;
    height=arc_age<sizeof(rise_height) ? rise_height[arc_age] : 0;
    c->pose=arc_age<2 ? MOF_MIRROR_AIR_1_1 :
            arc_age<12 ? MOF_MIRROR_AIR_1_2 : MOF_MIRROR_AIR_1_3;
    if (age<=MOF_PALMA_RELEASE && (target->x-f->x)*direction>d->minimum_gap+2)
        f->x+=3*direction;
    if (age>MOF_PALMA_RELEASE && f->x-2*direction>=d->left_wall &&
        f->x-2*direction<=d->right_wall) f->x-=2*direction;
    palma_height(body,height);
    if (age==MOF_PALMA_GOLD_HIT) {
        mof_combat.palma_hits[p]=mof_magic.hits[p];
        arc_hit(d,p,15,MOF_MOVE_HEAVY|MOF_EFFECT_CHIP,43);
    } else if (age>MOF_PALMA_GOLD_HIT && age<=MOF_PALMA_RELEASE &&
               mof_magic.hits[p]!=mof_combat.palma_hits[p] && target->state==MOF_DUEL_HIT) {
        /* The hit owns the lift until release. A missed/guarded hit never moves the rival. */
        mof_combat.slide[v]=0;
        palma_height(victim,height+4u);
        if (age==MOF_PALMA_RELEASE) {
            target->state=MOF_DUEL_FALL;
            target->state_since=d->tick;
            victim->motion.vy=20;
            victim->motion.vx=direction*40;
            mof_combat.fall[v]=MOF_COMBAT_HARD;
        }
    }
}

static void laconian_cut(MofDuel *d,uint8_t p)
{
    MofCaster *c=&mof_magic.caster[p];
    uint8_t v=1u-p,age=c->age;
    const MofDuelBox *hurt=&d->tested_hurt[v];
    int16_t gap=d->fighters[v].x-d->fighters[p].x;
    if (!c->face) gap=-gap;
    if (c->strain || age<8u || age>12u || gap<0 || gap>48) return;
    if (hurt->bottom<70 || hurt->top>138 ||
        (hurt->bottom<93 && gap>32)) return;
    c->strain=1;
    mof_magic.impact_move[p]=SLASH;
    mof_magic.impact_damage[p]=17;
    mof_magic.impact_flags[p]=MOF_MOVE_HEAVY|MOF_MOVE_ANTI_AIR|MOF_EFFECT_FALL|MOF_EFFECT_CHIP;
}
#else
static void continue_palma(MofDuel *d,uint8_t p) {
    MofDuelFighter *f=&d->fighters[p];
    MofCaster *c=&mof_magic.caster[p];
    uint8_t age=mof_magic.palma[p];
    if (age==255) {
        if (f->contact==MOF_DUEL_LANDED) mof_magic.palma[p]=1;
        else if (f->state!=MOF_DUEL_ATTACK || f->contact==MOF_DUEL_GUARDED) mof_magic.palma[p]=0;
        return;
    }
    if (!age) return;
    if (f->state!=MOF_DUEL_ATTACK || age>=23) {
        if (f->state<MOF_DUEL_FALL) rising_arc(d,p,0,0);
        c->pose=mof_magic.palma[p]=0;
        return;
    }
    c->pose=age<5 ? MOF_MIRROR_AIR_1_1 : age<19 ? MOF_MIRROR_AIR_1_2 : MOF_MIRROR_AIR_1_3;
    rising_arc(d,p,age<12 ? age : age-7,age>=12);
    if (age==4) arc_hit(d,p,4,0,36);
    if (age==9) arc_hit(d,p,6,MOF_MOVE_HEAVY,42);
    if (age==17) arc_hit(d,p,12,MOF_MOVE_HEAVY|MOF_EFFECT_FALL,48);
    ++mof_magic.palma[p];
}
#endif

static void advance_arc(MofDuel *d,uint8_t p)
{
    const MofCaster *c=&mof_magic.caster[p];
#ifdef MOF_ALIS_COMBAT
    if (c->move==SLASH) laconian_cut(d,p);
#endif
    if (c->move==SABER && c->strain_window) {
        rising_arc(d,p,c->age>3 ? c->age-3 : 0,0);
        if (c->age==7) arc_hit(d,p,5,0,34);
        if (c->age==13) arc_hit(d,p,10,MOF_MOVE_HEAVY|MOF_EFFECT_FALL,40);
    }
    continue_palma(d,p);
}

void mof_choreo_advance(MofDuel *d)
{
    advance_arc(d,0);
    advance_arc(d,1);
}
#ifndef MOF_DUEL_HOST_TEST
#define MOF_SUPER_INPUT mof_choreo_super_input
#include "alis_super_input.inc"
#undef MOF_SUPER_INPUT
#endif
#endif
