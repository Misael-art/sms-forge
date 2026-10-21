/* input.h — anel temporal POR ATOR com niveis do pad e pulsos de tier.
 *
 * Contrato (doc/22 + doc/23, secao 6.B):
 *  - Quem le a porta fisica e `main.c` (Porta A = P1, Porta B = P2). Ate aqui o
 *    modulo e so modelo temporal: compila no host sem SMSlib, e assim e testado
 *    (tools/sms_wrapper/mugen2sms/tests/test_input_ring_c.py).
 *  - `levels` sao os bits K_* de fight.h. K_LP = tecla fisica 1, K_HP = tecla
 *    fisica 2; a guarda nao e botao: e Down+Tras (o motor ja faz isso).
 *  - `input_tick()` chama a maquina de tier (input_tier.c) e grava UMA amostra
 *    por ator no anel de INPUT_BUF, ja relativa ao LADO (F = para o oponente).
 *  - `input_pattern_hit()` le o blob `_CMD_` versionado que o conversor emite
 *    (converters/sms_cmd.py: serialize_pattern) e consome o pulso que casou: um
 *    toque produce UM golpe, nao um golpe por frame enquanto o pulso mora no anel.
 *
 * Amostra (byte) — os quatro bits baixos sao os do blob, os proximos dois sao o
 * nivel das teclas fisicas, os dois mais altos sao o PULSO do tier (1o = familia
 * 1, 2o = familia 2):
 *
 *   0x01 U   0x02 D   0x04 B   0x08 F   0x10 tecla1   0x20 tecla2   0x40 E1  0x80 E2
 *
 * Blob CMD v3 usa dois bytes por passo; v4 usa [want, flags, release_time].
 * Flags: bits 0 hold, 1 release, 2-3 tier, 4 four-way (`$` MUGEN).
 * `release_time` em v4 mede a duracao da soltura de uma direcao cardinal; a
 * direcao pode ser acumulada fora do anel para preservar a janela de 16 samples.
 * `$D` casa D/DF/DB; `$F` casa F/UF/DF apos normalizar pela facing.
 * Tier no passo (2 bits do byte de flags, do blob):
 *   0 = sem requisito de forca (nivel, como era antes do mapa);
 *   1 = FRACO: pulso da familia nesta amostra e tecla JA solta;
 *   2 = FORTE: pulso da familia nesta amostra e tecla ainda segurando;
 *   3 = a maquina de runtime tem UM limiar (INPUT_TIER_T), nao distingue -> falha fechado.
 */
#ifndef INPUT_H
#define INPUT_H

/* Bits de input na convencao do motor. K_LP/K_HP sao as DUAS TECLAS FISICAS do
 * pad, nao "soco fraco/forte": KEY_1 = familia do soco (a / c), KEY_2 = familia
 * do chute (x / z); a forca sai do tempo de pressao (doc/22). K_GUARD e
 * K_SPECIAL nao sao botoes fisicos — guarda e Down+Tras, e especial vem de um
 * comando de movimento (FF) lido pelo anel. */
#define K_UP      0x01
#define K_DOWN    0x02
#define K_LEFT    0x04
#define K_RIGHT   0x08
#define K_LP      0x10            /* tecla fisica 1 (PORT_x_KEY_1) */
#define K_HP      0x20            /* tecla fisica 2 (PORT_x_KEY_2) */
#define K_GUARD   0x40            /* sintetico: roteiro/atalho, nao e botao */
#define K_SPECIAL 0x80            /* sintetico: comando de movimento */

#define INPUT_BUF     16        /* amostras por anel; potencia de 2 -> mascara, sem divisao */
#define INPUT_PLAYERS  2
#define CMD_BLOB_VERSION 4      /* == sms_cmd.BLOB_FMT_VERSION */

void input_init(void);
/* Descarta o anel de UM ator: entre rounds a ROM nao da tick de input, e um
 * pulso de tier escrito no round anterior moraria ali ate INPUT_BUF ticks e
 * dispararia um golpe no primeiro frame do round novo. Zera tambem a maquina
 * de tier: quem segurou o botao no intervalo precisa tocar de novo. */
void input_flush(unsigned char who);
/* who: 0 = P1 (Porta A), 1 = P2 (Porta B). facing: 0 = olhando para a direita. */
void input_tick(unsigned char who, unsigned char levels, unsigned char facing);
unsigned char input_pattern_hit(unsigned char who, const unsigned char *pattern);
/* 1 quando a amostra ESCRITA NO ULTIMO tick tem nivel ou pulso — o sinal que
 * diz a `fight_step` se o frame precisa do passo cheio. Chamar depois de
 * input_tick(). Nao e "o anel tem algo": amostras velhas moram no anel por
 * INPUT_BUF ticks e nao acordam ninguem. */
unsigned char input_busy(unsigned char who);

#endif /* INPUT_H */
