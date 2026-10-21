/* audio.c — PSGlib music + PSGlib SFX no slot compartilhado de áudio.
 *
 * O canal 0 fica reservado à melodia. Os quatro streams .psg usam apenas
 * canais 2/3 e são processados depois de PSGFrame(), então o feedback sonoro
 * não é apagado pela atualização da música no mesmo VBlank.
 */
#include "game.h"
#include "PSGlib.h"
#include "music_battle.h"
#include "music_title.h"
#include "sfx_shot.h"
#include "sfx_hit.h"
#include "sfx_hurt.h"
#include "sfx_down.h"

static unsigned char music_on;

void audio_init(void) {
    music_on = 0;
    PSGStop();
    PSGSFXStop();
}

void audio_music(unsigned char on) {
    if (on) {
        PSGStop();
        PSGPlay(music_battle);
        music_on = 1;
    } else if (music_on) {
        PSGStop();
        PSGSilenceChannels();
        music_on = 0;
    }
}

void audio_music_title(void) {
    PSGStop();
    PSGPlay(music_title);
    music_on = 1;
}

void sfx_play(unsigned char id) {
    /* Máscaras oficiais: nenhum SFX desta tabela possui SFX_CHANNEL0. */
    switch (id) {
    case SFX_SHOT:
        PSGSFXPlay((void *)sfx_shot, SFX_CHANNEL2);
        break;
    case SFX_HIT:
        PSGSFXPlay((void *)sfx_hit, SFX_CHANNELS2AND3);
        break;
    case SFX_HURT:
        PSGSFXPlay((void *)sfx_hurt, SFX_CHANNEL3);
        break;
    case SFX_DOWN:
        PSGSFXPlay((void *)sfx_down, SFX_CHANNEL3);
        break;
    default:
        break;
    }
}

void audio_frame(void) {
    PSGFrame();
    PSGSFXFrame();
}
