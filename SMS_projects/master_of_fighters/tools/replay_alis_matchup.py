"""Observe the public matchup, original Battle music, and both sound hardware profiles."""
import argparse
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

from replay_alis_chapter import PROJECT, capture_session, isolated


def verify_names_and_costume(path):
    with Image.open(path) as capture:
        frame = capture.convert("RGB")
    first = frame.crop((104,32,165,52))
    second = frame.crop((176,64,237,84))
    assert len(first.getcolors()) >= 3
    assert ImageChops.difference(first,second).getbbox() is None, "Name lettering differs"
    face = ImageOps.mirror(frame.crop((16,6,96,84)))
    opponent = frame.crop((160,86,240,164))
    differences = [(a,b) for a,b in zip(face.getdata(),opponent.getdata()) if a != b]
    green = {(0,170,85), (0,255,170)}
    assert {b for _,b in differences} == green
    assert ImageChops.difference(face,opponent).getbbox()[1] >= 60
    return {"name_ink_pixels":[59,20], "costume_pixels_compared":len(differences)}


def animate_camera(out):
    names = ["versus", *(f"camera-{i:02}" for i in range(1,21))]
    frames = []
    for name in names:
        with Image.open(out/(name+".png")) as frame:
            frames.append(frame.convert("RGB").resize((512,384), Image.Resampling.NEAREST))
    # Full first/last exposure on the automatic route, at the NTSC VDP cadence.
    frames[0].save(out/"versus.gif", save_all=True, append_images=frames[1:],
                   duration=[280, *([50] * 19), 320], loop=0, disposal=1)


def verify(build, bank, out, case):
    out.mkdir(parents=True, exist_ok=False)
    receipt=json.loads((build/"build_record.json").read_text())
    rom=PROJECT/receipt["rom_path"]
    assert isolated.sha(rom)==receipt["rom_sha256"]
    symbols=(build/"obj/master_of_fighters.map").read_text()
    def address(name):
        return int(re.search(r"^\s*([0-9A-F]{8})\s+_"+name+r"\s+",symbols,re.M)[1],16)
    backend,chapter=address("mof_battle_backend"),address("chapter")
    offsets=(build/"obj/alis_chapter.sym").read_text()
    def data_offset(name):
        return int(re.search(r"^\s*1 _"+name+r"\s+([0-9A-F]{8}) [GR]+$",offsets,re.M)[1],16)
    cursor=chapter-data_offset("chapter")+data_offset("battle_cursor")
    fm=case!="psg"
    isolated.DEFAULT_ROOT=PROJECT.parents[1]/".runtime/qa"
    session=isolated.start(rom,sms_fm=fm)
    log=dict(session_id=session.name,rom_sha256=receipt["rom_sha256"],case=case,
             sms_fm=fm,observations=[])
    def pad(mask,frames):
        return isolated.sequence(session,[dict(p1=mask,p2=0,frames=frames)])
    def press(mask):
        pad(mask,4);pad(0,14)
    def read(addr,n):
        return bytes(isolated.request(session,"read",addr,n)["ram"])
    def capture(label,position=None):
        result=isolated.capture(session,label+".png")
        file=Path(result["path"])
        for suffix in (".png",".json"):
            shutil.copyfile(file.with_suffix(suffix),out/file.with_suffix(suffix).name)
        if position is not None:
            reference = bank / ("versus.png" if position == 0 else f"versus-{position:02}.png")
            with Image.open(file) as screen,Image.open(reference) as expected:
                assert screen.size==expected.size==(256,192)
                difference = ImageChops.difference(screen.convert("RGB"), expected.convert("RGB")).getbbox()
                assert difference is None, (label, position, difference)
        return result["sha256"]
    def observe(tag):
        ch=read(chapter,16)
        row=dict(label=tag,frame=isolated.request(session,"status")["frame"],
                 story=ch[0],music=ch[1],phase=ch[5],backend=read(backend,1)[0])
        log["observations"].append(row)
        return row
    try:
        pad(0,145)
        pan_index = address("mof_pan_index")
        assert read(pan_index,1)[0] == 20
        log["boot_screen"]=capture("abertura",20)
        log["art"] = verify_names_and_costume(out/"abertura.png")
        press(16)
        if case=="mute":
            press(1);press(16);press(8);press(32)
        if case=="story":
            press(16);press(32)
        else:
            press(1 if case=="mute" else 2);press(16)
            log["versus_screen"]=capture("versus",0)
            row=observe("apresentacao")
            assert row["backend"]=={"fm":2,"psg":1,"mute":0}[case]
            if case == "fm":
                end_line = address("mof_pan_end_line")
                spills = address("mof_pan_spills")
                log["camera"] = []
                for step in range(1,21):
                    for _ in range(23):
                        if read(pan_index,1)[0] == step:
                            break
                        pad(0,1)
                    pad(0,1)
                    assert read(pan_index,1)[0] == step, step
                    entry = dict(step=step, end_line=read(end_line,1)[0], spills=read(spills,1)[0])
                    log["camera"].append(entry)
                    entry["sha256"] = capture(f"camera-{step:02}",step)
                    assert entry["spills"] == 0, entry
                animate_camera(out)
            if case=="psg":press(16)  # skip, independent of the automatic route
        pad(0,220)
        row=observe("arena")
        assert row["phase"]==2 and row["story"]==(case=="story")
        assert row["music"]==(case!="mute")
        assert row["backend"]==(0 if case=="mute" else 2 if fm else 1)
        log["arena_screen"]=capture("arena")
        if case in ("fm","psg"):
            assert capture_session(session,6,"battle")==0
            for name in ("battle.wav","battle.audio.json"):
                shutil.copyfile(session/name,out/name)
            log["wav_sha256"]=isolated.sha(out/"battle.wav")
            if case=="fm":
                positions=[int.from_bytes(read(cursor,2),"little")]
                for _ in range(9):
                    pad(0,195)
                    positions.append(int.from_bytes(read(cursor,2),"little"))
                limit = 0x8000 + json.loads((bank/"sources.json").read_text())["FM"]["bytes"]
                assert all(0x8000 <= pos < limit for pos in positions)
                assert any(a>b for a,b in zip(positions,positions[1:]))
                log["cursor_fm"]=positions
                assert observe("apos_uma_volta")["backend"]==2
                assert capture_session(session,4,"battle_loop")==0
                shutil.copyfile(session/"battle_loop.wav",out/"battle_loop.wav")
                shutil.copyfile(session/"battle_loop.audio.json",out/"battle_loop.audio.json")
        log["passed"]=True
    finally:
        isolated.close_session(session)
        log["closed"]=isolated.load(session)[1]["state"]
        shutil.copyfile(session/"commands.jsonl",out/"commands.jsonl")
        isolated.atomic(out/"observations.json",log)


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for key in ("build","bank","out"):
        cli.add_argument(key,type=Path)
    cli.add_argument("--case",choices=("fm","psg","mute","story"),required=True)
    args=cli.parse_args()
    verify(args.build,args.bank,args.out,args.case)
