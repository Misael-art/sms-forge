#!/usr/bin/env python3
"""Validate the isolated MUGEN frame-lineage draft and its fail-closed cases.

This is a curation sidecar for the fixed Ryo/Ryo cut. It is not installed in
tools/sms_wrapper and does not replace the canonical PNG asset-binding gate.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path


CANDIDATE = Path(__file__).resolve().parent
PROJECT = CANDIDATE.parents[3]
WORKSPACE = PROJECT.parents[1]
DEFAULT_SOURCE = PROJECT / "base/OUTROS/ffspRyo_v3.zip"
DEFAULT_PROFILE = PROJECT / "data/ryo_v3_runtime_cut_20261006.json"
DEFAULT_ROM = CANDIDATE / "rom.sms"
DEFAULT_PROBE = CANDIDATE / "probe_record.json"
DEFAULT_MANIFEST = CANDIDATE / "scene_cut_lineage_draft_manifest.json"
BASE_GENERATOR = WORKSPACE / "tools/sms_wrapper/mugen2sms/generators/scene_cut.py"
BANK_BYTES = 16384
EXPECTED_FRAMES_PER_SLOT = 94
EXPECTED_ASSETS = 376

import sys

sys.path.insert(0, str(WORKSPACE / "tools/sms_wrapper"))
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


def validate(manifest: dict, source_path: Path, profile_path: Path,
             rom_bytes: bytes, probe: dict) -> list[dict]:
    errors: list[dict] = []

    def fail(code: str, detail=None):
        errors.append({"code": code, "detail": detail})

    if manifest.get("schema") != "luta_mugen_scene_cut_frame_lineage_draft_v1":
        fail("unsupported_manifest_schema", manifest.get("schema"))
    if "isolated patch prototype" not in manifest.get("classification", ""):
        fail("draft_classification_missing", manifest.get("classification"))

    source_hash = file_sha(source_path)
    if source_hash != manifest.get("source_zip_sha256"):
        fail("source_archive_sha256_mismatch", {
            "manifest": manifest.get("source_zip_sha256"), "actual": source_hash
        })
        return errors
    profile_hash = file_sha(profile_path)
    if profile_hash != manifest.get("profile_sha256"):
        fail("profile_sha256_mismatch", {
            "manifest": manifest.get("profile_sha256"), "actual": profile_hash
        })
    generator_hash = file_sha(BASE_GENERATOR)
    if generator_hash != manifest.get("base_generator_sha256"):
        fail("base_generator_sha256_mismatch", {
            "manifest": manifest.get("base_generator_sha256"), "actual": generator_hash
        })

    rom_hash = sha256(rom_bytes)
    probe_rom_hash = probe.get("build", {}).get("rom", {}).get("sha256")
    if rom_hash != manifest.get("candidate_rom_sha256") or rom_hash != probe_rom_hash:
        fail("candidate_rom_sha256_mismatch", {
            "manifest": manifest.get("candidate_rom_sha256"),
            "probe": probe_rom_hash,
            "actual": rom_hash,
        })

    try:
        with zipfile.ZipFile(source_path) as archive:
            air_bytes = archive.read(manifest["air_member"])
            sff_bytes = archive.read(manifest["sff_member"])
    except (KeyError, OSError, zipfile.BadZipFile) as exc:
        fail("source_archive_members_unreadable", str(exc))
        return errors

    if sha256(air_bytes) != manifest.get("air_sha256"):
        fail("source_air_sha256_mismatch")
    if sha256(sff_bytes) != manifest.get("sff_sha256"):
        fail("source_sff_sha256_mismatch")
    air_result = air_parser.parse(air_bytes.decode("latin-1"), manifest["air_member"])
    sprites, sff_warnings = sff_parser.parse(sff_bytes)
    if sff_warnings:
        fail("source_sff_parse_warnings", sff_warnings[:8])
    sprite_by_key = {(sprite.group, sprite.image): sprite for sprite in sprites}

    records = manifest.get("lineage")
    if not isinstance(records, list):
        fail("lineage_not_a_list")
        return errors
    if len(records) != EXPECTED_ASSETS or manifest.get("generated_asset_count") != EXPECTED_ASSETS:
        fail("generated_asset_count_mismatch", {
            "rows": len(records), "declared": manifest.get("generated_asset_count"),
            "expected": EXPECTED_ASSETS,
        })

    pairs: dict[tuple[str, int, int], list[str]] = {}
    frame_indices: dict[str, set[tuple[int, int]]] = {"p1_ken": set(), "p2_ryu": set()}
    seen_assets: set[tuple[str, int, int, str]] = set()
    for index, row in enumerate(records):
        try:
            slot = row["fighter_slot"]
            air = row["air"]
            source_sff = row["sff"]
            asset = row["generated_tile_asset"]
            action_id = int(air["action"])
            frame_index = int(air["frame_index"])
            group = int(air["group"])
            image = int(air["image"])
            variant = row["palette_variant"]
            asset_bank = int(asset["bank"])
            offset = int(asset["offset"])
            size = int(asset["size"])
            final_bank = int(row["final_rom_bank"])
            rom_offset = int(row["rom_offset"])
            asset_sha = str(asset["sha256"])
        except (KeyError, TypeError, ValueError) as exc:
            fail("malformed_lineage_row", {"row": index, "error": str(exc)})
            continue

        if slot not in frame_indices:
            fail("unexpected_fighter_slot", {"row": index, "slot": slot})
            continue
        frame_indices[slot].add((action_id, frame_index))
        pairs.setdefault((slot, action_id, frame_index), []).append(variant)
        asset_identity = (slot, action_id, frame_index, variant)
        if asset_identity in seen_assets:
            fail("duplicate_frame_palette_asset", {"row": index, "identity": asset_identity})
        seen_assets.add(asset_identity)
        if variant not in ("p1", "p2"):
            fail("unknown_palette_variant", {"row": index, "variant": variant})

        action = air_result.actions.get(action_id)
        if action is None or not 0 <= frame_index < len(action.frames):
            fail("missing_source_air_frame", {"row": index, "action": action_id,
                                                "frame_index": frame_index})
        else:
            source_frame = action.frames[frame_index]
            expected_air = {
                "action": action_id,
                "frame_index": frame_index,
                "line": source_frame.line,
                "group": source_frame.group,
                "image": source_frame.image,
            }
            if air != expected_air:
                fail("source_air_identity_mismatch", {"row": index,
                                                        "expected": expected_air, "actual": air})

        sprite = sprite_by_key.get((group, image))
        if sprite is None:
            fail("missing_source_sprite", {"row": index, "group": group, "image": image})
        else:
            expected_sff = {
                "group": sprite.group,
                "image": sprite.image,
                "sprite_index": sprite.index,
                "axis": [sprite.axis_x, sprite.axis_y],
                "pixel_sha256": sha256(sprite.pixels),
                "size": [sprite.width, sprite.height],
            }
            if source_sff != expected_sff:
                fail("source_sff_identity_mismatch", {"row": index,
                                                        "expected": expected_sff,
                                                        "actual": source_sff})

        if size <= 0 or offset < 0 or offset + size > BANK_BYTES:
            fail("tile_payload_crosses_bank", {"row": index, "bank": asset_bank,
                                                "offset": offset, "size": size,
                                                "bank_bytes": BANK_BYTES})
            continue
        expected_rom_offset = final_bank * BANK_BYTES + offset
        if rom_offset != expected_rom_offset:
            fail("rom_offset_disagrees_with_bank", {"row": index,
                                                      "expected": expected_rom_offset,
                                                      "actual": rom_offset})
        if rom_offset < 0 or rom_offset + size > len(rom_bytes):
            fail("tile_payload_outside_candidate_rom", {"row": index,
                                                          "offset": rom_offset,
                                                          "size": size})
            continue
        payload = rom_bytes[rom_offset:rom_offset + size]
        if sha256(payload) != asset_sha:
            fail("tile_payload_sha256_mismatch", {"row": index,
                                                    "expected": asset_sha,
                                                    "actual": sha256(payload)})

    for slot in ("p1_ken", "p2_ryu"):
        frames = frame_indices[slot]
        declared = manifest.get("frame_count_by_slot", {}).get(slot)
        if len(frames) != EXPECTED_FRAMES_PER_SLOT or declared != EXPECTED_FRAMES_PER_SLOT:
            fail("frame_count_by_slot_mismatch", {"slot": slot, "actual": len(frames),
                                                   "declared": declared,
                                                   "expected": EXPECTED_FRAMES_PER_SLOT})
    for key, variants in pairs.items():
        if sorted(variants) != ["p1", "p2"]:
            fail("palette_pair_incomplete", {"identity": key, "variants": sorted(variants)})
    return errors


def run_self_check(manifest: dict, source_path: Path, profile_path: Path,
                   rom_bytes: bytes, probe: dict) -> dict:
    checks = []

    def expect(name: str, errors: list[dict], expected_code: str | None = None):
        if expected_code is None:
            ok = not errors
        else:
            ok = any(item["code"] == expected_code for item in errors)
        checks.append({"name": name, "ok": ok,
                       "errors": [item["code"] for item in errors[:8]],
                       "expected_error": expected_code})

    expect("valid_baseline", validate(manifest, source_path, profile_path, rom_bytes, probe))

    with tempfile.TemporaryDirectory(prefix="lineage_manifest_selfcheck_") as temp:
        temp_dir = Path(temp)
        changed_source = temp_dir / "changed_source.zip"
        changed_source.write_bytes(source_path.read_bytes() + b"\x00")
        expect("changed_source_fails_closed",
               validate(manifest, changed_source, profile_path, rom_bytes, probe),
               "source_archive_sha256_mismatch")

        missing_sprite = copy.deepcopy(manifest)
        missing_sprite["lineage"][0]["air"]["group"] = 65535
        expect("missing_sprite_fails_closed",
               validate(missing_sprite, source_path, profile_path, rom_bytes, probe),
               "missing_source_sprite")

        crossed_bank = copy.deepcopy(manifest)
        first_asset = crossed_bank["lineage"][0]["generated_tile_asset"]
        first_asset["offset"] = BANK_BYTES - int(first_asset["size"]) + 1
        expect("bank_boundary_fails_closed",
               validate(crossed_bank, source_path, profile_path, rom_bytes, probe),
               "tile_payload_crosses_bank")

        wrong_rom = bytearray(rom_bytes)
        wrong_rom[0] ^= 1
        expect("wrong_rom_fails_closed",
               validate(manifest, source_path, profile_path, bytes(wrong_rom), probe),
               "candidate_rom_sha256_mismatch")

    failures = [item for item in checks if not item["ok"]]
    return {
        "schema": "luta_mugen_scene_cut_lineage_manifest_selfcheck_v1",
        "status": "PASS" if not failures else "FAIL",
        "checks": checks,
        "failures": failures,
        "scope": "isolated Ryo/Ryo draft contract fixtures; no canonical gate or emulator proof",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true",
                        help="run valid baseline plus four fail-closed mutations")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--rom", type=Path, default=DEFAULT_ROM)
    parser.add_argument("--probe", type=Path, default=DEFAULT_PROBE)
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    probe = read_json(args.probe)
    rom_bytes = args.rom.read_bytes()
    if args.self_check:
        result = run_self_check(manifest, args.source, args.profile, rom_bytes, probe)
    else:
        errors = validate(manifest, args.source, args.profile, rom_bytes, probe)
        result = {
            "schema": "luta_mugen_scene_cut_lineage_manifest_validation_v1",
            "status": "PASS" if not errors else "FAIL",
            "checks": [{"name": "manifest_contract", "ok": not errors}],
            "failures": errors,
            "scope": "isolated Ryo/Ryo draft contract; not a canonical gate or emulator proof",
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
