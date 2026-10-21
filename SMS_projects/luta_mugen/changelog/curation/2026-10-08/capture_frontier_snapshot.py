#!/usr/bin/env python3
"""Index local MUGEN studies and preserve their source/report text snapshots.

ROMs, rendered media and ordinary build outputs stay in their existing local
locations, matching the SMSForge repository policy. Their paths, sizes and
SHA-256 digests are recorded so later curation can detect missing or changed
artifacts. Text sources, generated manifests, build records and QA reports are
copied into a compressed review archive.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import tempfile
import tarfile
from datetime import datetime, timezone


PROJECT = pathlib.Path(__file__).resolve().parents[3]
STUDIES = PROJECT / "out" / "local_study"
OUTPUT = pathlib.Path(__file__).resolve().parent
ARCHIVE = OUTPUT / "local_study_source_and_reports.tar.gz"
INVENTORY = OUTPUT / "frontier_inventory.json"

TEXT_SUFFIXES = {
    ".air", ".c", ".cfg", ".cmd", ".cns", ".csv", ".def", ".diff",
    ".h", ".hpp", ".inc", ".ini", ".json", ".log", ".md", ".patch",
    ".psg", ".py", ".s", ".sh", ".toml", ".tsv", ".txt", ".xml",
    ".yaml", ".yml",
}
OUTPUT_SUFFIXES = {
    ".asm", ".ihx", ".lst", ".map", ".noi", ".rel", ".sym",
}
MEDIA_SUFFIXES = {".gif", ".jpg", ".jpeg", ".mp3", ".mp4", ".png", ".wav"}
ROM_SUFFIXES = {".gg", ".sms"}
AUTHORITY_PATHS = (
    "doc/10-memory-bank.md",
    "doc/11-gdd.md",
    "doc/13-spec-cenas.md",
    "doc/15-tdd.md",
    "doc/plano-sessoes-emulicious-isoladas.md",
)


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify(path: pathlib.Path) -> str:
    suffix = path.suffix.lower()
    if suffix in ROM_SUFFIXES:
        return "rom"
    if suffix in MEDIA_SUFFIXES:
        return "media"
    if suffix in OUTPUT_SUFFIXES:
        return "compiler_output"
    if suffix == ".bin":
        return "binary_data_or_build_input"
    if suffix in TEXT_SUFFIXES or suffix in {"", ".jsonl"}:
        return "text_source_or_record"
    return "other"


def archive_candidate(path: pathlib.Path, rel: pathlib.Path, *, current: bool) -> bool:
    suffix = path.suffix.lower()
    if current and rel.parts[:1] in {
        ("base",), ("integrada",), ("rascunho",), ("res",)
    }:
        return True
    if suffix in TEXT_SUFFIXES or (not suffix and path.name in {"Makefile", "README"}):
        return True
    if suffix != ".bin":
        return False
    parts = rel.parts
    name = path.name
    if current and parts[:1] == ("inc",) and (
        name.startswith("ken_scene_bank") or name.startswith("versus_scene_banks")
    ):
        return True
    if "assets" in parts and "banks" in parts:
        return True
    if name == "versus_scene_banks_02.bin":
        return True
    if "generated" in parts and "versus_cut" in parts and name.startswith("ken_scene_bank"):
        return True
    return False


def file_record(path: pathlib.Path, rel: pathlib.Path, *, current: bool) -> dict:
    try:
        size = path.stat().st_size
        digest = sha256(path)
        return {
            "path": rel.as_posix(),
            "bytes": size,
            "sha256": digest,
            "class": classify(path),
            "archived": archive_candidate(path, rel, current=current),
        }
    except OSError as exc:
        return {
            "path": rel.as_posix(),
            "bytes": None,
            "sha256": None,
            "class": classify(path),
            "archived": False,
            "read_error": f"{type(exc).__name__}: {exc}",
        }


def curation_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Index curation artifacts without making a snapshot contain itself."""
    base = root / "changelog" / "curation"
    if not base.is_dir():
        return []
    excluded = {"frontier_inventory.json", "local_study_source_and_reports.tar.gz"}
    return sorted(
        path for path in base.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and path.name not in excluded
        and "__pycache__" not in path.parts
    )


def self_check() -> None:
    with tempfile.TemporaryDirectory(prefix="frontier_curation_selfcheck_") as temp:
        root = pathlib.Path(temp)
        base = root / "changelog" / "curation" / "2026-10-08"
        nested = base / "nested"
        cache = base / "__pycache__"
        nested.mkdir(parents=True)
        cache.mkdir()
        included = [base / "learning_ledger.json", nested / "report.md"]
        for path in included:
            path.write_text("fixture", encoding="utf-8")
        (base / "frontier_inventory.json").write_text("fixture", encoding="utf-8")
        (base / "local_study_source_and_reports.tar.gz").write_bytes(b"fixture")
        (cache / "generated.pyc").write_bytes(b"fixture")
        symlink = nested / "alias.md"
        try:
            symlink.symlink_to(included[1])
        except (OSError, NotImplementedError):
            pass
        actual = curation_files(root)
        if actual != sorted(included):
            raise AssertionError(f"unexpected curation file set: {actual}")
    print("frontier curation collector self-check: PASS")


def project_files() -> list[pathlib.Path]:
    paths: set[pathlib.Path] = set()
    for top in ("src", "inc", "data", "tools", ".agent", ".mddev"):
        base = PROJECT / top
        if base.exists():
            paths.update(p for p in base.rglob("*") if p.is_file() and not p.is_symlink())
    for rel in (
        ".gitignore",
        "README.md",
        "build.sh",
        "build.bat",
        "clean.sh",
        "clean.bat",
        "run.bat",
        ".mddev/project.json",
        "run.sh",
        "out/build_record.json",
        "out/rom/luta_mugen.sms",
        "changelog/roms/build_v088/rom.sms",
        "changelog/curation/2026-10-08/capture_frontier_snapshot.py",
        "changelog/curation/2026-10-08/frontier_summary.md",
        "changelog/curation/2026-10-08/learning_ledger.json",
        "changelog/curation/2026-10-08/candidate_repro_build_20261008.json",
        "changelog/curation/2026-10-08/route_reconciliation_20261008.json",
    ):
        path = PROJECT / rel
        if path.is_file() and not path.is_symlink():
            paths.add(path)
    paths.update(curation_files(PROJECT))
    for top in ("base", "integrada", "rascunho", "res"):
        base = PROJECT / top
        if base.is_dir():
            paths.update(p for p in base.rglob("*") if p.is_file() and not p.is_symlink())
    rom_history = PROJECT / "changelog" / "roms"
    if rom_history.is_dir():
        paths.update(p for p in rom_history.rglob("*") if p.is_file() and not p.is_symlink())
    out = PROJECT / "out"
    if out.is_dir():
        paths.update(
            p for p in out.rglob("*")
            if p.is_file() and not p.is_symlink()
            and "local_study" not in p.relative_to(out).parts
        )
    # Explicitly record key authority paths even when stat/open reports EIO or
    # the current worktree entry is missing; file_record keeps that failure.
    paths.update(PROJECT / rel for rel in AUTHORITY_PATHS)
    # Root-level QA and production evidence can live outside a study clone.
    # Preserve their text records in the archive and hash media without copying
    # the large captures themselves.
    for rel in ("out/evidence", "out/audits", "out/qa_native_20261006", "out/qa_native_20261007"):
        base = PROJECT / rel
        if base.is_dir():
            paths.update(p for p in base.rglob("*") if p.is_file() and not p.is_symlink())
    return sorted(paths)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-check", action="store_true",
        help="check curation-file collection in a temporary fixture without capturing",
    )
    args = parser.parse_args(argv)
    if args.self_check:
        self_check()
        return

    OUTPUT.mkdir(parents=True, exist_ok=True)
    if not STUDIES.is_dir():
        raise SystemExit(f"missing study directory: {STUDIES}")

    study_paths = sorted(p for p in STUDIES.rglob("*") if p.is_file() and not p.is_symlink())
    current_paths = project_files()
    records: dict[str, dict] = {}
    archive_inputs: list[tuple[pathlib.Path, str]] = []

    for index, path in enumerate(study_paths, 1):
        rel = path.relative_to(PROJECT)
        record = file_record(path, rel, current=False)
        records[rel.as_posix()] = record
        if record["archived"] and not record.get("read_error"):
            archive_inputs.append((path, rel.as_posix()))
        if index % 1000 == 0:
            print(f"hashed local-study files: {index}/{len(study_paths)}", flush=True)

    for path in current_paths:
        rel = path.relative_to(PROJECT)
        record = file_record(path, rel, current=True)
        records[rel.as_posix()] = record
        if record["archived"] and not record.get("read_error"):
            archive_inputs.append((path, f"current_worktree/{rel.as_posix()}"))

    with tarfile.open(ARCHIVE, mode="w:gz", compresslevel=6) as archive:
        for path, arcname in sorted(archive_inputs, key=lambda item: item[1]):
            archive.add(path, arcname=arcname, recursive=False)

    branch_records = []
    for branch in sorted(p for p in STUDIES.iterdir() if p.is_dir() and p.name != "__pycache__"):
        rel = branch.relative_to(PROJECT)
        record_path = branch / "out" / "build_record.json"
        build_record = None
        build_record_sha = None
        if record_path.is_file():
            try:
                build_record = json.loads(record_path.read_text(encoding="utf-8"))
                build_record_sha = records[record_path.relative_to(PROJECT).as_posix()]["sha256"]
            except (OSError, json.JSONDecodeError, KeyError):
                build_record = {"read_error": True}
        roms = [
            records[p.relative_to(PROJECT).as_posix()]
            for p in sorted(branch.rglob("*.sms"))
            if p.is_file() and p.relative_to(PROJECT).as_posix() in records
        ]
        evidence = [
            records[p.relative_to(PROJECT).as_posix()]
            for p in sorted((branch / "out" / "evidence").rglob("*"))
            if p.is_file() and p.relative_to(PROJECT).as_posix() in records
        ] if (branch / "out" / "evidence").is_dir() else []
        docs = [
            records[p.relative_to(PROJECT).as_posix()]
            for name in ("10-memory-bank.md", "11-gdd.md", "13-spec-cenas.md", "15-tdd.md")
            for p in branch.rglob(name)
            if p.is_file() and p.relative_to(PROJECT).as_posix() in records
        ]
        source_hash = hashlib.sha256()
        for path, item in sorted(records.items()):
            if not path.startswith(rel.as_posix() + "/") or item.get("sha256") is None:
                continue
            subpath = pathlib.PurePosixPath(path).relative_to(rel.as_posix())
            if subpath.parts[0] not in {"src", "inc", "data", "tools", ".mddev"}:
                continue
            source_hash.update(path.encode("utf-8"))
            source_hash.update(b"\0")
            source_hash.update(item["sha256"].encode("ascii"))
            source_hash.update(b"\n")
        branch_records.append({
            "name": branch.name,
            "path": rel.as_posix(),
            "source_tree_sha256": source_hash.hexdigest(),
            "build_record_path": record_path.relative_to(PROJECT).as_posix() if record_path.exists() else None,
            "build_record_sha256": build_record_sha,
            "build_record": build_record,
            "rom_count": len(roms),
            "roms": [{"path": x["path"], "bytes": x["bytes"], "sha256": x["sha256"]} for x in roms],
            "evidence_count": len(evidence),
            "evidence": [{"path": x["path"], "bytes": x["bytes"], "sha256": x["sha256"]} for x in evidence],
            "authority_snapshot_count": len(docs),
            "authority_snapshots": [{"path": x["path"], "bytes": x["bytes"], "sha256": x["sha256"]} for x in docs],
        })

    root_build = json.loads((PROJECT / "out/build_record.json").read_text(encoding="utf-8"))
    project_manifest_path = PROJECT / ".mddev/project.json"
    project_manifest = json.loads(project_manifest_path.read_text(encoding="utf-8"))
    root_rom = PROJECT / "out/rom/luta_mugen.sms"
    v088_rom = PROJECT / "changelog/roms/build_v088/rom.sms"
    ignored_paths = [
        "out/local_study/ (ignored by .gitignore)",
        "out/ (ignored by .gitignore)",
        "changelog/roms/ (ignored by .gitignore)",
    ]
    authority_paths = list(AUTHORITY_PATHS)
    inventory = {
        "schema": "luta_mugen_frontier_inventory_v1",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": str(PROJECT),
        "canonical_state": {
            "latest_changelog_build": "build_v088",
            "build_record": root_build,
            "build_record_rom_sha256_actual": sha256(root_rom) if root_rom.is_file() else None,
            "build_v088_rom_sha256_actual": sha256(v088_rom) if v088_rom.is_file() else None,
            "project_manifest_sha256": sha256(project_manifest_path),
            "project_manifest": project_manifest,
            "source_local_study_references": [
                "src/fight.c -> ../out/local_study/generated/versus_cut/versus_scene_runtime.h",
                "src/fight.c -> ../out/local_study/generated/versus_cut/fight_runtime_data.h",
                "src/main.c -> ../out/local_study/generated/versus_cut/fight_input_profile.h",
                ".mddev/project.json -> out/local_study/ryo_terry_cmdv4_20261008/versus_scene_banks_02.bin",
            ],
            "authority_context": {
                "status": "unreadable_eio_at_capture",
                "paths": authority_paths,
                "memory_bank_worktree_status": "git status reported deleted; no restoration attempted",
            },
            "ignored_output_roots": ignored_paths,
        },
        "inventory_summary": {
            "study_directories": len(branch_records),
            "study_directories_with_build_record": sum(1 for b in branch_records if b["build_record"] is not None),
            "study_directories_without_build_record": sum(1 for b in branch_records if b["build_record"] is None),
            "indexed_files": len(records),
            "archived_files": len(archive_inputs),
            "local_study_bytes": sum(x["bytes"] or 0 for p, x in records.items() if p.startswith("out/local_study/")),
            "local_study_read_errors": [p for p, x in records.items() if p.startswith("out/local_study/") and x.get("read_error")],
            "archive": {
                "path": ARCHIVE.relative_to(PROJECT).as_posix(),
                "bytes": ARCHIVE.stat().st_size,
                "sha256": sha256(ARCHIVE),
            },
        },
        "branches": branch_records,
        "files": list(records.values()),
    }
    INVENTORY.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inventory["inventory_summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
