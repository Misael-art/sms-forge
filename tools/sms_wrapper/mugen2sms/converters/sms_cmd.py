"""Comandos MUGEN -> patterns de buffer para o interpretador do Plano 2.

Pad SMS (SMSlib.h:296-302): 4 direcoes + KEY_1 + KEY_2. Diagonal = duas direcoes juntas
(so direcoes OPOSTAS sao impossiveis); `$F`/`$D` aceitam qualquer diagonal vizinha e sao
codificados por um bit do blob CMD v3/v4.
Corrigido em 2026-09-30 (L093): o texto anterior dizia "diagonal mecanicamente impossivel" e "1 botao".
Com `controls` (mapa do GDD, doc/22) cada tecla MUGEN vira o bit da sua familia fisica mais o
nivel de tier exigido; sem `controls` so `a`/`s` sao expressaveis e o resto segue pulado.
Convencao: F/B viram R/L relativos a frente; o runtime inverte pela facing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

DIR_BITS = {"U": 0x01, "D": 0x02, "B": 0x04, "F": 0x08, "N": 0x00}   # B=retrato, N=nenhum
KEY_BITS = {"a": 0x01, "s": 0x02}          # legado, sem mapa: a = tecla 1, s = tecla 2
PHYSICS = {"1": 0x01, "2": 0x02}           # tecla fisica do pad -> bit no nibble de botoes
DIAGONALS = {"DF": 0x0A, "DB": 0x06, "UF": 0x09, "UB": 0x05}   # D|F, D|B, U|F, U|B

# Blob: [BLOB_FMT_VERSION, n_passos, janela, buffer] e, por passo,
# [dir | keys<<4, flags, release_time]. V4 acrescenta um byte de carga para
# `~N` sem depender de manter toda a carga no anel de amostras.
BLOB_FMT_VERSION = 4
LEGACY_BLOB_FMT_VERSION = 3
TIER_FIELD_MAX = 3          # 2 bits: 0 = sem requisito, 1..3 = indice do tier + 1
TIER_RUNTIME_MAX = 2        # input_tier.c implements apenas fraco/forte


def route_command_prefix(route_id: str) -> str:
    """Stable, map-safe C prefix for one imported source route.

    SDCC's map output truncates long symbol names. A short readable stem plus
    a hash keeps distinct routes distinguishable in the ROM map as well as C.
    """
    if not isinstance(route_id, str) or not route_id.strip():
        raise ValueError("route id must be a non-empty string")
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", route_id.strip()).strip("_").upper()
    if not slug:
        raise ValueError("route id has no C identifier characters")
    digest = hashlib.sha256(slug.encode("ascii")).hexdigest()[:8].upper()
    return f"CUT_R_{slug[:4]}_{digest}"


def route_command_symbol(route_id: str, definition_index: int) -> str:
    if type(definition_index) is not int or definition_index < 0:
        raise ValueError("route command definition index must be non-negative")
    return f"{route_command_prefix(route_id)}_{definition_index}"


@dataclass
class StepCode:
    dir: int = 0
    keys: int = 0
    hold: bool = False
    release: bool = False
    rel_time: int = 0
    tier: int = 0           # 0 = qualquer pressao; i+1 = nivel i do mapa
    four_way: bool = False  # `$D`/$F: direcao cardinal tambem casa diagonais vizinhas


@dataclass
class Pattern:
    name: str
    window: int                                   # ticks maximos do comando
    buffer: int
    steps: list[StepCode] = field(default_factory=list)


def serialize_pattern(p: Pattern) -> bytes:
    data = bytearray([BLOB_FMT_VERSION, len(p.steps), p.window & 0xFF, p.buffer & 0xFF])
    for st in p.steps:
        data += bytes([st.dir | st.keys << 4,
                       (1 if st.hold else 0) | (2 if st.release else 0) |
                       (st.tier << 2) | (0x10 if st.four_way else 0),
                       st.rel_time & 0xFF])
    return bytes(data)


def to_patterns(commands, controls=None) -> tuple[list[Pattern], dict[str, str]]:
    """(patterns suportadas, {nome: motivo} das que exigem reautoria manual)."""
    out, skipped = [], {}
    for c in commands:
        bad = _unsupported(c, controls)
        if bad:
            skipped[c.name] = bad
            continue
        steps = []
        for st in c.steps:
            code = StepCode()
            for k in st.keys:
                if k.four_way and (k.key in DIR_BITS or k.key in DIAGONALS):
                    code.four_way = True
                if k.key in DIAGONALS:
                    code.dir |= DIAGONALS[k.key]
                elif k.key in DIR_BITS:
                    code.dir |= DIR_BITS[k.key]
                elif k.key == "n":
                    pass                              # "nenhuma tecla" nao acrescenta bits
                elif controls is not None:
                    phys, tier = controls.locate(k.key)
                    code.keys |= PHYSICS[phys]
                    code.tier = max(code.tier, tier + 1)
                else:
                    code.keys |= KEY_BITS[k.key]
                code.hold = code.hold or k.hold
                code.release = code.release or k.release
                code.rel_time = max(code.rel_time, k.release_time)
            if bad:
                break
            steps.append(code)
        if bad:
            skipped[c.name] = bad
            continue
        out.append(Pattern(c.name, c.time, c.buffer_time, steps))
    return out, skipped


def _unsupported(c, controls=None) -> str | None:
    for st in c.steps:
        if st.strict:
            return "strict-step-nao-suportado-no-runtime"
        timed = [k for k in st.keys if k.release_time]
        if timed:
            if any(k.release_time > 0xFF for k in timed):
                return "release-time-acima-de-255"
            if (len(st.keys) != 1 or len(timed) != 1 or
                    timed[0].key not in DIR_BITS or not timed[0].release or
                    timed[0].hold):
                return "release-time-exige-uma-direcao-cardinal"
        tiers: dict[str, int] = {}
        for k in st.keys:
            if k.key in DIR_BITS or k.key in DIAGONALS or k.key == "n":
                continue
            if controls is None:
                if k.key not in KEY_BITS:
                    return "botao>pad"
                continue
            loc = controls.locate(k.key)
            if loc is None:
                if k.key in controls.dropped:
                    return "botao-sem-tier-no-mapa"
                return "start-reservado" if k.key == "s" else "botao>pad"
            phys, tier = loc
            if tier + 1 > TIER_FIELD_MAX:
                return "tier-acima-de-3-niveis"
            if tier + 1 > TIER_RUNTIME_MAX:
                return "tier-acima-da-maquina-runtime"
            if phys in tiers:
                if tiers[phys] != tier:
                    return "acorde-na-mesma-tecla"
                continue
            # um passo carrega UM campo de tier: dois botoes de familias diferentes
            # so convivem se pedirem o mesmo nivel (a+x); a+z nao e representavel.
            if any(t != tier for t in tiers.values()):
                return "acorde-entre-teclas-tiers-diversos"
            tiers[phys] = tier
    timed_steps = [index for index, st in enumerate(c.steps)
                   if any(key.release_time for key in st.keys)]
    if len(timed_steps) > 1:
        return "multiplos-release-times-nao-suportados"
    if timed_steps and timed_steps[0] != 0:
        return "release-time-deve-ser-primeiro-passo"
    if c.errors:
        return "cmd-com-erro-de-parse"
    return None
