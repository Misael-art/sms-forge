/* Compact per-facing pose upload into a shared 128-pair SMS sprite pool.
 * Current patterns stay resident until a replacement is completely uploaded.
 * The allocator assigns individual tall pairs, so holes do not prevent a
 * transition when enough total pairs remain. If two replacements cannot both
 * fit, fight_render_changed retries the second after the first commits. */
#include "SMSlib.h"
#include "stream.h"

#define CHUNK STREAM_CHUNK_BYTES
#define PAIR_CAPACITY 128u
#define PRIORITY_BURST_MAX 4u
#define OWNER_CURRENT(who) ((unsigned char)((who) + 1u))
#define OWNER_PENDING(who) ((unsigned char)((who) + 3u))

static const PoseRef *poses;
static unsigned int pose_refs_count;

static unsigned char current_valid[2];
static unsigned char current_pose[2], current_facing[2];
static unsigned char current_pair_count[2], current_map_index[2];
static unsigned char request_pose[2], request_facing[2];
static unsigned char request_pair_count[2], request_map_index[2];
static unsigned char request_pairs_left[2], request_bank[2];
static unsigned char request_priority[2], priority_burst;
static const unsigned char *request_src[2];
static unsigned char *request_slot_cursor[2];
static unsigned char streaming[2];
/* Buffer de parâmetros do uploader Z80 direto: o par TALL de 64 B vai por
 * OUTI desenrolado, sem o laço OTIR. */
static const unsigned char *upload_src;
static unsigned char upload_dest_pair;
static unsigned char upload_next_actor;
__sfr __at (0x7e) stream_vcounter;

/* Local compact pair index -> physical VRAM pair. Two maps per actor let a
 * pending pose be staged without changing the metadata of the visible pose. */
static unsigned char slot_maps[2][2][PAIR_CAPACITY];
static unsigned char pair_owner[PAIR_CAPACITY];

static unsigned char pose_ref_is_valid(const PoseRef *r) {
    unsigned int packed_size;
    if (!r || (r->size & 63u) != 0u || r->size > 8192u ||
        r->off > 16384u) return 0;
    packed_size = r->size * 2u;
    return packed_size <= 16384u - r->off;
}

static void release_map(unsigned char who, unsigned char map_index,
                        unsigned char count, unsigned char owner) {
    unsigned char i, pair;
    for (i = 0; i < count; i++) {
        pair = slot_maps[who][map_index][i];
        if (pair < PAIR_CAPACITY && pair_owner[pair] == owner)
            pair_owner[pair] = 0;
    }
}

static unsigned char reserve_map(unsigned char who, unsigned char count) {
    unsigned char i, free_count = 0, mapped = 0;
    unsigned char map_index = (unsigned char)(current_map_index[who] ^ 1u);
    for (i = 0; i < PAIR_CAPACITY; i++)
        if (!pair_owner[i]) free_count++;
    if (count > free_count) return 0;

    request_map_index[who] = map_index;
    for (i = 0; i < PAIR_CAPACITY && mapped < count; i++) {
        if (!pair_owner[i]) {
            pair_owner[i] = OWNER_PENDING(who);
            slot_maps[who][map_index][mapped++] = i;
        }
    }
    return mapped == count;
}

static void cancel_request(unsigned char who) {
    if (streaming[who])
        release_map(who, request_map_index[who], request_pair_count[who],
                    OWNER_PENDING(who));
    streaming[who] = 0;
    request_pair_count[who] = 0;
    request_pairs_left[who] = 0;
    request_priority[who] = 0;
    request_bank[who] = 0;
    request_src[who] = 0;
    request_slot_cursor[who] = 0;
}

static void make_current(unsigned char who, unsigned char pose,
                         unsigned char facing) {
    unsigned char i, map_index = request_map_index[who];
    unsigned char count = request_pair_count[who];
    if (current_valid[who])
        release_map(who, current_map_index[who], current_pair_count[who],
                    OWNER_CURRENT(who));
    for (i = 0; i < count; i++) {
        unsigned char pair = slot_maps[who][map_index][i];
        if (pair < PAIR_CAPACITY && pair_owner[pair] == OWNER_PENDING(who))
            pair_owner[pair] = OWNER_CURRENT(who);
    }
    current_pose[who] = pose;
    current_facing[who] = facing;
    current_pair_count[who] = count;
    current_map_index[who] = map_index;
    current_valid[who] = 1;
    streaming[who] = 0;
}

void stream_init(const PoseRef *p, unsigned int count) {
    unsigned char i;
    poses = p;
    pose_refs_count = count;
    for (i = 0; i < PAIR_CAPACITY; i++) pair_owner[i] = 0;
    for (i = 0; i < 2; i++) {
        current_valid[i] = 0;
        current_pose[i] = 0xFF;
        current_facing[i] = 0xFF;
        current_pair_count[i] = 0;
        current_map_index[i] = 0;
        request_pose[i] = 0xFF;
        request_facing[i] = 0xFF;
        request_pair_count[i] = 0;
        request_priority[i] = 0;
        request_map_index[i] = 1;
        request_pairs_left[i] = 0;
        request_bank[i] = 0;
        request_src[i] = 0;
        request_slot_cursor[i] = 0;
        streaming[i] = 0;
    }
    upload_next_actor = 0;
    priority_burst = 0;
}

void stream_request(unsigned char who, unsigned char pose,
                    unsigned char facing, unsigned char priority) {
    unsigned int index = pose;
    const PoseRef *r;
    unsigned int pair_count_wide;
    unsigned char pair_count;
    if (who > 1 || !poses || index >= pose_refs_count) return;
    facing &= 1u;
    if (current_valid[who] && current_pose[who] == pose &&
        current_facing[who] == facing) {
        cancel_request(who);
        return;
    }
    if (streaming[who] && request_pose[who] == pose &&
        request_facing[who] == facing) {
        request_priority[who] = (priority != 0u);
        return;
    }
    cancel_request(who);
    r = &poses[index];
    if (!pose_ref_is_valid(r)) return;
    pair_count_wide = r->size >> 6;
    if (pair_count_wide > PAIR_CAPACITY) return;
    pair_count = (unsigned char)pair_count_wide;
    if (!reserve_map(who, pair_count)) return;
    request_pose[who] = pose;
    request_facing[who] = facing;
    request_pair_count[who] = pair_count;
    request_priority[who] = (priority != 0u);
    request_pairs_left[who] = pair_count;
    request_bank[who] = r->bank;
    request_src[who] = (const unsigned char *)(0x8000u + r->off +
          ((unsigned int)facing * r->size));
    request_slot_cursor[who] = &slot_maps[who][request_map_index[who]][0];
    if (!r->size) {
        make_current(who, pose, facing);
        return;
    }
    streaming[who] = 1;
}

static void upload_pair_fast(void) __naked {
    __asm
        ld a, (_upload_dest_pair)
        ld l, a
        ld h, #0
        add hl, hl
        add hl, hl
        add hl, hl
        add hl, hl
        add hl, hl
        add hl, hl
        di
        ld a, l
        out (0xbf), a
        ld a, h
        or #0x40
        out (0xbf), a
        ei
        ld hl, (_upload_src)
        ld b, #64
        ld c, #0xbe
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
        ret
    __endasm;
}

static void upload_chunk(unsigned char who) {
    unsigned char physical_pair;
    SMS_mapROMBank(request_bank[who]);
    upload_src = request_src[who];
    physical_pair = *request_slot_cursor[who];
    upload_dest_pair = physical_pair;
    upload_pair_fast();
    request_src[who] += CHUNK;
    request_slot_cursor[who]++;
    request_pairs_left[who]--;
    if (!request_pairs_left[who])
        make_current(who, request_pose[who], request_facing[who]);
}

void stream_step(void) {
    unsigned char uploads = 0, who, other, line;
    if (!streaming[0] && !streaming[1]) return;
    SMS_saveROMBank();
    /* Diagnostic budget retained from v084: one pair total, admitted only in
     * C0..CF. Request metadata is prepared before this VBlank path. */
    while (uploads < 1u) {
        line = stream_vcounter;
        if (line < 0xC0u || line >= 0xD0u) break;
        who = upload_next_actor;
        if (!streaming[who]) who ^= 1u;
        if (!streaming[who]) {
            priority_burst = 0;
            break;
        }
        other = (unsigned char)(who ^ 1u);
        if (streaming[other]) {
            if (request_priority[other] > request_priority[who] &&
                priority_burst < PRIORITY_BURST_MAX)
                who = other;
            if (request_priority[who] > request_priority[who ^ 1u])
                priority_burst++;
            else
                priority_burst = 0;
        } else {
            priority_burst = 0;
        }
        upload_chunk(who);
        upload_next_actor = (unsigned char)(who ^ 1u);
        uploads++;
    }
    SMS_restoreROMBank();
}

void stream_load_now(unsigned char who, unsigned char pose,
                     unsigned char facing) {
    unsigned int index = pose, off = 0, n, local_pair;
    const PoseRef *r;
    unsigned char pair_count, map_index, physical_pair;
    const unsigned char *src;
    if (who > 1 || !poses || index >= pose_refs_count) return;
    facing &= 1u;
    if (current_valid[who] && current_pose[who] == pose &&
        current_facing[who] == facing) {
        cancel_request(who);
        return;
    }
    cancel_request(who);
    r = &poses[index];
    if (!pose_ref_is_valid(r)) return;
    if ((r->size >> 6) > PAIR_CAPACITY) return;
    pair_count = (unsigned char)(r->size >> 6);
    if (!reserve_map(who, pair_count)) return;
    request_pose[who] = pose;
    request_facing[who] = facing;
    request_pair_count[who] = pair_count;
    map_index = request_map_index[who];
    if (r->size) {
        SMS_saveROMBank();
        SMS_mapROMBank(r->bank);
        while (off < r->size) {
            n = r->size - off;
            if (n > CHUNK) n = CHUNK;
            local_pair = off >> 6;
            physical_pair = slot_maps[who][map_index][local_pair];
            src = (const unsigned char *)(0x8000u + r->off +
                  ((unsigned int)facing * r->size) + off);
            SMS_VRAMmemcpy_brief((unsigned int)physical_pair << 6,
                                 src, (unsigned char)n);
            off += n;
        }
        SMS_restoreROMBank();
    }
    make_current(who, pose, facing);
}

unsigned char stream_disp(unsigned char who) {
    return (who < 2 && current_valid[who]) ? current_pose[who] : 0;
}

unsigned char stream_disp_facing(unsigned char who) {
    return (who < 2 && current_valid[who]) ? current_facing[who] : 0;
}

const unsigned char *stream_disp_map(unsigned char who) {
    if (who >= 2 || !current_valid[who]) return 0;
    return slot_maps[who][current_map_index[who]];
}

unsigned char stream_disp_pair_count(unsigned char who) {
    return (who < 2 && current_valid[who]) ? current_pair_count[who] : 0;
}
