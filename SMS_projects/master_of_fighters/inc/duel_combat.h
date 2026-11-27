#ifndef MOF_DUEL_COMBAT_H
#define MOF_DUEL_COMBAT_H
#include "duel_rules.h"

#ifdef MOF_ALIS_COMBAT
/* Outside the combat probes at C770 and the presentation state at C800/C900. */
typedef struct {
    int8_t slide[2];
    uint8_t fall[2], jump_charge[2], guard_load[2], guard_window[2];
    uint8_t landing[2], spark[2], command[2], command_age[2];
    uint8_t palma_hits[2], cutscene_return, frozen_buttons[2], scroll_y;
} MofCombat;
typedef char MofCombatRamSize[sizeof(MofCombat)<=0x80u ? 1 : -1];

#ifdef MOF_DUEL_HOST_TEST
extern MofCombat mof_combat;
#else
#define mof_combat (*(MofCombat *)0xc880u)
#endif

#define MOF_COMBAT_HARD 1u
#define MOF_COMBAT_BOUNCE 2u
#define MOF_COMBAT_ROLL 3u
#define MOF_COMBAT_GUARD_LIMIT 4u
#define MOF_COMBAT_BUFFER 4u
#define MOF_PALMA_CHOP 19u
#define MOF_PALMA_RISE 36u
#define MOF_PALMA_GOLD_HIT 38u
#define MOF_PALMA_RELEASE 47u
#define MOF_PALMA_END 55u
#define MOF_SFX_LANDING 22u

void mof_combat_step_body(MofDuel *duel,uint8_t player,uint8_t keys);
void mof_combat_body(MofDuel *duel,uint8_t player,uint8_t keys);
#endif
#endif
