/* main.c -- integrated runtime: 72-88 px Ken vs Ryu, static stage, HUD
 * on the name table, PSG and a best-of-three round cycle.
 *
 * Button 1 = punch, button 2 = guard; directions stay masked.
 * P1 = port A, P2 = port B.
 * Round: 99 seconds x 60 NTSC ROM frames (GDD 2026-09-30). Tie and
 * double KO score nobody. The anim clock and the stream budget are the
 * Lote B ones; this file does not treat that latency as acceptable.
 *
 * Telemetry at 0xC7A0.. (DAP). probe_over remains P2 state.
 * 0xC7F7 is the round number; the factory snapshot still labels it wave.
 * 0xC7F3 counts life drops. 0xC7FE is P1 wins in the high nibble.
 * 0xC7FF is the round timer in seconds.
 */
#include "SMSlib.h"
#include "luta.h"
#include "fight.h"
#include "stream.h"
#include "stage.h"
#include "hud.h"
#include "audio.h"
#include "trace_hooks.h"

SMS_EMBED_SEGA_ROM_HEADER(0, 0);

#define WORST_FRAME_WINDOW 3000u
#define RM_ROUND  0u
#define RM_FIGHT  1u
#define RM_ACTIVE 2u
#define RM_RESULT 3u
#define RM_MATCH  4u
#define ROUND_FPS 60u
#define ROUND_SECONDS 99u
#define ROUND_FRAMES 90u
#define FIGHT_FRAMES 60u
#define RESULT_FRAMES 120u

__sfr __at (0x7e) SMS_VCounterPort;

volatile unsigned char __at(0xC7E0) probe_magic0;
volatile unsigned char __at(0xC7E1) probe_magic1;
volatile unsigned char __at(0xC7E2) probe_magic2;
volatile unsigned char __at(0xC7E3) probe_magic3;
volatile unsigned char __at(0xC7E4) probe_schema;
volatile unsigned char __at(0xC7EA) probe_vline;
volatile unsigned int  __at(0xC7EB) probe_vovf;
volatile unsigned char __at(0xC7ED) probe_phase;
volatile unsigned char __at(0xC7EE) probe_worst_done;
volatile unsigned char __at(0xC7EF) probe_vline_min;
volatile unsigned int  __at(0xC7F0) probe_frame;
volatile unsigned char __at(0xC7D0) probe_profile_wait;
volatile unsigned char __at(0xC7D1) probe_profile_stream;
volatile unsigned char __at(0xC7D2) probe_profile_palette;
volatile unsigned char __at(0xC7D3) probe_profile_hud;
volatile unsigned char __at(0xC7D4) probe_profile_sat;
volatile unsigned char __at(0xC7D6) probe_vline_spill_max;
volatile unsigned char __at(0xC7F2) probe_hp;
volatile unsigned char __at(0xC7F3) probe_score;
volatile unsigned char __at(0xC7F4) probe_boss;
volatile unsigned char __at(0xC7F5) probe_over;
volatile unsigned char __at(0xC7F6) probe_state;
volatile unsigned char __at(0xC7F7) probe_round;
volatile unsigned char __at(0xC7F8) probe_keys;
volatile unsigned char __at(0xC7FE) probe_round_score;
volatile unsigned char __at(0xC7FF) probe_timer;

volatile unsigned char __at(0xC7A0) tl_lat_accept[2];
volatile unsigned char __at(0xC7A2) tl_lat_visible[2];
volatile unsigned char __at(0xC7A4) tl_lat_hitbox[2];
volatile unsigned char __at(0xC7A6) tl_lat_visible_max[2];
volatile unsigned char __at(0xC7A8) tl_lat_hitbox_max[2];
volatile unsigned char __at(0xC7AA) tl_presses[2];
volatile unsigned char __at(0xC7AC) tl_dur_hist[2][4];
volatile unsigned char __at(0xC7B4) tl_slots_used;
volatile unsigned char __at(0xC7B5) tl_slots_peak;
volatile unsigned char __at(0xC7B6) tl_alloc_fail;
volatile unsigned char __at(0xC7B7) tl_dropped;
volatile unsigned char __at(0xC7B8) tl_render_dropped_max;
volatile unsigned char __at(0xC7B9) tl_logic_end;
volatile unsigned char __at(0xC7BA) tl_render_end;
volatile unsigned char __at(0xC7BB) tl_render_end_max;
volatile unsigned char __at(0xC7BC) tl_magic;
volatile unsigned char __at(0xC7BD) tl_ph_track;
volatile unsigned char __at(0xC7BE) tl_ph_step0;
volatile unsigned char __at(0xC7BF) tl_ph_step1;
volatile unsigned char __at(0xC790) tl_snap[10];
volatile unsigned char __at(0xC79A) tl_snap_seq;

extern unsigned char render_dropped;

static unsigned char track_on[2], track_t[2], track_pose0[2];
static unsigned char track_vis_done[2], track_hit_done[2], track_state[2];
static unsigned char keys_prev[2];
static unsigned char vis_pose[2], vis_frames[2], vis_dur[2];

static unsigned char rm_state, rm_wait, rm_timer_s, rm_ticks;
static unsigned char rm_winner, rm_scored, rm_round, match_prev;
static unsigned char rm_wins[2];
static unsigned char probe_ready;

static unsigned char read_pad(unsigned char who) {
    unsigned int h = SMS_getKeysHeld();
    unsigned char k = 0;
    if (who) {
        if (h & PORT_B_KEY_1) k |= K_LP;
        if (h & PORT_B_KEY_2) k |= K_GUARD;
    } else {
        if (h & PORT_A_KEY_1) k |= K_LP;
        if (h & PORT_A_KEY_2) k |= K_GUARD;
    }
    return k;
}

static void track_after_sat(unsigned char who) {
    unsigned char pose = fight_visible_pose(who);
    unsigned char delta;
    if (pose == vis_pose[who]) {
        if (vis_frames[who] < 255u) vis_frames[who]++;
    } else {
        if (vis_dur[who] != 255u && vis_frames[who]) {
            delta = vis_frames[who] > vis_dur[who] ? vis_frames[who] - vis_dur[who] : 0;
            tl_dur_hist[who][delta > 3u ? 3u : delta]++;
        }
        vis_pose[who] = pose;
        vis_frames[who] = 1;
        vis_dur[who] = fight_visible_dur(who);
    }
    if (!track_on[who]) return;
    if (!track_vis_done[who] && pose == track_pose0[who]) {
        track_vis_done[who] = 1;
        tl_lat_visible[who] = track_t[who];
        if (track_t[who] > tl_lat_visible_max[who]) tl_lat_visible_max[who] = track_t[who];
    }
    if (track_vis_done[who] && !track_hit_done[who] && track_state[who] == 1u &&
        fight_visible_hitbox(who)) {
        track_hit_done[who] = 1;
        tl_lat_hitbox[who] = track_t[who];
        if (track_t[who] > tl_lat_hitbox_max[who]) tl_lat_hitbox_max[who] = track_t[who];
    }
    if (track_vis_done[who] && (track_hit_done[who] || track_state[who] != 1u))
        track_on[who] = 0;
    else if (track_t[who] < 250u)
        track_t[who]++;
    else
        track_on[who] = 0;
}

static void track_input(unsigned char who, unsigned char k, unsigned char ev,
                        unsigned char state_before) {
    unsigned char pressed = (unsigned char)(k & ~keys_prev[who]);
    keys_prev[who] = k;
    if (!pressed) return;
    if (fighters[who].state == state_before) return;
    tl_presses[who]++;
    track_on[who] = 1;
    track_t[who] = 0;
    track_vis_done[who] = track_hit_done[who] = 0;
    track_state[who] = (unsigned char)(ev == FIGHT_EVENT_PUNCH ? 1u : 2u);
    track_pose0[who] = fight_state_pose0(who);
    tl_lat_accept[who] = 0;
}

static void sample_worst_frame(void) {
    unsigned char vline;
    probe_phase = 2;
    vline = SMS_VCounterPort;
    if (!probe_worst_done) {
        probe_vline = vline;
        if (vline < probe_vline_min) probe_vline_min = vline;
        if (vline < 0xC0u) probe_vovf++;
        if (vline < 0xC0u && vline > probe_vline_spill_max)
            probe_vline_spill_max = vline;
        if (probe_frame == (WORST_FRAME_WINDOW - 1u)) probe_worst_done = 1;
    }
    probe_frame++;
    probe_phase = 3;
}

static void note_hit(void) {
    if (probe_score < 255u) probe_score++;
}

static void enter_result(unsigned char winner, unsigned char banner) {
    rm_state = RM_RESULT;
    rm_wait = RESULT_FRAMES;
    rm_winner = winner;
    rm_scored = 0;
    hud_set_banner(banner);
}

static unsigned char round_leader(void) {
    if (fighters[0].life > fighters[1].life) return 0;
    if (fighters[1].life > fighters[0].life) return 1;
    return 2;
}

static void reset_round(void) {
    SMS_displayOff();
    fight_reset(&fighters[0], 0);
    fight_reset(&fighters[1], 1);
    fight_draw();
    sat_upload();
    fight_sat_copied();
    rm_round++;
    rm_timer_s = ROUND_SECONDS;
    rm_ticks = 0;
    rm_state = RM_ROUND;
    rm_wait = ROUND_FRAMES;
    rm_winner = 2;
    rm_scored = 0;
    track_on[0] = track_on[1] = 0;
    hud_set_life(0, fighters[0].life, fight_max_life(0));
    hud_set_life(1, fighters[1].life, fight_max_life(1));
    hud_set_timer(rm_timer_s);
    hud_set_score(0, rm_wins[0]);
    hud_set_score(1, rm_wins[1]);
    hud_set_banner(BANNER_ROUND);
    hud_flush_all();
    audio_round();
    audio_frame();
    SMS_waitForVBlank();
    if (probe_ready) {
        probe_frame++;
        probe_phase = 3u;
    }
    SMS_displayOn();
}

static void finish_result(void) {
    if (!rm_scored) {
        rm_scored = 1;
        if (rm_winner < 2u) {
            rm_wins[rm_winner]++;
            hud_set_score(0, rm_wins[0]);
            hud_set_score(1, rm_wins[1]);
        }
    }
    if (rm_wins[0] >= 2u || rm_wins[1] >= 2u) {
        rm_state = RM_MATCH;
        match_prev = 0xFFu;
        hud_set_winner(rm_wins[0] >= 2u ? 0u : 1u);
    } else {
        reset_round();
    }
}

void main(void) {
    unsigned char i, k[2], ev[2], before[2];
    unsigned short life_before[2];

    probe_ready = 0;
    SMS_displayOff();
    SMS_init();
    SMS_VRAMmemsetW(0x0000u, 0x0000u, 16384u);
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_useFirstHalfTilesforSprites(1);
    sat_setup();
    fight_upload_palette();
    stage_load();
    audio_init();

    for (i = 0; i < 2; i++) {
        tl_lat_accept[i] = tl_lat_visible[i] = tl_lat_hitbox[i] = 0;
        tl_lat_visible_max[i] = tl_lat_hitbox_max[i] = tl_presses[i] = 0;
        tl_dur_hist[i][0] = tl_dur_hist[i][1] = tl_dur_hist[i][2] = tl_dur_hist[i][3] = 0;
        track_on[i] = 0;
        keys_prev[i] = 0;
        vis_pose[i] = 0xFFu;
        vis_frames[i] = 0;
        vis_dur[i] = 255u;
        rm_wins[i] = 0;
    }
    tl_render_dropped_max = tl_render_end_max = 0;
    rm_round = 0;

    fight_init();
    hud_init();
    reset_round();

    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 1;
    probe_ready = 1;
    probe_vline = 0;
    probe_vovf = 0;
    probe_phase = 0;
    probe_worst_done = 0;
    probe_vline_min = 0xff;
    probe_frame = 0;
    probe_vline_spill_max = 0;
    probe_score = 0;
    tl_magic = 'I';

    for (;;) {
        SMS_waitForVBlank();
        probe_profile_wait = SMS_VCounterPort;
        hud_flush();
        probe_profile_hud = SMS_VCounterPort;
        sat_upload();
        fight_sat_copied();
        probe_profile_sat = SMS_VCounterPort;
        if (fight_skip_stream())
            probe_profile_stream = SMS_VCounterPort;
        else {
            stream_step();
            probe_profile_stream = SMS_VCounterPort;
        }
        sample_worst_frame();
        /* release() só devolve slots na RAM (~35 linhas com os dois
         * lutadores). Depois de um stream que parou em >= 0xE0 isso
         * atravessava a linha 0 e o probe contava derrame de VRAM. */
        stream_reclaim();

        track_after_sat(0);
        track_after_sat(1);
        tl_ph_track = SMS_VCounterPort;

        k[0] = TRACE_PAD(0, read_pad(0));
        k[1] = TRACE_PAD(1, read_pad(1));
        if (rm_state == RM_ACTIVE) {
            for (i = 0; i < 2; i++) {
                before[i] = fighters[i].state;
                life_before[i] = fighters[i].life;
            }
            ev[0] = fight_step(&fighters[0], k[0], k[1]);
            tl_ph_step0 = SMS_VCounterPort;
            ev[1] = fight_step(&fighters[1], k[1], k[0]);
            tl_ph_step1 = SMS_VCounterPort;
            TRACE_RECORD();
            track_input(0, k[0], ev[0], before[0]);
            track_input(1, k[1], ev[1], before[1]);
            if (ev[0] == FIGHT_EVENT_PUNCH) audio_punch();
            if (ev[1] == FIGHT_EVENT_PUNCH) audio_punch();
            if (fighters[0].life != life_before[0])
                hud_set_life(0, fighters[0].life, fight_max_life(0));
            if (fighters[1].life != life_before[1])
                hud_set_life(1, fighters[1].life, fight_max_life(1));
            if (fighters[0].life < life_before[0]) note_hit();
            if (fighters[1].life < life_before[1]) note_hit();
            if (fighters[0].life == 0 || fighters[1].life == 0) {
                if (fighters[0].life == 0) fight_set_ko(&fighters[0]);
                if (fighters[1].life == 0) fight_set_ko(&fighters[1]);
                if (fighters[0].life == 0 && fighters[1].life == 0)
                    enter_result(2, BANNER_KO);
                else if (fighters[0].life == 0)
                    enter_result(1, BANNER_KO);
                else
                    enter_result(0, BANNER_KO);
                audio_ko();
            } else {
                if (fighters[0].life < life_before[0] ||
                    fighters[1].life < life_before[1])
                    audio_hit();
                rm_ticks++;
                if (rm_ticks >= ROUND_FPS) {
                    rm_ticks = 0;
                    if (rm_timer_s) rm_timer_s--;
                    hud_set_timer(rm_timer_s);
                    if (rm_timer_s == 0)
                        enter_result(round_leader(), BANNER_TIME);
                }
            }
        } else {
            fighters[0].keys_prev = k[0];
            fighters[1].keys_prev = k[1];
            tl_ph_step0 = tl_ph_step1 = SMS_VCounterPort;
            if (rm_state == RM_MATCH) {
                if ((k[0] & (unsigned char)~match_prev) & K_LP) {
                    rm_wins[0] = rm_wins[1] = 0;
                    rm_round = 0;
                    match_prev = k[0];
                    reset_round();
                } else {
                    match_prev = k[0];
                }
            }
        }
        tl_logic_end = SMS_VCounterPort;

        fight_draw();
        tl_render_end = SMS_VCounterPort;
        if (tl_render_end < 0xC0u && tl_render_end > tl_render_end_max)
            tl_render_end_max = tl_render_end;
        if (render_dropped > tl_render_dropped_max) tl_render_dropped_max = render_dropped;
        audio_frame();

        tl_snap[0] = probe_profile_stream;
        tl_snap[1] = tl_ph_track;
        tl_snap[2] = tl_ph_step0;
        tl_snap[3] = tl_ph_step1;
        tl_snap[4] = tl_logic_end;
        tl_snap[5] = *(volatile unsigned char *)0xC7C5;
        tl_snap[6] = *(volatile unsigned char *)0xC7C1;
        tl_snap[7] = *(volatile unsigned char *)0xC7C2;
        tl_snap[8] = *(volatile unsigned char *)0xC7C3;
        tl_snap[9] = *(volatile unsigned char *)0xC7C4;
        tl_snap_seq++;
        tl_slots_used = stream_slots_used;
        tl_slots_peak = stream_slots_peak;
        tl_alloc_fail = stream_alloc_fail;
        tl_dropped = stream_dropped;
        probe_hp = (unsigned char)fighters[0].life;
        probe_boss = (unsigned char)fighters[1].life;
        probe_state = fighters[0].state;
        probe_over = fighters[1].state;
        probe_keys = (unsigned char)(k[0] | (k[1] << 4));
        probe_round = rm_round;
        probe_timer = rm_timer_s;
        probe_round_score = (unsigned char)((rm_wins[0] << 4) | (rm_wins[1] & 0x0Fu));

        if (rm_state == RM_ROUND || rm_state == RM_FIGHT || rm_state == RM_RESULT) {
            if (rm_wait) rm_wait--;
            if (rm_wait == 0) {
                if (rm_state == RM_ROUND) {
                    rm_state = RM_FIGHT;
                    rm_wait = FIGHT_FRAMES;
                    hud_set_banner(BANNER_FIGHT);
                } else if (rm_state == RM_FIGHT) {
                    rm_state = RM_ACTIVE;
                    hud_set_banner(BANNER_CLEAR);
                } else {
                    finish_result();
                }
            }
        }
    }
}
