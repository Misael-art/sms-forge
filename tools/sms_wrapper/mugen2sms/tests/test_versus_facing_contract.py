"""A runtime-facing layout must be explicit and reject legacy P2 references."""
import pytest

from mugen2sms.generators.versus_scene_cut import merge_headers


def scene(stem):
    return f'''#ifndef ken_scene_runtime_H
#define ken_scene_runtime_H
#define {stem}_A0F0_TILES_BANK 2
#define {stem}_A0F0_TILES_OFF 0
#define {stem}_A0F0_FACE_SIZE 64
#define {stem}_A0F0_P2_TILES_BANK 2
#define {stem}_A0F0_P2_TILES_OFF 128
#define {stem}_A0F0_P2_FACE_SIZE 64
#define CUT_POSE_COUNT 1
static const PoseRef poses_all[2] = {{
    {{ {stem}_A0F0_TILES_BANK, {stem}_A0F0_TILES_OFF, {stem}_A0F0_FACE_SIZE }},
    {{ {stem}_A0F0_P2_TILES_BANK, {stem}_A0F0_P2_TILES_OFF + {stem}_A0F0_P2_FACE_SIZE, {stem}_A0F0_P2_FACE_SIZE }},
}};
static const unsigned char cut_sprite_palette[16] = {{ 0,1,2,3,4,5,6,7,0,9,10,11,12,13,14,15 }};
#endif /* ken_scene_runtime_H */
'''


def test_adjacent_facing_contract_is_emitted_only_for_matching_rows():
    a, b = scene('ONE'), scene('TWO')
    merged = merge_headers(a, b, 1, 1, require_facing_contract=True)
    assert '#define VERSUS_FACE_LAYOUT_ADJACENT_P2_LEFT 1' in merged
    legacy = b.replace('TWO_A0F0_P2_TILES_OFF + TWO_A0F0_P2_FACE_SIZE',
                       'TWO_A0F0_P2_TILES_OFF')
    with pytest.raises(ValueError, match='facing'):
        merge_headers(a, legacy, 1, 1, require_facing_contract=True)
    wrong_palette = b.replace('TWO_A0F0_P2_TILES_BANK, TWO_A0F0_P2_TILES_OFF + TWO_A0F0_P2_FACE_SIZE, TWO_A0F0_P2_FACE_SIZE',
                              'TWO_A0F0_TILES_BANK, TWO_A0F0_TILES_OFF + TWO_A0F0_FACE_SIZE, TWO_A0F0_FACE_SIZE')
    with pytest.raises(ValueError, match='facing'):
        merge_headers(a, wrong_palette, 1, 1, require_facing_contract=True)
