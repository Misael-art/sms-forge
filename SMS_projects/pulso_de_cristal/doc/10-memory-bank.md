# 10-memory-bank — pulso_de_cristal

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
2026-10-15 (madrugada) — **Os dois atos pendentes foram executados na ordem do
dono ("FACA 1 E 2").** (1) **Cabine aberta para a escuta dele**: `--open`
regenerou `out/escuta/m3_escuta.html` (8 janelas, 5,2 MB, ROM `f4f8ee3f`) e o
`xdg-open` entregou ao Chrome GUI da sessão; re-`--verify` depois de regenerar:
`[PASS]` byte-idêntico, exit 0. Continua **não** existindo
`out/logs/m3_escuta_verdict.json` — ouvido é do dono, e `--collect` ainda espera o
export dele. (2) **A lição L133 da sessão A9 foi RESTAURADA pela rota (a)**, com
prova: o conteúdo é o `tool_use Write` (linha 2657) + `Edit` (2670) da transcrição
dela, aplicados programaticamente, e o SHA da reconstrução é
`7e725673c543b0328d5280efada085c12d2067221e8d4dc2c9df1cda7eaef108` — **igual ao
SHA que a própria A9 pregou em `lesson_routes.application_records` antes do dano**.
7273 B em disco, JSON válido, 1 lição. O veredito de 37 B foi preservado como
evidência em `rascunho/curation_backup/2026-10-14_l133_CLOBBED_37b.json`.
`audit_learning_capture.py --root .` saiu de exit 1 (3 derivações) para **exit 0
por dados restaurados** — gate e prosa próprios não foram editados para verde.
Nada foi commitado: `HEAD` ainda carrega os 37 B naquele caminho, então a
restauração vive no working tree e comitar é decisão dele. Dossiê agora com **10
candidatos / 7 armadilhas / 6 emendas**, sha `5b5fb17e…` rebincado nas routes;
cadeia estendida com `restauracao_l133_rota_a`. `audit_doc_sync.py` está exit 1
com 10 derivações, **todas** `luta_mugen` por `Errno 5` (EIO do cartão), zero
relacionadas a este projeto — atribuído, não consertado.

2026-10-14 (noite) — **M3: só falta a escuta humana, e o instrumento dela agora é
verificado.** Cabine `tools/m3_escuta.py` ganhou `--verify`, `--collect` e
`--self-check`: as 8 janelas servidas são byte-idênticas à evidência hasheada e o
veredito exportado **só pousa** em `out/logs/` depois do `--collect`, com binding
de ROM+SHA (antes o doc prometia um caminho que nenhum código escrevia). **Ainda
não existe `out/logs/m3_escuta_verdict.json`: a escuta não aconteceu** — o que se
claima aqui é que o canal do veredito está aberto e provado, não que houve
veredito. Dossiê de curadoria emendado
(9 candidatos no total, 7 armadilhas, 4 emendas; `--json`-como-destino medido em **13** ferramentas e reproduzido ao vivo em arquivo de outra sessao;
registry corrigido para **L133/§124**, foto da manhã dizia L132). Sonda de arte
re-feita hoje: mesmo `403 code 112`, nenhum pixel novo.

2026-10-14 (fim de tarde) — **M3: eixo de áudio destravado e provado na ROM
entregue; falta só a escuta humana.** O bloqueio de 0–16% que este arquivo
registrava abaixo foi **refutado por medida, não por hopeful thinking**: a causa
era na ROM (`PSGSetMusicVolumeChannelsAttenuation` é **SET** dos quatro nibbles
do mixer, não estado por faixa → o fade de saída deixava atenuação 15 armada e a
cena seguinte começava muda), e o ganho do host foi elevado pelo dono a pedido.
Na mesma rota e métrica: pré-correção `peak=0` e `peak=1995 / ativo 2%`
(`capture_m3_run1/2.log`) → pós-correção `peak 2937/2872/5646`, `ativo
71/89/93%`, de volta à banda selada no M2 (dawn 5504, storm 6030). ROM atual
**`f4f8ee3f4c2a720a1da696fe7a84235a787cc1edeba5d0eb25d9592f5b2eb331`** (16384 B).

Os quatro casos de transição de `doc/17` estão fechados com veredites escritos
em `doc/17-state-transition-contract.md` (§ Veredites M3):
- **caso 1** arco ×2 em atração sem tecla presa — 8×900 f = 7200 f,
  `cnt_fade_dawn` 1→2→3 e `cnt_cut_storm` 1→2→3 (prova de *re-entrada*, não de
  relógio), 8 mp4 de framebuffer distintos 48–603, `m3_arc_E_r13.log`;
- **caso 2** spam de START no fade não re-entra; SELECT fora da aurora não
  dispara; **matriz de Pause nos quatro atos** (`m3_pause_F_r13.log`) e o
  discriminante W5/W6: `peak=0 / rms=0` **enquanto** `probe_frame` 476→920 —
  silêncio autoral, núcleo vivo;
- **caso 3** pior-frame re-selado na ROM entregue (`worst_frame_r13.json`:
  `pass`, `vovf_delta=0`, `vline_min=203`) **e** com pico por estado
  (`peek_r14.txt`: `ph_state_max_hud` 34/29/34/28/39/45/27/22/28, nove `spill_*`
  e quatro `spill_st_*` em **0**, pior frame 58 linhas cruas = 64 corrigidas em
  STORM);
- **caso 4** contadores+captura PASS (W4 93% ativo PASS vs W4B controle 89%,
  `cnt_sfx_crystal` 0→2 com `probe_state` verificado), **diferencial de energia
  reprovou o método**: arbitração PSGlib substitui o canal em vez de somar
  energia, logo RMS não é instrumento de audibilidade — delegado à cabine.
fps re-selado com **6 janelas** (59,67/59,69/59,80/59,69/59,81/59,62) para
satisfazer "≥5 amostras" pela rota declarada do projeto (probe SMRT via DAP).
`doc/13-spec-cenas.md` está **preenchido com os números medidos** das quatro
cenas, com as leituras-inválidas declaradas (`ph_state_max_sat[3]/[5]=251` e
`ph_stream_max=255` são wraps de delta módulo 256, não custo) e a VRAM de
patterns marcada como **placeholder** até o tileset autoral.

O eixo de áudio passou de "sem lastro" a **derivado pelo próprio harness**: as
oito janelas W1–W6 foram publicadas em `out/evidence/` com `cp -p` (mesma data
em que nasceram) e binding hasheado em `out/evidence/audio_m3_manifest.json`
(7 com `peak>0`; `w5` é o silêncio autoral, `peak=0`, publicado por
completude e sozinho não sustenta nada). No build seguinte, `build_inner.py`
DERIVOU `axes.audio=true` dos artefatos e `reconcile_claims.py` fechou
`[PASS] eixos declarados batem com os artefatos de evidencia` — sem editar
`build_record.json` à mão. A rota privada publica as capturas no bundle
(`out/evidence/sessions/<id>/`), e o glob do eixo lê `out/evidence/*.wav`
(não-recursivo): a lacuna é de **destino**, não de medida; por isso copiei em
vez de inventar arquivo, e o `tools/m3_audio_windows.sh` agora publica nos dois
lugares.

O que falta para M3 virar "fechada": **(a)** escuta humana das janelas W1–W6
(`tools/m3_escuta.py --open`, um comando, veredito exportável) e **(b)** o
tileset autoral das cenas. Pendência de curadoria humana: o piso de 90% do
`audit_audio.py` rejeita passagens quietas autorais (eco 52,7%, w1 71%, w2 89%)
— item P2, não aplicado.

### Registro anterior (2026-10-14, manhã) — preservado, supera-se por medida acima
**M3 em curso, metade ROM-side provada, metade de áudio bloqueada
no host.** Prova da própria ROM (`out/logs/capture_m3_run2.log`): spam de 6
START durante o fade registra **1** entrada de transição; SELECT só produz
`sfx_crystal` na aurora (3 toques = 3; em STORM o contador **não cresce**);
arco completo título→fade→aurora→corte→tempestade observado por contadores em
`0xC990–0xC996` + `probe_state`. fps 59,67 (janelas 59,67/59,64/59,83,
spread 0,19) com boot/frame_advance PASS e `check-bundle` PASS
(ROM `ba933b0b…`). Orçamento de VBlank **fechado por degraus medidos**
(r6→r12): transições a **2 linhas/frame** (12 frames) cabem; 3 linhas derramam.
Pior-frame selado: `vovf_delta 0`, `vline_min 203`, 64 linhas de blank
consumidas de ~66 físicas (raw 58 + correção de serial do VCounter) —
**mas selado na ROM `9f5f8bdf`; re-selo em `ba933b0b` é dívida declarada**.
Cena 03: 24 estilhaços na SAT, pico **6/scanline**, 0 overflow, 0 colisão com
`0xD0` (`out/logs/sprite_line_sim_storm.txt`). Corredor de sondas relocado para
`0xC900` com aprovação humana e gate `audit_probe_corridor.py`
(sondas=87 folga=383 PASS). Trilha medida: 7079 B de 16384 B (43,2%) e
`ruido_branco = 1.0` nas 3 faixas com percussão, após defeito do bit2 corrigido
no emissor (L079/§64). **BLOQUEIO (refutado acima):** 8 janelas de captura
isolada deram 0–16% de amostras ativas com rota `verified=True`, sink 100%, ROM
a ~60 fps e `probe_playing=1` (o monitor do sink privado da própria sessão
reproduziu); `audit_audio` encerrou `[OK] peak=1995` + `[FAIL] mix fraco: 2%
ativo < 90%`.
Candidatos e lições registrados em
`doc/curation/2026-10-14_pulso_m3_candidatos_curadoria.json` (nenhum ID novo
emitido, wrapper e SMS_GLOBAL intocados).

Histórico M1/M2 (2026-10-12): M1 fechada com escuta humana aprovada
("testei, funcionou, prossiga"). M2: 7 ativos emitidos por composição autoral
(`music_dawn` 1789B/1920f, `music_storm` 1808B/896f, `music_eco` 1453B/1728f,
SFX `crystal`/`crack`/`chime` 27/23/23B), gates `audit_psg_quality` 0/7
reprovados, `audit_audio_provenance` PASS, `audit_psg_channel_binding` PASS.
ROM jukebox buildada `5a8a8c9f…` e observada na sessão `73f1655ab5cf4514…`
(check-bundle PASS, fps 59,79, áudio isolado das 4 faixas musicais 17–35 s,
peak>0). Escuta humana das faixas novas: aprovada em 2026-10-12 ("prossiga").

## Eixos de entrega (7) — gate final exige os 7 simultâneos
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | `out/rom/pulso_de_cristal.sms` 16384 B sha `f4f8ee3f…` (FSM M3 + correção da atenuação + sondas no corredor `0xC900`) |
| validation_report | testado_em_emulador | `check-bundle` PASS na sessão `4246092d3447447090d6d8884f44a113` (ROM `f4f8ee3f`, `out/logs/m3_arc_B_r13.log`); `audit_sprite_line_sim` cena 03 PASS; `audit_probe_corridor` PASS; proveniência/binding PASS; piso 0/7 reprovados (`out/logs/psg_quality_m3b.json`) |
| boot no emulador | testado_em_emulador | `m3_dawn.png` no bundle `4246092d…/` (estado 2 = aurora, sonda `probe_state=2` lida no mesmo frame) |
| gameplay | testado_em_emulador | casos 1–4 de doc/17 fechados com veredite: arco ×2 sem tecla presa (`m3_arc_E_r13.log`, 8 mp4), spam/gate/matriz de Pause (`m3_arc_B_r13.log`, `m3_pause_F_r13.log`), SFX com estado verificado |
| 60/50 fps | testado_em_emulador | `…/5f325212…/runtime/runtime_probe_m3_fps6.json`: **6 janelas** 59,67/59,69/59,80/59,69/59,81/59,62 + `[PASS] boot / frame_advance / fps_constante` |
| orçamento de frame | **validado_budget (dívida paga)** | `out/evidence/worst_frame_r13.json` re-selado na ROM `f4f8ee3f` (`pass`, `vovf_delta=0`, `vline_min=203`) + pico por estado em `out/logs/peek_r14.txt`; preenchido em `doc/13-spec-cenas.md` |
| áudio | testado_em_emulador, **escuta humana pendente** | 8 janelas W1–W6 com `rom_sha256=f4f8ee3f` em `out/escuta/*.audio.json`: dawn 2872–5646 peak, `w4_dawn_mix` **93% ativo [PASS]**; W5 prova o silêncio autoral com núcleo vivo (`probe_frame` 476→920, peak 0); W6 reprise peak 5673. **Não** se claima "soa bem": a cabine (`tools/m3_escuta.py --open`) ainda não devolveu veredito, e o diferencial de energia é cego à substituição de canal |
| memory bank atualizado | este arquivo, 2026-10-14 (fim de tarde) | — |

**O que o harness deriva, hoje** (`out/build_record.json` axes, mesma fonte de
`reconcile_claims.axis_support`): `build`+`validation_report`+`audio`+
`memory_bank_atualizado` = **true por artefato**; `boot_emulador`, `gameplay` e
`fps_constante` = **false por destino do artefato, não por falta de medida**. A
medição existe e está casada com a ROM entregue — `informative=true` no bundle
`4246092d…/capture.json` (sha `f4f8ee3f`) e `fps_constante=true` em
`5f325212…/runtime/runtime_probe_m3_fps6.json` — mas os três eixos lêem os
caminhos da **rota desktop** (`out/evidence/evidence.json`, `out/evidence/fps.json`,
`out/evidence/input_memory.json`), e `capture_evidence.py --session` publica
apenas em `out/evidence/sessions/<id>/`. Fechar esses eixos exige decisão de
curadoria (o wrapper ler o bundle, ou uma rota declarada de publish), não
escrever JSON conjectural em `out/evidence/`. Registrado como candidato em
`doc/curation/2026-10-14_pulso_m3_candidatos_curadoria.json`; nada do wrapper foi
tocado.

> Status válidos: `não iniciado`, `documentado`, `implementado`, `buildado`,
> `testado_em_emulador`, `validado_budget`. Toda linha diferente de
> "não iniciado" EXIGE prova citada (caminho de arquivo/captura), não prosa.

## Decisões registradas
- Alvo = PSG SN76489 no SMSForge; forma = jogo-demo musical dirigido; trilha =
  autoral (decisões humanas confirmadas na sessão de planejamento, 2026-10-12).
- `specialization` fica `indefinido` em `.mddev/project.json`: não há família
  `musical_experience` na matriz de gêneros — declarado, não omitido (GDD).
- Arbitração SFX (TDD): SFX nunca no ch3; `sfx_crystal`/`sfx_crack` →
  `SFX_CHANNEL1`, `sfx_chime` → `SFX_CHANNEL2` (apenas cena 01). Literais
  alinhados a `audit_psg_channel_binding.py`.
- Semântica de playback verificada na fonte upstream: `PSGPlay` = loop
  infinito; `PSGPlayNoRepeat` = para no loop (gatilho de créditos via
  `PSGGetStatus`). Header devkitSMS (autoridade #8) lido 2026-10-12.
- Composição autoral: partitura JSON (superfície musical) → emissor
  determinístico local com `--self-check`, validando M1–M7 por construção e
  medindo o binário com `audit_psg_quality.py` (precedente:
  `MSSF2T/tools/gen_music_ken_ref.py`, `make_psg_assets.py`).
- FPS medido pela rota do runbook (probe SMRT via DAP), não `measure_fps.py`
  — sessão privada oculta não tem janela para o título. Precedente kage_matsuri.
- `measure_runtime_probe.py --out` NÃO pode apontar para dentro de
  `out/evidence/sessions/<id>` antes da publicação: a pasta pré-criada faz
  `publish()` reprovar com "session already published". Artefatos de runtime
  vivem em `out/logs/`; o bundle da sessão fica reservado ao capture_evidence.
  (M2 refine: a rota correta é publish FIRST, probe depois — o probe escreve
  `runtime/` dentro do bundle selado e o check-bundle ignora subdir extra.)
- Jukebox M2 troca de faixa por BORDA DE SUBIDA do joypad (sem isto, o mask
  segurado por N frames do script de input avança N faixas) e playback em
  `PSGPlay` (loop) em vez de `PSGPlayNoRepeat`: o warmup de 1,5 s do
  `capture_audio` (L048) comia a cabeça da faixa; com loop, toda janela
  ≥ duração+2 s contém uma passada completa. Gatilho definitivo de fim de
  faixa pertence ao M3.
- `capture_evidence.py` sem `--project` publica em CWD: a primeira tomada M2
  vazou o bundle para a raiz do workspace; consolidado no projeto e o script
  `tools/capture_m2_jukebox.sh` agora faz `cd` no projeto.
- Prova de emulador dos 3 SFX fica declaradamente para o M3 (arbitração
  SFX-sobre-música); na M2 os SFX têm piso medido + binding de canal +
  audição por pré-escuta numpy rotulada no player.

## Blocker dominante atual
**Escuta humana do arco (o único eixo que falta a M3):** as oito janelas
W1–W6+M2 estão capturadas, com rota `verified` e `rom_sha256=f4f8ee3f`, e a
máquina já disse o que pode dizer (nível, % ativo, estado da FSM no mesmo frame,
contadores de SFX). O que nenhuma métrica de energia diz é *se o ataque do
`sfx_crystal` se ouve sobre o arpejo* — a arbitração PSGlib **substitui** o canal
em vez de somar, então a cabine é o instrumento correto. Dois comandos, e a
ordem importa:
```
python3 tools/m3_escuta.py --verify    # o que a cabine serve == a evidencia hasheada
python3 tools/m3_escuta.py --open      # ouvir e exportar o veredito
python3 tools/m3_escuta.py --collect   # ingere o download de volta ao projeto
```
O `--collect` existe porque a cabine só *baixava* `m3_escuta_verdict.json`; sem
ele a linha abaixo prometeria um caminho que nenhum código escrevia. A ingestão
recusa ROM divergente, cabine velha (`gerado_em`), wav com SHA trocado, janela
não julgada e veredito fora do vocabulário — provado por `--self-check` (6
casos, 4 de rejeição) sem escrever dentro de `out/`. Ajuste musical pós-escuta
SÓ na partitura JSON.

**Bloqueio de destino (não de medida) para os outros três eixos:** `boot_emulador`,
`gameplay` e `fps_constante` seguem `false` no `build_record` porque o
`axis_support` só conhece os caminhos da rota desktop, enquanto este projeto roda
pela rota de sessão privada (SMS_GLOBAL §93). A medida existe, tem SHA da ROM
entregue e passou em `check-bundle`; o que falta é uma decisão de curadoria sobre
onde o harness deve olhar. O agente **não** fabrica `evidence.json`/`fps.json` para
verde.

**Bloqueio paralelo (arte):** cena 01 e demais cenas seguem com canal nativo de
geração de imagem bloqueado — **re-sondado em 2026-10-14 à noite** (não por
memória): ImageGen callable com o prompt verbatim de
`rascunho/art_prompts/cena01_vale_concept_v1.txt` devolveu o mesmo `403 code 112`
(billing hard limit, client=qoder). Sondas anteriores: duas em 2026-10-12.
Tomada registrada em `out/logs/generation_channel_decision.json`
(`probe_history[0]`, `last_probe_date=2026-10-14`); direção e retry lossless
continuam lá, e o mesmo canal funcionou no irmão master_of_fighters em
2026-10-11. Consequência medida: as linhas
"patterns" de `doc/13-spec-cenas.md` ficam **parciais** — o tileset em ROM hoje é
6 tiles de placeholder (`SMS_loadTiles` :916), e fechar VRAM de cena sobre
placeholder seria promover boot a entrega (L036/§39). Nenhum pixel novo foi
gerado, e `procedural_renderer` não foi usado como fonte final.

**Bloqueio encerrado nesta data (registrado para não virar lenda):**
*Captura de áudio no host (manhã de 2026-10-14): 8 janelas a 0–16% ativo com
rota `verified=True`.* **REFUTADO por medida**, não por hopeful thinking: a causa
era de ROM (`PSGSetMusicVolumeChannelsAttenuation` = SET dos nibbles do mixer, o
fade deixava atenuação 15 armada) somada ao ganho do host elevado pelo dono.
Mesma rota, mesma métrica: `peak=0`/`peak=1995, ativo 2%` → `peak 2872–5646,
ativo 71–93%`, dentro da banda selada no M2. Nada no serviço de áudio do host foi
alterado por agente. Triagem preservada em
`doc/curation/2026-10-14_pulso_m3_candidatos_curadoria.json`.

**Risco de host fora deste projeto:** `SMS_projects/luta_mugen/doc/` está
ilegível com *Erro de entrada/saída* (reproduzido duas vezes em 2026-10-14),
enquanto o resto do repo lê. Nenhum reparo tentado; exige verificação do meio e
restauração do git/backup antes de qualquer trabalho naquele projeto.

## Lições abertas
- Candidatos da sessão M3 registrados **sem ID novo** em
  `doc/curation/2026-10-14_pulso_m3_candidatos_curadoria.json` (hoje **10**
  candidatos + 7 armadilhas de harness + 6 emendas; `lessons` continua vazia e o
  **registry está em L133** — medido 2026-10-14 à noite em
  `doc/curation/id_registry.json`, com §124 na doutrina; a foto "L132" deste
  dossier era a manhã, e outra sessão aplicou o item SMSPower A9 no mesmo dia) e
  entradas correspondentes no ledger
  (`doc/agent_learning/learning_ledger.json`, **93** agora) com `application_records`
  em `lesson_routes.json`: dois candidatos a lição (SET de atenuação PSGlib com
  sentinela que deixa −12 dB em vigor; máscaras de porta/pausas da ponte e
  checagem negativa vazia), aplicações de L061/L079/L082/L089/L057/L128/L129 com
  evidência hasheada, os quatro candidatos da tarde (energia cega à substituição
  de canal, delta de VCounter módulo 256, silêncio autoral que aborta o gate,
  sonda que pausa o núcleo), o candidato do destino dos eixos, e os dois da noite:
  **`--json` é destino de relatório em 13 ferramentas sem nenhuma guarda** e
  **gate humano precisa de `--verify` + ingestão casada por SHA**, e o décimo
  (**hash pré-desastre registrado é a única prova de restauração**).
  O bloqueio de áudio que esta linha registrava como "risco aberto" foi
  **refutado por medida** à tarde (ver § Blocker dominante) — preservado no
  dossiê como histórico, não como estado.
- **Clobber de dossiê, restaurado e declarado:** às 20:34
  `audit_learning_capture.py --root . --json <caminho-do-dossiê>` escreveu o
  veredito de 37 bytes **por cima** dos 19.179 chars do dossiê — nessa ferramenta
  `--json` é destino do relatório (`open(a.json,"w")`), não seletor de leitura, e
  não recusa caminho pré-existente. O arquivo não estava no git. Restauração:
  base extraído do transcript da sessão + replay do mesmo script de emenda, com a
  cadeia de SHA registrada em `lesson_routes…restore_chain`
  (`3f809a8a` manhã → `a3a4b215` emenda nunca registrada → clobber → `cc7c3e25`
  replay → `a4f05d35` restaurado → `cace0005` emenda da noite → `b3bcd006` registro
  da segunda instância ao vivo (abaixo); a cadeia completa está em
  `lesson_routes.json…restore_chain`, e o sha que o gate confere é o do registro).
  Diferença declarada:
  os hashes de evidência foram recomputados na restauração. `audit_learning_capture.py`
  roda **sem** `--json` daqui pra frente — e a medição da noite mostra que a regra
  é mais larga que esta ferramenta: 13 no wrapper com o mesmo formato.
- **Segunda instância da armadilha, ao vivo e em arquivo de outra sessão (23:33)
  — RESTAURADA 23:58 pela rota (a):**
  `doc/curation/2026-10-14_l133_vram_map_reg6_sprite_window_free_pockets.json`
  — lição emitida por **outra** sessão (A9/SMSPower) — virou **37 bytes**,
  sha256 `89924049…`, conteúdo `{ "problems": [], "clean": true }`: veredito de
  auditoria morando no lugar da lição. E o git **não** a salvou: o veredito foi
  commitado (`74543b9`), então `HEAD` == dano. Consequência medida na hora:
  `audit_learning_capture.py --root .` (sem `--json`) devolvia deriva **vermelha
  no repo inteiro** porque a linha em `lesson_routes.json` aponta para esse
  caminho. Às 23:38 esta sessão registrou o fato e **não** tocou no arquivo
  alheio, com a justificativa literal de que "não temos o texto original"; essa
  justificativa era verdadeira naquele minuto e deixou de ser dez minutos depois,
  quando se achou a fonte.
  **Restauração executada após "FACA 1 E 2":** conteúdo = `tool_use Write`
  (linha 2657) + `Edit` (linha 2670) da transcrição da própria A9
  (`eb043711-fae6-4b1d-b59a-0395b2ae588f.jsonl`), aplicados programaticamente
  com `assert` de `old_string` único e JSON válido — esta sessão **não redigiu
  nenhuma linha de lição**. Prova de byte-exatidão: sha da reconstrução ==
  `7e725673c543b0328d5280efada085c12d2067221e8d4dc2c9df1cda7eaef108`, que é o
  SHA que a A9 tinha pregado em `lesson_routes.application_records` **antes** do
  dano (comando da linha 2675). Disco: 7273 B, 1 lição L133. Gate: exit 1 (3
  derivações) → **exit 0** por dados restaurados, sem editar gate nem prosa
  alheia. O veredito de 37 B ficou preservado como evidência em
  `rascunho/curation_backup/2026-10-14_l133_CLOBBED_37b.json`. **Nada commitado**:
  `HEAD` ainda tem os 37 B, então a restauração está no working tree e comitar é
  decisão do dono. Cadeia: `lesson_routes…restore_chain.restauracao_l133_rota_a`.
  Mitigação prática adotada (não espera a curadoria): este dossier tem cópia
  hasheada em `rascunho/curation_backup/2026-10-14_pulso_m3_candidatos_b3bcd006.json`
  — sha256 idêntico ao arquivo canônico (`b3bcd006…`), `cp -p`. Se o `--json` de
  alguém passar por cima de novo, a restauração deixa de ser arqueologia de
  transcript e vira um `cp` confere-hash.
- M1/M2 registradas abaixo; observações recorrentes viram JSON em
  `doc/curation/` + § em SMS_GLOBAL (`curation-learning.md`) na curadoria.

## Handoff
M3 em curso — falta **um** degrau, e ele é humano:
(1) sourcing de arte da cena 01 aguarda decisão humana (prompts persistidos;
rota recomendada = repetir `cena01_vale_concept_v1.txt` no cliente com quota,
como o irmão MoF fez em 2026-10-11; converter com `prepare_sms_pixel_art.py` +
gates de recursos/luma/procedência). Enquanto não converte, as linhas "patterns"
de `doc/13-spec-cenas.md` permanecem marcadas **parciais** de propósito.
(2) runtime da FSM das 4 cenas com probe de VBlank — **FEITO**: corredor
relocado para base `0xC900` com gate `audit_probe_corridor.py`; arbitração
SFX-sobre-música provada por contadores **e** com captura de áudio na ROM
`f4f8ee3f` (W3/W4 vs W4B controle).
(3) `doc/13-spec-cenas.md` **preenchido com números medidos** (2026-10-14):
tabela-mãe por estado (`ph_state_max_hud` 34/29/34/28/39/45/27/22/28, nove
`spill_*`=0), pior frame 58 linhas cruas = 64 corrigidas em STORM, name table
128 B/VBlank, cena 03 24 sprites pico 6/linha, fps em 6 janelas 59,62–59,81.
Leituras-inválidas declaradas como não-citáveis (`ph_state_max_sat[3]/[5]=251`,
`ph_stream_max=255`).
(4) evidência: arco em vídeo de framebuffer (8 mp4, `m3_arc_E_r13.log`),
`check-bundle` PASS na ROM atual, 8 wav de sink isolado com `rom_sha256`
casado, **publicadas também em `out/evidence/`** com binding hasheado em
`out/evidence/audio_m3_manifest.json` — é o destino que
`reconcile_claims._audio_supported` lê, e o build derivou `axes.audio=true` a
partir delas. **Resta a escuta humana** na cabine (`tools/m3_escuta.py --open`;
W5 é o caso que prova que silêncio ≠ emulador parado; W6 é a reprise).
Ajuste musical pós-escuta SÓ na partitura JSON.
(5) pendência de curadoria humana não aplicada pelo agente: o piso de 90% de
amostras ativas do `audit_audio.py` reprova passagens **quietas autorais** por
construção (eco 52,7%, `w1` 71%, `w2` 89%) — item P2, separado entre "mix fraco"
e "piso do instrumento"; aguarda decisão, com a métrica na mesa em
`out/logs/audit_audio_w*.txt`.
(6) **decisão de curadoria sobre destino dos eixos** (não aplicada pelo agente):
`boot_emulador`, `gameplay` e `fps_constante` estão `false` no `build_record`
apesar de medidos — `informative=true` no bundle `4246092d…/capture.json` e
`fps_constante=true` em `5f325212…/runtime/runtime_probe_m3_fps6.json`, ambos
com `rom_sha256=f4f8ee3f`, mas o `axis_support` só lê os caminhos da rota
desktop. Ou o wrapper passa a aceitar o bundle da sessão privada, ou se declara
uma rota de publish. Decisão do dono; enquanto não houver, estes três eixos não
se fecham sem fabricar JSON.
(7) **decisão de curadoria sobre o `--json` que sobrescreve dado**: medido nesta
noite, não é um defeito isolado do `audit_learning_capture.py` — **13**
ferramentas do wrapper tratam `--json` como destino de relatório
(`open(caminho,"w")`) sem nenhuma guarda, e apontá-las para um arquivo de dado
apaga o arquivo: `audit_debug_markers`, `audit_doc_sync`,
`audit_hardware_constants`, `audit_header_claims`, `audit_learning_capture`,
`audit_render_fidelity`, `audit_rom_asset_binding`, `audit_sprite_mode`,
`audit_visual_delivery`, `measure_vram_map`, `reconcile_claims`,
`screenshot_semantic_gate`, `validate_measurement_tools`. Correção proposta, não
aplicada: renomear para `--report-out`, recusar destino existente sem a chave
`problems`, e dar ao `validate_measurement_tools.py` um check dessa superfície —
hoje ele só prova `--self-check`, então a perda de dados é invisível ao cânone.
(8) **gate humano armado e verificado**: `tools/m3_escuta.py --verify` passa nas
8 janelas (blob do html == `out/escuta` == `out/evidence`, ROM `f4f8ee3f`, gate
por janela, 0 defeitos) e `--self-check` passa nos 6 casos, inclusive as 4
rejeições (ROM divergente, cabine velha, wav com SHA trocado, janela não julgada,
veredito fora do vocabulário). Depois do `--collect` o veredito pousa em
`out/logs/m3_escuta_verdict.json` com SHA do export e da ROM casados — é o último
degrau antes de M3 fechar, e ele é do dono.
   **Estado 2026-10-15 (madrugada):** `--open` executado a pedido — cabine
   regenerada (8 janelas, 5,2 MB, ROM `f4f8ee3f`) e entregue ao Chrome GUI da
   sessão; `--verify` refeito depois de regenerar continua `[PASS]` exit 0. O
   veredito **ainda não existe** no disco: falta o ato de ouvir e exportar, e o
   `--collect` só converte esse download em evidência hasheada.
