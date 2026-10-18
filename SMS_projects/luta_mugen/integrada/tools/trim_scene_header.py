#!/usr/bin/env python3
"""Drop the unpruned metasprite arrays from the generated scene header.

The integrated runtime draws from pose_table.h (pruned, per-fighter blob);
the Frame table only needs dur/pose/clsn/axis/width. Keeping the original
META/METAL/P2 arrays overflowed ROM bank 0. Their definitions are removed
and the matching Frame initializer fields become 0. Every other definition
is kept byte for byte (checked).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

META_ARRAY = re.compile(
    r"(?:#define (\w+_(?:P2_)?METAL?)_SIZE \d+\n)?const unsigned char (\w+_(?:P2_)?METAL?)\[\d+\] = \{.*?\};\n",
    re.S)


def trim(text: str) -> tuple[str, list[str]]:
    names = [m.group(2) for m in META_ARRAY.finditer(text)]
    out = META_ARRAY.sub("", text)
    for name in names:
        out = re.sub(rf"\b{name}\b", "0", out)
    return out, names


def self_check() -> None:
    src = ("#define A_META_SIZE 4\nconst unsigned char A_META[4] = {\n 1,2,3,0x80,\n};\n"
           "const unsigned char A_CLSN[2] = {\n 9,9,\n};\n"
           "static const Frame f[1] = {\n    { 4, 0, A_META, A_CLSN },\n};\n")
    out, names = trim(src)
    assert names == ["A_META"]
    assert "A_CLSN[2]" in out and "{ 4, 0, 0, A_CLSN }" in out and "A_META" not in out
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
    print(f"[TRIM] {len(names)} arrays de metasprite removidos; {len(text)} -> {len(out)} bytes de texto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
