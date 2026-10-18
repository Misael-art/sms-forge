"""REGRA 1 -- contrato de paletas da engine: cada lutador tem UMA linha de CRAM (15 cores + transparente)
para corpo E efeitos. Mede o que um personagem convertido ocupa e reprova quem estoura.

O relatorio separa o que e EXATO do que e ESTIMATIVA:
- exato: slots reservados; indices usados nos sheets; classe de cada slot = a tupla de palavras VDP
  dele em TODAS as variantes; classes iguais podem ser fundidas sem perda (mesma cor em toda variante,
  portanto o mesmo resultado em qualquer transformacao que dependa so da cor, como o flash);
- estimativa: cores de efeito "proximas" (dE76 <= limite) de uma classe estavel. Isso e aproximacao que
  precisa ser feita e julgada, nao prova de que a cor sobra.
Cores decodificadas com `converters.sprites.vdp_rgb` (a mesma grade do conversor).
"""
from __future__ import annotations

import collections
import math
import re
from pathlib import Path

from PIL import Image

from .converters.sprites import vdp_rgb

LINE_SLOTS = 15

# mapa de posse estatica (REGRA 1). Emprestimo e declarado, com janela e restauracao.
SLOT_MAP = {
    "PAL0": {"owner": "cenario (BG_A + BG_B compartilham a linha)", "loan": "fundo de super enquanto cobre a tela; restaura em bgfx_end/KO/fim de luta"},
    "PAL1": {"owner": "lutador P1 (corpo + efeitos)", "loan": "flash de impacto por tabela de swap pre-declarada, so nesta linha"},
    "PAL2": {"owner": "lutador P2 (corpo + efeitos)", "loan": "flash de impacto por tabela de swap pre-declarada, so nesta linha"},
    "PAL3": {"owner": "HUD", "loan": None},
}


def _lab(c):
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116  # noqa: E731
    r, g, b = [((v / 255 + 0.055) / 1.055) ** 2.4 if v / 255 > 0.04045 else v / 255 / 12.92 for v in c]
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    return (116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z)))


def delta_e(a, b) -> float:
    return math.dist(_lab(a), _lab(b))


def analyse(variants: list[list[int]], fxpal: list[int], body_used: set[int], fx_pixels: dict[int, int],
            limit: float = 10.0) -> dict:
    """variants: paletas do corpo (16 palavras VDP cada); fxpal: paleta dos efeitos;
    body_used: indices de corpo que aparecem em algum pixel; fx_pixels: indice de efeito -> pixels."""
    if not isinstance(limit, (int, float)) or not math.isfinite(limit) or limit < 0:
        raise ValueError(f"limite de dE invalido: {limit!r}")
    if not variants or any(len(v) != 16 for v in variants) or len(fxpal) != 16:
        raise ValueError("paletas devem ter 16 palavras (indice 0 = transparente)")
    if 0 in body_used or 0 in fx_pixels:
        raise ValueError("indice 0 e transparente: nao pode estar em uso opaco")
    cls = {i: tuple(v[i] for v in variants) for i in range(1, 16)}
    used = sorted(body_used)
    classes: dict[tuple, list[int]] = {}
    for i in used:
        classes.setdefault(cls[i], []).append(i)
    merges = {min(g): sorted(g) for g in classes.values() if len(g) > 1}
    remap = {i: min(g) for g in classes.values() for i in g}          # sem perda: mesma classe
    stable = {k for k in classes if len(set(k)) == 1}                   # mesma cor em toda variante
    varying = [k for k in classes if k not in stable]
    stable_rgb = {k[0]: vdp_rgb(k[0]) for k in stable}
    fx_words = {i: fxpal[i] for i in fx_pixels}
    fx_exact_new = sorted({w for w in fx_words.values() if w not in stable_rgb})   # cor exata sem classe estavel
    orphan = [w for w in fx_exact_new if not stable_rgb or
              min(delta_e(vdp_rgb(w), c) for c in stable_rgb.values()) > limit]
    weight = collections.Counter()
    for i, n in fx_pixels.items():
        weight[fx_words[i]] += n
    reps: list[int] = []
    for w in sorted(orphan, key=lambda w: -weight[w]):
        if not any(delta_e(vdp_rgb(w), vdp_rgb(r)) <= limit for r in reps):
            reps.append(w)
    body_slots = len(classes)
    exact_need = body_slots + len(fx_exact_new)
    estimate = body_slots + len(reps)
    return {
        "reserved_body_slots": 15, "body_indices_used": len(used), "unused_body_indices": [i for i in range(1, 16) if i not in body_used],
        "body_classes": body_slots, "stable_classes": len(stable), "varying_classes": len(varying),
        "lossless_merges": {str(k): v for k, v in merges.items()}, "remap": {str(k): v for k, v in remap.items() if k != v},
        "slots_after_lossless": body_slots, "free_after_lossless": LINE_SLOTS - body_slots,
        "fx_colours_exact": len(set(fx_words.values())), "fx_exact_without_stable_twin": len(fx_exact_new),
        "exact_need": exact_need, "exact_fits": exact_need <= LINE_SLOTS,
        "estimate": {"delta_e_limit": limit, "fx_dedicated": len(reps), "need": estimate,
                     "note": "aproximacao dE: as cores 'proximas' precisam ser remapeadas e julgadas"},
        "line_slots": LINE_SLOTS, "fits": exact_need <= LINE_SLOTS, "over_by": max(0, exact_need - LINE_SLOTS),
    }


def verify_remap(variants: list[list[int]], remap: dict[int, int], used: set[int]) -> bool:
    """Prova da fusao sem perda: todo pixel usado mostra a mesma palavra VDP em toda variante."""
    return all(v[i] == v[remap.get(i, i)] for v in variants for i in used)


def _array(src: str, name: str) -> list[int]:
    b = src[src.index(name):]
    b = b[:b.index("};")]
    return [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{1,4})", b)]


def check_project(project: Path, char_id: str, limit: float = 10.0) -> dict:
    src = (project / "src" / "mg_gen" / f"mg_{char_id}.c").read_text(encoding="utf-8")
    flat = _array(src, "static const u16 pals[][16]")
    variants = [flat[i:i + 16] for i in range(0, len(flat), 16)]
    fxpal = _array(src, "static const u16 fxpal[]")
    res = (project / "res" / f"mgres_{char_id}.res").read_text(encoding="utf-8")
    fx_px: collections.Counter = collections.Counter()
    body_used: set[int] = set()
    for name, path in re.findall(r'SPRITE (\w+) "([^"]+)"', res):
        data = Image.open(project / "res" / path).get_flattened_data()
        if name.endswith("_fx"):
            fx_px.update(i for i in data if i)
        else:
            body_used |= set(data) - {0}
    rep = analyse(variants, fxpal, body_used, dict(fx_px), limit)
    rep["remap_lossless_verified"] = verify_remap(variants, {int(k): v for k, v in rep["remap"].items()}, body_used)
    return {"character": char_id, "variants": len(variants), **rep}
