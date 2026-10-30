#include <genesis.h>

#include "core/app.h"
#include "game_vars.h"
#include "scenes/fight_pause.h"
#include "scenes/fight_policy.h"
#include "mg/mg_runtime.h"
#include "system/fx_options.h"
#include "system/input.h"

enum { PAUSE_OFF = 0, PAUSE_MENU, PAUSE_FX };
enum { ITEM_CONTINUE = 0, ITEM_FX, ITEM_PANEL, ITEM_MENU };

static const char *const kLabels[4] = {
    "CONTINUAR", "EFEITOS/DEBUG", "PAINEL DO TREINO", "MENU PRINCIPAL"
};

static u8 sState;
static u8 sRow;
static FightPausePanelFn sPanel;

static u8 itemCount(void)
{
    return sPanel ? 4 : 3;
}

static u8 itemAt(u8 row)
{
    if (!sPanel && row >= ITEM_PANEL) return ITEM_MENU;
    return row;
}

static void drawMenu(void)
{
    char line[24];
    VDP_setEnable(FALSE);
    VDP_setTextPlane(BG_A);
    VDP_setTextPalette(PAL0);
    VDP_setTextPriority(TRUE);
    PAL_setColor(15, RGB24_TO_VDPCOLOR(0xEEEEFF));
    VDP_clearTextArea(2, 2, 36, 23);
    /* WINDOW owns rows 0..6; every pause-menu glyph stays below it. */
    VDP_drawText("PAUSA", 17, 7);
    for (u8 row = 0; row < itemCount(); row++) {
        sprintf(line, "%c %s", row == sRow ? '>' : ' ', kLabels[itemAt(row)]);
        VDP_drawTextFill(line, 11, (u16)(9 + row * 2), 20);
    }
    VDP_drawTextFill("A CONFIRMA   START CONTINUA", 6, 19, 30);
    VDP_setEnable(TRUE);
}

static void leave(void)
{
    sState = PAUSE_OFF;
    VDP_setTextPriority(FALSE);
}

static void close(void)
{
    VDP_setEnable(FALSE);
    VDP_setTextPlane(BG_A);
    VDP_clearTextArea(2, 2, 36, 23);
    VDP_setEnable(TRUE);
    leave();
    INPUT_suppressHeldUntilRelease(0);
    INPUT_suppressHeldUntilRelease(1);
}

void FIGHT_PAUSE_reset(void)
{
    sState = PAUSE_OFF;
    sPanel = 0;
}

bool FIGHT_PAUSE_active(void)
{
    return sState != PAUSE_OFF;
}

void FIGHT_PAUSE_open(FightPausePanelFn panel)
{
    MG_fightHideActors();
    sPanel = panel;
    sState = PAUSE_MENU;
    sRow = 0;
    drawMenu();
}

void FIGHT_PAUSE_update(void)
{
    const u16 pressed = (u16)(INPUT_padRawPressed(0) |
        ((FIGHT_POLICY_padMask(gApp.gameMode) & 2) ? INPUT_padRawPressed(1) : 0));
    if (sState == PAUSE_FX) {
        if (FXOPT_update(pressed)) {
            sState = PAUSE_MENU;
            drawMenu();
        }
        return;
    }
    if (pressed & (BUTTON_START | BUTTON_B)) {
        close();
        return;
    }
    if (pressed & (BUTTON_UP | BUTTON_DOWN)) {
        const u8 n = itemCount();
        sRow = (u8)((sRow + (pressed & BUTTON_UP ? n - 1 : 1)) % n);
        drawMenu();
        return;
    }
    if (!(pressed & (BUTTON_A | BUTTON_C))) return;
    switch (itemAt(sRow)) {
    case ITEM_FX:
        sState = PAUSE_FX;
        VDP_setEnable(FALSE);
        VDP_clearTextArea(2, 2, 36, 23);
        /* linhas 0..6 ficam sob o HUD (plano WINDOW): a lista comeca na 8 */
        VDP_drawText("EFEITOS/DEBUG", 13, 7);
        FXOPT_open(5, 8);
        VDP_setEnable(TRUE);
        break;
    case ITEM_PANEL:
        leave();
        if (sPanel) sPanel();
        break;
    case ITEM_MENU:
        leave();
        APP_changeScene(APP_SCENE_MENU);
        break;
    default:
        close();
        break;
    }
}
