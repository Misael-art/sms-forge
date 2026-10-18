from types import SimpleNamespace

import pytest

from mugen2sms.generators.scene_cut import (
    _close_attack_rules, _far_attack_rules,
)


def _controller(state, command, distance, line, triggerall=None, triggers=None):
    return SimpleNamespace(
        type="changestate",
        params={"value": str(state)},
        triggerall=(triggerall if triggerall is not None else [
            f'command = "{command}"', "Command != \"holddown\"", distance]),
        triggers=(triggers if triggers is not None else {
            1: ["(Statetype = S) && ctrl"]}),
        line=line,
    )


def test_close_attack_rules_are_bound_to_actions_commands_and_distance():
    rows = [
        {"role": "punch_close", "action": 205, "state": 205},
        {"role": "hp_close", "action": 215, "state": 215},
        {"role": "kick_close", "action": 225, "state": 225},
        {"role": "hk_close", "action": 235, "state": 235},
    ]
    character = SimpleNamespace(raw_states={-1: SimpleNamespace(controllers=[
        _controller(205, "x", "P2BodyDist X < 15", 573),
        _controller(215, "y", "P2BodyDist X < 15", 584),
        _controller(225, "a", "P2BodyDist X < 15", 595),
        _controller(235, "b", "P2BodyDist X < 15", 606),
    ])})

    rules = _close_attack_rules(character, rows,
                                {"lp": "x", "hp": "y", "lk": "a", "hk": "b"})

    assert [rule["role"] for rule in rules] == [
        "punch_close", "hp_close", "kick_close", "hk_close"]
    assert [rule["source_command"] for rule in rules] == ["x", "y", "a", "b"]
    assert [rule["threshold_source_units"] for rule in rules] == [15] * 4
    assert [rule["source_line"] for rule in rules] == [573, 584, 595, 606]


def test_close_attack_rule_rejects_unmodeled_distance_predicate():
    character = SimpleNamespace(raw_states={-1: SimpleNamespace(controllers=[
        _controller(205, "x", "P2BodyDist X <= 15", 573),
    ])})

    with pytest.raises(ValueError, match="direct P2BodyDist X < integer"):
        _close_attack_rules(character,
                            [{"role": "punch_close", "action": 205, "state": 205}],
                            {"lp": "x"})


def test_close_attack_rule_rejects_command_mismatch():
    character = SimpleNamespace(raw_states={-1: SimpleNamespace(controllers=[
        _controller(205, "x", "P2BodyDist X < 15", 573),
    ])})

    with pytest.raises(ValueError, match="does not match commands.lp"):
        _close_attack_rules(character,
                            [{"role": "punch_close", "action": 205, "state": 205}],
                            {"lp": "y"})


@pytest.mark.parametrize("triggerall,triggers", [
    (["command = \"x\"", "P2BodyDist X < 15"],
     {1: ["(Statetype = S) && ctrl"]}),
    (["command = \"x\"", "Command != \"holddown\"",
      "P2BodyDist X < 15", "power >= 0"],
     {1: ["(Statetype = S) && ctrl"]}),
    (["command = \"x\"", "Command != \"holddown\"", "P2BodyDist X < 15"],
     {1: ["(Statetype = S) && ctrl"], 2: ["power >= 0"]}),
    (["command = \"x\"", "Command != \"holddown\"", "P2BodyDist X < 15"],
     {1: ["(Statetype = S) && ctrl", "power >= 0"]}),
])
def test_close_attack_rule_rejects_unmodeled_source_predicates(triggerall, triggers):
    controller = _controller(205, "x", "P2BodyDist X < 15", 573,
                             triggerall=triggerall, triggers=triggers)
    character = SimpleNamespace(raw_states={-1: SimpleNamespace(
        controllers=[controller])})

    with pytest.raises(ValueError):
        _close_attack_rules(character,
                            [{"role": "punch_close", "action": 205, "state": 205}],
                            {"lp": "x"})


def test_far_attack_rule_derives_ordered_complement_from_near_source_rule():
    near = SimpleNamespace(
        type="changestate", params={"value": "200"},
        triggerall=["command = \"x\"", "command != \"holddown\"",
                    "P2BodyDist X < 32"],
        triggers={1: ["statetype = S", "ctrl = 1"],
                  2: ["stateno = 20"], 3: ["stateno = 21"]},
        line=120,
    )
    far = SimpleNamespace(
        type="changestate", params={"value": "201"},
        triggerall=["command = \"x\"", "command != \"holddown\""],
        triggers={1: ["statetype = S", "ctrl = 1"],
                  2: ["stateno = 20"], 3: ["stateno = 21"],
                  4: ["stateno = 200", "time >= 7"]},
        line=134,
    )
    character = SimpleNamespace(raw_states={-1: SimpleNamespace(
        controllers=[near, far])})

    rules = _far_attack_rules(character, [
        {"role": "punch", "action": 200, "state": 200},
        {"role": "punch_far", "action": 201, "state": 201},
    ], {"lp": "x"})

    assert rules == [{
        "role": "punch_far", "near_role": "punch", "command_alias": "lp",
        "source_command": "x", "source_state": 201, "near_source_state": 200,
        "comparison": "ge", "threshold_source_units": 32,
        "source_condition": "P2BodyDist X >= 32 (ordered fallback after < 32)",
        "source_near_condition": "P2BodyDist X < 32",
        "source_line": 134, "source_near_line": 120,
        "source_uncompiled_trigger_groups": {
            "2": ["stateno = 20"], "3": ["stateno = 21"],
            "4": ["stateno = 200", "time >= 7"],
        },
        "source_near_uncompiled_trigger_groups": {
            "2": ["stateno = 20"], "3": ["stateno = 21"],
        },
        "runtime_gate": {
            "command_alias": "lp", "hold_down": False,
            "statetype": "S", "ctrl": True,
            "distance": {"axis": "x", "comparison": "ge",
                         "threshold_source_units": 32},
        },
        "scope": "direct standing/control far fallback only; chain/cancel trigger groups are not executed",
    }]


@pytest.mark.parametrize(
    "far_role,base_role,alias,command,near_state,far_state",
    [
        ("punch_far", "punch", "lp", "x", 200, 201),
        ("hp_far", "hp", "hp", "z", 220, 221),
        ("kick_far", "kick", "lk", "a", 230, 231),
        ("hk_far", "hk", "hk", "c", 250, 251),
    ],
)
def test_far_attack_rule_supports_each_mapped_control_tier(
        far_role, base_role, alias, command, near_state, far_state):
    near = _controller(near_state, command, "P2BodyDist X < 32", 700,
                       triggers={1: ["statetype = S", "ctrl = 1"]})
    far = SimpleNamespace(
        type="changestate", params={"value": str(far_state)},
        triggerall=[f'command = "{command}"', "command != \"holddown\""],
        triggers={1: ["statetype = S", "ctrl = 1"],
                  2: ["stateno = 20"], 3: ["movecontact = 1"]},
        line=720,
    )
    character = SimpleNamespace(raw_states={-1: SimpleNamespace(
        controllers=[near, far])})

    rules = _far_attack_rules(character, [
        {"role": base_role, "action": near_state, "state": near_state},
        {"role": far_role, "action": far_state, "state": far_state},
    ], {alias: command})

    assert len(rules) == 1
    assert rules[0]["role"] == far_role
    assert rules[0]["near_role"] == base_role
    assert rules[0]["source_command"] == command
    assert rules[0]["near_source_state"] == near_state
    assert rules[0]["source_state"] == far_state
    assert rules[0]["comparison"] == "ge"
    assert rules[0]["threshold_source_units"] == 32
    assert rules[0]["source_uncompiled_trigger_groups"] == {
        "2": ["stateno = 20"], "3": ["movecontact = 1"]}


def test_far_attack_rule_fails_closed_without_ordered_near_partner():
    far = SimpleNamespace(
        type="changestate", params={"value": "201"},
        triggerall=["command = \"x\"", "command != \"holddown\""],
        triggers={1: ["statetype = S", "ctrl = 1"]}, line=134)
    character = SimpleNamespace(raw_states={-1: SimpleNamespace(
        controllers=[far])})
    with pytest.raises(ValueError, match="earlier same-command near rule"):
        _far_attack_rules(character, [
            {"role": "punch", "action": 200, "state": 200},
            {"role": "punch_far", "action": 201, "state": 201},
        ], {"lp": "x"})
