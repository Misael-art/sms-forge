import json

import pytest

import audit_import_semantics
from audit_subagent_session import ref
from mugen2sms.analysis import trace_air_identity as trace


def source_identity():
    durations = [6, 8, 4, 4, 8]
    cumulative = [0]
    for duration in durations:
        cumulative.append(cumulative[-1] + duration)
    return {
        "schema": "mugen2sms.air-source-identity/v1",
        "kind": "air_source_identity",
        "sequence_scope": "one_finite_non_looping_action_pass",
        "counter_bits": 16,
        "source": {
            "package_name": "fixture.zip",
            "package_sha256": "a" * 64,
            "def_path": "fixture.def",
            "air_path": "fixture.air",
            "air_sha256": "b" * 64,
        },
        "action_id": 221,
        "durations": durations,
        "boundary_element_ids": [
            "221:0", "221:1", "221:2", "221:3", "221:4", "221:terminal",
        ],
        "boundary_cumulative_ticks": cumulative,
        "elements": [
            {"element_id": f"221:{index}", "element_index": index,
             "duration": duration}
            for index, duration in enumerate(durations)
        ],
    }


def make_ticks():
    ticks = []
    for tick in range(36):
        if tick < 5 or tick >= 35:
            action, element = 0, 0
        elif tick < 11:
            action, element = 221, 0
        elif tick < 19:
            action, element = 221, 1
        elif tick < 23:
            action, element = 221, 2
        elif tick < 27:
            action, element = 221, 3
        else:
            action, element = 221, 4
        ticks.append({"tick": tick, "p1_air_action": action, "p1_air_element": element,
                      "p2_air_action": 0, "p2_air_element": 0})
    return ticks


def test_decode_trc3_keeps_16_bit_action_and_element_per_slot():
    raw = bytearray(b"TRC3" + bytes([1, 1, 0, 6]))
    raw.extend([0x88, 0x13, 7, 0xDD, 0x00, 2])
    decoded = trace.decode_buffer(bytes(raw), expect_ticks=1)
    assert decoded[0]["p1_air_action"] == 5000
    assert decoded[0]["p1_air_element"] == 7
    assert decoded[0]["p2_air_action"] == 221
    assert decoded[0]["p2_air_element"] == 2


@pytest.mark.parametrize("raw", [
    b"TRC1" + bytes([1, 0, 0, 18]),
    b"TRC3" + bytes([0, 0, 0, 18]),
    b"TRC3" + bytes([1, 0, 0, 12]),
])
def test_decode_trc3_rejects_wrong_magic_incomplete_or_wrong_record_size(raw):
    with pytest.raises(ValueError):
        trace.decode_buffer(raw, expect_ticks=0)


def test_decode_trc3_rejects_truncated_payload():
    raw = b"TRC3" + bytes([1, 1, 0, 6]) + bytes(5)
    with pytest.raises(ValueError, match="truncated"):
        trace.decode_buffer(raw, expect_ticks=1)


def test_decode_trc3_rejects_trailing_payload_and_invalid_window():
    raw = b"TRC3" + bytes([1, 1, 0, 6]) + bytes(6) + b"stale"
    with pytest.raises(ValueError, match="trailing bytes"):
        trace.decode_buffer(raw, expect_ticks=1)
    with pytest.raises(ValueError, match="1..340"):
        trace.decode_buffer(b"", expect_ticks=0)


def test_derives_all_source_boundaries_and_terminal_from_tick_trace():
    result = trace.derive_action_boundaries(make_ticks(), "p1", source_identity())
    assert result["air_boundary_stamps"] == [5, 11, 19, 23, 27, 35]
    assert result["air_boundary_element_ids"] == source_identity()["boundary_element_ids"]
    assert result["observed_durations"] == [6, 8, 4, 4, 8]


def test_derived_boundary_trace_satisfies_identity_audit_contract(tmp_path):
    source_path = tmp_path / "source_air.json"
    source_path.write_text(json.dumps(source_identity()))
    trace_path = tmp_path / "air_trace.json"
    trace_path.write_text(json.dumps(
        trace.derive_action_boundaries(make_ticks(), "p1", source_identity())))
    record = {
        "kind": "air_identity_timing",
        "counter_bits": 16,
        "source_durations": source_identity()["durations"],
        "source_air": ref(source_path),
        "trace": ref(trace_path),
        "evidence": [ref(source_path), ref(trace_path)],
    }
    assert audit_import_semantics.evaluate(record, require_air_identity=True)["ok"]


def test_derivation_rejects_skipped_reordered_interrupted_and_truncated_actions():
    bad = make_ticks()
    bad[11]["p1_air_element"] = 2
    with pytest.raises(ValueError, match="skipped or reordered"):
        trace.derive_action_boundaries(bad, "p1", source_identity())

    bad = make_ticks()
    bad[19]["p1_air_action"] = 0
    bad[20]["p1_air_action"] = 221
    with pytest.raises(ValueError, match="interrupted or repeated"):
        trace.derive_action_boundaries(bad, "p1", source_identity())

    with pytest.raises(ValueError, match="terminal boundary"):
        trace.derive_action_boundaries(make_ticks()[:35], "p1", source_identity())

    bad = make_ticks()
    bad[18]["p1_air_element"] = 2
    with pytest.raises(ValueError, match="durations"):
        trace.derive_action_boundaries(bad, "p1", source_identity())


def test_derivation_rejects_inconsistent_source_manifest_and_trace_rows():
    bad_source = source_identity()
    bad_source["elements"][2]["duration"] = 5
    with pytest.raises(ValueError, match="element 2"):
        trace.derive_action_boundaries(make_ticks(), "p1", bad_source)

    bad_source = source_identity()
    bad_source["source"]["air_sha256"] = "not-a-hash"
    with pytest.raises(ValueError, match="lowercase SHA-256"):
        trace.derive_action_boundaries(make_ticks(), "p1", bad_source)

    bad_rows = make_ticks()
    bad_rows[0] = None
    with pytest.raises(ValueError, match="non-object row"):
        trace.derive_action_boundaries(bad_rows, "p1", source_identity())
