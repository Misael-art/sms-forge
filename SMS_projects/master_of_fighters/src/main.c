// main.c — master_of_fighters (esqueleto do modelo SMSForge)
//
// Boot deterministico minimo: tela estavel, sem animacao, sem input.
// Serve para provar build -> ROM -> boot no emulador ANTES de qualquer arte.
// Substitua pelo runtime da cena 01 depois que doc/11-gdd.md estiver preenchido.
//
// Restricoes sempre ativas (AGENTS.md): sem float, sem malloc, sem API inventada.
// A autoridade da API e sdk/devkitSMS/SMSlib/SMSlib.h — confira antes de usar.

#include "SMSlib.h"

#if defined(MOF_CPS2_SAMPLE) && MOF_CPS2_SAMPLE
/* Diagnostic selection within the existing consumer. Candidate source assets
 * remain outside res/; the default production skeleton is unchanged. */
#include "../out/diagnostics/dr_social_cps2_sample_v1/converted_tall_v5/sample_data.h"
#ifndef MOF_SAMPLE_STRESS_BYTES
#define MOF_SAMPLE_STRESS_BYTES 0
#endif
#if MOF_SAMPLE_STRESS_BYTES > SAMPLE_TILE_BYTES
#error Stress upload exceeds the resident source data
#endif
SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "Social CPS2 sample",
                              "Candidate idle and jab, not gameplay");

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
/* VDP V-counter I/O port, same instrument as the rev2 runtime (L061). */
__sfr __at(0x7e) SMS_VCounterPort;

static unsigned char pose, elapsed, autoplay, idle_ticks;
static unsigned int frame, old_keys;

static void emit_pose(const unsigned char *meta, unsigned char x,
                      unsigned char y) {
    while (meta[0] != 0x80u) {
        SMS_addSprite(x + meta[0], y + meta[1], meta[2]);
        meta += 3;
    }
}

void main(void) {
    unsigned int keys;
    unsigned char vcnt;
    SMS_displayOff();
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setBGPaletteColor(0, 0x15u);
    SMS_loadSpritePalette(sample_palette);
    SMS_loadTiles(sample_tiles, 0u, SAMPLE_TILE_BYTES);
    /* Blank tile 0, separate from the resident high-half sprite pool. */
    SMS_VRAMmemsetW(0u, 0u, 32u);
    SMS_VRAMmemsetW(SMS_PNTAddress, 0u, 32u * 24u * 2u);
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
    SMS_displayOn();
    for (;;) {
        probe_phase = 1u;
        keys = SMS_getKeysStatus();
        if ((keys & PORT_A_KEY_2) && !(old_keys & PORT_A_KEY_2))
            autoplay ^= 1u;
        if (pose == 0u) {
            if ((keys & PORT_A_KEY_1) && !(old_keys & PORT_A_KEY_1)) {
                pose = 1u;
                elapsed = 0u;
            } else if (autoplay && idle_ticks == 0u) {
                pose = 1u;
                elapsed = 0u;
            }
        }
        old_keys = keys;
        probe_phase = 4u;
        SMS_initSprites();
        emit_pose(sample_poses[pose], 40u, 72u);
        emit_pose(sample_reference_meta, 152u, 72u);
        SMS_finalizeSprites();
        SMS_waitForVBlank();
        probe_phase = 2u;
        SMS_copySpritestoSAT();
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
        if (frame <= 3000u) {
            probe_vline = vcnt;
            if (vcnt < 0xC0u) ++probe_vovf;
            if (vcnt < probe_vline_min) probe_vline_min = vcnt;
        } else {
            probe_worst_done = 1u;
        }
        if (pose != 0u) {
            if (++elapsed >= sample_durations[pose]) {
                elapsed = 0u;
                if (++pose == 7u) {
                    pose = 0u;
                    idle_ticks = 21u;
                }
            }
        } else if (idle_ticks != 0u) {
            --idle_ticks;
        }
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
