"""Legacy 1:4 converter behavior plus the current uniform fighter-scale contract."""
from __future__ import annotations

from mugen2sms.converters import sms_scale as sc
from mugen2sms.character import Character
from mugen2sms.parsers.air import Action, Frame
from mugen2sms.parsers import sff
from mugen2sms.analysis import scale_pilot


def sprite(w, h, pixels, palette=None):
    return sff.Sprite(1, 0, 0, 0, w, h, pixels,
                      palette or [(0, 0, 0)] * 256, False, None, 0)


def test_downscale_nearest_preserva_indices_e_palette():
    pal = [(0, 0, 0), (255, 0, 0), (0, 255, 0)] + [(0, 0, 0)] * 253
    px = bytes([1] * (16 * 8) + [2] * (16 * 8))       # 16x16: topo vermelho, base verde
    out = sc.downscale_indexed(sprite(16, 16, px, pal), 4)
    assert (out.width, out.height) == (4, 4)
    assert out.pixels == bytes([1] * 8 + [2] * 8)   # 4x4: 2 linhas 1, 2 linhas 2
    assert out.palette is pal or list(out.palette) == list(pal)


def test_orcamento_pose_sob_escala():
    # 128x112 nativo -> 32x28 -> 4 colunas de 8 px; 28 px = 2 linhas TALL
    assert sc.pose_runtime_size(128, 112) == (4, 2)
    assert not sc.exceeds_budget(128, 112)


def test_orcamento_estoura_apos_escala_vira_manual():
    # 192 px nativos -> 48 pos-escala -> 6 colunas de 8 px > MAX_COLS (4)
    assert sc.exceeds_budget(192, 48)
    # 256 px de altura nativa -> 64 pos-escala -> 4 linhas TALL > MAX_TALL_ROWS (3)
    assert sc.pose_runtime_size(48, 256) == (2, 4)
    assert sc.exceeds_budget(48, 256)


def test_tetos_do_gdd():
    assert (sc.SCALE, sc.MAX_COLS, sc.MAX_TALL_ROWS) == (4, 4, 3)


def test_uniform_scale_preserva_pixels_e_geometria_air():
    src_sprite = sff.Sprite(1, 0, 2, 4, 4, 4,
                            bytes((1, 1, 0, 0,
                                   1, 1, 0, 0,
                                   0, 0, 2, 2,
                                   0, 0, 2, 2)),
                            [(0, 0, 0), (255, 0, 0), (0, 255, 0)],
                            False, None, 0)
    frame = Frame(1, 0, 10, -2, 6, True, False, "A",
                  [(-4, -2, 3, 5)], [(-6, -8, 7, 9)])
    action = Action(0, [frame], 0)
    character = Character("fixture", "test", "fixture.def", "a" * 64,
                          {}, {}, [], {0: action}, [src_sprite], [], [], {},
                          {}, [])

    scaled = sc.scale_character(character, {0}, 1, 2)
    out_sprite = scaled.sprites[0]
    out_frame = scaled.anims[0].frames[0]

    assert (out_sprite.width, out_sprite.height) == (2, 2)
    assert out_sprite.pixels == bytes((1, 0, 0, 2))
    assert (out_sprite.axis_x, out_sprite.axis_y) == (1, 2)
    assert (out_frame.x, out_frame.y) == (5, -1)
    assert (out_frame.time, out_frame.hflip, out_frame.vflip, out_frame.blend) == (
        6, True, False, "A")
    assert out_frame.clsn1 == [(-2, -1, 2, 3)]
    assert out_frame.clsn2 == [(-3, -4, 4, 5)]
    assert frame.x == 10 and frame.clsn1 == [(-4, -2, 3, 5)]


def test_uniform_scale_ratio_and_signed_rounding():
    assert sc.target_ratio(93, 80, (72, 88)) == (80, 93)
    assert sc._round_ratio(3, 1, 2) == 2
    assert sc._round_ratio(-3, 1, 2) == -2


def test_mirrored_metasprite_origin_uses_padded_8px_grid():
    # A 31px image still occupies 4 sprite columns after metasprite mirroring.
    # Its base moves one pixel left; that transparent padding moves the opaque
    # raster origin back to the source pose's pivot-preserving location.
    assert scale_pilot.mirrored_origin_x(152, -27, 31) == 147
    assert scale_pilot.mirrored_origin_x(152, -27, 32) == 147
    assert scale_pilot.mirrored_origin_x(152, -27, 51) == 123
    assert scale_pilot.raster_origin_x(160, -18, 31, True) == 147
    assert scale_pilot.raster_origin_x(96, -3, 51, False) == 93
