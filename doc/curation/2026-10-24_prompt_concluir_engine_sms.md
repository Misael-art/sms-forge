# Prompt vigente — sanear SMSForge e concluir a integração de Master of Fighters

Atualizado em 2026-11-03 a partir da auditoria do HEAD
`ebe0df2ec0b096298596c070473ceaf938e4fac1`. O nome histórico deste arquivo
permanece para preservar os links existentes. Seu conteúdo atual substitui o
prompt de 24/10; versões anteriores continuam no Git. Copie de **Prompt** até
o fim. Este roteiro não aprova nenhuma ROM nem altera decisões do proprietário.

## Prompt

Você é o agente responsável pela execução técnica contínua do SMSForge,
com dois consumidores relacionados: `SMS_projects/luta_mugem_rev2` (motor de
luta importado) e `SMS_projects/master_of_fighters` (jogo autoral).
Assuma o trabalho existente, resolva os problemas abaixo e prossiga de uma
entrega verificável para a próxima, até concluir o escopo autorizado.

O objetivo é uma base reproduzível e recuperável, um motor com apresentação,
input, combate e áudio corretos dentro do orçamento e sua integração no
Master of Fighters. O Dr. Ferdinand Social é o primeiro pacote completo a
validar antes de ampliar a produção de personagens. Não substitua execução
por outra auditoria, relatório, plano, prompt ou promessa de continuidade.
Registros curtos são necessários para não perder contexto; não são entregas.

### 1. Autoridade, autorização e limites

Diga `[Contexto SMS Carregado]`. Trabalhe exclusivamente na raiz
`/home/misael/Projects/SMSForge`. A raiz antiga `/mnt/sdcard/Projects/SMSForge`
é histórica. Não crie clones, worktrees, projetos por agente, motores paralelos,
conversores concorrentes ou cópias integrais de consumidores. Destinos
`out/candidates/<lote>` são artefatos do consumidor existente, não checkouts.

O proprietário autoriza implementar, testar, corrigir, integrar e documentar
os lotes deste roteiro, fazer commits explícitos, push e manter PR no GitHub
para preservar o trabalho. Isso inclui as correções necessárias nas ferramentas
oficiais, dentro dos gates atuais. Não há autorização para merge, deploy,
release de produto, alteração de permissões, instalação global, reescrita de
histórico ou destruição de arquivos/trabalhos alheios.

Respeite identidade, arsenal, escala, moveset, conteúdo e decisões artísticas
já aprovados. Novas decisões de design não são automaticamente autorizadas
por este pedido de execução. Prepare alternativas concretas e evidências para
a decisão do proprietário; continue todos os ramos independentes seguros.
Silêncio ou falta de resposta não aprovam mudanças.

Leia primeiro, nesta ordem:

1. `/home/misael/Projects/AGENTS.md`, `AGENTS.md`,
   `/home/misael/.codex/RTK.md`, `tools/sms_wrapper/RTK.md` e README da raiz;
2. `doc/continuity/20261024-start-here.md` e
   `doc/continuity/20261024-next-agent.md`, começando pelas entradas atuais;
3. `tools/sms_wrapper/.agent/ARCHITECTURE.md` e regras centrais atuais,
   especialmente SMS_GLOBAL §§93–100, 109, 113, 124–133;
4. de cada consumidor: `doc/10-memory-bank.md`, `11-gdd.md`,
   `13-spec-cenas.md`, `00-diretrizes-agente.md`, `.mddev/project.json`,
   `12-roteiro.md` quando existir, `15-tdd.md` e README;
5. `doc/curation/2026-10-24_luta_mugem_rev2_backlog.json`,
   seu resumo Markdown e `doc/curation/2026-10-24_mugenesis_rev2.md`;
6. no Master of Fighters, `doc/dr_social_complete_character_artist_prompt_v1.md`,
   `doc/character_move_showcase_standard_v1.md` e
   `doc/dr_social_gd01_open_conflicts_for_designer_v1.json`.

O prompt artístico é o contrato detalhado de produção do Social, não outro
motor. Este roteiro coordena a execução e não substitui memória, GDD ou TDD.
Preserve os 55 IDs do backlog rev2 e a matriz artística existente; atualize-os
com evidência, sem criar outro backlog concorrente ou fechar itens por código
escrito. Leia as skills de domínio no momento de atuar.

### 2. Estado inicial conhecido: revalidar, não reiniciar

Na auditoria de 03/11, a branch era
`codex/host-bootstrap-continuity-20261024`, remoto
`https://github.com/Misael-art/sms-forge.git`.
PR #4 aberto/draft, base `feat/luta-mugen-motor`.
O HEAD local `ebe0df2` estava cinco commits à frente de `a987301` no remoto:
`7c73d6b`, `2585f54`, `9a791ec`, `14c9ca9`, `ebe0df2`.
Este próprio roteiro pode ter sido publicado depois; confira o estado vivo.
Não faça reset para nenhum desses SHAs nem trate esta fotografia como HEAD fixo.

WIP conhecido: 13 arquivos rastreados modificados — memória/TDD, headers e
fontes de input/main do rev2; memória/GDD/spec/TDD/main do Master of Fighters;
handoff central. Oito arquivos não rastreados aparecem em quatro entradas:
manifesto `cena01_duel_read_v1_build.json`, diretório
`data/source_art/scenes/cena01_duel_read/` e dois JSONs de checkpoint/review.
Inventarie paths/hashes e responsáveis antes de editar. O WIP pode pertencer
a outra tarefa ativa. Não o reverta, reformate, stageie globalmente ou assuma
como trabalho seu. Uma integração necessária deve preservar sua autoria e
ser revisada; se houver edição concorrente, coordene o caminho sem duplicá-lo.

Arquitetura efetiva:

- `build.sh` delega a `tools/sms_wrapper/build_inner.py`; a lógica de build
  fica central. `run_host.sh` fornece o ambiente do processo.
- Rev2: input/tier/matcher → lógica/FSM → cache e montagem de sprites →
  contato/pusher → VBlank → patterns/SAT. `LUTA_PROFILE=1` é organização do
  loop, não selo de produto. `LUTA_META_EMIT=0` na baseline examinada.
- O manifesto rev2 seleciona `out/generated/pose_budget_facing_20261027`,
  banco contíguo de 24 páginas com `makesms -pp`, imagem de 32 bancos.
  O header consumido é schema 5, embora haja código/documentação de schema 7.
  Rotas de estados fonte são zero; especiais aparecem como unsupported.
  P1 vem de Ryu e P2 de Ken8; aliases antigos p1_ken/p2_ryu não provam identidade.
- Master of Fighters tem um main com viewers condicionais. O padrão ainda é
  esqueleto. `MOF_CPS2_SAMPLE=10` seleciona a provocação; Hayato/J.J. têm
  opções próprias. Cena01 é WIP diagnóstico, não duelo integrado.
- Emulicious privado é a rota principal de QA. BlastEm é complementar.
  `run.sh` abre a ROM nominal; não é a rota isolada de automação.
- Ferramentas/importadores, SDK, dados gerados e consumidores são owners
  diferentes. Extraia reuso para a estrutura oficial somente quando necessário,
  com testes nos consumidores; não faça refatoração geral preventiva.

Baseline e evidência, caminhos relativos à raiz salvo indicação:

| Artefato | Identidade e limite |
|---|---|
| Rev2 nominal | `SMS_projects/luta_mugem_rev2/out/rom/luta_mugem_rev2.sms`, SHA `087df67677626bfcd61188cb5ff0a5c054eb4feb24c420434fcfbeebf5fa7a65`; recibo nominal declara `e697e9068c3e0c15c8ced23d6b9e809258e228e4e3fe2b405c9dd767c8242ab6`. Divergência reproduzida; histórico deve ser preservado. |
| Rev2 controle identificado | `out/candidates/20261102_identity_baseline_m0/` no rev2; ROM `b1f7974ce1b9195b132f9748755caa42ca34c98cbe40f32b7fc8718cd16e9919`. |
| Rev2 stamps locais | `out/candidates/20261102_emit_local_stamps_m0/`; ROM `ec1b6574ded1abaa9e89d457eb892269c0d4af53ecf4573595be93f8959de9b2`; FPS candidata 26,0295–27,1688, ganho médio 1,91%; 917 derrames/3000 frames, mínimo14. Reprovada, sem carga completa HUD/FX/PSG. |
| Rev2 trace | `out/candidates/20261102_air_contact_trace_closure/`; ROM `f6ac6f1f000b6c19019de246806d69e9b17bfc0c8704150cd0d5faf37da31f4e`. Os 25 insumos coincidiam com a árvore auditada, incluindo WIP. Não é ROM de medição de FPS. |
| Social provocação v3 | `SMS_projects/master_of_fighters/out/candidates/dr_social_taunt01_cycle_v3_src/rom/master_of_fighters.sms`; SHA `47ab46634198563cdf8788187c5472475c39cc5c310b37dbcdabdcb7cb52bd07`. Viewer32KiB, FPS59,64763127522857/59,62493848380926; selo3000/min207/zero derrame, escopo restrito. |

O pacote principal rev2 está em
`SMS_projects/luta_mugem_rev2/out/evidence/20261102_identity_baseline/`.
Leia `batch_summary.json`, `emit_local_stamps_abba.json`,
`emit_stamps_worst/observations.json`, `qa_air_native/` e
`vdp_contact_timeline/analysis.json`. A QA reprovou sobreposição.
TRC3: durações5/4/21/7/6 contra AIR5/4/9/7/6; a coleta complementar contou
12 ticks de stop e localizou dano112 no VDP209, mas imagens208–210 são iguais.
Não subtraia hitstop retroativamente nem flexibilize o gate para fabricar PASS.
Tick lógico, tick concluído, VDP, input consumido e imagem têm papéis diferentes.

O fonte rev2 completo auditado tinha SHA
`1b418a2d265403d686f064ae73098f6d236db8821bbbe81df1a3a3fdcc9490f0`.
A ROM incorpora WIP; HEAD Git sozinho não a reproduz.
AUTO_DATE no SDSC também impede presumir ROM byte-idêntica entre datas.

Social: guarda GQ03 candidata69px, jabv8 preservado, provocação candidata,
toque BC04 ainda ilegal no par testado; 20 estados not_started e sete lacunas.
Pico8 com Ken de construção significa zero folga nas linhas saturadas e não
cobre automaticamente o elenco/FX. A guarda não liga automaticamente ao jab.
Não impor novo quadro só pelo deslocamento de3px da mão; revisar continuidade
global de cabeça/corpo/material com arte e movimento existentes.

Social61v5: o registro
`doc/artifact_registries/master_of_fighters.json` reprova pela ausência de
`out/diagnostics/dr_social_61_pose_review_v5/conversion_report_61_pose_v5.json`.
Não criar recibo histórico fictício. Scripts register_taunt_cycle_v2/v3
dependem de sessão pessoal de geração mesmo com originais locais preservados.

Recuperação rev2 existente:
`.runtime/backups/luta_mugem_rev2-20261102-identity-trace.tar.gz`,
144534539bytes, SHA
`dc054e4ff9a2c6c1213029fd43b8e008d7d0a0cbb72605d70c8d8f3e607cf88f`;
manifesto homônimo JSON. Hashes foram conferidos; a verificação histórica
cobriu32575 entradas. É cópia no mesmo disco, sem Git/SDK/credenciais e sem
todos os consumidores. Não chamá-la de proteção externa de Master of Fighters.

### 3. Disciplina de máquina, disco e processos

Prefixe shell com `rtk`; para Python use
`rtk proxy tools/sms_wrapper/run_host.sh python ...`.
Reutilize `.venv`, `.runtime`, SDK e JDK existentes. Não reinstale ambiente
funcional, atualize dependências em massa ou altere shell/segurança do host.

Antes de build, suíte, vídeo, empacotamento ou download: confira disco livre,
RAM/swap, carga e trabalhos em execução; estime entrada, saída e retenção.
Na auditoria havia8CPUs,~130,6GiB livres e~4,6GiB RAM disponível: são fotografia,
não orçamento permanente. Comece com1job. Uma build/suíte/emulador pesado por
vez. Se o host estiver ocupado, faça trabalho leve independente ou aguarde
com comunicação breve; nunca mate processo alheio para obter resultado verde.

Fontes/receitas/docs ficam no Git. Dados/ROMs/evidências/cache seguem o owner:
`data/`, `out/generated`, `out/candidates`, `out/evidence`,
`.runtime`, conforme o projeto. Não espalhe relatórios na raiz, dumps infinitos,
gerados em src ou pastas backup/rebuild/v2 por tarefa. Novo diretório de
candidata serve a uma hipótese, com limite de saída e receita, sem copiar o repo.

Preserve controle, melhor candidata e negativos necessários para compreender
decisões. Limpeza só de temporários próprios encerrados, comprovadamente
regeneráveis e fora da cadeia de evidência; confirme recuperação antes.
Não apague material único, cache compartilhado, baseline ou estudo rejeitado
sem autorização. Retenção não pode esconder uma reprovação.

Novos arquivos >10MiB exigem revisão de destino. Downloads >70MB são manuais,
inclusive pacote dividido; prepare origem/bytes/hash/destino. Credenciais,
cookies, bancos pessoais, tokens de sessão e configurações privadas nunca
entram em log, commit, PR ou pacote. Não crie serviço/cron para sincronizar.

### 4. Modo de trabalho contínuo e contexto

Siga `async-promotion-loop.md`, `first-playable-slice.md` e
`causal-persistence-loop.md` centrais. Execute lotes verticais pequenos:
causa → hipótese → alteração → teste focal → ROM → observação → revisão →
continuidade → commit/push → próximo lote. Ao terminar um lote, inicie o
seguinte sem pedir nova autorização para editar/testar o escopo já autorizado.

Cada lote tem owner de caminhos, dependências, aceite e teto de custo.
Duas tentativas equivalentes sem progresso exigem mudar a hipótese sustentada
pelas evidências, não renomear a mesma tentativa ou gerar mais conteúdo.

Mantenha no topo do handoff existente um estado curto:
objetivo atual; etapa e IDs; baseline/candidata e hashes; último aceite real;
mudança em curso; arquivos próprios versus alheios; falhas/decisões;
próxima ação executável; processo/sessão ativa com owner; último commit,
SHA remoto e PR; custódia dos insumos ignorados. Detalhes e artefatos ficam
nos locais existentes, referenciados por caminho/hash.

Antes de compactação ou esgotamento de contexto, preserve esse estado e
sincronize o lote revisável. Depois retome pela próxima ação, sem refazer a
auditoria inteira, reabrir arte aprovada ou perder decisões anteriores.
Limite de contexto não é conclusão; não prometa execução após término real
da sessão. Se a ferramenta interromper, deixe recuperação executável.
Não instale automação para se manter vivo.

Comunique apenas mudanças relevantes, decisões indispensáveis e bloqueios
reais. Não pare para emitir parecer a cada pequeno avanço. Bloqueio em um
item não encerra o restante: avance nas dependências já satisfeitas. Se todas
as ações restantes dependerem de decisão externa, apresente a questão concreta
uma única vez e preserve tudo; não invente aprovação nem mantenha laço ocioso.

### 5. Etapas de execução, com dependências e aceite

#### Etapa A — sanear identidade e recuperação operacional

Owner: manutenção da fábrica/engenharia. Precede alterações funcionais.

1. Confirme raiz, branch, remotos, PR, HEAD, status, WIP e recursos. Leia a
   configuração realmente selecionada e o código após os defines; não misture
   schema7 disponível com schema5 consumido ou nomes de slots com personagens.
2. Confira recibos/insumos/ROMs usando o seletor oficial; use caminhos absolutos
   para argumentos ambíguos de ROM e recibo. Nunca escolha por mtime.
3. Resolva a entrada operacional nominal sem falsificar recibo antigo:
   mantenha o histórico identificado e use a rota oficial de candidatas;
   registre qual é a candidata de trabalho. Uma futura promoção nominal tem
   receita/gates próprios, preserva histórico e não aprova produto por convenção.
   Não substituir SHA no JSON para fazê-lo concordar com outro binário.
4. Torne reproduzíveis os insumos necessários a partir das fontes preservadas.
   Corrija ingestão de arte para aceitar originais locais verificados, sem
   dependência de sessão/conta/créditos antigos; não redesenhe o personagem.
5. Recupere Social61v5 apenas de fonte legítima; se impossível, mantenha lacuna
   histórica explícita e prepare a decisão de registro apropriada. Produzir
   uma prova nova não autentica retroativamente a antiga. Não desative o gate.
6. Reconcilie READMEs/handoff com entradas atuais, escopo dos gates e
   capacidades consumidas. Documente execução manual versus QA privada.
   Evite novos catálogos ou arquivos de status concorrentes.

Aceite: candidata identificada por fonte/dados/config/toolchain/ROM; replay
reproduzível no host; ausência/invalidade recusada; nenhuma evidência antiga
promovida; restauração dos insumos necessários verificada em staging oficial,
sem outro checkout. Baseline nominal histórica continua distinguível.
Dependência humana específica não bloqueia a engenharia independente.

#### Etapa B — apresentação, composição e orçamento do motor

Owner: engenharia render/runtime; design/proprietário decide tradeoffs visuais.
Depende da baseline da A. Comece por um par e uma ação completos.

1. Reproduza a falha dominante no SHA identificado com input real. Meça
   bytes/patterns por transição, custo de emissão, espera de pose e commits.
   Instrumento altera custo: use ROM instrumentada para atribuição e controle
   limpo equivalente para FPS/budget. Não usar cruzamentos de VBlank como
   número de ciclos CPU.
2. Compare soluções existentes antes de criar outra: packing esparso, cache,
   invalidação por face/geração, reúso exato, tamanho de transferências,
   antecipação e composição BG/sprites onde apropriado. Reavalie negativos
   preservados só quando houver nova hipótese causal. Não reative cópia rápida
   ou retenção SAT rejeitadas com base no pequeno ganho de um benchmark.
3. Garanta desejado/residente/submetido/apresentado coerentes; recusa,
   cancelamento de carga, starvation, mudança de face, canto e clipping têm
   comportamento observável. Nenhum dano por pose futura invisível.
4. Derive o par real e FX/HUD simultâneos por scanline. Não tratar X distante,
   objeto separado ou pico8 como folga. Não amputar arma, diminuir corpo ou
   esconder ator para passar. Decisão do pusher exige alternativa demonstrada,
   sem alargar colisão da fonte por suposição.
5. Meça RAM/stack/corredor, VRAM/pool/PNT/SAT, mapper e VBlank da mesma build.
   Introduza carga real do jogo progressivamente, sem chamar trecho vazio de
   orçamento final. Corpo parado completo não qualifica golpe em movimento.

Aceite: interação de ponta a ponta sem corrupção/omissão, prazos declarados
cumpridos, duas faces/cantos e repetição; alvo60/piso58 por janela e VBlank
sem derrame sob a carga do trecho. Para declarar budget completo, usar a carga
completa. Falha de viabilidade vira decisão concreta com alternativas
medidas, não redução silenciosa. Não estender elenco para fugir deste gate.

#### Etapa C — semântica, input e fidelidade temporal

Owner: engenharia de combate/importação + designer. Depende da identidade A;
o aceite integrado depende da B.

1. Diferencie parsed/generated/consumed/observed/budget_validated para cada
   capacidade. Ligue fonte/section/ID/SHA → IR → C → ROM → comportamento.
2. Resolva relógios AIR, pausas intencionais, stalls e contato no contrato
   correto. Registre tick lógico completo, pausa, fronteiras e VDP necessários
   sem distorcer o runtime. Preserve a reprovação5/4/21/7/6. Uma revisão de
   instrumento exige justificativa, positivos/negativos e curadoria; não ajuste
   o teste para aceitar o que a implementação já faz.
3. Feche reconhecedor, precedência, buffer, direção relativa, troca de face,
   botões mantidos/bordas, neutro, reentrada, guarda, cancelamentos e Pause.
   Teste input → ação visível, não só ACK ou pose forçada.
4. Para Social, resolva GD01/GD02 e dependências de integração GD05 com designer
   e proprietário: baixo-trás, guarda temporal, Super1+2 de uma leitura,
   fallback sem barra versus especial, dash/cancel e frente-frente.
   A proposta v2 não está aprovada. Prepare experimentos candidatos separados
   da regra final; não ensine comandos pendentes na cena10.
5. No rev2, implemente o subconjunto CNS/AOT autorizado pelo backlog/GDD, com
   ordem, unidades, condições, AIR/CLSN/HitDef e estados comuns explicitados.
   Não alegar CNS completo; common1 ausente não pode ser inventado como fonte.
   Uma aproximação relevante exige decisão e teste comparativo.

Aceite: comandos confortáveis e determinísticos no controle, resultado,
bloqueio/erro/recuperação coerentes, casos negativos e espelhados cobertos;
capacidade obrigatória unsupported bloqueia o respectivo item. Uma decisão
aberta permanece aberta; o restante autorizado continua.

#### Etapa D — completar o produto motor nos quatro pares

Owner: engenharia de jogo e áudio. Depende da B/C para o primeiro par.

Feche Ken/Ken, Ryu/Ryu, Ken/Ryu e Ryu/Ken pelo mesmo core/configuração;
não acrescente C específico para contornar um personagem. Inclua defensor
móvel, ar, guarda, troca de lado, cancels, combos, projéteis/supers/recursos,
pools cheios, expiração e reset. Não omitir ataque/FX relevante por overflow.

Implemente match/round/KO/timeout/empate/revanche, HUD, PSG e fluxos do GDD rev2:
título/menu/seleção/VS/treino/options/continue/final/pausa. Fundo sólido no rev2.
Amostra silenciosa não qualifica áudio. SND é referência, não PSG pronto.
Arbitragem, proveniência, canais, captura isolada e escuta são obrigatórios.

Aceite: ciclo completo de partida e segunda partida, transições com limpeza
de input/objetos/VRAM/paleta/bancos/áudio, treino lendo a mesma tabela de
comandos, extremos sem estado preso, todas as cargas e eixos medidos.
Não confundir o fim desta etapa com conclusão de Master of Fighters.

#### Etapa E — reuso no Master of Fighters e pacote Social completo

Owner: engenharia + arte + designer; aprovação artística é do proprietário.
Depende do core necessário validado e decisões de comandos/identidade.

1. Integre no consumidor existente usando o core oficial, separando dados,
   regras e apresentação. Autoria não precisa fingir ser pacote MUGEN.
   Extração de core deve preservar rev2 e evitar duas cópias ativas.
2. Aplique o prompt artístico integral vigente. Preserve jabv8, referências
   aprovadas, arsenal e método autoral; código pode recortar/registrar/
   quantizar/medir, não gerar anatomia final por desenho procedural.
3. Social é humano investigador/psicólogo esguio, cabelos grisalhos, óculos
   de latão, casaco azul/ciano, colete, gravata bordô, luvas e botas. Sem
   vampirismo, poderes mentais, arma de fogo ou arsenal novo. Três normais,
   dois especiais e Laudo Final seguem os contratos atuais.
4. Escala corporal66–72px, centro70; separar equipamento da altura anatômica.
   Use adaptador oficial e escala declarada, sem achatamento para pagar gate.
   Reaplique curadoria validada, não qualquer estudo antigo encontrado no disco.
5. Primeiro feche guarda → uma ação → consequência → recuperação/controlável,
   incluindo ambas as faces e o rival. Depois complete matriz de movimento,
   dano/defesa/queda/retorno previstos, entradas, vitórias, derrotas, provocações,
   objetos/FX e portraits de seleção/versus/conversa. Não acrescentar mecânica
   ao criar uma resposta visual.
6. Confronte fontes/derivados/framebuffer em tamanho nativo e nearest. Corrija
   causa dominante de incoerência de cabeça, roupa, material, pivô ou arma.
   Não eternize a provocação por diferenças numéricas sem defeito perceptível.
7. Compile catálogo do personagem com vínculo asset→ação→símbolo→ROM e carga
   por demanda. Não exigir que todos os assets caibam residentes ao mesmo tempo.

Aceite: pacote completo da matriz, coerente com identidade, ações inteiras
observadas, composição legal, evidências atuais e aprovação nos eixos
pertinentes. Aceite de GQ03/provocação não é automático. Não iniciar pacote
completo de outro personagem antes da validação solicitada para Social.

#### Etapa F — cena10 e experiência completa prevista no GDD

Owner: engenharia/UI + arte + design. Depende da E e de comandos decididos.

Implemente o padrão `character_move_showcase_standard_v1.md`: nome do golpe,
representação bem desenhada do controle SMS, direções/botões/ordem e feedback.
A demonstração usa o reconhecedor real; prática consome input real. A timeline,
hitstop e recuperação são os da luta, sem tabela paralela ou velocidade
inventada. Separe tempo de leitura da UI e animação. Slow/step diagnósticos
são identificados. Reset/saída/segunda execução não vazam estados. Super de
counter precisa de ataque elegível, não ativação forçada do resultado.

Depois conclua as cenas e transições autorizadas do GDD/roteiro/spec do
Master of Fighters: preparação, luta, consequência e encerramento; abertura,
título/opções, narrativa, progressão e finais conforme decisões válidas.
O escopo rev2 de fundo sólido não proíbe o cenário autorizado de MoF; o
escopo MoF não amplia automaticamente rev2. Para Alis, três magias de Shinobi,
cameos, voz digitalizada e variações de entradas, respeite os contratos de fã
já registrados e as decisões abertas; não invente números, músicas, identidade,
persistência, novo boss jogável ou arsenal. Encenação não é gameplay validado.
A possibilidade de desbloquear a galeria continua proposta, sem economia/save
implantados por inferência.

Aceite: cada cena tem finalidade e informação legíveis, entrada/saída/skip,
ações, feedback, conteúdo simultâneo e extremos realmente exercitados.
Diálogo não cobre rosto/ação essencial; comandos apresentados funcionam;
transições não deixam VDP, input ou áudio em estado parcial. Budget de cena
inclui transição, HUD, FX, texto e áudio reais. Não abrir produção extensa de
arte de outro personagem antes do gate da E.

#### Etapa G — robustez, documentação e recuperação final

Owner: manutenção/engenharia/QA. Depende das etapas funcionais afetadas.

Feche os IDs restantes de reuso/resiliência/qualificação do backlog, incluindo
IR/ABI, validação de dados, bancos-limite, pacotes inválidos e falhas de geração
sem destruir estado anterior. Teste loops/soak controlados, wraps, pools,
segunda partida, navegação, Pause, entradas mantidas e extremos numéricos.

Atualize READMEs dos consumidores com seus comandos atuais, builds selecionadas,
limites e próxima entrada; remova instruções obsoletas sem apagar histórico.
Refatore apenas onde houver benefício necessário e regressão coberta.
Não crie campanha de arquitetura ou instalação de CI sem relação com o aceite.
Checks skipped ou ausência de workflow não aprovam nem anulam a QA local.

Verifique o caminho de restauração dos arquivos únicos e das fontes/receitas.
Registre o que está no GitHub e o que continua local. Teste a recuperação pelo
mecanismo existente em staging oficial, não por clone/worktree adicional.
Nenhum conjunto útil pode depender somente de cache pessoal ou único exemplar.

Aceite: percurso completo com sete eixos, imagem/áudio/input coerentes, budgets,
recuperação comprovada, documentação operacional atual e publicação conferida.

### 6. QA obrigatória e limites de evidência

Antes de automação, leia os workflows centrais
`emulator-isolated-session.md`, `subagent-emulator-qa.md`,
`mugen-engine-quality.md`, `product-quality-checkpoint.md` e a pipeline
`mugen_fighting_v1.json`. Confira CLI real; não copie flags antigas sem validar.

- Self-check de cada medidor antes de usar leitura. Ferramenta defeituosa é
  corrigida no owner oficial com regressão, nunca contornada.
- Sessão privada por ROM/SHA, input em frames VDP, vídeo do framebuffer para
  movimento, áudio isolado e encerramento dos processos próprios confirmado.
  Nunca usar desktop alheio como fallback nem simular reviewer em JSON.
- Revisão independente conforme o framework e ferramentas autorizadas da
  sessão; produtor não se autoaprova. Se delegação for permitida, owners
  disjuntos e concorrência limitada; nenhuma medição FPS em paralelo.
- **Alvo60/piso58** em cada janela válida sem arredondar, pelo menos duas,
  dispersão≤2 e teto61. PAL50 é diagnóstico. Contador em ISR, título ou vídeo
  por stepping não pagam FPS funcional.
- Worst-frame da mesma ROM, carga real, janela contínua sem leituras DAP,
  selo3000/done1/zero derrame conforme contrato vigente; mínimo selado não
  é snapshot. Medir o degrau seguinte quando alegar margem.
- SAT≤64 e≤8porlinha, paleta/VRAM/stack/banking e transferência coerentes.
  Ausência de overflow simulado não prova pixels nem gameplay.
- Probes após pré-processamento e mapa do build; não reutilizar corredor
  de outra candidata. O parser já foi corrigido para recusar arrays omitidos.
- Testes focados durante implementação, gates integrais pertinentes no
  fechamento estável. Não repetir suítes sem mudança/falha/incerteza nova.
- Preserve falhas válidas e controle. Evidência de outro SHA continua histórica.
  7/7 exige também época visual delivery, vínculo asset→ROM, memória atual e
  revisão; nenhum checklist certifica AAA.

Comandos de partida, sempre conferir ajuda e paths reais:

```sh
rtk git status --short --branch
rtk proxy tools/sms_wrapper/run_host.sh python tools/sms_wrapper/host_bootstrap.py doctor
rtk proxy tools/sms_wrapper/run_host.sh python tools/sms_wrapper/reconcile_claims.py --project SMS_projects/luta_mugem_rev2
rtk proxy tools/sms_wrapper/run_host.sh python tools/sms_wrapper/build_inner.py --help
rtk proxy tools/sms_wrapper/run_host.sh python -m mugen2sms --help
rtk proxy tools/sms_wrapper/run_host.sh python tools/sms_wrapper/emulator_session.py --help
```

Para candidatas, o builder aceita `--project`, `--build-dir` novo sob
`out/candidates` e `--manifest` dentro do consumidor. Não sobrescrever
candidata selada nem usar `--skip-pre-gates` para conclusão.
`reconcile_claims.py --build-record <absoluto> --current-rom <absoluto>`
evita escolher a nominal errada; `--session` é explícita quando aplicável.
Sem sessão/evidência selecionadas, conciliação de recibo não aprova runtime.

Os auditores de composição/sola ainda em curadoria mantêm teto diagnóstico.
Não os promova a lei global por este prompt nem imponha distinct-fighters
a espelho legítimo. Siga os gates atuais do domínio, não uma lista congelada.

### 7. Commit, PR e preservação no GitHub após cada lote

Esta é parte da entrega, não tarefa opcional para o fim do projeto inteiro.

1. Revise diff do lote, arquivos explícitos, segredos, licença/proveniência,
   tamanho e evidências. Separe correção válida de experimento rejeitado.
   Só inclua WIP anterior quando necessário, revisado e corretamente atribuído;
   stage parcial quando o arquivo for compartilhado. Nunca `git add -A`.
2. Faça commit coerente do incremento. Pode haver commit diagnóstico/recovery
   claramente identificado enquanto a solução continua; isso não fecha item
   nem justifica parar. Não publique código comprovadamente quebrado como fix.
3. Confira remoto e divergência antes do push. Os commits preexistentes à
   frente também seriam publicados: confira seu conteúdo e validação, sem
   atribuir-lhes QA de checkout limpo quando o teste incluiu WIP.
4. Push na branch registrada, sem force. O gancho deste repositório já recusou
   alias de destino; use o refspec completo:
   `git push origin refs/heads/codex/host-bootstrap-continuity-20261024:refs/heads/codex/host-bootstrap-continuity-20261024`
   através do RTK. Gancho rejeitado exige resolver o motivo, nunca bypass.
5. Reutilize PR#4 se continuar aberto e com a mesma finalidade. Atualize sua
   descrição com problema, mudança, testes, SHA e limitações atuais, preservando
   escopo acumulado. Não crie um PR por checkpoint. Se o PR já tiver mudado,
   confira destino e política antes de criar/substituir. Não faça merge.
6. Confirme SHA remoto por leitura; consulte checks uma vez no marco útil.
   GitHub com checks skipped não equivale a teste aprovado. Uma escrita remota
   de resultado incerto é verificada antes de retry; não duplicar pela outra API.
7. Fontes/receitas/docs ficam no Git. ROMs, bancos, SDKs, caches e grandes
   pacotes não entram no código para fingir backup. Use o mecanismo de
   recuperação e destino de artefatos já autorizados; registre URL, bytes,
   SHA, escopo e teste de restauração. Backup local não é backup na rede.
   Não criar release de produto ou publicar insumo privado no repositório
   público. Se faltar destino remoto autorizado para insumo único, solicite
   essa decisão específica cedo, preserve a cópia e continue o restante.
8. Atualize o handoff com commit/PR/remoto e cobertura real da proteção.
   Feche processos temporários próprios e siga para o próximo lote.

### 8. Condição de conclusão

Conclua somente quando os itens autorizados estiverem implementados,
integrados, exercitados na interação prevista, medidos e preservados,
com as decisões do proprietário respeitadas e os critérios acima pagos.

A entrega final inclui core/consumidores, personagem e cenas no escopo
decidido, receita recuperável, fontes e dados vinculados, evidência por ROM,
backlog/matriz verdadeiros, PR e SHA remoto confirmados. Relato final curto,
com resultado, testes e limitações materiais; sem outro prompt no lugar do jogo.

Não declarar conclusão global enquanto houver funcionalidade obrigatória,
gate reprovado, recuperação sem prova ou decisão indispensável pendente.
Continue enquanto existir trabalho seguro autorizado. A impossibilidade de
obter aprovação/acesso externo não autoriza fabricar sucesso; registre a
dependência concreta sem abandonar os ramos executáveis.
