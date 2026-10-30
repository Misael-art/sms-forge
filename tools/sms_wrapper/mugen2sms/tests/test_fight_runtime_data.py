import json
from pathlib import Path

import pytest

from mugen2sms.converters.sms_cmd import route_command_symbol
from mugen2sms.generators.fight_runtime_data import render


ROLES = [
    {"role": name, "action": i * 10, "state": i * 10, "loop_start": None,
     "frame_count": 1}
    for i, name in enumerate(("idle", "walk_f", "walk_b", "jump", "crouch",
                              "guard", "punch", "hp", "special", "ko",
                              "kick", "hk"))
]
CONSTANTS = {
    "life": 1000, "walk_fwd": 512, "walk_back": -460,
    "jump_vy": 2585, "gravity": 110, "damage_punch": 30,
    "damage_hp": 20, "damage_kick": 35, "damage_hk": 80,
    "damage_special": 105, "special_vel": 512,
    "input_threshold_key1": 6, "input_threshold_key2": 6,
    "hitstop": 8, "hit_push": 3, "guard_push": 5,
}


def _manifest(path: Path, delta: int = 0):
    roles = [dict(row) for row in ROLES]
    for row in roles:
        row["action"] += delta
        if row["role"] == "punch":
            row["state"] = None
    data = {"source_sha256": ("a" if not delta else "b") * 64,
            "source_def": "character.def", "roles": roles,
            "source_limitations": ["fixture limitation"],
            "commands": {"special": "236_x", "lp": "x", "hp": "z",
                         "lk": "a", "hk": "c"},
            "runtime_constants": dict(CONSTANTS, life=1000 + delta)}
    path.write_text(json.dumps(data), encoding="utf-8")


def _shared_source_routes():
    def definition(term, line, route_id):
        return {
            "source_command_term": term,
            "source_command": term,
            "source_command_line": line,
            "source_command_raw": "x",
            "source_command_time": 10,
            "source_command_buffer_time": 1,
            "source_command_errors": [],
            "source_command_steps": [{"strict": False, "keys": [
                {"key": "x", "release": False, "release_time": 0,
                 "hold": False, "four_way": False}]}],
            "conversion_status": "represented",
            "conversion_reason": None,
            "pattern_blob_hex": "04010a01200400",
            "runtime_command_symbol": route_command_symbol(route_id, 0),
        }

    return [
        {"route_id": "wave_x", "source_command_terms": ["wave_x"],
         "source_controller_type": "changestate", "source_controller_line": 40,
         "source_triggerall": ['command = "wave_x"'],
         "source_triggers": {"1": ["ctrl = 1"]},
         "source_state": 80, "source_action": 80,
         "action_role": "special", "alias_of": None,
         "source_command_definitions": [definition("wave_x", 10, "wave_x")],
         "command_pattern_coverage": "complete",
         "unrepresented_command_patterns": []},
        {"route_id": "wave_y", "source_command_terms": ["wave_y"],
         "source_controller_type": "changestate", "source_controller_line": 55,
         "source_triggerall": ['command = "wave_y"'],
         "source_triggers": {"1": ["ctrl = 1"]},
         "source_state": 81, "source_action": 80,
         "action_role": "special", "alias_of": "wave_x",
         "source_command_definitions": [definition("wave_y", 11, "wave_y")],
         "command_pattern_coverage": "complete",
         "unrepresented_command_patterns": []},
    ]


def _header():
    lines = []
    for prefix in ("P1", "P2"):
        lines.append(f"#define {prefix}_CUT_POSE_COUNT 1")
        lines.append(f"#define {prefix}_FIXTURE_FRAME_META_SIZE 73")
        for role in ROLES:
            lines.append(f"#define {prefix}_CUT_ANIM_{role['role'].upper()} "
                         f"{ROLES.index(role)}")
        for index, role in enumerate(("punch_close", "hp_close", "kick_close", "hk_close"), 12):
            lines.append(f"#define {prefix}_CUT_ANIM_{role.upper()} {index}")
        for index, role in enumerate(("punch_far", "hp_far", "kick_far", "hk_far"), 16):
            lines.append(f"#define {prefix}_CUT_ANIM_{role.upper()} {index}")
        for role in ("SPECIAL", "LP", "HP", "LK", "HK"):
            lines.append(f"#define {prefix}_CUT_CMD_{role}_SIZE 7")
    for route in _shared_source_routes():
        for definition in route["source_command_definitions"]:
            symbol = definition["runtime_command_symbol"]
            blob = bytes.fromhex(definition["pattern_blob_hex"])
            lines.append(f"#define P1_{symbol}_SIZE {len(blob)}")
            lines.append(f"const unsigned char P1_{symbol}[{len(blob)}] = "
                         "{ " + ", ".join(str(value) for value in blob) + " };")
    lines += ["#define P1_POSE_BASE 0", "#define P2_POSE_BASE 10"]
    return "\n".join(lines) + "\n"


def test_runtime_state_tables_are_compiled_from_each_slot_manifest(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2, 100)
    p1_data = json.loads(p1.read_text())
    p1_data["source_routes"] = _shared_source_routes()
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")

    output, report = render((p1, p2), scene_header)

    assert "static const StateDef p1_states[ST_N_STATES]" in output
    assert "static const StateDef p2_states[ST_N_STATES]" in output
    assert "static const CommandDef p1_commands[]" in output
    assert "static const FightSourceRouteDef p1_source_routes[]" in output
    assert (f"{{ P1_{route_command_symbol('wave_x', 0)}, 80, 80, "
            "P1_CUT_ANIM_SPECIAL }") in output
    assert (f"{{ P1_{route_command_symbol('wave_y', 0)}, 81, 80, "
            "P1_CUT_ANIM_SPECIAL }") in output
    assert "#define P1_SOURCE_ROUTE_PATTERN_COUNT 2" in output
    assert "{ P1_CUT_CMD_SPECIAL, FIGHT_CMD_SPECIAL_UNSUPPORTED }" in output
    assert "{ P1_CUT_CMD_HP, FIGHT_CMD_HP }" in output
    assert "{ P1_CUT_CMD_LP, FIGHT_CMD_LP }" in output
    assert output.index("{ P1_CUT_CMD_HP, FIGHT_CMD_HP }") < output.index(
        "{ P1_CUT_CMD_LP, FIGHT_CMD_LP }")
    assert "{ 65535, P1_CUT_ANIM_PUNCH, S_HIT, 0, 30 }" in output
    assert "{ 70, P2_CUT_ANIM_HP, S_HIT, 0, 20 }" in output
    assert "{ 80, P2_CUT_ANIM_SPECIAL, 0, 0, 0 }" in output
    assert "{ 100, P2_CUT_ANIM_KICK, S_HIT, 0, 35 }" in output
    assert "{ 110, P2_CUT_ANIM_HK, S_HIT, 0, 80 }" in output
    assert "#define P1_CUT_META_MAX_BYTES 73" in output
    assert "#define P2_CUT_META_MAX_BYTES 73" in output
    assert "p1_frames_all, p1_anims, p1_states, p1_commands, 5, P1_CUT_POSE_COUNT, P1_POSE_BASE, 73" in output
    assert "p2_frames_all, p2_anims, p2_states, p2_commands, 5, P2_CUT_POSE_COUNT, P2_POSE_BASE, 73" in output
    assert report["source_slots"][0]["state_coverage"]["punch"]["source_state"] is None
    assert report["source_slots"][1]["state_coverage"]["punch"]["source_action"] == 160
    assert report["source_slots"][0]["command_coverage"]["hp"]["source_command"] == "z"
    assert report["source_slots"][0]["command_priority"][:3] == ["special", "hp", "lp"]
    assert report["source_slots"][0]["source_limitations"] == ["fixture limitation"]
    assert report["source_slots"][0]["source_routes"] == _shared_source_routes()
    assert report["source_slots"][0]["source_route_pattern_count"] == 2
    assert "controller predicates" in report["source_route_dispatch_contract"]["scope"]
    assert report["unsupported_runtime_roles"]["special"].startswith("projectile")
    assert "static const unsigned short p1_close_distances_q8[AT_N]" in output
    assert report["source_slots"][0]["optional_state_role_coverage"]["punch_close"] == {
        "available": False, "runtime_state_id": 65535, "runtime_flags": "0",
        "runtime_damage": 0, "fallback_role": "punch", "distance_runtime_q8": 0,
    }


def test_runtime_data_rejects_stale_cmd_blob_version(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    p1_data = json.loads(p1.read_text(encoding="utf-8"))
    p1_data["source_routes"] = _shared_source_routes()
    p1_data["source_routes"][0]["source_command_definitions"][0][
        "pattern_blob_hex"] = "02010a012004"
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")
    with pytest.raises(ValueError, match="CMD blob version/encoding"):
        render((p1, p2), scene_header)


def test_runtime_data_rejects_route_pattern_missing_from_c_header(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    p1_data = json.loads(p1.read_text(encoding="utf-8"))
    p1_data["source_routes"] = _shared_source_routes()
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    symbol = route_command_symbol("wave_x", 0)
    scene_header.write_text(
        _header().replace(f"#define P1_{symbol}_SIZE 7\n", ""),
        encoding="ascii")
    with pytest.raises(ValueError, match="missing source route command"):
        render((p1, p2), scene_header)


def test_runtime_data_rejects_route_pattern_bytes_that_differ_from_manifest(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    p1_data = json.loads(p1.read_text(encoding="utf-8"))
    p1_data["source_routes"] = _shared_source_routes()
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(
        _header().replace("4, 1, 10, 1, 32, 4, 0", "4, 1, 10, 1, 32, 4, 1", 1),
        encoding="ascii")
    with pytest.raises(ValueError, match="C bytes disagree with manifest"):
        render((p1, p2), scene_header)


def test_runtime_data_rejects_forged_timed_button_release_blob(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    p1_data = json.loads(p1.read_text(encoding="utf-8"))
    p1_data["source_routes"] = _shared_source_routes()
    definition = p1_data["source_routes"][0]["source_command_definitions"][0]
    definition["source_command_raw"] = "~15x"
    definition["source_command_steps"][0]["keys"][0]["release"] = True
    definition["source_command_steps"][0]["keys"][0]["release_time"] = 15
    definition["pattern_blob_hex"] = "04010a0122060f"
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")
    with pytest.raises(ValueError, match="timed release source shape is unsupported"):
        render((p1, p2), scene_header)


def test_close_attack_role_compiles_source_rule_and_scale_to_q8(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    p2_data = json.loads(p2.read_text())
    p2_data["fighter_scale"] = {"ratio": {"numerator": 72, "denominator": 107}}
    p2_data["runtime_constants"]["ground_front_source"] = 18
    p2.write_text(json.dumps(p2_data), encoding="utf-8")
    data = json.loads(p1.read_text())
    data["roles"].append({"role": "punch_close", "action": 205,
                          "state": 205, "loop_start": None,
                          "frame_count": 3})
    data["close_attack_rules"] = [{
        "role": "punch_close", "command_alias": "lp", "source_command": "x",
        "source_state": 205, "comparison": "lt", "threshold_source_units": 15,
        "source_condition": "P2BodyDist X < 15", "source_line": 573,
    }]
    data["fighter_scale"] = {"ratio": {"numerator": 72, "denominator": 107}}
    data["runtime_constants"].update({
        "ground_front_source": 17, "damage_punch_close": 24,
    })
    data["damage_models"] = [{
        "role": "punch_close", "source_state": 205,
        "source_hitdef_count": 1,
        "runtime_hit_policy": "first_visible_overlap_once",
        "fidelity": "approximate",
        "reason": "one visible overlap is applied per attack",
    }]
    p1.write_text(json.dumps(data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")

    output, report = render((p1, p2), scene_header)

    assert "{ 205, P1_CUT_ANIM_PUNCH_CLOSE, S_HIT, 0, 24 }" in output
    assert "p1_close_distances_q8[AT_N] = { 2584, 0, 0, 0 }" in output
    assert "p1_close_distances_q8, p1_far_distances_q8, 2928" in output
    assert "p2_close_distances_q8[AT_N] = { 0, 0, 0, 0 }" in output
    assert "{ 65535, P2_CUT_ANIM_PUNCH, 0, 0, 0 }" in output
    assert "p2_close_distances_q8, p2_far_distances_q8, 3101" in output
    assert report["source_slots"][1]["ground_front_runtime_q8"] == 3101
    assert report["source_slots"][1]["close_attack_coverage"] == []
    assert report["source_slots"][1]["close_geometry"] == {
        "ground_front_source_units": 18,
        "fighter_scale_ratio": {"numerator": 72, "denominator": 107},
        "ground_front_runtime_q8": 3101,
    }
    assert report["source_slots"][1]["optional_state_role_coverage"]["punch_close"] == {
        "available": False, "runtime_state_id": 65535, "runtime_flags": "0",
        "runtime_damage": 0, "fallback_role": "punch", "distance_runtime_q8": 0,
    }
    assert report["close_geometry_contract"] == {
        "required_when_close_attacks_exist": True,
        "required_when_far_attack_variants_exist": False,
        "ground_front_runtime_q8_by_slot": [2928, 3101],
    }
    close = report["source_slots"][0]["close_attack_coverage"][0]
    assert close["source_condition"] == "P2BodyDist X < 15"
    assert close["threshold_runtime_q8"] == 2584
    assert close["runtime_flags"] == "S_HIT"
    assert close["runtime_damage"] == 24
    assert close["runtime_hit_policy"] == "first_visible_overlap_once"
    assert close["source_hitdef_count"] == 1
    assert close["fidelity"] == "approximate"
    assert close["fidelity_reason"] == "one visible overlap is applied per attack"
    assert report["source_slots"][0]["optional_state_role_coverage"]["punch_close"][
        "source_action"] == 205

    p2_data["runtime_constants"].pop("ground_front_source")
    p2.write_text(json.dumps(p2_data), encoding="utf-8")
    with pytest.raises(ValueError, match="geometry for both runtime slots"):
        render((p1, p2), scene_header)


def test_close_attack_role_fails_closed_without_source_rule_or_scale(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    data = json.loads(p1.read_text())
    data["roles"].append({"role": "punch_close", "action": 205,
                          "state": 205, "loop_start": None,
                          "frame_count": 3})
    data["runtime_constants"].update({
        "ground_front_source": 17, "damage_punch_close": 24,
    })
    data["fighter_scale"] = {"ratio": {"numerator": 72, "denominator": 107}}
    p1.write_text(json.dumps(data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")

    with pytest.raises(ValueError, match="no imported State -1 rule"):
        render((p1, p2), scene_header)


def test_far_attack_fallback_compiles_state_distance_and_damage(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    p1_data = json.loads(p1.read_text())
    p1_data["roles"].append({"role": "punch_far", "action": 201,
                             "state": 201, "loop_start": None,
                             "frame_count": 4})
    p1_data["far_attack_rules"] = [{
        "role": "punch_far", "near_role": "punch", "command_alias": "lp",
        "source_command": "x", "source_state": 201,
        "near_source_state": 200, "comparison": "ge",
        "threshold_source_units": 32,
        "source_condition": "P2BodyDist X >= 32 (ordered fallback after < 32)",
        "source_near_condition": "P2BodyDist X < 32",
        "source_uncompiled_trigger_groups": {"4": ["stateno = 200", "time >= 7"]},
    }]
    p1_data["fighter_scale"] = {"ratio": {"numerator": 72, "denominator": 107}}
    p1_data["runtime_constants"].update({
        "ground_front_source": 18, "damage_punch_far": 18,
    })
    p1_data["damage_models"] = [{
        "role": "punch_far", "source_state": 201,
        "source_hitdef_count": 1,
        "runtime_hit_policy": "first_visible_overlap_once",
        "fidelity": "approximate", "reason": "far damage approximation",
    }]
    p2_data = json.loads(p2.read_text())
    p2_data["fighter_scale"] = {"ratio": {"numerator": 72, "denominator": 107}}
    p2_data["runtime_constants"]["ground_front_source"] = 17
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    p2.write_text(json.dumps(p2_data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")

    output, report = render((p1, p2), scene_header)

    assert "{ 201, P1_CUT_ANIM_PUNCH_FAR, S_HIT, 0, 18 }" in output
    assert "p1_far_distances_q8[AT_N] = { 5512, 0, 0, 0 }" in output
    assert "p2_far_distances_q8[AT_N] = { 0, 0, 0, 0 }" in output
    far = report["source_slots"][0]["far_attack_coverage"][0]
    assert far["source_condition"] == "P2BodyDist X >= 32 (ordered fallback after < 32)"
    assert far["runtime_state_id"] == 201
    assert far["runtime_flags"] == "S_HIT"
    assert far["runtime_damage"] == 18
    assert far["distance_runtime_q8"] == 5512
    assert far["fallback_role"] == "punch"
    assert "4" in far["source_uncompiled_trigger_groups"]
    assert report["source_slots"][1]["ground_front_runtime_q8"] == 2928


def test_all_profiled_far_attack_variants_compile_per_slot(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    p1_data = json.loads(p1.read_text())
    variants = [
        ("punch_far", "punch", "lp", "x", 200, 201, 30),
        ("hp_far", "hp", "hp", "z", 220, 221, 62),
        ("kick_far", "kick", "lk", "a", 230, 231, 35),
        ("hk_far", "hk", "hk", "c", 250, 251, 80),
    ]
    rules, models = [], []
    for role, base, alias, command, near_state, far_state, damage in variants:
        p1_data["roles"].append({
            "role": role, "action": far_state, "state": far_state,
            "loop_start": None, "frame_count": 3,
        })
        rules.append({
            "role": role, "near_role": base, "command_alias": alias,
            "source_command": command, "source_state": far_state,
            "near_source_state": near_state, "comparison": "ge",
            "threshold_source_units": 32,
            "source_condition": "P2BodyDist X >= 32 (ordered fallback after < 32)",
            "source_near_condition": "P2BodyDist X < 32",
            "source_uncompiled_trigger_groups": {"2": ["stateno = 20"]},
            "source_near_uncompiled_trigger_groups": {"3": ["stateno = 21"]},
        })
        p1_data["runtime_constants"][f"damage_{role}"] = damage
        models.append({
            "role": role, "source_state": far_state,
            "source_hitdef_count": 1,
            "runtime_hit_policy": "first_visible_overlap_once",
            "fidelity": "approximate", "reason": "far timing is simplified",
        })
    p1_data["far_attack_rules"] = rules
    p1_data["damage_models"] = models
    p1_data["fighter_scale"] = {"ratio": {"numerator": 72, "denominator": 107}}
    p1_data["runtime_constants"].update({"ground_front_source": 18})
    p2_data = json.loads(p2.read_text())
    p2_data["fighter_scale"] = {"ratio": {"numerator": 72, "denominator": 107}}
    p2_data["runtime_constants"].update({"ground_front_source": 17})
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    p2.write_text(json.dumps(p2_data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")

    output, report = render((p1, p2), scene_header)

    assert "p1_far_distances_q8[AT_N] = { 5512, 5512, 5512, 5512 }" in output
    for role, _base, _alias, _command, _near, state, damage in variants:
        assert f"{{ {state}, P1_CUT_ANIM_{role.upper()}, S_HIT, 0, {damage} }}" in output
    far = report["source_slots"][0]["far_attack_coverage"]
    assert [row["role"] for row in far] == [row[0] for row in variants]
    assert [row["runtime_damage"] for row in far] == [30, 62, 35, 80]
    assert all(row["distance_runtime_q8"] == 5512 for row in far)
    assert all(row["source_uncompiled_trigger_groups"] for row in far)
    assert report["source_slots"][1]["far_distance_q8_values"] == [0, 0, 0, 0]


def test_far_attack_rule_without_distance_geometry_on_other_slot_fails(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    data = json.loads(p1.read_text())
    data["roles"].append({"role": "punch_far", "action": 201,
                          "state": 201, "loop_start": None,
                          "frame_count": 4})
    data["far_attack_rules"] = [{
        "role": "punch_far", "near_role": "punch", "source_command": "x",
        "source_condition": "P2BodyDist X >= 32 (ordered fallback after < 32)",
        "comparison": "ge",
        "threshold_source_units": 32,
    }]
    data["fighter_scale"] = {"ratio": {"numerator": 72, "denominator": 107}}
    data["runtime_constants"].update({
        "ground_front_source": 18, "damage_punch_far": 18,
    })
    data["damage_models"] = [{"role": "punch_far"}]
    p1.write_text(json.dumps(data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")
    with pytest.raises(ValueError, match="geometry for both runtime slots"):
        render((p1, p2), scene_header)


def test_unconsumed_source_roles_are_reported_instead_of_silently_dropped(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    data = json.loads(p1.read_text())
    data["roles"].extend([
        {"role": "punch_unknown_far", "action": 201, "state": 201},
        {"role": "hp_wide_unmapped", "action": 221, "state": 221},
        {"role": "air_lp", "action": 600, "state": 600},
    ])
    p1.write_text(json.dumps(data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")

    output, report = render((p1, p2), scene_header)

    assert "P1_CUT_ANIM_HP_FAR" not in output
    assert report["role_accounting"]["unconsumed_source_roles_by_slot"]["p1"] == [
        {"role": "punch_unknown_far", "source_action": 201, "source_state": 201},
        {"role": "hp_wide_unmapped", "source_action": 221, "source_state": 221},
        {"role": "air_lp", "source_action": 600, "source_state": 600},
    ]
    assert report["unsupported_runtime_roles"]["unconsumed_source_roles"].startswith(
        "source actions are imported as data")


def test_runtime_state_generation_fails_closed_when_required_role_is_missing(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    data = json.loads(p2.read_text())
    data["roles"] = [row for row in data["roles"] if row["role"] != "guard"]
    p2.write_text(json.dumps(data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")

    with pytest.raises(ValueError, match="missing common fight roles"):
        render((p1, p2), scene_header)


def test_runtime_source_routes_require_shared_action_alias(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    data = json.loads(p1.read_text())
    data["source_routes"] = _shared_source_routes()
    data["source_routes"][1]["alias_of"] = None
    p1.write_text(json.dumps(data), encoding="utf-8")
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")

    with pytest.raises(ValueError, match="must alias wave_x"):
        render((p1, p2), scene_header)


def test_runtime_state_generation_fails_closed_without_meta_capacity(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    scene_header = tmp_path / "scene.h"
    scene_header.write_text("\n".join(
        line for line in _header().splitlines() if "META_SIZE" not in line) + "\n",
        encoding="ascii")

    with pytest.raises(ValueError, match="no metasprite sizes"):
        render((p1, p2), scene_header)


def test_runtime_command_generation_fails_closed_when_pattern_is_missing(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2)
    scene_header = tmp_path / "scene.h"
    scene_header.write_text("\n".join(
        line for line in _header().splitlines()
        if "P2_CUT_CMD_HP_SIZE" not in line) + "\n", encoding="ascii")

    with pytest.raises(ValueError, match="missing command pattern P2_CUT_CMD_HP_SIZE"):
        render((p1, p2), scene_header)


def _timing(stop_a, stop_d, hittime, guardtime, airtime, source="ground.hittime"):
    return {
        "stop_a": stop_a, "stop_d": stop_d, "hittime": hittime,
        "guardtime": guardtime, "airtime": airtime,
        "guardtime_source": source, "fidelity": "approximate",
    }


def test_schema_7_emits_per_state_recovery_and_schema_5_stays_compact(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2, 100)
    scene_header = tmp_path / "scene.h"
    scene_header.write_text(_header(), encoding="ascii")
    plain, plain_report = render((p1, p2), scene_header)
    assert "#define FIGHT_RUNTIME_DATA_SCHEMA 5" in plain
    assert plain_report["schema"] == "sms_fight_runtime_data_v5"
    assert "{ 65535, P1_CUT_ANIM_PUNCH, S_HIT, 0, 30 }" in plain

    p1_data = json.loads(p1.read_text())
    p2_data = json.loads(p2.read_text())
    p1_data["hit_timing"] = {"hp": _timing(16, 16, 21, 21, 20)}
    p2_data["hit_timing"] = {"hp": _timing(10, 12, 15, 15, 20)}
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    p2.write_text(json.dumps(p2_data), encoding="utf-8")

    output, report = render((p1, p2), scene_header)

    assert "#define FIGHT_RUNTIME_DATA_SCHEMA 7" in output
    assert report["schema"] == "sms_fight_runtime_data_v7"
    assert "{ 70, P1_CUT_ANIM_HP, S_HIT, 0, 20, 16, 16, 21, 21, 20 }" in output
    assert "{ 70, P2_CUT_ANIM_HP, S_HIT, 0, 20, 10, 12, 15, 15, 20 }" in output
    assert "{ 0, P1_CUT_ANIM_IDLE, S_CONTROL, 0, 0, 0, 0, 0, 0, 0 }" in output
    assert report["hit_recovery_contract"]["fidelity"] == "approximate"
    p1_data.pop("hit_timing")
    p1.write_text(json.dumps(p1_data), encoding="utf-8")
    with pytest.raises(ValueError, match="both runtime slots"):
        render((p1, p2), scene_header)


def test_hit_recovery_uses_authored_times_and_documented_defaults():
    from mugen2sms.generators.scene_cut import hit_recovery

    class Param:
        def __init__(self, name, const):
            self.name = name
            self.const = const

    class Hit:
        source_type = "hitdef"
        params = [
            Param("pausetime[0]", 16), Param("pausetime[1]", 16),
            Param("ground.hittime[0]", 21), Param("air.hittime[0]", 16),
            Param("guard.hittime[0]", None),
        ]

    class Later:
        source_type = "hitdef"
        params = [Param("ground.hittime[0]", 99), Param("pausetime[0]", 1),
                  Param("pausetime[1]", 1)]

    class State:
        controllers = [Hit(), Later()]

    class Character:
        states = {280: State()}

    timing = hit_recovery(Character(), 280)
    assert timing["stop_a"] == 16
    assert timing["stop_d"] == 16
    assert timing["hittime"] == 21
    assert timing["guardtime"] == 21
    assert timing["guardtime_source"] == "ground.hittime"
    assert timing["airtime"] == 16
    assert timing["fidelity"] == "approximate"
