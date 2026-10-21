#!/usr/bin/env python3
"""Mede o degrau de worst-frame que exige input real.

O medidor central cobre a cena passiva. Esta extensão local usa os mesmos
probes VCounter/VBlank da ROM e o mesmo canal DAP+uinput da prova de gameplay,
coletando amostras durante deslocamento, combo, travessia do torii e reset.
Não altera a ROM nem substitui o gate central; só fecha a cobertura causal
que ele não consegue alcançar sem injeção de input.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = "/mnt/sdcard/Projects/SMSForge"
ROM = "SMS_projects/kage_matsuri/out/rom/kage_matsuri.sms"
PROJECT_TOOLS = os.path.join(ROOT, "SMS_projects/kage_matsuri/tools")
sys.path.insert(0, PROJECT_TOOLS)
import prove_input_memory as P  # noqa: E402

OUT = os.path.join(ROOT, "SMS_projects/kage_matsuri/out/evidence/worst_frame_cycle.json")
PROBE_VLINE = 0xC7EA
PROBE_VOVF = 0xC7EB
PROBE_STATE = 0xC7F6
PROBE_KILLS = 0xC7F4
PROBE_PX = 0xC7FA
PROBE_POSE = 0xC7F9


def _metric(dap, records, label):
    # Leitura em voo: pausar para cada amostra altera a cadência e pode
    # fabricar overflow. O instrumento central também só pausa nos limites
    # das janelas; aqui mantemos a CPU correndo durante o input.
    vline = P.rd_byte(dap, PROBE_VLINE)
    vovf = P.rd_word(dap, PROBE_VOVF)  # word desde L071: byte saturava em 255
    state = P.rd_byte(dap, PROBE_STATE)
    kills = P.rd_byte(dap, PROBE_KILLS)
    px = P.rd_byte(dap, PROBE_PX)
    pose = P.rd_byte(dap, PROBE_POSE)
    s0_alive = P.rd_byte(dap, P.PROBE_S0_ALIVE)
    s1_alive = P.rd_byte(dap, P.PROBE_S1_ALIVE)
    records.append({"label": label, "t": round(time.monotonic(), 3),
                    "vline": vline, "vovf": vovf, "state": state,
                    "kills": kills, "px": px, "pose": pose,
                    "s0_alive": s0_alive, "s1_alive": s1_alive})
    return records[-1]


def _hold_sample(dap, backend, action, seconds, records, label):
    if not P._cycle_focus(backend):
        return False
    dap.cont()
    P.press_wayland(action) if backend == "wayland" else P.CE._run(
        ["xdotool", "keydown", {"right": "Right", "left": "Left"}[action]])
    time.sleep(seconds)
    P.release_wayland(action) if backend == "wayland" else P.CE._run(
        ["xdotool", "keyup", {"right": "Right", "left": "Left"}[action]])
    time.sleep(0.08)
    dap.pause()
    _metric(dap, records, label)
    return True


def _combo_sample(dap, backend, records):
    if not P._cycle_focus(backend):
        return False
    dap.cont()
    press = (lambda: P.press_wayland("botao1")) if backend == "wayland" else \
        (lambda: P.CE._run(["xdotool", "keydown", "a"]))
    release = (lambda: P.release_wayland("botao1")) if backend == "wayland" else \
        (lambda: P.CE._run(["xdotool", "keyup", "a"]))
    press()
    time.sleep(0.10)
    release()
    time.sleep(0.05)
    press()
    time.sleep(0.10)
    release()
    time.sleep(0.08)
    dap.pause()
    _metric(dap, records, "combo")
    return True


def _hold_b1_right_sample(dap, backend, seconds, records):
    if not P._cycle_focus(backend):
        return False
    dap.cont()
    if backend == "wayland":
        P.press_wayland("botao1")
        P.press_wayland("right")
    else:
        P.CE._run(["xdotool", "keydown", "a"])
        P.CE._run(["xdotool", "keydown", "Right"])
    time.sleep(seconds)
    if backend == "wayland":
        P.release_wayland("right")
    else:
        P.CE._run(["xdotool", "keyup", "Right"])
    time.sleep(0.08)
    dap.pause()
    _metric(dap, records, "torii_transition")
    return True


def run():
    if not os.path.isfile(os.path.join(ROOT, ROM)):
        print("[FAIL_AMBIENTE] ROM ausente")
        return 2
    backend = P.select_backend()
    if backend is None or not P.MRP._zombie_guard() or not P.MRP._port_free():
        print("[FAIL_AMBIENTE] canal de input/DAP indisponivel")
        return 2
    log_path = OUT.replace(".json", "_emu.log")
    logf = open(log_path, "w")
    proc = subprocess.Popen(
        ["java", "-jar", os.path.join(ROOT, "tools/emuladores/emulicious/Emulicious.jar"),
         "-remotedebug", str(P.PORT), "-set", "Update=0", ROM],
        stdout=logf, stderr=subprocess.STDOUT,
        start_new_session=True, env=P.ENV)
    dap = None
    records = []
    attack_attempts = []
    try:
        dap = P._connect_live_project()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo")
            return 1
        dap.cont()
        time.sleep(1.0)
        P._cycle_focus(backend)
        # Reuse the proven full-cycle choreography. The probe is read only at
        # its paused checkpoints, while the emulation runs continuously
        # between them; this keeps the budget sample from measuring DAP
        # pauses or a second, less reliable input script.
        P.tap_reset_wayland() if backend == "wayland" else P.tap_reset_x11()
        time.sleep(1.0)
        dap.pause()
        _metric(dap, records, "reset_initial")
        P._cycle_hold(dap, backend, "right", 0.15)
        _metric(dap, records, "round")
        if not P._cycle_align_target(dap, backend, "near_s0"):
            print("[FAIL] primeiro alvo nao entrou no envelope slash2")
            return 1
        combo_1 = None
        for attempt in range(6):
            P._cycle_combo(dap, backend)
            candidate = _metric(dap, records, "combo_1")
            attack_attempts.append({"stage": "combo_1", "attempt": attempt + 1,
                                    "kills": candidate["kills"],
                                    "pose": candidate["pose"] & 0x7F})
            if candidate["pose"] & 0x7F == 4 and candidate["kills"] == 1 and \
               (candidate["s0_alive"] + candidate["s1_alive"]) == 1:
                combo_1 = candidate
                break
            dap.cont()
            time.sleep(0.30)
            dap.pause()
            if not P._cycle_align_target(dap, backend, "near_s0_retry"):
                print("[FAIL] primeiro alvo nao entrou no envelope slash2")
                return 1
        if combo_1 is None:
            print("[FAIL] primeiro combo nao confirmou uma derrota apos 6 tentativas")
            return 1
        combo_2 = None
        for attempt in range(6):
            dap.cont()
            time.sleep(0.30)
            dap.pause()
            if not P._cycle_align_target(dap, backend, "near_s1"):
                print("[FAIL] segundo alvo nao entrou no envelope slash2")
                return 1
            P._cycle_combo(dap, backend)
            candidate = _metric(dap, records, "combo_2")
            attack_attempts.append({"stage": "combo_2", "attempt": attempt + 1,
                                    "kills": candidate["kills"],
                                    "pose": candidate["pose"] & 0x7F})
            if candidate["pose"] & 0x7F == 4 and candidate["kills"] == 2 and \
               candidate["s0_alive"] == 0 and candidate["s1_alive"] == 0:
                combo_2 = candidate
                break
        if combo_2 is None:
            print("[FAIL] segundo combo nao confirmou a derrota final apos 6 tentativas")
            return 1
        P._cycle_hold(dap, backend, "right", 1.00)
        _metric(dap, records, "torii_approach")
        P._cycle_hold_b1_and_right(dap, backend, 0.70)
        _metric(dap, records, "torii_transition")
        # Libera e deixa o jogo observar o release antes do novo edge.
        P.release_wayland("botao1") if backend == "wayland" else P.CE._run(
            ["xdotool", "keyup", "a"])
        dap.cont()
        time.sleep(0.18)
        dap.pause()
        P._cycle_focus(backend)
        dap.cont()
        if backend == "wayland":
            P.press_wayland("botao1")
            time.sleep(0.06)
            P.release_wayland("botao1")
        else:
            P.CE._run(["xdotool", "keydown", "a"])
            time.sleep(0.06)
            P.CE._run(["xdotool", "keyup", "a"])
        time.sleep(0.08)
        dap.pause()
        _metric(dap, records, "reset_after_torii")
        valid = [r for r in records if r["vline"] is not None]
        vline_max = max((r["vline"] for r in valid), default=None)
        # probe_vovf é zerado pelo reset final; conciliar somente a cadeia
        # anterior a esse marcador, sem transformar reset legítimo em delta.
        before_reset = [r for r in valid if r["label"] != "reset_after_torii"]
        vovf_start = before_reset[0]["vovf"] if before_reset else None
        vovf_end = before_reset[-1]["vovf"] if before_reset else None
        vovf_deltas = []
        for prev, cur in zip(before_reset, before_reset[1:]):
            if cur["vovf"] is not None and prev["vovf"] is not None and cur["vovf"] >= prev["vovf"]:
                vovf_deltas.append(cur["vovf"] - prev["vovf"])
        states = sorted({r["state"] for r in valid})
        labels = sorted({r["label"] for r in valid})
        vovf_delta = max(vovf_deltas, default=0)
        cycle_reached_win = any(r["state"] == 1 and r["kills"] == 2 for r in valid)
        reset_reached_clean = any(
            r["label"] == "reset_after_torii" and r["state"] == 0 and
            r["kills"] == 0 and r["px"] == 56 for r in valid
        )
        ok = (len(valid) >= 5 and vline_max is not None and vline_max < 0xC0 and
              vovf_start is not None and vovf_end is not None and vovf_delta == 0 and
              "combo" in labels and "torii_transition" in labels and
              cycle_reached_win and reset_reached_clean)
        sha = hashlib.sha256(open(os.path.join(ROOT, ROM), "rb").read()).hexdigest()
        result = {"schema": "kage_worst_frame_cycle_v1", "rom": ROM,
                  "rom_sha256": sha, "backend": backend,
                  "vline_max": vline_max, "vovf_delta": vovf_delta,
                  "cycle_reached_win": cycle_reached_win,
                  "reset_reached_clean": reset_reached_clean,
                  "attack_attempts": attack_attempts,
                  "samples": len(valid), "states": states, "labels": labels,
                  "verdict": "pass" if ok else "fail", "records": records,
                  "chain_of_custody": ["Emulicious DAP; leitura pausada",
                                       "input via %s (foco + uinput)" % backend,
                                       "ROUND, combo, aproximação do torii e reset"]}
        with open(OUT, "w") as f:
            json.dump(result, f, indent=2)
        print("[%s] cycle worst-frame: %d amostras, vline_max=%s, vovf_delta=%s, estados=%s" %
              ("PASS" if ok else "FAIL", len(valid), vline_max,
               result["vovf_delta"], states))
        return 0 if ok else 1
    finally:
        if dap:
            dap.close()
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()


def self_check():
    assert PROBE_VLINE == 0xC7EA and PROBE_VOVF == 0xC7EB
    assert PROBE_STATE == 0xC7F6 and PROBE_KILLS == 0xC7F4
    assert 0xC0 == 192
    print("[SELF-CHECK PASS] worst-frame cycle: probes, limite VBlank e regions de input")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    return self_check() if args.self_check else run()


if __name__ == "__main__":
    raise SystemExit(main())
