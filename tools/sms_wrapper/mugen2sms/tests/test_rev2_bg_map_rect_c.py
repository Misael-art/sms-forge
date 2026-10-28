"""Exercise bounded row damage and incremental BG name-table commits."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "SMS_projects/luta_mugem_rev2/src/main.c"
pytestmark = [pytest.mark.rev2,
              pytest.mark.skipif(shutil.which("cc") is None, reason="C compiler unavailable")]


def extract(source: str, name: str) -> str:
    match = re.search(r"^static (?:void|unsigned char) " + name +
                      r"\([^\n]*\n?.*?^}", source, re.M | re.S)
    assert match, f"runtime function {name} missing"
    return match.group()


def test_bg_map_row_damage_commits_direct_shadow_rows(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    functions = "\n".join(extract(source, name) for name in (
        "reset_bg_map_rect", "include_bg_map_rows", "bg_map_rect_cells",
        "commit_bg_map_rect"))
    code = r'''
#include <stdio.h>
#define BG_MAP_W 8u
#define BG_MAP_H 10u
static unsigned char bg_map_top, bg_map_height, bg_map_rect_valid;
static unsigned int vram[32u * 28u];
static unsigned calls, last_x, last_y, last_w, last_h;
static const unsigned int *last_src;
static void fake_area(unsigned char x, unsigned char y,
                      const unsigned int *src, unsigned char width,
                      unsigned char height) {
    unsigned char row, col;
    calls++; last_x=x; last_y=y; last_w=width; last_h=height; last_src=src;
    for (row=0u; row<height; row++)
        for (col=0u; col<width; col++)
            vram[(unsigned int)(y+row)*32u+x+col]=
                src[(unsigned int)row*width+col];
}
#define SMS_loadTileMapArea(x,y,src,w,h) \
    fake_area((unsigned char)(x),(unsigned char)(y),(src),(w),(h))
''' + functions + r'''
#define REQUIRE(c,msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
int main(void) {
    unsigned int shadow[BG_MAP_W*BG_MAP_H];
    unsigned char x,y;
    for (y=0u; y<BG_MAP_H; y++)
        for (x=0u; x<BG_MAP_W; x++)
            shadow[(unsigned int)y*BG_MAP_W+x]=(unsigned int)(0x1200u+y*8u+x);

    reset_bg_map_rect(1u);
    REQUIRE(bg_map_rect_cells()==80u && bg_map_top==0u && bg_map_height==10u,
            "first map did not schedule all rows");
    commit_bg_map_rect(shadow,bg_map_top,bg_map_height);
    REQUIRE(calls==1u && last_x==8u && last_y==8u && last_w==8u &&
            last_h==10u && last_src==shadow, "full map commit was not direct");

    reset_bg_map_rect(0u);
    include_bg_map_rows(0u,2u);
    include_bg_map_rows(5u,2u);
    REQUIRE(bg_map_rect_cells()==56u && bg_map_top==0u && bg_map_height==7u,
            "old/new row ranges were not united");
    commit_bg_map_rect(shadow,bg_map_top,bg_map_height);
    REQUIRE(calls==2u && last_y==8u && last_w==8u && last_h==7u &&
            last_src==shadow, "row range did not commit directly from shadow");

    reset_bg_map_rect(0u);
    REQUIRE(bg_map_rect_cells()==0u && bg_map_height==0u,
            "empty row range planned cells");
    commit_bg_map_rect(shadow,bg_map_top,bg_map_height);
    REQUIRE(calls==2u, "empty row range called SMSlib");

    reset_bg_map_rect(0u);
    include_bg_map_rows(3u,2u);
    REQUIRE(bg_map_rect_cells()==16u && bg_map_top==3u && bg_map_height==2u,
            "middle row range was wrong");
    commit_bg_map_rect(shadow,bg_map_top,bg_map_height);
    REQUIRE(calls==3u && last_y==11u && last_h==2u &&
            last_src==shadow+3u*BG_MAP_W, "middle rows used the wrong source");

    reset_bg_map_rect(0u);
    include_bg_map_rows(0u,1u);
    include_bg_map_rows(9u,1u);
    REQUIRE(bg_map_rect_cells()==80u && bg_map_top==0u && bg_map_height==10u,
            "opposite row edges did not expand to full map");
    return 0;
}
'''
    program = tmp_path / "bg_map_rows.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "bg_map_rows"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_bg_shadow_rebuild_clears_actor_rows_and_preserves_rest(tmp_path):
    source = SOURCE.read_text(encoding="utf-8")
    functions = "\n".join(extract(source, name) for name in (
        "reset_bg_map_rect", "include_bg_map_rows", "bg_map_rect_cells",
        "commit_bg_map_rect", "build_bg_shadow", "clear_bg_shadow"))
    code = r'''
#include <stdio.h>
#define LUTA_BG_DIFF_MAP 1
#define BG_MAP_W 8u
#define BG_MAP_H 10u
#define POOL_PAIRS 128u
#define SOLID_BG_TILE 256u
#define TILE_USE_SPRITE_PALETTE 0x0800u
#define TILE_PRIORITY 0x1000u
#define METASPRITE_END 0x80u
static unsigned int bg_shadow[BG_MAP_W*BG_MAP_H];
static unsigned char bg_previous_map_valid;
static unsigned char bg_map_top,bg_map_height,bg_map_rect_valid;
static unsigned char bg_actor_map_valid,bg_actor_top,bg_actor_height;
static const unsigned char *bg_previous_meta;
static unsigned char bg_previous_base,bg_previous_pairs,bg_previous_full;
static unsigned char bg_dirty,bg_valid;
static unsigned int vram[32u*28u];
static unsigned calls,last_w,last_h;
static void fake_area(unsigned char x,unsigned char y,const unsigned int *src,
                      unsigned char width,unsigned char height) {
    unsigned char row,col;
    calls++; last_w=width; last_h=height;
    for(row=0u;row<height;row++)
        for(col=0u;col<width;col++)
            vram[(unsigned int)(y+row)*32u+x+col]=
                src[(unsigned int)row*width+col];
}
#define SMS_loadTileMapArea(x,y,src,w,h) \
    fake_area((unsigned char)(x),(unsigned char)(y),(src),(w),(h))
''' + functions + r'''
#define REQUIRE(c,msg) do { if (!(c)) { puts(msg); return 1; } } while (0)
static unsigned int cell(unsigned char x,unsigned char y) {
    return vram[(unsigned int)(y+8u)*32u+x+8u];
}
int main(void) {
    static const unsigned char first[]={16u,0u,0u,METASPRITE_END};
    static const unsigned char second[]={32u,32u,0u,METASPRITE_END};
    unsigned char area;

    REQUIRE(build_bg_shadow(first,1u,0u,0,0),"initial shadow failed");
    REQUIRE(bg_map_top==0u && bg_map_height==10u && bg_map_rect_valid,
            "initial map did not schedule all rows");
    area=bg_map_rect_cells(); REQUIRE(area==80u,"initial area was wrong");
    commit_bg_map_rect(bg_shadow,bg_map_top,bg_map_height);
    bg_previous_map_valid=1u;
    REQUIRE(cell(2u,0u)==0x1800u && cell(2u,1u)==0x1801u,
            "initial actor tiles were not mapped");
    vram[(8u+9u)*32u+8u]=0x2345u;

    REQUIRE(build_bg_shadow(second,1u,1u,0,0),"replacement shadow failed");
    REQUIRE(bg_map_top==0u && bg_map_height==6u && bg_map_rect_valid,
            "old/new actor rows were not united");
    REQUIRE(bg_shadow[2u]==SOLID_BG_TILE &&
            bg_shadow[BG_MAP_W+2u]==SOLID_BG_TILE,
            "old actor cells were not cleared");
    REQUIRE(bg_shadow[4u*BG_MAP_W+4u]==0x1802u &&
            bg_shadow[5u*BG_MAP_W+4u]==0x1803u,
            "new actor cells were not written");
    area=bg_map_rect_cells(); REQUIRE(area==48u,"row upload area was wrong");
    commit_bg_map_rect(bg_shadow,bg_map_top,bg_map_height);
    REQUIRE(calls==2u && last_w==8u && last_h==6u,
            "replacement rows were not committed once");
    REQUIRE(cell(2u,0u)==SOLID_BG_TILE && cell(2u,1u)==SOLID_BG_TILE &&
            cell(4u,4u)==0x1802u && cell(4u,5u)==0x1803u,
            "PNT did not transition between actor poses");
    REQUIRE(cell(0u,9u)==0x2345u,
            "rows outside the damage range were overwritten");

    clear_bg_shadow();
    REQUIRE(bg_map_top==0u && bg_map_height==10u && !bg_actor_map_valid,
            "clear did not restore full-map damage");
    commit_bg_map_rect(bg_shadow,bg_map_top,bg_map_height);
    REQUIRE(calls==3u && last_w==8u && last_h==10u &&
            cell(4u,4u)==SOLID_BG_TILE && cell(4u,5u)==SOLID_BG_TILE,
            "full clear did not remove the replacement actor");
    return 0;
}
'''
    program = tmp_path / "bg_shadow_rows.c"
    program.write_text(code, encoding="utf-8")
    exe = tmp_path / "bg_shadow_rows"
    compiled = subprocess.run(["cc", "-std=c99", str(program), "-o", str(exe)],
                              capture_output=True, text=True)
    assert compiled.returncode == 0, compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
