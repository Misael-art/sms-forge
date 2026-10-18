#include "fight.h"
#include "fight_gfx.h"
#include "PSGlib.h"
#include "music_battle.h"
#include "sfx_hit.h"
#include "sfx_shot.h"
#include "sfx_hurt.h"
#include "sfx_down.h"

Fighter P[2];
unsigned char g_gs;
unsigned int g_frame;
unsigned char g_timer;
unsigned char g_tics;
unsigned char g_hitstop;
unsigned char g_attract;
unsigned char g_banner;
unsigned char g_banner_id;
unsigned char g_shake;

/* Probe SMRT — definidos em src/main.c (mapa 0xC7E0..0xC7FC). Escritas
 * ADITIVAS de instrumentacao: medir a janela REAL do soco na RAM (collide()
 * exige gap in (-4,24); separate() com PUSH_W=20 para os corpos em 20/21)
 * antes de qualquer remedio. volatile e obrigatorio (L009): sem ele o SDCC
 * apaga a escrita e o diagnostico se inverte. */
extern volatile unsigned char probe_timer;    /* P[0].timer            */
extern volatile unsigned char probe_atkwin;   /* startup+active do P1  */
extern volatile unsigned char probe_gap;      /* P[1].x - P[0].x       */
extern volatile unsigned char probe_hitstop;  /* g_hitstop             */
extern volatile unsigned char probe_hitused;  /* P[0].hit_used         */

/* Paleta do cais — espelha PAL em tools/author_stage_ken.py.
 * Os indices 0, 1, 13 e 14 sao TRAVADOS: HUD preto, fonte branca e as duas
 * cores das barras de vida (src/hud.c) dependem deles. */
static const unsigned char pal_bg[16] = {
    0x00, /*  0 preto (HUD)        */ 0x3F, /*  1 branco (fonte, casco) */
    0x39, /*  2 ceu                */ 0x3E, /*  3 nuvem                 */
    0x35, /*  4 ceu alto           */ 0x28, /*  5 mar medio             */
    0x20, /*  6 mar fundo          */ 0x2D, /*  7 mar claro             */
    0x1B, /*  8 madeira media      */ 0x06, /*  9 madeira escura        */
    0x2F, /* 10 madeira clara      */ 0x07, /* 11 laranja (friso/barril)*/
    0x2A, /* 12 cinza (cabine)     */ 0x03, /* 13 vermelho — travado    */
    0x0F, /* 14 amarelo — travado  */ 0x15  /* 15 contorno              */
};
/* Mesma paleta com cada canal pela metade, MENOS o indice 1: o branco fica
 * inteiro para o texto do titulo nao afundar junto com a cena. */
static const unsigned char pal_bg_title[16] = {
    0x00, 0x3F, 0x14, 0x15, 0x10, 0x14, 0x10, 0x14,
    0x05, 0x01, 0x15, 0x01, 0x15, 0x01, 0x05, 0x00
};

static const unsigned char pal_spr[16] = {
    0x00, 0x00, 0x3F, 0x1B, 0x06, 0x1F, 0x0A, 0x07,
    0x02, 0x08, 0x04, 0x1A, 0x34, 0x0F, 0x03, 0x15
};

/* Bit-reverse por byte: um tile 4bpp planar espelhado na horizontal e o
 * mesmo tile com cada byte invertido (verificado 32/32 contra as antigas
 * folhas _l). 256 B de tabela pagaram 9.7 KB de folhas duplicadas. */
static const unsigned char bitrev[256] = {
    0x00,0x80,0x40,0xC0,0x20,0xA0,0x60,0xE0,0x10,0x90,0x50,0xD0,0x30,0xB0,0x70,0xF0,
    0x08,0x88,0x48,0xC8,0x28,0xA8,0x68,0xE8,0x18,0x98,0x58,0xD8,0x38,0xB8,0x78,0xF8,
    0x04,0x84,0x44,0xC4,0x24,0xA4,0x64,0xE4,0x14,0x94,0x54,0xD4,0x34,0xB4,0x74,0xF4,
    0x0C,0x8C,0x4C,0xCC,0x2C,0xAC,0x6C,0xEC,0x1C,0x9C,0x5C,0xDC,0x3C,0xBC,0x7C,0xFC,
    0x02,0x82,0x42,0xC2,0x22,0xA2,0x62,0xE2,0x12,0x92,0x52,0xD2,0x32,0xB2,0x72,0xF2,
    0x0A,0x8A,0x4A,0xCA,0x2A,0xAA,0x6A,0xEA,0x1A,0x9A,0x5A,0xDA,0x3A,0xBA,0x7A,0xFA,
    0x06,0x86,0x46,0xC6,0x26,0xA6,0x66,0xE6,0x16,0x96,0x56,0xD6,0x36,0xB6,0x76,0xF6,
    0x0E,0x8E,0x4E,0xCE,0x2E,0xAE,0x6E,0xEE,0x1E,0x9E,0x5E,0xDE,0x3E,0xBE,0x7E,0xFE,
    0x01,0x81,0x41,0xC1,0x21,0xA1,0x61,0xE1,0x11,0x91,0x51,0xD1,0x31,0xB1,0x71,0xF1,
    0x09,0x89,0x49,0xC9,0x29,0xA9,0x69,0xE9,0x19,0x99,0x59,0xD9,0x39,0xB9,0x79,0xF9,
    0x05,0x85,0x45,0xC5,0x25,0xA5,0x65,0xE5,0x15,0x95,0x55,0xD5,0x35,0xB5,0x75,0xF5,
    0x0D,0x8D,0x4D,0xCD,0x2D,0xAD,0x6D,0xED,0x1D,0x9D,0x5D,0xDD,0x3D,0xBD,0x7D,0xFD,
    0x03,0x83,0x43,0xC3,0x23,0xA3,0x63,0xE3,0x13,0x93,0x53,0xD3,0x33,0xB3,0x73,0xF3,
    0x0B,0x8B,0x4B,0xCB,0x2B,0xAB,0x6B,0xEB,0x1B,0x9B,0x5B,0xDB,0x3B,0xBB,0x7B,0xFB,
    0x07,0x87,0x47,0xC7,0x27,0xA7,0x67,0xE7,0x17,0x97,0x57,0xD7,0x37,0xB7,0x77,0xF7,
    0x0F,0x8F,0x4F,0xCF,0x2F,0xAF,0x6F,0xEF,0x1F,0x9F,0x5F,0xDF,0x3F,0xBF,0x7F,0xFF
};

static unsigned char g_live;

/* --- streaming de pose, com banco duplo ------------------------------- */
/* Um lutador por frame, 96 B (3 tiles). Nao e chute: com 256 B o jogo caia
 * de 60 para 40 fps (o espelhamento em runtime custa CPU que o baseline, que
 * lia folhas ja espelhadas da ROM, nao gastava). Medido no gate de probe:
 *   32B->59.5   64B->58.3   96B->57.5   128B->55.5   256B->40 fps
 * 96 B segura ~57.5 fps estavel e poe a maior pose (896 B) na tela em ~9
 * frames. Mexer aqui SEM remedir o fps e como andar no escuro. */
#define STREAM_BYTES 96

static unsigned char st_buf[2][STREAM_BYTES]; /* preparado FORA do VBlank */
static unsigned int st_len[2];                /* bytes prontos para a VRAM */
static unsigned int st_dst[2];                /* tile destino do chunk */
static const unsigned char *st_src[2];
static unsigned int st_sz[2], st_off[2];
static unsigned char st_flip[2], st_pose[2], st_bank[2], st_on[2];
static unsigned char st_turn;   /* de quem e a vez de usar o VBlank */

static unsigned char cur_bank[2];   /* banco EXIBIDO (base de tiles) */
static unsigned char cur_pose[2], cur_flip[2];

static signed char meta_ram[2][64];
static unsigned char meta_dirty[2];

/* Cada SFX no canal para o qual FOI AUTORADO.
 *
 * make_psg_assets.py gera sfx_shot para SFX_CHANNEL2 e sfx_hit para
 * SFX_CHANNELS2AND3, mas os dois estavam sendo tocados em SFX_CHANNEL3: o
 * fluxo PSGlib nao batia com os canais que recebia. sfx_hurt e sfx_down JA
 * eram de canal 3 e estavam sem uso em inc/. Medido com capture_audio de
 * 11 s: sem SFX = 91% ativo, com os SFX no canal errado = 86% (e o cooldown
 * nao mudava nada — 14, 30 e 60 davam os mesmos 86%, porque o problema nunca
 * foi a frequencia, era o canal).
 *
 * O cooldown fica so pelo ouvido: impede metralhadora de retrigger num
 * flurry. Nao e o que sustenta o gate. */
#define SFX_COOLDOWN 20
static unsigned char sfx_cd;

static void psg_sfx(const unsigned char *sfx, unsigned char ch) {
    if (sfx_cd)
        return;
    PSGSFXPlay((void *)sfx, ch);
    sfx_cd = SFX_COOLDOWN;
}

/* Fireball: sfx_shot, canal 2 (o canal do proprio asset). */
static void psg_beep(void) {
    psg_sfx(sfx_shot, SFX_CHANNEL2);
}

/* Impacto: sfx_hurt ("hero recebe dano"), canal 3. Semantica e canal certos. */
static void psg_hit(void) {
    psg_sfx(sfx_hurt, SFX_CHANNEL3);
}

/* KO: sfx_down ("boss derrotado"), canal 3. Estava sem uso na ROM. */
static void psg_ko(void) {
    sfx_cd = 0;                 /* o KO nunca e engolido pelo cooldown */
    psg_sfx(sfx_down, SFX_CHANNEL3);
}

static const unsigned char *pose_tiles(unsigned char who, unsigned char pose) {
    if (who == 0) {
        switch (pose) {
        case POSE_WALK:    return ken_walk_tiles;
        case POSE_PUNCH:   return ken_punch_tiles;
        case POSE_SPECIAL: return ken_special_tiles;
        case POSE_HIT:     return ken_hit_tiles;
        case POSE_KO:      return ken_ko_tiles;
        case POSE_CROUCH:  return ken_crouch_tiles;
        case POSE_JUMP:    return ken_jump_tiles;
        default:           return ken_idle_tiles;
        }
    }
    switch (pose) {
    case POSE_WALK:    return guile_walk_tiles;
    case POSE_PUNCH:   return guile_punch_tiles;
    case POSE_SPECIAL: return guile_special_tiles;
    case POSE_HIT:     return guile_hit_tiles;
    case POSE_KO:      return guile_ko_tiles;
    case POSE_CROUCH:  return guile_crouch_tiles;
    case POSE_JUMP:    return guile_jump_tiles;
    default:           return guile_idle_tiles;
    }
}

static unsigned int pose_size(unsigned char who, unsigned char pose) {
    if (who == 0) {
        switch (pose) {
        case POSE_WALK:    return KEN_WALK_TILES_SIZE;
        case POSE_PUNCH:   return KEN_PUNCH_TILES_SIZE;
        case POSE_SPECIAL: return KEN_SPECIAL_TILES_SIZE;
        case POSE_HIT:     return KEN_HIT_TILES_SIZE;
        case POSE_KO:      return KEN_KO_TILES_SIZE;
        case POSE_CROUCH:  return KEN_CROUCH_TILES_SIZE;
        case POSE_JUMP:    return KEN_JUMP_TILES_SIZE;
        default:           return KEN_IDLE_TILES_SIZE;
        }
    }
    switch (pose) {
    case POSE_WALK:    return GUILE_WALK_TILES_SIZE;
    case POSE_PUNCH:   return GUILE_PUNCH_TILES_SIZE;
    case POSE_SPECIAL: return GUILE_SPECIAL_TILES_SIZE;
    case POSE_HIT:     return GUILE_HIT_TILES_SIZE;
    case POSE_KO:      return GUILE_KO_TILES_SIZE;
    case POSE_CROUCH:  return GUILE_CROUCH_TILES_SIZE;
    case POSE_JUMP:    return GUILE_JUMP_TILES_SIZE;
    default:           return GUILE_IDLE_TILES_SIZE;
    }
}

static const signed char *pose_meta(unsigned char who, unsigned char pose) {
    if (who == 0) {
        switch (pose) {
        case POSE_WALK:    return ken_walk_meta;
        case POSE_PUNCH:   return ken_punch_meta;
        case POSE_SPECIAL: return ken_special_meta;
        case POSE_HIT:     return ken_hit_meta;
        case POSE_KO:      return ken_ko_meta;
        case POSE_CROUCH:  return ken_crouch_meta;
        case POSE_JUMP:    return ken_jump_meta;
        default:           return ken_idle_meta;
        }
    }
    switch (pose) {
    case POSE_WALK:    return guile_walk_meta;
    case POSE_PUNCH:   return guile_punch_meta;
    case POSE_SPECIAL: return guile_special_meta;
    case POSE_HIT:     return guile_hit_meta;
    case POSE_KO:      return guile_ko_meta;
    case POSE_CROUCH:  return guile_crouch_meta;
    case POSE_JUMP:    return guile_jump_meta;
    default:           return guile_idle_meta;
    }
}

static unsigned char bank_a(unsigned char who) {
    return (unsigned char)(who ? TILE_P2A : TILE_P1A);
}

static unsigned char bank_b(unsigned char who) {
    return (unsigned char)(who ? TILE_P2B : TILE_P1B);
}

/* Copia n bytes para o buffer de RAM, espelhando se preciso. Roda FORA do
 * VBlank de proposito: 256 bitrevs nao cabem na janela junto do loadTiles. */
/* Ponteiros static, nao locais: o SDCC-Z80 mantem locais no quadro de pilha
 * e os recarrega a cada acesso via IX, o que colocava o laco perto de 100
 * ciclos por byte e derrubava o jogo de 60 para 36 fps. */
static unsigned char *sc_dst;
static const unsigned char *sc_src;
static unsigned char sc_blocks;

static void stage_chunk(unsigned char who, const unsigned char *src,
                        unsigned int n, unsigned char flip) {
    sc_dst = st_buf[who];
    sc_src = src;
    sc_blocks = (unsigned char)(n >> 3);   /* n e sempre multiplo de 32 */
    if (flip) {
        while (sc_blocks--) {
            sc_dst[0] = bitrev[sc_src[0]]; sc_dst[1] = bitrev[sc_src[1]];
            sc_dst[2] = bitrev[sc_src[2]]; sc_dst[3] = bitrev[sc_src[3]];
            sc_dst[4] = bitrev[sc_src[4]]; sc_dst[5] = bitrev[sc_src[5]];
            sc_dst[6] = bitrev[sc_src[6]]; sc_dst[7] = bitrev[sc_src[7]];
            sc_dst += 8; sc_src += 8;
        }
    } else {
        while (sc_blocks--) {
            sc_dst[0] = sc_src[0]; sc_dst[1] = sc_src[1];
            sc_dst[2] = sc_src[2]; sc_dst[3] = sc_src[3];
            sc_dst[4] = sc_src[4]; sc_dst[5] = sc_src[5];
            sc_dst[6] = sc_src[6]; sc_dst[7] = sc_src[7];
            sc_dst += 8; sc_src += 8;
        }
    }
}

/* Publica a pose no banco ocioso. Enquanto o upload nao termina, o banco
 * exibido continua intacto — nada de sprite meio velho / meio novo. */
static void request_pose(unsigned char who, unsigned char pose,
                         unsigned char flip) {
    unsigned char target;
    if (st_on[who] && st_pose[who] == pose && st_flip[who] == flip)
        return;
    if (!st_on[who] && cur_pose[who] == pose && cur_flip[who] == flip)
        return;
    target = (unsigned char)(cur_bank[who] == bank_a(who) ? bank_b(who)
                                                          : bank_a(who));
    st_src[who] = pose_tiles(who, pose);
    st_sz[who] = pose_size(who, pose);
    st_off[who] = 0;
    st_flip[who] = flip;
    st_pose[who] = pose;
    st_bank[who] = target;
    st_len[who] = 0;
    st_on[who] = 1;
    st_turn = who;   /* quem acabou de mudar de pose fura a fila */
}

void fight_prepare_stream(void) {
    unsigned char who = st_turn;
    unsigned int n;
    if (!st_on[who]) {
        who = (unsigned char)(1 - who);
        if (!st_on[who])
            return;
        st_turn = who;
    }
    if (st_len[who])
        return;
    n = st_sz[who] - st_off[who];
    if (n > STREAM_BYTES)
        n = STREAM_BYTES;
    stage_chunk(who, st_src[who] + st_off[who], n, st_flip[who]);
    st_dst[who] = (unsigned int)st_bank[who] + (st_off[who] >> 5);
    st_len[who] = n;
}

void fight_stream(void) {
    unsigned char who;
    PSGFrame();
    PSGSFXFrame();
    if (sfx_cd) sfx_cd--;
    for (who = 0; who < 2; who++) {
        if (!st_len[who])
            continue;
        SMS_loadTiles(st_buf[who], st_dst[who], st_len[who]);
        st_off[who] += st_len[who];
        st_len[who] = 0;
        if (st_off[who] >= st_sz[who]) {
            /* pose completa: so agora o banco exibido troca */
            cur_bank[who] = st_bank[who];
            cur_pose[who] = st_pose[who];
            cur_flip[who] = st_flip[who];
            meta_dirty[who] = 1;
            st_on[who] = 0;
            st_turn = (unsigned char)(1 - who);   /* passa a vez */
        }
    }
}

/* --- parallax por raster ----------------------------------------------
 * Uma camada de BG so, cortada em bandas pela interrupcao de linha:
 *   linhas   0.. 15  HUD           — H-scroll TRAVADO no VDP (R0 bit 6),
 *                                    entao o placar nao anda com o ceu
 *   linhas  16.. 63  ceu/nuvens    — scroll lento
 *   linhas  64..111  horizonte     — parado: o iate esta ATRACADO, se
 *                                    deslizasse junto com o mar denunciaria
 *                                    que ceu e mar sao a mesma camada
 *   linhas 112..127  mar perto     — scroll mais rapido (profundidade)
 *   linhas 128..191  deck          — parado, e onde os lutadores pisam
 * O valor do ceu e escrito no VBlank; as tres trocas seguintes saem do
 * handler. Custo medido: ~1% do frame. */
static unsigned char scr_sky, scr_near, scr_tick, rast_i;

void stage_raster(void) {
    if (rast_i == 0) {
        INLINE_SMS_setBGScrollX(0);          /* linha 64: horizonte parado */
        SMS_setLineCounter(47);              /* +48 -> quebra em 111 */
    } else if (rast_i == 1) {
        INLINE_SMS_setBGScrollX(scr_near);   /* linha 112: mar perto */
        SMS_setLineCounter(15);              /* +16 -> quebra em 127 */
    } else {
        INLINE_SMS_setBGScrollX(0);          /* linha 128: deck parado */
        SMS_setLineCounter(255);             /* nao dispara mais neste frame */
    }
    rast_i++;
}

/* Chamado no VBlank: arma a banda do ceu e rearma o contador de linha. */
void stage_scroll_frame(void) {
    scr_tick++;
    /* Na abertura o ceu fica parado: o titulo mora nas linhas 4 e 6, que sao
     * banda de ceu — com a nuvem rolando, o texto rolava junto. O mar perto
     * continua andando, entao a tela nao fica morta. */
    if (g_gs != GS_TITLE && (scr_tick & 7) == 0)
        scr_sky--;                           /* nuvens: 1 px a cada 8 frames */
    if ((scr_tick & 1) == 0) scr_near--;     /* mar perto: 1 px a cada 2 */
    rast_i = 0;
    SMS_setBGScrollX(scr_sky);
    /* 63, nao 47. O contador de linha dispara na linha N depois de recarregar
     * no VBlank; com 47 a primeira quebra caia na linha ~48 e TODAS as bandas
     * subiam 16 linhas — o mar perto comecava na 96 em vez da 112. So ficou
     * visivel quando o titulo pos texto na linha 12 (96..103) e ele saiu
     * rolando e enrolando junto com a agua. */
    SMS_setLineCounter(63);                  /* quebra em ~63 -> vale da 64 */
}

void fight_go_live(void) {
    g_live = 1;
}

/* Antes de go_live nao ha orcamento de VBlank a respeitar: carrega inteiro. */
static void load_pose_now(unsigned char who, unsigned char pose,
                          unsigned char flip) {
    const unsigned char *src = pose_tiles(who, pose);
    unsigned int sz = pose_size(who, pose);
    unsigned int off = 0, n;
    unsigned char base = bank_a(who);
    while (off < sz) {
        n = sz - off;
        if (n > STREAM_BYTES)
            n = STREAM_BYTES;
        stage_chunk(who, src + off, n, flip);
        SMS_loadTiles(st_buf[who], (unsigned int)base + (off >> 5), n);
        off += n;
    }
    cur_bank[who] = base;
    cur_pose[who] = pose;
    cur_flip[who] = flip;
    meta_dirty[who] = 1;
    st_on[who] = 0;
    st_len[who] = 0;
}

/* As folhas olham para a ESQUERDA; quem olha para a direita e espelhado. */
static unsigned char want_flip(unsigned char who) {
    return P[who].facing ? 1 : 0;
}

static void apply_pose(unsigned char who) {
    if (g_live)
        request_pose(who, P[who].pose, want_flip(who));
    else
        load_pose_now(who, P[who].pose, want_flip(who));
}

/* --- FSM -------------------------------------------------------------- */

static void set_state(unsigned char who, unsigned int st) {
    unsigned char pose = POSE_IDLE;
    if (P[who].state == st && st != ST_HIT)
        return;
    P[who].state = st;
    P[who].timer = 0;
    P[who].startup = 0;
    P[who].active = 0;
    P[who].recovery = 0;
    P[who].hit_used = 0;
    switch (st) {
    case ST_WALK_F:
    case ST_WALK_B: pose = POSE_WALK; break;
    case ST_JUMP:   pose = POSE_JUMP; break;
    case ST_PUNCH:
        pose = POSE_PUNCH;
        P[who].startup = 4; P[who].active = 4; P[who].recovery = 8;
        break;
    case ST_KICK:
        /* Chute e mais lento e mais punivel que o soco: os dois botoes
         * precisam ter contas diferentes, senao B2 e so um B1 repintado. */
        pose = POSE_PUNCH;
        P[who].startup = 7; P[who].active = 5; P[who].recovery = 13;
        break;
    case ST_SPECIAL:
        pose = POSE_SPECIAL;
        P[who].startup = 8; P[who].active = 4; P[who].recovery = 12;
        break;
    case ST_HIT: pose = POSE_HIT; P[who].recovery = 12; break;
    case ST_KO:  pose = POSE_KO; P[who].recovery = 60; break;
    case ST_WIN: pose = POSE_SPECIAL; P[who].recovery = 90; break;
    case ST_CROUCH: pose = POSE_CROUCH; break;
    case ST_GUARD: pose = POSE_CROUCH; break;
    default: pose = POSE_IDLE; break;
    }
    P[who].pose = pose;
    apply_pose(who);
}

static void reset_positions(void) {
    P[0].x = 40; P[0].y = GROUND_Y; P[0].vy = 0; P[0].facing = 1;
    P[1].x = 176; P[1].y = GROUND_Y; P[1].vy = 0; P[1].facing = 0;
    P[0].fireball_on = 0; P[1].fireball_on = 0;
    P[0].state = P[1].state = 0;
    set_state(0, ST_IDLE);
    set_state(1, ST_IDLE);
}

static unsigned int t_wait;      /* contador de espera de tela (titulo/result) */

/* Redesenha o palco inteiro. Na troca de tela isto substitui os text_clear
 * linha a linha: limpar por linha deixava restos do titulo por cima da luta
 * ("UPER" sobrevivendo na linha 4) e cada resto era um bug novo para cacar.
 * Com o display desligado o custo nao aparece. */
static void stage_map_draw(void) {
    unsigned char r, c;
    for (r = 0; r < 24; r++)
        for (c = 0; c < 32; c++)
            SMS_setTileatXY(c, r,
                            (unsigned int)TILE_STAGE + stage_ken_map[r][c]);
}

static void banner(unsigned char id, unsigned char frames);
static void reset_positions(void);

/* Troca de tela mexe em ~160 tiles de name table de uma vez, e roda dentro do
 * fight_update, que e FORA do VBlank: no display ativo parte das escritas se
 * perde — foi assim que sobrou um "UPER" do titulo por cima da luta. Com o
 * display desligado a escrita e livre; custa um frame preto, que numa
 * transicao de tela e o que se espera mesmo. */
static void title_enter(void) {
    SMS_displayOff();
    g_gs = GS_TITLE;
    t_wait = 0;
    g_attract = 1;
    P[0].hp = HP_MAX; P[1].hp = HP_MAX;
    P[0].rounds = 0; P[1].rounds = 0;
    g_timer = 99; g_tics = 0; g_hitstop = 0; g_shake = 0;
    g_banner = 0; g_banner_id = BN_NONE;
    scr_sky = 0;                 /* zera antes de congelar, senao o ceu salta */
    reset_positions();
    SMS_loadBGPalette(pal_bg_title);
    stage_map_draw();
    title_draw();
    SMS_displayOn();
}

/* demo=1 entra em modo de atracao (a ROM joga sozinha); demo=0 e o jogador. */
static void title_exit(unsigned char demo) {
    SMS_displayOff();
    SMS_loadBGPalette(pal_bg);
    stage_map_draw();
    hud_reset();
    hud_static();
    g_attract = demo;
    P[0].hp = HP_MAX; P[1].hp = HP_MAX;
    P[0].rounds = 0; P[1].rounds = 0;
    reset_positions();
    g_gs = GS_ROUND; g_timer = 99; g_tics = 0;
    banner(BN_ROUND1, 90);
    SMS_displayOn();
}

static void banner(unsigned char id, unsigned char frames) {
    g_banner_id = id;
    g_banner = frames;
}

void fight_init(void) {
    unsigned int i;
    SMS_loadBGPalette(pal_bg);
    SMS_loadSpritePalette(pal_spr);
    SMS_loadTiles(stage_ken_tiles, TILE_STAGE, STAGE_KEN_TILES_SIZE);
    text_init();

    /* Projeteis: quatro tiles cada, nas duas direcoes, carregados de uma vez.
     * Espelhar projetil em runtime nao vale um caminho de stream proprio. */
    SMS_loadTiles(hadouken_tiles, TILE_FB1L, HADOUKEN_TILES_SIZE);
    SMS_loadTiles(sonicboom_tiles, TILE_FB2L, SONICBOOM_TILES_SIZE);
    for (i = 0; i < HADOUKEN_TILES_SIZE; i++)
        st_buf[0][i] = bitrev[hadouken_tiles[i]];
    SMS_loadTiles(st_buf[0], TILE_FB1, HADOUKEN_TILES_SIZE);
    for (i = 0; i < SONICBOOM_TILES_SIZE; i++)
        st_buf[0][i] = bitrev[sonicboom_tiles[i]];
    SMS_loadTiles(st_buf[0], TILE_FB2, SONICBOOM_TILES_SIZE);

    /* O mapa guarda indices relativos (byte); o banco 256+ entra aqui. */
    stage_map_draw();

    P[0].hp = HP_MAX; P[1].hp = HP_MAX;
    P[0].rounds = 0; P[1].rounds = 0;
    P[0].hist_i = 0; P[1].hist_i = 0;
    g_gs = GS_ROUND; g_timer = 99; g_tics = 0; g_hitstop = 0;
    g_shake = 0;
    g_attract = 1;
    g_live = 0;
    cur_bank[0] = bank_b(0); cur_bank[1] = bank_b(1);
    cur_pose[0] = cur_pose[1] = 0xFF;
    st_on[0] = st_on[1] = 0;
    st_len[0] = st_len[1] = 0;
    reset_positions();
    PSGPlay((void *)music_battle);
    /* A ROM nasce na abertura, nao no meio de um round. */
    title_enter();
}

static void push_hist(unsigned char who, unsigned char dir) {
    P[who].hist[P[who].hist_i & 7] = dir;
    P[who].hist_i++;
}

/* Baixo, DEPOIS frente, dentro das 8 ultimas amostras.
 * O laco antigo ia do mais recente ao mais antigo e marcava saw_d no
 * caminho, entao o que ele reconhecia era frente->baixo (o movimento ao
 * contrario) — e, pior, um unico quadro na diagonal baixo-frente satisfazia
 * as duas condicoes de uma vez. Especial saia de graca ao andar agachado. */
static unsigned char qcf(unsigned char who) {
    unsigned char i, d, saw_d = 0;
    unsigned char fwd = P[who].facing ? 2 : 1; /* 1=L 2=R 4=D */
    for (i = 8; i > 0; i--) {                  /* do mais antigo ao mais recente */
        d = P[who].hist[(unsigned char)(P[who].hist_i - i) & 7];
        if (!saw_d) {
            if (d & 4) saw_d = 1;
        } else if (d & fwd) {
            return 1;
        }
    }
    return 0;
}

static unsigned char busy(unsigned char who) {
    unsigned int s = P[who].state;
    return (unsigned char)(s == ST_PUNCH || s == ST_KICK || s == ST_SPECIAL
                           || s == ST_HIT || s == ST_KO || s == ST_WIN);
}

/* Estar no ar e uma questao de ALTURA, nao de estado: quem leva golpe no
 * pulo sai de ST_JUMP mas continua no ar, e empurrao/facing/guarda precisam
 * saber disso. */
static unsigned char airborne(unsigned char who) {
    return (unsigned char)(P[who].y < GROUND_Y);
}

/* Gravidade vale em QUALQUER estado. Antes ela morava dentro do ramo de
 * ST_JUMP do control(): levar golpe no ar tirava o lutador desse estado, a
 * queda parava e ele ficava PENDURADO — e de la andava, agachava e socava.
 * O probe flagrou IDLE/WALK/CROUCH a y=93 com o chao em 112. */
static void set_state(unsigned char who, unsigned int st);

static void apply_gravity(unsigned char who) {
    if (P[who].y >= GROUND_Y && P[who].vy == 0)
        return;
    P[who].y += P[who].vy;
    P[who].vy++;
    if (P[who].y >= GROUND_Y) {
        P[who].y = GROUND_Y;
        P[who].vy = 0;
        if (P[who].state == ST_JUMP)
            set_state(who, ST_IDLE);
    }
}

/* Topo da hurtbox relativo a y. Agachado encolhe: soco alto passa por cima. */
static unsigned char hurt_top(unsigned char who) {
    return (unsigned char)(P[who].state == ST_CROUCH ? 34 : 12);
}

static void start_fireball(unsigned char who) {
    P[who].fireball_on = 1;
    P[who].fy = P[who].y + 24;
    if (P[who].facing) {
        P[who].fx = P[who].x + FIGHTER_W;
        P[who].fvx = 3;
    } else {
        P[who].fx = P[who].x - 8;
        P[who].fvx = -3;
    }
    psg_beep();
}

static void end_round(unsigned char loser) {
    psg_ko();
    set_state(loser, ST_KO);
    set_state((unsigned char)(1 - loser), ST_WIN);
    g_gs = GS_KO;
    banner(BN_KO, 120);
}

static void apply_hit(unsigned char att, unsigned char def, unsigned char dmg) {
    /* Guarda vale se o defensor segura TRAS e o golpe vem da frente. Antes
     * bastava estar num estado ST_GUARD qualquer, entao dava para bloquear
     * um golpe pelas costas. */
    unsigned char from_front = (unsigned char)
        ((P[def].facing && P[att].x > P[def].x) ||
         (!P[def].facing && P[att].x < P[def].x));
    if (P[def].guard && from_front && !airborne(def)) {
        if (P[def].hp > 2) P[def].hp -= 2;
        else P[def].hp = 1;               /* chip nunca mata */
        g_hitstop = 3;
        P[def].x += P[def].facing ? -2 : 2;
        /* Sem SFX no bloqueio: o hitstop e o recuo ja dao o retorno, e cada
         * disparo a mais rouba o canal 3 da musica. */
        return;
    }
    if (P[def].hp > dmg) P[def].hp -= dmg;
    else P[def].hp = 0;
    g_hitstop = 6;
    g_shake = 6;
    psg_hit();
    if (P[def].hp == 0) {
        end_round(def);
    } else {
        set_state(def, ST_HIT);
        P[def].x += P[def].facing ? -4 : 4;
    }
}

static void collide(void) {
    unsigned char a, b;
    signed int ax, ay0, ay1, bx, by0, by1;
    /* Probe atkwin (aditivo): collide JA paga o teste de estado por lutador,
     * entao a janela ativa do P1 sai daqui por ~14 bytes em vez de ~30 no
     * fight_update. Zerado no topo: quem nao esta em PUNCH/KICK deixa 0. */
    probe_atkwin = 0;
    for (a = 0; a < 2; a++) {
        b = (unsigned char)(1 - a);
        if (P[a].state != ST_PUNCH && P[a].state != ST_KICK) continue;
        if (!a)
            probe_atkwin = (unsigned char)(P[0].startup + P[0].active);
        if (P[a].hit_used) continue;
        if (P[a].timer < P[a].startup) continue;
        if (P[a].timer >= (unsigned char)(P[a].startup + P[a].active)) continue;
        /* Soco = alto, chute = baixo. Da sentido a agachar e a escolher botao. */
        if (P[a].state == ST_PUNCH) {
            ay0 = P[a].y + 18; ay1 = P[a].y + 32;
        } else {
            ay0 = P[a].y + 40; ay1 = P[a].y + 58;
        }
        ax = P[a].facing ? (P[a].x + 20) : (P[a].x - 4);
        bx = P[b].x + 8;
        by0 = P[b].y + hurt_top(b);
        by1 = P[b].y + 60;
        if (ax < bx + 16 && ax + 12 > bx && ay0 < by1 && ay1 > by0) {
            P[a].hit_used = 1;   /* um golpe, um acerto */
            apply_hit(a, b, (unsigned char)(P[a].state == ST_KICK ? 10 : 7));
        }
    }
    for (a = 0; a < 2; a++) {
        b = (unsigned char)(1 - a);
        if (!P[a].fireball_on) continue;
        bx = P[b].x + 8;
        by0 = P[b].y + hurt_top(b);
        by1 = P[b].y + 60;
        if (P[a].fx < bx + 16 && P[a].fx + 16 > bx &&
            P[a].fy < by1 && P[a].fy + 16 > by0) {
            P[a].fireball_on = 0;
            apply_hit(a, b, 12);
        }
    }
}

/* Corpos deixam de se atravessar: quem anda empurra, ninguem ocupa o mesmo
 * pixel. Sem isso os dois lutadores viravam um borrao no centro do palco. */
static void separate(void) {
    signed int d = P[1].x - P[0].x;
    signed int push;
    /* Probe (aditivo): o gap COM SINAL e exatamente este d ANTES do modulo
     * abaixo. Escrito aqui porque o subtrator 16-bit ja e pago pelo jogo —
     * duplica-lo no fight_update custava ~10 bytes de um teto de ~44. */
    probe_gap = (unsigned char)d;
    /* No ar nao ha empurrao: pular POR CIMA do oponente e movimento basico do
     * genero, e a caixa de corpo bloqueava isso mesmo com o lutador a meia
     * altura. Era tambem o que impedia os lados de trocarem — sem troca de
     * lado, o conserto do espelhamento em update_facing nunca era exercido. */
    if (airborne(0) || airborne(1))
        return;
    if (d < 0) d = -d;
    if (d >= PUSH_W) return;
    push = (PUSH_W - d + 1) >> 1;
    if (P[0].x <= P[1].x) {
        P[0].x -= push; P[1].x += push;
    } else {
        P[0].x += push; P[1].x -= push;
    }
    if (P[0].x < STAGE_X_MIN) P[0].x = STAGE_X_MIN;
    if (P[1].x < STAGE_X_MIN) P[1].x = STAGE_X_MIN;
    if (P[0].x > STAGE_X_MAX) P[0].x = STAGE_X_MAX;
    if (P[1].x > STAGE_X_MAX) P[1].x = STAGE_X_MAX;
}

/* Roteiro de atracao. Antes isso vivia solto dentro de control(), amarrado a
 * g_frame: quem pegasse o controle disputava o cabo de guerra com o script e
 * levava um Hadouken sozinho a cada frame depois do 900. Agora e um modo, e
 * o primeiro toque no controle o desliga para sempre. */
static void attract_script(unsigned char *left, unsigned char *right,
                           unsigned char *b1, unsigned char *b2,
                           unsigned char *down, unsigned char *up) {
    unsigned int t;
    if (g_frame < 50) { *right = 1; return; }
    if (g_frame >= 900) {
        /* Fase de desfecho: QCF+soco em ciclo ate o KO — mesma cadencia do
         * roteiro antigo, para a janela de evidencia do KO nao mudar. */
        t = g_frame % 40;
        if (t == 0 || t == 1) *down = 1;
        else if (t == 2) { *down = 1; *right = 1; }
        else if (t == 3) *right = 1;
        else if (t == 4) { *right = 1; *b1 = 1; }
        return;
    }
    /* Vitrine: anda, recua (guarda), soca, PULA, chuta, AGACHA.
     * Pulo e agachar entraram aqui porque sao poses proprias agora — e
     * porque, com o canal de teclado morto neste ambiente, a atracao e o
     * unico jeito de ver (e fotografar) esses estados rodando. */
    t = g_frame % 200;
    if (t < 24) *right = 1;
    else if (t < 48) *left = 1;          /* recua = guarda */
    else if (t == 60) *b1 = 1;
    /* Fecha a distancia ANTES de pular. Sem isto o pulo saia com ~68 px de
     * separacao (medido no probe) e +40 px de deslocamento aereo nao
     * ultrapassavam ninguem — o facing nunca trocava e o reespelhamento
     * ficava sem ser exercido. */
    else if (t >= 64 && t < 98) *right = 1;
    else if (t == 100) *up = 1;          /* pulo: ~20 frames no ar */
    /* Pulo PARA A FRENTE: passa por cima e troca os lados. */
    else if (t > 100 && t < 126) *right = 1;   /* segura ate o pouso */
    else if (t == 135) *b2 = 1;
    else if (t >= 150 && t < 175) *down = 1;
}

static void control(unsigned char who, unsigned int keys, unsigned char cpu) {
    unsigned char left  = (unsigned char)(keys & (who ? PORT_B_KEY_LEFT  : PORT_A_KEY_LEFT));
    unsigned char right = (unsigned char)(keys & (who ? PORT_B_KEY_RIGHT : PORT_A_KEY_RIGHT));
    unsigned char down  = (unsigned char)(keys & (who ? PORT_B_KEY_DOWN  : PORT_A_KEY_DOWN));
    unsigned char up    = (unsigned char)(keys & (who ? PORT_B_KEY_UP    : PORT_A_KEY_UP));
    unsigned char b1    = (unsigned char)(keys & (who ? PORT_B_KEY_1     : PORT_A_KEY_1));
    unsigned char b2    = (unsigned char)(keys & (who ? PORT_B_KEY_2     : PORT_A_KEY_2));
    unsigned char dir = 0, back, fwd;
    signed int dist;

    if (who == 0 && g_attract)
        attract_script(&left, &right, &b1, &b2, &down, &up);

    if (cpu && !(left | right | down | up | b1 | b2)) {
        dist = P[1].x - P[0].x;
        if (dist < 0) dist = -dist;
        if (dist < 44) {
            if ((g_frame & 63) == 0) b1 = 1;
            else if ((g_frame & 63) == 32) b2 = 1;
            /* Guarda quando o oponente ataca — mas so em metade das
             * janelas. Bloqueio perfeito somado ao chip que nunca mata
             * (apply_hit) deixava o dummy literalmente impossivel de vencer
             * no soco e no chute. */
            else if ((P[0].state == ST_PUNCH || P[0].state == ST_KICK)
                     && (g_frame & 8))
                right = 1;
        } else if ((g_frame & 7) < 5) {
            left = 1;
        }
    }

    if (left) dir |= 1;
    if (right) dir |= 2;
    if (down) dir |= 4;
    push_hist(who, dir);

    back = P[who].facing ? left : right;
    fwd  = P[who].facing ? right : left;
    /* Segurar tras defende — inclusive andando para tras, como no arcade. */
    P[who].guard = (unsigned char)(back && !busy(who) && !airborne(who));

    /* So o pulo de verdade dirige no ar; a queda e integrada por
     * apply_gravity, fora daqui. */
    if (P[who].state == ST_JUMP) {
        if (left && P[who].x > STAGE_X_MIN) P[who].x -= 2;
        if (right && P[who].x < STAGE_X_MAX) P[who].x += 2;
        return;
    }

    if (busy(who)) {
        P[who].timer++;
        if (P[who].state == ST_SPECIAL && P[who].timer == P[who].startup
            && !P[who].fireball_on)
            start_fireball(who);
        if (P[who].timer >= (unsigned char)(P[who].startup + P[who].active + P[who].recovery)
            && P[who].state != ST_KO && P[who].state != ST_WIN)
            set_state(who, ST_IDLE);
        return;
    }

    if (b1 && qcf(who)) { set_state(who, ST_SPECIAL); return; }
    if (up) { set_state(who, ST_JUMP); P[who].vy = -10; return; }
    if (b1) { set_state(who, ST_PUNCH); return; }
    if (b2) { set_state(who, ST_KICK); return; }
    if (down) { set_state(who, back ? ST_GUARD : ST_CROUCH); return; }
    if (back) {
        if (P[who].facing) { if (P[who].x > STAGE_X_MIN) P[who].x -= 2; }
        else               { if (P[who].x < STAGE_X_MAX) P[who].x += 2; }
        set_state(who, ST_WALK_B);
        return;
    }
    if (fwd) {
        if (P[who].facing) { if (P[who].x < STAGE_X_MAX) P[who].x += 2; }
        else               { if (P[who].x > STAGE_X_MIN) P[who].x -= 2; }
        set_state(who, ST_WALK_F);
        return;
    }
    set_state(who, ST_IDLE);
}

/* Facing so vira com o lutador livre: virar no meio de um soco trocava a
 * folha de tiles no ar e fazia o sprite piscar espelhado. */
static void update_facing(void) {
    unsigned char who, f;
    for (who = 0; who < 2; who++) {
        if (busy(who) || airborne(who))
            continue;
        f = (unsigned char)(P[who].x < P[1 - who].x ? 1 : 0);
        if (f == P[who].facing)
            continue;
        P[who].facing = f;
        /* Re-espelhar AQUI e o que faltava. A pose so era (re)carregada por
         * set_state, que retorna cedo quando o estado nao muda: quem estava
         * parado e era ultrapassado continuava com a folha do lado antigo, ou
         * seja, de costas para o oponente, ate trocar de estado por acaso. */
        apply_pose(who);
    }
}

static void next_round(void) {
    unsigned char win0 = (unsigned char)(P[1].hp == 0 && P[0].hp > 0);
    unsigned char win1 = (unsigned char)(P[0].hp == 0 && P[1].hp > 0);
    if (win0) P[0].rounds++;
    else if (win1) P[1].rounds++;
    else { P[0].rounds++; P[1].rounds++; }   /* duplo KO / tempo empatado */

    if (P[0].rounds >= 2 || P[1].rounds >= 2) {
        g_gs = GS_RESULT;
        t_wait = 0;
        banner(P[0].rounds > P[1].rounds ? BN_P1WINS
               : (P[1].rounds > P[0].rounds ? BN_P2WINS : BN_DRAW), 255);
        return;
    }
    P[0].hp = HP_MAX; P[1].hp = HP_MAX;
    reset_positions();
    g_gs = GS_ROUND; g_timer = 99; g_tics = 0;
    banner((unsigned char)(BN_ROUND1 + P[0].rounds + P[1].rounds), 90);
}

#define TITLE_DEMO_WAIT 540   /* ~9 s parado -> a ROM se demonstra sozinha */
#define RESULT_WAIT     420   /* ~7 s no resultado -> volta para a abertura */

void fight_update(unsigned int keys) {
    unsigned char i;

    if (g_gs == GS_TITLE) {
        t_wait++;
        /* Pisca o convite; o texto so e reescrito quando muda de fase. */
        if ((t_wait & 31) == 0)
            title_press((unsigned char)((t_wait >> 5) & 1));
        if (keys & (PORT_A_KEY_1 | PORT_A_KEY_2 | PORT_B_KEY_1 | PORT_B_KEY_2))
            title_exit(0);          /* alguem apertou: partida de verdade */
        else if (t_wait > TITLE_DEMO_WAIT)
            title_exit(1);          /* ninguem apertou: modo de atracao */
        return;
    }

    /* Qualquer toque no controle mata o modo de atracao — para sempre. */
    if (g_attract && (keys & (PORT_A_KEY_UP | PORT_A_KEY_DOWN | PORT_A_KEY_LEFT
                              | PORT_A_KEY_RIGHT | PORT_A_KEY_1 | PORT_A_KEY_2)))
        g_attract = 0;

    if (g_banner) g_banner--;
    if (g_shake) g_shake--;

    if (g_gs == GS_ROUND) {
        if (g_banner == 0) {
            g_gs = GS_FIGHT;
            banner(BN_FIGHT, 40);
            psg_beep();
        }
        return;
    }
    if (g_gs == GS_KO) {
        if (P[0].timer > 50 || P[1].timer > 50) next_round();
        else { P[0].timer++; P[1].timer++; }
        return;
    }
    if (g_gs == GS_RESULT) {
        /* Botao 1 recomeca ja; senao a tela devolve para a abertura sozinha.
         * Antes o resultado era um beco sem saida que so o reset tirava. */
        t_wait++;
        if (keys & (PORT_A_KEY_1 | PORT_B_KEY_1))
            title_exit(0);
        else if (t_wait > RESULT_WAIT)
            title_enter();
        return;
    }
    /* Instrumentacao do soco (aditiva, nenhuma logica muda): o estado da
     * colisao tem de ficar visivel TAMBEM quando o hitstop congela o update
     * abaixo — o early-return comeria a escrita e o probe mostraria um
     * hitstop que nunca existiu. Por isso a escrita vem ANTES do return.
     * Forma compacta de proposito: a ROM tem ~44 bytes de teto antes do
     * banco estourar no makesms (reserva 0x7F80..0x7FFF do header). */
    probe_hitstop = g_hitstop;
    probe_timer = P[0].timer;
    probe_hitused = P[0].hit_used;
    /* probe_atkwin mora em collide() (ver la, ~14 B em vez de ~30 aqui) e
     * probe_gap mora em separate() (o subtrator 16-bit ja e pago pelo jogo).
     * O gap e a janela ficam congelados durante o hitstop — o valor verdade,
     * nada se mexe; hitstop/timer/hitused sao reescritos todo frame aqui,
     * ANTES do early-return, para nunca ficarem invisiveis. */
    if (g_hitstop) { g_hitstop--; return; }

    g_tics++;
    if (g_tics >= 60 && g_timer) { g_tics = 0; g_timer--; }
    if (g_timer == 0) {
        banner(BN_TIMEUP, 120);
        if (P[0].hp > P[1].hp)      { P[1].hp = 0; end_round(1); }
        else if (P[1].hp > P[0].hp) { P[0].hp = 0; end_round(0); }
        else { P[0].hp = 0; P[1].hp = 0; set_state(0, ST_KO);
               set_state(1, ST_KO); g_gs = GS_KO; }
        return;
    }

    control(0, keys, 0);
    control(1, keys, 1);
    apply_gravity(0);
    apply_gravity(1);
    separate();
    update_facing();
    collide();
    for (i = 0; i < 2; i++) {
        if (P[i].fireball_on) {
            P[i].fx += P[i].fvx;
            if (P[i].fx < 0 || P[i].fx > 248) P[i].fireball_on = 0;
        }
    }
}

/* --- desenho ----------------------------------------------------------- */

static void rebuild_meta(unsigned char who) {
    const signed char *m = pose_meta(who, cur_pose[who]);
    unsigned char base = cur_bank[who];
    unsigned char n = 0;
    signed char lo = 127, hi = -128;
    const signed char *p;

    if (cur_flip[who]) {
        for (p = m; p[0] != (signed char)METASPRITE_END; p += 3) {
            if (p[0] < lo) lo = p[0];
            if (p[0] > hi) hi = p[0];
        }
    }
    while (m[0] != (signed char)METASPRITE_END && n < 60) {
        signed char dx = m[0];
        /* Espelho na SAT: a caixa da pose e refletida em torno de si mesma,
         * entao o lutador nao "escorrega" ao virar de lado. */
        meta_ram[who][n++] = cur_flip[who] ? (signed char)(lo + hi - dx) : dx;
        meta_ram[who][n++] = m[1];
        meta_ram[who][n++] = (signed char)(base + (unsigned char)m[2]);
        m += 3;
    }
    meta_ram[who][n] = (signed char)METASPRITE_END;
    meta_dirty[who] = 0;
}

static void draw_fb(unsigned char on, signed int fx, signed int fy,
                    const signed char *m, unsigned char base,
                    unsigned char flip) {
    signed char fb[16];
    unsigned char n = 0;
    signed char lo = 127, hi = -128;
    const signed char *p;
    if (!on) return;
    if (flip) {
        for (p = m; p[0] != (signed char)METASPRITE_END; p += 3) {
            if (p[0] < lo) lo = p[0];
            if (p[0] > hi) hi = p[0];
        }
    }
    while (m[0] != (signed char)METASPRITE_END && n < 12) {
        fb[n++] = flip ? (signed char)(lo + hi - m[0]) : m[0];
        fb[n++] = m[1];
        fb[n++] = (signed char)(base + (unsigned char)m[2]);
        m += 3;
    }
    fb[n] = (signed char)METASPRITE_END;
    SMS_addMetaSprite((unsigned char)fx, (unsigned char)fy, fb);
}

void fight_draw(void) {
    unsigned char who;
    signed int y;
    SMS_initSprites();
    /* Projeteis PRIMEIRO na SAT: 4+4+2 sprites na scanline do torso; os
     * 8 primeiros sobrevivem. Lutador de tras perde coluna, Hadouken nao. */
    draw_fb(P[0].fireball_on, P[0].fx, P[0].fy, hadouken_meta,
            (unsigned char)(P[0].fvx > 0 ? TILE_FB1 : TILE_FB1L),
            (unsigned char)(P[0].fvx > 0));
    draw_fb(P[1].fireball_on, P[1].fx, P[1].fy, sonicboom_meta,
            (unsigned char)(P[1].fvx > 0 ? TILE_FB2 : TILE_FB2L),
            (unsigned char)(P[1].fvx > 0));
    for (who = 0; who < 2; who++) {
        if (meta_dirty[who])
            rebuild_meta(who);
        y = P[who].y;
        /* Tremor do impacto e balanco de respiracao: a pose e uma so, entao a
         * vida vem do deslocamento. Sem isso o idle e uma estatua. */
        if (g_shake)
            y += (g_shake & 1) ? 2 : -2;
        else if (cur_pose[who] == POSE_IDLE && !airborne(who))
            y += (signed int)((g_frame >> 4) & 1);
        else if (cur_pose[who] == POSE_WALK && !airborne(who))
            y -= (signed int)((g_frame >> 2) & 1);
        SMS_addMetaSprite((unsigned char)P[who].x, (unsigned char)y,
                          meta_ram[who]);
    }
    SMS_copySpritestoSAT();
}
