"""Limpa sal do casaco e separa a derrota do neutro na boca.

Não regenera o busto, não troca o crop e não substitui as placas já
registradas. A derrota ganha um franzir de tinta sobre pele; o sorriso e o
neutro só perdem pontos soltos do casaco.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PREVIEW = HERE / "preview"
COAT = {4, 5}
SKIN_OR_INK = {1, 8, 9}
FROWN = ((64, 99), (63, 99), (65, 99), (62, 100), (66, 100), (61, 101), (67, 101))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_salt(image: Image.Image) -> int:
    pixels = image.load()
    width, height = image.size
    edits = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            value = pixels[x, y]
            neighbors = [
                pixels[x + dx, y + dy]
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dx, dy) != (0, 0)
            ]
            if len(set(neighbors)) == 1 and neighbors[0] in COAT and value not in COAT:
                edits.append((x, y, neighbors[0]))
    for x, y, value in edits:
        pixels[x, y] = value
    return len(edits)


def deepen_loss(image: Image.Image) -> int:
    pixels = image.load()
    painted = 0
    for x, y in FROWN:
        if pixels[x, y] in SKIN_OR_INK:
            pixels[x, y] = 1
            painted += 1
    return painted


def main() -> None:
    notes = []
    for name in ("versus_neutral_sms_256.png", "versus_win_sms_256.png", "versus_loss_sms_256.png"):
        source = PREVIEW / name
        image = Image.open(source)
        removed = clean_salt(image)
        painted = deepen_loss(image) if name.startswith("versus_loss") else 0
        dest = PREVIEW / name.replace("_sms_256", "_refined_256")
        image.save(dest, transparency=0, bits=8)
        zoom = image.crop((40, 40, 90, 110)).resize((200, 280), Image.Resampling.NEAREST)
        notes.append({
            "source": name,
            "source_sha256": sha256(source),
            "output": dest.name,
            "output_sha256": sha256(dest),
            "coat_salt_removed": removed,
            "frown_pixels": painted,
        })
        zoom.save(PREVIEW / (dest.stem + "_face4x.png"))
    (HERE / "proposals" / "versus_refine_v1.json").write_text(
        json.dumps({"not_an_approval": True, "plates": notes}, indent=2) + "\n")
    print(json.dumps(notes, indent=2))


if __name__ == "__main__":
    main()
