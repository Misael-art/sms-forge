"""Replay one case against both preserved Scene 02 pilots in serial."""
import argparse
import json
from pathlib import Path
from subprocess import SubprocessError
import sys
import time

from duel_probe import RECORD_BYTES, decode
from replay_duel_scene02 import CASES, replay


PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent.parent
PILOTS = (
    (6, "scene02_hold6_20261119_b02", "c1f08ccc607faf5656520e272288185569cdd63aa6da267987c3bd6f36084bc8"),
    (8, "scene02_hold8_20261119_b01", "d42ce2b4a61b60212ec619b13a3a7ca982c0015b1892e245b3696a69edf0af0d"),
)


def measure_cadence(session, directory):
    from measure_runtime_probe import _session, load_schema, schema_path, self_check
    from session_bridge import isolated

    if self_check() not in (None, 0):
        raise RuntimeError("The canonical SMRT tool did not pass its self-check")
    root, metadata = isolated.load(session)

    class CadenceReader(isolated.MemoryReader):
        first_frame = None
        began = None

        def __init__(self, root):
            super().__init__(root)
            self.windows = []

        def cont(self):
            ack = super().cont()
            self.first_frame = ack["frame"]
            self.began = time.monotonic()
            return ack

        def pause(self):
            ack = super().pause()
            if self.first_frame is not None:
                elapsed = time.monotonic() - self.began
                delta = ack["frame"] - self.first_frame
                self.windows.append({"vdp_frames": delta, "ack_elapsed_s": elapsed,
                                     "vdp_per_second": delta / elapsed})
                self.first_frame = None
            return ack

    reader = CadenceReader(root)
    code, _ = _session(
        reader, str(root / "emulator/rom.sms"), str(directory),
        "cadence", 12.0, 2, "Emulicious.jar", load_schema(schema_path()),
        private_meta=metadata,
    )
    report = json.loads((directory / "cadence.json").read_bytes())
    (directory / "host-vdp-windows.json").write_text(json.dumps({
        "session_id": metadata["session_id"], "rom_sha256": metadata["rom_sha256"],
        "windows": reader.windows,
    }, indent=2) + "\n", encoding="utf-8")
    vblank = isolated.request(root, "read", 0xC7EA, 8)["ram"]
    return code, report, {
        "last_vline": vblank[0], "vblank_overruns": vblank[1] | vblank[2] << 8,
        "phase": vblank[3], "presented_frames": vblank[6] | vblank[7] << 8,
    }


def compare(case, directory, ecj=None, hold_only=None, cadence=False, candidate=None,
            repertoire_round=False, bank_dir=None, impact_only=False, actions_round=False,
            realtime_trace=None, after_walks=False):
    sys.path.insert(0, str(WORKSPACE / "tools/sms_wrapper"))
    from session_bridge import isolated

    directory.mkdir(parents=True, exist_ok=False)
    results = []
    inputs = [(hold_only, candidate.resolve(), isolated.sha(candidate))] if candidate else [
        (hold, PROJECT / "out/candidates" / name / "rom/master_of_fighters.sms", digest)
        for hold, name, digest in PILOTS if hold_only is None or hold_only == hold
    ]
    with isolated.performance_reservation(), isolated.project_reservation(PROJECT):
        for hold, rom, expected_sha in inputs:
            row = {"hold": hold, "rom": str(rom), "sha256": expected_sha}
            session = None
            try:
                if (not candidate and rom.stat().st_size != 32768) or isolated.sha(rom) != expected_sha:
                    raise ValueError("ROM size or SHA mismatch")
                if repertoire_round or impact_only or realtime_trace:
                    from bind_scene02_repertoire import DIAGNOSTICS, verify_rom
                    row["mapper"] = verify_rom(rom, bank_dir or DIAGNOSTICS / "scene02-repertoire-banks-b02")
                session = isolated.start(rom, ecj=ecj, ttl=900)
                row["session_id"] = session.name
                for _ in range(12):
                    sample = isolated.request(session, "read", 0xC770, RECORD_BYTES)
                    try:
                        decode(bytes(sample["ram"]))
                        break
                    except ValueError:
                        isolated.request(session, "step", 1)
                else:
                    raise RuntimeError("MFD1 did not publish a stable boot record")
                if cadence and not realtime_trace:
                    report_dir = directory / str(hold)
                    report_dir.mkdir()
                    code, _, row["vblank_snapshot"] = measure_cadence(session, report_dir)
                    row["cadence_verdict"] = "smrt_window_passed" if code == 0 else "smrt_window_failed"
                    row["trace"] = str(report_dir.relative_to(directory) / "cadence.json")
                if realtime_trace:
                    from replay_duel_round import record_replay
                    summary = record_replay(session, realtime_trace, directory / f"{hold}-continuous")
                    row["round"] = f"{hold}-continuous/round-continuo.json"
                    if cadence:
                        row["cadence_verdict"] = ("fight_window_passed" if summary["cadence"]["passed"]
                                                  else "fight_window_failed")
                    row["verdict"] = "continuous_round_captured" if summary["same_contacts"] and (
                        summary["knockout"]) else "continuous_round_diverged"
                elif repertoire_round or impact_only:
                    from record_duel_repertoire import record_round
                    round_dir = directory / f"{hold}-round"
                    summary = record_round(session, round_dir, hold, impact_only=impact_only,
                                           actions_round=actions_round, after_walks=after_walks)
                    if impact_only:
                        row["round"] = str(round_dir.relative_to(directory) / "impacto-soco.json")
                        punch = summary["moves"][0]
                        sync = punch["requested_at_hit"] == punch["presented_at_hit"] == 8
                        if after_walks:
                            row["walks_complete"] = len(summary["walks"]) == 4 and all(
                                walk["displayed"] == walk["requested_frames"] for walk in summary["walks"]
                            )
                        row["verdict"] = "impact_synchronized" if sync and not (
                            summary["overruns"] or summary["renderer_fault"]
                        ) else "impact_failed"
                        row["punch"] = punch
                    else:
                        row["round"] = str(round_dir.relative_to(directory) / "round-completo.json")
                        row["verdict"] = "round_recorded" if not (
                            summary["logic_gaps_other_than_one_vdp"] or summary["delayed_presentations"] or
                            summary["renderer_fault"] or summary["overruns"] or summary["missed_vblank_epochs"] or
                            summary["min_vline"] < 0xC0
                        ) else "round_recorded_renderer_failed"
                elif cadence:
                    row["verdict"] = row["cadence_verdict"]
                else:
                    out = directory / f"{hold}-{case}.json"
                    row["verdict"] = replay(session.name, expected_sha, hold, case, out, True)
                    row["trace"] = out.name
            except (AssertionError, RuntimeError, ValueError, OSError, SubprocessError) as exc:
                row["verdict"] = "failed"
                row["error"] = str(exc)
                candidate_trace = directory / f"{hold}-{case}.json"
                if candidate_trace.is_file():
                    row["trace"] = candidate_trace.name
            finally:
                if session is not None:
                    isolated.close_session(session)
                    _, closed = isolated.load(session)
                    row["closed"] = closed["state"] == "closed"
                    (directory / f"{hold}-closed-session.json").write_text(
                        json.dumps(closed, indent=2) + "\n", encoding="utf-8")
            results.append(row)
    (directory / "comparison.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    expected = "continuous_round_captured" if realtime_trace else (
        "impact_synchronized" if impact_only else "round_recorded" if repertoire_round else (
        "smrt_window_passed" if cadence else "stepped_semantics_passed")
    )
    cadence_pass = "fight_window_passed" if realtime_trace else "smrt_window_passed"
    return all(row["verdict"] == expected and row.get("closed") and row.get("walks_complete", True) and
               (not cadence or row.get("cadence_verdict") == cadence_pass) for row in results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, default="guard_counter")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ecj", type=Path)
    parser.add_argument("--hold", type=int, choices=(6, 8))
    parser.add_argument("--realtime-cadence", action="store_true")
    recording = parser.add_mutually_exclusive_group()
    recording.add_argument("--repertoire-round", action="store_true")
    recording.add_argument("--impact-only", action="store_true", help="Replay the archived first Hayato punch")
    parser.add_argument("--after-walks", action="store_true", help="Run the four walk cycles before the impact probe")
    recording.add_argument("--actions-round", action="store_true", help="Capture eight normals, four walks and two specials")
    recording.add_argument("--realtime-from-trace", type=Path, help="Replay a same-ROM trace in a fresh continuous audio/video session")
    parser.add_argument("--candidate", type=Path, help="Optional new ROM, bound to the supplied hold")
    parser.add_argument("--bank-dir", type=Path, help="Art bank receipt to match in a repertoire ROM")
    args = parser.parse_args()
    if args.after_walks and not args.impact_only:
        parser.error("--after-walks requires --impact-only")
    if args.candidate and args.hold is None:
        parser.error("--candidate requires --hold")
    if (args.repertoire_round or args.impact_only or args.actions_round or args.realtime_from_trace) and not args.candidate:
        parser.error("repertoire evidence requires --candidate")
    raise SystemExit(0 if compare(args.case, args.out, args.ecj, args.hold,
                                  args.realtime_cadence, args.candidate,
                                  args.repertoire_round or args.actions_round, args.bank_dir,
                                  args.impact_only, args.actions_round, args.realtime_from_trace,
                                  args.after_walks) else 1)
