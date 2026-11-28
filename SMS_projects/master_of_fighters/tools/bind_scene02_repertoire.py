"""Validate the art banks and bind their mapper addresses to both builds."""

import argparse
import json
from pathlib import Path
import re

from make_duel_scene02_assets import ALIS, HAYATO, array, c_values, digest

PROJECT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = PROJECT / "out/diagnostics/repertoire_20261119"
STAGE = PROJECT / "out/diagnostics/duel_execution_20261119/generated/duel_scene02_assets.h"
NORMALS = ("pe_1_curto", "pe_2_curto", "pe_2_longo")
ALIS_POSTURES = tuple(("alis", "alis_" + pose) for pose in (
    "crouch_transition", "crouch", "crouch_guard", "stand_guard", "jump_rise",
    "jump_apex", "jump_fall", "jump_diagonal", "jump_guard",
))
HAYATO_JAB_START = ("hayato", "hayato_pe_1_curto_1")
PAGE_BYTES = 0x4000


def pose_order():
    for actor, legacy in (("hayato", HAYATO), ("alis", ALIS)):
        yield from ((actor, pose) for pose in legacy)
        for action in NORMALS:
            yield from ((actor, f"{actor}_{action}_{pose}") for pose in range(1, 4))


def verify_rom(path, bank_dir):
    pages = json.loads((bank_dir / "repertoire-pages.json").read_bytes())
    rom = path.read_bytes()
    expected_size = (256 if len(pages["banks"]) <= 14 else 512) * 1024
    if len(rom) != expected_size or rom[0x7FF0:0x7FF8] != b"TMR SEGA":
        raise ValueError("Repertoire ROM has an invalid size or SMS header")
    for row in pages["banks"]:
        source = bank_dir / row["file"]
        first = row["bank"] * PAGE_BYTES
        if digest(source) != row["sha256"] or rom[first:first + PAGE_BYTES] != source.read_bytes():
            raise ValueError(f"ROM mapper bank {row['bank']} differs from the verified art")
    return {"rom_sha256": digest(path), "bytes": len(rom),
            "verified_banks": [row["bank"] for row in pages["banks"]]}


def bind(bank_dir, destination):
    pages = json.loads((bank_dir / "repertoire-pages.json").read_bytes())
    contiguous_sprites = pages["format"] == "mof_scene02_repertoire_pages_v3"
    precomposed = contiguous_sprites or pages["format"] == "mof_scene02_repertoire_pages_v2"
    if (precomposed and pages.get("stage_sha256") != digest(STAGE)) or (
        not precomposed and pages["format"] != "mof_scene02_repertoire_pages_v1"
    ):
        raise ValueError("Unrecognized bank format or different scene backdrop")
    added = [tuple(pose) for pose in pages.get("added_poses", [])]
    crossing = pages.get("crossing_faces", False)
    poses = [*pose_order(), *added]
    if (len(set(poses)) != len(poses) or pages["roundtrip_verified_frames"] != 2 * len(poses) or
        pages["roundtrip_verified_p0_phases"] != 16 * len(poses)):
        raise ValueError("Incomplete pose/phase verification")
    if crossing and (2 * len(poses) >= 255 or
                     pages["orientations"][0]["initial_atlas"] != pages["orientations"][1]["initial_atlas"]):
        raise ValueError("Crossing requires one shared atlas and byte-sized physical IDs")
    banks = sorted(row["bank"] for row in pages["banks"])
    if banks != list(range(2, 2 + len(banks))) or not 9 <= len(banks) <= 30:
        raise ValueError("Expected contiguous art banks within the 512 KiB cartridge limit")
    if not added and len(banks) != 9:
        raise ValueError("The original standing repertoire uses nine art banks")
    contents = {}
    for row in pages["banks"]:
        source = bank_dir / row["file"]
        raw = source.read_bytes()
        if len(raw) != PAGE_BYTES or digest(source) != row["sha256"]:
            raise ValueError(f"Art bank integrity failed: {source}")
        contents[row["bank"]] = raw

    def checked(row):
        first = row["address"] - 0x8000
        last = first + row["bytes"]
        if not 0 <= first < last <= PAGE_BYTES:
            raise ValueError(f"Bank record outside mapper slot: {row}")
        return contents[row["bank"]][first:last]

    frames, atlases = [], []
    walking_is_sprite_only = True
    jab_has_initial_slot = True
    for face, orientation in zip(("right", "left"), pages["orientations"], strict=True):
        if orientation["hayato_facing"] != face:
            raise ValueError("Unrecognized orientation in the bank receipt")
        atlas = orientation["initial_atlas"]
        tiles = orientation["initial_tiles"]
        resident = checked(atlas)
        if len(resident) != tiles * 32 or tiles > 256:
            raise ValueError("Invalid startup atlas")
        atlases.append(f"{{0x{atlas['address']:04X}u, {atlas['bank']}u, {tiles}u}}")
        by_pose = {(entry["actor"], entry["pose"]): entry for entry in orientation["frames"]}
        if set(by_pose) != set(poses):
            raise ValueError("Unexpected poses in the bank receipt")
        side = []
        for identity in poses:
            entry = by_pose[identity]
            packet = checked(entry)
            count = packet[0]
            initial = entry.get("initial_sprite_slot", 255)
            if identity == HAYATO_JAB_START and initial == 255:
                jab_has_initial_slot = False
            if not 1 <= count <= 32 or len(packet) < 17 + 34 * count + 8:
                raise ValueError(f"Invalid packet for {identity}")
            if initial != 255:
                first = 17 + count * 2
                expected = packet[first:first + count * 32] if contiguous_sprites else b"".join(
                    packet[19 + 34*i:51 + 34*i] for i in range(count))
                if resident[32*initial:32*(initial+count)] != expected:
                    raise ValueError(f"Boot atlas does not match {identity}")
            p0_kind = ""
            if added:
                offsets = [int.from_bytes(packet[1+2*i:3+2*i], "little") for i in range(8)]
                if any(offset < 17 + 34 * count or offset >= len(packet) for offset in offsets):
                    raise ValueError(f"Invalid background phase offsets for {identity}")
                phases = [bool(packet[offset]) for offset in offsets]
                p0_kind = f", {1 if all(phases) else 2 if any(phases) else 0}u"
                if "_walk_" in identity[1] and any(phases):
                    walking_is_sprite_only = False
                if identity in ALIS_POSTURES and any(phases):
                    raise ValueError(f"Posture must use sprite patterns only: {identity}")
            side.append(f"{{0x{entry['address']:04X}u, {entry['bank']}u, {count}u, {initial}u{p0_kind}}}")
        frames.append(",\n    ".join(side) if crossing else
                      "{\n    " + ",\n    ".join(side) + "\n  }")

    stage = STAGE.read_text("ascii")
    margin = re.search(r"#define MOF_DUEL_ARENA_MARGIN (\d+)u", stage)
    if not margin:
        raise ValueError("Missing arena margin")
    arena_margin = pages.get("arena_margin", int(margin[1]))
    if not isinstance(arena_margin, int) or not 0 <= arena_margin < 64:
        raise ValueError("Invalid arena margin in bank receipt")
    output = [
        "/* Generated by bind_scene02_repertoire.py. */",
        "typedef struct { uint16_t address; uint8_t bank, count, initial"
        + (", p0_kind" if added else "") + "; } MofRepertoireFrame;",
        "typedef struct { uint16_t address; uint8_t bank, tiles; } MofRepertoireAtlas;",
        f"#define MOF_REPERTOIRE_FRAMES {len(poses)}u",
        f"#define MOF_DUEL_ARENA_MARGIN {arena_margin}u",
        f"static const MofRepertoireAtlas mof_repertoire_atlas[2] = {{{', '.join(atlases)}}};",
        "static const MofRepertoireFrame mof_repertoire_frames"
        + ("[2 * MOF_REPERTOIRE_FRAMES]" if crossing else "[2][MOF_REPERTOIRE_FRAMES]") + " = {\n  "
        + ",\n  ".join(frames) + "\n};",
        array("mof_duel_sprite_palette", pages["p1_palette"]),
        array("mof_duel_bg_palette", pages["p0_palette"]),
        array("mof_duel_bg_stage", c_values(stage, "mof_duel_bg_stage")),
        array("mof_duel_bg_rows", c_values(stage, "mof_duel_bg_rows")),
    ]
    if added:
        bg_limit = max(25, pages["max_background_cells"])
        if bg_limit > 80:
            raise ValueError("Two compositor pages exceed their reserved VRAM tiles")
        output.append(f"#define MOF_REPERTOIRE_BG_LIMIT {bg_limit}u")
    features = {}
    if crossing:
        features["MOF_DUEL_SCENE_CROSSOVER"] = 1
        output.append(array("mof_repertoire_actor", [int(actor == "alis") for actor, _ in poses]))
    if set(ALIS_POSTURES).intersection(added):
        initial = poses.index(ALIS_POSTURES[0])
        if tuple(poses[initial:initial + len(ALIS_POSTURES)]) != ALIS_POSTURES:
            raise ValueError("Incomplete or reordered Alis posture family")
        features["MOF_DUEL_SCENE_POSTURES"] = 1
        output.append(f"#define MOF_ALIS_POSTURE_START {initial}u")
    for family, groups in (("WALK", ("walk_forward", "walk_back")), ("SPECIALS", ("special",))):
        keys = [(actor, f"{actor}_{action}_{frame}") for actor in ("hayato", "alis")
                for action in groups for frame in range(1, 5 if family == "WALK" else 4)]
        if not set(keys).intersection(added):
            continue
        if not set(keys).issubset(added):
            raise ValueError(f"Incomplete added family: {family}")
        features[f"MOF_DUEL_SCENE_{family}"] = 1
        if family == "WALK" and walking_is_sprite_only:
            features["MOF_REPERTOIRE_SPRITE_WALK"] = 1
            if not jab_has_initial_slot:
                raise ValueError("Hayato's short punch must start in the resident atlas")
            output.append(f"#define MOF_REPERTOIRE_HAYATO_JAB_START {poses.index(HAYATO_JAB_START)}u")
        for actor in ("hayato", "alis"):
            for action in groups:
                first = poses.index((actor, f"{actor}_{action}_1"))
                count = 4 if family == "WALK" else 3
                if poses[first:first + count] != [(actor, f"{actor}_{action}_{i}") for i in range(1, count + 1)]:
                    raise ValueError("Action's pose IDs are not consecutive")
                output.append(f"#define MOF_{actor.upper()}_{action.upper()} {first}u")
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "duel_repertoire_assets.h").write_text("\n\n".join(output) + "\n", encoding="ascii")
    combined = destination / f"art-banks-02-{banks[-1]:02d}.bin"
    combined.write_bytes(b"".join(contents[bank] for bank in banks))
    # This makesms build silently drops entries beyond eight merge operations.
    options = ["-pp", "-mbank", f"{combined.relative_to(PROJECT).as_posix()}:0:{len(banks)}:2"]
    for hold in (6, 8):
        baseline = PROJECT / f".mddev/duel_scene02_hold_{hold}_build.json"
        manifest = json.loads(baseline.read_bytes())
        toolchain = manifest["toolchain"]
        toolchain["defines"].update(MOF_DUEL_REPERTOIRE=1, MOF_DUEL_FAST_SAT=1)
        toolchain["defines"].update(features)
        if added:
            toolchain["defines"]["MOF_DUEL_REPERTOIRE_ASSETS"] = 1
            toolchain.setdefault("include_dirs", []).append(destination.relative_to(PROJECT).as_posix())
        if precomposed:
            toolchain["defines"]["MOF_DUEL_REPERTOIRE_PRECOMPOSED"] = 1
        if contiguous_sprites:
            toolchain["defines"]["MOF_DUEL_REPERTOIRE_CONTIGUOUS_SPRITES"] = 1
        toolchain.pop("code_size_sources", None)
        toolchain["makesms_extra"] = options
        (destination / f"duel_repertoire_hold_{hold}_build.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Bound {2 * len(poses)} art packets in {len(contents)} banks for independent 6/8 builds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--banks", type=Path, default=DIAGNOSTICS / "scene02-repertoire-banks-b02")
    parser.add_argument("--out", type=Path, default=DIAGNOSTICS / "scene02-repertoire-bound")
    parser.add_argument("--verify-rom", type=Path)
    args = parser.parse_args()
    if args.verify_rom:
        print(json.dumps(verify_rom(args.verify_rom, args.banks.resolve())))
    else:
        bind(args.banks.resolve(), args.out.resolve())
