/* Música de quatro canais e SFX nas máscaras literais do manifesto.
 * PSGFrame e PSGSFXFrame uma vez por quadro, fora do bloco de VRAM.
 * Não chama PSGRestoreVolumes e não afirma que o canal da música volta.
 */
#include "PSGlib.h"
#include "audio.h"
#include "psg_blobs.h"

#define RANK_ROUND 1u
#define RANK_PUNCH 2u
#define RANK_HIT   3u
#define RANK_KO    4u

static unsigned char sfx_rank;

static unsigned char accept(unsigned char rank) {
    if (PSGSFXGetStatus() == PSG_STOPPED) sfx_rank = 0;
    if (sfx_rank != 0 && rank < sfx_rank) return 0;
    sfx_rank = rank;
    return 1;
}

void audio_init(void) {
    sfx_rank = 0;
    PSGPlay((void *)music_battle);
}

void audio_frame(void) {
    PSGFrame();
    PSGSFXFrame();
    if (PSGSFXGetStatus() == PSG_STOPPED) sfx_rank = 0;
}

void audio_punch(void) {
    if (!accept(RANK_PUNCH)) return;
    PSGSFXPlay((void *)sfx_shot, SFX_CHANNEL2);
}

void audio_hit(void) {
    if (!accept(RANK_HIT)) return;
    PSGSFXPlay((void *)sfx_hit, SFX_CHANNELS2AND3);
}

void audio_ko(void) {
    if (!accept(RANK_KO)) return;
    PSGSFXPlay((void *)sfx_down, SFX_CHANNEL3);
}

void audio_round(void) {
    if (!accept(RANK_ROUND)) return;
    PSGSFXPlay((void *)sfx_round, SFX_CHANNEL2);
}
