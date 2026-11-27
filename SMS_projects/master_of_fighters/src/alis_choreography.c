#ifdef MOF_ALIS_CHOREOGRAPHY
#pragma codeseg SMSBANK_CAMERA
#pragma constseg SMSBANK_CAMERA
#include "../inc/alis_magic.h"
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

static void advance_arc(MofDuel *d,uint8_t p)
{
    const MofCaster *c=&mof_magic.caster[p];
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
