"""Contrato temporal AIR -> runtime SMS (doc/21, item 2).

Compara, por acao, a linha do tempo de REFERENCIA do MUGEN (quadro exibido em cada tick) com a do MODELO do
runtime SMS, e mapeia `HitDef` acionados por `Time = N` ou `AnimElem = N` para o elemento AIR correspondente.

Fontes da referencia (nao derivada do runtime SMS; mesma base de tests/test_anim_time_contract.py do forge MD):
  [E] Elecbyte, AIR/CNS: `time` = ticks do elemento; `-1` = segura para sempre; elemento de tempo 0 nao e exibido;
      `LoopStart` marca o elemento onde o laco recomeca.
Modelo do runtime SMS (leitura de codigo, nao medicao):
  - generators/scene_cut.py:461  dur = 255 se time<0, senao max(1, min(254, time), stream_ticks|1)
  - integrada/src/fight.c tick_anim: ++tick >= dur avanca; ultimo quadro: loop_start ou volta ao idle
    (o modelo usa o LoopStart do AIR; como o gerador preenche `loop_start` NAO foi verificado);
    dur==255 segura; o relogio SO anda com a pose desejada visivel (parametro `stall`, nao modelavel estaticamente)
  - integrada/src/fight.c fight_step_full: hit = 1o tick em que o quadro VISIVEL tem Clsn1 sobrepondo a hurtbox;
    o trigger de HitDef ainda precisa estar ligado ao perfil gerado.

Divergencias estaticas (nao dependem de emulador): time 0 virando 1 tick, time>254 truncado, quadros
estendidos por `stream_ticks`, janela de hit != trigger do HitDef. O campo `hitdef_events` conserva as
condicoes CNS, dano, pausa, guarda e velocidade, e mapeia o trigger estático para quadro/tick AIR quando possível.
`stall` e latencia de apresentacao sao
parametros explicitos: o relatorio diz quanto derivaria, nao finge medir.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FOREVER = 255
TIME_EQ = re.compile(r"^\s*time\s*=\s*(\d+)\s*$", re.I)
ANIMELEM_EQ = re.compile(r"^\s*animelem\s*=\s*(\d+)\s*$", re.I)


def reference_timeline(frames, loopstart: int, horizon: int) -> list[int | None]:
    """Indice de quadro exibido em cada tick 0..horizon-1 segundo o MUGEN. None = acao terminou sem laco."""
    shown = [i for i, f in enumerate(frames) if f.time != 0]
    out: list[int | None] = []
    if not shown:
        return [None] * horizon
    first_loop = next((i for i in shown if i >= loopstart), shown[0])
    cur = shown[0]
    while len(out) < horizon:
        f = frames[cur]
        if f.time < 0:
            out += [cur] * (horizon - len(out))
            break
        out += [cur] * f.time
        nxt = next((i for i in shown if i > cur), None)
        cur = nxt if nxt is not None else first_loop
    return out[:horizon]


def distill_duration(time: int, stream_ticks: int = 1) -> int:
    """Copia literal da formula de scene_cut.py:461 (caminho `uniformly_scaled` usa stream_ticks=1)."""
    return FOREVER if time < 0 else max(1, min(254, time), stream_ticks)


def runtime_timeline(frames, loopstart: int, horizon: int, stream_ticks=None, stall: int = 0) -> list[int | None]:
    """Quadro exibido por tick no modelo de fight.c. `stall` = ticks extras de espera por quadro (pose nao visivel)."""
    durs = [distill_duration(f.time, (stream_ticks or {}).get(i, 1)) for i, f in enumerate(frames)]
    out: list[int | None] = []
    cur = 0
    while len(out) < horizon:
        if durs[cur] == FOREVER:
            out += [cur] * (horizon - len(out))
            break
        out += [cur] * (durs[cur] + stall)
        if cur + 1 >= len(frames):
            if loopstart is None:
                out += [None] * (horizon - len(out))   # volta ao idle
                break
            cur = loopstart
        else:
            cur += 1
    return out[:horizon]


def hit_window(frames) -> dict:
    """1o quadro com Clsn1 e o tick em que comeca, pelo AIR (referencia) e pelo runtime (durs destiladas)."""
    ref_t = run_t = 0
    for i, f in enumerate(frames):
        if f.clsn1:
            return {"frame": i, "start_tick_ref": ref_t, "start_tick_runtime": run_t}
        ref_t += max(f.time, 0)
        run_t += distill_duration(f.time)
    return {"frame": None, "start_tick_ref": None, "start_tick_runtime": None}


def _frame_at_reference_tick(frames, loopstart: int | None, tick: int) -> int | None:
    """AIR element shown at a state-clock tick; None means a one-shot has ended."""
    shown = [i for i, frame in enumerate(frames) if frame.time != 0]
    if not shown or tick < 0:
        return None
    loop_frames = [i for i in shown if loopstart is not None and i >= loopstart]
    current = shown[0]
    while True:
        frame = frames[current]
        if frame.time < 0:
            return current
        if tick < frame.time:
            return current
        tick -= frame.time
        following = next((i for i in shown if i > current), None)
        if following is not None:
            current = following
        elif loop_frames:
            current = loop_frames[0]
        else:
            return None


def _csv_param(params: dict[str, str], key: str) -> list[str]:
    value = params.get(key)
    return [part.strip() for part in value.split(",")] if value else []


def hitdef_events(raw_state, action, state_no: int, anim_id: int) -> list[dict]:
    """Map literal Time/AnimElem HitDef triggers to source AIR elements.

    The report retains all other conditions verbatim. A mapped timing is not
    called exact when triggerall or the trigger group has extra expressions.
    """
    events: list[dict] = []
    frames = action.frames if action is not None else []
    loopstart = action.loopstart if action is not None else None
    for controller_index, controller in enumerate(raw_state.controllers):
        if controller.type != "hitdef":
            continue
        groups = controller.triggers or {0: []}
        common = list(controller.triggerall)
        for group_id, expressions in sorted(groups.items()):
            expressions = list(expressions)
            timing_terms = []
            other_terms = []
            for expression in expressions:
                match = ANIMELEM_EQ.match(expression)
                if match:
                    timing_terms.append(("animelem", int(match.group(1))))
                    continue
                match = TIME_EQ.match(expression)
                if match:
                    timing_terms.append(("time", int(match.group(1))))
                    continue
                other_terms.append(expression)

            if not timing_terms:
                events.append({
                    "state": state_no, "anim": anim_id, "controller": controller_index,
                    "line": controller.line, "trigger_group": group_id,
                    "trigger_kind": "unmapped", "trigger_value": None,
                    "air_frame": None, "air_start_tick": None,
                    "timing_mapped": False, "conditions_exact": False,
                    "conditions": common + expressions,
                    "damage": _csv_param(controller.params, "damage"),
                })
                continue

            for kind, value in timing_terms:
                if kind == "animelem":
                    frame_index = value - 1
                    frame_index = frame_index if 0 <= frame_index < len(frames) else None
                    start_tick = (sum(max(frame.time, 0) for frame in frames[:frame_index])
                                  if frame_index is not None else None)
                else:
                    start_tick = value
                    frame_index = _frame_at_reference_tick(frames, loopstart, value)

                mapped = frame_index is not None
                air_frame = None
                if mapped:
                    frame = frames[frame_index]
                    air_frame = {
                        "index": frame_index,
                        "time": frame.time,
                        "clsn1": bool(frame.clsn1),
                    }
                events.append({
                    "state": state_no, "anim": anim_id, "controller": controller_index,
                    "line": controller.line, "trigger_group": group_id,
                    "trigger_kind": kind, "trigger_value": value,
                    "air_frame": air_frame, "air_start_tick": start_tick,
                    "timing_mapped": mapped,
                    "conditions_exact": mapped and not common and not other_terms
                    and len(timing_terms) == 1,
                    "conditions": common + expressions,
                    "damage": _csv_param(controller.params, "damage"),
                    "attr": controller.params.get("attr"),
                    "guardflag": controller.params.get("guardflag"),
                    "pausetime": _csv_param(controller.params, "pausetime"),
                    "ground_type": controller.params.get("ground.type"),
                    "ground_velocity": _csv_param(controller.params, "ground.velocity"),
                    "air_type": controller.params.get("air.type"),
                    "air_velocity": _csv_param(controller.params, "air.velocity"),
                })
    return events


def action_report(action, horizon: int | None = None, stall: int = 0) -> dict:
    fr = action.frames
    total = sum(max(f.time, 0) for f in fr)
    horizon = horizon or max(2 * total, 8)
    loop = action.loopstart
    ref = reference_timeline(fr, loop, horizon)
    run = runtime_timeline(fr, loop, horizon, stall=stall)
    first_div = next((t for t, (a, b) in enumerate(zip(ref, run)) if a != b), None)
    flags = []
    if any(f.time == 0 for f in fr):
        flags.append("time0_vira_1_tick")
    if any(f.time > 254 for f in fr):
        flags.append("time_truncado_254")
    if any(f.time < 0 for f in fr[:-1]):
        flags.append("forever_no_meio_corta_quadros_seguintes")
    return {"action": action.number, "frames": len(fr), "air_ticks": total, "horizon": horizon,
            "first_divergent_tick": first_div, "flags": flags, "hit": hit_window(fr)}


def build(ch, stall: int = 0) -> list[dict]:
    rows = []
    state_by_anim: dict[int, list[tuple[int, object]]] = {}
    for n, sd in ch.raw_states.items():
        a = sd.params.get("anim", "").strip()
        if not a.lstrip("-").isdigit():
            a = next((c.params.get("value", "").strip() for c in sd.controllers
                      if c.type == "changeanim" and c.params.get("value", "").strip().lstrip("-").isdigit()), "")
        if a.lstrip("-").isdigit():
            state_by_anim.setdefault(int(a), []).append((n, sd))
    for aid in sorted(ch.anims):
        r = action_report(ch.anims[aid], stall=stall)
        mapped_states = state_by_anim.get(aid, [])
        events = [event for state_no, raw_state in mapped_states
                  for event in hitdef_events(raw_state, ch.anims[aid], state_no, aid)]
        events.sort(key=lambda event: (
            event["air_frame"]["index"] if event["air_frame"] else 255,
            event["state"], event["line"], event["trigger_group"],
        ))
        r["hitdef_states"] = [state_no for state_no, _raw in mapped_states
                               if any(c.type == "hitdef" for c in _raw.controllers)]
        r["hitdef_events"] = events
        r["hitdef_profile_status"] = (
            "no_hitdef" if not events else
            "mapped" if all(event["timing_mapped"] for event in events) else "unmapped"
        )
        if any(not event["timing_mapped"] for event in events):
            r["flags"].append("hitdef_trigger_not_mapped_to_air")
        if any(event["air_frame"] and not event["air_frame"]["clsn1"] for event in events):
            r["flags"].append("hitdef_trigger_frame_has_no_clsn1")
        rows.append(r)
    return rows


def to_markdown(name: str, rows: list[dict], stall: int) -> str:
    bad = [r for r in rows if r["flags"] or r["first_divergent_tick"] is not None]
    out = [f"# Contrato temporal AIR->SMS - {name}", "",
           f"Acoes: {len(rows)} | com divergencia estatica: {len(bad)} | stall assumido: {stall} tick(s)/quadro", "",
           "Modelo = leitura de fight.c/scene_cut.py, nao medicao de emulador.", "",
           "| Acao | Quadros | Ticks AIR | 1o tick divergente | Janela hit ref/runtime | HitDef por AIR | Flags |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        h = r["hit"]
        win = "-" if h["frame"] is None else f"{h['start_tick_ref']}/{h['start_tick_runtime']}"
        hitdefs = ", ".join(
            f"S{event['state']}:{event['trigger_kind']}={event['trigger_value']}"
            f"→f{event['air_frame']['index'] if event['air_frame'] else '?'}"
            f"@{event['air_start_tick'] if event['air_start_tick'] is not None else '?'}"
            f" dmg={','.join(event['damage']) or '?'}"
            for event in r["hitdef_events"]
        ) or "-"
        out.append(f"| {r['action']} | {r['frames']} | {r['air_ticks']} | {r['first_divergent_tick']} | {win} | "
                   f"{hitdefs} | {', '.join(r['flags']) or '-'} |")
    return "\n".join(out) + "\n"


def self_check() -> int:
    from types import SimpleNamespace
    from ..parsers import air
    text = ("[Begin Action 1]\n0,0,0,0,3\n0,1,0,0,0\n0,2,0,0,2\n"           # time 0 no meio
            "[Begin Action 2]\n0,0,0,0,300\n"                                 # time > 254
            "[Begin Action 3]\n0,0,0,0,2\nLoopStart\n0,1,0,0,2\n0,2,0,0,2\n"  # laco
            "[Begin Action 4]\n0,0,0,0,2\n0,1,0,0,-1\n")                      # forever final
    acts = air.parse(text).actions
    rep = {n: action_report(a, horizon=12) for n, a in acts.items()}
    ref3 = reference_timeline(acts[3].frames, acts[3].loopstart, 12)
    ok = (
        "time0_vira_1_tick" in rep[1]["flags"] and rep[1]["first_divergent_tick"] == 3
        and "time_truncado_254" in rep[2]["flags"]
        and ref3 == [0, 0, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1]
        and rep[3]["first_divergent_tick"] is None and not rep[3]["flags"]
        and rep[4]["first_divergent_tick"] is None
        # stall desloca o runtime: a divergencia deixa de ser silenciosa
        and action_report(acts[3], horizon=12, stall=1)["first_divergent_tick"] == 2
    )
    profile_action = SimpleNamespace(
        frames=[SimpleNamespace(time=4, clsn1=False),
                SimpleNamespace(time=8, clsn1=True),
                SimpleNamespace(time=6, clsn1=False),
                SimpleNamespace(time=12, clsn1=True)],
        loopstart=None,
    )
    state = SimpleNamespace(controllers=[
        SimpleNamespace(type="hitdef", triggerall=[], triggers={1: ["AnimElem = 2"]},
                        params={"damage": "20", "attr": "S, NA"}, line=10),
        SimpleNamespace(type="hitdef", triggerall=[], triggers={1: ["AnimElem = 4"]},
                        params={"damage": "42", "guardflag": "MA"}, line=20),
        SimpleNamespace(type="hitdef", triggerall=[], triggers={1: ["AnimElem = 5"]},
                        params={"damage": "99"}, line=30),
    ])
    profile = hitdef_events(state, profile_action, 220, 220)
    ok = ok and (
        len(profile) == 3
        and profile[0]["air_frame"]["index"] == 1
        and profile[0]["air_start_tick"] == 4
        and profile[0]["damage"] == ["20"]
        and profile[0]["air_frame"]["clsn1"]
        and profile[1]["air_frame"]["index"] == 3
        and profile[1]["air_start_tick"] == 18
        and profile[1]["damage"] == ["42"]
        and not profile[2]["timing_mapped"]
    )
    print("self-check anim_time_contract:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None) -> int:
    from .. import character
    from ..source import Source
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("package", type=Path, nargs="?")
    ap.add_argument("--stall", type=int, default=0, help="ticks extras por quadro (latencia de apresentacao)")
    ap.add_argument("--out-md", type=Path)
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    if not a.package:
        ap.error("package obrigatorio sem --self-check")
    ch = character.load(Source(a.package))
    rows = build(ch, a.stall)
    md = to_markdown(ch.name, rows, a.stall)
    if a.out_md:
        a.out_md.write_text(md, encoding="utf-8")
    if a.out_json:
        a.out_json.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(md if not a.out_md else md.splitlines()[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
