# MSSF2T — análise técnica e de produto

Data: 2026-09-15. Escopo: diagnóstico e plano; nenhuma correção de runtime nesta passada.

## Conclusão

O MSSF2T é uma demonstração específica Ken × Guile com combate básico e uma boa infraestrutura externa de evidências. Ainda não é uma engine de autoria reutilizável. O obstáculo dominante é a combinação de **correção do núcleo + sincronização entre ação e imagem + capacidade de conteúdo**. Banking abre espaço de ROM, mas sozinho não resolve latência, scanlines, controle ou qualidade artística.

A HAMOOPIG oferece referências úteis de modularização, eventos e contratos; também permanece protótipo com revisão visual, audição crítica e pior-frame pendentes. Não deve ser tomada como implementação integralmente aprovada nem transplantada para Z80.

## Método e limites

Foram inspecionados os seis fontes C do SMS por inventário e os caminhos centrais de main/fight, headers, GDD, TDD, memória, especificações de banking, builders de arte, manifesto de proveniência, evidências existentes e interfaces da HAMOOPIG. Rebuild pelo wrapper: **passou**, 32.768 bytes, SHA `8a83ca2da18e2690d066cc29eed597986c97f6dd1d9af23baf204b00be8b27c4`. `_CODE`: 31.772 bytes a partir de 0x0200, fim 0x7E1C; distância até o teto local 0x7F80: **484 bytes**. `_DATA`: 702 bytes; isso não inclui uma prova de pior uso da pilha nem autoriza ocupar a região dos probes.

`reconcile_claims.py` e `audit_doc_sync.py` passaram. Os oito hashes do bundle histórico conferem com os arquivos atuais, e o hash da ROM se manteve. Isso comprova integridade do conjunto, não cobertura de todos os comportamentos. `source_audit.json` preserva a identidade das fontes. Não houve audição crítica nesta análise; presença de WAV ou percentual de sinal não prova qualidade musical. Os achados estáticos abaixo precisam de regressões executadas no alvo quando forem corrigidos.

Também foi realizada nova captura no Emulicious após o rebuild: `out/evidence/analysis_20260915.mp4`, 777 frames, 12,97 s, 256×192, quatro frames-chave com conteúdo. O instrumento registrou movimento e sinal de áudio; é uma observação curta de boot/atração, não playtest completo nem auditoria de frame time. A captura e suas limitações constam de `verificacao.json`.

As imagens históricas foram abertas: a abertura possui lutadores identificáveis, mas o cais é dominado por formas rígidas e linhas repetitivas. A captura chamada `ko_banner.png` mostra **GUILE WINS**, não o texto K.O.; ela não sustenta a afirmação documental de banner K.O. direto. Pode existir K.O. no vídeo: o frame correto deve ser localizado e registrado, sem inferir pelo nome do PNG.

## Achados prioritários

### A01 — P0: escrita além do buffer na preparação dos projéteis

`src/fight.c:88–90,530–534`: `st_buf[2][96]`, mas ambos os arrays de projéteis têm 128 bytes e os laços escrevem `st_buf[0][i]` até 127. Os 32 bytes adicionais ultrapassam o primeiro subarray, mesmo que hoje invadam a segunda linha do mesmo objeto e o boot pareça funcionar. A leitura seguinte também pede 128 bytes. Corrigir com buffer de tamanho comprovado ou upload em chunks; validar guardas, tamanhos e ROM com os dois projéteis. Não confundir ausência de crash com validade em C.

### A02 — P0: P2 perde esquerda, direita e ataques

`src/fight.c:779`: `(unsigned char)(keys & PORT_B_KEY_LEFT)` trunca 0x0100 para zero. RIGHT=0x0200, B1=0x0400 e B2=0x0800 também somem; UP=0x0040 e DOWN=0x0080 sobrevivem. Header local SMSlib, linhas 303–308, confirma as máscaras. Normalizar por comparação `!= 0` antes de estreitar ou decodificar o porto inteiro. A leitura global de 16 bits está correta, a conversão por botão não.

Além disso, `control(1, keys, 1)` sempre habilita IA: quando P2 solta o controle, a CPU volta a agir. É preciso modo explícito CPU/HUMAN/DUMMY/REPLAY; neutral humano não significa permissão para IA.

### A03 — P0: pose apresentada pode chegar depois do golpe

`request_pose`, `fight_prepare_stream`, `fight_stream`, `set_state`: a lógica ativa o soco após 4 ticks; a pose completa só aparece depois de ceil(bytes/96) uploads. Uma pose de 832–1024 bytes exige **9–11 uploads**, sem contar disputa entre lutadores. A transferência pode reiniciar quando chega outro pedido; `st_turn=who` permite que mudanças sucessivas interrompam o atendimento do outro jogador. O probe publica `P.pose`, não `cur_pose`: evidência de pose lógica não prova pose exibida.

O banco duplo evita misturar tiles de poses diferentes, mas não garante prontidão temporal. Esta é uma causa estrutural da sensação de golpe fraco/invisível. Medir tick de input, aceite, frame ativo e primeiro frame realmente apresentado. Não aumentar startup para esconder o atraso. Usar residência de frames críticos, deltas e pré-carregamento mensurado.

### A04 — P0: saturação de sprites usada como política visual

`fight_draw:1041`: projéteis entram primeiro, depois P0 e P1. O comentário assume 4+4+2 sprites/linha e deixa o VDP eliminar os excedentes. Isso não é um alocador que remove somente uma coluna previamente escolhida: favorece o primeiro lutador e pode apagar partes necessárias à leitura do segundo. Dois projéteis podem aumentar a pressão. O limite vale por linha mesmo com personagens distantes horizontalmente.

`doc/sprite_scene_golden.json` modela 8×8, enquanto o runtime usa 8×16; não inclui a matriz completa de poses, lados, saltos e projéteis. Seu PASS não fecha a cena real. Exportar a SAT efetiva, simular cada linha e criar contratos de composição que preservem corpo, mão/pé de contato e projétil. Não usar flicker como solução padrão.

### A05 — P1: resolução de contato favorece a ordem de atualização

`collide:667` resolve P0 primeiro e chama `apply_hit` imediatamente. Um hit muda P1 para ST_HIT/KO antes de avaliar seu normal; portanto trades simultâneos podem desaparecer em favor de P0. Projéteis são processados depois, inclusive após uma transição de KO, com risco de adjudicação contraditória. Primeiro coletar contatos num snapshot do tick; depois resolver dano, trade, prioridade e resultado uma única vez. Criar identidade de ataque/hit para evitar duplicata e permitir multi-hit intencional.

### A06 — P1: defesa e comando ainda são um subconjunto rígido

Soco/chute têm tempos distintos, mas chute usa POSE_PUNCH. Guarda depende de recuar, sem blockstun independente e sem regra explícita high/low; ST_GUARD usa pose agachada, mas `hurt_top` encolhe apenas ST_CROUCH. Especiais dos dois lutadores usam o mesmo QCF permissivo, detectado por baixo seguido de frente em oito amostras. Duas amostras de diagonal podem satisfazer isso. Não há timestamp por transição, consumo de comando, pressed/released ou buffer de ação separado. Durante hitstop, o retorno antecipado impede atualizar esse histórico.

Não impor que todo jogo reproduza Street Fighter. Expor regras por perfil: leniência, charge, janela de buffer, guarda, chip, ataques aéreos e cancelamentos. Defaults devem ser simples e comprovados com controles de dois botões.

### A07 — P1: resultados, empate, reset e região precisam de contrato

`next_round:878` soma vitória aos dois no empate e deriva banner de soma de vitórias; após um empate, pode anunciar ROUND3 no segundo round. `fight_update:964` fixa 60 ticks/segundo; PAL não é normalizado. TIMEUP é substituído por BN_KO quando `end_round` é chamado. `reset_positions` não limpa histórico de input; resets de partida/round devem possuir inventário explícito de timers, comandos, projéteis, guardas, stream, áudio e eventos. A IA avança sempre para a esquerda e recua para a direita, o que deixa de ser semanticamente correto após troca de lado.

### A08 — P1: pior-frame atual não sustenta os números narrados

O arquivo efetivamente selado `out/evidence/worst_frame.json` registra vline_max=254, delta=37, contador 218→255. A memória cita 247/~2700 e linha 251/262. O contador saturou: 37 é incremento observado até o teto, não total confiável da janela. O VCounter bruto tampouco deve ser confundido com índice linear de scanline sem decodificação por região.

O probe é amostrado antes de `SMS_waitForVBlank`, não depois de todas as transferências. Não prova que SAT, HUD, PSG e tiles terminaram dentro da janela segura. Substituir por medição de fases, missed VBlanks e contador sem saturação silenciosa, com leitura coerente. Testar o próprio instrumento. Não prometer DMA: o Master System não dispõe da rota DMA do Mega Drive.

### A09 — P1: proveniência contradiz a declaração de arte final

`tools/author_stage_ken.py` declara que todos os pixels são desenhados pelo script e contém retângulos, linhas e blobs; o TDD chama isso de arte autoral final. O manifesto ainda atribui o cais a outro builder. `author_native_fighters.py:61` recorta a sheet, redimensiona e quantiza seus pixels: chamar isso de guia que nunca entra na ROM é incorreto para esse caminho. Rastrear a execução/geração e o binding antes de classificar cada asset; não concluir autoria por nome do arquivo.

A diretriz local proíbe cenário final gerado por primitivas e referência restrita promovida a fonte. Preservar o baseline como estudo; reautorar os exemplos finais com fonte permitida e linhagem verificável. Nenhuma correção documental torna retroativamente autoral um pixel derivado.

### A10 — P1: banking proposto contém premissas a revisar

`doc/spec-banking.md` fala em 48 KB e abrir ~32 KB: crescer de 32 para 48 KB abre 16 KB brutos. Mistura endereço de CPU, segmento do linker e banco físico. Não adotar `BANK1=0x8400` como receita sem fixture no linker/conversor reais.

Mapear música somente antes de `PSGPlay` é insuficiente: a PSGlib local explicita que, sem MULTIBANK, o banco correto precisa estar ativo a cada `PSGFrame`. Com MULTIBANK, a biblioteca pode alterar o banco ao retornar. Código/ISR críticos devem permanecer fixos; ponteiros bancados precisam carregar banco+offset+tamanho e ter tempo de vida explícito. Reservar probes e pilha no mapa, além do BSS.

### A11 — P1: facilidade de autoria ausente

O lutador é o índice 0/1; tiles, tamanhos, metasprites, paleta, tempos, dano e cenário vivem em switches/constantes. Não há pacote declarativo de personagem, compilador de moves, validação de cronograma visual, regras desacopladas ou prova de criar segundo jogo sem editar núcleo. Extrair módulos é necessário, mas renomear funções não constitui engine orientada a conteúdo.

### A12 — P2: áudio com sinal não é mix de luta

Há BGM e SFX integrados e histórico útil de correção de canal. Contudo, o cooldown global de 20 frames pode suprimir feedback de um impacto após outro evento, e bloqueio não toca SFX por decisão de economia. Implementar prioridade por evento/canal, recuperação musical e sons distinguíveis para hit, block, whiff, especial, KO e interface. Não exigir 100% de atividade como critério artístico: silêncio e dinâmica podem ser intencionais. Ouvir BGM isolada, SFX isolados e combate pesado com música, nos dois padrões regionais suportados.

## Comparação com HAMOOPIG

| Eixo | Referência observada no Mega Drive | Tradução adequada ao SMS |
|---|---|---|
| Sistemas | headers de input, física, colisão, cenas, configuração | módulos pequenos C; buffers fixos; medir custo de chamada/estado |
| Eventos | `inc/combat_event.h`: evento com origem, instância, tick e consumo | fila fixa compacta; resolução simétrica; HUD/áudio consomem evento |
| Cenários | `inc/stage.h`: StageDefinition e contrato de câmera | StageDef para uma tilemap, bandas raster opcionais e paletas compartilhadas |
| Roster | tabelas Ken/Musgo e seleção | FighterDef com dados compilados e registro; sem branch por personagem no núcleo |
| QA | testes de reset, matriz de casos, probes, identidade da ROM | replay determinístico Z80, SAT real, instrumentação por fase, captura Emulicious |
| Estado | memória atual declara cobertura parcial e bloqueios | preservar honestidade; não usar suas pendências como padrão de aprovação |

O HUD em sprites do Mega Drive, DMA, múltiplos planos e XGM não são soluções transportáveis. Manter HUD em BG, PSG como base e o custo real de CPU/VRAM do SMS.

## Veredito nos sete eixos

| Eixo | Resultado desta análise |
|---|---|
| Build | rebuild confirmado, mesma SHA, 32 KB |
| Validation report | gates existentes passam; há lacunas semânticas demonstradas |
| Boot | evidência histórica íntegra; nova tentativa registrada em `verificacao.json` |
| Gameplay | histórico prova subconjunto de 1P; engine 2P/completa não comprovada; defeitos estáticos |
| Performance | insuficiente: instrumento parcial/saturado e sem fechamento de transferências |
| Áudio | arquivo íntegro e integração no código; qualidade auditiva não avaliada |
| Memória | existente, mas números/claims requerem reconciliação; não sobrescrita nesta auditoria |

## Referências técnicas externas consultadas

Headers locais são a autoridade de implementação; upstream serve para conferir intenção e contexto:

- [SMSlib — header do projeto](https://github.com/sverx/devkitSMS/blob/master/SMSlib/src/SMSlib.h): input e macros de mapper.
- [PSGlib — contrato de banking](https://github.com/sverx/devkitSMS/blob/master/PSGlib/src/PSGlib.h): atualização de música e banco ativo.
- [Documentação oficial Sega preservada no SMS Power](https://www.smspower.org/Development/SMSOfficialDocs): documentação primária de hardware. O plano deve fixar modo/região antes de traduzir números em gates.

Próximos passos e metas: `plano.md`. Prompt de execução: `prompt_agente.md`.
