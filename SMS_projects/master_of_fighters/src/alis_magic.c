#if defined(MOF_ALIS_MAGIC)
#pragma codeseg SMSBANK_MAGIC
#pragma constseg SMSBANK_MAGIC
#include <string.h>
#include "../inc/alis_magic.h"
#include "magic_art.h"

/* These assembler absolute symbols reserve no bytes of ROM or initialized
   data. The size assertion and the production map locate the whole buffer. */
#ifdef MOF_DUEL_HOST_TEST
MofMagic mof_magic;
#else
static void magic_ram_address(void) __naked {
    __asm
    .globl _mof_magic
    _mof_magic = 0xc900
    ret
    __endasm;
}
#endif
typedef char MagicRamSize[sizeof(MofMagic)<=512 ? 1 : -1];

enum { D=1,F=2,B=3,DF=4,DB=5 };
typedef struct {uint8_t cost,start,end,pose[3];} SpellTiming;
/* Poses are resolved against the same fighter packet manifest as the renderer. */
static const SpellTiming timings[SPELL_COUNT]={
    {0,0,0,{0,0,0}},
    {0,6,17,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3}},
    {0,9,23,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3}},
    {4,12,32,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3}},
    {4,10,32,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3}},
    {2,21,32,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3}},
    {0,7,22,{MOF_MIRROR_PREPARE, MOF_MIRROR_THRUST, MOF_MIRROR_RECOVER}},
    {0,5,26,{MOF_MIRROR_LOW_1_1, MOF_MIRROR_AIR_1_2, MOF_MIRROR_AIR_1_3}},
    {0,20,30,{MOF_MIRROR_LISTEN_1, MOF_MIRROR_LISTEN_2, MOF_MIRROR_LISTEN_3}},
    {0,3,23,{MOF_MIRROR_RIPOSTE_1, MOF_MIRROR_RIPOSTE_2, MOF_MIRROR_RIPOSTE_4}},
    {0,1,13,{MOF_MIRROR_PALMA_1, MOF_MIRROR_PALMA_2, MOF_MIRROR_PALMA_3}},
    {8,4,45,{MOF_MIRROR_PREPARE, MOF_MIRROR_THRUST, MOF_MIRROR_RECOVER}}
};
static const int8_t arc[32]={0,3,5,8,10,12,13,14,14,13,12,10,8,5,3,0,
                             -2,-4,-6,-8,-10,-11,-12,-12,-11,-10,-8,-6,-5,-3,-2,-1};

void mof_magic_reset(void) { memset(&mof_magic,0,sizeof(mof_magic)); }

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
static uint8_t command(MofCaster *c,uint8_t button) {
    const uint8_t *h=c->history;
    if (button==32 && h[0]==D && h[1]==DF && h[2]==F && h[3]==D && h[4]==DF && h[5]==F)
        return GUARDIANS;
    if (button==16 && h[3]==F && h[4]==B && h[5]==F) return STUN;
    if (button==16 && h[3]==F && h[4]==D && h[5]==DF) return SABER;
    if (h[3]==D && h[4]==DF && h[5]==F) {
        if (button==48) return TWIN_FIRE;
        if (button==16) return SLASH;
    }
    if (h[3]==D && h[4]==DB && h[5]==B) {
        if (button==32) return MYAU;
        if (button==16) return MIRROR;
    }
    if (h[4]==D && h[5]==D) return button==16 ? FIRE_TAP : button==32 ? REST : 0;
    if (button==32 && h[4]==B && h[5]==B) return CHAT;
    return 0;
}
static uint8_t armed(const MofDuel *d,uint8_t p,uint8_t move) {
    MofCaster *c=&mof_magic.caster[p];
    if (!move || (d->fighters[p].fighter!=MOF_DUEL_ALIS && move!=STUN) || chapter.meter[p]<timings[move].cost) return 0;
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
    if (move==STUN) {c->stun_used=1;mof_magic.caster[1-p].dizzy=84;}
    if (move==CHAT) c->chat_wait=100;
}
static void input_player(const MofDuel *d,uint8_t p,uint8_t keys) {
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
    if (edge && dir && c->window) move=command(c,buttons);
    if ((move==GUARDIANS || move==STUN) && !armed(d,p,move)) {
        c->window=0;mof_magic.locked[p]=1;mof_magic.pad[p]=0;return;
    }
    if (armed(d,p,move)) {
        mof_magic.locked[p]=1;mof_magic.pad[p]=0;
        if (move==FIRE_TAP) {c->pending=1;c->window=0;mof_magic.busy=1;}
        else begin(p,move);
    }
}
void mof_magic_input(const MofDuel *d,uint8_t one,uint8_t two) {
    mof_magic.live_step=!d->hitstop;
    input_player(d,0,one);input_player(d,1,two);
    if (mof_magic.caster[0].dizzy) {mof_magic.pad[0]=0;mof_magic.locked[0]=1;}
}
static void charge(uint8_t p) {if (chapter.meter[p]<8) ++chapter.meter[p];}

static void impact(MofDuel *d,uint8_t p,uint8_t damage,uint8_t heavy) {
    uint8_t v=1-p;
    MofDuelFighter *target=&d->fighters[v];
    MofCaster *c=&mof_magic.caster[v];
    uint8_t guarded=target->guarding && !c->dizzy;
    c->dizzy=c->move=c->pending=c->pose=0;
    target->state_since=d->tick;target->thrown=0;target->spent=1;
    if (guarded) {
        target->state=MOF_DUEL_BLOCK;target->reaction=MOF_REACT_GUARD_STAND+target->guarding-1;
        ++mof_magic.blocks[p];
    } else {
        target->life=target->life>damage ? target->life-damage : 0;
        target->state=target->life ? MOF_DUEL_HIT : MOF_DUEL_KO;
        target->hit_duration=heavy ? 20 : 10;target->reaction=MOF_REACT_BODY;
        ++mof_magic.hits[p];charge(v);
    }
    charge(p);d->hitstop=heavy ? 11 : 4;
    d->hitstop_target=v|(heavy && !guarded ? MOF_DUEL_HITSTOP_SHAKE : 0);
    mof_magic.audio=guarded ? MIRROR : heavy ? MYAU : FIRE_TAP;
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
    MofDuelBox box;
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
    mof_magic_hurt(d,v,&box);
    if (s->x+4<box.left || s->x-4>=box.right || s->y+4<box.top || s->y-4>=box.bottom) return;
    if (c->move==MIRROR && c->age>=3 && c->age<=12 && s->kind!=MYAU) {
        s->owner=v;s->dx=-s->dx;s->ttl=64;++mof_magic.reflects[v];mof_magic.audio=MIRROR;
        return;
    }
    impact(d,s->owner,s->damage,s->kind==MYAU);
    s->ttl=0;
}
static void cast(MofDuel *d,uint8_t p) {
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
            impact(d,p,12,1);c->strain=1;
        }
    }
    if (move==GUARDIANS && c->age>=4) {
        gap=r->x-f->x;
        if (gap>=-28 && gap<=28) {
            if (mof_magic.caster[1-p].dizzy && r->life && r->life<25) {
                mof_magic.finisher=p+1;
                mof_magic.target_fighter=r->fighter;
                r->life=0;r->state=MOF_DUEL_KO;r->state_since=d->tick;
                mof_magic.caster[1-p].dizzy=0;
            }
            c->move=c->pose=0;
        } else f->x+=gap>0 ? 6 : -6;
    }
    if (c->age>=timings[move].end) c->move=c->pose=0;
}
void mof_magic_step(MofDuel *d) {
    uint8_t i;
    if (!mof_magic.live_step) return;
    for (i=0;i<2;++i) {
        if (!mof_magic.caster[i].move) mof_magic.caster[i].strain=0;
        cast(d,i);
    }
    mof_magic.busy=0;
    for (i=0;i<4;++i) if (mof_magic.shots[i].ttl) {
        flight(d,&mof_magic.shots[i]);
        mof_magic.busy|=mof_magic.shots[i].ttl;
    }
    for (i=0;i<2;++i) {
        const MofCaster *c=&mof_magic.caster[i];
        mof_magic.busy|=c->move|c->dizzy|c->pending;
    }
}

static void glyph(uint8_t glyph_id,int16_t x,int16_t y,uint8_t face,uint8_t scroll) {
    uint8_t wide=(glyph_id>=GL_NUT && glyph_id<=GL_DIVE) ? 2 : 1;
    uint8_t id=magic_glyph[glyph_id*2+(!face)],xx,yy;
    int16_t row=(y-(wide*4))>>3;
    for (yy=0;yy<wide;++yy) {
        int16_t tile_y=row+yy;
        int16_t left=x-wide*4;
        if (tile_y<3 || tile_y>19) continue;
        if (tile_y>=4 && tile_y<12) left-=(int8_t)scroll;
        for (xx=0;xx<wide;++xx) {
            int16_t col=(left>>3)+xx;
            uint16_t cell;
            uint8_t base,stamp;
            MofMagicTile *t;
            if (col<1 || col>=32 || mof_magic.count>=MAGIC_TILES) continue;
            cell=tile_y*32+col;base=magic_map[cell];stamp=id+yy*wide+xx;
            t=&mof_magic.next[mof_magic.count++];
            t->cell=cell;t->restore=magic_restore[base];t->bank=magic_bank[stamp];
            t->address=magic_base[stamp]+((uint16_t)base<<5);
        }
    }
}
void mof_magic_plan(const MofDuel *d,uint8_t scroll) {
    uint8_t i;
    mof_magic.count=0;
    if (chapter.phase!=MOF_PLAY) return;
    for (i=0;i<4;++i) {
        MofShot *s=&mof_magic.shots[i];
        uint8_t g;
        if (!s->ttl) continue;
        if (s->kind==MYAU) g=s->age<=9 ? GL_NUT : s->age<=20 ? GL_WING : GL_DIVE;
        else g=s->kind==SLASH ? GL_WAVE : GL_FIRE;
        glyph(g,s->x,s->y,s->dx>0,scroll);
    }
    for (i=0;i<2;++i) {
        const MofCaster *c=&mof_magic.caster[i];
        const MofDuelFighter *f=&d->fighters[i];
        int16_t x=f->x,y=144+d->body[i].y_offset;
        if (c->dizzy) glyph(GL_STARS,x+((c->dizzy>>2)&3),y-60,1,scroll);
        if (c->move==REST || c->move==CHAT) glyph(GL_REST,x,y-50,1,scroll);
        else if (c->move==MIRROR) glyph(GL_MIRROR,x+(c->face ? 12 : -12),y-32,c->face,scroll);
        else if (c->move==SABER) glyph(GL_SABER,x+(c->face ? 19 : -19),y-52,c->face,scroll);
    }
}

static void visible_cell(uint16_t cell,uint16_t tile,const uint8_t *blades,uint8_t length)
{
    uint16_t address=0x7800u|(cell<<1);
    while (length--) {
        if (blades[0]==(uint8_t)address && blades[1]==(uint8_t)(address>>8)) return;
        blades+=3;
    }
    mof_magic.writes[mof_magic.write_count].cell=cell;
    mof_magic.writes[mof_magic.write_count++].tile=tile;
}
void mof_magic_tiles(const uint8_t *blades,uint8_t length,uint16_t first)
{
    uint8_t i;
    mof_magic.write_count=0;
    for (i=0;i<mof_magic.old_count;++i) {
        const MofMagicTile *old=&mof_magic.old[i];
        if (i>=mof_magic.count || old->cell!=mof_magic.next[i].cell)
            visible_cell(old->cell,old->restore,blades,length);
    }
    for (i=0;i<mof_magic.count;++i) {
        const MofMagicTile *t=&mof_magic.next[i],*old=&mof_magic.old[i];
        mof_magic.upload[i]=i>=mof_magic.old_count || old->bank!=t->bank || old->address!=t->address;
        visible_cell(t->cell,first+i,blades,length);
    }
}
#endif
