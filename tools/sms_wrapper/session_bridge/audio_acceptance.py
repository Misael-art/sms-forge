"""Real emulator checks for muted boot, stable private route and PCM duration.

Only session-private monitors are read. Never records the host default sink.
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import shutil
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from session_bridge import isolated as iso
from session_bridge.acceptance import build_probes
from capture_audio import capture_session, record_private_pcm, write_wav, _peak, RATE, _self_check

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rom", help="known audible SMS ROM")
    p.add_argument("--out")
    p.add_argument("--self-check", action="store_true")
    a = p.parse_args()
    if a.self_check:
        iso.self_check(); _self_check(); return
    if not a.rom or not a.out: p.error("--rom and --out required for emulator acceptance")
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    silent_rom = build_probes(out / "roms")[0]
    sessions = []
    result = {"status": "fail", "scope": "private audio routing and signal only", "checks": {}, "sessions": []}
    try:
        audible = iso.start(a.rom, enable_audio=False); sessions.append(audible)
        silent = iso.start(silent_rom); sessions.append(silent)
        root, meta = iso.load(audible)
        assert meta["audio_boot"]["muted_from_launch"] and not meta["ready"]["audio_enabled"]
        assert not iso.request(root, "status")["audio_enabled"]
        assert iso.verify_audio_route(meta)
        assert capture_session(root, 1, "muted_refused") == 2
        iso.request(root, "run")
        pcm = record_private_pcm(meta["audio_sink"], 2)
        iso.request(root, "pause")
        assert len(pcm) >= 2 * RATE * 2 * 0.95 and _peak(pcm) == 0
        write_wav(str(out / "muted_boot.wav"), pcm)
        result["muted_pcm"] = {"seconds": len(pcm)/2/RATE, "peak": _peak(pcm),
                                "sha256": iso.sha(out/"muted_boot.wav")}
        result["checks"]["boot_muted_and_nonzero_ROM_samples_blocked"] = "pass"
        result["checks"]["muted_capture_refused"] = "pass"
        # Unrouted activation is rejected by the coordinator, even with credentials.
        original = dict(meta)
        meta["audio_route"] = None; iso.atomic(root/"session.json", meta)
        try:
            try: iso.request(root, "audio-enable")
            except RuntimeError: pass
            else: raise AssertionError("unrouted audio activation accepted")
        finally: iso.atomic(root/"session.json", original)
        assert iso.request(root, "audio-enable")["audio_enabled"]
        result["checks"]["unrouted_activation_rejected"] = "pass"
        route = iso.load(root)[1]["audio_route"]
        for _ in range(5):
            iso.request(root, "step", 2)
            assert iso.verify_audio_route(iso.load(root)[1], route["sink_inputs"])
            time.sleep(1)
        time.sleep(3)
        assert iso.verify_audio_route(iso.load(root)[1], route["sink_inputs"])
        result["checks"]["pause_step_unmute_preserve_stream_identity"] = "pass"
        # Change the expected private sink contract without moving any stream.
        # A physical move is not a deterministic negative fixture here: host
        # policy can restore it before readback. Actual membership must disagree
        # with this tampered contract, then advancement must refuse it.
        iso.request(root, "audio-disable")
        alternate = iso.load(silent)[1]["audio_sink"]
        original_route_meta = iso.load(root)[1]
        changed = dict(original_route_meta); changed["audio_sink"] = alternate
        iso.atomic(root/"session.json", changed)
        assert not iso.verify_audio_route(changed)
        before = iso.request(root, "status")["frame"]
        try:
            try: iso.request(root, "step", 1)
            except RuntimeError: pass
            else: raise AssertionError("tampered sink contract accepted advancement")
            assert iso.request(root, "status")["frame"] == before
        finally:
            iso.atomic(root/"session.json", original_route_meta)
        iso.request(root, "audio-enable")
        result["checks"]["tampered_sink_contract_refuses_frame_advance"] = "pass"
        with concurrent.futures.ThreadPoolExecutor() as pool:
            jobs = [pool.submit(capture_session, s, 8, "audio_acceptance") for s in sessions]
            assert [j.result() for j in jobs] == [0, 1]  # silent control must fail signal gate
        for s in sessions:
            _, m = iso.load(s)
            rec = json.loads((s/"audio_acceptance.audio.json").read_text())
            assert rec["effective_seconds"] >= 7.6
            assert iso.verify_audio_route(m, m["audio_route"]["sink_inputs"])
            dst = out / s.name; dst.mkdir()
            for name in ["audio_acceptance.wav", "audio_acceptance.audio.json", "session.json", "ready.json", "commands.jsonl"]:
                shutil.copy2(s/name, dst/name)
            shutil.copy2(s/"emulator/ForgeSMS.java", dst/"ForgeSMS.java")
            shutil.copy2(s/"emulator/bridge.jar", dst/"bridge.jar")
            result["sessions"].append({"id": s.name, "rom_sha256": m["rom_sha256"],
                                      "bridge_sha256": m["bridge_sha256"], "audio": rec})
        result["checks"]["parallel_audible_and_silent_ROMs_private_monitors"] = "pass"
        result["checks"]["effective_duration_at_least_95_percent"] = "pass"
        iso.close_session(audible); sessions.remove(audible)
        assert iso.request(silent, "status")["ok"]
        iso.close_session(silent); sessions.remove(silent)
        result["checks"]["owned_cleanup_removes_sink_preserves_other_session"] = "pass"
        result["status"] = "pass"
    except Exception as e:
        result["error"] = str(e)
        raise
    finally:
        for s in sessions:
            try: iso.close_session(s)
            except (RuntimeError, OSError): pass
        result["script_sha256"] = iso.sha(__file__)
        iso.atomic(out/"audio_acceptance.json", result)
    print(json.dumps(result, indent=2))

if __name__ == "__main__": main()
