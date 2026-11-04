"""Framebuffer fit from a named source space onto Master System or Game Gear.

The default is a size-only conversion onto the Master System, 256x192.
CPS2 is 384x224, so that default is horizontal 2/3 and vertical 6/7.
The older uniform fighter band and the fixed 1:4 probe stay selectable.
A missing source name is refused. Times, flips and blend stay put.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image

SPACES: dict[str, tuple[int, int]] = {
    "cps1": (384, 224),
    "cps2": (384, 224),
    "sms": (256, 192),
    "game_gear": (160, 144),
}
MODES = ("pose_budget", "framebuffer", "fighter_scale", "legacy_quarter", "off")
DEFAULT_MODE = "pose_budget"
DEFAULT_TARGET = "sms"
MARKER = "display_fit:"
EXEMPT_GROUPS = frozenset({9000})
PAD = 8
COLUMN_LIMIT = 8
COLUMN_PX = COLUMN_LIMIT * PAD
POSE_GATE = 0.70
POSE_NEAR = 0.69
# Pair of fighters, tall 8x16, both on the same scanlines. POSE_NEAR stays in
# the report as within_8_ratio and does not open or close the extra scale.
NEUTRAL_COLUMNS = 4
WIDE_COLUMNS = 5
PARTNER_COLUMNS = 3
FX_COLUMNS = 3


@dataclass(frozen=True)
class DisplayFit:
    mode: str
    status: str
    source: str | None
    target: str | None
    source_width: int | None
    source_height: int | None
    target_width: int | None
    target_height: int | None
    scale_num_x: int
    scale_den_x: int
    scale_num_y: int
    scale_den_y: int
    reason: str
    pose_budget: bool = False

    def to_dict(self) -> dict:
        return {
            "mode": self.mode,
            "status": self.status,
            "source": self.source,
            "target": self.target,
            "source_px": [self.source_width, self.source_height],
            "target_px": [self.target_width, self.target_height],
            "scale_x": [self.scale_num_x, self.scale_den_x],
            "scale_y": [self.scale_num_y, self.scale_den_y],
            "pose_budget": self.pose_budget,
            "reason": self.reason,
            "pixels_policy": "size_only_nearest_indexed",
            "exempt_groups": sorted(EXEMPT_GROUPS),
        }


def _fit(mode, status, source, target, sw, sh, tw, th, nx, dx, ny, dy, reason,
         pose_budget: bool = False) -> DisplayFit:
    return DisplayFit(mode, status, source, target, sw, sh, tw, th, nx, dx, ny, dy,
                      reason, pose_budget)


def _ratio(target: int, source: int) -> tuple[int, int]:
    common = math.gcd(target, source)
    return target // common, source // common


def resolve_display_fit(mode: str | None = None, source: str | None = None,
                        target: str | None = None) -> DisplayFit:
    """Decide the size ratio. Pose budget is the default and requires a source."""
    selected = (mode or DEFAULT_MODE).lower()
    pose_budget = selected == "pose_budget"
    if pose_budget:
        selected = "framebuffer"
    target_name = (target or DEFAULT_TARGET).lower()
    source_name = source.lower() if source else None
    if selected not in MODES:
        return _fit(selected, "refused", source_name, target_name, None, None, None, None,
                    1, 1, 1, 1, f"unknown mode: {selected}")
    if selected == "off":
        return _fit("off", "off", source_name, target_name, None, None, None, None,
                    1, 1, 1, 1, "size fit off; pixels and boxes stay", pose_budget)
    if selected == "legacy_quarter":
        return _fit("legacy_quarter", "option", source_name, target_name, None, None,
                    None, None, 1, 4, 1, 4,
                    "historical 1:4 probe remains available; it is not the framebuffer fit")
    if selected == "fighter_scale":
        return _fit("fighter_scale", "option", source_name, target_name, None, None,
                    None, None, 1, 1, 1, 1,
                    "current uniform idle-height band remains available in scene_cut; "
                    "it is not a framebuffer ratio")
    mode_name = "pose_budget" if pose_budget else selected
    if target_name not in SPACES:
        return _fit(mode_name, "refused", source_name, target_name, None, None, None, None,
                    1, 1, 1, 1, f"unknown target: {target_name}", pose_budget)
    if not source_name:
        return _fit(mode_name, "refused", None, target_name, None, None, None, None,
                    1, 1, 1, 1, "source framebuffer is required at project definition",
                    pose_budget)
    if source_name not in SPACES:
        return _fit(mode_name, "refused", source_name, target_name, None, None, None, None,
                    1, 1, 1, 1, f"unknown source: {source_name}", pose_budget)
    sw, sh = SPACES[source_name]
    tw, th = SPACES[target_name]
    nx, dx = _ratio(tw, sw)
    ny, dy = _ratio(th, sh)
    if (nx, dx, ny, dy) == (1, 1, 1, 1):
        return _fit(mode_name, "identity", source_name, target_name, sw, sh, tw, th,
                    1, 1, 1, 1, "source and target framebuffers match; no sample is dropped",
                    pose_budget)
    return _fit(mode_name, "applied", source_name, target_name, sw, sh, tw, th, nx, dx, ny, dy,
                f"{source_name} {sw}x{sh} -> {target_name} {tw}x{th}: "
                f"horizontal {nx}/{dx}, vertical {ny}/{dy}", pose_budget)


def scale_length(length: int, numerator: int, denominator: int) -> int:
    return max(1, (length * numerator) // denominator)


def scale_coord(value: int, numerator: int, denominator: int) -> int:
    if value >= 0:
        return (value * numerator + denominator // 2) // denominator
    return -(((-value) * numerator + denominator // 2) // denominator)


def _sample(dst: int, src_len: int, numerator: int, denominator: int) -> int:
    return min(src_len - 1, (dst * denominator + numerator // 2) // numerator)


def _pad(length: int, axis: int, multiple: int = PAD) -> tuple[int, int, int]:
    padded = ((length + multiple - 1) // multiple) * multiple
    extra = padded - length
    leading = extra // 2
    axis += leading
    if axis < 0:
        axis = 0
    if axis >= padded:
        axis = padded - 1
    return padded, leading, axis


def scale_sprite(sprite, fit: DisplayFit):
    if sprite.group in EXEMPT_GROUPS or fit.status in {"off", "identity"}:
        return sprite, False
    width = scale_length(sprite.width, fit.scale_num_x, fit.scale_den_x)
    height = scale_length(sprite.height, fit.scale_num_y, fit.scale_den_y)
    pixels = bytearray(width * height)
    for y in range(height):
        sy = _sample(y, sprite.height, fit.scale_num_y, fit.scale_den_y)
        row = sy * sprite.width
        base = y * width
        for x in range(width):
            sx = _sample(x, sprite.width, fit.scale_num_x, fit.scale_den_x)
            pixels[base + x] = sprite.pixels[row + sx]
    axis_x = scale_coord(sprite.axis_x, fit.scale_num_x, fit.scale_den_x)
    axis_y = scale_coord(sprite.axis_y, fit.scale_num_y, fit.scale_den_y)
    padded_w, pad_x, axis_x = _pad(width, axis_x)
    padded_h, pad_y, axis_y = _pad(height, axis_y)
    if pad_x or pad_y:
        canvas = bytearray(padded_w * padded_h)
        for y in range(height):
            src = y * width
            dst = (y + pad_y) * padded_w + pad_x
            canvas[dst:dst + width] = pixels[src:src + width]
        pixels = canvas
        width, height = padded_w, padded_h
    return replace(sprite, axis_x=axis_x, axis_y=axis_y, width=width, height=height,
                   pixels=bytes(pixels)), True


def _scale_box(box, fit: DisplayFit):
    x1, y1, x2, y2 = box
    return (scale_coord(x1, fit.scale_num_x, fit.scale_den_x),
            scale_coord(y1, fit.scale_num_y, fit.scale_den_y),
            scale_coord(x2, fit.scale_num_x, fit.scale_den_x),
            scale_coord(y2, fit.scale_num_y, fit.scale_den_y))


def _columns(width: int) -> int:
    return (width + PAD - 1) // PAD


def sat_row_peak(sprite) -> int:
    """Peak 8x16 cells one tall row hands to the SAT.

    A fully transparent cell is the cell `omit_blank_cells` drops. It does not
    count. Padded width divided by 8 counts that cell and is not this number.
    """
    width, height = sprite.width, sprite.height
    pixels = sprite.pixels
    if width <= 0 or height <= 0 or not pixels:
        return 0
    columns = (width + PAD - 1) // PAD
    rows = (height + 15) // 16
    peak = 0
    for row in range(rows):
        y0 = row * 16
        y1 = min(y0 + 16, height)
        count = 0
        for col in range(columns):
            x0 = col * PAD
            x1 = min(x0 + PAD, width)
            blank = True
            for y in range(y0, y1):
                base = y * width
                for x in range(x0, x1):
                    if pixels[base + x]:
                        blank = False
                        break
                if not blank:
                    break
            if not blank:
                count += 1
        if count > peak:
            peak = count
    return peak


def _neutral_pose(poses: list[dict], neutral_action: int) -> dict:
    for pose in poses:
        if pose["action"] == neutral_action:
            return pose
    return min(poses, key=lambda pose: (pose["columns"], pose["action"]))


def _pair_fits(columns: int, neutral_columns: int) -> bool:
    """4+4 closes two neutrals. 5 is legal only against a pose of at most 3."""
    if columns <= NEUTRAL_COLUMNS:
        return True
    return columns <= WIDE_COLUMNS and neutral_columns <= PARTNER_COLUMNS


def measure_body_poses(character, fx_groups=()) -> list[dict]:
    """One record per body action. FX groups and portraits do not set the reference."""
    blocked = set(fx_groups) | set(EXEMPT_GROUPS)
    sizes = {(sprite.group, sprite.image): sprite for sprite in character.sprites}
    poses = []
    for number, action in character.anims.items():
        body = []
        for frame in action.frames:
            if frame.group < 0 or frame.group in blocked:
                continue
            sprite = sizes.get((frame.group, frame.image))
            if sprite is None:
                continue
            body.append(sprite)
        if not body:
            continue
        widest = max(body, key=lambda sprite: (sat_row_peak(sprite), sprite.width * sprite.height))
        poses.append({
            "action": int(number),
            "width": widest.width,
            "height": widest.height,
            "columns": sat_row_peak(widest),
            "padded_columns": _columns(widest.width),
            "sprite": [widest.group, widest.image],
        })
    return poses


def decide_pose_scale(poses: list[dict], neutral_action: int = 0) -> dict:
    """Size the extra scale from the neutral pose, at most 4 SAT columns.

    `within_8_ratio` stays in the report. `POSE_NEAR` does not open or close
    the scale. A wide attack does not pull the body down to make itself fit.
    """
    if not poses:
        return {"policy": "pose_budget_pair", "gate": "no_body_pose", "extra_scale": [1, 1],
                "within_8_ratio": 0.0, "pose_near": POSE_NEAR, "body_actions": 0,
                "within_8": 0, "case_by_case": [], "included_actions": [],
                "neutral_action": None, "neutral_columns": 0}
    within = [pose for pose in poses if pose["columns"] <= COLUMN_LIMIT]
    ratio = len(within) / len(poses)
    neutral = _neutral_pose(poses, neutral_action)
    report = {
        "policy": "pose_budget_pair",
        "body_actions": len(poses),
        "within_8": len(within),
        "within_8_ratio": round(ratio, 4),
        "pose_near": POSE_NEAR,
        "neutral_action": neutral["action"],
        "neutral_columns": neutral["columns"],
        "neutral_px": [neutral["width"], neutral["height"]],
        "hardware_columns": COLUMN_LIMIT,
        "neutral_column_limit": NEUTRAL_COLUMNS,
        "wide_column_limit": WIDE_COLUMNS,
        "partner_column_limit": PARTNER_COLUMNS,
        "fx_column_limit": FX_COLUMNS,
        "pair": "4+4 for two neutrals; 5+3 only when the other pose is at most 3",
    }
    columns = neutral["columns"]
    if columns <= NEUTRAL_COLUMNS:
        report["gate"] = "idle_at_4"
        report["extra_scale"] = [1, 1]
        return report
    common = math.gcd(NEUTRAL_COLUMNS, columns)
    report["gate"] = "idle_to_4"
    report["extra_scale"] = [NEUTRAL_COLUMNS // common, columns // common]
    return report


def _fx_over_budget(character, fx_groups) -> list[dict]:
    blocked = set(fx_groups) - set(EXEMPT_GROUPS)
    found = []
    for sprite in character.sprites:
        if sprite.group not in blocked:
            continue
        peak = sat_row_peak(sprite)
        if peak <= FX_COLUMNS:
            continue
        padded = _columns(sprite.width)
        found.append({
            "group": sprite.group,
            "image": sprite.image,
            "sat_columns": peak,
            "padded_columns": padded,
            "px": [sprite.width, sprite.height],
            "reason": (f"sat row {peak} > {FX_COLUMNS} after the body fraction; "
                       f"padded width {sprite.width}px is {padded} columns"),
        })
    found.sort(key=lambda item: (-item["sat_columns"], item["group"], item["image"]))
    return found


def scale_character(character, fit: DisplayFit, fx_groups=(), neutral_action: int = 0):
    """Copy the character. Sprite size, axis and boxes follow the fit."""
    if fit.status in {"refused", "option"}:
        raise ValueError(fit.reason)
    original = {(sprite.group, sprite.image): sprite for sprite in character.sprites}
    sprites = []
    changed = 0
    for sprite in character.sprites:
        scaled, did = scale_sprite(sprite, fit)
        sprites.append(scaled)
        changed += int(did)
    scaled_by_key = {(sprite.group, sprite.image): sprite for sprite in sprites}
    anims = {}
    for number, action in character.anims.items():
        frames = []
        for frame in action.frames:
            src = original.get((frame.group, frame.image))
            dst = scaled_by_key.get((frame.group, frame.image))
            if src is None or dst is None or frame.group in EXEMPT_GROUPS or fit.status in {"off", "identity"}:
                frames.append(frame)
                continue
            frames.append(replace(
                frame,
                x=dst.axis_x + scale_coord(frame.x - src.axis_x, fit.scale_num_x, fit.scale_den_x),
                y=dst.axis_y + scale_coord(frame.y - src.axis_y, fit.scale_num_y, fit.scale_den_y),
                clsn1=[_scale_box(box, fit) for box in frame.clsn1],
                clsn2=[_scale_box(box, fit) for box in frame.clsn2],
            ))
        anims[number] = replace(action, frames=frames)
    scaled_character = replace(character, sprites=sprites, anims=anims)
    if not fit.pose_budget or fit.status != "applied":
        report = {"policy": "framebuffer_only", "gate": "not_applied", "extra_scale": [1, 1],
                  "case_by_case": []}
        return scaled_character, changed, report
    poses = measure_body_poses(scaled_character, fx_groups)
    report = decide_pose_scale(poses, neutral_action)
    report["fx_groups"] = sorted(set(fx_groups))
    num, den = report["extra_scale"]
    fitted = scaled_character
    if (num, den) != (1, 1):
        extra = replace(fit, pose_budget=False, scale_num_x=num, scale_den_x=den,
                        scale_num_y=num, scale_den_y=den)
        fitted, changed_again, _ignored = scale_character(scaled_character, extra)
        changed += changed_again
    final_poses = measure_body_poses(fitted, fx_groups)
    if final_poses:
        neutral_after = _neutral_pose(final_poses, report["neutral_action"])
        included, case_by_case = [], []
        for pose in final_poses:
            bucket = included if _pair_fits(pose["columns"], neutral_after["columns"]) else case_by_case
            bucket.append(pose["action"])
        report["included_actions"] = included
        report["case_by_case"] = case_by_case
        report["neutral_columns_after"] = neutral_after["columns"]
        report["neutral_px_after"] = [neutral_after["width"], neutral_after["height"]]
    else:
        report["included_actions"] = []
        report["case_by_case"] = []
        report["neutral_columns_after"] = 0
        report["neutral_px_after"] = [0, 0]
    report["fx_excluded"] = _fx_over_budget(fitted, fx_groups)
    return fitted, changed, report


def load_profile(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("display profile must be an object")
    if payload.get("schema") != "mugen2sms.display_profile/v1":
        raise ValueError("display profile schema must be mugen2sms.display_profile/v1")
    return payload


def marker_line(fit: DisplayFit, pose: dict | None = None) -> str:
    line = (f"{MARKER} source={fit.source} target={fit.target} "
            f"x={fit.scale_num_x}/{fit.scale_den_x} y={fit.scale_num_y}/{fit.scale_den_y}")
    extra = (pose or {}).get("extra_scale")
    if extra and (extra != [1, 1] or (pose or {}).get("policy") == "pose_budget_pair"):
        line += f" pose={extra[0]}/{extra[1]} gate={pose['gate']}"
    return line


def _write_png(sprite, path: Path) -> None:
    image = Image.new("P", (sprite.width, sprite.height))
    palette: list[int] = []
    for red, green, blue in list(sprite.palette)[:256]:
        palette.extend((int(red), int(green), int(blue)))
    palette.extend([0, 0, 0] * (256 - len(palette) // 3))
    image.putpalette(palette[:768])
    image.putdata(sprite.pixels)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Index 0 stays the transparent key. The ACT color at that index, magenta
    # on some donors and black on others, is not a visible pixel.
    image.save(path, transparency=0)


def apply_character(character, fit: DisplayFit, out_dir: Path, fighter_id: str,
                    fx_groups=()) -> dict:
    marker = out_dir / "display_fit.marker"
    if marker.exists():
        raise FileExistsError(f"{fighter_id}: display_fit already marked; a second pass would rescale")
    scaled, changed, pose = scale_character(character, fit, fx_groups)
    out_dir.mkdir(parents=True, exist_ok=True)
    sheets = out_dir / "sheets"
    max_before = [0, 0]
    max_after = [0, 0]
    max_fitted = [0, 0]
    max_exempt = [0, 0]
    pixels_before = 0
    pixels_after = 0
    max_columns = 0
    fitted_columns = 0
    wider_than_line = 0
    fitted_wider = 0
    for src, dst in zip(character.sprites, scaled.sprites):
        max_before[0] = max(max_before[0], src.width)
        max_before[1] = max(max_before[1], src.height)
        max_after[0] = max(max_after[0], dst.width)
        max_after[1] = max(max_after[1], dst.height)
        pixels_before += src.width * src.height
        pixels_after += dst.width * dst.height
        columns = (dst.width + PAD - 1) // PAD
        max_columns = max(max_columns, columns)
        if columns > 8:
            wider_than_line += 1
        if src.group in EXEMPT_GROUPS:
            max_exempt[0] = max(max_exempt[0], dst.width)
            max_exempt[1] = max(max_exempt[1], dst.height)
            continue
        max_fitted[0] = max(max_fitted[0], dst.width)
        max_fitted[1] = max(max_fitted[1], dst.height)
        fitted_columns = max(fitted_columns, columns)
        if columns > 8:
            fitted_wider += 1
        _write_png(dst, sheets / f"g{dst.group}_{dst.image}.png")
    frames = {}
    for number, action in scaled.anims.items():
        frames[str(number)] = [
            {"group": frame.group, "image": frame.image, "x": frame.x, "y": frame.y,
             "time": frame.time, "hflip": frame.hflip, "vflip": frame.vflip,
             "clsn1": [list(box) for box in frame.clsn1],
             "clsn2": [list(box) for box in frame.clsn2]}
            for frame in action.frames
        ]
    (out_dir / "frames.json").write_text(json.dumps({"actions": frames}, indent=2) + "\n",
                                         encoding="utf-8")
    report = {
        "schema": "mugen2sms.display_fit_apply/v1",
        "fighter_id": fighter_id,
        "fit": fit.to_dict(),
        "sprites_total": len(scaled.sprites),
        "sprites_resized": changed,
        "sprites_exempt_group_9000": sum(1 for sprite in character.sprites if sprite.group in EXEMPT_GROUPS),
        "max_sprite_px_before": max_before,
        "max_sprite_px_after": max_after,
        "max_fitted_px_after": max_fitted,
        "max_exempt_px_after": max_exempt,
        "pixel_slots_before": pixels_before,
        "pixel_slots_after": pixels_after,
        "sms_columns_max_after": max_columns,
        "sms_columns_max_fitted": fitted_columns,
        "sprites_wider_than_8_sms_sprites": wider_than_line,
        "sprites_fitted_wider_than_8": fitted_wider,
        "scanline_budget": "8 hardware sprites of 8 px; this count is not simulator approval",
        "pose_budget": pose,
        "frames": sum(len(action.frames) for action in scaled.anims.values()),
        "durations_preserved": all(
            [frame.time for frame in character.anims[number].frames]
            == [frame.time for frame in action.frames]
            for number, action in scaled.anims.items()),
    }
    (out_dir / "apply_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    marker.write_text(marker_line(fit, pose) + "\n", encoding="utf-8")
    return report


def _self_check() -> None:
    sms = resolve_display_fit("framebuffer", "cps2", "sms")
    assert (sms.scale_num_x, sms.scale_den_x, sms.scale_num_y, sms.scale_den_y) == (2, 3, 6, 7)
    gear = resolve_display_fit("framebuffer", "cps2", "game_gear")
    assert (gear.scale_num_x, gear.scale_den_x, gear.scale_num_y, gear.scale_den_y) == (5, 12, 9, 14)
    assert resolve_display_fit("framebuffer", "sms", "sms").status == "identity"
    assert resolve_display_fit("framebuffer", None, "sms").status == "refused"
    assert resolve_display_fit("framebuffer", "cps2", None).target == "sms"
    assert resolve_display_fit(None, "cps2", None).status == "applied"
    assert resolve_display_fit(None, "cps2", None).pose_budget is True
    assert resolve_display_fit("framebuffer", "cps2", "sms").pose_budget is False
    idle_over = decide_pose_scale([{"action": i, "width": 48, "height": 80, "columns": 6}
                                   for i in range(107)] + [
        {"action": 1000 + i, "width": 88, "height": 80, "columns": 11} for i in range(46)] + [
        {"action": 440, "width": 96, "height": 48, "columns": 12}])
    assert idle_over["gate"] == "idle_to_4" and idle_over["extra_scale"] == [2, 3]
    assert idle_over["within_8_ratio"] < POSE_GATE
    assert idle_over["pose_near"] == POSE_NEAR
    already = decide_pose_scale([
        {"action": 0, "width": 32, "height": 56, "columns": 4},
        {"action": 440, "width": 96, "height": 48, "columns": 12},
    ])
    assert already["gate"] == "idle_at_4" and already["extra_scale"] == [1, 1]
    assert already["within_8_ratio"] == 0.5
    assert resolve_display_fit("nope", "cps2", "sms").status == "refused"
    assert resolve_display_fit("legacy_quarter", "cps2", "sms").status == "option"
    assert resolve_display_fit("fighter_scale", "cps2", "sms").status == "option"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mugen2sms.display_fit")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--id", action="append", dest="ids")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.self_check:
        _self_check()
        print("display_fit self-check ok")
        return 0
    if args.profile is None or args.project is None or args.out is None:
        parser.error("--profile, --project and --out are required")
    profile = load_profile(args.profile)
    fit = resolve_display_fit(profile.get("mode"), profile.get("source"), profile.get("target"))
    if fit.status != "applied":
        print(fit.reason)
        return 2
    from mugen2sms.character import load
    from mugen2sms.source import Source

    characters = profile.get("characters")
    if not isinstance(characters, list) or not characters:
        raise ValueError("profile characters must name the zips to convert")
    selected = set(args.ids or [row["id"] for row in characters])
    wrote = []
    for row in characters:
        if row.get("id") not in selected:
            continue
        source = Source(args.project / row["zip"])
        character = load(source, row.get("def"))
        try:
            report = apply_character(character, fit, args.out / row["id"], row["id"],
                                 row.get("fx_groups") or [])
        except FileExistsError as err:
            print(err)
            return 2
        wrote.append(report)
        print(f"{row['id']}: {report['sprites_resized']} sprites, "
              f"max {report['max_sprite_px_before']} -> {report['max_sprite_px_after']}")
    if not wrote:
        print("no character matched")
        return 2
    summary = args.out / "summary.json"
    summary.write_text(json.dumps({"schema": "mugen2sms.display_fit_summary/v1",
                                    "fit": fit.to_dict(), "characters": wrote}, indent=2) + "\n",
                       encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
