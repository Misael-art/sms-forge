#!/usr/bin/env python3
"""RAM-backed proof (sessao privada Emulicious; duracoes em frames do VDP) of KO and round reset for the current luta_mugen ROM.

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
import sys

TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools", "sms_wrapper"))
sys.path.insert(0, TOOLS)

import session_consumer as SC  # sessao privada: sem teclado, foco ou DAP do desktop (§93/L057)

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
        raise RuntimeError("header P2 gerado ilegível: %s" % exc)
    match = re.search(r"^#define\s+P2_CUT_MAX_LIFE\s+(\d+)\s*$",
                      source, re.M)
    if not match:
        raise RuntimeError("P2_CUT_MAX_LIFE ausente no header gerado")
    return int(match.group(1)) & 0xFF


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()



def _wait_idle(s, max_frames=400, chunk=4):
    st = s.byte(P_STATE)
    done = 0
    while st != ST_IDLE and done < max_frames:
        s.hold(0, 0, chunk)
        done += chunk
        st = s.byte(P_STATE)
    return st == ST_IDLE


def _approach(s, trace):
    for _ in range(40):
        px, p2x = s.byte(P_PX), s.byte(P_P2X)
        if gap_in_range(px, p2x):
            return True, p2x - px
        key = "Right" if p2x - px > GAP_MAX else "Left"
        trace.append({"px": px, "p2x": p2x, "gap": p2x - px, "key": key})
        s.hold(SC.R if key == "Right" else SC.L, 0, 4)
        s.hold(0, 0, 0)
        _wait_idle(s, 60)
    px, p2x = s.byte(P_PX), s.byte(P_P2X)
    return gap_in_range(px, p2x), p2x - px


def _attack(s):
    base = {"hp": s.byte(P_HP), "boss": s.byte(P_BOSS), "score": s.byte(P_SCORE), "state": s.byte(P_STATE),
            "px": s.byte(P_PX), "p2x": s.byte(P_P2X), "over": s.byte(P_OVER)}
    base["gap"] = base["p2x"] - base["px"]
    base["range_valid"] = gap_in_range(base["px"], base["p2x"])
    if not base["range_valid"] or base["state"] != ST_IDLE:
        return {"baseline": base, "keys": 0, "hit": False, "reason": "baseline fora de alcance ou P1 não IDLE"}
    r = s.hold(SC.B1, 0, 4)
    keys = s.byte(P_KEYS)
    s.hold(0, 0, 0)
    ko_snap = None
    for _ in range(100):     # dano/KO chegam no fim da animacao do golpe; round_over dura ~180 frames
        snap = (s.byte(P_OVER), s.byte(P_BOSS), s.byte(P_HP), s.byte(P_ROUND_SCORE), s.byte(P_TIMER))
        if ko_observed(snap[0], snap[1]):
            ko_snap = snap
            break
        if s.byte(P_STATE) == ST_IDLE:
            break
        s.hold(0, 0, 4)
    boss, hp, over, score = s.byte(P_BOSS), s.byte(P_HP), s.byte(P_OVER), s.byte(P_SCORE)
    delta = life_damage_delta(base["boss"], boss)
    return {"baseline": base, "keys": keys, "ack_porta": r.get("emulator_input"), "boss_after": boss,
            "hp_after": hp, "over_after": over, "score_after": score, "life_damage_delta_mod256": delta,
            "hit": bool(keys & 0x10 and delta and score != base["score"]), "ko_snapshot": ko_snap,
            "reason": "damage" if delta and score != base["score"] else "no damage"}


def run(rom):
    os.makedirs(os.path.dirname(OUT_REL), exist_ok=True)
    report = {"schema": "luta_round_lifecycle_v2_session", "rom": rom, "rom_sha256": _sha(rom),
              "region": "NTSC", "attempts": [], "ko": None, "round_reset": None, "passed": False,
              "chain_of_custody": [
                  "sessao privada Emulicious (Xvfb+bwrap, SMSJoypad P1/P2 na JVM); sem teclado/foco/DAP do desktop",
                  "duracao de comando = frames do VDP; estados pela RAM SMRT lida pela ponte",
                  "P2 life-zero → round_over → round score e life reset lidos da RAM"]}
    try:
        ctx = SC.private_session(rom)
        s = ctx.__enter__()
    except SC.SessionUnavailable as e:
        print("[FAIL_AMBIENTE] %s" % e)
        return 2, report
    exc = (None, None, None)
    try:
        report["session_id"], report["session_rom_sha256"] = s.id, s.rom_sha256
        if s.rom_sha256 != report["rom_sha256"]:
            print("[FAIL] SHA da ROM da sessao difere da ROM pedida")
            return 1, report
        expected_life = _max_life_low()
        magic = s.read(0xC7E0, 4)
        f0 = s.word(P_FRAME)
        s.hold(0, 0, 30)
        f1 = s.word(P_FRAME)
        report["boot_canary"] = {"magic": magic, "frame_before": f0, "frame_after": f1, "delta": f1 - f0,
                                 "live": magic == [83, 77, 82, 84] and f1 - f0 == 30}
        if not report["boot_canary"]["live"]:
            print("[FAIL] canario do canal de sessao falhou")
            return 1, report
        # atracao: avancar frames ate o roteiro completo (sem tocar em nada)
        frame = f1
        while frame < ATTRACT_END:
            s.hold(0, 0, min(120, ATTRACT_END - frame + 1))
            frame = s.word(P_FRAME)
        snap = (frame, s.byte(P_WAVE), s.byte(P_BOSS), s.byte(P_OVER), s.byte(P_ROUND_SCORE))
        if not attract_complete(snap[0], snap[1]):
            report["attract_wait_last"] = {"snapshot": snap}
            print("[FAIL] atração não completou")
            return 1, report
        report["attract_end"] = {"frame": snap[0], "wave": snap[1], "boss_life": snap[2], "over": snap[3],
                                 "round_score": snap[4]}
        s.hold(SC.R, 0, 8)             # qualquer entrada termina a demo
        s.hold(0, 0, 0)
        _wait_idle(s, 120)
        wins_before = snap[4] & 0x0F
        report["round_wins_before"] = wins_before
        ko_first = None
        for attempt in range(1, MAX_ATTACK_ATTEMPTS + 1):
            if s.byte(P_OVER):
                break
            trace = []
            in_range, gap = _approach(s, trace)
            if not in_range:
                report["attempts"].append({"attempt": attempt, "range_trace": trace, "gap": gap,
                                           "error": "não chegou ao alcance"})
                continue
            hit = _attack(s)
            report["attempts"].append({"attempt": attempt, "range_trace": trace, **hit})
            if hit.get("ko_snapshot"):
                ko_first = hit["ko_snapshot"]
                break
        # KO com round_over ainda alto; depois o intervalo e o reset do round
        ko = ko_first or (s.byte(P_OVER), s.byte(P_BOSS), s.byte(P_HP), s.byte(P_ROUND_SCORE), s.byte(P_TIMER))
        for _ in range(60):
            if ko_observed(ko[0], ko[1]):
                break
            s.hold(0, 0, 4)
            ko = (s.byte(P_OVER), s.byte(P_BOSS), s.byte(P_HP), s.byte(P_ROUND_SCORE), s.byte(P_TIMER))
        report["ko"] = {"over": ko[0], "boss_life": ko[1], "player_life": ko[2], "round_score": ko[3],
                        "timer": ko[4], "confirmed": ko_observed(ko[0], ko[1])}
        if not report["ko"]["confirmed"]:
            print("[FAIL] KO não observado via RAM")
            return 1, report
        ko_wins = ko[3] & 0x0F
        rs = None
        for _ in range(120):
            s.hold(0, 0, 4)
            rs = (s.byte(P_OVER), s.byte(P_BOSS), s.byte(P_HP), s.byte(P_ROUND_SCORE), s.byte(P_TIMER))
            if round_reset_observed(rs[0], rs[1], expected_life, ko_wins, rs[3], rs[2]):
                break
        reset_ok = bool(rs and round_reset_observed(rs[0], rs[1], expected_life, ko_wins, rs[3], rs[2]))
        report["round_reset"] = {"over": rs[0], "boss_life": rs[1], "player_life": rs[2], "round_score": rs[3],
                                 "timer": rs[4], "expected_boss_life_low_byte": expected_life,
                                 "confirmed": reset_ok}
        report["passed"] = bool(report["ko"]["confirmed"] and reset_ok)
        report["acks_tail"] = s.acks[-8:]
        print("[%s] KO=%s reset_round=%s attempts=%s; relatório=%s" %
              ("PASS" if report["passed"] else "FAIL", report["ko"]["confirmed"], reset_ok,
               len(report["attempts"]), OUT_REL))
        return (0 if report["passed"] else 1), report
    except BaseException:
        exc = sys.exc_info()
        raise
    finally:
        ctx.__exit__(*exc)


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
            if _.get("session_id"):    # copia exclusiva da sessao
                json.dump(_, open(OUT_REL.replace(".json", "_%s.json" % _["session_id"]), "w"), indent=2)
        return code
    except (BrokenPipeError, ConnectionError, OSError, RuntimeError) as exc:
        print("[FAIL_AMBIENTE] medição encerrada: %s" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
