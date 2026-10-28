"""Compile the supported common fight-state table from versus scene manifests.

This is a deliberately small runtime contract, not a general CNS interpreter.
Each character must declare every visual role consumed by the current generic
fight loop. State ids absent from the source cut remain 0xFFFF in the emitted
table; action ids remain in the generated Anim records.
"""
from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from ..converters.sms_cmd import (
    BLOB_FMT_VERSION, DIAGONALS, DIR_BITS, route_command_symbol,
)


REQUIRED_ROLES = (
    "idle", "walk_f", "walk_b", "jump", "crouch", "guard",
    "punch", "hp", "special", "ko", "kick", "hk",
)

OPTIONAL_ATTACK_ROLE_SPECS = (
    ("punch_close", "punch", "damage_punch_close"),
    ("hp_close", "hp", "damage_hp_close"),
    ("kick_close", "kick", "damage_kick_close"),
    ("hk_close", "hk", "damage_hk_close"),
)
OPTIONAL_FAR_ATTACK_ROLE_SPECS = (
    ("punch_far", "punch", "damage_punch_far"),
    ("hp_far", "hp", "damage_hp_far"),
    ("kick_far", "kick", "damage_kick_far"),
    ("hk_far", "hk", "damage_hk_far"),
)

STATE_ROLE_ORDER = (REQUIRED_ROLES +
                    tuple(spec[0] for spec in OPTIONAL_ATTACK_ROLE_SPECS) +
                    tuple(spec[0] for spec in OPTIONAL_FAR_ATTACK_ROLE_SPECS))

# Compounds and stronger tiers consume a pulse, so test them before weaker
# terminal-button commands.
COMMAND_ROLE_SPECS = (
    ("special", "FIGHT_CMD_SPECIAL_UNSUPPORTED"),
    ("hp", "FIGHT_CMD_HP"),
    ("lp", "FIGHT_CMD_LP"),
    ("hk", "FIGHT_CMD_HK"),
    ("lk", "FIGHT_CMD_LK"),
)


def _macro_role(header: str, prefix: str, role: str) -> str:
    macro = f"{prefix}_CUT_ANIM_{role.upper()}"
    if not re.search(rf"^#define\s+{re.escape(macro)}\s+\d+\s*$", header, re.M):
        raise ValueError(f"generated scene header is missing required role {macro}")
    return macro


def _meta_capacity(header: str, prefix: str) -> int:
    sizes = [int(value) for value in re.findall(
        rf"^#define\s+{re.escape(prefix)}_[A-Za-z0-9_]+_META_SIZE\s+(\d+)\s*$",
        header, re.M)]
    if not sizes:
        raise ValueError(f"generated scene header has no metasprite sizes for {prefix}")
    capacity = max(sizes)
    if not 1 <= capacity <= 255:
        raise ValueError(f"{prefix} maximum metasprite size outside uint8: {capacity}")
    return capacity


def _source_command_bytes(header: str, symbol: str,
                          seen: set[str] | None = None) -> bytes:
    """Read a generated CMD array, following an exact C alias when deduped."""
    seen = set() if seen is None else seen
    if symbol in seen:
        raise ValueError(f"generated CMD array alias cycle at {symbol}")
    seen.add(symbol)
    array = re.search(
        rf"^\s*(?:static\s+)?const\s+unsigned\s+char\s+"
        rf"{re.escape(symbol)}\s*\[\s*(\d+)\s*\]\s*=\s*\{{(.*?)\}}\s*;",
        header, re.M | re.S)
    if array is None:
        alias = re.search(
            rf"^#define\s+{re.escape(symbol)}\s+([A-Za-z_]\w*)\s*$",
            header, re.M)
        if alias is None:
            raise ValueError(f"generated CMD array is missing {symbol}")
        return _source_command_bytes(header, alias.group(1), seen)
    size = int(array.group(1))
    body = array.group(2)
    tokens = re.findall(r"0x[0-9A-Fa-f]+|\b\d+\b", body)
    residue = re.sub(r"0x[0-9A-Fa-f]+|\b\d+\b", "", body)
    if residue.strip(" ,\t\r\n") or len(tokens) != size:
        raise ValueError(f"generated CMD array {symbol} has malformed bytes")
    values = [int(token, 0) for token in tokens]
    if any(value > 0xFF for value in values):
        raise ValueError(f"generated CMD array {symbol} has a byte outside uint8")
    return bytes(values)


def _state_id(role: dict) -> int:
    value = role.get("state")
    if value is None:
        return 0xFFFF
    value = int(value)
    if not 0 <= value <= 0xFFFF:
        raise ValueError(f"source state id outside uint16: {value}")
    return value


def _source_routes(manifest_path: Path, manifest: dict,
                   by_role: dict[str, dict]) -> list[dict]:
    routes = manifest.get("source_routes", [])
    if not isinstance(routes, list):
        raise ValueError(f"{manifest_path}: source_routes must be a list")
    route_by_id = {}
    canonical_by_role = {}
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError(f"{manifest_path}: each source route must be an object")
        route_id = route.get("route_id")
        action_role = route.get("action_role")
        source_action = route.get("source_action")
        source_state = route.get("source_state")
        source_line = route.get("source_controller_line")
        command_terms = route.get("source_command_terms")
        triggerall = route.get("source_triggerall")
        trigger_groups = route.get("source_triggers")
        state_resolution = route.get("source_state_resolution")
        command_assignment = route.get("source_command_assignment")
        alias_of = route.get("alias_of")
        if (not isinstance(route_id, str) or not route_id.strip() or
                route_id in route_by_id):
            raise ValueError(f"{manifest_path}: source route ids must be unique strings")
        if not isinstance(action_role, str) or action_role not in by_role:
            raise ValueError(f"{manifest_path}: {route_id} references an unknown action role")
        if (type(source_action) is not int or not 0 <= source_action <= 0xFFFF or
                type(source_state) is not int or not 0 <= source_state <= 0xFFFF):
            raise ValueError(f"{manifest_path}: {route_id} state/action must be uint16")
        if type(source_line) is not int or source_line <= 0:
            raise ValueError(f"{manifest_path}: {route_id} controller line must be positive")
        if route.get("source_controller_type") != "changestate":
            raise ValueError(f"{manifest_path}: {route_id} is not a ChangeState route")
        if by_role[action_role].get("action") != source_action:
            raise ValueError(f"{manifest_path}: {route_id} action does not match role {action_role}")
        if (not isinstance(command_terms, list) or not command_terms or
                any(not isinstance(term, str) or not term.strip()
                    for term in command_terms)):
            raise ValueError(f"{manifest_path}: {route_id} command terms are malformed")
        if (not isinstance(triggerall, list) or
                any(not isinstance(term, str) for term in triggerall) or
                not isinstance(trigger_groups, dict) or
                any(not isinstance(group, list) or
                    any(not isinstance(term, str) for term in group)
                    for group in trigger_groups.values())):
            raise ValueError(f"{manifest_path}: {route_id} source trigger data is malformed")
        trigger_text = triggerall + [
            term for group in trigger_groups.values() for term in group]
        if (state_resolution is None) != (command_assignment is None):
            raise ValueError(
                f"{manifest_path}: {route_id} variable resolution/assignment must appear together")
        command_text = trigger_text
        if state_resolution is not None:
            if (not isinstance(state_resolution, dict) or
                    state_resolution.get("kind") != "varset_constant"):
                raise ValueError(f"{manifest_path}: {route_id} variable resolution is malformed")
            expression = state_resolution.get("change_state_expression")
            variable = state_resolution.get("source_variable")
            setter_line = state_resolution.get("setter_controller_line")
            setter_value = state_resolution.get("setter_value")
            expression_match = (re.fullmatch(
                r"\s*var\s*\(\s*(\d+)\s*\)\s*", expression, re.I)
                if isinstance(expression, str) else None)
            if (expression_match is None or type(variable) is not int or
                    int(expression_match.group(1)) != variable or
                    type(setter_line) is not int or setter_line <= 0 or
                    type(setter_value) is not int or setter_value != source_state):
                raise ValueError(f"{manifest_path}: {route_id} variable resolution disagrees")
            if (not isinstance(command_assignment, dict) or
                    command_assignment.get("source_controller_type") != "varset" or
                    type(command_assignment.get("source_controller_line")) is not int or
                    command_assignment.get("source_controller_line") != setter_line or
                    type(command_assignment.get("source_variable")) is not int or
                    command_assignment.get("source_variable") != variable or
                    type(command_assignment.get("source_value")) is not int or
                    command_assignment.get("source_value") != source_state):
                raise ValueError(f"{manifest_path}: {route_id} VarSet assignment is malformed")
            assignment_all = command_assignment.get("source_triggerall")
            assignment_groups = command_assignment.get("source_triggers")
            if (not isinstance(assignment_all, list) or
                    any(not isinstance(term, str) for term in assignment_all) or
                    not isinstance(assignment_groups, dict) or
                    any(not isinstance(group, list) or
                        any(not isinstance(term, str) for term in group)
                        for group in assignment_groups.values())):
                raise ValueError(f"{manifest_path}: {route_id} VarSet triggers are malformed")
            command_text = assignment_all + [
                term for group in assignment_groups.values() for term in group]
        actual_terms = {
            term.strip().casefold()
            for condition in command_text
            for term in re.findall(
                r"\bcommand\s*=\s*[\"']([^\"']+)[\"']",
                condition, re.IGNORECASE)
        }
        if any(term.strip().casefold() not in actual_terms for term in command_terms):
            raise ValueError(f"{manifest_path}: {route_id} command terms are absent from triggers")

        definitions = route.get("source_command_definitions")
        if not isinstance(definitions, list) or not definitions:
            raise ValueError(f"{manifest_path}: {route_id} has no source [Command] definitions")
        defined_terms = set()
        definition_lines = set()
        unrepresented_patterns = []
        for definition_index, definition in enumerate(definitions):
            if not isinstance(definition, dict):
                raise ValueError(f"{manifest_path}: {route_id} command definition is malformed")
            term = definition.get("source_command_term")
            name = definition.get("source_command")
            line = definition.get("source_command_line")
            raw = definition.get("source_command_raw")
            time = definition.get("source_command_time")
            buffer_time = definition.get("source_command_buffer_time")
            errors = definition.get("source_command_errors")
            steps = definition.get("source_command_steps")
            status = definition.get("conversion_status")
            reason = definition.get("conversion_reason")
            blob_hex = definition.get("pattern_blob_hex")
            if (not isinstance(term, str) or term.strip().casefold() not in
                    {value.strip().casefold() for value in command_terms} or
                    not isinstance(name, str) or name.strip().casefold() !=
                    term.strip().casefold()):
                raise ValueError(f"{manifest_path}: {route_id} command definition name mismatches")
            if type(line) is not int or line <= 0 or line in definition_lines:
                raise ValueError(f"{manifest_path}: {route_id} command definition line is invalid")
            definition_lines.add(line)
            if (not isinstance(raw, str) or type(time) is not int or
                    not 0 <= time <= 0xFF or type(buffer_time) is not int or
                    not 0 <= buffer_time <= 0xFF):
                raise ValueError(f"{manifest_path}: {route_id} command timing/raw data is invalid")
            if (not isinstance(errors, list) or
                    any(not isinstance(error, str) for error in errors) or
                    not isinstance(steps, list)):
                raise ValueError(f"{manifest_path}: {route_id} parsed command steps are malformed")
            timed_release_keys = []
            for step_index, step in enumerate(steps):
                if (not isinstance(step, dict) or type(step.get("strict")) is not bool or
                        not isinstance(step.get("keys"), list) or not step["keys"]):
                    raise ValueError(f"{manifest_path}: {route_id} parsed command step is malformed")
                for key in step["keys"]:
                    if (not isinstance(key, dict) or not isinstance(key.get("key"), str) or
                            any(type(key.get(flag)) is not bool
                                for flag in ("release", "hold", "four_way")) or
                            type(key.get("release_time")) is not int or
                            not 0 <= key["release_time"] <= 0xFF):
                        raise ValueError(f"{manifest_path}: {route_id} parsed command key is malformed")
                    if key["release_time"]:
                        timed_release_keys.append((step_index, step, key))
            if status == "represented":
                if definition.get("runtime_command_symbol") != route_command_symbol(
                        route_id, definition_index):
                    raise ValueError(
                        f"{manifest_path}: {route_id} command artifact symbol is missing or stale")
                if timed_release_keys:
                    if (len(timed_release_keys) != 1 or
                            timed_release_keys[0][0] != 0 or
                            len(timed_release_keys[0][1]["keys"]) != 1 or
                            timed_release_keys[0][1]["strict"] or
                            timed_release_keys[0][2]["key"] not in DIR_BITS or
                            not timed_release_keys[0][2]["release"] or
                            timed_release_keys[0][2]["hold"]):
                        raise ValueError(
                            f"{manifest_path}: {route_id} timed release source shape is unsupported")
                if not isinstance(blob_hex, str) or not blob_hex or reason is not None:
                    raise ValueError(f"{manifest_path}: {route_id} represented command blob is invalid")
                try:
                    blob = bytes.fromhex(blob_hex)
                except ValueError as exc:
                    raise ValueError(f"{manifest_path}: {route_id} command blob is not hex") from exc
                if (blob.hex() != blob_hex.lower() or len(blob) < 4 or
                        blob[0] != BLOB_FMT_VERSION):
                    raise ValueError(
                        f"{manifest_path}: {route_id} CMD blob version/encoding is invalid")
                if (blob[1] != len(steps) or len(blob) != 4 + 3 * len(steps) or
                        blob[2] != (time & 0xFF) or
                        blob[3] != (buffer_time & 0xFF)):
                    raise ValueError(
                        f"{manifest_path}: {route_id} CMD blob shape/timing disagrees with source")
                for index, step in enumerate(steps):
                    want = blob[4 + 3 * index]
                    flags = blob[5 + 3 * index]
                    release_time = blob[6 + 3 * index]
                    expected_release_time = max(
                        (key["release_time"] for key in step["keys"]), default=0)
                    expected_four_way = any(
                        key["four_way"] and key["key"] in (DIR_BITS | DIAGONALS)
                        for key in step["keys"])
                    if (want & 0xC0 or flags & 0xE0 or
                            ((flags >> 2) & 3) > 2 or
                            release_time != expected_release_time or
                            (release_time and not (flags & 2)) or
                            bool(flags & 0x10) != expected_four_way):
                        raise ValueError(
                            f"{manifest_path}: {route_id} CMD blob step flags disagree with runtime")
            elif status == "unsupported":
                if definition.get("runtime_command_symbol") is not None:
                    raise ValueError(
                        f"{manifest_path}: unsupported {route_id} command has a runtime artifact")
                if blob_hex is not None or not isinstance(reason, str) or not reason:
                    raise ValueError(f"{manifest_path}: {route_id} unsupported command reason is missing")
                unrepresented_patterns.append({
                    "source_command_term": term,
                    "source_command_line": line,
                    "reason": reason,
                })
            else:
                raise ValueError(f"{manifest_path}: {route_id} command conversion status is invalid")
            defined_terms.add(term.strip().casefold())
        missing_definitions = [term for term in command_terms
                              if term.strip().casefold() not in defined_terms]
        if missing_definitions:
            raise ValueError(
                f"{manifest_path}: {route_id} lacks definitions for {missing_definitions}")
        expected_coverage = "incomplete" if unrepresented_patterns else "complete"
        if route.get("command_pattern_coverage") != expected_coverage:
            raise ValueError(f"{manifest_path}: {route_id} command coverage disagrees with definitions")
        if route.get("unrepresented_command_patterns") != unrepresented_patterns:
            raise ValueError(f"{manifest_path}: {route_id} unsupported command list disagrees")

        canonical_id = canonical_by_role.get(action_role)
        if canonical_id is None:
            if alias_of is not None:
                raise ValueError(f"{manifest_path}: first {action_role} route cannot be an alias")
            canonical_by_role[action_role] = route_id
        elif alias_of != canonical_id:
            raise ValueError(f"{manifest_path}: {route_id} must alias {canonical_id}")
        elif (alias_of not in route_by_id or
              route_by_id[alias_of].get("source_action") != source_action):
            raise ValueError(f"{manifest_path}: {route_id} alias has a different AIR action")
        route_by_id[route_id] = route
    return routes


def _scaled_source_q8(value: int, ratio: dict, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    if not isinstance(ratio, dict):
        raise ValueError(f"{label} requires a uniform fighter scale ratio")
    numerator = ratio.get("numerator")
    denominator = ratio.get("denominator")
    if (type(numerator) is not int or type(denominator) is not int or
            numerator <= 0 or denominator <= 0):
        raise ValueError(f"{label} has an invalid fighter scale ratio")
    # Runtime positions are Q8.8. Preserve source fractions at that precision
    # and round half up, without introducing floating point.
    scaled = (value * numerator * 256 + denominator // 2) // denominator
    if scaled > 0x7FFF:
        raise ValueError(f"{label} exceeds signed-distance Q8.8 range")
    return scaled


_RECOVERY_KEYS = ("stop_a", "stop_d", "hittime", "guardtime", "airtime")


def _parse_hit_timing(manifest_path: Path, raw) -> dict | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"{manifest_path}: hit_timing must be an object")
    parsed = {}
    for role, row in raw.items():
        if not isinstance(role, str) or not isinstance(row, dict):
            raise ValueError(f"{manifest_path}: hit_timing entries must be objects")
        if role in parsed:
            raise ValueError(f"{manifest_path}: duplicate hit_timing {role}")
        values = {}
        for key in _RECOVERY_KEYS:
            value = row.get(key, 0)
            if type(value) is not int or not 0 <= value <= 255:
                raise ValueError(
                    f"{manifest_path}: hit_timing.{role}.{key} must be a uint8")
            values[key] = value
        values["guardtime_source"] = row.get("guardtime_source")
        values["fidelity"] = row.get("fidelity", "approximate")
        parsed[role] = values
    return parsed


def _recovery_suffix(hit_timing: dict | None, role: str) -> str:
    if hit_timing is None:
        return ""
    row = hit_timing.get(role, {})
    return ", " + ", ".join(str(int(row.get(key, 0))) for key in _RECOVERY_KEYS)


def _slot_rows(manifest_path: Path, header: str,
               prefix: str) -> tuple[list[str], list[str], dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    roles = manifest.get("roles")
    if not isinstance(roles, list):
        raise ValueError(f"{manifest_path}: roles must be a list")
    by_role = {}
    for role in roles:
        if not isinstance(role, dict):
            raise ValueError(f"{manifest_path}: each role must be an object")
        name = role.get("role")
        if not isinstance(name, str) or name in by_role:
            raise ValueError(f"{manifest_path}: role names must be unique strings")
        by_role[name] = role
    missing = [name for name in REQUIRED_ROLES if name not in by_role]
    if missing:
        raise ValueError(f"{manifest_path}: missing common fight roles {missing}")
    source_routes = _source_routes(manifest_path, manifest, by_role)
    for route in source_routes:
        for definition in route["source_command_definitions"]:
            symbol = definition.get("runtime_command_symbol")
            if symbol is None:
                continue
            size_symbol = f"{prefix}_{symbol}_SIZE"
            size_match = re.search(
                rf"^#define\s+{re.escape(size_symbol)}\s+(\d+)\s*$",
                header, re.M)
            if size_match is None:
                raise ValueError(
                    f"generated scene header is missing source route command {size_symbol}")
            expected_blob = bytes.fromhex(definition["pattern_blob_hex"])
            if int(size_match.group(1)) != len(expected_blob):
                raise ValueError(
                    f"generated source route command {size_symbol} size disagrees with CMD blob")
            if _source_command_bytes(header, f"{prefix}_{symbol}") != expected_blob:
                raise ValueError(
                    f"{manifest_path}: {route['route_id']} source route CMD C bytes disagree with manifest")

    constants = manifest.get("runtime_constants")
    required_constants = (
        "life", "walk_fwd", "walk_back", "jump_vy", "gravity",
        "damage_punch", "damage_hp", "damage_kick", "damage_hk",
        "damage_special", "special_vel", "input_threshold_key1",
        "input_threshold_key2",
        "hitstop", "hit_push", "guard_push",
    )
    if not isinstance(constants, dict) or any(key not in constants for key in required_constants):
        raise ValueError(f"{manifest_path}: incomplete runtime_constants")
    damage_models_source = manifest.get("damage_models", [])
    if not isinstance(damage_models_source, list):
        raise ValueError(f"{manifest_path}: damage_models must be a list")
    damage_models = {}
    for model in damage_models_source:
        if not isinstance(model, dict) or not isinstance(model.get("role"), str):
            raise ValueError(f"{manifest_path}: damage model requires a role")
        if model["role"] in damage_models:
            raise ValueError(f"{manifest_path}: duplicate damage model {model['role']}")
        damage_models[model["role"]] = model
    hit_timing = _parse_hit_timing(manifest_path, manifest.get("hit_timing"))
    macros = {name: _macro_role(header, prefix, name) for name in REQUIRED_ROLES}
    meta_capacity = _meta_capacity(header, prefix)
    # source_state_id, animation index, semantic flags, velocity Q8.8, damage
    specs = (
        ("idle", "S_CONTROL", "0", "0"),
        ("walk_f", "S_CONTROL", "walk_fwd", "0"),
        ("walk_b", "S_CONTROL", "walk_back", "0"),
        ("jump", "S_AIR", "0", "0"),
        ("crouch", "S_CONTROL | S_BLOCKABLE", "0", "0"),
        ("guard", "S_CONTROL | S_BLOCKABLE", "0", "0"),
        ("punch", "S_HIT", "0", "damage_punch"),
        ("hp", "S_HIT", "0", "damage_hp"),
        # A projectile is not a direct strike. Keep its source animation in
        # the data, but compile no hit flag until projectile support exists.
        ("special", "0", "0", "0"),
        ("ko", "0", "0", "0"),
        ("kick", "S_HIT", "0", "damage_kick"),
        ("hk", "S_HIT", "0", "damage_hk"),
    )
    rows = []
    state_coverage = {}
    for name, flags, vel_key, dmg_key in specs:
        row = by_role[name]
        vel = constants.get(vel_key, 0) if vel_key not in ("0",) else 0
        dmg = constants.get(dmg_key, 0) if dmg_key not in ("0",) else 0
        vel, dmg = int(vel), int(dmg)
        if not -32768 <= vel <= 32767:
            raise ValueError(f"{manifest_path}: {name} velocity outside int16")
        if not 0 <= dmg <= 255:
            raise ValueError(f"{manifest_path}: {name} damage outside uint8")
        rows.append(
            f"    {{ {_state_id(row)}, {macros[name]}, {flags}, {vel}, {dmg}"
            f"{_recovery_suffix(hit_timing, name)} }},")
        state_coverage[name] = {
            "available": True,
            "source_action": int(row["action"]),
            "source_state": None if row.get("state") is None else int(row["state"]),
        }

    close_rules_source = manifest.get("close_attack_rules", [])
    if not isinstance(close_rules_source, list):
        raise ValueError(f"{manifest_path}: close_attack_rules must be a list")
    supported_close_roles = {spec[0] for spec in OPTIONAL_ATTACK_ROLE_SPECS}
    close_rules = {}
    for rule in close_rules_source:
        if not isinstance(rule, dict):
            raise ValueError(f"{manifest_path}: each close attack rule must be an object")
        name = rule.get("role")
        if (not isinstance(name, str) or name not in supported_close_roles or
                name in close_rules):
            raise ValueError(
                f"{manifest_path}: close attack rule roles must be unique and supported")
        if rule.get("comparison") != "lt":
            raise ValueError(f"{manifest_path}: close attack comparison must be strict less-than")
        close_rules[name] = rule

    scale_profile = manifest.get("fighter_scale", {})
    scale_ratio = scale_profile.get("ratio") if isinstance(scale_profile, dict) else None
    close_distance_values = [0] * len(OPTIONAL_ATTACK_ROLE_SPECS)
    close_rows = []
    close_role_coverage = {}
    close_attack_coverage = []
    ground_front_q8 = 0
    has_close_role = False
    front_source = constants.get("ground_front_source")
    if front_source is not None:
        if type(front_source) is not int or front_source <= 0:
            raise ValueError(f"{manifest_path}: ground_front_source must be positive")
        ground_front_q8 = _scaled_source_q8(
            front_source, scale_ratio, f"{manifest_path}: ground.front")
    for index, (name, base_role, damage_key) in enumerate(OPTIONAL_ATTACK_ROLE_SPECS):
        row = by_role.get(name)
        rule = close_rules.get(name)
        if row is None:
            if rule is not None:
                raise ValueError(f"{manifest_path}: close rule {name} has no source role")
            close_rows.append(
                f"    {{ 65535, {macros[base_role]}, 0, 0, 0"
                f"{_recovery_suffix(hit_timing, name)} }},")
            close_role_coverage[name] = {
                "available": False,
                "runtime_state_id": 0xFFFF,
                "runtime_flags": "0",
                "runtime_damage": 0,
                "fallback_role": base_role,
                "distance_runtime_q8": 0,
            }
            state_coverage[name] = {"available": False}
            continue
        has_close_role = True
        if rule is None:
            raise ValueError(f"{manifest_path}: close role {name} has no imported State -1 rule")
        if front_source is None:
            raise ValueError(
                f"{manifest_path}: close roles require positive ground_front_source")
        if row.get("state") is None:
            raise ValueError(f"{manifest_path}: close role {name} requires a source state id")
        threshold_source = rule.get("threshold_source_units")
        if type(threshold_source) is not int or threshold_source <= 0:
            raise ValueError(f"{manifest_path}: {name} threshold must be a positive integer")
        threshold_q8 = _scaled_source_q8(
            threshold_source, scale_ratio, f"{manifest_path}: {name} threshold")
        close_distance_values[index] = threshold_q8
        damage = constants.get(damage_key)
        if type(damage) is not int or not 0 <= damage <= 255:
            raise ValueError(f"{manifest_path}: {damage_key} must be uint8 for {name}")
        damage_model = damage_models.get(name)
        if damage_model is None:
            raise ValueError(f"{manifest_path}: close role {name} has no damage model")
        role_macro = _macro_role(header, prefix, name)
        close_rows.append(
            f"    {{ {_state_id(row)}, {role_macro}, S_HIT, 0, {damage}"
            f"{_recovery_suffix(hit_timing, name)} }},")
        source_command = rule.get("source_command")
        source_condition = rule.get("source_condition")
        if not isinstance(source_command, str) or not isinstance(source_condition, str):
            raise ValueError(f"{manifest_path}: {name} source rule is incomplete")
        coverage = {
            "role": name,
            "available": True,
            "source_action": int(row["action"]),
            "source_state": int(row["state"]),
            "runtime_state_id": int(row["state"]),
            "runtime_flags": "S_HIT",
            "runtime_damage": damage,
            "runtime_hit_policy": damage_model.get("runtime_hit_policy"),
            "source_hitdef_count": damage_model.get("source_hitdef_count"),
            "fidelity": damage_model.get("fidelity"),
            "fidelity_reason": damage_model.get("reason"),
            "fallback_role": base_role,
            "distance_runtime_q8": threshold_q8,
            "source_command": source_command,
            "source_condition": source_condition,
            "threshold_source_units": threshold_source,
            "threshold_runtime_q8": threshold_q8,
        }
        close_role_coverage[name] = coverage
        close_attack_coverage.append(coverage)
        state_coverage[name] = {
            "available": True,
            "source_action": int(row["action"]),
            "source_state": int(row["state"]),
        }
    if set(close_rules) - {name for name in by_role if name in supported_close_roles}:
        raise ValueError(f"{manifest_path}: close rules do not match declared source roles")
    if has_close_role:
        for name in close_rules:
            if name not in by_role:
                raise ValueError(f"{manifest_path}: missing source role for close rule {name}")
    rows.extend(close_rows)

    far_rules_source = manifest.get("far_attack_rules", [])
    if not isinstance(far_rules_source, list):
        raise ValueError(f"{manifest_path}: far_attack_rules must be a list")
    supported_far_roles = {spec[0] for spec in OPTIONAL_FAR_ATTACK_ROLE_SPECS}
    far_rules = {}
    for rule in far_rules_source:
        if not isinstance(rule, dict):
            raise ValueError(f"{manifest_path}: each far attack rule must be an object")
        name = rule.get("role")
        if (not isinstance(name, str) or name not in supported_far_roles or
                name in far_rules):
            raise ValueError(
                f"{manifest_path}: far attack rule roles must be unique and supported")
        if rule.get("comparison") != "ge":
            raise ValueError(f"{manifest_path}: far attack comparison must be greater-or-equal")
        far_rules[name] = rule

    far_distance_values = [0] * len(OPTIONAL_FAR_ATTACK_ROLE_SPECS)
    far_rows = []
    far_role_coverage = {}
    far_attack_coverage = []
    for index, (name, base_role, damage_key) in enumerate(
            OPTIONAL_FAR_ATTACK_ROLE_SPECS):
        row = by_role.get(name)
        rule = far_rules.get(name)
        if row is None:
            if rule is not None:
                raise ValueError(f"{manifest_path}: far rule {name} has no source role")
            far_rows.append(
                f"    {{ 65535, {macros[base_role]}, 0, 0, 0"
                f"{_recovery_suffix(hit_timing, name)} }},")
            far_role_coverage[name] = {
                "available": False, "runtime_state_id": 0xFFFF,
                "runtime_flags": "0", "runtime_damage": 0,
                "fallback_role": base_role, "distance_runtime_q8": 0,
            }
            state_coverage[name] = {"available": False}
            continue
        if rule is None:
            raise ValueError(f"{manifest_path}: far role {name} has no imported fallback rule")
        if row.get("state") is None:
            raise ValueError(f"{manifest_path}: far role {name} requires a source state id")
        threshold_source = rule.get("threshold_source_units")
        if type(threshold_source) is not int or threshold_source <= 0:
            raise ValueError(f"{manifest_path}: {name} threshold must be positive")
        if rule.get("near_role") != base_role:
            raise ValueError(f"{manifest_path}: {name} near role must be {base_role}")
        threshold_q8 = _scaled_source_q8(
            threshold_source, scale_ratio, f"{manifest_path}: {name} threshold")
        far_distance_values[index] = threshold_q8
        damage = constants.get(damage_key)
        if type(damage) is not int or not 0 <= damage <= 255:
            raise ValueError(f"{manifest_path}: {damage_key} must be uint8 for {name}")
        damage_model = damage_models.get(name)
        if damage_model is None:
            raise ValueError(f"{manifest_path}: far role {name} has no damage model")
        role_macro = _macro_role(header, prefix, name)
        far_rows.append(
            f"    {{ {_state_id(row)}, {role_macro}, S_HIT, 0, {damage}"
            f"{_recovery_suffix(hit_timing, name)} }},")
        source_command = rule.get("source_command")
        source_condition = rule.get("source_condition")
        if not isinstance(source_command, str) or not isinstance(source_condition, str):
            raise ValueError(f"{manifest_path}: {name} source rule is incomplete")
        coverage = {
            "role": name,
            "available": True,
            "source_action": int(row["action"]),
            "source_state": int(row["state"]),
            "runtime_state_id": int(row["state"]),
            "runtime_flags": "S_HIT",
            "runtime_damage": damage,
            "runtime_hit_policy": damage_model.get("runtime_hit_policy"),
            "source_hitdef_count": damage_model.get("source_hitdef_count"),
            "fidelity": damage_model.get("fidelity"),
            "fidelity_reason": damage_model.get("reason"),
            "fallback_role": base_role,
            "distance_runtime_q8": threshold_q8,
            "source_command": source_command,
            "source_condition": source_condition,
            "near_source_state": rule.get("near_source_state"),
            "near_source_condition": rule.get("source_near_condition"),
            "source_uncompiled_trigger_groups": rule.get(
                "source_uncompiled_trigger_groups", {}),
            "source_near_uncompiled_trigger_groups": rule.get(
                "source_near_uncompiled_trigger_groups", {}),
        }
        far_role_coverage[name] = coverage
        far_attack_coverage.append(coverage)
        state_coverage[name] = {
            "available": True,
            "source_action": int(row["action"]),
            "source_state": int(row["state"]),
        }
    if set(far_rules) - {name for name in by_role if name in supported_far_roles}:
        raise ValueError(f"{manifest_path}: far rules do not match declared source roles")
    rows.extend(far_rows)

    unconsumed_source_roles = []
    for name, row in by_role.items():
        if name in STATE_ROLE_ORDER:
            continue
        action_id = row.get("action")
        if type(action_id) is not int or not 0 <= action_id <= 0xFFFF:
            raise ValueError(f"{manifest_path}: unconsumed role {name} action must be uint16")
        unconsumed_source_roles.append({
            "role": name,
            "source_action": action_id,
            "source_state": _state_id(row) if row.get("state") is not None else None,
        })

    command_source = manifest.get("commands")
    if not isinstance(command_source, dict):
        raise ValueError(f"{manifest_path}: commands must be a semantic-role map")
    command_rows = []
    command_coverage = {}
    for role, command_id in COMMAND_ROLE_SPECS:
        source_command = command_source.get(role)
        if source_command is None:
            continue
        if not isinstance(source_command, str) or not source_command.strip():
            raise ValueError(
                f"{manifest_path}: commands.{role} must be a non-empty string")
        symbol = f"{prefix}_CUT_CMD_{role.upper()}"
        size_symbol = f"{symbol}_SIZE"
        if not re.search(rf"^#define\s+{re.escape(size_symbol)}\s+\d+\s*$",
                         header, re.M):
            raise ValueError(
                f"generated scene header is missing command pattern {size_symbol}")
        command_rows.append(f"    {{ {symbol}, {command_id} }},")
        command_coverage[role] = {
            "source_command": source_command,
            "pattern_symbol": symbol,
            "runtime_command": command_id,
        }
    if not command_rows:
        raise ValueError(f"{manifest_path}: no supported command patterns")

    pose_count_macro = f"{prefix}_CUT_POSE_COUNT"
    if not re.search(rf"^#define\s+{re.escape(pose_count_macro)}\s+\d+\s*$", header, re.M):
        raise ValueError(f"generated scene header is missing {pose_count_macro}")
    pose_base = f"{prefix}_POSE_BASE"
    char_fields = [
        f"{prefix.lower()}_frames_all", f"{prefix.lower()}_anims",
        f"{prefix.lower()}_states", f"{prefix.lower()}_commands",
        str(len(command_rows)), pose_count_macro, pose_base,
        str(meta_capacity),
        str(int(constants["life"])), str(int(constants["jump_vy"])),
        str(int(constants["gravity"])), str(int(constants["hitstop"])),
        str(int(constants["hit_push"])), str(int(constants["guard_push"])),
        f"{prefix.lower()}_close_distances_q8",
        f"{prefix.lower()}_far_distances_q8", str(ground_front_q8),
    ]
    row_text = ", ".join(char_fields)
    if not 1 <= int(constants["life"]) <= 0xFFFF:
        raise ValueError(f"{manifest_path}: life outside uint16")
    thresholds = {
        "key1": int(constants["input_threshold_key1"]),
        "key2": int(constants["input_threshold_key2"]),
    }
    if any(not 2 <= value <= 255 for value in thresholds.values()):
        raise ValueError(f"{manifest_path}: input thresholds must be in 2..255")
    return rows, command_rows, {"character_initializer": row_text,
                  "hit_timing": hit_timing,
                  "meta_max_bytes": meta_capacity,
                  "source_sha256": manifest.get("source_sha256"),
                  "source_def": manifest.get("source_def"),
                  "source_routes": source_routes,
                  "source_route_pattern_count": sum(
                      definition.get("runtime_command_symbol") is not None
                      for route in source_routes
                      for definition in route["source_command_definitions"]),
                  "state_coverage": state_coverage,
                  "unconsumed_source_roles": unconsumed_source_roles,
                  "command_coverage": command_coverage,
                  "command_priority": [role for role, _ in COMMAND_ROLE_SPECS
                                       if role in command_coverage],
                  "input_thresholds": thresholds,
                  "damage_models": manifest.get("damage_models", []),
                  "unsupported_capabilities": manifest.get(
                      "unsupported_capabilities", []),
                  "source_limitations": manifest.get("source_limitations", []),
                  "optional_state_role_coverage": close_role_coverage,
                  "close_attack_coverage": close_attack_coverage,
                  "optional_far_attack_role_coverage": far_role_coverage,
                  "far_attack_coverage": far_attack_coverage,
                  "close_distance_q8_values": close_distance_values,
                  "far_distance_q8_values": far_distance_values,
                  "ground_front_runtime_q8": ground_front_q8,
                  "close_geometry": {
                      "ground_front_source_units": front_source,
                      "fighter_scale_ratio": scale_ratio,
                      "ground_front_runtime_q8": ground_front_q8,
                  }}


def _source_route_rows(meta: dict, header: str, prefix: str) -> list[str]:
    rows = []
    for route in meta["source_routes"]:
        anim_macro = _macro_role(header, prefix, route["action_role"])
        for definition in route["source_command_definitions"]:
            symbol = definition.get("runtime_command_symbol")
            if symbol is None:
                continue
            rows.append(
                f"    {{ {prefix}_{symbol}, {route['source_state']}, "
                f"{route['source_action']}, {anim_macro} }},")
    return rows


def render(manifest_paths: tuple[Path, Path], runtime_header: Path) -> tuple[str, dict]:
    header = runtime_header.read_text(encoding="ascii")
    p1_rows, p1_command_rows, p1_meta = _slot_rows(
        manifest_paths[0], header, "P1")
    p2_rows, p2_command_rows, p2_meta = _slot_rows(
        manifest_paths[1], header, "P2")
    p1_route_rows = _source_route_rows(p1_meta, header, "P1")
    p2_route_rows = _source_route_rows(p2_meta, header, "P2")
    has_close_attacks = any(
        meta["close_attack_coverage"] for meta in (p1_meta, p2_meta))
    has_far_attacks = any(
        meta["far_attack_coverage"] for meta in (p1_meta, p2_meta))
    if (has_close_attacks or has_far_attacks) and any(
            meta["ground_front_runtime_q8"] <= 0 for meta in (p1_meta, p2_meta)):
        raise ValueError(
            "distance variants require scaled ground.front geometry for both runtime slots")
    timed = [meta["hit_timing"] is not None for meta in (p1_meta, p2_meta)]
    if timed[0] != timed[1]:
        raise ValueError("hit timing must be present on both runtime slots or neither")
    schema_number = 7 if timed[0] else 5
    result = "\n".join([
        "/* Generated from the two scene-cut manifests; do not hand-edit. */",
        "#ifndef FIGHT_RUNTIME_DATA_H",
        "#define FIGHT_RUNTIME_DATA_H",
        f"#define FIGHT_RUNTIME_DATA_SCHEMA {schema_number}",
        f"#define P1_CUT_META_MAX_BYTES {p1_meta['meta_max_bytes']}",
        f"#define P2_CUT_META_MAX_BYTES {p2_meta['meta_max_bytes']}",
        "static const CommandDef p1_commands[] = {",
        *p1_command_rows,
        "};",
        "static const CommandDef p2_commands[] = {",
        *p2_command_rows,
        "};",
        "#ifndef FIGHT_SOURCE_ROUTE_DEF_DEFINED",
        "#define FIGHT_SOURCE_ROUTE_DEF_DEFINED",
        "typedef struct { const unsigned char *pattern; unsigned short source_state; "
        "unsigned short source_action; unsigned char action_anim; } FightSourceRouteDef;",
        "#endif",
        f"#define P1_SOURCE_ROUTE_PATTERN_COUNT {len(p1_route_rows)}",
        "static const FightSourceRouteDef p1_source_routes[] = {",
        *(p1_route_rows or ["    { 0, 0, 0, 0 },"]),
        "};",
        f"#define P2_SOURCE_ROUTE_PATTERN_COUNT {len(p2_route_rows)}",
        "static const FightSourceRouteDef p2_source_routes[] = {",
        *(p2_route_rows or ["    { 0, 0, 0, 0 },"]),
        "};",
        "static const unsigned short p1_close_distances_q8[AT_N] = { " +
        ", ".join(str(value) for value in p1_meta["close_distance_q8_values"]) + " };",
        "static const unsigned short p2_close_distances_q8[AT_N] = { " +
        ", ".join(str(value) for value in p2_meta["close_distance_q8_values"]) + " };",
        "static const unsigned short p1_far_distances_q8[AT_N] = { " +
        ", ".join(str(value) for value in p1_meta["far_distance_q8_values"]) + " };",
        "static const unsigned short p2_far_distances_q8[AT_N] = { " +
        ", ".join(str(value) for value in p2_meta["far_distance_q8_values"]) + " };",
        "static const StateDef p1_states[ST_N_STATES] = {",
        *p1_rows,
        "};",
        "static const StateDef p2_states[ST_N_STATES] = {",
        *p2_rows,
        "};",
        "static const CharacterData characters[2] = {",
        f"    {{ {p1_meta['character_initializer']} }},",
        f"    {{ {p2_meta['character_initializer']} }},",
        "};",
        "#endif /* FIGHT_RUNTIME_DATA_H */",
        "",
    ])
    report = {
        "schema": f"sms_fight_runtime_data_v{schema_number}",
        "hit_recovery_contract": {
            "fields": list(_RECOVERY_KEYS),
            "when": "schema 7; schema 5 leaves the fields zero and keeps character-wide hitstop",
            "clock": "defender pausetime freezes both actors; hittime, guardtime or airtime then counts down with control locked",
            "animation": "common1 gethit and knockdown are not in this profile; the current pose is held, then a non-control role returns to idle",
            "fidelity": "approximate",
        },
        "source_slots": [p1_meta, p2_meta],
        "role_policy": list(STATE_ROLE_ORDER),
        "unsupported_runtime_roles": {
            "special": "projectile entities are not implemented; command recognition never enters a strike state",
            "close_attacks": "close variants use source State -1 P2BodyDist X rules after scale conversion",
            "far_attack_variants": "far fallbacks use the ordered complement of an earlier near rule; chain/cancel trigger groups are not executed",
            "unconsumed_source_roles": "source actions are imported as data but have no runtime state/input mapping"
        },
        "role_accounting": {
            "required_runtime_roles": list(REQUIRED_ROLES),
            "optional_runtime_roles": [spec[0] for spec in (
                OPTIONAL_ATTACK_ROLE_SPECS + OPTIONAL_FAR_ATTACK_ROLE_SPECS)],
            "unconsumed_source_roles_by_slot": {
                "p1": p1_meta["unconsumed_source_roles"],
                "p2": p2_meta["unconsumed_source_roles"],
            },
            "scope": "unconsumed roles are not selectable; distance variants need matching imported source rules",
        },
        "source_route_dispatch_contract": {
            "compiled_tables": ["p1_source_routes", "p2_source_routes"],
            "fields": ["pattern", "source_state", "source_action", "action_anim"],
            "scope": "pattern-to-source target binding only; source controller predicates and gameplay effects are not executed by these tables",
        },
        "unknown_source_state_id": 0xFFFF,
        "scope": "current fixed common-state subset; not a general CNS VM",
        "close_geometry_contract": {
            "required_when_close_attacks_exist": has_close_attacks,
            "required_when_far_attack_variants_exist": has_far_attacks,
            "ground_front_runtime_q8_by_slot": [
                p1_meta["ground_front_runtime_q8"],
                p2_meta["ground_front_runtime_q8"],
            ],
        },
    }
    return result, report


def generate(manifest_paths: tuple[Path, Path], runtime_header: Path,
             output: Path, report_path: Path | None = None) -> dict:
    text, report = render(manifest_paths, runtime_header)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="ascii")
    profile_path = output.with_name("fight_input_profile.h")
    profile_header = "\n".join([
        "/* Generated from the per-slot scene manifests; do not hand-edit. */",
        "#ifndef FIGHT_INPUT_PROFILE_H",
        "#define FIGHT_INPUT_PROFILE_H",
        f"#define P1_CUT_INPUT_THRESHOLD_KEY1 {report['source_slots'][0]['input_thresholds']['key1']}",
        f"#define P1_CUT_INPUT_THRESHOLD_KEY2 {report['source_slots'][0]['input_thresholds']['key2']}",
        f"#define P2_CUT_INPUT_THRESHOLD_KEY1 {report['source_slots'][1]['input_thresholds']['key1']}",
        f"#define P2_CUT_INPUT_THRESHOLD_KEY2 {report['source_slots'][1]['input_thresholds']['key2']}",
        "#endif /* FIGHT_INPUT_PROFILE_H */",
        "",
    ])
    profile_path.write_text(profile_header, encoding="ascii")
    report["input_profile_header"] = {
        "path": profile_path.name,
        "sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
    }
    if report_path is not None:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    return report


def annotate_hit_timing(manifest_path: Path, source_dir: Path, def_name: str,
                        dest: Path) -> dict:
    """Copy one scene manifest and attach HitDef recovery times from its CNS."""
    from ..character import load
    from ..source import Source
    from .scene_cut import hit_recovery

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    character = load(Source(source_dir), def_name)
    timing = {}
    for item in manifest.get("damage_models", []):
        if not isinstance(item, dict) or not isinstance(item.get("role"), str):
            raise ValueError(f"{manifest_path}: damage model requires a role")
        state = item.get("source_state")
        if state is None:
            continue
        timing[item["role"]] = hit_recovery(character, int(state))
    manifest["hit_timing"] = timing
    manifest["hit_timing_source"] = {
        "source_dir": str(source_dir),
        "def_name": def_name,
        "source_sha256": character.source_sha256,
    }
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Attach HitDef recovery times and regenerate fight_runtime_data.h")
    parser.add_argument("--p1-manifest", type=Path, required=True)
    parser.add_argument("--p1-source", type=Path, required=True)
    parser.add_argument("--p1-def", required=True)
    parser.add_argument("--p2-manifest", type=Path, required=True)
    parser.add_argument("--p2-source", type=Path, required=True)
    parser.add_argument("--p2-def", required=True)
    parser.add_argument("--scene-header", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.out_dir
    p1 = annotate_hit_timing(args.p1_manifest, args.p1_source, args.p1_def,
                             out / "p1_scene_manifest.json")
    p2 = annotate_hit_timing(args.p2_manifest, args.p2_source, args.p2_def,
                             out / "p2_scene_manifest.json")
    report = generate(
        (out / "p1_scene_manifest.json", out / "p2_scene_manifest.json"),
        args.scene_header, out / "fight_runtime_data.h",
        out / "fight_runtime_data_manifest.json")
    if report["schema"] != "sms_fight_runtime_data_v7":
        raise SystemExit("recovery header was not schema 7")
    print(json.dumps({
        "schema": report["schema"],
        "p1_hp": p1["hit_timing"].get("hp"),
        "p2_hp": p2["hit_timing"].get("hp"),
        "header": str(out / "fight_runtime_data.h"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
