/* Targeted thresholds and gameplay interactions. The live ROM replay covers the mapper and VDP. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../inc/alis_magic.h"
#include "../src/duel_roster.inc"

MofChapter chapter;
static MofDuel duel;
static const MofDuelGeometry body[2]={
    {{-10,-52,10,-2},{{0,-45,24,-15},{0,-45,24,-15}}},
    {{-10,-52,10,-2},{{0,-45,24,-15},{0,-45,24,-15}}}
};
void mof_magic_hurt(const MofDuel *d,uint8_t p,MofDuelBox *box){mof_duel_hurt_box(d,p,box);}

uint8_t mof_magic_contact(MofDuel *d,uint8_t p,uint8_t damage,uint8_t flags)
{return mof_duel_effect_contact(d,p,damage,flags);}

static void reset(void)
{
    memset(&chapter,0,sizeof(chapter));
    chapter.target=2;chapter.phase=MOF_PLAY;
    assert(mof_duel_init_pair(&duel,body,6,MOF_DUEL_ALIS,MOF_DUEL_ALIS,32,224,16,239,24));
    assert(mof_duel_set_roster(&duel,mof_roster));
    mof_magic_reset();
}
static void tick(uint8_t a,uint8_t b)
{
    mof_magic_input(&duel,a,b);
    mof_duel_step_normal(&duel,mof_magic.pad[0],mof_magic.pad[1],255,255);
    mof_magic_step(&duel);
}
static void advance(unsigned n){while(n--) tick(0,0);}
static void input(unsigned p,const char *gesture,uint8_t button)
{
    unsigned f=duel.fighters[p].face_right ? 8 : 4,b=f^12;
    for (;*gesture;++gesture) {
        uint8_t k=*gesture=='d' ? 2 : *gesture=='f' ? f : *gesture=='b' ? b :
                  *gesture=='x' ? f|2 : *gesture=='z' ? b|2 : 0;
        if (!gesture[1]) k|=button;
        tick(p ? 0 : k,p ? k : 0);
    }
}
static void finisher(unsigned p,unsigned attacker,unsigned rival,unsigned reiki,unsigned wins,unsigned dizzy,unsigned eligible)
{
    unsigned v=1-p;
    reset();
    duel.fighters[p].life=attacker;duel.fighters[v].life=rival;
    chapter.meter[p]=reiki;chapter.wins[p]=wins;mof_magic.caster[v].dizzy=dizzy;
    input(p,"dxfdxf",32);
    assert(mof_magic.events[p][GUARDIANS]==eligible);
    assert(chapter.meter[p]==(eligible ? 0 : reiki));
    advance(46);assert(mof_magic.finisher==(eligible ? p+1 : 0));
    if (eligible) assert(!duel.fighters[v].life && mof_magic.target_fighter==MOF_DUEL_ALIS);
}

static void colliding_shot(uint8_t slot,uint8_t owner,uint8_t kind,uint8_t damage)
{
    MofShot *shot=&mof_magic.shots[slot];
    shot->owner=owner;
    shot->kind=kind;
    shot->ttl=12;
    shot->x=duel.fighters[1-owner].x;
    shot->y=111;
    shot->damage=damage;
}

/* Two sources for one owner, one for the other. Swap both sides and
   shot slots. The airborne projectile survives its owner's interruption. */
static void trade(uint8_t attacker,uint8_t reverse)
{
    uint8_t v=1-attacker, first=reverse ? 3 : 0;
    reset();
    colliding_shot(first,attacker,FIRE_TAP,6);
    colliding_shot(1,attacker,FIRE_HOLD,10);
    colliding_shot(3-first,v,FIRE_TAP,6);
    mof_magic.caster[v].chat_wait=17;
    tick(0,0);
    assert(duel.fighters[attacker].life==94 && duel.fighters[v].life==90);
    assert(mof_magic.hits[0]==1 && mof_magic.hits[1]==1);
    assert(duel.hitstop==MOF_DUEL_HEAVY_HITSTOP);
    assert(duel.hitstop_target==(v|MOF_DUEL_HITSTOP_SHAKE));
    assert(duel.fighters[attacker].hit_duration==MOF_DUEL_LIGHT_HITSTUN);
    assert(duel.fighters[v].hit_duration==MOF_DUEL_HEAVY_HITSTUN);
    for (uint8_t age=MOF_DUEL_HEAVY_HITSTOP;age;--age) {
        tick(0,0);
        assert(duel.hitstop==age-1 && !duel.fighters[0].contact && !duel.fighters[1].contact);
        assert(mof_magic.caster[v].chat_wait==16 && !mof_magic.effect_mask);
    }
    tick(0,0);
    assert(mof_magic.caster[v].chat_wait==15);
}

static void capabilities(void)
{
    static const MofCommand alternate[]={{REST,MOF_DUEL_TWO,G_BACK_BACK}};
    MofFighterDef other=mof_fighter_alis;
    reset();
    other.gestures=alternate;
    other.gesture_count=1;
    duel.fighters[0].def=&other;
    duel.fighters[0].life=80;
    chapter.meter[0]=2;
    input(0,"d-d",16);advance(25);
    assert(!mof_magic.events[0][FIRE_TAP]);
    input(0,"b-b",32);advance(29);
    assert(duel.fighters[0].life==86 && chapter.meter[0]==0);
    reset();
    duel.fighters[0].fighter=MOF_DUEL_HAYATO;
    input(0,"d-d",16);advance(8);
    assert(mof_magic.events[0][FIRE_TAP]);
    reset();
    duel.fighters[0].def=&other;
    duel.fighters[0].life=25;chapter.meter[0]=8;
    input(0,"fbf",16);
    assert(mof_magic.caster[1].dizzy);
}

int main(void)
{
    unsigned p;
    capabilities();
    for (p=0;p<2;++p) {
        trade(p,0);trade(p,1);
        reset();
        duel.fighters[p].contact=MOF_DUEL_LANDED;
        assert(!mof_magic_contact(&duel,p,10,MOF_MOVE_HEAVY));
        assert(duel.fighters[1-p].life==100);
        reset();
        duel.fighters[1-p].guarding=MOF_GUARD_STANDING;
        assert(mof_magic_contact(&duel,p,10,MOF_MOVE_HEAVY)==MOF_DUEL_GUARDED);
        assert(duel.hitstop_target==1-p && duel.fighters[1-p].life==100);
        finisher(p,25,24,8,1,84,1);
        finisher(p,26,24,8,1,84,0);
        finisher(p,25,25,8,1,84,0);
        finisher(p,25,24,7,1,84,0);
        finisher(p,25,24,8,0,84,0);
        finisher(p,25,24,8,1,0,0);
        reset();duel.fighters[p].life=25;chapter.meter[p]=8;
        input(p,"fbf",16);assert(mof_magic.caster[1-p].dizzy && chapter.meter[p]==8);
        advance(90);input(p,"fbf",16);assert(mof_magic.events[p][STUN]==1 && !mof_magic.caster[1-p].dizzy);
        reset();duel.fighters[p].life=98;chapter.meter[p]=2;
        input(p,"d-d",32);advance(23);assert(duel.fighters[p].life==100 && chapter.meter[p]==0);
        reset();duel.fighters[p].life=80;chapter.meter[p]=2;
        input(p,"d-d",32);duel.fighters[p].state=MOF_DUEL_HIT;
        duel.fighters[p].hit_duration=10;advance(34);assert(duel.fighters[p].life==80);
        reset();input(p,"b-b",32);advance(35);input(p,"b-b",32);advance(30);
        assert(chapter.meter[p]==1 && mof_magic.events[p][CHAT]==1);
        reset();input(p,"d-d",16);advance(8);
        assert(mof_magic.shots[p*2].ttl>0 && mof_magic.events[p][FIRE_TAP]==1);
        advance(30);input(p,"d-d",16);
        for (int n=0;n<7;++n) tick(p ? 0 : 16,p ? 16 : 0);
        advance(10);assert(mof_magic.events[p][FIRE_HOLD]==1 && mof_magic.shots[p*2].ttl>12);
    }
    reset();chapter.meter[0]=4;input(0,"dxf",48);advance(14);
    assert(mof_magic.shots[0].ttl && mof_magic.shots[1].ttl);
    assert(mof_magic.shots[0].y!=mof_magic.shots[1].y);
    /* Place a genuinely airborne target above both arcs. The simulation fixture
       preserves its position to measure the maximum reach free of any contact. */
    duel.body[1].motion.mode=MOF_MOTION_AIR;duel.body[1].y_offset=-88;
    for (int n=0;n<75;++n){mof_magic.live_step=1;mof_magic_step(&duel);}
    assert(mof_magic.full_range==2);
    reset();duel.fighters[0].x=80;duel.fighters[1].x=155;
    input(0,"dxf",16);advance(13);input(1,"dzb",16);advance(65);
    assert(mof_magic.reflects[1]==1 && mof_magic.hits[1]==1 && duel.fighters[0].life==90);
    reset();chapter.meter[0]=4;duel.fighters[1].x=67;
    input(0,"dzb",32);advance(20);assert(mof_magic.shots[0].age>9);
    advance(45);assert(mof_magic.hits[0]==1 && duel.fighters[1].life==82);
    puts("thresholds, both facings, full-range curves, heal interruption, Chat cooldown, reflection and Myau passed");
    return 0;
}
