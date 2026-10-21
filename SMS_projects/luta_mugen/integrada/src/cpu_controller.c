/* cpu_controller.c — tactical controller independent of MUGEN actor names. */
#include "cpu_controller.h"

/* Valores iniciais de protótipo. São tuning de comportamento, não um resultado
 * de playtest; reação é contada em ticks da ROM. Mesmo Hard atrasa e pode
 * escolher não defender. Ajustar depois de input real e teste de jogo. */
static const CpuProfile profiles[3] = {
    { 18u, 12u,  80u, 160u }, /* Easy: ~300 ms NTSC antes de reagir */
    { 12u,  8u, 152u, 208u }, /* Normal */
    {  7u,  4u, 220u, 232u }  /* Hard: ~117 ms NTSC; PAL usa ticks da ROM */
};

const CpuProfile *cpu_controller_profile(unsigned char difficulty) {
    if (difficulty > CPU_DIFFICULTY_HARD) difficulty = CPU_DIFFICULTY_NORMAL;
    return &profiles[difficulty];
}

void cpu_controller_init(CpuController *cpu, unsigned char difficulty,
                         unsigned int seed) {
    if (difficulty > CPU_DIFFICULTY_HARD) difficulty = CPU_DIFFICULTY_NORMAL;
    cpu->random_state = seed ? seed : 0xACE1u;
    cpu->difficulty = difficulty;
    cpu->threat_seen = 0;
    cpu->guard_this_threat = 0;
    cpu->reaction_left = 0;
    cpu->attack_cooldown = 0;
    cpu->decision_wait = 0;
    cpu->script_active = 0;
    cpu->script_move = 0xFFu;
    cpu->script_tick = 0;
    cpu->last_move = 0xFFu;
    cpu->last_interaction = CPU_INTERACTION_NONE;
    cpu->avoid_move = 0xFFu;
    cpu->avoid_move_ticks = 0;
}

static unsigned char random8(CpuController *cpu) {
    unsigned int low = (unsigned int)(cpu->random_state & 1u);
    cpu->random_state >>= 1;
    if (low) cpu->random_state ^= 0xB400u;
    return (unsigned char)(cpu->random_state >> 8);
}

static unsigned char add_saturated(unsigned char a, unsigned char b) {
    unsigned int sum = (unsigned int)a + (unsigned int)b;
    return sum > 255u ? 255u : (unsigned char)sum;
}

static unsigned char distance_px(const CpuObservation *o) {
    if (o->self_x >= o->opponent_x)
        return (unsigned char)(o->self_x - o->opponent_x);
    return (unsigned char)(o->opponent_x - o->self_x);
}

/* Move scripts stay self-relative until this final pad adapter. */
unsigned char cpu_controller_pad_levels(unsigned char relative,
                                       unsigned char facing_left) {
    unsigned char out = 0;
    if (relative & CPU_INPUT_UP) out |= K_UP;
    if (relative & CPU_INPUT_DOWN) out |= K_DOWN;
    if (relative & CPU_INPUT_KEY_1) out |= K_LP;
    if (relative & CPU_INPUT_KEY_2) out |= K_HP;
    if (relative & CPU_INPUT_FORWARD)
        out |= facing_left ? K_LEFT : K_RIGHT;
    if (relative & CPU_INPUT_BACK)
        out |= facing_left ? K_RIGHT : K_LEFT;
    return out;
}

static unsigned char facing_relative_levels(const CpuObservation *o,
                                           unsigned char relative) {
    return cpu_controller_pad_levels(relative, o->self_facing);
}

static unsigned char is_corner(const CpuObservation *o) {
    return (unsigned char)(o->self_at_left_edge || o->self_at_right_edge);
}

static unsigned char move_usable(const CpuMove *m, const CpuObservation *o) {
    if (!m->samples || !m->sample_count || m->min_range > m->max_range)
        return 0;
    if (m->energy_cost > o->self_energy) return 0;
    if (o->self_airborne) {
        if (!(m->flags & CPU_MOVE_AIR)) return 0;
    } else if (m->flags & CPU_MOVE_AIR) {
        return 0;
    }
    if (o->opponent_airborne && !(m->flags & CPU_MOVE_ANTIAIR)) return 0;
    return 1;
}

static void finish_script(CpuController *cpu, const CpuMove *moves,
                          unsigned char move_count, unsigned char add_wait) {
    const CpuProfile *profile = cpu_controller_profile(cpu->difficulty);
    unsigned char cooldown = profile->decision_ticks;
    if (cpu->script_move < move_count &&
        moves[cpu->script_move].cooldown > cooldown)
        cooldown = moves[cpu->script_move].cooldown;
    if (add_wait || cpu->script_active) cpu->attack_cooldown = cooldown;
    cpu->script_active = 0;
    cpu->script_move = 0xFFu;
    cpu->script_tick = 0;
}

static unsigned char emit_script(CpuController *cpu,
                                 const CpuObservation *o,
                                 const CpuMove *moves,
                                 unsigned char move_count) {
    const CpuMove *m;
    unsigned char sample;
    if (!cpu->script_active || cpu->script_move >= move_count) {
        cpu->script_active = 0;
        cpu->script_move = 0xFFu;
        cpu->script_tick = 0;
        return 0;
    }
    m = &moves[cpu->script_move];
    if (!m->samples || cpu->script_tick >= m->sample_count) {
        finish_script(cpu, moves, move_count, 1);
        return 0;
    }
    sample = m->samples[cpu->script_tick++];
    if (cpu->script_tick >= m->sample_count)
        finish_script(cpu, moves, move_count, 1);
    return facing_relative_levels(o, sample);
}

static unsigned char guard_levels(const CpuObservation *o) {
    unsigned char relative = CPU_INPUT_BACK;
    if (o->opponent_attack_height == CPU_THREAT_LOW)
        relative |= CPU_INPUT_DOWN;
    return facing_relative_levels(o, relative);
}

static unsigned char movement_toward_opponent(const CpuObservation *o) {
    return facing_relative_levels(o, CPU_INPUT_FORWARD);
}

static unsigned char movement_away_from_opponent(const CpuObservation *o) {
    return facing_relative_levels(o, CPU_INPUT_BACK);
}

static unsigned char choose_move(CpuController *cpu,
                                 const CpuObservation *o,
                                 const CpuMove *moves,
                                 unsigned char move_count,
                                 unsigned char distance,
                                 unsigned char *max_reach,
                                 unsigned char *min_reach) {
    unsigned char i, found = 0, best = 0xFFu;
    unsigned int best_score = 0xFFFFu;
    *max_reach = 0;
    *min_reach = 0xFFu;
    for (i = 0; i < move_count; i++) {
        const CpuMove *m = &moves[i];
        unsigned char preference;
        unsigned int score;
        if (!move_usable(m, o)) continue;
        if (m->max_range > *max_reach) *max_reach = m->max_range;
        if (m->min_range < *min_reach) *min_reach = m->min_range;
        if (distance < m->min_range || distance > m->max_range) continue;
        if (cpu->avoid_move_ticks && i == cpu->avoid_move) continue;

        preference = m->weight;
        if (o->opponent_recovery_ticks)
            preference = add_saturated(preference, 48u);
        if (o->opponent_guarding) {
            if (m->flags & CPU_MOVE_VS_GUARD)
                preference = add_saturated(preference, 56u);
            else
                preference = preference > 32u ?
                    (unsigned char)(preference - 32u) : 0u;
        }
        if (is_corner(o)) {
            if (m->flags & CPU_MOVE_ESCAPE)
                preference = add_saturated(preference, 64u);
            else
                preference = preference > 24u ?
                    (unsigned char)(preference - 24u) : 0u;
        }
        if (o->opponent_airborne && (m->flags & CPU_MOVE_ANTIAIR))
            preference = add_saturated(preference, 48u);
        if (o->self_life_band < o->opponent_life_band)
            preference = add_saturated(preference, 16u);

        /* Min-score selection uses weight as preference and a seeded tie/noise
         * value. It needs no division or variable-size temporary buffer. */
        score = (unsigned int)(255u - preference) + random8(cpu);
        if (!found || score < best_score) {
            found = 1;
            best = i;
            best_score = score;
        }
    }
    return best;
}

unsigned char cpu_controller_step(CpuController *cpu,
                                 const CpuObservation *o,
                                 const CpuMove *moves,
                                 unsigned char move_count) {
    const CpuProfile *profile;
    unsigned char distance, threat, max_reach, min_reach, selected;
    unsigned char aggression;

    profile = cpu_controller_profile(cpu->difficulty);
    if (o->self_last_interaction != CPU_INTERACTION_NONE) {
        cpu->last_interaction = o->self_last_interaction;
        if (o->self_last_interaction == CPU_INTERACTION_BLOCK ||
            o->self_last_interaction == CPU_INTERACTION_WHIFF) {
            cpu->avoid_move = cpu->last_move;
            cpu->avoid_move_ticks = (unsigned char)(profile->decision_ticks * 2u);
        }
    } else {
        cpu->last_interaction = CPU_INTERACTION_NONE;
        if (cpu->avoid_move_ticks) {
            cpu->avoid_move_ticks--;
            if (!cpu->avoid_move_ticks) cpu->avoid_move = 0xFFu;
        }
    }
    if (!o->self_alive || !o->opponent_alive) {
        if (cpu->script_active) finish_script(cpu, moves, move_count, 0);
        cpu->threat_seen = 0;
        cpu->reaction_left = 0;
        cpu->guard_this_threat = 0;
        return 0;
    }

    threat = o->opponent_attack_visible;
    if (!threat) {
        cpu->threat_seen = 0;
        cpu->reaction_left = 0;
        cpu->guard_this_threat = 0;
    } else if (!cpu->threat_seen) {
        cpu->threat_seen = 1;
        cpu->reaction_left = profile->reaction_ticks;
        cpu->guard_this_threat =
            (unsigned char)(random8(cpu) < profile->guard_chance);
    }

    if (threat) {
        if (cpu->script_active) finish_script(cpu, moves, move_count, 1);
        if (cpu->reaction_left) {
            cpu->reaction_left--;
            return 0;
        }
        if (cpu->guard_this_threat && o->self_can_act && !o->self_airborne)
            return guard_levels(o);
        return 0;
    }

    if (!o->self_can_act) {
        if (cpu->script_active) finish_script(cpu, moves, move_count, 1);
        return 0;
    }

    if (cpu->script_active)
        return emit_script(cpu, o, moves, move_count);

    distance = distance_px(o);
    if (cpu->attack_cooldown) cpu->attack_cooldown--;
    if (cpu->decision_wait) cpu->decision_wait--;

    selected = choose_move(cpu, o, moves, move_count, distance,
                           &max_reach, &min_reach);
    if (distance > max_reach) return movement_toward_opponent(o);
    if (distance < min_reach) {
        if (!is_corner(o)) return movement_away_from_opponent(o);
        cpu->decision_wait = profile->decision_ticks;
        return 0;
    }
    if (cpu->attack_cooldown || cpu->decision_wait || selected == 0xFFu)
        return 0;

    aggression = profile->aggression;
    if (o->opponent_recovery_ticks)
        aggression = add_saturated(aggression, 48u);
    if (o->self_life_band < o->opponent_life_band)
        aggression = add_saturated(aggression, 24u);
    if (random8(cpu) >= aggression) {
        cpu->decision_wait = profile->decision_ticks;
        return 0;
    }

    cpu->script_active = 1;
    cpu->script_move = selected;
    cpu->script_tick = 0;
    cpu->last_move = selected;
    return emit_script(cpu, o, moves, move_count);
}
