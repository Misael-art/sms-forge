"""Lote B — modelo de fila do stream de patterns (espelho de main.c v033).

O runtime autoritativo continua na ROM; aqui se prova o MODELO que pre-valida
chunk, residencia e pico de pool: 1 par TALL (64 B) por VBlank alternando
lados, cache hit, descarte do pending adversario, eviccao, memo de stall
(epoch, size), pico transitorio e quiescencia apos o ultimo evento.
Expectativas calculadas a mao (frames pares servem o lado 0; impares o lado 1).
"""
from __future__ import annotations

import json

import pytest

from mugen2sms.runtime.commit_budget import (
    PAIR_BYTES,
    POOL_PAIRS,
    Policy,
    Simulator,
    check_pose_fit,
    main,
    plan_problems,
    resident_frames,
    self_check,
    simulate,
)


def test_self_check_retorna_0():
    assert self_check() == 0


def test_constantes_batem_com_o_main_c():
    assert PAIR_BYTES == 64         # 2 tiles TALL x 32 B (main.c:42)
    assert POOL_PAIRS == 128        # 8192 B / 64 B por par TALL


def test_residencia_alternada_um_par_por_frame_util():
    r = simulate([{"frame": 0, "side": 0, "pose": 1, "pairs": 3}])
    assert r.timeline == [(0, 1), (2, 1), (4, 1)]
    assert r.completions == [(4, 0, 1)]
    assert r.totals["uploaded_pairs"] == 3
    assert r.totals["stalls"] == 0 and r.totals["evictions"] == 0
    assert resident_frames(3) == 6   # pior caso: 3 turnos x 2 frames


def test_sem_espaco_evicta_o_current_do_adversario():
    # 60+60 pre-carregados: 16 pares so' entram evictando o cur do lado 1,
    # que ocupava 60..120; a pose 12 sobe em 60..76 e completa no 16o turno.
    r = simulate(
        [{"frame": 0, "side": 0, "pose": 12, "pairs": 16}],
        preloads=[{"side": 0, "pose": 10, "pairs": 60},
                  {"side": 1, "pose": 11, "pairs": 60}])
    assert r.totals["evictions"] == 1
    assert r.totals["stalls"] == 0 and r.totals["dropped_pending"] == 0
    assert r.completions == [(30, 0, 12)]


def test_stall_com_memo_de_epoch_e_size_nao_retenta():
    # Pool 100% ocupado pelo current do lado 1; duas tentativas identicas:
    # a segunda e' memo stall (mesmo epoch, mesmo size).
    r = simulate(
        [{"frame": 0, "side": 1, "pose": 21, "pairs": 1},
         {"frame": 1, "side": 1, "pose": 21, "pairs": 1}],
        preloads=[{"side": 1, "pose": 20, "pairs": 128}])
    assert r.totals["requests"] == 2
    assert r.totals["stalls"] == 2 and r.totals["memo_stalls"] == 1
    assert r.totals["alloc_fail"] == 1 and r.totals["evictions"] == 0
    assert r.completions == []


def test_descarte_do_pending_adversario_libera_antes_da_eviccao():
    # 40+40 pre-carregados: a pose 50 (lado 1, 16 pares) entra em 80..96;
    # a pose 33 (lado 0, 48 pares) nao cabe em buraco nenhum e descarta o
    # pending do lado 1 em vez de evictar o current; completa em 0x3800-.
    r = simulate(
        [{"frame": 0, "side": 1, "pose": 50, "pairs": 16},
         {"frame": 2, "side": 0, "pose": 33, "pairs": 48}],
        preloads=[{"side": 0, "pose": 30, "pairs": 40},
                  {"side": 1, "pose": 31, "pairs": 40}])
    assert r.totals["dropped_pending"] == 1
    assert r.totals["evictions"] == 0 and r.totals["stalls"] == 0
    assert all(c[2] != 50 for c in r.completions)
    assert r.completions == [(96, 0, 33)]    # 48 turnos do lado 0 desde f2


def test_cache_hit_no_pre_carregado_nao_vira_pend():
    r = simulate(
        [{"frame": 0, "side": 0, "pose": 10, "pairs": 60},
         {"frame": 5, "side": 0, "pose": 10, "pairs": 60}],
        preloads=[{"side": 0, "pose": 10, "pairs": 60}])
    assert r.totals["cache_hits"] == 2 and r.totals["requests"] == 2
    assert r.completions == [] and r.totals["alloc_fail"] == 0


def test_pico_transitorio_nao_e_o_estado_final():
    # Regressao do max_used_pairs: 60+60 vivos + 8 pendentes = 128/128 no
    # instante do pedido; depois cede (completude do lado 0) para 68 e o novo
    # pend de 16 no buraco (base 0) leva a 84. O pico ficou em 128.
    sim = Simulator()
    sim.boot_preload(0, 10, 60)
    sim.boot_preload(1, 11, 60)
    sim.request(0, 12, 8)
    assert sim.used_pairs() == 128 and sim.peak_used == 128
    for f in range(15):
        sim.stream(f)
    assert sim.used_pairs() == 68    # completou em f14: 8 + 60
    sim.request(1, 13, 16)
    assert sim.used_pairs() == 84 and sim.peak_used == 128


def test_simulate_reporta_pico_e_conclui_apos_o_ultimo_evento():
    r = simulate(
        [{"frame": 0, "side": 0, "pose": 12, "pairs": 8},
         {"frame": 20, "side": 1, "pose": 13, "pairs": 16}],
        preloads=[{"side": 0, "pose": 10, "pairs": 60},
                  {"side": 1, "pose": 11, "pairs": 60}])
    assert r.totals["max_used_pairs"] == 128
    # 8 pares do lado 0 completam em f14; 16 do lado 1 (base 0) em f51.
    assert r.completions == [(14, 0, 12), (51, 1, 13)]


def test_encaixe_de_pose_sinaliza_erro_e_aviso():
    assert check_pose_fit(64) == ([], [])
    err, warn = check_pose_fit(65)   # 65*2 > 128: nao coexiste espelhado
    assert err == [] and warn != []
    assert check_pose_fit(129)[0] != []   # nao cabe no pool
    assert check_pose_fit(0)[0] != []


def test_policy_de_chunk_maior_sobe_mais_por_turno():
    r = simulate([{"frame": 0, "side": 0, "pose": 5, "pairs": 4}],
                 Policy(pairs_per_upload=2))
    assert r.timeline == [(0, 2), (2, 2)]
    assert r.completions == [(2, 0, 5)]
    assert resident_frames(4, Policy(pairs_per_upload=2)) == 4
    assert Policy(alternate_sides=False).upload_sides(3) == [0, 1]


def test_preload_acima_do_pool_e_contrato_violado():
    with pytest.raises(ValueError):
        simulate([], preloads=[{"side": 0, "pose": 1, "pairs": 64},
                               {"side": 1, "pose": 2, "pairs": 65}])


def test_plan_problems_marca_pose_inviavel_e_aviso():
    problems = plan_problems(
        {"events": [{"side": 0, "pose": 1, "pairs": 129}]})
    assert problems and "pose 1" in problems[0]
    problems = plan_problems(
        {"events": [{"side": 0, "pose": 2, "pairs": 65}]})
    assert problems and "aviso" in problems[0]
    assert plan_problems({"events": [{"side": 0, "pose": 3, "pairs": 32}]}) == []


def test_cli_contrato_violado_vira_problema_sem_traceback(tmp_path, capsys):
    payload = {"preloads": [{"side": 0, "pose": 1, "pairs": 64},
                            {"side": 1, "pose": 2, "pairs": 65}],
               "events": []}
    path = tmp_path / "events.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    code = main(["--events", str(path)])
    out = capsys.readouterr().out
    assert code == 1
    assert "[PROBLEMA]" in out and "simulacao:" in out
    assert "Traceback" not in out


def test_cli_grava_relatorio_json_com_schema(tmp_path):
    events = tmp_path / "events.json"
    events.write_text(json.dumps(
        {"events": [{"frame": 0, "side": 0, "pose": 1, "pairs": 3}]}),
        encoding="utf-8")
    report_path = tmp_path / "report.json"
    assert main(["--events", str(events), "--json", str(report_path)]) == 0
    rep = json.loads(report_path.read_text(encoding="utf-8"))
    assert rep["schema"] == "mugen2sms.commit-budget/v1"
    assert rep["ok"] and rep["problems"] == []
    assert rep["totals"]["uploaded_pairs"] == 3
    assert rep["totals"]["max_used_pairs"] == 3
    assert rep["completions"] == [[4, 0, 1]]
