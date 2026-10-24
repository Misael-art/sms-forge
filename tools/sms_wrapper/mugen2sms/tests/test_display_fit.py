"""Framebuffer fit: SMS is the default, the older scales stay optional."""
import pytest

from mugen2sms.converters import display_fit as fit
from mugen2sms.character import Character
from mugen2sms.parsers.air import Action, Frame
from mugen2sms.parsers import sff


def sprite(w, h, pixels, axis=(0, 0), group=0):
    return sff.Sprite(group, 0, axis[0], axis[1], w, h, pixels,
                      [(0, 0, 0), (255, 0, 0), (0, 255, 0)] + [(0, 0, 0)] * 253,
                      False, None, 0)


def test_default_cps2_to_sms_is_two_thirds_by_six_sevenths():
    resolved = fit.resolve_display_fit(None, "cps2", None)
    assert resolved.status == "applied"
    assert resolved.mode == "pose_budget"
    assert resolved.pose_budget is True
    assert resolved.target == "sms"
    assert (resolved.scale_num_x, resolved.scale_den_x) == (2, 3)
    assert (resolved.scale_num_y, resolved.scale_den_y) == (6, 7)
    assert resolved.to_dict()["target_px"] == [256, 192]


def test_game_gear_and_identity_and_refusal():
    gear = fit.resolve_display_fit("framebuffer", "cps2", "game_gear")
    assert (gear.scale_num_x, gear.scale_den_x, gear.scale_num_y, gear.scale_den_y) == (5, 12, 9, 14)
    assert fit.resolve_display_fit("framebuffer", "sms", "sms").status == "identity"
    assert fit.resolve_display_fit("framebuffer", None, "sms").status == "refused"
    assert fit.resolve_display_fit("framebuffer", "arcade", "sms").status == "refused"
    assert fit.resolve_display_fit("legacy_quarter", "cps2", "sms").status == "option"
    assert fit.resolve_display_fit("fighter_scale", "cps2", "sms").status == "option"


def test_anisotropic_scale_changes_size_only():
    src = sprite(6, 7, bytes([1] * 18 + [0] * 6 + [2] * 18), axis=(3, 4))
    frame = Frame(0, 0, 9, -2, 6, True, False, "A", [(-3, -2, 3, 4)], [(-4, -1, 2, 5)])
    character = Character("fixture", "test", "fixture.def", "a" * 64, {}, {}, [],
                          {0: Action(0, [frame], 0)}, [src], [], [], {}, {}, [])
    resolved = fit.resolve_display_fit("framebuffer", "cps2", "sms")
    scaled, changed, report = fit.scale_character(character, resolved)
    assert report["gate"] == "not_applied"
    out = scaled.sprites[0]
    out_frame = scaled.anims[0].frames[0]
    assert changed == 1
    assert (out.width, out.height) == (8, 8)
    assert (out.axis_x, out.axis_y) == (4, 4)
    assert out.pixels[0] == 0
    assert out.pixels[10] == 1
    assert out.pixels[34] == 2
    assert (out_frame.time, out_frame.hflip, out_frame.vflip, out_frame.blend) == (6, True, False, "A")
    assert (out_frame.x, out_frame.y) == (8, -1)
    assert out_frame.clsn1 == [(-2, -2, 2, 3)]
    assert out_frame.clsn2 == [(-3, -1, 1, 4)]
    assert frame.time == 6 and frame.x == 9 and frame.clsn1 == [(-3, -2, 3, 4)]


def test_optional_and_off_do_not_rewrite_pixels():
    src = sprite(6, 7, bytes([1] * 42), axis=(3, 4))
    frame = Frame(0, 0, 9, -2, 6, False, False, "", [], [])
    character = Character("fixture", "test", "fixture.def", "a" * 64, {}, {}, [],
                          {0: Action(0, [frame], 0)}, [src], [], [], {}, {}, [])
    with pytest.raises(ValueError):
        fit.scale_character(character, fit.resolve_display_fit("legacy_quarter", "cps2", "sms"))
    with pytest.raises(ValueError):
        fit.scale_character(character, fit.resolve_display_fit("fighter_scale", "cps2", "sms"))
    scaled, changed, _report = fit.scale_character(character, fit.resolve_display_fit("off", "cps2", "sms"))
    assert changed == 0
    assert scaled.sprites[0].pixels == src.pixels
    assert scaled.anims[0].frames[0].x == 9


def test_second_apply_is_the_guard(tmp_path):
    src = sprite(6, 7, bytes([1] * 42), axis=(3, 4))
    frame = Frame(0, 0, 9, -2, 6, False, False, "", [], [])
    character = Character("fixture", "test", "fixture.def", "a" * 64, {}, {}, [],
                          {0: Action(0, [frame], 0)}, [src], [], [], {}, {}, [])
    resolved = fit.resolve_display_fit("framebuffer", "cps2", "sms")
    report = fit.apply_character(character, resolved, tmp_path / "ken", "ken")
    assert report["sms_columns_max_after"] == 1
    assert report["sprites_wider_than_8_sms_sprites"] == 0
    assert report["durations_preserved"] is True
    marker = (tmp_path / "ken" / "display_fit.marker").read_text(encoding="utf-8")
    assert marker == "display_fit: source=cps2 target=sms x=2/3 y=6/7\n"
    with pytest.raises(FileExistsError):
        fit.apply_character(character, resolved, tmp_path / "ken", "ken")
    assert fit.main(["--self-check"]) == 0


def test_portrait_stays_out_of_the_fitted_ceiling(tmp_path):
    body = sprite(6, 7, bytes([1] * 42), axis=(3, 4), group=0)
    portrait = sprite(120, 140, bytes([3] * (120 * 140)), axis=(1, 2), group=9000)
    body_frame = Frame(0, 0, 9, 0, 4, False, False, "", [], [])
    portrait_frame = Frame(9000, 0, 9, 0, 7, True, False, "", [], [])
    character = Character("fixture", "test", "fixture.def", "b" * 64, {}, {}, [],
                          {0: Action(0, [body_frame, portrait_frame], 0)},
                          [body, portrait], [], [], {}, {}, [])
    resolved = fit.resolve_display_fit("framebuffer", "cps2", "sms")
    report = fit.apply_character(character, resolved, tmp_path / "ken", "ken")
    assert report["max_fitted_px_after"] == [8, 8]
    assert report["max_exempt_px_after"] == [120, 140]
    assert report["max_sprite_px_after"] == [120, 140]
    assert report["sms_columns_max_fitted"] == 1
    assert report["sms_columns_max_after"] == 15
    assert report["sprites_fitted_wider_than_8"] == 0
    assert not (tmp_path / "ken" / "sheets" / "g9000_0.png").exists()
    kept = report and character.anims[0].frames[1]
    written = json_frame(tmp_path / "ken" / "frames.json", 1)
    assert kept.time == 7 and kept.x == 9
    assert written["time"] == 7 and written["x"] == 9 and written["hflip"] is True


def json_frame(path, index):
    import json
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["actions"]["0"][index]


def _character(sprites, actions):
    return Character("fixture", "test", "fixture.def", "c" * 64, {}, {}, [],
                     actions, sprites, [], [], {}, {}, [])


def test_pose_budget_sizes_the_idle_not_the_widest_pose():
    sprites = []
    actions = {}
    for number in range(7):
        sprites.append(sprite(72, 56, bytes([1] * (72 * 56)), axis=(8, 8), group=number))
        actions[number] = Action(number, [Frame(number, 0, 0, 0, 4, False, False, "", [], [])], 0)
    for number in range(7, 10):
        sprites.append(sprite(144, 56, bytes([1] * (144 * 56)), axis=(8, 8), group=number))
        actions[number] = Action(number, [Frame(number, 0, 0, 0, 4, False, False, "", [], [])], 0)
    resolved = fit.resolve_display_fit(None, "cps2", "sms")
    scaled, changed, report = fit.scale_character(_character(sprites, actions), resolved)
    by_group = {item.group: item for item in scaled.sprites}
    assert changed == 20
    assert report["gate"] == "idle_to_4"
    assert report["extra_scale"] == [2, 3]
    assert report["pose_near"] == fit.POSE_NEAR
    assert report["case_by_case"] == [7, 8, 9]
    assert report["neutral_columns_after"] == 4
    assert 0 in report["included_actions"]
    assert (by_group[0].width, by_group[7].width) == (32, 64)
    assert scaled.anims[0].frames[0].time == 4


def test_idle_already_at_four_columns_keeps_extra_at_one():
    sprites = [
        sprite(48, 56, bytes([1] * (48 * 56)), axis=(8, 8), group=0),
        sprite(144, 56, bytes([1] * (144 * 56)), axis=(8, 8), group=1),
    ]
    actions = {
        0: Action(0, [Frame(0, 0, 0, 0, 4, False, False, "", [], [])], 0),
        1: Action(1, [Frame(1, 0, 0, 0, 4, False, False, "", [], [])], 0),
    }
    resolved = fit.resolve_display_fit(None, "cps2", "sms")
    scaled, _changed, report = fit.scale_character(_character(sprites, actions), resolved)
    by_group = {item.group: item for item in scaled.sprites}
    assert report["gate"] == "idle_at_4"
    assert report["extra_scale"] == [1, 1]
    assert report["within_8_ratio"] == 0.5
    assert report["case_by_case"] == [1]
    assert report["included_actions"] == [0]
    assert (by_group[0].width, by_group[1].width) == (32, 96)


def test_blank_cell_does_not_count_as_a_sat_column():
    pixels = bytearray(40 * 16)
    for x in range(8):
        pixels[x] = 1
    pose = sprite(40, 16, bytes(pixels), group=0)
    assert fit.sat_row_peak(pose) == 1
    assert fit._columns(pose.width) == 5


def test_wide_fx_does_not_set_the_body_fraction_and_is_excluded():
    idle = sprite(48, 16, bytes([1] * (48 * 16)), axis=(4, 8), group=0)
    effect = sprite(168, 16, bytes([1] * (168 * 16)), axis=(4, 8), group=8400)
    actions = {
        0: Action(0, [Frame(0, 0, 0, 0, 4, False, False, "", [], [])], 0),
        1: Action(1, [Frame(8400, 0, 0, 0, 4, False, False, "", [], [])], 0),
    }
    resolved = fit.resolve_display_fit(None, "cps2", "sms")
    _scaled, _changed, report = fit.scale_character(
        _character([idle, effect], actions), resolved, fx_groups=(8400,))
    assert report["extra_scale"] == [1, 1]
    assert report["included_actions"] == [0]
    assert report["fx_excluded"]
    assert report["fx_excluded"][0]["group"] == 8400
    assert report["fx_excluded"][0]["sat_columns"] > 3


def test_self_check():
    fit._self_check()


def test_sheet_marks_index_zero_transparent(tmp_path):
    from PIL import Image

    src = sprite(2, 1, bytes([0, 1]))
    src.palette[0] = (255, 0, 255)
    path = tmp_path / "sheet.png"
    fit._write_png(src, path)
    image = Image.open(path)
    assert image.mode == "P"
    assert image.info["transparency"] == 0
    assert list(image.get_flattened_data()) == [0, 1]
    assert image.getpalette()[:3] == [255, 0, 255]
