"""Pack the verified Scene 02 layers for Sega mapper slot 2."""

import argparse
import json
from pathlib import Path
import struct

from make_duel_scene02_assets import c_values, digest, pixels, planar

PAGE_BYTES = 0x4000
PAGE_ADDRESS = 0x8000
FIRST_PAGE = 2
FIRST_POSES = {"idle", "R01", "prepare"}


def first_pose(row):
    return row["pose"] in FIRST_POSES or row["pose"].endswith("_1")


def phase_packet(spill, palette, phase, background=None):
    cells = {}
    for x, y, color in spill:
        left, sx = divmod(x + phase, 8)
        top, sy = divmod(y, 8)
        mask, chunky = cells.setdefault((left, top), ([0] * 8, [0] * 64))
        mask[sy] |= 1 << (7 - sx)
        chunky[sy * 8 + sx] = palette.index(color)
    payload = bytearray((len(cells),))
    for (left, top), (mask, chunky) in sorted(cells.items()):
        payload.extend(struct.pack("bB", left, top))
        payload.extend(mask)
        tile = planar(chunky)
        if background is not None:
            tile = bytes(bits | (stage & (mask[i // 4] ^ 255))
                         for i, (bits, stage) in enumerate(zip(tile, background[top], strict=True)))
        payload.extend(tile)
    return payload


def frame_packet(row, palette, background=None, contiguous_sprites=False):
    cells = row["sprite_cells"]
    payload = bytearray((len(cells),))
    payload.extend(b"\0" * 16)
    for left, top, pattern in cells:
        payload.extend(struct.pack("bB", left, top))
        if not contiguous_sprites:
            payload.extend(bytes.fromhex(pattern))
    if contiguous_sprites:
        for _, _, pattern in cells:
            payload.extend(bytes.fromhex(pattern))
    for phase in range(8):
        struct.pack_into("<H", payload, 1 + phase * 2, len(payload))
        payload.extend(phase_packet(row["background_pixels"], palette, phase, background))
    return payload


def verify_packet(packet, row, palette, background=None, contiguous_sprites=False):
    if packet[0] != len(row["sprite_cells"]):
        raise ValueError("Sprite count changed in the bank packet")
    for index, (expected_x, expected_y, expected_pattern) in enumerate(row["sprite_cells"]):
        coordinates = 17 + index * (2 if contiguous_sprites else 34)
        pattern = 17 + packet[0] * 2 + index * 32 if contiguous_sprites else coordinates + 2
        if struct.unpack_from("bB", packet, coordinates) != (expected_x, expected_y):
            raise ValueError("SAT coordinates changed in the bank packet")
        if packet[pattern:pattern + 32].hex() != expected_pattern:
            raise ValueError("Sprite pixels changed in the bank packet")
    cursor = 17 + packet[0] * 34
    expected = {(x, y): color for x, y, color in row["background_pixels"]}
    for phase in range(8):
        offset, = struct.unpack_from("<H", packet, 1 + phase * 2)
        if offset != cursor:
            raise ValueError("Invalid phase offset in the bank packet")
        count = packet[cursor]
        cursor += 1
        observed = {}
        for _ in range(count):
            left, top = struct.unpack_from("bB", packet, cursor)
            mask = packet[cursor + 2:cursor + 10]
            tile = pixels(packet[cursor + 10:cursor + 42])
            backdrop = pixels(background[top]) if background is not None else (0,) * 64
            for index, color in enumerate(tile):
                y, x = divmod(index, 8)
                if mask[y] & (1 << (7 - x)):
                    key = left * 8 + x - phase, top * 8 + y
                    if key in observed:
                        raise ValueError("Two P0 tiles own the same source position")
                    observed[key] = palette[color]
                elif color != backdrop[index]:
                    raise ValueError("A P0 packet changed an uncovered background pixel")
            cursor += 42
        if observed != expected:
            raise ValueError("A P0 phase changed source pixels")
    if cursor != len(packet):
        raise ValueError("Unexpected tail in the bank packet")


def boot_atlas(frames, added=(), priority=()):
    slots = {}
    patterns = bytearray()
    by_pose = {(row["actor"], row["pose"]): row for row in frames}
    legacy = [key for key, row in by_pose.items() if key not in added and first_pose(row)]
    for key in dict.fromkeys([*priority, *legacy]):
        row = by_pose[key]
        if priority and len(patterns) // 32 + row["sprite_count"] > 256:
            if key in priority:
                raise ValueError(f"Startup posture bank cannot fit {key}")
            continue
        slots[key] = len(patterns) // 32
        for _, _, tile in row["sprite_cells"]:
            patterns.extend(bytes.fromhex(tile))
    if len(patterns) > 256 * 32:
        raise ValueError("First poses exceed sprite pattern addressing")
    return slots, patterns


def crossing_atlas(sides):
    """Keep both neutral stances and the crest of the jump in the boot atlas."""
    index = {(i, row["actor"], row["pose"]): row
             for i, rows in enumerate(sides) for row in rows}
    anchors = (("hayato", "idle"), ("alis", "idle"), ("alis", "alis_jump_apex"),
               ("alis", "alis_crouch_transition"), ("hayato", "hayato_pe_1_curto_1"))
    slots, atlas = {}, bytearray()
    startup = [(side, actor, pose) for actor, pose in anchors for side in range(len(sides))]
    startup.append((1, "alis", "alis_jump_rise"))
    for key in startup:
        row = index[key]
        slots[key] = len(atlas) // 32
        for _, _, tile in row["sprite_cells"]:
            atlas.extend(bytes.fromhex(tile))
    if len(atlas) >= 256 * 32:
        raise ValueError("Crossing startup poses exceed the shared atlas")
    return slots, atlas


def pack(plan_path, destination, stage_path=None, contiguous_sprites=False, crossing=False):
    plan = json.loads(plan_path.read_bytes())
    added = {tuple(pose) for pose in plan.get("added_poses", [])}
    priority = [tuple(pose) for pose in plan.get("boot_sprite_priority", [])]
    if plan["rejected"] or len(plan["frames"]) != 58 + 2 * len(added) or plan["max_sat"] > 64:
        raise ValueError("Expected both faces of every pose within SAT capacity")
    palette = plan["background_palette"]
    background = None
    if stage_path is not None:
        stage = stage_path.read_text("ascii")
        patterns = bytes(c_values(stage, "mof_duel_bg_stage"))
        rows = c_values(stage, "mof_duel_bg_rows")
        background = [patterns[32 * tile:32 * (tile + 1)] for tile in rows]
        if len(background) != 24 or any(len(tile) != 32 for tile in background):
            raise ValueError("Invalid Scene 02 row map for P0 precomposition")
    destination.mkdir(parents=True, exist_ok=False)
    pages = [bytearray()]

    def place(payload):
        if not payload or len(payload) > PAGE_BYTES:
            raise ValueError("Packet size does not fit one ROM bank")
        page = pages[-1]
        if len(page) + len(payload) > PAGE_BYTES:
            page = bytearray()
            pages.append(page)
        entry = {"bank": FIRST_PAGE + len(pages) - 1,
                 "address": PAGE_ADDRESS + len(page), "bytes": len(payload)}
        page.extend(payload)
        return entry

    result = {"format": "mof_scene02_repertoire_pages_v1", "plan_sha256": digest(plan_path),
              "p0_palette": palette, "p1_palette": plan["sprite_palette"],
              "orientations": [], "banks": []}
    if stage_path is not None:
        result["format"] = "mof_scene02_repertoire_pages_v3" if contiguous_sprites else "mof_scene02_repertoire_pages_v2"
        result["stage_sha256"] = digest(stage_path)
    if added:
        result["added_poses"] = plan["added_poses"]
        result["max_background_cells"] = plan["crossover"]["max_background_cells"]
    if "arena_margin" in plan:
        margin = plan["arena_margin"]
        if not 0 <= margin < 64 or plan["crossover"]["arena_gap_pixels"] != [24, 255 - 2 * margin]:
            raise ValueError("Arena margin does not match the validated crossover range")
        result["arena_margin"] = margin
    directions = (("right", "left"), ("left", "right"))
    sides = [[row for row in plan["frames"]
              if row["direction"] == (h_face if row["actor"] == "hayato" else a_face)]
             for h_face, a_face in directions]
    if crossing:
        if not contiguous_sprites or not priority:
            raise ValueError("Crossing needs the banked posture family")
        initial_slots, atlas = crossing_atlas(sides)
        initial_atlas = place(atlas)
        result["crossing_faces"] = True
    for side, (h_face, _) in enumerate(directions):
        frames = sides[side]
        if crossing:
            slots = {(actor, pose): slot for (face, actor, pose), slot in initial_slots.items()
                     if face == side}
        else:
            slots, atlas = boot_atlas(frames, added, priority)
            initial_atlas = place(atlas)
        orientation = {"hayato_facing": h_face, "initial_atlas": initial_atlas,
                       "initial_tiles": len(atlas) // 32, "frames": []}
        for row in frames:
            packet = frame_packet(row, palette, background, contiguous_sprites)
            verify_packet(packet, row, palette, background, contiguous_sprites)
            identity = row["actor"], row["pose"]
            entry = {"actor": identity[0], "pose": identity[1], **place(packet)}
            if identity in slots:
                entry["initial_sprite_slot"] = slots[identity]
            orientation["frames"].append(entry)
        result["orientations"].append(orientation)

    for bank, page in enumerate(pages, FIRST_PAGE):
        path = destination / f"bank-{bank:02d}.bin"
        path.write_bytes(page.ljust(PAGE_BYTES, b"\xff"))
        if path.read_bytes()[:len(page)] != page:
            raise ValueError(f"Bank changed while writing {path}")
        result["banks"].append({"bank": bank, "file": path.name,
                                "used_bytes": len(page), "sha256": digest(path)})
    result["roundtrip_verified_frames"] = len(plan["frames"])
    result["roundtrip_verified_p0_phases"] = len(plan["frames"]) * 8
    (destination / "repertoire-pages.json").write_text(json.dumps(result, indent=2) + "\n",
                                                       encoding="utf-8")
    print(json.dumps({"banks": len(pages), "initial_tiles": [
        entry["initial_tiles"] for entry in result["orientations"]]}))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("plan", type=Path)
    cli.add_argument("destination", type=Path)
    cli.add_argument("--scene-bg", type=Path, help="Precompose uncovered pixels over this authored stage")
    cli.add_argument("--contiguous-sprites", action="store_true", help="Pack each frame's sprite patterns as one stream")
    cli.add_argument("--crossing-faces", action="store_true", help="Use both sides at runtime")
    args = cli.parse_args()
    if args.contiguous_sprites and not args.scene_bg:
        cli.error("--contiguous-sprites requires --scene-bg")
    pack(args.plan, args.destination, args.scene_bg, args.contiguous_sprites, args.crossing_faces)
