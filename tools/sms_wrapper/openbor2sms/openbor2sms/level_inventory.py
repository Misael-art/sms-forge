# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/openbor2sgdk_forge/level_inventory.py
#   donor sha256: 3cba7a44d22798c6cb3e37787f351b71215eccac41b57355df0a7672453dff09
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms front-end O1)
# Body below is byte-identical to the donor file (verified by cmp at port time);
# no behavioral change.
"""Source-ordered inventory of level directives, without runtime semantics."""

from __future__ import annotations

from collections import Counter

from .model_text import Directive, LevelFile


STAGE_REFERENCES = {
    "background",
    "bossmusic",
    "frontpanel",
    "map",
    "music",
    "panel",
}
SPAWN_CONFIG = {"spawn1", "spawn2", "spawn3", "spawn4"}


def _directive_row(item: Directive) -> dict:
    return {
        "line": item.line,
        "command": item.command,
        "args": item.args,
        "raw": item.raw,
    }


def build_level_inventory(
    level: LevelFile,
    model_entries: list[tuple[str, str, int]],
) -> dict:
    """Summarize raw source structure; never estimate event concurrency."""
    aliases: dict[str, list[tuple[str, str, int]]] = {}
    for alias, path, line in model_entries:
        aliases.setdefault(alias.lower(), []).append((alias, path, line))
    command_counts = Counter(item.command for item in level.timeline)
    dynamic_spawns = [item for item in level.timeline if item.command == "spawn"]

    spawn_resolution = []
    unresolved = []
    ambiguous = []
    for item in dynamic_spawns:
        name = item.args[0] if item.args else None
        matches = aliases.get(name.lower(), []) if name else []
        row = {
            "line": item.line,
            "name": name,
            "alias_match": None,
        }
        if len(matches) == 1:
            found = matches[0]
            row["alias_match"] = {"alias": found[0], "path": found[1], "line": found[2]}
        elif len(matches) > 1:
            row["alias_matches"] = [
                {"alias": alias, "path": path, "line": line}
                for alias, path, line in matches
            ]
            ambiguous.append({"line": item.line, "name": name})
        elif name:
            unresolved.append({"line": item.line, "name": name})
        spawn_resolution.append(row)

    def rows_for(commands: set[str]) -> list[dict]:
        return [_directive_row(item) for item in level.timeline if item.command in commands]

    return {
        "schema_version": "1.0.0",
        "artifact_kind": "openbor_level_source_order_inventory",
        "status": "source_order_inventory_only",
        "semantic_execution_claim": False,
        "concurrency_claim": False,
        "source": {"level_path": level.path},
        "counts": {
            "directives": len(level.timeline),
            "commands": dict(sorted(command_counts.items())),
            "model_index_entries": len(model_entries),
            "dynamic_spawn_directives": len(dynamic_spawns),
            "group_directives": command_counts["group"],
            "wait_directives": command_counts["wait"],
            "at_directives": command_counts["at"],
            "spawn_config_directives": sum(command_counts[name] for name in SPAWN_CONFIG),
            "wall_directives": command_counts["wall"],
            "hole_directives": command_counts["hole"],
        },
        "stage_references": rows_for(STAGE_REFERENCES),
        "spawn_configuration": rows_for(SPAWN_CONFIG),
        "dynamic_spawns": spawn_resolution,
        "unresolved_spawn_aliases": unresolved,
        "ambiguous_spawn_aliases": ambiguous,
        "event_controls": rows_for({"at", "group", "wait", "endlevel", "next"}),
        "geometry_directives": rows_for({"wall", "hole"}),
        "timeline": [_directive_row(item) for item in level.timeline],
        "parser_issues": list(level.issues),
        "limitations": [
            "Group and wait directives are preserved in source order; their executable timing and concurrency are not inferred.",
            "Spawn alias matches use the textual models index only; model behavior, script effects, and runtime eligibility are not validated.",
            "Panel transitions, collision geometry, music playback, and gameplay fidelity remain unaudited.",
        ],
    }
