#!/usr/bin/env python3
"""Empacota arte de rascunho em tiles SMS 4bpp + mapa de palco.

Sprites: chroma magenta vira indice 0 (gi preto NAO e transparente).
Vista 16x32 em ordem 8x16 (SPRITEMODE_TALL). PNG em res/ como pares 16x16.
Palco: nearest na paleta mestra, SEM Floyd-Steinberg; teto 128 tiles unicos
com merge por distancia RGB (nao Hamming de bitplane).
"""
import os, sys, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.normpath(os.path.join(HERE, ".."))
WRAP = os.path.normpath(os.path.join(PROJ, "..", "..", "tools", "sms_wrapper"))
sys.path.insert(0, WRAP)
from png_io import write_indexed_png, read_indexed_png
from png_to_sms_tiles import tile_bytes
import sms_palette as pal

RASC = os.path.join(PROJ, "rascunho")
RES = os.path.join(PROJ, "res")
INC = os.path.join(PROJ, "inc")
PROOF = os.path.join(RES, "proof")
PALETTES = os.path.join(RES, "palettes")
MAGENTA = (255, 0, 255)
WAIT, END = 0x38, 0x00


def mag_key(rgb):
    r, g, b = rgb
    return r > 180 and b > 180 and g < 120


def load_rgb(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = list(im.getdata())
    rows = [px[y * w:(y + 1) * w] for y in range(h)]
    return w, h, rows


def crop_body(rows, w, h):
    """Janela 1:2 centrada na massa do corpo, nao no bbox da arma."""
    mass = [0] * w
    ys, xs = [], []
    for y in range(h):
        for x in range(w):
            if not mag_key(rows[y][x]):
                mass[x] += 1
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit("sprite vazio apos chroma")
    y0, y1 = min(ys), max(ys)
    ch = y1 - y0 + 1
    cw = max(8, (ch + 1) // 2)
    tot = sum(mass) or 1
    cx = sum(i * mass[i] for i in range(w)) / tot
    x0 = int(cx - cw / 2)
    x0 = max(0, min(w - cw, x0))
    x1 = min(w, x0 + cw)
    cut = [list(rows[y][x0:x1]) for y in range(y0, y1 + 1)]
    return cut, x1 - x0, ch


def scale_nearest(rows, w, h, tw, th):
    out = []
    for y in range(th):
        sy = min(h - 1, y * h // th)
        out.append([rows[sy][min(w - 1, x * w // tw)] for x in range(tw)])
    return out


def force_key(rows, w, h):
    for y in range(h):
        for x in range(w):
            if mag_key(rows[y][x]):
                rows[y][x] = MAGENTA
    return rows


def quantize_nearest(rows, w, h):
    return [[pal.code_rgb(pal.nearest_code(rows[y][x])) for x in range(w)]
            for y in range(h)]


def cap_palette_spr(rows, w, h):
    """Indice 0 = magenta; gi preto fica opaco."""
    freq = {}
    for y in range(h):
        for x in range(w):
            c = tuple(rows[y][x])
            freq[c] = freq.get(c, 0) + 1
    others = sorted(((n, c) for c, n in freq.items() if c != MAGENTA), reverse=True)
    kept = [MAGENTA] + [c for _, c in others[:15]]
    index = {c: i for i, c in enumerate(kept)}
    fallback = {}
    for c in freq:
        if c in index:
            continue
        fallback[c] = min(range(len(kept)),
                          key=lambda i: sum((kept[i][k] - c[k]) ** 2 for k in range(3)))
    pixels = []
    for y in range(h):
        row = bytearray(w)
        for x in range(w):
            c = tuple(rows[y][x])
            row[x] = index[c] if c in index else fallback[c]
        pixels.append(bytes(row))
    return kept, pixels


def cap_palette_bg(rows, w, h, max_colors=16):
    freq = {}
    for y in range(h):
        for x in range(w):
            c = tuple(rows[y][x])
            freq[c] = freq.get(c, 0) + 1
    kept = [c for _, c in sorted(((n, c) for c, n in freq.items()), reverse=True)][:max_colors]
    index = {c: i for i, c in enumerate(kept)}
    fallback = {}
    for c in freq:
        if c in index:
            continue
        fallback[c] = min(range(len(kept)),
                          key=lambda i: sum((kept[i][k] - c[k]) ** 2 for k in range(3)))
    pixels = []
    for y in range(h):
        row = bytearray(w)
        for x in range(w):
            c = tuple(rows[y][x])
            row[x] = index[c] if c in index else fallback[c]
        pixels.append(bytes(row))
    return kept, pixels


def write_header(path, symbol, data):
    arr = ",".join("0x%02X" % b for b in data)
    open(path, "w").write(
        "/* gerado por pack_kage.py */\n"
        "#define %s_SIZE %d\n"
        "const unsigned char %s[%d] = {%s};\n"
        % (symbol.upper(), len(data), symbol, len(data), arr))


def tiles_tall(pixels):
    """16x32 -> 8 tiles na ordem 8x16 (N e N+1 empilhados)."""
    tiles = bytearray()
    for ty_pair in range(2):
        for tx in range(2):
            y8 = ty_pair * 2
            tiles += tile_bytes(pixels, tx, y8)
            tiles += tile_bytes(pixels, tx, y8 + 1)
    return bytes(tiles)


def split_ud(palette, pixels, symbol):
    os.makedirs(os.path.join(RES, "sprites"), exist_ok=True)
    os.makedirs(PROOF, exist_ok=True)
    u = os.path.join(RES, "sprites", symbol + "_u.png")
    d = os.path.join(RES, "sprites", symbol + "_d.png")
    write_indexed_png(u, 16, 16, palette, pixels[:16], trns=(0,))
    write_indexed_png(d, 16, 16, palette, pixels[16:32], trns=(0,))
    # Prova de geometria da entidade completa. O runtime continua usando as
    # duas metades 16x16 em SPRITEMODE_TALL; este artefato apenas torna
    # auditável que a fonte empacotada é uma entidade 16x32 inteira, sem
    # confundir a metade superior com a altura do personagem.
    full = os.path.join(PROOF, symbol + "_full.png")
    write_indexed_png(full, 16, 32, palette, pixels, trns=(0,))
    return u, d


def sprite_rgb16x32(path):
    w, h, rows = load_rgb(path)
    cut, cw, ch = crop_body(rows, w, h)
    scaled = scale_nearest(cut, cw, ch, 16, 32)
    force_key(scaled, 16, 32)
    return quantize_nearest(scaled, 16, 32)


def remap_to_palette(rows, w, h, palette):
    index = {c: i for i, c in enumerate(palette)}
    pixels = []
    for y in range(h):
        row = bytearray(w)
        for x in range(w):
            c = tuple(rows[y][x])
            if c in index:
                row[x] = index[c]
            else:
                row[x] = min(range(len(palette)),
                             key=lambda i: sum((palette[i][k] - c[k]) ** 2 for k in range(3)))
        pixels.append(bytes(row))
    return pixels


def pack_sprite_with_pal(nearest, symbol, palette):
    pixels = remap_to_palette(nearest, 16, 32, palette)
    split_ud(palette, pixels, symbol)
    tiles = tiles_tall(pixels)
    write_header(os.path.join(INC, symbol + "_tiles.h"), symbol + "_tiles", tiles)
    print("[OK] sprite", symbol, len(tiles), "B")
    return tiles


def bitrev8(v):
    v = ((v & 0xF0) >> 4) | ((v & 0x0F) << 4)
    v = ((v & 0xCC) >> 2) | ((v & 0x33) << 2)
    v = ((v & 0xAA) >> 1) | ((v & 0x55) << 1)
    return v


def flip_tiles_tall(data):
    def rev(i):
        src = data[i * 32:(i + 1) * 32]
        out = bytearray(32)
        for row in range(8):
            o = row * 4
            for p in range(4):
                out[o + p] = bitrev8(src[o + p])
        return bytes(out)
    order = [2, 3, 0, 1, 6, 7, 4, 5]
    return b"".join(rev(i) for i in order)


def tile_rgb64(rows, tx, ty):
    pix = []
    for y in range(8):
        for x in range(8):
            pix.extend(rows[ty * 8 + y][tx * 8 + x])
    return tuple(pix)


def pack_stage(jpg):
    w, h, rows = load_rgb(jpg)
    scaled = scale_nearest(rows, w, h, 256, 192)
    nearest = quantize_nearest(scaled, 256, 192)
    palette, pixels = cap_palette_bg(nearest, 256, 192)
    rgb_rows = [[palette[pixels[y][x]] for x in range(256)] for y in range(192)]
    unique = []
    index = {}
    freq = {}
    raw_map = []
    for ty in range(24):
        row = []
        for tx in range(32):
            key = tile_rgb64(rgb_rows, tx, ty)
            freq[key] = freq.get(key, 0) + 1
            row.append(key)
        raw_map.append(row)
    print("[stage] unique exact", len(freq))
    ranked = sorted(freq.keys(), key=lambda k: -freq[k])
    kept = ranked[:128]
    index = {k: i for i, k in enumerate(kept)}

    def nearest_kept(key):
        if key in index:
            return index[key]
        best, bd = 0, 10 ** 9
        for i, k in enumerate(kept):
            d = 0
            for a, b in zip(key, k):
                d += (a - b) * (a - b)
                if d >= bd:
                    break
            if d < bd:
                best, bd = i, d
        index[key] = best
        return best

    mmap = []
    for ty in range(24):
        row = []
        for tx in range(32):
            row.append(nearest_kept(raw_map[ty][tx]))
        mmap.append(row)
    tile_blob = bytearray()
    pal_index = {c: i for i, c in enumerate(palette)}
    for i, key in enumerate(kept):
        # materializa o tile i num canvas 8x8 e emite 4bpp
        cell = [bytearray(8) for _ in range(8)]
        for p in range(64):
            rgb = (key[p * 3], key[p * 3 + 1], key[p * 3 + 2])
            cell[p // 8][p % 8] = pal_index.get(rgb, 0)
        tile_blob += tile_bytes(cell, 0, 0)
    dst = os.path.join(RES, "bg", "stage.png")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    # reconstrói PNG do palco com tiles fundidos (o que a ROM mostra)
    recon = [bytearray(256) for _ in range(192)]
    for ty in range(24):
        for tx in range(32):
            key = kept[mmap[ty][tx]]
            for p in range(64):
                rgb = (key[p * 3], key[p * 3 + 1], key[p * 3 + 2])
                recon[ty * 8 + p // 8][tx * 8 + p % 8] = pal_index.get(rgb, 0)
    write_indexed_png(dst, 256, 192, palette, [bytes(r) for r in recon])
    write_header(os.path.join(INC, "stage_tiles.h"), "stage_tiles", bytes(tile_blob))
    flat = bytes(c for r in mmap for c in r)
    write_header(os.path.join(INC, "stage_map.h"), "stage_map", flat)
    open(os.path.join(RES, "bg", "stage_map.bin"), "wb").write(flat)
    print("[OK] stage tiles", len(kept), "map 32x24")
    return palette


def pal_to_sms(palette):
    out = []
    for i in range(16):
        rgb = palette[i] if i < len(palette) else (0, 0, 0)
        r, g, b = pal.nearest_code(rgb)
        out.append((b << 4) | (g << 2) | r)
    return bytes(out)


def tone(period, channel, volume):
    base = (0x80, 0xA0, 0xC0)[channel]
    return [base | (period & 0x0F), 0x40 | ((period >> 4) & 0x3F),
            base + 0x10 | (volume & 0x0F)]


def stream(frames):
    data = bytearray()
    for fr in frames:
        data.extend(fr)
        data.append(WAIT)
    data.append(END)
    return bytes(data)


def make_music():
    melody = (0x0C0, 0x0A8, 0x090, 0x0A8, 0x0C0, 0x0E0, 0x0C0, 0x100)
    bass = (0x280, 0x240, 0x200, 0x240)
    frames = []
    for i in range(32):
        frames.append(tone(melody[i % 8], 0, 1) + tone(bass[i % 4], 1, 3))
    return stream(frames)


def make_sfx_slash():
    frames = []
    for vol, mode in ((0, 5), (1, 5), (2, 5), (4, 4), (8, 4), (12, 4), (15, 4)):
        frames.append([0xE0 | mode, 0xF0 | vol])
    return stream(frames)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()


def write_provenance(poses, stage_origin):
    assets = []
    for name, path in poses:
        origin = os.path.relpath(path, PROJ).replace("\\", "/")
        digest = sha256(path)
        for suf in ("_u.png", "_d.png"):
            assets.append({
                "file": "res/sprites/" + name + suf,
                "origin": origin,
                "tool": "Imagine+pack_kage.py",
                "author": "SMSForge",
                "role": name + suf,
                "sha256": digest,
            })
        assets.append({
            "file": "res/proof/" + name + "_full.png",
            "origin": origin,
            "tool": "Imagine+pack_kage.py",
            "author": "SMSForge",
            "role": name + " entity_geometry_16x32_proof",
            "sha256": digest,
        })
    origin = os.path.relpath(stage_origin, PROJ).replace("\\", "/")
    assets.append({
        "file": "res/bg/stage.png",
        "origin": origin,
        "tool": "Imagine+pack_kage.py",
        "author": "SMSForge",
        "role": "palco",
        "sha256": sha256(stage_origin),
    })
    man = os.path.join(PROJ, "doc", "asset_provenance_manifest.json")
    with open(man, "w") as f:
        json.dump({"assets": assets}, f, indent=2)
        f.write("\n")


def write_audio_provenance(sfx, music):
    man = os.path.join(PROJ, "doc", "audio_provenance_manifest.json")
    sfx_sha = hashlib.sha256(sfx).hexdigest()
    mus_sha = hashlib.sha256(music).hexdigest()
    doc = {
        "assets": [
            {
                "file": "res/audio/sfx_slash.psg",
                "origin": "stream autoral sintetizado para PSGlib",
                "author": "SMSForge",
                "tool": "pack_kage.py",
                "role": "corte da katana",
                "channels": "SFX_CHANNEL3",
                "frames": 7,
                "format": "PSGlib stream",
                "bytes": len(sfx),
                "sha256": sfx_sha,
            },
            {
                "file": "res/audio/music_kage.psg",
                "origin": "ostinato pentatonico matsuri",
                "author": "SMSForge",
                "tool": "pack_kage.py",
                "role": "musica de fundo ch0+ch1",
                "channels": "music_ch0_ch1",
                "frames": 32,
                "format": "PSGlib stream",
                "bytes": len(music),
                "sha256": mus_sha,
            },
        ]
    }
    with open(man, "w") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")


def main():
    os.makedirs(INC, exist_ok=True)
    os.makedirs(os.path.join(RES, "sprites"), exist_ok=True)
    os.makedirs(os.path.join(RES, "bg"), exist_ok=True)
    os.makedirs(PROOF, exist_ok=True)
    os.makedirs(PALETTES, exist_ok=True)
    poses = [
        ("kage_idle", os.path.join(RASC, "kage_side_idle.jpg")),
        ("kage_walk0", os.path.join(RASC, "kage_walk0.png")),
        ("kage_walk1", os.path.join(RASC, "kage_walk1.png")),
        ("kage_slash", os.path.join(RASC, "kage_slash.png")),
        ("samurai_idle", os.path.join(RASC, "samurai_side_idle.jpg")),
        ("samurai_walk", os.path.join(RASC, "samurai_side_walk.jpg")),
        ("kage_slash2", os.path.join(RASC, "kage_slash2.png")),
        ("kage_jump", os.path.join(RASC, "kage_jump.jpg")),
    ]
    rgb_poses = [(name, sprite_rgb16x32(path)) for name, path in poses]
    all_rows = []
    for _, rows in rgb_poses:
        all_rows.extend(rows)
    spr_pal, _ = cap_palette_spr(all_rows, 16, 32 * len(rgb_poses))
    kage_blob = bytearray()
    for name, rows in rgb_poses[:4]:
        tiles = pack_sprite_with_pal(rows, name, spr_pal)
        kage_blob += tiles
    kage_left = bytearray()
    for i in range(4):
        chunk = bytes(kage_blob[i * 256:(i + 1) * 256])
        kage_left += flip_tiles_tall(chunk)
    write_header(os.path.join(INC, "kage_right_tiles.h"), "kage_right_tiles",
                 bytes(kage_blob))
    write_header(os.path.join(INC, "kage_left_tiles.h"), "kage_left_tiles",
                 bytes(kage_left))
    sam_blob = bytearray()
    for name, rows in rgb_poses[4:6]:
        tiles = pack_sprite_with_pal(rows, name, spr_pal)
        sam_blob += tiles
    sam_left = bytearray()
    for i in range(2):
        chunk = bytes(sam_blob[i * 256:(i + 1) * 256])
        sam_left += flip_tiles_tall(chunk)
    write_header(os.path.join(INC, "samurai_tiles.h"), "samurai_tiles",
                 bytes(sam_blob))
    write_header(os.path.join(INC, "samurai_left_tiles.h"), "samurai_left_tiles",
                 bytes(sam_left))
    kage_ext_blob = bytearray()
    for name, rows in rgb_poses[6:]:
        tiles = pack_sprite_with_pal(rows, name, spr_pal)
        kage_ext_blob += tiles
    kage_ext_left = bytearray()
    for i in range(2):
        chunk = bytes(kage_ext_blob[i * 256:(i + 1) * 256])
        kage_ext_left += flip_tiles_tall(chunk)
    write_header(os.path.join(INC, "kage_ext_right_tiles.h"), "kage_ext_right_tiles",
                 bytes(kage_ext_blob))
    write_header(os.path.join(INC, "kage_ext_left_tiles.h"), "kage_ext_left_tiles",
                 bytes(kage_ext_left))
    stage_origin = os.path.join(RASC, "stage_side_matsuri.jpg")
    bg_pal = pack_stage(stage_origin)
    sprite_pal_sms = pal_to_sms(spr_pal)
    bg_pal_sms = pal_to_sms(bg_pal)
    write_header(os.path.join(INC, "palette_sprite.h"), "palette_sprite",
                 sprite_pal_sms)
    write_header(os.path.join(INC, "palette_bg.h"), "palette_bg",
                 bg_pal_sms)
    open(os.path.join(PALETTES, "palette_sprite.sms"), "wb").write(sprite_pal_sms)
    open(os.path.join(PALETTES, "palette_bg.sms"), "wb").write(bg_pal_sms)
    music = make_music()
    sfx = make_sfx_slash()
    write_header(os.path.join(INC, "music_kage.h"), "music_kage", music)
    write_header(os.path.join(INC, "sfx_slash.h"), "sfx_slash", sfx)
    os.makedirs(os.path.join(RES, "audio"), exist_ok=True)
    open(os.path.join(RES, "audio", "sfx_slash.psg"), "wb").write(sfx)
    open(os.path.join(RES, "audio", "music_kage.psg"), "wb").write(music)
    write_provenance(poses, stage_origin)
    write_audio_provenance(sfx, music)
    print("[OK] pack_kage concluido")
    return 0


if __name__ == "__main__":
    sys.exit(main())
