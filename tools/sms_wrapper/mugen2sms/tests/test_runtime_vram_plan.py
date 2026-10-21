"""Lote B — planta de VRAM do runtime: regras que o hardware impoe.

O validador julga a planta DECLARADA (Lote B, VRAM map): reg6 (sprite na
primeira metade), PNT/SAT canonicos da SMSlib, 448 tiles uteis de BG, limite
de 16 KiB, sobreposicao entre consumidores e o tile de reserva (fundo da PNT)
caindo dentro de regiao reescrita em runtime. Expectativas calculadas a mao a
partir das constantes de SMSlib verificadas no cabecalho.
"""
from __future__ import annotations

import json

from mugen2sms.runtime.vram_plan import (
    PNT_ADDR,
    PNT_BYTES,
    SAT_ADDR,
    SAT_BYTES,
    TILE_BYTES,
    Plan,
    Region,
    blank_tile_hazards,
    gaps,
    load_plan,
    plan_luta_mugem_rev2,
    report,
    self_check,
    validate,
)


def test_self_check_retorna_0():
    assert self_check() == 0


def test_planta_do_consumidor_limitada_so_pela_reserva_no_pool():
    # v033: pool 0..0x2000 (128 pares), PNT 0x3800, SAT 0x3F00; a violacao
    # estrutural e' nenhuma — o unico risco e' o tile 255 (0x1FE0) dentro do
    # pool reescrito pelo stream.
    rep = report(plan_luta_mugem_rev2(pairs=128, blank_tile=255))
    assert rep["schema"] == "mugen2sms.vram-plan/v1"
    assert rep["violations"] == []
    assert len(rep["blank_tile_hazards"]) == 1
    assert "0x1FE0..0x1FFF" in rep["blank_tile_hazards"][0]


def test_reserva_fora_do_pool_com_pattern_dedicado_passa():
    p = plan_luta_mugem_rev2(pairs=126, blank_tile=254)
    p.regions.append(Region("blank", 254 * TILE_BYTES, TILE_BYTES,
                            kind="bg_patterns", note="pattern zerado"))
    rep = report(p)
    assert rep["ok"] and rep["violations"] == []
    assert rep["blank_tile_hazards"] == []


def test_pool_de_sprite_nao_cruza_a_janela_do_reg6():
    ok = Plan(regions=[Region("pool", 0x0000, 0x2000, kind="sprite_patterns")])
    assert validate(ok) == []          # 0x0000..0x1FFF e' a primeira metade
    bad = Plan(regions=[Region("pool", 0x1000, 0x2000,
                               kind="sprite_patterns")])
    assert any("reg6" in v for v in validate(bad))


def test_bg_para_no_tile_447_antes_da_pnt():
    ok = Plan(regions=[Region("bg", 0x0000, 0x3800, kind="bg_patterns")])
    assert validate(ok) == []          # 448 tiles = 0x3800 encosta na PNT
    bad = Plan(regions=[Region("bg", 0x3700, 0x100 + TILE_BYTES,
                               kind="bg_patterns")])
    assert any("448 tiles" in v for v in validate(bad))


def test_pnt_e_sat_fora_do_canonico_reprovam():
    bad = Plan(regions=[Region("pnt", 0x3A00, PNT_BYTES, kind="pnt")])
    assert any("PNT declarada" in v for v in validate(bad))
    bad = Plan(regions=[Region("sat", SAT_ADDR, SAT_BYTES - 4, kind="sat")])
    assert any("SAT declarada" in v for v in validate(bad))
    ok = Plan(regions=[Region("pnt", PNT_ADDR, PNT_BYTES, kind="pnt"),
                       Region("sat", SAT_ADDR, SAT_BYTES, kind="sat")])
    assert validate(ok) == []


def test_sobreposicao_entre_consumidores_reprova():
    bad = Plan(regions=[
        Region("pool", 0x0000, 0x3900, kind="sprite_patterns", writable=True),
        Region("pnt", PNT_ADDR, PNT_BYTES, kind="pnt")])
    assert any("sobreposicao" in v for v in validate(bad))


def test_regiao_fora_da_vram_tamanho_invalido_e_kind_desconhecido():
    assert any("fora da VRAM" in v for v in validate(
        Plan(regions=[Region("x", 0x3F80, 0x100, kind="free")])))
    assert any("size" in v for v in validate(
        Plan(regions=[Region("z", 0x0000, 0, kind="free")])))
    assert any("kind desconhecido" in v for v in validate(
        Plan(regions=[Region("y", 0x0000, TILE_BYTES, kind="banana")])))


def test_tile_de_reserva_morando_em_pnt_denuncia():
    # tile 448 = 0x3800 e' o primeiro byte da PNT: "pattern" seria PNT viva
    p = Plan(regions=[Region("pnt", PNT_ADDR, PNT_BYTES, kind="pnt")],
             blank_tile=PNT_ADDR // TILE_BYTES)
    hazards = blank_tile_hazards(p)
    assert len(hazards) == 1 and "PNT" in hazards[0]


def test_tile_de_reserva_fora_do_indice_ou_da_vram():
    assert blank_tile_hazards(Plan(regions=[], blank_tile=512)) != []
    assert blank_tile_hazards(Plan(regions=[], blank_tile=511)) == []


def test_gaps_ignoram_regiao_free_e_ordenam_por_endereco():
    p = plan_luta_mugem_rev2(pairs=127, blank_tile=254)
    p.regions.append(Region("reserva", 0x0000, TILE_BYTES, kind="free"))
    assert gaps(p) == [(0x1FC0, 0x3800 - 0x1FC0), (0x3E00, 0x100)]


def test_load_plan_le_hex_e_defaults(tmp_path):
    raw = {"regions": [{"name": "pool", "start": "0x0000", "size": "0x2000",
                        "kind": "sprite_patterns", "writable": True}],
           "blank_tile": "0xFE", "sprite_first_half": True}
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    p = load_plan(path)
    assert p.regions[0].start == 0x0000 and p.regions[0].size == 0x2000
    assert p.regions[0].writable is True
    assert p.blank_tile == 0xFE
    assert validate(p) == []
