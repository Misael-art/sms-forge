"""Assenta as chaves novas da provocação 1 na célula de 128 px.

Não desenha anatomia, expressão nem intervalos. A autoria está nos JPEG.
Este arquivo confere o original local, recorta o campo pela cor do canto, reduz em
nearest com a mesma razão da guarda GQ03 e quantiza na paleta de J01.

A altura 104 da célula vale para o corpo de 836 px da guarda. Uma pose
mais alta no original permanece mais alta; o script não a esmaga de volta
a 104. O solo fica em y=116.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import register_gq03_authored_guard as reg  # noqa: E402

GUARD_JPG = HERE / "originals" / "GQ03_authored_guard.jpg"
GUARD_BODY_H = 836
CELL_H = 104
SOLE_Y = 116
CORNER_LIMIT = 45

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


def register_one(source: Path, dest: Path, logical_rel: str) -> dict:
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
        "dest": logical_rel,
        "sha256": sha256(dest),
        "box": list(box),
        "body_wh": [body_w, body_h],
        "cell_wh": [target_w, target_h],
        "place_xy": [left, top],
        "height_ratio_vs_guard": round(body_h / GUARD_BODY_H, 4),
        "corner_rgb": list(corner),
    })
    return report


def verify_file(path: Path, expected: str) -> None:
    if not path.is_file():
        raise SystemExit(f"insumo ausente: {path}; restaure a cópia registrada no Git")
    if sha256(path) != expected:
        raise SystemExit(f"SHA-256 divergente: {path}")


def replay_path(relative: str, directory: str) -> Path:
    path = Path(relative)
    if len(path.parts) != 2 or path.parent != Path(directory) or path.name == "..":
        raise SystemExit(f"caminho inválido no recibo: {relative}")
    result = HERE / path
    if result.parent.is_symlink() or result.is_symlink():
        raise SystemExit(f"link recusado no replay: {relative}")
    return result


def replay(version: int, clean_border=None) -> None:
    receipt_path = HERE / "proposals" / f"TA01_cycle_v{version}_registration.json"
    receipt = json.loads(receipt_path.read_text())
    if receipt["schema"] != f"social_taunt_cycle_v{version}_registration":
        raise SystemExit(f"schema de registro divergente: {receipt_path}")

    lineage = json.loads((HERE / "lineage_v1.json").read_text())
    guard = next(entry for entry in lineage["kept"] if entry["id"] == "GQ03_authored_guard")
    verify_file(GUARD_JPG, guard["original_sha256"])
    verify_file(HERE / guard["logical"], guard["sha256"])
    palette_receipt = json.loads((reg.J01.parents[2] / "idle_metadata_v5.json").read_text())
    verify_file(reg.J01, palette_receipt["sha256"])

    for study in receipt["studies_not_registered"]:
        verify_file(replay_path(study["file"], "originals"), study["sha256"])
    for frame in receipt["kept"]:
        verify_file(replay_path(frame["original"], "originals"), frame["original_sha256"])
    measured = guard_body_height()
    if measured != GUARD_BODY_H:
        raise SystemExit(f"altura da guarda mudou: {measured} != {GUARD_BODY_H}")

    with TemporaryDirectory(prefix=".taunt-replay-", dir=HERE) as tmp:
        staging = Path(tmp)
        outputs = []
        for frame in receipt["kept"]:
            source = HERE / frame["original"]
            measured_frame = {
                "original": frame["original"],
                "original_sha256": frame["original_sha256"],
            }
            if clean_border is not None:
                with Image.open(source) as original:
                    image = original.convert("RGB")
                measured_frame["border_specks_set_to_corner"] = clean_border(image)
                keyed = replay_path(frame["keyed_png"], "originals")
                source = staging / keyed.name
                image.save(source)
                outputs.append((source, keyed))
                measured_frame["keyed_png"] = frame["keyed_png"]
            logical_rel = frame["dest"]
            dest = replay_path(logical_rel, "logical")
            staged = staging / dest.name
            measured_frame.update(register_one(source, staged, logical_rel))
            if measured_frame != frame:
                raise SystemExit(f"derivado divergente do recibo: {logical_rel}")
            outputs.append((staged, dest))

        # Confira todos os derivados antes de repor qualquer arquivo ausente.
        for staged, dest in outputs:
            if dest.exists() or dest.is_symlink():
                verify_file(dest, sha256(staged))
        for staged, dest in outputs:
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(staged, dest)
            except FileExistsError:
                verify_file(dest, sha256(staged))
            print(f"[OK] {dest.relative_to(HERE)} {sha256(staged)}")


if __name__ == "__main__":
    replay(2)
