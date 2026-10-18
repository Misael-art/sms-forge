# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/openbor2sgdk_forge/pak.py
#   donor sha256: 13de21eecbf8321434827bdc465bb7dee11dcb35b6631a9d3dd7ed5fca54cfcc
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms intake O0)
# Body below is byte-identical to the donor file (verified by cmp at port time);
# no behavioral change. The pinned upstream reference (borpak at commit
# 787b6770409935137579715febf80cf7a529b748) stays as documented in the module docstring.
"""OpenBOR PAK reader.

Layout transcribed from the official borpak at
DCurrent/openbor commit 787b6770409935137579715febf80cf7a529b748
(tools/borpak/source/borpak.c and borpak.h, 2026-09-22).

PAK32 (format id 0) is the legacy layout: 8-byte header, file bytes,
then records of u32 record_size, u32 offset, u32 size, name bytes
(including the C NUL), and a final u32 table offset.
PAK64 (format id 1) uses u64 offset and size and an 8-byte footer.
"""

from __future__ import annotations

import hashlib
import io
import struct
from dataclasses import dataclass, field
from pathlib import Path

SPEC_COMMIT = "787b6770409935137579715febf80cf7a529b748"
SPEC_SOURCE = "DCurrent/openbor tools/borpak/source/borpak.c"

PACK_MAGIC = b"PACK"
HEADER_SIZE = 8
PAK32_ENTRY_BASE = 12
PAK64_ENTRY_BASE = 20
PAK32_FOOTER = 4
PAK64_FOOTER = 8
FORMAT_PAK32 = 0
FORMAT_PAK64 = 1


class PakError(ValueError):
    """A PAK failed a check defined by the pinned borpak reader."""


@dataclass(frozen=True)
class PakEntry:
    original_name: str
    normalized_name: str
    data_offset: int
    data_size: int
    record_size: int
    unsafe: bool
    name_sha256: str


@dataclass
class PakIndex:
    format_id: int
    format_name: str
    table_offset: int
    archive_size: int
    entries: list[PakEntry] = field(default_factory=list)
    case_collisions: list[list[str]] = field(default_factory=list)
    spec_commit: str = SPEC_COMMIT

    @property
    def file_count(self) -> int:
        return len(self.entries)


def _u32(buf: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(buf):
        raise PakError(f"truncated u32 at {offset}")
    return struct.unpack_from("<I", buf, offset)[0]


def _u64(buf: bytes, offset: int) -> int:
    if offset < 0 or offset + 8 > len(buf):
        raise PakError(f"truncated u64 at {offset}")
    return struct.unpack_from("<Q", buf, offset)[0]


def is_unsafe_path(name: str) -> bool:
    """Match borpak is_unsafe_path, including Windows drive letters."""
    if not name:
        return True
    if name[0] in "/\\":
        return True
    if ":" in name:
        return True
    cursor = name
    while cursor:
        split_at = len(cursor)
        for sep in "/\\":
            found = cursor.find(sep)
            if found != -1 and found < split_at:
                split_at = found
        component = cursor[:split_at]
        if component == "..":
            return True
        if split_at >= len(cursor):
            break
        cursor = cursor[split_at + 1 :]
    return False


def normalize_archive_name(name: str) -> str:
    """borpak extraction lowercases and writes the host slash.

    The index keeps a portable forward-slash form so case collisions are
    visible on Linux, where the official tool would also lowercase.
    """
    lowered = name.lower().replace("\\", "/")
    while lowered.startswith("./"):
        lowered = lowered[2:]
    parts = [part for part in lowered.split("/") if part not in ("", ".")]
    return "/".join(parts)


def c_string(name_bytes: bytes) -> str:
    nul = name_bytes.find(b"\x00")
    raw = name_bytes if nul < 0 else name_bytes[:nul]
    return raw.decode("latin-1")


def read_index(data: bytes) -> PakIndex:
    if len(data) < HEADER_SIZE + PAK32_FOOTER:
        raise PakError("archive is shorter than a PAK32 header and footer")
    if data[:4] != PACK_MAGIC:
        raise PakError("missing PACK magic")
    format_id = _u32(data, 4)
    if format_id == FORMAT_PAK32:
        entry_base = PAK32_ENTRY_BASE
        footer = PAK32_FOOTER
        format_name = "PACK v0 PAK32 (32-bit)"
        table_end = len(data) - footer
        table_offset = _u32(data, table_end)
    elif format_id == FORMAT_PAK64:
        entry_base = PAK64_ENTRY_BASE
        footer = PAK64_FOOTER
        format_name = "PACK v1 PAK64 (64-bit)"
        if len(data) < HEADER_SIZE + footer:
            raise PakError("archive is shorter than a PAK64 footer")
        table_end = len(data) - footer
        table_offset = _u64(data, table_end)
    else:
        raise PakError(f"unsupported PACK format id {format_id}")
    if table_offset < HEADER_SIZE or table_offset > table_end:
        raise PakError(f"malformed table offset {table_offset}")

    entries: list[PakEntry] = []
    pos = table_offset
    while pos < table_end:
        remaining = table_end - pos
        if remaining < entry_base:
            raise PakError(f"truncated table record at {pos}")
        record_size = _u32(data, pos)
        if record_size <= entry_base or record_size > remaining:
            raise PakError(f"malformed record size {record_size} at {pos}")
        if format_id == FORMAT_PAK32:
            data_offset = _u32(data, pos + 4)
            data_size = _u32(data, pos + 8)
            name_at = pos + PAK32_ENTRY_BASE
        else:
            data_offset = _u64(data, pos + 4)
            data_size = _u64(data, pos + 12)
            name_at = pos + PAK64_ENTRY_BASE
        name_bytes = data[name_at : pos + record_size]
        original = c_string(name_bytes)
        if data_offset > table_offset or data_size > table_offset - data_offset:
            raise PakError(f"data range escapes the file table: {original}")
        if data_offset < HEADER_SIZE and data_size:
            raise PakError(f"data overlaps the header: {original}")
        normalized = normalize_archive_name(original)
        entries.append(
            PakEntry(
                original_name=original,
                normalized_name=normalized,
                data_offset=data_offset,
                data_size=data_size,
                record_size=record_size,
                unsafe=is_unsafe_path(original),
                name_sha256=hashlib.sha256(original.encode("latin-1")).hexdigest(),
            )
        )
        pos += record_size
    if pos != table_end:
        raise PakError("file table did not end on the footer")

    groups: dict[str, list[str]] = {}
    for entry in entries:
        if entry.unsafe or not entry.normalized_name:
            continue
        groups.setdefault(entry.normalized_name, []).append(entry.original_name)
    collisions = [names for names in groups.values() if len(names) > 1]
    return PakIndex(
        format_id=format_id,
        format_name=format_name,
        table_offset=table_offset,
        archive_size=len(data),
        entries=entries,
        case_collisions=collisions,
    )


def read_entry(data: bytes, entry: PakEntry) -> bytes:
    if entry.unsafe:
        raise PakError(f"refusing unsafe path {entry.original_name}")
    end = entry.data_offset + entry.data_size
    if end > len(data):
        raise PakError(f"entry exceeds archive: {entry.original_name}")
    return data[entry.data_offset:end]


def find_entry(index: PakIndex, normalized_name: str) -> PakEntry:
    """Return the safe entry whose normalized name matches, or raise PakError."""
    key = normalize_archive_name(normalized_name)
    matches = [entry for entry in index.entries if entry.normalized_name == key]
    if not matches:
        raise PakError(f"missing archive member {key}")
    if len(matches) > 1 or matches[0].unsafe:
        raise PakError(f"refusing ambiguous or unsafe member {key}")
    return matches[0]


def build_pak32(files: list[tuple[str, bytes]]) -> bytes:
    """Write a PAK32 the way borpak writes one file at a time.

    Names are stored with backslashes and a trailing NUL, matching
    copy_archive_path plus strlen+1.
    """
    payload = bytearray()
    records = bytearray()
    for name, blob in files:
        archive_name = name.replace("/", "\\")
        name_bytes = archive_name.encode("latin-1") + b"\x00"
        offset = HEADER_SIZE + len(payload)
        payload.extend(blob)
        record_size = PAK32_ENTRY_BASE + len(name_bytes)
        records += struct.pack("<III", record_size, offset, len(blob))
        records += name_bytes
    table_offset = HEADER_SIZE + len(payload)
    return b"PACK" + struct.pack("<I", FORMAT_PAK32) + payload + records + struct.pack("<I", table_offset)


def build_pak64(files: list[tuple[str, bytes]]) -> bytes:
    payload = bytearray()
    records = bytearray()
    for name, blob in files:
        archive_name = name.replace("/", "\\")
        name_bytes = archive_name.encode("latin-1") + b"\x00"
        offset = HEADER_SIZE + len(payload)
        payload.extend(blob)
        record_size = PAK64_ENTRY_BASE + len(name_bytes)
        records += struct.pack("<IQQ", record_size, offset, len(blob))
        records += name_bytes
    table_offset = HEADER_SIZE + len(payload)
    return b"PACK" + struct.pack("<I", FORMAT_PAK64) + payload + records + struct.pack("<Q", table_offset)


def iter_safe_entries(index: PakIndex):
    for entry in index.entries:
        if entry.unsafe:
            continue
        if not entry.normalized_name:
            continue
        yield entry


def extract_members(
    data: bytes,
    index: PakIndex,
    destination: Path,
    *,
    suffixes: tuple[str, ...] | None = None,
    name_contains: tuple[str, ...] | None = None,
    max_bytes: int = 64 * 1024 * 1024,
) -> list[str]:
    """Extract safe members. Returns normalized relative paths written."""
    written: list[str] = []
    used = 0
    seen: set[str] = set()
    destination = destination.resolve()
    for entry in iter_safe_entries(index):
        rel = entry.normalized_name
        if rel in seen:
            raise PakError(f"case collision would overwrite {rel}")
        if suffixes and not rel.endswith(suffixes):
            continue
        if name_contains and not any(token in rel for token in name_contains):
            continue
        if entry.data_size > max_bytes or used + entry.data_size > max_bytes:
            raise PakError(f"expansion limit exceeded at {rel}")
        target = (destination / rel).resolve()
        if destination != target and destination not in target.parents:
            raise PakError(f"normalized path escapes destination: {rel}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(read_entry(data, entry))
        used += entry.data_size
        seen.add(rel)
        written.append(rel)
    return written


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def read_stream(handle: io.BufferedIOBase) -> bytes:
    return handle.read()
