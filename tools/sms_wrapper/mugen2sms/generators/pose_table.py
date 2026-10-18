#!/usr/bin/env python3
"""Build banked pose metasprites and row tables for the integrated SMS runtime."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FIRST_BANK = 2
PAIR = 64
END = 0x80
BANK_BYTES = 16384
POSE_INDEX_RECORD_BYTES = 11
POSE_CACHE_RECORD_BYTES = 12


def arr(text: str, name: str) -> list[int]:
    original = name
    seen: set[str] = set()
    while name not in seen:
        seen.add(name)
        match = re.search(
            rf"const unsigned char {re.escape(name)}\[\d+\] = \{{(.*?)\}};",
            text,
            re.S,
        )
        if match:
            return [int(value, 16) for value in re.findall(r"0x[0-9A-Fa-f]+", match.group(1))]
        alias = re.search(rf"^#define {re.escape(name)}\s+([A-Za-z_]\w*)\s*$", text, re.M)
        if not alias:
            break
        name = alias.group(1)
    raise KeyError(f"{original} (metadata alias chain unresolved)")


def define(text: str, name: str) -> int:
    match = re.search(rf"^#define {re.escape(name)} (\d+)", text, re.M)
    if not match:
        raise KeyError(name)
    return int(match.group(1))


def s8(value: int) -> int:
    return value - 256 if value > 127 else value


def prune(meta: list[int], blob: bytes) -> list[int]:
    if not meta or meta[-1] != END:
        raise ValueError("metasprite sem terminador")
    out = []
    for i in range(0, len(meta) - 1, 3):
        dx, dy, tile = meta[i:i + 3]
        if s8(dy) % 16:
            raise ValueError(f"dy {s8(dy)} fora da grade TALL")
        pair = blob[(tile // 2) * PAIR:(tile // 2 + 1) * PAIR]
        if len(pair) != PAIR:
            raise ValueError("par fora do blob")
        if pair != bytes(PAIR):
            out += [dx, dy, tile]
    if len(out) // 3 > 64:
        raise ValueError("pose com mais de 64 pecas")
    dys = [s8(value) for value in out[1::3]]
    if dys != sorted(dys):
        raise ValueError("pecas fora de ordem de linha (dy decrescente)")
    return out + [END]


def row_table(meta: list[int]) -> list[int]:
    """[count, dy0, n0, dy1, n1, ...] in metasprite order (rows contiguous)."""
    rows: list[list[int]] = []
    for dy in meta[1:-1:3]:
        if rows and rows[-1][0] == dy:
            rows[-1][1] += 1
        else:
            rows.append([dy, 1])
    return [len(rows)] + [value for row in rows for value in row]


def widest_row(meta: list[int]) -> int:
    dys = [s8(value) for value in meta[1:-1:3]]
    return max((dys.count(dy) for dy in set(dys)), default=0)


def resolve_meta_bank(source_bank_count: int, requested: int | None = None) -> int:
    first_free = FIRST_BANK + source_bank_count
    bank = first_free if requested is None else requested
    if bank < first_free:
        raise ValueError(
            f"metadata bank {bank} overlaps source banks "
            f"{FIRST_BANK}..{first_free - 1}; first free is {first_free}"
        )
    if bank > 255:
        raise ValueError(f"metadata bank {bank} exceeds the 8-bit mapper range")
    return bank


def metadata_layout(sizes: dict[str, int], first_bank: int) -> tuple[dict[str, tuple[int, int]], int]:
    ken_size, ryu_size = sizes["ken"], sizes["ryu"]
    if ken_size + ryu_size <= BANK_BYTES:
        return {"ken": (first_bank, 0), "ryu": (first_bank, ken_size)}, 1
    if ken_size <= BANK_BYTES and ryu_size <= BANK_BYTES:
        return {"ken": (first_bank, 0), "ryu": (first_bank + 1, 0)}, 2
    raise ValueError(
        "metadata de um lutador excede 16 KiB; precisa de uma tabela por fatias bancadas"
    )


def build(text: str, banks: bytes, meta_bank: int | None = None,
          index_bank: int | None = None) -> tuple[str, dict, bytes, bytes | None]:
    if len(banks) % BANK_BYTES:
        raise ValueError(f"source bank image is not a multiple of {BANK_BYTES} bytes")
    source_bank_count = len(banks) // BANK_BYTES
    first_meta_bank = resolve_meta_bank(source_bank_count, meta_bank)
    stats = {"source_bank_count": source_bank_count}
    actor_blobs: dict[str, bytearray] = {}
    actor_tables: dict[str, dict] = {}
    actor_raw_meta_bytes: dict[str, int] = {}
    for who, p2 in (("ken", False), ("ryu", True)):
        match = re.search(
            rf"static const Frame {who}_frames_all\[\w+\] = \{{(.*?)\n\}};",
            text,
            re.S,
        )
        if not match:
            raise ValueError(f"missing {who}_frames_all")
        frame_rows = [line for line in match.group(1).splitlines() if line.strip().startswith("{")]
        actor_blob = bytearray()
        interned_chunks: dict[bytes, int] = {}
        raw_meta_bytes = 0

        def append_chunk(chunk: bytes) -> int:
            """Store identical pose/row records once per actor ROM bank."""
            nonlocal raw_meta_bytes
            raw_meta_bytes += len(chunk)
            if chunk in interned_chunks:
                return interned_chunks[chunk]
            offset = len(actor_blob)
            interned_chunks[chunk] = offset
            actor_blob.extend(chunk)
            return offset

        entries, worst, max_pair = [], 0, 0
        for index, row in enumerate(frame_rows):
            names = re.findall(r"(\w+)_META\b", row)
            if not names:
                raise ValueError(f"frame {who}[{index}] has no META symbol")
            base = names[0]
            tiles = f"{base}_P2_TILES" if p2 else f"{base}_TILES"
            bank, off, size = (define(text, f"{tiles}_{key}") for key in ("BANK", "OFF", "SIZE"))
            start = (bank - FIRST_BANK) * BANK_BYTES + off
            blob = banks[start:start + size]
            if len(blob) != size:
                raise ValueError(f"source tile blob is truncated: {tiles}")
            meta_offsets, row_offsets = [], []
            for side in ("META", "METAL"):
                name = f"{base}_P2_{side}" if p2 else f"{base}_{side}"
                pruned = prune(arr(text, name), blob)
                worst = max(worst, (len(pruned) - 1) // 3)
                max_pair = max([max_pair] + [tile // 2 for tile in pruned[2:-1:3]])
                wide = widest_row(pruned)
                if wide > 8:
                    stats.setdefault("rows_over_8", []).append((who, index, side, wide))
                meta_offsets.append(append_chunk(bytes(pruned)))
                row_offsets.append(append_chunk(bytes(row_table(pruned))))
            entries.append({"tile_bank": bank, "tile_off": off,
                            "meta_offsets": meta_offsets, "row_offsets": row_offsets})
        actor_blobs[who] = actor_blob
        actor_raw_meta_bytes[who] = raw_meta_bytes
        actor_tables[who] = {"entries": entries, "poses": len(frame_rows),
                             "max_pieces": worst, "max_pair_id": max_pair}

    layout, meta_bank_count = metadata_layout(
        {who: len(blob) for who, blob in actor_blobs.items()}, first_meta_bank
    )
    if first_meta_bank + meta_bank_count - 1 > 255:
        raise ValueError("metadata pages exceed the 8-bit mapper range")
    index_image: bytes | None = None
    index_offsets = {"ken": 0,
                     "ryu": actor_tables["ken"]["poses"] * POSE_INDEX_RECORD_BYTES}
    if index_bank is not None:
        if not 2 <= index_bank <= 255:
            raise ValueError("pose index bank is outside the mapper range")
        index_size = sum(table["poses"] for table in actor_tables.values()) * POSE_INDEX_RECORD_BYTES
        if index_size > BANK_BYTES:
            raise ValueError(f"pose index needs {index_size} B, over one 16 KiB page")
        index = bytearray()
        for who in ("ken", "ryu"):
            actor_bank, actor_offset = layout[who]
            meta_base = actor_offset if actor_bank == layout["ken"][0] else 0
            for entry in actor_tables[who]["entries"]:
                values = [
                    entry["tile_bank"], entry["tile_off"],
                    meta_base + entry["meta_offsets"][0],
                    meta_base + entry["meta_offsets"][1],
                    meta_base + entry["row_offsets"][0],
                    meta_base + entry["row_offsets"][1],
                ]
                if values[1] >= BANK_BYTES or any(value >= BANK_BYTES for value in values[2:]):
                    raise ValueError("pose descriptor offset exceeds its 16 KiB page")
                index += bytes((values[0], values[1] & 0xFF, values[1] >> 8))
                for offset in values[2:]:
                    index += bytes((offset & 0xFF, offset >> 8))
        index_image = bytes(index) + bytes(BANK_BYTES - len(index))
    lines = ["/* gerado por mugen2sms/generators/pose_table.py - nao editar */",
             "#ifndef POSE_TABLE_H", "#define POSE_TABLE_H"]
    if index_bank is None:
        lines += [
            "typedef struct { unsigned char bank; unsigned int off; unsigned char meta_bank;",
            "                 const unsigned char *meta_r, *meta_l;",
            "                 const unsigned char *rows_r, *rows_l; } PoseTiles;",
        ]
    else:
        lines += [
            "typedef struct { unsigned char bank; unsigned int off; unsigned char meta_bank;",
            "                 unsigned int meta_r_off, meta_l_off, rows_r_off, rows_l_off; } PoseTiles;",
            f"#define POSE_INDEX_RECORD_BYTES {POSE_INDEX_RECORD_BYTES}u",
            f"#define POSE_CACHE_RECORD_BYTES {POSE_CACHE_RECORD_BYTES}u",
        ]
    for who in ("ken", "ryu"):
        lines.append(f"#define {who.upper()}_POSE_META_BANK {layout[who][0]}u")
        if index_bank is not None:
            lines.append(f"#define {who.upper()}_POSE_BASE {define(text, f'{who.upper()}_POSE_BASE')}")
    if layout["ken"][0] == layout["ryu"][0]:
        lines.append(f"#define POSE_META_BANK {layout['ken'][0]}u")

    for who in ("ken", "ryu"):
        actor_bank, actor_offset = layout[who]
        table = actor_tables[who]
        stats[who] = {key: table[key] for key in ("poses", "max_pieces", "max_pair_id")}
        lines.append(f"#define {who.upper()}_POSE_MAX_PIECES {table['max_pieces']}u")
        lines.append(f"#define {who.upper()}_POSE_PAIR_IDS {table['max_pair_id'] + 1}u")
        if index_bank is not None:
            lines.append(f"#define {who.upper()}_POSE_COUNT {table['poses']}u")
            lines.append(f"#define {who.upper()}_POSE_INDEX_BANK {index_bank}u")
            lines.append(f"#define {who.upper()}_POSE_INDEX_OFF {index_offsets[who]}u")
        else:
            lines.append(f"static const PoseTiles {who}_pose_tiles[{table['poses']}] = {{")
            for entry in table["entries"]:
                pointers = [
                    f"(const unsigned char *)0x{0x8000 + actor_offset + offset:04X}u"
                    for offset in entry["meta_offsets"] + entry["row_offsets"]
                ]
                lines.append(
                    f"    {{ {entry['tile_bank']}, {entry['tile_off']}, {actor_bank}, "
                    f"{pointers[0]}, {pointers[1]}, {pointers[2]}, {pointers[3]} }},"
                )
            lines.append("};")

    if meta_bank_count == 1:
        combined = actor_blobs["ken"] + actor_blobs["ryu"]
        meta_image = bytes(combined) + bytes(BANK_BYTES - len(combined))
    else:
        meta_image = b"".join(
            bytes(actor_blobs[who]) + bytes(BANK_BYTES - len(actor_blobs[who]))
            for who in ("ken", "ryu")
        )
    lines += ["#endif", ""]
    stats["meta_banks"] = {who: layout[who][0] for who in ("ken", "ryu")}
    stats["meta_bank_count"] = meta_bank_count
    stats["meta_bank_bytes"] = sum(len(blob) for blob in actor_blobs.values())
    stats["meta_uncompressed_bytes"] = sum(actor_raw_meta_bytes.values())
    stats["meta_bytes_saved_by_dedup"] = (
        stats["meta_uncompressed_bytes"] - stats["meta_bank_bytes"]
    )
    if index_bank is not None:
        stats["pose_index_bank"] = index_bank
        stats["pose_index_record_bytes"] = POSE_INDEX_RECORD_BYTES
        stats["pose_index_bytes"] = index_offsets["ryu"] + actor_tables["ryu"]["poses"] * POSE_INDEX_RECORD_BYTES
    return "\n".join(lines), stats, meta_image, index_image


def self_check() -> None:
    blob = bytes(PAIR) + bytes([1]) * PAIR
    alias_text = "#define FRAME_META SHARED_META\nconst unsigned char SHARED_META[4] = {0x00, 0x10, 0x02, 0x80};"
    assert arr(alias_text, "FRAME_META") == [0, 16, 2, END]
    assert prune([0, 0, 0, 8, 16, 2, END], blob) == [8, 16, 2, END]
    assert widest_row([0, 0, 2, 8, 0, 2, 0, 16, 2, END]) == 2
    assert row_table([0, 0, 2, 8, 0, 2, 0, 16, 2, END]) == [2, 0, 2, 16, 1]
    assert resolve_meta_bank(35) == 37
    assert resolve_meta_bank(40) == 42
    try:
        resolve_meta_bank(40, 41)
    except ValueError:
        pass
    else:
        raise AssertionError("metadata bank overlapping the source image was accepted")
    assert metadata_layout({"ken": 5000, "ryu": 6000}, 37) == (
        {"ken": (37, 0), "ryu": (37, 5000)}, 1
    )
    assert metadata_layout({"ken": 15500, "ryu": 15492}, 42) == (
        {"ken": (42, 0), "ryu": (43, 0)}, 2
    )
    for bad in ([0, 8, 2, END], [0, 0, 6, END], [0, 16, 2, 8, 0, 2, END]):
        try:
            prune(bad, blob)
        except ValueError:
            continue
        raise AssertionError(f"{bad} deveria reprovar")
    # Banked index descriptors contain only offsets, not pointers into a
    # mapper window, and are kept in one physical index page.
    index_fixture = """static const Frame ken_frames_all[2] = {
    { 4, 0, A_META, A_META, A_CLSN, A_AXIS, 8, 16, 0, 0 },
    { 4, 0, A_META, A_META, A_CLSN, A_AXIS, 8, 16, 0, 0 },
};
static const Frame ryu_frames_all[2] = {
    { 4, 0, A_META, A_META, A_CLSN, A_AXIS, 8, 16, 0, 0 },
    { 4, 0, A_META, A_META, A_CLSN, A_AXIS, 8, 16, 0, 0 },
};
const unsigned char A_META[4] = {0x00, 0x00, 0x00, 0x80};
const unsigned char A_CLSN[2] = {0x01, 0x80};
const unsigned char A_AXIS[4] = {0x00, 0x00, 0x00, 0x00};
#define A_METAL A_META
#define A_P2_META A_META
#define A_P2_METAL A_METAL
#define KEN_POSE_BASE 0
#define RYU_POSE_BASE 0
#define A_TILES_BANK 2
#define A_TILES_OFF 0
#define A_TILES_SIZE 64
#define A_P2_TILES_BANK 2
#define A_P2_TILES_OFF 64
#define A_P2_TILES_SIZE 64
"""
    # Build metadata with the small frame fixture's legal 64-byte tile pairs.
    _header, _stats, _meta, _index = build(index_fixture, bytes(16384), 3, 4)
    assert _index is not None and len(_index) == BANK_BYTES
    assert _index[0:POSE_INDEX_RECORD_BYTES] == _index[POSE_INDEX_RECORD_BYTES:2 * POSE_INDEX_RECORD_BYTES]
    start = 2 * POSE_INDEX_RECORD_BYTES
    assert _index[start:start + POSE_INDEX_RECORD_BYTES] == _index[start + POSE_INDEX_RECORD_BYTES:start + 2 * POSE_INDEX_RECORD_BYTES]
    assert _stats["meta_bytes_saved_by_dedup"] > 0
    assert "KEN_POSE_INDEX_BANK 4u" in _header
    assert "static const PoseTiles ken_pose_tiles" not in _header
    print("[PASS] pose_table self-check (TALL metadata and banked pose index)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--header", type=Path)
    parser.add_argument("--banks", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--bank-out", type=Path)
    parser.add_argument("--meta-bank", type=int,
                        help="banco físico de metadata; por padrão usa a primeira página após a arte")
    parser.add_argument("--index-bank", type=int,
                        help="emite descritores de pose numa página ROM separada")
    parser.add_argument("--index-out", type=Path,
                        help="página de índice de pose (requer --index-bank)")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        self_check()
        return 0
    required = (args.header, args.banks, args.out, args.bank_out)
    if any(value is None for value in required):
        parser.error("--header, --banks, --out e --bank-out são obrigatórios")
    if bool(args.index_bank is not None) != bool(args.index_out):
        parser.error("--index-bank e --index-out devem ser fornecidos juntos")
    header, stats, blob, index_blob = build(
        args.header.read_text(), args.banks.read_bytes(), args.meta_bank, args.index_bank)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.bank_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(header, encoding="utf-8")
    args.bank_out.write_bytes(blob)
    if args.index_out:
        assert index_blob is not None
        args.index_out.parent.mkdir(parents=True, exist_ok=True)
        args.index_out.write_bytes(index_blob)
    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
