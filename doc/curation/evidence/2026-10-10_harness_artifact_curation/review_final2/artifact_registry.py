#!/usr/bin/env python3
"""Locate, audit and inventory production artifacts; never move or approve them.

The registry is an index of existing paths and reserved outputs, not a second
asset tree. Approval records are checked for consistency, not authenticated.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

SCHEMA = "sms_artifact_registry_v1"
STATES = {"reserved", "candidate", "approved", "rejected", "superseded", "historical"}
SHA = re.compile(r"[0-9a-f]{64}")


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def relative(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("path must be a project-relative POSIX path")
    p = PurePosixPath(value)
    if p.is_absolute() or ".." in p.parts or str(p) != value or value == ".":
        raise ValueError(f"noncanonical path: {value}")
    return p


def inside(root, value):
    rel = relative(value)
    if rel.parts[:2] == ("SMS_projects", Path(root).name):
        raise ValueError("workspace prefix repeated inside project-relative path")
    p = Path(root).resolve() / str(rel)
    if not p.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError(f"path escapes project through symlink: {value}")
    return p


def resolve_registry(project, explicit=None):
    """One authority: local for new games, central adoption for existing games."""
    project = Path(project).resolve()
    workspace = Path(__file__).resolve().parents[2]
    local = project / "doc/artifact_registry.json"
    catalog = workspace / "doc/artifact_registry_catalog.json"
    central = None
    if catalog.exists():
        data = json.loads(catalog.read_text())
        if data.get("schema") != "sms_artifact_registry_catalog_v1":
            raise ValueError("invalid canonical registry catalog")
        entry = data.get("projects", {}).get(project.name)
        if entry:
            if inside(workspace, entry["project"]).resolve() != project:
                raise ValueError("catalog project ID/path mismatch")
            central = inside(workspace, entry["registry"])
    if central and local.exists() and central.resolve() != local.resolve():
        raise ValueError("two registry authorities; reconcile catalog before production")
    selected = central or (local if local.exists() else None)
    if explicit:
        requested = Path(explicit).resolve()
        if selected and requested != selected.resolve():
            raise ValueError("explicit registry conflicts with canonical authority")
        return requested
    return selected or local


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    return value


def file_ref(root, ref):
    if not isinstance(ref, dict) or not SHA.fullmatch(str(ref.get("sha256", ""))):
        raise ValueError("file ref needs lowercase SHA-256")
    p = inside(root, ref.get("path"))
    if not p.is_file() or digest(p) != ref["sha256"]:
        raise ValueError(f"missing/stale file: {ref.get('path')}")
    return p


def group(row):
    return tuple(row.get(k) for k in ("asset_id", "kind", "variant"))


def audit(project, data, scan=False):
    """Return bounded structural findings. Does not infer approval from filenames."""
    problems, warnings = [], []
    records, paths, groups = {}, {}, {}
    project = Path(project).resolve()
    try:
        if not isinstance(data, dict) or data.get("schema") != SCHEMA:
            raise ValueError("registry schema must be sms_artifact_registry_v1")
        if data.get("project_id") != project.name:
            raise ValueError("project_id does not match project directory")
        locations = data.get("locations")
        kinds = data.get("kinds")
        if not isinstance(locations, dict) or not locations or not isinstance(kinds, dict) or not kinds:
            raise ValueError("locations and kinds must be nonempty objects")
        roots = []
        for lid, loc in locations.items():
            nonempty(lid, "location ID")
            nonempty(loc.get("purpose"), "location purpose")
            p = inside(project, loc.get("path"))
            if loc.get("mode") not in {"managed", "legacy"}:
                raise ValueError("location mode must be managed or legacy")
            if any(p == q or p in q.parents or q in p.parents for q in roots):
                raise ValueError("overlapping locations create competing destinations")
            roots.append(p)
        for kid, kind in kinds.items():
            nonempty(kid, "kind ID")
            for key in ("purpose", "introduced_for", "procedure"):
                nonempty(kind.get(key), f"{kid}.{key}")
            if kind.get("location") not in locations:
                raise ValueError(f"{kid}: unknown location")
            roles = kind.get("required_file_roles")
            if not isinstance(roles, list) or not roles or len(set(roles)) != len(roles):
                raise ValueError(f"{kid}: unique required_file_roles needed")
            for role in roles:
                nonempty(role, "file role")
        artifacts = data.get("artifacts")
        heads = data.get("heads")
        if not isinstance(artifacts, list) or not isinstance(heads, list):
            raise ValueError("artifacts and heads must be arrays")
        fingerprints, revisions = set(), set()
        for row in artifacts:
            if not isinstance(row, dict):
                raise ValueError("artifact must be object")
            rid = nonempty(row.get("id"), "artifact ID")
            if rid in records:
                raise ValueError(f"duplicate artifact ID: {rid}")
            for key in ("asset_id", "variant", "reason"):
                nonempty(row.get(key), f"{rid}.{key}")
            if row.get("kind") not in kinds or row.get("status") not in STATES:
                raise ValueError(f"{rid}: unknown kind/status")
            revision = row.get("revision")
            if type(revision) is not int or revision < 1:
                raise ValueError(f"{rid}: positive integer revision needed")
            g = group(row)
            if (*g, revision) in revisions:
                raise ValueError(f"{rid}: duplicate logical revision")
            revisions.add((*g, revision))
            records[rid] = row
            groups.setdefault(g, []).append(rid)
            parents = row.get("parents")
            if not isinstance(parents, list) or len(set(parents)) != len(parents):
                raise ValueError(f"{rid}: parents must be unique IDs")
            files = row.get("files")
            if not isinstance(files, list) or not files:
                raise ValueError(f"{rid}: files needed, even for reserved outputs")
            roles = set()
            location = inside(project, locations[kinds[row["kind"]]["location"]]["path"])
            fp = []
            for ref in files:
                role = nonempty(ref.get("role"), "file role")
                if role in roles:
                    raise ValueError(f"{rid}: duplicate file role")
                roles.add(role)
                p = inside(project, ref.get("path"))
                if not p.is_relative_to(location) or p == location:
                    raise ValueError(f"{rid}: file outside its kind's destination")
                if p.resolve() in paths:
                    raise ValueError(f"{rid}: file already owned by {paths[p.resolve()]}; use parent ID")
                paths[p.resolve()] = rid
                if row["status"] == "reserved":
                    if p.exists() or p.is_symlink() or ref.get("sha256") is not None:
                        raise ValueError(f"{rid}: reserved output already exists or has a digest; seal it")
                else:
                    file_ref(project, ref)
                    fp.append((role, ref["sha256"]))
            if not set(kinds[row["kind"]]["required_file_roles"]).issubset(roles):
                raise ValueError(f"{rid}: required file roles missing")
            if fp:
                fingerprint = (*g, tuple(sorted(fp)))
                if fingerprint in fingerprints:
                    raise ValueError(f"{rid}: unchanged duplicate revision; reuse artifact")
                fingerprints.add(fingerprint)
            if row["status"] in {"approved", "rejected"}:
                decision = json.loads(file_ref(project, row.get("decision")).read_text())
                expected = sorted((f["path"], f["sha256"]) for f in files)
                actual = sorted((f.get("path"), f.get("sha256")) for f in decision.get("files", []))
                if (decision.get("schema") != "sms_artifact_decision_v1" or
                    decision.get("artifact_id") != rid or decision.get("scope") != row["kind"] or
                    decision.get("decision") != row["status"] or decision.get("actor_role") != "owner" or
                    not decision.get("actor") or not decision.get("source_note") or actual != expected):
                    raise ValueError(f"{rid}: decision is not owner/hash/role-bound")
        for rid, row in records.items():
            for parent in row["parents"]:
                if parent not in records or records[parent]["status"] == "reserved":
                    raise ValueError(f"{rid}: missing/unsealed parent {parent}")
        visiting, visited = set(), set()
        def walk(rid):
            if rid in visiting:
                raise ValueError("lineage cycle")
            if rid in visited:
                return
            visiting.add(rid)
            for parent in records[rid]["parents"]:
                walk(parent)
            visiting.remove(rid)
            visited.add(rid)
        for rid in records:
            walk(rid)
        seen = set()
        for head in heads:
            g = group(head)
            if g not in groups or g in seen:
                raise ValueError("head group missing or duplicated")
            seen.add(g)
            for key, allowed in (("candidate", {"reserved", "candidate", "approved"}), ("approved", {"approved"})):
                rid = head.get(key)
                if rid is not None and (rid not in records or group(records[rid]) != g or records[rid]["status"] not in allowed):
                    raise ValueError(f"invalid {key} head: {rid}")
            active = {rid for rid in groups[g] if records[rid]["status"] in {"reserved", "candidate", "approved"}}
            if active != {v for v in (head.get("candidate"), head.get("approved")) if v is not None}:
                raise ValueError("active artifact outside unique heads; supersede explicitly")
        if seen != set(groups):
            raise ValueError("every logical group needs exactly one heads entry")
        legacy = data.get("legacy_inventory", [])
        for ref in legacy:
            p = file_ref(project, ref)
            if p.resolve() in paths:
                raise ValueError("legacy baseline duplicates artifact ownership")
            if not any(p.is_relative_to(q) for q in roots):
                raise ValueError("legacy file outside declared locations")
            paths[p.resolve()] = "legacy_unclassified"
        if scan:
            for lid, loc in locations.items():
                if loc["mode"] != "managed":
                    continue
                root = inside(project, loc["path"])
                if root.exists():
                    for p in sorted(root.rglob("*")):
                        if p.is_file() and p.resolve() not in paths:
                            problems.append(f"unregistered file in managed location {lid}: {p.relative_to(project)}")
        if legacy:
            warnings.append(f"{len(legacy)} historical files indexed without classification/approval")
        if any(loc["mode"] == "legacy" for loc in locations.values()):
            warnings.append("legacy locations are not exhaustively gated; use inventory before adoption")
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        problems.append(str(error))
    return {"schema": "sms_artifact_audit_v1", "ok": not problems, "problems": problems,
            "warnings": warnings, "artifact_count": len(records), "indexed_file_count": len(paths),
            "claim_ceiling": "organization_and_reference_consistency_only"}


def inventory(project, roots):
    project = Path(project).resolve()
    files, problems = [], []
    for root in roots:
        try:
            p = inside(project, root)
            if not p.is_dir():
                raise ValueError(f"inventory root missing: {root}")
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    inside(project, str(f.relative_to(project)))
                    files.append({"path": f.relative_to(project).as_posix(), "sha256": digest(f), "bytes": f.stat().st_size})
        except (OSError, ValueError) as error:
            problems.append(str(error))
    if len({f["path"] for f in files}) != len(files):
        problems.append("overlapping inventory roots")
    return {"schema": "sms_artifact_inventory_v1", "project_id": project.name,
            "roots": roots, "files": files, "problems": problems, "ok": not problems,
            "claim_ceiling": "discovery_only_no_approval"}


def fixture(project):
    project = Path(project)
    p = project / "data/source_art/hero/v01/source.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"fixture only, not a visual asset")
    row = {"id": "hero-concept-v01", "asset_id": "hero", "kind": "concept", "variant": "main", "revision": 1,
           "status": "candidate", "parents": [], "reason": "first concept", "files": [
               {"role": "image", "path": p.relative_to(project).as_posix(), "sha256": digest(p)}]}
    return {"schema": SCHEMA, "project_id": project.name,
            "locations": {"source": {"path": "data/source_art", "purpose": "source art", "mode": "managed"}},
            "kinds": {"concept": {"purpose": "identity", "introduced_for": "concept work", "procedure": "original-artwork.md",
                                  "location": "source", "required_file_roles": ["image"]}},
            "artifacts": [row], "heads": [{**{k: row[k] for k in ("asset_id", "kind", "variant")},
                                            "candidate": row["id"], "approved": None}]}


def self_check():
    with tempfile.TemporaryDirectory(prefix="sms-artifacts-") as tmp:
        project = Path(tmp) / "game"
        d = fixture(project)
        assert audit(project, d, True)["ok"]
        def bad(change):
            v = copy.deepcopy(d)
            change(v)
            assert not audit(project, v)["ok"], v
        bad(lambda v: v["artifacts"].append(copy.deepcopy(v["artifacts"][0])))
        bad(lambda v: v["heads"].append(copy.deepcopy(v["heads"][0])))
        bad(lambda v: v["artifacts"][0]["files"][0].update(sha256="0" * 64))
        bad(lambda v: v["artifacts"][0]["files"][0].update(path="../escape.png"))
        bad(lambda v: v["locations"]["source"].update(path="SMS_projects/game/data/source_art"))
        bad(lambda v: v["artifacts"][0].update(parents=[v["artifacts"][0]["id"]]))
        bad(lambda v: v["artifacts"][0].update(status="approved"))
        extended = copy.deepcopy(d)
        extended["kinds"]["weapon_detail"] = {**extended["kinds"]["concept"], "purpose": "weapon grip", "introduced_for": "new creative need"}
        assert audit(project, extended)["ok"]
        p = project / "data/source_art/untracked.png"
        p.write_bytes(b"experiment")
        assert not audit(project, d, True)["ok"]
        assert audit(project, d)["ok"]  # No false claim of a whole-tree scan.
        p.unlink()
        approved = copy.deepcopy(d)
        row = approved["artifacts"][0]
        decision = project / "doc/decision.json"
        decision.parent.mkdir()
        decision.write_text(json.dumps({"schema": "sms_artifact_decision_v1", "artifact_id": row["id"],
            "scope": "concept", "decision": "approved", "actor_role": "owner", "actor": "fixture owner",
            "source_note": "synthetic approval, not a real decision", "files": row["files"]}))
        row.update(status="approved", decision={"path": "doc/decision.json", "sha256": digest(decision)})
        approved["heads"][0]["approved"] = row["id"]
        assert audit(project, approved)["ok"]
        approved["artifacts"][0]["decision"]["sha256"] = "0" * 64
        assert not audit(project, approved)["ok"]
    print("[SELF-CHECK OK] artifact_registry (unique heads, hashes, ownership, lineage, extension, scan, decision binding)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", nargs="?", choices=["check", "locate", "inventory"])
    ap.add_argument("--project")
    ap.add_argument("--registry", help="explicit existing registry; may live in central doc/")
    ap.add_argument("--roots", nargs="+")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--asset")
    ap.add_argument("--kind")
    ap.add_argument("--variant", default="main")
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    if not args.project or not args.command:
        ap.error("--project and command required")
    source = None
    try:
        source = resolve_registry(args.project, args.registry) if args.command != "inventory" else None
        if args.command == "inventory":
            if not args.roots:
                ap.error("inventory needs explicit --roots")
            out = inventory(args.project, args.roots)
        else:
            data = json.loads(source.read_text())
            out = audit(args.project, data, args.scan)
            out["registry_sha256"] = digest(source)
            if args.command == "locate" and out["ok"]:
                g = (args.asset, args.kind, args.variant)
                head = next((h for h in data["heads"] if group(h) == g), None)
                out["head"] = head
                out["artifacts"] = [a for a in data["artifacts"] if group(a) == g]
                if head is None:
                    out["ok"] = False
                    out["problems"].append("logical artifact not registered; extend this registry before producing")
        if args.json:
            target = Path(args.json)
            protected = [source.resolve()] if source else []
            protected += [inside(args.project, f["path"]).resolve() for f in out.get("files", [])]
            if target.exists() or target.is_symlink() or target.resolve() in protected:
                raise ValueError("report output must be new and separate from inputs")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x") as stream:
                json.dump(out, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out["ok"] else 1
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({"ok": False, "problems": [str(error)]}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
