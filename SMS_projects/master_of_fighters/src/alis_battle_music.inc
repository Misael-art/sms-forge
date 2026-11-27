/* Compiled only for the cartridge with the two original Battle scores. */
#include "matchup.h"
extern volatile uint8_t vblank_epoch;
__sfr __at(0xf2) battle_audio_control;

enum { BATTLE_INACTIVE, BATTLE_PSG, BATTLE_FM };
volatile uint8_t mof_battle_backend;
static uint8_t battle_p2, battle_stamp, battle_wait;
static const uint8_t *battle_cursor;

/* The SDCC Z80 register calling convention passes the register/value pair in HL.
   At the SMS clock the YM2413 requires 12 clocks after the address and 84
   after data. The delay also protects two adjacent writes from different packets. */
static void battle_write(uint16_t pair) __z88dk_fastcall __naked
{
    (void)pair;
    __asm
        ld a,l
        out (#0xf0),a
        ld a,h
        nop
        nop
        out (#0xf1),a
        ld b,#6
    battle_write_delay:
        djnz battle_write_delay
        ret
    __endasm;
}

static uint8_t battle_has_fm(void)
{
    uint8_t zero,one;
    battle_audio_control=0;
    zero=battle_audio_control & 3u;
    battle_audio_control=1;
    one=battle_audio_control & 3u;
    battle_audio_control=0;
    return !zero && one==1;
}

static void battle_stop(void)
{
    uint8_t reg;
    if (mof_battle_backend==BATTLE_FM) {
        for (reg=0x20; reg<=0x28; ++reg) battle_write(reg);
        battle_write(0x0e);
        battle_audio_control=0;
    }
    mof_battle_backend=BATTLE_INACTIVE;
}

static void battle_start(void)
{
    battle_wait=0;
    battle_stamp=vblank_epoch-1u;
    if (battle_has_fm()) {
        battle_audio_control=3; /* Japanese SMS mixes FM music with PSG effects. */
        battle_cursor=(const uint8_t *)0x8000;
        mof_battle_backend=BATTLE_FM;
    } else {
        mof_battle_backend=BATTLE_PSG;
        SMS_mapROMBank(MOF_BATTLE_BANK);
        PSGPlay((void *)MOF_BATTLE_PSG);
    }
}

static void battle_fm_frame(void)
{
    uint8_t count,delay;
    if (battle_wait) { --battle_wait; return; }
    do {
        delay=*battle_cursor++;
        count=*battle_cursor++;
        while (count--) {
            battle_write(*(const uint16_t *)battle_cursor);
            battle_cursor+=2;
        }
        if (!delay) battle_cursor=(const uint8_t *)MOF_BATTLE_LOOP;
    } while (!delay);
    battle_wait=delay-1u;
}

static void battle_music_frame(void)
{
    uint8_t now=vblank_epoch, ticks=now-battle_stamp;
    SMS_saveROMBank();
    battle_stamp=now;
    SMS_mapROMBank(MOF_BATTLE_BANK);
    while (ticks--) {
        if (mof_battle_backend==BATTLE_FM) battle_fm_frame();
        else PSGFrame();
    }
    SMS_restoreROMBank();
}
