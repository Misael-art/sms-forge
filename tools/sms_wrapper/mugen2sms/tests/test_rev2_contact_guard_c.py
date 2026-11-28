"""Exercise the conservative candidate at real combat call sites in host C."""
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


def test_contact_candidate_retries_without_freezing_or_invisible_damage(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    functions = []
    for declaration in ("static unsigned char contact_side_ready", "static void combat_step"):
        match = re.search(r"^" + declaration + r"\([^\n]*\n?.*?^}", source, re.M | re.S)
        assert match, declaration
        functions.append(match.group())
    code = r'''
#include <stdio.h>
#define LUTA_CONTACT_GUARD 1
#define LUTA_CONTACT_TRACE 1
#define LUTA_DIAG_PSG 0
#define S_HIT 4u
#define S_BLOCKABLE 8u
#define ST_KO 9u
typedef struct { unsigned char pose; } Frame;
typedef struct { unsigned char flags, dmg; } StateDef;
typedef struct { const StateDef *states; unsigned char pose_base, hitstop, hit_push, guard_push; } CharacterData;
typedef struct { unsigned int x,y,life; unsigned char face,role,stop,hit_done,recover; } Fighter;
typedef struct { const Frame *frame; unsigned int pose_global; unsigned char face,base_pair,role_fresh; } Slot;
typedef struct { const Frame *frame; unsigned char face,base_pair,x,y,role; } ContactStamp;
static CharacterData characters[2];
static Fighter fighter[2];
static Slot current[2];
static ContactStamp contact_committed[2];
static unsigned int contact_guard_rejected, contact_guard_accepted;
static unsigned int probe_clsn_checks,probe_guard_events,probe_hit_events,probe_damage_p1,probe_damage_p2;
static unsigned int probe_ko_events,probe_life_p1,probe_life_p2;
static unsigned char probe_recover_p1,probe_recover_p2;
static unsigned char last_kind,last_reason;
static unsigned char boxes_overlap(const Frame *a,unsigned char sa,unsigned char sec,const Frame *b,unsigned char sb) {
    (void)a;(void)sa;(void)sec;(void)b;(void)sb;return 1;
}
static void trace_contact(unsigned char a,unsigned char kind,const Frame *f0,const Frame *f1,unsigned char reason) {
    (void)a;(void)f0;(void)f1;last_kind=kind;last_reason=reason;
}
static void move_x(unsigned char d,signed int delta) {(void)d;(void)delta;}
static void set_role(unsigned char d,unsigned char role) {fighter[d].role=role;}
static void input_flush(unsigned char d) {(void)d;}
''' + "\n".join(functions) + r'''
#define CHECK(c,msg) do { if (!(c)) { puts(msg);return 1; } } while(0)
int main(void) {
    Frame attack={34}, defender={12}, old={33};
    StateDef p1[10]={{0}}, p2[10]={{0}};
    p1[7].flags=S_HIT;p1[7].dmg=112;
    characters[0].states=p1;characters[1].states=p2;
    characters[0].pose_base=0;characters[1].pose_base=48;
    characters[0].hitstop=12;characters[0].hit_push=5;characters[0].guard_push=5;
    fighter[0].role=7;fighter[1].role=2;fighter[0].life=fighter[1].life=1000;
    fighter[0].x=130u*256u;fighter[1].x=155u*256u;fighter[0].face=0;fighter[1].face=1;
    current[0].frame=&old;current[0].pose_global=33;current[0].face=0;current[0].base_pair=4;
    current[1].frame=&defender;current[1].pose_global=60;current[1].face=1;current[1].base_pair=20;
    current[0].role_fresh=current[1].role_fresh=1;
    contact_committed[0]=(ContactStamp){&old,0,4,130,0,7};
    contact_committed[1]=(ContactStamp){&defender,1,20,155,0,2};
    CHECK(!contact_side_ready(2,&attack) && !contact_side_ready(0,0),"invalid side/frame");
    combat_step(&attack,&defender);
    CHECK(contact_guard_rejected==1 && contact_guard_accepted==0 && last_kind==3 && last_reason==1 &&
          fighter[1].life==1000 && !fighter[0].hit_done && !fighter[0].stop && !fighter[1].stop,
          "mismatched contact was not rejected without state freeze");
    current[0].frame=&attack;current[0].pose_global=34;contact_committed[0].frame=&attack;
    CHECK(contact_side_ready(0,&attack),"ready frame rejected");
    contact_committed[0].base_pair=5;
    CHECK(!contact_side_ready(0,&attack),"stale tile base accepted");contact_committed[0].base_pair=4;
    contact_committed[0].x=129;
    CHECK(!contact_side_ready(0,&attack),"stale screen position accepted");contact_committed[0].x=130;
    current[0].face=1;
    CHECK(!contact_side_ready(0,&attack),"stale face accepted");current[0].face=0;
    contact_committed[0].role=0;
    CHECK(!contact_side_ready(0,&attack),"stale role accepted");contact_committed[0].role=7;
    current[0].role_fresh=0;
    CHECK(!contact_side_ready(0,&attack),"previous role instance accepted");current[0].role_fresh=1;
    combat_step(&attack,&defender);
    CHECK(contact_guard_rejected==1 && contact_guard_accepted==1 && last_kind==2 &&
          fighter[1].life==888 && fighter[0].hit_done && probe_damage_p2==112 &&
          fighter[0].stop==12 && fighter[1].stop==12,"eligible hit did not resolve");
    fighter[0].hit_done=0;p2[2].flags=S_BLOCKABLE;
    combat_step(&attack,&defender);
    CHECK(contact_guard_accepted==2 && last_kind==1 && probe_guard_events==1 &&
          fighter[1].life==888,"eligible guard changed life or was lost");
    return 0;
}
'''
    program = tmp_path / "contact_guard.c"
    program.write_text(code, encoding="utf-8")
    executable = tmp_path / "contact_guard"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(executable)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_candidate_marks_clipped_or_rejected_sprite_cells(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"^static void emit_frame\(.*?^}", source, re.M | re.S)
    assert match
    code = r'''
#include <stdio.h>
#include "rev2_diag.h"
#define DIAG_FLOOR 160u
#define LUTA_DIAG_CLIP_PLAIN 1
#define LUTA_DIAG_TELEMETRY 0
#define LUTA_CONTACT_GUARD 1
#define LUTA_CONTACT_STAMPS 1
#define LUTA_BG_CAMERA 0
#define METASPRITE_END 0x80
typedef struct { unsigned int x,y; unsigned char face; } Actor;
typedef struct { unsigned char face,base_pair; } Slot;
static Actor fighter[2];static Slot current[2];
static unsigned char contact_draw_count[2],contact_draw_invalid[2];
static unsigned int probe_omitted_sat,probe_sat_om_p1,probe_sat_om_p2;
static int calls,reject_call;
static int fake_sprite(int x,int y,int tile) {
    (void)x;(void)y;(void)tile;calls++;return calls==reject_call ? -1 : 0;
}
#define SMS_addSprite(x,y,t) fake_sprite(x,y,t)
''' + match.group() + r'''
#define CHECK(c,msg) do { if (!(c)) {puts(msg);return 1;} } while(0)
int main(void) {
    unsigned char axis[]={0,0,0,0}, low_axis[]={0,0,17,0};
    unsigned char meta[]={0,0,0,8,0,2,0x80}, single[]={0,0,0,0x80};
    Frame frame={1,0,meta,meta,0,axis,16,16,meta,meta};
    fighter[0].x=100u*256u;
    emit_frame(0,&frame);
    CHECK(contact_draw_count[0]==2 && !contact_draw_invalid[0],"valid cells not counted");
    calls=0;reject_call=2;contact_draw_count[0]=contact_draw_invalid[0]=0;
    emit_frame(0,&frame);
    CHECK(contact_draw_count[0]==1 && contact_draw_invalid[0] && probe_sat_om_p1==1,
          "SAT rejection not recorded");
    calls=reject_call=0;contact_draw_count[0]=contact_draw_invalid[0]=0;
    fighter[0].x=249u*256u;emit_frame(0,&frame);
    CHECK(contact_draw_count[0]==1 && contact_draw_invalid[0],"clipped cell not recorded");
    contact_draw_count[0]=contact_draw_invalid[0]=0;frame.meta=single;
    emit_frame(0,&frame);
    CHECK(contact_draw_count[0]==1 && contact_draw_invalid[0],"partial right edge accepted");
    contact_draw_count[0]=contact_draw_invalid[0]=0;fighter[0].x=100u*256u;frame.axis=low_axis;
    emit_frame(0,&frame);
    CHECK(contact_draw_count[0]==1 && contact_draw_invalid[0],"partial bottom edge accepted");
    contact_draw_count[0]=contact_draw_invalid[0]=0;frame.meta=0;
    emit_frame(0,&frame);
    CHECK(!contact_draw_count[0] && contact_draw_invalid[0],"missing metadata accepted");
    return 0;
}
'''
    program = tmp_path / "contact_emission.c"
    program.write_text(code, encoding="utf-8")
    executable = tmp_path / "contact_emission"
    compiled = subprocess.run(["cc", "-std=c99", "-I", str(ROOT / "SMS_projects/luta_mugem_rev2/inc"),
                               str(program), "-o", str(executable)], capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
