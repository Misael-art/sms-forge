"""One-time, non-destructive adoption; never overwrites an existing authority."""
from pathlib import Path
import json
import sys

workspace = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(workspace / "tools/sms_wrapper"))
from artifact_registry import audit, digest, group

root = workspace / "SMS_projects/master_of_fighters"
target = workspace / "doc/artifact_registries/master_of_fighters.json"
catalog = workspace / "doc/artifact_registry_catalog.json"
if target.exists() or catalog.exists():
    raise SystemExit("Authority already exists; reconcile, never overwrite")
d = json.loads((workspace / "tools/sms_wrapper/modelo/doc/artifact_registry.json").read_text())
d["project_id"] = root.name
d["locations"]["planning"] = {"path": "doc", "purpose": "existing contracts and reviews", "mode": "legacy"}
d["adoption"] = {
    "scope": "source tree indexed; selected roles classified; doc/diagnostics remain partial legacy",
    "owner_authentication": "not performed; original source-only declaration retained",
    "conflicts": [
        "Memory points at v10; consolidated workflow and conversion lineage still point at v5, retained as history.",
        "Nested SMS_projects/master_of_fighters tree contains a different JJ prompt; preserved outside output routes.",
        "Style #13 conflict remains open. Adoption approves no new art."
    ]
}

def add(rid, kind, revision, files, status="candidate", variant="main", parents=None, **extra):
    row = {"id": rid, "asset_id": "dr_social", "kind": kind, "variant": variant, "revision": revision,
           "status": status, "parents": parents or [], "reason": extra.pop("reason", "Existing record classified without new artistic approval"),
           "files": [{"role": role, "path": path, "sha256": digest(root / path)} for role, path in files], **extra}
    d["artifacts"].append(row)

source = "data/source_art/sprite_studies/dr_social/dr_social_basic_sequences_61f_owner_source_v1.png"
decision = source.replace(".png", ".json")
old = json.loads((root / decision).read_text())
add("dr-social-animation-source-v01", "animation_source", 1, [("image", source)], status="approved",
    approval_scope=old["approval_scope"], decision={"path": decision, "sha256": digest(root / decision)},
    reason="Original owner-provided 61-pose source; original source-only approval declaration retained unchanged")
add("dr-social-concept-direction-v03", "concept", 3, [("image", "data/source_art/concept_art/dr_social/dr_social_concept_sheet_v3_harmony_proposal.png")], status="historical")
add("dr-social-model-sheet-14-v03", "model_sheet", 3, [("image", "data/source_art/concept_art/dr_social/review_drafts/style_series/style_14_gouache_fantasy/dr_social_model_sheet_14_gouache_fantasy_v3.png")], variant="gouache-fantasy", parents=["dr-social-concept-direction-v03"])
add("dr-social-conversion-proof-v04", "conversion_proof", 4, [
    ("image", "data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.png"),
    ("contract", "data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.json")],
    reason="Two-pose conversion proof, distinct from the complete animation source")
add("dr-social-diagnostic-v05", "diagnostic_conversion", 5,
    [("report", "out/diagnostics/dr_social_61_pose_review_v5/conversion_report_61_pose_v5.json")],
    status="historical", parents=["dr-social-animation-source-v01"])
add("dr-social-diagnostic-v10", "diagnostic_conversion", 10, [
    ("report", "out/diagnostics/dr_social_61_pose_review_v10/conversion_report_61_pose_v10.json"),
    ("preview", "out/diagnostics/dr_social_61_pose_review_v10/dr_social_61_pose_converted_preview_4x.png")],
    parents=["dr-social-animation-source-v01"], supersedes="dr-social-diagnostic-v05",
    reason="Current candidate in memory; supersedes is navigation, not derivation of v10 pixels from v5")
add("dr-social-review-v10", "art_review", 10, [("report", "doc/dr_social_61_pose_art_review_v10.json")], parents=["dr-social-diagnostic-v10"], reason="Pending artistic axes; technical render does not promote art")
add("dr-social-jab-v04", "animation_source", 4, [("image", "data/source_art/sprite_studies/dr_social/review_drafts/2026-10-10_social_light_jab_v4/social_light_jab_candidate_v4.png")], variant="light-jab", reason="Blocked visual candidate; minimal key-present preflight is not artistic approval")
add("dr-social-jab-alpha-v05", "animation_source", 5, [("image", "data/source_art/sprite_studies/dr_social/review_drafts/2026-10-10_social_light_jab_v5_alpha_attempt/social_light_jab_transparency_failed_v5.png")], status="historical", variant="light-jab-alpha-attempt", parents=["dr-social-jab-v04"], reason="Failed alpha attempt preserved, excluded from active source")
for g in sorted({group(a) for a in d["artifacts"]}):
    rows = [a for a in d["artifacts"] if group(a) == g]
    d["heads"].append(dict(zip(("asset_id", "kind", "variant"), g),
        candidate=next((a["id"] for a in rows if a["status"] == "candidate"), None),
        approved=next((a["id"] for a in rows if a["status"] == "approved"), None)))
owned = {f["path"] for a in d["artifacts"] for f in a["files"]}
for f in sorted((root / "data/source_art").rglob("*")):
    if f.is_file():
        rel = f.relative_to(root).as_posix()
        if rel not in owned:
            d["legacy_inventory"].append({"path": rel, "sha256": digest(f)})
report = audit(root, d, True)
if not report["ok"]:
    raise SystemExit(json.dumps(report, ensure_ascii=False, indent=2))
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
catalog.write_text(json.dumps({"schema": "sms_artifact_registry_catalog_v1", "projects": {root.name: {
    "project": "SMS_projects/master_of_fighters", "registry": str(target.relative_to(workspace))}}}, indent=2) + "\n")
Path(__file__).with_name("real_registry_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False))
