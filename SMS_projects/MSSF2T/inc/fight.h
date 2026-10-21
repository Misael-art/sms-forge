#ifndef FIGHT_H
#define FIGHT_H

#include "SMSlib.h"

/* HAMOOPIG-like numeric FSM (subset). */
#define ST_IDLE     100
#define ST_PUNCH    101
#define ST_KICK     104
#define ST_GUARD    107
#define ST_CROUCH   200
#define ST_JUMP     300
#define ST_WALK_B   410
#define ST_WALK_F   420
#define ST_HIT      501
#define ST_KO       570
#define ST_WIN      611
#define ST_SPECIAL  700

#define GS_TITLE    4   /* tela de abertura; e onde a ROM nasce */
#define GS_ROUND    0
#define GS_FIGHT    1
#define GS_KO       2
#define GS_RESULT   3

/* --- VRAM ---------------------------------------------------------------
 * Sprites leem os tiles 0..255 (SMS_useFirstHalfTilesforSprites). Cada
 * lutador tem DOIS bancos de 32 tiles: o stream escreve no banco ocioso e
 * so troca o banco exibido quando a pose inteira chegou. Sem isso a pose
 * aparecia meio velha / meio nova durante os ~5 frames do upload — o rasgo
 * que aparecia em todo soco (startup=4 frames < upload).
 * A fonte fica em 18..58: e so BG, nenhum sprite referencia esses indices.
 */
/* O palco mudou para 256+: e regiao SO de BG (o name table indexa 0..511,
 * os sprites so enxergam 0..255), entao 93 tiles de cais nao disputam espaco
 * com lutador nenhum. O mapa continua em bytes; o offset entra em runtime. */
#define TILE_STAGE  256  /* 256..348 — palco (93 tiles) */
#define TILE_FONT   18   /* 18..60 — fonte 8x8 + barras (BG) */
#define TILE_P1A    96   /* 96..127  */
#define TILE_P1B    128  /* 128..159 */
#define TILE_P2A    160  /* 160..191 */
#define TILE_P2B    192  /* 192..223 */
#define TILE_FB1    224  /* 224..227 — Hadouken indo para a direita */
#define TILE_FB1L   228  /* 228..231 — mesmo, espelhado */
#define TILE_FB2    232  /* 232..235 — Sonic Boom indo para a direita */
#define TILE_FB2L   236  /* 236..239 — mesmo, espelhado */

#define FIGHTER_W   32
#define FIGHTER_H   64
#define GROUND_Y    112
#define HP_MAX      64

#define STAGE_X_MIN 8
#define STAGE_X_MAX 216
#define PUSH_W      20   /* meia-largura somada: corpos param de se atravessar */

#define POSE_IDLE    0
#define POSE_WALK    1
#define POSE_PUNCH   2
#define POSE_SPECIAL 3
#define POSE_HIT     4
#define POSE_KO      5
#define POSE_CROUCH  6
#define POSE_JUMP    7

/* Controle é uma propriedade explicita da partida. Neutral humano nunca
 * cai no caminho da CPU por acidente. */
#define CONTROL_HUMAN  0
#define CONTROL_CPU    1
#define CONTROL_DUMMY  2
typedef unsigned char ControlMode;
#define CONTROL_REPLAY 3

typedef struct {
    unsigned char attacker;
    unsigned char defender;
    unsigned char identity;
    unsigned char kind;
    unsigned char damage;
} Contact;

typedef struct {
    signed int x;
    signed int y;
    signed char vy;         /* pulo: velocidade vertical (0 = no chao) */
    unsigned char facing;   /* 1 = right */
    unsigned char hp;
    unsigned int state;
    unsigned char timer;
    unsigned char startup;
    unsigned char active;
    unsigned char recovery;
    unsigned char pose;
    unsigned char hit_used; /* um golpe so acerta uma vez por ativacao */
    unsigned char guard;    /* segurando tras neste frame */
    unsigned char rounds;
    unsigned char fireball_on;
    signed int fx, fy;
    signed char fvx;
    unsigned char hist[8];
    unsigned char hist_i;
} Fighter;

extern Fighter P[2];
extern unsigned char g_gs;
extern unsigned int g_frame;
extern unsigned char g_timer;
extern unsigned char g_tics;
extern unsigned char g_hitstop;
extern unsigned char g_attract;   /* 1 = ninguem tocou no controle ainda */
extern unsigned char g_banner;    /* frames restantes do texto central */
extern unsigned char g_banner_id;
extern unsigned char g_shake;     /* deslocamento vertical do impacto */
extern unsigned char g_round_number;
extern ControlMode g_control_mode[2];

/* IDs de banner (texto central). */
#define BN_NONE     0
#define BN_ROUND1   1
#define BN_ROUND2   2
#define BN_ROUND3   3
#define BN_FIGHT    4
#define BN_KO       5
#define BN_TIMEUP   6
#define BN_P1WINS   7
#define BN_P2WINS   8
#define BN_DRAW     9

/* Parallax por raster: ceu e mar-perto rolam, horizonte e deck ficam. */
void stage_raster(void);
void stage_scroll_frame(void);

void fight_init(void);
void fight_go_live(void);
void fight_update(unsigned int keys);
void fight_set_control_mode(unsigned char who, unsigned char mode);
void fight_set_replay_input(unsigned char who, unsigned int keys);
void fight_prepare_stream(void);
void fight_stream(void);
void fight_draw(void);

void text_init(void);
void text_at(unsigned char col, unsigned char row, const char *s);
void text_clear(unsigned char col, unsigned char row, unsigned char n);
void text_num(unsigned char col, unsigned char row, unsigned char v,
              unsigned char digits);
void hud_static(void);
void hud_reset(void);
void title_draw(void);
void title_press(unsigned char visivel);
void title_clear(void);
void hud_draw(void);
void hud_banner(void);

#endif
