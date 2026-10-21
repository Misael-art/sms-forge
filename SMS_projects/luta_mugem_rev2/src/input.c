/* input.c — ver inc/input.h. Modelo temporal dos dois pads, sem hardware.
 *
 * Sem float, sem malloc, sem SMSlib aqui: a porta fisica e lida em main.c e o
 * que chega e o nivel K_* do tick. O tier (fraco/forte por tempo de pressao) e
 * classificado por input_tier.c, um jogo de maquinas por ator.
 */
#include "input.h"
#include "input_tier.h"

/* codificacao da amostra = bits baixos do passo CMD (sms_cmd.py): */
#define CMD_BLOB_LEGACY_VERSION 3u
#define CMD_BLOB_V3_STEP_BYTES 2u
#define CMD_BLOB_V4_STEP_BYTES 3u
#define MAX_CMD_STEPS 8u
#define S_UP    0x01
#define S_DOWN  0x02
#define S_BACK  0x04
#define S_FWD   0x08
#define S_K1    0x10            /* nivel da tecla fisica 1 (fight.h: K_LP)  */
#define S_K2    0x20            /* nivel da tecla fisica 2 (fight.h: K_HP)  */
#define S_E1    0x40            /* pulso de tier da familia 1              */
#define S_E2    0x80            /* pulso de tier da familia 2              */
#define S_PULSE (S_E1 | S_E2)

/* A amostra nao e construida por quatro ramos: ela comeca de uma mascara de
 * bits, o que so vale enquanto cada K_* cair na mesma posicao do seu S_*.
 * Esta linha e a guarda dessa coincidencia -- se algum dos dois lados mudar de
 * bit, o build para aqui em vez de virar input invertido em runtime. */
typedef char input_mesma_posicao_de_bit[
    (S_UP == K_UP && S_DOWN == K_DOWN && S_K1 == K_LP && S_K2 == K_HP &&
     S_BACK == K_LEFT && S_FWD == K_RIGHT) ? 1 : -1];

static unsigned char buf[INPUT_PLAYERS][INPUT_BUF];   /* amostras normalizadas */
static unsigned char buf_i[INPUT_PLAYERS];            /* PROXIMA escrita */
static unsigned char nonzero[INPUT_PLAYERS];          /* amostras com input no anel */
static unsigned char pulsos[INPUT_PLAYERS];           /* amostras com pulso de tier */
static InputTier tiers[INPUT_PLAYERS];
/* A duracao da carga nao consome entradas do anel; cada soltura conserva a
 * duracao saturada da direcao cardinal liberada naquele tick. */
static unsigned char dir_release_age[INPUT_PLAYERS][INPUT_BUF][4];
static unsigned char dir_release_exact[INPUT_PLAYERS][INPUT_BUF];
static unsigned char dir_held_ticks[INPUT_PLAYERS][4];
static unsigned char dir_held_exact[INPUT_PLAYERS][4];

void input_init(void) {
    unsigned char who;
    for (who = 0; who < INPUT_PLAYERS; who++) input_flush(who);
}

void input_flush(unsigned char who) {
    unsigned char i, d;
    for (i = 0; i < INPUT_BUF; i++) buf[who][i] = 0;
    for (i = 0; i < INPUT_BUF; i++)
        for (d = 0; d < 4u; d++) dir_release_age[who][i][d] = 0;
    for (i = 0; i < INPUT_BUF; i++) dir_release_exact[who][i] = 0;
    for (d = 0; d < 4u; d++) {
        dir_held_ticks[who][d] = 0;
        dir_held_exact[who][d] = 0;
    }
    buf_i[who] = 0;
    nonzero[who] = 0;
    pulsos[who] = 0;
    input_tier_init(&tiers[who]);
}

void input_tick(unsigned char who, unsigned char levels, unsigned char facing) {
    unsigned char s, old, ev, i, prev_i, prev_dirs, current_dirs, d, mask;
    unsigned char *row;
    InputTier *t = &tiers[who];

    /* Atalho de ociosidade (medido, nao estimado): o corpo abaixo custa ~13
     * linhas de scanline por ator porque o SDCC coloca cada temporario em
     * -N(ix) e refaz a aritmetica de endereco do anel (diag_step_attr.py,
     * 2026-10-03). Com nenhum botao neste tick, nenhuma maquina de tier em
     * curso e nenhum input no anel, a amostra normalizada e OBRIGATORIAMENTE
     * zero: os bits de nivel e direcao viriam de `levels`, os de pulso de
     * `ev`, e `ev` so existe se `cnt` ainda contar uma pressao. Logo o unico
     * efeito observavel do corpo e avancar o relogio do anel, e e isso que
     * roda aqui. `nonzero` e a mesma premissa que `input_pattern_hit` ja usa
     * para nao varrer o anel; o relogio continua avancando, entao as idades
     * dos passos de FF/BB nao congelam. */
    if (!levels) {
        if (!nonzero[who] && !t->cnt[0] && !t->cnt[1] &&
            !t->fired[0] && !t->fired[1]) {
            i = buf_i[who];
            for (d = 0; d < 4u; d++) dir_release_age[who][i][d] = 0;
            dir_release_exact[who][i] = 0;
            buf_i[who] = (unsigned char)((i + 1u) & (INPUT_BUF - 1u));
            return;
        }
    }

    /* K_LP e 0x10, K_HP e 0x20: os dois bits de botao, ja na posicao da
     * familia (1 = tecla 1), sem dois testes de 16 bits. */
    ev = input_tier_step(t, (unsigned char)((levels >> 4) & 3u));

    /* K_UP|K_DOWN|K_LP|K_HP = 0x01|0x02|0x10|0x20 caem em S_UP|S_DOWN|S_K1|S_K2
     * com a MESMA bit-posicao, entao a amostra comeca como uma mascara e nao
     * como quatro ramos. Os dois unicos bits que mudam de lugar sao os
     * horizontais, e trocam entre si pela facing -- dois shifts e uma mascara
     * por bit, sem ramo. */
    s = (unsigned char)(levels & 0x33u);
    {
        unsigned char d = (unsigned char)(levels & 0x0Cu);
        if (facing) d = (unsigned char)(((d << 1) & 0x08u) | ((d >> 1) & 0x04u));
        s |= d;                       /* S_BACK 0x04, S_FWD 0x08 */
    }
    if (ev & (TIER_K1_LIGHT | TIER_K1_STRONG)) s |= S_E1;
    if (ev & (TIER_K2_LIGHT | TIER_K2_STRONG)) s |= S_E2;

    /* A linha do anel e uma so por tick: o endereco -N(ix) refeito a cada
     * acesso e o que resteira do custo do corpo. */
    row = buf[who];
    i = buf_i[who];
    prev_i = (unsigned char)((i - 1u) & (INPUT_BUF - 1u));
    prev_dirs = (unsigned char)(row[prev_i] & 0x0Fu);
    current_dirs = (unsigned char)(s & 0x0Fu);
    mask = 1u;
    dir_release_exact[who][i] = 0;
    for (d = 0; d < 4u; d++, mask = (unsigned char)(mask << 1)) {
        dir_release_age[who][i][d] = 0;
        if (current_dirs & mask) {
            if (prev_dirs & mask) {
                if (dir_held_ticks[who][d] != 0xFFu)
                    dir_held_ticks[who][d]++;
                if (current_dirs != mask) dir_held_exact[who][d] = 0;
            } else {
                dir_held_ticks[who][d] = 1u;
                dir_held_exact[who][d] = (current_dirs == mask) ? 1u : 0u;
            }
        } else {
            if (prev_dirs & mask) {
                dir_release_age[who][i][d] = dir_held_ticks[who][d];
                if (dir_held_exact[who][d]) dir_release_exact[who][i] |= mask;
            }
            dir_held_ticks[who][d] = 0;
            dir_held_exact[who][d] = 0;
        }
    }
    old = row[i];
    if (!old && s) nonzero[who]++;
    else if (old && !s) nonzero[who]--;
    if (!(old & S_PULSE)) { if (s & S_PULSE) pulsos[who]++; }
    else if (!(s & S_PULSE)) pulsos[who]--;
    row[i] = s;
    buf_i[who] = (unsigned char)((i + 1) & (INPUT_BUF - 1));
}

unsigned char input_busy(unsigned char who) {
    unsigned char i = (unsigned char)((buf_i[who] - 1) & (INPUT_BUF - 1));
    return buf[who][i] ? 1u : 0u;
}

/* token unico: passo de direcional ignora botao pressionado e vice-versa
 * (semantica MUGEN para "a" e "F" soltos); wants dupla exige as duas. */
static unsigned char step_match(unsigned char got, unsigned char want,
                                unsigned char tier, unsigned char four_way) {
    unsigned char wd = (unsigned char)(want & 0x0F);
    unsigned char wk = (unsigned char)(want & 0xF0);
    unsigned char expected_pulse = 0;
    if (wd && (four_way ? ((unsigned char)(got & wd) != wd)
                        : ((unsigned char)(got & 0x0F) != wd))) return 0;
    if (!wk) return 1;
    if (tier == 0) return (unsigned char)((got & (S_K1 | S_K2)) == wk);
    if (tier >= 3) return 0;                  /* sem um limiar por familia */
    if (wk & S_K1) expected_pulse |= S_E1;
    if (wk & S_K2) expected_pulse |= S_E2;
    /* Source State -1 checks multi-button commands before simple buttons
     * (for example Terry's y+b -> 240). A single-button pattern must not
     * consume a chord's simultaneous tier pulse as one of its members. */
    if ((got & S_PULSE) != expected_pulse) return 0;
    if (wk & S_K1) {
        if (!(got & S_E1)) return 0;
        if (tier == 1) { if (got & S_K1) return 0; }
        else           { if (!(got & S_K1)) return 0; }
    }
    if (wk & S_K2) {
        if (!(got & S_E2)) return 0;
        if (tier == 1) { if (got & S_K2) return 0; }
        else           { if (!(got & S_K2)) return 0; }
    }
    if (tier == 2 && (got & (S_K1 | S_K2)) != wk) return 0;
    return 1;
}

unsigned char input_pattern_hit(unsigned char who, const unsigned char *pattern) {
    unsigned char *row = buf[who];
    const unsigned char *steps;
    unsigned char n, window, age, have_newest = 0;
    unsigned char newest = 0, oldest = 0, newest_i = 0, got, cur;
    unsigned char w, f, version, step_bytes;
    unsigned char release_i = 0, release_dir = 0, have_timed_release = 0;
    signed char si;

    version = pattern[0];
    if (version == CMD_BLOB_VERSION) step_bytes = CMD_BLOB_V4_STEP_BYTES;
    else if (version == CMD_BLOB_LEGACY_VERSION) step_bytes = CMD_BLOB_V3_STEP_BYTES;
    else return 0;                                    /* formato desconhecido: fechado */
    n = pattern[1];
    window = pattern[2];
    if (!n || n > MAX_CMD_STEPS || window >= INPUT_BUF) return 0;
    /* Sem nenhuma amostra ativa, nenhum token pode casar; evita varrer os
     * neutros duas vezes a cada frame de idle/attract. */
    if (!nonzero[who]) return 0;
    steps = pattern + 4;
    /* Ultimo passo = token mais recente que o padrao exige. Se ele pede pulso
     * de tier (campo tier do PROPRIO blob) e nao
     * ha nenhum pulso vivo no anel, a varredura de 16 amostras nao pode casar:
     * `step_match` so aceita pulso quando tier >= 1. Em luta sustentada --
     * andar, agachar, guarda, pulo -- este e o caso dominante e custava quatro
     * varreduras por ator por frame. */
    if ((steps[(n - 1) * step_bytes] & 0xF0) &&
        ((steps[(n - 1) * step_bytes + 1] >> 2) & 3u)
        && !pulsos[who]) return 0;
    cur = row[(unsigned char)((buf_i[who] - 1) & (INPUT_BUF - 1))];
    si = (signed char)(n - 1);
    for (age = 0; age < INPUT_BUF && si >= 0; age++) {
        unsigned char i = (unsigned char)((buf_i[who] - 1 - age) & (INPUT_BUF - 1));
        unsigned char offset = (unsigned char)si * step_bytes;
        unsigned char release_time = (step_bytes == CMD_BLOB_V4_STEP_BYTES)
            ? steps[offset + 2u] : 0u;
        unsigned char timed_dir = 0;
        got   = row[i];
        w     = steps[offset];
        f     = steps[offset + 1u];
        if ((w & 0xC0u) || (f & 0xE0u)) return 0;  /* bits reservados */
        if (release_time) {
            unsigned char dirs = (unsigned char)(w & 0x0Fu);
            if (!(f & 2u) || (f & 1u) || (f & 0x0Cu) ||
                (w & 0x30u) ||
                (dirs != 0x01u && dirs != 0x02u &&
                 dirs != 0x04u && dirs != 0x08u)) return 0;
            if      (dirs == 0x01u) timed_dir = 0u;
            else if (dirs == 0x02u) timed_dir = 1u;
            else if (dirs == 0x04u) timed_dir = 2u;
            else                    timed_dir = 3u;
            if (dir_release_age[who][i][timed_dir] < release_time) continue;
            if (!(f & 0x10u) &&
                !(dir_release_exact[who][i] & (unsigned char)(1u << timed_dir)))
                continue;
            if (!have_timed_release) {
                release_i = i;
                release_dir = timed_dir;
                have_timed_release = 1u;
            }
        } else if (!step_match(got, w, (unsigned char)((f >> 2) & 3u),
                               (unsigned char)(f & 0x10u))) continue;
        if (f & 1) {                          /* hold: baixo AGORA tambem */
            if (!step_match(cur, w, (unsigned char)((f >> 2) & 3u),
                            (unsigned char)(f & 0x10u))) continue;
        }
        if (f & 2) {                          /* release: solto agora */
            if (step_match(cur, w, (unsigned char)((f >> 2) & 3u),
                           (unsigned char)(f & 0x10u))) continue;
        }
        if (!have_newest) { newest = age; newest_i = i; have_newest = 1; }
        oldest = age;
        si--;
    }
    if (si >= 0) return 0;
    if ((unsigned int)(oldest - newest) > (unsigned int)window) return 0;

    /* Consome o pulso que casou: o proximo frame nao pode repetir o golpe.
     * So os bits de pulso somem; direcional e nivel continuam no anel para os
     * padroes de movimento (FF/BB) que nao pedem forca. */
    got = row[newest_i];
    if (got & S_PULSE) {
        unsigned char after = (unsigned char)(got & (unsigned char)~S_PULSE);
        if (!after) nonzero[who]--;
        pulsos[who]--;              /* `after` nunca tem bit de pulso */
        row[newest_i] = after;
    }
    if (have_timed_release) {
        dir_release_age[who][release_i][release_dir] = 0;
        dir_release_exact[who][release_i] &=
            (unsigned char)~(1u << release_dir);
    }
    return 1;
}
