# Prompt de continuidade — Lote D: movimento e golpes de cada tipo em P1 e P2, medidos contra a linha de base

Data: 2026-10-02. Este handoff abre a fatia de jogabilidade completa do runtime
integrado do Lote C. Ele não promove a ROM a jogo entregue, não altera a decisão
humana de escala/flicker vigente e não substitui o memory bank (autoridade #1).

## Prompt para o próximo agente

Você continuará o motor MUGEN → Sega Master System no workspace
`/mnt/sdcard/Projects/SMSForge`, projeto `SMS_projects/luta_mugen`, branch
`feat/luta-mugen-motor`. Comece dizendo `[Contexto SMS Carregado]`. Sua missão:
implementar em uma única ROM NTSC integrada o conjunto completo de movimento e
golpe de **cada tipo** para P1 **e** P2 — andar frente/trás, agachar, pular,
guarda, soco fraco/forte, chute fraco/forte — e **medi-la contra a linha de
base do Lote C**, ação por ação, com trilha por tick e gates do cânone.
Trabalhe com máxima qualidade e continuidade: não encerre na primeira
implementação, no primeiro teste verde, nem após produzir diagnóstico ou
relatório — enquanto houver ramo causal seguro dentro desta missão, continue.
Um veredito de bloqueio legítimo encerra o ramo, não a missão.

### 1. Preparação e fontes de verdade

1. Leia `/home/misael/.codex/RTK.md`; todo comando shell deve usar `rtk` ou
   `rtk proxy`.
2. Leia o `AGENTS.md` do workspace, `tools/sms_wrapper/.agent/ARCHITECTURE.md`,
   `rules/SMS_GLOBAL.md` (§78–84 em particular: L093–L099 deste ciclo),
   `workflows/mugen-engine-quality.md` e `workflows/async-promotion-loop.md`.
3. Releia nesta ordem: `doc/10-memory-bank.md`, `doc/11-gdd.md`,
   `doc/13-spec-cenas.md`, `doc/00-diretrizes-agente.md`, `.mddev/project.json`,
   `doc/12-roteiro.md`, `doc/15-tdd.md`, `doc/engine_quality_contract.json` e
   `doc/05_technical/mugen_engine_standard.md`.
4. Leia os handoffs anteriores — `20-prompt-lote-c-...md`,
   `21-estudo-comparativo-sgdk-roadmap-...md`,
   `22-mapa-de-controle-sms-...md` — e os JSONs de aprendizado
   `doc/curation/2026-09-29_l090_l091_...json`,
   `doc/curation/2026-09-30_l092_...json`,
   `doc/curation/2026-09-30_l093_l095_...json`. **Eles são resultado e
   aprendizado acumulados: preservar é parte da missão (seção 2).**
5. Antes de editar, confirme branch, HEAD, `origin`, `git status` e a presença
   de cada ROM/fonte/artefato citado abaixo. A árvore carrega WIP alheio
   (MSSF2T com dívida própria no eixo de input, hamoopig, laboratórios, etc.).
   Não edite, reverta, adicione nem inclua em commit o que não é seu. Faça
   stage apenas de caminhos próprios deste lote. MSSF2T é intocável.
6. Headers `sdk/devkitSMS/SMSlib/SMSlib.h` e `PSGlib/PSGlib.h` são a autoridade
   final de API (`SMS_getJoystick`/`KEY_1`/`KEY_2`/`SPRITEMODE_TALL`: confira o
   header, não a memória). `sdk/README.md` para o toolchain.

O GDD vigente registra a decisão humana de opção 3 (flicker mínimo, nenhum
glitch, corpo idle 72–88 px). Este lote **não** reabre escala, não explora
zoom/MAG, paralaxe, H-scroll, raster, PCM/FM nem a matriz de rotas de escala
discutida em 2026-10-02 — isso seria outro lote, com decisão humana própria.

### 2. Preservação: o que você recebeu é resultado E aprendizado

Este lote servirá à curadoria do agente canônico. Portanto:

- **Nunca sobrescreva evidência**: ROM canônica do Lote C, vídeos, traces,
  capturas de áudio, bundles e relatórios citados no memory bank continuam
  byte a byte. Toda medição nova ganha nome e SHA novos.
- **Não reescreva histórico**: memória, GDD/TDD e os prompts 18–22 recebem
  acréscimos e retificações datadas; decisões superseded ficam marcadas como
  tais (padrão do projeto), nunca apagadas.
- **Furo de aprendizado vira métrica**: cada falha nova do lote (ferramenta,
  runtime, método) fecha como JSON canônico em `doc/curation/` + seção
  numerada em `SMS_GLOBAL.md` + ferramenta/autocorreção que a impeça, com
  `audit_learning_capture.py` PASS. Regra vira medição, nunca só prosa.
- **Separe explicitamente resultado novo × herdado** em todo relatório: número
  da ROM/sha do Lote C citado como comparação é herdado; só conta como desta
  ROM o que ela mesma produziu.
- **Vocabulário de status obrigatório** em cada afirmação: `documentado ≠
  implementado ≠ buildado ≠ testado_em_emulador ≠ validado_budget`.
- Ao fechar, atualize memory bank (fatos, comandos, SHAs, janelas, limites),
  `doc/changelog/` e os manifests de proveniência/vínculo; rode
  `audit_doc_sync.py`. Estado de sessão não substitui nada disso.

### 3. Estado recebido: a linha de base que você medirá contra

ROM canônica do Lote C: `out/local_study/luta_integrada/out/rom/scale_pilot_80px.sms`,
655.360 B, SHA-256 `c958278fa0196e84deecab1fef01f976100072cd9851e9c233f82a694a882999`;
receita `tools/sms_wrapper/build_luta_integrada.py` (`--check-only` PASS).
Vínculo em `doc/rom_asset_binding_lote_c.json`. Fontes em `integrada/`.

Números medidos a preservar como comparável (todos desta ROM ou de clone com
ganchos, SHA `4a049f76…`):

| Métrica | Valor Lote C |
|---|---|
| P1 soco: pose visível / hitbox | 26 / 125 frames após o toque |
| P2 soco: pose / hitbox | 18 / 39 frames (errou por distância fixa) |
| Guarda: P2 pose / P1 | 20 frames / leitura ambígua |
| Toque→dano (trilha de tick) | 124 ticks (tick 10 → 134) |
| Lentidão sobre AIR (soco Ken) | 12,73× em 5 quadros completos |
| Causa atribuída (L098) | guarda "pose desejada visível" de `tick_anim` = throughput de streaming, não FSM/entrada/tabela |
| Banda de upload (L099) | ~3 pares 8×16 por frame |
| Pose de soco Ken | 225 pares vs pool de 128 (pool 125/128 no corte atual) |
| Variantes não adotadas | `urgent_first` (hit 123), `action_first` (hit 88, custo: idle Ryu parado 40 ticks), `decoupled_pin` (pool no teto, idle Ken 8–24 ticks/pose) |
| NTSC | 59,59/59,75 FPS (janelas 30 s); worst-frame com 1 soco conectado: 3000 frames, `vovf_delta=0`, `vline_min=211` |
| Rounds | 2 timeouts → WIN 2–0; **KO por golpe nunca observado** (25 socos: 10 dano, 15 miss) |
| Flicker | L091 v2 idle PASS mecânico (0/781); Ryu <50% de cobertura por até 3 quadros; julgamento humano de "mínimo" pendente; captura **não cobre ações** |
| Áudio | `music_battle` escreve canais 0–3; SFX 2/3; captura isolada de soco 11,1 s PASS |

Blockers conhecidos que este lote toca de frente:
- Direções mascaradas; `main.c` lê B2 como guarda — diverge do mapa final do
  GDD (B1 soco, B2 chute, recuo+baixo = guarda; `fight.c` já usa Down+Back).
- `integrada/src/input_tier.c` (classificador O(1), 4 B RAM, teste diferencial
  gcc com mutação detectada) **não está ligado à ROM**: sem build SDCC, sem
  custo Z80 medido, tier não dispara padrão de comando.
- O corte do Ken tem apenas soco e chute; **não existem poses/estados dos
  tiers fortes** ainda, e o pool está em 125/128 pares.
- **Sem colisão de corpo (playerpush)**: L098 capturou P1 atravessando P2
  (x 96→155) com auto-facing invertendo o estado — movimento completo sem
  playerpush gera golpe impossível e leitura falsa de "andar".
- Latência/AIR: linha de base continua injogável; este lote pode melhorá-la,
  não pode reclassificá-la por documentação.

### 4. Problemas anteriores que não podem voltar

- ACK de input não prova pose, hitbox, dano nem HUD; pose apresentada deve
  corresponder ao estado lógico do mesmo tick.
- Captura de idle não prova ação; vídeo do Lote C sem máscara por lutador não
  prova glitch de ações.
- FPS de emulação, cadência de animação e latência humana são métricas
  diferentes; não apresente uma como as outras.
- Média que esconde pior caso não vale: reporte valor **por ação**.
- Duas execuções da mesma fórmula não constituem prova independente; juiz de
  trilha é `analysis/trace_compare.py` (L096), e a comparação de AIR é
  `analysis/trace_vs_air.py` (L098) — não o próprio produtor.
- Leitura de ferramenta sem `--self-check` aprovado não conta; DAP pausa a
  emulação — trace não é evidência de FPS.
- Não altere manifesto/texto para fazer gate passar (precedente PSG §Áudio do
  TDD: o manifesto descreve o desejado, os bytes provam o real).
- Números de Mega Drive não são lei SMS (planes, DMA, paleta, sprites/linha).
- Arte final de personagem/cenário não nasce de código; poses novas de golpe
  vêm do acervo MUGEN via pipeline com proveniência hasheada, senão o item é
  bloqueado e registrado, não fabricado.
- Pool/efeito sem linha medida no worst-frame não entra no build.
- `PASS` de L091 com janela de 8 quadros não significa flicker zero; o
  runtime integrado não autoriza claim `delivery`.

### 5. Objetivo finito

Entregar uma ROM NTSC que, com palco/HUD/PSG/rounds do Lote C preservados,
responda ao **mapa de controle final do GDD em ambos os pads** — P1 e P2 cada
um com: andar frente, andar trás, agachar, pular, guarda, soco fraco, soco
forte, chute fraco, chute forte — com playerpush e facing corretos, tiers
disparados pelo classificador de tempo de pressão (T=6, decisão de 2026-09-30;
`b`/`y` descartados por decisão, não por falha), e **cada ação acima medida
contra a linha de base da seção 3**, por trilha de tick na mesma metodologia
L097, com vídeo de framebuffer e áudio nos eventos. O especial QCF+P1 entra
**apenas** se o orçamento de pool do passo A comportar; senão, registra-se o
bloqueio com número. Um round completo deve ser vencido **por KO de golpe**
(soco ou chute de qualquer tier), não apenas por timeout.

### 6. Sequência de trabalho

#### A. Contrato e orçamento ANTES de código e de arte

1. Rode `analysis/move_checklist.py` e `analysis/anim_time_contract.py` (com
   `--self-check`) sobre os dois cortes com o mapa de 2 tiers definitivo:
   matriz ação × pad × AIR × pares 8×16 × bytes de upload por transição.
2. Calcule o total de pares do conjunto expandido (4 families de golpe por
   lutador + movimento) vs pool de 128 e a demanda B/VBlank por transição,
   no padrão do piloto de escala (`scale_pilot.py --self-check` + vídeo fresco
   antes de promover qualquer coisa).
3. Se o conjunto não couber (hipótese forte: não cabe), a decisão A/B/C do
   Lote C (reduzir pares por pose de ataque / desacoplar lógica de hit /
   residência seletiva) precisa de número por variante **e de decisão humana
   antes de reautoria de arte**: apresente a tabela com a recomendação e pare
   nesse ponto, registrando `Resultado / Bloqueio / Próxima ação`. Não
   promova corte "no feeling".
4. Atualize GDD (mapa de tiers + T=6 é decisão de 2026-09-30 ainda não
   espelhada no GDD — item 1 do doc 22) e TDD (mapa de RAM/pools nomeados)
   somente com decisões reais deste lote.

#### B. Input completo nos dois pads

- Ligue `input_tier.c` ao build SDCC da ROM (custo em ciclos Z80 medido, não
  estimado), implemente o mapa final nos dois pads com direções decodificadas,
  e faça o tier emitir nos padrões de comando (muda o blob `_CMD_` — formato
  versionado, golden atualizado **de propósito** e registrado).
- Adicione playerpush (empurrar sem atravessar; limites por linha de piso e
  por borda da arena) e corrija a inversão de auto-facing do achado L098.
- Negativos obrigatórios no harness: dois toques que não geram acorde inviável,
  liberação antes/depois de T, input concorrente nos dois pads, bordas de
  arena com push.

#### C. Estados e poses por tipo de golpe

- Estenda o corte conversor-para-ROM com as famílias LP/HP/LK/HK de Ken e Ryu
  a partir do acervo (mesmo pipeline S2–S4; proveniência com SHA; nada de
  pixels nascidos de código). Frames vazios, tempos, eixos e CLSN preservados
  pela política AIR; poses fortes de P1 e P2 distintas — clonar animação com
  outro nome reprova em `audit_animation_semantics.py`.
- A cada incremento: compile e rode só os testes focados do sistema alterado;
  gates integrais uma única vez no fechamento.

#### D. Medição contra a linha de base (núcleo da missão)

- Gere ROM fresca; confirme `--check-canonical` dos ganchos (código salva/mapeia
  restaurado; ROM com e sem hooks idêntica) e produza clone de trilha com SHA
  próprio. Roteiro de entrada por ação, **mesmos inputs e mesmas condições
  iniciais** entre baseline e novo quando comparar; use o helper range-synced
  (reamostrar alvo após IDLE — precedente do whiff) e eco de keys no canal de
  input (`emulator_input.py --self-check` antes de qualquer gate de janela;
  matar zumbi `pkill -f '[E]mulicious.jar'` em chamada separada — L057).
- Tabela por ação × jogador: aceite → 1º pose visível → hitbox ativa → dano ou
  whiff → recuperação, em ticks de ROM, contra os números da seção 3.
  Rode `trace_vs_air.py` por ação (razão sobre AIR) e `trace_compare.py` como
  juiz entre trilha esperada e produzida.
- Prova de gameplay real: KO por golpe observado na trilha E no framebuffer
  (banner, placar 1–0 derivado do evento, round seguinte com reset único de
  vida/posição/pose/flags/timer).
- Vídeo de framebuffer das transições relevantes (intro→luta, golpe→contato,
  KO→resultado) via `capture_video.py`; L091 **v2 por lutador com fundo
  subtraído** estendido a poses de ação, não só idle; captura de áudio isolada
  por evento (soco fraco/forte, chute fraco/forte, hit, KO) com
  `audit_audio.py` + piso de qualidade PSG.
- Desempenho na ROM final: `measure_runtime_probe.py` (janelas independentes),
  `measure_frame_advance.py`, `measure_worst_frame.py` com os dois jogadores
  ativos + HUD + PSG (o perfil do Lote C cobre um soco conectado de P1 só);
  PAL continua fora — declare não medido.
- Controle discriminante: uma variante que ignore o tier (forte == fraco) ou
  que pule o playerpush deve fazer a prova **falhar**; afrouxar critério para
  obter verde é proibido.

#### E. Gates de fechamento (uma vez, na ROM final)

Build real SDCC/devkitSMS; `audit_validate_resources`,
`audit_sprite_mode`/geometria, `audit_luma_floor`, `audit_provenance`,
`audit_tilemap_bounds`, `audit_symbol_size_sync`, `audit_psg_channel_binding`,
`audit_audio_provenance`, `audit_render_glitch` (vídeo novo),
`audit_hardware_constants`, `audit_mugen_engine_contract` (decisão/fallback por
técnica tocada), `audit_rom_asset_binding` novo, `seal_fresh_evidence_bundle`
(janela de 120 min), `reconcile_claims`, `audit_claims`,
`validate_measurement_tools`, `audit_doc_sync`, `audit_learning_capture`,
`audit_specialization`. Use `--help`; não invente opções.

### 7. Definição de conclusão

Lote D termina quando, numa mesma ROM fresca com SHA único: o mapa final do GDD
responde nos dois pads com as 9 ações por jogador comprovadas em trilha; o KO
por golpe foi observado; cada ação tem número contra a linha de base da seção 3
com razão AIR por ação; worst-frame/probe/frame-advance/áudio/vídeo passaram
nos gates; vínculo, bundle fresco, claims reconciliados, memory bank,
changelog, lição(s) nova(s) em `doc/curation/` e este prompt preservado como
handoff. Se um critério depender de decisão humana pendente (corte de pool do
passo A, por exemplo) ou de dado realmente ausente, registre o bloqueio com
evidência, comando de reprodução e alternativas investigadas — e **continue
todo trabalho independente restante**; o bloqueio encerra o ramo, não a missão.

Limites inegociáveis do relato: não declare jogo pronto, AAA, entrega `delivery`,
cadência AIR aprovada, responsividade aceita, flicker zero, PAL validado nem
"troca por `.def` sem C" — nada disso é provado por este lote. Teto de claim:
`protótipo jogável de engine de luta MUGEN→SMS dirigida por dados`, época
visual no máximo `technical_candidate`/`probe` conforme evidência.

Siga o workflow de desenvolvimento contínuo: lote vertical, um push no fim,
sem polling de CI nem narração de gates em loop; rode longos em background e
use a espera para o próximo trabalho seguro. A autorização prévia do usuário
para registrar progresso no GitHub permanecia válida no fechamento do Lote C;
reconfirme antes do push se houver dúvida. Reporte intermediário sempre:
`Resultado / Bloqueio / Próxima ação`, diferenciando implementação de prova em
emulador.
