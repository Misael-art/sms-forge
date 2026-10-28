"""Production collision uses the pose submitted in the same frame."""
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


def extract(source, name, kind="void"):
    match = re.search(r"^static " + kind + " " + name + r"\([^\n]*\n?.*?^}",
                      source, re.M | re.S)
    assert match, name
    return match.group()


def compile_and_run(tmp_path, code):
    program = tmp_path / "present_hit.c"
    program.write_text(code, encoding="utf-8")
    executable = tmp_path / "present_hit"
    result = subprocess.run(["cc", "-std=c99", str(program), "-o", str(executable)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_submitted_anchor_drives_screen_coordinates(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    code = r'''
#include <stdio.h>
#define LUTA_PRESENT_HIT 1
#define LUTA_CONTACT_SAT 0
#define DIAG_FLOOR 160u
typedef struct { signed int x1,y1,x2,y2; } MugenRect;
typedef struct { signed int l,t,r,b; } ScreenRect;
typedef struct { const void *frame; unsigned char face,base_pair,x,y,role; } ContactStamp;
static ContactStamp contact_prepared[2];
''' + extract(source, "mugen_to_screen") + r'''
#define CHECK(c,msg) do { if (!(c)) {puts(msg);return 1;} } while(0)
int main(void) {
    MugenRect m={17,-53,38,-34};ScreenRect out;
    contact_prepared[0]=(ContactStamp){0,0,4,130,0,7};mugen_to_screen(&m,0,&out);
    CHECK(out.l==147 && out.t==107 && out.r==168 && out.b==126,"right-facing coordinates");
    contact_prepared[0]=(ContactStamp){0,1,4,130,10,7};mugen_to_screen(&m,0,&out);
    CHECK(out.l==92 && out.t==97 && out.r==113 && out.b==116,"left-facing coordinates");
    return 0;
}
'''
    compile_and_run(tmp_path, code)


def test_future_logical_frame_cannot_deal_damage(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    code = r'''
#include <stdio.h>
#define LUTA_PRESENT_HIT 1
#define LUTA_CONTACT_SAT 0
#define LUTA_CONTACT_GUARD 0
#define LUTA_CONTACT_TRACE 0
#define LUTA_DIAG_PSG 0
#define S_HIT 4u
#define S_BLOCKABLE 8u
#define ST_KO 9u
typedef struct { unsigned char pose; } Frame;
typedef struct { unsigned char flags,dmg; } StateDef;
typedef struct { const StateDef *states; unsigned char pose_base,hitstop,hit_push,guard_push; } CharacterData;
typedef struct { unsigned int x,y,life; unsigned char face,role,stop,hit_done; } Fighter;
typedef struct { const Frame *frame; unsigned char face,base_pair,x,y,role; } ContactStamp;
static CharacterData characters[2];static Fighter fighter[2];
static ContactStamp contact_prepared[2];
static unsigned int probe_present_unready,probe_present_hits;
static unsigned int probe_clsn_checks,probe_guard_events,probe_hit_events,probe_damage_p1,probe_damage_p2;
static unsigned int probe_ko_events,probe_life_p1,probe_life_p2;
static const Frame *observed0,*observed1,*attack,*hurt;
static unsigned char boxes_overlap(const Frame *a,unsigned char sa,unsigned char sec,const Frame *b,unsigned char sb) {
    (void)sa;(void)sec;(void)sb;observed0=a;observed1=b;return a==attack && b==hurt;
}
static void move_x(unsigned char d,signed int delta) {(void)d;(void)delta;}
static void set_role(unsigned char d,unsigned char role) {fighter[d].role=role;}
static void input_flush(unsigned char d) {(void)d;}
''' + extract(source, "combat_step") + r'''
#define CHECK(c,msg) do { if (!(c)) {puts(msg);return 1;} } while(0)
int main(void) {
    Frame logical0={34}, logical1={48}, shown0={33}, shown1={60};
    StateDef p1[10]={{0}},p2[10]={{0}};p1[7].flags=S_HIT;p1[7].dmg=112;
    characters[0].states=p1;characters[1].states=p2;
    fighter[0].role=7;fighter[1].role=2;fighter[0].life=fighter[1].life=1000;
    attack=&logical0;hurt=&shown1;
    contact_prepared[0]=(ContactStamp){0,0,4,96,0,0};
    contact_prepared[1]=(ContactStamp){&shown1,1,20,160,0,2};
    combat_step(&logical0,&logical1);
    CHECK(probe_present_unready==1 && fighter[1].life==1000 && !probe_clsn_checks,
          "unsubmitted attacker applied damage");
    contact_prepared[0]=(ContactStamp){&shown0,0,4,96,0,7};
    combat_step(&logical0,&logical1);
    CHECK(probe_clsn_checks==1 && !probe_present_hits && fighter[1].life==1000 &&
          observed0==&shown0 && observed1==&shown1 && observed0!=&logical0,
          "logical frame was tested instead of the submitted pose");
    contact_prepared[0].frame=&logical0;
    combat_step(&logical0,&logical1);
    CHECK(probe_present_hits==1 && fighter[1].life==888 && fighter[0].hit_done &&
          observed0==&logical0,
          "submitted attack pose did not deal its damage");
    return 0;
}
'''
    compile_and_run(tmp_path, code)
