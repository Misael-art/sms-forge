"""Parser de stage MUGEN (.def de palco): [StageInfo]/[Camera]/[PlayerInfo]/[Bound]/[Shadow],
camadas [BG *] (normal/parallax/anim), [BGCtrlDef]/[BGCtrl] e as [Begin Action] das camadas anim.

So le e normaliza; nao decide o que cabe no Mega Drive (isso e da medicao/reducao).
Valores ausentes recebem o padrao documentado do MUGEN 1.0; o que o parser nao entende vira
aviso com arquivo:linha, nunca silencio.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import air, ini

BG_TYPES = ("normal", "parallax", "anim")
CTRL_TYPES = ("null", "enable", "visible", "posset", "posadd", "velset", "veladd", "sinx", "siny", "anim")
_NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)")


def nums(v: str | None, n: int, default: tuple) -> tuple:
    """Ate n numeros de 'a, b'; faltantes herdam do padrao ('.25', '-.25' e lixo no fim toleram)."""
    out = list(default)
    if v is not None:
        for i, part in enumerate(v.split(",")[:n]):
            m = _NUM.search(part)
            if m:
                out[i] = float(m.group())
    return tuple(out)


def _int(v: str | None, d: int) -> int:
    m = _NUM.search(v or "")
    return int(float(m.group())) if m else d


@dataclass
class BgLayer:
    name: str
    line: int
    type: str                               # normal | parallax | anim
    spriteno: tuple[int, int] | None        # normal/parallax
    actionno: int | None                    # anim
    id: int                                 # alvo de BGCtrl (0 = sem id)
    layerno: int                            # 0 atras dos lutadores, 1 na frente
    start: tuple[float, float]
    delta: tuple[float, float]
    mask: bool
    trans: str
    tile: tuple[int, int]                   # 0 nao, 1 infinito, >1 contagem
    tilespacing: tuple[float, float]
    velocity: tuple[float, float]           # px/tick, auto-scroll
    xscale: tuple[float, float] | None      # parallax: escala no topo/base
    width: tuple[float, float] | None       # parallax: alternativa a xscale
    yscalestart: float
    yscaledelta: float
    window: tuple[float, float, float, float] | None
    windowdelta: tuple[float, float]
    sin_x: tuple[float, float, float]       # amplitude, periodo, fase
    sin_y: tuple[float, float, float]


@dataclass
class BgCtrl:
    name: str
    line: int
    type: str
    time: tuple[int, int, int]              # inicio, fim, loop (-1 = sem loop proprio)
    value: tuple[float, ...]
    x: float | None
    y: float | None
    ctrlid: tuple[int, ...] | None          # None = herda do BGCtrlDef


@dataclass
class BgCtrlDef:
    name: str
    line: int
    looptime: int                           # -1 = nao repete
    ctrlid: tuple[int, ...] | None          # None = controla todas as camadas
    ctrls: list[BgCtrl] = field(default_factory=list)


@dataclass
class Stage:
    name: str
    localcoord: tuple[int, int]
    camera: dict
    player: dict
    bound: dict
    zoffset: int
    autoturn: bool
    resetbg: bool
    shadow: dict
    spr: str
    layers: list[BgLayer]
    ctrldefs: list[BgCtrlDef]
    actions: dict[int, air.Action]
    warnings: list[str]

    def layer_by_id(self, i: int) -> list[BgLayer]:
        return [la for la in self.layers if la.id == i]


def _line(sec: ini.Section, key: str) -> int:
    """Linha da chave (para o aviso apontar o valor ruim, nao o cabecalho)."""
    hits = sec.get_all(key)
    return hits[0][1] if hits else sec.line


def _floats(sec: ini.Section | None, keys: dict[str, float]) -> dict:
    return {k: nums(sec.get(k) if sec else None, 1, (d,))[0] for k, d in keys.items()}


def _layer(sec: ini.Section, src: str, warn: list[str]) -> BgLayer:
    t = (sec.get("type") or "normal").strip().lower()
    if t not in BG_TYPES:
        warn.append(f"{src}:{_line(sec, 'type')}: [{sec.name}] type '{t}' desconhecido; tratado como normal")
        t = "normal"
    sp = sec.get("spriteno")
    spriteno = tuple(int(x) for x in nums(sp, 2, (0, 0))) if sp is not None else None
    if t != "anim" and spriteno is None:
        warn.append(f"{src}:{sec.line}: [{sec.name}] sem spriteno")
    act = sec.get("actionno")
    if t == "anim" and act is None:
        warn.append(f"{src}:{sec.line}: [{sec.name}] anim sem actionno")
    win = sec.get("window")
    xs, wd = sec.get("xscale"), sec.get("width")
    if t != "parallax" and (xs is not None or wd is not None):
        warn.append(f"{src}:{_line(sec, 'xscale' if xs is not None else 'width')}: [{sec.name}] "
                    "xscale/width so valem em parallax; ignorados")
    return BgLayer(
        name=sec.name, line=sec.line, type=t, spriteno=spriteno,
        actionno=_int(act, -1) if act is not None else None,
        id=_int(sec.get("id"), 0), layerno=_int(sec.get("layerno"), 0),
        start=nums(sec.get("start"), 2, (0.0, 0.0)), delta=nums(sec.get("delta"), 2, (1.0, 1.0)),
        mask=bool(_int(sec.get("mask"), 0)), trans=(sec.get("trans") or "none").strip().lower(),
        tile=tuple(int(x) for x in nums(sec.get("tile"), 2, (0, 0))),
        tilespacing=nums(sec.get("tilespacing"), 2, (0.0, 0.0)),
        velocity=nums(sec.get("velocity"), 2, (0.0, 0.0)),
        xscale=nums(xs, 2, (1.0, 1.0)) if t == "parallax" and xs is not None else None,
        width=nums(wd, 2, (0.0, 0.0)) if t == "parallax" and wd is not None else None,
        yscalestart=nums(sec.get("yscalestart"), 1, (100.0,))[0],
        yscaledelta=nums(sec.get("yscaledelta"), 1, (0.0,))[0],
        window=nums(win, 4, (0.0, 0.0, 0.0, 0.0)) if win is not None else None,
        windowdelta=nums(sec.get("windowdelta"), 2, (0.0, 0.0)),
        sin_x=nums(sec.get("sin.x"), 3, (0.0, 0.0, 0.0)),
        sin_y=nums(sec.get("sin.y"), 3, (0.0, 0.0, 0.0)),
    )


def _ids(v: str | None) -> tuple[int, ...] | None:
    if v is None:
        return None
    return tuple(int(float(m)) for m in _NUM.findall(v))


def _ctrl(sec: ini.Section, src: str, warn: list[str]) -> BgCtrl:
    t = (sec.get("type") or "null").strip().lower()
    if t not in CTRL_TYPES:
        warn.append(f"{src}:{_line(sec, 'type')}: [{sec.name}] BGCtrl type '{t}' desconhecido; tratado como null")
        t = "null"
    tm = nums(sec.get("time"), 3, (0.0, None, -1.0))
    start = int(tm[0])
    end = int(tm[1]) if tm[1] is not None else start
    v = sec.get("value")
    x, y = sec.get("x"), sec.get("y")
    return BgCtrl(name=sec.name, line=sec.line, type=t, time=(start, end, int(tm[2])),
                  value=tuple(float(m) for m in _NUM.findall(v)) if v is not None else (),
                  x=nums(x, 1, (0.0,))[0] if x is not None else None,
                  y=nums(y, 1, (0.0,))[0] if y is not None else None,
                  ctrlid=_ids(sec.get("ctrlid")))


def parse(text: str, source: str = "<stage.def>") -> Stage:
    warn: list[str] = []
    secs = ini.parse(text)
    by = {}
    for s in secs:
        by.setdefault(s.name.strip().lower(), s)

    layers: list[BgLayer] = []
    ctrldefs: list[BgCtrlDef] = []
    for s in secs:
        n = s.name.strip().lower()
        if n.startswith("begin action") or n in ("bgdef",):
            continue
        if n.startswith("bgctrldef"):
            ctrldefs.append(BgCtrlDef(s.name, s.line, _int(s.get("looptime"), -1), _ids(s.get("ctrlid"))))
        elif n.startswith("bgctrl"):
            if not ctrldefs:
                warn.append(f"{source}:{s.line}: [{s.name}] BGCtrl antes de qualquer BGCtrlDef; ignorado")
                continue
            ctrldefs[-1].ctrls.append(_ctrl(s, source, warn))
        elif n.startswith("bg ") or n == "bg":
            layers.append(_layer(s, source, warn))

    info, cam, pl = by.get("info"), by.get("camera"), by.get("playerinfo")
    si, bd, sh, bgd = by.get("stageinfo"), by.get("bound"), by.get("shadow"), by.get("bgdef")
    lc = nums(si.get("localcoord") if si else None, 2, (320.0, 240.0))
    zoff = _int(si.get("zoffset") if si else None, 200)
    if si and si.get("zoffsetlink") is not None:
        warn.append(f"{source}:{si.line}: zoffsetlink nao modelado")

    air_actions = air.parse(text, source)
    actions = air_actions.actions
    for la in layers:
        if la.type == "anim" and la.actionno is not None and la.actionno not in actions:
            warn.append(f"{source}:{la.line}: [{la.name}] actionno {la.actionno} sem [Begin Action]")
    known = {la.id for la in layers if la.id}
    for cd in ctrldefs:
        for c in cd.ctrls:
            for i in (c.ctrlid if c.ctrlid is not None else cd.ctrlid) or ():
                if i not in known:
                    warn.append(f"{source}:{c.line}: [{c.name}] ctrlid {i} nao corresponde a nenhuma camada")

    shadow_color = nums(sh.get("color") if sh else None, 3, (0.0, 0.0, 0.0))
    return Stage(
        name=ini.unquote(info.get("name")) if info else "",
        localcoord=(int(lc[0]), int(lc[1])),
        camera={**_floats(cam, {"startx": 0, "starty": 0, "boundleft": -95, "boundright": 95,
                                "boundhigh": -25, "boundlow": 0, "verticalfollow": 0.2,
                                "floortension": 0, "tension": 50})},
        player={**_floats(pl, {"p1startx": -70, "p1starty": 0, "p1facing": 1, "p2startx": 70,
                               "p2starty": 0, "p2facing": -1, "leftbound": -1000, "rightbound": 1000})},
        bound=_floats(bd, {"screenleft": 15, "screenright": 15}),
        zoffset=zoff,
        autoturn=bool(_int(si.get("autoturn") if si else None, 1)),
        resetbg=bool(_int(si.get("resetbg") if si else None, 1)),
        shadow={"color": shadow_color, **_floats(sh, {"yscale": 0.4, "reflect": 0})},
        spr=ini.unquote(bgd.get("spr")) if bgd and bgd.get("spr") else "",
        layers=layers, ctrldefs=ctrldefs, actions=actions,
        warnings=warn + [w for w in air_actions.warnings if "linha ignorada" not in w],
    )


def enabled_windows(stage: Stage, layer_id: int) -> list[tuple[int, int, int]]:
    """Janelas (inicio, fim, looptime) em que um BGCtrl Enable liga a camada `layer_id`.
    Base do BGCtrl como evento temporal (o Mega Drive nao roda o interpretador de BGCtrl)."""
    out = []
    for cd in stage.ctrldefs:
        on = None
        for c in sorted(cd.ctrls, key=lambda c: c.time[0]):
            ids = c.ctrlid if c.ctrlid is not None else cd.ctrlid
            if ids is not None and layer_id not in ids:
                continue
            if c.type != "enable" or not c.value:
                continue
            if c.value[0] and on is None:
                on = c.time[0]
            elif not c.value[0] and on is not None:
                out.append((on, c.time[0], cd.looptime))
                on = None
    return out
