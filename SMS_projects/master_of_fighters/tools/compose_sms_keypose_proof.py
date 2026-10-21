#!/usr/bin/env python3
"""Compose an SMS proof board with exactly one idle and one action key pose.

The art previews are source-exact, nearest-neighbor renders. Tile occupancy
grids are drawn in separate panels and never on top of character pixels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


KEYS = {
    "magenta": (255, 0, 255),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
}
PAPER = (246, 244, 238)
CARD = (255, 254, 250)
PALE = (239, 236, 226)
NAVY = (9, 13, 68)
INK = (42, 47, 58)
MUTED = (100, 107, 116)
LINE = (204, 201, 192)
ACCENT = (0, 112, 139)
ALERT = (161, 49, 35)
GOOD = (25, 115, 81)
RGB6 = {0, 85, 170, 255}

ANIMATION_PRINCIPLES = [
    ("squash_stretch", "Squash and Stretch", "Aperto e estiramento", "Preservar volume e massa; deformar só quando a ação justificar."),
    ("anticipation", "Anticipation", "Antecipação", "A pose anterior prepara a ação e deixa sua intenção legível."),
    ("staging", "Staging", "Encenação", "Silhueta, foco e trajetória da arma comunicam uma ação por vez."),
    ("straight_ahead_pose_to_pose", "Straight Ahead / Pose to Pose", "Ação direta / pose a pose", "Declarar o método; definir poses-chave antes dos intervalos quando usar pose a pose."),
    ("follow_through_overlap", "Follow Through / Overlapping Action", "Ação seguinte / sobreposição", "Casaco, cravat e cabelo acompanham o tronco com atraso controlado."),
    ("slow_in_slow_out", "Slow In / Slow Out", "Entrada / saída lenta", "Distribuir quadros e holds para acelerar e desacelerar a ação."),
    ("arcs", "Arcs", "Arcos", "Ombro, cotovelo, punho e arma percorrem trajetórias coerentes."),
    ("secondary_action", "Secondary Action", "Ação secundária", "Gestos e roupa apoiam a ação principal sem competir com ela."),
    ("timing", "Timing", "Temporização", "Declarar duração em frames e holds para cada trecho da ação."),
    ("exaggeration", "Exaggeration", "Exagero", "Acentuar a leitura sem quebrar anatomia, identidade ou volume."),
    ("solid_drawing", "Solid Drawing", "Desenho sólido", "Manter volume, perspectiva, articulações e encaixes de arma em todos os quadros."),
    ("appeal", "Appeal", "Apelo", "Preservar a virtude, coragem e identidade marcante de Dr. Social."),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def resolve(root: Path, raw: str) -> Path:
    path = Path(raw)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/usr/share/fonts/noto/NotoSans-Bold.ttf" if bold else "/usr/share/fonts/noto/NotoSans-Regular.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def measure(image: Image.Image, transparent: int, tile: int = 8) -> dict[str, Any]:
    pixels = image.load()
    occupied: list[list[int]] = []
    patterns: set[bytes] = set()
    for ty in range(image.height // tile):
        for tx in range(image.width // tile):
            pattern = bytes(
                0 if pixels[tx * tile + dx, ty * tile + dy] == transparent
                else pixels[tx * tile + dx, ty * tile + dy]
                for dy in range(tile) for dx in range(tile)
            )
            if any(pattern):
                occupied.append([tx, ty])
                patterns.add(pattern)
    remaining = {
        (x, y) for y in range(image.height) for x in range(image.width)
        if pixels[x, y] != transparent
    }
    component_sizes: list[int] = []
    while remaining:
        stack = [remaining.pop()]
        size = 0
        while stack:
            x, y = stack.pop()
            size += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    point = (x + dx, y + dy)
                    if (dx or dy) and point in remaining:
                        remaining.remove(point)
                        stack.append(point)
        component_sizes.append(size)
    bbox = image.convert("RGBA").getchannel("A").getbbox()
    edge_clearance = (
        [bbox[0], bbox[1], image.width - bbox[2], image.height - bbox[3]]
        if bbox else [0, 0, 0, 0]
    )
    return {
        "bbox_xyxy_exclusive": list(bbox) if bbox else None,
        "bbox_px": [bbox[2] - bbox[0], bbox[3] - bbox[1]] if bbox else [0, 0],
        "empty_border_px_left_top_right_bottom": edge_clearance,
        "occupied_tile_cells": len(occupied),
        "unique_tile_patterns": len(patterns),
        "occupied_tile_coordinates_xy": occupied,
        "raw_4bpp_bytes_for_unique_patterns": len(patterns) * 32,
        "opaque_component_count_8_connected": len(component_sizes),
        "opaque_component_sizes_px_desc": sorted(component_sizes, reverse=True),
        "patterns": patterns,
    }


def choose_key(palette: list[tuple[int, int, int]]) -> tuple[str, tuple[int, int, int]]:
    scored = []
    for name, key in KEYS.items():
        distances = [math.sqrt(sum((c[i] - key[i]) ** 2 for i in range(3))) for c in palette]
        scored.append((sum(distances) / len(distances) if distances else 0,
                       min(distances) if distances else 0, key not in palette, name, key))
    _, _, _, name, key = max(scored)
    return name, key


def add_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, size: int,
             color: tuple[int, int, int] = INK, bold: bool = False) -> None:
    draw.text(xy, value, font=font(size, bold), fill=color)


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill=CARD,
         outline=LINE, radius: int = 24, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def crop_frame(sheet: Image.Image, index: int, fw: int, fh: int, columns: int) -> Image.Image:
    col, row = index % columns, index // columns
    frame = sheet.crop((col * fw, row * fh, (col + 1) * fw, (row + 1) * fh))
    frame.info["transparency"] = sheet.info.get("transparency", 0)
    return frame


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--concept", required=True)
    parser.add_argument("--source-contract", required=True)
    parser.add_argument("--palette-manifest", default="doc/palettes_manifest.json")
    parser.add_argument("--palette-runtime-contract", default="doc/palette_runtime_contract_v1.json")
    parser.add_argument("--palette-character-key", default="dr_ferdinand_social")
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--idle-frame-index", type=int, default=0)
    parser.add_argument("--action-frame-index", type=int, default=5)
    parser.add_argument("--frame-width", type=int, default=96)
    parser.add_argument("--frame-height", type=int, default=96)
    parser.add_argument("--scale-numerator", type=int, default=1)
    parser.add_argument("--scale-denominator", type=int, default=1)
    parser.add_argument("--revision", default="v2")
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--target-low", type=int, default=66)
    parser.add_argument("--target-high", type=int, default=72)
    parser.add_argument("--target-center", type=int, default=70)
    args = parser.parse_args()

    if args.scale_numerator < 1 or args.scale_denominator < 1:
        parser.error("scale numerator/denominator must be positive integers")
    scaled_w = args.frame_width * args.scale_numerator
    scaled_h = args.frame_height * args.scale_numerator
    if scaled_w % args.scale_denominator or scaled_h % args.scale_denominator:
        parser.error("source cell dimensions must scale to exact integer output dimensions")
    out_width = scaled_w // args.scale_denominator
    out_height = scaled_h // args.scale_denominator
    if out_width % 8 or out_height % 8:
        parser.error("converted pose canvas dimensions must remain tile-aligned multiples of 8")
    if not args.revision.isalnum():
        parser.error("revision must contain only letters and digits")

    project = Path(__file__).resolve().parents[1]
    source_path = resolve(project, args.source)
    concept_path = resolve(project, args.concept)
    contract_path = resolve(project, args.source_contract)
    palette_manifest_path = resolve(project, args.palette_manifest)
    palette_runtime_path = resolve(project, args.palette_runtime_contract)
    output_path = resolve(project, args.output)
    report_path = resolve(project, args.report)
    for path in (source_path, concept_path, contract_path, palette_manifest_path, palette_runtime_path):
        if not path.is_file():
            parser.error(f"required input missing: {path}")
    sheet = Image.open(source_path)
    if sheet.mode != "P":
        parser.error("source sheet must be indexed mode P")
    if sheet.size != (args.frame_width * args.columns, args.frame_height * args.rows):
        parser.error("source dimensions do not match the declared frame grid")
    total_frames = args.columns * args.rows
    indices = (args.idle_frame_index, args.action_frame_index)
    if indices[0] == indices[1] or any(i < 0 or i >= total_frames for i in indices):
        parser.error("idle/action must select two distinct frames inside the source grid")

    source_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    palette_manifest = json.loads(palette_manifest_path.read_text(encoding="utf-8"))
    palette_runtime_contract = json.loads(palette_runtime_path.read_text(encoding="utf-8"))
    palette_character = palette_manifest["characters"][args.palette_character_key]
    role_by_rgb = {tuple(entry["rgb"]): entry["role"] for entry in palette_character.get("colors", [])}
    transparent = int(source_contract.get("palette", {}).get("transparent_index", 0))
    palette_raw = sheet.getpalette() or []
    used_indices = set(sheet.get_flattened_data()) - {transparent}
    palette_rgb = [tuple(palette_raw[i * 3:i * 3 + 3]) for i in sorted(used_indices)]
    roster_rgb = {
        tuple(color["rgb"])
        for character in palette_manifest.get("characters", {}).values()
        for color in character.get("colors", [])
        if color.get("index") != transparent
    }
    key_name, key_rgb = choose_key(palette_rgb)
    if key_rgb in palette_rgb:
        parser.error("no allowed pure background key avoids collision with source colors")

    base_dir = output_path.parent / f"poses_{args.revision}"
    base_dir.mkdir(parents=True, exist_ok=True)
    pose_specs = [
        {"role": "idle", "frame_index": args.idle_frame_index,
         "label": "POSE A · IDLE / GUARDA NEUTRA",
         "description": "Postura pronta e equilibrada; bengala apoiada, identidade visual preservada."},
        {"role": "action", "frame_index": args.action_frame_index,
         "label": "POSE B · AÇÃO / BENGALA COM TERMINAL ARREDONDADO",
         "description": f"Frame-fonte {args.action_frame_index + 1:02d}: forma redonda legível; bengala inteira dentro da célula."},
    ]
    poses: list[dict[str, Any]] = []
    metrics_by_role: dict[str, dict[str, Any]] = {}
    pattern_union: set[bytes] = set()
    for spec in pose_specs:
        source_frame = crop_frame(sheet, spec["frame_index"], args.frame_width, args.frame_height, args.columns)
        if (args.scale_numerator, args.scale_denominator) == (1, 1):
            frame = source_frame
            transform_method = "identity"
        else:
            frame = source_frame.resize((out_width, out_height), Image.Resampling.NEAREST)
            frame.info["transparency"] = source_frame.info.get("transparency", 0)
            transform_method = "nearest_neighbor"
        pose_path = base_dir / f"dr_social_{spec['role']}_keypose_{args.revision}.png"
        frame.save(pose_path, format="PNG", optimize=True, transparency=transparent)
        met = measure(frame, transparent)
        min_border = min(met["empty_border_px_left_top_right_bottom"])
        if min_border < 1:
            parser.error(f"{spec['role']} content touches the frame edge; choose an intact pose/canvas")
        pattern_union.update(met.pop("patterns"))
        metrics_by_role[spec["role"]] = met
        poses.append({
            **spec,
            "source_path": str(pose_path.relative_to(project)),
            "source_sha256": sha256(pose_path),
            "canvas_px": [out_width, out_height],
            "transparent_index": transparent,
            "inspection_background_rgb": list(key_rgb),
            "source_parent_sheet": str(source_path.relative_to(project)),
            "source_parent_sha256": sha256(source_path),
            "source_frame_index_zero_based": spec["frame_index"],
            "source_parent_grid": {
                "columns": args.columns,
                "rows": args.rows,
                "frame_px": [args.frame_width, args.frame_height],
            },
            "source_transform": {
                "method": transform_method,
                "scale_ratio_numerator_denominator": [args.scale_numerator, args.scale_denominator],
                "input_px": [args.frame_width, args.frame_height],
                "output_px": [out_width, out_height],
                "resampling": "Pillow Image.Resampling.NEAREST" if transform_method == "nearest_neighbor" else "none",
            },
            "sprite_preview": {},
            "native_preview": {},
        })

    W, H = 3200, 1900
    page = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(page)
    add_text(draw, (70, 44), "PROVA TÉCNICA DE ASSET · MASTER SYSTEM", 54, NAVY, True)
    add_text(draw, (75, 116), "DR. FERDINAND SOCIAL  ·  DUAS POSES-CHAVE  ·  NÃO É SPRITE SHEET DE ANIMAÇÃO", 29, ACCENT, True)
    add_text(draw, (75, 163), f"Fatal Fury Special · Game Gear 160×144 → SMS 256×192 · altura-alvo de combate {args.target_low}–{args.target_high} px · amostra candidata", 23, MUTED)
    card(draw, (2500, 50, 3125, 152), fill=PALE)
    add_text(draw, (2540, 72), "CANDIDATO TÉCNICO", 25, NAVY, True)
    add_text(draw, (2540, 110), "review / runtime pending", 21, ALERT)

    card_boxes = [(65, 225, 1570, 1120), (1630, 225, 3135, 1120)]
    preview_scale = 6
    stage_width = out_width * preview_scale
    stage_height = out_height * preview_scale
    for pose, box in zip(poses, card_boxes):
        x0, y0, x1, y1 = box
        spec = pose
        role = spec["role"]
        frame = Image.open(project / spec["source_path"])
        metrics = metrics_by_role[role]
        card(draw, box)
        add_text(draw, (x0 + 32, y0 + 26), spec["label"], 31, NAVY, True)
        add_text(draw, (x0 + 32, y0 + 72), spec["description"], 19, MUTED)

        # The large source preview is an exact nearest-neighbor crop; no ruler,
        # grid, label, or border is drawn inside this rectangle.
        sprite_x, sprite_y = x0 + 45, y0 + 140
        rgba = frame.convert("RGBA")
        backdrop = Image.new("RGBA", frame.size, (*key_rgb, 255))
        backdrop.alpha_composite(rgba)
        zoom = backdrop.convert("RGB").resize((stage_width, stage_height), Image.Resampling.NEAREST)
        page.paste(zoom, (sprite_x, sprite_y))
        draw.rectangle((sprite_x - 2, sprite_y - 2, sprite_x + stage_width + 1, sprite_y + stage_height + 1), outline=NAVY, width=2)
        pose["sprite_preview"] = {"x": sprite_x, "y": sprite_y, "scale": preview_scale}
        add_text(draw, (sprite_x, sprite_y + stage_height + 12), f"{out_width}×{out_height} px · escala fonte {args.scale_numerator}/{args.scale_denominator} · zoom {preview_scale}× nearest", 17, MUTED)
        add_text(draw, (sprite_x, sprite_y + stage_height + 39), "Bengala íntegra · terminal redondo · borda vazia ≥1 px · mapa fora do sprite", 17, MUTED)

        native_x, native_y = x0 + 590, y0 + 170
        native_rgba = Image.new("RGBA", frame.size, (*key_rgb, 255))
        native_rgba.alpha_composite(rgba)
        page.paste(native_rgba.convert("RGB"), (native_x, native_y))
        pose["native_preview"] = {"x": native_x, "y": native_y}
        add_text(draw, (native_x, native_y - 30), "NATIVO 1×", 18, NAVY, True)

        map_x, map_y, cell = x0 + 775, y0 + 225, 22
        add_text(draw, (map_x, map_y - 38), "MAPA DE OCUPAÇÃO 8×8 · SEPARADO", 18, NAVY, True)
        occupied = {tuple(point) for point in metrics["occupied_tile_coordinates_xy"]}
        for ty in range(out_height // 8):
            for tx in range(out_width // 8):
                rx, ry = map_x + tx * cell, map_y + ty * cell
                fill = NAVY if (tx, ty) in occupied else key_rgb
                outline = (240, 240, 236) if (tx, ty) in occupied else (0, 126, 0)
                draw.rectangle((rx, ry, rx + cell - 1, ry + cell - 1), fill=fill, outline=outline, width=1)
        tile_total = (out_width // 8) * (out_height // 8)
        add_text(draw, (map_x, map_y + 236), f"{metrics['occupied_tile_cells']} células ocupadas / {tile_total}", 17, INK)
        add_text(draw, (map_x, map_y + 265), f"{metrics['unique_tile_patterns']} padrões únicos", 17, INK)
        add_text(draw, (map_x, map_y + 294), f"{metrics['raw_4bpp_bytes_for_unique_patterns']:,} bytes 4bpp", 17, INK)

        info_x = x0 + 1110
        add_text(draw, (info_x, y0 + 175), "CONVERSÃO MEDIDA", 19, ACCENT, True)
        add_text(draw, (info_x, y0 + 220), f"Canvas {out_width}×{out_height} px · {out_width // 8}×{out_height // 8} tiles", 20, NAVY, True)
        add_text(draw, (info_x, y0 + 260), f"BBox opaca {metrics['bbox_px'][0]}×{metrics['bbox_px'][1]} px", 18, INK)
        visible_h = metrics["bbox_px"][1]
        margins = metrics["empty_border_px_left_top_right_bottom"]
        if role == "idle":
            height_note = f"BBox total {visible_h}px incl. bengala · corpo {args.target_low}–{args.target_high}px: pending"
        else:
            height_note = f"BBox total {visible_h}px incl. item · ação varia com pose"
        add_text(draw, (info_x, y0 + 295), height_note, 17, INK)
        add_text(draw, (info_x, y0 + 324), f"Margem vazia L/T/R/B: {margins[0]}/{margins[1]}/{margins[2]}/{margins[3]} px", 14, GOOD)
        add_text(draw, (info_x, y0 + 348), "Paleta SMS", 19, ACCENT, True)
        add_text(draw, (info_x, y0 + 386), f"{len(used_indices)} cores úteis · RGB 6-bit", 18, INK)
        add_text(draw, (info_x, y0 + 420), f"Fundo de inspeção {key_name} #{key_rgb[0]:02X}{key_rgb[1]:02X}{key_rgb[2]:02X}", 16, MUTED)
        add_text(draw, (info_x, y0 + 485), "Hardware desta pose", 19, ACCENT, True)
        add_text(draw, (info_x, y0 + 524), f"Padrões únicos: {metrics['unique_tile_patterns']} / janela sprite 256", 17, INK)
        add_text(draw, (info_x, y0 + 558), "SAT/scanline e carga VRAM: pending", 17, ALERT)
        add_text(draw, (info_x, y0 + 592), "O mapa não representa objetos SAT.", 16, MUTED)
        add_text(draw, (info_x, y0 + 655), f"Fonte: frame {spec['frame_index'] + 1:02d} do estudo v9 · pose estática", 15, MUTED)

    # Hardware and promotion contract.
    card(draw, (65, 1160, 3135, 1610), fill=(250, 249, 244))
    add_text(draw, (95, 1188), "LIMITES FÍSICOS SMS · O QUE ESTA PROVA MEDE E O QUE AINDA BLOQUEIA", 24, NAVY, True)
    draw.line((2050, 1220, 2050, 1580), fill=LINE, width=2)
    hw_lines = [
        "256×192 · VRAM 16 KB = 512 padrões 8×8 de 32 B · janela endereçável de sprites: 256 padrões por seleção da base",
        "SAT: até 64 objetos · até 8 sprites por scanline · cada objeto 8 px de largura e 8 ou 16 px de altura",
        "CRAM: 32 entradas em BG P0 (16) + Sprite P1 (16); cores SMS RGB de 2 bits por canal.",
        "Sprite P1 é uma tabela compartilhada por todos os sprites: P1, P2, projéteis e efeitos usam os mesmos índices.",
        "Sprite P1: índice 0 transparente; índices 1–15 são as cores comuns de combate. Não há uma CRAM independente por personagem.",
        "BG/HUD usam P0; BG índice 0 sempre mostra cor (P0 ou P1). Transparência do índice 0 vale só para pixels de sprite; tiles podem selecionar P1.",
        f"Estudo-fonte Dr. Social: {len(used_indices)} cores úteis; {len(palette_manifest.get('characters', {}))} perfis do roster somam {len(roster_rgb)} RGBs distintos. Mapeamento comum P1: pending.",
        "RAM 8 KB · ROM linear sem mapper 48 KB · sem DMA · upload de paletas no VBlank exige medição da rotina.",
        "Teto de quadros por sheet NÃO é uma constante física; definir por pools VRAM/RAM, ROM/banking e carga VBlank no TDD.",
        f"Par idle+ação desta prova: {len(pattern_union)} padrões únicos exatos em 4bpp · não inclui BG/HUD/outros estados e não é alocação residente.",
    ]
    yy = 1225
    for i, line in enumerate(hw_lines):
        alert_line = i == 6
        add_text(draw, (100, yy + i * 34), line, 17, ALERT if alert_line else INK, alert_line)
    add_text(draw, (2080, 1227), f"PALETA DO ESTUDO-FONTE · {len(used_indices)} CORES ÚTEIS", 17, ACCENT, True)
    add_text(draw, (2080, 1252), "Não é paleta CRAM exclusiva do personagem.", 15, ALERT)
    palette_for_board = [{"index": 0, "rgb": list(key_rgb), "role": "transparente"}]
    palette_for_board += [
        {"index": index, "rgb": list(palette_raw[index * 3:index * 3 + 3]),
         "role": role_by_rgb.get(tuple(palette_raw[index * 3:index * 3 + 3]), "unmapped_rgb")}
        for index in sorted(used_indices)
    ]
    swatch_w = 142
    for i, entry in enumerate(palette_for_board):
        row, col = divmod(i, 7)
        sx, sy = 2080 + col * swatch_w, 1290 + row * 128
        rgb = tuple(entry["rgb"])
        draw.rectangle((sx, sy, sx + 50, sy + 42), fill=rgb, outline=NAVY, width=2)
        if entry["index"] == 0:
            draw.line((sx, sy, sx + 50, sy + 42), fill=NAVY, width=2)
            draw.line((sx + 50, sy, sx, sy + 42), fill=NAVY, width=2)
        add_text(draw, (sx + 57, sy + 1), f"{entry['index']:02d}", 14, NAVY, True)
        add_text(draw, (sx, sy + 49), "#%02X%02X%02X" % rgb, 13, INK)
        add_text(draw, (sx, sy + 76), entry["role"], 12, MUTED)

    card(draw, (65, 1640, 1210, 1860), fill=CARD)
    card(draw, (1235, 1640, 2220, 1860), fill=CARD)
    card(draw, (2245, 1640, 3135, 1860), fill=CARD)
    add_text(draw, (90, 1662), "REVISÃO VISUAL", 18, NAVY, True)
    cleanup = source_contract.get("pixel_cleanup_profile", {})
    min_component = cleanup.get("minimum_opaque_component_px", 2)
    tiny_components = sum(
        sum(size < min_component for size in metrics_by_role[role]["opaque_component_sizes_px_desc"])
        for role in ("idle", "action")
    )
    add_text(draw, (90, 1701), f"Ilhas opacas <{min_component}px: {tiny_components} · conectividade 8", 16, GOOD if not tiny_components else ALERT)
    add_text(draw, (90, 1732), "Cores por material, anatomia e concept: pending / revisor independente", 15, ALERT)
    add_text(draw, (1260, 1662), "ANIMAÇÃO", 18, NAVY, True)
    add_text(draw, (1260, 1701), "12 princípios listados e vinculados no JSON.", 16, INK)
    add_text(draw, (1260, 1732), "Duas poses não validam timing nem ciclo completo.", 16, ALERT)
    add_text(draw, (2270, 1662), "PROMOÇÃO", 18, NAVY, True)
    add_text(draw, (2270, 1701), "Sem aprovação para res/ ou ROM.", 16, ALERT)
    add_text(draw, (2270, 1732), "AAA é meta de qualidade, não veredito automático.", 16, INK)

    page.save(output_path, format="PNG", optimize=True)

    palette = sheet.getpalette() or []
    used_palette = []
    color_counts = Counter(sheet.get_flattened_data())
    for index in sorted(used_indices):
        rgb = palette[index * 3:index * 3 + 3]
        used_palette.append({
            "index": index,
            "rgb": rgb,
            "hex": "#{:02X}{:02X}{:02X}".format(*rgb),
            "pixel_count_in_parent_sheet": int(color_counts[index]),
            "role": role_by_rgb.get(tuple(rgb), "unmapped_rgb"),
        })
    report: dict[str, Any] = {
        "schema": "smsforge.keypose_proof_sheet.v4",
        "status": "technical_candidate_visual_and_runtime_review_pending",
        "asset": {
            "asset_id": f"dr_social_sms_keypose_proof_{args.revision}",
            "display_name": "Dr. Ferdinand Social",
            "project": "master_of_fighters",
            "stage": "conversion proof; two reference poses only",
            "source_study_status": source_contract.get("approval_scope", "not_declared"),
            "not_a_sprite_sheet": True,
        },
        "references": {
            "approved_concept_path": str(concept_path.relative_to(project)),
            "approved_concept_sha256": sha256(concept_path),
            "source_parent_sheet_path": str(source_path.relative_to(project)),
            "source_parent_sheet_sha256": sha256(source_path),
            "source_contract_path": str(contract_path.relative_to(project)),
            "source_contract_sha256": sha256(contract_path),
            "palette_manifest_path": str(palette_manifest_path.relative_to(project)),
            "palette_manifest_sha256": sha256(palette_manifest_path),
            "palette_runtime_contract_path": str(palette_runtime_path.relative_to(project)),
            "palette_runtime_contract_sha256": sha256(palette_runtime_path),
        },
        "poses": poses,
        "framing_contract": {
            "minimum_empty_border_px": 1,
            "fail_if_opaque_content_touches_canvas_edge": True,
            "weapon_and_equipment_are_inside_the_declared_pose_canvas": True,
            "canvas_dimensions_must_be_multiples_of_8": True,
        },
        "measured": {
            "poses": metrics_by_role,
            "selected_pair_unique_patterns": len(pattern_union),
            "selected_pair_raw_4bpp_bytes_if_all_unique_patterns_loaded": len(pattern_union) * 32,
            "measurement_scope": "exact indexed 8x8 patterns after declared nearest-neighbor conversion; no flip deduplication; art inventory only",
        },
        "resolution_and_scale": {
            "source_canvas_px": [args.frame_width, args.frame_height],
            "canvas_px_per_pose": [out_width, out_height],
            "tile_px": [8, 8],
            "gdd_visible_height_range_px": [args.target_low, args.target_high],
            "project_target_center_px": args.target_center,
            "height_measurement_scope": "opaque bboxes include handheld equipment; compare the GDD standing height range against anatomy crown-to-sole excluding held equipment; action pose height varies with pose",
            "benchmark": {
                "game": "Fatal Fury Special",
                "platform": "Game Gear",
                "screenshot_source": "https://www.mobygames.com/game/10591/fatal-fury-special/screenshots/game-gear/66969/",
                "gameplay_image_gallery": "https://www.gamestar.de/galerien/fatal_fury_special_game_gear,46053.html",
                "reference_screenshot_resolution_px": [160, 144],
                "sms_viewport_px": [256, 192],
                "standing_character_height_estimate_in_reference_px": 53,
                "projected_sms_height_px": 71,
                "working_target_px": [args.target_low, args.target_high],
                "method": "manual screenshot proportion estimate, multiplied by SMS/Game Gear viewport height ratio; game depth/pose scaling means this is a project reference, not a hardware law",
            },
            "gdd_scale_status_by_pose": {
                "idle": "standing_pose_reference; total_bbox_includes_cane; anatomy_only_height_measurement_pending",
                "action": "pose_dependent_action_bbox_includes_equipment; anatomy_only_height_measurement_pending",
            },
            "bbox_note": "bbox includes handheld weapon; no opaque pixel reaches the canvas edge",
            "minimum_empty_border_px": 1,
            "ground_pivot_px": [
                source_contract.get("sheet", {}).get("ground_pivot_px", [48, 86])[0] * args.scale_numerator // args.scale_denominator,
                source_contract.get("sheet", {}).get("ground_pivot_px", [48, 86])[1] * args.scale_numerator // args.scale_denominator,
            ],
        },
        "palette": {
            "transparent_index": transparent,
            "useful_color_limit_per_sprite_subpalette": 15,
            "useful_colors_in_parent_sheet": len(used_indices),
            "source_palette_scope": "character color study only; not a standalone runtime CRAM allocation",
            "runtime_palette_policy_ref": str(palette_runtime_path.relative_to(project)),
            "runtime_sprite_palette_assignment": "one shared sprite CRAM table for the complete active roster and effects",
            "runtime_sprite_palette_mapping_status": "pending_roster_wide_mapping_to_15_useful_colors",
            "roster_palette_source_manifest_count": len(palette_manifest.get("characters", {})),
            "roster_distinct_source_rgb_count": len(roster_rgb),
            "used_palette_indices_and_rgb": used_palette,
            "palette_character_key": args.palette_character_key,
            "sms_rgb6_grid_pass": all(channel in RGB6 for row in used_palette for channel in row["rgb"]),
            "alpha_binary_pass": set(sheet.convert("RGBA").getchannel("A").get_flattened_data()) <= {0, 255},
            "inspection_background_name": key_name,
            "inspection_background_rgb": list(key_rgb),
            "inspection_background_is_not_asset_color": key_rgb not in palette_rgb,
        },
        "sms_hardware": {
            "visible_canvas_px": [256, 192],
            "vram_bytes": 16384,
            "pattern_px": [8, 8],
            "pattern_bytes_4bpp": 32,
            "pattern_slots_total": 512,
            "sprite_pattern_window_slots": 256,
            "sat_entries_max": 64,
            "sprites_per_scanline_max": 8,
            "sprite_width_px": 8,
            "sprite_height_options_px": [8, 16],
            "cram_subpalettes": 2,
            "cram_entries_per_subpalette": 16,
            "cram_assignment": {
                "background_palette": "P0; stage and HUD; entry 0 reserved as visible backdrop color",
                "sprite_palette": "P1; one shared palette for all hardware sprites",
                "sprite_palette_index_0": "transparent for sprite pixels",
                "background_tiles_may_select_sprite_palette": True,
                "background_palette_select_define": "TILE_USE_SPRITE_PALETTE",
            },
            "transparent_index": 0,
            "useful_colors_per_subpalette_max": 15,
            "useful_colors_simultaneous_max": 30,
            "ram_bytes": 8192,
            "rom_no_mapper_bytes": 49152,
            "dma": False,
            "vblank_ntsc_ms_approx": 4.5,
            "max_frames_per_sprite_sheet": None,
            "frame_count_policy": "project_runtime_budget_required",
            "frame_count_reason": "physical hardware defines memory/transfer ceilings, not a universal animation-frame count",
        },
        "runtime_budget": {
            "status": "pending_tdd_and_scene_budget",
            "vram_residency": "pending",
            "sat_and_scanline": "pending",
            "vblank_upload": "pending",
            "rom_banking": "pending",
            "sheet_frame_count": "pending",
            "required_before_animation_sheet": [
                "GDD move/state frame semantics and duration",
                "TDD static pools and pattern ownership",
                "measured worst-frame VBlank upload budget",
                "ROM/banking storage policy",
                "metasprite geometry and audit_sprite_line_sim result",
            ],
            "not_claimed": "per-pose pattern count is not VRAM residency, SAT object count, scanline load, ROM size, or frame-load time",
        },
        "animation_principles": [
            {"id": pid, "name_en": en, "name_pt": pt, "criterion": criterion,
             "status": "pending", "evidence": "Two static key poses only; animation cadence and transitions are not authored or validated."}
            for pid, en, pt, criterion in ANIMATION_PRINCIPLES
        ],
        "review": {
            "pixel_clusters": "pending",
            "face_detail_readability": "pending",
            "outline_and_cutout": "pending",
            "component_integrity_gate": {
                "mode": cleanup.get("mode", "not_declared"),
                "minimum_opaque_component_px": min_component,
                "poses_with_island_below_minimum": tiny_components,
                "material_regions_status": cleanup.get("material_regions_status", "not_declared"),
                "tool": "audit_sprite_cutout.py",
            },
            "material_shading": "pending",
            "hand_weapon_attachment": "pending",
            "equipment_geometry": "pending",
            "native_size_readability": "pending",
            "standing_body_height_vs_gdd": {
                "status": "pending",
                "measurement_scope": "measure crown-to-sole anatomy excluding handheld cane/equipment",
                "expected_range_px": [args.target_low, args.target_high],
                "evidence": "compare standing idle in native and nearest-neighbor views against GDD range",
            },
            "concept_fidelity": "pending",
            "known_pose_scope": "action key uses source frame 06, whose rounded cane terminal remains readable after the declared transform; full item identity and concept fidelity still require independent human review",
            "equipment_terminal_shape": {
                "status": "pending",
                "expected_identity": "rounded cane terminal; do not flatten into a hammer-like cap",
                "evidence": "inspect frame 06 source, native 1x crop, and nearest-neighbor enlargement",
            },
            "frame_bounds": "both transformed poses require at least one fully transparent pixel on all four edges; action frame 06 keeps the rounded cane terminal entirely inside the canvas",
            "two_pose_staging": "pending",
            "independent_review": "pending",
            "owner_decision": "pending",
            "board_overlay_pixel_identity": "measured_by_audit_asset_proof_sheet.py",
        },
        "proof_image": {
            "path": str(output_path.relative_to(project)),
            "sha256": sha256(output_path),
            "dimensions_px": [W, H],
            "display_scale": "6x nearest-neighbor plus separate native 1x sample; source converted at 5/6 nearest-neighbor",
            "overlay_policy": "no line, grid, label, or annotation intersects either converted pose preview",
        },
        "promotion": {
            "approved_for_res": False,
            "rom_asset_binding": "not_created",
            "emulator_validation": "not_performed",
            "aaa_claim": False,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"proof: {output_path}")
    print(f"report: {report_path}")
    print(f"parent source SHA-256: {sha256(source_path)}")
    print(f"pose patterns: idle={metrics_by_role['idle']['unique_tile_patterns']} action={metrics_by_role['action']['unique_tile_patterns']} pair={len(pattern_union)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
