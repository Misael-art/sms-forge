"""Emit the per-slot fight tables consumed by the banked integrated runtime.

The scene cutter names actors P1/P2. The existing banked frame and pose
readers use the legacy C storage namespaces `ken`/`ryu` for slots 1 and 2.
Those namespaces do not identify the source characters; this generator keeps
the source definitions and hashes attached to the corresponding slots.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:  # package import in tests; direct-script import in the build wrapper
    from . import fight_runtime_data as common
except ImportError:  # pragma: no cover - exercised by the wrapper CLI
    import fight_runtime_data as common


def namespace_slot_actors(text: str) -> str:
    """Map generated P1/P2 actor identifiers onto the banked runtime aliases."""
    text = re.sub(r"(?<![A-Za-z0-9_])P1_", "KEN_", text)
    text = re.sub(r"(?<![A-Za-z0-9_])P2_", "RYU_", text)
    text = re.sub(r"(?<![A-Za-z0-9_])p1_", "ken_", text)
    return re.sub(r"(?<![A-Za-z0-9_])p2_", "ryu_", text)


def _anim_actions(header: str, actor: str) -> list[int]:
    match = re.search(
        rf"static const Anim {actor}_anims\[(\d+)\] = \{{(.*?)\n\}};",
        header, re.S)
    if not match:
        raise ValueError(f"missing {actor}_anims table")
    actions: list[int] = []
    for row in match.group(2).splitlines():
        row = row.strip()
        if not row.startswith("{"):
            continue
        parsed = re.fullmatch(
            r"\{\s*(\d+)u?\s*,\s*(\d+)u?\s*,\s*(\d+)u?\s*,\s*"
            rf"{actor}_frames_all\s*\+\s*(\d+)u?\s*\}}\s*,?", row)
        if not parsed:
            raise ValueError(f"unparsed {actor} Anim row: {row}")
        actions.append(int(parsed.group(1)))
    if len(actions) != int(match.group(1)):
        raise ValueError(f"{actor}_anims declares {match.group(1)} rows, found {len(actions)}")
    return actions


def _validate_role_actions(manifest_path: Path, header: str,
                           macro_prefix: str, actor: str) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    roles = manifest.get("roles")
    if not isinstance(roles, list):
        raise ValueError(f"{manifest_path}: roles must be a list")
    actions = _anim_actions(header, actor)
    for role in roles:
        if not isinstance(role, dict):
            raise ValueError(f"{manifest_path}: each role must be an object")
        name, action = role.get("role"), role.get("action")
        if not isinstance(name, str) or type(action) is not int:
            raise ValueError(f"{manifest_path}: role name/action is malformed")
        macro = f"{macro_prefix}_CUT_ANIM_{name.upper()}"
        found = re.search(rf"^#define\s+{re.escape(macro)}\s+(\d+)\s*$",
                          header, re.M)
        if not found:
            raise ValueError(f"generated scene header is missing {macro}")
        index = int(found.group(1))
        if index >= len(actions) or actions[index] != action:
            actual = None if index >= len(actions) else actions[index]
            raise ValueError(
                f"{manifest_path}: role {name} expects action {action}, "
                f"but {actor} animation index {index} has action {actual}")


def render(manifest_paths: tuple[Path, Path], runtime_header: Path,
           frame_header: Path, pose_header: Path) -> tuple[str, dict]:
    header = runtime_header.read_text(encoding="ascii")
    supporting_headers = (frame_header.read_text(encoding="ascii") + "\n" +
                         pose_header.read_text(encoding="ascii"))
    slots = (("p1", "ken", "KEN"), ("p2", "ryu", "RYU"))
    slot_rows: list[list[str]] = []
    slot_route_rows: list[list[str]] = []
    slot_meta: list[dict] = []
    slot_constants: list[dict] = []

    for manifest_path, (slot, actor, macro_prefix) in zip(manifest_paths, slots):
        _validate_role_actions(manifest_path, header, macro_prefix, actor)
        rows, _commands, metadata = common._slot_rows(
            manifest_path, header, macro_prefix)
        route_rows = common._source_route_rows(metadata, header, macro_prefix)
        for symbol in (
                f"{macro_prefix}_FRAME_DATA_BANK", f"{macro_prefix}_FRAME_DATA_OFF",
                f"{macro_prefix}_POSE_INDEX_BANK", f"{macro_prefix}_POSE_META_BANK",
                f"{macro_prefix}_POSE_INDEX_OFF"):
            if not re.search(rf"^#define\s+{re.escape(symbol)}\s+\d+u?\s*$",
                             supporting_headers, re.M):
                raise ValueError(f"generated frame/pose headers are missing {symbol}")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        slot_rows.append(rows)
        slot_route_rows.append(route_rows)
        slot_meta.append(metadata)
        slot_constants.append(data["runtime_constants"])

    def character_row(slot_index: int) -> str:
        slot, actor, prefix = slots[slot_index]
        constants = slot_constants[slot_index]
        fields = [
            f"{actor}_anims", f"{slot}_states",
            f"{prefix}_CUT_POSE_COUNT", f"{prefix}_POSE_BASE",
            f"{prefix}_FRAME_DATA_BANK", f"{prefix}_FRAME_DATA_OFF",
            f"{prefix}_POSE_INDEX_BANK", f"{prefix}_POSE_META_BANK",
            f"{prefix}_POSE_INDEX_OFF", str(int(constants["life"])),
            str(int(constants["jump_vy"])), str(int(constants["gravity"])),
            str(int(constants["hitstop"])), str(int(constants["hit_push"])),
            str(int(constants["guard_push"])),
            f"{actor}_close_distances_q8",
            f"{actor}_far_distances_q8",
            str(slot_meta[slot_index]["ground_front_runtime_q8"]),
        ]
        return "    { " + ", ".join(fields) + " },"

    for index, metadata in enumerate(slot_meta):
        metadata.pop("character_initializer", None)
        metadata["integrated_character_initializer"] = character_row(index).strip()

    output = "\n".join([
        "/* Generated per-slot state/physics tables; do not hand-edit. */",
        "#ifndef FIGHT_RUNTIME_DATA_H",
        "#define FIGHT_RUNTIME_DATA_H",
        "#define FIGHT_RUNTIME_DATA_SCHEMA 6",
        "static const unsigned short ken_close_distances_q8[AT_N] = { " +
        ", ".join(str(value) for value in slot_meta[0]["close_distance_q8_values"]) + " };",
        "static const unsigned short ryu_close_distances_q8[AT_N] = { " +
        ", ".join(str(value) for value in slot_meta[1]["close_distance_q8_values"]) + " };",
        "static const unsigned short ken_far_distances_q8[AT_N] = { " +
        ", ".join(str(value) for value in slot_meta[0]["far_distance_q8_values"]) + " };",
        "static const unsigned short ryu_far_distances_q8[AT_N] = { " +
        ", ".join(str(value) for value in slot_meta[1]["far_distance_q8_values"]) + " };",
        "static const StateDef p1_states[ST_N_STATES] = {",
        *slot_rows[0],
        "};",
        "static const StateDef p2_states[ST_N_STATES] = {",
        *slot_rows[1],
        "};",
        "#ifndef FIGHT_SOURCE_ROUTE_DEF_DEFINED",
        "#define FIGHT_SOURCE_ROUTE_DEF_DEFINED",
        "typedef struct { const unsigned char *pattern; unsigned short source_state; "
        "unsigned short source_action; unsigned char action_anim; } FightSourceRouteDef;",
        "#endif",
        f"#define P1_SOURCE_ROUTE_PATTERN_COUNT {len(slot_route_rows[0])}",
        "static const FightSourceRouteDef p1_source_routes[] = {",
        *(slot_route_rows[0] or ["    { 0, 0, 0, 0 },"]),
        "};",
        f"#define P2_SOURCE_ROUTE_PATTERN_COUNT {len(slot_route_rows[1])}",
        "static const FightSourceRouteDef p2_source_routes[] = {",
        *(slot_route_rows[1] or ["    { 0, 0, 0, 0 },"]),
        "};",
        "static const CharacterData characters[2] = {",
        character_row(0),
        character_row(1),
        "};",
        "#endif /* FIGHT_RUNTIME_DATA_H */",
        "",
    ])
    report = {
        "schema": "sms_integrated_fight_runtime_data_v3",
        "source_slots": slot_meta,
        "runtime_actor_aliases": {"p1": "ken", "p2": "ryu"},
        "runtime_actor_alias_scope": (
            "legacy C storage namespaces only; not character identity"),
        "source_identity_by_slot": {
            "p1": {"source_def": slot_meta[0].get("source_def"),
                   "source_sha256": slot_meta[0].get("source_sha256")},
            "p2": {"source_def": slot_meta[1].get("source_def"),
                   "source_sha256": slot_meta[1].get("source_sha256")},
        },
        "role_accounting": {
            "runtime_roles": list(common.STATE_ROLE_ORDER),
            "unconsumed_source_roles_by_slot": {
                "p1": slot_meta[0]["unconsumed_source_roles"],
                "p2": slot_meta[1]["unconsumed_source_roles"],
            },
            "scope": "unconsumed roles have no state or input mapping in this runtime",
        },
        "source_route_dispatch_contract": {
            "compiled_tables": ["p1_source_routes", "p2_source_routes"],
            "fields": ["pattern", "source_state", "source_action", "action_anim"],
            "scope": "pattern-to-source target binding only; source controller predicates and gameplay effects are not executed by these tables",
        },
        "scope": "fixed common-state subset; no general CNS interpreter",
    }
    return output, report


def generate(manifest_paths: tuple[Path, Path], runtime_header: Path,
             frame_header: Path, pose_header: Path, output: Path,
             report_path: Path) -> dict:
    text, report = render(manifest_paths, runtime_header, frame_header, pose_header)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="ascii")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    return report


def self_check() -> None:
    assert namespace_slot_actors(
        "P1_CUT_ANIM_IDLE p1_frames_all P2_POSE_BASE X_P2_TILES_BANK") == (
        "KEN_CUT_ANIM_IDLE ken_frames_all RYU_POSE_BASE X_P2_TILES_BANK")
    try:
        _anim_actions("", "ken")
    except ValueError as exc:
        assert "missing ken_anims" in str(exc)
    else:
        raise AssertionError("missing Anim table was accepted")
    print("[PASS] integrated_runtime_data self-check (slot aliases and Anim contract)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--p1-manifest", type=Path)
    parser.add_argument("--p2-manifest", type=Path)
    parser.add_argument("--runtime-header", type=Path)
    parser.add_argument("--frame-header", type=Path)
    parser.add_argument("--pose-header", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    required = (args.p1_manifest, args.p2_manifest, args.runtime_header,
                args.frame_header, args.pose_header, args.out, args.report)
    if any(value is None for value in required):
        parser.error("both manifests, three headers, --out and --report are required")
    generate((args.p1_manifest, args.p2_manifest), args.runtime_header,
             args.frame_header, args.pose_header, args.out, args.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
