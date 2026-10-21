#!/usr/bin/env python3
"""reconcile_claims.py — o eixo marcado como verdadeiro tem lastro no artefato?

`audit_claims.py` checa o TETO do claim (nao prometer mais do que o aprovado).
Este gate checa a COERENCIA: `out/build_record.json` declara os 7 eixos, mas
quem os preenche e o proprio processo que quer entregar. Se `evidence.json`
registra `interaction_proven: false` e o build_record diz `gameplay: true`,
a fabrica esta se contradizendo por escrito.

Regra: eixo `true` no build_record EXIGE artefato que o sustente.

Mapa eixo -> lastro exigido:
  build              out/rom/*.sms existe
  boot_emulador      evidence.json informative=true E rom_sha256 == ROM atual
  gameplay           evidence.json.interaction_proven=true E rom_sha256 == ROM atual
                     OU input_memory.json (input_provado + canal vivo + SHA da ROM)
  fps_constante      fps.json constante_50_60=true E rom_sha256 == ROM atual
  audio              arquivo de audio capturado (audit_audio.py e quem julga)
  validation_report  build_record.steps.pre_gates == pass
  memory_bank_atualizado   doc/10-memory-bank.md existe

Uso: reconcile_claims.py --project <dir> [--json <saida>] [--self-check]
Exit: 0 coerente | 1 eixo sem lastro | 3 uso
"""
import sys, os, json, glob, argparse

def _load(path):
    try:
        return json.load(open(path))
    except (OSError, json.JSONDecodeError):
        return None


def _rom_sha(project):
    import hashlib
    roms = glob.glob(os.path.join(project, "out", "rom", "*.sms"))
    if not roms:
        return None
    newest = max(roms, key=os.path.getmtime)
    h = hashlib.sha256()
    with open(newest, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _gameplay_supported(project, ev, rec):
    """Pixels (L018) OU memoria com SHA da ROM (L035/L039). Pixel sozinho
    neste host mentia (L038); RAM com canal morto tambem (L039). O booleano
    `interaction_proven` so vale para a ROM que o proprio evidence.json cita:
    um `true` herdado de outro binario nao prova o build atual."""
    sha = _rom_sha(project) or rec.get("rom_sha256")
    if bool((ev.get("gameplay") or {}).get("interaction_proven")):
        return bool(sha) and ev.get("rom_sha256") == sha
    mem = _load(os.path.join(project, "out", "evidence", "input_memory.json"))
    if not mem:
        return False
    return bool(mem.get("input_provado")
                and mem.get("canal_teclado_vivo")
                and sha
                and mem.get("rom_sha256") == sha)

def _audio_supported(project):
    """§26: wav ANTERIOR a ROM e prova de outro binario. O acervo costuma ter
    .wav de builds antigas; existir nao basta, precisa ser desta ROM.

    Fresco tambem NAO basta: um .wav novo e SILENCIOSO sustentava o eixo.
    Aconteceu em 2026-09-01 — captura adiantada gerou wav com peak=0 e o eixo
    passou. Exigir tambem SINAL (audit_audio e quem julga o mix)."""
    wavs = glob.glob(os.path.join(project, "out", "evidence", "*.wav"))
    roms = glob.glob(os.path.join(project, "out", "rom", "*.sms"))
    if not (wavs and roms):
        return False
    newest_rom = max(os.path.getmtime(r) for r in roms)
    import audit_audio
    for w in wavs:
        if os.path.getmtime(w) <= newest_rom:
            continue
        st = audit_audio.read_wav_stats(w)
        if st and st[1] > 0:              # peak > 0
            return True
    return False


def axis_support(project, rec=None):
    """FONTE UNICA da verdade sobre lastro: {eixo: (sustentado, porque_nao)}.

    Extraida de `reconcile` para que `build_inner.py` DERIVE os eixos daqui em
    vez de herdar do registro anterior. Antes, nenhuma ferramenta promovia eixo
    para true: o build inicializava tudo em false e so herdava, entao o primeiro
    true de qualquer projeto so podia ter vindo de edicao a mao do
    build_record.json — exatamente o que o runbook release-rom.md proibe. Com os
    dois lados lendo esta funcao, o veredito nao pode divergir entre quem grava
    e quem confere."""
    rec = rec if rec is not None else (_load(os.path.join(
        project, "out", "build_record.json")) or {})
    ev = _load(os.path.join(project, "out", "evidence", "evidence.json")) or {}
    fps = _load(os.path.join(project, "out", "evidence", "fps.json")) or {}
    sha = _rom_sha(project) or rec.get("rom_sha256")
    return {
        "build": (
            bool(glob.glob(os.path.join(project, "out", "rom", "*.sms"))),
            "nao ha ROM em out/rom/"),
        "validation_report": (
            (rec.get("steps", {}) or {}).get("pre_gates") == "pass",
            "build_record.steps.pre_gates != 'pass'"),
        "boot_emulador": (
            bool(ev.get("informative")) and bool(sha)
            and ev.get("rom_sha256") == sha,
            "evidence.json nao tem informative=true para a ROM atual "
            "(rom_sha256 ausente ou de outro binario)"),
        "gameplay": (
            _gameplay_supported(project, ev, rec),
            "nem evidence.json.interaction_proven para a ROM atual nem "
            "input_memory.json (input_provado + canal vivo + SHA da ROM) "
            "sustentam o eixo"),
        "fps_constante": (
            bool(fps.get("constante_50_60")) and bool(sha)
            and fps.get("rom_sha256") == sha,
            "fps.json nao tem constante_50_60=true para a ROM atual "
            "(rom_sha256 ausente ou de outro binario)"),
        "audio": (
            _audio_supported(project),
            "nao ha captura de audio (.wav) POSTERIOR a ROM e COM SINAL em "
            "out/evidence/ (wav antigo, ou novo porem silencioso, nao prova nada)"),
        "memory_bank_atualizado": (
            os.path.isfile(os.path.join(project, "doc", "10-memory-bank.md")),
            "doc/10-memory-bank.md nao existe"),
    }


def reconcile(project):
    """Retorna (problems, report)."""
    problems = []
    report = {"project": project, "axes": {}}
    rec = _load(os.path.join(project, "out", "build_record.json"))
    if rec is None:
        return ["out/build_record.json ausente ou ilegivel — sem claims a conciliar"], report

    axes = rec.get("axes", {}) or {}
    report["axes_declared"] = axes

    for axis, (supported, why) in axis_support(project, rec).items():
        declared = bool(axes.get(axis))
        report["axes"][axis] = {"declared": declared, "supported": supported}
        if declared and not supported:
            problems.append(f"eixo '{axis}' declarado TRUE mas {why}")

    report["coherent"] = not problems
    return problems, report

def _self_check():
    import tempfile, shutil
    d = tempfile.mkdtemp(prefix="smsrec_")
    try:
        def build(axes, ev=None, fps=None, rom=True, wav=True, mb=True):
            p = tempfile.mkdtemp(dir=d)
            os.makedirs(os.path.join(p, "out", "rom"))
            os.makedirs(os.path.join(p, "out", "evidence"))
            os.makedirs(os.path.join(p, "doc"))
            if rom:
                open(os.path.join(p, "out", "rom", "a.sms"), "wb").write(b"\0")
            rom_sha = None
            if rom:
                import hashlib as _h
                rom_sha = _h.sha256(
                    open(os.path.join(p, "out", "rom", "a.sms"), "rb").read()
                ).hexdigest()
            if wav:
                # WAV valido COM sinal (16-bit mono, amostras nao-zero)
                import wave as _w, struct as _s
                with _w.open(os.path.join(p, "out", "evidence", "a.wav"), "wb") as _f:
                    _f.setnchannels(1); _f.setsampwidth(2); _f.setframerate(8000)
                    _f.writeframes(b"".join(_s.pack("<h", 9000) for _ in range(800)))
            if mb:
                open(os.path.join(p, "doc", "10-memory-bank.md"), "w").write("x")
            json.dump({"axes": axes, "steps": {"pre_gates": "pass"}},
                      open(os.path.join(p, "out", "build_record.json"), "w"))
            if ev is not None:
                ev = dict(ev)
                if rom_sha:
                    ev.setdefault("rom_sha256", rom_sha)
                json.dump(ev, open(os.path.join(p, "out", "evidence",
                                                "evidence.json"), "w"))
            if fps is not None:
                fps = dict(fps)
                if rom_sha:
                    fps.setdefault("rom_sha256", rom_sha)
                json.dump(fps, open(os.path.join(p, "out", "evidence",
                                                 "fps.json"), "w"))
            return p

        all_true = {"build": True, "validation_report": True, "boot_emulador": True,
                    "gameplay": True, "fps_constante": True, "audio": True,
                    "memory_bank_atualizado": True}

        # COERENTE: todo eixo true com lastro
        ok = build(all_true,
                   ev={"informative": True, "gameplay": {"interaction_proven": True}},
                   fps={"constante_50_60": True})
        p, r = reconcile(ok)
        assert not p, f"projeto coerente nao deveria reprovar: {p}"
        assert r["coherent"]

        # REPROVA: gameplay=true com interaction_proven=false (caso real do lab)
        bad = build(all_true,
                    ev={"informative": True, "gameplay": {"interaction_proven": False}},
                    fps={"constante_50_60": True})
        p, _ = reconcile(bad)
        assert any("gameplay" in x for x in p), f"faltou pegar gameplay sem lastro: {p}"

        # PASS: pixels falham, mas input_memory.json prova RAM com SHA da ROM
        ram = build(all_true,
                    ev={"informative": True, "gameplay": {"interaction_proven": False}},
                    fps={"constante_50_60": True})
        romp = glob.glob(os.path.join(ram, "out", "rom", "*.sms"))[0]
        import hashlib as _hh
        sha = _hh.sha256(open(romp, "rb").read()).hexdigest()
        json.dump({"axes": all_true, "steps": {"pre_gates": "pass"},
                   "rom_sha256": sha},
                  open(os.path.join(ram, "out", "build_record.json"), "w"))
        json.dump({"input_provado": True, "canal_teclado_vivo": True,
                   "rom_sha256": sha},
                  open(os.path.join(ram, "out", "evidence",
                                    "input_memory.json"), "w"))
        p, _ = reconcile(ram)
        assert not any("gameplay" in x for x in p), \
            f"prova por memoria com SHA deveria fechar gameplay: {p}"

        json.dump({"input_provado": True, "canal_teclado_vivo": True,
                   "rom_sha256": "deadbeef"},
                  open(os.path.join(ram, "out", "evidence",
                                    "input_memory.json"), "w"))
        p, _ = reconcile(ram)
        assert any("gameplay" in x for x in p), \
            f"input_memory de outra ROM deveria reprovar: {p}"

        # REPROVA: evidence.json informative=true de OUTRA ROM (booleano sozinho)
        stale_ev = build(all_true,
                         ev={"informative": True, "rom_sha256": "deadbeef",
                             "gameplay": {"interaction_proven": True}},
                         fps={"constante_50_60": True})
        p, _ = reconcile(stale_ev)
        assert any("'boot_emulador'" in x for x in p), \
            f"evidence de outra ROM deveria reprovar boot: {p}"
        assert any("'gameplay'" in x for x in p), \
            f"interaction_proven de outra ROM deveria reprovar gameplay: {p}"

        # REPROVA: fps.json constante=true de OUTRA ROM (booleano sozinho)
        stale_fps = build(all_true,
                          ev={"informative": True,
                              "gameplay": {"interaction_proven": True}},
                          fps={"constante_50_60": True,
                               "rom_sha256": "deadbeef"})
        p, _ = reconcile(stale_fps)
        assert any("'fps_constante'" in x for x in p), \
            f"fps de outra ROM deveria reprovar: {p}"

        # REPROVA: fps=true sem fps.json
        p, _ = reconcile(build(all_true,
                               ev={"informative": True,
                                   "gameplay": {"interaction_proven": True}}))
        assert any("fps_constante" in x for x in p), "faltou pegar fps sem lastro"

        # REPROVA: audio=true com wav novo porem SILENCIOSO
        mudo = build(all_true, ev={"informative": True,
                                   "gameplay": {"interaction_proven": True}},
                     fps={"constante_50_60": True})
        import wave as _w2
        _wp = glob.glob(os.path.join(mudo, "out", "evidence", "*.wav"))[0]
        with _w2.open(_wp, "wb") as _f:
            _f.setnchannels(1); _f.setsampwidth(2); _f.setframerate(8000)
            _f.writeframes(b"\x00\x00" * 800)
        p, _ = reconcile(mudo)
        assert any("'audio'" in x for x in p), f"wav silencioso deveria reprovar: {p}"

        # REPROVA: audio=true com wav ANTERIOR a ROM (prova de outro binario)
        stale = build(all_true, ev={"informative": True,
                                    "gameplay": {"interaction_proven": True}},
                      fps={"constante_50_60": True})
        import time as _t
        _rom = glob.glob(os.path.join(stale, "out", "rom", "*.sms"))[0]
        _wav = glob.glob(os.path.join(stale, "out", "evidence", "*.wav"))[0]
        os.utime(_wav, (1000, 1000)); os.utime(_rom, (2000, 2000))
        p, _ = reconcile(stale)
        assert any("'audio'" in x for x in p), f"wav anterior a ROM deveria reprovar: {p}"

        # REPROVA: build=true sem ROM; audio=true sem wav
        p, _ = reconcile(build(all_true,
                               ev={"informative": True,
                                   "gameplay": {"interaction_proven": True}},
                               fps={"constante_50_60": True}, rom=False, wav=False))
        assert any("'build'" in x for x in p), "faltou pegar build sem ROM"
        assert any("'audio'" in x for x in p), "faltou pegar audio sem wav"

        # NAO reprova eixo declarado FALSE sem lastro (honestidade nao e erro)
        p, _ = reconcile(build({"gameplay": False}, ev={"informative": False}))
        assert not any("gameplay" in x for x in p), \
            "eixo declarado false nao pode ser reprovado por falta de lastro"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] reconcile_claims (pega eixo TRUE sem lastro no "
          "artefato; nao pune eixo declarado FALSE)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()

    if a.self_check:
        return _self_check()

    problems, report = reconcile(a.project)
    if a.json:
        json.dump({"problems": problems, **report}, open(a.json, "w"), indent=2)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} eixo(s) sem lastro. "
              "Eixo verdadeiro no papel e falso no artefato e overclaim.")
        return 1
    print("[PASS] eixos declarados batem com os artefatos de evidencia")
    return 0

if __name__ == "__main__":
    sys.exit(main())
