#!/usr/bin/env python3
"""B.2b: renderiza offline uma pose do versus_scene_runtime.h como o BG a ve.

Decodifica os patterns SMS 4bpp planares (4 planos x 8 bytes) e monta as
celulas TALL (8x16) na grade do meta (dx, dy, tile): pattern `tile` em
(dx,dy) e `tile+1` em (dx,dy+8). Paleta = versus_sprite_palette (BG P0:
entrada 0 preta, 1..15 iguais). Saida PNG com escala nearest.

Uso: render_pose.py <pose_base> <out.png> [--palette p1|p2]
  pose_base: ex. P1_RYU_A20F3 ou P2_KEN8_A20F3 (alias resolvido no header)
"""
import re
import sys

from PIL import Image

H = ("/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2/"
     "out/generated/ryu_ken_cross/versus_scene_runtime.h")
TEXT = open(H).read()

PALETTE = [0x00, 0x1A, 0x1B, 0x16, 0x2A, 0x05, 0x2B, 0x02,
           0x00, 0x02, 0x07, 0x2B, 0x0B, 0x1B, 0x2F, 0x16]


def rgb(c):
    return ((c & 3) * 85, ((c >> 2) & 3) * 85, ((c >> 4) & 3) * 85)


def array(name):
    m = re.search(r"const unsigned char " + re.escape(name) +
                  r"\[(\d+)\] = \{(.*?)\};", TEXT, re.S)
    if not m:
        return None
    return [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{2})", m.group(2))]


def resolve(name):
    for _ in range(4):
        if array(name) is not None:
            return name
        m = re.search(r"#define " + re.escape(name) + r"\s+(\w+)", TEXT)
        if not m:
            return None
        name = m.group(1)
    return None


def define_int(name):
    m = re.search(r"#define " + re.escape(name) + r"\s+(\d+)", TEXT)
    return int(m.group(1)) if m else None


def load_tiles(pose):
    bank = define_int(pose + "_TILES_BANK")
    off = define_int(pose + "_TILES_OFF")
    size = define_int(pose + "_TILES_SIZE")
    base = ("/mnt/sdcard/Projects/SMSForge/SMS_projects/luta_mugem_rev2/"
            "out/generated/ryu_ken_cross/")
    prefix = "ken_scene_bank" if 2 <= bank <= 26 else "ryu_scene_bank"
    path = base + f"{prefix}{bank}.bin"
    raw = open(path, "rb").read()
    return list(raw[off:off + size]), path


def decode_pattern(tiles, base):
    # formato dos banks gerados: por linha, 4 bytes de plano (row-interleaved)
    px = [[0] * 8 for _ in range(8)]
    for y in range(8):
        b0 = tiles[base + y * 4 + 0]
        b1 = tiles[base + y * 4 + 1]
        b2 = tiles[base + y * 4 + 2]
        b3 = tiles[base + y * 4 + 3]
        for x in range(8):
            bit = 7 - x
            px[y][x] = (((b0 >> bit) & 1) | (((b1 >> bit) & 1) << 1) |
                        (((b2 >> bit) & 1) << 2) | (((b3 >> bit) & 1) << 3))
    return px


def main():
    pose = sys.argv[1]
    out = sys.argv[2]
    meta_name = resolve(pose + "_META")
    meta = array(meta_name)
    if meta is None:
        print("nao achei", meta_name)
        return 2
    tiles, tiles_path = load_tiles(pose)
    print("tiles:", tiles_path)
    cells = []
    i = 0
    while i + 2 < len(meta) and not (meta[i] & 0x80):
        cells.append((meta[i], meta[i + 1], meta[i + 2]))
        i += 3
    w = max(c[0] for c in cells) + 8
    h = max(c[1] for c in cells) + 16
    im = Image.new("RGB", (w, h), (0, 0, 0))
    p = im.load()
    for dx, dy, tile in cells:
        for half in (0, 1):
            pat = decode_pattern(tiles, (tile + half) * 32)
            for y in range(8):
                for x in range(8):
                    p[dx + x, dy + half * 8 + y] = rgb(PALETTE[pat[y][x]])
    im.resize((w * 4, h * 4), Image.NEAREST).save(out)
    print(f"{pose}: {len(cells)} celulas, {w}x{h}, tiles {len(tiles)//32} patterns -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
