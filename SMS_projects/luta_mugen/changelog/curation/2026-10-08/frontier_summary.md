# Reconciliação das frentes MUGEN — 2026-10-08

## Decisão de continuidade

`build_v088` é a última ROM registrada na rota `changelog/roms/`, mas não representa o estado mais recente dos estudos. Os diretórios `out/local_study/*` são experimentos isolados e ignorados pelo Git; seus números `v089`–`v110` são nomes de estudo, não releases canônicas. Não renumerar nem promover um estudo como `build_v089` por semelhança de nome.

Foi criado um inventário hashado de todo o conteúdo dos estudos e das fontes/evidências selecionadas do projeto, mais um arquivo de revisão com textos, código, manifestos, build records e evidências textuais. ROMs, vídeos e demais saídas pesadas permanecem nos caminhos existentes e entram no inventário por caminho, bytes e SHA-256. Arquivos de banco usados como fonte de runtime são incluídos no pacote quando identificados como tal. A captura não remove, limpa, renomeia nem sobrescreve nenhum clone.

O recorte cobre também o corpus de entrada `base/` (incluindo os arquivos em `base/OUTROS`, `SOUND/`, `SPRITES/` e `character/`), as rotas alternativas `integrada/` e `rascunho/`, `res/`, `.agent/`, `.mddev/`, o histórico canônico inteiro `changelog/roms/` e os outputs do projeto fora de `out/local_study/`. Documentos de autoridade inacessíveis são registrados como erro de leitura, não substituídos por cópias antigas.

Arquivos desta reconciliação:

- `frontier_inventory.json` — índice de clones, fontes, build records, evidências, ROMs/mídia por hash e divergências observadas.
- `learning_ledger.json` — observações e lições com evidências e próximos passos para curadoria futura, sem promover código nem alterar doutrina global.
- `candidate_repro_build_20261008.json` — resultado da reprodução isolada do candidato coerente Ryo/Terry.
- `route_reconciliation_20261008.json` — comparação por caminho, bytes e SHA-256 da árvore canônica atual, do candidato `hitbroad` e da rota `integrada/`.
- `local_study_source_and_reports.tar.gz` — snapshot comprimido de fontes, corpus MUGEN de entrada, arquivos das rotas alternativas, documentação local, manifestos, relatórios, registros e bancos selecionados.
- `capture_frontier_snapshot.py` — procedimento reproduzível que gera ambos.

## Estado canônico observado

- A sequência em `changelog/roms/` termina em `build_v088`. `out/build_record.json` associa essa rota à ROM de SHA-256 `7afc9b13bbae169a26b5e4de2fec70608e1bcf3cb72cea4da6d99851f73eb029`.
- O registro atesta build e validação, mas não boot, gameplay, FPS, áudio ou memória. Portanto, não há base para chamar `build_v088` de entrega validada.
- O código ativo inclui headers gerados em `out/local_study/generated/versus_cut/`; `.mddev/project.json` referencia o banco de `out/local_study/ryo_terry_cmdv4_20261008/`. A divergência está confirmada: o manifesto `versus_cut` associa **os dois slots** a `ffspRyo.def`/SHA `7272abcf…f32133`, com 77 poses cada e banco de 507.904 bytes (SHA `67400983…dd6870`); o banco cmdv4, de 1.753.088 bytes (SHA `a85aeb99…b598e`), foi gerado para Ryo (`ffspRyo.def`, 94 poses) + Terry (`A-Terry.def`, 185 poses). Nomes `p1_ken`/`p2_ryu` e prefixos de símbolo são rótulos legados; `source_def` e SHA são a identidade.
- Há um conjunto de implementação candidato compartilhado por `out/local_study/ryo_terry_runtime_rom_ramfix_20261008/` e `out/local_study/ryo_terry_hitbroad_20261008/`: os dois têm os mesmos hashes de banco e headers, e o manifesto identifica Ryo/Terry. O build record do hitbroad declara build, validação, boot e gameplay para ROM SHA `931d7f33…c5dca`. A observação de RAM em sessão privada confirma dano nos dois sentidos, mas a captura de screenshot e a publicação do bundle falharam; o preparo de QA nativa foi bloqueado por EIO antes de criar pedido ou worker. A medição de runtime do mesmo SHA registrou janelas de 47,3, 27,61, 29,57 e 29,90 FPS, com `fps_constante=false`; áudio e memória também seguem falsos. O simulador de agenda é apenas modelo e conserva rótulos Ken/Ryu, embora seu input esteja preso por SHA ao header Ryo/Terry. É uma base útil para integração por componentes, sem revisão visual independente nem elegibilidade de entrega.
- Reproduzi esse candidato em uma cópia temporária sem `out/`: os pre-gates passaram, 11 objetos foram compilados e o ROM de 1.900.544 bytes saiu com o mesmo SHA `931d7f33…c5dca` do registro original. A reprodução não abriu emulador nem promoveu eixos runtime; o registro e os limites estão em `candidate_repro_build_20261008.json`.
- Os arquivos de autoridade do projeto (`doc/10-memory-bank.md`, GDD, spec de cenas, TDD e plano de sessões isoladas) retornaram `EIO`; o memory bank também aparece removido no `git status`. Nenhum foi restaurado a partir de cópia histórica: clones podem conter versões antigas e não são autoridade atual.
- Há mudanças e arquivos não rastreados preexistentes em `src/`, `inc/`, `data/`, `.mddev/` e `out/`. Foram mantidos intactos. Não houve promoção, build canônico, staging, commit ou push.
- A comparação hashada das árvores `src/`, `inc/`, `tools/`, `.mddev/`, `assets/` e `data/` (excluindo caches Python) mostra 41 arquivos na rota canônica, 39 no candidato `hitbroad` e 38 em `integrada/`. Cada rota compartilha 14 caminhos com a canônica, mas nenhum dos 14 arquivos tem bytes idênticos; `hitbroad` também tem 25 arquivos exclusivos e `integrada/` tem 24. Portanto, a ROM reproduzível é uma base de evidência e seleção de componentes, não uma árvore para copiar por cima do worktree. A matriz completa com hashes por arquivo está em `route_reconciliation_20261008.json`.

## Mapa das frentes preservadas

Os clones e artefatos estão individualizados no inventário. As trilhas não devem ser achatadas em uma única sequência:

1. **Importação e semântica MUGEN:** cortes de estados de Ryo e Terry (normais, agarrões, especiais, rotas-fonte e ações únicas), AIR/identidade, perfis de input, comando v4, release temporizado, deduplicação e reparos de RAM/banco.
2. **Runtime de luta:** runtime versus orientado a dados, estado/ataque/defesa, hitbox/hurtbox, dano entre P1/P2, CPU e tratamento de projéteis. Os headers/banco do `ryo_terry_hitbroad_20261008` têm hashes idênticos ao conjunto identificado como Ryo/Terry em `ryo_terry_runtime_rom_ramfix_20261008`; há evidência de dano por leitura de RAM, mas não prova FPS estável, áudio ou release.
3. **Renderização e limites SMS:** agenda de linhas, SAT, pareamento de slots, flicker, renderização de idle/ataque e otimizações testadas/rejeitadas. `audit_row_schedule.py` registrou 17.390 pares de poses, pico de 48 sprites na SAT e 8 por scanline no candidato hitbroad anterior.
4. **Desempenho e VBlank:** estudos v089–v110 sobre custo de piso, máscaras, spill e commit de rota. v109 (`b04f30942c75de79ed70870472df62ec845a2cc01f400f96bef1db0d0ae94716`) tem medição exata da própria ROM: perfil de palco passou, `vline_min=198`, `vovf_delta=0`, frame advance em 56,2 FPS constante. É uma melhoria de linhagem de fundo anterior; não comprova a ROM atual nem está integrada ao runtime Ryo/Terry.
5. **RAM, bancos e integridade de ROM:** variantes de mapeamento, leitura/correção de bancos, perfil e vinculação dados→ROM; continuam frentes separadas que precisam de hashes/IDs compatíveis na mesma build.
6. **Áudio/PSG:** registros de autoria, binding de canal, redundância e qualidade musical devem continuar como trilha própria; eixo de áudio da ROM canônica segue sem comprovação.
7. **Evidência, sessões e aprendizado:** relatórios de probe, FPS, capturas, QA e documentação repetida entre clones ficam indexados com identidade/hash. Um snapshot histórico não passa a valer como evidência da build atual.

## Resultados de desempenho e experiências

- Em `ryo_terry_nocpu_render_attack_diag_20261008`, idle com render ficou em 42,32–44,33 FPS e sem render em 58,86–59,37 FPS; ataques foram medidos em 28,24 FPS e recuperação em 43,68 FPS. Isso sustenta a hipótese de custo alto no renderer, não atribuição exclusiva. A amostra marcou `draw_scan=53`, `schedule=1`, `emit=65` ticks e 120 ticks entre fim da lógica e fim do render.
- Fast path de pares estáveis (`drawfast`) e caminho de dirty bits (`drawdirty`) foram tentativas medidas e rejeitadas por desempenho insuficiente. Mantê-las no histórico como resultados negativos; não reintroduzir sem nova hipótese e medição.
- O protótipo `ryo_terry_sat_slots_diag_20261008` compila e passou pre-gates e 400 comparações do modelo por linha, ROM SHA `67ff3a2d7497483726558ca1240eea05ddc9c7b0b552ee0e5002a60a617a9918`. Não teve sessão de emulador isolada e seus eixos de boot/gameplay/FPS/áudio/memória permanecem falsos; não promover.
- No hitbroad, o record `hitbroad_native_qa_blocked_20261008.json` confirma que o pedido de QA por subagentes foi bloqueado antes da criação porque o memory bank canônico retornou EIO. A evidência de dano é restrita à consequência em RAM; não contar o eixo `gameplay=true` do build record como revisão independente ou aprovação visual.
- v110 tem evidência copiada/stale de ROMs v108/v109, sem medição independente do próprio SHA. Não atribuir a v110 os resultados de v109.

## Reconciliação do runtime Ryo/Ryo — 2026-10-08

A conversão limpa com o perfil `ryo_v3_runtime_cut_20261006.json` passou no self-check e reproduziu exatamente o banco de 622.592 bytes do estudo (`SHA-256 1e002a1729566132cfa1efadd77b65cc216106246671ff9db5cdcf74bf5186f2`). O schema do runtime, porém, avançou de v4 para v5: agora há 13 rotas por slot e blobs CMD v4; os manifests declaram que a tabela apenas liga padrão a estado/ação/animação e não executa predicates/efeitos CNS.

O build temporário inicial falhou porque o `fight.c` canônico não declara `AT_N` nem os campos close/far/ground-front. Um segundo probe alterou só a cópia temporária para adicionar esses campos: os sete módulos compilaram e linkaram, mas SDCC avisou que o runtime declara 12 estados enquanto cada tabela gerada contém 20; `makesms` então falhou com `Bank 1 overflow` e não produziu ROM. O C canônico também não consome `p1_source_routes`/`p2_source_routes`. O parser `input.c` aceita CMD v4; faltam integração do modelo de estados, despacho das rotas e layout de metadados bancados. Há estudo Ryo/Terry com campos/estados ampliados, mas não é substituto arquivo a arquivo. Quarenta testes focados do gerador passaram; não há ROM nem QA nativa, que permanece bloqueada pelos documentos de autoridade com EIO. Detalhes, hashes e logs em `runtime_schema_reconciliation_20261008.json`, `runtime_schema_reconciliation_build.log` e `runtime_schema_compatibility_probe_build.log`.

## Corte Ryo/Ryo no runtime bancado — 2026-10-08

A trilha separada schema v6 conseguiu empacotar o corte Ryo/Ryo no runtime bancado avançado do estudo: tiles nos bancos 2–39, descritores frame/CLSN no 40, metadata de pose em 41–42 e índice no 43. O banco integrado tem 688.128 bytes e foi confirmado byte a byte dentro da ROM no offset `0x8000`. A ROM candidata tem 720.896 bytes, SHA-256 `b5549e29368e03efe0cc3f0a280d0bd7b2c426fd84f0d2b7e92b6cac970814d4`; build e pre-gates passaram.

As poses cruas chegam a 11 peças na mesma linha. O modelo de row scheduling, com self-check aprovado, verificou 8.836 pares Ryo/Ryo nas duas paridades: SAT máxima 48 e pico 8 por scanline, com rotação de omissões sem ausência permanente. É evidência de modelo, não de framebuffer ou custo de CPU. O gate de vínculo asset→ROM ainda falha porque não há mapa; não foi feita QA no emulador, FPS, áudio ou leitura de memória. As tabelas de source routes continuam sem execução no C dessa linhagem. Pacote local em `ryo_ryo_banked_runtime_probe_20261008/`, restrito a estudo local por licença de origem não confirmada.

## Proveniência MUGEN→ROM do candidato Ryo/Ryo — 2026-10-08

O audit atual `audit_rom_asset_binding.py` exige entradas `res_path` de PNG e foi desenhado para a cadeia source→imagem em `res/`→símbolo/gerado→SHA da ROM. O importador MUGEN começa em arquivos como SFF/DEF/AIR/CMD/CNS e gera payloads bancados; inserir SFF como se fosse PNG falsificaria o contrato. A reprovação por mapa ausente identifica uma lacuna de escopo, sem invalidar a igualdade byte a byte já medida entre o banco e a ROM.

O sidecar de pacote `mugen_import_to_rom_provenance.json`, reproduzível por `verify_mugen_provenance.py`, passou 27 verificações, incluindo hashes do ZIP/perfil/manifests, 25 arquivos do runtime, 20 artefatos, quatro segmentos bancados e o offset `0x8000` na ROM `b5549e29368e03efe0cc3f0a280d0bd7b2c426fd84f0d2b7e92b6cac970814d4`. A lista de 11 membros MUGEN relevantes está hashada.

O manifest do gerador ainda omite a chave SFF e o símbolo/página por frame, então o relatório de pacote não faz essa ligação sozinho. O sidecar complementar `mugen_frame_lineage.json` passou 25 verificações e produziu 376 vínculos para os 94 frames selecionados em cada slot e suas duas variantes de paleta: AIR `(group,image)`→sprite SFF/dimensões→símbolo→banco/offset→bytes idênticos no banco integrado e na ROM. A reprodução limpa confirmou as 38 páginas e 188 macros de frame por slot. O header e manifest completos diferem porque a saída preservada usa blobs CMD v3 e a reprodução atual usa CMD v4; essa diferença de runtime foi registrada separadamente, sem confundi-la com os bytes dos tiles. O vínculo específico não aprova fidelidade visual, comportamento CMD, emulador, gameplay, FPS, áudio ou memória e continua fora do gate PNG canônico. `LMUGEN-017` registra a lacuna do contrato; `LMUGEN-018` preserva o vínculo por frame e a incompatibilidade CMD v3/v4.

## Protótipo isolado do manifest de linhagem — 2026-10-08

A primeira versão do patch calculou a identidade de origem usando o sprite já escalado por `_prepare_scene`; hash de pixels e dimensões divergiam do SFF original. O draft foi corrigido para capturar o mapa de sprites do `Character` antes da transformação. Essa ordem é necessária para que os campos chamados “source” continuem descrevendo os bytes importados.

`draft_scene_cut_lineage.py` aplica o patch só a uma cópia temporária do gerador e reproduz os dois slots. O manifest protótipo inclui AIR (ação, frame, linha e chave group/image), SFF original (índice, eixo e SHA dos pixels) e, para p1/p2, símbolo, banco, offset, tamanho e SHA do payload. A validação passou 11/11 verificações: 94 frames e 188 payloads por slot, 38 páginas reproduzidas por slot e 376 vínculos até os bytes da ROM candidata de SHA `b5549e29368e03efe0cc3f0a280d0bd7b2c426fd84f0d2b7e92b6cac970814d4`. Patch, relatório e manifest estão em `ryo_ryo_banked_runtime_probe_20261008/scene_cut_lineage_draft*`.

O draft não foi aplicado a `tools/sms_wrapper`. É prova de linhagem deste recorte, não de fidelidade visual, execução de CMD/CNS, suporte geral do importador ou comportamento em emulador. `LMUGEN-019` registra a ordem de captura e a próxima sequência de fixtures. A promoção continua aguardando os documentos de autoridade legíveis e QA nativa preparada em sessão privada.

## Self-check do contrato de linhagem — 2026-10-08

O manifest do draft agora declara `palette_variant` em cada payload e `candidate_rom_sha256`. `validate_scene_cut_lineage_manifest.py --self-check` passa no baseline e comprova quatro recusas: arquivo-fonte alterado, chave AIR sem sprite SFF, payload que ultrapassa 16 KiB e bytes de outra ROM. O validador também confere hashes do perfil/gerador/ROM, identidade AIR/SFF, dois variantes por frame, posição no banco e SHA do payload ROM. Relatório persistido em `ryo_ryo_banked_runtime_probe_20261008/scene_cut_lineage_manifest_selfcheck.json`; `LMUGEN-020` registra o aprendizado.

Essas cinco fixtures exercitam somente o contrato isolado do recorte Ryo/Ryo. Não promovem o script ao wrapper, não substituem `audit_rom_asset_binding.py` e não provam qualidade visual, gameplay, FPS, áudio ou execução no emulador. A promoção continua bloqueada pelos documentos de autoridade inacessíveis e depende da revisão apropriada.

## Proveniência por frame Terry na ROM Ryo/Terry — 2026-10-08

O slot herdado `p2_ryu` aponta para `A-Terry.def`; identidade foi conferida pelo ZIP `A-Terry.zip` (SHA `ad646be4…b085687c`). O replay correto inicia nos bancos locais 5–73. O manifesto fundido mapeia esses 69 bancos para ROM 40–108. Um teste exploratório que iniciou o gerador no banco final 40 comparou nomes locais com índices diferentes e produziu um falso alarme; `verify_terry_frame_lineage.py` fixa a distinção e reproduz os 69 bancos e 370 macros de frame.

O relatório passou 15/15 verificações. Para 185 frames AIR do Terry e duas variantes de payload por frame, ele relaciona group/image e metadados SFF, símbolo, página/offset, bytes do mapper, do banco integrado e da ROM hitbroad SHA `931d7f338205473a44387e1093bb4c0578b7e88717bc6fe7b12f97d0a59c5dca`. O mapper de cena tem 107 páginas, prefixo exato do banco integrado de 111 páginas; o banco integrado aparece sem divergência na ROM a partir do banco 2 (`0x8000`). `LMUGEN-021` registra a lição sobre bancos locais e finais.

Isso valida a linhagem byte a byte e a reprodução de bancos/macros para este corte. O header e manifest completos não precisam ser byte-idênticos para essa conclusão; o relatório registra seus hashes separadamente. Não comprova conversão visual correta, execução de CMD/CNS, gameplay ou QA atual no emulador. O relatório está em `ryo_ryo_banked_runtime_probe_20261008/terry_frame_lineage.json` e continua sidecar de curadoria.

## Rota de harmonização

1. Recuperar acesso de leitura aos documentos de autoridade sem substituir o memory bank atual por snapshots históricos; resolver a remoção registrada e verificar origem/versão.
2. Com os documentos atuais legíveis, reconciliar o worktree por arquivo e comportamento usando `route_reconciliation_20261008.json`. Selecionar componentes do candidato `ryo_terry_hitbroad_20261008` — especialmente seu `banks_integrada.bin` e headers correspondentes — e vincular por SHA cada fonte, gerador, header, banco e ROM. A reprodução limpa confirmou build e pre-gates do candidato. Não copiar a árvore inteira nem combinar os headers `versus_cut` de Ryo/Ryo com o banco cmdv4 de Ryo/Terry. Tirar `out/local_study` das dependências de compilação; manter os estudos preservados como arquivo de pesquisa.
3. Integrar em lotes pequenos as frentes independentes: importador/semântica, runtime de luta, render/SAT, performance/VBlank, ROM/bancos e PSG. Para cada lote, manter seus resultados positivos e negativos e gerar evidência fresca para a ROM exata.
4. Só atribuir o próximo número canônico depois que a rota reproduzível de build estiver autocontida no projeto e o estado exigido pelo GDD estiver definido. Rodar QA em sessão privada com contexto válido e recuperar a validação de emulador; tratar build, RAM probe, FPS, gameplay visual, áudio e memória como eixos distintos.
5. Atualizar o memory bank como última etapa da harmonização, refletindo estado medido, blockers e hashes; não declarar entrega até cumprir a regra do workspace de ROM rodando no emulador.

## Limites desta captura

Este pacote preserva texto, código, registros, alguns bancos-fonte identificados e um índice hashado abrangente. ROMs, vídeos, imagens e outros binários de saída não são duplicados no arquivo; permanecem em seus locais originais e são verificáveis pelo inventário. Se a mídia original for apagada, o hash permite detectar a perda, mas não reconstruí-la. O snapshot de documentos dentro dos clones é histórico e explicitamente não substitui documentos de autoridade.

## Linhagem conjunta Ryo/Terry na mesma ROM — 2026-10-08

O verificador `ryo_ryo_banked_runtime_probe_20261008/verify_ryo_terry_frame_lineage.py` passou 20/20 checks e reuniu as duas metades do candidato misto na mesma identidade de ROM: SHA-256 `931d7f338205473a44387e1093bb4c0578b7e88717bc6fe7b12f97d0a59c5dca`. O P1 Ryo foi reproduzido a partir do banco local 2; seus 94 frames AIR e duas variantes de paleta geram 188 payloads. Os 185 frames AIR do P2 Terry e suas variantes, 370 payloads, foram rechecados contra o mesmo SHA. O total é 558 vínculos de frame/variante, cada qual associado à identidade AIR/SFF, símbolo, banco final, offset e bytes na ROM. Os hashes atuais dos dois ZIPs, perfis e gerador também são verificados.

Essa rota Ryo/Terry fica separada da candidata Ryo/Ryo (`b5549e…814d4`); a linhagem conjunta evita misturar as duas ROMs. É prova curation-only de bytes para este recorte e não demonstra fidelidade visual, execução de CMD/CNS, gameplay, FPS, áudio, memória ou validação no emulador. QA nativa segue condicionada à leitura dos documentos de autoridade, que continuam retornando EIO. `LMUGEN-022` preserva a descoberta no ledger.

## Aditivo hashado do inventário de curadoria — 2026-10-08

A comparação do inventário recapturado (`frontier_inventory.json`, 2026-10-08T18:11:21Z) com a curadoria atual encontrou 46 itens ausentes ou alterados (43 ausentes, 3 alterados). `frontier_addendum_20261008.json` registra caminho, tamanho e SHA-256 de cada item. Os 46 arquivos estão espelhados e verificados na cópia externa.

A chamada anterior do capturador com `--help` iniciou uma nova captura porque o script não tinha parser de argumentos. O arquivo local e o inventário foram atualizados para o par de SHA `5e78b0ec…c7e21d` (arquivo) e `e8e942c7…a2dc02d2` (índice). O backup externo preservou o par original `faa02907…6bbf7` / `3c619289…084aa9`; também recebeu cópias versionadas do par recapturado: `local_study_source_and_reports_recapture_20261008.tar.gz` e `frontier_inventory_recapture_20261008.json`. Assim as duas capturas continuam identificáveis.

O capturador agora coleta recursivamente os artefatos em `changelog/curation/` e usa `argparse`: `--help` só mostra uso e `--self-check` testa a coleta em fixture temporária. Ambos passaram sem alterar o inventário ou o arquivo compactado atual. `LMUGEN-023` e `LMUGEN-024` registram a cobertura do índice e a segurança da CLI.
