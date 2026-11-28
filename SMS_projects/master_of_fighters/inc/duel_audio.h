#ifndef MOF_DUEL_AUDIO_H
#define MOF_DUEL_AUDIO_H

#include "duel_rules.h"

void mof_duel_audio_init(void);
void mof_duel_audio_tick(const MofDuel *duel, uint8_t hayato_player,
                         const MofDuelStandingNormal *alis_normals);

#endif
