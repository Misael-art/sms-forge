"""Pack the two Alis portraits, Palma and the native Battle register scores."""
import argparse
import gzip
import hashlib
import json
import struct
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageOps

from alis_lettering import FIGHTER_NAME_FONT, fighter_nameplates, lettering, stamp_word
from pack_alis_scenes import ART, PORT_ART, PALETTE, GOLD, WHITE, native, rgb
from make_duel_scene02_assets import PROJECT, planar
from stage_alis_mirror import SECOND_COSTUME

PAGE = 16384
# The mirror roster supplies one character. Both slots use her pre-fight expression.
FIGHTERS = {"alis_landale": {"name": "ALIS", "versus_face": 1}}
PAIR = ("alis_landale", "alis_landale")
TRACKS = {"FM": "61528cb9a677cad75ecfc050f58951e505dfdafd4eed7663f18c9ac83065671d",
          "PSG": "5c106cc7a58ec22e6089e29241cbfcf0fee2d692267b789e7f47a61667c07763"}


def battle_frames(folder, chip):
    with ZipFile(folder / f"PhantasyStar-SMS-{chip}.zip") as bundle:
        title, = [n for n in bundle.namelist() if " - Battle.vgm" in n]
        vgm = gzip.decompress(bundle.read(title))
    if hashlib.sha256(vgm).hexdigest() != TRACKS[chip]:
        raise ValueError(f"Unexpected {chip} Battle source")
    loop_command = 28 + struct.unpack_from("<I", vgm, 28)[0]
    total = struct.unpack_from("<I", vgm, 24)[0]
    frames = [bytearray() for _ in range(total // 735 + 1)]
    pos, samples, loop = 64, 0, None
    loop_prefix = bytearray()
    phase = 0
    while True:
        if pos == loop_command:
            loop, phase = divmod(samples, 735)
            loop_prefix = frames[loop]
            frames[loop] = bytearray()
        op = vgm[pos]
        pos += 1
        if op == 0x66:
            break
        if op == 0x62:
            samples += 735
        elif op == 0x61:
            samples += struct.unpack_from("<H", vgm, pos)[0]
            pos += 2
        elif op == 0x4f and chip == "PSG":
            if vgm[pos] != 255:
                raise ValueError("Stereo routing cannot be expressed on SMS")
            pos += 1
        elif op == (0x51 if chip == "FM" else 0x50):
            if samples % 735 != phase:
                raise ValueError("A register write falls between NTSC ticks")
            size = 2 if chip == "FM" else 1
            frames[samples // 735].extend(vgm[pos:pos+size])
            pos += size
        else:
            raise ValueError(f"Unsupported VGM command {op:02x}")
    if samples != total or samples % 735 != phase or loop is None:
        raise ValueError("Invalid track duration or loop")
    return frames, loop, loop_prefix


def score(folder, chip):
    frames, loop, prefix = battle_frames(folder, chip)
    tail = frames.pop()
    cuts = [i for i, writes in enumerate(frames) if writes or i in (0, loop)]
    data = bytearray()
    for start, end in zip(cuts, cuts[1:] + [len(frames)]):
        regs = frames[start]
        if start == loop:
            loop_offset = len(data)
            if chip == "PSG":
                data.extend(v if v & 128 else 0x40 | (v & 63) for v in prefix)
                data.append(1)  # PSGlib loop point
            elif prefix:
                raise ValueError("Unexpected FM writes before the loop at the same tick")
        if chip == "FM":
            count = len(regs) // 2
            if count >= 255 or end-start > 255:
                raise ValueError("FM packet exceeds player limits")
            data.extend((end-start, count))
            data.extend(regs)
        else:
            data.extend(v if v & 128 else 0x40 | (v & 63) for v in regs)
            waits = end-start
            while waits:
                length = min(8, waits)
                data.append(0x37 + length)
                waits -= length
    if chip == "FM":
        data.extend((0, len(tail)//2))  # final writes at the same tick as the loop's first writes
        data.extend(tail)
    else:
        data.extend(v if v & 128 else 0x40 | (v & 63) for v in tail)
        data.append(0)
    return data, loop_offset, {"source_sha256": TRACKS[chip], "frames": len(frames),
                               "loop_frame": loop, "bytes": len(data),
                               "writes": (sum(map(len, frames)) + len(prefix) + len(tail)) // (2 if chip == "FM" else 1)}


def versus_page(out, horizon=False, version=None, model_palette=False):
    colors = PALETTE.copy()
    colors[7], colors[9] = 52, 32
    if model_palette:
        colors[3],colors[11]=39,59
    alternate = colors.copy()
    alternate[3], alternate[11] = SECOND_COSTUME[19], SECOND_COSTUME[35]
    card = Image.new("L", (256, 192))
    plate_name = "palma_horizonte.png" if horizon else "pista.png"
    if version == 3:
        plate_name = "palma_saturn_v3.png"
    with Image.open(PORT_ART / plate_name) as source:
        bounds = (0, source.height*32//192, source.width, source.height*123//192)
        if horizon:
            bounds = (0,195,1536,640)
            clouds = native(source.crop((0,34,1536,132)), (224,10), colors)
        if version == 3:
            bounds = (0,185,1536,765)
            clouds = native(source.crop((75,6,1536,178)), (224,10), colors)
        panorama = native(source.crop(bounds), (224,72), colors)
    with Image.open(ART / "portraits.png") as sheet:
        w, h = sheet.size
        for side, fighter in enumerate(PAIR):
            face = FIGHTERS[fighter]["versus_face"]
            source = sheet.crop((face*w//3, 0, (face+1)*w//3, h)).convert("RGB")
            portrait = native(source, (80, 80), colors)
            if model_palette:
                neutral=colors.copy()
                neutral[3],neutral[11]=neutral[2],neutral[2]
                portrait=native(source,(80,80),neutral)
            if side or model_palette:
                # Only the cloth uses the second costume ramp. Keep metal, hair and skin.
                sample = source.resize(portrait.size, Image.Resampling.NEAREST)
                for y in range(60, 80):
                    for x in range(80):
                        red, green, blue = sample.getpixel((x,y))
                        if red >= 100 and red - green >= 24 and blue - green >= 12 and red >= blue:
                            portrait.putpixel((x,y), 11 if red >= 192 else 3)
            if side:
                card.paste(ImageOps.mirror(portrait), (160, 86))
            else:
                card.paste(portrait, (16, 6))

    p1, p2 = [FIGHTERS[fighter]["name"] for fighter in PAIR]
    first, second = fighter_nameplates((p1,p2), max_width=128)
    p2_left = ((240 - second.width) // 8) * 8
    right_edge = p2_left + second.getbbox()[2]
    lettering(card, "P1", 104, 18, GOLD)
    card.paste(first, (104,32))
    lettering(card, "P2", right_edge - 11, 51, GOLD)
    card.paste(second, (p2_left,64))
    lettering(card, "ESTÁGIO 01", 16, 171, GOLD)
    lettering(card, "ESPAÇOPORTO DE PALMA", 16, 182, WHITE)
    if version is not None:
        lettering(card, f"V{version}  CIMA/BAIXO", 145,171,GOLD)
        lettering(card, "1 SEGUE", 195,182,WHITE)
    draw = ImageDraw.Draw(card)
    draw.line((16,84,159,84), fill=13)
    draw.line((16,84,35,84), fill=GOLD)
    stamp_word(card, "X", 171, 53, 11, (WHITE,GOLD,3), slant=3)

    # CRAM selection is per tile, including the partial rows around the portrait.
    bounds = (160, 80, 240, 168)
    card.paste(card.crop(bounds).point(lambda v: v + 16), bounds)
    patterns = []
    ids = {}
    def tilemap(image):
        entries = bytearray()
        for y in range(0, image.height, 8):
            for x in range(0, image.width, 8):
                tile = image.crop((x,y,x+8,y+8))
                second = tile.getpixel((0,0)) >= 16
                if second:
                    tile = tile.point(lambda v: v & 15)
                raw = tile.tobytes()
                if raw not in ids:
                    number = len(patterns)
                    patterns.append(planar(raw))
                    for variant, flags in ((tile,0), (ImageOps.mirror(tile),0x200),
                                           (ImageOps.flip(tile),0x400),
                                           (tile.transpose(Image.Transpose.ROTATE_180),0x600)):
                        ids.setdefault(variant.tobytes(), number | flags)
                entries.extend(struct.pack("<H", ids[raw] | (0x800 if second else 0)))
        return entries

    first_map = None
    strips = bytearray()
    offsets = list(range(panorama.width-144,-1,-4))
    pal = bytes(c for code in colors + alternate for c in rgb(code)).ljust(768, b"\0")
    frames = []
    for left in offsets:
        frame = card.copy()
        frame.paste(panorama.crop((left,0,left+144,72)), (16,94))
        if horizon:
            cloud_x = left//8*4
            frame.paste(clouds.crop((cloud_x,0,cloud_x+144,10)), (16,94))
        frames.append(frame)
    if horizon or version is not None:
        from palma_panorama import fit_window
        fit_window(card, frames, offsets, colors)
    for index,frame in enumerate(frames):
        if index == 0:
            first_map = tilemap(frame)
        else:
            # 18 columns, 10 rows. Include the static pixels in the two partial rows.
            strips.extend(tilemap(frame.crop((16,88,160,168))))
        frame = frame.convert("P")
        frame.putpalette(pal)
        frame.save(out/("versus.png" if not index else f"versus-{index:02}.png"))
    if len(patterns)>448:
        raise ValueError(f"Panorama needs {len(patterns)} patterns and overlaps the name table")
    size = len(patterns)*32
    page = struct.pack("<H",size) + bytes(colors) + b"".join(patterns) + first_map
    if len(page) > PAGE - 16:
        raise ValueError("Portrait CRAM table overlaps the card")
    return page.ljust(PAGE-16,b"\xff") + bytes(alternate), strips, offsets


def pack(base, archive_dir, out):
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((base/"chapter.json").read_text())
    tc = manifest["toolchain"]
    banks = [entry.rsplit(":", 3) for entry in tc["makesms_extra"] if ":" in entry]
    bank = max(int(start)+int(count) for _, _, count, start in banks)
    horizon = "MOF_PORT_CLOUDS" in (PROJECT/tc["include_dirs"][1]/"alis_pages.h").read_text()
    page, strips, offsets = versus_page(out, horizon)
    fm, loop_offset, fm_info = score(archive_dir, "FM")
    psg, _, psg_info = score(archive_dir, "PSG")
    if bank+2 >= 64 or max(len(page), len(fm)+len(psg), len(strips)) > PAGE:
        raise ValueError("Matchup assets exceed cartridge banks")
    payload = b"".join(part.ljust(PAGE, b"\xff") for part in (page, fm+psg))
    (out/"matchup.bin").write_bytes(payload)
    rows = [",".join(str(byte) for byte in strips[i:i+24]) for i in range(0,len(strips),24)]
    (out/"matchup_pan.h").write_text("static const uint8_t mof_pan_strips[] = {\n"
                                     + ",\n".join(rows) + "\n};\n")
    tc["mapper_code_banks"]["SMSBANK_CAMERA"] = bank+2
    constants = {"MOF_VERSUS_PAGE":bank, "MOF_PAN_BANK":bank+2, "MOF_PAN_STEPS":len(offsets)-1,
                 "MOF_BATTLE_BANK":bank+1, "MOF_BATTLE_LOOP":0x8000+loop_offset,
                 "MOF_BATTLE_PSG":0x8000+len(fm)}
    (out/"matchup.h").write_text("".join(f"#define {key} {value}u\n" for key,value in constants.items()))
    tc["defines"]["MOF_ALIS_MATCHUP"]=1
    rel = out.relative_to(PROJECT).as_posix()
    tc["include_dirs"].append(rel)
    tc["makesms_extra"] += ["-mbank", f"{rel}/matchup.bin:0:2:{bank}"]
    (out/"chapter.json").write_text(json.dumps(manifest,indent=2)+"\n")
    (out/"sources.json").write_text(json.dumps({"title":"Battle","composer":"Tokuhiko Uwabo",
        "game":"Phantasy Star","recording":"Valley Bell (SMS Power!)","FM":fm_info,"PSG":psg_info,
        "camera_x":offsets, "window":[16,94,144,72],
        "name_font":{"family":"Barlow SemiBold", "sha256":hashlib.sha256(FIGHTER_NAME_FONT.read_bytes()).hexdigest()},
        "pattern_count":int.from_bytes(page[:2],"little")//32,
        "portraits":hashlib.sha256((ART/"portraits.png").read_bytes()).hexdigest(),
        "stage":hashlib.sha256((PORT_ART/("palma_horizonte.png" if horizon else "pista.png")).read_bytes()).hexdigest()},indent=2)+"\n")


if __name__ == "__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ("base","archive_dir","out"):
        cli.add_argument(name,type=Path)
    args=cli.parse_args()
    pack(args.base.resolve(),args.archive_dir.resolve(),args.out.resolve())
