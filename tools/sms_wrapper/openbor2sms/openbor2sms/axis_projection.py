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


def _current_rom(project: Path, explicit: str | None) -> Path:
    if explicit:
        return _resolve(project, explicit, "ROM atual")
    roms = sorted((project / "out" / "rom").glob("*.sms"))
    if not roms:
        raise ProjectionError("nao ha ROM em out/rom/ para ancorar a projecao")
    return max(roms, key=lambda p: p.stat().st_mtime).resolve()


def project(
    project: str | Path,
    *,
    current_rom: str | None = None,
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
    rom = _current_rom(root, current_rom)
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
    bundle_doc = _load(paths["bundle"])
    cons = _load(paths["consumption"])
    mrp3 = _load(paths["runtime_metrics"])
    _load(paths["qa_runtime"])
    _load(paths["qa_visual"])

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
    axes = cons.get("axes") or {}
    missing_axes = [a for a in ("boot_emulador", "gameplay",
                                "fps_constante", "audio") if not axes.get(a)]
    if missing_axes:
        raise ProjectionError(f"consumption sem eixos: {missing_axes}")
    if mrp3.get("fps_constante") is not True or not mrp3.get("frame_advance_proved"):
        raise ProjectionError("runtime_metrics sem fps_constante/frame_advance_proved")
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
        "constante_50_60": True,
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

    destination = Path(out_dir).resolve() if out_dir else root / "out" / "evidence"
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
    base = Path(tempfile.mkdtemp(prefix="smspoj_"))
    try:
        def make_case(name: str, rom_bytes: bytes, source_sha: str | None = None):
            root = base / name
            (root / "out" / "rom").mkdir(parents=True)
            (root / "out" / "evidence").mkdir(parents=True)
            rom = root / "out" / "rom" / "a.sms"
            rom.write_bytes(rom_bytes)
            rom_sha = sha256_file(rom)
            wav = root / "sources" / "audio_signal.wav"
            wav.parent.mkdir(parents=True)
            wav.write_bytes(b"RIFF" + b"\x00" * 60)
            wav_sha = sha256_file(wav)
            qa = root / "sources" / "qa.json"
            qa.write_text("{}", encoding="utf-8")
            sha = rom_sha if source_sha is None else source_sha
            bundle = {
                "rom": {"sha256": sha, "bytes": len(rom_bytes)},
                "artifacts": [{
                    "id": "audio_signal",
                    "kind": "wav",
                    "file": {"path": "artifacts/audio_signal.wav",
                             "sha256": wav_sha, "bytes": wav.stat().st_size},
                }],
            }
            cons = {
                "rom_sha256": sha,
                "eligible": True,
                "problems": [],
                "axes": {"boot_emulador": True, "gameplay": True,
                         "fps_constante": True, "audio": True},
                "coverage": {
                    "boot_emulador": {"proof": "framebuffer",
                                      "artifacts": ["boot_png"],
                                      "derived": {"canvas": [256, 192]}},
                    "gameplay": {"proof": "input_ram_video",
                                 "artifacts": ["gameplay_observation"],
                                 "derived": {"before": 50, "after": 29,
                                             "relation": "decrease"}},
                    "fps_constante": {"proof": "regional_runtime_windows",
                                      "artifacts": ["fps_metrics"],
                                      "derived": {"region": "NTSC"}},
                    "audio": {"proof": "audio_signal",
                              "artifacts": ["audio_signal"],
                              "derived": {"peak": 1}},
                },
            }
            mrp3 = {
                "rom_sha256": sha,
                "session_id": "self-check",
                "fps_constante": True,
                "frame_advance_proved": True,
                "region": "NTSC",
                "fps_janelas": [59.6, 59.7, 59.8],
                "fps_spread": 0.2,
                "frames_delta_total": 100,
            }
            files = {}
            for key, doc in (("bundle", bundle), ("consumption", cons),
                             ("runtime_metrics", mrp3)):
                files[key] = root / "sources" / f"{key}.json"
                files[key].write_text(json.dumps(doc), encoding="utf-8")
            files["qa_runtime"] = qa
            files["qa_visual"] = qa
            files["wav"] = wav
            return root, rom, files

        root, rom, files = make_case("ok", b"ROM-ONE")
        result = project(
            root, current_rom=str(rom), out_dir=str(root / "out/evidence"),
            **{k: str(v) for k, v in files.items()})
        ev = json.loads((root / "out/evidence/evidence.json").read_text())
        fps = json.loads((root / "out/evidence/fps.json").read_text())
        assert ev["rom_sha256"] == result["rom_sha256"]
        assert fps["rom_sha256"] == result["rom_sha256"]
        assert (root / "out/evidence" / (
            "audio_" + result["rom_sha256"][:8] + ".wav")).is_file()

        # Stale sources: current ROM is a different binary -> refuse, no writes.
        other_sha = hashlib.sha256(b"ROM-TWO").hexdigest()
        root2, rom2, files2 = make_case("stale", b"ROM-TWO",
                                        source_sha=hashlib.sha256(
                                            b"ROM-ONE").hexdigest())
        try:
            project(root2, current_rom=str(rom2),
                    out_dir=str(root2 / "out/evidence"),
                    **{k: str(v) for k, v in files2.items()})
        except ProjectionError as exc:
            assert "nao e a ROM das fontes" in str(exc), exc
        else:
            raise AssertionError("fonte de outra ROM deveria recusar")
        assert not (root2 / "out/evidence/evidence.json").exists()
        assert not (root2 / "out/evidence/fps.json").exists()
        assert other_sha  # keeps the fixture explicit

        # A stale boolean without the matching SHA cannot be projected.
        root3, rom3, files3 = make_case("no-sha", b"ROM-THREE",
                                        source_sha="")
        try:
            project(root3, current_rom=str(rom3),
                    out_dir=str(root3 / "out/evidence"),
                    **{k: str(v) for k, v in files3.items()})
        except ProjectionError as exc:
            assert "divergem" in str(exc) or "nao e a ROM" in str(exc), exc
        else:
            raise AssertionError("fontes sem SHA deveriam recusar")
        assert not (root3 / "out/evidence/evidence.json").exists()
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("[SELF-CHECK OK] axis_projection "
          "(mesma ROM passa; ROM antiga/sem SHA recusa sem escrever)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Projeta evidencia selada nos caminhos canonicos, "
                    "exigindo o SHA da ROM atual.")
    ap.add_argument("--project", default=".")
    ap.add_argument("--current-rom")
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
