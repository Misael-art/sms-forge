"""Assenta as chaves novas da provocação 1 na célula de 128 px.

Não desenha anatomia, expressão nem intervalos. A autoria está nos JPEG.
Este arquivo copia o original, recorta o campo pela cor do canto, reduz em
nearest com a mesma razão da guarda GQ03 e quantiza na paleta de J01.

A altura 104 da célula vale para o corpo de 836 px da guarda. Uma pose
mais alta no original permanece mais alta; o script não a esmaga de volta
a 104. O solo fica em y=116.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import register_gq03_authored_guard as reg  # noqa: E402

SESSION = Path(
    "/home/misael/.grok/sessions/"
    "%2Fhome%2Fmisael%2FProjects%2FSMSForge/"
    "01a1993f-25fb-7522-9c39-97119c72c1dc/images"
)
GUARD_JPG = HERE / "originals" / "GQ03_authored_guard.jpg"
GUARD_BODY_H = 836
CELL_H = 104
SOLE_Y = 116
CORNER_LIMIT = 45

# Só as três chaves que a medição local deixou em quatro colunas.
KEPT = (
    ("13.jpg", "TA05_examine.jpg", "logical/TA05_examine.png"),
    ("15.jpg", "TA06_coat_lag.jpg", "logical/TA06_coat_lag.png"),
    ("18.jpg", "TA07_settle.jpg", "logical/TA07_settle.png"),
)
# Estudos medidos e não usados. A cópia preserva o byte; não entra no ciclo.
STUDIES = (
    ("11.jpg", "TA05_attempt_pinch.jpg"),
    ("12.jpg", "TA05_attempt_over_rims.jpg"),
    ("14.jpg", "TA06_coat_wide_study.jpg"),
    ("16.jpg", "TA07_settle_wide_study.jpg"),
    ("17.jpg", "TA07_handswap_study.jpg"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def guard_body_height() -> int:
    image = Image.open(GUARD_JPG).convert("RGB")
    pixels = image.load()
    width, height = image.size
    ys = [y for y in range(height) for x in range(width)
          if not reg.is_magenta(pixels[x, y])]
    if not ys:
        raise SystemExit("guarda sem figura")
    return max(ys) - min(ys) + 1


def corner_box(image: Image.Image) -> tuple[tuple[int, int, int, int], tuple[int, int, int]]:
    pixels = image.load()
    width, height = image.size
    corner = pixels[4, 4]
    limit = CORNER_LIMIT * CORNER_LIMIT

    def background(x: int, y: int) -> bool:
        red, green, blue = pixels[x, y]
        return ((red - corner[0]) ** 2 + (green - corner[1]) ** 2
                + (blue - corner[2]) ** 2) <= limit

    xs, ys = [], []
    for y in range(0, height, 2):
        for x in range(0, width, 2):
            if not background(x, y):
                xs.append(x)
                ys.append(y)
    if not xs:
        raise SystemExit("original sem figura")
    x0 = max(0, min(xs) - 4)
    y0 = max(0, min(ys) - 4)
    x1 = min(width, max(xs) + 6)
    y1 = min(height, max(ys) + 6)
    xs, ys = [], []
    for y in range(y0, y1):
        for x in range(x0, x1):
            if not background(x, y):
                xs.append(x)
                ys.append(y)
    box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
    if box[0] <= 1 or box[1] <= 1 or box[2] >= width - 1 or box[3] >= height - 1:
        raise SystemExit(f"figura encosta na borda: {box}")
    return box, corner


def register_one(source: Path, dest: Path) -> dict:
    image = Image.open(source).convert("RGB")
    box, corner = corner_box(image)
    body_w = box[2] - box[0]
    body_h = box[3] - box[1]
    target_h = (body_h * CELL_H + GUARD_BODY_H // 2) // GUARD_BODY_H
    target_w = (body_w * target_h + body_h // 2) // body_h
    if target_w > 128 or target_h > SOLE_Y or target_h < 1:
        raise SystemExit(f"{source.name} não cabe na célula: {target_w}x{target_h}")
    crop = image.crop(box)
    pixels = crop.load()
    mask = Image.new("1", crop.size)
    mask_px = mask.load()
    limit = CORNER_LIMIT * CORNER_LIMIT
    for y in range(crop.height):
        for x in range(crop.width):
            red, green, blue = pixels[x, y]
            distance = ((red - corner[0]) ** 2 + (green - corner[1]) ** 2
                        + (blue - corner[2]) ** 2)
            mask_px[x, y] = 0 if distance <= limit else 1
    fitted = crop.resize((target_w, target_h), Image.Resampling.NEAREST)
    mask_fit = mask.resize((target_w, target_h), Image.Resampling.NEAREST)
    j01 = Image.open(reg.J01)
    palette = j01.getpalette()
    reference = Image.new("P", (1, 1))
    reference.putpalette(palette)
    quantized = fitted.convert("RGB").quantize(
        palette=reference, dither=Image.Dither.NONE)
    canvas = Image.new("P", (128, 128))
    canvas.putpalette(palette)
    left = 64 - target_w // 2
    top = SOLE_Y - target_h
    kept = mask_fit.load()
    src = quantized.load()
    dst = canvas.load()
    for y in range(target_h):
        for x in range(target_w):
            if not kept[x, y]:
                continue
            value = src[x, y] or 1
            dst[left + x, y + top] = value
    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dest, transparency=0, bits=8)
    report = reg.band_report(canvas)
    report.update({
        "source": source.name,
        "dest": str(dest.relative_to(HERE)),
        "sha256": sha256(dest),
        "box": list(box),
        "body_wh": [body_w, body_h],
        "cell_wh": [target_w, target_h],
        "place_xy": [left, top],
        "height_ratio_vs_guard": round(body_h / GUARD_BODY_H, 4),
        "corner_rgb": list(corner),
    })
    return report


def copy_bytes(session_name: str, dest_name: str) -> str:
    dest = HERE / "originals" / dest_name
    if dest.exists():
        return sha256(dest)
    source = SESSION / session_name
    shutil.copyfile(source, dest)
    if sha256(dest) != sha256(source):
        raise SystemExit(f"cópia divergente: {dest_name}")
    return sha256(dest)


def main() -> None:
    measured = guard_body_height()
    if measured != GUARD_BODY_H:
        raise SystemExit(f"altura da guarda mudou: {measured} != {GUARD_BODY_H}")
    studies = []
    for session_name, dest_name in STUDIES:
        studies.append({
            "file": f"originals/{dest_name}",
            "sha256": copy_bytes(session_name, dest_name),
            "session_name": session_name,
            "registered": False,
        })
    kept = []
    for session_name, original_name, logical_rel in KEPT:
        original_sha = copy_bytes(session_name, original_name)
        report = register_one(HERE / "originals" / original_name,
                              HERE / logical_rel)
        report["original"] = f"originals/{original_name}"
        report["original_sha256"] = original_sha
        kept.append(report)
        print(logical_rel, report["sat_row_peak"], report["opaque_height"],
              report["opaque_top"], report["opaque_bottom"], report["sha256"][:12])
    guard = reg.band_report(Image.open(HERE / "logical" / "GQ03_authored_guard.png"))
    receipt = {
        "schema": "social_taunt_cycle_v2_registration",
        "scale": {
            "guard_jpg_body_h": GUARD_BODY_H,
            "cell_h_for_that_body": CELL_H,
            "sole_y": SOLE_Y,
            "corner_distance_limit": CORNER_LIMIT,
            "note": "Razão comum com a guarda. Pose mais alta não volta a 104.",
        },
        "guard_scaled_band": guard,
        "kept": kept,
        "studies_not_registered": studies,
        "not_an_approval": True,
    }
    out = HERE / "proposals" / "TA01_cycle_v2_registration.json"
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print("guard", guard["sat_row_peak"], guard["opaque_height"],
          guard["opaque_top"], guard["opaque_bottom"])


if __name__ == "__main__":
    main()
