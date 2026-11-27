#if defined(MOF_ALIS_MAGIC)
#pragma codeseg SMSBANK_MAGIC
#pragma constseg SMSBANK_MAGIC
#include <string.h>
#include <stddef.h>
#include "../inc/alis_magic.h"
#include "../inc/duel_combat.h"
#ifdef MOF_ALIS_FEEDBACK
#include "../inc/alis_feedback.h"
#endif
#include "magic_art.h"

/* These assembler absolute symbols reserve no bytes of ROM or initialized
   data. The size assertion and the production map locate the whole buffer. */
#ifdef MOF_DUEL_HOST_TEST
MofMagic mof_magic;
MofChapterPnt mof_chapter_pnt;
#else
static void magic_ram_address(void) __naked {
    __asm
    .globl _mof_magic
    _mof_magic = 0xc900
    .globl _mof_chapter_pnt
    _mof_chapter_pnt = 0xca40
    ret
    __endasm;
}
#endif
typedef char MagicRamSize[sizeof(MofMagic)<=0x140 ? 1 : -1];

typedef char PntRamSize[sizeof(MofChapterPnt)<=0xc0 ? 1 : -1];

typedef struct {uint8_t start,end,pose[3],impact_flags;} SpellTiming;
/* Poses are resolved against the same fighter packet manifest as the renderer. */
static const SpellTiming timings[SPELL_COUNT]={
    {0,0,{0,0,0},0},
    {6,17,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3},0},
    {9,23,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3},MOF_MOVE_HEAVY},
    {12,32,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3},MOF_MOVE_HEAVY},
    {10,32,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3},MOF_MOVE_HEAVY},
    {21,32,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3},0},
#ifdef MOF_ALIS_COMBAT
    {8,34,{MOF_MIRROR_SLASH_LOW, MOF_MIRROR_SLASH_RISE, MOF_MIRROR_RECOVER},MOF_MOVE_HEAVY},
#elif defined(MOF_ALIS_CHOREOGRAPHY)
    {7,22,{MOF_MIRROR_LOW_1_1, MOF_MIRROR_LOW_1_2, MOF_MIRROR_RECOVER},MOF_MOVE_HEAVY},
#else
    {7,22,{MOF_MIRROR_PREPARE, MOF_MIRROR_THRUST, MOF_MIRROR_RECOVER},MOF_MOVE_HEAVY},
#endif
    {5,26,{MOF_MIRROR_LOW_1_1, MOF_MIRROR_AIR_1_2, MOF_MIRROR_AIR_1_3},MOF_MOVE_HEAVY},
    {20,30,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3},0},
    {3,23,{MOF_MIRROR_RIPOSTE_1, MOF_MIRROR_RIPOSTE_2, MOF_MIRROR_RIPOSTE_4},0},
    {1,13,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3},0},
    {4,45,{MOF_MIRROR_PREPARE, MOF_MIRROR_THRUST, MOF_MIRROR_RECOVER},MOF_EFFECT_FINISH|MOF_MOVE_HEAVY}
};
static const int8_t arc[32]={0,3,5,8,10,12,13,14,14,13,12,10,8,5,3,0,
                             -2,-4,-6,-8,-10,-11,-12,-12,-11,-10,-8,-6,-5,-3,-2,-1};

void mof_magic_reset(void) {
    memset(&mof_magic,0,sizeof(mof_magic));
    mof_chapter_pnt.count=0;
#ifdef MOF_PALMA_VERSIONS
    uint8_t version=chapter.story ? 1 : mof_stage_choice;
    magic_map=magic_map_versions[version];
    magic_restore=magic_restore_versions[version];
    magic_base=magic_base_versions[version];
    magic_bank=magic_bank_versions[version];
#endif
}

#ifndef MOF_ALIS_COMBAT
#include "alis_magic_input.inc"
#endif

static void charge(uint8_t p) {if (chapter.meter[p]<8) ++chapter.meter[p];}

/* Collect both sides before cancelling poses. A pair of overlapping flames
   spends both projectiles, with one impact on this defender this tick. */
#ifdef MOF_ALIS_CHOREOGRAPHY
static void offer_effect(uint8_t p,uint8_t damage,uint8_t move,uint8_t flags) {
    if (!mof_magic.impact_move[p] || flags>mof_magic.impact_flags[p] ||
        (flags==mof_magic.impact_flags[p] && damage>mof_magic.impact_damage[p])) {
        mof_magic.impact_move[p]=move;
        mof_magic.impact_damage[p]=damage;
        mof_magic.impact_flags[p]=flags;
    }
}
#define offer(p,damage,move) offer_effect(p,damage,move,timings[move].impact_flags)
#else
static void offer(uint8_t p,uint8_t damage,uint8_t move) {
    uint8_t prev=mof_magic.impact_move[p];
    uint8_t force=timings[move].impact_flags;
    if (!prev || force>timings[prev].impact_flags ||
        (force==timings[prev].impact_flags && damage>mof_magic.impact_damage[p])) {
        mof_magic.impact_move[p]=move;
        mof_magic.impact_damage[p]=damage;
    }
}
#endif
static void resolve(MofDuel *d,uint8_t p) {
    uint8_t v=1u-p, move=mof_magic.impact_move[p], result;
    MofCaster *c=&mof_magic.caster[v];
    if (!move) return;
#ifdef MOF_ALIS_COMBAT
    result=mof_magic_contact(d,p,mof_magic.impact_damage[p],
        mof_magic.impact_flags[p]|(move==GUARDIANS ? 0 : MOF_EFFECT_CHIP));
#elif defined(MOF_ALIS_CHOREOGRAPHY)
    result=mof_magic_contact(d,p,mof_magic.impact_damage[p],mof_magic.impact_flags[p]);
#else
    result=mof_magic_contact(d,p,mof_magic.impact_damage[p],timings[move].impact_flags);
#endif
    if (!result) return;
    mof_magic.effect_mask|=(1u<<p);
    c->dizzy=c->move=c->pending=c->pose=0;
    if (result==MOF_DUEL_GUARDED) ++mof_magic.blocks[p];
    else ++mof_magic.hits[p];
    if (move==GUARDIANS && !d->fighters[v].life) {
        mof_magic.finisher=p+1;
        mof_magic.target_fighter=d->fighters[v].fighter;
    }
    /* Prefer the stronger audible contact in a trade. */
    if (!p || !(mof_magic.effect_mask&1u) ||
        timings[move].impact_flags>timings[mof_magic.impact_move[0]].impact_flags)
        mof_magic.audio=result==MOF_DUEL_GUARDED ? MIRROR : move;
}
static void spawn(MofDuel *d,uint8_t p,uint8_t index,uint8_t move) {
    MofShot *s=&mof_magic.shots[p*2+index];
    MofDuelFighter *a=&d->fighters[p];
    s->owner=p;s->kind=move;s->age=0;s->phase=(d->tick+p*11+index*15)&31;
    s->x=a->x+(a->face_right ? 10 : -10);
    if (move==MYAU) {
        s->x=a->x+(a->face_right ? -24 : 24);
        if (s->x<4) s->x=4;
        if (s->x>251) s->x=251;
    }
    s->dx=a->face_right ? 4 : -4;
    s->y=move==MYAU ? 137 : 111;
    s->ttl=move==FIRE_TAP ? 12 : move==FIRE_HOLD ? 25 :
#ifndef MOF_ALIS_COMBAT
        move==SLASH ? 20 :
#endif
        70;
    s->damage=move==MYAU ? 18 : move==TWIN_FIRE ? 7 : move==FIRE_TAP ? 6 : 10;
#ifdef MOF_ALIS_CHOREOGRAPHY
    if (move==MYAU) s->phase=0;
#endif
}
#ifdef MOF_ALIS_CHOREOGRAPHY
static void myau_flight(MofDuel *d,MofShot *s) {
    uint8_t target=1u-s->owner,stage,bit,reach;
    const MofDuelFighter *f=&d->fighters[target];
    const MofDuelBox *box=&d->tested_hurt[target];
    int16_t dx,center,limit;
#ifdef MOF_ALIS_FEEDBACK
    if (mof_feedback.duration && !s->age) return;
#endif
    if (!--s->ttl) return;
    ++s->age;
    stage=s->age<=11 ? 0 : s->age<=20 ? 1 : 2;
    dx=s->dx;
    if (stage==1) { dx=dx>0 ? 3 : -3;s->y-=6; }
    if (stage==2) {
        if (s->y>=132) {s->ttl=0;return;}
        dx=dx>0 ? 5 : -5;
        s->y+=5;
    }
    limit=f->x-(dx>0 ? 9 : -9);
    if ((dx>0 && s->x<limit) || (dx<0 && s->x>limit)) {
        s->x+=dx;
        if ((dx>0 && s->x>limit) || (dx<0 && s->x<limit)) s->x=limit;
    }
    bit=1u<<stage;
    if (s->phase&bit || !f->life || f->state>=MOF_DUEL_FALL) return;
    reach=stage==2 ? 10 : 6;
    center=s->x+d->tested_hurt_x[target]-f->x;
    if (center+reach<=box->left || center-reach>=box->right ||
        s->y+reach<=box->top || s->y-reach>=box->bottom) return;
    s->phase|=bit;
#ifdef MOF_ALIS_COMBAT
    offer_effect(s->owner,stage==0 ? 4 : stage==1 ? 6 : 10,MYAU,
                 stage==0 ? 0 : stage==1 ? MOF_MOVE_HEAVY|MOF_EFFECT_SHOVE :
                 MOF_MOVE_HEAVY|MOF_EFFECT_FALL);
#else
    offer_effect(s->owner,stage==0 ? 4 : stage==1 ? 6 : 10,MYAU,
                 stage==0 ? 0 : MOF_MOVE_HEAVY);
#endif
}
#endif
static void flight(MofDuel *d,MofShot *s) {
    uint8_t v=1-s->owner;
    MofDuelFighter *target=&d->fighters[v];
    MofCaster *c=&mof_magic.caster[v];
    const MofDuelBox *box=&d->tested_hurt[v];
    int16_t relative_x;
#ifdef MOF_ALIS_COMBAT
    uint8_t h=6;
    if (s->kind==MYAU) {myau_flight(d,s);return;}
#elif defined(MOF_ALIS_CHOREOGRAPHY)
    uint8_t h=s->kind==SLASH ? 12 : 6;
    if (s->kind==MYAU) {myau_flight(d,s);return;}
#else
    uint8_t h=4;
#endif
    ++s->age;
#ifndef MOF_ALIS_CHOREOGRAPHY
    if (s->kind==MYAU && s->age<=9) return;
    if (s->kind==MYAU && s->age<=17) {s->y-=7;return;}
#endif
    s->x+=s->dx;
    if (s->x<0 || s->x>255 || !--s->ttl) {
        if (s->kind==TWIN_FIRE && (s->x<0 || s->x>255)) ++mof_magic.full_range;
        s->ttl=0;return;
    }
    if (s->kind==TWIN_FIRE) s->y=109+arc[(s->phase+s->age)&31];
#ifndef MOF_ALIS_CHOREOGRAPHY
    else if (s->kind==MYAU) {
        int16_t distance=target->x-s->x;
        if (distance<0) distance=-distance;
        if (distance<86 && s->y<129) s->y+=5;
    }
#endif
    if (!target->life || target->state>=MOF_DUEL_FALL) return;
    /* The engine sampled the defender's posture in this live step. Its
       ground solver can then translate the pivot before projectiles move. */
    relative_x=s->x+(d->tested_hurt_x[v]-target->x);
    if (relative_x+4<=box->left || relative_x-4>=box->right ||
        s->y+h<=box->top || s->y-h>=box->bottom) return;
    if (c->move==MIRROR && c->age>=3 && c->age<=12 && s->kind!=MYAU) {
        s->owner=v;s->dx=-s->dx;s->ttl=64;++mof_magic.reflects[v];mof_magic.audio=MIRROR;
        return;
    }
    offer(s->owner,s->damage,s->kind);
    s->ttl=0;
}
static inline void cast(MofDuel *d,uint8_t p) {
    MofCaster *c=&mof_magic.caster[p];
    MofDuelFighter *f=&d->fighters[p],*r=&d->fighters[1-p];
    uint8_t move=c->move;
    int16_t gap;
    if (c->chat_wait) --c->chat_wait;
    if (c->dizzy) --c->dizzy;
    if (!move) {c->pose=0;return;}
    if (f->state!=MOF_DUEL_READY
#ifdef MOF_ALIS_CHOREOGRAPHY
        && !(move==MYAU && mof_magic.myau_cancel[p]==2 && f->state==MOF_DUEL_ATTACK)
#endif
        ) {c->move=c->pose=0;return;}
    ++c->age;
    c->pose=timings[move].pose[c->age<timings[move].start ? 0 : c->age<timings[move].start+6 ? 1 : 2];
#ifdef MOF_ALIS_CHOREOGRAPHY
    if (move==MYAU && c->age==1) spawn(d,p,0,move);
#endif
    if (c->age==timings[move].start) {
        if (move==REST || move==CHAT) {
            uint8_t gain;
            if(move==REST) {
                gain=f->life>94 ? 100-f->life : 6;
                f->life+=gain;
            } else {
                gain=chapter.meter[p]<8;
                charge(p);
            }
#ifdef MOF_ALIS_FEEDBACK
            if(gain) {
                mof_feedback.amount[p]=gain;
                mof_feedback.label[p]=move==REST ? MOF_GAIN_HP : MOF_GAIN_MP;
                mof_feedback.age[p]=16;
                ++mof_feedback.last_gain[p];
                mof_magic.audio=move==REST ? MOF_SFX_HP : MOF_SFX_MP;
            }
#endif
        }
        else if (move==FIRE_TAP || move==FIRE_HOLD || move==TWIN_FIRE
#ifndef MOF_ALIS_COMBAT
                 || move==SLASH
#endif
#ifndef MOF_ALIS_CHOREOGRAPHY
                 || move==MYAU
#endif
                 ) {
            spawn(d,p,0,move);
            if (move==TWIN_FIRE) spawn(d,p,1,move);
        }
    }
    if (move==SABER && c->age>=5 && c->age<=12 && !c->strain
#ifdef MOF_ALIS_CHOREOGRAPHY
        && !c->strain_window
#endif
        ) {
        gap=r->x-f->x;if (!c->face) gap=-gap;
        if (gap>=0 && gap<=35 && r->life && r->state<MOF_DUEL_FALL &&
            d->body[1-p].y_offset>=d->body[p].y_offset-49 && d->body[1-p].y_offset<=d->body[p].y_offset+28) {
            offer(p,12,SABER);c->strain=1;
        }
    }
    if (move==GUARDIANS && c->age>=4) {
        gap=r->x-f->x;
        if (gap>=-28 && gap<=28) {
            if (mof_magic.caster[1-p].dizzy && r->life && r->life<25) {
                offer(p,r->life,GUARDIANS);
            }
            c->move=c->pose=0;
        } else f->x+=gap>0 ? 6 : -6;
    }
    if (c->age>=timings[move].end) c->move=c->pose=0;
}
void mof_magic_step(MofDuel *d) {
    uint8_t i;
    mof_magic.effect_mask=0;
    if (!mof_magic.live_step) return;
    mof_magic.impact_move[0]=mof_magic.impact_move[1]=0;
    if (!mof_magic.caster[0].move) mof_magic.caster[0].strain=0;
    if (!mof_magic.caster[1].move) mof_magic.caster[1].strain=0;
    cast(d,0);cast(d,1);
#ifdef MOF_ALIS_CHOREOGRAPHY
    if (mof_magic.palma[0] || mof_magic.palma[1] ||
#ifdef MOF_ALIS_COMBAT
        mof_magic.caster[0].move==SLASH || mof_magic.caster[1].move==SLASH ||
#endif
        (mof_magic.caster[0].move==SABER && mof_magic.caster[0].strain_window) ||
        (mof_magic.caster[1].move==SABER && mof_magic.caster[1].strain_window))
        mof_choreo_step(d);
#endif
    mof_magic.busy=0;
    MofShot *s=mof_magic.shots;
    for (i=0;i<4;++i,++s) if (s->ttl) {
        flight(d,s);
        mof_magic.busy|=s->ttl;
    }
    if (mof_magic.impact_move[0]) resolve(d,0);
    if (mof_magic.impact_move[1]) resolve(d,1);
    mof_magic.busy|=mof_magic.caster[0].move|mof_magic.caster[0].dizzy|mof_magic.caster[0].pending|
                    mof_magic.caster[1].move|mof_magic.caster[1].dizzy|mof_magic.caster[1].pending;
#ifdef MOF_ALIS_CHOREOGRAPHY
    mof_magic.busy|=mof_magic.palma[0]|mof_magic.palma[1];
    mof_magic.busy|=mof_magic.myau_cancel[0]|mof_magic.myau_cancel[1];
    if ((d->fighters[0].standing_normal==MOF_DUEL_SPECIAL && d->fighters[0].contact==MOF_DUEL_LANDED) ||
        (d->fighters[1].standing_normal==MOF_DUEL_SPECIAL && d->fighters[1].contact==MOF_DUEL_LANDED))
        mof_magic.busy=1;
#endif
    /* A physical impact on this step takes the shared PSG voices ahead
       of a cast cue or reflection that produced no damage of its own. */
    if (d->hitstop && !mof_magic.effect_mask) mof_magic.audio=0;
}

/* The plan contains contiguous five-byte (cell, pattern address, bank)
   records. Only the wide glyph caller can emit several adjacent records. */
#ifdef MOF_DUEL_HOST_TEST
static void append_glyph(uint16_t cell,uint16_t stamp)
{
    if (mof_magic.count<MAGIC_TILES) {
        MofMagicTile *t=&mof_magic.next[mof_magic.count++];
        t->cell=cell;
        t->bank=magic_bank[stamp];
        t->address=magic_base[stamp]+((uint16_t)magic_map[cell]<<5);
#ifdef MOF_ALIS_CHOREOGRAPHY
        if (t->address>=0xc000u) {t->address-=0x4000u;++t->bank;}
#endif
    }
}
#else
typedef char MagicGlyphLayout[sizeof(MofMagicTile)==5 && offsetof(MofMagic,count)==86 &&
                              offsetof(MofMagic,next)==121 && MAGIC_TILES==16 ? 1 : -1];
static void append_glyph(uint16_t cell,uint16_t stamp) __naked
{
    cell;stamp;
    __asm
        ld a,(_mof_magic+86)
        cp #16
        ret nc
        push de                 ; stamp
        push hl                 ; map cell
        ld c,a
        inc a
        ld (_mof_magic+86),a
        ld a,c
        add a,a
        add a,a
        add a,c
        ld e,a
        ld d,#0
        ld hl,#(_mof_magic+121)
        add hl,de
        pop de
        ld (hl),e
        inc hl
        ld (hl),d
        inc hl
        push hl                 ; next address field
#ifdef MOF_PALMA_VERSIONS
        ld hl,(_magic_map)
#else
        ld hl,#_magic_map
#endif
        add hl,de
        ld l,(hl)
        ld h,#0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ex de,hl                ; composited tile offset
        pop bc
        pop hl                  ; stamp
        push hl
        add hl,hl
        push de
#ifdef MOF_PALMA_VERSIONS
        ld de,(_magic_base)
#else
        ld de,#_magic_base
#endif
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        pop hl
        add hl,de
#ifdef MOF_ALIS_CHOREOGRAPHY
        bit 6,h                 ; linear strip entered the next mapper bank
        res 6,h
#endif
        ld a,l
        ld (bc),a
        inc bc
        ld a,h
        ld (bc),a
        inc bc
        pop hl
#ifdef MOF_PALMA_VERSIONS
        ld de,(_magic_bank)
#else
        ld de,#_magic_bank
#endif
        add hl,de
        ld a,(hl)
#ifdef MOF_ALIS_CHOREOGRAPHY
        jr z,00001$
        inc a
00001$:
#endif
        ld (bc),a
        ret
    __endasm;
}
#endif
static inline void glyph_cell(int16_t col,uint8_t row,uint8_t stamp)
{
    if ((uint16_t)(col-1)<31u)
        append_glyph(((uint16_t)row<<5)+(uint8_t)col,stamp);
}
static void glyph(uint8_t glyph_id,int16_t x,int16_t y,uint8_t face,uint8_t scroll)
{
#ifdef MOF_ALIS_CHOREOGRAPHY
    static const uint8_t columns[]={2,2,1,2,2,3,1,2,1,2,1,2,3};
    static const uint8_t rows[]={2,3,1,2,2,2,1,1,1,3,1,1,4};
    uint8_t w=columns[glyph_id], stamp=magic_glyph[glyph_id*2+(!face)];
    int16_t origin=x-4*w;
    int16_t row=(y-4*rows[glyph_id])>>3;
    for (uint8_t yy=0;yy<rows[glyph_id];++yy,++row,stamp+=w) {
        int16_t left=origin;
#ifdef MOF_ALIS_COMBAT
        if (row<8 || row>17) continue;
#else
        if (row<3 || row>17) continue;
#endif
        if (row>=4 && row<12) left-=(int8_t)scroll;
        left>>=3;
        for (uint8_t xx=0;xx<w;++xx) glyph_cell(left+xx,row,stamp+xx);
    }
#else
    uint8_t wide=glyph_id>=GL_NUT && glyph_id<=GL_DIVE;
    uint8_t stamp=magic_glyph[glyph_id*2+(!face)];
    int16_t origin=x-(wide ? 8 : 4);
    int16_t row=(y-(wide ? 8 : 4))>>3;
    if (!wide) {
        if (row<3 || row>19) return;
        if (row>=4 && row<12) origin-=(int8_t)scroll;
        glyph_cell(origin>>3,row,stamp);
        return;
    }
    for (uint8_t yy=0;yy<2;++yy,++row,stamp+=2) {
        int16_t left=origin;
        if (row<3 || row>19) continue;
        if (row>=4 && row<12) left-=(int8_t)scroll;
        left>>=3;
        glyph_cell(left,row,stamp);
        glyph_cell(left+1,row,stamp+1);
    }
#endif
}
void mof_magic_plan(const MofDuel *d,uint8_t scroll) {
    uint8_t i;
    mof_magic.count=0;
    if (chapter.phase!=MOF_PLAY) return;
    MofShot *s=mof_magic.shots;
    for (i=0;i<4;++i,++s) {
        uint8_t g;
        if (!s->ttl) continue;
        if (s->kind==MYAU) g=s->age<=
#ifdef MOF_ALIS_CHOREOGRAPHY
            11
#else
            9
#endif
            ? GL_NUT : s->age<=20 ? GL_WING : GL_DIVE;
        else g=
#ifndef MOF_ALIS_COMBAT
            s->kind==SLASH ? GL_WAVE :
#endif
            GL_FIRE;
        glyph(g,s->x,s->y,s->dx>0,scroll);
    }
    for (i=0;i<2;++i) {
        const MofCaster *c=&mof_magic.caster[i];
        const MofDuelFighter *f=&d->fighters[i];
        int16_t x=f->x,y=144+d->body[i].y_offset;
#ifdef MOF_ALIS_CHOREOGRAPHY
#ifdef MOF_ALIS_COMBAT
        if (mof_combat.landing[i]) glyph(GL_DUST,x,141,f->face_right,scroll);
        else if (d->hitstop && mof_combat.spark[i])
            glyph(mof_combat.spark[i]==2 ? GL_SHIELD_SPARK : GL_SABER,
                  x+(f->face_right ? 11 : -11),y-34,f->face_right,scroll);
        if (mof_magic.palma[i]>=MOF_PALMA_RISE && mof_magic.palma[i]<=MOF_PALMA_RELEASE)
            glyph(GL_GOLD_ARC,x+(f->face_right ? 23 : -23),y-30,f->face_right,scroll);
        else if (mof_magic.palma[i]>=MOF_PALMA_CHOP && mof_magic.palma[i]<=MOF_PALMA_CHOP+4u)
            glyph(GL_WAVE,x+(f->face_right ? 25 : -25),y-30,f->face_right,scroll);
#else
        if (f->standing_normal==MOF_DUEL_SPECIAL && f->contact==MOF_DUEL_LANDED) {
            const MofDuelFighter *target=&d->fighters[1-i];
            glyph(GL_SHIELD_SPARK,target->x-(f->face_right ? 15 : -15),y-34,f->face_right,scroll);
        }
        if (mof_magic.palma[i] && mof_magic.palma[i]!=255)
            glyph(mof_magic.palma[i]>=13 ? GL_GOLD_ARC : GL_WAVE,x+(f->face_right ? 23 : -23),
                  y-32,f->face_right,scroll);
#endif
#endif
        if (c->dizzy) glyph(GL_STARS,x+((c->dizzy>>2)&3),y-60,1,scroll);
        if (c->move==REST || c->move==CHAT) glyph(GL_REST,x,y-50,1,scroll);
        else if (c->move==MIRROR) glyph(GL_MIRROR,x+(c->face ? 12 : -12),y-32,c->face,scroll);
#ifdef MOF_ALIS_COMBAT
        else if (c->move==SLASH && c->age>=8 && c->age<=14)
            glyph(GL_LACONIAN,x+(c->face ? 26 : -26),119-(c->age-8)*3,c->face,scroll);
#endif
        else if (c->move==SABER) {
#ifdef MOF_ALIS_CHOREOGRAPHY
            if (c->strain_window && c->age>=5 && c->age<=14)
                glyph(GL_WAVE,x+(c->face ? 22 : -22),y-31,c->face,scroll);
            else
#endif
                glyph(GL_SABER,x+(c->face ? 19 : -19),y-52,c->face,scroll);
        }
    }
}

/* Scratch directories are filled only for the cells in these two packets.
   The high bit marks a blade in front. The low bits name the last glyph. */
typedef struct { uint8_t old[768],next[768]; } MagicCellOwners;
#ifdef MOF_DUEL_HOST_TEST
static MagicCellOwners magic_owners;
#else
#define magic_owners (*(MagicCellOwners *)0xd200u)
#endif

static inline void stage_magic_cell(uint16_t cell,uint16_t tile)
{
    MofPntWrite *write=&mof_chapter_pnt.cells[mof_chapter_pnt.count++];
    write->address=0x7800u|(cell<<1);
    write->tile=tile;
}
void mof_magic_tiles(const uint8_t *blades,uint8_t length,uint16_t first,uint8_t blades_changed)
{
    const MofMagicTile *old,*next;
    const uint8_t *blade;
    uint8_t i;
    /* A stable slot continues to own its PNT cell when only the composite
       pattern changes. This also holds for stacked glyphs in identical order. */
    if (!blades_changed && mof_magic.count==mof_magic.old_count) {
        for (i=0,next=mof_magic.next,old=mof_magic.old;i<mof_magic.count;++i,++next,++old) {
            if (next->cell!=old->cell) break;
            mof_magic.upload[i]=next->address!=old->address || next->bank!=old->bank;
        }
        if (i==mof_magic.count) return;
    }
    if (!length && mof_magic.count<=1u && mof_magic.old_count<=1u) {
        old=mof_magic.old;
        next=mof_magic.next;
        if (mof_magic.old_count && (!mof_magic.count || old->cell!=next->cell))
            stage_magic_cell(old->cell,magic_restore[magic_map[old->cell]]);
        if (mof_magic.count) {
            mof_magic.upload[0]=!mof_magic.old_count || next->address!=old->address || next->bank!=old->bank;
            stage_magic_cell(next->cell,first);
        }
        return;
    }
    /* Only cells in the old or new packet can be read. Clear exactly that
       union before painting the two top-slot indices; RAM may be uninitialized. */
    for (i=0,old=mof_magic.old;i<mof_magic.old_count;++i,++old) magic_owners.next[old->cell]=0;
    for (i=0,next=mof_magic.next;i<mof_magic.count;++i,++next) magic_owners.old[next->cell]=0;
    for (i=0,old=mof_magic.old;i<mof_magic.old_count;++i,++old) magic_owners.old[old->cell]=i+1;
    for (i=0,next=mof_magic.next;i<mof_magic.count;++i,++next) magic_owners.next[next->cell]=i+1;
    for (i=0,blade=blades;i<length;++i,blade+=3) {
        uint16_t cell=(((uint16_t)blade[1]<<8 | blade[0])-0x7800u)>>1;
        magic_owners.next[cell]|=0x80;
    }
    for (i=0,old=mof_magic.old;i<mof_magic.old_count;++i,++old) {
        if (!magic_owners.next[old->cell] && magic_owners.old[old->cell]==i+1)
            stage_magic_cell(old->cell,magic_restore[magic_map[old->cell]]);
    }
    for (i=0,next=mof_magic.next,old=mof_magic.old;i<mof_magic.count;++i,++next,++old) {
        mof_magic.upload[i]=i>=mof_magic.old_count || next->address!=old->address || next->bank!=old->bank;
        if (magic_owners.next[next->cell]==i+1 && (blades_changed || magic_owners.old[next->cell]!=i+1))
            stage_magic_cell(next->cell,first+i);
    }
}
#endif
