"""Verify that the contact snapshot records collision inputs without mutating them."""
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


def test_trace_publishes_exact_logical_and_resident_state(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    enum = re.search(r"enum \{ CT_SEQ.*?CT_BYTES = 53 \};", source, re.S)
    assert enum
    functions = []
    for name in ("contact_trace_word", "trace_contact"):
        match = re.search(r"^static void " + name + r"\([^\n]*\n?.*?^}",
                          source, re.M | re.S)
        assert match, name
        functions.append(match.group())
    code = r'''
#include <stdint.h>
#include <stdio.h>
typedef struct { unsigned char pose; } Frame;
typedef struct { unsigned char pose_base; } Character;
typedef struct { unsigned short x, y; unsigned char face, role; } Fighter;
typedef struct { unsigned short pose_global; unsigned char face; } Slot;
static Character characters[2];
static Fighter fighter[2];
static Slot current[2];
static unsigned int frames;
static unsigned int probe_submit_p1, probe_submit_p2, probe_present_p1, probe_present_p2;
''' + enum.group() + r'''
volatile unsigned char contact_trace[CT_BYTES];
''' + "\n".join(functions) + r'''
static unsigned short getword(unsigned char offset) {
    return contact_trace[offset] | ((unsigned short)contact_trace[offset+1] << 8);
}
#define CHECK(c,msg) do { if (!(c)) { puts(msg); return 1; } } while(0)
int main(void) {
    Frame f0={8}, f1={7};
    characters[0].pose_base=40; characters[1].pose_base=100; frames=0x1234;
    current[0].pose_global=47; current[1].pose_global=106;
    current[0].face=0; current[1].face=1;
    fighter[0].x=0x3456; fighter[1].x=0x789a; fighter[0].y=0x2222; fighter[1].y=0x3333;
    fighter[0].face=1; fighter[1].face=0; fighter[0].role=7; fighter[1].role=5;
    probe_submit_p1=46; probe_submit_p2=105; probe_present_p1=0xffff; probe_present_p2=105;
    trace_contact(0,2,&f0,&f1,0);
    CHECK(contact_trace[CT_SEQ]==2 && contact_trace[CT_ATTACKER]==0 && contact_trace[CT_KIND]==2,
          "record not completely published");
    CHECK(getword(CT_TICK)==0x1234 && getword(CT_FRAME_P1)==((uintptr_t)&f0 & 0xffffu) &&
          getword(CT_FRAME_P2)==((uintptr_t)&f1 & 0xffffu),"frame identity or tick");
    CHECK(getword(CT_LOGICAL_P1)==48 && getword(CT_LOGICAL_P2)==107 &&
          getword(CT_RESIDENT_P1)==47 && getword(CT_RESIDENT_P2)==106,
          "logical/resident snapshot");
    CHECK(getword(CT_SUBMITTED_P1)==46 && getword(CT_SUBMITTED_P2)==105 &&
          getword(CT_PRESENT_P1)==0xffff && getword(CT_PRESENT_P2)==105,
          "previous submission snapshot");
    CHECK(getword(CT_USED_FRAME_P1)==((uintptr_t)&f0 & 0xffffu) &&
          getword(CT_USED_FRAME_P2)==((uintptr_t)&f1 & 0xffffu) &&
          contact_trace[CT_USED_X_P1]==0x34 && contact_trace[CT_USED_X_P2]==0x78 &&
          contact_trace[CT_USED_FACE_P1]==1 && contact_trace[CT_POLICY]==0,
          "actual logical collision inputs");
    CHECK(contact_trace[CT_FACE_P1]==1 && contact_trace[CT_FACE_P2]==0 &&
          contact_trace[CT_RESIDENT_FACE_P1]==0 && contact_trace[CT_RESIDENT_FACE_P2]==1 &&
          getword(CT_X_P1)==0x3456 && getword(CT_X_P2)==0x789a &&
          getword(CT_Y_P1)==0x2222 && getword(CT_Y_P2)==0x3333 &&
          contact_trace[CT_ROLE_P1]==7 && contact_trace[CT_ROLE_P2]==5,
          "facing, positions or roles");
    CHECK(fighter[0].x==0x3456 && fighter[1].y==0x3333 && current[1].pose_global==106,
          "trace modified gameplay inputs");
    contact_trace[CT_SEQ]=254; trace_contact(1,3,&f0,&f1,2);
    CHECK(contact_trace[CT_SEQ]==0 && contact_trace[CT_ATTACKER]==1 &&
          contact_trace[CT_KIND]==3 && contact_trace[CT_REASON]==2,
          "sequence wrap or guard event");
    return 0;
}
'''
    program = tmp_path / "contact_trace.c"
    program.write_text(code, encoding="utf-8")
    executable = tmp_path / "contact_trace"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(executable)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
