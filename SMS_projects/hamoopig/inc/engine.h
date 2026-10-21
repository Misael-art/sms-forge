#ifndef HAMOOPIG_ENGINE_H
#define HAMOOPIG_ENGINE_H

#include "SMSlib.h"
#include "types.h"
#include "tech_gfx.h"

extern Fighter P[2];
extern unsigned char g_scene;
extern unsigned char g_scene_req;
extern unsigned int g_frame;
extern unsigned char g_clock;
extern unsigned char g_clock_div;
extern unsigned char g_hitstop;
extern unsigned char g_round;
extern unsigned char g_banner;
extern unsigned char g_banner_id;
extern unsigned char g_result;
extern unsigned char g_sel_p1;
extern unsigned char g_sel_p2;
extern unsigned char g_control[2];
extern unsigned int g_keys_raw;
extern unsigned char g_pause_armed;
extern unsigned char g_lock;

#define BN_NONE    0u
#define BN_ROUND   1u
#define BN_FIGHT   2u
#define BN_KO      3u
#define BN_DRAW    4u
#define BN_TIME    5u
#define BN_P1WIN   6u
#define BN_P2WIN   7u
#define RES_NONE   0u
#define RES_P1     1u
#define RES_P2     2u
#define RES_DRAW   3u

void scene_request(unsigned char id);
void scene_commit(void);
void scene_enter(unsigned char id);

void input_tick(unsigned int raw);
unsigned char input_status(unsigned char who, unsigned char btn);
unsigned char input_pressed(unsigned char who, unsigned char btn);
unsigned char input_held(unsigned char who, unsigned char btn);

void gfx_boot(void);
void gfx_clear_nametable(void);
void text_at(unsigned char col, unsigned char row, const char *s);
void text_num(unsigned char col, unsigned char row, unsigned char v);
void text_clear(unsigned char col, unsigned char row, unsigned char n);

void title_enter(void);
void title_update(void);
void title_present(void);
void opening_enter(void);
void opening_update(void);
void select_enter(void);
void select_update(void);
void select_present(void);

void fight_enter(void);
void fight_reset_round(void);
void fight_update(void);
void fight_present(void);
const FighterDef *fighter_def(unsigned char id);
void fighter_set_state(unsigned char who, unsigned int st);
void stream_init(void);
void stream_request(unsigned char who, unsigned char pose, unsigned char fr,
                    unsigned char flip);
void stream_prepare(void);
void stream_upload(void);
void stream_draw(void);
void stream_load_now(unsigned char who, unsigned char pose, unsigned char fr,
                     unsigned char flip);
unsigned char stream_busy(unsigned char who);
unsigned char stream_ready(unsigned char who);
void stream_present(unsigned char who);
unsigned char stream_frame(unsigned char who);
const AnimDef *anim_of(unsigned char id, unsigned char pose);
void audio_boot(void);
void audio_title(void);
void audio_fight(void);
void audio_tick(void);
void audio_hit(void);
void audio_shot(void);

void combat_begin_tick(void);
void combat_emit(unsigned char atk, unsigned char def, unsigned char kind,
                 unsigned char inst, unsigned char dmg, unsigned int st);
void combat_resolve(void);
unsigned char combat_count(void);

void hud_enter_fight(void);
void hud_draw(void);

void probe_init(void);
void probe_frame_end(unsigned int raw, unsigned char vline);
unsigned char fighter_qcf(unsigned char who);

extern volatile unsigned char __at(0xC7D0) probe_hist[8];
extern volatile unsigned char __at(0xC7D8) probe_hist_i;
extern volatile unsigned char __at(0xC7D9) probe_qcf;
extern volatile unsigned char __at(0xC7DA) probe_dir;
extern volatile unsigned char __at(0xC7DB) probe_fire;
extern volatile unsigned char __at(0xC7DC) probe_p2g;
extern volatile unsigned char __at(0xC7DD) probe_ctrl;

extern volatile unsigned char __at(0xC7E0) probe_magic0;
extern volatile unsigned char __at(0xC7E1) probe_magic1;
extern volatile unsigned char __at(0xC7E2) probe_magic2;
extern volatile unsigned char __at(0xC7E3) probe_magic3;
extern volatile unsigned char __at(0xC7E4) probe_schema;
extern volatile unsigned char __at(0xC7E5) probe_timer;
extern volatile unsigned char __at(0xC7E6) probe_atkwin;
extern volatile unsigned char __at(0xC7E7) probe_gap;
extern volatile unsigned char __at(0xC7E8) probe_hitstop;
extern volatile unsigned char __at(0xC7E9) probe_hitused;
extern volatile unsigned char __at(0xC7EA) probe_vline;
extern volatile unsigned int  __at(0xC7EB) probe_vovf;
extern volatile unsigned char __at(0xC7ED) probe_phase;
extern volatile unsigned char __at(0xC7EE) probe_missed;
extern volatile unsigned char __at(0xC7EF) probe_sp;
extern volatile unsigned int  __at(0xC7F0) probe_frame;
extern volatile unsigned char __at(0xC7F2) probe_hp;
extern volatile unsigned char __at(0xC7F3) probe_score;
extern volatile unsigned char __at(0xC7F4) probe_boss;
extern volatile unsigned char __at(0xC7F5) probe_over;
extern volatile unsigned char __at(0xC7F6) probe_state;
extern volatile unsigned char __at(0xC7F7) probe_wave;
extern volatile unsigned char __at(0xC7F8) probe_keys;
extern volatile unsigned char __at(0xC7F9) probe_pose;
extern volatile unsigned char __at(0xC7FA) probe_px;
extern volatile unsigned char __at(0xC7FB) probe_py;
extern volatile unsigned char __at(0xC7FC) probe_p2x;

#endif
