# 10-memory-bank — MSSF2T

> ESTADO OPERACIONAL REAL. Autoridade #1.

## Última atualização
2026-09-25 (2) — **ÁUDIO REGENERADO NO PISO L078/L079; ROM CANÔNICA AGORA É
`78794874877935e3269528f5756829f2d50ee45f09a21b261b3dfb9c8b9651ef`, 32768 B.**
O tema do Ken foi recomposto pelo próprio gerador do projeto
(`tools/gen_music_ken_stage.py`, o arranjo original de 4 canais que nunca
chegara ao binário — ver L079) com as correções do piso: acento alternado no
arpejo (M2 ch1), pizzicato no baixo (M2 ch2), percussão toda em ruído BRANCO
(0x00/0x03/0x02, L079) e decay no lead. Reprovado pelo orçamento: a versão de
8 compassos mediu 1040 B (+123 sobre os 917 jogados) e a árvore de trabalho
atual já não comportava o acréscimo — makesms morreu de novo em "Bank 1
overflow", agora 33 B além do fim. Corte medido, não apertado: caiu o 2º
compassinho, que repetia a tônica Am já exposta no 1º (7 compassos = 672
frames, múltiplo de 4/4, cadência G# preservada). Stream final: **919 B
(dur=672f=11,2 s), piso `audit_psg_quality`: viol=[], gaps 14,7/16,2/12,
2 atenuações/canal, uníssono 0%, ruído branco 100%**. `music_title.psg/h`
regenerados compliantes (577 B, viol=[]) mas continuam fora da compilação —
a tela de título não referencia o header; o arquivo em disco não é mais o
reprovado de 10 cláusulas. Manifest de áudio re-hasheado (3 streams),
binding→ROM re-hasheado (15 entradas, `audit_rom_asset_binding --require`
ok), bundle selado com 7 artefatos pós-ROM, `reconcile_claims` PASS.
Folga real medida: dados terminam em 0x7FA8 e o bloco de cabecalho comeca em
0x7FB2 — sobram ~10 B. Qualquer proximo acrescimo a esta ROM exige primeira
medição (redundancia removivel ou paginacao 64 KB declarada no TDD), nao
suposicao.
`capture_audio` 20 s: peak=6430, ativo=100% (era 89% — a dinâmica agora é
visível até na métrica de presença), runtime probe: boot/frame_advance/
fps_constante PASS. O resultado worst-frame (`vline_max=216`, delta=57 em
12 s; o anterior era 181/~2900) foi **invalidado por L082**: a ROM contava
`vline >= 0xC0`, que seleciona finais ainda no VBlank. Ele não prova PASS nem
derramamento. Medir novamente o SHA corrente com `measure_worst_frame.py` antes
de reivindicar orçamento.
**EIXO INPUT REPROVADO NESTA ÁRVORE (não pelo áudio):**
`prove_input_memory.py` rodou contra a nova ROM com canal de teclado vivo
(BackSpace provado, foco ok), luta em FIGHT, mas `Left` deslocou dx=+0 e o
soco por input não conectou (alcance nunca atingido por teclado); o soco na
atração passou (19 hits). A refatoração WIP não-commitada em `fight.c`
(`g_control_mode` HUMAN/CPU/REPLAY) mudou o caminho do input — a prova do
efd7162f (dx +96/−94) não se reconstitui sozinha. Entrega com eixo gameplay
exige re-provar input depois que o WIP assentar.

2026-09-25 — **PISO DE QUALIDADE DE ÁUDIO MEDIDO (L078/L079, gate
`audit_psg_quality.py`).** O eixo `audio` deste projeto sempre significou
PRESENÇA (peak/ativo); a qualidade musical nunca foi medida, e a medição
reprovou: `music_battle.psg`/`music_ken_stage.psg` (SHA `aaf1cf1b8e54…`, as
duas são byte-idênticas) erram 2 cláusulas cirúrgicas — baixo ch2 com
atenuação única e percussão 99% PERIÓDICA (o gerador chama "bumbo/caixa" a
modos ≥ 4, que o SN76489 toca como assobio tonal); `music_title.psg`
(`64acda75ca90…`, herança do gerador compartilhado) reprova em 10 cláusulas.
Achado doc↔dado: o bank declarava o tema do Ken em 4 papéis, mas o stream em
disco não tem UM evento de nota em ch1 — o arpejo nunca chegou ao binário.
SFX 4/4 passam (decay e duração corretos). Artefato:
`out/logs/psg_quality.json`; dívida para fechar o piso no ledger
`doc/psg_quality_ledger.json`. Até a regeração conforme, o claim de entrega
com áudio tem qualidade demonstrada NÃO.

2026-09-24 — **RE-CONCILIAÇÃO (curadoria passo 2): ROM CANÔNICA AGORA É
`efd7162f8c9f829b4826047d24ac2cfed5ab163e094520ee4ca1d00521892122`, 32768 B, e
toda a cadeia de evidência foi re-medida contra ela.** O bank anterior selava
eixos em `8a83ca2d…` (v086); desde então entraram L065–L068 (chip de guarda,
contrato de throw, QCF) e o probe M02 ficou no fonte **sem builds válidos**:
o conteúdo chegava a 0x8000 e o makesms morria em "Bank 1 overflow" (16 B
além do espaço reservado). Destravado por remoção de redundância medida, não
de função: `probe_missed` (0xC7EE) era incrementado sob condição idêntica à de
`probe_vovf` e nunca era consumido por `analyze()` — L051 aplicado ao próprio
probe ("contador redundante come ROM"); inits mortos de frame/vline/phase
fora (são reescritos todo frame; o tool trabalha com deltas). Folga atual:
fim do conteúdo em 0x7DF2 → **501 B livres** antes do espaço SDSC (0x7FE7).
Rebuild idempotente na mesma SHA.

Medições FRES CAS nesta ROM (todas com lastro de arquivo em `out/evidence/`):
- `runtime_probe.json`: boot + frame advance + fps da própria ROM — janelas
  55,69 / 55,53 (205→656→1108 frames). PASS.
- `fps.json`: título do Emulicious 59–60 fps, média 59,8, 6 amostras,
  `constante_50_60=true`.
- `evidence.png`/`evidence.json`: boot capturado (variância luma 6317/5123).
- `audio_m03.wav` + `audit_audio`: peak 5143, **ativo 100%** (trilha do Ken
  continua na ROM nova).
- `input_memory.json` v3, SHA `efd7162f…`: `input_provado=true` (dx +96/−94
  com `probe_keys` 0x08/0x04 lidos durante o hold); **soco −7 por input a
  gap=19**, `keys_b1=0x10`, pose 0x82, `hit_used=true`; sideswap
  `cruzou_no_ar=true` (min_py 58, facing 0x82→0x00); atração connecta 14
  hits sozinha.
- `worst_frame_m03.json`: **veredito honesto = DERRAMOU** com número real.
  O contador agora é a word não-saturante de `probe_vovf` (o defeito que o
  curador apontou — 255 indistinguível entre saturação e contagem — morreu
  junto com o byte antigo): delta **181 frames derramados** em ~2.900 na
  janela de 45 s de atração (≈ 6 %), `vline_max=235/262` (0xEB), fases 1–3
  observadas em FIGHT com derrame. O M02 (instrumento) está fechado como
  MEDIÇÃO; a dívida de orçamento continua em pé — o número fresco é 181/235,
  não mais o 247/251 com byte saturado.

Eixos derivados por `build_inner`+`reconcile_claims` nesta SHA: build,
validation_report, boot_emulador, gameplay, fps_constante, audio,
memory_bank_atualizado — **todos `true` com evidência desta ROM**.
Complementos do mesmo dia: `semantic_boot_current.json` — boot PASS no
`screenshot_semantic_gate` em escala nativa (157 cores, dominante 19,5%; o
gate precisou de conserto sensível à escala, L072); binding asset→ROM
re-hasheado para `efd7162f…` (15 entradas, `audit_rom_asset_binding --require`
PASS); bundle selado com **8 artefatos** pós-ROM
(`evidence_bundle.json`, 25/09, rom_sha256 `efd7162f…`). Em 25/09 (curadoria
passo 3) entrou vídeo nativo da receita de combate: `recipe_combate.mp4`
(256×192, 46,34 s, movimento 76,4%, 6/6 frames informativos; f02 = luta,
f05 = "KEN WINS" com Guile caído — laço golpe→dano→KO OBSERVADO nesta ROM, o
que antes era inferência de `8a83ca2d…`) + `recipe_combate.json` + frames
`recipe_combate_f00..f05.png`. O que NÃO
foi re-medido, e portanto vale como binário antigo: `video_ko.mp4`,
`ko_banner.png`, `laco*.png`, `poses.json` — selados
em `8a83ca2d…`.

2026-09-15 — **CICLO M01 PARCIAL NA ROM `5ac2dcc8…`.** O GDD/TDD agora
declara o contrato de engine reutilizável e o backlog/checkpoint estão em
`doc/engine_backlog.json` e `doc/engine_progress.json`. O núcleo passou a
decodificar P1/P2 com comparação em 16 bits (`key_down`), possui modos
explícitos HUMAN/CPU/DUMMY/REPLAY, limpa o `Fighter` por atribuição estática no
reset, resolve contatos após um snapshot compacto de identidades e corrige
empate/timeout e direção da IA após troca de lado. A regressão permanente é
`tools/sms_wrapper/mssf2t_regression.py`: a fixture que falhava no fonte
legado reprova truncamento P2 e testa trade/deduplicação; agora passa.

Build canônico passou com `--opt-code-size`, 32768 B, SHA-256
`5ac2dcc8576a5dcb17fe419c1d5a754fb15a419d4841a181947ab8f9b5747362`.
`out/evidence/evidence.png` foi observado no Emulicious;
`out/evidence/runtime_probe.json` provou boot, frame advance e 57,35 fps em
NTSC, enquanto `out/evidence/fps.json` teve 5 amostras 59–60 fps (média
59,6). `out/evidence/worst_frame_m01.json` reprovou honestamente o orçamento:
11 frames derramaram em uma janela curta; o instrumento ainda é o contador de
8 bits legado e não fecha M02. A tentativa de `prove_input_memory.py` ficou
sem sessão DAP/log útil; o JSON de 09/09 não foi promovido para esta SHA.

Próximo bloqueador: M02 — trocar `probe_vovf` por contador sem saturação
silenciosa, medir fases antes/depois de upload e missed VBlank, e criar prova
P2/trade/reset no Z80 antes de voltar ao renderer.

2026-09-08 — **GOLDEN SLICE RE-SELADO NA v086 COM O SOCO PROVADO E GUILE DE FRENTE.** Ciclo
completo: (1) trilha do palco do Ken substituída pelo **port do tema de
referência** (MIDI de fã em `art_src_base/audio/music/reference/`, sha256
`44804801…`, transcrita para PSG de 4 canais em 917 B — dentro do slot de
945 B); (2) **soco conecta por input NA v085**: `guile_hp 64→57` (o −7
exato) a gap=20, `keys_b1=0x10`, pose 0x82, `hit_used=1` — whiff-punish por
tempo de relógio (recuo 40 ms → entrada 40 ms → B1 na recovery da CPU); os
whiffs anteriores foram **datados nos probes como defesa da CPU** (recuo
guarda em `(g_frame & 8)` → ST_WALK_B, contra-ataque, chute no agachado) —
a teoria da "janela de 4 px" estava morta (L060); (3) **worst-frame medido
pela primeira vez**: 247/~2.700 frames derramam no VBlank (vline_max
251/262) com fps 60 — dívida medida, não adivinhada (L061); (4) **banner
K.O. capturado** (`ko_banner.png`, do `video_ko.mp4` com roteiro de pressão
contínua, L062); (5) falha total de canal DAP explicada: **diálogo modal
"Update Behaviour"** do Emulicios bloqueava o carregamento da ROM —
`Update=0` no ini (L063).
ROM `out/rom/MSSF2T.sms` 32768 B — SHA
`8a83ca2da18e2690d066…` (SHA completa em `out/build_record.json`)
(build v086; v085 + **folhas do Guile espelhadas para a convenção
face-left** — o Guile estava renderizando de costas para o Ken, L060/bloco
5; tamanhos de folha idênticos, só orientação). **484 B livres** (fim da `_CODE`
em 0x7E1C; teto real do makesms: 0x7F80). Bundle:
`out/evidence/evidence_bundle.json` **selado com 8 artefatos frescos**
(evidence, runtime_probe, audio.wav, input_memory.json v3, worst_frame.json,
video_ko.mp4, ko_banner.png).

## Eixos — medidos NESTA SHA (8a83ca2d…), selados em 2026-09-08
> **SUPERSEDIDO em 2026-09-24** pela re-conciliação `efd7162f…` (bloco no topo
> — 7 eixos canônicos re-medidos; KO/laço NÃO re-medidos, viraram inferência).

| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | 32768 B, 484 B livres, rebuild idempotente (mesma SHA) |
| validation_report | buildado | `out/build_record.json` (pre_gates pass) |
| boot_emulador | testado_em_emulador | `evidence.png`/`evidence.json` (luma 6241/4800) |
| fps_constante | testado_em_emulador | título: 60.0 constante (8 amostras); contador da ROM: frame_advance provado no `runtime_probe.json` |
| audio | testado_em_emulador | `audio.wav` peak=5056, **100% ativo** — trilha nova (port do tema do Ken) |
| abertura | testado_em_emulador | `evidence.png` (boot + título) |
| laço de arcade | testado_em_emulador | `video_ko.mp4` (round completo: FIGHT → K.O. → GUILE WINS → ROUND 2) + `ko_banner.png` |
| KO | testado_em_emulador (**direto**) | banner "K.O." capturado com Ken caído — já não é inferência de "KEN WINS" |
| **gameplay** | **testado_em_emulador** | `input_memory.json` v3: `input_provado=true`, dx +83/−87; **`soco_provado=true`** (−7 a gap=20, pose 0x82, hit_used=1); `sideswap_provado=true` (cruzou_no_ar); **soco na atração**: 21 hits da demo (10/12) |
| memory_bank_atualizado | documentado | este arquivo |

`reconcile_claims.py` e `seal_fresh_evidence_bundle.py` rodaram DEPOIS deste
arquivo? **Não** — ordem desta passada: capturas → selo → memory bank →
rebuild idempotente → reconcile (a SHA não muda; eixos re-derivados com a
evidência fresca e o memory bank atualizado por último).

### Nota sobre o eixo KO — FECHADO DIRETO
O banner "K.O." está em `ko_banner.png` (frame extraído do
`video_ko.mp4` a ~45,5 s, Ken caído, texto "K.O." central). O banner dura
120 frames e foi capturado com roteiro de pressão contínua + extração 1 fps
(L062) — não mais inferência indireta.

## O canal de teclado: causa raiz encontrada (L039 → resolvida)
Fatos medidos nesta sessão:
1. A sessão do host é **KDE Plasma sobre Wayland** (`XDG_SESSION_TYPE=wayland`,
   `kwin_wayland` ativo, Emulicious é cliente Xwayland). Nesse arranjo o
   `xdotool` fica cego (`getwindowfocus` vazio) e o XTEST não entrega evento
   — exatamente os sintomas da L039. **Não era maldade do Java nem da ROM.**
2. O canal real é **kdotool** (ativa a janela via script do KWin por DBus) +
   **ydotool** (injeção via `/dev/uinput`, nível kernel; daemon `ydotoold`
   com socket dedicado `/tmp/.ydotool_socket_smsforge`).
3. Canário de canal: o reset do próprio Emulicious (Ctrl+BackSpace) zera
   `probe_frame` (ex.: 469 → 40). Sem isso, nenhuma leitura tem lastro.
4. Mapeamento físico descoberto por leitura de `probe_state`: **Botão 1 =
   tecla A** (título → luta na primeira amostra: Z e X não, A sim).
   Direcionais são as setas; pulo = Cima.

## O eixo gameplay fechou — e a troca de lado foi observada
`tools/prove_input_memory.py` (v2, mesma ROM):
- Partida REAL: B1 no título (a atração morre no primeiro toque).
- Direita: `probe_keys=0x08` **durante** o hold, P[0].x 24→98 (dx=+74).
- Esquerda: `probe_keys=0x04`, P[0].x 98→8 (dx=−90).
- Critério intacto: dx ≥ 8 px NA DIREÇÃO COMANDADA nos dois sentidos, com
  canal vivo. `--self-check` com 12 fixtures, incluindo as regressões exatas
  L039 (canal morto) e L038 (blob andou para o lado oposto e o gate antigo
  dava PASS por abs(dx)).
- Bônus honesto no mesmo artefato: o soco não conectou (guile_hp 64→64),
  mas a **CPU acertou o Ken** no meio da amostragem (hp 64→57) — jogo vivo
  dos dois lados.

### O soco conecta por input (2026-09-07)
Mesmo instrumento, fase nova (`_punch_phase` + `evaluate_punch`, 19
fixtures no `--self-check`): aproxima até encostar (corpos param a
`PUSH_W`=20, dentro do alcance <24), B1 de 9 frames, polling do
`probe_boss` por 1,4 s, retry ×3 com recuo. Run selada
(`input_memory.json`, mesma SHA):
- tentativa 0: **whiff honesto** — B1 não chegou no 1º toque
  (`pose_no_b1`=0x81 WALK, hp 64→64); o retry é do instrumento.
- tentativa 1: `pose_punch_vista`=0x82 (POSE_PUNCH|facing) e
  **guile_hp 64→57 (delta 7 = hit cheio, sem guarda)** — CONECTOU.
- Critério: canal vivo + gap < 24 lido antes do golpe + queda de
  `guile_hp`. Hit (−7), chip de guarda (−2) e KO (0) são conexões;
  64→64 é whiff — fixture da regressão selada no self-check.
- Nota honesta: `probe_keys` no instante pausado mostrava 0x08 (Right
  do approach se cruzando com o keydown do A na mesma leitura); a
  agência do soco está na pose 0x82 + queda de hp, não nesse sample.
- Ken levou 64→54 da CPU durante as amostras (hp no Left) — jogo vivo
  dos dois lados.

### L053: de "correto por leitura" para OBSERVADO
Mesma fase do instrumento: aproximação até gap ≤ 30, passo atrás para sair
do hitstun, pulo com Cima+Direção. Artefato selado (`input_memory.json`):
`min_py=57`, `cruzou_no_ar=true`, aterrissou px=89 > p2x=67, `probe_pose`
0x81 → 0x01 — **o facing virou para o novo lado**, exatamente o que o
conserto (`apply_pose` dentro de `update_facing`) deveria fazer.
Limite honesto mantido: o espelhamento **visual** do sprite na tela segue
provado por leitura do código; o probe enxerga a lógica, não os pixels.
Detalhe de método: a 1ª tentativa da sessão falhou honestamente
(min_py=112) porque em contato com a CPU o lutador está busy e o Cima é
ignorado — o instrumento ganhou retry com recuo; a falha ficou no log.

## Poses: agachar e pular deixaram de mentir
`ST_JUMP` desenhava a folha de ANDAR e `ST_CROUCH` a de PARADO. Agora são 8
poses distintas (idle, walk, punch, special, hit, KO, crouch, jump).
`poses.json` re-medido nesta sessão: agachar/pular provados por memória;
JUMP com menor y=67. A arte nova não saiu de `art_src_base/` (ver seção
anterior no git — `author_pose_variants.py` remodela a silhueta a partir das
folhas próprias). Custo: 2560 B.

### Gravidade valia só dentro de ST_JUMP (L050)
`apply_gravity()` agora roda em qualquer estado; `airborne()` é altura, não
estado. Depois do conserto toda pose de chão tem y mínimo = 112.

### Empurrão no ar
`separate()` ignora quem está no ar — por isso o pulo por cima agora cruza.

## Recuperação de ROM: a música era 240 cópias do mesmo frame
`music_battle` tinha 2881 B — 240 repetições byte a byte do mesmo frame de
12 B (L051). Cortado para 49 B (`tools/shrink_music_loop.py`): 3264 B
recuperados com áudio medido igual. Gate: `audit_psg_redundancy.py`.

## fight_gfx.h dizia 1024 para folha de 832 (L052)
O tamanho vivia em dois lugares e divergiu: leitura de 192 B além do array.
Agora `tools/gen_fight_gfx.py` gera o header a partir das folhas (fonte
única) e há `audit_symbol_size_sync.py`.

## Tela de abertura e laço de arcade
Composição com o que já havia (paleta escurecida, índice 1 branco para o
texto). Laço: **abertura → (Botão 1) luta · (9 s parado) atração → rounds →
KO → resultado → (7 s) abertura**. `music_title` fora do orçamento; a
abertura reusa `music_battle`.

## O que mudou nesta sessão (noite)
- **Instrumento:** `prove_input_memory.py` v2 — backend Wayland (kdotool +
  ydotool) com fallback X11 legado; leitura de `probe_keys` COM a tecla em
  baixo; partida real a partir do título; fase de troca de lado com retry;
  `--self-check` de 12 fixtures. A prova de input NÃO usa pixels.
- **Limpeza:** as 14 folhas `inc/*_l_tiles.h` (defasadas, fora do build) e o
  diagnóstico descartável `tools/diag_input.py` removidos. Rebuild **não**
  saiu byte-idêntico (SDCC); SHA desta evidência = `2990757f…`.
- **Evidência:** toda a cadeia re-medida contra o binário do rebuild:
  `input_memory.json` (v2, com sideswap), `fps.json` (59.8),
  `runtime_probe.json` (57.69/56.51), `evidence.png` (boot/abertura),
  `laco.png`/`laco2.png` (atração viva e KEN WINS), `audio.wav` (92%),
  `poses.json`. A captura de áudio falhou 3× silenciosa e passou no
  retry — transitório de ambiente (L048/L019), sem mexer na ROM.
- **Bug pego pelo selo:** a 1ª versão do instrumento v2 gravava
  `input_provado=false` no JSON enquanto o stdout imprimia PASS —
  `evidence_bundle` reprovou a contradição claim↔artefato; corrigido
  (o veredito agora é gravado no campo) e a fixture da regressão entrou no
  `--self-check`.
- **Git:** projeto versionado (baseline `b63eef0` antes das mudanças).

## Decisões
- Flip: **runtime** (bitrev + dx-mirror). Reverte a decisão anterior; custo
  em `doc/15-tdd.md`.
- `STREAM_BYTES` = 96 B/frame, um lutador por vez. **Não mexer sem remedir o
  fps.**
- Palco autoral em VRAM 256+ (região só de BG). `reference_only` é régua,
  nunca fonte.
- Canvas 32×64 locked. `ready_for_aaa` false.
- Input de prova: **memória, nunca pixels** neste host (L035/L038/L054).
- Input de prova neste host: **kdotool + ydotool** (`emulator_input.py`).
  xdotool/XTEST não atravessa o KWin (L039).

## Blockers
1. ~~Input não chega ao emulador~~ **RESOLVIDO** — era Wayland/KWin (L039).
2. ROM apertada: **484 B livres** (v085; o compilador realocou e deu folga
   sobre os 211 B da tarde de 07/09). Arte/trilha novos exigem **banking** —
   spec pronta em `doc/spec-banking.md` (aguarda aprovação).
3. **Worst-frame derrama**: 247/~2.700 frames com trabalho dentro do VBlank
   (pior linha 251/262) no modo atração, fps 60 — dívida MEDIDA (L061).
   Degrau: reduzir stream de troca de pose ou DMA (fora do MVP).
4. Silhueta ainda é downsample+quantize da sheet — spec pronta em
   `doc/spec-arte-autoral.md` (depende do banking; aguarda aprovação).
5. ~~Soco não conecta~~ **RESOLVIDO E EXPLICADO (2026-09-08)** — hit −7
   provado NA v085 (whiff-punish por relógio); whiffs anteriores datados
   como defesa da CPU (recuo-guarda, contra-ataque, chute no agachado —
   L060, probes P[1].state/guard). Extensão natural, não blocker: sequência
   de socos até o K.O. com a CPU devolvendo.
6. **Animação por movimento (feedback do curador, 2026-09-08)**: cada golpe
   hoje é UM frame estático — soco ≈ idle e o chute REUTILIZA a pose de
   soco (`set_state`: ST_KICK → POSE_PUNCH, `fight.c`). Os movimentos não
   leem como golpe. Caminho: 2-4 frames por movimento por lutador
   (anticipação/ativo/recuperação + ciclo de caminhada), derivados do
   sprite sheet de referência pelo pipeline `translate_ssf2t.py`
   (`prepare_sms_pixel_art.py` na fábrica), com a FSM avançando frame por
   timer. Custo: ROM (banking obrigatório) + frames novos — entra JUNTO com
   os blockers 2 e 4, depois da aprovação das specs.
7. ~~Guile sempre virado para a direita~~ **RESOLVIDO (2026-09-08, v086)** —
   as 8 folhas do Guile estavam autorizadas face-RIGHT contrariando a
   convenção do motor ("folhas olham para a esquerda"; `want_flip` =
   facing?1:0). Espelhadas em `res/fighters/`, headers regenerados
   (`emit_tiles_h` + `author_pose_variants.py` + `gen_fight_gfx.py`),
   binding re-hasheado. As variantes `_l` do tradutor continuam fora do
   build (flip é runtime).

## Quais evidências valem para esta SHA
**Atuais (2026-09-08, binário `8a83ca2d…`, seladas juntas — 8 artefatos):**
`evidence.png`/`evidence.json` (boot), `runtime_probe.json` (fps da ROM +
probe SMRT), `audio.wav` (trilha nova, 100% ativo), `input_memory.json`
(v3: input + soco −7 + sideswap + soco na atração), `worst_frame.json`
(derramou: 247), `video_ko.mp4` (laço completo com K.O.), `ko_banner.png`
(banner), `evidence_bundle.json` (**selado**).

**De binários anteriores (NÃO usar como prova):** `laco.png`, `laco2.png`,
`poses.json`, `fps.json` de 07/09 (esta foi re-medida), `gameplay*`,
`ko11*`, `special*`, `title*`, `rounds*`, `resultado*`, `volta_ao_titulo*`,
`band_*`, `blink_*`, `tl_*`, `pv_*`, `pose_*`, `audio_ken_stage.wav`,
`ken_stage_preview.wav`, `audio_ref.wav`, `boot.png`, `video_gameplay*`,
`runtime_probe_diag*` e tudo produzido contra `2990757f…`, `1800c79c…` ou
`e42c4887…`.

## Handoff
Golden slice **re-selado na v086 com soco, K.O., worst-frame e Guile de frente fechados**.
Próximos degraus, em ordem causal:
1. **Aprovação humana das duas specs**: `doc/spec-banking.md` (Sega mapper
   48K, dados em BANK1+, toca no `build_inner.py` — curadoria) e
   `doc/spec-arte-autoral.md` (silhueta nativa, depende do banking).
2. **Dívida do worst-frame** (L061): reduzir o stream de troca de pose
   (ou DMA fora do MVP). Número atual: 247 frames derramados com fps 60.
3. **Extensões de gameplay** (não blockers): sequência de socos até K.O.
   com a CPU devolvendo; especial por input (QCF) com prova por RAM;
   2P humano (PORT_B) para prova de soco sem IA.
4. Manutenção: `Update=0` no `Emulicious.ini` é o que evita o diálogo modal
   que bloqueia o carregamento da ROM (L063) — não remover.

Curadoria do ciclo: L058/L059 (proveniência de áudio, §47),
L060–L064 (§48–§51) em `doc/curation/2026-09-08_l060_l064_ciclo_mssf2t.json`;
gate novo no wrapper: `audit_audio_provenance.py` + `measure_worst_frame.py`.

### Idempotência real do rebuild (2026-09-09)
O header SDSC usava `SMS_EMBED_SDSC_HEADER_AUTO_DATE` — que embute um
carimbo de data em 2 bytes do SDSC (0x7FE7/0x7FFB): o rebuild do dia
seguinte mudava a SHA **sem mudar um byte de código** e derrubava o selo.
Pinado para `SMS_EMBED_SDSC_HEADER(0,1,2026,9,8,...)` em `src/main.c`:
dois rebuilds seguidos reproduzem `8a83ca2d…` exatamente (provado). A SHA
é agora invariante de fonte — rebuild nunca mais derruba o selo sozinho.

Curadoria L039/L053 (Wayland/uinput + troca observada) **fechada na fábrica**
em 2026-09-07: `emulator_input.py`, `reconcile_claims` aceita
`input_memory.json` com SHA da ROM.

### Nota de ambiente (2026-09-07, manhã)
Uma **segunda sessão de agente** rodava a suíte `laboratorio_01` no MESMO
Emulicious/host durante esta passada. Colisões reais: handoff
single-instance (meu boot nasceu no estado DELA, frame=1159), higiene
`pkill` mútua derrubando o DAP no meio do run, e disputa de foco de teclado
(kdotool `ids[0]` não distingue duas janelas "Emulicious"). Solução da
vez: arbitragem humana — a irmã foi pausada e o host ficou livre. Rotina
futura: conferir `pgrep -f "Emulicious[.]jar"` antes de rodar e nunca
disputar foco; `pkill` sempre com padrão `Emulicious[.]jar` (o padrão sem
colchetes mata o próprio shell que o executa).

## Ciclo 2026-09-07 (tarde) — trilha do cenário do Ken + dois defeitos de gate

### O que entrou na ROM
`music_battle` era uma sirene de 6 notas em uníssono nos três osciladores
(49 B, 12 frames repetidos 240×). Entrou no lugar um tema autoral: Lá menor
com G# emprestado da menor harmônica na cadência, 150 BPM, 8 compassos,
loop de 12,8 s, quatro canais com papéis separados (lead / harmonia que
vira arpejo nas viradas / baixo motor em colcheias / percussão de ruído).
Gerador: `tools/gen_music_ken_stage.py`, que serializa direto no formato
PSGlib. 945 B — `_CODE` vai a 0x7F2D e **sobram 211 bytes** no cartucho de
32 KB. Qualquer asset novo daqui pra frente exige banking.

Verificado no emulador, não só no papel: as viradas de acorde F3/G3/D3/E3
aparecem na captura de áudio real nas mesmas posições de tempo do render de
referência, dentro de 0,2 s.

### Defeito 1 — `audit_audio` media continuidade, não presença de som
O gate contava `|amostra| > 200` uma a uma. Toda onda periódica cruza o
zero, e cada cruzamento entrava como amostra "inativa": **quanto mais rica
a polifonia, pior a nota**. A sirene antiga (1 cruzamento de zero por
segundo) marcava 99,9%; o tema novo, sem nenhuma lacuna de silêncio além de
11 ms no boot, reprovava com 88%. Subir as atenuações do PSG elevou o peak
e ainda assim baixou o índice — prova de que o eixo medido não era nível.
Agora mede RMS em janelas de 10 ms. Silêncio continua dando 0%.

### Defeito 2 — nenhuma ferramenta promovia eixo para `true`
`build_inner.py` inicializava os 7 eixos em `false` e só **herdava** os
`true` do registro anterior; `reconcile_claims.py` apenas conferia. Logo o
primeiro `true` de qualquer projeto só podia ter vindo de edição à mão do
`build_record.json` — o que o runbook de publicação proíbe. Os eixos não tinham
como fechar pelo caminho legítimo.

Correção: os predicados viraram `reconcile_claims.axis_support()`, fonte
única, e `build_inner` **deriva** dali em vez de herdar. Quem grava e quem
confere não podem mais divergir.

### Defeito 3 (descoberto pela correção anterior)
Com a derivação ligada, `boot_emulador`, `fps_constante` e
`memory_bank_atualizado` ficaram `true` sustentados por artefatos **8h mais
velhos** que a ROM. Causa: `demote_stale_axes` tinha um atalho que, quando
o sha não mudava entre dois builds, retornava `PRESERVADO` e **pulava a
demoção inteira**. O atalho existia porque recompilar renovava o mtime da
ROM — causa já corrigida na raiz por `rom_birth_mtime`. Era remendo sobre
problema morto, e deixava passar evidência genuinamente velha. Removido: a
comparação por data já acerta sozinha com o mtime de nascimento restaurado.

`selftest.py`: 57/57 verdes depois das três mudanças.

### O soco: a acusação estava errada, mas o "FECHADO" também

Investigado em 07/09/2026 (tarde). **O soco não está quebrado, e também não
está provado.** As duas afirmações anteriores deste documento erraram, em
direções opostas.

**Conectei o soco à mão, medindo pela RAM:** com o emulador rodando durante
toda a tecla, `gap=20` → `guile_hp 54→47`, dano **7** — exatamente o
`apply_hit(a, b, 7)` de `ST_PUNCH` em `fight.c`. Na mesma sessão, `gap=24`
→ nada, confirmando o limite `gap < 24` derivado da geometria de
`collide()`: caixa do soco `[px+20, px+32]` contra corpo `[p2x+8, p2x+24]`.

**`collide()` está íntegro**, provado sem teclado nenhum: no modo de atração
a ROM comanda `b1` por código e o HP do Guile cai 64→52→40→28→16→4→0 até o
KO. O pipeline colisão→dano→probe funciona.

**Por que a ferramenta acusava regressão.** Três defeitos de medição em
`prove_input_memory.py`, todos corrigidos:

1. O laço de aproximação saía por `break` com o emulador **pausado** (o
   `break` pula o `dap.cont()`). A tecla era apertada e `probe_keys` lido
   **antes de retomar** — então `keys_b1` era valor velho, do último frame
   emulado, que foi durante o hold de "right". Daí o `0x08` das três
   tentativas da amostra selada: `0x08` é `PORT_A_KEY_RIGHT`; o botão 1 é
   `0x10` e **nunca apareceu**. A ferramenta afirmava "B1 dado a alcance"
   citando um campo que não continha B1 nenhum. Agora o jogo roda durante a
   tecla e `0x10` é exigido de fato (`b1_chegou`).
2. A aproximação em passos curtos com o emulador pausado entre eles não
   fechava a distância: esgotava 6 s parada em `gap` 42 e 24. E o `continue`
   da leitura perdida saía **sem** `cont()`, congelando o emulador pelo resto
   da tentativa. Passada longa com o jogo rodando chega a `gap=20` de forma
   consistente.
3. O veredito comparava `guile_hp` de antes de tudo com o de depois de tudo,
   **atravessando reset de round** — o HP volta a 64 e uma conexão real
   (54→47) virava "64→64, whiff". Agora vale o sinal medido dentro da
   tentativa.

`evaluate_punch` passa a distinguir três casos que antes eram um só: tecla
que não chegou (nada a concluir), whiff com B1 confirmado, e amostra antiga
sem o campo (inconclusiva). Self-check: 21 fixtures.

**O que fica em aberto.** Com a ferramenta corrigida, o run de ponta a ponta
ainda dá negativo — e agora é um negativo *confiável*: `gap=20`, `0x10`
confirmado em `probe_keys`, pose 130 (PUNCH) observada, `guile_hp 64→64`
dentro da tentativa. Ou seja: o soco conecta às vezes e falha às vezes, nas
mesmas condições aparentes. A janela é estreitíssima por construção —
`separate()` para os corpos em `PUSH_W=20` e a caixa exige `gap < 24`, então
sobram **4 px** de folga. Suspeita a testar: alguma condição de estado do
defensor (`hurt_top` sobe de 12 para 34 se ele estiver agachado, o que
mataria a sobreposição vertical) ou o frame exato em que `collide()` amostra
dentro da janela ativa de 4 frames.

Próximo degrau: ~~instrumentar a janela ativa~~ **FECHADO no ciclo
2026-09-08** — os probes (timer/gap/hitstop/hit_used + P[1].state/guard)
dataram a causa (defesa da CPU, L060) e o hit −7 foi provado na v085 e na
v086 com whiff-punish por relógio. A nota antiga "não reivindicar" fica
aqui como registro do estado da época; o teto de claim vigente é o do GDD
("protótipo jogável de luta 1v1"), e o soco consta como provado nos eixos.

## Ciclo 2026-09-25 (3) — identidade do tema: transcrição + voz "FIGHT" + re-selagem

- Pedido humano: "som diferente do tema original; pode colocar voz FIGHT na
  abertura; soa acelerada". Resposta medida: piso ganhou M7 (respiro >= 8
  frames) e LOOP_MIN 250 (L080, SMS_GLOBAL 65).
- `tools/gen_music_ken_stage.py` reescrito: transcritor determinístico do MID
  de referência hasheado. Battle 750 B / 1280 f (0 violações, 0 avisos,
  uníssono 0.0, gaps 14.5/135.6/78.7), title 494 B / 1152 f, voz 45 B / 24 f
  (formantes, canais 1+2+3, autorizada explicitamente — única mudança em
  `fight.c` além do WIP do humano: include, helper `psg_voice_fight`, chamada
  na transição ROUND→FIGHT).
- ROM 71af64d1cad9…: 32 K com 123 B de folga — o oitavo compasso e a voz
  couberam sem paginação (dívida dos 33 B que cortavam o compasso foi paga
  pela economia da transcrição, não por corte).
- `audit_psg_channel_binding.py` corrigido (L081, SMS_GLOBAL 66): máscaras
  compostas eram invisíveis ao gate; agora compara conjuntos de tokens e
  reprova canal não-literal. Manifesto de áudio reescrito com os SHAs finais
  + entrada sfx_fight; mapa `doc/rom_asset_binding.json` agora inclui os 7
  streams compilados (precedente do kage) e passa `--require`.
- Eixos re-medidos na ROM final: boot+semântica PASS, fps 8×60 constante,
  runtime probe PASS (após re-medida limpa — host estava sob carga de outro
  workspace), áudio isolado 33.4 s ativo=100% audit PASS, worst-frame segue
  honesto: derramou vovf_delta=26/12 s, vline_max=199 (classe pré-existente,
  não agravada). Bundle `out/evidence/evidence_bundle.json` selado com 7
  artefatos. Input/gameplay continuam NÃO re-provados (WIP g_control_mode do
  humano — dívida viva, decisão de quando refazer é humana).
