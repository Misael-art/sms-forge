#!/usr/bin/env python3
"""Restore the hash-bound 20261024 archive to a NEW directory, never over source.

Optional activation copies only the recorded generated build inputs into a
consumer with no out/generated yet. Evidence and axes are never activated.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

from host_bootstrap import ROOT, extract_selected, sha


def verify(root, rows):
    for row in rows:
        rel = Path(row["path"])
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("manifest traversal")
        path = root / rel
        if not path.is_file() or path.is_symlink() or path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise ValueError("handoff hash/size mismatch: " + str(rel))
    actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
    if actual != {row["path"] for row in rows}:
        raise ValueError("handoff file set differs from manifest")


def restore(manifest, destination, activate=False):
    doc = json.loads(manifest.read_text())
    if doc.get("schema") != "sms_host_handoff_archive_v1":
        raise ValueError("unsupported handoff schema")
    archive = ROOT / doc["archive"]["path"]
    if archive.stat().st_size != doc["archive"]["bytes"] or sha(archive) != doc["archive"]["sha256"]:
        raise ValueError("handoff archive hash/size mismatch")
    # Reject even a dangling link; do not resolve away an existing destination.
    destination = destination.absolute()
    if os.path.lexists(destination):
        raise ValueError("restore requires a new destination")
    generated = ROOT / "SMS_projects/luta_mugem_rev2/out/generated"
    if activate and os.path.lexists(generated):
        raise ValueError("out/generated already exists; preserve it and compare manually")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="handoff-", dir=destination.parent) as tmp:
        stage = Path(tmp) / "restored"
        stage.mkdir()
        extract_selected(archive, stage, tuple(doc["prefixes"]))
        verify(stage, doc["files"])
        # Handoff evidence is historical/read-only; no rewrite of embedded paths.
        for path in stage.rglob("*"):
            if path.is_file():
                path.chmod(0o444)
        stage.rename(destination)
    if activate:
        source = destination / "SMS_projects/luta_mugem_rev2/out/generated"
        generated.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="activate-", dir=generated.parent) as tmp:
            copied = Path(tmp) / "generated"
            shutil.copytree(source, copied)
            if os.path.lexists(generated):
                raise ValueError("concurrent generated output; activation refused")
            copied.rename(generated)
    return {"ok": True, "restored": str(destination), "files": len(doc["files"]),
            "build_inputs_activated": activate, "claim_ceiling": "historical_diagnostic_only",
            "limits": ["No evidence or axes activated; new host requires fresh sessions and QA.",
                       "Generated outputs are recorded inputs, not approval of pose budget or moves."]}


def self_check():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a").write_bytes(b"ok")
        row = {"path": "a", "bytes": 2, "sha256": sha(root / "a")}
        verify(root, [row])
        for bad in ({**row, "sha256": "0" * 64}, {**row, "path": "../outside"}):
            try:
                verify(root, [bad])
            except ValueError:
                pass
            else:
                raise AssertionError("bad handoff accepted")
        (root / "extra").write_bytes(b"extra")
        try:
            verify(root, [row])
        except ValueError:
            pass
        else:
            raise AssertionError("unlisted artifact accepted")
    print("[SELF-CHECK OK] handoff: exact file set, hashes and confined manifest paths; offline only")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=ROOT / "doc/continuity/20261024-mugen-resume.json")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--activate-build-inputs", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    if not args.out:
        ap.error("--out NEW_DIRECTORY required")
    try:
        result = restore(args.manifest, args.out, args.activate_build_inputs)
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
