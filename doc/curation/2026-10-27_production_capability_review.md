# Avaliação da capacidade de produção do SMSForge

Data: 27/10/2026. Base: `651284ca4c1388beb6da9a4b373bde9a96c24090`.
Escopo autorizado: avaliar e assimilar melhorias em workflows, ferramentas e
skills da fábrica. Este lote não altera runtime ou assets de consumidores.

## Parecer

O SMSForge possui uma base extensa de instrumentação, limites de hardware,
rastreabilidade e revisão. A evidência examinada ainda não demonstra uma
capacidade repetível de entregar jogos comparáveis aos melhores 8 bits.
O maior impedimento é transformar conhecimento e contratos em uma experiência
completa, legível e consistente sob carga real. Aumentar o número de skills ou
o número de efeitos não resolve esse impedimento.

Há duas dívidas diferentes: a produção tem falhas abertas; o registro de
maestria superestimava a força das próprias provas. As correções deste lote
melhoram a fábrica, sem converter manutenção documental em qualidade de jogo.

## Cobertura e força das evidências

Inventariados 34 skills, 26 workflows, 5 personas, 5 pipelines, arquitetura e
lei central: 72 documentos. O descobridor canônico encontrou 75 ferramentas
de medição; o wrapper contém 230 arquivos Python no momento do inventário.
Os paths e hashes estão no [inventário](evidence/2026-10-27_production_capability/inventory.json).
A avaliação cobre todas as famílias de produção, com leitura aprofundada dos
contratos centrais e dos pontos de risco. Não é auditoria linha a linha de
cada ferramenta, nem novo playtest de todos os jogos.

Foram examinados memória/GDD/spec/TDD de `luta_mugem_rev2`, backlog de 55
itens, parecer de 24/10, matriz de maestria, pipelines e fontes da API local.
A continuidade registra P2 fragmentado/fundo repetido e prova diagnóstica com
`vline_min=4`, `vovf_delta=1740`; isso é evidência histórica citada, não medição
refeita nesta sessão. A recuperação no host novo prova boot limitado.
O estado do consumidor não permite estender esse boot a gameplay, áudio,
performance ou qualidade artística.

## Capacidade por domínio

| Domínio | Base existente | Lacuna que impede excelência | Aceite concreto e owner |
|---|---|---|---|
| Direção e design | GDD, core loop, slice e checkpoint conjunto | Receita genérica curta; pouca orientação prática para ritmo, aprendizado, câmera e teste humano | Direção: ciclo com decisão/risco/retorno, teste de tarefas com público e correção dos problemas observados |
| Arte e animação | Proveniência, paleta por material, poses, recorte, roster, princípios e binding | Contratos fortes não garantem autoria, composição nem animação legível na ROM; skill visual carrega exemplos específicos de Master of Fighters | Arte/runtime: fontes aprovadas e poses completas legíveis em movimento na mesma cena |
| Hardware e render | Simuladores SAT, mapa VRAM, orçamento selado, probes, dumps e diagnósticos | Matriz/roadmap divergiam da doutrina; no rev2, legalidade por corte não preserva o personagem | Runtime: SAT viva, framebuffer, contato e upload coerentes no pior caso |
| Controle e game feel | Input por frames, casos observados, receitas de combate, FSM | Ação aceita pode aparecer tarde; métricas médias e ACK não provam resposta | Gameplay: entrada→pose→evento→recovery com prazo e vídeo/trace alinhados |
| Áudio | PSGlib, proveniência, parser de streams, canal autorado e captura isolada | Sinal e heurísticas não demonstram motivo musical, frase, mix ou loop agradável; arbitração precisa coexistir com render/IA | Áudio: escuta da ROM sob SFX concorrente, pausa/retorno e alvo regional |
| CPU, memória e escala | SDCC, pré-computação, bancos, pools e medidores | Reserva do próximo degrau e custo integrado ainda não fechados no consumidor | Budget: worst-frame com conteúdo real, RAM/stack e fronteiras de banco medidas |
| QA e reprodutibilidade | Sessões privadas, SHA, pedidos, snapshots e negativos | Self-check prova o instrumento no caso sintético; não cobre por si todo o corpus nem todo o jogo | QA: regressões do delta, soak e casos raros na ROM atual; histórico separado |
| Operação e conhecimento | Bootstrap, recuperação, ledger e rotas de lições | Conteúdo central extenso, cópias locais preservadas e rotas divergentes aumentam custo e risco de instrução antiga | Curadoria: leitura por tarefa, manutenção dos entrypoints e teste de aplicação das skills |
| Entrega e compatibilidade | Sete eixos, época delivery e release workflow | Nenhuma homologação geral de SMS1/SMS2/PAL/NTSC ou console físico decorre dos gates | Integração: matriz explícita dos alvos realmente exercitados e limites publicados |

Esses são julgamentos de prontidão por evidência; não pontuações numéricas de
arte, diversão ou domínio de hardware.

## Achados corrigidos neste lote

**Custódia de maestria.** O auditor original dava PASS ao registry com 32
entradas acima de `mapped`: 15 `emulador_provado`, 9 `reproduzivel`, 6
`default_senior` e 2 `incorporada`. Aceitava textos como nome de gate ou
“paleta carregada”. Não verificava arquivo, SHA ou associação à ROM. O novo
contrato verifica arquivos, papéis, escopo e hashes; provas de emulador incluem
ROM/mídia/relatório com identidade da ROM e sessão. Foram preservados os claims
antigos em `legacy_claim`, com nível `mapped` até reindexação. Não houve
apagamento de evidência nem alegação de que todas as técnicas foram refutadas.
O auditor continua sem autenticar execução ou julgar o conteúdo de uma captura.

**Conhecimento contraditório.** Matriz e roadmap ainda ensinavam shift de 32 px,
terminador sem qualificar modo, corrupção SMS1 como certeza e slot 0 inteiro
fixo. Foram alinhados às correções já canônicas e à skill de banking. O roadmap
agora distingue transformação de paleta por software, raster horizontal e
hipótese de ilusão vertical, sem anunciar hardware novo ou domínio universal.

**Integração de produção.** O pipeline principal saltava de TDD para cenas;
os workflows de slice e qualidade conjunta já existiam, mas não apareciam
nessa rota. Foram ligados antes da expansão de conteúdo. O JSON continua sendo
um roteiro declarativo: a presença de uma fase não executa nem paga o gate.

**Aplicação das skills.** O bootstrap ganhou seleção por tarefa; o core loop
passou a orientar métricas de movimento/câmera, encontros, ritmo, feedback e
teste humano. O fluxo de áudio ganhou frase/loop, disputa de canais e retorno
regional. São métodos de autoria e aplicação dos gates existentes, não novos
predicados que certificam diversão ou música. Não instalamos outra biblioteca
nem sobrescrevemos `.agent` local dos consumidores.

**Compatibilidade e cobertura dos medidores.** A varredura dos 75 instrumentos
encontrou uma falha preexistente em `audit_asset_proof_sheet.py`: três chamadas
a `get_flattened_data`, indisponível no Pillow 11.3.0 do ambiente fixado. O
gate passou a usar `getdata` para as imagens indexadas/canal alpha e entrou
na lista da suíte principal, onde antes faltava. Mantidos os testes de recorte,
paleta, transformação, borda e overlay. O auditor de constantes também
encontrou uma frase histórica de demanda de 9–10 sprites que sua regex lia
como capacidade; a frase passou a explicitar “demanda antes dos cortes”. O
número histórico foi preservado e o limite de hardware não foi alterado.

## O que as referências externas agregam

O post indicado apresenta **ForgeSkills**, um repositório diferente de
`awesome-gamedev-agent-skills`. O número anunciado no post era 20; o README
consultado já apresentava 28. Os próprios testes publicados delimitam a
validação a Blender/Python e preservam falhas; isso não qualifica uma engine
SMS. A contribuição é comparar artefatos e registrar diferenças concretas,
trabalhando uma causa por iteração. Esse princípio já existe no SMSForge e
serve para verificar sua aplicação, sem importar métricas 3D como qualidade
pixel art. [Post](https://www.reddit.com/r/aigamedev/comments/1xdnhmv/i_built_20_reusable_skills_to_make_ai_coding/),
[ForgeSkills](https://github.com/sekaikx/ForgeSkills/tree/23b054428e1d7df51f8f31798833bbcfc63864e1),
[testes declarados](https://github.com/sekaikx/ForgeSkills/blob/23b054428e1d7df51f8f31798833bbcfc63864e1/docs/TEST_RESULTS.md).

O catálogo `awesome-gamedev-agent-skills` oferece separação entre engine,
disciplina, gênero e workflow. O README consultado anuncia 76 skills; a descrição
do repositório ainda dizia 74. A contribuição aplicável é carregar apenas o
conhecimento necessário e associar versão/fonte. Seu router pode escolher
outra engine quando desconhece o projeto; esse fallback não cabe aqui.
[Router na revisão consultada](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/184b72be02884f782a0058f2eeae2ce4277453e4/router/SKILL.md).

| Referência | Assimilação para SMS | Limite da adaptação |
|---|---|---|
| [Level design](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/184b72be02884f782a0058f2eeae2ce4277453e4/skills/disciplines/level-design/SKILL.md) | Geometria a partir do movimento medido; ensinar/praticar/testar e revisar o percurso | Fórmula contínua não substitui integração discreta Z80; placeholder permanece diagnóstico |
| [Game feel](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/184b72be02884f782a0058f2eeae2ce4277453e4/skills/disciplines/game-feel/SKILL.md) | Eventos com feedback proporcional e retorno definido | Não importar número fixo de camadas, time-scale ou custo supostamente barato de FX |
| [Camera systems](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/184b72be02884f782a0058f2eeae2ce4277453e4/skills/disciplines/camera-systems/SKILL.md) | Enquadramento, antecipação de ameaça, limites e retorno | Scroll/HUD/streaming dividem recursos; smoothing float não é receita Z80 |
| [Audio design](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/184b72be02884f782a0058f2eeae2ce4277453e4/skills/disciplines/audio-design/SKILL.md) | Hierarquia sonora, variação intencional e transições musicais | Adaptar ao PSG/driver; não presumir buses, compressor, stems ou metas de loudness universais |
| [Boss encounter](https://github.com/sekaikx/ForgeSkills/blob/23b054428e1d7df51f8f31798833bbcfc63864e1/skills/gamedev-boss-encounter/SKILL.md) | Antecipação, janela ativa, resposta e recovery observáveis | Lock-on, esquiva e proibição de três ataques iguais são escolhas daquele exemplo, não leis de qualquer gênero |
| [Game testing](https://github.com/sekaikx/ForgeSkills/blob/23b054428e1d7df51f8f31798833bbcfc63864e1/skills/gamedev-game-testing/SKILL.md) | Regras puras, FSM, limiares e artefato renderizado | Host tests complementam SDCC/ROM; não substituem o emulador |

As incorporações foram redigidas para a arquitetura local. Não foi copiado
código dos catálogos nem instalado plugin externo. Popularidade e quantidade
de skills não foram usadas como prova de superioridade.

## Referências de jogos e experimentos

A seleção abaixo é uma proposta de estudo por aspecto, não um ranking nem um
benchmark já executado. Para comparação futura: versão/região, trecho exato,
input, frames, tamanho nativo, áudio e método de captura; registrar separadamente
observação e hipótese sobre implementação. Não copiar assets ou inferir
registradores de um vídeo. Os manuais/capturas ajudam a selecionar o caso;
medidas de custo exigem fonte ou instrumentação apropriada.

| Referência | Pergunta de produção | O que não transferir automaticamente |
|---|---|---|
| [Ninja Gaiden SMS](https://www.smspower.org/Games/NinjaGaiden-SMS) e [Sonic SMS](https://www.smspower.org/Games/SonicTheHedgehog-SMS) | Como comparar leitura, câmera, recuperação após erro e variedade de beats em trechos comerciais? | Não confundir versões SMS/GG/16 bits nem atribuir técnica interna sem prova |
| [Silver Valley](https://www.smspower.org/Homebrew/SilverValley-SMS) | Como estudar unidade visual/sonora e variedade em um jogo feito com devkitSMS? | Escala de conteúdo não prova viabilidade no renderer atual |
| [Flight of Pigarus](https://www.smspower.org/Homebrew/FlightOfPigarus-SMS) | O manual oferece ciclo de pontuação, ondas dependentes da velocidade de abate e replay: como preservar clareza com pressão? | O autor recomenda PAL e menciona dependência de SRAM para replay; não declarar NTSC equivalente |
| [Micro Mages](https://morphcat.de/micromages/) | O autor documenta 40 KB e até quatro jogadores: como extrair princípios de economia visual e reuso com decisões interessantes? | NES é outra arquitetura; orçamento, paleta e APIs não migram para SMS |
| [rasterParallax](https://www.smspower.org/Homebrew/RasterParallax-SMS) | Demo com fonte do autor para investigar line IRQ + h-scroll e profundidade | Demo não demonstra custo combinado de gameplay, HUD, música e sprites |

Para explorar o hardware, a fonte local de API permanece
`sdk/devkitSMS/SMSlib/SMSlib.h` e `PSGlib/PSGlib.h`. A documentação do
[VDP](https://www.smspower.org/Development/VDP-Index) e o
[devkitSMS](https://github.com/sverx/devkitSMS) ajudam a formular hipóteses.
A distinção [SMS1/SMS2](https://www.smspower.org/Development/SMS1SMS2VDPs)
precisa entrar no perfil de teste, não numa promessa genérica de compatibilidade.

## Próximos lotes por valor para o jogador

1. **Apresentação e resposta do consumidor atual.** Owner runtime, backlog
   ID01/R01/R02/R03/R05/R06/R09/R10/IN05. Aceite: sequência real completa,
   ambos os atores íntegros, contato visível e prazos/budget medidos na mesma
   ROM. Dependência: resolver representação antes de adicionar poses/efeitos.
2. **Qualidade conjunta e autoria.** Owners direção/arte/áudio, Q05/A01–A04.
   Comparar um trecho com uma referência por aspecto, ouvir mix real e testar
   tarefa com jogadores. Aceite: defeitos observados corrigidos e retestados,
   sem converter preferências em falhas de hardware.
3. **Domínio reutilizável.** Curadoria reindexa provas históricas e os owners
   de RE01–RE05 demonstram reuso por dados no core existente. Não criar um
   projeto substituto para escapar das falhas do rev2.
4. **Avanço experimental.** Só após estabilizar a interação, escolher técnica
   que resolva uma oportunidade visual/sonora: raster, cache, transformação de
   paleta, compactação ou áudio opcional. Medir baseline e próximo degrau;
   declarar fallback, revisão de VDP e alvos. Resultados permanecem restritos
   ao experimento até integração e QA.
5. **Robustez de produto.** Q04/Q06: soak, reinício/pausa/derrota, controles,
   save se previsto, documentação e alvos reais. Estender ensaio a console
   físico para claims que dependam dele. Não há acesso a console físico
   demonstrado neste lote.

O backlog do motor continua sendo a fonte operacional dessas pendências.
Este parecer não encerra seus 55 itens e não amplia seu GDD.

## Validação deste lote

Baseline: auditor de maestria, doc sync e learning capture aprovavam o estado
anterior. O contraprograma com evidência textual reproduziu a lacuna; fixtures
positivas/negativas agora cobrem hashes, ausência, schema, escape e ROM divergente.
Fechamento no host: 135/135 selftests, 75/75 self-checks de medidores e gates
de maestria, documentação, aprendizado e constantes passaram. O probe opcional
de build de projeto não foi executado. Resultados finais e comandos estão em
[validation.json](evidence/2026-10-27_production_capability/validation.json).
A suíte valida a manutenção da fábrica. Não houve nova execução de gameplay,
ensaio de áudio, comparação visual ou homologação de jogo nesta tarefa.
