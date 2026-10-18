from pathlib import Path
from types import SimpleNamespace

import pytest

from mugen2sms.analysis.fidelity import classify_character
from mugen2sms.analysis.sms_budget import SmsLimits
from mugen2sms.character import Character
from mugen2sms.converters import sms_cmd
from mugen2sms.converters.sms_controls import ControlMap
from mugen2sms.generators.fight_runtime_data import _source_routes
from mugen2sms.generators.scene_cut import _compile_source_routes, _prepare_scene
from mugen2sms.parsers.air import Action, Frame
from mugen2sms.parsers import cmd as cmdmod
from mugen2sms.parsers import sff


def _source_command(name, raw, line):
    steps, errors = cmdmod.parse_command_string(raw)
    return cmdmod.Command(name, steps, 15, 1, line, raw, errors)


def _terry_controls():
    return ControlMap.from_dict({
        "families": {"1": ["x", "y"], "2": ["a", "b"]},
        "thresholds": {"1": [6], "2": [6]},
        "policy": "release_or_threshold",
        "dropped": ["z", "c"],
    })


def test_uniform_scale_precedes_sat_fidelity_gate_and_preserves_timing_and_boxes():
    sprite = sff.Sprite(
        1, 0, 0, 0, 100, 128, bytes([1] * (100 * 128)),
        [(0, 0, 0), (255, 255, 255)] + [(0, 0, 0)] * 254,
        False, None, 0,
    )
    frame = Frame(1, 0, 0, 0, 6, False, False, "A",
                  [(-20, -80, 20, -10)], [(-30, -100, 30, 0)])
    action = Action(0, [frame], 0)
    character = Character("fixture", "test", "fixture.def", "a" * 64,
                          {}, {}, [], {0: action}, [sprite], [], [], {}, {}, [])

    source_fidelity = classify_character(character, SmsLimits())
    assert source_fidelity.by_id["anim:0.0"].classe == "unsupported"

    scaled, selected, source_sizes, report, uniformly_scaled = _prepare_scene(
        character,
        [{"role": "idle", "action": 0, "loop_start": 0}],
        {"target_idle_opaque_height_px": 80, "accepted_height_px": [72, 88]},
    )
    scaled_fidelity = classify_character(scaled, SmsLimits())

    assert uniformly_scaled is True
    assert source_sizes[(1, 0)] == [100, 128]
    assert (scaled.sprites[0].width, scaled.sprites[0].height) == (63, 80)
    assert scaled_fidelity.by_id["anim:0.0"].classe == "approximate"
    assert selected[0].frames[0].time == frame.time
    assert selected[0].frames[0].clsn1 == [(-13, -50, 13, -6)]
    assert selected[0].frames[0].clsn2 == [(-19, -63, 19, 0)]
    assert report["selected_action_air_durations_preserved"] is True
    assert report["selected_action_clsn_box_counts_preserved"] is True
    assert report["runtime_idle_opaque_height_px"] == 80


def test_source_routes_allow_distinct_states_to_alias_one_air_action():
    controllers = [
        SimpleNamespace(type="changestate", line=40, params={"value": "1000"},
                        triggerall=['command = "PowerWave_x"'],
                        triggers={1: ["ctrl = 1"]}),
        SimpleNamespace(type="changestate", line=55, params={"value": "1001"},
                        triggerall=['command = "PowerWave_y"'],
                        triggers={1: ["ctrl = 1"]}),
    ]
    character = SimpleNamespace(raw_states={
        -1: SimpleNamespace(controllers=controllers),
        1000: SimpleNamespace(params={"anim": "1000"}),
        1001: SimpleNamespace(params={"anim": "1000"}),
    }, commands=[
        _source_command("PowerWave_x", "~D, DF, F, x", 10),
        _source_command("PowerWave_y", "~D, DF, F, y", 15),
    ])
    routes = [
        {"route_id": "powerwave_x", "source_command_terms": ["PowerWave_x"],
         "source_controller_line": 40, "source_state": 1000,
         "action_role": "special"},
        {"route_id": "powerwave_y", "source_command_terms": ["PowerWave_y"],
         "source_controller_line": 55, "source_state": 1001,
         "action_role": "special", "alias_of": "powerwave_x"},
    ]

    compiled = _compile_source_routes(
        character, [{"role": "special", "action": 1000}], routes,
        _terry_controls())

    assert [route["source_action"] for route in compiled] == [1000, 1000]
    assert compiled[1]["source_state"] == 1001
    assert compiled[1]["alias_of"] == "powerwave_x"
    assert compiled[1]["source_triggers"] == {"1": ["ctrl = 1"]}
    assert compiled[0]["source_command_definitions"][0]["conversion_status"] == "represented"
    assert compiled[0]["source_command_definitions"][0]["runtime_command_symbol"] == (
        sms_cmd.route_command_symbol("powerwave_x", 0))
    assert compiled[1]["source_command_definitions"][0]["runtime_command_symbol"] == (
        sms_cmd.route_command_symbol("powerwave_y", 0))
    assert compiled[1]["source_command_definitions"][0]["source_command_raw"] == "~D, DF, F, y"


def test_source_route_resolves_command_varset_to_dynamic_changestate():
    setter = SimpleNamespace(
        type="varset", line=10, params={"v": "0", "value": "1000"},
        triggerall=[], triggers={1: ['command = "236_x"']})
    change = SimpleNamespace(
        type="changestate", line=20, params={"value": "Var(0)"},
        triggerall=["Var(0) > 999"], triggers={1: ["statetype = S", "ctrl"]})
    character = SimpleNamespace(raw_states={
        -1: SimpleNamespace(controllers=[setter, change]),
        1000: SimpleNamespace(params={"anim": "1000"}),
    }, commands=[_source_command("236_x", "~D, DF, F, x", 15)])
    controls = ControlMap.from_dict({
        "families": {"1": ["x", "z"], "2": ["a", "c"]},
        "thresholds": {"1": [6], "2": [6]},
        "policy": "release_or_threshold", "dropped": ["b", "y"],
    })
    routes = [{
        "route_id": "special_236_x",
        "source_command_terms": ["236_x"],
        "source_controller_line": 20,
        "source_state": 1000,
        "action_role": "special",
        "source_state_resolution": {
            "kind": "varset_constant", "source_variable": 0,
            "setter_controller_line": 10,
        },
    }]

    compiled = _compile_source_routes(
        character, [{"role": "special", "action": 1000}], routes, controls)
    route = compiled[0]
    runtime_routes = _source_routes(
        Path("fixture.json"),
        {"source_routes": compiled}, {"special": {"action": 1000}})

    assert route["source_state_resolution"] == {
        "kind": "varset_constant", "change_state_expression": "Var(0)",
        "source_variable": 0, "setter_controller_line": 10, "setter_value": 1000,
    }
    assert route["source_command_assignment"]["source_triggers"] == {
        "1": ['command = "236_x"']}
    assert route["source_triggerall"] == ["Var(0) > 999"]
    assert route["source_command_definitions"][0]["conversion_status"] == "represented"
    assert runtime_routes == compiled


def test_source_route_rejects_varset_after_dynamic_changestate():
    change = SimpleNamespace(
        type="changestate", line=10, params={"value": "Var(0)"},
        triggerall=["Var(0) > 999"], triggers={})
    setter = SimpleNamespace(
        type="varset", line=20, params={"v": "0", "value": "1000"},
        triggerall=[], triggers={1: ['command = "236_x"']})
    character = SimpleNamespace(raw_states={
        -1: SimpleNamespace(controllers=[change, setter]),
        1000: SimpleNamespace(params={"anim": "1000"}),
    }, commands=[_source_command("236_x", "~D, DF, F, x", 15)])
    route = {
        "route_id": "special_236_x", "source_command_terms": ["236_x"],
        "source_controller_line": 10, "source_state": 1000,
        "action_role": "special",
        "source_state_resolution": {
            "kind": "varset_constant", "source_variable": 0,
            "setter_controller_line": 20,
        },
    }

    with pytest.raises(ValueError, match="VarSet must precede"):
        _compile_source_routes(
            character, [{"role": "special", "action": 1000}], [route],
            _terry_controls())


def test_source_routes_reject_duplicate_action_role_without_alias():
    controllers = [
        SimpleNamespace(type="changestate", line=40, params={"value": "1000"},
                        triggerall=['command = "PowerWave_x"'], triggers={}),
        SimpleNamespace(type="changestate", line=55, params={"value": "1001"},
                        triggerall=['command = "PowerWave_y"'], triggers={}),
    ]
    character = SimpleNamespace(raw_states={
        -1: SimpleNamespace(controllers=controllers),
        1000: SimpleNamespace(params={"anim": "1000"}),
        1001: SimpleNamespace(params={"anim": "1000"}),
    }, commands=[
        _source_command("PowerWave_x", "~D, DF, F, x", 10),
        _source_command("PowerWave_y", "~D, DF, F, y", 15),
    ])
    routes = [
        {"route_id": "powerwave_x", "source_command_terms": ["PowerWave_x"],
         "source_controller_line": 40, "source_state": 1000,
         "action_role": "special"},
        {"route_id": "powerwave_y", "source_command_terms": ["PowerWave_y"],
         "source_controller_line": 55, "source_state": 1001,
         "action_role": "special"},
    ]

    with pytest.raises(ValueError, match="must alias powerwave_x"):
        _compile_source_routes(
            character, [{"role": "special", "action": 1000}], routes,
            _terry_controls())


def test_source_route_keeps_duplicate_command_definitions_and_compiles_each():
    controller = SimpleNamespace(type="changestate", line=40,
                                 params={"value": "3000"},
                                 triggerall=['command = "Power Geyser"'],
                                 triggers={1: ["ctrl = 1"]})
    character = SimpleNamespace(raw_states={
        -1: SimpleNamespace(controllers=[controller]),
        3000: SimpleNamespace(params={"anim": "3000"}),
    }, commands=[
        _source_command("Power Geyser", "~D, DF, F, D, DF, F, x", 4),
        _source_command("Power Geyser", "~D, DF, F, D, DF, F, y", 9),
    ])
    routes = [{"route_id": "power_geyser",
               "source_command_terms": ["Power Geyser"],
               "source_controller_line": 40, "source_state": 3000,
               "action_role": "power_geyser"}]

    compiled = _compile_source_routes(
        character, [{"role": "power_geyser", "action": 3000}], routes,
        _terry_controls())
    definitions = compiled[0]["source_command_definitions"]

    assert [entry["source_command_line"] for entry in definitions] == [4, 9]
    assert [entry["conversion_status"] for entry in definitions] == [
        "represented", "represented"]
    assert definitions[0]["pattern_blob_hex"] != definitions[1]["pattern_blob_hex"]
    assert [entry["runtime_command_symbol"] for entry in definitions] == [
        sms_cmd.route_command_symbol("power_geyser", 0),
        sms_cmd.route_command_symbol("power_geyser", 1)]


def test_source_route_preserves_and_compiles_timed_charge_command_details():
    controller = SimpleNamespace(type="changestate", line=40,
                                 params={"value": "2050"},
                                 triggerall=['command = "Rising Tackle_x"'],
                                 triggers={1: ["ctrl = 1"]})
    character = SimpleNamespace(raw_states={
        -1: SimpleNamespace(controllers=[controller]),
        2050: SimpleNamespace(params={"anim": "2050"}),
    }, commands=[
        _source_command("Rising Tackle_x", "~15$D,U, x", 45),
    ])
    routes = [{"route_id": "rising_tackle_x",
               "source_command_terms": ["Rising Tackle_x"],
               "source_controller_line": 40, "source_state": 2050,
               "action_role": "rising_tackle_x"}]

    compiled = _compile_source_routes(
        character, [{"role": "rising_tackle_x", "action": 2050}], routes,
        _terry_controls())
    definition = compiled[0]["source_command_definitions"][0]

    assert definition["conversion_status"] == "represented"
    assert definition["conversion_reason"] is None
    assert definition["pattern_blob_hex"] == "04030f0102120f010000100400"
    assert definition["runtime_command_symbol"] == (
        sms_cmd.route_command_symbol("rising_tackle_x", 0))
    assert definition["source_command_steps"][0]["keys"][0]["release_time"] == 15
    assert definition["source_command_steps"][0]["keys"][0]["four_way"] is True


def test_route_with_one_unrepresented_required_command_is_incomplete():
    controller = SimpleNamespace(
        type="changestate", line=40, params={"value": "4000"},
        triggerall=["power >= 1000",
                    'command = "holdfwd" && command = "y+b"'],
        triggers={1: ["stateno = 150"]})
    character = SimpleNamespace(raw_states={
        -1: SimpleNamespace(controllers=[controller]),
        4000: SimpleNamespace(params={"anim": "4000"}),
    }, commands=[
        _source_command("holdfwd", "/$F", 20),
        _source_command("y+b", "y+b", 25),
    ])
    routes = [{"route_id": "counter_attack",
               "source_command_terms": ["holdfwd", "y+b"],
               "source_controller_line": 40, "source_state": 4000,
               "action_role": "counter_attack"}]

    compiled = _compile_source_routes(
        character, [{"role": "counter_attack", "action": 4000}], routes,
        _terry_controls())
    route = compiled[0]

    assert route["command_pattern_coverage"] == "complete"
    assert route["unrepresented_command_patterns"] == []
