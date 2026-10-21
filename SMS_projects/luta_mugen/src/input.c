/* Ring do consumidor de produto: blobs CMD v3/v4, dois slots e tier temporal. */
#include "input.h"
#include "input_tier.h"

#define CMD_BLOB_VERSION 4u
#define CMD_BLOB_LEGACY_VERSION 3u
#define CMD_BLOB_V3_STEP_BYTES 2u
#define CMD_BLOB_V4_STEP_BYTES 3u
#define S_E1 0x40u
#define S_E2 0x80u
#define S_PULSE (S_E1 | S_E2)
#define S_LEVEL_MASK 0x33u
#define MAX_CMD_STEPS 8u

static unsigned char buf[2][INPUT_BUF];
static unsigned char buf_i[2];
static unsigned char nonzero[2];
static unsigned char pulses[2];
static unsigned char command_dirty[2];
static InputTier tiers[2];
/* A carga temporizada e mantida fora do anel: cada evento de soltura guarda
 * a duracao saturada da direcao cardinal que acabou de subir. */
static unsigned char dir_release_age[2][INPUT_BUF][4];
static unsigned char dir_release_exact[2][INPUT_BUF];
static unsigned char dir_held_ticks[2][4];
static unsigned char dir_held_exact[2][4];

void input_flush(unsigned char slot) {
    unsigned char i, d, key1, key2;
    if (slot >= 2u) return;
    key1 = tiers[slot].threshold[0];
    key2 = tiers[slot].threshold[1];
    for (i = 0; i < INPUT_BUF; i++) buf[slot][i] = 0;
    buf_i[slot] = 0;
    nonzero[slot] = 0;
    pulses[slot] = 0;
    command_dirty[slot] = 0;
    for (i = 0; i < INPUT_BUF; i++)
        for (d = 0; d < 4u; d++) dir_release_age[slot][i][d] = 0;
    for (i = 0; i < INPUT_BUF; i++) dir_release_exact[slot][i] = 0;
    for (d = 0; d < 4u; d++) {
        dir_held_ticks[slot][d] = 0;
        dir_held_exact[slot][d] = 0;
    }
    input_tier_init(&tiers[slot], key1, key2);
}

void input_init(void) {
    unsigned char slot;
    for (slot = 0; slot < 2u; slot++) {
        input_tier_init(&tiers[slot], 6, 6);
        input_flush(slot);
    }
}

void input_set_thresholds(unsigned char slot, unsigned char key1,
                          unsigned char key2) {
    if (slot >= 2u) return;
    input_tier_init(&tiers[slot], key1, key2);
}

unsigned char input_tick(unsigned char slot, unsigned char keys,
                         unsigned char facing) {
    unsigned char sample, old, events, i, dirs, levels, prev_i;
    unsigned char prev_dirs, current_dirs, d, mask;
    if (slot >= 2u) return 0;
    levels = (unsigned char)(((keys & INPUT_KEY1) ? 1u : 0u) |
                             ((keys & INPUT_KEY2) ? 2u : 0u));
    events = input_tier_step(&tiers[slot], levels);

    /* U/D e as duas teclas mantem a posicao do bit do blob; so F/B troca
     * quando o lutador olha para a esquerda. */
    sample = (unsigned char)(keys & S_LEVEL_MASK);
    dirs = (unsigned char)(keys & (INPUT_LEFT | INPUT_RIGHT));
    if (facing)
        dirs = (unsigned char)(((dirs << 1) & INPUT_RIGHT) |
                               ((dirs >> 1) & INPUT_LEFT));
    sample |= dirs;
    if (events & (INPUT_TIER_K1_LIGHT | INPUT_TIER_K1_STRONG)) sample |= S_E1;
    if (events & (INPUT_TIER_K2_LIGHT | INPUT_TIER_K2_STRONG)) sample |= S_E2;

    i = buf_i[slot];
    prev_i = (unsigned char)((i - 1u) & INPUT_BUF_MASK);
    prev_dirs = (unsigned char)(buf[slot][prev_i] & 0x0Fu);
    current_dirs = (unsigned char)(sample & 0x0Fu);
    mask = 1u;
    dir_release_exact[slot][i] = 0;
    for (d = 0; d < 4u; d++, mask = (unsigned char)(mask << 1)) {
        dir_release_age[slot][i][d] = 0;
        if (current_dirs & mask) {
            if (prev_dirs & mask) {
                if (dir_held_ticks[slot][d] != 0xFFu)
                    dir_held_ticks[slot][d]++;
                if (current_dirs != mask) dir_held_exact[slot][d] = 0;
            } else {
                dir_held_ticks[slot][d] = 1u;
                dir_held_exact[slot][d] = (current_dirs == mask) ? 1u : 0u;
            }
        } else {
            if (prev_dirs & mask) {
                dir_release_age[slot][i][d] = dir_held_ticks[slot][d];
                if (dir_held_exact[slot][d]) dir_release_exact[slot][i] |= mask;
            }
            dir_held_ticks[slot][d] = 0;
            dir_held_exact[slot][d] = 0;
        }
    }
    old = buf[slot][i];
    if (!old && sample) nonzero[slot]++;
    else if (old && !sample) nonzero[slot]--;
    if (!(old & S_PULSE)) { if (sample & S_PULSE) pulses[slot]++; }
    else if (!(sample & S_PULSE)) pulses[slot]--;
    if (old != sample) command_dirty[slot] = 1;
    buf[slot][i] = sample;
    buf_i[slot] = (unsigned char)((i + 1u) & INPUT_BUF_MASK);
    return events;
}

/* A command result can only appear when the normalized timeline changes.
 * Consume this once per tick to skip redundant scans of all CMD blobs. */
unsigned char input_take_command_dirty(unsigned char slot) {
    unsigned char dirty;
    if (slot >= 2u) return 0;
    dirty = command_dirty[slot];
    command_dirty[slot] = 0;
    return dirty;
}

/* Tier 0 means the source command asks for the physical level. Tiers 1/2
 * require a fresh weak/strong pulse and the corresponding release/held level. */
static unsigned char step_match(unsigned char got, unsigned char want,
                                unsigned char tier, unsigned char four_way) {
    unsigned char dirs = (unsigned char)(want & 0x0Fu);
    unsigned char keys = (unsigned char)(want & 0x30u);
    if (dirs && (four_way ? ((unsigned char)(got & dirs) != dirs)
                          : ((unsigned char)(got & 0x0Fu) != dirs))) return 0;
    if (!keys) return (unsigned char)(dirs || !(got & S_LEVEL_MASK));
    if (tier == 0u) return (unsigned char)((got & keys) == keys);
    if (tier >= 3u) return 0;  /* this runtime has one threshold per key */
    if (keys & INPUT_KEY1) {
        if (!(got & S_E1)) return 0;
        if (tier == 1u) { if (got & INPUT_KEY1) return 0; }
        else             { if (!(got & INPUT_KEY1)) return 0; }
    }
    if (keys & INPUT_KEY2) {
        if (!(got & S_E2)) return 0;
        if (tier == 1u) { if (got & INPUT_KEY2) return 0; }
        else             { if (!(got & INPUT_KEY2)) return 0; }
    }
    return 1;
}

unsigned char input_pattern_hit(unsigned char slot,
                                const unsigned char *pattern) {
    unsigned char *row, n, window, age, have_newest = 0;
    unsigned char newest = 0, oldest = 0, newest_i = 0, cur;
    unsigned char want, flags, got, version, step_bytes;
    unsigned char release_i = 0, release_dir = 0, have_timed_release = 0;
    signed char si;
    const unsigned char *steps;
    if (slot >= 2u || !pattern) return 0;
    version = pattern[0];
    if (version == CMD_BLOB_VERSION) step_bytes = CMD_BLOB_V4_STEP_BYTES;
    else if (version == CMD_BLOB_LEGACY_VERSION) step_bytes = CMD_BLOB_V3_STEP_BYTES;
    else return 0;
    n = pattern[1];
    window = pattern[2];
    if (!n || n > MAX_CMD_STEPS || window >= INPUT_BUF) return 0;
    if (!nonzero[slot]) return 0;
    row = buf[slot];
    steps = pattern + 4;
    flags = steps[(unsigned char)(n - 1u) * step_bytes + 1u];
    if ((flags & 0xE0u) ||
        (steps[(unsigned char)(n - 1u) * step_bytes] & 0xC0u))
        return 0;
    if ((steps[(unsigned char)(n - 1u) * step_bytes] & 0x30u) &&
        ((flags >> 2) & 3u) && !pulses[slot]) return 0;

    cur = row[(unsigned char)((buf_i[slot] - 1u) & INPUT_BUF_MASK)];
    si = (signed char)(n - 1u);
    for (age = 0; age < INPUT_BUF && si >= 0; age++) {
        unsigned char i = (unsigned char)((buf_i[slot] - 1u - age) & INPUT_BUF_MASK);
        unsigned char offset = (unsigned char)si * step_bytes;
        unsigned char release_time = (step_bytes == CMD_BLOB_V4_STEP_BYTES)
            ? steps[offset + 2u] : 0u;
        unsigned char timed_dir = 0;
        got = row[i];
        want = steps[offset];
        flags = steps[offset + 1u];
        if ((flags & 0xE0u) || (want & 0xC0u)) return 0;
        if (release_time) {
            unsigned char dirs = (unsigned char)(want & 0x0Fu);
            if (!(flags & 2u) || (flags & 1u) || (flags & 0x0Cu) ||
                (want & 0x30u) ||
                (dirs != 0x01u && dirs != 0x02u &&
                 dirs != 0x04u && dirs != 0x08u)) return 0;
            if      (dirs == 0x01u) timed_dir = 0u;
            else if (dirs == 0x02u) timed_dir = 1u;
            else if (dirs == 0x04u) timed_dir = 2u;
            else                    timed_dir = 3u;
            if (dir_release_age[slot][i][timed_dir] < release_time) continue;
            if (!(flags & 0x10u) &&
                !(dir_release_exact[slot][i] & (unsigned char)(1u << timed_dir)))
                continue;
            if (!have_timed_release) {
                release_i = i;
                release_dir = timed_dir;
                have_timed_release = 1u;
            }
        } else if (!step_match(got, want,
                               (unsigned char)((flags >> 2) & 3u),
                               (unsigned char)(flags & 0x10u))) continue;
        if ((flags & 1u) &&
            !step_match(cur, want, (unsigned char)((flags >> 2) & 3u),
                        (unsigned char)(flags & 0x10u)))
            continue;
        /* Tier 1 is emitted at release itself, so its release token is
         * already satisfied by the pulse and released level in this sample. */
        if ((flags & 2u) && ((flags >> 2) & 3u) != 1u &&
            step_match(cur, want, (unsigned char)((flags >> 2) & 3u),
                       (unsigned char)(flags & 0x10u))) continue;
        if (!have_newest) { newest = age; newest_i = i; have_newest = 1; }
        oldest = age;
        si--;
    }
    if (si >= 0 || (unsigned char)(oldest - newest) > window) return 0;

    /* A tier pulse belongs to one command only. Priority is resolved by the
     * caller (special before its terminal weak-button command). */
    want = steps[(unsigned char)(n - 1u) * step_bytes];
    flags = steps[(unsigned char)(n - 1u) * step_bytes + 1u];
    if ((want & 0x30u) && ((flags >> 2) & 3u)) {
        got = row[newest_i];
        if (got & S_PULSE) {
            row[newest_i] = (unsigned char)(got & (unsigned char)~S_PULSE);
            pulses[slot]--;
            if (!(row[newest_i])) nonzero[slot]--;
        }
    }
    if (have_timed_release) {
        dir_release_age[slot][release_i][release_dir] = 0;
        dir_release_exact[slot][release_i] &=
            (unsigned char)~(1u << release_dir);
    }
    return 1;
}
