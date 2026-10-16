#!/usr/bin/env python3
"""openbor2sms.sms_art — conversao de arte OpenBOR para o contrato de pixels SMS.

Fronteira (O2, doc/artifacts/o2_vdp_pilot_scope_20261015.json):
- palco: panel.gif -> faixa visivel do corredor (x 0..632, y 48..224 no quadro
  fonte = view crop 32..224 menos as 2 linhas de HUD), paleta P0 de codigos
  mestres 6-bit e dicionario de tiles por k-medoides (K alvo, default 192).
- poses: GIFs 1:1 -> canvases 8x8-alinhados ancorados no offset (240,204),
  indice 0 = transparente, paleta P1; espelho explicito porque o VDP do SMS
  nao tem flip de sprite (precedente kage: tiles espelhados sao padroes).
- este modulo NUNCA importa semantics.py nem reautora pixels: reposiciona,
  quantiza e espelha a arte extraida da fonte, com proveniencia rastreavel.

Saidas (relativas ao projeto):
  res/o2/stage/stage_corridor.png      palco quantizado (632x176)
  res/o2/poses/*.png                   poses (esquerda/direita) 8x8-alinhadas
  res/o2/hud/hud_tiles.png             tiles de HUD do piloto (32x8)
  rascunho/o2/*.png                    previews para revisao humana
  data/generated/art/<record>.json     registro de conversao

Uso:
  python3 -m openbor2sms.sms_art --project DIR [--generated-at ISO] [--bg-k N]
  python3 -m openbor2sms.sms_art --self-check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _find_wrapper(start: Path) -> Path:
    p = start
    while p != p.parent:
        if (p / "png_io.py").exists():
            return p
        p = p.parent
    raise SystemExit("png_io.py nao encontrado acima de " + str(start))


WRAP = _find_wrapper(HERE)
sys.path.insert(0, str(WRAP))

from png_io import write_indexed_png, write_png_rgb  # noqa: E402
import sms_palette as pal  # noqa: E402

MASTER_CODE = [(r, g, b) for r in range(4) for g in range(4) for b in range(4)]
MASTER_RGB = [pal.code_rgb(c) for c in MASTER_CODE]

# chave cromatica dos GIFs OpenBOR extraidos (ciano puro); confirmada por
# amostragem dos quatro cantos no inicio da conversao (falha LOUD se mudar).
KEY_CYAN = (0, 253, 255)
# cor do indice 0 (transparente) nos PNGs de sprite: magenta e codigo valido.
KEY_RGB = (255, 0, 255)

FORCED_BG_CODES = [(0, 0, 0), (0, 2, 0), (2, 0, 0)]  # preto, verde, vermelho (HUD)

# Bayer 4x4 para dither ordenado deterministico (so palco; sprites ficam duros)
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

SOURCE_ROOT = "data/source_openbor/gal_town1/data"
STAGE = {
    "gif": f"{SOURCE_ROOT}/bgs/town1/panel.gif",
    "crop": (0, 632, 48, 224),  # x0, x1, y0, y1 no quadro fonte
    "png": "res/o2/stage/stage_corridor.png",
}
POSES = {
    "ax": {
        "frames": ["idle01", "walk01", "walk03"],
        "mirror": True,
        "anchor": (240, 204),
        "gif_dir": f"{SOURCE_ROOT}/chars/ax",
    },
    "long": {
        "frames": ["idle01"],
        "mirror": False,
        "anchor": (240, 204),
        "gif_dir": f"{SOURCE_ROOT}/chars/long",
    },
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gif_rgb(path: Path, detect_key: bool = True):
    """GIF -> (w, h, rows de tuplas RGB, cor-chave).

    detect_key=True (sprites): os quatro cantos precisam ser uniformes e iguais
    a chave ciano declarada. detect_key=False (painel de palco): imagem opaca,
    sem chave; retorna key=None.
    """
    from PIL import Image
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    if not detect_key:
        rows = [list(px[x, y] for x in range(w)) for y in range(h)]
        return w, h, rows, None
    corners = {px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]}
    if len(corners) != 1:
        raise SystemExit(f"{path}: cantos nao sao uniformes: {sorted(corners)}")
    key = corners.pop()
    if key != KEY_CYAN:
        raise SystemExit(f"{path}: cor-chave {key} != esperada {KEY_CYAN}")
    rows = [list(px[x, y] for x in range(w)) for y in range(h)]
    return w, h, rows, key


# ---------------------------------------------------------------- paleta -----

def quantize_palette(source_hist, k, reserved=()):
    """Escolhe <=k codigos mestres por k-medoides ponderado sobre as cores-fonte.

    Medoides = codigos mestres 6-bit; atribuicao e atualizacao usam as cores
    originais (agregar por codigo antes distorce o otimo). `reserved`: codigos
    acrescentados ao fim, FORA do clustering — o mapeamento de cena jamais os
    usa (ex.: cores do HUD). Deterministico.

    Retorna (codes, info) com codes = lista de (r,g,b) canais 0..3.
    """
    items = sorted(source_hist.items(), key=lambda kv: (-kv[1], kv[0]))
    total_n = sum(w for _c, w in items)
    limit = max(0, k - len(reserved))
    # init deterministico: os `limit` codigos mestres de maior peso agregado
    weights = [0] * 64
    for rgb, w in items:
        j = min(range(64), key=lambda i: (_d2(MASTER_RGB[i], rgb), i))
        weights[j] += w
    codes = [i for i in sorted(range(64), key=lambda i: (-weights[i], MASTER_CODE[i]))
             if weights[i] > 0][:limit]
    for _ in range(10):
        assign = [[] for _ in codes]
        for rgb, w in items:
            j = min(range(len(codes)),
                    key=lambda m: (_d2(rgb, MASTER_RGB[codes[m]]), codes[m]))
            assign[j].append((rgb, w))
        mass = [sum(w for _r, w in mem) for mem in assign]
        order = sorted(range(len(codes)), key=lambda m: (-mass[m], m))
        used = set()
        best_for = {}
        for m in order:
            if not assign[m]:
                continue
            cands = [c for c in range(64) if c not in used]
            best_for[m] = min(cands, key=lambda c: (
                sum(w * _d2(rgb, MASTER_RGB[c]) for rgb, w in assign[m]), c))
            used.add(best_for[m])
        new_codes = [best_for[m] for m in range(len(codes)) if m in best_for]
        if new_codes == codes:
            break
        codes = new_codes
    seen, scene = set(), []
    for j in codes:
        if j not in seen:
            seen.add(j)
            scene.append(j)
    codes = scene
    final = list(codes)
    for r in reserved:
        j = MASTER_CODE.index(tuple(r))
        if j not in final:
            final.append(j)

    err_abs = 0.0
    err_d2 = 0.0
    mapping = {}
    for rgb, w in items:
        if not codes:
            break
        j = min(codes, key=lambda j: (_d2(rgb, MASTER_RGB[j]), j))
        err_abs += w * _d1_abs(rgb, MASTER_RGB[j])
        err_d2 += w * _d2(rgb, MASTER_RGB[j])
        mapping[rgb] = MASTER_CODE[j]
    stats = {
        "usable_colors": len(final),
        "scene_colors": len(codes),
        "reserved_colors": len(final) - len(codes),
        "source_colors": len(source_hist),
        "err_mean_abs_channel": round(err_abs / (3 * total_n), 2) if total_n else 0.0,
        "err_rms_channel": round((err_d2 / (3 * total_n)) ** 0.5, 2) if total_n else 0.0,
    }
    out = [MASTER_CODE[j] for j in final]
    info = {"codes": out, "stats": stats,
            "mapping_note": {str(kk): list(vv) for kk, vv in sorted(mapping.items())}}
    return out, info


def _d2(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3))


def _d1_abs(a, b):
    return sum(abs(a[i] - b[i]) for i in range(3))


def nearest_index(rgb, pal_rgb, cache):
    idx = cache.get(rgb)
    if idx is None:
        idx = min(range(len(pal_rgb)), key=lambda i: (_d2(pal_rgb[i], rgb), i))
        cache[rgb] = idx
    return idx


# ----------------------------------------------------------- dicionario ------

def build_dictionary(cells, pal_rgb, k):
    """K-medoides ponderado sobre tiles de 8x8 (cells: bytes(64) -> peso).

    Distancia = soma dos deltas quadraticos POR POSICAO (mesmo pixel), como o
    merge por distancia RGB do precedente kage. Deterministico; reporta rms e
    media absoluta por canal.
    """
    keys = sorted(cells.keys(), key=lambda t: (-cells[t], t))
    counts = [cells[t] for t in keys]
    n = len(keys)
    medoids = list(range(min(n, k)))
    L = len(pal_rgb)
    d2flat = [_d2(pal_rgb[i], pal_rgb[j]) for i in range(L) for j in range(L)]
    aflat = [_d1_abs(pal_rgb[i], pal_rgb[j]) for i in range(L) for j in range(L)]

    def dist(i, j, table):
        t1, t2 = keys[i], keys[j]
        return sum(table[a * L + b] for a, b in zip(t1, t2))

    for _ in range(5):
        assign = [[] for _ in medoids]
        for i in range(n):
            best = min(range(len(medoids)),
                       key=lambda m: (dist(i, medoids[m], d2flat), medoids[m]))
            assign[best].append(i)
        new_medoids = []
        moved = False
        for m, members in zip(medoids, assign):
            if not members:
                new_medoids.append(m)
                continue
            best = min(members, key=lambda cand: (
                sum(counts[x] * dist(x, cand, d2flat) for x in members), cand))
            new_medoids.append(best)
            if best != m:
                moved = True
        medoids = new_medoids
        if not moved:
            break
    assignment = [min(range(len(medoids)),
                      key=lambda m: (dist(i, medoids[m], d2flat), medoids[m]))
                  for i in range(n)]
    total_d2 = 0
    total_abs = 0
    total_px = 0
    for i in range(n):
        j = assignment[i]
        total_d2 += counts[i] * dist(i, medoids[j], d2flat)
        total_abs += counts[i] * dist(i, medoids[j], aflat)
        total_px += counts[i] * 64
    stats = {
        "distinct_cells": n,
        "k": len(medoids),
        "requested_k": k,
        "err_rms_channel": round((total_d2 / (3 * total_px)) ** 0.5, 2),
        "err_mean_abs_channel": round(total_abs / (3 * total_px), 2),
    }
    medoid_tiles = [keys[m] for m in medoids]
    cell_to_medoid = {keys[i]: keys[medoids[assignment[i]]] for i in range(n)}
    return medoid_tiles, cell_to_medoid, stats


# ---------------------------------------------------------------- grade ------

def rgb_to_index_grid(rows, pal_rgb, key=None, dither=False):
    """RGB -> indices da paleta. dither=True usa Bayer 4x4 entre os 2 codigos
    mais proximos (deterministico) — atenua o serrilhado do grid 4x4x4."""
    cache = {}
    out = []
    for y, row in enumerate(rows):
        grows = bytearray(len(row))
        for x, px in enumerate(row):
            if key is not None and px == key:
                grows[x] = 0
                continue
            entry = cache.get(px)
            if entry is None:
                order = sorted(range(len(pal_rgb)),
                               key=lambda i: (_d2(pal_rgb[i], px), i))
                entry = (order[0], order[1] if len(order) > 1 else order[0])
                cache[px] = entry
            c1, c2 = entry
            pick = c1
            if dither and c2 != c1:
                d1 = _d2(pal_rgb[c1], px)
                d2v = _d2(pal_rgb[c2], px)
                if d1 > 0 and d2v > 0:
                    t = (BAYER4[y & 3][x & 3] + 0.5) / 16.0
                    if d1 / (d1 + d2v) > t:
                        pick = c2
            grows[x] = pick
        out.append(bytes(grows))
    return out


def extract_cells(grid, x0, y0, cols, rows_):
    """Cells 8x8 em ordem coluna->linha (bytes de 64 pixels)."""
    cells = []
    for cy in range(rows_):
        for cx in range(cols):
            tile = bytearray(64)
            p = 0
            for yy in range(8):
                row = grid[y0 + cy * 8 + yy]
                for xx in range(8):
                    tile[p] = row[x0 + cx * 8 + xx]
                    p += 1
            cells.append(bytes(tile))
    return cells


def render_grid(cells, mapping, cols, rows_):
    out = [bytearray(cols * 8) for _ in range(rows_ * 8)]
    i = 0
    for cy in range(rows_):
        for cx in range(cols):
            tile = mapping[cells[i]]
            i += 1
            for yy in range(8):
                row = out[cy * 8 + yy]
                for xx in range(8):
                    row[cx * 8 + xx] = tile[yy * 8 + xx]
    return [bytes(r) for r in out]


def grid_to_rgb_rows(grid, pal_rgb, key_rgb=None):
    out = []
    for row in grid:
        out.append([key_rgb if (key_rgb is not None and v == 0) else pal_rgb[v]
                    for v in row])
    return out


def hcat_rows(a_rows, b_rows, gap, fill=(0, 0, 0)):
    h = max(len(a_rows), len(b_rows))
    w = len(a_rows[0]) + len(b_rows[0]) + gap
    out = []
    for y in range(h):
        ra = a_rows[y] if y < len(a_rows) else [fill] * len(a_rows[0])
        rb = b_rows[y] if y < len(b_rows) else [fill] * len(b_rows[0])
        out.append(list(ra) + [fill] * gap + list(rb))
    return out


def vcat_rows(a_rows, b_rows, gap, fill=(0, 0, 0)):
    w = max(len(a_rows[0]), len(b_rows[0]))
    out = []
    for row in a_rows:
        out.append(list(row) + [fill] * (w - len(row)))
    out.append([fill] * w)
    for row in b_rows:
        out.append(list(row) + [fill] * (w - len(row)))
    return out


def zoom_rows(rows, factor):
    out = []
    for row in rows:
        zrow = []
        for px in row:
            zrow.extend([px] * factor)
        out.extend([zrow] * factor)
    return out


# ---------------------------------------------------------------- poses ------

def actor_canvas(frames_data, anchor):
    """Extensoes uniao dos quadros -> canvas 8x8-alinhado (altura mult. de 16)."""
    ax, ay = anchor
    min_dx = min_dy = 10 ** 9
    max_dx = max_dy = -10 ** 9
    for _w, _h, rows, key in frames_data:
        for y, row in enumerate(rows):
            for x, px in enumerate(row):
                if px == key:
                    continue
                dx, dy = x - ax, y - ay
                min_dx, max_dx = min(min_dx, dx), max(max_dx, dx)
                min_dy, max_dy = min(min_dy, dy), max(max_dy, dy)
    x0 = 8 * (min_dx // 8)
    x1 = 8 * -(-(max_dx + 1) // 8)
    y0 = 8 * (min_dy // 8)
    h = 16 * -(-(max_dy + 1 - y0) // 16)
    return x0, y0, x1 - x0, h


def mirror_grid(grid):
    return [bytes(reversed(row)) for row in grid]


# ------------------------------------------------------------------ main -----

def convert(project: Path, generated_at: str, bg_k: int):
    extract_record = project / "data/generated/extract/gal_town1_art_extract_20261015.json"
    rec = json.loads(extract_record.read_text(encoding="utf-8"))
    rec_sha = sha256_file(extract_record)
    rec_members = {m["member"]: m for m in rec["members"]}

    sources = []

    def src_entry(rel):
        p = project / rel
        entry = {"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size}
        rel_member = "data/" + rel[len(SOURCE_ROOT) + 1:]
        m = rec_members.get(rel_member)
        if m is None:
            raise SystemExit(f"{rel}: membro ausente no registro de extracao")
        if m["sha256"] != entry["sha256"]:
            raise SystemExit(f"{rel}: sha difere do registro de extracao")
        sources.append(entry)
        return p

    # --- palco ---
    stage_path = src_entry(STAGE["gif"])
    sw, sh, srows, skey = load_gif_rgb(stage_path, detect_key=False)
    x0, x1, y0, y1 = STAGE["crop"]
    if not (0 <= x0 < x1 <= sw and 0 <= y0 < y1 <= sh):
        raise SystemExit("recorte do palco fora do quadro fonte")
    band = [row[x0:x1] for row in srows[y0:y1]]
    hist = {}
    for row in band:
        for px in row:
            hist[px] = hist.get(px, 0) + 1
    pal_bg, pal_bg_info = quantize_palette(hist, 15, reserved=FORCED_BG_CODES)
    pal_bg_rgb = [pal.code_rgb(c) for c in pal_bg]
    for c in FORCED_BG_CODES:
        if c not in pal_bg:
            raise SystemExit(f"codigo reservado {c} nao sobreviveu a quantizacao")
    scene_n = pal_bg_info["stats"]["scene_colors"]
    scene_rgb = pal_bg_rgb[:scene_n]
    band_idx = rgb_to_index_grid(band, scene_rgb, dither=True)
    cols = (x1 - x0) // 8
    rows_n = (y1 - y0) // 8
    cells = extract_cells(band_idx, 0, 0, cols, rows_n)
    cells_count = {}
    for t in cells:
        cells_count[t] = cells_count.get(t, 0) + 1
    medoids, cell_map, dict_stats = build_dictionary(cells_count, pal_bg_rgb, bg_k)
    stage_grid = render_grid(cells, cell_map, cols, rows_n)
    stage_png = project / STAGE["png"]
    stage_png.parent.mkdir(parents=True, exist_ok=True)
    write_indexed_png(str(stage_png), x1 - x0, y1 - y0, pal_bg_rgb, stage_grid, trns=(0,))

    # previews do palco (rascunho: revisao humana, nunca asset)
    preview_dir = project / "rascunho/o2"
    preview_dir.mkdir(parents=True, exist_ok=True)
    conv_rgb = grid_to_rgb_rows(stage_grid, pal_bg_rgb)
    prev = hcat_rows(band, conv_rgb, 12)
    write_png_rgb(str(preview_dir / "stage_preview.png"), len(prev[0]), len(prev), prev)
    zx, zy, zz = 320, 112, 2
    zs = zoom_rows([row[:zx] for row in band[:zy]], zz)
    zc = zoom_rows([row[:zx] for row in conv_rgb[:zy]], zz)
    zprev = vcat_rows(zs, zc, 12)
    write_png_rgb(str(preview_dir / "stage_zoom.png"), len(zprev[0]), len(zprev), zprev)

    # --- poses ---
    actors = {}
    pose_outputs = []
    for actor, cfg in POSES.items():
        frames_data = []
        frame_names = []
        for name in cfg["frames"]:
            rel = f'{cfg["gif_dir"]}/{name}.gif'
            p = src_entry(rel)
            w, h, rows, key = load_gif_rgb(p)
            frames_data.append((w, h, rows, key))
            frame_names.append(name)
        canvas = actor_canvas(frames_data, cfg["anchor"])
        actors[actor] = {"canvas": canvas, "frames": frame_names, "data": frames_data}
    # hist da uniao: contar pixels dentro dos canvases (o que a ROM mostra)
    union_hist = {}
    for actor, info in actors.items():
        x0a, y0a, cw, chh = info["canvas"]
        ax, ay = POSES[actor]["anchor"]
        for (w, h, rows, key) in info["data"]:
            for yy in range(chh):
                sy = ay + y0a + yy
                if not (0 <= sy < h):
                    continue
                for xx in range(cw):
                    sx = ax + x0a + xx
                    if 0 <= sx < w:
                        px = rows[sy][sx]
                        if px != key:
                            union_hist[px] = union_hist.get(px, 0) + 1
    pal_spr, pal_spr_info = quantize_palette(union_hist, 15)
    pal_spr_rgb = [pal.code_rgb(c) for c in pal_spr]
    png_palette = [KEY_RGB] + pal_spr_rgb

    previews = []
    for actor, info in actors.items():
        x0a, y0a, cw, chh = info["canvas"]
        ax, ay = POSES[actor]["anchor"]
        actor_rec = {"canvas": {"dx0": x0a, "dy0": y0a, "w": cw, "h": chh}, "poses": []}
        cache = {}
        for name, (w, h, rows, key) in zip(info["frames"], info["data"]):
            grid = []
            for yy in range(chh):
                sy = ay + y0a + yy
                row = bytearray(cw)
                for xx in range(cw):
                    sx = ax + x0a + xx
                    px = rows[sy][sx] if (0 <= sy < h and 0 <= sx < w) else key
                    row[xx] = 0 if px == key else 1 + nearest_index(px, pal_spr_rgb, cache)
                grid.append(bytes(row))
            variants = [("left", grid)]
            if POSES[actor]["mirror"]:
                variants.append(("right", mirror_grid(grid)))
            pose_entry = {"frame": name, "pngs": {}}
            for side, g in variants:
                out = project / f"res/o2/poses/{actor}_{name}_{side}.png"
                out.parent.mkdir(parents=True, exist_ok=True)
                write_indexed_png(str(out), cw, chh, png_palette, g, trns=(0,))
                pose_outputs.append(out)
                pose_entry["pngs"][side] = str(out.relative_to(project))
                pose_entry.setdefault("sha256", {})[side] = sha256_file(out)
            actor_rec["poses"].append(pose_entry)
        actors[actor]["record"] = actor_rec
        # preview
        sides = ["left"] + (["right"] if POSES[actor]["mirror"] else [])
        strip = None
        for name in info["frames"]:
            for side in sides:
                p = project / f"res/o2/poses/{actor}_{name}_{side}.png"
                from png_io import read_indexed_png
                got = read_indexed_png(str(p))
                rgb_rows = grid_to_rgb_rows(got["pixels"], png_palette, key_rgb=KEY_RGB)
                strip = rgb_rows if strip is None else hcat_rows(strip, rgb_rows, 6)
        if strip:
            previews.append((f"poses_{actor}", strip))

    # --- HUD do piloto (geometria declarada; cores pinadas em P0) ---
    hud_dir = project / "res/o2/hud"
    hud_dir.mkdir(parents=True, exist_ok=True)
    solid = {}
    for c, role in [((0, 2, 0), "green"), ((2, 0, 0), "red"), ((0, 0, 0), "black")]:
        rgb = pal.code_rgb(c)
        solid[role] = bytes([pal_bg_rgb.index(rgb)] * 64)
    hud_tiles = [solid["green"], solid["red"], solid["black"], solid["black"]]
    hud_rows = []
    for ty in range(8):
        row = bytearray()
        for t in hud_tiles:
            row += t[ty * 8:(ty + 1) * 8]
        hud_rows.append(bytes(row))
    hud_png = hud_dir / "hud_tiles.png"
    write_indexed_png(str(hud_png), 32, 8, pal_bg_rgb, hud_rows, trns=(0,))

    # --- previews de poses ---
    out_previews = []
    total_w = 0
    total_h = 0
    for name, rows in previews:
        p = preview_dir / f"{name}.png"
        write_png_rgb(str(p), len(rows[0]), len(rows), rows)
        out_previews.append(p)

    # --- registro ---
    today = generated_at[:10].replace("-", "")
    record_path = project / f"data/generated/art/o2_art_conversion_{today}.json"
    record_path.parent.mkdir(parents=True, exist_ok=True)
    outputs = []
    for p in [stage_png, hud_png] + pose_outputs + out_previews:
        outputs.append({"path": str(p.relative_to(project)),
                        "sha256": sha256_file(p), "bytes": p.stat().st_size})
    record = {
        "schema": "openbor_sms_art_conversion_v1",
        "generated_at": generated_at,
        "tool": "tools/sms_wrapper/openbor2sms/openbor2sms/sms_art.py",
        "project": str(project),
        "scope": "O2 — VDP pilot (palco por dicionario + poses 1:1 + HUD piloto)",
        "extract_record": {"path": str(extract_record.relative_to(project)),
                           "sha256": rec_sha},
        "sources": sources,
        "facing": {
            "native": "left",
            "basis": ("inspecao 1:1 dos GIFs extraidos: perfil/rosto a esquerda, "
                      "cabelo e arma atras a direita, em ax e long"),
            "mirror_role": ("orientacao 'right' = espelho horizontal explicito; o VDP "
                            "do SMS nao tem flip de sprite (precedente kage)"),
            "preview": "rascunho/o2/poses_ax.png",
        },
        "stage": {
            "source": STAGE["gif"],
            "crop": {"x0": x0, "x1": x1, "y0": y0, "y1": y1,
                     "note": "faixa visivel: view crop 32..224 menos 16 px de HUD"},
            "png": str(stage_png.relative_to(project)),
            "cols": cols, "rows": rows_n,
            "palette": "p0_bg",
            "mapping": ("dither ordenado Bayer 4x4 entre os 2 codigos de cena mais "
                        "proximos (deterministico; sprites NAO usam dither)"),
            "dictionary": dict_stats,
            "notes": ["HUD fixo cobre as linhas 0..1; PNT so recebe linhas 2..23",
                      "dicionario por k-medoides de tiles-fonte (medoides rastreaveis)",
                      "dither reduz o serrilhado do grid de cor 4x4x4 sem dither"],
        },
        "poses": {a: actors[a]["record"] for a in actors},
        "palettes": {
            "p0_bg": {"index0": "opaque (BG; preto)", **pal_bg_info,
                      "reserved_codes": [list(c) for c in FORCED_BG_CODES],
                      "reserved_note": ("verde/vermelho do HUD ficam fora do "
                                        "clustering e da atribuicao da cena")},
            "p1_sprites": {"index0": "transparente (magenta de contrato)", **pal_spr_info},
        },
        "hud": {
            "png": str(hud_png.relative_to(project)),
            "palette": "p0_bg",
            "role": "hud_piloto_nao_e_arte_final",
            "note": "tiles solidos (verde/vermelho/preto) + trilho preto",
        },
        "outputs": outputs,
        "notes": [
            "conversao 1:1: nenhum pixel desenhado; apenas recorte, quantizacao e espelho",
            "determinismo: mesmas fontes + --generated-at => bytes identicos",
        ],
    }
    record_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    return record_path, record


def self_check() -> int:
    ok = True
    # paleta: duas cores exatas -> erro zero
    codes, info = quantize_palette({(0, 0, 0): 10, (255, 255, 255): 5}, 4)
    ok &= info["stats"]["err_rms_channel"] == 0.0 and len(codes) >= 2
    # codigo reservado sobrevive no fim da paleta sem participar da cena
    codes, _ = quantize_palette({(0, 0, 0): 10}, 3, reserved=[(2, 0, 0)])
    ok &= (2, 0, 0) in codes and (0, 0, 0) in codes
    # dicionario: um tile so -> erro zero e identidade
    t = bytes([1] * 64)
    medoids, cmap, st = build_dictionary({t: 3}, [(0, 0, 0), (255, 0, 0)] + [(0, 0, 0)] * 14, 8)
    ok &= st["err_rms_channel"] == 0.0 and cmap[t] == medoids[0]
    # espelho duas vezes = original
    g = [bytes([0, 1, 2, 3]), bytes([4, 5, 6, 7])]
    ok &= mirror_grid(mirror_grid(g)) == g
    # dither determinista e restrito a paleta
    drows = [[(0, 0, 0), (255, 255, 255)] * 4]
    g1 = rgb_to_index_grid(drows, [(0, 0, 0), (255, 255, 255)], dither=True)
    g2 = rgb_to_index_grid(drows, [(0, 0, 0), (255, 255, 255)], dither=True)
    ok &= g1 == g2 and all(v in (0, 1) for v in g1[0])
    # celulas 8x8: extracao e render redondos
    grid = [bytes([i % 16] * 16) for i in range(8)]
    cells = extract_cells(grid, 0, 0, 2, 1)
    rendered = render_grid(cells, {cells[0]: cells[0], cells[1]: cells[1]}, 2, 1)
    ok &= rendered == grid
    if not ok:
        print("[SELF-CHECK FAIL] sms_art", file=sys.stderr)
        return 1
    print("[SELF-CHECK OK] sms_art")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OpenBOR -> pixels SMS (palco + poses)")
    ap.add_argument("--project", help="raiz do projeto SMSForge alvo")
    ap.add_argument("--generated-at", default=None)
    ap.add_argument("--bg-k", type=int, default=192)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.project:
        ap.error("--project e obrigatorio")
    project = Path(args.project).resolve()
    generated_at = args.generated_at or datetime.now(timezone.utc).replace(
        microsecond=0).isoformat()
    record_path, record = convert(project, generated_at, args.bg_k)
    st = record["stage"]["dictionary"]
    print(f"[sms_art] palco: {st['distinct_cells']} tiles distintos -> K={st['k']} "
          f"(rms/canal {st['err_rms_channel']})")
    for actor, arec in record["poses"].items():
        c = arec["canvas"]
        print(f"[sms_art] {actor}: canvas {c['w']}x{c['h']} @ ({c['dx0']},{c['dy0']}) "
              f"poses={[p['frame'] for p in arec['poses']]}")
    print(f"[sms_art] registro: {record_path.relative_to(project)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
