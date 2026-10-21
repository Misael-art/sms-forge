// main.c — pulso_de_cristal (M3: FSM das 4 cenas + probe worst-frame + arbitração)
//
// Arco dirigido do GDD: TITLE → DAWN → STORM → ECHO → CRÉDITOS → TITLE, com
// PAUSE→SILENT em qualquer ato. Cada aresta segue doc/17-state-transition-
// contract.md (owners, teardown, trabalho VDP); timings e tabelas de "quando"
// vem de doc/16-storyboard.md + inc/scene_tables.h (derivado da partitura —
// dado, não runtime).
//
// ARTE: esta build usa PLACEHOLDERS procedurais em quarentena (aprovação
// humana 2026-10-12: "prossiga" sobre o ramo FSM-primeiro; canal de concept
// bloqueado — out/logs/generation_channel_decision.json Ramo C). Nenhum pixel
// daqui sustenta claim de entrega visual; a arte final entra por contrato de
// asset + proveniência, e os tiles T_* serão substituídos pelo tileset autoral.
//
// MODO: determinístico no boot. Se NENHUM botão for pressuposto lido até o
// frame 240, a ROM trava o MODO ATRAÇÃO (exigência de measure_worst_frame.py:
// 3000 frames exercitando o pior caminho — transições, SAT, flash, rolagem)
// e avança sozinha em tempos curtos. Qualquer toque mantém o MODO JOGADOR:
// prompt START só no primeiro loop point (roteiro cena 01).
//
// Autoridade da API: sdk/devkitSMS/SMSlib/SMSlib.h (SMS_getKeysPressed :289,
// SMS_queryPauseRequested :349, SMS_setTileatXY :117, SMS_loadTiles :130,
// SMS_loadBGPalette :251, SMS_loadSpritePalette :252,
// SMS_initSprites/SMS_addSprite/SMS_copySpritestoSAT :188-211 — o copy preenche
// o resto da SAT com 0xD0 'VRAM safe', visto em devkitSMS-upstream/SMSlib/src/
// SMSlib_sprite.c:179-197; SMS_setBGScrollX/Y :50-51, SMS_getVCount :390) e
// PSGlib/PSGlib.h (PSGPlay/PSGPlayNoRepeat/PSGStop/PSGGetStatus :37-49,
// PSGSetMusicVolumeChannelsAttenuation :51, PSGSilenceChannels :62,
// PSGRestoreVolumes :63, PSGSFXPlay/PSGSFXStop/PSGSFXFrame :56-66).
// Restrições sempre ativas: sem float, sem malloc, sem API inventada.

#include "SMSlib.h"
#include "PSGlib.h"
#include "music_title.h"
#include "music_dawn.h"
#include "music_storm.h"
#include "music_eco.h"
#include "sfx_crystal.h"
#include "sfx_crack.h"
#include "sfx_chime.h"
#include "scene_tables.h"
#include "pnt_rows.h"

// ── Probe SMRT (schema 1 aditivo) + worst-frame (molde luta_mugen, L061/L071)
// volatile: sem isto o SDCC apaga a escrita (L009).
volatile unsigned char  __at(0xC9E0) probe_magic0;
volatile unsigned char  __at(0xC9E1) probe_magic1;
volatile unsigned char  __at(0xC9E2) probe_magic2;
volatile unsigned char  __at(0xC9E3) probe_magic3;
volatile unsigned char  __at(0xC9E4) probe_schema;
volatile unsigned char  __at(0xC9EA) probe_vline;      // VCounter após todo o blank
volatile unsigned int   __at(0xC9EB) probe_vovf;       // frames com vline<0xC0
volatile unsigned char  __at(0xC9ED) probe_phase;      // 1 input, 2 blank, 3 amostra, 4 SAT
volatile unsigned char  __at(0xC9EE) probe_worst_done; // janela selada
volatile unsigned char  __at(0xC9D2) probe_vline_min;   // era 0xC7EF: topo da pilha (tecla stack do map)
// ── BASE do corredor = 0xC900, não 0xC700 (2026-10-14, medido no map):
// o contrato canônico dos tools é 0xC7xx e é COMPARTILHADO (arena_nocturna,
// hamoopig, kage_matsuri, laboratorio_01, luta_mugen…). Este projeto tem
// 1,5 K de imagem de templates em RAM; com os +79 B do rework (sementes de
// estilhaços + estado de letreiro/cristal) o _DATA chegou a 0xC7DA e
// _INITIALIZED a 0xC7DF — ou seja, _PSGMusicStatus, _PSGChan*Volume,
// _PSGSFXPointer… caíram DENTRO do corredor 0xC7A9–0xC7D9. Escrita de probe
// corrompendo o estado do PSGlib, e leitura de probe sendo corrompida pelo
// stream (é o que explicava os "contadores impossíveis"). Os endereços
// abaixo são os mesmos offsets do contrato, deslocados de +0x200; os tools
// usam `--probe-base 0xC900` para ler. Margem medida: 0xC990–0xC9F9 livre,
// _DATA termina em 0xC7DB e a pilha afunda só até ~0xDFD6.
// aliasa o bloco F0+ com plausível-falso; D2 livre no contrato do tool
// (LOOP_PROFILE_SEQ só existe se tl_snap existir; este projeto não tem)
volatile unsigned int   __at(0xC9F0) probe_frame;
volatile unsigned char  __at(0xC9F2) probe_track;      // 0 título 1 aurora 2 tempestade 3 eco 4 créditos
volatile unsigned char  __at(0xC9F3) probe_playing;    // stream musical ativo
volatile unsigned char  __at(0xC9F5) probe_attract;    // 1 = atração travada
// O tool lê o estado DAQUI (PROBE_STATE=0xC7F6); era OR de bits em F6 com
// enum em F4 — descasamento de contrato, não coincidência: com o topo da
// pilha sobre F4–FF, só F6 (por baixo da profundidade máxima do ISR) grava
// sem colisão. probe_state = nome do contrato.
volatile unsigned char  __at(0xC9F6) probe_state;      // enum ST_* por frame
// Perfil por fase — contrato PROFILE_ADDRS de measure_worst_frame.py: bytes em
// 0xC7D0/3/4/1 são VCounter amostrado nas bordas da PIOR frame da janela, na
// ordem canônica do tool (wait → hud=escritas → sat → stream). Linhas entre
// duas leituras = diferença em módulo 256 (o contador dá UMA volta por frame;
// nenhum trecho legítimo ocupa duas voltas — soma de correção é armadilha).
volatile unsigned char  __at(0xC9D0) probe_profile_wait;
volatile unsigned char  __at(0xC9D1) probe_profile_stream;
volatile unsigned char  __at(0xC9D3) probe_profile_hud;
volatile unsigned char  __at(0xC9D4) probe_profile_sat;
volatile unsigned char  __at(0xC9D6) probe_vline_spill_max; // maior vline<0xC0
// linhas por etapa na pior frame + origem:
volatile unsigned char  __at(0xC9D7) ph_hud_lines;
volatile unsigned char  __at(0xC9D8) ph_sat_lines;
volatile unsigned char  __at(0xC9D9) ph_stream_lines;
volatile unsigned char  __at(0xC9DA) ph_worst_stage;   // 1 escritas 2 SAT 3 stream
volatile unsigned char  __at(0xC9DB) ph_worst_total;   // linhas wait→stream da pior frame
// histograma de derrame por estado (saturante em 255): qual cena derrama
volatile unsigned char  __at(0xC9C0) spill_title;
volatile unsigned char  __at(0xC9C1) spill_fade_dawn;
volatile unsigned char  __at(0xC9C2) spill_dawn;
volatile unsigned char  __at(0xC9C3) spill_cut_storm;
volatile unsigned char  __at(0xC9C4) spill_storm;
volatile unsigned char  __at(0xC9C5) spill_fade_eco;
volatile unsigned char  __at(0xC9C6) spill_echo;
volatile unsigned char  __at(0xC9C7) spill_credits;
volatile unsigned char  __at(0xC9C8) spill_black;
// decomposição por estado (evidência doc/17 caso 3): pior etapa hud e pior
// etapa sat de cada cena. ph_state_max_total[9]@0xC7DC chegou a existir e
// COLIDIA com probe_magic/schema 0xC7E0–E4 (corrompia o selo) — lição:
// conferência cruzada de endereços __at antes de publicar.
// ph_state_max_sat[9] viveu em 0xC7F7–FF; migrou para B5–BD. A motivação
// original ("o topo da pilha cai no bloco") foi REFUTADA pelos dumps ram.bin
// da sessão sp_stack_check: SP (crt0: 0xDFF0) afunda só até ~0xDFD6 e nunca
// alcança 0xC7xx — nem por endereço direto nem por espelho. A anomalia antiga
// dos bytes F7–FF fica NÃO-atribuída; B5–BD ficou porque o corredor é medido
// vago (stack_sentinel@BF lê 0x5A após 3000+ frames) e as leituras são são.
// Mapa final do round-5 (verificar SEMPRE contra o map BEFORE publicar —
// L089: conferir o map ANTES de publicar — L089 deu de novo: wait_max[9] em A9 invadia B0–B1 do trio spill_st_*):
//   A0–A6 spill_wait_min[7] (estados 1..7) | A7 gs_flash | A8 gs_erase
//   A9–AF spill_wait_max[7] (estados 1..7)
//   B0 spill_st_sat | B1 spill_st_stream | B2 spill_st_tail
//   B3–B4 ph_wr_hud_max (u16) | B5–BD ph_state_max_sat[9]
//   BE spill_st_input | BF stack_sentinel
//   D5 ph_ws_lines (round-9; era gs_crack, banda removida) | D6 spill_max
//   fora do corredor: D2, E4 (magics E0–E4 intocáveis)
// pior etapa hud (input_step + game_step: escritas de nome/paleta/SFX) para
// estados 0..6 (TITLE..ECHO). Vão livre 0xC7C9–CF: 0xC7EA–EC é probe_vline/
// vovf e 0xC7ED+ é fase/done/min/frame do contrato do tool — nenhum endereço
// __at novo pode tocar neles sem quebrar a selagem.
volatile unsigned char  __at(0xC9C9) ph_state_max_hud[7];
// subfases do motor da tempestade (pior frame na janela): 62 linhas medida em
// sat não casa com o custo teórico da SMSlib (~15) — decomponho step/sat/
// cauda nos bytes livres 0xC7DC–DE (DF sobra; E0–E4 são os magic do selo).
volatile unsigned char  __at(0xC9DC) sm_step_lines;
volatile unsigned char  __at(0xC9DD) sm_sat_lines;
volatile unsigned char  __at(0xC9DE) sm_tail_lines;
// atribuição L061 round-2: maxhud só cobre estados 0–6 (C7D0+ ocupado) e o
// stream nunca teve máximo próprio. credits/black (7/8) + stream global +
// estado da pior frame entram nos livres DF e E5–E7 (magics em E0–E4).
volatile unsigned char  __at(0xC9DF) ph_credits_hud;
volatile unsigned char  __at(0xC9E5) ph_black_hud;
volatile unsigned char  __at(0xC9E6) ph_stream_max;
volatile unsigned char  __at(0xC9E7) ph_worst_state;
// desempate 255: se ph_worst_end>=0xC0 o stream é ≥62 linhas (real); se <0xC0
// a frame anterior estourou e o waitForVBlank voltou no blank seguinte.
volatile unsigned char  __at(0xC9E8) ph_worst_end;
// causa por etapa (round-3): qual fase CRUZOU a borda 0xC0 (blank→tela
// ativa) na frame do derrame; tail = waitForVBlank retornou dentro da tela
// ativa — o rabo da frame anterior (fase-3 + storm_preblank) atravessou o
// VBlank e a flag de interrupção ficou travada. ATENÇÃO (reincidência L089
// evitada tarde demais): ED–EF NÃO eram livres — probe_phase/worst_done/
// vline_min vivem lá (linha 53–55). Os quatro agora ocupam a zona morta
// abaixo do bloco de sondas: E9 (livre de verdade) + B0–B2/B3–B4, com folga
// B5–BF para o topo do DATA (medido em 0xC78D); conflito de endereço é o
// detector mentir bonito, não falhar alto.
volatile unsigned char  __at(0xC9E9) spill_st_hud;
volatile unsigned char  __at(0xC9B0) spill_st_sat;
volatile unsigned char  __at(0xC9B1) spill_st_stream;
volatile unsigned char  __at(0xC9B2) spill_st_tail;
// bytes de VRAM escritos por scene_write_rows dentro da fase hud (pior frame
// da janela): diferencia "escrita gigante" (≈1536) de "compute puro".
volatile unsigned int   __at(0xC9B3) ph_wr_hud_max;
static unsigned int     wr_acc;
// round-4 (pós-telemetria de pilha): separar INPUT de GAME na atribuição e
// registrar o cp_wait dos frames de derrame por estado (min+max). min<0xC0
// em um estado com spill>0 = pelo menos uma espera pulada (tail em cascata);
// min>=0xC0 = todos os derrames daquele estado têm espera normal, ou seja a
// própria frame estourou. O par vive em 0xC7A4–BC: maxsat migrou para B5–BD
// e colava no max em BD–C6 (que ainda por cima pegaria spill_fade_eco/echo/
// credits/black do bloco C0+). ph_wr_hud_max é u16 em B3–B4 — nada novo em
// B4 (L089: conferência cruzada ANTES de publicar).
volatile unsigned char  __at(0xC9A0) spill_wait_min[7];  // min cp_wait (estados 1..7, índice=state-1)
volatile unsigned char  __at(0xC9A9) spill_wait_max[7];  // max cp_wait (estados 1..7, índice=state-1)
volatile unsigned char  __at(0xC9B5) ph_state_max_sat[9];  // era F7–FF; corredor medido vago
volatile unsigned char  __at(0xC9BE) spill_st_input;   // input_step cruzou 0xC0
volatile unsigned char  __at(0xC9BF) stack_sentinel;   // 0x5A no boot; ≠5A = pilha afundou no corredor
// bissecção do hud em fsm_storm (round-5, CONCLUÍDA e REMOVIDA): as bandas
// gs_flash/gs_erase/gs_crack/gs_disp/gs_shards/gs_banner/gs_music fecharam o
// gd_max=216 da frame de transição cut_storm→STORM em shards_reset=131 +
// banner_draw=55 + displayOn=1 + escrita=6 + stream=3. O custo delas (ROM e
// ~2 linhas/frame de getVCount) não cabe no bank 0 com a correção dentro;
// a atribuição ficou registrada aqui e no ledger. O que permanece é a banda
// de escrita PURA vs gap:
// F7–F9: provados vagos por dump bruto (ram.bin rounds 4–5) — a teoria de
// pilha neles foi refutada (SP@DFF0 afunda só até ~0xDFD6); leitura cruzada
// com sentinel@BF íntegro. Foram ph_wr_lines/ph_wr_state/ph_wr_gap (bissecção
// round-8/9); removidos com a bissecção concluída — o que responde a pergunta
// hoje é ph_ws_lines (linhas dentro de scene_write_rows) contra gd_max
// (linhas do game_step inteiro) e ph_wr_hud_max (bytes escritos).
// round-9 (tri-seção do gap): gd_max=64 numa frame de 3 linhas de PNT deixava
// 36 linhas órfãs. O `.lst` (ciclos por instrução) dava ~1450 cyc (6 linhas) de
// bookkeeping POR LINHA em scene_write_rows — 19 cyc por acesso `ix` (locais no
// frame de pilha, SDCC sem flag de otimização), o laço `sla/rl` de XYtoADDR
// (5 voltas × 59 + cópias = ~517) e a dança push/pop do pnt_cur_id. Medido
// (peek r9): ph_ws_lines=60 de 64 → scene_write_rows era o dono, e só 4 linhas
// eram FSM/despacho. 11 linhas/linha de PNT ≠ 6 estimadas: o laço de shift é
// pior que a soma dos ciclos anotados, porque cada acesso `ix` a um local de 16
// bits vale 19 e há ~40 deles por linha. Ataque na r10: tabela pnt_row_addr
// (boot), ponteiro para pnt_cur_id em vez de índice, sonda por CALL e não por
// linha.
volatile unsigned char  __at(0xC9D5) ph_ws_lines;   // linhas dentro de scene_write_rows
static unsigned char    ws_lines;                   // acumulador por frame
// máximos globais input (cp_mid−cp_wait) e game (cp_hud−cp_mid), em linhas
// de blank + estado da frame. D8/D9 pertencem a ph_sat/ph_stream_lines do
// contrato do perfil; o canto livre é pós-HEAP start (0xC790+, medido):
volatile unsigned char  __at(0xC990) gd_max;
volatile unsigned char  __at(0xC991) gd_state;
volatile unsigned char  __at(0xC992) gi_max;
volatile unsigned char  __at(0xC993) gi_state;
// contadores de ARESTA (doc/17 testes 2 e 4): a ponte de input nao prova o
// golpe nem a consequencia (workflow passo 4), entao a propia ROM registra.
// Spam de START durante um fade deve deixar cnt_fade_dawn em 1 (nao re-entra);
// cnt_sfx_crystal fora de DAWN deve permanecer 0 (arbitracao L041).
volatile unsigned char  __at(0xC994) cnt_fade_dawn;
volatile unsigned char  __at(0xC995) cnt_cut_storm;
volatile unsigned char  __at(0xC996) cnt_sfx_crystal;
static unsigned char cp_mid;                          // após input_step
// último conjunto de fases ANTES do commit: só o coerente vira perfil 0xC7D0+
static unsigned char cp_wait, cp_hud, cp_sat, cp_stream;
#define WORST_FRAME_WINDOW 3000u

// ── GAME_FSM (doc/17) — um dono por estado mutável: este arquivo.
// enum (não #define): measure_worst_frame.py rotula probe_state pela ordem
// dos nomes ST_* quando o fonte declara o enum.
typedef enum {
    ST_TITLE,      // 0
    ST_FADE_DAWN,  // 1
    ST_DAWN,       // 2
    ST_CUT_STORM,  // 3
    ST_STORM,      // 4
    ST_FADE_ECO,   // 5
    ST_ECHO,       // 6
    ST_CREDITS,    // 7
    ST_BLACK       // 8
} ST_STATE;

static unsigned char state;
static unsigned int t;          // frames no estado corrente
static unsigned char attract;   // travado quando ninguém tocou até f240
static unsigned char touched;
static unsigned char silent;    // PAUSE→SILENT: congela timers+stream, não é estado
static unsigned int prev_keys;
static unsigned char ev_start, ev_select;   // eventos (INPUT_FSM → consumidores)

// TITLE
static unsigned char reveal_row;   // próxima linha a revelar (1 linha/2 frames)
static unsigned char prompt_on;
static unsigned char beat_cell;    // célula 0..3 do medidor
static unsigned char beat_count;
// rampas de áudio (AUDIO_FSM): 0xFF = o stream manda; senão atenuação por-frame
static unsigned char fade_att;
// DAWN
static unsigned char cry_mask;     // bit i = cristal i aceso (dawn→eco, doc/17)
static unsigned char cry_focus;
static unsigned char atk_i;        // cursor em dawn_attacks
static unsigned char ramp_step, ramp_count;   // clareja: 6 passos × 30 f
// STORM
#define SHARDS 24u
static volatile unsigned char crack_flag;
static signed char shard_v[SHARDS], shard_v0[SHARDS];
static unsigned char shard_x[SHARDS], shard_x0[SHARDS];
static unsigned char shard_y[SHARDS], shard_y0[SHARDS];
static unsigned int storm_f;       // posição no loop (mod LOOP_STORM)
static unsigned char hit_i, flash_left, crack_cool;
static unsigned int scroll_acc;
// ECHO / CRÉDITOS / transições
static unsigned char extinguish_i, ext_count;
static unsigned char cred_step, cred_sub;
static unsigned char rewrite_row;    // 0xFF = sem reescrita pendente

// ── Paletas/vocabulário de placeholder (quarentena; códigos 6-bit legítimos)
#define T_DARK   0u
#define T_SKY    1u
#define T_ICE    2u
#define T_LIT    3u
#define T_HILL   4u
#define T_SHARD  5u
#define TILE_BYTES 32u

static const unsigned char pal_title[16] = {
    0x00, 0x15, 0x17, 0x26, 0x3D, 0x3F, 0x16, 0x25,
    0x00, 0x15, 0x17, 0x26, 0x3D, 0x3F, 0x16, 0x25 };
static const unsigned char pal_dawn[16] = {
    0x00, 0x18, 0x1A, 0x27, 0x3C, 0x3F, 0x36, 0x29,
    0x00, 0x18, 0x1A, 0x27, 0x3C, 0x3F, 0x36, 0x29 };
static const unsigned char pal_dawn_ramp[16] = {
    0x00, 0x28, 0x2A, 0x37, 0x3C, 0x3F, 0x3E, 0x39,
    0x00, 0x28, 0x2A, 0x37, 0x3C, 0x3F, 0x3E, 0x39 };
static const unsigned char pal_storm[16] = {
    0x00, 0x02, 0x16, 0x25, 0x08, 0x3F, 0x17, 0x26,
    0x00, 0x02, 0x16, 0x25, 0x08, 0x3F, 0x17, 0x26 };
static const unsigned char pal_flash[16] = {
    0x00, 0x3F, 0x3F, 0x3E, 0x3F, 0x3F, 0x3F, 0x3E,
    0x00, 0x3F, 0x3F, 0x3E, 0x3F, 0x3F, 0x3F, 0x3E };
static const unsigned char pal_spr[16] = {
    0x00, 0x0E, 0x2C, 0x3F, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };

// ── áudio (AUDIO_FSM). Literais de canal EXIGIDOS pelo audit_psg_channel_binding
// (L041/§12): crystal/crack em SFX_CHANNEL1, chime em SFX_CHANNEL2; nunca ch3.
static void sfx_crystal_play(void) { PSGSFXPlay((void *)sfx_crystal, SFX_CHANNEL1); }
static void sfx_crack_play(void)   { PSGSFXPlay((void *)sfx_crack,   SFX_CHANNEL1); }
static void sfx_chime_play(void)   { PSGSFXPlay((void *)sfx_chime,   SFX_CHANNEL2); }

static void music_enter(const void *stream, _Bool no_repeat) {
    PSGStop();
    PSGSFXStop();
    if (no_repeat) PSGPlayNoRepeat((void *)stream);
    else PSGPlay((void *)stream);
    // A atenuação é ESTADO do mixer da PSGlib, não da faixa: sem esta escrita,
    // o último valor de um fade-out anterior (att 15 = silêncio) continua em
    // vigor na cena que entra — a música toca, mas inaudível. Só se escreve 0
    // quando não há rampa armada; rampa ativa manda no seu próprio valor.
    if (fade_att == 0xFFu) PSGSetMusicVolumeChannelsAttenuation(0u, 0u, 0u, 0u);
    probe_playing = 1;
}

// Rampa: PSGlib regrava a atenuação a cada evento do stream, então a rampa é
// re-aplicada DEPOIS do PSGFrame em cada frame — um one-shot seria engolido.
static void apply_ramp(void) {
    if (fade_att != 0xFFu) {
        PSGSetMusicVolumeChannelsAttenuation(fade_att, fade_att, fade_att, fade_att);
    }
}

// ── VDP_FSM: linhas de cena por template (placeholder por zona do storyboard)
// L061-medido, degrau 2026-10-13: os loops C de 32 iterações por linha
// (title_row/dawn_row/storm_row/credits_row) custavam ~13 linhas de blank em
// COMPUTE por linha (main.lst: slots ix, 19 cyc/acesso) contra ~8 linhas do
// físico da escrita (64 B × 28 cyc/B; memcpy, memsetW e memset medidos com o
// MESMO custo — é throttle do VDP, não do laço). A forma da tela virou
// template PNT de 64 B — imagem em RAM montada no BOOT (ROM 16 K cheia,
// medido por s__HOME), receita gerada em inc/pnt_rows.h por
// tools/gen_pnt_rows.py; o writer escolhe o id por (cena,row), agrupa linhas
// consecutivas iguais num só SMS_VRAMmemcpy e pula linha cujo id já está no
// cache pnt_cur_id. Compute por frame: zero nas linhas estáticas; cristais =
// 1 buffer + commit em bloco; medidor = template + 4 put_tile.
static unsigned char pnt_cur_id[24];          // id no PNT; 0 = sujo/parcial
// Round-9-medido (lwb_peek r9): gd_max=64 linhas numa frame de fade_eco, sendo
// ph_ws_lines=60 DENTRO de scene_write_rows e só 27 de escrita física — 11
// linhas (≈2500 cyc) de bookkeeping POR LINHA de PNT. O `.lst` aponta os dois
// maiores: o laço `sla/rl` genérico de XYtoADDR (5 voltas × 59 cyc + cópias de
// 19 cyc = ~517) e os acessos `ix`/`iy` dos locais no frame de pilha (o wrapper
// compila SDCC sem flag de otimização). A conta de endereço vira TABELA de 24
// entradas montada no boot: bit-exata com a macro (XYtoADDR(0,r) =
// SMS_PNTAddress | r<<6; +col<<1 = XYtoADDR(col,r)), 2 leituras de RAM em vez
// de um laço de deslocamentos.
static unsigned int pnt_row_addr[24];

#define SC_TITLE    0u
#define SC_DAWN     1u
#define SC_STORM    2u
#define SC_DARK     3u
#define SC_CREDITS  4u
#define PID_CRYSTAL 90u                         // aurora linhas 9–19 (cry_mask)
#define PID_METER   91u                         // medidor (beat_cell; base PID_METER_T)

static void put_tile(unsigned char col, unsigned char row, unsigned char tile) {
    SMS_setAddr((unsigned int)(pnt_row_addr[row] + ((unsigned int)col << 1)));
    SMS_setTile(tile);                          // mesma escrita, sem o laço de shift
    pnt_cur_id[row] = 0u;                       // parcial ≠ template puro
}

// Round-6-medido (lwb_peek r6, corredor íntegro): gd_max=221 linhas numa frame
// de fade_eco, sendo ph_wr_gap=194 de COMPUTE (3× o seed de 64 iterações de
// crystal_buf_fill) contra 27 de escrita física (ph_wr_lines ≤ 30 p/ 192 B).
// Todas as linhas-cristal de SC_DAWN (9..19) têm a MESMA imagem — as colunas
// dos 8 cristais não dependem da linha — então a imagem vive num buffer
// persistente e só é refeita quando cry_mask muda; o commit de linha virou
// memcpy puro, sem laço por linha (o mesmo defeito dos loops de 32 iterações
// da linha 300, agora medido em vez de modelado).
static unsigned char cry_img[64];
static unsigned char cry_shown;                   // cry_mask já refletido

static void crystal_buf_fill(void) {
    unsigned char i, col, c, bit = 1u, tile;
    if (cry_mask == cry_shown) return;
    for (i = 0u; i < 8u; i++) {
        tile = (cry_mask & bit) ? T_LIT : T_ICE;
        for (col = 0u; col < 3u; col++) {
            c = (unsigned char)((i << 2) + 2u + col);
            if (c >= 32u) break;                   // cristal 7: só cols 30–31
            cry_img[c << 1] = tile;
        }
        bit = (unsigned char)(bit << 1);
    }
    cry_shown = cry_mask;
}

static unsigned char row_pid(unsigned char scene, unsigned char row) {
    unsigned char bb;
    switch (scene) {
    case SC_DAWN:
        if (row < 5u) return PID_SKY;
        if (row < 9u) return PID_ICE;
        if (row < 20u) return PID_CRYSTAL;
        return (row == 20u) ? PID_ICE_HILL : PID_DARK;
    case SC_STORM:
        if (row < 12u) return ((row >> 1) & 1u) ? PID_CLOUD_B : PID_CLOUD_A;
        if (row < 20u) return (unsigned char)(PID_SEA_FIRST + (row - 12u));
        return PID_DARK;
    case SC_DARK:
        return PID_DARK;
    case SC_CREDITS:
        if (row < 5u) return PID_SKY;
        if (row < 12u) return PID_ICE;
        bb = (unsigned char)(row - 12u + cred_step);
        if (bb < 6u || bb >= 12u) return PID_DARK;
        return (bb & 1u) ? PID_BAR_ICE : PID_BAR_SKY;
    default:                                    // SC_TITLE
        if (row < 4u) return PID_SKY;
        if (row < 7u) return (row & 1u) ? PID_WORD_O : PID_WORD_E;
        if (row < 14u) return PID_HILLS;
        if (row < 20u) return PID_FRONT;
        if (row < 22u) return prompt_on ? PID_PROMPT : PID_DARK;
        if (row == 22u) return PID_METER;
        return PID_DARK;
    }
}

// Cada linha é commitada sozinha (64 B): a escrita é throttle do VDP por byte
// (memcpy/memsetW/mmemset medidos iguais), então agrupar N linhas num só
// memcpy não economiza blank — e com fonte de 64 B leria o template vizinho
// (bug: linha r+1 de um grupo recebera a imagem de pid+1). O que importa é o
// SKIP por cache, que esse laço mantém.
static void scene_write_rows(unsigned char scene, unsigned char row, unsigned char n) {
    unsigned char i = 0u, pid, r, col, we, *cur;
    we = SMS_getVCount();
    if (row >= 24u) return;
    if ((unsigned int)(row + n) > 24u) n = (unsigned char)(24u - row);
    r = row;
    cur = &pnt_cur_id[row];
    while (i < n) {
        pid = row_pid(scene, r);
        if (*cur != pid) {                             // id igual já está no PNT
            *cur = pid;
            wr_acc += 64u;
            if (pid == PID_CRYSTAL) {
                crystal_buf_fill();
                SMS_VRAMmemcpy(pnt_row_addr[r], cry_img, 64u);
            } else if (pid == PID_METER) {
                SMS_VRAMmemcpy(pnt_row_addr[r], pnt_tpl_img[PID_METER_T], 64u);
                for (col = 2u; col < 6u; col++)        // put_tile suja a linha
                    put_tile(col, r, ((col - 2u) == beat_cell) ? T_LIT : T_ICE);
            } else {
                SMS_VRAMmemcpy(pnt_row_addr[r], pnt_tpl_img[pid], 64u);
            }
        }
        i++; r++; cur++;
    }
    // O guard `row >= 24` (retorna sem escrever nada) não entra aqui: ~30 cyc
    // não-atribuídos num caminho que a runtime nunca toma.
    ws_lines = (unsigned char)(ws_lines + (unsigned char)(SMS_getVCount() - we));
}

static void title_row(unsigned char row)       { scene_write_rows(SC_TITLE, row, 1u); }
static void dawn_row(unsigned char row)        { scene_write_rows(SC_DAWN, row, 1u); }
static void storm_row(unsigned char row)       { scene_write_rows(SC_STORM, row, 1u); }

// letreiro genérico (AURORA 6 tiles / TEMPESTADE 10) — arte autoral substitui
// Round-5-medido: banner_draw com 20 put_tile custou 55 linhas de blank na
// frame de transição (gd_max=216 dissecado). Agora é MÁQUINA DE ESTADO:
// 1 linha completa por frame — memcpy do template puro da própria linha
// (~11–13 linhas, zero compute) + os w put_tile do letreiro. Mesma semântica
// visual; quadro extra de latência.
static unsigned char ban_left, ban_col0, ban_w, ban_storm;
static void banner_draw(unsigned char col0, unsigned char w, _Bool storm_bg) {
    ban_col0 = col0; ban_w = w; ban_storm = storm_bg ? 1u : 0u; ban_left = 2u;
}

static void banner_service(void) {
    unsigned char row, base, c;
    if (!ban_left) return;
    row = (unsigned char)(4u - ban_left);        // 2, depois 3
    base = ban_storm ? row_pid(SC_STORM, row) : row_pid(SC_DAWN, row);
    wr_acc = (unsigned int)(wr_acc + 64u);
    SMS_VRAMmemcpy(pnt_row_addr[row], pnt_tpl_img[base], 64u);
    // patch por put_tile (custo medido ~2,75 linhas/tile) em vez do laço de 64
    // iterações em RAM: o seed saiu do caminho por mesma razão do cristal —
    // r6 mediu o laço como dono do "gap" de 194 linhas.
    for (c = ban_col0; c < (unsigned char)(ban_col0 + ban_w) && c < 32u; c++)
        put_tile(c, row, T_LIT);                 // deixa a linha suja (id 0)
    ban_left--;
}

// apagar o letreiro = devolver as linhas 2-3 ao vocabulário da própria cena.
// Round-5-medido: as duas linhas juntas custaram 42 linhas de blank num só
// frame (gs_erase) → máquina de estado, 1 linha/frame.
static unsigned char erb_left, erb_storm;
static void banner_erase_rows(unsigned char storm_bg) {
    erb_left = 2u; erb_storm = storm_bg;
}

static void banner_erase_service(void) {
    unsigned char row;
    if (!erb_left) return;
    row = (unsigned char)(5u - erb_left);        // 3 → 2: apaga de baixo p/ cima
    if (erb_storm) storm_row(row); else dawn_row(row);
    erb_left--;
}

// créditos: 6 barras (band 0..5) sobem pela janela 12..23 conforme cred_step
// — cada linha é um template puro (bar_ice/bar_sky/dark), sem compute.
static void credits_rows(unsigned char from, unsigned char count) {
    scene_write_rows(SC_CREDITS, from, count);
}

// ── cristais (props da cena 02; máscara atravessa dawn→eco, doc/17)
// Round-5-medido: crystal_paint com 18 put_tile custava ~45 linhas (maxhud
// dawn=97/echo=50 com derrames). Agora a luz/apagar só SUJA as 6 linhas do
// cristal; cry_service comita 1 linha por frame (memcpy de cry_img, 64 B,
// ~11–13 linhas) — mesmo conteúdo final, espalhado em 6 frames.
static unsigned char cry_dirty;                 // bits 0..5 = linhas 14..19
static void cry_service(void) {
    unsigned char r, row;
    if (!cry_dirty) return;
    r = 0u;
    while (!(cry_dirty & (unsigned char)(1u << r))) r++;
    cry_dirty &= (unsigned char)~(1u << r);
    row = (unsigned char)(14u + r);
    crystal_buf_fill();
    wr_acc = (unsigned int)(wr_acc + 64u);
    SMS_VRAMmemcpy(pnt_row_addr[row], cry_img, 64u);
    pnt_cur_id[row] = PID_CRYSTAL;              // cry_img = template puro da linha
}
static void crystal_light(unsigned char i) {
    i &= 7u;
    cry_mask |= (unsigned char)(1u << i);
    cry_focus = i;
    cry_dirty |= 0x3Fu;
}

static void crystal_dark(unsigned char i) {
    i &= 7u;
    cry_mask &= (unsigned char)~(1u << i);
    cry_dirty |= 0x3Fu;
}

// ── estilhaços (SPR_FSM, só cena 03): pool fixo 24, sem malloc.
// Posições iniciais de fórmula fixa (dado de build), movimento aritmético.
// Round-5-medido: `shard_x[i] = i * 53u + 7u` com `i % 3u` custou 131 linhas
// de blank (SDCC chama __moduchar por iteração e resolve a multiplicação por
// somas) — foi o dono do gd_max=216 na frame de transição cut_storm→STORM.
// A semente vai para RAM no BOOT, onde laço nenhum é orçamento; o reset da
// transição é cópia de bytes (~8 linhas).
static void shards_seed(void) {
    unsigned char i;
    for (i = 0u; i < SHARDS; i++) {
        shard_x0[i] = (unsigned char)(i * 53u + 7u);
        shard_y0[i] = (unsigned char)(i * 29u + 3u);
        shard_v0[i] = (signed char)(1 + (i % 3u));
    }
}

static void shards_reset(void) {
    unsigned char i;
    for (i = 0u; i < SHARDS; i++) {
        shard_x[i] = shard_x0[i];
        shard_y[i] = shard_y0[i];
        shard_v[i] = shard_v0[i];
    }
    storm_f = 0u; hit_i = 0u; flash_left = 0u; crack_cool = 0u; scroll_acc = 0u;
    crack_flag = 0u;
}

// Uma passada só: avança e publica o estilhaço com o valor quente em registro.
// Degrau medido (lwb_peek selado): step(16)+sat(45) separados = 61 passos de
// VBlank contra orçamento ~62; a travessia dupla dos 3 arrays + marshalling de
// argumentos por chamada SMS_addSprite era o custo. copySAT fica no chamador.
// O x é lido UMA vez (SDCC recomputava o endereço duas vezes por item) e o
// gatilho de crack (aresta doc/17: estilhaço alto → SFX) sai do hud: a varredura
// de 24 posições por frame vira bandeira levantada dentro deste laço, consumida
// em fsm_storm. Sem mudança de semântica: y observado é o mesmo valor.
static void shards_frame(void) {
    unsigned char i, y, x;
    probe_phase = 4u;                   // 4 = preparo/transferência de sprites
    for (i = 0; i < SHARDS; i++) {
        x = shard_x[i];
        y = (unsigned char)(shard_y[i] + (unsigned char)shard_v[i]);
        if (y >= 192u) {
            y = 0u;
            x = (unsigned char)(x + 19u + i);
            shard_x[i] = x;
        }
        shard_y[i] = y;
        if (y > 150u) crack_flag = 1u;
        SMS_addSprite(x, y, T_SHARD);
    }
}

// ── transições: mapa inteiro com display OFF, 2 linhas/frame (12 frames).
// Degraus medidos (lwb_peek selado): 12 linhas/frame via setTileatXY custou
// 185 linhas de blank (derrame); via cursor, 12 ainda passou de 62 → 6 por
// frame derramou 15 frames (medido: vovf_delta=15 == soma dos spills por
// estado; cut_storm=4 — todos os seus frames — fade_eco=3, fade_dawn=2,
// black=2: 6×8,5 de escrita + ~15 de stream = ~66 > ~62 de janela).
// 4 linhas/janela derramou 2–4 frames por estado de fade (round-5d, vovf=36);
// 3 linhas com bookkeeping por linha (round-8, gd_max=64) derramou 1 frame em
// ST_FADE_ECO: a sonda ph_ws_lines=60 de 64 (round-9) deu o dono a
// scene_write_rows e deixou só 4 linhas para FSM/despacho. Round-10 (tabela
// pnt_row_addr no boot, ponteiro para pnt_cur_id, sonda por CALL) baixou
// gd_max para 54 e ph_ws_lines para 50, mas a última volta ainda morria em
// 0xFD — 1 frame de derrame, e o resto é o custo físico de 64 B/linha, não
// contabilidade. 2 linhas (~20 + stream ~15 ≈ 35) é o degrau que fecha.
// Distribuído porque 24 linhas num só VBlank não cabe; cenário da reescrita é
// parâmetro (não estado).
static void rewrite_step_prepare(void) {
    SMS_displayOff();
    ban_left = 0u; erb_left = 0u; cry_dirty = 0u;   // escrita pendente não cruza a borda
    rewrite_row = 0u;
}

static _Bool rewrite_step(unsigned char scene) {
    unsigned char sc;
    if (rewrite_row == 0xFFu) return 0;
    sc = (scene == 3u) ? SC_DAWN : (scene == 4u) ? SC_DARK : scene;
    scene_write_rows(sc, rewrite_row, 2u);
    rewrite_row = (unsigned char)(rewrite_row + 2u);
    if (rewrite_row >= 24u) {
        rewrite_row = 0xFFu;
        SMS_displayOn();
        return 1;
    }
    return 0;
}

// ── INPUT_FSM: único leitor do port; entrega eventos, ninguém mais lê.
static void input_step(void) {
    unsigned int keys = SMS_getKeysPressed();
    ev_start = (unsigned char)((keys & PORT_A_KEY_1) && !(prev_keys & PORT_A_KEY_1));
    ev_select = (unsigned char)((keys & PORT_A_KEY_2) && !(prev_keys & PORT_A_KEY_2));
    prev_keys = keys;
    if (ev_start || ev_select) touched = 1;
    if (probe_frame == 240u && !touched) attract = 1u;
    if (SMS_queryPauseRequested()) {           //Pause: tecla física, não botão
        SMS_resetPauseRequest();
        silent = (unsigned char)(!silent);
        if (silent) PSGSilenceChannels();
        else PSGRestoreVolumes();
    }
}

// ── cenas de abertura/reentrada
// título-escuro no mapa: 24 linhas num frame SÓ existem aqui (boot, display
// ainda OFF) — um único write em bloco de 1536 B. Em runtime vivo a reentrada
// preta usa rewrite_step (cena SC_DARK, 2 linhas/janela com skip por id).
static void title_write_dark(void) {
    scene_write_rows(SC_DARK, 0u, 24u);
}

static void title_setup(void) {
    reveal_row = 0u;
    prompt_on = 0u;
    beat_cell = 0u; beat_count = 0u;
    fade_att = 0xFFu;
    probe_track = 0u; probe_playing = 0u;
    state = ST_TITLE; t = 0u; probe_state = ST_TITLE;
}

// ── GAME_FSM: um trecho por estado; t cresce 1 por frame
static void goto_state(unsigned char s) {
    state = s; t = 0u; probe_state = s;
}

static void fsm_title(void) {
    unsigned char col;
    if (t == 0u) sfx_chime_play();                        // roteiro: a pergunta
    if (t == 45u) { fade_att = 12u; music_enter(music_title, 0); }
    if (reveal_row < 24u && (t & 1u) == 0u) {             // 1 linha / 2 frames
        title_row(reveal_row);
        reveal_row++;
    }
    if (t >= 45u && fade_att != 0xFFu) {                  // piano-forte: att 12→0 em 120 f
        if ((unsigned char)(t % 10u) == 9u && fade_att > 0u) fade_att--;
        if (t >= 165u) fade_att = 0xFFu;
    }
    if (prompt_on && ++beat_count >= 48u) {               // pulse por compasso
        beat_count = 0u;
        beat_cell = (unsigned char)((beat_cell + 1u) & 3u);
        for (col = 2u; col < 6u; col++)
            put_tile(col, 22u, ((col - 2u) == beat_cell) ? T_LIT : T_ICE);
    }
    // prompt: jogador = primeiro loop point (roteiro); atração = f240
    if (!prompt_on && (attract ? (t >= 240u) : (t >= LOOP_TITLE))) {
        prompt_on = 1u;
        title_row(20u);                                   // START nas linhas 20-21
        title_row(21u);                                   // (planta baixa cena 01)
    }
    if ((prompt_on && ev_start) || (attract && t >= 300u)) {
        fade_att = 0u;
        cnt_fade_dawn++;
        goto_state(ST_FADE_DAWN);
    }
}

static void fsm_fade_dawn(void) {
    if (t < 60u) fade_att = (unsigned char)(1u + (t >> 2));   // 0→15 em 60 f, sem degrau de entrada
    else if (t == 60u) { PSGStop(); probe_playing = 0u; fade_att = 0xFFu; }
    else if (t == 120u) {                                 // 1 s de respiração
        rewrite_step_prepare();
        SMS_loadBGPalette((void *)pal_dawn);
        probe_track = 1u;
    }
    if (t > 120u && rewrite_step(1u)) {
        atk_i = 0u; ramp_step = 0u; ramp_count = 0u;
        goto_state(ST_DAWN);
        music_enter(music_dawn, 0);
        banner_draw(13u, 6u, 0u);                           // letreiro AURORA (4 s)
    }
}

static void fsm_dawn(void) {
    if (t == 240u) banner_erase_rows(0);                   // letreiro: 4 s
    banner_service();                                      // letreiro: 1 linha/frame
    banner_erase_service();
    cry_service();                                         // cristais: 1 linha/frame
    if (++ramp_count >= 30u && ramp_step < 6u) {           // clareja em degraus
        ramp_count = 0u;
        ramp_step++;
        if (ramp_step == 6u) SMS_loadBGPalette((void *)pal_dawn_ramp);
    }
    {                                                      // ressonância por ataque
        while (atk_i < DAWN_ATTACKS_N && dawn_attacks[atk_i] <= t) {
            if (dawn_attacks[atk_i] == t) crystal_light(atk_i);
            atk_i++;
        }
    }
    if (ev_select) {                                       // SELECT só na aurora
        sfx_crystal_play();
        crystal_light(cry_focus);
        cnt_sfx_crystal++;
    }
    if (ev_start) { goto_state(ST_CUT_STORM); cnt_cut_storm++; }   // aresta do contrato
    else if (attract && t >= 480u) { goto_state(ST_CUT_STORM); cnt_cut_storm++; }
}

static void fsm_cut_storm(void) {
    // "a tempestade não pede licença": PSGStop no frame N, PSGPlay no N+1
    // (doc/17). O stream toca durante a reescrita preta; o flash/scroll da
    // cena sincroniza com storm_hits a partir do frame 0 de STORM — offset
    // declarado ≤3 frames da tabela, medir na evidência.
    if (t == 0u) { PSGStop(); probe_playing = 0u; }
    else if (t == 1u) {
        rewrite_step_prepare();
        SMS_loadBGPalette((void *)pal_storm);
        probe_track = 2u;
        music_enter(music_storm, 0);
    } else if (rewrite_step(2u)) {
        shards_reset();
        banner_draw(11u, 10u, 1u);                           // TEMPESTADE (90 f)
        goto_state(ST_STORM);
    }
}

static void fsm_storm(void) {
    while (hit_i < STORM_HITS_N && storm_hits[hit_i] <= storm_f) {
        if (storm_hits[hit_i] == storm_f) flash_left = 2u;
        hit_i++;
    }
    if (flash_left == 2u) SMS_loadBGPalette((void *)pal_flash);
    else if (flash_left == 1u) SMS_loadBGPalette((void *)pal_storm);
    if (flash_left) flash_left--;
    if (t == 90u) banner_erase_rows(1);
    banner_service();                                       // letreiro: 1 linha/frame
    banner_erase_service();                                 // apaga: 1 linha/frame
    if (crack_cool) crack_cool--;
    else if (crack_flag) { sfx_crack_play(); crack_cool = 60u; crack_flag = 0u; }
    if (ev_start) goto_state(ST_FADE_ECO);                 // aresta do contrato
    else if (attract && t >= 600u) goto_state(ST_FADE_ECO);
}

static void fsm_fade_eco(void) {
    if (t < 60u) fade_att = (unsigned char)(1u + (t >> 2));   // 0→15 em 60 f, sem degrau de entrada
    else if (t == 60u) { PSGStop(); probe_playing = 0u; fade_att = 0xFFu; }
    else if (t == 120u) {
        // teardown OBRIGATÓRIO da tempestade (doc/17): SAT, flash, scroll
        SMS_initSprites();
        SMS_copySpritestoSAT();
        SMS_setBGScrollX(0);
        SMS_setBGScrollY(0);
        SMS_loadBGPalette((void *)pal_storm);              // flash de volta a zero
        rewrite_step_prepare();
        SMS_loadBGPalette((void *)pal_dawn);
        probe_track = 3u;
    }
    if (t > 120u && rewrite_step(3u)) {
        extinguish_i = 7u; ext_count = 0u;
        music_enter(music_eco, 1);                         // única não-loop
        goto_state(ST_ECHO);
    }
}

static void credits_setup(void) {
    cred_step = 0u; cred_sub = 0u;
    probe_track = 4u;
    goto_state(ST_CREDITS);
}

static void fsm_echo(void) {
    cry_service();                                         // cristais: 1 linha/frame
    if (++ext_count >= 72u) {                              // 1 cristal / compasso
        ext_count = 0u;
        if (extinguish_i < 8u) {
            crystal_dark(extinguish_i);
            extinguish_i = (extinguish_i == 0u) ? 0xFFu : (unsigned char)(extinguish_i - 1u);
        }
    }
    // créditos: o gatilho é o FIM do stream, não a nossa conta
    if (PSGGetStatus() == PSG_STOPPED) credits_setup();
    else if (attract && t >= 640u) {                       // atração: eco abreviada
        PSGStop(); probe_playing = 0u;
        credits_setup();
    }
}

static void fsm_credits(void) {
    // rolagem: 1 passo (linhas 12..23 deslocadas) a cada 30 f. Round-5-medido:
    // 3 linhas por frame (192 B ≈ 31 linhas de blank) derramavam 15 frames
    // neste estado — o degrau que cabe é 1 linha/frame (64 B ≈ 11 linhas),
    // 12 frames para as 12 linhas, dentro dos 30 f do passo.
    if (cred_sub) {
        credits_rows((unsigned char)(12u + (cred_sub - 1u)), 1u);
        if (++cred_sub > 12u) cred_sub = 0u;
    } else if (t > 0u && (t % 30u) == 0u) {
        if (cred_step >= 12u) {                            // rolagem completa
            PSGSilenceChannels();                          // silêncio como escolha
            SMS_displayOff();
            goto_state(ST_BLACK);
            return;
        }
        cred_step++;
        cred_sub = 1u;
    }
}

static void fsm_black(void) {
    if (t == 120u) {                                       // reentra pelo arco BOOT→TITLE
        PSGRestoreVolumes();
        PSGStop(); probe_playing = 0u;
        PSGSFXStop();
        SMS_loadBGPalette((void *)pal_title);
        rewrite_step_prepare();
    }
    if (t > 120u && rewrite_step(4u)) {
        // rewrite_step já ligou o display; o mapa veio inteiro escuro
        // (title_row_dark via cena 4), só faltam as variáveis.
        title_setup();
    }
}

// trabalho contínuo de VBlank (SPR commit + scroll do motor rítmico).
// Pipeline (L061-medido): a reconstrução da tabela-zumbi de sprites
// (initSprites+24×addSprite, sm_step=70 linhas) NÃO toca o VDP e foi movida
// para o tempo de tela ativa, fim do loop; a SAT inteira dentro do blank
// estourava o orçamento de ~62 linhas em todo frame de tempestade. No blank
// só fica o que escreve VDP: copySpritestoSAT (sm_sat=11) + scroll.
// Consequência declarada: os estilhaços usam a tabela construída no frame
// anterior — um frame de latência, invisível no movimento de queda.
static unsigned char cp_a, cp_b, cp_c, cp_d;   // subfases do motor (commit em fase 3)
static void vblank_scene_work(void) {
    if (state == ST_STORM) {
        cp_c = SMS_getVCount();
        SMS_copySpritestoSAT();         // resto da SAT vira 0xD0 (SMSlib_sprite.c)
        cp_d = SMS_getVCount();
        scroll_acc++;
        SMS_setBGScrollY((unsigned char)(scroll_acc & 0xFFu));
        // wrap do loop: o cursor de hits volta ao início, senão o flash
        // morre depois da primeira volta (aresta flash↔ch3 é por loop)
        if (++storm_f >= LOOP_STORM) { storm_f = 0u; hit_i = 0u; }
    }
}

static void storm_preblank(void) {      // tela ativa: só RAM-Z80
    if (!silent && state == ST_STORM) {
        cp_a = SMS_getVCount();
        SMS_initSprites();
        shards_frame();
        cp_b = SMS_getVCount();
    }
}

static void game_step(void) {
    switch (state) {
        case ST_TITLE:     fsm_title(); break;
        case ST_FADE_DAWN: fsm_fade_dawn(); break;
        case ST_DAWN:      fsm_dawn(); break;
        case ST_CUT_STORM: fsm_cut_storm(); break;
        case ST_STORM:     fsm_storm(); break;
        case ST_FADE_ECO:  fsm_fade_eco(); break;
        case ST_ECHO:      fsm_echo(); break;
        case ST_CREDITS:   fsm_credits(); break;
        default:           fsm_black(); break;
    }
    t++;
}

static void tiles_upload(void) {
    // Padrões de placeholder: sólidos por subpaleta + cunha de sprite.
    // 6 tiles × 32 B — custo único no boot, display ainda OFF.
    // Formato VDP (png_to_sms_tiles.py:27-39): PLANAR, 4 bytes/linha —
    // byte p = plano de bits p da cor nos 8 pixels (bit 7-x = pixel x).
    // Cada byte NÃO é um pixel: escrever 1 byte/pixel renderiza grade de
    // pontos — L061-provado em dump de VRAM+screenshot nativo do BlastEm.
    static const unsigned char pats[6][TILE_BYTES] = {
        { 0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00,
          0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00 },
        { 0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00,
          0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00 },
        { 0x00,0xFF,0x00,0x00, 0x7E,0xFF,0x00,0x00, 0x42,0xFF,0x00,0x00, 0x7E,0xFF,0x00,0x00,
          0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00, 0x00,0xFF,0x00,0x00 },
        { 0xFF,0xFF,0x00,0x00, 0x81,0xFF,0x00,0x00, 0xBD,0xFF,0x00,0x00, 0x81,0xFF,0x00,0x00,
          0xFF,0xFF,0x00,0x00, 0xFF,0xFF,0x00,0x00, 0xFF,0xFF,0x00,0x00, 0xFF,0xFF,0x00,0x00 },
        { 0xFF,0x00,0x00,0x00, 0xFF,0x18,0x00,0x00, 0xFF,0x3C,0x00,0x00, 0xFF,0x7E,0x00,0x00,
          0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00, 0xFF,0x00,0x00,0x00 },
        { 0xC3,0xFF,0x00,0x00, 0x66,0x7E,0x00,0x00, 0x24,0x3C,0x00,0x00, 0x18,0x00,0x00,0x00,
          0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00 }
    };
    SMS_loadTiles((void *)pats, 0, 6u * TILE_BYTES);
}

// Header 16KB => SDSC variante _16KB (combinação provada em ROM no
// laboratorio_01; SMSlib.h:460/:485). Se a FSM estourar 16 KB, a troca de
// variante é decisão nova + aprovação humana (GDD: cabe em 48 KB lineares).
SMS_EMBED_SEGA_ROM_HEADER_16KB(0, 0);
SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB(0, 1, "SMSForge", "pulso_de_cristal",
                                     "FSM M3 quatro cenas");

void main(void) {
    SMS_displayOff();
    probe_magic0 = 'S'; probe_magic1 = 'M'; probe_magic2 = 'R'; probe_magic3 = 'T';
    probe_schema = 1;
    probe_frame = 0; probe_vline = 0; probe_vovf = 0; probe_phase = 0;
    probe_worst_done = 0; probe_vline_min = 0xFF;
    probe_track = 0; probe_playing = 0; probe_state = 0; probe_attract = 0;
    probe_vline_spill_max = 0;
    gd_max = 0; gd_state = 0; gi_max = 0; gi_state = 0;
    cnt_fade_dawn = 0; cnt_cut_storm = 0; cnt_sfx_crystal = 0;
    ph_hud_lines = 0; ph_sat_lines = 0; ph_stream_lines = 0;
    ph_worst_stage = 0; ph_worst_total = 0;
    spill_title = 0; spill_fade_dawn = 0; spill_dawn = 0;
    spill_cut_storm = 0; spill_storm = 0; spill_fade_eco = 0;
    spill_echo = 0; spill_credits = 0; spill_black = 0;
    { unsigned char i; for (i = 0; i < 9u; i++) ph_state_max_sat[i] = 0u;
      for (i = 0; i < 7u; i++) ph_state_max_hud[i] = 0u; }
    sm_step_lines = 0; sm_sat_lines = 0; sm_tail_lines = 0;
    ph_credits_hud = 0; ph_black_hud = 0;
    ph_stream_max = 0; ph_worst_state = 0; ph_worst_end = 0;
    spill_st_hud = 0; spill_st_sat = 0; spill_st_stream = 0; spill_st_tail = 0;
    ph_wr_hud_max = 0; wr_acc = 0;
    ws_lines = 0; ph_ws_lines = 0;
    stack_sentinel = 0x5Au; spill_st_input = 0;
    { unsigned char i; for (i = 0u; i < 7u; i++) {
          spill_wait_max[i] = 0u; spill_wait_min[i] = 0xFFu; } }
    { unsigned char i; for (i = 0u; i < 24u; i++) pnt_cur_id[i] = 0xFFu; }  // nada escrito ainda
    tiles_upload();
    SMS_loadBGPalette((void *)pal_title);
    SMS_loadSpritePalette((void *)pal_spr);
    SMS_useFirstHalfTilesforSprites(1);                    // L006: sprites na 1ª metade
    attract = 0u; touched = 0u; silent = 0u; prev_keys = 0u;
    ev_start = 0u; ev_select = 0u;
    cry_mask = 0u; cry_focus = 0u;
    rewrite_row = 0xFFu;
    pnt_tpl_build();                                     // só no BOOT (sem budget)
    // tabela de endereços de linha: custo de endereço sai do VBlank.
    // Bit-exata com a macro verificada exaustivamente (24 linhas × 32 colunas,
    // Python): SMS_PNTAddress | ((y<<5)+x)<<1 == (SMS_PNTAddress | y<<6) + x<<1
    // para y<24 e x<32 — o termo deslocado cabe em 11 bits, então não há carry
    // nos bits 0x7800 e OR/+=" são a mesma aritmética.
    { unsigned char i; for (i = 0u; i < 24u; i++)
          pnt_row_addr[i] = SMS_PNTAddress | ((unsigned int)i << 6); }
    // base dos cristais semeada no boot: ICE + col0 HILL. Em runtime o
    // crystal_buf_fill só refaz os 24 slots quando cry_mask muda.
    { unsigned char k; for (k = 0u; k < 64u; k++)
          cry_img[k] = pnt_tpl_img[PID_ICE_HILL][k]; }
    cry_shown = 0xFFu;                                   // força o refresh
    crystal_buf_fill();                                  // ... AGORA no boot:
    // r7 mediu 1 frame de derrame em cada fade (spill_st_hud=2, hud=67 linhas
    // = 30 de escrita + 37 do refresh) — o refresh era o primeiro após o boot.
    // Com a imagem refletida em boot, o runtime só refaz os slots quando
    // cry_mask realmente muda, e isso já cabe (dawn/echo: spill 0).
    shards_seed();                                       // idem: reset vira cópia
    title_write_dark();                                    // vale adormecido (boot)
    title_setup();                                         // vars, t=0
    SMS_displayOn();

    for (;;) {
        unsigned char v, sp, tot;
        SMS_waitForVBlank();

        // fase 2: trabalho de VBlank na ordem canônica do contrato de perfil
        // (escritas de nome/paleta = "hud", depois SAT = "sat", depois áudio =
        // "stream"); a amostra final vem depois de tudo (L061).
        probe_phase = 2u;
        cp_wait = SMS_getVCount();
        cp_hud = cp_wait; cp_sat = cp_wait; cp_stream = cp_wait;
        wr_acc = 0u;
        ws_lines = 0u;
        input_step();
        cp_mid = SMS_getVCount();
        probe_state = state;                               // contrato do tool lê em F6
        if (!silent) {
            game_step();                                   // FSM: name table/CRAM
            cp_hud = SMS_getVCount();
            if (probe_frame < WORST_FRAME_WINDOW && wr_acc > ph_wr_hud_max)
                ph_wr_hud_max = wr_acc;
            vblank_scene_work();                           // motor: passos+SAT+scroll
            cp_sat = SMS_getVCount();
            PSGFrame();
            PSGSFXFrame();
            apply_ramp();
            cp_stream = SMS_getVCount();
            if (probe_playing && PSGGetStatus() == PSG_STOPPED) probe_playing = 0u;
        }
        // causa por etapa (round-3): primeira fase que termina dentro da tela
        // ativa (vcounter < 0xC0) é a que cruzou a borda; tail = já voltou
        // estourado do waitForVBlank (rabo da frame anterior).
        if (probe_frame < WORST_FRAME_WINDOW) {
            if (cp_wait < 0xC0u) { if (spill_st_tail < 255u) spill_st_tail++; }
            else if (cp_mid < 0xC0u) { if (spill_st_input < 255u) spill_st_input++; }
            else if (cp_hud < 0xC0u) { if (spill_st_hud < 255u) spill_st_hud++; }
            else if (cp_sat < 0xC0u) { if (spill_st_sat < 255u) spill_st_sat++; }
            else if (cp_stream < 0xC0u) { if (spill_st_stream < 255u) spill_st_stream++; }
        }
        // máximos GLOBAIS das duas metades do hud (deltas de VCounter em
        // módulo 256 = linhas; cada trecho legítimo cabe numa volta): a
        // hipótese "216 linhas em game_step na tempestade" agora tem
        // testemunha por fase, com estado da frame (F6 da pilha NÃO — o
        // estado aqui é a variável interna `state`, não a sonda).
        if (probe_frame < WORST_FRAME_WINDOW) {
            unsigned char d = (unsigned char)(cp_mid - cp_wait);
            if (d > gi_max) { gi_max = d; gi_state = state; }
            d = (unsigned char)(cp_hud - cp_mid);
            if (d > gd_max) {
                gd_max = d; gd_state = state;
                ph_ws_lines = ws_lines;    // quanto de d é scene_write_rows
            }
        }

        // fase 3: última leitura do blank na janela de diagnóstico; após o
        // selo, nenhum byte de teste — o DAP só conecta depois (L082).
        if (probe_frame < WORST_FRAME_WINDOW) {
            probe_phase = 3u;
            v = SMS_getVCount();
            probe_vline = v;
            if (v < probe_vline_min) probe_vline_min = v;
            if (v < 0xC0u) {
                probe_vovf++;                              // word: não satura
                if (v > probe_vline_spill_max) probe_vline_spill_max = v;
                // cp_wait das frames de derrame, por estado: <0xC0 = espera
                // pulada (tail em cascata, raiz a montante); >=0xC0 = espera
                // normal e a frame em si estourou o blank. TITLE(0) e
                // BLACK(8) nunca derramaram — vetores de 7 cobrem 1..7.
                sp = state;
                if (sp >= 1u && sp <= 7u) {
                    if (cp_wait > spill_wait_max[sp - 1u]) spill_wait_max[sp - 1u] = cp_wait;
                    if (cp_wait < spill_wait_min[sp - 1u]) spill_wait_min[sp - 1u] = cp_wait;
                }
                // histograma por estado, saturante em 255 (9 estados, 9 bytes)
                switch (sp) {
                    case ST_TITLE:
                        if (spill_title < 255u) spill_title++; break;
                    case ST_FADE_DAWN:
                        if (spill_fade_dawn < 255u) spill_fade_dawn++; break;
                    case ST_DAWN:
                        if (spill_dawn < 255u) spill_dawn++; break;
                    case ST_CUT_STORM:
                        if (spill_cut_storm < 255u) spill_cut_storm++; break;
                    case ST_STORM:
                        if (spill_storm < 255u) spill_storm++; break;
                    case ST_FADE_ECO:
                        if (spill_fade_eco < 255u) spill_fade_eco++; break;
                    case ST_ECHO:
                        if (spill_echo < 255u) spill_echo++; break;
                    case ST_CREDITS:
                        if (spill_credits < 255u) spill_credits++; break;
                    default:
                        if (spill_black < 255u) spill_black++; break;
                }
            }
            // linhas por etapa: diferença de VCounter em módulo 256 — o
            // contador dá UMA volta por frame; correção somada estourava u8
            tot = (unsigned char)(cp_stream - cp_wait);
            // decomposição por estado: pior hud (input+FSM) e pior sat (motor)
            { unsigned char hl = (unsigned char)(cp_hud - cp_wait);
              unsigned char sl = (unsigned char)(cp_sat - cp_hud);
              unsigned char tl = (unsigned char)(cp_stream - cp_sat);
              sp = state;
              if (sl > ph_state_max_sat[sp]) ph_state_max_sat[sp] = sl;
              if (sp < 7u) { if (hl > ph_state_max_hud[sp]) ph_state_max_hud[sp] = hl; }
              else if (sp == 7u) { if (hl > ph_credits_hud) ph_credits_hud = hl; }
              else if (hl > ph_black_hud) ph_black_hud = hl;
              if (tl > ph_stream_max) { ph_stream_max = tl; ph_worst_end = cp_stream; }
              if (sp == ST_STORM) {                        // só tem subfases na tempestade
                unsigned char d1 = (unsigned char)(cp_b - cp_a);   // build (tela ativa)
                unsigned char d2 = (unsigned char)(cp_d - cp_c);   // copySAT (blank)
                unsigned char d3 = (unsigned char)(cp_sat - cp_d); // scroll+wrap (blank)
                if (d1 > sm_step_lines) sm_step_lines = d1;
                if (d2 > sm_sat_lines) sm_sat_lines = d2;
                if (d3 > sm_tail_lines) sm_tail_lines = d3;
              }
            }
            if (tot > ph_worst_total) {
                ph_worst_total = tot;
                ph_worst_state = state;
                ph_hud_lines = (unsigned char)(cp_hud - cp_wait);
                ph_sat_lines = (unsigned char)(cp_sat - cp_hud);
                ph_stream_lines = (unsigned char)(cp_stream - cp_sat);
                ph_worst_stage =
                    (ph_sat_lines >= ph_hud_lines &&
                     ph_sat_lines >= ph_stream_lines) ? 2u :
                    (ph_stream_lines >= ph_hud_lines) ? 3u : 1u;
                // conjunto coerente da pior frame para o contrato PROFILE_ADDRS
                probe_profile_wait = cp_wait;
                probe_profile_hud = cp_hud;
                probe_profile_sat = cp_sat;
                probe_profile_stream = cp_stream;
            }
            if (probe_frame == (WORST_FRAME_WINDOW - 1u)) probe_worst_done = 1u;
        }

        probe_phase = 1u;
        probe_attract = attract;
        probe_state = state;
        probe_frame++;
        storm_preblank();                                  // tabela de sprites em tela ativa
    }
}
