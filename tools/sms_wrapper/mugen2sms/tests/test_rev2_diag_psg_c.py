"""Exercise event coalescing and preemption policy in the actual C helpers."""
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


def test_audio_probes_do_not_overlap_measurement_contract(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tools/sms_wrapper"))
    import measure_runtime_probe as runtime
    import measure_worst_frame as worst

    source = SOURCE.read_text(encoding="utf-8")
    declarations = re.findall(r"volatile unsigned (int|char) __at\(0x([0-9A-Fa-f]+)\) (probe_audio_\w+)", source)
    assert len(declarations) == 6
    used = set()
    for kind, address, _name in declarations:
        start = int(address, 16)
        cells = set(range(start, start + (2 if kind == "int" else 1)))
        assert not used.intersection(cells)
        used.update(cells)
    reserved = {0xC800 + offset for offset in worst.OFFSETS.values()}
    reserved.update(0xC800 + offset for offset in runtime.OFFSETS.values())
    reserved.update(range(0xC8D0, 0xC8D7))
    reserved.update(range(0xC900, 0xC904))
    reserved.update(range(0xC8E0, 0xC8E5))
    reserved.update((0xC8EC, 0xC8F1))  # second bytes of worst-frame words
    assert not used.intersection(reserved)


def test_psg_event_priority_and_frame_service(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    functions = []
    for name in ("diag_sfx_queue", "diag_sfx_tick"):
        match = re.search(r"^static void " + name + r"\([^\n]*\n?.*?^}",
                          source, re.M | re.S)
        assert match, name
        functions.append(match.group())
    code = r'''
#include <stdio.h>
#define DIAG_SFX_NONE 0u
#define DIAG_SFX_GUARD 1u
#define DIAG_SFX_HIT 2u
#define PSG_PLAYING 1u
#define SFX_CHANNEL3 2u
#define SFX_CHANNELS2AND3 3u
static unsigned char sfx_hit[1], sfx_hurt[1];
static unsigned int probe_audio_hit_queued, probe_audio_guard_queued, probe_audio_played;
static unsigned int probe_audio_first_frame, frames;
static unsigned char probe_audio_last_played, probe_audio_guard_dropped;
static unsigned char diag_sfx_pending, diag_sfx_active_priority;
static unsigned char status, last_mask;
static unsigned int serviced_frames, stops;
static unsigned char PSGSFXGetStatus(void) { return status; }
static void PSGSFXStop(void) { status=0; stops++; }
static void PSGSFXPlay(void *sample, unsigned char mask) {
    (void)sample; status=1; last_mask=mask;
}
static void PSGSFXFrame(void) { serviced_frames++; }
''' + "\n".join(functions) + r'''
#define CHECK(c,msg) do { if (!(c)) { puts(msg); return 1; } } while(0)
int main(void) {
    diag_sfx_queue(9); CHECK(diag_sfx_pending==0 && probe_audio_played==0,"invalid event");
    frames=17;
    diag_sfx_queue(DIAG_SFX_GUARD); diag_sfx_queue(DIAG_SFX_HIT); diag_sfx_tick();
    CHECK(probe_audio_guard_queued==1 && probe_audio_hit_queued==1 &&
          probe_audio_guard_dropped==1 && probe_audio_last_played==DIAG_SFX_HIT &&
          probe_audio_played==1 && last_mask==SFX_CHANNELS2AND3 && serviced_frames==1 &&
          probe_audio_first_frame==17,
          "same-tick hit priority");
    diag_sfx_queue(DIAG_SFX_GUARD); diag_sfx_tick();
    CHECK(probe_audio_guard_dropped==2 && probe_audio_played==1 && stops==0,
          "guard interrupted active hit");
    frames=20; diag_sfx_queue(DIAG_SFX_HIT); diag_sfx_tick();
    CHECK(probe_audio_played==2 && stops==1 && serviced_frames==3 &&
          probe_audio_first_frame==17,"hit restart");
    status=0; diag_sfx_queue(DIAG_SFX_GUARD); diag_sfx_tick();
    CHECK(probe_audio_played==3 && last_mask==SFX_CHANNEL3 &&
          probe_audio_last_played==DIAG_SFX_GUARD,"guard after completion");
    diag_sfx_queue(DIAG_SFX_GUARD); diag_sfx_queue(DIAG_SFX_GUARD);
    diag_sfx_queue(DIAG_SFX_HIT); diag_sfx_tick();
    CHECK(probe_audio_guard_dropped==4 && probe_audio_played==4 && stops==2 &&
          last_mask==SFX_CHANNELS2AND3,"coalescing and hit preemption");
    status=0; diag_sfx_tick();
    CHECK(diag_sfx_active_priority==0 && serviced_frames==6,"idle service");
    return 0;
}
'''
    program = tmp_path / "audio.c"
    program.write_text(code, encoding="utf-8")
    executable = tmp_path / "audio"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(executable)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
