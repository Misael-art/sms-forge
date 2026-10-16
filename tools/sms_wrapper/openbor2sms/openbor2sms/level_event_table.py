# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/openbor2sgdk_forge/level_event_table.py
#   donor sha256: d084609eac1c124ba99ad01a59b93db617579640b436b3e5ef3442d34d59a4a5
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms front-end O1)
# Body below is byte-identical to the donor file (verified by cmp at port time);
# no behavioral change.
"""Lower the typed static OpenBOR event preflight into a deterministic C table.

The generated table is data only. Its existence does not mean that an SGDK
scene consumes it or that the module has been played back.
"""

from __future__ import annotations

import json
import re


TABLE_VERSION = "openbor-level-event-table/1"
ENTITY_KINDS = {
    "enemy": "OB_LEVEL_ENTITY_ENEMY",
    "item": "OB_LEVEL_ENTITY_ITEM",
    "obstacle": "OB_LEVEL_ENTITY_OBSTACLE",
    "text": "OB_LEVEL_ENTITY_TEXT",
    "player": "OB_LEVEL_ENTITY_PLAYER",
    "endlevel": "OB_LEVEL_ENTITY_ENDLEVEL",
}
EVENT_KINDS = {
    "spawn": "OB_LEVEL_EVENT_SPAWN",
    "group": "OB_LEVEL_EVENT_GROUP",
    "wait": "OB_LEVEL_EVENT_WAIT",
}
DIRECTIVE_FLAGS = {
    "coords": "OB_LEVEL_EVENT_HAS_COORDS",
    "health": "OB_LEVEL_EVENT_HAS_HEALTH",
    "map": "OB_LEVEL_EVENT_HAS_MAP",
    "flip": "OB_LEVEL_EVENT_HAS_FLIP",
    "boss": "OB_LEVEL_EVENT_HAS_BOSS",
    "item": "OB_LEVEL_EVENT_HAS_ITEM",
}
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
_INTEGER = re.compile(r"^[+-]?[0-9]+$")


def _number(value: object, label: str, low: int, high: int) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    if isinstance(value, int):
        result = value
    elif isinstance(value, str) and _INTEGER.fullmatch(value.strip()):
        result = int(value.strip(), 10)
    else:
        raise ValueError(f"{label} must be an integer")
    if not low <= result <= high:
        raise ValueError(f"{label} outside {low}..{high}")
    return result


def _c_string(value: str) -> str:
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"model alias is not ASCII: {value!r}") from exc
    return json.dumps(value, ensure_ascii=True)


def _alias_key(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty model alias")
    value = value.strip()
    if any(character in value for character in "\r\n\0"):
        raise ValueError(f"{label} contains a control character")
    return value.casefold()


def compile_level_event_table(preflight: dict, symbol: str = "ob_level_events") -> tuple[str | None, dict]:
    """Return C source and a report, failing closed on an unsupported event field."""
    diagnostics: list[str] = []
    if not _IDENTIFIER.fullmatch(symbol) or symbol.startswith("__"):
        diagnostics.append("invalid_c_symbol")
    if preflight.get("artifact_kind") != "openbor_reference_event_capacity_preflight":
        diagnostics.append("unexpected_preflight_artifact_kind")
    if preflight.get("status") != "reference_profile_complete_module_version_unverified":
        diagnostics.append("preflight_not_complete_for_pinned_reference")
    if preflight.get("fidelity_claim") is not False:
        diagnostics.append("preflight_fidelity_claim_must_remain_false")
    if preflight.get("runtime_playback_claim") is not False:
        diagnostics.append("preflight_playback_claim_must_remain_false")
    reference_limitations = {
        "original_module_openbor_version_unverified",
        "reference_profile_is_not_openbor_runtime_playback",
    }
    blocking_preflight = [
        item for item in preflight.get("blockers", [])
        if item not in reference_limitations
    ]
    if blocking_preflight:
        diagnostics.append("preflight_has_unresolved_blockers")
    if preflight.get("spawn_model_type_unknown_count", 0) != 0:
        diagnostics.append("preflight_has_unknown_spawn_model_types")
    referenced_rows = preflight.get("referenced_spawn_models")
    if not isinstance(referenced_rows, list):
        diagnostics.append("referenced_spawn_model_registry_missing")
        referenced_rows = []
    referenced_types: dict[str, str] = {}
    for model in referenced_rows:
        if not isinstance(model, dict) or not isinstance(model.get("name"), str):
            diagnostics.append("referenced_spawn_model_registry_invalid")
            continue
        key = model["name"].casefold()
        model_type = model.get("type")
        if key in referenced_types and referenced_types[key] != model_type:
            diagnostics.append(f"referenced_spawn_model_type_conflict:{key}")
        referenced_types[key] = model_type
    event_ir = preflight.get("event_ir")
    if not isinstance(event_ir, dict):
        diagnostics.append("event_ir_missing")
        event_ir = {}
    if event_ir.get("ir_version") != "openbor-level-event-ir/1":
        diagnostics.append("unsupported_event_ir_version")
    if event_ir.get("status") != "analysis_only":
        diagnostics.append("event_ir_not_analysis_only")
    if event_ir.get("diagnostics"):
        diagnostics.append("event_ir_has_diagnostics")
    source = preflight.get("source")
    if not isinstance(source, dict):
        diagnostics.append("source_identity_missing")
        source = {}
    level_sha = source.get("level_sha256")
    pak_sha = source.get("pak_sha256")
    reference_profile = event_ir.get("reference_profile")
    if not isinstance(reference_profile, dict):
        reference_profile = {}
        diagnostics.append("reference_profile_missing")
    reference_commit = reference_profile.get("commit")
    if not isinstance(reference_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", reference_commit):
        diagnostics.append("reference_profile_commit_invalid")
    if not isinstance(level_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", level_sha):
        diagnostics.append("source_level_sha256_invalid")
    if not isinstance(pak_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", pak_sha):
        diagnostics.append("source_pak_sha256_invalid")

    events = event_ir.get("events")
    typed_events = preflight.get("spawn_queue")
    if not isinstance(events, list) or not isinstance(typed_events, list):
        diagnostics.append("typed_event_queue_missing")
        events, typed_events = [], []
    if len(events) != len(typed_events):
        diagnostics.append("typed_event_queue_length_mismatch")
    if len(events) > 65535:
        diagnostics.append("event_queue_exceeds_u16_count")
    if preflight.get("spawn_queue_entry_count") != len(events):
        diagnostics.append("preflight_event_count_mismatch")

    rows: list[dict] = []
    aliases: dict[str, dict] = {}

    def register_alias(alias: object, entity_kind: str, label: str) -> str:
        key = _alias_key(alias, label)
        previous = aliases.get(key)
        if previous is not None and previous["entity_kind"] != entity_kind:
            diagnostics.append(f"model_alias_type_conflict:{key}")
        else:
            aliases.setdefault(key, {"alias": str(alias).strip(), "entity_kind": entity_kind})
        return key

    for index, event in enumerate(events):
        if not isinstance(event, dict):
            diagnostics.append(f"event_{index}_invalid")
            continue
        typed = typed_events[index] if index < len(typed_events) else None
        if not isinstance(typed, dict):
            diagnostics.append(f"event_{index}_typed_record_missing")
            typed = {}
        kind = event.get("kind")
        if kind not in EVENT_KINDS:
            diagnostics.append(f"event_{index}_unsupported_kind:{kind}")
            continue
        if (typed.get("kind"), typed.get("line"), typed.get("at")) != (
            kind, event.get("line"), event.get("at")
        ):
            diagnostics.append(f"event_{index}_typed_record_mismatch")
        if kind == "spawn" and (
            typed.get("name") != event.get("name")
            or typed.get("directives") != event.get("directives")
        ):
            diagnostics.append(f"event_{index}_typed_spawn_mismatch")
        if kind == "group" and (
            typed.get("group_min") != event.get("group_min")
            or typed.get("group_max") != event.get("group_max")
        ):
            diagnostics.append(f"event_{index}_typed_group_mismatch")
        try:
            at = _number(event.get("at"), f"event_{index}.at", -2147483648, 2147483647)
            line = _number(event.get("line"), f"event_{index}.line", 0, 65535)
        except ValueError as exc:
            diagnostics.append(f"event_{index}:{exc}")
            continue

        row = {
            "kind": kind,
            "at": at,
            "source_line": line,
            "entity_kind": "OB_LEVEL_ENTITY_UNRESOLVED",
            "model_key": None,
            "item_key": None,
            "x": 0,
            "z": 0,
            "health": 0,
            "group_min": 0,
            "group_max": 0,
            "flags": [],
            "map_id": 0,
            "flip": 0,
            "boss": 0,
        }

        if kind == "spawn":
            name = event.get("name")
            entity_type = typed.get("model_type")
            if isinstance(name, str) and referenced_types.get(name.casefold()) != entity_type:
                diagnostics.append(f"event_{index}_spawn_model_registry_mismatch")
            entity_kind = ENTITY_KINDS.get(entity_type)
            if entity_kind is None:
                diagnostics.append(f"event_{index}_unknown_entity_type:{entity_type}")
            else:
                row["entity_kind"] = entity_kind
                try:
                    row["model_key"] = register_alias(name, entity_kind, f"event_{index}.name")
                except ValueError as exc:
                    diagnostics.append(f"event_{index}:{exc}")
            if typed.get("model_script_blocks", 0) != 0:
                diagnostics.append(f"event_{index}_spawn_scripts_not_lowered")

            seen: set[str] = set()
            for directive in event.get("directives", []):
                if not isinstance(directive, dict):
                    diagnostics.append(f"event_{index}_directive_invalid")
                    continue
                command = directive.get("command")
                args = directive.get("args", [])
                if command not in DIRECTIVE_FLAGS:
                    diagnostics.append(f"event_{index}_unsupported_directive:{command}")
                    continue
                if command in seen:
                    diagnostics.append(f"event_{index}_duplicate_directive:{command}")
                    continue
                seen.add(command)
                row["flags"].append(DIRECTIVE_FLAGS[command])
                try:
                    if command == "coords":
                        if not isinstance(args, list) or len(args) != 2:
                            raise ValueError("coords requires x and z")
                        row["x"] = _number(args[0], "coords.x", -32768, 32767)
                        row["z"] = _number(args[1], "coords.z", -32768, 32767)
                    elif command == "health":
                        if not isinstance(args, list) or len(args) != 1:
                            raise ValueError("health requires one value")
                        row["health"] = _number(args[0], "health", -32768, 32767)
                    elif command == "map":
                        if not isinstance(args, list) or len(args) != 1:
                            raise ValueError("map requires one value")
                        row["map_id"] = _number(args[0], "map", 0, 255)
                    elif command == "flip":
                        if not isinstance(args, list) or len(args) != 1:
                            raise ValueError("flip requires one value")
                        row["flip"] = _number(args[0], "flip", 0, 1)
                    elif command == "boss":
                        if len(args) > 1:
                            raise ValueError("boss accepts at most one value")
                        row["boss"] = 1 if not args else _number(args[0], "boss", 0, 1)
                    elif command == "item":
                        if not isinstance(args, list) or len(args) != 1:
                            raise ValueError("item requires one model alias")
                        row["item_key"] = register_alias(
                            args[0], "OB_LEVEL_ENTITY_ITEM", f"event_{index}.item"
                        )
                except ValueError as exc:
                    diagnostics.append(f"event_{index}:{exc}")
        elif kind == "group":
            try:
                group_min = _number(event.get("group_min", 0) or 0, f"event_{index}.group_min", -32768, 65535)
                group_max = _number(event.get("group_max", 0) or 0, f"event_{index}.group_max", -32768, 65535)
                row["group_min"] = 100 if group_min < 1 else group_min
                row["group_max"] = 1 if group_max < 1 else group_max
                if row["group_min"] > 65535 or row["group_max"] > 65535:
                    raise ValueError("normalized group bound exceeds u16")
            except ValueError as exc:
                diagnostics.append(f"event_{index}:{exc}")

        rows.append(row)

    model_id_by_key = {key: index for index, key in enumerate(sorted(aliases))}
    if len(model_id_by_key) > 65535:
        diagnostics.append("model_symbol_table_exceeds_u16_ids")
    for row in rows:
        row["model_id"] = (
            model_id_by_key[row["model_key"]]
            if row["model_key"] is not None else 65535
        )
        row["item_model_id"] = (
            model_id_by_key[row["item_key"]]
            if row["item_key"] is not None else 65535
        )
    model_rows = [
        {
            "model_id": model_id_by_key[key],
            "alias": aliases[key]["alias"],
            "entity_kind": aliases[key]["entity_kind"],
        }
        for key in sorted(aliases)
    ]

    report = {
        "schema_version": "1.0.0",
        "artifact_kind": "openbor_level_event_c_table",
        "table_version": TABLE_VERSION,
        "ir_version": "openbor-level-event-ir/1",
        "status": "blocked" if diagnostics else "ready_static_table",
        "symbol": symbol,
        "source": {
            "pak_sha256": pak_sha if isinstance(pak_sha, str) else None,
            "level_sha256": level_sha if isinstance(level_sha, str) else None,
            "level_member": source.get("level_member"),
            "reference_profile_id": reference_profile.get("id"),
            "reference_profile_commit": reference_commit,
        },
        "event_count": len(rows),
        "model_symbol_count": len(model_rows),
        "events": rows,
        "model_symbols": model_rows,
        "diagnostics": diagnostics,
        "runtime_binding": {
            "connected": False,
            "claim_limit": "This deterministic C table has no SGDK scene consumer yet; it is not module playback or conversion-equivalence evidence.",
        },
    }
    if diagnostics:
        return None, report

    lines = [
        "/* Generated by openbor2sgdk_forge; do not edit by hand. */",
        '#include "openbor/ob_level_events.h"',
        "",
        f'const char {symbol}_table_version[] = "{TABLE_VERSION}";',
        f'const char {symbol}_pak_sha256[] = "{pak_sha}";',
        f'const char {symbol}_level_sha256[] = "{level_sha}";',
        f'const char {symbol}_reference_commit[] = "{reference_commit}";',
        "",
        f"const ObLevelEvent {symbol}[] = {{",
    ]
    if not rows:
        lines.append("    { 0 },")
    for row in rows:
        flags = " | ".join(row["flags"]) if row["flags"] else "0u"
        lines.append(
            "    { "
            f"{row['at']}, {row['x']}, {row['z']}, {row['health']}, "
            f"{row['source_line']}u, {row['model_id']}u, {row['item_model_id']}u, "
            f"{row['group_min']}u, {row['group_max']}u, {EVENT_KINDS[row['kind']]}, "
            f"{row['entity_kind']}, {flags}, {row['map_id']}u, {row['flip']}u, {row['boss']}u "
            "},"
        )
    lines.extend([
        "};",
        f"const u16 {symbol}_count = {len(rows)}u;",
        "",
        f"const ObLevelModelSymbol {symbol}_models[] = {{",
    ])
    if not model_rows:
        lines.append('    { OB_LEVEL_MODEL_ID_NONE, OB_LEVEL_ENTITY_UNRESOLVED, "" },')
    for model in model_rows:
        lines.append(
            f"    {{ {model['model_id']}u, {model['entity_kind']}, "
            f"{_c_string(model['alias'])} }},"
        )
    lines.extend([
        "};",
        f"const u16 {symbol}_model_count = {len(model_rows)}u;",
        "",
    ])
    return "\n".join(lines), report


def render_level_event_header(report: dict) -> str:
    """Render declarations for a ready table so consumers need no handwritten externs."""
    if report.get("artifact_kind") != "openbor_level_event_c_table" or report.get("status") != "ready_static_table":
        raise ValueError("event table report is not ready")
    symbol = report.get("symbol")
    if not isinstance(symbol, str) or not _IDENTIFIER.fullmatch(symbol) or symbol.startswith("__"):
        raise ValueError("event table report has an invalid C symbol")
    guard = f"{symbol.upper()}_GENERATED_H"
    return "\n".join([
        "/* Generated by openbor2sgdk_forge; do not edit by hand. */",
        f"#ifndef {guard}",
        f"#define {guard}",
        "",
        '#include "openbor/ob_level_events.h"',
        "",
        f"extern const char {symbol}_table_version[];",
        f"extern const char {symbol}_pak_sha256[];",
        f"extern const char {symbol}_level_sha256[];",
        f"extern const char {symbol}_reference_commit[];",
        f"extern const ObLevelEvent {symbol}[];",
        f"extern const u16 {symbol}_count;",
        f"extern const ObLevelModelSymbol {symbol}_models[];",
        f"extern const u16 {symbol}_model_count;",
        "",
        f"#endif /* {guard} */",
        "",
    ])
