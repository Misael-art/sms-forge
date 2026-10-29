#!/usr/bin/env python3
"""Prepare authored indexed poses through the existing SMS converters.

This adapter draws no character pixels and builds no ROM. It accepts explicit,
hash-bound native PNGs, crops only transparent margins, applies display_fit,
uses sms_tiles' common subpalette and the reference runtime's tall-pair format.
The real consumer is built separately by build_inner.py, with its pre-gates.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
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
from pack_sms_metasprite import header_text, safe_sprite_pattern_capacity  # noqa: E402


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
    sheet = Image.new('P', (recipe['canvas'][0] * 3, recipe['canvas'][1] * 2))
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
        sheet.paste(result, ((n % 3) * im.width, (n // 3) * im.height))
        records.append({'id': spec['id'], 'path': str(path), 'sha256': sha(path)})
    sheet_path = output.parent / 'jab_source.png'
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


def prepare(config_path: Path, output: Path) -> dict:
    cfg = json.loads(config_path.read_text())
    if cfg.get('schema') != 'sms_authored_sprite_sample_v1':
        raise ValueError('expected sms_authored_sprite_sample_v1')
    if output.exists():
        raise FileExistsError('preserving sealed output; choose a new candidate destination')
    root = (config_path.parent / cfg.get('project_root', '.')).resolve()
    if not config_path.resolve().is_relative_to(root):
        raise ValueError('config must stay inside declared project root')
    specs = cfg['poses']
    if ([p['id'] for p in specs] != ['idle', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06']
            or cfg['durations'] != [2, 1, 1, 1, 1, 3]):
        raise ValueError('sample must preserve the six approved jab IDs and proposed timing')
    sources = [load_pose(root, sp) for sp in specs]
    fitted, fit_report = convert_poses(sources)
    ref = cfg['reference']
    reference = load_pose(root, ref)
    refs, ref_fit = convert_poses([reference], tuple(ref['extra_scale']))
    # The reference faces the candidate. Flip indices before packing, not in Z80.
    sp = refs[0]
    rows = [sp.pixels[y * sp.width:(y + 1) * sp.width][::-1]
            for y in range(sp.height)]
    reference = replace(sp, pixels=b''.join(rows), axis_x=sp.width - 1 - sp.axis_x)
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
    from mugen2sms.generators.scene_cut import _nearest_word, _assign_index
    codebook = cfg.get('shared_palette_codes', words[1:])
    if (not codebook or len(codebook) > 15 or len(set(codebook)) != len(codebook)
            or any(type(word) is not int or not 0 <= word <= 63 for word in codebook)):
        raise ValueError('shared P1 must contain 1..15 distinct SMS codes')
    rgb_palette = [(0, 0, 0)] + [((v & 3) * 85, ((v >> 2) & 3) * 85,
                                ((v >> 4) & 3) * 85) for v in codebook]
    width, height = 64, 80
    pivot = (24, 72)
    output.mkdir(parents=True)
    paths, frames, encoded = [], [], []
    for name, sprite in zip([p['id'] for p in specs] + ['reference'], all_sprites):
        indices = bytes(0 if i == 0 else
                        1 + _assign_index(_nearest_word(sprite.palette[i]), codebook)
                        for i in sprite.pixels)
        left, top = pivot[0] - sprite.axis_x, pivot[1] - sprite.axis_y
        if min(left, top) < 0 or left + sprite.width > width or top + sprite.height > height:
            raise ValueError(f'{name}: converted canvas would crop equipment or body')
        im = Image.new('P', (width, height))
        flat = [c for rgb in rgb_palette for c in rgb]
        im.putpalette(flat + [0] * (768 - len(flat)))
        small = Image.frombytes('P', (sprite.width, sprite.height), indices)
        small.putpalette(im.getpalette())
        im.paste(small, (left, top))
        path = output / f'{name}.png'
        im.save(path, transparency=0, bits=8)
        paths.append((name, path))
        frames.append({'id': name, 'path': str(path), 'sha256': sha(path),
                       'dimensions_before_canvas': [sprite.width, sprite.height],
                       'pivot_before_canvas': [sprite.axis_x, sprite.axis_y],
                       'placement': [left, top], 'peak_tall': sat_row_peak(sprite)})
        # Keep each cropped pose's hardware grid, then translate its metadata
        # to the common pivot. Padding the bitmap before packing adds a fifth
        # cell at unaligned margins and differs from the reference recipe.
        sms_sprite = replace(sprite, pixels=indices, palette=rgb_palette +
                             [(0, 0, 0)] * (256 - len(rgb_palette)))
        sms_pose = to_sms_pose(sms_sprite)
        blob, _ = pack_tiles_tall(sms_pose)
        blob = _remap_blob(blob, bytes(sms_pose.palette), codebook, 0)
        metadata = build_frames(sms_pose, omit_blank_cells=True)
        blob, metadata = _compact_facing_pose(blob, metadata, name)
        encoded.append((name, blob, metadata, left, top))
    # All eight poses remain resident, no streaming or deadline proxy. Reuse
    # the canonical tall pair encoder/compactor; this is just static residency.
    capacity = safe_sprite_pattern_capacity(0, 0x0000, 0x3800)
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
            rewritten.extend([x, y, tile])
            objects.append({'x': x, 'y': y, 'tile': tile})
        if len(objects) > 64:
            raise ValueError('tall pose exceeds SAT capacity')
        packed_poses.append({'name': name, 'meta': rewritten + [128], 'objects': objects,
                             'tile_map': [o['tile'] for o in objects]})
    packed = {'tile_base': 0, 'loaded_patterns': len(pool) // 32, 'tile_bytes': bytes(pool),
              'palette_codes': ([0] + codebook + [0] * 16)[:16], 'poses': packed_poses}
    header = output / 'sample_data.h'
    header.write_text(header_text(packed, 'sample'))
    positions = [(40, 72)] * len(fitted) + [(152, 72)]
    reference_objects = packed['poses'][-1]['objects']
    compositions = []
    for pose in packed['poses'][:-1]:
        objects = ([{'x': 40 + o['x'], 'y': 72 + o['y'], 'tile': o['tile']}
                    for o in pose['objects']] +
                   [{'x': 152 + o['x'], 'y': 72 + o['y'], 'tile': o['tile']}
                    for o in reference_objects])
        scene = {'schema': 'sprite_scene_manifest_v1', 'sprite_size': '8x16',
                 'zoomed': False, 'screen_h': 192, 'sprites': objects}
        scene_path = output / f'scene_{pose["name"]}.json'
        scene_path.write_text(json.dumps(scene, indent=2) + '\n')
        peak = max(sum(o['y'] <= line < o['y'] + 16 for o in objects) for line in range(192))
        compositions.append({'id': pose['name'], 'sat': len(objects), 'peak': peak,
                             'scene': str(scene_path), 'legal': peak <= 8 and len(objects) <= 64})
    report = {'schema': 'sms_authored_sprite_sample_conversion_v1', 'status': 'converted_candidate',
              'config_sha256': sha(config_path), 'source_specs': specs,
              'scale': fit_report, 'reference_scale': ref_fit,
              'source_to_sms': 'display_fit.scale_sprite + sms_tiles + runtime_format.pack_tiles_tall/build_frames + scene_cut._remap_blob/_compact_facing_pose',
              'palette_codes': [0] + codebook,
              'palette_policy': ('explicit shared material palette' if 'shared_palette_codes' in cfg else
                                 'one shared P1; both actors influence frequency codebook'),
              'canvas': [width, height], 'pivot': list(pivot), 'positions': positions,
              'frames': frames, 'compositions': compositions,
              'patterns': packed['loaded_patterns'], 'vram_pattern_bytes': len(packed['tile_bytes']),
              'resident_window': '0x0000..0x1FFF (256 patterns, blank pair included); PNT 0x3800; SAT 0x3F00; BG blank tile 0 shared',
              'header': str(header), 'header_sha256': sha(header),
              'art_approval': 'pending', 'runtime_timing': 'unmeasured', 'worst_vblank': 'unmeasured'}
    (output / 'conversion.json').write_text(json.dumps(report, indent=2) + '\n')
    if not all(c['legal'] for c in compositions):
        raise ValueError('pair composition exceeds physical limits; see preserved conversion.json; do not build this pair')
    with header.open('a') as stream:
        stream.write('\nconst unsigned char * const sample_poses[7] = {' +
                     ','.join(f'sample_{s["id"]}_meta' for s in specs) + '};\n')
        stream.write('const unsigned char sample_durations[7] = {0,2,1,1,1,1,3};\n')
    report['header_sha256'] = sha(header)
    (output / 'conversion.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def self_check() -> int:
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
    print('[SELF-CHECK OK] authored source adapter: opaque black, tall pairs, capacity, scale rejection')
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
