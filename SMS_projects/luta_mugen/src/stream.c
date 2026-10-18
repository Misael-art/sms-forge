/* stream.c — envio de poses da pagina bancada para a VRAM (Plano 2, Task 6).
 *
 * Layout: dois buffers por lutador (A/B) na primeira metade da VRAM
 * (sprites leem 0..127 — SMS_useFirstHalfTilesforSprites(1), L006). O stride
 * e medido no stream_init a partir do MAIOR pose gerado, arredondado para par
 * (par TALL). Nada e suposto: pose maior que o stride nao existe porque o
 * stride sai dos proprios blobs.
 *
 * Metodo medido em T6: ate 64 B por VBlank por lutador, lidos DIRETO da janela
 * ROM 0x8000 do banco mapeado para SMS_VRAMmemcpy_brief. O codigo e fixo
 * abaixo de 0x4000, portanto permanece visivel durante o upload. Remover o
 * staging RAM corta a leitura/copia byte a byte dentro da janela critica.
 *
 * Ao completar o upload no VBlank, o banco ocioso vira o exibido. A
 * preparacao de metasprites ocorre depois desse VBlank e a proxima copia SAT
 * apresenta a pose (pedido em N, exibicao em N+2 quando cabe num chunk).
 */
#include "SMSlib.h"
#include "stream.h"

#define CHUNK STREAM_CHUNK_BYTES          /* limite medido por ator/VBlank */

static const PoseRef *poses;
static unsigned char nposes;
static unsigned char stride;              /* tiles por buffer (par) */

static unsigned char cur_pose[2], cur_sel[2];
static unsigned char req_pose[2];
static unsigned int  off_[2], size_[2];
static unsigned char streaming_[2];

static unsigned char buf_base(unsigned char who, unsigned char sel) {
    return (unsigned char)((who * 2u + sel) * (unsigned int)stride);
}

void stream_init(const PoseRef *p, unsigned char n) {
    unsigned char i;
    unsigned int m = 0, t;
    poses = p;
    nposes = n;
    for (i = 0; i < n; i++) {
        t = (poses[i].size + 31u) >> 5;   /* tiles do pose */
        if (t > m) m = t;
    }
    stride = (unsigned char)((m + 1u) & ~1u);   /* par TALL >= 2 */
    cur_sel[0] = cur_sel[1] = 0;
    streaming_[0] = streaming_[1] = 0;
}

void stream_request(unsigned char who, unsigned char pose) {
    /* Nao abandona upload parcial quando a anima muda: termina o buffer
     * ocioso e o proximo frame solicita a pose logica mais recente. */
    if (streaming_[who]) return;
    if (cur_pose[who] == pose) return;
    req_pose[who] = pose;
    off_[who] = 0;
    size_[who] = poses[pose].size;
    streaming_[who] = 1;
}

static void upload_chunk(unsigned char who) {
    const PoseRef *r = &poses[req_pose[who]];
    unsigned int n = r->size - off_[who];
    const unsigned char *src;
    SMS_saveROMBank();
    SMS_mapROMBank(r->bank);
    src = (const unsigned char *)(0x8000u + r->off + off_[who]);
    if (n > CHUNK) n = CHUNK;
    SMS_VRAMmemcpy_brief(
        ((unsigned int)buf_base(who, (unsigned char)(1u - cur_sel[who])) << 5) +
            off_[who],
        src, (unsigned char)n);
    SMS_restoreROMBank();
    off_[who] += n;
    if (off_[who] >= r->size) {
        streaming_[who] = 0;
        cur_sel[who] = (unsigned char)(1u - cur_sel[who]);
        cur_pose[who] = req_pose[who];
    }
}

void stream_step(void) {
    unsigned char who;
    for (who = 0; who < 2; who++) {
        if (streaming_[who]) {
            upload_chunk(who);
        }
    }
}

void stream_load_now(unsigned char who, unsigned char pose) {
    const PoseRef *r = &poses[pose];
    unsigned int off = 0, n;
    const unsigned char *src;
    SMS_saveROMBank();
    SMS_mapROMBank(r->bank);
    while (off < r->size) {
        n = r->size - off;
        if (n > CHUNK) n = CHUNK;
        src = (const unsigned char *)(0x8000u + r->off + off);
        SMS_VRAMmemcpy_brief(
            ((unsigned int)buf_base(who, cur_sel[who]) << 5) + off,
            src, (unsigned char)n);
        off += n;
    }
    SMS_restoreROMBank();
    cur_pose[who] = pose;
    req_pose[who] = pose;
    streaming_[who] = 0;
}

unsigned char stream_disp(unsigned char who) {
    return cur_pose[who];
}

unsigned char stream_disp_base(unsigned char who) {
    return buf_base(who, cur_sel[who]);
}
