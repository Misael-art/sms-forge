"""OpenBOR -> SMS intake (O0): deterministic source verification and dependency porting.

Subcommands (every input path is explicit; no implicit donor or MUGEN paths):
  pak      hash + parse a PAK container; emit an intake record
  sources  hash files/directories and an optional .py tree hash; emit a manifest
  deps     port the donor dependency matrix/contract into a local, hash-bound record

Fail closed: identity expectations that do not match abort with exit 1.
Never writes an existing output path unless --force is given.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from .pak import (
        SPEC_COMMIT,
        SPEC_SOURCE,
        PakError,
        build_pak32,
        build_pak64,
        read_index,
        sha256_file,
    )
except ImportError:  # direct script use (python3 openbor2sms/intake.py)
    from pak import (
        SPEC_COMMIT,
        SPEC_SOURCE,
        PakError,
        build_pak32,
        build_pak64,
        read_index,
        sha256_file,
    )

SCHEMA_PAK = "openbor_sms_intake_v1"
SCHEMA_SOURCES = "openbor_sms_source_manifest_v1"
SCHEMA_DEPS = "openbor_sms_dependency_inventory_v1"

TREE_ALGORITHM = (
    "SHA256 over sorted relative path UTF-8, NUL, raw SHA256 digest of file bytes, "
    "newline for each .py file; excludes __pycache__ and .pytest_cache"
)
SKIP_DIRS = {"__pycache__", ".pytest_cache"}


class IntakeError(ValueError):
    """An intake input failed a declared identity/precondition check."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict, force: bool) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        if not force:
            raise IntakeError(f"output already exists (use --force to replace): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def _entry_digest(index) -> str:
    """Deterministic digest over sorted entry tuples (name, offset, size, unsafe)."""
    lines = []
    for entry in index.entries:
        line = "{}\x00{}\x00{}\x00{}\x00{}".format(
            entry.normalized_name,
            entry.original_name,
            entry.data_offset,
            entry.data_size,
            int(entry.unsafe),
        )
        lines.append(line)
    lines.sort()
    digest = hashlib.sha256()
    for line in lines:
        digest.update(line.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def _histogram(values) -> dict:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def pak_record(
    path,
    expect_sha256: str | None = None,
    expect_bytes: int | None = None,
    generated_at: str | None = None,
) -> dict:
    path = Path(path)
    if not path.is_file():
        raise IntakeError(f"PAK not readable: {path}")
    size = path.stat().st_size
    digest = sha256_file(path)
    problems = []
    if expect_sha256 is not None and digest != expect_sha256.lower():
        problems.append(f"sha256 expected {expect_sha256.lower()} got {digest}")
    if expect_bytes is not None and size != expect_bytes:
        problems.append(f"bytes expected {expect_bytes} got {size}")
    if problems:
        raise IntakeError("source identity mismatch: " + "; ".join(problems))
    verified = expect_sha256 is not None or expect_bytes is not None
    try:
        index = read_index(path.read_bytes())
    except PakError as error:
        raise IntakeError(f"{path}: {error}") from error

    safe = [entry for entry in index.entries if not entry.unsafe and entry.normalized_name]
    extensions = []
    top_level = []
    for entry in safe:
        name = entry.normalized_name
        tail = name.rsplit("/", 1)[-1]
        extensions.append(("." + tail.rsplit(".", 1)[-1].lower()) if "." in tail else "(none)")
        top_level.append(name.split("/", 1)[0] if "/" in name else "(root)")
    return {
        "schema": SCHEMA_PAK,
        "generated_at": generated_at or utc_now(),
        "tool": "openbor2sms intake pak",
        "source": {"path": str(path), "bytes": size, "sha256": digest},
        "expected": {
            "sha256": expect_sha256.lower() if expect_sha256 else None,
            "bytes": expect_bytes,
            "verified": verified,
        },
        "container": {
            "format_id": index.format_id,
            "format_name": index.format_name,
            "archive_size": index.archive_size,
            "table_offset": index.table_offset,
            "file_count": index.file_count,
            "unsafe_entry_count": sum(1 for entry in index.entries if entry.unsafe),
            "case_collision_count": len(index.case_collisions),
            "total_data_bytes": sum(entry.data_size for entry in index.entries),
            "index_digest_sha256": _entry_digest(index),
        },
        "histograms": {
            "scope": "safe entries only (unsafe/empty normalized names excluded)",
            "by_extension": _histogram(extensions),
            "by_top_level": _histogram(top_level),
        },
        "spec": {"commit": SPEC_COMMIT, "source": SPEC_SOURCE},
        "claim_ceiling": "container identity/index only; no conversion, runtime or resource acceptance",
    }


def _walk_files(root: Path):
    for current, dirs, files in sorted_os_walk(root):
        for name in files:
            yield Path(current) / name


def sorted_os_walk(root: Path):
    import os

    walked = []
    for current, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        walked.append((current, dirs, sorted(files)))
    for entry in sorted(walked, key=lambda item: item[0]):
        yield entry


def tree_hash(root, suffix: str = ".py") -> dict:
    root = Path(root)
    if not root.is_dir():
        raise IntakeError(f"tree root not readable: {root}")
    files = sorted(
        (p for p in root.rglob("*" + suffix) if p.is_file() and not any(part in SKIP_DIRS for part in p.parts)),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    digest = hashlib.sha256()
    for path in files:
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
        digest.update(b"\n")
    return {
        "algorithm": TREE_ALGORITHM,
        "root": str(root),
        "suffix": suffix,
        "file_count": len(files),
        "value": digest.hexdigest(),
    }


def sources_record(files, dirs, trees, suffix: str = ".py", generated_at: str | None = None) -> dict:
    entries: dict[str, dict] = {}
    for raw in files or []:
        path = Path(raw)
        if not path.is_file():
            raise IntakeError(f"file not readable: {path}")
        resolved = str(path.resolve())
        entries[resolved] = {
            "path": str(path),
            "origin": "explicit_file",
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    for raw in dirs or []:
        root = Path(raw)
        if not root.is_dir():
            raise IntakeError(f"directory not readable: {root}")
        for path in _walk_files(root):
            resolved = str(path.resolve())
            entries.setdefault(
                resolved,
                {
                    "path": str(path),
                    "origin": "dir_scan",
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                },
            )
    ordered = [entries[key] for key in sorted(entries)]
    tree_hashes = [tree_hash(root, suffix) for root in (trees or [])]
    return {
        "schema": SCHEMA_SOURCES,
        "generated_at": generated_at or utc_now(),
        "tool": "openbor2sms intake sources",
        "entries": ordered,
        "tree_hash": tree_hashes[0] if len(tree_hashes) == 1 else (tree_hashes or None),
        "claim_ceiling": "source identity only; hashes do not prove conversion or runtime",
    }


def deps_record(contract_path, matrix_path, manifest_path, generated_at: str | None = None) -> dict:
    def load(path, label):
        path = Path(path)
        if not path.is_file():
            raise IntakeError(f"{label} not readable: {path}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise IntakeError(f"{label} unreadable: {error}") from error
        return path, sha256_file(path), payload

    c_path, c_sha, contract = load(contract_path, "contract")
    m_path, m_sha, matrix = load(matrix_path, "matrix")
    s_path, s_sha, manifest = load(manifest_path, "source manifest")

    c_caps = {c.get("id"): c.get("status") for c in contract.get("capabilities", [])}
    m_caps = {c.get("id"): c.get("status") for c in matrix.get("importer_and_contract", {}).get("capabilities", [])}
    if not c_caps:
        raise IntakeError("contract has no capabilities to port")
    shared = set(c_caps) & set(m_caps)
    if any(c_caps[key] != m_caps[key] for key in shared):
        raise IntakeError("contract/matrix capability statuses disagree; port would be ambiguous")
    matrix_only = sorted(set(m_caps) - set(c_caps))
    contract_only = sorted(set(c_caps) - set(m_caps))
    if contract_only:
        raise IntakeError("matrix is missing contract capabilities (dependency closure incomplete): " + ", ".join(contract_only))

    evidence = {}
    for stage in matrix.get("source_to_runtime_pipeline", []):
        if stage.get("stage") == "local PAK containers":
            evidence = stage.get("evidence", {})
            break

    pilots = []
    for archive in manifest.get("archives", []):
        pak_path = archive.get("local_pak", "")
        match = None
        for candidate in evidence.values():
            if isinstance(candidate, dict) and candidate.get("path") == pak_path:
                match = candidate
                break
        pilots.append(
            {
                "id": archive.get("module"),
                "role": archive.get("role"),
                "pak": {
                    "path": pak_path,
                    "sha256": archive.get("local_pak_sha256"),
                    "bytes": archive.get("local_pak_bytes"),
                },
                "pak_format": (match or {}).get("format"),
                "observed_index_entries": (match or {}).get("observed_index_entries"),
                "discovery_zip": archive.get("discovery_zip"),
                "discovery_zip_sha256": archive.get("discovery_zip_sha256"),
                "zip_member": archive.get("zip_member"),
                "note": archive.get("note"),
            }
        )

    directive_stage = {}
    for stage in matrix.get("source_to_runtime_pipeline", []):
        if stage.get("stage") == "profile asset/resource conversion":
            directive_stage = stage.get("evidence", {})
            break

    importer = matrix.get("importer_and_contract", {})
    return {
        "schema": SCHEMA_DEPS,
        "generated_at": generated_at or utc_now(),
        "tool": "openbor2sms intake deps",
        "origin": {
            "contract": {"path": str(c_path), "sha256": c_sha},
            "matrix": {"path": str(m_path), "sha256": m_sha},
            "source_manifest": {"path": str(s_path), "sha256": s_sha},
        },
        "contract": {
            "schema_version": contract.get("schema_version"),
            "contract_status": contract.get("contract_status"),
            "reference": contract.get("reference"),
            "module_acceptance_rule": contract.get("module_acceptance_rule"),
            "status_vocabulary": contract.get("status_vocabulary"),
        },
        "pilots": pilots,
        "profiles": importer.get("declared_profile_ids", []),
        "capabilities": [
            {
                "id": cap.get("id"),
                "domain": cap.get("domain"),
                "status": cap.get("status"),
                "fidelity": cap.get("fidelity"),
                "claim_limit": cap.get("claim_limit"),
            }
            for cap in contract.get("capabilities", [])
        ],
        "matrix_only_capabilities": [
            {
                "id": cap.get("id"),
                "domain": cap.get("domain"),
                "status": cap.get("status"),
                "fidelity": cap.get("fidelity"),
                "claim_limit": cap.get("claim_limit"),
            }
            for cap in matrix.get("importer_and_contract", {}).get("capabilities", [])
            if cap.get("id") in matrix_only
        ],
        "directive_summary": {
            "gal_directives": directive_stage.get("gal_level_directives"),
            "status_counts": directive_stage.get("gal_directive_status_counts"),
            "origin_note": "ported summary; gal_town1_directive_matrix itself is ported in O1 with the neutral IR",
        },
        "file_dependencies": matrix.get("source_file_matrix", []),
        "donor_file_matrix": [
            {"path": row.get("path"), "role": row.get("role"), "status": row.get("status"), "sha256": row.get("sha256")}
            for row in importer.get("file_matrix", [])
        ],
        "blockers": matrix.get("unresolved_blockers", []),
        "reusable_measurements": matrix.get("measurements_to_reuse_not_repeat", []),
        "claim_ceiling": "ported donor records with hash origin only; not SMS evidence, not module acceptance",
    }


def _assert_equal(left, right, label):
    if left != right:
        raise AssertionError(f"{label}: {left!r} != {right!r}")


def self_check() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="openbor2sms-intake-") as tmp:
        tmp = Path(tmp)
        stamp = "2026-01-01T00:00:00+00:00"

        # --- pak mode ---
        blob = build_pak32([("data/chars/Hero/idle.txt", b"name Hero\n"), ("DATA/Levels/TOWN1.txt", b"seta 1\n")])
        pak = tmp / "fixture.pak"
        pak.write_bytes(blob)
        digest = sha256_file(pak)
        first = pak_record(pak, digest, len(blob), stamp)
        second = pak_record(pak, digest, len(blob), stamp)
        _assert_equal(first, second, "pak record determinism")
        _assert_equal(first["container"]["file_count"], 2, "entry count")
        _assert_equal(first["container"]["unsafe_entry_count"], 0, "unsafe count")
        _assert_equal(first["histograms"]["by_extension"][".txt"], 2, "extension histogram")
        _assert_equal(first["histograms"]["by_top_level"]["data"], 2, "top-level histogram")
        for bad in (
            lambda: pak_record(pak, "0" * 64, len(blob)),
            lambda: pak_record(pak, digest, len(blob) + 1),
        ):
            try:
                bad()
            except IntakeError:
                pass
            else:
                raise AssertionError("expected identity mismatch was not rejected")
        try:
            pak_record(tmp / "missing.pak")
        except IntakeError:
            pass
        else:
            raise AssertionError("missing PAK was not rejected")
        pak64 = tmp / "fixture64.pak"
        pak64.write_bytes(build_pak64([("sound/hit.wav", b"RIFF")]))
        _assert_equal(pak_record(pak64, generated_at=stamp)["container"]["format_id"], 1, "PAK64 format")

        # --- sources mode ---
        root = tmp / "tree"
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "a.py").write_text("A = 1\n")
        (root / "pkg" / "b.py").write_text("B = 2\n")
        (root / "pkg" / "__pycache__").mkdir()
        (root / "pkg" / "__pycache__" / "stale.py").write_text("ignored\n")
        extra = tmp / "doc.txt"
        extra.write_text("donor doc\n")
        manifest = sources_record([extra], [root], [root], generated_at=stamp)
        _assert_equal(len(manifest["entries"]), 3, "manifest entries (2 py + 1 doc)")
        _assert_equal(manifest["tree_hash"]["file_count"], 2, "tree hash excludes pycache")
        digest_a = manifest["tree_hash"]["value"]
        (root / "pkg" / "b.py").write_text("B = 3\n")
        _assert_equal(sources_record([extra], [root], [root], stamp)["tree_hash"]["value"] != digest_a, True, "tree hash tracks edits")
        try:
            sources_record([tmp / "missing.bin"], [], [])
        except IntakeError:
            pass
        else:
            raise AssertionError("missing file was not rejected")

        # --- deps mode ---
        caps = [{"id": "a", "domain": "import", "status": "partial", "fidelity": "partial", "claim_limit": "x"}]
        matrix_caps = caps + [{"id": "a2", "domain": "import", "status": "partial", "fidelity": "partial", "claim_limit": "y"}]
        contract = {
            "schema_version": "fixture/0",
            "contract_status": "draft",
            "reference": {"commit": "0" * 40},
            "module_acceptance_rule": "fixture rule",
            "status_vocabulary": ["partial"],
            "capabilities": caps,
        }
        matrix = {
            "importer_and_contract": {
                "declared_profile_ids": ["p1"],
                "capabilities": matrix_caps,
                "file_matrix": [{"path": "x.py", "role": "reader", "status": "supported", "sha256": "1" * 64}],
            },
            "source_file_matrix": [{"member": "M", "status": "adapted"}],
            "source_to_runtime_pipeline": [
                {"stage": "local PAK containers", "evidence": {"p": {"path": "a.pak", "format": "PACK v0 PAK32"}}},
                {"stage": "profile asset/resource conversion", "evidence": {"gal_level_directives": 26,
                                                                            "gal_directive_status_counts": {"adapted": 8, "rejected": 18}}},
            ],
            "unresolved_blockers": [{"id": "b", "status": "unknown", "detail": "d"}],
            "measurements_to_reuse_not_repeat": [{"topic": "t", "result": "r"}],
        }
        manifest_doc = {"archives": [{"module": "m", "role": "pilot", "local_pak": "a.pak",
                                      "local_pak_sha256": "2" * 64, "local_pak_bytes": 10}]}
        c_file = tmp / "contract.json"
        m_file = tmp / "matrix.json"
        s_file = tmp / "manifest.json"
        c_file.write_text(json.dumps(contract))
        m_file.write_text(json.dumps(matrix))
        s_file.write_text(json.dumps(manifest_doc))
        ported = deps_record(c_file, m_file, s_file, stamp)
        _assert_equal(ported["pilots"][0]["pak_format"], "PACK v0 PAK32", "pilot format ported")
        _assert_equal(ported["profiles"], ["p1"], "profiles ported")
        _assert_equal(ported["matrix_only_capabilities"][0]["id"], "a2", "matrix-only capability ported")
        _assert_equal(ported["directive_summary"]["status_counts"]["adapted"], 8, "directive summary")
        _assert_equal(ported["origin"]["matrix"]["sha256"], sha256_file(m_file), "matrix origin hash")
        matrix["importer_and_contract"]["capabilities"] = [dict(caps[0], status="unknown")]
        m_file.write_text(json.dumps(matrix))
        try:
            deps_record(c_file, m_file, s_file)
        except IntakeError:
            pass
        else:
            raise AssertionError("capability status disagreement was not rejected")
        matrix["importer_and_contract"]["capabilities"] = []
        m_file.write_text(json.dumps(matrix))
        try:
            deps_record(c_file, m_file, s_file)
        except IntakeError:
            pass
        else:
            raise AssertionError("contract-only capability (missing matrix row) was not rejected")

    print("[SELF-CHECK OK] openbor2sms intake (pak identity/determinism, sources manifest/tree hash, deps port)")
    return 0


def _summarize(record: dict) -> str:
    if record["schema"] == SCHEMA_PAK:
        container = record["container"]
        return (
            f"{record['source']['path']}: sha256={record['source']['sha256'][:16]}... "
            f"bytes={record['source']['bytes']} entries={container['file_count']} "
            f"format={container['format_name']} verified={record['expected']['verified']}"
        )
    if record["schema"] == SCHEMA_SOURCES:
        tree = record["tree_hash"]
        tree_note = f"tree_hash={tree['value'][:16]}... ({tree['file_count']} files)" if tree else "tree_hash=none"
        return f"entries={len(record['entries'])} {tree_note}"
    return f"pilots={[p['id'] for p in record['pilots']]} profiles={len(record['profiles'])} capabilities={len(record['capabilities'])}+{len(record.get('matrix_only_capabilities', []))}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openbor2sms", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", nargs="?", choices=["pak", "sources", "deps"])
    parser.add_argument("--path")
    parser.add_argument("--expect-sha256")
    parser.add_argument("--expect-bytes", type=int)
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--dir", action="append", default=[])
    parser.add_argument("--tree", action="append", default=[])
    parser.add_argument("--suffix", default=".py")
    parser.add_argument("--contract")
    parser.add_argument("--matrix")
    parser.add_argument("--source-manifest")
    parser.add_argument("--out")
    parser.add_argument("--generated-at")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)

    if args.self_check:
        return self_check()
    if not args.mode:
        parser.error("mode required unless --self-check")
    try:
        if args.mode == "pak":
            if not args.path or not args.out:
                parser.error("pak needs --path and --out")
            record = pak_record(args.path, args.expect_sha256, args.expect_bytes, args.generated_at)
        elif args.mode == "sources":
            if not args.out:
                parser.error("sources needs --out")
            record = sources_record(args.file, args.dir, args.tree, args.suffix, args.generated_at)
        else:
            if not (args.contract and args.matrix and args.source_manifest and args.out):
                parser.error("deps needs --contract, --matrix, --source-manifest and --out")
            record = deps_record(args.contract, args.matrix, args.source_manifest, args.generated_at)
        _write_json(Path(args.out), record, args.force)
    except (IntakeError, PakError, OSError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print(f"[OK] {_summarize(record)}")
    print(f"     out: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
