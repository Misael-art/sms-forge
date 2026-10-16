"""Neutral OpenBOR front-end (O1): hash-bound extraction and typed IR with origin.

Front-end only: no console decisions (no MD or SMS budgets), no runtime
emission. Every IR node carries origin — member path, source line, byte span
and raw-line SHA-256 — bound to the extracted file SHA-256. Fail closed on
identity mismatch or underivable origin; never silently drop a directive.

CLI (via python3 -m openbor2sms):
  extract  --pak <f> --expect-sha256 <hex> --expect-bytes <N> --member <m>...
           --destination <dir> --out <record.json>
  ir       --kind level|models_index --source <f> --member <m>
           --source-sha256 <hex> [--pak-sha256 <hex>]
           [--models-index <f> --models-index-member <m>]
           --out <ir.json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from .level_inventory import build_level_inventory
    from .model_text import parse_level, parse_models_index
    from .pak import PakError, find_entry, read_entry, read_index, sha256_file
    from .reference_semantics import compile_level_event_ir
except ImportError:  # direct script use (python3 openbor2sms/frontend.py)
    from level_inventory import build_level_inventory
    from model_text import parse_level, parse_models_index
    from pak import PakError, find_entry, read_entry, read_index, sha256_file
    from reference_semantics import compile_level_event_ir

SCHEMA_EXTRACT = "openbor_sms_extraction_record_v1"
SCHEMA_LEVEL_IR = "openbor_sms_frontend_level_ir_v1"
SCHEMA_MODELS_IR = "openbor_sms_frontend_models_ir_v1"

MODES = ("extract", "ir")

ORIGIN_SCHEME = (
    "member + line (1-based over str.splitlines) + byte_offset/byte_length "
    "(over the extracted file bytes) + raw_sha256 of the raw line bytes"
)

# Values whose unit is established by the ported pinned-reference semantics.
# Everything else stays explicitly undeclared: the SMS backend pins units when
# it consumes a value, and O1 never guesses one.
UNIT_DECLARATIONS = {
    "delay": {
        "unit": "centisecond-shaped",
        "status": "hypothesis",
        "basis": "analyze.delay_to_frames docstring (ChronoCrash animation page + legacy manual; no version-pinned trace yet)",
    },
    "makeinv": {
        "unit": "seconds * game_speed (200 logical ticks/s), signed; arg2 nonzero negates and disables blink",
        "status": "pinned_reference",
        "basis": "reference_semantics.lower_makeinv / REFERENCE_PROFILE at 787b6770409935137579715febf80cf7a529b748",
    },
}


class FrontendError(ValueError):
    """A front-end input failed a declared identity/precondition check."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write_json(path: Path, payload: dict, force: bool) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        if not force:
            raise FrontendError(f"output already exists (use --force to replace): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def line_spans(text: str) -> list[tuple[int, int]]:
    """Byte span (offset, length) per str.splitlines() line, origin-exact.

    Supports \\n, \\r\\n and \\r terminators only; any other line break makes
    the byte walk ambiguous and the source is rejected instead of guessed.
    """
    spans: list[tuple[int, int]] = []
    pos = 0
    byte_offset = 0
    for line in text.splitlines():
        if not text.startswith(line, pos):
            raise FrontendError(
                f"line span walk diverged at char {pos}: unsupported line break or non-contiguous text"
            )
        encoded = line.encode("utf-8")
        spans.append((byte_offset, len(encoded)))
        pos += len(line)
        byte_offset += len(encoded)
        if pos < len(text):
            if text.startswith("\r\n", pos):
                pos += 2
                byte_offset += 2
            elif text[pos] in "\r\n":
                pos += 1
                byte_offset += 1
            else:
                raise FrontendError(
                    f"unsupported line break at char {pos} (only \\n, \\r\\n and \\r are supported)"
                )
    if pos != len(text):
        raise FrontendError("line span walk did not consume the whole source")
    return spans


def _load_source(path: Path, expect_sha256: str | None) -> tuple[bytes, str, str]:
    path = Path(path)
    if not path.is_file():
        raise FrontendError(f"source not readable: {path}")
    data = path.read_bytes()
    digest = sha256_file(path)
    if expect_sha256 is not None and digest != expect_sha256.lower():
        raise FrontendError(
            f"source identity mismatch for {path}: sha256 expected {expect_sha256.lower()} got {digest}"
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise FrontendError(f"{path}: source is not UTF-8: {error}") from error
    return data, digest, text


def _line_origin(text: str, spans: list[tuple[int, int]], source_bytes: bytes, line: int, raw: str) -> dict:
    if not 1 <= line <= len(spans):
        raise FrontendError(f"line {line} outside the {len(spans)} parsed lines")
    byte_offset, byte_length = spans[line - 1]
    blob = source_bytes[byte_offset : byte_offset + byte_length]
    if blob != raw.encode("utf-8"):
        raise FrontendError(f"line {line}: byte span does not reproduce the raw line")
    return {
        "line": line,
        "byte_offset": byte_offset,
        "byte_length": byte_length,
        "raw_sha256": hashlib.sha256(blob).hexdigest(),
    }


def extract_pak_members(
    pak_path,
    expect_sha256: str,
    expect_bytes: int,
    members,
    destination,
    generated_at: str | None = None,
    force: bool = False,
) -> dict:
    """Extract named members under a hash-verified PAK and emit the record.

    Refuses: identity mismatch, missing/ambiguous/unsafe member, path escape,
    or an existing different file at a target. Reuses an existing identical
    file so a re-run is idempotent instead of destructive.
    """
    pak_path = Path(pak_path)
    destination = Path(destination)
    if not pak_path.is_file():
        raise FrontendError(f"PAK not readable: {pak_path}")
    if not members:
        raise FrontendError("no members requested")
    data = pak_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expect_sha256.lower():
        raise FrontendError(
            f"PAK identity mismatch: sha256 expected {expect_sha256.lower()} got {digest}"
        )
    if len(data) != expect_bytes:
        raise FrontendError(f"PAK identity mismatch: bytes expected {expect_bytes} got {len(data)}")
    index = read_index(data)

    rows = []
    for raw_member in members:
        entry = find_entry(index, raw_member)
        blob = read_entry(data, entry)
        target = (destination / entry.normalized_name).resolve()
        destination_resolved = destination.resolve()
        if destination_resolved != target and destination_resolved not in target.parents:
            raise FrontendError(f"normalized member path escapes destination: {entry.normalized_name}")
        reused = False
        if target.exists():
            if target.read_bytes() != blob:
                if not force:
                    raise FrontendError(
                        f"target exists with different bytes (use --force to replace): {target}"
                    )
            else:
                reused = True
        if not reused:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
        written = target.read_bytes()
        if written != blob:
            raise FrontendError(f"extracted bytes diverged from PAK member: {entry.normalized_name}")
        rows.append(
            {
                "member": entry.normalized_name,
                "pak_name": entry.original_name,
                "path": entry.normalized_name,
                "bytes": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(),
                "reused_existing": reused,
            }
        )
    return {
        "schema": SCHEMA_EXTRACT,
        "generated_at": generated_at or utc_now(),
        "tool": "openbor2sms frontend extract",
        "pak": {
            "path": str(pak_path),
            "bytes": len(data),
            "sha256": digest,
            "format_id": index.format_id,
            "format_name": index.format_name,
            "file_count": index.file_count,
        },
        "expected": {"sha256": expect_sha256.lower(), "bytes": expect_bytes, "verified": True},
        "destination": str(destination),
        "members": rows,
        "claim_ceiling": (
            "hash-bound extraction of named members only; containment does not prove parsing, "
            "conversion or runtime suitability"
        ),
    }


def _units_block(commands) -> dict:
    present = sorted(set(commands))
    declared = [
        {"command": command, **UNIT_DECLARATIONS[command]}
        for command in present
        if command in UNIT_DECLARATIONS
    ]
    return {
        "policy": (
            "integers pass through unchanged; O1 declares a unit only where the ported pinned "
            "reference semantics establish one, and the SMS backend pins consumption units later"
        ),
        "declared": declared,
        "undeclared_commands": [command for command in present if command not in UNIT_DECLARATIONS],
    }


def _models_index_block(data: bytes, digest: str, text: str, models_index_member: str, models_index_path) -> dict:
    entries = parse_models_index(text)
    spans = line_spans(text)
    lines = text.splitlines()
    rows = []
    for alias, path, line in entries:
        origin = _line_origin(text, spans, data, line, lines[line - 1])
        rows.append({"alias": alias, "path": path, **origin})
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["alias"].casefold(), []).append(row)
    duplicates = [
        {
            "alias_key": key,
            "occurrences": len(group),
            "entries": [{"alias": row["alias"], "path": row["path"], "line": row["line"]} for row in group],
        }
        for key, group in sorted(grouped.items())
        if len(group) > 1
    ]
    return {
        "member": models_index_member,
        "path": str(models_index_path),
        "bytes": len(data),
        "sha256": digest,
        "entry_count": len(rows),
        "entries": rows,
        "duplicate_aliases": duplicates,
    }


def level_ir(
    source_path,
    member: str,
    expect_sha256: str,
    pak_sha256: str | None = None,
    models_index_path=None,
    models_index_member: str | None = None,
    generated_at: str | None = None,
) -> dict:
    """Typed, origin-annotated IR for one level member. Deterministic for equal inputs."""
    data, digest, text = _load_source(Path(source_path), expect_sha256)
    level = parse_level(text, path=member)
    spans = line_spans(text)
    if len(spans) != len(text.splitlines()):
        raise FrontendError("line span count diverged from the parser line model")

    directives = []
    for item in level.timeline:
        origin = _line_origin(text, spans, data, item.line, item.raw)
        directives.append(
            {"command": item.command, "args": list(item.args), "raw": item.raw, **origin}
        )
    counts: dict[str, list[int]] = {}
    for item in level.timeline:
        counts.setdefault(item.command, []).append(item.line)
    directive_matrix = [
        {"command": command, "occurrences": len(lines), "source_lines": sorted(lines)}
        for command, lines in sorted(counts.items())
    ]

    source_lines = text.splitlines()
    spawns = [
        {
            "name": spawn.name,
            "at": spawn.at,
            "health": spawn.health,
            "coords": list(spawn.coords) if spawn.coords else None,
            "flip": spawn.flip,
            **_line_origin(text, spans, data, spawn.line, source_lines[spawn.line - 1]),
        }
        for spawn in level.spawns
    ]
    player_starts = [
        {
            "slot": start.slot,
            "x": start.x,
            "z": start.z,
            "y": start.y,
            "raw": start.raw,
            **_line_origin(text, spans, data, start.line, start.raw),
        }
        for start in level.player_starts
    ]

    limitations = [
        "Source-ordered IR only: no concurrency, timing, collision, audio or gameplay claim.",
        "The embedded event_ir projection is ported verbatim from the donor module; its claim text keeps referring to the donor runtime and no SMS runtime consumes this IR yet.",
    ]
    payload = {
        "schema": SCHEMA_LEVEL_IR,
        "generated_at": generated_at or utc_now(),
        "tool": "openbor2sms frontend ir",
        "ir_kind": "level",
        "origin_scheme": ORIGIN_SCHEME,
        "source": {"member": member, "path": str(source_path), "bytes": len(data), "sha256": digest},
        "pak_sha256": pak_sha256.lower() if pak_sha256 else None,
        "directives": directives,
        "directive_matrix": directive_matrix,
        "spawns": spawns,
        "player_starts": player_starts,
        "issues": list(level.issues),
        "units": _units_block(item.command for item in level.timeline),
        "event_ir": compile_level_event_ir(level),
    }
    if models_index_path is not None:
        if not models_index_member:
            raise FrontendError("models_index_member is required with models_index_path")
        models_path = Path(models_index_path)
        mdata, mdigest, mtext = _load_source(models_path, None)
        models = _models_index_block(mdata, mdigest, mtext, models_index_member, models_path)
        inventory = build_level_inventory(
            level, [(row["alias"], row["path"], row["line"]) for row in models["entries"]]
        )
        payload["models_index"] = models
        payload["inventory"] = inventory
    else:
        limitations.append("No models index was provided; spawn aliases stay unresolved in this file.")
    payload["limitations"] = limitations
    payload["claim_ceiling"] = (
        "typed IR with origin within the O1 front-end only; no emission, runtime, budget or conversion claim"
    )
    return payload


def models_ir(
    source_path,
    member: str,
    expect_sha256: str,
    pak_sha256: str | None = None,
    generated_at: str | None = None,
) -> dict:
    """Typed, origin-annotated IR for one models-index member. Deterministic."""
    data, digest, text = _load_source(Path(source_path), expect_sha256)
    block = _models_index_block(data, digest, text, member, source_path)
    return {
        "schema": SCHEMA_MODELS_IR,
        "generated_at": generated_at or utc_now(),
        "tool": "openbor2sms frontend ir",
        "ir_kind": "models_index",
        "origin_scheme": ORIGIN_SCHEME,
        "source": {"member": member, "path": str(source_path), "bytes": len(data), "sha256": digest},
        "pak_sha256": pak_sha256.lower() if pak_sha256 else None,
        "entries": block["entries"],
        "duplicate_aliases": block["duplicate_aliases"],
        "issues": [],
        "units": _units_block([]),
        "limitations": [
            "Index IR only: aliases and paths as written; model files, behavior and eligibility are not parsed here.",
            "duplicate_aliases marks case-insensitive alias collisions; spawn resolution treats those records as ambiguous.",
        ],
        "claim_ceiling": "typed IR with origin within the O1 front-end only; no model behavior, runtime or conversion claim",
    }


def self_check() -> int:
    import tempfile

    try:
        from .pak import build_pak32
    except ImportError:  # direct script use
        from pak import build_pak32

    level_text = (
        "music data/music/STAGE1.BOR\r\n"
        "spawn long\r\n"
        "coords 10 180\r\n"
        "at 0\r\n"
        "\r\n"
        "spawn second\r\n"
        "# comment only\r\n"
        "spawn1 50 20 200\r\n"
    )
    models_text = (
        "load Long data/chars/long/long.txt\n"
        "know Item data/items/item.txt\n"
        "load Pickup data/items/pickup.txt\n"
        "know pickup data/items/pickup_alt.txt\n"
    )
    blob = build_pak32(
        [("DATA/Levels/LV1.txt", level_text.encode("utf-8")), ("data/models.txt", models_text.encode("utf-8"))]
    )
    stamp = "2026-01-01T00:00:00+00:00"

    with tempfile.TemporaryDirectory(prefix="openbor2sms-frontend-") as tmp:
        tmp = Path(tmp)
        pak = tmp / "fixture.pak"
        pak.write_bytes(blob)
        digest = sha256_file(pak)
        dest = tmp / "extracted"
        record = extract_pak_members(
            pak, digest, len(blob), ["data/levels/lv1.txt", "data/models.txt"], dest, generated_at=stamp
        )
        assert record["expected"]["verified"] is True
        assert [row["member"] for row in record["members"]] == ["data/levels/lv1.txt", "data/models.txt"]
        assert (dest / "data/levels/lv1.txt").read_bytes() == level_text.encode("utf-8")
        again = extract_pak_members(
            pak, digest, len(blob), ["data/levels/lv1.txt"], dest, generated_at=stamp
        )
        assert again["members"][0]["reused_existing"] is True

        for bad in (
            lambda: extract_pak_members(pak, "0" * 64, len(blob), ["data/models.txt"], tmp / "x"),
            lambda: extract_pak_members(pak, digest, len(blob) + 1, ["data/models.txt"], tmp / "x"),
            lambda: extract_pak_members(pak, digest, len(blob), ["data/missing.txt"], tmp / "x"),
        ):
            try:
                bad()
            except (FrontendError, PakError):
                pass
            else:
                raise AssertionError("expected extraction precondition failure was not raised")

        level_file = dest / "data/levels/lv1.txt"
        first = level_ir(
            level_file,
            "data/levels/lv1.txt",
            sha256_file(level_file),
            pak_sha256=digest,
            models_index_path=dest / "data/models.txt",
            models_index_member="data/models.txt",
            generated_at=stamp,
        )
        second = level_ir(
            level_file,
            "data/levels/lv1.txt",
            sha256_file(level_file),
            pak_sha256=digest,
            models_index_path=dest / "data/models.txt",
            models_index_member="data/models.txt",
            generated_at=stamp,
        )
        assert first == second, "level IR is not deterministic"
        assert first["issues"], "missing diagnostics for the spawn without at"
        assert any("spawn second is not followed" in issue for issue in first["issues"])
        assert first["directive_matrix"][0]["command"] == "at"
        assert first["units"]["undeclared_commands"] == ["at", "coords", "music", "spawn", "spawn1"]
        assert first["inventory"]["unresolved_spawn_aliases"] == [{"line": 6, "name": "second"}]
        assert first["inventory"]["dynamic_spawns"][0]["alias_match"]["path"] == "data/chars/long/long.txt"

        source_bytes = level_text.encode("utf-8")
        for row in first["directives"]:
            span = source_bytes[row["byte_offset"] : row["byte_offset"] + row["byte_length"]]
            assert span.decode("utf-8") == row["raw"], row
        for row in first["spawns"]:
            span = source_bytes[row["byte_offset"] : row["byte_offset"] + row["byte_length"]]
            assert span.decode("utf-8").split()[0] == "spawn", row

        models_file = dest / "data/models.txt"
        m_ir = models_ir(models_file, "data/models.txt", sha256_file(models_file), pak_sha256=digest, generated_at=stamp)
        assert m_ir["duplicate_aliases"][0]["alias_key"] == "pickup"
        assert m_ir["duplicate_aliases"][0]["occurrences"] == 2
        assert m_ir["entries"][0]["line"] == 1 and m_ir["entries"][0]["byte_offset"] == 0

        mixed = tmp / "mixed.txt"
        mixed.write_bytes(b"spawn a\r\nspawn b\r")
        mixed_ir = level_ir(mixed, "data/levels/mixed.txt", sha256_file(mixed), generated_at=stamp)
        assert [row["line"] for row in mixed_ir["directives"]] == [1, 2]

        bad_utf8 = tmp / "bad.txt"
        bad_utf8.write_bytes(b"spawn a\xff\n")
        try:
            level_ir(bad_utf8, "data/levels/bad.txt", sha256_file(bad_utf8), generated_at=stamp)
        except FrontendError:
            pass
        else:
            raise AssertionError("non-UTF-8 source was not rejected")

        odd_break = tmp / "odd.txt"
        odd_break.write_text("spawn a\x0bignore 1\n", encoding="utf-8")
        try:
            level_ir(odd_break, "data/levels/odd.txt", sha256_file(odd_break), generated_at=stamp)
        except FrontendError:
            pass
        else:
            raise AssertionError("unsupported line break was not rejected")

        try:
            level_ir(level_file, "data/levels/lv1.txt", "0" * 64, generated_at=stamp)
        except FrontendError:
            pass
        else:
            raise AssertionError("source sha mismatch was not rejected")

    print("[SELF-CHECK OK] openbor2sms frontend (extract identity, IR origin byte spans, determinism, fail-closed)")
    return 0


def _summarize_existing(record: dict) -> str:
    return (
        f"pak sha256={record['pak']['sha256'][:16]}... members={len(record['members'])} "
        f"destination={record['destination']}"
    )


def _summarize_ir(record: dict) -> str:
    if record["ir_kind"] == "level":
        return (
            f"level IR member={record['source']['member']} directives={len(record['directives'])} "
            f"issues={len(record['issues'])} sha256={record['source']['sha256'][:16]}..."
        )
    return (
        f"models IR member={record['source']['member']} entries={len(record['entries'])} "
        f"duplicates={len(record['duplicate_aliases'])} sha256={record['source']['sha256'][:16]}..."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="openbor2sms frontend", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", nargs="?", choices=MODES)
    parser.add_argument("--pak")
    parser.add_argument("--expect-sha256")
    parser.add_argument("--expect-bytes", type=int)
    parser.add_argument("--member", action="append", default=[])
    parser.add_argument("--destination")
    parser.add_argument("--source")
    parser.add_argument("--source-sha256")
    parser.add_argument("--pak-sha256")
    parser.add_argument("--kind", choices=["level", "models_index"])
    parser.add_argument("--models-index")
    parser.add_argument("--models-index-member")
    parser.add_argument("--out")
    parser.add_argument("--generated-at")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)

    if args.self_check:
        return self_check()
    if not args.mode:
        parser.error("mode required unless --self-check")
    try:
        if args.mode == "extract":
            if not (args.pak and args.expect_sha256 and args.expect_bytes is not None
                    and args.member and args.destination and args.out):
                parser.error("extract needs --pak, --expect-sha256, --expect-bytes, --member, --destination and --out")
            record = extract_pak_members(
                args.pak, args.expect_sha256, args.expect_bytes, args.member, args.destination,
                args.generated_at, args.force,
            )
        else:
            if not (args.source and args.member and args.source_sha256 and args.kind and args.out):
                parser.error("ir needs --source, --member, --source-sha256, --kind and --out")
            if len(args.member) != 1:
                parser.error("ir takes exactly one --member")
            if args.kind == "level":
                record = level_ir(
                    args.source, args.member[0], args.source_sha256, args.pak_sha256,
                    args.models_index, args.models_index_member, args.generated_at,
                )
            else:
                if args.models_index:
                    parser.error("--models-index only applies to --kind level")
                record = models_ir(
                    args.source, args.member[0], args.source_sha256, args.pak_sha256, args.generated_at
                )
        _write_json(Path(args.out), record, args.force)
    except (FrontendError, PakError, OSError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    print(f"[OK] {_summarize_existing(record) if args.mode == 'extract' else _summarize_ir(record)}")
    print(f"     out: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
