/* cpu_controller.h — policy CPU pura, sem SMSlib e sem dados de personagem.
 *
 * Os move specs são emitidos pelo pipeline MUGEN e contêm uma sequência de
 * níveis do pad. Cada amostra usa direções relativas ao próprio lutador e as
 * duas teclas físicas; cpu_controller_step devolve K_* do input.h, isto é, o
 * mesmo contrato que input_pad_levels() entrega ao runtime humano.
 */
#ifndef CPU_CONTROLLER_H
#define CPU_CONTROLLER_H

#include "input.h"

#define CPU_INPUT_FORWARD 0x01u
#define CPU_INPUT_BACK    0x02u
#define CPU_INPUT_DOWN    0x04u
#define CPU_INPUT_UP      0x08u
#define CPU_INPUT_KEY_1   0x10u
#define CPU_INPUT_KEY_2   0x20u

#define CPU_MOVE_SPECIAL  0x01u
#define CPU_MOVE_SUPER    0x02u
#define CPU_MOVE_ANTIAIR  0x04u
#define CPU_MOVE_AIR      0x08u
#define CPU_MOVE_VS_GUARD 0x10u
#define CPU_MOVE_ESCAPE   0x20u

#define CPU_THREAT_NONE 0u
#define CPU_THREAT_HIGH 1u
#define CPU_THREAT_LOW  2u

#define CPU_INTERACTION_NONE  0u
#define CPU_INTERACTION_HIT   1u
#define CPU_INTERACTION_BLOCK 2u
#define CPU_INTERACTION_WHIFF 3u

typedef enum {
    CPU_DIFFICULTY_EASY = 0,
    CPU_DIFFICULTY_NORMAL = 1,
    CPU_DIFFICULTY_HARD = 2
} CpuDifficulty;

typedef struct {
    unsigned char reaction_ticks;
    unsigned char decision_ticks;
    unsigned char aggression;       /* limiar 0..255, não altera regras de combate */
    unsigned char guard_chance;     /* limiar 0..255; mesmo Hard não é perfeito */
} CpuProfile;

/* Uma ordem por lutador/ação. samples é dado estático gerado a partir do CMD;
 * nenhum estado ou nome de Ryo/Terry aparece no controlador.
 * min/max_range são pixels relativos ao eixo; energy_cost usa a unidade
 * declarada pelo pacote convertido. cooldown é finito e medido em ticks. */
typedef struct {
    const unsigned char *samples;
    unsigned char sample_count;
    unsigned char flags;
    unsigned char min_range;
    unsigned char max_range;
    unsigned char energy_cost;
    unsigned char weight;
    unsigned char cooldown;
} CpuMove;

/* Snapshot público do jogo. O adaptador preenche estes campos a partir da
 * posição/pose/recovery/vida/energia visíveis. attack_visible só sobe quando
 * o ataque é reconhecível visualmente; não deve expor o comando privado do pad.
 * Life bands são 0..3, já calculadas pelo owner do HUD para evitar divisão no
 * loop quente. */
typedef struct {
    unsigned char self_x;
    unsigned char opponent_x;
    unsigned char self_facing;      /* 0 = direita, 1 = esquerda */
    unsigned char self_alive;
    unsigned char self_can_act;
    unsigned char self_airborne;
    unsigned char self_at_left_edge;
    unsigned char self_at_right_edge;
    unsigned char self_energy;
    unsigned char self_life_band;
    unsigned char opponent_life_band;
    unsigned char opponent_alive;
    unsigned char opponent_airborne;
    unsigned char opponent_guarding;
    unsigned char opponent_recovery_ticks;
    unsigned char opponent_attack_visible;
    unsigned char opponent_attack_height; /* CPU_THREAT_HIGH/LOW */
    unsigned char self_last_interaction;  /* evento deste tick: resultado do golpe próprio */
} CpuObservation;

typedef struct {
    unsigned int random_state;
    unsigned char difficulty;
    unsigned char threat_seen;
    unsigned char guard_this_threat;
    unsigned char reaction_left;
    unsigned char attack_cooldown;
    unsigned char decision_wait;
    unsigned char script_active;
    unsigned char script_move;
    unsigned char script_tick;
    unsigned char last_move;
    unsigned char last_interaction;
    unsigned char avoid_move;
    unsigned char avoid_move_ticks;
} CpuController;

const CpuProfile *cpu_controller_profile(unsigned char difficulty);
void cpu_controller_init(CpuController *cpu, unsigned char difficulty,
                         unsigned int seed);

/* Converte uma amostra relativa de CpuMove no nível K_* do adaptador do pad.
 * Exportado para validar scripts gerados contra o mesmo input ring do humano. */
unsigned char cpu_controller_pad_levels(unsigned char relative,
                                        unsigned char facing_left);

/* Retorna níveis K_* (UP/DOWN/LEFT/RIGHT/KEY_1/KEY_2), nunca eventos de dano.
 * move_count deve caber em unsigned char; dados e scripts têm vida estática. */
unsigned char cpu_controller_step(CpuController *cpu,
                                 const CpuObservation *observation,
                                 const CpuMove *moves,
                                 unsigned char move_count);

#endif /* CPU_CONTROLLER_H */
