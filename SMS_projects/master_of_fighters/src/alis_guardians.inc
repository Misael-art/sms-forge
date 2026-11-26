/* These exposures play only after the deciding cut connects. */
#include "../inc/alis_magic.h"
#include "magic_cine.h"
/* PSG volume DAC. The panel remains visible; the VDP interrupt stays enabled. */
__sfr __at(0x7f) magic_psg;
static void magic_voice(void)
{
    const uint8_t *samples=(const uint8_t *)MAGIC_VOICE_ADDR;
    uint16_t count=MAGIC_VOICE_LEN;
    PSGStop();PSGSFXStop();PSGSilenceChannels();
    SMS_mapROMBank(MOF_GUARDIANS_PAGE);
    magic_psg=0x81;magic_psg=0x40;
    do {
        magic_psg=*samples++;
        __asm
        push bc
        ld b,#40
00100$: djnz 00100$
        pop bc
        __endasm;
    } while (--count);
    magic_psg=0x9f;
    mof_chapter_theme(mof_presentation->result_song);
}

/* Deltas point to already-resident patterns. Bound the number of PNT
   entries per blank, including a row run spanning multiple blanks. */
static const uint8_t *patch_cursor;
static uint8_t patch_left;
static uint16_t patch_cell;
static void magic_animate(void)
{
    uint8_t budget=20,n;
    while (budget && patch_cursor) {
        if (!patch_left) {
            patch_cell=*(const uint16_t *)patch_cursor;
            patch_left=patch_cursor[2];patch_cursor+=3;
            if (!patch_left) {patch_cursor=0;break;}
        }
        n=budget<patch_left ? budget : patch_left;
        budget-=n;patch_left-=n;
        SMS_setNextTileatLoc(patch_cell);patch_cell+=n;
        do {SMS_setTile(*(const uint16_t *)patch_cursor);patch_cursor+=2;} while (--n);
    }
}

static void magic_slash(uint8_t frame)
{
    uint8_t i,x=44+frame*3,y=107-frame;
    SMS_initSprites();
    for (i=0;i<sizeof(magic_cut_xy);i+=2)
        SMS_addSprite(x+magic_cut_xy[i],y+magic_cut_xy[i+1],i>>1);
    SMS_copySpritestoSAT();
}

static void prepare_laconian_cut(void)
{
    SMS_useFirstHalfTilesforSprites(0);
    SMS_mapROMBank(MAGIC_PATTERN_BANK);
    SMS_loadTiles((const void *)MAGIC_CUT_ADDR,256,MAGIC_CUT_BYTES);
    SMS_setSpritePaletteColor(1,35);SMS_setSpritePaletteColor(2,59);SMS_setSpritePaletteColor(3,63);
}

static void draw_laconian_cut(uint8_t t)
{
    magic_slash(t);
    SMS_setBGScrollX(t>=15 && t<21 ? (t&1 ? 2 : 254) : 0);
}

/* The roster owns the background. The caller supplies its own effect and
   duration. No function here needs the identity of the attacking fighter. */
void mof_chapter_reaction(uint8_t target,uint8_t duration,void (*prepare)(void),void (*draw)(uint8_t))
{
    static const uint8_t page[MOF_DUEL_FIGHTER_IDS]={[MOF_DUEL_HAYATO]=7,[MOF_DUEL_ALIS]=6};
    uint8_t t;
    if (target>=MOF_DUEL_FIGHTER_IDS) return;
    show_page(MOF_GUARDIANS_PAGE+page[target]);
    SMS_displayOff();
    if (prepare) prepare();
    SMS_waitForVBlank();SMS_displayOn();
    SMS_VDPturnOnFeature(VDPFEATURE_LEFTCOLBLANK);
    mof_magic.scene=page[target]+1;
    for (t=0;t<duration;++t) {
        SMS_waitForVBlank();
        if (draw) draw(t);
        mof_chapter_music();PSGSFXFrame();
    }
    SMS_setBGScrollX(0);SMS_useFirstHalfTilesforSprites(1);
    SMS_initSprites();SMS_copySpritestoSAT();
}

void mof_magic_victory(void)
{
    static const uint8_t duration[]={31,28,34,31,39,20};
    static const uint8_t sound[]={GUARDIANS,FIRE_HOLD,TWIN_FIRE,REST,MYAU,SLASH};
    uint8_t scene,t,phase,exposure,track,k;
    for (scene=0;scene<6;++scene) {
        show_page(MOF_GUARDIANS_PAGE+scene);
        mof_magic.scene=scene+1;
        if (!scene) magic_voice();
        mof_magic.audio=sound[scene];mof_magic_sound();
        patch_cursor=0;patch_left=0;exposure=0;phase=0;track=scene*3;
        for (t=0;t<duration[scene];++t) {
            SMS_waitForVBlank();
            SMS_mapROMBank(MOF_GUARDIANS_PAGE+scene);
            if (t && !(t&7u) && !patch_cursor) {
                exposure^=1;
                patch_cursor=(const uint8_t *)magic_patch[scene][exposure];
            }
            if (patch_cursor) magic_animate();
            if (magic_cycle[track] && !(t&3u)) {
                for (k=0;k<3;++k) SMS_setBGPaletteColor(13+k,magic_cycle[track+(phase+k)%3]);
                if (++phase==3) phase=0;
            }
            mof_chapter_music();PSGSFXFrame();
        }
    }
    mof_magic.audio=GUARDIANS;mof_magic_sound();
    mof_chapter_reaction(mof_magic.target_fighter,41,prepare_laconian_cut,draw_laconian_cut);
    mof_magic.scene=mof_magic.finisher=0;
}
