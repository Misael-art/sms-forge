/* input_tier.h — classificador de tier por tempo de pressao (doc/22).
 *
 * Cada tecla fisica do pad (KEY_1, KEY_2) e uma maquina de estado independente:
 *   segurada por >= INPUT_TIER_T ticks  -> evento FORTE no tick T-1 apos o toque (sem esperar soltar);
 *   solta antes                         -> evento FRACO no 1o tick com a tecla solta.
 * Pior caso adicionado: T-1 ticks nos dois tiers. Sem divisao, sem float, 4 bytes de RAM por ator.
 * Dois pads = duas maquinas: o estado vive na struct, nao em globais (doc/23, 6.B).
 * Referencia de host: tools/sms_wrapper/mugen2sms/converters/sms_controls.py classify_trace().
 * Desde 2026-10-03 esta ligado ao build da ROM (integrada/src/input.c o consome); os estados
 * e assets de golpe forte ainda faltam (doc/22, "O que falta"; doc/23, 6.C).
 */
#ifndef INPUT_TIER_H
#define INPUT_TIER_H

#ifndef INPUT_TIER_T
#define INPUT_TIER_T 6          /* ticks; parametro de jogabilidade, validar com jogador */
#endif

#define TIER_K1_LIGHT  0x01
#define TIER_K1_STRONG 0x02
#define TIER_K2_LIGHT  0x04
#define TIER_K2_STRONG 0x08

typedef struct {
    unsigned char cnt[2];        /* ticks de pressao consecutivos (satura em 255) */
    unsigned char fired[2];      /* forte ja emitido nesta pressao */
} InputTier;

void input_tier_init(InputTier *t);
/* down: bit0 = KEY_1 seguro, bit1 = KEY_2 seguro, neste tick. Retorna mascara TIER_*. */
unsigned char input_tier_step(InputTier *t, unsigned char down);

#endif
