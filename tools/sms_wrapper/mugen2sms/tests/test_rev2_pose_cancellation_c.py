"""Exercise the consumer's real cache functions when a pose request reverses."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "SMS_projects/luta_mugem_rev2/src/main.c"
pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="C compiler unavailable")


def extract(source: str, name: str) -> str:
    match = re.search(r"^static (?:void|unsigned char) " + name + r"\([^\n]*\n?.*?^}",
                      source, re.MULTILINE | re.DOTALL)
    assert match, f"runtime function {name} not found"
    return match.group()


def test_allocator_matches_bitmap_first_fit_with_fragmentation(tmp_path):
    """Compare the real allocator with a bitmap oracle, including unordered slots."""
    allocator = extract(SOURCE.read_text(encoding="utf-8"), "alloc_contiguous")
    code = r'''
#include <stdio.h>
#include <string.h>
#define POOL_PAIRS 128u
typedef struct { unsigned int pose_global; unsigned char base_pair, n_pairs; } CacheSlot;
static CacheSlot current[2], pending[2];
static unsigned char fail_valid[2];
''' + allocator + r'''
static unsigned long rng = 0x2748u;
static unsigned random_value(void) {
    rng = (rng * 1664525ul + 1013904223ul) & 0xfffffffful;
    return (unsigned)(rng >> 16);
}
int main(void) {
    CacheSlot *slots[4] = {&current[0], &current[1], &pending[0], &pending[1]};
    unsigned trial;
    {
        unsigned i; unsigned char base = 0xab;
        for (i = 0; i < 4; ++i) slots[i]->pose_global = 0xffffu;
        if (!alloc_contiguous(128u, &base) || base != 0u) return 2;
        slots[2]->pose_global = 1u; slots[2]->base_pair = 0u; slots[2]->n_pairs = 128u;
        base = 0xab;
        if (alloc_contiguous(1u, &base) || base != 0xab) return 3;
    }
    for (trial = 0; trial < 100000u; ++trial) {
        unsigned char bitmap[POOL_PAIRS] = {0};
        unsigned order[4] = {0, 1, 2, 3};
        unsigned pos = 0, i, n, expect = 255u;
        unsigned char actual = 0xabu, ok;
        for (i = 0; i < 4; ++i) slots[i]->pose_global = 0xffffu;
        for (i = 3; i > 0; --i) {
            unsigned j = random_value() % (i + 1u), tmp = order[i];
            order[i] = order[j]; order[j] = tmp;
        }
        for (i = 0; i < 4 && pos < POOL_PAIRS; ++i) {
            unsigned size, j;
            pos += random_value() % 13u;
            if (pos >= POOL_PAIRS) break;
            size = 1u + random_value() % 45u;
            if (size > POOL_PAIRS - pos) size = POOL_PAIRS - pos;
            slots[order[i]]->pose_global = i;
            slots[order[i]]->base_pair = (unsigned char)pos;
            slots[order[i]]->n_pairs = (unsigned char)size;
            for (j = pos; j < pos + size; ++j) bitmap[j] = 1;
            pos += size;
        }
        n = 1u + random_value() % POOL_PAIRS;
        for (i = 0; i + n <= POOL_PAIRS; ++i) {
            unsigned j;
            for (j = i; j < i + n && !bitmap[j]; ++j) {}
            if (j == i + n) { expect = i; break; }
        }
        fail_valid[0] = fail_valid[1] = 1u;
        ok = alloc_contiguous((unsigned char)n, &actual);
        if ((expect != 255u) != !!ok ||
            (ok && (actual != expect || fail_valid[0] || fail_valid[1])) ||
            (!ok && (actual != 0xabu || !fail_valid[0] || !fail_valid[1]))) {
            printf("trial %u size %u expected %u got %u ok %u\n", trial, n, expect, actual, ok);
            return 1;
        }
    }
    return 0;
}
'''
    program = tmp_path / "allocator_oracle.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "allocator_oracle"
    subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                   check=True, capture_output=True, text=True)
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_abandoned_upload_cannot_replace_current_pose(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    functions = "\n".join(extract(source, name) for name in
                          ("cache_invalidate", "alloc_contiguous", "pose_facing_offset",
                           "promote_pending", "stream_pending", "request_pose"))
    harness = r'''
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#define POOL_PAIRS 128u
#define LUTA_PROFILE 1
#define VERSUS_POSE_COUNT 8u
typedef struct Frame { int identity; } Frame;
typedef struct { unsigned char bank; unsigned int off, size; } PoseRef;
typedef struct {
    unsigned int pose_global;
    unsigned char base_pair, n_pairs, loaded_pairs;
    const Frame *frame;
    unsigned char face;
} CacheSlot;
static unsigned char fail_valid[2], fail_size[2];
static CacheSlot current[2], pending[2];
static PoseRef versus_poses[8];
static unsigned int probe_uploaded_pairs, probe_stall_frames;
static unsigned int probe_superseded_p1, probe_superseded_p2;
static unsigned int probe_overflow_p1, probe_overflow_p2;
static unsigned int probe_bad_pose_ref;
static unsigned int copies, copied_bytes;
static unsigned char fake_vram[8192], fake_rom[16384];
static void fake_copy(unsigned int dst, const void *src, unsigned char size) {
    uintptr_t pos = (uintptr_t)src - 0x8000u;
    if (!size || size > 192 || dst + size > sizeof(fake_vram) || pos + size > sizeof(fake_rom)) {
        puts("invalid transfer");
        return;
    }
    memcpy(fake_vram + dst, fake_rom + pos, size);
    copies++; copied_bytes += size;
}
#define SMS_saveROMBank() ((void)0)
#define SMS_mapROMBank(n) ((void)(n))
#define SMS_restoreROMBank() ((void)0)
#define SMS_VRAMmemcpy_brief(dst, src, size) fake_copy(dst, src, size)
#define STREAM_UPLOAD_PAIRS(dst, src, pairs) \
    SMS_VRAMmemcpy_brief((dst), (src), (unsigned char)((pairs) << 6))
''' + functions + r'''
#define REQUIRE(cond, msg) do { if (!(cond)) { puts(msg); return 1; } } while (0)
static void reset_slots(void) {
    memset(current, 0, sizeof(current)); memset(pending, 0, sizeof(pending));
    current[0].pose_global = current[1].pose_global = 0xFFFFu;
    pending[0].pose_global = pending[1].pose_global = 0xFFFFu;
    fail_valid[0] = fail_valid[1] = 0;
    copies = copied_bytes = probe_superseded_p1 = probe_superseded_p2 = 0;
    probe_overflow_p1 = probe_overflow_p2 = probe_bad_pose_ref = 0;
    memset(fake_vram, 0, sizeof(fake_vram));
    for (unsigned i = 0; i < sizeof(fake_rom); i++) fake_rom[i] = (unsigned char)(i * 37u + 11u);
    versus_poses[2] = (PoseRef){2, 0x100, 4 * 64};
}
int main(void) {
    Frame a = {1}, a_next = {11}, b = {2}, b_next = {22}, opponent = {3};
    reset_slots();
    current[0] = (CacheSlot){1, 0, 4, 4, &a};
    pending[0] = (CacheSlot){2, 4, 4, 2, &b};
    current[1] = (CacheSlot){3, 8, 4, 4, &opponent};
    request_pose(0, 1, 4, &a_next, 0);
    REQUIRE(pending[0].pose_global == 0xFFFFu, "abandoned pending pose remained live");
    REQUIRE(probe_superseded_p1 == 1, "cancellation was not counted");
    REQUIRE(stream_pending(0, 8) == 0 && copies == 0, "abandoned upload continued");
    REQUIRE(current[0].pose_global == 1 && current[0].frame == &a_next,
            "resident bitmap kept stale AIR frame metadata");
    REQUIRE(current[1].pose_global == 3 && current[1].frame == &opponent, "opponent was changed");

    reset_slots();
    current[0] = (CacheSlot){1, 0, 4, 4, &a};
    pending[0] = (CacheSlot){2, 4, 4, 2, &b};
    request_pose(0, 2, 4, &b_next, 0);
    REQUIRE(pending[0].pose_global == 2 && pending[0].loaded_pairs == 2 &&
            pending[0].frame == &b_next,
            "matching pending pose must continue");
    REQUIRE(probe_superseded_p1 == 0, "matching request counted as cancellation");
    REQUIRE(stream_pending(0, 8) == 2 && current[0].pose_global == 2 &&
            current[0].frame == &b_next,
            "matching pending pose did not complete");
    REQUIRE(copied_bytes == 128 && !memcmp(fake_vram + 384, fake_rom + 0x180, 128),
            "continued upload changed bytes or offsets");

    reset_slots();
    current[0] = (CacheSlot){1, 0, 4, 4, &a};
    pending[0] = (CacheSlot){2, 4, 7, 0, &b};
    versus_poses[2].size = 7 * 64;
    REQUIRE(stream_pending(0, 6) == 6 && pending[0].loaded_pairs == 6 &&
            current[0].pose_global == 1, "bounded upload promoted incomplete pose");
    REQUIRE(copied_bytes == 384 && !memcmp(fake_vram + 256, fake_rom + 0x100, 384),
            "bounded upload changed bytes or offsets");
    REQUIRE(stream_pending(0, 1) == 1 && current[0].pose_global == 2 &&
            copied_bytes == 448 && !memcmp(fake_vram + 256, fake_rom + 0x100, 448),
            "last pair or completed pose is wrong");

    reset_slots();
    current[0] = (CacheSlot){1, 0, 60, 60, &a};
    current[1] = (CacheSlot){3, 60, 60, 60, &opponent};
    versus_poses[2].size = 16 * 64;
    request_pose(0, 2, 16, &b, 0);
    REQUIRE(current[0].pose_global == 1 && current[1].pose_global == 3,
            "allocation failure displaced a resident fighter");
    REQUIRE(pending[0].pose_global == 0xFFFFu && probe_overflow_p1 == 1,
            "allocation failure was not recorded");
    request_pose(0, 2, 16, &b, 0);
    REQUIRE(probe_overflow_p1 == 1, "unchanged pool ignored failed-allocation memo");

    /* A failed memo must expire on every pool change, including after 256
     * changes on an 8-bit target. Otherwise an old generation aliases. */
    cache_invalidate(&current[1]);
    for (unsigned i = 0; i < 127u; i++) {
        unsigned char base;
        REQUIRE(alloc_contiguous(4, &base), "cannot create temporary pool entry");
        pending[1] = (CacheSlot){4, base, 4, 0, &opponent};
        cache_invalidate(&pending[1]);
    }
    {
        unsigned char base;
        REQUIRE(alloc_contiguous(4, &base), "cannot create last pool entry");
        pending[1] = (CacheSlot){4, base, 4, 0, &opponent};
    }
    request_pose(0, 2, 16, &b, 0);
    REQUIRE(pending[0].pose_global == 2,
            "old allocation failure survived 256 pool changes");

    reset_slots();
    current[0] = (CacheSlot){2, 0, 4, 4, &a, 0};
    current[1] = (CacheSlot){3, 4, 4, 4, &opponent, 1};
    request_pose(0, 2, 4, &a_next, 1);
    REQUIRE(pending[0].pose_global == 2 && pending[0].face == 1 &&
            current[0].face == 0, "facing change reused wrong resident bitmap");
    request_pose(0, 2, 4, &a_next, 0);
    REQUIRE(pending[0].pose_global == 0xFFFFu && current[0].face == 0,
            "return to resident face did not cancel opposite face");
    request_pose(0, 2, 4, &a_next, 1);
    {
        unsigned base = pending[0].base_pair * 64u;
        REQUIRE(stream_pending(0, 3) == 3 && current[0].face == 0,
                "incomplete opposite face was promoted");
        REQUIRE(!memcmp(fake_vram + base, fake_rom + 0x200, 3 * 64),
                "P1 left face bytes differ");
        REQUIRE(stream_pending(0, 1) == 1 && current[0].face == 1 &&
                current[0].frame == &a_next && current[1].face == 1,
                "P1 completed facing or opponent changed incorrectly");
    }

    reset_slots();
    current[1] = (CacheSlot){3, 0, 4, 4, &opponent, 1};
    versus_poses[3] = (PoseRef){3, 0x600, 4 * 64};
    request_pose(1, 3, 4, &b, 0);
    {
        unsigned base = pending[1].base_pair * 64u;
        REQUIRE(stream_pending(1, 4) == 4 && current[1].face == 0 &&
                !memcmp(fake_vram + base, fake_rom + 0x500, 4 * 64),
                "P2 right face bytes or publication differ");
    }

    reset_slots();
    current[0] = (CacheSlot){1, 0, 4, 4, &a, 0};
    pending[0] = (CacheSlot){2, 4, 4, 1, &b, 0};
    versus_poses[2] = (PoseRef){2, 0x3fc0, 64};
    request_pose(0, 2, 1, &b, 1);
    REQUIRE(pending[0].pose_global == 0xFFFFu && probe_bad_pose_ref == 1,
            "bank-crossing descriptor was accepted or stale upload survived");
    versus_poses[2] = (PoseRef){2, 0x3f80, 64};
    request_pose(0, 2, 1, &b, 1);
    REQUIRE(stream_pending(0, 1) == 1 && current[0].face == 1,
            "exact bank boundary was incorrectly rejected");
    request_pose(0, 99, 1, &b, 0);
    REQUIRE(probe_bad_pose_ref == 2, "out-of-range pose was not rejected");
    {
        unsigned int offset;
        PoseRef valid_p2_boundary = {2, 0x3fc0, 64};
        PoseRef underflow_p2 = {2, 0, 64};
        PoseRef wrong_bank = {1, 0, 64};
        PoseRef bad_size = {2, 0, 65};
        REQUIRE(pose_facing_offset(&valid_p2_boundary, 1, 1, &offset) && offset == 0x3fc0,
                "valid P2 boundary rejected");
        REQUIRE(!pose_facing_offset(&underflow_p2, 1, 0, &offset) &&
                !pose_facing_offset(&wrong_bank, 0, 0, &offset) &&
                !pose_facing_offset(&bad_size, 0, 0, &offset),
                "invalid source descriptor accepted");
    }
    return 0;
}
'''
    program = tmp_path / "cache_harness.c"
    program.write_text(harness, encoding="utf-8")
    exe = tmp_path / "cache_harness"
    subprocess.run(["cc", "-std=c99", "-Wno-int-to-pointer-cast", str(program), "-o", str(exe)],
                   check=True, capture_output=True, text=True)
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
