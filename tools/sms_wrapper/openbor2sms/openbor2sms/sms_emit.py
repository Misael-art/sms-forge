#!/usr/bin/env python3
"""openbor2sms.sms_emit — empacota a arte convertida (sms_art) em tabelas C,
plano de VRAM e manifests de cena para a ROM do piloto O2.

Consome:
- registro de conversao de arte (data/generated/art/o2_art_conversion_*.json)
  e os PNGs declarados nele (res/o2/...);
- IR de nivel (spawns/player_starts) e os .txt extraidos (delays por anim);
- registro de extracao (proveniencia).

Produz (relativo ao projeto):
  inc/o2/spr_tiles.h   blob de padroes de sprite (pares 8x16 deduplicados)
  inc/o2/spr_meta.h    metasprites por pose (ax esq/dir; long esq) + tipos
  inc/o2/pal_bg.h      paleta P0 (BG) em formato CRAM
  inc/o2/pal_spr.h     paleta P1 (sprites) em formato CRAM
  inc/o2/bg_tiles.h    dicionario de tiles do palco
  inc/o2/bg_cols.h     mapa de colunas (79 colunas x 22 linhas, indice local)
  inc/o2/hud_tiles.h   tiles de HUD (verde/vermelho/preto)
  inc/o2/level.h       constantes do piloto
  data/generated/plans/o2_vram_plan_*.json      plano sms_vram_plan_v1
  data/generated/emit/o2_sprite_scene_*.json    manifests sprite_scene_manifest_v1
  data/generated/emit/o2_emission_*.json        registro de emissao

Orcamento por linha (>=8 entradas SAT por scanline): o piloto desenha o
jogador inteiro e depois o inimigo em ordem (banda, densidade desc, coluna);
celulas que passariam de 8 entradas numa scanline sao puladas. O sim do pior
caso (px=484, z=180 parado; e pose walk) e gravado nos manifests e deve
passar no gate audit_sprite_line_sim.

Uso:
  python3 -m openbor2sms.sms_emit --project DIR [--generated-at ISO]
  python3 -m openbor2sms.sms_emit --self-check
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

from png_io import read_indexed_png  # noqa: E402

KEY_RGB = (255, 0, 255)

# poses emitidas (ordem = indices de pose no runtime)
AX_POSES = ["ax_idle01_left", "ax_idle01_right",
            "ax_walk01_left", "ax_walk01_right",
            "ax_walk03_left", "ax_walk03_right"]
ENEMY_POSES = ["long_idle01_left"]

# constantes do piloto (doc/artifacts/o2_vdp_pilot_scope_20261015.json)
PLAYER_START_X = 50
PLAYER_START_Z = 180
ENEMY_X = 500
ENEMY_Z = 180
PLAYER_MIN_X = 24
PLAYER_MAX_X = 484
Z_MIN = 160
Z_MAX = 232
CAM_DX = 120
CAM_MAX = 376
WALK_SPEED = 1
HP_PLAYER = 100
HP_ENEMY = 50
SCREEN_H = 192
PER_LINE_MAX = 8
SAT_MAX = 64
VRAM_TILES = 448

HUD_PLAYER_ROW = 0
HUD_ENEMY_ROW = 1
HUD_COL0 = 1
HUD_PLAYER_COLS = 20
HUD_ENEMY_COLS = 10


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def latest(project: Path, pattern: str) -> Path:
    hits = sorted(project.glob(pattern))
    if not hits:
        raise SystemExit(f"nenhum arquivo para {pattern}")
    return hits[-1]


def parse_anims(txt_path: Path):
    """Parse minimo dos .txt OpenBOR: anim -> delays/frames (por ordem)."""
    anims = {}
    cur = None
    for raw in txt_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("anim "):
            cur = line.split(None, 1)[1].strip()
            anims.setdefault(cur, {"delays": [], "frames": []})
        elif cur and line.startswith("delay"):
            parts = line.split()
            if len(parts) >= 2:
                anims[cur]["delays"].append(int(parts[1]))
        elif cur and line.startswith("frame"):
            anims[cur]["frames"].append(line.split()[-1])
    return anims


def ntsc_delay(delay10ms: int) -> int:
    return max(1, round(delay10ms * 60 / 100))


def pal_delay(delay10ms: int) -> int:
    return max(1, round(delay10ms * 50 / 100))


# ------------------------------------------------------------- tiles ---------

def tile32(rows8) -> bytes:
    """8 linhas x 8 indices (0..15) -> 32 bytes de padrao SMS (4 planos)."""
    out = bytearray()
    for row in rows8:
        planes = [0, 0, 0, 0]
        for x, v in enumerate(row):
            bit = 7 - x
            for p in range(4):
                if (v >> p) & 1:
                    planes[p] |= (1 << bit)
        out += bytes(planes)
    return bytes(out)


def pair_blob(rows16) -> bytes:
    return tile32(rows16[0:8]) + tile32(rows16[8:16])


def cell_density(rows16) -> int:
    return sum(1 for row in rows16 for v in row if v)


def extract_cells(png_path: Path, canvas, pair_pool: dict, key_rgb, p1_scaled):
    """Extrai celulas 8x16 do PNG; dedup de pares; retorna entradas.

    Entradas: dicts {dx, dy, tile, dens}. Ordem de varredura: banda, coluna.
    """
    got = read_indexed_png(str(png_path))
    w, h, px = got["w"], got["h"], got["pixels"]
    if not got["palette"] or tuple(got["palette"][0]) != key_rgb:
        raise SystemExit(f"pose sem transparencia magenta no indice 0: {png_path}")
    if [tuple(c) for c in got["palette"][1:]] != [tuple(c) for c in p1_scaled]:
        raise SystemExit(f"paleta da pose difere do registro de arte: {png_path}")
    dx0, dy0 = canvas["dx0"], canvas["dy0"]
    entries = []
    for b in range(h // 16):
        for c in range(w // 8):
            rows16 = [px[b * 16 + yy][c * 8:c * 8 + 8] for yy in range(16)]
            blob = pair_blob(rows16)
            dens = cell_density(rows16)
            if dens == 0:
                continue
            pid = pair_pool.get(blob)
            if pid is None:
                pid = len(pair_pool)
                pair_pool[blob] = pid
            entries.append({"dx": dx0 + c * 8, "dy": dy0 + b * 16,
                            "tile": pid * 2, "dens": dens})
    return entries


def sort_player_entries(entries):
    return sorted(entries, key=lambda e: (e["dy"], e["dx"]))


def sort_enemy_entries(entries):
    """Banda asc, densidade desc (esparsas por ultimo), coluna asc."""
    return sorted(entries, key=lambda e: (e["dy"], -e["dens"], e["dx"]))


# ------------------------------------------------- budget / simulacao --------

def cam_of(px: int) -> int:
    """Camera quantizada em 8 px (HUD fixo em BG exige scrollX = 0)."""
    return max(0, min(px - CAM_DX, CAM_MAX)) & ~7


def sim_scene(player_entries, enemy_entries, px, pz, ex, ez):
    """Simula o desenho do runtime (ordem SAT + orcamento por linha).

    Politica conservadora: todas as celulas do inimigo participam da contagem,
    mesmo as fora da tela (o runtime so pula o desenho quando x > 255) — assim
    a decisao de corte e funcao apenas de (pose, pz) e o emit pode gravar a
    mascara consultada pelo runtime.
    y do manifesto = primeira linha desenhada (mesmo Y de SMS_addSprite).
    Retorna (sprites, peak, drops).
    """
    cam = cam_of(px)
    lines = [0] * SCREEN_H
    sprites = []
    drops = []

    def add(entry, ax, az):
        x = ax - cam + entry["dx"]
        y = az - 32 + entry["dy"]
        if x > 255:
            return False
        for ly in range(y, min(y + 16, SCREEN_H)):
            lines[ly] += 1
        sprites.append({"x": x, "y": y, "tile": entry["tile"]})
        return True

    for e in player_entries:
        add(e, px, pz)
    for e in enemy_entries:
        x = ex - cam + e["dx"]
        y = ez - 32 + e["dy"]
        if y < SCREEN_H:
            if any(lines[ly] >= PER_LINE_MAX for ly in range(y, min(y + 16, SCREEN_H))):
                drops.append({"dx": e["dx"], "dy": e["dy"], "tile": e["tile"],
                              "x": x, "y": y})
                continue
        for ly in range(y, min(y + 16, SCREEN_H)):
            lines[ly] += 1
        if x > 255:
            continue
        sprites.append({"x": x, "y": y, "tile": e["tile"]})
    peak = max(lines) if lines else 0
    return sprites, peak, drops


def build_manifest(desc, sprites, peak, drops):
    return {
        "schema": "sprite_scene_manifest_v1",
        "sprite_size": "8x16",
        "zoomed": False,
        "screen_h": SCREEN_H,
        "sat_terminated": True,
        "sprites": sprites,
        "scene": desc,
        "simulation": {
            "peak_per_line": peak,
            "budget_drops": drops,
            "note": ("ordem SAT = jogador (tabela) + inimigo (banda, densidade "
                     "desc); corte por mascara pre-computada no emit (bit por "
                     "celula de inimigo), consultada pelo runtime"),
        },
    }


def enemy_drop_masks(ax_entries, enemy_entries):
    """Mascara de inclusao por (pose do jogador, pz) — 3 bytes por entrada.

    Politica conservadora: todas as celulas do inimigo entram na contagem
    (mesmo as que estao fora da tela, que o runtime pula so no desenho), entao
    a decisao de corte e funcao apenas de (pose, pz) e pode ser pre-computada
    em ROM. Bit i = celula i da tabela ordenada do inimigo (ate 24 celulas).
    """
    enemy_sorted = sort_enemy_entries([e for _key, entries in enemy_entries
                                       for e in entries])
    if len(enemy_sorted) > 24:
        raise SystemExit("mascara cobre no maximo 24 celulas de inimigo")
    masks = bytearray()
    for _key, entries in ax_entries:
        player_sorted = sort_player_entries(entries)
        for pz in range(Z_MIN, Z_MAX + 1):
            lines = [0] * SCREEN_H
            for e in player_sorted:
                y = pz - 32 + e["dy"]
                for ly in range(max(0, y), min(y + 16, SCREEN_H)):
                    lines[ly] += 1
            bits = [0] * len(enemy_sorted)
            for i, e in enumerate(enemy_sorted):
                y = ENEMY_Z - 32 + e["dy"]
                span = range(max(0, y), min(y + 16, SCREEN_H))
                if any(lines[ly] >= PER_LINE_MAX for ly in span):
                    continue
                bits[i] = 1
                for ly in span:
                    lines[ly] += 1
            masks += bytes([sum(bits[i] << i for i in range(0, min(8, len(bits)))),
                            sum(bits[i] << (i - 8) for i in range(8, min(16, len(bits)))),
                            sum(bits[i] << (i - 16) for i in range(16, len(bits)))])
    return bytes(masks)


def mask_stats(masks, pose_count, cell_count):
    """Resumo por pose: entradas com corte, pior corte e pz do pior caso."""
    n_pz = Z_MAX - Z_MIN + 1
    stats = []
    for p in range(pose_count):
        entries = 0
        total = 0
        worst = 0
        worst_pz = []
        for j in range(n_pz):
            b = masks[(p * n_pz + j) * 3:(p * n_pz + j + 1) * 3]
            v = b[0] | (b[1] << 8) | (b[2] << 16)
            dropped = cell_count - bin(v & ((1 << cell_count) - 1)).count("1")
            if dropped:
                entries += 1
                total += dropped
            if dropped > worst:
                worst = dropped
                worst_pz = [Z_MIN + j]
            elif dropped and dropped == worst:
                worst_pz.append(Z_MIN + j)
        stats.append({"pose_index": p, "entries_with_drops": entries,
                      "worst_cells_dropped": worst, "worst_pz": worst_pz,
                      "total_cells_dropped": total})
    return stats


# ------------------------------------------------------------- escrita -------

def c_array(name, data: bytes, per_line=16) -> str:
    lines = []
    for i in range(0, len(data), per_line):
        chunk = data[i:i + per_line]
        lines.append(",".join("0x%02X" % b for b in chunk))
    body = ",\n".join(lines)
    return f"const unsigned char {name}[{len(data)}] = {{\n{body}}};\n"


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cram_byte(code) -> int:
    r, g, b = code
    return (b << 4) | (g << 2) | r


# ------------------------------------------------------------------ main -----

def emit(project: Path, generated_at: str):
    art_record_path = latest(project, "data/generated/art/o2_art_conversion_*.json")
    art = load_json(art_record_path)
    for out in art["outputs"]:
        p = project / out["path"]
        if sha256_file(p) != out["sha256"]:
            raise SystemExit(f"artefato de arte divergente: {out['path']}")

    extract_path = latest(project, "data/generated/extract/gal_town1_art_extract_*.json")
    extract = load_json(extract_path)
    members = {m["member"]: m for m in extract["members"]}

    ir_path = latest(project, "data/generated/ir/gal_town1_level_ir_*.json")
    ir = load_json(ir_path)

    def src_entry(rel):
        p = project / rel
        return {"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size}

    sources = [src_entry(str(art_record_path.relative_to(project))),
               src_entry(str(extract_path.relative_to(project))),
               src_entry(str(ir_path.relative_to(project)))]

    txt_root = "data/source_openbor/gal_town1/data/chars"
    ax_txt = src_entry(f"{txt_root}/ax/ax.txt")
    long_txt = src_entry(f"{txt_root}/long/long.txt")
    sources += [ax_txt, long_txt]
    ax_anims = parse_anims(project / ax_txt["path"])
    long_anims = parse_anims(project / long_txt["path"])

    # spawns do IR
    pstart = None
    for ps in ir.get("player_starts", []):
        if ps.get("slot") == 1:
            pstart = ps
            break
    spawn = None
    for sp in ir.get("spawns", []):
        if (sp.get("name") or "").lower() == "long":
            spawn = sp
            break
    if pstart is None:
        raise SystemExit("player_starts slot 1 ausente no IR")
    if spawn is None:
        raise SystemExit("spawn 'long' ausente no IR")
    # mapeamento registrado no escopo O2 (decisions[0]): z do jogador =
    # PLAYER_MIN_Z + z da fonte; spawns de inimigo usam z direto do fonte.
    px0, pz0 = int(pstart["x"]), Z_MIN + int(pstart["z"])
    ex0, ez0 = int(spawn["coords"][0]), int(spawn["coords"][1])
    hp_enemy = int(spawn["health"]) if spawn.get("health") is not None else HP_ENEMY

    # delays (fonte -> NTSC)
    ax_idle_d = ax_anims["idle"]["delays"][0] if ax_anims["idle"]["delays"] else 8
    ax_walk_d = ax_anims["walk"]["delays"][0] if ax_anims["walk"]["delays"] else 12
    long_idle_d = long_anims["idle"]["delays"][0] if long_anims["idle"]["delays"] else 8
    ntsc_idle, ntsc_walk = ntsc_delay(ax_idle_d), ntsc_delay(ax_walk_d)
    if len(set(ax_anims["walk"]["delays"])) > 1:
        print("[sms_emit] aviso: walk tem delays mistos; usando o primeiro",
              file=sys.stderr)

    # paletas
    p0 = art["palettes"]["p0_bg"]["codes"]
    p1 = art["palettes"]["p1_sprites"]["codes"]
    scale = lambda codes: [(85 * c[0], 85 * c[1], 85 * c[2]) for c in codes]
    p0_scaled, p1_scaled = scale(p0), scale(p1)
    pal_bg = bytes([cram_byte(c) for c in p0] + [0x00] * (16 - len(p0)))
    if len(p0) > 16:
        raise SystemExit("P0 com mais de 16 cores")
    if len(p1) > 15:
        raise SystemExit("P1 com mais de 15 cores (indice 0 = transparente)")
    pal_spr = bytes([0x3C] + [cram_byte(c) for c in p1] + [0x00] * (15 - len(p1)))

    # poses
    pair_pool = {}
    poses_cfg = []
    for key in AX_POSES:
        actor = key.split("_")[0]
        rec = art["poses"][actor]
        canvas = rec["canvas"]
        png = next(p["pngs"]["left" if key.endswith("_left") else "right"]
                   for p in rec["poses"]
                   if key == f"{actor}_{p['frame']}_{'left' if key.endswith('_left') else 'right'}")
        poses_cfg.append((key, project / png, canvas, "ax"))
    for key in ENEMY_POSES:
        actor = key.split("_")[0]
        rec = art["poses"][actor]
        png = next(p["pngs"]["left"] for p in rec["poses"]
                   if key == f"{actor}_{p['frame']}_left")
        poses_cfg.append((key, project / png, rec["canvas"], "enemy"))

    ax_entries = []
    enemy_entries = []
    for key, png, canvas, kind in poses_cfg:
        entries = extract_cells(png, canvas, pair_pool, KEY_RGB, p1_scaled)
        if kind == "ax":
            ax_entries.append((key, entries))
        else:
            enemy_entries.append((key, entries))

    n_pairs = len(pair_pool)
    spr_tiles = b"".join(sorted(pair_pool, key=lambda b: pair_pool[b]))

    # menor dx do inimigo (para o define informativo do level.h)
    dmin = min(e["dx"] for _, entries in enemy_entries for e in entries)

    # palco
    stage_png = project / art["stage"]["png"]
    stage = read_indexed_png(str(stage_png))
    sw, shh, spx = stage["w"], stage["h"], stage["pixels"]
    if [tuple(c) for c in stage["palette"]] != p0_scaled:
        raise SystemExit("paleta do palco difere do registro de arte")
    cols, rows = sw // 8, shh // 8
    if cols != art["stage"]["cols"] or rows != art["stage"]["rows"]:
        raise SystemExit("dimensoes do palco divergem do registro")
    tile_pool = {}
    bg_cols = bytearray()
    stage_cells = []
    for cx in range(cols):
        for ry in range(rows):
            rows8 = [spx[ry * 8 + yy][cx * 8:cx * 8 + 8] for yy in range(8)]
            blob = tile32(rows8)
            if blob not in tile_pool:
                if len(tile_pool) >= 192:
                    raise SystemExit("palco excede 192 tiles do dicionario")
                tile_pool[blob] = len(tile_pool)
            stage_cells.append(tile_pool[blob])
    bg_tiles = b"".join(sorted(tile_pool, key=lambda b: tile_pool[b]))
    # bg_cols col-major: coluna x 22 linhas (linhas de exibicao 2..23)
    for cx in range(cols):
        for ry in range(rows):
            bg_cols.append(stage_cells[cx * rows + ry])
    bg_cols = bytes(bg_cols)

    # HUD
    hud_png = project / art["hud"]["png"]
    hud = read_indexed_png(str(hud_png))
    if hud["w"] != 32 or hud["h"] != 8:
        raise SystemExit("hud_tiles.png deve ser 32x8")
    hud_blobs = []
    for t in range(4):
        rows8 = [hud["pixels"][yy][t * 8:t * 8 + 8] for yy in range(8)]
        hud_blobs.append(tile32(rows8))
    if hud_blobs[2] != hud_blobs[3]:
        raise SystemExit("hud_tiles.png: tiles 3 e 4 devem ser iguais (preto)")
    if len({hud_blobs[0], hud_blobs[1], hud_blobs[2]}) != 3:
        raise SystemExit("hud_tiles.png: esperados 3 tiles distintos (verde/vermelho/preto)")
    hud_tiles = hud_blobs[0] + hud_blobs[1] + hud_blobs[2]

    # orcamento final
    spr_slots = n_pairs * 2
    bg_slots = len(tile_pool)
    hud_slots = 3
    total = spr_slots + bg_slots + hud_slots
    if total > VRAM_TILES:
        raise SystemExit(f"orcamento estourado: {total} > {VRAM_TILES} slots")
    tile_bg_base = spr_slots
    tile_hud_base = spr_slots + bg_slots

    # simulacoes do pior caso (px maximo, z=180)
    sims = []
    for pkey, entries in ax_entries:
        player_sorted = sort_player_entries(entries)
        for ekey, eentries in enemy_entries:
            enemy_sorted = sort_enemy_entries(eentries)
            sprites, peak, drops = sim_scene(player_sorted, enemy_sorted,
                                             PLAYER_MAX_X, PLAYER_START_Z, ex0, ez0)
            sims.append({"player": pkey, "enemy": ekey, "sprites": sprites,
                         "peak": peak, "drops": drops})
    worst = max(sims, key=lambda s: (s["peak"], len(s["sprites"])))
    if worst["peak"] > PER_LINE_MAX:
        raise SystemExit(f"pior caso viola 8/linha: {worst['peak']}")
    if len(worst["sprites"]) > SAT_MAX:
        raise SystemExit(f"pior caso estoura SAT: {len(worst['sprites'])}")
    max_sprites = max(len(s["sprites"]) for s in sims)

    # ---- headers ----
    inc = project / "inc/o2"
    heads = {}
    heads["pal_bg.h"] = (
        "/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
        f"#define O2_PAL_BG_LEN 16\n{c_array('o2_pal_bg', pal_bg)}")
    heads["pal_spr.h"] = (
        "/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
        f"#define O2_PAL_SPR_LEN 16\n{c_array('o2_pal_spr', pal_spr)}")
    heads["spr_tiles.h"] = (
        "/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
        f"#define O2_SPR_TILES_SIZE {len(spr_tiles)}\n"
        f"#define O2_SPR_PAIR_COUNT {n_pairs}\n{c_array('o2_spr_tiles', spr_tiles)}")
    heads["bg_tiles.h"] = (
        "/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
        f"#define O2_BG_TILES_SIZE {len(bg_tiles)}\n"
        f"#define O2_BG_TILE_COUNT {len(tile_pool)}\n{c_array('o2_bg_tiles', bg_tiles)}")
    heads["bg_cols.h"] = (
        "/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
        f"#define O2_STAGE_COLS {cols}\n#define O2_STAGE_ROWS {rows}\n"
        f"#define O2_BG_COLS_SIZE {len(bg_cols)}\n{c_array('o2_bg_cols', bg_cols)}")
    heads["hud_tiles.h"] = (
        "/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
        f"#define O2_HUD_TILES_SIZE {len(hud_tiles)}\n{c_array('o2_hud_tiles', hud_tiles)}")

    meta_txt = ["/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */",
                "typedef struct { signed char dx; signed char dy; unsigned char tile; } o2_cell;",
                "typedef struct { const o2_cell *cells; unsigned char count; } o2_pose;"]
    pose_refs = []
    for idx, (key, entries) in enumerate(ax_entries):
        ents = sort_player_entries(entries)
        body = ",".join("{%d,%d,%d}" % (e["dx"], e["dy"], e["tile"]) for e in ents)
        meta_txt.append(f"const o2_cell o2_ax_pose{idx}[] = {{{body}}};")
        pose_refs.append(f"{{o2_ax_pose{idx}, {len(ents)}}}")
        if len(ents) > 255:
            raise SystemExit("pose com mais de 255 celulas")
    meta_txt.append(f"#define O2_AX_POSE_COUNT {len(ax_entries)}")
    meta_txt.append(f"const o2_pose o2_ax_poses[{len(ax_entries)}] = {{"
                    + ", ".join(pose_refs) + "};")
    enemy_refs = []
    for idx, (key, entries) in enumerate(enemy_entries):
        ents = sort_enemy_entries(entries)
        body = ",".join("{%d,%d,%d}" % (e["dx"], e["dy"], e["tile"]) for e in ents)
        meta_txt.append(f"const o2_cell o2_enemy_pose{idx}[] = {{{body}}};")
        enemy_refs.append(f"{{o2_enemy_pose{idx}, {len(ents)}}}")
    meta_txt.append(f"#define O2_ENEMY_POSE_COUNT {len(enemy_entries)}")
    meta_txt.append(f"const o2_pose o2_enemy_poses[{len(enemy_entries)}] = {{"
                    + ", ".join(enemy_refs) + "};")
    heads["spr_meta.h"] = "\n".join(meta_txt) + "\n"

    # mascara de inclusao do inimigo por (pose do jogador, pz): o runtime so
    # consulta o bit e desenha se x <= 255; nenhuma contagem de linhas em CPU.
    masks = enemy_drop_masks(ax_entries, enemy_entries)
    heads["enemy_mask.h"] = (
        "/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
        f"#define O2_ENEMY_MASK_PZ_MIN {Z_MIN}\n"
        f"#define O2_ENEMY_MASK_PZ_COUNT {Z_MAX - Z_MIN + 1}\n"
        "#define O2_ENEMY_MASK_BYTES 3\n"
        f"#define O2_ENEMY_MASK_SIZE {len(masks)}\n"
        + c_array("o2_enemy_masks", masks))

    heads["level.h"] = f"""/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */
#define O2_SCREEN_H {SCREEN_H}
#define O2_PLAYER_START_X {px0}
#define O2_PLAYER_START_Z {pz0}
#define O2_PLAYER_MIN_X {PLAYER_MIN_X}
#define O2_PLAYER_MAX_X {PLAYER_MAX_X}
#define O2_Z_MIN {Z_MIN}
#define O2_Z_MAX {Z_MAX}
#define O2_CAM_DX {CAM_DX}
#define O2_CAM_MAX {CAM_MAX}
#define O2_WALK_SPEED {WALK_SPEED}
#define O2_ENEMY_X {ex0}
#define O2_ENEMY_Z {ez0}
#define O2_HP_PLAYER {HP_PLAYER}
#define O2_HP_ENEMY {hp_enemy}
#define O2_ENEMY_DX_MIN {dmin}
#define O2_TILE_SPR_BASE 0
#define O2_TILE_BG_BASE {tile_bg_base}
#define O2_TILE_HUD_GREEN {tile_hud_base}
#define O2_TILE_HUD_RED {tile_hud_base + 1}
#define O2_TILE_HUD_BLACK {tile_hud_base + 2}
#define O2_ANIM_DELAY_IDLE {ntsc_idle}
#define O2_ANIM_DELAY_WALK {ntsc_walk}
#define O2_HUD_PLAYER_ROW {HUD_PLAYER_ROW}
#define O2_HUD_ENEMY_ROW {HUD_ENEMY_ROW}
#define O2_HUD_COL0 {HUD_COL0}
#define O2_HUD_PLAYER_COLS {HUD_PLAYER_COLS}
#define O2_HUD_ENEMY_COLS {HUD_ENEMY_COLS}
"""
    written = []
    for name, text in heads.items():
        p = inc / name
        write_text(p, text)
        written.append({"path": str(p.relative_to(project)),
                        "sha256": sha256_file(p), "bytes": p.stat().st_size})
    mask_entry = next(w for w in written if w["path"].endswith("enemy_mask.h"))

    # ---- plano de VRAM ----
    plan = {
        "schema": "sms_vram_plan_v1",
        "screen_height": SCREEN_H,
        "vertical_scroll": False,
        "max_sprites": max_sprites,
        "reg6": "0xFB",
        "name_base": 0x3800,
        "regions": [
            {"label": "spr_tiles", "addr": 0, "bytes": len(spr_tiles),
             "role": "sprite_tiles"},
            {"label": "bg_tiles", "addr": tile_bg_base * 32, "bytes": len(bg_tiles),
             "role": "bg_tiles"},
            {"label": "hud_tiles", "addr": tile_hud_base * 32, "bytes": len(hud_tiles),
             "role": "bg_tiles"},
        ],
        "extra_name_tables": [],
        "pockets": [],
    }
    today = generated_at[:10].replace("-", "")
    plan_path = project / f"data/generated/plans/o2_vram_plan_{today}.json"
    write_text(plan_path, json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    written.append({"path": str(plan_path.relative_to(project)),
                    "sha256": sha256_file(plan_path), "bytes": plan_path.stat().st_size})

    # ---- manifests do pior caso ----
    manifests = []
    for pkey, entries in ax_entries:
        player_sorted = sort_player_entries(entries)
        for ekey, eentries in enemy_entries:
            enemy_sorted = sort_enemy_entries(eentries)
            sprites, peak, drops = sim_scene(player_sorted, enemy_sorted,
                                             PLAYER_MAX_X, PLAYER_START_Z, ex0, ez0)
            tag = pkey.replace("ax_", "")
            m = build_manifest(
                {"player_pose": pkey, "enemy_pose": ekey,
                 "player_x": PLAYER_MAX_X, "player_z": PLAYER_START_Z,
                 "enemy_x": ex0, "enemy_z": ez0, "camera": cam_of(PLAYER_MAX_X)},
                sprites, peak, drops)
            mp = project / f"data/generated/emit/o2_sprite_scene_{tag}_{today}.json"
            write_text(mp, json.dumps(m, indent=2, ensure_ascii=False) + "\n")
            manifests.append({"pose": pkey, "path": str(mp.relative_to(project)),
                              "sha256": sha256_file(mp), "bytes": mp.stat().st_size,
                              "sprites": len(sprites), "peak": peak,
                              "drops": len(drops)})
            written.append({"path": str(mp.relative_to(project)),
                            "sha256": sha256_file(mp), "bytes": mp.stat().st_size})

    # ---- registro de emissao ----
    record = {
        "schema": "openbor_sms_emission_v1",
        "generated_at": generated_at,
        "tool": "tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py",
        "scope": "O2 — pacote da ROM do piloto (tiles/metasprites/paletas/plano)",
        "sources": sources,
        "spawns": {
            "player": {"slot": 1, "x": px0, "z": pz0, "z_raw": int(pstart["z"]), "hp": HP_PLAYER,
                       "origin": "player_starts[slot=1]; z = PLAYER_MIN_Z + z_fonte (escopo O2 decisions[0]); hp de ax.txt"},
            "enemy": {"name": spawn.get("name"), "x": ex0, "z": ez0, "hp": hp_enemy,
                      "origin": "spawns[name=long]; z direto do fonte"},
        },
        "anim": {
            "idle_source_delay_10ms": ax_idle_d, "idle_ntsc_frames": ntsc_idle,
            "idle_pal_frames_declared": pal_delay(ax_idle_d),
            "walk_source_delay_10ms": ax_walk_d, "walk_ntsc_frames": ntsc_walk,
            "walk_pal_frames_declared": pal_delay(ax_walk_d),
            "walk_cycle_frames": ["walk01", "walk03"],
            "long_idle_source_delay_10ms": long_idle_d,
            "note": "1 delay = 10ms; NTSC = max(1, round(d*60/100)); PAL so declarado",
        },
        "sprites": {
            "pair_count": n_pairs,
            "slots_used": spr_slots,
            "poses": [{"pose": k, "cells": len(v)} for k, v in
                      ax_entries + enemy_entries],
            "budget_line_policy": (
                "jogador (ordem banda/coluna) sempre inteiro; inimigo em ordem "
                "(banda, densidade desc, coluna) com corte em 8 entradas/linha; "
                "decisao pre-computada no emit (inc/o2/enemy_mask.h) por "
                "(pose do jogador, pz) com politica conservadora: todas as "
                "celulas do inimigo contam no orcamento, mesmo fora da tela "
                "(o runtime so pula o desenho quando x > 255)"),
            "worst_case": {"peak_per_line": worst["peak"],
                           "sat_entries": len(worst["sprites"]),
                           "drops": worst["drops"],
                           "scene": {"player": worst["player"], "enemy": worst["enemy"]}},
        },
        "enemy_mask": {
            "path": mask_entry["path"], "sha256": mask_entry["sha256"],
            "bytes": mask_entry["bytes"], "pz_min": Z_MIN, "pz_max": Z_MAX,
            "pose_count": len(ax_entries), "cells": len(enemy_entries[0][1]),
            "policy": ("conservadora: contagem inclui todas as celulas do inimigo; "
                       "bit i = celula i da tabela ordenada; 3 bytes por entrada, "
                       "runtime consulta o bit e so desenha se x <= 255"),
            "stats": mask_stats(masks, len(ax_entries), len(enemy_entries[0][1])),
        },
        "tiles": {
            "sprite_base": 0, "sprite_slots": spr_slots,
            "bg_base": tile_bg_base, "bg_slots": bg_slots,
            "hud_base": tile_hud_base, "hud_slots": hud_slots,
            "total": total, "vram_tile_budget": VRAM_TILES,
            "margin": VRAM_TILES - total,
        },
        "simulations": [{"player": s["player"], "peak": s["peak"],
                         "sat_entries": len(s["sprites"]), "drops": len(s["drops"])}
                        for s in sims],
        "manifests": manifests,
        "outputs": written,
        "notes": [
            "tiles de sprite em pares 8x16 (SPRITEMODE_TALL) na primeira metade (reg6 0xFB)",
            "espelho = padroes proprios; VDP do SMS nao tem flip de sprite",
            "PNT so recebe linhas 2..23; HUD fixo nas linhas 0..1",
            "dither Bayer 4x4 apenas no palco; sprites com mapeamento duro",
            "camera quantizada em 8 px (cam &= ~7); BGScrollX = (-cam) & 0xFF "
            "desloca a imagem para a esquerda em cam pixels e o anel mod-32 de "
            "colunas fecha o wrap de 256 px; LOCKHSCROLL mantem as linhas 0..1 "
            "(HUD) fixas e LEFTCOLBLANK cobre a coluna 0",
            "corte do inimigo = mascara pre-computada (inc/o2/enemy_mask.h); o "
            "runtime nao conta linhas de sprite",
        ],
    }
    rec_path = project / f"data/generated/emit/o2_emission_{today}.json"
    write_text(rec_path, json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return rec_path, record


def self_check() -> int:
    ok = True
    # tile32: valor 1 -> plano 0 = 0xFF; valor 8 -> plano 3
    rows = [[1] * 8]
    t = tile32(rows)
    ok &= t[0] == 0xFF and t[1] == 0 and t[2] == 0 and t[3] == 0
    t = tile32([[8] * 8])
    ok &= t[3] == 0xFF and t[0] == 0
    # par: topo + base
    blob = pair_blob([[1] * 8] * 8 + [[16 - 1] * 8] * 8)
    ok &= len(blob) == 64 and blob[0] == 0xFF and blob[32 + 3] == 0xFF
    # orcamento: injeta 6+5 entradas no mesmo alinhamento -> corta para <=8
    player = [{"dx": 8 * i, "dy": 0, "tile": 0, "dens": 10} for i in range(6)]
    enemy = [{"dx": 8 * i, "dy": 0, "tile": 0, "dens": 10 - i} for i in range(5)]
    sprites, peak, drops = sim_scene(player, enemy, 484, 180, 500, 180)
    ok &= peak <= PER_LINE_MAX and len(drops) == 3 and len(sprites) == 8
    # mascara por (pose, pz): 6 do jogador + 5 do inimigo alinhados -> inclui 2,
    # corta 3; longe (pz minimo, sem sobreposicao de linhas) -> inclui as 5
    m = enemy_drop_masks([("ax", player)], [("enemy", enemy)])
    n_pz = Z_MAX - Z_MIN + 1
    ok &= len(m) == n_pz * 3
    ok &= m[(180 - Z_MIN) * 3] == 0b00000011
    ok &= m[0] == 0b00011111
    # cam clamp
    ok &= cam_of(10) == 0 and cam_of(400) == 280 and cam_of(600) == 376
    if not ok:
        print("[SELF-CHECK FAIL] sms_emit", file=sys.stderr)
        return 1
    print("[SELF-CHECK OK] sms_emit")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OpenBOR -> pacote C da ROM (O2)")
    ap.add_argument("--project", help="raiz do projeto SMSForge alvo")
    ap.add_argument("--generated-at", default=None)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.project:
        ap.error("--project e obrigatorio")
    project = Path(args.project).resolve()
    generated_at = args.generated_at or datetime.now(timezone.utc).replace(
        microsecond=0).isoformat()
    rec_path, record = emit(project, generated_at)
    t = record["tiles"]
    print(f"[sms_emit] sprites: {record['sprites']['pair_count']} pares "
          f"({t['sprite_slots']} slots) | BG {t['bg_slots']} | HUD {t['hud_slots']} "
          f"| total {t['total']}/{t['vram_tile_budget']} (margem {t['margin']})")
    wc = record["sprites"]["worst_case"]
    print(f"[sms_emit] pior caso: pico {wc['peak_per_line']}/linha, "
          f"{wc['sat_entries']} entradas SAT, {len(wc['drops'])} cortes")
    print(f"[sms_emit] registro: {rec_path.relative_to(project)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
