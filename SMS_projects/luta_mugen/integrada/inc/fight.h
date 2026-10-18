/* fight.h — motor de luta interpretado por dados AIR/SFF/ACT compilados.
 *
 * O estado do jogo vive em `Fighter` (luta.h); animacoes, tiles, paletas,
 * e caixas de colisao sao gerados offline de um corte declarado de arquivos
 * MUGEN. O interpretador Z80 segue fixo e nao carrega CNS em runtime.
 */
#ifndef FIGHT_H
#define FIGHT_H

#include "luta.h"

/* Bits de input ja na convencao do motor (Task 5 liga SMS_getKeysHeld a
 * estes bits via padroes do CMD; aqui vem de roteiro deterministico). */
#define K_UP     0x01
#define K_DOWN   0x02
#define K_LEFT   0x04
#define K_RIGHT  0x08
#define K_LP     0x10            /* botão 1 -> ação de soco selecionada */
#define K_HP     0x20            /* botão 2 -> ação de chute selecionada */
#define K_GUARD  0x40            /* guarda      -> state 120 */
#define K_SPECIAL 0x80           /* comando de movimento remapeado pelo buffer */

#define FIGHT_EVENT_NONE  0u
#define FIGHT_EVENT_PUNCH 1u
#define FIGHT_EVENT_KICK  2u
#define FIGHT_EVENT_SPECIAL 3u

/* Estado numerico exposto so para prova de RAM; os IDs de estados existentes
 * nao mudam quando o estado KO e acrescentado. */
#define FIGHT_STATE_KO 9u

extern Fighter fighters[2];
volatile extern unsigned char dbg_frame;   /* contador do loop p/ HUD */

void fight_init(void);                     /* inicializa o stream de poses (T6) */
void fight_reset(Fighter *p, unsigned char slot);
void fight_set_ko(Fighter *p);
unsigned char fight_step(Fighter *p, unsigned int keys,
                         unsigned int opp_keys);
void fight_draw(void);
/* 1 when the next iteration should not upload pairs: the scheduler was
 * deferred onto that iteration so it still finishes before the VBlank. */
unsigned char fight_skip_stream(void);
void fight_upload_palette(void);
void sat_setup(void);                      /* VDP reg 5: SAT at 0x3F00 */
void sat_upload(void);                     /* RAM SAT -> VRAM, in VBlank */            /* chamada no VBlank */
void fight_sat_copied(void);                /* após copiar meta para SAT */
unsigned char fight_visible_pose(unsigned char slot);
unsigned char fight_visible_dur(unsigned char slot);
unsigned char fight_visible_hitbox(unsigned char slot);
unsigned char fight_state_pose0(unsigned char slot);
unsigned short fight_max_life(unsigned char slot);

#endif /* FIGHT_H */
