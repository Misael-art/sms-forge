#!/usr/bin/env python3
"""Measure roster sprite scale and record per-axis human review decisions.

This audit measures occupied width/height and declared cross-character size
relations. It does not judge pose, chibi appearance, identity, line quality,
palette semantics, or whether a sprite matches its concept; those remain a
required human review recorded in the profile.

Usage:
  audit_roster_harmony.py --manifest <roster_profile.json>
  audit_roster_harmony.py --manifest <roster_profile.json> --json <report.json>
  audit_roster_harmony.py --self-check
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
import textwrap

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - environment diagnostic
    Image = None
    PIL_ERROR = str(exc)
else:
    PIL_ERROR = None


def _bbox_for_frame(path, cell, columns, frame_index, transparent_index=0):
    if Image is None:
        raise RuntimeError(f"Pillow unavailable: {PIL_ERROR}")
    im = Image.open(path)
    cw, ch = cell
    col, row = frame_index % columns, frame_index // columns
    left, top = col * cw, row * ch
    if left + cw > im.width or top + ch > im.height:
        raise ValueError("frame cell exceeds image dimensions")
    frame = im.crop((left, top, left + cw, top + ch))
    if im.mode == "P" and "transparency" not in im.info:
        mask = frame.point(lambda px: 0 if px == transparent_index else 255)
    else:
        mask = frame.convert("RGBA").getchannel("A")
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError("selected frame is fully transparent")
    x0, y0, x1, y1 = bbox
    return {"bbox_xyxy": [x0, y0, x1, y1],
            "width_px": x1 - x0, "height_px": y1 - y0,
            "baseline_y_px": y1}


def audit(manifest, project_root):
    problems, rows, by_key = [], [], {}
    characters = manifest.get("characters") or []
    if not characters:
        return {"status": "invalid_profile", "issues": ["characters is empty"],
                "characters": []}

    for spec in characters:
        key = spec.get("key")
        if not key or key in by_key:
            problems.append(f"missing or duplicate character key: {key!r}")
            continue
        path = os.path.join(project_root, spec.get("sprite_path", ""))
        item = {"key": key, "name": spec.get("name", key),
                "sprite_path": spec.get("sprite_path"), "issues": []}
        if not os.path.isfile(path):
            item["issues"].append("sprite file missing")
            rows.append(item)
            by_key[key] = item
            continue
        actual_sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        item["sha256"] = actual_sha
        expected_sha = spec.get("sprite_sha256")
        if expected_sha and actual_sha != expected_sha:
            item["issues"].append("source SHA-256 differs from profile")
        try:
            measured = _bbox_for_frame(
                path, spec["cell_size_px"], int(spec["columns"]),
                int(spec.get("frame_index", 0)),
                int(spec.get("transparent_index", 0)))
        except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
            item["issues"].append(f"cannot measure frame: {exc}")
            rows.append(item)
            by_key[key] = item
            continue
        item["measured"] = measured
        width_range = spec.get("target_width_px")
        height_range = spec.get("target_height_px")
        if not width_range or not height_range:
            item["issues"].append("target width/height range missing")
        else:
            if not width_range[0] <= measured["width_px"] <= width_range[1]:
                item["issues"].append(
                    f"width {measured['width_px']} outside {width_range}")
            if not height_range[0] <= measured["height_px"] <= height_range[1]:
                item["issues"].append(
                    f"height {measured['height_px']} outside {height_range}")
        review = spec.get("visual_review") or {}
        axes = manifest.get("required_visual_review_axes") or []
        failed = [axis for axis in axes if review.get(axis) == "fail"]
        pending = [axis for axis in axes if review.get(axis) not in ("pass", "fail")]
        item["visual_review_failed"] = failed
        item["visual_review_pending"] = pending
        item["visual_review_missing_or_failed"] = failed + pending
        if item["issues"]:
            item["numeric_status"] = "fail"
        else:
            item["numeric_status"] = "pass"
        rows.append(item)
        by_key[key] = item

    relation_results = []
    for rule in manifest.get("relative_constraints") or []:
        left, right = by_key.get(rule.get("left")), by_key.get(rule.get("right"))
        result = {"rule": rule, "status": "unmeasured"}
        if left and right and left.get("measured") and right.get("measured"):
            relation = rule.get("relation")
            limit = rule.get("max_difference_px", 0)
            if relation in ("height_lte", "height_near"):
                left_value = left["measured"]["height_px"]
                right_value = right["measured"]["height_px"]
                value_key = "height"
            elif relation == "width_near":
                left_value = left["measured"]["width_px"]
                right_value = right["measured"]["width_px"]
                value_key = "width"
            else:
                left_value = right_value = None
                value_key = None
            passed = ((left_value <= right_value) if relation == "height_lte" else
                      (abs(left_value - right_value) <= limit)
                      if relation in ("height_near", "width_near") else False)
            result["status"] = "pass" if passed else "fail"
            if value_key:
                result[f"left_{value_key}_px"] = left_value
                result[f"right_{value_key}_px"] = right_value
            if not passed:
                problems.append(f"relative constraint failed: {rule.get('id')}")
        else:
            problems.append(f"relative constraint lacks measured sources: {rule.get('id')}")
        relation_results.append(result)

    numeric_failures = [r["key"] for r in rows if r.get("numeric_status") == "fail"]
    human_failed = [r["key"] for r in rows if r.get("visual_review_failed")]
    human_pending = [r["key"] for r in rows if r.get("visual_review_pending")]
    if problems or numeric_failures:
        status = "needs_revision"
    elif human_failed:
        status = "owner_visual_revision_required"
    elif human_pending:
        status = "human_review_required"
    else:
        status = "ready_for_owner_review"
    return {
        "schema": "smsforge.roster_harmony_report.v1",
        "project": manifest.get("project"),
        "profile_status": manifest.get("status"),
        "status": status,
        "scope_note": "Measures declared bounds/relations and records reviewer-supplied visual pass/fail/pending; it does not automatically judge anatomy, cutout, palette harmony, finish, or ROM quality.",
        "issues": problems,
        "characters": rows,
        "relative_constraints": relation_results,
        "visual_review_failed": human_failed,
        "visual_review_pending": human_pending,
        "human_review_required": human_pending
    }


def _font(size, bold=False):
    if Image is None:
        raise RuntimeError(f"Pillow unavailable: {PIL_ERROR}")
    from PIL import ImageFont
    candidates = (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                  "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
                 if bold else
                 ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                  "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"])
    for path in candidates:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def render_board(report, manifest, project_root, output_path, scale=4):
    """Render a review-only board; source pixels are only cropped and enlarged."""
    if Image is None:
        raise RuntimeError(f"Pillow unavailable: {PIL_ERROR}")
    from PIL import ImageDraw
    specs = {row["key"]: row for row in manifest.get("characters", [])}
    result_rows = {row["key"]: row for row in report.get("characters", [])}
    order = list(specs)
    card_w, gap, margin = 340, 12, 16
    width = margin * 2 + len(order) * card_w + (len(order) - 1) * gap
    height = 660
    board = Image.new("RGB", (width, height), "#252a30")
    draw = ImageDraw.Draw(board)
    title_font, sub_font = _font(24, True), _font(12)
    name_font, body_font, tiny_font = _font(16, True), _font(12), _font(10)
    draw.text((margin, 12), "MASTER OF FIGHTERS / ROSTER SPRITE ALIGNMENT AUDIT",
              font=title_font, fill="#f2f4f6")
    owner_review = manifest.get("owner_review") or {}
    if owner_review.get("status") == "rejected_for_aesthetic_revision":
        subtitle = "OWNER REJECTED AESTHETIC · revise morphology / cutout / color clusters"
        badge = "SOURCE ONLY · NOT APPROVED"
        subtitle_color = "#ff8b78"
    else:
        subtitle = f"PRELIMINARY SOURCE FRAMES · native pixels at {scale}x nearest-neighbor · common baseline"
        badge = "NOT AN APPROVED SPRITE DELIVERY"
        subtitle_color = "#b9c1ca"
    draw.text((margin, 43), subtitle, font=sub_font, fill=subtitle_color)
    draw.text((width - 325, 23), badge, font=body_font, fill="#f2a45b")

    for i, key in enumerate(order):
        spec, row = specs[key], result_rows.get(key, {})
        x = margin + i * (card_w + gap)
        y0, y1 = 72, 620
        failures = row.get("issues") or []
        review = row.get("visual_review_missing_or_failed") or []
        if failures or any(v != "pass" for v in (spec.get("visual_review") or {}).values()):
            accent, status = "#e1796f", "REVISE / REVIEW"
        else:
            accent, status = "#72c39a", "SCALE REFERENCE"
        draw.rounded_rectangle((x, y0, x + card_w, y1), radius=9,
                               fill="#343a41", outline="#59616a", width=1)
        draw.text((x + 12, y0 + 10), spec.get("name", key),
                  font=name_font, fill="#eef1f4")
        draw.text((x + 12, y0 + 33), spec.get("game", ""),
                  font=tiny_font, fill="#b5bdc6")
        draw.text((x + 12, y0 + 53), status,
                  font=tiny_font, fill=accent)

        path = os.path.join(project_root, spec["sprite_path"])
        try:
            im = Image.open(path)
            cw, ch = spec["cell_size_px"]
            idx = int(spec.get("frame_index", 0))
            col, row_idx = idx % int(spec["columns"]), idx // int(spec["columns"])
            source_cell = im.crop((col * cw, row_idx * ch, (col + 1) * cw,
                                   (row_idx + 1) * ch))
            cell = source_cell.convert("RGBA")
            if im.mode == "P" and "transparency" not in im.info:
                alpha = source_cell.point(
                    lambda px: 0 if px == int(spec.get("transparent_index", 0)) else 255)
                cell.putalpha(alpha)
            alpha = cell.getchannel("A")
            bbox = alpha.getbbox()
            if bbox:
                sprite = cell.crop(bbox)
                sprite = sprite.resize((sprite.width * scale, sprite.height * scale),
                                       Image.Resampling.NEAREST)
                baseline = y0 + 402
                paste_x = x + (card_w - sprite.width) // 2
                board.paste(sprite, (paste_x, baseline - sprite.height), sprite)
                draw.line((x + 12, baseline, x + card_w - 12, baseline),
                          fill="#7d858e", width=1)
        except (OSError, KeyError, TypeError, ValueError):
            draw.text((x + 18, y0 + 190), "SOURCE UNAVAILABLE", font=body_font,
                      fill="#ee7770")

        measured = row.get("measured") or {}
        current = f"CURRENT {measured.get('width_px', '?')}×{measured.get('height_px', '?')} px"
        wr, hr = spec.get("target_width_px", ["?", "?"]), spec.get("target_height_px", ["?", "?"])
        target = f"TARGET {wr[0]}–{wr[1]} W × {hr[0]}–{hr[1]} H px"
        draw.text((x + 12, y0 + 414), current, font=body_font, fill="#f0f2f4")
        draw.text((x + 12, y0 + 434), target, font=tiny_font, fill="#bdc6cf")
        notes = textwrap.wrap(spec.get("short_observation", ""), width=34)[:3]
        for n, line in enumerate(notes):
            draw.text((x + 12, y0 + 454 + n * 15), line, font=tiny_font,
                      fill="#e0c9aa")

    draw.text((margin, 636),
              "Target bands are working values from doc/roster_harmony_contract_v1.json. "
              "The audit measures bounds/relations; morphology and style require human review.",
              font=tiny_font, fill="#b9c1ca")
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    board.save(output_path)


def self_check():
    if Image is None:
        raise RuntimeError(f"Pillow unavailable: {PIL_ERROR}")
    with tempfile.TemporaryDirectory(prefix="roster_harmony_") as root:
        for name, box in (("a.png", (2, 3, 8, 15)), ("b.png", (3, 4, 10, 14))):
            im = Image.new("P", (16, 16), 0)
            im.putpalette([0, 0, 0, 255, 0, 0] + [0, 0, 0] * 254)
            im.info["transparency"] = 0
            for y in range(box[1], box[3]):
                for x in range(box[0], box[2]):
                    im.putpixel((x, y), 1)
            im.save(os.path.join(root, name), transparency=0)
        profile = {
            "project": "self_check",
            "status": "fixture",
            "required_visual_review_axes": ["identity", "morphology"],
            "characters": [
                {"key": "a", "name": "A", "sprite_path": "a.png",
                 "sprite_sha256": hashlib.sha256(open(os.path.join(root, "a.png"), "rb").read()).hexdigest(),
                 "cell_size_px": [16, 16], "columns": 1, "frame_index": 0,
                 "target_width_px": [6, 6], "target_height_px": [12, 12],
                 "visual_review": {"identity": "pass", "morphology": "pass"}},
                {"key": "b", "name": "B", "sprite_path": "b.png",
                 "sprite_sha256": hashlib.sha256(open(os.path.join(root, "b.png"), "rb").read()).hexdigest(),
                 "cell_size_px": [16, 16], "columns": 1, "frame_index": 0,
                 "target_width_px": [7, 7], "target_height_px": [10, 10],
                 "visual_review": {"identity": "pass", "morphology": "pass"}}
            ],
            "relative_constraints": [
                {"id": "b_not_taller_than_a", "left": "b", "right": "a",
                 "relation": "height_lte"},
                {"id": "widths_close", "left": "a", "right": "b",
                 "relation": "width_near", "max_difference_px": 1}
            ]
        }
        report = audit(profile, root)
        assert report["status"] == "ready_for_owner_review", report
        assert report["characters"][0]["measured"]["height_px"] == 12
        assert report["relative_constraints"][0]["status"] == "pass"
        assert report["relative_constraints"][1]["status"] == "pass"
        profile["characters"][1]["visual_review"]["morphology"] = "fail"
        report = audit(profile, root)
        assert report["status"] == "owner_visual_revision_required", report
        assert report["visual_review_failed"] == ["b"]
        profile["characters"][1]["visual_review"]["morphology"] = "pending"
        report = audit(profile, root)
        assert report["status"] == "human_review_required", report
        profile["characters"][1]["target_height_px"] = [12, 12]
        profile["relative_constraints"][1]["max_difference_px"] = 0
        report = audit(profile, root)
        assert report["status"] == "needs_revision", report
        assert report["relative_constraints"][0]["status"] == "pass"
        assert report["relative_constraints"][1]["status"] == "fail"
    print("audit_roster_harmony.py --self-check: PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", help="project roster-harmony profile JSON")
    parser.add_argument("--project-root", help="root for paths in the profile")
    parser.add_argument("--json", help="write report JSON to this path")
    parser.add_argument("--board", help="write a review-only baseline-aligned PNG board")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    if not args.manifest:
        parser.error("--manifest is required unless --self-check is used")
    try:
        manifest = json.load(open(args.manifest, encoding="utf-8"))
        project_root = args.project_root or os.path.abspath(
            os.path.join(os.path.dirname(args.manifest), ".."))
        report = audit(manifest, project_root)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"audit_roster_harmony.py: {exc}", file=sys.stderr)
        return 3
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.board:
        try:
            render_board(report, manifest, project_root, args.board)
        except (OSError, KeyError, TypeError, ValueError, RuntimeError) as exc:
            print(f"audit_roster_harmony.py: board render failed: {exc}", file=sys.stderr)
            return 3
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            f.write(payload)
    else:
        print(payload, end="")
    return 1 if report["status"] in (
        "needs_revision", "owner_visual_revision_required") else 0


if __name__ == "__main__":
    raise SystemExit(main())
