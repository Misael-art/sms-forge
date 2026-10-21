"""Synthetic offline fixtures calibrate the consumer, not ROM/game quality."""

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import time
import unittest
import wave

from PIL import Image

from openbor2sms import evidence_consumer as consumer


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class BundleFixture:
    """All observations below are explicitly synthetic, never runtime evidence."""

    def __init__(self, root, video_bytes, frame_hashes):
        self.root = root
        self.frozen = time.time() - 1000
        self.sha = digest(b"synthetic offline ROM fixture")
        self.sid = "synthetic-session"
        self.scope = {"scene": "synthetic-TOWN1", "region": "NTSC", "claim_ceiling": "assigned_checks_only"}
        self.bundle = root / "bundle.json"
        self.current = root / "current.sms"
        self.current.write_bytes(b"synthetic offline ROM fixture")
        self.data = {
            "schema": consumer.SCHEMA, "rom": self.write("inputs/rom.sms", self.current.read_bytes(), True),
            "sealed_at": self.frozen + 200, "tools": [], "context": [], "sessions": [],
            "artifacts": [], "coverage": [],
        }
        self.data["rom"]["frozen_at"] = self.frozen
        os.utime(root / "inputs/rom.sms", (self.frozen - 1, self.frozen - 1))
        for role in consumer.TOOL_FIELDS:
            ref = self.write(f"inputs/{role}.bin", ("synthetic tool " + role).encode(), True)
            self.data["tools"].append({"role": role, **ref})
        for role in ("memory_bank", "gdd", "scene_spec", "tdd"):
            ref = self.write(f"inputs/{role}.md", ("Synthetic context " + role).encode(), True)
            self.data["context"].append({"role": role, **ref})
        self.initial = {"schema": 1, **self.identity(), "created_at": self.frozen + 10,
                        "state": "input_verified", "audio_sink": "synthetic-private-sink"}
        for tool in self.data["tools"]:
            self.initial[consumer.TOOL_FIELDS[tool["role"]]] = tool["sha256"]
        for index, role in enumerate(consumer.PROCESS_ROLES):
            self.initial[role] = {"pid": 10000000 + index, "start_ticks": str(100 + index)}
        self.final = {**self.initial, "state": "closed", "closed_at": self.frozen + 100}
        self.cleanup = {"schema": "sms_openbor_cleanup_v1", **self.identity(),
                        "checked_at": self.frozen + 101, "audio_sink": self.initial["audio_sink"],
                        "audio_sink_state": "removed", "processes": [
                            {"role": role, **self.initial[role], "state": "exited"}
                            for role in consumer.PROCESS_ROLES]}
        self.journal = []
        self.add("read", [0xc005, 1], 0, ram=[50])
        self.add("input", [16, 0, 0], 1, p1=16)
        self.add("read", [0xc010, 1], 2, ram=[16])
        self.add("read", [0xc005, 1], 8, ram=[43])
        self.add("read", [0xc7e0, 5], 12, ram=[83, 77, 82, 84, 2])
        windows = []
        for index in range(3):
            before = len(self.journal) + 1
            counter = 100 + index * 60
            frame = 12 + index * 60
            self.add("read", [0xc7f0, 2], frame, ram=list(counter.to_bytes(2, "little")))
            self.add("run", [], frame)
            self.add("pause", [], frame + 60)
            self.add("read", [0xc7f0, 2], frame + 60, ram=list((counter + 60).to_bytes(2, "little")))
            windows.append({"before_seq": before, "after_seq": before + 3,
                            "elapsed_seconds": 1, "max_counter_advance": 100})
        session = {"id": self.sid, "initial": self.obj("session.initial.json", self.initial),
                   "final": self.obj("session.final.json", self.final),
                   "cleanup": self.obj("cleanup.json", self.cleanup),
                   "journal": self.write_journal()}
        self.data["sessions"] = [session]
        self.contract = {"schema": consumer.CONTRACT_SCHEMA, "scope": self.scope, "required_cases": [
            {"id": "boot", "axis": "boot_emulador", "proof": "framebuffer"},
            {"id": "attack", "axis": "gameplay", "proof": "input_ram_video", "input_mask": 16,
             "input_read": {"address": 0xc010, "length": 1, "mask": 16},
             "effect_read": {"address": 0xc005, "length": 1}, "relation": "decrease"},
            {"id": "ntsc", "axis": "fps_constante", "proof": "regional_runtime_windows"},
            {"id": "sfx", "axis": "audio", "proof": "audio_signal"},
        ]}
        self.data["contract"] = self.obj("contract.json", self.contract, True)
        image = Image.new("RGB", (256, 192), (0, 0, 0))
        image.paste((255, 255, 255), (32, 32, 128, 128))
        image.save(root / "frame.png")
        png = (root / "frame.png").read_bytes()
        self.capture_meta = {"schema": 1, **self.identity(), "sha256": digest(png), "canvas": [256, 192],
                             "captured_at": self.frozen + 50, "informative": False}
        self.artifact("boot", "png", "frame.png", png, self.capture_meta)
        self.video_meta = {"schema": 1, **self.identity(), "sha256": digest(video_bytes), "canvas": [256, 192],
                           "first_frame": 0, "last_frame": 12, "frames": 12,
                           "frame_sha256": frame_hashes, "distinct_frames": 12,
                           "method": "one native framebuffer per VDP frame; stepped emulation",
                           "performance": "not_measured", "audio": "not_recorded"}
        self.artifact("video", "video", "attack.mp4", video_bytes, self.video_meta)
        self.observation = {"schema": "sms_openbor_input_observation_v1", **self.identity(),
                            "journal_sha256": session["journal"]["sha256"],
                            "before_seq": 1, "input_seq": 2, "consumed_seq": 3, "after_seq": 4}
        self.artifact("input", "input_observation", "input.json", self.json_bytes(self.observation), self.observation)
        self.metrics = {"schema": "runtime_metrics_v1", **self.identity(), "region": "NTSC",
                        "fps_janelas": [60, 60, 60], "frames_delta_total": 180,
                        "fps_constante": False, "axes": {"aprovado": False}}
        self.windows = {"schema": "sms_openbor_runtime_windows_v1", **self.identity(),
                        "journal_sha256": session["journal"]["sha256"], "header_seq": 5,
                        "counter": {"address": 0xc7f0, "length": 2}, "windows": windows}
        self.artifact("fps", "runtime_metrics", "runtime.json", self.json_bytes(self.metrics), self.windows)
        with wave.open(str(root / "signal.wav"), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(44100)
            wav.writeframes(struct.pack("<h", 1000) * 44100)
        audio = (root / "signal.wav").read_bytes()
        self.audio_meta = {**self.identity(), "wav_sha256": digest(audio),
                           "pid": self.initial["emulator_process"]["pid"], "sink": self.initial["audio_sink"],
                           "moved_sink_inputs": ["123"], "requested_seconds": 1, "effective_seconds": 1,
                           "samples": 44100, "peak": 1000, "audio_route": {
                               "pid": self.initial["emulator_process"]["pid"], "sink": self.initial["audio_sink"],
                               "sink_inputs": ["123"], "verified": True, "at": self.frozen + 30}}
        self.artifact("audio", "wav", "signal.wav", audio, self.audio_meta)
        self.data["coverage"] = [{"case_id": "boot", "artifacts": ["boot"]},
                                 {"case_id": "attack", "artifacts": ["input", "video"]},
                                 {"case_id": "ntsc", "artifacts": ["fps"]},
                                 {"case_id": "sfx", "artifacts": ["audio"]}]
        self.save()

    @staticmethod
    def json_bytes(obj):
        return json.dumps(obj).encode()

    def identity(self):
        return {"session_id": self.sid, "rom_sha256": self.sha}

    def write(self, name, raw, immutable=False):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.chmod(0o644)
        path.write_bytes(raw)
        os.utime(path, (self.frozen + 20, self.frozen + 20))
        if immutable:
            path.chmod(0o444)
        return {"path": name, "sha256": digest(raw), "bytes": len(raw)}

    def obj(self, name, obj, immutable=False):
        return self.write(name, self.json_bytes(obj), immutable)

    def add(self, operation, args, frame, **extra):
        seq = len(self.journal) + 1
        self.journal.append({"operation": operation, "args": args, "at": self.frozen + 10 + seq,
                             "ack": {"ok": True, "session_id": self.sid, "seq": seq,
                                     "frame": frame, "p1": 0, **extra}})

    def write_journal(self):
        return self.write("commands.jsonl", b"\n".join(self.json_bytes(row) for row in self.journal))

    def artifact(self, aid, kind, name, raw, meta):
        self.data["artifacts"].append({"id": aid, "kind": kind, "session_id": self.sid,
                                       "captured_at": self.frozen + 50, "file": self.write(name, raw),
                                       "metadata": self.obj(aid + ".metadata.json", meta)})

    def item(self, aid):
        return next(row for row in self.data["artifacts"] if row["id"] == aid)

    def update_artifact(self, aid, obj=None, meta=None, raw=None):
        item = self.item(aid)
        if obj is not None:
            raw = self.json_bytes(obj)
        if raw is not None:
            item["file"] = self.write(item["file"]["path"], raw)
        if meta is not None:
            item["metadata"] = self.obj(item["metadata"]["path"], meta)

    def refresh_journal(self):
        self.data["sessions"][0]["journal"] = self.write_journal()
        sha = self.data["sessions"][0]["journal"]["sha256"]
        self.observation["journal_sha256"] = sha
        self.windows["journal_sha256"] = sha
        self.update_artifact("input", obj=self.observation)
        self.update_artifact("fps", meta=self.windows)

    def save(self):
        self.bundle.write_text(json.dumps(self.data))

    def consume(self, **kwargs):
        self.save()
        return consumer.consume(self.bundle, self.current, **kwargs)


class EvidenceConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            raise unittest.SkipTest("media positive calibration requires ffmpeg/ffprobe")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hashes = []
            for index in range(12):
                im = Image.new("RGB", (256, 192), (0, 0, 0))
                im.paste((255, 255, 255), (index * 8, 40, index * 8 + 32, 80))
                path = root / f"{index:06d}.png"
                im.save(path)
                hashes.append(digest(path.read_bytes()))
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-framerate", "60", "-i",
                            str(root / "%06d.png"), "-c:v", "libx264", "-crf", "0", "-pix_fmt", "yuv444p",
                            str(root / "fixture.mp4")], check=True, capture_output=True)
            cls.video_bytes, cls.frame_hashes = (root / "fixture.mp4").read_bytes(), hashes

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.f = BundleFixture(Path(self.temp.name), self.video_bytes, self.frame_hashes)

    def rejected(self, text=None):
        report = self.f.consume()
        self.assertFalse(report["eligible"], report)
        self.assertFalse(any(report["axes"].values()), report)
        self.assertTrue(report["problems"])
        if text:
            self.assertIn(text, " ".join(report["problems"]))
        return report

    def test_positive_derives_runtime_axes_and_preserves_limits(self):
        report = self.f.consume(expected_cases={"boot", "attack", "ntsc", "sfx"}, expected_scope=self.f.scope)
        self.assertTrue(report["eligible"], report["problems"])
        self.assertEqual({axis for axis, value in report["axes"].items() if value}, set(consumer.PROOFS))
        self.assertEqual(report["coverage"]["attack"]["derived"], {"before": 50, "after": 43, "relation": "decrease"})
        self.assertIn("not_per_frame", report["axis_scope"]["fps_constante"])
        self.assertIn("not_music", report["axis_scope"]["audio"])
        self.assertEqual(report["claim_authority"], "coordinator")
        self.assertTrue(consumer.axis_support(self.f.bundle, self.f.current)["gameplay"][0])

    def test_positive_boot_only_never_infers_gameplay_fps_audio(self):
        self.f.contract["required_cases"] = self.f.contract["required_cases"][:1]
        self.f.data["contract"] = self.f.obj("contract.json", self.f.contract, True)
        self.f.data["artifacts"] = [self.f.item("boot")]
        self.f.data["coverage"] = self.f.data["coverage"][:1]
        report = self.f.consume()
        self.assertTrue(report["eligible"], report["problems"])
        self.assertEqual([key for key, value in report["axes"].items() if value], ["boot_emulador"])

    def test_changed_current_rom(self):
        self.f.current.write_bytes(b"another ROM")
        self.rejected("current ROM mismatch")

    def test_changed_snapshot_hash(self):
        path = self.f.root / "inputs/rom.sms"
        path.chmod(0o644)
        path.write_bytes(b"changed")
        path.chmod(0o444)
        self.rejected("SHA mismatch")

    def test_live_rom_is_not_immutable_snapshot(self):
        (self.f.root / "inputs/rom.sms").chmod(0o644)
        self.rejected("immutable snapshot")

    def test_rom_alias_even_with_matching_bytes(self):
        self.f.data["rom"]["path"] = "current.sms"
        self.f.current.chmod(0o444)
        self.rejected("live ROM alias")

    def test_stale_artifact_time(self):
        self.f.item("video")["captured_at"] = self.f.frozen - 1
        self.rejected("stale artifact")

    def test_stale_file_even_when_declared_time_is_fresh(self):
        path = self.f.root / self.f.item("boot")["file"]["path"]
        os.utime(path, (self.f.frozen - 1, self.f.frozen - 1))
        self.rejected("stale artifact file")

    def test_session_identity_mismatch(self):
        self.f.final["session_id"] = "other-session"
        self.f.data["sessions"][0]["final"] = self.f.obj("session.final.json", self.f.final)
        self.rejected("identity mismatch")

    def test_unclosed_session_is_not_cleanup(self):
        self.f.final["state"] = "input_verified"
        self.f.data["sessions"][0]["final"] = self.f.obj("session.final.json", self.f.final)
        self.rejected("session states")

    def test_missing_cleanup_process(self):
        self.f.cleanup["processes"].pop()
        self.f.data["sessions"][0]["cleanup"] = self.f.obj("cleanup.json", self.f.cleanup)
        self.rejected("cleanup process coverage")

    def test_changed_process_and_tool_identity(self):
        self.f.final["bridge_sha256"] = "0" * 64
        self.f.data["sessions"][0]["final"] = self.f.obj("session.final.json", self.f.final)
        self.rejected("tool mismatch")

    def test_missing_case(self):
        self.f.data["coverage"].pop(1)
        self.rejected("coverage missing")

    def test_coordinator_detects_removed_contract_case(self):
        report = self.f.consume(expected_cases={"boot", "attack", "ntsc", "sfx", "air_hit"})
        self.assertFalse(report["eligible"])
        self.assertIn("required cases mismatch", report["problems"][0])

    def test_wrong_scope(self):
        report = self.f.consume(expected_scope={**self.f.scope, "region": "PAL"})
        self.assertFalse(report["eligible"])
        self.assertIn("scope mismatch", report["problems"][0])

    def test_wrong_proof_kind(self):
        self.f.data["coverage"][1]["artifacts"] = ["boot"]
        self.rejected("proof artifacts mismatch")

    def test_media_metadata_wrong_session(self):
        self.f.video_meta["session_id"] = "other-session"
        self.f.update_artifact("video", meta=self.f.video_meta)
        self.rejected("identity mismatch")

    def test_invalid_png_bytes_despite_updated_hashes(self):
        raw = b"not a PNG"
        self.f.capture_meta["sha256"] = digest(raw)
        self.f.update_artifact("boot", raw=raw, meta=self.f.capture_meta)
        self.rejected()

    def test_uniform_png_cannot_be_approved_by_boolean(self):
        path = self.f.root / "bad.png"
        Image.new("RGB", (256, 192), (255, 255, 255)).save(path)
        raw = path.read_bytes()
        self.f.capture_meta.update(sha256=digest(raw), informative=True)
        self.f.update_artifact("boot", raw=raw, meta=self.f.capture_meta)
        self.f.data["axes"] = dict.fromkeys(consumer.AXES, True)
        self.rejected("uniform")

    def test_invalid_video_despite_updated_hash(self):
        raw = b"not a video"
        self.f.video_meta["sha256"] = digest(raw)
        self.f.update_artifact("video", raw=raw, meta=self.f.video_meta)
        self.rejected("decoder rejected")

    def test_wrong_video_frame_count(self):
        self.f.video_meta["frames"] = 60
        self.f.update_artifact("video", meta=self.f.video_meta)
        self.rejected("frame count")

    def test_video_does_not_cover_gameplay(self):
        self.f.video_meta.update(first_frame=100, last_frame=112)
        self.f.update_artifact("video", meta=self.f.video_meta)
        self.rejected("cover input")

    def test_invalid_wav_despite_updated_hash(self):
        raw = b"not a WAV"
        self.f.audio_meta["wav_sha256"] = digest(raw)
        self.f.update_artifact("audio", raw=raw, meta=self.f.audio_meta)
        self.rejected("WAV RIFF")

    def test_silent_wav_is_rejected(self):
        raw = (self.f.root / "signal.wav").read_bytes()[:44] + b"\0" * (44100 * 2)
        self.f.audio_meta.update(wav_sha256=digest(raw), peak=0)
        self.f.update_artifact("audio", raw=raw, meta=self.f.audio_meta)
        self.rejected("silent WAV")

    def test_audio_of_wrong_pid(self):
        self.f.audio_meta["pid"] = 42
        self.f.update_artifact("audio", meta=self.f.audio_meta)
        self.rejected("PID/private sink")

    def test_input_ack_alone_does_not_prove_consumption(self):
        self.f.journal[2]["ack"]["ram"] = [0]
        self.f.refresh_journal()
        self.rejected("not observed by ROM")

    def test_claim_pass_cannot_override_failed_consequence(self):
        self.f.journal[3]["ack"]["ram"] = [50]
        self.f.refresh_journal()
        self.f.data["claims"] = [{"id": "attack", "verdict": "pass"}]
        self.rejected("RAM consequence failed")

    def test_mutating_journal_rejected(self):
        self.f.journal[1]["operation"] = "write"
        self.f.refresh_journal()
        self.rejected("mutating journal")

    def test_journal_session_mismatch(self):
        self.f.journal[1]["ack"]["session_id"] = "other-session"
        self.f.refresh_journal()
        self.rejected("ACK/session")

    def test_stepped_windows_cannot_prove_fps(self):
        self.f.journal[6]["operation"] = "step"
        self.f.refresh_journal()
        self.rejected("never stepping")

    def test_ambiguous_frame_counter_window(self):
        self.f.windows["windows"][0]["max_counter_advance"] = 65536
        self.f.update_artifact("fps", meta=self.f.windows)
        self.rejected("ambiguous")

    def test_fps_boolean_cannot_replace_raw_windows(self):
        self.f.metrics["fps_constante"] = True
        self.f.windows["windows"] = []
        self.f.update_artifact("fps", obj=self.f.metrics, meta=self.f.windows)
        self.rejected("three regional")

    def test_hash_tampering(self):
        (self.f.root / "input.json").write_text("{}")
        self.rejected("SHA mismatch")

    def test_path_traversal(self):
        self.f.item("input")["file"]["path"] = "../input.json"
        self.rejected("path must")

    def test_symlink_and_hardlink_snapshot_rejected(self):
        path = self.f.root / "inputs/rom.sms"
        path.unlink()
        path.symlink_to(self.f.current)
        self.rejected("symlink")
        path.unlink()
        os.link(self.f.current, path)
        self.rejected("hardlink")

    def test_duplicate_case_and_nonfinite_timestamp(self):
        self.f.data["coverage"].append(copy.deepcopy(self.f.data["coverage"][0]))
        self.rejected("duplicate case_id")
        self.f.data["coverage"].pop()
        self.f.data["sealed_at"] = float("nan")
        self.rejected("invalid number")

    def test_m6_historical_format_never_promotes(self):
        legacy = {"schema": "sms_evidence_m6_v1", "rom_sha256": self.f.sha, "rom_bytes": 131072,
                  "claims": [{"id": "attack_causal", "verdict": "pass", "artifact": self.f.item("input")["file"]}],
                  "sessions": {"traces": ["m6/sessions/example"]}}
        self.f.data = legacy
        report = self.rejected("historical M6")
        self.assertEqual(report["historical_artifacts_checked"], ["attack_causal"])

    def test_unknown_schema_and_duplicate_json_keys(self):
        self.f.data["schema"] = "future-unsupported"
        self.rejected("unsupported evidence schema")
        self.f.bundle.write_text('{"schema":"x","schema":"y"}')
        report = consumer.consume(self.f.bundle, self.f.current)
        self.assertIn("duplicate JSON key", report["problems"][0])

    def test_cli_help_and_missing_arguments(self):
        command = ["python3", "-m", "openbor2sms.evidence_consumer"]
        result = subprocess.run(command + ["--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--self-check", result.stdout)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
