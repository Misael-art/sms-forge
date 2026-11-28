/* Targeted thresholds and gameplay interactions. The live ROM replay covers the mapper and VDP. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../inc/alis_magic.h"
#include "../src/duel_roster.inc"

MofChapter chapter;
static MofDuel duel;
#include "../src/duel_ground.inc"
static const MofDuelGeometry body[2]={
    {{-10,-52,10,-2},{{0,-45,24,-15},{0,-45,24,-15}}},
    {{-10,-52,10,-2},{{0,-45,24,-15},{0,-45,24,-15}}}
};

uint8_t mof_magic_contact(MofDuel *d,uint8_t p,uint8_t damage,uint8_t flags)
{return mof_duel_effect_contact(d,p,damage,flags);}

static void reset(void)
{
    memset(&chapter,0,sizeof(chapter));
#ifdef MOF_ALIS_COMBAT
    memset(&mof_combat,0,sizeof(mof_combat));
#endif
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

static void combo_contacts(void)
{
    for (uint8_t owner=0;owner<2;++owner) {
        uint8_t v=1u-owner;
        reset();
        /* Overlapping projectiles give one accepted hit, even in a trade. */
        colliding_shot(0,owner,FIRE_TAP,6);
        colliding_shot(1,owner,FIRE_TAP,6);
        colliding_shot(2,v,FIRE_TAP,6);
        tick(0,0);
        assert(duel.fighters[v].combo_received==1 && duel.fighters[owner].combo_received==1);
        advance(MOF_DUEL_LIGHT_HITSTOP);
        colliding_shot(0,owner,FIRE_HOLD,10);
        tick(0,0);
        assert(duel.fighters[v].life==84 && duel.fighters[v].combo_received==2);
        advance(MOF_DUEL_HEAVY_HITSTOP);
        assert(duel.fighters[v].combo_received==2);
        advance(MOF_DUEL_HEAVY_HITSTUN);
        assert(!duel.fighters[v].combo_received && duel.fighters[v].state==MOF_DUEL_READY);
        colliding_shot(0,owner,FIRE_TAP,6);
        tick(owner ? MOF_DUEL_LEFT : 0, owner ? 0 : MOF_DUEL_RIGHT);
        assert(duel.fighters[v].state==MOF_DUEL_BLOCK && !duel.fighters[v].combo_received);
        reset();
        assert(!duel.fighters[0].combo_received && !duel.fighters[1].combo_received);
    }
}

#ifdef MOF_ALIS_CHOREOGRAPHY
static void choreography(void)
{
    uint8_t seen_fall=0,max_hits=0,second=0;
    reset();
    chapter.meter[0]=4;
    duel.fighters[0].x=100;
    duel.fighters[1].x=160;
    input(0,"dzb",MOF_DUEL_TWO);
    advance(145);
    assert(duel.fighters[1].life==84 && mof_magic.hits[0]==2);

    reset();
    chapter.meter[0]=4;
    duel.fighters[0].x=65;
    duel.fighters[1].x=199;
    input(0,"dzb",MOF_DUEL_TWO);
    advance(110);
    assert(duel.fighters[1].life==100 && !mof_magic.shots[0].ttl);

    reset();
    chapter.meter[0]=4;
    duel.fighters[0].x=100;
    duel.fighters[1].x=124;
    mof_duel_step_normal(&duel,0,0,1u,MOF_DUEL_NO_NORMAL);
    for (uint8_t n=0;n<20 && duel.fighters[1].life==100;++n) tick(0,0);
    assert(duel.fighters[1].life==90 && mof_magic.myau_cancel[0]==1);
    advance(duel.hitstop);
    input(0,"dzb",MOF_DUEL_TWO);
    for (uint8_t n=0;n<120;++n) {
        tick(0,0);
        if (duel.fighters[1].combo_received>max_hits) max_hits=duel.fighters[1].combo_received;
    }
    assert(duel.fighters[1].life==70 && max_hits==4);
    max_hits=0;

    reset();
    chapter.meter[0]=4;
    duel.fighters[0].x=duel.right_wall-24;
    duel.fighters[1].x=duel.right_wall;
    mof_duel_step_normal(&duel,0,MOF_DUEL_RIGHT,1u,MOF_DUEL_NO_NORMAL);
    for (uint8_t n=0;n<20 && duel.fighters[1].state!=MOF_DUEL_BLOCK;++n) tick(0,MOF_DUEL_RIGHT);
    assert(duel.fighters[1].state==MOF_DUEL_BLOCK && !mof_magic.myau_cancel[0]);
    while (duel.hitstop) tick(0,MOF_DUEL_RIGHT);
    input(0,"dzb",MOF_DUEL_TWO);
    assert(!mof_magic.events[0][MYAU] && chapter.meter[0]==4);

    reset();
    duel.fighters[0].x=100;
    duel.fighters[1].x=130;
    input(0,"fdx",MOF_DUEL_ONE);
    for (uint8_t n=0;n<16;++n) tick(MOF_DUEL_ONE|MOF_DUEL_RIGHT|MOF_DUEL_DOWN,0);
    for (uint8_t n=0;n<90;++n) {
        tick(0,0);
        if (duel.fighters[1].life==95 && duel.body[0].y_offset<0) second=1;
        if (duel.fighters[1].state==MOF_DUEL_FALL) seen_fall=1;
    }
    assert(duel.fighters[0].x>100 && duel.fighters[1].life==85);
    assert(seen_fall && second && mof_magic.hits[0]==2);

    reset();
    duel.fighters[0].x=100;
    duel.fighters[1].x=124;
    mof_magic.palma[0]=255;  /* arm at the same point as the round's super spend */
    mof_duel_step_normal(&duel,0,0,MOF_DUEL_SUPER,MOF_DUEL_NO_NORMAL);
    seen_fall=0;
    for (uint8_t n=0;n<150;++n) {
        tick(0,0);
        if (duel.fighters[1].combo_received>max_hits) max_hits=duel.fighters[1].combo_received;
        if (duel.fighters[1].state==MOF_DUEL_FALL) seen_fall=1;
    }
    assert(duel.fighters[1].life==73 && seen_fall);
#ifdef MOF_ALIS_COMBAT
    assert(max_hits==3);
#else
    assert(max_hits==4);
#endif
    assert(!mof_magic.palma[0] && duel.body[0].y_offset==0);

    reset();
    duel.fighters[0].x=duel.right_wall-24;
    duel.fighters[1].x=duel.right_wall;
    mof_magic.palma[0]=255;
    mof_duel_step_normal(&duel,0,MOF_DUEL_RIGHT,MOF_DUEL_SUPER,MOF_DUEL_NO_NORMAL);
    for (uint8_t n=0;n<90;++n) tick(0,MOF_DUEL_RIGHT);
    assert(duel.fighters[1].life==100 && !mof_magic.palma[0] && !mof_magic.hits[0]);
}
#endif

#ifdef MOF_ALIS_COMBAT
static void revised_combat(void)
{
    static const uint8_t ranges[]={24,60,90,134};
    static const uint8_t hp[]={80,84,90,100};
    for (uint8_t i=0;i<4;++i) {
        uint8_t fallen=0;
        reset();
        duel.fighters[0].x=100;
        duel.fighters[1].x=100+ranges[i];
        chapter.meter[0]=4;
        input(0,"dzb",MOF_DUEL_TWO);
        for (uint8_t n=0;n<135;++n) {
            tick(0,0);
            fallen|=duel.fighters[1].state==MOF_DUEL_FALL;
        }
        assert(duel.fighters[1].life==hp[i] && mof_magic.hits[0]==3u-i);
        assert(fallen==(i!=3u) && !mof_magic.shots[0].ttl);
        assert(i==3u || duel.fighters[1].x>100+ranges[i]);
    }
    for (uint8_t guard=0;guard<=2;++guard) {
        reset();
        duel.fighters[0].x=100;
        duel.fighters[1].x=126;
        input(0,"dxf",MOF_DUEL_ONE);
        for (uint8_t n=0;n<12;++n)
            tick(0,guard==1u ? MOF_DUEL_RIGHT|MOF_DUEL_DOWN :
                guard==2u && n<4u ? MOF_DUEL_UP : 0u);
        assert(duel.fighters[1].life==(guard==1u ? 98u : 83u));
        assert(duel.fighters[1].state==(guard==1u ? MOF_DUEL_BLOCK : MOF_DUEL_FALL));
    }
}

static void revised_movement(void)
{
    uint8_t apex[3]={0,0,0};
    for (uint8_t type=0;type<3;++type) {
        uint8_t prepare=0;
        reset();
        if (type==2u) for (uint8_t n=0;n<3;++n) tick(MOF_DUEL_DOWN,0);
        for (uint8_t n=0;n<70;++n) {
            uint8_t height;
            tick(n<(type ? 10u : 1u) ? MOF_DUEL_UP : 0u,0);
            height=(uint8_t)-duel.body[0].y_offset;
            if (duel.body[0].jump_pending && !height) ++prepare;
            if (height>apex[type]) apex[type]=height;
        }
        assert(prepare==3u && duel.body[0].y_offset==0u);
    }
    assert(apex[0]>0u && apex[0]<apex[1] && apex[1]<apex[2]);
    for (uint8_t type=0;type<3;++type) {
        uint8_t bounce=0,grounded=0,roll=0;
        reset();
        duel.fighters[0].x=100;
        duel.fighters[1].x=126;
        assert(mof_magic_contact(&duel,0,12,MOF_MOVE_HEAVY|MOF_EFFECT_FALL|
               (type==2u ? MOF_EFFECT_HARD : 0u))==MOF_DUEL_LANDED);
        for (uint8_t n=0;n<125;++n) {
            const MofDuelMotion *motion=&duel.body[1].motion;
            uint8_t key=type==1u && motion->vy>0 && motion->y+2*motion->vy>=0 ? MOF_DUEL_RIGHT : 0;
            tick(0,key);
            bounce+=duel.fighters[1].state==MOF_DUEL_FALL && mof_combat.fall[1]==MOF_COMBAT_BOUNCE;
            grounded+=duel.fighters[1].state==MOF_DUEL_DOWNED;
            roll|=mof_combat.fall[1]==MOF_COMBAT_ROLL;
        }
        if (!type) assert(bounce>=4u && bounce<=6u && grounded==28u && !roll);
        else if (type==1u) assert(!grounded && roll);
        else assert(!bounce && grounded==38u && !roll);
    }
}

static void revised_defense(void)
{
    for (uint8_t wait=3u;wait<=7u;wait+=4u) {
        reset();
        duel.fighters[0].state=MOF_DUEL_HIT;
        duel.fighters[0].state_since=duel.tick;
        duel.fighters[0].hit_duration=wait;
        mof_duel_step_normal(&duel,0,0,0,MOF_DUEL_NO_NORMAL);
        advance(wait-1u);
        assert(duel.fighters[0].state==(wait==3u ? MOF_DUEL_ATTACK : MOF_DUEL_READY));
        assert(!mof_combat.command_age[0]);
    }
    reset();
    duel.fighters[0].x=duel.right_wall-24u;
    duel.fighters[1].x=duel.right_wall;
    for (uint8_t i=0;i<4;++i) {
        uint8_t contact=0;
        mof_duel_step_normal(&duel,0,MOF_DUEL_RIGHT,1u,MOF_DUEL_NO_NORMAL);
        for (uint8_t n=0;n<12 && !contact;++n) {
            tick(0,MOF_DUEL_RIGHT);
            contact=duel.fighters[0].contact;
        }
        assert(contact==MOF_DUEL_GUARDED && duel.fighters[1].life==100u);
        assert(duel.fighters[1].state==(i<3u ? MOF_DUEL_BLOCK : MOF_DUEL_HIT));
        for (uint8_t n=0;n<35;++n) tick(0,MOF_DUEL_RIGHT);
    }
}
#endif

static void overlay_order(void)
{
    reset();
    mof_magic.old_count=mof_magic.count=2;
    mof_magic.old[0].cell=10;
    mof_magic.old[1].cell=20;
    mof_magic.next[0].cell=mof_magic.next[1].cell=20;
    mof_chapter_pnt.count=0;
    mof_magic_tiles(NULL,0,432,0);
    assert(mof_chapter_pnt.count==1 && mof_chapter_pnt.cells[0].address==0x7814);
    mof_magic.old[0].cell=mof_magic.old[1].cell=20;
    mof_magic.next[1].cell=21;
    mof_chapter_pnt.count=0;
    mof_magic_tiles(NULL,0,432,0);
    assert(mof_chapter_pnt.count==2);
    assert(mof_chapter_pnt.cells[0].tile==432 && mof_chapter_pnt.cells[1].tile==433);
    reset();
    colliding_shot(0,0,FIRE_HOLD,10);colliding_shot(2,1,FIRE_HOLD,10);
    tick(0,0);
    assert(duel.hitstop_target==(MOF_DUEL_HITSTOP_BOTH|MOF_DUEL_HITSTOP_SHAKE));
}

static void capabilities(void)
{
    static const MofCommand alternate[]={{REST,MOF_DUEL_TWO,G_BACK_BACK}};
    static const MofCommand duplicate[]={{REST,MOF_DUEL_TWO,G_QCF},{CHAT,MOF_DUEL_TWO,G_QCF}};
    MofFighterDef other=mof_fighter_alis;
    const MofFighterDef *pair[MOF_DUEL_FIGHTER_IDS]={&other,&mof_fighter_alis};
    other.gestures=duplicate;other.gesture_count=2;
    assert(mof_duel_init_pair(&duel,body,6,MOF_DUEL_HAYATO,MOF_DUEL_ALIS,32,224,16,239,24));
    assert(!mof_duel_set_roster(&duel,pair));
    other.gestures=alternate;other.gesture_count=1;
    assert(mof_duel_set_roster(&duel,pair));
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
    reset();
    chapter.meter[0]=8;duel.fighters[0].life=25;
    mof_magic.caster[1].move=REST;mof_magic.caster[1].age=15;
    duel.fighters[1].life=70;
    input(0,"fbf",16);advance(30);
    assert(!mof_magic.caster[1].move && duel.fighters[1].life==70);
}

/* Compare every ground-control pair to the full solver, including the
   pre-walk hurt box retained for projectiles and both arena limits. */
static void ground_equivalence(void)
{
    unsigned one,two,layout;
    for (layout=0;layout<4;++layout) {
        reset();
        duel.fighters[0].x=layout&1 ? duel.right_wall : duel.left_wall;
        duel.fighters[1].x=layout&1 ? duel.left_wall : duel.right_wall;
        if (layout&2) duel.fighters[1].x=duel.fighters[0].x+(layout&1 ? -duel.minimum_gap : duel.minimum_gap);
        for (one=0;one<64;++one) for (two=0;two<64;++two) {
            MofDuel initial=duel,expected;
#ifdef MOF_ALIS_COMBAT
            MofCombat combat_initial=mof_combat;
#endif
            for (unsigned settle=0;settle<6;++settle)
                mof_duel_step_normal(&duel,one&2,two&2,MOF_DUEL_NO_NORMAL,MOF_DUEL_NO_NORMAL);
            MofDuel start=duel;
#ifdef MOF_ALIS_COMBAT
            MofCombat combat_start=mof_combat;
#endif
            mof_duel_step_normal(&duel,one,two,MOF_DUEL_NO_NORMAL,MOF_DUEL_NO_NORMAL);
            expected=duel;
            duel=start;
#ifdef MOF_ALIS_COMBAT
            mof_combat=combat_start;
#endif
            if (ground_step(one,two)) assert(memcmp(&duel,&expected,sizeof(duel))==0);
            duel=initial;
#ifdef MOF_ALIS_COMBAT
            mof_combat=combat_initial;
#endif
        }
    }
}

/* Walk the canonical timeline of every grounded normal into hit, guard
   and recovery, testing the fast step from each identical snapshot. */
static void ground_reactions(void)
{
    unsigned action, defender, frame, k;
    const uint8_t controls[]={0,2,4,8,6,10,16,32,18,34,20,40,1};
    for (action=0;action<MOF_DUEL_AIR_NORMALS;++action) {
        for (defender=0;defender<2;++defender) {
            uint8_t low=action>=MOF_DUEL_LOW_NORMALS ? MOF_DUEL_DOWN : 0;
            uint8_t guard=defender ? MOF_DUEL_RIGHT|low : 0;
            reset();
            duel.fighters[1].x=duel.fighters[0].x+24;
            for (frame=0;frame<5;++frame)
                mof_duel_step_normal(&duel,low,guard,MOF_DUEL_NO_NORMAL,MOF_DUEL_NO_NORMAL);
            mof_duel_step_normal(&duel,low,guard,action,MOF_DUEL_NO_NORMAL);
            for (frame=0;frame<45;++frame) {
                MofDuel original=duel;
#ifdef MOF_ALIS_COMBAT
                MofCombat combat_original=mof_combat;
#endif
                for (k=0;k<sizeof(controls);++k) {
                    uint8_t one=controls[k],two=controls[(frame+k)%sizeof(controls)];
                    MofDuel expected;
                    duel=original;
#ifdef MOF_ALIS_COMBAT
                    mof_combat=combat_original;
#endif
                    mof_duel_step_normal(&duel,one,two,MOF_DUEL_NO_NORMAL,MOF_DUEL_NO_NORMAL);
                    expected=duel;
                    duel=original;
#ifdef MOF_ALIS_COMBAT
                    mof_combat=combat_original;
#endif
                    if (ground_step(one,two)) assert(!memcmp(&duel,&expected,sizeof(duel)));
                }
                duel=original;
#ifdef MOF_ALIS_COMBAT
                mof_combat=combat_original;
#endif
                mof_duel_step_normal(&duel,low,guard,MOF_DUEL_NO_NORMAL,MOF_DUEL_NO_NORMAL);
            }
        }
    }
}

#ifdef MOF_ALIS_COMBAT
static void guardians_landing_projection(void)
{
    for (uint8_t player=0;player<2;++player) {
        for (uint8_t at_wall=0;at_wall<2;++at_wall) {
            reset();
            MofDuelFighter *falling=&duel.fighters[player];
            MofDuelBody *body=&duel.body[player];
            if (at_wall) falling->x=falling->face_right ? duel.left_wall : duel.right_wall;
            falling->life=0;
            falling->state=MOF_DUEL_FALL;
            body->y_offset=-29;
            body->motion.y=-29*MOF_MOTION_UNIT;
            body->motion.vy=18;
            body->motion.vx=falling->face_right ? -40 : 40;
            body->motion.mode=MOF_MOTION_AIR;
            mof_combat.cutscene_return=1;
            mof_combat.fall[player]=MOF_COMBAT_HARD;
            const uint8_t predicted=mof_combat_landing_x(&duel,player);
            for (uint8_t tick=0;tick<30 && falling->state==MOF_DUEL_FALL;++tick)
                mof_duel_step_normal(&duel,0,0,MOF_DUEL_NO_NORMAL,MOF_DUEL_NO_NORMAL);
            assert(falling->state==MOF_DUEL_DOWNED && falling->x==predicted);
        }
    }
}
#endif

int main(void)
{
#ifdef MOF_ALIS_COMBAT
    revised_combat();
    revised_movement();
    revised_defense();
    guardians_landing_projection();
#endif
    combo_contacts();
    unsigned p;
    ground_equivalence();ground_reactions();overlay_order();capabilities();
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
    mof_duel_hurt_box(&duel,1,&duel.tested_hurt[1]);
    duel.tested_hurt_x[1]=duel.fighters[1].x;
    for (int n=0;n<75;++n){mof_magic.live_step=1;mof_magic_step(&duel);}
    assert(mof_magic.full_range==2);
    reset();duel.fighters[0].x=80;duel.fighters[1].x=155;
#ifdef MOF_ALIS_COMBAT
    input(0,"d-d",16);
    for (uint8_t n=0;n<8;++n) tick(16,0);
    advance(7);input(1,"dzb",16);advance(65);
#else
    input(0,"dxf",16);advance(13);input(1,"dzb",16);advance(65);
#endif
    assert(mof_magic.reflects[1]==1 && mof_magic.hits[1]==1 && duel.fighters[0].life==90);
    reset();chapter.meter[0]=4;duel.fighters[1].x=67;
    input(0,"dzb",32);advance(20);assert(mof_magic.shots[0].age>9);
    advance(85);
#ifdef MOF_ALIS_CHOREOGRAPHY
    assert(mof_magic.hits[0]==3 && duel.fighters[1].life==80);
    choreography();
#else
    assert(mof_magic.hits[0]==1 && duel.fighters[1].life==82);
#endif
    puts("thresholds, both facings, full-range curves, heal interruption, Chat cooldown, reflection and Myau passed");
    return 0;
}
