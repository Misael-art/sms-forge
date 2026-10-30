"""Exercise the consumer's grounded body separation using source-sized widths."""
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


def test_ground_push_preserves_order_and_handles_limits(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"^static void pusher_step\(unsigned char left_side\).*?^}",
                      source, re.M | re.S)
    assert match, "grounded body separation must receive the pre-move order"
    program = tmp_path / "ground_push.c"
    program.write_text(r'''
#include <stdio.h>
#include <string.h>
#define DIAG_X_MIN (16u * 256u)
#define DIAG_X_MAX (240u * 256u)
typedef struct { unsigned int x, y; } Actor;
typedef struct { unsigned int ground_front_q8; } CharacterData;
static Actor fighter[2];
static CharacterData characters[2];
static unsigned int probe_pusher_frames, probe_push_invalid_geometry;
''' + match.group() + r'''
#define REQUIRE(c, msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
static void reset(unsigned ax, unsigned bx) {
    memset(fighter, 0, sizeof(fighter));
    fighter[0].x = ax; fighter[1].x = bx;
    characters[0].ground_front_q8 = 12u * 256u;
    characters[1].ground_front_q8 = 6u * 256u;
    probe_pusher_frames = probe_push_invalid_geometry = 0u;
}
int main(void) {
    unsigned a, b;
    reset(100u * 256u, 118u * 256u);
    pusher_step(0u);
    REQUIRE(fighter[0].x == 100u * 256u && fighter[1].x == 118u * 256u &&
            !probe_pusher_frames, "exact contact moved");
    reset(100u * 256u, 105u * 256u);
    pusher_step(0u);
    REQUIRE(fighter[1].x - fighter[0].x == 18u * 256u &&
            probe_pusher_frames == 1u, "overlap not separated");
    a = fighter[0].x; b = fighter[1].x;
    pusher_step(0u);
    REQUIRE(fighter[0].x == a && fighter[1].x == b && probe_pusher_frames == 1u,
            "separation not idempotent");
    reset(168u * 256u, 165u * 256u);
    pusher_step(0u);
    REQUIRE(fighter[0].x < fighter[1].x &&
            fighter[1].x - fighter[0].x == 18u * 256u, "grounded crossing not reversed");
    reset(165u * 256u, 168u * 256u);
    pusher_step(1u);
    REQUIRE(fighter[1].x < fighter[0].x &&
            fighter[0].x - fighter[1].x == 18u * 256u, "reverse order lost");
    reset(DIAG_X_MIN, DIAG_X_MIN + 2u * 256u);
    pusher_step(0u);
    REQUIRE(fighter[0].x == DIAG_X_MIN &&
            fighter[1].x - fighter[0].x == 18u * 256u, "left edge");
    reset(DIAG_X_MAX - 2u * 256u, DIAG_X_MAX);
    pusher_step(0u);
    REQUIRE(fighter[1].x == DIAG_X_MAX &&
            fighter[1].x - fighter[0].x == 18u * 256u, "right edge");
    reset(165u * 256u, 168u * 256u);
    fighter[0].y = 1u;
    pusher_step(1u);
    REQUIRE(fighter[0].x == 165u * 256u && fighter[1].x == 168u * 256u,
            "airborne crossing blocked");
    reset(100u * 256u, 100u * 256u);
    characters[1].ground_front_q8 = 0u;
    pusher_step(0u);
    REQUIRE(probe_push_invalid_geometry == 1u && !probe_pusher_frames,
            "missing width was not reported");
    characters[0].ground_front_q8 = 60000u;
    characters[1].ground_front_q8 = 60000u;
    pusher_step(0u);
    REQUIRE(probe_push_invalid_geometry == 2u && !probe_pusher_frames,
            "unrepresentable combined width was not reported");
    pusher_step(2u);
    REQUIRE(probe_push_invalid_geometry == 3u && !probe_pusher_frames,
            "invalid actor order was not reported");
    reset(DIAG_X_MIN - 1u, 100u * 256u);
    pusher_step(0u);
    REQUIRE(probe_push_invalid_geometry == 1u && fighter[0].x == DIAG_X_MIN - 1u,
            "out-of-arena coordinate was silently repaired");
    reset(100u * 256u, 100u * 256u);
    characters[1].ground_front_q8++;
    pusher_step(0u);
    REQUIRE(fighter[1].x - fighter[0].x == 18u * 256u + 1u,
            "fractional Q8 width lost");
    reset(100u * 256u, 118u * 256u);
    for (unsigned i = 0; i < 80u; i++) {
        fighter[0].x += 256u;
        pusher_step(0u);
        REQUIRE(fighter[0].x < fighter[1].x &&
                fighter[1].x - fighter[0].x == 18u * 256u &&
                fighter[1].x <= DIAG_X_MAX, "sustained approach crossed or left arena");
    }
    return 0;
}
''', encoding="ascii")
    exe = tmp_path / "ground_push"
    result = subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror",
                             str(program), "-o", str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
