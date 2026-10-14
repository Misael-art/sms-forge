#!/usr/bin/env python3
"""Audit explicit coordinate, finite AIR and collision-cache records.

These are record consistency gates, not gameplay emulation. Source fidelity
and whether the ROM truly maintains revision counters need native review.
"""
import argparse
import copy
import json
import tempfile
from pathlib import Path
from audit_subagent_session import check_ref,ref

REVISIONS=("position_revision","facing_revision","hurtbox_revision","state_revision")

def evaluate(data, require_air_identity=False):
    errors=[]; details={}
    try:
        evidence=data["evidence"]
        if not isinstance(evidence,list) or not evidence:raise ValueError("source/observation evidence absent")
        for item in evidence:check_ref(item)
        kind=data["kind"]
        if require_air_identity and kind!="air_identity_timing":raise ValueError("AIR identity requires air_identity_timing record")
        if kind=="source_distance":
            if data.get("profile")!="standing_facing_pair_uniform_scale":raise ValueError("coordinate profile unsupported")
            scale_num=data["scale_num"];scale_den=data["scale_den"]
            widths=data["source_front_widths"];threshold=data["source_threshold"]
            if not isinstance(widths,list) or len(widths)!=2 or any(type(v) is not int or v<0 for v in widths):raise ValueError("invalid source widths")
            if any(type(v) is not int or v<=0 for v in [scale_num,scale_den,threshold]):raise ValueError("invalid scale/threshold")
            cases=data["cases"]
            if not cases:raise ValueError("distance cases absent")
            details["cases"]=[]
            for case in cases:
                gap=case["axis_gap_sms"]
                if type(gap) is not int or gap<0:raise ValueError("invalid SMS gap")
                num=gap*scale_den-sum(widths)*scale_num
                result=num<threshold*scale_num
                if type(case["expected_lt_threshold"]) is not bool or result!=case["expected_lt_threshold"]:raise ValueError("axis/front comparison disagrees")
                if case.get("observed_numerator",num)!=num:raise ValueError("observed ROM numerator disagrees")
                details["cases"].append({"axis_gap_sms":gap,"source_distance_num":num,"denominator":scale_num,"lt_threshold":result})
        elif kind in {"air_timing","air_identity_timing"}:
            trace=json.loads(check_ref(data["trace"]).read_text())
            durations=data["source_durations"];stamps=trace["air_boundary_stamps"]
            if not isinstance(stamps,list):raise ValueError("AIR stamps must be a list")
            if not isinstance(durations,list) or not durations or data.get("counter_bits")!=16 or len(stamps)!=len(durations)+1:raise ValueError("AIR boundary coverage differs")
            if any(type(v) is not int or not 0<=v<65536 for v in stamps):raise ValueError("invalid ROM timestamp")
            if any(type(v) is not int or not 0<v<32768 for v in durations):raise ValueError("only finite unambiguous durations supported")
            measured=[(b-a)&0xffff for a,b in zip(stamps,stamps[1:])]
            if measured!=durations:raise ValueError("AIR durations differ from source")
            details["measured_frames"]=measured
            details["element_identity_and_order"]="not_measured; require source/ROM IDs associated with every boundary"
            if kind=="air_identity_timing":
                source=json.loads(check_ref(data["source_air"]).read_text())
                expected=source["boundary_element_ids"];observed=trace["air_boundary_element_ids"]
                exported=source.get("durations")
                if not isinstance(exported,list) or any(type(v) is not int or not 0<v<32768 for v in exported) or exported!=durations:
                    raise ValueError("source AIR export durations disagree or are not finite integers")
                for ids in (expected,observed):
                    if not isinstance(ids,list) or len(ids)!=len(stamps):raise ValueError("AIR IDs require N+1 boundaries including terminal")
                    if any(not (type(v) is int and v>=0 or isinstance(v,str) and v.strip()) for v in ids):raise ValueError("invalid AIR element ID")
                if any(type(a) is not type(b) or a!=b for a,b in zip(expected,observed)):raise ValueError("AIR element identity/order differs")
                details["element_identity_and_order"]="matched_declared_source_and_ROM_boundary_IDs"
                details["boundary_element_ids"]=observed
                details["source_export_truth"]="requires independent source/export and ROM instrumentation review"
        elif kind=="collision_cache":
            prepared=data["prepared"];current=data["at_contact"]
            for key in REVISIONS:
                if type(prepared.get(key)) is not int or type(current.get(key)) is not int or min(prepared[key],current[key])<0 or prepared[key]!=current[key]:
                    raise ValueError("stale collision cache:"+key)
            if type(current.get("frame")) is not int or type(data.get("valid_until_frame")) is not int or not 0<=current["frame"]<=data["valid_until_frame"]:
                raise ValueError("collision cache expired")
            details["revision_match"]=True
        else:raise ValueError("unknown semantics kind")
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:errors.append(str(e))
    return {"ok":not errors,"problems":errors,"details":details,"claim_ceiling":"declared_record_consistency_only",
            "limits":"No universal CNS compatibility, wall-clock FPS, dynamic opponent proof, or artistic judgment. AIR identity is checked only in air_identity_timing and remains declared-record consistency, not authentication of the AIR export or ROM instrumentation. Distance profile is restricted; counters/revisions require source and native observations."}

def fixture(root,kind="source_distance"):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    p=root/"source.json";p.write_text('{"offline_fixture":true}')
    base={"kind":kind,"evidence":[ref(p)]}
    if kind=="source_distance":base.update(profile="standing_facing_pair_uniform_scale",scale_num=72,scale_den=107,source_front_widths=[18,18],source_threshold=32,cases=[{"axis_gap_sms":45,"expected_lt_threshold":True},{"axis_gap_sms":46,"expected_lt_threshold":False,"observed_numerator":2330}])
    if kind in {"air_timing","air_identity_timing"}:
        p.write_text(json.dumps({"air_boundary_stamps":[65530,0,8]}))
        base.update(evidence=[ref(p)],trace=ref(p),counter_bits=16,source_durations=[6,8])
        if kind=="air_identity_timing":
            p.write_text(json.dumps({"offline_fixture":True,"air_boundary_stamps":[65530,0,8],"air_boundary_element_ids":[0,1,"terminal"]}))
            source=root/"source_air.json";source.write_text(json.dumps({"offline_fixture":True,"durations":[6,8],"boundary_element_ids":[0,1,"terminal"]}))
            base.update(evidence=[ref(p),ref(source)],trace=ref(p),source_air=ref(source))
    if kind=="collision_cache":base.update(prepared=dict.fromkeys(REVISIONS,1),at_contact=dict(dict.fromkeys(REVISIONS,1),frame=10),valid_until_frame=10)
    return base

def self_check():
    with tempfile.TemporaryDirectory() as tmp:
        for kind in ("source_distance","air_timing","air_identity_timing","collision_cache"):
            good=fixture(Path(tmp)/kind,kind);assert evaluate(good)["ok"]
            bad=copy.deepcopy(good)
            if kind=="source_distance":bad["source_front_widths"]=[0,0]
            if kind in {"air_timing","air_identity_timing"}:bad["source_durations"]=[6,9]
            if kind=="collision_cache":bad["at_contact"]["position_revision"]=2
            assert not evaluate(bad)["ok"]
        good=fixture(Path(tmp)/"identity","air_identity_timing")
        source=Path(good["source_air"]["path"]);trace=Path(good["trace"]["path"])
        source.write_text(json.dumps({"offline_fixture":True,"durations":[6,6],"boundary_element_ids":[0,1,"terminal"]}))
        trace.write_text(json.dumps({"offline_fixture":True,"air_boundary_stamps":[65530,0,6],"air_boundary_element_ids":[1,0,"terminal"]}))
        good.update(source_durations=[6,6],source_air=ref(source),trace=ref(trace),evidence=[ref(source),ref(trace)])
        assert not evaluate(good,True)["ok"]
        durations=copy.deepcopy(good);durations["kind"]="air_timing"
        assert evaluate(durations)["ok"] and not evaluate(durations,True)["ok"]
        for ids in ([0,1],[0,True,"terminal"],[0,1,""]):
            trace.write_text(json.dumps({"air_boundary_stamps":[65530,0,6],"air_boundary_element_ids":ids}))
            good.update(trace=ref(trace),evidence=[ref(source),ref(trace)])
            assert not evaluate(good)["ok"]
        trace.write_text(json.dumps({"air_boundary_stamps":[65530,0,6],"air_boundary_element_ids":[0,1,"terminal"]}))
        for exported in ([6.0,6.0],[True,6],"6,6"):
            source.write_text(json.dumps({"durations":exported,"boundary_element_ids":[0,1,"terminal"]}))
            good.update(source_air=ref(source),trace=ref(trace),evidence=[ref(source),ref(trace)])
            assert not evaluate(good,True)["ok"]
        for key in REVISIONS:
            bad=fixture(Path(tmp)/"cache","collision_cache");bad["at_contact"][key]=2
            assert not evaluate(bad)["ok"]
    print("[SELF-CHECK OK] explicit source coordinates, ROM AIR boundaries and cache revision validity")
    return 0

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--record");p.add_argument("--self-check",action="store_true");p.add_argument("--require-air-identity",action="store_true")
    a=p.parse_args()
    if a.self_check:return self_check()
    if not a.record:p.error("--record required")
    try:out=evaluate(json.loads(Path(a.record).read_text()),a.require_air_identity)
    except (ValueError,OSError) as e:out={"ok":False,"problems":[str(e)]}
    print(json.dumps(out,indent=2,ensure_ascii=False));return 0 if out["ok"] else 1

if __name__=="__main__":raise SystemExit(main())
