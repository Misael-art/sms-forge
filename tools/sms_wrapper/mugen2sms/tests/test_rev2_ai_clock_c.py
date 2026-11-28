"""Sequential AI input stays identical to the random-access 16-bit plan."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / "SMS_projects/luta_mugem_rev2"
pytestmark = [pytest.mark.rev2,
              pytest.mark.skipif(shutil.which("cc") is None, reason="C compiler unavailable")]


def test_ai_clock_matches_all_16bit_frames_and_wraps(tmp_path):
    program = tmp_path / "ai_clock.c"
    program.write_text(r'''
#include <limits.h>
#include <stdio.h>
#include "fight_input.h"

int main(void) {
    FightAIClock clock;
    unsigned long n;
    unsigned char face;
    if (USHRT_MAX != 65535u) return 2;
    fight_ai_clock_reset(&clock);
    if (clock.beat != 0u || clock.sub != 0u) return 3;
    for (n = 1ul; n <= 131072ul; n++) {
        unsigned short frame = (unsigned short)n;
        fight_ai_clock_advance(&clock, frame);
        if (clock.beat != (frame / FI_AI_BEAT_FRAMES) % FI_AI_BEATS ||
            clock.sub != frame % FI_AI_BEAT_FRAMES) {
            printf("phase mismatch at %lu (%u): %u/%u\n", n, frame,
                   clock.beat, clock.sub);
            return 4;
        }
        for (face = 0u; face < 2u; face++) {
            unsigned char beat = 255u;
            unsigned char expected = fight_input_ai_levels(frame, face, &beat);
            unsigned char actual = fight_input_ai_levels_clock(&clock, face);
            if (beat != clock.beat || expected != actual) {
                printf("levels mismatch at %lu face %u: %u/%u\n", n, face,
                       actual, expected);
                return 5;
            }
        }
    }
    /* Independent landmarks preserve button and direction semantics. */
    if (fight_input_ai_levels(25u, 0u, 0) != K_RIGHT ||
        fight_input_ai_levels(25u, 1u, 0) != K_LEFT ||
        fight_input_ai_levels(150u, 0u, 0) != K_LP ||
        fight_input_ai_levels(158u, 0u, 0) != 0u ||
        fight_input_ai_levels(200u, 0u, 0) != K_LP ||
        fight_input_ai_levels(203u, 0u, 0) != 0u)
        return 6;
    return 0;
}
''', encoding="ascii")
    exe = tmp_path / "ai_clock"
    command = ["cc", "-std=c99", "-Wall", "-Wextra", "-Werror",
               "-I", str(PROJECT / "inc"), str(program),
               str(PROJECT / "src/fight_input.c"),
               str(PROJECT / "src/input.c"),
               str(PROJECT / "src/input_tier.c"), "-o", str(exe)]
    compiled = subprocess.run(command, capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
