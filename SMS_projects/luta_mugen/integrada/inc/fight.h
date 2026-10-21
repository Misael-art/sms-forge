/* fight.h — motor de luta interpretado por dados AIR/SFF/ACT compilados.
 *
 * O estado do jogo vive em `Fighter` (luta.h); animacoes, tiles, paletas,
 * e caixas de colisao sao gerados offline de um corte declarado de arquivos
 * MUGEN. O interpretador Z80 segue fixo e nao carrega CNS em runtime.
 */
#ifndef FIGHT_H
#define FIGHT_H

#include "input.h"
#include "luta.h"

/* Bits de input vivem em inc/input.h (K_*): o modelo temporal nao depende de
 * luta.h/SMSlib e por isso compila no host (test_input_ring_c.py). */

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
void fight_cpu_init(unsigned char difficulty, unsigned int seed);
unsigned char fight_cpu_input(unsigned char slot);
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
unsigned short fight_source_action_id(unsigned char slot);
unsigned char fight_source_element_index(unsigned char slot);
unsigned short fight_max_life(unsigned char slot);

#endif /* FIGHT_H */
