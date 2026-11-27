enum { D=1,F=2,B=3,DF=4,DB=5 };
static const uint8_t spell_cost[SPELL_COUNT]={
    [TWIN_FIRE]=4, [MYAU]=4, [REST]=2, [GUARDIANS]=8
};

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
#ifdef MOF_ALIS_COMBAT
    else if (h[3]==DF && h[4]==F && h[5]==DF) gesture=G_DP;
    else if (h[4]==D && h[5]==F) gesture=G_QCF;
    else if (h[4]==D && h[5]==B) gesture=G_QCB;
#endif
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
    if (!move || move>=SPELL_COUNT || chapter.meter[p]<spell_cost[move]) return 0;
    if (move==REST) return d->fighters[p].life<100;
    if (move==CHAT) return !c->chat_wait && chapter.meter[p]<8;
    if (move==STUN) return !c->stun_used && d->fighters[p].life<=25 && chapter.meter[p]==8
        && d->fighters[1-p].state==MOF_DUEL_READY && !d->body[1-p].y_offset;
    if (move==GUARDIANS) return decisive(d,p) && mof_magic.caster[1-p].dizzy;
    if (move==TWIN_FIRE || move==MYAU || move==FIRE_TAP || move==FIRE_HOLD
#ifndef MOF_ALIS_COMBAT
        || move==SLASH
#endif
       )
        return !mof_magic.shots[p*2].ttl && !mof_magic.shots[p*2+1].ttl;
    return 1;
}
static void begin(uint8_t p,uint8_t move) {
    MofCaster *c=&mof_magic.caster[p];
    c->strain=0;c->age=0;c->move=move;c->window=0;c->pending=0;
#ifdef MOF_ALIS_CHOREOGRAPHY
    c->strain_window=0;
#endif
    chapter.meter[p]-=spell_cost[move];
    mof_magic.busy=1;
    ++mof_magic.events[p][move];
#ifdef MOF_ALIS_FEEDBACK
    if (move!=REST && move!=CHAT) mof_magic.audio=move;
    if (move==TWIN_FIRE || move==MYAU || move==GUARDIANS) {
        uint8_t duration=move==GUARDIANS ? 12 : 8;
        if (mof_feedback.duration<duration) mof_feedback.duration=duration;
        mof_feedback.participants|=1u<<p;
    }
#else
    mof_magic.audio=move;
#endif
    if (move==STUN) c->stun_used=1;
    if (move==CHAT) c->chat_wait=100;
}
static inline void input_player(const MofDuel *d,uint8_t p,uint8_t keys) {
    MofCaster *c=&mof_magic.caster[p];
    const MofDuelFighter *f=&d->fighters[p];
    uint8_t dir=direction(keys,f->face_right),buttons=keys&48,edge=buttons&~c->held_button;
    uint8_t move=0;
#ifdef MOF_ALIS_CHOREOGRAPHY
    uint8_t cancel=0;
#endif
    mof_magic.pad[p]=keys;mof_magic.locked[p]=0;
    if (d->hitstop) return;
    c->held_button=buttons;
    if (c->face!=f->face_right) {c->window=c->pending=0;c->previous=0;}
    c->face=f->face_right;
#ifdef MOF_ALIS_CHOREOGRAPHY
    if (f->state==MOF_DUEL_ATTACK && f->standing_normal==1u) {
        cancel=mof_magic.myau_cancel[p];
        if (cancel==1 && d->fighters[1-p].state!=MOF_DUEL_HIT) cancel=0;
    } else mof_magic.myau_cancel[p]=0;
    if (f->state!=MOF_DUEL_READY && !cancel) {
#else
    if (f->state!=MOF_DUEL_READY) {
#endif
        c->window=c->pending=c->move=c->pose=c->dizzy=0;
        c->previous=dir;
        return;
    }
    if (c->dizzy || c->move) {
        mof_magic.locked[p]=1;
        mof_magic.pad[p]=(c->move==SABER && c->age==3) ? MOF_DUEL_UP : 0;
#ifdef MOF_ALIS_CHOREOGRAPHY
        if (c->move==SABER && c->strain_window) mof_magic.pad[p]=0;
#endif
        c->previous=dir;
        return;
    }
    if (d->body[p].y_offset || d->body[p].jump_pending) {c->pending=c->window=0;return;}
    if (c->pending) {
#ifdef MOF_ALIS_CHOREOGRAPHY
        if (c->pending>=128) {
            if (!(buttons&16) || ++c->pending>=134) {
                begin(p,SABER);
                c->strain_window=(buttons&16)!=0;
            }
            mof_magic.pad[p]=0;mof_magic.locked[p]=1;return;
        }
#endif
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
#ifdef MOF_ALIS_CHOREOGRAPHY
    if (cancel && move!=MYAU) return;
#endif
    if ((move==GUARDIANS || move==STUN) && !armed(d,p,move)) {
        c->window=0;mof_magic.locked[p]=1;mof_magic.pad[p]=0;return;
    }
    if (move && armed(d,p,move)) {
        mof_magic.locked[p]=1;mof_magic.pad[p]=0;
        if (move==FIRE_TAP) {c->pending=1;c->window=0;mof_magic.busy=1;}
#ifdef MOF_ALIS_CHOREOGRAPHY
        else if (move==SABER) {c->pending=129;c->window=0;mof_magic.busy=1;}
        else if (move==MYAU && cancel) {
            mof_magic.myau_cancel[p]=2;
            begin(p,move);
        }
#endif
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
