#include <genesis.h>

#include "game_vars.h"
#include "system/input.h"

#if defined(MG_FRONTEND_SURVEY) && defined(MG_TEST_SCRIPT)
#error "MG_FRONTEND_SURVEY owns pad 1; do not combine with MG_TEST_SCRIPT"
#endif

#ifdef MG_FRONTEND_SURVEY
/* Diagnostic pad only. Product builds do not define MG_FRONTEND_SURVEY.
 * Each edge is one main-loop frame. The hold that follows is buttonless,
 * so the screen reached by that edge stays visible. */
static const u16 sSurveyFrameAt[] = {
    48, 89, 130, 171, 190, 231, 250, 291, 332, 373, 392, 411, 452, 471, 512,
    553, 594, 613, 632, 673, 692, 733, 774, 793, 834, 853, 894, 935, 954, 995,
    1014, 1055, 1096, 1115, 1156, 1197, 1268
};
static const u16 sSurveyButton[] = {
    BUTTON_START, BUTTON_A, BUTTON_A, BUTTON_B, BUTTON_B, BUTTON_DOWN, BUTTON_A,
    BUTTON_A, BUTTON_A, BUTTON_B, BUTTON_B, BUTTON_B, BUTTON_DOWN, BUTTON_A,
    BUTTON_A, BUTTON_A, BUTTON_B, BUTTON_B, BUTTON_B, BUTTON_DOWN, BUTTON_A,
    BUTTON_A, BUTTON_B, BUTTON_B, BUTTON_DOWN, BUTTON_A, BUTTON_A, BUTTON_B,
    BUTTON_B, BUTTON_DOWN, BUTTON_A, BUTTON_B, BUTTON_DOWN, BUTTON_A, BUTTON_A,
    BUTTON_A, BUTTON_A
};
enum { SURVEY_EDGES = sizeof(sSurveyFrameAt) / sizeof(sSurveyFrameAt[0]) };
static volatile u16 sSurveyMark[4 + (4 * 40)];

static u16 surveyButton(u16 frame)
{
    u16 i;
    for (i = 0; i < SURVEY_EDGES; i++) {
        if (sSurveyFrameAt[i] == frame) return sSurveyButton[i];
        if (sSurveyFrameAt[i] > frame) break;
    }
    return 0;
}

static void surveyRemember(u16 frame, u16 button)
{
    u16 slot;
    sSurveyMark[0] = 0x4653;
    sSurveyMark[1] = 0x5631;
    sSurveyMark[2] = frame;
    if (!button) return;
    slot = sSurveyMark[3];
    if (slot >= 40) return;
    sSurveyMark[4 + (slot * 4) + 0] = frame;
    sSurveyMark[4 + (slot * 4) + 1] = (u16)gApp.currentScene;
    sSurveyMark[4 + (slot * 4) + 2] = (u16)gApp.gameMode;
    sSurveyMark[4 + (slot * 4) + 3] = button;
    sSurveyMark[3] = (u16)(slot + 1);
}
#endif

static u16 sPrevState = 0;
static u16 sPrevState2 = 0;

enum { INPUT_PAD_COUNT = 2, INPUT_ACTION_BUTTON_COUNT = 6 };

static const u16 sActionButtons[INPUT_ACTION_BUTTON_COUNT] = {
    BUTTON_A, BUTTON_B, BUTTON_C, BUTTON_X, BUTTON_Y, BUTTON_Z
};
static const u16 sActionButtonMask =
    BUTTON_A | BUTTON_B | BUTTON_C | BUTTON_X | BUTTON_Y | BUTTON_Z;
static const u16 sThreeButtonMask = BUTTON_A | BUTTON_B | BUTTON_C;
static u16 sActionBindings[INPUT_PAD_COUNT][INPUT_ACTION_BUTTON_COUNT];
static u16 sRawHeld[INPUT_PAD_COUNT];
static u16 sActionHeld[INPUT_PAD_COUNT];
static u16 sActionPressed[INPUT_PAD_COUNT];
static u16 sActionReleased[INPUT_PAD_COUNT];
static u16 sSuppressedPhysical[INPUT_PAD_COUNT];

static u8 actionButtonIndex(u16 buttonMask)
{
    u8 i;
    for (i = 0; i < INPUT_ACTION_BUTTON_COUNT; i++)
        if (sActionButtons[i] == buttonMask) return i;
    return INPUT_ACTION_BUTTON_COUNT;
}

static u16 mappedActionState(u8 pad, u16 physicalState)
{
    u8 i;
    u16 logicalState = physicalState & (u16)~sActionButtonMask;
    for (i = 0; i < INPUT_ACTION_BUTTON_COUNT; i++) {
        const u16 physicalButton = sActionBindings[pad][i];
        if (physicalButton && (physicalState & physicalButton))
            logicalState |= sActionButtons[i];
    }
    return logicalState;
}

static void rebaseActionState(u8 pad)
{
    const u16 activePhysical = sRawHeld[pad] & (u16)~sSuppressedPhysical[pad];
    sActionHeld[pad] = mappedActionState(pad, activePhysical);
    sActionPressed[pad] = 0;
    sActionReleased[pad] = 0;
}

static void updateActionState(u8 pad, u16 physicalState)
{
    u16 logicalState;
    sRawHeld[pad] = physicalState;
    sSuppressedPhysical[pad] &= physicalState;
    logicalState = mappedActionState(
        pad, physicalState & (u16)~sSuppressedPhysical[pad]);
    sActionPressed[pad] = logicalState & (u16)~sActionHeld[pad];
    sActionReleased[pad] = sActionHeld[pad] & (u16)~logicalState;
    sActionHeld[pad] = logicalState;
}

static u16 availablePhysicalButtons(u8 pad)
{
    const bool sixButton = pad ? gInput.sixButton2 : gInput.sixButton;
    return sixButton ? sActionButtonMask : sThreeButtonMask;
}

void INPUT_init(void)
{
    u8 pad, i;
    JOY_setSupport(PORT_1, JOY_SUPPORT_6BTN);
    JOY_setSupport(PORT_2, JOY_SUPPORT_6BTN);
    sPrevState = 0;
    sPrevState2 = 0;
    gInput.held = 0;
    gInput.pressed = 0;
    gInput.released = 0;
    gInput.held2 = 0;
    gInput.pressed2 = 0;
    gInput.released2 = 0;
    gInput.sixButton = (JOY_getJoypadType(JOY_1) == JOY_TYPE_PAD6);
    gInput.sixButton2 = (JOY_getJoypadType(JOY_2) == JOY_TYPE_PAD6);
    for (pad = 0; pad < INPUT_PAD_COUNT; pad++) {
        sRawHeld[pad] = 0;
        sActionHeld[pad] = 0;
        sActionPressed[pad] = 0;
        sActionReleased[pad] = 0;
        sSuppressedPhysical[pad] = 0;
        for (i = 0; i < INPUT_ACTION_BUTTON_COUNT; i++)
            sActionBindings[pad][i] = sActionButtons[i];
    }
}

void INPUT_update(void)
{
    u16 current;
#ifdef MG_FRONTEND_SURVEY
    static u16 sSurveyFrame = 0;
    current = surveyButton(sSurveyFrame);
    surveyRemember(sSurveyFrame, current);
    if (sSurveyFrame != 0xFFFF) sSurveyFrame++;
#else
    current = JOY_readJoypad(JOY_1);
#endif
    gInput.pressed = current & ~sPrevState;
    gInput.released = sPrevState & ~current;
    gInput.held = current;
    sPrevState = current;
    gInput.sixButton = (JOY_getJoypadType(JOY_1) == JOY_TYPE_PAD6);
    updateActionState(0, current);

    current = JOY_readJoypad(JOY_2);
    gInput.pressed2 = current & ~sPrevState2;
    gInput.released2 = sPrevState2 & ~current;
    gInput.held2 = current;
    sPrevState2 = current;
    gInput.sixButton2 = (JOY_getJoypadType(JOY_2) == JOY_TYPE_PAD6);
    updateActionState(1, current);
}

bool INPUT_setActionBinding(u8 pad, u16 logicalButton, u16 physicalButton)
{
    u8 target, physicalOwner = INPUT_ACTION_BUTTON_COUNT, i;
    u16 oldPhysical;
    if (pad >= INPUT_PAD_COUNT) return FALSE;
    target = actionButtonIndex(logicalButton);
    if (target >= INPUT_ACTION_BUTTON_COUNT ||
        actionButtonIndex(physicalButton) >= INPUT_ACTION_BUTTON_COUNT ||
        !(availablePhysicalButtons(pad) & physicalButton)) return FALSE;

    oldPhysical = sActionBindings[pad][target];
    for (i = 0; i < INPUT_ACTION_BUTTON_COUNT; i++) {
        if ((i != target) && (sActionBindings[pad][i] == physicalButton)) {
            physicalOwner = i;
            break;
        }
    }
    if (physicalOwner < INPUT_ACTION_BUTTON_COUNT)
        sActionBindings[pad][physicalOwner] = oldPhysical;
    sActionBindings[pad][target] = physicalButton;

    /* The button used to confirm a bind must be released before it can act. */
    sSuppressedPhysical[pad] |= sRawHeld[pad] & sActionButtonMask;
    rebaseActionState(pad);
    return TRUE;
}

bool INPUT_resetActionBindings(u8 pad)
{
    u8 i;
    if (pad >= INPUT_PAD_COUNT) return FALSE;
    for (i = 0; i < INPUT_ACTION_BUTTON_COUNT; i++)
        sActionBindings[pad][i] = sActionButtons[i];
    sSuppressedPhysical[pad] |= sRawHeld[pad] & sActionButtonMask;
    rebaseActionState(pad);
    return TRUE;
}

void INPUT_suppressHeldUntilRelease(u8 pad)
{
    if (pad >= INPUT_PAD_COUNT) return;
    sSuppressedPhysical[pad] |= sRawHeld[pad];
    rebaseActionState(pad);
}

u16 INPUT_getActionBinding(u8 pad, u16 logicalButton)
{
    u8 index;
    if (pad >= INPUT_PAD_COUNT) return 0;
    index = actionButtonIndex(logicalButton);
    if (index >= INPUT_ACTION_BUTTON_COUNT) return 0;
    return sActionBindings[pad][index];
}

u16 INPUT_padRawHeld(u8 pad)
{
    if (pad == 0) return gInput.held;
    if (pad == 1) return gInput.held2;
    return 0;
}

u16 INPUT_padRawPressed(u8 pad)
{
    if (pad == 0) return gInput.pressed;
    if (pad == 1) return gInput.pressed2;
    return 0;
}

u16 INPUT_padRawReleased(u8 pad)
{
    if (pad == 0) return gInput.released;
    if (pad == 1) return gInput.released2;
    return 0;
}

u16 INPUT_padActionHeld(u8 pad)
{
    return pad < INPUT_PAD_COUNT ? sActionHeld[pad] : 0;
}

u16 INPUT_padActionPressed(u8 pad)
{
    return pad < INPUT_PAD_COUNT ? sActionPressed[pad] : 0;
}

u16 INPUT_padActionReleased(u8 pad)
{
    return pad < INPUT_PAD_COUNT ? sActionReleased[pad] : 0;
}

bool INPUT_padHasSixButton(u8 pad)
{
    if (pad == 0) return gInput.sixButton;
    if (pad == 1) return gInput.sixButton2;
    return FALSE;
}

u16 INPUT_padHeld(u8 pad)
{
    return INPUT_padRawHeld(pad);
}

bool INPUT_pressed(u16 buttonMask)
{
    return (gInput.pressed & buttonMask) != 0;
}

bool INPUT_held(u16 buttonMask)
{
    return (gInput.held & buttonMask) != 0;
}

bool INPUT_released(u16 buttonMask)
{
    return (gInput.released & buttonMask) != 0;
}

bool INPUT_hasSixButtonPad(void)
{
    return INPUT_padHasSixButton(0);
}
