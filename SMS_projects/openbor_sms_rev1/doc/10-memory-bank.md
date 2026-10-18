# 10-memory-bank — openbor_sms_rev1

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
**2026-10-17 — M6 (input causal, alvos móveis e pacing) fechado medido: ROM
`76cdbee3…` (131072 B, bancária) rodou todos os traços causais por input em
sessões isoladas frame-paced. A ROM do M5 (`b0eed40a…`) e a intermediária
(`87954b7f…`) estão STALE; nenhuma evidência delas sustenta claim do M6.**

O que entrou no M6:
- **D13 — guarda pós-hit**: `guard` era armado com 13 e nunca decrementado; a
  vítima ficava imune para sempre e a morte era inalcançável. Fix
  `if (a->guard) a->guard--;` no topo de `actor_advance`, antes do hitstop e
  do gate de pose (contagem em tempo real; o D8 pode segurar a pose sob
  starvation). Traço de morte: 8 hits 50→43→…→0, `dead=1`, estado DEAD f114,
  HUD `hde=0`.
- **Traços causais** (journal grava cada read com bytes de RAM): ataque hit1
  +16q (hp 50→43, guard 12) e hit2 +25q (43→36); pulo maxalt 55, 48q no ar,
  pouso q62, dx 65; knockdown TOSS f32 (alt 2, hp 100→95), RISE f84, maxalt
  51; profundidade whiff dz41 e hit alinhado dz6 (+19q, hp 43→36); morte 8
  hits. `vovf=0` nos traços.
- **Alvo móvel em z**: o inimigo persegue em profundidade — jogador z
  180→221, `e.z` 185→206 (x 272→231) e ataca ao alinhar (st2).
- **Vídeos por claim**: IA (e.x 299→240; 50/60 quadros distintos), ataque com
  dano (hp 50→43 em 60 quadros, 37 distintos), pulo (45 distintos), queda
  (termina em RISE), morte (hp 1→0, st6). Motion timelines e hashes nos JSONs.
- **Pacing medido**: hit do ataque ~16q ≈ 0,27 s; ataque completo ~60q (o
  uploader D8 segura o avanço das 5 poses; não é o somatório nominal de 21q);
  guarda 13q; pain ~85q; caminhada 1,6–1,7× mais lenta que a fonte; TOSS
  pequeno por windup de 15q. O jogador tem prioridade e zera o budget do
  inimigo enquanto sobe pose (usado de propósito no knockdown). O M6 também
  fechou o D8: hoist de locais + gate antes do prólogo baixaram o custo para
  ~10 linhas/64 B; `O3_COMMIT_MARGIN=22`, `O3_COMMIT_PROLOG=30`; throughput
  estável **128 B/q** (2 sub-commits).
- **FPS/pacing**: MRP 3 janelas 59,48/59,66/59,78 (PASS, boot e frame
  advance); MWF 3000 quadros `vovf_delta=0`, `vline_min=202` (PASS); stress
  com input (30 ciclos RIGHT/A/idle/LEFT/B/idle) até quadro ROM 3230,
  `vovf=0`, `done=1` (janela selada). Sessões e journals publicados.
- **Render**: still canônico `598625a4…` mostra a pose final do ataque
  (`ax_a105_right`, 100,0% estrutural em [92,68]) + inimigo em PAIN hp 43 +
  HUD por delta; `screenshot_semantic_gate` PASS (paleta 100%, 18 cores).
  A âncora da arte é `(xh-32, base-80)`; poses em troca de slot do uploader
  não casam 1:1 (o gate exige pose estável; declarado).
  `audit_render_glitch` **BLOQUEADO**: não há renderizador de referência
  full-frame 256×192 validado — declarado, não silencioso.
- **Coluna de BG fatiada**: `write_bg_row`/`write_bg_col` com `col_pend_w`/
  `col_pend_r` e guarda de 26 linhas; scrolling medido no stress
  (cam 160→360→200) sem `vovf`. A decisão aberta do M5 está fechada.
- **Cross-checks**: `audit_tilemap_bounds` OK (16 arquivos, 0 escritas
  ilegais; 5 literais não-provados são macros do HUD); registry `check` ok
  (36 artefatos). `vdp_regs.bin` de BlastEm segue do SHA antigo — regenerar
  no M7/M8 (D13 é lógica, sem mudança de layout de VRAM). `maxfallspeed`
  pinado: entrada 12 px/q, toss 6, pulo 6 (tabelas congeladas; sem
  velocidade acumulada).
- **Limitações declaradas**: PAL não medido; sem áudio (M7);
  `measure_fps`/`measure_frame_advance` N/A; `audit_render_glitch` bloqueado;
  a borda exata da caixa de profundidade (dz 15..41) não foi varrida.

## Histórico M5 (detalhe do fechamento)
**2026-10-17 — M5 (runtime O3: FSM/IA/hit/uploader) fechado medido: ROM
`b0eed40a…` (131072 B, bancária — 60 blocos de pose nos bancos 2–6) roda o
combate O3 a 59,5–59,8 fps medidos (nominal 59,92); `measure_worst_frame` PASS (`vovf_delta=0` em
3000 quadros, `vline_min=207`) e `measure_runtime_probe` PASS (fps
59,5/59,47/59,58; spread 0,11; boot provado) — ambos no mesmo SHA.**

O que entrou no M5:
- **Runtime O3** (`src/main.c`): FSM (idle/chase/attack/hit/drop/rise) + IA do
  inimigo + `resolve_hits` (dano/knockback/arcos) + dois streams de pose
  bancados com troca de slot + HUD de barras; câmera/dicionário herdados do O2.
  Núcleo de desenho de sprites em **asm `__naked`** nos dois loops (C
  equivalente atrás de `O3_DRAW_ASM`) — **A/B asm↔C PASSOU byte a byte**.
- **Uploader (D8)**: `stream_commit` com chunk de **320 B** por ator e
  sub-commit de **64 B**; a cópia adapta relendo `SMS_VCounterPort` a cada
  iteração; `SMS_VRAMmemcpy` (sem OTIR — GG-safe). Margem do gate de commit =
  **30 linhas** (`(64*30)/228 + 22`); com 26 a MWF mostrava 12 derrames rasos
  (~1 linha) por jitter da posição do custo.
- **Custos medidos (Emulicious + `main.lst`)**: 1 iteração real do loop ≈ **16
  linhas** de VBlank / 64 B (~57 c/B); prólogo do ator ~7,3 linhas; cópia da
  SAT ~14 linhas; **coluna de BG = 44 linhas** (medida, quadro 300); **redraw
  da LINHA INTEIRA do HUD = 52 linhas** (quadro 411; 32 tiles ≈ 1,6
  linha/tile) — era o derrame de ~+22 do quadro de dano (estimativa antiga de
  ~35 linhas para 2 linhas era otimista e foi refutada por medição).
- **Correção medida no fechamento (HUD)**: `draw_hud` redesenha só a **faixa
  cujo fill muda** (hit de 5 hp = 1 tile; morte 100→0 = 20 tiles) + **gate por
  tile** (margem 26 = rabo fixo dos commits: 2 prólogos ~14,6 + saída ~2 +
  folga) com **faixa pendente persistente** entre quadros; `draw_hud_boot`
  desenha as duas linhas inteiras no boot (display desligado). Antes: MWF
  `vovf_delta=1`; depois: **0**.
- **Evidência executada no mesmo sha `b0eed40a…`**: MWF PASS (3000 quadros,
  `vline_min=207`); MRP 8 s×3 PASS (fps 59,5/59,47/59,58; spread 0,11; boot
  provado); `capture_evidence` PASS (luta na tela; HUD verde ~95/vermelha 50;
  luma 4031/1696); sessões isoladas fechadas (nenhum Emulicious vivo).
- **Comparação O2→M5** (captura `586141…/evidence.png` vs M5): mesmo palco e
  linhagem de HUD; o O2 mostrava só o jogador, o M5 mostra os dois atores em
  combate na mesma cena.
- **Fluxo do uploader (honesto)**: 1–2 sub-commits de 64 B por quadro
  (64–128 B/f), com prioridade do jogador por design — a animação do inimigo
  avança mais devagar quando o jogador está ativo (aceito e registrado; o
  budget de 320 B/ator nunca engata na prática).
- **Probe v2 (ferramentas — commit à parte)**: `emulicious_dap.py` +
  `measure_runtime_probe.py` + `measure_worst_frame.py` — leitura por DAP sem
  foco de janela; min-capture permanente do pior quadro (frame/cam/p2state em
  0xC7E5–E9; `__at` absoluto, custo ~0 — só escreve em novo mínimo).
- **Limitações registradas**: **coluna de BG = 44 linhas** — com scrolling
  (M6) o stream de colunas precisa de escrita fatiada (2 meias-colunas por
  quadro) ou gate próprio; a janela do M5 tem `cam=0` (sem input). Queda
  grande de vida no HUD é limitada pelo gate (resto sai nos quadros
  seguintes). PAL não medido; sem áudio (M7). `measure_fps`/
  `measure_frame_advance` N/A (sessão isolada) — pacing coberto pelo MRP.
  Build de validação com `O3_SPILL_TRACE 0` (instrumentação TEMP fora).

Histórico O2 (2026-10-16) — o que mudou no O2:
- **Emissão SMS implementada** (`sms_art.py` + `sms_emit.py`, backend separado do
  front-end neutro — nunca importa `semantics.py`): palco por dicionário de
  k-medoides (**K=192**), paletas 6-bit (P0 12 códigos úteis = 10 cena + 2
  reservados HUD; P1 14 códigos + transparente), poses TALL 8×16 (**122 pares /
  244 slots**), colunas do mapa (79 colunas), HUD (3 tiles), spawns, delays e
  **máscara de corte pré-computada** (D10). Budget de VRAM: **439/448**
  (244+192+3), margem 9 não reclamada.
- **Runtime mínimo** (`src/main.c`): jogador com x/z/anim/facing, inimigo idle,
  câmera quantizada em 8 px (`cam=(px-120)&~7`), h-scroll `N=(-cam)&0xFF` com
  anel mod-32 de colunas reescrito a cada passo (inclusive ao voltar),
  `LOCKHSCROLL` + `LEFTCOLBLANK`, backdrop preto, HUD de barras, probe de RAM
  (`SMRT` v1; frame @0xC7F0).
- **Defeito corrigido e medido:** a contagem de corte em runtime (loops
  IX-relative do SDCC, ~115–150 ciclos/iteração) consumia ~2.07 quadros na pior
  pose; a decisão D10 (máscara na emissão) devolveu **1.0 loop/frame** em idle
  (300/300) e caminhada completa (520/520; px 50→484, cam 0→360, clamps ok).
- **Evidência executada:** vídeos frame-paced walk6/depth6/up6/back6 na sessão
  isolada publicada (`58614148…`), bundle de boot + capture.json publicados no
  projeto, probe em janelas (fps 59.58/59.73/59.57), `measure_vram_map` aprovado
  com 2 snapshots BlastEm, pixel 1:1 do framebuffer (0 divergências fora dos
  sprites em cam_col 45/41/3/8/0; HUD exato; faixa preta), fidelidade 1:1 da arte
  (jogador idle 1072 px e walk 999 px exatos; inimigo 0 divergências fora de
  corte/cobertura), `screenshot_semantic_gate` PASS, bundle selado (18 artefatos),
  `reconcile_claims`/`audit_claims` PASS, registry `ok:true --scan`
  (24 artefatos / 22 grupos / 56 arquivos com subconjunto de arte, records e
  runtime assets O2 registrados); sessão `58614148…` fechada ao final (`state
  closed`, nenhum Emulicious vivo).
- **Fechamento de lote (gates aplicáveis, uma vez):** `audit_deterministic_boot`
  **PASS** (2 execuções com estado idêntico; boot estático de quadro único);
  `audit_hardware_constants` PASS; `audit_header_claims` PASS; `audit_luma_floor`
  PASS (pares HUD/cena declarados); `audit_debug_markers` /
  `audit_symbol_size_sync` / `audit_placeholder_quarantine` /
  `audit_rom_asset_binding` / `audit_visual_delivery` / `audit_specialization` /
  `canonical_fixture_gate` PASS; `audit_doc_sync`: **0 derivas no projeto**
  (FAIL global = 10 derivas pré-existentes de luta_mugen, EIO); unittest 56 OK;
  self-checks `sms_art`/`sms_emit`/`openbor2sms` OK; `validate_measurement_tools`
  69/69.
- **Substituições declaradas (não contornadas):** `measure_fps.py` (título de
  janela inexistente na sessão isolada) e `measure_frame_advance.py` (HUD sem
  dígito-contador) são N/A — pacing coberto por janelas do probe + ritmo de loop;
  rota de input moderna da sessão isolada no lugar de `--press`; `measure_worst_frame`
  incompatível com o plano (prova = probe + simulações + pixel 1:1).
- **Limitações registradas:** ordem de corte do inimigo é estática (colunas
  visíveis da direita podem cair antes de outras; seleção x-aware adiada);
  3 coordenadas do HUD auditadas via defines; `audit_tilemap_mirror` =
  aprovado_com_não_provado; PAL declarado e não medido; sem áudio (fora do O2).
- **O1 (histórico):** front-end neutro de 5 módulos + IR tipado com origem;
  gates do lote verdes (detalhe abaixo).

Registros e provas do O2 (2026-10-16; hashes revalidados nesta sessão):
| Artefato | SHA-256 |
|----------|---------|
| `out/rom/openbor_sms_rev1.sms` (build #5, 32768 B) | `b0eb624f4978d542c08513bf2aa2676da0a15c37d8879abdb9f58339be261385` |
| `out/build_record.json` | `ae5af4fc3e1bcfdcbfcc7d75f5121c47545ba7344a5f522b8651ab843dc10a85` |
| `data/generated/art/o2_art_conversion_20261015.json` | `9b1f7ce533fae0a10185db1df2f308c81c557e799d2be822cdcf021af4d317a9` |
| `data/generated/emit/o2_emission_20261016.json` | `e3655919c4eb0c313e2bd3acd53aa8f6ed1cc66a2c7b1a0ef99dd8cd54b088e8` |
| `data/generated/plans/o2_vram_plan_20261016.json` | `fa4c9a2a7e06ec63657ab4a46acfac3b0c0c4162d89a42f6fb8de06a935b2172` |
| `inc/o2/enemy_mask.h` (máscara D10) | `fcf2d3d2babcf63ce15db5ca038b359dcf4759f1235f1685b09b37bb846aa0c3` |
| `out/evidence/o2_evidence_bundle_20261016.json` (18 artefatos selados) | `f1ad7623033dfb0183fa7de771a5a715d8def677c7eb9475d804571c23de44d4` |
| `doc/artifacts/o2_vdp_pilot_scope_20261016.json` (rev2) | `98faf180052d0d0e63c35aae1d323100548b72bf256a4156b2dcf0aa3048b3e5` |

Manifestos de sprite (6): `data/generated/emit/o2_sprite_scene_{idle01_left,idle01_right,walk01_left,walk01_right,walk03_left,walk03_right}_20261016.json` — 33–36 sprites, pico 8/linha, cortes 2–5 (shas no emission record). Sessão publicada: `out/evidence/sessions/586141485ce34b87aef6ece6ab4936b5/` (bundle de boot + `runtime/runtime_probe.json`); vídeos walk6/depth6/up6/back6 registrados no bundle (frames em `/tmp/smsforge-1000/586141…/evidence/`); snapshots BlastEm em `out/evidence/blastem/regs_20261016/`.

Detalhe do lote O1:
- **5 módulos neutros portados byte-idênticos + banner** (caminho/sha do doador,
  licença MIT): `model_text.py`, `level_inventory.py`, `analyze.py`,
  `reference_semantics.py`, `level_event_table.py`; 3 testes import-adaptados
  (só o import; asserções intactas). `semantics.py` **não** é front-end: codifica
  budgets MD do doador (pool 1424, VRAM 1408, célula 80, tela 320) — fronteira
  de emissão MD.
- **`frontend.py`** no motor (modos `extract`/`ir`) + dispatch + `test_frontend.py`.
- **Emissões:** subconjuntos GAL (town1 + models) e BT (01 + models) em
  `data/source_openbor/`; registros de extração, 4 IRs, diff de determinismo e
  manifesto de porte em `data/generated/` (hashes abaixo).
- **Determinismo PASS:** replays byte-idênticos dos 4 IRs com stamp fixa +
  replays normalizados dos 2 registros de extração.
- **Diagnósticos preservados (nada omitido em silêncio):** BT usa a forma de
  player start de 2 argumentos (`spawn1 x z`) que o parser doador (fiel) não
  aceita → 2 issues (linhas 6–7), `player_starts` vazio, lowering de eixos do
  BT bloqueado até decisão de semântica; GAL neutro: 160 diretivas / 26 comandos
  distintos / 23 spawns / 4 player starts / 0 issues; o membro town1 extraído
  bate com a matriz do doador (`1d167c8c…`).

Registros e provas do O1 (13 arquivos novos, todos no `artifact_registry`; hashes revalidados em 2026-10-15):
| Artefato | SHA-256 |
|----------|---------|
| `data/generated/port/openbor2sms_port_manifest_20261015.json` | `5f3b17132363a336ade7df61e999756f013d1c3ec71dc6367d7f3b011b82d8a4` |
| `data/source_openbor/gal_town1/data/levels/town1.txt` | `1d167c8cc703b815a32dbb4953c53af7f42532a6a647507a7e009e61377cc54d` |
| `data/source_openbor/gal_town1/data/models.txt` | `fbd18005ffbdb6346315896abd774fdf4c716ce148f7b07c9e1a9d047ff37581` |
| `data/source_openbor/bt_rescue/data/levels/01.txt` | `bbc691d1bb81a000c7c0ccd9c7187b6fdf59c0ad0eab4896861116925b972a9d` |
| `data/source_openbor/bt_rescue/data/models.txt` | `c15cc13b5a07a77aba64ca2854693ae808721953e9b1f3040ef41dd606e9d71a` |
| `data/generated/extract/gal_town1_extract_20261015.json` | `eee60d5e70215f23f6eb258faa1aea23fcb3ed414cc091b2f950a467190a0998` |
| `data/generated/extract/bt_rescue_extract_20261015.json` | `03c1ec32000396bc334f8e53e97a9d93fd4592bb3769c531f77e9944cbb40f34` |
| `data/generated/ir/gal_town1_level_ir_20261015.json` | `a9c6be9132e14fcd8bcad87f62ab90fcc8ab81b8d7cb256e15da5b5a0d57b4a1` |
| `data/generated/ir/gal_town1_models_ir_20261015.json` | `b44ad9e86a402f4b1e120d5f16ed970bd3d579757d6579cd11698ae607a3903a` |
| `data/generated/ir/bt_rescue_level_ir_20261015.json` | `bef0f287d6b2d48a0930b1b0ad70cd80f063c4ea9861eec1ac00f2eca2d3b619` |
| `data/generated/ir/bt_rescue_models_ir_20261015.json` | `8e1d8fbe4fcd987bc016287d5f0487e6bf22e2470c99e65402fb1d9b5fe8ad6b` |
| `data/generated/ir/determinism_diff_20261015.json` | `3a3e8b07577c41e6301ed59119be115a0c04a8db73c3ecfc71a8e083b4dcb4b7` |
| `doc/artifacts/o1_neutral_frontend_scope_20261015.json` | `7ce34bb8c0478f6d017a0f0f1d8d7df29244f5b0a709c67a905d1a24e56fb34f` |

Registros e provas do O0 (todos revalidados em 2026-10-15):
| Artefato | SHA-256 |
|----------|---------|
| `data/generated/intake/gal_pak_intake_20261015.json` | `8ec356a6fc10cc6fd9cd4df64aa716eb2058970ad46925e533e3f153202a31c1` |
| `data/generated/intake/bt_pak_intake_20261015.json` | `72cbff963486e6f77c5196a1b8d924cf27f0001ea839e0f422e1b624af90ae6e` |
| `data/generated/intake/donor_source_manifest_20261015.json` | `37ee39dfa349ebb32a684dc544f6b32bca7ac19f8c621d014e349034c4f78e82` |
| `data/generated/intake/dependency_inventory_20261015.json` | `69be8331841d842a6749494b0eeaf47e174da1bf4582348e53db13327bf081ab` |
| `doc/artifacts/o0_pilot_compatibility_boundary_20261015.json` | (registrado no artifact_registry) |

Medições próprias do intake (ferramenta `openbor2sms`, não herdadas):
- GAL.pak `64da17e8…50634c4`, 39.500.889 B, `PACK v0 PAK32 (32-bit)`, **3502
  entradas**, 0 unsafe, 0 colisões de caso, 39.359.149 B de dados (reproduz o
  número do doador: 3502).
- battle_toads.PAK `f2c5319d…46e7a6`, 36.324.119 B, `PACK v0 PAK32 (32-bit)`,
  **2151 entradas**, 0 unsafe, 0 colisões, 36.246.466 B de dados.
- Árvore Python do importador doador re-hasheada: `0701fdb5…ec842b` (32 arquivos
  `.py`) — idêntica à registrada pelo doador.
- Contrato/matriz do doador porteram 13 capacidades + 1 módulo-específica
  (`gal_town1_player_start`), 7 perfis declarados, 11 blockers, 13 medições
  reutilizáveis, 18 arquivos do conversor — com SHA-256 de origem no registro.

## Eixos de entrega (7) — gate final exige os 7 simultâneos
| Eixo | Status | Prova |
|------|--------|-------|
| build | `buildado` | ROM `76cdbee3…` (131072 B) = `out/rom`; build reprodutível (comentário não muda SHA) |
| validation_report | `buildado` | MWF PASS (`vovf_delta=0`, 3000 quadros, `vline_min=202`) + MRP PASS (59,48/59,66/59,78) — mesmo SHA |
| boot no emulador | `testado_em_emulador` | MRP boot provado + still canônico `598625a4…` (256×192) + sessões isoladas publicadas |
| gameplay | `testado_em_emulador` (recorte M6) | traços causais de ataque/pulo/queda/profundidade/morte + alvo móvel em z; videos por claim |
| fps regional (NTSC/PAL) | `testado_em_emulador` (NTSC) | MRP 8 s×3: 59,48/59,66/59,78; **PAL declarado, não medido** |
| áudio | `não iniciado` | M7 |
| memory bank atualizado | `documentado` | este arquivo + registros O0/O1/O2/M5/M6 |

> Status válidos: `não iniciado`, `documentado`, `implementado`, `buildado`,
> `testado_em_emulador`, `validado_budget`. Toda linha diferente de
> "não iniciado" EXIGE prova citada (caminho de arquivo/captura), não prosa.
> **O M5 não é o gate final de entrega**: gameplay por input causal (M6),
> áudio (M7) e PAL pendentes — marco medido, não delivery.

## Decisões registradas
- **Pilotos:** GAL = piloto inicial (recorte TOWN1 já inventariado pelo doador,
  perfis `gal_town*`); Battletoads = segundo piloto para **generalização real**
  (perfil `bt_rescue`; pré-flight de tiles já medido: nativo rejeitado, legado
  880 tiles/512 px de 2390 px). BT não é cópia do mesmo código com outro nome.
- **Origem externa dos PAKs: desconhecida** (documentado pelo doador). O pin
  OpenBOR `787b6770…` é referência semântica **condicional** (extrato parcial
  BSD-3-Clause), não origem demonstrada dos módulos.
- **Licenças:** doador MIT (`0b685fab…`); OpenBOR LICENSE BSD-3-Clause
  (`b8f39169…`); PAKs não publicáveis; licença de ferramenta não licencia
  redistribuição de personagens.
- **Sem cópia dos PAKs para o repo**: fontes permanecem no scratch do doador
  (read-only); `data/source_openbor/` receberá apenas **subconjuntos extraídos**
  sob controle, em O1; o PAK completo nunca vira `res/`.
- **Fronteira de compatibilidade v0** (por capacidade, estados
  `exact/adapted/blocked/dropped_by_owner`): registrada em
  `doc/artifacts/o0_pilot_compatibility_boundary_20261015.json`.
- **Motor:** `tools/sms_wrapper/openbor2sms/` — `pak.py` portado fiel (banner com
  SHA do doador `13de21ee…`; teste do doador portado) + `intake.py` (O0) +
  `frontend.py` (O1, modos `extract`/`ir`) + os 5 módulos neutros portados + 3
  testes import-adaptados; `--self-check` verde, 56 unittest em O1.
- **Front-end neutro = 5 módulos (correção do O0):** `semantics.py`,
  `emit_slice.py`, `images.py`, `streaming.py` e `profiles.py` ficam na
  fronteira de **emissão MD** (budgets do doador não viram lei SMS). A emissão
  SMS é backend separado (O2+); o front-end nunca importa `semantics.py`.
- **Registro multi-arquivo:** um artefato pode ter mais de um arquivo, com
  papéis únicos por arquivo (subconjuntos: `source` para level + `models_index`
  para models); `artifact_registry.py` rejeita papel duplicado dentro do
  artefato.
- **O2 — máscara de corte pré-computada (D10):** o corte do inimigo por
  orçamento de 8 sprites/linha é decidido na **emissão**
  (`inc/o2/enemy_mask.h[(pose*73+(pz-160))*3]`, 3 B/entrada, bit = célula), com
  política conservadora; o runtime só consulta o bit e pula `sx>255`. A
  contagem em runtime (loops IX-relative do SDCC) custava ~2.07 quadros na pior
  pose. Detalhe no escopo rev2.
- **O2 — scroll/câmera (medidos):** `cam = clamp(px-120,0,376) & ~7`; h-scroll
  `N = (-cam) & 0xFF`; tela x≥8 mostra a coluna PNT `cam_col+(x>>3)`; anel
  mod-32 de colunas reescrito por passo de 8 px (inclusive ao voltar);
  `LOCKHSCROLL` (HUD fixo) + `LEFTCOLBLANK` (x0..7); backdrop preto.
- **O2 — budget de VRAM:** 439/448 tiles (244 sprites + 192 BG + 3 HUD);
  K=192 do dicionário; margem 9 não reclamada; pockets nenhum.
- **O2 — paletas:** P0 12 códigos úteis (10 cena + 2 reservados do HUD) índice 0
  opaco; P1 14 códigos + índice 0 transparente (keyed); dither Bayer 4×4 só no
  palco; PNGs de `res/o2` guardam a paleta ×85 (RGB do emulador).
- **O2 — `palettes_manifest.json` adiado:** paletas canônicas no record de
  conversão; nenhum gate do O2 consome `--character`; criar quando O3+ exigir
  paleta por personagem (evita arquivo-morto).
- **O3/M5 — uploader bancado (D8):** cópia banco→VRAM em chunks de **320 B**
  por ator com sub-commit de **64 B**; o loop relê `SMS_VCounterPort` e para o
  chunk quando a margem acaba (retoma no quadro seguinte); margem do gate de
  commit = **30 linhas** (`(64*30)/228 + 22`; iteração ~16 + jitter ~2–3 +
  rabo do 2º ator ~9,3 + folga) — calibrada por MWF (26 deixava 12 derrames
  rasos ~1 linha).
- **O3/M5 — HUD por delta + gate por tile:** o redesenho da linha inteira no
  quadro de dano custava 52 linhas e derramava; agora só a faixa cuja cor muda
  é redesenhada, com **faixa pendente persistente** e gate por tile (margem
  26) — o restante sai nos quadros seguintes, sem mudança visual.
- **O3/M5 — coluna de BG (herança O2) = 44 linhas medidas:** com scrolling
  (M6) não cabe ao lado do resto do bloco (SAT ~14 + coluna 44 + rabo ~17);
  decisão adiada para o M6 (escrita fatiada por sub-coluna ou gate próprio).
  Registrado como limitação, não contornado.
- **O3/M5 — método de localização de estáticas:** símbolos `__at` são
  absolutos e o `.map` não lista estáticas locais do módulo; a base do módulo
  foi achada por **varredura de assinatura na RAM** (base 0xC000;
  cam=0xC045, written_col=0xC047, hp_drawn=0xC048, spill_v=0xC04A–C) — offsets
  de objeto do `.lst` + base = endereço linkado.

## Blocker dominante atual
**O3 (combate e IA) em andamento desde 2026-10-16** (escopo
`doc/artifacts/o3_combat_scope_20261016.json`, D1–D12). Fechados: **M1** — smoke
de mapper+uploader no laboratório (`SMS_projects/_laboratorio/mapper_vblank_copy`;
veredito medido em dois emuladores: a cópia bancada→VRAM **fora do VBlank chega
íntegra**, 1856/1856 B; a regra §9 permanece por efeito visual; L136 candidata
aguarda autorização do dono) e **M2** — IR de animação no frontend (`--kind
model`; records por personagem hasheados, no registry). Reconciliação D4
confirmada no IR: as caixas do recorte vivem na **diretiva** `attack2` (slot 2)
*dentro de* `anim attack1` (ax a102–a104: 240,142,44,62,7,…,15,15; long
a102–a103: 240,158,40,46,5,…,10,15) e a `anim attack2` usa `attack` (slot 1) —
diretiva ≠ animação; atribuição estado-até-limpar confere com a fonte.
**M3 fechado (2026-10-16)**: 60 pose-sides convertidas no canvas medido (80×96;
células 8×16 conferidas contra o escopo), P1 herdada do O2 sem mudança
(rms/canal 23,76); 30 GIFs sha-bound pelo extract r2; determinismo byte-idêntico;
gates `audit_validate_resources` (60 PNGs), `audit_luma_floor` (pares declarados
+ near pairs dY=9 documentados), `audit_provenance`, registry `check --scan`
todos PASS; 68 testes.
**M4 fechado (2026-10-17)**: emissão O3 determinística byte a byte — 6 headers
(`inc/o3/o3_poses.h`, `o3_blocks.h`, `o3_rows.h`, `o3_anim.h`, `o3_arcs.h`,
`level.h`), bancos do mapper 2–6 (79744/81920 B, 60 blocos), plano de VRAM
427/448 (reg6 `0xFB`), 12 manifests. **D9-a (bandas de 8 linhas) refutado por
medição** durante a emissão (solo declarado fall03/death01 caía 10 células por
cascata entre linhas adjacentes): política revisada **D9-a2 — contagem exata
por scanline** (tabela estática `o3_ax_rows[32][6]` no ROM + `ec[6]` de u8 na
RAM; passo 16 px ⇒ linha visível coberta por ≤1 linha de cada ator). Varredura
declarada: 48.384 casos, pico 8 = limiar, 0 violações; cross-check brute force
540/0; solo declarado = exatamente 1 drop (a 9ª célula da linha). Gates: 12/12
manifests `audit_sprite_line_sim` + `measure_vram_map` aprovado + registry
`check --scan` ok (35 artefatos); 84 testes. Records `o3-emission-r1` +
`o3-bank-blocks` no registry.
**M5 fechado (2026-10-17)**: runtime O3 no emulador — FSM/IA/hit/uploader +
A/B asm↔C byte a byte + MWF `vovf_delta=0` (3000 quadros) + MRP 59,5 fps,
tudo no SHA `b0eed40a…` (detalhe na "Última atualização").
**M6 fechado (2026-10-17)**: input causal em sessões frame-paced (journal com
bytes de RAM), ataque/pulo/knockdown/profundidade/morte, alvo móvel em x e z,
vídeos por claim, pacing medido, MWF/MRP/stress no SHA `76cdbee3…`; D13
(guarda pós-hit) corrigido e provado pela morte. A decisão da coluna de BG
foi fechada com escrita fatiada (`write_bg_row`/`write_bg_col`, guarda 26) e
scrolling medido sem `vovf`. `audit_render_glitch` declarado **bloqueado**
(sem renderizador legal full-frame); `maxfallspeed` pinado; `vdp_regs.bin`
fica para M7/M8 (mudança lógica, sem layout novo).
Blockers persistentes registrados (não bloqueiam O3): origem externa dos PAKs
desconhecida; `skills_scripts_and_callbacks` = unknown; medições MD não
transferíveis; **player-start de 2 argumentos do BT sem decisão de semântica**
(bloqueia lowering de eixos do BT; o GAL segue); **ordem de corte do inimigo é
estática** (seleção x-aware adiada — limitação visual declarada, não bloqueia);
`measure_fps`/`measure_frame_advance` N/A na sessão isolada (substituídos pelo
probe); PAL não medido; sem áudio. Restrição de lote: `semantics.py` e decisões
MD ficam fora do front-end neutro.

## Lições abertas
- **Curadoria do lote O2 feita em 2026-10-16**
  (`doc/curation/2026-10-16_l134_l135_openbor_o2_runtime_e_hscroll.json`;
  `audit_learning_capture --root .` PASS, self-check OK):
  1. **L134 (§125)** — loops IX-relative do SDCC custam ~115–150
     ciclos/iteração; decisão por varredura vai pré-computada na emissão
     (D10; máscara 3 B/entrada). Ferramentas: `measure_runtime_probe`,
     `audit_sprite_line_sim`;
  2. **L135 (§126)** — sinal do h-scroll `N = (-cam) & 0xFF` e anel mod-32 de
     colunas reescrito inclusive ao voltar; **fechada por evidência** — sem
     gate estático; candidato de ferramenta declarado para O4/terreno;
  3. pacing por contador na ROM — **aplicação** de L013/L035/L082/L089 (sem ID
     novo; `measure_fps`/`measure_frame_advance` continuam N/A na sessão
     isolada);
  4. vigilância de ids de tile/par TALL — **aplicação** de L006/L069; nenhum
     incidente documentado no O2 (offsets u8 + base K=192; pid*2 ≤ 242).
- **L136 candidata medida, aguardando autorização do dono** — o caso controlado
  do laboratório (`mapper_vblank_copy`, evidência de dois emuladores) refuta
  L047/§9 **como mecanismo de perda de dado**: a cópia bancada→VRAM fora do
  VBlank chega íntegra (1856/1856 B; ~230 linhas de cópia, ~8,07 B/linha). A
  regra §9 permanece por **efeito visual** (resíduo de redesenho a meio quadro).
  Fechamento previsto: `doc/curation/2026-10-16_l136_vram_fora_do_vblank.json`
  + §127 + emenda do bullet §9 + ledger/rotas (evitar co-mingling); **nada
  escrito sem autorização**.
- Reincidência vigiada: medição de outro console não é prova (L001);
  representação errada não vira gate humano (L036).
- Registro: artefato com mais de um arquivo exige papéis únicos por arquivo (o
  gate rejeita papel duplicado) — subconjuntos usam `source` + `models_index`.
- Janela de sessão: ferramentas que escrevem no diretório de sessão do projeto
  (`measure_runtime_probe` → `runtime/`) precisam que a publicação do bundle
  venha **antes** (a trava de publish é `target.exists()`); ordem registrada no
  O2.

## Handoff
O2 fechado medido e commitado (`555bb64`). **O3 em curso: M1–M4 commitados
(`2d728da`) e curadoria L134/L135 (`2b2f4b3`) + L136 (`b6a2046`)** — branch
`feat-luta-mugen-motor`, sem push (autorização do dono pendente).
**M5 fechado e commitado** (`4cb4d0b`, `70078c8`, `9ba2b6b`).
**M6 fechado medido nesta sessão** (ROM `76cdbee3…`; traços causais + MWF
`vovf_delta=0`; MRP 59,5; still com render fidelity 100%). Próximo passo:
1. **Commit do lote M6**: pendente — `src/main.c` (D13 + comentário da coluna),
   `doc/artifacts/o3_combat_scope_20261016.json`, `doc/artifact_registry.json`,
   este memory bank, `doc/15-tdd.md` e as evidências em `out/evidence/m6/`,
   `m6_evidence_76cdbee3.json`, `mwf_m6_76cdbee3_20261017.json`,
   `mrp_m6_76cdbee3_20261017.json`, `m6_stress_input_…json` + sessões. Sem push.
2. **M7 (áudio)**: SFX mínimos (D11), `capture_audio`/`audit_audio`/
   `audit_psg_quality`/`audit_psg_channel_binding`/`audit_audio_provenance`.
3. **M8 (fechamento)**: `audit_doc_sync`, `audit_causal_persistence`,
   `audit_visual_delivery`, `audit_mastery_registry`, regenerar `vdp_regs.bin`
   de BlastEm no SHA final e fechar os 7 eixos.
4. Pendências declaradas que não bloqueiam: PAL não medido; áudio (M7);
   `audit_render_glitch` bloqueado (sem renderizador legal full-frame);
   semântica de `spawn1 x z` (BT, diagnóstico preservado em `bef0f287…`);
   `audit_doc_sync` global FAIL por luta_mugen (EIO pré-existente, não tocar).

Nota herdada do O0: `data/source_art/concept_art/` materializado **vazio** é o
local designado do registry; sem contratos de arte em O0/O1, o
`audit_reference_boundary` passa a ser significativo quando houver contratos a
auditar (O2+).
