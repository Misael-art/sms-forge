"""VM de referencia em Python, semantica identica a mg_vm.c (ponto fixo 24.8, sem float).

Usada nos testes de contrato e para validar o bytecode antes de ir para a ROM.
"""
from __future__ import annotations

import struct

from . import opcodes as O

FX = O.FX


def _div(a, b):
    if b == 0:
        return 0
    q = abs(a) * FX // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def _mod(a, b):
    ia, ib = int(a / FX), int(b / FX)
    if ib == 0:
        return 0
    r = abs(ia) % abs(ib)
    return (r if ia >= 0 else -r) * FX


def run(code: bytes, env) -> int:
    """env: objeto com trg(id)->fx, trga(id,argfx)->fx, cmd(idx)->bool, animelemtime(elem)->int ticks."""
    st, pc = [], 0
    while True:
        op = O.OPS[code[pc]]
        pc += 1
        if op == "END":
            return st[-1] if st else 0
        if op == "PUSH8":
            st.append(struct.unpack("b", code[pc:pc + 1])[0] * FX); pc += 1
        elif op == "PUSH16":
            st.append(struct.unpack(">h", code[pc:pc + 2])[0] * FX); pc += 2
        elif op == "PUSHFX":
            st.append(struct.unpack(">i", code[pc:pc + 4])[0]); pc += 4
        elif op == "TRG":
            st.append(env.trg(code[pc])); pc += 1
        elif op == "TRGA":
            st.append(env.trga(code[pc], st.pop())); pc += 1
        elif op == "CMD":
            st.append(FX if env.cmd(code[pc]) else 0); pc += 1
        elif op == "ANIMELEMTIME":
            st.append(env.animelemtime(st.pop() // FX) * FX)
        elif op in ("ANDJ", "ORJ"):
            rel = struct.unpack(">H", code[pc:pc + 2])[0]
            pc += 2
            top = st[-1]
            if op == "ANDJ" and top == 0:
                pc += rel
            elif op == "ORJ" and top != 0:
                st[-1] = FX
                pc += rel
            else:
                st.pop()
        elif op == "BOOL":
            st[-1] = FX if st[-1] else 0
        elif op == "UNSUPPORTED":
            st.append(0); pc += 1
        elif op in ("NEG", "NOT", "BNOT", "ABS", "FLOOR"):
            a = st.pop()
            st.append({"NEG": -a, "NOT": 0 if a else FX, "BNOT": (~(a // FX)) * FX,
                       "ABS": abs(a), "FLOOR": (a >> O.FX_SHIFT) << O.FX_SHIFT}[op])
        elif op == "INRANGE":
            flags = code[pc]; pc += 1
            hi, lo, v = st.pop(), st.pop(), st.pop()
            ok_lo = v >= lo if flags & 1 else v > lo
            ok_hi = v <= hi if flags & 2 else v < hi
            st.append(FX if ok_lo and ok_hi else 0)
        elif op == "IFELSE":
            b, a, c = st.pop(), st.pop(), st.pop()
            st.append(a if c else b)
        else:
            b, a = st.pop(), st.pop()
            if op == "ADD": r = a + b
            elif op == "SUB": r = a - b
            elif op == "MUL": r = (a * b) >> O.FX_SHIFT
            elif op == "DIV": r = _div(a, b)
            elif op == "MOD": r = _mod(a, b)
            elif op == "POW": r = int((a / FX) ** int(b / FX) * FX) if b >= 0 else 0
            elif op == "EQ": r = FX if a == b else 0
            elif op == "NE": r = FX if a != b else 0
            elif op == "LT": r = FX if a < b else 0
            elif op == "LE": r = FX if a <= b else 0
            elif op == "GT": r = FX if a > b else 0
            elif op == "GE": r = FX if a >= b else 0
            elif op == "BAND": r = ((a // FX) & (b // FX)) * FX
            elif op == "BOR": r = ((a // FX) | (b // FX)) * FX
            elif op == "BXOR": r = ((a // FX) ^ (b // FX)) * FX
            elif op == "LAND": r = FX if a and b else 0
            elif op == "LOR": r = FX if a or b else 0
            elif op == "LXOR": r = FX if bool(a) != bool(b) else 0
            else:
                raise ValueError(op)
            st.append(r)
