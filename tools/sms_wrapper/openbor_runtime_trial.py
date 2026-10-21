"""Comparable frame-paced OpenBOR trials. Sequence/imagery, never real-time FPS.

Reads the actual actor layout supplied by the caller; no RAM writes. Each run
owns a private Emulicious session and preserves both initial/final manifests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

from session_bridge import isolated as iso


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n")


def run(rom, out, ticks=180, boot=280, player=0xC000, enemy=0xC030,
        actor_size=48, frames=False, script=None, service=0, service_size=20):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    rom = Path(rom).resolve()
    shutil.copy2(rom, out / "rom.sms")
    shutil.copy2(__file__, out / "trial_source.py")
    root = iso.start(out / "rom.sms")
    root, initial = iso.load(root)
    sid = initial["session_id"]
    save(out / "session_initial.json", initial)
    trace = []
    try:
        iso.sequence(sid, [{"frames": boot}])
        plan = script or [{"p1": 16, "frames": 1}, {"frames": ticks - 1}]
        inputs = [s.get("p1", 0) for s in plan for _ in range(s["frames"])]
        for index, mask in enumerate([0] + inputs):
            if index:
                iso.sequence(sid, [{"p1": mask, "frames": 1}])
            p = iso.request(sid, "read", player, actor_size)
            e = iso.request(sid, "read", enemy, actor_size)
            probe = iso.request(sid, "read", 0xC7E0, 32)
            row = dict(index=index, input=mask, vdp_frame=probe["frame"],
                       player=p["ram"], enemy=e["ram"], probe=probe["ram"])
            if service:
                svc = iso.request(sid, "read", service, service_size)
                row["service"] = svc["ram"]
            if frames:
                im = iso.capture(sid, f"trial_{index:04d}.png")
                dest = out / Path(im["path"]).name
                shutil.copy2(im["path"], dest)
                row["image"] = {"path": dest.name, "sha256": im["sha256"]}
            trace.append(row)
        im = iso.capture(sid, "endpoint.png")
        bundle = iso.publish(sid, "endpoint.png", out / "sessions")
        save(out / "capture_bundle.json", dict(path=str(bundle), check=iso.check_bundle(bundle)))
    finally:
        iso.close_session(sid)
        _, final = iso.load(sid)
        save(out / "session_final.json", final)
        if (root / "commands.jsonl").exists():
            shutil.copy2(root / "commands.jsonl", out / "commands.jsonl")
        save(out / "trace.json", dict(schema="openbor_runtime_trial_v1", rom_sha256=hashlib.sha256(rom.read_bytes()).hexdigest(),
            session_id=sid, method="one VDP frame per sequence followed by read-only RAM; not throughput", boot_frames=boot,
            layout=dict(player=player, enemy=enemy, size=actor_size,
                        service=service or None, service_size=service_size if service else None),
            script=plan if trace else script, trace=trace,
            cleanup_state=final["state"], captured_at=time.time()))
    print(json.dumps(dict(out=str(out), session_id=sid, rows=len(trace), cleanup=final["state"])))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--ticks", type=int, default=180)
    ap.add_argument("--boot", type=int, default=280)
    ap.add_argument("--player", type=lambda x: int(x, 0), default=0xC000,
                    help="actor A base (default: current openbor_sms_rev1 layout)")
    ap.add_argument("--enemy", type=lambda x: int(x, 0), default=0xC030)
    ap.add_argument("--actor-size", type=int, default=48)
    ap.add_argument("--service", type=lambda x: int(x, 0), default=0,
                    help="optional diagnostic block base (read-only)")
    # Bloco minimo = 6 bytes (bytes_p, bytes_e, flags, pad, vc0, vc1) em 0xC7CC.
    # Ler 20 bytes a partir dai invade o corredor de probe (0xC7D2 = vline_min).
    ap.add_argument("--service-size", type=int, default=6)
    ap.add_argument("--frames", action="store_true")
    ap.add_argument("--script", type=Path)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        assert hashlib.sha256(b"a").hexdigest() != hashlib.sha256(b"b").hexdigest()
        assert len([s.get("p1", 0) for s in [{"p1": 16, "frames": 1}, {"frames": 4}] for _ in range(s["frames"])]) == 5
        assert args.actor_size > 0 and args.service_size > 0
        print("[OK] trial plan self-check; runtime integration requires session")
        return
    if not args.rom or not args.out:
        ap.error("--rom and --out required")
    run(args.rom,args.out,args.ticks,args.boot,args.player,args.enemy,args.actor_size,args.frames,
        json.loads(args.script.read_text()) if args.script else None,
        args.service,args.service_size)


if __name__ == "__main__":
    main()
