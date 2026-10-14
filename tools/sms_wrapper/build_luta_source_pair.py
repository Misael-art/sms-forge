#!/usr/bin/env python3
"""Build an isolated integrated-runtime clone from a generated MUGEN pair cut.

All source-derived bytes stay in the ignored local-study output. The wrapper
copies the integrated runtime, binds the cut's pose metadata and command source,
then builds and checks the ROM's RAM and mapper banks.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "SMS_projects" / "luta_mugen"
INTEGRATED = PROJECT / "integrada"
RUNTIME_SOURCE = INTEGRATED
WRAPPER = ROOT / "tools" / "sms_wrapper"
sys.path.insert(0, str(WRAPPER))
from mugen2sms.generators.integrated_runtime_data import namespace_slot_actors

PAGE_BYTES = 16384
AUDIO_STEMS = ("music_battle", "sfx_round", "sfx_shot", "sfx_hit", "sfx_down")
HAND_HEADERS = (
    "fight.h", "input.h", "input_pad.h", "input_tier.h", "cpu_controller.h",
    "body.h", "luta.h", "stream.h", "stage.h", "hud.h", "audio.h",
    "trace_hooks.h",
)


def run(command: list[str], cwd: Path = ROOT) -> None:
    print("+", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=cwd)
    if result.returncode:
        raise SystemExit(result.returncode)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_audio_blobs(destination: Path) -> None:
    """Use the canonical provenance gate, or clearly mark a local-only fallback.

    The fallback is limited to EIO from the project manifest. It binds the raw
    .psg bytes into this diagnostic ROM and records their hashes, but it does
    not claim that those bytes satisfy the unreadable provenance contract.
    """
    manifest = PROJECT / "doc" / "audio_provenance_manifest.json"
    try:
        manifest.read_text(encoding="utf-8")
    except OSError as exc:
        if exc.errno != errno.EIO:
            raise
        header = [
            "/* local diagnostic fallback: audio provenance manifest unreadable */",
            "#ifndef PSG_BLOBS_H", "#define PSG_BLOBS_H",
        ]
        inputs = []
        for stem in AUDIO_STEMS:
            path = PROJECT / "res" / "audio" / f"{stem}.psg"
            data = path.read_bytes()
            if not data:
                raise SystemExit(f"[FAIL] PSG diagnostic source is empty: {path}")
            header.append(f"static const unsigned char {stem}[{len(data)}] = {{")
            for index in range(0, len(data), 16):
                chunk = ", ".join(f"0x{byte:02X}" for byte in data[index:index + 16])
                header.append(f"    {chunk},")
            header.append("};")
            inputs.append({
                "file": path.relative_to(PROJECT).as_posix(),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })
        header.extend(["#endif", ""])
        (destination / "inc" / "psg_blobs.h").write_text(
            "\n".join(header), encoding="utf-8")
        scope = {
            "schema": "local_audio_build_scope_v1",
            "status": "embedded_provenance_unverified",
            "manifest": manifest.relative_to(PROJECT).as_posix(),
            "manifest_error": str(exc),
            "input_hashes": inputs,
            "audio_emulator_validation": "not_run",
            "claims": {"provenance_verified": False, "audio_capture_passed": False},
        }
        (destination / "out" / "audio_build_scope.json").write_text(
            json.dumps(scope, indent=2) + "\n", encoding="utf-8")
        print("[UNVERIFIED_AUDIO] current PSG bytes embedded for local build; "
              "provenance remains blocked by manifest I/O", flush=True)
        return

    run([sys.executable, str(WRAPPER / "luta_mugen_gen_psg_blobs.py"),
         "--project", str(PROJECT), "--out", str(destination / "inc" / "psg_blobs.h")])


def mapper_layout(source_pages: int, meta_pages: int,
                  first_bank: int = 2) -> tuple[int, int]:
    if source_pages <= 0 or meta_pages <= 0:
        raise ValueError("source and metadata images must contain at least one page")
    meta_first = first_bank + source_pages
    last_bank = meta_first + meta_pages - 1
    if first_bank < 2 or last_bank > 255:
        raise ValueError(f"mapper page range {first_bank}..{last_bank} is invalid")
    return meta_first, source_pages + meta_pages


def source_hashes_by_actor(source_hashes: object) -> tuple[str, str]:
    """Return the independently declared P1/P2 source package hashes."""
    if not isinstance(source_hashes, dict):
        raise ValueError("pair cut must declare source_sha256 by actor")
    p1 = source_hashes.get("p1_ken")
    p2 = source_hashes.get("p2_ryu")
    if not isinstance(p1, str) or len(p1) != 64:
        raise ValueError("pair cut has no valid p1_ken source SHA-256")
    if not isinstance(p2, str) or len(p2) != 64:
        raise ValueError("pair cut has no valid p2_ryu source SHA-256")
    return p1, p2


def copy_tree(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)


def prepare_project(destination: Path, project_name: str) -> None:
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit(f"output already contains files; choose a new path: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    for name in (".mddev", "src", "inc", "assets", "tools", "trace",
                 "experimental", "res"):
        copy_tree(RUNTIME_SOURCE / name, destination / name)
    for name in ("out", "changelog", "doc"):
        (destination / name).mkdir(parents=True, exist_ok=True)
    manifest_path = destination / ".mddev" / "project.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = project_name
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def set_mapper_asset(project_json: Path, image_pages: int) -> None:
    manifest = json.loads(project_json.read_text(encoding="utf-8"))
    extra = manifest["toolchain"].get("makesms_extra", [])
    kept: list[str] = []
    index = 0
    while index < len(extra):
        arg = extra[index]
        if arg == "-mbank":
            index += 2
            continue
        if arg.startswith("assets/banks/banks_integrada.bin:"):
            index += 1
            continue
        kept.append(arg)
        index += 1
    kept.extend(["-mbank", f"assets/banks/banks_integrada.bin:0:{image_pages}:2"])
    manifest["toolchain"]["makesms_extra"] = kept
    project_json.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build(cut_dir: Path, config_p1: Path, config_p2: Path,
          source_p1: Path, source_p2: Path, destination: Path) -> Path:
    cut_dir = cut_dir.resolve()
    destination = destination.resolve()
    cut_manifest_path = cut_dir / "versus_scene_manifest.json"
    runtime_header = cut_dir / "versus_scene_runtime.h"
    source_image = cut_dir / "versus_scene_banks_02.bin"
    p1_manifest_path = cut_dir / "p1_ken" / "ken_scene_manifest.json"
    p2_manifest_path = cut_dir / "p2_ryu" / "ken_scene_manifest.json"
    required = (cut_manifest_path, runtime_header, source_image,
                p1_manifest_path, p2_manifest_path,
                config_p1, config_p2, source_p1, source_p2)
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("missing pair-cut input(s): " + ", ".join(missing))

    cut_manifest = json.loads(cut_manifest_path.read_text(encoding="utf-8"))
    try:
        p1_source_hash, p2_source_hash = source_hashes_by_actor(
            cut_manifest.get("source_sha256"))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    for label, path, source_hash in (
            ("P1", source_p1, p1_source_hash),
            ("P2", source_p2, p2_source_hash)):
        if sha256(path) != source_hash:
            raise SystemExit(f"{label} command source SHA diverges from the cut")
    for label, path, source_hash in (
            ("P1", config_p1, p1_source_hash),
            ("P2", config_p2, p2_source_hash)):
        config = json.loads(path.read_text(encoding="utf-8"))
        if config.get("source_sha256") != source_hash:
            raise SystemExit(f"{label} cut config SHA diverges from the scene cut")
    for label, path, source_hash in (
            ("P1", p1_manifest_path, p1_source_hash),
            ("P2", p2_manifest_path, p2_source_hash)):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("source_sha256") != source_hash:
            raise SystemExit(f"{label} slot manifest SHA diverges from the scene cut")

    source_bytes = source_image.read_bytes()
    if len(source_bytes) % PAGE_BYTES:
        raise SystemExit("source bank image is not a whole number of 16 KiB pages")
    source_pages = len(source_bytes) // PAGE_BYTES
    meta_first, _expected_total_pages = mapper_layout(source_pages, 1)
    prepare_project(destination, destination.name)
    inc = destination / "inc"
    banks = destination / "assets" / "banks"
    banks.mkdir(parents=True, exist_ok=True)
    # The integrated bank readers name slots KEN/RYU. Scene-cut data is
    # generated as P1/P2, so rename only those C identifier prefixes before
    # running the established frame/pose packers.
    runtime_text = namespace_slot_actors(runtime_header.read_text(encoding="ascii"))
    integrated_header = inc / "versus_scene_runtime_full_generated.h"
    integrated_header.write_text(runtime_text, encoding="ascii")

    run([sys.executable, str(WRAPPER / "luta_mugen_gen_stage_hud.py"),
         "--project", str(PROJECT), "--out-dir", str(inc), "--check-planta"])
    run([sys.executable, str(WRAPPER / "mugen2sms" / "generators" / "pose_table.py"),
         "--header", str(integrated_header),
         "--banks", str(source_image), "--out", str(inc / "pose_table.h"),
         "--bank-out", str(banks / f"pose_meta_{meta_first}.bin")])
    meta_blob = banks / f"pose_meta_{meta_first}.bin"
    if len(meta_blob.read_bytes()) % PAGE_BYTES:
        raise SystemExit("generated metadata is not aligned to 16 KiB pages")
    meta_pages = len(meta_blob.read_bytes()) // PAGE_BYTES
    actual_meta_first, total_pages = mapper_layout(source_pages, meta_pages)
    if actual_meta_first != meta_first:
        raise SystemExit("metadata generator changed its physical bank start")
    first_frame_bank = actual_meta_first + meta_pages
    frame_data_blob = banks / f"frame_data_{first_frame_bank}.bin"
    frame_data_header = inc / "source_frame_data.h"
    run([sys.executable, str(WRAPPER / "mugen2sms" / "generators" / "source_frame_data.py"),
         "--header", str(integrated_header),
         "--first-bank", str(first_frame_bank),
         "--out-header", str(frame_data_header),
         "--out-banks", str(frame_data_blob)])
    if len(frame_data_blob.read_bytes()) % PAGE_BYTES:
        raise SystemExit("generated frame data is not aligned to 16 KiB pages")
    frame_data_pages = len(frame_data_blob.read_bytes()) // PAGE_BYTES
    total_pages += frame_data_pages
    index_bank = first_frame_bank + frame_data_pages
    pose_index_blob = banks / f"pose_index_{index_bank}.bin"
    run([sys.executable, str(WRAPPER / "mugen2sms" / "generators" / "pose_table.py"),
         "--header", str(integrated_header),
         "--banks", str(source_image), "--out", str(inc / "pose_table.h"),
         "--bank-out", str(meta_blob), "--index-bank", str(index_bank),
         "--index-out", str(pose_index_blob)])
    if len(pose_index_blob.read_bytes()) % PAGE_BYTES:
        raise SystemExit("generated pose index is not aligned to 16 KiB pages")
    total_pages += len(pose_index_blob.read_bytes()) // PAGE_BYTES

    run([sys.executable, str(INTEGRATED / "tools" / "trim_scene_header.py"),
         "--header", str(integrated_header),
         "--out", str(inc / "scene_trimmed.h")])
    run([sys.executable, "-m", "mugen2sms.generators.integrated_runtime_data",
         "--p1-manifest", str(p1_manifest_path),
         "--p2-manifest", str(p2_manifest_path),
         "--runtime-header", str(integrated_header),
         "--frame-header", str(frame_data_header),
         "--pose-header", str(inc / "pose_table.h"),
         "--out", str(inc / "fight_runtime_data.h"),
         "--report", str(destination / "out" / "fight_runtime_data_manifest.json")],
        cwd=WRAPPER)
    run([sys.executable, str(WRAPPER / "mugen2sms" / "generators" / "cmd_patterns.py"),
         "--p1-source", str(source_p1), "--p1-config", str(config_p1),
         "--p2-source", str(source_p2), "--p2-config", str(config_p2),
         "--out-header", str(inc / "attack_cmds.h"),
         "--out-report", str(destination / "out" / "attack_cmds_report.json")])

    # Source/pose tables are independent of the audio provenance record. Keep
    # their generated review artifacts available even when PSG intake is blocked.
    prepare_audio_blobs(destination)

    combined_image = banks / "banks_integrada.bin"
    combined_image.write_bytes(
        source_bytes + meta_blob.read_bytes() + frame_data_blob.read_bytes() +
        pose_index_blob.read_bytes()
    )
    set_mapper_asset(destination / ".mddev" / "project.json", total_pages)
    run([sys.executable, str(WRAPPER / "build_inner.py"), "--project", str(destination)])

    rom = destination / "out" / "rom" / f"{destination.name}.sms"
    map_file = destination / "out" / "obj" / f"{destination.name}.map"
    if not rom.is_file() or not map_file.is_file():
        raise SystemExit("build wrapper returned without the expected ROM/map")
    sources = sorted((destination / "src").glob("*.c"))
    run([sys.executable, str(INTEGRATED / "tools" / "check_ram_layout.py"),
         "--map", str(map_file), "--rom", str(rom), "--sources",
         *[str(path) for path in sources], str(frame_data_header),
         str(inc / "pose_table.h")])
    run([sys.executable, str(INTEGRATED / "tools" / "check_rom_binding.py"),
         "--rom", str(rom), "--image", str(combined_image), "--base-bank", "2",
         "--pose-header", str(inc / "pose_table.h"), "--meta-blob", str(meta_blob),
         "--frame-data-blob", str(frame_data_blob),
         "--frame-data-header", str(frame_data_header),
         "--pose-index-blob", str(pose_index_blob),
         "--pose-index-header", str(inc / "pose_table.h")])
    print(f"[SOURCE PAIR BUILD] {rom} ({rom.stat().st_size} B); "
          f"source={source_pages} pages, metadata={meta_pages} pages at "
          f"{meta_first}..{meta_first + meta_pages - 1}")
    return rom


def self_check() -> None:
    assert mapper_layout(35, 1) == (37, 36)
    assert mapper_layout(40, 2) == (42, 42)
    assert source_hashes_by_actor({"p1_ken": "a" * 64,
                                   "p2_ryu": "a" * 64}) == ("a" * 64, "a" * 64)
    assert source_hashes_by_actor({"p1_ken": "a" * 64,
                                   "p2_ryu": "b" * 64}) == ("a" * 64, "b" * 64)
    slot_header = namespace_slot_actors(
        "#define P1_CUT_ANIM_IDLE 0\nstatic const Anim p2_anims[1];\n"
        "#define X_P2_TILES_BANK 7\n")
    assert "#define KEN_CUT_ANIM_IDLE 0" in slot_header
    assert "static const Anim ryu_anims[1]" in slot_header
    assert "#define X_P2_TILES_BANK 7" in slot_header
    try:
        mapper_layout(255, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("8-bit mapper overflow was accepted")
    print("[PASS] build_luta_source_pair self-check (contiguous mapper layout)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cut-dir", type=Path)
    parser.add_argument("--config-p1", type=Path)
    parser.add_argument("--config-p2", type=Path)
    parser.add_argument("--source-p1", type=Path)
    parser.add_argument("--source-p2", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    required = (args.cut_dir, args.config_p1, args.config_p2,
                args.source_p1, args.source_p2, args.out)
    if any(value is None for value in required):
        parser.error("--cut-dir, both configs/sources and --out are required")
    build(args.cut_dir, args.config_p1, args.config_p2,
          args.source_p1, args.source_p2, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
