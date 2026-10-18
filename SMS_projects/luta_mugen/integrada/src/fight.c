/* fight.c — motor de luta interpretado por tabelas MUGEN compiladas.
 *
 * A cena Ken e compilada de AIR/SFF/ACT e CNS para o header local derivado
 * (licença: não versionar bytes do personagem). Nenhum CNS roda no Z80.
 *
 * Leis do plano 2 implementadas aqui:
 *  - Tick de anim: if (++tick >= frames[frame].dur) avanca; sem anim =
 *    "dur" gerado, entao dur vem do AIR destilado (255 = segura).
 *  - Fisica Q8.8 SEM float: velocidades, gravidade e vida vêm do corte CNS.
 *  - Colisao: AABB de colunas inteiras lidas do blob CLSN (secao hit,
 *    sentinela -32767, secao hurt, sentinela). Frame sem CLSN herda o CLSN
 *    do frame 0 da anim (precedente: clsn2default do AIR).
 *  - Hit: hitstop=8 nos dois, knockback do contrato, dano destilado do CNS.
 *  - Sem pressao de VDP: tudo roda no loop; nada aloca (RAM estatica).
 *
 * P1 e P2 usam duas ACTs no único sprite palette do SMS: cada lado recebe
 * sete índices úteis, com P2 deslocado em oito (0 continua transparente).
 */
#include <string.h>
#include "SMSlib.h"
#include "luta.h"
#include "fight.h"
#include "stream.h"
#include "scene_trimmed.h"

#define FLOOR_PX   128                    /* mesmo chao medido da cena 01 */
#define X_MIN      (16u * 256u)           /* Q8.8 — borda util da arena */
#define X_MAX      (240u * 256u)

/* Estados semânticos do interpretador; parâmetros vêm do corte CNS. */
#define S_CONTROL   0x01
#define S_AIR       0x02
#define S_HIT       0x04
#define S_BLOCKABLE 0x08

typedef struct { unsigned short id;       /* ID MUGEN completo, sem truncamento */
                 unsigned char anim, flags;
                 signed int vel;          /* Q8.8 relativo ao facing */
                 unsigned char dmg; } StateDef;

enum { ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD,
       ST_PUNCH1, ST_PUNCH2, ST_SPECIAL, ST_KO, ST_N_STATES };

static const StateDef ken_states[ST_N_STATES] = {
    {   0, KEN_CUT_ANIM_IDLE,   S_CONTROL,                    0, 0 },
    {  20, KEN_CUT_ANIM_WALK_F, S_CONTROL, KEN_CUT_WALK_FWD_Q8, 0 },
    {  21, KEN_CUT_ANIM_WALK_B, S_CONTROL, KEN_CUT_WALK_BACK_Q8, 0 },
    {  40, KEN_CUT_ANIM_JUMP,   S_AIR,                         0, 0 },
    { 100, KEN_CUT_ANIM_CROUCH, S_CONTROL | S_BLOCKABLE,       0, 0 },
    { 120, KEN_CUT_ANIM_GUARD,  S_CONTROL | S_BLOCKABLE,       0, 0 },
    { 230, KEN_CUT_ANIM_PUNCH,  S_HIT, 0, KEN_CUT_DAMAGE_PUNCH },
    { 400, KEN_CUT_ANIM_KICK,   S_HIT, 0, KEN_CUT_DAMAGE_KICK },
    { 128, KEN_CUT_ANIM_SPECIAL, S_HIT, KEN_CUT_SPECIAL_VEL_Q8,
      KEN_CUT_DAMAGE_SPECIAL },
    { 5050, KEN_CUT_ANIM_KO, 0, 0, 0 },
};

static const StateDef ryu_states[ST_N_STATES] = {
    {   0, RYU_CUT_ANIM_IDLE,   S_CONTROL,                    0, 0 },
    {  20, RYU_CUT_ANIM_WALK_F, S_CONTROL, RYU_CUT_WALK_FWD_Q8, 0 },
    {  21, RYU_CUT_ANIM_WALK_B, S_CONTROL, RYU_CUT_WALK_BACK_Q8, 0 },
    {  40, RYU_CUT_ANIM_JUMP,   S_AIR,                         0, 0 },
    { 100, RYU_CUT_ANIM_CROUCH, S_CONTROL | S_BLOCKABLE,       0, 0 },
    { 120, RYU_CUT_ANIM_GUARD,  S_CONTROL | S_BLOCKABLE,       0, 0 },
    { 200, RYU_CUT_ANIM_PUNCH,  S_HIT, 0, RYU_CUT_DAMAGE_PUNCH },
    { 400, RYU_CUT_ANIM_KICK,   S_HIT, 0, RYU_CUT_DAMAGE_KICK },
    { 1300, RYU_CUT_ANIM_SPECIAL, S_HIT, RYU_CUT_SPECIAL_VEL_Q8,
      RYU_CUT_DAMAGE_SPECIAL },
    { 5050, RYU_CUT_ANIM_KO, 0, 0, 0 },
};

typedef struct {
    const Frame *frames;
    const Anim *anims;
    const StateDef *states;
    unsigned char pose_count, pose_base;
    unsigned short max_life;
    signed int jump_vy, gravity;
    unsigned char hitstop, hit_push, guard_push;
} CharacterData;

static const CharacterData characters[2] = {
    { ken_frames_all, ken_anims, ken_states, KEN_CUT_POSE_COUNT, KEN_POSE_BASE,
      KEN_CUT_MAX_LIFE, KEN_CUT_JUMP_VY_Q8, KEN_CUT_GRAVITY_Q8,
      KEN_CUT_HITSTOP, KEN_CUT_HIT_PUSH_PX, KEN_CUT_GUARD_PUSH_PX },
    { ryu_frames_all, ryu_anims, ryu_states, RYU_CUT_POSE_COUNT, RYU_POSE_BASE,
      RYU_CUT_MAX_LIFE, RYU_CUT_JUMP_VY_Q8, RYU_CUT_GRAVITY_Q8,
      RYU_CUT_HITSTOP, RYU_CUT_HIT_PUSH_PX, RYU_CUT_GUARD_PUSH_PX },
};

Fighter fighters[2];
volatile unsigned char dbg_frame;

static unsigned char prepared_pose[2], visible_pose[2];

/* ---- utilitarios ---- */

/* precedente MSSF2T fight.c:rebuild_meta — o terminador 0x80 so casa lido
 * ASSINADO (unsigned 128 != (signed)-128 promote a int). */
unsigned char meta_rebase(const unsigned char *meta, unsigned char base,
                          signed char *dst) {
    unsigned char n = 0;
    while ((signed char)meta[n] != (signed char)METASPRITE_END) {
        dst[n] = (signed char)meta[n];
        dst[n + 1] = (signed char)meta[n + 1];
        dst[n + 2] = (signed char)(base + meta[n + 2]);
        n += 3;
    }
    dst[n] = (signed char)METASPRITE_END;
    return n / 3;
}

static signed int rd16(const unsigned char *b) {
    return (signed int)((unsigned int)b[0] | ((unsigned int)b[1] << 8));
}

#define CLSN_END (-32767)

typedef struct { signed int l, t, r, b; } Rect;   /* px de tela */

static void clsn_read_box(const unsigned char *b, Box *o) {
    o->x1 = (signed char)rd16(b);     o->y1 = (signed char)rd16(b + 2);
    o->x2 = (signed char)rd16(b + 4); o->y2 = (signed char)rd16(b + 6);
}

/* caixa MUGEN (x relativo ao eixo, y<=0 acima do chao) -> AABB de tela. */
static void box_rect(const Fighter *p, const Box *b, Rect *r) {
    signed int xp = (signed int)(p->x >> 8);
    signed int alt = (signed int)(p->y >> 8);
    if (!p->facing) { r->l = xp + b->x1; r->r = xp + b->x2; }
    else            { r->l = xp - b->x2; r->r = xp - b->x1; }
    r->t = FLOOR_PX + b->y1 - alt;
    r->b = FLOOR_PX + b->y2 - alt;
}

static const Frame *cur_frame(const Fighter *p, unsigned char slot) {
    return &characters[slot].anims[p->anim].frames[p->frame];
}

static const Frame *frame_for_pose(unsigned char slot, unsigned char pose) {
    const CharacterData *cd = &characters[slot];
    if (pose < cd->pose_base || pose >= cd->pose_base + cd->pose_count)
        return &cd->frames[0];
    return &cd->frames[pose - cd->pose_base];
}

/* Usa a pose já copiada para a SAT; isso mantém hit/hurt sincronizados com
 * o frame que o VDP realmente mostra durante o streaming. */
static const unsigned char *hurt_clsn_visible(const Fighter *p, unsigned char slot) {
    const CharacterData *cd = &characters[slot];
    const Frame *f = frame_for_pose(slot, visible_pose[slot]);
    if (f->clsn) return f->clsn;
    return cd->anims[p->anim].frames[0].clsn;
}

static unsigned char boxes_overlap(const Fighter *attacker, const Fighter *defender,
                                   const unsigned char *hit_data,
                                   const unsigned char *hurt_data) {
    const unsigned char *hit = hit_data;
    const unsigned char *hurt_start = hurt_data;
    if (!hit || !hurt_start) return 0;
    while (rd16(hurt_start) != CLSN_END) hurt_start += 8;
    hurt_start += 2;                    /* sentinela entre hit e hurt */
    while (rd16(hit) != CLSN_END) {
        Box hb;
        Rect hr;
        const unsigned char *hurt = hurt_start;
        clsn_read_box(hit, &hb);
        box_rect(attacker, &hb, &hr);
        while (rd16(hurt) != CLSN_END) {
            Box ob;
            Rect or;
            clsn_read_box(hurt, &ob);
            box_rect(defender, &ob, &or);
            if (hr.l < or.r && or.l < hr.r && hr.t < or.b && or.t < hr.b)
                return 1;
            hurt += 8;
        }
        hit += 8;
    }
    return 0;
}

static void enter_state(Fighter *p, unsigned char slot, unsigned char s) {
    const CharacterData *cd = &characters[slot];
    p->state = s;
    p->anim = cd->states[s].anim;
    p->frame = 0;
    p->tick = 0;
    p->hit_done = 0;
    if (s == ST_JUMP) p->vy = cd->jump_vy;     /* impulso único ao sair do chão */
}

static void clamp_x(Fighter *p) {
    if (p->x < X_MIN) p->x = X_MIN;
    if (p->x > X_MAX) p->x = X_MAX;
}

/* ---- API ---- */

static const PoseTiles *pose_tiles(unsigned char slot, unsigned char pose) {
    const CharacterData *cd = &characters[slot];
    unsigned char i = (unsigned char)(pose - cd->pose_base);
    return slot ? &ryu_pose_tiles[i] : &ken_pose_tiles[i];
}

void fight_init(void) {
    stream_init();
}

void fight_reset(Fighter *p, unsigned char slot) {
    const CharacterData *cd = &characters[slot];
    p->facing = slot ? 1 : 0;
    p->x = slot ? (152u * 256u) : (96u * 256u);
    p->y = 0;
    p->vx = 0;
    p->vy = 0;
    p->life = cd->max_life;
    p->hitstop = 0;
    p->keys_prev = 0;
    enter_state(p, slot, ST_IDLE);
    /* carga bloqueante do idle: no boot nao pode existir frame com pose
     * exibida sem tiles (audit_deterministic_boot fotografa o frame 0). */
    {
        unsigned char pose = (unsigned char)(cd->pose_base +
            cd->anims[cd->states[ST_IDLE].anim].frames[0].pose);
        stream_load_now(slot, pose_tiles(slot, pose), p->facing, pose);
        prepared_pose[slot] = visible_pose[slot] = pose;
    }
}

void fight_set_ko(Fighter *p) {
    unsigned char slot = (p == &fighters[0]) ? 0 : 1;
    p->vx = 0;
    p->vy = 0;
    p->hitstop = 0;
    enter_state(p, slot, ST_KO);
}

/* Anim clock shared by the idle hold and the full step. Behavior matches
 * the block that used to live inside fight_step: the tick advances only
 * while the wanted pose is the one on screen. */
static void tick_anim(Fighter *p, unsigned char pslot) {
    const CharacterData *cd = &characters[pslot];
    const Anim *a = &cd->anims[p->anim];
    const Frame *fr = &a->frames[p->frame];
    unsigned char wanted_pose = (unsigned char)(cd->pose_base + fr->pose);
    if (visible_pose[pslot] != wanted_pose || fr->dur == 255) return;
    if (++p->tick < fr->dur) return;
    p->tick = 0;
    if (p->frame + 1 >= a->n_frames) {
        if (a->loop_start != 255) p->frame = a->loop_start;
        else enter_state(p, pslot, ST_IDLE);
    } else {
        p->frame++;
    }
}

/* Grounded idle, no key held. The full step's SDCC frame is 37 bytes and
 * costs ~18 scanlines per fighter; an idle probe never needs that frame.
 * Idle rows are S_CONTROL, vel 0, without S_AIR or S_HIT. */
static unsigned char fight_step_full(Fighter *p, unsigned int keys, unsigned int opp_keys);

unsigned char fight_step(Fighter *p, unsigned int keys, unsigned int opp_keys) {
    unsigned char pslot;
    Fighter *o;
    if (p->hitstop || p->state != ST_IDLE || p->y != 0 || keys != 0)
        return fight_step_full(p, keys, opp_keys);
    pslot = (p == &fighters[0]) ? 0 : 1;
    o = pslot ? &fighters[0] : &fighters[1];
    p->facing = (o->x > p->x) ? 0 : 1;
    p->keys_prev = 0;
    tick_anim(p, pslot);
    return FIGHT_EVENT_NONE;
}

static unsigned char fight_step_full(Fighter *p, unsigned int keys, unsigned int opp_keys) {
    const StateDef *sd;
    const CharacterData *cd;
    Fighter *o;
    unsigned int pressed;
    unsigned int fwdk, backk;
    unsigned char ns, pslot, oslot, event = FIGHT_EVENT_NONE;

    (void)opp_keys;   /* resumo p/ Task 5 (clash); hit reciproco usa fighters[] */

    if (p->hitstop) { p->hitstop--; return FIGHT_EVENT_NONE; }

    /* adversario por comparacao de endereco: (p - fighters) exigiria
     * __divsint por sizeof(Fighter)=18 — um call de biblioteca por frame
     * dentro do orcamento de VBlank (L061). */
    o = (p == &fighters[0]) ? &fighters[1] : &fighters[0];
    pslot = (p == &fighters[0]) ? 0 : 1;
    oslot = (unsigned char)(1u - pslot);
    cd = &characters[pslot];
    sd = &cd->states[p->state];

    if ((sd->flags & S_CONTROL) && p->y == 0) {
        /* auto-facing de solo; transicoes por precissao de borda em
         * UP/ataques (senao tecla segura reiniciaria o golpe todo frame). */
        p->facing = (o->x > p->x) ? 0 : 1;
        pressed = keys & ~p->keys_prev;
        if (p->facing) { fwdk = K_LEFT;  backk = K_RIGHT; }
        else           { fwdk = K_RIGHT; backk = K_LEFT;  }
        ns = p->state;
        if (pressed & K_SPECIAL)         ns = ST_SPECIAL;
        else if (pressed & K_LP)         ns = ST_PUNCH1;
        else if (pressed & K_HP)         ns = ST_PUNCH2;
        else if (pressed & K_UP)         ns = ST_JUMP;
        else if ((keys & K_GUARD) || ((keys & K_DOWN) && (keys & backk))) ns = ST_GUARD;
        else if (keys & K_DOWN)          ns = ST_CROUCH;
        else if (keys & fwdk)            ns = ST_WALK_F;
        else if (keys & backk)           ns = ST_WALK_B;
        else                             ns = ST_IDLE;
        p->keys_prev = keys;
        if (ns != p->state) {
            enter_state(p, pslot, ns);
            sd = &cd->states[ns];
            if (ns == ST_PUNCH1) event = FIGHT_EVENT_PUNCH;
            else if (ns == ST_PUNCH2) event = FIGHT_EVENT_KICK;
            else if (ns == ST_SPECIAL) event = FIGHT_EVENT_SPECIAL;
        }
    }

    /* fisica */
    if (sd->flags & S_AIR) {
        p->vy -= cd->gravity;
        if (p->vy >= 0) {
            p->y += (unsigned int)p->vy;
        } else if ((signed int)p->y >= -p->vy) {
            p->y += (unsigned int)p->vy;
        } else {
            p->y = 0;
            p->vy = 0;
            enter_state(p, pslot, ST_IDLE);
            sd = &cd->states[ST_IDLE];
        }
    } else if (sd->vel) {
        p->x = (unsigned int)((signed int)p->x +
                              (p->facing ? -sd->vel : sd->vel));
        clamp_x(p);
    }

    /* A logica espera o padrao da pose atual estar realmente visivel.
     * Sem isso, um frame de ataque curto pode atravessar o buffer duplo
     * antes de seus tiles chegarem a VRAM e a janela CLSN nunca aparece. */
    tick_anim(p, pslot);

    /* checagem de hit: janela = frame com caixa de golpe no blob CLSN
     * (destilado do HitDef trigger time=3 — o frame startup E a janela). */
    sd = &cd->states[p->state];
    if ((sd->flags & S_HIT) && !p->hit_done) {
        const Frame *attack_frame = frame_for_pose(pslot, visible_pose[pslot]);
        if (boxes_overlap(p, o, attack_frame->clsn,
                          hurt_clsn_visible(o, oslot))) {
            unsigned char push = cd->hit_push;
            p->hit_done = 1;
            /* Guarda bloqueia apenas de frente e no chão. */
            if ((characters[oslot].states[o->state].flags & S_BLOCKABLE) &&
                o->y == 0 &&
                o->facing != p->facing) {
                push = cd->guard_push;
            } else {
                if (o->life >= sd->dmg) o->life -= sd->dmg;
                else o->life = 0;
            }
            o->hitstop = cd->hitstop;
            p->hitstop = cd->hitstop;
            o->x = (unsigned int)((signed int)o->x +
                                  (p->facing ? -(signed int)push * 256
                                             : (signed int)push * 256));
            clamp_x(o);
        }
    }
    return event;
}

/* ---- render: pool slots + per-row flicker scheduler (option 3) ----
 *
 * Pieces of a fighter's metasprite sit in TALL rows (dy multiple of 16,
 * checked by gen_pose_table.py). A scanline therefore sees one row of each
 * fighter, and the VDP limit becomes: for every pair of rows that overlap
 * vertically, kept(Ken row) + kept(Ryu row) <= 8, and any single row <= 8.
 * Overlapping rows share the eight slots in proportion to their original
 * widths. Two parities round the Ken share down/up; neither can increase a
 * quota already reduced by another overlap. Omitted pieces rotate inside
 * each row; the framebuffer gate checks coverage over eight frames. */
#define ROWS_MAX 10u
#define LINE_LIMIT 8u

/* Per fighter row geometry, flat arrays [fighter * ROWS_MAX + row]. Row
 * counts and sizes come from the offline row table (gen_pose_table.py):
 * walking pieces in C cost ~600 cycles each (measured ~70 lines/fighter). */
/* One block so the scheduler assembly can index y/n/keep with fixed
 * offsets from IX/IY: y at +0, n at +20, keep at +40. */
static unsigned char rowdat[6 * ROWS_MAX];
#define row_y    (rowdat)
#define row_n    (rowdat + 2 * ROWS_MAX)
#define row_keep (rowdat + 4 * ROWS_MAX)
typedef char rowdat_offsets_are_20_40[(ROWS_MAX == 10u) ? 1 : -1];
static unsigned char rows[2];
static unsigned char draw_facing[2];
static unsigned char sched_frame;
/* Emitted pieces per fighter <= pieces of its pose (38 max, pose_table). */
#define OUT_PIECES 40u
typedef char out_pieces_fit[(KEN_POSE_MAX_PIECES <= OUT_PIECES &&
                             RYU_POSE_MAX_PIECES <= OUT_PIECES) ? 1 : -1];
/* Own sprite attribute table in RAM, written by the emit assembly and copied
 * to VRAM in VBlank by sat_upload(). Building a metasprite and then having
 * SMS_addMetaSprite parse it again cost ~100 lines/frame for ~50 pieces.
 * The SAT address is set explicitly (VDP register 5 = 0xFF -> 0x3F00) in
 * sat_setup(); nothing depends on SMSlib internals. Only assembly touches
 * these buffers, so volatile (required by the L009 pre-gate) costs nothing. */
#define SAT_VRAM_Y  0x3F00u
#define SAT_VRAM_XT 0x3F80u
volatile unsigned char __at(0xD000) sat_y[72];
volatile unsigned char __at(0xD048) sat_xt[144];
unsigned char sat_count;

unsigned char render_dropped;          /* telemetry: pieces withheld this frame */
__sfr __at (0x7e) fight_vcounter;
volatile unsigned char __at(0xC7C0) tl_rd_req;     /* render sub-phase stamps */
volatile unsigned char __at(0xC7C1) tl_rd_scan;
volatile unsigned char __at(0xC7C2) tl_rd_sched;
volatile unsigned char __at(0xC7C3) tl_rd_emit;
volatile unsigned char __at(0xC7C4) tl_rd_add;
volatile unsigned char __at(0xC7C5) tl_rd_start;
volatile unsigned char __at(0xC7C6) tl_stable_hits;
volatile unsigned char __at(0xC7C7) tl_np[5];   /* non-stable path stamps */

/* Row table in POSE_META_BANK: [count, (dy, pieces)...]. Screen row tops as
 * 8-bit (wrap is harmless: only differences are compared). */
/* Returns 1 when the row geometry (count, tops, sizes) actually changed;
 * the schedule is recomputed only then (it cost ~165 lines per pose change,
 * and most idle poses share the same rows). */
static unsigned char load_rows(unsigned char i, const unsigned char *t, unsigned char sy) {
    unsigned char *y = &row_y[i * ROWS_MAX];
    unsigned char *n = &row_n[i * ROWS_MAX];
    unsigned char c = *t++, v, changed = 0;
    if (c > ROWS_MAX) c = ROWS_MAX;
    if (rows[i] != c) { rows[i] = c; changed = 1; }
    for (; c; c--, y++, n++) {
        v = (unsigned char)(sy + *t++);
        if (*y != v) { *y = v; changed = 1; }
        v = *t++;
        if (*n != v) { *n = v; changed = 1; }
    }
    return changed;
}

/* ---- emit: write a run of pieces into the RAM SAT (assembly) ----
 * in : er_src (pieces dx,dy,tile in POSE_META_BANK), er_map, er_n (>= 1),
 *      er_sx/er_sy (8-bit origin), er_ydst/er_xdst (SAT RAM cursors)
 * out: cursors advanced. y = sy + dy - 1 (the VDP draws a sprite one line
 * below its SAT y), x = sx + dx, tile = map[tile >> 1] << 1. */
static const unsigned char *er_src;
static const unsigned char *er_map;
static unsigned char er_n, er_sx, er_sy, er_x;
static unsigned char *er_ydst, *er_xdst;

/* Per-frame copier: pieces come from the per-fighter template (tile already
 * remapped), so each piece is x = sx + dx, y = sy + dy - 1, tile copy;
 * IX walks the x/tile table (~145 cycles/piece instead of ~290 with the map
 * lookup). IX is SDCC's frame pointer: saved and restored. */
static void emit_run_asm(void) __naked {
    __asm
        push ix
        ld ix, (_er_xdst)
        ld hl, (_er_src)
        ld de, (_er_ydst)
        ld a, (_er_sx)
        ld c, a
        ld a, (_er_n)
        ld b, a
    er_loop:
        ld a, (hl)
        add a, c
        ld 0 (ix), a
        inc hl
        ld a, (_er_sy)
        add a, (hl)
        dec a
        ld (de), a
        inc de
        inc hl
        ld a, (hl)
        ld 1 (ix), a
        inc hl
        inc ix
        inc ix
        djnz er_loop
        ld (_er_xdst), ix
        ld (_er_ydst), de
        ld (_er_src), hl
        pop ix
        ret
    __endasm;
}

/* On a display change: pieces of the pruned metasprite (POSE_META_BANK,
 * mapped by the caller) -> template (dx, dy, pool tile). Stops at 0x80. */
volatile unsigned char __at(0xD100) tmpl[2][3 * OUT_PIECES];
static unsigned char *bt_dst;

static void build_tmpl_asm(void) __naked {
    __asm
        ld hl, (_er_src)
        ld de, (_bt_dst)
    bt_loop:
        ld a, (hl)
        cp #0x80
        ret z
        ld (de), a
        inc hl
        inc de
        ld a, (hl)
        ld (de), a
        inc hl
        inc de
        ld a, (hl)
        inc hl
        srl a
        push hl
        ld hl, (_er_map)
        add a, l
        ld l, a
        adc a, h
        sub a, l
        ld h, a
        ld a, (hl)
        add a, a
        pop hl
        ld (de), a
        inc de
        jr bt_loop
    __endasm;
}

static void build_template(unsigned char i, const unsigned char *meta, const unsigned char *map) {
    er_src = meta;
    er_map = map;
    bt_dst = (unsigned char *)tmpl[i];
    build_tmpl_asm();
}

/* Registers + VBlank upload of the RAM SAT. */
void sat_setup(void) {
    SMS_VDPControlPort = 0xFFu;          /* VDP register 5: SAT at 0x3F00 */
    SMS_VDPControlPort = 0x85u;
}

static unsigned char su_n;
/* Copy y[0..n] (terminator included when n < 64) then x/tile[0..2n) with
 * OUTI; call in VBlank (or with the display off). */
void sat_upload(void) __naked {
    __asm
        ld a, (_sat_count)
        ld (_su_n), a
        di
        ld a, #0x00
        out (0xbf), a
        ld a, #0x7F
        out (0xbf), a
        ei
        ld hl, #_sat_y
        ld c, #0xbe
        ld a, (_su_n)
        cp #64
        jr nc, su_y_full
        inc a
    su_y_full:
        ld b, a
    su_y:
        outi
        jr nz, su_y
        ld a, (_su_n)
        or a
        ret z
        di
        ld a, #0x80
        out (0xbf), a
        ld a, #0x7F
        out (0xbf), a
        ei
        ld hl, #_sat_xt
        ld a, (_su_n)
        add a, a
        ld b, a
    su_xt:
        outi
        jr nz, su_xt
        ret
    __endasm;
}

/* Dropped pieces of a row are the rotating window [rot, rot + drop) mod n,
 * so the kept ones are at most two contiguous runs. rot advances by drop
 * every frame (row_rot, per row, no multiply). */
static unsigned char row_rot[2 * ROWS_MAX];

/* Row loop in assembly (the C version measured ~73 lines/frame for both
 * fighters). Same algorithm as documented above; state through globals:
 *   er_src/er_map/SAT cursors as for emit_run_asm, em_n/em_k/em_r = row sizes,
 *   kept counts and rotations of this fighter, em_rows = row count.
 * Writes the 0x80 terminator and adds the withheld pieces to
 * render_dropped. */
static const unsigned char *em_n, *em_k;
static unsigned char *em_r;
static unsigned char em_rows, em_cnt, em_drop, em_rot, em_head;

static void emit_rows_asm(void) __naked {
    __asm
    em_row:
        ld a, (_em_rows)
        or a
        jp z, em_done
        ld hl, (_em_n)
        ld a, (hl)
        ld (_em_cnt), a
        ld b, a
        ld hl, (_em_k)
        ld a, b
        sub a, (hl)
        ld (_em_drop), a
        jr nz, em_has_drop
        ld a, b
        call em_copy
        jp em_next
    em_has_drop:
        ld c, a
        ld a, (_render_dropped)
        add a, c
        ld (_render_dropped), a
        ld hl, (_em_r)
        ld a, (hl)
        cp b
        jr c, em_rot_ok
        xor a
    em_rot_ok:
        ld (_em_rot), a
        add a, c
        cp b
        jr z, em_case1
        jr nc, em_case2
    em_case1:
        ld a, (_em_rot)
        call em_copy
        ld a, (_em_drop)
        call em_skip
        ld a, (_em_cnt)
        ld hl, #_em_rot
        sub a, (hl)
        ld hl, #_em_drop
        sub a, (hl)
        call em_copy
        jr em_advance
    em_case2:
        ld hl, #_em_cnt
        sub a, (hl)
        ld (_em_head), a
        call em_skip
        ld a, (_em_rot)
        ld hl, #_em_head
        sub a, (hl)
        call em_copy
        ld a, (_em_cnt)
        ld hl, #_em_rot
        sub a, (hl)
        call em_skip
    em_advance:
        ld a, (_em_rot)
        ld hl, #_em_drop
        add a, (hl)
        ld hl, #_em_cnt
        cp (hl)
        jr c, em_store
        sub a, (hl)
    em_store:
        ld hl, (_em_r)
        ld (hl), a
    em_next:
        ld hl, (_em_n)
        inc hl
        ld (_em_n), hl
        ld hl, (_em_k)
        inc hl
        ld (_em_k), hl
        ld hl, (_em_r)
        inc hl
        ld (_em_r), hl
        ld hl, #_em_rows
        dec (hl)
        jp em_row
    em_done:
        ret
    em_copy:
        or a
        ret z
        ld (_er_n), a
        jp _emit_run_asm
    em_skip:
        or a
        ret z
        ld c, a
        add a, a
        add a, c
        ld hl, (_er_src)
        add a, l
        ld l, a
        adc a, h
        sub a, l
        ld h, a
        ld (_er_src), hl
        ret
    __endasm;
}

static void emit(unsigned char i, const unsigned char *keep, unsigned char sx,
                 unsigned char sy) {
    er_src = (const unsigned char *)tmpl[i];
    er_sx = sx;
    er_sy = sy;
    em_n = &row_n[i * ROWS_MAX];
    em_k = keep;
    em_r = &row_rot[i * ROWS_MAX];
    em_rows = rows[i];
    emit_rows_asm();
}

/* Pose AIR shows after the current frame of p's animation. */
static unsigned char next_pose(const Fighter *p, unsigned char slot) {
    const CharacterData *cd = &characters[slot];
    const Anim *a = &cd->anims[p->anim];
    unsigned char f = (unsigned char)(p->frame + 1u);
    if (f >= a->n_frames) {
        if (a->loop_start != 255u) f = a->loop_start;
        else {
            a = &cd->anims[cd->states[ST_IDLE].anim];
            f = 0;
        }
    }
    return (unsigned char)(cd->pose_base + a->frames[f].pose);
}

/* Per-fighter render cache: recomputed only when its input changes.
 * The first integrated build redid all of this every frame (~60 lines for
 * the pose lookups/origin and ~40 for the scheduler). */
typedef struct {
    unsigned char anim, frame, facing;           /* logic key */
    unsigned char want_pose, next_pose_c;
    const PoseTiles *want_pt, *next_pt;
    unsigned char disp_pose, disp_facing;        /* display key */
    const unsigned char *meta, *map, *rowt;
    signed int ax, ay;
    unsigned char width;
    unsigned char sy;                            /* rows' origin */
    unsigned char stable;       /* display == wanted and prefetch issued */
    unsigned int x_cached;
    signed int sx;
} DrawCache;
static DrawCache dc[2];
static unsigned char keep_par[2][2 * ROWS_MAX];  /* schedule for parity 0/1 */
static unsigned char sched_valid;
/* Fighter allowed to allocate when both need a new target this iteration.
 * The one deferred becomes first on the next fight_draw. */
static unsigned char alloc_turn;
/* Row schedule moves to the next iteration, which then skips the upload. */
static unsigned char sched_due;
static unsigned char emitted_once;

unsigned char fight_skip_stream(void) {
    return sched_due;
}

/* Proportional shares for min(n, 8), indexed by Ken * 9 + Ryu.
 * floor/ceil alternate the fractional slot without a division in the Z80
 * loop. A row keeps its quota when it does not overlap another actor. */
static const unsigned char sc_floor[81] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0,
    8, 4, 2, 2, 1, 1, 1, 1, 0,
    8, 5, 4, 3, 2, 2, 2, 1, 1,
    8, 6, 4, 4, 3, 3, 2, 2, 2,
    8, 6, 5, 4, 4, 3, 3, 2, 2,
    8, 6, 5, 5, 4, 4, 3, 3, 3,
    8, 6, 6, 5, 4, 4, 4, 3, 3,
    8, 7, 6, 5, 5, 4, 4, 4, 3,
    8, 7, 6, 5, 5, 4, 4, 4, 4,
};
static const unsigned char sc_ceil[81] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0,
    8, 4, 3, 2, 2, 2, 2, 1, 1,
    8, 6, 4, 4, 3, 3, 2, 2, 2,
    8, 6, 5, 4, 4, 3, 3, 3, 3,
    8, 7, 6, 5, 4, 4, 4, 3, 3,
    8, 7, 6, 5, 5, 4, 4, 4, 4,
    8, 7, 6, 6, 5, 5, 4, 4, 4,
    8, 7, 7, 6, 6, 5, 5, 4, 4,
    8, 8, 7, 6, 6, 5, 5, 5, 4,
};
static const unsigned char *sc_table;
static unsigned char sc_cnt0;
static void schedule_asm(void) __naked {
    __asm
        ld hl, #_rowdat+20
        ld de, #_rowdat+40
        ld b, #20
    sc_init:
        ld a, (hl)
        cp #9
        jr c, sc_i1
        ld a, #8
    sc_i1:
        ld (de), a
        inc hl
        inc de
        djnz sc_init
        push ix
        push iy
        ld ix, #_rowdat
        ld a, (_rows)
        or a
        jp z, sc_done
        ld (_sc_cnt0), a
    sc_outer:
        ld iy, #_rowdat+10
        ld a, (_rows+1)
        or a
        jp z, sc_outer_next
        ld b, a
    sc_inner:
        ld a, 0 (ix)
        sub a, 0 (iy)
        add a, #15
        cp #31
        jr nc, sc_skip
        ld a, 40 (ix)
        add a, 40 (iy)
        cp #9
        jr c, sc_skip
        ld a, 20 (ix)
        cp #9
        jr c, sc_n0
        ld a, #8
    sc_n0:
        ld c, a
        add a, a
        add a, a
        add a, a
        add a, c
        ld c, a
        ld a, 20 (iy)
        cp #9
        jr c, sc_n1
        ld a, #8
    sc_n1:
        add a, c
        ld hl, (_sc_table)
        add a, l
        ld l, a
        adc a, h
        sub a, l
        ld h, a
        ld a, (hl)
        ld c, a
        cp 40 (ix)
        jr nc, sc_keep_k
        ld 40 (ix), a
    sc_keep_k:
        ld a, #8
        sub a, c
        cp 40 (iy)
        jr nc, sc_skip
        ld 40 (iy), a
    sc_skip:
        inc iy
        djnz sc_inner
    sc_outer_next:
        inc ix
        ld hl, #_sc_cnt0
        dec (hl)
        jp nz, sc_outer
    sc_done:
        pop iy
        pop ix
        ret
    __endasm;
}

static void compute_schedules(void) {
    sc_table = sc_floor;
    schedule_asm();
    memcpy(keep_par[0], row_keep, 2 * ROWS_MAX);
    sc_table = sc_ceil;
    schedule_asm();
    memcpy(keep_par[1], row_keep, 2 * ROWS_MAX);
}

void fight_draw(void) {
    unsigned char i, pass, rows_changed = 0, defer_emit = 0;
    unsigned char n_alloc = 0, heavy_used = 0, deferred = 0xFFu;
    unsigned char held_pose[2];
    signed int sx[2];
    unsigned char sy8;

    held_pose[0] = prepared_pose[0];
    held_pose[1] = prepared_pose[1];

    tl_rd_start = fight_vcounter;
    render_dropped = 0;
    /* pruned metasprites and row tables are read from POSE_META_BANK */
    SMS_saveROMBank();
    SMS_mapROMBank(POSE_META_BANK);
    for (pass = 0; pass < 2; pass++) {
        i = (unsigned char)(alloc_turn ^ pass);
        Fighter *p = &fighters[i];
        DrawCache *c = &dc[i];
        unsigned char display_pose;
        if (c->stable && c->anim == p->anim && c->frame == p->frame &&
            c->facing == p->facing) {
            /* Nothing to present or request: the wanted pose is displayed and
             * its successor was already requested (stream calls skipped; they
             * cost ~25 lines/fighter per frame in SDCC code). */
            prepared_pose[i] = c->disp_pose;
            tl_stable_hits++;
            if (p->x != c->x_cached) {
                c->x_cached = p->x;
                c->sx = c->disp_facing
                    ? FIGHTER_MIRRORED_ORIGIN_X((signed int)(p->x >> 8), c->ax, c->width)
                    : (signed int)(p->x >> 8) + c->ax;
            }
            sx[i] = c->sx;
            continue;
        }
        /* The second unstable fighter keeps the pose already on screen.
         * Both of them in one iteration measured scan ~130 on ROM ea856217
         * and crossed the next VBlank. Boot still builds both (meta == 0). */
        if (heavy_used && c->meta) {
            deferred = i;
            prepared_pose[i] = c->disp_pose;
            if (p->x != c->x_cached) {
                c->x_cached = p->x;
                c->sx = c->disp_facing
                    ? FIGHTER_MIRRORED_ORIGIN_X((signed int)(p->x >> 8), c->ax, c->width)
                    : (signed int)(p->x >> 8) + c->ax;
            }
            sx[i] = c->sx;
            continue;
        }
        heavy_used = 1;
        c->stable = 0;
        tl_np[0] = fight_vcounter;
        if (c->anim != p->anim || c->frame != p->frame || c->facing != p->facing ||
            !c->want_pt) {
            const CharacterData *cd = &characters[i];
            c->anim = p->anim;
            c->frame = p->frame;
            c->facing = p->facing;
            c->want_pose = (unsigned char)(cd->pose_base + cur_frame(p, i)->pose);
            c->want_pt = pose_tiles(i, c->want_pose);
            c->next_pose_c = next_pose(p, i);
            c->next_pt = pose_tiles(i, c->next_pose_c);
        }
        tl_np[1] = fight_vcounter;
        /* Prefetch: while the wanted pose is displayed, stream the pose AIR
         * shows next, so it is resident when the logic advances and each pose
         * keeps exactly its AIR duration. Input changes drop it.
         * At most one allocate per iteration. The other fighter keeps the
         * pose already on screen and is first on the next fight_draw. */
        {
            const PoseTiles *req_pt;
            unsigned char req_pose, skip = 0;
            if (stream_shows(i, c->want_pt, p->facing)) {
                req_pt = c->next_pt;
                req_pose = c->next_pose_c;
            } else {
                req_pt = c->want_pt;
                req_pose = c->want_pose;
            }
            if (stream_will_allocate(i, req_pt, p->facing)) {
                if (n_alloc) {
                    skip = 1;
                    deferred = i;
                } else {
                    n_alloc = 1;
                }
            }
            if (!skip)
                stream_request(i, req_pt, p->facing, req_pose);
        }
        tl_np[2] = fight_vcounter;
        {
            const unsigned char *meta, *map, *rowt;
            unsigned char fac;
            display_pose = stream_display(i, c->want_pt, p->facing, &meta, &map, &fac, &rowt);
            if (display_pose != c->disp_pose || fac != c->disp_facing || meta != c->meta) {
                const Frame *fd = frame_for_pose(i, display_pose);
                c->disp_pose = display_pose;
                c->disp_facing = fac;
                c->meta = meta;
                c->rowt = rowt;
                c->ax = rd16(fd->axis);
                c->ay = rd16(fd->axis + 2);
                c->width = fd->width;
                c->sy = 0xFFu;                   /* force row reload */
                build_template(i, meta, map);     /* pool tiles fixed per display */
            }
            c->map = map;
        }
        tl_np[3] = fight_vcounter;
        prepared_pose[i] = display_pose;
        draw_facing[i] = c->disp_facing;
        c->x_cached = p->x;
        c->sx = sx[i] = c->disp_facing
            ? FIGHTER_MIRRORED_ORIGIN_X((signed int)(p->x >> 8), c->ax, c->width)
            : (signed int)(p->x >> 8) + c->ax;
        /* Stable once the displayed pose is the wanted one and the prefetch
         * of its successor has been requested (it will be presented only
         * when the logic advances, which changes anim/frame). A deferred
         * allocate must not mark stable: the early-out would never request. */
        if (deferred != i &&
            display_pose == c->want_pose && c->disp_facing == p->facing &&
            stream_shows(i, c->want_pt, p->facing))
            c->stable = 1;
        sy8 = (unsigned char)(FLOOR_PX + c->ay - (signed int)(p->y >> 8));
        if (sy8 != c->sy) {
            c->sy = sy8;
            if (load_rows(i, c->rowt, sy8)) rows_changed = 1;
        }
        tl_np[4] = fight_vcounter;
    }
    if (deferred != 0xFFu) alloc_turn = deferred;
    tl_rd_scan = fight_vcounter;
    /* Presenting and scheduling in the same iteration measured ~300 ticks
     * from VCounter 194 (budget 254). The schedule runs next frame, with
     * the upload skipped, and this frame keeps the SAT already on screen. */
    if (!sched_valid || (sched_due && !rows_changed)) {
        compute_schedules();
        sched_valid = 1;
        sched_due = 0;
    } else if (rows_changed) {
        sched_due = 1;
        defer_emit = 1;
        stream_cancel_present();
    }
    if (emitted_once && n_alloc && !stream_presenting())
        defer_emit = 1;
    tl_rd_sched = fight_vcounter;
    if (defer_emit) {
        prepared_pose[0] = held_pose[0];
        prepared_pose[1] = held_pose[1];
    } else {
        er_ydst = (unsigned char *)sat_y;
        er_xdst = (unsigned char *)sat_xt;
        emit(0, &keep_par[sched_frame & 1u][0], (unsigned char)sx[0], dc[0].sy);
        emit(1, &keep_par[sched_frame & 1u][ROWS_MAX], (unsigned char)sx[1], dc[1].sy);
        sat_count = (unsigned char)(er_ydst - (unsigned char *)sat_y);
        if (sat_count > 64u) sat_count = 64u;   /* budget says <= 63; never more */
        if (sat_count < 64u) sat_y[sat_count] = 0xD0u;   /* list terminator */
        emitted_once = 1;
    }
    tl_rd_emit = fight_vcounter;
    SMS_restoreROMBank();
    tl_rd_add = fight_vcounter;
    sched_frame++;
}

/* Call immediately after sat_upload: `prepared_pose` is exactly
 * the pose whose pairs and metasprite the VDP now displays. */
void fight_sat_copied(void) {
    stream_sat_copied();
    visible_pose[0] = prepared_pose[0];
    visible_pose[1] = prepared_pose[1];
}

void fight_upload_palette(void) {
    static unsigned char loaded;
    if (!loaded) {
        SMS_loadSpritePalette(versus_sprite_palette);
        loaded = 1;
    }
}

unsigned short fight_max_life(unsigned char slot) {
    return characters[slot].max_life;
}

/* ---- telemetry queries (visible = what the VDP shows) ---- */
unsigned char fight_visible_pose(unsigned char slot) {
    return visible_pose[slot];
}

unsigned char fight_visible_dur(unsigned char slot) {
    return frame_for_pose(slot, visible_pose[slot])->dur;
}

/* Hit section of the visible pose's CLSN is non-empty. */
unsigned char fight_visible_hitbox(unsigned char slot) {
    const unsigned char *c = frame_for_pose(slot, visible_pose[slot])->clsn;
    return c && rd16(c) != CLSN_END;
}

/* First pose number of the animation the logic is currently in. */
unsigned char fight_state_pose0(unsigned char slot) {
    const CharacterData *cd = &characters[slot];
    return (unsigned char)(cd->pose_base + cd->anims[fighters[slot].anim].frames[0].pose);
}
