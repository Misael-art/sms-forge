#!/usr/bin/env python3
"""Replay HISTORICO de consumidores sobre sessoes privadas (§93/L057).

Aposentado em 2026-10-18 com o HAMOOPIG; requer --legacy e copias locais.
Aceitacao ativa da infraestrutura: session_bridge/acceptance.py.

Duas ROMs reais simultaneas (luta_mugen e hamoopig): IDs/displays/PIDs distintos, sequencias distintas sem
cruzamento entre sessoes nem entre P1/P2, screenshot e video ligados a ROM/sessao, audio privado, fechamento
de uma sessao preservando a outra, limpeza apos erro (botoes soltos), rejeicao de sessao encerrada e de ROM
adulterada. Eixos separados: ack da ponte, portas emuladas, RAM da ROM. Nao toca no desktop do usuario.
"""
import json, os, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import session_consumer as SC
from session_bridge import isolated as I

ROOT = HERE.parents[2]
MUGEN = ROOT / "SMS_projects/luta_mugen/out/rom/luta_mugen.sms"
HAMO = ROOT / "SMS_projects/hamoopig/out/rom/hamoopig.sms"


def main(out, *, legacy=False):
    if not legacy:
        print("[ARQUIVADO] HAMOOPIG foi retirado do versionamento. "
              "Use session_bridge/acceptance.py para a infraestrutura; "
              "este replay historico exige --legacy e as ROMs locais originais.")
        return 3
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    rep, checks = {"schema": "consumer_acceptance_v1", "checks": checks_list()}, None
    checks = rep["checks"]

    def chk(name, ok, **info):
        checks.append({"check": name, "ok": bool(ok), **info})
        print(("[PASS] " if ok else "[FAIL] ") + name, info if not ok else "")

    ca, cb = SC.private_session(MUGEN), SC.private_session(HAMO)
    a, b = ca.__enter__(), cb.__enter__()
    try:
        ma, mb = I.load(a.root)[1], I.load(b.root)[1]
        chk("ids_displays_pids_distintos", len({ma["session_id"], mb["session_id"]}) == 2
            and ma["display"] != mb["display"] and ma["emulator_process"]["pid"] != mb["emulator_process"]["pid"]
            and ma["rom_sha256"] != mb["rom_sha256"], a=ma["session_id"], b=mb["session_id"],
            displays=[ma["display"], mb["display"]])
        # leva hamoopig a luta (eixo ROM: cena 10) e mugen alem da atracao
        b.hold(0, 0, 180)
        for _ in range(2):
            b.hold(SC.B1, 0, 4); b.hold(0, 0, 36)
        b.hold(0, 0, 120)
        a.hold(0, 0, 60)
        pa0, pb0, pb2_0 = a.byte(0xC7FA), b.byte(0xC7FA), b.byte(0xC7FC)
        # sequencias DIFERENTES em paralelo: A so P1=Right; B so P2=Left (P1 de B nao pode mover)
        res = {}
        def run_a(): res["a"] = a.hold(SC.R, 0, 40)
        def run_b(): res["b"] = b.hold(0, SC.L, 40)
        ta, tb = threading.Thread(target=run_a), threading.Thread(target=run_b)
        ta.start(); tb.start(); ta.join(); tb.join()
        pa1, pb1, pb2_1 = a.byte(0xC7FA), b.byte(0xC7FA), b.byte(0xC7FC)
        chk("ack_portas_por_sessao", res["a"]["p1"] == SC.R and res["a"]["p2"] == 0 and res["b"]["p1"] == 0
            and res["b"]["p2"] == SC.L, a=[res["a"]["p1"], res["a"]["p2"]], b=[res["b"]["p1"], res["b"]["p2"]])
        chk("rom_a_moveu_p1_direita", pa1 - pa0 >= 8, antes=pa0, depois=pa1)
        chk("rom_b_p1_nao_cruzou", pb1 == pb0, antes=pb0, depois=pb1)
        rep["observacao_p2"] = {"hamoopig_p2x": [pb2_0, pb2_1], "nota": "hamoopig nao consome P2 humano; separacao P1/P2 "
                                "provada na ROM so pelo fixture controls_probe (acceptance.py), nao aqui"}
        # captura: screenshot ligado a sessao+ROM
        ra, rb = a.capture("cap_a.png"), b.capture("cap_b.png")
        chk("capturas_vinculadas", ra["session_id"] == ma["session_id"] and ra["rom_sha256"] == ma["rom_sha256"]
            and rb["session_id"] == mb["session_id"] and rb["rom_sha256"] == mb["rom_sha256"]
            and ra["sha256"] != rb["sha256"], a=ra["sha256"][:12], b=rb["sha256"][:12])
        va = I.video(a.root, 30, "vid_a")
        chk("video_nativo_ligado", va["frames"] == 30 and va["last_frame"] - va["first_frame"] >= 29
            and va["canvas"] == [256, 192], frames=va["frames"], first=va["first_frame"], last=va["last_frame"])
        # audio privado de A (nao do desktop)
        import capture_audio as CA
        rc = CA.capture_session(str(a.root), 4, "acc_audio")
        aj = json.loads((a.root / "acc_audio.audio.json").read_text())
        chk("audio_privado_a", rc == 0 and aj["session_id"] == ma["session_id"] and aj["peak"] > 0
            and aj["effective_seconds"] >= 3.8, peak=aj["peak"], eff=aj["effective_seconds"])
        # encerra A, B segue viva
        I.close_session(a.root)
        chk("a_encerrada_pid_morto", not I.alive(ma["emulator_process"]))
        st = b.status()
        chk("b_preservada_apos_fechar_a", st["ok"] and I.alive(mb["emulator_process"]) and b.step(2)["frame"] > st["frame"])
        try:
            I.request(a.root, "status"); closed_rejected = False
        except Exception as e:
            closed_rejected = True
        chk("sessao_encerrada_rejeitada", closed_rejected)
    finally:
        cb.__exit__(None, None, None)
        try:
            ca.__exit__(None, None, None)
        except Exception as e:
            rep["a_exit_after_manual_close"] = str(e)[:120]

    # ROM privada adulterada -> request recusado
    with SC.private_session(HAMO) as c:
        rp = c.root / "emulator/rom.sms"
        data = rp.read_bytes(); rp.chmod(0o644); rp.write_bytes(data + b"\0")
        try:
            c.byte(0xC7F6); rejected = False
        except Exception as e:
            rejected = "ROM changed" in str(e) or "changed" in str(e)
        rp.write_bytes(data)
        chk("rom_adulterada_rejeitada", rejected)

    # limpeza apos erro: botoes soltos + processo morto + sink removido
    holder = {}
    try:
        with SC.private_session(HAMO) as d:
            holder["s"] = d; holder["meta"] = I.load(d.root)[1]
            d.hold(SC.R | SC.B1, SC.L, 5)
            raise RuntimeError("falha simulada do consumidor")
    except RuntimeError:
        pass
    last = holder["s"].acks[-1]
    m = holder["meta"]
    import subprocess
    sinks = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True).stdout
    chk("erro_libera_botoes_e_limpa", last["op"] == "input" and last["p1"] == 0 and last["p2"] == 0
        and not I.alive(m["emulator_process"]) and m.get("audio_sink", "x") not in sinks, last=last)
    rep["ok"] = all(c["ok"] for c in checks)
    (out / "consumer_acceptance.json").write_text(json.dumps(rep, indent=2))
    print("[PASS] consumer_acceptance" if rep["ok"] else "[FAIL] consumer_acceptance")
    return 0 if rep["ok"] else 1


def checks_list():
    return []


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "out/local_study/sms_isolated_session/consumer_acceptance"
    sys.exit(main(out, legacy="--legacy" in sys.argv))
