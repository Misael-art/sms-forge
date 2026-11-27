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
#ifdef MOF_PALMA_VERSIONS
    const uint8_t *strip;
    uint8_t bank,edge;
    uint8_t delay,hold;
redraw:
    menu_page(MOF_VERSUS_PAGE+mof_stage_choice);
    strip=(const uint8_t *)mof_strip_addresses[mof_stage_choice];
    bank=mof_strip_banks[mof_stage_choice];
    delay=17;hold=19;
#else
    const uint8_t *strip=mof_pan_strips;
    uint8_t delay=17, hold=19;
#endif
    mof_pan_index=mof_pan_end_line=mof_pan_spills=0;
    for (;;) {
        SMS_waitForVBlank();
        if (mof_pan_index < MOF_PAN_STEPS) {
            if (!--delay) {
#ifdef MOF_PALMA_VERSIONS
                mof_camera_strip(bank,strip);
#else
                SMS_loadTileMapArea(2,11,strip,18,10);
#endif
                mof_pan_end_line=SMS_getVCount();
                if (mof_pan_end_line<192u) ++mof_pan_spills;
                ++mof_pan_index;
                strip+=360;
                delay=3;
            }
        } else if (timed) --hold;
#ifdef MOF_PALMA_VERSIONS
        edge=mof_matchup_keys();
        if (edge & MOF_DUEL_ONE) return;
        edge &= MOF_DUEL_UP|MOF_DUEL_DOWN;
        if (edge==MOF_DUEL_UP || edge==MOF_DUEL_DOWN) {
            if (edge==MOF_DUEL_DOWN) mof_stage_choice=mof_stage_choice==2 ? 0 : mof_stage_choice+1;
            else mof_stage_choice=mof_stage_choice ? mof_stage_choice-1 : 2;
            timed=0;
            goto redraw;
        }
#else
        if (mof_matchup_keys() & MOF_DUEL_ONE) return;
#endif
        if (timed && !hold) return;
    }
}

#include "alis_pages.h"
#define MENU_ENTRY mof_banked_menu
#include "alis_chapter_menu.inc"
#endif
