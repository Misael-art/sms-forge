"""Matriz de golpes: comando -> estado de entrada -> estados alcancaveis -> fidelidade + suporte ao pad SMS.

Tecnica assimilada de `move_checklist.py` do forge MD (doc/21, item 1), com o eixo que so o SMS tem: o
comando precisa ser digitavel no pad SMS com o mapa de controle por tempo de pressao (converters/sms_controls.py,
doc/22): 2 botoes fisicos, cada um com tiers fraco/forte, diagonais = duas direcoes.

Nao executa runtime: mede o que o CONVERSOR consegue representar. `OK` aqui nao e emulador
(documentado != implementado != buildado != testado_em_emulador != validado_budget).
Um estado alvo sem [Statedef] aparece como BLOCKED ("estado inexistente"), nunca some em silencio.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .. import character
from ..converters import sms_controls
from ..source import Source

STATE_ENTRY = ("changestate", "selfstate")
COSMETIC = {"screenbound", "playerpush", "forcefeedback", "afterimage", "afterimagetime", "palfx", "envcolor",
            "assertspecial", "trans", "envshake", "fallenvshake"}
CMD_RE = re.compile(r'command\s*=\s*"([^"]+)"', re.I)
POWER_RE = re.compile(r"\bpower\s*>=?\s*(\d+)", re.I)
INT_RE = re.compile(r"^-?\d+$")
FIRST_MOVE_STATE = 200


def _lit(text: str | None) -> int | None:
    t = (text or "").strip()
    return int(t) if INT_RE.match(t) else None


def _reach(ch, start: int) -> tuple[list[int], list[int]]:
    """(estados alcancaveis com definicao, alvos literais sem definicao)."""
    seen, missing, todo = [], [], [start]
    while todo:
        n = todo.pop()
        if n in seen or n in missing:
            continue
        if n not in ch.raw_states:
            missing.append(n)
            continue
        seen.append(n)
        if n in ch.states and ch.states[n].origin != "personagem" and n != start:
            continue
        for c in ch.raw_states[n].controllers:
            if c.type in STATE_ENTRY:
                t = _lit(c.params.get("value"))
                if t is not None and FIRST_MOVE_STATE <= t < 5000:
                    todo.append(t)
    return seen, missing


def _state_summary(ch, n: int) -> dict:
    raw, st = ch.raw_states[n], ch.states[n]
    anim = _lit(raw.params.get("anim"))
    for c in raw.controllers:
        if anim is None and c.type == "changeanim":
            anim = _lit(c.params.get("value"))
    act = ch.anims.get(anim) if anim is not None else None
    counts = {"hitdef": 0, "projectile": 0, "helper": 0, "explod": 0}
    bad, soft = [], []
    for rc, cc in zip(raw.controllers, st.controllers):
        if rc.type in counts:
            counts[rc.type] += 1
        if cc.fidelity == "unsupported":
            (soft if rc.type in COSMETIC else bad).append(f"{rc.type}@{rc.line}")
        elif cc.fidelity == "approximate":
            soft.append(f"{rc.type}~@{rc.line}")
    return {"state": n, "movetype": raw.params.get("movetype", "").strip(), "anim": anim,
            "anim_ticks": sum(f.time for f in act.frames if f.time > 0) if act else None,
            "anim_missing": anim is not None and act is None, **counts,
            "blocking": bad, "degrading": soft}


def pad_support(ch, cmap) -> dict[str, dict]:
    """{nome_do_comando: {ok, reasons, added_latency_ticks}}. Fonte unica: converters.sms_controls."""
    return {c.name: sms_controls.command_support(c, cmap) for c in ch.commands}


def build(ch, cmap=None) -> list[dict]:
    cmap = cmap or sms_controls.DEFAULT_MAP
    if -1 not in ch.raw_states:
        return []
    cmds = {c.name: c for c in ch.commands}
    pad = pad_support(ch, cmap)
    rows = []
    for rc, cc in zip(ch.raw_states[-1].controllers, ch.states[-1].controllers):
        if rc.type not in STATE_ENTRY:
            continue
        target = _lit(rc.params.get("value"))
        if target is None or target < FIRST_MOVE_STATE:
            continue
        text = list(rc.triggerall) + [t for g in rc.triggers.values() for t in g]
        names = sorted({m for t in text for m in CMD_RE.findall(t)})
        if not names:
            continue
        power = max([int(m) for t in text for m in POWER_RE.findall(t)] or [0])
        reach, absent = _reach(ch, target)
        summaries = [_state_summary(ch, n) for n in reach if n in ch.states]
        blocking = [f"{s['state']}:{b}" for s in summaries for b in s["blocking"]]
        soft = [f"{s['state']}:{b}" for s in summaries for b in s["degrading"]]
        blocking += [f"estado inexistente:{n}" for n in absent]
        if cc.fidelity == "unsupported":
            blocking.insert(0, f"entrada:{rc.type}@{rc.line}")
        if any(s["anim_missing"] for s in summaries):
            blocking.append("anim ausente")
        attack = any(s["movetype"].upper() == "A" for s in summaries)
        if attack and not any(s["hitdef"] or s["projectile"] or s["helper"] for s in summaries):
            blocking.append("golpe sem hitdef/projetil/helper alcancavel")
        missing_cmd = [n for n in names if n not in pad]
        blocking += [f"comando_inexistente:{n}" for n in missing_cmd]
        for n in names:
            if n in pad and not pad[n]["ok"]:
                blocking += [f"pad:{n}={w}" for w in pad[n]["reasons"]]
        latency = max([pad[n]["added_latency_ticks"] for n in names if n in pad] or [0])
        cmd_errors = [e for n in names for e in getattr(cmds.get(n), "errors", [])]
        dropped_only = bool(blocking) and all(
            b.startswith("pad:") and b.rsplit("=", 1)[-1].startswith("botao_sem_tier:")
            and b.rsplit(":", 1)[-1] in cmap.dropped for b in blocking)
        status = ("DROPPED" if dropped_only else "BLOCKED") if blocking else "DEGRADED" if (soft or cmd_errors) else "OK"
        rows.append({"commands": names, "entry_line": rc.line, "entry_fidelity": cc.fidelity, "target": target,
                     "power_cost": power, "attack": attack, "status": status, "blocking": blocking,
                     "degrading": soft, "command_errors": cmd_errors, "pad": {n: pad.get(n) for n in names}, "added_latency_ticks": latency,
                     "hitdefs": sum(s["hitdef"] for s in summaries),
                     "projectiles": sum(s["projectile"] for s in summaries),
                     "helpers": sum(s["helper"] for s in summaries),
                     "explods": sum(s["explod"] for s in summaries),
                     "anim_ticks": sum(s["anim_ticks"] or 0 for s in summaries),
                     "states": [s["state"] for s in summaries]})
    return sorted(rows, key=lambda r: (r["target"], r["entry_line"]))


def summary(rows: list[dict]) -> dict[str, int]:
    return {k: sum(1 for r in rows if r["status"] == k) for k in ("OK", "DEGRADED", "DROPPED", "BLOCKED")}


def to_markdown(name: str, rows: list[dict], cmap=None) -> str:
    cmap = cmap or sms_controls.DEFAULT_MAP
    tot = summary(rows)
    out = [f"# Matriz de golpes - {name}", "",
           f"Mapa: {cmap.families} limiares {cmap.thresholds}; inalcancaveis: {cmap.unreachable() or '-'}", "",
           f"Entradas: {len(rows)} | OK {tot['OK']} | DEGRADED {tot['DEGRADED']} | DROPPED {tot['DROPPED']} | BLOCKED {tot['BLOCKED']}", "",
           "Status = fidelidade de CONVERSAO e digitabilidade no pad SMS com o mapa por tempo de pressao; nao e teste em emulador.",
           "DROPPED = depende so de botao descartado por decisao (medios); BLOCKED = falha real.",
           "+Lat = pior caso de ticks que a classificacao tier fraco/forte soma ao atraso de entrada.", "",
           "| Comando(s) | Estado | Power | Hit | Proj | Help | Expl | Ticks | +Lat | Status | Motivo |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        why = "; ".join(r["blocking"] + r["degrading"] + r["command_errors"])[:160]
        out.append(f"| {', '.join(r['commands'])} | {r['target']} | {r['power_cost'] or ''} | {r['hitdefs']} | "
                   f"{r['projectiles']} | {r['helpers']} | {r['explods']} | {r['anim_ticks']} | {r['added_latency_ticks']} | {r['status']} | {why} |")
    return "\n".join(out) + "\n"


def self_check() -> int:
    """Fixture sintetica: golpe OK, especial QCF OK com latencia, alvo inexistente e mapa que desliga o botao."""
    import tempfile
    from ..tests.make_fixtures import build as build_fixture
    with tempfile.TemporaryDirectory() as tmp:
        ch = character.load(Source(build_fixture(Path(tmp) / "m", with_command_states=True)))
        by = {tuple(r["commands"]): r for r in build(ch)}
        nomap = {tuple(r["commands"]): r for r in build(ch, sms_controls.ControlMap({"2": ["x", "z"]}, {"2": [8]}))}
        ok = (by[("punch",)]["status"] == "OK" and by[("punch",)]["added_latency_ticks"] == 5
              and by[("special",)]["status"] == "OK"
              and by[("holdF",)]["status"] == "BLOCKED"
              and "estado inexistente:9999" in by[("holdF",)]["blocking"]
              and nomap[("punch",)]["status"] == "BLOCKED"      # `a` sem tier e nao esta em `dropped`
              and "pad:punch=botao_sem_tier:a" in nomap[("punch",)]["blocking"])
    print("self-check move_checklist:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("package", type=Path, nargs="?")
    ap.add_argument("--out-md", type=Path)
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--controls", type=Path, help="JSON do ControlMap (default: a/c soco, x/z chute, limiar 8 ticks)")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    if not a.package:
        ap.error("package obrigatorio sem --self-check")
    cmap = sms_controls.ControlMap.from_json(a.controls.read_text()) if a.controls else sms_controls.DEFAULT_MAP
    if cmap.validate():
        ap.error("mapa invalido: " + "; ".join(cmap.validate()))
    ch = character.load(Source(a.package))
    rows = build(ch, cmap)
    md = to_markdown(ch.name, rows, cmap)
    if a.out_md:
        a.out_md.write_text(md, encoding="utf-8")
    if a.out_json:
        a.out_json.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(md if not a.out_md else md.splitlines()[2])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
