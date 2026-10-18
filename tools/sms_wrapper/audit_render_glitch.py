#!/usr/bin/env python3
"""audit_render_glitch.py -- framebuffer video vs the legal images (L091).

The project renders every image the ROM may legally show (e.g. every pose
pair of the scene) as PNGs in --expected-dir, from the same patterns and
positions the ROM uses. Each captured framebuffer frame is compared with
the best-matching legal image on a foreground mask. Use --background for
bright or detailed stages; it is subtracted from both legal and captured
images so scenery cannot satisfy fighter-coverage checks. Modes:

  strict   zero flicker: every frame must equal a legal image
           (no expected pixel dark, no unexpected pixel lit).
  flicker  multiplexed sprites allowed: no unexpected foreground pixel in any frame
           (residual/corrupt tile, wrong slot), and within every run of
           --window consecutive frames matched to the same legal image the
           union of lit pixels must cover it (nothing omitted for good).

A mismatch within --edge-tolerance px of an edge is ignored (h264 chroma
bleed), so a glitch narrower than that is not detected. The video must be
newer than the ROM; ROM and video SHA-256 are bound into the JSON verdict.
Static simulators (audit_sprite_line_sim.py) do not prove the rendered image.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
from itertools import chain, islice
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np

LUMA_ON = 24


def grow(mask: np.ndarray, radius: int) -> np.ndarray:
    out = mask.copy()
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def best_match(lit: np.ndarray, legal: dict, tol: int, mode: str = "strict",
               grown_legal: dict | None = None) -> dict:
    """strict: minimise missing+extra. flicker: a frame shows a subset of a
    legal image, so minimise extra first (a smaller wrong pose would
    otherwise win on 'missing' and turn correct pixels into 'extra')."""
    grown_lit = grow(lit, tol)
    best = None
    for name, exp in legal.items():
        missing = int((exp & ~grown_lit).sum())
        expanded = grown_legal[name] if grown_legal is not None else grow(exp, tol)
        extra = int((lit & ~expanded).sum())
        key = (missing + extra,) if mode == "strict" else (extra, missing)
        if best is None or key < best["key"]:
            best = {"image": name, "missing": missing, "extra": extra, "key": key}
    best.pop("key")
    return best


def judge(frames: Iterable[np.ndarray], legal: dict, mode: str, window: int,
          tol: int, regions: tuple[tuple[str, tuple[int, int, int, int]], ...] = ()) -> dict:
    """Judge a frame stream with bounded memory; a full match video can be minutes long."""
    if window < 1:
        raise ValueError("window deve ser >= 1")
    grown_legal = {name: grow(mask, tol) for name, mask in legal.items()}
    region_masks = {}
    region_stats = {}
    for label, (x, y, width, height) in regions:
        roi = np.zeros((192, 256), bool)
        roi[y:y + height, x:x + width] = True
        if any(not (mask & roi).any() for mask in legal.values()):
            raise ValueError(f"região '{label}' não contém pixels em toda imagem legal")
        region_masks[label] = roi
        region_stats[label] = {
            "rect_xywh": [x, y, width, height], "coverages": [],
            "expected_pixel_frames": 0, "visible_pixel_frames": 0,
            "max_missing_pixels_per_frame": 0, "max_missing_pct_per_frame": 0.0,
            "zero_coverage_frames": 0, "max_streak_zero_coverage": 0,
            "max_streak_below_25_pct": 0, "max_streak_below_50_pct": 0,
        }
    failures = []
    frames_judged = max_missing = max_extra = 0
    images_seen = set()
    run_name = None
    run_window = deque()
    run_coverage_failed = False
    region_streaks = {name: {0.0: 0, 0.25: 0, 0.50: 0} for name in region_masks}
    for i, frame in enumerate(frames):
        match = best_match(frame, legal, tol, mode, grown_legal)
        frames_judged += 1
        max_missing = max(max_missing, match["missing"])
        max_extra = max(max_extra, match["extra"])
        images_seen.add(match["image"])
        if mode == "strict":
            if match["missing"] or match["extra"]:
                failures.append(match | {"index": i})
        elif match["extra"]:
            failures.append(match | {"index": i, "why": "extra"})

        if mode == "flicker":
            if match["image"] != run_name:
                run_name = match["image"]
                run_window.clear()
                run_coverage_failed = False
            run_window.append(frame)
            if len(run_window) == window:
                if not run_coverage_failed:
                    union = np.logical_or.reduce(tuple(run_window))
                    if (legal[run_name] & ~grow(union, tol)).any():
                        failures.append({"index": i - window + 1, "image": run_name,
                                         "why": "omitted_in_window"})
                        run_coverage_failed = True
                run_window.popleft()
        if region_masks:
            grown_frame = grow(frame, tol)
            for label, roi in region_masks.items():
                expected = legal[match["image"]] & roi
                expected_count = int(expected.sum())
                visible_count = int((expected & grown_frame).sum())
                missing_count = expected_count - visible_count
                coverage = visible_count / expected_count
                stats = region_stats[label]
                stats["coverages"].append(coverage)
                stats["expected_pixel_frames"] += expected_count
                stats["visible_pixel_frames"] += visible_count
                stats["max_missing_pixels_per_frame"] = max(
                    stats["max_missing_pixels_per_frame"], missing_count)
                missing_pct = 100.0 * missing_count / expected_count
                stats["max_missing_pct_per_frame"] = max(
                    stats["max_missing_pct_per_frame"], missing_pct)
                if visible_count == 0:
                    stats["zero_coverage_frames"] += 1
                for threshold, field in ((0.25, "25_pct"), (0.50, "50_pct")):
                    max_key = f"max_streak_below_{field}"
                    if coverage < threshold:
                        region_streaks[label][threshold] += 1
                        stats[max_key] = max(stats[max_key], region_streaks[label][threshold])
                    else:
                        region_streaks[label][threshold] = 0
                if visible_count == 0:
                    region_streaks[label][0.0] += 1
                    stats["max_streak_zero_coverage"] = max(
                        stats["max_streak_zero_coverage"], region_streaks[label][0.0])
                else:
                    region_streaks[label][0.0] = 0
    region_visibility = {}
    for label, stats in region_stats.items():
        coverage = np.asarray(stats.pop("coverages"), dtype=np.float64)
        expected = stats.pop("expected_pixel_frames")
        visible = stats.pop("visible_pixel_frames")
        stats["frames_with_legal_actor"] = int(coverage.size)
        stats["weighted_pixel_duty_pct"] = round(100.0 * visible / expected, 3) if expected else 0.0
        stats["frame_coverage_mean_pct"] = round(100.0 * float(coverage.mean()), 3) if coverage.size else 0.0
        stats["frame_coverage_p05_pct"] = round(100.0 * float(np.quantile(coverage, 0.05)), 3) if coverage.size else 0.0
        stats["frame_coverage_median_pct"] = round(100.0 * float(np.median(coverage)), 3) if coverage.size else 0.0
        stats["frame_coverage_min_pct"] = round(100.0 * float(coverage.min()), 3) if coverage.size else 0.0
        stats["longest_full_absence_frames"] = stats["max_streak_zero_coverage"]
        region_visibility[label] = stats
    return {"frames_judged": frames_judged, "frames_failed": len(failures),
            "first_failures": failures[:10],
            "max_missing": max_missing, "max_extra": max_extra,
            "images_seen": sorted(images_seen), "region_visibility": region_visibility}


def parse_ignore_rect(value: str) -> tuple[int, int, int, int]:
    try:
        rect = tuple(int(part) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("retângulo deve ser x,y,w,h") from exc
    if len(rect) != 4:
        raise argparse.ArgumentTypeError("retângulo deve ser x,y,w,h")
    x, y, w, h = rect
    if x < 0 or y < 0 or w < 1 or h < 1 or x + w > 256 or y + h > 192:
        raise argparse.ArgumentTypeError("retângulo deve caber na canvas 256x192")
    return rect


def parse_region(value: str) -> tuple[str, tuple[int, int, int, int]]:
    label, sep, rect_text = value.partition("=")
    if not sep or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", label):
        raise argparse.ArgumentTypeError("região deve ser nome=x,y,w,h")
    try:
        rect = parse_ignore_rect(rect_text)
    except argparse.ArgumentTypeError as exc:
        raise argparse.ArgumentTypeError("região deve ser nome=x,y,w,h e caber na canvas") from exc
    return label, rect


def apply_ignored_regions(mask: np.ndarray,
                          ignore_rects: tuple[tuple[int, int, int, int], ...]) -> np.ndarray:
    if not ignore_rects:
        return mask
    mask = mask.copy()
    for x, y, w, h in ignore_rects:
        mask[y:y + h, x:x + w] = False
    return mask


def rgb_foreground(rgb: np.ndarray, background: np.ndarray, threshold: int,
                   ignore_rects: tuple[tuple[int, int, int, int], ...] = ()) -> np.ndarray:
    delta = np.max(np.abs(rgb.astype(np.int16) - background.astype(np.int16)), axis=2)
    return apply_ignored_regions(delta > threshold, ignore_rects)


def load_rgb(path: Path, label: str) -> np.ndarray:
    from PIL import Image
    try:
        rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
    except OSError as exc:
        raise ValueError(f"{label} ilegível: {path}: {exc}") from exc
    if rgb.shape != (192, 256, 3):
        raise ValueError(f"{label} fora da canvas 256x192: {path}")
    return rgb


def legacy_luma_mask(img: np.ndarray, source: Path) -> np.ndarray:
    """Keep legacy black-stage inputs safe; bright scenes require --background."""
    mask = img > LUMA_ON
    fraction = float(mask.mean())
    if fraction > 0.20:
        raise ValueError(
            f"{source}: fundo claro ocupa {fraction:.1%}; forneça --background "
            "(placa RGB sem os atores) para julgar cobertura de sprites")
    return mask


def load_legal(directory: Path, background: np.ndarray | None = None,
               threshold: int = 32,
               ignore_rects: tuple[tuple[int, int, int, int], ...] = ()) -> dict:
    from PIL import Image
    legal = {}
    for png in sorted(directory.glob("*.png")):
        if background is None:
            img = np.asarray(Image.open(png).convert("L"))
            if img.shape != (192, 256):
                raise ValueError(f"{png}: imagem legal fora da canvas 256x192")
            mask = legacy_luma_mask(img, png)
            legal[png.stem] = apply_ignored_regions(mask, ignore_rects)
        else:
            img = np.asarray(Image.open(png).convert("RGB"), dtype=np.uint8)
            if img.shape != (192, 256, 3):
                raise ValueError(f"{png}: imagem legal fora da canvas 256x192")
            legal[png.stem] = rgb_foreground(img, background, threshold, ignore_rects)
        if not legal[png.stem].any():
            raise ValueError(f"{png}: a máscara legal ficou vazia após segmentação/ignores")
    if not legal:
        raise ValueError("nenhuma imagem legal em --expected-dir")
    return legal


def iter_video_frames(video: Path, background: np.ndarray | None = None,
                      threshold: int = 32,
                      ignore_rects: tuple[tuple[int, int, int, int], ...] = ()):
    """Decode one framebuffer at a time and yield its sprite mask."""
    rgb_mode = background is not None
    pixel_format = "rgb24" if rgb_mode else "gray"
    frame_bytes = 256 * 192 * (3 if rgb_mode else 1)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "quiet", "-i", str(video), "-f", "rawvideo",
         "-pix_fmt", pixel_format, "-"], stdout=subprocess.PIPE,
         stderr=subprocess.DEVNULL)
    assert proc.stdout is not None
    try:
        while True:
            raw = proc.stdout.read(frame_bytes)
            if not raw:
                break
            while len(raw) < frame_bytes:
                part = proc.stdout.read(frame_bytes - len(raw))
                if not part:
                    raise ValueError("último quadro RGB/grayscale do vídeo está truncado")
                raw += part
            if rgb_mode:
                rgb = np.frombuffer(raw, np.uint8).reshape(192, 256, 3)
                yield rgb_foreground(rgb, background, threshold, ignore_rects)
            else:
                gray = np.frombuffer(raw, np.uint8).reshape(192, 256)
                yield apply_ignored_regions(gray > LUMA_ON, ignore_rects)
        status = proc.wait()
        if status:
            raise ValueError(f"ffmpeg falhou ao decodificar {video} (status {status})")
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        proc.stdout.close()


def find_sustained_content(frames: Iterable[np.ndarray]) -> tuple[int, int, Iterable[np.ndarray]]:
    """Return lead-in, lit pixels before content, and a stream starting at content."""
    iterator = iter(frames)
    window = deque()
    prefix_lit = 0
    seen = 0
    for frame in iterator:
        seen += 1
        window.append(frame)
        if len(window) > SUSTAINED:
            prefix_lit += int(window.popleft().sum())
        if len(window) == SUSTAINED and all(f.any() for f in window):
            lead = seen - SUSTAINED
            return lead, prefix_lit, chain(tuple(window), iterator)
    return seen, prefix_lit + sum((int(f.sum()) for f in window), 0), iter(())


SUSTAINED = 4


def sustained_start(frames: list[np.ndarray]) -> int:
    for i in range(len(frames)):
        if all(f.any() for f in frames[i:i + SUSTAINED]) and len(frames[i:i + SUSTAINED]) == SUSTAINED:
            return i
    return len(frames)


def is_fresh(video: Path, rom: Path) -> bool:
    return video.stat().st_mtime > rom.stat().st_mtime


def self_check() -> int:
    a = np.zeros((192, 256), bool)
    a[40:56, 30:46] = True
    b = np.zeros((192, 256), bool)
    b[40:56, 160:176] = True
    legal = {"pair": a | b, "alone": a.copy()}
    ok = judge([a | b] * 4, legal, "strict", 2, 1)
    assert ok["frames_failed"] == 0
    omitted = (a | b).copy()
    omitted[40:56, 30:38] = False                       # one 8x16 sprite gone
    assert judge([omitted], {"pair": a | b}, "strict", 2, 1)["frames_failed"] == 1
    residue = (a | b).copy()
    residue[100:108, 200:208] = True                    # stray 8x8 tile
    assert judge([residue], legal, "flicker", 2, 1)["frames_failed"] == 1
    half1, half2 = (a | b).copy(), (a | b).copy()
    half1[40:56, 30:38] = False
    half2[40:56, 38:46] = False
    assert judge([half1, half2] * 3, {"pair": a | b}, "flicker", 2, 1)["frames_failed"] == 0
    assert judge([half1] * 6, {"pair": a | b}, "flicker", 2, 1)["frames_failed"] == 1
    # Flicker subset of the big pose must not be matched to a smaller pose.
    assert judge([half1, half2] * 3, legal, "flicker", 2, 1)["frames_failed"] == 0
    # Mixed poses (pixels from two legal images at once) still fail.
    c = np.zeros((192, 256), bool)
    c[100:116, 60:68] = True
    mixed = {"p": a, "q": c}
    assert judge([a | c], mixed, "flicker", 2, 1)["frames_failed"] == 1
    blank = np.zeros((192, 256), bool)
    flash = blank.copy()
    flash[135, 40] = True
    seq = [blank, flash, blank, blank, a | b, a | b, a | b, a | b]
    assert sustained_start(seq) == 4                     # flash is before content
    lead, pre_lit, content = find_sustained_content(iter(seq))
    assert lead == 4 and pre_lit == 1 and len(list(content)) == 4

    # Reproduce the L091 blind spot: a bright stage is present in both the
    # legal screenshot and a capture with both fighters missing. Luma-only
    # masks call the whole stage "lit" and falsely pass window coverage.
    bg = np.zeros((192, 256, 3), np.uint8)
    bg[24:128] = (0, 85, 170)
    bg[128:] = (85, 170, 0)
    actor_rgb = bg.copy()
    actor_rgb[40:56, 30:46] = (255, 0, 0)
    actor_rgb[40:56, 120:128] = (255, 255, 255)
    legal_actor = rgb_foreground(actor_rgb, bg, 32)
    missing_actors = rgb_foreground(bg.copy(), bg, 32)
    assert legal_actor.any() and not missing_actors.any()
    assert judge([missing_actors] * 2, {"pair": legal_actor}, "flicker", 2, 1)["frames_failed"] == 1
    # The changing HUD is excluded while actor coverage remains measurable.
    hud = (0, 0, 256, 24)
    live_with_hud = actor_rgb.copy()
    live_with_hud[4:8, 100:120] = (255, 255, 255)
    expected_mask = rgb_foreground(actor_rgb, bg, 32, (hud,))
    captured_mask = rgb_foreground(live_with_hud, bg, 32, (hud,))
    assert not captured_mask[:24].any()
    assert judge([captured_mask] * 2, {"pair": expected_mask}, "flicker", 2, 1)["frames_failed"] == 0
    region_report = judge(
        [a | b, half1, blank, b], {"pair": a | b}, "strict", 2, 0,
        (("ken", (0, 0, 128, 192)), ("ryu", (128, 0, 128, 192))))["region_visibility"]
    assert region_report["ken"]["frame_coverage_mean_pct"] == 37.5
    assert region_report["ken"]["longest_full_absence_frames"] == 2
    assert region_report["ryu"]["longest_full_absence_frames"] == 1
    # Without an explicit plate, a bright full-screen stage is not accepted
    # as an implicit actor mask.
    assert float((np.max(bg, axis=2) > LUMA_ON).mean()) > 0.20
    try:
        legacy_luma_mask(np.max(bg, axis=2), Path("bright_stage_fixture.png"))
        raise AssertionError("bright background accepted without an RGB plate")
    except ValueError as exc:
        assert "--background" in str(exc)
    dark_fixture = np.zeros((192, 256), np.uint8)
    dark_fixture[40:56, 30:46] = 255
    assert int(legacy_luma_mask(dark_fixture, Path("black_stage_fixture.png")).sum()) == 256
    assert parse_ignore_rect("0,0,256,24") == hud
    try:
        parse_ignore_rect("250,0,20,24")
        raise AssertionError("rectangle outside canvas accepted")
    except argparse.ArgumentTypeError:
        pass
    with tempfile.TemporaryDirectory() as d:
        v, r = Path(d, "v.mp4"), Path(d, "r.sms")
        v.write_bytes(b"v")
        r.write_bytes(b"r")
        os.utime(v, (1, 1))
        assert not is_fresh(v, r)
        os.utime(v, (4e9, 4e9))
        assert is_fresh(v, r)
    print("[SELF-CHECK OK] audit_render_glitch (strict, omissão, resíduo, "
          "cobertura com fundo colorido, HUD ignorado, flicker, pose mista, "
          "omissão permanente e captura stale)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--video", type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--expected-dir", type=Path, help="PNGs 256x192 das imagens legais")
    ap.add_argument("--background", type=Path,
                    help="PNG RGB 256x192 da placa sem atores; obrigatório para fundo claro")
    ap.add_argument("--background-threshold", type=int, default=32,
                    help="diferença máxima por canal para segmentar atores (RGB)")
    ap.add_argument("--ignore-rect", type=parse_ignore_rect, action="append", default=[],
                    metavar="X,Y,W,H", help="região dinâmica excluída; opção repetível")
    ap.add_argument("--region", type=parse_region, action="append", default=[],
                    metavar="NAME=X,Y,W,H", help="mede cobertura/duty cycle por região; repetível")
    ap.add_argument("--mode", choices=("strict", "flicker"), default="strict")
    ap.add_argument("--window", type=int, default=8, help="quadros para cobertura no modo flicker")
    ap.add_argument("--edge-tolerance", type=int, default=1)
    ap.add_argument("--skip", type=int, default=0,
                    help="quadros extras a ignorar apos o primeiro com conteudo")
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if not (a.video and a.rom and a.expected_dir and a.out):
        ap.error("--video, --rom, --expected-dir e --out sao obrigatorios")
    if a.window < 1 or a.skip < 0:
        ap.error("--window deve ser >=1 e --skip deve ser >=0")
    if not 0 <= a.background_threshold <= 255:
        ap.error("--background-threshold deve estar entre 0 e 255")
    try:
        background = load_rgb(a.background, "placa de fundo") if a.background else None
        ignore_rects = tuple(a.ignore_rect)
        regions = tuple(a.region)
        if len({name for name, _rect in regions}) != len(regions):
            ap.error("cada --region precisa de um nome único")
        legal = load_legal(a.expected_dir, background, a.background_threshold, ignore_rects)
        decoded = iter_video_frames(a.video, background, a.background_threshold, ignore_rects)
        # Earlier actor pixels remain reported; the stage and ignored HUD have
        # already been removed from the foreground masks.
        lead, pre_lit, frames = find_sustained_content(decoded)
        result = judge(islice(frames, a.skip, None), legal, a.mode, a.window,
                       a.edge_tolerance, regions)
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    fresh = is_fresh(a.video, a.rom)
    result.update({
        "schema": "render_glitch_v2", "mode": a.mode, "window": a.window,
        "edge_tolerance_px": a.edge_tolerance,
        "mask_mode": "rgb_background_difference" if a.background else "grayscale_luma",
        "background": str(a.background) if a.background else None,
        "background_sha256": hashlib.sha256(a.background.read_bytes()).hexdigest()
                              if a.background else None,
        "background_threshold_per_channel": a.background_threshold if a.background else None,
        "ignore_rectangles_xywh": [list(rect) for rect in ignore_rects],
        "measured_regions": {name: list(rect) for name, rect in regions},
        "rom": str(a.rom), "rom_sha256": hashlib.sha256(a.rom.read_bytes()).hexdigest(),
        "video": str(a.video), "video_sha256": hashlib.sha256(a.video.read_bytes()).hexdigest(),
        "video_newer_than_rom": fresh, "legal_images": len(legal),
        "lead_in_frames_dropped": lead, "pre_content_lit_pixels": pre_lit,
        "extra_skip": a.skip,
        "verdict": "PASS" if fresh and result["frames_judged"] and not result["frames_failed"] else "FAIL",
    })
    a.out.write_text(json.dumps(result, indent=1))
    print(f"[{result['verdict']}] render glitch {a.mode}: {result['frames_failed']}/"
          f"{result['frames_judged']} quadros reprovados, extra max {result['max_extra']}, "
          f"ausência max {result['max_missing']}, "
          f"video mais novo que a ROM={fresh}, pixels acesos antes do conteudo={pre_lit}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
