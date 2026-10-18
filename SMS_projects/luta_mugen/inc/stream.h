/* stream.h — banking Sega mapper + streaming de pose no VBlank (Plano 2, Task 6).
 *
 * A divida medida no S3: 1.160.704 B de tiles por lutador real jamais caberiam
 * nos 16 KB da primeira metade da VRAM, nem na ROM linear. Os tiles moram em
 * paginas de 16 KB no slot 2 do Sega mapper (makesms -mbank ...:0:1:2); so a
 * pose exibida e a que esta sendo enviada existem na VRAM, em dois buffers
 * por lutador. O teto medido desta cena e 64 B por ator/VBlank; o restante da
 * pose aguarda os VBlanks seguintes.
 *
 * Fila (contrato do plano; latencia e design, documentada no TDD):
 *   pose pedida no frame N -> upload no VBlank N+1 (stream_step)
 *   -> buffer alternado ao terminar e preparado em CPU -> apresentada pela
 *      SAT do VBlank N+2 quando cabe num chunk (mais tarde se houver chunks).
 * O desenho le stream_disp() (a pose que FISICAMENTE esta no buffer); a
 * logica (hit, caixas, fisica) corre na pose do frame logico — nunca trocar.
 *
 * Espelho horizontal NAO passa por aqui: SMS nao tem flip de sprite e o blob
 * do pose ja contem os pares espelhados (runtime_format._layout interna os
 * mirrors no pool) — a escolha META/METAL e do draw, ao custo de zero bytes.
 *
 * API verificada (sdk/devkitSMS/SMSlib/SMSlib.h):
 *   SMS_mapROMBank :71 · SMS_saveROMBank/SMS_restoreROMBank :76-83 (mesmo escopo)
 *   SMS_VRAMmemcpy_brief :394 (destino em bytes, size em bytes; source permanece
 *   no bank mapeado; base de tile precisa ser multiplicada por 32)
 * Precedentes: hamoopig/src/stream.c (buffers A/B, banco ocioso) e MSSF2T
 * doc/spec-banking.md (dados em banco, codigo linear; crt0_sms ja inicializa
 * [0xFFFD]=0, [0xFFFE]=1, [0xFFFF]=2).
 */
#ifndef STREAM_H
#define STREAM_H

/* Um pose no banco de tiles: pagina do slot 2, offset dentro da pagina e
 * tamanho em bytes (multiplo de 32; par TALL exige base par). */
typedef struct { unsigned char bank;
                 unsigned int off;
                 unsigned int size; } PoseRef;

#define STREAM_CHUNK_BYTES 64u /* teto medido com SAT + HUD na cena Ken */

void stream_init(const PoseRef *poses, unsigned char nposes);

/* Fila a pose do lutador `who` (0/1). Ignorada se a mesma pose ja esta
 * exibida, em transito ou na fila. */
void stream_request(unsigned char who, unsigned char pose);

/* Envia 1 chunk (<=64 B) por lutador e alterna o buffer ao completar.
 * Chamar na janela do VBlank (logo apos SMS_waitForVBlank). */
void stream_step(void);

/* Carga bloqueante para boot/reset: a pose ja vale no frame atual. */
void stream_load_now(unsigned char who, unsigned char pose);

/* Pose exibida e a base de tile absoluta dela (VRAM, par TALL). */
unsigned char stream_disp(unsigned char who);
unsigned char stream_disp_base(unsigned char who);

#endif /* STREAM_H */
