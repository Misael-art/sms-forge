"""Resolve a source CMD name through its hash-bound physical control profile.

The current profile subset records two commands per physical button:
the first fires on release before a hold threshold; the second fires when the
threshold is reached. Unsupported profile shapes fail closed instead of
guessing a button or timing rule.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def resolve_trigger(profile: dict, source_sha256: str, command: str) -> dict:
    if profile.get("schema") != "sms_mugen_control_profile_v1":
        raise ValueError("unsupported control profile schema")
    source = profile.get("source") or {}
    if source.get("sha256") != source_sha256:
        raise ValueError("control profile source SHA differs from imported package")
    if profile.get("policy") != "release_or_threshold":
        raise ValueError("unsupported control profile policy")
    if command in profile.get("dropped", []):
        raise ValueError(f"source command {command!r} is explicitly dropped")

    families = profile.get("families")
    thresholds = profile.get("thresholds")
    if not isinstance(families, dict) or not isinstance(thresholds, dict):
        raise ValueError("profile must declare command families and thresholds")
    matches = []
    for family, commands in families.items():
        if not isinstance(commands, list):
            raise ValueError("each control family must be a command list")
        if command in commands:
            matches.append((family, commands))
    if len(matches) != 1:
        raise ValueError("command must resolve to exactly one physical family")
    family_text, commands = matches[0]
    if family_text not in ("1", "2"):
        raise ValueError("only SMS physical buttons 1 and 2 are supported")
    if len(commands) != 2 or commands.count(command) != 1:
        raise ValueError("profile family must explicitly distinguish quick/held commands")
    family_thresholds = thresholds.get(family_text)
    if (not isinstance(family_thresholds, list) or len(family_thresholds) != 1 or
            not isinstance(family_thresholds[0], int) or
            isinstance(family_thresholds[0], bool) or
            not 1 <= family_thresholds[0] <= 255):
        raise ValueError("profile family requires one valid hold threshold")

    command_index = commands.index(command)
    return {
        "command": command,
        "physical_button": int(family_text),
        "activation": "release" if command_index == 0 else "hold",
        "threshold_frames": family_thresholds[0],
        "profile_status": profile.get("validation_status", "unspecified"),
    }


def load_trigger(path: Path, source_sha256: str, command: str) -> dict:
    raw = path.resolve().read_bytes()
    profile = json.loads(raw)
    result = resolve_trigger(profile, source_sha256, command)
    result["profile_path"] = str(path.resolve())
    result["profile_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def self_check() -> dict:
    profile = {
        "schema": "sms_mugen_control_profile_v1",
        "source": {"sha256": "a" * 64},
        "families": {"1": ["x", "z"], "2": ["a", "c"]},
        "thresholds": {"1": [6], "2": [6]},
        "policy": "release_or_threshold",
        "dropped": ["y", "b"],
    }
    checks = {
        "held_punch_uses_button1_and_six_frames": resolve_trigger(
            profile, "a" * 64, "z") == {
                "command": "z", "physical_button": 1, "activation": "hold",
                "threshold_frames": 6, "profile_status": "unspecified"},
        "quick_punch_uses_button1_release": resolve_trigger(
            profile, "a" * 64, "x")["activation"] == "release",
        "kick_family_uses_button2": resolve_trigger(
            profile, "a" * 64, "c")["physical_button"] == 2,
    }
    negatives = [
        ("reject_source_sha_mismatch", lambda: resolve_trigger(profile, "b" * 64, "z")),
        ("reject_dropped_command", lambda: resolve_trigger(profile, "a" * 64, "y")),
        ("reject_unknown_command", lambda: resolve_trigger(profile, "a" * 64, "q")),
        ("reject_ambiguous_family", lambda: resolve_trigger(
            {**profile, "families": {"1": ["x", "z"], "2": ["z", "c"]}},
            "a" * 64, "z")),
        ("reject_unclassified_family", lambda: resolve_trigger(
            {**profile, "families": {"3": ["z", "x"]}}, "a" * 64, "z")),
    ]
    for name, invoke in negatives:
        try:
            invoke()
        except ValueError:
            checks[name] = True
        else:
            checks[name] = False
    return {"checks": checks, "passed": all(checks.values())}
