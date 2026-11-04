/* COPIADO de tools/mugen2sgdk_forge/runtime/mg_char.c (v0.3.3). Edite na fonte. */
/* mg_char.c -- personagem: estados/controladores MUGEN, animacao, fisica, comandos. */
#include "mg/mg_runtime.h"
#include "mg/mg_ops.h"
#ifdef MG_FX_TRACE
#include "game_vars.h"
#include "system/runtime_probe.h"
#endif
#ifdef MG_COMMAND_GAP_COUNTERS
#include "core/app.h"
#include "system/diagnostic_sram_layout.h"
#endif

#define FXI(v) ((mgfx)(v) << MG_FX_SHIFT)
#ifdef MG_PARAM_LITERAL_INLINE
/* Parameters retain their original bytecode offsets. A literal has no trigger
 * or RNG side effect; decode it here instead of two evaluator calls. Every
 * other program still goes through the canonical native/VM dispatcher. */
static inline __attribute__((always_inline)) mgfx param_value(const MgPlayer *p, u16 off)
{
    if (off == MG_NONE) return 0;
    const u8 *b = p->sdef->code + off;
    if (b[0] == MG_OP_PUSH8 && b[2] == MG_OP_END)
        return (mgfx)((u32)(s32)(s8)b[1] << MG_FX_SHIFT);
    if (b[0] == MG_OP_PUSH16 && b[3] == MG_OP_END)
        return (mgfx)((u32)(s32)(s16)(((u16)b[1] << 8) | b[2]) << MG_FX_SHIFT);
    if (b[0] == MG_OP_PUSHFX && b[5] == MG_OP_END)
        return (mgfx)(((u32)b[1] << 24) | ((u32)b[2] << 16) | ((u32)b[3] << 8) | b[4]);
    return MG_eval(p, off);
}

static inline __attribute__((always_inline)) s32 param_int(const MgPlayer *p, u16 off, s32 dflt)
{
    if (off == MG_NONE) return dflt;
    return param_value(p, off) >> MG_FX_SHIFT;
}
#define EVAL_VALUE(p, off) param_value((p), (off))
#define EVAL_INT(p, off, d) param_int((p), (off), (d))
#else
#define EVAL_VALUE(p, off) MG_eval((p), (off))
#define EVAL_INT(p, off, d) MG_evalInt((p), (off), (d))
#endif
#define PARAM(p, c, i) ((p)->sdef->param_offs[(c)->params + (i)])
#define HAS(p, c, i) (PARAM(p, c, i) != MG_NONE)
#define PV(p, c, i) EVAL_VALUE((p), PARAM(p, c, i))
#define PIV(p, c, i, d) EVAL_INT((p), PARAM(p, c, i), (d))
#define HIST(p, t) ((p)->hist[((p)->hist_head - (t)) & (MG_INPUT_HIST - 1)])
#define SYM(p, c, i) ((p)->sdef->syms[(c)->sym + (i)])

#ifdef MG_UPDATE_DETAIL_PROFILE
#define MG_LOGIC_DETAIL_BEGIN(active, tick) do { if (active) (tick) = getSubTick(); } while (0)
#define MG_INPUT_DETAIL_MARK(active, side, phase, tick) do { \
    if (active) { \
        const u32 inputDetailNow = getSubTick(); \
        mg_fight_update_detail.input_phase_ticks[(side)][(phase)] += inputDetailNow - (tick); \
        (tick) = inputDetailNow; \
    } \
} while (0)
#define MG_LOGIC_DETAIL_MARK(active, tick, player, phase) do { \
    if (active) { \
        const u32 logicDetailNow = getSubTick(); \
        MG_fightUpdateDetailRecordLogic((player)->side, (phase), logicDetailNow - (tick)); \
        (tick) = logicDetailNow; \
    } \
} while (0)
#define MG_NEGATIVE_DETAIL_BEGIN(active, tick) do { if (active) (tick) = getSubTick(); } while (0)
#define MG_NEGATIVE_DETAIL_MARK(active, tick, player, phase) do { \
    if (active) { \
        const u32 negativeDetailNow = getSubTick(); \
        MG_fightUpdateDetailRecordNegative((player)->side, (phase), negativeDetailNow - (tick)); \
        (tick) = negativeDetailNow; \
    } \
} while (0)
#else
#define MG_LOGIC_DETAIL_BEGIN(active, tick) do { } while (0)
#define MG_INPUT_DETAIL_MARK(active, side, phase, tick) do { } while (0)
#define MG_LOGIC_DETAIL_MARK(active, tick, player, phase) do { } while (0)
#define MG_NEGATIVE_DETAIL_BEGIN(active, tick) do { } while (0)
#define MG_NEGATIVE_DETAIL_MARK(active, tick, player, phase) do { } while (0)
#endif

/* ------------------------------------------------------------------ busca */
s16 MG_findAnim(const MgCharDef *d, s16 id)
{
    s16 lo = 0, hi = d->nanims - 1;
    while (lo <= hi) {
        s16 mid = (lo + hi) >> 1;
        s16 v = d->anims[mid].id;
        if (v == id) return mid;
        if (v < id) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
}

s16 MG_findState(const MgCharDef *d, s16 id)
{
    s16 lo = 0, hi = d->nstates - 1;
    while (lo <= hi) {
        s16 mid = (lo + hi) >> 1;
        s16 v = d->states[mid].id;
        if (v == id) return mid;
        if (v < id) lo = mid + 1; else hi = mid - 1;
    }
    return -1;
}

/* ------------------------------------------------------------------ animacao */
/* Tempo acumulado ate o LoopStart. O laco seguinte comeca aqui, nao em 0, quando LoopStart > 0. */
static s32 anim_loop_base(const MgCharDef *d, u16 anim_idx)
{
    const MgAnim *a = &d->anims[anim_idx];
    const MgAnimFrame *ff = &d->frames[a->first];
    u8 n = a->loopstart < a->count ? a->loopstart : 0;
    s32 t = 0;
    for (u8 i = 0; i < n; i++) t += ff[i].time < 0 ? 0 : ff[i].time;
    return t;
}

/* Elemento com tempo 0 nao ocupa tick: o quadro nao aparece. Nao mexe no contador bruto. */
static void skip_zero_elems(const MgCharDef *d, u16 anim_idx, u8 *elem)
{
    const MgAnim *a = &d->anims[anim_idx];
    const MgAnimFrame *ff = &d->frames[a->first];
    for (u8 guard = 0; guard < a->count && ff[*elem].time == 0; guard++) {
        (*elem)++;
        if (*elem >= a->count)
            *elem = a->loopstart < a->count ? a->loopstart : 0;
    }
}

void MG_changeAnim(MgPlayer *p, s16 anim, u8 elem1)
{
    s16 idx = MG_findAnim(p->def, anim);
    if (idx < 0) return;                      /* MUGEN tambem ignora anim inexistente */
    const MgAnim *a = &p->def->anims[idx];
    const MgAnimFrame *f = &p->def->frames[a->first];
    if (elem1 < 1) elem1 = 1;
    if (elem1 > a->count) elem1 = a->count;
    p->anim_idx = idx;
    p->anim_id = anim;
    p->elem = elem1 - 1;
    p->elem_time = 0;
    p->anim_time = 0;
    for (u8 i = 0; i < p->elem; i++) p->anim_time += f[i].time < 0 ? 0 : f[i].time;
    skip_zero_elems(p->def, idx, &p->elem);
}

static void anim_step(u16 *anim_idx, u8 *elem, s16 *elem_time, s32 *anim_time, const MgCharDef *d)
{
    const MgAnim *a = &d->anims[*anim_idx];
    const MgAnimFrame *ff = &d->frames[a->first];
    /* Contador bruto e quadro andam separados. O bruto permanece em `total` no tick em que
       AnimTime = 0; so o passo seguinte volta ao LoopStart e soma 1. O quadro volta no passo
       em que a duracao do elemento acaba. */
    if (a->total >= 0 && *anim_time >= a->total)
        *anim_time = anim_loop_base(d, *anim_idx);
    if (*elem >= a->count)
        *elem = a->loopstart < a->count ? a->loopstart : 0;
    const MgAnimFrame *f = &ff[*elem];
    (*elem_time)++;
    (*anim_time)++;
    if (f->time >= 0 && *elem_time >= f->time) {
        *elem_time = 0;
        (*elem)++;
        if (*elem >= a->count)
            *elem = a->loopstart < a->count ? a->loopstart : 0;
        skip_zero_elems(d, *anim_idx, elem);
    }
}

void MG_animAdvance(MgPlayer *p)
{
    anim_step(&p->anim_idx, &p->elem, &p->elem_time, &p->anim_time, p->def);
}

/* ------------------------------------------------------------------ estados */
void MG_changeState(MgPlayer *p, s16 no, s16 ctrl, s16 anim)
{
    s16 idx = MG_findState(p->sdef, no);
    if (idx < 0 && p->sdef != p->def) {            /* estado nao existe no dono: volta ao proprio */
        p->sdef = p->def;
        idx = MG_findState(p->def, no);
    }
    if (idx < 0) idx = MG_findState(p->sdef, 0);  /* estado inexistente: MUGEN tambem cai no 0 */
    if (idx < 0) return;
    const MgState *s = &p->sdef->states[idx];
    /* Contadores persistentes pertencem a uma entrada de estado. Limpar o destino
       cobre reentrada, retorno de custom state e ChangeState para o mesmo numero. */
    for (u8 k = 0; k < s->npersist; k++) {
        u16 slot = (u16)s->persist_first + k;
        if (slot < MG_MAX_PERSIST_SLOTS) p->persist_count[slot] = 0;
    }
    p->prevstateno = p->stateno;
    p->stateno = s->id;
    p->state_idx = idx;
    p->time = 0;
    p->state_changed = 1;
    if (s->statetype != 'U') p->statetype = s->statetype;
    if (s->movetype != 'U') p->movetype = s->movetype;
    if (s->physics != 'U') p->physics = s->physics;
    if (!(s->flags & 2)) p->hitdef_active = 0;
    if (!(s->flags & 4)) { p->movecontact = p->movehit = p->moveguarded = 0; }
    if (!(s->flags & 8)) p->hitcount = 0;
    p->attackdist = 0;
    if (s->p_ctrl != MG_NONE) p->ctrl = EVAL_INT(p, s->p_ctrl, p->ctrl) ? 1 : 0;
    if (ctrl >= 0) p->ctrl = ctrl ? 1 : 0;
    if (s->p_velx != MG_NONE) p->vx = EVAL_VALUE(p, s->p_velx);
    if (s->p_vely != MG_NONE) p->vy = EVAL_VALUE(p, s->p_vely);
    if (s->p_poweradd != MG_NONE) p->power += EVAL_INT(p, s->p_poweradd, 0);
    if (s->p_sprpriority != MG_NONE) p->sprpriority = EVAL_INT(p, s->p_sprpriority, 0);
    if (s->p_juggle != MG_NONE) p->juggle = EVAL_INT(p, s->p_juggle, 0);
    if (anim >= 0) MG_changeAnim(p, anim, 1);
    else if (s->p_anim != MG_NONE) MG_changeAnim(p, EVAL_INT(p, s->p_anim, p->anim_id), 1);
    if ((s->flags & 1) && p->enemy && MG_FACE(p->enemy->x - p->x, p->facing) < 0) p->facing = -p->facing;
    if (p->power < 0) p->power = 0;
    if (p->power > MG_POWERMAX(p)) p->power = MG_POWERMAX(p);
}

/* ------------------------------------------------------------------ hitdef */
/* Consumers may provide one strong policy definition; keep VM and native
 * HitDefs on the same hook without changing explicit spark symbols. */
s16 __attribute__((weak)) MG_resolveDefaultSpark(const MgPlayer *p, bool guard)
{
    return guard ? p->def->consts->guard_sparkno : p->def->consts->sparkno;
}

static void read_hitdef(MgPlayer *p, const MgCtrl *c, u8 base, MgHitDef *h)
{
    #define HP(n, d) PIV(p, c, base + MG_P_HITDEF_##n, d)
    #define HF(n, d) (HAS(p, c, base + MG_P_HITDEF_##n) ? PV(p, c, base + MG_P_HITDEF_##n) : (d))
    h->damage = HP(DAMAGE_X, 0);
    h->guard_damage = HP(DAMAGE_Y, 0);
    h->pause_p1 = HP(PAUSETIME_X, 0);
    h->pause_p2 = HP(PAUSETIME_Y, 0);
    h->gpause_p1 = HP(GUARD_PAUSETIME_X, h->pause_p1);
    h->gpause_p2 = HP(GUARD_PAUSETIME_Y, h->pause_p2);
    h->hittime = HP(GROUND_HITTIME, 0);
    h->slidetime = HP(GROUND_SLIDETIME, 0);
    h->ghittime = HP(GUARD_HITTIME, h->slidetime);
    h->gslidetime = HP(GUARD_SLIDETIME, h->ghittime);
    h->gctrltime = HP(GUARD_CTRLTIME, h->gslidetime);
    h->airhittime = HP(AIR_HITTIME, 20);
    h->gvel_x = HF(GROUND_VELOCITY_X, 0);
    h->gvel_y = HF(GROUND_VELOCITY_Y, 0);
    h->avel_x = HF(AIR_VELOCITY_X, 0);
    h->avel_y = HF(AIR_VELOCITY_Y, 0);
    h->down_vx = HF(DOWN_VELOCITY_X, h->avel_x);
    h->down_vy = HF(DOWN_VELOCITY_Y, h->avel_y);
    h->down_hittime = HP(DOWN_HITTIME, 20);
    h->guardvel_x = HF(GUARD_VELOCITY, h->gvel_x);
    h->fall = HP(FALL, 0) != 0;
    h->airfall = HP(AIR_FALL, h->fall) != 0;
    h->fall_recover = HP(FALL_RECOVER, 1) != 0;
    h->fall_yvel = HF(FALL_YVELOCITY, -(9 * MG_FX) / 2);
    h->fall_xvel = HF(FALL_XVELOCITY, h->avel_x);
    h->spark_x = HP(SPARKXY_X, 0);
    h->spark_y = HP(SPARKXY_Y, 0);
    h->p1stateno = HP(P1STATENO, -1);
    h->p2stateno = HP(P2STATENO, -1);
    h->getpower = HP(GETPOWER, h->damage);
    h->givepower = HP(GIVEPOWER, h->damage / 2);
    h->yaccel = HF(YACCEL, (35 * MG_FX) / 100);
    h->id = HP(ID, 0);
    h->chainid = HP(CHAINID, -1);
    h->kill = HP(KILL, 1) != 0;
    h->guard_kill = HP(GUARD_KILL, 1) != 0;
    #undef HP
    #undef HF
    h->attr = SYM(p, c, MG_S_HITDEF_ATTR);
    h->hitflag = SYM(p, c, MG_S_HITDEF_HITFLAG);
    h->guardflag = SYM(p, c, MG_S_HITDEF_GUARDFLAG);
    h->animtype = SYM(p, c, MG_S_HITDEF_ANIMTYPE);
    h->air_animtype = SYM(p, c, MG_S_HITDEF_AIR_ANIMTYPE);
    h->groundtype = SYM(p, c, MG_S_HITDEF_GROUND_TYPE);
    h->airtype = SYM(p, c, MG_S_HITDEF_AIR_TYPE);
    h->priority = SYM(p, c, MG_S_HITDEF_PRIORITY);
    h->hitsound = SYM(p, c, MG_S_HITDEF_HITSOUND);
    h->guardsound = SYM(p, c, MG_S_HITDEF_GUARDSOUND);
    h->sparkno = SYM(p, c, MG_S_HITDEF_SPARKNO);
    h->guard_sparkno = SYM(p, c, MG_S_HITDEF_GUARD_SPARKNO);
    if (h->sparkno == -2) h->sparkno = MG_resolveDefaultSpark(p, FALSE);
    if (h->guard_sparkno == -2) h->guard_sparkno = MG_resolveDefaultSpark(p, TRUE);
}

#define PROJ_HD_BASE (MG_P_PROJECTILE_DAMAGE_X - MG_P_HITDEF_DAMAGE_X)

static void spawn_projectile(MgPlayer *p, const MgCtrl *c)
{
    MgProj *pr = 0;
    for (u8 i = 0; i < MG_MAX_PROJ; i++) if (!p->proj[i].active) { pr = &p->proj[i]; break; }
    if (!pr) return;                              /* limite do pool: registrado no README */
    MgDraw keep = pr->dr;                         /* preserva sprites SGDK (evita vazamento do pool) */
    memset(pr, 0, sizeof(*pr));
    pr->dr = keep;
    pr->id = PIV(p, c, MG_P_PROJECTILE_PROJID, 0);
    pr->anim_id = PIV(p, c, MG_P_PROJECTILE_PROJANIM, 0);
    pr->hitanim = PIV(p, c, MG_P_PROJECTILE_PROJHITANIM, -1);
    pr->remanim = PIV(p, c, MG_P_PROJECTILE_PROJREMANIM, pr->hitanim);
    s16 idx = MG_findAnim(p->def, pr->anim_id);
    if (idx < 0) return;
    pr->anim_idx = idx;
    pr->facing = p->facing;
    pr->x = p->x + MG_FACE(PV(p, c, MG_P_PROJECTILE_OFFSET_X), p->facing);
    pr->y = p->y + PV(p, c, MG_P_PROJECTILE_OFFSET_Y);
    pr->vx = PV(p, c, MG_P_PROJECTILE_VELOCITY_X);
    pr->vy = PV(p, c, MG_P_PROJECTILE_VELOCITY_Y);
    pr->ax = PV(p, c, MG_P_PROJECTILE_ACCEL_X);
    pr->ay = PV(p, c, MG_P_PROJECTILE_ACCEL_Y);
    pr->removetime = PIV(p, c, MG_P_PROJECTILE_PROJREMOVETIME, -1);
    pr->hits = PIV(p, c, MG_P_PROJECTILE_PROJHITS, 1);
    pr->contact_time = -1;
    read_hitdef(p, c, PROJ_HD_BASE, &pr->hd);
    pr->active = 1;
}

s16 MG_numHelper(u8 side, s16 id)
{
    s16 n = 0;
    for (u8 k = 0; k < MG_MAX_HELPERS; k++)
        if (mg_fight.helper_active[side][k] && (id <= 0 || mg_fight.helper[side][k].helper_id == id)) n++;
    return n;
}

void MG_readReversal(MgPlayer *p, const MgCtrl *c, MgHitDef *h)
{
    read_hitdef(p, c, 0, h);          /* reversaldef reusa a disposicao de parametros/simbolos do hitdef */
}

/* ------------------------------------------------------------------ controladores */
static void exec(MgPlayer *p, const MgCtrl *c)
{
    MG_CRUMB('0' + (c->type % 40));
    switch (c->type) {
    case MG_CT_CHANGESTATE:
        MG_changeState(p, PIV(p, c, MG_P_CHANGESTATE_VALUE, p->stateno),
                       HAS(p, c, MG_P_CHANGESTATE_CTRL) ? PIV(p, c, MG_P_CHANGESTATE_CTRL, 0) : -1,
                       HAS(p, c, MG_P_CHANGESTATE_ANIM) ? PIV(p, c, MG_P_CHANGESTATE_ANIM, -1) : -1);
        break;
    case MG_CT_SELFSTATE:
        p->sdef = p->def;
        MG_changeState(p, PIV(p, c, MG_P_SELFSTATE_VALUE, p->stateno),
                       HAS(p, c, MG_P_SELFSTATE_CTRL) ? PIV(p, c, MG_P_SELFSTATE_CTRL, 0) : -1,
                       HAS(p, c, MG_P_SELFSTATE_ANIM) ? PIV(p, c, MG_P_SELFSTATE_ANIM, -1) : -1);
        break;
    case MG_CT_CHANGEANIM:
        MG_changeAnim(p, PIV(p, c, MG_P_CHANGEANIM_VALUE, p->anim_id), PIV(p, c, MG_P_CHANGEANIM_ELEM, 1));
        break;
    case MG_CT_VELSET:
        if (HAS(p, c, MG_P_VELSET_X)) p->vx = PV(p, c, MG_P_VELSET_X);
        if (HAS(p, c, MG_P_VELSET_Y)) p->vy = PV(p, c, MG_P_VELSET_Y);
        break;
    case MG_CT_VELADD:
        if (HAS(p, c, MG_P_VELADD_X)) p->vx += PV(p, c, MG_P_VELADD_X);
        if (HAS(p, c, MG_P_VELADD_Y)) p->vy += PV(p, c, MG_P_VELADD_Y);
        break;
    case MG_CT_VELMUL:
        if (HAS(p, c, MG_P_VELMUL_X)) p->vx = (p->vx * (PV(p, c, MG_P_VELMUL_X) >> 2)) >> (MG_FX_SHIFT - 2);
        if (HAS(p, c, MG_P_VELMUL_Y)) p->vy = (p->vy * (PV(p, c, MG_P_VELMUL_Y) >> 2)) >> (MG_FX_SHIFT - 2);
        break;
    case MG_CT_POSADD:
        if (HAS(p, c, MG_P_POSADD_X)) p->x += MG_FACE(PV(p, c, MG_P_POSADD_X), p->facing);
        if (HAS(p, c, MG_P_POSADD_Y)) p->y += PV(p, c, MG_P_POSADD_Y);
        break;
    case MG_CT_POSSET:
        if (HAS(p, c, MG_P_POSSET_X)) p->x = FXI(mg_fight.camx + 160) + PV(p, c, MG_P_POSSET_X);
        if (HAS(p, c, MG_P_POSSET_Y)) p->y = PV(p, c, MG_P_POSSET_Y);
        break;
    case MG_CT_CTRLSET: p->ctrl = PIV(p, c, MG_P_CTRLSET_VALUE, 0) != 0; break;
    case MG_CT_TURN: p->facing = -p->facing; break;
    case MG_CT_GRAVITY: p->vy += p->def->consts->yaccel; break;
    case MG_CT_SPRPRIORITY: p->sprpriority = PIV(p, c, MG_P_SPRPRIORITY_VALUE, 0); break;
    case MG_CT_POWERADD:
        p->power += PIV(p, c, MG_P_POWERADD_VALUE, 0);
        if (p->power < 0) p->power = 0;
        if (p->power > MG_POWERMAX(p)) p->power = MG_POWERMAX(p);
        break;
    case MG_CT_LIFEADD: p->life += PIV(p, c, MG_P_LIFEADD_VALUE, 0); break;
    case MG_CT_POSFREEZE: p->posfreeze = PIV(p, c, MG_P_POSFREEZE_VALUE, 1) != 0; break;
    case MG_CT_VARSET:
    case MG_CT_VARADD:
    case MG_CT_VARRANDOM: {
        s16 idx = SYM(p, c, MG_S_VARSET_INDEX);
        u8 isf = SYM(p, c, MG_S_VARSET_FVAR);
        mgfx v = MG_eval(p, PARAM(p, c, 0));
        if (c->type == MG_CT_VARRANDOM) {
            s32 lo = SYM(p, c, MG_S_VARSET_MIN), hi = v >> MG_FX_SHIFT;
            v = FXI(lo + (hi > lo ? (s32)(random() % (u16)(hi - lo + 1)) : 0));
        }
        if (isf) {
            if (idx >= 0 && idx < MG_NUM_FVARS) p->fvars[idx] = (c->type == MG_CT_VARADD) ? p->fvars[idx] + v : v;
        } else if (idx >= 0 && idx < MG_NUM_VARS) {
            s32 iv = v >> MG_FX_SHIFT;
            p->vars[idx] = (c->type == MG_CT_VARADD) ? p->vars[idx] + iv : iv;
        }
        break;
    }
    case MG_CT_PLAYSND: MG_playMugenSound(p, SYM(p, c, MG_S_PLAYSND_SOUND)); break;
    case MG_CT_STOPSND: XGM2_stopPCM(SOUND_PCM_CH_AUTO); break;
    case MG_CT_STATETYPESET: {
        u8 st = SYM(p, c, MG_S_STATETYPESET_STATETYPE), mt = SYM(p, c, MG_S_STATETYPESET_MOVETYPE),
           ph = SYM(p, c, MG_S_STATETYPESET_PHYSICS);
        if (st != 'U') p->statetype = st;
        if (mt != 'U') p->movetype = mt;
        if (ph != 'U') p->physics = ph;
        break;
    }
    case MG_CT_NOTHITBY:
        p->nothitby_attr = SYM(p, c, MG_S_NOTHITBY_ATTR);
        p->nothitby_time = PIV(p, c, MG_P_NOTHITBY_TIME, 1);
        break;
    case MG_CT_HITBY:
        p->nothitby_attr = (u16)~SYM(p, c, MG_S_HITBY_ATTR) & 0x0777;
        p->nothitby_time = PIV(p, c, MG_P_HITBY_TIME, 1);
        break;
    case MG_CT_HITDEF:
        read_hitdef(p, c, 0, &p->hd);
        p->hitdef_active = 1;
        break;
    case MG_CT_PROJECTILE: spawn_projectile(p, c); break;
    case MG_CT_SUPERPAUSE:
        mg_fight.pause_time = PIV(p, c, MG_P_SUPERPAUSE_TIME, 30);
        mg_fight.pause_movetime = PIV(p, c, MG_P_SUPERPAUSE_MOVETIME, 0);
        mg_fight.pause_owner = p->side;
        p->power += PIV(p, c, MG_P_SUPERPAUSE_POWERADD, 0);
        if (SYM(p, c, MG_S_SUPERPAUSE_SOUND) >= 0) MG_playSoundSfx(p, SYM(p, c, MG_S_SUPERPAUSE_SOUND));
        if (SYM(p, c, MG_S_SUPERPAUSE_ANIM) >= 0)
            MG_spawnExplod(p, SYM(p, c, MG_S_SUPERPAUSE_ANIM),
                           p->x + MG_FACE(PV(p, c, MG_P_SUPERPAUSE_POS_X), p->facing),
                           p->y + PV(p, c, MG_P_SUPERPAUSE_POS_Y), -2, -1, p->facing);
        break;
    case MG_CT_TARGETBIND:
        if (p->target) {
            p->bind_time = PIV(p, c, MG_P_TARGETBIND_TIME, 1);
            p->bind_x = PV(p, c, MG_P_TARGETBIND_POS_X);
            p->bind_y = PV(p, c, MG_P_TARGETBIND_POS_Y);
        }
        break;
    case MG_CT_TARGETSTATE:
        if (p->target) {
            p->target->sdef = p->sdef;            /* alvo passa a rodar estados do atacante */
            MG_changeState(p->target, PIV(p, c, MG_P_TARGETSTATE_VALUE, 0), -1, -1);
        }
        break;
    case MG_CT_TARGETVELSET:
        if (p->target) {
            if (HAS(p, c, MG_P_TARGETVELSET_X)) p->target->vx = PV(p, c, MG_P_TARGETVELSET_X);
            if (HAS(p, c, MG_P_TARGETVELSET_Y)) p->target->vy = PV(p, c, MG_P_TARGETVELSET_Y);
        }
        break;
    case MG_CT_TARGETLIFEADD:
        if (p->target) p->target->life += PIV(p, c, MG_P_TARGETLIFEADD_VALUE, 0);
        break;
    case MG_CT_TARGETDROP: p->target = 0; p->bind_time = 0; break;
    case MG_CT_HITVELSET:
        if (PIV(p, c, MG_P_HITVELSET_X, 1)) p->vx = p->gh_vx;
        if (PIV(p, c, MG_P_HITVELSET_Y, 1)) p->vy = p->gh_vy;
        break;
    case MG_CT_HITFALLVEL:
        if (p->gh_fall) { p->vx = p->gh.fall_xvel; p->vy = p->gh.fall_yvel; }
        break;
    case MG_CT_HITFALLDAMAGE: break;              /* fall.damage nao modelado (README) */
    case MG_CT_HITFALLSET: {
        s16 v = PIV(p, c, MG_P_HITFALLSET_VALUE, -1);
        if (v >= 0) p->gh_fall = v;
        break;
    }
    case MG_CT_ENVSHAKE: {                        /* MUGEN: vertical; ampl padrao -4 (so o modulo importa) */
        s16 a;
        if (MG_fightDemoFxHidden()) break;
        a = PIV(p, c, MG_P_ENVSHAKE_AMPL, -4);
        if (a < 0) a = -a;
        mg_fight.envshake_ampl = (s8)(a > 7 ? 7 : a);
        mg_fight.screen_shake = PIV(p, c, MG_P_ENVSHAKE_TIME, 10);
        break;
    }
    case MG_CT_EXPLOD: {
        s16 anim = PIV(p, c, MG_P_EXPLOD_ANIM, -1);
        if (anim >= 0)
            MG_spawnExplod(p, anim, p->x + MG_FACE(PV(p, c, MG_P_EXPLOD_POS_X), p->facing),
                           p->y + PV(p, c, MG_P_EXPLOD_POS_Y), PIV(p, c, MG_P_EXPLOD_REMOVETIME, -2),
                           PIV(p, c, MG_P_EXPLOD_ID, -1), p->facing);
        break;
    }
    case MG_CT_REMOVEEXPLOD: {
        s16 id = PIV(p, c, MG_P_REMOVEEXPLOD_ID, -1);
        for (u8 i = 0; i < MG_MAX_EXPLOD; i++)
            if (mg_fight.explod[i].active && mg_fight.explod[i].bind_owner == p->side &&
                (id < 0 || mg_fight.explod[i].id == id)) mg_fight.explod[i].removetime = 0;
        break;
    }
    case MG_CT_HELPER: {
        /* helper pode criar helper (Vega Super2): o novo helper pertence ao MESMO dono; o pool limita a cadeia */
        u8 slot = 0;
        while (slot < MG_MAX_HELPERS && mg_fight.helper_active[p->side][slot]) slot++;
        if (slot == MG_MAX_HELPERS) break;        /* pool cheio: helper descartado (README) */
        MgPlayer *h = &mg_fight.helper[p->side][slot];
        MgDraw keep = h->dr;
        memset(h, 0, sizeof(*h));
        h->dr = keep;
        h->def = h->sdef = p->def;
        h->enemy = p->enemy;
        h->side = p->side;
        h->pal = p->pal;
        h->is_helper = 1;
        h->parent = p->is_helper ? p->parent : p;
        h->helper_id = PIV(p, c, MG_P_HELPER_ID, 0);
        h->facing = p->facing;
        mgfx px = PV(p, c, MG_P_HELPER_POS_X), py = PV(p, c, MG_P_HELPER_POS_Y);
        switch (SYM(p, c, MG_S_HELPER_POSTYPE)) {
        case 1: h->x = p->enemy->x + MG_FACE(px, p->facing); h->y = p->enemy->y + py; break;
        case 4: h->x = FXI(mg_fight.camx) + px; h->y = py; break;
        case 5: h->x = FXI(mg_fight.camx + 320) + px; h->y = py; break;
        default: h->x = p->x + MG_FACE(px, p->facing); h->y = p->y + py; break;
        }
        h->life = p->def->consts->life >> MG_FX_SHIFT;
        h->statetype = 'S'; h->movetype = 'I'; h->physics = 'N';
        h->stateno = -1;
        h->helper_slot = slot;
        mg_fight.helper_active[p->side][slot] = 1;
        MG_changeState(h, PIV(p, c, MG_P_HELPER_STATENO, 0), 0, -1);
        break;
    }
    case MG_CT_DESTROYSELF:
        if (p->is_helper) mg_fight.helper_active[p->side][p->helper_slot] = 0;
        break;
    case MG_CT_REVERSALDEF: p->rev = c; break;
    case MG_CT_PAUSE:
        mg_fight.pause_time = PIV(p, c, MG_P_PAUSE_TIME, 0);
        mg_fight.pause_movetime = PIV(p, c, MG_P_PAUSE_MOVETIME, 0);
        mg_fight.pause_owner = p->side;
        break;
    case MG_CT_ATTACKDIST: p->attackdist = PIV(p, c, MG_P_ATTACKDIST_VALUE, 160); break;
    case MG_CT_HITADD: {
        s16 n = PIV(p, c, MG_P_HITADD_VALUE, 0);
        p->hitcount += n;
        mg_fight.combo[p->side] += n;
        mg_fight.combo_tick[p->side] = mg_fight.ticks;
        break;
    }
    case MG_CT_PLAYERPUSH: if (!PIV(p, c, MG_P_PLAYERPUSH_VALUE, 1)) p->nopush = 1; break;
    case MG_CT_SCREENBOUND: if (!PIV(p, c, MG_P_SCREENBOUND_VALUE, 1)) p->freebound = 1; break;
    case MG_CT_WIDTH:
        /* 2002.04.14: edge omitido vale 0,0 e dura 1 tick. Bytecode antigo tem nparams 0. */
        if (c->nparams > MG_P_WIDTH_EDGE_X && HAS(p, c, MG_P_WIDTH_EDGE_X))
            p->edge_f = PIV(p, c, MG_P_WIDTH_EDGE_X, 0);
        if (c->nparams > MG_P_WIDTH_EDGE_Y && HAS(p, c, MG_P_WIDTH_EDGE_Y))
            p->edge_b = PIV(p, c, MG_P_WIDTH_EDGE_Y, 0);
        break;
    default: break;                                /* null, assertspecial */
    }
}

/* TRG winko; ANDJ (salto curto); ...; ANDJ -> END.
 * WinKO falso percorre so esses saltos e devolve 0, sem outro trigger.
 * WinKO verdadeiro segue para MG_eval; o trigger nao consome random. */
static inline __attribute__((always_inline)) u8 mg_skip_false_winko(const MgPlayer *p, const MgCtrl *c)
{
    const u8 *b = p->sdef->code + c->cond;
    const u8 *land;
    const MgPlayer *e;
    u16 rel, rel2;
    if (b[0] != MG_OP_TRG || b[1] != MG_TRG_WINKO || b[2] != MG_OP_ANDJ) return 0;
    rel = ((u16)b[3] << 8) | b[4];
    if (rel > 64) return 0;
    land = b + 5 + rel;
    if (land[0] != MG_OP_ANDJ) return 0;
    rel2 = ((u16)land[1] << 8) | land[2];
    if (rel2 > 512 || land[3 + rel2] != MG_OP_END) return 0;
    e = p->enemy;
    return !(mg_fight.round_state >= 2 && e->life <= 0 && p->life > 0);
}

static u8 persistent_allows(MgPlayer *p, const MgCtrl *c)
{
    if (c->persist_mode == 0) return 1; /* default persistent=1 */
    if (c->persist_slot >= MG_MAX_PERSIST_SLOTS) return 0;
    u16 *count = &p->persist_count[c->persist_slot];
    if (c->persist_mode == 1) {
        if (*count) return 0;
        *count = 1;
        return 1;
    }
    if (c->persist_mode == 2 && c->persist_every) {
        (*count)++;
        if (*count >= c->persist_every) {
            *count = 0;
            return 1;
        }
    }
    return 0;
}

#ifdef MG_NATIVE_HITDEF
u8 MG_nativeControllerAllowed(MgPlayer *p, const MgCtrl *c)
{
    return persistent_allows(p, c);
}
#endif

/* Estado -1: visita so os controladores liberados pelos comandos ativos (bitmap gerado pelo
 * compilador) + os sem portao, na ordem original. Equivalente a varrer todos com o portao. */
u8 MG_nativeExecuteController(MgPlayer *p, const MgCtrl *c)
{
    if (!persistent_allows(p, c)) return 0;
    exec(p, c);
    return p->state_changed || (p->is_helper && !mg_fight.helper_active[p->side][p->helper_slot]);
}

static void run_minus1(MgPlayer *p)
{
    const MgCharDef *d = p->def;
#if defined(MG_NATIVE_EXPRESSIONS) && !defined(MG_VM_DISABLE_NATIVE)
    const MgCharDef *sd = p->sdef;
    const MgExprFn *native = sd->native_code == sd->code ? sd->native_eval : 0;
#endif
    const MgState *s = &d->states[d->st_minus1];
    u8 words = d->neg1_words;
    u32 m[8];
    if (words > 8) words = 8;
#ifdef MG_UPDATE_DETAIL_PROFILE
    const bool minus1Measure = !p->is_helper && mg_fight_update_detail_active;
    u32 minus1Mark = minus1Measure ? getSubTick() : 0;
#endif
    const u32 *ung = d->neg1_masks + (u16)d->ncmds * d->neg1_words;
    for (u8 k = 0; k < words; k++) m[k] = ung[k];
    for (u8 j = 0; j < p->nlive; j++) {
        const u32 *r = d->neg1_masks + (u16)p->live[j] * d->neg1_words;
        for (u8 k = 0; k < words; k++) m[k] |= r[k];
    }
#ifdef MG_UPDATE_DETAIL_PROFILE
    if (minus1Measure) {
        mg_fight_update_detail.negative_mask_build_ticks[p->side] = getSubTick() - minus1Mark;
        mg_fight_update_detail.negative_live_commands[p->side] = p->nlive;
        u16 candidates = 0;
        for (u8 k = 0; k < words; k++) {
            u32 bits = m[k];
            while (bits) { candidates++; bits &= bits - 1; }
        }
        mg_fight_update_detail.negative_candidate_controllers[p->side] = candidates;
        minus1Mark = getSubTick();
    }
#endif
#if defined(MG_NATIVE_CONTROLLERS) && !defined(MG_VM_DISABLE_NATIVE)
    if (d->native_minus1 && d->native_code == d->code) {
        u8 handled = d->native_minus1(p, m);
#ifdef MG_UPDATE_DETAIL_PROFILE
        if (minus1Measure) {
            mg_fight_update_detail.negative_native_ticks[p->side] = getSubTick() - minus1Mark;
            minus1Mark = getSubTick();
        }
#endif
        if (handled) return;
    }
#endif
#ifdef MG_UPDATE_DETAIL_PROFILE
    if (minus1Measure) minus1Mark = getSubTick();
#endif
    /* visita so os bits ligados, em ordem crescente (= ordem original dos controladores) */
    const MgCtrl *base = &d->ctrls[s->first_ctrl];
    for (u8 k = 0; k < words; k++) {
        u32 bits = m[k];
        while (bits) {
            u32 t = bits;
            u8 bi = 0;
            if (!(t & 0xFFFF)) { t >>= 16; bi += 16; }
            if (!(t & 0xFF)) { t >>= 8; bi += 8; }
            if (!(t & 0xF)) { t >>= 4; bi += 4; }
            if (!(t & 0x3)) { t >>= 2; bi += 2; }
            if (!(t & 0x1)) bi += 1;
            bits &= bits - 1;
            u16 i = (u16)k * 32 + bi;
            if (i >= s->nctrl) {
#ifdef MG_UPDATE_DETAIL_PROFILE
                if (minus1Measure) mg_fight_update_detail.negative_fallback_ticks[p->side] = getSubTick() - minus1Mark;
#endif
                return;
            }
            const MgCtrl *c = base + i;
            if (p->hitpause_active_tick && !c->ignorehitpause) continue;
#if defined(MG_NATIVE_EXPRESSIONS) && !defined(MG_VM_DISABLE_NATIVE)
            MgExprFn fn = native && c->cond < sd->native_code_size ? native[c->cond] : 0;
            if (fn) { if (!fn(p)) continue; }
            else
#endif
            {
                if (mg_skip_false_winko(p, c)) continue;
                if (!MG_eval(p, c->cond)) continue;
            }
            if (!persistent_allows(p, c)) continue;
            exec(p, c);
            if (p->state_changed) {
#ifdef MG_UPDATE_DETAIL_PROFILE
                if (minus1Measure) mg_fight_update_detail.negative_fallback_ticks[p->side] = getSubTick() - minus1Mark;
#endif
                return;
            }
        }
    }
#ifdef MG_UPDATE_DETAIL_PROFILE
    if (minus1Measure) mg_fight_update_detail.negative_fallback_ticks[p->side] = getSubTick() - minus1Mark;
#endif
}

static void run_state(MgPlayer *p, s16 idx)
{
#if defined(MG_NATIVE_CONTROLLERS) && !defined(MG_VM_DISABLE_NATIVE)
    if (idx == p->sdef->st_minus2 && p->sdef->native_minus1 &&
        p->sdef->native_code == p->sdef->code && p->sdef->native_minus1(p, 0)) return;
#endif
#if defined(MG_NATIVE_STATES) && !defined(MG_VM_DISABLE_NATIVE)
    if (p->sdef->native_state && p->sdef->native_code == p->sdef->code &&
        p->sdef->native_state(p, idx)) return;
#endif
#if defined(MG_NATIVE_EXPRESSIONS) && !defined(MG_VM_DISABLE_NATIVE)
    const MgCharDef *sd = p->sdef;
    const MgExprFn *native = sd->native_code == sd->code ? sd->native_eval : 0;
#endif
    const MgState *s = &p->sdef->states[idx];
    const MgCtrl *c = &p->sdef->ctrls[s->first_ctrl];
    u8 own = p->sdef == p->def;
    for (u16 i = 0; i < s->nctrl; i++, c++) {
        if (p->hitpause_active_tick && !c->ignorehitpause) continue;
        /* portoes exatos gerados pelo compilador (condicoes necessarias baratas) */
        if (c->tkind == 1 && p->time != c->tval) continue;
        if (c->tkind == 2 && (p->elem + 1 != c->tval || p->elem_time != 0)) continue;
        if (c->gate != MG_NONE) {
            const u8 *g = p->sdef->gates + c->gate;
            u8 n = *g++, any = 0;
            if (own) while (n--) if (p->cmd_timer[*g++]) { any = 1; break; }
            if (!any) continue;
        }
#if defined(MG_NATIVE_EXPRESSIONS) && !defined(MG_VM_DISABLE_NATIVE)
        MgExprFn fn = native && c->cond < sd->native_code_size ? native[c->cond] : 0;
        if (fn) { if (!fn(p)) continue; }
        else
#endif
        {
            if (mg_skip_false_winko(p, c)) continue;
            if (!MG_eval(p, c->cond)) continue;
        }
        if (!persistent_allows(p, c)) continue;
        exec(p, c);
        if (p->is_helper && !mg_fight.helper_active[p->side][p->helper_slot]) return;
        if (p->state_changed) return;          /* ChangeState aborta o resto do estado antigo */
    }
}

/* ------------------------------------------------------------------ comandos */
static const u16 KEY_MASK[16] = {
    0, MG_IN_F, MG_IN_B, MG_IN_U, MG_IN_D, MG_IN_D | MG_IN_F, MG_IN_D | MG_IN_B, MG_IN_U | MG_IN_F,
    MG_IN_U | MG_IN_B, MG_IN_A, MG_IN_BB, MG_IN_C, MG_IN_X, MG_IN_Y, MG_IN_Z, MG_IN_S };
#define key_mask(k) KEY_MASK[(k) & 15]

#define DIRS (MG_IN_U | MG_IN_D | MG_IN_B | MG_IN_F)

static u8 key_down(u16 in, const MgCmdKey *k)
{
    u16 m = key_mask(k->key);
    if (k->key >= MG_K_A) return (in & m) == m;
    if (k->mods & MG_KEY_4WAY) return (in & m) == m;          /* $F aceita DF/UF */
    return (in & DIRS) == m;                                   /* direcao exata */
}

/* evento de um passo no tick t do historico (hist[0] = agora):
 *   /tecla  = segurada em t;  ~tecla = soltou em t (carga: segurou reltime ticks antes);
 *   tecla   = pressionou em t (todas as teclas do passo seguras, ao menos uma com borda). */
static u8 step_at(const MgPlayer *p, const MgCmdStep *st, s16 t)
{
    const MgCharDef *d = p->def;
    u16 now = HIST(p, t), before = (t + 1 < p->hist_len) ? HIST(p, t + 1) : 0;
    u8 edge = 0, need_edge = 0;
    for (u8 ki = 0; ki < st->nkeys; ki++) {
        const MgCmdKey *k = &d->keys[st->first_key + ki];
        u8 dn = key_down(now, k), was = key_down(before, k);
        if (k->mods & MG_KEY_HOLD) {
            if (!dn) return 0;
        } else if (k->mods & MG_KEY_REL) {
            if (!was || dn) return 0;
            if (k->reltime) {
                u16 held = 0;
                for (s16 j = t + 1; j < p->hist_len && key_down(HIST(p, j), k); j++) held++;
                if (held < k->reltime) return 0;
            }
        } else {
            if (!dn) return 0;
            need_edge = 1;
            if (!was) edge = 1;
        }
    }
    return !need_edge || edge;
}

/* Reconhecedor incremental guiado por eventos (como os motores de luta).
 * Cada comando guarda o proximo passo e a idade da sequencia. Por tick so sao visitados:
 * comandos em andamento, comandos cujo 1o passo reage a uma tecla que teve evento (indice
 * cmd_bucket gerado pelo compilador) e comandos de "segurar". Passos consecutivos podem
 * ocorrer no mesmo tick se as teclas diferem. Divergencia declarada: casamento guloso. */
static u8 s_fired;

static void cmd_fire(MgPlayer *p, u8 i)
{
    s_fired = 1;
    const MgCommand *cm = &p->def->cmds[i];
    if (!p->cmd_timer[i] && p->nlive < MG_MAX_LIVE) p->live[p->nlive++] = i;
    p->cmd_timer[i] = cm->buffer_time ? cm->buffer_time : 1;
}

static u8 dir_code(u16 in)
{
    switch (in & DIRS) {
    case MG_IN_F: return MG_K_F; case MG_IN_B: return MG_K_B; case MG_IN_U: return MG_K_U; case MG_IN_D: return MG_K_D;
    case MG_IN_D | MG_IN_F: return MG_K_DF; case MG_IN_D | MG_IN_B: return MG_K_DB;
    case MG_IN_U | MG_IN_F: return MG_K_UF; case MG_IN_U | MG_IN_B: return MG_K_UB;
    }
    return 0;
}

/* contexto do tick para o teste rapido de passos de uma tecla */
static u8 s_dir_now, s_dir_prev;
static u16 s_in_now, s_in_prev;

/* passo com uma tecla sem modificador especial: teste inline (sem step_at) */
static u8 step_fast(const MgPlayer *p, const MgCmdStep *st)
{
    if (st->nkeys != 1) return step_at(p, st, 0);
    const MgCmdKey *k = &p->def->keys[st->first_key];
#ifdef MG_INPUT_FAST_MODIFIERS
    /* The current input context was established before either recognizer pass.
     * HOLD wins over REL exactly as in step_at. Charged release still needs
     * older history; combinations still use the complete historical evaluator.
     * No command timer, ordering, age or pause cache is changed here. */
    if (k->mods & MG_KEY_HOLD) return key_down(s_in_now, k);
    if (k->mods & MG_KEY_REL) {
        if (k->reltime) return step_at(p, st, 0);
        return key_down(s_in_prev, k) && !key_down(s_in_now, k);
    }
    if (k->mods & MG_KEY_4WAY)
        return key_down(s_in_now, k) && !key_down(s_in_prev, k);
#else
    if (k->mods & (MG_KEY_4WAY | MG_KEY_REL | MG_KEY_HOLD)) return step_at(p, st, 0);
#endif
    if (k->key >= MG_K_A) {
        u16 m = key_mask(k->key);
        return (s_in_now & m) && !(s_in_prev & m);
    }
    return s_dir_now == k->key && s_dir_prev != k->key;
}

#ifdef MG_COMMAND_GAP_COUNTERS
/* Diagnostic-only counters. A frame stamp lazily clears a command's scratch
 * row, avoiding a large memset in every selected gameplay update. */
static u16 s_commandGapCurrentFrame;
static u8 s_commandGapActive;
static u16 s_commandGapScratchStamp[2][MG_MAX_CMDS];
static u16 s_commandGapScratch[2][MG_MAX_CMDS][MG_COMMAND_GAP_METRIC_COUNT];
static u16 s_commandGapTotals[2][MG_COMMAND_GAP_GROUP_COUNT][MG_MAX_CMDS][MG_COMMAND_GAP_METRIC_COUNT];
enum { MG_COMMAND_GAP_SIDE_UPDATES = 0, MG_COMMAND_GAP_SIDE_EVENT_UPDATES,
       MG_COMMAND_GAP_SIDE_EVENT_MASK, MG_COMMAND_GAP_SIDE_METRIC_COUNT };
static u16 s_commandGapSideScratchStamp[2];
static u16 s_commandGapSideScratch[2][MG_COMMAND_GAP_SIDE_METRIC_COUNT];
static u16 s_commandGapSideTotals[2][MG_COMMAND_GAP_GROUP_COUNT][MG_COMMAND_GAP_SIDE_METRIC_COUNT];
static u16 s_commandGapFrames, s_commandGapMissFrames, s_commandGapControlFrames;
static u16 s_commandGapSaturations;

static void command_gap_count(const MgPlayer *p, u8 command, u8 metric)
{
    if (!s_commandGapActive || p->side > 1 || command >= MG_MAX_CMDS ||
        metric >= MG_COMMAND_GAP_METRIC_COUNT) return;
    const u8 side = p->side;
    if (s_commandGapScratchStamp[side][command] != s_commandGapCurrentFrame) {
        memset(s_commandGapScratch[side][command], 0,
               sizeof(s_commandGapScratch[side][command]));
        s_commandGapScratchStamp[side][command] = s_commandGapCurrentFrame;
    }
    u16 *count = &s_commandGapScratch[side][command][metric];
    if (*count != 0xFFFF) (*count)++;
    else if (s_commandGapSaturations != 0xFFFF) s_commandGapSaturations++;
}

static void command_gap_side_begin(u8 side)
{
    if (!s_commandGapActive || side > 1) return;
    if (s_commandGapSideScratchStamp[side] != s_commandGapCurrentFrame) {
        memset(s_commandGapSideScratch[side], 0, sizeof(s_commandGapSideScratch[side]));
        s_commandGapSideScratchStamp[side] = s_commandGapCurrentFrame;
    }
    if (s_commandGapSideScratch[side][MG_COMMAND_GAP_SIDE_UPDATES] != 0xFFFF)
        s_commandGapSideScratch[side][MG_COMMAND_GAP_SIDE_UPDATES]++;
}

static void command_gap_side_event(u8 side, u16 ev)
{
    if (!s_commandGapActive || side > 1 || !ev) return;
    if (s_commandGapSideScratchStamp[side] != s_commandGapCurrentFrame) {
        memset(s_commandGapSideScratch[side], 0, sizeof(s_commandGapSideScratch[side]));
        s_commandGapSideScratchStamp[side] = s_commandGapCurrentFrame;
    }
    if (s_commandGapSideScratch[side][MG_COMMAND_GAP_SIDE_EVENT_UPDATES] != 0xFFFF)
        s_commandGapSideScratch[side][MG_COMMAND_GAP_SIDE_EVENT_UPDATES]++;
    s_commandGapSideScratch[side][MG_COMMAND_GAP_SIDE_EVENT_MASK] |= ev;
}
#endif

/* tenta avancar o comando i neste tick; devolve a nova posicao */
static u8 cmd_advance(MgPlayer *p, u8 i, u16 ev)
{
    const MgCharDef *d = p->def;
    const MgCommand *cm = &d->cmds[i];
    u8 pos = p->cmd_pos[i];
    const MgCmdStep *st = &d->steps[cm->first_step + pos];
    if (((st->kmask & ev) || (st->strict & MG_STEP_HOLD_ONLY)) && step_fast(p, st)) {
#ifdef MG_COMMAND_GAP_COUNTERS
        command_gap_count(p, i, MG_COMMAND_GAP_MATCHED_STEPS);
#endif
        if (pos == 0) p->cmd_age[i] = 0;
        pos++;
        while (pos < cm->nsteps) {
            const MgCmdStep *nx = &d->steps[cm->first_step + pos];
            const MgCmdStep *pv = nx - 1;
            if (nx->nkeys == pv->nkeys && d->keys[nx->first_key].key == d->keys[pv->first_key].key) break;
            if (!((nx->kmask & ev) || (nx->strict & MG_STEP_HOLD_ONLY)) || !step_fast(p, nx)) break;
#ifdef MG_COMMAND_GAP_COUNTERS
            command_gap_count(p, i, MG_COMMAND_GAP_MATCHED_STEPS);
#endif
            pos++;
        }
    } else if (pos) {
        const MgCmdStep *s0 = &d->steps[cm->first_step];
        if (((s0->kmask & ev) || (s0->strict & MG_STEP_HOLD_ONLY)) && step_fast(p, s0)) {
#ifdef MG_COMMAND_GAP_COUNTERS
            command_gap_count(p, i, MG_COMMAND_GAP_MATCHED_STEPS);
            command_gap_count(p, i, MG_COMMAND_GAP_RESTART_MATCHES);
#endif
            pos = 1; p->cmd_age[i] = 0;
        }
    }
    if (pos >= cm->nsteps) {
#ifdef MG_COMMAND_GAP_COUNTERS
        command_gap_count(p, i, MG_COMMAND_GAP_COMPLETIONS);
#endif
        cmd_fire(p, i); pos = 0;
    }
    return pos;
}

#ifdef MG_COMMAND_GAP_COUNTERS
static u8 cmd_advance_counted(MgPlayer *p, u8 i, u16 ev)
{
    command_gap_count(p, i, MG_COMMAND_GAP_ADVANCE_ATTEMPTS);
    return cmd_advance(p, i, ev);
}

void MG_commandGapDiagCommitFrame(u16 frame, u16 vintGap)
{
    if (!MG_COMMAND_TRACE_FRAME_SELECTED(frame)) return;
    const u8 group = vintGap == 1 ? 1 : 0; /* 0 = FCAD gap; 1 = one-VInt control */
    if (s_commandGapFrames != 0xFFFF) s_commandGapFrames++;
    if (group == 0) {
        if (s_commandGapMissFrames != 0xFFFF) s_commandGapMissFrames++;
    } else if (s_commandGapControlFrames != 0xFFFF) s_commandGapControlFrames++;

    for (u8 side = 0; side < 2; side++) {
        for (u16 command = 0; command < MG_MAX_CMDS; command++) {
            if (s_commandGapScratchStamp[side][command] != frame) continue;
            for (u8 metric = 0; metric < MG_COMMAND_GAP_METRIC_COUNT; metric++) {
                const u32 sum = (u32)s_commandGapTotals[side][group][command][metric] +
                                s_commandGapScratch[side][command][metric];
                if (sum > 0xFFFF) {
                    s_commandGapTotals[side][group][command][metric] = 0xFFFF;
                    if (s_commandGapSaturations != 0xFFFF) s_commandGapSaturations++;
                } else s_commandGapTotals[side][group][command][metric] = (u16)sum;
            }
            s_commandGapScratchStamp[side][command] = 0;
        }
        if (s_commandGapSideScratchStamp[side] == frame) {
            for (u8 metric = 0; metric < MG_COMMAND_GAP_SIDE_METRIC_COUNT; metric++) {
                if (metric == MG_COMMAND_GAP_SIDE_EVENT_MASK) {
                    s_commandGapSideTotals[side][group][metric] |=
                        s_commandGapSideScratch[side][metric];
                } else {
                    const u32 sum = (u32)s_commandGapSideTotals[side][group][metric] +
                                    s_commandGapSideScratch[side][metric];
                    if (sum > 0xFFFF) {
                        s_commandGapSideTotals[side][group][metric] = 0xFFFF;
                        if (s_commandGapSaturations != 0xFFFF) s_commandGapSaturations++;
                    } else s_commandGapSideTotals[side][group][metric] = (u16)sum;
                }
            }
            s_commandGapSideScratchStamp[side] = 0;
        }
    }
}

void MG_commandGapDiagWriteSram(u32 offset)
{
    u16 declared[2] = {0, 0};
    u16 rows = 0, dropped = 0;
    for (u8 side = 0; side < 2; side++) {
        const MgCharDef *def = mg_fight.p[side].def;
        declared[side] = def ? def->ncmds : 0;
    }
    for (u8 side = 0; side < 2; side++) {
        const MgCharDef *def = mg_fight.p[side].def;
        if (!def) continue;
        u16 commandCount = def->ncmds;
        if (commandCount > MG_MAX_CMDS) commandCount = MG_MAX_CMDS;
        for (u16 command = 0; command < commandCount; command++) {
            u8 nonzero = 0;
            for (u8 group = 0; group < MG_COMMAND_GAP_GROUP_COUNT; group++)
                for (u8 metric = 0; metric < MG_COMMAND_GAP_METRIC_COUNT; metric++)
                    nonzero |= s_commandGapTotals[side][group][command][metric] != 0;
            if (!nonzero) continue;
            if (rows >= MG_COMMAND_GAP_ROW_CAPACITY) {
                if (dropped != 0xFFFF) dropped++;
                continue;
            }
            const MgCommand *cmd = &def->cmds[command];
            const u32 row = offset + MG_COMMAND_GAP_DIAG_HEADER_BYTES +
                            ((u32)rows * MG_COMMAND_GAP_DIAG_RECORD_BYTES);
            SRAM_writeWord(row + 0, ((u16)side << 8) | command);
            SRAM_writeWord(row + 2, cmd->first_step);
            SRAM_writeWord(row + 4, ((u16)cmd->nsteps << 8) | cmd->time);
            SRAM_writeWord(row + 6, ((u16)cmd->buffer_time << 8) | cmd->hold_only);
            u32 cursor = row + 8;
            for (u8 group = 0; group < MG_COMMAND_GAP_GROUP_COUNT; group++)
                for (u8 metric = 0; metric < MG_COMMAND_GAP_METRIC_COUNT; metric++) {
                    SRAM_writeWord(cursor, s_commandGapTotals[side][group][command][metric]);
                    cursor += 2;
                }
            rows++;
        }
    }

    SRAM_writeLong(offset + 0, 0x434D5452); /* CMTR */
    SRAM_writeLong(offset + 4, 2);
    SRAM_writeLong(offset + 8, MG_COMMAND_TRACE_EXPECTED_FRAMES);
    SRAM_writeLong(offset + 12, s_commandGapFrames);
    SRAM_writeLong(offset + 16, s_commandGapMissFrames);
    SRAM_writeLong(offset + 20, s_commandGapControlFrames);
    SRAM_writeLong(offset + 24, rows);
    SRAM_writeLong(offset + 28, MG_COMMAND_GAP_ROW_CAPACITY);
    SRAM_writeLong(offset + 32, dropped);
    SRAM_writeLong(offset + 36, s_commandGapSaturations);
    SRAM_writeLong(offset + 40, declared[0]);
    SRAM_writeLong(offset + 44, declared[1]);
    u32 sideCursor = offset + 48;
    for (u8 group = 0; group < MG_COMMAND_GAP_GROUP_COUNT; group++)
        for (u8 side = 0; side < 2; side++)
            for (u8 metric = 0; metric < MG_COMMAND_GAP_SIDE_METRIC_COUNT; metric++) {
                SRAM_writeWord(sideCursor, s_commandGapSideTotals[side][group][metric]);
                sideCursor += 2;
            }
}
#else
#define cmd_advance_counted(p, i, ev) cmd_advance((p), (i), (ev))
#endif

static void track(MgPlayer *p, u8 i, u8 old, u8 pos)
{
    p->cmd_pos[i] = pos;
    if (!old && pos && p->nprog < MG_MAX_PROG) p->prog[p->nprog++] = i;
}

/* Re-fire cached held commands in their original ascending order.
 * Empty groups skip eight command tests during unchanged input. */
static void hold_refire(MgPlayer *p
#ifdef MG_UPDATE_DETAIL_PROFILE
                        , u16 *firedCount
#endif
)
{
    const MgCharDef *d = p->def;
    const u8 nh = d->nhold_cmds;
    for (u8 base = 0; base < nh; base += 8) {
        u8 mask = p->hold_ok[base >> 3];
        if (!mask) continue;
        const u8 *cmd = &d->hold_cmds[base];
        u8 left = nh - base;
        if (left > 8) left = 8;
        do {
            if (mask & 1) {
#ifdef MG_UPDATE_DETAIL_PROFILE
                if (firedCount && *firedCount != 0xFFFF) (*firedCount)++;
#endif
                cmd_fire(p, *cmd);
            }
            cmd++; mask >>= 1;
        } while (mask && --left);
    }
}

static void hold_set(MgPlayer *p, u8 i)
{
    p->hold_ok[i >> 3] |= (u8)(1u << (i & 7));
}

static void update_hold_only(MgPlayer *p, u16 in)
{
    p->hist_head = (p->hist_head + 1) & (MG_INPUT_HIST - 1);
    p->hist[p->hist_head] = in;
    if (p->hist_len < MG_INPUT_HIST) p->hist_len++;
    const MgCharDef *d = p->def;
    u8 w = 0;
    for (u8 j = 0; j < p->nlive; j++) {
        u8 i = p->live[j];
        if (--p->cmd_timer[i]) p->live[w++] = i;
    }
    p->nlive = w;
    u16 prev = p->hist_len > 1 ? HIST(p, 1) : 0;
    s_in_now = in; s_in_prev = prev;
    s_dir_now = dir_code(in); s_dir_prev = dir_code(prev);
    u8 nh = d->nhold_cmds;
    if (in != prev || p->hist_len < 2) {
        memset(p->hold_ok, 0, sizeof(p->hold_ok));
        for (u8 j = 0; j < nh; j++) {
            u8 i = d->hold_cmds[j];
            const MgCommand *cm = &d->cmds[i];
            if (cm->nsteps != 1) continue;             /* so comandos de um passo de segurar */
            s_fired = 0;
#ifdef MG_INPUT_FAST_MODIFIERS
            if (step_fast(p, &d->steps[cm->first_step])) cmd_fire(p, i);
#else
            if (step_at(p, &d->steps[cm->first_step], 0)) cmd_fire(p, i);
#endif
            if (s_fired) hold_set(p, j);
        }
    } else {
#ifdef MG_UPDATE_DETAIL_PROFILE
        hold_refire(p, 0);
#else
        hold_refire(p);
#endif
    }
}

static void update_commands(MgPlayer *p, u16 in)
{
    MG_PROF_BEGIN();
#ifdef MG_COMMAND_GAP_COUNTERS
    /* APP_update increments sceneFrames after MG_playerInput runs, so attribute
     * this recognizer update to the same post-update frame used by GSEM/FCAD. */
    s_commandGapCurrentFrame = (u16)(gApp.sceneFrames + 1);
    s_commandGapActive = p->side < 2 &&
                         MG_COMMAND_TRACE_FRAME_SELECTED(s_commandGapCurrentFrame);
    command_gap_side_begin(p->side);
#endif
#ifdef MG_UPDATE_DETAIL_PROFILE
    const bool inputDetailActive = mg_fight_update_detail_active &&
                                   p->side < MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT;
    const u8 inputDetailSide = p->side;
    u32 inputDetailTick = inputDetailActive ? getSubTick() : 0;
    u16 inputDetailBucketEntries = 0;
    u16 inputDetailProgressVisits = 0;
    u16 inputDetailProgressZeroPosSkips = 0;
    u16 inputDetailProgressTimeouts = 0;
    u16 inputDetailProgressNoEventKeeps = 0;
    u16 inputDetailProgressAdvanceCalls = 0;
    u16 inputDetailHoldScanEntries = 0;
    u16 inputDetailHoldAdvanceCalls = 0;
    u16 inputDetailHoldRefireCalls = 0;
#endif
    p->hist_head = (p->hist_head + 1) & (MG_INPUT_HIST - 1);
    p->hist[p->hist_head] = in;
    if (p->hist_len < MG_INPUT_HIST) p->hist_len++;
    const MgCharDef *d = p->def;

    /* buffers ativos */
    u8 w = 0;
    for (u8 j = 0; j < p->nlive; j++) {
        u8 i = p->live[j];
        if (--p->cmd_timer[i]) p->live[w++] = i;
    }
    p->nlive = w;
    MG_INPUT_DETAIL_MARK(inputDetailActive, inputDetailSide, 1, inputDetailTick);

    /* eventos deste tick: codigos MG_K_* de direcao (saida/entrada) e botoes que mudaram */
    u16 prev = p->hist_len > 1 ? HIST(p, 1) : 0;
    s_in_now = in; s_in_prev = prev;
    s_dir_now = dir_code(in); s_dir_prev = dir_code(prev);
    u16 ev = 0;
    if ((prev ^ in) & DIRS) ev |= (1 << dir_code(prev)) | (1 << dir_code(in));
    u16 bchg = (prev ^ in) & ~DIRS;
    if (bchg & MG_IN_A) ev |= 1 << MG_K_A;
    if (bchg & MG_IN_BB) ev |= 1 << MG_K_B_BTN;
    if (bchg & MG_IN_C) ev |= 1 << MG_K_C;
    if (bchg & MG_IN_X) ev |= 1 << MG_K_X;
    if (bchg & MG_IN_Y) ev |= 1 << MG_K_Y;
    if (bchg & MG_IN_Z) ev |= 1 << MG_K_Z;
    if (bchg & MG_IN_S) ev |= 1 << MG_K_S;
    ev &= ~1;
#ifdef MG_COMMAND_GAP_COUNTERS
    command_gap_side_event(p->side, ev);
#endif
    MG_PROF_MARK(8);
    MG_INPUT_DETAIL_MARK(inputDetailActive, inputDetailSide, 2, inputDetailTick);

    /* 1) em andamento: timeout, proximo passo ou recomeco */
    w = 0;
    u8 n = p->nprog;
    for (u8 j = 0; j < n; j++) {
#ifdef MG_COMMAND_GAP_COUNTERS
        command_gap_count(p, p->prog[j], MG_COMMAND_GAP_PROGRESS_VISITS);
#endif
#ifdef MG_UPDATE_DETAIL_PROFILE
        if (inputDetailActive) inputDetailProgressVisits++;
#endif
        u8 i = p->prog[j];
        u8 pos = p->cmd_pos[i];
        if (!pos) {
#ifdef MG_UPDATE_DETAIL_PROFILE
            if (inputDetailActive) inputDetailProgressZeroPosSkips++;
#endif
            continue;
        }
        if (++p->cmd_age[i] > d->cmds[i].time) {
            pos = 0;
#ifdef MG_COMMAND_GAP_COUNTERS
            command_gap_count(p, i, MG_COMMAND_GAP_EXPIRATIONS);
#endif
#ifdef MG_UPDATE_DETAIL_PROFILE
            if (inputDetailActive) inputDetailProgressTimeouts++;
#endif
        }
        if (pos && !ev) {                  /* sem evento: so passo de segurar pode avancar */
            const MgCmdStep *nx = &d->steps[d->cmds[i].first_step + pos];
            if (!(nx->strict & MG_STEP_HOLD_ONLY)) {
                p->prog[w++] = i;
#ifdef MG_UPDATE_DETAIL_PROFILE
                if (inputDetailActive) inputDetailProgressNoEventKeeps++;
#endif
                continue;
            }
        }
        p->cmd_pos[i] = pos;
#ifdef MG_UPDATE_DETAIL_PROFILE
        if (inputDetailActive) inputDetailProgressAdvanceCalls++;
#endif
        pos = cmd_advance_counted(p, i, ev);
        p->cmd_pos[i] = pos;
        if (pos) p->prog[w++] = i;
    }
    p->nprog = w;
    MG_INPUT_DETAIL_MARK(inputDetailActive, inputDetailSide, 3, inputDetailTick);

    /* 2) comecos: comandos cujo 1o passo reage aos eventos deste tick */
    if (ev) {
        for (u8 code = 1; code < 16; code++) {
            if (!(ev & (1 << code))) continue;
            for (u16 j = d->cmd_bucket_first[code]; j < d->cmd_bucket_first[code + 1]; j++) {
#ifdef MG_UPDATE_DETAIL_PROFILE
                if (inputDetailBucketEntries != 0xFFFF) inputDetailBucketEntries++;
#endif
                u8 i = d->cmd_bucket[j];
                if (p->cmd_pos[i] || p->cmd_timer[i] == d->cmds[i].buffer_time) continue;   /* ja tratado */
                track(p, i, 0, cmd_advance_counted(p, i, ev));
            }
        }
    }
    MG_INPUT_DETAIL_MARK(inputDetailActive, inputDetailSide, 4, inputDetailTick);
    /* 3) comandos de segurar (ex.: holdfwd = /$F): so muda quando a entrada muda */
    u8 nh = d->nhold_cmds;
    if (in != prev || p->hist_len < 2) {
        memset(p->hold_ok, 0, sizeof(p->hold_ok));
        for (u8 j = 0; j < nh; j++) {
#ifdef MG_UPDATE_DETAIL_PROFILE
            if (inputDetailActive) inputDetailHoldScanEntries++;
#endif
            u8 i = d->hold_cmds[j];
            if (p->cmd_pos[i]) continue;
            s_fired = 0;
#ifdef MG_UPDATE_DETAIL_PROFILE
            if (inputDetailActive) inputDetailHoldAdvanceCalls++;
#endif
            track(p, i, 0, cmd_advance_counted(p, i, ev));
            if (s_fired) hold_set(p, j);
        }
    } else {
#ifdef MG_UPDATE_DETAIL_PROFILE
        hold_refire(p, inputDetailActive ? &inputDetailHoldRefireCalls : 0);
#else
        hold_refire(p);
#endif
    }
    MG_INPUT_DETAIL_MARK(inputDetailActive, inputDetailSide, 5, inputDetailTick);
#ifdef MG_UPDATE_DETAIL_PROFILE
    if (inputDetailActive) {
        mg_fight_update_detail.input_live_commands[inputDetailSide] = p->nlive;
        mg_fight_update_detail.input_progress_commands[inputDetailSide] = p->nprog;
        mg_fight_update_detail.input_bucket_entries[inputDetailSide] = inputDetailBucketEntries;
        mg_fight_update_detail.input_hold_commands[inputDetailSide] = d->nhold_cmds;
        mg_fight_update_detail.input_progress_visits[inputDetailSide] = inputDetailProgressVisits;
        mg_fight_update_detail.input_progress_zero_pos_skips[inputDetailSide] = inputDetailProgressZeroPosSkips;
        mg_fight_update_detail.input_progress_timeouts[inputDetailSide] = inputDetailProgressTimeouts;
        mg_fight_update_detail.input_progress_no_event_keeps[inputDetailSide] = inputDetailProgressNoEventKeeps;
        mg_fight_update_detail.input_progress_advance_calls[inputDetailSide] = inputDetailProgressAdvanceCalls;
        mg_fight_update_detail.input_hold_scan_entries[inputDetailSide] = inputDetailHoldScanEntries;
        mg_fight_update_detail.input_hold_advance_calls[inputDetailSide] = inputDetailHoldAdvanceCalls;
        mg_fight_update_detail.input_hold_refire_calls[inputDetailSide] = inputDetailHoldRefireCalls;
    }
#endif
#ifdef MG_COMMAND_GAP_COUNTERS
    s_commandGapActive = 0;
#endif
    MG_PROF_MARK(9);
}

/* pad (SGDK) -> bits relativos a frente */
static u16 pad_to_rel(u16 pad, s8 facing)
{
    u16 r = 0;
    if (pad & BUTTON_UP) r |= MG_IN_U;
    if (pad & BUTTON_DOWN) r |= MG_IN_D;
    if (pad & BUTTON_RIGHT) r |= facing > 0 ? MG_IN_F : MG_IN_B;
    if (pad & BUTTON_LEFT) r |= facing > 0 ? MG_IN_B : MG_IN_F;
    /* layout 6 botoes: A B C = chutes (a b c), X Y Z = socos (x y z), START = s */
    if (pad & BUTTON_A) r |= MG_IN_A;
    if (pad & BUTTON_B) r |= MG_IN_BB;
    if (pad & BUTTON_C) r |= MG_IN_C;
    if (pad & BUTTON_X) r |= MG_IN_X;
    if (pad & BUTTON_Y) r |= MG_IN_Y;
    if (pad & BUTTON_Z) r |= MG_IN_Z;
    if (pad & BUTTON_START) r |= MG_IN_S;
    return r;
}

/* ------------------------------------------------------------------ transicoes do motor */
static u8 cmd(const MgPlayer *p, u16 idx) { return idx != MG_NONE && p->cmd_timer[idx]; }

static void engine_auto_transitions(MgPlayer *p)
{
    if (!p->ctrl || p->movetype != 'I') return;
    const MgCharDef *d = p->def;
    u8 up = cmd(p, d->cmd_holdup), down = cmd(p, d->cmd_holddown);
    u8 fwd = cmd(p, d->cmd_holdfwd), back = cmd(p, d->cmd_holdback);
    MgPlayer *e = p->enemy;
    u8 threat = e->movetype == 'A';
    for (u8 i = 0; i < MG_MAX_PROJ && !threat; i++) threat = e->proj[i].active;
    if (p->statetype == 'S') {
        if (back && threat && p->stateno != 130) { MG_changeState(p, 120, -1, -1); return; }
        if (p->stateno != 0 && p->stateno != 20) return;
        if (up) MG_changeState(p, 40, -1, -1);
        else if (down) MG_changeState(p, 10, -1, -1);
        else if ((fwd || back) && p->stateno != 20) MG_changeState(p, 20, -1, -1);
    } else if (p->statetype == 'C') {
        if (back && threat && p->stateno != 131) { MG_changeState(p, 120, -1, -1); return; }
        if (p->stateno != 11 && p->stateno != 10) return;   /* soltar baixo tambem interrompe o agachar */
        if (up) MG_changeState(p, 40, -1, -1);
        else if (!down) MG_changeState(p, 12, -1, -1);
    } else if (p->statetype == 'A') {
        if (back && threat && p->stateno != 132 && (p->stateno == 50)) MG_changeState(p, 120, -1, -1);
    }
}

/* ------------------------------------------------------------------ tick */
void MG_playerInput(MgPlayer *p, u16 pad)
{
    if (p->is_helper) return;
#ifdef MG_UPDATE_DETAIL_PROFILE
    const bool inputDetailActive = mg_fight_update_detail_active &&
                                   p->side < MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT;
    const u8 inputDetailSide = p->side;
    const u32 inputDetailStart = inputDetailActive ? getSubTick() : 0;
    u32 inputDetailTick = inputDetailStart;
#endif
    u16 in = p->is_cpu ? MG_cpuInput(p) : pad_to_rel(pad, p->facing);
    MG_INPUT_DETAIL_MARK(inputDetailActive, inputDetailSide, 0, inputDetailTick);
    p->in_prev = p->in_raw;
    p->in_raw = in;
    if (!p->is_cpu) {
        update_commands(p, in);
#ifdef MG_UPDATE_DETAIL_PROFILE
        if (inputDetailActive)
            mg_fight_update_detail.input_total_ticks[inputDetailSide] = getSubTick() - inputDetailStart;
#endif
        return;
    }
    /* CPU: sem reconhecimento de sequencias; ativa o comando escolhido pela IA */
    update_hold_only(p, in);
    if (p->ai_cmd >= 0 && p->ai_cmd < (s16)p->def->ncmds) cmd_fire(p, (u8)p->ai_cmd);
#ifdef MG_UPDATE_DETAIL_PROFILE
    if (inputDetailActive)
        mg_fight_update_detail.input_total_ticks[inputDetailSide] = getSubTick() - inputDetailStart;
#endif
}

void MG_playerLogic(MgPlayer *p)
{
#ifdef MG_UPDATE_DETAIL_PROFILE
    const bool logicDetailActive = !p->is_helper && mg_fight_update_detail_active;
    u32 logicDetailTick = 0;
    u32 negativeDetailTick = 0;
#endif
    p->hitpause_active_tick = p->hitpause > 0;
    p->nopush = p->freebound = 0;
    p->edge_f = p->edge_b = 0;
    p->rev = 0;
    if (p->hitpause_active_tick) {
        /* Relogios, animacao, shake e fisica congelam. So roda controlador com
           ignorehitpause=1; o latch continua vivo ate push/bounds no fim do tick. */
        MG_PROF_BEGIN();
        p->state_changed = 0;
        MG_LOGIC_DETAIL_BEGIN(logicDetailActive, logicDetailTick);
        MG_NEGATIVE_DETAIL_BEGIN(logicDetailActive, negativeDetailTick);
        if (p->sdef == p->def && !p->is_helper) {
            if (p->def->st_minus3 >= 0) run_state(p, p->def->st_minus3);
            MG_NEGATIVE_DETAIL_MARK(logicDetailActive, negativeDetailTick, p,
                                    MG_UPDATE_DETAIL_NEGATIVE_MINUS3);
            if (p->def->st_minus2 >= 0 && !p->state_changed) run_state(p, p->def->st_minus2);
            MG_NEGATIVE_DETAIL_MARK(logicDetailActive, negativeDetailTick, p,
                                    MG_UPDATE_DETAIL_NEGATIVE_MINUS2);
            if (p->def->st_minus1 >= 0 && !p->state_changed) run_minus1(p);
            MG_NEGATIVE_DETAIL_MARK(logicDetailActive, negativeDetailTick, p,
                                    MG_UPDATE_DETAIL_NEGATIVE_MINUS1);
            MG_LOGIC_DETAIL_MARK(logicDetailActive, logicDetailTick, p,
                                 MG_UPDATE_DETAIL_LOGIC_NEGATIVE_STATES);
        }
        MG_PROF_MARK(10);
        MG_LOGIC_DETAIL_BEGIN(logicDetailActive, logicDetailTick);
        for (u8 guard = 0; guard < 6; guard++) {
            p->state_changed = 0;
            run_state(p, p->state_idx);
            if (!p->state_changed || (p->is_helper && !mg_fight.helper_active[p->side][p->helper_slot])) break;
        }
        MG_LOGIC_DETAIL_MARK(logicDetailActive, logicDetailTick, p,
                             MG_UPDATE_DETAIL_LOGIC_CURRENT_STATE);
        MG_PROF_MARK(11);
        MG_PROF_MARK(12);
        return;
    }
    if (p->hitshake > 0) { p->hitshake--; }
    else if (p->hittime_left > 0) p->hittime_left--;
    if (p->nothitby_time > 0) p->nothitby_time--;
    if (p->contact_fresh) p->contact_fresh = 0;          /* MUGEN: MoveHit = 1 no 1o tick apos o golpe */
    else {
        if (p->movecontact) p->movecontact++;
        if (p->movehit) p->movehit++;
        if (p->moveguarded) p->moveguarded++;
    }

    /* auto-turn (MUGEN: parado/agachado com ctrl vira para o oponente) */
    if (p->ctrl && p->statetype != 'A' && p->movetype == 'I' && MG_FACE(p->enemy->x - p->x, p->facing) < 0)
        p->facing = -p->facing;

    /* regra do motor MUGEN: deitado (5110) e vivo por liedown.time ticks -> levantar (5120) */
    if (p->stateno == 5110 && p->life > 0 && p->time >= (p->def->consts->liedown_time >> MG_FX_SHIFT))
        MG_selfState(p, 5120);

    /* ordem MUGEN: -3, -2, -1 (comandos) sempre; so entao as transicoes automaticas do motor */
    MG_PROF_BEGIN();
    p->state_changed = 0;
    MG_LOGIC_DETAIL_BEGIN(logicDetailActive, logicDetailTick);
    MG_NEGATIVE_DETAIL_BEGIN(logicDetailActive, negativeDetailTick);
    if (p->sdef == p->def && !p->is_helper) {    /* negativos: nao em custom state nem em helper */
        if (p->def->st_minus3 >= 0) run_state(p, p->def->st_minus3);
        MG_NEGATIVE_DETAIL_MARK(logicDetailActive, negativeDetailTick, p,
                                MG_UPDATE_DETAIL_NEGATIVE_MINUS3);
        if (p->def->st_minus2 >= 0 && !p->state_changed) run_state(p, p->def->st_minus2);
        MG_NEGATIVE_DETAIL_MARK(logicDetailActive, negativeDetailTick, p,
                                MG_UPDATE_DETAIL_NEGATIVE_MINUS2);
        if (p->def->st_minus1 >= 0 && !p->state_changed) run_minus1(p);
        MG_NEGATIVE_DETAIL_MARK(logicDetailActive, negativeDetailTick, p,
                                MG_UPDATE_DETAIL_NEGATIVE_MINUS1);
        MG_PROF_MARK(10);
        MG_LOGIC_DETAIL_MARK(logicDetailActive, logicDetailTick, p,
                             MG_UPDATE_DETAIL_LOGIC_NEGATIVE_STATES);
        MG_LOGIC_DETAIL_BEGIN(logicDetailActive, logicDetailTick);
        if (!p->state_changed) engine_auto_transitions(p);
        MG_LOGIC_DETAIL_MARK(logicDetailActive, logicDetailTick, p,
                             MG_UPDATE_DETAIL_LOGIC_AUTO_TRANSITIONS);
        MG_PROF_MARK(12);
    }
    /* estado atual; se mudou, o novo roda no mesmo tick (limite anti-loop) */
    MG_LOGIC_DETAIL_BEGIN(logicDetailActive, logicDetailTick);
    for (u8 guard = 0; guard < 6; guard++) {
        p->state_changed = 0;
        run_state(p, p->state_idx);
        if (!p->state_changed) break;
    }
    MG_LOGIC_DETAIL_MARK(logicDetailActive, logicDetailTick, p,
                         MG_UPDATE_DETAIL_LOGIC_CURRENT_STATE);
    MG_PROF_MARK(11);
}

void MG_playerPhysics(MgPlayer *p)
{
    const MgConsts *k = p->def->consts;
    if (p->is_helper && !mg_fight.helper_active[p->side][p->helper_slot]) return;
    if (p->hitpause > 0) { p->hitpause--; return; }
    if (p->bind_time > 0 && p->target) {
        MgPlayer *t = p->target;
        t->x = p->x + MG_FACE(p->bind_x, p->facing);
        t->y = p->y + p->bind_y;
        p->bind_time--;
    }
    if (!p->posfreeze && p->hitshake <= 0) {
        p->x += MG_FACE(p->vx, p->facing);
        p->y += p->vy;
    }
    p->posfreeze = 0;
    switch (p->physics) {
    case 'S': p->vx = (p->vx * (k->stand_friction >> 2)) >> (MG_FX_SHIFT - 2); break;
    case 'C': p->vx = (p->vx * (k->crouch_friction >> 2)) >> (MG_FX_SHIFT - 2); break;
    case 'A':
        p->vy += k->yaccel;
        if (p->y >= 0 && p->vy > 0) {       /* pouso automatico do motor */
            p->y = 0;
            p->vy = 0;
            MG_changeState(p, 52, -1, -1);
        }
        break;
    default: break;
    }
    /* so fisica S/C prende ao chao; N (quedas, deitado) e livre como no MUGEN */
    if ((p->physics == 'S' || p->physics == 'C') && p->statetype != 'A') {
        if (p->y > 0 || (p->y < 0 && p->vy >= 0)) {
            p->y = 0;
            if (p->vy > 0) p->vy = 0;
        }
    }
    MG_animAdvance(p);
    p->time++;
}

void MG_projStep(MgPlayer *p, MgProj *pr)
{
    if (!pr->active) return;
    if (pr->contact_time >= 0) pr->contact_time++;
    pr->x += MG_FACE(pr->vx, pr->facing);
    pr->y += pr->vy;
    pr->vx += pr->ax;
    pr->vy += pr->ay;
    s32 at = 0;
    anim_step(&pr->anim_idx, &pr->elem, &pr->elem_time, &at, p->def);
    if (pr->removetime > 0) pr->removetime--;
    const MgAnim *a = &p->def->anims[pr->anim_idx];
    u8 anim_over = pr->elem == 0 && pr->elem_time == 0 && a->count > 0 && a->loopstart == 0 && pr->removing;
    if (pr->removetime == 0 || anim_over) pr->active = 0;
    s32 sx = (pr->x >> MG_FX_SHIFT) - mg_fight.camx;
    if (sx < -160 || sx > 480) pr->active = 0;
}

void MG_explodStep(MgExplod *e, const MgPlayer *owner)
{
    if (!e->active) return;
    const MgCharDef *anim_def = e->anim_def ? e->anim_def : owner->def;
    const MgAnim *a = &anim_def->anims[e->anim_idx];
    u8 last = e->elem == a->count - 1;
    const MgAnimFrame *f = &anim_def->frames[a->first + e->elem];
    anim_step(&e->anim_idx, &e->elem, &e->elem_time, &e->anim_time, anim_def);
    e->x += MG_FACE(e->vx, e->facing);
    e->y += e->vy;
    if (e->removetime == -2) {              /* ate o fim da animacao */
        if (last && f->time >= 0 && e->elem_time == 0) e->active = 0;
    } else if (e->removetime > 0) {
        if (--e->removetime == 0) e->active = 0;
    } else if (e->removetime == 0) e->active = 0;
#ifdef MG_FX_TRACE
    if (a->id == 8060) {
        const u8 slot = (u8)(e - mg_fight.explod);
        MDRuntimeProbe_recordFx80(gApp.sceneFrames, (u16)mg_fight.ticks, owner->side,
                                  e->active ? MD_FX80_EVENT_FRAME : MD_FX80_EVENT_TERMINAL,
                                  slot, e->elem, e->elem_time, e->removetime,
                                  (u16)e->anim_time, (s16)(e->x >> MG_FX_SHIFT),
                                  (s16)(e->y >> MG_FX_SHIFT), (u16)owner->power);
    }
#endif
}

void MG_selfState(MgPlayer *p, s16 no)
{
    p->sdef = p->def;
    MG_changeState(p, no, -1, -1);
}
