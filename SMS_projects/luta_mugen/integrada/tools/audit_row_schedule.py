#!/usr/bin/env python3
"""Check proportional row quotas against the integrated character data.

This models the assembly scheduler and rotating omissions, not CPU timing or
the framebuffer. A passing report still requires a new ROM/emulator capture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

PAGE_BYTES = 16384
INDEX_RECORD_BYTES = 11


def shares(up: bool) -> list[int]:
    return [min(8, (8 * k + (k + r - 1 if up else 0)) // (k + r))
            if k + r else 0 for k in range(9) for r in range(9)]


def schedule(ken: list[tuple[int, int]], ryu: list[tuple[int, int]],
             up: bool) -> tuple[list[int], list[int]]:
    a = [min(n, 8) for _, n in ken]
    b = [min(n, 8) for _, n in ryu]
    table = shares(up)
    for i, (ky, kn) in enumerate(ken):
        for j, (ry, rn) in enumerate(ryu):
            # Same modular subtraction as the assembly, including y wrap.
            if ((ky - ry + 15) & 255) < 31 and a[i] + b[j] > 8:
                q = table[min(kn, 8) * 9 + min(rn, 8)]
                a[i] = min(a[i], q)
                b[j] = min(b[j], 8 - q)
    return a, b


def kept(n: int, k: int, rot: int) -> tuple[set[int], int]:
    if not n:
        return set(), 0
    if rot >= n:
        rot = 0
    drop = n - k
    omitted = {(rot + d) % n for d in range(drop)}
    return set(range(n)) - omitted, (rot + drop) % n


def verify(ken: list[tuple[int, int]], ryu: list[tuple[int, int]]) -> dict:
    if any(n < 1 or n > 64 for _, n in ken + ryu):
        raise ValueError("invalid row width")
    if len(ken) > 10 or len(ryu) > 10:
        raise ValueError("more than ten rows in an actor")
    plans = [schedule(ken, ryu, bool(p)) for p in range(2)]
    max_sat = max(sum(a) + sum(b) for a, b in plans)
    peak = 0
    for a, b in plans:
        for y in range(192):
            n = sum(k for (top, _), k in zip(ken + ryu, a + b)
                    if ((y - top) & 255) < 16)
            peak = max(peak, n)
    if max_sat > 64 or peak > 8:
        raise ValueError(f"SAT/line violation: {max_sat}/{peak}")
    for actor, rows in enumerate((ken, ryu)):
        for row, (_, n) in enumerate(rows):
            rot = 0
            masks = []
            for f in range(24):
                mask, rot = kept(n, plans[f & 1][actor][row], rot)
                masks.append(mask)
            for start in range(len(masks) - 7):
                if set.union(*masks[start:start + 8]) != set(range(n)):
                    raise ValueError(f"permanent omission actor/row {actor}/{row}")
    return {"max_sat": max_sat, "max_scanline": peak}


def _macro(text: str, name: str) -> int:
    match = re.search(rf"^#define\s+{re.escape(name)}\s+(\d+)(?:u)?\s*$",
                      text, re.M)
    if not match:
        raise ValueError(f"missing generated pose macro {name}")
    return int(match.group(1))


def _s8(value: int) -> int:
    return value - 256 if value >= 128 else value


def _s16(value: int) -> int:
    return value - 65536 if value >= 32768 else value


def _axis_y(scene: str, symbol: str) -> int:
    seen = set()
    while symbol not in ("0", "NULL"):
        if symbol in seen:
            raise ValueError(f"cyclic generated frame axis alias {symbol}")
        seen.add(symbol)
        match = re.search(
            rf"(?:static\s+)?const\s+unsigned char\s+{re.escape(symbol)}\s*"
            r"\[\s*4\s*\]\s*=\s*\{([^}]+)\}", scene, re.S)
        if match:
            break
        alias = re.search(rf"^#define\s+{re.escape(symbol)}\s+(\w+)\s*$",
                          scene, re.M)
        if not alias:
            raise ValueError(f"missing generated frame axis {symbol}")
        symbol = alias.group(1)
    if symbol in ("0", "NULL"):
        return 0
    values = [int(token, 0) for token in
              re.findall(r"0x[0-9A-Fa-f]+|\b\d+\b", match.group(1))]
    if len(values) != 4:
        raise ValueError(f"malformed generated frame axis {symbol}")
    return _s16(values[2] | (values[3] << 8))


def _frame_descriptors(scene: str, who: str) -> list[tuple[int, int]]:
    match = re.search(
        rf"static const Frame {who}_frames_all\[\w+\] = \{{(.*?)\n\}};",
        scene, re.S)
    if not match:
        raise ValueError(f"missing generated frame table for {who}")
    out = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        fields = [field.strip() for field in line.strip("{} ,").split(",")]
        if len(fields) < 8:
            raise ValueError(f"malformed {who} frame row: {line}")
        pose = int(fields[1], 0)
        out.append((pose, _axis_y(scene, fields[5])))
    return out


def _pose_rows(index: bytes, metadata: bytes, pose_header: str,
               who: str, pose: int, axis_y: int, left: bool) -> list[tuple[int, int]]:
    upper = who.upper()
    count = _macro(pose_header, f"{upper}_POSE_COUNT")
    if not 0 <= pose < count:
        raise ValueError(f"{who} frame pose {pose} outside 0..{count - 1}")
    record_offset = (_macro(pose_header, f"{upper}_POSE_INDEX_OFF") +
                     pose * INDEX_RECORD_BYTES)
    record = index[record_offset:record_offset + INDEX_RECORD_BYTES]
    if len(record) != INDEX_RECORD_BYTES:
        raise ValueError(f"truncated {who} pose-index record {pose}")
    row_offset_pos = 9 if left else 7
    row_offset = record[row_offset_pos] | (record[row_offset_pos + 1] << 8)
    meta_bank = _macro(pose_header, f"{upper}_POSE_META_BANK")
    meta_base_bank = min(_macro(pose_header, "KEN_POSE_META_BANK"),
                         _macro(pose_header, "RYU_POSE_META_BANK"))
    if meta_bank < meta_base_bank:
        raise ValueError(f"{who} metadata bank precedes the metadata image")
    start = (meta_bank - meta_base_bank) * PAGE_BYTES + row_offset
    if start >= len(metadata):
        raise ValueError(f"{who} row table offset exceeds metadata image")
    row_count = metadata[start]
    end = start + 1 + row_count * 2
    if row_count > 10 or end > len(metadata):
        raise ValueError(f"invalid {who} row table for pose {pose}")
    rows = []
    for offset in range(start + 1, end, 2):
        dy, pieces = metadata[offset], metadata[offset + 1]
        rows.append(((128 + axis_y + _s8(dy)) & 255, pieces))
    return rows


def pose_rows(scene: str, poses: str, index: bytes, metadata: bytes,
              who: str, left: bool) -> list[list[tuple[int, int]]]:
    frames = _frame_descriptors(scene, who)
    expected = _macro(poses, f"{who.upper()}_POSE_COUNT")
    if len(frames) != expected:
        raise ValueError(f"{who} frame count {len(frames)} != pose count {expected}")
    out = []
    for pose, axis_y in frames:
        out.append(_pose_rows(index, metadata, poses, who, pose, axis_y, left))
    return out


def self_check() -> None:
    assert schedule([(54, 6)], [(53, 4)], False) == ([4], [4])
    assert schedule([(54, 6)], [(53, 4)], True) == ([5], [3])
    assert schedule([(54, 6)], [(80, 4)], False) == ([6], [4])
    assert schedule([(255, 6)], [(0, 4)], True) == ([5], [3])
    assert kept(6, 4, 5) == ({1, 2, 3, 4}, 1)
    for k in range(1, 9):
        for r in range(1, 9):
            for delta in range(-17, 18):
                verify([(50, k)], [(50 + delta, r)])
    try:
        verify([(40 + 16 * i, 8) for i in range(9)], [])
    except ValueError:
        pass
    else:
        raise AssertionError("SAT overflow accepted")
    scene = """const unsigned char AXIS_BASE[4] = {0x00, 0x00, 0xF0, 0xFF};
#define AXIS_ALIAS AXIS_BASE
static const Frame ken_frames_all[1] = {
    { 4, 0, META, META, 0, AXIS_ALIAS, 8, 16, 0, 0 },
};
static const Frame ryu_frames_all[1] = {
    { 4, 0, META, META, 0, 0, 8, 16, 0, 0 },
};
"""
    pose_header = """#define KEN_POSE_COUNT 1u
#define RYU_POSE_COUNT 1u
#define KEN_POSE_INDEX_OFF 0u
#define RYU_POSE_INDEX_OFF 11u
#define KEN_POSE_META_BANK 2u
#define RYU_POSE_META_BANK 3u
"""
    index = bytearray(INDEX_RECORD_BYTES * 2)
    index[0] = index[INDEX_RECORD_BYTES] = 2
    metadata = bytearray(PAGE_BYTES * 2)
    metadata[:3] = bytes((1, 16, 9))
    metadata[PAGE_BYTES:PAGE_BYTES + 3] = bytes((1, 240, 3))
    assert _frame_descriptors(scene, "ken") == [(0, -16)]
    assert _pose_rows(bytes(index), bytes(metadata), pose_header,
                      "ken", 0, -16, False) == [(128, 9)]
    assert _pose_rows(bytes(index), bytes(metadata), pose_header,
                      "ryu", 0, 0, True) == [(112, 3)]
    print("[PASS] audit_row_schedule self-check")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scene", type=Path)
    ap.add_argument("--poses", type=Path)
    ap.add_argument("--index", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--source", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    if not all((a.scene, a.poses, a.index, a.meta, a.source, a.out)):
        ap.error("required: --scene --poses --index --meta --source --out")
    source = a.source.read_text()
    for name, up in (("sc_floor", False), ("sc_ceil", True)):
        m = re.search(rf"{name}\[81\] = \{{(.*?)\}}", source, re.S)
        if not m or [int(x) for x in re.findall(r"\d+", m[1])] != shares(up):
            raise SystemExit(f"[FAIL] source quota table differs: {name}")
    scene, poses = a.scene.read_text(), a.poses.read_text()
    index, meta = a.index.read_bytes(), a.meta.read_bytes()
    k = pose_rows(scene, poses, index, meta, "ken", False)
    r = pose_rows(scene, poses, index, meta, "ryu", True)
    checks = [verify(kr, rr) for kr in k for rr in r]
    result = {
        "schema": "luta_row_schedule_v1", "passed": True,
        "pose_pairs": len(checks), "parities": 2, "window": 8,
        "max_sat": max(c["max_sat"] for c in checks),
        "max_scanline": max(c["max_scanline"] for c in checks),
        "scope": "fixed grounded anchors, all cut poses, right Ken/left Ryu; model only",
        "inputs_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (a.scene, a.poses, a.index, a.meta, a.source)},
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
