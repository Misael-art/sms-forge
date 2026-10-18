#!/usr/bin/env python3
"""Pack AIR frame descriptors and CLSN into mapper pages for the SMS runtime."""
from __future__ import annotations

import argparse
import re
import struct
from pathlib import Path

PAGE_BYTES = 16384
FRAME_RECORD_BYTES = 11
NO_CLSN = 0xFFFF


def number(value: str) -> int:
    return int(value.strip().rstrip("uU"), 0)


def split_fields(row: str) -> list[str]:
    return [field.strip() for field in row.split(",")]


def parse_arrays(text: str) -> tuple[dict[str, bytes], dict[str, str]]:
    arrays: dict[str, bytes] = {}
    for name, size, body in re.findall(
        r"const unsigned char\s+(\w+)\[(\d+)\]\s*=\s*\{(.*?)\};",
        text, re.S,
    ):
        values = [int(value, 0) for value in re.findall(r"0x[0-9a-fA-F]+|\b\d+\b", body)]
        if len(values) != int(size) or any(value < 0 or value > 255 for value in values):
            raise ValueError(f"malformed byte array {name}: declared {size}, found {len(values)}")
        arrays[name] = bytes(values)
    aliases = dict(re.findall(r"^#define\s+(\w+)\s+(\w+)\s*$", text, re.M))
    return arrays, aliases


def resolve(name: str, arrays: dict[str, bytes], aliases: dict[str, str]) -> bytes:
    if name in ("0", "NULL"):
        return b""
    seen: set[str] = set()
    while name not in arrays:
        if name in seen or name not in aliases:
            raise ValueError(f"unresolved source array {name}")
        seen.add(name)
        name = aliases[name]
    return arrays[name]


def parse_actor(text: str, actor: str, arrays: dict[str, bytes],
                aliases: dict[str, str]) -> tuple[bytes, list[tuple[int, int, int, int]], int, int]:
    frame_match = re.search(
        rf"static const Frame {actor}_frames_all\[\w+\] = \{{(.*?)\n\}};",
        text, re.S,
    )
    anim_match = re.search(
        rf"static const Anim {actor}_anims\[\w+\] = \{{(.*?)\n\}};",
        text, re.S,
    )
    if not frame_match or not anim_match:
        raise ValueError(f"missing {actor} Frame/Anim table")

    record_values: list[tuple[int, int, int, int, int, int, int, int]] = []
    clsn_pool = bytearray()
    clsn_offsets: dict[bytes, int] = {}
    max_clsn = 1
    for row in frame_match.group(1).splitlines():
        row = row.strip()
        if not row.startswith("{"):
            continue
        fields = split_fields(row.strip("{}, \t"))
        if len(fields) != 10:
            raise ValueError(f"{actor} Frame row has {len(fields)} fields, expected 10: {row[:100]}")
        duration, pose = number(fields[0]), number(fields[1])
        clsn = resolve(fields[4], arrays, aliases)
        axis = resolve(fields[5], arrays, aliases)
        width, height = number(fields[6]), number(fields[7])
        if not 0 <= duration <= 255 or not 0 <= pose <= 255:
            raise ValueError(f"{actor} frame duration/pose exceeds a byte")
        if not 0 <= width <= 255 or not 0 <= height <= 255:
            raise ValueError(f"{actor} frame dimensions exceed a byte")
        if len(axis) != 4:
            raise ValueError(f"{actor} frame axis must be four bytes, got {len(axis)}")
        if clsn and len(clsn) > 255:
            raise ValueError(f"{actor} CLSN exceeds the byte-sized runtime buffer: {len(clsn)}")
        max_clsn = max(max_clsn, len(clsn))
        if clsn:
            offset = clsn_offsets.get(clsn)
            if offset is None:
                offset = len(clsn_pool)
                clsn_offsets[clsn] = offset
                clsn_pool.extend(clsn)
        else:
            offset = NO_CLSN
        axis_x, axis_y = struct.unpack("<hh", axis)
        record_values.append((duration, pose, width, height, axis_x, axis_y,
                              offset, len(clsn)))
    if not record_values:
        raise ValueError(f"empty {actor} frame table")

    table_bytes = len(record_values) * FRAME_RECORD_BYTES
    records = [
        struct.pack("<BBBBhhHB", duration, pose, width, height, axis_x, axis_y,
                    NO_CLSN if clsn_off == NO_CLSN else table_bytes + clsn_off,
                    clsn_len)
        for duration, pose, width, height, axis_x, axis_y, clsn_off, clsn_len
        in record_values
    ]
    if any(len(record) != FRAME_RECORD_BYTES for record in records):
        raise AssertionError("Frame record schema size drift")
    descriptor = b"".join(records)
    if len(descriptor) + len(clsn_pool) > PAGE_BYTES:
        raise ValueError(
            f"{actor} frame data needs {len(descriptor) + len(clsn_pool)} B; "
            f"one bank holds {PAGE_BYTES} B"
        )
    actor_blob = descriptor + clsn_pool

    animations: list[tuple[int, int, int, int]] = []
    for row in anim_match.group(1).splitlines():
        row = row.strip()
        if not row.startswith("{"):
            continue
        match = re.fullmatch(
            rf"\{{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*"
            rf"{actor}_frames_all\s*\+\s*(\d+)\s*\}}\s*,?",
            row,
        )
        if not match:
            raise ValueError(f"unparsed {actor} Anim row: {row}")
        action, count, loop_start, first = map(int, match.groups())
        if first + count > len(records):
            raise ValueError(f"{actor} animation {action} exceeds its Frame table")
        if loop_start != 255 and loop_start >= count:
            raise ValueError(f"{actor} animation {action} loop start is out of range")
        animations.append((action, count, loop_start, first))
    if not animations:
        raise ValueError(f"empty {actor} Anim table")
    return actor_blob, animations, len(records), max_clsn


def pack(text: str, first_bank: int) -> tuple[str, bytes, dict]:
    if not 2 <= first_bank <= 255:
        raise ValueError(f"invalid first data bank {first_bank}")
    arrays, aliases = parse_arrays(text)
    actor_blobs: dict[str, bytes] = {}
    actor_anims: dict[str, list[tuple[int, int, int, int]]] = {}
    actor_frame_counts: dict[str, int] = {}
    actor_max_clsn: dict[str, int] = {}
    for actor in ("ken", "ryu"):
        actor_blob, animations, frame_count, max_clsn = parse_actor(
            text, actor, arrays, aliases
        )
        actor_blobs[actor] = actor_blob
        actor_anims[actor] = animations
        actor_frame_counts[actor] = frame_count
        actor_max_clsn[actor] = max_clsn

    if actor_blobs["ken"] == actor_blobs["ryu"]:
        layout = {"ken": (first_bank, 0), "ryu": (first_bank, 0)}
        images = [actor_blobs["ken"]]
    elif len(actor_blobs["ken"]) + len(actor_blobs["ryu"]) <= PAGE_BYTES:
        layout = {"ken": (first_bank, 0),
                  "ryu": (first_bank, len(actor_blobs["ken"]))}
        images = [actor_blobs["ken"] + actor_blobs["ryu"]]
    else:
        layout = {"ken": (first_bank, 0), "ryu": (first_bank + 1, 0)}
        images = [actor_blobs["ken"], actor_blobs["ryu"]]

    if first_bank + len(images) - 1 > 255:
        raise ValueError("frame data exceeds the 8-bit mapper range")
    blob = b"".join(image + bytes(PAGE_BYTES - len(image)) for image in images)
    lines = [
        "/* generated by mugen2sms/generators/source_frame_data.py */",
        "#ifndef SOURCE_FRAME_DATA_H", "#define SOURCE_FRAME_DATA_H",
        "#define FRAME_CACHE_FRAME_BYTES 10u",
        f"#define FRAME_CLSN_BUFFER_BYTES "
        f"{max(actor_max_clsn.values())}u",
        f"#define FRAME_CACHE_STRIDE "
        f"{10 + max(actor_max_clsn.values())}u",
    ]
    for actor in ("ken", "ryu"):
        bank, offset = layout[actor]
        upper = actor.upper()
        animations = actor_anims[actor]
        lines += [
            f"#define {upper}_FRAME_DATA_BANK {bank}u",
            f"#define {upper}_FRAME_DATA_OFF {offset}u",
            f"#define {upper}_FRAME_COUNT {actor_frame_counts[actor]}u",
            f"static const Anim {actor}_anims[{len(animations)}] = {{",
        ]
        lines.extend(
            f"    {{ {action}u, {count}u, {loop_start}u, {first}u }},"
            for action, count, loop_start, first in animations
        )
        lines.append("};")
    lines += ["#endif", ""]
    stats = {
        "frame_record_bytes": FRAME_RECORD_BYTES,
        "first_bank": first_bank,
        "bank_count": len(images),
        "banks": {actor: layout[actor][0] for actor in layout},
        "offsets": {actor: layout[actor][1] for actor in layout},
        "actor_bytes": {actor: len(actor_blobs[actor]) for actor in actor_blobs},
        "actor_frame_counts": actor_frame_counts,
        "anim_counts": {actor: len(actor_anims[actor]) for actor in actor_anims},
        "max_clsn_bytes": actor_max_clsn,
    }
    return "\n".join(lines), blob, stats


def self_check() -> None:
    header = """#define A_META_SIZE 4
const unsigned char A_META[4] = {0, 1, 2, 0x80};
const unsigned char A_CLSN[10] = {1, 0x80, 0, 0, 0, 0, 0, 0, 1, 0x80};
const unsigned char A_AXIS[4] = {0xfe, 0xff, 0x04, 0};
static const Frame ken_frames_all[1] = {
    { 6, 0, A_META, A_META, A_CLSN, A_AXIS, 32, 64, A_META, A_META },
};
static const Anim ken_anims[1] = {
    { 0, 1, 0, ken_frames_all + 0 },
};
static const Frame ryu_frames_all[1] = {
    { 6, 0, A_META, A_META, A_CLSN, A_AXIS, 32, 64, A_META, A_META },
};
static const Anim ryu_anims[1] = {
    { 0, 1, 0, ryu_frames_all + 0 },
};
"""
    out_header, blob, stats = pack(header, 44)
    assert len(blob) == PAGE_BYTES
    assert stats["banks"] == {"ken": 44, "ryu": 44}
    assert stats["actor_frame_counts"] == {"ken": 1, "ryu": 1}
    assert "#define FRAME_CACHE_FRAME_BYTES 10u" in out_header
    assert "{ 0u, 1u, 0u, 0u }" in out_header
    record = blob[:FRAME_RECORD_BYTES]
    dur, pose, width, height, ax, ay, clsn_off, clsn_len = struct.unpack("<BBBBhhHB", record)
    assert (dur, pose, width, height, ax, ay, clsn_off, clsn_len) == (
        6, 0, 32, 64, -2, 4, FRAME_RECORD_BYTES, 10
    )
    try:
        pack(header.replace("A_AXIS[4]", "A_AXIS[3]"), 44)
    except ValueError:
        pass
    else:
        raise AssertionError("truncated axis was accepted")
    print("[PASS] source_frame_data self-check (frame schema, CLSN, actor-page reuse)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--header", type=Path)
    parser.add_argument("--first-bank", type=int)
    parser.add_argument("--out-header", type=Path)
    parser.add_argument("--out-banks", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    if not all((args.header, args.first_bank is not None, args.out_header, args.out_banks)):
        parser.error("--header, --first-bank, --out-header and --out-banks are required")
    header, blob, stats = pack(args.header.read_text(encoding="utf-8"), args.first_bank)
    args.out_header.parent.mkdir(parents=True, exist_ok=True)
    args.out_banks.parent.mkdir(parents=True, exist_ok=True)
    args.out_header.write_text(header, encoding="utf-8")
    args.out_banks.write_bytes(blob)
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
