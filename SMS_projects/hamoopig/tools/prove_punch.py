#!/usr/bin/env python3
"""Prova de soco em SESSAO PRIVADA (§93/L057): aproximar por frames, B1, ler vida de P2 na RAM.
Eixos: ACK da ponte/estado das portas (no JSON) separados da leitura da ROM (probe)."""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sms_wrapper"))
import session_consumer as SC

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROM = os.path.join(PROJ, "out", "rom", "hamoopig.sms")
OUT = os.path.join(PROJ, "out", "evidence")


def main():
    os.makedirs(OUT, exist_ok=True)
    try:
        ctx = SC.private_session(ROM)
        s = ctx.__enter__()
    except SC.SessionUnavailable as e:
        print(f"[FAIL_AMBIENTE] {e}")
        return 2
    exc = (None, None, None)
    try:
        s.hold(0, 0, 180)
        for _ in range(2):
            s.hold(SC.B1, 0, 4)
            s.hold(0, 0, 36)
        s.hold(0, 0, 120)                       # ROUND+FIGHT lock: nao andar durante g_lock
        gap, px, p2x, trace = 255, 0, 0, []
        for _ in range(40):
            s.hold(SC.R, 0, 6)
            px, p2x, gap = s.byte(0xC7FA), s.byte(0xC7FC), s.byte(0xC7E7)
            trace.append({"px": px, "p2x": p2x, "gap": gap})
            if gap <= 24:
                break
        s.hold(0, 0, 20)
        hp0, st = s.byte(0xC7F4), s.byte(0xC7E6)
        r = s.hold(SC.B1, 0, 4)
        keys = s.byte(0xC7F8)
        s.hold(0, 0, 40)                        # janela ativa + recuperacao
        hp1, st1, used = s.byte(0xC7F4), s.byte(0xC7E6), s.byte(0xC7E9)
        rec = {"schema": "hamoopig_punch_v2_session", "session_id": s.id, "rom_sha256": s.rom_sha256,
               "hp0": hp0, "hp1": hp1, "px": px, "p2x": p2x, "gap": gap, "approach": trace,
               "state_pre": st, "state_post": st1, "hit_used": used, "keys_durante": keys,
               "ack_porta": r.get("emulator_input"), "delta": hp0 - hp1}
        json.dump(rec, open(os.path.join(OUT, f"punch_probe_{s.id}.json"), "w"), indent=2)
        print({k: rec[k] for k in ("hp0", "hp1", "gap", "state_pre", "state_post", "hit_used", "keys_durante", "delta")})
        # probe_keys (0xC7F8) nao reteve B1 apos 4 frames (informativo); a chegada do comando e provada pela ROM:
        # estado pre->pos diferente, hit_used e queda de vida de P2
        ok = gap <= 24 and st != st1 and used == 1 and hp1 < hp0
        print("PASS punch" if ok else "FAIL punch")
        return 0 if ok else 1
    except BaseException:
        exc = sys.exc_info()
        raise
    finally:
        ctx.__exit__(*exc)


if __name__ == "__main__":
    sys.exit(main())
