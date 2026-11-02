#!/usr/bin/env python3
"""reconcile_claims.py — o eixo marcado como verdadeiro tem lastro no artefato?

`audit_claims.py` checa o TETO do claim (nao prometer mais do que o aprovado).
Este gate checa a COERENCIA: `out/build_record.json` declara os 7 eixos, mas
quem os preenche e o proprio processo que quer entregar. Se `evidence.json`
registra `interaction_proven: false` e o build_record diz `gameplay: true`,
a fabrica esta se contradizendo por escrito.

Regra: eixo `true` no build_record EXIGE artefato que o sustente.

Identidade: ROM exata do recibo (ou nome nominal do manifesto em recibos
legados), SHA calculado igual ao recibo, nunca arquivo mais recente. Candidata
usa --build-record/--current-rom e evidencias/sessao explicitamente selecionadas.

validation_report significa somente pre_gates_only com entradas atuais por
hash/conjunto; nao e validacao de gameplay/budget. memory_bank_atualizado
significa somente documento legivel/fresco citando o SHA completo. Midia exige
ROM/sessao/artefato vinculados; projecoes reutilizam o consumidor OpenBOR.
Coerencia nao autentica o produtor nem aprova entrega.

Uso: reconcile_claims.py --project <dir> [--json <saida>] [--self-check]
Exit: 0 coerente | 1 eixo sem lastro | 3 uso
"""
import sys, os, json, argparse, hashlib, re, wave
from pathlib import Path
from measure_runtime_probe import runtime_fps_verdict

def _load(path):
    try:
        with open(path, encoding="utf-8") as source:
            data = json.load(source)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError, UnicodeError):
        return None


def select_rom(project, rec=None, current_rom=None):
    """One owning selector: receipt path, or explicit legacy nominal name.

    Never choose by mtime. Legacy candidate receipts already contain the exact
    path in steps.rom; legacy nominal receipts use the project manifest name.
    An explicit ROM must still agree with the selected receipt's SHA and path.
    """
    root = Path(project).resolve()
    rec = rec if rec is not None else _load(root / "out/build_record.json")
    if not isinstance(rec, dict):
        raise ValueError("recibo ausente ou ilegivel")
    value = rec.get("rom_path")
    if not value and rec.get("schema") == "smsforge.candidate_build/v1":
        step = rec.get("steps", {}).get("rom", "")
        match = re.fullmatch(r"(.+) \([0-9]+ bytes\)", step)
        value = match.group(1) if match else None
    if not value:
        manifest = _load(root / ".mddev/project.json")
        name = manifest.get("name") if isinstance(manifest, dict) else None
        if not isinstance(name, str) or not name or Path(name).name != name or name in (".", ".."):
            raise ValueError("manifesto sem nome nominal inequivoco; informe recibo com rom_path")
        value = f"out/rom/{name}.sms"
    rom = (root / value).resolve()
    if not rom.is_relative_to(root / "out") or not rom.is_file():
        raise ValueError("ROM do recibo ausente ou fora do out do consumidor")
    if current_rom is not None:
        explicit = (root / current_rom).resolve()
        if explicit != rom:
            raise ValueError("ROM explicita diverge do caminho do recibo")
    digest = _sha256(rom)
    if rec.get("rom_sha256") != digest:
        raise ValueError("SHA calculado da ROM diverge do recibo")
    if "rom_bytes" in rec and rec["rom_bytes"] != rom.stat().st_size:
        raise ValueError("tamanho da ROM diverge do recibo")
    return rom, digest


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _rom_sha(project, rec=None, current_rom=None):
    try:
        return select_rom(project, rec, current_rom)[1]
    except (OSError, ValueError, TypeError, AttributeError):
        return None


def _session_bound(doc, artifact, sha):
    """Check the owning private session and its frozen ROM, including stale media.

    This verifies identity/chronology only, never truth of gameplay assertions.
    OpenBOR's sealed bundle consumer is used separately for its projections.
    """
    from session_bridge import isolated
    sid = doc.get("session_id")
    if not isinstance(sid, str) or not re.fullmatch(r"[0-9a-f]{32}", sid):
        return False
    try:
        root, meta = isolated.load(sid)
        if doc.get("rom_sha256") != sha or meta.get("rom_sha256") != sha:
            return False
        if _sha256(root / "emulator/rom.sms") != sha:
            return False
        created = meta["created_at"]
        captured = doc.get("captured_at", Path(artifact).stat().st_mtime)
        if not created <= captured <= meta.get("closed_at", float("inf")):
            return False
        if Path(artifact).stat().st_mtime < created:
            return False
        return root, meta
    except (OSError, ValueError, TypeError, KeyError):
        return False


def _projection_support(project, ev, rom, fps):
    """Reconsume the official sealed OpenBOR bundle, not its cached PASS."""
    try:
        from openbor2sms.evidence_consumer import consume
        sha = _sha256(rom)
        if ev.get("rom_sha256") != sha:
            return {}
        ref = ev["sources"]["bundle"]
        bundle = Path(project) / ref["path"]
        if _sha256(bundle) != ref["sha256"]:
            return {}
        result = consume(bundle, rom)
        if not result["eligible"]:
            return {}
        axes = dict(result["axes"])
        # A valid bundle does not authenticate arbitrary projected FPS values.
        source = fps.get("source", {})
        raw_path = Path(project) / source.get("path", "")
        raw = _load(raw_path) or {}
        if (_sha256(raw_path) != source.get("sha256") or raw.get("rom_sha256") != sha or
            raw.get("session_id") != fps.get("session_id") or
            any(raw.get(key) != fps.get(key) for key in (
                "region", "fps_janelas", "frames_delta_total", "frame_advance_proved", "fps_constante"))):
            axes["fps_constante"] = False
        return axes
    except (OSError, ValueError, KeyError, TypeError, ImportError):
        return {}


def _audio_supported(project, rom=None, sha=None, evidence_dir=None, expected_session=None):
    """Native capture_audio sidecar + owning session + WAV hash + scoped signal.

    Legacy loose WAVs remain historical, never an automatic current approval.
    Default signal floor is music's 90%; SFX-only callers must explicitly use
    the existing audit_audio contract with active_floor=5 in their sidecar.
    """
    import audit_audio
    if rom is None:
        try:
            rom, sha = select_rom(project)
        except (OSError, ValueError, TypeError):
            return False
    directory = Path(evidence_dir) if evidence_dir else Path(project) / "out/evidence"
    for sidecar in sorted(directory.glob("*.audio.json")):
        meta = _load(sidecar)
        if not isinstance(meta, dict) or (expected_session is not None and meta.get("session_id") != expected_session):
            continue
        wav = sidecar.with_name(sidecar.name.removesuffix(".audio.json") + ".wav")
        try:
            bound = _session_bound(meta, wav, sha)
            if not bound or meta.get("wav_sha256") != _sha256(wav):
                continue
            _, session = bound
            from openbor2sms.evidence_consumer import _wav
            validated = _wav(wav.read_bytes(), meta, {
                "initial": session, "created": session["created_at"],
                "closed": session.get("closed_at", float("inf"))})
            floor = meta.get("active_floor", 90)
            if type(floor) not in (int, float) or not 5 <= floor <= 100:
                continue
            problems, stats = audit_audio.audit(str(wav), project, floor)
            if not problems and stats[0] == validated["samples"] and stats[1] == meta.get("peak"):
                return True
        except (OSError, ValueError, TypeError, KeyError, EOFError, wave.Error):
            continue
    return False


def _inputs_current(project, rec):
    inputs = rec.get("input_sha256")
    if not isinstance(inputs, dict) or not inputs:
        return False
    try:
        from build_inner import pre_gate_inputs
        validation = rec.get("pre_gate_input_sha256")
        return (isinstance(validation, dict) and validation == pre_gate_inputs(project)
                and all(_sha256(Path(project) / path) == digest for path, digest in inputs.items()))
    except (OSError, ValueError, TypeError, KeyError):
        return False


def axis_support(project, rec=None, *, current_rom=None, evidence_dir=None, session=None):
    """Scoped consistency predicates; no delivery or independent review approval."""
    rec = rec if rec is not None else (_load(Path(project) / "out/build_record.json") or {})
    try:
        rom, sha = select_rom(project, rec, current_rom)
        identity = True
        reason = ""
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        rom, sha, identity, reason = None, None, False, str(exc)
    directory = Path(evidence_dir) if evidence_dir else Path(project) / "out/evidence"
    ev = _load(directory / "evidence.json") or {}
    fps_path = directory / "fps.json"
    fps = _load(fps_path) or {}
    projected = _projection_support(project, ev, rom, fps) if identity and ev.get("artifact_kind") == "axis_evidence_projection" else {}
    if session:
        projected = {}  # Explicit native session cannot inherit another session's projection.
    selected_session = None
    if session:
        from session_bridge import isolated
        try:
            root, meta = isolated.load(session)
            if identity and meta.get("rom_sha256") == sha and _sha256(root / "emulator/rom.sms") == sha:
                selected_session = root, meta
        except (OSError, ValueError, KeyError, TypeError):
            pass
    boot = False
    if identity and ev.get("informative") is True and ev.get("rom_sha256") == sha:
        if projected:
            boot = projected.get("boot_emulador") is True
        elif _session_bound(ev, directory / "evidence.json", sha):
            from session_bridge import isolated
            root, _ = isolated.load(ev["session_id"])
            bundle = Path(ev.get("session_bundle", root / "nonexistent"))
            if not bundle.is_absolute():
                bundle = Path(project) / bundle
            ok, _ = isolated.check_bundle(bundle)
            capture = _load(bundle / "capture.json") or {}
            boot = ok and capture.get("session_id") == ev["session_id"] and capture.get("rom_sha256") == sha
            if boot:
                boot = bool(_session_bound(capture, bundle / Path(capture["path"]).name, sha))
    if session:
        boot = False
    if selected_session:
        from session_bridge import isolated
        root, meta = selected_session
        bundle = meta.get("published")
        if bundle:
            boot = isolated.check_bundle(bundle)[0]
            captured = _load(Path(bundle) / "capture.json") or {}
            boot = boot and captured.get("session_id") == meta["session_id"] and captured.get("rom_sha256") == sha
            if boot:
                boot = bool(_session_bound(captured, Path(bundle) / Path(captured["path"]).name, sha))
    mem_path = directory / "input_memory.json"
    mem = _load(mem_path) or {}
    gameplay = identity and ((projected.get("gameplay") is True) or
        (mem.get("input_provado") is True and mem.get("canal_teclado_vivo") is True
         and bool(_session_bound(mem, mem_path, sha))))
    fps_bound = identity and (bool(_session_bound(fps, fps_path, sha)) or
                              (projected.get("fps_constante") is True and fps.get("rom_sha256") == sha))
    if session:
        expected = selected_session[1]["session_id"] if selected_session else None
        gameplay = gameplay and mem.get("session_id") == expected
        fps_bound = fps_bound and fps.get("session_id") == expected
    audio_directory = selected_session[0] if selected_session else directory
    memory_ok = False
    try:
        memory = Path(project) / "doc/10-memory-bank.md"
        text = memory.read_text(encoding="utf-8")
        memory_ok = identity and bool(text.strip()) and sha in text and memory.stat().st_mtime >= rom.stat().st_mtime
    except (OSError, UnicodeError):
        pass
    return {
        "build": (identity, reason or "ROM/recibo sem identidade valida"),
        "validation_report": (identity and rec.get("steps", {}).get("pre_gates") == "pass" and _inputs_current(project, rec),
                              "pre-gates ausentes ou entradas atuais sem hashes correspondentes; escopo pre_gates_only"),
        "boot_emulador": (boot, "framebuffer sem bundle valido da mesma ROM/sessao"),
        "gameplay": (gameplay, "sem prova de input/consequencia vinculada a ROM/sessao"),
        "fps_constante": (fps_bound and runtime_fps_verdict(fps)["passed"],
                          "sem duas janelas vinculadas a ROM/sessao com alvo60/piso58 sem arredondar"),
        "audio": (identity and (not session or selected_session is not None) and
                  (projected.get("audio") is True or _audio_supported(project, rom, sha, audio_directory,
                     selected_session[1]["session_id"] if selected_session else None)),
                  "sem WAV/sidecar com SHA, sessao privada, duracao, rota e sinal no escopo declarado"),
        "memory_bank_atualizado": (memory_ok, "memoria ausente/ilegivel/stale ou sem SHA completo da ROM; escopo readable_current_rom_reference_only"),
    }


def reconcile(project, *, build_record=None, current_rom=None, evidence_dir=None, session=None):
    """Return consistency problems, even when all axes are false on a bad receipt."""
    record_path = Path(build_record) if build_record else Path(project) / "out/build_record.json"
    report = {"project": str(project), "build_record": str(record_path), "axes": {},
              "claim_ceiling": "record_consistency_only", "delivery_approved": False,
              "axis_scope": {"validation_report": "pre_gates_only",
                             "memory_bank_atualizado": "readable_current_rom_reference_only"}}
    rec = _load(record_path)
    if not isinstance(rec, dict):
        return ["recibo ausente ou ilegivel — sem claims a conciliar"], report
    problems = []
    try:
        rom, sha = select_rom(project, rec, current_rom)
        report.update(rom=str(rom), rom_sha256=sha, identity_valid=True)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        problems.append("identidade: " + str(exc))
        report["identity_valid"] = False
    if session:
        from session_bridge import isolated
        try:
            root, metadata = isolated.load(session)
            if metadata.get("rom_sha256") != report.get("rom_sha256") or _sha256(root / "emulator/rom.sms") != report.get("rom_sha256"):
                problems.append("identidade: sessao pertence a outra ROM")
            report["session_id"] = metadata["session_id"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            problems.append("identidade: sessao ausente/ilegivel: " + str(exc))
    axes = rec.get("axes", {}) or {}
    report["axes_declared"] = axes
    for axis, (supported, why) in axis_support(project, rec, current_rom=current_rom, evidence_dir=evidence_dir, session=session).items():
        declared = axes.get(axis) is True
        report["axes"][axis] = {"declared": declared, "supported": bool(supported)}
        if declared and not supported:
            problems.append(f"eixo '{axis}' declarado TRUE mas {why}")
    if session and not report.get("identity_valid"):
        problems.append("sessao nao pode qualificar recibo/ROM divergentes")
    report["coherent"] = not problems
    return problems, report


def _self_check():
    import unittest
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent / "tests"),
                                               pattern="test_build_evidence_identity.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() and suite.countTestCases() and not result.skipped else 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--json")
    ap.add_argument("--build-record", help="recibo exato, inclusive candidato isolado")
    ap.add_argument("--current-rom", help="ROM exata; precisa concordar com o recibo")
    ap.add_argument("--session", help="sessao privada exata; consome bundle/sidecar dos produtores oficiais")
    ap.add_argument("--evidence-dir", help="diretorio explicito de evidencia desta verificacao")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()

    if a.self_check:
        return _self_check()

    problems, report = reconcile(a.project, build_record=a.build_record,
                                 current_rom=a.current_rom, evidence_dir=a.evidence_dir, session=a.session)
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
