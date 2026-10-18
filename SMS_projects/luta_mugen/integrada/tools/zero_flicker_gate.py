#!/usr/bin/env python3
"""Zero-flicker / zero-glitch gate for the idle pair on a black stage.

Every captured framebuffer frame must be explained by one expected image:
Ken pose i united with Ryu pose j, rasterised from the exact streamed
patterns at the ROM's positions (line_lower_bound / gen_bg_fighter logic).
A frame fails when expected visible pixels are missing (omitted/flickered
sprite, missing BG tile) or unexpected pixels are lit (residual or corrupt
tile). The video must be newer than the ROM file and the ROM SHA is bound
into the verdict, so a stale capture cannot pass.

Visible = palette colour != black; pixels painted with a black palette
entry are invisible on the black stage and are not required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import gen_bg_fighter as bgf  # noqa: E402
import gen_render_bank as rb  # noqa: E402
import line_lower_bound as llb  # noqa: E402

LUMA_ON = 24           # capture pixel counted as lit
MAX_MISSING = 0        # expected visible pixels allowed to be dark
MAX_EXTRA = 0          # unexpected lit pixels allowed
EDGE_TOLERANCE = 1     # h264 chroma bleed: ignore mismatches within 1 px of an edge


def expected_masks(plans: dict, header: Path, banks: bytes, palette: list[int]) -> dict:
    actors = rb._actors(plans, header)
    masks = {}
    for key in ("ken_p1", "ryu_p2"):
        states = llb.actor_slot_states(plans[key], banks)
        masks[key] = []
        for f in range(len(actors[key])):
            m = np.zeros((192, 256), bool)
            for (x, y), v in bgf.pose_colors(actors[key][f], states[f]).items():
                if palette[v] and 0 <= x < 256 and 0 <= y < 192:
                    m[y, x] = True
            masks[key].append(m)
    return {(i, j): k | r for i, k in enumerate(masks["ken_p1"])
            for j, r in enumerate(masks["ryu_p2"])}


def _grow(m: np.ndarray, r: int) -> np.ndarray:
    g = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            g |= np.roll(np.roll(m, dy, 0), dx, 1)
    return g


def judge_frame(lit: np.ndarray, expected: dict) -> dict:
    best = None
    for key, exp in expected.items():
        missing = exp & ~_grow(lit, EDGE_TOLERANCE)
        extra = lit & ~_grow(exp, EDGE_TOLERANCE)
        score = int(missing.sum()) + int(extra.sum())
        if best is None or score < best["score"]:
            best = {"pair": key, "score": score, "missing": int(missing.sum()),
                    "extra": int(extra.sum())}
    best["ok"] = best["missing"] <= MAX_MISSING and best["extra"] <= MAX_EXTRA
    return best


def frames_from_video(video: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", str(video), "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 192, 256)


def is_fresh(video: Path, rom: Path) -> bool:
    return video.stat().st_mtime > rom.stat().st_mtime


def run(video: Path, rom: Path, expected: dict, skip: int) -> dict:
    fresh = is_fresh(video, rom)
    frames = frames_from_video(video)
    verdicts = [judge_frame(f > LUMA_ON, expected) for f in frames[skip:]]
    bad = [dict(v, index=i + skip) for i, v in enumerate(verdicts) if not v["ok"]]
    pairs_seen = sorted({v["pair"] for v in verdicts})
    return {"schema": "zero_flicker_gate_v1",
            "rom": str(rom), "rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
            "video": str(video), "video_sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
            "video_newer_than_rom": fresh, "frames_judged": len(verdicts),
            "frames_failed": len(bad), "first_failures": bad[:10],
            "pairs_seen": [list(p) for p in pairs_seen],
            "max_missing": max(v["missing"] for v in verdicts),
            "max_extra": max(v["extra"] for v in verdicts),
            "verdict": "PASS" if fresh and verdicts and not bad else "FAIL"}


def self_check() -> None:
    a = np.zeros((192, 256), bool)
    a[50:66, 40:56] = True
    b = np.zeros((192, 256), bool)
    b[50:66, 100:108] = True
    expected = {(0, 0): a | b, (1, 0): a}
    assert judge_frame(a | b, expected)["ok"]                      # exact frame
    omitted = (a | b).copy()
    omitted[50:66, 40:48] = False                                  # one 8x16 sprite gone
    assert not judge_frame(omitted, {(0, 0): a | b})["ok"]
    residue = (a | b).copy()
    residue[120:128, 200:208] = True                               # stray 8x8 tile
    assert not judge_frame(residue, expected)["ok"]
    assert judge_frame(a, expected)["pair"] == (1, 0)              # other legal pair
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        v, r = Path(d, "v.mp4"), Path(d, "r.sms")
        v.write_bytes(b"x")
        r.write_bytes(b"y")
        os.utime(v, (1, 1))                                        # stale capture
        assert not is_fresh(v, r)
        os.utime(v, (4e9, 4e9))
        assert is_fresh(v, r)
    print("[PASS] zero_flicker_gate self-check (exato, omissao, residuo, par alternativo, captura stale)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--report", type=Path)
    ap.add_argument("--source-header", type=Path)
    ap.add_argument("--banks", type=Path)
    ap.add_argument("--palette-header", type=Path, help="header com versus_sprite_palette usado pela ROM")
    ap.add_argument("--skip", type=int, default=2, help="primeiros quadros (boot)")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    import re
    text = a.palette_header.read_text()
    pal = [int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]+", re.search(
        r"versus_sprite_palette\[16\] = \{(.*?)\};", text, re.S).group(1))]
    plans = json.loads(a.report.read_text())["selected_facing_pool"]["idle_cache_plan"]
    result = run(a.video, a.rom, expected_masks(plans, a.source_header, a.banks.read_bytes(), pal), a.skip)
    a.out.write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in ("verdict", "frames_judged", "frames_failed",
                                              "max_missing", "max_extra", "video_newer_than_rom")}))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
