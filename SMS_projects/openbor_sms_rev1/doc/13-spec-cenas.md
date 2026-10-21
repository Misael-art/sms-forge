# 13-spec-cenas — openbor_sms_rev1

> Budget REAL por cena. **Autoridade #3.**
> Regra: **"estimado" é proibido neste arquivo.** Todo número aqui é medido,
> com o método da medição citado. Folga não medida é timidez (§18).
> **Baseline O3/M6: commit `da86de303bca969a393032d270c9d245d4055180`, ROM
> `76cdbee3f10a58a07199b9012ff6dbe53df372d7532d6a8aa324089824425e73`
> (131072 B).** Conciliação documental pós-M6 em 2026-10-18, sem nova execução.
> O2 permanece histórico por SHA; cena 02 segue fora da medição SMS (O7).

## Contrato de hardware (fixo, não negociável)
| Recurso | Limite físico |
|---------|---------------|
| Tela | 256×192 |
| VRAM | 16 KB |
| RAM | 8 KB |
| Sprites por scanline | 8 |
| Sprites na SAT | 64 |
| Subpaletas CRAM | 2 × 16; BG índice 0 visível; pixels de sprite P1 índice 0 transparentes |
| Cores por uso BG P0 + sprites P1 | até 16 BG + 15 sprites; códigos repetidos reduzem cores distintas |
| Janela VBlank | ≈4,5 ms NTSC no modo 192; orçamento útil depende da carga medida — **não existe DMA** |
| ROM sem mapper | 48 KB |

## Cena 01 — TOWN1, baseline O3/M6

Valores conferidos por leitura de `inc/o3/level.h`,
`data/generated/plans/o3_vram_plan_20261017.json` (SHA
`9c8831757812186f24555c09e589e30bfc59e8675a73fd3bfbac2565519a1099`) e
`data/generated/emit/o3_emission_20261017_r2.json`. São contagens/layout
estáticos; as medições de runtime abaixo são registros históricos da ROM
`76cdbee3…`, sem herança para uma próxima build.

### Layout O3 conferido nos arquivos

| Região | Faixa | Tiles | Bytes | Uso |
|---|---|---|---|---|
| patterns sprite | tiles 0..231 / `$0000..$1CFF` | 232 | 7424 | dois slots de 58 tiles por ator; 29 células TALL 8×16 por slot |
| patterns BG | tiles 232..423 / `$1D00..$34FF` | 192 | 6144 | dicionário TOWN1 herdado de O2 |
| patterns HUD | tiles 424..426 / `$3500..$355F` | 3 | 96 | verde 424, vermelho 425, preto 426 |
| total de patterns | tiles 0..426 | **427/448** | **13664** | 21 tiles / 672 B antes da PNT; não reclamados |
| name table | `$3800..$3EFF` | — | 1792 | 32×28×2 B; HUD nas linhas 0..1 |
| SAT reservada | `$3F00..$3FFF` | — | **256** | 64 Y + 64 de intervalo + 128 X/tile; payload completo de 192 B |
| janela sprite reg6 | `$FB`: `$0000..$1FFF` | 256 endereçáveis | 8192 | 232 usados por slots; BG também ocupa tiles 232..255 |
| extra name tables / pockets | nenhuma / nenhum | — | 0 | nenhuma sobra de PNT/SAT apropriada |

A SAT não é uma região de 128 B: esse é apenas o vetor X/tile. Reserva de
256 B confirmada em SMS_GLOBAL §124 e `SAT_RANGE=(0x3F00,0x4000)` do wrapper;
`SMSlib.h` confirma índice de sprite de 8 bits, PNT em `$3800` e reg6 `$FB`
via `SMS_useFirstHalfTilesforSprites`. A geometria física não é throughput.
O BG índice 0 é visível inclusive quando um tile seleciona P1; o índice 0
é transparente apenas no pixel de sprite. A linha de cores acima descreve
BG P0 + sprites P1, sem pretender contar backdrop/blanking separadamente.

O registro M4 `o3_emission_gates_20261017.json` traz PASS de
`measure_vram_map` **em plan-mode** e self-check registrado. Os snapshots
`out/evidence/blastem/regs_20261016/` pertencem à ROM O2; não há cross-check
de registradores vivos de M6 nesses dumps. A base pretendida é reg6 `$FB`,
PNT `$3800`, SAT `$3F00`; confirmar dumps do SHA candidato no próximo lote.

### Orçamento e limites registrados para a ROM M6

| Eixo | Registro existente | Alcance |
|---|---|---|
| SAT | teto de composição 58 células, pico pós-corte 8/linha | emissão D9-a2: 48384 casos, 0 violações; 540 cross-checks; não mede integridade artística |
| perdas de arte | pior par bruto 17/linha; Long solo 9/linha | corte determinístico; fall03/death01 perdem 1 célula solo; revisão artística pendente |
| uploader | sub-commit 64 B; teto compartilhado 320 B/q; 128 B/q neste caminho/carga; escalonador pós-M6 medido: jogador primeiro, pré-carga promovida a *want*, dor do inimigo preempta, contenção 128 B | tetos 64/96 medidos e rejeitados; 128 B/q é resultado do caminho, não limite físico nem serviço garantido ao inimigo. Prova: `out/evidence/post_m6/candidate_service_cap128/scheduler_comparison_20261018.json` |
| HUD / cenário | HUD por faixa alterada com gate; coluna BG fatiada com cursor persistente | guardas 26 linhas no código; sem usar o custo O2 como folga de M6 |
| worst-frame | MWF 3000 quadros, `vovf_delta=0`, `vline_min=202` | `out/evidence/mwf_m6_76cdbee3_20261017.json`; não equivale a duração CPU, folga livre ou aprovação com PSG/PAL |
| ritmo regional | MRP 3×8 s: 59,48 / 59,66 / 59,78 NTSC | `out/evidence/mrp_m6_76cdbee3_20261017.json`; vídeo stepped prova sequência, não taxa real |
| stress | frame ROM 3230, `vovf=0`, `done=1` | `out/evidence/m6_stress_input_d5639465181a463a926f0e01f4d7af46.json`; janela e input próprios |
| ataque | cap5 `701379cc`: FSM i1–i89, controle i90, 1º hit i27, display idle i102; `a7f02b84`: i1–i93/controle i94, 1º hit i30; b345: i1–i72/retorno i73. Dano i129 é ataque do inimigo (estado2 i103), não recuperação. Vídeo 171 q | duração wall-clock é limitada pelo upload de pose (display 12 q após o controle); corte cap5 14 células; cache/delta analítico, não medido; somatório nominal 21 q não é duração runtime. Prova: `out/evidence/o3_silhouette_presentation_20261019/` e `out/evidence/post_m6/candidate_b345/trials/attack_tap` |
| áudio / PAL / glitch global | M7 implementado/capturado no `a7f02b84`; cap5 pendente / PAL não medido / glitch bloqueado | não promover entrega, qualidade ou zero-glitch; áudio do cap5 não é eixo fechado |

Índice sucessor: `doc/artifacts/post_m6_evidence_index_20261018.json`;
preservação e hashes: `out/evidence/post_m6_history/20261018_lote_a/`.
Ele qualifica o histórico e não é novo selo de frescor nem adapter dos gates.
Gates focados do candidato pós-M6 `957122ae…`:
`out/evidence/post_m6/candidate_service_cap128/gates/gates_20261018.json`
(SHA `44a591c561b944b9ae148ee7198527da6304c6752d66a110d64fbe97ac53aa4f`).
`measure_fps`/`measure_frame_advance` seguem N/A nesta rota isolada;
`measure_worst_frame` foi usado no M6 e sua incompatibilidade abaixo é
restrita ao O2. Folga estática de 21 tiles não aprova o degrau seguinte;
novo uploader, PSG, carga e região exigem medidas próprias.

## Histórico O2 — Cena 01, build #5

ROM `b0eb624f4978d542c08513bf2aa2676da0a15c37d8879abdb9f58339be261385`,
32768 B, encerramento O2 de 2026-10-16 (commit `555bb64`). Os valores e
vereditos desta seção descrevem esse binário. Não são o layout nem o budget
O3/M6; correções de paleta/SAT acima são de geometria, não nova execução O2.
### Layout de VRAM declarado (plano `sms_vram_plan_v1`, MEDIDO)
Fonte: `data/generated/plans/o2_vram_plan_20261016.json` (`fa4c9a2a…`).

| Região | Faixa (tiles) | Tiles | Bytes | Uso |
|--------|---------------|-------|-------|-----|
| patterns sprite | 0..243 | 244 | 7808 | atores (122 pares TALL 8×16) |
| patterns BG | 244..435 | 192 | 6144 | dicionário do cenário (k-medoides, K=192) |
| patterns HUD | 436..438 | 3 | 96 | trilho + barras do HUD de piloto |
| **total de padrões** | 0..438 | **439/448** | 14048 | margem 9 |
| name table | `$3800` (`name_base` 14336) | — | 1792 | PNT 32×28 (linhas 0..1 = HUD) |
| SAT | `$3F00..$3FFF` | — | 256 reservados | atores (HUD na PNT); 128 B são só X/tile |
| janela de sprite (reg6) | `$FB` | — | — | $0000..$1FFF (256) — sprites na metade baixa |
| name table extra (reg2) | — | — | — | **nenhuma** (`extra_name_tables: []`) |
| sobras reclamadas | — | — | — | **nenhuma** (`pockets: []`; margem 9 não reclamada) |

Veredito: `measure_vram_map.py --plan … --snapshots <sessão>` **aprovado**
(0 blockers, 2 snapshots de sessão BlastEm; cross-check de reg6/reg5).
Registradores no boot: r0=64 (M4+LEFTCOLBLANK+LOCKHSCROLL), r1=62, r2=FF,
r6=FB (`audit_blastem_sms` ok, escopo `record_consistency_only`).

### Orçamento worst-frame (MEDIDO — política da máscara D10)
| Item | Valor medido | Método da medição |
|------|--------------|-------------------|
| sprites na SAT | 33–36 (≤ 64) | `audit_sprite_line_sim.py` sobre as 6 poses (pior caso z=180 sobreposto) |
| pico de sprites/linha | **8** (= limite 8; sem omissão além do corte declarado) | idem |
| cortes do inimigo | no encontro (z=180): 5 (idle) / 2–3 (walk); pior caso em toda a faixa de pz: 7 células (idle, pz 181+) | máscara `inc/o2/enemy_mask.h` (3 B/entrada; 6 poses × 73 pz; todas as 438 entradas cortam ≥1 célula) |
| escrita de PNT por passo de 8 px | 1 coluna × 24 linhas = 48 B | `sms_emit` (colunas) + verificação 1:1 do framebuffer |
| ritmo do loop (ROM) | **1.0 loop/frame** em idle e caminhada completa (300/300 e 520/520) | `measure_runtime_probe.py` (`probe_frame` 1:1 com o frame do emulador) |

- **Total worst-frame**: o quadro inteiro (SAT + PNT por passo + lógica) cabe em
  1 quadro NTSC com folga de loop (1.0); o defeito anterior (contagem de linha em
  runtime, ~2.07 frames) foi eliminado pela máscara pré-computada na emissão.
- **Headroom**: 12853 B de ROM livres (conteúdo até `0x4DCA` em 32768 B);
  9 tiles de VRAM não reclamados.
- **Método**: `measure_runtime_probe.py` (janelas de frames da própria ROM via
  DAP) + `audit_sprite_line_sim.py` + verificação pixel 1:1 do framebuffer.
  `measure_worst_frame.py` é **incompatível** com o plano do lote O2
  (declarado, não contornado) — a prova de orçamento deste lote é a dupla
  acima, nunca uma estimativa.
- **Degrau seguinte medido**: decisão D10 registrada no escopo O2 rev2
  (`doc/artifacts/o2_vdp_pilot_scope_20261016.json`).

### Sprites por scanline (pico) — MEDIDO
Manifestos `data/generated/emit/o2_sprite_scene_*_20261016.json` (6 poses):
33–36 entradas na SAT, pico 8/linha, cortes 2–5. Modo **SPRITEMODE_TALL
(8×16)** obrigatório (8×8 estoura a SAT: ~94 objetos > 64 — medição do rev1).
Espelho = padrões próprios (VDP do SMS não tem flip de sprite).

### fps observado — MEDIDO (NTSC)
Janelas do `measure_runtime_probe`: 59.58 / 59.73 / 59.57 (sessão publicada
`586141…`) e 59.41 / 59.72 / 59.42 (sessão de calibragem) — nominal
59.92274340431231, ≥5 amostras. **PAL declarado (idle 4 / walk 6 frames) e não
medido; fora dos claims do O2.**
Substituição declarada: `measure_fps.py` (lê o título da janela do host) e
`measure_frame_advance.py` (exige dígito-contador em tela; o HUD do O2 não tem
texto) são **N/A** na sessão isolada sem janela — os eixos de pacing são
cobertos pelas janelas do probe + ritmo de loop 1.0.

## Cena 02 — bt_rescue (segundo piloto, O7)
Fora do escopo de medição imediata. Pré-flight herdado do doador (não é mediação
SMS): nativo rejeitado (1158 tiles vs 896 aceitos), legado 880 tiles cobrindo
512 de 2390 px com 3 slots de inimigo — **a reconfirmar por medição própria
apenas se o perfil mudar** (assets/budget).
