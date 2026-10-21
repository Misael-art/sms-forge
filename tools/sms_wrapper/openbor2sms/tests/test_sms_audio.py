"""O3/D11 offline: fixtures PCM/PAK sinteticas, nunca conteudo do doador."""
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import wave

from openbor2sms import sms_audio as audio
from openbor2sms.pak import build_pak32


def wav_fixture(samples=b"\x80\xb0\x80\x50"):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setparams((1, 1, 8000, 0, "NONE", "not compressed"))
        output.writeframes(samples)
    return buffer.getvalue()


def archive_fixture():
    return build_pak32([(spec.source_member, wav_fixture()) for spec in audio.SFX])


def generate(blob=None):
    if blob is None:
        blob = archive_fixture()
    return audio.generate(blob, expected_sha256=hashlib.sha256(blob).hexdigest(),
                          expected_bytes=len(blob))


def driver_timeline(stream):
    """Oracle par appels: reproduit skip/lecture/OUT/stop du driver SFX.

    Deliberement distinct de l'inspecteur: pas de somme des WAIT, mais un
    appel par tick, et decodage des bits de canal des octets OUT.
    """
    pointer, skip, tick = 0, 0, 0
    writes = []
    for call in range(100):
        if skip:
            skip -= 1
        else:
            while pointer < len(stream):
                byte = stream[pointer]
                pointer += 1
                if byte >= 0x40:
                    writes.append((tick, byte))
                elif byte >= 0x38:
                    skip = byte & 7
                    break
                elif byte == 0:
                    return tick, call + 1, writes
                else:
                    raise AssertionError("oracle somente streams simples")
            else:
                raise AssertionError("stream sem fim")
        tick += 1
    raise AssertionError("stream nao terminou em 100 chamadas")


class StreamTests(unittest.TestCase):
    def test_three_roles_duration_priority_and_mask(self):
        self.assertEqual([(s.symbol, s.duration_ticks, s.priority) for s in audio.SFX],
                         [("sfx_attack", 6, 1), ("sfx_impact", 10, 2), ("sfx_fall", 18, 3)])
        self.assertEqual((audio.CHANNEL, audio.MASK, audio.MASK_NAME),
                         (3, 0x02, "SFX_CHANNEL3"))

    def test_actual_calls_terminal_channel_and_authored_events(self):
        for spec in audio.SFX:
            with self.subTest(spec=spec.symbol):
                stream = audio.encode_sfx(spec)
                tick, calls, writes = driver_timeline(stream)
                self.assertEqual((tick, calls), (spec.duration_ticks, spec.duration_ticks + 1))
                self.assertEqual(stream[-2:], b"\xff\x00")
                self.assertEqual({(byte >> 5) & 3 for _, byte in writes}, {3})
                expected = []
                for event in spec.events:
                    if event.noise_mode is not None:
                        expected.append((event.tick, 0xE0 | event.noise_mode))
                    expected.append((event.tick, 0xF0 | event.attenuation))
                self.assertEqual(writes, expected)
                inspection = audio.inspect_stream(stream)
                self.assertEqual(inspection["duration_ticks"], tick)
                self.assertEqual(inspection["driver_calls_through_stop"], calls)

    def test_long_hold_compact_wait_oracle(self):
        spec = replace(audio.SFX[0], duration_ticks=18,
                       events=(audio.NoiseEvent(0, 2, 4), audio.NoiseEvent(18, 15)))
        # WAIT8, WAIT8, WAIT2: 0x3f, 0x3f, 0x39, sans repetitions du volume.
        data = audio.encode_sfx(spec)
        self.assertEqual(data, b"\xe4\xf2\x3f\x3f\x39\xff\x00")
        self.assertEqual(driver_timeline(data)[:2], (18, 19))

    def test_invalid_streams_rejected(self):
        streams = (b"", b"\x00", b"\xe4\xf2\x38", b"\xe4\xf2\x38\x00",
                   b"\xe4\xf2\x38\xff\x00\x38", b"\x38\xe4\xff\x00",
                   b"\xe4\xf2\x01\x38\xff\x00", b"\xe4\xf2\x08\x00\x00",
                   b"\xc1\x40\x38\xdf\x00", b"\xe7\xf2\x38\xff\x00",
                   b"\xe3\xf2\x38\xff\x00", b"\xf2\x38\xff\x00",
                   b"\xe4\xf2\x40\x38\xff\x00")
        for stream in streams:
            with self.subTest(stream=stream), self.assertRaises(ValueError):
                audio.inspect_stream(stream)

    def test_invalid_declarations_rejected(self):
        source = audio.SFX[0]
        specs = [replace(source, duration_ticks=n) for n in (0, -1, 46, 1.5, True)]
        specs += [replace(source, priority=p) for p in (0, 256, True)]
        event_sets = ((), (audio.NoiseEvent(0, 3), audio.NoiseEvent(6, 15)),
                      (audio.NoiseEvent(0, 3, 7), audio.NoiseEvent(6, 15)),
                      (audio.NoiseEvent(0, 16, 4), audio.NoiseEvent(6, 15)),
                      (audio.NoiseEvent(1, 3, 4), audio.NoiseEvent(6, 15)),
                      (audio.NoiseEvent(0, 3, 4), audio.NoiseEvent(0, 5)),
                      (audio.NoiseEvent(0, 3, 4), audio.NoiseEvent(7, 15)),
                      (audio.NoiseEvent(0, 3, 4), audio.NoiseEvent(6, 14)),
                      (audio.NoiseEvent(0, 3, 4), audio.NoiseEvent(6, 15, 5)),
                      (audio.NoiseEvent(0, 15, 4), audio.NoiseEvent(6, 15)),
                      (audio.NoiseEvent(0, 3, 4), audio.NoiseEvent(3, 15),
                       audio.NoiseEvent(6, 15)))
        specs += [replace(source, events=events) for events in event_sets]
        for spec in specs:
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                audio.encode_sfx(spec)


class BundleTests(unittest.TestCase):
    def test_determinism_all_artifacts_across_destinations(self):
        first = generate()
        self.assertEqual(first, generate())
        with tempfile.TemporaryDirectory() as temporary:
            for directory in (Path(temporary) / "a", Path(temporary) / "b"):
                audio.write_bundle(directory, first)
                audio.write_bundle(directory, first)
                actual = {p.relative_to(directory).as_posix(): p.read_bytes()
                          for p in directory.rglob("*") if p.is_file()}
                self.assertEqual(actual, first)

    def test_manifest_hashes_bytes_sources_duration_and_limits(self):
        outputs = generate()
        manifest = json.loads(outputs[audio.MANIFEST_PATH])
        self.assertEqual(manifest["source_archive"]["sha256"], audio.sha256(archive_fixture()))
        self.assertEqual(manifest["validation"], {"host_streams": "checked", "runtime": "not_run",
                                                "audition": "not_run", "budget": "not_run"})
        for asset, spec in zip(manifest["assets"], audio.SFX):
            data = outputs[asset["file"]]
            self.assertEqual((asset["sha256"], asset["bytes"]), (audio.sha256(data), len(data)))
            ref = asset["reference"]
            self.assertEqual((ref["sha256"], ref["bytes"]),
                             (audio.sha256(wav_fixture()), len(wav_fixture())))
            self.assertEqual(outputs[ref["file"]], wav_fixture())
            self.assertEqual(ref["pak_member"], spec.source_member)
            self.assertEqual(ref["wav"]["samples"], 4)
            self.assertEqual(ref["wav"]["sample_rate"], 8000)
            self.assertEqual((asset["channels"], asset["mask"], asset["priority"]),
                             ("SFX_CHANNEL3", 2, spec.priority))
            self.assertEqual(asset["duration_ms_at_50_calls_per_second"], spec.duration_ticks * 20)
            self.assertEqual(asset["duration_ms_at_60_calls_per_second"],
                             {"numerator": spec.duration_ticks * 1000, "denominator": 60})
            self.assertEqual(asset["encoded_events"], audio.inspect_stream(data)["events"])
            self.assertIn("reautoria/adaptacao", asset["origin"])
            self.assertEqual(asset["classification"], "adapted")
            self.assertFalse(asset["fidelity_claim"])
            self.assertIn("IA", asset["author"])
        for record in manifest["driver_sources"] + [manifest["generator"]]:
            self.assertEqual(record["sha256"], audio.sha256((audio.REPO / record["file"]).read_bytes()))
        header = manifest["header"]
        self.assertEqual(header["sha256"], audio.sha256(outputs[header["file"]]))
        self.assertEqual(header["bytes"], len(outputs[header["file"]]))
        placement = manifest["runtime_contract"]["placement"]
        self.assertEqual(placement["banks"], [0, 1])
        self.assertEqual(placement["address_end_exclusive"], 0x8000)
        self.assertTrue(placement["verify_in_linker_map"])

    def test_header_arrays_sizes_duration_priority_mask_exact(self):
        outputs = generate()
        header = outputs[audio.HEADER_PATH].decode("ascii")
        self.assertNotIn("#pragma constseg BANK", header)
        for spec in audio.SFX:
            symbol = spec.symbol
            prefix = symbol.upper()
            array = re.search(rf"{symbol}\[{prefix}_SIZE\] = \{{([^}}]+)\}};", header)
            self.assertIsNotNone(array)
            data = bytes(int(token, 16) for token in re.findall(r"0x[0-9A-F]{2}", array[1]))
            self.assertEqual(data, outputs[f"res/audio/{symbol}.psg"])
            for suffix, expected in (("SIZE", len(data)), ("DURATION_TICKS", spec.duration_ticks),
                                     ("PRIORITY", spec.priority), ("MASK", "SFX_CHANNEL3")):
                self.assertIn(f"#define {prefix}_{suffix} {expected}\n", header)

    def test_pak_identity_missing_member_collision_and_bad_wav(self):
        blob = archive_fixture()
        for kwargs in ({"expected_sha256": "0" * 64, "expected_bytes": len(blob)},
                       {"expected_sha256": audio.sha256(blob), "expected_bytes": len(blob) + 1}):
            with self.assertRaisesRegex(ValueError, "PAK diverge"):
                audio.generate(blob, **kwargs)
        fixtures = [build_pak32([]),
                    build_pak32([(s.source_member, b"PCM is not PSG or valid WAV") for s in audio.SFX]),
                    build_pak32([(s.source_member, wav_fixture()) for s in audio.SFX] +
                                [(audio.SFX[0].source_member.upper(), wav_fixture())]),
                    build_pak32([(s.source_member, wav_fixture()[:-1]) for s in audio.SFX])]
        for fixture in fixtures:
            with self.subTest(fixture=audio.sha256(fixture)), self.assertRaises(ValueError):
                generate(fixture)
        with self.assertRaisesRegex(ValueError, "autoria"):
            audio.generate(blob, expected_sha256=audio.sha256(blob),
                           expected_bytes=len(blob), author=" ")

    def test_driver_drift_blocks_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            for relative in audio.DRIVER_FILES:
                target = repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((audio.REPO / relative).read_bytes())
            for relative in audio.DRIVER_FILES:
                target = repo / relative
                original = target.read_bytes()
                target.write_bytes(original + b"/* changed */")
                with patch.object(audio, "REPO", repo), self.assertRaisesRegex(ValueError, "mudou"):
                    generate()
                target.write_bytes(original)

    def test_existing_divergence_and_path_escape_do_not_write_other_outputs(self):
        outputs = generate()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "candidate"
            target = root / audio.MANIFEST_PATH
            target.parent.mkdir(parents=True)
            target.write_bytes(b"existing manifest")
            with self.assertRaisesRegex(ValueError, "existente diverge"):
                audio.write_bundle(root, outputs)
            self.assertFalse((root / audio.HEADER_PATH).exists())
            for relative in ("../escaped", str(Path(temporary) / "absolute")):
                with self.assertRaisesRegex(ValueError, "escapa"):
                    audio.write_bundle(root, {relative: b"invalid"})
            (root / "link").symlink_to(Path(temporary), target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "escapa"):
                audio.write_bundle(root, {"link/escaped": b"invalid"})

    def test_cli_tmp_generation_self_check_and_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pak_path = root / "fixture.pak"
            blob = archive_fixture()
            pak_path.write_bytes(blob)
            args = ["--pak", str(pak_path), "--expect-pak-sha256", audio.sha256(blob),
                    "--expect-pak-bytes", str(len(blob)), "--out", str(root / "generated")]
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(audio.main(args), 0)
                self.assertEqual(audio.main(["--self-check"]), 0)
            self.assertEqual((root / "generated" / audio.MANIFEST_PATH).read_bytes(),
                             generate()[audio.MANIFEST_PATH])
            args[3] = "0" * 64
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(audio.main(args), 1)


if __name__ == "__main__":
    unittest.main()
