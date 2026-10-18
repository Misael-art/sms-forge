/*
 * openbor_sms_rev1 — runtime O3: combate (fatia do plano OpenBOR->SMS).
 *
 * Escopo O3 (doc/artifacts/o3_combat_scope_20261016.json, D1..D12):
 * - movimento no plano (x + profundidade z) com walk 100 px/s (Q8.8);
 * - pulo com arco tabelado (D5: o3_jump_y/x, 40 frames NTSC) e deriva fixa
 *   na direcao do facing (jumpmove 3 do fonte fica sem uso — declarado);
 * - ataque (A = PORT_A_KEY_1) -> janela ativa -> hit -> dano -> pain2 ou
 *   queda (toss) -> land -> rise/death, com hitstop (5 f ax / 3 f long),
 *   guarda de 13 frames por vitima e 1 hit por ativacao (D4/D6);
 * - pulo no botao B (PORT_A_KEY_2);
 * - IA: facing + velocidade recomputados todo frame; juizo de ataque com
 *   stalltime = gs/5 = 40 ticks = 12 frames NTSC (openbor.c 43183/43464);
 * - entrada: spawn em altitude 200 cai pela tabela o3_entry_y (38 frames;
 *   pousa -> idle direto, como o pouso do pulo).
 *
 * Decisoes medidas que este arquivo implementa:
 * - D8 (uploads): slots duplos por ator; o upload de uma pose (<= 1856 B) e
 *   fatiado em sub-chunks de O3_COMMIT_SUB bytes dentro do bloco de VBlank
 *   (stream_commit), com teto por ator O3_UPLOAD_CHUNK = 320 B/frame; a
 *   pose SEGUINTE e pre-carregada no slot nao exibido durante a janela da
 *   pose corrente; o slot escrito nunca e exibido (sem rasgo). "Pose ready":
 *   enquanto a pose pretendida nao esta no ar, o avanco da animacao/fisica
 *   segura (D8), o input nao.
 *   M5 (medido): a copia e ADAPTATIVA — rele o VCounter antes de cada
 *   sub-chunk e para quando a janela util (0xC0..0xFF) nao cobre custo +
 *   margem. Chunk fixo de 640 derramava em 1304/3000 quadros (MWF) e
 *   sustentava 45,7 fps; a janela inteira so comporta ~300 B/frame de
 *   commit depois de SAT/PNT/HUD. Medicao 2026-10-17 no Emulicious:
 *   escrita VRAM em display ativo custa ~1-2 linhas de varredura por byte
 *   e derrubava o loop para 13 fps; o lab M1 (1856 B/loop em rajada apos o
 *   VBlank) roda 5,1 frames VDP/loop aqui contra 1:1 no BlastEm. A amostra
 *   do probe vem DEPOIS dos commits: o orcamento do corredor de VBlank fica
 *   medido por vline/vovf.
 * - D9-a2 (corte por linha): o jogador entra inteiro e desenha sempre que
 *   1 <= topo <= 191; o inimigo e visitado na ordem ja empacotada
 *   (densidade desc/banda/coluna) e uma celula cai quando
 *   ec[linha] + 1 + max(o3_ax_rows[pose do jogador][linhas sobrepostas])
 *   passaria de 8. Espelha o3_compose_rows/o3_compose_sprites do emissor.
 *   Celulas com topo >= 192 nao desenham nem contam (inertes no emit) e
 *   celulas fora de [0,255] em x nao desenham (politica conservadora).
 * - Leitura do hit (D4): caixa do atacante [alt+y_rel, alt+y_rel+h];
 *   caixa da vitima = bbox 229,149,22,56 relativa a 240,204, ou seja
 *   x [-11,+11] e banda vertical [alt-55, alt+1]; sobreposicao com
 *   desigualdades inclusivas (leitura literal do engine == leitura
 *   geometrica no envelope O3: pulo <= 54, toss <= 46).
 * - Toss: a queda reinicia a arte em fall2 quadro 0 (delay 255, segurado no
 *   ar); no pouso pula para o landframe (quadro 1) e ao fim da sequencia
 *   vai para rise (vivo) ou death (hp 0). Re-hit durante a queda so atualiza
 *   hp/guarda/hitstop. Vitima aerea entra no arco toss na altitude atual
 *   (aproximacao declarada; sem reinicio do chao).
 * - O pior caso da tabela toss termina em 2 px (O3_TOSS_FRAMES; pouso
 *   forcado a 0 no fim — 1 frame de diferenca, declarado).
 *
 * Fora do O3 (declarado, nao silencioso): placar/ondas/terreno/camera
 * completa (O4+), audio (M7), PAL, juggle fino, jumpmove, body-block.
 *
 * VRAM: sprites em [0,231] (2 slots x 29 celulas x 2 tiles x 2 atores);
 * BG na base 232; HUD 424/425/426 (plano o3_vram_plan_20261017). Bancos
 * 2..6 chegam via makesms -mbank (res/o3/banks/...) e sao lidos em
 * 0x8000+addr depois de SMS_mapROMBank (D1/D8).
 *
 * Sondas: corredor 0xC7E0..0xC7FF (contrato measure_runtime_probe.py).
 * Schema v2 (D10): mesmos enderecos do O2; 0xC7FD py (altitude do jogador),
 * 0xC7FE p2state (FSM do inimigo) e 0xC7FF p2z (profundidade do inimigo)
 * substituem campos mortos do O2. Todo __at() e volatile (L009).
 */
#include "SMSlib.h"
#include "o2/pal_bg.h"
#include "o2/pal_spr.h"
#include "o2/bg_tiles.h"
#include "o2/bg_cols.h"
#include "o2/hud_tiles.h"
#include "o2/level.h"     /* geometria do HUD (colunas/linhas) */
#include "o3/level.h"
#include "o3/o3_poses.h"
#include "o3/o3_blocks.h"
#include "o3/o3_anim.h"
#include "o3/o3_arcs.h"
#include "o3/o3_rows.h"

/* Header SEGA + SDSC (boot em Master System real/emulador que checa o
 * header; M5). SDSC com AUTO_DATE (0,0,0 no fonte). */
SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "openbor_sms_rev1 O3",
                                "combate O3: stream bancado, hit, IA");

/* VCounter: porta do registro de status (molde O2/luta_mugen). */
__sfr __at (0x7e) SMS_VCounterPort;

/* Corredor de sondas 0xC7E0..0xC7FF (contrato; todo __at volatile — L009). */
volatile unsigned char __at(0xC7E0) probe_magic0;
volatile unsigned char __at(0xC7E1) probe_magic1;
volatile unsigned char __at(0xC7E2) probe_magic2;
volatile unsigned char __at(0xC7E3) probe_magic3;
volatile unsigned char __at(0xC7E4) probe_schema;
/* Onde do pior quadro (M5): capturado quando vline bate novo min. */
volatile unsigned char __at(0xC7E5) probe_min_frame_lo;
volatile unsigned char __at(0xC7E6) probe_min_frame_hi;
volatile unsigned char __at(0xC7E7) probe_min_cam_lo;
volatile unsigned char __at(0xC7E8) probe_min_cam_hi;
volatile unsigned char __at(0xC7E9) probe_min_p2state;
volatile unsigned char __at(0xC7EA) probe_vline;      /* VCounter pos VBlank */
volatile unsigned int  __at(0xC7EB) probe_vovf;       /* frames com vline < 0xC0 */
volatile unsigned char __at(0xC7ED) probe_phase;      /* 1 CPU, 2 VBlank, 3 amostra */
volatile unsigned char __at(0xC7EE) probe_worst_done; /* janela selada */
volatile unsigned char __at(0xC7D2) probe_vline_min;  /* min da janela selada (MWF) */

volatile unsigned int  __at(0xC7F0) probe_frame;      /* 16 bits: fps real */
volatile unsigned char __at(0xC7F2) probe_hp;         /* vida do jogador */
volatile unsigned char __at(0xC7F3) probe_score;      /* sem placar no O3 */
volatile unsigned char __at(0xC7F4) probe_boss;       /* vida do inimigo */
volatile unsigned char __at(0xC7F5) probe_over;       /* jogador morreu */
volatile unsigned char __at(0xC7F6) probe_state;      /* FSM do jogador */
volatile unsigned char __at(0xC7F7) probe_wave;       /* sem ondas no O3 */
volatile unsigned char __at(0xC7F8) probe_keys;       /* Port A crua (byte baixo) */
volatile unsigned char __at(0xC7F9) probe_pose;       /* pose pretendida do jogador */
volatile unsigned char __at(0xC7FA) probe_px;         /* jogador.x >> 8 */
volatile unsigned char __at(0xC7FB) probe_pz;         /* jogador.z (profundidade) */
volatile unsigned char __at(0xC7FC) probe_p2x;        /* inimigo.x >> 8 */
volatile unsigned char __at(0xC7FD) probe_py;         /* v2: altitude do jogador */
volatile unsigned char __at(0xC7FE) probe_p2state;    /* v2: FSM do inimigo */
volatile unsigned char __at(0xC7FF) probe_p2z;        /* v2: profundidade do inimigo */

#define WORST_FRAME_WINDOW 3000u  /* janela canonica do worst-frame (MWF) */
#define O3_UPLOAD_CHUNK 320u         /* teto por ator do commit por frame (M5) */
#define O3_COMMIT_SUB   64u          /* granularidade do commit adaptativo */
/* Margens do gate de commit (linhas restantes no VCounter):
 *  MARGIN  = chunk + rabo (saida + probe ~2,5) + jitter ~3 => 16. Com o custo
 *            antigo (~16 linhas/64 B) o M5 precisou de 30 porque o chunk era
 *            seguido do rabo de 25 linhas; o hoist de locais + gate antes do
 *            prologo baixaram o custo para ~10 e o rabo para ~2,5.
 *  PROLOG  = MARGIN + prologo do ator (~7,3): nao pagar banco/enderecos se o
 *            primeiro chunk ja nao cabe. */
#define O3_COMMIT_MARGIN 22u
#define O3_COMMIT_PROLOG (O3_COMMIT_MARGIN + 8u)
#define O3_AI_THINK 12u              /* juizo de ataque (gs/5 = 40 ticks NTSC) */
#define O3_DRAW_ASM 1                /* 1 = nucleo asm do draw (M5); 0 = C-ref (A/B) */
#define O3_SPILL_TRACE 0             /* 0 no fechamento M5; 1 = diag TEMP (nao entregar) */
#define O3_FACING_LEFT 0u
#define O3_FACING_RIGHT 1u

/* FSM (semantica do probe): entrada = estado 4 (fall). */
#define O3_S_IDLE 0u
#define O3_S_WALK 1u
#define O3_S_ATTACK 2u
#define O3_S_PAIN 3u
#define O3_S_FALL 4u
#define O3_S_RISE 5u
#define O3_S_DEAD 6u

/* Arcos por tabela (D5): entrada/toss/pulo. */
#define O3_ARC_NONE 0u
#define O3_ARC_JUMP 1u
#define O3_ARC_TOSS 2u
#define O3_ARC_ENTRY 3u

/* Caixa da vitima (D4: bbox 229,149,22,56 rel. 240,204). */
#define O3_BBOX_HALF_W 11
#define O3_BBOX_UP 55
#define O3_BBOX_DOWN 1

#define O3_SLOT_SPAN 58u  /* tiles entre slot A e B (29 celulas x 2) */
#define O3_SLOT_TILE(slot_a, b) ((unsigned char)((slot_a) + ((b) ? O3_SLOT_SPAN : 0u)))

/* Conjunto de animacoes por ator (ids diferem entre ax e long). */
typedef struct {
    const o3_anim *tbl;
    unsigned char idle, walk, attack, jump, pain, fall, rise, death;
} o3_as;

/* Arte por ator: poses, blocos bancados e base do slot A. */
typedef struct {
    const o3_pose *poses;
    const o3_block *blocks;
    unsigned char slot_a;
} o3_art;

static const o3_as pl_as = { o3_ax_anims, O3_AX_ANIM_IDLE, O3_AX_ANIM_WALK,
                             O3_AX_ANIM_ATTACK1, O3_AX_ANIM_JUMP,
                             O3_AX_ANIM_PAIN2, O3_AX_ANIM_FALL2,
                             O3_AX_ANIM_RISE, O3_AX_ANIM_DEATH };
static const o3_as en_as = { o3_long_anims, O3_LONG_ANIM_IDLE, O3_LONG_ANIM_WALK,
                             O3_LONG_ANIM_ATTACK1, 0xFFu,
                             O3_LONG_ANIM_PAIN2, O3_LONG_ANIM_FALL2,
                             O3_LONG_ANIM_RISE, O3_LONG_ANIM_DEATH };
static const o3_art pl_art = { o3_ax_poses, o3_ax_blocks, O3_AX_SLOT_A };
static const o3_art en_art = { o3_long_poses, o3_long_blocks, O3_LONG_SLOT_A };

typedef struct {
    const o3_as *as;
    const o3_art *art;
    unsigned int x;               /* mundo; x 1:1 com o fonte */
    unsigned char z;              /* profundidade (banda de piso) */
    unsigned char alt;            /* altitude (px, 0 = no chao) */
    unsigned char facing;
    unsigned char hp;
    unsigned char state;          /* O3_S_* */
    unsigned char anim;           /* id no conjunto do ator */
    unsigned char frame;          /* indice no anim */
    unsigned char timer;          /* frames restantes do quadro (255 = seguro) */
    unsigned char hitstop;        /* frames de congelamento */
    unsigned char guard;          /* frames sem tomar hit (13 apos ser atingido) */
    unsigned char hit_used;       /* 1 hit por ativacao de ataque */
    unsigned char dead;           /* hp chegou a 0 (queda fatal) */
    unsigned char arc;            /* O3_ARC_* (0 = nenhum) */
    unsigned char arc_t;          /* indice na tabela do arco */
    int xacc, zacc;               /* acumuladores Q8.8 de movimento */
    /* stream de poses (D8) */
    unsigned char disp;           /* slot exibido (0=A, 1=B) */
    unsigned char disp_pose;      /* pose no slot exibido (0xFF = vazio) */
    unsigned char up_pose;        /* pose em upload (0xFF = nenhum) */
    unsigned char up_slot;        /* slot destino do upload */
    unsigned char up_want;        /* 1 = upload da pose desejada; 0 = pre-carga */
    unsigned char up_done;        /* chunk final ja copiado; CPU finaliza */
    unsigned char slot_pose[2];   /* conteudo de cada slot (0xFF = vazio) */
    unsigned int up_off;          /* bytes ja copiados do bloco */
} o3_actor;

static o3_actor pl;
static o3_actor e;
static unsigned char e_think;
static unsigned int cam;           /* quantizada em 8 px (cam & ~7) */
static unsigned char written_col;  /* ultima coluna de mundo escrita na PNT */
/* Coluna de BG fatiada (M6): cursor persiste entre quadros. Escrita inteira
 * custa ~44 linhas (22 linhas de PNT); com SAT (~14) nao cabe num VBlank.
 * 11 linhas/quadro => coluna completa em 2 quadros; a camera a pe pede uma
 * coluna a cada ~4,8 quadros (1,67 px/f em passos de 8), entao sobram ~2,8
 * quadros livres por periodo para os chunks de upload dos atores. */
static unsigned char col_pend_w;   /* coluna de mundo em escrita */
static unsigned char col_pend_r;   /* proxima linha [0..O2_STAGE_ROWS] = livre */
static unsigned char hp_drawn, hp_drawn_e;
/* Redesenho parcial da barra do HUD (M5): faixa pendente [lo,hi) em colunas
 * de tela + fill usado. O gate por tile no VBlank adia o resto para os
 * proximos quadros (medido: 1 tile ~1,6 linha de VBlank). */
static unsigned char hud_pl_lo, hud_pl_hi, hud_pl_fill;
static unsigned char hud_e_lo, hud_e_hi, hud_e_fill;
static volatile unsigned char __at(0xC7A0) ec[O3_ROWS]; /* zeros por linha (asm) */

/* Interface fixa C <-> nucleo asm do draw (M5). Enderecos absolutos para o
 * add a,#<sym nao paginar: lo(sym)+indice <= 0xFF (ec: 0xA0+5, mtab: 0xC0+11). */
volatile unsigned char __at(0xC7A6) o3_np;      /* celulas do jogador */
volatile unsigned char __at(0xC7A7) o3_ne;      /* celulas do inimigo */
volatile unsigned char __at(0xC7A8) o3_slot_p;  /* tile base do slot exibido */
volatile unsigned char __at(0xC7A9) o3_slot_e;
volatile unsigned char __at(0xC7AA) o3_ptop8m1; /* (u8)(ptop - 1) */
volatile unsigned char __at(0xC7AB) o3_pb1;     /* pb ? pb-1 : 0 */
volatile unsigned char __at(0xC7AC) o3_rpv0b;   /* rpv0 + 16 */
volatile unsigned char __at(0xC7AD) o3_rpv1b;   /* rpv1 + 16 */
volatile unsigned char __at(0xC7AE) o3_bm1_p;   /* (u8)(base_p - 1) */
volatile unsigned char __at(0xC7AF) o3_bm1_e;
volatile unsigned int  __at(0xC7B0) o3_cells_p; /* &poses[..].cells */
volatile unsigned int  __at(0xC7B2) o3_cells_e;
volatile unsigned int  __at(0xC7B4) o3_xh_p;    /* pl.x - cam / e.x - cam */
volatile unsigned int  __at(0xC7B6) o3_xh_e;
volatile unsigned int  __at(0xC7B8) o3_xnd;     /* XNbase - 2*Ybase (SAT) */
/* mtab[0..5] = pcv (linha so), mtab[6..11] = pmax (par adjacente) de
 * o3_ax_rows[pl.disp_pose] — espelha pcv/pmax do loop C do inimigo. */
volatile unsigned char __at(0xC7C0) o3_mtab[12];

/* Simbolos do modulo SMSlib_sprite (globais do .lib, sem declaracao no
 * header): a SAT e o contador vem do LINKER — nunca fixar endereco aqui.
 * O layout ja mudou uma vez (Y 0xC05C -> 0xC056) e um asm com base fixa
 * desenhou fora da tabela sem o build denunciar; referencia por simbolo
 * torna o nucleo imune a relayout. */
extern unsigned char SpriteTableY[];
extern unsigned char SpriteTableXN[];
extern unsigned char SpriteNextFree;

#if O3_SPILL_TRACE
/* Diag M5 (inativo com O3_SPILL_TRACE 0; bancada so para diagnostico):
 * perfil de custo de 5 chunks de 64 B no topo
 * do VBlank (quadro 100) + serie de leituras do gate no ultimo quadro, em bytes
 * livres do corredor (C7CC..C7DF; C7D2 = vline_min e C7E0+ = header/diag/frame).
 * NAO usar 0xC400: C45C e variavel viva do programa (medido por varredura de
 * operandos absolutos na ROM — o map nao lista as estaticas do main).
 * pr0..pr5 = VCounter antes/depois de cada um dos 5 chunks (320 B);
 * rd0..rd5 + rd_n = as 6 primeiras leituras do gate (e quantas houve) no
 * ultimo quadro; t_pl/t_e = VCounter apos stream_commit(pl)/(e). */
volatile unsigned char __at(0xC7CC) diag_pr0;
volatile unsigned char __at(0xC7CD) diag_pr1;
volatile unsigned char __at(0xC7CE) diag_pr2;
volatile unsigned char __at(0xC7CF) diag_pr3;
volatile unsigned char __at(0xC7D0) diag_pr4;
volatile unsigned char __at(0xC7D1) diag_pr5;
volatile unsigned char __at(0xC7D3) diag_rd0;
volatile unsigned char __at(0xC7D4) diag_rd1;
volatile unsigned char __at(0xC7D5) diag_commit_chunks;    /* live: chunks do quadro */
volatile unsigned char __at(0xC7D6) diag_commit_bytes_lo;  /* live: bytes do quadro */
volatile unsigned char __at(0xC7D7) diag_commit_bytes_hi;
volatile unsigned char __at(0xC7D8) diag_vc_last;          /* live: ultima leitura */
volatile unsigned char __at(0xC7D9) diag_rd2;
volatile unsigned char __at(0xC7DA) diag_rd3;
volatile unsigned char __at(0xC7DB) diag_rd4;
volatile unsigned char __at(0xC7DC) diag_rd5;
volatile unsigned char __at(0xC7DD) diag_rd_n;             /* leituras no quadro */
volatile unsigned char __at(0xC7DE) diag_t_e;              /* pos stream_commit(e) */
volatile unsigned char __at(0xC7DF) diag_t_pl;             /* pos stream_commit(pl) */
static unsigned char spill_v1, spill_v2, spill_v3;
#endif

static int iabs(int v)
{
    return v < 0 ? -v : v;
}

static unsigned char pose_of(const o3_anim *an, unsigned char idx,
                             unsigned char facing)
{
    return (unsigned char)((an->frames[idx].frame << 1) + facing);
}

static unsigned char pose_now(const o3_actor *a)
{
    return pose_of(&a->as->tbl[a->anim], a->frame, a->facing);
}

static void start_anim(o3_actor *a, unsigned char id)
{
    a->anim = id;
    a->frame = 0;
    a->timer = a->as->tbl[id].frames[0].delay;
}

/* ------------------------------------------------------------------ *
 * Escrita de BG (molde O2: anel mod-32 alinhado ao wrap de 256 px).
 * A coluna inteira (22 linhas) custa ~44 linhas de VBlank; o stream a
 * fatia em quadros com guarda por linha (M6, ver col_pend_*).
 * ------------------------------------------------------------------ */
static void write_bg_row(unsigned char world_col, unsigned char row)
{
    SMS_setNextTileatXY((unsigned char)(world_col & 31u),
                        (unsigned char)(row + 2u));
    SMS_setTile((unsigned int)(O3_TILE_BG_BASE
                + o2_bg_cols[(unsigned int)world_col * O2_STAGE_ROWS + row]));
}

static void write_bg_col(unsigned char world_col)   /* boot: display desligado */
{
    unsigned char i;
    for (i = 0; i < O2_STAGE_ROWS; i++)
        write_bg_row(world_col, i);
}

static void stream_columns(void)
{
    int right = (int)(cam >> 3) + 31;
    unsigned char vc;

    if (col_pend_r >= O2_STAGE_ROWS) {          /* sem coluna em curso */
        if ((int)written_col == right)
            return;
        if ((int)written_col < right) {
            col_pend_w = (unsigned char)(written_col + 1u);
            written_col++;
        } else {
            col_pend_w = (unsigned char)(written_col - 32u);
            written_col--;
        }
        col_pend_r = 0u;
    }
    while (col_pend_r < O2_STAGE_ROWS) {
        /* Guarda por linha: deixa a margem do rabo fixo dos commits
         * (2 prologos 14,6 + 2 saidas ~4 + probe ~2) com folga de jitter
         * (~5 linhas) -- mesmo criterio do gate de commit
         * (O3_COMMIT_MARGIN = 22 para chunks; O3_COMMIT_PROLOG = 30). */
        vc = SMS_VCounterPort;
        if ((unsigned char)(0xFFu - vc) < 26u)
            return;                             /* conclui no proximo quadro */
        write_bg_row(col_pend_w, col_pend_r);
        col_pend_r++;
    }
}

/* HUD: linha 0 = barra do jogador (verde), linha 1 = inimigo (vermelha).
 * Medicao (quadro 411, diag10): o redesenho da LINHA INTEIRA (32 tiles em
 * SMS_setTile) custou 52 linhas de VBlank — com o bloco valendo ~70 linhas,
 * um quadro de dano derramava (~+22). Agora so a FAIXA cuja cor muda e
 * redesenhada (hit tipico de 5 hp = 1 tile) e um gate por tile para antes
 * do rabo fixo dos commits (2 prologos ~14,6 + saida ~2 + folga), deixando
 * o resto para os quadros seguintes (faixa pendente persistente). */
static void draw_hud_boot(void)          /* display desligado: linhas inteiras */
{
    unsigned char i;
    unsigned char fill_p = (unsigned char)((unsigned int)pl.hp
                                           * O2_HUD_PLAYER_COLS / O3_HP_PLAYER);
    unsigned char fill_e = (unsigned char)((unsigned int)e.hp
                                           * O2_HUD_ENEMY_COLS / O3_HP_ENEMY);
    for (i = 0; i < 32u; i++) {
        unsigned int tp = O3_TILE_HUD_BLACK;
        if (i >= O2_HUD_COL0
            && i < (unsigned char)(O2_HUD_COL0 + O2_HUD_PLAYER_COLS)
            && (unsigned char)(i - O2_HUD_COL0) < fill_p)
            tp = O3_TILE_HUD_GREEN;
        SMS_setNextTileatXY(i, O2_HUD_PLAYER_ROW);
        SMS_setTile(tp);
    }
    for (i = 0; i < 32u; i++) {
        unsigned int tp = O3_TILE_HUD_BLACK;
        if (i >= O2_HUD_COL0
            && i < (unsigned char)(O2_HUD_COL0 + O2_HUD_ENEMY_COLS)
            && (unsigned char)(i - O2_HUD_COL0) < fill_e)
            tp = O3_TILE_HUD_RED;
        SMS_setNextTileatXY(i, O2_HUD_ENEMY_ROW);
        SMS_setTile(tp);
    }
}

static void draw_hud(void)
{
    if (pl.hp != hp_drawn) {
        unsigned char nf = (unsigned char)((unsigned int)pl.hp
                                           * O2_HUD_PLAYER_COLS / O3_HP_PLAYER);
        unsigned char of = (unsigned char)((unsigned int)hp_drawn
                                           * O2_HUD_PLAYER_COLS / O3_HP_PLAYER);
        unsigned char l = (unsigned char)(O2_HUD_COL0 + (of < nf ? of : nf));
        unsigned char h = (unsigned char)(O2_HUD_COL0 + (of < nf ? nf : of));
        if (hud_pl_lo >= hud_pl_hi) {
            hud_pl_lo = l;
            hud_pl_hi = h;
        } else {
            if (l < hud_pl_lo)
                hud_pl_lo = l;
            if (h > hud_pl_hi)
                hud_pl_hi = h;
        }
        hud_pl_fill = nf;
        hp_drawn = pl.hp;
    }
    if (hud_pl_lo < hud_pl_hi) {
        unsigned char c;
        for (c = hud_pl_lo; c < hud_pl_hi; c++) {
            unsigned int tp = O3_TILE_HUD_BLACK;
            if ((unsigned char)(0xFFu - SMS_VCounterPort) < 26u)
                break;                      /* nao cabe com margem */
            if ((unsigned char)(c - O2_HUD_COL0) < hud_pl_fill)
                tp = O3_TILE_HUD_GREEN;
            SMS_setNextTileatXY(c, O2_HUD_PLAYER_ROW);
            SMS_setTile(tp);
        }
        hud_pl_lo = c;
    }
    if (e.hp != hp_drawn_e) {
        unsigned char nf = (unsigned char)((unsigned int)e.hp
                                           * O2_HUD_ENEMY_COLS / O3_HP_ENEMY);
        unsigned char of = (unsigned char)((unsigned int)hp_drawn_e
                                           * O2_HUD_ENEMY_COLS / O3_HP_ENEMY);
        unsigned char l = (unsigned char)(O2_HUD_COL0 + (of < nf ? of : nf));
        unsigned char h = (unsigned char)(O2_HUD_COL0 + (of < nf ? nf : of));
        if (hud_e_lo >= hud_e_hi) {
            hud_e_lo = l;
            hud_e_hi = h;
        } else {
            if (l < hud_e_lo)
                hud_e_lo = l;
            if (h > hud_e_hi)
                hud_e_hi = h;
        }
        hud_e_fill = nf;
        hp_drawn_e = e.hp;
    }
    if (hud_e_lo < hud_e_hi) {
        unsigned char c;
        for (c = hud_e_lo; c < hud_e_hi; c++) {
            unsigned int tp = O3_TILE_HUD_BLACK;
            if ((unsigned char)(0xFFu - SMS_VCounterPort) < 26u)
                break;                      /* nao cabe com margem */
            if ((unsigned char)(c - O2_HUD_COL0) < hud_e_fill)
                tp = O3_TILE_HUD_RED;
            SMS_setNextTileatXY(c, O2_HUD_ENEMY_ROW);
            SMS_setTile(tp);
        }
        hud_e_lo = c;
    }
}

/* ------------------------------------------------------------------ *
 * Stream de poses (D8): copia fatiada banco->VRAM + troca de slot.
 * ------------------------------------------------------------------ */
static unsigned char new_next_pose(const o3_actor *a)
{
    const o3_anim *an = &a->as->tbl[a->anim];
    unsigned char d = (unsigned char)(a->frame + 1u);
    if (d < an->count)
        return pose_of(an, d, a->facing);
    if (an->loop)
        return pose_of(an, 0, a->facing);
    return 0xFFu;   /* fim de animacao sem loop: nada a pre-carregar */
}

static void preload_boot(o3_actor *a)
{
    unsigned char pose = pose_now(a);
    SMS_mapROMBank(a->art->blocks[pose].bank);
    SMS_VRAMmemcpy((unsigned int)(a->art->slot_a << 5),
                   (const void *)(0x8000u + a->art->blocks[pose].addr),
                   (unsigned int)(a->art->poses[pose].count) << 6);
    a->disp = 0;
    a->disp_pose = pose;
    a->slot_pose[0] = pose;
    a->slot_pose[1] = 0xFFu;
    a->up_pose = 0xFFu;
    a->up_slot = 1;
    a->up_want = 0;
    a->up_off = 0;
    a->up_done = 0;
}

static void stream_update(o3_actor *a)
{
    unsigned char want = pose_now(a);
    unsigned char tgt = (unsigned char)(1u - a->disp);

    if (a->up_done) {                       /* copia terminou no VBlank */
        a->slot_pose[a->up_slot] = a->up_pose;
        if (a->up_want || a->up_pose == want) {
            a->disp = a->up_slot;           /* troca so com a copia pronta */
            a->disp_pose = a->up_pose;
        }
        a->up_pose = 0xFFu;
        a->up_done = 0;
    }

    if (a->up_pose == 0xFFu) {
        if (want != a->disp_pose) {
            if (a->slot_pose[tgt] == want) {
                a->disp = tgt;                  /* ja esta no outro slot */
                a->disp_pose = want;
            } else {
                a->up_pose = want;
                a->up_slot = tgt;
                a->up_off = 0;
                a->up_want = 1;
            }
        } else {
            unsigned char nxt = new_next_pose(a);
            if (nxt != 0xFFu && nxt != want && a->slot_pose[tgt] != nxt) {
                a->up_pose = nxt;               /* pre-carga da pose seguinte */
                a->up_slot = tgt;
                a->up_off = 0;
                a->up_want = 0;
            }
        }
    } else if (a->up_want) {
        /* Copia desejada em andamento: deixa COMPLETAR (M5). A banda da
         * janela de VBlank e menor que a taxa de ticks do ataque (3 ticks
         * contra ~5 quadros de copia da maior pose); reiniciar a cada
         * mudanca de want congelava a pose exibida para sempre. Ao
         * terminar, o topo deste bloco inicia a want mais recente. */
    } else if (want != a->disp_pose && a->up_pose != want) {
        if (a->slot_pose[a->up_slot] == want) {
            a->up_pose = 0xFFu;                 /* pre-carga ja servia o alvo */
            a->disp = a->up_slot;
            a->disp_pose = want;
        } else {
            a->up_pose = want;                  /* interrompe a pre-carga */
            a->up_want = 1;
            a->up_off = 0;
        }
    }
}

/* Bloco de VBlank: um chunk do upload pendente, dentro da janela (D8).
 * O chunk NAO roda na fase de CPU: escrita em display ativo custa ~1-2
 * linhas de varredura por byte no Emulicious (medido 2026-10-17: o lab M1
 * a 1856 B/loop roda 5,1 frames VDP/loop aqui contra 1:1 no BlastEm) e
 * sustentava 13 fps em vez de 60. O jogador tem prioridade; o inimigo usa
 * o que sobra do orcamento de O3_UPLOAD_CHUNK por frame.
 *
 * M5: copia ADAPTATIVA — em sub-chunks de O3_COMMIT_SUB bytes, relendo o
 * VCounter antes de cada um e parando quando o resto da janela util
 * (VCounter 0xC0..0xFF) nao cobre custo + margem. O teto por ator segue
 * O3_UPLOAD_CHUNK, mas quem manda e a janela medida: o bloco nunca derrama
 * (contrato worst-frame, L061) e todo byte que cabe no quadro e usado. */
static unsigned int stream_commit(o3_actor *a, unsigned int budget)
{
    unsigned int total, off, done = 0u, n;
    unsigned int vaddr, saddr;
    unsigned char vc;

    if (a->up_pose == 0xFFu || a->up_done || budget == 0u)
        return 0u;
    /* M6: gate ANTES do prologo. Sem isto o 2o ator pagava banco + enderecos
     * (~7,3 linhas) em todo quadro em que seu chunk ja nao cabia — trabalho
     * jogado fora que encurtava a janela do 1o. */
    vc = SMS_VCounterPort;
    if (vc < 0xC0u || (unsigned char)(0xFFu - vc) < O3_COMMIT_PROLOG)
        return 0u;
    total = (unsigned int)a->art->poses[a->up_pose].count << 6;
    off = a->up_off;
    vaddr = (unsigned int)(O3_SLOT_TILE(a->art->slot_a, a->up_slot) << 5) + off;
    saddr = 0x8000u + (unsigned int)a->art->blocks[a->up_pose].addr + off;
    SMS_mapROMBank(a->art->blocks[a->up_pose].bank);
    /* M6: estado do lote em LOCAIS. O loop nao toca o ator ate o fim; SDCC
     * deixa de recarregar a->up_off/total/budget da pilha a cada iteracao
     * (era o grosso das ~4,6 linhas de overhead C por chunk no M5). */
    while (off < total && done < budget) {
        vc = SMS_VCounterPort;
#if O3_SPILL_TRACE
        switch (diag_rd_n) {
        case 0u: diag_rd0 = vc; break;
        case 1u: diag_rd1 = vc; break;
        case 2u: diag_rd2 = vc; break;
        case 3u: diag_rd3 = vc; break;
        case 4u: diag_rd4 = vc; break;
        case 5u: diag_rd5 = vc; break;
        default: break;
        }
        diag_rd_n++;
        diag_vc_last = vc;
#endif
        if (vc < 0xC0u)
            break;                              /* ja fora da janela */
        /* M6 (re-medido): 1 chunk de 64 B custa ~10 linhas depois do hoist
         * de locais (antes ~16). O rabo fixo virou ~2,5: gate antes do
         * prologo impede o 2o ator de pagar banco/enderecos quando seu chunk
         * nao cabe, entao o que resta e so a saida + o marco do probe. */
        if ((unsigned char)(0xFFu - vc) < O3_COMMIT_MARGIN)
            break;                              /* nao cabe com margem */
        n = total - off;
        if (n > O3_COMMIT_SUB)
            n = O3_COMMIT_SUB;
        if (n > budget - done)
            n = budget - done;
        SMS_VRAMmemcpy(vaddr, (const void *)saddr, n);
#if O3_SPILL_TRACE
        diag_commit_chunks++;
        {
            unsigned int b = (unsigned int)diag_commit_bytes_lo
                             | ((unsigned int)diag_commit_bytes_hi << 8);
            b += n;
            diag_commit_bytes_lo = (unsigned char)b;
            diag_commit_bytes_hi = (unsigned char)(b >> 8);
        }
#endif
        off += n;
        vaddr += n;
        saddr += n;
        done += n;
    }
    a->up_off = off;
    if (off >= total)
        a->up_done = 1u;                    /* CPU finaliza (slot/troca) */
    return done;
}

/* ------------------------------------------------------------------ *
 * FSM e arcos.
 * ------------------------------------------------------------------ */
static void start_attack(o3_actor *a)
{
    a->state = O3_S_ATTACK;
    a->hit_used = 0;
    start_anim(a, a->as->attack);
}

static void start_jump(o3_actor *a)   /* so o jogador (long nao tem pulo) */
{
    a->state = O3_S_FALL;
    a->arc = O3_ARC_JUMP;
    a->arc_t = 0;
    a->alt = o3_jump_y[0];
    start_anim(a, a->as->jump);
}

static void fsm_end(o3_actor *a)
{
    const o3_as *as = a->as;
    if (a->state == O3_S_ATTACK || a->state == O3_S_PAIN
        || a->state == O3_S_RISE) {
        a->state = O3_S_IDLE;
        start_anim(a, as->idle);
    } else if (a->state == O3_S_FALL) {      /* fim da sequencia de land */
        if (a->dead) {
            a->state = O3_S_DEAD;
            start_anim(a, as->death);
        } else {
            a->state = O3_S_RISE;
            start_anim(a, as->rise);
        }
    }
    /* DEAD: congela no ultimo quadro (guardado no fsm_tick) */
}

static void fsm_tick(o3_actor *a)
{
    const o3_anim *an = &a->as->tbl[a->anim];
    unsigned char d;

    if (a->state == O3_S_DEAD && a->timer == 0u)
        return;                              /* morte: ultimo quadro fica */
    if (pose_now(a) != a->disp_pose)
        return;                              /* D8: pose ready */
    if (a->timer) {
        a->timer--;
        return;
    }
    d = (unsigned char)(a->frame + 1u);
    if (d < an->count) {
        a->frame = d;
        a->timer = an->frames[d].delay;
    } else if (an->loop) {
        a->frame = 0;
        a->timer = an->frames[0].delay;
    } else {
        fsm_end(a);
    }
}

static void arc_advance(o3_actor *a)
{
    unsigned char t = (unsigned char)(a->arc_t + 1u);
    unsigned char right;
    int d = 0;

    /* Pouso checado ANTES da leitura da tabela: o inicio do arco pode estar
     * no fim (juggle entra na altura atual) e t passaria do ultimo indice. */
    if ((a->arc == O3_ARC_JUMP && t >= O3_JUMP_FRAMES)
        || (a->arc == O3_ARC_TOSS && t >= O3_TOSS_FRAMES)
        || (a->arc == O3_ARC_ENTRY && t >= O3_ENTRY_FRAMES)) {
        unsigned char was_toss = (unsigned char)(a->arc == O3_ARC_TOSS);
        a->alt = 0;
        a->arc = O3_ARC_NONE;
        if (was_toss) {
            a->frame = a->as->tbl[a->as->fall].land;   /* sequencia de land */
            a->timer = a->as->tbl[a->as->fall].frames[a->frame].delay;
        } else {
            a->state = O3_S_IDLE;            /* pouso do pulo/entrada */
            start_anim(a, a->as->idle);
        }
        return;
    }
    a->arc_t = t;
    if (a->arc == O3_ARC_JUMP) {
        a->alt = o3_jump_y[t];
        d = (int)o3_jump_x[t] - (int)o3_jump_x[t - 1u];
        right = a->facing;
    } else if (a->arc == O3_ARC_TOSS) {
        a->alt = o3_toss_y[t];
        d = (int)o3_toss_x[t] - (int)o3_toss_x[t - 1u];
        right = (unsigned char)!a->facing;   /* derruba para tras do facing */
    } else {
        a->alt = o3_entry_y[t];
        right = a->facing;                   /* entrada cai na vertical (d = 0) */
    }
    if (d) {
        if (right) {
            if ((int)a->x + d <= (int)O3_PLAYER_MAX_X)
                a->x = (unsigned int)((int)a->x + d);
        } else {
            if ((int)a->x - d >= (int)O3_PLAYER_MIN_X)
                a->x = (unsigned int)((int)a->x - d);
        }
    }
}

/* ------------------------------------------------------------------ *
 * Controle: jogador (input) e inimigo (IA), antes do advance.
 * ------------------------------------------------------------------ */
static void player_control(unsigned int keys)
{
    unsigned char dirx = 0;
    unsigned char moving = 0;

    if (pl.state != O3_S_IDLE && pl.state != O3_S_WALK)
        return;
    if (keys & PORT_A_KEY_LEFT)
        dirx = 2u;
    if (keys & PORT_A_KEY_RIGHT)
        dirx = 1u;                  /* direita vence quando ambos */
    if (dirx) {
        moving = 1;
        pl.facing = (unsigned char)(dirx == 1u);
        if (dirx == 1u)
            pl.xacc += (int)O3_WALK_Q8;
        else
            pl.xacc -= (int)O3_WALK_Q8;
        while (pl.xacc >= 256) {
            pl.xacc -= 256;
            if (pl.x < O3_PLAYER_MAX_X)
                pl.x++;
        }
        while (pl.xacc <= -256) {
            pl.xacc += 256;
            if (pl.x > O3_PLAYER_MIN_X)
                pl.x--;
        }
    }
    if (keys & PORT_A_KEY_UP) {
        moving = 1;
        pl.zacc -= (int)O3_WALK_Q8;
        while (pl.zacc <= -256) {
            pl.zacc += 256;
            if (pl.z > O3_Z_MIN)
                pl.z--;
        }
    }
    if (keys & PORT_A_KEY_DOWN) {
        moving = 1;
        pl.zacc += (int)O3_WALK_Q8;
        while (pl.zacc >= 256) {
            pl.zacc -= 256;
            if (pl.z < O3_Z_MAX)
                pl.z++;
        }
    }
    if (keys & PORT_A_KEY_1) {
        start_attack(&pl);          /* A = ataque (mapa comum OpenBOR) */
        return;
    }
    if (keys & PORT_A_KEY_2) {
        start_jump(&pl);            /* B = pulo */
        return;
    }
    if (moving) {
        pl.state = O3_S_WALK;
        if (pl.anim != pl.as->walk)
            start_anim(&pl, pl.as->walk);
    } else {
        pl.state = O3_S_IDLE;
        if (pl.anim != pl.as->idle)
            start_anim(&pl, pl.as->idle);
    }
}

static void move_toward(o3_actor *a, int dx, int dz)
{
    int adx = iabs(dx);
    int adz = iabs(dz);
    unsigned int s = (unsigned int)(adx + adz);
    unsigned int vx, vz;

    if (s == 0u)
        return;
    /* vx = piso(320*adx/s). Como |dz| <= 72 (z em [160,232]), 320*adz cabe
     * em 16 bits e piso(320*adx/s) = 320 - teto(320*adz/s); teto(a/s) =
     * (a + s - 1)/s. */
    vx = (unsigned int)O3_CHASE_Q8
         - (unsigned int)((((unsigned int)adz << 8)
                           + ((unsigned int)adz << 6)
                           + s - 1u) / s);
    vz = (unsigned int)O3_CHASE_Q8 - vx;
    if (dx > 0) {
        a->xacc += (int)vx;
        while (a->xacc >= 256) {
            a->xacc -= 256;
            if (a->x < O3_PLAYER_MAX_X)
                a->x++;
        }
    } else if (dx < 0) {
        a->xacc -= (int)vx;
        while (a->xacc <= -256) {
            a->xacc += 256;
            if (a->x > O3_PLAYER_MIN_X)
                a->x--;
        }
    }
    if (dz > 0) {
        a->zacc += (int)vz;
        while (a->zacc >= 256) {
            a->zacc -= 256;
            if (a->z < O3_Z_MAX)
                a->z++;
        }
    } else if (dz < 0) {
        a->zacc -= (int)vz;
        while (a->zacc <= -256) {
            a->zacc += 256;
            if (a->z > O3_Z_MIN)
                a->z--;
        }
    }
}

static void enemy_control(void)
{
    int dx, dz;

    if (e.state != O3_S_IDLE && e.state != O3_S_WALK)
        return;
    dx = (int)pl.x - (int)e.x;
    dz = (int)pl.z - (int)e.z;
    e.facing = (unsigned char)(dx >= 0);   /* arrow_move: facing todo frame */
    if (e_think) {
        e_think--;
    } else {
        e_think = O3_AI_THINK;
        if (!pl.dead && iabs(dx) <= O3_ATTACK_RANGE_X
            && iabs(dz) <= O3_ATTACK_RANGE_Z) {
            start_attack(&e);              /* facing ja aponta ao jogador */
            return;
        }
    }
    if (iabs(dx) > O3_ATTACK_RANGE_X || iabs(dz) > O3_ATTACK_RANGE_Z) {
        move_toward(&e, dx, dz);
        e.state = O3_S_WALK;
        if (e.anim != e.as->walk)
            start_anim(&e, e.as->walk);
    } else {
        e.state = O3_S_IDLE;
        if (e.anim != e.as->idle)
            start_anim(&e, e.as->idle);
    }
}

/* Avanco do ator: hitstop congela; pose pronta (D8) libera FSM e arcos. */
static void actor_advance(o3_actor *a)
{
    /* M6 (medido 2026-10-17): a guarda de 13 quadros era ARMADA no hit e nunca
     * desarmada — o primeiro acerto deixava a vitima imune para sempre e a
     * morte do inimigo era impossivel. Conta em tempo real, antes do hitstop e
     * do gate de pose: o D8 segura a FSM enquanto a pose nao chega, e uma
     * guarda presa ao gate ficaria congelada justamente sob starvation. */
    if (a->guard)
        a->guard--;
    if (a->hitstop) {
        a->hitstop--;
        return;
    }
    if (pose_now(a) != a->disp_pose)
        return;                            /* D8: pose ready (segura o FSM) */
    if (a->state == O3_S_FALL && a->arc)
        arc_advance(a);
    fsm_tick(a);
}

/* ------------------------------------------------------------------ *
 * Hit (D4): AABB x/profundidade/altitude, 1 hit por ativacao, guarda 13.
 * ------------------------------------------------------------------ */
static unsigned char hit_test(const o3_actor *a, const o3_actor *v,
                              const o3_attack *at)
{
    int ax0, ax1, vx0, vx1, at_top, at_bot, vt_top, vt_bot;

    if (v->guard || v->hp == 0u)
        return 0;
    if (iabs((int)a->z - (int)v->z) > (int)at->depth)
        return 0;
    if (a->facing) {
        ax0 = (int)a->x;
        ax1 = (int)a->x + (int)at->w;
    } else {
        ax0 = (int)a->x - (int)at->w;
        ax1 = (int)a->x;
    }
    vx0 = (int)v->x - O3_BBOX_HALF_W;
    vx1 = (int)v->x + O3_BBOX_HALF_W;
    if (ax0 > vx1 || ax1 < vx0)
        return 0;
    at_top = (int)a->alt + (int)at->y;
    at_bot = at_top + (int)at->h;
    vt_top = (int)v->alt - O3_BBOX_UP;
    vt_bot = (int)v->alt + O3_BBOX_DOWN;
    if (at_top > vt_bot || at_bot < vt_top)
        return 0;
    return 1;
}

static void apply_hit(o3_actor *a, o3_actor *v, const o3_attack *at,
                      unsigned char hitstop)
{
    a->hit_used = 1;
    a->hitstop = hitstop;
    v->hitstop = hitstop;                  /* hitpause tambem na vitima */
    v->guard = O3_NEXT_HIT_FRAMES;
    if (v->hp > at->dmg)
        v->hp = (unsigned char)(v->hp - at->dmg);
    else
        v->hp = 0;
    if (v->hp == 0u)
        v->dead = 1;
    if (v->state == O3_S_FALL && v->arc == O3_ARC_TOSS)
        return;                            /* re-hit na queda: so hp/guarda */
    if (v->alt > 0u || v->dead) {
        unsigned char t = 0;
        v->state = O3_S_FALL;
        start_anim(v, v->as->fall);
        v->arc = O3_ARC_TOSS;
        while (t < O3_TOSS_FRAMES && o3_toss_y[t] < v->alt)
            t++;                           /* juggle: entra na altitude atual */
        v->arc_t = t;
        v->alt = o3_toss_y[t];
    } else {
        v->state = O3_S_PAIN;
        start_anim(v, v->as->pain);
    }
}

static void resolve_hits(void)
{
    if (pl.state == O3_S_ATTACK && !pl.hit_used
        && pl.frame >= o3_ax_attack.first && pl.frame <= o3_ax_attack.last) {
        if (hit_test(&pl, &e, &o3_ax_attack))
            apply_hit(&pl, &e, &o3_ax_attack, O3_HITSTOP_AX);
    }
    if (e.state == O3_S_ATTACK && !e.hit_used
        && e.frame >= o3_long_attack.first && e.frame <= o3_long_attack.last) {
        if (hit_test(&e, &pl, &o3_long_attack))
            apply_hit(&e, &pl, &o3_long_attack, O3_HITSTOP_LONG);
    }
}

/* ------------------------------------------------------------------ *
 * Tabela de sprites (CPU); o VBlank so copia a SAT pronta.
 * Politica D9-a2 espelhando o3_compose_sprites/o3_compose_rows:
 * - jogador inteiro (primeiro na SAT), celula com topo < 1 nao desenha;
 * - inimigo na ordem empacotada (dens desc/banda/coluna; a tabela emitida
 *   ja esta nessa ordem): topo < 1 nao desenha nem conta; topo >= 192 nao
 *   desenha (invisivel; mesmo em tela) e nao conta; orcamento
 *   ec[linha] + 1 + max(o3_ax_rows[pose do jogador][linhas sobrepostas]) > 8
 *   derruba; x fora de [0,255] nao desenha mas ja contou no orcamento.
 * M5 (medido 2026-10-17): varrer as 6 linhas por celula dominava o frame
 * (~3,5 frames; ~208k ciclos). As bandas tem passo 16 e os cortes 1/191
 * deixam no maximo 2 linhas sobrepostas por celula: rp em
 * [o>>4, (o+15)>>4] com o = y0 - ptop (equivalente). Forma final
 * (equivalente, aritmetica 8 bits): com 256 = 16*16, o modulo 256 e o
 * borrow b = (y0 < ptop) dao rl = (o8>>4) - 16b e rh = ((o8+15)>>4) - 16b;
 * enviesados +16 ficam em 0..31 (u8), e como [rl,rh] cobre no maximo 2
 * linhas, m sai de maximas adjacentes pre-calculadas (pcv/pmax).
 * ------------------------------------------------------------------ */
#if O3_DRAW_ASM
/* -------------------- M5: nucleo asm do draw (espelho exato) -------------
 * O loop C do inimigo (395 un medidas com chunk 0) nao fecha 60 fps; este
 * nucleo executa a MESMA politica do emissor (o3_compose_rows/o3_overlap):
 *   y0 = base + dy; (u16)(y0-1) > 190 -> cai;
 *   linha r = (dy - O3_DY0E) >> 4; o8 = (u8)y0 - (u8)ptop;
 *   b = (u8)y0 < pb; bl8 = (o8>>4) + 16 - 16b; bh8 = bl8 + ((o8&15) != 0);
 *   clamps em rpv0b/rpv1b; m = mtab (pcv linha so / pmax par, linha bl8-16);
 *   (u8)(ec[r]+1+m) > 8 -> cai; senao ec[r]++ (a queda NAO desenha);
 *   sxv = xh + dx; (u16)sxv > 255 -> nao desenha (mas ja contou);
 *   SAT direto: Y[t] = y0-1; XN[2t] = (u8)sxv; XN[2t+1] = slot + 2*cell.
 * Invariantes (provas registradas no doc do lote/M5):
 *   - Teste y0 em 8 bits exato em todo estado alcancavel: z em [160,232]
 *     (O3_Z_MIN/MAX), alt <= 97 (o3_entry_y), dy >= -72 (poses do inimigo)
 *     => y0-1 em [-42,207] dentro de (-256,256); negativos viram [214,255]
 *     >= 191 e falham como devem; no caminho vivo y0-1 fica em [0,190].
 *   - b em 8 bits: com pb = 0 compara contra 0 e y0-1 >= 0 no caminho vivo.
 *   - XN[2t] = 2*(0xC05C+t) + 0x3FE4 (mod 65536), derivado do proprio IX;
 *     nenhum store indexado dependente de t (0x40(ix) nao valeria).
 *   - SpriteNextFree <= 29+28 = 57 < 64: nenhum check da lib dispara.
 *   - IX/IY preservados (contrato SDCC); A/BC/DE/HL livres.
 * A/B: O3_DRAW_ASM 0 compila o C-ref com o mesmo estado de entrada (setup
 * comum, interface o3_* escrita) para comparar SAT/ec byte a byte. */
void o3_draw_player(void) __naked
{
    __asm
	push	ix
	push	iy
	ld	a, (_SpriteNextFree)
	ld	l, a
	ld	h, #0x00
	ld	de, #_SpriteTableY
	add	hl, de
	push	hl
	pop	ix
	ld	a, (_o3_np)
	or	a, a
	jr	nz, o3p_go
	jp	o3p_end
o3p_go:
	ld	b, a
	ld	iy, (_o3_cells_p)
o3p_loop:
	ld	a, 0 (iy)
	ld	e, a
	add	a, a
	sbc	a, a
	ld	d, a
	ld	hl, (_o3_xh_p)
	add	hl, de
	ld	a, h
	or	a, a
	jp	nz, o3p_next
	ld	c, l
	ld	a, 1 (iy)
	ld	e, a
	ld	a, (_o3_bm1_p)
	add	a, e
	cp	a, #191
	jp	nc, o3p_next
	ld	0 (ix), a
	push	ix
	pop	hl
	add	hl, hl
	ld	de, (_o3_xnd)
	add	hl, de
	ld	(hl), c
	inc	hl
	ld	a, 2 (iy)
	add	a, a
	ld	d, a
	ld	a, (_o3_slot_p)
	add	a, d
	ld	(hl), a
	inc	ix
o3p_next:
	inc	iy
	inc	iy
	inc	iy
	dec	b
	jp	nz, o3p_loop
o3p_end:
	push	ix
	pop	hl
	ld	de, #_SpriteTableY
	or	a, a
	sbc	hl, de
	ld	a, l
	ld	(_SpriteNextFree), a
	pop	iy
	pop	ix
	ret
    __endasm;
}

void o3_draw_enemy(void) __naked
{
    __asm
	push	ix
	push	iy
	ld	a, (_SpriteNextFree)
	ld	l, a
	ld	h, #0x00
	ld	de, #_SpriteTableY
	add	hl, de
	push	hl
	pop	ix
	ld	a, (_o3_ne)
	or	a, a
	jr	nz, o3e_go
	jp	o3e_end
o3e_go:
	ld	b, a
	ld	iy, (_o3_cells_e)
o3e_loop:
	ld	a, 1 (iy)
	ld	e, a
	ld	a, (_o3_bm1_e)
	add	a, e
	cp	a, #191
	jp	nc, o3e_next
	ld	c, a
	ld	a, e
	add	a, #72
	rrca
	rrca
	rrca
	rrca
	and	a, #15
	ld	d, a
	ld	a, (_o3_ptop8m1)
	ld	h, a
	ld	a, c
	sub	a, h
	ld	e, a
	ld	a, (_o3_pb1)
	ld	h, a
	ld	a, c
	cp	a, h
	sbc	a, a
	and	a, #16
	ld	h, a
	ld	a, e
	rrca
	rrca
	rrca
	rrca
	and	a, #15
	add	a, #16
	sub	a, h
	ld	h, a
	ld	a, e
	and	a, #15
	sub	a, #1
	sbc	a, a
	inc	a
	add	a, h
	ld	e, a
	ld	a, (_o3_rpv0b)
	cp	a, h
	jr	c, o3e_blok
	ld	h, a
o3e_blok:
	ld	a, (_o3_rpv1b)
	cp	a, e
	jr	nc, o3e_bhok
	ld	e, a
o3e_bhok:
	ld	a, e
	cp	a, h
	jr	nz, o3e_mne
	ld	a, h
	sub	a, #16
	jp	o3e_mlook
o3e_mne:
	jr	nc, o3e_mpair
	xor	a, a
	ld	e, a
	jr	o3e_mbudget
o3e_mpair:
	ld	a, h
	sub	a, #16
	add	a, #6
o3e_mlook:
	ld	hl, #_o3_mtab
	add	a, l
	ld	l, a
	ld	a, (hl)
	ld	e, a
o3e_mbudget:
	ld	a, d
	add	a, #<(_ec)
	ld	l, a
	ld	h, #>(_ec)
	ld	a, (hl)
	inc	a
	add	a, e
	cp	a, #9
	jp	nc, o3e_next
	sub	a, e
	ld	(hl), a
	ld	a, 0 (iy)
	ld	e, a
	add	a, a
	sbc	a, a
	ld	d, a
	ld	hl, (_o3_xh_e)
	add	hl, de
	ld	a, h
	or	a, a
	jp	nz, o3e_next
	ld	0 (ix), c
	ld	c, l
	push	ix
	pop	hl
	add	hl, hl
	ld	de, (_o3_xnd)
	add	hl, de
	ld	(hl), c
	inc	hl
	ld	a, 2 (iy)
	add	a, a
	ld	d, a
	ld	a, (_o3_slot_e)
	add	a, d
	ld	(hl), a
	inc	ix
o3e_next:
	inc	iy
	inc	iy
	inc	iy
	dec	b
	jp	nz, o3e_loop
o3e_end:
	push	ix
	pop	hl
	ld	de, #_SpriteTableY
	or	a, a
	sbc	hl, de
	ld	a, l
	ld	(_SpriteNextFree), a
	pop	iy
	pop	ix
	ret
    __endasm;
}
#endif

static void draw_sprites(void)
{
    const o3_pose *pp;
    const unsigned char *axr;
    unsigned char row;
    unsigned char pb, ptop8, rpv0b, rpv1b;
    unsigned char slot_p, slot_e;
    int base_p, base_e, ptop, rpv0, rpv1, xh;

    if (pl.disp_pose == 0xFFu || e.disp_pose == 0xFFu)
        return;                            /* boot: nada em VRAM ainda */

    base_p = (int)pl.z - 32 - (int)pl.alt;
    xh = (int)pl.x - (int)cam;
    pp = &pl.art->poses[pl.disp_pose];
    slot_p = O3_SLOT_TILE(pl.art->slot_a, pl.disp);
    o3_cells_p = (unsigned int)(pp->cells);
    o3_np = pp->count;
    o3_bm1_p = (unsigned char)(base_p - 1);
    o3_xh_p = (unsigned int)xh;
    o3_slot_p = slot_p;
    /* Deslocamento da SAT XN derivado do proprio IX (Y+next): XN[2t] mora em
     * XNbase+2t; com IX = Ybase+t vale XN = 2*IX + (XNbase-2*Ybase). O
     * termo entre parenteses sai dos simbolos do linker, nunca de literal. */
    o3_xnd = (unsigned int)SpriteTableXN
             - ((unsigned int)SpriteTableY * 2u);
#if O3_DRAW_ASM
    o3_draw_player();
#else
    {
        const o3_cell *c, *cend;
        c = pp->cells;
        cend = c + pp->count;
        for (; c != cend; c++) {
            int sxv, syv;
            syv = base_p + c->dy;
            if ((unsigned int)(syv - 1) > 190u)
                continue;
            sxv = xh + c->dx;
            if ((unsigned int)sxv > 255u)
                continue;
            SMS_addSprite((unsigned char)sxv, (unsigned char)syv,
                          (unsigned char)(slot_p + (c->cell << 1)));
        }
    }
#endif

    base_e = (int)e.z - 32 - (int)e.alt;
    ptop = base_p + O3_DY0P;               /* p0 da linha 0 do jogador */
    ptop8 = (unsigned char)ptop;
    pb = (ptop > 0) ? ptop8 : 0u;          /* piso do borrow (y0 < ptop) */
    axr = o3_ax_rows[pl.disp_pose];
    for (row = 0; row < O3_ROWS - 1u; row++) {
        unsigned char nxt = axr[row + 1u];
        o3_mtab[row] = axr[row];
        o3_mtab[6u + row] = (nxt > axr[row]) ? nxt : axr[row];
    }
    o3_mtab[O3_ROWS - 1u] = axr[O3_ROWS - 1u];
    o3_mtab[6u + O3_ROWS - 1u] = axr[O3_ROWS - 1u];
    /* faixa de linhas do jogador visivel: p0 = ptop + 16*rp em [1,191] */
    rpv0 = ((1 - ptop) + 15) >> 4;
    if (rpv0 < 0)
        rpv0 = 0;
    rpv1 = (191 - ptop) >> 4;
    if (rpv1 > O3_ROWS - 1)
        rpv1 = O3_ROWS - 1;
    rpv0b = (unsigned char)(rpv0 + 16);
    rpv1b = (unsigned char)(rpv1 + 16);
    for (row = 0; row < O3_ROWS; row++)
        ec[row] = 0;

    xh = (int)e.x - (int)cam;
    pp = &e.art->poses[e.disp_pose];
    slot_e = O3_SLOT_TILE(e.art->slot_a, e.disp);
    o3_cells_e = (unsigned int)(pp->cells);
    o3_ne = pp->count;
    o3_bm1_e = (unsigned char)(base_e - 1);
    o3_xh_e = (unsigned int)xh;
    o3_slot_e = slot_e;
    o3_ptop8m1 = (unsigned char)(ptop8 - 1u);
    o3_pb1 = (pb != 0u) ? (unsigned char)(pb - 1u) : 0u;
    o3_rpv0b = rpv0b;
    o3_rpv1b = rpv1b;
#if O3_DRAW_ASM
    o3_draw_enemy();
#else
    {
        const o3_cell *c, *cend;
        c = pp->cells;
        cend = c + pp->count;
        for (; c != cend; c++) {
            int y0, sxv;
            unsigned char o8, bl8, bh8, b, m;

            y0 = base_e + c->dy;
            if ((unsigned int)(y0 - 1) > 190u)
                continue;
            row = (unsigned char)((unsigned char)(c->dy - O3_DY0E) >> 4);
            /* o = y0 - ptop; b = (y0 < ptop); bl8 = (o8>>4) + 16 - 16b;
             * bh8 = bl8 + ((o8&15) != 0), ANTES dos clamps: a formula
             * antiga ((o8+15)>>4) errava o8 em [241..255] (o em [-15..-1],
             * o8+15 estoura o byte e bh8 saia 16 a menos). */
            o8 = (unsigned char)y0 - ptop8;
            b = ((unsigned char)y0 < pb) ? 1u : 0u;
            bl8 = (unsigned char)((o8 >> 4) + 16u - 16u * b);
            bh8 = (unsigned char)(bl8 + ((o8 & 15u) != 0u));
            if (bl8 < rpv0b)
                bl8 = rpv0b;
            if (bh8 > rpv1b)
                bh8 = rpv1b;
            /* rh - rl <= 1 sempre: m sai das maximas adjacentes */
            if (bl8 <= bh8)
                m = (bl8 == bh8) ? o3_mtab[bl8 - 16] : o3_mtab[6u + bl8 - 16];
            else
                m = 0;
            if ((unsigned char)(ec[row] + 1u + m) > O3_PER_ROW_MAX)
                continue;                  /* D9-a2: a celula cai */
            ec[row]++;
            sxv = xh + c->dx;
            if ((unsigned int)sxv > 255u)
                continue;
            SMS_addSprite((unsigned char)sxv, (unsigned char)y0,
                          (unsigned char)(slot_e + (c->cell << 1)));
        }
    }
#endif
}

static void update_probe_fields(unsigned int keys)
{
    probe_hp = pl.hp;
    probe_score = 0;
    probe_boss = e.hp;
    probe_over = pl.dead;
    probe_state = pl.state;
    probe_wave = 0;
    probe_keys = (unsigned char)(keys & 0xFFu);
    probe_pose = pose_now(&pl);   /* pretendida pelo FSM; exibida == pretendida
                                   * fora das janelas de upload */
    probe_px = (unsigned char)(pl.x >> 8);
    probe_pz = pl.z;
    probe_p2x = (unsigned char)(e.x >> 8);
    probe_py = pl.alt;            /* v2 (D10) */
    probe_p2state = e.state;      /* v2 (D10) */
    probe_p2z = e.z;              /* v2 (D10) */
}

static void actor_spawn(o3_actor *a, const o3_as *as, const o3_art *art,
                        unsigned int x, unsigned char z, unsigned char facing,
                        unsigned char hp)
{
    a->as = as;
    a->art = art;
    a->x = x;
    a->z = z;
    a->alt = o3_entry_y[0];
    a->facing = facing;
    a->hp = hp;
    a->hitstop = 0;
    a->guard = 0;
    a->hit_used = 0;
    a->dead = 0;
    a->xacc = 0;
    a->zacc = 0;
    a->disp = 0;
    a->disp_pose = 0xFFu;
    a->up_pose = 0xFFu;
    a->up_slot = 1;
    a->up_want = 0;
    a->up_off = 0;
    a->up_done = 0;
    a->slot_pose[0] = 0xFFu;
    a->slot_pose[1] = 0xFFu;
    a->state = O3_S_FALL;              /* entrada: cai pela tabela (D5) */
    a->arc = O3_ARC_ENTRY;
    a->arc_t = 0;
    start_anim(a, as->fall);
}

void main(void)
{
    unsigned char i;
    unsigned int keys;

    SMS_init();
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_useFirstHalfTilesforSprites(1);
    SMS_displayOff();
    SMS_VDPturnOnFeature(VDPFEATURE_LEFTCOLBLANK | VDPFEATURE_LOCKHSCROLL);

    probe_magic0 = 'S';
    probe_magic1 = 'M';
    probe_magic2 = 'R';
    probe_magic3 = 'T';
    probe_schema = 2;                  /* D10: probe v2 aditivo */
    probe_frame = 0;
    probe_vovf = 0;
    probe_worst_done = 0;
    probe_vline_min = 0xFFu;
    probe_phase = 0;

    actor_spawn(&pl, &pl_as, &pl_art, O3_PLAYER_START_X, O3_PLAYER_START_Z,
                O3_FACING_RIGHT, O3_HP_PLAYER);
    actor_spawn(&e, &en_as, &en_art, O3_ENEMY_X, O3_ENEMY_Z,
                O3_FACING_LEFT, O3_HP_ENEMY);
    e_think = 0;
    cam = 0;
    written_col = 31;
    col_pend_r = O2_STAGE_ROWS;        /* sem coluna em curso (stream fatiado) */

    /* BG/HUD estaticos; os sprites vem do stream bancado (D1/D8). */
    SMS_loadTiles(o2_bg_tiles, O3_TILE_BG_BASE, O2_BG_TILES_SIZE);
    SMS_loadTiles(o2_hud_tiles, O3_TILE_HUD_GREEN, O2_HUD_TILES_SIZE);
    SMS_loadBGPalette(o2_pal_bg);
    SMS_loadSpritePalette(o2_pal_spr);
    SMS_setBackdropColor(1);

    for (i = 0; i < 32u; i++)
        write_bg_col(i);
    draw_hud_boot();                   /* display desligado: 2 linhas inteiras */
    hp_drawn = pl.hp;
    hp_drawn_e = e.hp;
    hud_pl_lo = 0u;
    hud_pl_hi = 0u;
    hud_e_lo = 0u;
    hud_e_hi = 0u;

    preload_boot(&pl);                 /* display desligado: carga inteira */
    preload_boot(&e);

    SMS_initSprites();
    draw_sprites();
    SMS_copySpritestoSAT();
    update_probe_fields(0);

    SMS_displayOn();

    for (;;) {
        SMS_waitForVBlank();

        /* Bloco de VBlank: SAT pronta, 1 coluna de PNT, H-scroll e o
         * chunk de upload (D8: escrita em display ativo derruba o loop). */
        probe_phase = 2;
        SMS_copySpritestoSAT();
#if O3_SPILL_TRACE
        spill_v1 = SMS_VCounterPort;
#endif
        draw_hud();                     /* so reescreve a linha que mudou */
#if O3_SPILL_TRACE
        spill_v2 = SMS_VCounterPort;
#endif
        stream_columns();
        SMS_setBGScrollX((unsigned char)(0u - cam));
#if O3_SPILL_TRACE
        spill_v3 = SMS_VCounterPort;
#endif
        {
            unsigned int budget = O3_UPLOAD_CHUNK;   /* jogador primeiro */
#if O3_SPILL_TRACE
            diag_commit_chunks = 0u;
            diag_commit_bytes_lo = 0u;
            diag_commit_bytes_hi = 0u;
            diag_rd_n = 0u;
#endif
            budget -= stream_commit(&pl, budget);
#if O3_SPILL_TRACE
            diag_t_pl = SMS_VCounterPort;
#endif
            budget -= stream_commit(&e, budget);
#if O3_SPILL_TRACE
            diag_t_e = SMS_VCounterPort;
#endif
        }
        if (!probe_worst_done) {
            probe_phase = 3;
            probe_vline = SMS_VCounterPort;
            if (probe_vline < probe_vline_min) {
                probe_vline_min = probe_vline;
                /* Onde foi: frame/cam/FSM do inimigo (replay do quadro exato). */
                probe_min_frame_lo = (unsigned char)probe_frame;
                probe_min_frame_hi = (unsigned char)(probe_frame >> 8);
                probe_min_cam_lo = (unsigned char)cam;
                probe_min_cam_hi = (unsigned char)(cam >> 8);
                probe_min_p2state = probe_p2state;
            }
            if (probe_vline < 0xC0u)
                probe_vovf++;
            if (probe_frame == (WORST_FRAME_WINDOW - 1u))
                probe_worst_done = 1;
        }
        probe_frame++;
        probe_phase = 1;

        /* Fase de CPU: input/IA -> FSM/arcos -> hit -> stream -> desenho. */
        keys = SMS_getKeysStatus();
        player_control(keys);
        enemy_control();
        actor_advance(&pl);
        actor_advance(&e);
        resolve_hits();
        stream_update(&pl);
        stream_update(&e);

        {
            int c = (int)pl.x - O3_CAM_DX;
            if (c < 0)
                c = 0;
            if (c > (int)O3_CAM_MAX)
                c = (int)O3_CAM_MAX;
            cam = (unsigned int)(c & (~7));
        }

        SMS_initSprites();
        draw_sprites();
        update_probe_fields(keys);
    }
}
