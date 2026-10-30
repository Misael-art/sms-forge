"""P1/P2 metasprite IDs must target the matching palette tile pool."""
from __future__ import annotations

import pytest

from mugen2sms.generators.runtime_format import _encode_indices, decode_indices
from mugen2sms.generators.scene_cut import (
    _compact_facing_pose, _pair_content_hashes, _palette_codebook, _palette_metas, _remap_blob,
    _runtime_table)
from mugen2sms.generators.smsdev import Artifact


def test_palette_metadata_is_emitted_as_distinct_artifacts():
    p1 = {
        "F_A0F0_META": Artifact("F_A0F0_META", b"p1-right", "air"),
        "F_A0F0_METAL": Artifact("F_A0F0_METAL", b"p1-left", "air"),
    }
    p2 = {
        "F_A0F0_META": Artifact("F_A0F0_META", b"p2-right", "air"),
        "F_A0F0_METAL": Artifact("F_A0F0_METAL", b"p2-left", "air"),
    }

    emitted = _palette_metas("F_A0F0", p1, p2)

    assert [(item.symbol, item.data) for item in emitted] == [
        ("F_A0F0_META", b"p1-right"),
        ("F_A0F0_P2_META", b"p2-right"),
        ("F_A0F0_METAL", b"p1-left"),
        ("F_A0F0_P2_METAL", b"p2-left"),
    ]


def test_missing_palette_metadata_is_rejected():
    p1 = {"F_A0F0_META": Artifact("F_A0F0_META", b"p1-right", "air"),
          "F_A0F0_METAL": Artifact("F_A0F0_METAL", b"p1-left", "air")}

    with pytest.raises(ValueError, match="palette-specific metasprite is missing"):
        _palette_metas("F_A0F0", p1, {})


def test_facing_compaction_preserves_bytes_positions_and_pair_references():
    first, second = bytes([0x11]) * 64, bytes([0x22]) * 64
    tiles = first + second + first
    metadata = bytes((3, 4, 2, 5, 6, 0, 7, 8, 4, 0x80))

    compact, rewritten = _compact_facing_pose(tiles, metadata, "F_A0F0")

    assert compact == second + first
    assert rewritten == bytes((3, 4, 0, 5, 6, 2, 7, 8, 2, 0x80))


def test_pair_content_hashes_repeat_for_exact_compact_pairs():
    first, second, third = bytes([0x11]) * 64, bytes([0x22]) * 64, bytes([0x33]) * 64
    hashes = _pair_content_hashes(first + second + first)
    assert hashes[0] != hashes[1]
    assert hashes[0] == hashes[2]
    assert _pair_content_hashes(second + third)[0] == hashes[1]


def test_pair_content_hashes_reject_partial_pair_bytes():
    with pytest.raises(ValueError, match="multiple of 64"):
        _pair_content_hashes(bytes(65))


def test_facing_compaction_rejects_odd_tall_sprite_id():
    with pytest.raises(ValueError, match="odd 8x16 pattern id"):
        _compact_facing_pose(bytes(64), bytes((0, 0, 1, 0x80)), "F_A0F0")


def test_runtime_frame_selects_both_palette_metadata_pairs():
    stem = "F_A0F0"
    artifacts = [
        Artifact(stem + suffix, b"x", "air")
        for suffix in ("_META", "_METAL", "_P2_META", "_P2_METAL", "_AXIS")
    ]
    role_frames = {"idle": [{"stem": stem, "duration": 4,
                              "width": 16, "height": 16}]}
    runtime = {key: 0 for key in (
        "life", "walk_fwd", "walk_back", "jump_vy", "gravity",
        "damage_punch", "damage_hp", "damage_kick", "damage_hk",
        "damage_special", "special_vel", "input_threshold_key1",
        "input_threshold_key2",
        "hitstop", "hit_push", "guard_push")}

    header = _runtime_table(
        [{"role": "idle", "action": 0, "loop_start": 0}], role_frames, 1,
        artifacts,
        {stem + "_TILES": (2, 0), stem + "_P2_TILES": (2, 64)},
        [0] * 16, runtime, {stem: 64, stem + "_P2": 128},
        {stem: {"right": [10], "left": [11],
                "p2_right": [12, 13], "p2_left": [14, 15]}})

    assert f"{stem}_META, {stem}_METAL, 0, {stem}_AXIS, 16, 16, " \
           f"{stem}_P2_META, {stem}_P2_METAL" in header
    assert "poses_all[CUT_POSE_COUNT * 2]" in header
    assert f"{stem}_FACE_SIZE 64" in header
    assert f"{stem}_P2_FACE_SIZE 128" in header
    # Frame.metal_p2 addresses the left face; the P2 PoseRef must stage it.
    assert (f"{{ {stem}_TILES_BANK, {stem}_TILES_OFF, {stem}_FACE_SIZE, "
            f"CUT_PAIR_HASH_POINTERS({stem}_RIGHT_PAIR_HASHES, "
            f"{stem}_LEFT_PAIR_HASHES) }}") in header
    assert (f"{{ {stem}_P2_TILES_BANK, {stem}_P2_TILES_OFF + "
            f"{stem}_P2_FACE_SIZE, {stem}_P2_FACE_SIZE, "
            f"CUT_PAIR_HASH_POINTERS({stem}_P2_RIGHT_PAIR_HASHES, "
            f"{stem}_P2_LEFT_PAIR_HASHES) }}") in header
    assert f"{stem}_RIGHT_PAIR_HASHES[1] = {{" in header
    assert "CUT_PAIR_CONTENT_HASHES_VERSION 1" in header
    assert "CUT_INPUT_THRESHOLD_KEY1 0" in header


def _tiles(spec):
    """spec entries are (palette index, CRAM word, number of solid 8x8 tiles)."""
    palette = bytearray(16)
    blob = bytearray()
    for index, word, count in spec:
        palette[index] = word
        blob += _encode_indices([index] * 64) * count
    tiles = Artifact("FIG_A0F0_TILES", bytes(blob), "sff")
    pal = Artifact("FIG_A0F0_PAL", bytes(palette), "sff")
    return _palette_codebook([tiles], {tiles.symbol: tiles, pal.symbol: pal})


def test_opaque_black_stays_when_it_is_the_most_used_color():
    # CRAM word 0 is black paint. The old filter treated that word as absent.
    book = _tiles([(1, 0, 10), (2, 2, 1)])
    assert book[0] == 0
    assert 2 in book


def test_frequent_black_and_white_do_not_displace_another_color():
    assert _tiles([(1, 0, 10), (2, 63, 9), (3, 2, 8), (4, 7, 1)]) == [0, 63, 2, 7]


def test_rare_dark_neighbor_can_make_room_for_black_without_white():
    # (170, 0, 85) is one step from the red already in the book. Black can
    # take that slot. The skin step stays, and pure white does not enter.
    book = _tiles([
        (1, 2, 20),    # red
        (2, 27, 15),   # skin
        (3, 7, 12),    # orange
        (4, 32, 10),   # blue
        (5, 8, 9),     # green
        (6, 43, 4),    # skin neighbor, kept
        (7, 18, 3),    # (170, 0, 85), the slot black may take
        (8, 0, 2),     # opaque black, rank 8
        (9, 63, 1),    # white, rank 9
    ])
    assert book == [2, 27, 7, 32, 8, 43, 0]
    assert 18 not in book
    assert 63 not in book


def test_warm_shadow_is_a_body_color_and_stays():
    # (170, 85, 0) is luma 101, a shading step. Giving that slot to black is
    # how the orange of the gi collapsed into the neighboring pink.
    book = _tiles([
        (1, 2, 30),
        (2, 27, 20),
        (3, 7, 18),
        (4, 32, 16),
        (5, 8, 14),
        (6, 43, 12),
        (7, 6, 4),
        (8, 0, 3),
    ])
    assert book == [2, 27, 7, 32, 8, 43, 6]
    assert 0 not in book


def test_cream_highlight_is_not_spent_on_pure_white():
    book = _tiles([
        (1, 47, 20),   # (255, 255, 170), one step from white
        (2, 43, 15),
        (3, 27, 12),
        (4, 11, 10),
        (5, 7, 9),
        (6, 2, 8),
        (7, 22, 6),
        (8, 63, 1),    # white
        (9, 0, 2),     # black
    ])
    assert 47 in book
    assert 63 not in book


def test_equal_distance_keeps_the_brighter_neighbor():
    # (170, 85, 0) is one channel from both dark red and brown.
    # The lower codebook index is the darker red; brightness decides the tie.
    book = [2, 22]
    palette = bytes([0, 6] + [0] * 14)
    blob = _encode_indices([1] * 64)
    mapped = decode_indices(_remap_blob(blob, palette, book, 0))
    assert mapped[0] == 2
    assert book[mapped[0] - 1] == 22


def test_opaque_black_remaps_to_a_visible_slot_and_index_zero_stays_clear():
    book = _tiles([(1, 0, 8), (2, 2, 4), (3, 63, 2)])
    palette = bytes([0, 0, 2] + [0] * 13)
    blob = _encode_indices([0, 1, 2] + [1] * 61)
    mapped = decode_indices(_remap_blob(blob, palette, book, 0))
    assert mapped[0] == 0
    assert mapped[1] != 0
    assert book[mapped[1] - 1] == 0
    assert book[mapped[2] - 1] == 2


def test_transparent_pose_keeps_an_empty_codebook():
    tiles = Artifact("FIG_A0F0_TILES", _encode_indices([0] * 64), "sff")
    pal = Artifact("FIG_A0F0_PAL", bytes(16), "sff")
    assert _palette_codebook([tiles], {tiles.symbol: tiles, pal.symbol: pal}) == []
