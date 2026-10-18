#!/usr/bin/env python3
"""Validate native-worker emulator evidence against a coordinator-owned request.

Checks bindings and coverage, not the truth of artistic/gameplay judgments.
Use --require-passed to reject valid reports that contain failed/not_run tests.
Native dispatch identity comes from the coordinator's actual tool receipt;
neither this gate nor the harness spawns agents.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess

SCHEMA = "sms_subagent_session_v2"
LEGACY_SCHEMA = "sms_subagent_session_v1"
CONTEXT_CONTRACT = "readable_project_context_v1"
CONTEXT_ROLES = ("doc/10-memory-bank.md", "doc/11-gdd.md", "doc/13-spec-cenas.md", "doc/15-tdd.md")
KINDS = {"framebuffer", "video", "audio", "rom_observation", "runtime_probe", "input_trace"}
STATUSES = {"passed", "failed", "blocked", "stale", "needs_review"}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ref(path):
    p = Path(path).resolve()
    return {"path": str(p), "sha256": sha(p)}

def check_ref(item):
    if not isinstance(item, dict) or not isinstance(item.get("path"), str):
        raise ValueError("artifact reference absent")
    path = Path(item["path"])
    if not path.is_absolute() or not path.is_file() or sha(path) != item.get("sha256"):
        raise ValueError("missing/stale artifact:" + str(path))
    return path

def validate_request(req):
    if not isinstance(req, dict): return ["request must be an object"]
    problems = []
    if req.get("schema") not in {SCHEMA, LEGACY_SCHEMA} or req.get("artifact_kind") != "session_qa_request":
        problems.append("invalid request schema")
    for key in ("task_id", "producer_id", "worker_id", "scope"):
        if not isinstance(req.get(key), str) or not req[key].strip(): problems.append("missing:"+key)
    if req.get("producer_id") == req.get("worker_id"): problems.append("self approval")
    if req.get("lane") not in {"visual", "runtime", "audio_qa"}: problems.append("invalid lane")
    if not Path(req.get("project", "")).is_absolute(): problems.append("project must be absolute")
    try:
        check_ref(req.get("rom"))
        for item in req.get("inputs", []): check_ref(item)
        if req.get("schema") == SCHEMA:
            root = Path(req["input_root"]).resolve()
            if not Path(req["input_root"]).is_absolute() or req.get("input_binding") != "frozen_snapshot_v1":
                raise ValueError("snapshot contract absent")
            inputs = req.get("inputs")
            if not isinstance(inputs, list) or not inputs:
                raise ValueError("snapshot inputs absent")
            for item in [req["rom"], *inputs]:
                if not check_ref(item).resolve().is_relative_to(root):
                    raise ValueError("snapshot outside input_root")
                if Path(item["path"]).is_symlink(): raise ValueError("snapshot must not be a symlink")
                if Path(item["path"]).stat().st_nlink>1: raise ValueError("snapshot must not be a hardlink")
            if not any(i["path"] == req["rom"]["path"] and i["sha256"] == req["rom"]["sha256"] for i in inputs):
                raise ValueError("ROM absent from snapshots")
            roles = []
            for item in inputs:
                if not Path(item.get("origin", "")).is_absolute() or not item.get("role"):
                    raise ValueError("snapshot origin/role absent")
                origin = Path(item["origin"])
                try:
                    aliases = origin.is_file() and origin.samefile(item["path"])
                except OSError:
                    aliases = False  # Origin health is not historical snapshot integrity.
                if aliases: raise ValueError("snapshot aliases active origin")
                roles.append(item["role"])
            if len(set(roles)) != len(roles): raise ValueError("duplicate snapshot role")
            if "context_contract" in req:
                if req["context_contract"]!=CONTEXT_CONTRACT or req.get("context_mode") not in {"production","diagnostic"}:
                    raise ValueError("invalid context contract/mode")
                documents=req.get("context_documents")
                if not isinstance(documents,list) or len(documents)!=len(CONTEXT_ROLES):
                    raise ValueError("context coverage incomplete")
                if {d.get("role") for d in documents if isinstance(d,dict)}!=set(CONTEXT_ROLES):
                    raise ValueError("context roles incomplete/duplicate")
                for doc in documents:
                    role=doc["role"];matches=[i for i in inputs if i["role"]==role]
                    if doc.get("status")=="snapshot":
                        if len(matches)!=1:raise ValueError("context snapshot absent:"+role)
                        content=check_ref(matches[0]).read_bytes().decode("utf-8")
                        if not content.strip():raise ValueError("empty context snapshot:"+role)
                    elif doc.get("status")=="missing":
                        if req["context_mode"]!="diagnostic" or not doc.get("reason") or matches or not req.get("diagnostic_reason"):
                            raise ValueError("undeclared/production context omission:"+role)
                    else:raise ValueError("unreadable context cannot be omitted:"+role)
    except (ValueError, OSError, KeyError, TypeError) as e: problems.append(str(e))
    cases = req.get("cases")
    if not isinstance(cases, list) or not cases: return problems + ["no assigned cases"]
    if req.get("schema") == SCHEMA:
        relation = req.get("case_relation")
        applicable = sum(isinstance(c,dict) and c.get("applicable",True) is True for c in cases)
        if relation not in {"independent", "chained"}: problems.append("case relation must be explicit")
        if relation == "independent" and applicable != 1:
            problems.append("independent request requires exactly one applicable case and fresh session")
    seen = set()
    for case in cases:
        if not isinstance(case, dict): problems.append("case must be an object"); continue
        cid = case.get("id")
        if not isinstance(cid, str) or not cid or cid in seen: problems.append("missing/duplicate case")
        if isinstance(cid,str): seen.add(cid)
        if "applicable" in case and type(case["applicable"]) is not bool: problems.append("applicable must be boolean")
        if case.get("precondition"):
            try:
                pre = case["precondition"]
                addr = int(str(pre["address"]),0); length = pre["length"]
                expected = bytes.fromhex(pre["equals_hex"])
                if type(length) is not int or not 1 <= length <= 256 or len(expected)!=length or not 0xC000<=addr<=0xDFFF or addr+length>0xE000:
                    raise ValueError()
            except (ValueError,KeyError,TypeError): problems.append("invalid ROM precondition:"+str(cid))
        if case.get("proof") not in KINDS: problems.append("unknown proof:"+str(cid))
        if not case.get("expectation") or not case.get("axis"): problems.append("case lacks axis/expectation:"+str(cid))
        if case.get("applicable", True) is False and not case.get("reason"): problems.append("N/A needs coordinator reason:"+str(cid))
        if case.get("sequence"):
            try:
                steps = case["sequence"]
                if not isinstance(steps,list) or len(steps)>256: raise ValueError()
                total = 0
                for s in steps:
                    for k, maximum in [("p1",63),("p2",63),("console",3),("frames",36000)]:
                        v = s.get(k,0)
                        if type(v) is not int or not 0<=v<=maximum: raise ValueError()
                    if "frames" not in s: raise ValueError()
                    total += s["frames"]
                if total>36000 or (case["proof"]=="video" and not 2<=total<=1800): raise ValueError()
            except (ValueError,AttributeError,TypeError): problems.append("invalid frame script:"+str(cid))
    return problems

def validate_report(report, req, check_session=True):
    if not isinstance(report, dict) or not isinstance(req, dict):
        return {"ok":False,"tests_passed":False,"problems":["request/report must be objects"]}
    problems = validate_request(req)
    if report.get("schema") != req.get("schema") or report.get("artifact_kind") != "harness_worker_result":
        problems.append("invalid worker result schema")
    for key in ("task_id", "project", "producer_id", "worker_id", "lane"):
        if report.get(key) != req.get(key): problems.append("request mismatch:"+key)
    if req.get("schema") == SCHEMA and report.get("case_relation") != req.get("case_relation"):
        problems.append("request mismatch:case_relation")
    if report.get("status") not in STATUSES: problems.append("invalid status")
    if report.get("claim_ceiling") != "assigned_checks_only" or report.get("promoted") is not False:
        problems.append("worker claim/promotion forbidden")
    try:
        check_ref(report.get("request"))
        loaded = json.loads(Path(report["request"]["path"]).read_text())
        if loaded != req: problems.append("report references different coordinator request")
    except (ValueError, OSError, KeyError) as e: problems.append(str(e))
    findings = report.get("findings")
    if not isinstance(findings, list): problems.append("findings must be explicit array")
    elif report.get("status") == "passed" and any(f.get("kind") in {"defect", "risk"} for f in findings):
        problems.append("blocking findings cannot pass")
    coverage = report.get("coverage")
    if not isinstance(coverage, list): coverage = []; problems.append("coverage absent")
    planned = {c["id"]: c for c in req.get("cases", []) if isinstance(c, dict) and isinstance(c.get("id"),str)}
    if any(not isinstance(c,dict) for c in coverage):
        coverage = []; problems.append("case results must be objects")
    ids = [c.get("id") for c in coverage]
    if len(ids) != len(set(ids)) or set(ids) != set(planned): problems.append("coverage differs from assigned cases")
    executed = any(c.get("status") in {"passed", "failed"} for c in coverage)
    session = report.get("session")
    sid, rom_hash = None, req.get("rom", {}).get("sha256")
    if executed or session is not None:
        try:
            if session.get("owner") != req["worker_id"]: problems.append("wrong session owner")
            sid = session["id"]
            bundle = Path(session["bundle"]) if session.get("bundle") else None
            meta = json.loads((bundle/"session.json").read_text()) if bundle else json.loads(check_ref(session["metadata"]).read_text())
            if not bundle and report.get("status") == "passed": problems.append("passed result requires sealed informative bundle")
            if check_session and bundle:
                from session_bridge.isolated import check_bundle
                ok, why = check_bundle(bundle)
                if not ok: problems.append("invalid bundle:"+why)
            if meta["session_id"] != sid or meta["rom_sha256"] != rom_hash: problems.append("session/ROM mismatch")
            closed = json.loads(check_ref(session["closed"]).read_text())
            for k in ("session_id", "rom_sha256", "emulator_process", "supervisor", "xvfb_process"):
                if closed.get(k) != meta.get(k): problems.append("cleanup identity mismatch:"+k)
            if closed.get("state") != "closed": problems.append("session not closed")
            if check_session:
                from session_bridge.isolated import alive
                for key in ("emulator_process", "supervisor", "xvfb_process"):
                    if closed.get(key) and alive(closed[key]): problems.append("owned process still alive:"+key)
        except (AttributeError, ValueError, OSError, KeyError, TypeError) as e: problems.append("missing/invalid session:"+str(e))
    artifacts = report.get("artifacts")
    if not isinstance(artifacts, list): artifacts = []; problems.append("artifacts absent")
    seen_artifacts, kinds = set(), {}
    for artifact in artifacts:
        aid = artifact.get("id")
        if not aid or aid in seen_artifacts: problems.append("missing/duplicate artifact id")
        seen_artifacts.add(aid); kinds[aid] = artifact.get("kind")
        try:
            path = check_ref(artifact); kind = artifact.get("kind")
            if kind not in KINDS: raise ValueError("unknown artifact kind")
            if kind == "input_trace":
                rows = [json.loads(line) for line in path.read_text().splitlines() if line]
                if not rows: raise ValueError("empty input trace")
                if any(r["ack"].get("session_id") != sid or r["ack"].get("ok") is not True for r in rows):
                    raise ValueError("trace session mismatch/rejected ACK")
            else:
                metadata = json.loads(check_ref(artifact["metadata"]).read_text())
                if metadata.get("session_id") != sid or metadata.get("rom_sha256") != rom_hash:
                    raise ValueError("artifact metadata session/ROM mismatch")
                if kind in {"framebuffer", "video"} and metadata.get("sha256") != artifact["sha256"]:
                    raise ValueError("framebuffer/video hash mismatch")
                if kind == "framebuffer":
                    from PIL import Image
                    with Image.open(path) as im:
                        if im.size != (256,192) or metadata.get("canvas") != [256,192]: raise ValueError("non-native framebuffer")
                if kind == "video" and (metadata.get("frames", 0) < 2 or metadata.get("performance") != "not_measured"):
                    raise ValueError("stepped video cannot prove FPS")
                if kind == "video":
                    probe = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
                                            "stream=width,height,nb_frames","-of","json",str(path)],
                                           capture_output=True,text=True,timeout=15)
                    streams = json.loads(probe.stdout).get("streams",[]) if probe.returncode == 0 else []
                    if not streams or [streams[0].get("width"),streams[0].get("height")] != [256,192]: raise ValueError("non-native video")
                    if int(streams[0].get("nb_frames",-1)) != metadata["frames"]: raise ValueError("video count mismatch")
                if kind == "audio":
                    import wave
                    with wave.open(str(path)) as wav: seconds = wav.getnframes()/wav.getframerate()
                    if metadata.get("wav_sha256") != artifact["sha256"] or seconds < metadata.get("requested_seconds", 0)*0.95:
                        raise ValueError("audio binding/duration failed")
                    if metadata.get("requested_seconds", 0) <= 0: raise ValueError("audio duration missing")
                    with wave.open(str(path)) as wav: pcm = wav.readframes(wav.getnframes())
                    import array
                    samples = array.array('h'); samples.frombytes(pcm)
                    if metadata.get("peak") != max((abs(x) for x in samples),default=0): raise ValueError("audio peak mismatch")
                if kind == "rom_observation" and (metadata.get("origin") != "read_only_bridge" or not metadata.get("samples")):
                    raise ValueError("ROM observations absent")
                if kind == "rom_observation" and any(s.get("session_id") != sid or s.get("ok") is not True
                                                       for s in metadata["samples"]):
                    raise ValueError("ROM observation ACK/session mismatch")
        except (ValueError, OSError, KeyError, TypeError, subprocess.TimeoutExpired) as e: problems.append("artifact:"+str(aid)+":"+str(e))
    for row in coverage:
        case = planned.get(row.get("id"), {})
        status = row.get("status")
        if status not in {"passed", "failed", "not_run", "not_applicable"}: problems.append("invalid case status")
        if not row.get("note"): problems.append("case observation/reason absent:"+str(row.get("id")))
        if status == "not_applicable" and case.get("applicable", True): problems.append("worker cannot waive required case")
        if status in {"passed", "failed"}:
            evidence = row.get("evidence", [])
            if not evidence or not set(evidence) <= seen_artifacts or case.get("proof") not in [kinds.get(i) for i in evidence]:
                problems.append("case lacks required evidence:"+str(row.get("id")))
        if status == "passed" and req.get("schema") == SCHEMA and case.get("precondition"):
            try:
                art=next(a for a in report["artifacts"] if a.get("id")==case["id"]+"_precondition")
                observed=json.loads(check_ref(art).read_text())
                if observed.get("expected")!=case["precondition"] or observed.get("session_id")!=sid or observed.get("rom_sha256")!=rom_hash:
                    raise ValueError("wrong precondition binding")
                if not observed.get("samples") or bytes(observed["samples"][0]["ram"])!=bytes.fromhex(case["precondition"]["equals_hex"]):
                    raise ValueError("ROM baseline differs")
            except (StopIteration,ValueError,OSError,KeyError,TypeError) as e:
                problems.append("missing/failed ROM precondition:"+str(e))
        if report.get("status") == "passed" and status not in {"passed", "not_applicable"}:
            problems.append("passed report has incomplete/failed case")
    if report.get("status") == "passed" and not executed: problems.append("passed report has no executed case")
    return {"ok": not problems, "tests_passed": not problems and report.get("status") == "passed",
            "problems": problems, "claim_ceiling": "assigned_checks_only",
            "case_relation":req.get("case_relation","legacy_combined_unverified"),
            "input_binding":req.get("input_binding","legacy_mutable_refs"),
            "context_mode":req.get("context_mode","legacy_context_unverified"),
            "limit": "bindings/coverage only; coordinator must match native tool receipt and review observations"}

def current_eligibility(req, rom):
    """Current-build comparison is separate from historical snapshot integrity."""
    try:
        actual = sha(rom)
        return {"eligible":actual==req["rom"]["sha256"],"observed_rom_sha256":actual,
                "expected_rom_sha256":req["rom"]["sha256"],"scope":"ROM only; current design/context needs coordinator reconciliation"}
    except (OSError,KeyError,TypeError) as e: return {"eligible":False,"problem":str(e)}

def fixture(root):
    """Offline schema fixture; never an emulator/gameplay approval."""
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    (root/"rom.sms").write_bytes(b"fixture not runnable")
    req = {"schema": SCHEMA, "artifact_kind": "session_qa_request", "task_id": "test",
           "project": str(root.resolve()), "producer_id": "producer", "worker_id": "native-worker",
           "lane": "runtime", "scope": "diagnostic fixture", "rom": ref(root/"rom.sms"),
           "input_root":str(root.resolve()),"input_binding":"frozen_snapshot_v1","case_relation":"independent",
           "inputs": [dict(ref(root/"rom.sms"),origin=str((root/"original.sms").resolve()),role="rom")],
           "cases": [{"id": "boot", "axis": "controls", "proof": "input_trace", "expectation": "ACK"}]}
    (root/"request.json").write_text(json.dumps(req))
    bundle = root/"bundle"; bundle.mkdir()
    meta = {"session_id": "fixture", "rom_sha256": req["rom"]["sha256"], "state": "sealed"}
    (bundle/"session.json").write_text(json.dumps(meta))
    (root/"closed.json").write_text(json.dumps(dict(meta, state="closed")))
    (root/"commands.jsonl").write_text(json.dumps({"ack": {"ok": True, "session_id": "fixture"}})+'\n')
    report = {"schema": SCHEMA, "artifact_kind": "harness_worker_result", **{k:req[k] for k in ["task_id","project","producer_id","worker_id","lane"]},
              "request": ref(root/"request.json"), "case_relation":"independent", "status": "passed", "claim_ceiling": "assigned_checks_only", "promoted": False,
              "session": {"id":"fixture","owner":req["worker_id"],"bundle":str(bundle.resolve()),"closed":ref(root/"closed.json")},
              "coverage": [{"id":"boot","status":"passed","note":"offline fixture","evidence":["commands"]}],
              "artifacts": [{"id":"commands","kind":"input_trace",**ref(root/"commands.jsonl")}], "findings": []}
    return req, report

def self_check():
    with tempfile.TemporaryDirectory() as tmp:
        req, rep = fixture(tmp)
        assert validate_report(rep, req, False)["tests_passed"]
        mutations = [lambda d:d.update(worker_id="producer"), lambda d:d.update(promoted=True),
                     lambda d:d.update(claim_ceiling="aaa"), lambda d:d.update(coverage=[]),
                     lambda d:d["coverage"][0].update(status="not_run"), lambda d:d["coverage"][0].update(status="not_applicable"),
                     lambda d:d.update(session=None), lambda d:d["artifacts"][0].update(sha256="0"*64),
                     lambda d:d["session"].update(id="other"), lambda d:d.update(findings=[{"kind":"defect"}])]
        for mutate in mutations:
            bad = copy.deepcopy(rep); mutate(bad)
            assert not validate_report(bad, req, False)["ok"]
        blocked = copy.deepcopy(rep); blocked.update(status="blocked", session=None, artifacts=[])
        blocked["coverage"][0].update(status="not_run", note="missing emulator dependency", evidence=[])
        assert validate_report(blocked, req, False)["ok"] and not validate_report(blocked, req, False)["tests_passed"]
        partial = copy.deepcopy(rep);partial.update(status="blocked")
        partial["session"].update(bundle=None,metadata=partial["session"]["closed"])
        partial["coverage"][0].update(status="not_run",note="collection interrupted",evidence=[])
        assert validate_report(partial,req,False)["ok"]
        partial["status"]="passed"
        assert not validate_report(partial,req,False)["ok"]
        (Path(tmp)/"commands.jsonl").write_text('{"ack":{"ok":true,"session_id":"wrong"}}\n')
        rep["artifacts"][0].update(ref(Path(tmp)/"commands.jsonl"))
        assert not validate_report(rep, req, False)["ok"]
    with tempfile.TemporaryDirectory() as tmp:
        req, rep = fixture(tmp)
        origin=Path(tmp)/"original.sms";origin.write_bytes(b"new active build")
        assert not validate_request(req) and not current_eligibility(req,origin)["eligible"]
        assert validate_report(rep,req,False)["tests_passed"]
        bad=copy.deepcopy(req);bad.pop("case_relation")
        assert validate_request(bad)
        bad=copy.deepcopy(req);bad["cases"].append(dict(bad["cases"][0],id="second"))
        assert validate_request(bad)
        bad["case_relation"]="chained"
        assert not validate_request(bad)
        bad["cases"][0]["applicable"]="false"
        assert validate_request(bad)
        origin.write_bytes((Path(tmp)/"rom.sms").read_bytes())
        (Path(tmp)/"rom.sms").unlink();(Path(tmp)/"rom.sms").symlink_to(origin)
        assert validate_request(req)
        (Path(tmp)/"rom.sms").unlink()
        import os
        os.link(origin,Path(tmp)/"rom.sms")
        assert validate_request(req)
    with tempfile.TemporaryDirectory() as tmp:
        req,rep=fixture(tmp)
        bad=copy.deepcopy(rep);bad["case_relation"]="chained"
        assert not validate_report(bad,req,False)["ok"]
        (Path(tmp)/"rom.sms").write_bytes(b"tampered snapshot")
        assert validate_request(req)
    with tempfile.TemporaryDirectory() as tmp:
        req,rep=fixture(tmp)
        req["schema"]=LEGACY_SCHEMA;rep["schema"]=LEGACY_SCHEMA
        for key in ("input_binding","input_root","case_relation"):req.pop(key)
        (Path(tmp)/"request.json").write_text(json.dumps(req));rep["request"]=ref(Path(tmp)/"request.json")
        assert validate_report(rep,req,False)["tests_passed"]
    print("[SELF-CHECK OK] subagent session: coverage, independent identity, stale bytes, binding, limits and blocked reports")
    return 0

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--request"); p.add_argument("--report"); p.add_argument("--require-passed", action="store_true")
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--current-rom",help="also require eligibility for this active ROM; historical integrity remains separate")
    a = p.parse_args()
    if a.self_check: return self_check()
    if not a.request or not a.report: p.error("--request and --report required")
    try: result = validate_report(json.loads(Path(a.report).read_text()), json.loads(Path(a.request).read_text()))
    except (ValueError, OSError, TypeError, KeyError) as e: result = {"ok":False,"tests_passed":False,"problems":[str(e)]}
    if a.current_rom:
        try: result["current_eligibility"] = current_eligibility(json.loads(Path(a.request).read_text()),a.current_rom)
        except (ValueError,OSError) as e: result["current_eligibility"] = {"eligible":False,"problem":str(e)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] and (not a.require_passed or result["tests_passed"]) and (not a.current_rom or result["current_eligibility"]["eligible"]) else 1

if __name__ == "__main__": raise SystemExit(main())
