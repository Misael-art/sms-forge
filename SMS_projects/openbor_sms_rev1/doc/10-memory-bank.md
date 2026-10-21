# 10-memory-bank — openbor_sms_rev1

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
**2026-10-20 (pós-M8 — bundle consumidor, QA cap5 e projeção). O candidato
`701379cc88e0…` fechou o bundle consumidor selado com três sessões reais
(gameplay `2f25ce4a…`, MRP3 `43d33c39…`, áudio `42fb1b68…`): bundle
`2f69939a…`, consumo `e1af7fad…`, `eligible=true` e eixos
boot/gameplay/fps/áudio true. O MRP3 da sessão nova mede
59,39/59,44/59,57 fps NTSC (spread 0,18; 1.441 frames); o áudio tem peak
1986/8,173 s. QA nativa cap5: runtime `5aeb7960…` (2/2 PASS; boot frame 400
SMRT hp=100/boss=50; ataque hp=95/boss=43/state=3/p2state=2; probe_frame
330) e visual `37b1481d…` (2/2 de legibilidade/integridade PASS, 5 achados;
81 q, 32 distintos/31 transições; inimigo íntegro em dor/recuperação).
**Achado de apresentação NÃO resolvido**: no contato (índice 27) a lâmina
branca está em x42..64 e o inimigo em x86..132; o golpe não toca visualmente
o alvo e o dano só é legível pela barra (80→64 px) e pela dor em 38. Isso
bloqueia promoção de apresentação/época visual; não invalida os eixos
atribuídos. A projeção cap5 foi escrita: `evidence.json`
`a473d670…` e `fps.json` `1ccfa0af…` (fontes QA `5fe14599…`/`a7662a8b…`,
áudio `f16b48b8…`). O cap5 segue candidato, não delivery: Lote C (controle
i90 < i94; display i102 > i94) e a direção do golpe aguardam decisão do
dono; PAL, regressão, oráculo full-frame, archive/version e commit/push
continuam pendentes.**

**2026-10-19 (pós-M8 — silhueta + apresentação). Candidato `701379cc88e0…`
(131072 B, cap5): corrige o a102 que zerava cabeça/tronco do inimigo; gate
`audit_silhouette_integrity.py` 1000 casos PASS; terminal do ataque medido
(controle i90, display idle i102, 1º hit i27; dano i129 = ataque do inimigo,
não recuperação); Lote C reaberto só no critério de controle (90 < 94), display
não. O M8 `a7f02b84…` continua histórico 7/7; o cap5 NÃO herdou os eixos:
MWF/MRP3/FPS/áudio/bundle do SHA atual pendentes. Não é delivery.**

**2026-10-19 (pós-M8 — projeção e binding). A projeção canônica agora exige
o `rom_sha256` da ROM atual: `openbor2sms.axis_projection` (durável em
`tools/sms_wrapper/openbor2sms/openbor2sms/axis_projection.py`) recusa fontes
do M8 `a7f02b84` ao projetar o cap5 `701379cc` e não escreve nada;
`reconcile_claims.py` exige o mesmo SHA em `boot_emulador`, `gameplay` e
`fps_constante` (booleano sozinho não conta), com self-check de ROM antiga.
`doc/rom_asset_binding.json` registra 11 entradas source→res→símbolo→ROM do
cap5 (poses/rows/anim/blocks/PSG; símbolos de pose/anim/blocks no linker map;
áudio static) e passa `audit_rom_asset_binding --require`. O binding é
identidade, **não** render independente. O cap5 segue candidato; o M8 7/7 é
histórico do `a7f02b84`; regressão/MWF/MRP3/FPS/áudio/PAL/oráculo e
archive/version continuam pendentes.**

**2026-10-20 (pós-M8 — runtime do cap5). Sessão isolada `0009288b…` no
`701379cc`: MRP3 59,67/59,69/59,43 fps NTSC (spread 0,26; 1.438 frames;
boot/frame_advance true) PASS; MWF `vovf_delta=0`/`vline_min=207` (3.000
frames; snapshot final estado 6/dead) PASS. Sessão fresca `8e86e6aa…`: áudio
com ataque (mask 16) peak 1976/8,17 s; a primeira captura na sessão longa
(dead) deu peak 0 — silêncio no estado dead não é ausência de áudio.
`audit_audio --active-floor 5` (o mesmo piso do gate M8, mix SFX-only) passa
com 6% no cap5 (M8 a7f 12%); o default 90% (música) falha em ambos. É mix de
SFX, não música contínua. Medido, **não projetado**:
`evidence.json`/`fps.json` canônicos seguem `a7f02b84`; bundle consumidor/QA,
regressão, PAL, oráculo e delivery continuam pendentes. Pacote
`out/evidence/o3_cap5_runtime_20261020` (manifest `aa493b5a…`).**

**2026-10-19 — M8 fechado nos 7 eixos no SHA
`a7f02b847693c836045806eef6016624a826edaff2b94ed89a3b07c5e64a4953`
(131072 B): `./build.sh` deriva **7/7 true**, bundle consumido `eligible=true`
nos 4 eixos, QA runtime/visual 2+2 casos com gate `ok`, MWF `vovf_delta=0`/
`vline_min=207`, MRP3 59,61/59,62/59,69 NTSC e áudio SFX capturado. Relatório
M8 `doc/artifacts/o3_m8_report_20261019.json` sha `2fed8a5b…`; registry
`check --scan` ok (46 artefatos/185 arquivos, sha `f603b196…`). **Não é
delivery visual**: época `delivery`, vínculo asset→ROM e `audit_render_glitch`
continuam bloqueados; PAL não medido — detalhe na Atualização M8 ao fim.**
(Lote E v2 e Lote C seguem registrados nas seções de 2026-10-19 ao fim do
arquivo.)

**2026-10-18 — corretivo pós-M6 (Lotes A–C, parcial). Candidato de então:
ROM `957122ae24f64d362767d10e903dd71cdf47d18800066c57d562123a573ddfa7`
(131072 B), reproduzível byte a byte a partir do `src/main.c` WIP.** O M6
(`76cdbee3…`) permanece a prova histórica e nada nele foi sobrescrito;
`b0eed40a…` (M5) e `87954b7f…` (intermediária) seguem STALE.
- **Escalonador de uploader (D8)**: decisão na fase CPU (`sched_update` após os
  dois `stream_update`); VBlank só executa ordem/cap (decidir no VBlank perdeu
  o 2º sub-chunk: 128→64 B/q). Política: jogador primeiro, pré-carga promovida
  a `up_want` quando coincide com a pose corrente, dor do inimigo preempta,
  contenção `O3_UPLOAD_CONTEND_CAP 128u`. Matriz com 4 SHAs: b345 base (8
  hits, intervalos 72 q, dor 108/36 q) < cap64 (6 hits, dor 56 q) < cap96
  `ef1786c4…` (7 hits, intervalos 96 q) < candidato `957122ae…` (8 hits,
  intervalos 96/87×6, dor 11 q, HP final 0 em i648). Tetos 64 e 96 reprovados
  por medição, não por preferência.
- **Ataque (wall-clock real)**: `attack_tap` — ataque i1–i72 com retorno i73
  (base b345) vs i1–i93/i94 (candidato); 1º hit i30 em ambos; HP final do
  jogador 100 (b345) vs 95 (candidato). O dano em i131 foi isolado em
  2026-10-19: o inimigo entra em ataque (estado2) em i102, 8 q após o
  controle em i94, e o jogador está neutro — **não é recuperação maior**;
  ver Atualização pós-M8. A janela de vídeo de 60 q termina em ATTACK/frame4 —
  não é o terminal. O somatório
  nominal 3+3+3+3+9=21 não é duração: o avanço é limitado pelo upload de pose.
- **Ar/hit/queda**: TOSS preserva a altitude de contato (arc 1→2; contatos em
  alt 0/5/48/51/52/53/55; Δalt máx. 12/q; Δx máx. 4; sem snap para 0; pouso
  arc→0 e RISE em st5; alt 1 só na cauda do TOSS jump_60 i130). Contato direto
  em 46/47 não observado (mais próximo 48 — a tabela de queda pula 46/47);
  alt 200 inalcançável (máx. 101). Lacunas declaradas.
- **Índice de profundidade honesto (Lote A)**: whiff = sessão dz41
  `0b271ce0…` (HP inimigo 43→43, alinhado null); dano = dz6 `f41e8c8c…`
  (43→36, hit frame 19). O rótulo interno `whiff_dz: 6` do segundo é fase de
  ensaio, não classificação. Originais intactos.
- **Instrumentação de serviço**: `O3_SERVICE_TRACE=1` perturba o VBlank
  (128→64 B/q) — contadores só para contabilidade relativa de estágio; timing
  absoluto vem de builds de entrega (`O3_SERVICE_TRACE=0`). Bloco de 6 B em
  `0xC7CC..0xC7D1` (bytes_p, bytes_e, flags, pad, vc0, vc1); `0xC7D2` =
  `probe_vline_min`. Sondas declaradas fora de `#if` (SHA neutro: `957122ae`
  antes e depois) para o gate de corredor derivar do fonte.
- **Layout WIP medido**: ator de 48 B; `pl` @0xC000, `e` @0xC030, `cam` u16
  @0xC062, `written_col` @0xC064, `_DATA` 0x6F (`out/obj/main.sym`). Corredor
  `0xC7A6..0xC7FF`, 62 sondas, folga 1637 — `audit_probe_corridor` PASS.
- **Gates focados no candidato** (`gates_20261018.json`, SHA `44a591c5…`):
  marcadores PASS, corredor PASS, tilemap 16 arquivos/0 escritas ilegais,
  símbolos PASS, claims PASS, 144 testes host OK, 72/72 ferramentas de medição
  provadas, registro ok (40 artefatos/174 arquivos); `audit_doc_sync` sem
  derivas do projeto (global falha só por luta_mugen, EIO pré-existente).
- **Sucessão (Lote A)**: índice
  `doc/artifacts/post_m6_evidence_index_20261018.json`, linkage
  `post_m6_depth_linkage_20261018.json`, relatório
  `post_m6_lote_a_report_20261018.json`; predecessor do escopo preservado
  byte-idêntico em `doc/artifacts/o3_combat_scope_20261016_predecessor.json`
  (`aaf3b545…`).
- **M7 — áudio (2026-10-18)**: reautoria PSG dos 3 SFX O3/D11 a partir do PAK
  doador (SHA revalidado `64da17e8…`, 39500889 B) por `openbor2sms.sms_audio`:
  `inc/o3/psg_sfx.h` (canal 3, `SFX_CHANNEL3`),
  `res/audio/sfx_{attack,impact,fall}.psg` (13/14/15 B; 6/10/18 ticks),
  referências extraídas `data/source_openbor/gal_audio/data/sounds/{att1,hit1,fall}.wav`
  e `doc/audio_provenance_manifest.json`. Integração runtime (`src/main.c`):
  arrays em bancos 0–1 (map 0x30FF/0x310C/0x311B < 0x8000);
  `PSGSetSFXVolumeAttenuation(0)` no boot; `PSGSFXFrame()` 1×/quadro no início
  da fase CPU (sem ISR); arbitragem declarada fall(3)>impact(2)>attack(1) com
  owner/pending; gatilhos em `start_attack`, `apply_hit` e contato de queda
  (`was_toss`). `_DATA` 0x6F→0x71 (`sfx_owner/sfx_pending` no fim);
  `pl/e/cam/written_col` intactos. **ROM
  `a7f02b847693c836045806eef6016624a826edaff2b94ed89a3b07c5e64a4953` (131072 B).**
  - Gameplay **idêntico** ao pré-áudio `957122ae…` (`attack_hold` 650 q: 8
    quedas de HP nos mesmos índices 30/126/213/300/387/474/561/648, HP final 0,
    VDP final 1050; diferenças só em ponteiros relocados).
  - Gates: `audit_audio_provenance` PASS; `audit_psg_channel_binding` PASS;
    `audit_psg_redundancy` PASS; `audit_psg_quality` 0/6 reprovados.
  - Captura isolada (sessão `b7fcff2c…`, sink privado, `input` p1 segurado):
    `audio_attack.wav` 294912 amostras/6,687 s, peak=1963, ativo=13%, sha256
    `c933ec31fb8d0b20a28c2e7e3e64d6050169aa719c7976798d861d6438a24a06`;
    `audit_audio` PASS com piso declarado 5% — mix SFX-only (música fora do
    escopo O3); o piso padrão 90% é para mix com música.
  - Budget com áudio e combate real: MWF sessão `ae60dae3…` (input de ataque em
    tempo real, janela de 3000 q selada) `vovf_delta=0`, `vline_min=207`, estado
    no selo KO — `worst_frame_audio_attack.json` sha `41d83bd4…`; MRP sessão
    `7c3aa06b…` 59,67/59,69 fps (2 janelas de 8 s, combate dentro das janelas) —
    `runtime_probe_audio_attack.json` sha `2efa6930…`. Evidência em
    `out/evidence/post_m6/candidate_audio_a7f02b84/`. Registro: entry
    `o3-audio-m7` → `doc/artifacts/o3_audio_m7_report_20261018.json`
    (sha `d3b5ed3f…`); `check` ok (41 artefatos/175 arquivos, sha `ab90d5f0…`);
    gates agregados `gates_audio_20261018.json` sha `987502a5…`. Os testes host
    passam a usar stub do gatilho sonoro (`sfx_request`; prioridades lidas do
    header autoral) para continuarem compilando o FSM real — o som é provado na
    ROM, nunca no host.

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
| build | `buildado` | ROM `a7f02b84…` (131072 B) = `out/rom`; `./build.sh` rc 0; `out/build_record.json` deriva **7/7 true** (`build_record_m8.json` `d5703240…`) |
| validation_report | `testado_em_emulador` | MWF PASS (`vovf_delta=0`, `vline_min=207`) + MRP3 3 janelas NTSC 59,6135/59,6165/59,6938 (`frames_delta_total=1441`); bundle consumido `eligible=true`, problems `[]` (`ade6c1b7…`) |
| boot no emulador | `testado_em_emulador` (teto `assigned_checks_only`) | bundle boot framebuffer 256×192 + QA runtime `boot_baseline` (SMRT, hp 100/boss 50) e QA visual `boot_scene` (frame 400); reports `28cb7d39…`/`c43e9ed2…`; `audit_deterministic_boot` PASS (2 execuções idênticas) |
| gameplay | `testado_em_emulador` (recorte QA `assigned_checks_only`) | consumer `input_ram_video`: boss 50→29; QA `attack_contact`: boss 43/hp 95/state 3; vídeo de 81 quadros com dano no índice 30 (barra 80→64 px) |
| fps regional (NTSC/PAL) | `testado_em_emulador` (NTSC) | MRP3 sessão `4f1f4541…`: 59,6135/59,6165/59,6938; spread 0,080; **PAL declarado, não medido** |
| áudio | `testado_em_emulador` (escopo SFX) | WAV `1638dd19…` (589868 B, 294912 amostras, peak 1936, 6,687 s); `audit_audio --active-floor 5` PASS (ativo 12–13%); `audit_psg_*` PASS; sessão `a9d92820…` |
| memory bank atualizado | `documentado` | este arquivo (Atualização M8 2026-10-19) + `out/evidence/m8/` |

> Status válidos: `não iniciado`, `documentado`, `implementado`, `buildado`,
> `testado_em_emulador`, `validado_budget`. Toda linha diferente de
> "não iniciado" EXIGE prova citada (caminho de arquivo/captura), não prosa.
> **Os 7 eixos fecham no SHA `a7f02b84…`, mas o resultado NÃO é `delivery`:**
> a época visual `delivery` segue não paga — `audit_visual_delivery --delivery`
> reprova (`wrong_visual_epoch: contrato de entrega visual ausente`),
> `audit_rom_asset_binding --require` reprova (`rom_asset_binding_unproven:
> mapa ausente`), `audit_render_glitch` continua bloqueado (sem oráculo
> full-frame independente) e PAL não foi medido. QA de subagentes tem teto
> `assigned_checks_only`; não aprova qualidade visual, gameplay amplo, áudio
> além do SFX capturado nem FPS além das janelas medidas.

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
**Pós-M6 (2026-10-18)**: Lotes A (evidência/sucessão) e B (ar/pacing) fechados
no candidato `957122ae…`; Lote C **fechado no baseline medido por decisão do
dono (2026-10-19)**: escalonador na fase CPU + contenção 128 (matriz de 4 SHAs
de contenção), terminal de ataque medido no SHA final (i1–i93, retorno i94,
1º hit i30); reuso de tile/par + cache residente, deltas/preload/invalidate por
transição e cópia especializada ficam `dropped_by_owner` (não comparados;
nenhum claim de ganho/perda; reabre se exigirem retorno < i93/i94 ou
throughput > 128 B/q sem vovf).
Lote D (`audit_render_glitch`) segue bloqueado por falta de oráculo full-frame
independente validado; Lote E v2 **fechado em 2026-10-19** (bundle de sessões
nativas consumido `eligible=true` nos 4 eixos + negativos recusados; ver
Atualização 2026-10-19). M7 áudio **integrado e medido** (SFX canal 3, captura isolada,
MWF/MRP com áudio sob combate) — deixa de ser módulo morto; PAL não medido;
`vdp_regs.bin` ainda do SHA anterior; capturas visuais do SHA final e stress do
fechamento pendentes (uma vez, no SHA final).

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

**Atualização 2026-10-18 (corretivo)**: Lotes A/B fechados no pré-áudio
`957122ae…`; **M7 fechado no candidato de áudio `a7f02b84…`** (autoria PSG +
integração + captura isolada + MWF/MRP sob combate); gates focados e registro
reconciliados; memory bank atualizado.
Próximo: (1) bundle v2 do Lote E (consumidor + testes host prontos; falta o
construtor sobre a mídia nativa do SHA — nenhum existe ainda); (2) Lote C
candidatos 2–4 (reuso de tile/par + cache residente; deltas/preload/invalidate
por transição; cópia especializada) — sem alvo não atendido que os justifique
até aqui; escopo explícito pendente; (3) QA por subagentes; (4) M8 (7 eixos).
Nada commitado ou pushado sem autorização — `src/main.c`, docs e artefatos
seguem WIP sobre HEAD `da86de303bca969a393032d270c9d245d4055180`.

**Atualização 2026-10-18 (mídia de fechamento do SHA de áudio)**: capturas
visuais, stress e diagnóstico BlastEm feitos no `a7f02b84…`:
- still de impacto na sessão publicada `20a4616cd59e4ffc8096b0a49c90be23`
  (`o3_m7_impact.png` sha `f05485d9…`, luma var 1445 — `--check-image` PASS;
  bundle selado com `rom.sms` do SHA em `out/evidence/sessions/<sid>/`);
- vídeo 650 q do combate (mesma sessão), 86 framebuffers distintos, 256×192,
  59,92 Hz: `o3_m7_combat.mp4` sha `f15b8ed4…` + record `o3_m7_combat.json`
  sha `b59960a9…` — copiados em
  `out/evidence/post_m6/candidate_audio_a7f02b84/media/`;
- stress churn (RIGHT30 A2 idle20 LEFT30 B2 idle20 ×30 = 3120 q) em trial
  frame-paced: sessão `99e49239dcc14587be248a33ab560022`, 3121 linhas
  contíguas (VDP 400→3520), 8 hits, enemy final 0, player HP 100→75, cleanup
  closed (`trials/stress_churn/`; trace sha `d56d1ae1…`, resumo sha
  `99eb119e…`);
- `vdp_regs.bin` do SHA final via BlastEm: sessão
  `blastem-sms-81a8d07b9c4a463cab953a96e8834116` (state completed, NTSC, SMS2),
  snapshots 000/001/002 com reg2=0xFF, reg5=0xFF, reg6=0xFB; `measure_vram_map`
  com o plano O3 => **aprovado**, 0 blockers/0 alertas, janela de sprite 256
  tiles, PNT 0x3800–0x3F00, 15712 B usados/672 B livres
  (`out/evidence/blastem/regs_a7f02b84/vram_map_a7f02b84.json`, sha
  `97628642…`).

**Atualização 2026-10-19 (Lote E v2 — bundle de evidência do SHA de áudio)**:
o Lote E v2 está **materializado e consumido** no `a7f02b84…`:
- Construtor novo `openbor2sms/evidence_bundle.py` monta o bundle a partir das
  sessões privadas reais em `out/evidence/m8/session_inputs/` (gameplay
  `8743f6ab…` com boot PNG + observação de input + vídeo; MRP3 `4f1f4541…`
  com 3 janelas; áudio `a9d92820…`), derivando janelas de runtime dos journals
  e cruzando com `runtime_metrics_v1`; não inventa métrica. A sessão MRP2
  `54ee190c…` (2 janelas) foi superada pela MRP3.
- Consumidor (`evidence_consumer.py`): **`eligible=true`** nos 4 eixos
  (boot_emulador, gameplay, fps_constante, audio), escopo TOWN1/NTSC,
  `claim_ceiling=assigned_checks_only`; derivados reais: boss 50→29
  (`decrease`), janelas 59,613/59,617/59,694 fps, `frames_delta_total=1441`,
  áudio 294912 amostras/pico 1936/6,687 s. Relatório
  `out/evidence/m8/consumption_a7f02b84.json` (sha `ade6c1b7…`); `bundle.json`
  sha `a0cc1f37…`.
- **Limitação de ambiente medida**: `/mnt/sdcard` é fuseblk com modo sintético
  777 — `chmod` não gruda e a checagem de imutabilidade do consumidor
  (`st_mode & 0o222 == 0`) não é representável ali. O bundle canônico
  consumível vive em `/home/…/smsforge_bundles/bundle_a7f02b84/` (btrfs);
  cópia byte-idêntica espelhada em `out/evidence/m8/bundle_a7f02b84/`
  (`diff -r` limpo). Receita de re-materialização no relatório.
- Negativos sobre o bundle real: bitflip de 1 byte no PNG → recusa
  `SHA mismatch: artifacts/boot_png.png`; `fps_windows.json` com 2 janelas →
  recusa `at least three regional runtime windows required`; self-check do
  consumidor 39 testes OK. Log `out/evidence/m8/negative_probe_20261019.txt`
  (sha `6a26b7b7…`).
- Registro: entry `o3-lote-e` → `doc/artifacts/o3_lote_e_report_20261019.json`
  (sha `75109fd0…`); `check` ok (42 artefatos/176 arquivos, sha `6959c0ff…`).

**Atualização 2026-10-19 (Lote C — escopo fechado por decisão do dono)**:
- Baseline medido: escalonador na fase CPU + contenção 128 (jogador primeiro,
  preload promovida, dor preempta); matriz de contenção com 4 SHAs comparada
  sob a mesma cena/input (b345 base, cap64 `bdd4e832…`, cap96 `ef1786c4…`,
  cap128 `957122ae…` → selecionado).
- **Terminal de ataque medido no SHA final** (`d4e55202…`, trial frame-paced):
  ataque i1–i93, retorno ao controle i94, 1º hit i30, HP do jogador 95 (hit em
  i131); b345 histórico retorna em i73. O claim de ~60 q não é repetido.
  Pose 2 do ataque segura 29 q no cap128 vs 8 q no b345 — é o uploader, não a
  física (física intocada).
- Budget: MWF `ae60dae3…` `vovf_delta=0`/`vline_min=207` (não é folga livre);
  MRP3 `4f1f4541…` 59,61/59,62/59,69 fps NTSC (3 janelas, 1441 quadros).
- **Decisão**: candidatos de reuso de tile/par + cache residente,
  deltas/preload/invalidate por transição e cópia especializada
  `dropped_by_owner` — não implementados nem comparados; nenhum claim de
  ganho/perda. Reabertura: retorno < i93/i94 sob a mesma cena/carga/input,
  throughput > 128 B/q sem violar `vovf=0`, ou conteúdo que estoure o upload.
- Registro: entry `o3-lote-c-scope` →
  `doc/artifacts/o3_lote_c_scope_decision_20261019.json` (sha `72722c45…`);
  `check` ok (43 artefatos/177 arquivos, sha `954cd8f8…`).

**Atualização 2026-10-19 (M8 — fechamento dos 7 eixos no SHA de áudio)**:
- **Build**: `./build.sh` rc 0; ROM `a7f02b84…` (131072 B) reproduzida;
  `out/build_record.json` com **7/7 eixos true** (`build_record_m8.json` sha
  `d5703240…`; log `6e5fb60d…`). O build lê os caminhos canônicos
  `out/evidence/evidence.json`/`fps.json`/`*.wav`; o M8 materializou esses
  caminhos por **projeção automática** dos relatórios reais
  (consumer/MRP/QA), sem nova medição e sem booleano manual: `evidence.json`
  sha `21c7be62…`, `fps.json` sha `904f629d…`, WAV `1638dd19…`; gerador
  `888f0535…`; `reconcile_claims` PASS 7/7.
- **Consumidor**: bundle `a0cc1f37…` → `eligible=true`, problems `[]`, 4 eixos
  (boot/gameplay/fps/áudio), `assigned_checks_only`; relatório `ade6c1b7…`;
  derivados boss 50→29, 59,6135/59,6165/59,6938 fps, 1441 quadros, áudio
  294912 amostras/peak 1936/6,687 s. A projeção para o build preserva os
  valores arredondados do MRP3 (`59,61/59,62/59,69`, spread 0,08); os precisos
  vêm das janelas do consumidor.
- **QA independente**: runtime (subagente nativo `ses_ea99c6e7…`, sessão
  `aade3375…`) 2/2 casos, request `5e546ea2…`, report `28cb7d39…`; visual
  (subagente nativo `ses_ea99c6e6…`, sessão `28d7fe90…`) 2/2, request
  `3d09cc85…`, report `c43e9ed2…`; ambos
  `audit_subagent_session --require-passed --current-rom` ok, problems `[]`,
  elegível; teto `assigned_checks_only`.
- **Gates**: PASS `audit_debug_markers`, `audit_probe_corridor`
  (0xC7A6..0xC7FF, 62 sondas, folga 1585), `audit_tilemap_bounds` (17
  arquivos, 0 escritas ilegais), `audit_symbol_size_sync`, `audit_claims`,
  `audit_meaningful_change`, `audit_audio_provenance`,
  `audit_psg_channel_binding`, `audit_psg_redundancy`, `audit_psg_quality`
  (0/3), `audit_audio` (piso 5; ativo 12–13%), `audit_reference_boundary`,
  `audit_hardware_constants`, `audit_mastery_registry`,
  `audit_visual_delivery` (default), `audit_deterministic_boot` (2 execuções
  idênticas), `audit_causal_persistence` (`advance`), `reconcile_claims`,
  `validate_measurement_tools` 72/72. Manifesto de gates `81b2afe7…`.
- **Bloqueios declarados**: `audit_render_glitch` não executado (sem oráculo
  full-frame independente); `audit_visual_delivery --delivery` →
  `wrong_visual_epoch` (contrato ausente); `audit_rom_asset_binding --require`
  → mapa `doc/rom_asset_binding.json` ausente; PAL não medido; contato aéreo
  46/47 não observado (mais próximo 48); altura 200 inalcançável (máx. 101);
  `O3_SERVICE_TRACE=1` perturba 128→64 B/q (timing absoluto só trace=0);
  `audit_doc_sync` global FAIL por 10 derivas de luta_mugen (EIO/ENOENT; 0 no
  openbor).
- **Antes/depois**: ataque b345 i1–i72/retorno i73 vs a7f02b84 i1–i93/i94
  (1º hit i30 em ambos; HP 100 vs 95); MWF `vovf=0`/`vline_min=207`; MRP3
  59,61/59,62/59,69 NTSC; 128 B/q (2 sub-commits); ROM 131072 B; VRAM
  `measure_vram_map` 0 blockers (`vdp_regs` `818dd0f0…`); áudio 3 SFX
  (6/10/18 ticks, canal 3). Erro visual full-frame não medido; PAL não medido.
- **Registro**: entry `o3-m8` → `o3_m8_report_20261019.json` (sha
  `2fed8a5b…`) + `m8_causal_state_20261019.json`; PSG/fontes do M7 agora
  registrados nos grupos de destino `o3-audio-psg` (`runtime_resource`) e
  `o3-audio-source` (`openbor_source`); `check --scan` ok (46 artefatos/185
  arquivos, sha `f603b196…`). Sem commit/push (sem autorização).

**Atualização 2026-10-19 (pós-M8 — silhueta, apresentação e Lote C)**:
- **Defeito e correção**: o `a7f02b84` (cap8) exibia o `a102` com 29 células e
  7/8 nas linhas 1–2; a SAT compartilhada zerava cabeça/tronco do inimigo
  (`ec=[0,0,0,2,2,0]`; frames 29/30/45 do run aprovado). O cap5
  `701379cc…` limita a101..a105 a 5 células/linha 1–2 (lado externo primeiro),
  remove 14 células e devolve 3/3 ao inimigo; o cap4 `56a09458…` devolve 4/4
  mas apaga quase todo o arco da espada. A contagem-fonte e o gate de 8/linha
  permanecem pré-trim.
- **Gate**: `audit_silhouette_integrity.py` (novo; `--self-check` PASS) mede
  1000 casos estáticos: inimigo em pé ≥2 nas linhas 1–2 e ≥5 no total,
  jogador ≥3 nas linhas 1–3, ataque do jogador ≤5 nas linhas 1–2. Relatório
  `doc/artifacts/o3_silhouette_gate_20261019.json` sha `bd0afced…`; pior
  caso 3/2 total 5. Limite: é estático, não prova a SAT/framebuffer; a QA
  viva lê `ec`/SAT no SHA. O caso a103/pain02 do cap5 fica 3/2 (piso) e o
  ataque do inimigo contra idle/pain do jogador não está na matriz.
- **Apresentação**: vídeo de framebuffer 171 q (`attack_terminal_cap5.mp4`,
  sha `9a91d274…`), 256×192; input em i1; 1ª pose visível i14; contato i27;
  controle i90; display idle i102; dano i129. O dano é o ataque do inimigo
  (estado2 i103, a101 visível i113, a102 i127); o jogador está neutro e já
  tinha controle/idle — não é recuperação longa. O `a7f02b84` também tem o
  estado2 em i102 e dano i131, 8 q após o controle i94; a display antiga não
  foi medida.
- **Lote C**: critério 1 de controle atendido (i90 < i94; 4 q); display não
  (i102 > i94; 8 q depois); critério 2 (>128 B/q sem violar `vovf=0`) não
  demonstrado; critério 3 (conteúdo) não. A comparação cache/delta é
  analítica: ataque completo 113 células/7.232 B por lado; único 87/5.568 B
  esquerdo; ataque+idle/walk 140 > 128 de cache; melhor caso de cache 88
  células/1.600 B/12,5 q, não implementado; delta por slot refutado (20–22 de
  23–24 mudam); cópia especializada >128 não testada. Nenhum ganho de runtime
  é reivindicado; reabertura registrada em
  `o3_lote_c_scope_decision_20261019.json`.
- **Evidência**: `out/evidence/o3_silhouette_presentation_20261019/`
  (211 arquivos; manifest sha `a093aee8…`), com ROMs old/cap4/cap5, gate,
  composições/SAT, vídeo e arte-fonte; relatório consolidado
  `doc/artifacts/o3_silhouette_presentation_20261019.json`.
- **Projeção e binding**: a projeção canônica do M8 foi endurecida com SHA da
  ROM: `axis_projection.py` (novo, durável no pacote `openbor2sms`) recusa
  fontes cujo `rom_sha256` difere de `--current-rom` antes de escrever;
  `reconcile_claims.py` exige o mesmo SHA em boot/gameplay/fps. Teste real:
  fontes M8 `a7f02b84` + ROM cap5 `701379cc` → recusa; ROM M8 antiga +
  fontes M8 → projeta em diretório temporário (7/7 histórico preservado).
  `doc/rom_asset_binding.json` (sha `6c2caa9a…`, 11 entradas) liga
  a102/rows/anim/blocks/PSG por source→res→símbolo→ROM; os símbolos de
  pose/anim/blocks aparecem no linker map, os de áudio são `static` e não
  aparecem. `audit_rom_asset_binding --require` PASS. O mapa é identidade,
  **não** render independente.
- **Runtime cap5 (2026-10-20)**: pacote histórico de medição
  `out/evidence/o3_cap5_runtime_20261020` (manifest `aa493b5a…`): MRP3
  `59,67/59,69/59,43` fps NTSC (spread 0,26; 1.438 frames;
  boot/frame_advance), MWF `vovf=0`/`vline_min=207` (3.000 frames), áudio
  fresco peak 1976/8,17 s com ataque (mask 16). O MWF terminou em estado dead
  (snapshot 6); cobre VBlank/IA/uploads inimigos, não ataque scriptado do
  jogador. A primeira captura de áudio no estado dead deu silêncio; a fresca
  provou sinal. `audit_audio --active-floor 5` (mesmo piso do M8) passa (6%
  cap5; 12% a7f); o default 90% de música falha em ambos.
- **Bundle, QA e projeção cap5 (2026-10-20)**: bundle consumidor
  `out/evidence/o3_cap5_consumer_20261020/bundle.json` (`2f69939a…`) selado
  com gameplay `2f25ce4a…`, MRP3 `43d33c39…` e áudio `42fb1b68…`; consumo
  `out/evidence/o3_cap5_consumption_20261020.json` (`e1af7fad…`) com
  `eligible=true`, problemas vazios e eixos boot/gameplay/fps/áudio true. O
  MRP3 novo mede 59,39/59,44/59,57 fps NTSC (spread 0,18; 1.441 frames);
  áudio peak 1986/8,173 s; `audit_audio --active-floor 5` PASS (6%). QA
  runtime `out/evidence/o3_cap5_qa_20261020/runtime/run_1b8a3f28…/report.json`
  (`5fe14599…`, sessão `5aeb7960…`) 2/2 PASS; QA visual
  `.../visual/run_fbbd7a45…/report.json` (`a7662a8b…`, sessão `37b1481d…`)
  2/2 de legibilidade/integridade PASS, 5 achados e nenhum `findings: []`.
  Projeção canônica no cap5: `out/evidence/evidence.json` (`a473d670…`) e
  `out/evidence/fps.json` (`1ccfa0af…`); áudio `audio_701379cc.wav`
  (`f16b48b8…`). O ataque ainda aponta para a esquerda enquanto o inimigo
  está à direita (índice 27: lâmina x42..64, inimigo x86..132; dano só por
  HUD/dor); isso é bloqueio de apresentação, não dos eixos atribuídos.
- **Estado**: o cap5 é candidato pós-M8, **não delivery**; os 7 eixos do M8
  não se transferem. A projeção cap5 cobre boot/gameplay/fps/áudio; o build
  record será rederivado após esta atualização. Pendente: regressão de
  dano/whiff/profundidade/queda/morte/bordas/scroll/áudio concorrente,
  direção do golpe/Lote C por decisão do dono, oráculo full-frame, PAL,
  archive/version e commit/push. A árvore segue sem commit.

Nota herdada do O0: `data/source_art/concept_art/` materializado **vazio** é o
local designado do registry; sem contratos de arte em O0/O1, o
`audit_reference_boundary` passa a ser significativo quando houver contratos a
auditar (O2+).
