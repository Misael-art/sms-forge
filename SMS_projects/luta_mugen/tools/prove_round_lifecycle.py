#!/usr/bin/env python3
"""RAM-backed proof of KO and round reset for the current luta_mugen ROM.

Run from the workspace root:
  python3 SMS_projects/luta_mugen/tools/prove_round_lifecycle.py \
      --rom SMS_projects/luta_mugen/out/rom/luta_mugen.sms
  python3 SMS_projects/luta_mugen/tools/prove_round_lifecycle.py --self-check

The helper proves one P1 win: P2 life reaches zero, `round_over` rises, then
the next round restores both lives and increments P1's round-win nibble.
Pixels and the emulator title are not used as proof.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools", "sms_wrapper"))
sys.path.insert(0, TOOLS)

import capture_evidence as CE
import emulator_input as EI
import measure_runtime_probe as MRP
from emulicious_dap import PORT

ROM_REL = "SMS_projects/luta_mugen/out/rom/luta_mugen.sms"
OUT_REL = "SMS_projects/luta_mugen/out/evidence/t10_round_lifecycle.json"
LOG_REL = "SMS_projects/luta_mugen/out/evidence/t10_round_lifecycle_emu.log"

P_FRAME = 0xC7F0
P_HP = 0xC7F2
P_SCORE = 0xC7F3
P_BOSS = 0xC7F4
P_OVER = 0xC7F5
P_STATE = 0xC7F6
P_WAVE = 0xC7F7
P_KEYS = 0xC7F8
P_PX = 0xC7FA
P_P2X = 0xC7FC
P_ROUND_SCORE = 0xC7FE
P_TIMER = 0xC7FF
ST_IDLE = 0
ATTRACT_END = 1400
GAP_MIN = 8
GAP_MAX = 16
MAX_ATTACK_ATTEMPTS = 32


def gap_in_range(px, p2x, gap_min=GAP_MIN, gap_max=GAP_MAX):
    if px is None or p2x is None or px >= p2x:
        return False
    return gap_min <= p2x - px <= gap_max


def ko_observed(over, boss_life):
    return over == 1 and boss_life == 0


def attract_complete(frame, wave):
    return frame is not None and frame >= ATTRACT_END and wave == 1


def life_damage_delta(before, after):
    """Byte-sized probe delta, including wrap at 256/512/768 life."""
    if before is None or after is None:
        return None
    delta = (before - after) & 0xFF
    return delta if 0 < delta <= 128 else 0


def round_reset_observed(over, boss_life, max_life_low, wins_before,
                         packed_wins, player_life):
    wins_after = packed_wins & 0x0F
    return (over == 0 and boss_life == max_life_low and
            wins_after == ((wins_before + 1) & 0x0F) and player_life > 0)


def _max_life_low():
    header = ("SMS_projects/luta_mugen/out/local_study/generated/versus_cut/"
              "versus_scene_runtime.h")
    try:
        source = open(header, encoding="utf-8").read()
    except OSError as exc:
        raise RuntimeError("header Ryu gerado ilegível: %s" % exc)
    match = re.search(r"^#define\s+RYU_CUT_MAX_LIFE\s+(\d+)\s*$",
                      source, re.M)
    if not match:
        raise RuntimeError("RYU_CUT_MAX_LIFE ausente no header gerado")
    return int(match.group(1)) & 0xFF


def _sample(dap, *addresses):
    if dap.pause() is None:
        return None
    values = tuple(dap.read_byte(addr) for addr in addresses)
    dap.cont()
    return values if all(v is not None for v in values) else None


def _read_frame(dap):
    """Read only the 16-bit frame counter while the CPU is paused."""
    if dap.pause() is None:
        return None
    value = dap.read_word(P_FRAME)
    dap.cont()
    return value


def _set_key(tecla, down, backend):
    if backend == "wayland":
        EI.ydotool_key(EI.EVDEV[tecla], down)
    elif down:
        CE._run(["xdotool", "keydown", tecla])
    else:
        CE._run(["xdotool", "keyup", tecla])


def _wait_idle(dap, timeout=2.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        vals = _sample(dap, P_STATE)
        if vals is None:
            return False, last
        last = vals[0]
        if last == ST_IDLE:
            return True, last
        time.sleep(0.05)
    return False, last


def _position(dap):
    vals = _sample(dap, P_PX, P_P2X)
    return vals if vals is not None else (None, None)


def _approach(dap, backend, trace, timeout=8.0):
    deadline = time.time() + timeout
    for _ in range(40):
        if time.time() >= deadline:
            break
        px, p2x = _position(dap)
        if gap_in_range(px, p2x):
            return True, p2x - px
        if px is None or p2x is None:
            return False, None
        key = "Right" if p2x - px > GAP_MAX else "Left"
        trace.append({"px": px, "p2x": p2x, "gap": p2x - px, "key": key})
        _set_key(key, True, backend)
        dap.cont()
        time.sleep(0.08)
        _set_key(key, False, backend)
        _wait_idle(dap, timeout=1.0)
    px, p2x = _position(dap)
    return gap_in_range(px, p2x), (p2x - px) if px is not None and p2x is not None else None


def _attack(dap, backend, max_hold=1.0):
    if dap.pause() is None:
        return {"error": "DAP não pausou para baseline"}
    baseline = {"hp": dap.read_byte(P_HP), "boss": dap.read_byte(P_BOSS),
                "score": dap.read_byte(P_SCORE), "state": dap.read_byte(P_STATE),
                "px": dap.read_byte(P_PX), "p2x": dap.read_byte(P_P2X),
                "over": dap.read_byte(P_OVER)}
    # Score is not in the six-byte probe snapshot; round-win count is read as
    # the independent corroboration for KO/reset instead.
    if any(v is None for v in baseline.values()):
        dap.cont()
        return {"error": "baseline DAP incompleto", "baseline": baseline}
    gap = baseline["p2x"] - baseline["px"]
    baseline["gap"] = gap
    baseline["range_valid"] = gap_in_range(baseline["px"], baseline["p2x"])
    if not baseline["range_valid"] or baseline["state"] != ST_IDLE:
        dap.cont()
        return {"baseline": baseline, "keys": 0, "hit": False,
                "reason": "baseline fora de alcance ou P1 não IDLE"}

    _set_key("a", True, backend)
    dap.cont()
    keys = 0
    boss_after = baseline["boss"]
    hp_after = baseline["hp"]
    score_after = baseline["score"]
    over_after = baseline["over"]
    deadline = time.time() + max_hold
    while time.time() < deadline:
        time.sleep(0.05)
        vals = _sample(dap, P_KEYS, P_BOSS, P_HP, P_OVER, P_SCORE)
        if vals is None:
            break
        keys |= vals[0]
        boss_after, hp_after, over_after, score_after = vals[1], vals[2], vals[3], vals[4]
        if life_damage_delta(baseline["boss"], boss_after) or over_after:
            break
    _set_key("a", False, backend)
    # Let the attack animation and any KO transition finish before retrying.
    time.sleep(0.15)
    delta = life_damage_delta(baseline["boss"], boss_after)
    return {"baseline": baseline, "keys": keys, "boss_after": boss_after,
            "hp_after": hp_after, "over_after": over_after,
            "score_after": score_after, "life_damage_delta_mod256": delta,
            "hit": bool(keys & 0x10 and delta and score_after != baseline["score"]),
            "reason": "damage" if delta and score_after != baseline["score"] else "no damage"}


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def run(rom):
    if EI.select_backend() is None:
        print("[FAIL_AMBIENTE] sem canal de input")
        return 2, None
    jar = CE.resolve_jar()
    if not jar or not shutil.which("java"):
        print("[FAIL_AMBIENTE] Emulicious.jar ou java ausente")
        return 2, None
    if not MRP._zombie_guard() or not MRP._port_free():
        return 2, None

    os.makedirs(os.path.dirname(OUT_REL), exist_ok=True)
    logf = open(LOG_REL, "w")
    proc = subprocess.Popen(["java", "-jar", jar, "-remotedebug", str(PORT),
                             os.path.abspath(rom)],
                            stdout=logf, stderr=subprocess.STDOUT,
                            start_new_session=True, env=EI.ENV)
    dap = None
    report = {"schema": "luta_round_lifecycle_v1", "rom": rom,
              "rom_sha256": _sha(rom), "region": "NTSC",
              "input_backend": EI.select_backend(), "attempts": [],
              "ko": None, "round_reset": None, "passed": False}
    try:
        dap = MRP._connect_live()
        if dap is None:
            print("[FAIL] canal DAP não conectou")
            return 1, report
        report["chain_of_custody"] = [
            "launch Emulicious -remotedebug 4901 com ROM whitelist",
            "reset Ctrl+BackSpace; canário probe_frame confirma boot novo",
            "teclas pelo canal emulator_input.py; estados pela RAM SMRT",
            "P2 life-zero → round_over → round score e life reset lidos via DAP",
        ]

        focused = False
        for _ in range(3):
            if EI.select_backend() == "wayland":
                focused = EI.focus_wayland()
            else:
                wid = CE._main_window_id()
                iid = CE._input_window_id(wid) if wid else None
                focused = bool(wid) and EI.focus_x11(wid, iid)
            if focused:
                break
            time.sleep(0.5)
        report["focus"] = focused
        if not focused:
            print("[FAIL] janela Emulicious não ganhou foco")
            return 1, report

        dap.cont()
        time.sleep(2.0)
        dap.pause()
        frame_before = dap.read_word(P_FRAME)
        dap.cont()
        EI.tap_reset()
        time.sleep(1.2)
        dap.pause()
        frame_reset = dap.read_word(P_FRAME)
        canary = (frame_before is not None and frame_reset is not None and
                  frame_reset < frame_before)
        report["boot_canary"] = {"frame_before": frame_before,
                                  "frame_after_reset": frame_reset,
                                  "live": canary}
        if not canary:
            print("[FAIL] reset/canário do canal input falhou")
            return 1, report

        expected_life = _max_life_low()
        initial = _sample(dap, P_HP, P_BOSS, P_OVER, P_ROUND_SCORE, P_WAVE)
        if initial is None:
            print("[FAIL] leitura SMRT inicial falhou")
            return 1, report
        # _sample leaves the emulator running; let the attract demo complete
        # before taking manual control, matching the canonical input proof.
        deadline = time.time() + 75.0
        attract_snapshot = None
        attract_frame = None
        while time.time() < deadline:
            frame = _read_frame(dap)
            if frame is None:
                break
            attract_frame = frame
            if frame >= ATTRACT_END:
                vals = _sample(dap, P_WAVE, P_BOSS, P_OVER, P_ROUND_SCORE)
                if vals is not None:
                    attract_snapshot = (frame,) + vals
                break
            time.sleep(0.1)
        if not attract_snapshot or not attract_complete(attract_snapshot[0],
                                                        attract_snapshot[1]):
            report["attract_wait_last"] = {"frame": attract_frame,
                                            "snapshot": attract_snapshot}
            print("[FAIL] atração não completou dentro de 75 s")
            return 1, report
        report["attract_end"] = {"frame": attract_snapshot[0],
                                 "wave": attract_snapshot[1],
                                 "boss_life": attract_snapshot[2],
                                 "over": attract_snapshot[3],
                                 "round_score": attract_snapshot[4]}

        # Any physical pad input ends the demo. Move once, release, then
        # position by freshly sampled RAM values before each punch.
        if EI.select_backend() == "wayland":
            focused = EI.focus_wayland()
        else:
            wid = CE._main_window_id()
            iid = CE._input_window_id(wid) if wid else None
            focused = bool(wid) and EI.focus_x11(wid, iid)
        report["focus_before_play"] = focused
        if not focused:
            print("[FAIL] foco perdido antes do controle manual")
            return 1, report
        _set_key("Right", True, EI.select_backend())
        dap.cont()
        time.sleep(0.18)
        _set_key("Right", False, EI.select_backend())
        _wait_idle(dap, timeout=2.0)

        wins_before = attract_snapshot[4] & 0x0F
        report["round_wins_before"] = wins_before
        for attempt in range(1, MAX_ATTACK_ATTEMPTS + 1):
            status = _sample(dap, P_BOSS, P_OVER, P_HP)
            if status is None:
                report["attempts"].append({"attempt": attempt,
                                           "error": "leitura de estado falhou"})
                break
            boss, over, hp = status
            if over:
                break
            trace = []
            in_range, gap = _approach(dap, EI.select_backend(), trace)
            if not in_range:
                report["attempts"].append({"attempt": attempt,
                                           "range_trace": trace,
                                           "gap": gap,
                                           "error": "não chegou ao alcance"})
                continue
            hit = _attack(dap, EI.select_backend())
            report["attempts"].append({"attempt": attempt,
                                       "range_trace": trace, **hit})
            if hit.get("error"):
                break
            _wait_idle(dap, timeout=2.0)

        # Confirm KO while `round_over` is still high, then watch the 180-frame
        # intermission and require a fresh life pool plus the first P1 win.
        ko_snapshot = None
        deadline = time.time() + 8.0
        while time.time() < deadline:
            vals = _sample(dap, P_OVER, P_BOSS, P_HP, P_ROUND_SCORE, P_TIMER)
            if vals is None:
                break
            ko_snapshot = vals
            if ko_observed(vals[0], vals[1]):
                break
            time.sleep(0.1)
        report["ko"] = ({"over": ko_snapshot[0], "boss_life": ko_snapshot[1],
                         "player_life": ko_snapshot[2], "round_score": ko_snapshot[3],
                         "timer": ko_snapshot[4],
                         "confirmed": ko_observed(ko_snapshot[0], ko_snapshot[1])}
                        if ko_snapshot else {"confirmed": False})
        if not report["ko"].get("confirmed"):
            print("[FAIL] KO não observado via RAM")
            return 1, report

        ko_wins = ko_snapshot[3] & 0x0F
        reset_snapshot = None
        deadline = time.time() + 10.0
        while time.time() < deadline:
            vals = _sample(dap, P_OVER, P_BOSS, P_HP, P_ROUND_SCORE, P_TIMER)
            if vals is None:
                break
            reset_snapshot = vals
            if round_reset_observed(vals[0], vals[1], expected_life,
                                    ko_wins, vals[3], vals[2]):
                break
            time.sleep(0.1)
        reset_ok = bool(reset_snapshot and round_reset_observed(
            reset_snapshot[0], reset_snapshot[1], expected_life,
            ko_wins, reset_snapshot[3], reset_snapshot[2]))
        report["round_reset"] = ({"over": reset_snapshot[0],
                                  "boss_life": reset_snapshot[1],
                                  "player_life": reset_snapshot[2],
                                  "round_score": reset_snapshot[3],
                                  "timer": reset_snapshot[4],
                                  "expected_boss_life_low_byte": expected_life,
                                  "confirmed": reset_ok}
                                 if reset_snapshot else {"confirmed": False})
        report["passed"] = bool(report["ko"].get("confirmed") and reset_ok)
        json.dump(report, open(OUT_REL, "w"), indent=2)
        print("[%s] KO=%s reset_round=%s attempts=%s; relatório=%s" %
              ("PASS" if report["passed"] else "FAIL",
               report["ko"].get("confirmed"), reset_ok,
               len(report["attempts"]), OUT_REL))
        return (0 if report["passed"] else 1), report
    finally:
        if dap is not None:
            dap.close()
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        logf.close()


def self_check():
    assert gap_in_range(100, 108)
    assert gap_in_range(100, 116)
    assert not gap_in_range(100, 117)
    assert not gap_in_range(116, 100)
    assert ko_observed(1, 0)
    assert not ko_observed(0, 0)
    assert attract_complete(1400, 1)
    assert not attract_complete(255, 1)  # frame é 16-bit, não byte
    assert life_damage_delta(120, 70) == 50
    assert life_damage_delta(20, 226) == 50  # 276 -> 226, byte wraps
    assert life_damage_delta(10, 10) == 0
    assert round_reset_observed(0, 232, 232, 0, 1, 232)
    assert not round_reset_observed(1, 232, 232, 0, 1, 232)
    assert not round_reset_observed(0, 0, 232, 0, 1, 232)
    assert _max_life_low() == 232
    print("[SELF-CHECK PASS] round lifecycle: alcance, KO e reset após vitória")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rom")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        return self_check()
    if args.rom not in (ROM_REL, "out/rom/luta_mugen.sms"):
        print("[FAIL_AMBIENTE] --rom fora da whitelist do projeto")
        return 3
    if not os.path.isfile(ROM_REL):
        print("[FAIL_AMBIENTE] rode da raiz do workspace")
        return 2
    try:
        code, _ = run(ROM_REL)
        if _ is not None:
            json.dump(_, open(OUT_REL, "w"), indent=2)
        return code
    except (BrokenPipeError, ConnectionError, OSError, RuntimeError) as exc:
        print("[FAIL_AMBIENTE] medição encerrada: %s" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
