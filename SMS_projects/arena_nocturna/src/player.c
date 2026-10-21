/* player.c — VANTA-9: movimento, disparo e invulnerabilidade. */
#include "game.h"

Player g_player;

#define SHOT_SPEED     4
#define SHOT_COOLDOWN  10
#define WALK_SPEED     2

/* Offsets em pixels de TELA: no modo zoom cada tile 8x8 mede 16x16. */
static const signed char hero_meta[] = {
    0, 0, HERO_TILE, 16, 0, HERO_TILE + 1,
    0, 16, HERO_TILE + 2, 16, 16, HERO_TILE + 3, METASPRITE_END
};
static const signed char hero_walk_meta[] = {
    /* O ciclo e carregado no mesmo slot de HERO_TILE por streaming. */
    0, 0, HERO_TILE, 16, 0, HERO_TILE + 1,
    0, 16, HERO_TILE + 2, 16, 16, HERO_TILE + 3, METASPRITE_END
};

void player_reset(void) {
    g_player.x = 44;
    g_player.y = 88;
    g_player.hp = 3;
    g_player.invuln = 0;
    g_player.moving = 0;
    g_player.facing = 0;
    g_player.cooldown = 0;
    g_player.shot_on = 0;
    /* Fora da tela e nao "em (0,0)": um projetil parado no canto superior
     * esquerdo aparece no boot e falseia a captura de tela inicial. */
    g_player.shot_x = -32;
    g_player.shot_y = -32;
    g_player.shot_prev_x = -32;
}

void player_update(unsigned int keys) {
    g_player.moving = (keys & (PORT_A_KEY_LEFT | PORT_A_KEY_RIGHT |
                               PORT_A_KEY_UP | PORT_A_KEY_DOWN)) ? 1 : 0;

    if ((keys & PORT_A_KEY_LEFT) && g_player.x > FIELD_X0) {
        g_player.x -= WALK_SPEED;
        g_player.facing = 1;
    }
    if ((keys & PORT_A_KEY_RIGHT) && g_player.x < FIELD_X1) {
        g_player.x += WALK_SPEED;
        g_player.facing = 0;
    }
    if ((keys & PORT_A_KEY_UP) && g_player.y > FIELD_Y0) g_player.y -= WALK_SPEED;
    if ((keys & PORT_A_KEY_DOWN) && g_player.y < FIELD_Y1) g_player.y += WALK_SPEED;

    if (g_player.cooldown) g_player.cooldown--;
    if (g_player.invuln) g_player.invuln--;

    if ((keys & PORT_A_KEY_2) && !g_player.shot_on && !g_player.cooldown) {
        g_player.shot_on = 1;
        g_player.shot_x = g_player.x + HERO_W;
        g_player.shot_prev_x = g_player.shot_x;
        g_player.shot_y = g_player.y + 8;
        g_player.cooldown = SHOT_COOLDOWN;
        sfx_play(SFX_SHOT);
    }

    if (g_player.shot_on) {
        /* shot_prev_x guarda o inicio do segmento percorrido neste frame;
         * a colisao com o boss e varrida sobre ele, nunca so sobre a
         * posicao final — a 8px/frame o tiro atravessaria alvos finos. */
        g_player.shot_prev_x = g_player.shot_x;
        g_player.shot_x += SHOT_SPEED;
        if (g_player.shot_x > 248) g_player.shot_on = 0;
    }
}

void player_draw(void) {
    /* Pisca a cada 2 frames enquanto invulneravel: e o feedback de dano que
     * o GDD exige, e some por completo quando o jogo acaba. */
    if (g_state != ST_OVER && (!g_player.invuln || (g_frame & 1))) {
        /* A pose de ataque é selecionada pelo streaming do frame; o mesmo
         * metasprite mantém o recorte 2x2 e deixa o tiro independente dele. */
        if (g_player.shot_on || g_player.moving)
            SMS_addMetaSprite(g_player.x, g_player.y, (void *)hero_walk_meta);
        else
            SMS_addMetaSprite(g_player.x, g_player.y, (void *)hero_meta);
    }
    if (g_player.shot_on)
        SMS_addSprite(g_player.shot_x, g_player.shot_y, SHOT_TILE);
}
