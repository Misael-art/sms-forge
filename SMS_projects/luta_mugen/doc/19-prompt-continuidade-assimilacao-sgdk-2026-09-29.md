# Continuidade do motor MUGEN → SMS: contexto, doação e execução

Data da análise: 2026-09-29. Este documento é um prompt para uma nova sessão de desenvolvimento. A análise leu código e registros locais; não recompilou ROMs, executou testes ou recertificou evidências. Números abaixo são registros do projeto, salvo achados explicitamente identificados como leitura de código.

## Prompt para o próximo agente

Você assume o desenvolvimento do motor MUGEN → Master System em `/mnt/sdcard/Projects/SMSForge`, projeto `SMS_projects/luta_mugen`. Prossiga com implementação e validação até fechar uma fatia jogável, respeitando o escopo do GDD. Relatórios intermediários não encerram o desenvolvimento quando existe uma próxima ação segura. Não peça novamente confirmação para etapas já autorizadas. Não declare capacidade sem evidência da ROM correspondente.

### 1. Entrada e fontes de verdade

Comece dizendo `[Contexto SMS Carregado]`. Leia `/home/misael/.codex/RTK.md`; comandos shell usam `rtk` ou `rtk proxy`. Leia o AGENTS.md aplicável e o framework `tools/sms_wrapper/.agent/ARCHITECTURE.md`, `rules/SMS_GLOBAL.md`, workflows `mugen-engine-quality.md` e `async-promotion-loop.md`.

No projeto, leia na ordem: `doc/10-memory-bank.md`, `doc/11-gdd.md`, `doc/13-spec-cenas.md`, `doc/00-diretrizes-agente.md`, `.mddev/project.json`, `doc/12-roteiro.md`, `doc/15-tdd.md`. Confira também `doc/engine_quality_contract.json` e `doc/05_technical/mugen_engine_standard.md` na raiz do workspace. Headers de SMSlib/PSGlib e `sdk/README.md` são autoridades de API/toolchain.

Há uma divergência documental conhecida: o workflow `mugen-engine-quality.md` ainda contém zero omissões/flicker apenas diagnóstico, enquanto a decisão humana mais recente no GDD e no início do memory bank é **opção 3: flicker mínimo e nenhum glitch**. Aplique a decisão humana atual; não ressuscite o contrato histórico de zero flicker. Registre a divergência e corrija a doutrina compartilhada somente seguindo a autorização e os gates de curadoria aplicáveis. Não sobrescreva `.agent` local existente.

### 2. Objetivo e direção artística

Construir uma engine orientada por dados, reutilizável para personagens MUGEN, com backend SMS explícito. O piso visual é altura opaca de idle **72–88 px**, escala uniforme por personagem, proporções, pivôs, offsets, ordem AIR e CLSN preservados. Poses estendidas podem exceder a altura do idle; devem ter envelopes e budgets próprios. Não normalize cada quadro separadamente.

Ken `ken_masters_adv`, derivado de CPS2, orienta a coesão artística futura. O Ryu atual vem de bootleg NES e é piloto técnico temporário útil para paletas; não é o modelo artístico definitivo. Preserve sua utilidade enquanto prepara uma futura substituição por fonte coesa ao Ken. Não bloqueie engenharia esperando arte completa. Não produza personagens ou cenário final desenhando pixels por código. Fontes/dados derivados exigem proveniência e política de distribuição respeitada.

Sangokushi III é referência de ambição de engenharia; alegações históricas e técnicas não medidas não são contratos de hardware. Qualidade AAA é objetivo contextual, não status atribuído por compilação, relatório, título do emulador ou screenshot de boot.

### 3. Estado que você recebe

Confira os SHAs e o worktree antes de agir; estes são os commits observados na análise:

- `b94320a`: opção 3, L090 planejador cíclico e L091 gate de glitch.
- `886d5cd`: registro do idle com streaming assembly.
- `02d7cf1`: dimensionamento da residência conjunta.
- `69dc780`: registro da integração 72–88 em curso a aproximadamente 30 FPS.

Referência isolada: `out/local_study/scale_pilot_rom_flicker_asmstream/`, dentro do projeto. ROM SHA-256 `0d6b959ab6480322e25636c9c95f5f1cdaa6aa7f9f90de042b66037fa4f05701`; registros de ~59,75 FPS, Ken 4,00 iterações/pose e Ryu 7,26, três vídeos aprovados no modo flicker. Idle fixo não aprova combate.

Candidato integrado: `out/local_study/luta_integrada/`. Contém `src/main.c`, `fight.c`, `stream.c`, `input.c`, ferramentas e dados locais. Está em diretório ignorado: commits de documentação NÃO preservam sua implementação. Inspecione e preserve o delta reproduzível antes de grandes alterações. Não copie cegamente todo `out/` para o Git; versione fontes próprias, configuração, geradores e receitas apropriadas, mantendo dumps, ROMs e recursos restritos conforme o contrato. Leve lógica de build para `tools/sms_wrapper/`, como exige o workspace. Há WIP alheio em MSSF2T, hamoopig e outros projetos: não altere, reverta, stage ou inclua em commits.

O memory bank registra para o integrado:

- Pool atual+próxima nas transições idle/guarda/soco: pior caso 125/128 pares de 64 B; folga de apenas 192 B. Não é aprovação de todos os golpes/FX.
- Metades fixas: 130/128; todas as entradas de guarda/soco residentes no esquema avaliado: 245/128. Rejeitados nesse esquema; isso não prova impossibilidade de toda estratégia de residência seletiva futura.
- SAT após poda de peças totalmente transparentes: 63/64 no pior par avaliado. Não há folga comprovada para magias ou faíscas.
- Idle observado: pico de 100 slots, zero falhas de alocação e zero uploads descartados. Isso não cobre cancelamentos ainda não exercitados.
- AIR coincide em iterações (76 poses Ken, 42 Ryu), mas loop a 29,8–29,9 Hz. Portanto animações estão lentas no tempo real, sem aprovação de cadência.
- Custos registrados em linhas: SAT ~12; streaming termina ~144 linhas após início do VBlank; fight_step 24+20; preparação 19 estável/~100 em troca, alocação ~60; agendador até53; emissão63. Ganhos propostos ainda são estimativas.
- Input existe no código para soco/guarda, mas o ensaio descrito é idle sem input. Latência, combate e glitch na última SAT própria estão pendentes.

O checkpoint de worst-frame acontece antes de `stream_step()`: mede a SAT, não todo o trabalho do frame. Streaming em display ativo é exceção local condicionada a slots não exibidos, timing seguro e prova de render. Não generalize a exceção para outras escritas.

### 4. Doador: estudar e assimilar por método

Leia os diretórios somente como fontes doadoras, sem modificá-los:

`/mnt/sdcard/Projects/Sgdk Forge/tools/mugen2sgdk_forge/`

`/mnt/sdcard/Projects/Sgdk Forge/SGDK_projects/Mugenesis_Demo [VER.001] [SGDK 211] [GEN] [GAME] [FIGHTING]/`

Práticas concretas identificadas:

| Fonte relativa ao doador | Prática | Aplicação SMS |
|---|---|---|
| `mugen2sgdk_forge/stage_runtime_geometry.py`, `wanted_deltas()` | Compila geometria e listas de entradas/saídas offline | Emitir IDs de pares únicos por pose/facing, listas de mudanças por transição e intervalos de scanline; runtime só resolve slots físicos e aplica trabalho limitado |
| Demo `src/scenes/fight_stage_stream.c`, `mark_wanted()` e `refresh_cache()` | Reconcilia IDs alterados contra conjunto final; cache quando nada mudou | Evitar varredura/deduplicação a cada quadro; proteger referências visíveis, cancelar pedidos obsoletos, liberar antes de alocar quando seguro |
| `perf/observer_ab.py` e demo `src/system/runtime_probe.c` | Janelas equivalentes, digest de gameplay, custo do observador, pico ligado ao quadro | Comparar telemetria ligada/desligada em roteiro idêntico; medir deadline e trabalho real, sem pausas DAP contaminando a janela |
| `tests/test_anim_time_contract.py` | Testa tempos e efeitos por fase do tick | Casos AIR 0/1/2/-1, LoopStart, hitpause, ChangeState e momento da hitbox; distinguir tick lógico, VBlank e apresentação |
| `mugen2sgdk_forge/runtime_trace.py` | Compara trilhas determinísticas antes/depois | Provar que otimizações mantêm estados, posições, vida, orientação e colisões; exigir também igualdade de comprimento das trilhas, pois a implementação lida usa zip e não basta para detectar cauda perdida |
| `move_checklist.py`, `duel_matrix.py`, `tests/host/` | CMD→estado→ações alcançáveis; duelos por golpe/distância | Criar matriz Ken/Ryu, ambos os lados, acerto/defesa/erro, chão/ar e cancelamentos; adaptar comandos ao controle SMS explicitamente |
| `source_audit.py`, `schemas/source_audit.schema.json` | Intake e classes de suporte com origem/hash | Declarar suportado/aproximado/não suportado/inconclusivo por recurso; não importar a classificação SGDK como capacidade SMS |
| `runtime/README.md`, `tests/test_runtime_sync.py` | Runtime canônico instalado e cópia verificada | Evitar divergência entre motor, projeto e clones; fonte canônica SMS + instalação verificável, sem copiar backend 68000 |
| `palette_contract.py` | Propriedade, fusão exata em todas as variantes e aproximação separada | Contrato conjunto de P1/P2/FX na paleta de sprites SMS; remap exige equivalência dos bytes/padrões e metadados corretos para P2 |
| Demo `src/scenes/fight_hud.c`, `drawBar()` | Atualiza apenas tiles entre bordas antigas/novas, com cache | HUD na name table SMS, reservado junto ao cenário; não transportar WINDOW/BG_A do Mega Drive |
| Testes `test_stage_restore_scroll.py`, `test_stage_window_ownership.py`, `test_hud_deferred_plane_restore.py` | Posse e restauração após efeitos/transições | Testar restauração de paleta, scroll, tiles, SAT, bancos e áudio em KO/restart/interrupções |

Não copie capacidades do Mega Drive: DMA, quatro paletas, planos BG_A/B/WINDOW, flip de sprite por hardware, pools grandes de RAM, estruturas e aritmética larga do 68000. Adote dados compactos adequados ao Z80, memória estática e APIs reais do SMS. Não transplante uma VM completa sem orçamento; comece pelo subconjunto gerado que o GDD exige, explicitando divergências.

O doador também está em desenvolvimento: seu checkpoint de 2026-09-29 registra `technical_demo`, rotas fight_base/stage ainda sem aprovação integrada e limitações semânticas. Use-o como fonte de soluções verificáveis, não como selo automático de qualidade. Revise diferenças e hashes do manifesto de doação existente; seis falhas de paridade estavam registradas. Não atualize pinos apenas para fazer testes passarem.

### 5. Plano de execução

**Lote A — preservar e medir a base.** Identifique ROM/fonte/configuração exatas do integrado. Registre SHA e receitas. Preserve o candidato reproduzível; rode self-checks antes de consumir medições. O `check_ram_layout.py` local tem uma lacuna por leitura de código: símbolo DATA/INITIALIZED ausente retorna zero. Faça falhar mapa inválido/símbolo obrigatório ausente e meça segmentos, áreas absolutas, buffers e reserva de stack; não declare toda RAM segura só pela soma de dois comprimentos. Mantenha a checagem banco37↔ROM e estenda o vínculo aos dados realmente usados. Faça smoke de render na SAT própria antes de construir mais em cima de imagem ainda não auditada.

**Lote B — recuperar 60 Hz sem alterar gameplay.** Use janela determinística com quadros estáveis, trocas simultâneas e wrap. Conte VBlanks decorridos, ticks lógicos, apresentações, uploads, misses e custo por fase. Use máximos e distribuição, não some medianas independentes para certificar worst-frame. Evite comparar posição absoluta do VCounter com duração sem tratar wrap/região. Meça custo da probe e diferenças on/off sem promover ROM sem telemetria como evidência final.

Compile offline pares únicos, descritores, limites de linhas e deltas de transições. Preserve uma rota correta para cancelamento, troca de facing e salto fora da sequência prevista; LUT de idle não resolve FSM arbitrária. Evite explosão cartesiana de tabelas: meça bytes de ROM, bancos, RAM e custo de lookup. Use cache com chave completa: pose, facing, posição relativa/vertical, clipping, composição concorrente e fase do flicker. Não reutilize agendamento de atores imóveis quando se moverem.

Otimize emissão SAT e alocação a partir do assembly gerado e dos hotspots medidos. Separe upload obrigatório do prefetch oportunista; limite prefetch por deadline total do quadro, deixando tempo para lógica/render/áudio. Não preencha toda a janela de streaming só porque existem bytes na fila. Meça após cada mudança isolada; não prometa ganhos de 63→35 ou60→15 linhas sem executar.

Defina relógios explicitamente. AIR contado em iterações lentas não satisfaz duração temporal. Não masque 30 FPS duplicando decrementos e pulando poses/hitboxes. Busque um tick e apresentação por quadro NTSC; defina política PAL de50Hz e sua relação com os ticks da fonte. Se houver atraso de asset, registre deadline perdido e a consequência; não o esconda na FSM.

**Lote C — input, guarda e soco dos dois jogadores.** Use entrada real pelos canais documentados e scripts determinísticos complementares. Meça quadro da leitura, aceitação, pose visível e hitbox efetiva em frames e milissegundos, inclusive extremos. Mesmo a30Hz, input pode diagnosticar semântica; apenas não o aprove como latência final. Exercite ambos atacando, guarda antes/durante golpe, soltar/apertar rápido, cancelar prefetch, virar durante upload e retornar ao idle por várias voltas.

Mantenha geração/ownership dos pedidos. Nunca escreva padrões ainda visíveis; commit de pose, facing, META e CLSN deve ser coerente. Um pedido cancelado não pode aparecer depois. Verifique que a retenção de atual+próxima+pedido antigo temporário não ultrapassa os125 pares estimados; exercite os estados transitórios, não apenas poses finais.

Adapte L091 a movimento, facing e poses legais derivadas da fonte/trace. Detecte pixels extras, resíduos, peça errada e omissão permanente. Quantifique flicker: duty cycle e maior sequência de ausência por região; não trate PASS numa janela de8 como ausência de flicker. Corpo, rosto e ataques precisam permanecer legíveis; render não altera física. Inclua boot/transições no relatório, explicitando qualquer trecho descartado.

**Lote D — cena mínima integrada e expansão.** Integre cenário estático autoral/proveniente, HUD por alteração e PSG com prioridade/restauração. Refaça mapa completo de VRAM/RAM/ROM e concorrência; 125/128 pares e63/64 sprites deixam pouca margem. Meça andar/pulo, demais ataques do GDD, colisões, dano, rounds, KO, timeout e reinício. Adicione parallax, FM, PCM, efeitos por raster ou BG-as-sprite apenas como estudos separados com custo e fallback. Não use técnicas avançadas para evitar o gargalo atual.

### 6. Critérios de fechamento e entrega

Testes de host verificam semântica, não tempo Z80/VDP. Use testes focados durante cada lote e gates integrais uma vez ao fechá-lo. Instrumentos precisam de self-check aprovado. Reutilize os gates existentes: contrato de engine, recursos/paleta/proveniência, geometria e simulador de scanline, animação semântica, glitch, probe/runtime, worst-frame, input, áudio, vínculo asset→ROM e selo de frescor. Consulte `--help`; não invente argumentos.

Para aceitar o lote integrado, a mesma ROM deve demonstrar: dois atores72–88, timings por pose e hitbox coerentes, input medido, estabilidade temporal NTSC (PAL separado), SAT/VRAM/RAM dentro do orçamento, flicker mensurado, zero glitch nos cenários exercitados e nenhum upload obsoleto. Para entrega de jogo acrescente cena, HUD, áudio, round completo e todos os eixos exigidos pelo workspace. Não estenda um teste idle a todas as ações.

Atualize memory bank, GDD/spec/TDD quando houver mudança real. Registre comando, versão, ROM SHA, fonte/configuração, janela, cenário, métricas e limitações. Versione apenas o delta próprio e reproduzível; commits de documentação não substituem código. Faça um push por lote completo conforme autorização vigente, sem polling de CI. Preserve WIP alheio.

Relate `Resultado / Bloqueio / Próxima ação`, distinguindo documentado, implementado, buildado, testado_em_emulador e validado_budget. Não encerre só com plano ou otimização isolada se houver próximo ramo seguro. Não declare AAA ou engine definitiva antes de fechar os critérios correspondentes.
