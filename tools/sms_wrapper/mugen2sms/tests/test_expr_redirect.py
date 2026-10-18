# Escopo por virgula do MUGEN (`enemynear, life`) no parser SMS.
# Motivo real: analysis/move_checklist.py abortava ao ler o ryu.zip (SFZ) do Lote D.
# Host apenas: nao prova emulador nem fidelidade de runtime.
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # tools/sms_wrapper
from mugen2sms.ir import expr as E                              # noqa: E402
from mugen2sms.ir import opcodes as O                           # noqa: E402


@pytest.fixture()
def ctx():
    return E.Ctx(commands={"hy1_w": 0}, constants={}, anims=set())


def trg(name):
    """Os bytes que um TRG desse campo ocupa no bytecode."""
    return bytes([O.OP["TRG"], O.TRIGGER[name]])


def test_enemynear_life_mapeia_para_o_campo_p2_real(ctx):
    ce = E.compile_expr("enemynear, life > 0", ctx)
    assert trg("p2life") in ce.code
    assert ce.unsupported == []


def test_enemynear_campos_com_gemeo_p2(ctx):
    for mugen, sms in [("stateno", "p2stateno"), ("statetype", "p2statetype"),
                       ("movetype", "p2movetype"), ("ctrl", "p2ctrl")]:
        ce = E.compile_expr(f"EnemyNear,{mugen} = 1", ctx)
        assert trg(sms) in ce.code, mugen
        assert ce.unsupported == [], mugen


def test_root_eh_o_proprio_no_runtime_sem_helper(ctx):
    # root,X com o runtime 1v1 sem helpers e o estado do proprio lutador.
    ce = E.compile_expr("root, stateno = 120", ctx)
    assert trg("stateno") in ce.code
    assert ce.unsupported == []


def test_campo_sem_equivalente_vira_unsupported_declarado(ctx):
    # enemynear,numpartner e o caso que travava o ryu.zip: existe no MUGEN, nao no VM SMS.
    ce = E.compile_expr("EnemyNear,NumPartner = 0", ctx)
    assert ce.unsupported == ["trigger 'enemynear,numpartner'"]


def test_dois_campos_apos_o_escopo(ctx):
    # enemynear,screenpos x: o campo e das duas palavras TWO_WORD do parser.
    ce = E.compile_expr("enemynear, screenpos x > 100", ctx)
    assert ce.unsupported == ["trigger 'enemynear,screenpos x'"]


def test_target_e_helper_ficam_visiveis_sem_abortar(ctx):
    ce = E.compile_expr("target, stateno = 52", ctx)
    assert ce.unsupported == ["trigger 'target,stateno'"]
    ce = E.compile_expr("helper(id=310), alive", ctx)
    assert ce.unsupported == ["trigger 'helper,alive'"]


def test_enemy_com_indice_explicito_nao_e_1v1(ctx):
    ce = E.compile_expr("enemy(1), life > 0", ctx)
    assert ce.unsupported == ["trigger 'enemy(1),life'"]


def test_virgula_fora_de_escopo_continua_reprovada(ctx):
    # A virgula so e grammar quando ha palavra de escopo antes. Sem isso, `a, b`
    # continua erro: torna-la curinga engoliria expressoes quebradas em gap inocuo.
    with pytest.raises(E.ExprError):
        E.compile_expr("life, life", ctx)
    with pytest.raises(E.ExprError):
        E.compile_expr("stateno = 52, ", ctx)


def test_escopo_dentro_de_parentese_e_intervalo(ctx):
    # forma exata do ryu.cns que reprovava, com intervalo ao lado.
    ce = E.compile_expr("((EnemyNear,NumPartner = 0 && PalNo = [1,6]))", ctx)
    assert "trigger 'enemynear,numpartner'" in ce.unsupported


def test_partner_e_escopo_de_team_mode_fora_do_runtime(ctx):
    # forma real do ryu.cns: `( Partner , Name = "Ken" )` em contexto de IA.
    ce = E.compile_expr('(partner, name = "Ken by M.M.R.")', ctx)
    assert "trigger 'partner,name'" in ce.unsupported


def test_enemynear_com_const_nao_aborta(ctx):
    # enemynear,const(data.attack) existe no MUGEN; o VM SMS nao tem p2defence/attack.
    ce = E.compile_expr("enemynear, const(data.attack) > 0", ctx)
    assert ce.unsupported == ["trigger 'enemynear,const(data.attack)'"]
