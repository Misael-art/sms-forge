# Itens 1 e 2 do doc/21: matriz de golpes e contrato temporal (host; nao prova emulador).
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # tools/sms_wrapper
from mugen2sms import character                                  # noqa: E402
from mugen2sms.analysis import anim_time_contract as T           # noqa: E402
from mugen2sms.analysis import move_checklist as M               # noqa: E402
from mugen2sms.converters import sms_controls as C               # noqa: E402
from mugen2sms.parsers import air                                # noqa: E402
from mugen2sms.source import Source                              # noqa: E402
from mugen2sms.tests.make_fixtures import build                  # noqa: E402


@pytest.fixture()
def ch(tmp_path):
    return character.load(Source(build(tmp_path / "m", with_command_states=True)))


def test_selfchecks_pass():
    assert M.self_check() == 0
    assert T.self_check() == 0
    assert C.self_check() == 0


def test_checklist_rows(ch):
    rows = {tuple(r["commands"]): r for r in M.build(ch)}
    assert rows[("punch",)]["status"] == "OK" and rows[("punch",)]["hitdefs"] == 1
    assert rows[("punch",)]["added_latency_ticks"] == 5
    # QCF (DB,D,DF + a) e digitavel: diagonal = duas direcoes; so o tier custa latencia
    assert rows[("special",)]["status"] == "OK" and rows[("special",)]["pad"]["special"]["ok"]
    assert "estado inexistente:9999" in rows[("holdF",)]["blocking"]


def test_checklist_without_state_minus1_is_empty(tmp_path):
    assert M.build(character.load(Source(build(tmp_path / "m")))) == []


def test_reference_timeline_semantics():
    a = air.parse("[Begin Action 1]\n0,0,0,0,2\nLoopStart\n0,1,0,0,0\n0,2,0,0,3\n").actions[1]
    # time 0 nunca e exibido; laco volta ao LoopStart (aqui o 1o elemento exibivel apos ele)
    assert T.reference_timeline(a.frames, a.loopstart, 10) == [0, 0, 2, 2, 2, 2, 2, 2, 2, 2]


def test_forever_holds_and_runtime_agrees():
    a = air.parse("[Begin Action 1]\n0,0,0,0,2\n0,1,0,0,-1\n").actions[1]
    assert T.reference_timeline(a.frames, 0, 6) == [0, 0, 1, 1, 1, 1]
    assert T.runtime_timeline(a.frames, 0, 6) == [0, 0, 1, 1, 1, 1]


def test_fixture_hit_window_diverges_from_hitdef_trigger(ch):
    rows = {r["action"]: r for r in T.build(ch)}
    r = rows[200]
    assert len(r["hitdef_events"]) == 1
    event = r["hitdef_events"][0]
    assert event["air_start_tick"] == 3
    assert r["hit"]["start_tick_runtime"] == 0          # Clsn1 esta no 1o quadro
    assert event["air_frame"]["clsn1"] is False
    assert "hitdef_trigger_frame_has_no_clsn1" in r["flags"]


def test_stall_shifts_runtime_and_is_reported():
    a = air.parse("[Begin Action 1]\n0,0,0,0,2\n0,1,0,0,2\n").actions[1]
    assert T.action_report(a, horizon=8)["first_divergent_tick"] is None
    assert T.action_report(a, horizon=8, stall=1)["first_divergent_tick"] == 2


def test_three_tier_map_reaches_medium_buttons(ch):
    m3 = C.ControlMap({"1": ["a", "b", "c"], "2": ["x", "y", "z"]}, {"1": [6, 14], "2": [6, 14]})
    assert m3.validate() == [] and m3.unreachable() == []
    assert C.DEFAULT_MAP.unreachable() == ["b", "y"]
    # latencia pior caso: tier fraco = limiar-1; tier k>0 = limiar k
    assert [m3.added_latency("1", t) for t in range(3)] == [5, 5, 13]


def test_medium_buttons_are_dropped_not_blocked(ch, tmp_path):
    from mugen2sms.parsers import cmd as cm
    steps, errs = cm.parse_command_string("b")
    c = cm.Command("mp", steps, 15, 1, 1, "b", errs)
    r = C.command_support(c, C.DEFAULT_MAP)
    assert r["reasons"] == ["botao_sem_tier:b"] and "b" in C.DEFAULT_MAP.dropped
    rt = C.ControlMap.from_json(C.DEFAULT_MAP.to_json())
    assert rt == C.DEFAULT_MAP


def test_trace_compare_catches_tail_loss_that_zip_hides():
    from mugen2sms.analysis import trace_compare as TC
    assert TC.self_check() == 0
    b = {"s": [{"tick": i, "x": i} for i in range(5)]}
    r = TC.compare(b, {"s": b["s"][:3]})
    assert not r["equivalent"] and r["scenarios"][0]["diverging_ticks"] == 0     # zip diria igual
    assert r["scenarios"][0]["length_mismatch"]


def test_trace_producer_pure_parts():
    import importlib.util
    spec = importlib.util.spec_from_file_location("lmt", Path(__file__).resolve().parents[2] / "luta_mugen_trace_dap.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.self_check() == 0
    # todo cenario embutido compila para exatamente a janela gravavel
    for name, (p1, p2) in m.SCENARIOS.items():
        assert sum(n for n, _, _ in m.compile_script(p1, p2)) == m.TRACE_MAX, name


def test_trace_vs_air_distinguishes_hold_from_other_delays():
    from mugen2sms.analysis import trace_vs_air as V
    assert V.self_check() == 0
