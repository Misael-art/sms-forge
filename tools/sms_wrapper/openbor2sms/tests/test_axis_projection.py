"""Projection contract using the calibrated bundle fixture; no runtime approval."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from openbor2sms import axis_projection as projection
from openbor2sms import evidence_consumer
import test_evidence_consumer as fixtures


class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.EvidenceConsumerTests.setUpClass.__func__(cls)

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.f = fixtures.BundleFixture(self.root, self.video_bytes, self.frame_hashes)
        (self.root / "out/rom").mkdir(parents=True)
        current = self.root / "out/rom/game.sms"
        current.write_bytes(self.f.current.read_bytes())
        self.f.current = current
        (self.root / ".mddev").mkdir()
        (self.root / ".mddev/project.json").write_text(json.dumps({"name": "game"}))
        (self.root / "out/build_record.json").write_text(json.dumps({"rom_sha256": self.f.sha}))
        names = {"boot": "boot_emulador", "attack": "gameplay", "ntsc": "fps_constante", "sfx": "audio"}
        for case in self.f.contract["required_cases"]:
            case["id"] = names[case["id"]]
        for item in self.f.data["coverage"]:
            item["case_id"] = names[item["case_id"]]
        self.f.data["contract"] = self.f.obj("contract.json", self.f.contract, True)
        self.f.save()
        self.cons = evidence_consumer.consume(self.f.bundle, self.f.current)
        self.assertTrue(self.cons["eligible"], self.cons)
        self.paths = {"bundle": str(self.f.bundle), "wav": str(self.root / "signal.wav")}
        for name, data in (("consumption", self.cons), ("runtime_metrics", {
                **self.f.metrics, "fps_constante": True, "frame_advance_proved": True})):
            path = self.root / (name + ".json")
            path.write_text(json.dumps(data))
            self.paths[name] = str(path)
        request = self.root / "qa-request.json"
        request.write_text(json.dumps({"rom": {"sha256": self.f.sha}}))
        report = {"request": {"path": str(request), "sha256": projection.sha256_file(request)}}
        qa = self.root / "qa.json"
        qa.write_text(json.dumps(report))
        self.paths.update(qa_runtime=str(qa), qa_visual=str(qa))
        # Isolate projection logic; the real QA validator has its own self-check.
        validator = patch("audit_subagent_session.validate_report", return_value={"tests_passed": True, "problems": []})
        self.validate = validator.start()
        self.addCleanup(validator.stop)

    def project(self):
        return projection.project(self.root, current_rom=str(self.f.current), **self.paths)

    def refused(self):
        with self.assertRaises(projection.ProjectionError):
            self.project()
        self.assertFalse((self.root / "out/evidence/evidence.json").exists())
        self.assertFalse((self.root / "out/evidence/fps.json").exists())

    def test_positive_reconsumes_bundle_before_projecting_scoped_axes(self):
        result = self.project()
        ev = json.loads(Path(result["evidence"]).read_text())
        self.assertEqual(ev["rom_sha256"], self.f.sha)
        self.assertEqual(ev["claim_ceiling"], "assigned_checks_only")
        self.assertEqual(self.validate.call_count, 2)

    def test_reconciliation_revalidates_projection_sha_and_fps_source(self):
        import reconcile_claims
        result = self.project()
        support = reconcile_claims.axis_support(self.root)
        self.assertTrue(support["gameplay"][0])
        self.assertTrue(support["audio"][0])
        self.assertTrue(support["fps_constante"][0])
        ev_path = Path(result["evidence"])
        ev = json.loads(ev_path.read_text())
        ev_path.write_text(json.dumps({**ev, "rom_sha256": "another-ROM"}))
        support = reconcile_claims.axis_support(self.root)
        self.assertFalse(support["gameplay"][0])
        self.assertFalse(support["audio"][0])
        ev_path.write_text(json.dumps(ev))
        fps_path = Path(result["fps"])
        fps = json.loads(fps_path.read_text())
        fps["fps_janelas"] = [59.9, 59.9, 59.9]
        fps_path.write_text(json.dumps(fps))
        self.assertFalse(reconcile_claims.axis_support(self.root)["fps_constante"][0])

    def test_latest_auxiliary_never_selects_rom(self):
        (self.root / ".mddev").mkdir(exist_ok=True)
        (self.root / ".mddev/project.json").write_text(json.dumps({"name": "game"}))
        roms = self.root / "out/rom"
        roms.mkdir(parents=True, exist_ok=True)
        nominal = roms / "game.sms"
        nominal.write_bytes(self.f.current.read_bytes())
        (roms / "auxiliary.sms").write_bytes(b"auxiliary")
        (self.root / "out/build_record.json").write_text(json.dumps({"rom_sha256": self.f.sha}))
        self.assertEqual(projection._current_rom(self.root, None), nominal)
        nominal.write_bytes(b"wrong nominal")
        with self.assertRaises(projection.ProjectionError):
            projection._current_rom(self.root, None)

    def test_cached_pass_cannot_hide_other_session_or_stale_artifact(self):
        for bad in ("session", "stale"):
            saved = copy.deepcopy(self.f.data)
            if bad == "session":
                self.f.audio_meta["session_id"] = "another-session"
                self.f.update_artifact("audio", meta=self.f.audio_meta)
            else:
                self.f.item("boot")["captured_at"] = self.f.frozen - 1
            self.f.save()
            self.refused()
            self.f.data = saved

    def test_wrong_qa_rom_failed_qa_and_mrp_floor_refuse_without_writes(self):
        self.validate.return_value = {"tests_passed": False, "problems": ["synthetic failure"]}
        self.refused()
        self.validate.return_value = {"tests_passed": True, "problems": []}
        metrics = json.loads(Path(self.paths["runtime_metrics"]).read_text())
        metrics["fps_janelas"] = [57.999999, 60, 60]
        Path(self.paths["runtime_metrics"]).write_text(json.dumps(metrics))
        self.refused()

    def test_rom_or_source_changed_during_preparation_refuses(self):
        real = evidence_consumer.consume

        def changing(*args, **kwargs):
            result = real(*args, **kwargs)
            self.f.current.write_bytes(b"changed while consuming")
            return result

        with patch.object(evidence_consumer, "consume", side_effect=changing):
            self.refused()


if __name__ == "__main__":
    unittest.main()
