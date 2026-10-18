# Prompt de continuidade — Lote C: palco, HUD, PSG e rounds

Data: 2026-09-30. Este handoff consolida o estado medido do Lote B e define
uma fatia de integração. Ele não promove a ROM a jogo entregue e não substitui
o memory bank.

## Prompt para o próximo agente

Você continuará o motor MUGEN → Sega Master System no workspace
`/mnt/sdcard/Projects/SMSForge`, projeto `SMS_projects/luta_mugen`. Comece
dizendo `[Contexto SMS Carregado]`. Implemente e valide uma fatia integrada de
palco estático, HUD, áudio PSG e ciclo de rounds. Não trate FPS de emulação,
uma captura de idle ou um relatório como prova de jogo completo.

### 1. Preparação e fontes de verdade

1. Leia `/home/misael/.codex/RTK.md`; todo comando shell deve usar `rtk` ou
   `rtk proxy`.
2. Leia o `AGENTS.md` do workspace, `tools/sms_wrapper/.agent/ARCHITECTURE.md`,
   `rules/SMS_GLOBAL.md`, `workflows/mugen-engine-quality.md` e
   `workflows/async-promotion-loop.md`.
3. Releia nesta ordem: `doc/10-memory-bank.md`, `doc/11-gdd.md`,
   `doc/13-spec-cenas.md`, `doc/00-diretrizes-agente.md`,
   `.mddev/project.json`, `doc/12-roteiro.md` e `doc/15-tdd.md`.
   Consulte também `doc/engine_quality_contract.json` e
   `doc/05_technical/mugen_engine_standard.md`.
4. Antes de editar, confirme branch, HEAD, `origin`, status e a presença de
   cada fonte/artefato citados abaixo. O worktree contém mudanças alheias em
   MSSF2T, hamoopig, laboratórios e outros projetos. Não as edite, reverta,
   adicione ou inclua no commit. Faça stage apenas de caminhos próprios deste
   lote.
5. Headers de `sdk/devkitSMS/SMSlib/SMSlib.h` e
   `sdk/devkitSMS/PSGlib/PSGlib.h` são a autoridade final de API. Confira
   `sdk/README.md` para o toolchain.

O GDD vigente registra a decisão humana de opção 3: flicker mínimo, nenhum
glitch, sprites de 72–88 px. Documentos antigos ainda dizem “zero flicker
visível”; não ressuscite esse critério nem altere a doutrina compartilhada
neste lote. A decisão atual não autoriza corrupção, resíduo ou omissão
permanente. PASS de L091 com janela de 8 quadros não significa ausência de
flicker.

### 2. Estado recebido: evidência e limites

O código de integração está em `SMS_projects/luta_mugen/integrada/`; a receita
reproduzível é `python3 tools/sms_wrapper/build_luta_integrada.py`. A ROM
registrada no fim do Lote B foi
`out/local_study/luta_integrada/out/rom/scale_pilot_80px.sms`, 655360 bytes,
SHA-256
`b58e16e25f968d2900ddeadd09f61b8b69e6410dc512212cb92f17ec50269e47`.
Código do lote: `e274d74`; documentação: `43df572`, ambos em
`feat/luta-mugen-motor` e `origin/feat/luta-mugen-motor` na última inspeção.
Confirme tudo no repositório antes de usar; não presuma que a ROM ainda existe
ou corresponde às fontes atuais.

Estado medido na ROM acima:

- Duas janelas DAP de 8 s: 59,04 e 59,06 FPS, spread 0,02, 962 quadros.
  Isso comprova estabilidade temporal NTSC naquela build, não cadência AIR,
  resposta do combate, PAL ou entrega visual.
- O vídeo de framebuffer de idle tem SHA-256
  `723a2ed23b0e62d756019784a821441d3f9ab594477046224a9630651b551a73`, 598
  quadros/9,98 s. L091 em modo `flicker`, janela 8: 0 quadros com pixels
  extras, extra máximo 0, ausência máxima 898 pixels. Esse último valor é
  contagem de pixels ausentes no pior quadro, não duração em quadros. A
  aceitação é cobertura dentro da janela, portanto há flicker e ele precisa
  ser caracterizado; não declare flicker zero.
- A cadência AIR ainda reprova: as 27 poses de idle completadas caíram no
  balde de pelo menos 3 quadros além da duração AIR. Não declare 4 quadros por
  pose nem animação em tempo AIR.
- A tecla foi aceita no próprio quadro da borda, mas o primeiro sprite novo
  apareceu em 30 quadros para soco/31 para guarda do P1, e em 17/22 quadros
  para soco/guarda do P2. O hitbox de soco apareceu em 127 quadros (P1) e 43
  (P2). A 59,04 FPS são aproximadamente 0,29–0,53 s até a pose e 0,73–2,15 s
  até hitbox. Estes números são uma linha de base ruim, não um aceite de
  responsividade.
- O controle ensaiado na ROM integrada é B1=soco e B2=guarda; direções estão
  mascaradas. No Emulicious usado no ensaio: P1 `a`/`s`, P2 `g`/`h`. Para P2,
  use `tl_presses[1]` e o estado: `probe_keys` não expõe os botões de P2. O GDD
  descreve B1=soco, B2=chute e recuo=guarda; registre e resolva essa diferença
  antes de declarar o mapa de controles do jogo.
- O integrado medido tem palco preto, sem HUD e sem áudio compilados. A
  evidência de input veio da RAM; não há vídeo de soco/guarda. Dano e combate
  real, tempo/rounds, áudio, palco, HUD, pior frame da nova composição e PAL
  não foram medidos nesta ROM.
- A ROM antiga de A2 não foi sobrescrita no memory bank. Preserve esse
  histórico.

Não apresente estabilidade a 59 Hz como velocidade de animação: são métricas
diferentes. Nem permita que palco/HUD/áudio aumentem a latência registrada sem
um motivo medido. Mesmo sem regressão, os números atuais continuam bloqueando
uma alegação de jogo responsivo ou de entrega.

### 3. Objetivo e limites deste lote

Construa, em incrementos verticais, uma única ROM NTSC integrada que percorra
o fluxo de round previsto no GDD e use um palco autoral estático, HUD na camada
de tiles e áudio PSG audível. Reuse dados e ideias que já existem no projeto,
mas inspecione antes de portar: `SMS_projects/luta_mugen/src/main.c`,
`src/audio.c`, `res/audio/` e `doc/audio_provenance_manifest.json` são uma
implementação anterior, com arquitetura/pool 1:4. Eles são doadores, não
prova de compatibilidade com o runtime integrado de 72–88 px.

Não amplie o lote para paralaxe, H-Blank, raster, BG-as-sprite, PCM, FM/YM2413,
seleção de personagem, múltiplos palcos ou produção completa da arte CPS2.
Comece com uma câmera fixa e um cenário. Ken continua referência artística
CPS2; Ryu NES bootleg permanece piloto técnico temporário de paleta. Arte de
personagem ou cenário final não pode nascer de código.

### 4. Sequência de trabalho

#### A. Baseline e causa da latência

- Confirme a fonte/ROM SHA recebida e salve métricas do estado inicial antes
  de integrar sistemas.
- Inspecione o caminho de input → estado → pose lógica → preparação/stream →
  SAT → hitbox. Descubra por que a pose de ataque demora 17–30 quadros e a
  hitbox 43–127; não esconda o atraso tocando SFX, alterando o contador ou
  apresentando uma pose que não corresponde ao estado/hitbox.
- Obtenha uma trilha por quadro que distinga aceite, estado, pose lógica,
  pose apresentada, upload, hitbox ativo e evento de dano. Use uma ROM limpa
  e as duas entradas P1/P2 comprovadas. Preserve a evidência original; gere
  nomes/SHA novos para novas medições.
- AIR e latência são bloqueios em aberto. Este lote pode prosseguir com os
  sistemas de apresentação, mas não pode reclassificar a linha de base como
  aceitável. Se a causa puder ser corrigida sem quebrar a prova de frame,
  faça a correção isoladamente e remeça; caso contrário, registre o blocker
  com a menor próxima ação reproduzível e não declare golden slice jogável.

#### B. Palco fixo, contrato antes de arte cara

- Leia roteiro e especificação de cenas; produza primeiro uma planta/storyboard
  em pixels e um contrato de palco: área de HUD, linha de piso, posições
  iniciais, faixa de movimento, camadas/tiles, paleta compartilhada, tiles
  reservados e bytes/ciclos de upload.
- Meça a convivência do mapa de fundo com tiles de HUD e os padrões dos dois
  lutadores. Use um só tileset/mapa BG de SMS e ROM/RAM/VRAM reais; não porte
  planos, janelas, DMA nem capacidade de VRAM do Mega Drive.
- Após o contrato e os gates de recurso/proveniência, crie ou integre um único
  palco estático com câmera fixa. A fonte deve ser declarada e hasheada. Se
  ainda não há fonte que possa entrar no repositório/distribuição, mantenha o
  artefato em quarentena conforme a política e reporte o bloqueio concreto;
  não fabrique arte final por código.
- Não faça scrolling neste lote. Não escreva padrões de tiles visíveis fora
  da janela segura de VRAM/VBlank. Mostre o palco junto aos dois lutadores e
  rode os gates de glitch, geometria e fidelidade relevantes.

#### C. HUD no Background

- HUD ocupa a name table/background, não a SAT: duas barras de vida, timer e
  placar de rounds, mais mensagens de round/KO/resultado necessárias ao GDD.
  Defina fonte, grid, paleta e tiles reservados; garanta que as regiões do
  palco/HUD não sobrescrevam os slots do streaming dos lutadores.
- Atualize somente células que mudaram, usando o limite antigo/novo das barras
  e uma fila fixa/limitada de escritas. Não use `malloc`; não faça atualização
  em massa fora da janela de vídeo segura.
- Defina a frequência do timer a partir do GDD/configuração MUGEN autorada;
  não invente duração. Se não existir um valor autoritativo, registre uma
  decisão explícita no documento do projeto antes de codificar.
- Valide vida, timer, score e mensagens contra estado observado em RAM e no
  framebuffer. O HUD deve refletir a mesma lógica de combate, sem virar uma
  fonte paralela de verdade.

#### D. Áudio PSG — resolver o contrato antes da integração

- Há um conflito conhecido que precisa ser resolvido: o TDD declara BGM nos
  canais 0+1 e SFX em 2+3; o manifesto atual declara `music_battle.psg` como
  “music channels 0-3”. Leia PSGlib, o parser/gerador e os bytes dos streams
  antes de escolher o roteamento. Rode `audit_psg_channel_binding.py` e
  `audit_audio_provenance.py` com seus self-checks aprovados. Não altere só o
  texto do manifesto para fazer o gate passar.
- Verifique origem, SHA, bytes e papel de todos os streams a reutilizar:
  `sfx_shot`, `sfx_hurt`, `sfx_hit`, `sfx_down`, `music_battle`,
  `sfx_special`, `sfx_round`. Reuse a geração existente quando for válida;
  reautoria deve atualizar manifesto/hash e respeitar a política de assets.
- Use apenas API real declarada em `PSGlib.h`. Atualize a música com
  `PSGFrame()` na cadência documentada, uma chamada por frame conforme a
  arquitetura validada. Defina política bounded de prioridade para SFX
  (KO/impacto/especial/ação/round, conforme GDD), comportamento de interrupção
  musical e restauração. Não afirme “channel stealing” ou restauração se o
  driver/stream não implementa isso.
- Faça captura isolada de áudio de boot/round e de contato/KO; prove que BGM e
  SFX coexistem no hardware emulado, sem silêncio, metralhadora ou perda de
  canais, e avalie o gate de qualidade PSG. Sincronize sons ao evento que os
  justifica (round, contato, KO), não ao simples fato de uma tecla ter sido
  pressionada.

#### E. FSM de round/match

- Inspecione `integrada/src/fight.c` e os eventos de combate já existentes; não
  replique vida/colisão numa segunda FSM. Integre um round manager estático
  com estados explícitos equivalentes a intro, ativo, resultado/KO/timeout,
  próximo round e fim de partida/rematch, conforme o GDD.
- Em best-of-three, score e vencedor devem derivar do evento real de KO ou
  timeout; empate/duplo KO deve ter regra definida pelo GDD ou documentada
  como decisão antes da implementação. Pausar luta durante banner/transição é
  permitido; congelar input/combate não deve suspender o VBlank, HUD/áudio
  necessários nem deixar a SAT desatualizada.
- No próximo round, reponha vida, posições, facing, pose/estado, hitbox,
  timer e flags de golpe uma única vez. Evite pontuar KO repetidamente em
  frames consecutivos. Mostre `ROUND`, `FIGHT`, `K.O.`/`TIME OVER`, score e
  vencedor no HUD, usando os eventos reais.
- A duração do timer e a política de empate têm que vir de fonte autoritativa
  ou ser decisões registradas no GDD. NTSC deve contar quadros ROM, não tempo
  de parede. PAL exige política própria e medição separada; não herde 60 Hz.

#### F. Integração e desempenho

- Após cada incremento, compile e faça apenas verificações focadas do sistema
  alterado; antes de fechar o lote, gere uma ROM fresca e rode uma única vez
  os gates integrais pertinentes.
- Meça worst-frame com palco, HUD, stream/SAT, input, duas lógicas de luta,
  HUD e PSG ativos. O perfil da ROM anterior não cobre esses novos custos.
  Confirme 59–60 FPS NTSC em janelas independentes, VBlank sem derrame e
  `frame_advance` regular. Compare latência e cadência AIR contra a linha de
  base e reporte valor por ação, não média que esconda pior caso.
- Exercite pelo menos: boot → ROUND/FIGHT → golpe que conecta → vida/HUD
  atualizados → KO → próximo round → segundo KO/timeout → resultado de
  partida. Inclua P1 e P2, golpe que erra, guarda se mantida, timer e reentrada
  após transição. Registre controles realmente aceitos; não alegue direcional
  ou chute enquanto mascarados/ausentes.
- Capture framebuffer dos estados/transições e áudio em arquivos distintos.
  Vincule artefatos à ROM SHA; execute self-check de cada ferramenta de
  medição antes de confiar nela. Atualize binding asset→ROM, claims,
  reconciliação, bundle fresco e memory bank. Marque separadamente
  `documentado`, `implementado`, `buildado`, `testado_em_emulador` e
  `validado_budget`.

### 5. Gates e definição de conclusão deste lote

Consulte `--help` e use os gates canônicos adequados, sem inventar opções.
No mínimo considere:

- build SMS real com SDCC/devkitSMS e auditoria de recursos, paleta,
  proveniência e geometria/scanline;
- `audit_render_glitch.py` em vídeo novo, com a decisão de flicker vigente;
- `measure_runtime_probe.py`, `measure_frame_advance.py` e
  `measure_worst_frame.py` na ROM integrada com sistemas ativos;
- `audit_tilemap_bounds.py`, `audit_psg_channel_binding.py`,
  `audit_audio_provenance.py`, captura/auditoria de áudio e qualidade PSG;
- `audit_rom_asset_binding.py`, `audit_claims.py`, `reconcile_claims.py` e
  selo de bundle fresco conforme o estágio alegado.

O Lote C só pode ser relatado como **integração de sistemas testada** se a
mesma ROM fresca mostrar o palco com dois lutadores, HUD consistente, áudio
PSG audível e um ciclo real de pelo menos um round, sem glitches, sem derrame
de frame e com artefatos vinculados ao SHA. Só declare o fluxo de best-of-three
implementado/testado se a sequência atingir o resultado previsto pelos dados
e eventos; uma tela que escreve “ROUND 2” não basta.

Mesmo que o Lote C passe, não declare “jogo pronto”, “AAA”, engine completa,
cadência AIR aprovada, input responsivo, zero flicker, PAL validado ou entrega
visual `delivery` enquanto esses eixos não tiverem evidência própria. A linha
de base atual de AIR/latência permanece um bloqueio explícito; a integração
não pode apagá-lo por documentação.

### 6. Registro e entrega do lote

Atualize o memory bank com apenas fatos observados, fonte/configuração,
comando, build ID/ROM SHA, emulador, janelas, controles, casos exercitados,
métricas e limites. Atualize GDD/TDD/spec somente para decisões ou mudanças
reais. Preserve este prompt como handoff do Lote C; não reescreva o histórico
do Lote A2/B.

Siga o workflow de desenvolvimento contínuo: lote completo, um push no fim,
sem polling/narração do CI em loop. A autorização prévia do usuário para
registrar progresso no GitHub continua válida. Faça commits de caminhos
próprios, preserve WIP não relacionado e reporte `Resultado / Bloqueio /
Próxima ação`, diferenciando implementação de prova em emulador.
