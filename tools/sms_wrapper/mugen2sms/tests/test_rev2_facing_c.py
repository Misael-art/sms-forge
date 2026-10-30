"""The displayed metadata and origin must follow the resident facing."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "SMS_projects/luta_mugem_rev2/src/main.c"
INCLUDE = ROOT / "SMS_projects/luta_mugem_rev2/inc"
pytestmark = pytest.mark.skipif(shutil.which("cc") is None, reason="C compiler unavailable")


def test_runtime_rejects_absent_or_wrong_generated_facing_contract(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r'^#if !defined\(VERSUS_FACE_LAYOUT_ADJACENT_P2_LEFT\).*?^#endif', source, re.M | re.S)
    assert match
    program = tmp_path / "contract.c"
    program.write_text(match.group() + "\nint main(void) { return 0; }\n", encoding="utf-8")
    for definition, expected in ((None, False), ("0", False), ("1", True)):
        command = ["cc", "-std=c99", "-fsyntax-only", str(program)]
        if definition is not None:
            command.insert(1, "-DVERSUS_FACE_LAYOUT_ADJACENT_P2_LEFT=" + definition)
        result = subprocess.run(command, capture_output=True, text=True)
        assert (result.returncode == 0) == expected, result.stderr


def test_emitter_uses_resident_facing_and_palette_metadata(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"^static void emit_frame\(.*?^}", source, re.M | re.S)
    assert match
    harness = r'''
#include <stdio.h>
#include "rev2_diag.h"
#define DIAG_FLOOR 160u
#define LUTA_DIAG_CLIP_PLAIN 1
#define LUTA_DIAG_TELEMETRY 0
#define METASPRITE_END 0x80
typedef struct { unsigned int x, y; unsigned char face; } Actor;
typedef struct { unsigned char base_pair, face; } CacheSlot;
static Actor fighter[2];
static CacheSlot current[2];
static unsigned int probe_omitted_sat, probe_sat_om_p1, probe_sat_om_p2;
static int observed_x, observed_tile, calls;
static int fake_sprite(int x, int y, int tile) {
    (void)y; observed_x = x; observed_tile = tile; calls++; return 0;
}
#define SMS_addSprite(x, y, t) fake_sprite(x, y, t)
''' + match.group() + r'''
int main(void) {
    unsigned char axis[] = {0, 0, 0, 0};
    unsigned char p1r[] = {0, 0, 0, 0x80}, p1l[] = {0, 0, 2, 0x80};
    unsigned char p2r[] = {0, 0, 4, 0x80}, p2l[] = {0, 0, 6, 0x80};
    Frame frame = {1, 0, p1r, p1l, 0, axis, 16, 16, p2r, p2l};
    for (unsigned side = 0; side < 2; side++) {
        for (unsigned face = 0; face < 2; face++) {
            fighter[side].x = 100u * 256u;
            fighter[side].face = face ^ 1u; /* logical direction can be ahead of upload */
            current[side].face = face;
            calls = 0;
            emit_frame(side, &frame);
            if (calls != 1 || observed_x != (face ? 84 : 100) ||
                observed_tile != (int)(side * 4u + face * 2u)) {
                printf("wrong resident metadata/origin for side %u face %u: x=%d tile=%d calls=%d\n",
                       side, face, observed_x, observed_tile, calls);
                return 1;
            }
        }
    }
    return 0;
}
'''
    program = tmp_path / "facing.c"
    program.write_text(harness, encoding="utf-8")
    exe = tmp_path / "facing"
    subprocess.run(["cc", "-std=c99", "-I", str(INCLUDE), str(program), "-o", str(exe)],
                   check=True, capture_output=True, text=True)
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
