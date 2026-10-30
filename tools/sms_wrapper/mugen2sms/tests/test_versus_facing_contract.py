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


def test_pair_hash_tables_are_namespaced_and_contract_is_merged():
    def with_pair_hashes(header, stem, maximum):
        marker = "static const PoseRef poses_all[2] = {"
        declarations = (
            f"#define CUT_PAIR_CONTENT_HASHES_VERSION 1\n"
            f"#define CUT_MAX_POSE_PAIRS {maximum}\n"
            f"static const unsigned char {stem}_A0F0_RIGHT_PAIR_HASHES[1] = {{ 7 }};\n"
            f"static const unsigned char {stem}_A0F0_LEFT_PAIR_HASHES[1] = {{ 8 }};\n"
            f"static const unsigned char {stem}_A0F0_P2_RIGHT_PAIR_HASHES[1] = {{ 9 }};\n"
            f"static const unsigned char {stem}_A0F0_P2_LEFT_PAIR_HASHES[1] = {{ 10 }};\n"
        )
        header = header.replace(marker, declarations + marker)
        header = header.replace(
            f"{stem}_A0F0_FACE_SIZE }},",
            f"{stem}_A0F0_FACE_SIZE, CUT_PAIR_HASH_POINTERS("
            f"{stem}_A0F0_RIGHT_PAIR_HASHES, {stem}_A0F0_LEFT_PAIR_HASHES) }},",
        )
        header = header.replace(
            f"{stem}_A0F0_P2_FACE_SIZE }},",
            f"{stem}_A0F0_P2_FACE_SIZE, CUT_PAIR_HASH_POINTERS("
            f"{stem}_A0F0_P2_RIGHT_PAIR_HASHES, "
            f"{stem}_A0F0_P2_LEFT_PAIR_HASHES) }},",
        )
        return header

    merged = merge_headers(with_pair_hashes(scene("ONE"), "ONE", 12),
                           with_pair_hashes(scene("TWO"), "TWO", 18), 1, 1,
                           require_facing_contract=True)
    assert "static const unsigned char P1_ONE_A0F0_RIGHT_PAIR_HASHES[1]" in merged
    assert "static const unsigned char P2_TWO_A0F0_P2_LEFT_PAIR_HASHES[1]" in merged
    assert "static const unsigned char ONE_A0F0_RIGHT_PAIR_HASHES[1]" not in merged
    assert "#define VERSUS_PAIR_CONTENT_HASHES_VERSION 1" in merged
    assert "#define VERSUS_MAX_POSE_PAIRS 18" in merged
    assert ("P1_CUT_PAIR_HASH_POINTERS(P1_ONE_A0F0_RIGHT_PAIR_HASHES, "
            "P1_ONE_A0F0_LEFT_PAIR_HASHES)" in merged)
    assert ("P2_CUT_PAIR_HASH_POINTERS(P2_TWO_A0F0_P2_RIGHT_PAIR_HASHES, "
            "P2_TWO_A0F0_P2_LEFT_PAIR_HASHES)" in merged)
