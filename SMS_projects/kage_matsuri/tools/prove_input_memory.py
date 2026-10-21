#!/usr/bin/env python3
"""Prova que o INPUT joga kage_matsuri — lendo a RAM, nao os pixels.

Por que existe: o detector de gameplay do capture_evidence procura o maior
blob "com forma de sprite" e mede o deslocamento dele. Na rua matsuri isso
e ambiguo por construcao (L038): lanternas, torii e samurais geram massas
saturadas que trocam de lugar sem input, e o HUD de sprites (cabecas do
Kage) e estatico por construcao. Medido em 08/09/2026: com "Left" o blob
rastreado "andou" +137 px (massa de cenario) e o gate de pixels reprovou
uma ROM que responde. Aqui a pergunta e respondida onde ela tem resposta
unica (L035): o jogador mora em probe_px (0xC7FA), py (0xC7FB), pose
(0xC7F9) e probe_keys (0xC7F8).

Canal de teclado (L039 -> resolvido): o host e KDE/Wayland. xdotool/XTEST
nao atravessa o KWin. O canal real e kdotool (foco via KWin/DBus) +
ydotool (uinput, nivel kernel). O fallback xdotool so vale em host X11.

Seguranca: --rom e validado contra whitelist literal do projeto; qualquer
outra coisa reprova com exit 2 sem tocar em arquivo.
Rodar a partir da raiz do workspace (os caminhos de saida sao relativos).

Uso: prove_input_memory.py --rom SMS_projects/kage_matsuri/out/rom/kage_matsuri.sms
     prove_input_memory.py --self-check
Exit: 0 provado | 1 reprovado | 2 ambiente ausente
Artefato: SMS_projects/kage_matsuri/out/evidence/input_memory.json
(schema input_memory_v2: andar nos dois sentidos + pulo + eco de B1)
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, "/mnt/sdcard/Projects/SMSForge/tools/sms_wrapper")

import capture_evidence as CE                                    # noqa: E402
import emulator_input as EI                                      # noqa: E402
import measure_runtime_probe as MRP                              # noqa: E402
from emulicious_dap import PORT                                  # noqa: E402

PROBE_FRAME = 0xC7F0
PROBE_HP = 0xC7F2
PROBE_KILLS = 0xC7F4
PROBE_STATE = 0xC7F6
PROBE_KEYS = 0xC7F8
PROBE_POSE = 0xC7F9
PROBE_PX = 0xC7FA
PROBE_PY = 0xC7FB
PROBE_S0_HP = 0xC7FC
PROBE_S0_ALIVE = 0xC7FD
PROBE_S1_HP = 0xC7FE
PROBE_S1_ALIVE = 0xC7FF
PROBE_S0_X = 0xC7EE
PROBE_S1_X = 0xC7EF
GROUND_Y = 128            # chao da rua (airborne = py < GROUND_Y)

ROM_REL = "SMS_projects/kage_matsuri/out/rom/kage_matsuri.sms"
YDOTOOL_SOCKET = "/tmp/.ydotool_socket_smsforge"
ENV = dict(os.environ, YDOTOOL_SOCKET=YDOTOOL_SOCKET)

SETTLE = 3.0             # boot + cena estavel
HOLD_S = 0.8             # direcional pressionado durante a leitura
B1_HOLD_S = 0.5          # 'a' segurado durante o polling de pose/keys


# ---------------------------------------------------------------- logica pura
def evaluate(samples, canal_vivo):
    """Criterio canonico: emulator_input.evaluate_direction (L038/L039)."""
    return EI.evaluate_direction(samples, canal_vivo)


def evaluate_jump(min_py, canal_vivo, py_antes):
    """Pulo por input: py desceu abaixo do chao com o canal vivo."""
    if not canal_vivo:
        return False, "canal de teclado morto: nenhuma leitura tem lastro"
    if py_antes is None or min_py is None:
        return False, "leitura de probe_py falhou"
    if min_py < GROUND_Y:
        return True, "py %d -> %d (< chao %d): pulo observado" % (
            py_antes, min_py, GROUND_Y)
    return False, ("py nunca saiu do chao (min=%s, chao=%d)" % (min_py, GROUND_Y))


def evaluate_slash(b1_visto, poses_vistas, canal_vivo):
    """B1 por input: 0x10 em probe_keys com o jogo RODANDO e pose de golpe."""
    if not canal_vivo:
        return False, "canal de teclado morto: nenhuma leitura tem lastro"
    if b1_visto is False:
        return False, "probe_keys nunca latchou 0x10: a tecla nao chegou"
    golpe = poses_vistas & {3, 4}
    if golpe:
        return True, "B1 0x10 confirmado e pose %s observada" % sorted(golpe)
    return True, "B1 0x10 confirmado (pose de golpe nao amostrada na janela)"


# --------------------------------------------------------------- injecao
def ensure_daemon():
    if not os.path.exists(YDOTOOL_SOCKET):
        subprocess.Popen(["ydotoold", "-p", YDOTOOL_SOCKET, "-P", "0660"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        time.sleep(1.0)


def ensure_focus_wayland():
    kid = None
    for _ in range(20):
        r = subprocess.run(["kdotool", "search", "--name", "Emulicious"],
                           capture_output=True, text=True, env=ENV,
                           timeout=20)
        ids = (r.stdout or "").split()
        if ids:
            kid = ids[0]
            break
        time.sleep(0.5)
    if kid is None:
        return False, None
    subprocess.run(["kdotool", "windowactivate", kid],
                   capture_output=True, text=True, env=ENV, timeout=20)
    time.sleep(0.3)
    r_act = subprocess.run(["kdotool", "getactivewindow"],
                           capture_output=True, text=True, env=ENV,
                           timeout=20)
    a = (r_act.stdout or "").strip()
    return a == kid, kid


def press_wayland(acao):
    mapa = {"right": "106:1", "left": "105:1", "up": "103:1",
            "botao1": "30:1"}
    spec = mapa.get(acao)
    if spec:
        subprocess.run(["ydotool", "key", spec], capture_output=True,
                       text=True, env=ENV, timeout=20)


def release_wayland(acao):
    mapa = {"right": "106:0", "left": "105:0", "up": "103:0",
            "botao1": "30:0"}
    spec = mapa.get(acao)
    if spec:
        subprocess.run(["ydotool", "key", spec], capture_output=True,
                       text=True, env=ENV, timeout=20)


def hold_wayland(acao, seconds):
    press_wayland(acao)
    time.sleep(seconds)
    release_wayland(acao)


def tap_reset_wayland():
    subprocess.run(["ydotool", "key", "29:1", "14:1", "14:0", "29:0"],
                   capture_output=True, text=True, env=ENV, timeout=20)


def ensure_focus_x11(wid, iid):
    for _ in range(5):
        CE._run(["xdotool", "windowactivate", "--sync", str(wid)])
        CE._run(["xdotool", "windowraise", str(wid)])
        CE._run(["xdotool", "windowfocus", "--sync", str(iid)])
        time.sleep(0.3)
        f = CE._run(["xdotool", "getwindowfocus"])
        if f and f.stdout.strip() in (str(wid), str(iid)):
            return True
    return False


def hold_x11(acao, seconds):
    nomes = {"right": "Right", "left": "Left", "up": "Up", "botao1": "a"}
    nome = nomes.get(acao)
    if nome is None:
        return
    CE._run(["xdotool", "keydown", nome])
    time.sleep(seconds)
    CE._run(["xdotool", "keyup", nome])


def tap_reset_x11():
    CE._run(["xdotool", "key", "ctrl+BackSpace"])


def select_backend():
    """wayland = kdotool+ydotool; sem eles, o legado xdotool so vale X11."""
    if shutil.which("kdotool") and shutil.which("ydotool"):
        ensure_daemon()
        return "wayland"
    if shutil.which("xdotool"):
        return "x11"
    return None


def _connect_live_project(tentativas=4):
    """Conecta depois da inicializacao da janela e do debugger do Emulicious."""
    for _ in range(40):
        if CE._main_window_id():
            break
        time.sleep(0.5)
    time.sleep(5.0)
    for _ in range(tentativas):
        dap = MRP.wait_port(MRP.PORT, timeout_s=20)
        if dap is None:
            return None
        try:
            dap.start_session()
            dap.cont()
            time.sleep(2.0)
            dap.pause()
            if dap.eval_int(f"@0x{PROBE_FRAME:X}") is not None:
                return dap
        except (ConnectionError, AssertionError):
            pass
        dap.close()
        time.sleep(2.0)
    return None


# ---------------------------------------------------------------------- prova
def _read_retry(dap, fn, addr, tentativas=3):
    """Leitura DAP com re-amostra: o avaliador responde com anotacao de
    simbolo de forma INTERMITENTE ("= $XXXX (_SYM_)") e parse vira None.
    Re-ler resolve; desistir na primeira leitura culparia o jogo pela
    janela da medicao (licao do ciclo de servico invertido do MSSF2T)."""
    for i in range(tentativas):
        v = fn(dap, addr)
        if v is not None:
            return v
        time.sleep(0.2 * (i + 1))
    return None


def rd_byte(dap, addr):
    return dap.read_byte(addr)


def rd_word(dap, addr):
    return dap.read_word(addr)


def run():
    if not os.path.isfile("SMS_projects/kage_matsuri/out/rom/kage_matsuri.sms"):
        print("[FAIL_AMBIENTE] rodar a partir da raiz do workspace "
              "(caminhos de saida sao relativos a raiz)")
        return 2, None
    backend = select_backend()
    if backend is None:
        print("[FAIL_AMBIENTE] sem kdotool/ydotool nem xdotool no PATH")
        return 2, None
    logf = open("SMS_projects/kage_matsuri/out/evidence/input_memory_emu.log", "w")
    proc = subprocess.Popen(
        ["java", "-jar",
         "/mnt/sdcard/Projects/SMSForge/tools/emuladores/emulicious/Emulicious.jar",
         "-remotedebug", str(PORT), "-set", "Update=0",
         "/mnt/sdcard/Projects/SMSForge/SMS_projects/kage_matsuri/out/rom/kage_matsuri.sms"],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True, env=ENV)
    dap = None
    try:
        dap = _connect_live_project()
        if dap is None:
            print("[FAIL] canal DAP nao ficou vivo")
            return 1, None
        dap.cont()
        time.sleep(SETTLE)
        dap.pause()
        st0 = _read_retry(dap, rd_byte, PROBE_STATE)
        hp0 = _read_retry(dap, rd_byte, PROBE_HP)
        print("boot: estado=%s hp=%s (jogo comeca direto em ST_PLAY)" % (
            st0, hp0))

        # ---- estado limpo: o reset do proprio Emulicious recomeca a ROM.
        # O canario de canal NAO e o contador de frame: variavel __at() nao
        # e zerada pelo crt0, o contador acorda com lixo de RAM e o semantica
        # "f1 < f0" mente nos dois sentidos. Canal vivo aqui = foco
        # verificado + ECO DE TECLA em probe_keys/deslocamento (o sintoma
        # L039 e probe_keys 0x00 eterno — fail-closed se nada ecoar).
        f0 = _read_retry(dap, rd_word, PROBE_FRAME)
        if backend == "wayland":
            focado, _kid = ensure_focus_wayland()
            dap.cont()
            tap_reset_wayland()
        else:
            wid = CE._main_window_id()
            iid = CE._input_window_id(wid)
            if wid:
                focado = ensure_focus_x11(wid, iid)
            dap.cont()
            tap_reset_x11()
        time.sleep(1.5)
        dap.pause()
        f1 = _read_retry(dap, rd_word, PROBE_FRAME)
        print("reset ctrl+BackSpace: frame %s -> %s (foco=%s; contador __at "
              "nao e canario)" % (f0, f1, focado))

        # ---- deslocamento: ler COM A TECLA AINDA EM BAIXO (probe_keys so
        # vale enquanto o botao esta pressionado; ler depois do keyup
        # esconderia se a ROM registrou ou nao o comando).
        samples = []
        ecos = []            # ecos de tecla em probe_keys (canal vivo)
        prev = _read_retry(dap, rd_byte, PROBE_PX)
        for acao, tecla, expect, bit in (("right", "Right", +1, 0x08),
                                         ("left", "Left", -1, 0x04)):
            if backend == "wayland":
                ensure_focus_wayland()
            else:
                wid = CE._main_window_id()
                iid = CE._input_window_id(wid)
                ensure_focus_x11(wid, iid)
            dap.cont()
            if backend == "wayland":
                press_wayland(acao)
            else:
                CE._run(["xdotool", "keydown", tecla])
            time.sleep(HOLD_S)
            dap.pause()
            x = _read_retry(dap, rd_byte, PROBE_PX)
            k = _read_retry(dap, rd_byte, PROBE_KEYS)
            pose = _read_retry(dap, rd_byte, PROBE_POSE)
            if backend == "wayland":
                release_wayland(acao)
            else:
                CE._run(["xdotool", "keyup", tecla])
            dx = (x - prev) if (x is not None and prev is not None) else None
            echo = bool(k is not None and (k & bit))
            ecos.append(echo)
            print("  %s: keys_durante=0x%02X pose=%s px %s -> %s (dx=%s)"
                  % (tecla, k or 0, pose, prev, x, dx))
            dap.cont()
            samples.append({"tecla": tecla, "sentido_esperado": expect,
                            "x_antes": prev, "x_depois": x, "dx": dx,
                            "probe_keys_durante": k})
            prev = x

        # ---- pulo: Cima segurado; py tem de descer abaixo do chao
        if backend == "wayland":
            ensure_focus_wayland()
        else:
            wid = CE._main_window_id()
            iid = CE._input_window_id(wid)
            ensure_focus_x11(wid, iid)
        dap.pause()
        py_antes = _read_retry(dap, rd_byte, PROBE_PY)
        dap.cont()
        if backend == "wayland":
            press_wayland("up")
        else:
            CE._run(["xdotool", "keydown", "Up"])
        min_py = None
        poses_ar = set()
        up_eco = False
        fim = time.time() + 2.0
        while time.time() < fim:
            time.sleep(0.06)
            dap.pause()
            py = _read_retry(dap, rd_byte, PROBE_PY, tentativas=2)
            pose = _read_retry(dap, rd_byte, PROBE_POSE, tentativas=2)
            k = _read_retry(dap, rd_byte, PROBE_KEYS, tentativas=2)
            if k is not None and (k & 0x01):
                up_eco = True
            if py is not None and (min_py is None or py < min_py):
                min_py = py
            if pose is not None:
                poses_ar.add(pose & 0x7F)
            dap.cont()
        if backend == "wayland":
            release_wayland("up")
        else:
            CE._run(["xdotool", "keyup", "Up"])
        dap.pause()
        jump = {"py_antes": py_antes, "min_py": min_py,
                "pose_jump_vista": 5 in poses_ar, "up_eco": up_eco}
        ok_jump, motivo_jump = evaluate_jump(min_py, up_eco, py_antes)
        jump["pulo_provado"] = ok_jump
        jump["motivo"] = motivo_jump
        print("[pulo] %s (%s)" % ("provado" if ok_jump else "NAO provado",
                                  motivo_jump))

        # ---- B1: 'a' segurada com o jogo RODANDO; 0x10 em probe_keys e
        # pose de golpe (3 ou 4) na janela. Ciclo de servico curto: cada
        # iteracao roda ~50 ms entre pausas curtas, o ULTIMO frame antes de
        # cada pausa teve a tecla baixa (licao do soco do MSSF2T).
        if backend == "wayland":
            ensure_focus_wayland()
        else:
            wid = CE._main_window_id()
            iid = CE._input_window_id(wid)
            ensure_focus_x11(wid, iid)
        dap.cont()
        if backend == "wayland":
            press_wayland("botao1")
        else:
            CE._run(["xdotool", "keydown", "a"])
        k_b1, b1_visto = None, False
        poses_b1 = set()
        fim_b1 = time.time() + B1_HOLD_S
        while time.time() < fim_b1:
            time.sleep(0.05)
            dap.pause()
            k = _read_retry(dap, rd_byte, PROBE_KEYS, tentativas=2)
            p = _read_retry(dap, rd_byte, PROBE_POSE, tentativas=2)
            dap.cont()
            if k is not None:
                k_b1 = k if k_b1 is None else (k_b1 | k)
                if k & 0x10:
                    b1_visto = True
            if p is not None:
                poses_b1.add(p & 0x7F)
        if backend == "wayland":
            release_wayland("botao1")
        else:
            CE._run(["xdotool", "keyup", "a"])
        dap.pause()
        slash = {"keys_durante_b1": k_b1, "b1_chegou": b1_visto,
                 "poses_vistas": sorted(poses_b1)}
        ok_slash, motivo_slash = evaluate_slash(b1_visto, poses_b1, b1_visto)
        slash["slash_provado"] = ok_slash
        slash["motivo"] = motivo_slash
        print("[B1] %s (%s)" % ("provado" if ok_slash else "NAO provado",
                                motivo_slash))

        # ---- canal vivo = foco + QUALQUER eco de tecla em probe_keys
        # (o sintoma L039 e 0x00 eterno). Fail-closed: sem eco nenhum,
        # nenhuma leitura tem lastro e o eixo nao fecha.
        canal_vivo = bool(focado and any(ecos)) or bool(focado and up_eco) \
            or bool(focado and b1_visto)
        ok, motivo = evaluate(samples, canal_vivo)
        metrics = _metrics(backend, canal_vivo, focado, samples, ok, motivo,
                           f0, f1)
        metrics["input_provado"] = ok
        metrics["motivo"] = motivo
        metrics["pulo"] = jump
        metrics["slash"] = slash
        _dump(metrics)
        print("[%s] input->jogador %s (%s)"
              % ("PASS" if ok else "FAIL",
                 "provado" if ok else "NAO provado", motivo))
        return (0 if ok else 1), metrics
    finally:
        try:
            if dap:
                dap.close()
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


def _dump(metrics):
    with open("SMS_projects/kage_matsuri/out/evidence/input_memory.json", "w") as f:
        json.dump(metrics, f, indent=1)


def _metrics(backend, canal_vivo, focado, samples, ok, motivo, f0, f1):
    with open("SMS_projects/kage_matsuri/out/rom/kage_matsuri.sms", "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    m = {
        "schema": "input_memory_v2",
        "rom": ROM_REL,
        "rom_sha256": sha,
        "probe_addrs": {"frame": hex(PROBE_FRAME), "px": hex(PROBE_PX),
                        "py": hex(PROBE_PY), "keys": hex(PROBE_KEYS),
                        "pose": hex(PROBE_POSE)},
        "backend": backend,
        "foco_verificado": focado,
        "frames": {"antes": f0, "depois": f1},
        "amostras": samples,
        "input_provado": False,
        "canal_teclado_vivo": canal_vivo,
        "criterio": "dx >= 8 px NA DIRECAO COMANDADA nos dois sentidos, "
                    "com canal vivo (foco verificado + eco da tecla em "
                    "probe_keys; contador __at nao e canario — acorda com "
                    "lixo de RAM pois crt0 nao zera absolute-at)",
        "por_que_memoria": ("pixels sao ambiguos na rua matsuri (L038): "
                            "cenario saturado troca de massa sem input e o "
                            "HUD de sprites e estatico; probe_px/py/keys "
                            "tem resposta unica (L035)"),
        "chain_of_custody": [
            "launch: java -jar Emulicious.jar -remotedebug " + str(PORT),
            "attach DAP; leitura com a emulacao PAUSADA",
            "input: backend " + backend
            + " (L039: XTEST nao atravessa KWin; canal real = uinput)",
            "leitura: @0xC7FA px, @0xC7FB py, @0xC7F8 keys (main.c probes)",
        ],
    }
    if motivo is not None:
        m["motivo"] = motivo
    return m


def _cycle_snapshot(dap, label):
    """Snapshot autentico: pausa DAP, le probes do jogo, retoma depois."""
    dap.pause()
    vals = {
        "label": label,
        "frame": _read_retry(dap, rd_word, PROBE_FRAME),
        "kills": _read_retry(dap, rd_byte, PROBE_KILLS),
        "state": _read_retry(dap, rd_byte, PROBE_STATE),
        "keys": _read_retry(dap, rd_byte, PROBE_KEYS),
        "pose": _read_retry(dap, rd_byte, PROBE_POSE),
        "px": _read_retry(dap, rd_byte, PROBE_PX),
        "py": _read_retry(dap, rd_byte, PROBE_PY),
        "s0_hp": _read_retry(dap, rd_byte, PROBE_S0_HP),
        "s0_alive": _read_retry(dap, rd_byte, PROBE_S0_ALIVE),
        "s1_hp": _read_retry(dap, rd_byte, PROBE_S1_HP),
        "s1_alive": _read_retry(dap, rd_byte, PROBE_S1_ALIVE),
        "s0_x": _read_retry(dap, rd_byte, PROBE_S0_X),
        "s1_x": _read_retry(dap, rd_byte, PROBE_S1_X),
    }
    return vals


def _cycle_focus(backend):
    if backend == "wayland":
        return ensure_focus_wayland()[0]
    wid = CE._main_window_id()
    iid = CE._input_window_id(wid)
    return bool(wid and ensure_focus_x11(wid, iid))


def _cycle_hold(dap, backend, action, seconds):
    if not _cycle_focus(backend):
        return False
    dap.cont()
    if backend == "wayland":
        press_wayland(action)
    else:
        wid = CE._main_window_id()
        CE._run(["xdotool", "keydown", {"right": "Right", "left": "Left"}[action]])
    time.sleep(seconds)
    if backend == "wayland":
        release_wayland(action)
    else:
        wid = CE._main_window_id()
        CE._run(["xdotool", "keyup", {"right": "Right", "left": "Left"}[action]])
    # Deixe o evento de release atravessar o frame do emulador antes de
    # pausar; pausar imediatamente pode deixar a tecla latched no probe.
    time.sleep(0.08)
    dap.pause()
    return True


def _cycle_combo(dap, backend):
    """Dois edges B1 na janela 6..12, sem pausar entre os dois cortes."""
    if not _cycle_focus(backend):
        return False
    dap.cont()
    if backend == "wayland":
        press_wayland("botao1")
    else:
        CE._run(["xdotool", "keydown", "a"])
    time.sleep(0.10)
    if backend == "wayland":
        release_wayland("botao1")
    else:
        CE._run(["xdotool", "keyup", "a"])
    time.sleep(0.05)
    if backend == "wayland":
        press_wayland("botao1")
    else:
        CE._run(["xdotool", "keydown", "a"])
    time.sleep(0.10)
    if backend == "wayland":
        release_wayland("botao1")
    else:
        CE._run(["xdotool", "keyup", "a"])
    time.sleep(0.08)
    dap.pause()
    return True


def _cycle_align_target(dap, backend, label):
    """Put the live samurai inside the slash2 envelope before one combo.

    The patrol advances while the DAP is running, so a single fixed nudge is
    not a stable proof boundary. Re-read the paused probes after each short
    nudge and stop only when the target is in the currently facing-independent
    overlap band. This changes only the test choreography, never the ROM.
    """
    for _ in range(32):
        near = _cycle_snapshot(dap, label)
        if near["px"] is None:
            return False
        if near["s0_alive"]:
            target = near["s0_x"]
        elif near["s1_alive"]:
            target = near["s1_x"]
        else:
            return True
        if target is None:
            return False
        # slash2 reaches [px, px+34] when facing right and
        # [px-26, px+8] when facing left. Keep a margin for patrol motion.
        if near["px"] <= target <= near["px"] + 28:
            # One tiny right nudge makes the facing used by slash2 explicit.
            return _cycle_hold(dap, backend, "right", 0.04)
        if near["px"] - 20 <= target < near["px"]:
            # Same for the left-facing envelope.
            return _cycle_hold(dap, backend, "left", 0.04)
        action = "right" if target > near["px"] + 28 else "left"
        if not _cycle_hold(dap, backend, action, 0.08):
            return False
    return False


def _cycle_hold_b1_and_right(dap, backend, seconds):
    if not _cycle_focus(backend):
        return False
    dap.cont()
    if backend == "wayland":
        press_wayland("botao1")
        press_wayland("right")
    else:
        CE._run(["xdotool", "keydown", "a"])
        CE._run(["xdotool", "keydown", "Right"])
    time.sleep(seconds)
    if backend == "wayland":
        release_wayland("right")
        # Deliberadamente mantém B1 baixo até o snapshot de win.
    else:
        CE._run(["xdotool", "keyup", "Right"])
    dap.pause()
    return True


def evaluate_full_cycle(s):
    """Veredito fail-closed da sequência 2->1->0, vitória e reset."""
    by = {x.get("label"): x for x in s}
    required = ("after_reset", "combo_1", "combo_2", "win_held", "reset")
    if any(k not in by for k in required):
        return False, "snapshot ausente na sequência: " + ",".join(required)
    a, c1, c2, w, r = (by[k] for k in required)
    if (a["kills"], a["s0_alive"], a["s1_alive"]) != (0, 1, 1):
        return False, "reset inicial não restaurou os dois defensores"
    if not (c1["pose"] & 0x7F) == 4 or c1["kills"] != 1 or \
       (c1["s0_alive"] + c1["s1_alive"]) != 1:
        return False, "primeiro combo não mostrou pose 4 + uma derrota"
    if not (c2["pose"] & 0x7F) == 4 or c2["kills"] != 2 or \
       c2["s0_alive"] != 0 or c2["s1_alive"] != 0:
        return False, "segundo combo não mostrou pose 4 + derrota do último samurai"
    if w["state"] != 1 or w["kills"] != 2 or w["px"] <= 200:
        return False, "torii/vitória não ficou ativo com B1 segurado"
    if (r["state"], r["kills"], r["s0_alive"], r["s1_alive"]) != (0, 0, 1, 1):
        return False, "B1 não reiniciou a cena para 2 samurais"
    return True, "combo->duas derrotas->torii->reset provado por RAM"


def run_full_cycle():
    rom = "SMS_projects/kage_matsuri/out/rom/kage_matsuri.sms"
    if not os.path.isfile(rom):
        print("[FAIL_AMBIENTE] ROM ausente; rode a partir da raiz do workspace")
        return 2, None
    backend = select_backend()
    if backend is None:
        print("[FAIL_AMBIENTE] sem canal de teclado")
        return 2, None
    if not MRP._zombie_guard() or not MRP._port_free():
        return 2, None
    logf = open("SMS_projects/kage_matsuri/out/evidence/full_cycle_emu.log", "w")
    proc = subprocess.Popen(
        ["java", "-jar", "/mnt/sdcard/Projects/SMSForge/tools/emuladores/emulicious/Emulicious.jar",
         "-remotedebug", str(PORT), "-set", "Update=0", rom],
        stdout=logf, stderr=subprocess.STDOUT,
        start_new_session=True, env=ENV)
    dap = None
    snapshots = []
    attack_attempts = []
    try:
        dap = _connect_live_project()
        if dap is None:
            print("[FAIL] canal DAP não ficou vivo")
            return 1, None
        dap.cont()
        time.sleep(1.0)
        _cycle_focus(backend)
        tap_reset_wayland() if backend == "wayland" else tap_reset_x11()
        time.sleep(1.0)
        snapshots.append(_cycle_snapshot(dap, "after_reset"))
        # Short approach: keep the two patrol targets separated so slash2
        # lands on the first one only; the second combo is aligned below.
        _cycle_hold(dap, backend, "right", 0.15)
        if not _cycle_align_target(dap, backend, "near_s0"):
            print("[FAIL] primeiro alvo nao entrou no envelope slash2")
            return 1, None
        combo_1 = None
        for attempt in range(6):
            _cycle_combo(dap, backend)
            time.sleep(0.04)
            candidate = _cycle_snapshot(dap, "combo_1")
            attack_attempts.append({"stage": "combo_1", "attempt": attempt + 1,
                                    "kills": candidate["kills"],
                                    "pose": candidate["pose"] & 0x7F,
                                    "s0_alive": candidate["s0_alive"],
                                    "s1_alive": candidate["s1_alive"]})
            if candidate["pose"] & 0x7F == 4 and candidate["kills"] == 1 and \
               (candidate["s0_alive"] + candidate["s1_alive"]) == 1:
                combo_1 = candidate
                break
            # Let slash2 finish before the next edge. A failed attempt may
            # have dealt one point of damage; retrying is still the same
            # authored action and does not change the ROM or its scope.
            dap.cont()
            time.sleep(0.30)
            dap.pause()
            if not _cycle_align_target(dap, backend, "near_s0_retry"):
                print("[FAIL] primeiro alvo nao entrou no envelope slash2")
                return 1, None
        if combo_1 is None:
            print("[FAIL] primeiro combo nao confirmou uma derrota apos 6 tentativas")
            return 1, None
        snapshots.append(combo_1)
        combo_2 = None
        for attempt in range(6):
            # Let any preceding slash2 finish before arming the next edge.
            dap.cont()
            time.sleep(0.30)
            dap.pause()
            if not _cycle_align_target(dap, backend, "near_s1"):
                print("[FAIL] segundo alvo nao entrou no envelope slash2")
                return 1, None
            _cycle_combo(dap, backend)
            time.sleep(0.04)
            candidate = _cycle_snapshot(dap, "combo_2")
            attack_attempts.append({"stage": "combo_2", "attempt": attempt + 1,
                                    "kills": candidate["kills"],
                                    "pose": candidate["pose"] & 0x7F,
                                    "s0_alive": candidate["s0_alive"],
                                    "s1_alive": candidate["s1_alive"]})
            if candidate["pose"] & 0x7F == 4 and candidate["kills"] == 2 and \
               candidate["s0_alive"] == 0 and candidate["s1_alive"] == 0:
                combo_2 = candidate
                break
        if combo_2 is None:
            print("[FAIL] segundo combo nao confirmou a derrota final apos 6 tentativas")
            return 1, None
        snapshots.append(combo_2)
        _cycle_hold(dap, backend, "right", 1.00)
        # Mantém B1 pressionado enquanto cruza x>200: não pode resetar cedo.
        _cycle_hold_b1_and_right(dap, backend, 0.70)
        time.sleep(0.05)
        snapshots.append(_cycle_snapshot(dap, "win_held"))
        if backend == "wayland":
            release_wayland("botao1")
        else:
            CE._run(["xdotool", "keyup", "a"])
        # O jogo precisa processar o release para limpar prev_b1 antes do
        # novo edge; durante o snapshot anterior a CPU estava pausada. Um
        # edge pode ser perdido pelo foco compositor/DAP, então repetimos
        # somente o input de reset, fail-closed, sem aceitar estado parcial.
        reset = None
        reset_attempts = []
        for attempt in range(4):
            dap.cont()
            time.sleep(0.18)
            dap.pause()
            if not _cycle_focus(backend):
                continue
            dap.cont()
            if backend == "wayland":
                press_wayland("botao1")
                time.sleep(0.06)
                release_wayland("botao1")
            else:
                CE._run(["xdotool", "keydown", "a"])
                time.sleep(0.06)
                CE._run(["xdotool", "keyup", "a"])
            time.sleep(0.08)
            candidate = _cycle_snapshot(dap, "reset")
            reset_attempts.append({"attempt": attempt + 1,
                                   "state": candidate["state"],
                                   "kills": candidate["kills"],
                                   "s0_alive": candidate["s0_alive"],
                                   "s1_alive": candidate["s1_alive"]})
            if (candidate["state"], candidate["kills"],
                candidate["s0_alive"], candidate["s1_alive"]) == (0, 0, 1, 1):
                reset = candidate
                break
        if reset is None:
            reset = candidate if reset_attempts else _cycle_snapshot(dap, "reset")
        snapshots.append(reset)
        ok, motivo = evaluate_full_cycle(snapshots)
        if not ok:
            print("[TRACE] " + json.dumps(snapshots, sort_keys=True))
        sha = hashlib.sha256(open(rom, "rb").read()).hexdigest()
        metrics = {"schema": "kage_full_cycle_memory_v1", "rom": rom,
                   "rom_sha256": sha, "backend": backend,
                   "probe_addrs": {"frame": hex(PROBE_FRAME), "state": hex(PROBE_STATE),
                                   "kills": hex(PROBE_KILLS), "s0_hp": hex(PROBE_S0_HP),
                                   "s0_alive": hex(PROBE_S0_ALIVE), "s1_hp": hex(PROBE_S1_HP),
                                   "s1_alive": hex(PROBE_S1_ALIVE), "s0_x": hex(PROBE_S0_X),
                                   "s1_x": hex(PROBE_S1_X)},
                   "snapshots": snapshots, "ciclo_provado": ok,
                   "attack_attempts": attack_attempts,
                   "reset_attempts": reset_attempts,
                   "motivo": motivo,
                   "chain_of_custody": ["Emulicious DAP; snapshots com emulação pausada",
                                        "input via %s (foco verificado + uinput)" % backend,
                                        "sem alteração do roteiro para satisfazer o teste"]}
        with open("SMS_projects/kage_matsuri/out/evidence/full_cycle_memory.json", "w") as f:
            json.dump(metrics, f, indent=2)
        print("[%s] %s" % ("PASS" if ok else "FAIL", motivo))
        return (0 if ok else 1), metrics
    finally:
        if dap:
            dap.close()
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        logf.close()


# ----------------------------------------------------------------- self-check
def self_check():
    """§19: fixtures sao as regressoes exatas que motivaram o tool."""
    falhas = []

    # 1. Regressao L039 EXATA: tecla pressionada, probe_keys 0x00, canal morto.
    s_l039 = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
               "x_depois": 40, "dx": 0, "probe_keys_durante": 0x00}]
    ok, motivo = evaluate(s_l039, canal_vivo=False)
    if ok:
        falhas.append("L039: canal morto foi aceito")
    if "canal" not in motivo:
        falhas.append("L039: motivo nao cita o canal: " + motivo)

    # 2. Armadilha L038 EXATA: "Right" e o objeto anda para a ESQUERDA.
    s_l038 = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 104,
               "x_depois": 72, "dx": -32, "probe_keys_durante": 0x00}]
    ok, _ = evaluate(s_l038, canal_vivo=True)
    if ok:
        falhas.append("L038: dx na direcao OPOSTA foi aceito")

    # 3. Movimento curto demais (teto 8): dx=+3 reprova.
    s_curto = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
                "x_depois": 43, "dx": 3, "probe_keys_durante": 0x08}]
    ok, _ = evaluate(s_curto, canal_vivo=True)
    if ok:
        falhas.append("dx=3 na direcao certa foi aceito (teto e 8)")

    # 4. Um sentido so: Right ok e Left parado reprova (criterio simetrico).
    s_meio = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
               "x_depois": 60, "dx": 20, "probe_keys_durante": 0x08},
              {"tecla": "Left", "sentido_esperado": -1, "x_antes": 60,
               "x_depois": 60, "dx": 0, "probe_keys_durante": 0x04}]
    ok, _ = evaluate(s_meio, canal_vivo=True)
    if ok:
        falhas.append("segundo sentido parado foi aceito")

    # 5. Caminho bom: dx >= 8 na direcao comandada nos DOIS sentidos.
    s_ok = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
             "x_depois": 56, "dx": 16, "probe_keys_durante": 0x08},
            {"tecla": "Left", "sentido_esperado": -1, "x_antes": 56,
             "x_depois": 42, "dx": -14, "probe_keys_durante": 0x04}]
    ok, motivo_ok = evaluate(s_ok, canal_vivo=True)
    if not ok:
        falhas.append("caminho bom foi reprovado: " + motivo_ok)

    # 6. Leitura perdida (None) reprova em vez de seguir.
    s_none = [{"tecla": "Right", "sentido_esperado": +1, "x_antes": 40,
               "x_depois": None, "dx": None, "probe_keys_durante": 0x08}]
    ok, _ = evaluate(s_none, canal_vivo=True)
    if ok:
        falhas.append("leitura None foi aceita")

    # ---- fixtures do pulo
    # 7. Canal morto: pulo nao tem lastro.
    ok, _ = evaluate_jump(100, False, 128)
    if ok:
        falhas.append("pulo: canal morto foi aceito")
    # 8. py nunca saiu do chao.
    ok, _ = evaluate_jump(128, True, 128)
    if ok:
        falhas.append("pulo: py no chao foi aceito como salto")
    # 9. Caminho bom: py desceu abaixo do chao.
    ok, _ = evaluate_jump(100, True, 128)
    if not ok:
        falhas.append("pulo: caminho bom foi reprovado")

    # ---- fixtures do B1
    # 10. Tecla que NAO chegou nao e golpe (licao do soco do MSSF2T).
    ok, _ = evaluate_slash(False, set(), True)
    if ok:
        falhas.append("B1: tecla perdida foi aceita")
    # 11. B1 confirmado e pose 3 vista.
    ok, _ = evaluate_slash(True, {0, 3}, True)
    if not ok:
        falhas.append("B1: caminho bom foi reprovado")
    # 12. B1 confirmado sem pose amostrada ainda vale (eco e o sinal forte).
    ok, _ = evaluate_slash(True, {0}, True)
    if not ok:
        falhas.append("B1: eco 0x10 sem pose foi reprovado")
    # 13. Canal morto reprova.
    ok, _ = evaluate_slash(True, {3}, False)
    if ok:
        falhas.append("B1: canal morto foi aceito")

    if falhas:
        print("[SELF-CHECK FAIL]")
        for f in falhas:
            print("  - " + f)
        return 1
    print("[SELF-CHECK PASS] 13 fixtures: L039 canal morto, L038 direcao "
          "oposta, dx curto, sentido unico, caminho bom, leitura None, "
          "pulo canal morto/chao/bom, B1 tecla perdida/eco+pose/eco puro/"
          "canal morto")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--full-cycle", action="store_true",
                    help="prova combo, duas derrotas, torii e reset por RAM")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    # whitelist literal: o instrumento so opera sobre a ROM do projeto
    if a.rom not in ("out/rom/kage_matsuri.sms",
                     "SMS_projects/kage_matsuri/out/rom/kage_matsuri.sms"):
        print("[FAIL_AMBIENTE] --rom fora da whitelist do projeto")
        return 2
    if a.full_cycle:
        return run_full_cycle()[0]
    return run()[0]


if __name__ == "__main__":
    raise SystemExit(main())
