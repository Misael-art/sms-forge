/* Scene 02 mapper-backed rendering. Patterns are staged outside the live SAT/PNT. */
#define REP_NO_FRAME 255u
#define REP_NO_SLOT  255u
#define REP_ALIS_IDLE 16u
#define REP_BG_BASE 288u
#ifdef MOF_REPERTOIRE_BG_LIMIT
#define REP_BG_LIMIT MOF_REPERTOIRE_BG_LIMIT
#else
#define REP_BG_LIMIT 25u
#endif
#define REP_BG_BATCH 4u
#define REP_PREFETCH_LIMIT 12u
#define REP_REQUESTS 6u
#define REP_SWAP_UPLOAD_LIMIT 5u
#define REP_SWAP_BUSY_CELLS 12u
#define REP_SWAP_BUSY_LIMIT 2u

typedef struct {
    uint8_t frame[2];
    uint8_t pivot[2];
#if defined(MOF_DUEL_SCENE_POSTURES)
    int8_t alis_y;
#endif
} RepertoireView;

typedef struct {
    const uint8_t *next;
    uint8_t bank, left, remaining;
} RepertoireLayer;

typedef struct {
    const uint8_t *source;
    uint16_t vram_address;
    uint8_t bank, count;
} RepertoireUpload;


#if defined(MOF_DUEL_SCENE_CROSSOVER)
#define REP_FRAME_KEYS (2u * MOF_REPERTOIRE_FRAMES)
#define rep_frames mof_repertoire_frames
static const uint8_t rep_key_mask[8] = {1u, 2u, 4u, 8u, 16u, 32u, 64u, 128u};
static uint8_t rep_protected[(REP_FRAME_KEYS + 7u) / 8u];
static uint8_t rep_side_offset;

static uint8_t rep_logical_frame(uint8_t frame)
{
    return frame >= MOF_REPERTOIRE_FRAMES && frame != REP_NO_FRAME
        ? frame - MOF_REPERTOIRE_FRAMES : frame;
}
#else
#define REP_FRAME_KEYS MOF_REPERTOIRE_FRAMES
#define rep_logical_frame(frame) (frame)
static const MofRepertoireFrame *rep_frames;
static uint8_t rep_protected[REP_FRAME_KEYS];
#endif
static uint8_t rep_owner[256], rep_slot[REP_FRAME_KEYS], rep_loaded[REP_FRAME_KEYS];
static RepertoireView rep_displayed, rep_bg_displayed, rep_bg_target, rep_wanted;
static RepertoireLayer rep_layers[2];
static MofDuelPntCell rep_bg_cells[2][REP_BG_LIMIT];
static uint8_t rep_bg_count[2], rep_bg_page, rep_bg_first, rep_bg_batch;
static uint8_t rep_bg_valid;
#if defined(MOF_DUEL_REPERTOIRE_PRECOMPOSED)
static uint8_t rep_bg_patterns[REP_PREFETCH_LIMIT][32];
#else
static uint8_t rep_bg_patterns[REP_BG_BATCH][32];
#endif
static RepertoireUpload rep_uploads[REP_REQUESTS];
static uint8_t rep_upload_count, rep_upload_groups, rep_publish_sat, rep_publish_bg, rep_visible;
#if defined(MOF_REPERTOIRE_SPRITE_WALK)
static uint8_t rep_sprite_walk_view;
#endif
static uint8_t rep_last_request[REP_REQUESTS], rep_last_display[2], rep_plan_valid;


static const uint8_t *rep_packet(uint8_t frame)
{
    SMS_mapROMBank(rep_frames[frame].bank);
    return (const uint8_t *)rep_frames[frame].address;
}

static const uint8_t *rep_phase(uint8_t frame, uint8_t pivot)
{
    const uint8_t *packet = rep_packet(frame);
    const uint8_t *index = packet + 1u + (pivot & 7u) * 2u;
    return packet + (uint16_t)(index[0] | ((uint16_t)index[1] << 8));
}

static uint8_t rep_equal(const RepertoireView *a, const RepertoireView *b)
{
    return a->frame[0] == b->frame[0] && a->frame[1] == b->frame[1] &&
           a->pivot[0] == b->pivot[0] && a->pivot[1] == b->pivot[1]
#if defined(MOF_DUEL_SCENE_POSTURES)
           && a->alis_y == b->alis_y
#endif
           ;
}

static void rep_empty(RepertoireView *view)
{
    view->frame[0] = view->frame[1] = REP_NO_FRAME;
    view->pivot[0] = view->pivot[1] = 0u;
#if defined(MOF_DUEL_SCENE_POSTURES)
    view->alis_y = 0;
#endif
}

static void rep_init(uint8_t side)
{
    const MofRepertoireAtlas *atlas = &mof_repertoire_atlas[side];
    uint8_t frame, index;
    uint16_t slot;
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    rep_side_offset = side ? MOF_REPERTOIRE_FRAMES : 0u;
#else
    rep_frames = mof_repertoire_frames[side];
#endif
    SMS_mapROMBank(atlas->bank);
    SMS_loadTiles((const uint8_t *)atlas->address, 0u, (uint16_t)atlas->tiles * 32u);
    for (slot = 0u; slot < 256u; ++slot) rep_owner[slot] = REP_NO_FRAME;
    for (frame = 0u; frame < REP_FRAME_KEYS; ++frame) {
        rep_slot[frame] = rep_frames[frame].initial;
        rep_loaded[frame] = 0u;
        if (rep_slot[frame] == REP_NO_SLOT) continue;
        rep_loaded[frame] = rep_frames[frame].count;
        for (index = 0u; index < rep_loaded[frame]; ++index)
            rep_owner[rep_slot[frame] + index] = frame;
    }
    rep_empty(&rep_displayed);
    rep_empty(&rep_bg_displayed);
    rep_empty(&rep_bg_target);
    rep_bg_valid = 0u;
    rep_plan_valid = 0u;
    mof_repertoire_delayed = 0u;
    mof_repertoire_fault = 0u;
}

static void rep_evict(uint8_t frame)
{
    uint8_t i, start = rep_slot[frame];
    for (i = 0u; i < rep_frames[frame].count; ++i)
        rep_owner[start + i] = REP_NO_FRAME;
    rep_slot[frame] = REP_NO_SLOT;
    rep_loaded[frame] = 0u;
}

static void rep_reserve(uint8_t frame)
{
    uint8_t slot = 0u, first = 0u, available = 0u;
    uint8_t owner, span, needed, offset;
    if (frame == REP_NO_FRAME || rep_slot[frame] != REP_NO_SLOT) return;
    needed = rep_frames[frame].count;
    /* Only occupied spans can be skipped. Stop on the wrap at the end of
       the 256-entry sprite table, even if the final span is occupied. */
    do {
        owner = rep_owner[slot];
        span = owner == REP_NO_FRAME ? 1u : rep_frames[owner].count;
        slot += span;
        if (owner != REP_NO_FRAME &&
#if defined(MOF_DUEL_SCENE_CROSSOVER)
            (rep_protected[owner >> 3] & rep_key_mask[owner & 7u])
#else
            rep_protected[owner]
#endif
        ) {
            first = slot;
            available = 0u;
            continue;
        }
        /* Each frame uses at most 32 patterns. available stays below
           needed until this check succeeds, so the sum cannot wrap. */
        available += span;
        if (available < needed) continue;
        for (offset = 0u; offset < needed; ++offset) {
            owner = rep_owner[first + offset];
            if (owner != REP_NO_FRAME) rep_evict(owner);
        }
        for (offset = 0u; offset < needed; ++offset) rep_owner[first + offset] = frame;
        rep_slot[frame] = first;
        return;
    } while (slot);
}

static void rep_protect(uint8_t frame)
{
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    if (frame != REP_NO_FRAME) rep_protected[frame >> 3] |= rep_key_mask[frame & 7u];
#else
    if (frame != REP_NO_FRAME) rep_protected[frame] = 1u;
#endif
}

static void rep_plan_uploads(const uint8_t request[REP_REQUESTS])
{
    uint8_t i, same = rep_plan_valid && rep_last_display[0] == rep_displayed.frame[0] &&
                      rep_last_display[1] == rep_displayed.frame[1];
    for (i = 0u; same && i < REP_REQUESTS; ++i)
        same = request[i] == rep_last_request[i];
    if (same) return;
    /* Existing slots can still need transfers. Protection only enters
       the calculation when a new reservation might evict one of them. */
    for (i = 0u; i < REP_REQUESTS; ++i) {
        if (request[i] != REP_NO_FRAME && rep_slot[request[i]] == REP_NO_SLOT)
            break;
    }
    if (i == REP_REQUESTS) return;
    memcpy(rep_last_request, request, REP_REQUESTS);
    rep_last_display[0] = rep_displayed.frame[0];
    rep_last_display[1] = rep_displayed.frame[1];
    rep_plan_valid = 1u;
    memset(rep_protected, 0, sizeof(rep_protected));
    rep_protect(0u);
    rep_protect(REP_ALIS_IDLE);
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    rep_protect(MOF_REPERTOIRE_FRAMES);
    rep_protect(REP_ALIS_IDLE + MOF_REPERTOIRE_FRAMES);
    /* Keep both sprites for the turn when Alis passes the opponent. */
    rep_protect(MOF_ALIS_POSTURE_START + MOF_ALIS_JUMP_APEX - 1u);
    rep_protect(MOF_ALIS_POSTURE_START + MOF_ALIS_JUMP_APEX - 1u + MOF_REPERTOIRE_FRAMES);
#endif
#ifdef MOF_REPERTOIRE_HAYATO_JAB_START
    /* A quick tap can follow a walk on the very next reading. Keep the
       startup in its boot slot so that window can prefetch the impact. */
    rep_protect(MOF_REPERTOIRE_HAYATO_JAB_START
#if defined(MOF_DUEL_SCENE_CROSSOVER)
                + rep_side_offset
#endif
    );
#endif
#if defined(MOF_DUEL_SCENE_POSTURES)
    /* An unexpected block or a new jump must have its first pose available. */
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    if (!rep_wanted.alis_y && duel.fighters[1u - hayato_player].state != MOF_DUEL_ATTACK)
        rep_protect(MOF_ALIS_POSTURE_START + MOF_ALIS_STAND_GUARD - 1u + rep_side_offset);
    rep_protect(MOF_ALIS_POSTURE_START + MOF_ALIS_CROUCH_TRANSITION - 1u + rep_side_offset);
#else
    rep_protect(MOF_ALIS_POSTURE_START + MOF_ALIS_STAND_GUARD - 1u);
    rep_protect(MOF_ALIS_POSTURE_START + MOF_ALIS_CROUCH_TRANSITION - 1u);
#endif
#endif
    rep_protect(rep_displayed.frame[0]);
    rep_protect(rep_displayed.frame[1]);
    rep_protect(request[0]);
    rep_protect(request[1]);
    /* An old speculative pose cannot pin a span needed by the new
       current view or the next phase. Only protect it at its turn. */
    for (i = 0u; i < REP_REQUESTS; ++i) {
        rep_protect(request[i]);
        rep_reserve(request[i]);
    }
}

static void rep_enqueue(uint8_t frame, uint8_t limit)
{
    RepertoireUpload *upload;
    const MofRepertoireFrame *asset;
    uint8_t pattern, count;
    if (frame == REP_NO_FRAME || rep_slot[frame] == REP_NO_SLOT) return;
    asset = &rep_frames[frame];
    pattern = rep_loaded[frame];
    count = asset->count - pattern;
    if (!count) return;
    if (count > limit) count = limit;
    upload = &rep_uploads[rep_upload_groups++];
    rep_upload_count += count;
    rep_loaded[frame] += count;
    upload->bank = asset->bank;
    upload->count = count;
#if defined(MOF_DUEL_REPERTOIRE_CONTIGUOUS_SPRITES)
    upload->source = (const uint8_t *)asset->address + 17u + asset->count * 2u + (uint16_t)pattern * 32u;
#else
    upload->source = (const uint8_t *)asset->address + 19u + (uint16_t)pattern * 34u;
#endif
    upload->vram_address = (uint16_t)(rep_slot[frame] + pattern) * 32u;
}

static void rep_key(RepertoireView *dst, const RepertoireView *src)
{
    uint8_t i, frame, pivot, has_background;
#if defined(MOF_DUEL_SCENE_POSTURES)
    /* All moving Alis poses are sprite-only. The tilemap key stays on the floor. */
    dst->alis_y = 0;
#endif
    for (i = 0u; i < 2u; ++i) {
        frame = src->frame[i];
        pivot = src->pivot[i];
#ifdef MOF_DUEL_REPERTOIRE_ASSETS
        has_background = rep_frames[frame].p0_kind;
        if (has_background == 2u) has_background = *rep_phase(frame, pivot);
#else
        has_background = (frame != 0u && frame != REP_ALIS_IDLE) && *rep_phase(frame, pivot);
#endif
        if (!has_background) {
            dst->frame[i] = REP_NO_FRAME;
            dst->pivot[i] = 0u;
        } else {
            dst->frame[i] = frame;
            dst->pivot[i] = pivot;
        }
    }
}

static void rep_begin_bg(const RepertoireView *key, uint8_t page)
{
    uint8_t i;
    const uint8_t *phase;
    rep_bg_target = *key;
    rep_bg_valid = 1u;
    rep_bg_count[page] = 0u;
    for (i = 0u; i < 2u; ++i) {
        rep_layers[i].left = key->pivot[i] >> 3;
        rep_layers[i].remaining = 0u;
        if (key->frame[i] == REP_NO_FRAME) continue;
        rep_layers[i].bank = rep_frames[key->frame[i]].bank;
        phase = rep_phase(key->frame[i], key->pivot[i]);
        rep_layers[i].remaining = *phase++;
        rep_layers[i].next = phase;
    }
}

static uint16_t rep_cell(const RepertoireLayer *layer)
{
    int16_t column;
    uint8_t row;
    if (!layer->remaining) return UINT16_MAX;
    SMS_mapROMBank(layer->bank);
    column = layer->left + (int8_t)layer->next[0];
    row = layer->next[1];
    if (column < 0 || column >= 32 || row >= 24u) {
        mof_repertoire_fault = 1u;
        return UINT16_MAX;
    }
    return ((uint16_t)column << 8) | row;
}

static void rep_merge(RepertoireLayer *layer, uint8_t *tile)
{
    const uint8_t *mask, *bits;
    uint8_t row, opaque, transparent;
    SMS_mapROMBank(layer->bank);
    mask = layer->next + 2u;
    bits = layer->next + 10u;
    for (row = 0u; row < 8u; ++row) {
        opaque = *mask++;
        transparent = (uint8_t)~opaque;
        *tile = (*tile & transparent) | (*bits++ & opaque);
        ++tile;
        *tile = (*tile & transparent) | (*bits++ & opaque);
        ++tile;
        *tile = (*tile & transparent) | (*bits++ & opaque);
        ++tile;
        *tile = (*tile & transparent) | (*bits++ & opaque);
        ++tile;
    }
    layer->next += 42u;
    --layer->remaining;
}

#if defined(MOF_DUEL_REPERTOIRE_PRECOMPOSED)
static void rep_copy_layer(RepertoireLayer *layer, uint8_t *tile)
{
    SMS_mapROMBank(layer->bank);
    memcpy(tile, layer->next + 10u, 32u);
    layer->next += 42u;
    --layer->remaining;
}

static void rep_prefetch_single_bg(uint8_t page, RepertoireLayer *layer)
{
    const uint8_t *src = layer->next;
    MofDuelPntCell *cell = rep_bg_cells[page] + rep_bg_count[page];
    uint8_t length = layer->remaining;
    if (length > REP_PREFETCH_LIMIT) length = REP_PREFETCH_LIMIT;
    if (rep_bg_count[page] + length > REP_BG_LIMIT) {
        mof_repertoire_fault = 2u;
        return;
    }
    SMS_mapROMBank(layer->bank);
    for (rep_bg_batch = 0u; rep_bg_batch < length; ++rep_bg_batch) {
        int16_t column = layer->left + (int8_t)src[0];
        uint8_t row = src[1];
        if (column < 0 || column >= 32 || row >= 24u) {
            mof_repertoire_fault = 1u;
            return;
        }
        cell->address = XYtoADDR((uint8_t)column, row);
        cell->backdrop = mof_duel_bg_rows[row];
        memcpy(rep_bg_patterns[rep_bg_batch], src + 10u, 32u);
        src += 42u;
        ++cell;
    }
    layer->next = src;
    layer->remaining -= length;
    rep_bg_count[page] += length;
}
#endif

static void rep_prepare_bg(uint8_t page, uint8_t prefetch_only)
{
    uint16_t hail, alis, key;
    uint8_t *tile;
    MofDuelPntCell *cell;
    rep_bg_first = rep_bg_count[page];
    rep_bg_batch = 0u;
#if defined(MOF_DUEL_REPERTOIRE_PRECOMPOSED)
    /* Keep the displayed view while one precomposed layer uses the transfer budget. */
    if (prefetch_only && ((rep_layers[0].remaining == 0u) != (rep_layers[1].remaining == 0u))) {
        rep_prefetch_single_bg(page, rep_layers[0].remaining ? rep_layers : rep_layers + 1u);
        return;
    }
#else
    (void)prefetch_only;
#endif
    while (rep_bg_batch < REP_BG_BATCH) {
        hail = rep_cell(&rep_layers[0]);
        alis = rep_cell(&rep_layers[1]);
        key = hail < alis ? hail : alis;
        if (key == UINT16_MAX) return;
        if (rep_bg_count[page] == REP_BG_LIMIT) {
            mof_repertoire_fault = 2u;
            return;
        }
        tile = rep_bg_patterns[rep_bg_batch++];
#if defined(MOF_DUEL_REPERTOIRE_PRECOMPOSED)
        if (alis == key) {
            rep_copy_layer(&rep_layers[1], tile);
            if (hail == key) rep_merge(&rep_layers[0], tile);
        } else {
            rep_copy_layer(&rep_layers[0], tile);
        }
#else
        memcpy(tile, mof_duel_bg_stage + (uint16_t)mof_duel_bg_rows[(uint8_t)key] * 32u, 32u);
        if (alis == key) rep_merge(&rep_layers[1], tile);
        if (hail == key) rep_merge(&rep_layers[0], tile);
#endif
        cell = &rep_bg_cells[page][rep_bg_count[page]++];
        cell->address = XYtoADDR(key >> 8, (uint8_t)key);
        cell->backdrop = mof_duel_bg_rows[(uint8_t)key];
    }
}

#if defined(MOF_DUEL_REPERTOIRE_CONTIGUOUS_SPRITES)
static const uint8_t * volatile rep_sat_source;
static uint8_t * volatile rep_sat_y_out, * volatile rep_sat_xt_out;
static volatile uint8_t rep_sat_length, rep_sat_first, rep_sat_origin;

/* Expand the bank's packed XY pairs into the two hardware SAT streams in RAM. */
static void rep_sat_emit(void) __naked
{
    __asm
        push ix
        ld hl, (_rep_sat_source)
        ld de, (_rep_sat_xt_out)
        ld ix, (_rep_sat_y_out)
        ld a, (_rep_sat_length)
        ld b, a
        ld a, (_rep_sat_first)
        ld c, a
    00100$:
        ld a, (_rep_sat_origin)
        add a, (hl)
        inc hl
        ld (de), a
        inc de
        ld a, c
        inc c
        ld (de), a
        inc de
        ld a, (hl)
        inc hl
        dec a
        ld 0 (ix), a
        inc ix
        djnz 00100$
        pop ix
        ret
    __endasm;
}
#endif

static void rep_sat(uint8_t frame, uint8_t x)
{
    uint8_t pattern = rep_slot[frame], count = rep_frames[frame].count;
    const uint8_t *data = rep_packet(frame) + 17u;
    uint8_t *y = sat_y + sat_count;
    uint8_t *xt = sat_xt + (uint16_t)sat_count * 2u;
    sat_count += count;
#if defined(MOF_DUEL_REPERTOIRE_CONTIGUOUS_SPRITES)
    rep_sat_source = data;
    rep_sat_y_out = y;
    rep_sat_xt_out = xt;
    rep_sat_length = count;
    rep_sat_first = pattern;
    rep_sat_origin = x;
    rep_sat_emit();
#else
    while (count--) {
        *xt++ = x + data[0];
        *y++ = data[1] - 1u;
        *xt++ = pattern++;
        data += 34u;
    }
#endif
}

static void rep_build_sat(const RepertoireView *wanted)
{
#ifdef MOF_DUEL_REPERTOIRE_ASSETS
    uint8_t first, second, delta, i;
    uint8_t *x;
    if (rep_visible && rep_displayed.frame[0] == wanted->frame[0] &&
        rep_displayed.frame[1] == wanted->frame[1]) {
        /* Published frames are protected from eviction. Translation alone
           keeps the Y entries and pattern slots from the previous SAT. */
        first = rep_frames[wanted->frame[0]].count;
        second = rep_frames[wanted->frame[1]].count;
        delta = wanted->pivot[0] - rep_displayed.pivot[0];
#if defined(MOF_DUEL_SCENE_CROSSOVER)
        sat_xt_first = delta ? 0u : 2u * first;
        sat_xt_dirty = delta != 0u;
#endif
        if (delta)
            for (i = first, x = sat_xt; i; --i, x += 2u) *x += delta;
        delta = wanted->pivot[1] - rep_displayed.pivot[1];
#if defined(MOF_DUEL_SCENE_CROSSOVER)
        if (delta) sat_xt_dirty = 1u;
#endif
        if (delta)
            for (i = second, x = sat_xt + 2u * first; i; --i, x += 2u) *x += delta;
        sat_y_dirty = 0u;
#if defined(MOF_DUEL_SCENE_POSTURES)
        delta = (uint8_t)(wanted->alis_y - rep_displayed.alis_y);
        if (delta) {
            for (i = second, x = sat_y + first; i; --i) *x++ += delta;
            sat_y_dirty = 1u;
#if defined(MOF_DUEL_SCENE_CROSSOVER)
            sat_y_first = first;
#endif
        }
#endif
        rep_publish_sat = 1u;
        mof_render_stage_lines[3] = SMS_getVCount();
        return;
    }
    sat_y_dirty = 1u;
#endif
#if defined(MOF_DUEL_SCENE_CROSSOVER)
    sat_y_first = sat_xt_first = 0u;
    sat_xt_dirty = 1u;
#endif
    sat_count = 0u;
    rep_sat(wanted->frame[0], wanted->pivot[0]);
    rep_sat(wanted->frame[1], wanted->pivot[1]);
#if defined(MOF_DUEL_SCENE_POSTURES)
    if (wanted->alis_y) {
        uint8_t index = rep_frames[wanted->frame[0]].count;
        for (; index < sat_count; ++index) sat_y[index] += (uint8_t)wanted->alis_y;
    }
#endif
    if (sat_count < 64u) sat_y[sat_count] = 0xD0u;
    rep_publish_sat = 1u;
    mof_render_stage_lines[3] = SMS_getVCount();
}

static uint8_t rep_ready(const RepertoireView *view)
{
    return rep_loaded[view->frame[0]] == rep_frames[view->frame[0]].count &&
           rep_loaded[view->frame[1]] == rep_frames[view->frame[1]].count;
}

static uint8_t rep_missing(const RepertoireView *view)
{
    uint8_t first = view->frame[0], second = view->frame[1];
    return rep_frames[first].count - rep_loaded[first] +
           rep_frames[second].count - rep_loaded[second];
}

static void rep_prepare(const RepertoireView *wanted, const RepertoireView *forecast,
                        const RepertoireView *later, const uint8_t planned[4], uint8_t views_changed)
{
    RepertoireView key, next, after;
    uint8_t i, page = rep_bg_page ^ 1u;
    uint8_t request[REP_REQUESTS], done_after_bg, unchanged, allowance, swap_limit;
    const RepertoireView *job;
#if defined(MOF_DUEL_SCENE_POSTURES)
    uint8_t air_translation;
#endif
    uint8_t quiet = !views_changed && rep_visible && !rep_publish_sat &&
                    !rep_publish_bg && !rep_upload_count && !rep_bg_batch;
    rep_wanted = *wanted;
    rep_publish_bg = rep_publish_sat = 0u;
    rep_upload_count = rep_upload_groups = 0u;
    rep_bg_batch = 0u;
    mof_render_stage_lines[1] = mof_render_stage_lines[2] = mof_render_stage_lines[3] =
        mof_render_stage_lines[0];
    if (quiet) return;
    unchanged = rep_visible && rep_equal(wanted, &rep_displayed);
#if defined(MOF_DUEL_SCENE_POSTURES)
    air_translation = rep_visible && (wanted->alis_y || rep_displayed.alis_y) &&
        (wanted->alis_y != rep_displayed.alis_y || wanted->pivot[1] != rep_displayed.pivot[1]) &&
        !rep_frames[rep_displayed.frame[1]].p0_kind && !rep_frames[wanted->frame[1]].p0_kind;
#endif
    if (unchanged && planned[0] == REP_NO_FRAME && planned[1] == REP_NO_FRAME) return;
    if (planned[0] == REP_NO_FRAME && planned[1] == REP_NO_FRAME &&
        rep_logical_frame(wanted->frame[0]) == 0u &&
        rep_logical_frame(wanted->frame[1]) == REP_ALIS_IDLE &&
        rep_bg_displayed.frame[0] == REP_NO_FRAME && rep_bg_displayed.frame[1] == REP_NO_FRAME) {
        rep_build_sat(wanted);
        return;
    }
    done_after_bg = 1u;
#if defined(MOF_REPERTOIRE_SPRITE_WALK)
    if (!rep_sprite_walk_view || rep_bg_displayed.frame[0] != REP_NO_FRAME ||
        rep_bg_displayed.frame[1] != REP_NO_FRAME)
#endif
    {
        rep_key(&key, wanted);
        rep_key(&next, forecast);
        done_after_bg = rep_equal(&key, &rep_bg_displayed);
        job = done_after_bg ? &next : &key;
        if (done_after_bg && rep_equal(&key, &next)) {
            rep_key(&after, later);
            job = &after;
        }
        if (!rep_bg_valid || !rep_equal(job, &rep_bg_target)) rep_begin_bg(job, page);
        rep_prepare_bg(page, unchanged && done_after_bg);
        mof_render_stage_lines[1] = SMS_getVCount();
        if (!done_after_bg && !rep_layers[0].remaining && !rep_layers[1].remaining && !mof_repertoire_fault)
            done_after_bg = 2u;
    }

    request[0] = wanted->frame[0];
    request[1] = wanted->frame[1];
    memcpy(request + 2u, planned, 4u);
    rep_plan_uploads(request);
    swap_limit = REP_SWAP_UPLOAD_LIMIT;
    if (done_after_bg == 2u && rep_bg_count[page] + rep_bg_count[rep_bg_page] > REP_SWAP_BUSY_CELLS)
        swap_limit = REP_SWAP_BUSY_LIMIT;
    /* Reserve the smaller budget only when this blank can publish the view.
       Loading speculative poses must not crowd out an already feasible swap. */
    allowance = REP_PREFETCH_LIMIT;
    if (!unchanged && done_after_bg && rep_missing(wanted) + rep_bg_batch <= swap_limit)
        allowance = swap_limit;
#if defined(MOF_DUEL_SCENE_POSTURES)
    else if (air_translation && rep_bg_batch <= REP_SWAP_UPLOAD_LIMIT)
        allowance = REP_SWAP_UPLOAD_LIMIT;
#endif
    allowance = allowance > rep_bg_batch ? allowance - rep_bg_batch : 0u;
    for (i = 0u; i < REP_REQUESTS && rep_upload_count < allowance; ++i)
        rep_enqueue(request[i], allowance - rep_upload_count);
    mof_render_stage_lines[2] = SMS_getVCount();
    if (!unchanged && done_after_bg && rep_ready(wanted) &&
        rep_upload_count + rep_bg_batch <= swap_limit) {
        rep_build_sat(wanted);
        rep_publish_bg = done_after_bg == 2u;
        return;
    }
#if defined(MOF_DUEL_SCENE_POSTURES)
    /* Alis may translate with the last published opponent while his next
       tilemap page is loading. Keep that page and its matching sprites. */
    if (air_translation && rep_upload_count + rep_bg_batch <= REP_SWAP_UPLOAD_LIMIT) {
        rep_wanted = rep_displayed;
        if (rep_loaded[wanted->frame[1]] == rep_frames[wanted->frame[1]].count)
            rep_wanted.frame[1] = wanted->frame[1];
        rep_wanted.pivot[1] = wanted->pivot[1];
        rep_wanted.alis_y = wanted->alis_y;
        rep_build_sat(&rep_wanted);
        if (!rep_equal(wanted, &rep_wanted)) ++mof_repertoire_delayed;
    }
#endif
}

static void rep_publish(void)
{
    uint8_t i, page = rep_bg_page ^ 1u;
    uint16_t tile_base = REP_BG_BASE + page * REP_BG_LIMIT;
    const RepertoireUpload *upload = rep_uploads;
    mof_vblank_payload[0] = rep_upload_count;
    mof_vblank_payload[1] = rep_bg_batch;
    mof_vblank_payload[2] = rep_publish_sat ? sat_count : 0u;
    mof_vblank_payload[3] = rep_publish_bg ? rep_bg_count[rep_bg_page] + rep_bg_count[page] : 0u;
    for (i = 0u; i < rep_upload_groups; ++i) {
        SMS_mapROMBank(upload->bank);
#if defined(MOF_DUEL_REPERTOIRE_CONTIGUOUS_SPRITES)
        UNSAFE_SMS_VRAMmemcpy(upload->vram_address, upload->source, (uint16_t)upload->count * 32u);
#else
        {
            const uint8_t *source = upload->source;
            uint16_t address = upload->vram_address;
            uint8_t count = upload->count;
            while (count--) {
                UNSAFE_SMS_VRAMmemcpy32(address, source);
                address += 32u;
                source += 34u;
            }
        }
#endif
        ++upload;
    }
    if (rep_bg_batch)
        UNSAFE_SMS_loadNTiles(rep_bg_patterns, tile_base + rep_bg_first, rep_bg_batch);
    if (!rep_publish_sat) {
        if (!rep_visible || !rep_equal(&rep_wanted, &rep_displayed)) ++mof_repertoire_delayed;
        return;
    }
    if (rep_publish_bg) {
        if (rep_bg_count[rep_bg_page]) {
            rep_pnt_stream = rep_bg_cells[rep_bg_page];
            rep_pnt_length = rep_bg_count[rep_bg_page];
            rep_pnt_first = 0u;
            rep_send_pnt();
        }
        if (rep_bg_count[page]) {
            rep_pnt_stream = rep_bg_cells[page];
            rep_pnt_length = rep_bg_count[page];
            rep_pnt_first = (uint8_t)tile_base;
            rep_send_pnt();
        }
        rep_bg_page = page;
        rep_bg_displayed = rep_bg_target;
        rep_bg_valid = 0u;
        rep_empty(&rep_bg_target);
        rep_layers[0].remaining = rep_layers[1].remaining = 0u;
    }
    copy_sat();
    rep_displayed = rep_wanted;
    rep_visible = 1u;
}
