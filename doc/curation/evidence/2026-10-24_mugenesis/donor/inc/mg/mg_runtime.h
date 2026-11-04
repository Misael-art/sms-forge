/* COPIADO de tools/mugen2sgdk_forge/runtime/mg_runtime.h (v0.3.3). Edite na fonte. */
/* mg_runtime.h -- runtime generico de luta para dados gerados pelo mugen2sgdk_forge.
 *
 * Semantica alvo: motor MUGEN (estados, triggers, HitDef, Clsn1/Clsn2), reduzida ao que
 * o Mega Drive executa a 60 fps. Tudo o que diverge esta listado em runtime/README.md.
 * Sem float, sem malloc: pools estaticos, ponto fixo 24.8.
 */
#ifndef MG_RUNTIME_H
#define MG_RUNTIME_H
#include <genesis.h>
#if defined(__has_include)
#if __has_include("mg_config.h")
#include "mg_config.h"          /* runtime options must precede feature guards */
#endif
#endif
#if defined(MG_NATIVE_CONTROLLERS) && !defined(MG_NATIVE_EXPRESSIONS)
#error "Native controllers require their generated native expressions"
#endif
#if defined(MG_NATIVE_CONDITION_CACHE) && !defined(MG_NATIVE_CONTROLLERS)
#error "Condition caching requires native controller ownership"
#endif
#if defined(MG_NATIVE_STATES) && !defined(MG_NATIVE_EXPRESSIONS)
#error "Native states require their generated native expressions"
#endif

#include "mg_types.h"

#ifndef MG_AUDIO_QUEUE_MAX_AGE
#define MG_AUDIO_QUEUE_MAX_AGE 6
#endif
#if MG_AUDIO_QUEUE_MAX_AGE < 1 || MG_AUDIO_QUEUE_MAX_AGE > 65535
#error "MG_AUDIO_QUEUE_MAX_AGE must be 1..65535; runtime SetMaxAge(0) explicitly disables expiry"
#endif


#ifndef MG_ROUND_TIME_SECONDS
#define MG_ROUND_TIME_SECONDS 99
#endif
#if MG_ROUND_TIME_SECONDS < 1 || MG_ROUND_TIME_SECONDS > 99
#error "MG_ROUND_TIME_SECONDS must be 1..99 for the current two-digit timer and signed tick counter"
#endif
#ifndef MG_ROUNDS_TO_WIN
#define MG_ROUNDS_TO_WIN 2
#endif
#if MG_ROUNDS_TO_WIN < 1 || MG_ROUNDS_TO_WIN > 2
#error "MG_ROUNDS_TO_WIN must fit the two win markers supported by the runtime HUD"
#endif

enum {
    MG_TRAINING_IDLE = 0,
    MG_TRAINING_JUMP,
    MG_TRAINING_DEFEND,
    MG_TRAINING_COUNTER,
    MG_TRAINING_SPECIAL,
    MG_TRAINING_CROUCH,
    MG_TRAINING_FREE
};

#define MG_NUM_VARS     65      /* var(0..59) + sysvar(0..4) em 60..64 */
#define MG_NUM_FVARS    45      /* fvar(0..39) + sysfvar(0..4) */
#define MG_MAX_CMDS     160
#define MG_INPUT_HIST   64      /* potencia de 2: buffer circular */
/* Command labels belong to an explicitly bounded consumer registry, not the
 * fight's two live character definitions. Rebind/unbind at roster changes. */
#ifndef MG_CMD_NAME_CAPACITY
#define MG_CMD_NAME_CAPACITY 4
#endif
#if MG_CMD_NAME_CAPACITY < 1 || MG_CMD_NAME_CAPACITY > 255
#error "MG_CMD_NAME_CAPACITY must be 1..255"
#endif
typedef enum {
    MG_CMD_NAMES_OK = 0,
    MG_CMD_NAMES_INVALID,
    MG_CMD_NAMES_FULL
} MgCmdNamesResult;
#define MG_MAX_PROJ     4
#define MG_MAX_EXPLOD   6
#define MG_MAX_PERSIST_SLOTS 16 /* medido por conversor; excesso bloqueia a geracao */
#ifndef MG_MAX_HELPERS
#define MG_MAX_HELPERS  1       /* helpers simultaneos por jogador; cada um custa um MgPlayer de RAM (medir antes de subir) */
#endif
#define MG_MAX_PARTS    4       /* sprites SGDK por objeto (quadros divididos) */
#if defined(MG_NATIVE_HITDEF) && !defined(MG_NATIVE_EXPRESSIONS)
#error "Native HitDef requires the generated native expression functions"
#endif
#if defined(MG_DRAW_OWNERSHIP) && MG_MAX_PARTS > 8
#error "Draw ownership mask supports at most eight parts"
#endif

#if defined(MG_SPARE_TILE_BANKS) && !defined(MG_ROUTE_FIGHT_BASE)
#error "Spare tile banks require fight_base ownership"
#endif

typedef struct {
    Sprite *spr[MG_MAX_PARTS]; s16 sheet[MG_MAX_PARTS]; u8 fixed0;
#ifdef MG_DRAW_OWNERSHIP
    /* Written by the draw lifecycle only: bit k owns spr[k]. Empty inactive
     * objects can skip repeated cleanup without inspecting render inputs. */
    u8 owned_parts;
#endif
#ifdef MG_FRAME_TILE_ALLOC
    /* Stable descriptors in RAM; authored frame/animation data stays in ROM.
     * Only dynamic parts use these descriptors. No automatic animation. */
    SpriteDefinition part_def[MG_MAX_PARTS];
#endif
#ifdef MG_SPARE_TILE_BANKS
    u16 spare_base[MG_MAX_PARTS], spare_size[MG_MAX_PARTS];
#endif
#if defined(MG_DRAW_CACHE) || defined(MG_PAUSE_DRAW_CACHE)
    const MgCharDef *cached_def;
    const MgAnimFrame *cached_frame;
    s16 cached_x, cached_y, cached_depth;
    u16 cached_vram, cached_pal;
    s8 cached_facing;
    u8 cached_visible, cache_valid;
#endif
} MgDraw;  /* fixed0: parte 0 na VRAM fixa */
#ifdef MG_SPARE_TILE_BANKS
void MG_fightSpareStats(u16 *live, u16 *peak, u16 *allocations, u16 *enabled);
#endif
#define MG_MAX_PROG     32      /* comandos em andamento simultaneos */
#define MG_MAX_LIVE     32      /* comandos ativos (buffer) simultaneos */

/* Diagnostico temporario para comparar trabalho do reconhecedor entre os
 * clusters FCAD e controles de um VInt imediatamente adjacentes. */
#if defined(MG_COMMAND_FRAME_TRACE) && !defined(MG_OBSERVER_AB)
#error "Command frame trace requires the fixed OBAB/FCAD measurement window"
#endif
#if defined(MG_COMMAND_FRAME_TRACE) && !defined(MG_CADENCE_EVENTS)
#error "Command frame trace requires FEVT gap witnesses"
#endif
#define MG_COMMAND_TRACE_EXPECTED_FRAMES 128
#define MG_COMMAND_TRACE_DIGEST_SCHEMA 2
#define MG_COMMAND_TRACE_FRAME_SELECTED(frame) ( \
    ((((frame) >= 101) && ((frame) <= 125)) && ((((frame) - 101) % 3) == 0)) || \
    ((((frame) >= 131) && ((frame) <= 155)) && ((((frame) - 131) % 3) == 0)) || \
    ((((frame) >= 161) && ((frame) <= 182)) && ((((frame) - 161) % 3) == 0)) || \
    ((((frame) >= 188) && ((frame) <= 206)) && ((((frame) - 188) % 3) == 0)) || \
    (((frame) >= 240) && ((frame) <= 252)) || \
    (((frame) >= 320) && ((frame) <= 332)) || \
    (((frame) >= 540) && ((frame) <= 552)) || \
    (((frame) >= 636) && ((frame) <= 648)) || \
    (((frame) >= 840) && ((frame) <= 852)) || \
    (((frame) >= 907) && ((frame) <= 910)) || \
    (((frame) >= 936) && ((frame) <= 948)) || \
    (((frame) >= 1140) && ((frame) <= 1152)) )
#ifdef MG_COMMAND_GAP_COUNTERS
#ifndef MG_COMMAND_FRAME_TRACE
#error "Per-command gap counters require same-frame semantic tracing"
#endif
#define MG_COMMAND_GAP_METRIC_COUNT 6
#define MG_COMMAND_GAP_GROUP_COUNT 2
#define MG_COMMAND_GAP_ROW_CAPACITY (2 * MG_MAX_CMDS)
enum {
    MG_COMMAND_GAP_PROGRESS_VISITS = 0,
    MG_COMMAND_GAP_ADVANCE_ATTEMPTS,
    MG_COMMAND_GAP_MATCHED_STEPS,
    MG_COMMAND_GAP_RESTART_MATCHES,
    MG_COMMAND_GAP_COMPLETIONS,
    MG_COMMAND_GAP_EXPIRATIONS
};
void MG_commandGapDiagCommitFrame(u16 frame, u16 vintGap);
void MG_commandGapDiagWriteSram(u32 offset);
#endif

/* bits de entrada ja relativos a frente do personagem */
#define MG_IN_U 0x0001
#define MG_IN_D 0x0002
#define MG_IN_B 0x0004
#define MG_IN_F 0x0008
#define MG_IN_A 0x0010
#define MG_IN_BB 0x0020
#define MG_IN_C 0x0040
#define MG_IN_X 0x0080
#define MG_IN_Y 0x0100
#define MG_IN_Z 0x0200
#define MG_IN_S 0x0400

/* v * facing sem multiplicacao de 32 bits (68000) */
#define MG_FACE(v, f) ((f) < 0 ? -(v) : (v))

typedef struct {
    s16 damage, guard_damage;
    s16 pause_p1, pause_p2, gpause_p1, gpause_p2;
    s16 hittime, slidetime, ghittime, gslidetime, gctrltime, airhittime;
    mgfx gvel_x, gvel_y, avel_x, avel_y, down_vx, down_vy, guardvel_x;
    s16 down_hittime;
    mgfx fall_yvel, fall_xvel, yaccel;
    u8  fall, airfall, fall_recover, kill, guard_kill;
    s16 spark_x, spark_y, p1stateno, p2stateno, getpower, givepower, id, chainid;
    u16 attr;
    u8  hitflag, guardflag, animtype, air_animtype, groundtype, airtype, priority;
    s16 hitsound, guardsound, sparkno, guard_sparkno;
} MgHitDef;

typedef struct {
    u8 active;
    s16 id, anim_id, hitanim, remanim;
    u16 anim_idx; u8 elem; s16 elem_time;
    mgfx x, y, vx, vy, ax, ay;
    s8 facing;
    s16 removetime, hits;
    u8 removing;
    s16 contact_time;          /* ticks desde o ultimo contato (-1 nunca) */
    MgHitDef hd;
    MgDraw dr;
} MgProj;

typedef struct {
    u8 active;
    s16 id;
    u16 anim_idx; u8 elem; s16 elem_time; s32 anim_time;
    const MgCharDef *anim_def;   /* definicao que possui a animacao; pode ser a fonte FX compartilhada */
    mgfx x, y, vx, vy;
    s8 facing;
    s16 removetime, bindtime;
    u8 bind_owner;             /* segue o dono enquanto bindtime */
    mgfx bx, by;
    s16 depth;
    s8 bgfx;                   /* >=0: efeito de fundo (indice em def->bgfx) em vez de sprite */
    u8 bgfx_shown;
    u8 spark;                  /* faisca de acerto/defesa (segue MgEffects.sparks, nao .fx) */
    MgDraw dr;
} MgExplod;

typedef struct MgPlayer MgPlayer;
struct MgPlayer {
    const MgCharDef *def;      /* dono das animacoes/sprites/sons/comandos */
    const MgCharDef *sdef;     /* dono dos estados em execucao (custom state = def do atacante) */
    MgPlayer *enemy;
    u8 side;
    u8 pal;                    /* PAL1/PAL2 do corpo */
    u8 palette_variant;        /* selected costume; portrait indices match this palette */
    u8 is_cpu;

    /* posicao em pixels do mundo (fx), y=0 chao, y<0 no ar; vel local (x relativo a facing) */
    mgfx x, y, vx, vy;
    s8 facing;

    s16 stateno, prevstateno;
    s16 state_idx;
    s32 time;
    u8 statetype, movetype, physics, ctrl;
    u8 state_changed;

    u16 anim_idx; s16 anim_id;
    u8 elem;                   /* 0-based */
    s16 elem_time;
    s32 anim_time;             /* ticks desde o inicio do ciclo */

    s32 life, power;
    s32 vars[MG_NUM_VARS];
    mgfx fvars[MG_NUM_FVARS];

    /* ataque */
    u8 hitdef_active;
    MgHitDef hd;
    s16 movecontact, movehit, moveguarded;   /* ticks desde o contato (0 = nao) */
    s16 hitcount;
    s16 attackdist;            /* AttackDist: 0 = padrao (160); zera ao trocar de estado */
    const MgCtrl *rev;         /* ReversalDef ativo neste tick (nulo = nenhum) */
    u8 contact_fresh;          /* contato acabou de ocorrer: MoveHit/MoveContact valem 1 no 1o tick executado depois */
    u8 nopush, freebound;      /* PlayerPush 0 / ScreenBound 0: valem so no tick corrente */
    s16 edge_f, edge_b;        /* Width edge deste tick, em px; 0 = o eixo pode encostar na borda */
    s16 hitpause;              /* congelado (pausetime) */
    u8 hitpause_active_tick;   /* latch: fisica decrementa hitpause antes de push/bounds */
    u8 posfreeze;
    u16 persist_count[MG_MAX_PERSIST_SLOTS]; /* contadores so para persistent != 1 */

    /* dano recebido */
    MgHitDef gh;               /* hitdef que me atingiu */
    mgfx gh_vx, gh_vy;
    s16 hitshake;              /* ticks de tremida restantes */
    s16 hittime_left;
    u8 gh_fall, gh_guarded;
    u16 nothitby_attr; s16 nothitby_time;
    s16 juggle;

    /* entrada */
    u16 in_raw, in_prev;
    u16 hist[MG_INPUT_HIST]; u8 hist_len; u8 hist_head;
    u8 cmd_timer[MG_MAX_CMDS];
    u8 cmd_pos[MG_MAX_CMDS];      /* proximo passo esperado */
    u8 cmd_age[MG_MAX_CMDS];      /* ticks desde o primeiro passo */
    u8 prog[MG_MAX_PROG]; u8 nprog;      /* comandos em andamento (pos > 0) */
    u8 live[MG_MAX_LIVE]; u8 nlive;      /* comandos com cmd_timer > 0 */
    u8 hold_ok[(MG_MAX_CMDS + 7) / 8];  /* resultado por indice em MgCharDef.hold_cmds */
    s16 ai_cmd;                          /* CPU: comando a ativar neste tick (-1 nenhum) */

    /* agarrao */
    MgPlayer *target; s16 bind_time; mgfx bind_x, bind_y;

    s16 sprpriority;
    MgProj proj[MG_MAX_PROJ];
    MgDraw dr;
    Sprite *shadow_spr;        /* sombra (P5): ultimo na lista, descartada primeiro em estouro de linha */
    s16 shake_screen;
    /* faisca: ultimo ponto de contato e indice de variacao (combos na mesma regiao) */
    s16 spark_last_x, spark_last_y; u32 spark_last_tick; u8 spark_var;
    /* helper reduzido (MUGEN Helper): roda estados do dono, invisivel a colisoes */
    u8 is_helper;
    s16 helper_id;
    u8 helper_slot;
    MgPlayer *parent;
};

typedef struct {
    MgPlayer p[2];
    MgPlayer helper[2][MG_MAX_HELPERS];   /* pool por jogador */
    u8 helper_active[2][MG_MAX_HELPERS];
    MgExplod explod[MG_MAX_EXPLOD];
    const MgCharDef *shared_fx_def; /* fonte explicita para uma animacao FX compartilhada */
    s16 shared_fx_anim_id;          /* apenas este ID pode ser resolvido fora do personagem local */
    s32 camx;                  /* pixels do mundo na borda esquerda da tela */
    s16 stage_left, stage_right, floor_y;
    s16 pause_time; u8 pause_owner; s16 pause_movetime;
    s16 round_state;           /* 0 intro, 1 luta, 2 KO, 3 fim */
    s16 round_timer, round_no;
    u8 wins[2];
    u32 ticks;
    u32 hit_event_count[2];      /* gameplay event oracle, independent from visual feedback */
    u32 guard_event_count[2];
    s16 screen_shake;          /* EnvShake do personagem: ticks restantes (eixo vertical, sem decaimento) */
    s8 envshake_ampl;          /* EnvShake: amplitude em pixels */
    /* efeitos de impacto (etapa 3): gatilho em apply_hit, avancados 1x por quadro em MG_fightRender */
    u8 shake_t;                /* ticks desde o impacto pesado; >= MG_SHAKE_LEN = parado */
    s8 shake_ax, shake_ay;     /* amplitude com sinal: X na direcao do golpe, Y (para baixo) so em queda/KO */
    s8 shake_x, shake_y;       /* deslocamento da camera NESTE quadro (mundo inteiro; HUD fica parado) */
    u8 flash_lvl[2];           /* nivel do flash do corpo (0 = parado); ver MgEffects.body_flash */
    u8 combo[2];               /* acertos consecutivos do atacante (lado) no combo atual */
    u32 combo_tick[2];         /* tick do ultimo acerto do combo */
    u8 bgfx_active;            /* fundo de super em tela cheia ativo (HUD deve se esconder) */
    u16 pal0_saved[16];        /* snapshot PAL0 devolvido por cram_restore no fim do emprestimo */
} MgFight;

extern MgFight mg_fight;

#ifdef MG_UPDATE_DETAIL_PROFILE
#define MG_UPDATE_DETAIL_PHASE_COUNT 12
#define MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT 2
#define MG_UPDATE_DETAIL_LOGIC_PHASE_COUNT 3
#define MG_UPDATE_DETAIL_NEGATIVE_PHASE_COUNT 3
#define MG_UPDATE_DETAIL_INPUT_PHASE_COUNT 6
#define MG_UPDATE_DETAIL_LOGIC_NEGATIVE_STATES 0
#define MG_UPDATE_DETAIL_LOGIC_AUTO_TRANSITIONS 1
#define MG_UPDATE_DETAIL_LOGIC_CURRENT_STATE 2
#define MG_UPDATE_DETAIL_NEGATIVE_MINUS3 0
#define MG_UPDATE_DETAIL_NEGATIVE_MINUS2 1
#define MG_UPDATE_DETAIL_NEGATIVE_MINUS1 2
#ifndef MG_UPDATE_DETAIL_FIRST_FRAME
#define MG_UPDATE_DETAIL_FIRST_FRAME 698
#endif
#ifndef MG_UPDATE_DETAIL_LAST_FRAME
#define MG_UPDATE_DETAIL_LAST_FRAME 714
#endif
typedef struct {
    u16 frame;
    u16 path; /* 0 normal; 1 SuperPause early return */
    u16 active_helpers;
    u16 active_projectiles;
    u16 active_explods;
    u32 phase[MG_UPDATE_DETAIL_PHASE_COUNT];
    u32 logic[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT][MG_UPDATE_DETAIL_LOGIC_PHASE_COUNT];
    u32 negative_logic[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT][MG_UPDATE_DETAIL_NEGATIVE_PHASE_COUNT];
    u32 negative_mask_build_ticks[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u32 negative_native_ticks[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u32 negative_fallback_ticks[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 negative_live_commands[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 negative_candidate_controllers[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u32 input_total_ticks[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u32 input_phase_ticks[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT][MG_UPDATE_DETAIL_INPUT_PHASE_COUNT];
    u16 input_live_commands[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_progress_commands[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_bucket_entries[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_hold_commands[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_progress_visits[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_progress_zero_pos_skips[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_progress_timeouts[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_progress_no_event_keeps[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_progress_advance_calls[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_hold_scan_entries[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_hold_advance_calls[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
    u16 input_hold_refire_calls[MG_UPDATE_DETAIL_LOGIC_PLAYER_COUNT];
} MgFightUpdateDetail;
extern MgFightUpdateDetail mg_fight_update_detail;
extern bool mg_fight_update_detail_active;
void MG_fightSetUpdateDetailFrame(u16 frame, bool enabled);
bool MG_fightUpdateDetailIsActive(void);
void MG_fightUpdateDetailRecordLogic(u8 side, u8 phase, u32 subticks);
void MG_fightUpdateDetailRecordNegative(u8 side, u8 phase, u32 subticks);
#endif

/* Perfil opcional no hardware (compilar com -DMG_PROFILE): subticks (1280 por quadro NTSC)
 * acumulados por etapa: 0 entrada/comandos, 1 estados, 2 fisica, 3 projeteis/explods,
 * 4 colisoes, 5 empurrao/rounds, 6 render, 7 SPR_update (medido pelo host da cena). */
/* marcador de diagnostico (so ROM de teste): escreve o passo atual na linha 4 da tela */
#ifdef MG_TEST_BREADCRUMB
extern char mg_crumbs[25];
extern u8 mg_crumb_i;
/* anel de 24 marcadores gravado na SRAM (offset 0x1000; 0x1018 = proxima posicao): sobrevive ao crash */
#define MG_CRUMB(ch) do { SRAM_enable(); SRAM_writeByte(0x1000 + mg_crumb_i, (ch)); \
    mg_crumb_i = (mg_crumb_i + 1) % 24; SRAM_writeByte(0x1018, mg_crumb_i); SRAM_disable(); } while (0)
#else
#define MG_CRUMB(ch) do { } while (0)
#endif

#if defined(MG_PROFILE) || defined(MG_LOGIC_PROFILE)
extern u32 mg_prof[16];   /* 8..: detalhe (8 hist, 9 laco comandos, 10 negativos, 11 estado atual, 12 auto) */
#define MG_PROF_BEGIN() u32 mg_prof_t = getSubTick()
#define MG_PROF_MARK(i) do { u32 mg_prof_n = getSubTick(); mg_prof[i] += mg_prof_n - mg_prof_t; mg_prof_t = mg_prof_n; } while (0)
#else
#define MG_PROF_BEGIN() do { } while (0)
#define MG_PROF_MARK(i) do { } while (0)
#endif

/* API */
void MG_fightSetSharedFxSource(const MgCharDef *source, s16 anim_id);
/* Personagem sem sombra gerada usa a sombra compartilhada da cena (padrao ligado). */
#ifndef MG_SHARED_SHADOW_FALLBACK
#define MG_SHARED_SHADOW_FALLBACK 1
#endif
#if MG_SHARED_SHADOW_FALLBACK || defined(MG_STUDY_FX80_BLINK)
void MG_fightUseSharedShadow(const SpriteDefinition *shadow);
#endif
void MG_fightSetSessionOptions(u8 cpuLevel, u8 roundsToWin, u8 roundSeconds,
                               u8 trainingMode, u8 trainingSparring,
                               u8 infiniteSpecial, u8 trainingTimer);
void MG_fightSetContinuousSession(u8 enabled);
void MG_fightSetSoundCategories(u8 effectsEnabled, u8 voiceEnabled);
void MG_fightSetEconomyBlink(u8 enabled);

/* Efeitos visuais ligaveis em runtime (Options e pausa da luta). Ver doc/engine_options.md. */
#define MG_FX_OFF    0
#define MG_FX_ON     1
#define MG_FX_BLINK  2         /* some nos ticks impares; tiles continuam alocados */
#define MG_SHADOW_ALTERNATE 3  /* sombra: P1 nos ticks pares, P2 nos impares */
typedef struct {
    u8 screen_flash;           /* fundo branco no acerto */
    u8 body_flash;             /* linha de paleta do defensor clareia ao branco e volta em 4 quadros */
    u8 sparks;                 /* MG_FX_OFF/ON/BLINK */
    u8 fx;                     /* explods de golpes e especiais: MG_FX_OFF/ON/BLINK */
    u8 fx8060;                 /* FX 8060 (estouro do super; pesa no limite H40) */
    u8 super_bgfx;             /* fundo do super (BGFX) */
    u8 shadow;                 /* MG_FX_OFF/ON/BLINK ou MG_SHADOW_ALTERNATE */
    u8 shared_spark;           /* golpe sem faisca propria usa a faisca da fonte compartilhada */
} MgEffects;
void MG_fightSetEffects(const MgEffects *fx);
const MgEffects *MG_fightGetEffects(void);
/* sparkno de fightfx comum indisponivel (sem pacote global): o runtime decide pela fonte compartilhada */
#define MG_SPARK_COMMON (-3)
/* Laboratorio de golpes. Desligado fora do modo DEMO. Nao altera Arcade, Versus ou Treino. */
void MG_fightSetDemoShowcase(u8 enabled);
u8 MG_fightDemoShowcase(void);
/* O HUD completo fica no ar. A tela de super, quando existe, continua escondendo o HUD so enquanto o bgfx esta ativo. */
u8 MG_fightDemoSuperBarOnly(void);
#define MG_DEMO_PLACE_START  0
#define MG_DEMO_PLACE_CENTER 1
#define MG_DEMO_PLACE_CORNER 2
/* Failure leaves the registry intact; counters saturate until explicit reset.
 * Passing names=NULL,count=0 removes this definition and releases one slot. */
MgCmdNamesResult MG_bindCmdNames(const MgCharDef *def, const char *const *names, u16 count);
void MG_clearCmdNames(void);
u8 MG_cmdNameCount(void);
u16 MG_cmdNameRejections(void);
u8 MG_fightDemoMoveCount(void);
const char *MG_fightDemoMoveName(u8 index);
void MG_fightDemoPlayOne(u8 index, u8 place);
void MG_fightDemoPlayAll(u8 place);
u8 MG_fightDemoBusy(void);
u8 MG_fightDemoFxHidden(void);
void MG_fightDemoStress(u8 enabled);   /* DEMO ESTRESSE: pior caso de recursos simultaneos */
u8 MG_fightDemoStressActive(void);
u8 MG_fightRoundSeconds(void);
u8 MG_fightRoundsToWin(void);
u8 MG_fightCpuLevel(void);
void MG_fightInit(const MgCharDef *p1, u8 p1pal, const MgCharDef *p2, u8 p2pal, u8 p2_cpu);
void MG_fightUpdate(u16 pad1, u16 pad2);     /* 1 tick de logica (sem DMA fora do VBlank) */
#ifdef MG_TEST_CAPTURE_VDP_STATE
#define MG_TEST_SPARK8050_PROBE_WORDS 20
void MG_testGetSpark8050Probe(u16 words[MG_TEST_SPARK8050_PROBE_WORDS]);
#endif
#ifdef MG_TEST_HOOKS
void MG_testApplyHit(MgPlayer *attacker, MgPlayer *defender, const MgHitDef *hitdef);
void MG_testApplyProjectileHit(MgPlayer *attacker, MgPlayer *defender, const MgHitDef *hitdef);
u16 MG_testFightSecondsLeft(void);
void MG_testRoundFlow(void);
void MG_testArmBackdropFlash(u8 frames);
#endif

/* ---- REGRA 1c generalizada: posse de CRAM declarada por consumidor ----
 * Uma linha CRAM tem 16 indices (0 = transparente). O contrato do projeto e
 * PAL0 cenario/HUD, PAL1/PAL2 corpo+retrato, PAL3 FX. Como as 4 linhas ja estao
 * todas comprometidas, isolamento se faz por FAIXA de indice e por emprestimo com
 * save/restore -- nunca por emprestar a linha inteira. */
typedef struct {
    u8        line;                    /* 0..3 = PAL0..PAL3 */
    u8        lo, hi;                  /* indices [lo..hi] que o consumidor possui;
                                        * (lo==hi==0) = reserva sem dono: indice 0 de uma linha
                                        * e a entrada transparente, entao nenhuma faixa propria e perdida */
    u8        borrow;                  /* 1 = nao dono: save/restore obrigatorios */
    const u16 *tab;                    /* swap pre-declarado (REGRA 1c) ou 0 */
} CramConsumer;

#define CRAM_CONSUMER(l, lo, hi, br) { (l), (lo), (hi), (br), 0 }

extern const CramConsumer CRAM_FLASH_P1, CRAM_FLASH_P2, CRAM_SUPER_BGFX, CRAM_FX_PAL3;
extern const CramConsumer CRAM_STAGERES, CRAM_HUDRES, CRAM_PORTRAIT_P1, CRAM_PORTRAIT_P2;

void cram_write(const CramConsumer *c, const u16 *src);   /* so [lo..hi], DMA_QUEUE, fonte estatica */
void cram_save(const CramConsumer *c, u16 *dst);          /* dst com ao menos hi-lo+1 palavras */
void cram_restore(const CramConsumer *c, const u16 *saved);
u8   cram_span(const CramConsumer *c);

/* O emprestimo de PAL0 do super e devolvido de dois lugares (fim do explod e transicao de
 * round/KO), entao a liberacao precisa ser idempotente. */
void bgfx_release(void);

/* Presentation-only pause: hides actors, invalidates draw caches; the next
 * ordinary render restores eligible actors without advancing simulation. */
void MG_fightHideActors(void);
void MG_fightRender(void);                   /* posiciona sprites; o upload ocorre em SPR_update */

/* Queue optional visuals AFTER SPR_update/HUD/observers, immediately before
 * VBlank processing. Default BGFX temporal lease is denied on each init. */
void MG_fightQueueVisuals(void);
bool MG_fightSetBgFxLease(bool granted);
u32 MG_fightVisualRefusals(u8 reason);
void MG_fightHudOverlayInterface(u8 visible); /* debug/modal priority intent, independent of messages */
void MG_fightHudOverlay(u8 visible);         /* foreground plane messages own priority while visible */
/* FALSE keeps the old fight intact: queue visuals + VBlank, then retry.
 * TRUE releases actors and resets presentation ownership. */
bool MG_fightEnd(void);
u32 MG_fightSpriteFailures(void);
#ifdef MG_ALLOC_FAILURE_EVENTS
void MG_fightSetAllocFrame(u32 totalFrame, u32 sceneFrame);
#endif
/* Snapshot only: callers must reserve before every later static upload.
 * All ranges are half-open and end before the live SGDK sprite pool. */
u16 MG_fightVramNext(void);
bool MG_fightReserveVram(u16 tiles, u16 *base);
u16 MG_fightVramAdmissionFailures(void);
bool MG_fightGetBgFxLoan(u16 *base, u16 *tileCount); /* resource range temporarily loaned to stage streaming */

/* internos compartilhados */
/* Resolve only the -2 default sentinel in HitDef/Projectile/ReversalDef.
 * guard selects guard_sparkno; defaults belong to p->def, never p->sdef.
 * The weak implementation returns the raw [Data] constant. A consumer may
 * supply one strong, side-effect-free definition for its fallback policy;
 * both interpreted and generated native HitDefs call it. Explicit -1 (off),
 * -3 (consumer shared spark) and nonnegative animation IDs bypass this hook.
 * New native output requires a runtime providing this symbol; no struct ABI
 * changes or automatic adaptation of older generated native code occurs. */
s16 MG_resolveDefaultSpark(const MgPlayer *p, bool guard);
#ifdef MG_NATIVE_EXPRESSIONS
mgfx MG_evalBytecode(const MgPlayer *p, u16 off);
/* Keep the native front at its call site: no interpreter register frame. */
static inline mgfx MG_eval(const MgPlayer *p, u16 off)
{
    if (off == MG_NONE) return 0;
#ifndef MG_VM_DISABLE_NATIVE
    const MgCharDef *d = p->sdef;
    if (d->native_eval && d->native_code == d->code && off < d->native_code_size) {
        MgExprFn fn = d->native_eval[off];
        if (fn) return fn(p);
    }
#endif
    return MG_evalBytecode(p, off);
}
#else
mgfx MG_eval(const MgPlayer *p, u16 off);
#endif
/* Shared arithmetic/complex triggers for generated native expressions. */
mgfx MG_nativeTrigger(const MgPlayer *p, u8 id);
mgfx MG_nativeRandom(void);                  /* same RNG call site as the VM; no trigger dispatch */
mgfx MG_nativeTriggerArg(const MgPlayer *p, u8 id, mgfx arg);
mgfx MG_nativeMultiply(mgfx a, mgfx b);
mgfx MG_nativeDivide(mgfx a, mgfx b);
u8 MG_nativeExecuteController(MgPlayer *p, const MgCtrl *ctrl);
u8 MG_nativeControllerAllowed(MgPlayer *p, const MgCtrl *ctrl);
s32  MG_evalInt(const MgPlayer *p, u16 off, s32 dflt);
void MG_changeState(MgPlayer *p, s16 no, s16 ctrl, s16 anim);
void MG_animAdvance(MgPlayer *p);          /* fim do tick: avanca elemento/tempo da animacao (usado pela fisica e pelos testes) */
s16 MG_numHelper(u8 side, s16 id);       /* helpers ativos do jogador; id <= 0 = todos */
void MG_readReversal(MgPlayer *p, const MgCtrl *c, MgHitDef *h);
void MG_changeAnim(MgPlayer *p, s16 anim, u8 elem1);
s16  MG_findAnim(const MgCharDef *d, s16 id);
s16  MG_findState(const MgCharDef *d, s16 id);
s16  MG_animElemTime(const MgPlayer *p, s16 elem1);
s32  MG_animTime(const MgPlayer *p);
void MG_playSound(const MgPlayer *p, s16 idx);
void MG_playSoundSfx(const MgPlayer *p, s16 idx);
void MG_playVoice(const MgPlayer *p, s16 idx);
typedef enum {
    MG_SOUND_EFFECT = 0,
    MG_SOUND_VOICE
} MgSoundCategory;
/* Generic source policy is EFFECT. A consumer may override this weak hook;
 * MUGEN sound group numbers alone do not imply a universal voice convention. */
MgSoundCategory MG_soundCategory(const MgPlayer *p, const MgSound *sound);
void MG_playMugenSound(const MgPlayer *p, s16 idx);
void MG_fightAudioQueueReset(void);
u8 MG_fightAudioQueuePending(void);
u8 MG_fightAudioQueuePeak(void);
u16 MG_fightAudioQueueOverflow(void);
u16 MG_fightAudioQueueExpired(void);
/* Default clock is SGDK vtimer (VInts). Isolated stubs without that symbol
 * read zero and must define it or inject a clock to exercise deadlines.
 * An injected clock is monotonic modulo u32, in VInts, and must be refreshed
 * before producing/pumping sounds, including UI pause frames if pumping there.
 * Switching clock sources rebases pending events and preserves their ages.
 * Age >= max_age expires before PCM submission; max_age=0 disables expiry.
 * Reset clears queue/statistics, retaining clock mode and max-age policy. */
void MG_fightAudioQueueSetClock(u32 now);
void MG_fightAudioQueueUseDefaultClock(void);
void MG_fightAudioQueueSetMaxAge(u16 max_age);
void MG_fightAudioQueuePump(void);
/* Reject newest at capacity; NULL preserves every admitted live effect. */
MgExplod *MG_spawnExplod(MgPlayer *owner, s16 anim, mgfx x, mgfx y, s16 removetime, s16 id, s8 facing);
u16 MG_fightExplodOverflow(void);
u16  MG_cpuInput(MgPlayer *p);
void MG_playerInput(MgPlayer *p, u16 pad);
void MG_playerLogic(MgPlayer *p);
void MG_playerPhysics(MgPlayer *p);
void MG_projStep(MgPlayer *p, MgProj *pr);
void MG_explodStep(MgExplod *e, const MgPlayer *owner);
void MG_selfState(MgPlayer *p, s16 no);
void MG_drawInit(MgDraw *d);
void MG_drawRelease(MgDraw *d);

#endif
