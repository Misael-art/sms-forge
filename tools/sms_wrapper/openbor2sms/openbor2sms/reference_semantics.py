# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/openbor2sgdk_forge/reference_semantics.py
#   donor sha256: 1fa8bbc34e6870ffcd67e63cfc9d9c4d50909f89ea736a37cd655a576fb41be0
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms front-end O1)
# Body below is byte-identical to the donor file (verified by cmp at port time);
# no behavioral change.
"""Pinned OpenBOR semantics and narrow event-capacity analysis."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, InvalidOperation
import re

from .model_text import LevelFile, ModelFile


REFERENCE_PROFILE = {
    "id": "openbor_dcurrent_787b6770",
    "repository": "https://github.com/DCurrent/openbor",
    "commit": "787b6770409935137579715febf80cf7a529b748",
    "files": {
        "engine/openbor.c": "8d210999b4af34c1932e0865daf39a007aec54155b1ed909176a39af905f5b2f",
        "engine/openbor.h": "e3891b5810d35f0584af98f9eb3dd6f7f2305a7185d0f6ffcbca3f1cfacd6964",
        "engine/source/gamelib/font.c": "74944769b719009836cb98571823536234bbc63d95f6b28dcd7ae1af0ff98f1a",
        "engine/source/gamelib/loadimg.c": "9c6a61772c1ed714c16e7fa0c777c46f1c54c05861d1bf9e13c875f2b2801edc",
        "engine/source/gamelib/bitmap.c": "8427555f80358437125777c4a2fa552cd4b15f27dac42cc6c30ef2a4aeecac5e",
        "LICENSE": "b8f3916944f0b5aee216ef7a494820d17ae658336a4680992dc244ebedecf3ea",
    },
    "engine_locations": {
        "group_dispatch": "engine/openbor.c:50037-50144",
        "wait_release": "engine/openbor.c:50170-50175",
        "group_defaults": "engine/openbor.c:23908-23909",
        "group_parse": "engine/openbor.c:24855-24868",
        "makeinv_parse": "engine/openbor.c:16045-16054",
        "makeinv_spawn": "engine/openbor.c:27523-27529",
        "makeinv_expiry": "engine/openbor.c:32943-32949",
        "default_next_hit": "engine/openbor.c:31556-31559,31773-31774",
    },
    "semantics": {
        "game_speed_default": 200,
        "game_speed_unit": "logical_clock_ticks_per_second",
        "makeinv_unit": "seconds multiplied by global_config.game_speed at model load",
        "makeinv_second_argument": "nonzero negates duration and disables blink",
        "default_next_hit_ticks": 40,
        "next_hit_comparison": "blocked while next_hit_time >= _time; first eligible tick is strictly later",
        "default_group_min": 100,
        "default_group_max": 100,
        "group_count_function": "count_ents(TYPE_ENEMY)",
        "group_count_type": "TYPE_ENEMY",
        "group_dispatch_guard": "active TYPE_ENEMY count < groupmin; dispatch while count < groupmax",
        "group_wait_same_pass": "wait sets level->waiting and advances current_spawn; the same eligible queue pass continues until groupmax or a future at-position",
        "wait_presence_function": "findent(TYPE_ENEMY)",
        "wait_release_guard": "wait releases when findent(TYPE_ENEMY) returns NULL",
    },
}

LEVEL_EVENT_IR_VERSION = "openbor-level-event-ir/1"


def _ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def _atoi_truthy(value: str) -> bool:
    """Match the reference engine's GET_INT_ARG/atoi use for makeinv arg 2."""
    match = re.match(r"^[\t\n\v\f\r ]*([+-]?\d+)", value)
    return bool(match and int(match.group(1), 10) != 0)


def lower_makeinv(args: list[str] | None) -> dict:
    """Lower pinned OpenBOR spawn invincibility without conflating hurt lockout.

    In DCurrent/openbor 787b6770, makeinv is a number of seconds multiplied by
    GAME_SPEED_DEFAULT (200 logical ticks/second). The engine stores the signed
    result: positive blinks, a nonzero second argument negates it, and expiry
    uses the absolute value. Frame counts are an explicit fixed-refresh SGDK
    adaptation, rounded up so a fractional frame never shortens the timer.
    """
    values = list(args or [])
    if not values:
        signed_ticks = 0
        seconds_text = None
    else:
        try:
            seconds = Decimal(values[0])
        except InvalidOperation as exc:
            raise ValueError(f"invalid makeinv duration: {values[0]!r}") from exc
        if not seconds.is_finite():
            raise ValueError(f"invalid makeinv duration: {values[0]!r}")
        signed_ticks = int(seconds * REFERENCE_PROFILE["semantics"]["game_speed_default"])
        seconds_text = values[0]
        if len(values) > 1 and _atoi_truthy(values[1]):
            signed_ticks = -signed_ticks

    duration_ticks = abs(signed_ticks)
    game_speed = REFERENCE_PROFILE["semantics"]["game_speed_default"]
    return {
        "source_seconds": seconds_text,
        "logical_ticks_signed": signed_ticks,
        "logical_ticks": duration_ticks,
        "ntsc_frames": _ceil_div(duration_ticks * 60, game_speed) if duration_ticks else 0,
        "pal_frames": _ceil_div(duration_ticks * 50, game_speed) if duration_ticks else 0,
        "blink": signed_ticks > 0,
        "reference_commit": REFERENCE_PROFILE["commit"],
        "note": (
            "makeinv is spawn invincibility, not post-hit recovery; signed duration is "
            "seconds * game_speed (200 ticks/s), positive blinks, and arg2 nonzero disables blink."
        ),
    }


def default_next_hit_frames(frame_rate_hz: int) -> int:
    """Frame adaptation of the pinned engine's default 40-tick hurt lockout.

    The target check blocks through equality (>=), so include one logical tick
    when calculating the first frame that can accept another hit.
    """
    if frame_rate_hz <= 0:
        raise ValueError("frame_rate_hz must be positive")
    semantics = REFERENCE_PROFILE["semantics"]
    ticks = semantics["default_next_hit_ticks"]
    game_speed = semantics["game_speed_default"]
    return _ceil_div((ticks + 1) * frame_rate_hz, game_speed)


def compile_spawn_queue(level: LevelFile) -> tuple[list[dict], list[str]]:
    """Compile only records closed by `at`, matching the pinned parser shape."""
    queue: list[dict] = []
    issues: list[str] = []
    pending: dict | None = None

    for item in level.timeline:
        if item.command == "spawn":
            if pending is not None:
                issues.append(f"{item.line}: queued record replaced before at")
            pending = {
                "kind": "spawn",
                "line": item.line,
                "name": item.args[0] if item.args else None,
                "directives": [],
            }
        elif item.command == "group":
            if pending is not None:
                issues.append(f"{item.line}: queued record replaced before at")
            pending = {
                "kind": "group",
                "line": item.line,
                "group_min": _int_or_none(item.args, 0),
                "group_max": _int_or_none(item.args, 1),
                "directives": [],
            }
        elif item.command == "wait":
            if pending is not None:
                issues.append(f"{item.line}: queued record replaced before at")
            pending = {"kind": "wait", "line": item.line, "directives": []}
        elif item.command == "at":
            position = _int_or_none(item.args, 0)
            if position is None:
                issues.append(f"{item.line}: at without an integer position")
            elif pending is None:
                issues.append(f"{item.line}: at has no recognized queued record")
            else:
                queue.append({**pending, "at": position, "at_line": item.line})
                pending = None
        elif pending is not None:
            pending["directives"].append({
                "line": item.line,
                "command": item.command,
                "args": item.args,
            })

    if pending is not None:
        issues.append(f"{pending['line']}: queued record is not closed by at")
    return queue, issues


def compile_level_event_ir(level: LevelFile) -> dict:
    """Preserve and type a level's static event queue without claiming runtime execution."""
    queue, queue_issues = compile_spawn_queue(level)
    issues = list(dict.fromkeys([*level.issues, *queue_issues]))
    directives = [
        {
            "line": item.line,
            "command": item.command,
            "args": list(item.args),
            "raw": item.raw,
        }
        for item in level.timeline
    ]
    return {
        "ir_version": LEVEL_EVENT_IR_VERSION,
        "source_path": level.path,
        "reference_profile": {
            "id": REFERENCE_PROFILE["id"],
            "commit": REFERENCE_PROFILE["commit"],
            "original_module_version_verified": False,
        },
        "status": "blocked" if issues else "analysis_only",
        "events": queue,
        "source_directives": directives,
        "diagnostics": issues,
        "runtime_binding": {
            "connected": False,
            "claim_limit": "This IR preserves a statically parsed event queue; the SGDK runtime does not consume it yet.",
        },
    }


def _int_or_none(args: list[str], index: int) -> int | None:
    if index >= len(args):
        return None
    try:
        return int(args[index], 10)
    except ValueError:
        return None


def _model_type(model: ModelFile | None) -> str | None:
    if model is None:
        return None
    value = model.header_value("type")
    return value[0].lower() if value else None


def simulate_reference_dispatch_step(
    typed_queue: list[dict],
    *,
    cursor: int,
    level_position: int,
    enemy_count: int,
    group_min: int | None = None,
    group_max: int | None = None,
    waiting: bool = False,
    wait_has_enemy: bool | None = None,
) -> dict:
    """Model one pinned OpenBOR level queue pass for host-side differential tests.

    The loop order follows update_scroller(): the initial group-min guard is
    checked once, then eligible records are consumed while active enemy count
    is below groupmax and ``at <= level_position``. A wait record sets the
    waiting state but does not break that same queue pass. Wait release is
    evaluated after dispatch, with its own ``findent(TYPE_ENEMY)`` predicate.

    This is a static reference model, not module playback. It assumes each
    typed spawn succeeds, each enemy spawn contributes one TYPE_ENEMY entity,
    and referenced model scripts have no additional effects. Unknown types or
    script-bearing records stop without advancing the cursor.
    """
    def require_int(value: object, label: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{label} must be an integer")
        return value

    cursor = require_int(cursor, "cursor")
    level_position = require_int(level_position, "level_position")
    enemy_count = require_int(enemy_count, "enemy_count")
    if cursor < 0 or enemy_count < 0:
        raise ValueError("cursor and enemy_count must be non-negative")
    if not isinstance(waiting, bool):
        raise ValueError("waiting must be a bool")
    if wait_has_enemy is not None and not isinstance(wait_has_enemy, bool):
        raise ValueError("wait_has_enemy must be a bool or None")
    if not isinstance(typed_queue, list):
        raise ValueError("typed_queue must be a list")

    semantics = REFERENCE_PROFILE["semantics"]
    group_min = semantics["default_group_min"] if group_min is None else require_int(group_min, "group_min")
    group_max = semantics["default_group_max"] if group_max is None else require_int(group_max, "group_max")
    group_min = 100 if group_min < 1 else group_min
    group_max = 1 if group_max < 1 else group_max
    has_enemy = enemy_count > 0 if wait_has_enemy is None else wait_has_enemy
    enemy_count_before = enemy_count
    cursor_before = cursor
    outer_group_gate_open = enemy_count < group_min
    processed: list[dict] = []
    blocker = None

    while outer_group_gate_open and enemy_count < group_max and cursor < len(typed_queue):
        event = typed_queue[cursor]
        if not isinstance(event, dict):
            blocker = f"event_{cursor}_invalid"
            break
        event_at = event.get("at")
        source_line = event.get("line")
        if (isinstance(event_at, bool) or not isinstance(event_at, int)
                or isinstance(source_line, bool) or not isinstance(source_line, int)):
            blocker = f"event_{cursor}_position_or_source_line_invalid"
            break
        if event_at > level_position:
            break

        kind = event.get("kind")
        before = {
            "enemy_count": enemy_count,
            "group_min": group_min,
            "group_max": group_max,
            "waiting": waiting,
        }
        action = None
        if kind == "group":
            minimum = event.get("group_min")
            maximum = event.get("group_max")
            if (isinstance(minimum, bool) or not isinstance(minimum, int)
                    or isinstance(maximum, bool) or not isinstance(maximum, int)):
                blocker = f"event_{cursor}_group_arguments_invalid"
                break
            group_min = 100 if minimum < 1 else minimum
            group_max = 1 if maximum < 1 else maximum
            action = "group_limits_applied"
        elif kind == "wait":
            waiting = True
            action = "wait_set_continue_queue_pass"
        elif kind == "spawn":
            model_type = event.get("model_type")
            if model_type not in {"enemy", "item", "obstacle", "text", "player", "endlevel"}:
                blocker = f"event_{cursor}_spawn_model_type_unknown"
                break
            scripts = event.get("model_script_blocks", 0)
            if isinstance(scripts, bool) or not isinstance(scripts, int) or scripts != 0:
                blocker = f"event_{cursor}_spawn_scripts_not_analyzed"
                break
            if model_type == "enemy":
                enemy_count += 1
                has_enemy = True
                action = "enemy_spawn_assumed"
            else:
                action = "non_enemy_spawn_assumed"
        else:
            blocker = f"event_{cursor}_unsupported_kind:{kind}"
            break

        processed.append({
            "source_line": source_line,
            "at": event_at,
            "kind": kind,
            "name": event.get("name"),
            "action": action,
            "before": before,
            "after": {
                "enemy_count": enemy_count,
                "group_min": group_min,
                "group_max": group_max,
                "waiting": waiting,
            },
        })
        cursor += 1

    released_wait = False
    if waiting and not has_enemy:
        waiting = False
        released_wait = True

    if blocker is not None:
        stop_reason = "fail_closed"
    elif not outer_group_gate_open:
        stop_reason = "group_min_blocked"
    elif cursor >= len(typed_queue):
        stop_reason = "queue_exhausted"
    elif enemy_count >= group_max:
        stop_reason = "group_max_blocked"
    else:
        stop_reason = "position_blocked"

    return {
        "cursor_before": cursor_before,
        "cursor_after": cursor,
        "level_position": level_position,
        "enemy_count_before": enemy_count_before,
        "enemy_count_after": enemy_count,
        "group_min": group_min,
        "group_max": group_max,
        "waiting": waiting,
        "wait_has_enemy_after": has_enemy,
        "wait_released_after_dispatch": released_wait,
        "processed": processed,
        "stop_reason": stop_reason,
        "blocker": blocker,
        "assumptions": [
            "each known spawn succeeds and advances once",
            "each enemy spawn adds one TYPE_ENEMY to count_ents",
            "wait_has_enemy models findent(TYPE_ENEMY) separately from group count",
            "model scripts are absent or have no unmodeled side effects",
        ],
        "reference_commit": REFERENCE_PROFILE["commit"],
    }


def build_reference_event_preflight(
    level: LevelFile,
    models: dict[str, ModelFile],
    model_alias_counts: Counter[str],
    reference_file_hashes: dict[str, str],
) -> dict:
    queue, queue_issues = compile_spawn_queue(level)
    level_has_dynamic_script = any(
        item.command in {"@script", "spawnscript", "spawnaction"}
        for item in level.timeline
    )
    referenced_models: dict[str, dict] = {}
    blockers: list[str] = []
    if queue_issues:
        blockers.extend(["spawn_queue_parse_incomplete", *queue_issues])
    if level.issues:
        blockers.extend(f"level_parse_issue:{issue}" for issue in level.issues)
    if level_has_dynamic_script:
        blockers.append("level_spawn_scripts_not_analyzed")

    typed_queue = []
    for event in queue:
        row = dict(event)
        if event["kind"] == "spawn":
            name = event["name"]
            key = name.lower() if name else ""
            if model_alias_counts[key] != 1:
                blockers.append(f"spawn_alias_not_unique:{name or '<missing>'}")
                model = None
            else:
                model = models.get(key)
            model_type = _model_type(model)
            scripts = sum(len(anim.scripts) for anim in model.anims) if model else 0
            row["model_type"] = model_type
            row["model_script_blocks"] = scripts
            if model is None or model_type is None:
                blockers.append(f"spawn_model_type_unknown:{name or '<missing>'}")
            if scripts:
                blockers.append(f"spawn_model_scripts_not_analyzed:{name}")
            referenced_models[key] = {
                "name": name,
                "type": model_type,
                "script_blocks": scripts,
            }
        typed_queue.append(row)

    spawn_type_counts = Counter(
        event.get("model_type") or "unknown"
        for event in typed_queue
        if event["kind"] == "spawn"
    )

    default_min = REFERENCE_PROFILE["semantics"]["default_group_min"]
    default_max = REFERENCE_PROFILE["semantics"]["default_group_max"]
    group_min = default_min
    group_max = default_max
    segments = []
    max_required = 0
    for index, event in enumerate(typed_queue):
        if event["kind"] != "group":
            continue
        minimum = event["group_min"]
        maximum = event["group_max"]
        if minimum is None or maximum is None:
            blockers.append(f"group_arguments_invalid:{event['line']}")
            continue
        group_min = 100 if minimum < 1 else minimum
        group_max = 1 if maximum < 1 else maximum
        end = next(
            (candidate for candidate in range(index + 1, len(typed_queue))
             if typed_queue[candidate]["kind"] == "group"),
            len(typed_queue),
        )
        positions: dict[int, list[dict]] = {}
        waits = []
        for candidate in typed_queue[index + 1:end]:
            if candidate["kind"] == "wait":
                waits.append({"line": candidate["line"], "at": candidate["at"]})
            elif candidate["kind"] == "spawn" and candidate.get("model_type") == "enemy":
                positions.setdefault(candidate["at"], []).append({
                    "line": candidate["line"],
                    "name": candidate["name"],
                })
        position_batches = []
        for position, spawns in sorted(positions.items()):
            batch_capacity = min(group_max, len(spawns))
            max_required = max(max_required, batch_capacity)
            position_batches.append({
                "at": position,
                "enemy_spawn_directives": spawns,
                "enemy_spawn_count": len(spawns),
                "configured_group_max": group_max,
                "reference_profile_batch_capacity": batch_capacity,
            })
        segments.append({
            "group_line": event["line"],
            "at": event["at"],
            "group_min": group_min,
            "group_max": group_max,
            "waits_until_next_group": waits,
            "enemy_batches": position_batches,
        })

    # Initial queued spawns before the first explicit group use engine defaults.
    first_group = next(
        (index for index, event in enumerate(typed_queue) if event["kind"] == "group"),
        len(typed_queue),
    )
    initial_enemies = [
        {"line": event["line"], "at": event["at"], "name": event["name"]}
        for event in typed_queue[:first_group]
        if event["kind"] == "spawn" and event.get("model_type") == "enemy"
    ]
    if initial_enemies:
        max_required = max(max_required, min(default_max, len(initial_enemies)))

    original_version_verified = False
    blockers.append("original_module_openbor_version_unverified")
    blockers.append("reference_profile_is_not_openbor_runtime_playback")
    result_status = (
        "reference_profile_partial"
        if queue_issues or any("not_analyzed" in item or "unknown" in item for item in blockers)
        else "reference_profile_complete_module_version_unverified"
    )
    return {
        "schema_version": "1.0.0",
        "artifact_kind": "openbor_reference_event_capacity_preflight",
        "status": result_status,
        "fidelity_claim": False,
        "runtime_playback_claim": False,
        "original_module_version_verified": original_version_verified,
        "reference_profile": {
            **REFERENCE_PROFILE,
            "verified_local_file_sha256": reference_file_hashes,
        },
        "source_level": level.path,
        "spawn_queue_entry_count": len(typed_queue),
        "spawn_directive_counts_by_model_type": dict(sorted(spawn_type_counts.items())),
        "typed_non_enemy_spawn_directive_count": sum(
            count for model_type, count in spawn_type_counts.items()
            if model_type not in {"enemy", "unknown"}
        ),
        "spawn_model_type_unknown_count": spawn_type_counts.get("unknown", 0),
        "spawn_counts_are_level_wide_directives_not_live_concurrency": True,
        "initial_enemy_spawns_before_first_group": initial_enemies,
        "spawn_queue": typed_queue,
        "referenced_spawn_models": list(referenced_models.values()),
        "group_segments": segments,
        "maximum_enemy_slots_requested_by_same_position_batch": max_required,
        "blockers": list(dict.fromkeys(blockers)),
        "claim_limit": "This report applies only to the pinned OpenBOR source profile and static PAK data. It is not playback evidence and does not identify the engine version used by this module. It assumes configured enemy spawns succeed; scripts, other spawned entity kinds, and gameplay-dependent lifetime are outside this enemy-slot count.",
    }
