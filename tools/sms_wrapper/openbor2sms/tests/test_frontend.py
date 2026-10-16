"""Front-end tests: extraction identity, IR origin byte spans, determinism, fail-closed.

Fixtures are synthetic and built in temporary directories; no module content
from the ARCHIVE is used.
"""

import json
import tempfile
import unittest
from pathlib import Path

from openbor2sms.frontend import (
    FrontendError,
    extract_pak_members,
    level_ir,
    line_spans,
    models_ir,
)
from openbor2sms.pak import PakError, build_pak32, sha256_file

LEVEL_TEXT = (
    "music data/music/STAGE1.BOR\r\n"
    "# caf\xe9 comment\r\n"
    "panel data/bgs/panel.gif\n"
    "spawn long\n"
    "coords 10 180\n"
    "at 0\n"
    "spawn second\n"
    "spawn1 50 20 200\n"
)
MODELS_TEXT = (
    "load Long data/chars/long/long.txt\n"
    "load long data/chars/alt/long_alt.txt\n"
    "know Item data/items/item.txt\n"
)


class FrontendTests(unittest.TestCase):
    def _fixture(self, tmp: Path):
        blob = build_pak32(
            [
                ("DATA/Levels/LV1.TXT", LEVEL_TEXT.encode("utf-8")),
                ("data/models.txt", MODELS_TEXT.encode("utf-8")),
            ]
        )
        pak = tmp / "fixture.pak"
        pak.write_bytes(blob)
        return pak, blob

    def test_extract_records_identity_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pak, blob = self._fixture(tmp)
            digest = sha256_file(pak)
            dest = tmp / "extracted"
            record = extract_pak_members(
                pak, digest, len(blob), ["data/levels/lv1.txt", "data/models.txt"], dest
            )
            self.assertEqual(record["schema"], "openbor_sms_extraction_record_v1")
            self.assertTrue(record["expected"]["verified"])
            self.assertEqual([row["member"] for row in record["members"]], ["data/levels/lv1.txt", "data/models.txt"])
            self.assertEqual((dest / "data/levels/lv1.txt").read_bytes(), LEVEL_TEXT.encode("utf-8"))
            self.assertEqual(record["members"][0]["sha256"], sha256_file(dest / "data/levels/lv1.txt"))
            self.assertFalse(record["members"][0]["reused_existing"])
            again = extract_pak_members(pak, digest, len(blob), ["data/levels/lv1.txt"], dest)
            self.assertTrue(again["members"][0]["reused_existing"])

    def test_extract_fails_closed_on_identity_and_missing_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pak, blob = self._fixture(tmp)
            digest = sha256_file(pak)
            cases = [
                lambda: extract_pak_members(pak, "0" * 64, len(blob), ["data/models.txt"], tmp / "a"),
                lambda: extract_pak_members(pak, digest, len(blob) + 1, ["data/models.txt"], tmp / "b"),
                lambda: extract_pak_members(pak, digest, len(blob), ["data/missing.txt"], tmp / "c"),
            ]
            for case in cases:
                with self.assertRaises((FrontendError, PakError)):
                    case()

    def test_extract_refuses_to_overwrite_different_bytes_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pak, blob = self._fixture(tmp)
            digest = sha256_file(pak)
            dest = tmp / "extracted"
            extract_pak_members(pak, digest, len(blob), ["data/models.txt"], dest)
            target = dest / "data/models.txt"
            target.write_bytes(b"tampered\n")
            with self.assertRaises(FrontendError):
                extract_pak_members(pak, digest, len(blob), ["data/models.txt"], dest)
            record = extract_pak_members(pak, digest, len(blob), ["data/models.txt"], dest, force=True)
            self.assertFalse(record["members"][0]["reused_existing"])
            self.assertEqual(target.read_bytes(), MODELS_TEXT.encode("utf-8"))

    def test_level_ir_origin_spans_reconstruct_source_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pak, blob = self._fixture(tmp)
            digest = sha256_file(pak)
            dest = tmp / "extracted"
            extract_pak_members(pak, digest, len(blob), ["data/levels/lv1.txt", "data/models.txt"], dest)
            source = dest / "data/levels/lv1.txt"
            ir = level_ir(
                source,
                "data/levels/lv1.txt",
                sha256_file(source),
                pak_sha256=digest,
                models_index_path=dest / "data/models.txt",
                models_index_member="data/models.txt",
                generated_at="2026-01-01T00:00:00+00:00",
            )
            raw = source.read_bytes()
            self.assertTrue(ir["directives"])
            for row in ir["directives"]:
                span = raw[row["byte_offset"] : row["byte_offset"] + row["byte_length"]]
                self.assertEqual(span.decode("utf-8"), row["raw"])
            for row in ir["spawns"] + ir["player_starts"]:
                span = raw[row["byte_offset"] : row["byte_offset"] + row["byte_length"]]
                self.assertTrue(span.decode("utf-8").startswith("spawn"))
            self.assertEqual([row["line"] for row in ir["directives"]], [1, 3, 4, 5, 6, 7, 8])
            self.assertTrue(any("spawn second is not followed" in issue for issue in ir["issues"]))

    def test_level_ir_is_deterministic_and_keeps_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pak, blob = self._fixture(tmp)
            digest = sha256_file(pak)
            dest = tmp / "extracted"
            extract_pak_members(pak, digest, len(blob), ["data/levels/lv1.txt", "data/models.txt"], dest)
            source = dest / "data/levels/lv1.txt"
            kwargs = dict(
                member="data/levels/lv1.txt",
                expect_sha256=sha256_file(source),
                pak_sha256=digest,
                models_index_path=dest / "data/models.txt",
                models_index_member="data/models.txt",
                generated_at="2026-01-01T00:00:00+00:00",
            )
            first = level_ir(source, **kwargs)
            second = level_ir(source, **kwargs)
            self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
            self.assertTrue(any("spawn second" in issue for issue in first["issues"]))
            self.assertTrue(first["event_ir"]["events"])
            self.assertEqual(
                [row["command"] for row in first["directive_matrix"]],
                sorted(row["command"] for row in first["directive_matrix"]),
            )

    def test_level_ir_marks_units_only_where_pinned(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "unit_level.txt"
            source.write_text("spawn long\ndelay 12\nat 0\n", encoding="utf-8")
            ir = level_ir(source, "data/levels/unit.txt", sha256_file(source), generated_at="t")
            declared = ir["units"]["declared"]
            self.assertEqual([row["command"] for row in declared], ["delay"])
            self.assertEqual(declared[0]["status"], "hypothesis")
            self.assertIn("spawn", ir["units"]["undeclared_commands"])

    def test_models_ir_flags_case_insensitive_duplicates_with_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            pak, blob = self._fixture(tmp)
            digest = sha256_file(pak)
            dest = tmp / "extracted"
            extract_pak_members(pak, digest, len(blob), ["data/models.txt"], dest)
            source = dest / "data/models.txt"
            ir = models_ir(source, "data/models.txt", sha256_file(source), pak_sha256=digest, generated_at="t")
            self.assertEqual(ir["schema"], "openbor_sms_frontend_models_ir_v1")
            duplicates = ir["duplicate_aliases"]
            self.assertEqual(len(duplicates), 1)
            self.assertEqual(duplicates[0]["alias_key"], "long")
            self.assertEqual(duplicates[0]["occurrences"], 2)
            first = ir["entries"][0]
            raw = source.read_bytes()
            span = raw[first["byte_offset"] : first["byte_offset"] + first["byte_length"]]
            self.assertEqual(span.decode("utf-8"), "load Long data/chars/long/long.txt")
            self.assertEqual(first["line"], 1)
            self.assertEqual(first["byte_offset"], 0)

    def test_ir_fails_closed_on_mismatch_non_utf8_and_odd_line_breaks(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            good = tmp / "good.txt"
            good.write_text("spawn long\nat 0\n", encoding="utf-8")
            with self.assertRaises(FrontendError):
                level_ir(good, "data/levels/good.txt", "0" * 64, generated_at="t")
            bad = tmp / "bad.txt"
            bad.write_bytes(b"spawn a\xff\n")
            with self.assertRaises(FrontendError):
                level_ir(bad, "data/levels/bad.txt", sha256_file(bad), generated_at="t")
            odd = tmp / "odd.txt"
            odd.write_text("spawn a\x0bat 0\n", encoding="utf-8")
            with self.assertRaises(FrontendError):
                level_ir(odd, "data/levels/odd.txt", sha256_file(odd), generated_at="t")

    def test_line_spans_cover_crlf_lf_cr_and_trailing_terminator(self):
        text = "a\r\nb\nc\rd"
        spans = line_spans(text)
        data = text.encode("utf-8")
        self.assertEqual(
            [data[off : off + length].decode("utf-8") for off, length in spans],
            ["a", "b", "c", "d"],
        )
        self.assertEqual(line_spans(""), [])


if __name__ == "__main__":
    unittest.main()
