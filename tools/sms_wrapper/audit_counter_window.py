#!/usr/bin/env python3
"""Check uniqueness of a wrapping counter delta under a declared event bound.

This checks arithmetic and hashed records, not the truth of the event bound,
the atomicity of the samples or whether the ROM reset its counter.
"""
import argparse
import copy
import json
import tempfile
from pathlib import Path
from audit_subagent_session import check_ref, ref


def evaluate(data, require_exact=False):
    errors=[];details={}
    try:
        if data.get("schema")!="sms_counter_window_v1" or data.get("counter_mode")!="wrapping_monotonic":
            raise ValueError("unsupported counter contract")
        evidence=data.get("evidence")
        if not isinstance(evidence,list) or not evidence:raise ValueError("counter evidence absent")
        for item in evidence:check_ref(item)
        bits=data["bits"];before=data["before"];after=data["after"];bound=data["max_events"]
        if type(bits) is not int or bits not in (8,16,32):raise ValueError("counter bits must be 8, 16 or 32")
        modulus=1<<bits
        if any(type(v) is not int or not 0<=v<modulus for v in (before,after)):raise ValueError("counter sample outside width")
        if data.get("no_reset_in_window") is not True:raise ValueError("no-reset precondition absent")
        delta=(after-before)%modulus
        if bound is not None and (type(bound) is not int or bound<0):raise ValueError("invalid event bound")
        if bound is not None and bound<delta:raise ValueError("event bound contradicts modular delta")
        count=None if bound is None else (bound-delta)//modulus+1
        exact=count==1
        details={"modular_delta":delta,"modulus":modulus,"possible_counts":count,
                 "candidate_counts":"unbounded: delta + k*modulus" if bound is None else
                     {"first":delta,"step":modulus,"last":delta+(count-1)*modulus},
                 "exact_under_declared_bound":exact,"exact_count":delta if exact else None}
        if data.get("claimed_exact_delta") is not None:
            claim=data["claimed_exact_delta"]
            if type(claim) is not int or not exact or claim!=delta:raise ValueError("exact count unsupported or disagrees")
        if require_exact and not exact:raise ValueError("counter window ambiguous; shorter window or wider/saturating instrument required")
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:errors.append(str(e))
    return {"ok":not errors,"problems":errors,"details":details,"claim_ceiling":"declared_counter_arithmetic_only",
            "limits":"Does not authenticate event bound, no-reset assertion, sampling window, source instrumentation or ROM execution. Does not validate event units, opportunities or denominator; no cache hit-rate or exclusive CPU-cost claim. Unbounded/multiwrap counts are not exact."}


def fixture(root):
    p=Path(root)/"counter.json";p.write_text('{"offline_fixture":true}')
    return {"schema":"sms_counter_window_v1","counter_mode":"wrapping_monotonic",
            "bits":8,"before":250,"after":5,"max_events":20,
            "no_reset_in_window":True,"evidence":[ref(p)]}


def self_check():
    with tempfile.TemporaryDirectory() as tmp:
        good=fixture(tmp);assert evaluate(good,True)["details"]["exact_count"]==11
        zero=dict(good,before=5,after=5,max_events=0);assert evaluate(zero,True)["ok"]
        ambiguous=dict(good,before=155,after=184,max_events=358)
        out=evaluate(ambiguous);assert out["ok"] and out["details"]["possible_counts"]==2
        assert not evaluate(ambiguous,True)["ok"]
        for change in ({"claimed_exact_delta":29},{"max_events":None,"claimed_exact_delta":29},
                       {"no_reset_in_window":False},{"before":True},{"bits":True},
                       {"max_events":28},{"counter_mode":"saturating"}):
            bad=copy.deepcopy(ambiguous);bad.update(change);assert not evaluate(bad,True)["ok"]
        for bits in (16,32):
            wide=dict(good,bits=bits,before=(1<<bits)-2,after=3,max_events=10)
            assert evaluate(wide,True)["details"]["exact_count"]==5
    print("[SELF-CHECK OK] counter windows: rollover, ambiguous/unbounded counts, exact bound and invalid samples")
    return 0


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--record");p.add_argument("--require-exact",action="store_true");p.add_argument("--self-check",action="store_true")
    a=p.parse_args()
    if a.self_check:return self_check()
    if not a.record:p.error("--record required")
    try:out=evaluate(json.loads(Path(a.record).read_text()),a.require_exact)
    except (ValueError,OSError,TypeError,AttributeError) as e:out={"ok":False,"problems":[str(e)]}
    print(json.dumps(out,indent=2));return 0 if out["ok"] else 1


if __name__=="__main__":raise SystemExit(main())
