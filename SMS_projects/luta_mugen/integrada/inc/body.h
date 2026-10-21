/* body.h — corpo-a-corpo (playerpush) e auto-facing, provados no host.
 *
 * O handoff do Lote D (doc/23, 6.B) pede "playerpush (empurrar sem atravessar;
 * limites por linha de piso e por borda da arena)" e a correcao da inversao de
 * auto-facing do achado L098. As duas REGRAS vivem aqui, sem SMSlib e sem
 * luta.h, para que `tests/test_body_push_c.py` as prove com gcc antes de
 * qualquer ROM. fight.c so chama.
 *
 * Posicoes em Q8.8 do mesmo espaco que `Fighter.x` (unsigned 16 bits no SDCC:
 * todo intermediario fica entre x_min e x_max por construcao, sem estourar 65535).
 */
#ifndef BODY_H
#define BODY_H

typedef struct {
    unsigned int x;          /* Q8.8, na arena [x_min, x_max] */
    unsigned int y;          /* altura acima da linha de piso, Q8.8 (0 = no chao) */
    unsigned char half_w;    /* meia-largura do corpo, px (vem da CLSN hurt) */
} Body;

/* Separou? 1 sim, 0 nao mexeu em nada. So age com os dois na linha de piso:
 * no ar um ator passa pelo outro (pular por cima continua valido). */
unsigned char body_separate(Body *a, Body *b, unsigned int x_min,
                            unsigned int x_max);

/* 0 = adversario a direita, 1 = a esquerda, empate = mantem o lado atual.
 * O empate era a inversao do L098: sem desempate, dois corpos no mesmo x
 * faziam o ator virar de lado e o direcional parecer invertido. */
unsigned char body_facing(unsigned int self_x, unsigned int other_x,
                          unsigned char current);

#endif /* BODY_H */
