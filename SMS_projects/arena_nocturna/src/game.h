/* game.h — contrato unico entre os modulos de arena_nocturna.
 *
 * Regra desta base: nenhum modulo escreve em VRAM fora da janela pos-VBlank,
 * e nenhum modulo le o teclado fora de main.c. Quem quebra isso quebra o
 * determinismo de boot, que e eixo congelado no GDD.
 */
#ifndef GAME_H
#define GAME_H

#include "SMSlib.h"

/* ---------------------------------------------------------------- geometria
 * O modo de sprite e ZOOMED: cada tile 8x8 ocupa 16x16 na tela. Todo offset
 * de metasprite e toda dimensao de colisao abaixo estao em PIXELS DE TELA,
 * nunca em pixels de tile — misturar as duas unidades foi o que produziu
 * hitboxes que nao batiam com o desenho.
 */
#define HERO_W        32
#define HERO_H        32
#define BOSS_W        64
#define BOSS_H        64
#define SHOT_W        16
#define SHOT_H        16

/* Campo jogavel em pixels de tela. A HUD ocupa as 2 primeiras linhas de tile
 * (16px) — que sao exatamente as que VDPFEATURE_LOCKHSCROLL trava — por isso
 * FIELD_Y0 comeca abaixo delas. */
#define FIELD_X0      12
#define FIELD_X1      196
#define FIELD_Y0      24
#define FIELD_Y1      132

/* ------------------------------------------------------------------- tiles
 * Layout de VRAM. BG ocupa 64..191 (arena_bg), sprites 192..255.
 * Qualquer asset novo entra a partir de SPRITE_TILE_TOP; passar de 256 e
 * estouro silencioso de VRAM.
 */
#define HERO_TILE            192
#define SHOT_TILE            196
#define COUNTER_TILE         197
#define HERO_WALK_TILE       200
#define IMPACT_TILE          204
#define BOSS_TL_TILE         208
#define BOSS_TR_TILE         212
#define BOSS_BL_TILE         216
#define BOSS_BR_TILE         220
#define BOSS_CHARGE_TL_TILE  224
#define BOSS_CHARGE_TR_TILE  228
#define BOSS_CHARGE_BL_TILE  232
#define BOSS_CHARGE_BR_TILE  236
#define SPRITE_TILE_TOP      240

/* ------------------------------------------------------------ orcamento SAT
 * O VDP desenha no maximo 8 sprites por scanline; o 9o some. O boss ocupa 4
 * colunas de sprite em cada scanline que cobre, entao sobram 4 para o resto.
 * Estes tetos existem para que o pior caso caiba — nao sao decoracao.
 */
#define MAX_COUNTERS   3
#define MAX_FX         2
#define FX_FRAMES      12

/* ------------------------------------------------------------------ estados
 * A maquina de estados e a estrutura que faltava: sem ela nao ha atracao,
 * nao ha pausa e nao ha tela de fim — o jogo era um unico laco.
 */
#define ST_TITLE   0
#define ST_PLAY    1
#define ST_PAUSE   2
#define ST_OVER    3
extern unsigned char g_state;
/* Demonstração determinística: mantém a fatia observável mesmo quando o
 * harness do Emulicious não entrega teclas ao joypad. Inputs reais continuam
 * sendo aceitos por state_play quando o canal físico estiver disponível. */
extern unsigned char g_demo_mode;

/* Contador global de frames. E o instrumento que measure_frame_advance.py
 * cronometra pelo HUD; nunca pode parar, nem durante hitstop ou pausa. */
extern unsigned int g_frame;
#define DEMO_WARMUP_FRAMES 240
#define TITLE_FRAMES        180

/* ------------------------------------------------------------------- player */
typedef struct {
    signed int  x, y;
    unsigned char hp;
    unsigned char invuln;   /* frames restantes de invulnerabilidade */
    unsigned char moving;
    unsigned char facing;   /* 0 = direita, 1 = esquerda */
    unsigned char cooldown; /* frames ate poder disparar de novo */
    unsigned char shot_on;
    signed int  shot_x, shot_y;
    signed int  shot_prev_x;
} Player;
extern Player g_player;

void player_reset(void);
void player_update(unsigned int keys);
void player_draw(void);

/* --------------------------------------------------------------------- boss
 * FSM real, com fases ligadas ao HP. A versao anterior tinha vaivem fixo de
 * 1px e um teleporte vertical de 8px — nao era comportamento, era ruido.
 */
#define BOSS_IDLE      0
#define BOSS_TELEGRAPH 1
#define BOSS_FIRE      2
#define BOSS_RECOIL    3
#define BOSS_DEAD      4
#define BOSS_HURT      5

typedef struct {
    signed int    x, y;
    signed int    vy;
    unsigned char hp, hp_max;
    unsigned char st;
    unsigned char timer;
    unsigned char phase;    /* 0,1,2 — sobe conforme o nucleo cai */
    unsigned char flash;    /* frames de piscada ao levar dano */
} Boss;
extern Boss g_boss;

void boss_reset(void);
void boss_update(void);
void boss_draw(void);
void boss_hit(void);

/* ----------------------------------------------------------------- projeteis */
typedef struct {
    unsigned char on;
    signed int    x, y;
    signed char   vx, vy;
} Counter;
extern Counter g_counter[MAX_COUNTERS];

typedef struct {
    unsigned char on;
    unsigned char timer;
    signed int    x, y;
} Fx;
extern Fx g_fx[MAX_FX];

void ent_reset(void);
void ent_update(void);
void ent_draw(void);
unsigned char ent_spawn_counter(signed int x, signed int y,
                                signed char vx, signed char vy);
void ent_spawn_fx(signed int x, signed int y);

/* --------------------------------------------------------------------- HUD
 * hud_dirty() marca; hud_draw() so escreve o que mudou. Redesenhar a HUD
 * inteira todo frame com o display ligado era escrita de VRAM fora da janela
 * segura — custo real, sem beneficio.
 */
void hud_reset(void);
void hud_mark(void);
void hud_draw(void);
void hud_banner(unsigned char state);

/* -------------------------------------------------------------------- audio */
#define SFX_SHOT   0
#define SFX_HIT    1
#define SFX_HURT   2
#define SFX_DOWN   3

void audio_init(void);
void audio_music(unsigned char on);
void audio_music_title(void);
void sfx_play(unsigned char id);
void audio_frame(void);

/* ------------------------------------------------------------------- partida */
extern unsigned int  g_score;
extern unsigned char g_hitstop;
extern unsigned char g_wave;   /* dificuldade progressiva: sobe com o tempo */

#endif /* GAME_H */
