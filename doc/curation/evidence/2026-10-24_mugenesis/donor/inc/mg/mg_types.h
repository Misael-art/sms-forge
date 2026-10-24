/* COPIADO de tools/mugen2sgdk_forge/runtime/mg_types.h (v0.3.3). Edite na fonte. */
/* mg_types.h -- contrato de dados entre o gerador mugen2sgdk_forge e o runtime.
 * Fonte canonica: tools/mugen2sgdk_forge/runtime/. Copiado para projetos por `install-runtime`.
 * Numeros em ponto fixo 24.8 (MG_FX). Sem float, sem malloc.
 */
#ifndef MG_TYPES_H
#define MG_TYPES_H

/* Incompatible struct/opcode layout requires an ABI increment and regeneration. */
#define MG_DATA_ABI_VERSION 1
#define MG_DATA_FEATURES 0x00000001UL /* sound source group/sample identity */

#include <genesis.h>
#if defined(__has_include)
#if __has_include("mg_config.h")
#include "mg_config.h" /* project options must reach generated translation units */
#endif
#endif

#define MG_FX_SHIFT 8
#define MG_FX       (1 << MG_FX_SHIFT)
#define MG_NONE     0xFFFF

typedef s32 mgfx;
struct MgPlayer;
typedef mgfx (*MgExprFn)(const struct MgPlayer *p);
typedef u8 (*MgNativeMinus1Fn)(struct MgPlayer *p, const u32 *bits);
typedef u8 (*MgStateStepFn)(struct MgPlayer *p);
typedef u8 (*MgNativeStateFn)(struct MgPlayer *p, s16 index);
/* native_minus1: original bitmap for -1, NULL selects the exact -2 table. */

typedef struct { s16 x1, y1, x2, y2; } MgBox;

typedef struct {
    const SpriteDefinition *def;
    s16 axis_x, axis_y;          /* eixo MUGEN dentro da celula */
    u16 cell_w, cell_h;
    u8  pal;                     /* 0 = corpo, 1 = efeitos */
    u8  pad;
} MgSheet;

#define MG_FRAME_HFLIP 1
#define MG_FRAME_VFLIP 2
#define MG_FRAME_BLEND 4         /* blend MUGEN: sem equivalente no VDP (desenhado opaco) */

typedef struct {
    s16 sheet;                   /* -1 = frame vazio */
    u8  frame;
    u8  flags;
    s16 ox, oy;                  /* offset do .air */
    s16 time;                    /* -1 = infinito */
    u8  nclsn1, nclsn2;          /* caixas de ataque / corpo */
    u16 clsn;                    /* indice em boxes[]: clsn1 depois clsn2 */
    u8  nparts;                  /* 1 = quadro simples; >1 = partes extras em parts[part..] */
    u8  pad;
    u16 part;
} MgAnimFrame;

/* parte extra de um quadro grande dividido pelo conversor (limites do rescomp/VDP) */
typedef struct { s16 sheet; u8 frame; u8 pad; } MgFramePart;

typedef struct {
    s16 id;
    u16 first;                   /* indice em frames[] */
    u8  count;
    u8  loopstart;
    s16 total;                   /* soma dos tempos; -1 se algum frame e infinito */
} MgAnim;

typedef struct {
    u8  type;                    /* MG_CT_* (mg_ops.h) */
    u8  nparams;
    u8  nsym;
    u8  pad;
    u16 cond;                    /* offset em code[] */
    u16 params;                  /* indice em param_offs[] (MG_NONE por parametro ausente) */
    u16 sym;                     /* indice em syms[] */
    u16 gate;                    /* offset em gates[] ([n, cmd...]); MG_NONE = sem portao */
    u8  tkind;                   /* portao de tempo: 0 nenhum, 1 time == tval, 2 inicio do elemento tval */
    s16 tval;
    u8  ignorehitpause;          /* MUGEN: avaliar este controlador durante hitpause */
    u8  persist_mode;            /* 0 = toda trigger (persistent=1), 1 = uma vez, 2 = cada persist_every triggers */
    u8  persist_slot;            /* indice na MgPlayer; 255 quando nao requer contador */
    u8  pad2;
    u16 persist_every;
} MgCtrl;

typedef struct {
    s16 id;
    u8  statetype, movetype, physics;
    u8  flags;                   /* bit0 facep2, bit1 hitdefpersist, bit2 movehitpersist, bit3 hitcountpersist */
    u16 p_anim, p_ctrl, p_poweradd, p_sprpriority, p_juggle, p_velx, p_vely;   /* offsets em code[] */
    u16 first_ctrl;
    u16 nctrl;
    u8 persist_first;            /* faixa de MgPlayer.persist_count[] deste estado */
    u8 npersist;
} MgState;

#define MG_KEY_REL   1           /* ~ */
#define MG_KEY_HOLD  2           /* / */
#define MG_KEY_4WAY  4           /* $ */
typedef struct { u8 key; u8 mods; u8 reltime; u8 pad; } MgCmdKey;
typedef struct { u16 first_key; u8 nkeys; u8 strict; u16 kmask; } MgCmdStep;   /* strict: bit0 ">", bit1 so "/segurar"; kmask: bits MG_K_* cujo evento pode satisfazer o passo */
#define MG_STEP_STRICT    1
#define MG_STEP_HOLD_ONLY 2
typedef struct { u16 first_step; u8 nsteps; u8 time; u8 buffer_time; u8 hold_only; } MgCommand;  /* hold_only: ultimo passo so /teclas */

/* teclas: direcoes relativas a frente do personagem, botoes MUGEN */
enum { MG_K_NONE, MG_K_F, MG_K_B, MG_K_U, MG_K_D, MG_K_DF, MG_K_DB, MG_K_UF, MG_K_UB,
       MG_K_A, MG_K_B_BTN, MG_K_C, MG_K_X, MG_K_Y, MG_K_Z, MG_K_S };

/* Keep the source .snd address with each converted PCM sample so runtime and
 * tooling can preserve MUGEN sound-group semantics after compaction. */
typedef struct { const u8 *data; u32 len; u32 group; u32 sample; } MgSound;

/* efeito de fundo em tela cheia animado por paleta (ex.: fundo de super), desenhado em BG_B/PAL0 1..14 */
typedef struct {
    s16 anim_id;
    const Image *img;
    const u16 (*pals)[16];
    u8 npals;
    u8 nelem;
    const u8 *elem_pal;          /* por elemento da animacao: indice em pals (255 = sem mudanca) */
} MgBgFx;

typedef struct {
    mgfx life, attack, defence, liedown_time, airjuggle;
    mgfx ground_back, ground_front, air_back, air_front, height;
    mgfx walk_fwd, walk_back, run_fwd_x, run_fwd_y, run_back_x, run_back_y;
    mgfx jump_neu_x, jump_neu_y, jump_back_x, jump_fwd_x;
    mgfx yaccel, stand_friction, crouch_friction;
    s16  sparkno, guard_sparkno;           /* anim propria; -1 nenhuma */
    s16  powermax;                         /* [Data] power; 0 = padrao 3000 (dados gerados antes do campo) */
} MgConsts;
#define MG_POWERMAX(p) ((p)->def->consts->powermax ? (p)->def->consts->powermax : 3000)

typedef struct {
    const char *name;
    const MgSheet *sheets;         u16 nsheets;
    const MgAnim *anims;           u16 nanims;       /* ordenado por id */
    const MgAnimFrame *frames;
    const MgFramePart *parts;
    const MgBox *boxes;
    const u8 *code;
    const u16 *param_offs;
    const s16 *syms;
    const MgCtrl *ctrls;
    const MgState *states;         u16 nstates;      /* ordenado por id */
    const MgCommand *cmds;         u16 ncmds;
    const MgCmdStep *steps;
    const MgCmdKey *keys;
    const u8 *gates;               /* portoes de comando por controlador */
    const u16 *cmd_bucket_first;   /* [17]: comandos cujo 1o passo reage a evento da tecla k em cmd_bucket[first[k]..first[k+1]) */
    const u8 *cmd_bucket;
    const u8 *hold_cmds; u8 nhold_cmds;   /* comandos cujo 1o passo e so "/segurar" (testados todo tick) */
    const u32 *neg1_masks; u8 neg1_words; /* estado -1: [ncmds+1][words] controladores liberados por comando; ultima linha = sem portao */
    const u16 (*pals)[16];         u8 npals;
    u8 default_pal;
    const u16 *fxpal;
    const MgSound *sounds;         u16 nsounds;      /* indice = posicao no .snd original */
    const MgBgFx *bgfx;            u8 nbgfx;
    const MgConsts *consts;
    s16 st_minus1, st_minus2, st_minus3;             /* indices em states[] ou -1 */
    u16 cmd_holdfwd, cmd_holdback, cmd_holdup, cmd_holddown;  /* MG_NONE se ausente */
    const TileSet *portrait;       /* retrato 32x32 (4x4 tiles, paleta do corpo) ou 0 */
    const SpriteDefinition *shadow;/* sombra 32x8 pontilhada (silhueta 0,0 achatada) ou 0 */
    const u8 *native_code;         /* identity guard: cloned definitions may replace code[] */
    const MgExprFn *native_eval;   /* ROM dispatch table; optional, bytecode remains authoritative */
    u16 native_code_size;
    const TileSet *const *portrait_variants;
    u8 nportrait_variants;
    MgNativeMinus1Fn native_minus1;
    MgNativeStateFn native_state;
    const MgAnimFrame *elem_time_frames; /* identity guards for optional ROM timing data */
    const MgAnim *elem_time_anims;
    const s32 *elem_time_starts;
    u16 elem_time_count;
    u32 portrait_approved_mask; /* bit por variante; so acceptance_status=final pode ser desenhada */
} MgCharDef;

#endif
