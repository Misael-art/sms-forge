/* hud.c — HUD por marcacao suja, confinada as duas linhas travadas.
 *
 * Dois defeitos corrigidos aqui, ambos so visiveis medindo:
 *
 * 1. A versao anterior reescrevia ~60 caracteres na name table TODO frame,
 *    com o display ligado. Escrever VRAM fora da janela curta pos-VBlank e
 *    custo puro e tearing garantido. Agora so o contador de frames — que e
 *    instrumento de medicao e precisa mudar sempre — e incondicional.
 *
 * 2. `SMS_setBGScrollX` desloca o plano INTEIRO, HUD junto. Com scroll
 *    perceptivel, o bloco de 8x8 do contador de frames muda de conteudo por
 *    causa do deslocamento, e nao da contagem: measure_frame_advance.py
 *    mediu 33 trocas onde deviam existir 10. A HUD agora vive nas linhas 0 e
 *    1, e o VDP tem VDPFEATURE_LOCKHSCROLL exatamente para trava-las.
 *
 * Consequencia dura: NADA de HUD abaixo de y=1. A trava do VDP cobre so as
 * duas primeiras linhas de tile — qualquer texto em y>=2 volta a escorregar.
 */
#include "game.h"

#define HUD_ROWS 2   /* casado com VDPFEATURE_LOCKHSCROLL; nao ha terceira */

static unsigned char dirty;

static const unsigned char hex_digits[] = "0123456789ABCDEF";

static void print_number(unsigned char x, unsigned char y,
                         unsigned int value, unsigned char digits) {
    unsigned char out[6];
    unsigned char i;
    out[digits] = 0;
    for (i = digits; i > 0; i--) {
        out[i - 1] = (unsigned char)('0' + (value % 10));
        value /= 10;
    }
    SMS_printatXY(x, y, out);
}

void hud_reset(void) {
    dirty = 1;
}

void hud_mark(void) {
    dirty = 1;
}

/* A faixa de mensagem divide a linha 1 com o placar do nucleo: colunas
 * 14..31, 18 caracteres. Mensagem que passa disso invade a linha seguinte
 * pela aritmetica de XYtoADDR, que nao satura x. */
static void banner_text(const unsigned char *s) {
    SMS_printatXY(14, 1, (const unsigned char *)"                  ");
    SMS_printatXY(14, 1, s);
}

void hud_banner(unsigned char state) {
    switch (state) {
    case ST_TITLE:
        banner_text((const unsigned char *)"1 OR 2: START");
        break;
    case ST_PAUSE:
        banner_text((const unsigned char *)"PAUSED  1:GO");
        break;
    case ST_OVER:
        if (g_boss.hp == 0)
            banner_text((const unsigned char *)"BOSS DOWN 1:AGAIN");
        else
            banner_text((const unsigned char *)"BREACH  1:AGAIN");
        break;
    default:
        banner_text((const unsigned char *)"2:FIRE  1:PAUSE");
        break;
    }
}

void hud_draw(void) {
    unsigned char frame_hex[4];
    unsigned int display_frame;

    /* Marcador de medicao: measure_frame_advance.py cronometra a troca deste
     * bloco. Os tres digitos sao nibbles DISTINTOS de g_frame — o codigo
     * anterior usava (frame >> 5), que sobrepunha bits do nibble vizinho e
     * fazia o digito do meio mudar fora do periodo declarado. */
    /* O primeiro digito troca a cada 128 frames: a janela de captura do host
     * nao precisa amostrar um tile a cada frame para provar o loop. */
    /* Durante o warmup deterministico, o marcador fica congelado em 000.
     * Assim o gate de boot não confunde o instante em que o host conseguiu
     * capturar a janela com uma divergência de estado da ROM. */
    display_frame = (g_frame < DEMO_WARMUP_FRAMES) ? 0 :
                    (unsigned int)(g_frame - DEMO_WARMUP_FRAMES);
    frame_hex[0] = hex_digits[(display_frame >> 7) & 15];
    frame_hex[1] = hex_digits[(display_frame >> 3) & 15];
    frame_hex[2] = hex_digits[display_frame & 15];
    frame_hex[3] = 0;
    SMS_printatXY(29, 0, frame_hex);

    if (!dirty) return;
    dirty = 0;

    SMS_printatXY(0, 0, (const unsigned char *)"VANTA-9 HP:");
    print_number(11, 0, g_player.hp, 1);
    SMS_printatXY(13, 0, (const unsigned char *)"SC:");
    print_number(16, 0, g_score, 4);
    SMS_printatXY(21, 0, (const unsigned char *)"W:");
    print_number(23, 0, g_wave, 1);

    SMS_printatXY(0, 1, (const unsigned char *)"CORE:");
    print_number(5, 1, g_boss.hp, 2);
}
