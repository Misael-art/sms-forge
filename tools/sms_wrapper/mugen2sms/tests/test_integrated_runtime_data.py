import json
from pathlib import Path

import pytest

from mugen2sms.converters.sms_cmd import route_command_symbol
from mugen2sms.generators.integrated_runtime_data import (
    namespace_slot_actors,
    render,
)


ROLE_NAMES = (
    "idle", "walk_f", "walk_b", "jump", "crouch", "guard", "punch",
    "hp", "special", "ko", "kick", "hk", "alternate_punch",
)
RUNTIME_ROLES = ROLE_NAMES[:12]
CONSTANTS = {
    "life": 1000, "walk_fwd": 512, "walk_back": -460,
    "jump_vy": 2585, "gravity": 110, "damage_punch": 30,
    "damage_hp": 20, "damage_kick": 35, "damage_hk": 80,
    "damage_special": 105, "special_vel": 512,
    "input_threshold_key1": 6, "input_threshold_key2": 6,
    "hitstop": 8, "hit_push": 3, "guard_push": 5,
}


def _manifest(path: Path, action_delta: int = 0, life: int = 1000) -> None:
    roles = []
    for index, name in enumerate(ROLE_NAMES):
        action = index * 10 + action_delta
        roles.append({
            "role": name,
            "action": action,
            "state": action if name in {"punch", "hp", "special", "ko",
                                         "kick", "hk"} else None,
            "loop_start": 0 if name in {"idle", "walk_f", "walk_b", "crouch", "guard"} else None,
            "frame_count": 1,
        })
    data = {
        "source_sha256": ("a" if action_delta == 0 else "b") * 64,
        "source_def": "fighter.def",
        "roles": roles,
        "source_limitations": ["fixture limitation"],
        "source_routes": [
            {"route_id": "wave_x", "source_command_terms": ["wave_x"],
             "source_controller_type": "changestate", "source_controller_line": 40,
             "source_triggerall": ['command = "wave_x"'],
             "source_triggers": {"1": ["ctrl = 1"]},
             "source_state": 80 + action_delta,
             "source_action": 80 + action_delta,
             "action_role": "special", "alias_of": None,
             "source_command_definitions": [_command_definition("wave_x", 10, "wave_x")],
             "command_pattern_coverage": "complete",
             "unrepresented_command_patterns": []},
            {"route_id": "wave_y", "source_command_terms": ["wave_y"],
             "source_controller_type": "changestate", "source_controller_line": 55,
             "source_triggerall": ['command = "wave_y"'],
             "source_triggers": {"1": ["ctrl = 1"]},
             "source_state": 81 + action_delta,
             "source_action": 80 + action_delta,
             "action_role": "special", "alias_of": "wave_x",
             "source_command_definitions": [_command_definition("wave_y", 11, "wave_y")],
             "command_pattern_coverage": "complete",
             "unrepresented_command_patterns": []},
        ],
        "commands": {"special": "236_x", "lp": "x", "hp": "z",
                     "lk": "a", "hk": "c"},
        "runtime_constants": dict(CONSTANTS, life=life),
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def _command_definition(term: str, line: int, route_id: str) -> dict:
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


def _header() -> str:
    lines = []
    actions = []
    for prefix, actor, delta, base in (
            ("P1", "p1", 0, 0), ("P2", "p2", 100, 13)):
        lines += [f"#define {prefix}_CUT_POSE_COUNT 13",
                  f"#define {prefix}_FIXTURE_META_SIZE 73",
                  f"#define {prefix}_POSE_BASE {base}"]
        for index, role in enumerate(ROLE_NAMES):
            lines.append(f"#define {prefix}_CUT_ANIM_{role.upper()} {index}")
        for role in ("SPECIAL", "LP", "HP", "LK", "HK"):
            lines.append(f"#define {prefix}_CUT_CMD_{role}_SIZE 7")
        for route_id in ("wave_x", "wave_y"):
            symbol = route_command_symbol(route_id, 0)
            blob = bytes.fromhex("04010a01200400")
            lines.append(f"#define {prefix}_{symbol}_SIZE {len(blob)}")
            lines.append(f"const unsigned char {prefix}_{symbol}[{len(blob)}] = "
                         "{ " + ", ".join(str(value) for value in blob) + " };")
        lines.append(f"static const Frame {actor}_frames_all[13] = {{}};")
        lines.append(f"static const Anim {actor}_anims[13] = {{")
        for index in range(13):
            actions.append(f"    {{ {index * 10 + delta}u, 1u, 0u, "
                            f"{actor}_frames_all + {index}u }},")
        lines.extend(actions[-13:])
        lines.append("};")
    return "\n".join(lines) + "\n"


def _supporting_headers(tmp_path: Path) -> tuple[Path, Path]:
    frame = tmp_path / "source_frame_data.h"
    pose = tmp_path / "pose_table.h"
    frame.write_text("\n".join(
        f"#define {prefix}_{name} 1u"
        for prefix in ("KEN", "RYU")
        for name in ("FRAME_DATA_BANK", "FRAME_DATA_OFF")) + "\n",
        encoding="ascii")
    pose.write_text("\n".join(
        f"#define {prefix}_{name} 1u"
        for prefix in ("KEN", "RYU")
        for name in ("POSE_INDEX_BANK", "POSE_META_BANK", "POSE_INDEX_OFF")) + "\n",
        encoding="ascii")
    return frame, pose


def test_integrated_tables_bind_each_slot_and_report_unconsumed_roles(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2, action_delta=100, life=900)
    header = tmp_path / "scene.h"
    header.write_text(namespace_slot_actors(_header()), encoding="ascii")
    frame, pose = _supporting_headers(tmp_path)

    output, report = render((p1, p2), header, frame, pose)

    assert "static const StateDef p1_states[ST_N_STATES]" in output
    assert "static const FightSourceRouteDef p1_source_routes[]" in output
    assert (f"{{ KEN_{route_command_symbol('wave_x', 0)}, 80, 80, "
            "KEN_CUT_ANIM_SPECIAL }") in output
    assert (f"{{ KEN_{route_command_symbol('wave_y', 0)}, 81, 80, "
            "KEN_CUT_ANIM_SPECIAL }") in output
    assert "#define P1_SOURCE_ROUTE_PATTERN_COUNT 2" in output
    assert "{ 60, KEN_CUT_ANIM_PUNCH, S_HIT, 0, 30 }" in output
    assert "{ 170, RYU_CUT_ANIM_HP, S_HIT, 0, 20 }" in output
    assert "{ 180, RYU_CUT_ANIM_SPECIAL, 0, 0, 0 }" in output
    assert "{ ken_anims, p1_states, KEN_CUT_POSE_COUNT, KEN_POSE_BASE" in output
    assert "{ ryu_anims, p2_states, RYU_CUT_POSE_COUNT, RYU_POSE_BASE" in output
    assert "900, 2585, 110, 8, 3, 5" in output
    assert report["role_accounting"]["unconsumed_source_roles_by_slot"]["p1"] == [
        {"role": "alternate_punch", "source_action": 120, "source_state": None},
    ]
    assert "integrated_character_initializer" in report["source_slots"][0]
    assert "ken_anims, p1_states" in report["source_slots"][0][
        "integrated_character_initializer"]
    assert report["source_slots"][0]["source_limitations"] == [
        "fixture limitation"]
    assert [route["source_state"] for route in
            report["source_slots"][0]["source_routes"]] == [80, 81]
    assert report["source_slots"][0]["source_routes"][1]["source_action"] == 80
    assert report["source_slots"][0]["source_route_pattern_count"] == 2
    assert report["source_route_dispatch_contract"]["compiled_tables"] == [
        "p1_source_routes", "p2_source_routes"]
    assert report["runtime_actor_alias_scope"].startswith("legacy C storage")
    assert report["source_identity_by_slot"]["p1"] == {
        "source_def": "fighter.def", "source_sha256": "a" * 64}
    assert report["source_identity_by_slot"]["p2"] == {
        "source_def": "fighter.def", "source_sha256": "b" * 64}


def test_integrated_table_rejects_manifest_action_that_disagrees_with_anim(tmp_path):
    p1, p2 = tmp_path / "p1.json", tmp_path / "p2.json"
    _manifest(p1)
    _manifest(p2, action_delta=100)
    header_text = namespace_slot_actors(_header())
    header = tmp_path / "scene.h"
    header.write_text(header_text.replace("{ 60u, 1u", "{ 61u, 1u", 1),
                      encoding="ascii")
    frame, pose = _supporting_headers(tmp_path)

    with pytest.raises(ValueError, match="role punch expects action 60"):
        render((p1, p2), header, frame, pose)


def test_slot_namespace_mapping_is_complete_for_generated_identifiers():
    source = ("#define P1_CUT_ANIM_IDLE 0\nstatic const Anim p2_anims[1];\n"
              "#define FRAME_P2_TILES_BANK 7\n")
    result = namespace_slot_actors(source)
    assert "KEN_CUT_ANIM_IDLE" in result
    assert "ryu_anims" in result
    assert "#define P1_" not in result and "#define P2_" not in result
    assert "Anim p2_" not in result
    assert "FRAME_P2_TILES_BANK" in result
