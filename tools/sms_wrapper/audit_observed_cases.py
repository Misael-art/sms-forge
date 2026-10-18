#!/usr/bin/env python3
"""Recompute assertions and observed VDP deadlines from hash-bound RAM journals.

Profile journal_ram_v1 only: RAM values and ACK frame intervals. No claim of
first-event latency, visible pose, wall-clock FPS, tool authenticity or cleanup.
Use audit_subagent_session for session QA and native visual review for pixels.
"""
import argparse
import copy
import json
import tempfile
import hashlib
from pathlib import Path

from audit_subagent_session import check_ref, ref
from report_output import write_new_report

OPERATIONS = {"status", "pause", "run", "audio-enable", "audio-disable", "input",
              "step", "sequence", "read", "sram", "capture", "video", "close"}


def integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError("invalid integer: " + label)
    return value


def evaluate(data):
    errors, results, points, inputs = [], [], {}, {}
    try:
        if data.get("profile") != "journal_ram_v1":
            raise ValueError("unsupported observed-case profile")
        rom = check_ref(data["rom"])
        session = json.loads(check_ref(data["session"]).read_text())
        if session["rom_sha256"] != ref(rom)["sha256"]:
            raise ValueError("session/ROM hash differs")
        sid = session["session_id"]
        if not isinstance(sid, str) or not sid.strip():
            raise ValueError("session identity absent")
        pid = integer(session["emulator_process"]["pid"], "emulator PID", 1)
        check_ref(data["layout_source"])
        inputs = {name: data[name] for name in ("rom", "session", "journal", "layout_source")}
        journal = [json.loads(line) for line in check_ref(data["journal"]).read_text().splitlines()]
        if not journal:
            raise ValueError("empty journal")
        by_seq, last_seq, last_frame = {}, -1, -1
        for row in journal:
            if row["operation"] not in OPERATIONS:
                raise ValueError("operation outside supported read-only session protocol")
            ack = row["ack"]
            seq = integer(ack["seq"], "ACK sequence")
            frame = integer(ack["frame"], "unwrapped VDP frame")
            ack_pid = integer(ack["pid"], "ACK PID", 1)
            if ack.get("ok") is not True or ack.get("session_id") != sid or ack_pid != pid:
                raise ValueError("ACK status/session/PID differs")
            if seq <= last_seq or frame < last_frame:
                raise ValueError("journal sequence/frame is not ordered")
            last_seq, last_frame = seq, frame
            if row["operation"] == "read":
                address, length = row["args"]
                integer(address, "read address")
                integer(length, "read length", 1)
                ram = ack["ram"]
                if not 0xC000 <= address < 0xE000 or length > 256 or address + length > 0xE000 or not isinstance(ram, list) or len(ram) != length:
                    raise ValueError("read block length/address differs")
                if any(type(v) is not int or not 0 <= v <= 255 for v in ram):
                    raise ValueError("invalid RAM byte")
            if row["operation"] == "input":
                masks = row["args"]
                if not isinstance(masks, list) or len(masks) != 3:
                    raise ValueError("input ACK lacks three explicit control masks")
                for key, value, maximum in zip(("p1", "p2", "console"), masks, (63, 63, 3)):
                    integer(value, "input mask")
                    if value > maximum or type(ack.get(key)) is not int or ack[key] != value:
                        raise ValueError("input mask differs from ACK: " + key)
            by_seq[seq] = row
        fields = data["fields"]
        if not isinstance(fields, dict) or not fields:
            raise ValueError("field layout absent")
        for name, field in fields.items():
            integer(field["address"], name + " address")
            if type(field["width"]) is not int or field["width"] not in (1, 2):
                raise ValueError("only u8/u16/s8/s16 fields supported")
            if type(field.get("signed", False)) is not bool or not 0xC000 <= field["address"] < 0xE000 or field["address"] + field["width"] > 0xE000:
                raise ValueError("invalid field domain")
        for name, point in data["points"].items():
            seqs = point["seqs"]
            if not isinstance(seqs, list) or not seqs or any(type(s) is not int for s in seqs):
                raise ValueError("point needs explicit ACK sequences")
            if seqs != sorted(set(seqs)):
                raise ValueError("point sequences duplicate or unordered")
            rows = [by_seq[s] for s in seqs]
            frames = {r["ack"]["frame"] for r in rows}
            if len(frames) != 1:
                raise ValueError("point combines different VDP frames")
            anchor = point.get("anchor", "read")
            if anchor == "input":
                if len(rows) != 1 or rows[0]["operation"] != "input":
                    raise ValueError("input anchor needs actual input ACK")
                points[name] = {"frame": rows[0]["ack"]["frame"], "seqs": seqs, "values": {}, "anchor": anchor}
                continue
            if anchor != "read" or any(r["operation"] != "read" for r in rows):
                raise ValueError("only RAM read points or input anchors supported")
            if any(r["operation"] != "read" for seq, r in by_seq.items() if seqs[0] <= seq <= seqs[-1]):
                raise ValueError("executing/input operation between point reads")
            values = {}
            for field_name, field in fields.items():
                candidates = []
                for row in rows:
                    address, length = row["args"]
                    offset = field["address"] - address
                    if 0 <= offset and offset + field["width"] <= length:
                        candidates.append(int.from_bytes(bytes(row["ack"]["ram"][offset:offset + field["width"]]),
                                                         "little", signed=field.get("signed", False)))
                if candidates:
                    if len(set(candidates)) != 1:
                        raise ValueError("conflicting reads within point: " + field_name)
                    values[field_name] = candidates[0]
            if not values:
                raise ValueError("point measures no declared field")
            points[name] = {"frame": rows[0]["ack"]["frame"], "seqs": seqs, "values": values, "anchor": anchor}
        cases = data["cases"]
        if not isinstance(cases, list) or not cases:
            raise ValueError("cases absent")
        ids = set()
        for case in cases:
            cid = case["id"]
            if not isinstance(cid, str) or not cid.strip() or cid in ids:
                raise ValueError("case ID absent/duplicate")
            ids.add(cid)
            conditions = case["conditions"]
            if not isinstance(conditions, list) or not conditions:
                raise ValueError("case conditions absent")
            checks, ram_checks = [], 0
            for condition in conditions:
                op = condition["op"]
                if op in ("eq", "field_eq"):
                    point = points[condition["point"]]
                    actual = point["values"][condition["field"]]
                    if op == "field_eq":
                        expected = point["values"][condition["other_field"]]
                    else:
                        expected = condition["value"]
                        if type(expected) is not int:
                            raise ValueError("RAM equality requires integer expectation")
                    ram_checks += 1
                    passed = actual == expected
                elif op in ("delta_eq", "vdp_deadline"):
                    start, end = points[condition["from"]], points[condition["to"]]
                    if start["seqs"][-1] >= end["seqs"][0] or start["frame"] > end["frame"]:
                        raise ValueError("case interval reversed or overlapping")
                    if op == "delta_eq":
                        field = condition["field"]
                        actual = end["values"][field] - start["values"][field]
                        expected = condition["value"]
                        if type(expected) is not int:
                            raise ValueError("RAM delta requires integer expectation")
                        passed = actual == expected
                        ram_checks += 1
                    else:
                        if start["anchor"] != "input":
                            raise ValueError("deadline must start at actual input ACK")
                        end_name = condition["to"]
                        if end["anchor"] != "read" or not any(
                                c.get("op") in ("eq", "field_eq") and c.get("point") == end_name
                                or c.get("op") == "delta_eq" and c.get("to") == end_name
                                for c in conditions):
                            raise ValueError("deadline endpoint needs its own ROM assertion")
                        actual = end["frame"] - start["frame"]
                        expected = integer(condition["max_vdp_frames"], "observed deadline")
                        passed = actual <= expected
                else:
                    raise ValueError("unsupported condition: " + str(op))
                checks.append({"condition": condition, "actual": actual, "expected": expected, "passed": passed})
            if not ram_checks:
                raise ValueError("case has no RAM assertion")
            passed = all(c["passed"] for c in checks)
            results.append({"id": cid, "passed": passed, "checks": checks})
            if not passed:
                errors.append("observations disagree with case: " + cid)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, OverflowError) as exc:
        errors.append(str(exc))
    return {"schema": "sms_observed_case_audit_v1", "ok": not errors, "problems": errors, "cases": results,
            "inputs": inputs, "points": points,
            "claim_ceiling": "journal_RAM_assertions_and_observed_VDP_intervals_only",
            "limits": "Layout meaning, probe accuracy and journal authenticity require independent review. "
                      "No framebuffer/presented-pixel proof, first-occurrence latency, FPS, counter-wrap disambiguation or cleanup approval. "
                      "A missed sampled deadline does not establish when an unsampled event first occurred. "
                      "Zero net endpoint delta does not prove absence of intermediate damage/healing."}


def fixture(root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    rom = root / "rom.sms"; rom.write_bytes(b"offline fixture, not a playable ROM")
    layout = root / "layout.json"; layout.write_text('{"fixture":true}')
    session = root / "session.json"
    session.write_text(json.dumps({"session_id": "fixture", "rom_sha256": ref(rom)["sha256"], "emulator_process": {"pid": 42}}))
    rows = []
    for seq, frame, operation, ram in [(1, 100, "read", [50, 0, 7, 7]), (2, 101, "input", None), (3, 106, "read", [43, 0, 7, 7])]:
        ack = dict(ok=True, session_id="fixture", pid=42, seq=seq, frame=frame)
        if ram is not None: ack["ram"] = ram
        else: ack.update(p1=16, p2=0, console=0)
        rows.append({"operation": operation, "args": [0xC000, 4] if ram is not None else [16, 0, 0], "ack": ack})
    journal = root / "commands.jsonl"; journal.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    return {"profile": "journal_ram_v1", "rom": ref(rom), "session": ref(session), "journal": ref(journal), "layout_source": ref(layout),
            "fields": {"hp": {"address": 0xC000, "width": 2}, "logical": {"address": 0xC002, "width": 1}, "submitted": {"address": 0xC003, "width": 1}},
            "points": {"before": {"seqs": [1]}, "input": {"seqs": [2], "anchor": "input"}, "after": {"seqs": [3]}},
            "cases": [{"id": "hit", "conditions": [{"op": "eq", "point": "before", "field": "hp", "value": 50},
                       {"op": "delta_eq", "from": "before", "to": "after", "field": "hp", "value": -7},
                       {"op": "field_eq", "point": "after", "field": "logical", "other_field": "submitted"},
                       {"op": "vdp_deadline", "from": "input", "to": "after", "max_vdp_frames": 5}]}]}


def self_check():
    with tempfile.TemporaryDirectory() as tmp:
        good = fixture(Path(tmp) / "good"); assert evaluate(good)["ok"]
        for change in ("whiff", "deadline", "not_input", "no_cases", "bool", "stale_hash", "wrong_pid", "duplicate_seq", "unsubmitted", "different_frames", "execution_between_reads", "conflicting_reads", "memory_write", "empty_input", "wrong_input_ack", "bool_pid", "unasserted_endpoint", "outside_ram", "unknown_op"):
            bad = copy.deepcopy(good)
            if change == "whiff": bad["cases"][0]["conditions"][1]["value"] = 0
            elif change == "deadline": bad["cases"][0]["conditions"][-1]["max_vdp_frames"] = 4
            elif change == "not_input": bad["cases"][0]["conditions"][-1]["from"] = "before"
            elif change == "no_cases": bad["cases"] = []
            elif change == "bool": bad["fields"]["hp"]["width"] = True
            elif change == "stale_hash": bad["journal"]["sha256"] = "0" * 64
            elif change == "unasserted_endpoint":
                bad["cases"][0]["conditions"] = [bad["cases"][0]["conditions"][0], bad["cases"][0]["conditions"][-1]]
            else:
                rows = [json.loads(line) for line in Path(good["journal"]["path"]).read_text().splitlines()]
                if change == "wrong_pid": rows[-1]["ack"]["pid"] = 43
                elif change == "memory_write": rows[-1]["operation"] = "poke"
                elif change == "empty_input": rows[1]["args"] = []
                elif change == "wrong_input_ack": rows[1]["ack"]["p1"] = 0
                elif change == "bool_pid":
                    metadata = json.loads(Path(good["session"]["path"]).read_text())
                    metadata["emulator_process"]["pid"] = 1
                    path = Path(tmp) / "pid_one_session.json"; path.write_text(json.dumps(metadata))
                    bad["session"] = ref(path)
                    for row in rows: row["ack"]["pid"] = 1
                    rows[-1]["ack"]["pid"] = True
                elif change == "outside_ram": rows[-1]["args"][0] = 0
                elif change == "unknown_op": rows[-1]["operation"] = "load_state"
                elif change == "duplicate_seq": rows[-1]["ack"]["seq"] = 1
                elif change == "unsubmitted": rows[-1]["ack"]["ram"][3] = 6
                elif change in ("different_frames", "execution_between_reads", "conflicting_reads"):
                    extra = copy.deepcopy(rows[-1]); extra["ack"]["seq"] = 4
                    if change == "different_frames": extra["ack"]["frame"] += 1
                    if change == "execution_between_reads":
                        rows[-1]["operation"] = "step"; rows[-1]["args"] = [1]
                    if change == "conflicting_reads": extra["ack"]["ram"][0] += 1
                    rows.append(extra); bad["points"]["after"]["seqs"] = [3, 4]
                path = Path(tmp) / (change + ".jsonl")
                path.write_text("\n".join(json.dumps(row) for row in rows))
                bad["journal"] = ref(path)
            assert not evaluate(bad)["ok"], change
    print("[SELF-CHECK OK] observed cases: RAM assertions, input ACK deadlines, identity, atomic points and negatives")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record")
    parser.add_argument("--report-out", help="new destination; existing files are refused")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check: return self_check()
    if not args.record: parser.error("--record required")
    try:
        payload = Path(args.record).read_bytes()
        result = evaluate(json.loads(payload))
        result["record"] = {"path": str(Path(args.record).resolve()), "sha256": hashlib.sha256(payload).hexdigest()}
        if args.report_out: write_new_report(args.report_out, result)
    except (ValueError, OSError) as exc:
        print(json.dumps({"ok": False, "problems": [str(exc)]})); return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
