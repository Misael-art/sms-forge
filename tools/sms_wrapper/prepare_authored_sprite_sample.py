#!/usr/bin/env python3
"""Prepare authored indexed poses through the existing SMS converters.

This adapter draws no character pixels and builds no ROM. It accepts explicit,
hash-bound native PNGs, crops only transparent margins, applies display_fit,
uses sms_tiles' common subpalette and the reference runtime's tall-pair format.
The real consumer is built separately by build_inner.py, with its pre-gates.

v1 freezes Social's six-pose diagnostic contract. v2 accepts explicit action
IDs/durations, a common roster scale, layout/facing and optional source-index
material codes. Explicit v2 sprite_size=8x8 uses the existing normal packer;
defaults remain tall and byte-stable. Overrides are scoped by PNG SHA/config, never by a
character name; shared indices must be reviewed in every affected material.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mugen2sms.converters.display_fit import (  # noqa: E402
    resolve_display_fit, sat_row_peak, scale_sprite,
)
from mugen2sms.converters.sms_tiles import _subpalette  # noqa: E402
from mugen2sms.converters.sms_tiles import to_sms_pose  # noqa: E402
from mugen2sms.generators.runtime_format import pack_tiles_tall, build_frames  # noqa: E402
from mugen2sms.generators.scene_cut import _remap_blob, _compact_facing_pose  # noqa: E402
from mugen2sms.parsers.sff import Sprite  # noqa: E402
from pack_sms_metasprite import (  # noqa: E402
    header_text, safe_sprite_pattern_capacity, pack_poses,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_native(recipe_path: Path, output: Path) -> dict:
    """One declared raw-raster registration; never an artistic pass verdict."""
    recipe = json.loads(recipe_path.read_text())
    raw = recipe_path.parent / recipe['source']
    if sha(raw) != recipe['source_sha256']:
        raise ValueError('raw source SHA mismatch')
    image = Image.open(raw).convert('RGBA')
    if list(image.size) != recipe['raw_size']:
        raise ValueError('raw raster dimensions changed')
    native = []
    scale_num, scale_den = recipe['scale']
    for spec in recipe['frames']:
        rect = spec['rect']
        crop = image.crop(rect)
        crop.putalpha(crop.getchannel('A').point(
            lambda value: 255 if value >= recipe['alpha_threshold'] else 0))
        size = (round(crop.width * scale_num / scale_den),
                round(crop.height * scale_num / scale_den))
        crop = crop.resize(size, Image.Resampling.NEAREST)
        canvas = Image.new('RGBA', tuple(recipe['canvas']))
        origin_x, origin_y = spec['cell_origin']
        left = recipe['pivot'][0] + round((rect[0] - origin_x - spec['raw_pivot'][0]) * scale_num / scale_den)
        top = recipe['pivot'][1] + round((rect[1] - origin_y - spec['raw_pivot'][1]) * scale_num / scale_den)
        if left < 0 or top < 0 or left + crop.width > canvas.width or top + crop.height > canvas.height:
            raise ValueError('registration would crop the native source')
        canvas.paste(crop, (left, top))
        native.append(canvas)
    # A single shared source palette, independent of the later SMS palette.
    # Transparent RGB is deliberately excluded from the quantizer's input.
    opaque = [rgb[:3] for im in native for rgb in im.getdata() if rgb[3] == 255]
    strip = Image.new('RGB', (len(opaque), 1))
    strip.putdata(opaque)
    if 'source_palette_rgb' in recipe:
        colors = recipe['source_palette_rgb']
        if (not 1 <= len(colors) <= 254 or any(len(c) != 3 or
                any(type(v) is not int or not 0 <= v <= 255 for v in c) for c in colors)):
            raise ValueError('invalid authored source palette')
        source_palette = [channel for rgb in colors for channel in rgb]
    else:
        palette_im = strip.quantize(colors=recipe['source_colors'], dither=Image.Dither.NONE)
        source_palette = palette_im.getpalette()[:recipe['source_colors'] * 3]
    palette_ref = Image.new('P', (1, 1))
    # Pillow requires a 256-entry palette; repeat a real color for unused slots.
    palette_ref.putpalette(source_palette + source_palette[:3] * (256 - len(source_palette) // 3))
    output.mkdir(parents=True, exist_ok=True)
    columns = recipe.get('sheet_columns', 3)
    if type(columns) is not int or not 1 <= columns <= 16:
        raise ValueError('sheet_columns must be an integer in 1..16')
    rows = max(2 if 'sheet_columns' not in recipe else 1,
               (len(native) + columns - 1) // columns)
    sheet = Image.new('P', (recipe['canvas'][0] * columns, recipe['canvas'][1] * rows))
    final_palette = [0, 0, 0] + source_palette
    final_palette += [0] * (768 - len(final_palette))
    sheet.putpalette(final_palette)
    records = []
    for n, (spec, im) in enumerate(zip(recipe['frames'], native)):
        path = output / f'{spec["id"]}.png'
        if path.exists():
            raise FileExistsError('preserving existing native source')
        colors = im.convert('RGB').quantize(palette=palette_ref, dither=Image.Dither.NONE)
        indices = bytes(index + 1 if alpha == 255 else 0 for index, alpha in
                        zip(colors.tobytes(), im.getchannel('A').tobytes()))
        result = Image.frombytes('P', im.size, indices)
        result.putpalette(final_palette)
        result.save(path, transparency=0, bits=8)
        sheet.paste(result, ((n % columns) * im.width, (n // columns) * im.height))
        records.append({'id': spec['id'], 'path': str(path), 'sha256': sha(path)})
    filename = recipe.get('sheet_filename', 'jab_source.png')
    if Path(filename).name != filename or not filename.endswith('.png'):
        raise ValueError('sheet_filename must be a local PNG filename')
    sheet_path = output.parent / filename
    if sheet_path.exists():
        raise FileExistsError('preserving existing native sheet')
    sheet.save(sheet_path, transparency=0, bits=8)
    return {'schema': 'sms_native_source_extraction_v1', 'recipe_sha256': sha(recipe_path),
            'source_sha256': sha(raw), 'frames': records, 'sheet_sha256': sha(sheet_path),
            'status': 'candidate_requires_artistic_review',
            'artistic_pixel_edits': [], 'source_colors': len(source_palette) // 3}


def load_pose(root: Path, spec: dict) -> Sprite:
    path = (root / spec['path']).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('source PNG must stay within declared source root')
    if sha(path) != spec['sha256']:
        raise ValueError(f'source SHA mismatch: {path}')
    with Image.open(path) as original:
        if original.mode != 'P' or original.info.get('transparency') != 0:
            raise ValueError('native source must be indexed with only index 0 transparent')
        original.load()
        bbox = original.convert('RGBA').getbbox()
        if not bbox:
            raise ValueError('empty source pose')
        image = original.crop(bbox)
        flat = image.getpalette()
        palette = [tuple(flat[i:i + 3]) for i in range(0, len(flat), 3)]
        palette += [(0, 0, 0)] * (256 - len(palette))
    px, py = spec['pivot']
    return Sprite(0, 0, px - bbox[0], py - bbox[1], image.width, image.height,
                  image.tobytes(), palette, False, None, 0)


def convert_poses(sprites: list[Sprite], extra: tuple[int, int] | None = None):
    fit = resolve_display_fit('pose_budget', 'cps2', 'sms')
    fitted = [scale_sprite(sp, fit)[0] for sp in sprites]
    columns = sat_row_peak(fitted[0])
    # Same policy as display_fit.decide_pose_scale: idle alone sets scale.
    # A wide attack never shrinks the body. The final pair is audited below.
    num, den = extra or ((4, columns) if columns > 4 else (1, 1))
    if min(num, den) <= 0 or num > den:
        raise ValueError('extra scale must be in (0,1]')
    if num != den:
        second = replace(fit, scale_num_x=num, scale_den_x=den,
                         scale_num_y=num, scale_den_y=den, pose_budget=False)
        fitted = [scale_sprite(sp, second)[0] for sp in fitted]
    return fitted, {'framebuffer': fit.to_dict(), 'extra': [num, den],
                    'neutral_columns_before_extra': columns,
                    'neutral_columns_after_extra': sat_row_peak(fitted[0])}


def pack_registered_sprite(sprite: Sprite, codebook: list[int], name: str,
                           phase=(0, 0)):
    """Move the hardware grid, never the visible bitmap or its source pivot.

    Transparent left/top padding selects the 8x16 cell phase. The caller must
    subtract that padding from META placement. The canonical tall encoder,
    palette mapper and nonblank-cell policy remain responsible for all bytes.
    This can reduce interval overlap, but cannot legalize truly wide pixels.
    """
    if (not isinstance(phase, (list, tuple)) or len(phase) != 2 or
            any(type(v) is not int for v in phase) or
            not 0 <= phase[0] < 8 or not 0 <= phase[1] < 16):
        raise ValueError('packing_phase_px must contain x=0..7, y=0..15 integers')
    px, py = phase
    if px or py:
        width = sprite.width + px
        pixels = bytearray(width * (sprite.height + py))
        for y in range(sprite.height):
            offset = (y + py) * width + px
            pixels[offset:offset + sprite.width] = sprite.pixels[y * sprite.width:(y + 1) * sprite.width]
        sprite = replace(sprite, width=width, height=sprite.height + py,
                         pixels=bytes(pixels), axis_x=sprite.axis_x + px,
                         axis_y=sprite.axis_y + py)
    pose = to_sms_pose(sprite)
    blob, _ = pack_tiles_tall(pose)
    blob = _remap_blob(blob, bytes(pose.palette), codebook, 0)
    metadata = build_frames(pose, omit_blank_cells=True)
    blob, metadata = _compact_facing_pose(blob, metadata, name)
    return blob, metadata, (-px, -py)


def map_source_indices(sprite: Sprite, codebook: list[int], overrides: dict | None = None):
    """Map original indexed colors once into the shared P1.

    Explicit source-index roles resolve measured hue drift near SMS rounding
    boundaries. They never edit the source PNG, alpha, geometry or reduced
    output. A shared source index still needs review in every material using it.
    """
    from mugen2sms.generators.scene_cut import _nearest_word, _assign_index
    overrides = {} if overrides is None else overrides
    if not isinstance(overrides, dict):
        raise ValueError('palette_index_codes must be an object')
    targets = {}
    for key, word in overrides.items():
        if (not isinstance(key, str) or not key.isdecimal() or str(int(key)) != key
                or not 1 <= int(key) < len(sprite.palette)
                or type(word) is not int or word not in codebook):
            raise ValueError('palette_index_codes requires opaque source indices and exact shared P1 codes')
        targets[int(key)] = codebook.index(word)
    return bytes(0 if index == 0 else 1 + (targets[index] if index in targets else
                 _assign_index(_nearest_word(sprite.palette[index]), codebook))
                 for index in sprite.pixels)


def pack_registered_eight(paths, phases, output: Path, capacity: int):
    """Use the existing 8x8 packer; translate its grid, never visible pixels.

    Packing PNGs are explicit intermediates. The public converted PNGs retain
    their original canvas/pivot. Only transparent margins are omitted here.
    """
    if not paths or len(paths) != len(phases):
        raise ValueError('8x8 packing needs one phase per pose')
    images = []
    for (name, path), phase in zip(paths, phases):
        if (not isinstance(phase, (list, tuple)) or len(phase) != 2 or
                any(type(n) is not int or not 0 <= n < 8 for n in phase)):
            raise ValueError('8x8 packing_phase_px needs x/y=0..7 integers')
        with Image.open(path) as original:
            image = original.copy()
        bbox = image.getbbox()  # indexed zero alone is transparent
        if not bbox:
            raise ValueError('8x8 packing cannot consume an empty pose')
        images.append((name, image, bbox, phase))
    width = max((bbox[2] + phase[0] + 7) // 8 * 8
                for _, _, bbox, phase in images)
    height = max((bbox[3] + phase[1] + 7) // 8 * 8
                 for _, _, bbox, phase in images)
    if width > 128 or height > 128:
        raise ValueError('8x8 packing canvas exceeds unsigned sample offsets')
    packing_dir = output / 'packing_8x8'
    packing_dir.mkdir()
    packing_paths = []
    for name, image, bbox, (px, py) in images:
        padded = Image.new('P', (width, height))
        padded.putpalette(image.getpalette())
        padded.paste(image.crop(bbox), (bbox[0] + px, bbox[1] + py))
        path = packing_dir / f'{name}.png'
        padded.save(path, transparency=0, bits=8)
        packing_paths.append((name, path))
    packed = pack_poses(packing_paths, reserve_blank=True, max_patterns=capacity)
    for pose, (_, _, _, (px, py)) in zip(packed['poses'], images):
        meta = []
        for obj in pose['objects']:
            obj['x'] -= px
            obj['y'] -= py
            if not (0 <= obj['x'] < 128 and 0 <= obj['y'] < 128):
                raise ValueError('packing phase requires signed offsets unsupported by sample emitter')
            meta.extend((obj['x'], obj['y'], obj['tile']))
        pose['meta'] = meta + [128]
        pose['counts'] = [sum(obj['y'] <= line < obj['y'] + 8
                              for obj in pose['objects']) for line in range(192)]
        pose['peak_scanline'] = max(pose['counts'])
    return packed


def pack_resident_tall(encoded, codebook, capacity):
    """Unchanged tall-pair residency policy shared by v1/v2 defaults."""
    pool = bytearray(64)
    pair_ids = {bytes(64): 0}
    packed_poses = []
    for name, blob, meta, left, top in encoded:
        rewritten, objects = [], []
        for n in range(0, len(meta) - 1, 3):
            pair = blob[meta[n + 2] * 32:meta[n + 2] * 32 + 64]
            if pair not in pair_ids:
                if len(pool) + 64 > capacity * 32:
                    raise ValueError('resident tall pairs exceed the physical sprite window')
                pair_ids[pair] = len(pool) // 32
                pool.extend(pair)
            x, y, tile = left + meta[n], top + meta[n + 1], pair_ids[pair]
            if not (0 <= x < 128 and 0 <= y < 128):
                raise ValueError('packing phase requires signed offsets unsupported by sample emitter')
            rewritten.extend([x, y, tile])
            objects.append({'x': x, 'y': y, 'tile': tile})
        if len(objects) > 64:
            raise ValueError('tall pose exceeds SAT capacity')
        packed_poses.append({'name': name, 'meta': rewritten + [128], 'objects': objects,
                             'tile_map': [o['tile'] for o in objects]})
    return {'tile_base': 0, 'loaded_patterns': len(pool) // 32, 'tile_bytes': bytes(pool),
            'palette_codes': ([0] + codebook + [0] * 16)[:16], 'poses': packed_poses}


def prepare(config_path: Path, output: Path) -> dict:
    cfg = json.loads(config_path.read_text())
    version = cfg.get('schema')
    if version not in ('sms_authored_sprite_sample_v1', 'sms_authored_sprite_sample_v2'):
        raise ValueError('expected sms_authored_sprite_sample_v1 or v2')
    sprite_size = cfg.get('sprite_size', '8x16')
    if sprite_size not in ('8x16', '8x8') or (version.endswith('v1') and sprite_size != '8x16'):
        raise ValueError('sprite_size must be 8x16, or explicit v2 opt-in 8x8')
    sprite_height = 8 if sprite_size == '8x8' else 16
    if output.exists():
        raise FileExistsError('preserving sealed output; choose a new candidate destination')
    root = (config_path.parent / cfg.get('project_root', '.')).resolve()
    if not config_path.resolve().is_relative_to(root):
        raise ValueError('config must stay inside declared project root')
    specs = cfg['poses']
    if version.endswith('v1') and (
            [p['id'] for p in specs] != ['idle', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06']
            or cfg['durations'] != [2, 1, 1, 1, 1, 3]):
        raise ValueError('sample must preserve the six approved jab IDs and proposed timing')
    if version.endswith('v2'):
        ids = [p['id'] for p in specs]
        durations = cfg['durations']
        if (not 1 <= len(ids) <= 32 or ids[0] != 'idle' or len(set(ids)) != len(ids)
                or any(not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*', name)
                       or name == 'reference' for name in ids)
                or len(durations) != len(ids) - 1
                or any(type(n) is not int or not 1 <= n <= 255 for n in durations)):
            raise ValueError('v2 requires idle, unique C identifiers and one 1..255 duration per action pose')
        if 'extra_scale' not in cfg:
            raise ValueError('v2 requires explicit common roster extra_scale')
    sources = [load_pose(root, sp) for sp in specs]
    fitted, fit_report = convert_poses(sources, tuple(cfg['extra_scale']) if
                                     version.endswith('v2') else None)
    ref = cfg['reference']
    reference = load_pose(root, ref)
    refs, ref_fit = convert_poses([reference], tuple(ref['extra_scale']))
    # Flip original indexed source before packing; no recoloring of SMS output.
    def facing(sprite, flip):
        if type(flip) is not bool:
            raise ValueError('flip flags must be booleans')
        if not flip:
            return sprite
        rows = [sprite.pixels[y * sprite.width:(y + 1) * sprite.width][::-1]
                for y in range(sprite.height)]
        return replace(sprite, pixels=b''.join(rows),
                       axis_x=sprite.width - 1 - sprite.axis_x)
    fitted = [facing(sp, cfg.get('flip_actor', False)) for sp in fitted]
    reference = facing(refs[0], cfg.get('flip_reference', True))
    all_sprites = fitted + [reference]
    # sms_tiles owns the mapping. Balance each actor's contribution, so six
    # source drawings cannot silently consume the reference actor's colors.
    merged_palette = [(0, 0, 0)]
    color_index = {}
    weighted_pixels = bytearray()
    for n, sprite in enumerate(all_sprites):
        data = bytearray()
        for index in sprite.pixels:
            if index == 0:
                data.append(0)
                continue
            rgb = sprite.palette[index]
            if rgb not in color_index:
                if len(merged_palette) == 256:
                    raise ValueError('combined source exceeds 255 colors; provide an authored palette')
                color_index[rgb] = len(merged_palette)
                merged_palette.append(rgb)
            data.append(color_index[rgb])
        weighted_pixels.extend(data * (len(fitted) if n == len(fitted) else 1))
    palette_sprite = replace(fitted[0], pixels=bytes(weighted_pixels), palette=merged_palette)
    words, _ = _subpalette(palette_sprite)
    # Feed the same palette contract back into the existing mapper by making
    # each sample contain the same codebook colors. No filter or cleanup pass.
    codebook = cfg.get('shared_palette_codes', words[1:])
    if (not codebook or len(codebook) > 15 or len(set(codebook)) != len(codebook)
            or any(type(word) is not int or not 0 <= word <= 63 for word in codebook)):
        raise ValueError('shared P1 must contain 1..15 distinct SMS codes')
    rgb_palette = [(0, 0, 0)] + [((v & 3) * 85, ((v >> 2) & 3) * 85,
                                ((v >> 4) & 3) * 85) for v in codebook]
    width, height = cfg.get('canvas_px', [64, 80]) if version.endswith('v2') else (64, 80)
    pivot = tuple(cfg.get('pivot_px', [24, 72])) if version.endswith('v2') else (24, 72)
    positions_cfg = cfg.get('positions', [[40, 72], [152, 72]]) if version.endswith('v2') else [[40, 72], [152, 72]]
    if (any(type(n) is not int or n < 8 or n > 128 or n % 8 for n in (width, height))
            or len(pivot) != 2 or any(type(n) is not int for n in pivot)
            or not 0 <= pivot[0] < width or not 0 <= pivot[1] <= height
            or len(positions_cfg) != 2 or any(len(p) != 2 for p in positions_cfg)
            or any(type(n) is not int or not 0 <= n < 192 for p in positions_cfg for n in p)):
        raise ValueError('invalid tile-aligned canvas, pivot or actor positions')
    output.mkdir(parents=True)
    paths, frames, encoded = [], [], []
    for spec, sprite in zip(specs + [dict(ref, id='reference')], all_sprites):
        name = spec['id']
        indices = map_source_indices(sprite, codebook, spec.get('palette_index_codes'))
        left, top = pivot[0] - sprite.axis_x, pivot[1] - sprite.axis_y
        if min(left, top) < 0 or left + sprite.width > width or top + sprite.height > height:
            raise ValueError(f'{name}: converted canvas would crop equipment or body')
        im = Image.new('P', (width, height))
        flat = [c for rgb in rgb_palette for c in rgb]
        im.putpalette(flat + [0] * (768 - len(flat)))
        small = Image.frombytes('P', (sprite.width, sprite.height), indices)
        small.putpalette(im.getpalette())
        im.paste(small, (left, top))
        expected_bottom = spec.get('expected_opaque_bottom_px')
        if expected_bottom is not None:
            if (type(expected_bottom) is not int or not 1 <= expected_bottom <= height):
                raise ValueError(f'{name}: expected_opaque_bottom_px must be inside the canvas')
            actual_bottom = im.getbbox()[3]
            if actual_bottom != expected_bottom:
                raise ValueError(f'{name}: opaque bottom {actual_bottom} != expected {expected_bottom}; recheck source registration')
        path = output / f'{name}.png'
        im.save(path, transparency=0, bits=8)
        paths.append((name, path))
        frames.append({'id': name, 'path': str(path), 'sha256': sha(path),
                       'dimensions_before_canvas': [sprite.width, sprite.height],
                       'pivot_before_canvas': [sprite.axis_x, sprite.axis_y],
                       'placement': [left, top], 'peak_tall': sat_row_peak(sprite)})
        if spec.get('palette_index_codes'):
            frames[-1]['palette_index_codes'] = spec['palette_index_codes']
        if sprite_height == 8:
            continue
        # Keep each cropped pose's hardware grid, then translate its metadata
        # to the common pivot. Padding the bitmap before packing adds a fifth
        # cell at unaligned margins and differs from the reference recipe.
        sms_sprite = replace(sprite, pixels=indices, palette=rgb_palette +
                             [(0, 0, 0)] * (256 - len(rgb_palette)))
        phase = spec.get('packing_phase_px', [0, 0])
        blob, metadata, (dx, dy) = pack_registered_sprite(sms_sprite, codebook, name, phase)
        rows = [metadata[n + 1] + dy for n in range(0, len(metadata) - 1, 3)]
        if not rows:
            raise ValueError(f'{name}: conversion has no occupied sprite cells')
        frames[-1].update(packing_phase_px=list(phase),
                         source_grid_peak_tall=frames[-1]['peak_tall'],
                         peak_tall=max(sum(y <= line < y + 16 for y in rows)
                                       for line in range(min(rows), max(rows) + 16)))
        encoded.append((name, blob, metadata, left + dx, top + dy))
    # All eight poses remain resident, no streaming or deadline proxy. Reuse
    # the canonical tall pair encoder/compactor; this is just static residency.
    capacity = safe_sprite_pattern_capacity(0, 0x0000, 0x3800)
    if sprite_height == 8:
        phases = [s.get('packing_phase_px', [0, 0]) for s in specs + [ref]]
        packed = pack_registered_eight(paths, phases, output, capacity)
        for frame, pose, phase in zip(frames, packed['poses'], phases):
            frame['source_grid_peak_tall'] = frame.pop('peak_tall')
            frame.update(packing_phase_px=list(phase), peak_8x8=pose['peak_scanline'])
    else:
        packed = pack_resident_tall(encoded, codebook, capacity)
    header = output / 'sample_data.h'
    header.write_text(header_text(packed, 'sample'))
    positions = [tuple(positions_cfg[0])] * len(fitted) + [tuple(positions_cfg[1])]
    reference_objects = packed['poses'][-1]['objects']
    compositions = []
    for pose in packed['poses'][:-1]:
        objects = ([{'x': positions[0][0] + o['x'], 'y': positions[0][1] + o['y'], 'tile': o['tile']}
                    for o in pose['objects']] +
                   [{'x': positions[-1][0] + o['x'], 'y': positions[-1][1] + o['y'], 'tile': o['tile']}
                    for o in reference_objects])
        scene = {'schema': 'sprite_scene_manifest_v1', 'sprite_size': sprite_size,
                 'zoomed': False, 'screen_h': 192, 'sprites': objects}
        scene_path = output / f'scene_{pose["name"]}.json'
        scene_path.write_text(json.dumps(scene, indent=2) + '\n')
        peak = max(sum(o['y'] <= line < o['y'] + sprite_height for o in objects) for line in range(192))
        visible = all(0 <= o['x'] <= 248 and 0 <= o['y'] <= 192 - sprite_height and o['y'] != 0xD0
                      for o in objects)
        compositions.append({'id': pose['name'], 'sat': len(objects), 'peak': peak,
                             'scene': str(scene_path), 'legal': peak <= 8 and len(objects) <= 64 and visible})
    report = {'schema': 'sms_authored_sprite_sample_conversion_v1', 'status': 'converted_candidate',
              'config_sha256': sha(config_path), 'source_specs': specs,
              'scale': fit_report, 'reference_scale': ref_fit,
              'source_to_sms': 'display_fit.scale_sprite + sms_tiles + runtime_format.pack_tiles_tall/build_frames + scene_cut._remap_blob/_compact_facing_pose',
              'palette_codes': [0] + codebook,
              'palette_policy': ('explicit shared material palette' if 'shared_palette_codes' in cfg else
                                 'one shared P1; both actors influence frequency codebook'),
              'packing_phase_policy': 'explicit transparent padding compensated in META; PNG, scale and pivot unchanged',
              'canvas': [width, height], 'pivot': list(pivot), 'positions': positions,
              'frames': frames, 'compositions': compositions,
              'patterns': packed['loaded_patterns'], 'vram_pattern_bytes': len(packed['tile_bytes']),
              'resident_window': '0x0000..0x1FFF (256 patterns, blank pair included); PNT 0x3800; SAT 0x3F00; BG blank tile 0 shared',
              'header': str(header), 'header_sha256': sha(header),
              'art_approval': 'pending', 'runtime_timing': 'unmeasured', 'worst_vblank': 'unmeasured'}
    if sprite_height == 8:
        report.update(sprite_size=sprite_size,
                      source_to_sms='display_fit.scale_sprite + sms_tiles shared P1 + pack_sms_metasprite.pack_poses (8x8)',
                      resident_window='0x0000..0x1FFF (256 patterns, one blank tile included); PNT 0x3800; SAT 0x3F00; BG blank tile 0 shared',
                      packing_input_canvas=[packed['width'], packed['height']])
    (output / 'conversion.json').write_text(json.dumps(report, indent=2) + '\n')
    if not all(c['legal'] for c in compositions):
        raise ValueError('pair composition exceeds physical limits; see preserved conversion.json; do not build this pair')
    with header.open('a') as stream:
        stream.write(f'\nconst unsigned char * const sample_poses[{len(specs)}] = {{' +
                     ','.join(f'sample_{s["id"]}_meta' for s in specs) + '};\n')
        stream.write(f'const unsigned char sample_durations[{len(specs)}] = {{0' +
                     ''.join(f',{n}' for n in cfg['durations']) + '};\n')
        if version.endswith('v2'):
            stream.write(f'#define SAMPLE_POSE_COUNT {len(specs)}u\n')
            if sprite_height == 8:
                stream.write('#define SAMPLE_SPRITE_HEIGHT 8u\n')
            for name, point in zip(('ACTOR', 'REFERENCE'), positions_cfg):
                stream.write(f'#define SAMPLE_{name}_X {point[0]}u\n#define SAMPLE_{name}_Y {point[1]}u\n')
    report['header_sha256'] = sha(header)
    (output / 'conversion.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def phase_self_check():
    """Decode emitted pairs independently of the source registration math."""
    from mugen2sms.generators.runtime_format import decode_indices
    width, height = 40, 16
    pixels = bytes((1 + (x + y) % 3) if (x < 24 if y < 8 else x >= 16) else 0
                   for y in range(height) for x in range(width))
    palette = [(0, 0, 0), (0, 0, 0), (255, 255, 255), (255, 0, 0)]
    sprite = Sprite(0, 0, 20, 16, width, height, pixels,
                    palette + [(0, 0, 0)] * 252, False, None, 0)
    codebook = [0, 63, 3]
    expected = {(x, y): codebook[pixels[y * width + x] - 1]
                for y in range(height) for x in range(width) if pixels[y * width + x]}
    peaks = {}
    for px in range(8):
        for py in range(16):
            blob, meta, (dx, dy) = pack_registered_sprite(sprite, codebook, 'fixture', [px, py])
            actual, rows = {}, []
            for n in range(0, len(meta) - 1, 3):
                x, y, tile = meta[n] + dx, meta[n + 1] + dy, meta[n + 2]
                rows.append(y)
                pair = blob[tile * 32:tile * 32 + 64]
                decoded = decode_indices(pair[:32]) + decode_indices(pair[32:])
                for offset, index in enumerate(decoded):
                    if index:
                        point = (x + offset % 8, y + offset // 8)
                        assert point not in actual  # no opaque overlap/duplication
                        actual[point] = codebook[index - 1]
            assert actual == expected  # includes every opaque black pixel
            peaks[px, py] = max(sum(y <= line < y + 16 for y in rows)
                                for line in range(min(rows), max(rows) + 16))
    assert peaks[0, 0] == 5 and peaks[0, 8] == 3
    for bad in ([8, 0], [0, 16], [-1, 0], [True, 0], [0], None):
        try:
            pack_registered_sprite(sprite, codebook, 'fixture', bad)
        except ValueError:
            pass
        else:
            raise AssertionError('invalid grid phase accepted')


def eight_self_check():
    """Reconstruct all 64 grids from emitted planar data, opaque black too."""
    import tempfile
    from mugen2sms.generators.runtime_format import decode_indices
    with tempfile.TemporaryDirectory(prefix='sms-authored-eight-') as tmp:
        root = Path(tmp)
        image = Image.new('P', (32, 32))
        image.putpalette([0, 0, 0, 0, 0, 0, 255, 255, 255] + [0] * 759)
        for y in range(11, 27):
            for x in range(10, 24):
                if (x + y) % 5:
                    image.putpixel((x, y), 1 if x < 17 else 2)
        path = root / 'fixture.png'
        image.save(path, transparency=0)
        expected = image.tobytes()
        for px in range(8):
            for py in range(8):
                output = root / f'p{px}_{py}'
                output.mkdir()
                packed = pack_registered_eight([('fixture', path)], [[px, py]], output, 256)
                actual = bytearray(32 * 32)
                for obj in packed['poses'][0]['objects']:
                    tile = obj['tile']
                    pixels = decode_indices(packed['tile_bytes'][tile * 32:tile * 32 + 32])
                    for offset, index in enumerate(pixels):
                        if index:
                            point = (obj['y'] + offset // 8) * 32 + obj['x'] + offset % 8
                            assert not actual[point]
                            actual[point] = index
                assert bytes(actual) == expected
                assert packed['palette_codes'][1] == 0  # opaque black, not omitted
        output = root / 'capacity'
        output.mkdir()
        try:
            pack_registered_eight([('fixture', path)], [[0, 0]], output, 1)
        except ValueError:
            pass
        else:
            raise AssertionError('8x8 physical pattern limit not enforced')


def self_check() -> int:
    phase_self_check()
    eight_self_check()
    material = Sprite(0, 0, 0, 1, 3, 1, bytes([0, 1, 2]),
                      [(0, 0, 0), (223, 216, 212), (43, 25, 33)] + [(0, 0, 0)] * 253,
                      False, None, 0)
    assert map_source_indices(material, [0, 21, 42, 47, 1]) == bytes([0, 4, 5])
    assert map_source_indices(material, [0, 21, 42, 47, 1], {'1': 42, '2': 0}) == bytes([0, 3, 1])
    sp = Sprite(0, 0, 12, 64, 24, 64, bytes([1]) * (24 * 64),
                [(0, 0, 0)] * 256, False, None, 0)
    fitted, report = convert_poses([sp])
    words, remap = _subpalette(fitted[0])
    assert words[1] == 0 and remap[1] == 1  # opaque black stays visible
    pose = to_sms_pose(fitted[0])
    blob, _ = pack_tiles_tall(pose)
    meta = build_frames(pose, omit_blank_cells=True)
    compact, rewritten = _compact_facing_pose(
        _remap_blob(blob, bytes(pose.palette), words[1:], 0), meta, 'selfcheck')
    assert compact and len(compact) % 64 == 0 and rewritten[-1] == 128
    assert report['extra'] == [1, 1]
    assert safe_sprite_pattern_capacity(0, 0, 0x3800) == 256
    assert safe_sprite_pattern_capacity(0, 0x2000, 0x3800) == 192
    try:
        convert_poses([sp], (2, 1))
    except ValueError:
        pass
    else:
        raise AssertionError('invalid extra scale was accepted')
    print('[SELF-CHECK OK] authored source adapter: 128tall+64normal grids render exact, canonical8x8 packer, source material mapping, opaque black, capacity, scale rejection')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--config', type=Path)
    group.add_argument('--extract-config', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--self-check', action='store_true')
    args = parser.parse_args()
    if args.self_check:
        return self_check()
    if not args.out or not (args.config or args.extract_config):
        parser.error('--out and one config are required')
    if args.extract_config:
        print(json.dumps(extract_native(args.extract_config.resolve(), args.out.resolve()), indent=2))
        return 0
    report = prepare(args.config.resolve(), args.out.resolve())
    print(json.dumps({'status': report['status'], 'patterns': report['patterns'],
                      'compositions': report['compositions']}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
