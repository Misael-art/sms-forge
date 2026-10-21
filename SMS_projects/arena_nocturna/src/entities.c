/* entities.c — pools fixos de contra-ataques e de FX.
 *
 * Pool com teto declarado, nunca alocacao: o pior caso de sprites por
 * scanline precisa ser calculavel em tempo de leitura do codigo, senao o
 * gate audit_sprite_line_sim nao tem o que verificar.
 */
#include "game.h"

Counter g_counter[MAX_COUNTERS];
Fx      g_fx[MAX_FX];

#define COUNTER_SZ 16
void ent_reset(void) {
    unsigned char i;
    for (i = 0; i < MAX_COUNTERS; i++) {
        g_counter[i].on = 0;
        g_counter[i].x = -32; g_counter[i].y = -32;
        g_counter[i].vx = 0;  g_counter[i].vy = 0;
    }
    for (i = 0; i < MAX_FX; i++) {
        g_fx[i].on = 0; g_fx[i].timer = 0;
        g_fx[i].x = -32; g_fx[i].y = -32;
    }
}

unsigned char ent_spawn_counter(signed int x, signed int y,
                                signed char vx, signed char vy) {
    unsigned char i;
    for (i = 0; i < MAX_COUNTERS; i++) {
        if (g_counter[i].on) continue;
        g_counter[i].on = 1;
        g_counter[i].x = x; g_counter[i].y = y;
        g_counter[i].vx = vx; g_counter[i].vy = vy;
        return 1;
    }
    /* Pool cheio: o disparo e simplesmente descartado. Preferir descartar a
     * reciclar o mais antigo — reciclar faz o projetil sumir na cara do
     * jogador, que e um dano injusto e invisivel. */
    return 0;
}

void ent_spawn_fx(signed int x, signed int y) {
    unsigned char i;
    for (i = 0; i < MAX_FX; i++) {
        if (g_fx[i].on) continue;
        g_fx[i].on = 1; g_fx[i].timer = FX_FRAMES;
        g_fx[i].x = x; g_fx[i].y = y;
        return;
    }
}

void ent_update(void) {
    unsigned char i;
    for (i = 0; i < MAX_COUNTERS; i++) {
        if (!g_counter[i].on) continue;
        g_counter[i].x += g_counter[i].vx;
        g_counter[i].y += g_counter[i].vy;
        if (g_counter[i].x < -COUNTER_SZ || g_counter[i].y < -COUNTER_SZ ||
            g_counter[i].y > 192) {
            g_counter[i].on = 0;
            continue;
        }
        if (g_player.invuln) continue;
        if (g_counter[i].x < g_player.x + HERO_W &&
            g_counter[i].x + COUNTER_SZ > g_player.x &&
            g_counter[i].y < g_player.y + HERO_H &&
            g_counter[i].y + COUNTER_SZ > g_player.y) {
            g_counter[i].on = 0;
            if (g_player.hp) g_player.hp--;
            g_player.invuln = 60;
            g_hitstop = 6;
            ent_spawn_fx(g_player.x + 8, g_player.y + 8);
            sfx_play(SFX_HURT);
            hud_mark();
            if (!g_player.hp) g_state = ST_OVER;
        }
    }

    /* O FX so envelhece fora do hitstop: durante a congelada o impacto tem
     * de permanecer na tela, que e exatamente o efeito procurado. */
    if (g_hitstop) return;
    for (i = 0; i < MAX_FX; i++) {
        if (!g_fx[i].on) continue;
        if (g_fx[i].timer) g_fx[i].timer--;
        else g_fx[i].on = 0;
    }
}

void ent_draw(void) {
    unsigned char i;
    for (i = 0; i < MAX_COUNTERS; i++)
        if (g_counter[i].on)
            SMS_addSprite(g_counter[i].x, g_counter[i].y, COUNTER_TILE);
    for (i = 0; i < MAX_FX; i++)
        if (g_fx[i].on)
            SMS_addSprite(g_fx[i].x, g_fx[i].y, IMPACT_TILE);
}
