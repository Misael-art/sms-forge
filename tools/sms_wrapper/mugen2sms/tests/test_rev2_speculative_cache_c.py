"""Exercise a speculative next-pose slot without early publication or eviction."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "SMS_projects/luta_mugem_rev2/src/main.c"
pytestmark = [pytest.mark.rev2,
              pytest.mark.skipif(shutil.which("cc") is None, reason="C compiler unavailable")]


def extract(source: str, name: str) -> str:
    match = re.search(r"^static (?:void|unsigned char) " + name + r"\([^\n]*\n?.*?^}",
                      source, re.M | re.S)
    assert match, f"runtime function {name} missing"
    return match.group()


def test_prefetch_keeps_current_until_requested_and_respects_urgent_work(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    functions = "\n".join(extract(source, name) for name in (
        "cache_invalidate", "alloc_contiguous", "pose_facing_offset", "promote_pending",
        "stream_pending", "cancel_prefetch", "request_pose", "stage_prefetch"))
    code = r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#define POOL_PAIRS 128u
#define LUTA_PROFILE 1
#define LUTA_SPECULATIVE_PREFETCH 1
#define VERSUS_POSE_COUNT 8u
typedef struct Frame { int identity; } Frame;
typedef struct { unsigned char bank; unsigned int off, size; } PoseRef;
typedef struct {
    unsigned int pose_global;
    unsigned char base_pair, n_pairs, loaded_pairs;
    const Frame *frame;
    unsigned char face, speculative;
} CacheSlot;
static unsigned char fail_valid[2], fail_size[2];
static CacheSlot current[2], pending[2];
static PoseRef versus_poses[8];
static unsigned int probe_uploaded_pairs, probe_stall_frames, probe_bad_pose_ref;
static unsigned int probe_superseded_p1, probe_superseded_p2;
static unsigned int probe_overflow_p1, probe_overflow_p2;
static unsigned int probe_prefetch_reserved_p1, probe_prefetch_reserved_p2;
static unsigned int probe_prefetch_hit_p1, probe_prefetch_hit_p2, probe_prefetch_discarded;
static unsigned char fake_vram[8192], fake_rom[16384];
static void fake_copy(unsigned int dst, const void *src, unsigned char size) {
    uintptr_t pos = (uintptr_t)src - 0x8000u;
    if (!size || size > 192 || dst + size > sizeof(fake_vram) || pos + size > sizeof(fake_rom)) {
        puts("invalid transfer"); return;
    }
    memcpy(fake_vram + dst, fake_rom + pos, size);
}
#define SMS_saveROMBank() ((void)0)
#define SMS_mapROMBank(n) ((void)(n))
#define SMS_restoreROMBank() ((void)0)
#define SMS_VRAMmemcpy_brief(dst, src, size) fake_copy(dst, src, size)
#define STREAM_UPLOAD_PAIRS(dst, src, pairs) \
    SMS_VRAMmemcpy_brief((dst), (src), (unsigned char)((pairs) << 6))
''' + functions + r'''
#define REQUIRE(c, msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
static void reset_slots(void) {
    memset(current, 0, sizeof(current)); memset(pending, 0, sizeof(pending));
    current[0].pose_global = current[1].pose_global = 0xFFFFu;
    pending[0].pose_global = pending[1].pose_global = 0xFFFFu;
    fail_valid[0] = fail_valid[1] = 0u;
    probe_prefetch_reserved_p1 = probe_prefetch_reserved_p2 = 0u;
    probe_prefetch_hit_p1 = probe_prefetch_hit_p2 = probe_prefetch_discarded = 0u;
    probe_superseded_p1 = probe_superseded_p2 = probe_bad_pose_ref = 0u;
    memset(fake_vram, 0, sizeof(fake_vram));
    for (unsigned i = 0; i < sizeof(fake_rom); i++) fake_rom[i] = (unsigned char)(i * 37u + 11u);
    for (unsigned i = 0; i < 8u; i++) versus_poses[i] = (PoseRef){2, i * 0x500u, 4u * 64u};
}
int main(void) {
    Frame a = {1}, b = {2}, next = {3}, other = {4};
    unsigned base;
    reset_slots();
    current[0] = (CacheSlot){1, 0, 4, 4, &a, 0, 0};
    current[1] = (CacheSlot){3, 4, 4, 4, &other, 1, 0};
    stage_prefetch(0u, 2u, 4u, &b, 0u);
    base = pending[0].base_pair * 64u;
    REQUIRE(pending[0].pose_global == 2u && pending[0].speculative &&
            probe_prefetch_reserved_p1 == 1u, "prefetch was not staged");
    REQUIRE(stream_pending(0u, 8u) == 4u && pending[0].loaded_pairs == 4u &&
            pending[0].speculative && current[0].pose_global == 1u,
            "completed speculative pose became visible early");
    REQUIRE(!memcmp(fake_vram + base, fake_rom + 0xA00, 256u), "prefetched bytes differ");
    request_pose(0u, 1u, 4u, &a, 0u);
    REQUIRE(pending[0].pose_global == 2u && pending[0].speculative,
            "current-pose request discarded useful prefetch");
    request_pose(0u, 2u, 4u, &next, 0u);
    REQUIRE(current[0].pose_global == 2u && current[0].frame == &next &&
            pending[0].pose_global == 0xFFFFu && probe_prefetch_hit_p1 == 1u,
            "requested ready prefetch was not published");

    reset_slots();
    current[0] = (CacheSlot){1, 0, 4, 4, &a, 0, 0};
    stage_prefetch(0u, 2u, 4u, &b, 0u);
    REQUIRE(stream_pending(0u, 2u) == 2u, "partial prefetch upload");
    request_pose(0u, 2u, 4u, &next, 0u);
    REQUIRE(!pending[0].speculative && pending[0].loaded_pairs == 2u &&
            current[0].pose_global == 1u && !probe_prefetch_hit_p1,
            "partial prefetch did not become urgent safely");
    REQUIRE(stream_pending(0u, 2u) == 2u && current[0].pose_global == 2u &&
            current[0].frame == &next, "partial urgent upload did not complete");

    reset_slots();
    current[0] = (CacheSlot){1, 0, 4, 4, &a, 0, 0};
    stage_prefetch(0u, 2u, 4u, &b, 0u);
    REQUIRE(stream_pending(0u, 1u) == 1u, "stale setup");
    request_pose(0u, 4u, 4u, &next, 0u);
    REQUIRE(pending[0].pose_global == 4u && !pending[0].speculative &&
            pending[0].loaded_pairs == 0u && current[0].pose_global == 1u,
            "changed request reused stale speculative upload");
    stage_prefetch(0u, 2u, 4u, &b, 0u);
    REQUIRE(pending[0].pose_global == 4u && !pending[0].speculative,
            "prefetch displaced urgent upload");

    reset_slots();
    current[0] = (CacheSlot){1, 0, 4, 4, &a, 0, 0};
    current[1] = (CacheSlot){3, 4, 4, 4, &other, 1, 0};
    stage_prefetch(0u, 2u, 4u, &b, 0u);
    versus_poses[4].off = 0x1A00u;
    request_pose(1u, 4u, 4u, &next, 1u);
    REQUIRE(pending[1].pose_global == 4u && !pending[1].speculative,
            "urgent opponent did not enter pending");
    REQUIRE(stream_pending(0u, 4u) == 0u && pending[0].loaded_pairs == 0u,
            "speculative traffic ran while opponent was urgent");
    REQUIRE(stream_pending(1u, 4u) == 4u && current[1].pose_global == 4u,
            "urgent opponent did not complete");
    REQUIRE(stream_pending(0u, 4u) == 4u && current[0].pose_global == 1u,
            "prefetch did not resume safely after urgent work");

    reset_slots();
    current[0] = (CacheSlot){1, 0, 50, 50, &a, 0, 0};
    current[1] = (CacheSlot){3, 50, 50, 50, &other, 1, 0};
    versus_poses[2] = (PoseRef){2, 0x800u, 28u * 64u};
    versus_poses[4] = (PoseRef){2, 0x2000u, 28u * 64u};
    stage_prefetch(1u, 2u, 28u, &b, 1u);
    REQUIRE(pending[1].speculative && pending[1].n_pairs == 28u,
            "opponent prefetch did not occupy remaining pool");
    request_pose(0u, 4u, 28u, &next, 0u);
    REQUIRE(pending[1].pose_global == 0xFFFFu && pending[0].pose_global == 4u &&
            current[0].pose_global == 1u && current[1].pose_global == 3u &&
            probe_prefetch_discarded == 1u,
            "urgent pose did not reclaim only speculative memory");
    return 0;
}
'''
    program = tmp_path / "prefetch.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "prefetch"
    compiled = subprocess.run(["cc", "-std=c99", "-Wno-int-to-pointer-cast", str(program),
                               "-o", str(exe)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_predictor_follows_only_the_active_air_sequence(tmp_path):
    function = extract(SOURCE.read_text(encoding="utf-8"), "prefetch_next")
    code = r'''
#include <stdio.h>
#define VERSUS_POSE_COUNT 8u
typedef struct Frame { unsigned char dur, pose; } Frame;
typedef struct { unsigned char n_frames, loop_start; const Frame *frames; } Anim;
typedef struct { const Anim *anims; unsigned char pose_base; } CharacterData;
typedef struct { unsigned int pose_global; const Frame *frame; unsigned char face; } CacheSlot;
typedef struct { unsigned char face, done, anim, fidx; } Actor;
typedef struct { unsigned int size; } PoseRef;
static Frame frames[3] = {{3u, 1u}, {4u, 2u}, {5u, 3u}};
static Anim anims[2] = {{3u, 0u, frames}, {3u, 0u, frames}};
static CharacterData characters[2] = {{anims, 0u}, {anims, 0u}};
static CacheSlot current[2];
static Actor fighter[2];
static PoseRef versus_poses[8];
static unsigned int probe_bad_pose_ref;
static unsigned stages, cancels, staged_pose, staged_pairs, staged_face;
static const Frame *staged_frame;
static void cancel_prefetch(unsigned char side) { (void)side; cancels++; }
static void stage_prefetch(unsigned char side, unsigned int pose, unsigned char pairs,
                           const Frame *frame, unsigned char face) {
    (void)side; stages++; staged_pose = pose; staged_pairs = pairs;
    staged_frame = frame; staged_face = face;
}
''' + function + r'''
#define REQUIRE(c, msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
int main(void) {
    versus_poses[2].size = 192u;
    versus_poses[1].size = 128u;
    fighter[0] = (Actor){0u, 0u, 0u, 0u};
    current[0] = (CacheSlot){1u, &frames[0], 0u};
    prefetch_next(0u, &frames[0], 1u);
    REQUIRE(stages == 1u && staged_pose == 2u && staged_pairs == 3u &&
            staged_frame == &frames[1] && staged_face == 0u, "wrong next AIR frame");
    fighter[0].fidx = 2u; current[0].pose_global = 3u; current[0].frame = &frames[2];
    prefetch_next(0u, &frames[2], 3u);
    REQUIRE(stages == 2u && staged_pose == 1u && staged_pairs == 2u &&
            staged_frame == &frames[0], "loop start was not respected");
    anims[0].loop_start = 255u;
    prefetch_next(0u, &frames[2], 3u);
    REQUIRE(cancels == 1u && stages == 2u, "terminal sequence predicted a frame");
    fighter[0].fidx = 0u; current[0].pose_global = 1u; current[0].frame = &frames[0];
    frames[0].dur = 255u;
    prefetch_next(0u, &frames[0], 1u);
    REQUIRE(cancels == 2u && stages == 2u, "hold predicted a frame");
    frames[0].dur = 3u; fighter[0].done = 1u;
    prefetch_next(0u, &frames[0], 1u);
    REQUIRE(cancels == 3u, "completed actor predicted a frame");
    fighter[0].done = 0u; fighter[0].fidx = 1u;
    prefetch_next(0u, &frames[0], 1u);
    REQUIRE(cancels == 4u, "stale AIR frame survived role change");
    fighter[0].fidx = 4u;
    prefetch_next(0u, &frames[0], 1u);
    REQUIRE(cancels == 5u, "out-of-range AIR index survived");
    fighter[0].fidx = 0u; current[0].frame = NULL;
    prefetch_next(0u, &frames[0], 1u);
    REQUIRE(cancels == 6u, "uninitialized resident predicted a frame");
    current[0].frame = &frames[0]; fighter[0].face = 1u;
    prefetch_next(0u, &frames[0], 1u);
    REQUIRE(cancels == 7u, "facing mismatch survived");
    fighter[0].face = 0u; frames[1].pose = 9u;
    prefetch_next(0u, &frames[0], 1u);
    REQUIRE(cancels == 8u && probe_bad_pose_ref == 1u && stages == 2u,
            "invalid next pose was not rejected");
    prefetch_next(2u, &frames[0], 1u);
    REQUIRE(probe_bad_pose_ref == 2u, "invalid side was not rejected");
    return 0;
}
'''
    program = tmp_path / "predictor.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "predictor"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
