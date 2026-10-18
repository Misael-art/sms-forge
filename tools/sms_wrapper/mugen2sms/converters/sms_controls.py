"""Mapa de controle MUGEN (6 botoes) -> pad SMS (2 botoes) por TEMPO DE PRESSAO (doc/22).

Ideia (decisao de design proposta pelo usuario, 2026-09-30): como varios lutas de MS/NES, cada botao fisico
alimenta uma FAMILIA de golpes e o tempo segurando escolhe a forca — toque rapido = fraco, segurar um pouco mais
= forte. Os golpes MUGEN sao derivados desta logica: a=soco fraco, c=soco forte, x=chute fraco, z=chute forte
(b/y, os medios, ficam sem tier por padrao e sao reportados como inalcancaveis, nao escondidos).

Fatos de hardware (headers, autoridade #8): SMSlib.h:296-302 — o pad tem UP/DOWN/LEFT/RIGHT, KEY_1 e KEY_2
(START e alias de KEY_1). Diagonais sao duas direcoes juntas (o runtime ja usa Down+Back para guarda);
so direcoes OPOSTAS sao fisicamente impossiveis. O blob CMD v3/v4 representa tiers por tempo de pressao
e `$` como mascara de direcao cardinal com diagonais vizinhas; v4 registra `~N` em uma soltura cardinal.

Decisao do usuario (2026-09-30): sem golpes medios => 2 tiers por tecla. Limiar padrao T=6 ticks (100 ms a 60 Hz):
o menor que ainda deixa um toque deliberado (~3-5 quadros) cair no tier fraco; e PARAMETRO de jogabilidade, a validar
com jogador e emulador.

Custo temporal: decidir o tier exige esperar. Politica `release_or_threshold`; T conta ticks de pressao a partir do
tick do toque, inclusive. Tecla segurada por >= T ticks => tier forte, emitido no tick T-1 apos o toque, SEM esperar a
soltura. Solta antes => tier fraco, emitido no 1o tick com a tecla solta (latencia = duracao do toque k <= T-1).
Pior caso adicionado, em ticks apos o toque: T-1 nos dois tiers; o fraco tipico e a duracao do toque. Isto SOMA ao
atraso de entrada ja medido (26 quadros ate a pose) — custo de design, a medir em emulador.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

DIRS_CARDINAL = {"U", "D", "B", "F"}
DIRS_DIAGONAL = {"DF", "DB", "UF", "UB"}
OPPOSED = (("U", "D"), ("F", "B"))
TICK_HZ = {"NTSC": 60, "PAL": 50}
RUNTIME_TIER_MAX = 2  # input_tier.c emite fraco/forte


@dataclass
class ControlMap:
    # tecla fisica -> botoes MUGEN por tier (tier 0 = toque, ultimo = mais forte)
    families: dict[str, list[str]] = field(default_factory=lambda: {"1": ["a", "c"], "2": ["x", "z"]})
    # limiares em ticks entre tiers consecutivos (len = tiers-1); por tecla
    thresholds: dict[str, list[int]] = field(default_factory=lambda: {"1": [6], "2": [6]})
    policy: str = "release_or_threshold"
    # botoes MUGEN descartados POR DECISAO (nao por falha): comandos que so dependem deles viram DROPPED
    dropped: tuple[str, ...] = ("b", "y")

    def validate(self) -> list[str]:
        errs = []
        seen: dict[str, str] = {}
        for phys, btns in self.families.items():
            if phys not in ("1", "2"):
                errs.append(f"tecla fisica '{phys}' inexistente (so 1 e 2)")
            if len(self.thresholds.get(phys, [])) != len(btns) - 1:
                errs.append(f"tecla {phys}: {len(btns)} tiers exigem {len(btns) - 1} limiares")
            if sorted(self.thresholds.get(phys, [])) != list(self.thresholds.get(phys, [])) or \
                    any(t < 2 for t in self.thresholds.get(phys, [])):
                errs.append(f"tecla {phys}: limiares devem ser crescentes e >= 2 ticks")
            for b in btns:
                if b in seen:
                    errs.append(f"botao '{b}' repetido em {seen[b]} e {phys}")
                seen[b] = phys
        return errs

    def locate(self, button: str) -> tuple[str, int] | None:
        for phys, btns in self.families.items():
            if button in btns:
                return phys, btns.index(button)
        return None

    def added_latency(self, phys: str, tier: int) -> int:
        th = self.thresholds.get(phys, [])
        return (th[0] if tier == 0 else th[tier - 1]) - 1

    def unreachable(self, all_buttons=("a", "b", "c", "x", "y", "z")) -> list[str]:
        return [b for b in all_buttons if self.locate(b) is None]

    @classmethod
    def from_dict(cls, d: dict) -> "ControlMap":
        return cls(d["families"], d["thresholds"], d.get("policy", "release_or_threshold"),
                   tuple(d.get("dropped", ("b", "y"))))

    @classmethod
    def from_json(cls, text: str) -> "ControlMap":
        return cls.from_dict(json.loads(text))

    def to_json(self) -> str:
        return json.dumps({"families": self.families, "thresholds": self.thresholds, "policy": self.policy,
                           "dropped": list(self.dropped)},
                          indent=2)


DEFAULT_MAP = ControlMap()


def classify_trace(trace, threshold: int) -> list[tuple[int, int, int]]:
    """Referencia da politica `release_or_threshold` para 2 tiers. trace[t] = bitmask das teclas fisicas
    (bit0 = KEY_1, bit1 = KEY_2) no tick t. Retorna [(tick_do_evento, tecla 0/1, tier 0/1)], ordenado por tick."""
    events = []
    for key in (0, 1):
        count, fired = 0, False
        for t, bits in enumerate(list(trace) + [0]):
            if (bits >> key) & 1:
                count = min(count + 1, 255)
                if count == threshold and not fired:
                    events.append((t, key, 1))
                    fired = True
            else:
                if count and not fired:
                    events.append((t, key, 0))
                count, fired = 0, False
    return sorted(events)


def step_reasons(step, cmap: ControlMap) -> tuple[list[str], int]:
    """(motivos de inviabilidade, latencia adicionada em ticks) de UM passo do comando."""
    why: list[str] = []
    added = 0
    if step.strict:
        why.append("strict-step-nao-suportado-no-runtime")
    timed = [k for k in step.keys if k.release_time]
    if timed:
        if any(k.release_time > 0xFF for k in timed):
            why.append("release-time-acima-de-255")
        elif (len(step.keys) != 1 or len(timed) != 1 or
              timed[0].key not in DIRS_CARDINAL or not timed[0].release or
              timed[0].hold):
            why.append("release-time-exige-uma-direcao-cardinal")
    dirs = {k.key for k in step.keys if k.key in DIRS_CARDINAL | DIRS_DIAGONAL}
    parts: set[str] = set()
    for d in dirs:
        parts |= {d} if d in DIRS_CARDINAL else {d[0], d[1]}
    for a, b in OPPOSED:
        if a in parts and b in parts:
            why.append(f"direcoes_opostas:{a}+{b}")
    used: dict[str, str] = {}
    for k in step.keys:
        if k.key in DIRS_CARDINAL or k.key in DIRS_DIAGONAL:
            continue
        if k.key == "s":
            why.append("start_reservado")
            continue
        loc = cmap.locate(k.key)
        if loc is None:
            why.append(f"botao_sem_tier:{k.key}")
            continue
        phys, tier = loc
        if tier + 1 > RUNTIME_TIER_MAX:
            why.append("tier-acima-da-maquina-runtime")
        if phys in used:
            why.append(f"acorde_na_mesma_tecla:{used[phys]}+{k.key}")
        used[phys] = k.key
        if not k.release:
            added = max(added, cmap.added_latency(phys, tier))
    return why, added


def command_support(cmd, cmap: ControlMap) -> dict:
    """Viabilidade de um Command no pad com este mapa. `ok` = digitavel; `added_latency_ticks` = pior caso."""
    reasons: list[str] = []
    added = 0
    for st in cmd.steps:
        w, a = step_reasons(st, cmap)
        reasons += w
        added = max(added, a)
    timed_steps = [index for index, step in enumerate(cmd.steps)
                   if any(key.release_time for key in step.keys)]
    if len(timed_steps) > 1:
        reasons.append("multiplos-release-times-nao-suportados")
    elif timed_steps and timed_steps[0] != 0:
        reasons.append("release-time-deve-ser-primeiro-passo")
    if cmd.errors:
        reasons.append("cmd_com_erro_de_parse")
    return {"ok": not reasons, "reasons": sorted(set(reasons)), "added_latency_ticks": added}


def self_check() -> int:
    from ..parsers import cmd as cm

    def command(name, text):
        steps, errs = cm.parse_command_string(text)
        return cm.Command(name, steps, 15, 1, 1, text, errs)

    m = ControlMap()
    cases = {
        "qcf_c": command("qcf_c", "~D, DF, F, c"),      # hadouken forte: viavel, latencia do tier forte
        "lp": command("lp", "a"),
        "mp": command("mp", "b"),                        # medio: sem tier
        "chord": command("chord", "a+c"),                # dois tiers da mesma tecla
        "opp": command("opp", "F+B"),
        "cross": command("cross", "a+x"),                # soco+chute = KEY_1+KEY_2
        "tau": command("tau", "s"),
        "timed_release": command("timed_release", "~15D, U, x"),
        "timed_not_first": command("timed_not_first", "D, ~15U"),
        "two_timed": command("two_timed", "~3D, ~4U"),
        "strict": command("strict", ">D, DF, F, x"),
    }
    r = {k: command_support(v, m) for k, v in cases.items()}
    ok = (
        m.validate() == []
        and r["qcf_c"]["ok"] and r["qcf_c"]["added_latency_ticks"] == 5
        and r["lp"]["ok"] and r["lp"]["added_latency_ticks"] == 5
        and r["mp"]["reasons"] == ["botao_sem_tier:b"]
        and r["chord"]["reasons"] == ["acorde_na_mesma_tecla:a+c"]
        and r["opp"]["reasons"] == ["direcoes_opostas:F+B"]
        and r["cross"]["ok"]
        and r["tau"]["reasons"] == ["start_reservado"]
        and r["timed_release"]["ok"]
        and r["timed_not_first"]["reasons"] == ["release-time-deve-ser-primeiro-passo"]
        and r["two_timed"]["reasons"] == ["multiplos-release-times-nao-suportados"]
        and r["strict"]["reasons"] == ["strict-step-nao-suportado-no-runtime"]
        and m.unreachable() == ["b", "y"]
        and classify_trace([1, 1, 0, 0], 6) == [(2, 0, 0)]                       # toque de 2 ticks: fraco na soltura
        and classify_trace([1] * 10, 6) == [(5, 0, 1)]                           # segurou: forte no tick T-1
        and classify_trace([1, 1, 1, 1, 1, 0], 6) == [(5, 0, 0)]                 # T-1 ticks: ainda fraco
        and classify_trace([3, 3, 3, 3, 3, 3, 0], 6) == [(5, 0, 1), (5, 1, 1)]   # duas teclas independentes
        and ControlMap({"1": ["a", "b", "c"]}, {"1": [6, 14]}).validate() == []
        and ControlMap({"1": ["a", "b"]}, {"1": []}).validate() != []        # limiar ausente
        and ControlMap({"1": ["a", "a"]}, {"1": [8]}).validate() != []       # botao repetido
    )
    print("self-check sms_controls:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(self_check())
