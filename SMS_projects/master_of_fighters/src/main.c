// main.c — master_of_fighters (esqueleto do modelo SMSForge)
//
// Boot deterministico minimo: tela estavel, sem animacao, sem input.
// Serve para provar build -> ROM -> boot no emulador ANTES de qualquer arte.
// Substitua pelo runtime da cena 01 depois que doc/11-gdd.md estiver preenchido.
//
// Restricoes sempre ativas (AGENTS.md): sem float, sem malloc, sem API inventada.
// A autoridade da API e sdk/devkitSMS/SMSlib/SMSlib.h — confira antes de usar.

#include "SMSlib.h"

// Header 16KB => SDSC precisa ser a variante _16KB (combinacao provada em ROM
// no laboratorio_01; SMSlib.h:460 e :485 sao a autoridade).
SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "master_of_fighters",
                                     "esqueleto do modelo");

void main(void) {
    SMS_displayOff();
    // indice 0 e transparente/backdrop nas duas subpaletas (lei de paleta §8).
    SMS_setBGPaletteColor(0, 0x00);   // preto
    SMS_setBGPaletteColor(1, 0x3F);   // branco (codigo 6-bit: canais 0-3)
    /* Sprites leem padroes da PRIMEIRA metade da VRAM (tiles 0..255).
     * Sem isto o VDP le em tile+256 e sprites viram ruido colorido — causa-raiz
     * real do L006. SMSlib.h:53. Gate: audit_sprite_mode.py. */
    SMS_useFirstHalfTilesforSprites(1);
    SMS_displayOn();

    // Boot determinístico: estado inicial estavel, sem variacao entre frames.
    // (audit_deterministic_boot.py reprova ROM animada sem estado estavel.)
    for (;;) {
        SMS_waitForVBlank();
    }
}
