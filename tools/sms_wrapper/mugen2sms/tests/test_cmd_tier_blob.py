"""Blob `_CMD_` versionado com tier por tempo de pressao (GDD 2026-09-30 / doc/22).

O pad SMS tem duas teclas fisicas; o mapa do GDD da uma familia por tecla e o
tempo de pressao escolhe a forca. O blob antigo so sabia `a`/`s`, entao `c`,
`x` e `z` eram pulados como `botao>pad` e o runtime nao tinha o que consultar.
"""
from mugen2sms.converters import sms_cmd
from mugen2sms.converters.sms_controls import ControlMap, DEFAULT_MAP
from mugen2sms.parsers import cmd as cmdmod


def _command(name: str, text: str) -> cmdmod.Command:
    steps, errors = cmdmod.parse_command_string(text)
    return cmdmod.Command(name, steps, 15, 1, 1, text, errors)


def test_mapa_do_gdd_converte_as_quatro_teclas_em_bit_de_tecla_mais_tier():
    patterns, skipped = sms_cmd.to_patterns(
        [_command(n, n) for n in ("a", "c", "x", "z")], DEFAULT_MAP)
    assert skipped == {}
    by_name = {p.name: p.steps[0] for p in patterns}
    assert (by_name["a"].keys, by_name["a"].tier) == (0x01, 1)
    assert (by_name["c"].keys, by_name["c"].tier) == (0x01, 2)
    assert (by_name["x"].keys, by_name["x"].tier) == (0x02, 1)
    assert (by_name["z"].keys, by_name["z"].tier) == (0x02, 2)


def test_tier_do_meio_descartado_por_decisao_nao_e_falha_de_pad():
    patterns, skipped = sms_cmd.to_patterns([_command("mp", "b")], DEFAULT_MAP)
    assert patterns == []
    assert skipped == {"mp": "botao-sem-tier-no-mapa"}


def test_sem_mapa_o_comportamento_legado_e_preservado():
    patterns, skipped = sms_cmd.to_patterns([_command("c", "c")])
    assert patterns == []
    assert skipped == {"c": "botao>pad"}


def test_direcoes_e_diagonais_continuam_no_nibble_de_direcao():
    patterns, skipped = sms_cmd.to_patterns([_command("df_c", "DF, c")], DEFAULT_MAP)
    assert skipped == {}
    first, second = patterns[0].steps
    assert (first.dir, first.keys, first.tier) == (0x0A, 0, 0)
    assert (second.dir, second.keys, second.tier) == (0, 0x01, 2)


def test_serializar_prefixa_a_versao_do_formato():
    pattern = sms_cmd.Pattern("hp", window=15, buffer=1,
                              steps=[sms_cmd.StepCode(keys=0x01, tier=2)])
    assert sms_cmd.serialize_pattern(pattern) == bytes(
        [sms_cmd.BLOB_FMT_VERSION, 1, 15, 1, 0x10, 0x08, 0])


def test_source_route_command_symbols_are_stable_c_identifiers():
    rising = sms_cmd.route_command_prefix("Rising Tackle_x")
    assert rising.startswith("CUT_R_RISI_")
    assert sms_cmd.route_command_symbol("Rising Tackle_x", 0) == f"{rising}_0"
    assert sms_cmd.route_command_prefix("RISING/TACKLE_X") == rising
    assert sms_cmd.route_command_prefix("Power Geyser") != sms_cmd.route_command_prefix("Power Wave")
    assert len("RYU_" + sms_cmd.route_command_symbol("Rising Tackle_x", 9)) <= 27


def test_hold_e_release_dividem_o_byte_de_flags_com_o_tier():
    pattern = sms_cmd.Pattern("charge", window=15, buffer=1, steps=[
        sms_cmd.StepCode(dir=0x04, hold=True),
        sms_cmd.StepCode(keys=0x02, release=True, tier=1)])
    assert sms_cmd.serialize_pattern(pattern)[4:] == bytes(
        [0x04, 0x01, 0, 0x20, 0x06, 0])


def test_four_way_modificador_ocupa_bit_4_sem_interferir_no_tier():
    patterns, skipped = sms_cmd.to_patterns(
        [_command("flex_down", "$D"), _command("flex_forward", "/$F, x")],
        DEFAULT_MAP)
    assert skipped == {}
    by_name = {p.name: p for p in patterns}
    assert by_name["flex_down"].steps[0].four_way is True
    assert sms_cmd.serialize_pattern(by_name["flex_down"])[5] == 0x10
    assert sms_cmd.serialize_pattern(by_name["flex_down"])[6] == 0
    forward, button = by_name["flex_forward"].steps
    assert forward.four_way and forward.hold and forward.dir == 0x08
    assert sms_cmd.serialize_pattern(by_name["flex_forward"])[5] == 0x11
    assert button.tier == 1


def test_dois_tiers_da_mesma_tecla_nao_geram_padrao_ambiguo():
    patterns, skipped = sms_cmd.to_patterns([_command("chord", "a+c")], DEFAULT_MAP)
    assert patterns == []
    assert skipped == {"chord": "acorde-na-mesma-tecla"}


def test_runtime_so_suporta_dois_tiers_apesar_do_campo_codificar_tres():
    tres = ControlMap({"1": ["a", "b", "c"]}, {"1": [6, 14]})
    patterns, skipped = sms_cmd.to_patterns([_command("mp", "b")], tres)
    assert skipped == {}
    assert patterns[0].steps[0].tier == 2
    patterns, skipped = sms_cmd.to_patterns([_command("hp3", "c")], tres)
    assert patterns == []
    assert skipped == {"hp3": "tier-acima-da-maquina-runtime"}
    quatro = ControlMap({"1": ["a", "b", "c", "x"]}, {"1": [6, 10, 14]})
    patterns, skipped = sms_cmd.to_patterns([_command("x", "x")], quatro)
    assert patterns == []
    assert skipped == {"x": "tier-acima-de-3-niveis"}


def test_acorde_entre_teclas_com_o_mesmo_tier_e_viavel():
    """soco fraco + chute fraco = KEY_1 + KEY_2 no mesmo tick: um passo, dois bits."""
    patterns, skipped = sms_cmd.to_patterns([_command("cross", "a+x")], DEFAULT_MAP)
    assert skipped == {}
    step = patterns[0].steps[0]
    assert (step.keys, step.tier) == (0x03, 1)


def test_acorde_entre_teclas_com_tiers_diferentes_nao_esmagado_para_o_maior():
    """Um passo so tem UM campo de tier: `a+z` (fraco na tecla 1, forte na 2) nao e
    representavel. Esmagar para o maximo faria o blob pedir o pulso forte tambem na
    tecla 1 — um padrao que nenhum toque do jogador produz. Melhor pular e reportar."""
    patterns, skipped = sms_cmd.to_patterns([_command("cross", "a+z")], DEFAULT_MAP)
    assert patterns == []
    assert skipped == {"cross": "acorde-entre-teclas-tiers-diversos"}


def test_modificadores_sem_representacao_no_blob_sao_rejeitados():
    patterns, skipped = sms_cmd.to_patterns(
        [_command("timed_release", "~15$D, U, x"),
         _command("strict", ">D, DF, F, x")], DEFAULT_MAP)
    assert [p.name for p in patterns] == ["timed_release"]
    assert skipped == {
        "strict": "strict-step-nao-suportado-no-runtime",
    }
    first = patterns[0].steps[0]
    assert (first.dir, first.release, first.rel_time, first.four_way) == (2, True, 15, True)
    assert sms_cmd.serialize_pattern(patterns[0])[4:7] == bytes([0x02, 0x12, 15])


def test_timed_release_fails_closed_outside_single_cardinal_direction():
    patterns, skipped = sms_cmd.to_patterns(
        [_command("timed_button", "~15x"),
         _command("timed_chord", "~15D+U"),
         _command("too_long", "~256D"),
         _command("not_first", "D, ~15U"),
         _command("two_timed", "~3D, ~4U")], DEFAULT_MAP)
    assert patterns == []
    assert skipped == {
        "timed_button": "release-time-exige-uma-direcao-cardinal",
        "timed_chord": "release-time-exige-uma-direcao-cardinal",
        "too_long": "release-time-acima-de-255",
        "not_first": "release-time-deve-ser-primeiro-passo",
        "two_timed": "multiplos-release-times-nao-suportados",
    }
