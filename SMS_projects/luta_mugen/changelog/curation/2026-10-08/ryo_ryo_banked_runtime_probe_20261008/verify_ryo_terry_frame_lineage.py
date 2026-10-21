#!/usr/bin/env python3
"""Bind both Ryo/Terry source cuts to one exact hitbroad ROM.

P1 Ryo is replayed from its local scene banks; P2 Terry lineage is consumed
from its hash-bound report and rechecked against the same ROM bytes. This is a
curation sidecar, not emulator, visual, command, or gameplay proof.
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
STUDY = PROJECT / "out/local_study/ryo_terry_cmdv4_20261008"
MERGED_MANIFEST = STUDY / "versus_scene_manifest.json"
MAPPER_IMAGE = STUDY / "versus_scene_banks_02.bin"
P1_SLOT = STUDY / "p1_ken"
P1_SOURCE = PROJECT / "base/OUTROS/ffspRyo_v3.zip"
P1_PROFILE = PROJECT / "data/ryo_v3_runtime_cut_20261006.json"
P2_REPORT = CANDIDATE / "terry_frame_lineage.json"
BUILD = PROJECT / "out/local_study/ryo_terry_hitbroad_20261008"
INTEGRATED_BANKS = BUILD / "assets/banks/banks_integrada.bin"
ROM = BUILD / "changelog/roms/build_v002/rom.sms"
BUILD_RECORD = BUILD / "out/build_record.json"
PROJECT_CONFIG = BUILD / ".mddev/project.json"
REPORT = CANDIDATE / "ryo_terry_frame_lineage.json"
BANK_BYTES = 16384

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


def read_macros(header: str, symbol: str) -> dict[str, int]:
    pattern = re.compile(
        rf"^#define\s+{re.escape(symbol)}_(SIZE|BANK|OFF)\s+(\d+)\s*$",
        re.MULTILINE,
    )
    return {key: int(value) for key, value in pattern.findall(header)}


def frame_macros(header: str, manifest: dict) -> dict[str, dict[str, int]]:
    match = re.search(
        r"^#define\s+([A-Z0-9_]+)_A-?\d+F\d+_TILES_BANK\s+\d+",
        header,
        re.MULTILINE,
    )
    if match is None:
        return {}
    prefix = match.group(1)
    result = {}
    for role in manifest.get("roles", []):
        action = int(role["action"])
        for frame_index in range(int(role["frame_count"])):
            for suffix in ("", "_P2"):
                symbol = f"{prefix}_A{action}F{frame_index}{suffix}_TILES"
                result[symbol] = read_macros(header, symbol)
    return result


def main() -> int:
    merged = read_json(MERGED_MANIFEST)
    p1_manifest = read_json(P1_SLOT / "ken_scene_manifest.json")
    terry_report = read_json(P2_REPORT)
    build_record = read_json(BUILD_RECORD)
    project_config = read_json(PROJECT_CONFIG)
    mapper_record = merged["mapper_images"][0]
    mapper = MAPPER_IMAGE.read_bytes()
    integrated = INTEGRATED_BANKS.read_bytes()
    rom = ROM.read_bytes()
    bank_match = re.search(r":(\d+)$", project_config["toolchain"]["makesms_extra"][-1])
    if bank_match is None:
        raise RuntimeError("integrated-bank start is absent from makesms_extra")
    integrated_first_bank = int(bank_match.group(1))
    mapper_start = int(mapper_record["bank_start"])
    rom_hash = sha256(rom)
    checks = []

    def check(name: str, ok: bool, details=None):
        checks.append({"name": name, "ok": bool(ok), "details": details})

    check("candidate_rom_identity_shared",
          rom_hash == build_record["rom_sha256"]
          and rom_hash == terry_report["candidate"]["rom_sha256"],
          {"rom_sha256": rom_hash, "build_record": build_record["rom_sha256"],
           "terry_report": terry_report["candidate"]["rom_sha256"]})
    check("terry_subreport_passes_and_is_complete",
          terry_report["status"] == "PASS_TERRY_FRAME_BYTE_LINEAGE"
          and len(terry_report["checks"]) == 15
          and all(row["ok"] for row in terry_report["checks"])
          and len(terry_report["lineage"]) == 370)
    check("terry_source_archive_current",
          file_sha(PROJECT / "base/OUTROS/A-Terry.zip")
          == terry_report["source"]["archive_sha256"])
    check("terry_profile_current",
          file_sha(PROJECT / terry_report["profile"]["path"])
          == terry_report["profile"]["sha256"])
    check("terry_generator_identity_current",
          file_sha(WORKSPACE / "tools/sms_wrapper/mugen2sms/generators/scene_cut.py")
          == terry_report["generator"]["sha256"])

    expected_rom = build_record["rom_sha256"]
    p1_hash = file_sha(P1_SOURCE)
    p1_profile_hash = file_sha(P1_PROFILE)
    check("ryo_source_matches_preserved_and_merged_manifests",
          p1_hash == p1_manifest["source_sha256"]
          and p1_hash == merged["source_sha256"]["p1_ken"]
          and p1_manifest.get("source_def") == "ffspRyo.def")
    profile = read_json(P1_PROFILE)
    check("ryo_profile_source_hash_matches", profile["source_sha256"] == p1_hash)
    check("scene_mapper_hash_and_bank_image_match",
          len(mapper) == int(mapper_record["bytes"])
          and sha256(mapper) == mapper_record["sha256"]
          and mapper == integrated[:len(mapper)])
    rom_insert_offset = integrated_first_bank * BANK_BYTES
    check("integrated_bank_is_embedded_in_shared_rom",
          rom[rom_insert_offset:rom_insert_offset + len(integrated)] == integrated,
          {"bank_start": integrated_first_bank, "rom_offset": rom_insert_offset,
           "integrated_bytes": len(integrated), "integrated_sha256": sha256(integrated)})

    with zipfile.ZipFile(P1_SOURCE) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        air_name = next(name for name in names if name.lower().endswith(".air"))
        sff_name = next(name for name in names if name.lower().endswith(".sff"))
        air_bytes = archive.read(air_name)
        sff_bytes = archive.read(sff_name)
    air_result = air_parser.parse(air_bytes.decode("latin-1"), air_name)
    sprites, sff_warnings = sff_parser.parse(sff_bytes)
    sprite_by_key = {(sprite.group, sprite.image): sprite for sprite in sprites}
    check("ryo_sff_parse_clean", not sff_warnings, sff_warnings[:8])

    p1_rows = [row for row in merged["banks"] if row.get("fighter") == "p1_ken"]
    p1_targets = {int(row["source_bank"]): int(row["bank"]) for row in p1_rows}
    p1_bank_records = {int(row["bank"]): row for row in p1_manifest["banks"]}
    check("ryo_has_38_mapped_local_pages",
          len(p1_targets) == 38 and len(p1_bank_records) == 38
          and set(p1_targets) == set(p1_bank_records),
          {"local_pages": sorted(p1_bank_records),
           "final_pages": sorted(p1_targets.values())})

    old_header_path = P1_SLOT / "ken_scene_runtime.h"
    old_header = old_header_path.read_text(encoding="ascii")
    old_macros = frame_macros(old_header, p1_manifest)
    role_by_action = {int(role["action"]): role for role in p1_manifest["roles"]}
    lineage = []
    frame_errors = []
    source_frame_count = 0
    for action_id, role in sorted(role_by_action.items()):
        action = air_result.actions.get(action_id)
        if action is None or len(action.frames) != int(role["frame_count"]):
            frame_errors.append(f"AIR action {action_id}: missing or wrong frame count")
            continue
        for frame_index, frame in enumerate(action.frames):
            source_frame_count += 1
            frame_key = f"anim:{action_id}.{frame_index}"
            frame_record = p1_manifest.get("frames", {}).get(frame_key)
            sprite = sprite_by_key.get((frame.group, frame.image))
            if frame_record is None or sprite is None:
                frame_errors.append(f"{frame_key}: SFF sprite or frame record missing")
                continue
            size_source = [sprite.width, sprite.height]
            if frame_record.get("size_source") != size_source:
                frame_errors.append(f"{frame_key}: source size differs from SFF")
            for variant, suffix in (("p1", ""), ("p2", "_P2")):
                prefix_match = re.search(
                    r"^#define\s+([A-Z0-9_]+)_A-?\d+F\d+_TILES_BANK\s+\d+",
                    old_header,
                    re.MULTILINE,
                )
                if prefix_match is None:
                    frame_errors.append("Ryo P1 header lacks generated tile prefix")
                    break
                symbol = (f"{prefix_match.group(1)}_A{action_id}F{frame_index}"
                          f"{suffix}_TILES")
                macros = old_macros.get(symbol, {})
                if set(macros) != {"SIZE", "BANK", "OFF"}:
                    frame_errors.append(f"{symbol}: incomplete macros")
                    continue
                source_bank, offset, size = macros["BANK"], macros["OFF"], macros["SIZE"]
                if size <= 0 or offset < 0 or offset + size > BANK_BYTES:
                    frame_errors.append(f"{symbol}: payload crosses local bank")
                    continue
                page_path = P1_SLOT / f"ken_scene_bank{source_bank}.bin"
                page = page_path.read_bytes() if page_path.is_file() else b""
                page_record = p1_bank_records.get(source_bank)
                page_ok = (len(page) == BANK_BYTES and page_record is not None
                           and sha256(page) == page_record.get("sha256"))
                final_bank = p1_targets.get(source_bank)
                if final_bank is None:
                    frame_errors.append(f"{symbol}: no merged final bank")
                    continue
                mapper_offset = (final_bank - mapper_start) * BANK_BYTES + offset
                integrated_offset = (final_bank - integrated_first_bank) * BANK_BYTES + offset
                rom_offset = final_bank * BANK_BYTES + offset
                payload = page[offset:offset + size]
                mapper_payload = mapper[mapper_offset:mapper_offset + size]
                integrated_payload = integrated[integrated_offset:integrated_offset + size]
                rom_payload = rom[rom_offset:rom_offset + size]
                payload_ok = (len(payload) == size and payload == mapper_payload
                              and payload == integrated_payload and payload == rom_payload)
                if not page_ok or not payload_ok:
                    frame_errors.append(f"{symbol}: local/mapper/integrated/ROM bytes diverge")
                lineage.append({
                    "fighter_slot": "p1_ken",
                    "source_def": "ffspRyo.def",
                    "palette_variant": variant,
                    "air": {"action": action_id, "frame_index": frame_index,
                            "line": frame.line, "group": frame.group, "image": frame.image},
                    "sff": {"group": sprite.group, "image": sprite.image,
                            "sprite_index": sprite.index,
                            "axis": [sprite.axis_x, sprite.axis_y],
                            "pixel_sha256": sha256(sprite.pixels), "size": size_source},
                    "generated_symbol": symbol,
                    "source_bank": source_bank,
                    "final_rom_bank": final_bank,
                    "bank_offset": offset,
                    "payload_bytes": size,
                    "tile_payload_sha256": sha256(payload),
                    "rom_offset": rom_offset,
                    "source_page_hash_matches_manifest": page_ok,
                    "payload_matches_mapper_integrated_bank_and_rom": payload_ok,
                })
    check("ryo_p1_94_air_frames_resolve_to_sff_and_rom", not frame_errors,
          {"frames": source_frame_count, "errors": frame_errors[:20]})
    check("ryo_p1_188_frame_macros_match_count", len(old_macros) == 188,
          {"actual": len(old_macros), "expected": 188})
    check("ryo_p1_lineage_has_188_payloads", len(lineage) == 188,
          {"actual": len(lineage), "expected": 188})

    replay = {}
    with tempfile.TemporaryDirectory(prefix="ryo_terry_p1_replay_") as temp:
        fresh_dir = Path(temp) / "p1_ryo"
        generated = generate(P1_SOURCE, P1_PROFILE, fresh_dir, 2, None)
        fresh_manifest = read_json(fresh_dir / "ken_scene_manifest.json")
        fresh_header = (fresh_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
        bank_mismatches = []
        for row in generated["banks"]:
            name = row["file"]
            if (not (fresh_dir / name).is_file() or not (P1_SLOT / name).is_file()
                    or (fresh_dir / name).read_bytes() != (P1_SLOT / name).read_bytes()):
                bank_mismatches.append(name)
        fresh_macros = frame_macros(fresh_header, fresh_manifest)
        macro_mismatches = sorted(
            name for name in set(old_macros) | set(fresh_macros)
            if old_macros.get(name) != fresh_macros.get(name)
        )
        replay = {
            "first_local_bank": 2,
            "generated_page_count": len(generated["banks"]),
            "bank_page_mismatch_count": len(bank_mismatches),
            "bank_page_mismatch_sample": bank_mismatches[:12],
            "preserved_frame_macro_count": len(old_macros),
            "fresh_frame_macro_count": len(fresh_macros),
            "frame_macro_mismatch_count": len(macro_mismatches),
            "frame_macro_mismatch_sample": macro_mismatches[:12],
            "fresh_header_sha256": file_sha(fresh_dir / "ken_scene_runtime.h"),
            "preserved_header_sha256": file_sha(old_header_path),
            "fresh_manifest_sha256": file_sha(fresh_dir / "ken_scene_manifest.json"),
            "preserved_manifest_sha256": file_sha(P1_SLOT / "ken_scene_manifest.json"),
            "fresh_frame_count": len(fresh_manifest.get("frames", {})),
        }
        check("clean_ryo_generator_reproduces_38_pages",
              len(generated["banks"]) == 38 and not bank_mismatches,
              {"count": len(bank_mismatches), "sample": bank_mismatches[:12]})
        check("clean_ryo_generator_reproduces_188_macros",
              len(fresh_macros) == 188 and not macro_mismatches,
              {"fresh": len(fresh_macros), "mismatch_count": len(macro_mismatches),
               "sample": macro_mismatches[:12]})
        check("clean_ryo_generator_resolves_94_frames",
              len(fresh_manifest.get("frames", {})) == 94)

    terry_rows = terry_report["lineage"]
    terry_rom_errors = []
    for index, row in enumerate(terry_rows):
        offset = int(row["rom_offset"])
        size = int(row["payload_bytes"])
        expected_offset = int(row["final_rom_bank"]) * BANK_BYTES + int(row["bank_offset"])
        if offset != expected_offset or offset < 0 or offset + size > len(rom):
            terry_rom_errors.append(f"row {index}: invalid ROM offset/bounds")
            continue
        if sha256(rom[offset:offset + size]) != row["tile_payload_sha256"]:
            terry_rom_errors.append(f"row {index}: ROM payload hash mismatch")
    check("terry_370_payloads_reverified_against_shared_rom", not terry_rom_errors,
          {"records": len(terry_rows), "errors": terry_rom_errors[:12]})

    combined = lineage + terry_rows
    check("both_slots_and_source_identities_present",
          {row["fighter_slot"] for row in combined} == {"p1_ken", "p2_ryu"}
          and {row["source_def"] for row in combined} == {"ffspRyo.def", "A-Terry.def"})
    check("shared_cut_has_558_unique_frame_palette_payloads",
          len(combined) == 558
          and len({(row["fighter_slot"], row["air"]["action"],
                    row["air"]["frame_index"], row["palette_variant"])
                   for row in combined}) == 558,
          {"actual": len(combined), "expected": 558})

    failures = [row for row in checks if not row["ok"]]
    result = {
        "schema": "luta_mugen_ryo_terry_shared_rom_frame_lineage_v1",
        "classification": "curation-only, same-ROM Ryo/Terry source-to-payload byte lineage; no visual/runtime/emulator claim",
        "status": "PASS_RYO_TERRY_SHARED_ROM_LINEAGE" if not failures else "FAIL",
        "candidate": {
            "project": "out/local_study/ryo_terry_hitbroad_20261008",
            "rom_sha256": rom_hash,
            "integrated_bank_sha256": sha256(integrated),
            "integrated_bank_bytes": len(integrated),
            "integrated_first_bank": integrated_first_bank,
            "rom_insertion_offset": rom_insert_offset,
            "mapper_image_sha256": sha256(mapper),
            "mapper_bank_start": mapper_start,
            "mapper_bank_count": len(mapper) // BANK_BYTES,
            "total_lineage_records": len(combined),
        },
        "source_profiles": {
            "p1_ryo": {"archive": "base/OUTROS/ffspRyo_v3.zip",
                        "source_def": "ffspRyo.def", "archive_sha256": p1_hash,
                        "profile": "data/ryo_v3_runtime_cut_20261006.json",
                        "profile_sha256": p1_profile_hash, "frame_count": 94,
                        "payload_count": len(lineage)},
            "p2_terry": {"archive": "base/OUTROS/A-Terry.zip",
                          "source_def": "A-Terry.def",
                          "archive_sha256": terry_report["source"]["archive_sha256"],
                          "profile": terry_report["profile"]["path"],
                          "profile_sha256": terry_report["profile"]["sha256"],
                          "frame_count": 185, "payload_count": len(terry_rows),
                          "subreport_sha256": file_sha(P2_REPORT)},
        },
        "generator": {
            "path": "tools/sms_wrapper/mugen2sms/generators/scene_cut.py",
            "sha256": file_sha(WORKSPACE / "tools/sms_wrapper/mugen2sms/generators/scene_cut.py"),
            "p1_ryo_clean_reproduction": replay,
        },
        "checks": checks,
        "failures": failures,
        "lineage": combined,
        "limitations": [
            "The p1_ken and p2_ryu labels are inherited; source definitions and archive hashes establish Ryo and Terry identity.",
            "Payload lineage proves the selected imported bytes and bank placement in this ROM, not visual fidelity or semantic correctness of the art conversion.",
            "The report does not prove source CMD/CNS execution, gameplay, boot, FPS, audio, or memory behavior.",
            "The underlying build record and prior Terry sidecar are hash-checked; no fresh private emulator QA was performed.",
            "No canonical source, docs, framework file, or local study artifact is modified by this verifier.",
        ],
    }
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "failures": failures,
        "rom_sha256": rom_hash,
        "p1_ryo_records": len(lineage),
        "p2_terry_records": len(terry_rows),
        "total_records": len(combined),
        "report": str(REPORT),
    }, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
