"""Esquema de controladores de estado suportados pelo runtime + compilacao de parametros.

Cada controlador vira: tipo (u8), programa de condicao, e N parametros fixos por tipo.
Parametro = programa de expressao (bytecode) ou constante simbolica (ints).
Controladores fora do esquema sao classificados (partial/unsupported) no relatorio.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import expr as E
from . import opcodes as O

# ordem = id do controlador no runtime (MG_CT_*)
# cada parametro: nome MUGEN, componente (0=x/primeiro, 1=y/segundo...), default (texto MUGEN ou None=ausente)
SCHEMA: dict[str, list[tuple[str, int, str | None]]] = {
    "null": [],
    "changestate": [("value", 0, None), ("ctrl", 0, None), ("anim", 0, None)],
    "selfstate": [("value", 0, None), ("ctrl", 0, None), ("anim", 0, None)],
    "changeanim": [("value", 0, None), ("elem", 0, "1")],
    "velset": [("x", 0, None), ("y", 0, None)],
    "veladd": [("x", 0, None), ("y", 0, None)],
    "velmul": [("x", 0, None), ("y", 0, None)],
    "posadd": [("x", 0, None), ("y", 0, None)],
    "posset": [("x", 0, None), ("y", 0, None)],
    "ctrlset": [("value", 0, None)],
    "turn": [],
    "gravity": [],
    "sprpriority": [("value", 0, "0")],
    "poweradd": [("value", 0, None)],
    "lifeadd": [("value", 0, None)],
    "posfreeze": [("value", 0, "1")],
    "varset": [],      # tratados a parte (var(n) = expr / v = n, value = expr)
    "varadd": [],
    "varrandom": [],
    "playsnd": [("value", 0, None), ("channel", 0, "-1")],   # value resolvido p/ indice de som
    "stopsnd": [("channel", 0, "-1")],
    "statetypeset": [],  # simbolos -> sym
    "nothitby": [("time", 0, "1")],
    "hitby": [("time", 0, "1")],
    "hitdef": [
        ("damage", 0, "0"), ("damage", 1, "0"),
        ("pausetime", 0, "0"), ("pausetime", 1, "0"),
        ("guard.pausetime", 0, None), ("guard.pausetime", 1, None),
        ("ground.hittime", 0, "0"), ("ground.slidetime", 0, "0"),
        ("guard.hittime", 0, None), ("guard.slidetime", 0, None), ("guard.ctrltime", 0, None),
        ("ground.velocity", 0, "0"), ("ground.velocity", 1, "0"),
        ("air.velocity", 0, "0"), ("air.velocity", 1, "0"),
        ("guard.velocity", 0, None),
        ("air.hittime", 0, "20"),
        ("fall", 0, "0"), ("air.fall", 0, None), ("fall.recover", 0, "1"),
        ("fall.yvelocity", 0, "-4.5"), ("fall.xvelocity", 0, None),
        ("sparkxy", 0, "0"), ("sparkxy", 1, "0"),
        ("p1stateno", 0, "-1"), ("p2stateno", 0, "-1"),
        ("getpower", 0, None), ("givepower", 0, None),
        ("yaccel", 0, ".35"), ("id", 0, "0"), ("chainid", 0, "-1"),
        ("kill", 0, "1"), ("guard.kill", 0, "1"),
    ],
    "projectile": [
        ("projid", 0, "0"), ("projanim", 0, "0"), ("projhitanim", 0, "-1"), ("projremanim", 0, "-1"),
        ("offset", 0, "0"), ("offset", 1, "0"), ("velocity", 0, "0"), ("velocity", 1, "0"),
        ("accel", 0, "0"), ("accel", 1, "0"), ("projremovetime", 0, "-1"), ("projpriority", 0, "1"),
        ("projhits", 0, "1"),
    ],   # + todos os parametros de hitdef (anexados)
    "superpause": [("time", 0, "30"), ("movetime", 0, "0"), ("poweradd", 0, "0"),
                   ("anim", 0, "-1"), ("pos", 0, "0"), ("pos", 1, "0")],
    "targetbind": [("time", 0, "1"), ("pos", 0, "0"), ("pos", 1, "0")],
    "targetstate": [("value", 0, None)],
    "targetvelset": [("x", 0, None), ("y", 0, None)],
    "targetlifeadd": [("value", 0, None)],
    "targetdrop": [],
    "hitvelset": [("x", 0, "1"), ("y", 0, "1")],
    "hitfallvel": [],
    "hitfalldamage": [],
    "hitfallset": [("value", 0, "-1")],
    "envshake": [("time", 0, "10"), ("ampl", 0, "4")],
    "explod": [("anim", 0, None), ("id", 0, "-1"), ("pos", 0, "0"), ("pos", 1, "0"),
               ("vel", 0, "0"), ("vel", 1, "0"), ("removetime", 0, "-2"), ("bindtime", 0, "0"),
               ("sprpriority", 0, "0")],
    "removeexplod": [("id", 0, "-1")],
    "width": [],
    "assertspecial": [],
    "helper": [("stateno", 0, "0"), ("id", 0, "0"), ("pos", 0, "0"), ("pos", 1, "0")],
    "destroyself": [],
}
SCHEMA["projectile"] = SCHEMA["projectile"] + SCHEMA["hitdef"]
CONTROLLER_IDS = {name: i for i, name in enumerate(SCHEMA)}

# Aproximacoes declaradas: tipo MUGEN -> (tipo runtime, motivo)
APPROX = {
    "changeanim2": ("changeanim", "usa anim do proprio personagem (anim de P2 nao suportada)"),
    "makedust": ("null", "poeira decorativa omitida"),
    "forcefeedback": ("null", "sem vibracao no Mega Drive"),
    "fallenvshake": ("null", "tremor de queda omitido"),
    "hitfallvel": ("hitfallvel", ""),
}
UNSUPPORTED_REASON = {
    "afterimage": "VDP nao tem blending/transparencia; rastro exigiria sprites extras (manual)",
    "palfx": "efeito de paleta por RGB exigiria CRAM dinamica (manual)",
    "attackmulset": "multiplicador de ataque nao modelado",
    "gamemakeanim": "animacao de sistema (fightfx) indisponivel",
    "envcolor": "flash de tela exigiria CRAM dinamica (manual)",
}

# simbolos dos parametros textuais do HitDef
ANIMTYPE = {"light": 0, "medium": 1, "med": 1, "hard": 2, "back": 3, "up": 4, "diagup": 5}
GROUNDTYPE = {"high": 1, "low": 2, "trip": 3, "none": 0}
STATETYPE = {"s": ord("S"), "c": ord("C"), "a": ord("A"), "l": ord("L"), "u": ord("U")}
MOVETYPE = {"i": ord("I"), "a": ord("A"), "h": ord("H"), "u": ord("U")}
POSTYPE = {"p1": 0, "p2": 1, "front": 2, "back": 3, "left": 4, "right": 5}
PHYSICS = {"s": ord("S"), "c": ord("C"), "a": ord("A"), "n": ord("N"), "u": ord("U")}


def split_top(text: str) -> list[str]:
    """Divide 'a, ifelse(b,c,d)' respeitando parenteses e aspas."""
    out, depth, cur, q = [], 0, [], False
    for ch in text:
        if ch == '"':
            q = not q
        if not q:
            if ch in "([":
                depth += 1
            elif ch in ")]":
                depth -= 1
            elif ch == "," and depth == 0:
                out.append("".join(cur).strip())
                cur = []
                continue
        cur.append(ch)
    out.append("".join(cur).strip())
    return out


def attr_flags(text: str) -> int:
    """attr = S, NA | hitflag = MAF | guardflag = MA -> bitmask.
    bits 0-2: S,C,A (tipo de estado) ; bits 4-6: N,S,H (classe) ; bits 8-10: A,T,P (ataque/throw/projetil)."""
    parts = [p.strip().upper() for p in text.split(",")]
    m = 0
    for ch in parts[0]:
        m |= {"S": 1, "C": 2, "A": 4}.get(ch, 0)
    for p in parts[1:]:
        if len(p) >= 2:
            m |= {"N": 0x10, "S": 0x20, "H": 0x40}.get(p[0], 0)
            m |= {"A": 0x100, "T": 0x200, "P": 0x400}.get(p[1], 0)
    return m


def flag_letters(text: str) -> int:
    """hitflag/guardflag: H L A M(=HL) F D P + -"""
    m = 0
    for ch in text.strip().upper():
        m |= {"H": 1, "L": 2, "A": 4, "M": 3, "F": 8, "D": 16, "P": 32, "+": 64, "-": 128}.get(ch, 0)
    return m


def sound_ref(text: str, own_prefix: str) -> tuple[bool, int, int] | None:
    """Referencia de som -> (comum, grupo, amostra).

    HitDef hitsound/guardsound: prefixo 'S' = SND do proprio personagem; sem prefixo = fight.snd comum.
    PlaySnd value: prefixo 'F' = fight.snd comum; sem prefixo = SND do personagem.
    """
    parts = split_top(text)
    if len(parts) < 2:
        return None
    g, s = parts[0].strip(), parts[1].strip()
    pre = g[:1].upper() if g[:1].isalpha() else ""
    g = g[1:] if pre else g
    common = (pre != "S") if own_prefix == "S" else (pre == "F")
    try:
        return common, int(g), int(s)
    except ValueError:
        return None


def self_anim_ref(text: str) -> tuple[bool, int] | None:
    """sparkno/anim 'S720' -> (proprio=True, 720); '40' -> (proprio=False, 40) (fightfx comum)."""
    t = text.strip()
    own = t[:1].upper() == "S"
    try:
        return own, int(t[1:] if own else t)
    except ValueError:
        return None


@dataclass
class CParam:
    name: str
    code: bytes | None           # None = ausente (runtime usa default proprio)
    const: float | None = None


@dataclass
class CController:
    type: str                    # nome no SCHEMA (runtime)
    source_type: str             # nome MUGEN original
    fidelity: str                # direct | approximate | unsupported
    notes: list[str]
    cond: bytes
    params: list[CParam]
    sym: dict[str, int] = field(default_factory=dict)   # constantes simbolicas (attr, animtype, sons...)
    line: int = 0
    label: str = ""
    gate: list[int] | None = None
    tgate: tuple[int, int] | None = None


def _param_text(params: dict[str, str], name: str) -> str | None:
    return params.get(name)


def compile_controller(c, ctx: E.Ctx, sounds: dict[tuple[bool, int, int], int], source: str) -> CController:
    src = c.type
    notes: list[str] = []
    rtype = src
    fidelity = "direct"
    if src in APPROX:
        rtype, why = APPROX[src]
        if why:
            notes.append(why)
            fidelity = "approximate"
    if rtype not in SCHEMA:
        reason = UNSUPPORTED_REASON.get(src, "controlador sem implementacao no runtime")
        return CController("null", src, "unsupported", [reason], b"\x01\x00\x00", [], line=c.line, label=c.label)

    cond = E.compile_condition(c.triggerall, c.triggers, ctx)
    notes += [f"trigger: {u}" for u in cond.unsupported]
    params: list[CParam] = []
    for pname, comp, default in SCHEMA[rtype]:
        text = _param_text(c.params, pname)
        if pname == "value" and rtype == "playsnd":
            params.append(CParam(f"{pname}[{comp}]", None))   # resolvido em sym; mantem o indice
            continue
        if text is None:
            text = default
        if text is None:
            params.append(CParam(f"{pname}[{comp}]", None))
            continue
        comps = split_top(text)
        piece = comps[comp] if comp < len(comps) and comps[comp] != "" else None
        if piece is None:
            params.append(CParam(f"{pname}[{comp}]", None))
            continue
        try:
            ce = E.compile_expr(piece, ctx)
        except E.ExprError as e:
            notes.append(f"{pname}: {e}")
            params.append(CParam(f"{pname}[{comp}]", None))
            continue
        notes += [f"{pname}: {u}" for u in ce.unsupported]
        params.append(CParam(f"{pname}[{comp}]", ce.code, ce.constant))

    sym: dict[str, int] = {}
    p = c.params
    if rtype in ("hitdef", "projectile"):
        sym["attr"] = attr_flags(p.get("attr", "S, NA"))
        sym["hitflag"] = flag_letters(p.get("hitflag", "MAF"))
        sym["guardflag"] = flag_letters(p.get("guardflag", ""))
        sym["animtype"] = ANIMTYPE.get(p.get("animtype", "light").strip().lower(), 0)
        sym["air.animtype"] = ANIMTYPE.get(p.get("air.animtype", p.get("animtype", "light")).strip().lower(), 0)
        sym["ground.type"] = GROUNDTYPE.get(p.get("ground.type", "high").strip().lower(), 1)
        sym["air.type"] = GROUNDTYPE.get(p.get("air.type", p.get("ground.type", "high")).strip().lower(), 1)
        pr = split_top(p.get("priority", "4, hit"))
        try:
            sym["priority"] = int(pr[0])
        except ValueError:
            sym["priority"] = 4
        for key in ("hitsound", "guardsound"):
            if key in p:
                ref = sound_ref(p[key], "S")
                sym[key] = sounds.get(ref, -1) if ref else -1
                if ref and sym[key] < 0:
                    notes.append(f"{key} {p[key]} sem amostra disponivel")
                    fidelity = "approximate"
        for key in ("sparkno", "guard.sparkno"):
            ref = self_anim_ref(p[key]) if key in p else None
            if ref is None:
                sym[key] = -2          # runtime usa faisca padrao do personagem ([Data] sparkno)
            elif ref[1] < 0:
                sym[key] = -1          # sem faisca
            elif ref[0] and ref[1] in ctx.anims:
                sym[key] = ref[1]
            else:
                sym[key] = -2
                notes.append(f"{key} {p[key].strip()}: fightfx comum indisponivel; usa faisca padrao")
                fidelity = "approximate"
    if rtype == "superpause":
        ref = self_anim_ref(p.get("anim", "-1"))
        sym["anim"] = ref[1] if ref and ref[0] and ref[1] in ctx.anims else -1
        if ref and ref[1] >= 0 and sym["anim"] < 0:
            notes.append(f"anim {p.get('anim')}: animacao comum indisponivel")
            fidelity = "approximate"
        ref = sound_ref(p["sound"], "S") if "sound" in p else None
        sym["sound"] = sounds.get(ref, -1) if ref else -1
    if rtype == "playsnd":
        ref = sound_ref(p.get("value", ""), "F")
        sym["sound"] = sounds.get(ref, -1) if ref else -1
        if sym["sound"] < 0:
            notes.append(f"som {p.get('value')} indisponivel")
            fidelity = "approximate"
    if rtype == "statetypeset" or src == "statetypeset":
        sym["statetype"] = STATETYPE.get(p.get("statetype", "u").strip().lower()[:1], ord("U"))
        sym["movetype"] = MOVETYPE.get(p.get("movetype", "u").strip().lower()[:1], ord("U"))
        sym["physics"] = PHYSICS.get(p.get("physics", "u").strip().lower()[:1], ord("U"))
    if rtype == "helper":
        sym["postype"] = POSTYPE.get(p.get("postype", "p1").strip().lower(), 0)
        notes.append("helper reduzido: roda estados do dono; nao e atingivel e seus HitDef sao ignorados")
        fidelity = "approximate"
    if rtype in ("nothitby", "hitby"):
        sym["attr"] = attr_flags(p.get("value", p.get("value2", "SCA")))
    if rtype in ("varset", "varadd", "varrandom"):
        target, valtext = _var_assignment(p)
        if target is None:
            return CController("null", src, "unsupported", ["atribuicao de variavel nao reconhecida"],
                               b"\x01\x00\x00", [], line=c.line, label=c.label)
        kind, idx = target
        sym["fvar"] = 1 if kind == "fvar" else 0
        sym["index"] = idx
        if rtype == "varrandom":
            rng = split_top(p.get("range", "0,1000"))
            valtext = f"{rng[0]}" if len(rng) == 1 else f"{rng[1]}"
            sym["min"] = int(float(rng[0])) if len(rng) > 1 else 0
        ce = E.compile_expr(valtext, ctx)
        notes += [f"value: {u}" for u in ce.unsupported]
        params.append(CParam("value", ce.code, ce.constant))

    if any(n.startswith("trigger:") or ": trigger" in n or ": funcao" in n for n in notes) and fidelity == "direct":
        fidelity = "approximate"
    return CController(rtype, src, fidelity, notes, cond.code, params, sym, c.line, c.label, cond.gate, cond.tgate)


_VARKEY = re.compile(r"^(var|fvar|sysvar|sysfvar)\((\d+)\)$")


def _var_assignment(p: dict[str, str]):
    for k, v in p.items():
        m = _VARKEY.match(k.replace(" ", ""))
        if m:
            kind = "fvar" if "fvar" in m.group(1) else "var"
            base = 60 if m.group(1).startswith("sys") else 0   # sysvars no fim da tabela do runtime
            return (kind, base + int(m.group(2))), v
    for key, kind in (("v", "var"), ("fv", "fvar")):
        if key in p:
            try:
                return (kind, int(p[key])), p.get("value", "0")
            except ValueError:
                return None, None
    return None, None
