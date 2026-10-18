"""Parser de .cmd: [Command] (sequencias de entrada) e [Remap]/[Defaults].

Os blocos [State -1] do .cmd sao controladores de estado e sao lidos por cns.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ini import Section, unquote

DIRS = {"F", "B", "U", "D", "DF", "DB", "UF", "UB"}
BUTTONS = {"a", "b", "c", "x", "y", "z", "s"}
_TOKEN = re.compile(r"^(?P<mods>[~/$>]*)(?P<rel>\d*)(?P<mods2>[/$]*)(?P<key>[A-Za-z]+)$")


@dataclass
class Key:
    key: str                 # F/B/U/D/DF.. ou a/b/c/x/y/z/s
    release: bool = False    # ~  (soltar)
    release_time: int = 0    # ~30 (segurar N ticks antes de soltar = carga)
    hold: bool = False       # /  (manter pressionado)
    four_way: bool = False   # $  (direcao aceita diagonais vizinhas)


@dataclass
class Step:
    keys: list[Key]          # varias = simultaneas (+)
    strict: bool = False     # >  (nenhuma outra entrada entre este e o anterior)


@dataclass
class Command:
    name: str
    steps: list[Step]
    time: int
    buffer_time: int
    line: int
    raw: str
    errors: list[str] = field(default_factory=list)


def _parse_key(tok: str) -> tuple[Key | None, bool, str | None]:
    tok = tok.strip()
    m = _TOKEN.match(tok)
    if not m:
        return None, False, f"token invalido '{tok}'"
    mods = m.group("mods") + m.group("mods2")
    key = m.group("key")
    # MUGEN diferencia caixa: direcoes em maiuscula (B = tras), botoes em minuscula (b = botao B)
    norm = key if key in DIRS else key.lower()
    if norm not in DIRS and norm not in BUTTONS:
        return None, False, f"tecla desconhecida '{key}'"
    k = Key(norm, "~" in mods, int(m.group("rel") or 0), "/" in mods, "$" in mods)
    return k, ">" in mods, None


def parse_command_string(s: str) -> tuple[list[Step], list[str]]:
    steps, errors = [], []
    for part in s.split(","):
        keys, strict = [], False
        for sub in part.split("+"):
            k, st, err = _parse_key(sub)
            if err:
                errors.append(err)
                continue
            strict = strict or st
            keys.append(k)
        if keys:
            steps.append(Step(keys, strict))
    return steps, errors


def parse(sections: list[Section], source: str = "<cmd>") -> tuple[list[Command], dict, list[str]]:
    commands, warnings = [], []
    defaults = {"command.time": 15, "command.buffer.time": 1}
    for sec in sections:
        low = sec.name.lower()
        if low == "defaults":
            for k in defaults:
                v = sec.get(k)
                if v and v.strip().isdigit():
                    defaults[k] = int(v)
        elif low == "command":
            name = unquote(sec.get("name"))
            raw = sec.get("command")
            if not name or raw is None:
                warnings.append(f"{source}:{sec.line}: [Command] sem name/command")
                continue
            steps, errors = parse_command_string(raw)
            t = sec.get("time")
            bt = sec.get("buffer.time")
            cmd = Command(name, steps,
                          int(t) if t and t.strip().isdigit() else defaults["command.time"],
                          int(bt) if bt and bt.strip().isdigit() else defaults["command.buffer.time"],
                          sec.line, raw, [f"{source}:{sec.line}: {e}" for e in errors])
            warnings.extend(cmd.errors)
            commands.append(cmd)
    return commands, defaults, warnings
