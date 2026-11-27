#ifdef MOF_ALIS_MATCHUP
#pragma codeseg SMSBANK_CAMERA
#pragma constseg SMSBANK_CAMERA
#include "SMSlib.h"
#include "../inc/alis_chapter.h"
#include "matchup.h"
#include "matchup_pan.h"

volatile uint8_t mof_pan_index, mof_pan_end_line, mof_pan_spills;

void mof_matchup_pan(uint8_t timed)
{
    const uint8_t *strip=mof_pan_strips;
    uint8_t delay=17, hold=19;
    mof_pan_index=mof_pan_end_line=mof_pan_spills=0;
    for (;;) {
        SMS_waitForVBlank();
        if (mof_pan_index < MOF_PAN_STEPS) {
            if (!--delay) {
                SMS_loadTileMapArea(2,11,strip,18,10);
                mof_pan_end_line=SMS_getVCount();
                if (mof_pan_end_line<192u) ++mof_pan_spills;
                ++mof_pan_index;
                strip+=360;
                delay=3;
            }
        } else if (timed && !--hold) return;
        if (mof_matchup_keys() & MOF_DUEL_ONE) return;
    }
}

#include "alis_pages.h"
#define MENU_ENTRY mof_banked_menu
#include "alis_chapter_menu.inc"
#endif
