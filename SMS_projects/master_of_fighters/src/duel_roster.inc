/* Fighter rules records by MOF_DUEL_* id. A new fighter adds its record
   file here; mof_duel_set_roster() refuses a pair with a missing record. */

#include "fighter_alis.inc"

static const MofFighterDef *const mof_roster[MOF_DUEL_FIGHTER_IDS] = {
    0,                  /* MOF_DUEL_HAYATO has no mirror record yet. */
    &mof_fighter_alis,  /* MOF_DUEL_ALIS */
};
