"""Contract/regression tests for the thin authored-PNG conversion adapter."""
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_authored_sprite_sample import (load_pose, convert_poses, prepare,
                                           extract_native, phase_self_check)


def fixture(tmp_path, opaque=1):
    # Deliberately asymmetric technical fixture; never a game-art asset.
    im = Image.new('P', (128, 128))
    im.putpalette([0, 0, 0, 0, 170, 255, 255, 255, 85] + [0] * (768 - 9))
    for y in range(16, 96):
        for x in range(48, 72):
            im.putpixel((x, y), opaque)
    im.putpixel((49, 20), 2)
    path = tmp_path / 'source.png'
    im.save(path, transparency=0)
    return {'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'pivot': [60, 96]}


def test_hash_and_crop_preserve_indices_and_pivot(tmp_path):
    spec = fixture(tmp_path)
    sp = load_pose(tmp_path, spec)
    assert (sp.width, sp.height, sp.axis_x, sp.axis_y) == (24, 80, 12, 80)
    assert sp.pixels[4 * 24 + 1] == 2
    spec['sha256'] = '0' * 64
    with pytest.raises(ValueError, match='SHA mismatch'):
        load_pose(tmp_path, spec)


def test_reject_truecolor_and_external_path(tmp_path):
    spec = fixture(tmp_path)
    Image.new('RGBA', (8, 8)).save(tmp_path / 'source.png')
    spec['sha256'] = hashlib.sha256((tmp_path / 'source.png').read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='indexed'):
        load_pose(tmp_path, spec)
    spec['path'] = '../outside.png'
    with pytest.raises(ValueError, match='within'):
        load_pose(tmp_path, spec)


def test_attack_does_not_change_neutral_scale(tmp_path):
    sp = load_pose(tmp_path, fixture(tmp_path))
    from dataclasses import replace
    wide = replace(sp, width=96, pixels=bytes([1]) * (96 * sp.height))
    single, scale1 = convert_poses([sp])
    pair, scale2 = convert_poses([sp, wide])
    assert scale1 == scale2
    assert single[0].pixels == pair[0].pixels


def test_shared_palette_does_not_turn_opaque_color_transparent(tmp_path):
    spec = fixture(tmp_path)
    ids = ['idle', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06']
    cfg = {'schema': 'sms_authored_sprite_sample_v1',
           'poses': [dict(spec, id=name) for name in ids],
           'durations': [2, 1, 1, 1, 1, 3],
           'reference': dict(spec, extra_scale=[2, 3])}
    config = tmp_path / 'config.json'
    config.write_text(json.dumps(cfg))
    out = tmp_path / 'converted'
    report = prepare(config, out)
    with Image.open(out / 'idle.png') as im:
        # The dominant codebook entry has zero-based position 0, but must
        # occupy visible PNG index 1. This protects the source silhouette.
        assert sum(v != 0 for v in im.tobytes()) > 100
        assert im.info['transparency'] == 0
    assert all(c['legal'] for c in report['compositions'])
    assert report['patterns'] <= 256
    with pytest.raises(FileExistsError, match='sealed'):
        prepare(config, out)
    cfg['durations'][0] = 1
    config.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match='timing'):
        prepare(config, tmp_path / 'bad')


def test_native_registration_keeps_black_opaque_and_uses_source_palette(tmp_path):
    im = Image.new('RGBA', (8, 8))
    for x in range(2, 6):
        for y in range(1, 7):
            im.putpixel((x, y), (0, 0, 0, 253))
    raw = tmp_path / 'raw.png'
    im.save(raw)
    recipe = {'source': raw.name, 'source_sha256': hashlib.sha256(raw.read_bytes()).hexdigest(),
              'raw_size': [8, 8], 'scale': [1, 1], 'canvas': [8, 8], 'pivot': [4, 8],
              'alpha_threshold': 128, 'source_palette_rgb': [[0, 0, 0], [111, 111, 111]],
              'frames': [{'id': 'J01', 'rect': [0, 0, 8, 8],
                          'cell_origin': [0, 0], 'raw_pivot': [4, 8]}]}
    path = tmp_path / 'recipe.json'
    path.write_text(json.dumps(recipe))
    report = extract_native(path, tmp_path / 'native')
    with Image.open(tmp_path / 'native/J01.png') as indexed:
        assert indexed.getpixel((2, 1)) == 1
        assert indexed.convert('RGBA').getpixel((2, 1)) == (0, 0, 0, 255)
        assert indexed.convert('RGBA').getpixel((0, 0))[3] == 0
    assert report['source_colors'] == 2


def test_wide_pair_is_rejected_without_omitting_cells(tmp_path):
    spec = fixture(tmp_path)
    im = Image.new('P', (128, 128))
    im.putpalette(Image.open(tmp_path / 'source.png').getpalette())
    for y in range(32, 96):
        for x in range(32, 112):
            im.putpixel((x, y), 1)
    im.save(tmp_path / 'wide.png', transparency=0)
    wide = {'path': 'wide.png', 'sha256': hashlib.sha256((tmp_path / 'wide.png').read_bytes()).hexdigest(),
            'pivot': [64, 96]}
    cfg = {'schema': 'sms_authored_sprite_sample_v1',
           'poses': [dict(wide if name == 'J04' else spec, id=name)
                     for name in ['idle', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06']],
           'durations': [2, 1, 1, 1, 1, 3], 'reference': dict(spec, extra_scale=[2, 3])}
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match='composition'):
        prepare(path, tmp_path / 'converted')
    report = json.loads((tmp_path / 'converted/conversion.json').read_text())
    assert next(c for c in report['compositions'] if c['id'] == 'J04')['peak'] > 8
    assert not (tmp_path / 'converted/sample_data.h').read_text().endswith('sample_durations[7] = {0,2,1,1,1,1,3};\n')
    # Grid phase does not grant an exemption for genuinely wide opaque rows.
    cfg['poses'][4]['packing_phase_px'] = [0, 8]
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match='composition'):
        prepare(path, tmp_path / 'wide_phased')


def test_all_grid_phases_preserve_pixels_and_opaque_black():
    phase_self_check()


def test_default_and_explicit_zero_phase_have_identical_runtime_data(tmp_path):
    spec = fixture(tmp_path)
    cfg = {'schema': 'sms_authored_sprite_sample_v1',
           'poses': [dict(spec, id=name) for name in
                     ['idle', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06']],
           'durations': [2, 1, 1, 1, 1, 3],
           'reference': dict(spec, extra_scale=[2, 3])}
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(cfg))
    prepare(path, tmp_path / 'implicit')
    for p in cfg['poses'] + [cfg['reference']]:
        p['packing_phase_px'] = [0, 0]
    path.write_text(json.dumps(cfg))
    prepare(path, tmp_path / 'explicit')
    for name in ['sample_data.h', 'idle.png', 'J04.png', 'reference.png']:
        assert (tmp_path / 'implicit' / name).read_bytes() == (tmp_path / 'explicit' / name).read_bytes()


def test_reject_phase_requiring_unsigned_y_wrap(tmp_path):
    spec = fixture(tmp_path)
    cfg = {'schema': 'sms_authored_sprite_sample_v1',
           'poses': [dict(spec, id=name, packing_phase_px=[0, 8]) for name in
                     ['idle', 'J01', 'J02', 'J03', 'J04', 'J05', 'J06']],
           'durations': [2, 1, 1, 1, 1, 3],
           'reference': dict(spec, extra_scale=[2, 3])}
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match='signed offsets'):
        prepare(path, tmp_path / 'invalid_for_emitter')
    assert not (tmp_path / 'invalid_for_emitter/sample_data.h').exists()
