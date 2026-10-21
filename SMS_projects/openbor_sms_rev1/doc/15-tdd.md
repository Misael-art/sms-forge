# 15-tdd — openbor_sms_rev1

> Arquitetura técnica. Autoridade #7.
> A API definitiva é o header (`sdk/devkitSMS/SMSlib/SMSlib.h`, autoridade #8) —
> este documento NUNCA inventa assinatura. Em dúvida: leia o header.

## Arquitetura do pipeline (contrato de conversão)
```
PAK → dependências resolvidas → IR tipado → perfil de compatibilidade
    → dados ROM/bancos → runtime C/Z80 → ROM observada
```
O host extrai/compila; o **SMS não mantém o PAK completo em RAM**. Toda feature
carrega estado `exact | adapted | blocked | dropped_by_owner` com parser,
lowering, consumidor, teste e prova por hash. Separar sempre
`parsed ≠ generated ≠ consumed ≠ observed ≠ budget_validated`.

### Host (implementado em `tools/sms_wrapper/openbor2sms/` — infra do wrapper)
| Módulo | Papel | Estado (O0) |
|--------|-------|-------------|
| `pak.py` | leitor PAK32/PAK64 (porte fiel do doador, banner com SHA) | **implementado** (19 unittest verdes com `intake.py`) |
| `intake.py` | verificação determinística de fontes (pak/sources/deps) | **implementado**, `--self-check` verde |
| `model_text.py` | parser de texto de modelo/level | O1 (porte) |
| `level_inventory.py` | inventário lexical de nível | O1 (porte) |
| `semantics.py` / `reference_semantics.py` | semântica + perfil de referência condicional | O1 (porte) |
| `level_event_table.py` | tabela estática de eventos (emissor determinístico C) | O1 (porte) |
| `analyze.py` | análise estática de capacidades/assets | O1 (porte) |
| `emit_slice.py`, `images.py`, `streaming.py`, `profiles.py` | **decisões MD** — referência de origem/cache/ownership/testes; a emissão SMS é separada | NÃO portar como SMS |
| `sms_art.py` | conversão de arte SMS: palco por dicionário de tiles, paletas 6-bit, poses TALL keyed, previews, records de conversão | **implementado** (O2), `--self-check` verde |
| `sms_emit.py` | contrato de emissão: IR + escopo → dados C + emission record com hashes + máscara de corte pré-computada (D10); `--generated-at` pinável para reprodutibilidade | **implementado** (O2), `--self-check` verde |

### Dados e locations (registro único)
- `data/source_openbor/` — subconjuntos extraídos dos PAKs (managed, hasheado).
- `data/generated/` — IR, tabelas, transcripts (managed) — **nunca** `res/`.
- `res/` — só recursos que passaram gates de produção (proveniência, recorte,
  paleta, prova técnica).

## Tipos e unidades (contrato de semântica)
- Mundo horizontal (X), profundidade no chão (Z) e altura de salto (Y)
  **separadas**; projeção/tipos/unidades declarados por campo do IR.
- Caixas/ataques usam profundidade, facing e frame ativo; sort visual não
  define colisão; física não para porque um hit mudou a FSM no ar.
- Handles/pools estáticos com geração, cleanup e invalidação de alvo/hit.
- Relógio: `delay` OpenBOR → conversão **racional** com política NTSC/PAL;
  fronteira de equivalência declarada no IR (origem desconhecida do runtime
  original é registrada, não mascarada).

## Restrições assumidas (herdadas, sempre ativas)
```
❌ float/double em runtime quente  — SDCC Z80 faz float em software; use int16/Q8.8
❌ malloc / free                   — buffers estáticos; RAM = 8 KB
❌ VRAM em massa fora do VBlank    — sem DMA
❌ >8 sprites/scanline, >64 na SAT
❌ >15 cores úteis em paleta sprite indexada (P1 índice 0 transparente)
```

## Armadilhas Z80/SDCC vigiadas neste projeto
- `int` é 16-bit signed; `char` é unsigned por padrão (SDCC z80).
- Multiplicação/divisão são caras (sem HW mul) → tabelas lookup / Q8.8.
- ISR curta: trabalho pesado fica no loop principal. Pause = NMI.
- Variável `__at()` sem `volatile` é apagada pelo SDCC (L009) — sondas seguem
  o workflow de marcadores.

## Runtime SMS observado (O2 — piloto VDP, histórico `b0eb624f…`)
- **Scroll/câmera (medido):** `cam = clamp(px-120, 0, 376) & ~7` (quantizada em
  8 px); `N = (-cam) & 0xFF` no registrador de h-scroll; a tela x≥8 mostra a
  coluna PNT `cam_col + (x>>3)`; anel mod-32 de colunas
  (`[cam_col..cam_col+31]`) reescrito a cada passo de 8 px, inclusive para trás;
  `VDPFEATURE_LOCKHSCROLL` (HUD fixo nas linhas 0..1) + `VDPFEATURE_LEFTCOLBLANK`
  (x0..7); backdrop preto (`SMS_setBackdropColor(1)`).
- **Orçamento de sprites:** máscara pré-computada na emissão (decisão D10) —
  `inc/o2/enemy_mask.h[(pose_index()*73 + (pz-160))*3]`, 3 B/entrada, bit i =
  célula i da tabela ordenada do inimigo; política conservadora (todas as
  células contam, mesmo fora da tela); jogador sempre inteiro; runtime = lookup
  + `sx > 255` pula. Política antiga (contagem em runtime) consumia ~2.07
  quadros na pior pose — eliminada.
- **Poses:** idle01 + ciclo walk01/walk03 (ax), idle01 (long); espelho = padrões
  próprios. Delays: idle 8→5 NTSC, walk 12→7 NTSC (PAL declarado).
- **HUD:** linhas 0..1; trilho preto + barra verde (hp 100 → 160 px) + barra
  vermelha (hp 50 → 80 px); 3 tiles; piloto, não arte final.
- **Probe de RAM:** magic/schema (`SMRT` v1) — frame u16 @0xC7F0; estatísticas do
  jogador/câmera @0xC000. Ver `doc/13-spec-cenas.md` (medições) e o escopo
  `doc/artifacts/o2_vdp_pilot_scope_20261016.json` (rev2).

## Runtime SMS observado (O3 — baseline M6)

Conciliação documental de 2026-10-18: M6 já commitado em
`da86de303bca969a393032d270c9d245d4055180`; ROM
`76cdbee3f10a58a07199b9012ff6dbe53df372d7532d6a8aa324089824425e73`,
131072 B. Nenhuma nova build/execução neste Lote A. M5 descreve a ROM
`b0eed40a…`; os traços M6 descrevem apenas `76cdbee3…`. Índice sucessor em
`doc/artifacts/post_m6_evidence_index_20261018.json`; originais preservados.
M1–M8 são marcos internos de O3, distintos de O0–O8 do plano geral.

- **FSM por ator** (`src/main.c`): idle/chase/attack/hit/drop/rise/dead; o
  ataque consome a caixa `attack2` do frame ativo (D4 — `first..last`);
  dano/knockback em `resolve_hits`; `hit_used` impede hit duplo no mesmo golpe.
- **D13 — guarda pós-hit (medida)**: `guard` (13 q) decrementa no topo de
  `actor_advance`, antes do hitstop e do gate de pose; sem isso a vítima ficava
  imune para sempre e a morte era inalcançável. Prova: traço de morte com 8
  hits 50→0 (`dead=1`, estado DEAD f114, HUD `hde=0`).
- **IA chase (D6/D7)**: `O3_CHASE_Q8=0x0140=320` contra
  `O3_WALK_Q8=0x01AB=427`: razão **320/427 ≈ 0,7494×**, não 1,5× a
  velocidade do jogador. São 1,25 e 1,66796875 px por chamada elegível;
  em 60 chamadas/s, 75 e 100,078125 px/s. `move_toward(dx,dz)` divide o
  budget 320 proporcionalmente por `|dx|+|dz|` (não norma euclidiana).
  `facing = (dx>=0)` na IA livre; ataque exige `|dx|<=40 && |dz|<=15` e
  congela facing. `O3_AI_THINK=12` é recarga do contador; o ramo de decisão
  só ocorre na chamada seguinte após chegar a zero (13 chamadas elegíveis
  entre decisões livres), sem claim de cadência em segundos sob interrupções.
  Provas M6: e.x 299→240 (vídeo), e.z 185→206 (traço dedicado).
- **Posição versus animação**: `player_control` integra os acumuladores antes
  de `actor_advance`; em IDLE/WALK a posição não espera readiness da pose.
  O gate de pose segura o avanço da FSM/animação (e arcos no caminho FALL).
  A frase histórica “caminhada 1,6–1,7× mais lenta” não tem janela que separe
  deslocamento, estado e poses; não sustenta redução de velocidade posicional
  nem razão medida de cadência. Medir ambos separadamente no próximo lote.
- **Pulo/queda (D5)**: tabelas congeladas `o3_jump_y/x` (40 q, ápice 55,
  deriva 67 px), `o3_toss_y/x` (36 q) e `o3_entry_y` (entrada, 38 q); sem
  float no runtime. TOSS só com `alt>0` (ou dead); o knockdown do M6 termina
  em RISE f84. Pós-M6 medido no candidato `957122ae…` (`jump_*` e `stand` em
  `out/evidence/post_m6/candidate_service_cap128/trials/`): o TOSS preserva a
  altitude de contato (arc 1→2; contatos em alt 0/5/48/51/52/53/55, Δalt máx.
  12/q, Δx máx. 4), sem snap para 0, pouso em alt 0 com arc→0 e RISE em st5;
  alt 1 só na cauda do TOSS (jump_60 i130); contato direto em 46/47 não
  observado (mais próximo 48; a tabela de queda pula 46/47); alt 200
  inalcançável nesta cena (máx. 101).
- **Uploader (D8)**: dois slots por ator (29 células × 2 tiles); commit
  adaptativo em sub-chunks de 64 B, budget 320 B/q compartilhado, margem 22
  linhas, prólogo 30. O registro M6 relata **128 B/q** (2 sub-chunks) neste
  caminho/carga; não é constante física do SMS nem prazo de serviço por ator.
  A pose seguinte é pré-carregada no slot não exibido; a troca de slot só
  ocorre com a cópia pronta. **Escalonador pós-M6 (medido)**: a decisão roda
  na fase CPU (`sched_update` após os dois `stream_update`) e o bloco de
  VBlank só executa a ordem/cap decididos (decidir no VBlank custou o 2º
  sub-chunk: 128→64 B/q). Política selecionada em `957122ae…`: jogador
  primeiro, pré-carga promovida a `up_want` quando coincide com a pose
  corrente, e um `want` de dor do inimigo preempta; contenção 128 B. Matriz
  medida (SHAs/métricas em
  `out/evidence/post_m6/candidate_service_cap128/scheduler_comparison_20261018.json`):
  b345 8 hits/intervalos 72 q/dor 108 e 36 q; dor-sem-promoção 83–100 q;
  promoção+teto 64 com 6 hits e dor 56 q; teto 96 com 7 hits/intervalos 96 q;
  candidato com 8 hits/intervalos 87 q/dor 11 q/morte em i648.
  **Pacing**: o avanço da animação espera a pose ficar pronta. `attack_tap`
  mede ataque i1–i72 com retorno i73 (b345) e i1–i93/i94 (a7f02b84), 1º hit
  i30 em ambos. No cap5 `701379cc`, o ataque termina em i89, o controle volta
  em i90, o 1º hit é i27 e o display volta ao idle em i102 (vídeo 171 q). O
  dano em i129 é o ataque do inimigo (estado2 i103), não recuperação maior; a
  janela antiga de 60 q não era o terminal; os delays nominais 3+3+3+3+9=21
  não são duração wall-clock.
  **Instrumentação**: `O3_SERVICE_TRACE=1` perturba o VBlank (128→64 B/q);
  contadores de serviço são só contabilidade relativa de estágio — o timing
  absoluto vem de builds de entrega (`O3_SERVICE_TRACE=0`) via deltas de
  `up_off` e `probe_vline`. Leitura do bloco: 6 B em `0xC7CC..0xC7D1`
  (bytes_p, bytes_e, flags, pad, vc0, vc1); não ler 20 B (`0xC7D2` é
  `probe_vline_min`).
- **Render**: células posicionadas por `(x - cam) + dx`, `z - 32 - alt + dy`;
  corte por scanline com tabela estática `o3_ax_rows` (D9-a2); HUD por delta
  (faixa alterada; linhas inteiras só no boot com display desligado); coluna de BG fatiada
  (`write_bg_row`/`write_bg_col`, guarda de 26 linhas).
- **Arte na tela (medida)**: a âncora do canvas autoral é `(xh-32, base-80)`;
  `audit_render_fidelity` confirma 100% estrutural na pose estável
  (`ax_a105_right` em [92,68]); poses em troca de slot do uploader não casam
  1:1 (o gate exige pose estável; declarado). Still canônico: sessão
  `598625a4…`.
- **Probe v2** (`0xC7E0..0xC7FF`): `vline` b10, `vovf` b11, `done` b14, frame
  u16 b16..17; `py` @0xC7FD = altitude do jogador, `p2state` @0xC7FE, `p2z`
  @0xC7FF. RAM do candidato WIP: ator de **48 B** com `pl` @0xC000 e `e`
  @0xC030 (`main.sym` do build `957122ae…`: offsets 0 e 0x30 em `_DATA`),
  `cam` u16 @0xC062, `written_col` @0xC064; o layout M6 de 30/34 B
  (`pl` @0xC004 / `e` @0xC026) é histórico. Bloco de serviço só em build
  diagnóstica (`O3_SERVICE_TRACE=1`; sondas declaradas sempre para o gate de
  corredor, escritas/leituras só na build diagnóstica): 6 B em
  `0xC7CC..0xC7D1` (bytes_p,
  bytes_e, flags, pad, vc0, vc1); não ler 20 B (`0xC7D2` = `probe_vline_min`).
  Corredor de sondas verificado (`audit_probe_corridor`).

## Mapa de memória (RAM)
Histórico medido pós-link (O2, build #5, ROM `b0eb624f…`): estáticas do jogador/câmera em `0xC000`
(px u16, pz, facing, anim, walk_frame, anim_timer; `cam` u16 @0xC007;
`written_col` @0xC009); `probe_frame` u16 @0xC7F0; corredor de sondas
`0xC7E0..0xC7FF` (25 sondas, folga 1796 medida). `audit_probe_corridor.py` PASS.
RAM = 8 KiB; nenhuma alocação dinâmica. Candidato WIP: `_DATA` de 0x6F em
`0xC000` (`pl` 48 B @0xC000, `e` 48 B @0xC030, `cam` @0xC062, `written_col`
@0xC064); o mapa O2 acima permanece histórico.

## Entidades, objetos e pools
O2 e O3/M6 têm 1 jogador + 1 inimigo **estáticos**, papéis Ax/Long fixos;
nenhum pool genérico/owner de itens é provado pelo recorte. TEXT, ITEM/pickup,
equipamento quando exigido, OBSTACLE e demais objetos pertencem a O5 do plano,
com fila/owners e dependências em O4. Antecipar owner bloqueante de O5 se a
fila real O4 exigir; nunca saltar evento, contar objeto como inimigo ou tratar
parsing/IR como lifecycle implementado. Pool cheio exige retry idempotente,
sem apagar entidade ou duplicar spawn. Mais inimigos e 2P exigem contrato e
budget próprios; nenhum orçamento de 1P é transferido.

## Features O3 — estado de conversão
| Feature | Tag | Prova/limite |
|---|---|---|
| input causal frame-paced | `exact` | journal grava cada read (bytes de RAM); sessões isoladas |
| hit/dano/guarda (D13) | `adapted` | ticks 200 Hz → frames NTSC; guarda 13 q; traço de morte 8 hits |
| pulo/tombo/knockdown | `adapted` | tabelas por-frame; ápice 55; TOSS com windup 15 q |
| profundidade/alvo móvel em z | `adapted` | `move_toward(dx,dz)`; e.z 185→206 no traço |
| pacing do ataque | `adapted` | hit1 +16 q; cap5 `701379cc`: FSM i1–i89, controle i90, 1º hit i27, display idle i102; dano i129 vem do ataque inimigo (estado2 i103); vídeo 171 q; Lote C reaberto só no critério de controle |
| render fidelity | `exact` | 100% estrutural na pose estável; slot em troca não casa |
| audit_render_glitch | `blocked` | sem renderizador legal full-frame 256×192 validado |
| asset→ROM binding | `adapted` | `doc/rom_asset_binding.json` cap5 `701379cc`: 11 entradas source→res→símbolo→ROM; poses/anim/blocks no linker map, áudio static; `--require` PASS; identidade, não render independente |
| projeção de eixos | `exact` | cap5 `701379cc`: `evidence.json` `a473d670…` e `fps.json` `1ccfa0af…` projetados do bundle `2f69939a…`, consumo `e1af7fad…` e QA `5fe14599…`/`a7662a8b…`; `axis_projection.py` exige `--current-rom` e recusa fonte de outro SHA antes de escrever; M8 `a7f02b84` histórico não se transfere ao cap5 |
| QA cap5 (runtime+visual) | `adapted` | runtime `5aeb7960…` 2/2 PASS (boot frame 400 SMRT hp=100/boss=50; ataque hp=95/boss=43/state=3/p2state=2) e visual `37b1481d…` 2/2 de legibilidade/integridade PASS (81 q, 32 distintos/31 transições; inimigo íntegro em dor/recuperação); teto `assigned_checks_only`; a janela visual prova o início da recuperação (70), não o idle i102 |
| direção do golpe vs alvo | `blocked` | QA visual cap5: no índice 27 a lâmina branca x42..64 e o inimigo x86..132; sem sobreposição visual; dano legível só por HUD 80→64 px e dor em 38; decisão de apresentação do dono pendente; não promove época visual/delivery |
| PAL | `blocked` | não medido |
| FPS/MWF | `adapted` | cap5 `701379cc`: MRP3 59,39/59,44/59,57 fps NTSC, spread 0,18, 1.441 frames, boot/frame_advance true (pacote anterior 59,67/59,69/59,43; 1.438); MWF `vovf=0`/`vline_min=207`; projetado em `fps.json` |
| áudio | `adapted` | M7 PSG implementado; `a7f02b84` (3 SFX, canal 3) e cap5 `701379cc` com sinal fresco (cap5 peak 1986/8,173 s, mask 16). `audit_audio --active-floor 5` (mesmo piso do M8, SFX-only) PASS (6% cap5; 12% a7f); default 90% de música falha; bundle/consumer cap5 `2f69939a…`, áudio `f16b48b8…` projetado; delivery ainda bloqueada por apresentação/Lote C/PAL |

## Máquina de estados
Implementada (O3/M5–M6): estados `idle/chase/attack/hit/drop/rise/dead`;
`startup/active/recovery` vêm do anim (`o3_aframe` com delays e frames
ativos); hitstop é pausa curta com orçamento no loop, não recursão; queda
(TOSS com `alt>0`) e getup (RISE) são arcos tabelados; morte exige hp 0 e
`guard==0` (D13). Transições provadas por input causal no M6 (attack, jump,
knockdown, depth, death) — ver memory bank e `m6_evidence_76cdbee3.json`.

## Banking
- Alvo inicial: **48 KB linear sem mapper**.
- Se exceder: mapper Sega (páginas 16 KB, regs 0xFFFE/0xFFFF), código restrito
  a 32 KB, dados bancados a partir do bank 2.
- Status (O3/M6): ROM **131072 B** bancária (mapper Sega habilitado), 60
  blocos de pose nos bancos 2–6 (79744/81920 B); código/`DATA` restritos a
  32 KB; `audit_probe_corridor` registrado verde no baseline M6 (sem rerun aqui). O2 sem mapper foi o piloto
  (32768 B); o O3 excedeu o linear por medição (D1).

## Áudio
- Driver: PSGlib (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Áudio do PAK (WAV/BOR/OGG) é fonte a classificar/adaptar; **não** converte
  automaticamente para PSG; reautoria/transcrição rastreável e aprovável.
- Arbitração música×SFX (4 canais) declarada quando existir conteúdo; noise
  bit2=1 branco, 0 periódico; preview/FFT/pico não certificam composição.

## Orçamento de frame
- **O2 (piloto, histórico):** quadro inteiro (SAT 33–36 + PNT 48 B/passo de
  8 px + lógica) a **1.0 loop/frame**; janelas 59,4–59,7 NTSC; pico 8/linha.
- **O3/M6 (medido):** SAT até 2×29 células com corte por linhas exatas;
  uploader 128 B/q (2×64 B) + coluna de BG fatiada + HUD por delta. MWF
  3000 quadros `vovf_delta=0`, `vline_min=202`; MRP 3×8 s
  59,48/59,66/59,78 (NTSC); stress com input até quadro ROM 3230 sem `vovf`.
  NTSC medido; **PAL não medido** (declarado). `measure_fps`/
  `measure_frame_advance` são N/A na sessão isolada (o probe mede fps/boot);
  a janela VBlank ~4,5 ms sem DMA continua o contrato.

## Testes
- Host: `python3 -m unittest discover -s tests` em
  `tools/sms_wrapper/openbor2sms/` (fixtures sintéticas; nenhum conteúdo de
  módulo nos testes) + `--self-check` das ferramentas.
- Integração: parametrizada por `--project`, sem caminhos hardcoded no doador.
- Replay de tabela, pool cheio, stale handle, liberação de espera, same-pass,
  interrupções e restart são regressões obrigatórias (O4+).


## Integração documental pós-M6
`doc/artifacts/post_m6_lote_a_report_20261018.json` registra hashes, correções
sem execução e lacunas. O índice sucessor distingue negativo dz41 e positivo
dz6, recupera manifests finais/journals de `/tmp` com origem e bytes próprios
e preserva o índice/selo M6. Manifests `closed`/ACK `close` recuperados não
substituem comprovante histórico completo de cleanup (processos, sink,
display/socket). Não há promoção de qualidade nem herança para outra ROM.

A anotação antiga “commit M6 pendente” da memória é superada por HEAD
`da86de3`; a memória e o registro único serão conciliados pelo coordenador.
Este worker não os edita. Os hashes anteriores permanecem nos snapshots;
o registro único precisa receber o novo hash do escopo e os novos artefatos.
O sucessor é índice documental, não adapter de `reconcile_claims`/`audit_claims`.
