#!/usr/bin/env python3
"""Prova minima em SESSAO PRIVADA (§93/L057): entrar na luta, Right por frames, ler probe_px.
Sem teclado/foco/DAP do desktop; duracao = frames do VDP; ROM+SHA reais da sessao no JSON."""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "sms_wrapper"))
import session_consumer as SC

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROM = os.path.join(PROJ, "out", "rom", "hamoopig.sms")
OUT = os.path.join(PROJ, "out", "evidence")
SCENE_FIGHT = 10


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
        s.hold(0, 0, 180)                       # boot/titulo
        for _ in range(2):                      # botao 1 duas vezes: titulo -> selecao -> luta
            s.hold(SC.B1, 0, 4)
            s.hold(0, 0, 36)
        s.hold(0, 0, 120)                       # ROUND+FIGHT lock (~90 frames)
        scene, px0 = s.byte(0xC7F6), s.byte(0xC7FA)
        print(f"pre scene={scene} px={px0}")
        r = s.hold(SC.R, 0, 48)
        px1, keys, scene = s.byte(0xC7FA), s.byte(0xC7F8), s.byte(0xC7F6)
        dx = px1 - px0
        print(f"post scene={scene} px={px1} keys={keys} dx={dx}")
        rec = {"schema": "hamoopig_walk_v2_session", "session_id": s.id, "rom_sha256": s.rom_sha256,
               "scene": scene, "px0": px0, "px1": px1, "keys": keys, "dx": dx,
               "ack_porta": r.get("emulator_input"), "frames_held": 48}
        json.dump(rec, open(os.path.join(OUT, f"walk_probe_{s.id}.json"), "w"), indent=2)
        ok = scene == SCENE_FIGHT and dx >= 8
        print("PASS walk" if ok else "FAIL walk")
        return 0 if ok else 1
    except BaseException:
        exc = sys.exc_info()
        raise
    finally:
        ctx.__exit__(*exc)


if __name__ == "__main__":
    sys.exit(main())
