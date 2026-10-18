/* luta.h — contrato das tabelas geradas (mugen2sms S4.5b) para o runtime.
 *
 * Formato byte-a-byte provado em ROM por MSSF2T (inc/ken_idle_tiles.h:58 e
 * src/fight.c rebuild_meta/draw_fb): metasprite = triplas assinadas
 * (dx, dy, tile) com dx=0x80 no terminador; tile de runtime =
 * (pool_idx*2) + base_de_carga_do_pose, por isso o draw soma `base` ao ler.
 * Espelho horizontal E outro padrao no pool (SMS nao tem flip de sprite);
 * o blob METAL ja traz base+idx do espelho e dx refletido (dx' = lo+hi-dx).
 *
 * API verificada em sdk/devkitSMS/SMSlib/SMSlib.h:
 *   SMS_setSpriteMode/SPRITEMODE_TALL :54-57 (par TALL = tileEven, tileEven+1)
 *   SMS_useFirstHalfTilesforSprites   :53   (L006 — sprites leem 1a metade)
 *   SMS_addMetaSprite / METASPRITE_END:214-216
 *   SMS_loadTiles                     :130  (4bpp, 32 B/tile, tamanho em bytes)
 *   SMS_setBGPaletteColor/_Sprite     :249-250 (palavra 6-bit r|g<<2|b<<4)
 *
 * CLSN (T4): quádruplas int16 little-endian em DUAS secoes — hit (clsn1) e
 * hurt (clsn2) — cada uma terminada pela sentinela -32767 (0x01 0x80).
 * Secao vazia comeca com a sentinela. Coordenadas MUGEN: x relativo ao eixo,
 * y negativo ACIMA do chao (clsn2 do idle = -8,-16,8,0 = corpo inteiro).
 * AXIS: par int16 (x, y) = canto superior-esquerdo da pose relativo ao eixo.
 */
#ifndef LUTA_H
#define LUTA_H

#include "SMSlib.h"

/* O METAL espelha a grade de colunas 8 px, incluindo o padding à direita.
 * Ao refletir sobre o eixo, a origem usa essa largura arredondada para que
 * poses com largura não múltipla de 8 mantenham o mesmo pivô. */
#define FIGHTER_MIRRORED_ORIGIN_X(anchor_x, axis_x, width_px) \
    ((signed int)(anchor_x) - ((signed int)(axis_x) + \
     (signed int)((((unsigned int)(width_px) + 7u) & 0xFFF8u))))

/* Uma frame: duração AIR em ticks (255 = segura), pose lógico, metadados AIR
 * transformados para o grid SMS e dimensões já após a escala do contrato.
 * Cada ACT pode deduplicar tiles em outra ordem; P2 possui seu próprio par
 * META/METAL associado ao blob de padrões da paleta 2. */
typedef struct { unsigned char dur, pose;
                 const unsigned char *meta, *metal, *clsn, *axis;
                 unsigned char width, height;
                 const unsigned char *meta_p2, *metal_p2; } Frame;

/* Caixa de colisao (clsn do AIR): cantos em px MUGEN (y para cima), achatar
 * para AABB de tela acontece no runtime (fight.c). */
typedef struct { signed char x1, y1, x2, y2; } Box;

typedef struct { unsigned short id;                  /* anim id do AIR */
                 unsigned char n_frames, loop_start;/* 255=one-shot; otherwise AIR loop index */
                 const Frame *frames; } Anim;

/* Posicao em Q8.8: x = px de tela (0..255.99), y = ALTURA acima do chao
 * (0 = no chao; evita sinal em estado quente). vx/vy Q8.8 com sinal. */
typedef struct { unsigned char facing;              /* 0=dir, 1=esq */
                 unsigned int x, y;
                 signed int vx, vy;
                 unsigned char state, anim, frame, tick;
                 unsigned char hit_done, hitstop, keys_prev;
                 unsigned short life; } Fighter;

/* Sprites leem a primeira metade da VRAM: base 0 (SMSlib.h:53, L006). */
#define FIGHTER_TILE_BASE 0x00

/* Copia as triplas de `meta` para `dst` somando `base` ao byte de tile e
 * devolve o numero de entradas (precedente: rebuild_meta do MSSF2T).
 * dst precisa de espaco para 3*(n+1) bytes. */
extern unsigned char meta_rebase(const unsigned char *meta, unsigned char base,
                                 signed char *dst);

#endif /* LUTA_H */
