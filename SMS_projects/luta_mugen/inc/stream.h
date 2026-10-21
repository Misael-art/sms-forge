/* stream.h — streaming de poses compactas no VBlank para Master System.
 *
 * A divida medida no S3: 1.160.704 B de tiles por lutador real jamais caberiam
 * nos 16 KB da primeira metade da VRAM, nem na ROM linear. Os tiles moram em
 * paginas de 16 KB no slot 2 do Sega mapper (makesms -mbank ...:0:1:2). O pool
 * de sprite tem 128 pares TALL; poses/facings compactos recebem uma faixa
 * contigua. A pose exibida permanece reservada enquanto outra faixa e enviada.
 * O build v088 envia um par de 64 B total por VBlank, somente quando VCounter
 * esta em C0..CF; a cópia usa OUTI desenrolado. Solicitação de ataque pode
 * receber quatro pares consecutivos antes de ceder a uma pose ambiental.
 * Continua experimento de escalonamento, não banda AIR aprovada; o pior quadro
 * e a latência de pose ainda precisam de medição na ROM.
 *
 * Fila (contrato do plano; latencia e design, documentada no TDD):
 *   pose pedida no frame N -> upload no VBlank N+1 (stream_step)
 *   -> faixa nova publicada ao terminar -> preparada em CPU -> apresentada
 *      pela SAT no proximo commit.
 * O desenho le stream_disp() (a pose que FISICAMENTE esta no buffer); a
 * logica (hit, caixas, fisica) corre na pose do frame logico — nunca trocar.
 *
 * SMS nao tem flip de sprite. O conversor emite payload compacto separado por
 * facing e remapeia META/METAL para cada faixa real de patterns.
 *
 * API verificada (sdk/devkitSMS/SMSlib/SMSlib.h):
 *   SMS_mapROMBank :71 · SMS_saveROMBank/SMS_restoreROMBank :76-83 (mesmo escopo)
 *   SMS_VDPControlPort :385 (0xBF); SMS_VRAMmemcpy_brief :394 (destino em
 *   bytes, size em bytes; source permanece no bank mapeado; base de tile
 *   precisa ser multiplicada por 32). O caminho de jogo emite o mesmo par
 *   diretamente por OUTI (precedente local: integrada/src/stream.c).
 * Precedentes: hamoopig/src/stream.c (buffers A/B, banco ocioso) e MSSF2T
 * doc/spec-banking.md (dados em banco, codigo linear; crt0_sms ja inicializa
 * [0xFFFD]=0, [0xFFFE]=1, [0xFFFF]=2).
 */
#ifndef STREAM_H
#define STREAM_H

/* Um pose/facing no banco de tiles: pagina do slot 2, offset dentro da pagina
 * e tamanho em bytes (multiplo de 64; um par de patterns por sprite TALL). */
typedef struct { unsigned char bank;
                 unsigned int off;
                 unsigned int size; } PoseRef;

#define STREAM_CHUNK_BYTES 64u /* par TALL atomico: dois tiles de 8x8 */

void stream_init(const PoseRef *poses, unsigned int nposes);

/* Fila a pose do lutador `who` (0/1). Ignorada se a mesma pose ja esta
 * exibida ou em transito. `pose` e global P1/P2; facing=0 direita, 1 esquerda;
 * priority=1 marca uma ação temporalmente sensível, 0 uma pose ambiental. */
void stream_request(unsigned char who, unsigned char pose,
                    unsigned char facing, unsigned char priority);

/* v088: solicitações com prioridade 1 (ação de combate) podem receber até
 * quatro pares consecutivos antes de ceder a uma solicitação ambiental. O
 * teto de transferência continua em 1 par (64 B) total por chamada e o VDP
 * precisa estar em C0..CF. Prioridades iguais seguem round-robin. */
void stream_step(void);

/* Carga bloqueante para boot/reset: pose/facing ja valem no frame atual. */
void stream_load_now(unsigned char who, unsigned char pose,
                     unsigned char facing);

/* Pose/facing e mapa de pares locais para slots físicos no pool de 8 KiB. */
unsigned char stream_disp(unsigned char who);
unsigned char stream_disp_facing(unsigned char who);
const unsigned char *stream_disp_map(unsigned char who);
unsigned char stream_disp_pair_count(unsigned char who);

#endif /* STREAM_H */
