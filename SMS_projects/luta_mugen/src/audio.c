/* audio.c — music + seis eventos autorais em PSGlib.
 *
 * Canais: a trilha usa o driver de música; SFX ocupam apenas os canais
 * autorados em audio_provenance_manifest.json. PSGFrame e PSGSFXFrame
 * avançam uma vez por VBlank conforme PSGlib/README.md e PSGlib.h.
 */
#include "PSGlib.h"
#include "audio.h"
#include "sfx_shot.h"
#include "sfx_hurt.h"
#include "sfx_special.h"
#include "sfx_hit.h"
#include "sfx_down.h"
#include "sfx_round.h"
#include "music_battle.h"

void audio_init(void) {
    PSGPlay((void *)music_battle);
    PSGSFXPlay((void *)sfx_round, SFX_CHANNEL2);
}

void audio_frame(void) {
    PSGFrame();
    PSGSFXFrame();
}

void audio_punch(void) {
    PSGSFXPlay((void *)sfx_shot, SFX_CHANNEL2);
}

void audio_kick(void) {
    PSGSFXPlay((void *)sfx_hurt, SFX_CHANNEL3);
}

void audio_special(void) {
    PSGSFXPlay((void *)sfx_special, SFX_CHANNELS2AND3);
}

void audio_hit(void) {
    PSGSFXPlay((void *)sfx_hit, SFX_CHANNELS2AND3);
}

void audio_ko(void) {
    PSGSFXPlay((void *)sfx_down, SFX_CHANNEL3);
}

void audio_round(void) {
    PSGSFXPlay((void *)sfx_round, SFX_CHANNEL2);
}
