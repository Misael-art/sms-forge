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
#include "input.h"
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

typedef struct { const unsigned char *pattern; unsigned char command; } CommandDef;

enum { ST_IDLE, ST_WALK_F, ST_WALK_B, ST_JUMP, ST_CROUCH, ST_GUARD,
       ST_PUNCH1, ST_PUNCH2, ST_SPECIAL, ST_KO, ST_KICK1, ST_KICK2,
       ST_N_STATES };

typedef struct {
    const Frame *frames;
    const Anim *anims;
    const StateDef *states;
    const CommandDef *commands;
    unsigned char command_count;
    unsigned char pose_count, pose_base, meta_max_bytes;
    unsigned short max_life;
    signed int jump_vy, gravity;
    unsigned char hitstop, hit_push, guard_push;
} CharacterData;

#include "../out/local_study/generated/versus_cut/fight_runtime_data.h"

Fighter fighters[2];
volatile unsigned char dbg_frame;

#define FIGHT_META_MAX_BYTES \
    ((P1_CUT_META_MAX_BYTES > P2_CUT_META_MAX_BYTES) ? \
     P1_CUT_META_MAX_BYTES : P2_CUT_META_MAX_BYTES)
/* Capacidade compilada do maior metasprite realmente emitido por cada slot. */
static signed char meta_ram[2][FIGHT_META_MAX_BYTES];
static unsigned char prepared_pose[2], visible_pose[2];
static unsigned char prepared_facing[2], visible_facing[2];
/* Metadados gerados são constantes no segmento fixo. Rebase só quando a
 * pose/facing ou o buffer de VRAM muda. */
static const unsigned char *meta_cached_source[2];
static const unsigned char *meta_cached_map[2];
/* A SAT em RAM sobrevive a SMS_copySpritestoSAT. Só é reconstruída quando
 * pose/base/facing/posição ou metadata mudam; pedidos ao streamer continuam
 * sendo enviados em cada tick. */
static unsigned char render_cached_pose[2];
static unsigned char render_cached_facing[2];
static unsigned char render_cached_x[2], render_cached_y[2];
static unsigned char sat_dirty;

/* ---- utilitarios ---- */

/* precedente MSSF2T fight.c:rebuild_meta — o terminador 0x80 so casa lido
 * ASSINADO (unsigned 128 != (signed)-128 promote a int). */
unsigned char meta_rebase(const unsigned char *meta,
                          const unsigned char *slot_map,
                          signed char *dst, unsigned char capacity,
                          unsigned char pair_count) {
    unsigned char n = 0;
    unsigned char tile_id, local_pair, physical_pair;
    if (!meta || !slot_map || !dst || !capacity) return 0;
    while ((signed char)meta[n] != (signed char)METASPRITE_END) {
        if ((unsigned int)n + 3u >= capacity) {
            dst[0] = (signed char)METASPRITE_END;
            return 0;
        }
        tile_id = meta[n + 2];
        if (tile_id & 1u) {
            dst[0] = (signed char)METASPRITE_END;
            return 0;
        }
        local_pair = tile_id >> 1;
        if (local_pair >= pair_count) {
            dst[0] = (signed char)METASPRITE_END;
            return 0;
        }
        physical_pair = slot_map[local_pair];
        dst[n] = (signed char)meta[n];
        dst[n + 1] = (signed char)meta[n + 1];
        dst[n + 2] = (signed char)(physical_pair << 1);
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
static void box_rect(const Fighter *p, unsigned char facing,
                     const Box *b, Rect *r) {
    signed int xp = (signed int)(p->x >> 8);
    signed int alt = (signed int)(p->y >> 8);
    if (!facing) { r->l = xp + b->x1; r->r = xp + b->x2; }
    else         { r->l = xp - b->x2; r->r = xp - b->x1; }
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
                                   unsigned char attacker_facing,
                                   unsigned char defender_facing,
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
        box_rect(attacker, attacker_facing, &hb, &hr);
        while (rd16(hurt) != CLSN_END) {
            Box ob;
            Rect or;
            clsn_read_box(hurt, &ob);
            box_rect(defender, defender_facing, &ob, &or);
            if (hr.l < or.r && or.l < hr.r && hr.t < or.b && or.t < hr.b)
                return 1;
            hurt += 8;
        }
        hit += 8;
    }
    return 0;
}

/* Union horizontal do CLSN2 da pose que esta na SAT. O dado de frame usado
 * na colisao de golpes tambem define o pushbox; nao ha largura inventada. */
static unsigned char hurt_bounds_visible(const Fighter *p, unsigned char slot,
                                         signed int *left, signed int *right) {
    const unsigned char *box = hurt_clsn_visible(p, slot);
    unsigned char found = 0;
    if (!box || !left || !right) return 0;
    while (rd16(box) != CLSN_END) box += 8;
    box += 2;
    while (rd16(box) != CLSN_END) {
        Box b;
        Rect r;
        clsn_read_box(box, &b);
        box_rect(p, visible_facing[slot], &b, &r);
        if (!found || r.l < *left) *left = r.l;
        if (!found || r.r > *right) *right = r.r;
        found = 1;
        box += 8;
    }
    return found;
}

static void separate_ground_overlap(Fighter *p, unsigned char pslot,
                                    Fighter *o, unsigned char oslot) {
    signed int pl = 0, pr = 0, ol = 0, oright = 0;
    signed int overlap;
    unsigned int distance, available;
    unsigned char move_left;
    if (p->y || o->y) return;
    if (!hurt_bounds_visible(p, pslot, &pl, &pr) ||
        !hurt_bounds_visible(o, oslot, &ol, &oright)) return;
    if (pl >= oright || ol >= pr) return;
    overlap = (pr < oright ? pr : oright) - (pl > ol ? pl : ol);
    if (overlap <= 0) return;
    move_left = (unsigned char)((p->x < o->x) ||
                                ((p->x == o->x) && !pslot));
    distance = (unsigned int)overlap << 8;
    if (move_left) {
        if (p->x <= X_MIN) return;
        available = p->x - X_MIN;
        if (distance > available) distance = available;
        p->x -= distance;
    } else {
        if (p->x >= X_MAX) return;
        available = X_MAX - p->x;
        if (distance > available) distance = available;
        p->x += distance;
    }
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
    stream_init(versus_poses, VERSUS_POSE_COUNT);
}

unsigned char fight_decode_command(unsigned char slot) {
    const CharacterData *cd;
    unsigned char i;
    if (slot >= 2u) return FIGHT_CMD_NONE;
    cd = &characters[slot];
    for (i = 0; i < cd->command_count; i++)
        if (input_pattern_hit(slot, cd->commands[i].pattern))
            return cd->commands[i].command;
    return FIGHT_CMD_NONE;
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
    meta_cached_source[slot] = 0;
    enter_state(p, slot, ST_IDLE);
    /* carga bloqueante do idle: no boot nao pode existir frame com pose
     * exibida sem tiles (audit_deterministic_boot fotografa o frame 0). */
    stream_load_now(slot, (unsigned char)(cd->pose_base +
                        cd->anims[cd->states[ST_IDLE].anim].frames[0].pose),
                    p->facing);
    prepared_pose[slot] = visible_pose[slot] = stream_disp(slot);
    prepared_facing[slot] = visible_facing[slot] = stream_disp_facing(slot);
}

void fight_set_ko(Fighter *p) {
    unsigned char slot = (p == &fighters[0]) ? 0 : 1;
    p->vx = 0;
    p->vy = 0;
    p->hitstop = 0;
    enter_state(p, slot, ST_KO);
}

unsigned char fight_step(Fighter *p, unsigned int keys, unsigned int opp_keys,
                         unsigned char command) {
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
        /* auto-facing de solo. Golpes chegam como eventos de comando depois
         * do tier e do CMD v2; bits crus de KEY_1/KEY_2 nunca iniciam estado. */
        p->facing = (o->x > p->x) ? 0 : 1;
        pressed = keys & ~p->keys_prev;
        if (p->facing) { fwdk = K_LEFT;  backk = K_RIGHT; }
        else           { fwdk = K_RIGHT; backk = K_LEFT;  }
        ns = p->state;
        if (command == FIGHT_CMD_LP)     ns = ST_PUNCH1;
        else if (command == FIGHT_CMD_HP) ns = ST_PUNCH2;
        else if (command == FIGHT_CMD_LK) ns = ST_KICK1;
        else if (command == FIGHT_CMD_HK) ns = ST_KICK2;
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
            if (ns == ST_PUNCH1 || ns == ST_PUNCH2)
                event = FIGHT_EVENT_PUNCH;
            else if (ns == ST_KICK1 || ns == ST_KICK2)
                event = FIGHT_EVENT_KICK;
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
            visible_facing[pslot] == p->facing &&
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
        if (boxes_overlap(p, o, visible_facing[pslot], visible_facing[oslot],
                          attack_frame->clsn,
                          hurt_clsn_visible(o, oslot))) {
            unsigned char push = cd->hit_push;
            p->hit_done = 1;
            /* Guarda bloqueia apenas de frente e no chão. */
            if ((characters[oslot].states[o->state].flags & S_BLOCKABLE) &&
                o->y == 0 &&
                visible_facing[oslot] != visible_facing[pslot]) {
                push = cd->guard_push;
            } else {
                if (o->life >= sd->dmg) o->life -= sd->dmg;
                else o->life = 0;
            }
            o->hitstop = cd->hitstop;
            p->hitstop = cd->hitstop;
            o->x = (unsigned int)((signed int)o->x +
                                  (visible_facing[pslot] ? -(signed int)push * 256
                                             : (signed int)push * 256));
            clamp_x(o);
        }
    }
    return event;
}

static unsigned char fight_render_changed(unsigned char slot) {
    Fighter *p = &fighters[slot];
    const CharacterData *cd = &characters[slot];
    const Frame *flog = cur_frame(p, slot);
    unsigned char display_pose = stream_disp(slot);
    unsigned char display_facing = stream_disp_facing(slot);
    unsigned char wanted_pose = (unsigned char)(cd->pose_base + flog->pose);
    stream_request(slot, wanted_pose, p->facing,
                   (unsigned char)((cd->states[p->state].flags & S_HIT) != 0));
    return !meta_cached_source[slot] ||
           render_cached_pose[slot] != display_pose ||
           render_cached_facing[slot] != display_facing ||
           render_cached_x[slot] != (unsigned char)(p->x >> 8) ||
           render_cached_y[slot] != (unsigned char)(p->y >> 8);
}

static void fight_render_slot(unsigned char slot) {
    Fighter *p = &fighters[slot];
    const CharacterData *cd = &characters[slot];
    unsigned char display_pose = stream_disp(slot);
    unsigned char display_facing = stream_disp_facing(slot);
    const Frame *fd = frame_for_pose(slot, display_pose);
    const unsigned char *meta;
    const unsigned char *slot_map = stream_disp_map(slot);
    unsigned char pair_count = stream_disp_pair_count(slot);
    signed int ax, ay, sx, sy;

    /* O pool de P2 pode ter outra ordem por ACT: metadata deve continuar
     * ligada ao mesmo blob de paleta. */
    if (slot) {
        if (display_facing)
            meta = fd->metal_p2 ? fd->metal_p2 : fd->metal;
        else
            meta = fd->meta_p2 ? fd->meta_p2 : fd->meta;
    } else {
        meta = display_facing ? fd->metal : fd->meta;
    }
    ax = rd16(fd->axis);
    ay = rd16(fd->axis + 2);
    sx = display_facing
        ? FIGHTER_MIRRORED_ORIGIN_X((signed int)(p->x >> 8), ax, fd->width)
        : (signed int)(p->x >> 8) + ax;
    sy = FLOOR_PX + ay - (signed int)(p->y >> 8);

    prepared_pose[slot] = display_pose;
    prepared_facing[slot] = display_facing;
    if (!meta) {
        meta_cached_source[slot] = 0;
        return;
    }
    if (meta_cached_source[slot] != meta || meta_cached_map[slot] != slot_map) {
        if (!meta_rebase(meta, slot_map, meta_ram[slot],
                         cd->meta_max_bytes, pair_count)) {
            meta_cached_source[slot] = 0;
            return;
        }
        meta_cached_source[slot] = meta;
        meta_cached_map[slot] = slot_map;
    }
    SMS_addMetaSprite((unsigned char)sx, (unsigned char)sy, meta_ram[slot]);
    render_cached_pose[slot] = display_pose;
    render_cached_facing[slot] = display_facing;
    render_cached_x[slot] = (unsigned char)(p->x >> 8);
    render_cached_y[slot] = (unsigned char)(p->y >> 8);
}

void fight_draw(void) {
    unsigned char redraw = fight_render_changed(0);
    if (fight_render_changed(1)) redraw = 1;
    if (!redraw) return;

    /* CLSN2 impede atravessamento em solo; no ar os lutadores ainda podem
     * cruzar. As caixas so precisam ser relidas quando a pose/facing/posicao
     * visivel vai reconstruir a SAT, nao em cada frame parado. */
    separate_ground_overlap(&fighters[0], 0, &fighters[1], 1);

    /* SpriteNextFree zera só o contador da lista software; a SAT anterior
     * continua válida quando a pose e as origens não mudam. */
    SMS_initSprites();
    fight_render_slot(0);
    fight_render_slot(1);
    sat_dirty = 1;
}

unsigned char fight_sat_needs_copy(void) {
    return sat_dirty;
}

/* Call immediately after SMS_copySpritestoSAT: `prepared_pose` is exactly
 * the tile metadata and buffer base written to the VDP's sprite table. */
void fight_sat_copied(void) {
    visible_pose[0] = prepared_pose[0];
    visible_pose[1] = prepared_pose[1];
    visible_facing[0] = prepared_facing[0];
    visible_facing[1] = prepared_facing[1];
    sat_dirty = 0;
}

unsigned char fight_visible_pose(unsigned char slot) {
    if (slot >= 2u) return 0xFF;
    return visible_pose[slot];
}

unsigned char fight_target_pose(unsigned char slot) {
    Fighter *p;
    if (slot >= 2u) return 0xFF;
    p = &fighters[slot];
    return (unsigned char)(characters[slot].pose_base +
                           cur_frame(p, slot)->pose);
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
