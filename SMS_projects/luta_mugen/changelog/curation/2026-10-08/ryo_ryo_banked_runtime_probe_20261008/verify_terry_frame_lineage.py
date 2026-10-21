#!/usr/bin/env python3
"""Trace preserved Terry AIR/SFF frames through banks into the hitbroad ROM.

This curation-only verifier also cleanly replays the current scene-cut
generator. It keeps inherited slot labels distinct from source identity and
does not claim runtime or visual validation.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path


CANDIDATE = Path(__file__).resolve().parent
PROJECT = CANDIDATE.parents[3]
WORKSPACE = PROJECT.parents[1]
SOURCE = PROJECT / "base/OUTROS/A-Terry.zip"
PROFILE = PROJECT / "data/terry_falchion22_runtime_cut_20261008f_source_routes.json"
STUDY = PROJECT / "out/local_study/ryo_terry_cmdv4_20261008"
PRESERVED_SLOT = STUDY / "p2_ryu"
MERGED_MANIFEST = STUDY / "versus_scene_manifest.json"
MAPPER_IMAGE = STUDY / "versus_scene_banks_02.bin"
BUILD = PROJECT / "out/local_study/ryo_terry_hitbroad_20261008"
INTEGRATED_BANKS = BUILD / "assets/banks/banks_integrada.bin"
ROM = BUILD / "changelog/roms/build_v002/rom.sms"
BUILD_RECORD = BUILD / "out/build_record.json"
PROJECT_CONFIG = BUILD / ".mddev/project.json"
REPORT = CANDIDATE / "terry_frame_lineage.json"
BANK_BYTES = 16384
EXPECTED_FRAMES = 185
EXPECTED_ASSETS = 370

sys.path.insert(0, str(WORKSPACE / "tools/sms_wrapper"))
from mugen2sms.generators.scene_cut import generate  # noqa: E402
from mugen2sms.parsers import air as air_parser  # noqa: E402
from mugen2sms.parsers import sff as sff_parser  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def bank_macros(header: str, symbol: str) -> dict[str, int]:
    pattern = re.compile(
        rf"^#define\s+{re.escape(symbol)}_(SIZE|BANK|OFF)\s+(\d+)\s*$",
        re.MULTILINE,
    )
    return {name: int(value) for name, value in pattern.findall(header)}


def frame_macro_map(header: str, manifest: dict) -> dict[str, dict[str, int]]:
    prefix_match = re.search(
        r"^#define\s+([A-Z0-9_]+)_A-?\d+F\d+_TILES_BANK\s+\d+",
        header,
        re.MULTILINE,
    )
    if prefix_match is None:
        return {}
    prefix = prefix_match.group(1)
    output = {}
    for role in manifest.get("roles", []):
        action = int(role["action"])
        for frame_index in range(int(role["frame_count"])):
            for suffix in ("", "_P2"):
                symbol = f"{prefix}_A{action}F{frame_index}{suffix}_TILES"
                output[symbol] = bank_macros(header, symbol)
    return output


def command_wire_version(header: str):
    match = re.search(
        r"const unsigned char CUT_CMD_BUTTON1\[\d+\]\s*=\s*\{\s*0x([0-9A-Fa-f]{2})",
        header,
    )
    return int(match.group(1), 16) if match else None


def main() -> int:
    merged = read_json(MERGED_MANIFEST)
    preserved_manifest = read_json(PRESERVED_SLOT / "ken_scene_manifest.json")
    probe = read_json(BUILD_RECORD)
    project_config = read_json(PROJECT_CONFIG)
    mapper_record = merged["mapper_images"][0]
    mapper_bytes = MAPPER_IMAGE.read_bytes()
    integrated = INTEGRATED_BANKS.read_bytes()
    rom = ROM.read_bytes()
    bank_start_match = re.search(
        r":(\d+)$", project_config["toolchain"]["makesms_extra"][-1]
    )
    if bank_start_match is None:
        raise RuntimeError("cannot read integrated-bank start from makesms_extra")
    integrated_first_bank = int(bank_start_match.group(1))
    checks = []

    def check(name: str, ok: bool, details=None):
        checks.append({"name": name, "ok": bool(ok), "details": details})

    source_hash = file_sha(SOURCE)
    profile_hash = file_sha(PROFILE)
    rom_hash = sha256(rom)
    check("source_archive_matches_both_scene_manifests",
          source_hash == preserved_manifest["source_sha256"]
          and source_hash == merged["source_sha256"]["p2_ryu"],
          {"source_zip_sha256": source_hash,
           "slot_sha256": preserved_manifest["source_sha256"],
           "merged_p2_sha256": merged["source_sha256"]["p2_ryu"]})
    check("profile_source_matches_archive",
          json.loads(PROFILE.read_text(encoding="utf-8"))["source_sha256"] == source_hash)
    check("candidate_rom_matches_build_record",
          rom_hash == probe["rom_sha256"],
          {"rom_sha256": rom_hash, "build_record_sha256": probe["rom_sha256"]})

    mapper_start = int(mapper_record["bank_start"])
    check("merged_mapper_image_matches_record",
          len(mapper_bytes) == int(mapper_record["bytes"])
          and sha256(mapper_bytes) == mapper_record["sha256"])
    check("mapper_image_is_first_scene_segment_of_integrated_bank",
          mapper_bytes == integrated[:len(mapper_bytes)],
          {"mapper_bytes": len(mapper_bytes), "integrated_bytes": len(integrated),
           "mapper_banks": len(mapper_bytes) // BANK_BYTES})
    rom_insert_offset = integrated_first_bank * BANK_BYTES
    check("integrated_bank_image_matches_exact_rom_bytes",
          rom[rom_insert_offset:rom_insert_offset + len(integrated)] == integrated,
          {"rom_offset": rom_insert_offset, "bank_bytes": len(integrated),
           "integrated_sha256": sha256(integrated)})

    p2_rows = [row for row in merged["banks"] if row.get("fighter") == "p2_ryu"]
    bank_targets = {int(row["source_bank"]): int(row["bank"]) for row in p2_rows}
    check("p2_terry_has_69_mapped_source_pages",
          len(p2_rows) == 69 and len(bank_targets) == 69,
          {"mapped_pages": len(bank_targets), "final_bank_span": [
              min(bank_targets.values()) if bank_targets else None,
              max(bank_targets.values()) if bank_targets else None]})

    with zipfile.ZipFile(SOURCE) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        air_name = next(name for name in members if name.lower().endswith(".air"))
        sff_name = next(name for name in members if name.lower().endswith(".sff"))
        air_bytes = archive.read(air_name)
        sff_bytes = archive.read(sff_name)
    air_result = air_parser.parse(air_bytes.decode("latin-1"), air_name)
    sprites, sff_warnings = sff_parser.parse(sff_bytes)
    sprite_by_key = {(sprite.group, sprite.image): sprite for sprite in sprites}
    check("source_sff_parse_clean", not sff_warnings, sff_warnings[:8])
    check("source_members_match_slot_identity",
          preserved_manifest.get("source_def") == "A-Terry.def"
          and air_name.lower() == "air.air" and sff_name.lower() == "sff.sff",
          {"source_def": preserved_manifest.get("source_def"),
           "air_member": air_name, "sff_member": sff_name})

    old_header_path = PRESERVED_SLOT / "ken_scene_runtime.h"
    old_header = old_header_path.read_text(encoding="ascii")
    old_macros = frame_macro_map(old_header, preserved_manifest)
    bank_records = {int(row["bank"]): row for row in preserved_manifest["banks"]}
    lineage = []
    frame_failures = []
    frame_count = 0
    roles_by_action = {int(role["action"]): role for role in preserved_manifest["roles"]}
    for action_id, role in sorted(roles_by_action.items()):
        action = air_result.actions.get(action_id)
        if action is None or len(action.frames) != int(role["frame_count"]):
            frame_failures.append(f"action {action_id}: AIR/manifest frame count mismatch")
            continue
        for frame_index, frame in enumerate(action.frames):
            frame_count += 1
            frame_key = f"anim:{action_id}.{frame_index}"
            frame_record = preserved_manifest.get("frames", {}).get(frame_key)
            sprite = sprite_by_key.get((frame.group, frame.image))
            if frame_record is None or sprite is None:
                frame_failures.append(f"{frame_key}: preserved record or source SFF sprite missing")
                continue
            expected_size = [sprite.width, sprite.height]
            if frame_record.get("size_source") != expected_size:
                frame_failures.append(f"{frame_key}: source dimensions disagree with SFF")
            page_lineages = []
            for variant, suffix in (("p1", ""), ("p2", "_P2")):
                prefix_match = re.search(
                    r"^#define\s+([A-Z0-9_]+)_A-?\d+F\d+_TILES_BANK\s+\d+",
                    old_header,
                    re.MULTILINE,
                )
                if prefix_match is None:
                    frame_failures.append("preserved header has no frame macro prefix")
                    break
                symbol = (f"{prefix_match.group(1)}_A{action_id}F{frame_index}"
                          f"{suffix}_TILES")
                macros = old_macros.get(symbol, {})
                if set(macros) != {"SIZE", "BANK", "OFF"}:
                    frame_failures.append(f"{symbol}: incomplete frame macros")
                    continue
                source_bank = macros["BANK"]
                offset = macros["OFF"]
                size = macros["SIZE"]
                if offset < 0 or size <= 0 or offset + size > BANK_BYTES:
                    frame_failures.append(f"{symbol}: payload crosses source bank")
                    continue
                source_page_path = PRESERVED_SLOT / f"ken_scene_bank{source_bank}.bin"
                source_page = source_page_path.read_bytes() if source_page_path.is_file() else b""
                page_record = bank_records.get(source_bank)
                page_ok = (len(source_page) == BANK_BYTES and page_record is not None
                           and sha256(source_page) == page_record.get("sha256"))
                final_bank = bank_targets.get(source_bank)
                if final_bank is None:
                    frame_failures.append(f"{symbol}: no merged bank target")
                    continue
                mapper_offset = (final_bank - mapper_start) * BANK_BYTES + offset
                integrated_offset = (final_bank - integrated_first_bank) * BANK_BYTES + offset
                rom_offset = final_bank * BANK_BYTES + offset
                payload = source_page[offset:offset + size]
                mapper_payload = mapper_bytes[mapper_offset:mapper_offset + size]
                integrated_payload = integrated[integrated_offset:integrated_offset + size]
                rom_payload = rom[rom_offset:rom_offset + size]
                payload_ok = (len(payload) == size and payload == mapper_payload
                              and payload == integrated_payload and payload == rom_payload)
                if not page_ok or not payload_ok:
                    frame_failures.append(f"{symbol}: source bank/mapper/integrated/ROM bytes diverge")
                record = {
                    "fighter_slot": "p2_ryu",
                    "source_def": "A-Terry.def",
                    "palette_variant": variant,
                    "air": {"action": action_id, "frame_index": frame_index,
                            "line": frame.line, "group": frame.group, "image": frame.image},
                    "sff": {"group": sprite.group, "image": sprite.image,
                            "sprite_index": sprite.index,
                            "axis": [sprite.axis_x, sprite.axis_y],
                            "pixel_sha256": sha256(sprite.pixels), "size": expected_size},
                    "generated_symbol": symbol,
                    "source_bank": source_bank,
                    "final_rom_bank": final_bank,
                    "bank_offset": offset,
                    "payload_bytes": size,
                    "tile_payload_sha256": sha256(payload),
                    "rom_offset": rom_offset,
                    "source_page_hash_matches_manifest": page_ok,
                    "payload_matches_mapper_integrated_bank_and_rom": payload_ok,
                }
                page_lineages.append(record)
                lineage.append(record)
            if len(page_lineages) != 2:
                frame_failures.append(f"{frame_key}: expected two palette payloads")

    check("all_185_selected_air_frames_resolve_to_source_sff", not frame_failures,
          {"frames": frame_count, "errors": frame_failures[:20]})
    check("preserved_frame_macro_count_370", len(old_macros) == EXPECTED_ASSETS,
          {"actual": len(old_macros), "expected": EXPECTED_ASSETS})
    check("terry_lineage_record_count_370", len(lineage) == EXPECTED_ASSETS,
          {"actual": len(lineage), "expected": EXPECTED_ASSETS})

    replay = {}
    with tempfile.TemporaryDirectory(prefix="terry_frame_lineage_replay_") as temp:
        fresh_dir = Path(temp) / "p2_terry"
        generated = generate(SOURCE, PROFILE, fresh_dir, 5, None)
        fresh_manifest = read_json(fresh_dir / "ken_scene_manifest.json")
        fresh_header = (fresh_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
        bank_mismatches = []
        for row in generated["banks"]:
            name = row["file"]
            fresh_page = fresh_dir / name
            preserved_page = PRESERVED_SLOT / name
            if (not fresh_page.is_file() or not preserved_page.is_file()
                    or fresh_page.read_bytes() != preserved_page.read_bytes()):
                bank_mismatches.append(name)
        fresh_macros = frame_macro_map(fresh_header, fresh_manifest)
        macro_mismatches = sorted(
            symbol for symbol in set(fresh_macros) | set(old_macros)
            if fresh_macros.get(symbol) != old_macros.get(symbol)
        )
        replay = {
            "first_local_bank": 5,
            "preserved_slot_bank_range": [min(bank_records), max(bank_records)],
            "generated_bank_count": len(generated["banks"]),
            "bank_page_mismatch_count": len(bank_mismatches),
            "bank_page_mismatch_sample": bank_mismatches[:12],
            "preserved_frame_macro_count": len(old_macros),
            "fresh_frame_macro_count": len(fresh_macros),
            "frame_macro_mismatch_count": len(macro_mismatches),
            "frame_macro_mismatch_sample": macro_mismatches[:12],
            "fresh_header_sha256": file_sha(fresh_dir / "ken_scene_runtime.h"),
            "preserved_header_sha256": file_sha(old_header_path),
            "fresh_manifest_sha256": file_sha(fresh_dir / "ken_scene_manifest.json"),
            "preserved_manifest_sha256": file_sha(PRESERVED_SLOT / "ken_scene_manifest.json"),
            "fresh_cmd_wire_version": command_wire_version(fresh_header),
            "preserved_cmd_wire_version": command_wire_version(old_header),
            "fresh_frame_count": len(fresh_manifest.get("frames", {})),
        }
        check("clean_current_generator_reproduces_69_terry_pages",
              not bank_mismatches and len(generated["banks"]) == 69,
              {"count": len(bank_mismatches), "sample": bank_mismatches[:12]})
        check("clean_current_generator_reproduces_370_frame_macros",
              not macro_mismatches and len(fresh_macros) == EXPECTED_ASSETS,
              {"fresh": len(fresh_macros), "preserved": len(old_macros),
               "mismatch_count": len(macro_mismatches),
               "sample": macro_mismatches[:12]})
        check("clean_current_generator_resolves_185_frames",
              len(fresh_manifest.get("frames", {})) == EXPECTED_FRAMES)

    failures = [item for item in checks if not item["ok"]]
    result = {
        "schema": "luta_mugen_terry_frame_lineage_v1",
        "classification": "curation-only preserved Terry frame-to-ROM byte mapping with clean generator replay; no visual/runtime/emulator claim",
        "status": "PASS_TERRY_FRAME_BYTE_LINEAGE" if not failures else "FAIL",
        "source": {
            "archive": "base/OUTROS/A-Terry.zip",
            "archive_sha256": source_hash,
            "air_member": air_name,
            "air_sha256": sha256(air_bytes),
            "sff_member": sff_name,
            "sff_sha256": sha256(sff_bytes),
            "air_action_count": len(air_result.actions),
            "sff_sprite_count": len(sprites),
            "air_parser_warning_count": len(air_result.warnings),
            "air_parser_warning_scope": "full AIR; selected action/frame identity is checked individually",
            "sff_parser_warnings": sff_warnings,
        },
        "profile": {
            "path": "data/terry_falchion22_runtime_cut_20261008f_source_routes.json",
            "sha256": profile_hash,
            "source_sha256": json.loads(PROFILE.read_text(encoding="utf-8"))["source_sha256"],
        },
        "generator": {
            "path": "tools/sms_wrapper/mugen2sms/generators/scene_cut.py",
            "sha256": file_sha(WORKSPACE / "tools/sms_wrapper/mugen2sms/generators/scene_cut.py"),
            "clean_reproduction": replay,
        },
        "candidate": {
            "project": "out/local_study/ryo_terry_hitbroad_20261008",
            "rom_sha256": rom_hash,
            "integrated_bank_sha256": sha256(integrated),
            "integrated_bank_bytes": len(integrated),
            "integrated_first_bank": integrated_first_bank,
            "rom_insertion_offset": rom_insert_offset,
            "mapper_image_sha256": sha256(mapper_bytes),
            "mapper_bank_start": mapper_start,
            "mapper_bank_count": len(mapper_bytes) // BANK_BYTES,
            "p2_final_bank_span": [min(bank_targets.values()), max(bank_targets.values())]
            if bank_targets else None,
            "lineage_count": len(lineage),
        },
        "checks": checks,
        "failures": failures,
        "lineage": lineage,
        "limitations": [
            "Inherited p2_ryu labels identify the slot; the verified source definition is A-Terry.def with the recorded ZIP SHA.",
            "The lineage binds preserved AIR/SFF identities and tile payload bytes to the exact hitbroad ROM; it does not prove visual fidelity or source-to-pixel conversion correctness.",
            "The CMD/CNS tables, command predicates, route dispatch and game behavior are outside this byte-lineage check.",
            "The build record has boot/gameplay flags, but this verifier does not authenticate them or replace fresh private native QA.",
            "No canonical source, document or framework file was changed by this sidecar verifier.",
        ],
    }
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "failures": failures,
        "lineage_records": len(lineage),
        "clean_reproduction": replay,
        "rom_sha256": rom_hash,
        "report": str(REPORT),
    }, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
