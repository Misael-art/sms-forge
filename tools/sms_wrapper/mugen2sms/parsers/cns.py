"""Parser de .cns/.st/.cmd: [Data]/[Size]/[Velocity]/[Movement], [Statedef N] e controladores [State N, ...].

Expressoes ficam como texto cru. A traducao para C e feita por converters/states.py,
que classifica o que e traduzivel e o que exige reimplementacao manual.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ini import Section

_STATEDEF = re.compile(r"^statedef\s+(-?\d+)", re.I)
_STATE = re.compile(r"^state\s+(-?\d+)\s*(?:,\s*(.*))?$", re.I)
_TRIG = re.compile(r"^trigger(all|\d+)$")


@dataclass
class Controller:
    type: str                                   # minusculo
    label: str
    triggerall: list[str] = field(default_factory=list)
    triggers: dict[int, list[str]] = field(default_factory=dict)  # grupo -> condicoes (AND)
    params: dict[str, str] = field(default_factory=dict)
    line: int = 0


@dataclass
class StateDef:
    number: int
    params: dict[str, str] = field(default_factory=dict)
    controllers: list[Controller] = field(default_factory=list)
    source: str = ""
    line: int = 0


@dataclass
class CnsResult:
    constants: dict[str, dict[str, str]]        # secao -> chave -> valor
    states: dict[int, StateDef]
    warnings: list[str]


_SKIP = object()
CONST_SECTIONS = {"data", "size", "velocity", "movement", "quotes"}


def parse(sections: list[Section], source: str, into: CnsResult | None = None) -> CnsResult:
    res = into or CnsResult({}, {}, [])
    current = None                         # MUGEN: controlador pertence ao ultimo Statedef do arquivo
    for sec in sections:
        low = sec.name.lower()
        if low in CONST_SECTIONS:
            d = res.constants.setdefault(low, {})
            for k, v, _ in sec.items:
                if k:
                    d.setdefault(k, v)
            continue
        m = _STATEDEF.match(sec.name)
        if m:
            n = int(m.group(1))
            current = n
            if n in res.states and res.states[n].params:
                res.warnings.append(f"{source}:{sec.line}: Statedef {n} duplicado; mantido o primeiro "
                                    f"({res.states[n].source}:{res.states[n].line})")
                current = _SKIP              # controladores do duplicado tambem sao descartados
                continue
            sd = res.states.setdefault(n, StateDef(n))
            sd.params = {k: v for k, v, _ in sec.items if k}
            sd.source, sd.line = source, sec.line
            continue
        m = _STATE.match(sec.name)
        if m:
            # o numero do rotulo [State N, ...] e ignorado pelo MUGEN quando ha Statedef antes
            if current is _SKIP:
                continue
            n = current if current is not None else int(m.group(1))
            ctrl = Controller("", (m.group(2) or "").strip(), line=sec.line)
            for k, v, ln in sec.items:
                if not k:
                    continue
                t = _TRIG.match(k)
                if t:
                    if t.group(1) == "all":
                        ctrl.triggerall.append(v)
                    else:
                        ctrl.triggers.setdefault(int(t.group(1)), []).append(v)
                elif k == "type":
                    ctrl.type = v.strip().lower()
                else:
                    ctrl.params.setdefault(k, v)
            if not ctrl.type:
                res.warnings.append(f"{source}:{sec.line}: controlador sem type")
                continue
            if not ctrl.triggers and ctrl.type != "null":
                res.warnings.append(f"{source}:{sec.line}: controlador {ctrl.type} sem trigger1 (nunca executa)")
            sd = res.states.get(n)
            if sd is None:
                # State -1/-2/-3 (cmd) ou controlador antes do statedef
                sd = res.states.setdefault(n, StateDef(n, source=source, line=sec.line))
            sd.controllers.append(ctrl)
    return res
