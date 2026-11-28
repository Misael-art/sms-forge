"""Host-C regression for mapping one actor's TALL cells into BG name-table rows."""
from __future__ import annotations
import re
import shutil
import subprocess
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'SMS_projects/luta_mugem_rev2/src/main.c'
pytestmark = [pytest.mark.rev2,
              pytest.mark.skipif(shutil.which('cc') is None, reason='C compiler unavailable')]


def test_bg_tilemap_preserves_pairs_and_rejects_invalid_or_clipped_cells(tmp_path):
    source = SOURCE.read_text(encoding='utf-8')
    match = re.search(r'^static unsigned char build_bg_shadow\([^\n]*\n?.*?^}', source, re.M | re.S)
    assert match, 'BG actor map function missing'
    code = r'''
#include <stdint.h>
#include <stdio.h>
#define BG_MAP_W 8u
#define BG_MAP_H 10u
#define POOL_PAIRS 128u
#define SOLID_BG_TILE 256u
#define TILE_USE_SPRITE_PALETTE 0x0800u
#define TILE_PRIORITY 0x1000u
#define METASPRITE_END 0x80u
static uint16_t bg_shadow[BG_MAP_W * BG_MAP_H];
''' + match.group() + r'''
#define REQUIRE(c, msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
int main(void) {
    const unsigned char meta[] = {0, 0, 0, 8, 16, 2, 0x80};
    const unsigned char xbad[] = {64, 0, 0, 0x80};
    const unsigned char ybad[] = {0, 80, 0, 0x80};
    const unsigned char alignbad[] = {1, 0, 0, 0x80};
    const unsigned char tilebad[] = {0, 0, 4, 0x80};
    const unsigned char duplicate[] = {0, 0, 0, 0, 0, 2, 0x80};
    REQUIRE(build_bg_shadow(meta, 2u, 4u, 80, 80), "valid META rejected");
    REQUIRE(bg_shadow[0] == 0x1808u && bg_shadow[8] == 0x1809u &&
            bg_shadow[17] == 0x180au && bg_shadow[25] == 0x180bu &&
            bg_shadow[1] == 256u, "wrong top/bottom patterns or blank tile");
    REQUIRE(build_bg_shadow(meta, 2u, 4u, -1, 80) && bg_shadow[0] == 256u &&
            bg_shadow[17] == 0x180au, "left clipping differs from sprite path");
    REQUIRE(build_bg_shadow(meta, 2u, 4u, 80, -1) && bg_shadow[0] == 256u &&
            bg_shadow[17] == 0x180au, "top clipping differs from sprite path");
    REQUIRE(build_bg_shadow(meta, 2u, 4u, 249, 80) && bg_shadow[0] == 0x1808u &&
            bg_shadow[17] == 256u, "right clipping differs from sprite path");
    REQUIRE(!build_bg_shadow(xbad, 2u, 4u, 80, 80), "accepted META outside width");
    REQUIRE(!build_bg_shadow(ybad, 2u, 4u, 80, 80), "accepted META outside height");
    REQUIRE(!build_bg_shadow(alignbad, 2u, 4u, 80, 80), "accepted unaligned META");
    REQUIRE(!build_bg_shadow(tilebad, 2u, 4u, 80, 80), "accepted tile outside pose");
    REQUIRE(!build_bg_shadow(duplicate, 2u, 4u, 80, 80), "accepted overlapping cells");
    REQUIRE(!build_bg_shadow(meta, 2u, 127u, 80, 80), "accepted pool overflow");
    return 0;
}
'''
    program = tmp_path / 'bg.c'
    program.write_text(code, encoding='utf-8')
    exe = tmp_path / 'bg'
    compiled = subprocess.run(['cc', '-std=c99', str(program), '-o', str(exe)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
