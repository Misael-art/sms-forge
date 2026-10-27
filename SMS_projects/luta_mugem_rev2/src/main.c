/* main.c — luta_mugem_rev2 ROM diagnostica M1 (instrumento de telemetria).
 *
 * Proposito: medir na ROM a parede de streaming VRAM e a pressao de scanline
 * do renderer sprite-only com DOIS atores reais (pacote de dados selecionado
 * pelo manifesto). NAO e entrega de gameplay:
 * omissoes declaradas — sem HUD/audio, sem projetel/FX, sem hitstun com
 * animacao de dano, sem hibrido BG (design wave-4). Desde a wave-5b o papel
 * de cada ator vem do PADEREIO (pad fisico no lado 0, IA no lado 1, ambos
 * pelo mesmo anel de input/tier/comandos), nao de um script: continua sendo
 * maquina de estados sobre dados gerados, nao interpretador CNS.
 *
 * Medicoes (probes __at em 0xC800, schema probe 1):
 *   1. boot: probe_boot_p2_fit registra se os dois idles do pacote selecionado
 *      couberam; o antigo exemplo de 4224 B por lado nao vale para todo corte.
 *   2. streaming: ate 8 pares TALL (64 B) por lado no perfil atual; stall e
 *      evict sao contadores, nao prova de deadline ou ausencia de starvation.
 *   3. scanline: probe_max_line e probe_over8_events so sao atualizados com
 *      LUTA_DIAG_TELEMETRY ligado; sem isso nao provam composicao.
 *   4. Lote B.2: politica de producao = chunk orcado de upload por lado +
 *      exibicao da pose RESIDENTE (imagem valida nunca e' omitida; a espera e'
 *      contada) + nenhum desalojamento do oponente + janela de VBlank com
 *      inicio/fim registrados. Sondas desejada/residente/submetida/apresentada
 *      sao distintas (o disp sozinho nao prova emissao, Lote B doc/25 §88).
 *
 * Autoridades: sdk/devkitSMS/SMSlib/SMSlib.h (API), fight_runtime_data.py
 * schema 5 (layout dos dados). Restricoes: sem float, sem malloc, VRAM apenas
 * durante VBlank (ou display-off no boot), sem DMA.
 */
#include "SMSlib.h"
#include "rev2_diag.h"
#include "fight_input.h"
#include "input_tier.h"      /* INPUT_TIER_T: o limiar que as guardas de abaixo comparam */
#include "versus_scene_runtime.h"
#include "fight_runtime_data.h"

/* A versao anterior do pacote apontava P2 para a face direita. Usar aquele
 * header com este runtime confundiria bytes e metadata, inclusive quando o
 * offset parecesse caber. Exigir o contrato emitido pelo gerador atual. */
#if !defined(VERSUS_FACE_LAYOUT_ADJACENT_P2_LEFT) || VERSUS_FACE_LAYOUT_ADJACENT_P2_LEFT != 1
#error "versus-cut sem contrato de faces adjacentes P1-direita/P2-esquerda; regenere os dados"
#endif

/* Pacote cruzado: tabelas const dos 2 lutadores levam a imagem não-bancada a
 * ~19,6 KB — dentro do teto documentado de 32 KB (sdk/README, skill
 * sms-banking-header), entao o par de header migra para a variante 32 KB
 * (SEGA @0x7FF0 / SDSC @0x7FE0, bank 1 estatico no boot). */
SMS_EMBED_SEGA_ROM_HEADER(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE(0, 1, "SMSForge", "luta_mugem_rev2",
                                     "diag m4 ryu/ken streaming");

#define DIAG_FLOOR          160u          /* chao em px da arena solida */
#define DIAG_X_MIN          (16u * 256u)  /* Q8.8 borda util */
#define DIAG_X_MAX          (240u * 256u)
#define POOL_PAIRS          128u          /* 8192 B / 64 B por par TALL */
#define SOLID_BG_TILE       256u          /* 0x2000: fora do pool de sprites */
#define SCRIPT_STEP_FRAMES  150u          /* janela de pacing/SMRT (wave-4) */

/* wave-4l: chave LOCAL do projeto (build_inner.py nao aceita -D por projeto;
 * curadoria de wrapper exigira aprovacao humana). 1 = ROM diagnostica com a
 * particao regional 4j. 0 = ROM sem telemetria diagnostica (tick ISR, wraps
 * de regiao, clear+varredura line_diff, diffs de emit_frame, bloco de pacing);
 * permanecem apenas as sondas do contrato de selo (SMRT, vline/vovf/
 * worst_done) — e o corpo adjacente-entrega que o selo worst-frame mede. */
#define LUTA_DIAG_TELEMETRY 0

/* wave-4m (gate b'): chave LOCAL do projeto, mesmo padrao da 4l (build_inner
 * nao aceita -D por projeto; curadoria de wrapper exige aprovacao humana).
 * 1 = emissao por SMS_addSprite (asm naked, custo documentado no fonte da
 * biblioteca) no lugar de SMS_addSpriteClipping (C com predicados de recorte).
 * A troca so e admitida se o gate de equivalencia visual passar: o pre-guard
 * do emit_frame ja restringe sx a [0,256) e sy a [0,192), que sao exatamente
 * as faixas em que os predicados de recorte da biblioteca nao podem rejeitar.
 * 0 = caminho atual (clip). */
#define LUTA_DIAG_CLIP_PLAIN 1

/* Lote B (doc/25): perfil de runtime UNICO com chave LOCAL (mesmo padrao da
 * 4l/4m; build_inner.py nao aceita -D por projeto). 0 = diagnostico: o laco
 * mantem a ordem historica do baseline (upload e logica DEPOIS de
 * waitForVBlank; SAT no fim da fase de emissao) — e o instrumento congelado.
 * 1 = producao: logica/input/cache/construcao de metasprites rodam no display
 * ativo; so os commits VDP (upload de patterns + copia da SAT) ficam no
 * VBlank, com a janela registrada (probe_phase 2->3; vline/vovf ao fim).
 * Nao ha duas engines: as MESMAS funcoes sao chamadas nas duas ordens; a
 * v031 permanece a referencia diagnostica arquivada. */
#define LUTA_PROFILE 1

/* Lote B.2: teto de pares TALL por VBlank POR LADO no perfil de producao.
 * O valor e' candidato declarado e a medida que o elege e' o par
 * (probe_upload_pairs_maxvbl, probe_vline/probe_vovf) nas sessoes de
 * worst-frame: cada candidato (2/4/8) e' uma ROM com SHA proprio, mesma carga,
 * unico delta = este define. O orcamento real de VBlank e' medido, nao
 * presumido: 1 par = 64 B de OUTI em VBlank + a copia da SAT, com o teto
 * fechado registrado por probe_vbl_entry/probe_vbl_exit_max. */
#define UPLOAD_CHUNK_PAIRS 8u

/* wave-5b: o classificador de tier do doador tem UM limiar (INPUT_TIER_T) e os
 * blobs CMD emitidos trazem o tier 1/2 por familia; a maquina so e fiel se o
 * limiar do anel for o mesmo limiar que o gerador usou para classificar a trilha
 * (converters/sms_controls.py classify_trace). Guarda de compilacao no idiomado
 * doador (src/input.c): se o gerar outro DEF com limiar diferente, o build para
 * aqui em vez de emitir fraco/forte invertido em runtime. */
typedef char input_tier_guarda_p1[
    (INPUT_TIER_T == P1_CUT_INPUT_THRESHOLD_KEY1 &&
     INPUT_TIER_T == P1_CUT_INPUT_THRESHOLD_KEY2) ? 1 : -1];
typedef char input_tier_guarda_p2[
    (INPUT_TIER_T == P2_CUT_INPUT_THRESHOLD_KEY1 &&
     INPUT_TIER_T == P2_CUT_INPUT_THRESHOLD_KEY2) ? 1 : -1];

/* ---------------- probes (corredor __at; volatile por L009) --------------
 * Formas canonicas: `volatile unsigned <tipo> __at(0xADDR) nome;` — o audit
 * deriva o corredor do fonte (measure_worst_frame.PROBE_DECL_RX). */
volatile unsigned int __at(0xC800) probe_magic;         /* 0x5232 */
volatile unsigned int __at(0xC802) probe_schema;        /* 1 */
volatile unsigned int __at(0xC804) probe_frame;
volatile unsigned int __at(0xC806) probe_step;
volatile unsigned int __at(0xC808) probe_stall_frames;
volatile unsigned int __at(0xC80A) probe_uploaded_pairs;
volatile unsigned int __at(0xC80C) probe_evict_events;
volatile unsigned int __at(0xC80E) probe_omitted_sat;
volatile unsigned int __at(0xC810) probe_over8_events;
volatile unsigned int __at(0xC812) probe_max_line;
volatile unsigned int __at(0xC814) probe_free_pairs_min;
volatile unsigned int __at(0xC816) probe_used_pairs_max;
volatile unsigned int __at(0xC818) probe_disp_p1;       /* 0xFFFF = ausente */
volatile unsigned int __at(0xC81A) probe_disp_p2;
volatile unsigned int __at(0xC81C) probe_boot_p2_fit;   /* 1 coube, 0 nao */
volatile unsigned int __at(0xC81E) probe_boot_overflow_b;
/* Sonda de pacing (REBAIXADA pela atribuicao wave-4): o flanco da ISR e
 * coalescido pelo waitForVBlank, entao este contador marca iteracoes do
 * loop (1 wake por iteracao), NAO periodos de VBlank consumidos — delta==1
 * nao prova que o corpo cabe no frame. Periodo real: razao frames-VDP /
 * iteracoes no BlastEm + probe_vbl_tick abaixo. */
volatile unsigned int __at(0xC820) probe_vblank_total;
volatile unsigned int __at(0xC822) probe_vbl_prev_iter;
volatile unsigned int __at(0xC824) probe_vbl_per_iter_max;

/* Atribuicao regional do corpo (wave-4b..4e). Fase 1: stream=0 em 592 iteracoes,
 * emissao=87,1%. Fase 2 (ROM a25169f7): SMS_copySpritestoSAT=1 flanco em 592
 * (~0), logica=0,41, TODO o corpo esta na preparacao da emissao. Fase 3:
 * emit_frame=2,67/iter domina. Wave-4c: telemetria de 16 linhas por sprite
 * vira array de diferencas + varredura unary (emit_frame inteiro cai a 0,85).
 * Wave-4d (ROM f921b815): varredura movida para a regiao pool; add-only
 * =0,46/iter, pool+varredura=0,53, logica=0,83 (cauda 1,20) — o dominante
 * remanescente e a LOGICA. Wave-4e: DA-DB (preenchimento, medido 0,06 e
 * mergeado na regiao de emissao) passa a medir o bloco de step do script,
 * sub-regiao de D8-D9; logica menos step isola FSM/atores/request_pose.
 * Stream medido zero duas vezes e reincorporado na regiao de logica;
 * sat medido ~0 reincorporado na regiao de pool. Tick real de VBlank no hook
 * da SMSlib (SMS_setFrameInterruptHandler, SMSlib.h:373 = autoridade #8; esta
 * ROM nao tem PSGlib nem outro dono do hook). 8 bits = atomico no Z80.
 * Layout sem sobreposicao: D7 tick, D8-D9 logica (stream+FSM+atores+step),
 * DA-DB atores+pose (⊂ D8-D9; step medido na 4e e zerado, reocupado na 4f), DC-DD initSprites+preenchimento+emit_frame
 * (add-only), DE-DF varredura+espelhos/pool+SAT. D0..D6 reservados a
 * semantica de profile das ferramentas; EF nunca declarado. */
volatile unsigned char __at(0xC8D7) probe_vbl_tick;
volatile unsigned int __at(0xC8D8) probe_reg_logic_edges;
volatile unsigned int __at(0xC8DA) probe_reg_actors_edges;
volatile unsigned int __at(0xC8DC) probe_reg_frame_edges;
volatile unsigned int __at(0xC8DE) probe_reg_pool_edges;

void probe_vbl_isr(void) { probe_vbl_tick++; }

/* ---------------- M2 (wave-5a): sondas de colisao/dano/hitstop ------------
 * Palavras livres do corredor 0xC826..0xC838 (folga medida 1791 na wave-4m;
 * D0..D6 continuam reservados ao profile das ferramentas, EF nunca
 * declarado). damage_pN = sofrido pelo lado N; hitstop conta actor-frames
 * congelados; clsn_checks = quadros S_HIT avaliados (prova de consumo). */
volatile unsigned int __at(0xC826) probe_hit_events;
volatile unsigned int __at(0xC828) probe_guard_events;
volatile unsigned int __at(0xC82A) probe_damage_p1;
volatile unsigned int __at(0xC82C) probe_damage_p2;
volatile unsigned int __at(0xC82E) probe_life_p1;
volatile unsigned int __at(0xC830) probe_life_p2;
volatile unsigned int __at(0xC832) probe_hitstop_frames;
volatile unsigned int __at(0xC834) probe_ko_events;
volatile unsigned int __at(0xC836) probe_clsn_checks;
volatile unsigned int __at(0xC838) probe_pusher_frames;
volatile unsigned int __at(0xC83A) probe_face_flips;
/* wave-5a: estado geometrico dos atores em px, para cotejar o simulador
 * offline com a ROM sem adivinhar posicao (a captura so mostra o resultado). */
volatile unsigned int __at(0xC83C) probe_x_p1;
volatile unsigned int __at(0xC83E) probe_x_p2;
volatile unsigned int __at(0xC840) probe_face_p1;   /* 0 direita, 1 esquerda */
volatile unsigned int __at(0xC842) probe_face_p2;

/* ---------------- wave-5b: sondas da camada de input ---------------------
 * Espelho cru da porta (prova de mapeamento de bit, nao de interpretacao), os
 * niveis K_* que entraram no anel por lado, contagens de comando casado por
 * resultado (virou papel x reconhecido sem rota de golpe), frames com anel
 * ativo, trocas de papel por input e a leitura dos DADOS (numero de rotas e
 * mascara de codigos de golpe ausentes). 0xC844..0xC861. */
volatile unsigned char __at(0xC844) probe_levels_p1;
volatile unsigned char __at(0xC845) probe_levels_p2;
volatile unsigned int __at(0xC846) probe_keys_raw;        /* SMS_getKeysStatus */
volatile unsigned int __at(0xC848) probe_cmd_hits_p1;     /* virou papel */
volatile unsigned int __at(0xC84A) probe_cmd_hits_p2;
volatile unsigned int __at(0xC84C) probe_cmd_unrouted_p1; /* casou, sem golpe */
volatile unsigned int __at(0xC84E) probe_cmd_unrouted_p2;
volatile unsigned int __at(0xC850) probe_input_frames_p1;
volatile unsigned int __at(0xC852) probe_input_frames_p2;
volatile unsigned int __at(0xC854) probe_role_changes_p1;
volatile unsigned int __at(0xC856) probe_role_changes_p2;
volatile unsigned char __at(0xC858) probe_cmd_route_count;   /* command_count */
volatile unsigned char __at(0xC859) probe_cmd_unrouted_mask; /* LP|HP|LK|HK */
volatile unsigned char __at(0xC85A) probe_tier_t;            /* INPUT_TIER_T */
volatile unsigned char __at(0xC85B) probe_ai_beat;           /* beat da IA */
volatile unsigned int __at(0xC85C) probe_cmd_last_index_p1;
volatile unsigned int __at(0xC85E) probe_cmd_last_index_p2;

/* ---------------- Lote B.2: sondas da politica de producao ----------------
 * Corredor livre 0xC862..0xC8D1 (folga medida 1547 B; mapa f348df69). Quatro
 * estados DISTINTOS por lado (doc/25 §88): desejada (pedido da logica),
 * residente (bytes em VRAM), submetida (frame entregue ao construtor de
 * metasprites em RAM) e apresentada (submetida sem rejeicao da SAT no lado).
 * 0xFFFF = ausente. Espera = frames com imagem valida porem pose antiga;
 * substituicao = pending com dados em voo trocado por pedido novo (recuperacao
 * de fila medida); overflow = pedido sem alocacao (politica de producao NAO
 * desaloja o oponente); omissao SAT por lado = pecas rejeitadas por addSprite. */
volatile unsigned int __at(0xC862) probe_desired_p1;
volatile unsigned int __at(0xC864) probe_desired_p2;
volatile unsigned int __at(0xC866) probe_resident_p1;
volatile unsigned int __at(0xC868) probe_resident_p2;
volatile unsigned int __at(0xC86A) probe_submit_p1;
volatile unsigned int __at(0xC86C) probe_submit_p2;
volatile unsigned int __at(0xC86E) probe_present_p1;
volatile unsigned int __at(0xC870) probe_present_p2;
volatile unsigned int __at(0xC872) probe_wait_p1;
volatile unsigned int __at(0xC874) probe_wait_p2;
volatile unsigned int __at(0xC876) probe_overflow_p1;
volatile unsigned int __at(0xC878) probe_overflow_p2;
volatile unsigned int __at(0xC87A) probe_superseded_p1;
volatile unsigned int __at(0xC87C) probe_superseded_p2;
volatile unsigned int __at(0xC87E) probe_sat_om_p1;
volatile unsigned int __at(0xC880) probe_sat_om_p2;
volatile unsigned int __at(0xC882) probe_backlog_max;      /* pico de pares pendentes */
volatile unsigned int __at(0xC884) probe_upload_maxvbl;    /* pico de pares por VBlank */
volatile unsigned char __at(0xC886) probe_vbl_entry;       /* VCounter ao entrar no work */
volatile unsigned char __at(0xC887) probe_vbl_exit_max;    /* pior saida sem wrap */
volatile unsigned int __at(0xC888) probe_bad_pose_ref;     /* descritor recusado */
volatile unsigned char __at(0xC88A) probe_resident_face_p1;
volatile unsigned char __at(0xC88B) probe_resident_face_p2;
volatile unsigned char __at(0xC88C) probe_desired_face_p1;
volatile unsigned char __at(0xC88D) probe_desired_face_p2;
volatile unsigned char __at(0xC88E) probe_submit_face_p1;
volatile unsigned char __at(0xC88F) probe_submit_face_p2;
volatile unsigned int __at(0xC890) probe_push_invalid_geometry;

/* Contrato worst-frame do measure_worst_frame.py (L061), SMRT aditivo na
 * base 0xC800: probe_vline = VCounter lido APOS todo o trabalho do frame
 * (upload, logic, metasprite, SAT copiado). >=0xC0 = fechou dentro do
 * VBlank; <0xC0 = derramou no proximo display ativo, contado por
 * probe_vovf (word, sem saturacao). A ROM mede 3000 frames continuos de
 * atracao e sela o menor vline em probe_vline_min com probe_worst_done=1;
 * o DAP so conecta depois do selo. 0xC8EF fica nunca declarado: topo da
 * pilha do laco main aliasa o bloco F0+ (contrato do tool). */
volatile unsigned char __at(0xC8D2) probe_vline_min;
volatile unsigned char __at(0xC8EA) probe_vline;
volatile unsigned int __at(0xC8EB) probe_vovf;
volatile unsigned char __at(0xC8ED) probe_phase;
volatile unsigned char __at(0xC8EE) probe_worst_done;

#define WORST_FRAME_WINDOW 3000u

/* VCounter do VDP, porta 0x7E. Verificado no header autoridade #8: SMSlib.h
 * NAO expoe leitura de line counter. Porta de hardware, nao API inventada. */
__sfr __at (0x7e) SMS_VCounterPort;

/* Bloco SMRT canonico da pagina 0xC800 — contrato lido por
 * measure_runtime_probe.py (magic+schema em +0xE0, frame em +0xF0,
 * snapshot em +0xF2..+0xFB). Espelhos byte com clamp declarados:
 * state=boot_p2_fit, wave=evict, keys=omitted_sat, +0xF9=stall,
 * px=uploaded, py=role_p1, hp=step, score=max_line, boss/over=used/free. */
volatile unsigned char __at(0xC8E0) probe_smrt_magic[4];    /* 'S','M','R','T' */
volatile unsigned char __at(0xC8E4) probe_smrt_schema;      /* 1 */
volatile unsigned int __at(0xC8F0) probe_smrt_frame;        /* espelho de frames */
volatile unsigned char __at(0xC8F2) probe_b_step;
volatile unsigned char __at(0xC8F3) probe_b_maxline;
volatile unsigned char __at(0xC8F4) probe_b_used;
volatile unsigned char __at(0xC8F5) probe_b_free;
volatile unsigned char __at(0xC8F6) probe_b_bootfit;
volatile unsigned char __at(0xC8F7) probe_b_evict;
volatile unsigned char __at(0xC8F8) probe_b_omitted;
volatile unsigned char __at(0xC8F9) probe_b_stall;
volatile unsigned char __at(0xC8FA) probe_b_uploaded;
volatile unsigned char __at(0xC8FB) probe_b_role_p1;

#define CLAMP255(v) ((unsigned char)((v) > 255u ? 255u : (v)))

/* ---------------- atores do script --------------------------------------- */
typedef struct {
    unsigned int x;              /* Q8.8 */
    unsigned int y;              /* altura sobre o chao, Q8.8 */
    signed int vy;
    unsigned char role, anim, fidx, tick;
    unsigned char done;          /* wave-5b: one-shot do papel expirou */
    unsigned short life;         /* M2: dados — inicia em max_life */
    unsigned char hit_done;      /* M2: golpe ja registrado nesta entrada de estado */
    unsigned char stop;          /* M2: hitstop restante em frames deste ator */
    unsigned char face;          /* M2: 0 = para a direita, 1 = para a esquerda */
} DiagActor;

static DiagActor fighter[2];

/* ---------------- cache de poses (pool VRAM 0x0000..0x1FFF) -------------- */
typedef struct {
    unsigned int pose_global;    /* 0xFFFF = vazio */
    unsigned char base_pair;     /* par TALL inicial no pool */
    unsigned char n_pairs;
    unsigned char loaded_pairs;
    const Frame *frame;          /* Lote B.2: frame residente (imagem valida) */
    unsigned char face;          /* orientacao dos bytes e metadados residentes */
} CacheSlot;

/* O conjunto vivo e derivado dos 4 slots (corrente/pendente x 2 lados).
 * Uma falha de alocacao so pode ser memorizada ate a proxima mudanca do
 * conjunto; flags invalidas nao podem dar a volta como uma epoca de 8 bits. */
static unsigned char fail_valid[2];
static unsigned char fail_size[2];
static CacheSlot current[2], pending[2];
#if LUTA_DIAG_TELEMETRY
static unsigned char line_diff[DIAG_FLOOR];
#endif
static unsigned int frames;

static void cache_invalidate(CacheSlot *s) {
    if (s->pose_global != 0xFFFFu) {
        fail_valid[0] = fail_valid[1] = 0u;
        s->n_pairs = 0;
    }
    s->pose_global = 0xFFFFu;
    s->loaded_pairs = 0;
    s->frame = 0;            /* Lote B.2: sem frame residente, sem imagem */
}

/* wave-4i: first-fit POR EXTENSOES, equivalente por construcao ao scan de
 * bitmap. Prova: o menor inicio livre x* de um run de n pares ou e 0, ou o
 * par x*-1 esta ocupado por um bloco vivo e como [x*, x*+n) e livre esse
 * bloco termina exatamente em x*. Logo basta testar {0} U {fim de cada um
 * dos 4 slots vivos} e tomar o menor candidato sem sobreposicao — a base
 * escolhida e identica a do scan anterior, sem caminhar 128 pares. */
static unsigned char alloc_contiguous(unsigned char n, unsigned char *out_base) {
    const CacheSlot *all[4];
    unsigned char cand, best, i, j, fits;

    all[0] = &current[0];
    all[1] = &current[1];
    all[2] = &pending[0];
    all[3] = &pending[1];
    best = 0xFFu;
    for (i = 0; i < 5u; i++) {
        cand = 0;
        if (i != 0u) {
            if (all[i - 1u]->pose_global == 0xFFFFu)
                continue;
            cand = (unsigned char)(all[i - 1u]->base_pair +
                                   all[i - 1u]->n_pairs);
        }
        if ((unsigned int)cand + (unsigned int)n > POOL_PAIRS)
            continue;
        fits = 1;
        for (j = 0; j < 4u; j++) {
            if (all[j]->pose_global == 0xFFFFu)
                continue;
            if (cand + n <= all[j]->base_pair)
                continue;
            if (all[j]->base_pair + all[j]->n_pairs <= cand)
                continue;
            fits = 0;
            break;
        }
        if (fits && cand < best)
            best = cand;
    }
    if (best == 0xFFu)
        return 0;
    *out_base = best;
    fail_valid[0] = fail_valid[1] = 0u;
    return 1;
}

static unsigned char used_pairs(void) {
    const CacheSlot *all[4];
    unsigned char i, n = 0;

    all[0] = &current[0];
    all[1] = &current[1];
    all[2] = &pending[0];
    all[3] = &pending[1];
    for (i = 0; i < 4u; i++)
        if (all[i]->pose_global != 0xFFFFu)
            n = (unsigned char)(n + all[i]->n_pairs);
    return n;
}

/* O versus-cut guarda duas faces adjacentes de mesmo tamanho. A referencia
 * P1 aponta para direita; a P2 aponta para esquerda (com sua propria faixa
 * de indices da paleta compartilhada). Recusar qualquer descritor cujo par
 * de faces nao caiba inteiro na pagina de 16 KiB antes de tocar a VRAM. */
static unsigned char pose_facing_offset(const PoseRef *ref, unsigned char side,
                                        unsigned char face, unsigned int *offset) {
    unsigned int size = ref->size;
    if (side > 1u || face > 1u || ref->bank < 2u || size == 0u ||
        size > 8192u || (size & 63u))
        return 0u;
    if (side == 0u) {
        if (ref->off > 16384u - (size << 1)) return 0u;
        *offset = ref->off + (face ? size : 0u);
    } else {
        if (ref->off < size || ref->off > 16384u - size) return 0u;
        *offset = ref->off - (face ? 0u : size);
    }
    return 1u;
}

/* Sobe ate `budget` pares (64 B cada) do pending; budget==0xFF sobe o pose
 * inteiro (usado apenas no boot, com display ainda OFF). Lote B.2: o laco de
 * producao chama com UPLOAD_CHUNK_PAIRS por lado (orcamento medido), com
 * servico garantido a cada lado por VBlank; retorna os pares subidos para o
 * registro do pico por VBlank (probe_upload_maxvbl). */
static unsigned char stream_pending(unsigned char side, unsigned char budget) {
    const PoseRef *ref;
    const unsigned char *source;
    unsigned int vram, pose_offset;
    unsigned char moved, batch;

    if (pending[side].pose_global == 0xFFFFu ||
        pending[side].loaded_pairs >= pending[side].n_pairs)
        return 0u;
    ref = &versus_poses[pending[side].pose_global];
    if (!pose_facing_offset(ref, side, pending[side].face, &pose_offset)) {
        cache_invalidate(&pending[side]);
        probe_bad_pose_ref++;
        return 0u;
    }
    moved = 0u;
    SMS_saveROMBank();
    SMS_mapROMBank(ref->bank);
    while (budget && pending[side].loaded_pairs < pending[side].n_pairs) {
        /* A API brief recebe size em byte: 4 pares seriam 256 e
         * truncariam para zero. Tres pares consecutivos cabem em 192 B e
         * preservam a mesma ordem e janela de patterns da pose. */
        batch = (unsigned char)(pending[side].n_pairs - pending[side].loaded_pairs);
        if (batch > budget) batch = budget;
        if (batch > 3u) batch = 3u;
        vram = (unsigned int)(pending[side].base_pair +
                              pending[side].loaded_pairs) * 64u;
        source = (const unsigned char *)(0x8000u + pose_offset +
                              (unsigned int)pending[side].loaded_pairs * 64u);
        SMS_VRAMmemcpy_brief(vram, source, (unsigned char)(batch << 6));
        pending[side].loaded_pairs = (unsigned char)(pending[side].loaded_pairs + batch);
        probe_uploaded_pairs += batch;
        budget = (unsigned char)(budget - batch);
        moved = (unsigned char)(moved + batch);
    }
    SMS_restoreROMBank();
    if (pending[side].loaded_pairs >= pending[side].n_pairs) {
        cache_invalidate(&current[side]);
        current[side] = pending[side];
        pending[side].pose_global = 0xFFFFu;
        pending[side].frame = 0;
    }
    return moved;
}

/* Pede o pose para o lado, com o frame que o representa (Lote B.2: o frame
 * residente passa a ser guardado no slot para que a exibicao mantenha imagem
 * valida nos misses). Diagnostico (PROFILE=0): sem espaco, descarta pending do
 * adversario; ainda sem espaco, EVICTA o current adversario (omissao visivel
 * medida). Producao (PROFILE=1): NENHUM desalojamento do oponente; falha de
 * alocacao mantem as duas imagens e conta overflow (o pedido espera o proximo
 * evento de fila — completude/supersessao invalida o memo de falha). */
static void request_pose(unsigned char side, unsigned int pose_global,
                         unsigned char n_pairs, const Frame *frame,
                         unsigned char face) {
    unsigned char base;
    unsigned int checked_offset;
    if (side > 1u) {
        probe_bad_pose_ref++;
        return;
    }
    if (face > 1u || pose_global >= VERSUS_POSE_COUNT) {
        cache_invalidate(&pending[side]);
        probe_bad_pose_ref++;
        return;
    }
    if (current[side].pose_global == pose_global && current[side].face == face) {
        /* Uma solicitacao pode voltar a imagem residente enquanto outra
         * ainda e carregada. Cancelar essa geracao impede sua promocao
         * posterior; a mesma imagem pode ter metadata AIR diferente. */
        if (pending[side].pose_global != 0xFFFFu) {
            if (side == 0u) probe_superseded_p1++;
            else            probe_superseded_p2++;
            cache_invalidate(&pending[side]);
        }
        current[side].frame = frame;
        return;
    }
    if (pending[side].pose_global == pose_global && pending[side].face == face) {
        /* A imagem ainda em voo pode ser reutilizada por outro elemento AIR;
         * conservar os bytes, mas publicar a metadata do elemento atual. */
        pending[side].frame = frame;
        return;
    }
    if (!pose_facing_offset(&versus_poses[pose_global], side, face, &checked_offset) ||
        (versus_poses[pose_global].size >> 6) != n_pairs) {
        cache_invalidate(&pending[side]);
        probe_bad_pose_ref++;
        return;
    }
    /* Com o pool inalterado, falha de mesmo tamanho permanece impossivel.
     * Qualquer alocacao ou liberacao invalida o memo dos dois lados. */
    if (fail_valid[side] && fail_size[side] == n_pairs) {
        probe_stall_frames++;
        return;
    }
    /* Lote B.2: pending com dados em voo trocado por pedido novo = substituicao
     * segura (o span alocado e' liberado por cache_invalidate; o upload sempre
     * esteve indexado ao slot, nunca a um pedido global). */
    if (pending[side].pose_global != 0xFFFFu) {
        if (side == 0u) probe_superseded_p1++;
        else            probe_superseded_p2++;
    }
    cache_invalidate(&pending[side]);
    if (alloc_contiguous(n_pairs, &base)) {
        pending[side].pose_global = pose_global;
        pending[side].base_pair = base;
        pending[side].n_pairs = n_pairs;
        pending[side].loaded_pairs = 0;
        pending[side].frame = frame;
        pending[side].face = face;
        return;
    }
#if LUTA_PROFILE
    /* Producao: nao desaloja o oponente (nem pending, nem current). */
    if (side == 0u) probe_overflow_p1++;
    else            probe_overflow_p2++;
#else
    cache_invalidate(&pending[side ^ 1u]);
    if (alloc_contiguous(n_pairs, &base)) {
        pending[side].pose_global = pose_global;
        pending[side].base_pair = base;
        pending[side].n_pairs = n_pairs;
        pending[side].loaded_pairs = 0;
        pending[side].frame = frame;
        pending[side].face = face;
        return;
    }
    if (current[side ^ 1u].pose_global != 0xFFFFu) {
        cache_invalidate(&current[side ^ 1u]);
        probe_evict_events++;
        if (alloc_contiguous(n_pairs, &base)) {
            pending[side].pose_global = pose_global;
            pending[side].base_pair = base;
            pending[side].n_pairs = n_pairs;
            pending[side].loaded_pairs = 0;
            pending[side].frame = frame;
            pending[side].face = face;
            return;
        }
    }
#endif
    fail_valid[side] = 1u;
    fail_size[side] = n_pairs;
    probe_stall_frames++;
}

/* ---------------- metasprite -> SAT + contagem por scanline -------------- */
static void emit_frame(unsigned char side, const Frame *frame) {
    signed int axis_x = (signed int)((unsigned int)frame->axis[0] |
                            ((unsigned int)frame->axis[1] << 8));
    signed int axis_y = (signed int)((unsigned int)frame->axis[2] |
                            ((unsigned int)frame->axis[3] << 8));
    const unsigned char *meta_data;
    const signed char *meta;
    signed int origin_x, origin_y, dx, dy, sx, sy;
    unsigned char tile_base, tile;
    signed int add;

    /* Metadados, origem e indices devem pertencer a MESMA face residente;
     * a face logica pode mudar enquanto os novos patterns ainda sobem. */
    if (side)
        meta_data = current[side].face ? frame->metal_p2 : frame->meta_p2;
    else
        meta_data = current[side].face ? frame->metal : frame->meta;
    if (!meta_data)
        return;
    tile_base = (unsigned char)(current[side].base_pair * 2u);
    origin_y = (signed int)DIAG_FLOOR -
               (signed int)(fighter[side].y >> 8) + axis_y;
    if (!current[side].face)
        origin_x = (signed int)(fighter[side].x >> 8) + axis_x;
    else
        origin_x = FIGHTER_MIRRORED_ORIGIN_X(
                       (unsigned char)(fighter[side].x >> 8), axis_x,
                       frame->width);
    meta = (const signed char *)meta_data;
    while (meta[0] != (signed char)METASPRITE_END) {
        dx = meta[0];
        dy = meta[1];
        tile = (unsigned char)meta[2] + tile_base;
        sx = origin_x + dx;
        sy = origin_y + dy;
        if (sx >= 0 && sx < 256 && sy >= 0 && sy < 192) {
#if LUTA_DIAG_CLIP_PLAIN
            /* wave-4m (gate b'): SMS_addSprite e o macro do header (SMSlib.h:189)
             * que expandse SMS_addSprite_f (asm naked). Sem NO_SPRITE_CHECKS o
             * header (SMSlib.h:199) declara retorno signed char: -1 SAT cheia,
             * -2 Y invalido (0xD1, inalcanca com sy<192). Rejeicao por recorte
             * exclusiva do clip exige janela fora de [0,255]x[0,191] ou
             * coordenada fora do pre-guard — ambos inalcanaveis aqui. */
            add = SMS_addSprite(sx, sy, tile);
#else
            add = SMS_addSpriteClipping(sx, sy, tile);
#endif
            if (add < 0) {
                probe_omitted_sat++;
                if (side == 0u) probe_sat_om_p1++;
                else            probe_sat_om_p2++;
            }
#if LUTA_DIAG_TELEMETRY
            else if (sy < (signed int)DIAG_FLOOR) {
                /* wave-4c: array de diferencas no lugar do loop de 16 linhas
                 * por sprite (2.67 flancos/iter na fase 3). Duas escritas por
                 * sprite; a varredura unary ocorre uma vez por frame no loop
                 * principal, com semantica identica: probe_over8_events conta
                 * linhas com contagem final >= 9 (cada linha cruza o 9 uma
                 * unica vez, incrementos monotonicos) e probe_max_line e o
                 * maximo final. sy ja esta clipado em [0,192) acima. */
                line_diff[(unsigned char)sy]++;
                if ((sy + 16) < (signed int)DIAG_FLOOR)
                    line_diff[(unsigned char)(sy + 16)]--;
            }
#endif
        }
        meta += 3;
    }
}

/* ---------------- FSM de script (dados gerados, nao nomes) --------------- */
/* Passo de posicao em Q8.8 SEM SINAL. Em Z80/SDCC `int` tem 16 bits: a borda
 * util DIAG_X_MAX (240 px = 61440) nao cabe em signed int (vira -4096; 0xF000
 * como int16 assinado - antes grafado -3926), entao
 * qualquer clamp escrito em dominio assinado e verdadeiro para quase todo nx e
 * teleporta o ator para a borda direita. O delta e sempre pequeno (velocidade
 * CNS ou push), entao a direcao decide o lado da subtracao e nenhum valor
 * acima de 32767 e lido como assinado. */
static void move_x(unsigned char side, signed int delta) {
    unsigned int x = fighter[side].x;
    if (delta >= 0) {
        unsigned int d = (unsigned int)delta;
        if (d > (unsigned int)(DIAG_X_MAX - x)) x = DIAG_X_MAX;
        else x += d;
    } else {
        unsigned int d = (unsigned int)(0 - delta);
        if (x <= (unsigned int)(DIAG_X_MIN - 1u) + d) x = DIAG_X_MIN;
        else x -= d;
    }
    fighter[side].x = x;
}

static void set_role(unsigned char side, unsigned char role) {
    const CharacterData *cd = &characters[side];
    fighter[side].role = role;
    fighter[side].anim = cd->states[role].anim;
    fighter[side].fidx = 0;
    fighter[side].tick = 0;
    fighter[side].done = 0u;     /* wave-5b: nova instancia de papel */
    fighter[side].hit_done = 0u;   /* M2: nova instancia de golpe */
    if ((cd->states[role].flags & S_AIR) && fighter[side].y == 0)
        fighter[side].vy = cd->jump_vy;
}

static void advance_actor(unsigned char side, unsigned int *out_pose_global,
                          const Frame **out_frame) {
    const CharacterData *cd = &characters[side];
    const Anim *anim = &cd->anims[fighter[side].anim];
    const Frame *frame = &anim->frames[fighter[side].fidx];
    signed int vel;

    /* M2: hitstop congela o avanco deste ator (sem movimento, gravidade ou
     * tick de animacao); o frame e a pose permanecem os atuais. */
    if (fighter[side].stop) {
        fighter[side].stop--;
        probe_hitstop_frames++;
        *out_pose_global = (unsigned int)cd->pose_base + frame->pose;
        *out_frame = frame;
        return;
    }

    vel = cd->states[fighter[side].role].vel;
    if (vel && fighter[side].y == 0)
        move_x(side, fighter[side].face ? -vel : vel);
    if (fighter[side].y || fighter[side].vy) {
        signed int ny = (signed int)fighter[side].y + fighter[side].vy;
        fighter[side].vy -= cd->gravity;
        if (ny <= 0) { ny = 0; fighter[side].vy = 0; }
        fighter[side].y = (unsigned int)ny;
    }

    /* tick conta quantas vezes o elemento atual ja foi entregue a logica.
     * Transitar ANTES da proxima entrega preserva elementos de duracao 1 e
     * mantem fidx no elemento visivel durante hitstop. O gerador deste corte
     * emite duracoes 1..254 ou 255 para hold; PAL e fidelidade de holds
     * continuam sujeitos aos contratos e provas especificos. */
    if (frame->dur != 255u && fighter[side].tick >= frame->dur) {
        fighter[side].tick = 0u;
        if (fighter[side].fidx + 1u < anim->n_frames)
            fighter[side].fidx++;
        else if (anim->loop_start != 255u)
            fighter[side].fidx = anim->loop_start;
        else
            fighter[side].tick = frame->dur; /* terminal: nao reiniciar */
        frame = &anim->frames[fighter[side].fidx];
    }
    *out_pose_global = (unsigned int)cd->pose_base + frame->pose;
    *out_frame = frame;
    if (frame->dur != 255u) {
        if (fighter[side].tick < frame->dur) fighter[side].tick++;
        if (fighter[side].tick >= frame->dur &&
            fighter[side].fidx + 1u >= anim->n_frames && anim->loop_start == 255u)
            fighter[side].done = 1u;
    } else if (fighter[side].fidx + 1u >= anim->n_frames) {
        fighter[side].done = 1u;  /* politica historica de hold terminal */
    }
}

/* ---------------- M2 (wave-5a): colisao/guarda/dano/hitstop/pusher --------
 * Consome exclusivamente dados gerados da fonte: clsn por frame (clsn1/
 * clsn2 do AIR, blobs int16 LE com sentinela -32767, secao hit primeiro,
 * hurt depois), dmg/flags por estado (hitdef do CNS), hitstop
 * (pausetime[0]), hit/guard push (ground/guard.velocity[0]) e life
 * (data.life). Semantica do contrato do wrapper
 * (analysis/anim_time_contract.py:14): hit = primeiro tick em que a Clsn1
 * do quadro ativo sobrepoe a hurtbox do defensor, uma vez por instancia de
 * golpe (hit_done, resetado em set_role).
 * Aproximacoes DECLARADAS (rom de diagnostica, NAO execucao CNS):
 *  - facing (para onde o ator aponta) e DERIVADO da ordem de x no chao, como
 *    o MUGEN refaz a face quando no estado ground; no ar a face e congelada
 *    (permite cross-up). Nao ha no pacote controle de face por estado CNS,
 *    entao o refresh e por posicao, nao por `face` do state;
 *  - guarda = estado defensor S_BLOCKABLE, sem teste de crossup por botao;
 *  - push aplicado uma vez por evento, em px (cd->hit_push/cd->guard_push),
 *    na direcao de afastamento do defensor em relacao ao atacante;
 *  - hitstop (cd->hitstop) congela o avanco dos dois atores;
 *  - HITSTUN com animacao de dano NAO implementado: o tempo do hitdef nao
 *    esta no pacote versus-cut e os estados de hit pertencem ao conjunto
 *    common1.cns bloqueado (fronteira registrada, nao inventado);
 *  - pusher no chao usa soma das larguras frontais convertidas do pacote;
 *    sem Width/PlayerPush CNS, largura traseira ou push no ar, e uma
 *    aproximacao registrada, nao equivalencia completa com a fonte.
 * Render: o versus-cut guarda as duas faces em patterns distintos. O cache
 * seleciona os bytes e metadados da face residente; enquanto outra face
 * esta pendente, a logica e o contato ainda podem estar adiante da imagem.
 * Coordenadas MUGEN cruas: x positivo = para frente (na direcao do facing),
 * y negativo = para cima (convencao do AIR no pacote), origem nos pes do
 * ator (NAO o AXIS do sprite; AXIS e so deslocamento de desenho).
 * Conversao a tela aqui; sem float, sem malloc (AGENTS.md). */

#define CLSN_SENT     (-32767)

typedef struct { signed int x1, y1, x2, y2; } MugenRect;
typedef struct { signed int l, t, r, b; } ScreenRect;

static signed int clsn_i(const unsigned char *c, unsigned char k) {
    return (signed int)((unsigned int)c[2u * k] |
                        ((unsigned int)c[2u * k + 1u] << 8));
}
/* cursor da secao hurt: pula a secao hit ate a sentinela e avanca 1. */
static unsigned char clsn_hurt_start(const unsigned char *c) {
    unsigned char k = 0u;
    while (clsn_i(c, k) != CLSN_SENT) k += 4u;
    return (unsigned char)(k + 1u);
}
/* le a caixa de indice idx da secao comeca no cursor k; 0 na sentinela. */
static unsigned char clsn_box_at(const unsigned char *c, unsigned char k,
                                 unsigned char idx, MugenRect *m) {
    unsigned char i = 0u;
    for (;;) {
        signed int v = clsn_i(c, k);
        if (v == CLSN_SENT) return 0u;
        if (i == idx) {
            m->x1 = v;
            m->y1 = clsn_i(c, (unsigned char)(k + 1u));
            m->x2 = clsn_i(c, (unsigned char)(k + 2u));
            m->y2 = clsn_i(c, (unsigned char)(k + 3u));
            return 1u;
        }
        k = (unsigned char)(k + 4u);
        i++;
    }
}
static void mugen_to_screen(const MugenRect *m, unsigned char s, ScreenRect *o) {
    signed int fx = (signed int)(fighter[s].x >> 8);
    signed int fy = (signed int)DIAG_FLOOR - (signed int)(fighter[s].y >> 8);
    if (!fighter[s].face) { o->l = fx + m->x1; o->r = fx + m->x2; }
    else                  { o->l = fx - m->x2; o->r = fx - m->x1; }
    o->t = fy + m->y1;   /* y do AIR e negativo para cima: y1 e o topo */
    o->b = fy + m->y2;
}
static unsigned char rects_overlap(const ScreenRect *a, const ScreenRect *b) {
    return (unsigned char)(a->l <= b->r && b->l <= a->r &&
                           a->t <= b->b && b->t <= a->b);
}
/* alguma caixa da secao `a_sec` (0=hit,1=hurt) de fa sobreposta a alguma
 * hurtbox de fb? */
static unsigned char boxes_overlap(const Frame *fa, unsigned char sa,
                                   unsigned char a_sec,
                                   const Frame *fb, unsigned char sb) {
    MugenRect ma, mb;
    ScreenRect ra, rb;
    unsigned char ka, kb, ia, ib;
    if (!fa->clsn || !fb->clsn) return 0u;
    ka = a_sec ? clsn_hurt_start(fa->clsn) : 0u;
    kb = clsn_hurt_start(fb->clsn);
    for (ia = 0u; clsn_box_at(fa->clsn, ka, ia, &ma); ia++) {
        mugen_to_screen(&ma, sa, &ra);
        for (ib = 0u; clsn_box_at(fb->clsn, kb, ib, &mb); ib++) {
            mugen_to_screen(&mb, sb, &rb);
            if (rects_overlap(&ra, &rb)) return 1u;
        }
    }
    return 0u;
}

static void combat_step(const Frame *fn0, const Frame *fn1) {
    unsigned char a;
    for (a = 0u; a < 2u; a++) {
        unsigned char d = (unsigned char)(1u - a);
        const CharacterData *cd = &characters[a];
        const StateDef *st = &cd->states[fighter[a].role];
        const Frame *fa = a ? fn1 : fn0;
        const Frame *fd = a ? fn0 : fn1;
        unsigned char push;
        if (fighter[a].hit_done) continue;
        if (!(st->flags & S_HIT)) continue;
        if (fighter[d].life == 0u) continue;
        probe_clsn_checks++;
        if (!boxes_overlap(fa, a, 0u, fd, d)) continue;
        fighter[a].hit_done = 1u;
        if (cd->hitstop) {
            fighter[a].stop = cd->hitstop;
            fighter[d].stop = cd->hitstop;
        }
        if (characters[d].states[fighter[d].role].flags & S_BLOCKABLE) {
            probe_guard_events++;
            push = cd->guard_push;
        } else {
            unsigned int taken;
            probe_hit_events++;
            taken = (unsigned int)st->dmg;
            if (taken > fighter[d].life) taken = fighter[d].life;
            fighter[d].life = (unsigned short)(fighter[d].life - taken);
            if (a == 0u) probe_damage_p2 += taken;
            else         probe_damage_p1 += taken;
            if (fighter[d].life == 0u) {
                probe_ko_events++;
                set_role(d, ST_KO);
                /* wave-5b: reset dos objetos no KO. O anel do lado derrotado e
                 * limpo para que um pulso de tier vivo nao sobreviva ao papel
                 * terminal e acorde o ator no frame seguinte. */
                input_flush(d);
            }
            push = cd->hit_push;
        }
        {
            /* afastar o defensor do atacante (ordem de x), nao o lado fixo:
             * com cross-up o atacante pode estar a direita. */
            move_x(d, (fighter[d].x >= fighter[a].x) ?
                         ((signed int)push << 8)
                         : -((signed int)push << 8));
        }
    }
    probe_life_p1 = fighter[0].life;
    probe_life_p2 = fighter[1].life;
}

/* Facing por frame, na ordem do chao: quem esta a esquerda aponta para a
 * direita e vice-versa. No ar a face permanece (cross-up possivel). Empate de
 * x (os dois na mesma borda, empurrados pelo pusher) nao vira virada: sem essa
 * guarda a face oscilaria todo frame e o flip deixaria de ser prova de
 * mecanica. Conta apenas flancos de virada, para provar que o mecanismo
 * operou na ROM. */
static void facing_step(void) {
    unsigned char s;
    for (s = 0u; s < 2u; s++) {
        unsigned char want;
        if (fighter[s].y) continue;
        if (fighter[1u - s].x == fighter[s].x) continue;
        want = (unsigned char)(fighter[1u - s].x < fighter[s].x);
        if (want != fighter[s].face) {
            fighter[s].face = want;
            probe_face_flips++;
        }
    }
}

/* Aproximacao limitada: no chao, a largura frontal convertida dos dois
 * personagens define a separacao. A ordem foi registrada antes do movimento,
 * portanto um passo que atravesse o outro ator nao inverte essa ordem. No ar
 * nao ha push, permitindo cross-up. Width/PlayerPush CNS e largura traseira
 * ainda nao sao executados; nao declarar equivalencia completa de MUGEN. */
static void pusher_step(unsigned char left_side) {
    unsigned char right_side;
    unsigned int lx, rx, lw, rw, span, need, center, half, target;

    if (fighter[0].y || fighter[1].y) return;
    if (left_side > 1u) { probe_push_invalid_geometry++; return; }
    right_side = (unsigned char)(left_side ^ 1u);
    lx = fighter[left_side].x;
    rx = fighter[right_side].x;
    lw = characters[left_side].ground_front_q8;
    rw = characters[right_side].ground_front_q8;
    span = (unsigned int)(DIAG_X_MAX - DIAG_X_MIN);
    if (lx < DIAG_X_MIN || lx > DIAG_X_MAX || rx < DIAG_X_MIN ||
        rx > DIAG_X_MAX || !lw || !rw || lw > span || rw > span - lw) {
        probe_push_invalid_geometry++;
        return;
    }
    need = (unsigned int)(lw + rw);
    if (lx <= rx && rx - lx >= need) return;

    /* floor((lx+rx)/2) sem soma de Q8.8 que transborde o int16 do Z80. */
    center = (unsigned int)((lx >> 1) + (rx >> 1) + (lx & rx & 1u));
    half = (unsigned int)(need >> 1);
    target = center > half ? (unsigned int)(center - half) : 0u;
    if (target < DIAG_X_MIN) target = DIAG_X_MIN;
    if (target > DIAG_X_MAX - need) target = DIAG_X_MAX - need;
    fighter[left_side].x = target;
    fighter[right_side].x = (unsigned int)(target + need);
    probe_pusher_frames++;
}

/* ---------------- wave-5b: estagio de input ---------------- */
/* Side 0 le o pad fisico (PORT_A); side 1 recebe niveis de pad da IA, funcao
 * pura de (frame, face). Os dois percorrem o MESMO caminho: input_tick ->
 * maquina de tier -> anel de 16 amostras -> tabela de comandos do lutador. A
 * unica saida aplicada aqui e um PAPEL via set_role() — nem dano, nem posicao,
 * nem animacao sao escritos por esta camada, o que faz da prova causal
 * entrada->papel->pose->dano valer para humano e IA ao mesmo tempo.
 *
 * Vista e resultado estaticos: fight_input_step recebe ponteiros, e o SDCC
 * endereca locais apontados via ix (o custo do anel ja medido em
 * diag_step_attr.py veio dai); serem estaticos mantem o acesso direto. */
static FightView fi_view;
static FightResult fi_res;
static FightAIClock ai_clock;

static void input_stage(void) {
    unsigned char side;
    unsigned int keys = SMS_getKeysStatus();
    probe_keys_raw = keys;

    for (side = 0u; side < 2u; side++) {
        const CharacterData *cd = &characters[side];
        unsigned char levels;
        unsigned char beat = 0u;

        if (side == 0u) {
            /* PORT_A_KEY_UP..KEY_2 = 0x0001..0x0020 caem na mesma posicao dos
             * K_* do anel (autoridade #8). A mascara fecha START(=KEY_1),
             * RESET 0x1000, SLOT 0x2000 e os TH de light gun, que nao sao pad. */
            levels = (unsigned char)(keys & 0x3Fu);
        } else {
            fight_ai_clock_advance(&ai_clock, (unsigned short)frames);
            beat = ai_clock.beat;
            levels = fight_input_ai_levels_clock(&ai_clock, fighter[1u].face);
            probe_ai_beat = beat;
        }

        fi_view.role       = fighter[side].role;
        fi_view.done       = fighter[side].done;
        fi_view.on_ground  = (unsigned char)(fighter[side].y == 0u);
        fi_view.alive      = (unsigned char)(fighter[side].life != 0u);
        fi_view.face       = fighter[side].face;

        fight_input_step(side, cd, &fi_view, levels, &fi_res);

        if (side == 0u) {
            probe_levels_p1 = levels;
            probe_input_frames_p1++;
        } else {
            probe_levels_p2 = levels;
            probe_input_frames_p2++;
        }

        /* Contabilidade de rota: indice do padrao que casou, e quantos casaram
         * sem golpe (o pacote tem SPECIAL sem rota e LP/LK sem tabela). */
        if (fi_res.cmd_index != FI_CMD_NONE) {
            if (side == 0u) {
                probe_cmd_last_index_p1 = fi_res.cmd_index;
                if (fi_res.unrouted) probe_cmd_unrouted_p1++;
                else                 probe_cmd_hits_p1++;
            } else {
                probe_cmd_last_index_p2 = fi_res.cmd_index;
                if (fi_res.unrouted) probe_cmd_unrouted_p2++;
                else                 probe_cmd_hits_p2++;
            }
        }

        if (fi_res.role != FI_ROLE_NONE) {
            set_role(side, fi_res.role);
            if (side == 0u) probe_role_changes_p1++;
            else            probe_role_changes_p2++;
        }
    }
}

/* ---------------- Lote B: helpers do laco de perfil unico -----------------
 * PROFILE=0 (diagnostico) e PROFILE=1 (producao) chamam as MESMAS funcoes;
 * muda apenas a ORDEM no laco — nao ha duas engines. Nenhum helper escreve
 * VDP: os commits (stream de patterns + SMS_copySpritestoSAT) ficam com o
 * laco, que no perfil de producao os mantem dentro do VBlank pedido. */

/* Contabilidade de VBlank por iteracao (telemetria wave-4). Com telemetria
 * desligada nao ha hook de ISR nem contador: a chamada e no-op de custo zero
 * provado pelo pre-processador. */
#if LUTA_DIAG_TELEMETRY
static void vblank_account(void) {
    probe_vblank_total++;
    {
        unsigned int d = probe_vblank_total - probe_vbl_prev_iter;
        probe_vbl_prev_iter = probe_vblank_total;
        if (d > probe_vbl_per_iter_max)
            probe_vbl_per_iter_max = d;
    }
}
#else
#define vblank_account() ((void)0)
#endif

/* Uma passada de logica: face -> input/papel -> atores -> combate -> pusher ->
 * request_pose. Mesma sequencia da wave-5b (v031), so reancorada fora do
 * wrap de stream (o stream virou passo explicito do laco). */
static void logic_tick(const Frame *fn[2], unsigned int poses_req[2]) {
    unsigned char side;
    unsigned char left_before = (fighter[0].x <= fighter[1].x) ? 0u : 1u;
#if LUTA_DIAG_TELEMETRY
    unsigned char t0 = probe_vbl_tick;
#endif
    probe_phase = 1u;   /* CPU/logica do frame (avanco de atores) */
    if ((frames % SCRIPT_STEP_FRAMES) == 0u) {
        /* wave-4e mediu step em 0 flancos em 864 iteracoes; na 4f o
         * slot DA-DB foi reocupado por atores+pose e o step nao e mais
         * instrumentado.
         * wave-5b: o SCRIPT de papéis saiu do laço — quem decide papel
         * é o estágio de input (pad + IA pelo mesmo anel). O `step` e
         * mantido só como janela de pacing/SMRT (a mesma divisão de 150
         * frames dos selos 4e..5a), sem nenhum set_role. */
        unsigned int step = frames / SCRIPT_STEP_FRAMES;
        probe_step = step;
        /* Snapshot SMRT nos limites de passo: 5 leituras u16 por 150
         * frames, nao por VBlank. */
        probe_b_maxline = CLAMP255(probe_max_line);
        probe_b_evict = CLAMP255(probe_evict_events);
        probe_b_omitted = CLAMP255(probe_omitted_sat);
        probe_b_stall = CLAMP255(probe_stall_frames);
        probe_b_uploaded = CLAMP255(probe_uploaded_pairs);
    }
    /* M2 (wave-5a): face derivada da ordem de x antes do avanco, para
     * que movimento, colisao e render usem a mesma orientacao no
     * frame. */
    facing_step();
    /* wave-5b: o estagio de input vem DEPOIS da face (o anel normaliza
     * tras/frente pela facing e a IA posiciona o movimento) e ANTES do
     * avanco, para que o papel decidido neste tick ja mova, colida e
     * renderize no mesmo frame — entrada->papel->pose->dano sem
     * atraso artificial. */
    input_stage();
    {   /* wave-4g-1: DA-DB = advance_actor apenas; request_pose/alloc fica
         * fora do wrap (ainda na logica). Lote B: o stream saiu deste wrap
         * (passo explicito do laco); a telemetria fica logica-sem-stream
         * (~0 medida na wave-4b). */
#if LUTA_DIAG_TELEMETRY
        unsigned char t2 = probe_vbl_tick;
        for (side = 0; side < 2u; side++)
            advance_actor(side, &poses_req[side], &fn[side]);
        probe_reg_actors_edges += (unsigned char)(probe_vbl_tick - t2);
#else
        for (side = 0; side < 2u; side++)
            advance_actor(side, &poses_req[side], &fn[side]);
#endif
    }
    /* M2 (wave-5a): resolucao de combate e separacao de corpos sobre
     * os frames logicos deste frame (frames_now), que e o quadro
     * visivel quando probe_stall_frames == 0. */
    combat_step(fn[0], fn[1]);
    pusher_step(left_before);
    for (side = 0; side < 2u; side++) {
        if (poses_req[side] != 0xFFFFu) {
            if (poses_req[side] < VERSUS_POSE_COUNT)
                request_pose(side, poses_req[side],
                             (unsigned char)(versus_poses[poses_req[side]].size >> 6),
                             fn[side], fighter[side].face);
            else {
                cache_invalidate(&pending[side]);
                probe_bad_pose_ref++;
            }
        }
    }
#if LUTA_DIAG_TELEMETRY
    probe_reg_logic_edges += (unsigned char)(probe_vbl_tick - t0);
#endif
}

/* Construcao dos metasprites SOMENTE em RAM (shadow SAT + contadores). O
 * commit VDP fica com SMS_copySpritestoSAT, passo explicito do laco, para o
 * perfil de producao commitar so no VBlank. */
static void sprites_build(const Frame *fn[2], const unsigned int poses_req[2]) {
    unsigned char side;
#if LUTA_DIAG_TELEMETRY
    unsigned char i;
    unsigned char t0 = probe_vbl_tick;
#endif
    probe_phase = 4u;       /* preparacao de metasprites em RAM */
    SMS_initSprites();
#if LUTA_DIAG_TELEMETRY
    probe_reg_frame_edges += (unsigned char)(probe_vbl_tick - t0);
    t0 = probe_vbl_tick;
    /* wave-4j: o clear de line_diff (160 stores/frame) e telemetria e saiu
     * do wrap de emissao; emite-se agora caminhada+add apenas, e o clear
     * conta no slot de telemetria DA-DB junto da varredura. */
    for (i = 0; i < DIAG_FLOOR; i++) line_diff[i] = 0;
    probe_reg_actors_edges += (unsigned char)(probe_vbl_tick - t0);
    t0 = probe_vbl_tick;
#endif
    for (side = 0; side < 2u; side++) {
#if LUTA_PROFILE
        /* Producao: exibe a pose RESIDENTE (imagem valida nunca e' omitida).
         * A espera (pedida != residente) e' medida por lado; a apresentacao
         * distingue-se da submissao quando a SAT rejeita peca do lado. */
        unsigned int submitted = 0xFFFFu;
        unsigned int om_before =
            (side == 0u) ? probe_sat_om_p1 : probe_sat_om_p2;
        unsigned int om_after;
        if (current[side].frame) {
            submitted = current[side].pose_global;
            emit_frame(side, current[side].frame);
        }
        om_after = (side == 0u) ? probe_sat_om_p1 : probe_sat_om_p2;
        if (side == 0u) {
            probe_submit_p1 = submitted;
            probe_submit_face_p1 = (submitted != 0xFFFFu) ? current[side].face : 0xFFu;
            probe_present_p1 = (submitted != 0xFFFFu && om_after == om_before)
                                   ? submitted : 0xFFFFu;
        } else {
            probe_submit_p2 = submitted;
            probe_submit_face_p2 = (submitted != 0xFFFFu) ? current[side].face : 0xFFu;
            probe_present_p2 = (submitted != 0xFFFFu && om_after == om_before)
                                   ? submitted : 0xFFFFu;
        }
        if (current[side].pose_global != poses_req[side] ||
            current[side].face != fighter[side].face) {
            probe_stall_frames++;   /* pedida != residente: espera medida */
            if (side == 0u) probe_wait_p1++;
            else            probe_wait_p2++;
        }
#else
        /* Diagnostico (controle): gate historico — so desenha quando exibida ==
         * pedida; caso contrario o ator inteiro e' omitido (stall). */
        if (current[side].pose_global == poses_req[side] &&
            current[side].face == fighter[side].face)
            emit_frame(side, fn[side]);
        else
            probe_stall_frames++;   /* pedida != exibida neste frame */
#endif
    }
    probe_disp_p1 = current[0].pose_global;
    probe_disp_p2 = current[1].pose_global;
#if LUTA_PROFILE
    probe_desired_p1 = poses_req[0];
    probe_desired_p2 = poses_req[1];
    probe_resident_p1 = current[0].pose_global;
    probe_resident_p2 = current[1].pose_global;
    probe_desired_face_p1 = fighter[0].face;
    probe_desired_face_p2 = fighter[1].face;
    probe_resident_face_p1 = current[0].frame ? current[0].face : 0xFFu;
    probe_resident_face_p2 = current[1].frame ? current[1].face : 0xFFu;
#endif
#if LUTA_DIAG_TELEMETRY
    probe_reg_frame_edges += (unsigned char)(probe_vbl_tick - t0);
    /* wave-4j: particao completa sem dupla contagem — a varredura e o clear
     * vao inteiros para o slot de telemetria DA-DB e o wrap de pool (DE-DF)
     * comeca DEPOIS da varredura. */
    {
        unsigned char acc = 0u;
        unsigned char l = 0u;
        unsigned char mx = 0u;
        unsigned char ts = probe_vbl_tick;
        for (; l < (unsigned char)DIAG_FLOOR; l++) {
            acc += line_diff[l];
            if (acc >= 9u)
                probe_over8_events++;
            if (acc > mx)
                mx = acc;
        }
        probe_max_line = mx;
        probe_reg_actors_edges += (unsigned char)(probe_vbl_tick - ts);
    }
    t0 = probe_vbl_tick;
#endif
    /* Contadores proprios (nao ler volatile): evita 16 probes u16 lidas
     * por VBlank no laudo de pacing. */
    {
        unsigned char used = used_pairs();
        if ((unsigned int)used > probe_used_pairs_max)
            probe_used_pairs_max = used;
        if ((unsigned int)(POOL_PAIRS - used) < probe_free_pairs_min)
            probe_free_pairs_min = POOL_PAIRS - used;
        /* Lote B.2: pico de backlog de fila (pares pendentes ainda nao
         * subidos); a recuperacao de fila e' a substituicao/completude. */
        {
            unsigned int backlog = 0u;
            if (pending[0].pose_global != 0xFFFFu)
                backlog += (unsigned int)(pending[0].n_pairs -
                                          pending[0].loaded_pairs);
            if (pending[1].pose_global != 0xFFFFu)
                backlog += (unsigned int)(pending[1].n_pairs -
                                          pending[1].loaded_pairs);
            if (backlog > probe_backlog_max)
                probe_backlog_max = backlog;
        }
        probe_smrt_frame = frames;
        probe_b_step = CLAMP255(frames / SCRIPT_STEP_FRAMES);
        probe_b_used = used;
        probe_b_free = (unsigned char)(POOL_PAIRS - used);
        /* wave-5a: geometria atual dos atores em px (cotejo com o
         * simulador offline; 4 escritas u16 por frame). */
        probe_x_p1 = fighter[0].x >> 8;
        probe_x_p2 = fighter[1].x >> 8;
        probe_face_p1 = fighter[0].face;
        probe_face_p2 = fighter[1].face;
        /* estaveis desde o boot */
        probe_b_bootfit = (unsigned char)probe_boot_p2_fit;
        probe_b_role_p1 = fighter[0].role;
    }
#if LUTA_DIAG_TELEMETRY
    /* Lote B: a copia-SAT saiu deste bloco (passo explicito do laco nos dois
     * perfis); DE-DF mede agora so os espelhos/pool. */
    probe_reg_pool_edges += (unsigned char)(probe_vbl_tick - t0);
#endif
}

/* Amostra final de VDP (fase 3): VCounter ao fim de TODO o trabalho do frame
 * (no perfil de producao, da fatia de commits VDP). >=0xC0 = fechou dentro do
 * VBlank; <0xC0 = derramou no proximo display ativo. Janela autonoma de 3000
 * frames de atracao; depois do selo as grandezas ficam congeladas para uma
 * unica leitura do DAP. */
static void worst_sample(void) {
    unsigned char vcnt = SMS_VCounterPort;
    probe_phase = 3u;
    if (probe_frame <= WORST_FRAME_WINDOW) {
        probe_vline = vcnt;
        if (vcnt < 0xC0u)
            probe_vovf++;   /* word: nao satura em 255 */
        else if (vcnt > probe_vbl_exit_max)
            probe_vbl_exit_max = vcnt;  /* pior saida AINDA no VBlank */
        if (vcnt < probe_vline_min)
            probe_vline_min = vcnt;
    } else if (probe_worst_done == 0u) {
        probe_worst_done = 1u;
    }
}

void main(void) {
    const Frame *boot_frame;
    const Frame *frames_now[2];
    unsigned int poses_req[2];
    unsigned int pose_g;
    unsigned int boot_p1_size = 0u;
    unsigned int checked_offset;
    unsigned char i;

    SMS_displayOff();
    SMS_init();
    SMS_VRAMmemsetW(0x0000u, 0x0000u, 16384u);
    SMS_setSpriteMode(SPRITEMODE_TALL);
    SMS_useFirstHalfTilesforSprites(1);
    SMS_setBGPaletteColor(0, 0x00);   /* fundo solido preto, sem cenario */
    SMS_loadSpritePalette(versus_sprite_palette);
    /* Tile 255 mora em 0x1FE0, dentro do pool que o streaming sobrescreve.
     * Tile 256 foi zerado acima e fica na segunda metade da VRAM; a PNT
     * continua apontando para um pattern vazio mesmo quando os atores mudam. */
    SMS_VRAMmemsetW(0x3800u, SOLID_BG_TILE, 1536u);

    /* L009-L134: sondas __at nao sao inicializadas pelo crt0; sem zerar,
     * todo contador parte de lixo da RAM e a evidencia nasce ilegivel.
     * wave-5b: o corredor baixo crescia ate 0xC85F (48 palavras) — o limite
     * era a extensao real do bloco, nao um numero redondo. Lote B.2: o bloco
     * cresceu com as sondas da politica (ate 0xC885); zerar ate 0xC8D1 cobre
     * o corredor declarado sem tocar nos bytes 0xC8D2+ (inicializados
     * individualmente abaixo). */
    {
        volatile unsigned int *p = (volatile unsigned int *)0xC800u;
        unsigned char z;
        for (z = 0u; z < 105u; z++) p[z] = 0u;
    }
    probe_magic = 0x5232u;
    probe_schema = 1u;
    probe_smrt_magic[0] = 'S';
    probe_smrt_magic[1] = 'M';
    probe_smrt_magic[2] = 'R';
    probe_smrt_magic[3] = 'T';
    probe_smrt_schema = 1u;
    probe_smrt_frame = 0u;
    /* worst-frame: __at nao e inicializado pelo crt0 (L009); vline_min parte
     * de 0xFF porque e rastreador de MINIMO na janela de 3000 frames. */
    probe_vovf = 0u;
    probe_vline = 0u;
    probe_phase = 0u;
    probe_worst_done = 0u;
    probe_vline_min = 0xFFu;
    /* atribuicao regional: __at nao e inicializado pelo crt0 (L009);
     * o hook da ISR so e instalado com as somas ja zeradas. */
#if LUTA_DIAG_TELEMETRY
    probe_vbl_tick = 0u;
    probe_reg_logic_edges = 0u;
    probe_reg_actors_edges = 0u;
    probe_reg_frame_edges = 0u;
    probe_reg_pool_edges = 0u;
    SMS_setFrameInterruptHandler(probe_vbl_isr);
#else
    /* wave-4l: sem telemetria por frame. Um RMW unico em cada sonda __at que
     * deixou de ser escrita no laco — nada no caminho quente, mas mantem o
     * corredor 0xC820/0xC8D7..0xC8DF presente no .map para o
     * audit_probe_corridor (SDCC descarta simbolos nunca referenciados). */
    probe_vbl_tick = probe_vbl_tick;
    probe_reg_logic_edges = probe_reg_logic_edges;
    probe_reg_actors_edges = probe_reg_actors_edges;
    probe_reg_frame_edges = probe_reg_frame_edges;
    probe_reg_pool_edges = probe_reg_pool_edges;
    probe_vblank_total = probe_vblank_total;
    probe_vbl_prev_iter = probe_vbl_prev_iter;
    probe_vbl_per_iter_max = probe_vbl_per_iter_max;
#endif
    current[0].pose_global = 0xFFFFu;
    current[1].pose_global = 0xFFFFu;
    pending[0].pose_global = 0xFFFFu;
    pending[1].pose_global = 0xFFFFu;
    fighter[0].x = 96u * 256u;
    fighter[1].x = 160u * 256u;
    fighter[0].face = 0u;   /* layout inicial: p1 a esquerda, aponta p/ direita */
    fighter[1].face = 1u;
    fighter[0].life = characters[0].max_life;
    fighter[1].life = characters[1].max_life;
    probe_life_p1 = fighter[0].life;
    probe_life_p2 = fighter[1].life;
    set_role(0, ST_IDLE);
    set_role(1, ST_IDLE);

    /* wave-5b: o anel e a maquina de tier dos dois lados comecam limpos; sem
     * input_init() a RAM nao inicializada dos buffers estaticos deixaria
     * amostras e contadores de pulso vivos no primeiro frame. */
    input_init();
    fight_ai_clock_reset(&ai_clock);
    /* Contabilidade de rota derivada DOS DADOS (nenhum nome de lutador):
     * quantos padroes chegaram a tabela do runtime e quais codigos de golpe
     * ficaram sem rota neste pacote. */
    probe_cmd_route_count = characters[0].command_count;
    probe_cmd_unrouted_mask = fight_unrouted_mask(&characters[0]);
    probe_tier_t = INPUT_TIER_T;

    /* boot: P1 idle em base 0; depois TENTA P2 idle com alocacao crua (sem
     * evict) — probe_boot_p2_fit registra o resultado real. pending e
     * preenchido e stream_pending(upload_all) promove current internamente;
     * copiar pending (ja esvaziado) de volta em current deixava os pares
     * orfaos no bitmap e dispensava o upload do boot. */
    boot_frame = &characters[0].anims[characters[0].states[ST_IDLE].anim].frames[0];
    pose_g = (unsigned int)characters[0].pose_base + boot_frame->pose;
    if (pose_g >= VERSUS_POSE_COUNT ||
        !pose_facing_offset(&versus_poses[pose_g], 0u, fighter[0].face, &checked_offset)) {
        probe_bad_pose_ref++;
    } else {
        boot_p1_size = versus_poses[pose_g].size;
        i = (unsigned char)(boot_p1_size >> 6);
        if (alloc_contiguous(i, &pending[0].base_pair)) {
            pending[0].pose_global = pose_g;
            pending[0].n_pairs = i;
            pending[0].loaded_pairs = 0;
            pending[0].frame = boot_frame;
            pending[0].face = fighter[0].face;
            stream_pending(0, 0xFFu);
        }
    }
    boot_frame = &characters[1].anims[characters[1].states[ST_IDLE].anim].frames[0];
    pose_g = (unsigned int)characters[1].pose_base + boot_frame->pose;
    if (pose_g >= VERSUS_POSE_COUNT ||
        !pose_facing_offset(&versus_poses[pose_g], 1u, fighter[1].face, &checked_offset)) {
        probe_bad_pose_ref++;
        probe_boot_p2_fit = 0u;
    } else {
        i = (unsigned char)(versus_poses[pose_g].size >> 6);
        if (alloc_contiguous(i, &pending[1].base_pair)) {
            pending[1].pose_global = pose_g;
            pending[1].n_pairs = i;
            pending[1].loaded_pairs = 0;
            pending[1].frame = boot_frame;
            pending[1].face = fighter[1].face;
            stream_pending(1, 0xFFu);
            probe_boot_p2_fit = (current[1].pose_global == pose_g);
        } else {
            unsigned int total = boot_p1_size + versus_poses[pose_g].size;
            probe_boot_p2_fit = 0u;
            probe_boot_overflow_b = total > 8192u ? total - 8192u : 0u;
        }
    }
    probe_used_pairs_max = used_pairs();
    probe_free_pairs_min = (unsigned int)(POOL_PAIRS - probe_used_pairs_max);
    SMS_displayOn();

#if LUTA_PROFILE
    /* PRODUCAO (Lote B): logica/cache/construcao de metasprites no display
     * ativo; so os commits VDP (upload de patterns + copia da SAT) ficam no
     * VBlank pedido, com a janela registrada (probe_phase 2; vline/vovf ao
     * fim). As MESMAS funcoes do diagnostico; muda a ordem. A amostra de pad
     * da ISR e consumida pela logica do tick seguinte — profundidade de
     * pipeline de 1 frame (declarada no TDD). */
    for (;;) {
        frames++;
        probe_frame = frames;
        logic_tick(frames_now, poses_req);
        sprites_build(frames_now, poses_req);

        /* Commits VDP do frame, so aqui, dentro do VBlank pedido. */
        SMS_waitForVBlank();
        vblank_account();
        /* Lote B.2: janela registrada (comeco = VCounter ao entrar no work;
         * fim = probe_vline/probe_vbl_exit_max em worst_sample) e chunk
         * orcado POR LADO por VBlank (servico garantido a cada ator). */
        probe_phase = 2u;
        probe_vbl_entry = SMS_VCounterPort;
        {
            unsigned int moved = stream_pending(0u, UPLOAD_CHUNK_PAIRS);
            moved += stream_pending(1u, UPLOAD_CHUNK_PAIRS);
            if (moved > probe_upload_maxvbl)
                probe_upload_maxvbl = moved;
        }
        SMS_copySpritestoSAT();
        worst_sample();
    }
#else
    /* DIAGNOSTICO (congelado, v031): ordem historica do baseline — upload e
     * logica DEPOIS do waitForVBlank, SAT ao fim da preparacao de emissao.
     * Instrumento com selo causal fechado; a ordem nao se altera. */
    for (;;) {
        SMS_waitForVBlank();
        frames++;
        probe_frame = frames;
        vblank_account();
        /* controle: teto historico de 1 par de 64 B por VBlank, round-robin. */
        probe_phase = 2u;       /* trabalho de VBlank comeca no upload */
        stream_pending((unsigned char)(frames & 1u), 1u);
        logic_tick(frames_now, poses_req);
        sprites_build(frames_now, poses_req);
        SMS_copySpritestoSAT();
        worst_sample();
    }
#endif
}
