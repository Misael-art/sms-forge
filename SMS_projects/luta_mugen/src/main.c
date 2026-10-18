/* main.c — cena T7 Ken vs dummy do motor FSM (Plano 2).
 *
 * A cena 01 (probe_import) mediu as leis de hardware e saiu de cena: aqui o
 * loop de combate usa o corte Ken gerado e e interpretado por fight.c. P1
 * comeca em ATRACAO (roteiro
 * deterministico — gate audit_deterministic_boot); a PRIMEIRA tecla fisica do
 * pad mata a atracao e o controle passa a ser do jogador (precedente MSSF2T
 * "qualquer tecla mata g_attract"). P2 roda dummy deterministico. Os dois
 * slots usam o mesmo corte Ken com paletas ACT diferentes; outro .def ainda
 * nao e carregado simultaneamente. Animacao avanca sem tecla fisica.
 *
 * Probe de memoria (L035, mapa SMRT dos projetos-irmaos): o ESTADO mora em
 * 0xC7E0.. e o DAP do Emulicious le com a emulacao pausada — a prova de
 * input vivo (Task 5) nao depende de pixels nem de foco de janela.
 *
 * Telemetria (nao entrega visual — diretriz estetica): uma celula em (29,0)
 * muda a cada 128 frames, o periodo medido por measure_frame_advance. Ela
 * compartilha uma fila de ate 2 escritas BG por VBlank com o HUD.
 *
 * Telemetria worst-frame (L061/L082, contrato measure_worst_frame.py): a
 * ROM roda 3000 frames sem DAP; vline_min registra o menor VCounter ao fim
 * do trabalho e vovf conta derrames. done sela ambos antes de o DAP conectar,
 * para uma pausa de depuracao nao virar custo de runtime medido.
 *
 * Contratos citados (sdk/devkitSMS/SMSlib/SMSlib.h): SMS_addMetaSprite :215,
 * SMS_loadTiles :130, SMS_setTileatXY :117, useFirstHalfTiles :53 (L006),
 * SMS_getKeysHeld :290, PORT_A_KEY_* :298-303.
 */
#include "SMSlib.h"
#include "fight.h"
#include "input.h"
#include "stream.h"
#include "audio.h"

/* Símbolos de input estáveis. O gerador os preenche com os padrões nomeados
 * pelo .def selecionado; trocar o personagem não troca a interface do core. */
extern const unsigned char KEN_CUT_CMD_BUTTON1[];
extern const unsigned char KEN_CUT_CMD_FORWARD_DOUBLE[];
/* Remapeo documentado do pad de 4 direcoes: D, F, B1 (sem diagonal). */
static const unsigned char CMD_QCF_B1[] = {
    0x03, 0x0C, 0x01,
    0x02, 0x00, 0x08, 0x00, 0x10, 0x00
};

/* T6: ROM bancada (paginas de 16 KB, dados no slot 2) — header generico,
 * os variantes _16KB mentem no tamanho (precedente hamoopig main.c:7-8 com
 * makesms_extra -mbank ...:0:1:2 no project.json). */
SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "luta_mugen",
                                "T6 banking + streaming por pose");

/* VCounter: registro do VDP lido por porta (molde MSSF2T src/main.c:58,
 * que declara localmente — SMSlib.h nao expoe o sfr). */
__sfr __at (0x7e) SMS_VCounterPort;

/* O SMSlib.lib distribuido neste SDK foi compilado sem VDPTYPE_DETECTION.
 * Este leitor privado replica o detector oficial em
 * sdk/devkitSMS-upstream/SMSlib/src/SMSlib.c:81-109; nao declara API nova. */
static unsigned char detect_vdp_wrap(void) __z88dk_fastcall __naked
    __preserves_regs(c,d,e,h,iyh,iyl) {
    __asm
        in a,(0x7E)
1$:
        ld b,a
        in a,(0x7E)
        cp b
        jr nz,1$
        cp #0x80
        jr nz,1$
        ld l,a
        in a,(0x7E)
2$:
        ld b,a
        in a,(0x7E)
        cp b
        jr nz,2$
        cp l
        jr z,2$
        ret c
        ld l,a
        jp 2$
    __endasm;
}

/* ---- tiles de fundo e HUD (2a metade: poses ocupam 0..21) ---- */
static const unsigned char tile_empty[32] = { 0 };
static const unsigned char tile_floor[32] = {
    0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF,
    0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF,
    0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF, 0x00, 0xFF
};
/* quadrantes: TL=bit3 TR=bit2 BL=bit1 BR=bit0 -> 16 glifos distintos */
static const unsigned char hex_glyphs[512] = {
    /* 0 */ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    /* 1 */ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00,
    /* 2 */ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00,
    /* 3 */ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    /* 4 */ 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    /* 5 */ 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00,
    /* 6 */ 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00,
    /* 7 */ 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    /* 8 */ 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    /* 9 */ 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00,
    /* A */ 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00,
    /* B */ 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00,
    /* C */ 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    /* D */ 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00, 0x0F, 0x00, 0x00, 0x00,
    /* E */ 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00, 0xF0, 0x00, 0x00, 0x00,
    /* F */ 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00, 0xFF, 0x00, 0x00, 0x00
};

#define T_EMPTY 127
#define T_FLOOR 126               /* pal 2; p1|p3 = indice 10 -> cor 2 (CRAM 10) */
#define T_HEX   128               /* 128..143 = glifos 0..F */
#define T_HEALTH 144              /* 144..161 = 9 niveis x 2 lados */
#define T_KO_K 162
#define T_KO_O 163
#define T_TIME_T 164
#define T_TIME_I 165
#define T_TIME_M 166
#define T_TIME_E 167
#define T_DIGIT 168              /* 168..177 = legiveis 0..9 */
#define WORST_FRAME_WINDOW 3000u   /* >=50 s NTSC; 60 s PAL */

/* ---- probe SMRT (mapa SNAP_ADDRS de measure_runtime_probe.py; L035) ----
 * __at() SEMPRE volatile (L009), senao o SDCC apaga a escrita. py = ALTITUDE
 * (0 = chao), nao y de tela — difere do convenio MSSF2T (chao=112). */
volatile unsigned char  __at(0xC7E0) probe_magic0;
volatile unsigned char  __at(0xC7E1) probe_magic1;
volatile unsigned char  __at(0xC7E2) probe_magic2;
volatile unsigned char  __at(0xC7E3) probe_magic3;
volatile unsigned char  __at(0xC7E4) probe_schema;
volatile unsigned int   __at(0xC7F0) probe_frame;    /* 16 bits: fps real */
volatile unsigned char  __at(0xC7F2) probe_hp;       /* vida P1 (byte) */
volatile unsigned char  __at(0xC7F3) probe_score;    /* hits conectados P1 */
volatile unsigned char  __at(0xC7F4) probe_boss;     /* vida P2 (byte) */
volatile unsigned char  __at(0xC7F5) probe_over;     /* round encerrado */
volatile unsigned char  __at(0xC7F6) probe_state;    /* estado P1 (ST_*) */
volatile unsigned char  __at(0xC7F7) probe_wave;     /* 1 = atracao ativa */
volatile unsigned char  __at(0xC7F8) probe_keys;     /* Port A crua (byte baixo) */
volatile unsigned char  __at(0xC7F9) probe_pose;     /* anim P1 (indice) */
volatile unsigned char  __at(0xC7FA) probe_px;       /* P1.x >> 8 */
volatile unsigned char  __at(0xC7FB) probe_py;       /* P1.y >> 8 = altura */
volatile unsigned char  __at(0xC7FC) probe_p2x;      /* P2.x >> 8 */
volatile unsigned char  __at(0xC7FD) probe_pattern;  /* A, FF, QCF+B1 */
volatile unsigned char  __at(0xC7FE) probe_round_score; /* P1 low nibble, P2 high */
volatile unsigned char  __at(0xC7FF) probe_timer;       /* seconds left */
volatile unsigned char  __at(0xC7D5) probe_region_hz;   /* 50 PAL / 60 NTSC */
volatile unsigned char  __at(0xC7D7) probe_special; /* FIGHT_EVENT_SPECIAL visto */
/* triade worst-frame (mede_worst_frame DECL_RX exige estas declarações na
 * fonte; vovf WORD — byte com guarda saturava e confundia reset com
 * estouro, L071/§56). */
volatile unsigned char  __at(0xC7EA) probe_vline;    /* VCounter apos as escritas de VDP */
volatile unsigned int   __at(0xC7EB) probe_vovf;    /* frames com vline<0xC0 */
volatile unsigned char  __at(0xC7ED) probe_phase;   /* 1 CPU, 2 VBlank, 3 amostra, 4 preparo */
volatile unsigned char  __at(0xC7EE) probe_worst_done; /* janela selada */
volatile unsigned char  __at(0xC7EF) probe_vline_min;  /* min da janela selada */
/* Perfil temporário de T6: checkpoints do maior VCounter já dentro do
 * display ativo (maior derrame). D0-D6 são extensão local deste projeto. */
volatile unsigned char  __at(0xC7D0) probe_profile_wait;
volatile unsigned char  __at(0xC7D1) probe_profile_stream;
volatile unsigned char  __at(0xC7D2) probe_profile_palette;
volatile unsigned char  __at(0xC7D3) probe_profile_hud;
volatile unsigned char  __at(0xC7D4) probe_profile_sat;
volatile unsigned char  __at(0xC7D6) probe_vline_spill_max;

static unsigned char hits_p1;    /* golpes conectados por P1 (telemetria) */
static unsigned char profile_sample_wait, profile_sample_stream;
static unsigned char profile_sample_palette, profile_sample_hud;
static unsigned char profile_sample_sat;
#define HUD_CELL_COUNT 33u
#define HUD_QUEUE_SIZE 64u
#define HUD_QUEUE_MASK 63u
#define HUD_TIMER_TENS 24u
#define HUD_TIMER_ONES 25u
#define HUD_SCORE_P1 26u
#define HUD_SCORE_P2 27u
#define HUD_FRAME_CELL 28u
#define HUD_BANNER_FIRST 29u
static unsigned char hud_tile_7 = T_EMPTY;
static unsigned char hud_tile_wanted[HUD_CELL_COUNT];
static unsigned char hud_tile_shown[HUD_CELL_COUNT];
static unsigned char hud_tile_dirty[HUD_CELL_COUNT];
static unsigned char hud_tile_queued[HUD_CELL_COUNT];
static unsigned char hud_queue_ids[HUD_QUEUE_SIZE];
static unsigned char hud_queue_head, hud_queue_tail;
static unsigned short health_last[2];
static unsigned char round_over, round_banner, round_timeout;
static unsigned char match_over, round_scored, round_winner;
static unsigned char round_wins[2], round_seconds, round_ticks, round_fps;
static unsigned char hud_seconds_seen, hud_wins_seen[2];
static unsigned char pad_previous;
static unsigned int round_wait;
static const unsigned char ko_k_rows[8] =
    { 0xC6, 0xCC, 0xD8, 0xF0, 0xD8, 0xCC, 0xC6, 0x00 };
static const unsigned char ko_o_rows[8] =
    { 0x3C, 0x66, 0xC3, 0xC3, 0xC3, 0x66, 0x3C, 0x00 };
static const unsigned char time_t_rows[8] =
    { 0xFF, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00 };
static const unsigned char time_i_rows[8] =
    { 0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x7E, 0x00 };
static const unsigned char time_m_rows[8] =
    { 0xC3, 0xE7, 0xDB, 0xDB, 0xC3, 0xC3, 0xC3, 0x00 };
static const unsigned char time_e_rows[8] =
    { 0xFF, 0xC0, 0xC0, 0xFC, 0xC0, 0xC0, 0xFF, 0x00 };
static const unsigned char digit_rows[10][8] = {
    { 0x3C, 0x66, 0xC3, 0xC3, 0xC3, 0x66, 0x3C, 0x00 },
    { 0x18, 0x38, 0x18, 0x18, 0x18, 0x18, 0x7E, 0x00 },
    { 0x7E, 0xC3, 0x03, 0x0E, 0x38, 0x60, 0xFF, 0x00 },
    { 0x7E, 0xC3, 0x03, 0x1E, 0x03, 0xC3, 0x7E, 0x00 },
    { 0x0E, 0x1E, 0x36, 0x66, 0xC6, 0xFF, 0x06, 0x00 },
    { 0xFF, 0xC0, 0xC0, 0xFC, 0x06, 0x03, 0xC6, 0x7C },
    { 0x3E, 0x60, 0xC0, 0xFC, 0xC6, 0xC3, 0x66, 0x3C },
    { 0xFF, 0x03, 0x06, 0x0C, 0x18, 0x18, 0x18, 0x18 },
    { 0x3C, 0x66, 0xC3, 0x66, 0x3C, 0x66, 0xC3, 0x3C },
    { 0x3C, 0x66, 0xC3, 0x63, 0x3F, 0x03, 0x06, 0x7C }
};

static void hud_init(void) {
    unsigned char i;
    hud_queue_head = hud_queue_tail = 0;
    for (i = 0; i < HUD_CELL_COUNT; i++) {
        hud_tile_wanted[i] = T_EMPTY;
        hud_tile_shown[i] = T_EMPTY;
        hud_tile_dirty[i] = 0;
        hud_tile_queued[i] = 0;
    }
}

static void hud_queue(unsigned char id, unsigned char tile) {
    if (id >= HUD_CELL_COUNT) return;
    if (hud_tile_shown[id] == tile) {
        hud_tile_dirty[id] = 0;
        return;
    }
    hud_tile_wanted[id] = tile;
    hud_tile_dirty[id] = 1;
    if (!hud_tile_queued[id]) {
        hud_queue_ids[hud_queue_tail] = id;
        hud_queue_tail = (unsigned char)((hud_queue_tail + 1u) & HUD_QUEUE_MASK);
        hud_tile_queued[id] = 1;
    }
}

static void hud_xy(unsigned char id, unsigned char *x, unsigned char *y) {
    if (id < 24u) {
        unsigned char cell = id < 12u ? id : (unsigned char)(id - 12u);
        *x = (id < 12u) ? (unsigned char)(2u + cell)
                        : (unsigned char)(29u - cell);
        *y = 1;
    } else if (id == HUD_TIMER_TENS) { *x = 15; *y = 0; }
    else if (id == HUD_TIMER_ONES) { *x = 16; *y = 0; }
    else if (id == HUD_SCORE_P1) { *x = 0; *y = 0; }
    else if (id == HUD_SCORE_P2) { *x = 27; *y = 0; }
    else if (id == HUD_FRAME_CELL) { *x = 29; *y = 0; }
    else { *x = (unsigned char)(14u + id - HUD_BANNER_FIRST); *y = 6; }
}

/* At most two BG cells are transferred in a gameplay VBlank. */
static void hud_upload_pending(void) {
    unsigned char uploaded = 0, id, x, y;
    while (uploaded < 2u && hud_queue_head != hud_queue_tail) {
        id = hud_queue_ids[hud_queue_head];
        hud_queue_head = (unsigned char)((hud_queue_head + 1u) & HUD_QUEUE_MASK);
        hud_tile_queued[id] = 0;
        if (!hud_tile_dirty[id]) continue;
        hud_xy(id, &x, &y);
        SMS_setTileatXY(x, y, hud_tile_wanted[id]);
        hud_tile_shown[id] = hud_tile_wanted[id];
        hud_tile_dirty[id] = 0;
        uploaded++;
    }
}

/* Display-off boot/round reset may flush all queued cells at once. */
static void hud_flush_all(void) {
    unsigned char i, x, y;
    for (i = 0; i < HUD_CELL_COUNT; i++) {
        if (hud_tile_dirty[i]) {
            hud_xy(i, &x, &y);
            SMS_setTileatXY(x, y, hud_tile_wanted[i]);
            hud_tile_shown[i] = hud_tile_wanted[i];
            hud_tile_dirty[i] = 0;
        }
        hud_tile_queued[i] = 0;
    }
    hud_queue_head = hud_queue_tail = 0;
}

/* HUD e glifos sao tiles de interface; personagens e cenarios continuam
 * vindo de assets com proveniencia. Cada barra usa 12 tiles de 8 px. */
static void build_health_tiles(void) {
    unsigned char tile, row, x, plane, level, slot;
    unsigned char data[32];
    for (tile = 0; tile < 18; tile++) {
        slot = (unsigned char)(tile / 9u);
        level = (unsigned char)(tile % 9u);
        for (row = 0; row < 8; row++)
            for (plane = 0; plane < 4; plane++) data[row * 4u + plane] = 0;
        for (x = 0; x < 8; x++) {
            unsigned char filled = slot
                ? (unsigned char)(x >= (unsigned char)(8u - level))
                : (unsigned char)(x < level);
            unsigned char color = filled ? (slot ? 4 : 3) : 2;
            unsigned char mask = (unsigned char)(0x80u >> x);
            for (row = 0; row < 8; row++)
                for (plane = 0; plane < 4; plane++)
                    if (color & (1u << plane))
                        data[row * 4u + plane] |= mask;
        }
        SMS_loadTiles(data, (unsigned int)(T_HEALTH + tile), sizeof(data));
    }
}

static void build_ko_glyph(unsigned char tile, const unsigned char *rows) {
    unsigned char data[32];
    unsigned char y, x;
    for (y = 0; y < 8; y++) {
        data[y * 4u] = 0;
        data[y * 4u + 1u] = 0;
        data[y * 4u + 2u] = 0;
        data[y * 4u + 3u] = 0;
        for (x = 0; x < 8; x++)
            if (rows[y] & (0x80u >> x))
                data[y * 4u] |= (unsigned char)(0x80u >> x);
    }
    SMS_loadTiles(data, tile, sizeof(data));
}

static void stage_health_bars(void) {
    unsigned char slot, cell;
    for (slot = 0; slot < 2; slot++) {
        unsigned short max_life = fight_max_life(slot);
        unsigned short life = fighters[slot].life;
        unsigned int half_pixels;
        if (health_last[slot] == life) continue;
        health_last[slot] = life;
        half_pixels = max_life
            ? ((unsigned int)life * 48u + max_life / 2u) / max_life
            : 0;
        for (cell = 0; cell < 12; cell++) {
            unsigned int used = (unsigned int)cell * 4u;
            unsigned char level = 0;
            if (half_pixels > used) {
                unsigned int remain = (half_pixels - used) * 2u;
                level = (unsigned char)(remain > 8u ? 8u : remain);
            }
            hud_queue((unsigned char)(slot * 12u + cell),
                      (unsigned char)(T_HEALTH + (slot ? 9u : 0u) + level));
        }
    }
}

static void upload_round_banner(void) {
    if (round_over && !round_banner) {
        if (round_timeout) {
            hud_queue(29, T_TIME_T);
            hud_queue(30, T_TIME_I);
            hud_queue(31, T_TIME_M);
            hud_queue(32, T_TIME_E);
        } else {
            hud_queue(30, T_KO_K);
            hud_queue(31, T_KO_O);
        }
        round_banner = 1;
    }
}

static void upload_match_hud(void) {
    unsigned char tens, ones;
    if (hud_seconds_seen != round_seconds) {
        tens = (unsigned char)(round_seconds / 10u);
        ones = (unsigned char)(round_seconds % 10u);
        hud_queue(HUD_TIMER_TENS, (unsigned char)(T_DIGIT + tens));
        hud_queue(HUD_TIMER_ONES, (unsigned char)(T_DIGIT + ones));
        hud_seconds_seen = round_seconds;
    }
    if (hud_wins_seen[0] != round_wins[0]) {
        hud_queue(HUD_SCORE_P1, (unsigned char)(T_DIGIT + round_wins[0]));
        hud_wins_seen[0] = round_wins[0];
    }
    if (hud_wins_seen[1] != round_wins[1]) {
        hud_queue(HUD_SCORE_P2, (unsigned char)(T_DIGIT + round_wins[1]));
        hud_wins_seen[1] = round_wins[1];
    }
}

static unsigned char round_leader(void) {
    if (fighters[0].life > fighters[1].life) return 0;
    if (fighters[1].life > fighters[0].life) return 1;
    return 2;                   /* empate: nenhuma vitória atribuída */
}

static void reset_round(void) {
    SMS_waitForVBlank();
    SMS_displayOff();
    fight_reset(&fighters[0], 0);
    fight_reset(&fighters[1], 1);
    SMS_initSprites();
    fight_draw();
    fight_upload_palette();
    SMS_copySpritestoSAT();
    fight_sat_copied();
    health_last[0] = 0xFFFFu;
    health_last[1] = 0xFFFFu;
    stage_health_bars();
    hud_queue(29, T_EMPTY);
    hud_queue(30, T_EMPTY);
    hud_queue(31, T_EMPTY);
    hud_queue(32, T_EMPTY);
    round_over = 0;
    round_banner = 0;
    round_timeout = 0;
    round_scored = 0;
    round_winner = 2;
    round_wait = 0;
    round_seconds = 99;
    round_ticks = 0;
    hud_seconds_seen = 0xFF;
    hud_wins_seen[0] = hud_wins_seen[1] = 0xFF;
    upload_match_hud();
    hud_flush_all();
    audio_round();
    SMS_waitForVBlank();
    SMS_displayOn();
}

/* ---- roteiro deterministico: {frame_em_que_muda, teclas_P1, teclas_P2} ----
 * Geometria inicial: P1 em x=96 (facing dir), P2 em x=152 (facing esq).
 * Cada segmento tambem exercita um gate do engine:
 *  - 120: walk aproxima P1 de 96 -> 144
 *  - 180: punch1 (state 230) acerta P2: dano derivado do CNS, hitstop 8
 *  - 300: jump (vy=2560, grav=128 -> ~40 frames no ar, terra sozinho)
 *  - 420: crouch (hurtbox baixa) · 540: guard
 *  - 660: kick (state 400) acerta P2: dano derivado do CNS
 *  - 900: P2 avanca e CRUZA P1 — auto-facing vira nos dois
 *  - 1020: kick do P2 acerta P1
 *  - 1200: kick do P2 contra P1 em guard -> sem dano, push autorado */
typedef struct { unsigned int t; unsigned char k1, k2; } ScriptRow;
static const ScriptRow script[] = {
    {   0, 0, 0 },
    { 120, K_RIGHT, 0 },
    { 142, 0, 0 },
    { 180, K_LP, 0 },
    { 196, 0, 0 },
    { 300, K_UP, 0 },
    { 316, 0, 0 },
    { 420, K_DOWN, 0 },
    { 480, 0, 0 },
    { 540, K_GUARD, 0 },
    { 600, 0, 0 },
    { 630, K_RIGHT, 0 },
    { 646, 0, 0 },                    /* P1 em ~160 */
    { 660, K_HP, 0 },
    { 684, 0, 0 },
    { 780, K_LEFT, 0 },
    { 816, 0, 0 },                    /* P1 recua p/ ~136 */
    { 900, 0, K_LEFT },
    { 930, 0, 0 },                    /* P2 cruza: fica em ~124 */
    {1020, 0, K_HP },
    {1044, 0, 0 },
    {1100, K_GUARD, 0 },
    {1200, K_GUARD, K_HP },           /* bloqueio: P1 segura guard */
    {1220, K_GUARD, 0 },
    {1320, 0, 0 },
};

/* Cursor do roteiro: as linhas sao ordenadas por t e t e monotono — avancar
 * o cursor custa O(1) por frame; a unica regressao possivel e o wrap de
 * t (unsigned int), tratada de volta ao inicio no mesmo O(1). Varre as 25
 * linhas todo frame custaria ~2x1000 ciclos (medido no carimbo E9). */
static unsigned char script_row;

static unsigned char script_keys(unsigned int t, unsigned char who) {
    unsigned char n = (unsigned char)(sizeof(script) / sizeof(script[0]));
    if (t < script[script_row].t) script_row = 0;
    while (script_row + 1 < n && t >= script[script_row + 1].t) script_row++;
    return who ? script[script_row].k2 : script[script_row].k1;
}

/* Dummy determinístico: três janelas de 60 frames (neutro, recuo curto,
 * tentativa de soco). A tecla de recuo acompanha o facing atual do P2. */
static unsigned char dummy_keys(unsigned int frame) {
    unsigned char phase = (unsigned char)((frame / 60u) % 3u);
    unsigned char within = (unsigned char)(frame % 60u);
    if (phase == 1 && within < 6)
        return fighters[1].facing ? K_RIGHT : K_LEFT;
    if (phase == 2 && within == 0)
        return K_LP;
    return 0;
}

void main(void) {
    unsigned char x, y;
    unsigned char pad, k1, k2;
    unsigned char attract = 1;
    unsigned char event1, event2, hitdone1, hitdone2;
    unsigned int t = 0;
    unsigned int life2_prev;

    SMS_displayOff();
    /* L006/SMSlib.h:53 — sprites leem a 1a metade (poses em 0..21). */
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setSpriteMode(SPRITEMODE_TALL);

    fight_init();
    input_init();
    audio_init();
    SMS_loadTiles(tile_empty, T_EMPTY, sizeof(tile_empty));
    SMS_loadTiles(tile_floor, T_FLOOR, sizeof(tile_floor));
    SMS_loadTiles(hex_glyphs, T_HEX, sizeof(hex_glyphs));
    build_health_tiles();
    build_ko_glyph(T_KO_K, ko_k_rows);
    build_ko_glyph(T_KO_O, ko_o_rows);
    build_ko_glyph(T_TIME_T, time_t_rows);
    build_ko_glyph(T_TIME_I, time_i_rows);
    build_ko_glyph(T_TIME_M, time_m_rows);
    build_ko_glyph(T_TIME_E, time_e_rows);
    for (x = 0; x < 10; x++)
        build_ko_glyph((unsigned char)(T_DIGIT + x), digit_rows[x]);

    /* CRAM de BG e entry = palette*4 + (indice_do_pixel & 3) (0..15), NAO o
     * numero da palette. Tile SMS = 4 bytes por linha, um por plano: chao
     * (0x00,0xFF,0x00,0xFF) -> p1|p3 = indice 10 -> cor 2; tile 126 -> pal 2
     * => entry 10. Glifos: pixel indice 1, tile 128+g -> pal g&3 => entries
     * 1,5,9,13. Errar a entry deixa a real nao-inicializada: o chao saiu
     * cinza/oliva/rosa/ciano conforme o humor do emulador entre runs — cor
     * fora da paleta mestra em dois deles (semantic gate reprovaria). */
    SMS_setBGPaletteColor(0, 0x00);    /* backdrop */
    SMS_setBGPaletteColor(1, 0x3F);
    SMS_setBGPaletteColor(5, 0x3F);
    SMS_setBGPaletteColor(9, 0x3F);
    SMS_setBGPaletteColor(13, 0x3F);   /* branco do glifo nas 4 palettes */
    SMS_setBGPaletteColor(2, 0x05);    /* fundo escuro das barras */
    SMS_setBGPaletteColor(3, 0x0C);    /* vida P1 */
    SMS_setBGPaletteColor(4, 0x30);    /* vida P2 */
    SMS_setBGPaletteColor(10, 0x15);   /* cinza do chao (pal 2, cor 2) */
    for (y = 0; y < 16; y++)
        for (x = 0; x < 32; x++)
            SMS_setTileatXY(x, y, T_EMPTY);
    for (y = 16; y < 24; y++)         /* chao em y=128 — cena no viewport */
        for (x = 0; x < 32; x++)
            SMS_setTileatXY(x, y, T_FLOOR);

    hud_init();

    fight_reset(&fighters[0], 0);
    fight_reset(&fighters[1], 1);
    health_last[0] = 0xFFFFu;
    health_last[1] = 0xFFFFu;
    round_over = 0;
    round_banner = 0;
    round_timeout = 0;
    match_over = 0;
    round_scored = 0;
    round_winner = 2;
    round_wins[0] = round_wins[1] = 0;
    round_seconds = 99;
    round_ticks = 0;
    round_fps = (detect_vdp_wrap() == 0xF2) ? 50 : 60;
    hud_seconds_seen = 0xFF;
    hud_wins_seen[0] = hud_wins_seen[1] = 0xFF;
    pad_previous = 0;
    round_wait = 0;
    stage_health_bars();
    upload_match_hud();
    hud_flush_all();
    life2_prev = fight_max_life(1);
    dbg_frame = 0;
    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 1;
    probe_region_hz = round_fps;
    probe_special = 0;
    probe_pattern = 0;
    probe_frame = 0;
    probe_vline = 0;
    probe_vovf = 0;
    probe_phase = 0;
    probe_worst_done = 0;
    probe_vline_min = 0xFF;
    probe_vline_spill_max = 0xFF;
    probe_profile_wait = 0;
    probe_profile_stream = 0;
    probe_profile_palette = 0;
    probe_profile_hud = 0;
    probe_profile_sat = 0;
    hits_p1 = 0;

    /* A SAT inicial e a paleta ficam prontas antes de ligar o display. */
    SMS_initSprites();
    fight_draw();
    fight_upload_palette();
    SMS_copySpritestoSAT();
    fight_sat_copied();
    SMS_displayOn();

    for (;;) {
        SMS_waitForVBlank();
        profile_sample_wait = SMS_VCounterPort;

        /* Janela de VBlank: todas as escritas de VDP ficam neste bloco. */
        probe_phase = 2;
        stream_step();
        profile_sample_stream = SMS_VCounterPort;
        fight_upload_palette();
        profile_sample_palette = SMS_VCounterPort;
        x = (unsigned char)(T_HEX + ((dbg_frame >> 7) & 0xF));
        if (x != hud_tile_7) {
            hud_queue(HUD_FRAME_CELL, x);
            hud_tile_7 = x;
        }
        hud_upload_pending();
        profile_sample_hud = SMS_VCounterPort;
        SMS_copySpritestoSAT();
        fight_sat_copied();
        profile_sample_sat = SMS_VCounterPort;

        /* A ROM mede o trecho que contém uploads, CRAM, HUD e SAT. O trabalho
         * de CPU começa depois; só um valor <0xC0 conta como derrame. */
        if (!probe_worst_done) {
            probe_phase = 3;
            probe_vline = SMS_VCounterPort;
            if (probe_vline < probe_vline_min)
                probe_vline_min = probe_vline;
            if (probe_vline < 0xC0) {
                probe_vovf++;
                if (probe_vline_spill_max == 0xFF ||
                    probe_vline > probe_vline_spill_max) {
                    probe_vline_spill_max = probe_vline;
                    probe_profile_wait = profile_sample_wait;
                    probe_profile_stream = profile_sample_stream;
                    probe_profile_palette = profile_sample_palette;
                    probe_profile_hud = profile_sample_hud;
                    probe_profile_sat = profile_sample_sat;
                }
            }
            if (probe_frame == (WORST_FRAME_WINDOW - 1u))
                probe_worst_done = 1;
        }
        probe_frame++;

        /* Daqui ate o proximo wait: apenas CPU e tabela de sprites em RAM. */
        probe_phase = 1;
        /* PSG nao escreve no VDP; manter o sequenciador fora do orçamento
         * crítico de VRAM deixa o VBlank só com pose, HUD e SAT. */
        audio_frame();
        /* Qualquer tecla física encerra a demonstração automática. P2 passa
         * sempre pelo dummy determinístico da cena ken_vs_dummy. */
        pad = input_read();
        if (pad) attract = 0;
        k1 = attract ? script_keys(t, 0) : pad;
        k2 = dummy_keys(t);

        input_tick(k1, fighters[0].facing);
        if (input_pattern_hit(KEN_CUT_CMD_BUTTON1))  probe_pattern |= 0x01;
        if (input_pattern_hit(KEN_CUT_CMD_FORWARD_DOUBLE)) probe_pattern |= 0x02;
        if (input_pattern_hit(CMD_QCF_B1)) {
            k1 |= K_SPECIAL;
            probe_pattern |= 0x04;
        }

        SMS_initSprites();
        if (!round_over) {
            hitdone1 = fighters[0].hit_done;
            hitdone2 = fighters[1].hit_done;
            event1 = fight_step(&fighters[0], k1, k2);
            event2 = fight_step(&fighters[1], k2, k1);
            if (event1 == FIGHT_EVENT_PUNCH || event2 == FIGHT_EVENT_PUNCH)
                audio_punch();
            if (event1 == FIGHT_EVENT_KICK || event2 == FIGHT_EVENT_KICK)
                audio_kick();
            if (event1 == FIGHT_EVENT_SPECIAL ||
                event2 == FIGHT_EVENT_SPECIAL) {
                audio_special();
                probe_special = 1;
            }
            if ((!hitdone1 && fighters[0].hit_done) ||
                (!hitdone2 && fighters[1].hit_done))
                audio_hit();
            if (!fighters[0].life || !fighters[1].life) {
                if (!fighters[0].life) fight_set_ko(&fighters[0]);
                if (!fighters[1].life) fight_set_ko(&fighters[1]);
                round_over = 1;
                round_wait = 180u;
                round_scored = 0;
                round_timeout = 0;
                if (!fighters[0].life && fighters[1].life)
                    round_winner = 1;
                else if (fighters[0].life && !fighters[1].life)
                    round_winner = 0;
                else
                    round_winner = 2;
                audio_ko();
            } else if (round_fps && round_seconds) {
                if (++round_ticks >= round_fps) {
                    round_ticks = 0;
                    round_seconds--;
                    if (!round_seconds) {
                        round_over = 1;
                        round_wait = 180u;
                        round_scored = 0;
                        round_timeout = 1;
                        round_winner = round_leader();
                    }
                }
            }
        } else if (round_wait) {
            round_wait--;
        } else if (match_over) {
            if ((pad & K_LP) && !(pad_previous & K_LP)) {
                round_wins[0] = round_wins[1] = 0;
                match_over = 0;
                reset_round();
                life2_prev = fight_max_life(1);
            }
        } else {
            if (!round_scored) {
                if (round_winner < 2) {
                    round_wins[round_winner]++;
                    if (round_wins[round_winner] >= 2) match_over = 1;
                }
                round_scored = 1;
            }
            if (!match_over) {
                reset_round();
                life2_prev = fight_max_life(1);
            }
        }
        /* Compute digits and coalesce HUD changes in CPU time; VBlank only
         * transfers the bounded two-cell queue. */
        upload_match_hud();
        upload_round_banner();
        fight_draw();
        stage_health_bars();
        probe_phase = 4;

        if (fighters[1].life < life2_prev) hits_p1++;
        life2_prev = fighters[1].life;
        probe_hp = (unsigned char)fighters[0].life;
        probe_score = hits_p1;
        probe_boss = (unsigned char)fighters[1].life;
        probe_over = round_over;
        probe_state = fighters[0].state;
        probe_wave = attract;
        probe_keys = (unsigned char)SMS_getKeysHeld();
        probe_pose = fighters[0].anim;
        probe_px = (unsigned char)(fighters[0].x >> 8);
        probe_py = (unsigned char)(fighters[0].y >> 8);
        probe_p2x = (unsigned char)(fighters[1].x >> 8);
        probe_round_score = (unsigned char)(round_wins[0] |
                                             (round_wins[1] << 4));
        probe_timer = round_seconds;

        /* O HUD físico acompanha dbg_frame no próximo VBlank; período
         * 128 / 8 / 1 como no contrato measure_frame_advance. */
        dbg_frame++;
        t++;
        pad_previous = pad;
    }
}
