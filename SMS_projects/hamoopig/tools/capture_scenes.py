#!/usr/bin/env python3
"""Captura title/select/fight com DAP continue (capture_evidence congela no attach)."""
import os, sys, time, subprocess, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WRAP = os.path.join(ROOT, "tools", "sms_wrapper")
sys.path.insert(0, WRAP)
from emulicious_dap import wait_port  # noqa: E402
from emulator_session import require_no_stale  # noqa: E402
import capture_evidence as CE  # noqa: E402
import emulator_input as EI  # noqa: E402

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROM = os.path.join(PROJ, "out", "rom", "hamoopig.sms")
OUT = os.path.join(PROJ, "out", "evidence")
JAR = os.path.join(ROOT, "tools", "emuladores", "emulicious", "Emulicious.jar")


def shot(name, wid):
    path = os.path.join(OUT, name)
    ok, _ = CE._shoot_window(path, wid)
    print(("PASS" if ok else "FAIL"), path)
    return ok


def main():
    os.makedirs(OUT, exist_ok=True)
    if not require_no_stale(why="hamoopig scenes"):
        return 2
    logf = open(os.path.join(OUT, "scenes_emu.log"), "w")
    proc = subprocess.Popen(
        ["java", "-jar", JAR, "-remotedebug", "4901", "-set", "Update=0", ROM],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wid = None
        for _ in range(40):
            time.sleep(0.5)
            if proc.poll() is not None:
                print("FAIL emulator exited")
                return 1
            wid = CE._main_window_id()
            if wid:
                break
        if not wid:
            print("FAIL no window")
            return 1
        time.sleep(2.0)
        dap = None
        for _ in range(4):
            cand = wait_port(timeout_s=10)
            if cand is None:
                continue
            try:
                cand.start_session()
                cand.cont()
                dap = cand
                break
            except (ConnectionError, AssertionError):
                try:
                    cand.close()
                except (OSError, ConnectionError):
                    pass
                time.sleep(2.0)
        if dap is None:
            print("WARN DAP ausente — captura so da janela")
        time.sleep(5.0)
        shot("title.png", wid)
        EI.press_spec("a=200")
        time.sleep(0.8)
        shot("select.png", wid)
        EI.press_spec("a=200")
        time.sleep(1.2)
        shot("fight.png", wid)
        time.sleep(0.55)
        shot("fight_idle_b.png", wid)
        EI.press_spec("Right=900")
        time.sleep(0.2)
        shot("fight_walk.png", wid)
        EI.press_spec("a=200")
        time.sleep(0.25)
        shot("fight_punch.png", wid)
        if dap is not None:
            dap.pause()
            frame = dap.eval_int("word.ram@@0xC7F0")
            scene = dap.eval_int("@0xC7F6")
            px = dap.eval_int("@0xC7FA")
            print(f"probe frame={frame} scene={scene} px={px}")
            dap.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
