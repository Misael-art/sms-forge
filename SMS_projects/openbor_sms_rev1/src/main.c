/*
 * openbor_sms_rev1 — piloto O2 (VDP / primeira fatia jogavel).
 *
 * Escopo (doc/artifacts/o2_vdp_pilot_scope_20261015.json):
 * - movimento no plano de chao (x + profundidade z, z=180 inicial),
 * - facing por espelho (padroes proprios; o VDP do SMS nao tem flip),
 * - animacao de idle/walk (delays convertidos para NTSC),
 * - um inimigo presente (long, idle, virado para o jogador) e HUD de duas barras.
 *
 * Fora do O2 (declarado, nao silencioso): pulo/ataque/dano/IA (O3),
 * camera/rolagem/terreno completos (O4), PAL e audio.
 *
 * Decisoes medidas (doc/15-tdd.md e registro de emissao):
 * - sprites TALL (8x16) na primeira metade da VRAM (reg6 = 0xFB, L006);
 * - metasprite por tabela o2_pose (celulas 8x16); nao existe modo SMS que
 *   desenhe arte mais larga que 8px, a montagem e por celulas;
 * - camera quantizada em 8px com anel de colunas mod-32 e BGScrollX =
 *   (-cam) & 0xFF: o registrador do VDP desloca a imagem para a direita
 *   por N, entao o sinal correto e -cam; o wrap de 256 px casa com o wrap
 *   do anel e a janela [cam_col..cam_col+31] aparece contigua (1 coluna
 *   por 8 px, 44 B); LOCKHSCROLL (reg0 bit 6) mantem o HUD em BG
 *   (linhas 0..1) fora do scroll sem IRQ de linha, e LEFTCOLBLANK
 *   (reg0 bit 5, L043) cobre o primeiro tile da esquerda;
 * - orcamento por scanline em runtime: o pior caso medido (jogador idle +
 *   long sobrepostos) somaria 10 entradas SAT/linha, acima das 8 do VDP;
 *   o jogador entra inteiro e o inimigo entra na ordem da tabela
 *   (banda, densidade desc, coluna) com corte em 8/linha. Manifests do pior
 *   caso em data/generated/emit/ passaram em audit_sprite_line_sim;
 * - toda escrita de VRAM acontece no bloco de VBlank (colunas de PNT e SAT);
 *   a tabela de sprites e o orcamento rodam na fase de CPU.
 */
#include "SMSlib.h"
#include "o2/pal_bg.h"
#include "o2/pal_spr.h"
#include "o2/spr_tiles.h"
#include "o2/spr_meta.h"
#include "o2/bg_tiles.h"
#include "o2/bg_cols.h"
#include "o2/hud_tiles.h"
#include "o2/level.h"
#include "o2/enemy_mask.h"

/* VCounter: porta do registro de status. Molde: luta_mugen src/main.c:45,
 * MSSF2T src/main.c:58. */
__sfr __at (0x7e) SMS_VCounterPort;

/* Corredor de sondas 0xC7E0.. (contrato measure_runtime_probe.py; todo
 * __at() precisa ser volatile — L009). */
volatile unsigned char __at(0xC7E0) probe_magic0;
volatile unsigned char __at(0xC7E1) probe_magic1;
volatile unsigned char __at(0xC7E2) probe_magic2;
volatile unsigned char __at(0xC7E3) probe_magic3;
volatile unsigned char __at(0xC7E4) probe_schema;

volatile unsigned char __at(0xC7EA) probe_vline;      /* VCounter pos VBlank */
volatile unsigned int  __at(0xC7EB) probe_vovf;       /* frames com vline < 0xC0 */
volatile unsigned char __at(0xC7ED) probe_phase;      /* 1 CPU, 2 VBlank, 3 amostra */
volatile unsigned char __at(0xC7EE) probe_worst_done; /* janela selada */
volatile unsigned char __at(0xC7EF) probe_vline_min;  /* min da janela selada */

volatile unsigned int  __at(0xC7F0) probe_frame;      /* 16 bits: fps real */
volatile unsigned char __at(0xC7F2) probe_hp;         /* vida do jogador */
volatile unsigned char __at(0xC7F3) probe_score;      /* sem placar no O2 */
volatile unsigned char __at(0xC7F4) probe_boss;       /* vida do inimigo */
volatile unsigned char __at(0xC7F5) probe_over;       /* sem combate no O2 */
volatile unsigned char __at(0xC7F6) probe_state;      /* 0 = caminhando */
volatile unsigned char __at(0xC7F7) probe_wave;       /* sem ondas no O2 */
volatile unsigned char __at(0xC7F8) probe_keys;       /* Port A crua (byte baixo) */
volatile unsigned char __at(0xC7F9) probe_pose;       /* indice de pose exibido */
volatile unsigned char __at(0xC7FA) probe_px;         /* jogador.x >> 8 */
volatile unsigned char __at(0xC7FB) probe_pz;         /* jogador.z (profundidade) */
volatile unsigned char __at(0xC7FC) probe_p2x;        /* inimigo.x >> 8 */
volatile unsigned char __at(0xC7FD) probe_p1_target_pose;
volatile unsigned char __at(0xC7FE) probe_round_score;
volatile unsigned char __at(0xC7FF) probe_timer;

#define O2_WORST_FRAME_WINDOW 1024u   /* frames ate selar a janela de pior quadro */
#define O2_ANIM_IDLE 0u
#define O2_ANIM_WALK 1u
#define O2_FACING_LEFT 0u
#define O2_FACING_RIGHT 1u

static unsigned int px;            /* mundo; x 1:1 com o fonte */
static unsigned char pz;           /* profundidade (banda de piso) */
static unsigned char facing;
static unsigned char anim;
static unsigned char walk_frame;
static unsigned char anim_timer;
static unsigned int cam;           /* quantizada em 8 px (cam & ~7) */
static unsigned char written_col;  /* ultima coluna de mundo escrita na PNT */

static unsigned char pose_index(void)
{
    if (anim == O2_ANIM_IDLE)
        return facing;
    return (unsigned char)(2u + ((unsigned char)(walk_frame << 1)) + facing);
}

/* Escreve a coluna de mundo w nas linhas 2..23 (as linhas 0..1 sao o HUD). */
static void write_bg_col(unsigned char world_col)
{
    const unsigned char *src = &o2_bg_cols[(unsigned int)world_col * O2_STAGE_ROWS];
    unsigned char screen_col = (unsigned char)(world_col & 31u);
    unsigned char i;
    for (i = 0; i < O2_STAGE_ROWS; i++) {
        SMS_setNextTileatXY(screen_col, (unsigned char)(i + 2u));
        SMS_setTile((unsigned int)(O2_TILE_BG_BASE + src[i]));
    }
}

/* Anel de 32 colunas alinhado ao wrap de 256 px da PNT: a coluna de mundo w
 * mora no slot (w & 31) e o BGScrollX carrega (cam & 0xFF), de modo que a
 * janela [cam_col..cam_col+31] aparece contigua na tela. Avanca escrevendo
 * colunas novas; ao voltar a camera, reescreve a coluna esquerda que o anel
 * sobrescreveu. No maximo 1 coluna por frame (movimento e 1 px/frame). */
static void stream_columns(void)
{
    int cam_col = (int)(cam >> 3);
    int right = cam_col + 31;
    while ((int)written_col < right) {
        written_col++;
        write_bg_col(written_col);
    }
    while ((int)written_col > right) {
        write_bg_col((unsigned char)(written_col - 32));
        written_col--;
    }
}

/* HUD estatico: linha 0 = barra do jogador (verde), linha 1 = do inimigo
 * (vermelha); trilho preto. No O2 nao ha dano, entao e desenhado no boot. */
static void draw_hud(void)
{
    unsigned char i;
    unsigned char fill_p = (unsigned char)((unsigned int)O2_HP_PLAYER
                                           * O2_HUD_PLAYER_COLS / O2_HP_PLAYER);
    unsigned char fill_e = (unsigned char)((unsigned int)O2_HP_ENEMY
                                           * O2_HUD_ENEMY_COLS / O2_HP_ENEMY);
    for (i = 0; i < 32u; i++) {
        /* unsigned int: os tiles de BG/HUD passam de 255 (244..438) e um
         * unsigned char truncaria o indice para a faixa dos sprites. */
        unsigned int tp = O2_TILE_HUD_BLACK;
        unsigned int te = O2_TILE_HUD_BLACK;
        if (i >= O2_HUD_COL0
            && i < (unsigned char)(O2_HUD_COL0 + O2_HUD_PLAYER_COLS)
            && (unsigned char)(i - O2_HUD_COL0) < fill_p)
            tp = O2_TILE_HUD_GREEN;
        if (i >= O2_HUD_COL0
            && i < (unsigned char)(O2_HUD_COL0 + O2_HUD_ENEMY_COLS)
            && (unsigned char)(i - O2_HUD_COL0) < fill_e)
            te = O2_TILE_HUD_RED;
        SMS_setNextTileatXY(i, O2_HUD_PLAYER_ROW);
        SMS_setTile(tp);
        SMS_setNextTileatXY(i, O2_HUD_ENEMY_ROW);
        SMS_setTile(te);
    }
}

/* Tabela de sprites (RAM). Roda na fase de CPU; o VBlank so copia a SAT
 * pronta. O corte do inimigo vem pre-computado do emit (enemy_mask.h): o
 * runtime consulta o bit da mascara por (pose do jogador, pz) em vez de
 * contar linhas — a contagem em C (acesso indexado do SDCC) custava ~1
 * frame por volta e derrubava o jogo para 1/3 de loop por frame. */
static void draw_sprites(void)
{
    const o2_pose *pp;
    const o2_cell *c;
    const unsigned char *m;
    unsigned int mlo;
    unsigned char mhi;
    unsigned char i;

    /* Jogador: sempre inteiro (prioridade total; max 5 celulas/linha). */
    pp = &o2_ax_poses[pose_index()];
    for (i = 0; i < pp->count; i++) {
        c = &pp->cells[i];
        SMS_addSprite((unsigned char)((int)px - (int)cam + c->dx),
                      (unsigned char)((int)pz - 32 + c->dy),
                      c->tile);
    }

    /* Inimigo: mascara de inclusao por (pose, pz); celulas fora da tela
     * (x > 255) nao sao desenhadas, mas ja contam na mascara (politica
     * conservadora gerada no emit). */
    m = &o2_enemy_masks[((unsigned int)pose_index() * O2_ENEMY_MASK_PZ_COUNT
                         + (unsigned int)(pz - O2_ENEMY_MASK_PZ_MIN))
                        * O2_ENEMY_MASK_BYTES];
    mlo = (unsigned int)m[0] | ((unsigned int)m[1] << 8);
    mhi = m[2];
    pp = &o2_enemy_poses[0];
    for (i = 0; i < pp->count; i++) {
        int sxv;
        c = &pp->cells[i];
        if (i < 16u) {
            if (!(mlo & (unsigned int)(1u << i)))
                continue;
        } else {
            if (!(mhi & (unsigned char)(1u << (i - 16u))))
                continue;
        }
        sxv = (int)O2_ENEMY_X - (int)cam + c->dx;
        if (sxv > 255)
            continue;
        SMS_addSprite((unsigned char)sxv,
                      (unsigned char)((int)O2_ENEMY_Z - 32 + c->dy),
                      c->tile);
    }
}

static void update_probe_fields(unsigned int keys)
{
    probe_hp = O2_HP_PLAYER;
    probe_boss = O2_HP_ENEMY;
    probe_score = 0;
    probe_over = 0;
    probe_state = 0;
    probe_wave = 0;
    probe_keys = (unsigned char)(keys & 0xFFu);
    probe_pose = pose_index();
    probe_px = (unsigned char)(px >> 8);
    probe_pz = pz;
    probe_p2x = (unsigned char)(O2_ENEMY_X >> 8);
    probe_p1_target_pose = 0;
    probe_round_score = 0;
    probe_timer = 0;
}

void main(void)
{
    unsigned char i;
    unsigned int keys;

    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_useFirstHalfTilesforSprites(1);
    SMS_displayOff();

    /* H-scroll ao vivo (reg0): LOCKHSCROLL congela o scroll das linhas 0..1
     * (HUD em BG, sem IRQ de linha) e LEFTCOLBLANK cobre o primeiro tile da
     * esquerda (L043). */
    SMS_VDPturnOnFeature(VDPFEATURE_LEFTCOLBLANK | VDPFEATURE_LOCKHSCROLL);

    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 1;
    probe_frame = 0;
    probe_vovf = 0;
    probe_worst_done = 0;
    probe_vline_min = 0xFFu;
    probe_phase = 0;

    px = O2_PLAYER_START_X;
    pz = O2_PLAYER_START_Z;
    facing = O2_FACING_RIGHT;   /* spawns olham para o oponente */
    anim = O2_ANIM_IDLE;
    walk_frame = 0;
    anim_timer = 0;
    cam = 0;
    written_col = 31;

    SMS_loadTiles(o2_spr_tiles, O2_TILE_SPR_BASE, O2_SPR_TILES_SIZE);
    SMS_loadTiles(o2_bg_tiles, O2_TILE_BG_BASE, O2_BG_TILES_SIZE);
    SMS_loadTiles(o2_hud_tiles, O2_TILE_HUD_GREEN, O2_HUD_TILES_SIZE);
    SMS_loadBGPalette(o2_pal_bg);
    SMS_loadSpritePalette(o2_pal_spr);
    SMS_setBackdropColor(1);    /* preto: P1[1] = 0x00 (backdrop usa a
                                 * paleta de sprite; a faixa do
                                 * LEFTCOLBLANK tambem fica preta) */

    for (i = 0; i < 32u; i++)
        write_bg_col(i);
    draw_hud();

    SMS_initSprites();
    draw_sprites();
    SMS_copySpritestoSAT();
    update_probe_fields(0);

    SMS_displayOn();

    for (;;) {
        SMS_waitForVBlank();

        /* Bloco de VBlank: so SAT pronta, (no maximo) 1 coluna de PNT e o
         * registrador de scroll horizontal. O registrador do VDP desloca a
         * imagem para a direita por N; para a janela comecar em cam (pixel
         * de mundo): N = (-cam) & 0xFF. Com o anel em slots mod-32, o wrap
         * de 256 px fecha a contiguidade. */
        probe_phase = 2;
        SMS_copySpritestoSAT();
        stream_columns();
        SMS_setBGScrollX((unsigned char)(0u - cam));
        if (!probe_worst_done) {
            probe_phase = 3;
            probe_vline = SMS_VCounterPort;
            if (probe_vline < probe_vline_min)
                probe_vline_min = probe_vline;
            if (probe_vline < 0xC0u)
                probe_vovf++;
            if (probe_frame == (O2_WORST_FRAME_WINDOW - 1u))
                probe_worst_done = 1;
        }
        probe_frame++;
        probe_phase = 1;

        /* Fase de CPU: input, estado, tabela de sprites e orcamento. */
        keys = SMS_getKeysStatus();
        {
            unsigned char moving = 0;
            unsigned char anim_advance = 0;
            if (keys & PORT_A_KEY_LEFT) {
                if (px > O2_PLAYER_MIN_X)
                    px -= O2_WALK_SPEED;
                facing = O2_FACING_LEFT;
                moving = 1;
            }
            if (keys & PORT_A_KEY_RIGHT) {
                if (px < O2_PLAYER_MAX_X)
                    px += O2_WALK_SPEED;
                facing = O2_FACING_RIGHT;
                moving = 1;
            }
            if (keys & PORT_A_KEY_UP) {
                if (pz > O2_Z_MIN)
                    pz--;
                moving = 1;
            }
            if (keys & PORT_A_KEY_DOWN) {
                if (pz < O2_Z_MAX)
                    pz++;
                moving = 1;
            }
            if (moving) {
                anim = O2_ANIM_WALK;
                anim_advance = 1;
            } else {
                anim = O2_ANIM_IDLE;
                anim_timer = 0;
                walk_frame = 0;
            }
            if (anim_advance) {
                anim_timer++;
                if (anim_timer >= O2_ANIM_DELAY_WALK) {
                    anim_timer = 0;
                    walk_frame ^= 1u;
                }
            }
        }
        {
            int c = (int)px - O2_CAM_DX;
            if (c < 0)
                c = 0;
            if (c > (int)O2_CAM_MAX)
                c = (int)O2_CAM_MAX;
            cam = (unsigned int)(c & (~7));
        }

        SMS_initSprites();
        draw_sprites();
        update_probe_fields(keys);
    }
}
