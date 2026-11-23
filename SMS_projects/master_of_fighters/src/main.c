// main.c — master_of_fighters (esqueleto do modelo SMSForge)
//
// Boot deterministico minimo: tela estavel, sem animacao, sem input.
// Serve para provar build -> ROM -> boot no emulador ANTES de qualquer arte.
// Substitua pelo runtime da cena 01 depois que doc/11-gdd.md estiver preenchido.
//
// Restricoes sempre ativas (AGENTS.md): sem float, sem malloc, sem API inventada.
// A autoridade da API e sdk/devkitSMS/SMSlib/SMSlib.h — confira antes de usar.

#include "SMSlib.h"

#if !defined(MOF_DUEL_PILOT)

#if defined(MOF_ALIS_STRONG_HOLD) && !defined(MOF_ALIS_ROUND1) && !defined(MOF_HAYATO_SAMPLE) && !defined(MOF_JJ_SAMPLE) && !(defined(MOF_CPS2_SAMPLE) && MOF_CPS2_SAMPLE)
#error O piloto de pressao requer um conjunto diagnostico de poses
#endif
#if defined(MOF_ALIS_ROUND1) && (!defined(MOF_ALIS_STRONG_HOLD) || defined(MOF_HAYATO_SAMPLE) || defined(MOF_JJ_SAMPLE) || defined(MOF_CENA01) || defined(MOF_CPS2_SAMPLE))
#error A rodada de Alis exige o proprio par e o comando segurado
#endif
#if (defined(MOF_CPS2_SAMPLE) && MOF_CPS2_SAMPLE) || defined(MOF_HAYATO_SAMPLE) || defined(MOF_JJ_SAMPLE) || defined(MOF_CENA01) || defined(MOF_ALIS_ROUND1)
/* Diagnostic selection within the existing consumer. Candidate source assets
 * remain outside res/; the default production skeleton is unchanged. */
#if defined(MOF_CENA01) && !defined(MOF_JJ_SAMPLE)
#error Cena 01 reutiliza os sprites aprovados do par J.J./Social
#endif
#if defined(MOF_CENA01)
#include "../data/source_art/scenes/cena01_duel_read/cena01_bg.h"
#endif
#if defined(MOF_ALIS_ROUND1)
#include "../out/diagnostics/alis_strong_thrust_round1/grounded_faces_assets_probe/both_faces_assets.h"
#define SAMPLE_POSE_COUNT 4u
#define SAMPLE_SPRITE_HEIGHT 8u
#define SAMPLE_TILE_BYTES ALIS_SAMPLE_TILE_BYTES
#define sample_palette alis_sample_palette
#define sample_tiles alis_sample_tiles
static const unsigned char sample_durations[4] = {0u, 7u, 3u, 6u};
#elif defined(MOF_JJ_SAMPLE)
#if MOF_JJ_SAMPLE == 1
#include "../out/diagnostics/jj_zillion_single_shot_v5/converted_left/sample_data.h"
#elif MOF_JJ_SAMPLE == 2
#include "../out/diagnostics/jj_zillion_single_shot_v5/converted_right/sample_data.h"
#else
#error Unknown J.J. diagnostic composition
#endif
#elif defined(MOF_HAYATO_SAMPLE)
#if MOF_HAYATO_SAMPLE == 1
#include "../out/diagnostics/hayato_cps2_sample_v1/guard_v2_left_baseline_v3/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 2
#include "../out/diagnostics/hayato_cps2_sample_v1/guard_v2_right_baseline_v3/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 3
#include "../out/diagnostics/hayato_cps2_sample_v1/social_jab_left_baseline_v3/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 4
#include "../out/diagnostics/hayato_cps2_sample_v1/social_jab_right_baseline_v3_mirrorphase/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 5
#include "../out/diagnostics/hayato_short_cut_v1/registered_left/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 6
#include "../out/diagnostics/hayato_short_cut_v1/registered_right/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 7
#include "../out/diagnostics/hayato_short_cut_v2/converted_v3_left/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 8
#include "../out/diagnostics/hayato_short_cut_v2/converted_v3_right/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 9
#include "../out/diagnostics/hayato_short_cut_v2/converted_v4_left/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 10
#include "../out/diagnostics/hayato_short_cut_v2/converted_v4_right/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 11
#include "../out/diagnostics/hayato_short_cut_v2/converted_v5_left/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 12
#include "../out/diagnostics/hayato_short_cut_v2/converted_v5_right/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 13
#include "../out/diagnostics/hayato_short_cut_v2/converted_v6_left/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 14
#include "../out/diagnostics/hayato_short_cut_v2/converted_v6_right/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 15
#include "../out/diagnostics/hayato_short_cut_v2/timing_only_v7/converted_left/sample_data.h"
#elif MOF_HAYATO_SAMPLE == 16
#include "../out/diagnostics/hayato_short_cut_v2/timing_only_v7/converted_right/sample_data.h"
#else
#error Unknown Hayato diagnostic composition
#endif
#elif MOF_CPS2_SAMPLE == 10
#include "../out/diagnostics/social_taunt01_cycle_v3_20261101/converted/sample_data.h"
#elif MOF_CPS2_SAMPLE == 9
#include "../out/diagnostics/social_taunt01_cycle_v2_20261101/converted/sample_data.h"
#elif MOF_CPS2_SAMPLE == 8
#include "../out/diagnostics/dr_social_cps2_sample_v1/contact_grid_v8/converted/sample_data.h"
#elif MOF_CPS2_SAMPLE == 5
#include "../out/diagnostics/dr_social_cps2_sample_v1/face_revision_v5/converted/sample_data.h"
#else
#include "../out/diagnostics/dr_social_cps2_sample_v1/converted_tall_v5/sample_data.h"
#endif
#ifndef SAMPLE_POSE_COUNT
#define SAMPLE_POSE_COUNT 7u
#define SAMPLE_ACTOR_X 40u
#define SAMPLE_ACTOR_Y 72u
#define SAMPLE_REFERENCE_X 152u
#define SAMPLE_REFERENCE_Y 72u
#endif
#ifndef SAMPLE_SPRITE_HEIGHT
#define SAMPLE_SPRITE_HEIGHT 16u
#endif
#ifndef MOF_SAMPLE_STRESS_BYTES
#define MOF_SAMPLE_STRESS_BYTES 0
#endif
#if defined(MOF_ALIS_STRONG_HOLD) && SAMPLE_POSE_COUNT < 2
#error O piloto de estocada precisa de guarda e poses de acao
#endif
#if defined(MOF_ALIS_STRONG_HOLD)
/* Provisorio para a rodada: amostras consecutivas do loop da ROM. */
#define ALIS_STRONG_HOLD_TICKS 12u
#endif
#if MOF_SAMPLE_STRESS_BYTES > SAMPLE_TILE_BYTES
#error Stress upload exceeds the resident source data
#endif
SMS_EMBED_SEGA_ROM_HEADER(0, 0);
#if defined(MOF_ALIS_ROUND1)
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "Alis strong thrust probe",
                              "Experimental art, reach and BG split");
#elif defined(MOF_CENA01)
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "Cena 01 duel read",
                              "HUD and floor plate; approved sprites unchanged");
#elif defined(MOF_JJ_SAMPLE)
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "J.J. pose sample",
                              "Character poses only, no shot/FX or gameplay");
#elif defined(MOF_HAYATO_SAMPLE) && MOF_HAYATO_SAMPLE >= 5
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "Hayato cut sample",
                              "Candidate guard and short cut, not gameplay");
#elif defined(MOF_CPS2_SAMPLE) && MOF_CPS2_SAMPLE == 10
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "Social taunt continuity",
                              "Settle and return; command undefined");
#elif defined(MOF_CPS2_SAMPLE) && MOF_CPS2_SAMPLE == 9
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "Social taunt diagnostic",
                              "Glasses taunt playback; command undefined");
#else
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "Social CPS2 sample",
                              "Candidate idle and jab, not gameplay");
#endif

/* SMRT/worst-frame contracts; __at storage must be volatile and initialized.
 * The linker map is checked against this corridor before emulator readings. */
volatile unsigned char __at(0xC7D2) probe_vline_min;
volatile unsigned char __at(0xC7E0) probe_smrt_magic[4];
volatile unsigned char __at(0xC7E4) probe_smrt_schema;
volatile unsigned char __at(0xC7EA) probe_vline;
volatile unsigned int __at(0xC7EB) probe_vovf;
volatile unsigned char __at(0xC7ED) probe_phase;
volatile unsigned char __at(0xC7EE) probe_worst_done;
volatile unsigned int __at(0xC7F0) probe_smrt_frame;
volatile unsigned char __at(0xC7F6) probe_state;
volatile unsigned char __at(0xC7F8) probe_keys;
volatile unsigned char __at(0xC7F9) probe_hold;
#if defined(MOF_ALIS_STRONG_HOLD)
volatile unsigned char __at(0xC7FA) probe_strong_latched;
volatile unsigned char __at(0xC7FB) probe_strong_triggers;
volatile unsigned char __at(0xC7FC) probe_strong_pressure;
#endif
#if defined(MOF_ALIS_ROUND1)
volatile unsigned char __at(0xC7FD) probe_alis_flags;
volatile unsigned char __at(0xC7FE) probe_alis_distance;
#endif
/* VDP V-counter I/O port, same instrument as the rev2 runtime (L061). */
__sfr __at(0x7e) SMS_VCounterPort;

static unsigned char pose, elapsed, autoplay, idle_ticks;
static unsigned int frame, old_keys;
#if defined(MOF_ALIS_STRONG_HOLD)
static unsigned char strong_hold_ticks, strong_latched;
#endif
#if defined(MOF_ALIS_ROUND1)
static unsigned char alis_face, alis_distance, alis_last_hud;
static const unsigned char *alis_last_bg;
/* Origins, not pivots: actor and reference canvases have pivot X=64. */
static const unsigned char alis_target_origins[2][3] = {
    {52u, 60u, 68u}, {60u, 52u, 44u}
};
#endif

static void emit_pose(const unsigned char *meta, unsigned char x,
                      unsigned char y) {
    while (meta[0] != 0x80u) {
        SMS_addSprite(x + meta[0], y + meta[1], meta[2]);
        meta += 3;
    }
}

#if defined(MOF_ALIS_ROUND1)
/* The split contains original palette indices; P0 is loaded from the same
 * codebook as P1. The target sprite may occlude a blade on BG: this layering
 * and every transition remain pending live framebuffer review. */
static const unsigned char *alis_bg_for_pose(unsigned char facing,
                                              unsigned char current_pose) {
    if (current_pose == 1u)
        return facing ? alis_bg_left_prepare : alis_bg_right_prepare;
    if (current_pose == 2u)
        return facing ? alis_bg_left_thrust : alis_bg_right_thrust;
    return 0;
}

static void alis_write_bg(const unsigned char *map, unsigned char clear) {
    while (map[0] != 255u) {
        SMS_setTileatXY(map[0], map[1], clear ? 0u : ALIS_BG_TILE_BASE + map[2]);
        map += 3;
    }
}

/* Row 1: one of three distance markers, left-face marker, active marker,
 * and geometric reach marker. These are diagnostics, not collision results. */
static void alis_write_hud(unsigned char distance, unsigned char flags) {
    SMS_setTileatXY(1u, 1u, distance == 0u ? ALIS_HUD_TILE : 0u);
    SMS_setTileatXY(2u, 1u, distance == 1u ? ALIS_HUD_TILE : 0u);
    SMS_setTileatXY(3u, 1u, distance == 2u ? ALIS_HUD_TILE : 0u);
    SMS_setTileatXY(5u, 1u, (flags & 4u) ? ALIS_HUD_TILE : 0u);
    SMS_setTileatXY(7u, 1u, (flags & 1u) ? ALIS_HUD_TILE : 0u);
    SMS_setTileatXY(9u, 1u, (flags & 2u) ? ALIS_HUD_TILE : 0u);
}

/* Converted thrust and target silhouette at canvas Y=44 (screen Y=108).
 * This compares visible edges only; no hit, block or damage is resolved. */
static unsigned char alis_geometry_reaches(unsigned char facing,
                                            unsigned char distance) {
    unsigned char target_x = alis_target_origins[facing][distance];
    if (facing)
        return (112u + 9u) <= (unsigned int)target_x + 69u;
    return 119u >= (unsigned int)target_x + 59u;
}
#endif

void main(void) {
    unsigned int keys;
    unsigned char vcnt;
#if defined(MOF_ALIS_ROUND1)
    unsigned char alis_flags, alis_hud_state;
    const unsigned char *alis_next_bg;
#endif
    SMS_displayOff();
#if SAMPLE_SPRITE_HEIGHT == 8
    SMS_setSpriteMode(SPRITEMODE_NORMAL);
#else
    SMS_setSpriteMode(SPRITEMODE_TALL);
#endif
    SMS_useFirstHalfTilesforSprites(1);
#if defined(MOF_ALIS_ROUND1)
    SMS_loadBGPalette(sample_palette);
#elif defined(MOF_CENA01)
    SMS_loadBGPalette(cena01_bg_palette);
#else
    SMS_setBGPaletteColor(0, 0x15u);
#endif
    SMS_loadSpritePalette(sample_palette);
    SMS_loadTiles(sample_tiles, 0u, SAMPLE_TILE_BYTES);
    /* Blank tile 0, separate from the resident high-half sprite pool. */
    SMS_VRAMmemsetW(0u, 0u, 32u);
#if defined(MOF_CENA01)
    /* Padrões de fundo em 0x2000, depois do pool de sprites e antes da PNT. */
    SMS_loadTiles(cena01_tiles, CENA01_TILE_BASE, CENA01_TILE_BYTES);
    SMS_loadTileMapArea(0, 0, cena01_map, 32, 24);
#else
    SMS_VRAMmemsetW(SMS_PNTAddress, 0u, 32u * 24u * 2u);
#endif
#if defined(MOF_ALIS_ROUND1)
    SMS_loadTiles(alis_bg_tiles, ALIS_BG_TILE_BASE, ALIS_BG_TILE_BYTES);
#endif
    pose = 0u;
    elapsed = 0u;
    autoplay = 1u;
    idle_ticks = 60u; /* stable initial idle before the first autoplay jab */
    frame = 0u;
    old_keys = 0u;
    probe_smrt_magic[0] = 'S';
    probe_smrt_magic[1] = 'M';
    probe_smrt_magic[2] = 'R';
    probe_smrt_magic[3] = 'T';
    probe_smrt_schema = 1u;
    probe_vline_min = 255u;
    probe_vovf = 0u;
    probe_worst_done = 0u;
    probe_smrt_frame = 0u;
    probe_state = 0u;
    probe_keys = 0u;
    probe_hold = 0u;
#if defined(MOF_ALIS_STRONG_HOLD)
    strong_hold_ticks = 0u;
    strong_latched = 0u;
    probe_strong_latched = 0u;
    probe_strong_triggers = 0u;
    probe_strong_pressure = 0u;
#endif
#if defined(MOF_ALIS_ROUND1)
    alis_face = 0u;
    alis_distance = 1u;
    alis_last_hud = 255u;
    alis_last_bg = 0;
    probe_alis_flags = 0u;
    probe_alis_distance = 1u;
#endif
    SMS_displayOn();
    for (;;) {
        probe_phase = 1u;
        keys = SMS_getKeysStatus();
#if defined(MOF_ALIS_ROUND1)
        /* Selection is available in guard; no mid-animation facing change. */
        if (pose == 0u) {
            if ((keys & PORT_A_KEY_2) && !(old_keys & PORT_A_KEY_2))
                alis_face ^= 1u;
            if ((keys & PORT_A_KEY_UP) && !(old_keys & PORT_A_KEY_UP))
                alis_distance = alis_distance ? alis_distance - 1u : 2u;
            else if ((keys & PORT_A_KEY_DOWN) && !(old_keys & PORT_A_KEY_DOWN))
                alis_distance = alis_distance == 2u ? 0u : alis_distance + 1u;
        }
#endif
#if defined(MOF_ALIS_STRONG_HOLD)
        /* Cada pressao consome no maximo um limiar, mesmo durante recuperacao.
         * Soltar rearma; uma pressao vencida durante outra pose nao e guardada. */
        if (!(keys & PORT_A_KEY_1)) {
            strong_hold_ticks = 0u;
            strong_latched = 0u;
        } else if (!strong_latched) {
            if (strong_hold_ticks < ALIS_STRONG_HOLD_TICKS)
                ++strong_hold_ticks;
            if (strong_hold_ticks == ALIS_STRONG_HOLD_TICKS) {
                strong_latched = 1u;
                if (pose == 0u) {
                    pose = 1u;
                    elapsed = 0u;
                    ++probe_strong_triggers;
                }
            }
        }
#else
        if ((keys & PORT_A_KEY_2) && !(old_keys & PORT_A_KEY_2))
            autoplay ^= 1u;
#if SAMPLE_POSE_COUNT > 1
        if (pose == 0u) {
            if ((keys & PORT_A_KEY_1) && !(old_keys & PORT_A_KEY_1)) {
                pose = 1u;
                elapsed = 0u;
            } else if (autoplay && idle_ticks == 0u) {
                pose = 1u;
                elapsed = 0u;
            }
        }
#endif
#endif
        old_keys = keys;
        probe_phase = 4u;
        SMS_initSprites();
#if defined(MOF_ALIS_ROUND1)
        alis_next_bg = alis_bg_for_pose(alis_face, pose);
        /* Pixel bounds belong to the current converted artwork only. */
        alis_flags = (pose == 2u ? 1u : 0u) |
                     ((pose == 2u && alis_geometry_reaches(alis_face, alis_distance)) ? 2u : 0u) |
                     (alis_face ? 4u : 0u);
        alis_hud_state = alis_flags | (alis_distance << 3);
        if (alis_face) {
            emit_pose(alis_sample_left_poses[pose], 112u, 64u);
            emit_pose(alis_sample_left_reference_meta,
                      alis_target_origins[1][alis_distance], 64u);
        } else {
            emit_pose(alis_sample_right_poses[pose], 0u, 64u);
            emit_pose(alis_sample_right_reference_meta,
                      alis_target_origins[0][alis_distance], 64u);
        }
#else
        emit_pose(sample_poses[pose], SAMPLE_ACTOR_X, SAMPLE_ACTOR_Y);
        emit_pose(sample_reference_meta, SAMPLE_REFERENCE_X, SAMPLE_REFERENCE_Y);
#endif
        SMS_finalizeSprites();
        SMS_waitForVBlank();
        probe_phase = 2u;
        SMS_copySpritestoSAT();
#if defined(MOF_ALIS_ROUND1)
        if (alis_last_bg != alis_next_bg) {
            if (alis_last_bg) alis_write_bg(alis_last_bg, 1u);
            if (alis_next_bg) alis_write_bg(alis_next_bg, 0u);
            alis_last_bg = alis_next_bg;
        }
        if (alis_last_hud != alis_hud_state) {
            alis_write_hud(alis_distance, alis_flags);
            alis_last_hud = alis_hud_state;
        }
#endif
#if MOF_SAMPLE_STRESS_BYTES > 0
        /* Measured next step: resend a correct prefix into the same slots.
         * This changes transfer cost, never artwork, palette or pose count. */
        SMS_loadTiles(sample_tiles, 0u, MOF_SAMPLE_STRESS_BYTES);
#endif
        vcnt = SMS_VCounterPort;
        probe_phase = 3u;
        ++frame;
        probe_smrt_frame = frame;
        probe_state = pose;
        probe_keys = (unsigned char)keys;
        probe_hold = elapsed;
#if defined(MOF_ALIS_STRONG_HOLD)
        probe_strong_pressure = strong_hold_ticks;
        probe_strong_latched = strong_latched;
#endif
#if defined(MOF_ALIS_ROUND1)
        probe_alis_flags = alis_flags;
        probe_alis_distance = alis_distance;
#endif
        if (frame <= 3000u) {
            probe_vline = vcnt;
            if (vcnt < 0xC0u) ++probe_vovf;
            if (vcnt < probe_vline_min) probe_vline_min = vcnt;
        } else {
            probe_worst_done = 1u;
        }
#if SAMPLE_POSE_COUNT > 1
        if (pose != 0u) {
            if (++elapsed >= sample_durations[pose]) {
                elapsed = 0u;
                if (++pose == SAMPLE_POSE_COUNT) {
                    pose = 0u;
                    idle_ticks = 21u;
                }
            }
        } else if (idle_ticks != 0u) {
            --idle_ticks;
        }
#endif
    }
}
#else
// Header 16KB => SDSC precisa ser a variante _16KB (combinacao provada em ROM
// no laboratorio_01; SMSlib.h:460 e :485 sao a autoridade).
SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "master_of_fighters",
                                     "esqueleto do modelo");

void main(void) {
    SMS_displayOff();
    // indice 0 e transparente/backdrop nas duas subpaletas (lei de paleta §8).
    SMS_setBGPaletteColor(0, 0x00);   // preto
    SMS_setBGPaletteColor(1, 0x3F);   // branco (codigo 6-bit: canais 0-3)
    /* Sprites leem padroes da PRIMEIRA metade da VRAM (tiles 0..255).
     * Sem isto o VDP le em tile+256 e sprites viram ruido colorido — causa-raiz
     * real do L006. SMSlib.h:53. Gate: audit_sprite_mode.py. */
    SMS_useFirstHalfTilesforSprites(1);
    SMS_displayOn();

    // Boot determinístico: estado inicial estavel, sem variacao entre frames.
    // (audit_deterministic_boot.py reprova ROM animada sem estado estavel.)
    for (;;) {
        SMS_waitForVBlank();
    }
}
#endif

#endif /* !MOF_DUEL_PILOT */
