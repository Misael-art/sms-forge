"""Check native scale and the separate blade/armor colors in Scene 02."""

import argparse
from collections import Counter
import json
from pathlib import Path

from PIL import Image, ImageDraw

from make_duel_scene02_assets import digest
from revise_scene02_alis import raster
from stage_alis_mirror import (AIR, CAUGHT, KICK_MATERIAL_REGIONS, PROJECT, THROW,
                              recolor, restore_kick_material, rgb)


KICKS = sum(AIR[2:], ())
POSES = KICKS + THROW + CAUGHT
FLEXED = {"air_3_2", "caught_3", "caught_5"}
CONCEPT = PROJECT / "data/source_art/concept_art/alis_landale/alis_concept_sheet_v4.png"


def audit_followup(indexed, palette, baseline):
    old_data = json.loads(baseline.read_bytes())
    old_frames = {(row["name"], row["player"], row["right"]): row for row in old_data["frames"]}
    records = []
    for key, frame in indexed.items():
        name, player, right = key
        if name not in KICK_MATERIAL_REGIONS and name not in ("alis_crouch", "alis_crouch_guard", "throw_5"):
            continue
        before = raster(old_frames[key], old_data["palette"])
        after = raster(frame, palette)
        before_height = max(y for x, y in before) - min(y for x, y in before) + 1
        after_height = max(y for x, y in after) - min(y for x, y in after) + 1
        changed = sum(before.get(point) != after.get(point) for point in before.keys() | after.keys())
        if name in KICK_MATERIAL_REGIONS:
            regions = KICK_MATERIAL_REGIONS[name]
            expected = {point: recolor(restore_kick_material(color, point[0] if right else -point[0] - 1,
                                                            point[1], regions), player)
                        for point, color in before.items()}
            passed = changed > 0 and after == expected
        elif name == "throw_5":
            passed = before_height == after_height and changed > 60 and sum(c == 56 for c in after.values()) >= 20
        else:
            passed = 1 <= before_height - after_height <= 2 and max(y for x, y in after) == 143
        records.append(dict(pose=name, player=player + 1, right=right, before_height=before_height,
                            after_height=after_height, changed=changed, passed=passed))
    return records


def audit(plan, output, baseline=None):
    data = json.loads(plan.read_bytes())
    indexed = {(row["name"], row["player"], row["right"]): row for row in data["frames"]}
    rows = []
    sheet = Image.new("RGB", (96 * 4, 69 * (len(POSES) + 2)), "#292839")
    draw = ImageDraw.Draw(sheet)
    for player in (0, 1):
        for right in (False, True):
            column = player * 2 + int(right)
            labels = ("idle", "alis_stand_guard") + POSES
            idle = raster(indexed["idle", player, right], data["palette"])
            idle_height = max(y for x, y in idle) - min(y for x, y in idle) + 1
            for index, name in enumerate(labels):
                frame = indexed[name, player, right]
                art = raster(frame, data["palette"])
                top, sole = min(y for x, y in art), max(y for x, y in art)
                x0, ground = column * 96 + 46, index * 69 + 67
                draw.text((column * 96 + 3, index * 69 + 1), name, fill="white")
                draw.line((column * 96 + 2, ground, column * 96 + 93, ground), fill="#686679")
                for (x, y), color in art.items():
                    draw.point((x0 + x, ground + y - 144), rgb(color))
                if name not in POSES:
                    continue
                # Register a region on the breastplate separately from the
                # weapon. The last backward step shifts the torso behind X.
                left, right_edge = (-17, -2) if name == "caught_5" else (-8, 6)
                chest = Counter(color for (x, y), color in art.items()
                                if left <= (x if right else -x - 1) <= right_edge and top + 12 <= y <= top + 25)
                blade = [(x, y) for (x, y), color in art.items() if color == 56]
                fabric = (24, 44) if player else (19, 35)
                height = sole - top + 1
                minimum = idle_height - (8 if name in FLEXED else 4)
                faults = []
                if not minimum <= height <= idle_height + 3 or sole != 143:
                    faults.append("scale_or_ground_registration")
                if chest[16] < 9 or chest[56]:
                    faults.append("breastplate_material")
                if len(blade) < 8 or max(y for x, y in blade) - min(y for x, y in blade) < 5:
                    faults.append("separate_blade")
                if sum(color in fabric for color in art.values()) < 12:
                    faults.append("costume_material")
                if name in KICKS + CAUGHT and frame["spill_tiles"]:
                    faults.append("moving_pose_requires_background")
                rows.append(dict(pose=name, player=player + 1, right=right, height=height, sole=sole,
                                 idle_height=idle_height, indigo_chest_pixels=chest[16],
                                 cyan_chest_pixels=chest[56], cyan_blade_pixels=len(blade),
                                 background_tiles=frame["spill_tiles"], faults=faults))
    output.mkdir(parents=True, exist_ok=True)
    sheet.save(output / "native.png")
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST).save(output / "review-2x.png")
    failures = sum(bool(row["faults"]) for row in rows)
    result = dict(plan_sha256=digest(plan), concept_sha256=digest(CONCEPT), source_sha256=data["source_sha256"],
                  checked=len(rows), failed=failures, frames=rows)
    if baseline:
        followup = audit_followup(indexed, data["palette"], baseline)
        result["baseline_sha256"] = digest(baseline)
        result["followup"] = followup
        result["followup_failures"] = sum(not row["passed"] for row in followup)
        print(f"{len(followup)} follow-up variants, {result['followup_failures']} out of contract")
    (output / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"{len(rows)} variants, {failures} out of contract")
    return bool(failures or result.get("followup_failures"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    raise SystemExit(audit(args.plan, args.output, args.baseline))
