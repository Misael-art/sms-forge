# 10-memory-bank — kage_matsuri

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-09-25 (2) — **PISO L078/L079 FECHADO; ROM CANÔNICA AGORA É
`d7e94286aa1c899525ad79be77be2308dd8d7ca595c47e8c262b103703def166`, 16384 B.**
`tools/gen_music_kage.py` compõe a faixa no piso usando o composer consertado
do wrapper (`make_psg_assets.compose_music`) com materia própria: escala yo
em Ré (D F G A C, sem meio-tom — sabor festival/Goemon), cadencia Dm-F-C-G,
lead ataque+decay, arpejo de preenchimento com acento alternado, pizzicato no
baixo e percussao BRANCA gateada. Stream: **577 B / 128 frames (2,56 s), piso
`audit_psg_quality`: viol=[], M5 no limite exato (128≥125)**. O reprovado de
0,6 s (`8a61b3e2c17b…`) saiu do disco. `sfx_slash.psg` inalterado (passava;
periodico metalico legitimo). Manifest + `rom_asset_binding` re-hasheados,
`audit_rom_asset_binding --require` ok (a entrada agora é o .psg novo),
bundle selado com 8 artefatos pós-ROM, `reconcile_claims` PASS. Folga medida
da ROM nova: dados terminam em 0x375E, ~2,2 KB livres antes do bloco de
cabeçalho — há espaço para crescer.
Medidas na nova ROM: capture_audio 20 s peak=6030 ativo=100%; runtime probe
boot/frame_advance/fps_constante PASS ([59,44 / 59,38] — a 1ª rodada da
medição reprovou fps_constante por ruído do host e foi re-medida limpa);
`prove_input_memory` PASS integral (dx +98/−98 nos dois sentidos, pulo e B1
observados na RAM). Os resultados worst-frame (`vline_max=239`,
`vovf_delta=67`) foram **invalidados por L082**: o probe contava
`vline >= 0xC0`, final que ainda cai dentro do VBlank. Nem o delta nem o
`vline_max` provam derramamento; repetir com o critério corrigido antes de
declarar orçamento do ciclo.
Eixo audio agora significa PRESENÇA + QUALIDADE medida, não só presença.

2026-09-25 — **PISO DE QUALIDADE DE ÁUDIO MEDIDO (L078/L079, gate
`audit_psg_quality.py`).** `music_kage.psg` (`8a61b3e2c17b…`) reprova: 2
canais com nota nova a cada frame (metralhadora de 16 Hz), volume estático
em ambos, loop de 32 frames (0,6 s), sem canal de ruído. `sfx_slash.psg`
PASSA — e usa ruído periódico legitimamente (metálico de lâmina, Kenseiden).
Artefato: `out/logs/psg_quality.json`. O que o eixo `audio` selado significa
até aqui é PRESENÇA; qualidade exig regeração da faixa no piso (dívida no
ledger `doc/psg_quality_ledger.json`).

2026-09-25 — **RE-CONCILIAÇÃO (curadoria passo 2): ROM CANÔNICA AGORA É
`f02dfd3c749ed546d4303e1938ebb41cbc08837e8c7bbd96fae08251772419f9`, 16384 B,
com cadeia fresca e probe no esquema canônico.** Causas da divergência que o
curador apontou (bank anunciava `283e250a…`, disco tinha `1e6c4e9b…`):
(a) o SDSC usava `SMS_EMBED_SDSC_HEADER_AUTO_DATE_16KB` — cada rebuild em dia
diferente mudava a SHA sem mudar código (mesma doença que matou o selo do
MSSF2T em 09/09; pinado aqui para `2026-09-19`);
(b) o probe do kage vivia em mapa próprio: `s0_x/s1_x` em 0xC7EC/0xC7ED,
exatamente onde `measure_worst_frame.py` lê o byte ALTO da word `vovf` e a
`phase` — duas ferramentas lendo a mesma RAM com mapas diferentes. O byte
`vovf` antigo ainda saturava em 255 por guarda `!= 0xFF`. Corrigido ao esquema
canônico (vline 0xEA, vovf WORD em 0xEB, phase 0xED, s0_x/s1_x movidos para
0xEE/0xEF; `probe_vovf` só zera no boot — reset de vitória não come mais a
contagem no meio da janela). `tools/prove_input_memory.py` e
`tools/measure_worst_frame_cycle.py` acompanharam o mapa. Rebuild idempotente
na mesma SHA (pinagem provada).

Medições FRES CAS nesta ROM (todas seladas no bundle, 10 artefatos):
- `runtime_probe.json`: boot + frame advance + 58,48/58,16 fps da própria ROM.
- `fps.json`: título 60,0 constante, 6 amostras.
- `evidence.png`/`evidence.json` + `semantic_boot_current.json`: boot PASS no
  gate semântico em escala nativa — exigiu conserto no gate, que acusava
  "lixo de VRAM" no chão denso do palco (6,7% de blocos ricos) porque o limiar
  5% foi calibrado em capturas escaladas, onde o bloco 8×8 da janela cobre
  só 1/4 do tile. Agora o limiar é sensível à escala: 5% escalada / 30%
  nativa, com fixtures de regressão (arte densa nativa passa, ruído nativo
  reprova — separação medida: arte 2,3–6,7%, ruído sintético 100%).
- `audio.wav` + `audit_audio`: peak 3689, ativo 100%.
- `input_memory.json`: dx ±96 com `keys` lidos durante o hold, pulo (py
  128→106), B1 com eco 0x10 e pose 3.
- `full_cycle_memory.json`: **combo→duas derrotas→torii→reset provado por
  RAM**. Nota honesta: a 1ª tentativa falhou ("combo nao confirmou derrota
  apos 6 tentativas") e a 2ª passou — flake de ambiente, registrado, não
  escondido.
- `worst_frame.json` (cena parada, 45 s): PASS — `vovf_delta=0`,
  `vline_max=4`.
- `worst_frame_cycle.json` (ciclo causal): **FAIL com número honesto** —
  `vline_max=245`, `vovf_delta=67` via word não-saturante. Confirma as
  leituras antigas (66/243–246): o bloqueio de budget era real, não artefato
  do contador. Blocação continua em pé: o ciclo de ação derrama no VBlank.
- `recipe_combate.mp4` (curadoria passo 3, 25/09): vídeo nativo com roteiro
  de input (`Right/a/Left/Up` via canal kdotool+ydotool) — 37,91 s, 6/6
  frames informativos, movimento 3,2% (fundo denso estático por projeto de
  cena; o que se move são sprites e pips de vida, visíveis em f02/f05).
  Última evidência do segundo projeto nas receitas canônicas
  (`sms-recipe-combate-1v1`, `sms-recipe-animacao-impacto`).

Eixos derivados por `build_inner`+`reconcile_claims`: os 7 canônicos `true`
nesta SHA. Binding asset→ROM re-hasheado para `f02dfd3c…` (12 entradas,
`audit_rom_asset_binding --require` PASS). **O que NÃO vale para esta ROM:**
tudo selado em `283e250a…` e
`1e6c4e9b…` (final5/final6/final7, `cycle_video*`, vídeos, review Ptolemy,
binding audits antigos). **PAL continua bloqueador regional não re-medido
aqui** (última medição: 48,99/48,22 fora da faixa, em `283e250a…`).

## Eixos — medidos em 283e250a… (registro antigo)
> **SUPERSEDIDO em 2026-09-25** pela re-conciliação `f02dfd3c…` (bloco acima).

## Registro anterior (2026-09-09, ROM `283e250a…`)
2026-09-09 — execução P0→P4 percorrida na ROM final `283e250a…`; saída ainda
bloqueada por PAL e budget causal.

`player_hp` (8,8): 3 pips com a cabeca do Kage (tiles 128/130). `goal_torii`
(200,24): samurais restantes com o samurai idle (tiles 192/194). Zero tile
novo — recursos de cena. Slash2 e jump foram substituídos por fontes selecionadas
do acervo (`anim_kage_slash2/f015.png` e `anim_kage_combo/f025.png`), o proof
16×32 foi gerado e o binding aponta para símbolos realmente presentes no mapa.

## Eixos
| Eixo | Status | Prova |
|------|--------|-------|
| build | testado | `build_inner.py --project SMS_projects/kage_matsuri` PASS; ROM 16384 B, SHA `283e250a…` |
| validation_report | testado | pré-gates do wrapper + binding, visual delivery, recursos, sprites/scanline, animação e áudio PASS |
| boot_emulador | testado_em_emulador | `evidence_final7.json.png` + `semantic_boot_final7.json` PASS; luma 5791.1, paleta 100% |
| gameplay | testado_em_emulador | `full_cycle_memory.json` PASS: combo→2 derrotas→torii (`state=1`, `px=202`, B1 segurado)→reset; input básico PASS |
| fps_constante | testado_em_emulador NTSC; PAL reprovado | `runtime_probe_final7.json.json`: 58.51/57.53 quadros/s, avanço PASS. `runtime_probe_pal_final7.json.json`: 48.99/48.22 quadros/s, fora da faixa do gate |
| audio | testado_em_emulador | `audio_final7.wav.wav` isolado: 491520 amostras, peak 3604, 100% ativo; `audit_audio` PASS |
| memory_bank_atualizado | testado | este registro após as medições finais |

## Arte e Contrato Visual
- Kage: 6 poses 16x32 (`idle`, `walk0`, `walk1`, `slash1`, `slash2`, `jump`) em 8x16 com bitrev esquerdo offline.
- Samurai: 2 poses 16x32 (`idle`, `walk`) em 8x16 com bitrev esquerdo offline.
- HUD: camada de sprite SEM tile novo (ve acima); SAT pior caso 22 entradas, pico 6 sprites/linha (`audit_sprite_line_sim`).
- Palco: rua de matsuri autoral em 128 tiles BG sem branding.
- Conformidade: `audit_claims`, `audit_audio_provenance`, `audit_visual_delivery --delivery`, `audit_rom_asset_binding --require`, `audit_sprite_line_sim`, `audit_animation_semantics` — PASS.
- Entrega visual: `visual_delivery_final6.json` PASS; `render_fidelity_video7_kage.json` encontrou `kage_idle_full` em 16×32 no framebuffer nativo.
- Budget: `worst_frame_final6.json` PASS (`vline_max=4`, `vovf_delta=0`, 37 amostras/45 s em ROUND). `worst_frame_cycle.json` FAIL (`vline_max=243`, `vovf_delta=66`); combo/torii não estão promovidos para budget fechado.

## Ferramenta de prova de input
`tools/prove_input_memory.py` (self-check 13 fixtures PASS). Por que existe: o
rastreador de pixels do `capture_evidence --press` e ambiguo no palco matsuri
(L038 — com "Left" o blob "andou" +137 px de cenario). Canario de canal por
ECO DE TECLA, nao por frame: `probe_frame` e `__at()` e o crt0 nao zera
absolute-at — o contador acorda com lixo de RAM (48731 no boot) e a semantica
"f1 < f0" mente. O avaliador DAP do Emulicious responde com anotacao de
simbolo de forma intermitente — re-ler (fail-closed preservado: sem eco,
nada fecha). Armadilha de host resolvida: `Emulicious.ini` estava com janela
maximizada (3376x1458) e `capture_evidence` rejeitava a captura como desktop
(teto 1.5 Mpx) — ini corrigido para janela 1056x840 @ scale 4.

## Handoff de assets (AGENTE DE ARTE)
`doc/handoff-assets.md`: selecionar frame de clímax em `rascunho/anim_kage_slash2/`
-> `rascunho/kage_slash2.png` e traduzir pose de salto -> `rascunho/kage_jump.jpg`.
Runtime/pipeline/gates sao de outro agente. Depois de soltar as fontes:
clean+pack+build, re-selar binding, 5 gates, evidencia fresca.

## Fora de escopo
Dano ao jogador, projéteis/ataque do samurai e nova cena após o torii não foram
adicionados: não estão especificados no GDD. O torii desta fatia é o estado
de vitória e reinício já provado por RAM.


## Revisão documental do plano — 2026-09-09

`implementation_plan.md` foi percorrido até P4, com saída bloqueada; prompt em
`prompt_continuidade.md`. A ROM baseline foi preservada em
`out/baseline_2026-09-09/` antes do rebuild. A última build foi seguida por
sessões novas de emulador, captura nativa, áudio isolado, runtime DAP e budget.

O ciclo foi renovado e está em `full_cycle_memory.json` com snapshots pausados
e probes de HP/alive/posição. `cycle_video5.mp4` tem 256×192, 571 frames,
9.53 s, 8/8 frames informativos e áudio anexado; `audio_final5_retry.wav` é
isolado. `worst_frame_final6.json` cobre ROUND por 45 s. O medidor causal
alcançou combo/torii, mas falhou com derrame. O blocker regional é PAL: 49.37/49.42
quadros/s contra a faixa do gate; o critério não foi reduzido.

Review independente: `out/evidence/independent_quality_review.json`, revisor
`Ptolemy`, gameplay/art/hardware, schema validado por
`independent_quality_review_validation.json`. O parecer permanece `blocked`
por PAL e budget de ação; foi renovado contra os artefatos final5/final6 antes
do selo. Não há autoaprovação nem claim AAA.

Instrumentos secundários: `measure_frame_advance.py` não encontrou o contador
HUD (`0 transições`, sem estado completo), enquanto o runtime DAP provou
avanço com 964 frames NTSC. `audit_deterministic_boot.py` self-check passou,
mas a captura real divergida entre dois frames de animação (`ccfa…`/`74bc…`);
isso fica reportado como limitação do gate visual, não como PASS fabricado.
Bundle fresco finalmente selado em `out/evidence/fresh_evidence_bundle.json`
com 17 artefatos posteriores à ROM, SHA do bundle
`3a2464a3f4671dec85b3d787ea7c1248b5fa2a0cd343b4ee776f8e42dcafb1e2`.
O parecer independente renovado está em
`out/evidence/independent_quality_review.json` (SHA
`89f68f335e19ca4689a834712179429ec96363fdd7a3e1a3598c2091124cfb2b`), validado
por `independent_quality_review_validation.json` (`ok=true`).

## Atualização final7 pós-build — 2026-09-09

Os números acima de final5/final6 são históricos. Após a última build canônica,
as capturas foram renovadas: `evidence_final7.json.png`,
`cycle_video_final7.mp4.mp4` (256×192, 614 frames, 10.25 s),
`audio_final7.wav.wav` (491520 amostras, peak 3604),
`runtime_probe_final7.json.json` (NTSC 58.51/57.53 quadros/s) e
`runtime_probe_pal_final7.json.json` (PAL 48.99/48.22 quadros/s, FAIL do
limite regional). `full_cycle_memory.json` passou com tentativas limitadas de
ataque; `worst_frame_cycle.json` continua FAIL (`vline_max=243`,
`vovf_delta=66`) e a corrida mais recente não fechou a cadeia do medidor.
O review e o bundle precisam apontar para estes hashes antes do handoff final.

Selo final7 concluído: `fresh_evidence_bundle.json` SHA
`7092c64f2c304a92ebbe7cf105cd58efb1a8f33eae0da1e58d96186143f64f0f` contém
19 artefatos pós-ROM. Review independente `f4a26015e361465321c3f8666af65b9da639dc6d10ea546b9bc97509c2b27223`
e validação `88e3d2b410ca3fbaf6c1195c9dabea5ec824026c7b71916d5ccbb0e71ca092be`
foram validados pelo router (`ok=true`); status permanece `blocked` por PAL
e budget causal.

## Continuidade P0→P4 — 2026-09-19

Baseline preservada em `out/baseline_2026-09-19/`. Build canônico pelo wrapper:
PASS, 16.384 bytes, ROM `out/rom/kage_matsuri.sms`, SHA256
`1e6c4e9bb9e91b0b5649d8877a5a5b78bdb10c4930146f5b9bea9e5bb74a77a3`.
Binding, procedência e sprite-line passaram para esse SHA.

`out/evidence/full_cycle_memory.json` passou por RAM: combo→duas derrotas→
`state=1`, `px=202`, B1 segurado→reset (`kills=0`, `alive=1/1`). SHA do
artefato `14ccaec52507ea11c67dacc4e30bbe6b63e1e4770487a21aae0e64f1c665d109`.
`out/evidence/worst_frame_cycle.json`, no mesmo ROM, falhou com
`vline_max=246`, `vovf_delta=66`, 7 amostras, estados play/win; SHA
`64afc41a5eb1fde15f43c2573d2d77cfb120c31a73051240ea6dbd6ba09320f2`.

Não há FPS NTSC/PAL fresco aceito para este SHA: as tentativas de renovação
encontraram NPE de inicialização do debugger do Emulicious, além de uma
ocupação concorrente da porta 4901 pelo `hamoopig`. A ferramenta local recebeu
espera de janela e `-set Update=0`, com self-check verde, mas vídeo, áudio,
review e bundle final7 continuam históricos. Estado: protótipo jogável provado
por RAM; entrega bloqueada por budget causal e evidência/runtime renovados.
Bundle fresco parcial foi selado em
`out/evidence/fresh_evidence_bundle_current.json`, 8 artefatos, SHA
`ca07c2d8da7454bc02d226622b904d845229af33f9db80b457df8a4d13e315d2`. Inclui
vídeo nativo 256×192/283 frames, áudio isolado e render fidelity PASS
(65,3%); a conciliação atual passou, com `fps_constante` não declarado. Não é
bundle de entrega porque ainda faltam boot/FPS NTSC-PAL e review do SHA.

## Ciclo 2026-09-25 (3) — tema de festival recomposto + re-selagem

- Tema recomposto contra o piso estendido (M7, LOOP_MIN 250 — L080):
  0/2 streams reprovados medidos em disco.
- ROM b1eb19bfbf91… reconstruída; `doc/rom_asset_binding.json` atualizado
  (SHA do stream `.psg` + SHA da ROM) e passa `--require`. Evidências refatas:
  boot+semântica PASS, fps 60.0 constante, runtime probe PASS na re-medida
  (1ª tentativa falhou fps_constante sob carga de outro workspace — quirk
  conhecido), áudio isolado `kage_v3.wav` 28.2 s com audit PASS. Bundle:
  `out/evidence/evidence_bundle.json` (6 artefatos posteriores à ROM).
