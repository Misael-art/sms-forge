"""Trilha por tick x duracoes do AIR: quanto cada quadro de uma acao demorou alem do contrato (doc/21 itens 2+3).

Entrada: uma trilha de `luta_mugen_trace_dap.py` (campos pN_state/pN_frame/pN_tick/pN_hitstop) e a acao AIR do
estado analisado. Para cada quadro da acao mede, em ticks, quanto ele ficou em tela (descontando ticks de hitstop,
em que a logica congela) e compara com `time` do AIR. A diferenca e o ATRASO do quadro (stall).

Leitura causal, com limite: no runtime (fight.c tick_anim) o contador `tick` so avanca quando a pose desejada ja
esta visivel; durante a espera ele fica parado. Um quadro cuja duracao medida excede o `time` do AIR e cujo
`tick` ficou parado em 0 por pelo menos esse atraso (`lead0`) e, portanto, compativel com espera de pose (streaming), nao com dado de AIR nem com
entrada. Isto e inferencia do codigo + trilha, nao a medicao direta da pose visivel.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def frame_segments(trace: list[dict], side: str, state: int) -> list[dict]:
    """Segmentos consecutivos (quadro) dentro da PRIMEIRA permanencia continua no estado."""
    segs: list[dict] = []
    started = False
    for r in trace:
        if r[f"{side}_state"] != state:
            if started:
                break
            continue
        started = True
        fr = r[f"{side}_frame"]
        if not segs or segs[-1]["frame"] != fr:
            segs.append({"frame": fr, "start": r["tick"], "ticks": 0, "hitstop": 0, "lead0": 0, "_lead": True})
        s = segs[-1]
        s["ticks"] += 1
        s["hitstop"] += r[f"{side}_hitstop"]
        if not r[f"{side}_hitstop"] and s["_lead"]:        # hitstop congela o contador: nao conta nem encerra
            if r[f"{side}_tick"] == 0:
                s["lead0"] += 1
            else:
                s["_lead"] = False
    return segs


def analyze(trace: list[dict], side: str, state: int, air_frames, truncated_ok: bool = False) -> dict:
    segs = frame_segments(trace, side, state)
    rows = []
    for s in segs:
        f = air_frames[s["frame"]] if s["frame"] < len(air_frames) else None
        air = None if f is None else f.time
        observed = s["ticks"] - s["hitstop"]
        rows.append({**s, "air_time": air, "observed_active": observed,
                     "stall": None if air is None or air < 0 else observed - air})
        rows[-1]["hold_explains_stall"] = (rows[-1]["stall"] is None or rows[-1]["stall"] <= 0
                                           or s["lead0"] >= rows[-1]["stall"])
    # o ultimo segmento pode estar cortado pelo fim da janela: nao conta como medida de quadro completo
    last_open = bool(trace) and segs and segs[-1]["start"] + segs[-1]["ticks"] >= trace[-1]["tick"] + 1
    complete = rows[:-1] if last_open and not truncated_ok else rows
    done = [r for r in complete if r["stall"] is not None]
    return {"side": side, "state": state, "segments": rows, "last_segment_open": bool(last_open),
            "complete_frames": len(done),
            "air_total": sum(r["air_time"] for r in done),
            "observed_total": sum(r["observed_active"] for r in done),
            "stall_total": sum(r["stall"] for r in done),
            "slowdown": (round(sum(r["observed_active"] for r in done) / max(1, sum(r["air_time"] for r in done)), 2)
                         if done else None),
            "all_stalls_explained_by_counter_hold": all(r["hold_explains_stall"] for r in done)}


def first_hit_tick(trace: list[dict], side: str, state: int) -> int | None:
    """Tick em que hit_done passa a 1 dentro do estado (momento em que a logica registrou o golpe)."""
    for r in trace:
        if r[f"{side}_state"] == state and r[f"{side}_hit_done"]:
            return r["tick"]
    return None


def display_sync(profile: list[dict], state: int, pose_of_frame, last_pose_ok: bool = True) -> dict:
    """Sincronia entre a pose LOGICA (p1_frame -> pose) e a pose EXIBIDA (vis_pose_p1) dentro de uma permanencia
    no estado. Perfil do `luta_mugen_trace_dap.py --profile`. Mede a defasagem da arte, nao o tempo da logica."""
    ticks = [r for r in profile if r["p1_state"] == state]
    if not ticks:
        return {"ticks": 0}
    synced = sum(1 for r in ticks if r["vis_pose_p1"] == pose_of_frame(r["p1_frame"]))
    shown, order = {}, []
    for r in ticks:
        v = r["vis_pose_p1"]
        shown[v] = shown.get(v, 0) + 1
        if not order or order[-1] != v:
            order.append(v)
    logical = sorted({pose_of_frame(r["p1_frame"]) for r in ticks})
    return {"ticks": len(ticks), "synced_ticks": synced, "synced_fraction": round(synced / len(ticks), 3),
            "displayed_poses_in_order": order, "ticks_per_displayed_pose": shown,
            "logical_poses": logical, "logical_poses_never_displayed": [p for p in logical if p not in shown]}


def self_check() -> int:
    from ..parsers.air import Frame
    air = [Frame(0, 0, 0, 0, 2), Frame(0, 1, 0, 0, 1), Frame(0, 2, 0, 0, 2)]

    def row(t, fr, tick, hs=0, st=6):
        return {"tick": t, "p1_state": st, "p1_frame": fr, "p1_tick": tick, "p1_hitstop": hs, "p1_hit_done": 0}
    # contrato cumprido: 2+1+2 ticks
    ok_trace = [row(0, 0, 0), row(1, 0, 1), row(2, 1, 0), row(3, 2, 0), row(4, 2, 1), row(5, 0, 0, st=0)]
    a = analyze(ok_trace, "p1", 6, air)
    ok = a["stall_total"] == 0 and a["complete_frames"] == 3 and a["slowdown"] == 1.0
    # quadro 0 espera 10 ticks com o contador parado: stall 8, e o hitstop nao conta como atraso
    slow = [row(t, 0, 0) for t in range(10)] + [row(10, 1, 0)] + [row(11, 2, 0, hs=1), row(12, 2, 0, hs=1),
                                                                    row(13, 2, 1), row(14, 0, 0, st=0)]
    b = analyze(slow, "p1", 6, air)
    ok = ok and b["segments"][0]["stall"] == 8 and b["segments"][0]["lead0"] == 10
    ok = ok and b["segments"][2]["hitstop"] == 2 and b["segments"][2]["observed_active"] == 1
    ok = ok and b["segments"][2]["stall"] == -1 and b["segments"][1]["stall"] == 0
    ok = ok and b["complete_frames"] == 3 and b["air_total"] == 5 and b["observed_total"] == 12
    ok = ok and b["stall_total"] == 7 and b["slowdown"] == 2.4 and b["all_stalls_explained_by_counter_hold"]
    # contador NAO parado + atraso => nao e espera de pose: a inferencia causal deve recusar
    moving = [row(t, 0, 1) for t in range(6)] + [row(6, 1, 0), row(7, 2, 0), row(8, 2, 1), row(9, 0, 0, st=0)]
    ok = ok and not analyze(moving, "p1", 6, air)["all_stalls_explained_by_counter_hold"]
    # janela que termina no meio do quadro: o ultimo quadro nao entra como medida completa
    cut = [row(t, 0, 0) for t in range(4)]
    c = analyze(cut, "p1", 6, air)
    ok = ok and c["last_segment_open"] and c["complete_frames"] == 0
    # outro estado nao contamina
    ok = ok and analyze(ok_trace, "p1", 9, air)["segments"] == []
    prof = [{"p1_state": st, "p1_frame": f, "vis_pose_p1": v} for st, f, v in
            [(6, 0, 9), (6, 0, 9), (6, 1, 9), (6, 2, 10), (6, 3, 10), (6, 3, 12), (0, 0, 0)]]
    d = display_sync(prof, 6, lambda f: 10 + f)
    ok = ok and d["ticks"] == 6 and d["synced_ticks"] == 0 and d["displayed_poses_in_order"] == [9, 10, 12]
    ok = ok and d["logical_poses_never_displayed"] == [11, 13]
    d2 = display_sync(prof, 6, lambda f: {0: 9, 1: 9, 2: 10, 3: 10}[f])
    ok = ok and d2["synced_ticks"] == 5 and d2["synced_fraction"] == round(5 / 6, 3)
    ok = ok and display_sync(prof, 99, lambda f: f) == {"ticks": 0}
    print("self-check trace_vs_air:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None) -> int:
    from .. import character
    from ..source import Source
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trace", type=Path, nargs="?")
    ap.add_argument("package", type=Path, nargs="?")
    ap.add_argument("--scenario")
    ap.add_argument("--side", default="p1")
    ap.add_argument("--state", type=int)
    ap.add_argument("--action", type=int)
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--profile", type=Path, help="trilha de perfil (--profile do produtor): mede a sincronia arte x logica")
    ap.add_argument("--pose-base", type=int, help="pose do quadro 0 da acao (pose = base + quadro)")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    if a.profile:
        if a.pose_base is None or a.state is None or not a.scenario:
            ap.error("--profile exige --scenario --state --pose-base")
        d = display_sync(json.loads(a.profile.read_text())[a.scenario], a.state, lambda f: a.pose_base + f)
        if a.out_json:
            a.out_json.write_text(json.dumps(d, indent=1), encoding="utf-8")
        print(json.dumps(d))
        return 0
    if not (a.trace and a.package and a.scenario and a.state is not None and a.action is not None):
        ap.error("trace package --scenario --state --action obrigatorios sem --self-check")
    trace = json.loads(a.trace.read_text())[a.scenario]
    ch = character.load(Source(a.package))
    if a.action not in ch.anims:
        ap.error(f"acao {a.action} inexistente no AIR")
    rep = analyze(trace, a.side, a.state, ch.anims[a.action].frames)
    rep["first_hit_tick"] = first_hit_tick(trace, a.side, a.state)
    if a.out_json:
        a.out_json.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    for s in rep["segments"]:
        print(f"quadro {s['frame']}: AIR {s['air_time']} | medido {s['observed_active']} (hitstop {s['hitstop']}) | "
              f"stall {s['stall']} | contador parado em 0 por {s['lead0']} ticks | explicado: {s['hold_explains_stall']}")
    print(f"completos {rep['complete_frames']}: AIR {rep['air_total']} ticks, medido {rep['observed_total']}, "
          f"lentidao {rep['slowdown']}x; 1o hit_done no tick {rep['first_hit_tick']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
