#!/usr/bin/env python3
"""capture_audio.py — grava o audio DO EMULADOR, isolado do resto da maquina.

Antes deste gate o acervo tinha .wav sem procedencia: alguem gravou de algum
jeito, em algum momento, de alguma ROM. Nao dava para saber se o som era da
build citada — nem se era do emulador.

PRIVACIDADE (licao L017, agora no dominio do audio): gravar o *monitor* do sink
padrao capturaria TODO o audio da maquina — musica, chamadas, notificacoes.
Aqui o fluxo do emulador e movido para um sink NULO dedicado e so o monitor
desse sink e gravado. Nenhum outro aplicativo entra na captura. O sink e
removido no final, sempre (o audio do usuario volta ao normal).

Limite honesto (§28): o gate prova que HA som e que ele veio do emulador.
NAO prova que e a musica certa nas notas certas — isso exige ouvido humano ou
comparacao com referencia.

Uso:
  capture_audio.py --project <dir> --rom <rom.sms> [--seconds 6] [--out audio]
  capture_audio.py --self-check
Exit: 0 gravado | 1 falha/silencio | 2 ambiente ausente | 3 uso
"""
import sys, os, json, threading, time, wave, shutil, argparse, subprocess, select, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SINK = "smsforge_capture"
RATE = 44100

def _run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def _emulator_sink_inputs():
    """Indices dos fluxos de audio pertencentes ao emulador (java)."""
    r = _run(["pactl", "list", "sink-inputs"])
    out, idx, is_emu = [], None, False
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("Sink Input #"):
            if idx is not None and is_emu:
                out.append(idx)
            idx, is_emu = line.split("#")[1].strip(), False
        low = line.lower()
        if "java" in low or "emulicious" in low:
            is_emu = True
    if idx is not None and is_emu:
        out.append(idx)
    return out

def sink_inputs_by_pid(pid):
    """Sink-inputs cujo application.process.id e EXATAMENTE pid (L057: nunca outra JVM)."""
    out, idx, owner = [], None, None
    for line in _run(["pactl", "list", "sink-inputs"]).stdout.splitlines() + ["Sink Input #END"]:
        line = line.strip()
        if line.startswith("Sink Input #"):
            if idx is not None and owner == str(pid): out.append(idx)
            idx, owner = line.split("#")[1].strip(), None
        elif line.startswith("application.process.id"):
            owner = line.split("=", 1)[1].strip().strip('"')
    return out

def record_private_pcm(sink, seconds):
    """Bounded read of only the named private monitor; never the default monitor."""
    if seconds <= 0 or seconds > 300: raise ValueError("audio duration must be 0..300 seconds")
    want = int(seconds * RATE * 2)
    rec = subprocess.Popen(["parec", "-d", f"{sink}.monitor", "--format=s16le", f"--rate={RATE}", "--channels=1"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    parts, size, deadline = [], 0, time.monotonic() + seconds + 15
    try:
        while size < want and time.monotonic() < deadline:
            if not select.select([rec.stdout], [], [], min(0.5, max(0, deadline-time.monotonic())))[0]: continue
            chunk = os.read(rec.stdout.fileno(), 65536)
            if not chunk: break
            parts.append(chunk); size += len(chunk)
    finally:
        if rec.poll() is None:
            rec.terminate()
            try: rec.wait(timeout=3)
            except subprocess.TimeoutExpired: rec.kill(); rec.wait(timeout=3)
        rec.stdout.close()
    return b"".join(parts)

def duration_sufficient(pcm, requested):
    return requested > 0 and len(pcm) / 2 / RATE >= requested * 0.95

def capture_session(session, seconds=6, out_name="audio"):
    """Audio real da sessao privada: sink nulo da sessao + fluxo do PID exato."""
    from session_bridge import isolated
    if not re.fullmatch(r"[A-Za-z0-9_-]+", out_name):
        raise ValueError("audio output must be a simple session-local name")
    root, meta = isolated.load(session)
    sink, pid = meta.get("audio_sink"), meta["emulator_process"]["pid"]
    if not sink or not isolated.alive(meta["emulator_process"]):
        print("[FAIL_AMBIENTE] sessao sem sink privado ou emulador morto"); return 2
    if _run(["pactl", "list", "short", "sinks"]).stdout.find(sink) < 0:
        print("[FAIL_AMBIENTE] sink privado ausente"); return 2
    if not meta.get("audio_route") or not isolated.verify_audio_route(meta):
        print("[FAIL_AMBIENTE] sessao nao roteou o fluxo do PID exato na partida (audio_error="
              f"{meta.get('audio_error')}); captura recusada"); return 2
    if not isolated.request(root, "status")["audio_enabled"]:
        print("[FAIL_AMBIENTE] sessao ainda em mute; captura recusada"); return 2
    isolated.request(root, "run")
    moved = list(meta["audio_route"]["sink_inputs"])
    try:
        time.sleep(1.5)  # L048: warmup before measuring
        pcm = record_private_pcm(sink, seconds)
    finally:
        isolated.request(root, "pause")
    if not isolated.verify_audio_route(meta):
        print("[FAIL_AMBIENTE] rota de audio mudou durante a captura"); return 2
    effective = len(pcm) / 2 / RATE
    if not duration_sufficient(pcm, seconds):
        print(f"[FAIL] duracao efetiva {effective:.2f}s < pedida {seconds}s"); return 1
    wav = str(root / f"{out_name}.wav"); write_wav(wav, pcm)
    peak = _peak(pcm)
    import hashlib
    rec = {"session_id": meta["session_id"], "pid": pid, "rom_sha256": meta["rom_sha256"], "sink": sink,
           "moved_sink_inputs": moved, "requested_seconds": seconds, "effective_seconds": round(effective, 3),
           "audio_route": meta["audio_route"], "samples": len(pcm)//2, "peak": peak,
           "wav_sha256": hashlib.sha256(open(wav, "rb").read()).hexdigest(),
           "claim": "signal_from_session_pid; not music correctness"}
    (root / f"{out_name}.audio.json").write_text(json.dumps(rec, indent=1))
    print(f"[{'OK' if peak else 'FAIL'}] {wav} peak={peak} samples={len(pcm)//2}")
    return 0 if peak else 1

def _peak(pcm_bytes):
    import array
    a = array.array("h")
    a.frombytes(pcm_bytes[: len(pcm_bytes) // 2 * 2])
    return max((abs(x) for x in a), default=0)


def classify_silence(current_peak, historical_peak=None):
    """L048: peak=0 nao autoriza editar a ROM sem controle historico."""
    if current_peak > 0:
        return "signal"
    if historical_peak is None:
        return "silence_unconfirmed"
    if historical_peak > 0:
        return "current_rom_mute"
    return "environment_race"


def _emulicious_pids():
    r = _run(["pgrep", "-f", "Emulicious[.]jar"])
    if r.returncode != 0:
        return []
    return [p for p in r.stdout.split() if p.isdigit()]


def _kill_emulicious_zombies(except_pid=None):
    """L057/§93: discovery is not ownership; never terminate other agents."""
    return []

def write_wav(path, pcm_bytes, rate=RATE):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm_bytes)

def capture(project, rom, seconds=6, out_name="audio", reference_rom=None):
    import capture_evidence as ce
    for t in ("pactl", "parec", "java"):
        if not shutil.which(t):
            print(f"[FAIL_AMBIENTE] ferramenta ausente: {t}")
            return 2
    jar = ce.resolve_jar()
    if not jar:
        print("[FAIL_AMBIENTE] Emulicious.jar nao encontrado")
        return 2
    # L057: entrada e ABORT (nao mate processo do usuario sem pedir). A politica
    # KILL desta ferramenta vale so DENTRO da retentativa, quando ja sabemos que
    # o zumbi esta silenciando a captura da ROM certa (L048) — ver linha ~165.
    from emulator_session import require_no_stale
    if not require_no_stale(why="captura de audio isolada"):
        return 2

    out_dir = os.path.join(project, "out", "evidence")
    os.makedirs(out_dir, exist_ok=True)
    wav_path = os.path.join(out_dir, f"{out_name}.wav")

    mod = _run(["pactl", "load-module", "module-null-sink",
                f"sink_name={SINK}", "sink_properties=device.description=SMSForge"])
    if mod.returncode != 0:
        print(f"[FAIL_AMBIENTE] nao foi possivel criar sink isolado: {mod.stderr[:120]}")
        return 2
    mod_id = mod.stdout.strip()
    proc = None
    try:
        proc = subprocess.Popen(["java", "-jar", jar, "-set", "Update=0",
                                 os.path.abspath(rom)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
                                start_new_session=True)
        moved = []
        for _ in range(30):                       # espera o fluxo de audio nascer
            time.sleep(0.5)
            for si in _emulator_sink_inputs():
                if si not in moved and _run(["pactl", "move-sink-input", si,
                                             SINK]).returncode == 0:
                    moved.append(si)
            if moved:
                break
        if not moved:
            print("[FAIL] emulador nao produziu fluxo de audio para isolar")
            return 1
        # FALSO NEGATIVO CONHECIDO: gravar cedo demais (fluxo movido antes de a
        # musica entrar em regime) produz WAV 100% silencioso, indistinguivel de
        # "o jogo nao tem som". Isso quase levou a "consertar" um bug inexistente:
        # a ROM tinha audio e a captura e que estava adiantada. Por isso: warmup
        # crescente + repeticao enquanto o peak for zero.
        pcm = b""
        for attempt in range(3):
            time.sleep(1.5 + 2.0 * attempt)
            try:
                rec = subprocess.run(
                    ["parec", "-d", f"{SINK}.monitor", "--format=s16le",
                     f"--rate={RATE}", "--channels=1"],
                    capture_output=True, timeout=seconds + 5)
                pcm = rec.stdout
            except subprocess.TimeoutExpired as e:
                pcm = e.stdout or b""
            if len(pcm) >= RATE and _peak(pcm) > 0:
                break
            print(f"[retry] captura {attempt+1} veio silenciosa; "
                  "aumentando warmup (pode ser adiantamento, nao mudez)")
        if len(pcm) < RATE:                        # < 0.5s de audio
            print(f"[FAIL] captura vazia ({len(pcm)}B)")
            return 1
        if _peak(pcm) == 0:
            # L048: silencio apos warmup e corrida de ambiente ate prova em
            # contrario. Mata zumbis (exceto este processo) e tenta de novo.
            extra = _kill_emulicious_zombies(except_pid=proc.pid if proc else None)
            if extra:
                print(f"[retry] {len(extra)} java zumbi(s) encerrado(s); "
                      "recapturando (L048)")
                time.sleep(1.5)
                try:
                    rec = subprocess.run(
                        ["parec", "-d", f"{SINK}.monitor", "--format=s16le",
                         f"--rate={RATE}", "--channels=1"],
                        capture_output=True, timeout=seconds + 5)
                    pcm = rec.stdout or b""
                except subprocess.TimeoutExpired as e:
                    pcm = e.stdout or b""
            if _peak(pcm) == 0:
                hist_peak = None
                ref = reference_rom
                if not ref:
                    auto = os.path.join(project, "out", "evidence", "audio_ref.sms")
                    if os.path.isfile(auto):
                        ref = auto
                if ref and os.path.isfile(ref) and os.path.abspath(ref) != os.path.abspath(rom):
                    print(f"[retry] controle historico na mesma rodada: {ref}")
                    # nao relanca o emulador aqui (harness vivo); so classifica
                    # se o caller passou um wav de referencia ja medido.
                    ref_wav = os.path.join(os.path.dirname(wav_path), "audio_ref.wav")
                    if os.path.isfile(ref_wav):
                        try:
                            import audit_audio
                            hist_peak = audit_audio.read_wav_stats(ref_wav)[1]
                        except (OSError, ValueError, ImportError):
                            hist_peak = None
                kind = classify_silence(_peak(pcm), hist_peak)
                write_wav(wav_path, pcm)
                print(f"[FAIL] 3 capturas silenciosas: {wav_path} ({kind}). "
                      "Nao edite a ROM. Mate zumbis e grave um controle "
                      "historico na mesma rodada (L048/L019).")
                return 1
        write_wav(wav_path, pcm)
        print(f"[OK] audio do EMULADOR gravado (isolado): {wav_path} "
              f"({len(pcm)//2} amostras, {len(pcm)/2/RATE:.1f}s)")
        return 0
    finally:
        if proc:
            proc.terminate()
        _run(["pactl", "unload-module", mod_id])   # devolve o audio do usuario

def _self_check():
    import tempfile, struct, math
    d = tempfile.mkdtemp(prefix="smsaud_")
    try:
        # WAV escrito por esta ferramenta e legivel pelo gate audit_audio
        import audit_audio
        pcm = b"".join(struct.pack("<h", int(12000 * math.sin(i / 8.0)))
                       for i in range(RATE))
        p = os.path.join(d, "t.wav")
        write_wav(p, pcm)
        st = audit_audio.read_wav_stats(p)
        assert st is not None, "audit_audio nao conseguiu ler o WAV gerado"
        n, peak, active = st
        assert n == RATE, f"amostras erradas: {n}"
        assert peak > 10000, f"peak inesperado: {peak}"
        assert active > 90, f"tom continuo deveria ser ~100% ativo: {active}"
        # silencio tem que ser detectavel como tal
        ps = os.path.join(d, "s.wav")
        write_wav(ps, b"\x00\x00" * RATE)
        n2, peak2, active2 = audit_audio.read_wav_stats(ps)
        assert peak2 == 0 and active2 == 0, "silencio deveria dar peak/active 0"
        assert duration_sufficient(b"\0" * (RATE * 2), 1)
        assert duration_sufficient(b"\0" * (RATE * 19 // 10), 1)
        assert not duration_sufficient(b"\0" * (RATE * 19 // 10 - 2), 1)
        assert not duration_sufficient(b"", 1)
        assert not duration_sufficient(b"", 0)
        # deteccao de fluxo do emulador nao inventa resultado sem emulador
        assert isinstance(_emulator_sink_inputs(), list)
        assert sink_inputs_by_pid(2**22 + 12345) == [], 'PID inexistente nao pode casar fluxo'
        # L048: classificar silencio exige controle historico
        assert classify_silence(500, None) == "signal"
        assert classify_silence(0, None) == "silence_unconfirmed"
        assert classify_silence(0, 900) == "current_rom_mute"
        assert classify_silence(0, 0) == "environment_race"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] capture_audio (WAV gerado e legivel pelo audit_audio; "
          "tom ativo, silencio e corrida L048 distinguidos)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--rom")
    ap.add_argument("--session",help="private session ID; sink privado por sessao, fluxo do PID exato")
    ap.add_argument("--seconds", type=int, default=6)
    ap.add_argument("--out", default="audio")
    ap.add_argument("--reference-rom",
                    help="ROM historica com som conhecido (controle L048)")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    if a.session:
        return capture_session(a.session, a.seconds, a.out)
    if not (a.project and a.rom):
        print("[FAIL] --project e --rom obrigatorios", file=sys.stderr)
        return 3
    return capture(a.project, a.rom, a.seconds, a.out, a.reference_rom)

if __name__ == "__main__":
    sys.exit(main())
