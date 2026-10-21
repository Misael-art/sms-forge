#!/usr/bin/env python3
"""Verify transform-level MUGEN input -> generated bank -> ROM provenance.

This curation helper is deliberately not the canonical rom_asset_binding gate.
It records only links supported by the existing importer manifests and build
artifacts; it does not claim per-sprite lineage or emulator validation.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


CANDIDATE = Path(__file__).resolve().parent
PROJECT = CANDIDATE.parents[3]
WORKSPACE = PROJECT.parents[1]
REPORT = CANDIDATE / "mugen_import_to_rom_provenance.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    record = load_json(CANDIDATE / "probe_record.json")
    checks = []

    def check(name: str, expected, actual):
        checks.append({
            "name": name,
            "expected": expected,
            "actual": actual,
            "ok": expected == actual,
        })

    source = PROJECT / "base/OUTROS/ffspRyo_v3.zip"
    profile = PROJECT / "data/ryo_v3_runtime_cut_20261006.json"
    source_sha = digest_file(source)
    profile_sha = digest_file(profile)
    check("source_archive_sha256", record["inputs"]["source_zip"]["sha256"], source_sha)
    check("profile_sha256", record["inputs"]["profile"]["sha256"], profile_sha)

    semantic_members = []
    semantic_suffixes = (".def", ".sff", ".air", ".cmd", ".cns")
    with zipfile.ZipFile(source) as archive:
        for info in sorted(archive.infolist(), key=lambda item: item.filename.lower()):
            if info.is_dir() or not info.filename.lower().endswith(semantic_suffixes):
                continue
            payload = archive.read(info.filename)
            semantic_members.append({
                "path_in_archive": info.filename,
                "bytes": len(payload),
                "sha256": sha256(payload),
            })

    runtime_manifest_path = CANDIDATE / "runtime_source_manifest.json"
    runtime_manifest = load_json(runtime_manifest_path)
    runtime_sources = []
    for entry in runtime_manifest["entries"]:
        path = PROJECT / entry["path"]
        actual_bytes = path.stat().st_size if path.is_file() else None
        actual_sha = digest_file(path) if path.is_file() else None
        ok = actual_bytes == entry["bytes"] and actual_sha == entry["sha256"]
        runtime_sources.append({
            "path": entry["path"],
            "expected_bytes": entry["bytes"],
            "actual_bytes": actual_bytes,
            "expected_sha256": entry["sha256"],
            "actual_sha256": actual_sha,
            "ok": ok,
        })
    check("runtime_source_manifest_entries", len(runtime_manifest["entries"]), len(runtime_sources))
    check("runtime_source_files_verified", True, all(item["ok"] for item in runtime_sources))

    artifact_checks = []
    for artifact in record.get("artifacts", []):
        path = CANDIDATE / artifact["path"]
        actual_bytes = path.stat().st_size if path.is_file() else None
        actual_sha = digest_file(path) if path.is_file() else None
        ok = actual_bytes == artifact["bytes"] and actual_sha == artifact["sha256"]
        artifact_checks.append({
            "path": artifact["path"],
            "expected_bytes": artifact["bytes"],
            "actual_bytes": actual_bytes,
            "expected_sha256": artifact["sha256"],
            "actual_sha256": actual_sha,
            "ok": ok,
        })
    check("probe_artifact_inventory", len(record.get("artifacts", [])), len(artifact_checks))
    check("probe_artifacts_verified", True, all(item["ok"] for item in artifact_checks))

    scene_manifest = load_json(CANDIDATE / "generated/versus_scene_manifest.json")
    scene_hashes = scene_manifest.get("source_sha256", {})
    check("scene_manifest_p1_source", source_sha, scene_hashes.get("p1_ken"))
    check("scene_manifest_p2_source", source_sha, scene_hashes.get("p2_ryu"))
    frame_manifest_path = CANDIDATE / "generated/p1_ken/ken_scene_manifest.json"
    frame_manifest = load_json(frame_manifest_path)
    frame_records = frame_manifest.get("frames", {})
    source_ref_fields = {"source_group", "source_image", "source_sprite_id", "tile_symbol", "bank", "offset"}
    explicit_source_ref_count = sum(
        1 for item in frame_records.values()
        if source_ref_fields.intersection(item)
    )
    scene_generator = WORKSPACE / "tools/sms_wrapper/mugen2sms/generators/scene_cut.py"
    generator_text = scene_generator.read_text(encoding="utf-8")
    generator_lines = generator_text.splitlines()
    source_lookup_line = next((i + 1 for i, line in enumerate(generator_lines)
                               if "sprite = by_key[(frame.group, frame.image)]" in line), None)
    frame_record_line = next((i + 1 for i, line in enumerate(generator_lines)
                              if 'source_frames[f"anim:{aid}.{i}"] = {' in line), None)
    check("frame_manifest_has_records", True, bool(frame_records))
    check("scene_generator_reads_source_sff_key", True, source_lookup_line is not None)
    check("scene_generator_emits_action_frame_key", True, frame_record_line is not None)
    check("frame_manifest_omits_explicit_sprite_and_output_refs", True,
          explicit_source_ref_count == 0)
    runtime_data = load_json(CANDIDATE / "generated/fight_runtime_data_manifest.json")
    slot_source_hashes = [slot.get("source_sha256") for slot in runtime_data.get("source_slots", [])]
    check("runtime_manifest_slot_sources", [source_sha, source_sha], slot_source_hashes)

    bank_path = CANDIDATE / "banks_integrada.bin"
    bank_data = bank_path.read_bytes()
    layout = load_json(CANDIDATE / "bank_layout.json")
    bytes_per_bank = len(bank_data) // layout["total_banks"] if layout["total_banks"] else 0
    check("bank_image_size", layout["total_bytes"], len(bank_data))
    check("bank_image_sha256", layout["merged_sha256"], sha256(bank_data))
    check("bank_size_integral", True, bool(bytes_per_bank and len(bank_data) == bytes_per_bank * layout["total_banks"]))

    bank_segments = []
    for part in layout["parts"]:
        rel_start = (part["first_bank"] - layout["first_bank"]) * bytes_per_bank
        rel_end = rel_start + part["bytes"]
        segment = bank_data[rel_start:rel_end]
        actual_sha = sha256(segment)
        bank_segments.append({
            "name": part["name"],
            "bank_range": [part["first_bank"], part["last_bank"]],
            "expected_bytes": part["bytes"],
            "actual_bytes": len(segment),
            "expected_sha256": part["sha256"],
            "actual_sha256": actual_sha,
            "ok": len(segment) == part["bytes"] and actual_sha == part["sha256"],
        })
    check("bank_segments_verified", True, all(item["ok"] for item in bank_segments))

    rom_path = CANDIDATE / record["build"]["rom"]["path"]
    rom_data = rom_path.read_bytes()
    rom_sha = sha256(rom_data)
    check("rom_size", record["build"]["rom"]["bytes"], len(rom_data))
    check("rom_sha256", record["build"]["rom"]["sha256"], rom_sha)
    rom_offset = layout["first_bank"] * bytes_per_bank
    inserted = rom_data[rom_offset:rom_offset + len(bank_data)]
    check("bank_image_rom_offset", 0x8000, rom_offset)
    check("bank_image_exact_rom_bytes", sha256(bank_data), sha256(inserted))
    check("bank_image_rom_bytes_equal", len(bank_data), len(inserted))

    gate_result = load_json(CANDIDATE / "rom_asset_binding_audit.json")
    audit = gate_result.get("report", {})
    check("png_asset_gate_map_present", False, audit.get("present"))
    check("png_asset_gate_reports_missing_map", True, any(
        "mapa ausente" in item for item in gate_result.get("problems", [])
    ))

    frame_lineage_path = CANDIDATE / "mugen_frame_lineage.json"
    frame_lineage = load_json(frame_lineage_path) if frame_lineage_path.is_file() else {}
    check("frame_lineage_sidecar_pass", "PASS_SELECTED_FRAME_BYTE_LINEAGE",
          frame_lineage.get("status"))
    check("frame_lineage_record_count", 376,
          frame_lineage.get("merged_scene", {}).get("lineage_count"))
    check("frame_lineage_all_checks_pass", True,
          bool(frame_lineage.get("checks")) and all(
              item.get("ok") for item in frame_lineage.get("checks", [])
          ))

    limitations = [
        "Transform-level provenance only: the manifests connect the source archive hash to generated scene/runtime outputs and the bank image to the exact ROM bytes.",
        "This package-level report does not itself carry the per-frame map; the companion mugen_frame_lineage.json verifies selected AIR/SFF-to-tile-byte references for this cut.",
        "The scene-cut generator resolves each AIR frame's group/image to an SFF sprite, but the frame manifest omits that source key and the generated tile symbol/bank offset, preventing a direct per-frame audit from this candidate package.",
        "This report does not satisfy audit_rom_asset_binding.py, whose current schema requires a project res_path PNG entry.",
        "No emulator, gameplay, FPS, audio, memory, or visual-delivery evidence is added by hashing these files.",
        "Generated source-route tables remain unconsumed by the candidate C runtime; general MUGEN CNS semantics are not proven.",
    ]
    errors = [item["name"] for item in checks if not item["ok"]]
    result = {
        "schema": "luta_mugen_import_to_rom_provenance_v1",
        "classification": "curation-only transform-level provenance; not a delivery gate or canonical asset-binding map",
        "candidate_rom_sha256": rom_sha,
        "source_archive": {
            "path": "base/OUTROS/ffspRyo_v3.zip",
            "bytes": source.stat().st_size,
            "sha256": source_sha,
            "semantic_members": semantic_members,
        },
        "profile": {
            "path": "data/ryo_v3_runtime_cut_20261006.json",
            "bytes": profile.stat().st_size,
            "sha256": profile_sha,
        },
        "runtime_source_manifest": {
            "path": str(runtime_manifest_path.relative_to(CANDIDATE)),
            "entry_count": len(runtime_sources),
            "verified_count": sum(item["ok"] for item in runtime_sources),
            "entries": runtime_sources,
        },
        "probe_artifacts": {
            "count": len(artifact_checks),
            "verified_count": sum(item["ok"] for item in artifact_checks),
            "entries": artifact_checks,
        },
        "scene_manifest_source_links": {
            "manifest_sha256": digest_file(CANDIDATE / "generated/versus_scene_manifest.json"),
            "source_sha256_by_slot": scene_hashes,
            "runtime_manifest_source_sha256_by_slot": slot_source_hashes,
            "generated_scene_bank_sha256": record["pipeline"]["scene_bank_sha256"],
        },
        "frame_lineage_sidecar": {
            "path": str(frame_lineage_path.relative_to(CANDIDATE)),
            "sha256": digest_file(frame_lineage_path) if frame_lineage_path.is_file() else None,
            "status": frame_lineage.get("status"),
            "lineage_count": frame_lineage.get("merged_scene", {}).get("lineage_count"),
        },
        "frame_lineage_inspection": {
            "scene_cut_generator": "tools/sms_wrapper/mugen2sms/generators/scene_cut.py",
            "scene_cut_generator_sha256": digest_file(scene_generator),
            "generator_source_lookup_line": source_lookup_line,
            "generator_frame_manifest_record_line": frame_record_line,
            "manifest_path": str(frame_manifest_path.relative_to(CANDIDATE)),
            "frame_record_count": len(frame_records),
            "explicit_source_or_output_reference_fields": sorted(source_ref_fields),
            "frame_records_with_any_explicit_reference": explicit_source_ref_count,
            "interpretation": "generator resolves AIR group/image to SFF sprite and creates action/frame symbols, but this manifest serializes neither the source sprite key nor generated tile symbol/bank offset per frame",
            "scope": "static source/manifests inspection; not pixel-by-pixel transform verification",
        },
        "bank_image": {
            "path": "banks_integrada.bin",
            "bytes": len(bank_data),
            "sha256": sha256(bank_data),
            "bytes_per_bank_derived": bytes_per_bank,
            "segments": bank_segments,
        },
        "rom": {
            "path": "rom.sms",
            "bytes": len(rom_data),
            "sha256": rom_sha,
            "bank_image_offset": rom_offset,
            "bank_image_bytes_match": inserted == bank_data,
        },
        "existing_png_asset_gate": {
            "present": audit.get("present"),
            "problems": gate_result.get("problems", []),
            "interpretation": "expected scope mismatch: imported MUGEN package and generated bank data are not project res_path PNG entries",
        },
        "checks": checks,
        "errors": errors,
        "limitations": limitations,
        "status": "PASS_TRANSFORM_LEVEL_PROVENANCE_WITH_EXPLICIT_GAPS" if not errors else "FAIL",
    }
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "checks": len(checks),
        "passed": sum(item["ok"] for item in checks),
        "failed": errors,
        "semantic_members": len(semantic_members),
        "runtime_sources_verified": sum(item["ok"] for item in runtime_sources),
        "probe_artifacts_verified": sum(item["ok"] for item in artifact_checks),
        "bank_offset": hex(rom_offset),
        "rom_sha256": rom_sha,
        "report": str(REPORT),
    }, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
