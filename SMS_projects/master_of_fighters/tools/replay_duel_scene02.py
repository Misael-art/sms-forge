"""Replay one Scene 02 case on a fresh, paused Emulicious session."""

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

from duel_probe import RECORD_BYTES, decode


ROOT = Path(__file__).resolve().parents[3]
DOWN, LEFT, RIGHT, ONE = 2, 4, 8, 16
ALIS_CASES = ("alis_hit_edge", "alis_miss_edge", "alis_miss_punish", "alis_guard_counter",
              "alis_wrong_guard", "alis_buttons")
CASES = ("hit_near", "hit_edge", "whiff_punish", "guard", "guard_counter", "corner_counter", *ALIS_CASES)


def alis_exchange(case, hold, h_player, a_player, step, walk, samples, expected, observed):
    """Exercise the standing repertoire, whose probe reports global art IDs."""
    baseline = samples[-1]
    hx = baseline[h_player]["pivot"][0]
    ax = baseline[a_player]["pivot"][0]
    right = ax > hx
    edge_cases = {"alis_hit_edge": 66, "alis_miss_edge": 67, "alis_miss_punish": 67}
    gap = edge_cases.get(case, 28)
    target_x = hx + gap * (1 if right else -1)
    walk("alis_walk_into_range", abs(target_x - ax), a_keys=RIGHT if target_x > ax else LEFT)
    ready = step("setup_released")
    if (ready[a_player]["pivot"][0], ready[h_player]["pivot"][0]) != (target_x, hx):
        raise AssertionError("Alis did not stop at the declared distance")
    if any(not ready[player]["can_act"] or ready[player]["keys_consumed"] for player in (h_player, a_player)):
        raise AssertionError("The exchange did not begin from released standing guard")

    if case == "alis_buttons":
        expected["starts"] = [20, 17, 17]
        # Leave the held button down past recovery before releasing it.
        observed["consumed_readings"] = []
        for count in (hold - 1, hold, hold + 23):
            first = len(samples)
            for _ in range(count):
                step("button_1_held", a_keys=ONE)
            for _ in range(24):
                step("button_1_released")
            segment = samples[first:]
            started = next((index for index, row in enumerate(segment) if row[a_player]["state"] == 1), None)
            if started is None:
                raise AssertionError("Button 1 did not rearm for the next attack")
            observed["consumed_readings"].append(sum(
                row[a_player]["keys_consumed"] == ONE for row in segment[:started + 1]))
        observed["starts"] = [row[a_player]["pose_requested"] for row in samples
                              if row[a_player]["state"] == 1 and row[a_player]["action_tick"] == 0]
        expected["consumed_readings"] = [hold - 1, hold, hold]
        if observed != expected:
            raise AssertionError(f"Expected touch and two separate holds: {expected}, observed {observed}")
        return

    guarded = case == "alis_guard_counter"
    punished = case == "alis_miss_punish"
    missed = case == "alis_miss_edge" or punished
    expected.update(gap_px=gap, contact=3 if missed else (2 if guarded else 1),
                    contact_age=6 if missed else 5, contact_pose=18, local_pose_for_contact=2,
                    hayato_life=100 if missed or guarded else 90,
                    hayato_free_age=0 if missed else (8 if guarded else 13),
                    alis_free_age=25 if punished else (21 if guarded else 18),
                    counter_contact_age=17 if punished else (13 if guarded else None),
                    alis_life=84 if punished else (94 if guarded else 100))
    if punished:
        expected["hayato_free_after_punish_age"] = 37
        expected["hayato_punish_poses"] = [2, 46, 46, 46]
    if guarded:
        expected["hayato_punish_poses"] = [2, 8, 8, 8]
    step("alis_press_prime", a_keys=ONE)
    for reading in range(1, hold + 1):
        start = step(f"alis_press_{reading}", a_keys=ONE if reading < hold else 0)
        if reading < hold and start[a_player]["state"] != 0:
            raise AssertionError("Alis attacked before reaching the hold threshold")
    if start[a_player]["state"] != 1 or start[a_player]["action_tick"] or start[a_player]["pose_requested"] != 17:
        raise AssertionError("Button 1 alone did not start the standing sword thrust on the threshold")

    exchange = [start]
    for age in range(1, 40 if punished else 26):
        h_back = LEFT if right else RIGHT
        a_back = RIGHT if right else LEFT
        h_keys = 0
        if punished:
            h_keys = DOWN if age == 5 else a_back | ONE if age == 6 else 0
        elif guarded:
            h_keys = h_back if age == 4 else ONE if age == 7 else 0
        elif case == "alis_wrong_guard" and age == 4:
            h_keys = RIGHT if right else LEFT
        elif not missed and age in (11, 12):
            h_keys = h_back
        free = expected["alis_free_age"]
        a_keys = a_back if age in (free - 2, free - 1) else 0
        label = {4: "before_active", 5: "first_active", 6: "last_active", 7: "first_recovery",
                 18: "normal_recovery_end", 21: "end_of_counter_hitstun"}.get(age, "exchange")
        if (guarded and age == 14) or (punished and age == 18):
            label = "after_hayato_counter"
        exchange.append(step(label, h_keys=h_keys, a_keys=a_keys))
    results = [(age, row) for age, row in enumerate(exchange) if row[a_player]["contact"]]
    if len(results) != 1:
        raise AssertionError(f"Expected one thrust result, got {len(results)}")
    contact_age, event = results[0]
    attack, target = event[a_player], event[h_player]
    active_ages = [age for age, row in enumerate(exchange) if row[a_player]["boxes"]["attack"]]
    if active_ages != ([5, 6] if missed else [5]):
        raise AssertionError(f"Alis exposed her strike box on the wrong ticks: {active_ages}")
    recoil = (hx - target["pivot"][0]) * (1 if right else -1)
    target_state = 0 if missed else (2 if guarded else 3)
    if target["state"] != target_state or recoil != (0 if missed else (3 if guarded else 4)):
        raise AssertionError(f"Hayato reaction or knockback differs: state={target['state']}, px={recoil}")
    counter = [(age, row) for age, row in enumerate(exchange) if row[h_player]["contact"]]
    if (guarded or punished) and (len(counter) != 1 or counter[0][1][h_player]["contact"] != 1):
        raise AssertionError("Hayato did not land exactly one punish")
    if not (guarded or punished) and counter:
        raise AssertionError("Hayato attacked in an unopposed reach test")
    for player, age, displacement in ((a_player, expected["alis_free_age"], 1 if right else -1),
                                      (h_player, expected["hayato_free_age"], -1 if right else 1)):
        if player == h_player and (guarded or missed):
            continue
        x_locked, x_before, x_free = (row[player]["pivot"][0] for row in exchange[age - 2:age + 1])
        if (x_before - x_locked, x_free - x_before) != (0, displacement):
            raise AssertionError(f"{player}: movement did not resume on the first free tick")
    attack_box, hurt_box = attack["boxes"]["attack"], target["boxes"]["hurt"]
    overlap = min(attack_box["right"], hurt_box["right"]) - max(attack_box["left"], hurt_box["left"])
    if case in edge_cases and overlap != (0 if missed else 1):
        raise AssertionError(f"The half-open boxes overlapped by {overlap} px at the reach boundary")
    observed.update(
        gap_px=gap, contact=attack["contact"], contact_age=contact_age,
        contact_pose=attack["pose_presented"], local_pose_for_contact=attack["pose_used_for_contact"],
        hayato_life=target["life"], alis_life=exchange[-1][a_player]["life"],
        hayato_free_age=0 if missed else next(
            age for age, row in enumerate(exchange[contact_age:], contact_age)
            if row[h_player]["can_act"] or (guarded and row[h_player]["pose_requested"] == 7)),
        alis_free_age=next(age for age, row in enumerate(exchange) if row[a_player]["can_act"]),
        counter_contact_age=counter[0][0] if counter else None)
    observed["contact_pose_requested"] = attack["pose_requested"]
    observed["contact_pose_resident"] = attack["pose_resident"]
    observed["active_ages"] = active_ages
    observed["hayato_recoil_px"] = recoil
    observed["horizontal_overlap_px"] = overlap
    observed["contact_vdp_frame"] = event["vdp_frame"]
    observed["contact_logic_tick"] = event["logic_tick"]
    observed["contact_boundary_images"] = [
        {"logic_tick": row["logic_tick"], "vdp_frame": row["vdp_frame"], **row["framebuffer"]}
        for row in exchange[contact_age - 1:contact_age + 2] if "framebuffer" in row]
    observed["first_alis_free_tick"] = exchange[observed["alis_free_age"]]["logic_tick"]
    observed["first_hayato_free_tick"] = exchange[observed["hayato_free_age"]]["logic_tick"]
    if punished:
        observed["hayato_free_after_punish_age"] = next(
            age for age, row in enumerate(exchange[17:], 17) if row[h_player]["can_act"])
    if counter:
        response_age, response_sample = counter[0]
        response = response_sample[h_player]
        observed["hayato_punish_vdp_frame"] = response_sample["vdp_frame"]
        observed["hayato_punish_following_vdp_frame"] = exchange[response_age + 1]["vdp_frame"]
        observed["hayato_punish_poses"] = [
            response["pose_used_for_contact"], response["pose_requested"],
            response["pose_resident"], response["pose_presented"]]
    mismatches = {key: [value, observed[key]] for key, value in expected.items() if value != observed[key]}
    if mismatches:
        raise AssertionError(f"Alis thrust mismatch (expected, observed): {mismatches}")


def replay(session, sha, hold, case, output, capture_events=False, render_range=None):
    sys.path.insert(0, str(ROOT / "tools/sms_wrapper"))
    from session_bridge import isolated

    workspace, metadata = isolated.load(session)
    if metadata["rom_sha256"] != sha:
        raise ValueError("Session ROM SHA differs from the case ROM SHA")
    samples = []
    pending_input = (0, 0)

    def snapshot(label):
        if samples:
            previous = samples[-1]
        else:
            initial = isolated.request(workspace, "read", 0xC770, RECORD_BYTES)
            previous = decode(bytes(initial["ram"]))
        stamp = (previous["stamp"] + 2) & 0xFF
        vdp_budget = 8 if case in ALIS_CASES else 3
        phase = isolated.request(workspace, "sample-commit", 0xC774, stamp, vdp_budget)
        read = isolated.request(workspace, "read", 0xC770, RECORD_BYTES)
        raw = bytes(read["ram"])
        record = decode(raw)
        if read["frame"] != phase["frame"] or record["stamp"] != stamp:
            raise ValueError("The MFD1 publication changed after the commit boundary")
        if record["logic_tick"] != ((previous["logic_tick"] + 1) & 0xFFFF):
            raise ValueError("The ROM did not publish one game tick at the next VDP boundary")
        sample = {"label": label, "vdp_frame": read["frame"], "cycles_since_previous_commit": phase["cycles_advanced"],
                  "raw_hex": raw.hex(), **record}
        if render_range is not None:
            render = isolated.request(workspace, "read", *render_range)
            if render["frame"] != read["frame"]:
                raise ValueError("Renderer state and MFD1 commit are from different VDP frames")
            sample["renderer_ram_hex"] = bytes(render["ram"]).hex()
        if samples and phase["start_frame"] != samples[-1]["vdp_frame"]:
            raise ValueError("The emulator advanced between replay samples")
        samples.append(sample)
        if capture_events and (label in ("setup_released", "before_active", "first_active",
                                         "last_active", "first_recovery", "normal_recovery_end",
                                         "end_of_counter_hitstun", "after_hayato_counter") or any(
            sample[slot]["contact"] for slot in ("p1", "p2")
        )):
            name = f"{output.stem}-{sample['vdp_frame']}.png"
            try:
                frame = isolated.capture(workspace, name)
                if frame["frame"] != sample["vdp_frame"]:
                    raise ValueError("Captured framebuffer and sampled RAM are from different VDP frames")
                shutil.copy2(frame["path"], output.parent / name)
                sample["framebuffer"] = {"file": name, "sha256": frame["sha256"]}
            except (OSError, RuntimeError, ValueError, ImportError) as error:
                sample["framebuffer_error"] = str(error)
        return sample

    def step(label, h_keys=0, a_keys=0):
        nonlocal pending_input
        p1, p2 = (h_keys, a_keys) if h_player == "p1" else (a_keys, h_keys)
        isolated.request(workspace, "input", p1, p2, 0)
        sample = snapshot(label)
        consumed = (sample[h_player]["keys_consumed"], sample[a_player]["keys_consumed"])
        sample["input_requested_for_next_tick"] = {"hayato": h_keys, "alis": a_keys}
        if consumed != pending_input:
            raise ValueError(f"{label}: ROM consumed {consumed}, expected previous input {pending_input}")
        pending_input = (h_keys, a_keys)
        return sample

    def walk(label, distance, h_keys=0, a_keys=0):
        if distance:
            step(label + "_prime", h_keys, a_keys)
            for _ in range(distance - 1):
                step(label, h_keys, a_keys)
            step(label)

    verdict = "collection_incomplete"
    expected = {}
    observed = {}
    with output.open("x", encoding="utf-8") as file:
        try:
            baseline = snapshot("baseline")
            fighters = {baseline[player]["fighter"]: player for player in ("p1", "p2")}
            if set(fighters) != {0, 1}:
                raise ValueError("Unexpected fighter identities")
            h_player, a_player = fighters[0], fighters[1]
            h, a = baseline[h_player], baseline[a_player]
            if any(f["state"] or f["life"] != 100 or f["keys_consumed"] for f in (h, a)):
                raise ValueError("Start on a fresh released guard with both life bars full")
            if case in ALIS_CASES:
                alis_exchange(case, hold, h_player, a_player, step, walk, samples, expected, observed)
                verdict = ("stepped_semantics_passed" if all(
                    newer["vdp_frame"] == older["vdp_frame"] + 1
                    for older, newer in zip(samples, samples[1:])
                ) else "stepped_semantics_observed_pacing_failed")
                return verdict
            hx, ax = h["pivot"][0], a["pivot"][0]
            direction = 1 if h["facing_right"] else -1
            guard_key = RIGHT if direction > 0 else LEFT
            target_gap = {"hit_edge": 37, "whiff_punish": 38}.get(case, 33)
            is_guard = case in ("guard", "guard_counter", "corner_counter")
            wants_counter = case in ("whiff_punish", "guard_counter", "corner_counter")
            is_miss = case == "whiff_punish"
            if case == "corner_counter":
                wall = 192 if direction > 0 else 63
                walk("walk_alis_to_wall", abs(wall - ax), a_keys=guard_key)
                ax = samples[-1][a_player]["pivot"][0]
                if ax != wall:
                    raise ValueError("Alis did not reach the declared wall")
            target_x = ax - direction * target_gap
            walk("set_hayato_distance", abs(target_x - hx), h_keys=RIGHT if target_x > hx else LEFT)
            ready = step("setup_released")
            if ready[h_player]["pivot"][0] != target_x or ready[a_player]["pivot"][0] != ax:
                raise ValueError("The authored case distance could not be reproduced")

            step("hayato_press_prime", h_keys=ONE)
            for read_index in range(1, hold + 1):
                current = step("hayato_press", h_keys=ONE if read_index < hold else 0)
            if current[h_player]["state"] != 1 or current[h_player]["action_tick"] != 0:
                raise ValueError("Hayato did not trigger at the requested hold")
            expected_counter = (21 if is_miss else 22) + hold - 6 if wants_counter else None
            expected = {"gap_px": target_gap, "hayato_action_start": current["logic_tick"],
                        "hayato_contact": 3 if is_miss else (2 if is_guard else 1),
                        "hayato_contact_tick": 10 if is_miss else 9,
                        "alis_life": 100 if is_miss or is_guard else 88,
                        "alis_recoil_px": 0 if is_miss or case == "corner_counter" else (3 if is_guard else 4),
                        "first_alis_action_tick": (12 if is_guard else 17) if not is_miss else None,
                        "alis_counter_contact_tick": expected_counter,
                        "first_hayato_free_tick": expected_counter + 8 if wants_counter else 25}
            start = current["logic_tick"]
            contacts = []
            alis_contacts = []
            alis_first_free = None
            for tick in range(1, 38):
                next_tick = tick + 1
                a_keys = guard_key if is_guard and next_tick == 9 else 0
                if wants_counter and next_tick >= (11 if is_miss else 12):
                    a_keys = ONE
                current = step("action", a_keys=a_keys)
                if current["logic_tick"] != ((start + tick) & 0xFFFF):
                    raise ValueError("A VDP boundary did not publish the expected game tick")
                if current[h_player]["contact"]:
                    contacts.append(current)
                if current[a_player]["contact"]:
                    alis_contacts.append(current)
                if contacts and alis_first_free is None and current[a_player]["can_act"]:
                    alis_first_free = tick
            if len(contacts) != 1:
                raise AssertionError(f"Expected exactly one Hayato result, got {len(contacts)}")
            result = contacts[0]
            observed = {
                "hayato_contact": result[h_player]["contact"],
                "hayato_contact_tick": (result["logic_tick"] - start) & 0xFFFF,
                "hayato_contact_pose": result[h_player]["pose_presented"],
                "alis_life": result[a_player]["life"],
                "alis_recoil_px": (result[a_player]["pivot"][0] - ax) * direction,
                "first_hayato_free_tick": (current[h_player]["free_since"] - start) & 0xFFFF,
                "alis_counter_contact_tick": ((alis_contacts[0]["logic_tick"] - start) & 0xFFFF)
                    if alis_contacts else None,
            }
            if not is_miss:
                observed["first_alis_action_tick"] = alis_first_free
            for field, actual in observed.items():
                required = 3 if field == "hayato_contact_pose" else expected[field]
                if actual != required:
                    raise AssertionError(f"{field}: expected {required}, observed {actual}")
            if wants_counter and (len(alis_contacts) != 1 or alis_contacts[0][a_player]["contact"] != 1
                                  or current[h_player]["life"] != 90):
                raise AssertionError("Alis counter did not connect exactly once")
            verdict = ("stepped_semantics_passed" if all(
                right["vdp_frame"] == left["vdp_frame"] + 1
                for left, right in zip(samples, samples[1:])
            ) else "stepped_semantics_observed_pacing_failed")
        finally:
            try:
                isolated.request(workspace, "input", 0, 0, 0)
            finally:
                json.dump({"case": case, "hold": hold, "session_id": metadata["session_id"],
                           "rom_sha256": sha, "expected": expected, "observed": observed,
                           "renderer_address_span": render_range, "verdict": verdict,
                           "samples": samples}, file, indent=2)
                file.write("\n")
    return verdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument("--rom-sha256", required=True)
    parser.add_argument("--hold", type=int, choices=(6, 8), required=True)
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--capture-events", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{64}", args.rom_sha256):
        parser.error("Provide the exact SHA-256 of the candidate")
    print(replay(args.session, args.rom_sha256, args.hold, args.case, args.out, args.capture_events))
