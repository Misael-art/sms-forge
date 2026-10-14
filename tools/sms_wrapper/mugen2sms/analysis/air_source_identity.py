"""Emit a hash-bound, finite, one-pass source contract for one MUGEN AIR action.

The record preserves AIR element order even when two elements reference the
same sprite. It is source-side data only; it does not prove what a ROM runs.

Usage:
    python -m mugen2sms.analysis.air_source_identity <package.zip> --action 200 --out action.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

from .. import character
from ..parsers import air, ini
from ..source import Source

SCHEMA = "mugen2sms.air-source-identity/v1"
_ACTION = re.compile(r"^\[\s*begin\s+action\s+(-?\d+)\s*\]$", re.I)


def _has_explicit_loopstart(text: str, action_id: int) -> bool:
    current: int | None = None
    for raw in text.splitlines():
        line = ini.strip_comment(raw).strip()
        match = _ACTION.match(line)
        if match:
            current = int(match.group(1))
        elif current == action_id and line.lower().startswith("loopstart"):
            return True
    return False


def compile_action_record(action_id: int, action: air.Action, *,
                          package_name: str, package_sha256: str,
                          def_path: str, air_path: str, air_sha256: str,
                          explicit_loopstart: bool = False) -> dict:
    """Build an immutable source manifest for a single finite non-loop action."""
    if action.number != action_id:
        raise ValueError(f"action key {action_id} differs from parsed action {action.number}")
    if not action.frames:
        raise ValueError(f"AIR action {action_id} has no elements")
    if explicit_loopstart:
        raise ValueError(f"AIR action {action_id} has loopstart; terminal boundary is not reachable in one pass")

    durations = [frame.time for frame in action.frames]
    if any(type(value) is not int or not 0 < value < 32768 for value in durations):
        raise ValueError(f"AIR action {action_id} contains non-finite or ambiguous durations")

    boundaries = [0]
    for duration in durations:
        boundaries.append(boundaries[-1] + duration)

    elements = []
    for index, frame in enumerate(action.frames):
        element_id = f"{action_id}:{index}"
        elements.append({
            "element_id": element_id,
            "element_index": index,
            "source_line": frame.line,
            "group": frame.group,
            "image": frame.image,
            "x": frame.x,
            "y": frame.y,
            "duration": frame.time,
            "hflip": frame.hflip,
            "vflip": frame.vflip,
            "blend": frame.blend,
            "clsn1": [list(box) for box in frame.clsn1],
            "clsn2": [list(box) for box in frame.clsn2],
        })

    return {
        "schema": SCHEMA,
        "kind": "air_source_identity",
        "source": {
            "package_name": package_name,
            "package_sha256": package_sha256,
            "def_path": def_path,
            "air_path": air_path,
            "air_sha256": air_sha256,
        },
        "action_id": action_id,
        "action_line": action.line,
        "sequence_scope": "one_finite_non_looping_action_pass",
        "counter_bits": 16,
        "durations": durations,
        "boundary_element_ids": (
            [element["element_id"] for element in elements]
            + [f"{action_id}:terminal"]
        ),
        "boundary_cumulative_ticks": boundaries,
        "elements": elements,
        "limits": [
            "source AIR identity and order only; no ROM execution is measured",
            "terminal boundary applies to this finite non-looping action pass",
            "sprite pixel equality does not merge AIR element identities",
        ],
    }


def load_action(package: Path, action_id: int, def_name: str | None = None) -> dict:
    """Read a package without extracting it and compile one action from its AIR."""
    src = Source(package)
    parsed_character = character.load(src, def_name)
    action = parsed_character.anims.get(action_id)
    if action is None:
        raise ValueError(f"AIR action {action_id} not found in {parsed_character.def_path}")
    if any(re.search(rf"\baction\s+{action_id}\s+duplicada\b", warning, re.I)
           for warning in parsed_character.warnings):
        raise ValueError(f"AIR action {action_id} is duplicated; source identity is ambiguous")

    sections = ini.parse(ini.decode(src.read(parsed_character.def_path)))
    files = next((section for section in sections if section.name.lower() == "files"), None)
    anim_ref = files.get("anim") if files is not None else None
    if not anim_ref:
        raise ValueError(f"{parsed_character.def_path}: [Files] anim reference missing")
    base = str(PurePosixPath(parsed_character.def_path).parent)
    air_path = src.find(anim_ref, base)
    if air_path is None:
        raise ValueError(f"{parsed_character.def_path}: AIR reference cannot be resolved: {anim_ref}")
    air_bytes = src.read(air_path)
    air_text = ini.decode(air_bytes)
    return compile_action_record(
        action_id, action,
        package_name=package.name,
        package_sha256=src.sha256(),
        def_path=parsed_character.def_path,
        air_path=air_path,
        air_sha256=hashlib.sha256(air_bytes).hexdigest(),
        explicit_loopstart=_has_explicit_loopstart(air_text, action_id),
    )


def self_check() -> int:
    same_sprite = [air.Frame(0, 0, 0, 0, 6), air.Frame(0, 0, 0, 0, 6)]
    action = air.Action(200, same_sprite, line=12)
    record = compile_action_record(
        200, action, package_name="fixture.zip", package_sha256="a" * 64,
        def_path="fixture.def", air_path="fixture.air", air_sha256="b" * 64)
    ok = (record["durations"] == [6, 6]
          and record["boundary_element_ids"] == ["200:0", "200:1", "200:terminal"]
          and record["boundary_cumulative_ticks"] == [0, 6, 12]
          and record["elements"][0]["image"] == record["elements"][1]["image"])
    for bad_duration in (0, -1, 32768):
        bad = air.Action(201, [air.Frame(0, 0, 0, 0, bad_duration)])
        try:
            compile_action_record(201, bad, package_name="fixture.zip",
                                  package_sha256="a" * 64, def_path="fixture.def",
                                  air_path="fixture.air", air_sha256="b" * 64)
            ok = False
        except ValueError:
            pass
    try:
        compile_action_record(202, air.Action(202, [air.Frame(0, 0, 0, 0, 1)]),
                              package_name="fixture.zip", package_sha256="a" * 64,
                              def_path="fixture.def", air_path="fixture.air",
                              air_sha256="b" * 64, explicit_loopstart=True)
        ok = False
    except ValueError:
        pass
    print("self-check air_source_identity:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path, nargs="?")
    parser.add_argument("--def", dest="def_name")
    parser.add_argument("--action", type=int)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.package or args.action is None or not args.out:
        parser.error("package, --action e --out são obrigatórios sem --self-check")
    try:
        record = load_action(args.package, args.action, args.def_name)
    except (OSError, ValueError, KeyError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                        encoding="utf-8")
    print(f"[SOURCE ONLY] action {record['action_id']}: {len(record['durations'])} elements, "
          f"AIR SHA-256 {record['source']['air_sha256']} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
