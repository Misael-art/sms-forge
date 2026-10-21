# B.2b-3b — Política de SAT do fallback sprite-only

**Resultado:** nenhum candidato foi promovido. A quota 6+2 (v042) passa
8 sprites/linha e o vídeo 256×192, mas custa 22,0% do pacing
(`smrt_frame=4483` vs 5745) e viola §129 nas duas atribuições de papel
(6>5 no ataque do jogador ou 2<3 no piso do jogador). A quota 5+3 (v043)
maximiza o primário dentro do teto (5) e mantém o secundário no piso (3);
passa linha/§129, mas o escalar ainda custa 12,4% (`smrt_frame=5033` vs
5745). O próximo passo é pré-computar a lista 5/3 e medir o pacing.

## Mandato e baseline

- §92: híbrido BG corpo + partes/FX na SAT; se falhar, comparação concreta
  e tradeoff declarado, sem reduzir arte/escala/FX em silêncio.
- Baseline de pacing: v036 sprite-only `7002b0ba…` = 5745 no selo 300 s;
  v040 `d998209b…` = 5743; alvo do gate `smrt_frame >= 5745`.
- Produção canônica intocada: `087df676…`; `src/main.c` `042ba22e…`.

## Candidatos

| candidato | política | pacing | linha (8/linha) | §129 | vídeo | veredito |
|---|---|---|---|---|---|---|
| v036 | sprite-only, SAT-64 | 5745 | — | — | — | render fail (P2 26%) |
| v037 | híbrido v3 (BG+SAT) | 3945 (−31,3%) | 0/64 | — | — | render pass 1 quadro; pacing fail |
| v040 | sprite-only, ordem alternada | 5743 | **FAIL** pico 14; 78/77 linhas >8 | — | pass | linha fail |
| v041 | cap whole-cell com varredura de 16 linhas | **2055 (−64,2%)** | PASS sim. 39/8 | — | — | pacing fail |
| v042 | quota 6+2 por banda de 16 px | **4483 (−22,0%)** | **PASS** 40/8, 0 overflow | **FAIL** (6>5 ou 2<3) | pass | **pacing fail** |
| v043 | quota escalar 5+3 | **5033 (−12,4%)** | **PASS** 40/8 | **PASS** (f002) | pass | **pacing fail** |

## v041 — o cap por linha é caro demais

O cap whole-cell reduziu a SAT a 39 células e a simulação passou 8/linha,
mas a varredura de 16 linhas por célula derrubou o pacing para 2055
(−64,2%). `worst_done=0`, `sat_om=17029/17266`, `vbl_exit_max=255`.
Não é um caminho de produção.

## v042 — a quota 6+2 passa a linha, mas não o pacing nem §129

- ROM `4431533947b96c84…`, fonte `main.c.rowquota_v042`
  (`efde6b88…`), corredor 110 sondas / folga 1539 B.
- Selo 300 s: `smrt_frame=4483`, `vovf=2506`, `worst_done=1`,
  `sat_om_p1=33993`, `sat_om_p2=47462`, `sat_frames=4483`,
  `add_total_max=70` (tentativas; SAT válida = 40), `vbl_exit_max=255`,
  `stage_slice_max=215`.
- SAT real (BlastEm padded, snapshots 1020/1021): `SpriteNextFree=40`;
  P1 30 células (6 por banda × 5), P2 10 (2 × 5); linha **PASS 40/8,
  0 overflow**.
- §129/L137: P1 player → ataque 6 > 5 (fail); P2 player → 2 < 3 (fail).
  O 6+2 é inválido por construção nas duas atribuições; o 5+3 maximiza o
  primário dentro do teto (5) e mantém o secundário no piso (3). O 4+4
  também passaria, mas reduz mais o primário; o 5+3 é a escolha de máxima
  completude do primário.
- Vídeo: 600 quadros, 133 distintos, 256×192, 59,92 Hz,
  `max_from_initial_fraction=0,1158`, SHA `783ccd0c…`. A alternância
  anti-fase aparece em 573/600 quadros; a saturação é ~7,5 Hz porque o
  loop do jogo caiu para ~14,9 fps.
- **Cautela de captura:** os PNGs pareados f1020/f1021 do v042 têm o mesmo
  SHA (`ccdd51c5…`) e mostram o lado cheio **oposto** ao shadow SAT do
  snapshot 1020; a captura está um quadro de jogo atrasada/adiantada.
  O veredito visual usa o vídeo e a SAT shadow, não o par de PNGs.
- **Sonda `present` inválida sob quota:** qualquer célula omitida marca o
  lado inteiro como 65535; não usar `present` como gate desta política.
  `sat_om` é omissão declarada (≈18 células/quadro), não falha de SAT-64.

## v043 — quota escalar 5+3: linha/§129 passam, pacing ainda falha

Fonte `main.c.rowquota_v043` (`eb5576ad…`), ROM
`13b78bd2435673df…`, corredor 110 sondas / folga 1539 B. Remove o array
`row_count[16]` e o clear por lado; usa `last_dy`/`row_n` escalares e quota
5/3 calculada uma vez por lado.
- Selo 300 s: `smrt_frame=5033` (**−12,4%** vs 5745; **+12,3%** vs v042
  4483), `vovf=2506`, `worst_done=1`, `sat_om=28094/51482`,
  `sat_frames=5033`, `vbl_exit_max=255`, `stage_slice_max=214`,
  `damage_p1=1000`, `ko_events=1`. **Pacing fail.**
- SAT real (BlastEm padded, snapshots 1020/1021): snapshot 001 = 25
  células (P2 primário 5/banda; P1 em transição, não emitido); snapshot
  002 = **40 células** (P1 15 = 3/banda; P2 25 = 5/banda), `SpriteNextFree=40`.
  Linha **PASS 40/8** nos dois; §129 **PASS** no f002 nas duas atribuições
  (jogador 3 ou 5; ataque ≤5; inimigo ≥2 e ≥5).
- Vídeo: 600 quadros, 127 distintos, 256×192, 59,92 Hz,
  `max_from_initial_fraction=0,1190`, SHA `a257e6ee…`. O 5/3 é mais
  equilibrado que o 6/2 (lado cheio ~1957, faixa ~974; v042 2223/596),
  mas a seleção “primeiras N” ainda pode produzir listras; o próximo
  passo é seleção espacial contígua/central.

## Tradeoff §92 — concreto

1. **Híbrido v037**: render 100% em um quadro, SAT 0/64, mas pacing 3945
   (−31,3%). O writer row-batched/contíguo (≤66 T/célula) não foi tentado;
   é a única rota que devolve SAT para partes/FX.
2. **Sprite-only v040**: pacing ≈baseline, mas o VDP descarta a 9ª+ entrada:
   pico 14/linha, 78/77 linhas em overflow, P2 26% do P1. O SAT-64 e a
   linha são orçamentos distintos; a ordem alternada distribui a omissão,
   mas não a elimina.
3. **Quota v042**: pacing 4483 (−22,0%), linha pass, visual de um corpo
   cheio + faixa de 2 células do outro, alternando ~7,5 Hz. A SAT válida
   cai para 40/64. É a primeira política que passa a linha, mas o custo de
   pacing é alto e §129 reprova o 6+2.
4. **Quota v043 5+3**: passa linha e §129, mas o pacing 5033 ainda fica
   12,4% abaixo de 5745. O escalar recuperou 12,3% sobre o v042; o custo
   restante é a checagem por célula. O próximo passo é **pré-computar a
   lista limitada** (5/3) por pose/lado e emitir sem checagem por célula —
   preserva o pacing e permite seleção centrada/contígua, em vez do corte
   “primeiras N” enviesado para a borda. Ainda é omissão declarada, não
   render 100%.
5. **Limite físico**: dois corpos de ~56×80 não cabem inteiros em 8
   sprites/linha. Sem híbrido, a escolha é omissão declarada (quota) ou
   violação de linha (v040); não há terceira opção no sprite-only puro.

## Decisão

- v042 **não é gate-passing**: pacing fail e §129 fail; não promover.
- v041 **não é gate-passing**: pacing fail; não promover.
- v040 **não é gate-passing**: linha fail; não promover.
- v037 **não é gate-passing**: pacing fail; R&D.
- v043 **não é gate-passing**: pacing fail (5033 < 5745); linha/§129
  passam. O 5/3 é a política recomendada, mas a implementação escalar
  não paga o pacing; a lista pré-computada é o próximo candidato.
- Aprovação humana pendente para o fallback, a política 5/3, a seleção
  espacial e a geração da lista pré-computada.
- Aprovações pendentes: fallback/FX, empacotamento 1 MB, guarda BlastEm +
  lição **L139**, política de quota (5+3 vs 6+2), geração de lista
  pré-computada.

## Evidência e custódia

- Relatório B2b-3 anterior preservado:
  `out/logs/runs/20261020T005000Z_b2b3_decision.json`.
- SAT shadow v040: `b2b3b_sat/shadow_f001.json`/`f002.json`
  (64 sprites, pico 14, 78/77 linhas).
- SAT shadow v042: `b2b3b_sat/shadow_v042_f001.json`/`f002.json`
  (40 sprites, pico 8, 0 overflow).
- SAT shadow v043: `b2b3b_sat/shadow_v043_f001.json`/`f002.json`
  (f001 25 em transição; f002 40 = 15+25, pico 8).
- §129: `b2b3b_sat/silhouette_v042.json` (P1 30, P2 10; 6/2 fail) e
  `silhouette_v043_f002.json` (15/25; 5/3 pass; limitação: mede células,
  não pixels nem a ROM).
- BlastEm v042: `blastem_v042_1020_1021/blastem-sms-f2832c39…`;
  v043: `blastem_v043_1020_1021/blastem-sms-dec09ac7…`.
- Vídeo v042: `captures/video_v042_pair.mp4` + `.json`;
  v043: `captures/video_v043_pair.mp4` + `.json`;
  v040: `captures/video_v040_pair.mp4`.
- Custódia: `out/evidence/loteB2b_20261019/b2b3b/`.
- Self-checks: `reports/tool_selfchecks.txt` — `audit_sprite_line_sim`,
  `capture_video`, `measure_worst_frame`, `blastem_sms` e
  `emulator_session` **OK**.
- Limitações: `audit_silhouette_integrity.py` é O3-específico; a contagem
  §129 do luta_mugem é manual e declarada. A captura pareada v042 não é
  sincronizada com o snapshot SAT. O v043 f001 é uma transição com P1 não
  emitido; a amostra de política é o f002. O selo mede um estado de luta
  que pode diferir do v040; o que vale é o contador de frames do loop, não
  o resultado do combate.
