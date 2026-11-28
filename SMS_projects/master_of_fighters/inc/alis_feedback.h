#ifndef MOF_ALIS_FEEDBACK_H
#define MOF_ALIS_FEEDBACK_H
#include "duel_rules.h"

/* C800..C87F lies between the published duel probes and the spell state.
   Each label saves its two original PNT entries. Tiles 268..271 follow
   the 12 arena base tiles and end before the life patterns at 272. */
typedef struct {
    uint16_t loc, background;
    uint8_t used;
} MofFeedbackCell;
typedef struct {
    uint8_t remaining, duration, participants, presented;
    uint8_t label[2], age[2], amount[2], last_gain[2];
    uint8_t palette[16], dark[16], light, shadow;
    MofFeedbackCell cells[4];
    uint16_t sampled_pad;
    uint8_t shown[2]; /* pose and facing packed in the resident SAT frame */
} MofFeedback;
#define mof_feedback (*(MofFeedback *)0xc800u)
#define MOF_GAIN_HP 1u
#define MOF_GAIN_MP 2u
#define MOF_SFX_HP  20u
#define MOF_SFX_MP  21u
void mof_feedback_frame(const MofDuel *duel);
void mof_feedback_pause(const MofDuel *duel);
void mof_feedback_present(const MofDuel *duel);
void mof_feedback_clear(void);
void mof_feedback_audio(void);
void mof_feedback_wait(const MofDuel *duel);
void mof_feedback_init(void);
#endif
