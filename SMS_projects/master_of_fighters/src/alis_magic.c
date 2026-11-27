#if defined(MOF_ALIS_MAGIC)
#pragma codeseg SMSBANK_MAGIC
#pragma constseg SMSBANK_MAGIC
#include <string.h>
#include <stddef.h>
#include "../inc/alis_magic.h"
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

enum { D=1,F=2,B=3,DF=4,DB=5 };
typedef struct {uint8_t cost,start,end,pose[3],impact_flags;} SpellTiming;
/* Poses are resolved against the same fighter packet manifest as the renderer. */
static const SpellTiming timings[SPELL_COUNT]={
    {0,0,0,{0,0,0},0},
    {0,6,17,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3},0},
    {0,9,23,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3},MOF_MOVE_HEAVY},
    {4,12,32,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3},MOF_MOVE_HEAVY},
    {4,10,32,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3},MOF_MOVE_HEAVY},
    {2,21,32,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3},0},
    {0,7,22,{MOF_MIRROR_PREPARE, MOF_MIRROR_THRUST, MOF_MIRROR_RECOVER},MOF_MOVE_HEAVY},
    {0,5,26,{MOF_MIRROR_LOW_1_1, MOF_MIRROR_AIR_1_2, MOF_MIRROR_AIR_1_3},MOF_MOVE_HEAVY},
    {0,20,30,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3},0},
    {0,3,23,{MOF_MIRROR_RIPOSTE_1, MOF_MIRROR_RIPOSTE_2, MOF_MIRROR_RIPOSTE_4},0},
    {0,1,13,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3},0},
    {8,4,45,{MOF_MIRROR_PREPARE, MOF_MIRROR_THRUST, MOF_MIRROR_RECOVER},MOF_EFFECT_FINISH|MOF_MOVE_HEAVY}
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

static uint8_t direction(uint8_t keys,uint8_t face) {
    uint8_t x=keys&12, y=keys&3;
    if (y==3 || y==1 || x==12) return 6;
    if (!x) return y ? D : 0;
    if (x==(face ? 8 : 4)) return y ? DF : F;
    return y ? DB : B;
}
static uint8_t decisive(const MofDuel *d,uint8_t p) {
    return d->fighters[p].life && d->fighters[p].life<=25 && chapter.meter[p]==8
        && chapter.wins[p]+1>=chapter.target && d->fighters[1-p].life && d->fighters[1-p].life<25;
}
static uint8_t command(const MofFighterDef *def,const uint8_t *h,uint8_t buttons) {
    const MofCommand *binding;
    uint8_t i,gesture;
    if (h[3]==F && h[4]==B && h[5]==F && buttons==MOF_DUEL_ONE) return STUN;
    if (h[3]==D && h[4]==DF && h[5]==F) {
        gesture=G_QCF;
        if (h[0]==D && h[1]==DF && h[2]==F) gesture=G_DOUBLE_QCF;
    } else if (h[3]==F && h[4]==D && h[5]==DF) gesture=G_DP;
    else if (h[3]==D && h[4]==DB && h[5]==B) gesture=G_QCB;
    else if (h[4]==D && h[5]==D) gesture=G_DOWN_DOWN;
    else if (h[4]==B && h[5]==B) gesture=G_BACK_BACK;
    else return SPELL_NONE;
    do {
        binding=def->gestures;
        for (i=0;i<def->gesture_count;++i,++binding)
            if (binding->needs==gesture && binding->keys==buttons) return binding->move;
        if (gesture!=G_DOUBLE_QCF) break;
        gesture=G_QCF;
    } while (1);
    return SPELL_NONE;
}
static uint8_t armed(const MofDuel *d,uint8_t p,uint8_t move) {
    MofCaster *c=&mof_magic.caster[p];
    if (!move || move>=SPELL_COUNT || chapter.meter[p]<timings[move].cost) return 0;
    if (move==REST) return d->fighters[p].life<100;
    if (move==CHAT) return !c->chat_wait && chapter.meter[p]<8;
    if (move==STUN) return !c->stun_used && d->fighters[p].life<=25 && chapter.meter[p]==8
        && d->fighters[1-p].state==MOF_DUEL_READY && !d->body[1-p].y_offset;
    if (move==GUARDIANS) return decisive(d,p) && mof_magic.caster[1-p].dizzy;
    if (move==TWIN_FIRE || move==MYAU || move==FIRE_TAP || move==FIRE_HOLD || move==SLASH)
        return !mof_magic.shots[p*2].ttl && !mof_magic.shots[p*2+1].ttl;
    return 1;
}
static void begin(uint8_t p,uint8_t move) {
    MofCaster *c=&mof_magic.caster[p];
    c->strain=0;c->age=0;c->move=move;c->window=0;c->pending=0;
    chapter.meter[p]-=timings[move].cost;
    mof_magic.busy=1;
    ++mof_magic.events[p][move];
    mof_magic.audio=move;
    if (move==STUN) c->stun_used=1;
    if (move==CHAT) c->chat_wait=100;
}
static inline void input_player(const MofDuel *d,uint8_t p,uint8_t keys) {
    MofCaster *c=&mof_magic.caster[p];
    const MofDuelFighter *f=&d->fighters[p];
    uint8_t dir=direction(keys,f->face_right),buttons=keys&48,edge=buttons&~c->held_button;
    uint8_t move=0;
    mof_magic.pad[p]=keys;mof_magic.locked[p]=0;
    if (d->hitstop) return;
    c->held_button=buttons;
    if (c->face!=f->face_right) {c->window=c->pending=0;c->previous=0;}
    c->face=f->face_right;
    if (f->state!=MOF_DUEL_READY) {
        c->window=c->pending=c->move=c->pose=c->dizzy=0;
        c->previous=dir;
        return;
    }
    if (c->dizzy || c->move) {
        mof_magic.locked[p]=1;
        mof_magic.pad[p]=(c->move==SABER && c->age==3) ? MOF_DUEL_UP : 0;
        c->previous=dir;
        return;
    }
    if (d->body[p].y_offset || d->body[p].jump_pending) {c->pending=c->window=0;return;}
    if (c->pending) {
        if (!(buttons&16) || ++c->pending>=6) {
            move=(buttons&16) ? FIRE_HOLD : FIRE_TAP;
            if (armed(d,p,move)) begin(p,move);
            c->pending=0;
        }
        mof_magic.pad[p]=0;mof_magic.locked[p]=1;return;
    }
    if (c->window) --c->window;
    if (dir && dir!=c->previous) {
        if (!c->window) memset(c->history,0,6);
        memmove(c->history,c->history+1,5);c->history[5]=dir;c->window=16;
    }
    c->previous=dir;
    if (edge && edge==buttons && dir && c->window) move=command(f->def,c->history,buttons);
    if ((move==GUARDIANS || move==STUN) && !armed(d,p,move)) {
        c->window=0;mof_magic.locked[p]=1;mof_magic.pad[p]=0;return;
    }
    if (move && armed(d,p,move)) {
        mof_magic.locked[p]=1;mof_magic.pad[p]=0;
        if (move==FIRE_TAP) {c->pending=1;c->window=0;mof_magic.busy=1;}
        else begin(p,move);
    }
}
void mof_magic_input(const MofDuel *d,uint8_t one,uint8_t two) {
    mof_magic.live_step=!d->hitstop;
    input_player(d,0,one);input_player(d,1,two);
    if (!d->hitstop) {
        uint8_t p;
        for (p=0;p<2;++p) {
            const MofCaster *c=&mof_magic.caster[p];
            if (c->move==STUN && !c->age) {
                MofCaster *victim=&mof_magic.caster[1-p];
                victim->dizzy=84;
                victim->pending=0;
                if (victim->move!=STUN) victim->move=victim->pose=0;
                mof_magic.pad[1-p]=0;
                mof_magic.locked[1-p]=1;
            }
        }
    }
}
static void charge(uint8_t p) {if (chapter.meter[p]<8) ++chapter.meter[p];}

/* Collect both sides before cancelling poses. A pair of overlapping flames
   spends both projectiles, with one impact on this defender this tick. */
static void offer(uint8_t p,uint8_t damage,uint8_t move) {
    uint8_t prev=mof_magic.impact_move[p];
    uint8_t force=timings[move].impact_flags;
    if (!prev || force>timings[prev].impact_flags ||
        (force==timings[prev].impact_flags && damage>mof_magic.impact_damage[p])) {
        mof_magic.impact_move[p]=move;
        mof_magic.impact_damage[p]=damage;
    }
}
static void resolve(MofDuel *d,uint8_t p) {
    uint8_t v=1u-p, move=mof_magic.impact_move[p], result;
    MofCaster *c=&mof_magic.caster[v];
    if (!move) return;
    result=mof_magic_contact(d,p,mof_magic.impact_damage[p],timings[move].impact_flags);
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
    s->ttl=move==FIRE_TAP ? 12 : move==FIRE_HOLD ? 25 : move==SLASH ? 20 : 70;
    s->damage=move==MYAU ? 18 : move==TWIN_FIRE ? 7 : move==FIRE_TAP ? 6 : 10;
}
static void flight(MofDuel *d,MofShot *s) {
    uint8_t v=1-s->owner;
    MofDuelFighter *target=&d->fighters[v];
    MofCaster *c=&mof_magic.caster[v];
    const MofDuelBox *box=&d->tested_hurt[v];
    int16_t relative_x;
    ++s->age;
    if (s->kind==MYAU && s->age<=9) return;
    if (s->kind==MYAU && s->age<=17) {s->y-=7;return;}
    s->x+=s->dx;
    if (s->x<0 || s->x>255 || !--s->ttl) {
        if (s->kind==TWIN_FIRE && (s->x<0 || s->x>255)) ++mof_magic.full_range;
        s->ttl=0;return;
    }
    if (s->kind==TWIN_FIRE) s->y=109+arc[(s->phase+s->age)&31];
    else if (s->kind==MYAU) {
        int16_t distance=target->x-s->x;
        if (distance<0) distance=-distance;
        if (distance<86 && s->y<129) s->y+=5;
    }
    if (!target->life || target->state>=MOF_DUEL_FALL) return;
    /* The engine sampled the defender's posture in this live step. Its
       ground solver can then translate the pivot before projectiles move. */
    relative_x=s->x+(d->tested_hurt_x[v]-target->x);
    if (relative_x+4<=box->left || relative_x-4>=box->right ||
        s->y+4<=box->top || s->y-4>=box->bottom) return;
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
    if (f->state!=MOF_DUEL_READY) {c->move=c->pose=0;return;}
    ++c->age;
    c->pose=timings[move].pose[c->age<timings[move].start ? 0 : c->age<timings[move].start+6 ? 1 : 2];
    if (c->age==timings[move].start) {
        if (move==REST) f->life=f->life>94 ? 100 : f->life+6;
        else if (move==CHAT) charge(p);
        else if (move==FIRE_TAP || move==FIRE_HOLD || move==SLASH || move==TWIN_FIRE || move==MYAU) {
            spawn(d,p,0,move);
            if (move==TWIN_FIRE) spawn(d,p,1,move);
        }
    }
    if (move==SABER && c->age>=5 && c->age<=12 && !c->strain) {
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
}
void mof_magic_plan(const MofDuel *d,uint8_t scroll) {
    uint8_t i;
    mof_magic.count=0;
    if (chapter.phase!=MOF_PLAY) return;
    MofShot *s=mof_magic.shots;
    for (i=0;i<4;++i,++s) {
        uint8_t g;
        if (!s->ttl) continue;
        if (s->kind==MYAU) g=s->age<=9 ? GL_NUT : s->age<=20 ? GL_WING : GL_DIVE;
        else g=s->kind==SLASH ? GL_WAVE : GL_FIRE;
        glyph(g,s->x,s->y,s->dx>0,scroll);
    }
    for (i=0;i<2;++i) {
        const MofCaster *c=&mof_magic.caster[i];
        if (!c->dizzy && c->move!=REST && c->move!=CHAT && c->move!=MIRROR && c->move!=SABER) continue;
        const MofDuelFighter *f=&d->fighters[i];
        int16_t x=f->x,y=144+d->body[i].y_offset;
        if (c->dizzy) glyph(GL_STARS,x+((c->dizzy>>2)&3),y-60,1,scroll);
        if (c->move==REST || c->move==CHAT) glyph(GL_REST,x,y-50,1,scroll);
        else if (c->move==MIRROR) glyph(GL_MIRROR,x+(c->face ? 12 : -12),y-32,c->face,scroll);
        else if (c->move==SABER) glyph(GL_SABER,x+(c->face ? 19 : -19),y-52,c->face,scroll);
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
