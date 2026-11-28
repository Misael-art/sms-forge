#ifdef MOF_ALIS_CHAPTER
#ifdef MOF_RULE_BANK
#pragma codeseg SMSBANK_RULES
#endif
#include "../inc/alis_chapter.h"

uint8_t mof_cpu[3];
uint8_t mof_chapter_cpu(const MofDuel *duel)
{
    const MofDuelFighter *f=&duel->fighters[1],*r=&duel->fighters[0];
    uint8_t front=f->face_right ? MOF_DUEL_RIGHT : MOF_DUEL_LEFT;
    uint8_t back=f->face_right ? MOF_DUEL_LEFT : MOF_DUEL_RIGHT;
    int16_t gap=f->x-r->x;
    if (gap<0) gap=-gap;
    if (mof_cpu[2]) { --mof_cpu[2]; return mof_cpu[0]; }
    ++mof_cpu[1];
    mof_cpu[2]=5;
    if (mof_cpu[0] & (MOF_DUEL_ONE|MOF_DUEL_TWO)) mof_cpu[0]=0;
    else if (r->state==MOF_DUEL_ATTACK && (mof_cpu[1]&3))
        mof_cpu[0]=back | (r->keys & MOF_DUEL_DOWN);
    else if (gap>24)
        mof_cpu[0]=front | ((mof_cpu[1]&7)==0 ? MOF_DUEL_UP : 0);
    else {
        mof_cpu[0]=(mof_cpu[1]&2 ? MOF_DUEL_TWO : MOF_DUEL_ONE) | (mof_cpu[1]&4 ? MOF_DUEL_DOWN : 0);
        mof_cpu[2]=(mof_cpu[1]&1) ? 2 : 7;
    }
    return mof_cpu[0];
}

#endif
