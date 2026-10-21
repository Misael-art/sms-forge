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
 *  - Input: o UNICO caminho de golpe e o anel de `input.c` lendo o blob `_CMD_`
 *    versionado (doc/22: forca = tempo de pressao, dois tiers por tecla). Nivel
 *    de botao nao gera golpe; por isso o tier forte e um padrao separado, e nao
 *    um "multiplicador" do fraco. Alias sem pose no corte congela em
 *    NO_ADV_STATE (falha fechado), nunca recebe dano inventado.
 *  - Corpo: dois atores na linha de piso nao se atravessam (body.c); o
 *    auto-facing so vira com x diferente, o empate do L098 nao vira mais.
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
#include "body.h"
#include "input_tier.h"
#include "cpu_controller.h"
#include "scene_trimmed.h"
#include "source_frame_data.h"
#include "attack_cmds.h"
#include "trace_hooks.h"

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

enum { AT_LP, AT_HP, AT_LK, AT_HK, AT_N };

enum { ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD,
       ST_PUNCH, ST_HP, ST_SPECIAL, ST_KO, ST_KICK, ST_HK,
       ST_PUNCH_CLOSE, ST_HP_CLOSE, ST_KICK_CLOSE, ST_HK_CLOSE,
       ST_PUNCH_FAR, ST_HP_FAR, ST_KICK_FAR, ST_HK_FAR,
       ST_N_STATES };

typedef struct {
    const Anim *anims;
    const StateDef *states;
    unsigned char pose_count, pose_base, frame_data_bank;
    unsigned int frame_data_off;
    unsigned char pose_index_bank, pose_meta_bank;
    unsigned int pose_index_off;
    unsigned short max_life;
    signed int jump_vy, gravity;
    unsigned char hitstop, hit_push, guard_push;
    const unsigned short *close_distances_q8;
    const unsigned short *far_distances_q8;
    unsigned short ground_front_q8;
} CharacterData;

#include "fight_runtime_data.h"

#define FRAME_DATA_RECORD_BYTES 11u
static unsigned char frame_cache_index[2];
static unsigned char frame_cache_valid[2];
/* Keep the variable-sized frame/CLSN caches out of SDCC's ordinary DATA
 * segment, which ends beside fixed runtime probes. Frame caches occupy
 * C810..C91B; the 4-record pose cache starts at aligned C920. The live VDP
 * staging buffers begin at D000. check_ram_layout.py verifies the ranges. */
volatile unsigned char __at(0xC810) frame_cache_storage[2u * FRAME_CACHE_STRIDE];
volatile unsigned char __at(0xC920) pose_runtime_cache[4u * POSE_CACHE_RECORD_BYTES];
typedef char frame_cache_layout_must_match[
    sizeof(Frame) == FRAME_CACHE_FRAME_BYTES ? 1 : -1];
#define FRAME_CACHE_FOR(slot) \
    ((volatile Frame *)(frame_cache_storage + \
      (unsigned int)(slot) * FRAME_CACHE_STRIDE))
#define FRAME_CLSN_FOR(slot) \
    (frame_cache_storage + (unsigned int)(slot) * FRAME_CACHE_STRIDE + \
     FRAME_CACHE_FRAME_BYTES)

Fighter fighters[2];
volatile unsigned char dbg_frame;

static unsigned char prepared_pose[2], visible_pose[2];

/* Os quatro padroes do mapa de controle (doc/22), por ator, lidos do `.cmd`
 * real pelo gerador `mugen2sms/generators/cmd_patterns.py`: `P0_*` = jogador 1
 * (porta A), `P1_*` = jogador 2 (porta B). Os nomes sao por SLOT, entao trocar
 * de elenco nao muda uma linha deste arquivo. */

/* Estado que cada padrao monta. NO_ADV_STATE e a sentinela fail-closed para
 * qualquer alias sem papel mapeado no corte; sem pose nao há dano inventado. */
#define NO_ADV_STATE  0xFFu
static const unsigned char attack_states[2][AT_N] = {
    { ST_PUNCH, ST_HP, ST_KICK, ST_HK },
    { ST_PUNCH, ST_HP, ST_KICK, ST_HK },
};
static const unsigned char close_attack_states[2][AT_N] = {
    { ST_PUNCH_CLOSE, ST_HP_CLOSE, ST_KICK_CLOSE, ST_HK_CLOSE },
    { ST_PUNCH_CLOSE, ST_HP_CLOSE, ST_KICK_CLOSE, ST_HK_CLOSE },
};
static const unsigned char far_attack_states[2][AT_N] = {
    { ST_PUNCH_FAR, ST_HP_FAR, ST_KICK_FAR, ST_HK_FAR },
    { ST_PUNCH_FAR, ST_HP_FAR, ST_KICK_FAR, ST_HK_FAR },
};

static unsigned char standing_attack_allowed(unsigned char state,
                                             unsigned int keys) {
    return (unsigned char)(!(keys & K_DOWN) &&
        (state == ST_IDLE || state == ST_WALK_F || state == ST_WALK_B));
}

static unsigned char body_half_w[2];
/* O corte vigente tem CPU só no P2; não duplique roteiro/estado para P1. */
static CpuController cpu_controller;
static CpuMove cpu_moves[AT_N];
static unsigned char cpu_move_count;
static const unsigned char cpu_light_1[2] = { CPU_INPUT_KEY_1, 0u };
static const unsigned char cpu_light_2[2] = { CPU_INPUT_KEY_2, 0u };
static unsigned char cpu_strong_1[INPUT_TIER_T];
static unsigned char cpu_strong_2[INPUT_TIER_T];
static unsigned char cpu_difficulty;
static unsigned int cpu_seed;
static unsigned char cpu_ready;
static unsigned char cpu_interaction[2];
static unsigned char cpu_attack_active[2];
static unsigned char cpu_attack_hit[2];

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

static signed int rd16(const volatile unsigned char *b) {
    return (signed int)((unsigned int)b[0] | ((unsigned int)b[1] << 8));
}

#define CLSN_END (-32767)

typedef struct { signed int l, t, r, b; } Rect;   /* px de tela */

/* Descriptor layout is generated by source_frame_data.py. A frame and its
 * variable CLSN are copied out of the mapped page before the bank is restored,
 * so callers never retain a pointer into a page that another actor remaps. */
static const volatile Frame *frame_load(unsigned char slot, unsigned char index) {
    const CharacterData *cd = &characters[slot];
    volatile Frame *frame = FRAME_CACHE_FOR(slot);
    const unsigned char *page = (const unsigned char *)0x8000u;
    const unsigned char *record;
    unsigned int off, clsn_off;
    unsigned char clsn_size, i;
    if (index >= cd->pose_count) index = 0;
    if (frame_cache_valid[slot] && frame_cache_index[slot] == index)
        return frame;
    SMS_saveROMBank();
    SMS_mapROMBank(cd->frame_data_bank);
    off = cd->frame_data_off + (unsigned int)index * FRAME_DATA_RECORD_BYTES;
    record = page + off;
    frame->dur = record[0];
    frame->pose = record[1];
    frame->width = record[2];
    frame->height = record[3];
    frame->axis_x = rd16(record + 4);
    frame->axis_y = rd16(record + 6);
    clsn_off = (unsigned int)record[8] | ((unsigned int)record[9] << 8);
    clsn_size = record[10];
    frame->clsn = 0;
    if (clsn_off != 0xFFFFu && clsn_size && clsn_size <= FRAME_CLSN_BUFFER_BYTES) {
        for (i = 0; i < clsn_size; i++)
            FRAME_CLSN_FOR(slot)[i] =
                page[cd->frame_data_off + clsn_off + i];
        frame->clsn = FRAME_CLSN_FOR(slot);
    }
    SMS_restoreROMBank();
    frame_cache_index[slot] = index;
    frame_cache_valid[slot] = 1u;
    return frame;
}

static void clsn_read_box(const volatile unsigned char *b, Box *o) {
    /* Box stores 16-bit little-endian values, but this runtime immediately
     * truncates every coordinate to signed 8-bit. Reading the low byte is
     * exactly that truncation and removes four helper calls from hit checks. */
    o->x1 = (signed char)b[0]; o->y1 = (signed char)b[2];
    o->x2 = (signed char)b[4]; o->y2 = (signed char)b[6];
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

static const volatile Frame *cur_frame(const Fighter *p, unsigned char slot) {
    const Anim *anim = &characters[slot].anims[p->anim];
    return frame_load(slot, (unsigned char)(anim->first_frame + p->frame));
}

static const volatile Frame *frame_for_pose(unsigned char slot, unsigned char pose) {
    const CharacterData *cd = &characters[slot];
    if (pose < cd->pose_base || pose >= cd->pose_base + cd->pose_count)
        return frame_load(slot, 0u);
    return frame_load(slot, (unsigned char)(pose - cd->pose_base));
}

/* Usa a pose já copiada para a SAT; isso mantém hit/hurt sincronizados com
 * o frame que o VDP realmente mostra durante o streaming. */
static const volatile unsigned char *hurt_clsn_visible(const Fighter *p, unsigned char slot) {
    const CharacterData *cd = &characters[slot];
    const volatile Frame *f = frame_for_pose(slot, visible_pose[slot]);
    if (f->clsn) return f->clsn;
    return frame_load(slot, cd->anims[p->anim].first_frame)->clsn;
}

static unsigned char boxes_overlap(const Fighter *attacker, const Fighter *defender,
    const volatile unsigned char *hit_data,
                                   const volatile unsigned char *hurt_data) {
    const volatile unsigned char *hit = hit_data;
    const volatile unsigned char *hurt_start = hurt_data;
    if (!hit || !hurt_start) return 0;
    while (rd16(hurt_start) != CLSN_END) hurt_start += 8;
    hurt_start += 2;                    /* sentinela entre hit e hurt */
    while (rd16(hit) != CLSN_END) {
        Box hb;
        Rect hr;
        const volatile unsigned char *hurt = hurt_start;
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

static void cpu_publish_interaction(unsigned char slot, unsigned char event) {
    /* Contact is more informative than a simultaneous whiff transition. */
    if (event != CPU_INTERACTION_WHIFF ||
        cpu_interaction[slot] == CPU_INTERACTION_NONE)
        cpu_interaction[slot] = event;
}

static void enter_state(Fighter *p, unsigned char slot, unsigned char s) {
    const CharacterData *cd = &characters[slot];
    if (cpu_attack_active[slot]) {
        if (!cpu_attack_hit[slot])
            cpu_publish_interaction(slot, CPU_INTERACTION_WHIFF);
        cpu_attack_active[slot] = 0;
        cpu_attack_hit[slot] = 0;
    }
    if (cd->states[s].flags & S_HIT) {
        cpu_attack_active[slot] = 1;
        cpu_attack_hit[slot] = 0;
    }
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

/* Meia-largura do corpo, MEDIDA da secao hurt da CLSN do idle (o clsn2 do AIR):
 * nenhum numero inventado. Sem caixa hurt o corpo e zero, e playerpush algum
 * acontece — empurrar sem medida e o que o handoff proibe. */
static unsigned char idle_body_half_w(unsigned char slot) {
    const CharacterData *cd = &characters[slot];
    const Anim *idle = &cd->anims[cd->states[ST_IDLE].anim];
    const volatile unsigned char *c = frame_load(slot, idle->first_frame)->clsn;
    signed int lo = 32767, hi = -32768, w;
    if (!c) return 0;
    while (rd16(c) != CLSN_END) c += 8;      /* secao hit */
    c += 2;                                   /* sentinela entre hit e hurt */
    while (rd16(c) != CLSN_END) {
        Box b;
        clsn_read_box(c, &b);
        if ((signed int)b.x1 < lo) lo = b.x1;
        if ((signed int)b.x2 > hi) hi = b.x2;
        c += 8;
    }
    if (hi < lo) return 0;
    w = hi - lo;
    return (unsigned char)((w + 1) >> 1);
}

/* playerpush: os dois corpos na linha de piso nao se atravessam, e cada um
 * para na borda da arena (L098 capturou P1 em x 96->155 por dentro de P2).
 * A separacao e idempotente, entao chamar no passo cheio de cada ator nao
 * reempurra o que o outro ja separou neste frame. */
static void ground_resolve(unsigned char pslot) {
    unsigned char oslot = (unsigned char)(1u - pslot);
    Body a, b;
    a.x = fighters[pslot].x;
    a.y = fighters[pslot].y;
    a.half_w = body_half_w[pslot];
    b.x = fighters[oslot].x;
    b.y = fighters[oslot].y;
    b.half_w = body_half_w[oslot];
    if (!body_separate(&a, &b, X_MIN, X_MAX)) return;
    fighters[pslot].x = a.x;
    fighters[oslot].x = b.x;
}

/* P2BodyDist X is the gap between each actor's front edge. The imported
 * ground.front widths and source threshold are scaled per slot and stored as
 * Q8.8; close attacks keep the source's strict '<' comparison. */
static unsigned int p2_body_distance_q8(unsigned char slot) {
    unsigned char other = (unsigned char)(1u - slot);
    unsigned int gap = fighters[slot].x >= fighters[other].x
        ? fighters[slot].x - fighters[other].x
        : fighters[other].x - fighters[slot].x;
    unsigned int fronts = characters[slot].ground_front_q8 +
                          characters[other].ground_front_q8;
    return gap > fronts ? (unsigned int)(gap - fronts) : 0u;
}

static unsigned char attack_state_for(unsigned char slot, unsigned char alias,
                                      unsigned int keys) {
    const CharacterData *cd = &characters[slot];
    unsigned char base = attack_states[slot][alias];
    unsigned char close = close_attack_states[slot][alias];
    unsigned char far = far_attack_states[slot][alias];
    unsigned int distance;
    /* Imported source distance variants apply only to standing/control input;
     * crouch-specific actions remain outside this cut. */
    if (cd->far_distances_q8[alias] &&
        standing_attack_allowed(fighters[slot].state, keys) &&
        (cd->states[far].flags & S_HIT)) {
        distance = p2_body_distance_q8(slot);
        if (distance >= cd->far_distances_q8[alias]) return far;
    }
    if (cd->close_distances_q8[alias] &&
        standing_attack_allowed(fighters[slot].state, keys) &&
        (cd->states[close].flags & S_HIT)) {
        distance = p2_body_distance_q8(slot);
        if (distance < cd->close_distances_q8[alias]) return close;
    }
    return base;
}

/* Alcance de um alias vem das hitboxes MUGEN já escaladas no AIR/Frame. Isso
 * deixa a policy genérica: ela só vê faixa pública de distância, não nomes de
 * personagem nem dados privados de comando. */
static unsigned char cpu_attack_range(unsigned char slot, unsigned char state,
                                     unsigned char *min_range,
                                     unsigned char *max_range) {
    const CharacterData *cd = &characters[slot];
    const Anim *anim = &cd->anims[cd->states[state].anim];
    unsigned char fi;
    signed int left = 32767, right = -32768;
    unsigned char other = (unsigned char)(1u - slot);

    for (fi = 0; fi < anim->n_frames; fi++) {
        const volatile unsigned char *c = frame_load(
            slot, (unsigned char)(anim->first_frame + fi))->clsn;
        if (!c) continue;
        while (rd16(c) != CLSN_END) {
            Box box;
            clsn_read_box(c, &box);
            if ((signed int)box.x1 < left) left = box.x1;
            if ((signed int)box.x2 > right) right = box.x2;
            c += 8;
        }
    }
    if (right < left) return 0u;

    left -= (signed int)body_half_w[other];
    right += (signed int)body_half_w[other];
    if (left < 0) left = 0;
    if (right > 255) right = 255;
    if (left > right) return 0u;
    *min_range = (unsigned char)left;
    *max_range = (unsigned char)right;
    return 1u;
}

static void cpu_build_moves(void) {
    unsigned char alias;
    const unsigned char slot = 1u;
    cpu_move_count = 0;
    for (alias = 0; alias < AT_N; alias++) {
        unsigned char state = attack_states[1][alias];
        unsigned char close_state = close_attack_states[1][alias];
        CpuMove *move;
        unsigned char key1, strong, lo, hi, close_lo, close_hi;
        if (state == NO_ADV_STATE ||
            !cpu_attack_range(slot, state, &lo, &hi)) continue;
        if ((characters[slot].states[close_state].flags & S_HIT) &&
            cpu_attack_range(slot, close_state, &close_lo, &close_hi)) {
            if (close_lo < lo) lo = close_lo;
            if (close_hi > hi) hi = close_hi;
        }

        key1 = (unsigned char)(alias == AT_LP || alias == AT_HP);
        strong = (unsigned char)(alias == AT_HP || alias == AT_HK);
        move = &cpu_moves[cpu_move_count++];
        move->samples = key1 ? (strong ? cpu_strong_1 : cpu_light_1)
                             : (strong ? cpu_strong_2 : cpu_light_2);
        move->sample_count = strong ? INPUT_TIER_T : 2u;
        move->flags = 0u;
        move->min_range = lo;
        move->max_range = hi;
        move->energy_cost = 0u;
        move->weight = 128u;
        move->cooldown = 2u;
    }
}

static unsigned char cpu_life_band(unsigned short life, unsigned short max_life) {
    unsigned int quarter = (unsigned int)max_life >> 2;
    if (life >= (unsigned int)max_life - quarter) return 3u;
    if (life >= (unsigned int)max_life / 2u) return 2u;
    if (life >= quarter) return 1u;
    return 0u;
}

void fight_cpu_init(unsigned char difficulty, unsigned int seed) {
    unsigned char i;
    if (difficulty > CPU_DIFFICULTY_HARD) difficulty = CPU_DIFFICULTY_NORMAL;
    cpu_difficulty = difficulty;
    cpu_seed = seed ? seed : 0xACE1u;
    for (i = 0; i < INPUT_TIER_T; i++) {
        cpu_strong_1[i] = CPU_INPUT_KEY_1;
        cpu_strong_2[i] = CPU_INPUT_KEY_2;
    }
    cpu_ready = 1u;
}

unsigned char fight_cpu_input(unsigned char slot) {
    CpuObservation observation;
    Fighter *self, *opponent;
    const CharacterData *self_data, *opponent_data;
    unsigned char other;
    if (!cpu_ready || slot != 1u) return 0u;
    self = &fighters[slot];
    other = (unsigned char)(1u - slot);
    opponent = &fighters[other];
    self_data = &characters[slot];
    opponent_data = &characters[other];

    observation.self_x = (unsigned char)(self->x >> 8);
    observation.opponent_x = (unsigned char)(opponent->x >> 8);
    observation.self_facing = self->facing;
    observation.self_alive = self->life != 0u;
    observation.self_can_act = (unsigned char)(!self->hitstop &&
        (self_data->states[self->state].flags & S_CONTROL));
    observation.self_airborne = self->y != 0u;
    observation.self_at_left_edge = self->x <=
        (unsigned int)(X_MIN + ((unsigned int)body_half_w[slot] << 8));
    observation.self_at_right_edge = self->x >=
        (unsigned int)(X_MAX - ((unsigned int)body_half_w[slot] << 8));
    observation.self_energy = 0u; /* energy is not in this fixture's Fighter */
    observation.self_life_band = cpu_life_band(self->life, self_data->max_life);
    observation.opponent_life_band = cpu_life_band(opponent->life,
                                                    opponent_data->max_life);
    observation.opponent_alive = opponent->life != 0u;
    observation.opponent_airborne = opponent->y != 0u;
    observation.opponent_guarding = (unsigned char)(
        opponent->state == ST_GUARD || opponent->state == ST_CROUCH);
    observation.opponent_recovery_ticks = (unsigned char)(
        !opponent->hitstop &&
        !(opponent_data->states[opponent->state].flags & S_CONTROL));
    observation.opponent_attack_visible = (unsigned char)(
        (opponent_data->states[opponent->state].flags & S_HIT) &&
        fight_visible_hitbox(other));
    /* Este fixture só tem guarda baixa (tras+baixo). Até os dados MUGEN
     * declararem altura de ataque, a CPU escolhe essa entrada observável. */
    observation.opponent_attack_height = observation.opponent_attack_visible ?
        CPU_THREAT_LOW : CPU_THREAT_NONE;
    observation.self_last_interaction = cpu_interaction[slot];
    cpu_interaction[slot] = CPU_INTERACTION_NONE;
    return cpu_controller_step(&cpu_controller, &observation,
                               cpu_moves, cpu_move_count);
}

/* ---- API ---- */

void fight_init(void) {
    input_init();
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
    cpu_interaction[slot] = CPU_INTERACTION_NONE;
    cpu_attack_active[slot] = 0;
    cpu_attack_hit[slot] = 0;
    body_half_w[slot] = idle_body_half_w(slot);
    /* Round novo com a mao no botao: o pulso do round anterior mora no anel ate
     * INPUT_BUF ticks e a ROM nao da tick de input fora da luta. */
    input_flush(slot);
    enter_state(p, slot, ST_IDLE);
    /* carga bloqueante do idle: no boot nao pode existir frame com pose
     * exibida sem tiles (audit_deterministic_boot fotografa o frame 0). */
    {
        unsigned char pose = (unsigned char)(cd->pose_base +
            frame_load(slot, cd->anims[cd->states[ST_IDLE].anim].first_frame)->pose);
        stream_load_now(slot, pose, p->facing);
        prepared_pose[slot] = visible_pose[slot] = pose;
    }
    if (slot == 1u && cpu_ready) {
        cpu_build_moves();
        cpu_controller_init(&cpu_controller, cpu_difficulty, cpu_seed);
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
    const volatile Frame *fr = frame_load(
        pslot, (unsigned char)(a->first_frame + p->frame));
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

/* Chao, idle e sem nenhum input no ultimo tick. O passo cheio tem frame de
 * 37 bytes no SDCC e custa ~18 linhas de scanline por lutador; um frame de
 * probe em idle nunca precisa daquele frame. O atalho e por `input_busy`, nao
 * por `keys != 0`: o tier FRACO nasce no tick em que a tecla JA foi solta
 * (doc/22), entao quem define o golpe nao esta em `keys`. */
static unsigned char fight_step_full(Fighter *p, unsigned int keys, unsigned int opp_keys);

unsigned char fight_step(Fighter *p, unsigned int keys, unsigned int opp_keys) {
    unsigned char pslot = (p == &fighters[0]) ? 0 : 1;
    Fighter *o;
    if (!p->hitstop && p->y == 0) {
        o = pslot ? &fighters[0] : &fighters[1];
        /* auto-facing com desempate: no empate do L098 o ator virava de lado e
         * o direcional parecia invertido. Vira so quando x e diferente. */
        p->facing = body_facing(p->x, o->x, p->facing);
    }
    input_tick(pslot, (unsigned char)keys, p->facing);
    if (p->hitstop || p->state != ST_IDLE || p->y != 0 || input_busy(pslot))
        return fight_step_full(p, keys, opp_keys);
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
    unsigned char adv, attack;

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
        pressed = keys & ~p->keys_prev;
        if (p->facing) { fwdk = K_LEFT;  backk = K_RIGHT; }
        else           { fwdk = K_RIGHT; backk = K_LEFT;  }
        ns = p->state;
        attack = 0;
        adv = NO_ADV_STATE;
        /* This cut imports standing attacks only. State -1's ``ctrl`` gate
         * does not make a crouch input a standing punch. */
        if (standing_attack_allowed(p->state, keys) && pslot) {
            if (input_pattern_hit(pslot, P1_CMD_LP)) {
                attack = 1; adv = attack_state_for(pslot, AT_LP, keys);
            }
            if (!attack && input_pattern_hit(pslot, P1_CMD_HP)) {
                attack = 1; adv = attack_state_for(pslot, AT_HP, keys);
            }
            if (!attack && input_pattern_hit(pslot, P1_CMD_LK)) {
                attack = 1; adv = attack_state_for(pslot, AT_LK, keys);
            }
            if (!attack && input_pattern_hit(pslot, P1_CMD_HK)) {
                attack = 1; adv = attack_state_for(pslot, AT_HK, keys);
            }
        } else if (standing_attack_allowed(p->state, keys)) {
            if (input_pattern_hit(pslot, P0_CMD_LP)) {
                attack = 1; adv = attack_state_for(pslot, AT_LP, keys);
            }
            if (!attack && input_pattern_hit(pslot, P0_CMD_HP)) {
                attack = 1; adv = attack_state_for(pslot, AT_HP, keys);
            }
            if (!attack && input_pattern_hit(pslot, P0_CMD_LK)) {
                attack = 1; adv = attack_state_for(pslot, AT_LK, keys);
            }
            if (!attack && input_pattern_hit(pslot, P0_CMD_HK)) {
                attack = 1; adv = attack_state_for(pslot, AT_HK, keys);
            }
        }
        if (attack) {
            if (adv != NO_ADV_STATE) ns = adv;
        } else if (pressed & K_SPECIAL)  ns = ST_SPECIAL;
        else if (pressed & K_UP)         ns = ST_JUMP;
        else if ((keys & K_DOWN) && (keys & backk)) ns = ST_GUARD;
        else if (keys & K_DOWN)          ns = ST_CROUCH;
        else if (keys & fwdk)            ns = ST_WALK_F;
        else if (keys & backk)           ns = ST_WALK_B;
        else                             ns = ST_IDLE;
        p->keys_prev = keys;
        if (ns != p->state) {
            enter_state(p, pslot, ns);
            sd = &cd->states[ns];
            if (ns == ST_PUNCH || ns == ST_HP ||
                ns == ST_PUNCH_CLOSE || ns == ST_HP_CLOSE ||
                ns == ST_PUNCH_FAR || ns == ST_HP_FAR)
                event = FIGHT_EVENT_PUNCH;
            else if (ns == ST_KICK || ns == ST_HK ||
                     ns == ST_KICK_CLOSE || ns == ST_HK_CLOSE)
                event = FIGHT_EVENT_KICK;
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
        const volatile Frame *attack_frame = frame_for_pose(pslot, visible_pose[pslot]);
        if (boxes_overlap(p, o, attack_frame->clsn,
                          hurt_clsn_visible(o, oslot))) {
            unsigned char push = cd->hit_push;
            p->hit_done = 1;
            /* Guarda bloqueia apenas de frente e no chão. */
            if ((characters[oslot].states[o->state].flags & S_BLOCKABLE) &&
                o->y == 0 &&
                o->facing != p->facing) {
                push = cd->guard_push;
                cpu_attack_hit[pslot] = 1;
                cpu_publish_interaction(pslot, CPU_INTERACTION_BLOCK);
            } else {
                if (o->life >= sd->dmg) o->life -= sd->dmg;
                else o->life = 0;
                cpu_attack_hit[pslot] = 1;
                cpu_publish_interaction(pslot, CPU_INTERACTION_HIT);
            }
            o->hitstop = cd->hitstop;
            p->hitstop = cd->hitstop;
            o->x = (unsigned int)((signed int)o->x +
                                  (p->facing ? -(signed int)push * 256
                                             : (signed int)push * 256));
            clamp_x(o);
        }
    }
    /* um passo de resolucao por ator por frame: cobre a caminhada acima e o
     * knockback do golpe, e o mesmo passo visto pelo outro ator ja separado
     * nao mexe em nada. */
    ground_resolve(pslot);
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

/* Row table in the pose's metadata bank: [count, (dy, pieces)...]. Screen row tops as
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
 * in : er_src (pieces dx,dy,tile in the mapped metadata bank), er_map, er_n (>= 1),
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

/* On a display change: pieces of the pruned metasprite (pose metadata bank,
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
    return (unsigned char)(cd->pose_base +
        frame_load(slot, (unsigned char)(a->first_frame + f))->pose);
}

/* Per-fighter render cache: recomputed only when its input changes.
 * The first integrated build redid all of this every frame (~60 lines for
 * the pose lookups/origin and ~40 for the scheduler). */
typedef struct {
    unsigned char anim, frame, facing;           /* logic key */
    unsigned char want_pose, next_pose_c;
    unsigned char pose_data_valid;
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
    /* Each fighter's pose tables live in its own mapped metadata bank. */
    SMS_saveROMBank();
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
            !c->pose_data_valid) {
            const CharacterData *cd = &characters[i];
            c->anim = p->anim;
            c->frame = p->frame;
            c->facing = p->facing;
            c->want_pose = (unsigned char)(cd->pose_base + cur_frame(p, i)->pose);
            c->next_pose_c = next_pose(p, i);
            c->pose_data_valid = 1u;
        }
        tl_np[1] = fight_vcounter;
        /* Prefetch: while the wanted pose is displayed, stream the pose AIR
         * shows next, so it is resident when the logic advances and each pose
         * keeps exactly its AIR duration. Input changes drop it.
        * At most one allocate per iteration. The other fighter keeps the
         * pose already on screen and is first on the next fight_draw. */
        {
            unsigned char req_pose, skip = 0;
            if (stream_shows(i, c->want_pose, p->facing)) {
                req_pose = c->next_pose_c;
            } else {
                req_pose = c->want_pose;
            }
            if (stream_will_allocate(i, req_pose, p->facing)) {
                if (n_alloc) {
                    skip = 1;
                    deferred = i;
                } else {
                    n_alloc = 1;
                }
            }
            if (!skip)
                stream_request(i, req_pose, p->facing);
        }
        tl_np[2] = fight_vcounter;
        {
            const unsigned char *meta, *map, *rowt;
            unsigned char fac;
            SMS_mapROMBank(characters[i].pose_meta_bank);
            display_pose = stream_display(i, c->want_pose, p->facing,
                                          &meta, &map, &fac, &rowt);
            if (display_pose != c->disp_pose || fac != c->disp_facing || meta != c->meta) {
                const volatile Frame *fd = frame_for_pose(i, display_pose);
                c->disp_pose = display_pose;
                c->disp_facing = fac;
                c->meta = meta;
                c->rowt = rowt;
                c->ax = fd->axis_x;
                c->ay = fd->axis_y;
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
            stream_shows(i, c->want_pose, p->facing))
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
    const volatile unsigned char *c = frame_for_pose(slot, visible_pose[slot])->clsn;
    return c && rd16(c) != CLSN_END;
}

/* First pose number of the animation the logic is currently in. */
unsigned char fight_state_pose0(unsigned char slot) {
    const CharacterData *cd = &characters[slot];
    return (unsigned char)(cd->pose_base +
        frame_load(slot, cd->anims[fighters[slot].anim].first_frame)->pose);
}

/* Only the isolated TRC3 clone needs source AIR identity queries. Keeping the
 * functions out of the canonical build preserves its ROM bytes and hot path. */
#ifdef TRACE_AIR_IDENTITY
unsigned short fight_source_action_id(unsigned char slot) {
    if (slot > 1u) return 0xFFFFu;
    return characters[slot].anims[fighters[slot].anim].id;
}

unsigned char fight_source_element_index(unsigned char slot) {
    if (slot > 1u) return 0xFFu;
    return fighters[slot].frame;
}
#endif
