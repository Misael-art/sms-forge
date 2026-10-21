# 17-state-transition-contract — pulso_de_cristal

> Contrato de transição por aresta (skill `sms-state-transitions`). O que o
> GDD não prevê fica marcado fora de escopo, nunca "aprovado por silêncio".

## Owners globais (um dono por estado)
| Estado | Owner único |
|--------|-------------|
| `game_state`, `sub`, timers de transição | GAME_FSM |
| name table, tiles, mapa | VDP_FSM |
| CRAM (subpaletas + rampa + flash) | PAL_FSM |
| SAT/estilhaços | SPR_FSM (só cena 03) |
| stream musical, atenuações, SFX | AUDIO_FSM |
| medidor de compasso / contadores HUD | HUD_FSM |
| leitura de bordas de input | INPUT_FSM (fornece eventos; ninguém mais lê o port) |

## Arestas

### BOOT → TITLE
- gatilho: power-on; política de input: nada aceito até handler do 1º VBlank.
- saída: n/a (boot determinístico: probe zerado, preta, sem stream).
- entrada: AUDIO_FSM dispara `sfx_chime` no frame 0, rampa + `PSGPlay` no
  frame 45 (storyboard); VDP_FSM enfileira revelação linha a linha.
- persistente: n/a. resetado: tudo ao valor de boot.
- trabalho VDP: 24 linhas × 64 B = 1536 B num único frame de boot com
  **display OFF** (`title_write_dark`), depois revelação de 1 linha (64 B) a
  cada 2 frames por 48 frames — medido em `worst_frame_r*` (linha no VBlank
  vivo custa ~11–13 linhas de blank; ver 13-spec-cenas).
- recuperação: restart físico = mesmo boot (streams são dados).

### TITLE →(START)→ FADE_DAWN → DAWN
- gatilho: borda de subida de START, somente depois do prompt ativo.
- política de input durante a troca: START/SELECT descartados; PAUSE aceita.
- saída: AUDIO_FSM faz rampa `PSGSetMusicVolumeChannelsAttenuation` até
  15/15/15/15 (~1 s) → `PSGStop()`; VDP_FSM limpa timer de revelação;
  HUD_FSM congela medidor no fim da rampa.
- entrada: name table da cena 02 escrita sob **display off** (regra da skill
  VBlank: tela nova = mapa inteiro com display off, não revelação linha a
  linha em tela viva) em degraus de 2 linhas/frame (12 frames; `rewrite_step`),
  paleta da aurora, `PSGPlay(music_dawn)` no 1º frame após display on.
- persistente: contagem de ciclo. resetado: máscara de cristais não —
  atravessa (cristais acoram de dawn a eco; declarado no storyboard).
- trabalho VDP: 1 reescrita de mapa 1536 B (24 linhas × 64 B) distribuída em
  12 VBlanks; worst-frame = 2 linhas (128 B) + `PSGPlay` restart + 0 sprites
  — medido com probe de VBlank (ver 13-spec-cenas).
- recuperação: START repetido no meio da rampa não re-entra (estado
  `FADE_DAWN` ignora bordas até `DAWN`).

### DAWN →(START)→ CUT_STORM → STORM
- gatilho: START (borda). CUT: sem fade — a tempestade não pede licença.
- saída: `PSGStop()` no frame N; entrada: `PSGPlay(music_storm)` no frame
  N+1; name table/SAT inteiros substituídos com display off; flash off.
- persistente: contagem, máscara de cristais (não visível na 03).
- resetado: foco de cristal, timers de rampa.
- trabalho VDP: mapa 03 + upload de padrões de estilhaço (tiles próprios,
  slots fixos de VRAM declarados em spec-cenas) + SAT 24 × 4 B por frame.
- recuperação: reentrância idêntica (CUT é 2 frames, trivialmente reproduzível).

### STORM →(START)→ FADE_ECO → ECHO
- como TITLE→FADE_DAWN (fade por atenuação) mas com teardown extra
  OBRIGATÓRIO: `SPR_FSM` zera SAT e o pool de estilhaços; flash volta a zero;
  scroll zerado. Nada de sprite cruza para eco.

### ECHO →(fim do stream)→ CREDITS
- gatilho: `PSGGetStatus()==PSG_STOPPED` (stream único não-loop).
- saída: cristais seguem apagando na ordem inversa.
- entrada: rolagem de créditos (1 linha/30 f); HUD mostra compassos do ciclo.
- política de input: START/SELECT descartados; PAUSE aceita (SILENT).
- persistente: contagem de ciclo.

### CREDITS →(auto: eco terminada + rolagem completa)→ TITLE
- `PSGSilenceChannels()` → 120 frames de preto com framebuffer vivo →
  reentra TITLE exatamente pelo arco BOOT→TITLE (repetir o ciclo sem
  tecla presa é caso de teste, não esperança).

### PAUSE (qualquer ato) → SILENT → reprise
- gatilho: tecla Pause; saída: `PSGSilenceChannels()`; retomada:
  `PSGRestoreVolumes()` — repreeendida, não reiniciada (TDD).
- durante SILENT: VDP_FSM pausa timers de escrita (scroll, revelação,
  rolagem) mas mantém framebuffer; INPUT_FSM continua polindo bordas.

## Fora de escopo (GDD não prevê)
- retry/continue, seleção de ato, save, qualquer aresta a partir de GAME_OVER
  (não existe estado de derrota — experiência dirigida).

## Casos de teste de transição (evidência M3)
1. ciclo completo TITLE→…→CREDITS→TITLE ×2 sem tecla presa (input script +
   probe `probe_track/probe_playing` + vídeo do framebuffer).
2. START spam durante FADE (não re-entra), SELECT durante CUT (não dispara
   SFX — SFX só em DAWN com cristal em foco), Pause em cada ato.
3. worst-frame de cada transição medido (probe_vline/vovf) — wovf não pode
   avançar em nenhum arco.
4. SELECT→`sfx_crystal` com `music_dawn` tocando: captura de áudio isolada
   provando o ataque no ch1 e retomada do arpejo (arbitração L041/§12).

## Veredites M3 (medido 2026-10-14)

Cadeia de ROMs: `ba933b0b…` e `9f5f8bdf…` são tomadas **pré-correção** do
áudio; `f4f8ee3f4c2a720a1da696fe7a84235a787cc1edeba5d0eb25d9592f5b2eb331` é a
ROM atual e a única dona das evidências desta seção, salvo onde indicado.

**Causa raiz do eixo de áudio (medida, não sentida).** `PSGSetMusicVolumeChannelsAttenuation`
é um **SET dos quatro nibbles do mixer**, não um estado por faixa. O fade-out de
saída deixava att=15/15/15/15 armado e a cena seguinte começava muda: as
capturas pré-correção na mesma rota davam `audio_m3_title_dawn.wav` peak=0 e
`audio_m3_dawn_select.wav` peak=1995 / ativo=2% (`out/logs/capture_m3_run1.log`,
`capture_m3_run2.log`). A correção escreveu att=0 explícito em `music_enter()`
e simetricamente nos fades. Pós-correção, na **mesma rota e métrica**: W1 peak
2937, W2 peak 2872, W4 peak 5646 / ativo 93% (`audit_audio.py`). A hipótese
"host faminto" está refutada por medição: o caminho não mudou, o nível voltou à
banda do M2 (dawn 5504 / storm 6030 de peak).

### Caso 1 — ciclo completo ×2 sem tecla presa: **PASS**
Sessão `723c4f52eda047e4a9b5444b9b95ce01`, 8 segmentos × 900 f = 7200 f de
vídeo do framebuffer (`out/evidence/m3/m3_arc_e1..e8.mp4`, playback 59,9227 Hz,
quadros distintos por segmento 59/562/95/54/603/99/48/609 — nenhum congelado).
Sondas por segmento: `probe_state` 4→6→8→2→6→8→2→6, `probe_track` 2,3,4,1,3,4,1,3,
`probe_playing` 1 nas cenas e 0 só em BLACK (silêncio como escolha). A volta
completa é provada por contador, não por relógio: `cnt_fade_dawn` 1→2 (f3762)→3
(f6502) e `cnt_cut_storm` 1→2 (f4674)→3 (f7415) — cada FADE_DAWN depois do
primeiro exige ter atravessado CREDITS→BLACK→TITLE. `p1=p2=console=0` em todas
as sondas e `probe_attract=1` o tempo todo: ninguém tocou em nada.
Log: `out/logs/m3_arc_E_r13.log`.

### Caso 2 — spam e Pause: **PASS** nas três cláusulas
Sessão `4246092d3447447090d6d8884f44a113` (`out/logs/m3_arc_B_r13.log`),
roteiros frame-atômicos da ponte, estado lido antes de qualquer afirmação:
- **START spam durante o fade**: 6 bordas de 2 f em `FADE_DAWN` → `cnt_fade_dawn`
  permanece **1** e `probe_state` permanece **1**. A aresta não re-entra.
- **SELECT fora de DAWN**: em DAWN, 3 SELECT sobem `cnt_sfx_crystal` para 3;
  depois de `START→CUT→STORM` (`cnt_cut_storm=1`, `probe_state=4`), 4 SELECT
  não sobem o contador (**3**). Em TITLE, SELECT não gera contador nenhum.
- **Pause em cada ato**: a ponte injeta o Pause **físico** do console (bit 0 de
  `console` = `SMSKEY_PAUSE` no `ForgeSMS.java` da sessão), que a ROM lê por NMI
  em `SMS_queryPauseRequested()`. Matriz `out/logs/m3_pause_F_r13.log`, segurar
  700 f em SILENT: TITLE state 0 frame 67→771; DAWN state 2 frame 445→1149;
  STORM state 4 frame 2083→2787; ECHO state 6 frame 3700→4404. Em todos os
  quatro, `probe_state` **não mudou** (FSM congelada) enquanto `probe_frame`
  avançou o passo pedido (framebuffer vivo, FSM não travou); ao soltar, o arco
  retomou sozinho (0→4, 2→4, 4→6, 6→1 em ≤900 f).
- **SILENT é audível como silêncio, não como emulador parado**: janela W5
  (sessão `aa15f770…`, 4 s de captura com **zero** input dentro dela, Pause
  acionado antes) mede peak=0 / rms=0,0 / ativo 0% **enquanto** `probe_frame`
  vai de 476 a 920 (+444 f) e `probe_state` permanece 2 — o núcleo rodou e o
  silêncio mesmo assim saiu, logo é silêncio autoral (`PSGSilenceChannels`), não
  emulador congelado. W6 (sessão `7a5584db…`) é a reprise: solto antes da
  janela, mesma `music_dawn`, peak 5673 / rms 1120 / ativo 63,2%. **Nota de
  instrumento:** 63,2% vem da métrica por amostra (`|a|>50`) do `measure` da
  janela; a MESMA wav no gate `audit_audio.py` (janelas acima do piso de RMS) dá
  **89%**, `[FAIL] mix fraco < 90%` (`out/logs/audit_audio_w6_dawn_reprise.txt`).
  São duas métricas diferentes sobre o mesmo arquivo, não duas medições
  conflitantes — cito as duas para que nenhuma vire número órfão. As janelas
  estão seladas em `out/escuta/w5_dawn_silent.*` e `w6_dawn_reprise.*`
  com `rom_sha256=f4f8ee3f…`; se a reprise reiniciou a faixa ou continuou do
  ponto é julgamento de ouvido (W6 na cabine), não desta métrica.

### Caso 3 — worst-frame do arco: **PASS, com pico por estado medido**
`out/evidence/worst_frame_r13.json`, ROM `f4f8ee3f…`, janela selada de 3000 f
(ROM em f5676), `veredito=pass`, `vovf_delta=0`, `vline_min=203` (limiar da
ferramenta 0xC0=192), `perfil_vcounter` do snapshot: wait 194 / hud 230 / sat
243 / stream 252 → 42+13+9 = **64 linhas de VBlank consumidas** no frame
amostrado, `spill_max=0`. A janela é a atração, que exercita o arco inteiro por
auto-avanço (`src/main.c:687,732,767,808`), então o `vovf` — contador da própria
ROM, imune a amostragem — cobre as quatro cenas.

**A limitação declarada nesta seção em r13 foi superada pela leitura por estado**
(`tools/lwb_peek.py --wait 100` → `out/logs/peek_r14.txt`, ROM `f4f8ee3f`,
`frame=6289`, `done=1`): os nove contadores `spill_*` **e** os quatro `spill_st_*`
(tail/input/hud/sat/stream) valem **0**, e `ph_state_max_hud[0..6]` +
`ph_credits_hud` + `ph_black_hud` dão o pico de linhas da metade "escritas"
**por cena** (34/29/34/28/39/45/27/22/28). O pior frame da janela tem nome:
`ph_worst_total=58` linhas (`wait→stream`, módulo 256; 64 corrigidas pelo
instrumento), `ph_worst_state=4` (STORM), `ph_worst_stage=1` (escritas de
nome/paleta). Portanto o claim agora é o forte: **"nenhum frame de nenhuma das
nove faixas do arco derramou, e o pico por faixa está medido"**.

O que essa leitura **não** sustenta, declarado para não virar lenda:
`ph_state_max_sat[3]` e `[5]` valem 251 = artefato do delta `cp_sat − cp_hud` em
módulo 256 quando o checkpoint não é alcançado na cena (`src/main.c:1083`);
`ph_stream_max=255` é o mesmo artefato (:1084). Nenhum dos três é custo de VBlank
e nenhum aparece em `13-spec-cenas` como número.

### Caso 4 — SELECT sobre `music_dawn`: **contadores e captura PASS; diferencial de energia é cego ao método**
- Disparo: em DAWN com `music_dawn` tocando, `cnt_sfx_crystal` 0→2 com estado
  verificado por sonda antes e depois da janela (W3/W4).
- Audibilidade instrumental: `audit_audio.py` na captura de sink isolado —
  W4 (mix com dois SELECT) peak 5646 / ativo 93% **PASS**; W4B (mesmo roteiro de
  frames, SELECT sempre 0) peak 5647 / ativo 89%, `cnt_sfx_crystal=0`.
- Diferencial WITH/CONTROL (`tools/m3_caso4_diff.py`, `--self-check` passando:
  `out/logs/m3_caso4_diff_selfcheck.txt`) **reprovou o método, não a ROM**:
  presses de parede (W3) dão 8 transientes para 2 presses esperados; presses
  frame-atômicos (W4) dão **0** transientes, delta máximo +0.080. Explicação
  coerente com o código: a arbitração do PSGlib **substitui** o canal 1 durante
  o SFX em vez de somar energia, então a envoltória RMS mal muda e a diferença
  de energia não é instrumento para "ouvi o ataque?". A audibilidade fica
  delegada ao julgamento humano na cabine (`tools/m3_escuta.py --open`), que é
  o único instrumento que sabe a diferença entre timbre e nível.
  Registro como candidato de curadoria: *medida de energia não prova SFX sob
  arbitração de substituição de canal*.

