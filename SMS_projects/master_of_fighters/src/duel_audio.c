#if defined(MOF_DUEL_REPERTOIRE)

#include "PSGlib.h"
#include "../inc/duel_audio.h"
#include "../inc/duel_commands.h"
#include "../inc/duel_sfx.h"

#ifdef MOF_ALIS_COMBAT
/* A close body impact starts at a lower pitch than the light body cue. */
static const uint8_t mof_sfx_body_heavy[]={0xc8,0x71,0xd4,0xe7,0xf5,0x38,
    0xc1,0x75,0xd6,0xf8,0x39,0xd9,0xfc,0x38,0xdf,0xff,0};
#endif

void mof_duel_audio_init(void)
{
    PSGSilenceChannels();
}

#if defined(MOF_DUEL_SCENE_MIRROR)
static uint8_t material_of(const MofDuelFighter *fighter)
{
    return fighter->standing_normal < MOF_DUEL_NORMALS_PER_FIGHTER
        ? fighter->def->moves[fighter->standing_normal].material : MOF_MATERIAL_BODY;
}
#endif

void mof_duel_audio_tick(const MofDuel *duel, uint8_t hayato_player,
                         const MofDuelStandingNormal *alis_normals)
{
    const MofDuelFighter *alis = &duel->fighters[1u - hayato_player];
    const MofDuelFighter *hayato = &duel->fighters[hayato_player];
    uint8_t move = alis->standing_normal;
#if defined(MOF_DUEL_SCENE_MIRROR)
    /* Two voices share the same hardware channels. Impact beats swing,
       and an equal contact in the same tick uses the first controller. */
    if (alis->contact != MOF_DUEL_LANDED &&
        (hayato->contact == MOF_DUEL_LANDED ||
         (alis->contact != MOF_DUEL_GUARDED && !alis->contact &&
          alis->state != MOF_DUEL_ATTACK))) {
        alis = hayato;
        hayato = &duel->fighters[1u - hayato_player];
        move = alis->standing_normal;
    }
    /* The sounding fighter's record names the material of each move. */
    uint8_t material = material_of(alis);
    alis_normals = alis->def->moves;
#else
    uint8_t material = move;
#endif

    /* Contact takes precedence over preparation. A miss emits only the swing. */
#if defined(MOF_DUEL_SCENE_MIRROR)
    if (alis->contact == MOF_DUEL_PARRIED || hayato->contact == MOF_DUEL_PARRIED)
        PSGSFXPlay((void *)mof_sfx_guard, SFX_CHANNELS2AND3);
    else
#endif
#if defined(MOF_ALIS_CHAPTER)
    /* The special and Super sounds ship with the chapter build. */
    if ((alis->contact==MOF_DUEL_LANDED && material==MOF_MATERIAL_SUPER) ||
        (hayato->contact==MOF_DUEL_LANDED && material_of(hayato)==MOF_MATERIAL_SUPER))
        PSGSFXPlay((void *)mof_sfx_palma, SFX_CHANNELS2AND3);
    else if ((alis->contact==MOF_DUEL_LANDED && material==MOF_MATERIAL_SPECIAL) ||
             (hayato->contact==MOF_DUEL_LANDED && material_of(hayato)==MOF_MATERIAL_SPECIAL))
        PSGSFXPlay((void *)mof_sfx_special, SFX_CHANNELS2AND3);
    else
#endif
    if (alis->contact == MOF_DUEL_LANDED && material == MOF_INPUT_SHORT_ONE)
        PSGSFXPlay((void *)mof_sfx_shield_hit, SFX_CHANNELS2AND3);
    else if (alis->contact == MOF_DUEL_LANDED && material == MOF_INPUT_LONG_ONE)
        PSGSFXPlay((void *)mof_sfx_blade_hit, SFX_CHANNELS2AND3);
    else if (alis->contact == MOF_DUEL_LANDED || hayato->contact == MOF_DUEL_LANDED)
#ifdef MOF_ALIS_COMBAT
        PSGSFXPlay((void *)(duel->hitstop_target&MOF_DUEL_HITSTOP_SHAKE ?
                   mof_sfx_body_heavy : mof_sfx_body_hit),SFX_CHANNELS2AND3);
#else
        PSGSFXPlay((void *)mof_sfx_body_hit, SFX_CHANNELS2AND3);
#endif
    else if (alis->contact == MOF_DUEL_GUARDED || hayato->contact == MOF_DUEL_GUARDED)
        PSGSFXPlay((void *)mof_sfx_guard, SFX_CHANNELS2AND3);
    else if (alis->state == MOF_DUEL_ATTACK && material <= MOF_INPUT_LONG_ONE &&
             mof_duel_age(duel, alis) == alis_normals[move].first_active - 2u &&
             PSGSFXGetStatus() == PSG_STOPPED) {
        if (material == MOF_INPUT_SHORT_ONE)
            PSGSFXPlay((void *)mof_sfx_shield_swing, SFX_CHANNEL3);
        else
            PSGSFXPlay((void *)mof_sfx_blade_swing, SFX_CHANNELS2AND3);
    }
    PSGSFXFrame();
}

#ifdef MOF_ALIS_MAGIC
#include "alis_magic_sound.inc"
#endif
#endif
