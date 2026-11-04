"""Compare the real Z80 pacing clock against division across frame wrap."""
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


def test_pacing_clock_matches_reference_for_two_wraps(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"^static void advance_pacing_clock\(void\) \{.*?^\}", source, re.M | re.S)
    assert match, "runtime pacing clock is missing"
    code = r'''
#include <stdint.h>
#include <stdio.h>
#define SCRIPT_STEP_FRAMES 150u
static uint16_t frames, pacing_step;
static uint8_t pacing_remainder;
''' + match.group() + r'''
int main(void) {
    unsigned n;
    for (n = 0; n < 131072u; ++n) {
        frames++;
        advance_pacing_clock();
        if (pacing_step != (uint16_t)(frames / 150u) ||
            pacing_remainder != (uint8_t)(frames % 150u)) {
            printf("mismatch at iteration %u frame %u: step %u remainder %u\n",
                   n, frames, pacing_step, pacing_remainder);
            return 1;
        }
        if ((pacing_step > 255u ? 255u : pacing_step) !=
            ((frames / 150u) > 255u ? 255u : (frames / 150u))) {
            puts("saturated probe differs"); return 1;
        }
    }
    return 0;
}
'''
    program = tmp_path / "pacing.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "pacing"
    result = subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
