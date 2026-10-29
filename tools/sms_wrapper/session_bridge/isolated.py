"""Linux isolated Emulicious sessions. No host focus or global process kill.

Library and CLI behind emulator_session.py. Diagnostic mode is not an FPS,
audio or visual-quality approval. Credentials stay in a private session dir.
"""
from __future__ import annotations
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid
import zipfile
import platform

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
EMULATOR = WORKSPACE / "tools/emuladores/emulicious"
SUPPORTED_JAR = "db185a1ed0af3bdab5ebdeb254612d02d3848bac155dbc89333d1b04e21c371d"
DEFAULT_ROOT = Path(f"/tmp/smsforge-{os.getuid()}")
BUTTONS = {"up": 1, "down": 2, "left": 4, "right": 8, "1": 16, "2": 32}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def atomic(path, data):
    path = Path(path)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(path)

def identity(pid):
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return None

def alive(process):
    return identity(process["pid"]) == process["start_ticks"] and process["start_ticks"] is not None

def process_record(pid):
    return {"pid": pid, "start_ticks": identity(pid)}

def checked(cmd, **kwargs):
    result = subprocess.run(list(map(str, cmd)), capture_output=True, text=True, **kwargs)
    if result.returncode:
        raise RuntimeError(f"{cmd[0]} failed: {(result.stdout + result.stderr)[-4000:]}")
    return result

def build_bridge(ecj=None):
    jar = EMULATOR / "Emulicious.jar"
    if sha(jar) != SUPPORTED_JAR:
        raise RuntimeError("Emulicious JAR changed; repay bridge compatibility before use")
    cache = WORKSPACE / "out/session_bridge"
    cache.mkdir(parents=True, exist_ok=True)
    with open(cache / "build.lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        source = HERE / "ForgeSMS.java"
        key = sha(source) + SUPPORTED_JAR
        target = cache / "smsforge-input.jar"
        if target.exists() and (cache / "key").exists() and (cache / "key").read_text() == key:
            return target
        classes = cache / "classes"
        if classes.exists(): shutil.rmtree(classes)
        classes.mkdir()
        compiler = shutil.which("javac")
        if compiler:
            command = [compiler, "--release", "17"]
        elif ecj:
            # Some distro runtimes omit release metadata. The private view
            # supplies the actual Java version, without editing /usr/lib/jvm.
            props = checked(["java", "-XshowSettings:properties", "-version"])
            values = {}
            for line in props.stderr.splitlines():
                if " = " in line:
                    k, v = line.split(" = ", 1); values[k.strip()] = v.strip()
            view = cache / "java-system"
            (view / "lib").mkdir(parents=True, exist_ok=True)
            (view / "release").write_text('JAVA_VERSION="' + values["java.version"] + '"\n')
            for name in ("modules", "jrt-fs.jar"):
                link = view / "lib" / name
                if not link.exists(): link.symlink_to(Path(values["java.home"]) / "lib" / name)
            command = ["java", "-jar", str(Path(ecj).resolve()), "--system", str(view), "-17"]
        else:
            raise RuntimeError("javac 17+ required, or supply --ecj PATH (Eclipse compiler)")
        checked(command + ["-proc:none", "-classpath", str(jar), "-d", str(classes), str(source)])
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            for path in classes.rglob("*.class"): z.write(path, path.relative_to(classes))
        (cache / "key").write_text(key)
        return target

def auth_file(path):
    cookie = secrets.token_bytes(16)
    fields = (b"", b"", b"MIT-MAGIC-COOKIE-1", cookie)
    path.write_bytes(struct.pack("!H", 65535) + b"".join(struct.pack("!H", len(x)) + x for x in fields))
    path.chmod(0o600)

def load(session):
    root = Path(session)
    if not root.is_absolute(): root = DEFAULT_ROOT / session
    root = root.resolve()
    meta = json.loads((root / "session.json").read_text())
    if meta["session_id"] != root.name or meta["root"] != str(root):
        raise RuntimeError("session path identity mismatch")
    return root, meta

def start(rom, xvfb=None, ecj=None, ttl=1800, enable_audio=True):
    rom = Path(rom).resolve()
    if not rom.is_file() or rom.suffix.lower() != ".sms": raise ValueError("existing .sms ROM required")
    for binary in ("java", "bwrap"):
        if not shutil.which(binary): raise RuntimeError(f"{binary} required; no desktop fallback")
    runtime = WORKSPACE / "out/session_bridge/runtime"
    xvfb = xvfb or shutil.which("Xvfb") or (str(runtime / "xvfb/usr/bin/Xvfb") if (runtime / "xvfb/usr/bin/Xvfb").is_file() else None)
    ecj = ecj or (str(runtime / "ecj.jar") if (runtime / "ecj.jar").is_file() else None)
    if not xvfb or not Path(xvfb).is_file(): raise RuntimeError("Xvfb required; no desktop fallback")
    bridge = build_bridge(ecj)
    if ttl < 10 or ttl > 7200: raise ValueError("session TTL must be 10..7200 seconds")
    DEFAULT_ROOT.mkdir(mode=0o700, exist_ok=True)
    if DEFAULT_ROOT.stat().st_uid != os.getuid() or DEFAULT_ROOT.stat().st_mode & 0o077:
        raise RuntimeError("session root must be owned by this user with mode 0700")
    sid = uuid.uuid4().hex
    root = DEFAULT_ROOT / sid; root.mkdir(mode=0o700)
    (root / "emulator").mkdir(); (root / "evidence").mkdir()
    for name in ("Emulicious.jar", "License.txt"):
        shutil.copy2(EMULATOR / name, root / "emulator" / name)
    shutil.copy2(bridge, root / "emulator/bridge.jar")
    shutil.copy2(HERE / "ForgeSMS.java",root / "emulator/ForgeSMS.java")
    shutil.copy2(rom, root / "emulator/rom.sms")
    # Empty, intentional configuration: never inherit shared mappings,
    # recent ROMs, cheats, SRAM or debugger settings from another agent.
    config = root / "emulator/Emulicious.ini"
    config.write_text("Update=0\nAudioSync=false\nScale=1\nFrameskip=0\nDisableFrameBlending=true\n"
                      "DisableHardwareAcceleration=true\nOpenMostRecentOnStartup=false\n"
                      "SMSInputDeviceA=1\nSMSInputDeviceB=1\nScreenshotCropBorders=true\n"
                      "SMSGamepadAKeyboard=false\nSMSGamepadBKeyboard=false\nKeyboardRequireWindowFocus=true\n")
    (root / "token").write_text(secrets.token_hex(32) + "\n"); (root / "token").chmod(0o600)
    auth_file(root / "Xauthority")
    meta = {"schema": 1, "session_id": sid, "root": str(root), "state": "created",
            "created_at": time.time(), "source_rom": str(rom), "rom_sha256": sha(rom),
            "emulator_sha256": sha(root / "emulator/Emulicious.jar"),
            "bridge_sha256": sha(root / "emulator/bridge.jar"), "bridge_source_sha256": sha(HERE / "ForgeSMS.java"),
            "config_initial_sha256": sha(config), "xvfb": str(Path(xvfb).resolve()),
            "host_display":os.environ.get("DISPLAY"),
            "xvfb_sha256": sha(xvfb), "ttl_seconds": ttl,
            "host_load": os.getloadavg(), "audio": "private_sink_unvalidated",
            "enable_audio_requested": bool(enable_audio), "input": "process_local_SMSJoypad"}
    atomic(root / "session.json", meta)
    with open(root / "supervisor.log", "w") as log:
        subprocess.Popen([sys.executable, str(HERE / "isolated.py"), "_supervise", str(root)],
                         stdout=log, stderr=log, start_new_session=True, close_fds=True)
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        current = json.loads((root / "session.json").read_text())
        if current["state"] == "input_verified":
            return root
        if current["state"] in ("failed", "closed"):
            raise RuntimeError(f"isolated boot failed; see {root}/supervisor.log and emulator.log")
        time.sleep(0.05)
    raise RuntimeError(f"isolated boot timeout; see {root}; supervisor TTL will clean up owned processes")

def route_audio(meta, timeout=8.0):
    """Move ONLY the sink-input owned by this session's exact PID into its private sink.
    Host policy (jamesdsp) reroutes streams at birth, so routing is post-hoc; the session
    boots muted and primes the stream with zeros; only confirmed routing permits unmute."""
    pid, sink = meta["emulator_process"]["pid"], meta.get("audio_sink")
    if not sink: return None
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        out, idx, owner = [], None, None
        text = subprocess.run(["pactl", "list", "sink-inputs"], capture_output=True, text=True).stdout
        for line in text.splitlines() + ["Sink Input #END"]:
            line = line.strip()
            if line.startswith("Sink Input #"):
                if idx is not None and owner == str(pid): out.append(idx)
                idx, owner = line.split("#")[1].strip(), None
            elif line.startswith("application.process.id"): owner = line.split("=", 1)[1].strip().strip('"')
        moved = [i for i in out if subprocess.run(["pactl", "move-sink-input", i, sink], capture_output=True).returncode == 0]
        if moved and verify_audio_route(meta, moved):
            return {"sink_inputs": moved, "pid": pid, "sink": sink, "at": time.time(), "verified": True}
        time.sleep(0.05)
    return None

def verify_audio_route(meta, inputs=None):
    """Read back actual sink membership; a successful move alone is not evidence."""
    sinks = checked(["pactl", "--format=json", "list", "sinks"])
    streams = checked(["pactl", "--format=json", "list", "sink-inputs"])
    target = [s["index"] for s in json.loads(sinks.stdout) if s["name"] == meta.get("audio_sink")]
    owned = [s for s in json.loads(streams.stdout)
             if str(s.get("properties", {}).get("application.process.id")) == str(meta["emulator_process"]["pid"])]
    return bool(target and owned and all(s["sink"] == target[0] for s in owned)
                and (inputs is None or {str(s["index"]) for s in owned} == set(inputs)))

def close_session(session):
    root, meta = load(session)
    result = request(root, "close")
    end = time.monotonic() + 15
    while time.monotonic() < end:
        current = load(root)[1]
        if current["state"] == "closed" and not alive(meta["emulator_process"]):
            sinks = json.loads(checked(["pactl", "--format=json", "list", "sinks"]).stdout)
            if any(s["name"] == meta.get("audio_sink") for s in sinks):
                raise RuntimeError("owned audio sink survived shutdown")
            return result
        time.sleep(0.1)
    raise RuntimeError("owned supervisor shutdown timeout")

def supervise(root):
    root, meta = load(root)
    children = []
    meta["supervisor"] = process_record(os.getpid()); atomic(root / "session.json", meta)
    try:
        readfd, writefd = os.pipe()
        with open(root / "xvfb.log", "w") as log:
            x = subprocess.Popen([meta["xvfb"], "-displayfd", str(writefd), "-screen", "0", "800x600x24",
                                  "-nolisten", "tcp", "-auth", str(root / "Xauthority"), "-noreset"],
                                 pass_fds=(writefd,), stdout=log, stderr=log)
        children.append(x); os.close(writefd)
        try:
            # Xvfb may write the digits and newline separately. Closing after
            # the first read can SIGPIPE its final write and destroy the socket.
            data = b""; deadline = time.monotonic() + 10
            while b"\n" not in data and len(data) < 64:
                remaining = deadline - time.monotonic()
                if remaining <= 0 or not select.select([readfd], [], [], remaining)[0]:
                    raise RuntimeError("Xvfb did not allocate display")
                part = os.read(readfd, 64-len(data))
                if not part: raise RuntimeError("Xvfb display pipe closed before readiness")
                data += part
            if b"\n" not in data: raise RuntimeError("incomplete Xvfb display readiness")
            number = data.decode().strip()
            if not number.isdigit(): raise RuntimeError("invalid Xvfb display")
        finally: os.close(readfd)
        display = ":" + number
        # Host policy may ignore PULSE_SINK. Boot stays muted until PID routing is read back.
        sink = "smsforge_" + meta["session_id"].replace("-", "")[:16]
        mod = subprocess.run(["pactl", "load-module", "module-null-sink", f"sink_name={sink}",
                              "sink_properties=device.description=SMSForge_" + sink[-8:]],
                             capture_output=True, text=True)
        if mod.returncode == 0 and mod.stdout.strip().isdigit():
            sink_module = mod.stdout.strip(); meta.update(audio_sink=sink, audio_sink_module=sink_module)
        else:
            sink_module = None; meta.update(audio_sink=None, audio_error=mod.stderr[:200])
        meta.update(display=display, xvfb_process=process_record(x.pid), state="prepared")
        atomic(root / "session.json", meta)
        env = os.environ.copy()
        for key in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS"):
            env.pop(key, None)
        env.update(DISPLAY=display, XAUTHORITY=str(root / "Xauthority"),
                   XDG_CONFIG_HOME=str(root / "config"), XDG_DATA_HOME=str(root / "data"),
                   XDG_CACHE_HOME=str(root / "cache"))
        if sink_module: env.update(PULSE_SINK=sink)  # advisory only: this host's audio policy reroutes explicit sinks
        # Private /dev hides /dev/input, /dev/uinput and /dev/snd. Private /tmp
        # exposes only this X socket. The workspace and user's home are read-only.
        command = ["bwrap", "--die-with-parent", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc",
                   "--tmpfs", "/tmp", "--dir", "/tmp/.X11-unix",
                   "--ro-bind", f"/tmp/.X11-unix/X{number}", f"/tmp/.X11-unix/X{number}",
                   "--bind", str(root), str(root), "--chdir", str(root / "emulator"),
                   "java", "-Duser.home=" + str(root), "-Dsmsforge.root=" + str(root),
                   "-Dsmsforge.session=" + meta["session_id"], "-cp", "bridge.jar:Emulicious.jar",
                   "smsforge.ForgeSMS", "-nojoy", "-muted", "-scale", "1", "rom.sms"]
        with open(root / "emulator.log", "w") as log:
            emulator = subprocess.Popen(command, stdout=log, stderr=log, env=env)
        children.append(emulator)
        meta["sandbox"] = process_record(emulator.pid); atomic(root / "session.json", meta)
        deadline = time.monotonic() + 35
        while not (root / "ready.json").exists():
            if emulator.poll() is not None: raise RuntimeError("emulator exited before virtual input ready")
            if time.monotonic() > deadline: raise RuntimeError("bridge readiness timeout")
            time.sleep(0.05)
        ready = json.loads((root / "ready.json").read_text())
        meta.update(emulator_process=process_record(ready["pid"]), ready=ready)
        meta["audio_route"] = route_audio(meta)  # before 'input_verified': start() returns only after routing
        if meta.get("audio_sink") and not meta["audio_route"]: meta["audio_error"] = "stream of exact PID not found/moved"
        meta["audio_boot"] = {"muted_from_launch": True, "ready_audio_enabled": ready["audio_enabled"],
                              "silent_stream_priming": True}
        atomic(root / "session.json", meta)
        if meta["audio_route"] and meta["enable_audio_requested"]:
            enabled = request(root, "audio-enable")
            if not enabled["audio_enabled"] or enabled["running"]:
                raise RuntimeError("audio activation did not preserve paused startup")
            meta["audio_boot"]["unmuted_after_verified_route"] = True
        meta["state"] = "input_verified"
        atomic(root / "session.json", meta)
        expires = time.monotonic() + meta["ttl_seconds"]
        while emulator.poll() is None and x.poll() is None and time.monotonic() < expires:
            time.sleep(0.2)
        # Metadata may have been advanced by clients; preserve captures/seals.
        meta = json.loads((root / "session.json").read_text())
        meta["state"] = "closed"; meta["closed_at"] = time.time()
    except Exception as e:
        print(str(e), flush=True); meta["state"] = "failed"; meta["error"] = str(e)
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
                try: child.wait(timeout=3)
                except subprocess.TimeoutExpired: child.kill(); child.wait(timeout=3)
        if meta.get("audio_sink_module"):  # only after the emulator is gone
            subprocess.run(["pactl", "unload-module", meta["audio_sink_module"]], capture_output=True)
        atomic(root / "session.json", meta)

def request(session, operation, *args):
    root, meta = load(session)
    with open(root / "client.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        root, meta = load(root)
        if meta["state"] in ("closed", "failed") or not alive(meta["emulator_process"]):
            raise RuntimeError("session closed or process identity changed")
        if sha(root / "emulator/rom.sms") != meta["rom_sha256"]:
            raise RuntimeError("private ROM changed")
        if operation == "audio-enable" and (not meta.get("audio_route") or not verify_audio_route(meta)):
            raise RuntimeError("audio activation requires verified private PID route")
        if operation in ("run", "step", "sequence", "video", "record-start") and meta.get("audio_route") and not verify_audio_route(meta):
            raise RuntimeError("private audio route changed; refusing emulator advancement")
        sequence_file = root / "sequence"
        seq = (int(sequence_file.read_text()) if sequence_file.exists() else 0) + 1
        sequence_file.write_text(str(seq))
        token = (root / "token").read_text().strip()
        message = " ".join(map(str, [meta["session_id"], token, seq, operation, *args])) + "\n"
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(30); client.connect(str(root / "control.sock")); client.sendall(message.encode())
            response = b""
            while b"\n" not in response:
                chunk = client.recv(4096)
                if not chunk: raise RuntimeError("bridge closed without acknowledgement")
                response += chunk
        result = json.loads(response)
        if not result.get("ok") or result.get("session_id") != meta["session_id"] or result.get("seq") != seq:
            raise RuntimeError("bridge rejected command or identity mismatch")
        if result["pid"] != meta["emulator_process"]["pid"]: raise RuntimeError("wrong emulator PID")
        with open(root / "commands.jsonl", "a") as journal:
            journal.write(json.dumps({"operation": operation, "args": args, "ack": result, "at": time.time()}) + "\n")
        if operation in ("run", "capture", "record-start", "record-stop"):
            meta["state"] = ("running" if operation in ("run", "record-start") else
                             "recorded" if operation == "record-stop" else "captured")
            atomic(root / "session.json", meta)
        return result

def capture(session, name="frame.png"):
    root, meta = load(session)
    result = request(root, "capture", name)
    path = root / "evidence" / name
    from PIL import Image
    with Image.open(path) as im:
        if im.size != (256, 192) or len(im.getcolors(65536) or []) < 2:
            raise RuntimeError("uninformative or non-SMS framebuffer")
    from capture_evidence import image_informative
    informative,detail=image_informative(str(path))
    if not informative:raise RuntimeError("uninformative framebuffer: "+detail)
    record = {"schema": 1, "session_id": meta["session_id"], "rom_sha256": meta["rom_sha256"],
              "emulator_sha256": meta["emulator_sha256"], "bridge_sha256": meta["bridge_sha256"],
              "config_sha256": sha(root / "emulator/Emulicious.ini"), "display": meta["display"],
              "effective_config_sha256": sha(root / "effective-config.ini"),
              "emulator_process": meta["emulator_process"], "frame": result["frame"],
              "captured_at": time.time(), "path": str(path), "sha256": sha(path),
              "canvas": [256, 192], "audio": meta["audio"], "host_load": os.getloadavg()}
    record.update(informative=True,detail=detail)
    atomic(path.with_suffix(".json"), record)
    return record

def video(session,count=120,name="video"):
    """Actual framebuffers captured one per VDP frame. No audio/FPS claim."""
    root,meta=load(session)
    result=request(root,"video",name,count)
    frames=root/"evidence"/name
    target=root/"evidence"/(name+".mp4")
    hz=result["nominal_hz"]
    checked(["ffmpeg","-nostdin","-v","error","-framerate",str(hz),"-i",frames/"%06d.png",
             "-c:v","libx264","-crf","0","-pix_fmt","yuv444p",target],timeout=60)
    hashes=[sha(p) for p in sorted(frames.glob("*.png"))]
    record={"schema":1,"session_id":meta["session_id"],"rom_sha256":meta["rom_sha256"],
            "first_frame":result["first_frame"],"last_frame":result["frame"],
            "frames":count,"frame_sha256":hashes,"distinct_frames":len(set(hashes)),
            "canvas":[256,192],"playback_hz":hz,"path":str(target),"sha256":sha(target),
            "method":"one native framebuffer per VDP frame; stepped emulation",
            "performance":"not_measured","audio":"not_recorded"}
    if len(hashes)!=count:raise RuntimeError("missing video frames")
    atomic(target.with_suffix(".json"),record);return record


def realtime_video(session, seconds=8, name="realtime_video"):
    """Native cropped RGB24 callback during free run, never frame stepping.

    This records presentation; capture overhead and nominal playback timebase
    must not be promoted to a ROM throughput or perceived-fluidity verdict.
    """
    import re
    if (isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or
            not 1 <= seconds <= 30 or not isinstance(name, str) or
            not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", name)):
        raise ValueError("realtime capture needs 1..30 seconds and a safe artifact name")
    root, meta = load(session)
    raw = root / "evidence" / (name + ".rgb")
    target = root / "evidence" / (name + ".mp4")
    if raw.exists() or target.exists():
        raise FileExistsError("preserving existing realtime capture")
    estimate = int(seconds * 61 * 256 * 192 * 3)
    if shutil.disk_usage(root).free < estimate * 2 + 64 * 1024 * 1024:
        raise RuntimeError("insufficient space for native RGB capture and retained evidence")
    load_before = os.getloadavg()
    request(root, "record-start", name)
    try:
        time.sleep(seconds)
    finally:
        stopped = request(root, "record-stop")
    count = stopped["recorded_frames"]
    if count < 60 or raw.stat().st_size != count * 256 * 192 * 3:
        raise RuntimeError("native realtime RGB length/count mismatch; capture is not approved")
    hz = stopped["nominal_hz"]
    checked(["ffmpeg", "-nostdin", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
             "-video_size", "256x192", "-framerate", str(hz), "-i", raw,
             "-an", "-c:v", "libx264rgb", "-crf", "0", "-threads", "1", target], timeout=60)
    record = {"schema": 1, "session_id": meta["session_id"], "rom_sha256": meta["rom_sha256"],
              "first_frame": stopped["first_frame"], "last_frame": stopped["frame"],
              "frames": count, "capture_elapsed_ns": stopped["capture_elapsed_ns"],
              "canvas": [256, 192], "playback_hz": hz, "path": str(target),
              "sha256": sha(target), "raw_rgb24": str(raw), "raw_sha256": sha(raw),
              "raw_bytes": raw.stat().st_size, "method": "native DisplayWindow RGB24 callback; unpaused realtime runner",
              "performance": "not_measured_by_capture; use separate ROM probe windows",
              "perceived_fluidity": "not_approved", "audio": "not_recorded",
              "host_load_before": load_before, "host_load_after": os.getloadavg()}
    atomic(target.with_suffix(".json"), record)
    return record

@contextlib.contextmanager
def project_reservation(project):
    """Serializes measurements/publication, not independent functional sessions."""
    key = hashlib.sha256(str(Path(project).resolve()).encode()).hexdigest()
    with open(DEFAULT_ROOT / ("project-" + key + ".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield

@contextlib.contextmanager
def performance_reservation():
    """One cooperating factory performance run per host; load still recorded."""
    DEFAULT_ROOT.mkdir(mode=0o700,exist_ok=True)
    with open(DEFAULT_ROOT / "performance.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield

def sequence(session, steps):
    """Atomic frame-paced script. A completed/aborted script releases controls.
    The returned trace proves VDP duration; ROM readback remains a separate axis.
    """
    if not steps or len(steps)>256: raise ValueError("sequence requires 1..256 steps")
    script=[]
    for s in steps:
        values=[s.get("p1",0),s.get("p2",0),s.get("console",0),s["frames"]]
        if any(not isinstance(v,int) or isinstance(v,bool) for v in values):raise ValueError("integer masks/frames required")
        if not all(0<=v<=m for v,m in zip(values,[63,63,3,36000])):raise ValueError("mask/frame range")
        script.append(":".join(map(str,values)))
    if sum(s["frames"] for s in steps)>36000:raise ValueError("sequence frame budget")
    return request(session,"sequence",",".join(script))

def publish(session, name, directory):
    root, meta = load(session); directory = Path(directory).resolve()
    record = json.loads((root / "evidence" / name).with_suffix(".json").read_text())
    source = root / "evidence" / name
    if record["session_id"] != meta["session_id"] or record["rom_sha256"] != meta["rom_sha256"] or sha(source) != record["sha256"]:
        raise RuntimeError("capture seal mismatch")
    with project_reservation(directory):
        # Each session publishes a distinct immutable bundle. No last-writer wins.
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / meta["session_id"]
        if target.exists(): raise RuntimeError("session already published")
        stage = directory / ("." + meta["session_id"] + ".tmp")
        stage.mkdir()
        shutil.copy2(source, stage / name); atomic(stage / "capture.json", record)
        atomic(stage / "session.json", meta)
        shutil.copy2(root / "emulator/rom.sms",stage / "rom.sms")
        shutil.copy2(root / "emulator/bridge.jar",stage / "bridge.jar")
        shutil.copy2(root / "emulator/ForgeSMS.java",stage / "ForgeSMS.java")
        shutil.copy2(root / "emulator/Emulicious.ini",stage / "Emulicious.ini")
        shutil.copy2(root / "effective-config.ini",stage / "effective-config.ini")
        if (root / "commands.jsonl").exists(): shutil.copy2(root / "commands.jsonl", stage / "commands.jsonl")
        stage.replace(target)
        meta["state"] = "sealed"; meta["published"] = str(target); atomic(root / "session.json", meta)
    return target

def check_bundle(directory):
    """Verify session/ROM/config/artifact binding, not gameplay or FPS claims."""
    root=Path(directory)
    try:
        meta=json.loads((root/"session.json").read_text());record=json.loads((root/"capture.json").read_text())
        checks=[record["session_id"]==meta["session_id"],
                record["rom_sha256"]==meta["rom_sha256"]==sha(root/"rom.sms"),
                record["emulator_process"]==meta["emulator_process"],
                record["display"]==meta["display"],record["display"]!=meta.get("host_display"),
                record["emulator_sha256"]==meta["emulator_sha256"]==SUPPORTED_JAR,
                record["bridge_sha256"]==meta["bridge_sha256"],
                record["bridge_sha256"]==sha(root/"bridge.jar"),
                meta["bridge_source_sha256"]==sha(root/"ForgeSMS.java"),
                record["config_sha256"]==sha(root/"Emulicious.ini"),
                record["effective_config_sha256"]==sha(root/"effective-config.ini"),
                record["captured_at"]>=meta["created_at"],record["canvas"]==[256,192]]
        name=Path(record["path"]).name
        checks.append(sha(root/name)==record["sha256"])
        from PIL import Image
        with Image.open(root/name) as im:
            checks.extend([im.size==(256,192),len(im.getcolors(65536) or [])>=2])
        from capture_evidence import image_informative
        checks.append(image_informative(str(root/name))[0])
        if not all(checks):raise ValueError("session/ROM/capture/config binding mismatch")
        return True,"session-bound informative framebuffer; no gameplay/audio/FPS approval"
    except (OSError,ValueError,KeyError,TypeError) as e:return False,str(e)

def prepare_runtime(xvfb_package,ecj):
    """Private extraction only. Existing host tools are never replaced."""
    if sys.platform!="linux" or platform.machine()!="x86_64":raise RuntimeError("this portable package requires Linux x86_64")
    root=WORKSPACE/"out/session_bridge/runtime";root.mkdir(parents=True,exist_ok=True)
    # Inputs are explicit local packages from the official vendor sites; their
    # hashes and provenance are recorded, not silently fetched on every test.
    xvfb_package=Path(xvfb_package).resolve();ecj=Path(ecj).resolve()
    target=root/"xvfb";target.mkdir(exist_ok=True)
    listing=checked(["tar","--zstd","-tf",xvfb_package]).stdout.splitlines()
    if any(Path(n).is_absolute() or ".." in Path(n).parts for n in listing):raise ValueError("unsafe package member")
    checked(["tar","--zstd","-xf",xvfb_package,"-C",target])
    shutil.copy2(ecj,root/"ecj.jar")
    atomic(root/"provenance.json",{"xvfb_package_sha256":sha(xvfb_package),"ecj_sha256":sha(ecj),
            "xvfb_package_source":str(xvfb_package),"ecj_source":str(ecj),
            "xvfb_vendor":"https://www.x.org/","ecj_vendor":"https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/"})
    checked([target/"usr/bin/Xvfb","-help"])
    return root

def self_check():
    assert set(BUTTONS.values()) == {1, 2, 4, 8, 16, 32}
    assert not alive({"pid": os.getpid(), "start_ticks": "invalid"})
    assert alive(process_record(os.getpid()))
    source = (HERE / "ForgeSMS.java").read_text()
    assert "frameFinished()" in source and "seq <= sequence" in source
    assert "system.peekByte" in source and "pokeByte" not in source
    assert 'SMSButtons.SMSKEY_A_UP' in source
    assert 'mutedArgs[0] = "-muted"' in source
    assert 'if (m.getName().equals("write") && !audioEnabled)' in source
    assert 'm.getName().equals("flush")' in source
    assert 'display.setScreenRecorderStream(stream,true)' in source
    assert 'StandardOpenOption.CREATE_NEW' in source
    for seconds, name in ((0, 'clip'), (31, 'clip'), (True, 'clip'), (2, '../escape')):
        try: realtime_video('unused', seconds, name)
        except ValueError: pass
        else: raise AssertionError('invalid realtime capture request accepted')
    try: sequence("unused",[{"p1":64,"frames":1}])
    except ValueError:pass
    else:raise AssertionError("invalid SMS mask accepted")
    try: sequence("unused",[{"p1":1,"frames":1.5}])
    except ValueError:pass
    else:raise AssertionError("wall-time/noninteger duration accepted")
    print("[OK] isolated session self-check (pure; runtime acceptance separate)")
    return 0

class MemoryReader:
    """Read-only bridge facade for canonical runtime probes (not DAP writes)."""
    def __init__(self,session):self.session=session;self.last_raw="private RAM bridge"
    def read_block(self,addr,n):return request(self.session,"read",addr,n)["ram"]
    def read_byte(self,addr):return self.read_block(addr,1)[0]
    def read_word(self,addr):
        b=self.read_block(addr,2);return b[0]|b[1]<<8
    def cont(self):return request(self.session,"run")
    def pause(self):return request(self.session,"pause")

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="operation", required=True)
    s = sub.add_parser("start"); s.add_argument("rom"); s.add_argument("--xvfb"); s.add_argument("--ecj"); s.add_argument("--ttl", type=int, default=1800)
    for op in ("status", "pause", "run", "close", "step", "input", "read", "capture", "publish", "sequence", "video"):
        q = sub.add_parser(op); q.add_argument("session")
        if op == "step": q.add_argument("frames", type=int)
        if op == "input":
            q.add_argument("--p1", type=int, default=0); q.add_argument("--p2", type=int, default=0); q.add_argument("--console", type=int, default=0)
        if op == "read": q.add_argument("address", type=lambda x: int(x, 0)); q.add_argument("length", type=int)
        if op in ("capture", "publish"): q.add_argument("--name", default="frame.png")
        if op == "publish": q.add_argument("directory")
        if op == "sequence": q.add_argument("script",help="JSON file: list of {p1,p2,console,frames}")
        if op=="video":q.add_argument("--frames",type=int,default=120);q.add_argument("--name",default="video")
    sub.add_parser("self-check")
    s=sub.add_parser("check-bundle");s.add_argument("directory")
    s=sub.add_parser("prepare-runtime");s.add_argument("--xvfb-package",required=True);s.add_argument("--ecj",required=True)
    s = sub.add_parser("_supervise"); s.add_argument("session")
    a = p.parse_args(argv)
    try:
        if a.operation == "start": print(start(a.rom, a.xvfb, a.ecj, a.ttl)); return 0
        if a.operation == "_supervise": supervise(a.session); return 0
        if a.operation == "self-check": return self_check()
        if a.operation == "prepare-runtime": print(prepare_runtime(a.xvfb_package,a.ecj));return 0
        if a.operation == "check-bundle":
            ok,why=check_bundle(a.directory);print(("[PASS] " if ok else "[FAIL] ")+why);return 0 if ok else 1
        if a.operation == "capture": result = capture(a.session, a.name)
        elif a.operation == "publish": result = str(publish(a.session, a.name, a.directory))
        elif a.operation == "sequence": result = sequence(a.session,json.loads(Path(a.script).read_text()))
        elif a.operation == "video":result=video(a.session,a.frames,a.name)
        else:
            args = {"step": lambda: [a.frames], "input": lambda: [a.p1, a.p2, a.console],
                    "read": lambda: [a.address, a.length]}.get(a.operation, lambda: [])()
            result = close_session(a.session) if a.operation == "close" else request(a.session, a.operation, *args)
        print(json.dumps(result, indent=2)); return 0
    except Exception as e:
        print(f"[FAIL_AMBIENTE] {e}", file=sys.stderr); return 2

if __name__ == "__main__": sys.exit(main())
