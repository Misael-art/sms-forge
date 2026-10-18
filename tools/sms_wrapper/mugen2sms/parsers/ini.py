"""Leitor tolerante do dialeto INI do MUGEN (.def/.cmd/.cns/.st).

Preserva ordem, secoes repetidas e numero de linha para diagnosticos (arquivo:linha).
Chaves sao normalizadas para minusculas; valores ficam como texto cru (sem avaliar expressoes).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Section:
    name: str          # texto original entre colchetes
    line: int
    items: list[tuple[str, str, int]] = field(default_factory=list)  # (chave, valor, linha)

    def get(self, key: str, default: str | None = None) -> str | None:
        key = key.lower()
        for k, v, _ in self.items:
            if k == key:
                return v
        return default

    def get_all(self, key: str) -> list[tuple[str, int]]:
        key = key.lower()
        return [(v, ln) for k, v, ln in self.items if k == key]


def strip_comment(line: str) -> str:
    # ';' fora de aspas inicia comentario
    out, quoted = [], False
    for ch in line:
        if ch == '"':
            quoted = not quoted
        elif ch == ";" and not quoted:
            break
        out.append(ch)
    return "".join(out).strip()


def parse(text: str) -> list[Section]:
    sections: list[Section] = []
    cur: Section | None = None
    for ln, raw in enumerate(text.splitlines(), 1):
        line = strip_comment(raw)
        if not line:
            continue
        if line.startswith("[") and "]" in line:
            cur = Section(line[1 : line.index("]")].strip(), ln)
            sections.append(cur)
            continue
        if cur is None:
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            cur.items.append((k.strip().lower(), v.strip(), ln))
        else:
            cur.items.append(("", line, ln))  # linhas soltas (ex.: .air)
    return sections


def unquote(v: str | None) -> str | None:
    if v is None:
        return None
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1]
    return v


def decode(data: bytes) -> str:
    # MUGEN nao declara encoding; latin-1 nunca falha e preserva bytes
    return data.decode("latin-1")
