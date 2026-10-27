"""Check camera offset bounds without sacrificing the opposite edge."""
from __future__ import annotations
import re
import shutil
import subprocess
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[4]
SOURCE=ROOT/'SMS_projects/luta_mugem_rev2/src/main.c'
pytestmark=[pytest.mark.rev2,pytest.mark.skipif(shutil.which('cc') is None,reason='C compiler unavailable')]


def test_camera_shift_is_bounded_and_reports_infeasible_extents(tmp_path):
    source=SOURCE.read_text(encoding='utf-8')
    m=re.search(r'^static unsigned char bg_camera_adjust\([^\n]*\n?.*?^}',source,re.M|re.S)
    assert m,'camera bounds function missing'
    c=r'''
#include <stdio.h>
''' + m.group() + r'''
#define CHECK(left,right,want,conflict) do { unsigned char bad=99u; \
    unsigned char got=bg_camera_adjust(left,right,&bad); \
    if (got!=(want) || bad!=(conflict)) { \
      printf("bounds %d %d got %u/%u expected %u/%u\n",left,right,got,bad,want,conflict);return 1; } \
  } while(0)
int main(void) {
    CHECK(1, 176, 7u, 0u);
    CHECK(8, 256, 0u, 0u);
    CHECK(-4, 244, 12u, 0u);
    CHECK(-4, 248, 0u, 1u);
    CHECK(0, 255, 0u, 1u);
    CHECK(-80, 100, 0u, 1u);
    return 0;
}
'''
    p=tmp_path/'camera.c';p.write_text(c,encoding='utf-8');exe=tmp_path/'camera'
    result=subprocess.run(['cc','-std=c99',str(p),'-o',str(exe)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    result=subprocess.run([str(exe)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_camera_plan_uses_both_resident_extents_and_counts_conflicts(tmp_path):
    source=SOURCE.read_text(encoding='utf-8')
    functions=[]
    for name,kind in [('bg_camera_adjust','unsigned char'),
                      ('bg_camera_actor_origin','signed int'),
                      ('plan_bg_camera','void')]:
        m=re.search(r'^static '+kind+' '+name+r'\([^\n]*\n?.*?^}',source,re.M|re.S)
        assert m,f'{name} missing'
        functions.append(m.group())
    code=r'''
#include <stdint.h>
#include <stdio.h>
#include "rev2_diag.h"
typedef struct { unsigned int x; } Actor;
typedef struct { const Frame *frame; unsigned char face; } Slot;
static Actor fighter[2];
static Slot current[2];
static unsigned char bg_camera_x,probe_bg_camera_shift;
static unsigned int probe_bg_camera_conflict,probe_bg_camera_applied;
'''+'\n'.join(functions)+r'''
#define REQUIRE(cond,msg) do { if (!(cond)) { puts(msg);return 1; } } while(0)
int main(void) {
    const unsigned char axis[]={0,0,0,0};
    Frame a={0},b={0};a.axis=axis;b.axis=axis;a.width=32;b.width=32;
    current[0].frame=&a;current[0].face=0;
    current[1].frame=&b;current[1].face=1;
    fighter[0].x=1u*256u;fighter[1].x=120u*256u;
    plan_bg_camera();
    REQUIRE(bg_camera_x==7u && probe_bg_camera_shift==7u &&
            probe_bg_camera_applied==1u && probe_bg_camera_conflict==0u,
            "feasible camera did not protect both extents");
    current[1].face=0;fighter[1].x=240u*256u;
    plan_bg_camera();
    REQUIRE(bg_camera_x==0u && probe_bg_camera_shift==0u &&
            probe_bg_camera_conflict==1u,"opposite-edge conflict was hidden");
    current[1].frame=0;plan_bg_camera();
    REQUIRE(bg_camera_x==0u && probe_bg_camera_conflict==2u,
            "missing resident extent was not counted");
    return 0;
}
'''
    program=tmp_path/'plan.c';program.write_text(code,encoding='utf-8');exe=tmp_path/'plan'
    result=subprocess.run(['cc','-std=c99','-I',str(ROOT/'SMS_projects/luta_mugem_rev2/inc'),
                           str(program),'-o',str(exe)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    result=subprocess.run([str(exe)],capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr
