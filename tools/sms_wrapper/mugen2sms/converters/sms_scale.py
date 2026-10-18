# Perfil histórico legacy_probe_quarter. Não é limite do motor nem perfil de delivery.
# A revisão 2026-09-26 exige escala uniforme por personagem/cena; este backend
# permanece para reproduzir T10 e é bloqueado pelo audit_mugen_engine_contract.
"""Perfil histórico `legacy_probe_quarter` — GDD 2026-09-25 (decisão T10).

Esta API e seus limites permanecem para reproduzir T10. Não definem a escala
vigente nem autorizam delivery; o fluxo atual usa `fighter_scale` racional e
uniforme por personagem/cena em `scene_cut.py`, com o padrão de 72–88 px.

Medicao que originou a regra (s4_generation_report.json, round Ken): pior pose x 2
lutadores = pico 32 sprites/scanline (teto 8, SMSlib) e SAT 256 (teto 64). Ken em
escala nativa MUGEN nao cabe no VDP.

Contrato histórico T10:
- modo de sprite: SPRITEMODE_TALL 8x16 (SMSlib.h:57);
- lutador <=4 sprites/linha (~32 px) x <=3 linhas TALL (~48 px) — 2 lutadores fecham
  o teto exato de 8/scanline, sem flicker (proibido pelo GDD);
- downscale 1:4 FIXO aplicado a todo sprite que nao caiba em 1:1; pose que ainda
  estourar apos a escala vira `manual` (reautoria) e NAO entra no build.

Amostragem nearest topo-esquerda: mesmo metodo de `prepare_sms_pixel_art.py`
(nearest_downscale), que e a doutrina de pixel do SMSForge para reducao.
"""
from __future__ import annotations

from dataclasses import replace
from math import gcd
from types import SimpleNamespace

SCALE = 4          # 1:4 fixo (GDD)
MAX_COLS = 4       # sprites de 8 px por scanline, por lutador (~32 px)
MAX_TALL_ROWS = 3  # sprites TALL 8x16 de altura (~48 px)


def pose_runtime_size(w_px: int, h_px: int) -> tuple[int, int]:
    """(colunas de 8 px, linhas TALL de 16 px) APOS o downscale 1:4, por excesso."""
    w8 = -(-w_px // SCALE)
    h8 = -(-h_px // SCALE)
    return (-(-w8 // 8), -(-h8 // 16))


def exceeds_budget(w_px: int, h_px: int) -> bool:
    cols, rows = pose_runtime_size(w_px, h_px)
    return cols > MAX_COLS or rows > MAX_TALL_ROWS


def needs_scale(w_px: int, h_px: int) -> bool:
    """1:1 ja cabe no orcamento do lutador? (se nao, entra em downscale)."""
    cols = -(-w_px // 8)
    rows = -(-h_px // 16)
    return cols > MAX_COLS or rows > MAX_TALL_ROWS


def downscale_indexed(sp, k: int = SCALE):
    """Sprite IR (width/height/pixels flat/por palette) -> copia reduzida nearest.

    Paleta e preservada intacta: reduzir pixels nunca aumenta cores uteis; o que
    muda e a frequencia, e `_subpalette` decide por frequencia (sms_tiles.py).
    """
    w, h = max(1, sp.width // k), max(1, sp.height // k)
    src = sp.pixels
    sw = sp.width
    flat = bytearray(w * h)
    for y in range(h):
        sy = min(sp.height - 1, y * k) * sw
        base = y * w
        for x in range(w):
            flat[base + x] = src[sy + min(sw - 1, x * k)]
    return SimpleNamespace(width=w, height=h, pixels=bytes(flat), palette=sp.palette,
                           group=getattr(sp, "group", None), image=getattr(sp, "image", None))


def _round_ratio(value: int, numerator: int, denominator: int) -> int:
    """Round signed coordinates symmetrically, with ties away from zero."""
    magnitude = abs(value) * numerator
    result = (magnitude * 2 + denominator) // (2 * denominator)
    return result if value >= 0 else -result


def _scaled_size(value: int, numerator: int, denominator: int) -> int:
    return max(1, _round_ratio(value, numerator, denominator))


def _resample_indices(sp, numerator: int, denominator: int):
    """Resize indexed pixels with deterministic nearest-neighbour sampling."""
    width = _scaled_size(sp.width, numerator, denominator)
    height = _scaled_size(sp.height, numerator, denominator)
    pixels = bytearray(width * height)
    for y in range(height):
        sy = min(sp.height - 1, ((2 * y + 1) * denominator) // (2 * numerator))
        for x in range(width):
            sx = min(sp.width - 1, ((2 * x + 1) * denominator) // (2 * numerator))
            pixels[y * width + x] = sp.pixels[sy * sp.width + sx]
    return width, height, bytes(pixels)


def measure_idle_opaque_bounds(character, action):
    """Union nontransparent idle pixels in AIR-axis coordinates."""
    by_key = {(sprite.group, sprite.image): sprite for sprite in character.sprites}
    boxes = []
    for frame_index, frame in enumerate(action.frames):
        sprite = by_key.get((frame.group, frame.image))
        if sprite is None:
            raise ValueError(f"idle frame {frame_index} references a missing sprite")
        xs, ys = [], []
        for pos, color in enumerate(sprite.pixels):
            if color:
                xs.append(pos % sprite.width)
                ys.append(pos // sprite.width)
        if not xs:
            continue
        ox, oy = frame.x - sprite.axis_x, frame.y - sprite.axis_y
        boxes.append({"frame": frame_index,
                      "xyxy": [min(xs) + ox, min(ys) + oy,
                               max(xs) + ox, max(ys) + oy],
                      "source_size": [sprite.width, sprite.height]})
    if not boxes:
        raise ValueError("idle action has no opaque pixels")
    bounds = [min(box["xyxy"][0] for box in boxes),
              max(box["xyxy"][2] for box in boxes),
              min(box["xyxy"][1] for box in boxes),
              max(box["xyxy"][3] for box in boxes)]
    return bounds, boxes


def target_ratio(opaque_height: int, target_px: int,
                 accepted_range: tuple[int, int]) -> tuple[int, int]:
    """Smallest exact rational representation of target_px / opaque_height."""
    if opaque_height <= 0:
        raise ValueError("opaque idle height must be positive")
    lo, hi = accepted_range
    if not lo <= target_px <= hi:
        raise ValueError(f"target height {target_px} is outside accepted range {lo}..{hi}")
    common = gcd(target_px, opaque_height)
    return target_px // common, opaque_height // common


def scale_character(character, action_ids: set[int], numerator: int, denominator: int):
    """Copy a character with one uniform transform applied to selected AIR actions.

    The same ratio is applied to source pixels, sprite axes, AIR offsets, and
    CLSN coordinates. AIR durations, frame order, and flips remain unchanged.
    """
    if numerator <= 0 or denominator <= 0:
        raise ValueError("scale ratio must be positive")
    original_sprites = {(sprite.group, sprite.image): sprite for sprite in character.sprites}
    sprites = []
    for sprite in character.sprites:
        width, height, pixels = _resample_indices(sprite, numerator, denominator)
        sprites.append(replace(sprite, axis_x=_round_ratio(sprite.axis_x, numerator, denominator),
                               axis_y=_round_ratio(sprite.axis_y, numerator, denominator),
                               width=width, height=height, pixels=pixels))
    scaled_sprites = {(sprite.group, sprite.image): sprite for sprite in sprites}

    anims = dict(character.anims)
    for action_id in action_ids:
        if action_id not in anims:
            raise ValueError(f"AIR action {action_id} is missing")
        action = anims[action_id]
        frames = []
        for frame in action.frames:
            original = original_sprites[(frame.group, frame.image)]
            scaled = scaled_sprites[(frame.group, frame.image)]
            scale_boxes = lambda boxes: [tuple(_round_ratio(v, numerator, denominator)
                                                 for v in box) for box in boxes]
            frames.append(replace(frame,
                                  x=scaled.axis_x + _round_ratio(
                                      frame.x - original.axis_x, numerator, denominator),
                                  y=scaled.axis_y + _round_ratio(
                                      frame.y - original.axis_y, numerator, denominator),
                                  clsn1=scale_boxes(frame.clsn1),
                                  clsn2=scale_boxes(frame.clsn2)))
        anims[action_id] = replace(action, frames=frames)
    return replace(character, sprites=sprites, anims=anims)
