# 10-memory-bank — openbor_sms_rev1

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
**2026-10-16 — lote O2 (piloto VDP) fechado medido: ROM build #5
(`b0eb624f…`, 32768 B) roda a ritmo cheio (1.0 loop/frame) com movimento x/z,
facing, animação, 1 inimigo, cenário rastreado por dicionário e HUD de piloto;
evidência selada (18 artefatos) e claims reconciliados.**

O que mudou no O2:
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
| build | `buildado` | ROM build #5 `b0eb624f…` (32768 B) = `out/rom` = `out/build_record.json` |
| validation_report | `buildado` | pre-gates verdes no build; `reconcile_claims` PASS (eixos declarados batem com artefatos) |
| boot no emulador | `testado_em_emulador` | bundle publicado `out/evidence/sessions/586141…/` (capture.json, canvas 256×192, sha da ROM); registradores BlastEm (`out/evidence/blastem/regs_20261016/`) |
| gameplay | `testado_em_emulador` (recorte O2) | vídeos walk6/depth6/up6/back6 + probe RAM (px/pz/facing/cam) + pixel 1:1 do framebuffer; **sem combate (O3)** |
| fps regional (NTSC/PAL) | `testado_em_emulador` (NTSC) | janelas do probe 59.58/59.73/59.57 (nominal 59.9227…); **PAL declarado, não medido** |
| áudio | `não iniciado` | fora do escopo O2 (declarado) |
| memory bank atualizado | `documentado` | este arquivo + registros O0/O1/O2 |

> Status válidos: `não iniciado`, `documentado`, `implementado`, `buildado`,
> `testado_em_emulador`, `validado_budget`. Toda linha diferente de
> "não iniciado" EXIGE prova citada (caminho de arquivo/captura), não prosa.
> **A entrega O2 não é o gate final de entrega**: áudio/PAL pendentes e o corte do
> inimigo tem limitação declarada — O2 é marco medido, não delivery.

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

## Blocker dominante atual
**O3 (combate e IA) não iniciado.** O backend SMS existe e o piloto VDP O2 está
medido; falta jump/attack/damage/IA e revisão humana dos artefatos de piloto —
sem isso não há eixo de gameplay completo nem delivery.
Blockers persistentes registrados (não bloqueiam O3): origem externa dos PAKs
desconhecida; `skills_scripts_and_callbacks` = unknown; medições MD não
transferíveis; **player-start de 2 argumentos do BT sem decisão de semântica**
(bloqueia lowering de eixos do BT; o GAL segue); **ordem de corte do inimigo é
estática** (seleção x-aware adiada — limitação visual declarada, não bloqueia);
`measure_fps`/`measure_frame_advance` N/A na sessão isolada (substituídos pelo
probe); PAL não medido; sem áudio. Restrição de lote: `semantics.py` e decisões
MD ficam fora do front-end neutro.

## Lições abertas
- Candidatas a curation do O2 (fechar na curadoria do lote, com ferramenta):
  1. loops IX-relative do SDCC custam ~115–150 ciclos/iteração em Z80 — orçamento
     de linha não se conta no runtime; pré-computar na emissão (D10);
  2. sinal do h-scroll: `N = (-cam) & 0xFF` (não `cam`) e anel mod-32 de colunas
     fechando o wrap de 256 px, inclusive andando para trás;
  3. `SMS_waitForVBlank` quantiza o ritmo; medir o loop com contador na ROM
     (`measure_runtime_probe`) em vez de inferir de título de janela;
  4. id de tile truncado (se reincidir) e validade do id de pares TALL.
- Reincidência vigiada: medição de outro console não é prova (L001);
  representação errada não vira gate humano (L036).
- Registro: artefato com mais de um arquivo exige papéis únicos por arquivo (o
  gate rejeita papel duplicado) — subconjuntos usam `source` + `models_index`.
- Janela de sessão: ferramentas que escrevem no diretório de sessão do projeto
  (`measure_runtime_probe` → `runtime/`) precisam que a publicação do bundle
  venha **antes** (a trava de publish é `target.exists()`); ordem registrada no
  O2.

## Handoff
O2 está fechado medido (build #5; evidência selada; claims reconciliados).
Próximo passo exato — **autorização de commit** (o lote está pronto para
revisão humana) e, após, O3:
1. **Commit**: aguardar autorização explícita do dono; nada foi commitado
   (árvore `?? SMS_projects/openbor_sms_rev1/` e `?? tools/sms_wrapper/openbor2sms/`).
2. **O3 (combate e IA)**: jump/attack/damage/IA por fonte com startup/active/
   recovery; hitboxes com profundidade; FSM; o corte do inimigo ganha seleção
   x-aware se necessário; herdar orçamento medido (8/linha, 439/448).
3. **Curadoria do lote** (depois do commit): fechar as lições candidatas do O2
   em `doc/curation/` com ferramenta que mede (loop IX-relative → tabela na
   emissão; sinal do h-scroll/anel; pacing por contador na ROM).
4. Pendências declaradas que não bloqueiam O3: PAL não medido; áudio não
   iniciado; semântica de `spawn1 x z` (BT, diagnóstico preservado em
   `bef0f287…`); `audit_doc_sync` global FAIL por luta_mugen (EIO pré-existente,
   não tocar).

Nota herdada do O0: `data/source_art/concept_art/` materializado **vazio** é o
local designado do registry; sem contratos de arte em O0/O1, o
`audit_reference_boundary` passa a ser significativo quando houver contratos a
auditar (O2+).
