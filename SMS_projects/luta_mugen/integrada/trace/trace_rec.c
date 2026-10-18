/* trace_rec.c — gravador de trilha por tick + roteiro de entrada deterministico (L097).
 *
 * SO existe na ROM clone do produtor. A entrada vem de `trace_script` (RLE: n, keys_p1, keys_p2; n=0 termina)
 * e o pad real e ignorado, entao a trilha nao depende de relogio de parede. O tick 0 e o primeiro quadro de
 * luta ativa (RM_ACTIVE). A cada tick, 12 B (6 por lutador) vao para 0xC800.. e, ao encher, `done`=1.
 * Registro por lutador: state, frame, tick, x em px, life (byte baixo), flags.
 *   flags: bit0 facing | bit1 hit_done | bit2-3 life>>8 | bit4 hitstop!=0 | bit5 y!=0
 * Cabecalho (8 B): 'T','R','C','1'|'2', done, n_lo, n_hi, rec_size.
 * Modo perfil (TRACE_PROFILE=1, 'TRC2'): por tick, 12 B = p1 state, p1 frame, p1 tick, p2 frame,
 *   VCounter ao fim de cada fase da iteracao (wait, hud, sat, stream), slots do pool em uso, pose visivel do P1,
 *   progresso do upload de cada lutador (pares ja copiados do alvo NEXT) e contagem de
 *   alvos descartados (stream_dropped). `load_done` e static no stream.c: o produtor o torna global SO na
 *   copia de perfil (instrumentada; nao e a ROM canonica). Leitura direta dos enderecos do probe do main.c.
 * Regiao 0xC800..0xCFFF nao tem simbolo no mapa da ROM canonica (check_ram_layout); o produtor re-checa.
 */
#include "fight.h"
#include "trace_script.h"
#include "trace_cfg.h"       /* TRACE_PROFILE 0 = estado da luta (TRC1) | 1 = perfil de fase/stream (TRC2) */

#define TRACE_BASE 0xC800u
#define TRACE_HDR 8u
#define TRACE_REC 12u
#define TRACE_MAX 170u        /* (0xD000 - 0xC808) / 12 */

volatile unsigned char __at(0xC800) trace_buf[2048];
#if TRACE_PROFILE
extern unsigned char load_done[2];
extern unsigned char stream_dropped;
#endif

static unsigned int n;
static unsigned int idx;
static unsigned char left, cur0, cur1, started;

static void load_entry(void) {
    unsigned char c = trace_script[idx];
    if (c == 0) { left = 0; cur0 = cur1 = 0; return; }
    left = c; cur0 = trace_script[idx + 1]; cur1 = trace_script[idx + 2];
    idx += 3;
}

unsigned char trace_pad(unsigned char who, unsigned char real) {
    (void)real;
    if (!started) { started = 1; idx = 0; load_entry(); }
    return who ? cur1 : cur0;
}

void trace_record(void) {
    volatile unsigned char *p;
    const Fighter *q;
    unsigned char f, fl;
    if (n >= TRACE_MAX) return;
    if (n == 0) {
        trace_buf[0] = 'T'; trace_buf[1] = 'R'; trace_buf[2] = 'C'; trace_buf[3] = TRACE_PROFILE ? '2' : '1';
        trace_buf[4] = 0; trace_buf[7] = TRACE_REC;
    }
    p = &trace_buf[TRACE_HDR + n * TRACE_REC];
#if TRACE_PROFILE
    p[0] = fighters[0].state; p[1] = fighters[0].frame; p[2] = fighters[0].tick; p[3] = load_done[0];
    p[4] = *(volatile unsigned char *)0xC7D0;   /* probe_profile_wait   */
    p[5] = *(volatile unsigned char *)0xC7D3;   /* probe_profile_hud    */
    p[6] = *(volatile unsigned char *)0xC7D4;   /* probe_profile_sat    */
    p[7] = *(volatile unsigned char *)0xC7D1;   /* probe_profile_stream */
    p[8] = *(volatile unsigned char *)0xC7B4;   /* tl_slots_used        */
    p[9] = fight_visible_pose(0);               /* pose visivel do P1 (era alloc_fail: sempre 0) */
    p[10] = load_done[1];
    p[11] = stream_dropped;
    (void)q; (void)fl;
    for (f = 0; f < 0; f++) {
#else
    for (f = 0; f < 2; f++) {
#endif
        q = &fighters[f];
        fl = (unsigned char)(q->facing & 1u);
        if (q->hit_done) fl |= 2u;
        fl |= (unsigned char)(((q->life >> 8) & 3u) << 2);
        if (q->hitstop) fl |= 16u;
        if (q->y) fl |= 32u;
        p[0] = q->state; p[1] = q->frame; p[2] = q->tick;
        p[3] = (unsigned char)(q->x >> 8); p[4] = (unsigned char)q->life; p[5] = fl;
        p += 6;
    }
    n++;
    trace_buf[5] = (unsigned char)n; trace_buf[6] = (unsigned char)(n >> 8);
    if (left && --left == 0) load_entry();
    if (n >= TRACE_MAX) trace_buf[4] = 1;     /* done por ultimo: o leitor so confia com done=1 */
}
