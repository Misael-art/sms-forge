"""Lista de valores MUGEN no lado direito de uma comparacao (`X = v1, v2, v3`).

Medido no acervo do Lote D (ryu.zip, SFZ): 4 abortos de parse em 2764 linhas de
trigger, todos da forma `enemynear,HitDefAttr = SCA, HA,HT,HP`. O campo
hitdefattr NAO existe na VM deste runtime (opcodes.TRIGGER), entao o unico
resultado honesto e UM gap declarado que avalia 0 — nunca inventar campo de VM,
nunca silenciar, nunca abortar o personagem inteiro.
"""
import pytest

from mugen2sms.ir import expr as E
from mugen2sms.ir import opcodes as O
from mugen2sms.ir import vm


def ctx():
    return E.Ctx(commands={}, constants={}, anims=set())


def compile_(text):
    return E.compile_expr(text, ctx())


def test_hitdefattr_value_list_parses_without_abort():
    ce = compile_("enemynear, HitDefAttr = SCA, HA, HT, HP")
    assert O.OP["UNSUPPORTED"] in ce.code


def test_hitdefattr_value_list_is_one_declared_gap_naming_the_field():
    ce = compile_("enemynear, HitDefAttr = SCA, HA, HT, HP")
    assert len(ce.unsupported) == 1
    rec = ce.unsupported[0].lower()
    assert "hitdefattr" in rec
    assert "sca" in rec and "hp" in rec


def test_value_list_inside_a_real_conjunction():
    # linha 1529 de ryu.cmd, exatamente como está no acervo
    ce = compile_("stateno = 410 && movehit || p2statetype != A && "
                  "enemynear,HitDefAttr = SCA, HA,HT,HP && p2bodydist X = [-5,100]")
    assert any("hitdefattr" in u.lower() for u in ce.unsupported)


def test_representable_field_with_list_is_gap_not_silence():
    ce = compile_("stateno != 100, 200")
    assert len(ce.unsupported) == 1
    assert O.OP["UNSUPPORTED"] in ce.code


def test_comma_inside_call_args_is_still_an_argument_separator():
    ce = compile_('ifelse(ctrl = 1, 2, 3)')
    assert O.OP["IFELSE"] in ce.code
    assert not any("lista" in u for u in ce.unsupported)


def test_animelem_comma_clause_is_not_a_value_list():
    # `animelem = 3, >= 5` ja e tratado como clausula propria, nao como lista
    ce = compile_("animelem = 3, >= 5")
    assert O.OP["ANIMELEMTIME"] in ce.code
    assert ce.unsupported == []


def test_animelem_comma_interval_checks_element_time_range():
    # Forma real de superturbo.cns: element 2, elapsed ticks 0 through 16.
    ce = compile_("AnimElem = 2,[0,16]")
    assert O.OP["ANIMELEMTIME"] in ce.code
    assert bytes([O.OP["INRANGE"], 3]) in ce.code  # both interval bounds are inclusive
    assert ce.unsupported == []


@pytest.mark.parametrize(("ticks", "expected"), [(-1, False), (0, True), (16, True), (17, False)])
def test_animelem_comma_interval_vm_boundaries(ticks, expected):
    class Env:
        def animelemtime(self, element):
            assert element == 2
            return ticks

    assert bool(vm.run(compile_("AnimElem = 2,[0,16]").code, Env())) is expected


def test_animelem_without_time_clause_still_requires_element_start():
    class Env:
        def animelemtime(self, element):
            assert element == 3
            return 0

    assert vm.run(compile_("animelem = 3").code, Env()) == O.FX


def test_timemod_comma_clause_keeps_modulo_semantics():
    class Env:
        def trg(self, trigger):
            assert trigger == O.TRIGGER["time"]
            return 4 * O.FX

    ce = compile_("timemod = 3, 1")
    assert O.OP["MOD"] in ce.code
    assert O.OP["EQ"] in ce.code
    assert vm.run(ce.code, Env()) == O.FX


def test_value_list_evaluates_false_in_the_vm():
    ce = compile_("enemynear, HitDefAttr = SCA, HA, HT, HP")
    assert O.OP["UNSUPPORTED"] in ce.code
    assert ce.constant is None
