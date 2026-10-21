# 13-spec-cenas — pulso_de_cristal

> Budget REAL por cena. **Autoridade #3.**
> Regra: **"estimado" é proibido neste arquivo.** Todo número aqui é medido,
> com o método da medição citado. Folga não medida é timidez (§18).

## Contrato de hardware (fixo, não negociável)
| Recurso | Limite físico | Fonte (não é número de outro console) |
|---------|---------------|----------------------------------------|
| Tela | 256×192 | modo 192 px, janela vertical 224 (`SMS_setBGScrollY(224u)`, `src/main.c:971`) |
| VRAM | 16 KB | `sdk/devkitSMS/SMSlib/SMSlib.h` (autoridade #8) |
| RAM | 8 KB | idem |
| Sprites por scanline | 8 | hardware SMS; verificado por `audit_sprite_line_sim.py` |
| Entradas na tabela de objetos | 64 (`MAXSPRITES 64`, `sdk/devkitSMS-upstream/SMSlib/src/SMSlib_common.c:23`; SAT em `SMS_SATAddress 0x7F00`, :19). **SMS1 tem metade da tabela de atributos → 32 úteis e a escrita acima espelha** (mesma classe de armadilha do reg2 bit0=0 que `audit_tilemap_mirror.py` bloqueia). Este projeto visa SMS2/GG, onde 64 é o número da biblioteca. |
| Subpaletas | 2 × 16 (índice 0 transparente nas duas) | header SMSlib |
| Cores úteis simultâneas | 30 | 2×16 menos os dois índices 0 |
| Janela VBlank | ~4,5 ms (NTSC) — **não existe DMA**. A moeda usada embaixo é **linha de VCounter**, lida com `SMS_getVCount()`; o instrumento modela o período do contador em 262 com a descontinuidade documentada DA→D5 (`measure_worst_frame.py:409-442`) | — |
| ROM sem mapper | 48 KB | `sdk/README.md` |
| Canais de áudio | 3 tone + 1 noise (SN76489), driver PSGlib | `PSGlib.h` |

## Status deste arquivo
As quatro cenas têm **worst-frame medido na ROM atual**
(`f4f8ee3f4c2a720a1da696fe7a84235a787cc1edeba5d0eb25d9592f5b2eb331`, 16384 B),
na janela selada de 3000 frames (`out/evidence/worst_frame_r13.json`,
veredito `pass`, `vovf_delta=0`, `vline_min=203`) e por-estado em
`out/logs/peek_r14.txt` (corredor 0xC990–0xC9F6, `frame=6289`, `done=1`).
O que ainda está vazio aqui é **não medido de verdade**, não timidez:
- **tiles de padrão (arte autoral)**: a ROM carrega 6 tiles provisórios
  (`SMS_loadTiles(pats, 0, 6u * TILE_BYTES)`, `src/main.c:916`, `TILE_BYTES 32u`
  → 192 B no slot 0). A linha "patterns BG/patterns sprite" fica **a declarar no
  contrato de asset** — medir VRAM de um placeholder e promovê-lo a orçamento do
  tileset autoral seria infração de época visual (L036/§39);
- **fps por cena isolada**: medido no arco (6 janelas, abaixo), não por cena
  parada — o arco é o claim do projeto (transição contínua), então a medição
  feita é a do arco;
- **leitura por estado de `ph_state_max_sat[3]` e `[5]`**: valem 251 = `256−5`,
  artefato do delta em módulo 256 (`src/main.c:1083`) quando o checkpoint
  `cp_sat` não é alcançado naquela cena. **Não são custo e não são citáveis.**
  O mesmo vale para `ph_stream_max = 255` (:1084). Já `ph_state_max_hud[]` é
  citável: `cp_hud` sempre roda depois de `cp_wait`.

## Trilha — orçamento de stream por faixa (MEDIDO 2026-10-14)
Método: `audit_psg_quality.py --project . --json out/logs/psg_quality_m3b.json`
(duração = frames do stream, contados no binário pelo decodificador; bytes =
`len(blob)` gravado pelo emissor, que já roda o mesmo auditor antes de escrever).
SHA-256 dos `.psg` em `doc/audio_provenance_manifest.json` (gate
`audit_audio_provenance.py` = PASS).

| Faixa | Frames/loop (M5≥250) | Bytes .psg |ROM usada | Método |
|-------|----------------------|------------|-----------|--------|
| music_title | 1536 f (25,6 s) | 1956 B | 11,9% | `audit_psg_quality.py` no binário |
| music_dawn | 1920 f (32,0 s) | 1789 B | 10,9% | idem |
| music_storm | 896 f (14,9 s) | 1808 B | 11,0% | idem |
| music_eco | 1728 f (28,8 s) | 1453 B | 8,9% | idem |
| sfx_chime / crack / crystal | 29 / 11 / 19 f | 23 / 23 / 27 B | 0,4% | `audit_psg_quality.py` (política SFX S1/S2) |

- Total de áudio na ROM: **7079 B de 16384 B (43,2%)**.
- Ruido: as três faixas com percussão medem `ruido_branco = 1.0` (M4). Rounds
  anteriores do emissor emitiam latch `0xE0 | (shift & 3)`, que **apagava o
  bit2** e produzia ruído periódico (assobio) — L079/§64: bit2=1 é branco.
  Corrigido no emissor + nas partituras (modo 4–7), `--self-check` do emissor
  agora exige o branco por construção.

## Orçamento de VBlank por estado (MEDIDO — a tabela-mãe das quatro cenas)
Método: a própria ROM grava `SMS_getVCount()` em quatro checkpoints do VBlank
(`cp_wait → cp_hud → cp_sat → cp_stream`, `src/main.c:993-1010`) e acumula
máximos por estado no corredor `0xC900`. Leitura: `tools/lwb_peek.py --wait 100`
→ `out/logs/peek_r14.txt` (ROM `f4f8ee3f`, `frame=6289`, janela de 3000 f
cumprida, `vovf=0`). Unidade = **linha de VCounter** (delta em módulo 256).

| Estado | hud (input+FSM+nome/paleta) | sat (motor) | spill (frames que cruzaram 0xC0) |
|--------|------------------------------|-------------|----------------------------------|
| 0 TITLE | 34 | 2 | 0 |
| 1 FADE_DAWN | 29 | 2 | 0 |
| 2 DAWN | 34 | 2 | 0 |
| 3 CUT_STORM | 28 | não usável (251 = wrap) | 0 |
| 4 STORM | 39 | 13 | 0 |
| 5 FADE_ECO | 45 | não usável (251 = wrap) | 0 |
| 6 ECHO | 27 | 2 | 0 |
| 7 CREDITS | 22 (`ph_credits_hud`) | 2 | 0 |
| 8 BLACK | 28 (`ph_black_hud`) | 2 | 0 |

- **Pior frame da janela inteira**: 58 linhas `wait→stream` em módulo 256 =
  **64 linhas corrigidas** pela descontinuidade DA→D5 do instrumento
  (`worst_frame_r13.json`: hud 42 + sat 13 + stream 9), estado **STORM**
  (`ph_worst_state=4`), etapa dona = **escritas de nome/paleta**
  (`ph_worst_stage=1`).
- **Split da metade "hud" (global, máximos separados por checkpoint `cp_mid`)**:
  input ≤ **3 linhas** (`gi_max`, estado TITLE) e `game_step` ≤ **42 linhas**
  (`gd_max`, estado FADE_ECO). Nada de input no pior frame.
- **Bytes de name table no pior VBlank**: `ph_wr_hud_max = 128 B` = exatamente
  2 linhas × 64 B — o degrau declarado em doc/17 (`rewrite_step 2 linhas/frame`),
  medido e não assumido.
- **Causa do trabalho dentro de `scene_write_rows`**: `ph_ws_lines = 37` linhas
  (as 42 de hud não são todas de escrita: a FSM e a paleta vivem no mesmo trecho).
- **Stream musical no pior frame**: `PSGFrame()+PSGSFXFrame()+apply_ramp()` =
  **9 linhas** com música tocando (`ph_stream_lines=9`). Este é o número que
  fecha a linha "`PSGFrame()` com música" que estava em "não medido".
- **Derrame**: os nove contadores `spill_*` **e** os quatro `spill_st_*`
  (tail/input/hud/sat/stream) valem **0** — nenhum frame dos 3000 selados terminou
  dentro da tela ativa, com causa-imune-a-amostragem.
- `stack_sentinel = 90` (pilha não invadiu o corredor).

## Cena 01 — título
### Layout de VRAM declarado
| Região | Faixa | Tiles | Uso |
|--------|-------|-------|-----|
| patterns BG | slot 0, 192 B medidos em runtime (`SMS_loadTiles(pats, 0, 6u*32u)`) | 6 (T_DARK, T_SKY, T_ICE, T_LIT, T_HILL, T_SHARD) | **placeholder** — o tileset autoral gelado fica a declarar no contrato de asset |
| patterns sprite | mesma tabela (T_SHARD = tile 5, lido no slot 5) | 0 próprios | cena 01 não usa sprite (ver simulação) |
| name table | `SMS_PNTAddress` (reg@5 pela biblioteca), linhas montadas em `pnt_row_addr[]` :32×64 B | 24 visíveis de 32 construídas (a volta de 224 px pede as 8 extras) | revelação linha a linha |
| SAT | `SMS_SATAddress 0x7F00` (devkitSMS `SMSlib_common.c:19`) | 0 entradas nesta cena | `copySAT` enche o resto com 0xD0 |

### Orçamento worst-frame (MEDIDO — ver tabela-mãe)
| Item | Valor medido | Método da medição |
|------|--------------|-------------------|
| name table (revelação) | **1 linha/2 frames = 64 B por VBlank**; estado TITLE inteiro ≤ **34 linhas** | `peek_r14.txt` `ph_state_max_hud[0]=34`; degrau de bytes confirmado por `ph_wr_hud_max=128` (2×64 B) no pior frame da janela |
| `PSGFrame()` com `music_title` tocando | **9 linhas** | checkpoint `cp_wait→cp_stream`, `worst_frame_r13.json` `linhas_por_etapa.stream` |
| `PSGFrame+PSGSFXFrame` com chime | **9 linhas** (mesmo teto; o chime de 29 f cai na janela dos 3000 f selados) | idem — a janela inclui BOOT→TITLE com `sfx_chime` no frame 0 |
| input | **≤ 3 linhas** | `gi_max=3` |

- **Total worst-frame da cena**: 34 linhas de hud + 2 de sat + 9 de stream, com o
  teto global da janela em **58 linhas (64 corrigidas)** — a cena 01 **não** é a
  dona do pior frame (é a 03).
- **Headroom**: a leitura dura do instrumento é `vline_min = 203` (≥ 0xC0) e
  `vovf_delta = 0` nos 3000 frames. Claim suportado: *a janela nunca terminou na
  tela ativa*. Folga em linhas para a cena 01: o teto observado da cena é 34 de
  um trabalho que no pior frame global chega a 58 sem derramar.
- **Método**: contagem instrumentada na ROM (não estimativa), sessão privada
  `emulator_session.py`, DAP conectado **depois** do selo (L082).

### Sprites por scanline (pico)
zero sprites na cena 01 — a SAT custa 2 linhas (`copySAT` de tabela vazia, o
`0xD0` de descanso). Sem manifesto de sprite para simular.

### fps observado
no arco (não por cena): **59,67 / 59,69 / 59,80 / 59,69 / 59,81 / 59,62** —
6 janelas, ROM `f4f8ee3f`, `[PASS] boot / frame_advance / fps_constante` em
`out/evidence/sessions/5f3252122bfc4f558b0cdea87c984c16/runtime/runtime_probe_m3_fps6.json`.
Rota declarada do projeto: probe de runtime na RAM (L035/§37), não foco de janela.

## Cena 02 — aurora (FADE_DAWN + DAWN)
| Item | Valor medido | Método |
|------|--------------|--------|
| Fade de saída (rampa de atenuação até 15/15/15/15) | custa dentro de `apply_ramp()`, incluído nas **9 linhas** de stream; `game_step` do estado FADE_ECO é o teto global de `gd_max=42` | `peek_r14.txt` |
| Reescrita do mapa sob display off | **2 linhas/frame = 128 B** por VBlank (piso do `ph_wr_hud_max` medido), FADE_DAWN inteiro ≤ **29 linhas** | `worst_frame_r13.json` + `ph_state_max_hud[1]=29` |
| DAWN estática + `music_dawn` | ≤ **34 linhas** de hud, sat 2, stream 9 | tabela-mãe |
| Rampa de paleta (N cores × writes) | **não medida por writes** — o checkpoint não separa CRAM de name table dentro de `game_step` | ver "o que fica em aberto" abaixo |
| `Select` → `sfx_crystal` com música | pior frame observado **com o contador de SFX avançando em DAWN**: hud 34 + sat 2 + stream 9 (o SFX não cria linha nova de VBlank — `PSGSFXFrame()` já está no trecho de stream) | `out/logs/m3_arc_B_r13.log` B4 (`cnt_sfx_crystal=3`, `probe_state=2`) + tabela-mãe |

- **Pico de scanline**: sem sprites na cena (sat = 2 linhas de `copySAT` vazio).
- **Áudio (MEDIDO, mesma rota, ROM `f4f8ee3f`)**: `w2_dawn_continuous` 4,46 s —
  peak 2872, 89% ativo (`out/logs/audit_audio_w2_dawn_continuous.txt`);
  `w4_dawn_mix` peak 5646, **93% ativo [PASS]**; `w4b` (controle, zero presses)
  peak 5647, 89%. Bandas seladas em M2 para referência: dawn 5504, storm 6030.
  **Caveat obrigatório**: o ganho do host foi elevado no meio da campanha
  (pedido humano de 2026-10-14), então `w1/w2/w3*` (≈2900) e `w4*/w6` (≈5650)
  **não são comparáveis entre grupos**; a comparação válida é dentro do mesmo
  grupo de sessões, mesma janela e mesma rota.
- **Pause (SILENT) na cena 02**: `probe_frame` 476 → 920 (444 f de núcleo vivo)
  com **peak 0 / rms 0 / 0% ativo** (`out/escuta/w5_dawn_silent.audio.json`,
  `out/logs/m3_audio_W56_r13.log`) — silêncio autoral, não emulador congelado;
  reprise `w6` peak 5673 — 63,2% na métrica por amostra (`|a|>50` do `measure`
  da janela) e **89% de janelas ativas no gate** `audit_audio.py` sobre a mesma
  wav (`out/logs/audit_audio_w6_dawn_reprise.txt`): duas métricas, um arquivo.

## Cena 03 — tempestade (CUT_STORM + STORM)
| Item | Valor medido | Método |
|------|--------------|--------|
| CUT_STORM (2 frames, sem fade) | hud ≤ **28 linhas**; sat **não usável** (251 = wrap do delta, `src/main.c:1083`) | tabela-mãe + declaração acima |
| STORM inteira | hud ≤ **39 linhas**, sat **13 linhas** | `ph_state_max_hud[4]`, `ph_state_max_sat[4]` |
| `copySpritestoSAT` puro no blank | **11 linhas** (`sm_sat_lines`); scroll+wrap depois dela: **2 linhas** (`sm_tail_lines`) | sub-fases instrumentadas só na tempestade (`src/main.c:1091-1098`) |
| Build dos estilhaços | **71 linhas** — e isso é **tela ativa**, não VBlank | `sm_step_lines` (checkpoint `cp_a→cp_b` fora do blank) |
| `music_storm` + `sfx_crack` simultâneos | incluídos nas **9 linhas** de stream do pior frame global, que é **desta cena** (`ph_worst_state=4`) | `worst_frame_r13.json` |
| Pior frame total da janela | **58 linhas (64 corrigidas): 42 hud + 13 sat + 9 stream**, sem derrame (`vovf_delta=0`, `vline_min=203`, `spill_storm=0`) | idem |

- **Pico de sprites/scanline (MEDIDO)**: `{"sprites": 24, "peak_per_line": 6,
  "overflow_lines": 0, "violations": []}` — `[PASS] 24 sprites, pico 6/linha`,
  varredura integral do ciclo de 192 frames do manifesto da cena
  (`out/logs/sprite_line_sim_storm.txt` sobre `doc/scene_manifest_storm.json`,
  `audit_sprite_line_sim.py`). Headroom real: 6 dos 8 por linha, 24 das 64
  entradas — **a cena respira por declaração de direção (estilhaços), não por
  medo de orçamento**.
- **Áudio**: `storm` selado em M2 com 79,3% ativo / rms 1413 (tabela Trilha);
  a fome do ruído foi **medida e não observada**: nenhum frame do arco derramou
  e `sfx_crack` toca com a música rodando.

## Cena 04 — eco + créditos (FADE_ECO + ECHO + CREDITS + BLACK)
| Item | Valor medido | Método |
|------|--------------|--------|
| FADE_ECO (teardown: SAT zerada, flash zero, scroll zero) | `game_step` **42 linhas = o teto global da janela**, inteira 45 linhas; sat não usável (wrap) | `gd_max=42 / gd_state=5`, `ph_state_max_hud[5]=45` |
| ECHO | hud ≤ **27 linhas** (o estado mais barato da ROM), sat 2 | tabela-mãe |
| Rolagem de créditos (1 linha a cada 30 f) | hud ≤ **22 linhas** | `ph_credits_hud=22` |
| Silêncio final (BLACK, framebuffer vivo) | hud ≤ **28 linhas**, `probe_frame` segue avançando, FSM não trava | `ph_black_hud=28`, arco E (`m3_arc_E_r13.log`) |
| Gatilho `PSGGetStatus()==PSG_STOPPED` → CREDITS | observado no arco: `probe_playing` cai para 0 e a rolagem entra sem tecla | caso 1 de doc/17, `cnt_fade_dawn` 1→2→3 |

- **Áudio**: `eco` selado em M2 com 52,7% ativo / rms 256 — **passagem autoral
  quieta por construção**, o que é exatamente o caso que o piso de 90% do
  `audit_audio.py` reprovou hoje (`w1` 71% e `w2` 89% `[FAIL]` na rota do
  projeto). Pendência de curadoria humana (P2), registrada em doc/17, não
  escondida aqui.

## O que fica em aberto (medir antes de fechar a cena, não antes)
1. **VRAM do tileset autoral** (cenas 01–04): linha "patterns" desta tabela só
   fecha quando o model sheet virar `.res` com proveniência; hoje mede placeholder.
2. **Custo da rampa de paleta isolada**: os checkpoints atuais misturam CRAM e
   name table dentro de `game_step`. Degrau para medir: um checkpoint só de
   `PAL_*` no corredor vago.
3. **fps por cena parada**: medido no arco; não reclamado por cena.
4. **Áudio do caso 4 (SFX sobre a música)**: o canal é **substituído** pela PSGlib,
   então a energia total não muda (diferencial de RMS cego por construção —
   `out/logs/m3_caso4_diff_w4.txt`: 0 transientes, Δ máx +0,080 para 2 presses
   frame-atômicos). O que a máquina prova é contagem+estado; a audibilidade é
   caso de escuta humana (`tools/m3_escuta.py`).

## Regra de fechamento de cena
Nenhuma cena sai de "documentado" sem: VRAM declarada, worst-frame medido com
áudio tocando, fps ≥5 amostras, pico de scanline do simulador, e evidência
(wav+screen/vídeo) selada na sessão privada do emulador.

Estado contra essa regra (2026-10-14, ROM `f4f8ee3f`) — "parcial" aqui é o nome
honesto do que falta, não uma etapa cumprida:

| Cena | worst-frame c/ áudio | fps (arco, 6 janelas) | pico de scanline | evidência selada | VRAM declarada |
|------|----------------------|-----------------------|------------------|------------------|----------------|
| 01 título | medido | medido | n/a (0 sprites, sat 2 linhas) | vídeo E/B + wav W1 | **parcial** (patterns = placeholder) |
| 02 aurora | medido | medido | n/a (0 sprites) | wav W2/W4/W4B/W5/W6 + vídeo | **parcial** |
| 03 tempestade | medido (é o pior frame da janela) | medido | **medido** (24 sprites, pico 6/linha, 0 overflow) | vídeo E + wav storm M2 | **parcial** + tileset de estilhaço autoral pendente |
| 04 eco+créditos | medido (`gd_max=42` mora aqui) | medido | n/a (teardown zera a SAT) | vídeo E (2 voltas) + wav eco M2 | **parcial** |

Fechamento total das quatro cenas depende de **um só** item: o tileset autoral
convertido com proveniência declarada. Não há número escondido faltando.
