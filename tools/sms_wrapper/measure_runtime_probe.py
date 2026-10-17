#!/usr/bin/env python3
"""measure_runtime_probe.py — o ESTADO da ROM lido na MEMORIA, nao em pixels.

L035. Os probes existem no fonte desde o inicio (0xC7F0..7) e nenhuma
ferramenta lia — o diagnostico de runtime corria por pixels: foco do
gerenciador de janelas (L007), rasgo do import (L013), Nyquist de
screenshot (L025). Este gate le o payload AUTENTICADO do probe via DAP do
Emulicious e fecha, por memoria:
  - boot: magic "SMRT" + schema — recusa metrica de payload de outro
    binario (o §26 visto pelo consumidor, nao so pelo selador);
  - frame_advance: probe_frame avanca dentro da janela de EXECUCAO (§36
    sem rasgo de import, sem Nyquist de captura, sem foco de janela);
  - fps_constante: janelas concordantes na faixa 50..60;
  - input_route: relata a rota de input PAGA (teclado via WM; este build do
    adaptador DAP nao tem escrita — fato 5 de emulicious_dap.py).

A ROM precisa conter o cabecalho (main.c: probe_magic0..probe_schema).
Leitura de memoria so acontece com a emulacao PAUSADA; o tempo de execucao
de cada janela e medido ENTRE o ack do continue e o envio do pause, entao a
pausa nao contamina o fps.

Uso: measure_runtime_probe.py --rom X.sms [--project D] [--seconds 8]
                                [--janelas 2] [-o saida.json] [--self-check]
Exit: 0 eixos provados | 1 probe/canal reprovado | 2 ambiente ausente | 3 uso
"""
import sys, os, json, time, argparse, subprocess, shutil, hashlib, math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from emulicious_dap import (wait_port, parse_eval_value, fps_from_window,   # noqa: E402
                            fps_constant, magic_ok, EmuliciousDap, PORT)
from schema_guard import (load_schema, validate as validate_instance,       # noqa: E402
                          schema_path, SchemaUnsupported)
import capture_evidence as CE                                               # noqa: E402

PROBE_BLOCK = 0xC700          # base canonica do corredor de sondas (contrato)
PROBE_BASE = 0xC7E0
HEADER_LEN = 5
FRAME_ADDR = 0xC7F0
# v2 (D10, 2026-10-17): 0xC7FB = profundidade do jogador ("pz", nome do
# proprio fonte); 0xC7FD = altitude ("py"); 0xFC/0xFE/0xFF = alvo movel.
SNAP_ADDRS = {"hp": 0xC7F2, "score": 0xC7F3, "boss": 0xC7F4, "over": 0xC7F5,
              "state": 0xC7F6, "wave": 0xC7F7, "keys": 0xC7F8,
              "px": 0xC7FA, "pz": 0xC7FB, "p2x": 0xC7FC, "py": 0xC7FD,
              "p2state": 0xC7FE, "p2z": 0xC7FF}
OFFSETS = {"base": 0xE0, "frame": 0xF0, "hp": 0xF2, "score": 0xF3, "boss": 0xF4,
           "over": 0xF5, "state": 0xF6, "wave": 0xF7, "keys": 0xF8,
           "px": 0xFA, "pz": 0xFB, "p2x": 0xFC, "py": 0xFD, "p2state": 0xFE,
           "p2z": 0xFF}


def apply_probe_block(block):
    """Move the whole probe contract to another corridor, keeping every offset.

    Um projeto cujo _DATA encosta em 0xC790 nao pode manter as sondas la: o map
    mostra as variaveis da SMSlib/PSGlib caindo DENTRO do corredor (a escrita de
    probe corrompe o estado do stream e a leitura vira lixo — L089, medido
    2026-10-14). A saida e o projeto declarar outra base (ex. 0xC900) e o tool
    ler la. O default continua 0xC700, entao nenhuma ROM existente muda.
    """
    global PROBE_BLOCK, PROBE_BASE, FRAME_ADDR, SNAP_ADDRS
    if not (0xC000 <= block <= 0xDF00):
        raise ValueError("base do corredor fora da RAM do SMS: %s" % hex(block))
    if (block & 0xFF) or not (0xC000 <= block + 0x100 <= 0xE000):
        raise ValueError("base do corredor precisa ser uma pagina (0xXX00): %s"
                         % hex(block))
    PROBE_BLOCK = block
    PROBE_BASE = block + OFFSETS["base"]
    FRAME_ADDR = block + OFFSETS["frame"]
    SNAP_ADDRS = {k: block + OFFSETS[k]
                  for k in ("hp", "score", "boss", "over", "state", "wave",
                            "keys", "px", "pz", "p2x", "py", "p2state",
                            "p2z")}
    return PROBE_BASE


MIN_OVERSAMPLE = 3.0     # janela >> latencia de pause/continue (§36.1)
FPS_MIN, FPS_MAX = 50.0, 60.0


def target_fps_verdict(samples, region, tolerance=1.0, max_spread=1.0):
    """Window-rate target, not a proof of frame pacing or input latency.

    Broad 50..60 legacy acceptance cannot qualify a 60fps NTSC target. Bounds
    are explicit measurement tolerance (including pause transport), not a
    license to call an arbitrary stable slow game full speed.
    """
    target = {"NTSC": 60.0, "PAL": 50.0}.get(region) if isinstance(region, str) else None
    valid = (target is not None and isinstance(samples, list) and len(samples) >= 2 and
             all(type(x) in (int, float) and math.isfinite(x) and x > 0 for x in samples) and
             type(tolerance) in (int, float) and math.isfinite(tolerance) and 0 <= tolerance <= 1 and
             type(max_spread) in (int, float) and math.isfinite(max_spread) and 0 <= max_spread <= 1)
    spread = max(samples) - min(samples) if valid else None
    return {"region": region, "target_fps": target, "tolerance_fps": tolerance,
            "max_spread_fps": max_spread, "sample_count": len(samples) if isinstance(samples, list) else 0,
            "spread_fps": spread, "passed": bool(valid and spread <= max_spread and
                all(abs(x - target) <= tolerance for x in samples)),
            "claim_ceiling": "regional_mean_frame_rate_windows_only_not_per_frame_pacing_or_game_feel"}


def probe_verdict(m):
    """Eixos do probe a partir das metricas. PURA — fixture no self-check."""
    axes = {
        "boot": magic_ok((m.get("probe") or {}).get("header")),
        "frame_advance": (m.get("frames_delta_total") or 0) > 0,
        "fps_constante": bool(m.get("fps_constante")),
    }
    axes["aprovado"] = all(axes.values())
    return axes


def _zombie_guard():
    """L057: politica e mensagem unicas. Aqui ha um motivo EXTRA alem da janela
    errada — a porta do DAP e single-session."""
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from emulator_session import require_no_stale
    return require_no_stale(
        why="probe de runtime (porta %s / canal DAP sao single-session)" % PORT)


def _port_free():
    import socket as _s
    try:
        _s.create_connection(("127.0.0.1", PORT), timeout=0.5).close()
    except OSError:
        return True
    print(f"[FAIL_AMBIENTE] porta {PORT} ocupada — adaptador DAP de outra "
          "sessao ainda vivo?")
    return False


def measure(rom, project, seconds=8.0, janelas=2, out_name="runtime_probe"):
    jar = CE.resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado (resolve_jar)")
        return 2, None
    if not shutil.which("java"):
        print("[FAIL_AMBIENTE] java ausente")
        return 2, None
    try:
        schema = load_schema(schema_path())
    except (OSError, ValueError) as e:
        print(f"[FAIL_AMBIENTE] runtime_metrics_v1.schema.json ilegivel: {e}")
        return 2, None
    if not _zombie_guard() or not _port_free():
        return 2, None
    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    log_path = os.path.join(out_dir, f"{out_name}_emu.log")
    logf = open(log_path, "w")
    proc = subprocess.Popen(
        ["java", "-jar", jar, "-remotedebug", str(PORT), os.path.abspath(rom)],
        stdout=logf, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        dap = _connect_live()
        if dap is None:
            print(f"[FAIL] canal DAP nao ficou vivo (porta {PORT}; "
                  f"log: {log_path})")
            return 1, None
        try:
            return _session(dap, rom, out_dir, out_name, seconds, janelas,
                            os.path.basename(jar), schema)
        finally:
            dap.close()
    finally:
        # Fato 5: sem terminate request — o desligamento e do processo, como
        # capture_evidence ja faz.
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
        logf.close()


def _connect_live(tentativas=4):
    """Conexao, sessao e canario; reconecta enquanto o evaluate nao responder.

    Fato pago (L035): conectar ANTES do boot da ROM deixa a sessao stale —
    initialize/attach respondem, mas o evaluate pende para sempre. As sondas
    que funcionaram conectavam com a ROM ja rodando. O canario @0xC7F0 e o
    teste: sem resposta, fecha e reconecta (attach novo pausa e o cont()
    retoma, entao reconectar e seguro).
    """
    time.sleep(5.0)                      # deixa o boot da ROM comecar
    for _ in range(tentativas):
        dap = wait_port(PORT, timeout_s=20)
        if dap is None:
            return None
        try:
            dap.start_session()
            dap.cont()
            time.sleep(2.0)
            dap.pause()
            if dap.eval_int(f"@0x{FRAME_ADDR:X}") is not None:
                return dap
        except (ConnectionError, AssertionError):
            pass
        dap.close()
        time.sleep(3.0)
    return None


def _session(dap, rom, out_dir, out_name, seconds, janelas, jar_name, schema, private_meta=None):

    header = dap.read_block(PROBE_BASE, HEADER_LEN)
    if header is None:
        print(f"[FAIL] cabecalho do probe ilegivel (ultimo texto do "
              f"avaliador: {dap.last_raw!r}) — ROM buildada com o probe?")
        return 1, None
    frame0 = dap.read_word(FRAME_ADDR)
    if frame0 is None:
        print(f"[FAIL] probe_frame ilegivel (ultimo texto do avaliador: "
              f"{dap.last_raw!r})")
        return 1, None
    magic = bytes(header[:4]).decode(errors="replace") if header else "????"
    boot_ok = magic_ok(header)
    print(f"[{'PASS' if boot_ok else 'FAIL'}] cabecalho do probe: "
          f"magic={magic!r} schema={header[4] if header else '?'} "
          f"frame={frame0}")

    fps_list, deltas = [], 0
    for w in range(janelas):
        if w:
            if dap.pause() is None:
                print("[FAIL] pause sem resposta no meio da medicao")
                break
            frame0 = dap.read_word(FRAME_ADDR)
        # Relogio conservador: marca ANTES de enviar continue e ANTES de
        # enviar pause. A emulacao so roda DENTRO da janela marcada (o run
        # comeca apos o continue e pode continuar 1 latencia apos o pause),
        # entao o fps sai subestimado no pior caso — nunca inflado acima do
        # real. Marcando apos o ack do continue, a latencia virava fps
        # 60.1..60.3 e a propria faixa 50..60 reprovava uma ROM a 60.
        t0 = time.time()
        dap.cont()
        time.sleep(seconds)
        t1 = time.time()
        dap.pause()
        if private_meta is not None:
            t1=time.time()  # include stop/transport overhead: conservative FPS
        frame1 = dap.read_word(FRAME_ADDR)
        running = t1 - t0
        delta=((frame1 or 0)-(frame0 or 0))&0xFFFF if private_meta is not None else (frame1 or 0)-(frame0 or 0)
        f = fps_from_window(delta, running)
        fps_list.append(f)
        deltas += delta
        print(f"       janela {w + 1}: delta={frame1} - {frame0} frames em "
              f"{running:.2f}s -> fps={f}")

    snapshot = {k: dap.read_byte(a) for k, a in SNAP_ADDRS.items()}
    const, spread = fps_constant(fps_list, FPS_MIN, FPS_MAX)
    regional = None
    if private_meta is not None:
        status = dap.pause()
        nominal = status.get("nominal_hz")
        if type(nominal) not in (int, float) or not math.isfinite(nominal) or not (49 <= nominal <= 51 or 59 <= nominal <= 61):
            print("[FAIL] session region/nominal_hz unavailable or unsupported")
            return 1, None
        region = "PAL" if nominal < 55 else "NTSC"
        regional = target_fps_verdict(fps_list, region)
        const, spread = regional["passed"], regional["spread_fps"]

    sha = hashlib.sha256(open(rom, "rb").read()).hexdigest()
    metrics = {
        "schema": "runtime_metrics_v1",
        "rom": rom,
        "rom_sha256": sha,
        "region": "NTSC",
        "fps_measured": fps_list[0] if fps_list else None,
        "fps_janelas": fps_list,
        "fps_spread": spread,
        "fps_constante": const,
        "frame_advance_proved": deltas > 0,
        "frames_delta_total": deltas,
        "audio_active_pct": None,        # produtor proprio: capture_audio.py
        "boot_proved": boot_ok,
        "probe": {"magic": magic, "header": header, "base": hex(PROBE_BASE),
                  "schema_version": header[4] if header else None,
                  "frame_addr": hex(FRAME_ADDR), "snapshot": snapshot},
        "input_route": {
            "canal": "teclado via WM (xdotool), eco em probe_keys",
            "escrita_memoria": "ausente neste build do adaptador DAP "
                               "(fato pago 2026-09-04, L035)",
        },
        "tool": "emulicious-DAP/evaluate-@ (Expressions.txt) 2026-09-04",
        "chain_of_custody": [
            f"launch: java -jar {jar_name} -remotedebug {PORT}",
            "attach DAP (pausa na entry) -> continue por janela",
            "leitura: @addr / word.ram@@addr com a emulacao pausada",
            "fps: delta de probe_frame sobre o tempo de EXECUCAO (pausa "
            "fora do relogio)",
        ],
    }
    axes = probe_verdict(metrics)
    if private_meta is not None:
        metrics["session_id"]=private_meta["session_id"]
        metrics["host_load"]=list(os.getloadavg())
        metrics["input_route"]={"canal":"process-local SMSJoypad P1/P2; VDP frame pacing",
                               "escrita_memoria":"disabled; read-only bridge",
                               "rom_input_observation":"not proved by FPS probe"}
        metrics["tool"]="emulicious-original-JAR/private-process-bridge"
        metrics["chain_of_custody"]=["session: "+private_meta["session_id"],
                                    "display: "+private_meta["display"],
                                    "ROM SHA: "+private_meta["rom_sha256"],
                                    "frame delta observed in ROM RAM; original realtime runner; conservative clock"]
        metrics["region"] = region
        metrics["regional_frame_rate_check"] = regional
    metrics["axes"] = axes
    # A travessia que faltava (L035): o produtor abre o schema e valida a
    # propria instancia ANTES de selar. Instancia fora do contrato nao cria
    # arquivo — "schema": "runtime_metrics_v1" deixa de ser string literal.
    try:
        viol = validate_instance(metrics, schema)
    except SchemaUnsupported as e:
        print(f"[FAIL] schema fora do subconjunto do validador: {e}")
        return 1, None
    if viol:
        for v in viol:
            print(f"[FAIL] instancia viola runtime_metrics_v1: {v}")
        print("[FAIL] arquivo NAO selado — produtor nao escreve instancia "
              "fora do contrato")
        return 1, None
    out_json = os.path.join(out_dir, f"{out_name}.json")
    json.dump(metrics, open(out_json, "w"), indent=2)
    for axis, ok in axes.items():
        if axis != "aprovado":
            print(f"[{'PASS' if ok else 'FAIL'}] {axis}")
    print(("[PASS] " if axes["aprovado"] else "[FAIL] ")
          + f"runtime probe registrado: {out_json}")
    return (0 if axes["aprovado"] else 1), metrics


def self_check():
    assert target_fps_verdict([59.4, 59.8], "NTSC")["passed"]
    assert target_fps_verdict([49.5, 50.0], "PAL")["passed"]
    assert not target_fps_verdict([55.0, 55.0], "NTSC")["passed"]
    assert not target_fps_verdict([50.0, 50.0], "NTSC")["passed"]
    assert not fps_constant([60.0, None])[0]
    assert not fps_constant([60.0])[0]
    assert not fps_constant([True, 60.0])[0]
    assert not target_fps_verdict([59.0, 60.1], "NTSC")["passed"]
    for samples, region in (([True, 60], "NTSC"), ([float('nan'), 60], "NTSC"),
                            ([60], "NTSC"), ([60, 60], "UNKNOWN"), ([60, 60], [])):
        assert not target_fps_verdict(samples, region)["passed"]
    # parse do avaliador: o trap exato da L010 era tomar "$0" universal.
    assert parse_eval_value("@0xC7F0 = $9A") == 154
    assert parse_eval_value("word.ram@@0xC7F0 = $29A") == 666
    assert parse_eval_value("@0xC7F8 = $0") == 0, \
        "zero legitimo nao pode virar None"
    assert parse_eval_value("Unknown variable encountered: probe_frame") is None
    assert parse_eval_value("sem igual") is None
    assert parse_eval_value(None) is None

    # cabecalho: fixture boa e as violacoes (§20); v2 (D10) aditivo
    assert magic_ok([0x53, 0x4D, 0x52, 0x54, 1])
    assert magic_ok([0x53, 0x4D, 0x52, 0x54, 2]), "probe v2 (D10) recusado"
    assert not magic_ok([0x53, 0x4D, 0x52, 0x54, 3]), \
        "schema fora do suportado passou"
    assert not magic_ok([0x53, 0x4D, 0x52, 0x00, 1]), "magic errado passou"
    assert not magic_ok(None)
    assert not magic_ok([0x53, 0x4D])

    # corredor relocado: o contrato inteiro acompanha a base, offsets fixos
    apply_probe_block(0xC900)
    assert PROBE_BASE == 0xC9E0 and FRAME_ADDR == 0xC9F0, \
        "relocação não moveu header/frame"
    assert SNAP_ADDRS["state"] == 0xC9F6 and SNAP_ADDRS["pz"] == 0xC9FB, \
        "relocação não moveu o snapshot"
    assert SNAP_ADDRS["py"] == 0xC9FD and SNAP_ADDRS["p2z"] == 0xC9FF, \
        "campos v2 não acompanharam a relocação"
    try:
        apply_probe_block(0xC790)
        raise AssertionError("base fora da pagina foi aceita")
    except ValueError:
        pass
    try:
        apply_probe_block(0xDF80)
        raise AssertionError("corredor dentro da pilha foi aceito")
    except ValueError:
        pass
    apply_probe_block(0xC700)
    assert PROBE_BASE == 0xC7E0 and FRAME_ADDR == 0xC7F0 and \
        SNAP_ADDRS["state"] == 0xC7F6, "contrato canonico nao voltou"

    # fps por janela
    assert fps_from_window(480, 8.0) == 60.0
    assert fps_from_window(0, 8.0) == 0.0
    assert fps_from_window(480, 0) is None
    assert fps_from_window(None, 8.0) is None

    # constancia: concordante passa; janela fora da faixa reprovou
    ok, sp = fps_constant([59.4, 59.8])
    assert ok and sp == 0.4, f"janelas concordantes reprovaram: {ok} {sp}"
    ok, _ = fps_constant([59.0, 45.0])
    assert not ok, "fps fora da faixa passou (§20)"
    ok, _ = fps_constant([60.0, 30.0])
    assert not ok, "janelas divergentes passaram por constante"
    ok, _ = fps_constant([None])
    assert not ok

    # veredito: fixture boa, frame congelado e magic de outro binario
    good = {"probe": {"header": [0x53, 0x4D, 0x52, 0x54, 1]},
            "frames_delta_total": 480, "fps_constante": True}
    assert probe_verdict(good)["aprovado"]
    frozen = dict(good, frames_delta_total=0)
    assert not probe_verdict(frozen)["frame_advance"], \
        "ROM congelada passou frame_advance (o defeito exato do §36)"
    foreign = dict(good, probe={"header": [0x4D, 0x44, 0x52, 0x54, 1]})
    assert not probe_verdict(foreign)["boot"], \
        "payload de outro binario passou o cabecalho"

    # A travessia do schema (L035): instancia valida passa; as quatro
    # violacoes classicas reprovam; keyword nao suportada e fail-closed.
    from schema_guard import validate as _vi, SchemaUnsupported as _SU
    SCHEMA = {"type": "object",
              "required": ["rom", "fps_measured"],
              "properties": {
                  "rom": {"type": "string"},
                  "fps_measured": {"type": "number"},
                  "region": {"enum": ["NTSC", "PAL"]},
                  "audio_active_pct": {"type": ["number", "null"]},
                  "sprites_per_line_max": {"type": "integer", "maximum": 8},
                  "fps_janelas": {"type": "array",
                                  "items": {"type": "number"}}}}
    assert _vi({"rom": "x.sms", "fps_measured": 59.4}, SCHEMA) == []
    bad = _vi({"fps_measured": 59.4}, SCHEMA)
    assert any("rom" in v for v in bad), "required ausente passou"
    assert _vi({"rom": 7, "fps_measured": 59.4}, SCHEMA), "tipo errado passou"
    assert _vi({"rom": "x", "fps_measured": "60"}, SCHEMA), \
        "fps como string passou"
    assert _vi({"rom": "x", "fps_measured": 59.4, "region": "SECAM"},
               SCHEMA), "enum passou"
    assert _vi({"rom": "x", "fps_measured": 59.4,
                "sprites_per_line_max": 9}, SCHEMA), "maximum passou"
    assert _vi({"rom": "x", "fps_measured": 59.4,
                "audio_active_pct": "93%"}, SCHEMA), \
        "type list (number|null) nao reprovou string"
    ok_j = _vi({"rom": "x", "fps_measured": 59.4,
                "fps_janelas": [59.4, 59.3]}, SCHEMA)
    bad_j = _vi({"rom": "x", "fps_measured": 59.4,
                 "fps_janelas": [59.4, "59.3"]}, SCHEMA)
    assert ok_j == [] and bad_j, "items nao validou elemento do array"
    try:
        _vi({"rom": "x"}, {"properties": {"rom": {"pattern": "^x$"}}})
        raise SystemExit("[FAIL] keyword nao suportada nao foi reprovada "
                         "(fail-closed violado)")
    except _SU:
        pass
    print("[SELF-CHECK OK] runtime_probe (parse @, cabecalho, fps, veredito, "
          "schema_guard)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--rom")
    ap.add_argument("--session",help="private session ID; reads canonical SMRT probe without global DAP port")
    ap.add_argument("--seconds", type=float, default=8.0,
                    help="duracao de cada janela de execucao (default 8)")
    ap.add_argument("--janelas", type=int, default=2)
    ap.add_argument("--out", default="runtime_probe")
    ap.add_argument("--probe-base", default=None,
                    help="pagina do corredor de sondas (default 0xC700; "
                         "ex. 0xC900 para um projeto cujo _DATA encosta la)")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.probe_base:
        apply_probe_block(int(args.probe_base, 16))
    if args.self_check:
        return self_check()
    if args.session:
        from session_bridge.isolated import load,sha,MemoryReader,performance_reservation,project_reservation
        try:
            root,meta=load(args.session)
            if args.rom and sha(args.rom)!=meta["rom_sha256"]:raise ValueError("ROM/session mismatch")
            if args.seconds<MIN_OVERSAMPLE or args.janelas<2:raise ValueError("at least two windows of three seconds required")
            out_dir=os.path.join(os.path.abspath(args.project),"out","evidence","sessions",meta["session_id"],"runtime")
            os.makedirs(out_dir,exist_ok=True)
            reader=MemoryReader(root)
            if not magic_ok(reader.read_block(PROBE_BASE,HEADER_LEN)):raise ValueError("canonical SMRT probe absent")
            with performance_reservation(),project_reservation(args.project):
                code,_=_session(reader,str(root/"emulator/rom.sms"),out_dir,args.out,args.seconds,args.janelas,
                                "Emulicious.jar",load_schema(schema_path()),private_meta=meta)
            return code
        except (OSError,RuntimeError,ValueError) as e:
            print("[FAIL] "+str(e));return 2
    if not args.rom:
        print("[FAIL] --rom obrigatorio (ou use --self-check)", file=sys.stderr)
        return 3
    code, _ = measure(args.rom, os.path.abspath(args.project), args.seconds,
                      args.janelas, args.out)
    return code


if __name__ == "__main__":
    sys.exit(main())
