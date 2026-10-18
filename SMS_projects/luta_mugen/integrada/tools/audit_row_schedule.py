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

import render_legal_idle as legal


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


def pose_rows(scene: str, poses: str, blob: bytes, who: str,
              left: bool) -> list[list[tuple[int, int]]]:
    frames = legal._frames(scene, who, actions=["all"])
    descriptors = legal._poses(poses, who)
    out = []
    for po, _ax, ay, _width in frames:
        ptr = descriptors[po][3 if left else 2]
        pieces = legal.pieces(blob[ptr - 0x8000:])
        tops = sorted(set(dy for _dx, dy, _tile in pieces))
        out.append([((128 + ay + dy) & 255,
                     sum(y == dy for _, y, _ in pieces)) for dy in tops])
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
    print("[PASS] audit_row_schedule self-check")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scene", type=Path)
    ap.add_argument("--poses", type=Path)
    ap.add_argument("--meta", type=Path)
    ap.add_argument("--source", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    if not all((a.scene, a.poses, a.meta, a.source, a.out)):
        ap.error("required: --scene --poses --meta --source --out")
    source = a.source.read_text()
    for name, up in (("sc_floor", False), ("sc_ceil", True)):
        m = re.search(rf"{name}\[81\] = \{{(.*?)\}}", source, re.S)
        if not m or [int(x) for x in re.findall(r"\d+", m[1])] != shares(up):
            raise SystemExit(f"[FAIL] source quota table differs: {name}")
    scene, poses, meta = a.scene.read_text(), a.poses.read_text(), a.meta.read_bytes()
    k = pose_rows(scene, poses, meta, "ken", False)
    r = pose_rows(scene, poses, meta, "ryu", True)
    checks = [verify(kr, rr) for kr in k for rr in r]
    result = {
        "schema": "luta_row_schedule_v1", "passed": True,
        "pose_pairs": len(checks), "parities": 2, "window": 8,
        "max_sat": max(c["max_sat"] for c in checks),
        "max_scanline": max(c["max_scanline"] for c in checks),
        "scope": "fixed grounded anchors, all cut poses, right Ken/left Ryu; model only",
        "inputs_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (a.scene, a.poses, a.meta, a.source)},
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
