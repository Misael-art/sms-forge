/* COPIADO de tools/mugen2sgdk_forge/runtime/mg_fight.c (v0.3.3). Edite na fonte. */
/* mg_fight.c -- luta 1x1: ordem do tick, colisao Clsn1 x Clsn2, acerto/defesa, projeteis,
 * explods, empurrao, camera, render, rounds, HUD transitorio e CPU. */
#include "mg/mg_runtime.h"
#include "mg/mg_bgfx_batch.h"
#include "mg/mg_ops.h"
#include "mg/mg_peak.h"
#if defined(MG_BOUNDS_TRACE_VERTICAL_SWEEP) && !defined(MG_BOUNDS_TRACE)
#error "MG_BOUNDS_TRACE_VERTICAL_SWEEP requires MG_BOUNDS_TRACE"
#endif

#if defined(MG_FX_TRACE) || defined(MG_BOUNDS_TRACE)
#include "game_vars.h"
#include "system/runtime_probe.h"
#endif

/* This project copy is the stage-free consumer runtime. Stage profiles are
 * rejected by mg_config.h until their renderer and CRAM owners are integrated. */
#if !defined(MG_ROUTE_FIGHT_BASE)
#error "Mugenesis installed runtime requires the stage-free MG_ROUTE_FIGHT_BASE profile"
#endif

#define FXI(v) ((mgfx)(v) << MG_FX_SHIFT)
#define FX2I(v) ((s16)((v) >> MG_FX_SHIFT))

MgFight mg_fight;
static const MgCharDef *sPendingSharedFxDef;
static s16 sPendingSharedFxAnimId = -1;
static u8 sRoundSeconds = MG_ROUND_TIME_SECONDS;
static u8 sRoundsToWin = MG_ROUNDS_TO_WIN;
static u8 sCpuLevel = 4;
static u8 sTrainingMode;
static u8 sTrainingSparring = MG_TRAINING_IDLE;
static s16 sTrainingSpecialCmd[2] = { -1, -1 };
static u8 sInfiniteSpecial;
static u8 sTrainingTimer = TRUE;
static u8 sContinuousSession;
static u8 sSfxEnabled = TRUE;
static u8 sVoiceEnabled = TRUE;
static MgEffects sFx = {
    TRUE, TRUE, MG_FX_ON, MG_FX_ON, TRUE, TRUE, MG_FX_ON, TRUE
};
static u8 sDemoShowcase;

static void hideDrawSprites(MgDraw *dr)
{
    u8 k;

    for (k = 0; k < MG_MAX_PARTS; k++)
        if (dr->spr[k]) SPR_setVisibility(dr->spr[k], HIDDEN);
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
    dr->cache_valid = FALSE;
#endif
}

void MG_fightSetSharedFxSource(const MgCharDef *source, s16 anim_id)
{
    sPendingSharedFxDef = source;
    sPendingSharedFxAnimId = source && anim_id >= 0 ? anim_id : -1;
}

#if MG_SHARED_SHADOW_FALLBACK || defined(MG_STUDY_FX80_BLINK)
static const SpriteDefinition *sSharedShadow;

void MG_fightUseSharedShadow(const SpriteDefinition *shadow)
{
    sSharedShadow = shadow;
}
#endif

void MG_fightHideActors(void)
{
    for (u8 side=0; side<2; side++) {
        hideDrawSprites(&mg_fight.p[side].dr);
        if (mg_fight.p[side].shadow_spr) SPR_setVisibility(mg_fight.p[side].shadow_spr,HIDDEN);
        for (u8 i=0;i<MG_MAX_PROJ;i++) hideDrawSprites(&mg_fight.p[side].proj[i].dr);
        for (u8 i=0;i<MG_MAX_HELPERS;i++) hideDrawSprites(&mg_fight.helper[side][i].dr);
    }
    for (u8 i=0;i<MG_MAX_EXPLOD;i++) hideDrawSprites(&mg_fight.explod[i].dr);
}

void MG_fightSetSessionOptions(u8 cpuLevel, u8 roundsToWin, u8 roundSeconds,
                               u8 trainingMode, u8 trainingSparring,
                               u8 infiniteSpecial, u8 trainingTimer)
{
    sCpuLevel = (cpuLevel == 2 || cpuLevel == 4 || cpuLevel == 8) ? cpuLevel : 4;
    sRoundsToWin = (roundsToWin == 1 || roundsToWin == 2) ? roundsToWin : MG_ROUNDS_TO_WIN;
    sRoundSeconds = (roundSeconds == 30 || roundSeconds == 60 || roundSeconds == 99)
        ? roundSeconds : MG_ROUND_TIME_SECONDS;
    sTrainingMode = trainingMode ? TRUE : FALSE;
    sTrainingSparring = trainingSparring <= MG_TRAINING_FREE
        ? trainingSparring : MG_TRAINING_IDLE;
    sInfiniteSpecial = infiniteSpecial ? TRUE : FALSE;
    sTrainingTimer = trainingTimer ? TRUE : FALSE;
    sTrainingSpecialCmd[0] = sTrainingSpecialCmd[1] = -1;
}

void MG_fightSetContinuousSession(u8 enabled)
{
    sContinuousSession = enabled ? TRUE : FALSE;
}

void MG_fightSetSoundCategories(u8 effectsEnabled, u8 voiceEnabled)
{
    sSfxEnabled = effectsEnabled ? TRUE : FALSE;
    sVoiceEnabled = voiceEnabled ? TRUE : FALSE;
}

/* Atalho da opcao antiga PISCA FX/SOMBRA: faisca, FX e sombra piscam juntos. */
void MG_fightSetEconomyBlink(u8 enabled)
{
    const u8 mode = enabled ? MG_FX_BLINK : MG_FX_ON;
    if (sFx.sparks != MG_FX_OFF) sFx.sparks = mode;
    if (sFx.fx != MG_FX_OFF) sFx.fx = mode;
    if (sFx.shadow != MG_FX_OFF) sFx.shadow = mode;
}

void MG_fightSetEffects(const MgEffects *fx)
{
    if (!fx) return;
    sFx = *fx;
}

const MgEffects *MG_fightGetEffects(void)
{
    return &sFx;
}

/* Laboratorio DEMO. O menu e do projeto. O motor so posiciona e executa.
 * Cada golpe sai uma vez sem apresentacao, espera um ciclo de idle e repete
 * com spark, explod, flash, shake e a tela de super. P2 nao ataca junto. */
#define DEMO_CAP 40
enum {
    DEMO_STEP_MENU = 0,
    DEMO_STEP_FIRE,
    DEMO_STEP_WATCH,
    DEMO_STEP_IDLE_ENTER,
    DEMO_STEP_IDLE,
    DEMO_STEP_STRESS
};

static u8 sDemoMode;
static u8 sDemoPlace;
static u8 sDemoShowFx;
static u8 sDemoPass;
static u8 sDemoStep;
static u8 sDemoBuilt;
static u8 sDemoIndex;
static u8 sDemoMoveN;
static u8 sDemoPlayed;
static u8 sDemoMenuPosed;
static u16 sDemoSpan;
static u16 sDemoIdle;
static u16 sDemoWatch;
static s16 sDemoMoveId;
static s16 sDemoIds[DEMO_CAP];
static const char *sDemoNames[DEMO_CAP];

static void demo_clear_flash(void);
static void stress_tick(void);

static const MgCharDef *sCmdNameDef[MG_CMD_NAME_CAPACITY];
static const char *const *sCmdNameTab[MG_CMD_NAME_CAPACITY];
static u16 sCmdNameN[MG_CMD_NAME_CAPACITY];
static u8 sCmdNameSets;
static u16 sCmdNameRejections;

MgCmdNamesResult MG_bindCmdNames(const MgCharDef *def, const char *const *names, u16 count)
{
    u8 i;
    if (!def || (!names && count)) {
        if (sCmdNameRejections != 0xFFFF) sCmdNameRejections++;
        return MG_CMD_NAMES_INVALID;
    }
    for (i = 0; i < sCmdNameSets; i++) {
        if (sCmdNameDef[i] != def) continue;
        if (!names) {
            --sCmdNameSets;
            for (; i < sCmdNameSets; i++) {
                sCmdNameDef[i] = sCmdNameDef[i + 1];
                sCmdNameTab[i] = sCmdNameTab[i + 1];
                sCmdNameN[i] = sCmdNameN[i + 1];
            }
            sCmdNameDef[i] = 0; sCmdNameTab[i] = 0; sCmdNameN[i] = 0;
        } else {
            sCmdNameTab[i] = names;
            sCmdNameN[i] = count;
        }
        return MG_CMD_NAMES_OK;
    }
    if (!names) return MG_CMD_NAMES_OK; /* removing an absent definition is idempotent */
    if (sCmdNameSets >= MG_CMD_NAME_CAPACITY) {
        if (sCmdNameRejections != 0xFFFF) sCmdNameRejections++;
        return MG_CMD_NAMES_FULL;
    }
    sCmdNameDef[sCmdNameSets] = def;
    sCmdNameTab[sCmdNameSets] = names;
    sCmdNameN[sCmdNameSets] = count;
    sCmdNameSets++;
    return MG_CMD_NAMES_OK;
}

void MG_clearCmdNames(void)
{
    memset(sCmdNameDef, 0, sizeof(sCmdNameDef));
    memset(sCmdNameTab, 0, sizeof(sCmdNameTab));
    memset(sCmdNameN, 0, sizeof(sCmdNameN));
    sCmdNameSets = 0; sCmdNameRejections = 0;
}
u8 MG_cmdNameCount(void) { return sCmdNameSets; }
u16 MG_cmdNameRejections(void) { return sCmdNameRejections; }

u8 MG_fightDemoFxHidden(void)
{
    return sDemoShowcase && !sDemoShowFx;
}

static void demo_reset(void)
{
    sDemoMode = sDemoPlace = sDemoShowFx = sDemoPass = 0;
    sDemoStep = DEMO_STEP_MENU;
    sDemoBuilt = sDemoIndex = sDemoMoveN = sDemoPlayed = sDemoMenuPosed = 0;
    sDemoSpan = 1;
    sDemoIdle = sDemoWatch = 0;
    sDemoMoveId = -1;
}

static const char *demo_cmd_name(const MgCharDef *def, u16 index)
{
    u8 i;
    const char *name;
    if (!def) return 0;
    for (i = 0; i < sCmdNameSets; i++) {
        if (sCmdNameDef[i] != def || index >= sCmdNameN[i]) continue;
        name = sCmdNameTab[i][index];
        if (!name || !name[0]) return 0;
        return name;
    }
    return 0;
}

static s16 demo_literal(const u8 *code, u16 off)
{
    const u8 *c;
    if (off == MG_NONE) return -32768;
    c = code + off;
    if (c[0] == MG_OP_PUSH8 && c[2] == MG_OP_END) return (s16)(s8)c[1];
    if (c[0] == MG_OP_PUSH16 && c[3] == MG_OP_END)
        return (s16)(((u16)c[1] << 8) | c[2]);
    return -32768;
}

static void demo_push(s16 id, const char *name)
{
    u8 i;
    if (id < 0 || sDemoMoveN >= DEMO_CAP) return;
    for (i = 0; i < sDemoMoveN; i++) {
        if (sDemoIds[i] != id) continue;
        if (!sDemoNames[i] && name) sDemoNames[i] = name;
        return;
    }
    sDemoIds[sDemoMoveN] = id;
    sDemoNames[sDemoMoveN] = name;
    sDemoMoveN++;
}

static void demo_consider(const MgCharDef *d, s16 id, const char *name)
{
    s16 idx;
    const MgState *s;
    if (id < 0) return;
    idx = MG_findState(d, id);
    if (idx < 0) return;
    s = &d->states[idx];
    if (id >= 1000 || id >= 800 || (id >= 200 && s->movetype == 'A'))
        demo_push(id, name);
}

static void demo_add_root(const MgCharDef *d, s16 id)
{
    s16 idx = MG_findState(d, id);
    const MgState *s;
    if (idx < 0) return;
    s = &d->states[idx];
    if (s->movetype != 'A' || s->statetype != 'S') return;
    demo_push(id, 0);
}

static u8 demo_rank(s16 id)
{
    if (id >= 1000) return 1;
    if (id >= 800) return 2;
    return 0;
}

static void demo_sort(void)
{
    u8 i;
    for (i = 1; i < sDemoMoveN; i++) {
        s16 v = sDemoIds[i];
        const char *name = sDemoNames[i];
        u8 rank = demo_rank(v);
        u8 j = i;
        while (j > 0) {
            u8 prev = demo_rank(sDemoIds[j - 1]);
            if (prev < rank || (prev == rank && sDemoIds[j - 1] <= v)) break;
            sDemoIds[j] = sDemoIds[j - 1];
            sDemoNames[j] = sDemoNames[j - 1];
            j--;
        }
        sDemoIds[j] = v;
        sDemoNames[j] = name;
    }
}

static const char *demo_gate_name(const MgCharDef *d, const MgCtrl *c)
{
    const u8 *g;
    u8 n, i;
    const char *name;
    if (!d->gates || c->gate == MG_NONE) return 0;
    g = d->gates + c->gate;
    n = g[0];
    if (n > 8) n = 8;
    for (i = 0; i < n; i++) {
        name = demo_cmd_name(d, g[1u + i]);
        if (name) return name;
    }
    return 0;
}

static u16 demo_one_idle(const MgPlayer *p)
{
    s16 total = 1;
    s16 idx;
    if (!p->def) return 1;
    idx = MG_findAnim(p->def, 0);
    if (idx >= 0 && p->def->anims[idx].total >= 1) total = p->def->anims[idx].total;
    return (u16)total;
}

static void demo_build(const MgPlayer *p)
{
    const MgCharDef *d = p->def;
    sDemoMoveN = 0;
    if (d && d->st_minus1 >= 0) {
        const MgState *st = &d->states[d->st_minus1];
        u16 i;
        for (i = 0; i < st->nctrl; i++) {
            const MgCtrl *c = &d->ctrls[st->first_ctrl + i];
            s16 id;
            if (c->type != MG_CT_CHANGESTATE || !c->nparams || c->params == MG_NONE) continue;
            id = demo_literal(d->code, d->param_offs[c->params + MG_P_CHANGESTATE_VALUE]);
            if (id == -32768) continue;
            demo_consider(d, id, demo_gate_name(d, c));
        }
    }
    if (d) {
        demo_add_root(d, 800);
        demo_add_root(d, 850);
    }
    demo_sort();
    sDemoSpan = demo_one_idle(p);
    sDemoBuilt = 1;
}

static void demo_ensure(void)
{
    if (sDemoBuilt || !mg_fight.p[0].def) return;
    demo_build(&mg_fight.p[0]);
}

static s16 demo_axis(const MgConsts *consts, u8 front)
{
    mgfx w;
    s16 px;
    if (!consts) return front ? 12 : 8;
    w = front ? consts->ground_front : consts->ground_back;
    px = (s16)(w >> MG_FX_SHIFT);
    if (px < 1) px = front ? 12 : 8;
    return px;
}

static void demo_snap_camera(void)
{
    s32 mid = (s32)FX2I(mg_fight.p[0].x) + (s32)FX2I(mg_fight.p[1].x);
    mid = mid / 2 - 160;
    if (mid < mg_fight.stage_left) mid = mg_fight.stage_left;
    if (mid > (s32)mg_fight.stage_right - 320) mid = (s32)mg_fight.stage_right - 320;
    mg_fight.camx = (s16)mid;
}

static void demo_place(u8 place)
{
    MgPlayer *a = &mg_fight.p[0];
    MgPlayer *b = &mg_fight.p[1];
    s16 gap, ax, bx, mid;
    if (!a->def || !b->def) return;
    gap = (s16)(demo_axis(a->def->consts, 1) + demo_axis(b->def->consts, 1));
    if (place == MG_DEMO_PLACE_CENTER) {
        mid = (s16)(((s32)mg_fight.stage_left + (s32)mg_fight.stage_right) / 2);
        ax = (s16)(mid - gap / 2);
        bx = (s16)(ax + gap);
    } else if (place == MG_DEMO_PLACE_CORNER) {
        bx = (s16)(mg_fight.stage_right - demo_axis(b->def->consts, 0));
        ax = (s16)(bx - gap);
    } else {
        mid = (s16)(((s32)mg_fight.stage_left + (s32)mg_fight.stage_right) / 2);
        ax = (s16)(mid - 70);
        bx = (s16)(mid + 70);
    }
    a->x = FXI(ax);
    b->x = FXI(bx);
    a->y = b->y = 0;
    a->vx = a->vy = b->vx = b->vy = 0;
    a->facing = 1;
    b->facing = -1;
    demo_snap_camera();
}

static void demo_snap_idle(MgPlayer *p)
{
    p->sdef = p->def;
    p->hitpause = 0;
    p->hitshake = 0;
    p->hittime_left = 0;
    p->bind_time = 0;
    p->target = 0;
    p->nothitby_time = 0;
    p->vx = 0;
    p->vy = 0;
    p->y = 0;
    p->gh_fall = 0;
    MG_changeState(p, 0, 0, -1);
    p->facing = p->side ? (s8)-1 : (s8)1;
    p->vx = 0;
    p->vy = 0;
    p->y = 0;
    p->hitpause = 0;
}

static void demo_quiet(void)
{
    u8 i, s, k;
    for (i = 0; i < MG_MAX_EXPLOD; i++) {
        mg_fight.explod[i].active = 0;
        MG_drawRelease(&mg_fight.explod[i].dr);
    }
    bgfx_release();
    mg_fight.screen_shake = 0;
    mg_fight.envshake_ampl = 0;
    mg_fight.shake_ax = 0;
    mg_fight.shake_ay = 0;
    mg_fight.shake_x = 0;
    mg_fight.shake_y = 0;
    mg_fight.shake_t = 255;
    demo_clear_flash();
    for (s = 0; s < 2; s++) {
        MgPlayer *p = &mg_fight.p[s];
        for (i = 0; i < MG_MAX_PROJ; i++) {
            p->proj[i].active = 0;
            MG_drawRelease(&p->proj[i].dr);
        }
        for (k = 0; k < MG_MAX_HELPERS; k++) {
            mg_fight.helper_active[s][k] = 0;
            MG_drawRelease(&mg_fight.helper[s][k].dr);
        }
    }
}

static u8 demo_launch(MgPlayer *p, s16 id)
{
    s16 idx = MG_findState(p->def, id);
    u8 air;
    if (idx < 0) return 0;
    air = p->def->states[idx].statetype == 'A';
    p->sdef = p->def;
    p->hitpause = 0;
    p->hitshake = 0;
    p->hittime_left = 0;
    p->bind_time = 0;
    p->target = 0;
    p->nothitby_time = 0;
    p->vx = 0;
    p->vy = 0;
    p->y = air ? FXI(-56) : 0;
    p->gh_fall = 0;
    MG_changeState(p, id, 0, -1);
    p->facing = p->side ? (s8)-1 : (s8)1;
    if (air) p->y = FXI(-56);
    p->hitpause = 0;
    return p->stateno == id;
}

static u8 demo_body_idle(const MgPlayer *p)
{
    return p->movetype == 'I' && p->stateno == 0 && p->hitpause == 0 && p->hitshake == 0;
}

static u8 demo_stage_clear(void)
{
    u8 i, s, k;
    if (mg_fight.bgfx_active || mg_fight.pause_time || mg_fight.screen_shake) return 0;
    for (i = 0; i < MG_MAX_EXPLOD; i++)
        if (mg_fight.explod[i].active) return 0;
    for (s = 0; s < 2; s++) {
        for (i = 0; i < MG_MAX_PROJ; i++)
            if (mg_fight.p[s].proj[i].active) return 0;
        for (k = 0; k < MG_MAX_HELPERS; k++)
            if (mg_fight.helper_active[s][k]) return 0;
    }
    return 1;
}

static void demo_pose_menu(void)
{
    sDemoShowFx = 0;
    demo_quiet();
    demo_place(MG_DEMO_PLACE_START);
    demo_snap_idle(&mg_fight.p[0]);
    demo_snap_idle(&mg_fight.p[1]);
    sDemoMenuPosed = 1;
}

static void demo_finish_move(void)
{
    if (sDemoMode == 2 && (u8)(sDemoIndex + 1) < sDemoMoveN) {
        sDemoIndex++;
        sDemoPass = 0;
        sDemoShowFx = 0;
        sDemoStep = DEMO_STEP_FIRE;
        return;
    }
    sDemoMode = 0;
    sDemoPass = 0;
    sDemoShowFx = 0;
    sDemoStep = DEMO_STEP_MENU;
    sDemoMenuPosed = 0;
    demo_pose_menu();
}

static void demo_begin_fire(void)
{
    s16 id;
    if (sDemoIndex >= sDemoMoveN) {
        demo_finish_move();
        return;
    }
    id = sDemoIds[sDemoIndex];
    sDemoMoveId = id;
    sDemoShowFx = sDemoPass == 2;
    demo_quiet();
    demo_place(sDemoPlace);
    demo_snap_idle(&mg_fight.p[0]);
    demo_snap_idle(&mg_fight.p[1]);
    if (id >= 1000) {
        u8 i;
        for (i = 0; i < 2; i++)
            if (mg_fight.p[i].def) mg_fight.p[i].power = MG_POWERMAX(&mg_fight.p[i]);
    }
    sDemoShowFx = sDemoPass == 2;
    sDemoPlayed = demo_launch(&mg_fight.p[0], id);
    demo_snap_idle(&mg_fight.p[1]);
    sDemoWatch = 0;
    sDemoStep = DEMO_STEP_WATCH;
}

static void demo_tick(void)
{
    u8 ready;
    if (!sDemoShowcase) return;
    demo_ensure();
    if (mg_fight.round_state == 0) mg_fight.round_state = 1;
    if (mg_fight.round_state != 1) return;
    switch (sDemoStep) {
    case DEMO_STEP_MENU:
        if (!sDemoMenuPosed) demo_pose_menu();
        break;
    case DEMO_STEP_FIRE:
        demo_begin_fire();
        break;
    case DEMO_STEP_WATCH:
        sDemoWatch++;
        ready = !sDemoPlayed || (demo_body_idle(&mg_fight.p[0]) && demo_stage_clear());
        if (ready || sDemoWatch >= 720) {
            if (sDemoPass == 0) sDemoStep = DEMO_STEP_IDLE_ENTER;
            else demo_finish_move();
        }
        break;
    case DEMO_STEP_IDLE_ENTER:
        sDemoShowFx = 0;
        demo_quiet();
        demo_place(sDemoPlace);
        demo_snap_idle(&mg_fight.p[0]);
        demo_snap_idle(&mg_fight.p[1]);
        sDemoIdle = 0;
        sDemoWatch = 0;
        sDemoStep = DEMO_STEP_IDLE;
        break;
    case DEMO_STEP_STRESS:
        stress_tick();
        break;
    case DEMO_STEP_IDLE:
        sDemoWatch++;
        if (demo_body_idle(&mg_fight.p[0]) && sDemoIdle < 60000) sDemoIdle++;
        if (sDemoIdle >= sDemoSpan || sDemoWatch >= (u16)(sDemoSpan + 180)) {
            sDemoPass = 2;
            sDemoStep = DEMO_STEP_FIRE;
        }
        break;
    default:
        sDemoStep = DEMO_STEP_MENU;
        sDemoMenuPosed = 0;
        break;
    }
}

/* ESTRESSE: os dois lutadores disparam em rodizio todo estado de ataque >= 1000 (especiais e
 * supers), cada vez que voltam ao idle, com barra cheia, KO bloqueado e efeitos visiveis.
 * Serve para medir o pior caso do projeto; nao e jogabilidade. */
static s16 sStressIds[2][DEMO_CAP];
static u8 sStressN[2], sStressNext[2];
static u16 sStressFrames;

static void stress_build(u8 side)
{
    const MgCharDef *d = mg_fight.p[side].def;
    sStressN[side] = 0;
    sStressNext[side] = 0;
    if (!d) return;
    for (u16 i = 0; i < d->nstates && sStressN[side] < DEMO_CAP; i++) {
        const MgState *st = &d->states[i];
        if (st->id >= 1000 && st->id < 4000 && st->movetype == 'A' && st->statetype != 'A')
            sStressIds[side][sStressN[side]++] = st->id;
    }
}

static void stress_tick(void)
{
    sStressFrames++;
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *p = &mg_fight.p[s];
        if (!p->def) continue;
        p->power = MG_POWERMAX(p);
        {
            const s32 maxl = p->def->consts->life >> MG_FX_SHIFT;
            if (p->life < maxl / 2) p->life = maxl;   /* vida volta cheia: o estresse nunca termina em KO */
        }
        if (!sStressN[s] || !demo_body_idle(p)) continue;
        s16 id = sStressIds[s][sStressNext[s] % sStressN[s]];
        sStressNext[s]++;
        demo_launch(p, id);
        /* demo_launch fixa a direcao pelo lado (P1 direita, P2 esquerda); depois de se cruzarem
         * isso os deixava de costas. Como na luta: sempre de frente para o oponente. */
        p->facing = p->enemy && p->enemy->x < p->x ? (s8)-1 : (s8)1;
    }
    /* se a luta os afastou, volta ao centro quando os dois estiverem livres */
    if ((sStressFrames & 255) == 0 && demo_body_idle(&mg_fight.p[0]) && demo_body_idle(&mg_fight.p[1]))
        demo_place(MG_DEMO_PLACE_CENTER);
}

void MG_fightDemoStress(u8 enabled)
{
    if (!sDemoShowcase) return;
    if (enabled) {
        if (sDemoStep != DEMO_STEP_MENU) return;
        stress_build(0);
        stress_build(1);
        sDemoMode = 3;
        sDemoShowFx = 1;
        sStressFrames = 0;
        demo_quiet();
        demo_place(MG_DEMO_PLACE_CENTER);
        demo_snap_idle(&mg_fight.p[0]);
        demo_snap_idle(&mg_fight.p[1]);
        sDemoStep = DEMO_STEP_STRESS;
        return;
    }
    if (sDemoStep != DEMO_STEP_STRESS) return;
    demo_finish_move();
}

u8 MG_fightDemoStressActive(void)
{
    return sDemoShowcase && sDemoStep == DEMO_STEP_STRESS;
}

static void demo_sustain(void)
{
    u8 i;
    s16 id;
    if (!sDemoShowcase) return;
    for (i = 0; i < 2; i++) {
        MgPlayer *p = &mg_fight.p[i];
        if (p->def && p->life <= 0) p->life = 1;
    }
    if (sDemoStep == DEMO_STEP_MENU || sDemoIndex >= sDemoMoveN) return;
    id = sDemoIds[sDemoIndex];
    if (id < 1000) return;
    for (i = 0; i < 2; i++)
        if (mg_fight.p[i].def) mg_fight.p[i].power = MG_POWERMAX(&mg_fight.p[i]);
}

void MG_fightSetDemoShowcase(u8 enabled)
{
    u8 on = enabled ? TRUE : FALSE;
    if (on != sDemoShowcase) demo_reset();
    sDemoShowcase = on;
}

u8 MG_fightDemoShowcase(void)
{
    return sDemoShowcase;
}

u8 MG_fightDemoSuperBarOnly(void)
{
    return 0;
}

u8 MG_fightDemoMoveCount(void)
{
    demo_ensure();
    return sDemoMoveN;
}

const char *MG_fightDemoMoveName(u8 index)
{
    demo_ensure();
    if (index >= sDemoMoveN) return 0;
    return sDemoNames[index];
}

static void demo_arm(u8 index, u8 place, u8 mode)
{
    if (!sDemoShowcase || sDemoStep != DEMO_STEP_MENU) return;
    demo_ensure();
    if (!sDemoMoveN) return;
    if (mode == 1 && index >= sDemoMoveN) return;
    sDemoMode = mode;
    sDemoIndex = mode == 2 ? 0 : index;
    sDemoPlace = place > MG_DEMO_PLACE_CORNER ? MG_DEMO_PLACE_START : place;
    sDemoPass = 0;
    sDemoShowFx = 0;
    sDemoMenuPosed = 0;
    sDemoStep = DEMO_STEP_FIRE;
}

void MG_fightDemoPlayOne(u8 index, u8 place)
{
    demo_arm(index, place, 1);
}

void MG_fightDemoPlayAll(u8 place)
{
    demo_arm(0, place, 2);
}

u8 MG_fightDemoBusy(void)
{
    return sDemoShowcase && sDemoStep != DEMO_STEP_MENU;
}
u8 MG_fightRoundSeconds(void) { return sRoundSeconds; }
u8 MG_fightRoundsToWin(void) { return sRoundsToWin; }
u8 MG_fightCpuLevel(void) { return sCpuLevel; }

#ifdef MG_UPDATE_DETAIL_PROFILE
MgFightUpdateDetail mg_fight_update_detail;
bool mg_fight_update_detail_active;
static u16 sUpdateDetailFrame;
static bool sUpdateDetailEnabled;

void MG_fightSetUpdateDetailFrame(u16 frame, bool enabled)
{
    sUpdateDetailFrame = frame;
    sUpdateDetailEnabled = enabled;
    mg_fight_update_detail_active = enabled;
}

bool MG_fightUpdateDetailIsActive(void)
{
    return sUpdateDetailEnabled;
}

void MG_fightUpdateDetailRecordLogic(u8 side, u8 phase, u32 subticks)
{
    if (!sUpdateDetailEnabled || side >= MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT ||
        phase >= MG_UPDATE_DETAIL_LOGIC_PHASE_COUNT) return;
    mg_fight_update_detail.logic[side][phase] += subticks;
}

void MG_fightUpdateDetailRecordNegative(u8 side, u8 phase, u32 subticks)
{
    if (!sUpdateDetailEnabled || side >= MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT ||
        phase >= MG_UPDATE_DETAIL_NEGATIVE_PHASE_COUNT) return;
    mg_fight_update_detail.negative_logic[side][phase] += subticks;
}

#define MG_UPDATE_DETAIL_MARK(index) do { \
    if (updateDetailCapture) { \
        const u32 updateDetailNow = getSubTick(); \
        mg_fight_update_detail.phase[(index)] = updateDetailNow - updateDetailTick; \
        updateDetailTick = updateDetailNow; \
    } \
} while (0)
#else
#define MG_UPDATE_DETAIL_MARK(index) do { } while (0)
#endif
#ifdef MG_TEST_BREADCRUMB
char mg_crumbs[25];
u8 mg_crumb_i;
#endif
/* VRAM fixa por jogador (sem realocacao a cada troca de sheet); 0 = alocacao automatica */
static u16 s_vram[2];
static u16 s_vram_cap[2];   /* tiles reservados em s_vram: maior sheet de CORPO (pal 0) */
/* efeitos de fundo: tiles pre-carregados apos os corpos; base por jogador/efeito (0 = sem espaco) */
#define MG_MAX_BGFX 4
static u16 s_bgfx_base[2][MG_MAX_BGFX];
static u16 s_bgfx_end[2][MG_MAX_BGFX]; /* immutable reservation ends */
static u32 sSpriteFailures;
static u8 sHudOverlay;
u32 MG_fightSpriteFailures(void) { return sSpriteFailures; }
static s8 s_bgfx_owner = -1;
#if defined(MG_PROFILE) || defined(MG_LOGIC_PROFILE)
u32 mg_prof[16];
#endif

#ifndef MG_STAGE_WORLD_WIDTH
#define MG_STAGE_WORLD_WIDTH 640 /* largura compatível do runtime sem contrato local de stage */
#endif
#if MG_STAGE_WORLD_WIDTH < 320
#error "MG_STAGE_WORLD_WIDTH must cover at least one 320px viewport"
#endif
#define STAGE_W        MG_STAGE_WORLD_WIDTH
#define FLOOR_Y        200      /* linha do chao na tela (px) */
#define SPR_VRAM_TILES 900
#define MG_AUDIO_QUEUE_CAPACITY 64
#define MG_AUDIO_QUEUE_MASK (MG_AUDIO_QUEUE_CAPACITY - 1)
#if (MG_AUDIO_QUEUE_CAPACITY & MG_AUDIO_QUEUE_MASK) != 0
#error "MG_AUDIO_QUEUE_CAPACITY must be a power of two"
#endif

/* ------------------------------------------------------------------ efeitos de impacto
 * Camera shake: so em IMPACTO PESADO (acerto, nao defesa, que derruba, mata ou tira >= 100).
 * No Ken isso e 73 de 204 acertos (36%), medido no harness em 36000 ticks.
 * E uma mola amortecida: o 1o quadro empurra o mundo na direcao do golpe e ele volta
 * oscilando, com amplitude decrescente. Queda/KO tambem batem no eixo Y (o chao treme).
 * O flash de impacto altera somente o backdrop PAL0[0] do perfil sem palco; nenhuma linha
 * partilhada por corpo, projétil ou FX e tocada. Impacto pesado dura 2 quadros; os restantes, 1. */
#define MG_HEAVY_DAMAGE 100
#ifndef MG_TEST_DISABLE_STAGE3_SHAKE
#define MG_SHAKE_LEN    12
/* resposta da mola em oitavos da amplitude, 1 entrada por quadro */
static const s8 kShake[MG_SHAKE_LEN] = { 8, -6, 5, -4, 3, -3, 2, -2, 1, -1, 1, 0 };
#endif
#ifndef MG_TEST_DISABLE_STAGE3_FLASH
static const u16 kImpactBackdropColor = RGB24_TO_VDPCOLOR(0xFFFFFF);
static u16 sBaseBackdropColor;
static u8 sBackdropFlashFrames;
static u8 sBackdropFlashActive;
#endif
/* Flash do corpo (recuperado do runtime de 2026-09-25, 33a179bc): todo acerto clareia a linha de
 * paleta do defensor ao branco e apaga em 4 quadros; impacto pesado comeca no branco puro.
 * A linha e compartilhada com os projeteis desse lado e com o retrato P2 do HUD, que clareiam
 * junto (doc/agent_learning/stagefree_flash_cram_ownership_20261006.md). Opcional: MgEffects.body_flash. */
/* canal de 3 bits clareado para o branco em nivel/4 (nivel 0..4) */
static const u8 kFlash[5][8] = {
    { 0, 1, 2, 3, 4, 5, 6, 7 }, { 2, 3, 3, 4, 5, 6, 6, 7 }, { 4, 4, 5, 5, 6, 6, 7, 7 },
    { 5, 6, 6, 6, 7, 7, 7, 7 }, { 7, 7, 7, 7, 7, 7, 7, 7 },
};
static const u16 *s_basepal[2];     /* paleta do corpo de cada lado (restaurada no fim do flash) */
/* Tabela pre-montada por lutador (niveis 2..4). Memoria estatica: DMA_QUEUE le a fonte no VBlank. */
static u16 s_flash_tab[2][3][15];

/* Consumidores de CRAM declarados (REGRA 1c generalizada). Depois dos statics: as
 * constantes apontam para dados estaticos e o DMA_QUEUE so os le no VBlank. */
const CramConsumer CRAM_FLASH_P1   = CRAM_CONSUMER(1, 1, 15, 0); /* flash do corpo P1 (MgEffects.body_flash) */
const CramConsumer CRAM_FLASH_P2   = CRAM_CONSUMER(2, 1, 15, 0); /* flash do corpo P2 (MgEffects.body_flash) */
const CramConsumer CRAM_SUPER_BGFX = CRAM_CONSUMER(0, 1, 14, 1);
const CramConsumer CRAM_FX_PAL3    = CRAM_CONSUMER(3, 0, 15, 0);
/* Reservas de posse: lo==hi==0 escreve nada. A faixa real e declarada por quem consome
 * (retrato na Etapa C; stage/HUD na Etapa D), o que impede dois consumidores de reivindicarem
 * o mesmo indice por silencio. */
const CramConsumer CRAM_STAGERES   = CRAM_CONSUMER(0, 1, 8, 0);
const CramConsumer CRAM_HUDRES     = CRAM_CONSUMER(0, 9, 15, 0);
const CramConsumer CRAM_PORTRAIT_P1 = CRAM_CONSUMER(1, 0, 0, 0);
const CramConsumer CRAM_PORTRAIT_P2 = CRAM_CONSUMER(2, 0, 0, 0);

u8 cram_span(const CramConsumer *c)
{
    if (!c->lo && !c->hi) return 0;                 /* indice transparente nao pertence a paleta de tiles */
    return (u8)(c->hi >= c->lo ? c->hi - c->lo + 1 : 0);
}

static u16 cram_base(const CramConsumer *c) { return (u16)(c->line * 16 + c->lo); }

/* Fonte deve ser memoria estatica: DMA_QUEUE so le o ponteiro no VBlank. */
void cram_write(const CramConsumer *c, const u16 *src)
{
    u8 n = cram_span(c);
    if (!n) return;
    PAL_setColors(cram_base(c), src, n, DMA_QUEUE);
}

void cram_save(const CramConsumer *c, u16 *dst)
{
    u8 n = cram_span(c);
    if (!n) return;
    PAL_getColors(cram_base(c), dst, n);
}

void cram_restore(const CramConsumer *c, const u16 *saved) { cram_write(c, saved); }

/* PAL0[0] e transparente para tiles, mas tambem alimenta o backdrop global.
 * Trata-se apenas do perfil stage-free e fica fora das faixas CRAM de assets. */
static void backdrop_save(u16 *color) { PAL_getColors(0, color, 1); }
static void backdrop_write(const u16 *color) { PAL_setColors(0, color, 1, DMA_QUEUE); }

static void build_flash_table(u8 side)
{
    const u16 *src = s_basepal[side];
    for (u8 l = 2; l <= 4; l++) {
        const u8 *t = kFlash[l];
        for (u8 i = 0; i < 15; i++) {
            u16 v = src[i + 1];
            s_flash_tab[side][l - 2][i] = ((u16)t[(v >> 9) & 7] << 9) | ((u16)t[(v >> 5) & 7] << 5) | ((u16)t[(v >> 1) & 7] << 1);
        }
    }
}

/* Devolve a linha do corpo se um flash ficou pela metade (desligar a opcao, fim de round). */
static void body_flash_restore(void)
{
    for (u8 s = 0; s < 2; s++) {
        if (!mg_fight.flash_lvl[s]) continue;
        mg_fight.flash_lvl[s] = 0;
        if (s_basepal[s]) cram_write(s ? &CRAM_FLASH_P2 : &CRAM_FLASH_P1, &s_basepal[s][1]);
    }
}

static void demo_clear_flash(void)
{
    body_flash_restore();
#if !defined(MG_TEST_DISABLE_STAGE3_FLASH) && defined(MG_ROUTE_FIGHT_BASE)
    sBackdropFlashFrames = 0;
    if (sBackdropFlashActive) {
        backdrop_write(&sBaseBackdropColor);
        sBackdropFlashActive = 0;
    }
#endif
}

static s16 s_bgb_scroll_x, s_bgb_scroll_y;

static void impact_fx(const MgPlayer *d, s32 dmg, s8 afc)
{
    if (MG_fightDemoFxHidden()) return;
#if !defined(MG_TEST_DISABLE_STAGE3_FLASH) || !defined(MG_TEST_DISABLE_STAGE3_SHAKE)
    u8 heavy = d->gh_fall || d->life <= 0 || dmg >= MG_HEAVY_DAMAGE;
#endif
#ifndef MG_TEST_DISABLE_STAGE3_FLASH
    if (sFx.screen_flash && sBackdropFlashFrames < (heavy ? 2 : 1)) sBackdropFlashFrames = heavy ? 2 : 1;
#endif
    if (sFx.body_flash && s_basepal[d->side]) mg_fight.flash_lvl[d->side] = heavy ? 4 : 3;
#ifndef MG_TEST_DISABLE_STAGE3_SHAKE
    if (!heavy) return;
    s8 a = 2 + (s8)(dmg / 40);                      /* 35 -> 2 px ... 130 -> 5 px */
    if (d->life <= 0) a += 2;                       /* KO: o golpe final pesa mais */
    if (a > 7) a = 7;
    mg_fight.shake_ax = afc < 0 ? -a : a;
    mg_fight.shake_ay = (d->gh_fall || d->life <= 0) ? a / 2 + 1 : 0;
    mg_fight.shake_t = 0;
#else
    (void)d;
    (void)dmg;
    (void)afc;
#endif
}

/* avanca 1 quadro: calcula o deslocamento da camera e aplica o flash. Custo zero parado. */
static void impact_fx_step(void)
{
    s8 x = 0, y = 0;
#ifndef MG_TEST_DISABLE_STAGE3_SHAKE
    if (mg_fight.shake_t < MG_SHAKE_LEN) {
        s8 k = kShake[mg_fight.shake_t++];
        x = (s8)((mg_fight.shake_ax * k) >> 3);
        y = (s8)((mg_fight.shake_ay * (k < 0 ? -k : k)) >> 3);   /* Y so desce: o chao quica */
    }
#endif
    if (mg_fight.screen_shake > 0) {                /* EnvShake do personagem: vertical, alternado */
        s8 e = mg_fight.envshake_ampl ? mg_fight.envshake_ampl : 2;
        y += (mg_fight.screen_shake & 2) ? e : -e;
        mg_fight.screen_shake--;
    }
    mg_fight.shake_x = x;
    mg_fight.shake_y = y;
    if (x != s_bgb_scroll_x) {
        s_bgb_scroll_x = x;
#if !defined(MG_STAGE_SOURCE_STREAM) && !defined(MG_ROUTE_FIGHT_BASE)
        VDP_setHorizontalScroll(BG_B, x);
#endif
    }
    if (y != s_bgb_scroll_y) {
        s_bgb_scroll_y = y;
#if !defined(MG_STAGE_SOURCE_STREAM) && !defined(MG_ROUTE_FIGHT_BASE)
        VDP_setVerticalScroll(BG_B, -y);
#endif
    }
#ifndef MG_TEST_DISABLE_STAGE3_FLASH
    if (sBackdropFlashFrames) {
        /* PAL0[0] e o backdrop da rota sem palco; sprites transparentes continuam transparentes. */
        backdrop_write(&kImpactBackdropColor);
        sBackdropFlashFrames--;
        sBackdropFlashActive = 1;
    } else if (sBackdropFlashActive) {
        backdrop_write(&sBaseBackdropColor);
        sBackdropFlashActive = 0;
    }
#endif
    for (u8 s = 0; s < 2; s++) {
        u8 lvl = mg_fight.flash_lvl[s];
        if (!lvl || !s_basepal[s]) continue;
        const CramConsumer *cons = s ? &CRAM_FLASH_P2 : &CRAM_FLASH_P1;
        /* lvl 1 = ultima passada: devolve a linha ao corpo original; acima, a tabela pre-montada */
        cram_write(cons, lvl == 1 ? &s_basepal[s][1] : s_flash_tab[s][lvl - 2]);
#ifdef MG_TEST_BODY_FLASH_HOLD
        if (lvl >= 3) continue;   /* diagnostico: congela o clareamento para a captura provar o caminho de CRAM */
#endif
        mg_fight.flash_lvl[s] = lvl - 1;
    }
}

static u16 fightTicksPerSecond(void)
{
    return SYS_isPAL() ? 50 : 60;
}

static u16 fightSecondsLeft(void)
{
    const u16 rate = fightTicksPerSecond();
    if (mg_fight.round_state == 0) return sRoundSeconds;
    if (mg_fight.round_state != 1 || mg_fight.round_timer <= 0) return 0;
    return (u16)((mg_fight.round_timer + rate - 1) / rate);
}

/* ------------------------------------------------------------------ som / explod */
static const MgSound *sAudioQueue[MG_AUDIO_QUEUE_CAPACITY];
static u32 sAudioQueueBorn[MG_AUDIO_QUEUE_CAPACITY];
static u8 sAudioQueueHead, sAudioQueueCount, sAudioQueuePeak;
static u16 sAudioQueueOverflow, sAudioQueueExpired;
static u16 sAudioQueueMaxAge = MG_AUDIO_QUEUE_MAX_AGE;
static u32 sAudioQueueClock;
static u8 sAudioQueueClockInjected;
/* SGDK timer.h declares/defines this volatile VInt clock. A weak reference
 * lets isolated legacy host stubs link; new deadline tests supply the symbol. */
extern volatile u32 vtimer __attribute__((weak));

static u32 audioQueueNow(void)
{
    return sAudioQueueClockInjected ? sAudioQueueClock : (&vtimer ? vtimer : 0);
}

static void audioQueueRebase(u32 old_now, u32 new_now)
{
    for (u8 n = 0; n < sAudioQueueCount; n++) {
        const u8 slot = (sAudioQueueHead + n) & MG_AUDIO_QUEUE_MASK;
        sAudioQueueBorn[slot] = new_now - (u32)(old_now - sAudioQueueBorn[slot]);
    }
}

void MG_fightAudioQueueSetClock(u32 now)
{
    if (!sAudioQueueClockInjected) audioQueueRebase(audioQueueNow(), now);
    sAudioQueueClock = now;
    sAudioQueueClockInjected = TRUE;
}

void MG_fightAudioQueueUseDefaultClock(void)
{
    if (!sAudioQueueClockInjected) return;
    const u32 old_now = audioQueueNow();
    sAudioQueueClockInjected = FALSE;
    audioQueueRebase(old_now, audioQueueNow());
}

void MG_fightAudioQueueSetMaxAge(u16 max_age) { sAudioQueueMaxAge = max_age; }

static void audioQueuePop(void)
{
    sAudioQueue[sAudioQueueHead] = 0;
    sAudioQueueBorn[sAudioQueueHead] = 0;
    sAudioQueueHead = (sAudioQueueHead + 1) & MG_AUDIO_QUEUE_MASK;
    sAudioQueueCount--;
}

static void audioQueueExpire(u32 now)
{
    while (sAudioQueueCount && sAudioQueueMaxAge &&
           (u32)(now - sAudioQueueBorn[sAudioQueueHead]) >= sAudioQueueMaxAge) {
        audioQueuePop();
        if (sAudioQueueExpired != 0xFFFF) sAudioQueueExpired++;
    }
}

static void audioQueuePush(const MgSound *sound)
{
    const u32 now = audioQueueNow();
    audioQueueExpire(now);
    if (sAudioQueueCount >= MG_AUDIO_QUEUE_CAPACITY) {
        if (sAudioQueueOverflow != 0xFFFF) sAudioQueueOverflow++;
        return;
    }
    const u8 slot = (sAudioQueueHead + sAudioQueueCount) & MG_AUDIO_QUEUE_MASK;
    sAudioQueue[slot] = sound;
    sAudioQueueBorn[slot] = now;
    sAudioQueueCount++;
    if (sAudioQueueCount > sAudioQueuePeak) sAudioQueuePeak = sAudioQueueCount;
}

void MG_fightAudioQueuePump(void)
{
    while (sAudioQueueCount) {
        audioQueueExpire(audioQueueNow());
        if (!sAudioQueueCount) break;
        const MgSound *sound = sAudioQueue[sAudioQueueHead];
        if (!sound || !XGM2_playPCM(sound->data, sound->len, SOUND_PCM_CH_AUTO)) break;
        audioQueuePop();
    }
}

void MG_fightAudioQueueReset(void)
{
    memset(sAudioQueue, 0, sizeof(sAudioQueue));
    memset(sAudioQueueBorn, 0, sizeof(sAudioQueueBorn));
    sAudioQueueHead = sAudioQueueCount = sAudioQueuePeak = 0;
    sAudioQueueOverflow = sAudioQueueExpired = 0;
}

u8 MG_fightAudioQueuePending(void) { return sAudioQueueCount; }
u8 MG_fightAudioQueuePeak(void) { return sAudioQueuePeak; }
u16 MG_fightAudioQueueOverflow(void) { return sAudioQueueOverflow; }
u16 MG_fightAudioQueueExpired(void) { return sAudioQueueExpired; }

void MG_playSound(const MgPlayer *p, s16 idx)
{
    if (!p || !p->def || !p->def->sounds || idx < 0 || idx >= (s16)p->def->nsounds) return;
    const MgSound *s = &p->def->sounds[idx];
    MG_CRUMB('P');
    /* Discard expired presentation events before a fresh event competes for space. */
    audioQueueExpire(audioQueueNow());
    if (sAudioQueueCount || !XGM2_playPCM(s->data, s->len, SOUND_PCM_CH_AUTO)) audioQueuePush(s);
}

void MG_playSoundSfx(const MgPlayer *p, s16 idx)
{
    if (sSfxEnabled) MG_playSound(p, idx);
}

void MG_playVoice(const MgPlayer *p, s16 idx)
{
    if (sVoiceEnabled) MG_playSound(p, idx);
}

__attribute__((weak)) MgSoundCategory MG_soundCategory(const MgPlayer *p, const MgSound *sound)
{
    (void)p; (void)sound;
    return MG_SOUND_EFFECT;
}

void MG_playMugenSound(const MgPlayer *p, s16 idx)
{
    if (!p || !p->def || !p->def->sounds || idx < 0 || idx >= (s16)p->def->nsounds) return;
    if (MG_soundCategory(p, &p->def->sounds[idx]) == MG_SOUND_VOICE) MG_playVoice(p, idx);
    else MG_playSoundSfx(p, idx);
}

static u8 fx80_explod(const MgExplod *e)
{
    if (!e->active || e->bind_owner >= 2) return 0;
    const MgPlayer *owner = &mg_fight.p[e->bind_owner];
    const MgCharDef *anim_def = e->anim_def ? e->anim_def : owner->def;
    return anim_def && e->anim_idx < anim_def->nanims && anim_def->anims[e->anim_idx].id == 8060;
}

#ifdef MG_FX_TRACE
static void fx80_record(u8 owner, u8 event, u8 slot, u8 elem,
                        s16 elem_time, s16 removetime, u16 anim_time,
                        s16 x, s16 y, u16 power)
{
    MDRuntimeProbe_recordFx80(gApp.sceneFrames, (u16)mg_fight.ticks, owner, event,
                              slot, elem, elem_time, removetime, anim_time, x, y, power);
}

static void fx80_record_power(const MgPlayer *p)
{
    fx80_record(1, MD_FX80_EVENT_P2_POWER, 0xFF, 0, 0, 0, 0,
                FX2I(p->x), FX2I(p->y), (u16)p->power);
}
#endif

/* Faiscas da fonte compartilhada (Ryu S8000..S8050) servem a quem nao tem faisca propria. */
#define MG_SHARED_SPARK_FIRST 8000
#define MG_SHARED_SPARK_LAST  8050

static u16 sExplodOverflow;
u16 MG_fightExplodOverflow(void) { return sExplodOverflow; }

static MgExplod *explod_spawn(MgPlayer *owner, s16 anim, mgfx x, mgfx y, s16 removetime, s16 id,
                              s8 facing, u8 is_spark)
{
    if (!owner || !owner->def || owner->side >= 2) return 0;
    if (MG_fightDemoFxHidden()) return 0;
    if (anim == 8060 && !sFx.fx8060) return 0;
    const MgCharDef *anim_def = owner->def;
    s16 idx = MG_findAnim(anim_def, anim);
    if (idx < 0 && mg_fight.shared_fx_def &&
        (anim == mg_fight.shared_fx_anim_id ||
         (is_spark && sFx.shared_spark && anim >= MG_SHARED_SPARK_FIRST && anim <= MG_SHARED_SPARK_LAST))) {
        anim_def = mg_fight.shared_fx_def;
        idx = MG_findAnim(anim_def, anim);
    }
    if (idx < 0) return 0;
    if (anim_def == owner->def) {
        /* Explod que vira fundo do super segue super_bgfx; os demais seguem fx (ou sparks). */
        u8 is_bgfx = FALSE;
        for (u8 i = 0; i < owner->def->nbgfx && i < MG_MAX_BGFX; i++)
            if (owner->def->bgfx[i].anim_id == anim && s_bgfx_base[owner->side][i]) is_bgfx = TRUE;
        if (is_bgfx ? !sFx.super_bgfx : (!is_spark && sFx.fx == MG_FX_OFF)) return 0;
    } else if (!is_spark && sFx.fx == MG_FX_OFF) {
        return 0;
    }
    MgExplod *e = 0;
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++) if (!mg_fight.explod[i].active) { e = &mg_fight.explod[i]; break; }
    if (!e) { /* reject newest; admitted effects retain ownership and age */
        if (sExplodOverflow != 0xFFFF) sExplodOverflow++;
        return 0;
    }
#ifdef MG_FX_TRACE
    u8 slot = (u8)(e - mg_fight.explod);
    if (fx80_explod(e)) {
        const MgPlayer *old_owner = &mg_fight.p[e->bind_owner];
        fx80_record(e->bind_owner, MD_FX80_EVENT_REPLACED, slot, e->elem,
                    e->elem_time, e->removetime, (u16)e->anim_time,
                    FX2I(e->x), FX2I(e->y), (u16)old_owner->power);
    }
#endif
    /* Sheet indices belong to their character definition. A recycled Explod
     * cannot keep sprites allocated from a different source definition. */
    if (e->anim_def && e->anim_def != anim_def) {
        MG_drawRelease(&e->dr);
        MG_drawInit(&e->dr);
    }
    MgDraw keep = e->dr;
    memset(e, 0, sizeof(*e));
    e->dr = keep;
    e->active = 1;
    e->id = id;
    e->anim_idx = idx;
    e->anim_def = anim_def;
    e->x = x;
    e->y = y;
    e->facing = facing;
    e->removetime = removetime;
    e->bind_owner = owner->side;
    e->depth = -5;
    e->bgfx = -1;
    if (anim_def == owner->def)
        for (u8 i = 0; i < owner->def->nbgfx && i < MG_MAX_BGFX; i++)
            if (owner->def->bgfx[i].anim_id == anim && s_bgfx_base[owner->side][i]) e->bgfx = i;
#ifdef MG_FX_TRACE
    if (anim == 8060)
        fx80_record(owner->side, MD_FX80_EVENT_SPAWN, slot, e->elem,
                    e->elem_time, e->removetime, (u16)e->anim_time,
                    FX2I(e->x), FX2I(e->y), (u16)owner->power);
#endif
    e->spark = is_spark;
    return e;
}

MgExplod *MG_spawnExplod(MgPlayer *owner, s16 anim, mgfx x, mgfx y, s16 removetime, s16 id, s8 facing)
{
    return explod_spawn(owner, anim, x, y, removetime, id, facing, FALSE);
}

/* ------------------------------------------------------------------ caixas */
typedef struct { s16 x1, y1, x2, y2; } Rect;

static Rect world_box(const MgBox *b, mgfx x, mgfx y, s8 facing)
{
    Rect r;
    s16 px = FX2I(x), py = FX2I(y);
    if (facing > 0) { r.x1 = px + b->x1; r.x2 = px + b->x2; }
    else { r.x1 = px - b->x2; r.x2 = px - b->x1; }
    r.y1 = py + b->y1;
    r.y2 = py + b->y2;
    return r;
}

static u8 overlap(const Rect *a, const Rect *b)
{
    return a->x1 <= b->x2 && b->x1 <= a->x2 && a->y1 <= b->y2 && b->y1 <= a->y2;
}

#ifdef MG_BOUNDS_TRACE
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
#error "BND1 requires draw_part submissions; MG_DRAW_CACHE can skip them"
#endif
enum {
    BND_F_CONTACT = 1u << 0,
    BND_F_ATTACKER_P2 = 1u << 1,
    BND_F_AUXILIARY_CONTACT = 1u << 2,
    BND_F_GUARDED = 1u << 3,
    BND_F_RESOLVE_RAN = 1u << 4,
    BND_F_PUSHBOX_MOVED = 1u << 5,
    BND_F_CLAMP_P1 = 1u << 6,
    BND_F_CLAMP_P2 = 1u << 7,
    BND_F_CORNER_PUSH_P1 = 1u << 8,
    BND_F_CORNER_PUSH_P2 = 1u << 9,
    BND_F_BOUNDS_COMPLETE = 1u << 10,
    BND_F_CAMERA_MOVED = 1u << 11,
    BND_F_RENDER_P1_VALID = 1u << 12,
    BND_F_RENDER_P2_VALID = 1u << 13,
    BND_F_HORIZONTAL_CLIPPED = 1u << 14,
    BND_F_VERTICAL_CLIPPED = 1u << 15
};

/* Payload: contact[0..3], pre-resolve[4..7], post-resolve[8..11],
 * post-bounds[12..15], camera[16..17], shake[18..19], screen cell bounds
 * P1/P2[20..27], screen axes P1/P2[28..31], submitted cell counts[32..33]. */
static u16 s_boundsFlags;
static u16 s_boundsPayload[34];
static u8 s_boundsActive;
static u8 s_boundsRenderValid[2];
static u16 s_boundsRenderCount[2];
static s16 s_boundsRender[2][4];
static u32 s_boundsLastSparseTick;
static u8 s_boundsHasSparseTick;
static u8 s_boundsClampFrameMask;
static u8 s_boundsClampPreviousMask;
static u8 s_boundsCornerFrameMask;
static u8 s_boundsCornerPreviousMask;

static void bounds_trace_begin(void)
{
    memset(s_boundsPayload, 0, sizeof(s_boundsPayload));
    memset(s_boundsRenderValid, 0, sizeof(s_boundsRenderValid));
    memset(s_boundsRenderCount, 0, sizeof(s_boundsRenderCount));
    s_boundsFlags = 0;
    s_boundsClampFrameMask = 0;
    s_boundsCornerFrameMask = 0;
    s_boundsActive = TRUE;
    s_boundsPayload[16] = (u16)FX2I(mg_fight.camx);
}

static void bounds_trace_capture_axes(u16 payload_offset)
{
    for (u8 side = 0; side < 2; side++) {
        const MgPlayer *p = &mg_fight.p[side];
        s_boundsPayload[payload_offset + side * 2] = (u16)FX2I(p->x);
        s_boundsPayload[payload_offset + side * 2 + 1] = (u16)FX2I(p->y);
    }
}

static void bounds_trace_note_contact(const Rect *hit, u8 attacker_side, u8 auxiliary, u8 guarded)
{
    if (!s_boundsActive || (s_boundsFlags & BND_F_CONTACT)) return;
    s_boundsFlags |= BND_F_CONTACT;
    if (attacker_side != 0) s_boundsFlags |= BND_F_ATTACKER_P2;
    if (auxiliary) s_boundsFlags |= BND_F_AUXILIARY_CONTACT;
    if (guarded) s_boundsFlags |= BND_F_GUARDED;
    s_boundsPayload[0] = (u16)hit->x1;
    s_boundsPayload[1] = (u16)hit->y1;
    s_boundsPayload[2] = (u16)hit->x2;
    s_boundsPayload[3] = (u16)hit->y2;
}

static void bounds_trace_pause_finalize(void)
{
    bounds_trace_capture_axes(4);
    bounds_trace_capture_axes(8);
    bounds_trace_capture_axes(12);
    s_boundsPayload[17] = (u16)FX2I(mg_fight.camx);
}

static void bounds_trace_bounds_complete(void)
{
    bounds_trace_capture_axes(12);
    s_boundsPayload[17] = (u16)FX2I(mg_fight.camx);
    s_boundsFlags |= BND_F_BOUNDS_COMPLETE;
}

static void bounds_trace_render_begin(void)
{
    if (!s_boundsActive) return;
    s_boundsPayload[17] = (u16)FX2I(mg_fight.camx);
    s_boundsPayload[18] = (u16)mg_fight.shake_x;
    s_boundsPayload[19] = (u16)mg_fight.shake_y;
    if (s_boundsPayload[16] != s_boundsPayload[17]) s_boundsFlags |= BND_F_CAMERA_MOVED;
    memset(s_boundsRenderValid, 0, sizeof(s_boundsRenderValid));
    memset(s_boundsRenderCount, 0, sizeof(s_boundsRenderCount));
}

static void bounds_trace_note_render_axis(u8 side, s16 x, s16 y)
{
    if (!s_boundsActive || side >= 2) return;
    const u16 offset = (u16)(28 + side * 2);
    s_boundsPayload[offset] = (u16)x;
    s_boundsPayload[offset + 1] = (u16)y;
}

static void bounds_trace_note_body_cell(const MgDraw *dr, s16 x, s16 y, u8 width, u8 height)
{
    if (!s_boundsActive) return;
    u8 side;
    if (dr == &mg_fight.p[0].dr) side = 0;
    else if (dr == &mg_fight.p[1].dr) side = 1;
    else return;

    s16 right = (s16)(x + width), bottom = (s16)(y + height);
    if (!s_boundsRenderValid[side]) {
        s_boundsRender[side][0] = x;
        s_boundsRender[side][1] = y;
        s_boundsRender[side][2] = right;
        s_boundsRender[side][3] = bottom;
        s_boundsRenderValid[side] = TRUE;
    } else {
        if (x < s_boundsRender[side][0]) s_boundsRender[side][0] = x;
        if (y < s_boundsRender[side][1]) s_boundsRender[side][1] = y;
        if (right > s_boundsRender[side][2]) s_boundsRender[side][2] = right;
        if (bottom > s_boundsRender[side][3]) s_boundsRender[side][3] = bottom;
    }
    if (s_boundsRenderCount[side] != 0xFFFFu) s_boundsRenderCount[side]++;
}

static void bounds_trace_finish_render(void)
{
    if (!s_boundsActive) return;
    const u8 clampRise = s_boundsClampFrameMask & (u8)~s_boundsClampPreviousMask;
    const u8 cornerRise = s_boundsCornerFrameMask & (u8)~s_boundsCornerPreviousMask;
    if (clampRise & 0x01u) s_boundsFlags |= BND_F_CLAMP_P1;
    if (clampRise & 0x02u) s_boundsFlags |= BND_F_CLAMP_P2;
    if (cornerRise & 0x01u) s_boundsFlags |= BND_F_CORNER_PUSH_P1;
    if (cornerRise & 0x02u) s_boundsFlags |= BND_F_CORNER_PUSH_P2;
    s_boundsClampPreviousMask = s_boundsClampFrameMask;
    s_boundsCornerPreviousMask = s_boundsCornerFrameMask;
    u8 candidate = (s_boundsFlags & (BND_F_CONTACT | BND_F_PUSHBOX_MOVED | BND_F_CLAMP_P1 |
                                    BND_F_CLAMP_P2 | BND_F_CORNER_PUSH_P1 | BND_F_CORNER_PUSH_P2)) != 0;
    for (u8 side = 0; side < 2; side++) {
        const u16 payload_offset = (u16)(20 + side * 4);
        s_boundsPayload[32 + side] = s_boundsRenderCount[side];
        if (!s_boundsRenderValid[side]) continue;
        const s16 left = s_boundsRender[side][0], top = s_boundsRender[side][1];
        const s16 right = s_boundsRender[side][2], bottom = s_boundsRender[side][3];
        s_boundsPayload[payload_offset] = (u16)left;
        s_boundsPayload[payload_offset + 1] = (u16)top;
        s_boundsPayload[payload_offset + 2] = (u16)right;
        s_boundsPayload[payload_offset + 3] = (u16)bottom;
        s_boundsFlags |= side == 0 ? BND_F_RENDER_P1_VALID : BND_F_RENDER_P2_VALID;
        if (left < 0 || right > 320) s_boundsFlags |= BND_F_HORIZONTAL_CLIPPED;
        if (top < 0 || bottom > 224) s_boundsFlags |= BND_F_VERTICAL_CLIPPED;
        /* A 48 px horizontal margin includes the fight_base idle P2 cell
         * (right=273). Use 32 px so the trace starts on actual edge approach. */
        if (left < 32 || right > 288 || top < 48 || bottom > 224) candidate = TRUE;
    }

    const u16 urgent = BND_F_CONTACT | BND_F_CLAMP_P1 | BND_F_CLAMP_P2 |
                       BND_F_CORNER_PUSH_P1 | BND_F_CORNER_PUSH_P2;
    u8 verticalSweepSample = 0;
#ifdef MG_BOUNDS_TRACE_VERTICAL_SWEEP
    verticalSweepSample = (mg_fight.p[0].y != 0 || mg_fight.p[1].y != 0);
    if (verticalSweepSample) candidate = TRUE;
#endif
    if (candidate && !(s_boundsFlags & urgent) && !verticalSweepSample) {
        if (s_boundsHasSparseTick && mg_fight.ticks - s_boundsLastSparseTick < 120u) candidate = FALSE;
        else {
            s_boundsLastSparseTick = mg_fight.ticks;
            s_boundsHasSparseTick = TRUE;
        }
    }

    if (candidate) {
        u16 words[MD_BOUNDS_TRACE_WORD_COUNT];
        const u32 presented_frame = gApp.totalFrames + 1u;
        words[0] = (u16)(presented_frame >> 16);
        words[1] = (u16)presented_frame;
        words[2] = (u16)(gApp.sceneFrames + 1u);
        words[3] = (u16)mg_fight.ticks;
        words[4] = s_boundsFlags;
        for (u8 i = 0; i < 34; i++) words[5 + i] = s_boundsPayload[i];
        MDRuntimeProbe_recordBounds(words);
    }
    s_boundsActive = FALSE;
}
#endif /* MG_BOUNDS_TRACE */

/* alguma Clsn1 do quadro de ataque encosta em alguma Clsn2 do defensor?
 * Se sim, devolve em *hit a intersecao do primeiro par que colidiu (ponto de contato real). */
static u8 frames_collide(const MgCharDef *ad, const MgAnimFrame *af, mgfx ax, mgfx ay, s8 afc,
                         const MgPlayer *d, Rect *hit)
{
    const MgAnimFrame *df = &d->def->frames[d->def->anims[d->anim_idx].first + d->elem];
    if (!af->nclsn1 || !df->nclsn2) return 0;
    for (u8 i = 0; i < af->nclsn1; i++) {
        Rect r1 = world_box(&ad->boxes[af->clsn + i], ax, ay, afc);
        for (u8 j = 0; j < df->nclsn2; j++) {
            Rect r2 = world_box(&d->def->boxes[df->clsn + df->nclsn1 + j], d->x, d->y, d->facing);
            if (overlap(&r1, &r2)) {
                hit->x1 = r1.x1 > r2.x1 ? r1.x1 : r2.x1;
                hit->x2 = r1.x2 < r2.x2 ? r1.x2 : r2.x2;
                hit->y1 = r1.y1 > r2.y1 ? r1.y1 : r2.y1;
                hit->y2 = r1.y2 < r2.y2 ? r1.y2 : r2.y2;
                return 1;
            }
        }
    }
    return 0;
}

static const MgAnimFrame *cur_frame(const MgPlayer *p)
{
    return &p->def->frames[p->def->anims[p->anim_idx].first + p->elem];
}

#ifndef MG_EDGE_RENDER_MARGIN_MAX
/* Margem visual de borda (px por lado): o eixo MUGEN so chega a min(extensao das celulas do quadro, MAX)
 * da borda da tela. 0 desliga. E adaptacao do perfil sem cenario, nao regra do MUGEN: o clamp por
 * Width edge limita o eixo, nao as celulas desenhadas (ver doc/agent_learning/fight_base_axis_vs_render_bounds_20261005.md). */
#define MG_EDGE_RENDER_MARGIN_MAX 40
#endif
#if MG_EDGE_RENDER_MARGIN_MAX > 0 || defined(MG_TEST_FIGHT_BASE_RENDER_BOUND_CLAMP) || defined(MG_TEST_HOOKS)
#if defined(MG_TEST_FIGHT_BASE_RENDER_BOUND_CLAMP) && !defined(MG_ROUTE_FIGHT_BASE)
#error "render-bound clamp diagnostic requires the stage-free fight_base route"
#endif
/* Cache por lado dos limites horizontais das celulas do quadro atual, relativos ao eixo e ja com facing/flip. */
static const MgCharDef *sEdgeBoundsDef[2];
static const MgAnimFrame *sEdgeBoundsFrame[2];
static s8 sEdgeBoundsFacing[2];
static s16 sEdgeBoundsLeft[2], sEdgeBoundsRight[2];

static u8 frameRenderBounds(const MgPlayer *p, s16 *left, s16 *right)
{
    if (!p->def || p->side >= 2 || p->anim_idx >= p->def->nanims) return 0;
    const MgAnim *anim = &p->def->anims[p->anim_idx];
    if (p->elem >= anim->count) return 0;
    const MgAnimFrame *f = &p->def->frames[anim->first + p->elem];
    const u8 side = p->side;
    if (sEdgeBoundsDef[side] != p->def || sEdgeBoundsFrame[side] != f ||
        sEdgeBoundsFacing[side] != p->facing) {
        s16 minX = 0x7FFF, maxX = -0x7FFF;
        u8 n = f->sheet < 0 ? 0 : (f->nparts ? f->nparts : 1);
        if (n > MG_MAX_PARTS) n = MG_MAX_PARTS;
        for (u8 k = 0; k < n; k++) {
            const s16 sheet = k ? p->def->parts[f->part + k - 1].sheet : f->sheet;
            if (sheet < 0 || sheet >= p->def->nsheets) continue;
            const MgSheet *sh = &p->def->sheets[sheet];
            const u8 flip = (p->facing < 0) ^ ((f->flags & MG_FRAME_HFLIP) != 0);
            const s16 x = MG_FACE(f->ox, p->facing) -
                (flip ? (s16)(sh->cell_w - sh->axis_x) : sh->axis_x);
            const s16 x2 = x + sh->cell_w;
            if (x < minX) minX = x;
            if (x2 > maxX) maxX = x2;
        }
        sEdgeBoundsDef[side] = p->def;
        sEdgeBoundsFrame[side] = f;
        sEdgeBoundsFacing[side] = p->facing;
        sEdgeBoundsLeft[side] = minX;
        sEdgeBoundsRight[side] = maxX;
    }
    *left = sEdgeBoundsLeft[side];
    *right = sEdgeBoundsRight[side];
    return *left != 0x7FFF && *right != -0x7FFF;
}
#endif

/* hitflag: H=pe L=agachado A=ar F=caindo D=deitado ; + so em gethit ; - so fora de gethit */
static u8 can_hit(const MgHitDef *h, const MgPlayer *d)
{
    if (d->nothitby_time > 0 && (h->attr & d->nothitby_attr & 0x7) && (h->attr & d->nothitby_attr & 0x770)) return 0;
    if ((h->hitflag & 64) && d->movetype != 'H') return 0;
    if ((h->hitflag & 128) && d->movetype == 'H') return 0;
    switch (d->statetype) {
    case 'S': return (h->hitflag & 1) != 0;
    case 'C': return (h->hitflag & 2) != 0;
    case 'A': return (h->hitflag & 4) || (d->gh_fall && (h->hitflag & 8));
    case 'L': return (h->hitflag & 16) != 0;
    }
    return 1;
}

static u8 guards(const MgHitDef *h, const MgPlayer *d, s8 attacker_side_dir)
{
    if (d->movetype == 'H' && !(d->stateno >= 150 && d->stateno <= 155)) return 0;
    u8 in_guard = d->stateno >= 120 && d->stateno <= 155;
    u8 back = d->def->cmd_holdback != MG_NONE && d->cmd_timer[d->def->cmd_holdback];
    if (!in_guard && !(d->ctrl && back)) return 0;
    if (!in_guard && attacker_side_dir != d->facing) return 0;     /* ataque vindo por tras */
    switch (d->statetype) {
    case 'S': return (h->guardflag & 1) != 0;
    case 'C': return (h->guardflag & 2) != 0;
    case 'A': return (h->guardflag & 4) != 0;
    }
    return 0;
}

/* Faisca ancorada no ponto de contato (centro da intersecao Clsn1 x Clsn2).
 * Divergencia deliberada do MUGEN (que usa borda frontal + sparkxy): leitura de onde o golpe acertou.
 * Acertos seguidos na mesma regiao (<=16 px, <=90 ticks) percorrem 4 variacoes sutis (jitter). */
#define SPARK_REGION 16
#define SPARK_WINDOW 90
#define SPARK_DUPLICATE_REGION 27
static const s8 kSparkJitter[4][2] = { { 0, 0 }, { 3, -2 }, { -3, 2 }, { 2, 3 } };
static u32 sSpark8050LastTick;
static s16 sSpark8050LastX, sSpark8050LastY;
static u8 sSpark8050LastOwner, sSpark8050LastValid;
#ifdef MG_TEST_CAPTURE_VDP_STATE
static u16 sSpark8050ProbeCalls;
static u32 sSpark8050ProbePrevTick, sSpark8050ProbeCurrTick;
static s16 sSpark8050ProbePrevX, sSpark8050ProbePrevY;
static s16 sSpark8050ProbeCurrX, sSpark8050ProbeCurrY;
static s16 sSpark8050ProbeDx, sSpark8050ProbeDy;
static u8 sSpark8050ProbePrevOwner, sSpark8050ProbeCurrOwner;
static u8 sSpark8050ProbeSameTick, sSpark8050ProbeOppositeOwner;
static u8 sSpark8050ProbeWithin16, sSpark8050ProbeWithinThreshold, sSpark8050ProbeSuppressed;
#endif

/* Intensidade do contato para escolher a faisca compartilhada. */
#define MG_SPARK_GUARD  0
#define MG_SPARK_LIGHT  1
#define MG_SPARK_MEDIUM 2
#define MG_SPARK_HEAVY  3

/* Faisca comum sem pacote fightfx: usa a faisca da fonte compartilhada pela intensidade
 * (defesa S8040, leve S8010, media S8020, pesada S8030). */
static s16 shared_spark_anim(u8 level)
{
    static const s16 kShared[4] = { 8040, 8010, 8020, 8030 };
    return kShared[level & 3];
}

static void spark(MgPlayer *owner, s16 anim, const Rect *hit, s8 afc, const MgPlayer *def, u8 level)
{
    if (sFx.sparks == MG_FX_OFF) return;
    if (anim == MG_SPARK_COMMON) {
        if (!sFx.shared_spark || !mg_fight.shared_fx_def) return;
        anim = shared_spark_anim(level);
    }
    if (anim < 0) return;
#ifdef MG_TEST_SUPPRESS_SPARKNO_8010
    /* Diagnostico isolado: omite so o hit spark 8010; nao muda contato/dano/hitpause. */
    if (anim == 8010) return;
#endif
#ifdef MG_TEST_SUPPRESS_SPARKNO_8050
    /* O Hadouken normal (state 1000) declara sparkno=s8050 na fonte MUGEN. */
    if (anim == 8050) return;
#endif
#ifdef MG_TEST_SUPPRESS_SPARKNO_8050_P2_OWNER
    /* Diagnostico: remove apenas o 8050 produzido pelo golpe do dono P2,
     * mantendo o hit spark de P1, flash, projeteis e a logica do impacto. */
    if (anim == 8050 && owner->side == 1) return;
#endif
#ifdef MG_TEST_SUPPRESS_SPARKNO_8060
    /* Diagnostico do Super Hadouken: omite so o hit spark 8060. */
    if (anim == 8060) return;
#endif
    s16 cx = (hit->x1 + hit->x2) >> 1, cy = (hit->y1 + hit->y2) >> 1;
#ifdef MG_TEST_CAPTURE_VDP_STATE
    if (anim == 8050) {
        if (sSpark8050ProbeCalls) {
            sSpark8050ProbePrevTick = sSpark8050ProbeCurrTick;
            sSpark8050ProbePrevOwner = sSpark8050ProbeCurrOwner;
            sSpark8050ProbePrevX = sSpark8050ProbeCurrX;
            sSpark8050ProbePrevY = sSpark8050ProbeCurrY;
            sSpark8050ProbeDx = cx - sSpark8050ProbePrevX;
            sSpark8050ProbeDy = cy - sSpark8050ProbePrevY;
            sSpark8050ProbeSameTick = sSpark8050ProbePrevTick == mg_fight.ticks;
            sSpark8050ProbeOppositeOwner = sSpark8050ProbePrevOwner != owner->side;
            sSpark8050ProbeWithin16 = abs(sSpark8050ProbeDx) <= 16 && abs(sSpark8050ProbeDy) <= 16;
            sSpark8050ProbeWithinThreshold = abs(sSpark8050ProbeDx) <= SPARK_DUPLICATE_REGION &&
                abs(sSpark8050ProbeDy) <= SPARK_DUPLICATE_REGION;
        }
        sSpark8050ProbeCurrTick = mg_fight.ticks;
        sSpark8050ProbeCurrOwner = owner->side;
        sSpark8050ProbeCurrX = cx;
        sSpark8050ProbeCurrY = cy;
        sSpark8050ProbeCalls++;
    }
#endif
    /* Opposing 8050 sparks from the same simulation tick visually collide when
     * their measured contact anchors are within 27 px on each axis. Keep one
     * composed impact; both hit events and their gameplay effects still run. */
    if (anim == 8050) {
        if (sSpark8050LastValid && sSpark8050LastTick == mg_fight.ticks &&
            sSpark8050LastOwner != owner->side &&
            abs(cx - sSpark8050LastX) <= SPARK_DUPLICATE_REGION &&
            abs(cy - sSpark8050LastY) <= SPARK_DUPLICATE_REGION) {
#ifdef MG_TEST_CAPTURE_VDP_STATE
            sSpark8050ProbeSuppressed = 1;
#endif
            return;
        }
        sSpark8050LastTick = mg_fight.ticks;
        sSpark8050LastX = cx;
        sSpark8050LastY = cy;
        sSpark8050LastOwner = owner->side;
        sSpark8050LastValid = 1;
    }
    /* regiao relativa ao corpo do defensor (o empurrao do golpe nao "muda de regiao") */
    s16 rx = cx - FX2I(def->x), ry = cy - FX2I(def->y);
    if (abs(rx - owner->spark_last_x) <= SPARK_REGION && abs(ry - owner->spark_last_y) <= SPARK_REGION &&
        mg_fight.ticks - owner->spark_last_tick <= SPARK_WINDOW)
        owner->spark_var = (owner->spark_var + 1) & 3;
    else
        owner->spark_var = 0;
    owner->spark_last_x = rx;
    owner->spark_last_y = ry;
    owner->spark_last_tick = mg_fight.ticks;
    s16 jx = kSparkJitter[owner->spark_var][0] * afc, jy = kSparkJitter[owner->spark_var][1];
    explod_spawn(owner, anim, FXI(cx + jx), FXI(cy + jy), -2, -1, afc, TRUE);
}

/* aplica o acerto/defesa. Projectile/helper herdam hitpause do HitDef de seu dono. */
static void apply_hit(MgPlayer *a, MgPlayer *d, const MgHitDef *h, u8 from_proj, const Rect *hit, s8 afc)
{
    u8 g = guards(h, d, -afc);
#ifdef MG_BOUNDS_TRACE
    bounds_trace_note_contact(hit, a->side, from_proj, g);
#endif
    d->target = 0;
    if (!from_proj) a->target = d;
    if (g) {
        mg_fight.guard_event_count[d->side]++;
        s32 dmg = h->guard_damage;
        if (!h->guard_kill && d->life - dmg <= 0) dmg = d->life - 1;
        d->life -= dmg;
        a->moveguarded = a->movecontact = 1;
        a->contact_fresh = 1;
        a->hitpause = h->gpause_p1;
        d->hitshake = h->gpause_p2;
        d->hittime_left = h->ghittime;
        d->gh = *h;
        d->gh_guarded = 1;
        d->gh_fall = 0;
        d->gh_vx = h->guardvel_x;
        d->gh_vy = 0;
        d->sdef = d->def;
        MG_changeState(d, d->statetype == 'C' ? 152 : (d->statetype == 'A' ? 154 : 150), 0, -1);
        MG_playSoundSfx(a, h->guardsound);
        spark(a, h->guard_sparkno, hit, afc, d, MG_SPARK_GUARD);
        return;
    }
    mg_fight.hit_event_count[d->side]++;
    s32 dmg = h->damage;
    if (!h->kill && d->life - dmg <= 0) dmg = d->life - 1;
    d->life -= dmg;
    if (d->life < 0) d->life = 0;
    a->movehit = a->movecontact = 1;
    a->contact_fresh = 1;
    a->hitcount++;
    a->hitpause = h->pause_p1;
    a->power += h->getpower;
    d->power += h->givepower;
    if (a->power > MG_POWERMAX(a)) a->power = MG_POWERMAX(a);
    if (d->power > MG_POWERMAX(d)) d->power = MG_POWERMAX(d);
    /* combo: continua se o defensor ja estava em atordoamento (movetype H) */
    if (d->movetype == 'H' && mg_fight.combo[a->side]) mg_fight.combo[a->side]++;
    else mg_fight.combo[a->side] = 1;
    mg_fight.combo_tick[a->side] = mg_fight.ticks;
    d->gh = *h;
    d->gh_guarded = 0;
    d->hitshake = h->pause_p2;
    u8 downed = d->statetype == 'L';
    u8 was_airborne = !downed && (d->y < 0 || d->statetype == 'A');
    u8 air = !downed && (was_airborne || h->gvel_y != 0);
    if (downed) {
        d->gh_vx = h->down_vx;
        d->gh_vy = h->down_vy;
        if (h->down_vy == 0) {
            d->hittime_left = h->down_hittime;
            d->gh_fall = 0;                         /* down.hittime returns to lie state */
        } else {
            d->hittime_left = h->airhittime;        /* down.hittime is ignored for Y launch */
            d->gh_fall = h->airfall;
            air = 1;
        }
    } else if (air) {
        /* A grounded launch still consumes ground.velocity and fall. */
        d->gh_vx = was_airborne ? h->avel_x : h->gvel_x;
        d->gh_vy = was_airborne ? h->avel_y : h->gvel_y;
        d->hittime_left = h->airhittime;
        d->gh_fall = was_airborne ? h->airfall : h->fall;
    } else {
        d->gh_vx = h->gvel_x;
        d->gh_vy = h->gvel_y;
        d->hittime_left = h->hittime;
        d->gh_fall = h->fall;
    }
    if ((sTrainingMode || sContinuousSession || sDemoShowcase) && d->life <= 0) d->life = 1;
    if (d->life <= 0) {                        /* KO: sempre cai */
        d->gh_fall = 1;
        if (d->gh_vy >= 0) d->gh_vy = h->fall_yvel;
        if (d->gh_vx == 0) d->gh_vx = -FXI(3);
    }
    if (d->facing == afc) { d->facing = -afc; }           /* vira para o atacante */
    impact_fx(d, dmg, afc);
    MG_playSoundSfx(a, h->hitsound);
    spark(a, h->sparkno, hit, afc, d,
          (d->gh_fall || d->life <= 0 || dmg >= MG_HEAVY_DAMAGE) ? MG_SPARK_HEAVY
          : (dmg >= MG_HEAVY_DAMAGE / 2 ? MG_SPARK_MEDIUM : MG_SPARK_LIGHT));
    if (h->p2stateno >= 0 && !from_proj) {
        d->sdef = a->sdef;                                 /* custom state do atacante */
        MG_changeState(d, h->p2stateno, 0, -1);
        a->target = d;
    } else {
        d->sdef = d->def;
        s16 st = (air || d->gh_fall) ? 5020 : (downed ? 5080 : (d->statetype == 'C' ? 5010 : 5000));
        MG_changeState(d, st, 0, -1);
    }
    if (h->p1stateno >= 0 && !from_proj) MG_changeState(a, h->p1stateno, -1, -1);
}

#ifdef MG_TEST_HOOKS
u8 MG_testFrameRenderBounds(const MgPlayer *p, s16 *left, s16 *right) { return frameRenderBounds(p, left, right); }
#endif
#ifdef MG_TEST_HOOKS
void MG_testApplyHit(MgPlayer *attacker, MgPlayer *defender, const MgHitDef *hitdef)
{
    const Rect contact = { 0, 0, 0, 0 };
    apply_hit(attacker, defender, hitdef, 0, &contact, attacker->facing);
}

void MG_testApplyProjectileHit(MgPlayer *attacker, MgPlayer *defender, const MgHitDef *hitdef)
{
    const Rect contact = { 0, 0, 0, 0 };
    apply_hit(attacker, defender, hitdef, 1, &contact, attacker->facing);
}
#endif

/* ReversalDef: o defensor reverte o golpe em vez de sofrer dano. Vale para golpe corpo a corpo cujo attr casa
 * com reversal.attr e cuja caixa toca o defensor; projeteis nao sao revertidos (README). */
static u8 try_reversal(MgPlayer *a, MgPlayer *d)
{
    if (!d->rev || !a->hitdef_active || a->movetype != 'A' || a->hitpause) return 0;
    MgHitDef rh;
    MG_readReversal(d, d->rev, &rh);
    if (!((a->hd.attr & rh.attr & 0x7) && (a->hd.attr & rh.attr & 0x770))) return 0;
    Rect hit;
    if (!frames_collide(a->def, cur_frame(a), a->x, a->y, a->facing, d, &hit)) return 0;
    a->hitdef_active = 0;
    d->hitpause = rh.pause_p1;
    a->hitpause = rh.pause_p2;
    d->target = a;
    d->movehit = d->movecontact = 1;
    if (rh.p2stateno >= 0) { a->sdef = d->sdef; MG_changeState(a, rh.p2stateno, -1, -1); }
    if (rh.p1stateno >= 0) MG_changeState(d, rh.p1stateno, -1, -1);
    return 1;
}

#ifdef MG_NAV_DIAG
u8 mg_nav_gate[2];
#endif
static void resolve_hits(void)
{
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *a = &mg_fight.p[s], *d = a->enemy;
        /* golpe corpo a corpo */
        Rect hit;
        if (try_reversal(a, d)) continue;
#ifdef MG_NAV_DIAG
        {   /* diagnostico: quais gates do golpe corpo a corpo passaram (OR desde o inicio do HitDef ativo) */
            static u8 sPrevActive[2];
            if (a->hitdef_active && !sPrevActive[s]) mg_nav_gate[s] = 0;
            if (a->hitdef_active)
                mg_nav_gate[s] |= (u8)(1u | (a->movetype == 'A' ? 2u : 0u) | (a->hitpause == 0 ? 4u : 0u) |
                                       (can_hit(&a->hd, d) ? 8u : 0u) |
                                       (frames_collide(a->def, cur_frame(a), a->x, a->y, a->facing, d, &hit) ? 16u : 0u));
            sPrevActive[s] = a->hitdef_active;
        }
#endif
        if (a->hitdef_active && a->movetype == 'A' && a->hitpause == 0 && can_hit(&a->hd, d) &&
            frames_collide(a->def, cur_frame(a), a->x, a->y, a->facing, d, &hit)) {
            a->hitdef_active = 0;              /* um HitDef = um acerto */
            apply_hit(a, d, &a->hd, 0, &hit, a->facing);
        }
        /* helper: acerta como projetil do dono (dano/poder/combo pertencem ao dono; geometria e do helper) */
        for (u8 k = 0; k < MG_MAX_HELPERS; k++) {
            MgPlayer *h = &mg_fight.helper[s][k];
            if (mg_fight.helper_active[s][k] && h->hitdef_active && h->movetype == 'A' && h->hitpause == 0 &&
                can_hit(&h->hd, d) && frames_collide(h->def, cur_frame(h), h->x, h->y, h->facing, d, &hit)) {
                h->hitdef_active = 0;
                h->movehit = h->movecontact = 1;
                apply_hit(a, d, &h->hd, 1, &hit, h->facing);
            }
        }
        /* projeteis */
        for (u8 i = 0; i < MG_MAX_PROJ; i++) {
            MgProj *pr = &a->proj[i];
            if (!pr->active || pr->removing) continue;
            const MgAnimFrame *pf = &a->def->frames[a->def->anims[pr->anim_idx].first + pr->elem];
            if (!can_hit(&pr->hd, d) || !frames_collide(a->def, pf, pr->x, pr->y, pr->facing, d, &hit)) continue;
            apply_hit(a, d, &pr->hd, 1, &hit, pr->facing);
            pr->contact_time = 0;
            if (--pr->hits <= 0) {
                s16 idx = pr->hitanim >= 0 ? MG_findAnim(a->def, pr->hitanim) : -1;
                if (idx >= 0) {
                    pr->anim_idx = idx; pr->elem = 0; pr->elem_time = 0;
                    pr->vx = pr->vy = pr->ax = pr->ay = 0;
                    pr->removing = 1;
                    pr->removetime = 0x7FFF;
                } else pr->active = 0;
            }
        }
    }
    /* projetil x projetil: se anulam */
    for (u8 i = 0; i < MG_MAX_PROJ; i++) {
        MgProj *p1 = &mg_fight.p[0].proj[i];
        if (!p1->active || p1->removing) continue;
        for (u8 j = 0; j < MG_MAX_PROJ; j++) {
            MgProj *p2 = &mg_fight.p[1].proj[j];
            if (!p2->active || p2->removing) continue;
            s16 dx = FX2I(p1->x - p2->x), dy = FX2I(p1->y - p2->y);
            if (abs(dx) < 24 && abs(dy) < 24) { p1->active = 0; p2->active = 0; break; }   /* um par por projetil */
        }
    }
}

/* ------------------------------------------------------------------ empurrao / limites / camera */
static void push_and_bounds(void)
{
    MgPlayer *a = &mg_fight.p[0], *b = &mg_fight.p[1];
#ifdef MG_BOUNDS_TRACE
    const mgfx pushStartX[2] = { a->x, b->x };
#endif
    if (a->y > -FXI(8) && b->y > -FXI(8) && a->sdef == a->def && b->sdef == b->def && !a->nopush && !b->nopush) {
        mgfx wa = a->def->consts->ground_front, wb = b->def->consts->ground_front;
        mgfx dx = b->x - a->x;
        mgfx need = wa + wb;
        mgfx adx = dx < 0 ? -dx : dx;
        if (adx < need) {
            mgfx overlap = need - adx;
            if (!a->hitpause_active_tick && !b->hitpause_active_tick) {
                mgfx push = overlap >> 1;
                if (dx >= 0) { a->x -= push; b->x += push; }
                else { a->x += push; b->x -= push; }
            } else if (!a->hitpause_active_tick) {
                if (dx >= 0) a->x -= overlap; else a->x += overlap;
            } else if (!b->hitpause_active_tick) {
                if (dx >= 0) b->x += overlap; else b->x -= overlap;
            }
        }
    }
#ifdef MG_BOUNDS_TRACE
    if (a->x != pushStartX[0] || b->x != pushStartX[1]) s_boundsFlags |= BND_F_PUSHBOX_MOVED;
#endif
    mgfx cornerLoss[2] = { 0, 0 };
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *p = &mg_fight.p[s];
        if (p->freebound || p->hitpause_active_tick) continue;
#if defined(MG_TEST_FIGHT_BASE_CAMERA_WIDE_NO_ZERO_EDGE_CLAMP)
        /* Diagnostic only: determine whether zero MUGEN width edges are the
         * condition that pins an actor to the moving viewport edge. */
        if (p->edge_f == 0 && p->edge_b == 0) continue;
#endif
        /* Margem da borda da TELA (Width edge), nao a largura de empurrao. Padrao 0:
           o eixo encosta na borda e FrontEdgeDist pode ser 0. ScreenBound 0 pula isto. */
        mgfx front = FXI(p->edge_f), back = FXI(p->edge_b);
        mgfx lo = FXI(mg_fight.camx) + (p->facing > 0 ? back : front);
        mgfx hi = FXI(mg_fight.camx + 320) - (p->facing > 0 ? front : back);
#if MG_EDGE_RENDER_MARGIN_MAX > 0
        {   /* o corpo desenhado fica na tela: mesma posicao serve a colisao, ao pushback e ao render */
            s16 rl, rr;
            if (frameRenderBounds(p, &rl, &rr)) {
                const s16 ml = rl < 0 ? (s16)(-rl) : 0, mr = rr > 0 ? rr : 0;
                /* a camera anda ate 4 px DEPOIS deste clamp (fim de push_and_bounds): folga para o quadro nao cortar */
                const mgfx rlo = FXI(mg_fight.camx) + FXI((ml > MG_EDGE_RENDER_MARGIN_MAX ? MG_EDGE_RENDER_MARGIN_MAX : ml) + (ml ? 4 : 0));
                const mgfx rhi = FXI(mg_fight.camx + 320) - FXI((mr > MG_EDGE_RENDER_MARGIN_MAX ? MG_EDGE_RENDER_MARGIN_MAX : mr) + (mr ? 4 : 0));
                if (rlo > lo) lo = rlo;
                if (rhi < hi) hi = rhi;
            }
        }
#endif
        if (lo > hi) lo = hi = (lo + hi) >> 1;
        {
            /* Pushback de canto: o deslocamento que a borda da tela tira de um defensor em hit/guard
             * (knockback e empurrao) volta, no sentido oposto, para quem o acertou corpo a corpo.
             * Projetil/helper nao entram (a->target so e definido para golpe direto). */
            const mgfx before = p->x;
            if (p->x < lo) p->x = lo;
            if (p->x > hi) p->x = hi;
#ifdef MG_BOUNDS_TRACE
            if (p->x != before) s_boundsClampFrameMask |= (u8)(1u << s);
#endif
            if (p->x != before && p->movetype == 'H') {
                MgPlayer *at = p->enemy;
                if (at && at->target == p && !at->freebound) cornerLoss[at->side] += before - p->x;
            }
        }
#ifdef MG_TEST_FIGHT_BASE_RENDER_BOUND_CLAMP
        /* A zero width edge can place the actor axis on the viewport border
         * while the actual MUGEN sprite cell extends beyond it. Adjust only
         * the diagnostic actor position enough to contain its current frame. */
        {
            s16 renderLeft, renderRight;
            if (frameRenderBounds(p, &renderLeft, &renderRight) &&
                renderRight - renderLeft <= 320) {
                const s16 axisX = FX2I(p->x) - mg_fight.camx + mg_fight.shake_x;
                if (axisX + renderLeft < 0)
                    p->x += FXI(-(axisX + renderLeft));
                else if (axisX + renderRight > 320)
                    p->x -= FXI(axisX + renderRight - 320);
            }
        }
#endif
    }
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *at = &mg_fight.p[s];
        if (!cornerLoss[s] || at->hitpause_active_tick) continue;
#ifdef MG_BOUNDS_TRACE
        const mgfx cornerStartX = at->x;
#endif
        at->x -= cornerLoss[s];   /* perda positiva = parede direita: atacante recua para a esquerda */
#ifdef MG_BOUNDS_TRACE
        if (at->x != cornerStartX) s_boundsCornerFrameMask |= (u8)(1u << s);
#endif
        {   /* o atacante recuado tambem respeita a borda da tela */
            mgfx front = FXI(at->edge_f), back = FXI(at->edge_b);
            mgfx lo = FXI(mg_fight.camx) + (at->facing > 0 ? back : front);
            mgfx hi = FXI(mg_fight.camx + 320) - (at->facing > 0 ? front : back);
            if (lo > hi) lo = hi = (lo + hi) >> 1;
#ifdef MG_BOUNDS_TRACE
            const mgfx beforeCornerClamp = at->x;
#endif
            if (at->x < lo) at->x = lo;
            if (at->x > hi) at->x = hi;
#ifdef MG_BOUNDS_TRACE
            if (at->x != beforeCornerClamp) s_boundsClampFrameMask |= (u8)(1u << s);
#endif
        }
    }
    s32 mid = (FX2I(a->x) + FX2I(b->x)) / 2 - 160;
    if (mid < mg_fight.stage_left) mid = mg_fight.stage_left;
    if (mid > mg_fight.stage_right - 320) mid = mg_fight.stage_right - 320;
    s32 d = mid - mg_fight.camx;
    if (d > 4) d = 4;
    if (d < -4) d = -4;
    mg_fight.camx += d;
}

/* ------------------------------------------------------------------ render */
/* Spare tile banks belong only to the guarded fight_base VDP layout.
 * Static ownership maps avoid loop allocation and cannot cross table holes. */
#ifdef MG_SPARE_TILE_BANKS
static const u16 sSpareBase[2] = { 0xF800 / 32, 0xD000 / 32 };
static const u16 sSpareCapacity[2] = { 64, 128 };
static u8 sSpareUsed[192], sSpareEnabled;
static u16 sSpareLive, sSparePeak, sSpareAllocations;

static u16 spare_alloc(u16 need)
{
    if (!sSpareEnabled || !need || need > 128) return 0;
    u16 offset = 0;
    for (u8 bank = 0; bank < 2; bank++) {
        if (need <= sSpareCapacity[bank]) {
            u16 run = 0;
            for (u16 i = 0; i < sSpareCapacity[bank]; i++) {
                run = sSpareUsed[offset + i] ? 0 : run + 1;
                if (run == need) {
                    const u16 first = i + 1 - need;
                    memset(&sSpareUsed[offset + first], 1, need);
                    sSpareLive += need;
                    if (sSpareLive > sSparePeak) sSparePeak = sSpareLive;
                    sSpareAllocations++;
                    return sSpareBase[bank] + first;
                }
            }
        }
        offset += sSpareCapacity[bank];
    }
    return 0;
}

static void spare_free(MgDraw *d, u8 k)
{
    if (!d->spare_base[k]) return;
    const u8 bank = d->spare_base[k] >= sSpareBase[0] ? 0 : 1;
    const u16 offset = bank ? 64 : 0;
    memset(&sSpareUsed[offset + d->spare_base[k] - sSpareBase[bank]], 0, d->spare_size[k]);
    sSpareLive -= d->spare_size[k];
    d->spare_base[k] = d->spare_size[k] = 0;
}

void MG_fightSpareStats(u16 *live, u16 *peak, u16 *allocations, u16 *enabled)
{
    *live = sSpareLive; *peak = sSparePeak;
    *allocations = sSpareAllocations; *enabled = sSpareEnabled;
}
#endif

/* Allocation failure events: diagnostic-only SRAM, independent of window1290.
 * SRAM0x1800..0x1e5f is outside breadcrumbs0x1000 and first64 FEVT records.
 * Keep first16 failures across fight epochs; count all and expose truncation.
 * No pixels, allocation policy, retry or gameplay are changed by this flag. */
#ifdef MG_ALLOC_FAILURE_EVENTS
#define ALFT_OFFSET 0x1800
#define ALFT_CAPACITY 16
#define ALFT_WORDS 25
static u32 sAllocFrame, sAllocSceneFrame, sAllocEpoch, sAllocTotal, sAllocCount;
static u32 sAllocRecord[ALFT_WORDS];

void MG_fightSetAllocFrame(u32 totalFrame, u32 sceneFrame)
{
    sAllocFrame = totalFrame; sAllocSceneFrame = sceneFrame;
}

static void alloc_trace_header(void)
{
    SRAM_enable();
    SRAM_writeLong(ALFT_OFFSET, 0x414C4654); /* ALFT */
    SRAM_writeLong(ALFT_OFFSET + 4, 1);
    SRAM_writeLong(ALFT_OFFSET + 8, ALFT_WORDS);
    SRAM_writeLong(ALFT_OFFSET + 12, ALFT_CAPACITY);
    SRAM_writeLong(ALFT_OFFSET + 16, sAllocCount);
    SRAM_writeLong(ALFT_OFFSET + 20, sAllocTotal);
    SRAM_writeLong(ALFT_OFFSET + 24, sAllocEpoch);
    SRAM_disable();
}

static void alloc_trace_failure(const MgDraw *dr, u8 part, s16 sheet, u8 frame,
                                const SpriteDefinition *original, const SpriteDefinition *request,
                                u16 freeBefore, u16 largestBefore, u16 target, u8 site)
{
    const MgPlayer *owner = 0;
    u16 kind = 255, side = 65535, index = 65535, anim = 65535;
    for (u8 s = 0; s < 2; s++) {
        const MgPlayer *p = &mg_fight.p[s];
        if (dr == &p->dr) { owner = p; kind = 0; side = s; index = 0; anim = p->anim_idx; }
        for (u8 i = 0; i < MG_MAX_PROJ; i++)
            if (dr == &p->proj[i].dr) { owner = p; kind = 1; side = s; index = i; anim = p->proj[i].anim_idx; }
        for (u8 i = 0; i < MG_MAX_HELPERS; i++)
            if (dr == &mg_fight.helper[s][i].dr) {
                owner = &mg_fight.helper[s][i]; kind = 2; side = s; index = i; anim = owner->anim_idx;
            }
    }
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++)
        if (dr == &mg_fight.explod[i].dr) {
            side = mg_fight.explod[i].bind_owner;
            if (side < 2) owner = &mg_fight.p[side];
            kind = 3; index = i; anim = mg_fight.explod[i].anim_idx;
        }
    sAllocTotal++;
    if (sAllocCount < ALFT_CAPACITY) {
        u16 live = 0, peak = 0;
#ifdef MG_SPARE_TILE_BANKS
        u16 allocations, enabled;
        MG_fightSpareStats(&live, &peak, &allocations, &enabled);
#endif
        sAllocRecord[0] = sAllocFrame; sAllocRecord[1] = sAllocSceneFrame;
        sAllocRecord[2] = sAllocEpoch; sAllocRecord[3] = sAllocTotal;
        sAllocRecord[4] = (u32)(unsigned long)original;
        sAllocRecord[5] = site; sAllocRecord[6] = kind; sAllocRecord[7] = side;
        sAllocRecord[8] = index; sAllocRecord[9] = part; sAllocRecord[10] = (u16)sheet;
        sAllocRecord[11] = frame; sAllocRecord[12] = request->maxNumTile;
        sAllocRecord[13] = request->maxNumSprite;
        sAllocRecord[14] = freeBefore; sAllocRecord[15] = largestBefore;
        sAllocRecord[16] = SPR_getFreeVRAM(); sAllocRecord[17] = SPR_getLargestFreeVRAMBlock();
        sAllocRecord[18] = target; sAllocRecord[19] = SPR_getNumActiveSprite();
        sAllocRecord[20] = owner ? (u16)owner->stateno : 65535;
        sAllocRecord[21] = anim; sAllocRecord[22] = owner ? (u32)owner->time : 0;
        sAllocRecord[23] = live; sAllocRecord[24] = peak;
        SRAM_enable();
        for (u16 i = 0; i < ALFT_WORDS; i++)
            SRAM_writeLong(ALFT_OFFSET + 32 + sAllocCount * (ALFT_WORDS * 4) + i * 4, sAllocRecord[i]);
        SRAM_disable();
        sAllocCount++;
    }
    alloc_trace_header();
}
#endif

static void draw_release_part(MgDraw *d, u8 k)
{
#ifdef MG_DRAW_OWNERSHIP
    d->owned_parts &= (u8)~(1u << k);
#endif
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
    d->cache_valid = 0;
#endif
    if (d->spr[k]) SPR_releaseSprite(d->spr[k]);
    d->spr[k] = 0; d->sheet[k] = -1;
#ifdef MG_SPARE_TILE_BANKS
    spare_free(d, k);
#endif
}

void MG_drawInit(MgDraw *d)
{
    for (u8 i = 0; i < MG_MAX_PARTS; i++) { d->spr[i] = 0; d->sheet[i] = -1; }
    d->fixed0 = 0;
#ifdef MG_DRAW_OWNERSHIP
    d->owned_parts = 0;
#endif
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
    d->cache_valid = 0;
#endif
#ifdef MG_SPARE_TILE_BANKS
    memset(d->spare_base, 0, sizeof(d->spare_base));
    memset(d->spare_size, 0, sizeof(d->spare_size));
#endif
}

void MG_drawRelease(MgDraw *d)
{
#ifdef MG_DRAW_OWNERSHIP
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
    d->cache_valid = 0;
#endif
    if (!d->owned_parts) return;
    for (u8 i = 0; i < MG_MAX_PARTS; i++)
        if (d->owned_parts & (1u << i)) draw_release_part(d, i);
#else
    for (u8 i = 0; i < MG_MAX_PARTS; i++)
        draw_release_part(d, i);
#endif
}

static void draw_priority(MgDraw *d, bool priority)
{
    for (u8 k = 0; k < MG_MAX_PARTS; k++)
        if (d->spr[k]) SPR_setPriority(d->spr[k], priority);
}

static void hud_overlay_apply(u8 visible)
{
    visible = visible != 0;
    if (visible == sHudOverlay) return;
    sHudOverlay = visible;
    for (u8 s = 0; s < 2; s++) {
        draw_priority(&mg_fight.p[s].dr, !visible);
        for (u8 k = 0; k < MG_MAX_PROJ; k++) draw_priority(&mg_fight.p[s].proj[k].dr, !visible);
        for (u8 k = 0; k < MG_MAX_HELPERS; k++) draw_priority(&mg_fight.helper[s][k].dr, !visible);
    }
    for (u8 k = 0; k < MG_MAX_EXPLOD; k++) draw_priority(&mg_fight.explod[k].dr, !visible);
}

/* Message and interface/debug intents have independent lifetimes. */
static u8 sHudMessage, sHudInterface;
void MG_fightHudOverlay(u8 visible)
{
    sHudMessage = visible != 0;
    hud_overlay_apply(sHudMessage || sHudInterface);
}
void MG_fightHudOverlayInterface(u8 visible)
{
    sHudInterface = visible != 0;
    hud_overlay_apply(sHudMessage || sHudInterface);
}

/* Fixed reservations never grow into the next owner or the live sprite pool.
 * Re-evaluate before cache reuse as well as before creating/uploading a part. */
static u16 body_vram_target(u16 base, u16 tiles)
{
    if (!base) return 0;
    if (!((base == s_vram[0] && tiles <= s_vram_cap[0]) ||
          (base == s_vram[1] && tiles <= s_vram_cap[1])) ||
        (u32)base + tiles > TILE_SPRITE_INDEX) return 0;
    return base;
}

/* desenha uma parte (sheet/frame) no slot k do objeto */
static void draw_part(const MgCharDef *d, MgDraw *dr, u8 k, s16 sheet, u8 frame, u8 fflags, s16 ox, s16 oy,
                      mgfx x, mgfx y, s8 facing, u16 body_pal, s16 depth, u16 vram)
{
    MG_CRUMB('D');
    const MgSheet *sh = &d->sheets[sheet];
    u16 pal = sh->pal ? PAL3 : body_pal;
    Sprite **spr = &dr->spr[k];
    /* guarda: sheet maior que a reserva (nao observado no Ken) vai ao pool neste quadro,
     * em vez de transbordar a VRAM vizinha; volta ao slot fixo quando o sheet couber */
    if (vram && k == 0) vram = body_vram_target(vram, sh->def->maxNumTile);
    if (*spr && k == 0 && dr->fixed0 != (vram != 0)) draw_release_part(dr, k);
#ifdef MG_FRAME_TILE_ALLOC
    const SpriteDefinition *render_def = sh->def;
    if (!(vram && k == 0) && sh->def->numAnimation && sh->def->animations &&
        frame < sh->def->animations[0]->numFrame) {
        const AnimationFrame *next_frame = sh->def->animations[0]->frames[frame];
        const u16 tiles = next_frame->tileset->numTile;
        const u16 sprites = next_frame->numSprite & 0x7F;
        /* Release before changing a descriptor still owned by a Sprite.
         * Grow within a sheet; a new sheet starts with its actual frame size. */
        if (*spr && (dr->sheet[k] != sheet || tiles > dr->part_def[k].maxNumTile ||
                     sprites > dr->part_def[k].maxNumSprite)) {
            draw_release_part(dr, k);
        }
        if (!*spr) {
            dr->part_def[k] = *sh->def;
            dr->part_def[k].maxNumTile = tiles ? tiles : 1;
            dr->part_def[k].maxNumSprite = sprites ? sprites : 1;
        }
        render_def = &dr->part_def[k];
    }
#else
    const SpriteDefinition *render_def = sh->def;
#endif
    /* SGDK frees an auto-VRAM block before growing it in setDefinition.
     * A failed reallocation leaves the old sprite pointing at released tiles.
     * Recreate size-changing dynamic parts, with a clean retry on failure. */
    if (*spr && !(vram && k == 0) && dr->sheet[k] != sheet && dr->sheet[k] >= 0 &&
        d->sheets[dr->sheet[k]].def->maxNumTile != sh->def->maxNumTile) {
        draw_release_part(dr, k);
    }
    if (!*spr) {
        if (k == 0) dr->fixed0 = vram != 0;
#ifdef MG_SPARE_TILE_BANKS
        u16 target = (vram && k == 0) ? vram : spare_alloc(render_def->maxNumTile);
        if (target && !(vram && k == 0)) {
            dr->spare_base[k] = target;
            dr->spare_size[k] = render_def->maxNumTile;
        }
#else
        const u16 target = (vram && k == 0) ? vram : 0;
#endif
#ifdef MG_ALLOC_FAILURE_EVENTS
        const u16 freeBefore = SPR_getFreeVRAM(), largestBefore = SPR_getLargestFreeVRAMBlock();
#endif
#ifdef MG_PEAK_TRACE
        if (mg_peak_enabled) {
            const MgPeakFrame *pf = MG_peakCurrent();
            const u16 free = SPR_getFreeVRAM();
            const u16 used = pf->pool_capacity > free ? pf->pool_capacity - free : 0;
            MG_peakDemand(SPR_getUsedVDPSprite() + render_def->maxNumSprite,
                          target ? used : used + render_def->maxNumTile,
                          SPR_getLargestFreeVRAMBlock(), 0);
        }
#endif
        *spr = target ? SPR_addSpriteEx(render_def, 0, 0, TILE_ATTR_FULL(pal, !sHudOverlay, FALSE, FALSE, target),
                                                   SPR_FLAG_AUTO_TILE_UPLOAD)
                                : SPR_addSpriteEx(render_def, 0, 0, TILE_ATTR(pal, !sHudOverlay, FALSE, FALSE),
                                                   SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
        if (!*spr) {
#ifdef MG_ALLOC_FAILURE_EVENTS
            alloc_trace_failure(dr, k, sheet, frame, sh->def, render_def, freeBefore, largestBefore, target, 1);
#endif
#ifdef MG_SPARE_TILE_BANKS
            spare_free(dr, k);
#endif
#ifdef MG_PEAK_TRACE
            if (mg_peak_enabled) MG_peakDemand(0, 0, SPR_getLargestFreeVRAMBlock(), 1);
#endif
            sSpriteFailures++; return;
        }
#ifdef MG_DRAW_OWNERSHIP
        dr->owned_parts |= (u8)(1u << k);
#endif
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
        /* MUGEN owns frame timing. An unchanged draw can skip its setters
         * only when the SGDK animation timer cannot advance independently. */
        SPR_setAutoAnimation(*spr, FALSE);
#endif
        dr->sheet[k] = sheet;
    } else if (dr->sheet[k] != sheet) {
#ifdef MG_ALLOC_FAILURE_EVENTS
        const u16 freeBefore = SPR_getFreeVRAM(), largestBefore = SPR_getLargestFreeVRAMBlock();
#endif
        if (!SPR_setDefinition(*spr, render_def)) {
#ifdef MG_ALLOC_FAILURE_EVENTS
            u16 target = (vram && k == 0) ? vram : 0;
#ifdef MG_SPARE_TILE_BANKS
            if (!target) target = dr->spare_base[k];
#endif
            alloc_trace_failure(dr, k, sheet, frame, sh->def, render_def, freeBefore, largestBefore, target, 2);
#endif
#ifdef MG_PEAK_TRACE
            if (mg_peak_enabled) MG_peakDemand(0, 0, SPR_getLargestFreeVRAMBlock(), 1);
#endif
            sSpriteFailures++; SPR_setVisibility(*spr, HIDDEN); return;
        }
        dr->sheet[k] = sheet;
    }
    SPR_setAnimAndFrame(*spr, 0, frame);
    u8 flip = (facing < 0) ^ ((fflags & MG_FRAME_HFLIP) != 0);
    SPR_setHFlip(*spr, flip);
    SPR_setVFlip(*spr, (fflags & MG_FRAME_VFLIP) != 0);
    SPR_setPalette(*spr, pal);
    s16 px = FX2I(x) - mg_fight.camx + mg_fight.shake_x;
    s16 py = mg_fight.floor_y + FX2I(y) + mg_fight.shake_y;
    s16 sx = px + MG_FACE(ox, facing) - (flip ? (s16)(sh->cell_w - sh->axis_x) : sh->axis_x);
    s16 sy = py + oy - sh->axis_y;
    SPR_setPosition(*spr, sx, sy);
#ifdef MG_BOUNDS_TRACE
    bounds_trace_note_body_cell(dr, sx, sy, sh->cell_w, sh->cell_h);
#endif
    SPR_setDepth(*spr, depth);
#ifdef MG_SUBSPRITE_CULL
    /* SGDK checks every hardware rectangle at the edges. Keep all visible
     * pixels while avoiding SAT entries for wholly offscreen rectangles. */
    SPR_setVisibility(*spr, AUTO_SLOW);
#else
    SPR_setVisibility(*spr, VISIBLE);
#endif
}

static void draw(const MgCharDef *d, MgDraw *dr, u16 anim_idx, u8 elem,
                 mgfx x, mgfx y, s8 facing, u16 body_pal, s16 depth, u8 visible, u16 vram)
{
    const MgAnimFrame *f = &d->frames[d->anims[anim_idx].first + elem];
    if (vram && f->sheet >= 0)
        vram = body_vram_target(vram, d->sheets[f->sheet].def->maxNumTile);
#ifdef MG_BOUNDS_TRACE
    if (dr == &mg_fight.p[0].dr)
        bounds_trace_note_render_axis(0, FX2I(x) - mg_fight.camx + mg_fight.shake_x,
                                      mg_fight.floor_y + FX2I(y) + mg_fight.shake_y);
    else if (dr == &mg_fight.p[1].dr)
        bounds_trace_note_render_axis(1, FX2I(x) - mg_fight.camx + mg_fight.shake_x,
                                      mg_fight.floor_y + FX2I(y) + mg_fight.shake_y);
#endif
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
    const s16 px = FX2I(x) - mg_fight.camx + mg_fight.shake_x;
    const s16 py = mg_fight.floor_y + FX2I(y) + mg_fight.shake_y;
    /* Superpause is a scheduling window, not a promise of static pixels.
     * Reuse only an identical full draw key. Moving owner, shake, input and
     * ignorehitpause controllers continue normally. */
    const u8 reuse =
#ifdef MG_DRAW_CACHE
        1;
#else
        mg_fight.pause_time || mg_fight.round_state != 1 ||
        mg_fight.p[0].hitpause_active_tick || mg_fight.p[1].hitpause_active_tick;
#endif
    if (reuse && dr->cache_valid && dr->cached_def == d && dr->cached_frame == f &&
        dr->cached_x == px && dr->cached_y == py && dr->cached_depth == depth &&
        dr->cached_vram == vram && dr->cached_pal == body_pal &&
        dr->cached_facing == facing && dr->cached_visible == visible) return;
    const u32 failures = sSpriteFailures;
#endif
    u8 n = (!visible || f->sheet < 0) ? 0 : (f->nparts ? f->nparts : 1);
    if (n > MG_MAX_PARTS) n = MG_MAX_PARTS;
    /* Free absent parts before requesting any tile block for the new frame. */
    for (u8 k = n; k < MG_MAX_PARTS; k++)
        if (dr->spr[k]) {
            if (k == 0 && dr->fixed0) SPR_setVisibility(dr->spr[k], HIDDEN);
            else {
                /* A part absent from this frame cannot reuse its tiles until
                 * another frame requests it. Return that dynamic block now;
                 * otherwise a hidden large FX keeps the pool fragmented. */
                draw_release_part(dr, k);
            }
        }
    if (n) draw_part(d, dr, 0, f->sheet, f->frame, f->flags, f->ox, f->oy, x, y, facing, body_pal, depth, vram);
    for (u8 k = 1; k < n; k++) {
        const MgFramePart *pt = &d->parts[f->part + k - 1];
        draw_part(d, dr, k, pt->sheet, pt->frame, f->flags, f->ox, f->oy, x, y, facing, body_pal, depth, 0);
    }
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
    dr->cached_def = d; dr->cached_frame = f;
    dr->cached_x = px; dr->cached_y = py; dr->cached_depth = depth;
    dr->cached_vram = vram; dr->cached_pal = body_pal;
    dr->cached_facing = facing; dr->cached_visible = visible;
    /* A failed part must retry even if every requested pixel is unchanged. */
    dr->cache_valid = sSpriteFailures == failures;
#endif
}

#ifdef MG_RENDER_PREPARE
static void draw_prepare(const MgCharDef *d, MgDraw *dr, u16 anim_idx, u8 elem, u16 vram)
{
    const MgAnimFrame *f = &d->frames[d->anims[anim_idx].first + elem];
    u8 n = f->sheet < 0 ? 0 : (f->nparts ? f->nparts : 1);
    if (n > MG_MAX_PARTS) n = MG_MAX_PARTS;
    for (u8 k = 0; k < MG_MAX_PARTS; k++) {
        if (!dr->spr[k]) continue;
        if (k >= n) {
            if (k == 0 && dr->fixed0) SPR_setVisibility(dr->spr[k], HIDDEN);
            else draw_release_part(dr, k);
            continue;
        }
        const MgFramePart *part = k ? &d->parts[f->part + k - 1] : 0;
        const s16 sheet = k ? part->sheet : f->sheet;
        const u8 frame = k ? part->frame : f->frame;
        const SpriteDefinition *def = d->sheets[sheet].def;
        u16 fixed = k == 0 ? vram : 0;
        if (fixed) fixed = body_vram_target(fixed, def->maxNumTile);
        if (k == 0 && dr->fixed0 != (fixed != 0)) { draw_release_part(dr, k); continue; }
        if (fixed) continue;
#ifdef MG_FRAME_TILE_ALLOC
        if (def->numAnimation && def->animations && frame < def->animations[0]->numFrame) {
            const AnimationFrame *next = def->animations[0]->frames[frame];
            if (dr->sheet[k] != sheet || next->tileset->numTile > dr->part_def[k].maxNumTile ||
                (next->numSprite & 0x7F) > dr->part_def[k].maxNumSprite)
                draw_release_part(dr, k);
            continue;
        }
#endif
        if (dr->sheet[k] != sheet && dr->sheet[k] >= 0 &&
            d->sheets[dr->sheet[k]].def->maxNumTile != def->maxNumTile)
            draw_release_part(dr, k);
    }
}
#endif

static u16 s_vram_next;
static u16 sVramAdmissionFailures;

u16 MG_fightVramNext(void) { return s_vram_next; }
u16 MG_fightVramAdmissionFailures(void) { return sVramAdmissionFailures; }

bool MG_fightReserveVram(u16 tiles, u16 *base)
{
    /* Recheck the current boundary on every call: the pool may have been
     * reconfigured since init. Widen before addition to prevent u16 wrap. */
    if (!base || !tiles || s_vram_next < TILE_USER_INDEX ||
        (u32)s_vram_next + tiles > TILE_SPRITE_INDEX) {
        if (sVramAdmissionFailures != 0xFFFF) sVramAdmissionFailures++;
        return FALSE;
    }
    *base = s_vram_next;
    s_vram_next += tiles;
    return TRUE;
}

bool MG_fightGetBgFxLoan(u16 *base, u16 *tileCount)
{
    if (!base || !tileCount) return FALSE;
    for (u8 side = 0; side < 2; side++) {
        const MgCharDef *def = mg_fight.p[side].def;
        if (!def) continue;
        for (u8 i = 0; i < MG_MAX_BGFX && i < def->nbgfx; i++) {
            if (!s_bgfx_base[side][i]) continue;
            *base = s_bgfx_base[side][i];
            *tileCount = def->bgfx[i].img->tileset->numTile;
            return TRUE;
        }
    }
    *base = 0;
    *tileCount = 0;
    return FALSE;
}

static void hud(void)
{
#ifdef MG_EXTERNAL_HUD
    return;                                  /* HUD do jogo (arte convertida) substitui o texto */
#endif
    if (MG_fightDemoSuperBarOnly()) {
        static s16 lastPow[2] = { -1, -1 };
        char digit[2];
        u8 s;
        for (s = 0; s < 2; s++) {
            s16 n = (s16)(mg_fight.p[s].power / 1000);
            if (n < 0) n = 0;
            if (n > 9) n = 9;
            if (n == lastPow[s]) continue;
            lastPow[s] = n;
            digit[0] = (char)('0' + n);
            digit[1] = 0;
            VDP_drawText(digit, s ? 38 : 1, 26);
        }
        return;
    }
    /* UI transitoria (texto): substituida por lifebar convertida na etapa de screenpack.
     * Redesenha so quando algum valor muda (VDP_drawText e caro no 68000). */
    static s16 last[5] = { -1, -1, -1, -1, -1 };
    s16 cur[5];
    for (u8 s = 0; s < 2; s++) {
        const MgPlayer *p = &mg_fight.p[s];
        s32 maxl = p->def->consts->life >> MG_FX_SHIFT;
        s16 n = maxl ? (s16)((p->life * 14) / maxl) : 0;
        cur[s * 2] = n < 0 ? 0 : n;
        cur[s * 2 + 1] = (s16)(p->power / 1000);
    }
    cur[4] = fightSecondsLeft();
    if (mg_fight.round_state != 1) cur[4] = -2 - mg_fight.round_state;
    char line[20];
    for (u8 s = 0; s < 2; s++) {
        if (cur[s * 2] == last[s * 2] && cur[s * 2 + 1] == last[s * 2 + 1]) continue;
        for (u8 i = 0; i < 14; i++) line[i] = i < cur[s * 2] ? '=' : '.';
        line[14] = '0' + cur[s * 2 + 1];
        line[15] = 0;
        VDP_drawText(line, s ? 24 : 1, 1);
    }
    if (cur[4] != last[4]) {
        s16 t = fightSecondsLeft();
        line[0] = '0' + (t / 10) % 10;
        line[1] = '0' + t % 10;
        line[2] = 0;
        VDP_drawText(line, 19, 1);
        VDP_drawText(mg_fight.round_state == 0 ? "ROUND" : "     ", 17, 10);
    }
    for (u8 i = 0; i < 5; i++) last[i] = cur[i];
}

/* efeito de fundo: tilemap em BG_B (baixa prioridade) + PAL0 1..14 trocada a cada elemento */
/* Deferred BGFX presentation. Simulation never appends DMA operations. */
static u8 sBgfxLeaseGranted, sBgfxReleasePending, sBgfxFatal, sBgfxRestoreQueued;
static s8 sBgfxPending = -1;
static const Image *sBgfxOwnedImage;
static u32 sBgfxRefusals[MG_BATCH_QUEUE_CONTRACT_BROKEN + 1];

static void bgfx_note(MgBatchStatus status)
{
    if (status != MG_BATCH_OK && sBgfxRefusals[status] != 0xFFFFFFFFu)
        sBgfxRefusals[status]++;
    if (status == MG_BATCH_QUEUE_CONTRACT_BROKEN) sBgfxFatal = TRUE;
}

u32 MG_fightVisualRefusals(u8 reason)
{
    return reason <= MG_BATCH_QUEUE_CONTRACT_BROKEN ? sBgfxRefusals[reason] : 0;
}

bool MG_fightSetBgFxLease(bool granted)
{
    /* The product promises exclusive BG_B/PAL0[1..14] ownership. A clear is
     * correct only for stage-free BG_B. Stage restoration needs another adapter. */
    if (!granted && (mg_fight.bgfx_active || sBgfxReleasePending)) return FALSE;
    sBgfxLeaseGranted = granted != 0; return TRUE;
}

/* Init/teardown caller has already drained/reset old scene DMA and VDP owners. */
static void bgfx_reset_visuals(void)
{
    sBgfxLeaseGranted = sBgfxReleasePending = sBgfxFatal = sBgfxRestoreQueued = 0;
    sBgfxPending = s_bgfx_owner = -1; sBgfxOwnedImage = 0;
    memset(sBgfxRefusals, 0, sizeof(sBgfxRefusals));
}

static void bgfx_render(MgExplod *e, const MgPlayer *o)
{
    const s8 index = (s8)(e - mg_fight.explod);
    (void)o;
    if (sBgfxPending < 0 || index == s_bgfx_owner) sBgfxPending = index;
}

void bgfx_release(void)
{
    sBgfxPending = -1;
    if (mg_fight.bgfx_active) sBgfxReleasePending = TRUE;
}

static void bgfx_end(void) { bgfx_release(); }

/* Call exactly once after SPR_update + every ordinary queue producer, then
 * immediately flush with SYS_doVBlankProcess. No game state update in between. */
void MG_fightQueueVisuals(void)
{
    MgExplod *e;
    const MgPlayer *owner;
    const MgBgFx *fx;
    MgBatchStatus status;
    u8 palette;
    if (sBgfxFatal) return;
    if (mg_fight.bgfx_active) {
        e = s_bgfx_owner >= 0 ? &mg_fight.explod[(u8)s_bgfx_owner] : 0;
        /* A slot can expire and be reused before render. shown is reset by
         * spawn, so the new instance must never inherit the old visual lease. */
        if (!e || !e->active || !e->bgfx_shown || e->bgfx < 0 || e->bind_owner >= 2 ||
            !mg_fight.p[e->bind_owner].def ||
            (u8)e->bgfx >= mg_fight.p[e->bind_owner].def->nbgfx ||
            mg_fight.p[e->bind_owner].def->bgfx[(u8)e->bgfx].img != sBgfxOwnedImage)
            sBgfxReleasePending = TRUE;
    }
    if (sBgfxReleasePending) {
        status = MG_bgfxQueueClear40x28(&mg_fight.pal0_saved[1], 0, sBgfxLeaseGranted);
        bgfx_note(status);
        if (status == MG_BATCH_OK) {
            mg_fight.bgfx_active = 0; s_bgfx_owner = -1;
            sBgfxReleasePending = 0; sBgfxOwnedImage = 0;
            sBgfxRestoreQueued = TRUE;
        }
        /* Restoration is still queued. Never capture a new saved palette
         * until the main loop has drained this batch at the following VBlank. */
        sBgfxPending = -1; return;
    }
    if (sBgfxPending < 0) return;
    e = &mg_fight.explod[(u8)sBgfxPending];
    if (!e->active || e->bgfx < 0 || e->bgfx >= MG_MAX_BGFX || e->bind_owner >= 2) {
        sBgfxPending = -1; return;
    }
    owner = &mg_fight.p[e->bind_owner];
    if (!owner->def || (u8)e->bgfx >= owner->def->nbgfx) { sBgfxPending = -1; return; }
    fx = &owner->def->bgfx[(u8)e->bgfx];
    if ((fx->nelem && !fx->elem_pal) || (fx->npals && !fx->pals)) {
        bgfx_note(MG_BATCH_INVALID); sBgfxPending = -1; return;
    }
    palette = e->elem < fx->nelem ? fx->elem_pal[e->elem] : 255;
    if (!sBgfxLeaseGranted) { bgfx_note(MG_BATCH_OWNER_BUSY); sBgfxPending = -1; return; }
    if (mg_fight.bgfx_active) {
        if (sBgfxPending == s_bgfx_owner && palette < fx->npals)
            bgfx_note(MG_bgfxQueuePalette14(&fx->pals[palette][1], 0, TRUE));
        sBgfxPending = -1; return;
    }
    {
        u16 unchanged_palette[14];
        const u16 *colors;
        MgBgfxBatch batch;
        if (palette < fx->npals) colors = &fx->pals[palette][1];
        else {
            /* No authored palette on this element: preserve the current one. */
            SYS_disableInts(); PAL_getColors(1, unchanged_palette, 14); SYS_enableInts();
            colors = unchanged_palette;
        }
        batch = (MgBgfxBatch){fx->img, colors, &mg_fight.pal0_saved[1],
            s_bgfx_base[owner->side][(u8)e->bgfx],
            s_bgfx_end[owner->side][(u8)e->bgfx], 0, 0, 0, TRUE};
        status = MG_bgfxQueueNone40x28(&batch); bgfx_note(status);
        if (status == MG_BATCH_OK) {
            e->bgfx_shown = TRUE; s_bgfx_owner = sBgfxPending;
            sBgfxOwnedImage = fx->img; mg_fight.bgfx_active = TRUE;
        }
    }
    sBgfxPending = -1;
}

void MG_fightRender(void)
{
    sBgfxPending = -1;
    MG_PEAK_MARK(MG_PK_FX_DRAW);
    MG_PROF_BEGIN();
    MG_CRUMB('k');
    impact_fx_step();
#ifdef MG_BOUNDS_TRACE
    bounds_trace_render_begin();
#endif
    /* Part zero can fail while later parts allocate successfully. Cleanup
     * must visit every slot, and happen before another actor requests VRAM. */
    for (u8 s = 0; s < 2; s++) {
        for (u8 i = 0; i < MG_MAX_PROJ; i++)
            if (!mg_fight.p[s].proj[i].active) MG_drawRelease(&mg_fight.p[s].proj[i].dr);
        for (u8 k = 0; k < MG_MAX_HELPERS; k++)
            if (!mg_fight.helper_active[s][k]) MG_drawRelease(&mg_fight.helper[s][k].dr);
    }
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++)
        if (!mg_fight.explod[i].active) {
            MG_drawRelease(&mg_fight.explod[i].dr);
            if (s_bgfx_owner == i) bgfx_end();
        }
#ifdef MG_RENDER_PREPARE
    /* Return every active owner's obsolete block before any new block is
     * requested. Render order/depth, animation timing and authored data stay intact. */
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *p = &mg_fight.p[s];
        draw_prepare(p->def, &p->dr, p->anim_idx, p->elem, s_vram[s]);
        for (u8 i = 0; i < MG_MAX_PROJ; i++) {
            MgProj *pr = &p->proj[i];
            if (pr->active) draw_prepare(p->def, &pr->dr, pr->anim_idx, pr->elem, 0);
        }
        for (u8 k = 0; k < MG_MAX_HELPERS; k++) {
            MgPlayer *h = &mg_fight.helper[s][k];
            if (mg_fight.helper_active[s][k]) draw_prepare(h->def, &h->dr, h->anim_idx, h->elem, 0);
        }
    }
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++) {
        MgExplod *e = &mg_fight.explod[i];
        if (e->active && e->bgfx < 0) {
            const MgCharDef *anim_def = e->anim_def ? e->anim_def : mg_fight.p[e->bind_owner].def;
            draw_prepare(anim_def, &e->dr, e->anim_idx, e->elem, 0);
        }
    }
#endif
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *p = &mg_fight.p[s];
        s16 depth = -(p->sprpriority * 4) - (s ? 1 : 0);
        MG_PEAK_MARK(s ? MG_PK_P2_DRAW : MG_PK_P1_DRAW);
        draw(p->def, &p->dr, p->anim_idx, p->elem, p->x, p->y, p->facing, p->pal, depth, 1, s_vram[s]);
        for (u8 i = 0; i < MG_MAX_PROJ; i++) {
            MgProj *pr = &p->proj[i];
            if (!pr->active) continue;
#ifndef MG_TEST_HIDE_PROJECTILE_RENDER
            draw(p->def, &pr->dr, pr->anim_idx, pr->elem, pr->x, pr->y,
                                 pr->facing, p->pal, -20, 1, 0);
#endif
        }
    }
    MG_PEAK_MARK(MG_PK_FX_DRAW);
    /* sombras: no chao sob cada lutador, profundidade maxima (atras de tudo e descartadas primeiro) */
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *p = &mg_fight.p[s];
        const SpriteDefinition *shadowDef = p->def->shadow;
#if MG_SHARED_SHADOW_FALLBACK || defined(MG_STUDY_FX80_BLINK)
        if (!shadowDef) shadowDef = sSharedShadow;
#endif
        if (!shadowDef) continue;
        if (!p->shadow_spr) {
#ifdef MG_PEAK_TRACE
            if (mg_peak_enabled) {
                const u16 free = SPR_getFreeVRAM(), cap = MG_peakCurrent()->pool_capacity;
                MG_peakDemand(SPR_getUsedVDPSprite() + shadowDef->maxNumSprite,
                              (cap > free ? cap - free : 0) + shadowDef->maxNumTile,
                              SPR_getLargestFreeVRAMBlock(), 0);
            }
#endif
            p->shadow_spr = SPR_addSpriteEx(shadowDef, 0, 0, TILE_ATTR(p->pal, FALSE, FALSE, FALSE),
                                            SPR_FLAG_AUTO_VRAM_ALLOC | SPR_FLAG_AUTO_TILE_UPLOAD);
            if (!p->shadow_spr) {
#ifdef MG_PEAK_TRACE
                if (mg_peak_enabled) MG_peakDemand(0, 0, SPR_getLargestFreeVRAMBlock(), 1);
#endif
                continue;
            }
            SPR_setDepth(p->shadow_spr, SPR_MAX_DEPTH);
        }
        SPR_setPosition(p->shadow_spr, FX2I(p->x) - mg_fight.camx - 16 + mg_fight.shake_x,
                        mg_fight.floor_y - 4 + mg_fight.shake_y);
        {
            const u8 odd = (u8)(mg_fight.ticks & 1u);
            u8 shadowHidden = mg_fight.bgfx_active;
            if (sFx.shadow == MG_FX_OFF) shadowHidden = TRUE;
            else if (sFx.shadow == MG_FX_BLINK) shadowHidden |= odd;
            else if (sFx.shadow == MG_SHADOW_ALTERNATE) shadowHidden |= (u8)(odd != s);   /* P1 par, P2 impar */
#ifdef MG_SUBSPRITE_CULL
            SPR_setVisibility(p->shadow_spr, shadowHidden ? HIDDEN : AUTO_SLOW);
#else
            SPR_setVisibility(p->shadow_spr, shadowHidden ? HIDDEN : VISIBLE);
#endif
        }
    }
    MG_PEAK_MARK(MG_PK_FX_DRAW);
    for (u8 s = 0; s < 2; s++)
        for (u8 k = 0; k < MG_MAX_HELPERS; k++) {
            MgPlayer *h = &mg_fight.helper[s][k];
            if (mg_fight.helper_active[s][k])
                draw(h->def, &h->dr, h->anim_idx, h->elem, h->x, h->y, h->facing, h->pal, -25, 1, 0);
        }
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++) {
        MgExplod *e = &mg_fight.explod[i];
        const MgPlayer *o = &mg_fight.p[e->bind_owner];
        if (!e->active) {
            continue;
        }
        if (e->bgfx >= 0) { bgfx_render(e, o); continue; }
        const MgCharDef *anim_def = e->anim_def ? e->anim_def : o->def;
#ifdef MG_STUDY_FX80_BLINK
        /* Odd fight ticks drop only the 8060 sprites. Body tiles stay allocated. */
        if (fx80_explod(e) && (mg_fight.ticks & 1u)) {
            hideDrawSprites(&e->dr);
            continue;
        }
#endif
        /* Opcoes de efeito: faisca e FX desligados somem; em pisca somem nos ticks impares.
         * Os tiles continuam alocados. Corpos, projeteis e o plano do bgfx nao piscam. */
        {
            const u8 mode = e->spark ? sFx.sparks : sFx.fx;
            if (mode == MG_FX_OFF || (!sFx.fx8060 && fx80_explod(e)) ||
                (mode == MG_FX_BLINK && (mg_fight.ticks & 1u))) {
                hideDrawSprites(&e->dr);
                continue;
            }
        }
        draw(anim_def, &e->dr, e->anim_idx, e->elem, e->x, e->y, e->facing, o->pal, -30, 1, 0);
    }
#ifdef MG_STUDY_FX80_BLINK
    /* Row 26 stays under the WINDOW life bar (rows 0..6) on BG_A. */
    VDP_drawText((mg_fight.ticks & 1u) ? "FX 8060 APAGADO" : "FX 8060 LIGADO ", 1, 26);
#endif
    MG_CRUMB('p');
    hud();
    MG_CRUMB('q');
    MG_PROF_MARK(6);
#ifdef MG_BOUNDS_TRACE
    bounds_trace_finish_render();
#endif
}

/* ------------------------------------------------------------------ CPU */
/* IA reimplementada (o personagem nao traz IA propria). Como a IA do MUGEN, ela ATIVA
 * comandos declarados no .cmd (p->ai_cmd) em vez de digitar sequencias; so as direcoes do
 * ultimo passo sao seguradas, para os comandos de segurar e o tipo de estado baterem. */
static s16 ai_cool[2];
static u16 ai_hold[2];
static u8 ai_hold_t[2];

static s16 findTrainingSpecial(const MgCharDef *def)
{
    if (!def || !def->cmds || !def->steps || !def->keys) return -1;
    for (u16 ci = 0; ci < def->ncmds; ci++) {
        const MgCommand *command = &def->cmds[ci];
        if (command->nsteps < 2 ||
            ci == def->cmd_holdfwd || ci == def->cmd_holdback ||
            ci == def->cmd_holdup || ci == def->cmd_holddown) continue;
        const MgCmdStep *last = &def->steps[command->first_step + command->nsteps - 1];
        for (u8 k = 0; k < last->nkeys; k++) {
            const u8 key = def->keys[last->first_key + k].key;
            if (key >= MG_K_A && key != MG_K_S) return (s16)ci;
        }
    }
    return -1;
}

static u16 key_bits(u8 k)
{
    static const u16 m[] = { 0, MG_IN_F, MG_IN_B, MG_IN_U, MG_IN_D, MG_IN_D | MG_IN_F, MG_IN_D | MG_IN_B,
                             MG_IN_U | MG_IN_F, MG_IN_U | MG_IN_B, MG_IN_A, MG_IN_BB, MG_IN_C,
                             MG_IN_X, MG_IN_Y, MG_IN_Z, MG_IN_S };
    return k < 16 ? m[k] : 0;
}

u16 MG_cpuInput(MgPlayer *p)
{
    u8 s = p->side;
    p->ai_cmd = -1;
    if (sDemoShowcase) return 0;
    if (mg_fight.round_state != 1) return 0;
    const MgPlayer *e = p->enemy;
    s16 dist = FX2I(MG_FACE(e->x - p->x, p->facing));
    if (sTrainingMode && sTrainingSparring == MG_TRAINING_IDLE) return 0;
    if (sTrainingMode && sTrainingSparring == MG_TRAINING_JUMP) {
        if (ai_cool[s] > 0) { ai_cool[s]--; return 0; }
        ai_cool[s] = 36 + (random() % 30);
        return MG_IN_U;
    }
    /* Fixed profiles own this input. FREE falls through to the shared AI. */
    if (sTrainingMode && sTrainingSparring == MG_TRAINING_DEFEND) return MG_IN_B;
    if (sTrainingMode && sTrainingSparring == MG_TRAINING_CROUCH) return MG_IN_D;
    if (sTrainingMode && sTrainingSparring == MG_TRAINING_COUNTER) {
        if (e->movetype == 'A' && dist < 90)
            return MG_IN_B | ((e->statetype == 'C') ? MG_IN_D : 0);
        if (ai_cool[s] > 0) { ai_cool[s]--; return 0; }
        ai_cool[s] = 18;
        return MG_IN_X;
    }
    if (ai_hold_t[s]) { ai_hold_t[s]--; return ai_hold[s]; }
    if ((!sTrainingMode || sTrainingSparring == MG_TRAINING_FREE) &&
        e->movetype == 'A' && dist < 90 && (random() & 3))
        return MG_IN_B | ((e->statetype == 'C') ? MG_IN_D : 0);
    if (ai_cool[s] > 0) { ai_cool[s]--; return dist > 70 ? MG_IN_F : 0; }
    if (sCpuLevel <= 2) ai_cool[s] = 18 + (random() % 24);
    else if (sCpuLevel >= 8) ai_cool[s] = 2 + (random() % 8);
    else ai_cool[s] = 6 + (random() % 20);
    if (!p->ctrl) return 0;
    const MgCharDef *d = p->def;
    if (!d || !d->cmds || !d->steps || !d->keys || !d->ncmds) return dist > 60 ? MG_IN_F : 0;
    if (sTrainingMode && sTrainingSparring == MG_TRAINING_SPECIAL) {
        if (sTrainingSpecialCmd[s] == -1) {
            const s16 found = findTrainingSpecial(d);
            sTrainingSpecialCmd[s] = found >= 0 ? found : -2;
        }
        if (sTrainingSpecialCmd[s] >= 0) {
            const u16 ci = (u16)sTrainingSpecialCmd[s];
            const MgCommand *command = &d->cmds[ci];
            const MgCmdStep *last = &d->steps[command->first_step + command->nsteps - 1];
            u16 dirs = 0;
            for (u8 k = 0; k < last->nkeys; k++) {
                const u8 key = d->keys[last->first_key + k].key;
                if (key < MG_K_A) dirs |= key_bits(key);
            }
            p->ai_cmd = (s16)ci;
            ai_hold[s] = dirs;
            ai_hold_t[s] = dirs ? 4 : 0;
            return dirs;
        }
        return 0;
    }
    const u8 tries = sCpuLevel >= 8 ? 12 : (sCpuLevel <= 2 ? 3 : 6);
    for (u8 attempt = 0; attempt < tries; attempt++) {
        u16 ci = random() % d->ncmds;
        const MgCommand *cm = &d->cmds[ci];
        if (ci == d->cmd_holdfwd || ci == d->cmd_holdback || ci == d->cmd_holdup || ci == d->cmd_holddown) continue;
        if (!cm->nsteps) continue;
        const MgCmdStep *last = &d->steps[cm->first_step + cm->nsteps - 1];
        u8 has_button = 0;
        u16 dirs = 0;
        for (u8 k = 0; k < last->nkeys; k++) {
            u8 key = d->keys[last->first_key + k].key;
            if (key >= MG_K_A && key != MG_K_S) has_button = 1;
            else if (key < MG_K_A) dirs |= key_bits(key);
        }
        if (!has_button) continue;
        if (cm->nsteps == 1 && dist > 70) continue;     /* normais so de perto */
        p->ai_cmd = ci;
        ai_hold[s] = dirs;
        ai_hold_t[s] = dirs ? 4 : 0;
        return dirs;
    }
    return dist > 60 ? MG_IN_F : 0;
}

/* ------------------------------------------------------------------ rounds */
static void reset_player(MgPlayer *p, s16 x, s8 facing)
{
    for (u8 i = 0; i < MG_MAX_PROJ; i++) p->proj[i].active = 0;
    p->x = FXI(x); p->y = 0; p->vx = p->vy = 0;
    p->facing = facing;
    p->life = p->def->consts->life >> MG_FX_SHIFT;
#ifdef MG_TEST_FULL_POWER
    p->power = 3000;                           /* so ROM de teste: supers disponiveis para evidencia */
#endif
#ifdef MG_TEST_LOW_LIFE
    if (p->side == 1) p->life = 150;           /* so ROM de teste: KO por super (fundo de vitoria) */
#endif
    p->hitpause = p->hitshake = p->hittime_left = 0;
    p->hitdef_active = 0;
    p->target = 0; p->bind_time = 0;
    p->sdef = p->def;
    p->ctrl = 0;
    p->statetype = 'S'; p->movetype = 'I'; p->physics = 'S';
    MG_changeState(p, 5900, 0, -1);
    MG_changeAnim(p, 0, 1);
    p->ctrl = 0;
}

static void start_round(void)
{
    mg_fight.camx = (STAGE_W - 320) / 2;
    reset_player(&mg_fight.p[0], STAGE_W / 2 - 70, 1);
    reset_player(&mg_fight.p[1], STAGE_W / 2 + 70, -1);
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++) {
#ifdef MG_FX_TRACE
        if (fx80_explod(&mg_fight.explod[i])) {
            MgExplod *e = &mg_fight.explod[i];
            const MgPlayer *owner = &mg_fight.p[e->bind_owner];
            fx80_record(e->bind_owner, MD_FX80_EVENT_ROUND_RESET, i, e->elem,
                        e->elem_time, e->removetime, (u16)e->anim_time,
                        FX2I(e->x), FX2I(e->y), (u16)owner->power);
        }
#endif
        mg_fight.explod[i].active = 0;
    }
    /* o round mata o explod dono sem espera-lo morrer: devolve PAL0 aqui, nao na varredura do render,
     * que nunca roda se a luta acabar sob o super (vitoria troca de cena antes do proximo frame) */
    bgfx_release();
    memset(mg_fight.helper_active, 0, sizeof(mg_fight.helper_active));
    mg_fight.round_state = 0;
    mg_fight.round_timer = 90;                 /* intro */
    mg_fight.round_no++;
    mg_fight.pause_time = 0;
    mg_fight.combo[0] = mg_fight.combo[1] = 0;
#ifndef MG_EXTERNAL_HUD
    VDP_clearTextArea(0, 8, 40, 4);
#endif
}

static void round_flow(void)
{
    MgPlayer *a = &mg_fight.p[0], *b = &mg_fight.p[1];
    switch (mg_fight.round_state) {
    case 0:
        if (--mg_fight.round_timer <= 0) {
            mg_fight.round_state = 1;
            mg_fight.round_timer = sRoundSeconds * fightTicksPerSecond();
            a->ctrl = b->ctrl = 1;
#ifndef MG_EXTERNAL_HUD
            VDP_clearTextArea(0, 8, 40, 4);
#endif
        }
        break;
    case 1:
        if (sDemoShowcase) {
            mg_fight.round_timer = sRoundSeconds * fightTicksPerSecond();
            break;
        }
        if (sTrainingMode || sContinuousSession) {
            if (sTrainingMode && !sTrainingTimer)
                mg_fight.round_timer = sRoundSeconds * fightTicksPerSecond();
            else if (mg_fight.round_timer > 0)
                mg_fight.round_timer--;
            break;
        }
        if (a->life <= 0 || b->life <= 0 || --mg_fight.round_timer <= 0) {
            mg_fight.round_state = 2;
            if (mg_fight.round_timer <= 0) {           /* tempo: menor vida perde */
                if (a->life != b->life) MG_selfState(a->life < b->life ? a : b, 170);
            }
            mg_fight.round_timer = 150;
#ifndef MG_EXTERNAL_HUD
            VDP_drawText(a->life <= 0 || b->life <= 0 ? "K.O." : "TIME", 18, 10);
#endif
        }
        break;
    case 2:
        if (--mg_fight.round_timer == 60) {
            MgPlayer *w = a->life > b->life ? a : (b->life > a->life ? b : 0);
            if (w && w->statetype != 'A' && w->movetype != 'H') MG_selfState(w, 180);
        }
        if (mg_fight.round_timer <= 0) {
            if (a->life > b->life) mg_fight.wins[0]++;
            else if (b->life > a->life) mg_fight.wins[1]++;
            if (mg_fight.wins[0] >= sRoundsToWin || mg_fight.wins[1] >= sRoundsToWin) {
                /* Preserve the final score until the player selects rematch or return. */
                mg_fight.round_state = 3;
                mg_fight.round_timer = 0;
                a->ctrl = b->ctrl = 0;
            } else {
                start_round();
            }
        }
        break;
    case 3:
        break; /* result screen owns input; combat state remains frozen */
    }
}

#ifdef MG_TEST_HOOKS
u16 MG_testFightSecondsLeft(void) { return fightSecondsLeft(); }
void MG_testRoundFlow(void) { round_flow(); }
void MG_testArmBackdropFlash(u8 frames)
{
#ifndef MG_TEST_DISABLE_STAGE3_FLASH
    sBackdropFlashFrames = frames > 2 ? 2 : frames;
#else
    (void)frames;
#endif
}
#endif

/* ------------------------------------------------------------------ API */
void MG_fightInit(const MgCharDef *p1, u8 p1pal, const MgCharDef *p2, u8 p2pal, u8 p2_cpu)
{
    bgfx_reset_visuals();
    const MgCharDef *shared_fx_def = sPendingSharedFxDef;
    const s16 shared_fx_anim_id = sPendingSharedFxAnimId;
    sPendingSharedFxDef = 0;
    sPendingSharedFxAnimId = -1;
    MG_fightAudioQueueReset();
#ifndef MG_TEST_DISABLE_STAGE3_FLASH
    sBackdropFlashFrames = sBackdropFlashActive = 0;
    backdrop_save(&sBaseBackdropColor);
#endif
    sSpark8050LastValid = 0;
#ifdef MG_TEST_CAPTURE_VDP_STATE
    sSpark8050ProbeCalls = 0;
    sSpark8050ProbePrevTick = sSpark8050ProbeCurrTick = 0;
    sSpark8050ProbePrevX = sSpark8050ProbePrevY = 0;
    sSpark8050ProbeCurrX = sSpark8050ProbeCurrY = 0;
    sSpark8050ProbeDx = sSpark8050ProbeDy = 0;
    sSpark8050ProbePrevOwner = sSpark8050ProbeCurrOwner = 0;
    sSpark8050ProbeSameTick = sSpark8050ProbeOppositeOwner = 0;
    sSpark8050ProbeWithin16 = sSpark8050ProbeWithinThreshold = sSpark8050ProbeSuppressed = 0;
#endif
#ifdef MG_ALLOC_FAILURE_EVENTS
    sAllocEpoch++;
    alloc_trace_header();
#endif
    sSpriteFailures = 0;
    sExplodOverflow = sVramAdmissionFailures = 0;
    sHudOverlay = sHudMessage = sHudInterface = 0;
#ifdef MG_SPARE_TILE_BANKS
    memset(sSpareUsed, 0, sizeof(sSpareUsed));
    sSpareLive = sSparePeak = sSpareAllocations = 0;
    /* These holes are also stage banks in other routes. A mismatching layout
     * or a character with a background loan retains ordinary allocation. */
    sSpareEnabled = !p1->nbgfx && !p2->nbgfx && VDP_getPlaneWidth() == 64 &&
        VDP_getPlaneHeight() == 32 && VDP_getBGAAddress() == 0xE000 &&
        VDP_getBGBAddress() == 0xC000 && VDP_getWindowAddress() == 0xE000 &&
        VDP_getSpriteListAddress() == 0xF400 && VDP_getHScrollTableAddress() == 0xF000;
#endif
    memset(&mg_fight, 0, sizeof(mg_fight));
    if (shared_fx_def && shared_fx_anim_id >= 0 &&
        MG_findAnim(shared_fx_def, shared_fx_anim_id) >= 0) {
        mg_fight.shared_fx_def = shared_fx_def;
        mg_fight.shared_fx_anim_id = shared_fx_anim_id;
    } else {
        mg_fight.shared_fx_anim_id = -1;
    }
#ifdef MG_BOUNDS_TRACE
    s_boundsClampFrameMask = s_boundsClampPreviousMask = 0;
    s_boundsCornerFrameMask = s_boundsCornerPreviousMask = 0;
    s_boundsLastSparseTick = 0;
    s_boundsHasSparseTick = FALSE;
#endif
#ifdef MG_TEST_FIGHT_BASE_CAMERA_WIDE
    /* Diagnostic A/B only: expand the camera clamp while preserving every
     * fighter world coordinate and the stage-free black backdrop. */
#if !defined(MG_ROUTE_FIGHT_BASE)
#error "wide fight_base camera diagnostic requires the stage-free route"
#endif
    mg_fight.stage_left = -160;
    mg_fight.stage_right = 480;
#else
    mg_fight.stage_left = 0;
    mg_fight.stage_right = STAGE_W;
#endif
    mg_fight.floor_y = FLOOR_Y;
    const MgCharDef *defs[2] = { p1, p2 };
    u8 pals[2] = { p1pal, p2pal };
    if (p1 == p2 && p1pal == p2pal) pals[1] = (p1pal + 1) % p2->npals;     /* espelho: cor diferente */
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *p = &mg_fight.p[s];
        p->def = p->sdef = defs[s];
        p->side = s;
        p->enemy = &mg_fight.p[s ^ 1];
        p->pal = s ? PAL2 : PAL1;
        p->palette_variant = pals[s] % defs[s]->npals;
        p->is_cpu = s == 1 && p2_cpu;
        MG_drawInit(&p->dr);
        for (u8 k = 0; k < MG_MAX_HELPERS; k++) MG_drawInit(&mg_fight.helper[s][k].dr);
        for (u8 i = 0; i < MG_MAX_PROJ; i++) MG_drawInit(&p->proj[i].dr);
        const u16 *bodypal = defs[s]->pals[p->palette_variant];
        PAL_setColors(s ? 32 : 16, bodypal, 16, DMA);
        s_basepal[s] = bodypal;
        build_flash_table(s);
        mg_fight.flash_lvl[s] = 0;
    }
    const u16 *fxpal = mg_fight.shared_fx_def && mg_fight.shared_fx_def->fxpal
        ? mg_fight.shared_fx_def->fxpal : p1->fxpal;
    PAL_setColors(48, fxpal, 16, DMA);
    s_bgfx_owner = -1;
    /* reserva VRAM fixa para os corpos: maior quadro dos sheets de CORPO (pal 0). Sheets de efeito
     * (PAL3) nunca foram observados na parte 0 do lutador; se aparecerem, draw_part os manda ao pool */
    u16 need[2] = { 0, 0 };
    for (u8 s = 0; s < 2; s++)
        for (u16 i = 0; i < defs[s]->nsheets; i++)
            if (!defs[s]->sheets[i].pal && defs[s]->sheets[i].def->maxNumTile > need[s])
                need[s] = defs[s]->sheets[i].def->maxNumTile;
    s_vram_cap[0] = need[0];
    s_vram_cap[1] = need[1];
    u16 next = TILE_USER_INDEX;
    if ((u32)TILE_USER_INDEX + need[0] + need[1] <= TILE_SPRITE_INDEX) {
        s_vram[0] = TILE_USER_INDEX;
        s_vram[1] = TILE_USER_INDEX + need[0];
        next += need[0] + need[1];
    } else {
        s_vram[0] = s_vram[1] = 0;            /* nao cabe: volta a alocacao automatica */
    }
    /* tiles dos efeitos de fundo logo apos os corpos, se couberem antes do pool de sprites */
    /* Dynamic bodies occupy only the SGDK pool, so they reserve no static tiles. */
    s_vram_next = next;
    for (u8 s = 0; s < 2; s++)
        for (u8 i = 0; i < MG_MAX_BGFX; i++) {
            s_bgfx_base[s][i] = s_bgfx_end[s][i] = 0;
            if (i >= defs[s]->nbgfx) continue;
            const MgBgFx *fx = &defs[s]->bgfx[i];
            u16 n = fx->img->tileset->numTile;
            u16 dup = 0;                          /* mesmo efeito ja carregado (espelho P1=P2) */
            for (u8 t = 0; t < s; t++)
                for (u8 j = 0; j < MG_MAX_BGFX && j < defs[t]->nbgfx; j++)
                    if (defs[t]->bgfx[j].img == fx->img && s_bgfx_base[t][j]) dup = s_bgfx_base[t][j];
            if (dup) { s_bgfx_base[s][i] = dup; s_bgfx_end[s][i] = dup + n; continue; }
            u16 base;
            if (!MG_fightReserveVram(n, &base)) continue; /* explicit bounded rejection */
            s_bgfx_base[s][i] = base; /* reserve only; upload when the super starts */
            s_bgfx_end[s][i] = base + n;
        }
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++) MG_drawInit(&mg_fight.explod[i].dr);
    ai_cool[0] = ai_cool[1] = 0;
    ai_hold[0] = ai_hold[1] = 0;
    ai_hold_t[0] = ai_hold_t[1] = 0;
    sTrainingSpecialCmd[0] = sTrainingSpecialCmd[1] = -1;
    start_round();
}

#ifdef MG_TEST_CAPTURE_VDP_STATE
void MG_testGetSpark8050Probe(u16 words[MG_TEST_SPARK8050_PROBE_WORDS])
{
    words[0] = sSpark8050ProbeCalls;
    words[1] = (u16)sSpark8050ProbePrevTick;
    words[2] = (u16)(sSpark8050ProbePrevTick >> 16);
    words[3] = sSpark8050ProbePrevOwner;
    words[4] = (u16)sSpark8050ProbePrevX;
    words[5] = (u16)sSpark8050ProbePrevY;
    words[6] = (u16)sSpark8050ProbeCurrTick;
    words[7] = (u16)(sSpark8050ProbeCurrTick >> 16);
    words[8] = sSpark8050ProbeCurrOwner;
    words[9] = (u16)sSpark8050ProbeCurrX;
    words[10] = (u16)sSpark8050ProbeCurrY;
    words[11] = (u16)sSpark8050ProbeDx;
    words[12] = (u16)sSpark8050ProbeDy;
    words[13] = sSpark8050ProbeSameTick;
    words[14] = sSpark8050ProbeOppositeOwner;
    words[15] = sSpark8050ProbeWithin16;
    words[16] = sSpark8050ProbeWithinThreshold;
    words[17] = sSpark8050ProbeSuppressed;
    words[18] = (u16)(sSpark8050ProbeCurrTick - sSpark8050ProbePrevTick);
    words[19] = SPARK_DUPLICATE_REGION;
}
#endif

#ifdef MG_PHASE_TRACE
void mg_phase_trace(int phase);            /* 0 inicio do tick, 1 apos controladores, 2 apos fisica/animacao, 3 apos colisao */
#define MG_PHASE(n) mg_phase_trace(n)
#else
#define MG_PHASE(n) ((void)0)
#endif

void MG_fightUpdate(u16 pad1, u16 pad2)
{
    MG_fightAudioQueuePump();
    if (mg_fight.round_state == 3) {
        mg_fight.ticks++;
        return;
    }
#ifdef MG_BOUNDS_TRACE
    bounds_trace_begin();
#endif
#ifdef MG_UPDATE_DETAIL_PROFILE
    const bool updateDetailCapture = sUpdateDetailEnabled;
    u32 updateDetailTick = 0;
    if (updateDetailCapture) {
        memset(&mg_fight_update_detail, 0, sizeof(mg_fight_update_detail));
        mg_fight_update_detail.frame = sUpdateDetailFrame;
        updateDetailTick = getSubTick();
    }
#endif
    MG_PROF_BEGIN();
    MG_CRUMB('a');
    mg_fight.ticks++;
    MG_PHASE(0);
    MgPlayer *p0 = &mg_fight.p[0], *p1 = &mg_fight.p[1];
#ifdef MG_FX_TRACE
    s32 p2PowerBefore = p1->power;
#endif
    if (sDemoShowcase) {
        pad1 = 0;
        pad2 = 0;
        if (mg_fight.pause_time == 0) demo_tick();
    }
    if (sTrainingMode && sInfiniteSpecial) p0->power = 3000;
    MG_PEAK_MARK(MG_PK_P1_INPUT);
    MG_playerInput(p0, pad1);
    MG_PEAK_MARK(MG_PK_P2_INPUT);
    MG_playerInput(p1, pad2);
    MG_UPDATE_DETAIL_MARK(0);
    MG_PROF_MARK(0);
    if (mg_fight.round_state == 0) { p0->ctrl = p1->ctrl = 0; }

    if (mg_fight.pause_time > 0) {             /* SuperPause: so o dono anda durante movetime */
#ifdef MG_UPDATE_DETAIL_PROFILE
        if (updateDetailCapture) mg_fight_update_detail.path = 1;
#endif
        mg_fight.pause_time--;
        MgPlayer *o = &mg_fight.p[mg_fight.pause_owner];
        if (mg_fight.pause_movetime > 0) {
            mg_fight.pause_movetime--;
            MG_PEAK_MARK(o->side ? MG_PK_P2_LOGIC : MG_PK_P1_LOGIC);
            MG_playerLogic(o);
            MG_PEAK_MARK(o->side ? MG_PK_P2_PHYSICS : MG_PK_P1_PHYSICS);
            MG_playerPhysics(o);
        }
        MG_PEAK_MARK(MG_PK_EXPLODS);
        for (u8 i = 0; i < MG_MAX_EXPLOD; i++)
            if (mg_fight.explod[i].active) {
#ifdef MG_UPDATE_DETAIL_PROFILE
                if (updateDetailCapture) mg_fight_update_detail.active_explods++;
#endif
                MG_explodStep(&mg_fight.explod[i], &mg_fight.p[mg_fight.explod[i].bind_owner]);
            }
        MG_UPDATE_DETAIL_MARK(11);
#ifdef MG_FX_TRACE
        if (p1->power != p2PowerBefore) fx80_record_power(p1);
#endif
#ifdef MG_BOUNDS_TRACE
        bounds_trace_pause_finalize();
#endif
        demo_sustain();
        return;
    }
    MG_CRUMB('b');
    MG_PEAK_MARK(MG_PK_P1_LOGIC);
    MG_playerLogic(p0);
    MG_UPDATE_DETAIL_MARK(1);
    MG_CRUMB('c');
    MG_PEAK_MARK(MG_PK_P2_LOGIC);
    MG_playerLogic(p1);
    MG_UPDATE_DETAIL_MARK(2);
    MG_CRUMB('d');
    MG_PHASE(1);
    MG_PROF_MARK(1);
    MG_PEAK_MARK(MG_PK_P1_PHYSICS);
    MG_playerPhysics(p0);
    MG_UPDATE_DETAIL_MARK(3);
    MG_PEAK_MARK(MG_PK_P2_PHYSICS);
    MG_playerPhysics(p1);
    MG_UPDATE_DETAIL_MARK(4);
    MG_PROF_MARK(2);
    MG_PHASE(2);
    MG_CRUMB('e');
    MG_PEAK_MARK(MG_PK_HELPERS);
    for (u8 s = 0; s < 2; s++)
        for (u8 k = 0; k < MG_MAX_HELPERS; k++)
            if (mg_fight.helper_active[s][k]) {
#ifdef MG_UPDATE_DETAIL_PROFILE
                if (updateDetailCapture) mg_fight_update_detail.active_helpers++;
#endif
                MG_playerLogic(&mg_fight.helper[s][k]);
                if (mg_fight.helper_active[s][k]) MG_playerPhysics(&mg_fight.helper[s][k]);
            }
    MG_UPDATE_DETAIL_MARK(5);
    MG_CRUMB('f');
    MG_PEAK_MARK(MG_PK_PROJECTILES);
    for (u8 s = 0; s < 2; s++)
        for (u8 i = 0; i < MG_MAX_PROJ; i++) {
#ifdef MG_UPDATE_DETAIL_PROFILE
            if (updateDetailCapture && mg_fight.p[s].proj[i].active)
                mg_fight_update_detail.active_projectiles++;
#endif
            MG_projStep(&mg_fight.p[s], &mg_fight.p[s].proj[i]);
        }
    MG_UPDATE_DETAIL_MARK(6);
    MG_PEAK_MARK(MG_PK_EXPLODS);
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++)
        if (mg_fight.explod[i].active) {
#ifdef MG_UPDATE_DETAIL_PROFILE
            if (updateDetailCapture) mg_fight_update_detail.active_explods++;
#endif
            MG_explodStep(&mg_fight.explod[i], &mg_fight.p[mg_fight.explod[i].bind_owner]);
        }
    MG_UPDATE_DETAIL_MARK(7);
    MG_PROF_MARK(3);
    MG_CRUMB('g');
    MG_PEAK_MARK(MG_PK_COLLISION);
#ifdef MG_BOUNDS_TRACE
    bounds_trace_capture_axes(4);
#endif
    if (mg_fight.round_state == 1 || mg_fight.round_state == 2) {
#ifdef MG_BOUNDS_TRACE
        s_boundsFlags |= BND_F_RESOLVE_RAN;
#endif
        resolve_hits();
    }
#ifdef MG_BOUNDS_TRACE
    bounds_trace_capture_axes(8);
#endif
    MG_UPDATE_DETAIL_MARK(8);
    MG_CRUMB('h');
    MG_PEAK_MARK(MG_PK_BOUNDS);
    MG_PHASE(3);
    MG_PROF_MARK(4);
    push_and_bounds();
#ifdef MG_BOUNDS_TRACE
    bounds_trace_bounds_complete();
#endif
    MG_UPDATE_DETAIL_MARK(9);
    MG_CRUMB('i');
    MG_PEAK_MARK(MG_PK_ROUND);
    round_flow();
    MG_UPDATE_DETAIL_MARK(10);
    MG_CRUMB('j');
    MG_PROF_MARK(5);
#ifdef MG_FX_TRACE
    if (p1->power != p2PowerBefore) fx80_record_power(p1);
#endif
    demo_sustain();
}

bool MG_fightEnd(void)
{
    /* Teardown must not erase the palette needed by a deferred restoration.
     * The consumer retains this scene and drains visuals before retrying. */
    if (mg_fight.bgfx_active || sBgfxReleasePending) {
        bgfx_release();
        return FALSE;
    }
    if (sBgfxRestoreQueued && DMA_getQueueSize()) return FALSE;
    sPendingSharedFxDef = 0;
    sPendingSharedFxAnimId = -1;
    MG_fightAudioQueuePump();
#ifndef MG_TEST_DISABLE_STAGE3_FLASH
    if (sBackdropFlashActive || sBackdropFlashFrames)
        backdrop_write(&sBaseBackdropColor);
    sBackdropFlashFrames = sBackdropFlashActive = 0;
#endif
    for (u8 s = 0; s < 2; s++) {
        MgPlayer *p = &mg_fight.p[s];
        MG_drawRelease(&p->dr);
        if (p->shadow_spr) SPR_releaseSprite(p->shadow_spr);
        for (u8 k = 0; k < MG_MAX_HELPERS; k++) MG_drawRelease(&mg_fight.helper[s][k].dr);
        for (u8 i = 0; i < MG_MAX_PROJ; i++) MG_drawRelease(&p->proj[i].dr);
    }
    for (u8 i = 0; i < MG_MAX_EXPLOD; i++) {
#ifdef MG_FX_TRACE
        if (fx80_explod(&mg_fight.explod[i])) {
            MgExplod *e = &mg_fight.explod[i];
            const MgPlayer *owner = &mg_fight.p[e->bind_owner];
            fx80_record(e->bind_owner, MD_FX80_EVENT_SCENE_EXIT, i, e->elem,
                        e->elem_time, e->removetime, (u16)e->anim_time,
                        FX2I(e->x), FX2I(e->y), (u16)owner->power);
        }
#endif
        MG_drawRelease(&mg_fight.explod[i].dr);
    }
    MG_fightAudioQueueReset();
    memset(&mg_fight, 0, sizeof(mg_fight));
    bgfx_reset_visuals();
    return TRUE;
}
