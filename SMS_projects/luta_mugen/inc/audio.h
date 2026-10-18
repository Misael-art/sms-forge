/* audio.h — canal PSG do prototipo Ken vs dummy. */
#ifndef LUTA_AUDIO_H
#define LUTA_AUDIO_H

void audio_init(void);
void audio_frame(void);       /* uma chamada por VBlank */
void audio_punch(void);
void audio_kick(void);
void audio_special(void);
void audio_hit(void);
void audio_ko(void);
void audio_round(void);

#endif /* LUTA_AUDIO_H */
