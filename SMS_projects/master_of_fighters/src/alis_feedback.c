#if defined(MOF_ALIS_FEEDBACK)
#pragma codeseg SMSBANK_CAMERA
#pragma constseg SMSBANK_CAMERA
#include "SMSlib.h"
#include "../inc/alis_feedback.h"
#include "alis_pages.h"

#define SCRATCH 268u
typedef char feedback_ram_fits[sizeof(MofFeedback)<=128 ? 1 : -1];
static const uint8_t digits[7][5]={{0},{2,6,2,2,7},{7,1,7,4,7},{7,1,7,1,7},
                                     {5,5,7,1,1},{7,4,7,1,7},{7,4,7,5,7}};
static const uint8_t letters[3][5]={{5,5,7,5,5},{5,7,7,5,5},{6,5,6,4,4}};
static const uint8_t cross[5]={0,2,7,2,0};
static const uint8_t sparks[4][8]={
    {0x81,0x42,0,0,0,0,0x42,0x81},{0,0x42,0x24,0,0,0x24,0x42,0},
    {0,0,0x24,0x18,0x18,0x24,0,0},{0,0x18,0x18,0x7e,0x7e,0x18,0x18,0}
};
static uint16_t peek(uint16_t loc)
{
    SMS_readNextTilefromLoc(loc);
    return SMS_getTile();
}
static void put(uint16_t loc,uint16_t tile)
{
    SMS_setNextTileatLoc(loc);
    SMS_setTile(tile);
}
static void release(uint8_t n)
{
    MofFeedbackCell *cell=&mof_feedback.cells[n];
    if (cell->used && (peek(cell->loc)&511u)==SCRATCH+n)
        put(cell->loc,cell->background);
    cell->used=0;
}
void mof_feedback_clear(void)
{
    uint8_t n=4;
    while (n) release(--n);
}
void mof_feedback_init(void)
{
    uint8_t i,hi=0,lo=255;
    for (i=0;i<16;++i) {
        uint8_t c=mof_feedback.palette[i];
        uint8_t r=c&3,g=(c>>2)&3,b=c>>4, lum=r*3+g*6+b;
        if (lum>=hi) { hi=lum; mof_feedback.light=i; }
        if (lum<lo) { lo=lum; mof_feedback.shadow=i; }
        mof_feedback.dark[i]=(r ? r-1 : 0) | ((g ? g-1 : 0)<<2) | ((b ? b-1 : 0)<<4);
    }
    /* Half an MP segment, in the left four pixels of the original full tile. */
    uint8_t full[32], empty[32];
    SMS_readVRAM(full,(MOF_DIGIT_TILE+11u)*32u,32);
    SMS_readVRAM(empty,(MOF_DIGIT_TILE+10u)*32u,32);
    for(i=0;i<32;++i) full[i]=(full[i]&0xf0)|(empty[i]&15);
    SMS_loadTiles(full,287,32);
}
static uint8_t reverse(uint8_t b)
{
    b=(b>>4)|(b<<4); b=((b&0xcc)>>2)|((b&0x33)<<2);
    return ((b&0xaa)>>1)|((b&0x55)<<1);
}
static void draw_cell(uint8_t n,uint16_t loc,const uint8_t *rows,uint8_t force)
{
    MofFeedbackCell *cell=&mof_feedback.cells[n];
    uint8_t image[32],i,plane,mask,shade;
    uint16_t tile;
    if (cell->used && cell->loc!=loc) release(n);
    tile=peek(loc);
    if (cell->used && (tile&511u)==SCRATCH+n) {
        if (!force) return;
        tile=cell->background;
    }
    cell->background=tile; cell->loc=loc; cell->used=1;
    SMS_readVRAM(image,(tile&511u)*32u,32);
    /* Original h/v flip and palette stay on the entry. Transform the ink
       to pattern space so screen text always reads left to right. */
    for(i=0;i<8;++i) {
        uint8_t offset=(tile&0x400 ? 7-i : i)*4;
        uint8_t white=tile&0x800 ? 13 : mof_feedback.light;
        uint8_t dark=tile&0x800 ? 1 : mof_feedback.shadow;
        mask=rows[i];shade=i ? rows[i-1]>>1 : 0;
        if(tile&0x200) { mask=reverse(mask);shade=reverse(shade); }
        for(plane=1;plane!=16;plane<<=1,++offset)
            image[offset]=(image[offset]&~(mask|shade)) | ((white&plane) ? mask : 0) |
                          ((dark&plane) ? (shade&~mask) : 0);
    }
    SMS_loadTiles(image,SCRATCH+n,32);
    put(loc,(tile&0xe00u)|0x1000u|(SCRATCH+n));
}
/* The input may have requested a cast pose while the VDP is still showing
   its crouch or guard. Attach to the hand in the displayed figure. */
static void focus_point(uint8_t frame, int16_t *x, int16_t *y)
{
    uint8_t pose=frame>>1;
    int8_t dx=2, height=30;
    if (pose==9) { dx=-3; height=17; }      /* lowering the sword */
    else if (pose==10 || pose==11) { dx=0; height=14; }
    else if (pose==21 || (pose>=77 && pose<=79)) { dx=-9; height=26; }
    else if (pose>=83 && pose<=85) { dx=-16; height=29; }
    else if (pose>=86 && pose<=89) { dx=-8; height=29; }
    *x+=frame&1 ? dx : -dx-1;
    *y-=height;
}
void mof_feedback_frame(const MofDuel *duel)
{
    uint8_t p;
    uint8_t seconds=mof_feedback.remaining;
    int8_t scroll=16-((duel->fighters[0].x+duel->fighters[1].x)>>4);
    for(p=0;p<2;++p) {
        const MofDuelFighter *actor=&duel->fighters[p];
        int16_t x=actor->x,y=144+duel->body[p].y_offset;
        uint8_t first=p*2,age=mof_feedback.age[p], kind=mof_feedback.label[p],row;
        uint16_t loc;
        if(seconds) {
            if (!(mof_feedback.participants&(1u<<p))) continue;
            focus_point(mof_feedback.shown[p],&x,&y);
        } else if(age) { x-=8; y-=64+(age<=8 ? 8 : 0); }
        else { release(first+1);release(first);mof_feedback.label[p]=0;continue; }
        row=y<24 ? 3 : (uint8_t)y>>3;
        if(row>=4 && row<12) x-=scroll;
        if(x<8) x=8; if(x>238) x=238;
        loc=(uint16_t)row*32+((uint8_t)x>>3);
        if(seconds) {
            /* At minimum distance the hands can land in one tile. Keep the
               second focus visible just above the shared point. */
            if(p && mof_feedback.participants==3 && mof_feedback.cells[0].used &&
               loc==mof_feedback.cells[0].loc) loc-=32;
            uint8_t stage=((mof_feedback.duration-seconds)*4)/mof_feedback.duration;
            draw_cell(first,loc,sparks[stage],1);
        } else {
            uint8_t left[8]={0},right[8]={0},i;
            for(i=0;i<5;++i) {
                left[i+1]=(cross[i]<<5)|(digits[mof_feedback.amount[p]][i]<<1);
                right[i+1]=(letters[kind==MOF_GAIN_HP ? 0 : 1][i]<<5)|(letters[2][i]<<1);
            }
            if(age>12) { left[0]=0x82; right[7]=0x44; }
            draw_cell(first,loc,left,age==16 || age==12);draw_cell(first+1,loc+1,right,age==16 || age==12);
            --mof_feedback.age[p];
        }
    }
}
void mof_feedback_wait(const MofDuel *duel)
{
    mof_feedback.presented=0;
    mof_feedback.remaining=mof_feedback.duration;
    while (mof_feedback.remaining) {
        SMS_waitForVBlank();
        if (!mof_feedback.presented) {
            mof_feedback_clear();
            SMS_loadBGPalette(mof_feedback.dark);
        }
        mof_feedback_frame(duel);
        mof_feedback.sampled_pad=SMS_getKeysStatus();
        ++mof_feedback.presented;
        --mof_feedback.remaining;
        mof_feedback_audio();
    }
    SMS_waitForVBlank();
    mof_feedback_clear();
    SMS_loadBGPalette(mof_feedback.palette);
    mof_feedback.duration=mof_feedback.participants=0;
}
#endif
