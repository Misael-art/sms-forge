#ifndef MOF_ALIS_CHAPTER_H
#define MOF_ALIS_CHAPTER_H
#include "duel_rules.h"

enum { MOF_ROUND, MOF_FIGHT_CALL, MOF_PLAY, MOF_RESULT };
enum { MOF_CONTINUE, MOF_NEXT_ROUND, MOF_REMATCH, MOF_MAIN_MENU };
typedef struct {
    uint8_t story, music, target, wins[2], phase, age, seconds, subsecond;
    uint8_t meter[2], idle[2], winner, expired, round;
    uint8_t combo[2];  /* hits by controller, for the HUD */
} MofChapter;
typedef struct {
    uint8_t intro_first, intro_count, ending_first, ending_count;
    uint8_t victory[2], defeat, arena_bank;
    uint16_t opening_song, battle_song, result_song;
    uint8_t listen_pose, victory_pose;
} MofChapterPresentation;

extern MofChapter chapter;
extern const MofChapterPresentation *mof_presentation;
#ifdef MOF_ALIS_MAGIC
/* One background per opponent; the attack supplies its own fixed-ROM callbacks. */
void mof_chapter_reaction(uint8_t target,uint8_t duration,void (*prepare)(void),void (*draw)(uint8_t));
#endif
void mof_chapter_select(const MofChapterPresentation *presentation);
#ifdef MOF_ALIS_MATCHUP
void menu_page(uint8_t page);
uint8_t menu_input(void);
void menu_title(void);
void menu_opening(void);
void menu_intro(void);
void mof_banked_menu(void);
uint8_t mof_matchup_keys(void);
void mof_matchup_pan(uint8_t timed);
#ifdef MOF_PALMA_VERSIONS
extern uint8_t mof_stage_choice;
void mof_camera_strip(uint8_t bank,const uint8_t *strip);
#endif
void mof_chapter_pair(uint8_t p1,uint8_t p2);
#endif
void mof_chapter_menu(void);
void mof_chapter_match(void);
void mof_chapter_round(void);
void mof_chapter_arena(void);
void mof_port_raster_start(void);
void mof_chapter_hud(uint8_t banner);
void mof_chapter_music(void);
void mof_chapter_theme(uint16_t song);
void mof_chapter_update(const MofDuel *duel);
uint8_t mof_chapter_result(void);
uint8_t mof_chapter_cpu(const MofDuel *duel);
void mof_chapter_spend_super(uint8_t player);
uint8_t mof_chapter_super_input(uint8_t player, uint8_t keys, uint8_t face, uint8_t free);
#endif
