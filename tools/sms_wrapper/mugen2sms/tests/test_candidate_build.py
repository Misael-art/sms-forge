"""Candidate builds must preserve the selected ROM and reject stale inputs."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "sms_candidate_build", ROOT / "tools/sms_wrapper/build_inner.py"
)
assert SPEC and SPEC.loader
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


def test_candidate_integer_defines_are_deterministic_and_reject_unsafe_values():
    flags = BUILD.candidate_compiler_defines({"defines": {
        "UPLOAD_CHUNK_PAIRS": 4, "LUTA_UPLOAD_TRACE": 1}})
    assert flags == ["-DLUTA_UPLOAD_TRACE=1", "-DUPLOAD_CHUNK_PAIRS=4"]
    for invalid in ({"defines": []}, {"defines": {"": 1}}, {"defines": {1: 1, "X": 1}},
                    {"defines": {"A B": 1}}, {"defines": {"X=1": 2}},
                    {"defines": {"X": "$(echo BAD)"}}, {"defines": {"X": True}},
                    {"defines": {"X": -1}}, {"defines": {"X": 65536}}):
        with pytest.raises(ValueError):
            BUILD.candidate_compiler_defines(invalid)


def test_defines_cannot_change_nominal_build(tmp_path, monkeypatch):
    project = tmp_path / "game"
    (project / ".mddev").mkdir(parents=True)
    (project / ".mddev/project.json").write_text(json.dumps(
        {"name": "game", "toolchain": {"defines": {"LUTA_UPLOAD_TRACE": 1}}}))
    monkeypatch.setattr(BUILD, "pre_gates", lambda *_: pytest.fail("must reject before gates"))
    monkeypatch.setattr(BUILD.sys, "argv", ["build_inner.py", "--project", str(project)])
    assert BUILD.main() == 1
    assert not (project / "out").exists()


def test_candidate_directory_is_new_and_cannot_escape(tmp_path):
    project = tmp_path / "game"
    root = project / "out/candidates"
    root.mkdir(parents=True)
    candidate = root / "first"
    assert Path(BUILD.reserve_candidate_dir(str(project), str(candidate))) == candidate
    marker = candidate / "keep"
    marker.write_text("existing evidence")
    with pytest.raises(ValueError, match="ja existe"):
        BUILD.reserve_candidate_dir(str(project), str(candidate))
    with pytest.raises(ValueError, match="out/candidates"):
        BUILD.reserve_candidate_dir(str(project), str(project / "out/rom"))
    (root / "escape").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="out/candidates"):
        BUILD.reserve_candidate_dir(str(project), str(root / "escape/other"))
    assert marker.read_text() == "existing evidence"


def test_declared_include_directory_stays_inside_project(tmp_path):
    project = tmp_path / "game"
    (project / "out/generated/pack").mkdir(parents=True)
    config = {"toolchain": {"include_dirs": ["out/generated/pack"]}}
    assert BUILD.project_include_dirs(str(project), config) == [str(project / "out/generated/pack")]
    for path in ("../outside", str(tmp_path), "out/missing"):
        with pytest.raises(ValueError):
            BUILD.project_include_dirs(str(project), {"toolchain": {"include_dirs": [path]}})
    (project / "out/generated/link").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="dentro do projeto"):
        BUILD.project_include_dirs(str(project), {"toolchain": {"include_dirs": ["out/generated/link"]}})


def test_candidate_inputs_hash_include_and_banked_data(tmp_path, monkeypatch):
    project = tmp_path / "game"
    (project / ".mddev").mkdir(parents=True)
    (project / "src").mkdir()
    (project / "generated data").mkdir()
    (project / ".mddev/project.json").write_text("{}")
    src = project / "src/main.c"
    src.write_text("/* source */")
    header = project / "generated data/pose.h"
    header.write_text("header v1")
    bank = project / "generated data/bank.bin"
    bank.write_bytes(b"bank v1")
    tc = {}
    for name in ("sdcc", "makesms", "SMSlib.lib", "PSGlib.lib", "crt0_sms.rel"):
        path = tmp_path / name
        path.write_bytes(name.encode())
        tc[name] = str(path)
    tc["inc"] = []
    for name in ("sdcpp", "sdasz80", "sdldz80", "z80.lib"):
        (tmp_path / name).write_bytes(name.encode())

    seen_commands = []

    def sdcc_output(command, **kwargs):
        seen_commands.append(command)
        if "--print-search-dirs" in command:
            output = f"programs:\n{tmp_path}\nlibdir:\n{tmp_path}\n"
        else:
            output = "main.o: src/main.c generated\\ data/pose.h\n"
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(BUILD.subprocess, "run", sdcc_output)
    manifest = {"toolchain": {"makesms_extra": ["-mbank", "generated data/bank.bin:0:1:2"]}}
    before = BUILD.candidate_inputs(str(project), manifest, tc, [str(src)])
    assert before["generated data/pose.h"] == hashlib.sha256(header.read_bytes()).hexdigest()
    assert before["generated data/bank.bin"] == hashlib.sha256(bank.read_bytes()).hexdigest()
    with_defines = {"toolchain": {"defines": {"LUTA_UPLOAD_TRACE": 1},
                                  "makesms_extra": ["-mbank", "generated data/bank.bin:0:1:2"]}}
    BUILD.candidate_inputs(str(project), with_defines, tc, [str(src)])
    assert any("-M" in command and "-DLUTA_UPLOAD_TRACE=1" in command
               for command in seen_commands)
    bank.write_bytes(b"changed bank")
    assert before != BUILD.candidate_inputs(str(project), manifest, tc, [str(src)])
    padded = {"toolchain": {"makesms_extra": ["-pp", "-mbank", "generated data/bank.bin:0:1:2"]}}
    assert BUILD.candidate_inputs(str(project), padded, tc, [str(src)])["generated data/bank.bin"] == \
           hashlib.sha256(bank.read_bytes()).hexdigest()
    for unsupported in ({"link_extra": ["unknown.lib"]},
                        {"makesms_extra": ["-unknown"]},
                        {"makesms_extra": ["-pm", "-pp"]},
                        {"makesms_extra": ["-mbank"]}):
        with pytest.raises(ValueError):
            BUILD.candidate_inputs(str(project), {"toolchain": unsupported}, tc, [str(src)])
    bank.unlink()
    with pytest.raises(ValueError, match="entrada de build ausente"):
        BUILD.candidate_inputs(str(project), manifest, tc, [str(src)])


@pytest.mark.parametrize("changed", [False, True])
def test_candidate_build_never_publishes_nominal_or_stale_record(tmp_path, monkeypatch, changed):
    project = tmp_path / "game"
    for folder in (".mddev", "src", "out/rom", "changelog/roms"):
        (project / folder).mkdir(parents=True)
    (project / ".mddev/project.json").write_text(json.dumps(
        {"name": "game", "toolchain": {"defines": {"LUTA_UPLOAD_TRACE": 1}}}))
    (project / "src/main.c").write_text("void main(void) {}")
    nominal_rom = project / "out/rom/game.sms"
    nominal_rom.write_bytes(b"original")
    nominal_record = project / "out/build_record.json"
    nominal_record.write_text("original record")
    candidate = project / "out/candidates/test"
    tc = {"sdcc": "sdcc", "makesms": "makesms", "inc": [], "peep": "",
          "crt0_sms.rel": "crt0", "SMSlib.lib": "sms", "PSGlib.lib": "psg"}
    monkeypatch.setattr(BUILD, "pre_gates", lambda p: [])
    monkeypatch.setattr(BUILD, "find_toolchain", lambda: (tc, ""))
    manifest_hash = hashlib.sha256((project / ".mddev/project.json").read_bytes()).hexdigest()
    snapshots = iter([{"src/main.c": "before", ".mddev/project.json": manifest_hash},
                      {"src/main.c": "after" if changed else "before",
                       ".mddev/project.json": manifest_hash}])
    monkeypatch.setattr(BUILD, "candidate_inputs", lambda *a: next(snapshots))

    seen_commands = []

    def run(command, cwd=None, **kwargs):
        seen_commands.append(command)
        if "--version" in command:
            return SimpleNamespace(returncode=0, stdout="SDCC fake", stderr="")
        if command[0] == "sdcc":
            output = Path(cwd) / command[command.index("-o") + 1]
            output.write_bytes(b"object or linked image")
        else:
            output = Path(cwd) / command[-1]
            output.write_bytes(b"candidate ROM")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(BUILD.subprocess, "run", run)
    monkeypatch.setattr(BUILD.sys, "argv", ["build_inner.py", "--project", str(project),
                                            "--build-dir", str(candidate)])
    assert BUILD.main() == (1 if changed else 0)
    assert any("-c" in command and "-DLUTA_UPLOAD_TRACE=1" in command
               for command in seen_commands)
    record = candidate / "build_record.json"
    if changed:
        assert not record.exists()
    else:
        doc = json.loads(record.read_text())
        assert doc["rom_sha256"] == hashlib.sha256(b"candidate ROM").hexdigest()
        assert doc["axes"]["build"] and not doc["axes"]["boot_emulador"]
        assert doc["profile"] == "candidate_unpromoted"
        assert doc["compiler_defines"] == ["-DLUTA_UPLOAD_TRACE=1"]
    assert nominal_rom.read_bytes() == b"original"
    assert nominal_record.read_text() == "original record"
    assert not list((project / "changelog/roms").iterdir())


def test_changed_manifest_between_parse_and_snapshot_never_builds(tmp_path, monkeypatch):
    project = tmp_path / "game"
    (project / ".mddev").mkdir(parents=True)
    (project / "src").mkdir()
    manifest = project / ".mddev/project.json"
    manifest.write_text(json.dumps({"name": "game"}))
    (project / "src/main.c").write_text("void main(void) {}")
    monkeypatch.setattr(BUILD, "pre_gates", lambda p: [])

    def change_manifest():
        manifest.write_text(json.dumps({"name": "game", "toolchain": {"optimization": "code_size"}}))
        return ({"sdcc": "fake"}, "")

    monkeypatch.setattr(BUILD, "find_toolchain", change_manifest)
    monkeypatch.setattr(BUILD, "candidate_inputs", lambda *a: {
        ".mddev/project.json": hashlib.sha256(manifest.read_bytes()).hexdigest()})
    monkeypatch.setattr(BUILD.subprocess, "run", lambda *a, **kw: pytest.fail("must not compile"))
    candidate = project / "out/candidates/changed"
    monkeypatch.setattr(BUILD.sys, "argv", ["build_inner.py", "--project", str(project),
                                            "--build-dir", str(candidate)])
    assert BUILD.main() == 1
    assert not (candidate / "build_record.json").exists()
    assert not (candidate / "rom").exists()


def test_failed_power_of_two_padding_never_publishes_candidate_receipt(tmp_path, monkeypatch):
    project = tmp_path / "game"
    for folder in (".mddev", "src", "out/rom"):
        (project / folder).mkdir(parents=True)
    manifest = project / ".mddev/project.json"
    manifest.write_text(json.dumps({"name": "game", "toolchain": {"makesms_extra": ["-pp"]}}))
    (project / "src/main.c").write_text("void main(void) {}")
    nominal = project / "out/rom/game.sms"
    nominal.write_bytes(b"original")
    tc = {"sdcc": "sdcc", "makesms": "makesms", "inc": [], "peep": "",
          "crt0_sms.rel": "crt0", "SMSlib.lib": "sms", "PSGlib.lib": "psg"}
    monkeypatch.setattr(BUILD, "pre_gates", lambda p: [])
    monkeypatch.setattr(BUILD, "find_toolchain", lambda: (tc, ""))
    manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    monkeypatch.setattr(BUILD, "candidate_inputs", lambda *a: {".mddev/project.json": manifest_hash})

    def run(command, cwd=None, **kwargs):
        if command[0] == "sdcc":
            (Path(cwd) / command[command.index("-o") + 1]).write_bytes(b"linked")
        else:
            (Path(cwd) / command[-1]).write_bytes(b"not a power of two")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(BUILD.subprocess, "run", run)
    candidate = project / "out/candidates/bad-padding"
    monkeypatch.setattr(BUILD.sys, "argv", ["build_inner.py", "--project", str(project),
                                            "--build-dir", str(candidate)])
    assert BUILD.main() == 1
    assert not (candidate / "build_record.json").exists()
    assert nominal.read_bytes() == b"original"
