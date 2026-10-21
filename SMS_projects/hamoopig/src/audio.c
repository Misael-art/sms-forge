#include "engine.h"
#include "PSGlib.h"
#include "sfx_hurt.h"
#include "sfx_shot.h"
#include "music_battle.h"
#include "music_title.h"

void audio_boot(void)
{
}

void audio_title(void)
{
    PSGStop();
    PSGPlay((void *)music_title);
}

void audio_fight(void)
{
    PSGStop();
    PSGPlay((void *)music_battle);
}

void audio_tick(void)
{
    PSGFrame();
    PSGSFXFrame();
}

void audio_hit(void)
{
    PSGSFXPlay((void *)sfx_hurt, SFX_CHANNEL3);
}

void audio_shot(void)
{
    PSGSFXPlay((void *)sfx_shot, SFX_CHANNEL2);
}
