"""The fallback emitter preserves cells and contact stamps at clipping/SAT boundaries."""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / "SMS_projects/luta_mugem_rev2"


@pytest.mark.rev2
@pytest.mark.skipif(shutil.which("cc") is None, reason="host C compiler unavailable")
def test_emission_and_stamps_match_reference_with_clipping_and_full_sat(tmp_path):
    source = (PROJECT / "src/main.c").read_text()
    function = re.search(r"^static void emit_frame\([^\n]*\n.*?^}", source, re.M | re.S).group()
    # SDCC's signed int is 16 bits; the host compiler's is 32 bits. Decode
    # serialized signed axis words with that target ABI in this host harness.
    function = function.replace("(signed int)((unsigned int)frame->axis", "(int16_t)((unsigned int)frame->axis")
    harness = r'''
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "rev2_diag.h"
#define LUTA_META_EMIT 0
#define LUTA_PAIR_SLOT_REUSE 0
#define LUTA_CONTACT_STAMPS 1
#define LUTA_DIAG_CLIP_PLAIN 1
#define LUTA_DIAG_STAGE_PROFILE 0
#define LUTA_DIAG_TELEMETRY 0
#define LUTA_BG_CAMERA 0
#define DIAG_FLOOR 160u
#define METASPRITE_END 0x80
typedef struct { unsigned char face,base_pair; } Slot;
typedef struct { unsigned short x,y; } Fighter;
static Slot current[2]; static Fighter fighter[2];
static unsigned char contact_draw_count[2],contact_draw_invalid[2];
static unsigned short probe_omitted_sat,probe_sat_om_p1,probe_sat_om_p2;
static unsigned char cells[64][3],used;
static signed char SMS_addSprite(int x,int y,unsigned char tile) {
    if (used==64) return -1;
    cells[used][0]=x;cells[used][1]=y;cells[used][2]=tile;used++;return 0;
}
''' + function + r'''
static unsigned long seed=19;
static unsigned random_byte(void) { seed=(seed*1664525ul+1013904223ul)&0xfffffffful;return seed>>24; }
#define CHECK(c) do {if(!(c)){printf("case=%u side=%u line=%u\n",trial,side,__LINE__);return 1;}}while(0)
int main(void) {
    unsigned trial,side,i,n,initial,drawn,invalid,omitted; int ox,oy,sx,sy;
    unsigned char meta[70*3+1],axis[4],expected[64][3]; Frame frame;
    for(trial=0;trial<10000;trial++) {
        side=random_byte()&1; n=1+random_byte()%70; initial=random_byte()%65;
        for(i=0;i<n;i++) {meta[3*i]=random_byte()%255-127;meta[3*i+1]=random_byte();meta[3*i+2]=random_byte();}
        meta[3*n]=METASPRITE_END;
        { short ax=(short)(random_byte()%129)-64,ay=(short)(random_byte()%129)-96;
          axis[0]=ax;axis[1]=(unsigned short)ax>>8;axis[2]=ay;axis[3]=(unsigned short)ay>>8;
          frame=(Frame){1,0,meta,meta,0,axis,(unsigned char)(8*(1+random_byte()%10)),64,meta,meta};
          current[side]=(Slot){random_byte()&1,random_byte()%128};
          fighter[side]=(Fighter){(unsigned short)(random_byte()<<8),(unsigned short)((random_byte()%180)<<8)};
          ox=current[side].face?FIGHTER_MIRRORED_ORIGIN_X(fighter[side].x>>8,ax,frame.width):(int)(fighter[side].x>>8)+ax;
          oy=160-(int)(fighter[side].y>>8)+ay; }
        drawn=invalid=omitted=0;memset(expected,0,sizeof expected);
        for(i=0;i<n;i++) {
            sx=ox+(signed char)meta[3*i];sy=oy+(signed char)meta[3*i+1];
            if(sx>=0&&sx<256&&sy>=0&&sy<192) {
                if(sx>248||sy>176) invalid=1;
                if(initial+drawn==64){omitted++;invalid=1;}
                else {expected[initial+drawn][0]=sx;expected[initial+drawn][1]=sy;
                      expected[initial+drawn][2]=(unsigned char)(meta[3*i+2]+2*current[side].base_pair);drawn++;}
            } else invalid=1;
        }
        memset(cells,0,sizeof cells);used=initial;
        contact_draw_count[side]=3;contact_draw_invalid[side]=0;
        probe_omitted_sat=probe_sat_om_p1=probe_sat_om_p2=0;
        emit_frame(side,&frame);
        CHECK(used==initial+drawn);CHECK(!memcmp(cells,expected,sizeof cells));
        CHECK(contact_draw_count[side]==3+drawn);CHECK(contact_draw_invalid[side]==invalid);
        CHECK(probe_omitted_sat==omitted);
        CHECK((side?probe_sat_om_p2:probe_sat_om_p1)==omitted);
    }
    return 0;
}
'''
    cfile = tmp_path / "emit_stamps.c"
    cfile.write_text(harness)
    exe = tmp_path / "emit_stamps"
    result = subprocess.run(["cc", "-std=c99", "-I", str(PROJECT / "inc"), str(cfile), "-o", str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
