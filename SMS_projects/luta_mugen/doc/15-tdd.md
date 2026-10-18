# 15-tdd — luta_mugen

> **Revisão vigente 2026-09-26:** `engine_quality_contract.json` e
> `16-engine-review-2026-09-26.md` supersedem a escala 1:4/48 px como limite do
> motor. Números e tarefas T10 abaixo são histórico do perfil
> `legacy_probe_quarter`, sem aceite no novo piso. O piloto 72–88 px está
> medido para idle estático; ver `17-scale-pilot-2026-09-26.md`. Custos
> simultâneos, cadência AIR de combate, RAM/VRAM e capacidade expansível ainda
> bloqueiam a promoção para arte completa. Técnicas opcionais exigem A/B.


> Arquitetura técnica. Autoridade #7.
> A API definitiva é o header (`sdk/devkitSMS/SMSlib/SMSlib.h`, autoridade #8) —
> este documento NUNCA inventa assinatura. Em dúvida: leia o header.
>
> Rascunho S3 (2026-09-25): toda grandeza de hardware abaixo tem fonte citada;
> todo número de personagem vem de `out/local_study/s3_fidelity_ken.json`
> (medido por `mugen2sms/analysis/`, reproduzível). Em 2026-09-26, o runtime
> da arena de fixture já tem ROM bancária medida em emulador (Task 6); isso
> não promove o corte do Ken nem a entrega do produto. Cadeia de status:
> `documentado ≠ implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget`.

## Restrições assumidas (herdadas, sempre ativas)
```
❌ float/double em runtime quente  — SDCC Z80 faz float em software; use int16/Q8.8
❌ malloc / free                   — buffers estáticos; RAM = 8 KB
❌ VRAM em massa fora do VBlank    — sem DMA
❌ >8 sprites/scanline, >64 na SAT
```

## Grandeza de hardware, com fonte (L001: proibido número de outro console virar lei do SMS)

| Grandeza | Valor | Fonte |
|----------|-------|-------|
| Sprites por scanline | 8 | doutrina AGENTS.md; `audit_sprite_line_sim.py` |
| Capacidade da SAT | 64 entradas | devkitSMS `SMSlib/src/SMSlib_common.c:21` `#define MAXSPRITES 64`; esgota → `SMS_addSprite_f` retorna −1 (`SMSlib.h:199`) |
| Sprite alto 8×16 | `SPRITEMODE_TALL` | `SMSlib.h:57` |
| Metasprite | `SMS_addMetaSprite`, `METASPRITE_END=0x80` | `SMSlib.h:214-216` |
| Tile | 8×8 @ 4bpp = 32 B | `SMSlib.h:130` (`(tilefrom)*32`) |
| Subpaleta | 16 índices, 0 transparente → 15 úteis | `SMSlib.h:131`; AGENTS.md |
| Name table visível | 32×24 = 768 tiles | 256×192 / 8×8 |
| VRAM | 16 KB | VDP |
| RAM | 8 KB | Z80 |

Codificado em `tools/sms_wrapper/mugen2sms/analysis/sms_budget.py::SmsLimits`
(uma linha de comentário-citação por campo; `--self-check` embutido).

## Pipeline de dados (S0–S4 = Plano 1; S5–S6 = Plano 2)

```
pacote MUGEN (zip/pasta, somente-leitura)
  → mugen2sms.source.Source            [S2 ✔]
  → parsers (ini/sff/air/cns/cmd/snd)  [S2 ✔]
  → Character IR + report              [S2 ✔]
  → analysis/sms_budget + fidelity     [S3 ✔ — este documento]
  → converters (tiles/clsn/cmd/sound)  [S4]
  → generators SMS (C + .res)          [S4]
  → runtime interpretador de tabelas   [Plano 2]
```

IR não conhece SMS; generators não leem MUGEN (invariant herdada do doador MD).

## Ken Masters ADV medido contra o VDP (fonte: `s3_fidelity_ken.json`)

Totais por classe: **direct 2273 · approximate 317 · manual 93 · unsupported 297**
(3080 elementos; cada um com `motivo`).

| Categoria | direct | approximate | manual | unsupported | motivo dominante |
|-----------|--------|-------------|--------|-------------|------------------|
| sprite (463) | 447 | — | 16 | — | `paleta>15uteis` (16 sprites com >15 cores) |
| pose/frame (934) | 448 | 243 | — | 243 | `scanline>8` (243); `sat>64` (232 — efeitos 320×240 de intro/victory); `sprite-ausente` (11 — referenciam sprites de sistema ausentes do .sff do personagem) |
| clsn (662 frames com caixas) | 662 | — | — | — | colisão em software Z80, sem custo de VDP |
| comando (91) | 14 | — | 77 | — | `botao>pad` — MUGEN usa b/c/x/y/z; pad SMS tem 1 botão |
| som (33) | — | — | — | 33 | `pcm>psg` — PCM não existe no VDP |
| controlador de estado (796) | 702 | 73 | — | 21 | unsupported: 17 blending/rastro, 2 fightfx, 1 paleta-RAM dinâmica, 1 multiplicador não modelado |

Distribuição de largura de sprite (colunas de 8 px): mediana 69×83 px;
**270/463 sprites (58%) têm >8 colunas** — a arte MUGEN é maior que a tela SMS.

### VRAM (pool de tiles)
- Tiles brutos: 67.501 · **dedup 8×8: 36.401 únicos = 1.164.832 B** vs 16.384 B de VRAM.
- Conclusão medida: **personagem inteiro nunca reside**; streaming por pose é obrigatório
  (padrão MSSF2T: arte em banks, upload só no VBlank).
- Orçamento por pose jogável (pós-corte ≤8 col × ≤8 linhas altas): ≤64 tiles = **≤2 KB
  de tiles ativos por frame**, sobrando ≥8 KB para BG + sprites do cenário.

### ROM e banking
- Estimativa da seleção jogável: ~120 poses finais × ~40 tiles × 32 B ≈ **150 KB só de arte
  de UM lutador** (dedup intrapersonagem já embutido na contagem de tiles únicos).
- 2 lutadores + cenário + código ⇒ **estoura qualquer mapa linear**; banking Sega mapper
  (páginas 16 KB, dados a partir de BANK1, streaming só no VBlank) — mesmo padrão do spec
  de banking do MSSF2T. Status: **bancado** (decisão tomada por medição, não por medo).

## Corte jogável (decisão explícita do que entra no MVP)

| Furo medido | Decisão |
|-------------|---------|
| sons PCM (33, todos unsupported) | **Nada porta direto.** Reautoria PSG: 6 SFX (soco, chute, especial, hit, KO, round) + 1 BGM, declarados em manifest de áudio. Ken audível = zero PCM. |
| comandos com b/c/x/y/z (77) | **Remapeio manual**: tabela de comandos do runtime só aceita {direções, A, start}; combo especial passa para QCB+A etc. na faixa `manual`, reautorado 1 lutador. |
| `scanline>8` (243 poses) | **Decisão histórica 2026-09-25, supersedida no padrão 2026-09-26**: 1:4/32×48 sobrevive apenas em `legacy_probe_quarter` para reproduzir T10. Rota vigente: idle opaco 72–88 px na área útil inicial de 160 px, razão uniforme por personagem/cena, pivôs/CLSN preservados e custo por pose medido. O pedido anterior de zero flicker visível foi supersedido pela decisão humana posterior registrada no GDD: opção 3, flicker mínimo e nenhum glitch. Poses/budgets fora do contrato bloqueiam promoção. Ver GDD vigente, `mugen_engine_standard.md` e `18-gap-diagnostico-plano-prompt-2026-09-29.md`. |
| `sat>64` (232 frames de efeito) | **Fora do MVP** — intros/victory screens fullscreen não cabem na SAT; ficam no IR como documentação do acervo. |
| `sprite-ausente` (11 frames) | **Fora** — dependem de sprites de sistema (fightfx) que não estão no pacote do personagem. |
| paleta >15 úteis (16 sprites) | Quantização no conversor + revisão visual; `manual` até passar em `audit_validate_resources`. |
| controladores unsupported (21) | 17 blending/rastro → substituídos por sprite-extra ou omitidos; 2 fightfx → omitidos; 1 flash de paleta → CRAM dinâmica no VBlank se sobrar tempo; 1 multiplicador → fora do escopo (sem dano variável no MVP). |
| 12 paletas do .act | P2 (dummy) = **shift de faixa de índice** no MESMO sprite palette (o SMS tem UMA paleta de sprite; sem escolha por sprite — SMSlib.h:249-250). Paletas ACT de P1/P2 devem caber em 15 úteis conjuntas; custo = cópia dos padrões com índices deslocados (medido no Plano 2 Task 2), não zero. |

## Mapa de memória (RAM) — candidatos, a fechar no Plano 2 com o runtime escrito
| Faixa | Tamanho | Conteúdo |
|-------|---------|----------|
| — | — | (fechado em S5; nenhum byte acima de 8 KB será declarado sem pool nomeado) |

## Entidades e pools (estáticos) — orçamento inicial em jogo
| Pool | Máx | Bytes/entidade | Total |
|------|-----|----------------|-------|
| lutador+helper (Q8.8 pos/vel, estado, anim, timer, vida, flags) | 4 slots | 32 B | 128 B |
| stack da VM de condições (IR `vm.py`) | 2 × 32 | 1 B/entry | 64 B |
| staging de tiles p/ upload no VBlank | — | 0 B | 0 B (source lido direto do bank via `SMS_VRAMmemcpy_brief`; endereço de destino em bytes, revisão T6) |
| buffers do SMSlib (SAT, name table espelho) | — | (SMSlib aloc; ~2 KB) | — |

**Regra:** nenhum pool entra no build sem linha medida no worst-frame
(`measure_worst_frame.py`), padrão MSSF2T.

## Máquina de estados
_(runtime — Plano 2; o IR por estado já é interpretável: 126 estados de Ken medidos,
origem 99 personagem + 27 common_forge)_

## Banking
- Alvo inicial: **48 KB linear sem mapper** (B01) → **reprovado por medição S3**
  (só a arte do corte de 1 lutador ≈ 150 KB).
- Adotado: **mapper Sega** (páginas 16 KB, regs 0xFFFE/0xFFFF), código ≤32 KB,
  dados no slot 2, streaming apenas no bloco VBlank depois de
  `SMS_waitForVBlank()`; o código salva, mapeia e restaura o bank ao redor do
  `SMS_VRAMmemcpy_brief`. O destino do memcpy é endereço em bytes: `base_tile * 32
  + offset_bytes` (SMSlib.h:394; `SMS_loadTiles` aplica esse fator na macro em
  SMSlib.h:130).
- Status atual: **implementado e validado no fixture sintético**. Build
  `b5d5db7b…`, 65.536 B; `measure_worst_frame.py` selou 3.000 frames com
  `vovf_delta=0`, `vline_min=0xC8`. O pipeline do Ken real ainda não está
  entregue.

## Áudio
- Driver: PSGlib (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Canais declarados: BGM em 0+1 e SFX em 2+3 via
  `PSGSFXPlay(sfx, SFX_CHANNELS2AND3)`; `audit_psg_channel_binding.py` deve
  confirmar que chamadas e manifesto continuam alinhados.
- **Resolução medida em 2026-09-30, sem reautoria.** O stream
  `music_battle.psg` (1001 bytes, SHA-256
  `c9861a780dbc98f9ccbd9554e156678ed263a34bae70f9ffca5115cefc1ee8fa`)
  escreve os quatro canais: tom 0, tom 1, tom 2 e ruído 3. A frase
  “BGM em 0+1 e SFX em 2+3” acima é o roteamento desejado; os bytes
  autorados não o obedecem. O lote integrado não altera o manifesto para
  fazer o gate passar e não reautora a música. Os SFX mantêm a máscara
  literal do manifesto (`SFX_CHANNEL2`, `SFX_CHANNEL3`,
  `SFX_CHANNELS2AND3`) e ocupam 2 e/ou 3 enquanto tocam, por cima da
  música de quatro canais. `PSGRestoreVolumes` não é chamado; o TDD não o
  trata como rotina de retorno de SFX. A captura isolada do Lote C durante
  entrada de soco tem 11,1 s, peak 5887, 100% ativo e `audit_audio.py` PASS.
  Ela prova sinal integrado durante a ação, mas não julga qualidade musical
  nem separa a restauração nota a nota dos canais 2/3.
- YM2413/FM é **opcional**: o jogo tem que funcionar sem ele.
- Medido: 33/33 sons PCM → **zero bytes portados**; só reautoria PSG entra.

## Lote C — integração de palco, HUD, áudio e rounds (2026-09-30)

- `stage.c` carrega na inicialização um mapa estático e paleta de fundo;
  não usa scroll. A arte é uma arena técnica original, ainda fixture de
  engenharia, não cenário final.
- `hud.c` mantém as células desejadas/mostradas em arrays fixos e escreve no
  máximo duas células sujas por VBlank. Barras, timer, placar e banners ficam
  na name table; não consomem SAT.
- `audio.c` chama `PSGFrame()` e `PSGSFXFrame()` uma vez por iteração e aplica
  ranking fixo para round, soco, hit e KO. A música autora escreve nos quatro
  canais; SFX ocupa temporariamente 2/3, conforme manifesto.
- `main.c` implementa estados de intro ROUND/FIGHT, luta ativa, resultado e
  partida encerrada. Timer NTSC usa 60 quadros da ROM por segundo, 99 s por
  round; empate/KO duplo não pontua; primeira pessoa a dois pontos encerra a
  partida. Rematch fica em B1 do P1. PAL não está validado.
- O runtime integrado ainda lê B1=soco e B2=guarda; direções estão
  mascaradas. Não equiparar esse piloto ao mapa final do GDD (B1 soco, B2
  chute, recuo guarda).
- Trace funcional por DAP, mesma ROM: 25 socos P1 aceitos, 10 com dano de 50
  cada e 15 misses; P2 ficou em 500/1000 ao timeout. A FSM marcou 1–0 e iniciou
  o round 2, sem KO observado. O fonte aplica recuo e o input não aceita
  direções, hipótese compatível com a série de misses, mas o trace não grava
  coordenadas para provar a causa exata. O DAP pausa a emulação durante as
  leituras; não usar este trace para FPS.
- Esta integração não altera a cadência AIR nem remove a latência já medida.
  O worst-frame de 3000 quadros incluiu um B1 que conectou e terminou sem
  overflow, mas seu perfil por etapa é inválido sem quadro derramado. Cobre
  esse caminho, não todos os golpes/poses nem o orçamento completo.

## Orçamento de frame
O loop atual foi medido em emulador: no fixture de luta, `stream_step`, carga
condicional de paleta, atualização do HUD e cópia da SAT ocorrem após
`SMS_waitForVBlank()`; input, física e preparação de metasprites ficam em CPU
depois do bloco VDP. `measure_worst_frame.py` na SHA
`b5d5db7b6295e8c6947b0125f0d4ef468fc179fb4e4d72215b5b5573227fafc5` mediu
3.000 frames, nenhum VDP write atravessando para display ativo e
`vline_min=0xC8`. O snapshot de checkpoints por etapa não existe nesse PASS,
pois o perfil captura apenas quadros com derrame. Esta era a ROM de fixture;
a medição do corte Ken real está registrada na atualização T10 abaixo.

## Atualização de runtime — T10 Ken vs Ryu dummy (2026-09-26)

Build observada no Emulicious: ROM 131.072 B, SHA
`af9eb127895ed07de6884592bbac420e31c660b39d371d4c9f5faaacd629dc97`.
T10 integra o corte Ken (44 poses, banks 2–4) e o corte Ryu (32 poses, banks
5–6) na mesma ROM. `fight_step` seleciona o perfil por slot e consulta tabelas
de animação/CLSN/física distintas. P2 continua dummy determinístico; o parser
de comandos físicos só controla P1. As tabelas de estado em `fight.c` ainda
referenciam os símbolos Ken/Ryu, então trocar um `.def` sem alterar o C do
núcleo não está provado nesta composição.

- `measure_worst_frame.py`: PASS na ROM T10 em 3.000 frames, `vovf_delta=0`,
  `vline_min=200`. O perfil por checkpoints retorna inválido porque não há
  quadro derramado para perfilar; nenhum tempo por etapa foi medido.
- `measure_frame_advance.py`: 58,6 FPS, 27 transições em 59,81 s,
  `constante=true`. Título do Emulicious: média 59,8 FPS (6/6 válidas).
- `measure_runtime_probe.py --seconds 120 --janelas 2`: PASS na ROM T10,
  58,10/59,78 FPS, spread 1,68; boot e avanço também PASS
  (`t10_current_runtime_probe_120.json`). A tentativa de 2×240 s quebrou o DAP
  antes da segunda janela; os 54,22 FPS daquela janela ficam como diagnóstico.
  Não se transfere o resultado T9 (58,87/59,86 FPS, SHA `2210b016…ebf21f`).
- `t10_input_memory_range_sync_pass.json`: direção, pulo até 76 px, dano,
  crouch, guard e QCF+B1 PASS no mapa SMRT com input físico. O helper revalida
  P1/P2 após IDLE e amostra o alcance com o jogo pausado antes do B1: gap 16,
  vida 152→102 e score 2→3. O whiff anterior fica como diagnóstico em
  `t10_input_memory_idle_wait_retry_whiff.json`.
  `t10_current_audio.wav`: sinal isolado por 15,6 s, ativo em 100%, auditado;
  sem avaliação subjetiva da composição.
- A tela T10 é somente `probe`; a captura semântica aprova paleta e pixels,
  mas não demonstra uma silhueta final de luta. Não declarar `delivery`.
- `seal_fresh_evidence_bundle.py`: PASS; o bundle T10 sela 38 artefatos,
  incluindo o reteste range-synced e seu self-check. `reconcile_claims.py`
  confirma os sete eixos binários; `audit_claims.py` não encontrou claim acima
  do teto.
  KO/reset, gameplay prolongado e contrato visual continuam fora do PASS.

Build Ryu separada: `t9_ryu_def_switch.json`, 65.536 B, 32 poses, dois banks.
Os SHA de `src/main.c`, `src/fight.c` e `inc/fight.h` são idênticos aos da
build Ken. Isso prova substituição de dados no build, não mistura de dois
personagens em runtime; para a cena golden, metadados e pose banks devem ser
selecionáveis por fighter sem aumentar o pico acima de 8 sprites/scanline.
