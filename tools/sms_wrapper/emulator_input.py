#!/usr/bin/env python3
"""emulator_input.py — canal de teclado do Emulicious neste host (L039).

KDE Plasma / Wayland: xdotool/XTEST nao atravessa o KWin (getwindowfocus
vazio, probe_keys=0x00, ate o reset do emulador falha). O canal real e
kdotool (foco via DBus do KWin) + ydotool (injecao /dev/uinput, nivel
kernel). Fallback xdotool so vale em sessao X11.

Uso:
  from emulator_input import select_backend, press_spec
  emulator_input.py --self-check
Exit: 0 ok | 3 uso
"""
import os, shutil, subprocess, sys, time

YDOTOOL_SOCKET = "/tmp/.ydotool_socket_smsforge"
ENV = dict(os.environ, YDOTOOL_SOCKET=YDOTOOL_SOCKET)

# Nomes xdotool / aliases -> codigo evdev (ydotool key CODE:1 / CODE:0).
EVDEV = {
    "Right": 106, "Left": 105, "Up": 103, "Down": 108,
    "right": 106, "left": 105, "up": 103, "down": 108,
    "a": 30, "A": 30, "botao1": 30,
    "s": 31, "S": 31, "botao2": 31,
    "z": 44, "Z": 44, "x": 45, "X": 45,
    "Return": 28, "space": 57, "Space": 57,
    "BackSpace": 14, "ctrl": 29,
    # Atalhos do proprio Emulicious (nao sao joypad): gravacao e screenshot.
    # Nomes/valores conferidos no jar — ver capture_video.py.
    "F7": 65, "F8": 66, "F9": 67, "F10": 68, "F12": 88,
}

def run_session_sequence(session, steps):
    """Private P1/P2 masks for exact VDP frames; no desktop keyboard/focus.
    steps = [{"p1":16,"p2":0,"frames":3}, ...]. ROM observation is separate.
    """
    from session_bridge.isolated import sequence
    return sequence(session, steps)


def _run(cmd, timeout=20, env=None):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, env=env)
    except (subprocess.TimeoutExpired, OSError):
        return None


def select_backend():
    """wayland se kdotool+ydotool existem; senao x11 se xdotool existe."""
    if shutil.which("kdotool") and shutil.which("ydotool"):
        return "wayland"
    if shutil.which("xdotool"):
        return "x11"
    return None


def ensure_ydotool_daemon():
    if os.path.exists(YDOTOOL_SOCKET):
        return
    if not shutil.which("ydotoold"):
        return
    subprocess.Popen(["ydotoold", "-p", YDOTOOL_SOCKET, "-P", "0660"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    time.sleep(1.0)


def focus_wayland():
    """Ativa a janela Emulicious via KWin. Retorna True se o ativo bate."""
    kid = None
    for _ in range(20):
        r = _run(["kdotool", "search", "--name", "Emulicious"], env=ENV)
        ids = (r.stdout or "").split() if r else []
        if ids:
            kid = ids[0]
            break
        time.sleep(0.5)
    if kid is None:
        return False
    _run(["kdotool", "windowactivate", kid], env=ENV)
    time.sleep(0.3)
    r_act = _run(["kdotool", "getactivewindow"], env=ENV)
    a = (r_act.stdout or "").strip() if r_act else ""
    return a == kid


def focus_x11(window_id, input_id=None):
    iid = str(input_id or window_id)
    wid = str(window_id)
    for _ in range(5):
        _run(["xdotool", "windowactivate", "--sync", wid])
        _run(["xdotool", "windowraise", wid])
        _run(["xdotool", "windowfocus", "--sync", iid])
        time.sleep(0.3)
        f = _run(["xdotool", "getwindowfocus"])
        if f and f.stdout.strip() in (wid, iid):
            return True
    return False


def ydotool_key(code, down):
    spec = "%d:%d" % (int(code), 1 if down else 0)
    _run(["ydotool", "key", spec], env=ENV)


def press_spec(spec, x11_window=None, x11_input=None, refocus=True):
    """Executa 'Right=400,Left=200'. Retorna (done, backend, focused).

    done = [(tecla, ms), ...] na ordem enviada. Lista curta = foco falhou
    no meio (fail-closed, L007/L039).

    refocus=True (padrao): reativa a janela ANTES de cada tecla. Em Wayland
    o focus_wayland() dorme ~300 ms — ~18 frames NTSC. Isso estoura um
    buffer de comando de 8 ticks (QCF). Gestos encadeados devem usar
    refocus=False depois de um foco unico no comeco.
    """
    backend = select_backend()
    if backend is None:
        return [], None, False
    done = []
    focused = False
    if backend == "wayland":
        ensure_ydotool_daemon()
        focused = focus_wayland()
        if not focused:
            return [], backend, False
    elif x11_window is not None:
        focused = focus_x11(x11_window, x11_input or x11_window)
        if not focused:
            return [], backend, False
    for step in [s.strip() for s in spec.split(",") if s.strip()]:
        key, _, ms = step.partition("=")
        ms = int(ms or 400)
        if backend == "wayland":
            if refocus:
                if not focus_wayland():
                    return done, backend, False
            code = EVDEV.get(key)
            if code is None:
                return done, backend, True
            ydotool_key(code, True)
            time.sleep(ms / 1000.0)
            ydotool_key(code, False)
            focused = True
        else:
            iid = x11_input or x11_window
            if x11_window is None:
                return done, backend, False
            if refocus:
                focused = focus_x11(x11_window, iid)
                if not focused:
                    return done, backend, False
            _run(["xdotool", "keydown", "--window", str(iid), key],
                 timeout=max(10, ms // 1000 + 10))
            time.sleep(ms / 1000.0)
            _run(["xdotool", "keyup", "--window", str(iid), key])
        done.append((key, ms))
    return done, backend, focused


def press_chord(keys, ms=200, x11_window=None, x11_input=None, refocus=True):
    """Segura varias teclas ao mesmo tempo (throw B1+B2). keys=['a','x']."""
    backend = select_backend()
    if backend is None:
        return [], None, False
    codes = []
    for key in keys:
        c = EVDEV.get(key)
        if c is None:
            return [], backend, False
        codes.append(c)
    if backend == "wayland":
        ensure_ydotool_daemon()
        if refocus and not focus_wayland():
            return [], backend, False
        for c in codes:
            ydotool_key(c, True)
        time.sleep(ms / 1000.0)
        for c in reversed(codes):
            ydotool_key(c, False)
        return list(keys), backend, True
    iid = x11_input or x11_window
    if x11_window is None:
        return [], backend, False
    if refocus:
        if not focus_x11(x11_window, iid):
            return [], backend, False
    for key in keys:
        _run(["xdotool", "keydown", "--window", str(iid), key])
    time.sleep(ms / 1000.0)
    for key in reversed(keys):
        _run(["xdotool", "keyup", "--window", str(iid), key])
    return list(keys), backend, True


def tap_reset():
    """Atalho de reset do Emulicious (Ctrl+BackSpace). Canario do canal."""
    backend = select_backend()
    if backend == "wayland":
        ensure_ydotool_daemon()
        _run(["ydotool", "key", "29:1", "14:1", "14:0", "29:0"], env=ENV)
        return backend
    if backend == "x11":
        _run(["xdotool", "key", "ctrl+BackSpace"])
        return backend
    return None


def evaluate_direction(samples, canal_vivo):
    """dx >= 8 px NA DIRECAO COMANDADA nos dois sentidos, canal vivo (L038/L039)."""
    if not canal_vivo:
        return False, "canal de teclado morto: nenhuma leitura tem lastro"
    for s in samples:
        dx = s["dx"]
        if dx is None:
            return False, "leitura de probe_px falhou (" + s["tecla"] + ")"
        if dx * s["sentido_esperado"] < 8:
            return False, ("%s deslocou dx=%+d (precisava >= 8 na direcao "
                           "comandada %+d)" % (s["tecla"], dx,
                                               s["sentido_esperado"]))
    return True, "deslocamento na direcao comandada nos dois sentidos"


def evaluate_swap(before, flight, after, ground_y=112):
    """L053: cruzou por cima e o facing virou para o novo lado."""
    if not (before["px"] is not None and before["p2x"] is not None):
        return False, "leitura do estado inicial falhou"
    if not (before["px"] < before["p2x"]):
        return False, "estado inicial nao e Ken a esquerda do Guile"
    if not flight.get("pulo"):
        return False, ("nao houve pulo (min_py=%s, chao=%d)"
                       % (flight.get("min_py"), ground_y))
    if not (after["px"] is not None and after["p2x"] is not None
            and after["px"] > after["p2x"]):
        return False, "Ken nao aterrissou a direita do Guile (nao cruzou)"
    if not (before.get("facing_bit") and not after.get("facing_bit")):
        return False, ("facing nao virou de 1 para 0 com a troca de lado "
                       "(antes=%s depois=%s)" % (before.get("facing"),
                                                 after.get("facing")))
    return True, "pulo por cima observado e facing virou para o novo lado"


def _self_check():
    assert EVDEV["Right"] == 106 and EVDEV["Left"] == 105
    assert EVDEV["Up"] == 103 and EVDEV["a"] == 30
    assert EVDEV["botao1"] == EVDEV["A"] == 30
    b = select_backend()
    assert b in ("wayland", "x11", None)
    steps = [s.strip() for s in "Right=400,Left=200".split(",") if s.strip()]
    assert len(steps) == 2 and steps[0].startswith("Right")
    import inspect
    assert "refocus" in inspect.signature(press_spec).parameters
    assert inspect.signature(press_spec).parameters["refocus"].default is True
    # L065: 8 ticks a 60 Hz cabem ~133 ms; dois refocos de 300 ms nao cabem.
    def qcf_fits(hist_n, fps, inter_key_ms, dir_holds_ms):
        span = sum(dir_holds_ms) + inter_key_ms * (len(dir_holds_ms) - 1)
        return span <= (hist_n / float(fps)) * 1000.0
    assert not qcf_fits(8, 60, 300, [40, 40]), "L065: refoco 300ms coube em 8 ticks"
    assert qcf_fits(8, 60, 0, [40, 40]), "QCF sem refoco deveria caber"
    ok, _ = evaluate_direction([], False)
    assert not ok, "L039: canal morto foi aceito"
    ok, _ = evaluate_direction(
        [{"tecla": "Right", "sentido_esperado": 1, "dx": -32},
         {"tecla": "Left", "sentido_esperado": -1, "dx": -8}], True)
    assert not ok, "L038: direcao oposta foi aceita"
    ok, _ = evaluate_direction(
        [{"tecla": "Right", "sentido_esperado": 1, "dx": 74},
         {"tecla": "Left", "sentido_esperado": -1, "dx": -90}], True)
    assert ok, "caminho bom de input_memory.json foi reprovado"
    costas = evaluate_swap(
        {"px": 50, "p2x": 70, "facing_bit": True, "facing": 1},
        {"pulo": True, "min_py": 57},
        {"px": 89, "p2x": 67, "facing_bit": True, "facing": 1})
    assert not costas[0], "L053: cruzou e ficou de costas foi aceito"
    bom = evaluate_swap(
        {"px": 50, "p2x": 70, "facing_bit": True, "facing": 1},
        {"pulo": True, "min_py": 57},
        {"px": 89, "p2x": 67, "facing_bit": False, "facing": 0})
    assert bom[0], "sideswap observado foi reprovado: " + bom[1]
    print("[SELF-CHECK OK] emulator_input (mapa evdev, backend=%s, "
          "L038/L039/L053)" % b)
    return 0


def main():
    if "--self-check" in sys.argv:
        return _self_check()
    if "--session" in sys.argv:
        import argparse,json
        parser=argparse.ArgumentParser()
        parser.add_argument("--session",required=True)
        parser.add_argument("--script",required=True,help="JSON list of masks and VDP frame durations")
        a=parser.parse_args()
        try:
            with open(a.script) as source:steps=json.load(source)
            print(json.dumps(run_session_sequence(a.session,steps),indent=2));return 0
        except (OSError,RuntimeError,ValueError) as e:
            print("[FAIL] "+str(e),file=sys.stderr);return 2
    print("uso: emulator_input.py --self-check", file=sys.stderr)
    return 3


if __name__ == "__main__":
    sys.exit(main())
