"""Construtor do bundle de evidencia v2 (Lote E / `sms_openbor_evidence_v2`).

Monta o pacote a partir de sessoes privadas reais (manifesto inicial/final,
journal nativo e artefatos nativos) + contrato explicito + snapshots de
ferramentas/contexto. Nunca inventa medicao:

- a observacao de input e as janelas de runtime sao DERIVADAS do journal real
  (reads/input/run/pause) e conferidas contra o `runtime_metrics_v1` do medidor;
- o cleanup so vira registro apos provar por identidade de `start_ticks`
  (/proc) que cada processo morreu e, quando o `pactl` responde, que o sink
  privado sumiu (a propria sessao fechada ja e a prova primaria);
- `config_initial` e materializado como o texto canonico do bridge e aceito
  somente se o sha256 bater com o manifesto da sessao.

A autoridade de validacao e o consumidor (`evidence_consumer.py`); este script
falha fechado antes de entregar um bundle que ele recusaria.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import time
import wave
from pathlib import Path

PROCESS_ROLES = ("supervisor", "xvfb_process", "sandbox", "emulator_process")
TOOL_FIELDS = {"emulator": "emulator_sha256", "bridge": "bridge_sha256",
               "bridge_source": "bridge_source_sha256", "config_initial": "config_initial_sha256"}
CONTEXT_MAP = {"memory_bank": "10-memory-bank.md", "gdd": "11-gdd.md",
               "scene_spec": "13-spec-cenas.md", "tdd": "15-tdd.md"}
CANONICAL_EMULICIOUS_INI = (
    "Update=0\nAudioSync=false\nScale=1\nFrameskip=0\nDisableFrameBlending=true\n"
    "DisableHardwareAcceleration=true\nOpenMostRecentOnStartup=false\n"
    "SMSInputDeviceA=1\nSMSInputDeviceB=1\nScreenshotCropBorders=true\n"
    "SMSGamepadAKeyboard=false\nSMSGamepadBKeyboard=false\nKeyboardRequireWindowFocus=true\n")
BOSS_ADDR, KEYS_ADDR = 0xC7F4, 0xC7F8
HEADER_ADDR, FRAME_ADDR = 0xC7E0, 0xC7F0
INPUT_MASK = 16
SMRT_HEADER = [83, 77, 82, 84, 2]


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path):
    return sha256_bytes(Path(path).read_bytes())


def load_json(path):
    return json.loads(Path(path).read_text())


def save_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")
    return path


def place(src, dst, immutable=False, mtime=None):
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if mtime is not None:
        os.utime(dst, (mtime, mtime))
    if immutable:
        dst.chmod(0o444)
    return dst


def file_ref(root, path, immutable=False):
    path = Path(path)
    if immutable:
        path.chmod(0o444)
    need(path.stat().st_nlink == 1, f"hardlink not allowed: {path}")
    return {"path": str(path.relative_to(root)), "sha256": sha256_file(path),
            "bytes": path.stat().st_size}


def process_identity(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return None


def process_alive(proc):
    return process_identity(proc["pid"]) == proc["start_ticks"] and proc["start_ticks"] is not None


def sink_present(name):
    """True/False quando o pactl responde; None quando indisponivel (nao prova)."""
    try:
        result = subprocess.run(["pactl", "--format=json", "list", "sinks"],
                                capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    try:
        sinks = json.loads(result.stdout)
    except ValueError:
        return None
    return any(item.get("name") == name for item in sinks)


def load_session(directory):
    directory = Path(directory).resolve()
    initial = load_json(directory / "session_initial.json")
    final = load_json(directory / "session_final.json")
    raw = (directory / "commands.jsonl").read_bytes()
    entries = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    sid = initial.get("session_id")
    need(isinstance(sid, str) and sid, "session id missing")
    need(final.get("session_id") == sid, f"{sid}: final session id mismatch")
    need(initial.get("state") in ("input_verified", "captured", "sealed"), f"{sid}: initial state")
    need(final.get("state") == "closed", f"{sid}: final state must be closed")
    created = initial.get("created_at")
    closed = final.get("closed_at")
    need(final.get("created_at") == created, f"{sid}: created_at changed")
    need(isinstance(created, (int, float)) and isinstance(closed, (int, float)) and created < closed,
          f"{sid}: session timeline invalid")
    seq, frame, at = -1, -1, created
    for entry in entries:
        ack = entry.get("ack", {})
        need(ack.get("ok") is True and ack.get("session_id") == sid, f"{sid}: journal ACK/session mismatch")
        next_seq, next_frame, next_at = ack.get("seq"), ack.get("frame"), entry.get("at")
        need(isinstance(next_seq, int) and next_seq > seq, f"{sid}: journal seq order")
        need(isinstance(next_frame, int) and next_frame >= frame, f"{sid}: journal frame order")
        need(isinstance(next_at, (int, float)) and at <= next_at <= closed, f"{sid}: journal at order")
        seq, frame, at = next_seq, next_frame, next_at
    need(entries, f"{sid}: empty journal")
    return {"sid": sid, "dir": directory, "initial": initial, "final": final,
            "created": created, "closed": closed, "entries": entries,
            "journal": {entry["ack"]["seq"]: entry for entry in entries},
            "journal_sha256": sha256_bytes(raw), "rom_sha256": initial.get("rom_sha256")}


def build_cleanup(session, checked_at):
    rows = []
    for role in PROCESS_ROLES:
        proc = session["initial"].get(role)
        need(isinstance(proc, dict) and session["final"].get(role) == proc,
             f"{session['sid']}: process identity mismatch: {role}")
        need(isinstance(proc.get("pid"), int) and proc["pid"] >= 1, f"{role}: pid")
        need(isinstance(proc.get("start_ticks"), str) and proc["start_ticks"].isdigit(),
             f"{role}: start_ticks")
        need(not process_alive(proc), f"{session['sid']}: {role} pid={proc['pid']} still alive")
        rows.append({"role": role, "pid": proc["pid"], "start_ticks": proc["start_ticks"],
                     "state": "exited"})
    record = {"schema": "sms_openbor_cleanup_v1", "session_id": session["sid"],
              "rom_sha256": session["rom_sha256"], "checked_at": checked_at, "processes": rows}
    sink = session["initial"].get("audio_sink")
    if sink:
        need(session["final"].get("audio_sink") == sink, f"{session['sid']}: audio sink changed")
        state = sink_present(sink)
        need(state is not True, f"{session['sid']}: private sink still present: {sink}")
        record["audio_sink"] = sink
        record["audio_sink_state"] = "removed"
    return record


def derive_gameplay(session):
    entries = session["entries"]
    boss = [e for e in entries if e["operation"] == "read" and e["args"] == [BOSS_ADDR, 1]]
    keys = [e for e in entries if e["operation"] == "read" and e["args"] == [KEYS_ADDR, 1]]
    inputs = [e for e in entries if e["operation"] == "input"
              and isinstance(e.get("args"), list) and len(e["args"]) == 3
              and e["args"][0] & INPUT_MASK == INPUT_MASK]
    videos = [e for e in entries if e["operation"] == "video"]
    need(len(inputs) == 1 and len(videos) == 1, f"{session['sid']}: one input and one video op required")
    input_e, video_e = inputs[0], videos[0]
    need(input_e["args"][0] == INPUT_MASK and input_e["ack"].get("p1") == INPUT_MASK,
         f"{session['sid']}: input ACK mask")
    before = max((e for e in boss if e["ack"]["seq"] < input_e["ack"]["seq"]),
                 key=lambda e: e["ack"]["seq"])
    after = min((e for e in boss if e["ack"]["seq"] > input_e["ack"]["seq"]),
                key=lambda e: e["ack"]["seq"])
    consumed = min((e for e in keys if e["ack"]["seq"] > input_e["ack"]["seq"]),
                   key=lambda e: e["ack"]["seq"])
    seqs = (before["ack"]["seq"], input_e["ack"]["seq"], consumed["ack"]["seq"], after["ack"]["seq"])
    need(seqs[0] < seqs[1] < seqs[2] <= seqs[3], f"{session['sid']}: observation order")
    frames = (before["ack"]["frame"], input_e["ack"]["frame"],
              consumed["ack"]["frame"], after["ack"]["frame"])
    need(frames[0] <= frames[1] <= frames[2] <= frames[3] and frames[3] > frames[0],
         f"{session['sid']}: observation frame order")
    value_before, value_consumed, value_after = (entry["ack"]["ram"][0]
                                                 for entry in (before, consumed, after))
    need(value_consumed & INPUT_MASK == INPUT_MASK, f"{session['sid']}: ROM did not observe the input")
    need(value_after < value_before, f"{session['sid']}: no RAM consequence")
    observation = {"schema": "sms_openbor_input_observation_v1", "session_id": session["sid"],
                   "rom_sha256": session["rom_sha256"], "journal_sha256": session["journal_sha256"],
                   "input_mask": INPUT_MASK, "before_seq": seqs[0], "input_seq": seqs[1],
                   "consumed_seq": seqs[2], "after_seq": seqs[3], "before": value_before,
                   "consumed": value_consumed, "after": value_after}
    return observation, video_e, after["at"]


def check_video(session, directory):
    record = load_json(Path(directory) / "o3_gameplay.json")
    media = Path(directory) / "o3_gameplay.mp4"
    need(record.get("schema") == 1 and record.get("sha256") == sha256_file(media),
         f"{session['sid']}: video schema/hash")
    need(record.get("session_id") == session["sid"] and record.get("rom_sha256") == session["rom_sha256"],
         f"{session['sid']}: video identity")
    count = record.get("frames")
    hashes = record.get("frame_sha256")
    need(isinstance(count, int) and 2 <= count <= 600 and isinstance(hashes, list) and len(hashes) == count,
         f"{session['sid']}: video frame count/hashes")
    need(record.get("distinct_frames") == len(set(hashes)), f"{session['sid']}: video distinct frames")
    need(record.get("last_frame", 0) - record.get("first_frame", -1) == count,
         f"{session['sid']}: video VDP window")
    need(record.get("canvas") == [256, 192], f"{session['sid']}: video canvas")
    need(record.get("method") == "one native framebuffer per VDP frame; stepped emulation"
         and record.get("performance") == "not_measured", f"{session['sid']}: video acquisition scope")
    return record


def check_png(session, directory):
    record = load_json(Path(directory) / "o3_boot.json")
    need(record.get("schema") == 1 and record.get("sha256") == sha256_file(Path(directory) / "o3_boot.png"),
         f"{session['sid']}: png schema/hash")
    need(record.get("session_id") == session["sid"] and record.get("rom_sha256") == session["rom_sha256"],
         f"{session['sid']}: png identity")
    need(record.get("canvas") == [256, 192], f"{session['sid']}: png canvas")
    need(isinstance(record.get("captured_at"), (int, float)), f"{session['sid']}: png captured_at")
    return record


def derive_windows(session):
    entries = session["entries"]
    headers = [e for e in entries if e["operation"] == "read" and e["args"] == [HEADER_ADDR, 5]
               and e["ack"]["ram"][:5] == SMRT_HEADER]
    need(headers, f"{session['sid']}: SMRT v2 header read missing")
    reads = [e for e in entries if e["operation"] == "read" and e["args"] == [FRAME_ADDR, 2]]
    windows, rates, total, last = [], [], 0, -1
    for current, nxt in zip(reads, reads[1:]):
        b_seq, a_seq = current["ack"]["seq"], nxt["ack"]["seq"]
        between = [e for e in entries if b_seq < e["ack"]["seq"] < a_seq]
        if [e["operation"] for e in between] != ["run", "pause"]:
            continue
        need(last < b_seq, f"{session['sid']}: overlapping runtime windows")
        # Espelho do relogio conservador do medidor: t0 logo apos ler o
        # contador, t1 apos o ack do pause; ambos presos ao journal real.
        elapsed = between[1]["at"] - current["at"]
        need(elapsed > 0, f"{session['sid']}: nonpositive window")
        start = int.from_bytes(bytes(current["ack"]["ram"]), "little")
        end = int.from_bytes(bytes(nxt["ack"]["ram"]), "little")
        delta = (end - start) % 65536
        need(0 < delta and nxt["ack"]["frame"] > current["ack"]["frame"],
             f"{session['sid']}: stopped/ambiguous counter")
        windows.append({"before_seq": b_seq, "after_seq": a_seq,
                        "elapsed_seconds": elapsed, "max_counter_advance": delta})
        rates.append(delta / elapsed)
        total += delta
        last = a_seq
    need(len(windows) >= 3, f"{session['sid']}: at least three runtime windows required")
    return headers[0]["ack"]["seq"], windows, rates, total, reads[-1]["at"]


def check_audio(session, directory):
    directory = Path(directory)
    meta = load_json(directory / "audio_attack.audio.json")
    wav_path = directory / "audio_attack.wav"
    raw = wav_path.read_bytes()
    need(raw[:4] == b"RIFF" and raw[8:12] == b"WAVE" and struct.unpack_from("<I", raw, 4)[0] + 8 == len(raw),
         f"{session['sid']}: invalid WAV RIFF length")
    need(meta.get("wav_sha256") == sha256_bytes(raw) and meta.get("session_id") == session["sid"]
         and meta.get("rom_sha256") == session["rom_sha256"], f"{session['sid']}: WAV metadata hash/identity")
    route = meta.get("audio_route") or {}
    pid = session["initial"]["emulator_process"]["pid"]
    sink = session["initial"].get("audio_sink")
    need(meta.get("pid") == pid and route.get("pid") == pid, f"{session['sid']}: audio PID binding")
    need(meta.get("sink") == sink == route.get("sink"), f"{session['sid']}: audio sink binding")
    need(route.get("verified") is True and meta.get("moved_sink_inputs")
         and route.get("sink_inputs") == meta["moved_sink_inputs"], f"{session['sid']}: audio route proof")
    need(session["created"] <= route.get("at") <= session["closed"], f"{session['sid']}: audio route timeline")
    with wave.open(str(wav_path), "rb") as wav:
        need(wav.getnchannels() == 1 and wav.getsampwidth() == 2 and wav.getframerate() == 44100
             and wav.getcomptype() == "NONE", f"{session['sid']}: WAV format")
        count = wav.getnframes()
        pcm = wav.readframes(count)
    peak = max(abs(item[0]) for item in struct.iter_unpack("<h", pcm))
    seconds = count / 44100
    need(meta.get("samples") == count and meta.get("peak") == peak
         and abs(meta.get("effective_seconds", -1) - seconds) <= .001, f"{session['sid']}: WAV statistics")
    need(meta.get("requested_seconds", 0) > 0 and seconds >= meta["requested_seconds"] * .95 and peak > 0,
         f"{session['sid']}: short or silent WAV")
    return meta


def build(rom_path, out_dir, gameplay_dir, mrp_dir, audio_dir, docs_dir,
          emulator_jar, bridge_jar, bridge_source, scene, sealed_at=None):
    rom_path, out_dir = Path(rom_path).resolve(), Path(out_dir).resolve()
    need(rom_path.suffix.lower() == ".sms" and rom_path.is_file(), "existing .sms ROM required")
    need(not out_dir.exists(), f"refusing to overwrite existing bundle: {out_dir}")
    rom_sha = sha256_file(rom_path)
    frozen = rom_path.stat().st_mtime
    gameplay, mrp, audio = (load_session(directory) for directory in (gameplay_dir, mrp_dir, audio_dir))
    for session in (gameplay, mrp, audio):
        need(session["rom_sha256"] == rom_sha, f"{session['sid']}: ROM mismatch")
        need(frozen <= session["created"], f"{session['sid']}: ROM frozen after session creation")
    tools = {"emulator": Path(emulator_jar).resolve(), "bridge": Path(bridge_jar).resolve(),
             "bridge_source": Path(bridge_source).resolve(),
             "config_initial": sha256_bytes(CANONICAL_EMULICIOUS_INI.encode())}
    for role in ("emulator", "bridge", "bridge_source"):
        digest = sha256_file(tools[role])
        for session in (gameplay, mrp, audio):
            field = TOOL_FIELDS[role]
            need(session["initial"].get(field) == digest == session["final"].get(field),
                 f"{session['sid']}: tool identity mismatch: {role}")
    for session in (gameplay, mrp, audio):
        need(session["initial"].get(TOOL_FIELDS["config_initial"]) == tools["config_initial"],
             f"{session['sid']}: config_initial canonical text mismatch")
    checked = time.time()
    need(all(session["closed"] <= checked for session in (gameplay, mrp, audio)), "session not closed yet")
    cleanups = {session["sid"]: build_cleanup(session, checked) for session in (gameplay, mrp, audio)}
    observation, video_entry, observation_at = derive_gameplay(gameplay)
    video = check_video(gameplay, gameplay_dir)
    png = check_png(gameplay, gameplay_dir)
    need(video["first_frame"] <= video_entry["ack"]["frame"], "video does not cover input")
    need(video["last_frame"] >= gameplay["journal"][observation["after_seq"]]["ack"]["frame"],
         "video does not cover consequence")
    metrics = load_json(Path(mrp_dir) / "runtime_metrics.json")
    need(metrics.get("schema") == "runtime_metrics_v1" and metrics.get("region") == "NTSC"
         and metrics.get("session_id") == mrp["sid"] and metrics.get("rom_sha256") == rom_sha,
         "runtime metrics schema/identity")
    header_seq, windows, rates, total, metrics_at = derive_windows(mrp)
    reported = metrics.get("fps_janelas")
    need(isinstance(reported, list) and len(reported) == len(rates)
         and all(abs(a - b) <= .011 for a, b in zip(reported, rates))
         and metrics.get("frames_delta_total") == total,
         f"reported runtime metrics disagree with raw windows: {reported} vs {[round(r, 4) for r in rates]}")
    need(all(abs(rate - 60) <= 1 for rate in rates) and max(rates) - min(rates) <= 1,
         "regional runtime means outside tolerance")
    audio_meta = check_audio(audio, audio_dir)
    windows_doc = {"schema": "sms_openbor_runtime_windows_v1", "session_id": mrp["sid"],
                   "rom_sha256": rom_sha, "journal_sha256": mrp["journal_sha256"],
                   "header_seq": header_seq, "counter": {"address": FRAME_ADDR, "length": 2},
                   "windows": windows}
    contract = {"schema": "sms_openbor_evidence_contract_v1",
                "scope": {"scene": scene, "region": "NTSC", "claim_ceiling": "assigned_checks_only"},
                "required_cases": [
                    {"id": "boot_emulador", "axis": "boot_emulador", "proof": "framebuffer",
                     "note": "informative native framebuffer only"},
                    {"id": "gameplay", "axis": "gameplay", "proof": "input_ram_video",
                     "input_mask": INPUT_MASK,
                     "input_read": {"address": KEYS_ADDR, "length": 1, "mask": INPUT_MASK},
                     "effect_read": {"address": BOSS_ADDR, "length": 1}, "relation": "decrease"},
                    {"id": "fps_constante", "axis": "fps_constante", "proof": "regional_runtime_windows"},
                    {"id": "audio", "axis": "audio", "proof": "audio_signal"}]}
    for name, captured in (("png", png["captured_at"]), ("observation", observation_at),
                           ("video", video_entry["at"]), ("metrics", metrics_at),
                           ("audio", audio_meta["audio_route"]["at"])):
        session = gameplay if name in ("png", "observation", "video") else (mrp if name == "metrics" else audio)
        need(session["created"] <= captured <= session["closed"], f"{name}: captured_at outside session")
    out_dir.mkdir(parents=True)
    root = out_dir
    sessions_dir = root / "sessions"
    session_rows = []
    for session in (gameplay, mrp, audio):
        target = sessions_dir / session["sid"]
        target.mkdir(parents=True)
        initial = place(session["dir"] / "session_initial.json", target / "initial.json")
        final = place(session["dir"] / "session_final.json", target / "final.json")
        journal = place(session["dir"] / "commands.jsonl", target / "journal.jsonl")
        cleanup = save_json(target / "cleanup.json", cleanups[session["sid"]])
        session_rows.append({"id": session["sid"], "initial": file_ref(root, initial),
                             "final": file_ref(root, final), "journal": file_ref(root, journal),
                             "cleanup": file_ref(root, cleanup)})
    artifacts_dir = root / "artifacts"
    boot_png = place(Path(gameplay_dir) / "o3_boot.png", artifacts_dir / "boot_png.png")
    boot_meta = place(Path(gameplay_dir) / "o3_boot.json", artifacts_dir / "boot_png.json")
    observation_path = save_json(artifacts_dir / "gameplay_observation.json", observation)
    gameplay_video = place(Path(gameplay_dir) / "o3_gameplay.mp4", artifacts_dir / "gameplay_video.mp4")
    video_meta = place(Path(gameplay_dir) / "o3_gameplay.json", artifacts_dir / "gameplay_video.json")
    metrics_path = place(Path(mrp_dir) / "runtime_metrics.json", artifacts_dir / "fps_metrics.json")
    windows_path = save_json(artifacts_dir / "fps_windows.json", windows_doc)
    audio_wav = place(Path(audio_dir) / "audio_attack.wav", artifacts_dir / "audio_signal.wav")
    audio_meta_path = place(Path(audio_dir) / "audio_attack.audio.json", artifacts_dir / "audio_signal.json")
    artifacts = [
        {"id": "boot_png", "kind": "png", "session_id": gameplay["sid"], "captured_at": png["captured_at"],
         "file": file_ref(root, boot_png), "metadata": file_ref(root, boot_meta)},
        {"id": "gameplay_observation", "kind": "input_observation", "session_id": gameplay["sid"],
         "captured_at": observation_at, "file": file_ref(root, observation_path),
         "metadata": file_ref(root, observation_path)},
        {"id": "gameplay_video", "kind": "video", "session_id": gameplay["sid"],
         "captured_at": video_entry["at"], "file": file_ref(root, gameplay_video),
         "metadata": file_ref(root, video_meta)},
        {"id": "fps_metrics", "kind": "runtime_metrics", "session_id": mrp["sid"],
         "captured_at": metrics_at, "file": file_ref(root, metrics_path),
         "metadata": file_ref(root, windows_path)},
        {"id": "audio_signal", "kind": "wav", "session_id": audio["sid"],
         "captured_at": audio_meta["audio_route"]["at"], "file": file_ref(root, audio_wav),
         "metadata": file_ref(root, audio_meta_path)},
    ]
    coverage = [{"case_id": "boot_emulador", "artifacts": ["boot_png"]},
                {"case_id": "gameplay", "artifacts": ["gameplay_observation", "gameplay_video"]},
                {"case_id": "fps_constante", "artifacts": ["fps_metrics"]},
                {"case_id": "audio", "artifacts": ["audio_signal"]}]
    inputs = root / "inputs"
    rom_copy = place(rom_path, inputs / "rom.sms", mtime=frozen)
    contract_path = save_json(inputs / "contract.json", contract)
    tools_rows = []
    tool_names = {"emulator": "emulator.jar", "bridge": "bridge.jar",
                  "bridge_source": "bridge_source.java"}
    for role, filename in tool_names.items():
        tool_copy = place(tools[role], inputs / "tools" / filename, immutable=True)
        tools_rows.append({"role": role, **file_ref(root, tool_copy, immutable=True)})
    config_path = inputs / "tools" / "config_initial.ini"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_bytes(CANONICAL_EMULICIOUS_INI.encode())
    tools_rows.append({"role": "config_initial", **file_ref(root, config_path, immutable=True)})
    context_rows = []
    for role, filename in CONTEXT_MAP.items():
        source = Path(docs_dir) / filename
        need(source.is_file(), f"context doc missing: {source}")
        context_copy = place(source, inputs / "context" / filename, immutable=True)
        context_rows.append({"role": role, **file_ref(root, context_copy, immutable=True)})
    sealed = time.time() if sealed_at is None else float(sealed_at)
    need(max(session["closed"] for session in (gameplay, mrp, audio)) <= checked <= sealed,
         "seal timeline invalid")
    bundle = {"schema": "sms_openbor_evidence_v2",
              "rom": {**file_ref(root, rom_copy, immutable=True), "frozen_at": frozen},
              "sealed_at": sealed,
              "contract": file_ref(root, contract_path, immutable=True),
              "tools": tools_rows, "context": context_rows,
              "sessions": session_rows, "artifacts": artifacts, "coverage": coverage}
    bundle_path = save_json(root / "bundle.json", bundle)
    return bundle_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--gameplay-dir", required=True)
    parser.add_argument("--mrp-dir", required=True)
    parser.add_argument("--audio-dir", required=True)
    parser.add_argument("--docs-dir", required=True)
    parser.add_argument("--emulator-jar", required=True)
    parser.add_argument("--bridge-jar", required=True)
    parser.add_argument("--bridge-source", required=True)
    parser.add_argument("--scene", default="TOWN1")
    parser.add_argument("--sealed-at", type=float, default=None)
    args = parser.parse_args(argv)
    bundle = build(args.rom, args.out, args.gameplay_dir, args.mrp_dir, args.audio_dir,
                   args.docs_dir, args.emulator_jar, args.bridge_jar, args.bridge_source,
                   args.scene, args.sealed_at)
    print(json.dumps({"bundle": str(bundle), "sha256": sha256_file(bundle)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
