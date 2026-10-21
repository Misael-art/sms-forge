#!/usr/bin/env python3
"""Exercise a curation-only scene_cut manifest patch without touching tools/.

The patch draft adds source AIR/SFF references and generated tile locations to
each selected frame record. The canonical generator is read-only here; a temp
copy is imported, run on the archived Ryo source, and checked against the
preserved pages and candidate ROM.
"""
from __future__ import annotations

import difflib
import hashlib
import importlib.util
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
BASE_GENERATOR = WORKSPACE / "tools/sms_wrapper/mugen2sms/generators/scene_cut.py"
PATCH_OUT = CANDIDATE / "scene_cut_lineage_draft.patch"
REPORT_OUT = CANDIDATE / "scene_cut_lineage_draft_validation.json"
MANIFEST_OUT = CANDIDATE / "scene_cut_lineage_draft_manifest.json"

sys.path.insert(0, str(WORKSPACE / "tools/sms_wrapper"))
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


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_tile_macros(header: str, symbol: str) -> dict[str, int]:
    pattern = re.compile(
        rf"^#define\s+{re.escape(symbol)}_(SIZE|BANK|OFF)\s+(\d+)\s*$",
        re.MULTILINE,
    )
    return {name: int(value) for name, value in pattern.findall(header)}


def prepare_patch(source_text: str) -> str:
    anchor = "    ch = character_loader.load(Source(source_path))\n"
    replacement = anchor + (
        "    source_sprites_by_key = {(sprite.group, sprite.image): sprite\n"
        "                            for sprite in ch.sprites}\n"
    )
    if source_text.count(anchor) != 1:
        raise RuntimeError("scene_cut.py source-load anchor changed; draft patch needs review")
    patched = source_text.replace(anchor, replacement)
    anchor = "        pose_frames: dict[str, list[dict]] = {}\n        source_frames = {}\n"
    replacement = (
        "        pose_frames: dict[str, list[dict]] = {}\n"
        "        source_frames = {}\n"
        "        final_by_symbol = {artifact.symbol: artifact for artifact in final}\n"
    )
    if patched.count(anchor) != 1:
        raise RuntimeError("scene_cut.py frame-table anchor changed; draft patch needs review")
    patched = patched.replace(anchor, replacement)
    anchor = "                pose_frames[role[\"role\"]].append({\"stem\": symbol_stem, \"duration\": duration,\n                                                    \"raw_duration\": frame.time,\n                                                    \"stream_ticks\": stream_ticks,\n                                                    \"width\": width, \"height\": height})\n"
    replacement = anchor + (
        "                frame_asset_refs = {}\n"
        "                source_sprite = source_sprites_by_key[(frame.group, frame.image)]\n"
        "                for palette_variant, asset_symbol in ((\"p1\", tile_symbol), (\"p2\", p2_symbol)):\n"
        "                    asset_bank, asset_offset = bank_map[asset_symbol]\n"
        "                    asset_data = final_by_symbol[asset_symbol].data\n"
        "                    frame_asset_refs[palette_variant] = {\n"
        "                        \"symbol\": asset_symbol, \"bank\": asset_bank,\n"
        "                        \"offset\": asset_offset, \"size\": len(asset_data),\n"
        "                        \"sha256\": hashlib.sha256(asset_data).hexdigest(),\n"
        "                    }\n"
    )
    if patched.count(anchor) != 1:
        raise RuntimeError("scene_cut.py pose append anchor changed; draft patch needs review")
    patched = patched.replace(anchor, replacement)
    anchor = "                    \"size_runtime\": [width, height],\n"
    replacement = anchor + (
        "                    \"source_air\": {\"action\": aid, \"frame_index\": i,\n"
        "                                    \"line\": frame.line, \"group\": frame.group,\n"
        "                                    \"image\": frame.image},\n"
        "                    \"source_sff\": {\"group\": source_sprite.group, \"image\": source_sprite.image,\n"
        "                                    \"sprite_index\": source_sprite.index,\n"
        "                                    \"axis\": [source_sprite.axis_x, source_sprite.axis_y],\n"
        "                                    \"pixel_sha256\": hashlib.sha256(source_sprite.pixels).hexdigest()},\n"
        "                    \"generated_tile_assets\": frame_asset_refs,\n"
    )
    if patched.count(anchor) != 1:
        raise RuntimeError("scene_cut.py frame-record anchor changed; draft patch needs review")
    return patched.replace(anchor, replacement)


def main() -> int:
    source_text = BASE_GENERATOR.read_text(encoding="utf-8")
    patched_text = prepare_patch(source_text)
    diff = "".join(difflib.unified_diff(
        source_text.splitlines(keepends=True), patched_text.splitlines(keepends=True),
        fromfile="tools/sms_wrapper/mugen2sms/generators/scene_cut.py",
        tofile="scene_cut.py + MUGEN frame lineage fields (draft)",
    ))
    PATCH_OUT.write_text(diff, encoding="utf-8")

    checks = []

    def check(name: str, ok: bool, details=None):
        checks.append({"name": name, "ok": bool(ok), "details": details})

    with zipfile.ZipFile(SOURCE) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        air_name = next(name for name in members if name.lower().endswith(".air"))
        sff_name = next(name for name in members if name.lower().endswith(".sff"))
        air_bytes, sff_bytes = archive.read(air_name), archive.read(sff_name)
    air_result = air_parser.parse(air_bytes.decode("latin-1"), air_name)
    sprites, sff_warnings = sff_parser.parse(sff_bytes)
    sprite_by_key = {(item.group, item.image): item for item in sprites}
    check("source_sff_parse_clean", not sff_warnings, sff_warnings[:8])

    package_root = str(WORKSPACE / "tools/sms_wrapper")
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    with tempfile.TemporaryDirectory(prefix="scene_cut_lineage_draft_") as temp:
        temp_root = Path(temp)
        draft_module_path = temp_root / "scene_cut.py"
        draft_module_path.write_text(patched_text, encoding="utf-8")
        module_name = "mugen2sms.generators.scene_cut_lineage_draft"
        spec = importlib.util.spec_from_file_location(module_name, draft_module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load isolated scene_cut draft module")
        draft_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = draft_module
        spec.loader.exec_module(draft_module)

        rom = (CANDIDATE / "rom.sms").read_bytes()
        integrated_banks = (CANDIDATE / "banks_integrada.bin").read_bytes()
        layout = read_json(CANDIDATE / "bank_layout.json")
        scene_manifest = read_json(STUDY / "versus_scene_manifest.json")
        mapper_record = scene_manifest["mapper_images"][0]
        mapper_bytes = (STUDY / mapper_record["file"]).read_bytes()
        bank_size = 16384
        scene_range = {}
        for row in scene_manifest["banks"]:
            scene_range[("p1_ken", int(row["source_bank"]))] = int(row["bank"])
        for row in scene_manifest["bank_reuse"]["exact_aliases"]:
            scene_range[(row["fighter"], int(row["source_bank"]))] = int(row["bank"])
        scene_part = next(item for item in layout["parts"] if item["name"] == "scene_tiles")
        candidate_scene_start = (scene_part["first_bank"] - layout["first_bank"]) * bank_size
        candidate_scene = integrated_banks[candidate_scene_start:candidate_scene_start + scene_part["bytes"]]

        lineage_records = []
        reproduced_slots = []
        for fighter, first_bank in (("p1_ken", 2), ("p2_ryu", 5)):
            generated_dir = temp_root / fighter
            generated = draft_module.generate(SOURCE, PROFILE, generated_dir, first_bank, None)
            generated_manifest = read_json(generated_dir / "ken_scene_manifest.json")
            generated_header = (generated_dir / "ken_scene_runtime.h").read_text(encoding="ascii")
            preserved_dir = STUDY / fighter
            bank_mismatches = []
            for bank_row in generated["banks"]:
                name = bank_row["file"]
                if (generated_dir / name).read_bytes() != (preserved_dir / name).read_bytes():
                    bank_mismatches.append(name)
            check(f"draft_reproduces_38_scene_pages_{fighter}", not bank_mismatches,
                  {"bank_count": len(generated["banks"]), "mismatches": bank_mismatches})

            roles_by_action = {int(role["action"]): role for role in generated_manifest["roles"]}
            frames = generated_manifest.get("frames", {})
            frame_failures = []
            assets_before = len(lineage_records)
            for action_id, role in sorted(roles_by_action.items()):
                action = air_result.actions.get(action_id)
                if action is None or len(action.frames) != int(role["frame_count"]):
                    frame_failures.append(f"action {action_id}: AIR frame count mismatch")
                    continue
                for frame_index, frame in enumerate(action.frames):
                    key = f"anim:{action_id}.{frame_index}"
                    record = frames.get(key)
                    sprite = sprite_by_key.get((frame.group, frame.image))
                    if record is None or sprite is None:
                        frame_failures.append(f"{key}: missing manifest record or SFF sprite")
                        continue
                    source_air = record.get("source_air", {})
                    source_sff = record.get("source_sff", {})
                    assets = record.get("generated_tile_assets", {})
                    expected_air = {"action": action_id, "frame_index": frame_index,
                                    "line": frame.line, "group": frame.group, "image": frame.image}
                    expected_sff = {"group": sprite.group, "image": sprite.image,
                                    "sprite_index": sprite.index,
                                    "axis": [sprite.axis_x, sprite.axis_y],
                                    "pixel_sha256": sha256(sprite.pixels)}
                    if source_air != expected_air or source_sff != expected_sff:
                        frame_failures.append(f"{key}: source identity fields mismatch")
                    if record.get("size_source") != [sprite.width, sprite.height]:
                        frame_failures.append(f"{key}: source dimensions mismatch")

                    for variant in ("p1", "p2"):
                        asset = assets.get(variant, {})
                        symbol = asset.get("symbol")
                        macros = read_tile_macros(generated_header, symbol) if symbol else {}
                        if set(macros) != {"SIZE", "BANK", "OFF"}:
                            frame_failures.append(f"{key}/{variant}: generated symbol macros absent")
                            continue
                        if {"SIZE": asset.get("size"), "BANK": asset.get("bank"),
                            "OFF": asset.get("offset")} != macros:
                            frame_failures.append(f"{key}/{variant}: recorded asset location differs from header")
                            continue
                        source_bank = int(asset["bank"])
                        bank_path = generated_dir / f"ken_scene_bank{source_bank}.bin"
                        page = bank_path.read_bytes()
                        payload = page[int(asset["offset"]):int(asset["offset"]) + int(asset["size"])]
                        final_bank = scene_range.get((fighter, source_bank))
                        if final_bank is None or sha256(payload) != asset["sha256"]:
                            frame_failures.append(f"{key}/{variant}: source bank/payload hash mismatch")
                            continue
                        mapper_offset = (final_bank - int(mapper_record["bank_start"])) * bank_size
                        integrated_offset = (final_bank - layout["first_bank"]) * bank_size
                        rom_offset = final_bank * bank_size + int(asset["offset"])
                        if (mapper_bytes[mapper_offset + int(asset["offset"]):
                                      mapper_offset + int(asset["offset"]) + int(asset["size"])] != payload
                                or candidate_scene[integrated_offset + int(asset["offset"]):
                                                   integrated_offset + int(asset["offset"]) + int(asset["size"])] != payload
                                or rom[rom_offset:rom_offset + int(asset["size"])] != payload):
                            frame_failures.append(f"{key}/{variant}: candidate ROM payload mismatch")
                        lineage_records.append({
                            "fighter_slot": fighter,
                            "palette_variant": variant,
                            "air": expected_air,
                            "sff": {**expected_sff, "size": [sprite.width, sprite.height]},
                            "generated_tile_asset": asset,
                            "final_rom_bank": final_bank,
                            "rom_offset": rom_offset,
                        })

            slot_assets = len(lineage_records) - assets_before
            check(f"draft_frame_metadata_and_rom_payloads_{fighter}", not frame_failures,
                  {"frames": len(frames), "assets_verified": slot_assets,
                   "errors": frame_failures[:20]})
            check(f"draft_frame_count_94_{fighter}", len(frames) == 94, len(frames))
            check(f"draft_asset_count_188_{fighter}", slot_assets == 188, slot_assets)
            reproduced_slots.append({
                "fighter_slot": fighter,
                "first_bank": first_bank,
                "bank_pages_reproduced": len(generated["banks"]) - len(bank_mismatches),
                "frame_count": len(frames),
                "assets_checked": slot_assets,
            })

        check("draft_asset_count_376_total", len(lineage_records) == 376, len(lineage_records))
        check("candidate_rom_sha_matches_probe",
              sha256(rom) == read_json(CANDIDATE / "probe_record.json")["build"]["rom"]["sha256"])

        draft_manifest = {
            "schema": "luta_mugen_scene_cut_frame_lineage_draft_v1",
            "classification": "isolated patch prototype; not applied to canonical generator",
            "source_zip_sha256": file_sha(SOURCE),
            "air_member": air_name,
            "air_sha256": sha256(air_bytes),
            "sff_member": sff_name,
            "sff_sha256": sha256(sff_bytes),
            "profile_sha256": file_sha(PROFILE),
            "base_generator_sha256": file_sha(BASE_GENERATOR),
            "draft_generator_sha256": sha256(patched_text.encode("utf-8")),
            "candidate_rom_sha256": sha256(rom),
            "frame_count_by_slot": {item["fighter_slot"]: item["frame_count"] for item in reproduced_slots},
            "clean_reproduction": reproduced_slots,
            "generated_asset_count": len(lineage_records),
            "lineage": lineage_records,
            "limitations": [
                "Draft output is verified for this exact Ryo/Ryo profile and source archive only.",
                "Current scene-cut frame payload contains both palette variants; runtime palette/slot selection remains a separate semantic contract.",
                "This proves bytes and references, not visual fidelity or MUGEN command/state behavior.",
                "The canonical asset-binding gate remains PNG-scoped; the draft is not a pass of that gate.",
            ],
        }
        MANIFEST_OUT.write_text(json.dumps(draft_manifest, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")

    failures = [item for item in checks if not item["ok"]]
    report = {
        "schema": "luta_mugen_scene_cut_lineage_draft_validation_v1",
        "status": "PASS_ISOLATED_DRAFT" if not failures else "FAIL",
        "patch_path": str(PATCH_OUT.relative_to(CANDIDATE)),
        "patch_sha256": file_sha(PATCH_OUT),
        "draft_manifest_path": str(MANIFEST_OUT.relative_to(CANDIDATE)),
        "draft_manifest_sha256": file_sha(MANIFEST_OUT),
        "checks": checks,
        "failures": failures,
        "air_parser_warnings": {
            "count": len(air_result.warnings),
            "sample": air_result.warnings[:12],
            "scope": "full AIR file; selected action/frame identities are checked separately",
        },
        "sff_parser_warnings": sff_warnings,
        "disposition": "Keep as an isolated reviewable draft until authority docs are readable; do not copy into tools/sms_wrapper or promote the generated schema yet.",
    }
    REPORT_OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "checks_passed": len(checks) - len(failures),
        "checks_total": len(checks),
        "failures": failures,
        "frames_by_slot": {item["fighter_slot"]: item["frame_count"] for item in draft_manifest["clean_reproduction"]},
        "lineage_assets": len(draft_manifest["lineage"]),
        "patch_sha256": report["patch_sha256"],
        "manifest": str(MANIFEST_OUT),
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
