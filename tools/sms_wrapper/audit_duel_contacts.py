#!/usr/bin/env python3
"""Compare MFD1 recordings or examine reported poses of both actors at contact."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def number(row, field, maximum=None):
    value = row[field]
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise ValueError(f"invalid {field}: {value!r}")
    return value


def contacts(receipt, stepped):
    """Keep each recorder's native frame coordinate. A replay frame is video-relative."""
    rows = receipt["moves" if stepped else "actual_contacts"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("empty or invalid contact list")
    frame_key, tick_key, pose_key, display_key, hp_key = (
        ("hit_vdp_frame", "hit_tick", "requested_at_hit", "presented_at_hit", "opponent_life")
        if stepped else ("video_frame", "logic_tick", "requested", "presented", "life")
    )
    if stepped:
        first = number(receipt, "first_vdp_frame")
        last = number(receipt, "last_vdp_frame")
    else:
        first = 0
        last = number(receipt["video"], "frames") - 1
    previous_frame, previous_tick = -1, -1
    seen = set()
    result = []
    for row in rows:
        player = row["player"]
        frame, tick = number(row, frame_key), number(row, tick_key)
        if player not in ("p1", "p2") or not first <= frame <= last:
            raise ValueError("contact actor or frame outside recording")
        if frame < previous_frame or tick < previous_tick:
            raise ValueError("unordered contacts or wrapped clock outside this round profile")
        if (player, tick) in seen:
            raise ValueError("repeated contact for one attacker on the same logic tick")
        seen.add((player, tick))
        previous_frame, previous_tick = frame, tick
        event = {"player": player, frame_key: frame, "logic_tick": tick,
                 "requested": number(row, pose_key, 255), "presented": number(row, display_key, 255),
                 "opponent_life": number(row, hp_key, 255)}
        if stepped:
            if number(row, "opponent_life_before", 255) <= event["opponent_life"]:
                raise ValueError("stepped contact has no damage")
        else:
            event["resident"] = number(row, "resident", 255)
        result.append(event)
    return result


def compare(stepped, replay, rom_sha):
    if not re.fullmatch(r"[0-9a-f]{64}", rom_sha):
        raise ValueError("expected lowercase ROM SHA-256")
    for receipt in (stepped, replay):
        if receipt["rom_sha256"] != rom_sha:
            raise ValueError("receipt belongs to another ROM")
        if not isinstance(receipt["session_id"], str) or not receipt["session_id"].strip():
            raise ValueError("missing session identity")
    if replay["source_session"] != stepped["session_id"] or replay["session_id"] == stepped["session_id"]:
        raise ValueError("replay must refer to the stepped run from a different session")
    ordered = contacts(stepped, True)
    repeated = contacts(replay, False)

    def signature(event):
        return (event["player"], event["requested"], event["opponent_life"])

    first_difference = None
    for index, (left, right) in enumerate(zip(ordered, repeated), 1):
        if signature(left) != signature(right):
            first_difference = index
            break
    if first_difference is None and len(ordered) != len(repeated):
        first_difference = min(len(ordered), len(repeated)) + 1
    sequence_matches = first_difference is None
    divergences = []
    for mode, events, other in (("stepped", ordered, repeated), ("continuous", repeated, ordered)):
        for index, event in enumerate(events, 1):
            if event["requested"] != event["presented"]:
                mismatch = {"recording": mode, "ordinal": index, **event}
                if sequence_matches:
                    mismatch["other_recording_contact"] = other[index - 1]
                divergences.append(mismatch)
    return {
        "ok": sequence_matches and not divergences,
        "scope": "Reported damaging contacts and requested/presented pose IDs only",
        "rom_sha256": rom_sha, "stepped_session": stepped["session_id"],
        "continuous_session": replay["session_id"],
        "counts": {"stepped": len(ordered), "continuous": len(repeated)},
        "ordered_contacts_match": sequence_matches,
        "pose_divergences": divergences,
        "first_sequence_difference": first_difference,
    }


def compare_actor_poses(matrix, scenario, rom_sha):
    if not re.fullmatch(r"[0-9a-f]{64}", rom_sha) or matrix["rom_sha256"] != rom_sha:
        raise ValueError("invalid ROM identity or matrix from another ROM")
    matches = [row for row in matrix["scenarios"] if row["folder"] == scenario]
    if len(matches) != 1:
        raise ValueError("expected exactly one matching scenario")
    run = matches[0]
    if not isinstance(run["session_id"], str) or not run["session_id"].strip():
        raise ValueError("missing stepped session")
    if not isinstance(run["contacts"], list) or not run["contacts"]:
        raise ValueError("expected a non-empty list of contacts")
    divergences = []
    seen = set()
    for event in run["contacts"]:
        identity = (number(event, "vdp_frame"), event["actor"])
        if identity[1] not in ("p1", "p2") or identity in seen:
            raise ValueError("invalid or duplicate actor at frame")
        seen.add(identity)
        tick = number(event, "logic_tick")
        for role, length in (("attacker", 3), ("victim", 2)):
            poses = event[role + "_pose"]
            if (not isinstance(poses, list) or len(poses) != length or
                    any(type(p) is not int or not 0 <= p <= 255 for p in poses) or poses[0] == 255):
                raise ValueError(f"invalid {role} pose tuple")
            if any(p != poses[0] for p in poses[1:]):
                divergences.append({"actor": event["actor"], "role": role, "case": event["case"],
                                    "logic_tick": tick, "vdp_frame": identity[0], "poses": poses})
    return {"ok": not divergences, "rom_sha256": rom_sha, "session_id": run["session_id"],
            "scenario": scenario, "contacts": len(seen), "pose_divergences": divergences,
            "scope": "Reported pose IDs at contact only, attacker requested/resident/presented, "
                     "victim requested/presented. No framebuffer, completeness or timing verdict."}


def fixture():
    sha = "a" * 64
    stepped = {"rom_sha256": sha, "session_id": "one", "first_vdp_frame": 100,
               "last_vdp_frame": 114, "moves": [{"player": "p1", "hit_vdp_frame": 112,
               "hit_tick": 7, "requested_at_hit": 8, "presented_at_hit": 8,
               "opponent_life_before": 100, "opponent_life": 94}]}
    replay = {"rom_sha256": sha, "session_id": "two", "source_session": "one",
              "video": {"frames": 15}, "actual_contacts": [{"player": "p1", "video_frame": 10,
              "logic_tick": 6, "requested": 8, "resident": 8, "presented": 8, "life": 94}]}
    return stepped, replay, sha


def self_check():
    stepped, replay, sha = fixture()
    assert compare(stepped, replay, sha)["ok"]
    replay["same_contacts"] = True
    replay["actual_contacts"][0]["presented"] = 7
    result = compare(stepped, replay, sha)
    assert not result["ok"] and result["ordered_contacts_match"]
    assert result["pose_divergences"][0]["recording"] == "continuous"
    replay["actual_contacts"][0].update(presented=8, life=93)
    assert compare(stepped, replay, sha)["first_sequence_difference"] == 1
    for field, value in (("rom_sha256", "b" * 64), ("source_session", "other"),
                         ("session_id", "one"), ("actual_contacts", [])):
        try:
            compare(stepped, {**replay, field: value}, sha)
        except ValueError:
            continue
        raise AssertionError(field)
    event = {"actor": "p1", "case": "air", "logic_tick": 2, "vdp_frame": 3,
             "attacker_pose": [46, 46, 46], "victim_pose": [63, 63]}
    matrix = {"rom_sha256": sha, "scenarios": [{"folder": "test", "session_id": "one",
                                                "contacts": [event]}]}
    assert compare_actor_poses(matrix, "test", sha)["ok"]
    event["victim_pose"][1] = 9
    assert compare_actor_poses(matrix, "test", sha)["pose_divergences"][0]["role"] == "victim"
    print("[SELF-CHECK OK] MFD1 paired receipts and actor pose matrix")


def load_receipt(path):
    data = path.read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--stepped", type=Path)
    parser.add_argument("--continuous", type=Path)
    parser.add_argument("--actor-matrix", type=Path, help="Scene 02 report_alis_mirror matrix")
    parser.add_argument("--scenario", help="exact folder name in actor matrix")
    parser.add_argument("--rom-sha256")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    if args.actor_matrix or args.scenario:
        if not all((args.actor_matrix, args.scenario, args.rom_sha256)) or args.stepped or args.continuous:
            parser.error("matrix mode requires --actor-matrix, --scenario and --rom-sha256 only")
    elif not all((args.stepped, args.continuous, args.rom_sha256)):
        parser.error("--stepped, --continuous and --rom-sha256 required")
    try:
        if args.actor_matrix:
            matrix, matrix_sha = load_receipt(args.actor_matrix)
            result = compare_actor_poses(matrix, args.scenario, args.rom_sha256)
            result["receipt_sha256"] = {"actor_matrix": matrix_sha}
        else:
            stepped, stepped_sha = load_receipt(args.stepped)
            replay, replay_sha = load_receipt(args.continuous)
            result = compare(stepped, replay, args.rom_sha256)
            result["receipt_sha256"] = {"stepped": stepped_sha, "continuous": replay_sha}
    except (OSError, KeyError, TypeError, ValueError) as exc:
        result = {"ok": False, "invalid_input": str(exc)}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
