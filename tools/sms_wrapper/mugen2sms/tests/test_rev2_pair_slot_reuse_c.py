"""Exercise exact pair-slot reuse against the runtime's real mapping/upload code."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "SMS_projects/luta_mugem_rev2/src/main.c"
pytestmark = [pytest.mark.rev2,
              pytest.mark.skipif(shutil.which("cc") is None,
                                 reason="C compiler unavailable")]


def test_pair_reuse_probes_do_not_overlap_worst_frame_seal():
    source = SOURCE.read_text(encoding="utf-8")
    matches = re.findall(
        r"__at\(0x([0-9A-F]+)\)\s+"
        r"(probe_pair_(?:reused|uploads)_(?:p1|p2)|probe_vline_min)\b",
        source,
    )
    assert dict((name, address) for address, name in matches) == {
        "probe_pair_reused_p1": "C900",
        "probe_pair_uploads_p1": "C901",
        "probe_pair_reused_p2": "C902",
        "probe_pair_uploads_p2": "C903",
        "probe_vline_min": "C8D2",
    }
    assert len(matches) == 5 and len({address for address, _ in matches}) == 5


def extract(source: str, name: str) -> str:
    match = re.search(
        r"^static (?:void|unsigned char|const unsigned char \*)\s*" + name +
        r"\([^\n]*\n?.*?^}", source, re.MULTILINE | re.DOTALL)
    assert match, f"runtime function {name} missing"
    return match.group()


def test_pair_reuse_maps_exact_matches_and_uploads_only_new_pairs(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    functions = "\n".join(extract(source, name) for name in (
        "cache_invalidate", "used_pairs", "pose_facing_offset", "pose_pair_hashes",
        "pair_bytes_equal", "prepare_pair_mapping", "promote_pending",
        "prepare_pair_request", "stream_pending"))
    code = r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define POOL_PAIRS 128u
#define VERSUS_MAX_POSE_PAIRS 32u
#define LUTA_PAIR_SLOT_REUSE 1
#define LUTA_STREAM_WIDE_COPY 0
typedef struct Frame { unsigned char id; } Frame;
typedef struct {
    unsigned char bank;
    unsigned int off, size;
    const unsigned char *right_pair_hashes, *left_pair_hashes;
} PoseRef;
typedef struct {
    unsigned int pose_global;
    unsigned char base_pair, n_pairs, loaded_pairs;
    const Frame *frame;
    unsigned char face;
    unsigned char pair_slot[VERSUS_MAX_POSE_PAIRS];
} CacheSlot;
static unsigned char fail_valid[2];
static unsigned int fail_pose[2];
static unsigned char fail_face[2];
static unsigned char used_pair_count_cached, used_pair_count_dirty;
static unsigned char pair_hash_head[256];
static unsigned char pair_hash_next[VERSUS_MAX_POSE_PAIRS];
static unsigned char pair_hash_touched[VERSUS_MAX_POSE_PAIRS];
static unsigned char pair_hash_touched_count, pair_hash_index_valid;
static unsigned char pending_pair_upload_count[2];
static unsigned char pending_pair_upload_source[2][VERSUS_MAX_POSE_PAIRS];
static unsigned char pending_pair_upload_target[2][VERSUS_MAX_POSE_PAIRS];
static CacheSlot current[2], pending[2];
static PoseRef versus_poses[4];
static volatile unsigned char probe_pair_reused_p1, probe_pair_uploads_p1;
static volatile unsigned char probe_pair_reused_p2, probe_pair_uploads_p2;
static unsigned int probe_uploaded_pairs, probe_bad_pose_ref;
static unsigned char fake_vram[8192], fake_rom[4][16384], fake_bank;
static unsigned char read_mapped_rom_byte(unsigned int offset) {
    return fake_rom[fake_bank][offset];
}
static void fake_copy(unsigned int dst, const void *src, unsigned char size) {
    uintptr_t pos = (uintptr_t)src - 0x8000u;
    if (!size || size > 192u || dst + size > sizeof(fake_vram) ||
        pos + size > sizeof(fake_rom[0])) {
        puts("invalid transfer"); return;
    }
    memcpy(fake_vram + dst, fake_rom[fake_bank] + pos, size);
}
static unsigned char saved_bank;
#define SMS_saveROMBank() (saved_bank = fake_bank)
#define SMS_mapROMBank(n) (fake_bank = (unsigned char)(n))
#define SMS_restoreROMBank() (fake_bank = saved_bank)
#define SMS_VRAMmemcpy_brief(dst, src, size) fake_copy(dst, src, size)
#define STREAM_UPLOAD_PAIRS(dst, src, pairs) \
    SMS_VRAMmemcpy_brief((dst), (src), (unsigned char)((pairs) << 6))
''' + functions + r'''
#define REQUIRE(c, msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
static unsigned char current_hashes[32], next_hashes[32], third_hashes[32];
static void reset(void) {
    unsigned i;
    memset(current, 0, sizeof(current)); memset(pending, 0, sizeof(pending));
    current[0].pose_global = current[1].pose_global = 0xFFFFu;
    pending[0].pose_global = pending[1].pose_global = 0xFFFFu;
    memset(fake_vram, 0, sizeof(fake_vram));
    memset(fake_rom, 0, sizeof(fake_rom));
    fake_bank = saved_bank = 0u;
    memset(pending_pair_upload_count, 0, sizeof(pending_pair_upload_count));
    memset(fail_valid, 0, sizeof(fail_valid)); probe_uploaded_pairs = 0u;
    used_pair_count_cached = 0u; used_pair_count_dirty = 1u;
    memset(pair_hash_head, 0, sizeof(pair_hash_head));
    pair_hash_touched_count = pair_hash_index_valid = 0u;
    probe_pair_reused_p1 = probe_pair_uploads_p1 = 0u;
    probe_pair_reused_p2 = probe_pair_uploads_p2 = 0u;
    for (i = 0; i < 32u; ++i) {
        current_hashes[i] = (unsigned char)(10u + i);
        next_hashes[i] = (unsigned char)(100u + i);
    }
}
static void install(unsigned char side, unsigned char n_current,
                    unsigned char n_next, unsigned char overlap) {
    unsigned char other = (unsigned char)(side ^ 1u);
    unsigned int current_offset = side ? 0x1000u : 0u;
    unsigned int next_offset = side ? 0x2000u : 0x1000u;
    unsigned char face = side ? 1u : 0u;
    unsigned i;
    for (i = 0; i < overlap; ++i) next_hashes[i] = current_hashes[i];
    if (overlap < n_next) next_hashes[overlap] = current_hashes[0];
    if (overlap > 1u) {
        current_hashes[1] = current_hashes[0];
        next_hashes[1] = current_hashes[0];
    }
    versus_poses[1] = (PoseRef){2u, current_offset, (unsigned int)n_current * 64u,
                                current_hashes, current_hashes};
    versus_poses[2] = (PoseRef){2u, next_offset, (unsigned int)n_next * 64u,
                                next_hashes, next_hashes};
    current[side].pose_global = 1u; current[side].n_pairs = n_current;
    current[side].face = face;
    for (i = 0; i < n_current; ++i) {
        current[side].pair_slot[i] = (unsigned char)i;
        memset(fake_vram + (unsigned int)i * 64u, (int)(10u + i), 64u);
        memset(fake_rom[2] + current_offset + (unsigned int)i * 64u,
               (int)(10u + i), 64u);
    }
    current[other].pose_global = 3u; current[other].n_pairs = 4u;
    for (i = 0; i < 4u; ++i) {
        current[other].pair_slot[i] = (unsigned char)(80u + i);
        memset(fake_vram + (80u + i) * 64u, (int)(70u + i), 64u);
    }
    for (i = 0; i < n_next; ++i) {
        unsigned char value = i < overlap ? (unsigned char)(10u + i) :
                                            (unsigned char)(120u + i);
        memset(fake_rom[2] + next_offset + (unsigned int)i * 64u, value, 64u);
    }
}
static int run_case(unsigned char side, unsigned char old_n, unsigned char new_n,
                    unsigned char overlap) {
    unsigned char i, moved;
    unsigned int before;
    unsigned char face = side ? 1u : 0u;
    unsigned char other = (unsigned char)(side ^ 1u);
    Frame next_frame = {2u};
    install(side, old_n, new_n, overlap);
    REQUIRE(prepare_pair_request(side, 2u, new_n, &next_frame, face),
            "could not prepare pair request");
    REQUIRE((side ? probe_pair_reused_p2 : probe_pair_reused_p1) == overlap &&
            (side ? probe_pair_uploads_p2 : probe_pair_uploads_p1) ==
                (unsigned char)(new_n - overlap),
            "reuse/upload counters differ from exact ID intersection");
    REQUIRE(pending[side].base_pair == 0u || overlap == 0u,
            "base diagnostic unexpectedly changed for reused mapping");
    for (i = 0; i < overlap; ++i)
        REQUIRE(pending[side].pair_slot[i] == current[side].pair_slot[i],
                "shared pair did not keep its physical slot");
    for (i = overlap; i < new_n; ++i) {
        unsigned char expected = (unsigned char)(old_n + i - overlap);
        REQUIRE(pending[side].pair_slot[i] == expected,
                "new pair did not receive first free physical slot");
    }
    before = probe_uploaded_pairs;
    while (pending[side].pose_global != 0xFFFFu) {
        moved = stream_pending(side, 4u);
        REQUIRE(moved > 0u || pending[side].pose_global == 0xFFFFu,
                "pair upload stopped before pending completion");
    }
    REQUIRE(probe_uploaded_pairs - before == (unsigned int)(new_n - overlap),
            "stream uploaded reused pairs or skipped new pairs");
    REQUIRE(current[side].pose_global == 2u && current[side].n_pairs == new_n,
            "completed mapping was not promoted");
    for (i = 0; i < new_n; ++i) {
        unsigned char expected = i < overlap ? (unsigned char)(10u + i) :
                                               (unsigned char)(120u + i);
        REQUIRE(fake_vram[(unsigned int)current[side].pair_slot[i] * 64u] == expected,
                "mapped physical pair bytes do not match the requested content");
    }
    REQUIRE(used_pairs() == (unsigned char)(new_n + 4u),
            "physical used-pair count ignored the non-contiguous mapping");
    REQUIRE(!used_pair_count_dirty && used_pair_count_cached == new_n + 4u,
            "completed mapping did not seal the cached occupancy count");
    REQUIRE(used_pairs() == (unsigned char)(new_n + 4u) &&
            !used_pair_count_dirty,
            "unchanged occupancy was not served from the clean cache");
    cache_invalidate(&current[other]);
    REQUIRE(used_pair_count_dirty,
            "releasing an occupied slot did not invalidate the occupancy cache");
    REQUIRE(used_pairs() == new_n && !used_pair_count_dirty,
            "occupancy cache did not recount after slot release");
    return 0;
}
static int test_reindex_after_promotion(void) {
    unsigned char i, moved;
    Frame third_frame = {3u};
    reset();
    if (run_case(0u, 17u, 17u, 9u)) return 1;
    for (i = 0u; i < 17u; i++) {
        if (i < 8u) {
            third_hashes[i] = next_hashes[i];
            memcpy(fake_rom[2] + 0x3000u + (unsigned int)i * 64u,
                   fake_rom[2] + 0x1000u + (unsigned int)i * 64u, 64u);
        } else {
            third_hashes[i] = (unsigned char)(200u + i);
            memset(fake_rom[2] + 0x3000u + (unsigned int)i * 64u,
                   (int)(140u + i), 64u);
        }
    }
    versus_poses[3] = (PoseRef){2u, 0x3000u, 17u * 64u,
                                third_hashes, third_hashes};
    REQUIRE(prepare_pair_request(0u, 3u, 17u, &third_frame, 0u),
            "could not prepare request after pair-index rebuild");
    REQUIRE(probe_pair_reused_p1 == 8u && probe_pair_uploads_p1 == 9u,
            "rebuilt pair index lost exact matches after promotion");
    for (i = 0u; i < 8u; i++)
        REQUIRE(pending[0].pair_slot[i] == current[0].pair_slot[i],
                "rebuilt pair index reused a different physical slot");
    while (pending[0].pose_global != 0xFFFFu) {
        moved = stream_pending(0u, 4u);
        REQUIRE(moved > 0u || pending[0].pose_global == 0xFFFFu,
                "rebuilt pair request stopped before completion");
    }
    REQUIRE(current[0].pose_global == 3u && used_pairs() == 17u,
            "second promoted mapping has an invalid occupancy count");
    for (i = 0u; i < 17u; i++) {
        unsigned char expected = i < 8u ? (unsigned char)(10u + i) :
                                          (unsigned char)(140u + i);
        REQUIRE(fake_vram[(unsigned int)current[0].pair_slot[i] * 64u] == expected,
                "second mapping contains stale or mismatched pair bytes");
    }
    return 0;
}
int main(void) {
    reset();
    if (run_case(0u, 17u, 17u, 17u)) return 1;
    reset();
    if (run_case(0u, 17u, 17u, 9u)) return 1;
    reset();
    if (run_case(1u, 17u, 20u, 0u)) return 1;
    if (test_reindex_after_promotion()) return 1;
    return 0;
}
'''
    program = tmp_path / "pair_slot_reuse.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "pair_slot_reuse"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
