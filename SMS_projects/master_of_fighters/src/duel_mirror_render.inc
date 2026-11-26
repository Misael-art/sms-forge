/* Each control owns four 32-pattern slots. A displayed slot stays pinned
   until the next SAT is sent. Bank packets use the Scene 02 XY/tiles/P0 ABI. */
#define MIRROR_EMPTY 255u
#define MIRROR_SLOT_COUNT 4u
#define MIRROR_BG_BASE 288u
#define MIRROR_UPLOAD_BUDGET 8u
#if defined(MOF_ALIS_CHAPTER)
#define MIRROR_PRELOAD_BUDGET 10u
#else
#define MIRROR_PRELOAD_BUDGET 14u
#endif

typedef struct {
    uint8_t frame, x;
    int8_t y;
} MirrorView;

typedef struct {
    uint8_t key, loaded;
} MirrorSlot;
typedef char MirrorSlotLayout[sizeof(MirrorSlot) == 2u && MIRROR_SLOT_COUNT == 4u ? 1 : -1];

typedef struct {
    const uint8_t *source;
    uint8_t bank, tile, count;
} MirrorUpload;

static MirrorSlot mirror_cache[2][MIRROR_SLOT_COUNT];
static MirrorView mirror_display[2], mirror_submit[2];
static uint8_t mirror_live_slot[2], mirror_submit_slot[2];
static MirrorUpload mirror_uploads[8];
static uint8_t mirror_upload_count, mirror_upload_tiles, mirror_sat_dirty;
static uint8_t mirror_sat_y_first, mirror_sat_y_count, mirror_sat_xt_first, mirror_sat_xt_count;
static MofDuelPntCell mirror_cells[2][MOF_MIRROR_SPILL];
static MofDuelPntCell *mirror_stage_cells;
static uint8_t mirror_bg_tiles[MOF_MIRROR_SPILL * 32u];
static uint8_t mirror_bg_count, mirror_old_bg_count, mirror_bg_dirty;
static uint8_t mirror_bg_page, mirror_bg_loaded, mirror_bg_batch;
static uint8_t mirror_bg_frame[2], mirror_bg_x[2];
static uint8_t mirror_bg_active_frame[2], mirror_bg_active_x[2];

static const uint8_t *mirror_packet(const MofMirrorFrame *frame, uint8_t player)
{
    SMS_mapROMBank(frame->bank + (player ? MOF_MIRROR_COSTUME_BANKS : 0u));
    return (const uint8_t *)frame->address;
}

/* SDCC Z80 passes the owner in A and the key in L. Read the four keys
   without rescanning the slot table or allocating an IX frame. */
static uint8_t mirror_find_slot(uint8_t player, uint8_t key) __naked
{
    player; key;
    __asm
        ld c, l
        inc l
        jr z, mirror_slot_missing
        ld hl, #_mirror_cache
        or a
        jr z, mirror_slot_compare
        ld de, #8
        add hl, de
    mirror_slot_compare:
        ld b, #4
    mirror_slot_next:
        ld a, (hl)
        cp c
        jr z, mirror_slot_found
        inc hl
        inc hl
        djnz mirror_slot_next
    mirror_slot_missing:
        ld a, #255
        ret
    mirror_slot_found:
        ld a, #4
        sub b
        ret
    __endasm;
}

static uint8_t mirror_warm(uint8_t player, uint8_t key)
{
    uint8_t slot;
    if (key == MIRROR_EMPTY) return 1u;
    slot = mirror_find_slot(player, key);
    return slot != MIRROR_EMPTY && mirror_cache[player][slot].loaded == mirror_frames[key].count;
}

static uint8_t mirror_request(uint8_t player, uint8_t key, uint8_t *pinned, uint8_t room)
{
    const MofMirrorFrame *frame;
    MirrorSlot *cache;
    MirrorUpload *upload;
    uint8_t slot, count;
    if (key == MIRROR_EMPTY) return MIRROR_EMPTY;
    slot = mirror_find_slot(player, key);
    if (slot == MIRROR_EMPTY) {
        if (room == mirror_upload_tiles) return MIRROR_EMPTY;
        for (slot = 0u; slot < MIRROR_SLOT_COUNT; ++slot)
            if (!(*pinned & (1u << slot))) break;
        if (slot == MIRROR_SLOT_COUNT) return MIRROR_EMPTY;
        mirror_cache[player][slot].key = key;
        mirror_cache[player][slot].loaded = 0u;
    }
    *pinned |= 1u << slot;
    frame = &mirror_frames[key];
    cache = &mirror_cache[player][slot];
    if (cache->loaded == frame->count) return slot;
    count = frame->count - cache->loaded;
    if (count > room - mirror_upload_tiles) count = room - mirror_upload_tiles;
    if (count) {
        upload = &mirror_uploads[mirror_upload_count++];
        upload->source = (const uint8_t *)frame->address + 17u +
            2u * frame->count + (uint16_t)cache->loaded * 32u;
        upload->bank = frame->bank + (player ? MOF_MIRROR_COSTUME_BANKS : 0u);
        upload->tile = player * 128u + slot * 32u + cache->loaded;
        upload->count = count;
        cache->loaded += count;
        mirror_upload_tiles += count;
    }
    return cache->loaded == frame->count ? slot : MIRROR_EMPTY;
}

static const uint8_t * volatile mirror_xy;
static uint8_t * volatile mirror_y_out, * volatile mirror_xt_out;
static volatile uint8_t mirror_sat_length, mirror_sat_tile, mirror_sat_x, mirror_sat_y;

static void mirror_emit_sat(void) __naked
{
    __asm
        push ix
        ld hl, (_mirror_xy)
        ld de, (_mirror_xt_out)
        ld ix, (_mirror_y_out)
        ld a, (_mirror_sat_length)
        ld b, a
        ld a, (_mirror_sat_tile)
        ld c, a
    00980$:
        ld a, (_mirror_sat_x)
        add a, (hl)
        inc hl
        ld (de), a
        inc de
        ld a, c
        inc c
        ld (de), a
        inc de
        ld a, (_mirror_sat_y)
        add a, (hl)
        inc hl
        dec a
        ld 0 (ix), a
        inc ix
        djnz 00980$
        pop ix
        ret
    __endasm;
}

static void mirror_build_sat(void)
{
    uint8_t player;
    sat_count = 0u;
    for (player = 0u; player < 2u; ++player) {
        const MirrorView *view = &mirror_submit[player];
        const MofMirrorFrame *frame = &mirror_frames[view->frame];
        mirror_xy = mirror_packet(frame, 0u) + 17u;
        mirror_xt_out = sat_xt + sat_count * 2u;
        mirror_y_out = sat_y + sat_count;
        mirror_sat_length = frame->count;
        mirror_sat_tile = player * 128u + mirror_submit_slot[player] * 32u;
        mirror_sat_x = view->x;
        mirror_sat_y = (uint8_t)view->y;
        mirror_emit_sat();
        sat_count += frame->count;
    }
    if (sat_count < 64u) sat_y[sat_count] = 0xD0u;
    mirror_sat_y_first = mirror_sat_xt_first = 0u;
    mirror_sat_y_count = sat_count + (sat_count < 64u);
    mirror_sat_xt_count = sat_count * 2u;
}

static uint8_t * volatile mirror_shift_cells;
static volatile uint8_t mirror_shift_step, mirror_shift_delta;

static void mirror_shift_sat(void) __naked
{
    __asm
        ld hl, (_mirror_shift_cells)
        ld a, (_mirror_shift_step)
        ld e, a
        ld d, #0
        ld a, (_mirror_shift_delta)
        ld c, a
        ld a, (_mirror_sat_length)
        ld b, a
    mirror_shift_loop:
        ld a, (hl)
        add a, c
        ld (hl), a
        add hl, de
        djnz mirror_shift_loop
        ret
    __endasm;
}

static void mirror_translate_sat(void)
{
    uint8_t player, first, count, delta;
    uint8_t end_y = 0u, end_xt = 0u;
    mirror_sat_y_first = mirror_sat_xt_first = MIRROR_EMPTY;
    first = 0u;
    for (player = 0u; player < 2u; ++player) {
        count = mirror_frames[mirror_submit[player].frame].count;
        delta = (uint8_t)(mirror_submit[player].y - mirror_display[player].y);
        if (delta) {
            if (mirror_sat_y_first == MIRROR_EMPTY) mirror_sat_y_first = first;
            end_y = first + count;
            mirror_shift_cells = sat_y + first;
            mirror_shift_step = 1u;
            mirror_shift_delta = delta;
            mirror_sat_length = count;
            mirror_shift_sat();
        }
        delta = mirror_submit[player].x - mirror_display[player].x;
        if (delta) {
            if (mirror_sat_xt_first == MIRROR_EMPTY) mirror_sat_xt_first = first * 2u;
            end_xt = (first + count) * 2u;
            mirror_shift_cells = sat_xt + first * 2u;
            mirror_shift_step = 2u;
            mirror_shift_delta = delta;
            mirror_sat_length = count;
            mirror_shift_sat();
        }
        first += count;
    }
    mirror_sat_y_count = end_y ? end_y - mirror_sat_y_first : 0u;
    mirror_sat_xt_count = end_xt ? end_xt - mirror_sat_xt_first : 0u;
}

static void mirror_add_background(const MirrorView *view, uint8_t player)
{
    const MofMirrorFrame *frame = &mirror_frames[view->frame];
    const uint8_t *packet, *phase;
    uint8_t cells, index, i, mask;
    uint16_t cell;
    int16_t column;
    uint8_t *tile;
    if (!frame->spill) return;
    packet = mirror_packet(frame, player);
    phase = packet + 1u + (view->x & 7u) * 2u;
    phase = packet + (phase[0] | ((uint16_t)phase[1] << 8));
    cells = *phase++;
    while (cells--) {
        column = (view->x >> 3) + (int8_t)phase[0];
        if (column < 0 || column >= 32 || phase[1] >= 24u) {
            mof_repertoire_fault = 1u;
            return;
        }
        cell = XYtoADDR(column, phase[1]);
        for (index = 0u; index < mirror_bg_count; ++index)
            if (mirror_stage_cells[index].address == cell) break;
        if (index >= MOF_MIRROR_SPILL) {
            mof_repertoire_fault = 1u;
            return;
        }
        tile = mirror_bg_tiles + index * 32u;
        if (index == mirror_bg_count) {
            mirror_stage_cells[index].address = cell;
            mirror_stage_cells[index].backdrop = mof_duel_bg_rows[phase[1]];
            memcpy(tile, phase + 10u, 32u);
            ++mirror_bg_count;
        } else {
            for (i = 0u; i < 32u; ++i) {
                mask = phase[2u + (i >> 2)];
                tile[i] = (tile[i] & (uint8_t)~mask) | (phase[10u + i] & mask);
            }
        }
        phase += 42u;
    }
}

/* An already armed airborne strike gets its next pose before speculative
   poses. Keep the usual priority when two attacks are active together. */
static uint8_t mirror_air_priority(const MirrorView wanted[2])
{
    uint8_t a = (wanted[0].frame >> 1) - MOF_MIRROR_AIR_0_1;
    uint8_t b = (wanted[1].frame >> 1) - MOF_MIRROR_AIR_0_1;
    if (a < 12u && b >= 12u) return 0u;
    if (b < 12u && a >= 12u) return 1u;
    return MIRROR_EMPTY;
}

static void mirror_prepare(const MirrorView wanted[2], const uint8_t next[2], const uint8_t later[2])
{
    MirrorView background[2];
    uint8_t player, order, pinned[2], slot, has_spill, new_background, actual_change = 0u;
    uint8_t priority = mirror_air_priority(wanted);
    uint8_t first = priority == MIRROR_EMPTY ? duel.tick & 1u : priority;
    uint8_t key[2], x[2];
    mirror_sat_dirty = mirror_bg_dirty = mirror_bg_batch = mirror_upload_count = mirror_upload_tiles = 0u;
    has_spill = mirror_old_bg_count ||
        mirror_frames[wanted[0].frame].spill || mirror_frames[wanted[1].frame].spill;
    if (!has_spill && wanted[0].frame == mirror_display[0].frame &&
        wanted[1].frame == mirror_display[1].frame &&
        mirror_warm(0u, next[0]) && mirror_warm(1u, next[1]) &&
        mirror_warm(0u, later[0]) && mirror_warm(1u, later[1]) &&
        (next[0] == MIRROR_EMPTY || !mirror_frames[next[0]].spill) &&
        (next[1] == MIRROR_EMPTY || !mirror_frames[next[1]].spill) &&
        (later[0] == MIRROR_EMPTY || !mirror_frames[later[0]].spill) &&
        (later[1] == MIRROR_EMPTY || !mirror_frames[later[1]].spill)) {
        if (wanted[0].x != mirror_display[0].x || wanted[1].x != mirror_display[1].x ||
            wanted[0].y != mirror_display[0].y || wanted[1].y != mirror_display[1].y) {
            mirror_submit[0] = wanted[0];
            mirror_submit[1] = wanted[1];
            mirror_submit_slot[0] = mirror_live_slot[0];
            mirror_submit_slot[1] = mirror_live_slot[1];
            mirror_translate_sat();
            mirror_sat_dirty = 1u;
        }
        return;
    }
    for (order = 0u; order < 2u; ++order) {
        player = first ^ order;
        pinned[player] = 1u << mirror_live_slot[player];
        slot = mirror_find_slot(player, next[player]);
        if (slot != MIRROR_EMPTY) pinned[player] |= 1u << slot;
        slot = mirror_find_slot(player, later[player]);
        if (slot != MIRROR_EMPTY) pinned[player] |= 1u << slot;
        slot = mirror_request(player, wanted[player].frame, &pinned[player], MIRROR_UPLOAD_BUDGET);
        mirror_submit[player] = wanted[player];
        mirror_submit_slot[player] = slot;
        if (slot != MIRROR_EMPTY && player == priority && duel.tested_pose[player] < 2u &&
            wanted[player].y &&
            next[player] != MIRROR_EMPTY && !mirror_frames[next[player]].spill)
            mirror_request(player, next[player], &pinned[player], MIRROR_UPLOAD_BUDGET);
        if (slot == MIRROR_EMPTY) {
            mirror_submit[player].frame = mirror_display[player].frame;
            mirror_submit_slot[player] = mirror_live_slot[player];
            if (mirror_submit[player].y && mirror_frames[mirror_submit[player].frame].spill)
                mirror_submit[player] = mirror_display[player];
            ++mof_repertoire_delayed;
        }
        if (mirror_display[player].frame != mirror_submit[player].frame ||
            mirror_display[player].x != mirror_submit[player].x ||
            mirror_display[player].y != mirror_submit[player].y)
            mirror_sat_dirty = 1u;
    }
    slot = mirror_sat_dirty ? MIRROR_UPLOAD_BUDGET : MIRROR_PRELOAD_BUDGET;
    if (has_spill || (next[0] != MIRROR_EMPTY && mirror_frames[next[0]].spill) ||
                     (next[1] != MIRROR_EMPTY && mirror_frames[next[1]].spill) ||
                     (later[0] != MIRROR_EMPTY && mirror_frames[later[0]].spill) ||
                     (later[1] != MIRROR_EMPTY && mirror_frames[later[1]].spill)) {
        for (player = 0u; player < 2u; ++player) {
            background[player] = mirror_submit[player];
            key[player] = mirror_frames[background[player].frame].spill ?
                background[player].frame : MIRROR_EMPTY;
            x[player] = key[player] == MIRROR_EMPTY ? 0u : background[player].x;
            if (mirror_bg_active_frame[player] != key[player] || mirror_bg_active_x[player] != x[player])
                actual_change = 1u;
        }
        if (!actual_change) {
            /* Warm the inactive page during the anticipation of a wide
               strike. Keep the current PNT intact until that strike shows. */
            for (player = 0u; player < 2u; ++player) {
                uint8_t upcoming = wanted[player].frame;
                if (upcoming == mirror_submit[player].frame || !mirror_frames[upcoming].spill) {
                    upcoming = next[player];
                    if (upcoming == MIRROR_EMPTY || !mirror_frames[upcoming].spill)
                        upcoming = later[player];
                    if (upcoming == MIRROR_EMPTY || !mirror_frames[upcoming].spill)
                        continue;
                }
                background[player].frame = key[player] = upcoming;
                background[player].x = x[player] = wanted[player].x;
            }
        }
        new_background = 0u;
        for (player = 0u; player < 2u; ++player) {
            if (mirror_bg_frame[player] != key[player] || mirror_bg_x[player] != x[player])
                new_background = 1u;
            mirror_bg_frame[player] = key[player];
            mirror_bg_x[player] = x[player];
        }
        if (new_background) {
            mirror_bg_count = 0u;
            mirror_bg_loaded = 0u;
            /* Draw the back sprite's spill first. P1 retains SAT priority. */
            mirror_add_background(&background[1], 1u);
            mirror_add_background(&background[0], 0u);
        }
        mirror_bg_batch = mirror_bg_count - mirror_bg_loaded;
        if (mirror_bg_batch > slot - mirror_upload_tiles)
            mirror_bg_batch = slot - mirror_upload_tiles;
        if (actual_change) {
            /* A PNT swap also restores the old entries and moves the SAT.
               Fill the inactive page first when that work shares a large upload. */
            if (mirror_bg_loaded + mirror_bg_batch < mirror_bg_count ||
                mirror_upload_tiles + mirror_bg_batch > 4u) {
                mirror_sat_dirty = 0u;
                ++mof_repertoire_delayed;
            } else {
                mirror_bg_dirty = 1u;
            }
        }
        slot -= mirror_bg_batch;
    }
    if (mirror_sat_dirty) {
        if (mirror_display[0].frame == mirror_submit[0].frame &&
            mirror_display[1].frame == mirror_submit[1].frame) mirror_translate_sat();
        else mirror_build_sat();
    }
    if (mirror_bg_dirty) return;
    if (!mirror_sat_dirty) {
        /* A transfer-only VBlank can fill more of the inactive slots
           and page. Finish the demanded pair before looking ahead. */
        slot = MIRROR_PRELOAD_BUDGET - mirror_bg_batch;
        for (order = 0u; order < 2u; ++order) {
            player = first ^ order;
            if (mirror_submit[player].frame != wanted[player].frame)
                mirror_request(player, wanted[player].frame, &pinned[player], slot);
        }
    }
    for (order = 0u; order < 2u; ++order) {
        player = first ^ order;
        mirror_request(player, next[player], &pinned[player], slot);
    }
    for (order = 0u; order < 2u; ++order) {
        player = first ^ order;
        mirror_request(player, later[player], &pinned[player], slot);
    }
}

static void mirror_publish(void)
{
    uint8_t i;
    uint16_t bg_base = MIRROR_BG_BASE + (mirror_bg_page ? 0u : MOF_MIRROR_SPILL);
    mof_vblank_payload[0] = mirror_upload_tiles;
    mof_vblank_payload[1] = mirror_bg_batch;
    mof_vblank_payload[2] = mirror_sat_dirty ? mirror_sat_y_count + mirror_sat_xt_count : 0u;
    mof_vblank_payload[3] = mirror_bg_dirty ? mirror_old_bg_count + mirror_bg_count : 0u;
    for (i = 0u; i < mirror_upload_count; ++i) {
        const MirrorUpload *upload = &mirror_uploads[i];
        SMS_mapROMBank(upload->bank);
        UNSAFE_SMS_loadNTiles(upload->source, upload->tile, upload->count);
    }
    if (mirror_bg_batch) {
        UNSAFE_SMS_loadNTiles(mirror_bg_tiles + (uint16_t)mirror_bg_loaded * 32u,
                              bg_base + mirror_bg_loaded, mirror_bg_batch);
        mirror_bg_loaded += mirror_bg_batch;
    }
    if (mirror_bg_dirty) {
        if (mirror_old_bg_count) {
            rep_pnt_stream = mirror_cells[mirror_bg_page];
            rep_pnt_length = mirror_old_bg_count;
            rep_pnt_first = 0u;
            rep_send_pnt();
        }
        if (mirror_bg_count) {
            rep_pnt_stream = mirror_stage_cells;
            rep_pnt_length = mirror_bg_count;
            rep_pnt_first = (uint8_t)bg_base;
            rep_send_pnt();
        }
        mirror_old_bg_count = mirror_bg_count;
        mirror_stage_cells = mirror_cells[mirror_bg_page];
        mirror_bg_page ^= 1u;
        mirror_bg_active_frame[0] = mirror_bg_frame[0];
        mirror_bg_active_frame[1] = mirror_bg_frame[1];
        mirror_bg_active_x[0] = mirror_bg_x[0];
        mirror_bg_active_x[1] = mirror_bg_x[1];
    }
    if (mirror_sat_dirty) {
        if (mirror_sat_y_count)
            UNSAFE_SMS_VRAMmemcpy(DUEL_SAT_Y_ADDRESS + mirror_sat_y_first,
                                  sat_y + mirror_sat_y_first, mirror_sat_y_count);
        if (mirror_sat_xt_count)
            UNSAFE_SMS_VRAMmemcpy(DUEL_SAT_XT_ADDRESS + mirror_sat_xt_first,
                                  sat_xt + mirror_sat_xt_first, mirror_sat_xt_count);
        for (i = 0u; i < 2u; ++i) {
            mirror_display[i] = mirror_submit[i];
            mirror_live_slot[i] = mirror_submit_slot[i];
        }
    }
}

static void mirror_render_boot(void)
{
    uint8_t player, slot;
    for (player = 0u; player < 2u; ++player) {
        uint8_t face = duel.fighters[player].face_right;
        uint8_t startup[4] = {face, face ^ 1u, MOF_MIRROR_ALIS_CROUCH_TRANSITION * 2u + face,
                              MOF_MIRROR_HIT_HEAD * 2u + face};
        for (slot = 0u; slot < MIRROR_SLOT_COUNT; ++slot) {
            const MofMirrorFrame *frame = &mirror_frames[startup[slot]];
            const uint8_t *packet = mirror_packet(frame, player);
            SMS_loadTiles(packet + 17u + frame->count * 2u,
                          player * 128u + slot * 32u, frame->count * 32u);
            mirror_cache[player][slot].key = startup[slot];
            mirror_cache[player][slot].loaded = frame->count;
        }
        mirror_submit[player].frame = face;
        mirror_submit[player].x = (uint8_t)duel.fighters[player].x;
        mirror_submit[player].y = 0;
        mirror_submit_slot[player] = 0u;
    }
    mirror_old_bg_count = mirror_bg_count = mirror_bg_dirty = mirror_upload_count = 0u;
    mirror_bg_page = mirror_bg_batch = mirror_bg_loaded = 0u;
    mirror_stage_cells = mirror_cells[1];
    mirror_bg_frame[0] = mirror_bg_frame[1] = MIRROR_EMPTY;
    mirror_bg_x[0] = mirror_bg_x[1] = 0u;
    mirror_bg_active_frame[0] = mirror_bg_active_frame[1] = MIRROR_EMPTY;
    mirror_bg_active_x[0] = mirror_bg_active_x[1] = 0u;
    mirror_sat_dirty = 1u;
    mirror_build_sat();
    mirror_publish();
}
