/* boss.c — o guardiao: FSM com fases, telegrafo e recuo.
 *
 * O comportamento anterior era `bx += 1 a cada 8 frames` e um salto vertical
 * de 8px por bit de frame — o jogador nao tinha o que ler nem o que antecipar.
 * Aqui cada disparo e precedido por um estado TELEGRAPH visivel, e a fase
 * (ligada ao HP) muda cadencia e leque de tiro.
 */
#include "game.h"

Boss g_boss;

#define BOSS_HP_MAX   12
#define BOSS_X_MIN    150
#define BOSS_X_MAX    184
#define BOSS_Y_MIN    40
#define BOSS_Y_MAX    104

/* 4 quadrantes de 16x16 tiles = 64x64 na tela, 16 sprites de hardware. */
static const signed char boss_meta[] = {
     0,  0, BOSS_TL_TILE,     16,  0, BOSS_TL_TILE + 1,
    32,  0, BOSS_TR_TILE,     48,  0, BOSS_TR_TILE + 1,
     0, 16, BOSS_TL_TILE + 2, 16, 16, BOSS_TL_TILE + 3,
    32, 16, BOSS_TR_TILE + 2, 48, 16, BOSS_TR_TILE + 3,
     0, 32, BOSS_BL_TILE,     16, 32, BOSS_BL_TILE + 1,
    32, 32, BOSS_BR_TILE,     48, 32, BOSS_BR_TILE + 1,
     0, 48, BOSS_BL_TILE + 2, 16, 48, BOSS_BL_TILE + 3,
    32, 48, BOSS_BR_TILE + 2, 48, 48, BOSS_BR_TILE + 3,
    METASPRITE_END
};
static const signed char boss_charge_meta[] = {
     0,  0, BOSS_TL_TILE,     16,  0, BOSS_TL_TILE + 1,
    32,  0, BOSS_TR_TILE,     48,  0, BOSS_TR_TILE + 1,
     0, 16, BOSS_TL_TILE + 2, 16, 16, BOSS_TL_TILE + 3,
    32, 16, BOSS_TR_TILE + 2, 48, 16, BOSS_TR_TILE + 3,
     0, 32, BOSS_BL_TILE,     16, 32, BOSS_BL_TILE + 1,
    32, 32, BOSS_BR_TILE,     48, 32, BOSS_BR_TILE + 1,
     0, 48, BOSS_BL_TILE + 2, 16, 48, BOSS_BL_TILE + 3,
    32, 48, BOSS_BR_TILE + 2, 48, 48, BOSS_BR_TILE + 3,
    METASPRITE_END
};

/* Cadencia por fase, em frames. Fase 0 e legivel; fase 2 pressiona. */
static const unsigned char idle_frames[3]      = { 90, 64, 44 };
static const unsigned char telegraph_frames[3] = { 36, 28, 22 };

void boss_reset(void) {
    g_boss.x = 168;
    g_boss.y = 64;
    g_boss.vy = 1;
    g_boss.hp = BOSS_HP_MAX;
    g_boss.hp_max = BOSS_HP_MAX;
    g_boss.st = BOSS_IDLE;
    g_boss.timer = idle_frames[0];
    g_boss.phase = 0;
    g_boss.flash = 0;
}

void boss_hit(void) {
    if (!g_boss.hp) return;
    g_boss.hp--;
    g_boss.flash = 8;
    /* Fase sobe em 2/3 e 1/3 do nucleo. Com HP_MAX=12: 8 e 4. */
    if (g_boss.hp <= (BOSS_HP_MAX / 3)) g_boss.phase = 2;
    else if (g_boss.hp <= (BOSS_HP_MAX * 2 / 3)) g_boss.phase = 1;
    if (!g_boss.hp) {
        g_boss.st = BOSS_DEAD;
        g_boss.timer = 60;
        sfx_play(SFX_DOWN);
    } else {
        g_boss.st = BOSS_HURT;
        g_boss.timer = 10;
        sfx_play(SFX_HIT);
    }
}

static void boss_fire(void) {
    signed int ox = g_boss.x - 16;
    signed int oy = g_boss.y + 24;
    /* Trajeto deliberadamente legível no modo ZOOMED: o orb percorre a
     * arena em mais frames, sem abrir mão da colisão swept no tiro do hero. */
    signed char speed = (signed char)(-3 - (signed char)g_boss.phase);

    ent_spawn_counter(ox, oy, speed, 0);
    /* Fase 1 abre um leque de 3; fase 2 mantem o leque e acelera a cadencia,
     * em vez de somar projeteis — somar estouraria o teto de 8 sprites por
     * scanline com o boss ja ocupando 4 colunas. */
    if (g_boss.phase >= 1) {
        ent_spawn_counter(ox, oy - 16, speed, -1);
        ent_spawn_counter(ox, oy + 16, speed, 1);
    }
}

void boss_update(void) {
    if (g_boss.flash) g_boss.flash--;
    if (g_boss.st == BOSS_DEAD) {
        if (g_boss.timer) g_boss.timer--;
        else g_state = ST_OVER;
        return;
    }
    if (g_boss.st == BOSS_HURT) {
        if (g_boss.timer) g_boss.timer--;
        else {
            g_boss.st = BOSS_IDLE;
            g_boss.timer = idle_frames[g_boss.phase];
        }
        return;
    }

    /* Vaivem vertical continuo de 1px/frame — movimento, nao teleporte. */
    g_boss.y += g_boss.vy;
    if (g_boss.y <= BOSS_Y_MIN) { g_boss.y = BOSS_Y_MIN; g_boss.vy = 1; }
    if (g_boss.y >= BOSS_Y_MAX) { g_boss.y = BOSS_Y_MAX; g_boss.vy = -1; }

    if (g_boss.timer) { g_boss.timer--; return; }

    switch (g_boss.st) {
    case BOSS_IDLE:
        g_boss.st = BOSS_TELEGRAPH;
        g_boss.timer = telegraph_frames[g_boss.phase];
        break;
    case BOSS_TELEGRAPH:
        boss_fire();
        g_boss.st = BOSS_FIRE;
        g_boss.timer = 6;
        break;
    case BOSS_FIRE:
        /* Recuo: o guardiao volta um passo, dando a janela de contra-ataque. */
        g_boss.x = BOSS_X_MAX;
        g_boss.st = BOSS_RECOIL;
        g_boss.timer = 12;
        break;
    default: /* BOSS_RECOIL */
        g_boss.x = BOSS_X_MIN + 18;
        g_boss.st = BOSS_IDLE;
        g_boss.timer = idle_frames[g_boss.phase];
        break;
    }
}

void boss_draw(void) {
    /* O impacto nao apaga o boss em frames alternados: isso era flicker sem
     * semantica e fazia o tiro parecer atravessar o alvo. O feedback agora e
     * o FX separado + hitstop, mantendo a silhueta do boss sempre presente. */
    if (g_boss.st == BOSS_TELEGRAPH)
        SMS_addMetaSprite(g_boss.x, g_boss.y, (void *)boss_charge_meta);
    else
        SMS_addMetaSprite(g_boss.x, g_boss.y, (void *)boss_meta);
}
