/* stream.c -- shared pair pool + assembly upload loop (see stream.h).
 *
 * The upload loop is the one proven in scale_pilot_rom_flicker_asmstream
 * (Ken 4.00 frames/pose at AIR 4, gate L091 PASS): per 64 B pair, OUTI copy
 * while VCounter is 0xC0-0xDF. The phase profile of ROM ea856217 (sa_limit
 * 0x20) still crossed the next VBlank whenever that copy ran on to ~line 46
 * (~90 ticks from the SAT stamp). The loop stops at VCounter >= 0xE0
 * (cp #0xE0 / jp nc). sa_limit remains the backstop if a copy is still
 * running in the active display.
 * Target slots are never in the displayed SAT.
 *
 * Measured in the first integrated build: scanning all 128 slots twice and
 * copying the whole target struct at every commit took ~90 lines right
 * after the SAT copy. Each target now keeps its own slot list and SHOWN /
 * NEXT are indices into two targets per fighter (commit = index swap).
 */
#include "SMSlib.h"
#include "luta.h"
#include "stream.h"

#define MAP_IDS (KEN_POSE_PAIR_IDS > RYU_POSE_PAIR_IDS ? KEN_POSE_PAIR_IDS : RYU_POSE_PAIR_IDS)
/* Largest pose has 38 distinct pairs (gen_pose_table.py); 64 here pushed the
 * data segment over the fixed probe addresses at 0xC7A0-0xC7FF. */
#define MAX_UPLOADS 40u
typedef char uploads_fit[(KEN_POSE_MAX_PIECES <= MAX_UPLOADS &&
                          RYU_POSE_MAX_PIECES <= MAX_UPLOADS) ? 1 : -1];
#define NO_SLOT 0xFFu

typedef struct { unsigned char bank; unsigned int off; unsigned char slot; } PairLoad;
typedef char pair_load_is_4_bytes[(sizeof(PairLoad) == 4u) ? 1 : -1];

typedef struct {
    const PoseTiles *pt;          /* 0 = empty */
    unsigned char facing, pose;
    unsigned char nslots;
    unsigned char map[MAP_IDS];   /* compact pair id -> pool slot */
    PairLoad loads[MAX_UPLOADS];  /* one per slot: also the slot list */
} Target;

static Target tgt[2][2];
static unsigned char shown_i[2];          /* tgt[who][shown_i] is SHOWN */
static unsigned char load_done[2];        /* progress of NEXT */
static unsigned char presenting[2];       /* NEXT was put in the SAT being built */
/* Free slots as a stack: allocation pops, release pushes (O(1) per pair).
 * A linear scan of a used[] map cost up to ~200 lines per pose change
 * because other targets' slots are interleaved. */
static unsigned char free_stack[STREAM_SLOTS];
static unsigned char free_top;          /* number of free slots */
static unsigned char reclaim[2];      /* NEXT holds the old SHOWN, not a request */

unsigned char stream_slots_used, stream_slots_peak;
unsigned char stream_alloc_fail, stream_dropped;

#define SHOWN(w) (&tgt[w][shown_i[w]])
#define NEXT(w)  (&tgt[w][shown_i[w] ^ 1u])

static const unsigned char *target_meta(const Target *t) {
    return t->facing ? t->pt->meta_l : t->pt->meta_r;
}

/* ---- pool bookkeeping in assembly (the C loops cost ~40 lines per pose
 * change and fighter). Interface through globals. ---- */
static const PairLoad *rl_loads;
static unsigned char rl_n;

/* push load.slot onto the free stack for rl_n loads starting at rl_loads */
static void release_asm(void) __naked {
    __asm
        ld a, (_rl_n)
        or a
        ret z
        ld b, a
        ld hl, (_rl_loads)
        ld d, #0
    rl_loop:
        inc hl
        inc hl
        inc hl
        ld c, (hl)
        inc hl
        push hl
        ld a, (_free_top)
        ld e, a
        inc a
        ld (_free_top), a
        ld hl, #_free_stack
        add hl, de
        ld (hl), c
        pop hl
        djnz rl_loop
        ret
    __endasm;
}

static void release(Target *t) {
    rl_loads = t->loads;
    rl_n = t->nslots;
    release_asm();
    stream_slots_used -= t->nslots;
    t->nslots = 0;
    t->pt = 0;
}

/* Walk only the pose's pieces (<= 38): a generation stamp per pair id says
 * whether the id was already assigned in this allocation, so the 77-entry
 * map is never cleared or scanned (that version cost ~120 lines/fighter).
 * Worst case needs <= 38 slots; the pool always keeps at least that free
 * while both fighters hold at most current + next (125 of 128, sized). */
static unsigned char seen_gen[MAP_IDS];
static unsigned char gen;

static const unsigned char *al_meta;
static unsigned char *al_map;
static PairLoad *al_loads;
static unsigned char al_bank, al_n, al_fail;
static unsigned int al_off;
__sfr __at (0x7e) st_vcounter;
volatile unsigned char __at(0xC7CC) tl_al[4];  /* DIAG: before/after asm, pieces, n */

/* For each piece until 0x80: id = tile >> 1; skip ids already stamped with
 * gen; else take the first free slot from al_s, mark it, map[id] = slot and
 * append {bank, off + id * 64, slot}. Sets al_fail when the pool runs out
 * (the C caller rolls back the al_n loads already written). */
static void allocate_asm(void) __naked {
    __asm
        ld hl, (_al_meta)
        xor a
        ld (_al_n), a
        ld (_al_fail), a
    al_loop:
        ld a, (hl)
        cp #0x80
        ret z
        inc hl
        inc hl
        ld a, (hl)
        inc hl
        srl a
        push hl
        ld e, a
        ld d, #0
        ld hl, #_seen_gen
        add hl, de
        ld a, (_gen)
        cp (hl)
        jr z, al_skip
        ld (hl), a
        ld a, (_free_top)
        or a
        jr z, al_full
        dec a
        ld (_free_top), a
        ld c, a
        ld b, #0
        ld hl, #_free_stack
        add hl, bc
        ld c, (hl)
        ld hl, (_al_map)
        add hl, de
        ld (hl), c
        ld hl, (_al_loads)
        ld a, (_al_bank)
        ld (hl), a
        inc hl
        ld a, e
        rrca
        rrca
        and a, #0xC0
        ld b, a
        ld a, (_al_off)
        add a, b
        ld (hl), a
        inc hl
        ;; SRL drops the carry of this add and leaves bit 1 of the id.
        ;; ADC would then add 256 to every id == 2 or 3 (mod 4).
        push af
        ld a, e
        srl a
        srl a
        ld b, a
        pop af
        ld a, (_al_off+1)
        adc a, b
        ld (hl), a
        inc hl
        ld (hl), c
        inc hl
        ld (_al_loads), hl
        ld hl, #_al_n
        inc (hl)
    al_skip:
        pop hl
        jr al_loop
    al_full:
        ld a, #1
        ld (_al_fail), a
        pop hl
        ret
    __endasm;
}

/* Walk only the pose's pieces; the pool keeps at least 38 free while both
 * fighters hold at most current + next (125 of 128, sized). */
static unsigned char allocate(Target *t) {
    unsigned char id;
    if (++gen == 0) {                 /* wrapped: clear stamps once */
        for (id = 0; id < MAP_IDS; id++) seen_gen[id] = 0;
        gen = 1;
    }
    al_meta = target_meta(t);
    al_map = t->map;
    al_loads = t->loads;
    al_bank = t->pt->bank;
    al_off = t->pt->off;
    SMS_saveROMBank();
    SMS_mapROMBank(POSE_META_BANK);
    tl_al[0] = st_vcounter;
    allocate_asm();
    tl_al[1] = st_vcounter;
    tl_al[3] = al_n;
    SMS_restoreROMBank();
    if (al_fail) {                    /* pool short: undo, retry later */
        rl_loads = t->loads;
        rl_n = al_n;
        release_asm();
        stream_alloc_fail++;
        return 0;
    }
    t->nslots = al_n;
    stream_slots_used += al_n;
    if (stream_slots_used > stream_slots_peak) stream_slots_peak = stream_slots_used;
    return 1;
}

void stream_init(void) {
    unsigned char s;
    for (s = 0; s < STREAM_SLOTS; s++) free_stack[s] = (unsigned char)(STREAM_SLOTS - 1u - s);
    free_top = STREAM_SLOTS;
    for (s = 0; s < 2; s++) {
        tgt[s][0].pt = tgt[s][1].pt = 0;
        tgt[s][0].nslots = tgt[s][1].nslots = 0;
        shown_i[s] = 0;
        presenting[s] = 0;
    }
    stream_slots_used = stream_slots_peak = 0;
    stream_alloc_fail = stream_dropped = 0;
}

void stream_request(unsigned char who, const PoseTiles *pt, unsigned char facing,
                    unsigned char pose) {
    Target *n = NEXT(who);
    Target *sh = SHOWN(who);
    if (presenting[who]) return;              /* committed at the SAT copy */
    if (sh->pt == pt && sh->facing == facing) {
        if (n->pt) { release(n); stream_dropped++; }
        return;
    }
    if (n->pt == pt && n->facing == facing) return;
    if (n->pt) { release(n); stream_dropped++; }   /* stale upload never shown */
    n->pt = pt;
    n->facing = facing;
    n->pose = pose;
    load_done[who] = 0;
    if (!allocate(n)) n->pt = 0;
}

unsigned char stream_will_allocate(unsigned char who, const PoseTiles *pt,
                                   unsigned char facing) {
    Target *n = NEXT(who);
    Target *sh = SHOWN(who);
    if (presenting[who]) return 0;
    if (sh->pt == pt && sh->facing == facing) return 0;
    if (n->pt == pt && n->facing == facing) return 0;
    return 1;
}

/* ---- upload loop (assembly; interface through globals) ---- */
static const PairLoad *sa_ptr;
static unsigned char sa_left, sa_done, sa_mode;
/* Active-display streaming stops at this VCounter so logic + render still
 * finish before line 192; set from the measured phase costs. */
unsigned char sa_limit = STREAM_LIMIT_DEFAULT;

static void stream_pairs_asm(void) __naked {
    __asm
        ld hl, (_sa_ptr)
        ld a, (_sa_left)
        ld d, a
        ld e, #0
    sa_next:
        ld a, d
        or a
        jp z, sa_exit
        in a, (0x7e)
        cp #0xC0
        jr nc, sa_vblank
        ld c, a
        ld a, (_sa_limit)
        cp c
        jp c, sa_exit
        jp z, sa_exit
        ld a, #1
        jr sa_go
    sa_vblank:
        cp #0xE0
        jp nc, sa_exit
        xor a
    sa_go:
        ld (_sa_mode), a
        ld a, (hl)
        ld (#0xffff), a
        inc hl
        ld c, (hl)
        inc hl
        ld b, (hl)
        inc hl
        ld a, (hl)
        inc hl
        push hl
        ld h, a
        ld l, #0
        srl h
        rr l
        srl h
        rr l
        di
        ld a, l
        out (0xbf), a
        ld a, h
        or a, #0x40
        out (0xbf), a
        ei
        ld a, b
        add a, #0x80
        ld h, a
        ld l, c
        ld c, #0xbe
        ld b, #64
        ld a, (_sa_mode)
        or a
        jr nz, sa_safe
    sa_fast:
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        outi
        jp nz, sa_fast
        jr sa_after
    sa_safe:
        outi
        nop
        jp nz, sa_safe
    sa_after:
        pop hl
        dec d
        inc e
        jp sa_next
    sa_exit:
        ld a, e
        ld (_sa_done), a
        ld (_sa_ptr), hl
        ret
    __endasm;
}

static void upload(unsigned char who) {
    Target *n = NEXT(who);
    unsigned char left;
    if (!n->pt || reclaim[who]) return;
    left = n->nslots - load_done[who];
    if (!left) return;
    sa_ptr = &n->loads[load_done[who]];
    sa_left = left;
    stream_pairs_asm();
    load_done[who] += sa_done;
}

static unsigned char frame_parity;

void stream_step(void) {
    SMS_saveROMBank();
    /* Alternate who goes first so neither fighter starves. */
    if (frame_parity) { upload(1); upload(0); }
    else              { upload(0); upload(1); }
    frame_parity ^= 1u;
    SMS_restoreROMBank();
}

void stream_load_now(unsigned char who, const PoseTiles *pt, unsigned char facing,
                     unsigned char pose) {
    const unsigned char *src;
    unsigned char i;
    Target *n = NEXT(who);
    if (SHOWN(who)->pt) release(SHOWN(who));
    if (n->pt) release(n);
    n->pt = pt;
    n->facing = facing;
    n->pose = pose;
    if (!allocate(n)) return;
    SMS_saveROMBank();
    for (i = 0; i < n->nslots; i++) {
        SMS_mapROMBank(n->loads[i].bank);
        src = (const unsigned char *)(0x8000u + n->loads[i].off);
        SMS_VRAMmemcpy((unsigned int)n->loads[i].slot * 64u, src, 64u);
    }
    SMS_restoreROMBank();
    load_done[who] = n->nslots;
    presenting[who] = 1;
    stream_sat_copied();
    stream_reclaim();
}

unsigned char stream_shows(unsigned char who, const PoseTiles *pt, unsigned char facing) {
    return SHOWN(who)->pt == pt && SHOWN(who)->facing == facing;
}

unsigned char stream_presenting(void) {
    return (unsigned char)(presenting[0] | presenting[1]);
}

void stream_cancel_present(void) {
    presenting[0] = presenting[1] = 0;
}

/* NEXT is presented only when it is exactly the target the logic wants:
 * a prefetched pose must never appear before its AIR turn. */
unsigned char stream_display(unsigned char who, const PoseTiles *want, unsigned char want_facing,
                             const unsigned char **meta, const unsigned char **map,
                             unsigned char *facing, const unsigned char **rows) {
    const Target *t = SHOWN(who);
    const Target *n = NEXT(who);
    presenting[who] = 0;
    if (!reclaim[who] && n->pt == want && n->facing == want_facing &&
        load_done[who] == n->nslots) {
        t = n;
        presenting[who] = 1;
    }
    *meta = target_meta(t);
    *rows = t->facing ? t->pt->rows_l : t->pt->rows_r;
    *map = t->map;
    *facing = t->facing;
    return t->pose;
}

/* In VBlank: only the index swap. The old SHOWN target (no longer in the
 * SAT) is released later by stream_reclaim(), in CPU time: releasing inside
 * VBlank took the window the fast OUTI uploads need (measured ~35 lines). */
void stream_sat_copied(void) {
    unsigned char who;
    for (who = 0; who < 2; who++) {
        if (!presenting[who]) continue;
        presenting[who] = 0;
        shown_i[who] ^= 1u;                        /* NEXT becomes SHOWN */
        load_done[who] = 0;
        reclaim[who] = 1;                          /* old SHOWN is now NEXT slot */
    }
}

/* Call after stream_step and before the next stream_request. */
void stream_reclaim(void) {
    unsigned char who;
    for (who = 0; who < 2; who++) {
        if (!reclaim[who]) continue;
        reclaim[who] = 0;
        if (NEXT(who)->pt) release(NEXT(who));
    }
}
