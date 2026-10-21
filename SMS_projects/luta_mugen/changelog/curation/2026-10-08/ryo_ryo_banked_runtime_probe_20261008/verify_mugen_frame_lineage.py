#!/usr/bin/env python3
"""Verify source AIR/SFF frame -> generated tiles -> exact Ryo/Ryo ROM bytes.

This curation-only verifier replays the current scene-cut generator into a
temporary directory, then checks preserved frame headers/banks against the
source archive, merged scene bank and candidate ROM. It is not a canonical
gate and it does not replace visual or emulator QA.
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
SOURCE = PROJECT / "base/OUTROS/ffspRyo_v3.zip"
PROFILE = PROJECT / "data/ryo_v3_runtime_cut_20261006.json"
STUDY = PROJECT / "out/local_study/ryo_ryo_cut_20261008a_source_routes/versus_cut"
REPORT = CANDIDATE / "mugen_frame_lineage.json"

sys.path.insert(0, str(WORKSPACE / "tools/sms_wrapper"))
from mugen2sms.generators.scene_cut import generate  # noqa: E402
from mugen2sms.parsers import air as air_parser  # noqa: E402
from mugen2sms.parsers import sff as sff_parser  # noqa: E402


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_file(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def define_values(header: str, symbol: str) -> dict[str, int]:
    found = {}
    pattern = re.compile(
        rf"^#define\s+{re.escape(symbol)}_(SIZE|BANK|OFF)\s+(\d+)\s*$",
        re.MULTILINE,
    )
    for key, value in pattern.findall(header):
        found[key] = int(value)
    return found


def frame_macro_map(header: str, scene_manifest: dict) -> dict[str, dict[str, int]]:
    prefix_match = re.search(r"^#define\s+([A-Z0-9]+)_A-?\d+F\d+_TILES_BANK\s+\d+",
                             header, re.MULTILINE)
    if prefix_match is None:
        return {}
    prefix = prefix_match.group(1)
    output = {}
    for role in scene_manifest.get("roles", []):
        action = int(role["action"])
        for frame_index in range(int(role["frame_count"])):
            for suffix in ("", "_P2"):
                symbol = f"{prefix}_A{action}F{frame_index}{suffix}_TILES"
                output[symbol] = define_values(header, symbol)
    return output


def main() -> int:
    probe = json_file(CANDIDATE / "probe_record.json")
    candidate_bank = (CANDIDATE / "banks_integrada.bin").read_bytes()
    candidate_rom = (CANDIDATE / "rom.sms").read_bytes()
    layout = json_file(CANDIDATE / "bank_layout.json")
    merged_manifest = json_file(STUDY / "versus_scene_manifest.json")
    mapper_record = merged_manifest["mapper_images"][0]
    mapper_path = STUDY / mapper_record["file"]
    mapper_image = mapper_path.read_bytes()
    bank_size = len(candidate_bank) // layout["total_banks"]
    scene_part = next(part for part in layout["parts"] if part["name"] == "scene_tiles")
    scene_start = (scene_part["first_bank"] - layout["first_bank"]) * bank_size
    candidate_scene = candidate_bank[scene_start:scene_start + scene_part["bytes"]]
    checks = []

    def check(name: str, ok: bool, details=None):
        checks.append({"name": name, "ok": bool(ok), "details": details})

    check("source_archive_hash", file_sha(SOURCE) == probe["inputs"]["source_zip"]["sha256"])
    check("profile_hash", file_sha(PROFILE) == probe["inputs"]["profile"]["sha256"])
    check("scene_manifest_source_hash", merged_manifest["source_sha256"] == {
        "p1_ken": file_sha(SOURCE), "p2_ryu": file_sha(SOURCE)
    })
    check("merged_mapper_image_hash", file_sha(mapper_path) == mapper_record["sha256"])
    check("scene_image_equals_integrated_bank_segment", mapper_image == candidate_scene)
    check("scene_image_rom_sha_from_probe", sha256(candidate_scene) == layout["parts"][0]["sha256"])

    with zipfile.ZipFile(SOURCE) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        air_name = next(name for name in names if name.lower().endswith(".air"))
        sff_name = next(name for name in names if name.lower().endswith(".sff"))
        air_bytes = archive.read(air_name)
        sff_bytes = archive.read(sff_name)
    air_result = air_parser.parse(air_bytes.decode("latin-1"), air_name)
    sprites, sff_warnings = sff_parser.parse(sff_bytes)
    sprite_by_key = {(item.group, item.image): item for item in sprites}
    check("source_sff_has_no_parser_warnings", not sff_warnings, sff_warnings[:8])

    bank_targets: dict[tuple[str, int], int] = {}
    for row in merged_manifest["banks"]:
        bank_targets[("p1_ken", int(row["source_bank"]))] = int(row["bank"])
    for row in merged_manifest["bank_reuse"]["exact_aliases"]:
        bank_targets[(row["fighter"], int(row["source_bank"]))] = int(row["bank"])
    check("all_p1_p2_source_pages_mapped", len(bank_targets) == 76,
          {"mapped": len(bank_targets), "expected": 76})

    lineage = []
    repro_results = []
    with tempfile.TemporaryDirectory(prefix="mugen_frame_lineage_") as temp:
        temp_root = Path(temp)
        for fighter, first_bank in (("p1_ken", 2), ("p2_ryu", 5)):
            preserved_dir = STUDY / fighter
            with tempfile.TemporaryDirectory(prefix=f"{fighter}_", dir=temp_root) as local_tmp:
                repro_dir = Path(local_tmp) / "scene_cut"
                reproduced = generate(SOURCE, PROFILE, repro_dir, first_bank, None)
                generated_files = [entry["file"] for entry in reproduced["banks"]]
                bank_mismatches = []
                for name in generated_files:
                    fresh = repro_dir / name
                    preserved = preserved_dir / name
                    if (not fresh.is_file() or not preserved.is_file()
                            or fresh.read_bytes() != preserved.read_bytes()):
                        bank_mismatches.append(name)
                fresh_header = (repro_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
                preserved_header = (preserved_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
                preserved_manifest = json_file(preserved_dir / "ken_scene_manifest.json")
                fresh_frame_macros = frame_macro_map(fresh_header, reproduced)
                preserved_frame_macros = frame_macro_map(preserved_header, preserved_manifest)
                macro_mismatches = sorted(
                    symbol for symbol in set(fresh_frame_macros) | set(preserved_frame_macros)
                    if fresh_frame_macros.get(symbol) != preserved_frame_macros.get(symbol)
                )
                preserved_cmd = re.search(
                    r"const unsigned char CUT_CMD_BUTTON1\[\d+\] = \{\s*0x([0-9A-Fa-f]{2})",
                    preserved_header,
                )
                fresh_cmd = re.search(
                    r"const unsigned char CUT_CMD_BUTTON1\[\d+\] = \{\s*0x([0-9A-Fa-f]{2})",
                    fresh_header,
                )
                preserved_manifest_sha = file_sha(preserved_dir / "ken_scene_manifest.json")
                fresh_manifest_sha = file_sha(repro_dir / "ken_scene_manifest.json")
                preserved_header_sha = file_sha(preserved_dir / "ken_scene_runtime.h")
                fresh_header_sha = file_sha(repro_dir / "ken_scene_runtime.h")
                repro_results.append({
                    "fighter": fighter,
                    "first_bank": first_bank,
                    "fresh_bank_count": len(generated_files),
                    "bank_mismatches": bank_mismatches,
                    "frame_macro_mismatches": macro_mismatches,
                    "frame_macros_compared": len(fresh_frame_macros),
                    "header_full_sha_match": fresh_header_sha == preserved_header_sha,
                    "fresh_header_sha256": fresh_header_sha,
                    "preserved_header_sha256": preserved_header_sha,
                    "manifest_full_sha_match": fresh_manifest_sha == preserved_manifest_sha,
                    "fresh_manifest_sha256": fresh_manifest_sha,
                    "preserved_manifest_sha256": preserved_manifest_sha,
                    "preserved_cmd_wire_version": int(preserved_cmd.group(1), 16) if preserved_cmd else None,
                    "fresh_cmd_wire_version": int(fresh_cmd.group(1), 16) if fresh_cmd else None,
                    "fresh_manifest_source_sha256": reproduced.get("source_sha256"),
                })
                check(f"clean_scene_cut_tile_bank_reproduction_{fighter}", not bank_mismatches,
                      {"compared_bank_count": len(generated_files),
                       "mismatches": bank_mismatches[:12]})
                check(f"clean_scene_cut_frame_macro_reproduction_{fighter}", not macro_mismatches,
                      {"compared_macro_count": len(fresh_frame_macros),
                       "mismatches": macro_mismatches[:12]})
                check(f"clean_scene_cut_cmd_v4_delta_recorded_{fighter}",
                      preserved_cmd is not None and fresh_cmd is not None
                      and int(preserved_cmd.group(1), 16) == 3
                      and int(fresh_cmd.group(1), 16) == 4,
                      {"preserved": int(preserved_cmd.group(1), 16) if preserved_cmd else None,
                       "fresh": int(fresh_cmd.group(1), 16) if fresh_cmd else None})

    for fighter in ("p1_ken", "p2_ryu"):
        slot_dir = STUDY / fighter
        scene_manifest = json_file(slot_dir / "ken_scene_manifest.json")
        header_path = slot_dir / "ken_scene_runtime.h"
        header = header_path.read_text(encoding="ascii")
        prefix_match = re.search(r"^#define\s+([A-Z0-9]+)_A-?\d+F\d+_TILES_BANK\s+\d+",
                                 header, re.MULTILINE)
        prefix = prefix_match.group(1) if prefix_match else None
        check(f"{fighter}_source_sha256", scene_manifest["source_sha256"] == file_sha(SOURCE))
        check(f"{fighter}_macro_prefix_found", prefix is not None)
        check(f"{fighter}_source_bank_manifest_count", len(scene_manifest["banks"]) == 38,
              len(scene_manifest["banks"]))
        scene_page_records = {int(item["bank"]): item for item in scene_manifest["banks"]}
        roles_by_action = {}
        for role in scene_manifest["roles"]:
            roles_by_action[int(role["action"])] = role

        frame_count = 0
        frame_failures = []
        for action_id, role in sorted(roles_by_action.items()):
            action = air_result.actions.get(action_id)
            if action is None:
                frame_failures.append(f"AIR action {action_id} absent")
                continue
            if len(action.frames) != int(role["frame_count"]):
                frame_failures.append(
                    f"action {action_id}: AIR frames={len(action.frames)} manifest={role['frame_count']}"
                )
                continue
            for frame_index, frame in enumerate(action.frames):
                frame_count += 1
                frame_key = f"anim:{action_id}.{frame_index}"
                source_sprite = sprite_by_key.get((frame.group, frame.image))
                frame_record = scene_manifest.get("frames", {}).get(frame_key)
                if source_sprite is None or frame_record is None:
                    frame_failures.append(f"{fighter} {frame_key}: source sprite or record missing")
                    continue
                dimensions_ok = frame_record.get("size_source") == [source_sprite.width, source_sprite.height]
                if not dimensions_ok:
                    frame_failures.append(f"{fighter} {frame_key}: source dimensions mismatch")

                for palette_variant, suffix in (("p1", ""), ("p2", "_P2")):
                    symbol = f"{prefix}_A{action_id}F{frame_index}{suffix}_TILES"
                    macros = define_values(header, symbol)
                    if set(macros) != {"SIZE", "BANK", "OFF"}:
                        frame_failures.append(f"{fighter} {symbol}: incomplete header macros")
                        continue
                    source_bank = macros["BANK"]
                    local_offset = macros["OFF"]
                    size = macros["SIZE"]
                    if local_offset + size > bank_size:
                        frame_failures.append(f"{fighter} {symbol}: payload crosses bank boundary")
                        continue
                    page_path = slot_dir / f"ken_scene_bank{source_bank}.bin"
                    page = page_path.read_bytes() if page_path.is_file() else b""
                    page_record = scene_page_records.get(source_bank)
                    page_ok = bool(page_record and len(page) == bank_size
                                   and sha256(page) == page_record["sha256"])
                    final_bank = bank_targets.get((fighter, source_bank))
                    if final_bank is None:
                        frame_failures.append(f"{fighter} {symbol}: source bank has no merged-page mapping")
                        continue
                    final_offset = (final_bank - int(mapper_record["bank_start"])) * bank_size
                    merged_page = mapper_image[final_offset:final_offset + bank_size]
                    candidate_bank_offset = (final_bank - layout["first_bank"]) * bank_size
                    integrated_page = candidate_scene[candidate_bank_offset:candidate_bank_offset + bank_size]
                    rom_offset = final_bank * bank_size + local_offset
                    payload = page[local_offset:local_offset + size]
                    merged_payload = merged_page[local_offset:local_offset + size]
                    integrated_payload = integrated_page[local_offset:local_offset + size]
                    rom_payload = candidate_rom[rom_offset:rom_offset + size]
                    payload_ok = (len(payload) == size and payload == merged_payload
                                  and payload == integrated_payload and payload == rom_payload)
                    if not page_ok or not payload_ok:
                        frame_failures.append(f"{fighter} {symbol}: page or ROM bytes diverge")
                    lineage.append({
                        "fighter_slot": fighter,
                        "palette_variant": palette_variant,
                        "air_action": action_id,
                        "air_frame_index": frame_index,
                        "air_source_line": frame.line,
                        "source_sff_group": frame.group,
                        "source_sff_image": frame.image,
                        "source_sff_sprite_index": source_sprite.index,
                        "source_sff_sprite_size": [source_sprite.width, source_sprite.height],
                        "source_sff_pixel_sha256": sha256(source_sprite.pixels),
                        "frame_manifest_key": frame_key,
                        "generated_symbol": symbol,
                        "source_bank": source_bank,
                        "final_rom_bank": final_bank,
                        "bank_offset": local_offset,
                        "payload_bytes": size,
                        "rom_offset": rom_offset,
                        "tile_payload_sha256": sha256(payload),
                        "source_manifest_size_matches_sff": dimensions_ok,
                        "source_page_hash_matches_manifest": page_ok,
                        "tile_payload_matches_merged_integrated_and_rom": payload_ok,
                    })
        check(f"{fighter}_all_selected_frames_resolve", not frame_failures,
              {"frames": frame_count, "errors": frame_failures[:20]})

    check("lineage_record_count", len(lineage) == 376,
          {"actual": len(lineage), "expected": 376})
    check("candidate_rom_matches_probe", sha256(candidate_rom) == probe["build"]["rom"]["sha256"])
    check("candidate_scene_bank_matches_probe", sha256(candidate_scene) == layout["parts"][0]["sha256"])

    errors = [item for item in checks if not item["ok"]]
    result = {
        "schema": "luta_mugen_frame_lineage_v1",
        "classification": "curation-only per-frame source/output/ROM byte mapping; not visual QA, emulator proof, or a canonical gate",
        "source": {
            "archive": "base/OUTROS/ffspRyo_v3.zip",
            "archive_sha256": file_sha(SOURCE),
            "air_member": air_name,
            "air_sha256": sha256(air_bytes),
            "sff_member": sff_name,
            "sff_sha256": sha256(sff_bytes),
            "air_action_count": len(air_result.actions),
            "sff_sprite_count": len(sprites),
            "air_parser_warnings_outside_or_inside_full_archive": {
                "count": len(air_result.warnings),
                "sample": air_result.warnings[:12],
                "interpretation": "full AIR contains non-frame annotations and fractional timings outside the selected 94-pose cut; selected action/frame counts and keys are checked separately below",
            },
        },
        "generator": {
            "path": "tools/sms_wrapper/mugen2sms/generators/scene_cut.py",
            "sha256": file_sha(WORKSPACE / "tools/sms_wrapper/mugen2sms/generators/scene_cut.py"),
            "profile": "data/ryo_v3_runtime_cut_20261006.json",
            "profile_sha256": file_sha(PROFILE),
            "clean_reproduction": repro_results,
            "preserved_vs_current_cmd_wire_delta": "preserved scene headers emit CMD blob version 3; clean reruns of current generator emit version 4, while all 38 tile banks and selected frame macros are compared independently",
        },
        "merged_scene": {
            "manifest_sha256": file_sha(STUDY / "versus_scene_manifest.json"),
            "mapper_image_sha256": sha256(mapper_image),
            "candidate_integrated_scene_sha256": sha256(candidate_scene),
            "candidate_rom_sha256": sha256(candidate_rom),
            "mapper_bank_start": mapper_record["bank_start"],
            "bank_bytes": bank_size,
            "lineage_count": len(lineage),
        },
        "checks": checks,
        "failed_checks": errors,
        "limitations": [
            "This proves source identifiers, regenerated symbol/page payloads, merged banks and candidate ROM bytes for the selected 94 poses per slot; it does not judge whether the converted art looks faithful or correct.",
            "The generated output is mapped by the current generator's action/frame naming convention and header macros; arbitrary MUGEN assets outside this cut are not covered.",
            "The preserved scene-cut header/manifests have an older command-data encoding. Clean reproduction shows CMD blob version 3 versus current version 4; this verifier checks scene pages and frame macros separately and does not certify runtime CMD schema compatibility.",
            "No emulation, FPS, gameplay, audio, memory, or visual-delivery claim is made.",
            "Source-route tables still are not executed by this candidate runtime.",
            "The canonical PNG asset-binding gate remains unchanged and is not passed by this MUGEN-specific report.",
        ],
        "status": "PASS_SELECTED_FRAME_BYTE_LINEAGE" if not errors else "FAIL",
        "lineage": lineage,
    }
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "checks_passed": len(checks) - len(errors),
        "checks_total": len(checks),
        "failures": errors,
        "lineage_records": len(lineage),
        "reproduction": repro_results,
        "report": str(REPORT),
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
