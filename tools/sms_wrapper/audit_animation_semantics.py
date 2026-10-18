#!/usr/bin/env python3
"""audit_animation_semantics.py — strip reordenado não é animação.

Porta o MÉTODO do validate_strip/validate_motion_semantics do SGDKForge:
hash de frame, nomes de ação e roster exigido. Sem PIL; usa png_io.

Reprova:
  frames_reordered_only
  duplicate_action_under_new_name
  required_state_missing
  pivot_inconsistent
  empty_or_identical_cycle
  geometry_contract_violation (bbox, altura, largura, baseline ou canvas)
  duplicate_frame_in_action (quando unique_frames_required)

Uso:
  audit_animation_semantics.py --manifest <json>
  audit_animation_semantics.py --self-check
Exit: 0 ok | 1 semântica inválida | 3 uso
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from png_io import write_indexed_png, read_indexed_png, PngError  # noqa: E402


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def frame_hash(path):
    img = read_indexed_png(path)
    body = b"".join(img["pixels"])
    return hashlib.sha256(body).hexdigest()


def visible_bbox(path):
    """Mede bbox de pixels opacos; o indice 0 e sempre transparente."""
    img = read_indexed_png(path)
    points = [(x, y) for y, row in enumerate(img["pixels"])
              for x, idx in enumerate(row) if idx != 0 and idx not in img["trns"]]
    if not points:
        return img, None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    box = (min(xs), min(ys), max(xs), max(ys))
    return img, {
        "x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3],
        "width": box[2] - box[0] + 1,
        "height": box[3] - box[1] + 1,
        "baseline_y": box[3],
    }


def audit(manifest, project="."):
    problems = []
    actions = manifest.get("actions") or []
    required = list(manifest.get("required_states") or [])
    present = {a.get("name") for a in actions}
    for state in required:
        if state not in present:
            problems.append(f"required_state_missing: '{state}' ausente do roster")

    signatures = {}  # frozenset(hashes) or tuple -> action name
    for action in actions:
        name = action.get("name") or "?"
        frames = action.get("frames") or []
        if len(frames) < 2 and name not in {"victory", "defeat", "ko"}:
            problems.append(f"empty_or_identical_cycle: '{name}' tem {len(frames)} frame(s)")
        hashes = []
        pivots = []
        for fr in frames:
            rel = fr if isinstance(fr, str) else fr.get("png")
            path = rel if os.path.isabs(rel) else os.path.join(project, rel)
            if not os.path.isfile(path):
                problems.append(f"empty_or_identical_cycle: '{name}' frame ausente ({rel})")
                continue
            hashes.append(frame_hash(path))
            if isinstance(fr, dict) and "pivot" in fr:
                pivots.append(tuple(fr["pivot"]))
        geometry = action.get("geometry_contract")
        if geometry:
            expected_canvas = geometry.get("canvas_px")
            width_range = geometry.get("visible_width_px")
            height_range = geometry.get("visible_height_px")
            expected_baseline = geometry.get("baseline_y_px")
            tolerance = geometry.get("baseline_tolerance_px", 0)
            for fr in frames:
                rel = fr if isinstance(fr, str) else fr.get("png")
                path = rel if os.path.isabs(rel) else os.path.join(project, rel)
                if not os.path.isfile(path):
                    continue
                try:
                    img, box = visible_bbox(path)
                except (OSError, ValueError, PngError) as exc:
                    problems.append(
                        f"geometry_contract_violation: '{name}' frame '{rel}' ilegivel ({exc})")
                    continue
                if expected_canvas and [img["w"], img["h"]] != list(expected_canvas):
                    problems.append(
                        f"geometry_contract_violation: '{name}' frame '{rel}' canvas="
                        f"{img['w']}x{img['h']} esperado={expected_canvas}")
                if box is None:
                    problems.append(
                        f"geometry_contract_violation: '{name}' frame '{rel}' sem pixels visiveis")
                    continue
                if width_range and not width_range[0] <= box["width"] <= width_range[1]:
                    problems.append(
                        f"geometry_contract_violation: '{name}' frame '{rel}' largura="
                        f"{box['width']} fora de {width_range}")
                if height_range and not height_range[0] <= box["height"] <= height_range[1]:
                    problems.append(
                        f"geometry_contract_violation: '{name}' frame '{rel}' altura="
                        f"{box['height']} fora de {height_range}")
                if expected_baseline is not None and abs(box["baseline_y"] - expected_baseline) > tolerance:
                    problems.append(
                        f"geometry_contract_violation: '{name}' frame '{rel}' baseline="
                        f"{box['baseline_y']} esperado={expected_baseline} ±{tolerance}")
        if hashes and len(set(hashes)) == 1 and len(hashes) > 1:
            problems.append(f"empty_or_identical_cycle: '{name}' é o mesmo frame repetido")
        if action.get("unique_frames_required") and len(set(hashes)) != len(hashes):
            duplicate_hashes = {h for h in hashes if hashes.count(h) > 1}
            duplicate_indexes = [i for i, h in enumerate(hashes) if h in duplicate_hashes]
            problems.append(
                f"duplicate_frame_in_action: '{name}' indices={duplicate_indexes}; "
                "unique_frames_required=true")
        sig_set = frozenset(hashes)
        sig_tuple = tuple(hashes)
        for other_name, (other_set, other_tuple) in signatures.items():
            if sig_tuple == other_tuple:
                problems.append(
                    f"duplicate_action_under_new_name: '{name}' == '{other_name}' (mesma ordem)"
                )
            elif sig_set == other_set and sig_tuple != other_tuple:
                problems.append(
                    f"frames_reordered_only: '{name}' é permutação de '{other_name}'"
                )
        signatures[name] = (sig_set, sig_tuple)
        if pivots and len(set(pivots)) > 1:
            problems.append(f"pivot_inconsistent: '{name}' pivots={pivots}")
    return problems


def _frame(path, pattern):
    pal = [(0, 0, 0), (255, 255, 255), (0, 0, 255)] + [(0, 0, 0)] * 13
    rows = [bytes([(pattern(x, y)) for x in range(16)]) for y in range(16)]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_indexed_png(path, 16, 16, pal, rows)


def _self_check():
    d = tempfile.mkdtemp(prefix="smsanim_")
    try:
        a1 = os.path.join(d, "idle_0.png")
        a2 = os.path.join(d, "idle_1.png")
        b1 = os.path.join(d, "walk_0.png")
        b2 = os.path.join(d, "walk_1.png")
        g1 = os.path.join(d, "geometry_0.png")
        g2 = os.path.join(d, "geometry_1.png")
        _frame(a1, lambda x, y: 1 if x < 8 else 0)
        _frame(a2, lambda x, y: 1 if y < 8 else 0)
        _frame(b1, lambda x, y: 2 if x > 8 else 1)
        _frame(b2, lambda x, y: 2 if y > 8 else 1)
        _frame(g1, lambda x, y: 1 if 4 <= x < 12 and 4 <= y < 16 else 0)
        _frame(g2, lambda x, y: 2 if 4 <= x < 12 and 4 <= y < 16 and x < 8 else
                                (1 if 4 <= x < 12 and 4 <= y < 16 else 0))
        _frame(os.path.join(d, "geometry_bad.png"),
               lambda x, y: 1 if 4 <= x < 12 and 4 <= y < 15 else 0)
        good = {
            "required_states": ["idle", "walk"],
            "actions": [
                {"name": "idle", "frames": [a1, a2]},
                {"name": "walk", "frames": [b1, b2],
                 "pivot": None},
            ],
        }
        # pivots via dict frames
        good["actions"][1]["frames"] = [
            {"png": b1, "pivot": [8, 16]},
            {"png": b2, "pivot": [8, 16]},
        ]
        assert not audit(good, d), audit(good, d)

        geometry = {
            "actions": [{"name": "idle", "unique_frames_required": True,
                         "frames": [g1, g2],
                         "geometry_contract": {
                             "canvas_px": [16, 16],
                             "visible_width_px": [8, 8],
                             "visible_height_px": [12, 12],
                             "baseline_y_px": 15,
                             "baseline_tolerance_px": 0,
                         }}]
        }
        assert not audit(geometry, d), audit(geometry, d)
        geometry["actions"][0]["frames"] = [g1, os.path.join(d, "geometry_bad.png")]
        p = audit(geometry, d)
        assert any("geometry_contract_violation" in x and "baseline" in x for x in p), p
        assert any("geometry_contract_violation" in x and "altura" in x for x in p), p
        geometry["actions"][0]["frames"] = [g1, g1]
        p = audit(geometry, d)
        assert any("duplicate_frame_in_action" in x for x in p), p

        missing = {"required_states": ["idle", "heavy"], "actions": good["actions"]}
        p = audit(missing, d)
        assert any("required_state_missing" in x for x in p), p

        reorder = {
            "actions": [
                {"name": "idle", "frames": [a1, a2]},
                {"name": "idle_alt", "frames": [a2, a1]},
            ]
        }
        p = audit(reorder, d)
        assert any("frames_reordered_only" in x for x in p), p

        clone = {
            "actions": [
                {"name": "light", "frames": [b1, b2]},
                {"name": "medium", "frames": [b1, b2]},
            ]
        }
        p = audit(clone, d)
        assert any("duplicate_action_under_new_name" in x for x in p), p

        same = {"actions": [{"name": "walk", "frames": [a1, a1]}]}
        p = audit(same, d)
        assert any("empty_or_identical_cycle" in x for x in p), p

        piv = {"actions": [{"name": "walk", "frames": [
            {"png": b1, "pivot": [8, 16]},
            {"png": b2, "pivot": [4, 10]},
        ]}]}
        p = audit(piv, d)
        assert any("pivot_inconsistent" in x for x in p), p
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] animation_semantics "
          "(roster, permutação, clone, ciclo idêntico, pivot, bbox, baseline, quadros únicos)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest")
    ap.add_argument("--project", default=".")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return _self_check()
    if not args.manifest:
        print("uso: audit_animation_semantics.py --manifest <json> | --self-check",
              file=sys.stderr)
        return 3
    man = json.load(open(args.manifest, encoding="utf-8"))
    problems = audit(man, args.project)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print("[OK] animation_semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
