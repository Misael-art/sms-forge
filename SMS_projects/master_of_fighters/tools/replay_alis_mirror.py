"""Execute Scene 02 mirror inputs on the two native controller ports."""

import argparse
import json
from pathlib import Path
import sys

from PIL import Image

from bind_scene02_repertoire import verify_rom
from capture_video import _self_check
from duel_probe import decode
from replay_alis_postures import DOWN, LEFT, ONE, RIGHT, TWO, UP, WORKSPACE, dump
from replay_duel_round import MFD1, record_replay, sample_state, snapshot_sat
from revise_scene02_alis import raster
from session_bridge import isolated
from stage_alis_mirror import POSES, rgb


class Round:
    def __init__(self, session):
        self.session = session
        _, self.current = sample_state(session)
        self.trace = []
        self.cases = {}
        self.sat_exposures = {}
        self.inputs = None

    def play(self, case, p1, p2, ticks):
        if self.inputs != (p1, p2):
            isolated.request(self.session, "input", p1, p2, 0)
            self.inputs = p1, p2
        first = len(self.trace)
        for _ in range(ticks):
            stamp = (self.current["stamp"] + 2) & 255
            commit = isolated.request(self.session, "sample-commit", MFD1 + 4, stamp, 8)
            read = isolated.request(self.session, "read", MFD1, 130)
            assert read["frame"] == commit["frame"]
            raw = read["ram"]
            observed = decode(bytes(raw[:74]))
            assert observed["stamp"] == stamp
            if self.current["logic_tick"] != 65535 and observed["logic_tick"] != 0:
                assert observed["logic_tick"] == self.current["logic_tick"] + 1
            self.current = observed
            self.trace.append(dict(frame=read["frame"], inputs=[p1, p2], reactions=raw[88:90],
                                   actions=raw[90:92], vblank_payload=raw[84:88],
                                   cadence_vcounts=raw[100:104], vblank_start=raw[107],
                                   bridge_step_cycles=commit["cycles_advanced"],
                                   published=raw[128] | raw[129] << 8, **observed))
            if any(observed[player]["contact"] in (1, 2) or observed[player]["state"] == 8
                   for player in ("p1", "p2")):
                key = "-".join(str(observed[player]["pose_presented"]) for player in ("p1", "p2"))
                if key not in self.sat_exposures:
                    self.sat_exposures[key] = snapshot_sat(self.session)
        self.cases[case] = (first, len(self.trace))
        return self.trace[first:]

    def direction(self, player, toward):
        return RIGHT if self.current[player]["facing_right"] == toward else LEFT

    def near(self, player, label):
        other = "p2" if player == "p1" else "p1"
        distance = abs(self.current[player]["pivot"][0] - self.current[other]["pivot"][0])
        if distance > 24:
            self.single(player, label, self.direction(player, True), distance - 22)

    def set_gap(self, player, expected, label):
        other = "p2" if player == "p1" else "p1"
        for attempt in range(4):
            gap = abs(self.current[player]["pivot"][0] - self.current[other]["pivot"][0])
            remaining = gap - expected
            if not remaining:
                return
            self.single(player, f"{label}_{attempt}", self.direction(player, remaining > 0),
                        abs(remaining))
            self.play(f"{label}_neutral_{attempt}", 0, 0, 3)
        gap = abs(self.current[player]["pivot"][0] - self.current[other]["pivot"][0])
        assert gap == expected, (label, gap, expected)

    def single(self, player, case, keys, ticks):
        return self.play(case, keys if player == "p1" else 0, keys if player == "p2" else 0, ticks)


def exercise(round_, foundation):
    play = round_.play
    initial = round_.current
    assert initial["p1"]["fighter"] == initial["p2"]["fighter"] == 1
    assert initial["p1"]["pivot"] == [111, 144] and initial["p2"]["pivot"] == [144, 144]
    play("idle", 0, 0, 12)
    play("cold_sword_p1", LEFT | ONE, 0, 8)
    play("sword_p1_recovery", 0, 0, 23)
    play("sword_p2", 0, RIGHT | ONE, 8)
    play("sword_p2_recovery", 0, 0, 23)
    play("walk_and_crouch", RIGHT, DOWN, 8)
    play("recover_crouch", 0, 0, 5)
    play("cross_p1_launch", UP | RIGHT, DOWN, 5)
    play("cross_p1_flight", 0, 0, 25)
    play("p2_only_vertical", 0, UP, 28)
    play("release", 0, 0, 4)
    # Both inputs are live in the same logical update, in opposite postures.
    play("both_jump_stagger", UP, DOWN, 7)
    play("second_jumps", 0, UP, 27)
    play("both_settle", 0, 0, 7)
    for owner in ("p1", "p2"):
        round_.near(owner, f"close_{owner}")
        for i, (button, readings) in enumerate(((ONE, 3), (ONE, 7), (TWO, 3), (TWO, 7))):
            round_.near(owner, f"range_{owner}_{i}")
            play(f"neutral_{owner}_{i}", 0, 0, 4)
            round_.single(owner, f"normal_{owner}_{i}", button, readings)
            play(f"normal_end_{owner}_{i}", 0, 0, 25)
    if foundation:
        return
    exercise_low(round_, "p1")


def exercise_low(round_, owner):
    for i, (button, readings) in enumerate(((ONE, 3), (ONE, 7), (TWO, 3), (TWO, 7))):
        round_.near(owner, f"low_range_{i}")
        round_.single(owner, f"low_base_{i}", DOWN, 5)
        round_.single(owner, f"low_{i}", DOWN | button, readings)
        round_.single(owner, f"low_end_{i}", DOWN, 27)
        round_.play(f"low_recover_{i}", 0, 0, 30)


def exercise_aerial(round_, owner="p1"):
    round_.play("air_warmup", 0, 0, 12)
    round_.near(owner, "first_range")
    for i, (button, readings) in enumerate(((ONE, 3), (ONE, 7), (TWO, 3), (TWO, 7))):
        round_.near(owner, f"air_range_{i}")
        round_.play(f"air_settle_{i}", 0, 0, 5)
        round_.play(f"air_jump_pair_{i}", UP, UP, 6)
        round_.single(owner, f"air_button_{i}", button, readings)
        round_.play(f"air_recovery_{i}", 0, 0, 48)
    if owner == "p2":
        return
    round_.play("walk_input", LEFT, RIGHT, 8)
    round_.near("p1", "range_air_block")
    round_.play("settle_for_air_block", 0, 0, 5)
    round_.play("air_block_launch", UP, UP, 6)
    back = round_.direction("p2", False)
    round_.play("air_block_swing", ONE, back, 3)
    round_.play("air_block_contact", 0, back, 19)
    round_.play("air_block_landing", 0, 0, 8)


def exercise_defense(round_):
    round_.play("settle", 0, 0, 12)
    round_.near("p1", "close")
    round_.play("neutral", 0, 0, 5)
    back = round_.direction("p2", False)
    round_.play("warm_sword", ONE, 0, 8)
    round_.play("standing_guard", 0, back, 14)
    round_.play("stand_recover", 0, 0, 10)
    round_.near("p1", "close_for_low_guard")
    round_.play("settle_low_guard", 0, DOWN | back, 4)
    round_.play("low_guard_sweep", DOWN | TWO, DOWN | back, 8)
    round_.play("low_guard_impact", DOWN, DOWN | back, 19)
    round_.play("low_guard_recover", 0, 0, 10)
    round_.near("p1", "close_for_low_reaction")
    round_.play("settle_both_low", DOWN, DOWN, 4)
    round_.play("low_shield_press", DOWN | ONE, DOWN, 3)
    low_hit = round_.play("unguarded_low_target", DOWN, DOWN, 17)
    assert any(row["p1"]["contact"] == 1 and row["reactions"][1] == 2 for row in low_hit)
    round_.play("ready_for_wrong_guard", 0, 0, 12)
    round_.near("p1", "close_for_wrong_guard")
    round_.play("low_preparation", DOWN, 0, 4)
    round_.play("sweep_press", DOWN | TWO, 0, 8)
    wrong = round_.play("sweep_hits_standing_guard", DOWN, round_.direction("p2", False), 20)
    assert any(row["p1"]["contact"] == 1 and row["actions"][0] == 7 for row in wrong)
    round_.play("wrong_guard_getup", 0, 0, 30)


def exercise_throw(round_):
    round_.play("settle", 0, 0, 12)
    # The boot gap is 33 pixels. Only the throwing command changes.
    round_.play("throw_whiff_at_33", RIGHT | ONE | TWO, 0, 3)
    round_.play("throw_whiff_recovery", 0, 0, 49)
    round_.near("p1", "close_for_ineligible")
    round_.play("target_vertical", 0, UP, 5)
    round_.play("throw_airborne_whiff", RIGHT | ONE | TWO, 0, 3)
    round_.play("recover_airborne_whiff", 0, 0, 50)
    for owner in ("p1", "p2"):
        if owner == "p1":
            round_.set_gap(owner, 32, "last_valid_throw_gap")
        else:
            if round_.current["p2"]["facing_right"]:
                round_.single("p2", "p2_cross_for_left_facing_throw",
                              UP | round_.direction("p2", True), 8)
                round_.play("settle_after_p2_cross", 0, 0, 26)
            assert not round_.current["p2"]["facing_right"]
            round_.near(owner, f"close_for_throw_{owner}")
        round_.play(f"settle_{owner}", 0, 0, 5)
        round_.single(owner, f"throw_{owner}", round_.direction(owner, True) | ONE | TWO, 3)
        round_.play(f"throw_finish_{owner}", 0, 0, 73)
        round_.play(f"retake_{owner}", LEFT, RIGHT, 4)
    owner = min(("p1", "p2"), key=lambda player: round_.current[player]["pivot"][0])
    round_.play("both_to_left_wall", LEFT, LEFT, 100)
    round_.near(owner, "corner_throw_range")
    round_.play("corner_settle", 0, 0, 4)
    round_.single(owner, "corner_throw", round_.direction(owner, True) | ONE | TWO, 3)
    round_.play("corner_release_and_getup", 0, 0, 73)


def exercise_shield_shove(round_, baseline=False):
    round_.play("settle", 0, 0, 12)
    for owner, rival in (("p1", "p2"), ("p2", "p1")):
        for hold, action, duration in ((2, 10, 8), (9, 11, 12)):
            label = f"{owner}_air_kick_{action}"
            round_.set_gap(owner, 24, f"{label}_range")
            round_.play(f"{label}_jump", UP, UP, 6)
            frames = round_.single(owner, f"{label}_press", TWO, hold)
            frames += round_.play(f"{label}_recovery", 0, 0, 33)
            impact = next(row for row in frames if row[owner]["contact"] == 1)
            assert impact["actions"][owner == "p2"] == action, (label, impact)
            following = frames[frames.index(impact):]
            if baseline and action == 11:
                assert impact[rival]["state"] == 5 and any(row[rival]["state"] == 6 for row in following)
            else:
                assert all(row[rival]["state"] == 3 for row in following[:duration]), label
                assert following[duration][rival]["state"] == 0, label
                assert all(row[rival]["state"] not in (5, 6, 7) for row in following), label

        round_.set_gap(owner, 32, f"{owner}_pull_range")
        round_.play(f"{owner}_grip_neutral", 0, 0, 4)
        press = round_.direction(owner, True) | ONE | TWO
        gesture = round_.single(owner, f"{owner}_grip", press, 3)
        gesture += round_.play(f"{owner}_shove_recovery", 0, 0, 63)
        caught = [row for row in gesture if row[rival]["state"] == 8]
        assert len(caught) >= 8, owner
        impact = next(row for row in gesture if row[owner]["contact"] == 1)
        assert impact[rival]["life"] == gesture[0][rival]["life"] - 16
        if baseline:
            assert min(row[rival]["pivot"][1] for row in caught) < 144
            assert impact[rival]["state"] == 5
            continue
        assert all(row[rival]["pivot"][1] == 144 for row in gesture)
        assert all((row[rival]["pivot"][0] > row[owner]["pivot"][0]) ==
                   gesture[0][owner]["facing_right"] for row in gesture)
        def gap(row):
            return abs(row[rival]["pivot"][0] - row[owner]["pivot"][0])
        assert gap(caught[0]) == 32 and gap(impact) == 24
        after = gesture[gesture.index(impact):]
        assert all(row[rival]["state"] == 3 for row in after[:10])
        assert 10 <= gap(after[9]) - gap(impact) <= 16
        assert [row[rival]["state"] for row in (after[10], after[15], after[33], after[40])] == [5, 6, 7, 0]

    if baseline:
        return
    for owner in ("p1", "p2"):
        round_.set_gap(owner, 24, f"{owner}_strong_standing_range")
        grounded_contact = round_.single(owner, f"{owner}_strong_standing_press", TWO, 9)
        grounded_contact += round_.play(f"{owner}_strong_standing_recover", 0, 0, 42)
        assert any(row[owner]["contact"] == 1 and row["actions"][owner == "p2"] == 3
                   for row in grounded_contact), owner

    round_.set_gap("p1", 24, "air_kick_grounded_range")
    round_.play("air_kick_grounded_launch", UP, 0, 14)
    grounded = round_.play("air_kick_grounded_press", TWO, 0, 9)
    grounded += round_.play("air_kick_grounded_recover", 0, 0, 29)
    index = next(i for i, row in enumerate(grounded) if row["p1"]["contact"] == 1)
    assert grounded[index]["actions"][0] == 11 and grounded[index]["p1"]["pivot"][1] < 144
    assert all(row["p2"]["state"] == 3 and row["p2"]["pivot"][1] == 144 for row in grounded[index:index + 12])
    assert abs(grounded[index]["p2"]["pivot"][0] - grounded[index - 1]["p2"]["pivot"][0]) == 7
    assert grounded[index + 12]["p2"]["state"] == 0

    round_.set_gap("p1", 24, "air_kick_block_range")
    round_.play("air_kick_block_launch", UP, UP, 6)
    before_guard = round_.current["p2"]["life"]
    guarded = round_.play("air_kick_block_press", TWO, round_.direction("p2", False), 9)
    guarded += round_.play("air_kick_block_recover", 0, 0, 29)
    assert any(row["p1"]["contact"] == 2 and row["actions"][0] == 11 for row in guarded)
    assert all(row["p2"]["life"] == before_guard and row["p2"]["state"] not in (5, 6, 7) for row in guarded)

    round_.play("both_at_right_wall", RIGHT, RIGHT, 96)
    round_.near("p1", "corner_range")
    round_.play("corner_neutral", 0, 0, 4)
    wall = round_.current["p2"]["pivot"][0]
    round_.single("p1", "corner_grip", RIGHT | ONE | TWO, 3)
    corner = round_.play("corner_shove", 0, 0, 63)
    impact = next(row for row in corner if row["p1"]["contact"] == 1)
    assert impact["p2"]["state"] == 3
    assert all(row["p2"]["pivot"][0] == wall for row in corner)
    assert any(row["p2"]["state"] == 6 for row in corner) and corner[-1]["p2"]["state"] == 0


def exercise_simultaneous(round_):
    round_.play("settle", 0, 0, 12)
    round_.near("p1", "close")
    round_.play("neutral", 0, 0, 4)
    round_.play("two_swords", ONE, ONE, 8)
    round_.play("two_swords_recover", 0, 0, 29)
    round_.near("p1", "close_again")
    round_.play("neutral_again", 0, 0, 4)
    round_.play("two_heavy_kicks", TWO, TWO, 8)
    round_.play("two_heavy_kicks_recover", 0, 0, 31)


def exercise_controls(round_):
    round_.play("settle", 0, 0, 12)
    for player, button in (("p1", ONE), ("p2", TWO)):
        for readings in (5, 6, 7):
            round_.near(player, f"range_{player}_{readings}")
            round_.play(f"neutral_{player}_{readings}", 0, 0, 4)
            round_.single(player, f"button_{player}_{readings}", button, readings)
            round_.play(f"release_{player}_{readings}", 0, 0, 28)
    round_.near("p1", "close_for_shield_step")
    round_.play("special_down", DOWN, 0, 4)
    round_.play("special_forward", round_.direction("p1", True) | ONE, 0, 4)
    round_.play("special_release", 0, 0, 28)


def exercise_materials(round_):
    round_.play("settle", 0, 0, 8)
    round_.set_gap("p1", 24, "sword_range")
    round_.play("sword_launch", UP, 0, 6)
    prior_y = 144
    for step in range(16):
        y = round_.play(f"sword_arc_{step}", 0, 0, 1)[-1]["p1"]["pivot"][1]
        if prior_y < 70 and y > prior_y:
            break
        prior_y = y
    else:
        raise AssertionError("Missing sword descent")
    sword = round_.play("sword_press", ONE, 0, 7) + round_.play("sword_release", 0, 0, 20)
    assert any(row["actions"][0] == 9 and row["p1"]["contact"] == 1 and row["p1"]["pivot"][1] < 144
               for row in sword)

    round_.set_gap("p1", 24, "air_shield_range")
    round_.play("air_shield_launch", UP, UP, 6)
    round_.play("air_shield_press", ONE, 0, 3)
    air_shield = round_.play("air_shield_release", 0, 0, 26)
    assert any(row["actions"][0] == 8 and row["p1"]["contact"] == 1 for row in air_shield)

    round_.set_gap("p2", 24, "ground_shield_range")
    round_.play("ground_shield_press", 0, ONE, 3)
    ground_shield = round_.play("ground_shield_release", 0, 0, 20)
    assert any(row["actions"][1] == 0 and row["p2"]["contact"] == 1 for row in ground_shield)

    round_.set_gap("p1", 24, "sweep_range")
    round_.play("sweep_press", DOWN | TWO, 0, 8)
    sweep = round_.play("sweep_release", DOWN, 0, 48)
    assert any(row["actions"][0] == 7 and row["p1"]["contact"] == 1 for row in sweep)
    down_sequence = [row["p2"]["pose_presented"] for row in sweep]
    stages = [down_sequence.index(POSES.index(name)) for name in ("fall", "downed", "ground_rise", "getup")]
    assert stages == sorted(set(stages))


def exercise_retouch(round_):
    exposure_failures = []
    for index, player in enumerate(("p1", "p2")):
        def single(label, keys, ticks):
            return round_.single(player, f"{player}_{label}", keys, ticks)

        single("sword_ready", 0, 16)
        round_.set_gap(player, 24, f"{player}_sword_gap")
        single("sword_launch", UP, 6)
        previous = 144
        for tick in range(16):
            y = single(f"sword_arc_{tick}", 0, 1)[-1][player]["pivot"][1]
            if previous < 70 and y > previous:
                break
            previous = y
        else:
            raise AssertionError((player, "missing descending jump"))
        sequence = single("sword_press", ONE, 7) + single("sword_finish", 0, 27)
        edge = next(row for row in sequence if row[player]["keys_consumed"] & ONE)
        prep = POSES.index("air_0_1")
        assert edge[player]["pose_requested"] == prep
        if edge[player]["pose_presented"] != prep:
            exposure_failures.append(
                (player, edge["logic_tick"], prep, edge[player]["pose_presented"]))
        hit = next(row for row in sequence if row[player]["contact"] == 1 and row["actions"][index] == 9)
        assert hit["logic_tick"] - edge["logic_tick"] <= 6 and hit[player]["pivot"][1] <= 130
        assert hit[player]["boxes"]["attack"]["top"] <= 108

        for action, label, direction, hold in (
            (2, "light_kick", 0, 2), (3, "heavy_kick", 0, 9),
            (6, "low_kick", DOWN, 2), (7, "sweep", DOWN, 9),
            (10, "jump_kick", UP, 2), (11, "jump_heavy_kick", UP, 25),
        ):
            single(label + "_ready", 0, 20)
            round_.set_gap(player, 24, f"{player}_{label}_gap")
            single(label + "_neutral", 0, 4)
            pressed = single(label + "_press", direction | TWO, hold)
            sequence = pressed + single(label + "_release", direction & DOWN, 54)
            edge = next(row for row in sequence if row[player]["keys_consumed"] & TWO)
            assert edge[player]["keys_consumed"] == direction | TWO
            commenced = next(row for row in sequence
                             if row[player]["state"] == 1 and row["actions"][index] == action)
            if direction == UP:
                prep_name = f"air_{(action - 8) & ~1}_1"
                prep = next(row for row in sequence if row[player]["pose_requested"] == POSES.index(prep_name))
                assert prep["logic_tick"] - edge["logic_tick"] <= 3
                active = next(row for row in sequence if row[player]["boxes"]["attack"] is not None)
                assert active["logic_tick"] - edge["logic_tick"] <= 7
                assert active[player]["pivot"][1] < 144
                assert not any(row[player]["state"] == 1 and row["actions"][index] < 8 for row in sequence)
                if action == 11:
                    assert any(row[player]["pivot"][1] == 144 and row[player]["keys_consumed"] & TWO
                               for row in sequence if row["logic_tick"] > active["logic_tick"])
            else:
                assert any(row[player]["contact"] == 1 and row["actions"][index] == action
                           for row in sequence), (player, label, commenced["logic_tick"])
            if action == 7:
                victim = "p2" if player == "p1" else "p1"
                presented = [row[victim]["pose_presented"] for row in sequence]
                ordered = [presented.index(POSES.index(name)) for name in ("downed", "ground_rise", "getup")]
                assert ordered == sorted(set(ordered))
    return exposure_failures


def exercise_landing(round_, baseline=False):
    round_.play("settle", 0, 0, 12)
    for owner in ("p1", "p2"):
        def play(suffix, keys, ticks):
            return round_.single(owner, f"{label}_{suffix}", keys, ticks)

        for button, base in ((ONE, 8), (TWO, 10)):
            for heavy in (False, True):
                action = base + heavy
                label = f"{owner}_landing_{action}"
                direction = round_.direction(owner, False) if button == TWO else 0
                play("jump", UP | direction, 14)
                approach = play("attack", button | direction, 5 if heavy else 2)
                posture = DOWN | (button if heavy else 0)
                for tick in range(11):
                    approach += play(f"land_{tick}", posture, 1)
                    if approach[-1][owner]["pivot"][1] == 144:
                        break
                landing = next(i for i, row in enumerate(approach)
                               if i and row[owner]["pivot"][1] == 144 and approach[i - 1][owner]["pivot"][1] < 144)
                assert any(row[owner]["state"] == 1 and row["actions"][owner == "p2"] == action
                           and row[owner]["pivot"][1] < 144 for row in approach[:landing]), label
                landed = approach[landing]
                assert landed[owner]["pivot"][1] == 144
                if baseline:
                    assert landed[owner]["state"] == 1, (label, landed[owner])
                    play("baseline_recovery", 0, 26)
                    continue
                assert landed[owner]["state"] == 0 and landed[owner]["boxes"]["attack"] is None, label
                assert landed[owner]["pose_requested"] in (POSES.index("alis_crouch_transition"),
                                                           POSES.index("alis_crouch")), label
                still_held = play("ground_hold", posture, 2)
                assert all(row[owner]["state"] == 0 for row in still_held), label
                play("release", DOWN, 1)
                play("new_press", DOWN | button, 2)
                ground = play("new_release", DOWN, 28)
                released = next(row for row in ground if row[owner]["keys_consumed"] == DOWN)
                assert released[owner]["state"] == 1 and released["actions"][owner == "p2"] == base - 4, label
                play("neutral", 0, 8)
        if not baseline:
            # The emulator receives a change at a VDP boundary. Accept only
            # a trial whose fresh edge the ROM consumes on the floor reading.
            for lead in (1, 2):
                label = f"{owner}_landing_edge_{lead}"
                play("jump", UP, 14)
                play("kick", TWO, len(approach) - lead)
                edge_rows = play("new_button_on_contact", DOWN | ONE | TWO, lead + 1)
                first_edge = next(row for row in edge_rows if row[owner]["keys_consumed"] & ONE)
                floor = next(row for row in edge_rows if row[owner]["pivot"][1] == 144)
                if first_edge == floor:
                    assert floor[owner]["state"] == 0 and floor[owner]["boxes"]["attack"] is None
                    release_rows = play("release_new_button", DOWN | TWO, 3)
                    released = next(row for row in release_rows if row[owner]["keys_consumed"] == DOWN | TWO)
                    assert released[owner]["state"] == 1 and released["actions"][owner == "p2"] == 4
                    play("neutral", 0, 28)
                    break
                play("neutral", 0, 28)
            else:
                raise AssertionError(f"{owner}: input did not align with the landing reading")


def exercise_motion(round_, center_each=False):
    round_.play("settle", 0, 0, 12)
    round_.play("rise_with_one_held", UP | ONE, 0, 5)
    through_landing = round_.play("keep_one_through_landing", ONE, 0, 23)
    armed = [row for row in through_landing if row["p1"]["state"] == 1]
    assert armed and all(row["actions"][0] == 9 for row in armed)
    assert round_.current["p1"]["pivot"][1] == 144
    round_.play("release_one", 0, 0, 4)
    round_.play("rearm_ground_one", ONE, 0, 5)
    after_rearm = round_.play("ground_one_released", 0, 0, 22)
    assert any(row["actions"][0] == 0 and row["p1"]["state"] == 1 for row in after_rearm)
    for actor in ("p1", "p2"):
        for toward in (True, False):
            name = f"{actor}_{'forward' if toward else 'back'}"
            if center_each:
                round_.near(actor, f"{name}_close")
                pivots = [round_.current[player]["pivot"][0] for player in ("p1", "p2")]
                translation = 128 - sum(pivots) // 2
                if translation:
                    shift = RIGHT if translation > 0 else LEFT
                    round_.play(f"{name}_center", shift, shift, abs(translation))
                    round_.play(f"{name}_stand", 0, 0, 4)
            way = round_.direction(actor, toward)
            arc = round_.single(actor, f"{name}_takeoff", UP | way, 8)
            arc.extend(round_.single(actor, f"{name}_sword_press", way | ONE, 7))
            arc.extend(round_.single(actor, f"{name}_jump_buffered", UP | way, 27))
            arc.extend(round_.play(f"{name}_finish", 0, 0, 18))
            heights = [row[actor]["pivot"][1] for row in arc]
            assert sum(before == 144 and after < 144
                       for before, after in zip(heights, heights[1:])) == 2, name
            assert min(heights) == 66 and heights[-1] == 144, name
            if center_each:
                first_airborne = next(i for i, y in enumerate(heights) if y < 144)
                first_landing = heights.index(144, first_airborne)
                xs = [row[actor]["pivot"][0] for row in arc[first_airborne:first_landing]]
                assert max(abs(a - b) for a, b in zip(xs, xs[1:])) == 6, name


def exercise_edges(round_):
    round_.play("settle", 0, 0, 12)
    # First nonintersecting gap: offense right plus the inclusive distance
    # to the facing defender's hurt box. Both actors use the same air arc.
    gaps = (31, 56, 36, 40, 32, 42, 37, 41, 30, 30, 33, 30)
    for action, gap in enumerate(gaps):
        owner = "p1" if action % 2 == 0 else "p2"
        button = ONE if action % 4 < 2 else TWO
        readings = 7 if action % 2 else 3
        low = DOWN if 4 <= action < 8 else 0
        round_.set_gap(owner, gap, f"outside_{action}")
        if action >= 8:
            round_.play(f"outside_launch_{action}", UP, UP, 6)
        if low:
            round_.single(owner, f"outside_lower_{action}", low, 4)
        attack = round_.single(owner, f"outside_press_{action}", low | button, readings)
        attack += round_.single(owner, f"outside_recovery_{action}", low, 37)
        # A miss is emitted on the final active tick. The same attack ID
        # reaching the wrong victim posture cannot certify this distance.
        assert any(row[owner]["contact"] == 3 and row["actions"][action % 2] == action
                   for row in attack), (action, gap)
        assert all(row[owner]["contact"] != 1 for row in attack)
        round_.play(f"outside_rearm_{action}", 0, 0, 5)


def exercise_punish(round_):
    round_.play("settle", 0, 0, 12)
    for action, outside, down in ((3, 40, 0), (7, 41, DOWN)):
        label = f"punish_{action}"
        round_.set_gap("p1", outside, f"{label}_range")
        round_.play(f"{label}_posture", down, 0, 4)
        round_.play(f"{label}_windup", down | TWO, 0, 7)
        observed = []
        for delay in range(16):
            row = round_.play(f"{label}_wait_{delay}", down, 0, 1)[0]
            observed.append(row)
            if row["p1"]["contact"] == 3:
                assert row["actions"][0] == action
                break
            if action == 7 and row["p1"]["action_tick"] == 9:
                # Enter from the first visible miss. The final active box
                # still tests the original gap before the defender moves.
                attack = row["p1"]["boxes"]["attack"]
                hurt = row["p2"]["boxes"]["hurt"]
                assert attack and attack["right"] <= hurt["left"], label
                break
        else:
            raise AssertionError(f"{label}: attack did not miss")
        toward = round_.direction("p2", True)
        observed.extend(round_.single("p2", f"{label}_advance", toward, outside - 35))
        assert any(row["p1"]["contact"] == 3 and row["actions"][0] == action
                   for row in observed), label
        round_.single("p2", f"{label}_counter", toward | TWO, 2)
        counter = round_.play(f"{label}_counter_release", 0, 0, 22)
        index = next(i for i, row in enumerate(counter) if row["p2"]["contact"] == 1)
        assert index > 0 and counter[index - 1]["p1"]["state"] == 1, label
        assert counter[index]["p1"]["free_since"] != counter[index]["logic_tick"], label
        round_.play(f"{label}_recover", 0, 0, 11)


def exercise_all_guards(round_):
    round_.play("settle", 0, 0, 12)
    round_.play("right_wall_pair", RIGHT, RIGHT, 100)
    assert round_.current["p2"]["pivot"][0] == 212
    assert round_.current["p2"]["pivot"][0] - round_.current["p1"]["pivot"][0] == 24
    for action in range(12):
        label = f"guard_action_{action}"
        attacker_pose = DOWN if 4 <= action < 8 else 0
        guard = RIGHT | (DOWN if action in (6, 7) else 0)
        button = ONE if action % 4 < 2 else TWO
        duration = 7 if action % 2 else 3
        if action >= 8:
            round_.play(f"{label}_jump", UP, UP, 6)
        else:
            round_.play(f"{label}_ready", attacker_pose, guard, 5)
        impact = round_.play(f"{label}_press", attacker_pose | button, guard, duration)
        impact += round_.play(f"{label}_release", attacker_pose, guard, 29)
        assert any(row["p1"]["contact"] == 2 and row["actions"][0] == action
                   for row in impact), action
        assert all(row["p2"]["life"] == 100 for row in impact), action
        round_.play(f"{label}_rearm", 0, 0, 12)


def exercise_reset(round_):
    round_.play("settle", 0, 0, 12)
    for number in range(7):
        round_.near("p1", f"close_{number}")
        round_.play(f"neutral_{number}", 0, 0, 5)
        round_.play(f"throw_{number}", round_.direction("p1", True) | ONE | TWO, 0, 3)
        round_.play(f"fall_{number}", 0, 0, 77)
        if round_.current["p2"]["life"] == 0:
            break
    assert round_.current["p2"]["state"] == 4, round_.current["p2"]
    before = [round_.current[player]["pivot"] for player in ("p1", "p2")]
    round_.play("ko_locks_movement", RIGHT, LEFT, 5)
    assert [round_.current[player]["pivot"] for player in ("p1", "p2")] == before
    round_.play("reset_from_p2", 0, ONE, 3)
    round_.play("reset_settle", 0, 0, 4)
    assert all(round_.current[player]["life"] == 100 for player in ("p1", "p2"))
    round_.play("first_move_after_reset", RIGHT, 0, 5)
    assert round_.current["p1"]["pivot"][0] > 111


def spectrum(image, pivot, colors):
    x, y = pivot
    return sum(pixel in colors for pixel in image.crop(
        (max(0, x - 38), max(0, y - 57), min(256, x + 39), min(192, y + 1))).getdata())


def inspect_scanout(session, out, recording, trace, sha):
    colors = [{rgb(code) for code in (19, 35)}, {rgb(code) for code in (24, 44)}]
    exposures = []
    for case, condition in [
        ("boot", lambda a, b: a["pivot"] == [111, 144] and b["pivot"] == [144, 144]),
        ("swapped", lambda a, b: a["pivot"][0] - b["pivot"][0] > 45 and a["pivot"][1] == b["pivot"][1] == 144),
    ]:
        for sample in trace:
            a, b = sample["p1"], sample["p2"]
            if not condition(a, b):
                continue
            frame = sample["frame"] - recording["first_frame"]
            path = session / "evidence/mirror" / f"{frame:06d}.png"
            if not path.exists():
                continue
            with Image.open(path) as file:
                image = file.convert("RGB")
            p1 = spectrum(image, a["pivot"], colors[0])
            p2 = spectrum(image, b["pivot"], colors[1])
            if p1 > 15 and p2 > 15:
                image.save(out / f"{case}.png")
                exposures.append(dict(case=case, frame=sample["frame"], p1_ruby=p1, p2_emerald=p2))
                break
    dump(out / "costumes.json", dict(session_id=session.name, rom_sha256=sha, exposures=exposures))
    assert len(exposures) == 2, exposures


def prove_contacts(session, out, recording, trace, banks, sha):
    pages = json.loads((banks / "repertoire-pages.json").read_bytes())
    palette = pages["palette"]
    frames = {(row["name"], row["player"], row["right"]): raster(row, palette)
              for row in pages["frames"]}
    exposures = []
    for sample in trace:
        for player, other in (("p1", "p2"), ("p2", "p1")):
            actor, victim = sample[player], sample[other]
            if actor["contact"] not in (1, 2):
                continue
            expected = {}
            if actor["pose_presented"] == actor["pose_requested"]:
                expected = composition_pixels(sample, frames)
            found = match_scanout(session, recording, sample, expected,
                                  out / f"contact-{player}-{sample['logic_tick']}.png")
            exposures.append(dict(
                player=player, logic_tick=sample["logic_tick"], contact=actor["contact"],
                action=sample["actions"][int(player == "p2")], requested=actor["pose_requested"],
                resident=actor["pose_resident"], presented=actor["pose_presented"],
                victim_requested=victim["pose_requested"], victim_presented=victim["pose_presented"],
                hitbox=actor["boxes"]["attack"], victim_hurtbox=victim["boxes"]["hurt"], scanout=found))
    dump(out / "contact-pixels.json", dict(session_id=session.name, rom_sha256=sha, exposures=exposures))


def composition_pixels(sample, frames):
    expected = {}
    for index, player in enumerate(("p1", "p2")):
        state = sample[player]
        x, y = state["pivot"]
        pixels = frames[POSES[state["pose_presented"]], index, state["presented_facing_right"]]
        for (u, v), color in pixels.items():
            point = x + u, y + v - 144
            if 0 <= point[0] < 256 and 0 <= point[1] < 192:
                expected[point] = None if point in expected else rgb(color)
    return expected


def match_scanout(session, recording, sample, expected, destination):
    if not expected:
        return None
    for frame in range(sample["frame"] - 1, sample["frame"] + 4):
        path = session / "evidence/mirror" / f"{frame - recording['first_frame'] - 1:06d}.png"
        if not path.exists():
            continue
        with Image.open(path) as file:
            image = file.convert("RGB")
        if all(image.getpixel(point) == color for point, color in expected.items() if color is not None):
            image.save(destination)
            return dict(file=destination.name, sha256=isolated.sha(destination), frame=frame,
                        matched_pixels=sum(color is not None for color in expected.values()))
    return None


def prove_shove_phases(session, out, recording, round_, banks, sha):
    pages = json.loads((banks / "repertoire-pages.json").read_bytes())
    frames = {(row["name"], row["player"], row["right"]): raster(row, pages["palette"])
              for row in pages["frames"]}
    exposures = []
    for owner, rival in (("p1", "p2"), ("p2", "p1")):
        press = round_.cases[f"{owner}_air_kick_10_press"][0]
        kick = round_.cases[f"{owner}_air_kick_10_recovery"][1]
        armed = None
        for row in round_.trace[press:kick]:
            if row[owner]["pose_presented"] != POSES.index("air_2_1"):
                continue
            armed = match_scanout(session, recording, row, composition_pixels(row, frames),
                                  out / f"{owner}-air-kick-armed.png")
            if armed:
                break
        exposures.append(dict(owner=owner, phase="air_kick_armed", scanout=armed))
        grip = round_.cases[f"{owner}_grip"][0]
        recovery = round_.cases[f"{owner}_shove_recovery"][1]
        trace = round_.trace[grip:recovery]
        for phase, player, pose, state in (
            ("grip", owner, "throw_1", (rival, 8)),
            ("pull", owner, "throw_2", (rival, 8)),
            ("brace", owner, "throw_3", (rival, 8)),
            ("impact", owner, "throw_4", (rival, 3)),
            ("steps", rival, "caught_5", (rival, 3)),
            ("fall", rival, "fall", (rival, 5)),
            ("floor", rival, "downed", (rival, 6)),
            ("recovery", owner, "throw_5", (rival, 6)),
        ):
            found = None
            for row in trace:
                if row[player]["pose_presented"] != POSES.index(pose) or row[state[0]]["state"] != state[1]:
                    continue
                if phase == "impact" and row[owner]["contact"] != 1:
                    continue
                found = match_scanout(session, recording, row, composition_pixels(row, frames),
                                      out / f"{owner}-{phase}.png")
                if found:
                    break
            exposures.append(dict(owner=owner, phase=phase, scanout=found))
    dump(out / "shove-phases.json", dict(session_id=session.name, rom_sha256=sha, exposures=exposures))
    assert all(item["scanout"] for item in exposures), exposures


def run(args):
    sha = verify_rom(args.rom, args.banks)["rom_sha256"]
    assert _self_check() == 0
    args.out.mkdir(parents=True)
    exposure_failures = []
    project = Path(__file__).resolve().parents[1]
    with isolated.performance_reservation(), isolated.project_reservation(project):
        isolated.DEFAULT_ROOT = WORKSPACE / ".runtime/s"
        session = isolated.start(args.rom, ttl=900)
        try:
            round_ = Round(session)
            isolated.request(session, "record-steps-start", "mirror")
            try:
                if args.scenario == "air":
                    exercise_aerial(round_)
                elif args.scenario == "throw":
                    exercise_throw(round_)
                elif args.scenario == "shield_shove":
                    exercise_shield_shove(round_, args.baseline)
                elif args.scenario == "landing":
                    exercise_landing(round_, args.baseline)
                elif args.scenario == "guard":
                    exercise_defense(round_)
                elif args.scenario == "simultaneous":
                    exercise_simultaneous(round_)
                elif args.scenario == "controls":
                    exercise_controls(round_)
                elif args.scenario == "materials":
                    exercise_materials(round_)
                elif args.scenario == "retouch":
                    exposure_failures = exercise_retouch(round_)
                elif args.scenario == "motion":
                    exercise_motion(round_)
                elif args.scenario == "motion_open":
                    exercise_motion(round_, center_each=True)
                elif args.scenario == "edges":
                    exercise_edges(round_)
                elif args.scenario == "punish":
                    exercise_punish(round_)
                elif args.scenario == "guards_all":
                    exercise_all_guards(round_)
                elif args.scenario == "reverse":
                    round_.play("settle", 0, 0, 12)
                    exercise_low(round_, "p2")
                    exercise_aerial(round_, "p2")
                elif args.scenario == "reset":
                    exercise_reset(round_)
                else:
                    exercise(round_, args.foundation)
            finally:
                recording = isolated.request(session, "record-steps-stop")
                trace = round_.trace
                hits = [
                    dict(player=player, requested_at_hit=row[player]["pose_requested"],
                         opponent_life=row[other]["life"], pose_presented=row[player]["pose_presented"],
                         action=row["actions"][index], frame=row["frame"])
                    for row in trace
                    for index, (player, other) in enumerate((("p1", "p2"), ("p2", "p1")))
                    if row[player]["contact"] == 1
                ]
                dump(args.out / "input.json", dict(rom_sha256=sha, session_id=session.name, recording=recording,
                                                   samples=trace, cases=round_.cases, moves=hits))
            render = isolated.request(session, "read", 0xC7D2, 32)["ram"]
            sat = snapshot_sat(session)
            dump(args.out / "runtime.json", dict(rom_sha256=sha, session_id=session.name, sat=sat,
                                                 phase_sat=round_.sat_exposures,
                                                 fault=render[8], overruns=render[25] | render[26] << 8,
                                                 worst_vdp_gap=max(b["frame"] - a["frame"]
                                                                   for a, b in zip(trace, trace[1:]))))
        finally:
            isolated.close_session(session)
            meta = isolated.load(session)[1]
            dump(args.out / "stepped-closed.json", meta)
            assert meta["state"] == "closed"
        if args.scenario == "mixed":
            inspect_scanout(session, args.out, recording, trace, sha)
        prove_contacts(session, args.out, recording, trace, args.banks, sha)
        if args.scenario == "shield_shove" and not args.baseline:
            prove_shove_phases(session, args.out, recording, round_, args.banks, sha)
        summaries = [{**hit, "pose": POSES[hit["requested_at_hit"]]} for hit in hits]
        dump(args.out / "contacts.json", dict(rom_sha256=sha, session_id=session.name, hits=summaries))
        if args.continuous and any(row[player]["contact"] in (1, 2)
                                   for row in trace for player in ("p1", "p2")):
            live = isolated.start(args.rom, ttl=900)
            try:
                result = record_replay(live, args.out / "input.json", args.out / "continuous")
                print(json.dumps(result["cadence"], indent=2))
            finally:
                isolated.close_session(live)
                meta = isolated.load(live)[1]
                dump(args.out / "continuous-closed.json", meta)
                assert meta["state"] == "closed"
        print(json.dumps(summaries, indent=2))
        assert not exposure_failures, ("Delayed aerial windup", exposure_failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("rom", "banks", "out"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--foundation", action="store_true")
    parser.add_argument("--continuous", action="store_true")
    parser.add_argument("--baseline", action="store_true", help="Expect the historical behavior for this scenario")
    parser.add_argument("--scenario", choices=("mixed", "air", "throw", "guard", "simultaneous",
                                              "controls", "motion", "motion_open", "edges", "punish", "reverse",
                                              "guards_all", "reset", "retouch", "materials", "shield_shove",
                                              "landing"), default="mixed")
    run(parser.parse_args())
