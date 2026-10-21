"""Compile the actual C functions, not a Python reimplementation of the FSM.

Host integer ABI differs from SDCC; hardware, rendering and performance still
require the frozen ROM in Emulicious. Mutants demonstrate causal regressions.
"""
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / "SMS_projects/openbor_sms_rev1"


def audio_stub():
    """M7: o gatilho sonoro e efeito colateral; aqui vira stub para o FSM/hit/
    arco REAIS continuarem compilando. Audio se prova na ROM (captura isolada),
    nunca neste host. As prioridades sao lidas do header autoral (sem drift)."""
    header = (PROJECT / "inc/o3/psg_sfx.h").read_text()
    values = {m.group(1): m.group(2)
              for m in re.finditer(r"#define SFX_(\w+)_PRIORITY (\d+)", header)}
    for name in ("ATTACK", "IMPACT", "FALL"):
        if name not in values:
            raise AssertionError("psg_sfx.h sem SFX_%s_PRIORITY" % name)
    return ("#define SFX_ATTACK_PRIORITY %s\n"
            "#define SFX_IMPACT_PRIORITY %s\n"
            "#define SFX_FALL_PRIORITY %s\n"
            "static void sfx_request(unsigned char prio) { (void)prio; }\n"
            % (values["ATTACK"], values["IMPACT"], values["FALL"]))


def translation(source):
    defs = source[source.index("#define WORST_FRAME_WINDOW"):source.index("static unsigned char e_think;")]
    names = ["iabs", "pose_of", "pose_now", "start_anim", "actor_presented", "queue_presentation", "latch_presentation",
             "new_next_pose", "stream_update", "start_attack", "start_jump", "fsm_end", "fsm_tick", "arc_advance",
             "actor_advance", "hit_test", "apply_hit", "resolve_hits"]
    functions = []
    for name in names:
        match = re.search(r"^static [^\n]*\b" + name + r"\(", source, re.M)
        if not match:
            raise AssertionError("C function missing: " + name)
        end = source.index("\n}", match.start()) + 2
        functions.append(source[match.start():end])
    return ('#include <assert.h>\n#include <string.h>\n#include "o3/level.h"\n'
            '#include "o3/o3_poses.h"\n#include "o3/o3_blocks.h"\n'
            '#include "o3/o3_anim.h"\n#include "o3/o3_arcs.h"\n'
            + defs + "\n" + audio_stub() + "\n" + "\n".join(functions))


class RuntimeC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compiler = shutil.which("cc")
        if not cls.compiler:
            raise unittest.SkipTest("host C compiler unavailable")
        cls.source = (PROJECT / "src/main.c").read_text()

    def compile_run(self, body, source=None):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "trial.c"
            exe = Path(tmp) / "trial"
            src.write_text(translation(source or self.source) + r'''
static void setup(void) {
 memset(&pl,0,sizeof(pl)); memset(&e,0,sizeof(e));
 pl.as=&pl_as; pl.art=&pl_art; e.as=&en_as; e.art=&en_art;
 pl.hp=100; e.hp=50; pl.facing=1; pl.x=100; e.x=125;
 pl.z=e.z=180; pl.up_pose=e.up_pose=255;
 pl.slot_pose[0]=pl.slot_pose[1]=e.slot_pose[0]=e.slot_pose[1]=255;
 start_anim(&pl,pl.as->idle); start_anim(&e,e.as->idle);
}
static void present(o3_actor *a) {
 a->disp_pose=pose_now(a); queue_presentation(a); latch_presentation(a);
}
int main(void) { setup();
''' + body + "\nreturn 0; }\n")
            built = subprocess.run([self.compiler, "-std=c99", "-I", str(PROJECT / "inc"), str(src), "-o", str(exe)], capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stderr)
            return subprocess.run([str(exe)], capture_output=True, text=True)

    def check(self, body):
        result = self.compile_run(body)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_resident_timing_initial_boundaries_terminal(self):
        body = '''
start_attack(&pl);
for(int i=0;i<21;i++) {
 present(&pl);
 assert(pl.state==O3_S_ATTACK);
 assert(pl.frame==(i<3?0:i<6?1:i<9?2:i<12?3:4));
 actor_advance(&pl);
}
assert(pl.state==O3_S_IDLE); assert(pl.frame==0);
'''
        self.check(body)
        mutant = self.source.replace("if (a->timer)\n            return;", "return;", 1)
        self.assertNotEqual(self.compile_run(body, mutant).returncode, 0)

    def test_no_future_or_abandoned_activation_hit(self):
        self.check('''
start_attack(&pl); present(&pl);
pl.frame=1; pl.disp_pose=pose_now(&pl);
resolve_hits(); assert(e.hp==50); /* not in this frame's SAT */
queue_presentation(&pl); resolve_hits(); assert(e.hp==50);
latch_presentation(&pl); resolve_hits(); assert(e.hp==43);
resolve_hits(); assert(e.hp==43); /* consumed once */
pl.hit_used=0; pl.hitstop=0; e.guard=0;
start_anim(&pl,pl.as->attack); pl.frame=1;
resolve_hits(); assert(e.hp==43); /* prior activation invalid */
''')

    def test_guard_expires_even_io_or_hitstop(self):
        body = '''pl.guard=13; pl.hitstop=20; pl.disp_pose=255;
for(int i=0;i<13;i++) actor_advance(&pl);
assert(pl.guard==0); assert(pl.hitstop==7);'''
        self.check(body)
        self.assertNotEqual(self.compile_run(body,self.source.replace("a->guard--;", "a->guard = a->guard;",1)).returncode,0)

    def test_toss_continuity_height_envelope_and_rehit_death(self):
        self.check('''
int heights[]={0,1,46,47,55,200};
for(int j=0;j<6;j++) {
 setup(); e.alt=heights[j]; e.arc=O3_ARC_JUMP; e.state=O3_S_FALL;
 if(!e.alt) e.hp=1; /* ground lethal selects toss */
 apply_hit(&pl,&e,&o3_ax_attack,O3_HITSTOP_AX);
 assert(e.alt==heights[j]); assert(e.arc==O3_ARC_TOSS);
 int prev=e.alt, calls=0;
 while(e.arc) {
  arc_advance(&e); int dy=(int)e.alt-prev;
  assert(dy>=-6 && dy<=6); prev=e.alt; assert(++calls<90);
 }
 assert(e.alt==0); assert(e.frame==e.as->tbl[e.as->fall].land);
}
setup(); e.alt=55; apply_hit(&pl,&e,&o3_ax_attack,5);
arc_advance(&e); int h=e.alt,t=e.arc_t; e.hp=1;
apply_hit(&pl,&e,&o3_ax_attack,5);
assert(e.alt==h && e.arc_t==t && e.dead);
''')

    def test_cancel_complete_and_partial_slot_invalidation(self):
        body = '''
present(&pl); unsigned char old=pose_now(&pl);
start_attack(&pl); stream_update(&pl);
unsigned char abandoned=pl.up_pose;
pl.up_done=1; start_anim(&pl,pl.as->pain); stream_update(&pl);
assert(pl.disp_pose==old); assert(pl.disp_pose!=abandoned);
assert(pl.up_pose==pose_now(&pl));
assert(pl.slot_pose[pl.up_slot]==255);
pl.facing=0; stream_update(&pl);
assert(pl.up_pose==pose_now(&pl)); assert(pl.up_off==0);
pl.up_done=1; stream_update(&pl);
assert(pl.disp_pose==pose_now(&pl));
assert(pl.up_pose==255 || pl.up_slot!=pl.disp);
'''
        self.check(body)
        mutant=self.source.replace("if (a->up_pose == want) {","if (a->up_want || a->up_pose == want) {",1)
        self.assertNotEqual(self.compile_run(body,mutant).returncode,0)

    def test_depth_sign_facing_and_altitude_boundaries(self):
        self.check('''
for(int facing=0;facing<2;facing++) for(int sign=-1;sign<=1;sign+=2)
 for(int dz=14;dz<=16;dz++) {
  setup(); pl.facing=facing; e.x=pl.x+(facing?25:-25); e.z=180+sign*dz;
  assert(hit_test(&pl,&e,&o3_ax_attack)==(dz<=15));
 }
setup(); e.alt=55; assert(hit_test(&pl,&e,&o3_ax_attack)); /* inclusive border */
e.alt=56; assert(!hit_test(&pl,&e,&o3_ax_attack)); e.alt=55;
pl.alt=55; assert(hit_test(&pl,&e,&o3_ax_attack));
e.alt=200; assert(!hit_test(&pl,&e,&o3_ax_attack));
''')


if __name__ == "__main__":
    unittest.main()
