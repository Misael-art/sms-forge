"""GQ02 — fecha a sola da guarda J01 sem redesenhar o corpo.

A medição extra 7/9 mostrou um único bloco de cinco colunas, nas linhas da
sola. Esta revisão desloca o componente esquerdo para a bengala e o direito
para dentro, em rampa, e recompõe a haste por cima. Não corta a arma, não
apaga células de uma pose larga e não altera cabeça, tronco, pega nem pivô.

Candidato de atuação. Não é aprovação, não entra em res/ e não autoriza
intervalos da bengala.
"""

from __future__ import annotations

import hashlib
import json
import sys
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

SOURCE = HERE.parent / "cps2_sample_v1" / "jab_revision_v8" / "native" / "J01.png"
DEST = HERE / "logical" / "GQ02_stacked_guard.png"
PREVIEW = HERE / "preview" / "GQ02_stacked_guard_4x.png"
BOARD = HERE / "preview" / "GQ02_against_j01_4x.png"
NOTE = HERE / "proposals" / "GQ02_recipe.json"

# A sola precisa entrar nas colunas 3–5 depois do encaixe. A cauda e a bota
# de trás dobram para junto da haste; a bota da frente recua o mínimo que tira
# a ponta da quinta coluna. A haste original é recomposta por cima.
LEFT_SHIFT = {y: 4 + round(17 * (y - 92) / 21) for y in range(92, 116)}
RIGHT_SHIFT = {y: 0 for y in range(128)}
for _y, _amount in {100: 2, 101: 3, 102: 4, 103: 6, 104: 7, 105: 8}.items():
    RIGHT_SHIFT[_y] = _amount
for _y in range(106, 116):
    RIGHT_SHIFT[_y] = 9


def _runs(row: list[int]) -> list[tuple[int, int]]:
    found = []
    x = 0
    while x < len(row):
        if row[x] == 0:
            x += 1
            continue
        start = x
        while x < len(row) and row[x]:
            x += 1
        found.append((start, x - 1))
    return found


def _run_containing(runs: list[tuple[int, int]], x: int) -> tuple[int, int] | None:
    for start, end in runs:
        if start <= x <= end:
            return start, end
    return None


def author(source: Image.Image) -> Image.Image:
    width, height = source.size
    src = source.load()
    out = source.copy()
    dst = out.load()
    moved = 0
    stacked = 0
    for y in range(height):
        row = [src[x, y] for x in range(width)]
        runs = _runs(row)
        cane = _run_containing(runs, 51)
        left = shift = LEFT_SHIFT.get(y, 0)
        right = RIGHT_SHIFT.get(y, 0)
        if left == 0 and right == 0:
            continue
        edited = row[:]
        if left and runs and runs[0][1] < (cane[0] if cane else 48):
            start, end = runs[0]
            for x in range(start, end + 1):
                edited[x] = 0
            for x in range(start, end + 1):
                moved += 1
                nx = x + left
                if 0 <= nx < width:
                    if edited[nx]:
                        stacked += 1
                    edited[nx] = row[x]
        if right:
            right_runs = [item for item in runs if item[0] > (cane[1] if cane else 55)]
            for start, end in right_runs:
                for x in range(start, end + 1):
                    edited[x] = 0
            for start, end in right_runs:
                for x in range(start, end + 1):
                    moved += 1
                    nx = x - right
                    if 0 <= nx < width:
                        if edited[nx]:
                            stacked += 1
                        edited[nx] = row[x]
        if cane:
            for x in range(cane[0], cane[1] + 1):
                edited[x] = row[x]
        for x, value in enumerate(edited):
            dst[x, y] = value
    author.moved = moved
    author.stacked = stacked
    return out


def scaled_peak(image: Image.Image) -> dict:
    palette_raw = image.getpalette()
    palette = [tuple(palette_raw[i:i + 3]) for i in range(0, 768, 3)]
    sprite = Sprite(0, 0, 64, 116, image.width, image.height,
                    bytes(image.getdata()), palette, False, None, 0)
    fit = resolve_display_fit("pose_budget", "cps2", "sms")
    first, _ = scale_sprite(sprite, fit)
    second_fit = replace(fit, scale_num_x=7, scale_den_x=9,
                         scale_num_y=7, scale_den_y=9, pose_budget=False)
    second, _ = scale_sprite(first, second_fit)
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
        "sole_rows": [row for row in opaque if row[0] >= 64],
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source = Image.open(SOURCE)
    if source.mode != "P" or source.info.get("transparency") != 0:
        raise SystemExit("J01 precisa continuar indexado com índice 0 transparente")
    if source.size != (128, 128):
        raise SystemExit("canvas de J01 mudou")
    posed = author(source)
    posed.save(DEST, transparency=0, bits=8)
    zoom = posed.resize((512, 512), Image.Resampling.NEAREST)
    source_zoom = source.resize((512, 512), Image.Resampling.NEAREST)
    zoom.save(PREVIEW)
    board = Image.new("RGB", (1024, 512), (0, 0, 0))
    board.paste(source_zoom.convert("RGB"), (0, 0))
    board.paste(zoom.convert("RGB"), (512, 0))
    board.save(BOARD)
    report = {
        "id": "GQ02_stacked_guard",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "output": str(DEST.relative_to(ROOT)),
        "output_sha256": sha256(DEST),
        "left_shift_by_row": {str(y): n for y, n in LEFT_SHIFT.items()},
        "right_shift_by_row": {str(y): n for y, n in RIGHT_SHIFT.items() if n},
        "pixels_relocated": author.moved,
        "pixels_stacked_on_existing": author.stacked,
        "local_scale_preview_extra_7_9": scaled_peak(posed),
        "source_scale_preview_extra_7_9": scaled_peak(source),
        "not_an_approval": True,
        "official_pair": "local preview only; the pair receipt is proposals/GQ02_pair_result.json",
    }
    NOTE.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "output_sha256": report["output_sha256"],
        "preview_peak": report["local_scale_preview_extra_7_9"]["sat_row_peak"],
        "source_peak": report["source_scale_preview_extra_7_9"]["sat_row_peak"],
        "preview_height": report["local_scale_preview_extra_7_9"]["opaque_height"],
        "preview_max_span": report["local_scale_preview_extra_7_9"]["max_span"],
    }, indent=2))


if __name__ == "__main__":
    main()
