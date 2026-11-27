#if defined(MOF_ALIS_CHAPTER)
#include "SMSlib.h"
#include "PSGlib.h"
#include "../inc/alis_chapter.h"
#include "alis_pages.h"

MofChapter chapter;
const MofChapterPresentation *mof_presentation;

void mof_chapter_select(const MofChapterPresentation *presentation)
{
    mof_presentation=presentation;
}
#ifdef MOF_PALMA_VERSIONS
#include "matchup.h"
uint8_t mof_stage_choice;
static uint8_t active_arena, signal_x,signal_y,reader_x,reader_y;
static const uint8_t arena_banks[]=STAGE_ARENA_BANKS;
static const uint8_t signal_cols[]=STAGE_SIGN_X, signal_rows[]=STAGE_SIGN_Y;
static const uint8_t reader_cols[]=STAGE_PORT_SCAN_X, reader_rows[]=STAGE_PORT_SCAN_Y;
#define ARENA_BANK active_arena
#else
#define ARENA_BANK mof_presentation->arena_bank
#endif
static uint8_t last_pad;
static uint8_t rhythm[2], gesture[2], direction[2], last_face[2];
static uint8_t old_seconds, old_banner, old_gauge[2], banner_tiles, shutter;
static uint8_t displayed_combo[2];
static uint8_t cpu_keys, cpu_wait, cpu_cycle;

#ifdef MOF_ALIS_MAGIC
#include "../inc/alis_magic.h"
#include <stddef.h>
typedef char PntPacketLayout[offsetof(MofChapterPnt,cells)==1 && sizeof(MofPntWrite)==4 ? 1 : -1];

/* All entries are complete SMS VDP write commands. A spell can produce
   16 restorations and 16 overlays; the arena adds at most 15 entries. */
static void chapter_cell(uint8_t x,uint8_t y,uint16_t tile)
{
    MofPntWrite *cell=&mof_chapter_pnt.cells[mof_chapter_pnt.count++];
    cell->address=0x7800u+((uint16_t)y<<6)+(x<<1);
    cell->tile=tile;
}

void mof_chapter_flush_pnt(void) __naked
{
    __asm
        ld hl,#_mof_chapter_pnt
        ld a,(hl)
        or a
        ret z
        ld b,a
        ld (hl),#0
        inc hl
        di
    mof_chapter_pnt_loop:
        ld a,(hl)
        inc hl
        out (#0xbf),a
        ld a,(hl)
        inc hl
        out (#0xbf),a
        ld a,(hl)
        inc hl
        out (#0xbe),a
        ld a,(hl)
        inc hl
        out (#0xbe),a
        djnz mof_chapter_pnt_loop
        ei
        ret
    __endasm;
}
#else
#define chapter_cell(x,y,tile) SMS_setTileatXY(x,y,tile)
#endif

#ifdef MOF_PORT_SKY
static volatile uint8_t port_apron_scroll, port_runway_scroll;
static uint8_t flight_clock, flight[2], scanner;

/* Weapon tiles are precomposed in screen space. Rows 12–19 stay fixed. */
#ifdef MOF_PORT_CLOUDS
#include "palma_cloud_raster.inc"
#endif
#if !defined(MOF_PORT_CLOUDS) || defined(MOF_PALMA_VERSIONS)
static void port_classic_raster(void)
{
    uint8_t line=SMS_getVCount();
    if (line < 48u) {
        INLINE_SMS_setBGScrollX(port_apron_scroll);
    } else if (line >= 144u && line < 176u) {
        INLINE_SMS_setBGScrollX(port_runway_scroll);
    } else if ((line >= 80u && line < 112u) || line >= 176u) {
        INLINE_SMS_setBGScrollX(0);
    }
}

#endif

void mof_port_raster_start(void)
{
#ifdef MOF_PORT_CLOUDS
#ifdef MOF_PALMA_VERSIONS
    if (active_arena==STAGE_CLASSIC_BANK) {
        SMS_setLineInterruptHandler(port_classic_raster);
        SMS_setLineCounter(31);
    } else
#endif
    {
        SMS_setLineInterruptHandler(port_raster);
        SMS_setLineCounter(15);
    }
#else
    SMS_setLineInterruptHandler(port_classic_raster);
    SMS_setLineCounter(31);
#endif
    SMS_enableLineInterrupt();
}

static void port_bird(uint8_t bird, uint8_t advance)
{
    uint8_t phase=flight[bird], column=phase>>2;
#if defined(MOF_PALMA_VERSIONS)
    uint8_t row=active_arena==STAGE_CLASSIC_BANK ? 3u+bird : 3u;
#elif defined(MOF_PORT_CLOUDS)
    const uint8_t row=3; /* Both birds circle in clear sky, 17 columns apart. */
#else
    uint8_t row=3u+bird;
#endif
    uint16_t tile;
    if (advance) {
        phase=(phase+1u)&127u;
        flight[bird]=phase;
        if (!(phase&3u)) chapter_cell(column,row,MOF_PORT_SKY);
        column=phase>>2;
    }
    tile=MOF_PORT_SKY+1u+((phase&3u)<<1);
    chapter_cell(column,row,tile);
    chapter_cell((column+1u)&31u,row,tile+1u);
}
#endif

#ifdef MOF_ALIS_MATCHUP
#include "alis_battle_music.inc"
static uint8_t versus_pair;
void mof_chapter_pair(uint8_t p1,uint8_t p2)
{
    battle_p2=p2;
    versus_pair=(p1==MOF_DUEL_ALIS && p2==MOF_DUEL_ALIS);
}
#endif

void mof_chapter_theme(uint16_t song)
{
    PSGStop();
#ifdef MOF_ALIS_MATCHUP
    battle_stop();
    if (chapter.music && battle_p2==MOF_DUEL_ALIS && song==mof_presentation->battle_song) {
        battle_start();
        return;
    }
#endif
    if (chapter.music) {
        SMS_mapROMBank(mof_presentation->arena_bank);
        PSGPlay((void *)song);
    }
}

void mof_chapter_music(void)
{
#ifdef MOF_ALIS_MATCHUP
    if (mof_battle_backend) { battle_music_frame(); return; }
#endif
    if (chapter.music) {
        SMS_mapROMBank(mof_presentation->arena_bank);
        PSGFrame();
    }
}

/* Each panel is self-contained in a mapper page (palette, patterns, PNT).
   Its assets can reuse the entire display-off tile area between matches. */
static void show_page(uint8_t page)
{
    const uint8_t *data=(const uint8_t *)0x8000;
    uint16_t length;
    SMS_displayOff();
#ifdef MOF_PORT_SKY
    SMS_disableLineInterrupt();
    SMS_setBGScrollX(0);
    SMS_VDPturnOffFeature(VDPFEATURE_LEFTCOLBLANK);
#endif
    SMS_VRAMmemset(0x3f00, 0xd0, 1);
    SMS_mapROMBank(page);
    length=*(const uint16_t *)data;
    SMS_loadBGPalette(data+2);
#ifdef MOF_ALIS_MAGIC
    /* The Lutz brow tiles use a stationary gold palette during lightning. */
    if (page==MOF_GUARDIANS_PAGE+2u) SMS_loadSpritePalette((const uint8_t *)0xbff0);
#endif
#ifdef MOF_ALIS_MATCHUP
#ifdef MOF_PALMA_VERSIONS
    if (page>=MOF_VERSUS_PAGE && page<MOF_VERSUS_PAGE+3)
#else
    if (page==MOF_VERSUS_PAGE)
#endif
        SMS_loadSpritePalette((const uint8_t *)0xbff0);
#endif
    SMS_loadTiles(data+18,0,length);
    SMS_loadTileMap(0,0,data+18+length,1536);
    SMS_waitForVBlank();
    SMS_displayOn();
    last_pad=(uint8_t)SMS_getKeysStatus() & 63u;
}

#ifdef MOF_ALIS_MAGIC
#include "alis_guardians.inc"
#endif

static uint8_t menu_pressed(void)
{
    uint8_t pad=(uint8_t)SMS_getKeysStatus() & 63u;
    uint8_t edges=pad & (uint8_t)~last_pad;
    last_pad=pad;
    return edges;
}

static uint8_t menu_edges(void)
{
    SMS_waitForVBlank();
    mof_chapter_music();
    return menu_pressed();
}

#ifdef MOF_ALIS_MATCHUP
/* Called from the camera bank. The legacy opening song selects the stage bank. */
uint8_t mof_matchup_keys(void)
{
    mof_chapter_music();
    SMS_mapROMBank(MOF_PAN_BANK);
    return menu_pressed();
}

static void show_matchup(uint8_t timed)
{
#ifndef MOF_PALMA_VERSIONS
    show_page(MOF_VERSUS_PAGE);
#endif
    SMS_mapROMBank(MOF_PAN_BANK);
    mof_matchup_pan(timed);
}
#endif

static void story_pages(uint8_t from,uint8_t count)
{
    uint8_t edge;
    for (;count;--count,++from) {
        show_page(from);
        do { edge=menu_edges(); } while (!(edge & (MOF_DUEL_ONE|MOF_DUEL_TWO)));
        if (edge & MOF_DUEL_TWO) break;
    }
}

static void chapter_title(void)
{
#ifdef MOF_ALIS_MATCHUP
    if (versus_pair) { show_matchup(0); return; }
#endif
    show_page(MOF_PAGE_TITLE);
    while (!(menu_edges() & MOF_DUEL_ONE)) {}
}

#ifdef MOF_ALIS_MATCHUP
/* Menu code runs from the slot used by page data and songs. Re-select its
   bank in fixed ROM before returning from each operation that changes slots. */
#ifdef MOF_PALMA_VERSIONS
void mof_camera_strip(uint8_t bank,const uint8_t *strip)
{
    SMS_mapROMBank(bank);
    SMS_loadTileMapArea(2,11,strip,18,10);
    SMS_mapROMBank(MOF_PAN_BANK);
}
#endif
void menu_page(uint8_t page)
{
    show_page(page);
    SMS_mapROMBank(MOF_PAN_BANK);
}

uint8_t menu_input(void)
{
    SMS_waitForVBlank();
    return mof_matchup_keys();
}

void menu_title(void)
{
    chapter_title();
    SMS_mapROMBank(MOF_PAN_BANK);
}

void menu_opening(void)
{
    mof_chapter_theme(mof_presentation->opening_song);
    SMS_mapROMBank(MOF_PAN_BANK);
}

void menu_intro(void)
{
    story_pages(mof_presentation->intro_first,mof_presentation->intro_count);
    SMS_mapROMBank(MOF_PAN_BANK);
}

void mof_chapter_menu(void)
{
#ifdef MOF_PALMA_VERSIONS
    if (!chapter.target) mof_stage_choice=2;
#endif
    SMS_mapROMBank(MOF_PAN_BANK);
    mof_banked_menu();
}
#else
#define MENU_ENTRY mof_chapter_menu
#define menu_page show_page
#define menu_input menu_edges
#define menu_title chapter_title
#define menu_opening() mof_chapter_theme(mof_presentation->opening_song)
#define menu_intro() story_pages(mof_presentation->intro_first,mof_presentation->intro_count)
#include "alis_chapter_menu.inc"
#endif

void mof_chapter_match(void)
{
    chapter.wins[0]=chapter.wins[1]=chapter.round=0;
    mof_chapter_theme(mof_presentation->battle_song);
#ifdef MOF_ALIS_MATCHUP
    if (!chapter.story && versus_pair) show_matchup(1);
#endif
}

void mof_chapter_round(void)
{
    uint8_t i;
    if (chapter.round<3) ++chapter.round;
    chapter.phase=MOF_ROUND;
    chapter.seconds=60;
    chapter.age=chapter.subsecond=chapter.expired=0;
    old_seconds=old_banner=old_gauge[0]=old_gauge[1]=255;
    banner_tiles=16;
    shutter=0;
    cpu_keys=cpu_cycle=cpu_wait=0;
    for (i=0;i<2;++i) {
        chapter.meter[i]=chapter.idle[i]=0;
        chapter.combo[i]=displayed_combo[i]=0;
        rhythm[i]=gesture[i]=direction[i]=0;
    }
}

void mof_chapter_arena(void)
{
#ifdef MOF_PALMA_VERSIONS
    uint8_t version=chapter.story ? 1 : mof_stage_choice;
    active_arena=arena_banks[version];
    signal_x=signal_cols[version];signal_y=signal_rows[version];
    reader_x=reader_cols[version];reader_y=reader_rows[version];
#endif
    SMS_mapROMBank(ARENA_BANK);
#ifdef MOF_ALIS_MAGIC
    SMS_mapROMBank(MAGIC_PATTERN_BANK);
    SMS_loadTiles((const void *)MAGIC_BARS_ADDR,279,256);
    SMS_mapROMBank(ARENA_BANK);
#endif
#ifdef MOF_PORT_SKY
    SMS_loadBGPalette((const void *)MOF_PORT_PALETTE);
#endif
    SMS_loadTiles((const void *)0x8000,MOF_ARENA_FIRST,MOF_ARENA_BYTES);
    SMS_loadTileMap(0,0,(const void *)(0x8000u+MOF_ARENA_BYTES),1536);
#if MOF_ARENA_SPARE_COUNT > 0
    /* A streamed pose ends before this pattern in each SAT cache slot.
       The packer checks every pose from both costumes before assigning it. */
    const uint8_t *tiles=(const uint8_t *)MOF_ARENA_SPARE_ADDR;
    uint8_t remaining=MOF_ARENA_SPARE_COUNT, first=MOF_ARENA_SPARE_FIRST;
    while (remaining) {
        uint8_t n=remaining<MOF_ARENA_SPARE_WIDTH ? remaining : MOF_ARENA_SPARE_WIDTH;
        SMS_loadTiles(tiles,first,n*32u);
        tiles+=n*32u;
        first+=32;
        remaining-=n;
    }
#endif
#ifdef MOF_PORT_SKY
#ifdef MOF_PORT_CLOUDS
    port_cloud_phase=0;
#endif
    flight[0]=26;
    flight[1]=94;
    flight_clock=scanner=0;
    port_apron_scroll=port_runway_scroll=0;
#ifdef MOF_ALIS_MAGIC
    mof_chapter_pnt.count=0;
#endif
    port_bird(0,0);
    port_bird(1,0);
#ifdef MOF_ALIS_MAGIC
    mof_chapter_flush_pnt();
#endif
    SMS_setBGScrollX(0);
    SMS_VDPturnOnFeature(VDPFEATURE_LEFTCOLBLANK);
#endif
}

/* Called during non-playing phases, or after the measured fight SAT write.
   Only cells that changed are emitted on a playing frame. */
static void chapter_banner(uint8_t banner)
{
    uint8_t i;
    if (old_banner!=banner) {
        SMS_mapROMBank(ARENA_BANK);
        if (old_banner!=255) {
            const uint8_t *map=(const uint8_t *)(0x8000u+MOF_ARENA_BYTES);
            SMS_loadTileMap(12,4,map+2*(4*32+12),16);
            SMS_loadTileMap(12,5,map+2*(5*32+12),16);
        }
        banner_tiles=banner==255 ? 16 : 0;
        old_banner=banner;
    }
    if (banner_tiles<16) {
        const uint8_t *slice=(const uint8_t *)(MOF_BANNER_DATA+((uint16_t)banner<<9)+((uint16_t)banner_tiles<<5));
        SMS_mapROMBank(ARENA_BANK);
        UNSAFE_SMS_VRAMmemcpy128((MOF_BANNER_TILE+banner_tiles)*32u,slice);
        banner_tiles+=4;
        if (banner_tiles==16) {
            for (i=0;i<16;++i) {
                if (!(i&7u)) SMS_setNextTileatXY(12,4+(i>>3));
                SMS_setTile(MOF_BANNER_TILE+i);
            }
        }
    }
}

void mof_chapter_stage_hud(void)
{
    uint8_t i;
    if (chapter.phase==MOF_PLAY) {
#ifdef MOF_PORT_SKY
        uint8_t light=(chapter.subsecond<4 || (chapter.subsecond>=9 && chapter.subsecond<13));
        uint8_t scan=(chapter.subsecond>=32 && chapter.subsecond<43);
        if (scanner!=scan) {
            scanner=scan;
#ifdef MOF_PALMA_VERSIONS
            chapter_cell(reader_x,reader_y,MOF_PORT_SCANNER+scan);
#else
            chapter_cell(MOF_PORT_SCAN_X,MOF_PORT_SCAN_Y,MOF_PORT_SCANNER+scan);
#endif
        }
        if (!(++flight_clock&3u)) port_bird((flight_clock>>2)&1u,1);
#else
        uint8_t light=(chapter.subsecond>=17 && chapter.subsecond<29);
#endif
        if (shutter!=light) {
            shutter=light;
#ifdef MOF_PALMA_VERSIONS
            chapter_cell(signal_x,signal_y,MOF_SIGN_TILE+light);
#else
            chapter_cell(MOF_SIGN_X,MOF_SIGN_Y,MOF_SIGN_TILE+light);
#endif
        }
    }
    if (old_seconds!=chapter.seconds) {
        old_seconds=chapter.seconds;
#ifdef MOF_ALIS_MAGIC
        chapter_cell(15,1,MOF_DIGIT_TILE+chapter.seconds/10);
        chapter_cell(16,1,MOF_DIGIT_TILE+chapter.seconds%10);
#else
        SMS_setNextTileatXY(15,1);
        SMS_setTile(MOF_DIGIT_TILE+chapter.seconds/10);
        SMS_setTile(MOF_DIGIT_TILE+chapter.seconds%10);
#endif
    }
    for (i=0;i<2;++i) {
        uint8_t charge=chapter.meter[i]>>1;
#ifdef MOF_ALIS_MAGIC
        if (chapter.meter[i]==8 && (chapter.subsecond&8)) charge=0;
#endif
        if (charge!=old_gauge[i]) {
            uint8_t k;
            old_gauge[i]=charge;
#ifdef MOF_ALIS_MAGIC
            for (k=0;k<4;++k)
                chapter_cell((i ? 26 : 2)+k,2,MOF_DIGIT_TILE+(k<charge ? 11 : 10));
#else
            SMS_setNextTileatXY(i ? 26 : 2,2);
            for (k=0;k<4;++k) SMS_setTile(MOF_DIGIT_TILE+(k<charge ? 11 : 10));
#endif
        }
    }
    /* Append after the scene and both gauges. If this frame filled the PNT
       queue, keep the old display value and retry on the next presentation. */
    for (i=0;i<2;++i) {
        uint8_t hits=chapter.combo[i], x=i ? 23u : 7u;
        if (hits<2u) hits=0;
        if (displayed_combo[i]==hits) continue;
#ifdef MOF_ALIS_MAGIC
        if (mof_chapter_pnt.count > sizeof(mof_chapter_pnt.cells)/sizeof(mof_chapter_pnt.cells[0])-2u)
            break;
#endif
        chapter_cell(x,2,MOF_DIGIT_TILE+(hits>=10u ? hits/10u : 10u));
        chapter_cell(x+1u,2,MOF_DIGIT_TILE+(hits ? hits%10u : 10u));
        displayed_combo[i]=hits;
    }
}

void mof_chapter_publish_hud(uint8_t banner)
{
    chapter_banner(banner);
#ifdef MOF_ALIS_MAGIC
    mof_chapter_flush_pnt();
#endif
}

void mof_chapter_hud(uint8_t banner)
{
#ifdef MOF_ALIS_MAGIC
    mof_chapter_stage_hud();
    mof_chapter_publish_hud(banner);
#else
    chapter_banner(banner);
    mof_chapter_stage_hud();
#endif
}

static void end_round(uint8_t a,uint8_t b)
{
    chapter.phase=MOF_RESULT;
    chapter.winner=a==b ? 2 : (a<b);
    if (chapter.winner<2) ++chapter.wins[chapter.winner];
    chapter.age=0;
    mof_chapter_theme(mof_presentation->result_song);
    SMS_mapROMBank(MOF_RULE_BANK);
}

void mof_chapter_update(const MofDuel *duel)
{
    uint8_t i;
#ifdef MOF_PORT_SKY
    uint8_t center=(uint8_t)((duel->fighters[0].x+duel->fighters[1].x)>>1);
    port_apron_scroll=16u-(center>>3);
    port_runway_scroll=32u-(center>>2);
#endif
    for (i=0;i<2;++i) {
        const MofDuelFighter *f=&duel->fighters[i];
        chapter.combo[i]=duel->fighters[1u-i].combo_received;
        if (f->state==MOF_DUEL_READY && !f->keys) {
            if (chapter.idle[i]<254) ++chapter.idle[i];
            else chapter.idle[i]=150;
        } else chapter.idle[i]=0;
        if (f->contact==MOF_DUEL_LANDED || f->contact==MOF_DUEL_GUARDED) {
            if (chapter.meter[i]<8 && (f->standing_normal!=MOF_DUEL_SUPER
#ifdef MOF_ALIS_MAGIC
                || (mof_magic.effect_mask & (1u<<i))
#endif
                )) ++chapter.meter[i];
            if (chapter.meter[1-i]<8 && f->contact==MOF_DUEL_LANDED) ++chapter.meter[1-i];
        }
    }
    if (duel->fighters[0].state==MOF_DUEL_KO || duel->fighters[1].state==MOF_DUEL_KO)
        end_round(duel->fighters[0].life,duel->fighters[1].life);
    else if (++chapter.subsecond==60) {
        chapter.subsecond=0;
        if (!--chapter.seconds) {
            chapter.expired=1;
            end_round(duel->fighters[0].life,duel->fighters[1].life);
        }
    }
}

uint8_t mof_chapter_result(void)
{
    uint8_t edge;
#ifdef MOF_ALIS_MAGIC
    if (mof_magic.finisher) mof_magic_victory();
#endif
    if (chapter.winner==2 || chapter.wins[chapter.winner]<chapter.target) {
        mof_chapter_theme(mof_presentation->battle_song);
        return MOF_NEXT_ROUND;
    }
    if (chapter.story && !chapter.winner)
        story_pages(mof_presentation->ending_first,mof_presentation->ending_count);
    show_page(chapter.story && chapter.winner ? mof_presentation->defeat :
              mof_presentation->victory[chapter.winner]);
    do { edge=menu_edges(); } while (!(edge & (MOF_DUEL_ONE|MOF_DUEL_TWO)));
    return edge & MOF_DUEL_TWO ? MOF_MAIN_MENU : MOF_REMATCH;
}

uint8_t mof_chapter_cpu(const MofDuel *duel)
{
    const MofDuelFighter *f=&duel->fighters[1],*r=&duel->fighters[0];
    uint8_t front=f->face_right ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t back=f->face_right ? MOF_DUEL_LEFT : MOF_DUEL_RIGHT;
    int16_t gap=f->x-r->x;
    if (gap<0) gap=-gap;
    if (cpu_wait) { --cpu_wait; return cpu_keys; }
    ++cpu_cycle;
    cpu_wait=5;
    if (cpu_keys & (MOF_DUEL_ONE|MOF_DUEL_TWO)) cpu_keys=0;
    else if (r->state==MOF_DUEL_ATTACK && (cpu_cycle&3))
        cpu_keys=back | (r->keys & MOF_DUEL_DOWN);
    else if (gap>24)
        cpu_keys=front | ((cpu_cycle&7)==0 ? MOF_DUEL_UP : 0);
    else {
        cpu_keys=(cpu_cycle&2 ? MOF_DUEL_TWO : MOF_DUEL_ONE) | (cpu_cycle&4 ? MOF_DUEL_DOWN : 0);
        cpu_wait=(cpu_cycle&1) ? 2 : 7;
    }
    return cpu_keys;
}

void mof_chapter_spend_super(uint8_t player)
{
    chapter.meter[player]=rhythm[player]=gesture[player]=direction[player]=0;
}

/* Two distinct down/forward strokes at the current facing, then a fresh 1.
   A failed full-meter check falls back through the usual special reader. */
uint8_t mof_chapter_super_input(uint8_t p,uint8_t keys,uint8_t face,uint8_t free)
{
    uint8_t front=face ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t dir=keys & 15u;
    if (!free || face!=last_face[p] || !rhythm[p]) gesture[p]=0;
    last_face[p]=face;
    if (rhythm[p]) --rhythm[p];
    if (free && dir!=direction[p]) {
        if (dir==MOF_DUEL_DOWN) { gesture[p]=gesture[p]==2 ? 3 : 1; rhythm[p]=18; }
        else if (dir==front && (gesture[p]==1 || gesture[p]==3)) ++gesture[p];
        else if (dir && dir!=(front|MOF_DUEL_DOWN)) gesture[p]=0;
    }
    direction[p]=dir;
    return gesture[p]==4 && dir==front && chapter.meter[p]==8;
}
#endif
