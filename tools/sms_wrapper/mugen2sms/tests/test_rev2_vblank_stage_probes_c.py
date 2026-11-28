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


def test_vblank_samples_stay_frozen_after_seal_and_counter_wrap(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"^static void vblank_stage_sample\([^\n]*\n?.*?^}",
                      source, re.M | re.S)
    assert match, "VBlank stage sampling helper missing"
    worst = re.search(r"^static void worst_sample\([^\n]*\n.*?^}", source, re.M | re.S)
    assert worst, "worst-frame sampling helper missing"
    code = r'''
#include <stdio.h>
#include <stdint.h>
#define WORST_FRAME_WINDOW 3000u
static uint16_t probe_frame, probe_vovf;
static unsigned char probe_worst_done, probe_phase, probe_vline;
static unsigned char probe_vline_min=255u, probe_vbl_exit_max;
static unsigned char SMS_VCounterPort;
''' + worst.group() + "\n" + match.group() + r'''
#define REQUIRE(c,msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
int main(void) {
    volatile unsigned int count=0u;
    probe_frame=1u; SMS_VCounterPort=0xBFu;
    vblank_stage_sample(&count);
    REQUIRE(count==1u,"active-display crossing was not counted");
    SMS_VCounterPort=0xC0u;
    vblank_stage_sample(&count);
    REQUIRE(count==1u,"VBlank completion was counted as a spill");
    probe_frame=3000u; SMS_VCounterPort=0xBFu;
    worst_sample();
    REQUIRE(probe_vovf==1u && probe_vline==0xBFu && probe_vline_min==0xBFu,
            "last frame in the window was not counted");
    probe_frame=3001u; SMS_VCounterPort=0u;
    worst_sample();
    vblank_stage_sample(&count);
    REQUIRE(probe_worst_done==1u && count==1u,"window did not seal");

    probe_frame=UINT16_MAX;
    ++probe_frame;
    worst_sample();
    vblank_stage_sample(&count);
    REQUIRE(probe_worst_done==1u && probe_phase==3u,"wrap changed the seal or phase");
    REQUIRE(probe_vovf==1u && probe_vline==0xBFu && probe_vline_min==0xBFu,
            "wrap reopened the sealed window");
    REQUIRE(count==1u,"wrap reopened the sealed stage counter");
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
