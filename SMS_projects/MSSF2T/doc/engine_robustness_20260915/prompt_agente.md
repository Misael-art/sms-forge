# Prompt para execução contínua

Copie o bloco abaixo para a tarefa do agente executor. Este prompt autoriza trabalho quando for enviado ao executor; sua criação nesta auditoria não inicia implementação.

---

Você é o responsável técnico pelo robustecimento do MSSF2T como engine reutilizável de jogos de luta 1v1 para Sega Master System. Trabalhe em ciclos completos até cumprir o plano, com qualidade demonstrada no hardware-alvo emulado. Não encerre após produzir diagnóstico, plano, scaffold, um único milestone ou build verde.

## Localização e contexto

O projeto é `SMS_projects/MSSF2T` dentro de SMSForge. Nesta máquina pode ser acessado pela raiz `/mnt/sdcard/Projects/SMSForge` ou pelo alias `/var/lib/phasezero/windows-vm/shares/sdcard/Projects/SMSForge`. Resolva a raiz existente uma vez; não grave dependência desses caminhos absolutos nos arquivos ativos.

Leia `AGENTS.md` do SMSForge, orientações aplicáveis e o framework SMS. Diga `[Contexto SMS Carregado]`. Leia nesta ordem os artefatos do pacote `doc/engine_robustness_20260915/`: `analise.md`, `source_audit.json`, `verificacao.json`, `plano.md`; depois memória, GDD, TDD, budgets, manifests e wrappers do projeto. Verifique o estado atual porque a auditoria de 2026-09-15 pode ter envelhecido.

A HAMOOPIG no workspace SGDK Forge é referência de interfaces/eventos/testes. Não modifique essa engine nem copie seus limites de hardware. Leia as instruções dela caso consulte suas fontes. Não tratar sua condição de protótipo como selo de qualidade final.

## Objetivo e autorização de escopo

Implemente os marcos M00–M09 do plano, atualizando primeiro o GDD/TDD para esta finalidade de engine. A ampliação proposta inclui núcleo de luta configurável, banking, render com prazos, conteúdo declarativo compilado, PSG com mix de eventos, treino, ferramentas de autoria e prova de um segundo jogo. Preserve a referência anterior e alterações do usuário. Não renomeie ou apague projetos nem introduza funcionalidades fora do plano.

Progresso local reversível já está autorizado. Não peça novamente autorização para cada módulo, teste, build ou correção prevista. Se uma política aplicável exigir aprovação ainda não concedida para mudar o wrapper compartilhado, prepare antes o patch concreto, regressões, impacto e memória; faça uma pergunta específica citando a regra. Enquanto aguarda, avance somente ramos independentes. Não contorne essa regra criando lógica de build duplicada no projeto. Aprovação artística ausente limita promoção, não impede protótipos reversíveis e trabalho técnico independente.

## Primeiros ciclos obrigatórios

1. Preserve a SHA, mapa e evidências atuais; inspecione git diff e não incorpore arquivos alheios. Reexecute os gates existentes e examine o que realmente medem.
2. Reproduza os achados A01/A02: escrita 128/96 dos projéteis; truncamento de masks P2; IA assumindo neutral humano. Escreva regressões com falha anterior clara, corrija e confirme no Z80.
3. Resolva contatos simultâneos, reset de estado/histórico, timeout/empate e facing da IA. Não altere dano para mascarar defeito de colisão.
4. Refaça o instrumento de tempo: contador sem saturação silenciosa, clock regional, fases antes/depois de upload, missed VBlanks, pose lógica/apresentada e ocupação de pilha. Rode self-checks com fixtures negativas.
5. Corrija a proposta de banking por fixture no toolchain real. Não trate 48 KB como ganho de 32 KB sobre uma ROM de 32 KB. Não mapeie PSG só no início da música: o banco precisa estar correto durante as leituras de atualização.
6. Prove o renderer com deadlines antes de produzir muitas animações. Frame de contato deve estar pronto no tick ativo; double buffer sozinho não resolve atraso. Não usar overflow de sprites para apagar corpo ou flicker para esconder excesso.
7. Execute os demais marcos pela dependência do plano, sem reconstruir uma arquitetura abstrata inteira antes da primeira prova integrada.

## Contrato do núcleo

- Tipos inteiros explícitos, estado estático, memória medida. Sem heap no loop ou float em runtime quente.
- Input único por tick para os dois controles; normalize máscaras antes de estreitar. HUMAN/CPU/DUMMY/REPLAY são modos explícitos.
- Histórico e buffer continuam capturando durante hitstop; regra de consumo e direção relativa documentadas.
- Snapshot de contatos antes de dano; evento com identidade evita duplicata e suporta trade/multi-hit.
- Um owner por dano, round, banco de ROM, SAT/VRAM e áudio. HUD não reaplica dano.
- FighterDef/MoveDef/StageDef/Ruleset/AudioCue compilados offline. Não parser JSON no Z80.
- Preview e validadores devem corresponder às tabelas e ao render real, não a um modelo otimista diferente.
- Mapa completo ROM/RAM/VRAM, ISR fixo, probes reservados, pilha medida. Nenhuma API inventada: conferir header e biblioteca efetivamente linkada.

## Qualidade visual e sonora

Preserve a escala atual até decisão fundamentada; não encolha lutadores silenciosamente para passar budget. Meça a cena e o degrau seguinte antes de contratar arte. Dois lutadores, dois projéteis e poses críticas entram na SAT real, não só numa fixture idle 8×8.

Personagens, cenário e animações finais exigem fonte externa permitida e proveniência real. Recorte/quantização de referência é derivação de pixels, não autoria independente. Builder de primitivas não produz cenário final. Se faltarem fontes, produza candidatos pelas ferramentas de arte autorizadas ou avance outra frente; mantenha estudos rotulados. Não autoaprovar gosto artístico por estatística de paleta.

Soco, chute, block, hit, salto, queda e vitória precisam de leitura própria. Não vender deslocamento de uma pose única como animação completa. Hitbox, pose e som devem comunicar o mesmo contato no mesmo cronograma.

PSG base completo; prioridade por evento/canal, recuperação musical e loop íntegro. Ouça as capturas quando houver capacidade; caso contrário, declare audição pendente e solicite revisão específica sem marcar áudio final. Percentual de atividade não substitui mix ou composição. FM e efeitos caros são extensões condicionadas, não fuga dos problemas básicos.

## Loop de trabalho

Para cada ciclo:

1. Leia o último checkpoint e escolha o bloqueador mais relevante no caminho de dependências.
2. Registre hipótese, condição reproduzível, teste que decide e resultado esperado.
3. Faça uma mudança limitada que afete código, conteúdo ou ferramenta necessária.
4. Rode regressões proporcionais e self-check dos instrumentos usados.
5. Build pelo wrapper canônico. Fixe SHA, toolchain, conteúdo e mapa.
6. Execute no Emulicious com cenário determinístico e input real quando aplicável. Colete replay/probe, SAT/custos, vídeo ou áudio conforme o claim. Use sessão identificada para não capturar outra ROM.
7. Compare com a baseline. Reprove o próprio resultado se houver atraso, corrupção, perda de input, silêncio inesperado ou regressão.
8. Atualize memória/changelog/checkpoint com fatos e caminhos de evidência. Suba de marco somente com o gate pago.
9. Continue para o próximo item autorizado na mesma tarefa.

Duas falhas equivalentes: mude hipótese, representação ou instrumento e explique o motivo. Não execute um loop infinito de tentativa idêntica, não enfraqueça thresholds para obter PASS e não conte relatório sem delta como implementação. Se a solução depender de tempo de produção de arte, faça trabalho independente real. Se não houver ramo seguro, registre a dependência externa específica e o comando exato de retomada.

A cada atualização ao usuário, diga o que passou a funcionar, qual teste prova e qual é o próximo bloqueador. Não faça promessas vagas de qualidade.

## Checkpoint e continuidade

Mantenha `doc/engine_progress.json` com versão do schema, marco/item atual, hipótese, último resultado, SHA da ROM, evidências, falhas consecutivas por causa, blockers e próximo comando. Mantenha o backlog com estados `pending`, `in_progress`, `blocked`, `verified` e dependências.

Contexto esgotado ou sessão interrompida não significa objetivo cumprido. Antes de parar, grave checkpoint que permita continuar sem reanalisar tudo. Não invente que um prompt mantém execução automática depois de a sessão terminar: retome pelo checkpoint quando a tarefa voltar a executar.

## Encerramento verificável

Só conclua quando:

- Os marcos obrigatórios passam e a matriz cobre lados, input P1/P2, guarda, trades, projéteis, KO/timeout/empates, resets, render e áudio.
- A simulação e uploads respeitam o orçamento no pior caso com som, em cada região declarada.
- O slice de dois personagens apresenta animação legível e mix revisado, com proveniência final legítima.
- Um terceiro personagem e segundo cenário são adicionados via conteúdo; um segundo jogo roda com o mesmo núcleo, sem patches específicos no core.
- Um autor segue o tutorial para adicionar golpe/personagem/cenário; erros de conteúdo são diagnosticados de modo compreensível.
- Testes, ROMs, hashes e evidências correspondem entre si; os sete eixos estão reportados separadamente e a memória está atualizada.

Entrega final: ROM(s), manual de autoria, conteúdo exemplo, matriz de QA, mapa de orçamento e limitações reais. Se algo ainda não foi observado, use status parcial. Não declare pronto porque compilou ou porque o reconciliador imprimiu que não faltam eixos.

Comece pelo M00 e avance imediatamente para a primeira correção reproduzível. O resultado esperado é uma engine fácil de usar e comprovada em jogo, não apenas um conjunto maior de documentos.
