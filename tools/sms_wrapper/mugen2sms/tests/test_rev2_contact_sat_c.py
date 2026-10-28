"""Check the candidate that resolves collision from a committed SAT snapshot."""
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
    program = tmp_path / "sat_collision.c"
    program.write_text(code, encoding="utf-8")
    executable = tmp_path / "sat_collision"
    result = subprocess.run(["cc", "-std=c99", str(program), "-o", str(executable)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_committed_position_and_facing_drive_collision_coordinates(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    code = r'''
#include <stdio.h>
#define LUTA_CONTACT_SAT 1
#define DIAG_FLOOR 160u
typedef struct { signed int x1,y1,x2,y2; } MugenRect;
typedef struct { signed int l,t,r,b; } ScreenRect;
typedef struct { unsigned char x,y,face; } ContactStamp;
static ContactStamp contact_committed[2];
''' + extract(source, "mugen_to_screen") + r'''
#define CHECK(c,msg) do { if (!(c)) {puts(msg);return 1;} } while(0)
int main(void) {
    MugenRect m={17,-53,38,-34};ScreenRect out;
    contact_committed[0]=(ContactStamp){130,0,0};mugen_to_screen(&m,0,&out);
    CHECK(out.l==147 && out.t==107 && out.r==168 && out.b==126,"right-facing coordinates");
    contact_committed[0]=(ContactStamp){130,10,1};mugen_to_screen(&m,0,&out);
    CHECK(out.l==92 && out.t==97 && out.r==113 && out.b==116,"left-facing coordinates");
    return 0;
}
'''
    compile_and_run(tmp_path, code)


def test_candidate_uses_committed_frames_and_rejects_stale_snapshots(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    code = r'''
#include <stdio.h>
#define LUTA_CONTACT_SAT 1
#define LUTA_CONTACT_GUARD 0
#define LUTA_CONTACT_TRACE 1
#define LUTA_DIAG_PSG 0
#define S_HIT 4u
#define S_BLOCKABLE 8u
#define ST_KO 9u
typedef struct { unsigned char pose; } Frame;
typedef struct { unsigned char flags,dmg; } StateDef;
typedef struct { const StateDef *states; unsigned char pose_base,hitstop,hit_push,guard_push; } CharacterData;
typedef struct { unsigned int x,y,life; unsigned char face,role,stop,hit_done; } Fighter;
typedef struct { const Frame *frame; unsigned int pose_global; unsigned char face,base_pair,role_fresh; } Slot;
typedef struct { const Frame *frame; unsigned char face,base_pair,x,y,role; } ContactStamp;
static CharacterData characters[2];static Fighter fighter[2];static Slot current[2];
static ContactStamp contact_committed[2];
static unsigned int contact_sat_unready,contact_sat_overlaps;
static unsigned int probe_clsn_checks,probe_guard_events,probe_hit_events,probe_damage_p1,probe_damage_p2;
static unsigned int probe_ko_events,probe_life_p1,probe_life_p2;
static const Frame *expected0,*expected1,*observed0,*observed1,*logical0,*logical1;
static unsigned char boxes_overlap(const Frame *a,unsigned char sa,unsigned char sec,const Frame *b,unsigned char sb) {
    (void)sa;(void)sec;(void)sb;observed0=a;observed1=b;return a==expected0 && b==expected1;
}
static void trace_contact(unsigned char a,unsigned char kind,const Frame *f0,const Frame *f1,unsigned char reason) {
    (void)a;(void)kind;(void)reason;logical0=f0;logical1=f1;
}
static void move_x(unsigned char d,signed int delta) {(void)d;(void)delta;}
static void set_role(unsigned char d,unsigned char role) {fighter[d].role=role;}
static void input_flush(unsigned char d) {(void)d;}
''' + extract(source, "contact_sat_ready", "unsigned char") + "\n" + extract(source, "combat_step") + r'''
#define CHECK(c,msg) do { if (!(c)) {puts(msg);return 1;} } while(0)
int main(void) {
    Frame submitted0={34}, submitted1={12}, logical_p1={35}, logical_p2={13};
    StateDef p1[10]={{0}},p2[10]={{0}};p1[7].flags=S_HIT;p1[7].dmg=112;
    characters[0].states=p1;characters[1].states=p2;characters[0].pose_base=0;characters[1].pose_base=48;
    fighter[0].role=7;fighter[1].role=2;fighter[0].life=fighter[1].life=1000;
    fighter[0].face=0;fighter[1].face=1;
    current[0]=(Slot){&submitted0,34,0,4,1};current[1]=(Slot){&submitted1,60,1,20,1};
    contact_committed[0]=(ContactStamp){&submitted0,0,4,130,0,7};
    contact_committed[1]=(ContactStamp){&submitted1,1,20,155,0,2};
    expected0=&submitted0;expected1=&submitted1;
    contact_committed[0].role=0;combat_step(&logical_p1,&logical_p2);
    CHECK(contact_sat_unready==1 && fighter[1].life==1000 && !fighter[0].hit_done,
          "stale role caused contact");
    contact_committed[0].role=7;contact_committed[1].base_pair=21;
    CHECK(!contact_sat_ready(1),"stale resident base accepted");contact_committed[1].base_pair=20;
    current[1].role_fresh=0;
    CHECK(!contact_sat_ready(1),"previous role instance accepted");current[1].role_fresh=1;
    combat_step(&logical_p1,&logical_p2);
    CHECK(contact_sat_overlaps==1 && fighter[1].life==888 && fighter[0].hit_done &&
          observed0==&submitted0 && observed1==&submitted1 &&
          logical0==&logical_p1 && logical1==&logical_p2,
          "committed and logical frames were confused");
    return 0;
}
'''
    compile_and_run(tmp_path, code)


def test_role_change_invalidates_previous_sat_snapshot(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    code = r'''
#include <stdio.h>
#define LUTA_CONTACT_STAMPS 1
#define S_AIR 2u
typedef struct { unsigned char anim,flags; } StateDef;
typedef struct { const StateDef *states; int jump_vy; } CharacterData;
typedef struct { unsigned int y; int vy; unsigned char role,anim,fidx,tick,done,hit_done; } Fighter;
typedef struct { const void *frame; } Stamp;
typedef struct { unsigned char role_fresh; } Slot;
static CharacterData characters[2];static Fighter fighter[2];
static Stamp contact_prepared[2],contact_committed[2];
static Slot current[2],pending[2];
''' + extract(source, "set_role") + r'''
int main(void) {
    StateDef states[2]={{0},{3,0}};int stale=1;
    characters[0].states=states;fighter[0].role=1;
    contact_prepared[0].frame=&stale;contact_committed[0].frame=&stale;
    current[0].role_fresh=pending[0].role_fresh=1;
    set_role(0,1);
    if (contact_prepared[0].frame || contact_committed[0].frame || fighter[0].anim!=3 ||
        current[0].role_fresh || pending[0].role_fresh) return 1;
    return 0;
}
'''
    compile_and_run(tmp_path, code)


def test_trace_separates_logical_frames_from_the_sat_collision_inputs(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    enum = re.search(r"enum \{ CT_SEQ.*?CT_BYTES = 53 \};", source, re.S)
    assert enum
    code = r'''
#include <stdint.h>
#define LUTA_CONTACT_SAT 1
#define LUTA_CONTACT_STAMPS 1
typedef struct { unsigned char pose; } Frame;
typedef struct { unsigned char pose_base; } Character;
typedef struct { unsigned short x,y; unsigned char face,role; } Fighter;
typedef struct { unsigned short pose_global; unsigned char face,role_fresh; } Slot;
typedef struct { const Frame *frame; unsigned char face,base_pair,x,y,role; } Stamp;
static Character characters[2];static Fighter fighter[2];static Slot current[2];
static Stamp contact_committed[2];static unsigned int frames;
static unsigned int probe_submit_p1,probe_submit_p2,probe_present_p1,probe_present_p2;
''' + enum.group() + r'''
volatile unsigned char contact_trace[CT_BYTES];
''' + extract(source, "contact_trace_word") + "\n" + extract(source, "trace_contact") + r'''
static unsigned short getword(unsigned char o) {return contact_trace[o] | ((unsigned short)contact_trace[o+1]<<8);}
int main(void) {
    Frame logical0={35},logical1={13},used0={34},used1={12};
    characters[1].pose_base=48;current[0].pose_global=34;current[1].pose_global=60;
    current[0].role_fresh=current[1].role_fresh=1;
    contact_committed[0]=(Stamp){&used0,0,4,130,0,7};
    contact_committed[1]=(Stamp){&used1,1,20,155,0,2};
    fighter[0].x=140u*256u;fighter[1].x=160u*256u;
    trace_contact(0,2,&logical0,&logical1,0);
    if (contact_trace[CT_SEQ]!=2 || contact_trace[CT_POLICY]!=1 ||
        getword(CT_LOGICAL_P1)!=35 || getword(CT_LOGICAL_P2)!=61 ||
        getword(CT_USED_FRAME_P1)!=((uintptr_t)&used0 & 0xffffu) ||
        getword(CT_USED_FRAME_P2)!=((uintptr_t)&used1 & 0xffffu) ||
        contact_trace[CT_USED_X_P1]!=130 || contact_trace[CT_USED_X_P2]!=155 ||
        contact_trace[CT_USED_FACE_P2]!=1 || contact_trace[CT_ROLE_FRESH_P1]!=1 ||
        contact_trace[CT_ROLE_FRESH_P2]!=1) return 1;
    return 0;
}
'''
    compile_and_run(tmp_path, code)


def test_cache_metadata_freshness_tracks_requests_and_promotion(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    code = r'''
#include <stdio.h>
#define LUTA_CONTACT_STAMPS 1
#define LUTA_SPECULATIVE_PREFETCH 0
#define LUTA_PROFILE 1
#define VERSUS_POSE_COUNT 4u
typedef struct { unsigned char id; } Frame;
typedef struct { unsigned char bank; unsigned int off,size; } PoseRef;
typedef struct { unsigned int pose_global; unsigned char base_pair,n_pairs,loaded_pairs;
                 const Frame *frame; unsigned char face,role_fresh; } CacheSlot;
static CacheSlot current[2],pending[2];static PoseRef versus_poses[4];
static unsigned char fail_valid[2],fail_size[2];
static unsigned int probe_uploaded_pairs,probe_bad_pose_ref,probe_superseded_p1,probe_superseded_p2;
static unsigned int probe_overflow_p1,probe_overflow_p2,probe_stall_frames;
static unsigned char pose_facing_offset(const PoseRef *p,unsigned char side,unsigned char face,unsigned int *off) {
    (void)side;(void)face;*off=p->off;return 1;
}
static unsigned char alloc_contiguous(unsigned char n,unsigned char *base) {(void)n;*base=8;return 1;}
#define SMS_saveROMBank() ((void)0)
#define SMS_mapROMBank(n) ((void)(n))
#define SMS_restoreROMBank() ((void)0)
#define SMS_VRAMmemcpy_brief(dst,src,size) ((void)(dst),(void)(src),(void)(size))
''' + extract(source, "cache_invalidate") + "\n" + extract(source, "stream_pending", "unsigned char") + "\n" + extract(source, "request_pose") + r'''
#define CHECK(c,msg) do { if (!(c)) {puts(msg);return 1;} } while(0)
int main(void) {
    Frame old={1},fresh={2};
    versus_poses[2]=(PoseRef){2,0,128};
    current[0]=(CacheSlot){1,0,2,2,&old,0,0};pending[0].pose_global=0xffff;
    pending[1].pose_global=current[1].pose_global=0xffff;
    request_pose(0,1,2,&fresh,0);
    CHECK(current[0].role_fresh && current[0].frame==&fresh,"current matching request not refreshed");
    pending[0]=(CacheSlot){2,2,2,0,&old,0,0};
    request_pose(0,2,2,&fresh,0);
    CHECK(pending[0].role_fresh && pending[0].frame==&fresh,"pending matching request not refreshed");
    CHECK(stream_pending(0,2)==2 && current[0].role_fresh && current[0].frame==&fresh &&
          !pending[0].role_fresh,"freshness not transferred on promotion");
    pending[0]=(CacheSlot){2,4,2,0,&old,0,0};
    CHECK(stream_pending(0,2)==2 && !current[0].role_fresh,"stale pending metadata promoted as fresh");
    cache_invalidate(&current[0]);
    request_pose(0,2,2,&fresh,0);
    CHECK(pending[0].role_fresh && pending[0].frame==&fresh,"new allocation not marked fresh");
    cache_invalidate(&pending[0]);CHECK(!pending[0].role_fresh,"invalidated slot remained fresh");
    return 0;
}
'''
    compile_and_run(tmp_path, code)
