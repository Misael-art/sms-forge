"""Synthetic fixtures for the intake tool. No module content is included."""

import json
import tempfile
import unittest
from pathlib import Path

from openbor2sms.intake import (
    IntakeError,
    deps_record,
    pak_record,
    sources_record,
    tree_hash,
)
from openbor2sms.pak import build_pak32, sha256_file


STAMP = "2026-01-01T00:00:00+00:00"


class PakRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openbor2sms-test-")
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_record_is_deterministic_and_verifies_identity(self):
        blob = build_pak32([("data/a.txt", b"A"), ("data/b.txt", b"B")])
        pak = self.root / "a.pak"
        pak.write_bytes(blob)
        digest = sha256_file(pak)
        first = pak_record(pak, digest, len(blob), STAMP)
        second = pak_record(pak, digest, len(blob), STAMP)
        self.assertEqual(first, second)
        self.assertTrue(first["expected"]["verified"])
        self.assertEqual(first["container"]["file_count"], 2)
        self.assertEqual(first["container"]["index_digest_sha256"], second["container"]["index_digest_sha256"])

    def test_index_digest_changes_with_content_payload_only(self):
        # Same names/offsets but different payload bytes must keep the same index
        # digest (it identifies the index, not the payload).
        one = build_pak32([("data/a.txt", b"A")])
        two = build_pak32([("data/a.txt", b"Z")])
        pak = self.root / "a.pak"
        pak.write_bytes(one)
        first = pak_record(pak, generated_at=STAMP)
        pak.write_bytes(two)
        second = pak_record(pak, generated_at=STAMP)
        self.assertEqual(first["container"]["index_digest_sha256"], second["container"]["index_digest_sha256"])
        self.assertNotEqual(first["source"]["sha256"], second["source"]["sha256"])

    def test_identity_mismatch_fails_closed(self):
        pak = self.root / "a.pak"
        pak.write_bytes(build_pak32([("data/a.txt", b"A")]))
        with self.assertRaises(IntakeError):
            pak_record(pak, "0" * 64)
        with self.assertRaises(IntakeError):
            pak_record(pak, sha256_file(pak), 1)

    def test_unsafe_and_collision_are_counted_not_hidden(self):
        blob = build_pak32([("..\\escape.txt", b"x"), ("data/A.txt", b"A"), ("data/a.txt", b"a")])
        pak = self.root / "a.pak"
        pak.write_bytes(blob)
        record = pak_record(pak, generated_at=STAMP)
        self.assertEqual(record["container"]["unsafe_entry_count"], 1)
        self.assertEqual(record["container"]["case_collision_count"], 1)


class SourcesRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openbor2sms-test-")
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_tree_hash_is_stable_and_tracks_edits(self):
        tree = self.root / "tree"
        (tree / "pkg").mkdir(parents=True)
        (tree / "pkg" / "a.py").write_text("A = 1\n")
        (tree / "pkg" / "b.py").write_text("B = 2\n")
        (tree / "pkg" / "__pycache__").mkdir()
        (tree / "pkg" / "__pycache__" / "stale.py").write_text("never counted\n")
        first = tree_hash(tree)
        self.assertEqual(first["file_count"], 2)
        self.assertEqual(first, tree_hash(tree))
        (tree / "pkg" / "b.py").write_text("B = 3\n")
        self.assertNotEqual(first["value"], tree_hash(tree)["value"])

    def test_manifest_dedupes_and_sorts(self):
        tree = self.root / "tree"
        tree.mkdir()
        (tree / "b.py").write_text("B = 1\n")
        (tree / "a.py").write_text("A = 1\n")
        doc = self.root / "doc.txt"
        doc.write_text("doc\n")
        record = sources_record([doc, doc], [tree], [tree], generated_at=STAMP)
        self.assertEqual(len(record["entries"]), 3)
        paths = [entry["path"] for entry in record["entries"]]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(record["tree_hash"]["file_count"], 2)

    def test_missing_input_fails_closed(self):
        with self.assertRaises(IntakeError):
            sources_record([self.root / "missing.bin"], [], [])


class DepsRecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="openbor2sms-test-")
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, name, payload):
        path = self.root / name
        path.write_text(json.dumps(payload))
        return path

    def _fixtures(self):
        caps = [{"id": "a", "domain": "import", "status": "partial", "fidelity": "partial", "claim_limit": "x"}]
        matrix_caps = caps + [{"id": "module_scoped", "domain": "runtime", "status": "partial",
                               "fidelity": "partial", "claim_limit": "y"}]
        contract = {
            "schema_version": "fixture/0",
            "contract_status": "draft",
            "reference": {"commit": "0" * 40},
            "module_acceptance_rule": "fixture rule",
            "status_vocabulary": ["partial"],
            "capabilities": caps,
        }
        matrix = {
            "importer_and_contract": {
                "declared_profile_ids": ["p1"],
                "capabilities": matrix_caps,
                "file_matrix": [{"path": "x.py", "role": "reader", "status": "supported", "sha256": "1" * 64}],
            },
            "source_file_matrix": [{"member": "M", "status": "adapted"}],
            "source_to_runtime_pipeline": [
                {"stage": "local PAK containers", "evidence": {"p": {"path": "a.pak", "format": "PACK v0 PAK32"}}},
                {"stage": "profile asset/resource conversion",
                 "evidence": {"gal_level_directives": 26,
                              "gal_directive_status_counts": {"adapted": 8, "rejected": 18}}},
            ],
            "unresolved_blockers": [{"id": "b", "status": "unknown", "detail": "d"}],
            "measurements_to_reuse_not_repeat": [{"topic": "t", "result": "r"}],
        }
        manifest = {"archives": [{"module": "m", "role": "pilot", "local_pak": "a.pak",
                                  "local_pak_sha256": "2" * 64, "local_pak_bytes": 10}]}
        return contract, matrix, manifest

    def test_port_is_complete_and_hash_bound(self):
        contract, matrix, manifest = self._fixtures()
        c_file = self._write("c.json", contract)
        m_file = self._write("m.json", matrix)
        s_file = self._write("s.json", manifest)
        record = deps_record(c_file, m_file, s_file, STAMP)
        self.assertEqual(record["origin"]["matrix"]["sha256"], sha256_file(m_file))
        self.assertEqual(record["pilots"][0]["pak_format"], "PACK v0 PAK32")
        self.assertEqual(record["profiles"], ["p1"])
        self.assertEqual(record["capabilities"][0]["id"], "a")
        self.assertEqual(record["matrix_only_capabilities"][0]["id"], "module_scoped")
        self.assertEqual(record["directive_summary"]["status_counts"], {"adapted": 8, "rejected": 18})

    def test_capability_status_disagreement_fails_closed(self):
        contract, matrix, manifest = self._fixtures()
        matrix["importer_and_contract"]["capabilities"] = [dict(contract["capabilities"][0], status="unknown")]
        c_file = self._write("c.json", contract)
        m_file = self._write("m.json", matrix)
        s_file = self._write("s.json", manifest)
        with self.assertRaises(IntakeError):
            deps_record(c_file, m_file, s_file)

    def test_missing_input_fails_closed(self):
        contract, matrix, manifest = self._fixtures()
        c_file = self._write("c.json", contract)
        m_file = self._write("m.json", matrix)
        with self.assertRaises(IntakeError):
            deps_record(c_file, m_file, self.root / "missing.json")


if __name__ == "__main__":
    unittest.main()
