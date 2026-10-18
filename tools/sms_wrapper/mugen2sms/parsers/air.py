"""Parser de .air (animacoes, tempos, offsets, flips, blend e caixas Clsn1/Clsn2)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .ini import strip_comment

Box = tuple[int, int, int, int]  # x1, y1, x2, y2 relativos ao eixo, normalizados (x1<=x2, y1<=y2)

_ACTION = re.compile(r"^\[\s*begin\s+action\s+(-?\d+)\s*\]", re.I)
_CLSN_HDR = re.compile(r"^clsn([12])(default)?\s*:\s*(\d+)", re.I)
_CLSN_BOX = re.compile(r"^clsn([12])\s*\[\s*\d+\s*\]\s*=\s*(.+)$", re.I)


@dataclass
class Frame:
    group: int
    image: int
    x: int
    y: int
    time: int                   # -1 = infinito
    hflip: bool = False
    vflip: bool = False
    blend: str = ""             # A, A1, S, AS..D.. -> sem equivalente direto no VDP
    clsn1: list[Box] = field(default_factory=list)  # ataque (hitbox)
    clsn2: list[Box] = field(default_factory=list)  # corpo (hurtbox)
    line: int = 0


@dataclass
class Action:
    number: int
    frames: list[Frame] = field(default_factory=list)
    loopstart: int = 0
    line: int = 0


@dataclass
class AirParseResult:
    actions: dict[int, Action]
    warnings: list[str]


def _box(txt: str) -> Box:
    x1, y1, x2, y2 = (int(float(t)) for t in txt.split(",")[:4])
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def parse(text: str, source: str = "<air>") -> AirParseResult:
    actions: dict[int, Action] = {}
    warnings: list[str] = []
    cur: Action | None = None
    default = {"1": [], "2": []}
    pending = {"1": None, "2": None}   # caixas do proximo frame (None = usa default)
    reading: str | None = None
    reading_default = False

    for ln, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw)
        if not line:
            continue
        m = _ACTION.match(line)
        if m:
            n = int(m.group(1))
            if n in actions:
                warnings.append(f"{source}:{ln}: action {n} duplicada; mantida a primeira")
                cur = Action(n, line=ln)  # descartavel
            else:
                cur = actions.setdefault(n, Action(n, line=ln))
            default = {"1": [], "2": []}
            pending = {"1": None, "2": None}
            continue
        if cur is None:
            continue
        if line.lower().startswith("loopstart"):
            cur.loopstart = len(cur.frames)
            continue
        m = _CLSN_HDR.match(line)
        if m:
            reading, reading_default = m.group(1), bool(m.group(2))
            if reading_default:
                default[reading] = []
            else:
                pending[reading] = []
            continue
        m = _CLSN_BOX.match(line)
        if m:
            try:
                box = _box(m.group(2))
            except ValueError:
                warnings.append(f"{source}:{ln}: caixa invalida '{line}'")
                continue
            kind = m.group(1)
            if reading_default and reading == kind:
                default[kind].append(box)
            else:
                if pending[kind] is None:
                    pending[kind] = []
                pending[kind].append(box)
            continue
        if line[0].isdigit() or line[0] == "-":
            parts = [p.strip() for p in line.split(",")]
            try:
                g, i, x, y, t = (int(p) for p in parts[:5])
            except ValueError:
                warnings.append(f"{source}:{ln}: frame invalido '{line}'")
                continue
            flip = parts[5].upper() if len(parts) > 5 else ""
            blend = parts[6].upper() if len(parts) > 6 else ""
            fr = Frame(g, i, x, y, t, "H" in flip, "V" in flip, blend,
                       list(pending["1"] if pending["1"] is not None else default["1"]),
                       list(pending["2"] if pending["2"] is not None else default["2"]), ln)
            cur.frames.append(fr)
            pending = {"1": None, "2": None}
            reading = None
            continue
        warnings.append(f"{source}:{ln}: linha ignorada '{line[:40]}'")
    for a in actions.values():
        if not a.frames:
            warnings.append(f"{source}:{a.line}: action {a.number} sem frames")
    return AirParseResult(actions, warnings)
