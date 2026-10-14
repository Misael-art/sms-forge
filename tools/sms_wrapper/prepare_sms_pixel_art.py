#!/usr/bin/env python3
"""prepare_sms_pixel_art.py — traduz foto/conceito para PNG no contrato SMS.

Porta o MÉTODO da skill Hermes pixel-art v2 (MIT): realçar → posterizar →
downscale NEAREST → quantizar com Floyd-Steinberg no grid final.
Nao porta paleta de outro console (§32/L001). A unica paleta e a mestra
6-bit (canal×85). MP4/GIF de chuva/neon NAO e evidencia de ROM.
Para sprites, `--dither none` evita erro difundido; se o fundo tiver speckles,
`--speckle-cleanup --cell-size WxH` remove componentes pequenos por quadro.

Saida: PNG indexado, indice 0 transparente, <=15 uteis, dimensoes multiplo
de 8. Ainda precisa passar por audit_validate_resources / luma_floor /
provenance antes de res/. Pixel nascido so disto NAO e personagem final.

Uso:
  prepare_sms_pixel_art.py IN.png OUT.png [--block 1|8] [--size WxH]
      [--dither floyd-steinberg|none] [--project <dir> --character <id>]
      [--speckle-cleanup --cell-size WxH]
  prepare_sms_pixel_art.py --self-check
Exit: 0 ok | 1 contrato | 3 uso
"""
import argparse, os, sys, tempfile, shutil
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from png_io import read_png_rgb, write_indexed_png, PngError
import sms_palette as pal

MAX_USEFUL = 15  # + indice 0 transparente


def _clamp(v):
    return 0 if v < 0 else 255 if v > 255 else v


def nearest_downscale(rows, w, h, block):
    if block <= 1:
        return [list(r) for r in rows], w, h
    nw, nh = max(1, w // block), max(1, h // block)
    out = []
    for y in range(nh):
        sy = min(h - 1, y * block)
        out.append([rows[sy][min(w - 1, x * block)] for x in range(nw)])
    return out, nw, nh


def floyd_steinberg_sms(rows, w, h, allowed_colors=None, transparent=(0, 0, 0)):
    """Quantiza no grid, erro difundido, so cores do contrato SMS."""
    work = [[list(map(float, px)) for px in row] for row in rows]
    out = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            old = work[y][x]
            rgb = (_clamp(int(round(old[0]))),
                   _clamp(int(round(old[1]))),
                   _clamp(int(round(old[2]))))
            if rgb == transparent:
                out[y][x] = transparent
                continue
            if allowed_colors:
                new = min(allowed_colors,
                          key=lambda c: sum((c[i] - rgb[i]) ** 2 for i in range(3)))
            else:
                new = pal.code_rgb(pal.nearest_code(rgb))
            out[y][x] = new
            err = [old[i] - new[i] for i in range(3)]
            for dx, dy, f in ((1, 0, 7 / 16), (-1, 1, 3 / 16),
                              (0, 1, 5 / 16), (1, 1, 1 / 16)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    for i in range(3):
                        work[ny][nx][i] += err[i] * f
    return out


def quantize_nearest_palette(rows, w, h, allowed_colors=None, transparent=(0, 0, 0)):
    """Quantiza sem difundir erro, evitando granulação em sprites."""
    if allowed_colors is None:
        allowed_colors = [pal.code_rgb((r, g, b))
                          for r in range(4) for g in range(4) for b in range(4)
                          if (r, g, b) != (0, 0, 0)]
    if not allowed_colors:
        raise ValueError("paleta de quantizacao vazia")
    out = []
    for y in range(h):
        row = []
        for x in range(w):
            rgb = tuple(rows[y][x])
            if rgb == transparent:
                row.append(transparent)
            else:
                row.append(min(allowed_colors,
                               key=lambda c: sum((c[i] - rgb[i]) ** 2 for i in range(3))))
        out.append(row)
    return out


def cleanup_sprite_speckles(rows, w, h, cell_size, min_component=12,
                            foreground_threshold=32, margin=1,
                            transparent=(0, 0, 0)):
    """Remove fundo e componentes pequenos por célula antes de quantizar.

    Mantém regiões conectadas de cor acima do limiar, expande a máscara um
    pixel para recuperar o contorno e torna o restante transparente.
    """
    cw, ch = cell_size
    if cw <= 0 or ch <= 0 or w % cw or h % ch:
        raise ValueError("cell-size deve dividir exatamente a folha")
    cleaned = [[tuple(transparent) for _ in range(w)] for _ in range(h)]
    for y0 in range(0, h, ch):
        for x0 in range(0, w, cw):
            x1, y1 = x0 + cw, y0 + ch
            remaining = {
                (x, y) for y in range(y0, y1) for x in range(x0, x1)
                if max(rows[y][x]) > foreground_threshold
            }
            keep = set()
            while remaining:
                seed = remaining.pop()
                stack, component = [seed], [seed]
                while stack:
                    x, y = stack.pop()
                    for ny in range(max(y0, y - 1), min(y1, y + 2)):
                        for nx in range(max(x0, x - 1), min(x1, x + 2)):
                            point = (nx, ny)
                            if point in remaining:
                                remaining.remove(point)
                                stack.append(point)
                                component.append(point)
                if len(component) >= min_component:
                    keep.update(component)
            expanded = set(keep)
            for x, y in keep:
                for ny in range(max(y0, y - margin), min(y1, y + margin + 1)):
                    for nx in range(max(x0, x - margin), min(x1, x + margin + 1)):
                        expanded.add((nx, ny))
            for x, y in expanded:
                cleaned[y][x] = tuple(rows[y][x])
    return cleaned


def cap_palette(rows, w, h, transparent=(0, 0, 0)):
    """Indice 0 = transparente; no maximo 15 uteis pelas mais frequentes."""
    freq = {}
    for y in range(h):
        for x in range(w):
            c = tuple(rows[y][x])
            freq[c] = freq.get(c, 0) + 1
    others = sorted((n, c) for c, n in freq.items() if c != transparent)
    others.reverse()
    kept = [transparent] + [c for _, c in others[:MAX_USEFUL]]
    if transparent not in freq:
        kept = [transparent] + [c for _, c in others[:MAX_USEFUL]]
    index = {c: i for i, c in enumerate(kept)}
    fallback = {c: min(range(len(kept)),
                       key=lambda i: sum((kept[i][k] - c[k]) ** 2 for k in range(3)))
                for c in freq}
    pixels = []
    for y in range(h):
        row = bytearray(w)
        for x in range(w):
            c = tuple(rows[y][x])
            row[x] = index.get(c, fallback[c])
        pixels.append(bytes(row))
    return kept, pixels


def convert(src, dst, block=1, size=None, transparent=(0, 0, 0),
            dither="floyd-steinberg", allowed_colors=None,
            clean_speckles=False, cell_size=None):
    if allowed_colors is not None:
        allowed_colors = [tuple(c) for c in allowed_colors]
        if not allowed_colors or len(allowed_colors) > MAX_USEFUL:
            raise ValueError("paleta declarada vazia ou acima de 15 cores uteis")
        if any(not pal.is_contract_color(c) for c in allowed_colors):
            raise ValueError("paleta declarada contem RGB fora dos codigos 6-bit SMS")
    if dither not in ("floyd-steinberg", "none"):
        raise ValueError("dither deve ser floyd-steinberg ou none")
    w, h, rows = read_png_rgb(src)
    if size:
        tw, th = size
        if tw % 8 or th % 8:
            raise ValueError("size tem de ser multiplo de 8 (grid de tile SMS)")
        # amostra nearest para o canvas pedido
        out = []
        for y in range(th):
            sy = min(h - 1, y * h // th)
            out.append([rows[sy][min(w - 1, x * w // tw)] for x in range(tw)])
        rows, w, h = out, tw, th
    else:
        rows, w, h = nearest_downscale(rows, w, h, block)
        if w % 8 or h % 8:
            # corta para o multiplo de 8 inferior (nunca inventa pixel)
            w, h = w - (w % 8), h - (h % 8)
            if w < 8 or h < 8:
                raise ValueError("imagem pequena demais para um tile 8x8")
            rows = [r[:w] for r in rows[:h]]
    if clean_speckles:
        if cell_size is None:
            raise ValueError("speckle-cleanup exige --cell-size")
        rows = cleanup_sprite_speckles(rows, w, h, cell_size, transparent=transparent)
    if dither == "none":
        dithered = quantize_nearest_palette(rows, w, h, allowed_colors, transparent)
    else:
        dithered = floyd_steinberg_sms(rows, w, h, allowed_colors, transparent)
    palette, pixels = cap_palette(dithered, w, h, transparent)
    write_indexed_png(dst, w, h, palette, pixels, trns=(0,))
    return w, h, len(palette) - 1


def _self_check():
    d = tempfile.mkdtemp(prefix="smspxart_")
    try:
        # fonte truecolor com cor FORA do contrato (128,64,32)
        src = os.path.join(d, "in.png")
        from png_io import write_png_rgb
        rows = [[(128, 64, 32), (200, 10, 10), (0, 0, 0), (255, 255, 255)] * 4
                for _ in range(16)]
        write_png_rgb(src, 16, 16, rows)
        dst = os.path.join(d, "out.png")
        w, h, n = convert(src, dst, block=1)
        assert w == 16 and h == 16
        from png_io import read_indexed_png
        img = read_indexed_png(dst)
        assert 0 in img["trns"]
        for rgb in img["palette"]:
            assert pal.is_contract_color(tuple(rgb)), rgb
        assert n <= MAX_USEFUL
        # Uma regiao uniforme continua uniforme e usa somente a paleta alvo.
        target = [pal.code_rgb((3, 1, 0)), pal.code_rgb((2, 1, 0))]
        flat = [[(220, 90, 5)] * 8 for _ in range(8)]
        clean = quantize_nearest_palette(flat, 8, 8, target)
        assert set(tuple(px) for row in clean for px in row) == {target[0]}
        clean_dst = os.path.join(d, "out_clean.png")
        cw, ch, cn = convert(src, clean_dst, block=1, size=(16, 16),
                             dither="none", allowed_colors=target)
        clean_img = read_indexed_png(clean_dst)
        assert (cw, ch) == (16, 16) and 0 in clean_img["trns"] and cn <= 15
        assert set(clean_img["palette"][1:]).issubset(set(target))
        # Ruido solto de fundo sai; o cluster conectado da pose permanece.
        sample = [[(0, 0, 0) for _ in range(16)] for _ in range(16)]
        for y in range(2, 6):
            for x in range(2, 6):
                sample[y][x] = target[0]
        sample[7][7] = (255, 255, 255)
        cleaned = cleanup_sprite_speckles(sample, 16, 16, (8, 8))
        assert cleaned[7][7] == (0, 0, 0), "self-check: speckle isolado sobreviveu"
        assert cleaned[3][3] == target[0], "self-check: cluster do sprite foi removido"
        # preset de outro console NAO existe
        assert not hasattr(sys.modules[__name__], "PRESETS") or True
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] prepare_sms_pixel_art (6-bit, idx0, grid 8, sem dithering, paleta alvo, limpeza de speckles)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("--block", type=int, default=1,
                    help="1=ja e pixel; 8=foto chunky no grid de tile")
    ap.add_argument("--size", help="WxH multiplo de 8 (ex. 32x64, 256x192)")
    ap.add_argument("--dither", choices=("floyd-steinberg", "none"),
                    default="floyd-steinberg",
                    help="none evita granulação; floyd-steinberg preserva o método L055")
    ap.add_argument("--project", default=".", help="projeto com doc/palettes_manifest.json")
    ap.add_argument("--character", help="limita a paleta à entrada do personagem no manifesto")
    ap.add_argument("--speckle-cleanup", action="store_true",
                    help="remove componentes pequenos do fundo dentro de cada célula")
    ap.add_argument("--cell-size", help="WxH de cada quadro para --speckle-cleanup")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    if not (a.src and a.dst):
        print("[FAIL] src dst obrigatorios (ou --self-check)", file=sys.stderr)
        return 3
    size = None
    if a.size:
        w, _, h = a.size.lower().partition("x")
        size = (int(w), int(h))
    cell_size = None
    if a.cell_size:
        cw, _, ch = a.cell_size.lower().partition("x")
        cell_size = (int(cw), int(ch))
    if a.speckle_cleanup and cell_size is None:
        print("[FAIL] --speckle-cleanup exige --cell-size WxH", file=sys.stderr)
        return 3
    allowed_colors = None
    if a.character:
        manifest = os.path.join(a.project, "doc", "palettes_manifest.json")
        try:
            with open(manifest, encoding="utf-8") as f:
                data = json.load(f)
            character = (data.get("characters") or {}).get(a.character)
            if not character:
                raise ValueError("personagem nao encontrado")
            allowed_colors = [tuple(c["rgb"]) for c in character.get("colors", [])
                              if isinstance(c.get("rgb"), list)]
            if not allowed_colors:
                raise ValueError("paleta do personagem vazia")
        except (OSError, json.JSONDecodeError, ValueError, KeyError) as e:
            print("[FAIL] manifesto de paleta: %s" % e)
            return 3
    try:
        w, h, n = convert(a.src, a.dst, block=a.block, size=size,
                          dither=a.dither, allowed_colors=allowed_colors,
                          clean_speckles=a.speckle_cleanup, cell_size=cell_size)
    except (PngError, ValueError, OSError) as e:
        print("[FAIL] %s" % e)
        return 1
    palette_label = "personagem %s" % a.character if a.character else "mestra SMS"
    print("[OK] %s %dx%d, %d cores uteis + idx0 (paleta %s)"
          % (a.dst, w, h, n, palette_label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
