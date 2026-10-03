# 10-memory-bank — luta_mugen

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Opção B medida (variante `decoupled`, soco do P1) — 2026-10-01

Cópia isolada `out/local_study/trace_b/` (gitignored), variante `decoupled` do
`luta_mugen_trace_dap.py`; fonte canônica intocada. ROM estado `ff021901…`,
ROM profile `8406a4ee…`; 1 execução cada, só `soco` do P1, janela de 170 ticks.

- **Lógica (estado):** soco aceito no tick 10; quadros de 1, 1, 2, 12 (4 de AIR
  + 8 de hitstop), 2, 1, 2 ticks — segue o AIR; **dano ao P2 no tick 14**
  (1000→950), contra o tick 134 do baseline (124 ticks após o toque).
- **Arte (pose visível do P1 por tick, modo profile):** o idle continua em tela
  até o tick 54; só então aparece **uma** pose de soco (id 32, a última das 7),
  do tick 55 ao 85 (31 ticks). Ou seja, **1 de 7 poses de soco é exibida, 45
  ticks depois do toque e 41 depois do dano; a ação lógica terminou no tick 30**.
- Leitura: B resolve o tempo da lógica e **quebra a causalidade visual** — o
  golpe machuca sem ser visto e a única pose mostrada aparece muito depois. A
  banda de upload (~3 pares/quadro, poses de 27–37 pares) não mudou; B só
  tira a espera da lógica. Não é aceitável como entrega sozinha; B precisa de
  garantia de arte (poses-chave do golpe em tela na janela de hit) = A ou C.
- Não medido: P2, demais ações, FPS/latência humana, custo de flicker.

**Segunda rodada (escolha do usuário: B + residência seletiva)**, mesma cópia
isolada, executor `out/local_study/trace_b/run_key.py` (registra variantes em
runtime; `tools/sms_wrapper` não foi alterado). Poses do soco do Ken: startup
26 (34 pares), **hit 29 (29 pares, única com Clsn1)**, recuperação 32 (34);
união das 3 = 63 pares únicos (startup/recuperação quase iguais por conteúdo);
a união dos 7 quadros = 125 de 225. Pool no idle: pico 100 de 128 → 28 livres.
- Residência das 3 poses-chave (63) **não cabe**; a de hit sozinha (29) excede
  a folga por 1 par; tirar o prefetch do Ryu libera no máximo 20 e dobra o
  período do idle dele. Limite de 128 pares é de hardware (tile de 8 bits).
- `decoupled_key` (ordem de streaming: hit → recuperação, preemptando o
  prefetch do idle; ROM `9bfb7bc7…`): pose de hit só no **tick 33** (23 após o
  toque, depois do fim da ação lógica, tick 30), 1 de 7 poses. Banda do Ken
  ~1,3 pares/tick (29 pares ≈ 22 ticks) — ordenar não basta.
- `decoupled_pin` (pose de hit fixada na VRAM no boot, só facing 0; ROM
  `bab8f023…`): **pose de hit em tela do tick 13 ao 39** (toque 10, dano 14);
  recuperação (32) do tick 40 ao 60; 2 de 7 poses. **Custo: pool no teto
  (pico 128) e o idle do Ken cai de 4 para 8–24 ticks por pose** (prefetch do
  idle sem folga). Variante só diagnóstica: pino só do Ken e só virado à
  direita; esquerda cai no streaming normal.
- Leitura: a residência resolve a causalidade do golpe mas consome a folga que
  o idle precisa. Para fechar é preciso liberar ~13+ pares (estimativa, não
  medida) no idle de um dos lutadores (menos pares por pose de idle) ou
  reduzir a pose de hit; escolha de arte/escopo. Nada adotado na fonte
  canônica. Uma execução por variante, só `soco` do P1.

## Estudo SMS×SGDK — itens 1 e 2 do roadmap — 2026-09-30

Estudo e roadmap: `doc/21-estudo-comparativo-sgdk-roadmap-2026-09-30.md`. Estado
**implementado** (análise de host) e **testado em pytest**; **não** testado em
emulador e não altera a ROM `c958278f…`.

- `tools/sms_wrapper/mugen2sms/analysis/move_checklist.py` (matriz de golpes,
  com coluna de suporte ao pad SMS via `converters/sms_cmd.py`) e
  `analysis/anim_time_contract.py` (linha do tempo AIR de referência vs modelo
  do runtime; janela de hit vs `time=N` do HitDef). Ambos têm `--self-check`;
  o do contrato de tempo falha sob mutação da fórmula de duração.
  `character.py` expõe `raw_states`; testes em `mugen2sms/tests/test_analysis_move_anim.py`
  (7 passam). Desvio de `character.py` e os dois módulos novos pinados em
  `doc/doacao_md_mugen2sms.json`.
- Suíte `mugen2sms/tests`: 102 passam, 7 falham — todas em `test_donation_parity`
  (deriva do doador MD em `generators/runtime_format.py`, `generators/scene_cut.py`,
  `ir/controllers.py`, `ir/expr.py`, `ir/opcodes.py`, `palette_contract.py`,
  `source.py`). Falhavam antes (8 sem as mudanças deste lote); não foram tocadas.
- Leitura real em `ken_masters_adv.zip` (saída em `out/local_study/study_2026-09-30/`,
  gitignored): 70 entradas de comando → 4 OK, 2 DEGRADED, 64 BLOCKED. **Todos
  os 86 bloqueios citados são de pad** (44 "botão>pad", 42 "diagonal-impossível").
  O pad tem 1 botão; a arquitetura atual usa um mapa de controle escrito à mão
  em `fight.c` (K_LP/K_HP/K_SPECIAL), não derivado do `.cmd`. Consequência: o
  número 64 BLOCKED mede a ausência de uma camada de remapeamento
  declarada, não a qualidade do conversor. **A QCF+B1 do GDD aparece como
  diagonal impossível no conversor** — o especial só existe porque o runtime
  o liga a uma tecla dedicada; isso contradiz o GDD até haver decisão.
- Contrato de tempo no Ken: 161 ações; 17 com a janela de hit do runtime
  (1º quadro visível com Clsn1) fora do `time=N` do HitDef; 1 com `time>254`
  truncado; 0 com `time=0`. O modelo **usa o LoopStart do AIR**; como o gerador
  preenche `loop_start` do runtime não foi verificado. `stall` (espera de pose
  visível) é parâmetro, não medição; o atraso de 26/125 quadros do Lote C
  **não** é explicado por esta análise.

**Follow-up (mesmo dia): mapa de controle por tempo de pressão** — decisão do
usuário: sem golpes médios, 2 tiers (`a/c` soco, `x/z` chute), T=6 ticks
(estimativa, sem dado de jogador). Detalhes em
`doc/22-mapa-de-controle-sms-2026-09-30.md`. Implementado
`converters/sms_controls.py` (`ControlMap`, `classify_trace`, `--self-check`),
ligado à matriz, e `integrada/src/input_tier.c` (classificador O(1), 4 B de RAM;
teste diferencial gcc contra a referência Python, mutação detectada; **não
ligado à ROM**, sem build SDCC nem custo Z80). **Correção do achado anterior:** o
pad SMS tem `KEY_1` e `KEY_2` e diagonais são duas direções (`SMSlib.h:296-302`);
`converters/sms_cmd.py` e `analysis/fidelity.py` herdavam "1 botão" e "diagonal
impossível"; **corrigido em L093** (diagonal = união de bits; golden atualizado;
`audit_hardware_constants.py` agora reprova a premissa). Ken, 70 entradas,
mapa adotado: 19 OK, 19 DEGRADED, 27 DROPPED (só usam `b`/`y`), 5 BLOCKED (4
acordes de super fora do escopo do GDD, 1 golpe sem hitdef). QCF é digitável.
Pior caso de espera: T−1 = 5 ticks (83 ms a 60 Hz), somado ao atraso de
entrada já não aprovado. Ligar ao runtime exige estados/poses de golpe forte
(o corte do Ken tem só soco e chute; pool 125/128) e o `main.c` ainda lê B2
como guarda.

Rastreio e aprendizado: `doc/curation/2026-09-30_l093_l095_assimilacao_sgdk_controle_sms.json`
(L093–L095, `SMS_GLOBAL` §78–80, ledger). Bateria integral PASS: selftest 64/64,
validate_measurement_tools 47/47, audit_doc_sync, audit_learning_capture,
audit_hardware_constants; mugen2sms 109 passam / 7 falham (deriva do doador, anterior).

Item 3 (juiz): `analysis/trace_compare.py`, L096 (`SMS_GLOBAL` §81) — reprova cauda
perdida que o `zip` do doador aceitaria; **sem produtor de trilha SMS ainda**.

**Item 3 (produtor, L097, `SMS_GLOBAL` §82):** `tools/sms_wrapper/luta_mugen_trace_dap.py`.
A ROM clone (`integrada/trace/trace_rec.c`, ganchos `inc/trace_hooks.h`) grava 12 B/tick
em 0xC800.. a partir de um roteiro de entrada embutido (pad real ignorado) e o DAP
despeja o buffer após `done=1`. Ganchos de custo zero: ROM idêntica com e sem eles
(`--check-canonical`, SHA `c1ecaba5…`; difere do `c958278f…` do Lote C por outras
mudanças da árvore local, ex. `fight.c`, não pelos ganchos). Cenário `soco`, 2
execuções independentes: ROM clone `4a049f76…`, despejo idêntico, `trace_compare`
equivalente. Conteúdo: P1 aceita o soco no tick 10; quadros trocam nos ticks 36, 73,
102; dano ao P2 no tick 134 (1000→950, hitstop) = 124 ticks depois do toque,
coerente com os 26/~125 do Lote C, agora por tick e reprodutível. Limites: só
estado da luta (não render/SAT/FPS/latência humana); janela de 170 ticks; ~2,5 min
por execução; só `soco` executado (idle, soco_p2, agachar, andar_frente, pulo
definidos). Os intervalos entre quadros do soco (26, 37, 29, 32 ticks) não foram
comparados com o AIR nesta passagem.

**Atraso de animação, medido por tick (L098, `SMS_GLOBAL` §83):** `analysis/trace_vs_air.py`.
Soco (estado 6, AIR 260), ROM clone `4a049f76…`: AIR 2,1,2,4,2,1 ticks; medido 26, 37,
29, 35 (8 de hitstop), 13, 12; lentidão 12,73x sobre 5 quadros completos; `hit_done` no
tick 134 (124 após o toque), contra a janela do AIR no tick 5. Em todos os quadros o
contador de animação ficou parado em 0 pelo menos o atraso: é a guarda "pose desejada
visível" de `tick_anim`, ou seja, **throughput de streaming de poses**, não FSM, entrada
nem tabela (a tabela destilada preserva 2,1,2,4,2,1,2). Caminhada (estado 1, AIR 20):
1 quadro completo, AIR 3, medido 15 (5x). Limites: atribuição por trilha + código, não
medida direta da pose visível; golpe com poses ainda não residentes; 170 ticks.
**Achado lateral:** em `andar_frente` P1 atravessa P2 (x 96→155 com P2 em 152) e o
auto-facing vira o estado para andar-para-trás: sem colisão de corpo (playerpush).

**Banda de upload (L099, `SMS_GLOBAL` §84):** perfil de fase (`--profile`, ROM instrumentada).
`stream_step` começa em VCounter ~0xD4 e termina ~0xE5–0xEB; o upload avança 3 pares em ticks
alternados e o Ryu (idle) usa a outra paridade: ~3 pares/quadro no total. Poses do soco do
Ken (acao 260): 34, 37, 27, 29, 27, 37, 34 pares (225; pool de 128), 0–2 pares compartilhados
entre poses consecutivas: upload por delta não ajuda. AIR pediria ~17 pares/tick numa pose
de 34 pares em 2 ticks. Variantes em clone isolado: `urgent_first` (ROM `c38f02f6…`) 140→132
ticks, hit 134→123; `action_first` (ROM `415df368…`) hit 134→88 (-34%), 12,73x→9,79x, custo:
idle do Ryu parado 40 ticks contra 20. Ainda 88 ticks (~1,5 s) até o golpe: injogável. Uma
execução por variante; só soco do P1. Nenhuma variante foi adotada na fonte canônica.
**Decisões de escopo pendentes (não são otimização local):** (A) reduzir pares por pose de
ataque (arte/key poses, ~12 pares para cadência de 3 ticks); (B) desacoplar a lógica de hit do
tempo de arte (muda a regra "pose antes da hitbox"); (C) residência seletiva de poses de ataque
(pool 125/128 não comporta 225 pares).

Próximo: decidir A/B/C; usar a trilha para provar que otimizações não mudam o estado;
item 4 (estados por `.def`); ligar `input_tier` à ROM depende de assets de golpe forte.

## Lote C — palco, HUD, PSG e ciclo de rounds — 2026-09-30

O estado vigente de flicker continua sendo a decisão humana opção 3:
**flicker mínimo, nenhum glitch**. Os trechos históricos posteriores de A2/B
que preservam o critério antigo de zero flicker continuam como histórico; não
definem o aceite atual. PASS de L091 com janela 8 não significa flicker zero.

### ROM e build

Fontes próprias em `integrada/`; receita `tools/sms_wrapper/build_luta_integrada.py`.
Os geradores de palco/HUD e PSG agora ficam em `tools/sms_wrapper/` e recebem
o caminho do projeto como argumento; o build integral numa cópia isolada gerou
a mesma ROM SHA abaixo. A ROM de evidência canônica não foi sobrescrita.
ROM `out/local_study/luta_integrada/out/rom/scale_pilot_80px.sms`, 655360 B,
SHA-256 `c958278fa0196e84deecab1fef01f976100072cd9851e9c233f82a694a882999`.
O build/self-check passou antes das leituras. `build_luta_integrada.py
--check-only` repetido depois: PASS em RAM estática e vínculo banco→ROM.

- `_DATA` termina em `0xC720`; `_INITIALIZED` em `0xC726`; os símbolos
  absolutos ocupam até `0xC800`. SAT própria: `_sat_y` `0xD000..0xD047`,
  `_sat_xt` `0xD048..0xD0D7`, `_tmpl` `0xD100..0xD1EF`. Reset define SP
  `0xDFF0`; reserva estática medida: 3584 B. Profundidade de chamada não
  medida.
- Banco 37 coincide com `pose_meta_37.bin`; bancos citados 2–23 e 25–36
  coincidem com a imagem. Banco 24 não é citado pela tabela de poses.
- `doc/rom_asset_binding_lote_c.json` liga a ROM, o PNG técnico do palco,
  streams PSG e fontes/bancos dos dois lutadores; auditoria de vínculo PASS.
  Ryu segue piloto técnico temporário de bootleg NES; Ken segue o alvo visual
  CPS2. A arena é fixture técnica original, não arte final.

### Sistemas integrados e medidos

- `stage.c`: arena estática sem scroll, piso em y=128, âncoras x=96/152,
  tiles de fundo a partir do tile 256. `hud.c`: barras, timer, placar e
  mensagens em tiles da name table, fila fixa, até duas células sujas por
  VBlank. Vídeo idle mostra palco, os dois lutadores de 78–80 px e HUD.
- `main.c`: intro ROUND/FIGHT, luta ativa, resultado e fim de partida.
  Timer de 99 s por round, contado em 60 frames NTSC da própria ROM; empate
  no timeout/KO duplo não pontua; melhor de três, primeira pessoa a 2 pontos
  encerra. `B1` do P1 reinicia após vitória.
- Probe NTSC final `lote_c_integrado_ntsc_stability30.json`: 59,59 e 59,75
  FPS em janelas independentes de 30,14/30,09 s, spread 0,16, delta total
  3594 frames; boot, avanço e cadência constante passaram. Uma leitura curta
  de 8 s deu 58,26/58,44 FPS; a medição mais longa confirmou a faixa-alvo.
  PAL não medido.
- DAP, mesma ROM: P1 soco aceito na borda (`tl_presses` +1), pose visível em
  26 frames, hitbox em 125; P2 perdeu 50 de 1000 pontos de vida (`damage_events`
  +1). Outro trace: P2 soco aceito, pose em 18 e hitbox em 39 frames, mas
  errou pela distância fixa. P2 guarda visível em 20 frames. A leitura visual
  da guarda de P1 ficou ambígua. Direções seguem mascaradas; o piloto lê B1
  como soco e B2 como guarda, divergindo do mapa final do GDD.
  Comparação descritiva com a linha de base B: P1 soco 30→26 frames até pose
  e 127→125 até hitbox; P2 soco 17→18 até pose e 43→39 até hitbox; guarda P2
  22→20. As variações são pequenas e não aprovam responsividade; guarda P1
  continua sem leitura conclusiva.
- Trace funcional DAP `lote_c_ko_trace_dap.json`, SHA-256
  `ed55b0dca38971bdd8ec11c29c9811f6383c6d9227c556fab1c56c2d1c5f2b25`:
  25 socos P1 aceitos, 10 causaram dano (50 cada) e 15 erraram. O primeiro
  round terminou por timeout com P2 em 500/1000; o placar passou a 1–0 e o
  round 2 iniciou (timer 98). Nenhum KO foi observado. As leituras DAP pausam
  e retomam a emulação, portanto este trace é funcional, não evidência de FPS.
  O código aplica recuo após acerto e mantém direções mascaradas; a separação
  é uma explicação compatível com os misses, mas posições não foram gravadas
  neste trace. O artefato fica em `out/` (gitignored).
- Vídeo de framebuffer `lote_c_best_of_three_verified.mp4`, 256×192,
  14960 quadros/249,66 s, SHA-256
  `81e428ce0b0b8e7fbaaac456e4b546c1bd61c7adfaedfe06740b5a94ac37233b`.
  Input script `a=400,s=125000,a=400,s=130000`. Os quadros mostram o timeout
  do primeiro round e, depois, `WIN 1` com placar 2–0 após dois timeouts.
  Áudio foi anexado, peak 13105. O veredito L091 v1 desse vídeo (`0/14960`,
  extra máximo 0) está **invalidado para claims visuais**: a máscara por
  luminância contou o palco azul/verde e o HUD como ator, e só casou
  `ken0_ryu0`. O `max_missing=48468` do relatório antigo é contaminado pelo
  fundo; não é contagem útil de omissão do lutador.
- Retificação L092, mesma ROM sem rebuild: captura fresca de framebuffer
  `lote_c_idle_rgb_mask_fresh.mp4`, 256×192, 781 quadros/13,033 s, SHA-256
  `c09a8e7857e8d1937062a206f11adf8db50e598f8a0eb833b9bac66c80726a06`.
  `lote_c_background_reference.png` (SHA-256
  `beeb5402b78fb533e9a5b2cf1a6049422047f59d347dadd1dda743f6b03d7db8`) foi
  calibrada por linha a partir das 24 referências legais; a cor modal teve
  pelo menos 74,479% dos pixels de cada linha. A análise usou diferença RGB
  máxima por canal >32 e ignorou a faixa de HUD `(0,0,256,24)`. O gate v2
  `lote_c_idle_rgb_mask_fresh_glitch_regions.json` (SHA-256
  `e80182aec8a15afe048e52f038541a0f09e95d9a870796f9ef24af265734cbcb`) passou
  0/781, extra máximo
  0, ausência instantânea máxima 901 px e 12 poses idle casadas. Duty relativo
  à pose legal, com tolerância de borda de 1 px: Ken 87,292% ponderado, P05
  67,135%, mínimo 65,262%; Ryu 78,048%, P05 48,262%, mínimo 47,000%. Nenhum
  lutador teve quadro de cobertura zero; Ryu ficou abaixo de 50% por até 3
  quadros, Ken por 0. A aprovação da janela 8 é mecânica; Ryu ainda mostra
  omissões perceptíveis e “flicker mínimo” não foi aprovado por julgamento
  visual humano. Esta captura é idle e não estende a evidência às ações.
- Captura isolada `lote_c_audio_punch_isolated.wav`: 11,1 s, peak 5887,
  100% de amostras ativas; `audit_audio.py` PASS durante o ensaio de entrada
  P1. `audit_audio_provenance`, `audit_psg_channel_binding` e piso PSG dos
  sete streams passaram. Isso prova sinal no runtime integrado; não prova
  qualidade subjetiva da música nem mixagem nota a nota. O stream `music_battle`
  escreve canais 0–3; SFX usa 2/3.
- A captura `lote_c_best_of_three_verified.mp4` também conserva os frames de
  vitória `lote_c_best_of_three_verified_f14.png` e
  `lote_c_best_of_three_verified_f15.png`. Todas as evidências e ROMs acima
  permanecem em `out/` (gitignored); este registro mantém os caminhos e hashes.
  O bundle original `lote_c_fresh_bundle_final.json` era fresco na sessão do
  Lote C e expirou a janela de 120 minutos; seu relatório L091 v1 não deve ser
  usado como prova visual. O bundle complementar atual de correção visual,
  `lote_c_visual_correction_bundle.json`, vincula a captura, o sidecar, a
  placa e calibração do fundo, quatro frames-chave e o veredito L091 v2 ao
  mesmo SHA da ROM; contém 9 artefatos pós-ROM, selados dentro de 120 min.
  SHA-256 do bundle `f6720b1c7324383863db5ba07e76162289ce10f2a0fa4bbad1e4055b6d776f98`.
  Ele não renova os eixos anteriores de áudio, gameplay ou worst-frame.

### Budget e limites do lote

O worst-frame anterior da mesma ROM mediu 3000 frames sem input, `vovf_delta=0`,
`vline_min=212`; era IDLE e o perfil por etapa foi inválido. No novo ensaio,
um B1 foi enviado durante a janela: na leitura DAP do frame 2850,
`tl_presses[0]=1`, `damage_events=1` e a vida de P2 era 950. A janela selada
terminou com `vovf_delta=0`, `vline_min=211`, 3000 frames medidos; o perfil por
etapa continua inválido sem derrame. Isso sustenta o pior quadro deste caminho
com um soco que conecta, não todas as ações ou combinações. PAL e todas as
demais poses/estados continuam fora da prova.

KO foi tentado, mas não alcançado; permanecem sem medição/aprovação chute,
caminhada/direções, salto, hitstop completo, resposta aceitável, cadência AIR,
PAL, HUD sob toda a gama de
dano, pior caso de todos os golpes/poses, restauração musical julgada por
audição humana, arte final do palco, época visual `delivery` e AAA. A máquina
fechou o ciclo best-of-three por timeout; isso não transforma a ROM em jogo
entregue nem apaga o atraso de input/AIR do Lote B.

| Eixo | Estado do Lote C |
|------|------------------|
| documentado | sim: GDD, spec, TDD e este memory bank atualizados |
| implementado | sim: palco técnico, HUD, PSG e round manager no runtime integrado |
| buildado | sim: ROM SHA acima |
| testado_em_emulador | sim: NTSC, dano P1, timeouts, best-of-three, áudio e L091 |
| validado_budget | parcial; RAM/layout e probes de frame medidos, escopo de ações incompleto |

## Lote B — um quadro NTSC e latência de input — 2026-09-29

O Lote A2 não foi reescrito. A ROM e os vídeos de lá continuam no disco:
base `c265b029a9df9defb24e24b8f2cdbce347d950b051a316c16cca3a59ff4ec79d`,
`idle_sat.mp4` `cb54322e78e13dd1e3fabf6f104ef7404cdc7dfc8da9f40e79e47afd5c6e3ae1`
(baseline e `out/evidence/`), `idle_sat_allocfix.mp4`
`62c84787040b4cbd64a851a123dba65c3cf437583ec0d0669aaef631d5844c15`.
O fim de DATA citado no A2 (`0xC6AE`) é o da ROM `1f14626e`. Nesta ROM
`_DATA` tem `0x6AB` bytes e termina em `0xC6AB`; `_INITIALIZED` (+6)
termina em `0xC6B1`. `_sa_limit` está em `0xC6AB`. Não ler `0xC6A8` nem
`0xC6A9`.

### Perfil da ROM que ainda perdia o VBlank

ROM `1f14626e6ba0b6d0a53466975864355c1813a2c0c24dc9cdadf96ad7169bf08f`,
28 pausas DAP, `sa_limit` vivo 112 no endereço antigo. O retorno de
`SMS_waitForVBlank` cai em VCounter 194 (`0xC2`). O orçamento até o
próximo `0xC0` é `(192-194)&255` = 254 tiques. As 28 iterações passaram
de 254. Duas populações, com SAT ~17, `fight_step` ~24+20 e emit ~60–66
em todo quadro. Upload longo ~139–194 mais varredura estável ~14 dava
totais ~283–326. Upload curto (reclaim bloqueia a cópia, 2–20) mais
track/reclaim ~29–30, varredura de troca de pose ~119 e emit ~60 dava
totais ~276–420. Exemplo 00: 17+171+5+24+19+3+1+13+1+60 = 314. Exemplo
01: 18+2+29+24+20+2+1+119+1+60 = 276. `tl_render_end_max` ficou 184.
`probe_vline_spill_max` ficou 0 porque `sample_worst_frame` lê o
VCounter logo depois do upload (~210–212). Pool 97–100, pico 100, falha
0: não era a causa. Um allocate por lutador, sozinho, não coube.
`sa_limit` 0x20 com a parada ainda atravessando a área ativa (ROM
`ea856217e81eff72ac8fdc50439dbd1123802fc2227143f032e83763d2a6a292`)
mediu 33,28/33,25. Parar em `0xE8` e adiar o corpo instável do segundo
lutador (ROM `61067811b8561263`, sobrescrita depois) mediu 44,83/44,45.

### Cortes que produziram o quadro único

Um `fight_step` por lutador por iteração. A duração AIR não é
decrementada duas vezes. PAL não foi medido.

1. O upload rápido para em VCounter `>= 0xE0` (`cp #0xE0` / `jp nc`).
   `STREAM_LIMIT_DEFAULT` continua `0x20` e só vale se o laço entrar
   já na área ativa. O comentário do fonte foi alinhado a `0xE0` depois
   do probe; não houve rebuild por causa do comentário.
2. `fight_draw` percorre os lutadores em `alloc_turn ^ pass`. No máximo
   um corpo instável por iteração (`heavy_used`). O outro, se `meta`
   já existe, mantém a pose na tela (só refresca x) e vira `alloc_turn`
   no quadro seguinte. O boot ainda monta os dois porque `meta == 0`.
   `stream_will_allocate` continua limitando um allocate real dentro
   do lutador que corre.
3. `compute_schedules` adia quando `sched_valid` e `rows_changed`
   (`sched_due = 1`). Essa iteração não emite, chama
   `stream_cancel_present()` e restaura `prepared_pose`. A seguinte
   vê `fight_skip_stream()`, pula `stream_step` e então calcula a
   escala e emite. O boot (`!sched_valid`) ainda calcula e emite na hora.
4. Depois do primeiro emit (`emitted_once`), um quadro que alocou
   (`n_alloc`) e não está apresentando pula o emit e restaura
   `prepared_pose`. Um quadro que apresenta a pose nova não pula.
   Pular o emit sem restaurar `prepared_pose` faria `visible_pose`
   mentir e o reclaim soltaria slots ainda na tela.

### ROM medida a ~59 Hz

`out/local_study/luta_integrada/out/rom/scale_pilot_80px.sms`,
655360 B, SHA-256
`b58e16e25f968d2900ddeadd09f61b8b69e6410dc512212cb92f17ec50269e47`.
Receita: `python3 tools/sms_wrapper/build_luta_integrada.py`.
Self-check de `measure_runtime_probe.py` antes da leitura. Comando:
`--project SMS_projects/luta_mugen/out/local_study/luta_integrada --rom <ROM acima> --seconds 8 --janelas 2 --out idle_60hz_sched_probe`.
Magic `SMRT`, schema 1, `probe_frame` em `0xC7F0`. Janelas 59,04 e
59,06 fps, spread 0,02, delta total 962. Boot, `frame_advance` e
`fps_constante` passaram. `audio_active_pct` null. Snapshot sem input
(`probe_keys` 0). JSON `out/evidence/idle_60hz_sched_probe.json`.
Reserva estática de pilha 3584 B; profundidade de chamada não medida.

Vídeo fresco de framebuffer, idle, sem input:
`out/evidence/idle_60hz.mp4`, SHA-256
`723a2ed23b0e62d756019784a821441d3f9ab594477046224a9630651b551a73`,
h264 256×192, 598 quadros, 9,98 s, `motion_fraction` 0,0583, mais novo
que a ROM. Áudio não anexado (peak 0, L048): não é prova de som.
`capture_video.py --seconds 9 --out idle_60hz --frames 4`, depois do
`--self-check`. Gate, depois do `--self-check` de
`audit_render_glitch.py`: `--mode flicker --window 8 --edge-tolerance 1 --video <mp4> --rom <ROM> --expected-dir out/legal_idle -o out/evidence/idle_60hz_glitch.json`.
**PASS**: 0/598, extra máximo 0, ausência máxima 898, 24 imagens
legais, pixels acesos antes do conteúdo 0. PASS de janela 8 não é
ausência de flicker. Omissão dentro da janela é legal.

Cadência AIR não foi atingida. Antes de qualquer tecla, `tl_dur_hist`
em `0xC7AC` leu `[0, 0, 0, 12, 0, 0, 0, 15]` no `probe_frame` 331:
cada pose visível concluída ficou no balde 3+ (segurada pelo menos 3
quadros além da duração AIR). Idle não é estátua. Não declarar 4,00
quadros por pose. A janela `0xE0` é o limite medido desta ROM; não
subir `sa_limit` nem reabrir o VBlank sem um perfil novo.

### Input, mesma ROM, sem rebuild

`emulator_input.py --self-check` passou (Wayland, kdotool+ydotool).
Foco uma vez; teclas seguintes com refocus desligado. Direções
continuam mascaradas em `read_pad`: só B1 = soco (`K_LP` 0x10) e
B2 = guarda (`K_GUARD` 0x40). Mapa neste Emulicious: P1 soco `a`
(evdev 30), P1 guarda `s` (31), P2 soco `g` (34), P2 guarda `h` (35).
`probe_keys = k[0] | (k[1] << 4)` perde os botões do P2. Prova do P2:
`tl_presses[1]` em `0xC7AB` e `probe_over` (estado do lutador 1) em
`0xC7F5`. `tl_lat_accept` é escrito 0 no quadro da borda; 0 com
`tl_presses` incrementado é aceite no mesmo quadro, não “sem medida”.
A guarda não escreve `tl_lat_hitbox`. O contador visível não é zerado
numa borda nova: valor igual ao anterior é ambíguo.

Segundos de tecla, uma ação a partir de idle, leitura depois de soltar
e de 0,4 s. Os quatro aceites incrementaram `tl_presses`. Conversão a
59,04 fps, não um segundo probe: 17 quadros ~0,29 s, 22 ~0,37 s,
30 ~0,51 s, 31 ~0,53 s, 43 ~0,73 s, 127 ~2,15 s.

- P1 soco (`a`): presses 0→1, aceite 0, visível 0→30, hitbox 0→127,
  pose 2→30, estado terminou 6, frames 401→599. Pose 0 do soco Ken é
  a absoluta 26 (`ken_frames_all+26` = `{2, 26, …}`, base 0). O
  snapshot final 30 é um quadro posterior do mesmo soco; o contador
  30 indica que a pose 26 já tinha aparecido.
- P1 guarda (`s`): presses 1→2, aceite 0, visível 30→31, hitbox ficou
  127 (não se aplica), pose 32→0, estado 0, frames 645→851. Pose 0 da
  guarda Ken é a absoluta 25. A escrita 31 é real. O snapshot final
  já era idle.
- P2 soco (`g`): presses 1→2 no jogador 1, aceite 0, visível 0→17,
  hitbox 0→43, pose 47→45, estado 0, frames 874→1075. `probe_keys`
  permaneceu 0. Pose 0 do soco Ryu é a absoluta 65 (base 44 + local
  21). O snapshot depois de soltar já era a pose 45.
- P2 guarda, primeira leitura depois de soltar: presses 2→3, visível
  ficou 17, pose 46→44, estado 0. Ambíguo, porque 17 era o soco
  anterior e a pose 44 é o idle local 0.

Remedida com a tecla `h` ainda baixa, boot limpo, mesma ROM. Idle no
frame 320: estado 0, pose 46, visível 0, máximo 0, presses 0. Doze
amostras em estado 5, presses 1, `probe_keys` 0x00. No frame 344
(24 quadros depois) a pose ainda era 47 e o visível 0. No frame 367 a
pose era 64, visível 22, máximo 22, e assim até o frame 600. Pose 0
da guarda Ryu é 64 (base 44 + `ryu_frames_all[20]` = `{1, 20, …}`,
anim índice 5). Ao soltar, no frame 621 o estado já era 0 e a pose
visível ainda era 64. Latência visível da guarda do P2: 22 quadros.
Hitbox de guarda não entra na métrica.

Não declara combate, dano, HUD, áudio, palco, round nem entrega.
Não há vídeo de framebuffer do soco ou da guarda; a prova é o
contador mais o id da pose lido na RAM com o emulador rodando.
A doutrina compartilhada do wrapper não foi reescrita.

## Lote A2 — glitch da SAT: offset do par, PASS L091 flicker — 2026-09-29

Causa, no `allocate_asm` de `integrada/src/stream.c`. O byte alto de
`off + id*64` fazia `adc` depois de dois `srl` do id. O `srl` descarta o
carry da soma do byte baixo e deixa o bit 1 do id. Todo par com
`id ≡ 2 ou 3 (mod 4)` era gravado 256 bytes adiante, salvo quando o byte
baixo da base da pose estourava pelo mesmo valor (Ken idle 1, 3 e 5, base
`…80`, saíam certos por coincidência). A SAT continuava com o `dx`/`dy` da
meta e o slot de `map[id]`; o upload copiava os bytes nomeados (VRAM == ROM
no offset gravado). O desenho mostrava o padrão de `id+4` na célula certa.
Âncoras no dump: P1 facing 0, x=96 em Q8.8, y=0; P2 facing 1, x=152, y=0;
piso 128. Não era âncora nem modelo do VDP.

Relação de quadro: `fight_draw` monta a SAT; `sat_upload` envia no VBlank
seguinte; `fight_sat_copied` troca SHOWN/NEXT. A pausa DAP foi em PC
`0x401b`/`0x4022`, antes de `stream_step` (`0x40d3`) e depois do upload, com
`visible_pose == prepared_pose`. O índice do vídeo não é `probe_frame`. A
SAT de visible Ken 4 / Ryu 2 (`probe_frame` 161) reconstrói os quadros
139–140 de `idle_sat.mp4` com extra 0 e ausência 0. Os quadros 523–524
(444 extras contra a legal `ken4_ryu2`) cabem com extra 0 na imagem bugada
de `ken4_ryu0`: o melhor encaixe legal tinha escolhido o Ryu errado. 196/196
offsets dos dois dumps seguem a fórmula bugada.

Correção: `push af` / `pop af` em volta do deslocamento, para o `adc` usar
o carry da soma baixa. Sem mudança de pool, âncora, máscara ou gate.

ROM nova `out/local_study/luta_integrada/out/rom/scale_pilot_80px.sms`,
655360 B, SHA-256
`1f14626e6ba0b6d0a53466975864355c1813a2c0c24dc9cdadf96ad7169bf08f`.
A ROM-base `c265b029a9df9defb24e24b8f2cdbce347d950b051a316c16cca3a59ff4ec79d`
e o vídeo `idle_sat.mp4`
(`cb54322e78e13dd1e3fabf6f104ef7404cdc7dfc8da9f40e79e47afd5c6e3ae1`) ficam em
`out/local_study/baseline_c265b029/` e também o mp4 original no estudo.
Receita: `python3 tools/sms_wrapper/build_luta_integrada.py`. Checkers de
RAM e banco passaram na ROM nova (DATA termina `0xC6AE`, `_tmpl` em
`0xD1F0`, `ld sp,#0xDFF0`, reserva 3584 B; banco 37 e bancos 2–23/25–36
coincidem). Profundidade de chamada não medida.

Vídeo fresco de framebuffer, idle, sem input:
`out/evidence/idle_sat_allocfix.mp4`, SHA-256
`62c84787040b4cbd64a851a123dba65c3cf437583ec0d0669aaef631d5844c15`,
256×192, 592 quadros, 9,88 s, mais novo que a ROM. Comando:
`capture_video.py --project SMS_projects/luta_mugen/out/local_study/luta_integrada --rom <ROM acima> --seconds 9 --out idle_sat_allocfix --frames 4`.
Gate, depois dos `--self-check` de `audit_render_glitch.py`,
`capture_video.py`, `check_ram_layout.py` e `check_rom_binding.py`:
`audit_render_glitch.py --mode flicker --window 8 --edge-tolerance 1 --expected-dir out/legal_idle -o out/evidence/idle_sat_allocfix_glitch.json`.
**PASS**: 0/592, extra máximo 0, ausência máxima 936 (omissão de flicker
num quadro; a janela 8 cobre a imagem legal casada), 24 imagens legais,
pixels acesos antes do conteúdo 0. Pares que venceram o casamento: ken
0/1/3/4 com ryu 0/1/2. Não declara que todo par idle apareceu como melhor
casamento.

Cadência desta ROM, medida depois do PASS visual. Self-check de
`measure_runtime_probe.py` passou; em seguida
`--seconds 8 --janelas 2 --out idle_sat_allocfix_probe` leu `probe_frame`
em `0xC7F0` (magic `SMRT`). Janelas 29,96 e 30,58 fps, spread 0,62,
`fps_constante` false. Boot e `frame_advance` passaram (delta total 489).
O laço ainda perde um VBlank: um `fight_step` por lutador e uma
apresentação por iteração. Input não foi injetado (snapshot `probe_keys`
= 0). Combate, HUD, áudio e entrega não foram medidos. A doutrina
compartilhada do wrapper não foi reescrita.

## Lote A — fontes preservadas, RAM/bancos medidos, SAT reprovada — 2026-09-29

Divergência de doutrina, aplicada e não editada no wrapper: o workflow
`mugen-engine-quality.md` ainda trata omissão visível como reprovação da
entrega e chama multiplexação de diagnóstico. A decisão humana vigente no
GDD e neste arquivo é a opção 3 (flicker mínimo, nenhum glitch). A doutrina
compartilhada não foi reescrita nesta sessão: curadoria do wrapper continua
exigindo autorização explícita e os gates dela. O trabalho abaixo segue a
opção 3.

Fontes próprias do estudo integrado, antes só em `out/local_study/luta_integrada/`
(gitignored), estão em `SMS_projects/luta_mugen/integrada/` (`src/`, headers
de mão, geradores, `.mddev/project.json`). Bancos, header de cena e ROM
continuam locais. Receita: `tools/sms_wrapper/build_luta_integrada.py`
(e `integrada/build.sh`). Não houve rebuild: a ROM medida é a já existente.

ROM `out/local_study/luta_integrada/out/rom/scale_pilot_80px.sms`, 655360 B,
SHA-256 `c265b029a9df9defb24e24b8f2cdbce347d950b051a316c16cca3a59ff4ec79d`.
Mapa `out/obj/scale_pilot_80px.map`. Self-check de `check_ram_layout.py` e
`check_rom_binding.py` passou antes da leitura.

RAM (layout estático, não “toda a RAM segura”):
- `_DATA` 0xC000+0x6A8 termina 0xC6A8; `_INITIALIZED` +6 termina 0xC6AE;
  `l__BSS` = 0. Soma DATA+INITIALIZED em 0xC6AE não é o veredito.
- Primeiro absoluto `_tl_snap` em 0xC790: 226 B entre o segmento e a telemetria.
- SAT própria: `_sat_y` 0xD000+72, `_sat_xt` 0xD048+144, `_tmpl` 0xD100+240
  termina 0xD1F0.
- `ld sp,#0xDFF0` nos primeiros 16 B da ROM. Reserva estática até o SP:
  3584 B (piso do checker 256 B). Profundidade de chamada não medida.
- Sem sobreposição entre segmentos e os `__at` do fonte. Símbolo obrigatório
  ausente agora falha; o checker antigo tratava essa ausência como comprimento 0.

Bancos: banco 37 da ROM igual a `pose_meta_37.bin`. Bancos citados por
`pose_table.h` (2–23 e 25–36) iguais à imagem concatenada. O banco 24 não
é citado por essa tabela e não entrou na prova.

Smoke da SAT própria, idle, sem input, NTSC, palco preto. Vídeo de
framebuffer `out/evidence/idle_sat.mp4` (256×192, 539 quadros, 8,99 s,
mais novo que a ROM). Imagens legais: 24 pares idle Ken×Ryu gerados dos
mesmos metas e bancos (`integrada/tools/render_legal_idle.py`); ken0×ryu
mede 78–80 px de altura opaca. `audit_render_glitch.py --self-check` passou;
`--mode flicker` na captura **reprova**: 547 falhas em 539 quadros, extra
máximo 444 px. 4 quadros têm extra 0 (subconjunto legal); a mediana fica
em 186 px. Na maioria dos quadros ruins os pixels extras não cabem em
nenhuma pose autoral colocada na mesma âncora — não é só omissão de
flicker. Há quadros em que um lutador coincide com a pose e o outro não.
PASS de janela 8 não foi obtido e não significaria ausência de flicker.
Nada promovido. Cadência continua a do registro anterior (~30 Hz). Input,
combate, HUD e áudio não foram exercitados nesta captura.

## Integração do motor 72–88 (em curso) — 2026-09-29

Clone `out/local_study/luta_integrada/` (FSM de `fight.c` + input por porta
A/B restrito a soco/guarda, pool compartilhado, SAT própria). Build pelo
script `tools/build_integrada.sh`, que regenera tabela/banco 37 e checa:
`check_ram_layout.py` (DATA não pode alcançar a RAM fixa de probe 0xC7A0) e
banco 37 da ROM == blob gerado. Ferramentas novas no clone, todas com
--self-check: `gen_pose_table.py` (metas podadas + tabela de linhas por
pose/lado no banco 37; P2 usa o blob `_P2_TILES`), `trim_scene_header.py`,
`check_ram_layout.py`.

Medido (ROM do clone, idle, sem input):
- Pool: pico 100 de 128, 0 falhas de alocação, 0 uploads descartados.
- Duração das poses com prefetch da pose seguinte: Ken 76 e Ryu 42 poses com
  desvio 0 em **iterações do loop** (sem prefetch eram +2 em quase todas).
- **Loop a 29,8–29,9 FPS** (2 quadros por iteração). Logo o AIR roda na
  metade da velocidade real: cadência 60 Hz NÃO atingida; latência de input
  ainda não medida por isso.
- Orçamento (linhas, mediana): SAT ~12; streaming até ~144 linhas após o
  início do VBlank (prefetch contínuo); rastreamento 5; `fight_step` 24+20;
  laço dos lutadores 19 estável / ~100 em troca de pose (alocação 60);
  agendamento 0 / 53 em troca; emissão 63.

Defeitos achados e corrigidos no caminho (todos por medição):
- DATA do SDCC sobrepunha a RAM fixa de probe (0xC8D0 > 0xC7A0): FPS e
  telemetria viravam lixo sem erro → checagem executável.
- `banks_integrada.bin` obsoleto (banco 37 de layout anterior): o pool lia
  metasprites erradas, estourava a lista de uploads e corrompia RAM →
  script de build + comparação ROM↔blob.
- Encadeamento herdado do T10 (pedir a pose só quando a anterior termina):
  +2 quadros por pose → prefetch da pose seguinte no pool.
- Custos de C do SDCC (~150–600 ciclos por iteração): liberação no VBlank,
  varredura do mapa, emissão, agendamento, alocação → movidos para
  assembly / pilha de slots livres / cache por mudança. `--opt-code-speed
  --max-allocs-per-node 50000` não ganhou nada (23,2 FPS igual).
- `SMS_addMetaSprite` relia a metasprite: substituída por SAT própria em RAM
  com o registrador 5 do VDP programado explicitamente (SAT em 0x3F00).

Pendente para 60 Hz: ~20 linhas no quadro estável e ~120 nos quadros de
troca de pose (emissão em registradores, alocação por lista de pares
pré-gerada, `fight_step`). Depois: input real, latência entrada→pose→hitbox,
gate L091 em vídeo com input. Nada promovido.

## Retomada do motor — dimensionamento da residência conjunta — 2026-09-29

Pedido humano: retomar `luta_mugen` a partir do streaming em assembly
(`flicker_asmstream`), preservando 72–88 px/proporções/pivôs/AIR e a opção 3;
dimensionar residência antes de integrar input e idle/guarda/soco nos dois.

Medido offline no corte 72–88 (`versus_scene_runtime_full_generated.h` +
bancos; `generated/residencia_idle_guarda_soco.json`), ações idle/guarda/soco
(Ken soco = 260, Ryu soco = 200 neste corte):
- pares únicos por pose: Ken idle 29–31, guarda 32, soco 28–38; Ryu idle 20,
  guarda 25, soco 23–27;
- **ping-pong com metades fixas (2× maior pose por lutador): 130 de 128 pares
  — não cabe**; poses de entrada de guarda/soco residentes: 245 de 128 —
  impossível;
- **pool compartilhado (pose atual + próxima, pior caso das transições
  permitidas, incluindo cancelamentos para as entradas): Ken 73 + Ryu 52 =
  125 de 128 pares** — cabe com 3 de folga;
- SAT: pior par de poses 83 peças sem poda; **com poda de peças 100%
  transparentes 63 de 64** (Ken soco 37 + Ryu soco 26).

Consequências de projeto: alocador dinâmico de pares por slot livre (não
metades fixas); poda obrigatória em todo o corte; agendador de flicker por
scanline em runtime (as tabelas pré-geradas só cobriam o par idle fixo);
qualquer ação/FX nova exige refazer esta conta. O header 72–88 exporta os
mesmos símbolos do corte 1:4 (anims, CNS, `PoseRef`), então a FSM de
`fight.c` pode ser reaproveitada. Nada integrado ainda.

## Streaming em assembly: cadência AIR exata no idle — 2026-09-29

Commit do lote anterior: `b94320a`. Depois dele, clones locais:

1. `scale_pilot_rom_flicker_fastsafe` (ROM `d464780d…`): cópia display-safe
   própria a 30 ciclos/byte (OUTI+NOP+JP NZ, endereço com DI/EI). Medida por
   VCounter no DAP (`diag_copytime`): **9–10 linhas por par de 64 B** contra ~22
   da `SMS_VRAMmemcpy`. Gate de glitch PASS em 3 vídeos (nenhum byte perdido).
   Cadência do Ken NÃO melhorou (5,67 frames/pose).
2. Diagnóstico (`diag_copytime`, contadores lidos por delta no DAP; histograma
   inicial descartado por RAM não zerada): poses do Ken duravam 5–7 frames;
   ~2 pares rápidos + ~5,7 seguros por frame; **5–8 linhas de C entre duas
   cópias** (indexação de struct, shifts de 16 bits, contadores uint16).
3. `scale_pilot_rom_flicker_asmstream` (ROM SHA-256
   `0d6b959ab6480322e25636c9c95f5f1cdaa6aa7f9f90de042b66037fa4f05701`): laço
   de streaming inteiro em assembly (interface por globais, modo por par pelo
   VCounter). Bundle `out/evidence/as_bundle.json` selou 6 artefatos. Probe
   59,75/59,75 FPS constantes; worst-frame 3.000 `vovf_delta=0`; streaming
   termina na linha 35 (antes, no limite ~116); **Ken 4,00 frames/pose (AIR 4),
   Ryu 7,26 (AIR 7–8)**; `audit_render_glitch --mode flicker` PASS 0/735,
   0/759, 0/741.

Modelo por ação com banda conservadora de 832 B/frame para o Ken (NÃO medido
em FSM): andar ×1,05, chute ×1,12, especial ×1,08, soco ×1,57 (poses de 1–2
ticks com 35–38 pares), agachar/guarda 3 frames onde o AIR pede 1; latência de
entrada ~3 frames em toda ação porque a 1ª pose sobe inteira. Próximo gate:
runtime com FSM e ping-pong dinâmico por lutador, medindo cadência por ação,
latência de entrada e gate de glitch em vídeo de cada ação. Nada promovido.

## Padrão do motor: opção 3 + curadoria L090/L091 — 2026-09-29

Decisão humana: opção 3 (flicker mínimo e sem glitch) é o padrão; GDD
atualizado. Curadoria autorizada e aplicada:
- **L090/§75** `scale_pilot.py`: plano de slots idle agora periódico (ponto fixo
  guloso ou ping-pong) com `_assert_idle_plan_periodic` (dois ciclos). Relatório
  real regenerado (`generated/.../scale_pilot_l090_audit.json`):
  `greedy_fixed_point` nos dois lutadores, mesmos bytes de upload. Pino do
  manifesto de doação atualizado com `deviation_log`.
- **L091/§76** `tools/sms_wrapper/audit_render_glitch.py` (strict/flicker,
  casamento por "sobrando" primeiro no modo flicker, início no conteúdo
  sustentado com `pre_content_lit_pixels` registrado). Lição
  `doc/curation/2026-09-29_l090_l091_idle_slot_period_render_glitch.json`;
  AGENTS.md atualizado. validate_measurement_tools 47/47, doc-sync e
  learning-capture PASS. mugen2sms: 94 passam, **6 falhas pré-existentes de
  paridade de doação** (runtime_format/scene_cut alterados fora desta sessão;
  character, ir/controllers, ir/expr, ir/opcodes: doador SGDKForge mudou após a
  cópia) — não re-pinadas sem conferência.

ROM base da opção 3: `out/local_study/scale_pilot_rom_flicker_min/`, SHA-256
`deadcfab71b7bdf8783ebdbf3d9474353f1a5fa0f5e04435a573b5079e5e6a72`; bundle
`out/evidence/final_bundle.json` selou 6 artefatos. Probe 59,52/59,59 FPS
constantes; worst-frame 3.000 `vovf_delta=0`; Ken 5,38 frames/pose (AIR 4),
Ryu 7,26 (AIR 7–8); `audit_render_glitch --mode flicker` PASS em 3 capturas
desde o boot (0/767, 0/756, 0/761). Corrigidos na ROM: 1ª SAT antes do
displayOn e display ligado em VBlank (antes: sprite perdido no canto nos
primeiros quadros, pego pelo gate). Aberto: flash de 7–9 px em y 135–136
antes do `main` (antes de qualquer código da ROM desenhar), registrado em cada
JSON; causa (crt0/power-on/emulador) não isolada. Escrita de VRAM em display
ativo continua como exceção com prova (slots não exibidos + gate), não regra.
Idle só, palco preto, NTSC; sem input/combate/HUD/áudio. Nada promovido.

## Critério visual atualizado — zero flicker na entrega — 2026-09-29

O pedido humano mais recente passa a exigir idle opaco 72–88 px,
proporções/pivôs/CLSN/AIR preservados, zero flicker visível/glitch e velocidade
de jogo estável. Isso supersede a decisão anterior de aceitar flicker controlado
como base de entrega. O clone `scale_pilot_rom_fast_render` segue como referência
de desempenho (~59,6 fps), mas é diagnóstico: tem flicker visível, Ken abaixo da
cadência AIR e um fragmento isolado no pé do Ryu sem causa fechada.

O corte local de 44 poses Ken/32 Ryu mede idle 81/80 px; bounds máximos
escalados são Ken 107×41 (KO) e 51×108 (special), Ryu 71×40 (KO) e 30×83
(special). No simulador, cada personagem isolado fica em até 7 sprites/linha,
mas o par idle chega a 11/linha (55 SAT): hoje não existe aceite de flicker
zero para dois lutadores nessa composição. Ver
`doc/18-gap-diagnostico-plano-prompt-2026-09-29.md` para evidência, plano e
prompt de continuação. Arte final permanece bloqueada até a solução caber sem
omissão visível.

## BG fighter andando a 1 px — bloqueio de throughput — 2026-09-29

Clone `out/local_study/scale_pilot_rom_bg_walk/`, ROM SHA-256 prefixo
`d9f0cf6272776e00` (704 KB); bundle `out/evidence/walk_bundle.json` selou 5
artefatos. `tools/gen_bg_walk.py` (--self-check; round trip pixel a pixel):
4 poses × 8 fases pré-deslocadas, região 6×11, até 45 tiles (1.440 B) por
atualização, bancos 38–41, name table com borda em branco que limpa a coluna
abandonada. Ryu anda 0↔16 px, 1 px por atualização, o mais rápido possível.

Medido: 59,74/59,72 FPS constantes; worst-frame 3.000 `vovf_delta=0`; gate
zero-flicker em modo dividido (Ken x<136, Ryu com deslocamento 0..16, identifica
deslocamento ±1 px) PASS 537/537, 0/0; deslocamentos 0–15 observados.
Custo: Ryu 1 atualização a cada 4,96 frames ≈ **12 px/s**; Ken caiu para
**5,98 frames/pose** (AIR 4) por dividir o streaming.

Veredito: lutador inteiro em BG com 1 px é limpo mas **BLOCKED para locomoção**
(caminhada de luta nesta escala ~60–120 px/s, 5–10× acima). Híbrido parcial
(só peças que estouram 8/linha): pior par exige 10 de 20 peças do Ryu no BG,
~640 B/px → ~26 px/s ESTIMADO, não medido; ainda 2–4× abaixo.
Com o limite inferior (sprite-only impossível) isto configura conflito de
hardware entre {72–88 px, dois lutadores lado a lado, zero flicker, locomoção
livre}. Pela regra do doc 18: parar antes de reduzir personagem ou aceitar
omissão; decisão de escopo é humana. Nada promovido; T10 intocada.

## Lote zero-flicker (doc 18) — idle do par 72–88 px — 2026-09-29

Clone `out/local_study/scale_pilot_rom_zero_flicker/`, ROM SHA-256 prefixo
`7d73a666ab1ddfa2`; bundle `out/evidence/pp_bundle.json` selou 5 artefatos
posteriores à ROM (probe, worst-frame, vídeo, JSON do vídeo, gate).

1. **Sprite-only refutado por limite inferior** (`tools/line_lower_bound.py`,
   --self-check PASS; `generated/zero_flicker_line_lower_bound.json`): cobertura
   mínima de pixels opacos por intervalos de 8 px. Ken 5–6/linha, Ryu 4; os 24
   pares idle dão pico 9–10 em 19–33 linhas. Nenhum re-layout/dedup/cull desce
   abaixo disso; sprites 8×16 reais só pioram.
2. **Defeito de plano de slots encontrado e corrigido** (`tools/pingpong_plan.py`,
   --self-check com fixture do defeito): o relatório de origem (scale_pilot) não
   é cíclico — a volta última→0 grava pares da pose 0 em slots diferentes
   (Ken 58/59, Ryu 102/103, entradas dos pés, dy=64) enquanto a ROM usa a META
   inicial, e o 0→1 seguinte sobrescreve esses slots. Glitch determinístico a
   partir da 2ª volta. **Explica o fragmento no pé do Ryu** (fast_render) e o
   "3→0 slots 102/103 vs 82/83" do isolamento P2 anterior. Correção: ping-pong
   (poses pares banco A, ímpares banco B), periodicidade verificada em 2 ciclos.
   O defeito vem do planejador em `tools/sms_wrapper/mugen2sms` (não alterado;
   candidato de curadoria).
3. **Híbrido BG/sprite**: Ken em sprites (metasprite inteira, ≤30 SAT, pico
   6/linha, sem scheduler); Ryu no BG (`tools/gen_bg_fighter.py`, --self-check,
   asserção pixel a pixel da composição), região 5×11 tiles, 41–44 tiles/pose,
   `TILE_USE_SPRITE_PALETTE`, dois conjuntos de tiles alternados, entradas de
   name table geradas prontas e copiadas no VBlank (montá-las em RAM custava
   ~48 linhas e derrubava o loop a 54 FPS).
4. **Gate** `tools/zero_flicker_gate.py` (--self-check: exato, omissão 8×16,
   resíduo 8×8, par alternativo, captura stale): cada quadro precisa ser
   explicado por um par (Ken i ∪ Ryu j) rasterizado dos padrões reais.
   Negativo real: vídeo do fast_render reprova 536/536 (até 4.038 px faltando).
   Híbrido antes do ping-pong: 87/537 reprovados (pés do Ken após a volta).

Medido na ROM final: probe 59,75/59,79 FPS constantes, boot/avanço PASS;
worst-frame 3.000 frames `vovf_delta=0`, `vline_min=202`; vídeo `pp.mp4.mp4`
538 frames, 204 quadros com mudança = trocas de pose previstas (sem mudança
por flicker); **gate zero-flicker PASS 536/536, 0 px faltando, 0 sobrando**.
Cadência: Ken 4,15 frames/pose (AIR 4), Ryu 7,26 (AIR 7–8), médias.

Limites deste resultado (não promover):
- escrita de VRAM em display ativo continua (pares do Ken e tiles do Ryu em
  slots/tiles não referenciados; ping-pong verifica que nenhum upload toca slot
  exibido). É exceção candidata com prova, não regra aprovada;
- gate tolera 1 px de borda (compressão h264): glitch de 1 px não é detectado;
- só idle, palco preto, NTSC, posições fixas, cadência média (não por transição);
- lutador em BG só se move em passos de 8 px sem pré-deslocamento (8 fases ×
  tiles de ROM) ou deslocamento em runtime — custo não medido; sobre cenário
  real exige composição com os tiles do palco — não medido; Ryu continua
  amostra bootleg NES.

## Runtime base B — cadência AIR recuperada — 2026-09-29

Registro da decisão anterior ao critério visual atualizado acima: B (escala
72–88 px, flicker controlado) segue como base de desempenho diagnóstico, não
como alvo visual de delivery. Clone
`out/local_study/scale_pilot_rom_fast_render/`, ROM SHA-256 prefixo
`34025741996b6b42` (build determinístico, rebuild reproduz o SHA). Bundle
`out/evidence/final_bundle.json` selou 4 artefatos posteriores à ROM.

Medido: probe 59,57/59,81 FPS constantes, boot/avanço PASS; worst-frame PASS
3000 frames, `vovf_delta=0`, `vline_min=204`; vídeo `l70.mp4.mp4` 538 frames,
8/8 informativos, taxa de loop pelo vídeo 59,2/s. Cadência medida por
contadores de troca de pose no probe (0xC7F2/0xC7F4): **Ken 5,37 frames/pose
(AIR 4), Ryu 7,25 (AIR 7–8)**.

Correção do registro anterior: o custo de B foi CALCULADO errado. Medido no
B original (`cull_cap21`): Ken 14,9 frames/pose e Ryu ~877 (3 trocas em 2.631
frames): Ken fazia upload primeiro e a guarda barrava quase todo par do Ryu.

Mudanças (cada uma medida):
1. Alternância par a par entre lutadores + guarda como único orçamento:
   Ken 19,4 / Ryu 12,8.
2. `UNSAFE_SMS_copySpritestoSAT` agora legítima (roda primeiro, no VBlank):
   Ken 15,2 / Ryu 9,7.
3. Streaming também em display ativo com `SMS_VRAMmemcpy` (slots de destino
   não exibidos até o prazo AIR), rápido só em 0xC0–0xE7, parada em
   `PILOT_STREAM_LIMIT`. Derrubou o loop para 30/s: o render custava ~122–160
   linhas (~650–900 ciclos/sprite: código SDCC via IX + `SMS_addSprite_f`).
4. Render via `SMS_addMetaSprite` (API pública): sublistas por lutador ×
   par de poses × variante geradas por `tools/gen_render_bank.py`
   (--self-check PASS) num banco próprio (37, ~11,2 KB, deduplicado); o boot
   valida cada sublista contra os caches de runtime e falha fechado. Render
   caiu para 38 linhas.
5. Limite 0x70 = teto medido; 0x80 reprova (46,8 FPS, ganho de Ken só
   5,4→5,1).

A worst-frame agora amostra logo após a SAT (único trabalho preso ao VBlank);
o streaming em display ativo é intencional e a prova de que o loop não perde
frame é o FPS constante + a taxa de loop pelo vídeo.

Diagnósticos inválidos descartados nesta sessão: "fast-only 30 FPS" e
"348 FPS" mediram ROM de build que FALHOU (erro interno SDCC
`SDCCgenconstprop` com ramo constante-morto); o `BUILD OK` ausente passou
despercebido. Candidato a lição de curadoria: gate que recusa medir se o
build da mesma invocação falhou.

Observação aberta: no vídeo, um fragmento isolado nos pés do Ryu num quadro.
Não se sabe se é tile legítimo em turno de flicker ou erro. Sem IoU, input,
combate, HUD ou áudio neste clone. Ken ainda ~26% abaixo do AIR; o flicker
continua visível nas linhas compartilhadas. Não promovido a entrega.

## Comparação A/B do padrão de escala 72–88 px — 2026-09-28

Decisão histórica de 2026-09-28, superada em 2026-09-29 para a entrega: manter
o piso 72–88 px com flicker controlado. Os dados abaixo são diagnóstico; B é
referência de desempenho, não aceite visual. O par idle fonte tinha 55 entradas
SAT e pico de 11 sprites/linha (10 após poda). Dois clones de `schedule_indices`
medidos:

- **A `scale_pilot_rom_cull`** (ROM `3dd24686…`): poda de peças 8×16 100%
  transparentes via `tools/cull_empty_pairs.py` (--self-check PASS). Ken 35→30
  peças/pose; cobertura média do escalonador 73,4%→80,4%. Upload inalterado
  (o par vazio já era um slot deduplicado). 34,91/34,91 FPS, não constante;
  worst-frame `derramou` 3000/3000, `vline_min=54`, streaming 102 linhas.
  Vídeo `cull.mp4.mp4`: Ryu com tiles de lixo (padrão de VRAM corrompida).
- **B `scale_pilot_rom_cull_cap21`** (ROM `7fc76fc1…`): A + SAT antes do
  streaming + teto 2 pares Ken/1 par Ryu por VBlank com pose retida até o
  sucessor estar residente + listas de desenho geradas com ids diretos dos
  caches por lutador (sem merge em runtime) + guarda VCounter 0xC0–0xE7 antes
  de cada par. **59,72/59,76 FPS constantes, boot/avanço PASS; worst-frame PASS
  3000 frames, `vovf_delta=0`, `vline_min=243`.** Vídeo `guard_e8.mp4.mp4`:
  pixels limpos; lacunas restantes são colunas multiplexadas pelo flicker.
  Degraus medidos no caminho: 2+2 → 51,3 FPS/429 derrames; 2+1 → 53,5/282;
  +ids diretos → 59,8/282 (spill_max 4 linhas); guarda 0xF0 → 7; 0xE8 → 0.
  O derrame acompanhava a taxa de troca de pose (merge em runtime).
- Custo de B (calculado, não medido em vídeo): Ken ≥15 frames/pose (AIR 4),
  Ryu ≥20 (AIR 7–8) — a animação idle fica 2,5–3,75× mais lenta que o AIR.
  Sem áudio, input, combate ou auditoria IoU nestes clones.

Recomendação: B como base de runtime; próximo gate é recuperar cadência AIR
(menos pares únicos por pose/reuso entre poses) sem perder o VBlank.

## Hipótese de escrita VRAM rápida em display ativo — 2026-09-28

Clone `out/local_study/scale_pilot_rom_safe_order/` (base: schedule_indices):
SAT copiada primeiro no VBlank; streaming com `UNSAFE_SMS_VRAMmemcpy64` só com
VCounter em 0xC0–0xF9, senão `SMS_VRAMmemcpy` (segura em display ativo).
Hipótese: OUTI a 16 ciclos no display ativo perderia bytes e causaria as
silhuetas fragmentadas (Ryu frames 1–3). Probe NTSC 31,17/31,28 FPS (pior que
34,71), boot/avanço PASS, `fps_constante=false`. Vídeo `safe_order_v2.mp4.mp4`
(573 frames/9,56 s, 8/8 informativos; 1ª tentativa falhou no ffmpeg sem log)
continua com lacunas de colunas/blocos iguais às do baseline, na inspeção visual.
Hipótese NÃO confirmada, e sem auditoria IoU nem worst-frame nesta ROM. A causa
provável das lacunas é a omissão do escalonador de flicker (pico 11/linha > 8), não
corrupção de upload. Registro à parte: o clone `batched` (sem registro anterior)
mediu 25,33/25,23 FPS e worst-frame `derramou` com `vovf_delta=3000`, `vline_min=80`
e streaming de 137 linhas; rejeitado.
Próximo ramo: reduzir sprites por linha na fonte (≤8, sem flicker) ou cortar o
volume de upload do Ken (1.920 B/pose a cada 4 ticks ≈ 480 B/frame).

## Atualização de throughput do piloto — 2026-09-26

O melhor clone diagnóstico deste lote é `out/local_study/scale_pilot_rom_schedule_indices/`:
lista de índices SAT pré-gerada por par de poses e variante, em vez de varrer
máscaras de flicker no loop. ROM SHA-256
`f332765572475314720632e1259bff7a515145ac664ba8826979d9c7e29909`; probe
NTSC 34,71/34,87 FPS, boot e avanço PASS, `fps_constante=false`. Vídeo fresco
`out/local_study/scale_pilot_rom_schedule_indices/out/evidence/schedule_indices.mp4`
(538 frames/8,98 s; 32/32 informativos; movimento 6,2%; sem áudio) mostra AIR,
mas ainda perde partes das silhuetas. Continua sendo estudo local ignorado pelo
Git, sem input, combate, HUD, FX ou áudio.
`out/local_study/scale_pilot_rom_schedule_indices/out/evidence/schedule_indices_fresh_bundle.json`
selou cinco artefatos posteriores à ROM com o mesmo SHA.

As variantes de delta planar (19,30/19,25 FPS), delta híbrido
(24,34/24,49 FPS) e reuso de slots residentes (25,20/25,45 FPS) não melhoram
o baseline de ~25,2 FPS. A melhor hipótese até aqui é reduzir composição de
SAT em runtime, não fazer patch por linha. A medição estendida do clone de
índices selou 3.000/3.000 frames: `vovf_delta=3000`, `vline_min=54`, retorno
máximo ao display na linha 140 após a espera, streaming 102 linhas e SAT 16.
Isso iguala o perfil VBlank do baseline: a lista de índices melhora o loop
para 34,71/34,87 FPS, mas não resolve o derrame nem atinge 50/60 FPS. O
snapshot parcial anterior (168/3.000 em 180 s) foi `sem_lastro` e foi
substituído pela janela selada.
O piloto 72–88 px não foi promovido e T10 permanece intocado.

Direção artística confirmada: Ken Masters ADV derivado de sprites CPS2 é o
modelo de proporção/acabamento. Ryu de sprites de bootleg NES permanece apenas
como amostra técnica de paletas P1/P2/runtime. A medição com Ryu mantém valor
de engenharia, mas não valida coerência do elenco; substituir por modelo
compatível com Ken/CPS2 antes da arte completa. Preservar escala opaca 72–88
px, proporções, pivôs, offsets AIR e CLSN nas próximas conversões.

Próximo gate: reduzir o custo de streaming/SAT dentro do VBlank, diminuir a
perda de silhueta e atingir 50/60 FPS antes de aceitar o corte. A lista
pré-gerada ainda não é suficiente: ela não mudou o perfil de deadline do VDP.

Experimento offline de fase da grade 8×16 (relatório
`out/local_study/generated/anchor_grid_metrics.json`): acrescentar padding
transparente à esquerda/acima para alinhar cada pose ao pivô preserva a posição
raster por compensação do eixo, mas não reduz patterns. Com fase zero, os pares
únicos idle (contando os dois facings emitidos pelo empacotador) subiram de
235→295 em Ken e 116→149 em Ryu. A fase dominante nos offsets AIR ([6,15] Ken,
[6,5] Ryu) ainda subiu para 289 e 129. O total das poses selecionadas também
cresceu: 1.998→2.262 pares Ken e 914→1.024 Ryu na fase dominante. Hipótese
rejeitada; `scene_cut.py` e o runtime não foram alterados. É análise offline,
sem captura no emulador, e não substitui a medição de upload/VBlank.

## Atualização do runtime do piloto — 2026-09-26

Este registro supersede as passagens abaixo que diziam que o plano idle ainda
não executava AIR em runtime. A ROM clone-only agora reproduz o ciclo AIR
completo de idle do Ken P1 e do Ryu P2, com cache de pose em RAM, remapeamento
de META, uploads exatos de padrões 8×16 distribuídos pelos ticks AIR e cópia
segura da SAT da SMSlib. A captura fresca `out/local_study/scale_pilot_rom_idle_cache/out/evidence/idle_cache_profiled_safe.mp4`
tem SHA-256 `decf8aa29ad0c1f670cb44fa97725d890922cdaea908e6053e6c07ff05c8e04c`,
479 frames/7,994 s em 256×192, 32/32 quadros informativos e movimento de 6,93%.
Ela comprova AIR visível neste clone, não qualidade final ou combate. Os
quadros também mostram partes das silhuetas omitidas pelo scheduler; o par idle
fonte chega a 55 entradas SAT e pico 11 por linha antes da multiplexação, então
flicker e legibilidade ainda reprovam a inspeção visual.

ROM observada: `out/local_study/scale_pilot_rom_idle_cache/out/rom/scale_pilot_80px.sms`,
655.360 B, SHA-256
`ef45985eae2a1735e1e5b4707de011fae5ace8f36f064072e441322eb5540581`. O probe
do loop avançou em 25,23 e 25,17 FPS NTSC (`fps_constante=false`); portanto o
runtime falha o piso de 50/60 FPS. O pior quadro selou 3.000/3.000 iterações e
registrou `vovf_delta=3000`, `vline_min=54`, `derramou`. O perfil mediu 102
linhas até terminar streaming, mais 16 linhas na cópia SAT e maior retorno ao
display na linha 140 após a espera; paleta/HUD não foram executados. Este é um
diagnóstico válido de sobrecarga, não um budget aprovado.

O bundle `out/local_study/scale_pilot_rom_idle_cache/out/evidence/idle_cache_final_bundle.json`
selou seis artefatos posteriores à ROM com o mesmo SHA, incluindo screenshot,
vídeo, runtime probe e worst-frame.

A variante que chamou `UNSAFE_SMS_copySpritestoSAT()` foi rejeitada: sua
captura falhou por imagem quase parada (0,59% de mudança). O clone voltou a
`SMS_copySpritestoSAT()` e a captura fresca acima passou. O achado anterior de
2,35 FPS/218 frames em 90 s ficou `sem_lastro`; o medidor de pior quadro agora
aceita `--wait-seconds 90..1800`, mantém janela selada de 3.000 frames e
registrou esta ROM com espera de 150 s. L089/§74 documenta a lição.

Direção visual mantida: Ken Masters ADV/CPS2 é o modelo de referência. Ryu de
bootleg NES segue apenas como piloto de paleta/runtime e deve ser substituído
por modelo coerente com Ken/CPS2 antes da arte completa; nada deste resultado
requer descartar o estudo técnico de paletas. O próximo gate é reduzir tráfego
de padrões e custo de SAT sem alterar altura opaca de 72–88 px, pivôs ou AIR,
depois repetir FPS, pior quadro e vídeo. Clone sem input, combate, HUD, FX,
áudio, PAL ou integração ao renderer canônico; T10 continua em
`legacy_probe_quarter`. `fighter_scale=measured`, não `accepted`.

## Estado atual — piloto de escala 72–88 px (2026-09-26)

Ken e Ryu foram escalados uniformemente por personagem a partir dos fontes
MUGEN originais, preservando proporções e transformação de eixos/offsets/CLSN.
Direção visual: Ken Masters ADV baseado em sprites CPS2 é o modelo de
referência. O Ryu usado aqui vem de sprites de um bootleg NES; seu papel é
somente estudo técnico de paletas P1/P2 e runtime. O Ryu não define estilo nem
entra como arte final; antes do roster completo, substituir por modelo coerente
com Ken/CPS2. Essa dívida visual não invalida o progresso de paleta/cache.
Ken: idle opaco 93→81 px, razão 80/93; Ryu: 62→80 px, razão 40/31. Os frames
renderizados de idle 0 medem 51×77 e 31×77 px, sem igualar artificialmente as
larguras. O corte registra 44/32 poses; manifests conferem contagem, ordem,
duração AIR, flips, eixos e quantidades de caixas CLSN. Isso prova preservação
nos dados emitidos, não reprodução temporal de todas as poses pelo runtime.

Fontes read-only, fora do Git, confirmadas por SHA-256:

- Ken (modelo CPS2 de referência): `/mnt/sdcard/Projects/Mugenesis/Base de Estudo/chars/street-fighter/ken_masters_adv.zip`, `822936f0de76a51db6174ffced7f1cbce6c54bb532fda4e68fd177bf6aaf25a3`.
- Ryu (sprites de bootleg NES; somente amostra técnica de paleta/runtime): `/mnt/sdcard/Projects/Mugenesis/Base de Estudo/chars/street-fighter/ryu_kang.zip`, `d3430ad559e2be75a3a99986920533018a522bed1363f2d51f3175ca59f0e55f`.

`scene_cut.py` agora emite META/METAL próprios para cada pool de paleta; o
medidor verifica metadados P1/P2 e `fight_draw` escolhe o par correspondente.
A ROM clone-only `out/local_study/scale_pilot_rom_p2/out/rom/scale_pilot_80px.sms`
tem 655.360 B, SHA `076f54dad965e8f9fd4e9a8332604df4e176934e4d5d3f43a7eb2a4f23c567a0`.
O vídeo fresco de Emulicious está em
`out/local_study/scale_pilot_rom_p2/out/evidence/scale_pilot_80px_p2.mp4`, SHA
`af5031bbbf4b98c0dd9272d6344907c7d4b9a0b731b4d051a069b576f969ba59`, 419
frames/6,99 s em 256×192, sem áudio. A auditoria compara a máscara do frame 0:
Ken 2.346/2.346 e Ryu P2 1.710/1.710 pixels (IoU 1,0). O frame Ryu usa
META/METAL P2. Isso prova somente frame-0, facing esquerdo e binding desse
frame; não prova AIR dinâmico ou flicker perceptual.

O primeiro link integral mediu 34.724 B no banco fixo e falhou. O gerador agora
alia somente arrays META/METAL byte a byte idênticos: 196 aliases retiraram
18.055 B sem alterar índices nem conteúdo de pose. O header com as 44/32 poses
linka com `_CODE` de 16.669 B e 15.550 B livres no banco 1. A ROM diagnóstica
integral tem 655.360 B, SHA
`7a7a2e3f6cb46250222f66ccbde630cf7114126a03270583d2de18511becd23e`; TMR SEGA
passou e os bancos de patterns 2–36 foram comparados byte a byte. O ROM e o
header bruto anterior à deduplicação permanecem em `out/local_study/`.

Captura Emulicious da ROM integral: 179 frames, 2,987 s, 256×192, sem áudio.
O `scale_pilot.py --video` passou a máscara/pivô do frame 0 (IoU 1,0); o
auditor continua `blocked` pelos budgets de SAT/scanline, VRAM/RAM e cadência.
Esse harness inclui as tabelas integrais mas desenha somente os idles frame 0;
não reproduz AIR. A metadata deste corte reside no segmento fixo já linkado;
crescimento de elenco ainda exige layout bancado e prova de ponteiros.

O build canônico atual de `luta_mugen` também passou no wrapper
(`build_inner.py`, 5 objetos, ROM de 131.072 B, SHA
`84da5a208e93cc7308dbe3604ba7e284cc793d2f7724b8e8b9ed71a0b00b08f7`). O
`build_record.json` marca build, relatório, boot e memory-bank atualizados; os
eixos gameplay, FPS e áudio continuam falsos. Esse binário usa o perfil legado
`legacy_probe_quarter` e os dados de `generated/versus_cut`; não é o runtime do
piloto 72–88 px. Não conectar o header novo diretamente ao renderer atual:
`fight.c` reserva 40 B de META por lutador, enquanto o corte novo chega a 148 B,
e `stream.c` limita cada ator a 64 B/VBlank, abaixo dos deltas medidos.

A auditoria global segue `blocked`: par idle = 55 SAT / pico 11 por linha;
pior par = 91 SAT / 23 por linha; buffers duplos completos 19.712 B frente a
8.192 B; metasprite máximo 148 B frente a 40 B atuais; 75 frames excedem o
AIR no cálculo de stream de 64 B/VBlank. Pool literal dos idle precisa 20.896 B
únicos. Current+next compacto de idle usa 6.464/8.192 B, mas ações selecionadas
pedem 8.256 B com facing fixo sem dedup; um único par idêntico transparente
reduziria esse número a 8.192 B sem folga, ainda sem implementação. Nenhum
reúso é creditado ao runtime. O contrato `fighter_scale=measured`, não
`accepted`; arte completa não liberada.

O analisador agora calcula novos pares exatos por transição AIR, além da
hipótese de 64 B/VBlank: Ken idle 0→1 requer 1.920 B em 4 ticks (480 B/VBlank);
Ryu P2 idle 0→1 requer 1.280 B em 7 ticks (183 B/VBlank). As duas poses
current+next ocupam 6.464 B e cabem por contagem nos 8.192 B, mas a implementação
atual de 64 B/ator/VBlank não alcança esses deltas. Isso é demanda calculada da
arte; se ambos prefetcharem juntos desde o início, a demanda média é 663 B por
VBlank. Throughput real continua a exigir probe de pior quadro na ROM.

O próximo passo analítico foi concretizado em `scale_pilot_dedup_emulator_audit.json`:
`selected_facing_pool.idle_cache_plan` atribui slots 0–63 ao Ken P1 e 64–127 ao
Ryu P2 e fornece META já remapeado, eixos assinados, AIR ticks e cargas exatas
por banco/offset para todos os frames idle. O máximo current+next é 3.904 B do
Ken e 2.560 B do Ryu (6.464 B juntos); a primeira transição exige 480 e 183
B/VBlank, respectivamente. O helper de plano preserva bytes de padrão, dx/dy,
terminador e eixo no self-check. É somente um plano de alocação da fonte; o
runtime ainda não o executa, a taxa de VDP não foi medida e o vídeo continua
mostrando apenas frame 0. `fighter_scale=measured`; arte completa não liberada.

Os fontes atuais removem o antigo bloqueio de recuperar META/METAL P2. O probe
P1→P2 continua mostrando que a metadata antiga não pode ser reconstruída por
parecença: 88/2.660 pares de Ken e 50/1.404 de Ryu são idênticos por bytes, sem
cobertura de pose completa. Isso justifica gerar índices a partir da pose/pool
P2 original, como foi feito, em vez de herdar P1.

Doador SGDKForge foi revisto somente em leitura; métodos incorporados e
limites MD→SMS estão em `16-engine-review-2026-09-26.md` e
`donor_review_2026-09-26.json`. O próximo gate antes de arte completa é
reproduzir AIR em ROM com pivôs e duração por frame, medindo upload/prefetch;
depois fechar scheduler scanline/SAT, VRAM, RAM e pior quadro conjunto. Se a
escala de elenco estourar o segmento fixo, metadata e tabelas devem ser
bancadas com referências válidas após cada troca. Relatório
`17-scale-pilot-2026-09-26.md`. Nenhuma prova deste clone atualiza os sete
eixos da ROM canônica T10.

## Revisão autoritativa — 2026-09-26, novo piso do motor

Pedido humano supersede 1:4/48 px como padrão de entrega. Norma canônica em
`../../../doc/05_technical/mugen_engine_standard.md`; matriz executável local
`engine_quality_contract.json`; diagnóstico/rota em `16-engine-review-2026-09-26.md`.
Perfil proposto: área útil 160 px, corpo idle 72–88 px. T10 continua
`legacy_probe_quarter`, com o mesmo SHA, sem nova ROM nesta revisão.

Doadores revisitados em `/mnt/sdcard/SGDKForge`: ferramenta mugen2sgdk_forge e
Mugenesis_Demo; leitura e hashes em `donor_review_2026-09-26.json`. Assimilados
métodos de fonte→IR→contrato, sweep de câmera, piloto FX e ownership/restauração;
VM/DMA/planes MD não foram portados. O doador também mantém gates de entrega abertos.

CLI principal SMS tinha imports MD ausentes (ImportError reproduzido no --help);
reparada. Novo auditor de contrato possui planning e delivery separados. O estado
T10 passou planning e reprovou delivery com 13 bloqueios: perfil legado e 12
capacidades sem aceite comprovado no novo contrato. Isso não invalida as provas
parciais históricas; elas não cobrem o novo perfil de entrega.

Fechamento observado desta revisão: 92 testes do conversor e 64/64 verificações
do wrapper passaram; os autochecks das 45 ferramentas de medição passaram.
Doc-sync e learning-capture passaram. Relatórios em
`../out/quality_review_2026-09-26/`. SHA da ROM reconferido:
`af9eb127895ed07de6884592bbac420e31c660b39d371d4c9f5faaacd629dc97`.
Esses checks validam ferramentas/contrato; não são nova evidência de emulador.

Após o bundle histórico T10, a ferramenta experimental de KO/reset falhou três
vezes por leitura word/byte, pausas DAP e aproximação sem alcance. Diagnósticos
`t10_round_lifecycle_subbyte_frame_fail.json`, `..._slow_poll_fail.json` e
`..._range_oscillation_fail.json` estão fora do bundle de 38 artefatos. KO/reset
continua NÃO PROVADO; não se atribui defeito de gameplay a essas tentativas.

Revisão de contrato/tools concluída. Após o piloto medido acima, o harness de
KO/reset ainda não foi corrigido/repetido; a nova ROM é apenas um clone
diagnóstico, não T10. As afirmações históricas abaixo são T10, não conformidade
ao novo piso. Nenhuma técnica foi promovida a maestria ou AAA.

## Estado histórico da ROM T10
2026-09-26 — T10 integrou Ken e Ryu na mesma ROM bancária de 131.072 B,
SHA `af9eb127895ed07de6884592bbac420e31c660b39d371d4c9f5faaacd629dc97`.
O runtime atribui cada slot ao seu próprio corte, animações, física, paleta e
bancos. P2 continua sendo dummy determinístico; a troca de personagem sem
alteração no C do núcleo ainda não foi provada para esta composição.

## Eixos de entrega (7) — gate final exige os 7 simultâneos
| Eixo | Status | Prova |
|------|--------|-------|
| build | testado_em_emulador | `build.sh` → ROM bancária de 131.072 B, SHA `af9eb127…dc97` |
| validation_report | testado_em_emulador parcial | bundle com 38 artefatos selado; assets/vínculo, estáticos, doc-sync, learning, reconcile e claims PASS; o gate visual segue em `probe` |
| boot no emulador | testado_em_emulador | `t10_ken_ryu_pair.png` + semântica PASS; `t10_deterministic_boot.log` confirma 2/2; época `probe` |
| gameplay | testado_em_emulador parcial | `t10_input_memory_range_sync_pass.json` prova input/dano PASS; whiff anterior preservado como diagnóstico; KO/reset e partida longa pendem |
| Cadência PAL/NTSC | testado_em_emulador | loop 58,6 fps constante; título 59–60; DAP 2×120 s PASS (58,10/59,78, spread 1,68); a tentativa DAP 2×240 s caiu antes da 2ª janela |
| áudio | testado_em_emulador (sinal) | `t10_current_audio.wav`: 15,6 s, ativo 100%, peak 5853; `audit_audio.py` PASS |
| memory bank atualizado | implementado | esta atualização registra a ROM e os resultados T10 |

## Fatia atual — T10 Ken vs Ryu dummy (2026-09-26)

- Ken usa 44 poses e Ryu 32; os cinco bancos 2–6 são gerados em
  `out/local_study/generated/versus_cut/` e o manifesto `.mddev` aponta para
  eles. O conteúdo MUGEN permanece fora do Git.
- `t10_ken_ryu_line_sim.json` analisa as 44×32 combinações de pose, as duas
  orientações de facing e as diferenças de altura alcançáveis no pulo. Pico
  conjunto: 8 sprites/scanline; simulador PASS, sem violação.
- `t10_input_memory_range_sync_pass.json` PASS na ROM atual: P1/P2 foram
  reamostrados após IDLE; posição na borda do B1 `P1=199, P2=215, gap=16`,
  B1 chegou, a vida de Ryu caiu 50 (152→102) e score foi 2→3. A tentativa de
  whiff anterior permanece em `t10_input_memory_idle_wait_retry_whiff.json`;
  a correção e o delta estão em `t10_causal_input_whiff.json`. O helper também
  passou `--self-check`. A falha de foco sem janela mapeada fica em
  `t10_input_memory_idle_wait_retry_fail.json`; a primeira falha histórica em
  `t10_input_memory_initial_fail.json`.
- `t10_current_worst_frame.json`: 3.000 frames, `vovf_delta=0`,
  `vline_min=200`, PASS; perfil por etapa inválido sem derrame.
- `t10_current_frame_advance.json`: 27 transições em 59,81 s, mediana
  58,6 fps, `constante=true`. `t10_current_fps.json`: 6/6 entre 59 e 60
  quadros/s,
  média 59,8. `t10_current_runtime_probe_120.json` PASS em duas janelas de
  120 s: 58,10/59,78 fps, spread 1,68; boot e avanço PASS. A tentativa de
  2×240 s caiu após a primeira janela (BrokenPipe, 54,22 fps) e não produziu
  JSON; `t10_causal_runtime_probe.json` registra a rota recuperada com 2×120 s.
- `t10_rom_asset_binding.json` PASS: cinco bancos, fontes, header gerado e
  captura vinculados ao SHA desta ROM. `t10_ken_ryu_pair_semantic.json` PASS.
- `t10_fresh_bundle.json` sela 38 artefatos da mesma ROM, incluindo o reteste
  range-synced e seu self-check; `t10_reconcile_claims.json`
  confirma lastro para os sete eixos binários do build record. Isso não promove
  a época visual nem substitui as provas de KO/reset e gameplay prolongado.
- `t10_visual_delivery.json` reprova `wrong_visual_epoch`: não existe contrato
  de entrega visual. A captura mostra lutadores pequenos sobre uma arena vazia;
  permanece `probe`, sem claim de entrega.
- O preset histórico T10 continua em 1:4; não é mais piso do GDD. O roteiro e storyboard do
  único palco ainda estão vazios; aguardo a direção da arena solicitada ao
  usuário e sigo nos gates técnicos independentes.

> Vocabulário: `documentado ≠ implementado ≠ buildado ≠ testado_em_emulador`.
> O motor (ferramentas) está em `implementado com testes Python` — 79/79 verdes
> (`tools/sms_wrapper/mugen2sms/tests/`, executado 2026-09-25). Isso NÃO é
> eixo de entrega do jogo.

## O que FOI OBSERVADO (Plano 1)
- S0–S4 commitados: `4166868` (S0), `6b181f2` (S1), `f773b05` (S2),
  `db70051` (S3), `2d3a326` (S4). Cópia doada sob contrato de paridade
  (`doc/doacao_md_mugen2sms.json`, 34 arquivos, pino por SHA).
- Ken `ken_masters_adv` parseia inteiro: 463 sprites / 161 animações / 934
  frames / 1.526 clsn / 91 comandos / 126 estados / 33 sons, 0 erros de parse
  (medido por `ken_full_parse.py` contra o acervo local, fora do Git).
- Fidelidade medida (S3): 2.273 direct / 317 approximate / 93 manual / 297
  unsupported. VRAM: 36.401 tiles únicos dedup = 1,16 MB vs 16 KB → streaming
  por pose obrigatório.
- **Gate do harness REPROVA o corte nativo**: pior pose × 2 lutadores =
  pico 32/scanline (teto 8), SAT 256 (teto 64)
  (`out/local_study/generated/s4_generation_report.json`, gitignored).
  Veredito `FAIL` registrado, não contornado.
- Resposta à reprovação é decisão HUMANA, tomada em 2026-09-25: escala
  travada TALL 8×16, lutador ≤4 sprites/linha × ≤3 colunas (≈32×48 px em
  tela), downscale 1:4 fixo no conversor, pose que estourar vira `manual`,
  flicker proibido. Está no GDD §"Escala do lutador" e no TDD §"Corte
  jogável". O conversor passou a aplicar esse contrato nas Tasks 1–2 do Plano
  2; a medição do corte Ken S4.5b registrou worst-scene PASS, pico 8/scanline e
  SAT 32. O texto de reprovação acima descreve o estado histórico pré-correção.

## O que FOI OBSERVADO (Plano 2 até Task 3)
- Leis de hardware MEDIDAS na cena 01 (não assumidas): par TALL
  `(pattern, pattern+1)` = (topo, base) — probe branco/preto mostrou branco em
  cima; origem de `SMS_addMetaSprite` = 1ª linha visível do topo da pose;
  espelho-h renderiza como OUTRO padrão (METAL no oponente); fixture com
  trailer de paleta PCX + `same=0` no subheader produz PAL visível (0x25).
- O harness `capture_evidence.py` reprova cena cujo conteúdo fica FORA da
  metade central da imagem (viewport box = canvas x64..191, y29..137) — a cena
  01 foi recentrada (chão na linha 16, lutadores x=96/152) em vez de maquiar o
  gate.
- `-set Update=0` do Emulicious só pinta depois do primeiro redraw (~2 s de
  Java): burst de capturas precisa aguardar a janela existir E o floor aparecer.
- Ken redondo S4.5b: 3.921 artefatos / 376.226 B (+199.396 B de espelhos — o
  custo real da ausência de flip), gate worst-scene PASS peak 8 / SAT 32.

## O que FOI OBSERVADO (Plano 2 Task 4 — FSM + física + clsn)
- `src/fight.c` interpreta tabelas compiladas do fixture `mini`: 7 animações
  (0/20/40/100/120/200/201), 8 estados, física Q8.8 inteira (vx 512 fwd /
  −384 back, JUMP_VY 2560, GRAV 128 ≈ 40 frames de ar), hitbox AABB em
  software com janela = frame de startup, hitstop 8 nos dois lutadores,
  pushback 16 (8 se bloqueado), knockback posicional, auto-facing no chão.
- **Formato CLSN mudou (desvio consciente, re-pinnado no contrato de doação
  `ccb56ad9…`)**: duas seções com sentinela `-32767` cada —
  `<hit i16×4…> -32767 <hurt i16×4…> -32767`. Motivo: o runtime precisa
  distinguir hitbox de hurtbox por frame; o formato antigo (lista única) não
  permite. Fixture sintético expandido: 9 imagens / 7 animações com sprite e
  clsn DISTINTOS por ação (anti-clonagem virou contrato de teste).
- Telemetria de frame na BG: `dbg_frame` (`__at` com volatile, L009) exportado
  em 3 dígitos hexadecimais por glifos de quadrante 2×2 (células 29/30/31);
  pixels procedurais de telemetria são a exceção declarada da diretriz
  estética. Célula de período 8 (dígito 2) é INSAMPLÁVEL neste host
  (Nyquist 1,2 < 3,0 — `t4_frame_advance.json` FAIL honesto); a medição
  canonica usa a célula de período 128 com janela de 60 s.
- Compromisso de paleta PAGÁVEL na Task 7: o SMS tem uma paleta de sprite; P1
  carrega o `_PAL` do frame atual e P2 em pose diferente herda a cor de P1.
- Blocker do gate de boot determinístico era um zumbi `capture_evidence --keep`
  (L057): o gate mediu a janela ERRADA e deu FAIL falso; morto o zumbi, PASS
  com 2 execuções de estado idêntico.

## O que FOI OBSERVADO (Plano 2 Task 5 — input vivo + mapa SMRT)
- `src/input.c`: ring buffer de amostras facing-relative (16, máscara
  power-of-2), matcher de passos no formato do CMD blob gerado
  (`[dir|keys<<4, flags]`, segurar/soltar), janela = idade máxima − mínima dos
  passos casados. `K_GUARD` NÃO é alcançável no pad de 2 botões — bit
  sintético de teste; o bloqueio vivo é o crouch (S_BLOCKABLE). Remap
  "recuar = guard" do GDD fica para a cena 02 (documentado em `inc/input.h`).
- Mapa SMRT da ROM (magic `SMRT`+schema 1 em 0xC7E0..E4; frame u16 0xC7F0;
  snapshot 0xC7F2..0xC7FD: hp/score/boss/over/state/wave(atracao)/keys/pose/
  px/py/p2x/pattern-latch) — `measure_runtime_probe.py` PASS e fps medido na
  RAM via DAP, sem depender de pixels nem de foco de janela.
- `tools/prove_input.py` (criterio próprio com `--self-check`, 11 fixtures):
  canario = reset Ctrl+BackSpace zerando `probe_frame`; leitura de `keys`
  DURANTE a tecla em baixo; tecla que não chegou ≠ whiff; veredito só na RAM.
  Na ROM final: 5/5 eixos PASS (números na tabela de eixos).
- **Bug caçado pela evidência — BG CRAM entry errada**: `SMS_setBGPaletteColor
  (entry, cor)` recebe entry ABSOLUTA 0..15 = `palette*4 + (indice&3)`; o
  código escrevia em `2` querendo dizer "palette 2". O chão (tile 126 → pal 2;
  bytes 0x00,0xFF por linha no formato 4-bytes-por-linha-do-gerador →
  p1|p3 = índice 10 → cor 2) lê a entry **10**, nunca inicializada — entre
  runs o chão saiu cinza, oliva, ROSA (254,170,255) e CIANO (170,255,255),
  cores FORA da paleta mestra que `screenshot_semantic_gate` reprovaria. Os
  glifos (tile 128+g → pal g&3, índice 1) só tinham branco na palette 0;
  agora entries 1/5/9/13 = 0x3F. Lição: cor que MUDA entre runs é entrada não
  inicializada, não capricho do emulador.
- Armadilha do `capture_video.py --press`: a rajada inteira roda no INÍCIO da
  gravação e o gate compara primeiro×último frame (piso 1%). Um script que
  volta ao ponto de partida (Right depois Left) reprova com 0.83% mesmo com a
  cena toda em movimento. Script que termina LONGE (`Up=250,Right=1800`) passa
  com 1.1%.
- Foco Wayland é compartilhado: logo após `prove_input.py` fechar, o F7 do
  `capture_video` não chegou à janela (FAIL honesto "gravação não começou");
  um retry com o palco limpo passou. Zumbi morto antes de CADA gate (L057).
- `mini_art.h` DEFINE os blobs (não extern) — só `fight.c` o inclui; demais
  TUs declaram `extern const unsigned char MINI_CMD_*[5]` (senão
  ASlink multiple-definition).

## Decisões registradas
- Motor = ferramentas em `tools/sms_wrapper/mugen2sms/`; runtime interpreta
  tabelas compiladas; CNS-em-runtime recusado (2026-09-25).
- Banking Sega mapper decidido (ROM ≈150 KB/lutador medido no round S4).
- P2/dummy = shift de faixa de índice no MESMO sprite palette (o SMS tem uma única
  paleta de sprite; custo de padrões duplicados medido no Plano 2, não "zero").
- Áudio: zero PCM portado; 6 SFX + 1 BGM reautorizados em PSGlib.
- Licença: arte real do Ken nunca entra no Git; derivativos só em
  `out/local_study/` (gitignored); fixtures sintéticos são os únicos dados
  MUGEN-like no repo.
- A decisão de escala de 2026-09-25 foi supersedida pelo briefing de 2026-09-26; ver revisão autoritativa acima.

## Blocker dominante atual
T10 põe Ken e Ryu simultaneamente na ROM; bundle fresco e reconciliação dos
eixos passaram. A prova de input/dano range-synced PASS; o whiff anterior
revelou a necessidade de reamostrar o alvo depois do IDLE, agora coberta pelo
helper local. KO/reset e partida longa não foram provados. A época visual é `probe`:
o contrato e storyboard do palco estão vazios. A direção visual está confirmada:
Ken Masters ADV/CPS2 define o alvo artístico; Ryu bootleg NES é amostra técnica
e precisa ser substituído antes da arte completa. Também falta provar que o
`.def` muda o personagem sem alterar C do núcleo nesta composição.

## Lições abertas
- L-aberta-1: `validate_measurement_tools.py` descobre ferramentas por prefixo
  `audit_`/`measure_` na raiz do wrapper; as ferramentas do mugen2sms não são
  alcançadas. Curadoria pendente (registrar no discovery ou criar wrapper) —
  só com aprovação humana explícita.
- L-aberta-2: downscale 1:4 em arte de 69×83 px mediana produz ~17×21 px —
  silhueta de lutador pode definhar. A prova é visual, no emulador (S5), não
  na planilha. Hipótese: recorte por boneco (remake de pose) pode substituir
  downscale bruto em poses-chave. Ferramenta que fecha: `audit_render_fidelity`
  + evidência capturada na cena 01.

## Handoff
T10 da ROM SHA `af9eb127…dc97` está selada em
`out/evidence/t10_fresh_bundle.json`, já com a prova de dano range-synced.
Próximo ramo: observar KO/reset e partida longa; então fechar a Task 8 — especial
de Ryu e prova do contrato `.def`. A época visual segue `probe` até existir
direção aprovada, storyboard, assets e vínculo com a ROM.
Antes de qualquer gate de janela:
matar zumbi (`pkill -f '[E]mulicious.jar'` em chamada separada — L057) e
`emulator_input.py --self-check`. Últimos checks focados: probe 24/24,
debug markers PASS, input self-check PASS; testes Python do conversor registrados
em 2026-09-25 (79/79), sem rerun nesta alteração de runtime.

## Última correção e evidência do piloto — 2026-09-26

Em `runtime_format.py`, a omissão opcional de células vazias comparava o bloco
8×16 (64 bytes) com o sentinela de bloco 8×8 (32 bytes), portanto não removia
nenhum par alto totalmente transparente. O sentinela agora representa os dois
blocos empilhados. O teste focado cobre remoção de células vazias e preservação
de conteúdo não vazio: `pytest tools/sms_wrapper/mugen2sms/tests/test_runtime_format.py
-q` passou 7/7.

No clone local ignorado `out/local_study/scale_pilot_rom_blank_fix/`, a
regeneração retirou 826 placements SAT transparentes nos 76 quadros e duas
orientações por quadro. Os 76 blobs de patterns, 76 eixos e 75 listas CLSN
permaneceram byte a byte iguais; as 152 listas META/METAL equivalem às antigas
após filtrar somente entradas cujo par 8×16 é zero. O SHA da imagem do mapper
continua `1bc791d24ce400f090446690d6e923c613d58fbda31f4e0beab03ee49c73a809`.
Pelo auditor, o par idle cai de 55 para 50 entradas SAT e de 11 para 10 sprites
na linha de pico; o pior par cai de 91 para 64 entradas SAT, mas ainda atinge
23 sprites por linha. O caso current+next de todas as ações/facings cai de
8.320 para 8.192 B: ocupa os 8 KiB inteiros, sem margem ou prova de runtime.
Os buffers duplos calculados continuam em 19.712 B e a maior META segue em
115 B contra os 40 B que o runtime reserva.

O clone foi buildado e executado no Emulicious. ROM SHA-256
`5dd11c383205960d42ae257e7c1f6859eb55461b9ccfeed746bbb961d1e3c6f9`; vídeo
fresco `blank_fix.mp4.mp4` registra 496 frames/8,28 s em 256×192. A captura
continua visualmente fragmentada. O probe leu 34,97/35,02 FPS NTSC (não
constante). O auditor foi corrigido para comparar a união temporal capturada
com as máscaras rasterizadas da união dos seis quadros idle esperados, em vez
de comparar todo o clipe AIR a uma única imagem frame-0. Novo envelope IoU:
Ken 0,944830, Ryu 0,768231; ambos ainda reprovam o limite 0,995. Os valores
anteriores 0,856517/0,760714 usavam o critério incompatível e ficam supersedidos.
`scale_pilot.py --self-check` cobre agora a rasterização de opacidade 4bpp e
passou; o relatório fresco está em `out/local_study/scale_pilot_rom_blank_fix/out/evidence/blank_fix_scale_pilot_video.json`.
Esse envelope pressupõe o fundo preto do clone; não serve para auditar
oclusão de lutador por cenário.
Áudio ausente, gameplay, hit/flicker aceitável e
budget de VBlank não foram provados. A tabela offline do idle seleciona 38–40
de 48–50 placements por variante; cada placement aparece em 5–8/8 variantes
(80,44% de ocupação média). A 34,97 FPS o ciclo de oito variantes fica em
4,37 Hz; isso não é aceite de flicker. A janela do worst-frame de 3.000 quadros
selou `derramou`: `vovf_delta=3000`, `vline_min=54`, `runner_wait_s=600`.
No snapshot terminal da janela, o perfil marcou 119 linhas para streaming e 16
para a cópia SAT. O código sobrescreve esses checkpoints a cada frame, então
são valores do último frame, não máximos por estágio. A variante de índices
anterior marcou 102+16 no seu snapshot terminal; os estados finais também
diferem. Não comparar esses breakdowns como regressão/ganho nem atribuir sua
diferença à omissão dos placements. O veredito de derrame, os 3.000 overflows,
`vline_min=54` e o retorno máximo à linha 140 (`spill_max=72`) são medidos na
janela completa e sustentam a reprovação. Evidência:
`out/local_study/scale_pilot_rom_blank_fix/out/evidence/blank_fix_worst_frame_long.json`, mesmo SHA da ROM.

Estado permanece `fighter_scale=measured`, não `accepted`; nenhum asset de arte
completa está liberado. Direção visual permanece Ken Masters ADV/CPS2; Ryu do
bootleg NES continua útil ao estudo de paleta/runtime e continua marcado para
substituição antes do roster e da produção artística completos.

### Isolamento P2 idle por frame — 2026-09-26

Novas capturas freeze-frame dos clones locais isolam os quatro frames idle do
Ryu P2. O frame 0 mantém máscara temporal exata (IoU 1,0; 59,9% dos quadros
quase completos). Frames 1/2/3 caem para IoU 0,556636/0,649762/0,541993 e
cobertura de 57,3%/72,6%/57,0%; nenhum quadro deles atinge 95% de cobertura e
precisão. Os pixels-fonte usados não mapeiam para cores pretas na paleta do
piloto. A tabela offline do escalonador cobre todos os placements nas 24
combinações Ken/Ryu ao longo de oito variantes. Simulação dos slots confirma
20/20 pares nas transições 0→1, 1→2 e 2→3, mas detecta a volta 3→0 enviando os
pares dos entries 18/19 aos slots 102/103, enquanto META0 os referencia em
82/83. A discrepância capturada nos frames congelados 1–3 continua sem causa
isolada; a simulação estática não prova a execução nem o prazo de VBlank.
Registro versionado com hashes em `doc/scale_pilot_freeze_p2_2026-09-26.json`;
ROMs e vídeos brutos permanecem nos clones locais sob `out/local_study/`.

Este é um diagnóstico do Ryu de bootleg NES, mantido exclusivamente como
amostra técnica de paleta/cache. Não bloqueia a continuidade do motor. Ken
Masters ADV ripado da CPS2 continua sendo a direção artística; a substituição
do Ryu permanece obrigatória antes da produção de arte completa. O estado de
escala continua `measured`, não aceito; não há promoção a arte final ou AAA.
