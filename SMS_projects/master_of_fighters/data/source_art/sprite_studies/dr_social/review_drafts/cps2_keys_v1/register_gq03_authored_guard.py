"""Assenta a guarda autoral GQ03 na célula de 128 px.

Não desenha tornozelo, cauda nem expressão. Recorta o campo magenta, reduz
em nearest com uma razão só, quantiza na paleta já existente de J01 e mede
a mesma escala do adaptador. A autoria está no original; este arquivo só
registra e mede.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
sys.path.insert(0, str(ROOT / "tools" / "sms_wrapper"))
from mugen2sms.converters.display_fit import (  # noqa: E402
    resolve_display_fit, sat_row_peak, scale_sprite,
)
from mugen2sms.parsers.sff import Sprite  # noqa: E402

J01 = HERE.parent / "cps2_sample_v1" / "jab_revision_v8" / "native" / "J01.png"
BC04 = HERE / "logical" / "BC04_cane_tap_contact.png"
AUTHORED = HERE / "originals" / "GQ03_authored_guard.jpg"
DEST = HERE / "logical" / "GQ03_authored_guard.png"
PREVIEW = HERE / "preview" / "GQ03_authored_guard_4x.png"
LEGS = HERE / "preview" / "GQ03_legs_4x.png"
NOTE = HERE / "proposals" / "GQ03_recipe.json"
OVERFLOW = HERE / "proposals" / "BC04_overflow_materials_v1.json"

GROUPS = {}
for index, name in (
    (1, "contorno"), (2, "contorno"), (3, "contorno"),
    (4, "cinza"), (5, "cinza"), (6, "cinza"), (7, "cinza"),
    (8, "pele"), (9, "pele"), (10, "pele"),
    (11, "casaco"), (12, "casaco"), (13, "casaco"), (14, "casaco"),
    (16, "casaco"), (17, "casaco"),
    (18, "gravata"), (19, "gravata"), (20, "gravata"),
    (21, "cinza_frio"), (22, "cinza_frio"), (23, "branco"),
    (24, "latao"), (25, "latao"), (26, "latao"), (27, "latao"),
    (28, "bota"), (29, "bota"), (30, "bota"),
):
    GROUPS[index] = name


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_magenta(rgb: tuple[int, int, int]) -> bool:
    red, green, blue = rgb
    return red > 200 and blue > 200 and green < 100


def register() -> Image.Image:
    source = Image.open(AUTHORED).convert("RGB")
    pixels = source.load()
    width, height = source.size
    xs, ys = [], []
    for y in range(height):
        for x in range(width):
            if not is_magenta(pixels[x, y]):
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit("original sem figura")
    box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
    if box[0] <= 1 or box[1] <= 1 or box[2] >= width - 1 or box[3] >= height - 1:
        raise SystemExit(f"figura encosta na borda do original: {box}")
    mask = Image.new("1", source.size)
    mask_px = mask.load()
    for y in range(height):
        for x in range(width):
            mask_px[x, y] = 0 if is_magenta(pixels[x, y]) else 1
    crop = source.crop(box)
    mask_crop = mask.crop(box)
    body_h = box[3] - box[1]
    body_w = box[2] - box[0]
    target_h = 104
    target_w = (body_w * target_h + body_h // 2) // body_h
    fitted = crop.resize((target_w, target_h), Image.Resampling.NEAREST)
    mask_fit = mask_crop.resize((target_w, target_h), Image.Resampling.NEAREST)
    if target_w > 128 or target_h > 116:
        raise SystemExit(f"não cabe na célula: {target_w}x{target_h}")
    j01 = Image.open(J01)
    palette = j01.getpalette()
    reference = Image.new("P", (1, 1))
    reference.putpalette(palette)
    quantized = fitted.convert("RGB").quantize(palette=reference, dither=Image.Dither.NONE)
    canvas = Image.new("P", (128, 128))
    canvas.putpalette(palette)
    left = 64 - target_w // 2
    top = 116 - target_h
    kept = mask_fit.load()
    src = quantized.load()
    dst = canvas.load()
    remapped = 0
    for y in range(target_h):
        for x in range(target_w):
            if not kept[x, y]:
                continue
            value = src[x, y]
            if value == 0:
                value = 1
                remapped += 1
            dst[left + x, y + top] = value
    canvas.save(DEST, transparency=0, bits=8)
    register.box = box
    register.target = (target_w, target_h, left, top)
    register.remapped = remapped
    return canvas


def as_indexed(image: Image.Image) -> Image.Image:
    if image.mode == "P" and image.getpalette() is not None:
        return image
    j01 = Image.open(J01)
    palette = j01.getpalette()
    colors = [tuple(palette[i:i + 3]) for i in range(0, 96, 3)]
    rgba = image.convert("RGBA")
    out = Image.new("P", rgba.size)
    out.putpalette(palette)
    src = rgba.load()
    dst = out.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, alpha = src[x, y]
            if alpha == 0:
                continue
            best_index, best_distance = 1, 10**9
            for index, color in enumerate(colors):
                if index == 0:
                    continue
                distance = ((red - color[0]) ** 2 + (green - color[1]) ** 2
                            + (blue - color[2]) ** 2)
                if distance < best_distance:
                    best_index, best_distance = index, distance
            dst[x, y] = best_index
    as_indexed.note = "arquivo RGBA; índices são o vizinho da paleta de J01, só nesta medição"
    return out


def scaled(image: Image.Image) -> Sprite:
    image = as_indexed(image)
    palette_raw = image.getpalette()
    palette = [tuple(palette_raw[i:i + 3]) for i in range(0, 768, 3)]
    # Pillow 11.3 retirou get_flattened_data. tobytes() no modo P é o
    # mesmo buffer de índices: a guarda continua 69 px, topo 9, base 77.
    flat = getattr(image, "get_flattened_data", None)
    pixels = bytes(flat()) if flat is not None else image.tobytes()
    sprite = Sprite(0, 0, 64, 116, image.width, image.height,
                    pixels, palette, False, None, 0)
    fit = resolve_display_fit("pose_budget", "cps2", "sms")
    first, _ = scale_sprite(sprite, fit)
    second_fit = replace(fit, scale_num_x=7, scale_den_x=9,
                         scale_num_y=7, scale_den_y=9, pose_budget=False)
    second, _ = scale_sprite(first, second_fit)
    return second


def band_report(image: Image.Image) -> dict:
    second = scaled(image)
    pixels = second.pixels
    width = second.width
    opaque = []
    for y in range(second.height):
        xs = [x for x in range(width) if pixels[y * width + x]]
        if xs:
            opaque.append((y, xs[0], xs[-1], xs[-1] - xs[0] + 1))
    return {
        "sat_row_peak": sat_row_peak(second),
        "opaque_height": opaque[-1][0] - opaque[0][0] + 1,
        "opaque_top": opaque[0][0],
        "opaque_bottom": opaque[-1][0],
        "max_span": max(row[3] for row in opaque),
        "sprite_wh": [second.width, second.height],
    }


def components(image: Image.Image) -> dict:
    second = scaled(image)
    pixels = second.pixels
    width = second.width
    lines = []
    for y in range(second.height):
        row = pixels[y * width:(y + 1) * width]
        runs = []
        x = 0
        while x < width:
            if row[x] == 0:
                x += 1
                continue
            start = x
            hist = Counter()
            while x < width and row[x]:
                hist[GROUPS.get(row[x], f"indice_{row[x]}")] += 1
                x += 1
            runs.append({
                "x0": start,
                "x1": x - 1,
                "material": hist.most_common(1)[0][0],
                "counts": dict(hist),
            })
        cells = set()
        for run in runs:
            for x in range(run["x0"], run["x1"] + 1):
                cells.add(x // 8)
        if len(cells) >= 5:
            lines.append({
                "y": y,
                "cells": sorted(cells),
                "cell_count": len(cells),
                "runs": runs,
            })
    return {
        "scale": "pose_budget 2/3 x 6/7, depois extra 7/9, célula 128 inteira",
        "lines_with_5_or_more_cells": lines,
        "line_count": len(lines),
        "peak_cells": max((line["cell_count"] for line in lines), default=0),
        "sat_row_peak": sat_row_peak(second),
    }


def main() -> None:
    posed = register()
    zoom = posed.resize((512, 512), Image.Resampling.NEAREST).convert("RGB")
    zoom.save(PREVIEW)
    legs = posed.crop((0, 64, 128, 128)).resize((512, 256), Image.Resampling.NEAREST)
    legs.convert("RGB").save(LEGS)
    preview = band_report(posed)
    bc04 = Image.open(BC04)
    overflow = components(bc04)
    j01 = components(Image.open(J01))
    recipe = {
        "id": "GQ03_authored_guard",
        "role": "candidata autoral de guarda. Não é aprovação e não substitui J01.",
        "authored_original": str(AUTHORED.relative_to(ROOT)),
        "authored_sha256": sha256(AUTHORED),
        "prompt": "prompts/GQ03_authored_guard.txt",
        "references_fed": [
            "J01 nativo do jab v8, ampliado 8× em nearest, como referência da edição",
        ],
        "not_fed": [
            "model sheet inteiro",
            "GQ02",
            "author_gq02_stacked_guard.py",
        ],
        "registration": {
            "magenta_key": "R>200, B>200, G<100; o campo dentro da caixa também fica transparente",
            "source_bbox": list(register.box),
            "isotropic_nearest_to_opaque_height": 104,
            "placed": {
                "size": list(register.target[:2]),
                "origin": list(register.target[2:]),
                "sole_y": 116,
                "bbox_center_x": 64,
            },
            "palette": "paleta indexada existente de J01, sem dither",
            "index_0_opaque_reassigned_to_outline": register.remapped,
            "anatomy_edits": [],
        },
        "sms_scale_not_mixed": "encaixe oficial 2/3×6/7 e depois extra 7/9. Não é 35/52.",
        "local_preview_extra_7_9": preview,
        "output": str(DEST.relative_to(ROOT)),
        "output_sha256": sha256(DEST),
        "not_an_approval": True,
    }
    NOTE.write_text(json.dumps(recipe, indent=2) + "\n")
    overflow_note = {
        "id": "BC04_overflow_materials_v1",
        "source": str(BC04.relative_to(ROOT)),
        "source_sha256": sha256(BC04),
        "question": "Quais materiais ocupam as linhas com 5 ou mais células de 8 px.",
        "groups": "Índices da paleta de J01. Latão inclui fivela e bengala; a posição do trecho separa os dois.",
        "bc04_file_mode": "RGBA. A classificação usa o índice mais próximo da paleta de J01 e não grava outro PNG.",
        "bc04": overflow,
        "j01_control": {
            "line_count": j01["line_count"],
            "peak_cells": j01["peak_cells"],
            "sat_row_peak": j01["sat_row_peak"],
            "lines": j01["lines_with_5_or_more_cells"],
        },
        "not_a_fix": "Medição. Não eleva, encurta, apaga nem separa a bengala.",
    }
    OVERFLOW.write_text(json.dumps(overflow_note, indent=2) + "\n")
    print(json.dumps({
        "gq03_sha256": recipe["output_sha256"],
        "placed": recipe["registration"]["placed"],
        "preview": preview,
        "bc04_peak_cells": overflow["peak_cells"],
        "bc04_lines": overflow["line_count"],
        "j01_lines": j01["line_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
