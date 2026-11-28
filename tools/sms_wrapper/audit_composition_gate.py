#!/usr/bin/env python3
"""Gate de composicao — deriva a largura maxima por linha do metassprite emitido.

Mede o pico de entradas 8x16 que interceptam a mesma scanline, inclusive
quando seus dy diferem. O limite por ator e uma politica declarada do projeto
(default 4); nao decide o budget do par, nem implementa a politica 5+3.
A medida usa exatamente os arrays
que o runtime emite no header do corte (por padrao P1 `_META` e P2
`_P2_METAL`); nao redesenha pose, nao altera corte e nao mede par composto.

Saidas:
  <prefix>_composition_gate.h   arrays const para o runtime
  <prefix>_composition_gate.json detalhe por pose/anim e SHA da fonte

Uso:
  audit_composition_gate.py --header CUT/versus_scene_runtime.h \
      [--out-header DIR/versus_composition_gate.h] \
      [--out-json DIR/versus_composition_gate.json] \
      [--idle-columns 4] [--p1-field meta] [--p2-field p2metal] \
      [--prefix versus] [--anim-count 12]
  audit_composition_gate.py --self-check

Exit: 0 mediu | 1 contrato/reprova | 3 uso/IO

O resultado e diagnostico: nao prova consumo pelo runtime, imagem desenhada,
facing dinamico, par composto, VBlank ou fidelidade. Recusar um papel nao
implementa esse movimento. Saidas existentes nunca sao substituidas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "smsforge.composition_gate/v2"
IDLE_COLUMNS = 4
FRAME_FIELDS = (
    "duration", "pose", "meta", "metal", "clsn", "axis",
    "width", "height", "p2meta", "p2metal",
)
SYMBOL_FIELDS = ("meta", "metal", "p2meta", "p2metal")


class GateError(ValueError):
    """Header fora do contrato do corte ou metassprite malformado."""


def parse_arrays(text: str):
    arrays = {}
    for match in re.finditer(
        r"(?:static\s+)?const\s+unsigned\s+char\s+(\w+)\s*\[\s*(\d+)\s*\]\s*=\s*\{(.*?)\};",
        text,
        re.S,
    ):
        name, size, body = match.group(1), int(match.group(2)), match.group(3)
        body = re.sub(r"/\*.*?\*/|//[^\n]*", "", body, flags=re.S)
        tokens = body.strip().rstrip(",").split(",") if body.strip() else []
        if any(not re.fullmatch(r"\s*(?:0x[0-9A-Fa-f]+|0|[1-9][0-9]*)\s*", v)
               for v in tokens):
            raise GateError(f"{name}: expected literal byte initializers")
        values = [int(v.strip(), 0) for v in tokens]
        if len(values) != size:
            raise GateError(f"{name}: declared {size}, got {len(values)}")
        if name in arrays:
            raise GateError(f"{name}: duplicate array")
        if any(v > 255 for v in values):
            raise GateError(f"{name}: initializer outside byte range")
        arrays[name] = bytes(values)
    aliases = {}
    for match in re.finditer(r"^#define\s+(\w+)\s+(\w+)\s*$", text, re.M):
        name, target = match.group(1), match.group(2)
        if name in aliases:
            raise GateError(f"{name}: duplicate alias")
        aliases[name] = target
    return arrays, aliases


def resolve(name: str, arrays, aliases) -> bytes:
    seen = set()
    while name not in arrays:
        if name not in aliases or name in seen:
            raise GateError(f"unresolved array {name}")
        seen.add(name)
        name = aliases[name]
    return arrays[name]


def cells(name: str, arrays, aliases):
    data = resolve(name, arrays, aliases)
    if not data or data[-1] != 0x80 or (len(data) - 1) % 3:
        raise GateError(f"{name}: malformed metasprite")
    out = []
    for i in range(0, len(data) - 1, 3):
        dx, dy, tile = data[i], data[i + 1], data[i + 2]
        if dx >= 0x80:
            dx -= 0x100
        if dx == -128:
            raise GateError(f"{name}: early metasprite terminator")
        if dy >= 0x80:
            dy -= 0x100
        out.append((dx, dy, tile))
    if not out:
        raise GateError(f"{name}: metasprite has no cells")
    return out


def peak_scanline(entries):
    """Local unclipped bound; SAT parsing counts each full 16-line entry."""
    events = {}
    for _dx, dy, _tile in entries:
        events[dy] = events.get(dy, 0) + 1
        events[dy + 16] = events.get(dy + 16, 0) - 1
    active = peak = 0
    for line in sorted(events):
        active += events[line]
        peak = max(peak, active)
    return peak


def _table_body(text: str, kind: str, table: str) -> str:
    match = re.search(
        r"static\s+const\s+" + kind + r"\s+" + re.escape(table) +
        r"\s*\[[^\]]*\]\s*=\s*\{(.*?)\n\};",
        text,
        re.S,
    )
    if not match:
        raise GateError(f"table {table} not found")
    return match.group(1)


def frame_rows(text: str, table: str):
    rows = []
    for match in re.finditer(r"\{([^{}]*)\}", _table_body(text, "Frame", table)):
        parts = [part.strip() for part in match.group(1).split(",")]
        if len(parts) != len(FRAME_FIELDS):
            raise GateError(
                f"{table}: frame row has {len(parts)} fields; expected {len(FRAME_FIELDS)}"
            )
        try:
            rows.append({
                "duration": int(parts[0], 0),
                "pose": int(parts[1], 0),
                "meta": parts[2],
                "metal": parts[3],
                "clsn": parts[4],
                "axis": parts[5],
                "width": int(parts[6], 0),
                "height": int(parts[7], 0),
                "p2meta": parts[8],
                "p2metal": parts[9],
            })
        except ValueError as error:
            raise GateError(f"{table}: non-integer frame field: {error}") from error
    if not rows:
        raise GateError(f"{table}: empty frame table")
    return rows


def anim_defs(text: str, table: str):
    rows = []
    expected_frames = table[:-5] + "frames_all" if table.endswith("anims") else None
    for match in re.finditer(r"\{([^{}]*)\}", _table_body(text, "Anim", table)):
        parts = [part.strip() for part in match.group(1).split(",")]
        if len(parts) != 4:
            raise GateError(f"{table}: anim row has {len(parts)} fields; expected 4")
        frame_expr = re.fullmatch(r"([A-Za-z_]\w*)\s*\+\s*(\d+)", parts[3])
        if not frame_expr:
            raise GateError(f"{table}: anim frame expression is not '<table> + N': {parts[3]}")
        source_table = frame_expr.group(1)
        if expected_frames is not None and source_table != expected_frames:
            raise GateError(
                f"{table}: points at {source_table}, expected {expected_frames}"
            )
        try:
            rows.append({
                "duration": int(parts[0], 0),
                "count": int(parts[1], 0),
                "loop": int(parts[2], 0),
                "table": source_table,
                "start": int(frame_expr.group(2), 0),
            })
        except ValueError as error:
            raise GateError(f"{table}: non-integer anim field: {error}") from error
    if not rows:
        raise GateError(f"{table}: empty anim table")
    return rows


def _valid_prefix(prefix: str) -> str:
    if not re.fullmatch(r"[a-z_][a-z0-9_]*", prefix):
        raise GateError("prefix must be a lowercase C identifier ([a-z_][a-z0-9_]*)")
    return prefix


def build_gate(
    text: str,
    *,
    source_label: str,
    idle_columns: int = IDLE_COLUMNS,
    p1_field: str = "meta",
    p2_field: str = "p2metal",
    anim_count: int | None = None,
    prefix: str = "versus",
    source_sha256: str | None = None,
):
    """Mede o header e devolve (resultado_json, texto_do_header_gerado)."""
    if not 1 <= idle_columns <= 8:
        raise GateError("idle_columns must be 1..8 (project policy, not pair proof)")
    if p1_field not in SYMBOL_FIELDS or p2_field not in SYMBOL_FIELDS:
        raise GateError(f"emitted field must be one of {SYMBOL_FIELDS}")
    prefix = _valid_prefix(prefix)
    arrays, aliases = parse_arrays(text)
    p1_rows = frame_rows(text, "p1_frames_all")
    p2_rows = frame_rows(text, "p2_frames_all")
    p1_anims = anim_defs(text, "p1_anims")
    p2_anims = anim_defs(text, "p2_anims")
    if len(p1_anims) != len(p2_anims):
        raise GateError("p1/p2 anim counts differ")
    if anim_count is not None and len(p1_anims) != anim_count:
        raise GateError(f"expected {anim_count} anims per side, got {len(p1_anims)}")
    anim_count = len(p1_anims)
    if not 1 <= anim_count <= 128:
        raise GateError("anim count must be 1..128 for the emitted byte index")

    result = {
        "schema": SCHEMA,
        "source_header": source_label,
        "source_header_sha256": source_sha256 or hashlib.sha256(text.encode("ascii")).hexdigest(),
        "sprite_size": "8x16",
        "idle_columns": idle_columns,
        "anim_count": anim_count,
        "emitted_fields": {"p1": p1_field, "p2": p2_field},
        "measurement": "unclipped_local_8x16_scanline_peak",
        "claim_ceiling": "metadata_diagnostic_only",
        "rule": f"pose fits declared per-actor policy iff scanline peak <= {idle_columns}",
        "sides": {},
    }

    flat = []
    for side, rows, anims, field in (
        ("p1", p1_rows, p1_anims, p1_field),
        ("p2", p2_rows, p2_anims, p2_field),
    ):
        side_result = {"anims": [], "dropped_anims": []}
        per_anim = [0] * anim_count
        for index, anim in enumerate(anims):
            if anim["table"] != f"{side}_frames_all":
                raise GateError(
                    f"{side}_anims[{index}] points at {anim['table']}, "
                    f"expected {side}_frames_all"
                )
            start, count = anim["start"], anim["count"]
            if count <= 0 or start < 0 or start + count > len(rows):
                raise GateError(
                    f"{side}_anims[{index}]: frames {start}..{start + count - 1} "
                    f"outside table of {len(rows)}"
                )
            frames = []
            for pos in range(start, start + count):
                row = rows[pos]
                emitted = row[field]
                entries = cells(emitted, arrays, aliases)
                peak = peak_scanline(entries)
                frames.append({
                    "index": pos,
                    "pose": row["pose"],
                    "symbol": re.sub(r"_META$", "", row["meta"]),
                    "emitted": emitted,
                    "width_px": row["width"],
                    "height_px": row["height"],
                    "cells": len(entries),
                    "max_cells_per_row": peak,
                    "legal": peak <= idle_columns,
                })
                per_anim[index] = max(per_anim[index], peak)
            dropped = [frame for frame in frames if not frame["legal"]]
            side_result["anims"].append({
                "anim": index,
                "start": start,
                "n_frames": count,
                "max_cells_per_row": per_anim[index],
                "legal": per_anim[index] <= idle_columns,
                "dropped": dropped,
            })
            if per_anim[index] > idle_columns:
                side_result["dropped_anims"].append(index)
        side_result["max_cells_per_anim"] = per_anim
        result["sides"][side] = side_result
        flat.extend(per_anim)

    dropped_poses = sum(
        len(anim["dropped"])
        for side in ("p1", "p2")
        for anim in result["sides"][side]["anims"]
    )
    result["dropped_pose_count"] = dropped_poses
    result["dropped_pose_total"] = len(p1_rows) + len(p2_rows)
    result["dropped_anim_by_side"] = {
        side: result["sides"][side]["dropped_anims"] for side in ("p1", "p2")
    }
    result["max_cells_by_side"] = {
        side: result["sides"][side]["max_cells_per_anim"] for side in ("p1", "p2")
    }

    upper = prefix.upper()
    guard = upper + "_COMPOSITION_GATE_H"
    header = [
        f"/* {prefix}_composition_gate.h - gerado por audit_composition_gate.py",
        f" * Fonte: {source_label} (campo emitido: P1 {p1_field}; P2 {p2_field}).",
        f" * Politica por ator: pico de scanline <= {idle_columns}; nao aprova o par nem gameplay.",
        " * Nao editar a mao. */",
        f"#ifndef {guard}",
        f"#define {guard}",
        "",
        f"#define {upper}_COMPOSITION_IDLE_COLUMNS {idle_columns}u",
        f"#define {upper}_COMPOSITION_ANIM_COUNT {anim_count}u",
        "",
        f"static const unsigned char {prefix}_anim_max_cells[{anim_count * 2}] = {{",
        "    " + ", ".join(str(v) for v in flat[:anim_count]) + ",",
        "    " + ", ".join(str(v) for v in flat[anim_count:]) + ",",
        "};",
        "",
        f"#define {upper}_ANIM_MAX_CELLS(side, anim) \\",
        f"    ({prefix}_anim_max_cells[(unsigned char)(side) * {upper}_COMPOSITION_ANIM_COUNT + \\",
        "                          (unsigned char)(anim)])",
        f"#define {upper}_ANIM_LEGAL(side, anim) \\",
        f"    ({upper}_ANIM_MAX_CELLS(side, anim) <= {upper}_COMPOSITION_IDLE_COLUMNS)",
        "",
        f"#endif /* {guard} */",
        "",
    ]
    return result, "\n".join(header)


def _summary(result):
    return {
        "dropped_poses": result["dropped_pose_count"],
        "total_poses": result["dropped_pose_total"],
        "p1_dropped_anims": result["dropped_anim_by_side"]["p1"],
        "p2_dropped_anims": result["dropped_anim_by_side"]["p2"],
        "p1_max_cells_per_anim": result["max_cells_by_side"]["p1"],
        "p2_max_cells_per_anim": result["max_cells_by_side"]["p2"],
    }


SYNTHETIC_HEADER = """\
const unsigned char P1_META[4] = { 0x00, 0x00, 0x00, 0x80 };
const unsigned char P1_METAL[4] = { 0x00, 0x00, 0x00, 0x80 };
const unsigned char P1_CLSN[4] = { 0x01, 0x80, 0x01, 0x80 };
const unsigned char P1_AXIS[4] = { 0x00, 0x00, 0x00, 0x00 };
const unsigned char P2_META[4] = { 0x00, 0x00, 0x00, 0x80 };
const unsigned char P2_METAL[4] = { 0x00, 0x00, 0x00, 0x80 };
const unsigned char P2_WIDE_METAL[16] = {
    0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x10, 0x00,
    0x00, 0x18, 0x00, 0x00, 0x20, 0x00, 0x00, 0x80,
};
const unsigned char P2_CLSN[4] = { 0x01, 0x80, 0x01, 0x80 };
const unsigned char P2_AXIS[4] = { 0x00, 0x00, 0x00, 0x00 };

static const Frame p1_frames_all[2] = {
    { 1, 0, P1_META, P1_METAL, P1_CLSN, P1_AXIS, 16, 16, P1_META, P1_META },
    { 1, 1, P1_META, P1_METAL, P1_CLSN, P1_AXIS, 16, 16, P1_META, P1_META },
};
static const Anim p1_anims[2] = {
    { 0, 1, 255, p1_frames_all + 0 },
    { 0, 1, 255, p1_frames_all + 1 },
};
static const Frame p2_frames_all[2] = {
    { 1, 0, P2_META, P2_METAL, P2_CLSN, P2_AXIS, 16, 16, P2_META, P2_WIDE_METAL },
    { 1, 1, P2_META, P2_METAL, P2_CLSN, P2_AXIS, 16, 16, P2_META, P2_METAL },
};
static const Anim p2_anims[2] = {
    { 0, 1, 255, p2_frames_all + 0 },
    { 0, 1, 255, p2_frames_all + 1 },
};
"""


def self_check() -> int:
    checks = []
    checks.append(("dy diferentes sobrepostos contam juntos",
                   peak_scanline([(0, 0, 0)] * 3 + [(8, 8, 0)] * 3) == 6))
    checks.append(("linhas adjacentes nao se sobrepoem",
                   peak_scanline([(0, 0, 0)] * 3 + [(8, 16, 0)] * 3) == 3))
    checks.append(("dy negativo usa signed char como runtime",
                   cells("M", {"M": bytes([0, 248, 0, 128])}, {})[0][1] == -8))
    result, header = build_gate(
        SYNTHETIC_HEADER,
        source_label="<self-check>",
        idle_columns=4,
        p1_field="meta",
        p2_field="p2metal",
        anim_count=2,
        prefix="versus",
    )
    checks.append((
        "P2 wide derruba uma pose",
        result["dropped_pose_count"] == 1
        and result["dropped_pose_total"] == 4
        and result["dropped_anim_by_side"] == {"p1": [], "p2": [0]},
    ))
    checks.append((
        "P1 fica legal em 1 celula",
        result["max_cells_by_side"]["p1"] == [1, 1]
        and result["max_cells_by_side"]["p2"] == [5, 1],
    ))
    checks.append((
        "header gerado carrega arrays e macros",
        "versus_anim_max_cells[4]" in header
        and "1, 1" in header
        and "5, 1" in header
        and "VERSUS_ANIM_LEGAL" in header,
    ))
    try:
        build_gate(
            SYNTHETIC_HEADER.replace("0x80 };", "0x00 };", 1),
            source_label="<bad>",
        )
        malformed_rejected = False
    except GateError:
        malformed_rejected = True
    checks.append(("metassprite sem sentinela reprova", malformed_rejected))

    try:
        build_gate(
            SYNTHETIC_HEADER.replace("const unsigned char P1_META[4]", "const unsigned char P1_META[5]"),
            source_label="<bad-size>",
        )
        size_rejected = False
    except GateError:
        size_rejected = True
    checks.append(("tamanho declarado divergente reprova", size_rejected))

    try:
        build_gate(
            SYNTHETIC_HEADER.replace("p2_frames_all + 0", "p1_frames_all + 0"),
            source_label="<bad-anim>",
        )
        anim_rejected = False
    except GateError:
        anim_rejected = True
    checks.append(("anim apontando para tabela errada reprova", anim_rejected))

    for name, ok in checks:
        print("  %-44s %s" % (name, "ok" if ok else "FALHOU"))
    if not all(ok for _name, ok in checks):
        print("[SELF-CHECK FAIL] composition_gate")
        return 1
    print("[SELF-CHECK OK] audit_composition_gate")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--header", help="header do corte com Frame/Anim")
    parser.add_argument("--out-header", help="header C gerado")
    parser.add_argument("--out-json", help="relatorio JSON")
    parser.add_argument("--idle-columns", type=int, default=IDLE_COLUMNS)
    parser.add_argument("--p1-field", choices=SYMBOL_FIELDS, default="meta")
    parser.add_argument("--p2-field", choices=SYMBOL_FIELDS, default="p2metal")
    parser.add_argument("--prefix", default="versus")
    parser.add_argument("--anim-count", type=int)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)

    if args.self_check:
        return self_check()
    if not args.header:
        print("[FAIL] --header obrigatorio", file=sys.stderr)
        return 3
    header_path = Path(args.header)
    try:
        text = header_path.read_text(encoding="ascii")
        result, generated = build_gate(
            text,
            source_label=str(header_path),
            idle_columns=args.idle_columns,
            p1_field=args.p1_field,
            p2_field=args.p2_field,
            anim_count=args.anim_count,
            prefix=args.prefix,
            source_sha256=hashlib.sha256(header_path.read_bytes()).hexdigest(),
        )
    except (OSError, UnicodeError, GateError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 3

    out_header = Path(args.out_header) if args.out_header else header_path.with_name(
        f"{args.prefix}_composition_gate.h"
    )
    out_json = Path(args.out_json) if args.out_json else header_path.with_name(
        f"{args.prefix}_composition_gate.json"
    )
    try:
        publish_outputs(out_header, out_json, generated, result)
    except OSError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 3

    print(json.dumps(_summary(result)))
    print(f"[PASS] {out_header} e {out_json}", file=sys.stderr)
    return 0


def publish_outputs(out_header, out_json, generated, result):
    """Exclusive publication; remove only our newly created files on failure."""
    paths = [Path(out_header), Path(out_json)]
    if paths[0].resolve() == paths[1].resolve():
        raise OSError("header and JSON outputs must differ")
    for path in paths:
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"output already exists: {path}")
    payloads = [generated, json.dumps(result, indent=2, ensure_ascii=False) + "\n"]
    created = []
    try:
        for path, payload in zip(paths, payloads):
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8") as stream:
                created.append(path)
                stream.write(payload)
    except OSError:
        for path in created:
            path.unlink()
        raise


if __name__ == "__main__":
    sys.exit(main())
