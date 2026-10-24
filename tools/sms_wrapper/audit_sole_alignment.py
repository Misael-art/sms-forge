#!/usr/bin/env python3
"""Auditoria de alinhamento do pe — AXIS_y, linha opaca e hurtbox CLSN2.

Le o header emitido pelo corte (arrays AXIS/CLSN e a tabela Frame) e o PNG
indexado do quadro em `display_fit`. Calcula:

  sole_offset      = int16(AXIS_y) + ultima linha opaca do PNG
  hurt_bottom      = maior y2 entre as hurtboxes (CLSN2)
  hurt_minus_sole  = hurt_bottom - sole_offset

O PNG e a fonte visual do mesmo corte: a linha opaca e medida no PNG nativo,
sem reescalar. Indice 0 e transparente por contrato do workspace; tRNS tambem
e respeitado. O tool nao redesenha, nao corrige e nao promove o +1 px a lei:
ele mede e, se pedido, reprova pelo limite declarado.

Uso:
  audit_sole_alignment.py --header CUT/versus_scene_runtime.h \
      --pose-root out/display_fit/pose_budget_8 \
      [--symbol P1_RYU_A0F0 --symbol P1_RYU_A260F0 ...] \
      [--max-abs-delta 1] [--out relatorio.json]
  audit_sole_alignment.py --self-check

Mapeamento simbolo -> PNG:
  P1_RYU_A260F0 -> <pose-dir-p1>/frames.json actions["260"][0]
                 -> <pose-dir-p1>/sheets/g<group>_<image>.png
  O lado vem do prefixo P1/P2; o diretorio pode ser explicito
  (`--pose-dir p1=... --pose-dir p2=...`) ou derivado de `--pose-root`
  pelo nome do lutador no simbolo (RYU/KEN).

Exit: 0 mediu | 1 limite excedido/sem quadro | 3 uso/IO/contrato
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import png_io  # noqa: E402
from report_output import write_new_report  # noqa: E402

SCHEMA = "smsforge.sole_alignment/v2"
CLSN_SENTINEL = -32767
FRAME_FIELDS = (
    "duration", "pose", "meta", "metal", "clsn", "axis",
    "width", "height", "p2meta", "p2metal",
)


class SoleError(ValueError):
    """Header, frames.json ou PNG fora do contrato."""


def parse_arrays(text: str):
    arrays = {}
    for match in re.finditer(
        r"(?:static\s+)?const\s+unsigned\s+char\s+(\w+)\s*\[\s*(\d+)\s*\]\s*=\s*\{(.*?)\};",
        text,
        re.S,
    ):
        name, size, body = match.group(1), int(match.group(2)), match.group(3)
        values = [int(v, 0) for v in re.findall(r"0x[0-9A-Fa-f]+|\b\d+\b", body)]
        if len(values) != size:
            raise SoleError(f"{name}: declared {size}, got {len(values)}")
        if name in arrays:
            raise SoleError(f"{name}: duplicate array")
        arrays[name] = bytes(values)
    aliases = {}
    for match in re.finditer(r"^#define\s+(\w+)\s+(\w+)\s*$", text, re.M):
        name, target = match.group(1), match.group(2)
        if name in aliases:
            raise SoleError(f"{name}: duplicate alias")
        aliases[name] = target
    return arrays, aliases


def resolve(name: str, arrays, aliases) -> bytes:
    seen = set()
    while name not in arrays:
        if name not in aliases or name in seen:
            raise SoleError(f"unresolved array {name}")
        seen.add(name)
        name = aliases[name]
    return arrays[name]


def _table_body(text: str, kind: str, table: str) -> str:
    match = re.search(
        r"static\s+const\s+" + kind + r"\s+" + re.escape(table) +
        r"\s*\[[^\]]*\]\s*=\s*\{(.*?)\n\};",
        text,
        re.S,
    )
    if not match:
        raise SoleError(f"table {table} not found")
    return match.group(1)


def frame_rows(text: str, table: str):
    rows = []
    for match in re.finditer(r"\{([^{}]*)\}", _table_body(text, "Frame", table)):
        parts = [part.strip() for part in match.group(1).split(",")]
        if len(parts) != len(FRAME_FIELDS):
            raise SoleError(
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
            raise SoleError(f"{table}: non-integer frame field: {error}") from error
    if not rows:
        raise SoleError(f"{table}: empty frame table")
    return rows


def anim_defs(text: str, table: str):
    rows = []
    expected_frames = table[:-5] + "frames_all" if table.endswith("anims") else None
    for match in re.finditer(r"\{([^{}]*)\}", _table_body(text, "Anim", table)):
        parts = [part.strip() for part in match.group(1).split(",")]
        if len(parts) != 4:
            raise SoleError(f"{table}: anim row has {len(parts)} fields; expected 4")
        frame_expr = re.fullmatch(r"([A-Za-z_]\w*)\s*\+\s*(\d+)", parts[3])
        if not frame_expr:
            raise SoleError(f"{table}: anim frame expression is not '<table> + N': {parts[3]}")
        source_table = frame_expr.group(1)
        if expected_frames is not None and source_table != expected_frames:
            raise SoleError(
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
            raise SoleError(f"{table}: non-integer anim field: {error}") from error
    if not rows:
        raise SoleError(f"{table}: empty anim table")
    return rows


def symbol_base(name: str) -> str:
    if not isinstance(name, str) or not name or name == "0":
        raise SoleError(f"invalid frame symbol {name!r}")
    return re.sub(r"_META$", "", name)


def symbol_action_frame(symbol: str):
    match = re.search(r"_A(\d+)F(\d+)$", symbol)
    if not match:
        raise SoleError(f"symbol does not encode action/frame: {symbol}")
    return int(match.group(1)), int(match.group(2))


def axis_y(data: bytes) -> int:
    if len(data) != 4:
        raise SoleError(f"AXIS must be 4 bytes, got {len(data)}")
    return struct.unpack("<hh", data)[1]


def clsn_sections(data: bytes):
    if not data or len(data) % 2:
        raise SoleError(f"CLSN must be an even byte string, got {len(data)}")
    values = list(struct.unpack("<%dh" % (len(data) // 2), data))

    def read_boxes(start):
        boxes = []
        index = start
        while index < len(values):
            if values[index] == CLSN_SENTINEL:
                return boxes, index + 1
            if index + 4 > len(values):
                raise SoleError(f"CLSN truncated box at int16 index {index}")
            boxes.append(tuple(values[index:index + 4]))
            index += 4
        raise SoleError("CLSN missing sentinel")

    hit, cursor = read_boxes(0)
    hurt, cursor = read_boxes(cursor)
    if cursor != len(values):
        raise SoleError(f"CLSN trailing data after hurt sentinel: {len(values) - cursor} int16")
    return hit, hurt


def alignment(axis_y_value: int, sole_row: int, hurt_boxes):
    """Retorna (sole_offset, hurt_bottom, hurt_minus_sole). Puro para self-check."""
    sole_offset = axis_y_value + sole_row
    hurt_bottom = max((box[3] for box in hurt_boxes), default=None)
    delta = None if hurt_bottom is None else hurt_bottom - sole_offset
    return sole_offset, hurt_bottom, delta


def bottom_opaque_row(pixels, transparent=None):
    """Ultima linha com pixel fora do conjunto transparente; None se vazio."""
    if transparent is None:
        transparent = {0}
    if not pixels:
        return None
    width = len(pixels[0])
    if not width or any(len(row) != width for row in pixels):
        raise SoleError("pixel matrix must be non-empty and rectangular")
    for y in range(len(pixels) - 1, -1, -1):
        if any(pixel not in transparent for pixel in pixels[y]):
            return y
    return None


def load_sole_row(path: Path, expected_w: int, expected_h: int) -> int:
    try:
        image = png_io.read_indexed_png(str(path))
    except (OSError, png_io.PngError) as error:
        raise SoleError(str(error)) from error
    if (image["w"], image["h"]) != (expected_w, expected_h):
        raise SoleError(
            f"{path}: PNG {image['w']}x{image['h']} != header {expected_w}x{expected_h}"
        )
    transparent = transparent_indices(path.read_bytes())
    row = bottom_opaque_row(image["pixels"], transparent)
    if row is None:
        raise SoleError(f"{path}: PNG has no opaque pixel")
    return row


def transparent_indices(data):
    """tRNS contains alpha VALUES by palette index, not transparent indices.

    png_io validates the PNG; decode just this property rather than treating
    its historical `trns` set of alpha values as indices (255 may be opaque).
    Partial alpha has no meaning in this indexed runtime contract.
    """
    pos = 8
    while pos + 12 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        if kind == b"tRNS":
            alpha = data[pos + 8:pos + 8 + length]
            if any(value not in (0, 255) for value in alpha):
                raise SoleError("partial alpha is outside the indexed runtime contract")
            if alpha and alpha[0] != 0:
                raise SoleError("index 0 must be transparent")
            return {0} | {index for index, value in enumerate(alpha) if value == 0}
        pos += length + 12
    return {0}


def load_frames_manifest(pose_dir: Path):
    path = pose_dir / "frames.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SoleError(f"{path}: {error}") from error
    actions = manifest.get("actions")
    if not isinstance(actions, dict):
        raise SoleError(f"{path}: missing actions object")
    return manifest


def pose_png_path(pose_dir: Path, manifest, action: int, frame: int) -> Path:
    entries = manifest["actions"].get(str(action))
    if not isinstance(entries, list) or frame < 0 or frame >= len(entries):
        raise SoleError(
            f"{pose_dir}/frames.json: action {action} has no frame {frame}"
        )
    entry = entries[frame]
    if not isinstance(entry, dict):
        raise SoleError(f"{pose_dir}/frames.json: action {action} frame {frame} is not an object")
    try:
        group, image = int(entry["group"]), int(entry["image"])
    except (KeyError, TypeError, ValueError) as error:
        raise SoleError(
            f"{pose_dir}/frames.json: action {action} frame {frame} lacks group/image"
        ) from error
    return pose_dir / "sheets" / f"g{group}_{image}.png"


def _character_token(symbol: str) -> str:
    match = re.match(r"P[12]_([A-Za-z0-9]+)_", symbol)
    if not match:
        raise SoleError(f"symbol does not encode fighter prefix: {symbol}")
    return re.sub(r"\d+$", "", match.group(1)).lower()


def _resolve_pose_dir(side: str, symbol: str, explicit, pose_root):
    if side in explicit:
        return Path(explicit[side])
    if pose_root is None:
        raise SoleError(f"no pose dir for {side}; use --pose-dir {side}=DIR or --pose-root")
    token = _character_token(symbol)
    root = Path(pose_root)
    candidates = [
        path for path in root.iterdir()
        if path.is_dir() and path.name.lower() == token
    ]
    if len(candidates) != 1:
        raise SoleError(
            f"{root}: expected exactly one subdir for '{token}', found {len(candidates)}"
        )
    return candidates[0]


def _collect_frames(text: str):
    arrays, aliases = parse_arrays(text)
    sides = {}
    for side in ("p1", "p2"):
        rows = frame_rows(text, f"{side}_frames_all")
        anims = anim_defs(text, f"{side}_anims")
        for index, anim in enumerate(anims):
            if anim["table"] != f"{side}_frames_all":
                raise SoleError(
                    f"{side}_anims[{index}] points at {anim['table']}, "
                    f"expected {side}_frames_all"
                )
            if anim["count"] <= 0 or anim["start"] < 0 or anim["start"] + anim["count"] > len(rows):
                raise SoleError(f"{side}_anims[{index}]: frames outside table")
        by_symbol = {}
        for row in rows:
            base = symbol_base(row["meta"])
            by_symbol.setdefault(base, {"side": side, "row": row, "anims": []})
        for index, anim in enumerate(anims):
            for pos in range(anim["start"], anim["start"] + anim["count"]):
                base = symbol_base(rows[pos]["meta"])
                if index not in by_symbol[base]["anims"]:
                    by_symbol[base]["anims"].append(index)
        sides[side] = {"rows": rows, "anims": anims, "by_symbol": by_symbol}
    return arrays, aliases, sides


def measure_one(side: str, entry, pose_dir: Path, arrays, aliases, manifest):
    row = entry["row"]
    symbol = symbol_base(row["meta"])
    action, frame = symbol_action_frame(symbol)
    axis = axis_y(resolve(row["axis"], arrays, aliases))
    if row["clsn"] == "0":
        hurt = []
    else:
        _hit, hurt = clsn_sections(resolve(row["clsn"], arrays, aliases))
    png = pose_png_path(pose_dir, manifest, action, frame)
    sole_row = load_sole_row(png, row["width"], row["height"])
    sole_offset, hurt_bottom, delta = alignment(axis, sole_row, hurt)
    return {
        "side": side,
        "symbol": symbol,
        "anim": entry["anims"][0] if entry["anims"] else None,
        "anims": list(entry["anims"]),
        "action": action,
        "frame": frame,
        "axis_y": axis,
        "sole_row": sole_row,
        "sole_offset": sole_offset,
        "hurt_bottom": hurt_bottom,
        "hurt_minus_sole": delta,
        "png": str(png),
        "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
        "frames_manifest_sha256": hashlib.sha256((pose_dir / "frames.json").read_bytes()).hexdigest(),
        "width_px": row["width"],
        "height_px": row["height"],
    }


def measure_text(
    text: str,
    *,
    source_label: str,
    pose_dirs=None,
    pose_root=None,
    symbols=None,
    source_sha256: str | None = None,
    require_hurt: bool = False,
):
    arrays, aliases, sides = _collect_frames(text)
    explicit = {side: Path(path) for side, path in (pose_dirs or {}).items()}
    if symbols:
        selected = []
        seen = set()
        for raw in symbols:
            base = symbol_base(raw)
            if base in seen:
                continue
            seen.add(base)
            matches = [
                (side, sides[side]["by_symbol"][base])
                for side in ("p1", "p2") if base in sides[side]["by_symbol"]
            ]
            if len(matches) != 1:
                raise SoleError(f"symbol {base} found on {len(matches)} sides; expected 1")
            selected.append(matches[0])
    else:
        selected = []
        for side in ("p1", "p2"):
            selected.extend((side, entry) for entry in sides[side]["by_symbol"].values())

    records = []
    manifests = {}
    resolved_dirs = {}
    for side, entry in selected:
        symbol = symbol_base(entry["row"]["meta"])
        if side not in resolved_dirs:
            resolved_dirs[side] = _resolve_pose_dir(side, symbol, explicit, pose_root)
        pose_dir = resolved_dirs[side]
        if side not in manifests:
            manifests[side] = load_frames_manifest(pose_dir)
        record = measure_one(side, entry, pose_dir, arrays, aliases, manifests[side])
        if require_hurt and record["hurt_bottom"] is None:
            raise SoleError(f"{record['symbol']}: no hurtbox CLSN2")
        records.append(record)

    if not records:
        raise SoleError("no frames selected")
    deltas = [r["hurt_minus_sole"] for r in records if r["hurt_minus_sole"] is not None]
    max_abs = max((abs(delta) for delta in deltas), default=None)
    worst = None
    if deltas:
        worst = max(
            (r for r in records if r["hurt_minus_sole"] is not None),
            key=lambda r: abs(r["hurt_minus_sole"]),
        )
    result = {
        "schema": SCHEMA,
        "claim_ceiling": "geometry_diagnostic_only",
        "limitation": "last opaque row need not be an anatomical sole; no source-to-ROM pixel identity proof",
        "source_header": source_label,
        "source_header_sha256": source_sha256 or hashlib.sha256(text.encode("ascii")).hexdigest(),
        "method": "sole_offset = int16(AXIS_y) + bottom opaque row; "
                  "hurt_minus_sole = max(CLSN2 y2) - sole_offset",
        "transparent_index": 0,
        "pose_dirs": {side: str(path) for side, path in resolved_dirs.items()},
        "frames": records,
        "summary": {
            "measured": len(records),
            "with_hurt": len(deltas),
            "without_hurt": len(records) - len(deltas),
            "max_abs_delta": max_abs,
            "worst": worst,
            "delta_histogram": dict(sorted(Counter(str(d) for d in deltas).items())),
        },
    }
    return result


SYNTHETIC_HEADER = """\
const unsigned char P1_META[4] = { 0x00, 0x00, 0x00, 0x80 };
const unsigned char P1_CLSN[12] = {
    0x01, 0x80, 0xF2, 0xFF, 0xD2, 0xFF, 0x0A, 0x00, 0x01, 0x00, 0x01, 0x80,
};
const unsigned char P1_AXIS[4] = { 0xF1, 0xFF, 0xCB, 0xFF };
static const Frame p1_frames_all[1] = {
    { 1, 0, P1_RYU_A0F0_META, P1_RYU_A0F0_META, P1_CLSN, P1_AXIS, 32, 56, P1_RYU_A0F0_META, P1_RYU_A0F0_META },
};
static const Anim p1_anims[1] = {
    { 0, 1, 255, p1_frames_all + 0 },
};
static const Frame p2_frames_all[1] = {
    { 1, 0, P2_KEN8_A0F0_META, P2_KEN8_A0F0_META, P2_CLSN, P2_AXIS, 32, 56, P2_KEN8_A0F0_META, P2_KEN8_A0F0_META },
};
static const Anim p2_anims[1] = {
    { 0, 1, 255, p2_frames_all + 0 },
};
"""


def self_check() -> int:
    checks = []
    chunk = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 3) + b"tRNS"
    checks.append(("tRNS mapeia indices, nao valores alpha",
                   transparent_indices(chunk + bytes([0, 0, 255]) + b"\0" * 4) == {0, 1}))
    try:
        transparent_indices(chunk + bytes([0, 127, 255]) + b"\0" * 4)
        partial_rejected = False
    except SoleError:
        partial_rejected = True
    checks.append(("alpha parcial reprova contrato", partial_rejected))
    idle = bytes.fromhex(
        "0180 f2ff d2ff 0a00 0100 fbff cbff 0700 d2ff 0180"
    )
    punch = bytes.fromhex("0180 0200 cdff 1300 0000 0180")
    hit, hurt = clsn_sections(idle)
    checks.append(("CLSN2 do idle tem 2 hurtboxes", hit == [] and len(hurt) == 2))
    checks.append((
        "hurt_bottom do idle = 1",
        alignment(axis_y(bytes.fromhex("f1ffcbff")), 53, hurt)
        == (0, 1, 1),
    ))
    _hit, hurt = clsn_sections(punch)
    checks.append((
        "punch: offset 3, hurt 0, delta -3",
        alignment(-56, 59, hurt) == (3, 0, -3),
    ))
    checks.append((
        "Ken idle: delta -1",
        alignment(-53, 53, [(-11, -52, 8, -1)]) == (0, -1, -1),
    ))
    checks.append((
        "Ken punch: delta -2",
        alignment(-57, 60, [(-7, -51, 10, 1), (-17, -14, -9, 0)]) == (3, 1, -2),
    ))
    try:
        clsn_sections(bytes.fromhex("0180 0200 cdff 1300 0000"))
        missing_sentinel = False
    except SoleError:
        missing_sentinel = True
    checks.append(("CLSN sem sentinela final reprova", missing_sentinel))
    checks.append((
        "linha opaca e a ultima linha nao transparente",
        bottom_opaque_row([[0, 0], [0, 1]], {0}) == 1
        and bottom_opaque_row([[0], [0]], {0}) is None,
    ))
    checks.append((
        "simbolo separa acao e quadro",
        symbol_action_frame("P1_RYU_A260F0") == (260, 0)
        and symbol_action_frame("P2_KEN8_A250F0") == (250, 0),
    ))
    arrays, aliases, sides = _collect_frames(SYNTHETIC_HEADER)
    checks.append((
        "header sintetico resolve P1 e uma anim",
        len(sides["p1"]["rows"]) == 1
        and len(sides["p1"]["anims"]) == 1
        and sides["p1"]["by_symbol"]["P1_RYU_A0F0"]["anims"] == [0],
    ))
    fake_manifest = {"actions": {"260": [{"group": 260, "image": 0}]}}
    checks.append((
        "simbolo -> PNG usa group/image do frames.json",
        pose_png_path(Path("/p"), fake_manifest, 260, 0)
        == Path("/p/sheets/g260_0.png"),
    ))
    for name, ok in checks:
        print("  %-44s %s" % (name, "ok" if ok else "FALHOU"))
    if not all(ok for _name, ok in checks):
        print("[SELF-CHECK FAIL] sole_alignment")
        return 1
    print("[SELF-CHECK OK] audit_sole_alignment")
    return 0


def _parse_pose_dirs(values):
    parsed = {}
    for value in values or []:
        if "=" not in value:
            raise SoleError(f"--pose-dir must be SIDE=DIR, got {value!r}")
        side, path = value.split("=", 1)
        if side not in ("p1", "p2") or not path:
            raise SoleError(f"--pose-dir must be p1=DIR or p2=DIR, got {value!r}")
        parsed[side] = path
    return parsed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--header", help="header do corte com Frame/Anim")
    parser.add_argument("--pose-root", help="raiz com subdirs do lutador (ryu/ken)")
    parser.add_argument("--pose-dir", action="append", default=[],
                        help="mapeamento explicito SIDE=DIR (repetivel)")
    parser.add_argument("--symbol", action="append", default=[],
                        help="quadro exato (ex. P1_RYU_A0F0); default: todos")
    parser.add_argument("--max-abs-delta", type=int,
                        help="reprova se |hurt_minus_sole| exceder N")
    parser.add_argument("--require-hurt", action="store_true",
                        help="reprova quadro sem hurtbox CLSN2")
    parser.add_argument("--out", help="arquivo JSON de saida")
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
        pose_dirs = _parse_pose_dirs(args.pose_dir)
        result = measure_text(
            text,
            source_label=str(header_path),
            pose_dirs=pose_dirs,
            pose_root=args.pose_root,
            symbols=args.symbol or None,
            source_sha256=hashlib.sha256(header_path.read_bytes()).hexdigest(),
            require_hurt=args.require_hurt,
        )
    except (OSError, UnicodeError, SoleError) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 3

    if args.out:
        try:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            write_new_report(out_path, result)
        except OSError as error:
            print(f"[FAIL] {error}", file=sys.stderr)
            return 3

    print(json.dumps(result, indent=2, ensure_ascii=False))
    summary = result["summary"]
    print(
        "[sole] medidos=%d com_hurt=%d max_abs=%s"
        % (summary["measured"], summary["with_hurt"], summary["max_abs_delta"]),
        file=sys.stderr,
    )
    if args.max_abs_delta is not None:
        if summary["max_abs_delta"] is None:
            print("[FAIL] nenhum delta medido", file=sys.stderr)
            return 1
        if summary["max_abs_delta"] > args.max_abs_delta:
            print(
                "[FAIL] |hurt_minus_sole| maximo %d > limite %d"
                % (summary["max_abs_delta"], args.max_abs_delta),
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
