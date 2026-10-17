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

# ---------------------------------------------------------------- O3 ---------
# Lote O3 (combate): slots duplos por ator, blocos bancados (mapper), politica
# de corte por contadores de banda (D9-a), arc tables (D5) e tabelas de
# anim/IA. Referencia: doc/artifacts/o3_combat_scope_20261016.json.
O3_SCOPE = "doc/artifacts/o3_combat_scope_20261016.json"
O3_PER_LINE = 8
O3_ROWS = 6                      # linhas de canvas (96 px / 16)
O3_ROW_PITCH = 16                # passo vertical das linhas de celula
O3_DY0P = -80                    # canvas ax (conferido contra o escopo)
O3_DY0E = -72                    # canvas long (conferido contra o escopo)
O3_CELL_TILES = 2                # celula 8x16 = 2 tiles
O3_SLOT_CELLS = 29               # maior pose medida (ax/a102)
O3_SLOT_TILES = 58               # 29 * 2
O3_AX_SLOT_A = 0
O3_AX_SLOT_B = 58
O3_LONG_SLOT_A = 116
O3_LONG_SLOT_B = 174
O3_SPR_TILES = 232               # 2 atores x 2 slots x 58
O3_BG_BASE = 232
O3_BG_TILES = 192
O3_HUD_BASE = 424
O3_HUD_TILES = 3
O3_BANK_FIRST = 2                # blocos nos bancos 2..6 (D1)
O3_BANK_COUNT = 5
O3_BANK_BYTES = 16384
O3_DELAY_CAP = 255               # delay 999 (hold da fonte) satura em 255


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


# ------------------------------------------------------------ O3 helpers ----

def o3_row_counts(cells):
    """Contagem de celulas por linha de canvas (passo de 16 px)."""
    per = {}
    for c in cells:
        per[c["row"]] = per.get(c["row"], 0) + 1
    return per


def o3_overlap_rows(row, dy0p, dy0e, base_p, base_e, player_rows):
    """Linhas do jogador que dividem scanlines visiveis com a linha `row`
    do inimigo.

    Linhas de um mesmo ator nao se sobrepoem (passo 16 = altura da celula),
    entao uma scanline visivel e coberta por no maximo uma linha de cada
    ator; a contagem e exata: ax_row[rp] + ec[row]."""
    out = []
    e0 = base_e + dy0e + O3_ROW_PITCH * row
    if e0 < 1 or e0 > SCREEN_H - 1:
        return out
    for rp in player_rows:
        p0 = base_p + dy0p + O3_ROW_PITCH * rp
        if p0 < 1:
            continue
        lo = max(1, e0, p0)
        hi = min(SCREEN_H - 1, e0 + 15, p0 + 15)
        if hi >= lo:
            out.append(rp)
    return out


def o3_cells_of_png(png_path: Path, key_rgb, p1_scaled):
    """Celulas 8x16 ocupadas do canvas; ordem de varredura (banda, coluna)."""
    got = read_indexed_png(str(png_path))
    w, h, px = got["w"], got["h"], got["pixels"]
    if not got["palette"] or tuple(got["palette"][0]) != key_rgb:
        raise SystemExit(f"pose sem transparencia magenta no indice 0: {png_path}")
    if [tuple(c) for c in got["palette"][1:]] != [tuple(c) for c in p1_scaled]:
        raise SystemExit(f"paleta da pose difere do registro de arte: {png_path}")
    cells = []
    for row in range(h // 16):
        for col in range(w // 8):
            rows16 = [px[row * 16 + yy][col * 8:col * 8 + 8] for yy in range(16)]
            dens = cell_density(rows16)
            if dens:
                cells.append({"row": row, "col": col, "dens": dens,
                              "rows16": rows16})
    return cells


def o3_priority_order(cells):
    """Ordem de inclusao/sacrificio do inimigo: densidade desc, banda asc,
    coluna asc (celula esparsa cai primeiro; revisao artistica pendente)."""
    return sorted(cells, key=lambda c: (-c["dens"], c["row"], c["col"]))


def o3_line_peak_rows(ax_row, enemy_row, dy0p, dy0e, base_p, base_e):
    """Pico exato de celulas por scanline visivel (x ignorado: so reduz).

    - linha com topo < 1 nao desenha (politica O3) e nao conta;
    - linha com topo >= 192 desenha mas nao afeta linha visivel;
    - linha visivel e coberta por no maximo uma linha de cada ator, entao a
      contagem na scanline e ax_row[rp] + ec[r] nas regioes de sobreposicao."""
    peak = 0
    p_rows = ax_row or {}
    for r, ec in (enemy_row or {}).items():
        e0 = base_e + dy0e + O3_ROW_PITCH * r
        if e0 < 1:
            continue
        hi = min(SCREEN_H - 1, e0 + 15)
        if hi < e0:
            continue
        peak = max(peak, ec)
        for rp, pc in p_rows.items():
            p0 = base_p + dy0p + O3_ROW_PITCH * rp
            if p0 < 1:
                continue
            plo = max(e0, p0)
            phi = min(hi, p0 + 15)
            if phi >= plo:
                peak = max(peak, pc + ec)
    for rp, pc in p_rows.items():
        p0 = base_p + dy0p + O3_ROW_PITCH * rp
        if p0 < 1:
            continue
        if min(SCREEN_H - 1, p0 + 15) >= p0:
            peak = max(peak, pc)
    return peak


def o3_blocks_for_cells(cells):
    """Bloco de upload: par 8x16 (topo/baixo) por celula, na ordem empacotada."""
    out = bytearray()
    for c in cells:
        out += pair_blob(c["rows16"])
    return bytes(out)


def o3_pack_banks(blob_sizes):
    """Primeiro-encaixe nos bancos 2..6, com backfill; nunca parte um bloco.

    Blocos visitados na ordem da tabela e alocados no primeiro banco com
    folga (o runtime le banco/endereco da tabela, entao a ordem fisica e
    livre). Reprova se um bloco nao couber num banco ou os bancos acabarem
    (D1: blocos nos bancos 2-6; banco 7 de reserva)."""
    out = []
    free = [O3_BANK_BYTES] * O3_BANK_COUNT
    for i, size in enumerate(blob_sizes):
        if size > O3_BANK_BYTES:
            raise SystemExit(f"bloco {i} maior que um banco: {size}")
        for j in range(O3_BANK_COUNT):
            if free[j] >= size:
                out.append((O3_BANK_FIRST + j, O3_BANK_BYTES - free[j]))
                free[j] -= size
                break
        else:
            raise SystemExit("blocos de pose nao cabem nos bancos 2..6")
    return out


def o3_sim_arc(v0, vx, k=0.5, g=0.1):
    """D5: por tick pos += v*100/game_speed (k=0.5) e v -= g*k; tabela por
    frame NTSC (200 ticks/s -> 60 fps). Retorna (y[], x[], ticks_de_pouso).

    y[]/x[] por frame: indice 0 = origem; comprimento = frames + 1.
    x[] guarda o modulo do deslocamento (o runtime aplica o sinal do facing)."""
    yticks = [0.0]
    xticks = [0.0]
    alt = 0.0
    v = float(v0)
    x = 0.0
    t = 0
    while True:
        t += 1
        alt += v * k
        x += vx * k
        v -= g * k
        yticks.append(alt)
        xticks.append(x)
        if alt <= 0.0:
            break
    y = [0]
    xx = [0]
    n = 1
    while True:
        tick = int(n * 200 / 60 + 0.5)
        if tick >= len(yticks):
            break
        y.append(int(yticks[tick] + 0.5))
        xx.append(int(xticks[tick] + 0.5))
        n += 1
    return y, xx, t


def o3_sim_fall(alt0, k=0.5, g=0.1):
    """Queda de entrada (spawn em altitude alt0) com a mesma integracao de D5.

    Retorna (y[], ticks_de_pouso); y[0] = alt0 e y[-1] = 0."""
    yticks = [float(alt0)]
    alt = float(alt0)
    v = 0.0
    t = 0
    while True:
        t += 1
        alt += v * k
        v -= g * k
        yticks.append(alt)
        if alt <= 0.0:
            break
    y = [alt0]
    n = 1
    while True:
        tick = int(n * 200 / 60 + 0.5)
        if tick >= len(yticks):
            break
        y.append(max(0, int(yticks[tick] + 0.5)))
        n += 1
    return y, t


def o3_compose_rows(ax_row, enemy_cells, dy0p, dy0e, base_p, base_e,
                    limit=O3_PER_LINE):
    """Politica D9-a revisada (medicao M4): contagem exata por scanline.

    - o jogador nunca cai; sua contagem e estatica por linha de canvas
      (ax_row: {row: n}); x fora da tela nao entra (conservador);
    - o inimigo e visitado na ordem pre-computada (sacrificio: dens desc);
    - celula com topo < 1 nao desenha nem conta; topo >= 192 desenha e nao
      conta (nao afeta scanline visivel);
    - a contagem da linha candidata e ec[row] + 1 + max(ax_row[rp]) sobre as
      linhas do jogador que dividem scanlines visiveis com a linha do inimigo
      (o3_overlap_rows): e exata, sem cascata entre linhas vizinhas.

    Retorna (ec, drops, pico_exato)."""
    ec = {}
    drops = []
    p_rows = ax_row or {}
    for order, c in enumerate(enemy_cells):
        y0 = base_e + dy0e + O3_ROW_PITCH * c["row"]
        if y0 < 1:
            continue
        if y0 < SCREEN_H:
            m = 0
            for rp in o3_overlap_rows(c["row"], dy0p, dy0e, base_p, base_e,
                                      p_rows.keys()):
                m = max(m, p_rows[rp])
            if ec.get(c["row"], 0) + 1 + m > limit:
                drops.append({"order": order, "row": c["row"],
                              "col": c["col"], "dens": c["dens"]})
                continue
        ec[c["row"]] = ec.get(c["row"], 0) + 1
    return ec, drops, o3_line_peak_rows(ax_row, ec, dy0p, dy0e, base_p, base_e)


def o3_compose_sprites(ax_row, player_cells, dy0p, base_p, px,
                       enemy_cells, dy0e, base_e, ex, cam):
    """Composicao completa (SAT + drops + pico exato) espelhando o runtime.

    Ordem SAT: jogador (ordem da tabela de pose) e depois inimigo (ordem de
    prioridade). x fora de [0,255] nao desenha (o corte ignora x: conservador).
    y < 1 nao desenha nem conta (mesma regra do runtime). Player/None = so
    inimigo (caso solo)."""
    sat = []
    for c in (player_cells or []):
        y = base_p + dy0p + O3_ROW_PITCH * c["row"]
        if y < 1:
            continue
        x = px - cam + c["dx"]
        if x < 0 or x > 255:
            continue
        sat.append({"x": x, "y": y, "tile": O3_AX_SLOT_A + 2 * c["slot"]})
    ec, drops, peak = o3_compose_rows(ax_row, enemy_cells, dy0p, dy0e,
                                      base_p, base_e)
    dropped = {d["order"] for d in drops}
    for oi, c in enumerate(enemy_cells):
        if oi in dropped:
            continue
        y = base_e + dy0e + O3_ROW_PITCH * c["row"]
        if y < 1:
            continue
        x = ex - cam + c["dx"]
        if x < 0 or x > 255:
            continue
        sat.append({"x": x, "y": y, "tile": O3_LONG_SLOT_A + 2 * c["slot"]})
    return sat, ec, drops, peak


def o3_line_peak(sprites):
    """Pico exato de entradas por scanline para uma lista de sprites 8x16."""
    lines = [0] * SCREEN_H
    for s in sprites:
        for ly in range(max(0, s["y"]), min(s["y"] + 16, SCREEN_H)):
            lines[ly] += 1
    return max(lines) if lines else 0


def o3_shadow_lines(ax_row, enemy_cells, dy0p, dy0e, base_p, base_e,
                    include=None):
    """Simulacao linha-a-linha independente (brute force) do pico de celulas
    desenhadas por scanline visivel.

    `include` = indices do inimigo que desenham (None = todos). Confere a
    politica exata (o3_compose_rows) sem compartilhar a sua aritmetica."""
    lines = [0] * SCREEN_H

    def add(y0, n):
        if y0 < 1:
            return
        for ly in range(y0, min(y0 + 16, SCREEN_H)):
            lines[ly] += n

    for rp, pc in (ax_row or {}).items():
        add(base_p + dy0p + O3_ROW_PITCH * rp, pc)
    for oi, c in enumerate(enemy_cells):
        if include is not None and oi not in include:
            continue
        add(base_e + dy0e + O3_ROW_PITCH * c["row"], 1)
    return max(lines) if lines else 0


def o3_policy_crosscheck(cases):
    """Confere a politica exata contra o brute force linha-a-linha.

    `cases` = [(ax_row, enemy_cells, dy0p, dy0e, base_p, base_e)].
    Falha se o pico da politica diferir do brute force do mesmo conjunto
    incluido ou se o brute force passar de 8/linha. Retorna (casos, falhas)."""
    bad = 0
    for ax_row, cells, dy0p, dy0e, base_p, base_e in cases:
        ec, drops, peak = o3_compose_rows(ax_row, cells, dy0p, dy0e,
                                          base_p, base_e)
        keep = {i for i in range(len(cells))} - {d["order"] for d in drops}
        brute = o3_shadow_lines(ax_row, cells, dy0p, dy0e, base_p, base_e,
                                include=keep)
        if peak != brute or brute > O3_PER_LINE:
            bad += 1
    return len(cases), bad


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


# ------------------------------------------------------------- O3 emit ------

def _o3_load_env(project: Path):
    """Carrega e verifica escopo/M3/IR/O2 do lote O3 (fail-closed)."""
    scope_path = project / O3_SCOPE
    scope = load_json(scope_path)
    if (scope.get("schema") != "openbor_sms_batch_boundary_v1"
            or scope.get("artifact_kind") != "openbor_sms_o3_combat_scope"):
        raise SystemExit("escopo O3 ausente ou inesperado")

    art_path = latest(project, "data/generated/art/o3_art_conversion_*.json")
    art = load_json(art_path)
    for out in art["outputs"]:
        p = project / out["path"]
        if sha256_file(p) != out["sha256"]:
            raise SystemExit(f"artefato de arte divergente: {out['path']}")

    ir_paths, ir = {}, {}
    for actor in ("ax", "long"):
        ir_paths[actor] = latest(
            project, f"data/generated/ir/gal_town1_{actor}_model_ir_*.json")
        ir[actor] = load_json(ir_paths[actor])
        src = ir[actor]["source"]
        if sha256_file(project / src["path"]) != src["sha256"]:
            raise SystemExit(f"IR {actor}: fonte divergente ({src['path']})")

    o2_path = latest(project, "data/generated/emit/o2_emission_*.json")
    o2 = load_json(o2_path)
    return {"scope": scope, "scope_path": scope_path, "art": art,
            "art_path": art_path, "ir": ir, "ir_paths": ir_paths,
            "o2": o2, "o2_path": o2_path}


def _o3_pose_cells(data, canvas, actor, order):
    """Celulas de uma pose (lista empacotada) com dx/dy/slot."""
    dx0, dy0 = canvas[actor]["dx0"], canvas[actor]["dy0"]
    packed = []
    for slot, c in enumerate(order(data)):
        packed.append({"row": c["row"], "col": c["col"], "dens": c["dens"],
                       "slot": slot, "dx": dx0 + c["col"] * 8,
                       "dy": dy0 + c["row"] * 16, "rows16": c["rows16"]})
    return packed


def _o3_anim_plan(env):
    """Tabelas de anim do recorte: frames filtrados ao pose set + delays pinados."""
    scope = env["scope"]
    sc = scope["slice_contract"]
    anchor = scope["measured_budgets"]["canvas"]["anchor"]
    frame_sets = {"ax": scope["measured_budgets"]["pose_set_final"]["ax_frames"],
                  "long": scope["measured_budgets"]["pose_set_final"]["long_frames"]}
    anim_ids = {"ax": ["idle", "walk", "attack1", "jump", "pain2", "fall2",
                       "rise", "death"],
                "long": ["idle", "walk", "attack1", "pain2", "fall2", "rise",
                         "death"]}
    expected = {
        "ax": {"idle": [5], "walk": [7, 7], "attack1": [3, 3, 3, 3, 9],
               "jump": [21, O3_DELAY_CAP], "pain2": [5, 30],
               "fall2": [O3_DELAY_CAP, 5, 5, 5, 1], "rise": [33, 12],
               "death": [1]},
        "long": {"idle": [5], "walk": [7, 7], "attack1": [3, 3, 3, 9],
                 "pain2": [5, 30], "fall2": [O3_DELAY_CAP, 5, 5, 5, 1],
                 "rise": [33, 12]}}
    # ciclo de morte do long pinado em NTSC ("5/1,4/2,3/3,2/4,1/5 + 30" com a
    # repeticao x3 da fonte; delay 50 -> 30)
    long_death = ([5, 1] * 3 + [4, 2] * 3 + [3, 3] * 3 + [2, 4] * 3
                  + [1, 5] * 3 + [30])
    plan = {"ax": [], "long": []}
    attacks = {}
    for actor in ("ax", "long"):
        frame_idx = {f: i for i, f in enumerate(frame_sets[actor])}
        by_name = {a["name"]: a for a in env["ir"][actor]["anims"]}
        for aid, name in enumerate(anim_ids[actor]):
            src = by_name.get(name)
            if src is None:
                raise SystemExit(f"IR {actor}: anim {name} ausente")
            seq, dropped = [], 0
            for f in src["frames"]:
                frame = Path(f["path"]).name[:-4]
                if frame not in frame_idx:
                    dropped += 1
                    continue
                seq.append((frame, frame_idx[frame], f))
            if not seq:
                raise SystemExit(f"IR {actor}/{name}: nenhum frame no pose set")
            if name == "death" and actor == "long":
                delays = list(long_death)
                if len(delays) != len(seq):
                    raise SystemExit("ciclo de morte do long diverge da fonte")
            else:
                delays = [min(O3_DELAY_CAP, ntsc_delay(f["delay"]))
                          for _fr, _i, f in seq]
                if delays != expected[actor][name]:
                    raise SystemExit(
                        f"delays {actor}/{name} = {delays} != pin "
                        f"{expected[actor][name]}")
            entry = {"id": aid, "name": name,
                     "frames": [[i, d] for (_fr, i, _f), d in zip(seq, delays)],
                     "frame_names": [fr for fr, _i, _f in seq],
                     "loop": 1 if name in ("idle", "walk") else 0,
                     "land": 0xFF, "dropped_source_frames": dropped}
            if name == "fall2" and src["landframe"] is not None:
                entry["land"] = int(src["landframe"])
            plan[actor].append(entry)
        # caixa de ataque: IR x pin do escopo (relativa ao anchor 240,204)
        src = by_name["attack1"]
        pin = sc["attack_boxes"][f"{actor}_attack1"]
        seq = [f for f in src["frames"]
               if Path(f["path"]).name[:-4] in frame_idx]
        box = slot = None
        active = []
        for pos, f in enumerate(seq):
            if not f["attacks"]:
                continue
            at = f["attacks"][0]
            vals = [at["x"], at["y"], at["right"], at["down"], at["damage"],
                    at["pausetime"], at["depth"]]
            if box is None:
                box, slot = vals, at["slot"]
            elif vals != box or at["slot"] != slot:
                raise SystemExit(f"{actor}/attack1: caixas/slots divergentes")
            active.append(pos)
        pin_box = [pin["box"][0], pin["box"][1], pin["box"][2], pin["box"][3],
                   pin["box"][4], pin["box"][8], pin["box"][9]]
        if box != pin_box:
            raise SystemExit(f"{actor}/attack1: caixa IR {box} != escopo {pin_box}")
        pin_active = [pos for pos, f in enumerate(seq)
                      if Path(f["path"]).name[:-4] in pin["ativo"]]
        if active != pin_active:
            raise SystemExit(f"{actor}/attack1: frames ativos {active} != pin {pin_active}")
        attacks[actor] = {
            "slot": slot, "box_abs": box,
            "rel": [box[0] - anchor[0], box[1] - anchor[1], box[2], box[3]],
            "damage": box[4], "pause": box[5], "depth": box[6],
            "first": active[0], "last": active[-1], "active": active}
    return plan, attacks


def _o3_header_poses(poses):
    out = ["/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
           "/* pose = frame*2 + lado (0=left, 1=right); cell = indice no slot;\n"
           "   tile do sprite = slot_base + 2*cell; dx/dy relativos ao anchor */\n"
           "typedef struct { signed char dx; signed char dy; "
           "unsigned char cell; } o3_cell;\n"
           "typedef struct { const o3_cell *cells; unsigned char count; } o3_pose;\n"]
    for actor in ("ax", "long"):
        for i, p in enumerate(poses[actor]):
            body = ",".join(f"{{{c['dx']},{c['dy']},{c['slot']}}}"
                            for c in p["cells"])
            out.append(f"const o3_cell o3_{actor}_pose{i:02d}[] = {{{body}}};\n")
        out.append(f"#define O3_{actor.upper()}_POSE_COUNT {len(poses[actor])}\n")
        entries = ",".join(f"{{o3_{actor}_pose{i:02d},{len(p['cells'])}}}"
                           for i, p in enumerate(poses[actor]))
        out.append(f"const o3_pose o3_{actor}_poses[{len(poses[actor])}] = "
                   f"{{{entries}}};\n")
    return "".join(out)


def _o3_header_blocks(blocks, bank_map):
    out = ["/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
           "/* bloco da pose = count*64 bytes, lido em 0x8000+addr apos\n"
           "   SMS_mapROMBank(bank); banco 7 = reserva (D1) */\n"
           "typedef struct { unsigned char bank; unsigned int addr; } o3_block;\n"]
    idx = 0
    for actor in ("ax", "long"):
        n = len(blocks[actor])
        entries = ",".join(f"{{{bank_map[idx + i][0]},{bank_map[idx + i][1]}}}"
                           for i in range(n))
        out.append(f"const o3_block o3_{actor}_blocks[{n}] = {{{entries}}};\n")
        out.append(f"#define O3_{actor.upper()}_BLOCK_COUNT {n}\n")
        idx += n
    out.append(f"#define O3_BLOCK_BYTES_PER_CELL 64\n"
               f"#define O3_BANK_FIRST {O3_BANK_FIRST}\n"
               f"#define O3_BANK_COUNT {O3_BANK_COUNT}\n")
    return "".join(out)


def _o3_header_rows(poses, canvas):
    out = ["/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
           "/* politica de corte D9-a revisada (contagem exata por scanline):\n"
           "   o runtime mantem ec[O3_ROWS] (celulas incluidas por linha do\n"
           "   inimigo) e consulta a tabela estatica do jogador por indice de\n"
           "   pose (frame*2 + lado); linhas do mesmo ator nao se sobrepoem\n"
           "   (passo 16 px), entao line_count = o3_ax_rows[pose][rp] + ec[r]\n"
           "   nas regioes sobrepostas. Sobreposicao: linhas cujos topos\n"
           "   dividem scanlines visiveis (1..191). */\n"
           f"#define O3_ROWS {O3_ROWS}\n"
           f"#define O3_ROW_PITCH {O3_ROW_PITCH}\n"
           f"#define O3_DY0P ({canvas['ax']['dy0']})\n"
           f"#define O3_DY0E ({canvas['long']['dy0']})\n"]
    rows = ["{" + ",".join(str(v) for v in (p["rows"].get(r, 0)
                                            for r in range(O3_ROWS))) + "}"
            for p in poses["ax"]]
    out.append(f"const unsigned char o3_ax_rows[{len(poses['ax'])}][{O3_ROWS}]"
               " = {" + ",".join(rows) + "};\n")
    return "".join(out)


def _o3_header_anim(plan, attacks):
    out = ["/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
           "/* frame = indice no pose set; pose = frame*2 + facing (0=left,1=right);\n"
           "   land = 0xFF quando nao ha landframe; delays em frames NTSC */\n"
           "typedef struct { unsigned char frame; unsigned char delay; } o3_aframe;\n"
           "typedef struct { const o3_aframe *frames; unsigned char count; "
           "unsigned char loop; unsigned char land; } o3_anim;\n"
           "typedef struct { signed char x, y; unsigned char w, h, dmg, pause, "
           "depth, first, last; } o3_attack;\n"]
    for actor in ("ax", "long"):
        for e in plan[actor]:
            rows = ",".join(f"{{{i},{d}}}" for i, d in e["frames"])
            out.append(f"const o3_aframe o3_{actor}_anim_{e['name']}[] = {{{rows}}};\n")
        for e in plan[actor]:
            out.append(f"#define O3_{actor.upper()}_ANIM_{e['name'].upper()} {e['id']}\n")
        out.append(f"#define O3_{actor.upper()}_ANIM_COUNT {len(plan[actor])}\n")
        entries = ",".join(
            f"{{o3_{actor}_anim_{e['name']}}},{len(e['frames'])},{e['loop']},"
            f"{e['land']}}}" for e in plan[actor])
        out.append(f"const o3_anim o3_{actor}_anims[{len(plan[actor])}] = "
                   f"{{{entries}}};\n")
        a = attacks[actor]
        out.append(f"const o3_attack o3_{actor}_attack = "
                   f"{{{a['rel'][0]},{a['rel'][1]},{a['rel'][2]},{a['rel'][3]},"
                   f"{a['damage']},{a['pause']},{a['depth']},{a['first']},"
                   f"{a['last']}}};\n")
    return "".join(out)


def _o3_header_arcs(arcs):
    out = ["/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
           "/* D5 simulado por tick (pos += v*100/gs, v -= g*100/gs) e amostrado por\n"
           "   frame NTSC; x = modulo do deslocamento (sinal do facing no runtime) */\n"]
    for label, d in (("jump", arcs["jump"]), ("toss", arcs["toss"])):
        out.append(f"#define O3_{label.upper()}_FRAMES {d['frames']}\n")
        out.append(c_array(f"o3_{label}_y", bytes(d["y"]), per_line=16))
        out.append(c_array(f"o3_{label}_x", bytes(d["x"]), per_line=16))
    out.append(f"#define O3_ENTRY_FRAMES {arcs['entry']['frames']}\n")
    out.append(c_array("o3_entry_y", bytes(arcs["entry"]["y"]), per_line=16))
    return "".join(out)


def _o3_header_level(env):
    sc = env["scope"]["slice_contract"]
    q88 = sc["physics_tables"]["q88"]
    return (
        "/* gerado por tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py */\n"
        f"#define O3_SCREEN_H {SCREEN_H}\n"
        f"#define O3_PLAYER_START_X {sc['spawn']['player']['x']}\n"
        f"#define O3_PLAYER_START_Z {sc['spawn']['player']['z']}\n"
        f"#define O3_PLAYER_START_ALT {sc['spawn']['player']['altitude']}\n"
        f"#define O3_PLAYER_MIN_X {PLAYER_MIN_X}\n"
        f"#define O3_PLAYER_MAX_X {PLAYER_MAX_X}\n"
        f"#define O3_ENEMY_X {sc['spawn']['enemy']['x']}\n"
        f"#define O3_ENEMY_Z {sc['spawn']['enemy']['z']}\n"
        f"#define O3_Z_MIN {Z_MIN}\n"
        f"#define O3_Z_MAX {Z_MAX}\n"
        f"#define O3_CAM_DX {CAM_DX}\n"
        f"#define O3_CAM_MAX {CAM_MAX}\n"
        f"#define O3_HP_PLAYER {sc['cast']['hp_player']}\n"
        f"#define O3_HP_ENEMY {sc['cast']['hp_enemy']}\n"
        f"#define O3_WALK_Q8 {q88['player_walk']}u\n"
        f"#define O3_CHASE_Q8 {q88['enemy_chase']}u\n"
        f"#define O3_ATTACK_RANGE_X {sc['ia']['attack_range_x']}\n"
        f"#define O3_ATTACK_RANGE_Z {sc['ia']['attack_range_z']}\n"
        f"#define O3_HIT_Z_TOLERANCE {sc['hit_rules']['z_tolerance']}\n"
        f"#define O3_NEXT_HIT_FRAMES {sc['hit_rules']['next_hit_frames']}\n"
        f"#define O3_HITSTOP_AX {sc['hit_rules']['hitstop_frames']['ax']}\n"
        f"#define O3_HITSTOP_LONG {sc['hit_rules']['hitstop_frames']['long']}\n"
        f"#define O3_TILE_SPR_BASE {O3_AX_SLOT_A}\n"
        f"#define O3_TILE_BG_BASE {O3_BG_BASE}\n"
        f"#define O3_TILE_HUD_GREEN {O3_HUD_BASE}\n"
        f"#define O3_TILE_HUD_RED {O3_HUD_BASE + 1}\n"
        f"#define O3_TILE_HUD_BLACK {O3_HUD_BASE + 2}\n"
        f"#define O3_SLOT_CELLS {O3_SLOT_CELLS}\n"
        f"#define O3_CELL_TILES {O3_CELL_TILES}\n"
        f"#define O3_AX_SLOT_A {O3_AX_SLOT_A}\n"
        f"#define O3_AX_SLOT_B {O3_AX_SLOT_B}\n"
        f"#define O3_LONG_SLOT_A {O3_LONG_SLOT_A}\n"
        f"#define O3_LONG_SLOT_B {O3_LONG_SLOT_B}\n"
        f"#define O3_PER_ROW_MAX {O3_PER_LINE}\n")


def emit_o3(project: Path, generated_at: str):
    env = _o3_load_env(project)
    scope, art = env["scope"], env["art"]
    mb = scope["measured_budgets"]
    stamp = generated_at[:10].replace("-", "")
    canvas = mb["canvas"]
    if canvas["ax"]["dy0"] != O3_DY0P or canvas["long"]["dy0"] != O3_DY0E:
        raise SystemExit(
            "canvas dy0 do escopo difere das constantes O3_DY0P/O3_DY0E")
    frame_sets = {"ax": mb["pose_set_final"]["ax_frames"],
                  "long": mb["pose_set_final"]["long_frames"]}
    for actor in ("ax", "long"):
        if [p["frame"] for p in art["poses"][actor]["poses"]] != frame_sets[actor]:
            raise SystemExit(f"poses {actor} do M3 divergem do escopo (ordem/nomes)")
        if art["poses"][actor]["frames"] != frame_sets[actor]:
            raise SystemExit(f"frames {actor} do M3 divergem do escopo")
    p1_codes = art["palettes"]["p1_sprites"]["codes"]
    p1_scaled = [(85 * c[0], 85 * c[1], 85 * c[2]) for c in p1_codes]

    # ---- poses: celulas, perfis, blocos, bancos -----------------------------
    poses = {"ax": [], "long": []}
    blocks = {"ax": [], "long": []}
    cells_both = {"ax": 0, "long": 0}
    max_cells = 0
    max_row = {"ax": 0, "long": 0}
    long_over = []
    for actor in ("ax", "long"):
        order = o3_priority_order if actor == "long" else \
            (lambda cs: sorted(cs, key=lambda c: (c["row"], c["col"])))
        for pose in art["poses"][actor]["poses"]:
            frame, declared = pose["frame"], pose["cells_8x16"]
            side_cells = {}
            for side in ("left", "right"):
                png = project / pose["pngs"][side]
                if sha256_file(png) != pose["sha256"][side]:
                    raise SystemExit(f"PNG de pose divergente: {pose['pngs'][side]}")
                got = o3_cells_of_png(png, KEY_RGB, p1_scaled)
                if len(got) != declared:
                    raise SystemExit(
                        f"{actor}/{frame}/{side}: {len(got)} celulas != {declared} (M3)")
                side_cells[side] = got
            if declared != mb["cells_per_frame"][actor][frame]:
                raise SystemExit(f"{actor}/{frame}: contagem diverge do escopo")
            for side in ("left", "right"):
                per_row = o3_row_counts(side_cells[side])
                row_peak = max(per_row.values())
                if actor == "ax" and row_peak > O3_PER_LINE:
                    raise SystemExit(
                        f"ax/{frame}/{side}: {row_peak} celulas na mesma linha"
                        " (jogador desenha inteiro, sem mecanismo de corte)")
                if actor == "long" and row_peak > O3_PER_LINE:
                    long_over.append({"frame": frame, "side": side,
                                      "row_peak": row_peak})
                max_row[actor] = max(max_row[actor], row_peak)
                packed = _o3_pose_cells(side_cells[side], canvas, actor, order)
                poses[actor].append(
                    {"frame": frame, "side": side, "cells": packed,
                     "rows": per_row})
                blocks[actor].append(o3_blocks_for_cells(packed))
                cells_both[actor] += len(packed)
                max_cells = max(max_cells, len(packed))
    if max_cells > O3_SLOT_CELLS:
        raise SystemExit(f"pose com {max_cells} celulas > slot {O3_SLOT_CELLS}")
    flat_blocks = blocks["ax"] + blocks["long"]
    total_bytes = sum(len(b) for b in flat_blocks)
    if total_bytes > O3_BANK_COUNT * O3_BANK_BYTES:
        raise SystemExit("blocos excedem os bancos 2..6")
    bank_map = o3_pack_banks([len(b) for b in flat_blocks])
    bank_bin = bytearray(O3_BANK_COUNT * O3_BANK_BYTES)
    bank_used = {}
    for blob, (bank, addr) in zip(flat_blocks, bank_map):
        off = (bank - O3_BANK_FIRST) * O3_BANK_BYTES + addr
        bank_bin[off:off + len(blob)] = blob
        bank_used[bank] = max(bank_used.get(bank, 0), addr + len(blob))

    # ---- anim/arcs -----------------------------------------------------------
    anim_plan, attacks = _o3_anim_plan(env)
    jump_y, jump_x, jump_ticks = o3_sim_arc(3.3, 1.0)
    toss_y, toss_x, toss_ticks = o3_sim_arc(3.0, 1.2)
    entry_y, entry_ticks = o3_sim_fall(200)
    arcs = {"jump": {"frames": len(jump_y) - 1, "apex": max(jump_y),
                     "drift": jump_x[-1], "ticks": jump_ticks,
                     "y": jump_y, "x": jump_x},
            "toss": {"frames": len(toss_y) - 1, "apex": max(toss_y),
                     "drift": toss_x[-1], "ticks": toss_ticks,
                     "y": toss_y, "x": toss_x},
            "entry": {"frames": len(entry_y) - 1, "ticks": entry_ticks,
                      "y": entry_y}}
    if not (39 <= arcs["jump"]["frames"] <= 41
            and 53 <= arcs["jump"]["apex"] <= 56
            and 64 <= arcs["jump"]["drift"] <= 68):
        raise SystemExit(f"pulo fora do contrato D5: {arcs['jump']}")
    if not (35 <= arcs["toss"]["frames"] <= 37
            and 44 <= arcs["toss"]["apex"] <= 47
            and 70 <= arcs["toss"]["drift"] <= 74):
        raise SystemExit(f"arremesso fora do contrato D5: {arcs['toss']}")

    # ---- varredura declarada da politica (D9-a revisada) ---------------------
    dy0p = canvas["ax"]["dy0"]
    dy0e = canvas["long"]["dy0"]
    dz_values = (-128, -64, -24, -8, 0, 8, 24, 64, 128)

    ax_rows = [p["rows"] for p in poses["ax"]]

    scan = {"cases": 0, "violations": [], "max_line_peak": 0,
            "scenes_with_drops": 0, "top": []}
    for ai, pa in enumerate(poses["ax"]):
        for li, pl in enumerate(poses["long"]):
            for dz in dz_values:
                for s_p in (9, 19, 25):
                    for rho in (0, 7):
                        base_p = 8 * s_p + rho
                        base_e = base_p + dz
                        _ec, drops, peak = o3_compose_rows(
                            ax_rows[ai], pl["cells"], dy0p, dy0e,
                            base_p, base_e)
                        scan["cases"] += 1
                        if peak > scan["max_line_peak"]:
                            scan["max_line_peak"] = peak
                        if peak > O3_PER_LINE:
                            scan["violations"].append(
                                {"ax": ai, "long": li, "dz": dz, "s_p": s_p,
                                 "rho": rho, "peak": peak})
                        if drops:
                            scan["scenes_with_drops"] += 1
                        scan["top"].append((len(drops), peak, ai, li, dz, s_p, rho))
        if len(scan["top"]) > 20000:
            scan["top"].sort(key=lambda t: (-t[0], -t[1]))
            del scan["top"][8:]
    scan["top"].sort(key=lambda t: (-t[0], -t[1]))
    scan["top"] = scan["top"][:8]
    if scan["violations"]:
        raise SystemExit(
            f"politica D9-a viola 8/linha em {len(scan['violations'])} casos")

    # ---- cross-check brute force (linha a linha, independente) --------------
    xcheck_cases, xcheck_bad = o3_policy_crosscheck([
        (ax_rows[ai], poses["long"][li]["cells"], dy0p, dy0e,
         8 * s_p + rho, 8 * s_p + rho + dz)
        for ai in range(0, len(poses["ax"]), 7)
        for li in range(0, len(poses["long"]), 5)
        for dz in (-64, 0, 24)
        for s_p in (9, 19, 25)
        for rho in (0, 7)])
    if xcheck_bad:
        raise SystemExit(
            f"politica de linhas diverge do brute force em {xcheck_bad} casos")

    # ---- solo (acumulacao do proprio inimigo; caso declarado 9/linha) --------
    solo = []
    for li, pl in enumerate(poses["long"]):
        _ec, drops, peak = o3_compose_rows({}, pl["cells"], dy0p, dy0e,
                                           152, 152)
        solo.append({"pose": li, "frame": pl["frame"], "side": pl["side"],
                     "peak": peak, "drops": len(drops), "dropped": drops})
    solo_declared = [s for s in solo if s["frame"] in ("fall03", "death01")]
    if any(s["drops"] != 1 for s in solo_declared):
        raise SystemExit("caso declarado fall03/death01 solo nao cai em 1 celula")
    if any(s["drops"] for s in solo if s["frame"] not in ("fall03", "death01")):
        raise SystemExit("long solo fora do declarado com celulas caindo")
    declared_over = {"fall03", "death01"}
    if not {d["frame"] for d in long_over} <= declared_over:
        raise SystemExit(f"long com linha acima de 8 fora do declarado: {long_over}")

    # ---- manifests -----------------------------------------------------------
    def scene_desc(kind, pa, pl, dz, base_p, counters, note):
        return {"kind": kind, "policy": "o3 linhas exatas D9-a revisada",
                "player": None if pa is None else
                {"frame": pa["frame"], "side": pa["side"],
                 "pose_index": poses["ax"].index(pa),
                 "rows": "contagem por linha de canvas (sem x)"},
                "enemy": {"frame": pl["frame"], "side": pl["side"],
                          "pose_index": poses["long"].index(pl)},
                "dz": dz, "base_player": base_p, "base_enemy": base_p + dz,
                "counters": counters, "note": note,
                "sat_order": "jogador (ordem da pose) + inimigo (dens desc)"}

    def write_manifest(path: Path, scene, sat, ec, drops, pre_peak):
        peak = o3_line_peak(sat)
        if peak > O3_PER_LINE:
            raise SystemExit(f"{path.name}: pico {peak} > 8 pos-politica")
        if len(sat) > SAT_MAX:
            raise SystemExit(f"{path.name}: SAT {len(sat)} > {SAT_MAX}")
        for s in sat:
            if not (0 <= s["x"] <= 255 and 1 <= s["y"] <= 255
                    and 0 <= s["tile"] <= 255):
                raise SystemExit(f"{path.name}: sprite fora do contrato: {s}")
        manifest = {
            "schema": "sprite_scene_manifest_v1",
            "sprite_size": "8x16", "zoomed": False, "screen_h": SCREEN_H,
            "sat_terminated": True, "sprites": sat, "scene": scene,
            "simulation": {"peak_per_line": peak, "pre_policy_peak": pre_peak,
                           "row_counters": {str(k): v
                                            for k, v in sorted(ec.items())},
                           "drops": len(drops), "drops_detail": drops[:8],
                           "sat_entries": len(sat),
                           "note": ("politica D9-a revisada: contagem exata por "
                                    "linha de canvas (passo 16) + tabela "
                                    "estatica do jogador; conferido pelo gate "
                                    "audit_sprite_line_sim")}}
        write_text(path, json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
        return manifest

    px, ex, cam = 484, 500, cam_of(484)
    manifests = []

    def emit_pair(pa, pl, dz, base_p, kind, stem):
        sat, ec, drops, peak = o3_compose_sprites(
            pa["rows"], pa["cells"], dy0p, base_p, px,
            pl["cells"], dy0e, base_p + dz, ex, cam)
        all_sat = []
        for c in pa["cells"]:
            y = base_p + dy0p + O3_ROW_PITCH * c["row"]
            if y < 1:
                continue
            x = px - cam + c["dx"]
            if 0 <= x <= 255:
                all_sat.append({"x": x, "y": y, "tile": 0})
        for c in pl["cells"]:
            y = base_p + dz + dy0e + O3_ROW_PITCH * c["row"]
            if y < 1:
                continue
            x = ex - cam + c["dx"]
            if 0 <= x <= 255:
                all_sat.append({"x": x, "y": y, "tile": 0})
        pre_peak = o3_line_peak(all_sat)
        scene = scene_desc(kind, pa, pl, dz, base_p,
                           "linhas do jogador (estatico) + ec do inimigo",
                           "cena de politica (x fixo para o gate; decisao "
                           "x-independente, licao O2)")
        path = project / f"data/generated/emit/{stem}_{stamp}.json"
        manifest = write_manifest(path, scene, sat, ec, drops, pre_peak)
        manifests.append((path, manifest))
        return manifest

    for side in ("left", "right"):
        pa = next(p for p in poses["ax"]
                  if p["frame"] == "a102" and p["side"] == side)
        pl = next(p for p in poses["long"]
                  if p["frame"] == "fall03" and p["side"] == side)
        emit_pair(pa, pl, 24, 152, "worst_pair_declared",
                  f"o3_sprite_scene_pair_a102_{side}_fall03_{side}_dz24")

    for frame in ("fall03", "death01"):
        for side in ("left", "right"):
            pl = next(p for p in poses["long"]
                      if p["frame"] == frame and p["side"] == side)
            sat, ec, drops, peak = o3_compose_sprites(
                None, None, dy0p, 152, px, pl["cells"], dy0e, 152, ex, cam)
            all_sat = []
            for c in pl["cells"]:
                y = 152 + dy0e + O3_ROW_PITCH * c["row"]
                if y < 1:
                    continue
                x = ex - cam + c["dx"]
                if 0 <= x <= 255:
                    all_sat.append({"x": x, "y": y, "tile": 0})
            scene = scene_desc("solo_declared", None, pl, 0, 152,
                               "zero (acumulacao do proprio inimigo)",
                               "propriedade de politica do caso declarado 9/linha")
            path = project / (
                f"data/generated/emit/o3_sprite_scene_solo_long_{frame}"
                f"_{side}_{stamp}.json")
            manifest = write_manifest(path, scene, sat, ec, drops,
                                      o3_line_peak(all_sat))
            manifests.append((path, manifest))

    for i, (ndrops, peak, ai, li, dz, s_p, rho) in enumerate(scan["top"][:6]):
        pa, pl = poses["ax"][ai], poses["long"][li]
        emit_pair(pa, pl, dz, 8 * s_p + rho, "scan_pressure",
                  f"o3_sprite_scene_scan{i}_ax_{pa['frame']}_{pa['side']}"
                  f"_long_{pl['frame']}_{pl['side']}_dz{dz}")

    # ---- escritas ------------------------------------------------------------
    inc = project / "inc/o3"
    heads = {
        "o3_poses.h": _o3_header_poses(poses),
        "o3_blocks.h": _o3_header_blocks(blocks, bank_map),
        "o3_rows.h": _o3_header_rows(poses, canvas),
        "o3_anim.h": _o3_header_anim(anim_plan, attacks),
        "o3_arcs.h": _o3_header_arcs(arcs),
        "level.h": _o3_header_level(env),
    }
    for name, text in heads.items():
        write_text(inc / name, text)
    bank_bin_path = project / f"res/o3/banks/o3_pose_blocks_{stamp}.bin"
    bank_bin_path.parent.mkdir(parents=True, exist_ok=True)
    bank_bin_path.write_bytes(bytes(bank_bin))

    plan = {
        "schema": "sms_vram_plan_v1", "screen_height": SCREEN_H,
        "vertical_scroll": False, "max_sprites": 2 * O3_SLOT_CELLS,
        "reg6": "0xFB", "name_base": 14336,
        "regions": [
            {"label": "spr_tiles", "addr": 0, "bytes": O3_SPR_TILES * 32,
             "role": "sprite_tiles"},
            {"label": "bg_tiles", "addr": O3_BG_BASE * 32,
             "bytes": O3_BG_TILES * 32, "role": "bg_tiles"},
            {"label": "hud_tiles", "addr": O3_HUD_BASE * 32,
             "bytes": O3_HUD_TILES * 32, "role": "bg_tiles"}],
        "extra_name_tables": [], "pockets": []}
    plan_path = project / f"data/generated/plans/o3_vram_plan_{stamp}.json"
    write_text(plan_path, json.dumps(plan, indent=1, ensure_ascii=False) + "\n")

    # reuso D12: conferir bytes dos headers O2 citados (BG/HUD/paletas)
    reuse_paths = ("inc/o2/pal_bg.h", "inc/o2/pal_spr.h", "inc/o2/bg_tiles.h",
                   "inc/o2/bg_cols.h", "inc/o2/hud_tiles.h")
    o2_by_path = {o["path"]: o for o in env["o2"]["outputs"]}
    reuse = []
    for rel in reuse_paths:
        o = o2_by_path.get(rel)
        if o is None:
            raise SystemExit(f"O2 nao registra {rel} (reuso D12)")
        p = project / rel
        if sha256_file(p) != o["sha256"]:
            raise SystemExit(f"header O2 divergente: {rel}")
        reuse.append({"path": rel, "sha256": o["sha256"],
                      "bytes": p.stat().st_size})
    pal_spr_bytes = bytes([0x3C] + [cram_byte(c) for c in p1_codes]
                          + [0x00] * (15 - len(p1_codes)))
    if c_array("o2_pal_spr", pal_spr_bytes) not in \
            (project / "inc/o2/pal_spr.h").read_text(encoding="utf-8"):
        raise SystemExit("pal_spr.h O2 nao contem a P1 herdada byte a byte")

    # ---- registro -------------------------------------------------------------
    outputs = []
    for name in heads:
        p = inc / name
        outputs.append({"path": str(p.relative_to(project)),
                        "sha256": sha256_file(p), "bytes": p.stat().st_size})
    for p in (bank_bin_path, plan_path):
        outputs.append({"path": str(p.relative_to(project)),
                        "sha256": sha256_file(p), "bytes": p.stat().st_size})
    for p, _m in manifests:
        outputs.append({"path": str(p.relative_to(project)),
                        "sha256": sha256_file(p), "bytes": p.stat().st_size})

    def src_entry(path: Path):
        return {"path": str(path.relative_to(project)),
                "sha256": sha256_file(path), "bytes": path.stat().st_size}

    record = {
        "schema": "openbor_sms_o3_emission_v1",
        "generated_at": generated_at,
        "tool": "tools/sms_wrapper/openbor2sms/openbor2sms/sms_emit.py",
        "scope": ("O3 — emissao de combate (slots duplos, blocos bancados, "
                  "politica de banda, arcs, anim)"),
        "sources": [src_entry(env["scope_path"]), src_entry(env["art_path"]),
                    src_entry(env["ir_paths"]["ax"]),
                    src_entry(env["ir_paths"]["long"]),
                    src_entry(env["o2_path"])],
        "reused_o2": reuse,
        "poses": {"ax": {"count": len(poses["ax"]),
                         "cells_both_sides": cells_both["ax"]},
                  "long": {"count": len(poses["long"]),
                           "cells_both_sides": cells_both["long"]},
                  "total_cells_both_sides": cells_both["ax"] + cells_both["long"],
                  "max_cells": max_cells, "slot_cells": O3_SLOT_CELLS,
                  "blocks_bytes": total_bytes,
                  "pose_index": "frame*2 + lado (0=left, 1=right)"},
        "banks": {"first": O3_BANK_FIRST, "count": O3_BANK_COUNT,
                  "bytes_each": O3_BANK_BYTES,
                  "capacity": O3_BANK_COUNT * O3_BANK_BYTES,
                  "used": total_bytes,
                  "free": O3_BANK_COUNT * O3_BANK_BYTES - total_bytes,
                  "per_bank": {str(b): bank_used.get(b, 0) for b in range(
                      O3_BANK_FIRST, O3_BANK_FIRST + O3_BANK_COUNT)},
                  "bin": {"path": str(bank_bin_path.relative_to(project)),
                          "sha256": sha256_file(bank_bin_path),
                          "bytes": bank_bin_path.stat().st_size}},
        "policy": {
            "id": "D9-a",
            "decision": ("contagem exata por scanline (revisao D9-a2, medida): "
                         "celulas 8x16 em passo de 16 px nao se sobrepoem dentro "
                         "do mesmo ator, entao cada scanline visivel e coberta "
                         "por <=1 linha de cada ator; line_count = "
                         "o3_ax_rows[pose][rp] + ec[row] nas regioes "
                         "sobrepostas; tabela estatica 32x6 (192 B ROM) + 6 "
                         "contadores u8 RAM; inimigo anda a ordem de prioridade "
                         "dens desc"),
            "refuted": {
                "model": "contadores de banda (24 bandas de 8 linhas)",
                "when": ("M4, 2026-10-17, durante a emissao: o caso sintetico "
                         "9-em-linha e o solo declarado fall03/death01 "
                         "divergiram do brute force linha a linha"),
                "measured": ("bandas de 8 linhas conflitam linhas adjacentes "
                             "(o deslocamento relativo entre atores nao e "
                             "multiplo de 8), logo o contador de banda nao e "
                             "a contagem da scanline: no caso declarado "
                             "fall03/death01 solo caem 10 celulas (nao 1) e o "
                             "blast radius e inaceitavel"),
                "verdict": ("bandas refutadas por medicao; politica revisada "
                            "para linhas exatas (D9-a2) sem cascata")},
            "rationale": ("candidato (b) mascara expandida por (pose, bucket "
                          "de z) nao fecha: ambos atores variam z (73x73) e "
                          "pose (32x28) — tabela inviavel; contadores de banda "
                          "nao dao contagem exata (ver refuted); linhas exatas "
                          "custam 192 B ROM + 6 B RAM e ~6 comparacoes/celula"),
            "scan": {"space": ("32 poses ax x 28 poses long x 9 dz x "
                               "3 bases x 2 residuos"),
                     "cases": scan["cases"],
                     "max_line_peak": scan["max_line_peak"],
                     "scenes_with_drops": scan["scenes_with_drops"],
                     "violations": len(scan["violations"])},
            "crosscheck": {"cases": xcheck_cases, "violations": xcheck_bad,
                           "method": ("o3_policy_crosscheck: pico da politica "
                                      "exata vs brute force linha a linha "
                                      "(o3_shadow_lines) no mesmo conjunto "
                                      "incluido")},
            "solo": [{"frame": s["frame"], "side": s["side"],
                      "drops": s["drops"], "peak": s["peak"],
                      "dropped": s["dropped"]}
                     for s in solo if s["drops"]]},
        "arcs": {"method": ("D5 simulado por tick em Python na emissao "
                            "(pos += v*100/gs; v -= g*100/gs; g=0.1; gs=200) "
                            "e amostrado por frame NTSC"),
                 "jump": {"frames": arcs["jump"]["frames"],
                          "apex": arcs["jump"]["apex"],
                          "drift": arcs["jump"]["drift"],
                          "declared": {"frames": 40, "apex": 54, "drift": 66}},
                 "toss": {"frames": arcs["toss"]["frames"],
                          "apex": arcs["toss"]["apex"],
                          "drift": arcs["toss"]["drift"],
                          "declared": {"frames": 36, "apex": 46, "drift": 72}},
                 "entry": {"frames": arcs["entry"]["frames"], "declared": 27,
                           "note": ("divergencia declarada: D5 diz ~27 frames; "
                                    "com a mesma integracao do pulo simula "
                                    f"{arcs['entry']['frames']} (cap "
                                    "maxfallspeed a pinar no M5)")}},
        "anim": {actor: [{"id": e["id"], "name": e["name"],
                          "frames": e["frames"],
                          "frame_names": e["frame_names"],
                          "loop": e["loop"], "land": e["land"],
                          "dropped_source_frames": e["dropped_source_frames"]}
                         for e in anim_plan[actor]]
                 for actor in ("ax", "long")},
        "attacks": attacks,
        "vram": {"sprite_slots": [0, O3_SPR_TILES - 1],
                 "sprite_tiles": O3_SPR_TILES, "bg_base": O3_BG_BASE,
                 "bg_slots": O3_BG_TILES, "hud_base": O3_HUD_BASE,
                 "hud_slots": O3_HUD_TILES,
                 "total": O3_SPR_TILES + O3_BG_TILES + O3_HUD_TILES,
                 "budget": VRAM_TILES,
                 "margin": VRAM_TILES - (O3_SPR_TILES + O3_BG_TILES + O3_HUD_TILES),
                 "plan": {"path": str(plan_path.relative_to(project)),
                          "sha256": sha256_file(plan_path)}},
        "manifests": [{"path": str(p.relative_to(project)),
                       "sha256": sha256_file(p),
                       "scene_kind": m["scene"]["kind"],
                       "peak_per_line": m["simulation"]["peak_per_line"],
                       "pre_policy_peak": m["simulation"]["pre_policy_peak"],
                       "drops": m["simulation"]["drops"],
                       "sat_entries": m["simulation"]["sat_entries"]}
                      for p, m in manifests],
        "checks": {
            "art_sha_bound": len(art["outputs"]),
            "ir_source_sha_bound": 2,
            "o2_reuse_sha_bound": len(reuse),
            "pal_p1_byte_identical_o2": True,
            "cells_match_m3_and_scope": True,
            "policy_crosscheck_cases": xcheck_cases,
            "policy_crosscheck_violations": xcheck_bad,
            "policy_scan_cases": scan["cases"],
            "policy_scan_violations": 0,
            "solo_declared_drops": {f"{s['frame']}_{s['side']}": s["drops"]
                                    for s in solo_declared},
            "player_row_peak_cells": max_row["ax"],
            "long_rows_over_8": long_over,
            "banks_fit": True,
            "vram_total_vs_budget": [O3_SPR_TILES + O3_BG_TILES + O3_HUD_TILES,
                                     VRAM_TILES]},
        "outputs": outputs,
        "notes": [
            "blocos por pose empacotados na ordem da tabela (jogador varredura; inimigo dens desc)",
            "upload = copia linear banco->slot (bloco = count*64 bytes; maximo 29x64=1856)",
            "slots duplos por ator: A/B (double buffer com 'pose ready' no M5)",
            "corte do inimigo = politica D9-a revisada (linhas exatas, D9-a2); x nao entra na decisao (licao O2)",
            "walk da fonte tem 4 quadros; pose set usa walk01/walk03 (walk02/04 omitidos por escopo)",
            "ax anim attack2 (movimento, th101-103) fora do recorte O3; declarar na revisao de escopo (M8)",
            "solo fall03/death01: 9 celulas na mesma linha do canvas -> a 9a cai (drop declarado; contagem por linha, nao por banda)",
            "tabelas O3 cabem nos 32 KB com o codigo (O2 free_bytes = 12853; tabelas ~6 KB)"],
        "open_items": [
            "ordem de sacrificio fina (dens desc) pendente de revisao artistica",
            "entry drop: 38 frames simulados vs ~27 declarados (maxfallspeed a pinar no M5)",
            "gate temporal (audit_sprite_line_sim) roda sobre os manifests deste registro",
            "measure_vram_map com vdp_regs de sessao: M5 (so plan-mode agora)"],
    }
    rec_path = project / f"data/generated/emit/o3_emission_{stamp}.json"
    write_text(rec_path, json.dumps(record, indent=1, ensure_ascii=False) + "\n")
    return rec_path, record


def self_check_o3() -> bool:
    ok = True
    # politica D9-a2: solo 9-em-linha -> exatamente 1 drop e pico 8
    line = [{"row": 4, "col": c, "dens": 9 - c} for c in range(9)]
    ec, drops, peak = o3_compose_rows({}, line, -80, -72, 152, 152)
    ok &= len(drops) == 1 and peak == 8 and max(ec.values()) == 8
    # jogador 8 na linha sobreposta + inimigo 1 -> 1 drop (contagem exata)
    ax_row = {2: 8}
    enemy_one = [{"row": 1, "col": 0, "dens": 5}]
    ec, drops, peak = o3_compose_rows(ax_row, enemy_one, -80, -72, 152, 152)
    ok &= len(drops) == 1 and peak == 8
    # linha do inimigo sem sobreposicao visivel com o jogador -> sem drop
    ec, drops, peak = o3_compose_rows({0: 8}, enemy_one, -80, -72, 152, 152)
    ok &= not drops and peak == 8
    # brute force independente concorda com a politica (pico identico)
    cases, bad = o3_policy_crosscheck([
        ({}, line, -80, -72, 152, 152),
        ({2: 8}, enemy_one, -80, -72, 152, 152),
        ({0: 8}, enemy_one, -80, -72, 152, 152),
        ({1: 5, 2: 5, 3: 5}, [{"row": i % 6, "col": i, "dens": 1}
                              for i in range(7)], -80, -72, 176, 152)])
    ok &= cases == 4 and bad == 0
    jy, jx, _jt = o3_sim_arc(3.3, 1.0)
    ty, tx, _tt = o3_sim_arc(3.0, 1.2)
    ok &= 39 <= len(jy) - 1 <= 41 and 53 <= max(jy) <= 56
    ok &= 64 <= jx[-1] <= 68
    ok &= 35 <= len(ty) - 1 <= 37 and 44 <= max(ty) <= 47
    ok &= 70 <= tx[-1] <= 74
    ey, _et = o3_sim_fall(200)
    ok &= ey[0] == 200 and ey[-1] == 0 and 36 <= len(ey) - 1 <= 40
    m = o3_pack_banks([1856] * 40)
    ok &= len(m) == 40 and all(b >= 2 for b, _ in m)
    try:
        o3_pack_banks([O3_BANK_BYTES + 1])
        ok = False
    except SystemExit:
        pass
    return ok


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
    ok &= self_check_o3()
    if not ok:
        print("[SELF-CHECK FAIL] sms_emit", file=sys.stderr)
        return 1
    print("[SELF-CHECK OK] sms_emit")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="OpenBOR -> pacote C da ROM (O2/O3)")
    ap.add_argument("--project", help="raiz do projeto SMSForge alvo")
    ap.add_argument("--generated-at", default=None)
    ap.add_argument("--scope", choices=("o2", "o3"), default="o2",
                    help="lote de emissao (o2 = piloto, o3 = combate)")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)
    if args.self_check:
        return self_check()
    if not args.project:
        ap.error("--project e obrigatorio")
    project = Path(args.project).resolve()
    generated_at = args.generated_at or datetime.now(timezone.utc).replace(
        microsecond=0).isoformat()
    if args.scope == "o3":
        rec_path, record = emit_o3(project, generated_at)
        pos, banks, vram = record["poses"], record["banks"], record["vram"]
        pol = record["policy"]["scan"]
        print(f"[sms_emit] O3 poses: ax {pos['ax']['count']} / long "
              f"{pos['long']['count']} lados | {pos['total_cells_both_sides']} "
              f"celulas | blocos {pos['blocks_bytes']} B em "
              f"{banks['used']}/{banks['capacity']} (bancos {banks['first']}.."
              f"{banks['first'] + banks['count'] - 1})")
        print(f"[sms_emit] O3 politica D9-a: {pol['cases']} casos de varredura, "
              f"pico {pol['max_line_peak']}/limiar {O3_PER_LINE}, "
              f"{pol['violations']} violacoes | VRAM {vram['total']}/{vram['budget']}")
        print(f"[sms_emit] O3 manifests: {len(record['manifests'])} | registro: "
              f"{rec_path.relative_to(project)}")
        return 0
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
