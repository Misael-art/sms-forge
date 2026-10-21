#!/usr/bin/env python3
"""Remove source arrays now consumed through the banked runtime data tables."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SOURCE_ARRAY = re.compile(
    r"(?:#define (\w+_(?:P2_)?(?:META|METAL|CLSN|AXIS))_SIZE \d+\n)?"
    r"const unsigned char (\w+_(?:P2_)?(?:META|METAL|CLSN|AXIS))\[\d+\] = \{.*?\};\n",
    re.S)
FRAME_TABLE = re.compile(
    r"static const Frame \w+_frames_all\[\w+\] = \{.*?\n\};\n", re.S)
ANIM_TABLE = re.compile(
    r"static const Anim \w+_anims\[\w+\] = \{.*?\n\};\n", re.S)
LEGACY_POSE_TABLE = re.compile(
    r"static const PoseRef versus_poses\[\w+\] = \{.*?\n\};\n", re.S)


def trim(text: str) -> tuple[str, list[str]]:
    names = [m.group(2) for m in SOURCE_ARRAY.finditer(text)]
    out = SOURCE_ARRAY.sub("", text)
    out = FRAME_TABLE.sub("", out)
    out = ANIM_TABLE.sub("", out)
    out = LEGACY_POSE_TABLE.sub("", out)
    for name in names:
        out = re.sub(rf"\b{name}\b", "0", out)
    return out, names


def self_check() -> None:
    src = ("#define A_META_SIZE 4\nconst unsigned char A_META[4] = {1,2,3,0x80};\n"
           "const unsigned char A_CLSN[2] = {9,9};\n"
           "const unsigned char A_AXIS[4] = {0,0,0,0};\n"
           "static const Frame ken_frames_all[1] = {\n"
           "    { 4, 0, A_META, A_META, A_CLSN, A_AXIS, 8, 16, 0, 0 },\n};\n"
           "static const Anim ken_anims[1] = {\n"
           "    { 0, 1, 0, ken_frames_all + 0 },\n};\n")
    src += ("static const PoseRef versus_poses[1] = {\n"
            "    { 2, 0, 73 },\n};\n")
    out, names = trim(src)
    assert names == ["A_META", "A_CLSN", "A_AXIS"]
    assert "ken_frames_all" not in out and "ken_anims" not in out
    assert "A_META[4]" not in out and "A_CLSN[2]" not in out
    assert "versus_poses" not in out
    print("[PASS] trim_scene_header self-check")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--header", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        self_check()
        return 0
    text = a.header.read_text()
    out, names = trim(text)
    kept_before = set(re.findall(r"const unsigned char (\w+)\[", text)) - set(names)
    kept_after = set(re.findall(r"const unsigned char (\w+)\[", out))
    if kept_before != kept_after:
        raise SystemExit(f"definicoes perdidas: {sorted(kept_before - kept_after)[:5]}")
    a.out.write_text(out)
    print(f"[TRIM] {len(names)} arrays-fonte removidos; {len(text)} -> {len(out)} bytes de texto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
