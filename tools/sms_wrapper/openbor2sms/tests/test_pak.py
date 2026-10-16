# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/tests/test_pak.py
#   donor sha256: dc576744fefeb659be4b84ba9735c8aeae07882827bf2542d990f0fff63c3819
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms intake O0)
# Adaptation: only the import path changed from openbor2sgdk_forge.pak to
# openbor2sms.pak; assertions are unchanged from the donor test.
"""Fixtures are synthetic. They do not contain module content."""

import struct
import unittest
from pathlib import Path
import tempfile

from openbor2sms.pak import (
    PakError,
    build_pak32,
    build_pak64,
    extract_members,
    is_unsafe_path,
    read_entry,
    read_index,
)


class PakLayoutTests(unittest.TestCase):
    def test_pak32_roundtrip_preserves_bytes_and_backslash_name(self) -> None:
        blob = build_pak32([("data/chars/Hero/idle.txt", b"name Hero\n")])
        self.assertEqual(blob[:4], b"PACK")
        self.assertEqual(struct.unpack_from("<I", blob, 4)[0], 0)
        index = read_index(blob)
        self.assertEqual(index.format_id, 0)
        self.assertEqual(index.file_count, 1)
        entry = index.entries[0]
        self.assertEqual(entry.original_name, "data\\chars\\Hero\\idle.txt")
        self.assertEqual(entry.normalized_name, "data/chars/hero/idle.txt")
        self.assertEqual(read_entry(blob, entry), b"name Hero\n")

    def test_pak64_roundtrip(self) -> None:
        blob = build_pak64([("data/models.txt", b"know\n")])
        index = read_index(blob)
        self.assertEqual(index.format_id, 1)
        self.assertEqual(read_entry(blob, index.entries[0]), b"know\n")

    def test_truncated_and_bad_magic(self) -> None:
        with self.assertRaises(PakError):
            read_index(b"PACK")
        with self.assertRaises(PakError):
            read_index(b"PAKZ" + b"\x00" * 12)

    def test_unknown_format_id_is_not_treated_as_empty(self) -> None:
        blob = b"PACK" + struct.pack("<I", 7) + struct.pack("<I", 8)
        with self.assertRaises(PakError):
            read_index(blob)

    def test_path_traversal_and_absolute_are_unsafe(self) -> None:
        self.assertTrue(is_unsafe_path("..\\secret.txt"))
        self.assertTrue(is_unsafe_path("data/../../etc/passwd"))
        self.assertTrue(is_unsafe_path("/etc/passwd"))
        self.assertTrue(is_unsafe_path("C:\\windows\\note.txt"))
        self.assertFalse(is_unsafe_path("data\\chars\\hero.txt"))
        blob = build_pak32([("../escape.txt", b"nope"), ("data/ok.txt", b"yes")])
        index = read_index(blob)
        unsafe = [entry for entry in index.entries if entry.unsafe]
        self.assertEqual(len(unsafe), 1)
        with self.assertRaises(PakError):
            read_entry(blob, unsafe[0])

    def test_data_range_past_table_is_rejected(self) -> None:
        name = b"data\\bad.txt\x00"
        record = struct.pack("<III", 12 + len(name), 1000, 10) + name
        table_offset = 8
        blob = b"PACK" + struct.pack("<I", 0) + record + struct.pack("<I", table_offset)
        with self.assertRaises(PakError):
            read_index(blob)

    def test_case_collision_blocks_extract(self) -> None:
        blob = build_pak32([("data/A.txt", b"A"), ("data/a.txt", b"a")])
        index = read_index(blob)
        self.assertEqual(len(index.case_collisions), 1)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PakError):
                extract_members(blob, index, Path(tmp))

    def test_extract_lowercases_and_stays_inside_destination(self) -> None:
        blob = build_pak32([("data/Chars/Hero.TXT", b"health 10\n")])
        index = read_index(blob)
        with tempfile.TemporaryDirectory() as tmp:
            written = extract_members(blob, index, Path(tmp), suffixes=(".txt",))
            self.assertEqual(written, ["data/chars/hero.txt"])
            self.assertEqual((Path(tmp) / written[0]).read_bytes(), b"health 10\n")

    def test_unknown_suffix_is_not_silently_extracted(self) -> None:
        blob = build_pak32([("data/pic.gif", b"GIF")])
        index = read_index(blob)
        with tempfile.TemporaryDirectory() as tmp:
            written = extract_members(blob, index, Path(tmp), suffixes=(".txt",))
            self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
