#!/usr/bin/env python3
"""Static RAM layout of an SDCC map against the C objects that occupy it.

The first integrated build overlapped the fixed probe (0xC7A0) because a
missing l__DATA / l__INITIALIZED was treated as length zero. This tool
fails a map that lacks those symbols or whose area table disagrees with
them. A passing verdict is the absence of overlap among segments, absolute
buffers and the stack ceiling — the sum of two segment lengths is printed
and is not the verdict.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

RAM_LO = 0xC000
RAM_HI = 0xE000
MIN_STACK = 256
REQUIRED_LENGTHS = ("DATA", "INITIALIZED", "BSS")

AREA_RE = re.compile(
    r"^(_[A-Z][A-Z0-9]*)\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s+=\s+\d+\.\s+bytes"
)
SYM_RE = re.compile(r"^\s+([0-9A-Fa-f]{8})\s+(\S+)")
DEFINE_RE = re.compile(r"^[ \t]*#define[ \t]+([A-Za-z_]\w*)([ \t]+(.*))?$")
AT_RE = re.compile(
    r"(?:(?:static|const|volatile)[ \t]+)*"
    r"((?:unsigned|signed)[ \t]+)?(char|int|short)[ \t]+"
    r"__at[ \t]*\([ \t]*(0x[0-9A-Fa-f]+|\d+)[ \t]*\)[ \t]*"
    r"([A-Za-z_]\w*)"
    r"((?:[ \t]*\[[^\[\]]+\])*)"
)
TYPE_SIZE = {
    "char": 1, "unsigned char": 1, "signed char": 1,
    "int": 2, "unsigned int": 2, "signed int": 2,
    "short": 2, "unsigned short": 2, "signed short": 2,
}


class LayoutError(Exception):
    pass


def eval_expr(expr: str, names: dict[str, int]) -> int:
    expr = expr.split("//", 1)[0].strip()
    expr = re.sub(r"(0x[0-9A-Fa-f]+|\d+)[uU]\b", r"\1", expr)
    tree = ast.parse(expr, mode="eval")

    def ev(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return node.value
        if isinstance(node, ast.Name):
            if node.id not in names:
                raise LayoutError(node.id)
            return names[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            a, b = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add):
                return a + b
            if isinstance(node.op, ast.Sub):
                return a - b
            return a * b
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        raise LayoutError(type(node).__name__)

    return ev(tree)


def load_defines(text: str) -> dict[str, int]:
    raw: dict[str, str] = {}
    for line in text.splitlines():
        m = DEFINE_RE.match(line)
        if not m or m.group(2) is None:
            continue
        name, _gap, body = m.group(1), m.group(2), m.group(3)
        if body is None or "(" in name:
            continue
        raw[name] = body.strip()
    resolved: dict[str, int] = {}
    pending = dict(raw)
    for _ in range(len(pending) + 1):
        stuck = {}
        for name, body in pending.items():
            try:
                resolved[name] = eval_expr(body, resolved)
            except (LayoutError, SyntaxError, ValueError):
                stuck[name] = body
        if len(stuck) == len(pending):
            break
        pending = stuck
    return resolved


def parse_objects(text: str, defines: dict[str, int]) -> dict[str, tuple[int, int]]:
    found: dict[str, tuple[int, int]] = {}
    for m in AT_RE.finditer(text):
        signedness = (m.group(1) or "").strip()
        base = m.group(2)
        key = (signedness + " " + base).strip()
        if key not in TYPE_SIZE:
            raise LayoutError(f"tipo sem tamanho conhecido: {key}")
        addr = int(m.group(3), 0)
        name = m.group(4)
        dims = re.findall(r"\[([^\[\]]+)\]", m.group(5) or "")
        size = TYPE_SIZE[key]
        for dim in dims:
            n = eval_expr(dim.strip(), defines)
            if n <= 0:
                raise LayoutError(f"{name}: dimensao {dim!r} invalida")
            size *= n
        if name in found and found[name] != (addr, size):
            raise LayoutError(f"{name} declarado duas vezes")
        found[name] = (addr, size)
    return found


def parse_sources(paths: list[Path]) -> dict[str, tuple[int, int]]:
    chunks = [p.read_text(encoding="utf-8", errors="replace") for p in paths]
    text = "\n".join(chunks)
    defines = load_defines(text)
    return parse_objects(text, defines)


def parse_map(text: str) -> tuple[dict[str, tuple[int, int]], dict[str, int]]:
    areas: dict[str, tuple[int, int]] = {}
    symbols: dict[str, int] = {}
    for line in text.replace("\x0c", "\n").splitlines():
        am = AREA_RE.match(line)
        if am:
            name, addr_s, size_s = am.group(1), am.group(2), am.group(3)
            addr, size = int(addr_s, 16), int(size_s, 16)
            if name in areas and areas[name] != (addr, size):
                raise LayoutError(f"area {name} repetida com outro tamanho")
            areas[name] = (addr, size)
            continue
        sm = SYM_RE.match(line)
        if not sm:
            continue
        addr, name = int(sm.group(1), 16), sm.group(2)
        if name in symbols and symbols[name] != addr:
            raise LayoutError(f"simbolo {name} em dois enderecos")
        symbols[name] = addr
    return areas, symbols


def sp_from_rom(rom: bytes) -> int:
    hits = []
    window = rom[:16]
    for i in range(max(0, len(window) - 2)):
        if window[i] == 0x31:
            hits.append(window[i + 1] | (window[i + 2] << 8))
    if len(hits) != 1:
        raise LayoutError(
            f"ld sp no reset: {len(hits)} imediatos nos primeiros 16 bytes "
            "(esperado exatamente 1)")
    sp = hits[0]
    if not (RAM_LO < sp <= RAM_HI):
        raise LayoutError(f"SP inicial {sp:#06x} fora da RAM de trabalho")
    return sp


def _contains(start: int, end: int, addr: int) -> bool:
    return start <= addr < end


def analyze(map_text: str, objects: dict[str, tuple[int, int]], sp: int,
            min_stack: int = MIN_STACK) -> tuple[list[str], list[str]]:
    """Return (failures, report lines). Empty failures means the static layout fits."""
    failures: list[str] = []
    lines: list[str] = []
    try:
        areas, symbols = parse_map(map_text)
    except LayoutError as exc:
        return [f"mapa invalido: {exc}"], []

    if not areas and not symbols:
        return ["mapa invalido: nenhuma area e nenhum simbolo"], []

    lengths: dict[str, int] = {}
    for seg in REQUIRED_LENGTHS:
        key = f"l__{seg}"
        if key not in symbols:
            failures.append(
                f"simbolo obrigatorio ausente: {key} "
                "(ausencia nao vale comprimento zero)")
            continue
        lengths[seg] = symbols[key]

    segments: list[tuple[str, int, int]] = []
    for seg, length in lengths.items():
        area = areas.get(f"_{seg}")
        if length == 0:
            if area and area[1] != 0:
                failures.append(f"l__{seg}=0 mas a area _{seg} tem {area[1]} bytes")
            continue
        if area is None:
            failures.append(f"l__{seg}={length:#x} sem area _{seg} no mapa")
            continue
        addr, size = area
        if size != length:
            failures.append(
                f"_{seg}: area {size:#x} diverge de l__{seg} {length:#x}")
        origin = symbols.get(f"s__{seg}")
        if origin is not None and origin != addr:
            failures.append(
                f"s__{seg} {origin:#06x} diverge do endereco da area {addr:#06x}")
        end = addr + size
        if end < addr or addr < RAM_LO or end > RAM_HI:
            failures.append(f"_{seg} {addr:#06x}+{size:#x} sai da RAM {RAM_LO:#06x}-{RAM_HI:#06x}")
            continue
        segments.append((seg, addr, end))
        lines.append(f"segmento _{seg} {addr:#06x}+{size:#x} termina {end:#06x}")

    data_end = None
    if "DATA" in lengths and "INITIALIZED" in lengths:
        data_end = RAM_LO + lengths["DATA"] + lengths["INITIALIZED"]
        lines.append(
            f"soma DATA+INITIALIZED termina {data_end:#06x} "
            "(nao e o veredito; BSS e absolutos entram na conta)")

    intervals: list[tuple[str, int, int]] = [
        (f"_{name}", start, end) for name, start, end in segments
    ]
    segment_spans = [(start, end) for _n, start, end in intervals]

    def in_segment(addr: int) -> bool:
        return any(_contains(s, e, addr) for s, e in segment_spans)

    # __at objects stay absolute even when a segment has grown over them.
    # Treating "address falls inside _DATA" as membership hid that overlap.
    by_symbol = {f"_{name}": (addr, size) for name, (addr, size) in objects.items()
                 if RAM_LO <= addr < RAM_HI}
    ram_syms = {
        name: addr for name, addr in symbols.items()
        if RAM_LO <= addr < RAM_HI and not name.startswith(("l__", "s__"))
    }

    for sym, (addr, size) in sorted(by_symbol.items(), key=lambda kv: kv[1][0]):
        if sym not in ram_syms:
            failures.append(f"{sym} declarado em {addr:#06x} nao aparece no mapa")
            continue
        if ram_syms[sym] != addr:
            failures.append(f"{sym}: fonte {addr:#06x} mapa {ram_syms[sym]:#06x}")
            continue
        end = addr + size
        if end > RAM_HI:
            failures.append(f"{sym} {addr:#06x}+{size:#x} sai da RAM")
            continue
        intervals.append((sym, addr, end))
        lines.append(f"absoluto {sym} {addr:#06x}+{size:#x} termina {end:#06x}")

    for sym, addr in sorted(ram_syms.items(), key=lambda kv: kv[1]):
        if sym in by_symbol or in_segment(addr):
            continue
        failures.append(f"absoluto {sym} em {addr:#06x} sem tamanho no fonte")

    intervals.sort(key=lambda it: (it[1], it[2], it[0]))
    for i in range(len(intervals)):
        n1, a1, b1 = intervals[i]
        for n2, a2, b2 in intervals[i + 1:]:
            if a2 >= b1:
                break
            failures.append(f"sobreposicao {n1} {a1:#06x}-{b1:#06x} com {n2} {a2:#06x}-{b2:#06x}")

    if not (RAM_LO < sp <= RAM_HI):
        failures.append(f"SP {sp:#06x} fora da RAM")
    else:
        lines.append(f"SP inicial {sp:#06x} (ld sp do reset)")
        if intervals:
            top_name, _top_s, top_e = max(intervals, key=lambda it: it[2])
            if top_e > sp:
                failures.append(
                    f"{top_name} termina {top_e:#06x}, acima do SP {sp:#06x}")
            else:
                reserve = sp - top_e
                lines.append(
                    f"reserva de stack {reserve} B entre {top_name} {top_e:#06x} e SP "
                    f"(piso {min_stack} B; profundidade de chamada nao medida)")
                if reserve < min_stack:
                    failures.append(
                        f"reserva de stack {reserve} B < piso {min_stack} B")
        else:
            failures.append("nenhum intervalo medido; layout nao verificavel")

    return failures, lines


def _synthetic_map(areas: list[tuple[str, int, int]], symbols: dict[str, int]) -> str:
    chunks = []
    for name, addr, size in areas:
        chunks.append(f"{name:<32}{addr:08X}    {size:08X} = {size:8d}. bytes (REL,CON)")
    for name, addr in symbols.items():
        chunks.append(f"     {addr:08X}  {name}")
    return "\n".join(chunks) + "\n"


def self_check() -> None:
    good_areas = [("_DATA", 0xC000, 0x100), ("_INITIALIZED", 0xC100, 0x10),
                  ("_BSS", 0xC110, 0x20)]
    good_syms = {
        "l__DATA": 0x100, "l__INITIALIZED": 0x10, "l__BSS": 0x20,
        "s__DATA": 0xC000, "s__INITIALIZED": 0xC100, "s__BSS": 0xC110,
        "_buf": 0xD000,
    }
    good_obj = {"buf": (0xD000, 16)}
    fail, lines = analyze(_synthetic_map(good_areas, good_syms), good_obj, 0xDFF0)
    assert not fail, fail
    assert any("nao e o veredito" in ln for ln in lines)

    missing = dict(good_syms)
    del missing["l__DATA"]
    fail, _ = analyze(_synthetic_map(good_areas, missing), good_obj, 0xDFF0)
    assert any("l__DATA" in f and "ausente" in f for f in fail), fail

    missing_i = dict(good_syms)
    del missing_i["l__INITIALIZED"]
    fail, _ = analyze(_synthetic_map(good_areas, missing_i), good_obj, 0xDFF0)
    assert any("l__INITIALIZED" in f for f in fail), fail

    # DATA+INITIALIZED still ends under 0xC7A0, but the segment covers an absolute.
    clash_areas = [("_DATA", 0xC000, 0x720), ("_INITIALIZED", 0xC720, 0)]
    clash_syms = {
        "l__DATA": 0x720, "l__INITIALIZED": 0, "l__BSS": 0,
        "s__DATA": 0xC000, "_probe": 0xC700,
    }
    fail, _ = analyze(_synthetic_map(clash_areas, clash_syms),
                      {"probe": (0xC700, 16)}, 0xDFF0)
    assert any("sobreposicao" in f for f in fail), fail

    # BSS reaches the absolute while DATA+INITIALIZED alone would look fine.
    bss_areas = [("_DATA", 0xC000, 0x10), ("_INITIALIZED", 0xC010, 0),
                 ("_BSS", 0xC010, 0x800)]
    bss_syms = {
        "l__DATA": 0x10, "l__INITIALIZED": 0, "l__BSS": 0x800,
        "s__DATA": 0xC000, "s__BSS": 0xC010, "_probe": 0xC700,
    }
    fail, _ = analyze(_synthetic_map(bss_areas, bss_syms),
                      {"probe": (0xC700, 8)}, 0xDFF0)
    assert any("sobreposicao" in f and "_BSS" in f for f in fail), fail

    overlap_syms = dict(good_syms)
    overlap_syms["_other"] = 0xD008
    fail, _ = analyze(_synthetic_map(good_areas, overlap_syms),
                      {"buf": (0xD000, 16), "other": (0xD008, 8)}, 0xDFF0)
    assert any("sobreposicao" in f for f in fail), fail

    fail, _ = analyze(_synthetic_map(good_areas, good_syms),
                      {"buf": (0xD000, 16)}, 0xD020)
    assert any("reserva de stack" in f for f in fail), fail

    # End exactly MIN_STACK below SP passes; one byte closer fails.
    tight_syms = dict(good_syms)
    tight_syms["_buf"] = 0xDE00
    fail, _ = analyze(_synthetic_map(good_areas, tight_syms),
                      {"buf": (0xDE00, 0xF0)}, 0xDFF0)
    assert not fail, fail
    fail, _ = analyze(_synthetic_map(good_areas, tight_syms),
                      {"buf": (0xDE00, 0xF1)}, 0xDFF0)
    assert any("reserva de stack" in f for f in fail), fail

    orphan = dict(good_syms)
    orphan["_mystery"] = 0xD100
    fail, _ = analyze(_synthetic_map(good_areas, orphan), good_obj, 0xDFF0)
    assert any("_mystery" in f for f in fail), fail

    fail, _ = analyze(_synthetic_map(good_areas, good_syms),
                      {"buf": (0xD000, 16), "ghost": (0xD200, 4)}, 0xDFF0)
    assert any("ghost" in f for f in fail), fail

    bad_area = [("_DATA", 0xC000, 0x50), ("_INITIALIZED", 0xC100, 0x10)]
    fail, _ = analyze(_synthetic_map(bad_area, good_syms), good_obj, 0xDFF0)
    assert any("diverge" in f for f in fail), fail

    fail, _ = analyze("", {}, 0xDFF0)
    assert any("mapa invalido" in f for f in fail), fail

    src = ("#define OUT_PIECES 40u\n"
           "volatile unsigned char __at(0xD000) sat_y[72];\n"
           "volatile unsigned int __at(0xC7EB) probe_vovf;\n"
           "volatile unsigned char __at(0xD100) tmpl[2][3 * OUT_PIECES];\n")
    objs = parse_objects(src, load_defines(src))
    assert objs["sat_y"] == (0xD000, 72)
    assert objs["probe_vovf"] == (0xC7EB, 2)
    assert objs["tmpl"] == (0xD100, 240)

    rom = bytes([0xF3, 0xED, 0x56, 0x31, 0xF0, 0xDF]) + bytes(16)
    assert sp_from_rom(rom) == 0xDFF0
    try:
        sp_from_rom(bytes(16))
        raise AssertionError("ROM sem ld sp deveria falhar")
    except LayoutError:
        pass
    print("[PASS] check_ram_layout self-check")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--map", type=Path)
    ap.add_argument("--sources", type=Path, nargs="*", default=[])
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--sp", type=lambda s: int(s, 0), default=None)
    ap.add_argument("--min-stack", type=int, default=MIN_STACK)
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        self_check()
        return 0
    if args.map is None or not args.sources:
        ap.error("--map e --sources sao obrigatorios")
    if args.rom is None and args.sp is None:
        ap.error("--rom (ld sp medido) ou --sp")
    try:
        objects = parse_sources(args.sources)
        sp = sp_from_rom(args.rom.read_bytes()) if args.rom else args.sp
        if args.rom and args.sp is not None and sp != args.sp:
            print(f"[FAIL] SP do ROM {sp:#06x} diverge de --sp {args.sp:#06x}")
            return 1
    except (LayoutError, OSError, SyntaxError) as exc:
        print(f"[FAIL] {exc}")
        return 1
    failures, lines = analyze(args.map.read_text(encoding="utf-8", errors="replace"),
                              objects, sp, args.min_stack)
    for ln in lines:
        print(f"[RAM] {ln}")
    if failures:
        for f in failures:
            print(f"[FAIL] {f}")
        return 1
    print(f"[PASS] layout estatico sem sobreposicao; reserva de stack acima de "
          f"{args.min_stack} B. A soma de dois comprimentos nao fecha a RAM.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
