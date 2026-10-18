#!/usr/bin/env python3
"""Audit sealed stage-boundary counts; this does not measure CPU durations.

Input: measure_worst_frame JSON with stage_spill_counts. Aggregate OR masks,
post-seal samples, and missing pre-stage baselines cannot support attribution.
"""
import argparse
import copy
import json
import re
from pathlib import Path

ORDER = ("before_stream", "after_stream", "after_palette", "after_hud", "after_sat")

def evaluate(data):
    errors=[]
    frames=data.get("frames_medidos");total=data.get("vovf_delta")
    if type(frames) is not int or not 1<=frames<=65535: errors.append("invalid sealed frame count")
    if type(total) is not int or not 0<=total<=65535: errors.append("invalid overflow count")
    if data.get("janela_selada") is not True: errors.append("window not sealed")
    if not re.fullmatch(r"[0-9a-f]{64}",str(data.get("rom_sha256",""))): errors.append("ROM hash absent")
    if not data.get("session_id"): errors.append("session absent")
    if data.get("session_rom_sha256")!=data.get("rom_sha256"): errors.append("session ROM mismatch")
    counts=data.get("stage_spill_counts",{})
    values=[counts.get(k) for k in ORDER] if isinstance(counts,dict) else []
    valid=len(values)==len(ORDER) and all(type(v) is int and 0<=v<=65535 for v in values)
    if not valid: errors.append("missing/invalid pre-stage baseline or stage count")
    deltas={}
    if valid:
        if values!=sorted(values): errors.append("non-monotonic counts; attribution unsupported")
        if type(frames) is int and any(v>frames for v in values): errors.append("counts exceed sealed window")
        if values[-1]!=total: errors.append("final stage disagrees with canonical overflow")
        deltas={ORDER[i]:values[i]-values[i-1] for i in range(1,len(ORDER))}
        if data.get("first_crossing_frames_by_stage") is not None and data["first_crossing_frames_by_stage"]!=deltas:
            errors.append("declared crossing deltas disagree")
    return {"ok":not errors,"problems":errors,"baseline_exposed_frames":values[0] if valid else None,
            "first_crossing_frames_by_stage":deltas if not errors else {},
            "claim_ceiling":"declared_boundary_consistency_only",
            "budget_passed":not errors and total==0,
            "limits":"Gate checks declared numeric consistency, not whether ROM counters really froze at the seal. Coordinator must review instrumentation and source/observation binding. Same sealed window and one boolean observation per frame/stage required. No CPU durations, sole root cause, multi-wrap inference, or safe upload rate."}

def fixture():
    return {"frames_medidos":3000,"vovf_delta":442,"janela_selada":True,"rom_sha256":"a"*64,
            "session_rom_sha256":"a"*64,"session_id":"offline-fixture",
            "stage_spill_counts":dict(zip(ORDER,[0,212,212,212,442]))}

def self_check():
    good=fixture(); assert evaluate(good)["ok"] and not evaluate(good)["budget_passed"]
    mutations=[lambda d:d["stage_spill_counts"].pop("before_stream"),
               lambda d:d.update(janela_selada=False),lambda d:d.update(vovf_delta=441),
               lambda d:d["stage_spill_counts"].update(after_hud=100),
               lambda d:d["stage_spill_counts"].update(after_stream=True),
               lambda d:d.update(frames_medidos=100),lambda d:d.update(session_rom_sha256="b"*64),
               lambda d:d.update(first_crossing_frames_by_stage={})]
    for change in mutations:
        bad=copy.deepcopy(good);change(bad);assert not evaluate(bad)["ok"]
    zero=fixture();zero.update(vovf_delta=0,stage_spill_counts=dict.fromkeys(ORDER,0))
    assert evaluate(zero)["budget_passed"]
    print("[SELF-CHECK OK] sealed stage boundaries: baseline, monotonic counts, same ROM/window and claim ceiling")
    return 0

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--report");p.add_argument("--self-check",action="store_true")
    a=p.parse_args()
    if a.self_check:return self_check()
    if not a.report:p.error("--report required")
    try: result=evaluate(json.loads(Path(a.report).read_text()))
    except (ValueError,OSError,AttributeError,TypeError) as e:result={"ok":False,"problems":[str(e)]}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result["ok"] else 1

if __name__=="__main__":raise SystemExit(main())
