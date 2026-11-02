#!/usr/bin/env python3
"""Project real O3 evidence into the canonical axis files the build reads.

This is NOT a new measurement. It copies fields from the sealed consumer
bundle, the MRP3 runtime metrics and the QA reports into
`out/evidence/evidence.json` and `out/evidence/fps.json`, but only after
proving that every source names the SAME ROM SHA as `--current-rom`.

A stale report from another binary is refused and nothing is written. That is
the hardening the M8 projection lacked: an `informative: true` or
`constante_50_60: true` boolean is not self-authenticating; the SHA makes the
claim belong to this build. `reconcile_claims.py` independently requires the
same SHA.

Usage:
  python3 -m openbor2sms.axis_projection --project <dir> \
      --current-rom <rom.sms> [--bundle ...] [--consumption ...] \
      [--runtime-metrics ...] [--qa-runtime ...] [--qa-visual ...] \
      [--wav ...] [--out-dir ...]
  python3 -m openbor2sms.axis_projection --self-check

The defaults are the sealed M8 a7f02b84 sources so the historical projection
is reproducible when that ROM is supplied explicitly. For a new ROM, pass a
new consumer bundle; the tool refuses to reuse the M8 one.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from measure_runtime_probe import runtime_fps_verdict

DEFAULT_SOURCES = {
    "bundle": "out/evidence/m8/bundle_a7f02b84/bundle.json",
    "consumption": "out/evidence/m8/consumption_a7f02b84.json",
    "runtime_metrics": (
        "out/evidence/m8/session_inputs/"
        "4f1f45411420453d9c93a76f160410ba/runtime_metrics.json"
    ),
    "qa_runtime": (
        "out/evidence/m8/qa/runtime/"
        "run_ce3bb103775b4d07aff60ee736a2a210/report.json"
    ),
    "qa_visual": (
        "out/evidence/m8/qa/visual/"
        "run_a4c73f390ab44855a855e69044cf0eaa/report.json"
    ),
    "wav": "out/evidence/m8/bundle_a7f02b84/artifacts/audio_signal.wav",
}


class ProjectionError(ValueError):
    """A source is missing, incoherent, or belongs to another ROM."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProjectionError(f"fonte ilegivel {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProjectionError(f"fonte nao e objeto JSON: {path}")
    return data


def _resolve(project: Path, value: str, label: str) -> Path:
    p = Path(value)
    if not p.is_absolute():
        p = project / p
    if not p.is_file():
        raise ProjectionError(f"{label} ausente: {value}")
    return p.resolve()


def _relative(project: Path, path: Path) -> str:
    try:
        return str(path.relative_to(project))
    except ValueError:
        return str(path)


def _current_rom(project: Path, explicit: str | None, build_record: str | None = None) -> Path:
    from reconcile_claims import select_rom
    receipt = Path(build_record) if build_record else project / "out/build_record.json"
    if not build_record and explicit:
        selected = (project / explicit).resolve()
        if selected.is_relative_to(project / "out/candidates"):
            receipt = selected.parent.parent / "build_record.json"
    try:
        rec = _load(receipt)
        return select_rom(project, rec, explicit)[0]
    except (OSError, ValueError) as exc:
        raise ProjectionError(str(exc)) from exc


def project(
    project: str | Path,
    *,
    current_rom: str | None = None,
    build_record: str | None = None,
    bundle: str | None = None,
    consumption: str | None = None,
    runtime_metrics: str | None = None,
    qa_runtime: str | None = None,
    qa_visual: str | None = None,
    wav: str | None = None,
    out_dir: str | None = None,
) -> dict:
    """Verify source ROM identity and write the two canonical projections.

    Raises ProjectionError before writing anything if a source is stale or
    incoherent. Returns a small summary with the written paths and hashes.
    """
    root = Path(project).resolve()
    rom = _current_rom(root, current_rom, build_record)
    current_sha = sha256_file(rom)

    paths = {
        "bundle": _resolve(root, bundle or DEFAULT_SOURCES["bundle"], "bundle"),
        "consumption": _resolve(
            root, consumption or DEFAULT_SOURCES["consumption"], "consumption"),
        "runtime_metrics": _resolve(
            root, runtime_metrics or DEFAULT_SOURCES["runtime_metrics"],
            "runtime_metrics"),
        "qa_runtime": _resolve(
            root, qa_runtime or DEFAULT_SOURCES["qa_runtime"], "qa_runtime"),
        "qa_visual": _resolve(
            root, qa_visual or DEFAULT_SOURCES["qa_visual"], "qa_visual"),
        "wav": _resolve(root, wav or DEFAULT_SOURCES["wav"], "wav"),
    }
    before = {key: sha256_file(path) for key, path in paths.items()}
    bundle_doc = _load(paths["bundle"])
    cons = _load(paths["consumption"])
    mrp3 = _load(paths["runtime_metrics"])
    for role in ("qa_runtime", "qa_visual"):
        report = _load(paths[role])
        request_ref = report.get("request", {})
        request_path = Path(request_ref.get("path", ""))
        if not request_path.is_absolute():
            request_path = paths[role].parent / request_path
        if not request_path.is_file() or sha256_file(request_path) != request_ref.get("sha256"):
            raise ProjectionError(f"{role}: pedido ausente ou SHA divergente")
        request = _load(request_path)
        if request.get("rom", {}).get("sha256") != current_sha:
            raise ProjectionError(f"{role}: QA de outra ROM")
        from audit_subagent_session import validate_report
        checked = validate_report(report, request)
        if not checked["tests_passed"]:
            raise ProjectionError(f"{role}: QA nao aprovada: {checked['problems']}")
    from .evidence_consumer import consume
    checked_bundle = consume(paths["bundle"], rom)
    if not checked_bundle["eligible"]:
        raise ProjectionError(f"bundle inelegivel: {checked_bundle['problems']}")

    source_sha = ((bundle_doc.get("rom") or {}).get("sha256") or "").lower()
    cons_sha = (cons.get("rom_sha256") or "").lower()
    mrp3_sha = (mrp3.get("rom_sha256") or "").lower()
    if not (source_sha and source_sha == cons_sha == mrp3_sha):
        raise ProjectionError(
            "fontes divergem no SHA da ROM: "
            f"bundle={source_sha[:12]} consumption={cons_sha[:12]} "
            f"runtime={mrp3_sha[:12]}")
    if source_sha != current_sha:
        raise ProjectionError(
            "ROM atual nao e a ROM das fontes: "
            f"atual={current_sha[:12]} fontes={source_sha[:12]}; "
            "projecao recusada (nao herde eixos de outro binario)")

    if cons.get("eligible") is not True or cons.get("problems"):
        raise ProjectionError(
            f"consumption inelegivel: eligible={cons.get('eligible')!r} "
            f"problems={cons.get('problems')!r}")
    if cons.get("bundle_sha256") != before["bundle"] or cons.get("coverage") != checked_bundle.get("coverage"):
        raise ProjectionError("consumption nao corresponde ao bundle revalidado")
    axes = checked_bundle.get("axes") or {}
    missing_axes = [a for a in ("boot_emulador", "gameplay",
                                "fps_constante", "audio") if not axes.get(a)]
    if missing_axes:
        raise ProjectionError(f"consumption sem eixos: {missing_axes}")
    fps_check = runtime_fps_verdict(mrp3)
    if not fps_check["passed"]:
        raise ProjectionError("runtime_metrics nao prova alvo60/piso58 FPS da ROM sem arredondar")
    janelas = mrp3.get("fps_janelas") or []
    if mrp3.get("region") != "NTSC" or len(janelas) != 3:
        raise ProjectionError(
            f"runtime_metrics fora do contrato NTSC/3 janelas: "
            f"region={mrp3.get('region')!r} janelas={len(janelas)}")

    audio_art = next(
        (a for a in (bundle_doc.get("artifacts") or [])
         if a.get("id") == "audio_signal" or a.get("kind") == "wav"),
        None,
    )
    wav_sha = sha256_file(paths["wav"])
    if audio_art:
        declared = (((audio_art.get("file") or {}).get("sha256")) or "").lower()
        if declared and declared != wav_sha:
            raise ProjectionError(
                "wav diverge do artefato selado do bundle: "
                f"wav={wav_sha[:12]} bundle={declared[:12]}")

    cov = cons.get("coverage") or {}
    try:
        boot = cov["boot_emulador"]["derived"]
        gameplay = cov["gameplay"]["derived"]
        fps_cov = cov["fps_constante"]["derived"]
    except (KeyError, TypeError) as exc:
        raise ProjectionError(f"coverage incompleto: {exc}") from exc

    sources = {
        "bundle": {
            "path": _relative(root, paths["bundle"]),
            "sha256": sha256_file(paths["bundle"]),
        },
        "consumption": {
            "path": _relative(root, paths["consumption"]),
            "sha256": sha256_file(paths["consumption"]),
        },
        "runtime_mrp3": {
            "path": _relative(root, paths["runtime_metrics"]),
            "sha256": sha256_file(paths["runtime_metrics"]),
            "session_id": mrp3.get("session_id"),
        },
        "qa_runtime": {
            "path": _relative(root, paths["qa_runtime"]),
            "sha256": sha256_file(paths["qa_runtime"]),
        },
        "qa_visual": {
            "path": _relative(root, paths["qa_visual"]),
            "sha256": sha256_file(paths["qa_visual"]),
        },
        "audio": {
            "path": _relative(root, paths["wav"]),
            "sha256": wav_sha,
        },
    }
    generated_at = _dt.date.today().isoformat()

    evidence = {
        "schema": "openbor_sms_axis_evidence_projection_v1",
        "artifact_kind": "axis_evidence_projection",
        "generated_at": generated_at,
        "rom_sha256": current_sha,
        "rom_bytes": (bundle_doc.get("rom") or {}).get("bytes") or rom.stat().st_size,
        "region": "NTSC",
        "informative": True,
        "boot": {
            "proof": cov["boot_emulador"].get("proof"),
            "canvas": boot.get("canvas"),
            "artifacts": cov["boot_emulador"].get("artifacts"),
        },
        "gameplay": {
            "interaction_proven": True,
            "proof": cov["gameplay"].get("proof"),
            "artifacts": cov["gameplay"].get("artifacts"),
            "before": gameplay.get("before"),
            "after": gameplay.get("after"),
            "relation": gameplay.get("relation"),
            "qa_runtime_cases": ["boot_baseline", "attack_contact"],
        },
        "sources": sources,
        "claim_ceiling": "assigned_checks_only",
        "limits": [
            "projecao de evidencia aceita; nao e nova medicao",
            "consumer: assigned_checks_only; sem aprovacao de entrega ou qualidade visual",
            "PAL nao medido",
        ],
    }
    fps_doc = {
        "schema": "openbor_sms_fps_evidence_projection_v1",
        "artifact_kind": "axis_evidence_projection",
        "generated_at": generated_at,
        "rom_sha256": current_sha,
        "region": mrp3.get("region"),
        "fps_acceptance": fps_check,
        "fps_constante": mrp3.get("fps_constante"),
        "frame_advance_proved": mrp3.get("frame_advance_proved"),
        "fps_janelas": janelas,
        "fps_spread": mrp3.get("fps_spread"),
        "frames_delta_total": mrp3.get("frames_delta_total"),
        "windows": len(janelas),
        "session_id": mrp3.get("session_id"),
        "source": sources["runtime_mrp3"],
        "claim_ceiling": "assigned_checks_only",
        "limits": [
            "NTSC apenas; PAL nao medido",
            "projecao do runtime_metrics_v1 do MRP3",
        ],
    }

    if before != {key: sha256_file(path) for key, path in paths.items()} or current_sha != sha256_file(rom):
        raise ProjectionError("fontes ou ROM mudaram durante preparacao")
    candidate_root = root / "out/candidates"
    default_out = rom.parent.parent / "evidence" if rom.is_relative_to(candidate_root) else root / "out/evidence"
    destination = Path(out_dir).resolve() if out_dir else default_out
    if rom.is_relative_to(candidate_root) and not destination.is_relative_to(rom.parent.parent):
        raise ProjectionError("projecao candidata deve permanecer no destino candidato")
    destination.mkdir(parents=True, exist_ok=True)
    evidence_path = destination / "evidence.json"
    fps_path = destination / "fps.json"
    wav_path = destination / f"audio_{current_sha[:8]}.wav"
    evidence_path.write_text(
        json.dumps(evidence, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    fps_path.write_text(
        json.dumps(fps_doc, indent=1, ensure_ascii=False) + "\n",
        encoding="utf-8")
    shutil.copy2(paths["wav"], wav_path)
    return {
        "rom_sha256": current_sha,
        "evidence": str(evidence_path),
        "evidence_sha256": sha256_file(evidence_path),
        "fps": str(fps_path),
        "fps_sha256": sha256_file(fps_path),
        "audio": str(wav_path),
        "audio_sha256": sha256_file(wav_path),
        "sources": sources,
    }


def _self_check() -> int:
    import unittest
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parents[1] / "tests"),
                                               pattern="test_axis_projection.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() and not result.skipped and suite.countTestCases() else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Projeta evidencia selada nos caminhos canonicos, "
                    "exigindo o SHA da ROM atual.")
    ap.add_argument("--project", default=".")
    ap.add_argument("--current-rom")
    ap.add_argument("--build-record", help="recibo exato; candidata usa o recibo no proprio destino")
    for key in DEFAULT_SOURCES:
        ap.add_argument("--" + key.replace("_", "-"), dest=key)
    ap.add_argument("--out-dir")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return _self_check()
    try:
        result = project(
            args.project,
            current_rom=args.current_rom,
            build_record=args.build_record,
            bundle=args.bundle,
            consumption=args.consumption,
            runtime_metrics=args.runtime_metrics,
            qa_runtime=args.qa_runtime,
            qa_visual=args.qa_visual,
            wav=args.wav,
            out_dir=args.out_dir,
        )
    except ProjectionError as exc:
        print(f"[REFUSE] {exc}")
        return 2
    print(f"[OK] rom {result['rom_sha256']}")
    print(f"evidence {result['evidence']} sha {result['evidence_sha256']}")
    print(f"fps      {result['fps']} sha {result['fps_sha256']}")
    print(f"audio    {result['audio']} sha {result['audio_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
