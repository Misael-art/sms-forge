"""Prevent State -1 button chords from matching one simple attack command."""
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "SMS_projects/luta_mugen/integrada/src"
INC = ROOT / "SMS_projects/luta_mugen/integrada/inc"

pytestmark = pytest.mark.skipif(
    shutil.which("gcc") is None or not (SRC / "input.c").exists(),
    reason="gcc ou input.c ausente",
)

HARNESS = r'''
#include <stdio.h>
#include "input.h"

static const unsigned char k1_strong[] = {4, 1, 15, 1, 0x10, 0x08, 0};
static const unsigned char k2_strong[] = {4, 1, 15, 1, 0x20, 0x08, 0};
static const unsigned char both_strong[] = {4, 1, 15, 1, 0x30, 0x08, 0};

static void check_levels(unsigned char levels) {
    unsigned char single1, single2, both;
    unsigned char tick;
    input_init();
    for (tick = 0; tick < 6; tick++) input_tick(0, levels, 0);
    single1 = input_pattern_hit(0, k1_strong);
    single2 = input_pattern_hit(0, k2_strong);
    both = input_pattern_hit(0, both_strong);
    printf("%u %u %u\n", single1, single2, both);
}

int main(void) {
    check_levels(0x10); /* tecla 1 isolada */
    check_levels(0x20); /* tecla 2 isolada */
    check_levels(0x30); /* acorde simultaneo */
    return 0;
}
'''


def test_runtime_chord_is_not_consumed_by_single_button_patterns(tmp_path):
    source = tmp_path / "input_chord_harness.c"
    executable = tmp_path / "input_chord_harness"
    source.write_text(HARNESS)
    subprocess.run(
        [
            "gcc", "-std=c99", "-Wall", "-Werror", "-I", str(INC),
            str(source), str(SRC / "input.c"), str(SRC / "input_tier.c"),
            "-o", str(executable),
        ],
        check=True,
    )
    result = subprocess.run(
        [str(executable)], capture_output=True, text=True, check=True
    )
    assert result.stdout == "1 0 0\n0 1 0\n0 0 1\n"
