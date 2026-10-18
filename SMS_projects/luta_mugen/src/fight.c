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
#include "SMSlib.h"
#include "luta.h"
#include "fight.h"
#include "stream.h"
#include "../out/local_study/generated/versus_cut/versus_scene_runtime.h"

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

/* 40 B = até 13 entradas + terminador; o corte cabe em 4 colunas x 3 linhas
 * TALL, como exige o contrato de escala do GDD. */
static signed char meta_ram[2][40];
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

void fight_init(void) {
    stream_init(versus_poses, (unsigned char)VERSUS_POSE_COUNT);
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
    stream_load_now(slot, (unsigned char)(cd->pose_base +
                        cd->anims[cd->states[ST_IDLE].anim].frames[0].pose));
    prepared_pose[slot] = visible_pose[slot] = stream_disp(slot);
}

void fight_set_ko(Fighter *p) {
    unsigned char slot = (p == &fighters[0]) ? 0 : 1;
    p->vx = 0;
    p->vy = 0;
    p->hitstop = 0;
    enter_state(p, slot, ST_KO);
}

unsigned char fight_step(Fighter *p, unsigned int keys, unsigned int opp_keys) {
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

    /* tick de animacao */
    {
        const Anim *a = &cd->anims[p->anim];
        unsigned char wanted_pose = (unsigned char)(cd->pose_base +
            a->frames[p->frame].pose);
        /* A logica espera o padrao da pose atual estar realmente visivel.
         * Sem isso, um frame de ataque curto pode atravessar o buffer duplo
         * antes de seus tiles chegarem a VRAM e a janela CLSN nunca aparece. */
        if (visible_pose[pslot] == wanted_pose &&
            a->frames[p->frame].dur != 255 &&
            ++p->tick >= a->frames[p->frame].dur) {
            p->tick = 0;
            if (p->frame + 1 >= a->n_frames) {
                if (a->loop_start != 255) p->frame = a->loop_start;
                else enter_state(p, pslot, ST_IDLE);
            } else {
                p->frame++;
            }
        }
    }

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

void fight_draw(void) {
    unsigned char i;

    /* projeteis antes dos lutadores: nenhum no corte atual */
    for (i = 0; i < 2; i++) {
        Fighter *p = &fighters[i];
        const CharacterData *cd = &characters[i];
        /* LOGICA decide a pose pedida; PIXEL so mostram a pose EXIBIDA
         * (stream.h: pedida em N, aplicada em N+2 — latencia e design). */
        const Frame *flog = cur_frame(p, i);
        unsigned char display_pose = stream_disp(i);
        unsigned char wanted_pose = (unsigned char)(cd->pose_base + flog->pose);
        const Frame *fd;
        const unsigned char *meta;
        signed int ax, ay;
        signed int sx, sy;

        prepared_pose[i] = display_pose;
        fd = frame_for_pose(i, display_pose);
        ax = rd16(fd->axis);
        ay = rd16(fd->axis + 2);
        stream_request(i, wanted_pose);
        /* O pool de P2 pode ter outra ordem de deduplicacao por ACT. Escolher
         * o META/METAL da mesma paleta do blob evita cruzar indices. Arrays
         * ausentes em headers historicos caem no par legado; o gate de escala
         * continua bloqueando essa variante sem prova. */
        if (i) {
            if (p->facing)
                meta = fd->metal_p2 ? fd->metal_p2 : fd->metal;
            else
                meta = fd->meta_p2 ? fd->meta_p2 : fd->meta;
        } else {
            meta = p->facing ? fd->metal : fd->meta;
        }
        meta_rebase(meta, stream_disp_base(i), meta_ram[i]);
        sx = p->facing
            ? FIGHTER_MIRRORED_ORIGIN_X((signed int)(p->x >> 8), ax, fd->width)
            : (signed int)(p->x >> 8) + ax;
        sy = FLOOR_PX + ay - (signed int)(p->y >> 8);
        SMS_addMetaSprite((unsigned char)sx, (unsigned char)sy, meta_ram[i]);
    }
}

/* Call immediately after SMS_copySpritestoSAT: `prepared_pose` is exactly
 * the tile metadata and buffer base written to the VDP's sprite table. */
void fight_sat_copied(void) {
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
