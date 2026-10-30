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
typedef struct { unsigned int x,y,life; unsigned char face,role,stop,hit_done,recover; } Fighter;
typedef struct { const Frame *frame; unsigned char face,base_pair,x,y,role; } ContactStamp;
static CharacterData characters[2];static Fighter fighter[2];
static ContactStamp contact_prepared[2];
static unsigned int probe_present_unready,probe_present_hits;
static unsigned int probe_clsn_checks,probe_guard_events,probe_hit_events,probe_damage_p1,probe_damage_p2;
static unsigned int probe_ko_events,probe_life_p1,probe_life_p2;
static unsigned char probe_recover_p1,probe_recover_p2;
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


def test_interrupted_attack_cannot_hit_later_and_same_tick_trade_is_symmetric(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    code = r'''
#include <stdio.h>
#include <string.h>
#define LUTA_PRESENT_HIT 1
#define LUTA_CONTACT_SAT 0
#define LUTA_CONTACT_GUARD 0
#define LUTA_CONTACT_TRACE 0
#define LUTA_DIAG_PSG 0
#define FIGHT_RUNTIME_DATA_SCHEMA 7
#define S_HIT 4u
#define S_BLOCKABLE 8u
#define ST_KO 9u
typedef struct { unsigned char pose; } Frame;
typedef struct { unsigned char flags,dmg,stop_a,stop_d,guardtime,airtime,hittime; } StateDef;
typedef struct { const StateDef *states; unsigned char pose_base,hitstop,hit_push,guard_push; } CharacterData;
typedef struct { unsigned int x,y,life; unsigned char face,role,stop,hit_done,recover; } Fighter;
typedef struct { const Frame *frame; unsigned char face,base_pair,x,y,role; } ContactStamp;
static CharacterData characters[2]; static Fighter fighter[2];
static ContactStamp contact_prepared[2];
static unsigned int probe_present_unready,probe_present_hits;
static unsigned int probe_clsn_checks,probe_guard_events,probe_hit_events,probe_damage_p1,probe_damage_p2;
static unsigned int probe_ko_events,probe_life_p1,probe_life_p2;
static unsigned char probe_recover_p1,probe_recover_p2,active[2];
static unsigned char boxes_overlap(const Frame *a,unsigned char sa,unsigned char sec,const Frame *b,unsigned char sb) {
    (void)a;(void)sec;(void)b;(void)sb;return active[sa];
}
static void move_x(unsigned char d,signed int delta) {(void)d;(void)delta;}
static void set_role(unsigned char d,unsigned char role) {fighter[d].role=role;}
static void input_flush(unsigned char d) {(void)d;}
''' + extract(source, "combat_step") + r'''
#define CHECK(c,msg) do { if (!(c)) {puts(msg);return 1;} } while(0)
int main(void) {
    Frame frames[2]={{1},{2}}; StateDef states[2][10]={{{0}}};
    unsigned i;
    for (i=0;i<2;i++) {
        states[i][7].flags=S_HIT;states[i][7].dmg=100;
        states[i][7].stop_a=states[i][7].stop_d=4;
        states[i][7].hittime=6;
        characters[i].states=states[i];fighter[i].role=7;fighter[i].life=1000;
        contact_prepared[i]=(ContactStamp){&frames[i],0,0,0,0,7};
    }
    active[0]=1;active[1]=0;
    combat_step(&frames[0],&frames[1]);
    CHECK(fighter[1].life==900 && fighter[1].recover==6,"initial hit missing");
    active[1]=1; /* pose becomes overlapping while the old role is still visible */
    combat_step(&frames[0],&frames[1]);
    CHECK(fighter[0].life==1000,"interrupted attack caused delayed damage");
    fighter[1].stop=0;fighter[1].recover=0;
    combat_step(&frames[0],&frames[1]);
    CHECK(fighter[0].life==1000 && fighter[1].hit_done,
          "interrupted attack revived after pause and recover expired");

    for (i=0;i<2;i++) { fighter[i].life=1000;fighter[i].hit_done=0;fighter[i].recover=0;fighter[i].stop=0; }
    active[0]=0;active[1]=1;
    combat_step(&frames[0],&frames[1]);
    CHECK(fighter[0].life==900 && fighter[0].recover==6,"side 2 hit missing");
    active[0]=1;
    combat_step(&frames[0],&frames[1]);
    CHECK(fighter[1].life==1000,"side 1 interrupted attack caused delayed damage");
    fighter[0].stop=0;fighter[0].recover=0;
    combat_step(&frames[0],&frames[1]);
    CHECK(fighter[1].life==1000 && fighter[0].hit_done,
          "side 1 interrupted attack revived after pause and recover expired");

    for (i=0;i<2;i++) { fighter[i].life=1000;fighter[i].hit_done=0;fighter[i].recover=0;fighter[i].stop=0; }
    active[0]=active[1]=1;
    states[0][7].stop_a=4;states[0][7].stop_d=3;
    states[1][7].stop_a=2;states[1][7].stop_d=7;
    combat_step(&frames[0],&frames[1]);
    CHECK(fighter[0].life==900 && fighter[1].life==900,
          "simultaneous non-lethal hits depend on side order");
    CHECK(fighter[0].stop==7 && fighter[1].stop==3,
          "simultaneous hits shortened an actor's pause");

    for (i=0;i<2;i++) { fighter[i].life=1000;fighter[i].hit_done=0;fighter[i].recover=0;fighter[i].stop=0; }
    fighter[1].role=2;states[1][2].flags=S_BLOCKABLE;
    contact_prepared[1].role=2;states[0][7].guardtime=5;
    active[0]=1;active[1]=0;
    combat_step(&frames[0],&frames[1]);
    CHECK(fighter[1].life==1000 && fighter[1].recover==5 &&
          !fighter[1].hit_done && probe_guard_events==1,
          "guard was treated as an interrupting hit");
    return 0;
}
'''
    compile_and_run(tmp_path, code)
