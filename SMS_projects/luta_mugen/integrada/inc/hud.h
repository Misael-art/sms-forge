#ifndef HUD_H
#define HUD_H

#define BANNER_CLEAR 0u
#define BANNER_ROUND 1u
#define BANNER_FIGHT 2u
#define BANNER_KO    3u
#define BANNER_TIME  4u

void hud_init(void);
void hud_set_life(unsigned char who, unsigned short life, unsigned short max_life);
void hud_set_timer(unsigned char seconds);
void hud_set_score(unsigned char who, unsigned char wins);
void hud_set_banner(unsigned char kind);
void hud_set_winner(unsigned char who);
void hud_flush(void);       /* no máximo 2 células; chamar no VBlank */
void hud_flush_all(void);   /* display apagado */

#endif
