#!/usr/bin/env python3
"""Project real O3 evidence into the canonical axis files the build reads.

This is NOT a new measurement. It copies fields from the sealed consumer
bundle, the MRP3 runtime metrics and the QA reports into
`out/evidence/evidence.json` and `out/evidence/fps.json`, but only after
revalidating the consumer bundle and both hash-bound QA requests/reports
against the SAME ROM SHA as `--current-rom`. Existing outputs are refused.

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
import os
import sys
import tempfile
from pathlib import Path

# Also support python -m openbor2sms.axis_projection with only the package on PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from audit_subagent_session import check_ref, validate_report
from .evidence_consumer import consume

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


def _qa(path: Path, lane: str, root: Path, current_sha: str) -> dict:
    report = _load(path)
    try:
        request = _load(check_ref(report.get("request")))
        if request.get("lane") != lane or Path(request.get("project", "")).resolve() != root:
            raise ValueError("lane/projeto diferente")
        if request.get("rom", {}).get("sha256") != current_sha:
            raise ValueError("QA de outra ROM ou sem SHA")
        checked = validate_report(report, request)
        if not checked["ok"] or not checked["tests_passed"]:
            raise ValueError(str(checked["problems"]) + "; QA deve estar passed")
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise ProjectionError(f"QA {lane} recusada: {exc}") from exc
    return report


def _write_projection(destination: Path, payloads: dict[str, bytes]) -> None:
    # Refuse existing files, including broken symlinks and hardlink aliases.
    # Exclusive creates also close the race after preflight; roll back only files
    # created by this invocation on a partial write failure.
    destination.mkdir(parents=True, exist_ok=True)
    if any(os.path.lexists(destination / name) for name in payloads):
        raise ProjectionError("destino existente: escolha --out-dir novo; historico preservado")
    created = []
    try:
        for name, payload in payloads.items():
            target = destination / name
            with target.open("xb") as stream:
                created.append(target)
                stream.write(payload)
    except OSError as exc:
        for target in created:
            target.unlink()
        raise ProjectionError(f"escrita recusada: {exc}") from exc


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

    if cons.get("bundle_sha256") != sha256_file(paths["bundle"]):
        raise ProjectionError("consumption nao pertence ao bundle informado")
    fresh = consume(paths["bundle"], rom)
    if fresh.get("eligible") is not True or fresh.get("problems"):
        raise ProjectionError(f"bundle nao revalidado: {fresh.get('problems')}")
    if any(cons.get(key) != fresh.get(key) for key in ("axes", "coverage", "scope")):
        raise ProjectionError("consumption diverge da revalidacao do bundle")
    qa_r = _qa(paths["qa_runtime"], "runtime", root, current_sha)
    qa_v = _qa(paths["qa_visual"], "visual", root, current_sha)
    if (qa_r["worker_id"] == qa_v["worker_id"] or
            qa_r["session"]["id"] == qa_v["session"]["id"]):
        raise ProjectionError("QA runtime/visual requer workers e sessoes distintos")

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
    declared = ((audio_art or {}).get("file") or {}).get("sha256")
    if not declared or declared != wav_sha:
        raise ProjectionError("wav ausente/diverge do artefato selado do bundle")
    fps_art = next((a for a in bundle_doc.get("artifacts", [])
                    if a.get("id") == "fps_metrics"), {})
    if fps_art.get("file", {}).get("sha256") != sha256_file(paths["runtime_metrics"]):
        raise ProjectionError("runtime_metrics diverge do artefato selado do bundle")

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
            "qa_runtime_cases": [c["id"] for c in qa_r["coverage"] if c["status"] == "passed"],
        },
        "sources": sources,
        "claim_ceiling": "assigned_checks_only",
        "limits": [
            "projecao de evidencia aceita; nao e nova medicao",
            "consumer: assigned_checks_only; sem aprovacao de entrega ou qualidade visual",
            "PAL nao medido",
            "achados QA preservados nas fontes; passed nao aprova contato visual ou delivery",
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
    evidence_path = destination / "evidence.json"
    fps_path = destination / "fps.json"
    wav_path = destination / f"audio_{current_sha[:8]}.wav"
    _write_projection(destination, {
        evidence_path.name: (json.dumps(evidence, indent=1, ensure_ascii=False) + "\n").encode("utf-8"),
        fps_path.name: (json.dumps(fps_doc, indent=1, ensure_ascii=False) + "\n").encode("utf-8"),
        wav_path.name: paths["wav"].read_bytes(),
    })
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
    """Offline projection tests; mocked consumer/seal are never runtime evidence."""
    import copy
    from unittest.mock import patch
    from audit_subagent_session import fixture, ref
    module = sys.modules[__name__]
    with tempfile.TemporaryDirectory(prefix="smsproj_") as temp:
        base = Path(temp)

        def make_case(name):
            root = base / name
            root.mkdir()
            rom = root / "rom.sms"
            rom.write_bytes(b"fixture not runnable")
            digest = sha256_file(rom)
            wav = root / "audio.wav"
            wav.write_bytes(b"offline waveform fixture")
            files = {"wav": wav}
            for lane in ("runtime", "visual"):
                folder = root / lane
                req, report = fixture(folder)
                req.update(project=str(root), lane=lane, worker_id=lane)
                (folder / "request.json").write_text(json.dumps(req))
                report.update(project=str(root), lane=lane, worker_id=lane,
                              request=ref(folder / "request.json"))
                report["session"].update(owner=lane, id=lane)
                for file in (folder / "bundle/session.json", folder / "closed.json"):
                    meta = json.loads(file.read_text());meta["session_id"] = lane
                    file.write_text(json.dumps(meta))
                (folder / "commands.jsonl").write_text(json.dumps({"ack":{"ok":True,"session_id":lane}})+"\n")
                report["session"]["closed"] = ref(folder / "closed.json")
                report["artifacts"][0].update(ref(folder / "commands.jsonl"))
                files["qa_" + lane] = folder / "report.json"
                files["qa_" + lane].write_text(json.dumps(report))
            mrp = {"rom_sha256":digest,"session_id":"metrics", "region":"NTSC",
                   "fps_constante":True,"frame_advance_proved":True,
                   "fps_janelas":[59.6,59.7,59.8],"frames_delta_total":100}
            files["runtime_metrics"] = root / "metrics.json"
            files["runtime_metrics"].write_text(json.dumps(mrp))
            bundle = {"rom":{"sha256":digest,"bytes":rom.stat().st_size},
                      "artifacts":[{"id":"audio_signal","kind":"wav","file":ref(wav)},
                                   {"id":"fps_metrics","kind":"runtime_metrics","file":ref(files["runtime_metrics"])}]}
            cons = {"rom_sha256":digest,"eligible":True,"problems":[],"scope":{"claim_ceiling":"assigned_checks_only"},
                    "axes":dict.fromkeys(("boot_emulador","gameplay","fps_constante","audio"),True),
                    "coverage":{axis:{"proof":"fixture","artifacts":[],"derived":{}}
                                for axis in ("boot_emulador","gameplay","fps_constante","audio")}}
            files["bundle"] = root / "bundle.json"
            files["bundle"].write_text(json.dumps(bundle))
            cons["bundle_sha256"] = sha256_file(files["bundle"])
            files["consumption"] = root / "consumption.json"
            files["consumption"].write_text(json.dumps(cons))
            return root, rom, files, copy.deepcopy(cons)

        def run(case, output=None):
            root, rom, files, expected = case
            # Sealing and consumer correctness have their own fixtures. This
            # seam tests real QA contract validation and projection refusals.
            with patch.object(module, "consume", return_value=expected), patch(
                    "session_bridge.isolated.check_bundle", return_value=(True, "offline fixture")):
                return project(root, current_rom=str(rom), out_dir=str(output or root/"projected"),
                               **{key:str(value) for key,value in files.items()})

        good = make_case("positive")
        result = run(good)
        evidence = _load(Path(result["evidence"]))
        assert evidence["gameplay"]["qa_runtime_cases"] == ["boot"]
        assert evidence["rom_sha256"] == sha256_file(good[1])
        assert result["audio_sha256"] == sha256_file(good[2]["wav"])
        original = {p:p.read_bytes() for p in Path(result["evidence"]).parent.iterdir()}
        try:
            run(good)
        except ProjectionError:
            pass
        else:
            raise AssertionError("existing output overwritten")
        assert all(p.read_bytes()==raw for p,raw in original.items())

        mutations = {
            "empty_qa":lambda c: c[2]["qa_runtime"].write_text("{}"),
            "failed_qa":lambda c: edit(c[2]["qa_runtime"], lambda d:d.update(status="blocked")),
            "stale_request":lambda c: edit(c[2]["qa_visual"],lambda d:d["request"].update(sha256="0"*64)),
            "wrong_qa_rom":lambda c: edit(c[2]["qa_runtime"].parent/"request.json",lambda d:d["rom"].update(sha256="0"*64)),
            "wrong_lane":lambda c: c[2].update(qa_visual=c[2]["qa_runtime"]),
            "missing_coverage":lambda c:edit(c[2]["qa_runtime"],lambda d:d.update(coverage=[])),
            "defect_pass":lambda c:edit(c[2]["qa_visual"],lambda d:d.update(findings=[{"kind":"defect"}])),
            "stale_rom":lambda c:c[1].write_bytes(b"other ROM"),
            "missing_sha":lambda c:edit(c[2]["runtime_metrics"],lambda d:d.pop("rom_sha256")),
            "wrong_consumer_bundle":lambda c:edit(c[2]["consumption"],lambda d:d.update(bundle_sha256="0"*64)),
            "forged_coverage":lambda c:edit(c[2]["consumption"],lambda d:d.update(coverage={})),
            "changed_wav":lambda c:c[2]["wav"].write_bytes(b"changed"),
            "changed_metrics":lambda c:edit(c[2]["runtime_metrics"],lambda d:d.update(fps_janelas=[60,60,60])),
        }
        def edit(path, mutate):
            data=_load(path);mutate(data);path.write_text(json.dumps(data))
        for name, mutate in mutations.items():
            case=make_case(name);mutate(case)
            try:
                run(case)
            except ProjectionError:
                pass
            else:
                raise AssertionError(name+" was accepted")
            assert not (case[0]/"projected").exists(), name+" wrote output"
        for kind in ("symlink", "hardlink", "broken_symlink"):
            folder=good[0]/kind;folder.mkdir()
            target=folder/"fps.json";source=good[2]["wav"]
            if kind=="hardlink":target.hardlink_to(source)
            else:target.symlink_to(source if kind=="symlink" else folder/"absent")
            before=source.read_bytes()
            try:run(good,folder)
            except ProjectionError:pass
            else:raise AssertionError(kind+" output accepted")
            assert source.read_bytes()==before and not (folder/"evidence.json").exists()
    print("[SELF-CHECK OK] axis_projection: QA/ROM/bundle/media bindings, 13 negative cases and immutable outputs; offline seams only")
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
    except (ProjectionError, OSError, TypeError, KeyError, AttributeError) as exc:
        print(f"[REFUSE] {exc}")
        return 2
    print(f"[OK] rom {result['rom_sha256']}")
    print(f"evidence {result['evidence']} sha {result['evidence_sha256']}")
    print(f"fps      {result['fps']} sha {result['fps_sha256']}")
    print(f"audio    {result['audio']} sha {result['audio_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
