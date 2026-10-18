/* input.c — leitura da Porta A + buffer temporal de 16 amostras (Task 5).
 *
 * Sem float, sem malloc, sem I/O alem de SMS_getKeysHeld (SMSlib.h:290).
 * O buffer e um anel de 16 bytes (potencia de 2 -> mascara, sem divisao);
 * cada frame input_tick() grava a amostra JA relativa ao lado (F/B), entao
 * os blobs CMD gerados (sms_cmd.py) comparam sem conhecer facing.
 */
#include "SMSlib.h"
#include "fight.h"
#include "input.h"

/* codificacao da amostra = byte do passo no blob CMD (sms_cmd.py): */
#define S_UP    0x01
#define S_DOWN  0x02
#define S_BACK  0x04
#define S_FWD   0x08
#define S_A     0x10
#define S_S     0x20

static unsigned char buf[INPUT_BUF];   /* amostras normalizadas */
static unsigned char buf_i;            /* PROXIMA escrita (ultima = buf_i-1) */
static unsigned char nonzero_samples;   /* quantas amostras do anel têm input */

void input_init(void) {
    unsigned char i;
    for (i = 0; i < INPUT_BUF; i++) buf[i] = 0;
    buf_i = 0;
    nonzero_samples = 0;
}

/* Nivel cru do pad -> convencao K_* do engine. START = botao 1 (SMSlib
 * alias), nao tem estado proprio no engine de luta. */
unsigned char input_read(void) {
    unsigned int h = SMS_getKeysHeld() &
                     (PORT_A_KEY_UP | PORT_A_KEY_DOWN | PORT_A_KEY_LEFT |
                      PORT_A_KEY_RIGHT | PORT_A_KEY_1 | PORT_A_KEY_2);
    unsigned char k = 0;
    if (h & PORT_A_KEY_UP)    k |= K_UP;
    if (h & PORT_A_KEY_DOWN)  k |= K_DOWN;
    if (h & PORT_A_KEY_LEFT)  k |= K_LEFT;
    if (h & PORT_A_KEY_RIGHT) k |= K_RIGHT;
    if (h & PORT_A_KEY_1)     k |= K_LP;
    if (h & PORT_A_KEY_2)     k |= K_HP;
    return k;
}

void input_tick(unsigned char keys, unsigned char facing) {
    unsigned char s = 0;
    unsigned char old;
    if (keys & K_UP)   s |= S_UP;
    if (keys & K_DOWN) s |= S_DOWN;
    if (facing) {   /* virado para a esquerda: esquerda e FRENTE */
        if (keys & K_LEFT)  s |= S_FWD;
        if (keys & K_RIGHT) s |= S_BACK;
    } else {
        if (keys & K_RIGHT) s |= S_FWD;
        if (keys & K_LEFT)  s |= S_BACK;
    }
    if (keys & K_LP) s |= S_A;
    if (keys & K_HP) s |= S_S;
    old = buf[buf_i];
    if (!old && s) nonzero_samples++;
    else if (old && !s) nonzero_samples--;
    buf[buf_i] = s;
    buf_i = (unsigned char)((buf_i + 1) & (INPUT_BUF - 1));
}

/* token unico: passo de direcional ignora botao pressionado e vice-versa
 * (semantica MUGEN para "a" e "F" soltos); wants dupla exige as duas. */
static unsigned char step_match(unsigned char got, unsigned char want) {
    unsigned char wd = (unsigned char)(want & 0x0F);
    unsigned char wk = (unsigned char)(want & 0xF0);
    if (wd && (unsigned char)(got & 0x0F) != wd) return 0;
    if (wk && (unsigned char)(got & wk) != wk)   return 0;
    return (unsigned char)(wd | wk);
}

unsigned char input_pattern_hit(const unsigned char *pattern) {
    unsigned char n = pattern[0];
    unsigned char window = pattern[1];
    const unsigned char *steps = pattern + 3;
    signed char si;
    unsigned char age, newest = 0, oldest = 0, have_newest = 0;
    unsigned char cur;

    /* Sem nenhuma amostra ativa, nenhum token de direcao/botao pode casar.
     * Evita varrer 16 neutros duas vezes a cada frame de idle/attract. */
    if (!n || !nonzero_samples) return 0;
    cur = buf[(unsigned char)((buf_i - 1) & (INPUT_BUF - 1))];
    si = (signed char)(n - 1);
    for (age = 0; age < INPUT_BUF && si >= 0; age++) {
        unsigned char want, flags, got;
        want  = steps[si * 2];
        flags = steps[si * 2 + 1];
        got   = buf[(unsigned char)((buf_i - 1 - age) & (INPUT_BUF - 1))];
        if (!step_match(got, want)) continue;
        if (flags & 1) {                       /* hold: baixo AGORA tambem */
            if (!step_match(cur, want)) continue;
        }
        if (flags & 2) {                       /* release: solto agora */
            if (step_match(cur, want)) continue;
        }
        if (!have_newest) { newest = age; have_newest = 1; }
        oldest = age;
        si--;
    }
    if (si >= 0) return 0;
    return (unsigned char)((oldest - newest) <= window);
}
