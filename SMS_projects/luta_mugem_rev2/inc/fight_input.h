/* fight_input.h — camada de perfil de CMD por lutador sobre o anel de input.
 *
 * A camada decide PAPEIS semânticos e nada mais: não escreve dano, posição,
 * animação nem paleta. O anel (src/input.c) normaliza pelo facing, consome o
 * pulso de tier e casa os blobs CMD emitidos pelo conversor; aqui entra a
 * política do consumidor: prioridade da tabela, contexto por direção do pad e
 * a política de cancel declarada.
 *
 * Fronteiras DECLARADAS (rom de diagnóstico, não execução CNS):
 *  - comando só produz papel a partir de papel com S_CONTROL no chão; o pacote
 *    versus-cut não traz cancelstate/cancelanim, então não há cancel — o
 *    one-shot expira (flag `done`) e o papel volta ao contexto;
 *  - papel sem rota de golpe (FIGHT_CMD_SPECIAL_UNSUPPORTED, ou código ausente
 *    da tabela) é CONTADO, nunca sacrificado em silêncio: ver
 *    fight_unrouted_mask() e o resultado `unrouted`;
 *  - a IA entrega NÍVEIS DE PAD (função pura de frame+facing) e percorre o
 *    mesmo anel, a mesma máquina de tier e a mesma tabela de comandos que o
 *    humano — prova causal pad→papel→pose→dano vale para os dois lados.
 *
 * Compila no host sem SMSlib (mesmo contrato de src/input.c), então o teste
 * diferencial (tests/input_wave5b_diff.py) exercita ESTE módulo, não uma
 * reimplementação em Python.
 */
#ifndef FIGHT_INPUT_H
#define FIGHT_INPUT_H

#include "input.h"
#include "rev2_diag.h"

#define FI_ROLE_NONE  0xFFu    /* manter o papel atual */
#define FI_CMD_NONE   0xFFu    /* nenhum comando casou neste tick */

/* Vista mínima do ator que a camada de input precisa ler. O restante do estado
 * (x, y, vida, animação) pertence ao consumidor. */
typedef struct {
    unsigned char role;        /* papel atual (índice em cd->states) */
    unsigned char done;        /* one-shot do papel atual expirou */
    unsigned char on_ground;   /* 1 quando y == 0 */
    unsigned char alive;       /* 1 quando vida > 0 */
    unsigned char face;        /* 0 = olhando para a direita */
} FightView;

/* Resultado do tick de um lado. */
typedef struct {
    unsigned char role;                    /* papel a aplicar, FI_ROLE_NONE = manter */
    unsigned char cmd_index;               /* índice em cd->commands que casou */
    unsigned char cmd_code;                /* FIGHT_CMD_* do que casou, 0 se nenhum */
    unsigned char unrouted;                /* 1 = casou comando sem rota de golpe */
    unsigned char busy;                    /* input_busy() deste lado neste tick */
} FightResult;

/* Código de comando -> papel de golpe nas tabelas emitidas (schema 5).
 * FI_ROLE_NONE = o código não tem papel de golpe (especial sem rota). */
unsigned char fight_command_role(unsigned char code);

/* Máscara de códigos de golpe AUSENTES na tabela de comandos do lutador:
 * bit0 LP, bit1 HP, bit2 LK, bit3 HK. Derivada dos dados, não de nomes. */
unsigned char fight_unrouted_mask(const CharacterData *cd);

/* Normaliza `levels` no anel do lado e decide o papel. `levels` são bits K_*
 * ABSOLUTOS do pad (esquerda/direita de tela); o anel faz a relativa à facing. */
void fight_input_step(unsigned char side, const CharacterData *cd,
                      const FightView *v, unsigned char levels,
                      FightResult *out);

/* Beat da IA (duração fixa, ciclo fechado) e o plano por beat. */
#define FI_AI_BEAT_FRAMES  25u
#define FI_AI_BEATS         12u

/* Níveis de pad que a IA entrega no frame dado. Função pura de (frame, face):
 * nenhuma escrita em dano, papel, posição ou animação. */
unsigned char fight_input_ai_levels(unsigned short frame, unsigned char face,
                                    unsigned char *out_beat);

#endif /* FIGHT_INPUT_H */
