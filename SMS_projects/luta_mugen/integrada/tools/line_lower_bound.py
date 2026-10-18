#!/usr/bin/env python3
"""Lower bound of hardware sprites per scanline for the idle pair.

For every scanline, the fewest 8-px-wide sprites that can cover all opaque
pixels of both fighters is the minimum cover of those x positions by
intervals of width 8 (greedy from the left is optimal). No metasprite
re-layout, dedup, culling or cache can go below it; only fewer opaque pixels
per line (art/scale) or moving pixels off the sprite layer can. The SMS VDP
shows at most 8 sprites per line, so any line above 8 proves sprite-only
zero-flicker impossible for that pose pair at that spacing.

Pixels come from the exact 4bpp pattern pairs streamed to VRAM (bank blob)
placed where the ROM places them (gen_idle_cache_header._pose_sprites).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gen_idle_cache_header as gen  # noqa: E402
import gen_render_bank as rb  # noqa: E402

FIRST_BANK = 2
SPRITE_W = 8
LINE_LIMIT = 8


def decode_pair(pair: bytes) -> list[list[int]]:
    """64 B = two stacked SMS 8x8 4bpp planar tiles -> 16 rows of 8 indices."""
    rows = []
    for row in range(16):
        b = pair[row * 4:row * 4 + 4]
        rows.append([sum(((b[p] >> (7 - x)) & 1) << p for p in range(4)) for x in range(8)])
    return rows


def min_cover(xs: list[int]) -> int:
    count, reach = 0, -1
    for x in sorted(set(xs)):
        if x > reach:
            count += 1
            reach = x + SPRITE_W - 1
    return count


def pose_pixels(sprites: list, slots: dict[int, bytes]) -> set[tuple[int, int]]:
    px = set()
    for x, y, _prio, tile, _owner, _sid in sprites:
        rows = decode_pair(slots[tile // 2])
        for dy, row in enumerate(rows):
            for dx, color in enumerate(row):
                if color:
                    px.add((x + dx, y + dy))
    return px


def actor_slot_states(plan: dict, banks: bytes) -> list[dict[int, bytes]]:
    def pair(bank: int, off: int) -> bytes:
        base = (bank - FIRST_BANK) * 16384 + off
        return banks[base:base + 64]
    slots = {l["target_pair_slot"]: pair(l["source_bank"], l["source_off"])
             for l in plan["initial_pose"]["pattern_loads"]}
    states = [dict(slots)]
    for row in sorted(plan["transitions"], key=lambda r: r["from_frame"]):
        for l in row["uploads"]:
            slots[l["target_pair_slot"]] = pair(l["source_bank"], l["source_off"])
        if row["to_frame"]:
            states.append(dict(slots))
    return states


def analyse(plans: dict, header: Path, banks: bytes) -> dict:
    actors = rb._actors(plans, header)
    states = {k: actor_slot_states(plans[k], banks) for k in ("ken_p1", "ryu_p2")}
    pix = {k: [pose_pixels(actors[k][f], states[k][f]) for f in range(len(actors[k]))]
           for k in actors}
    per_actor = {}
    for k in pix:
        per_actor[k] = []
        for f, p in enumerate(pix[k]):
            ys = [y for _, y in p]
            per_line = [min_cover([x for x, y in p if y == line]) for line in range(192)]
            per_actor[k].append({"frame": f, "opaque_h": max(ys) - min(ys) + 1,
                                 "opaque_w": max(x for x, _ in p) - min(x for x, _ in p) + 1,
                                 "sat_now": len(actors[k][f]),
                                 "line_lower_bound_peak": max(per_line)})
    pairs = []
    for kf, kp in enumerate(pix["ken_p1"]):
        for rf, rp in enumerate(pix["ryu_p2"]):
            union = kp | rp
            per_line = [min_cover([x for x, y in union if y == line]) for line in range(192)]
            pairs.append({"ken": kf, "ryu": rf, "peak": max(per_line),
                          "lines_over_8": sum(1 for c in per_line if c > LINE_LIMIT)})
    return {"per_actor": per_actor, "pairs": pairs,
            "pair_peak": max(p["peak"] for p in pairs),
            "sprite_only_zero_flicker_possible": all(p["peak"] <= LINE_LIMIT for p in pairs)}


def self_check() -> None:
    assert min_cover([0, 7]) == 1 and min_cover([0, 8]) == 2 and min_cover([]) == 0
    assert min_cover(list(range(0, 51))) == 7  # 51 px contiguous -> 7 sprites
    solid = bytes([0xFF, 0, 0, 0]) * 16
    rows = decode_pair(solid)
    assert rows[0] == [1] * 8 and len(rows) == 16
    blank = decode_pair(bytes(64))
    assert all(c == 0 for r in blank for c in r)
    assert pose_pixels([(10, 20, 0, 4, 0, 0)], {2: solid}) == {(10 + x, 20 + y) for x in range(8) for y in range(16)}
    print("[PASS] line_lower_bound self-check")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path)
    ap.add_argument("--source-header", type=Path)
    ap.add_argument("--banks", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    banks = a.banks.read_bytes()
    plans = json.loads(a.report.read_text())["selected_facing_pool"]["idle_cache_plan"]
    result = analyse(plans, a.source_header, banks)
    result["inputs_sha256"] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (a.report, a.source_header, a.banks)}
    a.out.write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in ("pair_peak", "sprite_only_zero_flicker_possible")}))
    for k, rows in result["per_actor"].items():
        print(k, [(r["opaque_w"], r["opaque_h"], r["sat_now"], r["line_lower_bound_peak"]) for r in rows])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
