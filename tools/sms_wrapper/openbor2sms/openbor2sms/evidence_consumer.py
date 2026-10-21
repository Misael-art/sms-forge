"""Read-only OpenBOR evidence adapter; never writes build records or claims.

``consume(bundle, current_rom, expected_cases=..., expected_scope=...)`` returns
derived axes, per-case results, scope and diagnostics. ``axis_support`` exposes
the tuple interface used by reconcile_claims. Integration is intentionally left
to the coordinator: do not OR a failed successor with unbound legacy evidence.

Successor schema: sms_openbor_evidence_v2. Paths are relative to the bundle,
confined to its directory, with {path, sha256, bytes} references. Required keys:
rom (reference plus frozen_at), sealed_at, contract (reference), tools/context
(lists of references with role), sessions (id, initial/final/journal/cleanup
references), artifacts (id, kind, session_id, captured_at, file and metadata
references), coverage (case_id, artifacts IDs). No input axes are consumed.

The hashed sms_openbor_evidence_contract_v1 contains scope {scene, region,
claim_ceiling: assigned_checks_only}, required_cases [{id, axis, proof, ...}].
Proofs: framebuffer, input_ram_video, regional_runtime_windows, audio_signal.
Gameplay cases additionally define input_mask, input_read {address,length,mask},
effect_read {address,length}, relation (increase/decrease/change/equal).
An input observation selects before_seq/input_seq/consumed_seq/after_seq from
the real private-session JSONL journal; numeric RAM effects are recomputed.

Native capture schema 1 PNG/video and capture_audio's JSON are supported.
runtime_metrics_v1 needs supplemental sms_openbor_runtime_windows_v1 metadata:
journal_sha256, header_seq, counter {address,length}, windows with before_seq,
after_seq, elapsed_seconds, max_counter_advance. These bind measured windows
to journal reads; max_counter_advance must exclude rollover ambiguity.
Cleanup schema sms_openbor_cleanup_v1 records checked_at and processes
[{role,pid,start_ticks,state: exited}], plus audio_sink_state: removed if used.
Manifests remain the real schema 1 initial and closed final session records.

All links are checked, PNG/video/WAV bytes decoded, no emulator is launched.
Recorded observations are not authenticated against a malicious producer.
FPS support means regional window means, NOT per-frame pacing; audio means
isolated signal, NOT fidelity. Cases/context still need coordinator review.
M6 v1 is inspected as historical material and NEVER promotes runtime axes.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import wave


SCHEMA = "sms_openbor_evidence_v2"
CONTRACT_SCHEMA = "sms_openbor_evidence_contract_v1"
AXES = ("build", "validation_report", "boot_emulador", "gameplay",
        "fps_constante", "audio", "memory_bank_atualizado")
PROOFS = {"boot_emulador": "framebuffer", "gameplay": "input_ram_video",
          "fps_constante": "regional_runtime_windows", "audio": "audio_signal"}
SCOPES = {"boot_emulador": "informative_native_framebuffer_only",
          "gameplay": "assigned_input_and_ram_effect_cases_only",
          "fps_constante": "regional_mean_frame_rate_windows_only_not_per_frame_pacing_or_game_feel",
          "audio": "isolated_session_signal_only_not_music_correctness"}
PROCESS_ROLES = ("supervisor", "xvfb_process", "sandbox", "emulator_process")
TOOL_FIELDS = {"emulator": "emulator_sha256", "bridge": "bridge_sha256",
               "bridge_source": "bridge_source_sha256", "config_initial": "config_initial_sha256"}
SHA = re.compile(r"[0-9a-f]{64}\Z")


class EvidenceError(ValueError):
    """Invalid or unsupported evidence, never a reason to inherit old axes."""


def _need(condition, message):
    if not condition:
        raise EvidenceError(message)


def _number(value, label):
    _need(type(value) in (int, float) and math.isfinite(value) and value >= 0,
          f"{label}: expected finite nonnegative number")
    return value


def _integer(value, label, minimum=0):
    _need(type(value) is int and value >= minimum, f"{label}: invalid integer")
    return value


def _sha(value):
    _need(isinstance(value, str) and SHA.fullmatch(value), "invalid SHA256")
    return value


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _need(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result
    value = json.loads(raw, object_pairs_hook=pairs,
                       parse_constant=lambda x: (_ for _ in ()).throw(EvidenceError(f"invalid number {x}")))
    _need(isinstance(value, dict), "JSON object required")
    return value


def _index(rows, key):
    _need(isinstance(rows, list) and rows, f"nonempty {key} list required")
    result = {}
    for row in rows:
        _need(isinstance(row, dict), f"invalid {key} entry")
        value = row.get(key)
        _need(isinstance(value, str) and value.strip() and value not in result,
              f"missing/duplicate {key}: {value}")
        result[value] = row
    return result


class _Reader:
    def __init__(self, root):
        self.root = root.resolve()
        self.observed = {}

    def read(self, ref, immutable=False):
        _need(isinstance(ref, dict), "file reference required")
        relative = ref.get("path")
        _need(isinstance(relative, str) and relative and not Path(relative).is_absolute()
              and ".." not in Path(relative).parts, "path must be bundle-relative without traversal")
        path = self.root / relative
        for part in (path, *path.parents):
            if part == self.root:
                break
            _need(not part.is_symlink(), f"symlink rejected: {relative}")
        _need(path.resolve().is_relative_to(self.root) and path.is_file(), f"missing/confined file: {relative}")
        stat = path.stat()
        _need(stat.st_nlink == 1, f"hardlink rejected: {relative}")
        if immutable:
            _need(stat.st_mode & 0o222 == 0, f"immutable snapshot required: {relative}")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        _need(digest == _sha(ref.get("sha256")), f"SHA mismatch: {relative}")
        _need(len(raw) == _integer(ref.get("bytes"), "bytes", 1), f"byte count mismatch: {relative}")
        self.observed[path] = digest
        return path, raw

    def obj(self, ref, immutable=False):
        return _json(self.read(ref, immutable)[1])

    def recheck(self):
        for path, digest in self.observed.items():
            _need(hashlib.sha256(path.read_bytes()).hexdigest() == digest,
                  f"file changed during consumption: {path.name}")


def _identity(record, sid, sha):
    _need(record.get("session_id") == sid and record.get("rom_sha256") == sha,
          "session/ROM identity mismatch")


def _session(reader, row, rom_sha, frozen, sealed, tools):
    sid = row["id"]
    initial, final, cleanup = (reader.obj(row[key]) for key in ("initial", "final", "cleanup"))
    for record in (initial, final, cleanup):
        _identity(record, sid, rom_sha)
    _need(type(initial.get("schema")) is int and initial["schema"] == 1
          and type(final.get("schema")) is int and final["schema"] == 1, "unsupported session schema")
    _need(initial.get("state") in ("input_verified", "captured", "sealed")
          and final.get("state") == "closed", "initial/final session states required")
    created = _number(initial.get("created_at"), "created_at")
    closed = _number(final.get("closed_at"), "closed_at")
    checked = _number(cleanup.get("checked_at"), "cleanup checked_at")
    _need(frozen <= created < closed <= checked <= sealed, "stale/session/cleanup timeline mismatch")
    _need(final.get("created_at") == created, "session creation changed")
    for role, field in TOOL_FIELDS.items():
        _need(initial.get(field) == tools[role]["sha256"] == final.get(field), f"session tool mismatch: {role}")
    _need(cleanup.get("schema") == "sms_openbor_cleanup_v1", "cleanup schema required")
    processes = _index(cleanup.get("processes"), "role")
    _need(set(processes) == set(PROCESS_ROLES), "cleanup process coverage mismatch")
    for role in PROCESS_ROLES:
        proc = initial.get(role)
        _need(isinstance(proc, dict) and final.get(role) == proc, f"process identity mismatch: {role}")
        _integer(proc.get("pid"), "pid", 1)
        _need(isinstance(proc.get("start_ticks"), str) and proc["start_ticks"].isdigit(), "start_ticks required")
        item = processes[role]
        _need(item.get("pid") == proc["pid"] and item.get("start_ticks") == proc["start_ticks"]
              and item.get("state") == "exited", f"cleanup not proved: {role}")
    if initial.get("audio_sink"):
        _need(final.get("audio_sink") == initial["audio_sink"]
              and cleanup.get("audio_sink") == initial["audio_sink"]
              and cleanup.get("audio_sink_state") == "removed", "private audio sink cleanup missing")
    _, journal_raw = reader.read(row["journal"])
    entries = [_json(line) for line in journal_raw.splitlines() if line.strip()]
    journal, seq, frame, at = {}, -1, -1, created
    for entry in entries:
        ack = entry.get("ack", {})
        _need(isinstance(ack, dict) and ack.get("ok") is True and ack.get("session_id") == sid,
              "journal ACK/session mismatch")
        next_seq = _integer(ack.get("seq"), "journal seq", 1)
        next_frame = _integer(ack.get("frame"), "VDP frame")
        next_at = _number(entry.get("at"), "journal at")
        _need(next_seq > seq and next_frame >= frame and at <= next_at <= closed, "journal order/timeline mismatch")
        _need(entry.get("operation") in {"audio-enable", "audio-disable", "input", "step", "read",
              "status", "sequence", "video", "run", "pause", "capture", "release", "close"},
              "unsupported or mutating journal operation")
        journal[next_seq] = entry
        seq, frame, at = next_seq, next_frame, next_at
    _need(journal, "empty journal")
    return {"initial": initial, "created": created, "closed": closed,
            "journal": journal, "journal_sha256": row["journal"]["sha256"]}


def _png(raw):
    from PIL import Image, ImageStat
    with Image.open(io.BytesIO(raw)) as image:
        _need(image.format == "PNG" and image.size == (256, 192), "native PNG framebuffer required")
        image.verify()
    with Image.open(io.BytesIO(raw)) as image:
        image.load()
        rgb = image.convert("RGB")
        colors = rgb.getcolors(256 * 192)
        _need(colors and len(colors) >= 2 and all(all(c % 85 == 0 for c in color) for _, color in colors),
              "PNG outside SMS palette or uniform")
        _need(ImageStat.Stat(rgb.convert("L")).var[0] >= 40, "uninformative PNG")
    return {"canvas": [256, 192]}


def _run(args):
    result = subprocess.run(args, capture_output=True, timeout=45, check=False)
    _need(result.returncode == 0, f"media decoder rejected file: {args[0]}")
    return result.stdout


def _video(path, meta):
    info = _json(_run(["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-of", "json", str(path)]))
    streams = info.get("streams", [])
    _need(len(streams) == 1 and streams[0].get("codec_type") == "video", "single video stream required")
    stream = streams[0]
    _need((stream.get("width"), stream.get("height")) == (256, 192), "video canvas mismatch")
    count = int(stream.get("nb_read_frames", 0))
    _need(2 <= count <= 600 and count == meta.get("frames"), "video frame count invalid (allowed 2..600)")
    _need(_integer(meta.get("last_frame"), "last_frame") - _integer(meta.get("first_frame"), "first_frame") == count,
          "video VDP window mismatch")
    hashes = meta.get("frame_sha256")
    _need(isinstance(hashes, list) and len(hashes) == count, "video source frame hashes missing")
    for digest in hashes:
        _sha(digest)
    _need(meta.get("distinct_frames") == len(set(hashes)), "video distinct source frames mismatch")
    # FFmpeg 5.1 renamed -vsync to -fps_mode; FFmpeg 9 removed the old spelling.
    # Keep the decoder pinned to one output frame per input frame on both.
    decode = ["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(path),
              "-map", "0:v:0"]
    tail = ["-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"]
    first = subprocess.run(decode + ["-fps_mode", "passthrough"] + tail,
                           capture_output=True, timeout=45, check=False)
    if first.returncode == 0:
        raw = first.stdout
    else:
        legacy = subprocess.run(decode + ["-vsync", "0"] + tail,
                                capture_output=True, timeout=45, check=False)
        _need(legacy.returncode == 0, f"media decoder rejected file: {decode[0]}")
        raw = legacy.stdout
    stride = 256 * 192 * 3
    _need(len(raw) == count * stride, "truncated/invalid decoded video")
    distinct = len({hashlib.sha256(raw[i:i + stride]).digest() for i in range(0, len(raw), stride)})
    _need(distinct > 1 and distinct == meta["distinct_frames"], "frozen video or source/decoded diversity mismatch")
    _need(meta.get("method") == "one native framebuffer per VDP frame; stepped emulation"
          and meta.get("performance") == "not_measured", "unsupported video acquisition scope")
    return {"frames": count, "distinct_frames": distinct}


def _wav(raw, meta, session):
    _need(raw[:4] == b"RIFF" and raw[8:12] == b"WAVE"
          and len(raw) >= 12 and struct.unpack_from("<I", raw, 4)[0] + 8 == len(raw), "invalid WAV RIFF length")
    with wave.open(io.BytesIO(raw), "rb") as wav:
        _need(wav.getnchannels() == 1 and wav.getsampwidth() == 2 and wav.getframerate() == 44100
              and wav.getcomptype() == "NONE", "expected capture_audio PCM16 mono 44100 WAV")
        count = wav.getnframes()
        pcm = wav.readframes(count)
        _need(len(pcm) == count * 2 and count > 0, "truncated WAV data")
    peak = max(abs(x[0]) for x in struct.iter_unpack("<h", pcm))
    seconds = count / 44100
    requested = _number(meta.get("requested_seconds"), "requested_seconds")
    _need(requested > 0 and seconds >= requested * .95 and peak > 0, "short or silent WAV")
    _need(meta.get("samples") == count and meta.get("peak") == peak
          and abs(_number(meta.get("effective_seconds"), "effective_seconds") - seconds) <= .001,
          "WAV statistics mismatch")
    initial = session["initial"]
    route = meta.get("audio_route", {})
    _need(isinstance(route, dict) and meta.get("pid") == initial["emulator_process"]["pid"]
          and route.get("pid") == meta["pid"] and meta.get("sink") == initial.get("audio_sink")
          and route.get("sink") == meta["sink"] and route.get("verified") is True
          and meta.get("moved_sink_inputs") and route.get("sink_inputs") == meta["moved_sink_inputs"],
          "audio PID/private sink binding missing")
    _need(session["created"] <= _number(route.get("at"), "audio route at") <= session["closed"],
          "audio route outside session")
    return {"samples": count, "peak": peak, "seconds": seconds}


def _read_value(session, seq, selector):
    entry = session["journal"].get(_integer(seq, "read seq", 1), {})
    address = _integer(selector.get("address"), "RAM address")
    length = _integer(selector.get("length"), "RAM length", 1)
    _need(0xc000 <= address < address + length <= 0xe000 and length <= 8, "RAM selector out of range")
    _need(entry.get("operation") == "read" and entry.get("args") == [address, length], "missing matching RAM read")
    ram = entry["ack"].get("ram")
    _need(isinstance(ram, list) and len(ram) == length
          and all(type(x) is int and 0 <= x <= 255 for x in ram), "invalid RAM read bytes")
    return int.from_bytes(bytes(ram), "little"), entry["ack"]["frame"]


def _input(case, observation, session, video):
    _need(observation.get("schema") == "sms_openbor_input_observation_v1"
          and observation.get("journal_sha256") == session["journal_sha256"], "input observation/journal binding missing")
    before, frame0 = _read_value(session, observation.get("before_seq"), case["effect_read"])
    consumed, frame1 = _read_value(session, observation.get("consumed_seq"), case["input_read"])
    after, frame2 = _read_value(session, observation.get("after_seq"), case["effect_read"])
    seq = _integer(observation.get("input_seq"), "input seq", 1)
    entry = session["journal"].get(seq, {})
    mask = _integer(case.get("input_mask"), "input_mask", 1)
    _need(mask <= 63 and entry.get("operation") == "input" and isinstance(entry.get("args"), list)
          and len(entry["args"]) == 3, "frame-paced P1 input required")
    p1 = _integer(entry["args"][0], "P1")
    _need(p1 <= 63 and p1 & mask == mask and entry["ack"].get("p1") == p1, "input ACK mask mismatch")
    read_mask = _integer(case["input_read"].get("mask"), "input RAM mask", 1)
    _need(read_mask == mask and consumed & read_mask == mask, "input not observed by ROM")
    _need(observation["before_seq"] < seq < observation["consumed_seq"] <= observation["after_seq"]
          and frame0 <= entry["ack"]["frame"] <= frame1 <= frame2 and frame2 > frame0,
          "input/effect order mismatch")
    _need(video["first_frame"] <= entry["ack"]["frame"] and video["last_frame"] >= frame2,
          "video does not cover input and consequence")
    relation = case.get("relation")
    tests = {"decrease": after < before, "increase": after > before, "change": after != before, "equal": after == before}
    _need(relation in tests and tests[relation], "RAM consequence failed")
    return {"before": before, "after": after, "relation": relation}


def _runtime(metrics, windows, session, region):
    _need(metrics.get("schema") == "runtime_metrics_v1" and metrics.get("region") == region,
          "runtime metrics schema/region mismatch")
    _need(windows.get("schema") == "sms_openbor_runtime_windows_v1"
          and windows.get("journal_sha256") == session["journal_sha256"], "raw runtime windows required")
    header = session["journal"].get(windows.get("header_seq"), {})
    _need(header.get("operation") == "read" and header.get("ack", {}).get("ram", [])[:5] == [83, 77, 82, 84, 2],
          "SMRT v2 ROM header missing")
    rows = windows.get("windows")
    _need(isinstance(rows, list) and len(rows) >= 3, "at least three regional runtime windows required")
    selector = windows["counter"]
    _need(selector.get("length") == 2, "SMRT frame counter must be uint16")
    rates, total, last = [], 0, -1
    for row in rows:
        start, frame0 = _read_value(session, row.get("before_seq"), selector)
        end, frame1 = _read_value(session, row.get("after_seq"), selector)
        bound = _integer(row.get("max_counter_advance"), "max_counter_advance", 1)
        elapsed = _number(row.get("elapsed_seconds"), "elapsed_seconds")
        _need(last < row["before_seq"] < row["after_seq"] and elapsed > 0 and bound < 65536,
              "ambiguous/overlapping runtime counter window")
        operations = [item["operation"] for seq, item in session["journal"].items()
                      if row["before_seq"] < seq < row["after_seq"]]
        _need(operations == ["run", "pause"], "runtime window must use real-time run/pause, never stepping")
        delta = (end - start) % 65536
        _need(0 < delta <= bound and frame1 > frame0, "stopped or ambiguous ROM frame counter")
        rates.append(delta / elapsed)
        total += delta
        last = row["after_seq"]
    target = 60 if region == "NTSC" else 50
    _need(all(abs(rate - target) <= 1 for rate in rates) and max(rates) - min(rates) <= 1,
          "regional runtime means outside tolerance")
    reported = metrics.get("fps_janelas")
    _need(isinstance(reported, list) and len(reported) == len(rates)
          and all(abs(_number(a, "fps window") - b) <= .011 for a, b in zip(reported, rates))
          and metrics.get("frames_delta_total") == total, "reported runtime metrics disagree with raw windows")
    return {"fps_janelas": rates, "frames_delta_total": total, "region": region}


def consume(bundle, current_rom, *, expected_cases=None, expected_scope=None):
    """Fail closed; no caller-supplied approval booleans. Paths are explicit.

    expected_cases is an optional exact set of coordinator-assigned case IDs;
    expected_scope is the exact scope object. Production integration should
    supply both from its trusted assignment, rather than trusting bundle scope.
    No build/validation/memory axis is inferred by this runtime-only adapter.
    """
    report = {"schema": "sms_openbor_evidence_consumption_v1", "axes": dict.fromkeys(AXES, False),
              "axis_scope": SCOPES.copy(), "scope": None, "coverage": {}, "problems": [],
              "eligible": False, "claim_authority": "coordinator",
              "limits": ["record_consistency_not_producer_authentication", "assigned_checks_only",
                         "no_delivery_or_visual_quality_approval", "video_limit_600_frames_per_artifact"]}
    try:
        bundle = Path(bundle)
        reader = _Reader(bundle.parent)
        raw = bundle.read_bytes()
        data = _json(raw)
        report["bundle_sha256"] = hashlib.sha256(raw).hexdigest()
        report["source_schema"] = data.get("schema")
        if data.get("schema") == "sms_evidence_m6_v1":
            checked = []
            for claim in data.get("claims", []):
                if claim.get("artifact") is not None:
                    reader.read(claim["artifact"])
                    checked.append(claim.get("id"))
            report["historical_artifacts_checked"] = checked
            raise EvidenceError("historical M6: immutable ROM, final sessions/cleanup and explicit coverage absent; no automatic promotion")
        _need(data.get("schema") == SCHEMA, "unsupported evidence schema")
        current_rom = Path(current_rom)
        current_sha = hashlib.sha256(current_rom.read_bytes()).hexdigest()
        rom_path, _ = reader.read(data["rom"], immutable=True)
        sha = data["rom"]["sha256"]
        report["rom_sha256"] = sha
        _need(current_sha == sha and not current_rom.samefile(rom_path), "current ROM mismatch or live ROM alias")
        frozen = _number(data["rom"].get("frozen_at"), "frozen_at")
        sealed = _number(data.get("sealed_at"), "sealed_at")
        _need(rom_path.stat().st_mtime <= frozen < sealed, "ROM freeze/seal timeline invalid")
        contract = reader.obj(data["contract"], immutable=True)
        _need(contract.get("schema") == CONTRACT_SCHEMA, "unsupported evidence contract schema")
        scope = contract.get("scope")
        _need(isinstance(scope, dict) and isinstance(scope.get("scene"), str) and scope["scene"].strip()
              and scope.get("region") in ("NTSC", "PAL") and scope.get("claim_ceiling") == "assigned_checks_only",
              "explicit scene/region/claim scope required")
        report["scope"] = scope
        _need(expected_scope is None or scope == expected_scope, "coordinator scope mismatch")
        cases = _index(contract.get("required_cases"), "id")
        _need(expected_cases is None or set(expected_cases) == set(cases), "coordinator required cases mismatch")
        for case in cases.values():
            _need(case.get("axis") in PROOFS and case.get("proof") == PROOFS[case["axis"]], "unsupported axis/proof scope")
        tools = _index(data.get("tools"), "role")
        _need(set(tools) == set(TOOL_FIELDS), "tool snapshot roles mismatch")
        for ref in tools.values():
            reader.read(ref, immutable=True)
        context = _index(data.get("context"), "role")
        _need(set(context) == {"memory_bank", "gdd", "scene_spec", "tdd"}, "context snapshot roles mismatch")
        for ref in context.values():
            _need(reader.read(ref, immutable=True)[1].decode("utf-8").strip(), "empty context snapshot")
        sessions = {sid: _session(reader, row, sha, frozen, sealed, tools)
                    for sid, row in _index(data.get("sessions"), "id").items()}
        artifacts = _index(data.get("artifacts"), "id")
        coverage = _index(data.get("coverage"), "case_id")
        _need(set(coverage) == set(cases), "coverage missing/extra cases")
        checked = {}
        used_paths = set()
        for aid, item in artifacts.items():
            sid = item.get("session_id")
            _need(sid in sessions, "artifact references unknown session")
            session = sessions[sid]
            captured = _number(item.get("captured_at"), "artifact captured_at")
            _need(session["created"] <= captured <= session["closed"], "stale artifact outside session")
            path, content = reader.read(item["file"])
            _need(path not in used_paths and path.stat().st_mtime >= frozen, "reused path or stale artifact file")
            used_paths.add(path)
            kind = item.get("kind")
            meta = reader.obj(item["metadata"])
            _identity(meta, sid, sha)
            if kind in ("png", "video"):
                _need(type(meta.get("schema")) is int and meta["schema"] == 1
                      and meta.get("sha256") == item["file"]["sha256"]
                      and meta.get("canvas") == [256, 192], "capture schema/hash/canvas mismatch")
            if kind == "png":
                _need(meta.get("captured_at") == captured, "capture timestamp mismatch")
                stats = _png(content)
            elif kind == "video":
                stats = _video(path, meta)
            elif kind == "wav":
                _need(meta.get("wav_sha256") == item["file"]["sha256"], "WAV metadata hash mismatch")
                stats = _wav(content, meta, session)
            elif kind in ("input_observation", "runtime_metrics"):
                stats = _json(content)
                _identity(stats, sid, sha)
            else:
                raise EvidenceError(f"unsupported artifact kind: {kind}")
            checked[aid] = {"kind": kind, "session_id": sid, "meta": meta, "stats": stats}
        used = set()
        for cid, case in cases.items():
            ids = coverage[cid].get("artifacts")
            _need(isinstance(ids, list) and ids and len(ids) == len(set(ids))
                  and all(aid in checked for aid in ids), "case artifact coverage missing/duplicate")
            items = [checked[aid] for aid in ids]
            _need(len({item["session_id"] for item in items}) == 1, "case artifacts belong to different sessions")
            kinds = {item["kind"]: item for item in items}
            expected = {"framebuffer": {"png"}, "input_ram_video": {"input_observation", "video"},
                        "regional_runtime_windows": {"runtime_metrics"}, "audio_signal": {"wav"}}[case["proof"]]
            _need(set(kinds) == expected and len(items) == len(expected), "case proof artifacts mismatch")
            session = sessions[items[0]["session_id"]]
            if case["proof"] == "input_ram_video":
                stats = _input(case, kinds["input_observation"]["stats"], session, kinds["video"]["meta"])
            elif case["proof"] == "regional_runtime_windows":
                item = kinds["runtime_metrics"]
                stats = _runtime(item["stats"], item["meta"], session, scope["region"])
            else:
                stats = items[0]["stats"]
            report["coverage"][cid] = {"axis": case["axis"], "proof": case["proof"], "artifacts": ids, "derived": stats}
            used.update(ids)
        _need(used == set(artifacts), "unassigned artifacts in bundle")
        _need({item["session_id"] for item in artifacts.values()} == set(sessions), "unassigned sessions in bundle")
        reader.recheck()
        _need(bundle.read_bytes() == raw and hashlib.sha256(current_rom.read_bytes()).hexdigest() == current_sha,
              "bundle/current ROM changed during consumption")
        for axis in PROOFS:
            report["axes"][axis] = any(case["axis"] == axis for case in cases.values())
        report["eligible"] = True
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ImportError, EOFError,
            struct.error, wave.Error, subprocess.SubprocessError) as exc:
        report["problems"].append(str(exc))
        report["axes"] = dict.fromkeys(AXES, False)
    return report


def axis_support(bundle, current_rom, **kwargs):
    """Scoped tuple API; caller must retain consume()'s scope/coverage report."""
    report = consume(bundle, current_rom, **kwargs)
    reason = "; ".join(report["problems"]) or "no corresponding proof in assigned scope"
    return {axis: (supported, "" if supported else reason) for axis, supported in report["axes"].items()}


def self_check():
    """Run calibrated offline positive/negative fixtures, never an emulator."""
    import unittest
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parents[1] / "tests"),
                                              pattern="test_evidence_consumer.py")
    _need(suite.countTestCases() > 0, "self-check tests missing")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() and not result.skipped else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--current-rom", type=Path)
    parser.add_argument("--expected-case", action="append", help="exact coordinator case IDs (repeat)")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.bundle or not args.current_rom:
        parser.error("--bundle and --current-rom are required")
    report = consume(args.bundle, args.current_rom, expected_cases=args.expected_case)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
