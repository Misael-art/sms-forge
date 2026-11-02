"""The opt-in ROM recorder uses the existing TRC3 decoder contract and freezes."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from mugen2sms.analysis.trace_air_identity import decode_buffer

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.rev2
@pytest.mark.skipif(shutil.which("cc") is None, reason="host C compiler unavailable")
def test_completed_tick_recorder_serializes_both_source_ids_and_freezes(tmp_path):
    source = (ROOT / "SMS_projects/luta_mugem_rev2/src/main.c").read_text()
    functions = []
    for name in ("init_air_trace", "record_air_trace"):
        functions.append(re.search(r"^static void " + name + r"\([^\n]*\n.*?^}", source, re.M | re.S).group())
    code = r'''
#include <stdio.h>
#include <string.h>
#define AIR_TRACE_TICKS 340u
#define AIR_TRACE_BYTES (8u+AIR_TRACE_TICKS*6u)
typedef struct { unsigned short id; } Anim;
typedef struct { const Anim *anims; } CharacterData;
typedef struct { unsigned char anim,fidx; } Actor;
static CharacterData characters[2];static Actor fighter[2];static unsigned short frames;
static unsigned short air_trace_count,probe_air_trace_start_frame;
static volatile unsigned char probe_air_trace[AIR_TRACE_BYTES];
''' + "\n".join(functions) + r'''
int main(void) {
    Anim p1[2]={{280},{5000}},p2[2]={{221},{8000}};unsigned i;
    unsigned char frozen[AIR_TRACE_BYTES];
    characters[0].anims=p1;characters[1].anims=p2;init_air_trace();
    for(i=0;i<340;i++) {
        frames=100+i;fighter[0].anim=i&1;fighter[1].anim=(i+1)&1;
        fighter[0].fidx=i%5;fighter[1].fidx=i%7;record_air_trace();
    }
    if(probe_air_trace_start_frame!=100 || air_trace_count!=340 || probe_air_trace[4]!=1) return 1;
    memcpy(frozen,(const void*)probe_air_trace,AIR_TRACE_BYTES);
    for(i=0;i<20;i++) record_air_trace();
    if(memcmp(frozen,(const void*)probe_air_trace,AIR_TRACE_BYTES)) return 2;
    return fwrite(frozen,1,AIR_TRACE_BYTES,stdout)==AIR_TRACE_BYTES?0:3;
}
'''
    program = tmp_path / "air_recorder.c"
    program.write_text(code)
    exe = tmp_path / "air_recorder"
    result = subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True)
    assert result.returncode == 0, result.stderr
    rows = decode_buffer(result.stdout)
    assert len(rows) == 340
    for i, row in enumerate(rows):
        assert row["p1_air_action"] == (5000 if i & 1 else 280)
        assert row["p2_air_action"] == (221 if i & 1 else 8000)
        assert row["p1_air_element"] == i % 5
        assert row["p2_air_element"] == i % 7
