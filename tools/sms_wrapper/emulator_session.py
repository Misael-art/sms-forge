#!/usr/bin/env python3
"""emulator_session.py — uma politica so para "ja existe Emulicious rodando" (L057).

O perigo tem nome e lei desde a L017/§34, e mesmo assim o acervo o tratava de
tres jeitos diferentes: `capture_evidence`/`capture_video` abortavam,
`capture_audio` matava o zumbi, `measure_runtime_probe` abortava com outra
mensagem — e `audit_deterministic_boot`/`measure_frame_advance` nao faziam nada.
Onde nao havia guarda, o gate nao ficou mudo: ficou CONFIANTE E ERRADO.

DEMONSTRADO em 2026-09-07 (nao e deducao):
  1. subiu-se um Emulicious com MSSF2T e deixou-se rodando;
  2. rodou-se `audit_deterministic_boot.py --rom laboratorio_01.sms`;
  3. veredito: "[FAIL] boot NAO deterministico: hashes divergentes";
  4. o PNG que ele julgou mostra Ken x Guile, "ROUND 1" — MSSF2T.
O gate acusou o laboratorio_01 com base em frames de OUTRO binario, que por
acaso estava animando. Falso FAIL sobre uma ROM que ele nunca observou. A causa
raiz e sempre a mesma linha: `xdotool/kdotool search --name Emulicious` devolve
a janela de QUALQUER processo, e todo mundo pega a primeira.

Politica atual (§93): rota privada `isolated` com display e SMSJoypads proprios.
  ABORT — guarda da rota legada por nome global. Nunca encerra outras JVMs.
  KILL  — alias historico; agora reprova. Descoberta de PID nao prova ownership.

Uso:
  from emulator_session import require_no_stale, StalePolicy
  if not require_no_stale(why="captura de evidencia"): return 2
  emulator_session.py --self-check
  emulator_session.py isolated start ROM.sms
  emulator_session.py isolated close ID
Exit: 0 ok | 3 uso
"""
import os, sys, time, subprocess

# `Emulicious[.]jar`: o colchete impede o pgrep de casar com a PROPRIA linha de
# comando do shell que o invoca (`bash -c "... Emulicious.jar ..."`). Sem isso a
# ferramenta se acha zumbi — ou, pior num pkill, mata o proprio shell.
PGREP_PATTERN = "Emulicious[.]jar"

ABORT = "abort"
KILL = "kill"


class StalePolicy:
    ABORT = ABORT
    KILL = KILL


def _run(cmd, timeout=20):
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None


def _is_java(pid):
    """O processo e mesmo uma JVM? `pgrep -f` casa a linha de comando INTEIRA.

    O colchete do padrao impede o pgrep de achar a si proprio, mas nao impede
    que ele ache o SHELL que invocou a ferramenta — qualquer `bash -c "...
    Emulicious.jar ..."` casa. Medido: o experimento do zumbi devolveu 3 PIDs e
    dois eram o wrapper do proprio comando. Abortar por causa do shell que te
    chamou e falso positivo com cara de gate rigoroso; o teste real e argv[0]
    ser um executavel java.
    """
    try:
        with open("/proc/%s/cmdline" % pid, "rb") as f:
            argv0 = f.read().split(b"\0", 1)[0].decode("utf8", "replace")
    except OSError:
        return False
    return os.path.basename(argv0).startswith("java")


def stale_pids(exclude=None):
    """PIDs de JVMs do Emulicious vivas, menos os de `exclude`."""
    r = _run(["pgrep", "-f", PGREP_PATTERN])
    if not r or r.returncode != 0:
        return []
    skip = {str(p) for p in (exclude or [])}
    return [p for p in r.stdout.split()
            if p.isdigit() and p not in skip and _is_java(p)]


def explain(pids, why=None):
    """Mensagem unica. O gate que so diz 'ja existe Emulicious' nao ensina."""
    return (
        "[FAIL_AMBIENTE] ja existe Emulicious rodando (pid %s)%s. Use uma "
        "sessao privada: emulator_session.py isolated start ROM.sms; ou "
        "encerre manualmente apenas a instancia identificada.\n"
        "  Motivo (L057, demonstrado): a busca de janela por NOME devolve a "
        "janela de qualquer instancia. Com um zumbi vivo o gate nao falha — "
        "ele mede a ROM ERRADA e emite veredito confiante sobre a sua. Ja "
        "aconteceu: audit_deterministic_boot reprovou o laboratorio_01 "
        "fotografando o MSSF2T.\n"
        "  O zumbi tambem reescreve o Emulicious.ini ao morrer, apagando "
        "atalhos instalados por capture_video (L056)."
        % (", ".join(pids), (" — " + why) if why else "")
    )


def kill_stale(exclude=None, wait=0.8):
    """Legacy broad kill removed: discovered PIDs do not establish ownership."""
    raise RuntimeError("KILL global proibido; encerre a sessao que voce criou pelo ID")


def require_no_stale(policy=ABORT, why=None, exclude=None, out=None):
    """True = campo livre. Em ABORT imprime a explicacao e devolve False."""
    out = out or sys.stdout
    pids = stale_pids(exclude=exclude)
    if not pids:
        return True
    if policy == KILL:
        print("[FAIL_AMBIENTE] KILL global desativado: PIDs encontrados nao "
              "provam propriedade da sessao.",file=out)
        return False
    print(explain(pids, why), file=out)
    return False


def _self_check():
    import io
    assert PGREP_PATTERN == "Emulicious[.]jar", "pgrep casaria com o proprio shell"
    # a explicacao tem que NOMEAR o defeito, nao so anunciar o estado
    msg = explain(["123"], why="teste")
    assert "ROM ERRADA" in msg and "123" in msg and "isolated start" in msg, msg
    assert "laboratorio_01" in msg and "MSSF2T" in msg, "perdeu o caso demonstrado"
    # ABORT nao mata nada e devolve False quando ha zumbi
    buf = io.StringIO()
    real = globals()["stale_pids"]
    globals()["stale_pids"] = lambda exclude=None: ["999"]
    try:
        assert require_no_stale(out=buf) is False
        assert require_no_stale(policy=KILL,out=buf) is False
        assert "FAIL_AMBIENTE" in buf.getvalue()
        globals()["stale_pids"] = lambda exclude=None: []
        assert require_no_stale(out=io.StringIO()) is True
    finally:
        globals()["stale_pids"] = real
    # exclude tira o proprio processo da conta
    assert isinstance(stale_pids(exclude=[os.getpid()]), list)
    # o SHELL que chamou nao e uma JVM: pgrep -f casa a linha dele, _is_java nao
    assert _is_java(os.getpid()) is False, "python nao deveria contar como java"
    assert _is_java(999999999) is False, "pid inexistente nao pode contar"
    from session_bridge.isolated import self_check
    self_check()
    print("[OK] emulator_session self-check")
    return 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["isolated"]:
        from session_bridge.isolated import main
        sys.exit(main(sys.argv[2:]))
    if "--self-check" in sys.argv[1:]:
        sys.exit(_self_check())
    print(__doc__.splitlines()[0])
    pids = stale_pids()
    print("Emulicious vivos: %s" % (", ".join(pids) if pids else "nenhum"))
    sys.exit(0)
