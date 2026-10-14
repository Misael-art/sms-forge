import json

import pytest

import audit_import_semantics
from mugen2sms.analysis.air_source_identity import compile_action_record
from mugen2sms.parsers.air import Action, Frame


def test_duplicate_sprite_elements_keep_distinct_air_identity():
    action = Action(220, [Frame(4, 2, 0, 0, 6), Frame(4, 2, 0, 0, 8)])
    record = compile_action_record(
        220, action, package_name="fixture.zip", package_sha256="a" * 64,
        def_path="fixture.def", air_path="fixture.air", air_sha256="b" * 64)
    assert record["boundary_element_ids"] == ["220:0", "220:1", "220:terminal"]
    assert record["durations"] == [6, 8]
    assert record["elements"][0]["image"] == record["elements"][1]["image"]


def test_rejects_looping_action_and_unbounded_duration():
    action = Action(10, [Frame(0, 0, 0, 0, 6)])
    args = dict(package_name="fixture.zip", package_sha256="a" * 64,
                def_path="fixture.def", air_path="fixture.air", air_sha256="b" * 64)
    with pytest.raises(ValueError, match="loopstart"):
        compile_action_record(10, action, **args, explicit_loopstart=True)
    action.frames[0].time = -1
    with pytest.raises(ValueError, match="durations"):
        compile_action_record(10, action, **args)


def test_manifest_matches_import_semantics_and_rejects_equal_duration_permutation(tmp_path):
    source = tmp_path / "source_air.json"
    trace = tmp_path / "rom_trace.json"
    action = Action(230, [Frame(1, 4, 0, 0, 6), Frame(1, 4, 0, 0, 6)])
    manifest = compile_action_record(
        230, action, package_name="fixture.zip", package_sha256="a" * 64,
        def_path="fixture.def", air_path="fixture.air", air_sha256="b" * 64)
    source.write_text(json.dumps(manifest), encoding="utf-8")
    trace_data = {
        "air_boundary_stamps": [65530, 0, 6],
        "air_boundary_element_ids": ["230:0", "230:1", "230:terminal"],
    }
    trace.write_text(json.dumps(trace_data), encoding="utf-8")
    source_ref = audit_import_semantics.ref(source)
    trace_ref = audit_import_semantics.ref(trace)
    record = {
        "kind": "air_identity_timing",
        "evidence": [source_ref, trace_ref],
        "source_air": source_ref,
        "trace": trace_ref,
        "source_durations": manifest["durations"],
        "counter_bits": 16,
    }
    assert audit_import_semantics.evaluate(record, require_air_identity=True)["ok"]

    trace_data["air_boundary_element_ids"] = ["230:1", "230:0", "230:terminal"]
    trace.write_text(json.dumps(trace_data), encoding="utf-8")
    record["trace"] = audit_import_semantics.ref(trace)
    record["evidence"] = [source_ref, record["trace"]]
    rejected = audit_import_semantics.evaluate(record, require_air_identity=True)
    assert not rejected["ok"]
    assert rejected["problems"] == ["AIR element identity/order differs"]

    trace_data["air_boundary_element_ids"] = ["240:0", "240:1", "240:terminal"]
    trace.write_text(json.dumps(trace_data), encoding="utf-8")
    record["trace"] = audit_import_semantics.ref(trace)
    record["evidence"] = [source_ref, record["trace"]]
    rejected_action = audit_import_semantics.evaluate(record, require_air_identity=True)
    assert not rejected_action["ok"]
    assert rejected_action["problems"] == ["AIR element identity/order differs"]
