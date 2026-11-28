/* fight_input.c — ver inc/fight_input.h. Camada de decisão sobre o anel.
 *
 * Sem float, sem malloc, sem SMSlib: quem lê a porta física é main.c. Os
 * limiares de tempo (tier) vivem em src/input_tier.c e a janela de amostras em
 * src/input.c; este arquivo só liga dados emitidos a papéis.
 */
#include "fight_input.h"

/* Código -> papel: os dois lados desta correspondência são contratos do
 * gerador (rev2_diag.h enumera os papéis do STATE_ROLE_ORDER e os códigos
 * FIGHT_CMD_*; fight_runtime_data.py emite a tabela de comandos com esses
 * códigos). Nenhum nome de lutador aparece aqui. */
unsigned char fight_command_role(unsigned char code) {
    switch (code) {
        case FIGHT_CMD_LP: return (unsigned char)ST_PUNCH;
        case FIGHT_CMD_HP: return (unsigned char)ST_HP;
        case FIGHT_CMD_LK: return (unsigned char)ST_KICK;
        case FIGHT_CMD_HK: return (unsigned char)ST_HK;
        default:           return FI_ROLE_NONE;
    }
}

/* Rota ausente = código de golpe que nenhum elemento de cd->commands carrega.
 * É a contabilidade de "comando sem rota" pedida pelo contrato do produto:
 * o padrão existe no cabeçalho de cena, mas não chegou à tabela do runtime. */
unsigned char fight_unrouted_mask(const CharacterData *cd) {
    unsigned char mask = 0x0Fu;
    unsigned char i;
    for (i = 0u; i < cd->command_count; i++) {
        switch (cd->commands[i].command) {
            case FIGHT_CMD_LP: mask = (unsigned char)(mask & ~0x01u); break;
            case FIGHT_CMD_HP: mask = (unsigned char)(mask & ~0x02u); break;
            case FIGHT_CMD_LK: mask = (unsigned char)(mask & ~0x04u); break;
            case FIGHT_CMD_HK: mask = (unsigned char)(mask & ~0x08u); break;
            default: break;
        }
    }
    return mask;
}

/* Papel de contexto a partir das DIREÇÕES cruas do pad, normalizadas pela face
 * do ator (F = para o oponente). Ordem declarada: guarda (Baixo+Trás, que não é
 * botão) > pulo (Cima, só a partir do chão) > agachar > andar > idle. */
static unsigned char context_role(const FightView *v, unsigned char levels) {
    unsigned char down = (unsigned char)(levels & K_DOWN);
    unsigned char fwd  = (unsigned char)(v->face ? (levels & K_LEFT)
                                                 : (levels & K_RIGHT));
    unsigned char back = (unsigned char)(v->face ? (levels & K_RIGHT)
                                                 : (levels & K_LEFT));
    if (down && back)                              return (unsigned char)ST_GUARD;
    if ((levels & K_UP) && v->on_ground)           return (unsigned char)ST_JUMP;
    if (down)                                      return (unsigned char)ST_CROUCH;
    if (fwd)                                       return (unsigned char)ST_WALK_F;
    if (back)                                      return (unsigned char)ST_WALK_B;
    return (unsigned char)ST_IDLE;
}

void fight_input_step(unsigned char side, const CharacterData *cd,
                      const FightView *v, unsigned char levels,
                      FightResult *out) {
    unsigned char flags;

    out->role = FI_ROLE_NONE;
    out->cmd_index = FI_CMD_NONE;
    out->cmd_code = 0u;
    out->unrouted = 0u;

    input_tick(side, levels, v->face);
    out->busy = input_busy(side);

    if (!v->alive) return;          /* KO: papel terminal até o reset */

    flags = cd->states[v->role].flags;

    /* 1) Comando, na ordem da tabela emitida (prioridade do gerador:
     *    compostos/fortes antes dos terminais). Só a partir de papel
     *    controlavel no chao; sem dados de cancel, o one-shot expira primeiro. */
    if ((flags & S_CONTROL) && v->on_ground) {
        unsigned char i;
        for (i = 0u; i < cd->command_count; i++) {
            if (!input_pattern_hit(side, cd->commands[i].pattern)) continue;
            out->cmd_index = i;
            out->cmd_code = cd->commands[i].command;
            {
                unsigned char r = fight_command_role(out->cmd_code);
                if (r == FI_ROLE_NONE) {
                    out->unrouted = 1u;   /* reconhecido, sem rota de golpe */
                    return;
                }
                out->role = r;
            }
            return;
        }
    }

    /* 2) One-shot expirado: volta ao contexto (idle/and/agach/guard/pulo).
     * So no chao: o papel de pulo e S_AIR e a fonte nao traz estado aereo
     * alcancavel neste pacote, entao o ator mantem a pose de pulo ate y == 0
     * (o avanco de fisica e independente do papel). Reverter no ar reiniciaria
     * a animacao no meio do arco. */
    if (v->done && !(flags & S_CONTROL)) {
        if (!v->on_ground) return;
        out->role = context_role(v, levels);
        return;
    }

    /* 3) Contexto contínuo: troca de papel apenas em papel controlável. */
    if (flags & S_CONTROL) {
        unsigned char c = context_role(v, levels);
        if (c != v->role) out->role = c;
    }
}

/* Batidas do plano da IA: uma por FI_AI_BEAT_FRAMES frames, ciclo fechado.
 * Duas variáveis genéricas de movimento (meia-lua para frente e meia-lua para
 * tras) coexistem porque o pacote traz CMDs diferentes por lutador; a IA nao
 * escolhe por nome — ela entrega os dois movimentos e a tabela de comandos do
 * lado decide qual reconhece. */
#define AI_BEAT_IDLE      0u
#define AI_BEAT_WALK_F    1u
#define AI_BEAT_WALK_B    2u
#define AI_BEAT_CROUCH    3u
#define AI_BEAT_GUARD     4u
#define AI_BEAT_JUMP      5u
#define AI_BEAT_HOLD_K1   6u
#define AI_BEAT_HOLD_K2   7u
#define AI_BEAT_TAP_K1    8u
#define AI_BEAT_TAP_K2    9u
#define AI_BEAT_MOTION_A 10u
#define AI_BEAT_MOTION_B 11u

/* Temporalidade do plano, derivada da maquina de tier e do anel (nao chutada):
 *  - FORTE: o pulso sai no tick em que a contagem de pressao atinge
 *    INPUT_TIER_T (6) com a tecla ainda segurada -> segurar 8 ticks garante o
 *    forte dentro do beat e o tier 2 do blob casa (a tecla continua no anel);
 *  - FRACO: 3 ticks de pressao e soltura -> pulso no 4o tick com a tecla fora,
 *    que e o tier 1 dos blobs de golpe leve e dos especiais emitidos;
 *  - movimento composto: 2 ticks por direcao com 1 tick de soltura entre as
 *    duas primeiras etapas, toque no fim. O ultimo passo (pulso) fica a 8
 *    amostras da primeira direcao, dentro das 16 do anel E da janela 15 do
 *    blob P1/P2_CUT_CMD_SPECIAL — um plano mais lento nao casaria nunca. */
#define AI_HOLD_TICKS   8u
#define AI_TAP_TICKS    3u
#define AI_MOTION_STEPS 10u   /* entradas usadas da tabela de movimento */

/* Direcoes em bits RELATIVOS (layout do proprio blob: U=0x01 D=0x02 B=0x04
 * F=0x08); a face do ator decide onde cada uma cai no pad absoluto. As teclas
 * (K_LP 0x10, K_HP 0x20) NAO colidem com 0x04/0x08, entao passam pelo mesmo
 * mask: um mask de 0x03 descartava a tecla do passo final do movimento e a IA
 * ficava incapaz de lancar especial -- silencioso, porque o plano seguia
 * entregando as direcoes. */
#define R_DOWN  0x02u
#define R_BACK  0x04u
#define R_FWD   0x08u
#define R_K2    K_HP            /* tecla fisica 2: ja e um bit absoluto */
#define R_KEEP  (K_UP | K_DOWN | K_LP | K_HP)

static unsigned char rel_to_abs(unsigned char rel, unsigned char fwd,
                                unsigned char back) {
    unsigned char out = (unsigned char)(rel & R_KEEP);
    if (rel & R_BACK) out = (unsigned char)(out | back);
    if (rel & R_FWD)  out = (unsigned char)(out | fwd);
    return out;
}

/* frente, solta, baixo, frente+baixo, toque KEY_2 */
static const unsigned char ai_motion_a[AI_MOTION_STEPS] = {
    R_FWD, R_FWD, 0u, R_DOWN, R_DOWN, (R_DOWN | R_FWD), (R_DOWN | R_FWD),
    R_K2, R_K2, 0u
};
/* baixo, solta, frente+baixo, frente, toque KEY_2 */
static const unsigned char ai_motion_b[AI_MOTION_STEPS] = {
    R_DOWN, R_DOWN, 0u, (R_DOWN | R_FWD), (R_DOWN | R_FWD), R_FWD, R_FWD,
    R_K2, R_K2, 0u
};

/* O mesmo plano serve a função de consulta aleatória e o relógio sequencial;
 * só o cálculo da fase muda, não os níveis que entram no anel de input. */
static unsigned char ai_levels_phase(unsigned char beat, unsigned char sub,
                                     unsigned char face) {
    unsigned char fwd  = (unsigned char)(face ? K_LEFT : K_RIGHT);
    unsigned char back = (unsigned char)(face ? K_RIGHT : K_LEFT);

    switch (beat) {
        case AI_BEAT_WALK_F:   return fwd;
        case AI_BEAT_WALK_B:   return back;
        case AI_BEAT_CROUCH:   return K_DOWN;
        case AI_BEAT_GUARD:    return (unsigned char)(K_DOWN | back);
        case AI_BEAT_JUMP:     return (sub < AI_TAP_TICKS) ? K_UP : 0u;
        case AI_BEAT_HOLD_K1:  return (sub < AI_HOLD_TICKS) ? K_LP : 0u;
        case AI_BEAT_HOLD_K2:  return (sub < AI_HOLD_TICKS) ? K_HP : 0u;
        case AI_BEAT_TAP_K1:   return (sub < AI_TAP_TICKS) ? K_LP : 0u;
        case AI_BEAT_TAP_K2:   return (sub < AI_TAP_TICKS) ? K_HP : 0u;
        case AI_BEAT_MOTION_A:
            if (sub >= AI_MOTION_STEPS) return 0u;
            return rel_to_abs(ai_motion_a[sub], fwd, back);
        case AI_BEAT_MOTION_B:
            if (sub >= AI_MOTION_STEPS) return 0u;
            return rel_to_abs(ai_motion_b[sub], fwd, back);
        default:                 return 0u;      /* idle */
    }
}

unsigned char fight_input_ai_levels(unsigned short frame, unsigned char face,
                                    unsigned char *out_beat) {
    unsigned char beat = (unsigned char)((frame / FI_AI_BEAT_FRAMES) % FI_AI_BEATS);
    unsigned char sub = (unsigned char)(frame % FI_AI_BEAT_FRAMES);
    if (out_beat) *out_beat = beat;
    return ai_levels_phase(beat, sub, face);
}

void fight_ai_clock_reset(FightAIClock *clock) {
    clock->beat = 0u;
    clock->sub = 0u;
}

void fight_ai_clock_advance(FightAIClock *clock, unsigned short frame) {
    /* O contador da ROM também volta a zero; 65536 não é múltiplo de 300. */
    if (frame == 0u) {
        fight_ai_clock_reset(clock);
        return;
    }
    clock->sub++;
    if (clock->sub >= FI_AI_BEAT_FRAMES) {
        clock->sub = 0u;
        clock->beat++;
        if (clock->beat >= FI_AI_BEATS) clock->beat = 0u;
    }
}

unsigned char fight_input_ai_levels_clock(const FightAIClock *clock,
                                          unsigned char face) {
    return ai_levels_phase(clock->beat, clock->sub, face);
}
