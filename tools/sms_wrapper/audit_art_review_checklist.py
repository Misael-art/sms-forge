#!/usr/bin/env python3
"""Require complete, hash-bound human review axes for character art.

This gate validates that a reviewer inspected every declared art axis and that
the candidate cannot be promoted while any axis is failed/pending or owner
approval is absent. It does not infer artistic correctness from pixels.

Usage:
  audit_art_review_checklist.py --manifest <checklist.json> --project-root <dir>
  audit_art_review_checklist.py --manifest <checklist.json> --verify-hashes
  audit_art_review_checklist.py --self-check

Exit: 0 passed | 1 invalid/failed | 2 review pending | 3 usage error
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile


SCHEMA = "sms_art_review_checklist_v1"
STATUSES = ("pass", "fail", "pending", "not_applicable")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PIXEL_SPRITE_KINDS = {"pixel_sprite_sheet", "pixel_sprite_roster_board"}
PIXEL_SPRITE_REQUIRED_AXES = {
    "pixel_clusters",
    "face_detail_readability",
    "outline_and_cutout",
    "material_shading",
    "material_shadow_flow_coherence",
    "semantic_palette_role_confinement",
    "hand_weapon_attachment",
    "equipment_geometry",
    "frame_pose_integrity",
    "native_size_readability",
}
CONCEPT_SHEET_REQUIRED_AXES = {
    "document_and_layout",
    "artist_reference_and_scope",
    "distinctive_style_signature",
    "pose_anatomy_and_joint_continuity",
    "visual_cohesion_and_distinction",
}


def _is_sha(value):
    return isinstance(value, str) and bool(SHA256_RE.fullmatch(value))


def _file_sha(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_ref(reference, label, root, verify_hashes, problems):
    if not isinstance(reference, dict):
        problems.append(f"{label}: reference must be an object")
        return
    path = reference.get("path")
    expected = reference.get("sha256")
    if not isinstance(path, str) or not path.strip():
        problems.append(f"{label}: path missing")
    if not _is_sha(expected):
        problems.append(f"{label}: invalid/missing sha256")
    if verify_hashes and isinstance(path, str) and path.strip():
        full = path if os.path.isabs(path) else os.path.join(root, path)
        if not os.path.isfile(full):
            problems.append(f"{label}: file missing: {path}")
        elif _is_sha(expected) and _file_sha(full) != expected:
            problems.append(f"{label}: sha256 mismatch: {path}")


def audit(manifest, project_root=".", verify_hashes=False):
    problems, failures, pending = [], [], []
    if manifest.get("schema") != SCHEMA:
        problems.append(f"schema must be {SCHEMA}")

    asset = manifest.get("asset")
    _verify_ref(asset, "asset", project_root, verify_hashes, problems)
    if isinstance(asset, dict) and not asset.get("kind"):
        problems.append("asset: kind missing")

    evidence = manifest.get("source_evidence")
    _verify_ref(evidence, "source_evidence", project_root, verify_hashes, problems)

    required_characters = manifest.get("required_characters")
    required_axes = manifest.get("required_axes")
    if not isinstance(required_characters, list) or not required_characters:
        problems.append("required_characters must be a non-empty list")
        required_characters = []
    if len(set(required_characters)) != len(required_characters):
        problems.append("required_characters contains duplicates")
    if not isinstance(required_axes, list) or not required_axes:
        problems.append("required_axes must be a non-empty list")
        required_axes = []
    if len(set(required_axes)) != len(required_axes):
        problems.append("required_axes contains duplicates")
    asset_kind = asset.get("kind") if isinstance(asset, dict) else None
    if asset_kind in PIXEL_SPRITE_KINDS:
        missing_pixel_axes = sorted(PIXEL_SPRITE_REQUIRED_AXES - set(required_axes))
        if missing_pixel_axes:
            problems.append(
                "pixel sprite review requires explicit micro-axes: "
                + ", ".join(missing_pixel_axes))
    elif asset_kind == "character_concept_model_sheet":
        missing_concept_axes = sorted(CONCEPT_SHEET_REQUIRED_AXES - set(required_axes))
        if missing_concept_axes:
            problems.append(
                "concept model sheet review requires explicit axes: "
                + ", ".join(missing_concept_axes))
    elif isinstance(asset_kind, str) and asset_kind.startswith("pixel_sprite_"):
        problems.append(f"asset: unsupported pixel sprite kind {asset_kind!r}")

    characters = manifest.get("characters")
    if not isinstance(characters, list):
        problems.append("characters must be a list")
        characters = []
    by_id = {}
    for character in characters:
        if not isinstance(character, dict):
            problems.append("character row must be an object")
            continue
        char_id = character.get("id")
        if not isinstance(char_id, str) or not char_id:
            problems.append("character id missing")
            continue
        if char_id in by_id:
            problems.append(f"duplicate character id: {char_id}")
            continue
        by_id[char_id] = character

    missing = sorted(set(required_characters) - set(by_id))
    unexpected = sorted(set(by_id) - set(required_characters))
    if missing:
        problems.append(f"required characters missing: {', '.join(missing)}")
    if unexpected:
        problems.append(f"unexpected characters: {', '.join(unexpected)}")

    axis_counts = {status: 0 for status in STATUSES}
    for char_id in required_characters:
        character = by_id.get(char_id)
        if not character:
            continue
        refs = character.get("references")
        if not isinstance(refs, list) or not refs:
            problems.append(f"{char_id}: at least one source reference is required")
        else:
            for index, reference in enumerate(refs):
                _verify_ref(reference, f"{char_id}.references[{index}]",
                            project_root, verify_hashes, problems)

        observed = character.get("observed_defects")
        revisions = character.get("revision_notes")
        if not isinstance(observed, list):
            problems.append(f"{char_id}: observed_defects must be a list")
        if not isinstance(revisions, list):
            problems.append(f"{char_id}: revision_notes must be a list")

        axis_rows = character.get("review_axes")
        if not isinstance(axis_rows, dict):
            problems.append(f"{char_id}: review_axes must be an object")
            continue
        for axis in required_axes:
            row = axis_rows.get(axis)
            if not isinstance(row, dict):
                problems.append(f"{char_id}: review axis missing: {axis}")
                continue
            status = row.get("status")
            note = row.get("note")
            if status not in STATUSES:
                problems.append(f"{char_id}.{axis}: invalid status {status!r}")
                continue
            axis_counts[status] += 1
            if not isinstance(note, str) or not note.strip():
                problems.append(f"{char_id}.{axis}: reviewer note required")
            if status == "not_applicable" and asset_kind == "character_concept_model_sheet" and axis == "document_and_layout":
                problems.append(f"{char_id}.{axis}: concept sheet layout cannot be exempted")
            if status == "not_applicable" and not row.get("reason"):
                problems.append(f"{char_id}.{axis}: not_applicable requires reason")
            if status == "fail":
                failures.append(f"{char_id}.{axis}")
            elif status == "pending":
                pending.append(f"{char_id}.{axis}")
        extra_axes = sorted(set(axis_rows) - set(required_axes))
        if extra_axes:
            problems.append(f"{char_id}: undeclared review axes: {', '.join(extra_axes)}")

    owner = manifest.get("owner_approval")
    if not isinstance(owner, dict) or not isinstance(owner.get("approved"), bool):
        problems.append("owner_approval.approved must be explicitly true/false")
        owner = {"approved": False}
    elif owner.get("approved"):
        for field in ("reviewer", "date", "scope"):
            if not owner.get(field):
                problems.append(f"owner approval missing {field}")
        if owner.get("reviewer") == manifest.get("producer"):
            problems.append("producer cannot provide owner approval")
    else:
        pending.append("owner_approval")

    independent = manifest.get("independent_review")
    if not isinstance(independent, dict):
        problems.append("independent_review object required")
    else:
        review_status = independent.get("status")
        if review_status == "passed":
            reviewer = independent.get("reviewer")
            if not reviewer:
                problems.append("independent review reviewer missing")
            elif reviewer == manifest.get("producer"):
                problems.append("independent review cannot be performed by producer")
            _verify_ref(independent.get("report"), "independent_review.report",
                        project_root, verify_hashes, problems)
        elif review_status in {"pending", "pending_assignment", "not_requested"}:
            pending.append("independent_review")
        elif review_status in {"fail", "blocked", "revise_before_growth"}:
            failures.append("independent_review")
        else:
            problems.append(f"independent_review: invalid status {review_status!r}")

    if problems or failures:
        status, exit_code = "fail", 1
    elif pending:
        status, exit_code = "pending", 2
    else:
        status, exit_code = "pass", 0

    return {
        "schema": "sms_art_review_checklist_report_v1",
        "status": status,
        "exit_code": exit_code,
        "asset_id": manifest.get("asset_id"),
        "characters_reviewed": len(by_id),
        "axis_counts": axis_counts,
        "failed_axes": failures,
        "pending_axes": pending,
        "problems": problems,
        "claim_ceiling": "checklist_completeness_only; artistic_truth_requires_human_review",
    }


def _self_check():
    axes = sorted(PIXEL_SPRITE_REQUIRED_AXES) + ["hands", "equipment"]
    characters = ["alpha", "beta"]
    with tempfile.TemporaryDirectory(prefix="sms_art_review_") as root:
        for name in ("asset.png", "source.png", "ref.png", "review.json"):
            with open(os.path.join(root, name), "wb") as stream:
                stream.write(name.encode("ascii"))
        def ref(name):
            path = os.path.join(root, name)
            return {"path": name, "sha256": _file_sha(path)}
        rows = []
        for char_id in characters:
            rows.append({
                "id": char_id,
                "references": [ref("ref.png")],
                "observed_defects": [],
                "revision_notes": ["reviewed"],
                "review_axes": {axis: {"status": "pass", "note": "clear"}
                                for axis in axes},
            })
        base = {
            "schema": SCHEMA,
            "asset_id": "fixture",
            "producer": "artist",
            "asset": dict(ref("asset.png"), kind="pixel_sprite_sheet"),
            "source_evidence": ref("source.png"),
            "required_characters": characters,
            "required_axes": axes,
            "characters": rows,
            "independent_review": {"status": "passed", "reviewer": "reviewer",
                                   "report": ref("review.json")},
            "owner_approval": {"approved": True, "reviewer": "owner",
                               "date": "2026-01-01", "scope": "fixture"},
        }
        report = audit(base, root, verify_hashes=True)
        assert report["status"] == "pass", report
        assert report["exit_code"] == 0, report

        broad = json.loads(json.dumps(base))
        broad["required_axes"] = ["hands", "equipment"]
        report = audit(broad, root, verify_hashes=True)
        assert any("pixel sprite review requires explicit micro-axes" in problem
                   for problem in report["problems"]), report

        shade_flow_missing = json.loads(json.dumps(base))
        shade_flow_missing["required_axes"].remove("material_shadow_flow_coherence")
        for row in shade_flow_missing["characters"]:
            del row["review_axes"]["material_shadow_flow_coherence"]
        report = audit(shade_flow_missing, root, verify_hashes=True)
        assert any("material_shadow_flow_coherence" in problem
                   for problem in report["problems"]), report

        palette_role_missing = json.loads(json.dumps(base))
        palette_role_missing["required_axes"].remove("semantic_palette_role_confinement")
        for row in palette_role_missing["characters"]:
            del row["review_axes"]["semantic_palette_role_confinement"]
        report = audit(palette_role_missing, root, verify_hashes=True)
        assert any("semantic_palette_role_confinement" in problem
                   for problem in report["problems"]), report

        unknown_kind = json.loads(json.dumps(base))
        unknown_kind["asset"]["kind"] = "pixel_sprite_roster_baord"
        report = audit(unknown_kind, root, verify_hashes=True)
        assert any("unsupported pixel sprite kind" in problem
                   for problem in report["problems"]), report

        concept = json.loads(json.dumps(base))
        concept["asset"]["kind"] = "character_concept_model_sheet"
        concept_axes = sorted(CONCEPT_SHEET_REQUIRED_AXES) + ["identity"]
        concept["required_axes"] = concept_axes
        for row in concept["characters"]:
            row["review_axes"] = {
                axis: {"status": "pending", "note": "awaiting visual review"}
                for axis in concept_axes
            }
        report = audit(concept, root, verify_hashes=True)
        assert report["status"] == "pending" and not report["problems"], report

        concept_missing = json.loads(json.dumps(concept))
        concept_missing["required_axes"].remove("pose_anatomy_and_joint_continuity")
        for row in concept_missing["characters"]:
            del row["review_axes"]["pose_anatomy_and_joint_continuity"]
        report = audit(concept_missing, root, verify_hashes=True)
        assert any("concept model sheet review requires explicit axes" in problem
                   for problem in report["problems"]), report

        layout_missing = json.loads(json.dumps(concept))
        layout_missing["required_axes"].remove("document_and_layout")
        for row in layout_missing["characters"]:
            del row["review_axes"]["document_and_layout"]
        report = audit(layout_missing, root, verify_hashes=True)
        assert any("document_and_layout" in problem for problem in report["problems"]), report

        layout_exempt = json.loads(json.dumps(concept))
        for row in layout_exempt["characters"]:
            row["review_axes"]["document_and_layout"] = {
                "status": "not_applicable", "note": "fixture", "reason": "raw has no cards"}
        report = audit(layout_exempt, root, verify_hashes=True)
        assert any("layout cannot be exempted" in problem for problem in report["problems"]), report

        waiting = json.loads(json.dumps(base))
        waiting["owner_approval"]["approved"] = False
        report = audit(waiting, root, verify_hashes=True)
        assert report["status"] == "pending" and report["exit_code"] == 2, report

        failed = json.loads(json.dumps(base))
        failed["characters"][0]["review_axes"]["hands"] = {
            "status": "fail", "note": "grip is unclear"}
        report = audit(failed, root, verify_hashes=True)
        assert report["status"] == "fail" and report["exit_code"] == 1, report

        incomplete = json.loads(json.dumps(base))
        del incomplete["characters"][1]["review_axes"]["equipment"]
        report = audit(incomplete, root, verify_hashes=True)
        assert report["status"] == "fail" and report["problems"], report

        stale = json.loads(json.dumps(base))
        stale["asset"]["sha256"] = "0" * 64
        report = audit(stale, root, verify_hashes=True)
        assert any("sha256 mismatch" in problem for problem in report["problems"]), report

    print("[SELF-CHECK OK] audit_art_review_checklist "
          "(eixos conceituais, fluxo sombra/material obrigatório, cobertura, "
          "revisão independente, fail/pending e hashes)")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", help="review checklist JSON")
    parser.add_argument("--project-root", default=".",
                        help="root for relative artifact/reference paths")
    parser.add_argument("--verify-hashes", action="store_true",
                        help="verify candidate, evidence and source-reference SHA-256")
    parser.add_argument("--json", help="optional output report path")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        return _self_check()
    if not args.manifest:
        parser.error("--manifest is required unless --self-check is used")
    try:
        with open(args.manifest, encoding="utf-8") as stream:
            manifest = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] cannot load manifest: {exc}", file=sys.stderr)
        return 1
    report = audit(manifest, args.project_root, args.verify_hashes)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["status"] == "pass":
        print("[PASS] review checklist complete; owner-approved")
    elif report["status"] == "pending":
        print("[PENDING] checklist blocks promotion until review axes and owner approval close")
    else:
        print("[FAIL] invalid checklist or failed artistic axes block promotion")
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
