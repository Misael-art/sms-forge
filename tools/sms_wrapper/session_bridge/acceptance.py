"""Reproducible real-ROM acceptance; artifacts are diagnostic, not delivery.

Does not type on the user's desktop or close unrelated emulators.
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import sys
import time
import socket
import shutil
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_inner import find_toolchain
from session_bridge.isolated import HERE, EMULATOR, checked, sha, start, request, capture, publish, atomic, self_check,sequence,video,check_bundle,close_session

def build_probes(directory):
    tc, error = find_toolchain()
    if error: raise RuntimeError(error)
    directory = Path(directory).resolve(); directory.mkdir(parents=True, exist_ok=True)
    roms = []
    for i in (1, 2):
        obj = directory / f"probe{i}.rel"; ihx = directory / f"probe{i}.ihx"; rom = directory / f"probe{i}.sms"
        peep = ["--peep-file", tc["peep"]] if Path(tc["peep"]).exists() else []
        checked([tc["sdcc"], "-c", "-mz80", *peep, *["-I"+p for p in tc["inc"]],
                 "-DPROBE_ID="+str(i), "-o", obj, HERE / "controls_probe.c"])
        checked([tc["sdcc"], "-mz80", "--no-std-crt0", "--data-loc", "0xC000", "-o", ihx,
                 tc["crt0_sms.rel"], obj, tc["SMSlib.lib"], tc["PSGlib.lib"]])
        checked([tc["makesms"], ihx, rom]); roms.append(rom)
    return roms

def probe(session):
    data = request(session, "read", 0xC700, 34)["ram"]
    if bytes(data[:4]) != b"SMI1": raise AssertionError("ROM probe magic missing")
    word = lambda n: data[n] | data[n+1] << 8
    return {"id": data[4], "frame": word(5), "keys": word(7), "pause": data[9],
            "held": [word(i) for i in range(10,34,2)]}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True); p.add_argument("--xvfb", required=True); p.add_argument("--ecj")
    a=p.parse_args(argv); out=Path(a.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    self_check(); roms=build_probes(out / "roms")
    shared_before=sha(EMULATOR / "Emulicious.ini")
    sessions=[]; results={"schema":1,"purpose":"isolated_controls_diagnostic","checks":{},"audio":"not_validated","performance":"not_measured"}
    try:
        for rom in roms: sessions.append(start(rom,a.xvfb,a.ecj))
        s1,s2=sessions
        info=[json.loads((s/"session.json").read_text()) for s in sessions]
        for s,m in zip(sessions,info):
            assert m["audio_boot"]["muted_from_launch"] and not m["audio_boot"]["ready_audio_enabled"]
            assert not request(s,"status")["running"]
        results["checks"]["muted_boot_paused_start"]="pass"
        assert info[0]["display"]!=info[1]["display"]
        assert info[0]["emulator_process"]["pid"]!=info[1]["emulator_process"]["pid"]
        assert probe(s1)["id"]==1 and probe(s2)["id"]==2
        assert request(s1,"sram")["sram"][0]==1 and request(s2,"sram")["sram"][0]==2
        results["checks"]["two_distinct_roms_displays_processes"]="pass"
        results["checks"]["separate_sram_rom_observed_writes"]="pass"
        before=[probe(s) for s in sessions]
        def hold(s,p1,p2,n):
            request(s,"input",p1,p2,0); request(s,"step",n); value=probe(s)
            request(s,"input",0,0,0); request(s,"step",2); return value
        with concurrent.futures.ThreadPoolExecutor() as pool:
            f1=pool.submit(hold,s1,16,8,17);f2=pool.submit(hold,s2,4,32,29)
            after=[f1.result(),f2.result()]
        for b,v,n,mask in zip(before,after,[17,29],[16|(8<<6),4|(32<<6)]):
            assert v["keys"]==mask, (v,mask)
            assert (v["frame"]-b["frame"])&65535==n,(v,b,n)
            for i in range(12):
                assert (v["held"][i]-b["held"][i])&65535==(n if mask&(1<<i) else 0),(i,v,b)
        results["checks"]["parallel_exact_17_29_frames_no_cross_input"]="pass"
        results["rom_observations"]={"before":before,"after":after}
        for s in sessions:
            for port in (0,1):
                for bit in (1,2,4,8,16,32):
                    value=hold(s,bit if port==0 else 0,bit if port==1 else 0,3)
                    assert value["keys"]==bit<<(6*port),(port,bit,value)
        results["checks"]["all_six_sms_controls_both_ports_both_roms"]="pass"
        for s in sessions:
            before_pause=probe(s)["pause"]
            request(s,"input",0,0,1);request(s,"step",3)
            assert probe(s)["pause"]==before_pause+1
            request(s,"input",0,0,0);request(s,"step",2)
        results["checks"]["console_pause_nmi"]="pass"
        for s in sessions:
            def raw(sid,token,seq,op):
                with socket.socket(socket.AF_UNIX) as sock:
                    sock.settimeout(5);sock.connect(str(s/"control.sock"))
                    sock.sendall(f"{sid} {token} {seq} {op}\n".encode())
                    return json.loads(sock.recv(4096))
            sid=s.name;token=(s/"token").read_text().strip();seq=int((s/"sequence").read_text())
            assert raw("wrong",token,seq+1,"status")["ok"] is False
            assert raw(sid,"wrong",seq+1,"status")["ok"] is False
            assert raw(sid,token,seq,"status")["ok"] is False
            request(s,"status")
            before_script=probe(s)
            script=sequence(s,[{"p1":2,"frames":4},{"p1":10,"frames":4},{"p1":24,"frames":3}])
            assert [t["end"]-t["begin"] for t in script["trace"]]==[4,4,3]
            assert script["p1"]==script["p2"]==0
            after_script=probe(s)
            assert (after_script["frame"]-before_script["frame"])&65535==11
        results["checks"]["wrong_session_token_stale_sequence_rejected"]="pass"
        results["checks"]["atomic_frame_script_release_and_rom_count"]="pass"
        # Host keyboard-like events injected only into the test's private
        # display. They must not reach the process-local gameplay providers.
        for s,m in zip(sessions,info):
            env={"DISPLAY":m["display"],"XAUTHORITY":str(s/"Xauthority")}
            windows=checked(["xdotool","search","--pid",str(m["emulator_process"]["pid"])],env=env).stdout.split()
            assert windows,"owned emulator window absent"
            checked(["xdotool","key","--window",windows[-1],"Up","Down","Left","Right","a","s","Return"],env=env)
            request(s,"step",5);assert probe(s)["keys"]==0
            # Device denial is checked inside each target namespace, not
            # inferred from an empty host device list.
            assert not Path(f'/proc/{m["emulator_process"]["pid"]}/root/dev/input').exists()
            assert not Path(f'/proc/{m["emulator_process"]["pid"]}/root/dev/uinput').exists()
        results["checks"]["private_keyboard_events_do_not_change_rom_input"]="pass"
        results["checks"]["physical_device_paths_hidden_in_target"]="pass"
        results["physical_joystick_hotplug"]="not_exercised; structural device denial verified"
        results["host_desktop_typing"]="not_injected; host focus untouched"
        record=video(s1,12,"diagnostic_video")
        assert record["distinct_frames"]>=10 and record["last_frame"]-record["first_frame"]==12
        shutil.copy2(record["path"],out/"diagnostic_video.mp4")
        atomic(out/"diagnostic_video.json",record)
        results["checks"]["video_one_framebuffer_per_vdp_frame"]="pass"
        checked([sys.executable,str(HERE.parent/"measure_runtime_probe.py"),"--session",s1,
                 "--project",out,"--seconds","3.2","--janelas","2"])
        metrics=json.loads((out/"out/evidence/sessions"/s1.name/"runtime/runtime_probe.json").read_text())
        assert metrics["axes"]["aprovado"] and metrics["session_id"]==s1.name
        results["performance"]={"scope":"controls diagnostic only","fps_janelas":metrics["fps_janelas"],"host_load":metrics["host_load"]}
        results["checks"]["canonical_runtime_probe_private_realtime_route"]="pass"
        captures=[]
        for i,s in enumerate(sessions):
            request(s,"input",16 if i==0 else 4,8 if i==0 else 32,0);request(s,"step",4)
            record=capture(s);captures.append(record)
            bundle=publish(s,"frame.png",out/"bundles")
            assert check_bundle(bundle)[0]
            original=(bundle/"rom.sms").read_bytes()
            (bundle/"rom.sms").write_bytes(b"wrong ROM")
            assert not check_bundle(bundle)[0]
            (bundle/"rom.sms").write_bytes(original)
        assert captures[0]["sha256"]!=captures[1]["sha256"]
        results["captures"]=captures
        results["checks"]["separate_informative_framebuffers_and_seals"]="pass"
        results["checks"]["bundle_rejects_changed_rom"]="pass"
        close_session(s1)
        try: request(s1,"input",16,0,0)
        except RuntimeError: pass
        else: raise AssertionError("closed session accepted input")
        request(s2,"input",0,0,0);request(s2,"step",5);assert probe(s2)["keys"]==0
        results["checks"]["owned_shutdown_other_session_survives"]="pass"
        results["checks"]["closed_session_rejected"]="pass"
        results["status"]="pass"
    except Exception as e:
        results["status"]="fail";results["error"]=str(e);raise
    finally:
        for s in sessions:
            try: close_session(s)
            except (RuntimeError,OSError): pass
        results["session_paths"]=list(map(str,sessions))
        results["shared_config_before"]=shared_before
        results["shared_config_after"]=sha(EMULATOR/"Emulicious.ini")
        results["checks"]["shared_config_unchanged"]="pass" if results["shared_config_after"]==shared_before else "fail"
        atomic(out/"acceptance.json",results)
    print(json.dumps(results,indent=2));return 0

if __name__=="__main__":sys.exit(main())
