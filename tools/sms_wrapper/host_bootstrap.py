#!/usr/bin/env python3
"""Install a pinned SMS build/QA environment, or report blockers without mutation.

Supported target: Linux x86_64, CPython 3.11–3.14. OS package setup is in
bootstrap_host.sh; Python packages stay in a checkout-local venv. Never
restore project evidence, configuration, credentials or user profiles here.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import select
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STATE = ROOT / "out/host-bootstrap"
RELEASE = "https://github.com/Misael-art/sms-forge/releases/download/continuity-20261021/"
ASSETS = {
    "sdk": {"name": "sdk_20261021.tar.zst", "bytes": 27495180,
            "sha256": "ca2ab84e244bb6bcbc44eb92c6a03b88d38fc30760a64ed3d7a8147d82e74945"},
    "emulators": {"name": "emulators_20261021.tar.zst", "bytes": 93081359,
                  "sha256": "1f28daa439ac3eb8bf0f6459b1d12421f2b5c7c64c4b321c1a5335c3cd849c2a"},
}
KEY_FILES = {
    'sdk/sdcc-portable/lib/sdcc/x86_64-pc-linux-gnu/12.1.0/cc1': '72262ca9a2e2bfd7b899eb832e92f4a1810073bd2c5a68f51441a7894f7f577b',
    "sdk/sdcc-portable/bin/sdcc": "09dbddb81fd724efe18bc83c48dbad1d6a50b33964f9a5520a1c9fd7445be564",
    "sdk/devkitSMS/SMSlib/SMSlib.h": "a258e4df64dbc4bf4ae0ddf20e68796cbda02e4635cd2123a7d0b6ffda1d0c4a",
    "sdk/devkitSMS/PSGlib/PSGlib.h": "89391c5e48b4d7ad5bc71fe840c531f9701ad705a0ba00252aacc382a75fa7f4",
    "sdk/devkitSMS/crt0/crt0_sms.rel": "a652979b91716663122090b9b468b48f707122ca3334451a8d83432fe0b48eff",
    "sdk/devkitSMS/SMSlib/SMSlib.lib": "5a82820d0d4f56ae375d1184cd12bec95791ed3644a20b5e99c492db786057ed",
    "sdk/devkitSMS/PSGlib/PSGlib.lib": "040b43dbeea62b1e74da924778fd38d917bbb49436262b9448ccd07be56496e0",
    "sdk/devkitSMS/tools/makesms": "617b2e794af50841ce14b40e4085abe6292f829581451b0423e28e117517b346",
    "tools/emuladores/emulicious/Emulicious.jar": "db185a1ed0af3bdab5ebdeb254612d02d3848bac155dbc89333d1b04e21c371d",
    "tools/emuladores/emulicious/License.txt": "731953038f318207b6c59f3a2fffcacdfdae95301a43cafa374f2aa82ce02ca2",
}
BUILD_COMMANDS = ("git", "zstd")
QA_COMMANDS = ("java", "javac", "Xvfb", "xdpyinfo", "bwrap", "ffmpeg", "ffprobe", "pactl", "pacat")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(command, **kwargs):
    return subprocess.run(list(map(str, command)), check=True, text=True,
                          capture_output=True, timeout=kwargs.pop("timeout", 180), **kwargs)


def environment(root=ROOT):
    env = os.environ.copy()
    env.update(SMS_DEVKITSMS=str(root / "sdk/devkitSMS"),
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONDONTWRITEBYTECODE="1")
    env["PATH"] = os.pathsep.join(map(str, (root / "out/host-bootstrap/venv/bin",
                                          root / "sdk/sdcc-portable/bin",
                                          root / "sdk/devkitSMS/tools"))) + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = str(root / "tools/sms_wrapper")
    return env


def download(asset, cache):
    cache.mkdir(parents=True, exist_ok=True)
    target = cache / asset["name"]
    if target.exists():
        if target.stat().st_size != asset["bytes"] or sha(target) != asset["sha256"]:
            raise ValueError("cache hash mismatch; preserve and inspect: " + str(target))
        return target
    temp = cache / (target.name + "." + uuid.uuid4().hex + ".part")
    try:
        req = urllib.request.Request(RELEASE + asset["name"], headers={"User-Agent": "SMSForge-bootstrap"})
        with urllib.request.urlopen(req, timeout=60) as response, temp.open("xb") as stream:
            remaining = asset["bytes"]
            while True:
                chunk = response.read(min(1024 * 1024, remaining + 1))
                if not chunk:
                    break
                remaining -= len(chunk)
                if remaining < 0:
                    raise ValueError("download exceeds pinned size")
                stream.write(chunk)
        if temp.stat().st_size != asset["bytes"] or sha(temp) != asset["sha256"]:
            raise ValueError("release hash/size mismatch; pin unchanged")
        temp.replace(target)
    finally:
        temp.unlink(missing_ok=True)
    return target


def extract_selected(archive, destination, prefixes):
    """Stream zstd; reject traversal, links and special files before publication."""
    destination = Path(destination)
    total = count = 0
    seen = set()
    with subprocess.Popen(["zstd", "-dc", str(archive)], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as decoder:
        try:
            with tarfile.open(fileobj=decoder.stdout, mode="r|") as tar:
                for member in tar:
                    name = PurePosixPath(member.name)
                    if name.is_absolute() or ".." in name.parts or "\\" in member.name:
                        raise ValueError("archive path rejected: " + member.name)
                    if not any(str(name).startswith(p + "/") or str(name) == p for p in prefixes):
                        continue
                    if str(name).startswith("tools/emuladores/emulicious/") and not member.isdir():
                        if name.name not in {"Emulicious.jar", "License.txt"} or len(name.parts) != 4:
                            continue  # Never restore a personal ini, debugger state or recent ROM list.
                    if not (member.isdir() or member.isreg()) or member.name in seen:
                        raise ValueError("archive link/type/duplicate rejected: " + member.name)
                    seen.add(member.name)
                    count += 1
                    total += member.size
                    if total > 600 * 1024 * 1024 or count > 20000:
                        raise ValueError("archive expansion bound exceeded")
                    path = destination / name
                    if member.isdir():
                        path.mkdir(parents=True, exist_ok=True)
                        path.chmod(0o755)
                    else:
                        path.parent.mkdir(parents=True, exist_ok=True)
                        with tar.extractfile(member) as src, path.open("xb") as dst:
                            shutil.copyfileobj(src, dst)
                        path.chmod(0o755 if "/bin/" in member.name or member.name.endswith(("/makesms", "/cc1")) else 0o644)
            decoder.stdout.close()
            error = decoder.stderr.read().decode(errors="replace")
            if decoder.wait(timeout=30):
                raise ValueError("zstd failed: " + error[-500:])
        except BaseException:
            decoder.kill()
            decoder.wait()
            raise
    return {"files_and_dirs": count, "bytes": total}


def install_trees(asset, prefixes):
    archive = download(asset, STATE / "downloads")
    with tempfile.TemporaryDirectory(prefix="stage-", dir=STATE) as tmp:
        stage = Path(tmp)
        extract_selected(archive, stage, prefixes)
        for name, expected in KEY_FILES.items():
            if any(name.startswith(p + "/") for p in prefixes):
                if not (stage / name).is_file() or sha(stage / name) != expected:
                    raise ValueError("staged pinned file mismatch: " + name)
        # Existing trees are verified completely, never replaced or repaired.
        for prefix in prefixes:
            source, target = stage / prefix, ROOT / prefix
            for parent in (target, *target.parents):
                if parent == ROOT:
                    break
                if parent.is_symlink():
                    raise ValueError("installation path aliases outside checkout: " + str(parent))
            if not source.is_dir():
                raise ValueError("archive prefix missing: " + prefix)
            if target.exists() or target.is_symlink():
                if target.is_symlink() or not target.is_dir():
                    raise ValueError("existing destination is not an owned directory: " + str(target))
                for file in source.rglob("*"):
                    if file.is_file():
                        old = target / file.relative_to(source)
                        if old.is_symlink() or not old.is_file() or sha(old) != sha(file):
                            raise ValueError("existing installation differs; preserve it: " + str(old))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                source.rename(target)


def venv_install():
    target = STATE / "venv"
    if target.is_symlink():
        raise ValueError("venv symlink refused; preserve the existing environment")
    if not target.exists():
        run([sys.executable, "-m", "venv", target])
    py = target / "bin/python"
    prefix = run([py, "-c", "import sys; print(sys.prefix)"]).stdout.strip()
    if Path(prefix).resolve() != target.resolve():
        raise ValueError("Python does not belong to checkout-local venv")
    run([py, "-m", "pip", "install", "--disable-pip-version-check", "--no-input",
         "--only-binary=:all:", "--require-hashes", "-r", HERE / "requirements-host.lock"],
        timeout=600, env={**os.environ, "PIP_CACHE_DIR": str(STATE / "pip-cache")})
    return py


def smoke_build(directory):
    directory.mkdir(parents=True, exist_ok=True)
    env = environment()
    sdk = ROOT / "sdk/devkitSMS"
    source = directory / "smoke.c"
    source.write_text('#include "SMSlib.h"\n#include "PSGlib.h"\n'
                      'SMS_EMBED_SEGA_ROM_HEADER(0,0);\nvoid main(void){SMS_init();SMS_displayOn();'
                      'for(;;){SMS_waitForVBlank();PSGFrame();}}\n')
    commands = [
        ["sdcc", "-mz80", "-c", source, "-o", directory / "smoke.rel",
         "-I" + str(sdk / "SMSlib"), "-I" + str(sdk / "PSGlib")],
        ["sdcc", "-mz80", "--no-std-crt0", "--data-loc", "0xC000", "-o", directory / "smoke.ihx",
         sdk / "crt0/crt0_sms.rel", directory / "smoke.rel", sdk / "SMSlib/SMSlib.lib", sdk / "PSGlib/PSGlib.lib"],
        ["makesms", directory / "smoke.ihx", directory / "smoke.sms"],
    ]
    logs = []
    for command in commands:
        result = run(command, cwd=directory, env=env)
        logs.append({"command": list(map(str, command)), "stdout": result.stdout, "stderr": result.stderr})
    rom = directory / "smoke.sms"
    data = rom.read_bytes()
    if len(data) % 16384 or data[0x7FF0:0x7FF8] != b"TMR SEGA":
        raise ValueError("smoke ROM size/header invalid")
    return {"rom_sha256": sha(rom), "rom_bytes": len(data), "commands": logs,
            "limit": "compile/link/header only; not emulator or gameplay acceptance"}


def doctor(profile, live=False):
    problems, checks = [], {}
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        problems.append("supported platform is Linux x86_64")
    if not (3, 11) <= sys.version_info[:2] <= (3, 14):
        problems.append("Python 3.11..3.14 required by binary-wheel lock")
    commands = BUILD_COMMANDS + (QA_COMMANDS if profile != "build" else ())
    for name in commands:
        checks[name] = shutil.which(name)
        if not checks[name]:
            problems.append("missing OS command: " + name)
    for name, expected in KEY_FILES.items():
        if profile == "build" and name.startswith("tools/"):
            continue
        path = ROOT / name
        ok = path.is_file() and sha(path) == expected
        checks[name] = ok
        if not ok:
            problems.append("missing/changed pin: " + name)
        elif ("/bin/" in name or name.endswith(("/makesms", "/cc1"))) and not os.access(path, os.X_OK):
            problems.append("non executable: " + name)
    py = STATE / "venv/bin/python"
    if py.is_file():
        try:
            run([py, "-m", "pip", "check"])
            run([py, "-c", "from PIL import Image; import numpy, pytest"])
            expected = {}
            for line in (HERE / "requirements-host.lock").read_text().splitlines():
                if "==" in line and not line.startswith("#"):
                    name, version = line.split()[0].split("==")
                    expected[name] = version
            actual = json.loads(run([py, "-c", "import importlib.metadata as m,json; "
                                     "print(json.dumps({n:m.version(n) for n in " + repr(list(expected)) + "}))"]).stdout)
            if actual != expected:
                raise ValueError("venv versions differ from requirements-host.lock")
            checks["venv"] = True
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            problems.append("venv unusable: " + str(exc))
    else:
        problems.append("checkout-local venv missing")
    checks["disk_free_bytes"] = shutil.disk_usage(ROOT).free
    if checks["disk_free_bytes"] < 2 * 1024**3:
        problems.append("less than 2 GiB free; preserve headroom for staging/evidence")
    if profile == "full":
        try:
            from blastem_sms import runtime, BINARY_SHA
            checks["blastem_pinned_runtime"] = sha(runtime()) == BINARY_SHA
        except (ValueError, OSError, KeyError) as exc:
            problems.append("BlastEm pin unavailable: " + str(exc))
    if live and profile != "build":
        # Active, explicit preflight; no emulator, desktop controls or global kills.
        for label, command in (
            ("sandbox", ["bwrap", "--unshare-user", "--unshare-pid", "--ro-bind", "/", "/", "--proc", "/proc", "--dev", "/dev", "true"]),
            ("pulse", ["pactl", "info"]),
            ("java", ["java", "-version"]),
            ("javac", ["javac", "-version"]),
        ):
            try:
                result = run(command, timeout=15)
                checks[label] = (result.stdout + result.stderr)[-1200:]
            except (OSError, subprocess.SubprocessError) as exc:
                problems.append(label + " unavailable: " + str(exc))
        if shutil.which("Xvfb"):
            child = None
            try:
                child = subprocess.Popen(["Xvfb", "-displayfd", "1", "-screen", "0", "256x192x24",
                                          "-nolisten", "tcp"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                if not select.select([child.stdout], [], [], 5)[0]:
                    raise ValueError("private Xvfb startup timeout")
                display = child.stdout.readline().decode().strip()
                if not display.isdigit() or child.poll() is not None:
                    raise ValueError("private Xvfb failed to publish a display")
                checks["private_xvfb"] = "started and closed own display :" + display
            except (OSError, ValueError) as exc:
                problems.append("Xvfb startup failed: " + str(exc))
            finally:
                if child is not None:
                    if child.poll() is None:
                        child.terminate()
                    try:
                        child.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
                    child.stdout.close()
        try:
            # Only compile the bridge when the pinned JAR is present.
            if checks.get("tools/emuladores/emulicious/Emulicious.jar"):
                run([py, "-c", "from session_bridge.isolated import build_bridge; print(build_bridge())"],
                    env=environment())
                checks["bridge_compiles"] = True
        except (OSError, subprocess.SubprocessError) as exc:
            problems.append("bridge compilation failed: " + str(exc))
    return {"schema": "sms_host_doctor_v1", "profile": profile, "ok": not problems,
            "checks": checks, "problems": problems, "active_checks": live,
            "claim_ceiling": "environment_readiness_only",
            "limits": ["No emulator/input/audio capture/FPS proof; run isolated acceptance next.",
                       "OS packages follow distro security updates; pinned SDK and Python do not pin kernel/JVM/audio stack."]}


def apply(profile):
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise ValueError("pinned portable toolchain supports Linux x86_64 only")
    if not (3, 11) <= sys.version_info[:2] <= (3, 14):
        raise ValueError("Python 3.11..3.14 required")
    for cmd in BUILD_COMMANDS:
        if not shutil.which(cmd):
            raise ValueError("missing " + cmd + "; use bootstrap_host.sh --apply --system-packages")
    if shutil.disk_usage(ROOT).free < 2 * 1024**3:
        raise ValueError("2 GiB free required before download/extraction")
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / "install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        install_trees(ASSETS["sdk"], ("sdk/sdcc-portable", "sdk/devkitSMS"))
        license_src = HERE / "vendor/devkitSMS-LICENSES.txt"
        license_dst = ROOT / "sdk/devkitSMS/LICENSES.txt"
        if license_dst.exists() and sha(license_dst) != sha(license_src):
            raise ValueError("existing SDK license differs; preserve and inspect")
        if not license_dst.exists():
            shutil.copyfile(license_src, license_dst)
        if profile != "build":
            install_trees(ASSETS["emulators"], ("tools/emuladores/emulicious",))
            shared_config = ROOT / "tools/emuladores/emulicious/Emulicious.ini"
            if not shared_config.exists():
                with shared_config.open("x") as stream:
                    stream.write("Update=0\nOpenMostRecentOnStartup=false\n")
        venv_install()
        run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "_" + uuid.uuid4().hex[:8]
        output = STATE / "runs" / run_id
        output.mkdir(parents=True)
        try:
            smoke = smoke_build(output / "smoke")
            if profile == "full":
                run([STATE / "venv/bin/python", HERE / "blastem_sms.py", "install"],
                    env=environment(), timeout=180)
            result = doctor(profile, live=True)
            result["smoke_build"] = smoke
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            result = {"ok": False, "problems": [str(exc)], "claim_ceiling": "environment_readiness_only"}
            if isinstance(exc, subprocess.CalledProcessError):
                result["command_output"] = (exc.stdout or "") + (exc.stderr or "")
        result.update(run_id=run_id, source_root=str(ROOT),
                      bootstrap_sha256=sha(__file__), requirements_sha256=sha(HERE / "requirements-host.lock"))
        report = output / "report.json"
        report.write_text(json.dumps(result, indent=2) + "\n")
        print("REPORT=" + str(report))
        return result


def prune_cache():
    removed = []
    if not STATE.exists():
        return {"ok": True, "removed": [], "scope": "downloads and pip-cache only"}
    with (STATE / "install.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for name in ("downloads", "pip-cache"):
            path = STATE / name
            if path.is_symlink():
                raise ValueError("cache symlink refused: " + str(path))
            if path.exists():
                shutil.rmtree(path)
                removed.append(name)
    return {"ok": True, "removed": removed, "scope": "downloads and pip-cache only; venv/SDK/runs/evidence preserved"}


def self_check():
    from unittest.mock import patch
    import io
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name in ("ok", "traversal", "link", "duplicate"):
            raw = root / (name + ".tar")
            with tarfile.open(raw, "w") as tar:
                entry = tarfile.TarInfo("sdk/devkitSMS/x" if name != "traversal" else "sdk/../outside")
                if name == "link":
                    entry.type = tarfile.SYMTYPE
                    entry.linkname = "/etc/passwd"
                else:
                    entry.size = 2
                tar.addfile(entry, None if name == "link" else io.BytesIO(b"ok"))
                if name == "duplicate":
                    tar.addfile(entry, io.BytesIO(b"ok"))
            packed = root / (name + ".zst")
            run(["zstd", "-q", raw, "-o", packed])
            try:
                extract_selected(packed, root / name, ("sdk/devkitSMS",))
            except ValueError:
                assert name != "ok"
            else:
                assert name == "ok"
                assert (root / name / "sdk/devkitSMS/x").read_bytes() == b"ok"
        cache = root / "cache"
        cache.mkdir()
        source = cache / "bad"
        source.write_bytes(b"bad")
        try:
            download({"name": "bad", "bytes": 3, "sha256": "0" * 64}, cache)
        except ValueError:
            pass
        else:
            raise AssertionError("bad cached hash accepted")
        assert source.read_bytes() == b"bad"
        # Reinstallation verifies existing contents and never clobbers a divergence.
        tree_root = root / "install"
        state = tree_root / "out/host-bootstrap"
        state.mkdir(parents=True)
        def fixture_extract(archive, destination, prefixes):
            folder = Path(destination) / "sdk/devkitSMS"
            folder.mkdir(parents=True)
            (folder / "fixture").write_bytes(b"pinned")
        expected = hashlib.sha256(b"pinned").hexdigest()
        with patch.dict(globals(), ROOT=tree_root, STATE=state,
                        KEY_FILES={"sdk/devkitSMS/fixture": expected}), \
                patch.dict(globals(), download=lambda a, c: source, extract_selected=fixture_extract):
            install_trees({}, ("sdk/devkitSMS",))
            install_trees({}, ("sdk/devkitSMS",))
            installed = tree_root / "sdk/devkitSMS/fixture"
            installed.write_bytes(b"custom")
            try:
                install_trees({}, ("sdk/devkitSMS",))
            except ValueError:
                pass
            else:
                raise AssertionError("divergent installation overwritten")
            assert installed.read_bytes() == b"custom"
        with patch.object(sys, "version_info", (3, 9)), patch.object(shutil, "which", return_value=None):
            assert not doctor("build")["ok"]
        with patch.dict(globals(), STATE=root / "state"):
            (STATE / "downloads").mkdir(parents=True)
            (STATE / "pip-cache").mkdir()
            (STATE / "runs").mkdir()
            keep=STATE / "runs/evidence.json";keep.write_text("preserve")
            assert set(prune_cache()["removed"])=={"downloads","pip-cache"}
            assert keep.read_text()=="preserve"
        assert (environment(root)["PATH"].split(os.pathsep)[0]) == str(root / "out/host-bootstrap/venv/bin")
    print("[SELF-CHECK OK] host bootstrap: confined archives, links/duplicates, hash refusal, blockers and local environment; offline only")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("build", "qa", "full"), default="full")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--system-packages", action="store_true", help="handled by bootstrap_host.sh only")
    parser.add_argument("--doctor", action="store_true")
    parser.add_argument("--live-checks", action="store_true")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--prune-cache", action="store_true", help="explicitly delete only this checkout download/pip caches under install lock")
    args = parser.parse_args()
    if args.self_check:
        return self_check()
    try:
        if args.prune_cache:
            result = prune_cache()
        elif args.apply:
            result = apply(args.profile)
        else:
            result = doctor(args.profile, args.live_checks)
            result["next_command"] = "bash tools/sms_wrapper/bootstrap_host.sh --apply --system-packages --profile " + args.profile
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 2
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "claim_ceiling": "environment_readiness_only"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
