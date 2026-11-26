#ifndef MOF_ALIS_MAGIC_H
#define MOF_ALIS_MAGIC_H
#include "alis_chapter.h"

/* Standalone chapter extension. IDs live outside the engine's 16-bit normal mask. */
enum MofSpell { SPELL_NONE, FIRE_TAP, FIRE_HOLD, TWIN_FIRE, MYAU, REST, SLASH,
                SABER, CHAT, MIRROR, STUN, GUARDIANS, SPELL_COUNT };
enum MofGlyph { GL_FIRE, GL_WAVE, GL_SABER, GL_NUT, GL_WING, GL_DIVE, GL_REST, GL_STARS, GL_MIRROR };
typedef struct {
    uint8_t move, age, face, previous, history[6], window, pending, held_button;
    uint8_t dizzy, stun_used, chat_wait, strain, strain_window, pose;
} MofCaster;
typedef struct {
    int16_t x;
    int8_t dx;
    uint8_t y, owner, kind, age, ttl, phase, damage;
} MofShot;
typedef struct { uint16_t cell, restore, address; uint8_t bank; } MofMagicTile;
#define MAGIC_TILES 16
typedef struct {
    MofCaster caster[2];
    MofShot shots[4];
    uint8_t pad[2], locked[2], live_step, finisher, scene, audio, count, old_count;
    uint8_t events[2][SPELL_COUNT], hits[2], blocks[2], reflects[2], full_range, last_y[2];
    MofMagicTile next[MAGIC_TILES], old[MAGIC_TILES];
    uint8_t target_fighter, busy, upload[MAGIC_TILES], write_count;
    struct {uint16_t cell,tile;} writes[MAGIC_TILES*2];
} MofMagic;
/* Cartridge-private work RAM C900..CAFF. Stack descends from DFF0.
   The symbol is absolute in the linker map, outside the C770..C7F1 probes. */
extern MofMagic mof_magic;
void mof_magic_reset(void);
void mof_magic_input(const MofDuel *duel,uint8_t one,uint8_t two);
void mof_magic_step(MofDuel *duel);
void mof_magic_plan(const MofDuel *duel, uint8_t apron_scroll);
void mof_magic_hurt(const MofDuel *duel,uint8_t player,MofDuelBox *box);
void mof_magic_tiles(const uint8_t *blades,uint8_t length,uint16_t first);
void mof_magic_publish(void);
void mof_magic_sound(void);
void mof_magic_victory(void);
#endif
