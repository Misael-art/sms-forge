"""Exercise the real consumer animation step on one-tick and looping frames."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "SMS_projects/luta_mugem_rev2/src/main.c"
pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="C compiler unavailable")


def test_air_elements_are_exposed_for_their_declared_ticks(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"^static void advance_actor\(.*?^}", source, re.M | re.S)
    assert match
    harness = r'''
#include <stdio.h>
#include <string.h>
#define S_CONTROL 1u
#define ST_IDLE 0u
typedef struct { unsigned char dur, pose; } Frame;
typedef struct { unsigned char n_frames, loop_start; const Frame *frames; } Anim;
typedef struct { unsigned char flags; signed int vel; } StateDef;
typedef struct { const Anim *anims; const StateDef *states; unsigned int pose_base; signed int gravity; } CharacterData;
typedef struct { unsigned char anim, fidx, tick, role, done, stop, face, recover;
                 unsigned int y; unsigned short life; signed int vy; } Actor;
static Actor fighter[2];
static CharacterData characters[2];
static unsigned int probe_hitstop_frames;
static void move_x(unsigned char side, signed int delta) { (void)side; (void)delta; }
static void set_role(unsigned char side, unsigned char role) { (void)side; (void)role; }
''' + match.group() + r'''
#define REQUIRE(c, message) do { if (!(c)) { puts(message); return 1; } } while (0)
int main(void) {
    Frame finite[] = {{1, 0}, {2, 1}, {1, 2}};
    Frame looped[] = {{2, 3}, {1, 4}};
    Anim anims[] = {{3, 255, finite}, {2, 0, looped}};
    StateDef states[] = {{0}};
    const unsigned char expected[] = {0, 1, 1, 2};
    const unsigned char loop_expected[] = {3, 3, 4, 3, 3, 4};
    unsigned int pose; const Frame *frame;
    memset(fighter, 0, sizeof(fighter));
    characters[0] = (CharacterData){anims, states, 10, 1};
    for (unsigned i = 0; i < sizeof(expected); i++) {
        advance_actor(0, &pose, &frame);
        REQUIRE(pose == 10u + expected[i] && frame->pose == expected[i], "finite AIR order or duration changed");
        REQUIRE(fighter[0].done == (i == sizeof(expected) - 1), "finite terminal boundary changed");
    }
    memset(fighter, 0, sizeof(fighter));
    advance_actor(0, &pose, &frame);
    fighter[0].stop = 2;
    advance_actor(0, &pose, &frame);
    REQUIRE(frame->pose == 0, "hitstop replaced the displayed one-tick element");
    advance_actor(0, &pose, &frame);
    REQUIRE(frame->pose == 0, "hitstop did not hold the last displayed element");
    advance_actor(0, &pose, &frame);
    REQUIRE(frame->pose == 1, "AIR did not advance after hitstop");
    memset(fighter, 0, sizeof(fighter)); fighter[0].anim = 1;
    for (unsigned i = 0; i < sizeof(loop_expected); i++) {
        advance_actor(0, &pose, &frame);
        REQUIRE(pose == 10u + loop_expected[i], "loop AIR order or duration changed");
        REQUIRE(!fighter[0].done, "loop incorrectly terminated");
    }
    fighter[0].stop = 2;
    unsigned before_index = fighter[0].fidx, before_tick = fighter[0].tick;
    advance_actor(0, &pose, &frame);
    REQUIRE(fighter[0].fidx == before_index && fighter[0].tick == before_tick,
            "hitstop advanced animation");
    return 0;
}
'''
    program = tmp_path / "air_harness.c"
    program.write_text(harness, encoding="utf-8")
    exe = tmp_path / "air_harness"
    subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                   check=True, capture_output=True, text=True)
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
