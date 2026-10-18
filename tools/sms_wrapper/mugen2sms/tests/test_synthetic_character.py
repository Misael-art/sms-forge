# S2 — pipeline sintetico: pacote mini MUGEN -> Character IR completo e serializavel.
import dataclasses, json, sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # tools/sms_wrapper
from mugen2sms.character import load                            # noqa: E402
from mugen2sms.source import Source                             # noqa: E402
from mugen2sms.tests.make_fixtures import build, SPRITE_W, SPRITE_H  # noqa: E402


@pytest.fixture()
def character(tmp_path):
    root = build(tmp_path / "minichar")
    return load(Source(root))


def test_synthetic_character_loads_and_serializes(character):
    d = dataclasses.asdict(character)
    json.dumps(d, default=str)
    assert character.name == "Mini Fixture"
    assert character.author == "fixture"
    assert character.anims, "sem animacoes"
    assert character.sprites, "sem sprites"


def test_legacy_author_colon_is_preserved(tmp_path):
    root = build(tmp_path / "author_colon")
    def_path = root / "mini.def"
    text = def_path.read_text(encoding="ascii")
    def_path.write_text(text.replace('author = "fixture"', "Author: Falchion22"), encoding="ascii")
    parsed = load(Source(root))
    assert parsed.author == "Falchion22"
    assert parsed.info["author"] == "Falchion22"


def test_sprites_include_link_and_pcx_sizes(character):
    by_img = {s.image: s for s in character.sprites}
    assert set(by_img) == set(range(9))
    assert by_img[0].width == SPRITE_W and by_img[0].height == SPRITE_H
    assert by_img[2].linked_from is not None, "link nao resolvido"
    assert by_img[2].pixels == by_img[0].pixels


def test_action_anims_are_distinct_per_action(character):
    """T4: o fixture cobre idle/walk/jump/crouch/guard/punch1/punch2 sem clonar acao."""
    assert {0, 20, 40, 100, 120, 200, 201} <= set(character.anims)
    a20 = character.anims[20]
    assert len(a20.frames) == 2
    assert a20.frames[0].image != a20.frames[1].image, "walk nao alterna padrao"
    # cada pose de acao usa imagem SFF propria (0=link do idle, 2=link do punch1)
    def imgs(n):
        return {character.anims[n].frames[i].image
                for i in range(len(character.anims[n].frames))}
    assert imgs(0) == {0} and imgs(20) == {3, 4} and imgs(40) == {7}
    assert imgs(100) == {5} and imgs(120) == {6} and imgs(201) == {8, 7, 4}
    # crouch tem hurtbox mais baixa que idle — caixa distingue a acao
    assert character.anims[100].frames[0].clsn2 == [(-8, -12, 8, 0)]
    assert character.anims[201].frames[0].clsn1 == [(0, -16, 16, -4)]
    assert len(character.anims[201].frames) == 3


def test_anims_frames_and_clsn_survive(character):
    a200 = character.anims[200]
    assert len(a200.frames) == 2
    assert a200.frames[1].hflip
    assert a200.frames[0].clsn1 == [(0, -14, 12, -8)]
    assert a200.frames[0].clsn2 == [(-8, -16, 8, 0)]
    assert character.anims[0].frames[0].clsn2 == [(-8, -16, 8, 0)]  # clsn2default
    assert character.report["anims"]["missing_sprites"] == []


def test_commands_and_states_compiled(character):
    names = {c.name for c in character.commands}
    assert {"punch", "special", "holdF"} <= names
    assert 0 in character.states and 200 in character.states
    assert character.states[0].statetype == ord("S")
    assert character.states[0].params.get("anim") is not None
    assert any(c.type == "hitdef" for c in character.states[200].controllers)


def test_palette_and_source_sha(character):
    assert character.palettes and len(character.palettes[0][1]) == 256
    assert len(character.source_sha256) == 64
