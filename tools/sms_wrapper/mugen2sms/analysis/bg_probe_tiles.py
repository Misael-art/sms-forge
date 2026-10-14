"""Exact tile helpers for isolated BG normal probes; no delivery renderer claim.

Factored from the local source-index 200/201 study. Mixed cells keep P1 above
P2 and approximate P2's color with P1's palette, as in that diagnostic.
"""
from __future__ import annotations
import struct
from collections import defaultdict
from pathlib import Path
from mugen2sms.converters.sms_tiles import _pal
FLOOR = 160
MARKER_COL = 29
MARKER_ROW = 0
SPRITE_PALETTE_FLAG = 0x0800


def sms_word(rgb: tuple[int, int, int]) -> int:
    r, g, b = _pal.nearest_code(rgb)
    return r | (g << 2) | (b << 4)

def word_rgb(word: int) -> tuple[int, int, int]:
    return tuple(((word >> shift) & 3) * 85 for shift in (0, 2, 4))

def source_frame(character, action_id: int, frame_index: int, center_x: int,
                 source_slots: dict[int, int], facing_left: bool = False) -> dict[tuple[int, int], bytes]:
    frame = character.anims[action_id].frames[frame_index]
    sprites = {(sprite.group, sprite.image): sprite for sprite in character.sprites}
    sprite = sprites[(frame.group, frame.image)]
    width = sprite.width
    padded_width = (width + 7) & 0xFFF8
    axis_x = frame.x - sprite.axis_x
    axis_y = frame.y - sprite.axis_y
    origin_x = (center_x - (axis_x + padded_width) if facing_left
                else center_x + axis_x)
    origin_y = FLOOR + axis_y
    origin_x = (origin_x + 4) & 0xFFF8
    origin_y = (origin_y + 4) & 0xFFF8
    flip_h = bool(frame.hflip) ^ facing_left
    flip_v = bool(frame.vflip)
    pixels: dict[tuple[int, int], bytearray] = defaultdict(lambda: bytearray(64))

    for source_y in range(sprite.height):
        y = origin_y + (sprite.height - 1 - source_y if flip_v else source_y)
        for source_x in range(width):
            palette_index = sprite.pixels[source_y * width + source_x]
            if palette_index == 0:
                continue
            x_offset = padded_width - 1 - source_x if flip_h else source_x
            x = origin_x + x_offset
            if not (0 <= x < 256 and 0 <= y < 192):
                continue
            cell = (x // 8, y // 8)
            pixels[cell][(y & 7) * 8 + (x & 7)] = palette_index

    return {cell: bytes(data) for cell, data in pixels.items() if any(data)}

def compose(p1: dict[tuple[int, int], bytes], p2: dict[tuple[int, int], bytes],
            source_slots: dict[int, int],
            mixed_slot: dict[int, int]) -> dict[tuple[int, int], tuple[bytes, int]]:
    zero = bytes(64)
    result: dict[tuple[int, int], tuple[bytes, int]] = {}
    for cell in set(p1) | set(p2):
        left = p1.get(cell, zero)
        right = p2.get(cell, zero)
        if cell not in p1:
            pixels = bytes(source_slots[index] if index else 0 for index in right)
            palette_flag = SPRITE_PALETTE_FLAG
        elif cell not in p2:
            pixels = bytes(source_slots[index] if index else 0 for index in left)
            palette_flag = 0
        else:
            pixels = bytes(source_slots[value] if value else
                           (mixed_slot[index] if index else 0)
                           for value, index in zip(left, right))
            palette_flag = 0
        if any(pixels):
            pattern, flips = canonical(pixels)
            result[cell] = (pattern, flips | palette_flag)
    return result

def orientations(pixels: bytes) -> tuple[tuple[bytes, int], ...]:
    return tuple(
        (bytes(pixels[(7 - y if vertical else y) * 8 +
                      (7 - x if horizontal else x)]
               for y in range(8) for x in range(8)),
         (0x0200 if horizontal else 0) | (0x0400 if vertical else 0))
        for vertical in (0, 1) for horizontal in (0, 1)
    )

def canonical(pixels: bytes) -> tuple[bytes, int]:
    return min(orientations(pixels), key=lambda item: (item[0], item[1]))

def pnt_transition(before: list[int], after: list[int], payload: bytearray) -> tuple[list[dict], dict]:
    changed = [index for index, pair in enumerate(zip(before, after))
               if pair[0] != pair[1]]
    runs: list[tuple[int, int]] = []
    if changed:
        start = last = changed[0]
        for index in changed[1:]:
            if index - last <= 2:
                last = index
            else:
                runs.append((start, last + 1))
                start = last = index
        runs.append((start, last + 1))
    split: list[tuple[int, int]] = []
    for start, end in runs:
        while end - start > 120:
            split.append((start, start + 120))
            start += 120
        split.append((start, end))

    writes = []
    for start, end in split:
        source_offset = len(payload)
        payload.extend(b"".join(struct.pack("<H", word) for word in after[start:end]))
        writes.append({"index": start, "count": end - start,
                       "source_offset": source_offset,
                       "bytes": (end - start) * 2})
    return writes, {
        "changed_entries": len(changed),
        "runs": len(writes),
        "data_bytes": sum(item["bytes"] for item in writes),
        "bytes_with_vdp_address": sum(item["bytes"] + 2 for item in writes),
    }

def save_expected(name: str, frame: dict[tuple[int, int], tuple[bytes, int]],
                  p1_palette: list[int], p2_palette: list[int],
                  marker: bytes, output: Path) -> None:
    from PIL import Image

    p1_colors = [word_rgb(word) for word in p1_palette]
    p2_colors = [word_rgb(word) for word in p2_palette]
    image = Image.new("RGB", (256, 192), p1_colors[0])
    pixels = image.load()
    for (col, row), (pattern, flags) in frame.items():
        palette = p2_colors if flags & SPRITE_PALETTE_FLAG else p1_colors
        for y in range(8):
            sy = 7 - y if flags & 0x0400 else y
            for x in range(8):
                sx = 7 - x if flags & 0x0200 else x
                pixels[col * 8 + x, row * 8 + y] = palette[pattern[sy * 8 + sx]]
    image.save(output / f"{name}.png")
    marked = image.copy()
    mp = marked.load()
    for y in range(8):
        for x in range(8):
            mp[MARKER_COL * 8 + x, MARKER_ROW * 8 + y] = p1_colors[marker[y * 8 + x]]
    marked.save(output / f"{name}_marker_on.png")

def encode_sms_tile(pixels: bytes) -> bytes:
    if len(pixels) != 64:
        raise ValueError(f"pixel tile must have 64 values, got {len(pixels)}")
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            value = pixels[y * 8 + x]
            if value > 15:
                raise ValueError(f"invalid SMS color index {value}")
            bit = 7 - x
            for plane in range(4):
                out[y * 4 + plane] |= ((value >> plane) & 1) << bit
    return bytes(out)
