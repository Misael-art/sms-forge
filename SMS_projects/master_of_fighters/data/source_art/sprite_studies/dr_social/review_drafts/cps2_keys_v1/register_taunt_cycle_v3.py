"""Registra o assentamento corrigido e a subida da mão.

Não desenha anatomia. A autoria está nos JPEG. A cópia do original é
byte a byte. Três ou quatro pixels soltos no canto da borda, fora do
corpo, voltam à cor do canto antes da chave. O corpo usa a mesma razão
da guarda e não é esmagado.
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
import register_taunt_cycle_v2 as base  # noqa: E402

SESSION = Path(
    "/home/misael/.grok/sessions/"
    "%2Fhome%2Fmisael%2FProjects%2FSMSForge/"
    "01a1993f-25fb-7522-9c39-97119c72c1dc/images"
)
KEPT = (
    ("22.jpg", "TA07_settle_v2.jpg", "logical/TA07_settle_v2.png"),
    ("24.jpg", "TA08_hand_rise.jpg", "logical/TA08_hand_rise.png"),
)
STUDIES = (
    ("19.jpg", "TA07_attempt_hand_up.jpg"),
    ("20.jpg", "TA07_attempt_waist_dark.jpg"),
    ("21.jpg", "TA07_attempt_from_bright.jpg"),
    ("23.jpg", "TA07_attempt_halo.jpg"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_border(image: Image.Image) -> list[list[int]]:
    pixels = image.load()
    width, height = image.size
    corner = pixels[4, 4]
    limit = base.CORNER_LIMIT * base.CORNER_LIMIT

    def background(x: int, y: int) -> bool:
        red, green, blue = pixels[x, y]
        return ((red - corner[0]) ** 2 + (green - corner[1]) ** 2
                + (blue - corner[2]) ** 2) <= limit

    specks = []
    for y in range(height):
        for x in range(width):
            if x < 8 or y < 8 or x >= width - 8 or y >= height - 8:
                if not background(x, y):
                    specks.append((x, y))
    if len(specks) > 8:
        raise SystemExit(f"borda com figura de verdade: {len(specks)}")
    for x, y in specks:
        pixels[x, y] = corner
    return [[x, y] for x, y in specks]


def main() -> None:
    measured = base.guard_body_height()
    if measured != base.GUARD_BODY_H:
        raise SystemExit(f"altura da guarda mudou: {measured}")
    studies = []
    for session_name, dest_name in STUDIES:
        dest = HERE / "originals" / dest_name
        if not dest.exists():
            shutil.copyfile(SESSION / session_name, dest)
        studies.append({
            "file": f"originals/{dest_name}",
            "sha256": sha256(dest),
            "session_name": session_name,
            "registered": False,
        })
    kept = []
    for session_name, original_name, logical_rel in KEPT:
        dest = HERE / "originals" / original_name
        if not dest.exists():
            shutil.copyfile(SESSION / session_name, dest)
        if sha256(dest) != sha256(SESSION / session_name):
            raise SystemExit(f"cópia divergente: {original_name}")
        image = Image.open(dest).convert("RGB")
        specks = clean_border(image)
        cleaned = HERE / "originals" / (Path(original_name).stem + "_keyed.png")
        image.save(cleaned)
        report = base.register_one(cleaned, HERE / logical_rel)
        report["original"] = f"originals/{original_name}"
        report["original_sha256"] = sha256(dest)
        report["border_specks_set_to_corner"] = specks
        report["keyed_png"] = f"originals/{cleaned.name}"
        kept.append(report)
        print(logical_rel, report["opaque_height"], report["sat_row_peak"],
              report["max_span"], report["sha256"][:12])
    receipt = {
        "schema": "social_taunt_cycle_v3_registration",
        "replaces_pose": "logical/TA07_settle.png permanece; o ciclo novo usa a v2",
        "scale_note": (
            "A v1 media 886 px de corpo contra 836 da guarda, com as mesmas "
            "razões de ombro, quadril e sola. Era deriva uniforme, não "
            "extensão. Estas duas ficam em 72 px de altura SMS, dentro de "
            "66–72, sola na mesma base. Não foram esmagadas."
        ),
        "color_note": (
            "O azul escuro da v1 caía no código SMS 20, o verde-azulado. "
            "A v2 e a subida da mão voltam ao ciano da família 56/57."
        ),
        "kept": kept,
        "studies_not_registered": studies,
        "not_an_approval": True,
    }
    out = HERE / "proposals" / "TA01_cycle_v3_registration.json"
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
