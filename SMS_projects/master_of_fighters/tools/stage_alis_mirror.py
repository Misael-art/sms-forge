"""Pack Alis × Alis with one physical palette and independent frame tables."""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps

from bind_scene02_repertoire import PROJECT, STAGE
from make_duel_scene02_assets import array, c_values, digest, pixels, planar
from pack_scene02_repertoire import PAGE_BYTES, frame_packet, verify_packet
from plan_scene02_repertoire import make_plan
from stage_alis_postures import POSES as POSTURE_CELS, connected_pixels, convert, rgb


STANDING = (tuple(f"alis_pe_1_curto_{i}" for i in (1, 2, 3)), ("prepare", "thrust", "recover"),
            tuple(f"alis_pe_2_curto_{i}" for i in (1, 2, 3)),
            tuple(f"alis_pe_2_longo_{i}" for i in (1, 2, 3)))
LOW = tuple(tuple(f"low_{i}_{phase}" for phase in (1, 2, 3)) for i in range(4))
AIR = tuple(tuple(f"air_{i}_{phase}" for phase in (1, 2, 3)) for i in range(4))
SPECIAL = tuple(f"alis_special_{i}" for i in (1, 2, 3))
THROW = tuple(f"throw_{i}" for i in range(1, 6))
CAUGHT = tuple(f"caught_{i}" for i in range(1, 6))
REACTIONS = ("hit_head", "hit_body", "hit_low", "impact_stand", "impact_low", "impact_air",
             "fall", "downed", "getup")
WALKS = tuple(f"alis_walk_{way}_{i}" for way in ("forward", "back") for i in range(1, 5))
POSTURES = tuple("alis_" + name for name in ("crouch_transition", "crouch", "crouch_guard",
                 "stand_guard", "jump_rise", "jump_apex", "jump_fall", "jump_diagonal", "jump_guard"))
ACTIONS = STANDING + LOW + AIR + (SPECIAL, THROW)
POSES = ("idle", *WALKS, *POSTURES, *(pose for family in ACTIONS for pose in family),
         *REACTIONS, *CAUGHT, "ground_rise")
SOURCE = PROJECT / "data/source_art/sprite_studies/scene02_alis_mirror_20261121"
POSTURE_SHEET = SOURCE.parent / "scene02_alis_postures_20261121/pose-study.png"

NEUTRAL_COLORS = {3: 6, 7: 11}
SECOND_COSTUME = {19: 24, 35: 44}
FABRIC_RAMP = (19, 35)
# Keep packet indices stable between the two native costumes. On the v4
# sheet these swatches are indigo armor, pink fabric and its pale highlight.
MODEL_SWATCHES = {16: 37, 19: 39, 35: 59}
PELVIS_X = 12
# Inclusive native regions, relative to the right-facing pelvis and ground
# canvas. Only neutral shades inside the named material are retouched.
KICK_MATERIAL_REGIONS = {
    "alis_pe_2_longo_1": (("cloth", -10, -4, 114, 118), ("cloth", -10, -7, 107, 107),
                         ("skin", -14, -12, 110, 111), ("gold", -15, -15, 113, 115)),
    "alis_pe_2_longo_2": (("cloth", -8, -2, 115, 118), ("cloth", -9, -7, 107, 108),
                         ("skin", -12, -11, 109, 111), ("gold", -13, -12, 114, 114)),
    "alis_pe_2_longo_3": (("cloth", -10, -5, 114, 118), ("cloth", -11, -8, 107, 108),
                         ("skin", -14, -13, 110, 112)),
    "air_2_1": (("skin", -8, -7, 111, 112), ("gold", -10, -10, 115, 115),
                ("cloth", -3, 0, 117, 118)),
    "air_3_1": (("skin", -8, -7, 112, 113), ("gold", -11, -10, 114, 116),
                ("cloth", -5, -2, 118, 122)),
    "air_3_2": (("skin", -10, -9, 115, 116), ("gold", -13, -12, 119, 120),
                ("cloth", -6, -4, 117, 123)),
    "air_3_3": (("skin", -8, -7, 109, 110), ("gold", -11, -10, 112, 113),
                ("cloth", -4, -2, 116, 119)),
}
MATERIAL_SHADES = {"cloth": (19, 35), "skin": (22, 27), "gold": (6, 11)}


def recolor(color, costume):
    color = NEUTRAL_COLORS.get(color, color)
    return SECOND_COSTUME.get(color, color) if costume else color


def restore_kick_material(color, x, y, regions):
    if color in (21, 42):
        for material, left, right, top, bottom in regions:
            if left <= x <= right and top <= y <= bottom:
                return MATERIAL_SHADES[material][int(color == 42)]
    return color


def read_cell(image, columns, rows, index):
    row, col = divmod(index, columns)
    return image.crop((col * image.width // columns, row * image.height // rows,
                       (col + 1) * image.width // columns, (row + 1) * image.height // rows))


def import_cel(image, divisor, slot, palette, x_origin=0, minimum_y=0,
               maximum_width=None, sample_bottom_trim=0, concept_materials=False, alpha_floor=192, fabric_midpoint=None):
    mask = image.getchannel("A").point(lambda alpha: 255 if alpha >= alpha_floor else 0)
    bounds = mask.getbbox()
    if bounds is None:
        raise ValueError("Empty source cel")
    image = image.crop(bounds)
    if maximum_width is not None:
        divisor = max(divisor, image.width / maximum_width)
    w, h = round(image.width / divisor), round(image.height / divisor)
    if slot - h < minimum_y:
        w, h = round(w * (slot - minimum_y) / h), slot - minimum_y
    sampling_box = None
    if sample_bottom_trim:
        # The trim is measured in native pixels. Apply the same sampling
        # phase to both channels and continue to register the sole at slot.
        sampling_box = (0, 0, image.width, image.height * (1 - sample_bottom_trim / h))
    # Mark the outline already present in the source before nearest-neighbor
    # can sample past that stroke into a neighboring highlight.
    ink = Image.frombytes("L", image.size, bytes(
        255 if a >= 160 and r <= 105 and g <= 70 and b <= 70 else 0
        for r, g, b, a in image.getdata()
    )).resize((w, h), Image.Resampling.BOX, box=sampling_box)
    image = image.resize((w, h), Image.Resampling.NEAREST, box=sampling_box)
    mask = image.getchannel("A")
    colors = {code: rgb(code) for code in palette[1:] if code not in SECOND_COSTUME.values()}
    opaque = {(x, y) for y in range(h) for x in range(w) if mask.getpixel((x, y)) >= alpha_floor}
    drawing = {}
    for x, y in opaque:
        red, green, blue, _ = image.getpixel((x, y))
        # A pink highlight belongs to the shared costume ramp even when
        # its RGB would be closer to white or gray in the hardware palette.
        fabric = red >= 115 and red - green >= 24 and blue - green >= 12 and red >= blue
        choices = FABRIC_RAMP if fabric else colors
        if concept_materials and not fabric:
            if blue >= 128 and green >= 96 and green - red >= 32 and blue >= green:
                choices = (56,)
            elif blue >= 70 and blue - red >= 22 and blue - green >= 21 and green < 116:
                choices = (16,)
            elif red >= 136 and 14 <= red - green <= 85 and 7 <= green - blue <= 61:
                choices = (22, 27)
        code = min(choices, key=lambda candidate: sum(
            (left - right) ** 2 for left, right in zip((red, green, blue), colors[candidate])))
        if fabric_midpoint is not None and code in FABRIC_RAMP:
            # These source sheets have different exposures. Recover the light
            # already painted into the detected fabric, before mapping to CRAM.
            code = FABRIC_RAMP[int(red + green >= fabric_midpoint)]
        if code in (42, 63) and ink.getpixel((x, y)) >= 82 and any(
            p not in opaque for p in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
        ):
            code = 1
        drawing[x + x_origin, y + slot - h] = code
    return connected_pixels(drawing)


def new_drawings(source, palette, posture_palette, model_palette=False):
    plan = [
        ("low.png", 3, 4, sum(LOW, ()), 6.5, 144, 0, (-2, -4, -2, -2, -7, -2, -2, -7, -2, -2, -9, -2)),
        ("reactions.png", 3, 3, (*REACTIONS[:7], "ground_rise", "getup"),
         5.45, 144, 0, (-6, -4, -5, -5, -5, -4, -13, -24, -6)),
    ]
    results = {}
    for name, columns, rows, poses, divisor, slot, minimum_y, x_values in plan:
        with Image.open(source / name) as file:
            image = file.convert("RGBA")
        for i, (pose, x_origin) in enumerate(zip(poses, x_values, strict=True)):
            cel = read_cell(image, columns, rows, i)
            width = 56 if pose == "ground_rise" else None
            scale = 6.25 if pose == "fall" else divisor
            trim = 0.4 if pose == "ground_rise" else 0
            results[pose] = import_cel(cel, scale, slot, palette, x_origin, minimum_y,
                                       maximum_width=width, sample_bottom_trim=trim,
                                       fabric_midpoint=(239 if name=="low.png" else 260) if model_palette else None)
    # Two whole-body tracks registered against the 52 px idle. The cut
    # boundaries follow the authored gaps rather than the provisional grid.
    with Image.open(source / "shield-grip-concept.png") as file:
        grip = file.convert("RGBA")
    grip_columns = (0, 545, 1010, 1527, grip.width)
    for index, origin in enumerate((-7, -7, -8, -14)):
        cel = grip.crop((grip_columns[index], 58, grip_columns[index + 1], 680))
        results[THROW[index]] = import_cel(cel, 11.5, 144, palette, origin,
                                          concept_materials=True, alpha_floor=245)
    with Image.open(source / "shield-stagger-concept.png") as file:
        stagger = file.convert("RGBA")
    for index, (pose, origin) in enumerate(zip(CAUGHT, (-4, -5, -3, -9, -13), strict=True)):
        results[pose] = import_cel(read_cell(stagger, 5, 1, index), 10.3, 144, palette, origin,
                                   concept_materials=True, alpha_floor=245)
    with Image.open(source / "shield-recovery-b53.png") as file:
        results["throw_5"] = import_cel(file.convert("RGBA"), 20.5, 144, palette, -7,
                                       concept_materials=True, alpha_floor=245)
    with Image.open(POSTURE_SHEET) as file:
        posture = file.convert("RGBA")
    for index in (1, 2):
        pose, x_adjust, y_adjust = POSTURE_CELS[index]
        results[pose] = convert(read_cell(posture, 3, 3, index), posture_palette, x_adjust, y_adjust, divisor=6.35)
    with Image.open(source / "air-b40.png") as file:
        air = file.convert("RGBA")
    for step, poses in enumerate(AIR[:2]):
        for phase, pose in enumerate(poses):
            cel = read_cell(air, 4, 4, step * 4 + phase)
            results[pose] = import_cel(cel, 5.55, 144, palette, -2)
    # The light contact loses one fringe row after component cleanup.
    results["air_2_2"] = import_cel(read_cell(air, 4, 4, 9), 5.08, 145, palette, -4,
                                  concept_materials=True, alpha_floor=235)
    with Image.open(source / "air-kicks-concept.png") as file:
        kicks = file.convert("RGBA")
    for index, pose, origin in ((0, "air_2_1", -2), (2, "air_2_3", -2), (3, "air_3_1", -2),
                                (4, "air_3_2", -4), (5, "air_3_3", -2)):
        results[pose] = import_cel(read_cell(kicks, 3, 2, index), 8.25, 144, palette, origin,
                                  concept_materials=True, alpha_floor=245)
    for pose, regions in KICK_MATERIAL_REGIONS.items():
        if pose in results:
            results[pose] = {point: restore_kick_material(color, point[0] - PELVIS_X, point[1], regions)
                             for point, color in results[pose].items()}
    with Image.open(source / "air-grips-b48.png") as file:
        contact = file.convert("RGBA")
    for index, (pose, origin, scale) in enumerate((("air_0_2", -2, 15.7), ("air_1_2", 4, 16.0))):
        results[pose] = import_cel(read_cell(contact, 2, 1, index), scale, 144, palette, origin,
                                       fabric_midpoint=205 if model_palette else None)
    with Image.open(source / "floor-material-b48.png") as file:
        cel = ImageOps.mirror(read_cell(file.convert("RGBA"), 1, 2, 0))
        results["downed"] = import_cel(cel, 26, 144, palette, -25, fabric_midpoint=259 if model_palette else None)
    return results


def recolor_control(row, old_palette, palette, costume):
    result = dict(row)
    right = row["direction"] == "right"
    shift = -PELVIS_X if right else PELVIS_X
    regions = KICK_MATERIAL_REGIONS.get(row["pose"], ())
    cells = []
    for x, top, pattern in row["sprite_cells"]:
        indices = pixels(bytes.fromhex(pattern))
        if row["pose"] == "alis_pe_1_curto_2":
            # The contact cel inherits a pale cuff from the old arm crop.
            # Keep the boot whites and restore the gold band before the fist.
            for column in (22, 23):
                tile_x = (column if right else -column - 1) - x
                if not 0 <= tile_x < 8:
                    continue
                for y in range(max(110, top), min(113, top + 8)):
                    offset = (y - top) * 8 + tile_x
                    if indices[offset] and old_palette[indices[offset]] == 63:
                        indices[offset] = old_palette.index(27 if y == 112 else 11, 1)
        if regions:
            for offset, index in enumerate(indices):
                if index:
                    screen_x = x + shift + offset % 8
                    canonical_x = screen_x if right else -screen_x - 1
                    color = restore_kick_material(old_palette[index], canonical_x, top + offset // 8, regions)
                    indices[offset] = old_palette.index(color, 1)
        converted = [palette.index(recolor(old_palette[index], costume), 1) if index else 0 for index in indices]
        cells.append([x + shift, top, planar(converted).hex()])
    result["sprite_cells"] = cells
    result["background_pixels"] = [
        [x + shift, y, recolor(restore_kick_material(color, x + shift if right else -x - shift - 1,
                                                     y, regions), costume)]
        for x, y, color in row["background_pixels"]
    ]
    return result


def fit_cel(drawing, palette, backdrop, costume, right, airborne):
    art = {(x - PELVIS_X if right else -x + PELVIS_X - 1, y): recolor(color, costume)
           for (x, y), color in drawing.items()}
    placement = make_plan(art, palette, () if airborne else backdrop, max_objects=32)
    if placement is None:
        return None
    cells, spill, _ = placement
    return dict(sprite_cells=[[x, y, pattern.hex()] for x, y, pattern in cells],
                background_pixels=[[x, y, color] for (x, y), color in spill.items()])


def keep_dark_outline(row, palette):
    """Navy armor goes violet in v4. Keep exposed navy ink as opaque black."""
    navy, black = palette.index(16), palette.index(0, 1)
    occupied = {(x,y) for x,y,_ in row["background_pixels"]}
    tiles = []
    for left,top,encoded in row["sprite_cells"]:
        ink = pixels(bytes.fromhex(encoded))
        tiles.append((left,top,ink))
        occupied.update((left+i%8,top+i//8) for i,c in enumerate(ink) if c)
    result = []
    for left,top,ink in tiles:
        for i,c in enumerate(ink):
            if c==navy:
                x,y=left+i%8,top+i//8
                if any(pt not in occupied for pt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):
                    ink[i]=black
        result.append([left,top,planar(ink).hex()])
    return dict(row,sprite_cells=result)


def sheet_drawings(folder):
    """Read native, pelvis-registered cels from the character construction sheet."""
    spec = json.loads((folder / "revisao.json").read_text())
    path = folder / spec["arquivo"]
    if digest(path) != spec["sha256"]:
        raise ValueError("Character sheet differs from its art receipt")
    width, height = spec["celula_px"]
    pivot_x, pivot_y = spec["pivo_do_chao_na_celula"]
    ids = spec["ids"]
    if len(ids) != len(set(ids)) or any(i not in range(len(POSES)) for i in ids):
        raise ValueError("Invalid pose list in character sheet")
    drawings = {}
    with Image.open(path) as sheet:
        sheet = sheet.convert("RGBA")
        if sheet.size != (len(ids) * width, height):
            raise ValueError("Character sheet dimensions do not match the cel grid")
        for column, index in enumerate(ids):
            cell = read_cell(sheet, len(ids), 1, column)
            drawing = {}
            for offset, (r, g, b, alpha) in enumerate(cell.getdata()):
                if not alpha:
                    continue
                if alpha != 255 or r % 85 or g % 85 or b % 85:
                    raise ValueError(f"Non-native ink in {POSES[index]}")
                x = PELVIS_X + offset % width - pivot_x
                y = 144 + offset // width - pivot_y
                drawing[x, y] = (r // 85) | ((g // 85) << 2) | ((b // 85) << 4)
            if not drawing:
                raise ValueError(f"Empty pose {POSES[index]}")
            drawings[POSES[index]] = drawing
    return drawings


def build(control, source, out, foundation=False, *, extra_drawings=None, stage_header=STAGE, review_sheet=None, model_palette=False):
    plan = json.loads(control.read_bytes())
    old_palette = plan["sprite_palette"]
    palette = [code for code in old_palette if code not in NEUTRAL_COLORS] + list(SECOND_COSTUME.values())
    backdrop = plan["background_palette"]
    assert len(palette) == 16 and len(set(palette[1:])) == 15
    art = {} if foundation else new_drawings(source, palette, old_palette, model_palette)
    pose_order = POSES + tuple(extra_drawings or ())
    if extra_drawings:
        art.update(extra_drawings)
    if review_sheet is not None:
        art.update(sheet_drawings(review_sheet))
    base = {(row["pose"], row["direction"] == "right"): row for row in plan["frames"]
            if row["actor"] == "alis" and row["pose"] not in art}
    if not foundation and set(POSES) - set(art) - {name for name, _ in base}:
        raise ValueError("Mirror action table is incomplete")
    stage = stage_header.read_text("ascii")
    backgrounds = bytes(c_values(stage, "mof_duel_bg_stage"))
    rows = c_values(stage, "mof_duel_bg_rows")
    background = [backgrounds[i * 32:i * 32 + 32] for i in rows]
    pages = [bytearray()]

    def place(data):
        page = pages[-1]
        if len(page) + len(data) > PAGE_BYTES:
            pages.append(bytearray())
            page = pages[-1]
        bank, address = len(pages) + 1, 0x8000 + len(page)
        page.extend(data)
        return bank, address

    poses, geometry, sprite_coordinates, sizes = [], [], [], []
    for player in (0, 1):
        if player:
            costume_stride = len(pages)
            pages.append(bytearray())
        for name in pose_order:
            for right in (False, True):
                index = pose_order.index(name) * 2 + int(right)
                if (name, right) in base:
                    row = recolor_control(base[name, right], old_palette, palette, player)
                elif foundation:
                    if not player:
                        geometry.append(geometry[int(right)])
                        sprite_coordinates.append(sprite_coordinates[int(right)])
                    continue
                else:
                    airborne = name.startswith("air_") or name in ("impact_air", "fall")
                    row = fit_cel(art[name], palette, backdrop, player, right, airborne)
                    if row is None:
                        raise ValueError(f"{name}/{right}/P{player + 1} exceeds four sprites per line")
                if model_palette:
                    row = keep_dark_outline(row,palette)
                packet = frame_packet(row, backdrop, background, contiguous_sprites=True)
                verify_packet(packet, row, backdrop, background, contiguous_sprites=True)
                bank, address = place(packet)
                count = len(row["sprite_cells"])
                spill = max(packet[int.from_bytes(packet[1 + i*2:3 + i*2], "little")] for i in range(8))
                sizes.append((count, spill))
                layout = (address, bank - (costume_stride if player else 0), count, spill)
                coordinates = packet[17:17 + 2 * count]
                if player and (geometry[index] != layout or sprite_coordinates[index] != coordinates):
                    raise ValueError(f"Costumes differ in packet layout for {name}/{right}")
                if not player:
                    geometry.append(layout)
                    sprite_coordinates.append(coordinates)
                poses.append(dict(name=name, player=player, right=right, bank=bank, address=address,
                                  count=count, spill_tiles=spill, **row))
    if len(pages) != 2 * costume_stride or len(pages) > 30:
        raise ValueError("Mirror costume banks do not fit two equal regions in 512 KiB")
    if model_palette:
        if any(c in FABRIC_RAMP for row in poses for _,_,c in row["background_pixels"]):
            raise ValueError("Fabric escaped the sprite palette into a weapon tile")
        palette = [MODEL_SWATCHES.get(c,c) for c in palette]
    max_count, max_spill = (max(x[i] for x in sizes) for i in (0, 1))
    margin = max(32, *(max(-x, x + 7) for row in poses for x, _, _ in row["sprite_cells"]),
                 *(abs(x) for row in poses for x, _, _ in row["background_pixels"]))
    assert max_count <= 32 and 2 * len(pose_order) < 255
    out.mkdir(parents=True)
    packed = bytearray()
    bank_rows = []
    for number, raw in enumerate(pages, 2):
        path = out / f"bank-{number:02d}.bin"
        path.write_bytes(raw.ljust(PAGE_BYTES, b"\xff"))
        packed.extend(path.read_bytes())
        bank_rows.append(dict(bank=number, file=path.name, sha256=digest(path)))
    source_hashes = {p.name: digest(p) for p in source.glob("*.png")}
    if review_sheet is not None:
        for file in ("revisao.json", "poses.png"):
            source_hashes[f"../{review_sheet.name}/{file}"] = digest(review_sheet / file)
    if not foundation:
        source_hashes[f"../{POSTURE_SHEET.parent.name}/{POSTURE_SHEET.name}"] = digest(POSTURE_SHEET)
    (out / "repertoire-pages.json").write_text(json.dumps(dict(
        format="mof_scene02_mirror_v1", banks=bank_rows, palette=palette,
        source_sha256=source_hashes,
        control_sha256=digest(control), foundation=foundation, max_count=max_count, max_spill=max_spill,
        arena_margin=margin, pelvis_translation=PELVIS_X, costume_bank_stride=costume_stride,
        frames=poses), separators=(",", ":")) + "\n")
    bank_path = out / "mirror-banks.bin"
    bank_path.write_bytes(packed)
    header = [
        "/* Generated by stage_alis_mirror.py. */",
        f"#define MOF_MIRROR_POSES {len(pose_order)}u",
        f"#define MOF_MIRROR_SPILL {max(1, 2 * max_spill)}u",
        f"#define MOF_MIRROR_COSTUME_BANKS {costume_stride}u",
        *(f"#define MOF_MIRROR_{name.upper()} {i}u" for i, name in enumerate(pose_order)),
        "typedef struct { uint16_t address; uint8_t bank, count, spill; } MofMirrorFrame;",
        f"static const MofMirrorFrame mirror_frames[{2*len(pose_order)}] = {{\n"
        + ",\n".join(f"{{0x{address:04X}u,{bank}u,{count}u,{spill}u}}"
                     for address, bank, count, spill in geometry) + "\n};",
        array("mirror_action_start", [pose_order.index(family[0]) for family in ACTIONS] +
              ([pose_order.index("palma_1")] if extra_drawings else []) +
              ([pose_order.index("riposte_1")] if "riposte_1" in pose_order else [])),
        array("mof_duel_sprite_palette", palette), array("mof_duel_bg_palette", backdrop),
        array("mof_duel_bg_stage", backgrounds), array("mof_duel_bg_rows", rows),
        f"#define MOF_DUEL_ARENA_MARGIN {margin}u",
    ]
    (out / "duel_mirror_assets.h").write_text("\n\n".join(header) + "\n")
    manifest = json.loads((PROJECT / ".mddev/duel_scene02_hold_6_build.json").read_bytes())
    tc = manifest["toolchain"]
    tc.pop("code_size_sources", None)
    tc["defines"].update(MOF_DUEL_REPERTOIRE=1, MOF_DUEL_FAST_SAT=1,
                         MOF_DUEL_SCENE_POSTURES=1, MOF_DUEL_SCENE_CROSSOVER=1,
                         MOF_DUEL_SCENE_SPECIALS=1, MOF_DUEL_SCENE_MIRROR=1)
    if foundation:
        tc["defines"]["MOF_DUEL_MIRROR_FOUNDATION"] = 1
    tc.setdefault("include_dirs", []).append(out.relative_to(PROJECT).as_posix())
    tc["makesms_extra"] = ["-pp", "-mbank", f"{bank_path.relative_to(PROJECT)}:0:{len(pages)}:2"]
    (out / "mirror_build.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{len(pose_order)} poses, {len(pages)} banks, {max_count} sprites and {max_spill} P0 cells per actor")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("control", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--foundation", action="store_true")
    args = parser.parse_args()
    build(args.control.resolve(), args.source.resolve(), args.out.resolve(), args.foundation)
