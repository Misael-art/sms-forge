"""Offline contract calibration. These fixtures never qualify a ROM or gameplay."""
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reconcile_claims as gate
import build_inner
from session_bridge import isolated


class BuildIdentityTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for folder in (".mddev", "src", "doc", "out/rom", "out/evidence"):
            (self.root / folder).mkdir(parents=True)
        self.rom = self.root / "out/rom/game.sms"
        self.rom.write_bytes(b"synthetic offline ROM")
        self.sha = gate._sha256(self.rom)
        self.write(".mddev/project.json", {"name": "game"})
        (self.root / "src/main.c").write_text("/* synthetic source */")
        self.record = {"rom_sha256": self.sha, "steps": {"pre_gates": "pass"},
                       "axes": {"build": True, "validation_report": True},
                       "input_sha256": {name: gate._sha256(self.root / name)
                                        for name in (".mddev/project.json", "src/main.c")}}
        self.record["pre_gate_input_sha256"] = build_inner.pre_gate_inputs(self.root)
        self.write("out/build_record.json", self.record)
        self.sid = "a" * 32
        self.sessions = self.root / "sessions"
        self.session = self.sessions / self.sid
        (self.session / "emulator").mkdir(parents=True)
        (self.session / "emulator/rom.sms").write_bytes(self.rom.read_bytes())
        self.meta = {"session_id": self.sid, "root": str(self.session), "state": "closed",
                     "created_at": 1000, "closed_at": 3000, "rom_sha256": self.sha,
                     "emulator_process": {"pid": 123, "start_ticks": "456"}, "audio_sink": "fixture"}
        self.write(f"sessions/{self.sid}/session.json", self.meta)
        patcher = patch.object(isolated, "DEFAULT_ROOT", self.sessions)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write(self, name, obj):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj))
        return path

    def test_nominal_ignores_newer_auxiliary_and_rejects_wrong_receipt(self):
        extra = self.root / "out/rom/auxiliary.sms"
        extra.write_bytes(b"auxiliary proof")
        os.utime(extra, (4000, 4000))
        self.assertEqual(gate.select_rom(self.root)[0], self.rom)
        self.assertFalse(gate.reconcile(self.root)[0])
        self.record["rom_sha256"] = gate._sha256(extra)
        self.record["axes"] = {}
        self.write("out/build_record.json", self.record)
        self.assertIn("SHA", " ".join(gate.reconcile(self.root)[0]))

    def test_candidate_is_explicit_and_never_changes_nominal(self):
        target = self.root / "out/candidates/example/rom/game.sms"
        target.parent.mkdir(parents=True)
        target.write_bytes(b"candidate")
        rec = {**self.record, "rom_path": str(target.relative_to(self.root)),
               "rom_sha256": gate._sha256(target)}
        receipt = self.write("out/candidates/example/build_record.json", rec)
        nominal = (self.rom.read_bytes(), (self.root / "out/build_record.json").read_bytes())
        problems, report = gate.reconcile(self.root, build_record=receipt, current_rom=target)
        self.assertEqual(problems, [])
        self.assertFalse(report["delivery_approved"])
        self.assertTrue(gate.reconcile(self.root, build_record=receipt, current_rom=self.rom)[0])
        self.assertEqual(nominal, (self.rom.read_bytes(), (self.root / "out/build_record.json").read_bytes()))
        # Existing v1 candidate receipts retain their exact steps.rom path.
        rec.pop("rom_path")
        rec.update(schema="smsforge.candidate_build/v1", steps={"rom": f"{target} (9 bytes)"})
        self.assertEqual(gate.select_rom(self.root, rec)[0], target)

    def test_pre_gates_and_memory_are_scoped_and_current(self):
        self.assertTrue(gate.axis_support(self.root)["validation_report"][0])
        (self.root / "src/main.c").write_text("changed")
        self.assertFalse(gate.axis_support(self.root)["validation_report"][0])
        memory = self.root / "doc/10-memory-bank.md"
        memory.write_text("Historical boolean true")
        self.assertFalse(gate.axis_support(self.root)["memory_bank_atualizado"][0])

        memory.write_text("Observed candidate SHA: " + self.sha)
        self.assertTrue(gate.axis_support(self.root)["memory_bank_atualizado"][0])
        memory.write_bytes(b"\xff")
        self.assertFalse(gate.axis_support(self.root)["memory_bank_atualizado"][0])
        memory.unlink()
        self.assertFalse(gate.axis_support(self.root)["memory_bank_atualizado"][0])

    def test_added_resource_invalidates_current_pre_gates(self):
        self.assertTrue(gate.axis_support(self.root)["validation_report"][0])
        (self.root / "res").mkdir()
        (self.root / "res/added.png").write_bytes(b"synthetic invalid resource")
        self.assertFalse(gate.axis_support(self.root)["validation_report"][0])

    def test_new_source_and_changed_provenance_invalidate_pre_gates(self):
        source = self.root / "src/extra.c"
        source.write_text("/* new source */")
        self.assertFalse(gate.axis_support(self.root)["validation_report"][0])
        source.unlink()
        self.assertTrue(gate.axis_support(self.root)["validation_report"][0])
        self.write("doc/asset_provenance_manifest.json", {"assets": []})
        self.assertFalse(gate.axis_support(self.root)["validation_report"][0])

    def test_resource_symlink_alias_remains_a_distinct_gate_input(self):
        (self.root / "res").mkdir()
        (self.root / "res/a.png").write_bytes(b"fixture")
        before = build_inner.pre_gate_inputs(self.root)
        (self.root / "res/b.png").symlink_to("a.png")
        after = build_inner.pre_gate_inputs(self.root)
        self.assertNotEqual(before, after)
        self.assertEqual(after["res/a.png"], after["res/b.png"])

    def test_capture_from_outside_session_lifetime_is_rejected(self):
        artifact = self.root / "frame.png"
        artifact.write_bytes(b"offline bytes, not framebuffer evidence")
        os.utime(artifact, (2000, 2000))
        doc = {"session_id": self.sid, "rom_sha256": self.sha, "captured_at": 2000}
        self.assertTrue(gate._session_bound(doc, artifact, self.sha))
        self.assertFalse(gate._session_bound({**doc, "captured_at": 3001}, artifact, self.sha))

    def test_unreadable_memory_fails_closed(self):
        original = Path.read_text

        def unreadable(path, *args, **kwargs):
            if path.name == "10-memory-bank.md":
                raise PermissionError("synthetic unreadable context")
            return original(path, *args, **kwargs)

        with patch.object(Path, "read_text", unreadable):
            self.assertFalse(gate.axis_support(self.root)["memory_bank_atualizado"][0])

    def audio(self):
        wav = self.root / "out/evidence/signal.wav"
        with wave.open(str(wav), "wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(44100)
            stream.writeframes(struct.pack("<h", 1000) * 44100)
        os.utime(wav, (2000, 2000))
        meta = {"session_id": self.sid, "rom_sha256": self.sha,
                "wav_sha256": gate._sha256(wav), "pid": 123, "sink": "fixture",
                "moved_sink_inputs": ["42"], "samples": 44100, "peak": 1000,
                "requested_seconds": 1, "effective_seconds": 1, "captured_at": 2000,
                "audio_route": {"pid": 123, "sink": "fixture", "verified": True,
                                "sink_inputs": ["42"], "at": 2000}}
        return wav, meta

    def test_audio_requires_rom_session_hash_timeline_duration_and_signal(self):
        wav, meta = self.audio()
        self.assertFalse(gate._audio_supported(self.root))  # Fresh + signal alone is insufficient.
        sidecar = self.write("out/evidence/signal.audio.json", meta)
        self.assertTrue(gate._audio_supported(self.root))
        self.assertTrue(gate._audio_supported(self.root, expected_session=self.sid))
        self.assertFalse(gate._audio_supported(self.root, expected_session="b" * 32))
        for key, bad in (("rom_sha256", "other"), ("session_id", "b" * 32),
                         ("wav_sha256", "other"), ("pid", 999), ("captured_at", 999),
                         ("requested_seconds", 10), ("samples", 12)):
            sidecar.write_text(json.dumps({**meta, key: bad}))
            self.assertFalse(gate._audio_supported(self.root), key)
        sidecar.write_text(json.dumps(meta))
        os.utime(wav, (999, 999))
        self.assertFalse(gate._audio_supported(self.root))
        os.utime(wav, (2000, 2000))
        wav.write_bytes(wav.read_bytes()[:-2] + b"\0\0")
        self.assertFalse(gate._audio_supported(self.root))

    def test_fps_requires_current_rom_session_and_unrounded_windows(self):
        from measure_runtime_probe import runtime_fps_verdict
        for rates, expected in (([58, 60], True), ([57.999, 59], False), ([60, 62], False)):
            metrics = {"rom_sha256": self.sha, "session_id": self.sid, "captured_at": 2000,
                       "region": "NTSC", "fps_janelas": rates, "frames_delta_total": 120,
                       "frame_advance_proved": True, "fps_constante": True}
            path = self.write("out/evidence/fps.json", metrics)
            os.utime(path, (2000, 2000))
            self.assertEqual(gate.axis_support(self.root)["fps_constante"][0], expected)
            self.assertEqual(runtime_fps_verdict(metrics)["passed"], expected)
        metrics["session_id"] = "b" * 32
        metrics["fps_janelas"] = [60, 60]
        self.write("out/evidence/fps.json", metrics)
        self.assertFalse(gate.axis_support(self.root)["fps_constante"][0])


class ToolchainAndSessionTests(unittest.TestCase):
    def test_close_reaps_only_the_supervisor_started_by_this_process(self):
        from unittest.mock import Mock
        child = Mock()
        metadata = {"session_id": "fixture", "state": "closed", "emulator_process": {},
                    "supervisor": {}, "xvfb_process": {}, "audio_sink": "fixture-sink"}
        with patch.object(isolated, "load", return_value=(Path("/unused"), metadata)), \
             patch.object(isolated, "request", return_value={"ok": True}), \
             patch.object(isolated, "alive", return_value=False), \
             patch.object(isolated, "checked", return_value=SimpleNamespace(stdout="[]")), \
             patch.dict(isolated._OWNED_SUPERVISORS, {"fixture": child}, clear=True):
            self.assertEqual(isolated.close_session("fixture"), {"ok": True})
            child.wait.assert_called_once()
            self.assertNotIn("fixture", isolated._OWNED_SUPERVISORS)

    def test_sdcc_below_at_above_minimum_and_unparseable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sdcc = root / "sdcc"
            sdcc.touch()
            for sub, names in (("SMSlib", ("SMSlib.h", "SMSlib.lib")),
                               ("PSGlib", ("PSGlib.h", "PSGlib.lib")),
                               ("crt0", ("crt0_sms.rel",))):
                (root / sub).mkdir()
                for name in names:
                    (root / sub / name).touch()
            with patch.dict(os.environ, {"SMS_DEVKITSMS": tmp}), patch("shutil.which", return_value=str(sdcc)):
                for version, expected in (("3.9.0", False), ("4.0.0", False), ("4.1.99", False),
                                           ("4.2.0", True), ("4.6.0", True), ("5.0.0", True), ("unknown", False)):
                    result = SimpleNamespace(stdout="SDCC " + version)
                    with patch.object(build_inner.subprocess, "run", return_value=result):
                        tc, _ = build_inner.find_toolchain()
                    self.assertEqual(tc is not None, expected, version)

    def test_official_openbor_cli_from_canonical_environment(self):
        import host_bootstrap
        import subprocess
        root = Path(__file__).resolve().parents[3]
        with tempfile.TemporaryDirectory() as tmp:
            for package in ("openbor2sms", "mugen2sms"):
                run = subprocess.run([sys.executable, "-m", package, "--help"], cwd=tmp,
                                     env=host_bootstrap.environment(root, jobs=1),
                                     capture_output=True, text=True, timeout=20)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertIn("usage:", run.stdout.lower())

    def test_session_constructor_failure_still_closes_owned_session(self):
        import session_consumer
        with tempfile.TemporaryDirectory() as tmp:
            rom = Path(tmp) / "game.sms"
            rom.write_bytes(b"offline fixture")
            with patch.object(isolated, "start", return_value=Path(tmp)), \
                 patch.object(session_consumer, "Session", side_effect=ValueError("bad session")), \
                 patch.object(isolated, "close_session") as close:
                with self.assertRaises(ValueError):
                    with session_consumer.private_session(rom):
                        self.fail("must not yield")
                close.assert_called_once_with(Path(tmp))

    def test_rom_changed_during_preparation_never_launches_emulator(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            emulator = root / "tools"
            emulator.mkdir()
            for name in ("Emulicious.jar", "License.txt", "bridge.jar", "Xvfb", "ecj.jar", "ForgeSMS.java"):
                (emulator / name).write_bytes(name.encode())
            rom = root / "game.sms"
            rom.write_bytes(b"before")
            sessions = root / "sessions"
            sessions.mkdir(mode=0o700)
            copy = shutil.copy2

            def changing_copy(source, target):
                result = copy(source, target)
                if Path(source) == rom:
                    rom.write_bytes(b"changed during snapshot")
                return result

            with patch.object(isolated, "EMULATOR", emulator), patch.object(isolated, "HERE", emulator), \
                 patch.object(isolated, "DEFAULT_ROOT", sessions), \
                 patch.object(isolated, "build_bridge", return_value=emulator / "bridge.jar"), \
                 patch.object(isolated.shutil, "which", return_value="available"), \
                 patch.object(isolated.shutil, "copy2", side_effect=changing_copy), \
                 patch.object(isolated.subprocess, "Popen") as launch:
                with self.assertRaisesRegex(RuntimeError, "ROM changed"):
                    isolated.start(rom, xvfb=str(emulator / "Xvfb"), ecj=str(emulator / "ecj.jar"))
                launch.assert_not_called()
                records = list(sessions.glob("*/session.json"))
                self.assertEqual(len(records), 1)
                self.assertEqual(json.loads(records[0].read_text())["state"], "failed")


if __name__ == "__main__":
    unittest.main()
