#include <genesis.h>

#include "resources.h"
#include "system/audio.h"

static u8 sCueFrames = 0;
typedef struct { const char *name, *source; const u8 *data; } AudioTrack;
static const AudioTrack sTracks[] = {
    { "SUZAKU - FIGHT", "SUZAKU / BGM", mus_suzaku_fight }
};
static AudioMusicState sMusicState = AUDIO_MUSIC_STOPPED;
static u16 sTrack;
static u8 sMusicPending;
static u32 sMusicTicks, sMusicLastVInt;
static u8 sPreviewKind; /* 0 none, 1 SFX, 2 voice; Options owns PCM3. */
static u8 sMusicVolume = 100;
static u8 sEffectsEnabled = TRUE;
static u8 sVoiceEnabled = TRUE;

static void audioStopPsg(void)
{
    PSG_setEnvelope(0, PSG_ENVELOPE_MIN);
    PSG_setEnvelope(1, PSG_ENVELOPE_MIN);
    PSG_setEnvelope(2, PSG_ENVELOPE_MIN);
    PSG_setEnvelope(3, PSG_ENVELOPE_MIN);
}

static void audioPulsePsg(u8 channel, u16 tone, u8 envelope, u8 frames)
{
    PSG_setFrequency(channel, tone);
    PSG_setEnvelope(channel, envelope);
    sCueFrames = frames;
}

void AUDIO_stopAll(void)
{
    sMusicState = AUDIO_MUSIC_STOPPED;
    sMusicPending = 0;
    sMusicTicks = 0;
    sCueFrames = 0;
    audioStopPsg();
    AUDIO_stopPcmSamples();
    XGM2_stop();
}

void AUDIO_stopPcmSamples(void)
{
    sPreviewKind = 0;
    XGM2_stopPCM(SOUND_PCM_CH1);
    XGM2_stopPCM(SOUND_PCM_CH2);
    XGM2_stopPCM(SOUND_PCM_CH3);
}

static void musicClock(void)
{
    const u32 delta = vtimer - sMusicLastVInt;
    sMusicTicks = delta > 0xFFFFFFFFUL - sMusicTicks ? 0xFFFFFFFFUL : sMusicTicks + delta;
    sMusicLastVInt = vtimer;
}
u16 AUDIO_musicCount(void) { return sizeof(sTracks) / sizeof(sTracks[0]); }
const char *AUDIO_musicName(u16 index) { return index < AUDIO_musicCount() ? sTracks[index].name : "SEM FAIXA"; }
const char *AUDIO_musicSource(u16 index) { return index < AUDIO_musicCount() ? sTracks[index].source : "SEM ORIGEM"; }
u16 AUDIO_musicIndex(void) { return sTrack; }
AudioMusicState AUDIO_musicState(void) { return sMusicState; }
u32 AUDIO_musicTicks(void) { return sMusicTicks; }
bool AUDIO_playMusic(u16 index)
{
    if (index >= AUDIO_musicCount()) return FALSE;
    AUDIO_stopPreview();
    sTrack = index;
    sMusicTicks = 0;
    sMusicLastVInt = vtimer;
    sMusicState = AUDIO_MUSIC_PLAYING;
    sMusicPending = 1;
    AUDIO_setMusicVolume(sMusicVolume);
    XGM2_play(sTracks[index].data);
    return TRUE;
}
void AUDIO_startFightBgm(void) { AUDIO_playMusic(0); }
void AUDIO_stopFightBgm(void)
{
    sMusicState = AUDIO_MUSIC_STOPPED;
    sMusicPending = 0;
    sMusicTicks = 0;
    XGM2_stop();
}
void AUDIO_pauseMusic(void)
{
    if (sMusicState != AUDIO_MUSIC_PLAYING) return;
    musicClock();
    sMusicState = AUDIO_MUSIC_PAUSED;
    XGM2_pause();
}
void AUDIO_resumeMusic(void)
{
    if (sMusicState != AUDIO_MUSIC_PAUSED) return;
    sMusicLastVInt = vtimer;
    sMusicState = AUDIO_MUSIC_PLAYING;
    sMusicPending = 1;
    XGM2_resume();
}

void AUDIO_setMusicVolume(u8 volume)
{
    if (volume > 100) volume = 100;
    sMusicVolume = volume;
    XGM2_setFMVolume(volume);
    XGM2_setPSGVolume(volume);
}

void AUDIO_setEffectsEnabled(bool enabled)
{
    sEffectsEnabled = enabled ? TRUE : FALSE;
    if (!sEffectsEnabled) {
        if (sCueFrames) { sCueFrames = 0; audioStopPsg(); }
        if (sPreviewKind == 1) { XGM2_stopPCM(SOUND_PCM_CH3); sPreviewKind = 0; }
    }
}

void AUDIO_setVoiceEnabled(bool enabled)
{
    sVoiceEnabled = enabled ? TRUE : FALSE;
    if (!sVoiceEnabled && sPreviewKind == 2) { XGM2_stopPCM(SOUND_PCM_CH3); sPreviewKind = 0; }
}

void AUDIO_stopPreview(void)
{
    XGM2_stopPCM(SOUND_PCM_CH3);
    sPreviewKind = 0;
    if (sCueFrames) { sCueFrames = 0; audioStopPsg(); }
}
bool AUDIO_previewSample(const u8 *sample, u32 length, bool voice)
{
    if (!sample || !length || (voice ? !sVoiceEnabled : !sEffectsEnabled)) return FALSE;
    AUDIO_stopPreview();
    if (!XGM2_playPCM(sample, length, SOUND_PCM_CH3)) return FALSE;
    sPreviewKind = voice ? 2 : 1;
    return TRUE;
}
void AUDIO_testVoiceSample(const u8 *sample, u32 length) { AUDIO_previewSample(sample, length, TRUE); }
void AUDIO_testSfxSample(const u8 *sample, u32 length) { AUDIO_previewSample(sample, length, FALSE); }

void AUDIO_init(void)
{
    PSG_reset();
    XGM2_loadDriver(TRUE);
    AUDIO_stopAll();
    sCueFrames = 0;
}

void AUDIO_playCue(AudioCue cue)
{
    if (!sEffectsEnabled) return;
    switch (cue)
    {
        case AUDIO_CUE_MENU:
            audioStopPsg();
            audioPulsePsg(0, 440, 5, 5);
            break;
        case AUDIO_CUE_JUMP:
            audioStopPsg();
            audioPulsePsg(0, 720, 3, 6);
            break;
        case AUDIO_CUE_LAND:
            audioStopPsg();
            PSG_setNoise(PSG_NOISE_TYPE_PERIODIC, PSG_NOISE_FREQ_CLOCK8);
            PSG_setEnvelope(3, 6);
            sCueFrames = 4;
            break;
        case AUDIO_CUE_STRIKE:
            audioStopPsg();
            audioPulsePsg(1, 180, 2, 8);
            break;
        case AUDIO_CUE_PAUSE:
            audioStopPsg();
            audioPulsePsg(0, 320, 4, 4);
            break;
        default:
            sCueFrames = 0;
            break;
    }
}

void AUDIO_update(void)
{
    if (sMusicState == AUDIO_MUSIC_PLAYING) {
        musicClock();
        /* Commands are asynchronous: false immediately after PLAY/RESUME is
         * not an end event. Wait for acknowledgement; never restart implicitly.
         * The current track loops in its XGM2 data. */
        if (XGM2_isPlaying()) sMusicPending = 0;
        else if (!sMusicPending) sMusicState = AUDIO_MUSIC_STOPPED;
    }

    if (sCueFrames == 0) {
        return;
    }

    sCueFrames--;
    if (sCueFrames == 0) {
        audioStopPsg();
    }
}
