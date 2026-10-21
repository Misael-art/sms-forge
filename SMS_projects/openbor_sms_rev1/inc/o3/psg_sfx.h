/* Gerado por openbor2sms.sms_audio; reautoria PSG O3/D11.
 * Incluir UMA vez em unidade fixa dos bancos 0..1, nunca BANK2+.
 * Confirmar arrays inteiros abaixo de 0x8000 no .map.
 * PSGSFXFrame le ponteiro direto; slot2 e do uploader de poses.
 * SIZE = bytes; DURATION_TICKS = intervalos ate o mute/stop.
 * Prioridade deve ser aplicada pelo owner; PSGlib nao arbitra.
 */
#ifndef O3_PSG_SFX_H
#define O3_PSG_SFX_H
#include "PSGlib.h"
#if SFX_CHANNEL3 != 0x02
#error "Mascara PSGlib divergente"
#endif
#define SFX_ATTACK_SIZE 13
#define SFX_ATTACK_DURATION_TICKS 6
#define SFX_ATTACK_PRIORITY 1
#define SFX_ATTACK_MASK SFX_CHANNEL3
static const unsigned char sfx_attack[SFX_ATTACK_SIZE] = {
    0xE4, 0xF3, 0x38, 0xE5, 0xF5, 0x39, 0xE6, 0xF9, 0x39, 0xFC, 0x38, 0xFF, 0x00
};
#define SFX_IMPACT_SIZE 15
#define SFX_IMPACT_DURATION_TICKS 10
#define SFX_IMPACT_PRIORITY 2
#define SFX_IMPACT_MASK SFX_CHANNEL3
static const unsigned char sfx_impact[SFX_IMPACT_SIZE] = {
    0xE4, 0xF0, 0x38, 0xE5, 0xF3, 0x39, 0xE6, 0xF6, 0x3A, 0xFA, 0x3A, 0xFD, 0x38, 0xFF, 0x00
};
#define SFX_FALL_SIZE 14
#define SFX_FALL_DURATION_TICKS 18
#define SFX_FALL_PRIORITY 3
#define SFX_FALL_MASK SFX_CHANNEL3
static const unsigned char sfx_fall[SFX_FALL_SIZE] = {
    0xE5, 0xF1, 0x39, 0xE6, 0xF4, 0x3A, 0xF7, 0x3B, 0xFA, 0x3C, 0xFD, 0x3B, 0xFF, 0x00
};
#endif
