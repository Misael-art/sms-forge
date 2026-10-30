"""Check sealed VBlank boundary counters without promoting a timing claim."""
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


def test_stage_counter_counts_only_overruns_inside_sealed_window(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"^static void vblank_stage_sample\([^\n]*\n?.*?^}",
                      source, re.M | re.S)
    assert match, "VBlank stage sampling helper missing"
    code = r'''
#include <stdio.h>
#define WORST_FRAME_WINDOW 3000u
static unsigned int probe_frame;
static unsigned char SMS_VCounterPort;
''' + match.group() + r'''
#define REQUIRE(c,msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
int main(void) {
    volatile unsigned int count=0u;
    probe_frame=1u; SMS_VCounterPort=0xBFu;
    vblank_stage_sample(&count);
    REQUIRE(count==1u,"active-display crossing was not counted");
    SMS_VCounterPort=0xC0u;
    vblank_stage_sample(&count);
    REQUIRE(count==1u,"VBlank completion was counted as a spill");
    probe_frame=3001u; SMS_VCounterPort=0u;
    vblank_stage_sample(&count);
    REQUIRE(count==1u,"post-seal frame changed the counter");
    return 0;
}
'''
    program = tmp_path / "vblank_stage_probe.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "vblank_stage_probe"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_vblank_stage_boundaries_follow_map_stream_sat_order():
    source = SOURCE.read_text(encoding="utf-8")
    names = [
        "probe_vblank_stage_before_map",
        "probe_vblank_stage_after_map",
        "probe_vblank_stage_after_stream",
        "probe_vblank_stage_after_sat",
    ]
    positions = [source.index(f"vblank_stage_sample(&{name})") for name in names]
    assert positions == sorted(positions), "VBlank stage samples are out of order"
    assert "LUTA_DIAG_VBLANK_STAGES && LUTA_UPLOAD_TRACE" in source, \
        "overlapping diagnostic buffer modes are not rejected"
