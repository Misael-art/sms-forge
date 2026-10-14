#!/usr/bin/env python3
"""quality_review_router.py — review independente, no máximo 3 domínios.

Porta o MÉTODO do SGDKForge: o produtor não se autoaprova; parecer stale
(hash divergente) cai; review não declara ready_for_aaa.

Uso:
  quality_review_router.py plan --request <json>
  quality_review_router.py validate-report --report <json>
  quality_review_router.py --self-check
Exit: 0 ok | 1 contrato violado | 3 uso
"""
from __future__ import annotations

import argparse
import json
import sys

VERSION = "1.0.0"
MAX_REVIEWS = 3
STAGES = ("foundation", "pre_growth", "vertical_slice", "release_candidate")
DOMAINS = (
    "game_design", "gameplay", "art", "animation", "audio",
    "code", "hardware", "governance",
)
OWNERS = {
    "game_design": "skills/game-design-core-loop.md",
    "gameplay": "skills/sms-gameplay-experience-review.md",
    "art": "skills/sms-visual-excellence.md",
    "animation": "skills/sms-sprite-animation.md",
    "audio": "skills/sms-psg-audio.md",
    "code": "agents/sms-game-director.md",
    "hardware": "skills/sms-vdp-budget-analyst.md",
    "governance": "rules/SMS_GLOBAL.md",
}
STAGE_DEFAULTS = {
    "foundation": ("game_design",),
    "pre_growth": ("gameplay", "game_design"),
    "vertical_slice": ("gameplay", "art", "hardware"),
    "release_candidate": ("governance", "gameplay", "hardware"),
}


def plan(request):
    findings = []
    if request.get("artifact_kind") != "quality_review_request":
        findings.append("artifact_kind deve ser quality_review_request")
    stage = request.get("stage")
    if stage not in STAGES:
        findings.append(f"stage '{stage}' fora de {STAGES}")
    producer = request.get("producer") or request.get("author")
    if not producer:
        findings.append("producer ausente — review sem autor não é independente")

    artifacts = request.get("artifacts") or []
    if not artifacts:
        findings.append("sem artefatos hash-bound")
    for art in artifacts:
        if not art.get("sha256") or not art.get("path"):
            findings.append(f"artefato sem path/sha256: {art}")

    requested = list(request.get("domains") or STAGE_DEFAULTS.get(stage, ()))
    domains = []
    for d in requested:
        if d not in DOMAINS:
            findings.append(f"domínio desconhecido: {d}")
            continue
        if d not in domains:
            domains.append(d)
    if len(domains) > MAX_REVIEWS:
        domains = domains[:MAX_REVIEWS]

    reviews = [{
        "domain": d,
        "owner_skill": OWNERS[d],
        "read_only": True,
        "independent_of_producer": True,
    } for d in domains]

    out = {
        "schema": "quality_review_plan_v1",
        "artifact_kind": "quality_review_plan",
        "tool": {"name": "quality_review_router", "version": VERSION},
        "stage": stage,
        "producer": producer,
        "reviews": reviews,
        "findings": findings,
        "claim_ceiling": "quality_review_plan_only",
        "ok": not findings and bool(reviews),
    }
    if request.get("execution_mode") == "isolated_native_subagents":
        out["execution_mode"] = "isolated_native_subagents"
        for key in ("project", "rom", "requested_tasks"):
            out[key] = request.get(key)
            if not out[key]: findings.append("native review request missing:"+key)
        out["workflow"] = "workflows/subagent-emulator-qa.md"
        for review in reviews: review["private_session_per_worker"] = True
        out["ok"] = not findings and bool(reviews)
    return out


def validate_report(report, plan_doc=None):
    problems = []
    if plan_doc and plan_doc.get("execution_mode") == "isolated_native_subagents" and report.get("execution_mode") != "isolated_native_subagents":
        problems.append("native plan cannot downgrade to legacy review")
    if report.get("artifact_kind") != "independent_quality_review":
        problems.append("artifact_kind deve ser independent_quality_review")
    if report.get("claim_ceiling") != "independent_quality_review_only":
        problems.append("quality_review_claim_ceiling_mismatch")
    if report.get("ready_for_aaa") is True or report.get("claim") in {"aaa", "ready_for_aaa"}:
        problems.append("quality_review_cannot_claim_aaa")
    producer = report.get("producer")
    reviewer = report.get("reviewer")
    if not reviewer:
        problems.append("reviewer ausente")
    if not producer: problems.append("producer ausente")
    if producer and reviewer and producer == reviewer:
        problems.append("self_approval_forbidden")
    if report.get("status") not in {"passed", "revise_before_growth", "blocked",
                                    "needs_evidence", "stale"}:
        problems.append("status fora do vocabulário")

    artifacts = report.get("artifacts") or []
    if not artifacts: problems.append("sem artefatos hash-bound")
    for art in artifacts:
        expected = art.get("sha256")
        observed = art.get("observed_sha256")
        if not expected or not observed: problems.append("artifact expected/observed hash absent")
        elif expected != observed:
            problems.append(f"stale_artifact:{art.get('path')}")

    domains = report.get("domains") or []
    if len(domains) > MAX_REVIEWS:
        problems.append(f"mais de {MAX_REVIEWS} reviews")
    if plan_doc:
        planned = [r["domain"] for r in plan_doc.get("reviews") or []]
        extra = [d for d in domains if d not in planned]
        if extra:
            problems.append(f"domínio fora do plano: {extra}")

    taste_only = all(
        f.get("kind") in {"opportunity", "taste"}
        for f in (report.get("findings") or [])
    ) if report.get("findings") else False
    blocking = [f for f in (report.get("findings") or [])
                if f.get("kind") in {"defect", "risk"}]
    if blocking and report.get("status") == "passed":
        problems.append("defect/risk não pode passar como passed")
    if taste_only and report.get("status") == "blocked":
        problems.append("opportunity/taste não bloqueia")
    if report.get("execution_mode") == "isolated_native_subagents":
        from audit_subagent_session import check_ref, validate_report as validate_worker
        workers = report.get("session_reports") or []
        if not workers: problems.append("native session reports absent")
        try: checkpoint_rom = check_ref(report["rom"])
        except (ValueError,OSError,KeyError) as e: problems.append("checkpoint ROM absent/stale:"+str(e));checkpoint_rom=None
        if not report.get("project"): problems.append("checkpoint project absent")
        task_ids, session_ids = [], []
        for worker in workers:
            try:
                req = json.loads(check_ref(worker["request"]).read_text())
                result = json.loads(check_ref(worker["report"]).read_text())
                if req.get("producer_id") != report.get("producer") or req.get("project") != report.get("project") or req.get("rom",{}).get("sha256") != report.get("rom",{}).get("sha256"):
                    problems.append("native result belongs to another producer/project/ROM")
                task_ids.append(req.get("task_id"))
                if result.get("session"): session_ids.append(result["session"]["id"])
                checked = validate_worker(result, req)
                if not checked["ok"] or (report.get("status") == "passed" and not checked["tests_passed"]):
                    problems.append("invalid/incomplete native session review:"+str(worker.get("report")))
            except (ValueError, OSError, KeyError, TypeError) as e: problems.append(str(e))
        if len(task_ids) != len(set(task_ids)) or set(task_ids) != set(report.get("requested_tasks",[])):
            problems.append("native reports differ from checkpoint assigned tasks")
        if len(session_ids) != len(set(session_ids)): problems.append("native workers shared a mutable session")
        if plan_doc and plan_doc.get("execution_mode") == "isolated_native_subagents":
            for key in ("producer","project","rom","requested_tasks"):
                if plan_doc.get(key) != report.get(key): problems.append("native checkpoint differs from plan:"+key)

    return {
        "schema": "independent_quality_review_validation",
        "ok": not problems,
        "problems": problems,
        "claim_ceiling": "quality_review_validation_only",
    }


def _self_check() -> int:
    req = {
        "artifact_kind": "quality_review_request",
        "stage": "vertical_slice",
        "producer": "agent-a",
        "domains": ["gameplay", "art", "hardware", "audio"],
        "artifacts": [
            {"path": "out/rom/game.sms", "sha256": "abc"},
            {"path": "out/evidence/shot.png", "sha256": "def"},
        ],
    }
    p = plan(req)
    assert p["ok"] and len(p["reviews"]) == 3, p
    assert p["reviews"][0]["read_only"]

    bad_req = dict(req, producer=None, artifacts=[])
    p2 = plan(bad_req)
    assert not p2["ok"] and p2["findings"], p2

    report = {
        "artifact_kind": "independent_quality_review",
        "claim_ceiling": "independent_quality_review_only",
        "producer": "agent-a",
        "reviewer": "agent-b",
        "status": "revise_before_growth",
        "domains": ["gameplay", "art", "hardware"],
        "artifacts": [{"path": "out/rom/game.sms", "sha256": "abc",
                       "observed_sha256": "abc"}],
        "findings": [{"kind": "defect", "summary": "hitstop inaudível"}],
        "ready_for_aaa": False,
    }
    v = validate_report(report, p)
    assert v["ok"], v

    self_ok = dict(report, reviewer="agent-a")
    v = validate_report(self_ok, p)
    assert any("self_approval" in x for x in v["problems"]), v

    aaa = dict(report, ready_for_aaa=True)
    v = validate_report(aaa, p)
    assert any("cannot_claim_aaa" in x for x in v["problems"]), v

    stale = dict(report)
    stale["artifacts"] = [{"path": "out/rom/game.sms", "sha256": "abc",
                           "observed_sha256": "fff"}]
    v = validate_report(stale, p)
    assert any("stale_artifact" in x for x in v["problems"]), v
    assert not validate_report(dict(report, artifacts=[]))["ok"]
    assert not validate_report(dict(report, producer=None))["ok"]
    assert not validate_report(dict(report, execution_mode="isolated_native_subagents", session_reports=[]))["ok"]

    print("[SELF-CHECK OK] quality_review_router "
          "(máx 3; sem autoaprovação; sem AAA; hash stale cai)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", choices=["plan", "validate-report"])
    ap.add_argument("--request")
    ap.add_argument("--report")
    ap.add_argument("--plan")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return _self_check()
    if args.command == "plan":
        if not args.request:
            print("uso: quality_review_router.py plan --request <json>", file=sys.stderr)
            return 3
        out = plan(json.load(open(args.request, encoding="utf-8")))
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out["ok"] else 1
    if args.command == "validate-report":
        if not args.report:
            print("uso: quality_review_router.py validate-report --report <json>",
                  file=sys.stderr)
            return 3
        plan_doc = json.load(open(args.plan, encoding="utf-8")) if args.plan else None
        out = validate_report(json.load(open(args.report, encoding="utf-8")), plan_doc)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0 if out["ok"] else 1
    print("uso: quality_review_router.py plan|validate-report | --self-check",
          file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
