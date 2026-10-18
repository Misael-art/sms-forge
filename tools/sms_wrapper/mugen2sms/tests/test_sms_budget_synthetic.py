"""S3: orçamento VDP e fidelidade por recurso — casos-limite sinteticos (L001: so numeros SMS)."""
from __future__ import annotations

import pytest

from mugen2sms.analysis.fidelity import classify_character
from mugen2sms.analysis.sms_budget import SmsLimits, columns, dedup_tiles, tiles_cover, used_colors
from mugen2sms.ir import controllers as C
from mugen2sms.parsers import air, sff, snd, cmd as cmdmod
from mugen2sms.character import CState


def sprite(idx=0, w=8, h=8, pixels=None, group=5900):
    if pixels is None:
        pixels = bytes([1] * (w * h))
    return sff.Sprite(group, idx, 0, 0, w, h, pixels, [(0, 0, 0)] * 256, False, None, idx)


def char_with(sprites=(), anims=(), commands=(), sounds=(), states=()):
    class Ch:
        pass
    ch = Ch()
    ch.sprites, ch.anims, ch.commands, ch.sounds, ch.states = list(sprites), dict(anims), list(commands), list(sounds), dict(states)
    ch.report = {"controller_fidelity": {"direct": 0, "approximate": 0, "unsupported": 0}}
    return ch


def anim(number, frames):
    return number, air.Action(number, frames)


def frame(g, i, time=1):
    return air.Frame(g, i, 0, 0, time)


def test_tiles_cover_8x8_grid():
    assert tiles_cover(64, 64) == 64
    assert tiles_cover(9, 1) == 2          # borda incompleta ocupa tile inteiro
    assert columns(72) == 9


def test_dedup_tiles_collapses_identical():
    a, b = sprite(0, 8, 8, bytes([1] * 64)), sprite(1, 8, 8, bytes([1] * 64))
    uniq, total = dedup_tiles([a, b])
    assert (uniq, total) == (1, 2)


def test_used_colors_ignores_transparent_index0():
    assert used_colors(sprite(0, 8, 8, bytes([0, 2, 3]))) == 2


def test_pose_within_escala_do_gdd_e_direct():
    pose = sprite(0, w=32, h=48)                      # <=4 colunas x <=3 linhas TALL
    rep = classify_character(char_with([pose], dict([anim(0, [frame(5900, 0)])])), SmsLimits())
    assert rep.by_id["anim:0.0"].classe == "direct"
    assert rep.by_id["sprite:5900,0"].classe == "direct"


def test_pose_alta_demais_para_1x1_vira_downscale_aproximate():
    pose = sprite(0, w=32, h=64)                       # 4 linhas TALL > 3 -> precisa 1:4
    rep = classify_character(char_with([pose], dict([anim(0, [frame(5900, 0)])])), SmsLimits())
    assert rep.by_id["anim:0.0"].classe == "approximate"
    assert rep.by_id["anim:0.0"].motivo == "downscale1:4"


def test_pose_larga_vira_downscale_aproximate():
    pose = sprite(0, w=72, h=64)                       # 9 colunas; cabe apos 1:4 -> approximate
    rep = classify_character(char_with([pose], dict([anim(0, [frame(5900, 0)])])), SmsLimits())
    assert rep.by_id["anim:0.0"].classe == "approximate"
    assert rep.by_id["anim:0.0"].motivo == "downscale1:4"


def test_pose_que_nem_1_4_salva_vira_manual():
    pose = sprite(0, w=192, h=24)                      # 48 px pos-escala = 6 colunas > 4
    rep = classify_character(char_with([pose], dict([anim(0, [frame(5900, 0)])])), SmsLimits())
    assert rep.by_id["anim:0.0"].classe == "manual"
    assert rep.by_id["anim:0.0"].motivo == "estourou-apos-escala"


def test_pose_beyond_sat_is_unsupported():
    pose = sprite(0, w=256, h=512, pixels=bytes([1] * (256 * 512)))
    rep = classify_character(char_with([pose], dict([anim(0, [frame(5900, 0)])])), SmsLimits())
    assert rep.by_id["anim:0.0"].classe == "unsupported"
    assert rep.by_id["anim:0.0"].motivo.startswith("sat>")


def test_overfull_palette_is_manual():
    px = bytes((i % 33) + 1 for i in range(64))        # 33 cores uteis
    rep = classify_character(char_with([sprite(0, 8, 8, px)]), SmsLimits())
    assert rep.by_id["sprite:5900,0"].classe == "manual"
    assert rep.by_id["sprite:5900,0"].motivo.startswith("paleta>15uteis")


def test_sound_pcm_is_unsupported():
    s = snd.Sound(100, 0, b"RIFF", 1, 11025, 1, 100, None)
    rep = classify_character(char_with(sounds=[s]), SmsLimits())
    assert rep.by_id["sound:100,0"].classe == "unsupported"
    assert rep.by_id["sound:100,0"].motivo == "pcm>psg"


def test_command_beyond_sms_pad_is_manual():
    def cmd(name, raw):
        k = cmdmod.Key(raw)
        st = cmdmod.Step([k])
        return cmdmod.Command(name, [st], 1, 0, 1, raw)
    rep = classify_character(
        char_with(commands=[cmd("punch", "a"), cmd("kick", "b"), cmd("holdF", "F")]), SmsLimits())
    assert rep.by_id["cmd:punch"].classe == "direct"
    assert rep.by_id["cmd:holdF"].classe == "direct"      # maiuscula = direcao, nao botao
    assert rep.by_id["cmd:kick"].classe == "manual"
    assert rep.by_id["cmd:kick"].motivo.startswith("botao>pad")


def test_state_controllers_inherit_converter_fidelity():
    cc = C.CController("displaytocds", "DisplayToClipboard", "direct", [], b"", [])
    st = CState(0, "personagem", ord("S"), ord("I"), ord("N"), {}, {}, [cc])
    rep = classify_character(char_with(states={0: st}), SmsLimits())
    assert rep.by_id["state:0:0"].classe == "direct"


def test_totals_match_per_element():
    pose = sprite(0, w=72, h=64)
    rep = classify_character(char_with([pose], dict([anim(0, [frame(5900, 0)])]),
                                       sounds=[snd.Sound(1, 0, b"x", 1, 1, 1, 1, None)]), SmsLimits())
    from collections import Counter
    assert rep.totals == dict(Counter(e.classe for e in rep.per_element))
    assert set(rep.totals) <= {"direct", "approximate", "manual", "unsupported"}
