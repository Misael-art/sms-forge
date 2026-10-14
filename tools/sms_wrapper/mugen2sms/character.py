"""Etapa de personagem: pacote MUGEN -> IR compilado + relatorio de fidelidade.

Nao gera arquivos SGDK (isso e generators/). Nao altera a origem.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from pathlib import PurePosixPath
import re

from .ir import controllers as C
from .ir import expr as E
from .parsers import air, cmd, cns, ini, sff, snd
from .source import Source

STATEDEF_PARAMS = ("type", "movetype", "physics", "anim", "ctrl", "poweradd", "juggle",
                   "facep2", "hitdefpersist", "movehitpersist", "hitcountpersist", "sprpriority")


@dataclass
class CState:
    number: int
    origin: str                  # personagem | common_forge
    statetype: int
    movetype: int
    physics: int
    params: dict[str, bytes | None]   # anim, ctrl, poweradd, velset x/y, sprpriority...
    flags: dict[str, int]
    controllers: list[C.CController]
    notes: list[str] = field(default_factory=list)


@dataclass
class Character:
    name: str
    author: str
    def_path: str
    source_sha256: str
    info: dict[str, str]
    constants: dict[str, dict[str, str]]
    commands: list[cmd.Command]
    anims: dict[int, air.Action]
    sprites: list[sff.Sprite]
    palettes: list[tuple[str, list]]          # (nome, 256 cores) de pal1..palN
    sounds: list[snd.Sound]
    states: dict[int, CState]
    report: dict
    warnings: list[str]
    raw_states: dict[int, cns.StateDef] = field(default_factory=dict)   # CNS bruto, para analysis/


def _sym(text: str | None, table: dict, default: int) -> int:
    if not text:
        return default
    return table.get(text.strip().lower()[:1], default)


def _compile_states(parsed: cns.CnsResult, origins: dict[int, str], ctx: E.Ctx,
                    sound_index: dict, report: dict) -> dict[int, CState]:
    out = {}
    for n in sorted(parsed.states):
        sd = parsed.states[n]
        p = sd.params
        params: dict[str, bytes | None] = {}
        notes: list[str] = []
        for key in ("anim", "ctrl", "poweradd", "sprpriority", "juggle"):
            if key in p:
                try:
                    ce = E.compile_expr(p[key], ctx)
                    params[key] = ce.code
                    notes += [f"{key}: {u}" for u in ce.unsupported]
                except E.ExprError as e:
                    notes.append(f"{key}: {e}")
        if "velset" in p:
            comps = C.split_top(p["velset"])
            for i, axis in enumerate("xy"):
                if i < len(comps) and comps[i]:
                    params[f"velset.{axis}"] = E.compile_expr(comps[i], ctx).code
        flags = {k: int(p[k]) for k in ("facep2", "hitdefpersist", "movehitpersist", "hitcountpersist")
                 if k in p and p[k].strip().lstrip("-").isdigit()}
        ctrls = [C.compile_controller(c, ctx, sound_index, sd.source) for c in sd.controllers]
        for cc in ctrls:
            key = f"{cc.source_type}:{cc.fidelity}"
            report["controllers"][key] = report["controllers"].get(key, 0) + 1
            if cc.fidelity != "direct":
                report["controller_notes"].append(
                    {"state": n, "type": cc.source_type, "fidelity": cc.fidelity,
                     "line": cc.line, "notes": cc.notes})
        out[n] = CState(n, origins.get(n, "personagem"),
                        _sym(p.get("type"), C.STATETYPE, ord("S")),
                        _sym(p.get("movetype"), C.MOVETYPE, ord("I")),
                        _sym(p.get("physics"), C.PHYSICS, ord("N")),
                        params, flags, ctrls, notes)
    return out


def load(src: Source, def_name: str | None = None) -> Character:
    warnings: list[str] = []
    defs = [d for d in src.defs()]
    if def_name is None:
        chars = [d for d in defs if "[files]" in ini.decode(src.read(d)).lower()
                 and "cns" in ini.decode(src.read(d)).lower()]
        if not chars:
            raise ValueError("nenhum .def de personagem no pacote")
        def_name = chars[0]
        if len(chars) > 1:
            warnings.append(f"varios .def de personagem; usado {def_name} (outros: {chars[1:]})")
    base = str(PurePosixPath(def_name).parent)
    secs = {s.name.lower(): s for s in ini.parse(ini.decode(src.read(def_name)))}
    info = {}
    if "info" in secs:
        for key, value, _ in secs["info"].items:
            if key:
                info[key] = ini.unquote(value)
        # Some older MUGEN character DEFs use the common `Author: name`
        # spelling instead of an INI `author = name` key. Preserve attribution
        # without treating arbitrary free-form INFO lines as fields.
        if not info.get("author"):
            for key, value, _ in secs["info"].items:
                if not key:
                    match = re.match(r"^\s*author\s*:\s*(.*?)\s*$", value, re.I)
                    if match and match.group(1):
                        info["author"] = ini.unquote(match.group(1))
                        break
    files = secs.get("files")
    if files is None:
        raise ValueError(f"{def_name}: sem [Files]")

    missing = []

    def need(key):
        v = files.get(key)
        if not v:
            return None
        n = src.find(v, base)
        if n is None:
            missing.append({"key": key, "ref": v})
        return n

    report = {"missing_refs": missing, "controllers": {}, "controller_notes": [], "commands": {},
              "sprites": {}, "anims": {}, "sounds": {}, "states": {}}

    # comandos
    cmd_name = need("cmd")
    cmd_secs = ini.parse(ini.decode(src.read(cmd_name))) if cmd_name else []
    commands, _, w = cmd.parse(cmd_secs, cmd_name or "<cmd>")
    warnings += w
    report["commands"] = {"total": len(commands), "with_errors": sum(1 for c in commands if c.errors)}

    # estados: ordem MUGEN = st, st1.., stcommon, cmd (-1). Primeiro definido vence.
    parsed = cns.CnsResult({}, {}, [])
    origins: dict[int, str] = {}
    cns_name = need("cns")
    if cns_name:
        cns.parse(ini.parse(ini.decode(src.read(cns_name))), cns_name, parsed)
    for key in ["st"] + [f"st{i}" for i in range(10)]:
        v = files.get(key)
        if v:
            n = src.find(v, base)
            if n and n != cns_name:
                cns.parse(ini.parse(ini.decode(src.read(n))), n, parsed)
            elif n is None:
                missing.append({"key": key, "ref": v})
    # stcommon so preenche lacunas: estados do personagem sempre vencem (sem aviso de duplicata)
    stcommon = files.get("stcommon")
    common_name = src.find(stcommon, base) if stcommon else None
    common = cns.CnsResult({}, {}, [])
    if common_name:
        cns.parse(ini.parse(ini.decode(src.read(common_name))), common_name, common)
        origin = "stcommon"
    else:
        if stcommon:
            missing.append({"key": "stcommon", "ref": stcommon,
                            "resolution": "substituido por common_forge.cns (estados comuns originais do Forge)"})
        text = resources.files("mugen2sms.data").joinpath("common_forge.cns").read_text("utf-8")
        cns.parse(ini.parse(text), "common_forge.cns", common)
        origin = "common_forge"
    warnings += common.warnings
    for n, sd in common.states.items():
        if n not in parsed.states:
            parsed.states[n] = sd
            origins[n] = origin
    for sec, vals in common.constants.items():
        for k, v in vals.items():
            parsed.constants.setdefault(sec, {}).setdefault(k, v)
    if cmd_name:
        cns.parse(cmd_secs, cmd_name, parsed)
    warnings += parsed.warnings

    # animacoes
    anim_name = need("anim")
    anims = air.parse(ini.decode(src.read(anim_name)), anim_name).actions if anim_name else {}

    # sprites e paletas
    sprites: list[sff.Sprite] = []
    spr_name = need("sprite")
    if spr_name:
        sprites, w = sff.parse(src.read(spr_name))
        warnings += w
    palettes = []
    for i in range(1, 13):
        v = files.get(f"pal{i}")
        if not v:
            continue
        n = src.find(v, base)
        if n is None:
            missing.append({"key": f"pal{i}", "ref": v})
            continue
        palettes.append((PurePosixPath(n).stem, sff.read_act(src.read(n))))

    # sons
    sounds: list[snd.Sound] = []
    snd_name = need("sound")
    if snd_name:
        sounds, w = snd.parse(src.read(snd_name))
        warnings += w
    sound_index = {(False, s.group, s.sample): i for i, s in enumerate(sounds)}

    ctx = E.Ctx({c.name.lower(): i for i, c in enumerate(commands)}, parsed.constants, set(anims))
    states = _compile_states(parsed, origins, ctx, sound_index, report)

    # referencias cruzadas
    keys = {(s.group, s.image) for s in sprites}
    miss_spr = sorted({(f.group, f.image) for a in anims.values() for f in a.frames
                       if f.group >= 0 and (f.group, f.image) not in keys})
    report["anims"] = {"total": len(anims), "frames": sum(len(a.frames) for a in anims.values()),
                       "missing_sprites": [list(x) for x in miss_spr],
                       "blend_frames": sum(1 for a in anims.values() for f in a.frames if f.blend)}
    report["sprites"] = {"total": len(sprites), "linked": sum(1 for s in sprites if s.linked_from is not None)}
    report["sounds"] = {"total": len(sounds), "seconds": round(sum(s.seconds for s in sounds), 2),
                        "invalid": sum(1 for s in sounds if s.error)}
    report["states"] = {"total": len(states),
                        "from_common_forge": sorted(n for n, s in states.items() if s.origin == "common_forge")}
    fid = {"direct": 0, "approximate": 0, "unsupported": 0}
    for k, v in report["controllers"].items():
        fid[k.split(":")[1]] += v
    report["controller_fidelity"] = fid

    return Character(info.get("displayname") or info.get("name") or def_name, info.get("author", ""),
                     def_name, src.sha256(), info, parsed.constants, commands, anims, sprites,
                     palettes, sounds, states, report, warnings, parsed.states)
