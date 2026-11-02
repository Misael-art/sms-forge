# Apresentação de golpes — padrão de projeto e continuidade do Dr. Social

Versão 1, direção do proprietário em 2026-11-01. **Documentado; implementação,
arte, comandos finais e validação pendentes.** Este é um padrão de Master of
Fighters, não uma técnica homologada globalmente no SMSForge. Ver
[registro de direção](decisions/character-move-showcase_owner_direction_20261101.json),
[GDD](11-gdd.md), [roteiro](12-roteiro.md), [cenas](13-spec-cenas.md) e [TDD](15-tdd.md).

## Revisão vigente — incremento 07e4bce, 2026-11-01

**GQ03 corrigiu a autoria da guarda, mas não concluiu o personagem.** O agente
respondeu ao diagnóstico anterior: voltou à edição de imagem referenciada em
J01, preservou GQ02 como estudo e discriminou materiais do excesso em BC04.
O script de GQ03 foi inspecionado: recorte por chave, redução nearest, encaixe
e quantização; não contém o shear anatômico de GQ02. Isso corrige aquele desvio,
sem aprovar automaticamente o desenho ou a tradução SMS.

Fonte lógica `44c64bc9…`, derivado SMS `279d65f5…`; receita registra o original
`e168fc42…` e J01 como referência. Inspecionados fonte ampliada, saída SMS e
J01. GQ03 apresenta uma base compacta desenhada, mas a saída SMS ainda funde
as botas em parte da região inferior e simplifica rosto/materiais. Preservar
esse resultado para comparação, sem chamar quantização de acabamento aprovado.
O próprio produtor relata diferenças de cabelo/colete/base: verificar identidade
contra model sheet e jab. **Um intervalo resolve deslocamento/pose, não mudança
de figurino, cabelo ou proporção.** Não aprovar um morph entre versões distintas
do personagem, nem determinar por texto que basta exatamente um novo quadro.

### Conferência técnica e seus limites

Self-checks do adaptador e simulador passaram nesta revisão. Reexecutei o
simulador nos cinco manifests existentes, sem reconversão, edição de pixels,
build ou sessão de emulador:

| Manifest | SAT | Pico/overflow |
|---|---:|---|
| GQ03 base | 32 | 8 / zero |
| GQ03 espelhada | 32 | 8 / zero |
| Packing x=1, x=4 e x=7 | 34 cada | 8 / zero |

Recibo: `out/diagnostics/social_gq03_review_20261101/simulation_review.json`.
São testes do mesmo Ken de construção. Transladar todo um metasprite em X
preservando seus intervalos Y não muda a contagem por scanline; oito posições
não são oito novos orçamentos. Posição nos cantos ainda precisa prova de clipping,
wrap e integridade do corpo/arma no runtime. Packing distinto e face espelhada
são casos diferentes e foram conferidos como tal. Pico 8 significa zero folga
**nas linhas saturadas** para sprites adicionais. Não prova impossibilidade de
qualquer FX, nem serve ao elenco inteiro: BG/FX e novo par exigem budget próprio.

O diagnóstico de materiais do BC04 é exploratório: classifica cores próximas
da paleta e colunas, não identifica semanticamente toda a anatomia nem substitui
o simulador dos intervalos 8×16. Serve para orientar atuação: casaco/corpo,
haste e botas contribuem em faixas distintas. Preservar a intenção e alcance
do toque; não tornar “as duas solas no chão” ou “casaco atrás da haste” leis
universais de animação. Apoio e ação secundária precisam ser naturais.

### Parecer de design sobre controles v2 — proposta ainda não aprovada

A v2 é mais concreta, mas **não está pronta para virar GD01/GD02**:

- 1 jab, 2 toque e direção baixa+1 checagem formam uma candidata compreensível.
  Falta baixo-trás: definir se mantém guarda baixa e qual ataque resulta. Minha
  recomendação de design é avaliar a checagem a partir das três direções baixas,
  com prioridade explícita dos comandos completos; não está aprovada.
- Quarto de lua+1/2 pode ser candidato dos especiais. `dash_run` existe no
  contrato, mas não encontrei nesses documentos aprovação de “frente, frente”
  como seu comando. Tratar isso como hipótese de conflito, não decisão existente.
- Super exigindo duas bordas na mesma leitura privilegia precisão de um frame.
  Rejeito sua promoção sem experimento de controle real. Especificar bordas de
  pressão, botões já mantidos, lockout e reentrada: “ambos estão apertados” não
  equivale a “ambos começaram nesta leitura”. Comparar tolerância curta sem
  atrasar normais e, se isso exigir cancelamento novo, explicitar a regra para
  decisão; alternativa é propor um comando direcional com um botão. Nenhuma
  alternativa ou quantidade de frames fica aprovada aqui.
- Separar caminhada/guarda pelo tempo segurando trás adiciona uma distinção
  temporal ainda sem justificativa de experiência. Recomendo estudar recuo com
  trás e defesa contextual diante de ameaça elegível, incluindo guarda baixa,
  sem esperar N frames para a intenção defensiva. Hipótese para decisão e teste.
- Há conflito entre “sem barra 1+2 sai jab” e “especial completo vence normal”.
  Resolver explicitamente quarto de lua+1+2 sem barra, duas bordas desencontradas,
  direções baixas, ataque durante dash e estados nos quais não se pode agir.
  A regra de “encerra corrida com normal” também é proposta de cancelamento,
  não mero detalhe gráfico.

Janelas de 10/15/20 frames são hipóteses do produtor para comparar, não números
validados. Sem reconhecedor/ROM e teste de resposta, não aprovar facilidade de
execução nem mostrar a receita como lição na cena 10. O artista entrega as
necessidades de representação; designer/engenharia resolvem as regras e o
proprietário registra a decisão. Isso não bloqueia os desenhos independentes.

### Direção do próximo lote

Consolidar identidade da candidata sem recomeçar toda a guarda; se houver
deriva, corrigir a fonte autoral antes de gerar intervalos. Em seguida, chave
viável do toque e ciclo completo, conferindo todas as poses/retorno. Preservar
jab v8. A ligação com ele permanece pendente de continuidade visual e budget;
não inserir espera oculta no ataque. Se o toque continuar bloqueado, escolher
um estado já previsto e independente para fechar uma sequência observável.
O próximo checkpoint precisa mostrar progresso temporal, não somente outra
guarda legal. Galeria parcial pode demonstrar o que existe, claramente rotulada;
continua sem aprovar combate, comandos, FPS ou o pacote completo.

## Histórico — revisão do incremento 4f86572, 2026-11-01

**Dr. Social segue incompleto. GQ02 é estudo geométrico medido, não guarda
artística aprovada.** Esta foi a revisão de 4f86572; a revisão de 07e4bce acima e o prompt ao fim
são o direcionamento vigente.

O agente compreendeu a faixa GDD, a diferença entre simulação e ROM e a
necessidade de não inventar comandos. Preservou o jab e os originais. Porém,
a continuação desviou do método autoral: `author_gq02_stacked_guard.py`
desloca segmentos de cada linha de J01, empilha pixels e repõe a haste;
`refine_versus_plates_v1.py` pinta a expressão de derrota por sete coordenadas.
Não se trata apenas de converter paleta, recortar ou empacotar arte pronta:
esses scripts decidem nova anatomia/atuação. São estudos diagnósticos úteis,
mas não podem ser promovidos a personagem final sob AGENTS/SMS_GLOBAL §15.
O problema está demonstrado nesses derivados; não há motivo para atribuí-lo
a uma suposta referência antiga ruim nem descartar o model sheet aprovado.

| Peça | Conferência desta revisão | Consequência |
|---|---|---|
| GQ02 | Fonte `499a3932…`; 471 pixels deslocados, 64 sobrepostos segundo a receita. Derivado `08362e94…`: bbox 27×69 px. Self-checks do adaptador e simulador passaram; nova execução do simulador no manifest existente confirmou 35 sprites, pico 8, zero overflow. | Evidência limitada de composição naquele Ken/posição/face. Não refiz a conversão nem uma ROM. Pico 8 deixa zero folga nas linhas saturadas; requer par/FX/estados reais. |
| Atuação da guarda | Prancha J01/GQ02 inspecionada. A mudança comprime apoio e espaço entre pernas, cria quebras na região dos tornozelos e escada interna na cauda. | Parecer visual desfavorável à promoção dessa deformação como arte final. Redesenhar uma candidata autoral com sustentação anatômica e revalidar; não pedir ao dono que aceite a escada como condição de progresso. |
| Jab v8 | Fonte preservada; o início J01 é a guarda larga anterior. | A legalidade de GQ02 não se transfere a J01–J06. Revisar conexão entre guarda, preparo e retorno, sem substituir a fonte aprovada silenciosamente. |
| Portraits versus | Prancha tripla inspecionada. Limpeza de pontos não resolve por si só volume/crop; o franzir procedural não fecha atuação nem animação. | Preservar originais; dirigir expressão por olhos, sobrancelha, boca e postura coerentes, pelo método autoral. |
| Cena 10 | Storyboard 256×192, D-pad/1/2 identificáveis, texto pendente, palco sem atores. | Planta de layout, não UI final nem prova de escala/alcance/legibilidade em composição. |
| Pacote | Matriz registra 21 `not_started` e sete lacunas visuais, além de chaves/placas candidatas. | Não existe arranjo novo compilado de todos os assets; nenhuma animação nova foi validada nesta revisão. |

### Controles: avaliação da proposta, sem aprovação de GD01/GD02

`dr_social_two_button_proposal_v1.json` é um começo útil: 1 → jab,
baixo+1 → checagem baixa, 2 → toque. A frase “qual botão é leve” ainda deixa
até essa tabela condicional. O artista não deve escolher o restante sozinho.
Como hipótese de design para apresentar ao proprietário, preferir uma tabela
única candidata e avaliar quarto de lua para os especiais antes de duplo toque,
pois `dash_run` já faz parte do contrato. Isso **não aprova** quarto de lua,
qual especial ocupa 1/2, guarda, cancelamentos ou janelas numéricas.

A proposta precisa explicar, com casos observáveis: diagonal baixa e postura;
frente/trás nos dois lados; guarda versus movimento; ataque durante dash;
ordem de prioridade normal/especial/Super; press versus hold; comando expirado;
inputs simultâneos com pequena diferença temporal; ausência de barra e replay.
Para Super 1+2, declarar se o primeiro botão espera ou pode gerar normal,
a tolerância e o resultado sem barra. “Comando incompleto nunca gera normal”
não é promessa gratuita: pode exigir espera perceptível e afetar o jab.
Registrar a alternativa escolhida, seu custo de resposta e o teste necessário.
Attempt/hit/whiff continuam ramos do mesmo Super. Números permanecem hipóteses
até experimento; animações diagnósticas não são frame-data competitivo.

### Próximo resultado necessário

Uma pose autoral que preserve a função e a escala, seguida de composição medida
e de uma sequência completa com retorno. A função do toque é alcance frontal
rombo: não encurtar arma/alcance, mudar altura lógica ou esconder pixels para
passar. “Alcance” ainda é hipótese causal: no BC04 medido também há contribuição
da sola. Localizar linhas, células e materiais que somam o excesso antes de
escolher a solução. Guarda legal isolada não prova que o ataque cabe.

Arte independente continua enquanto GD01/GD02 aguardam decisão. O padrão
abaixo permanece: nome/controle/comando reais, animação na velocidade da luta,
manifesto por ação e integração gradual no consumidor. Galeria diagnóstica
parcial é válida como diagnóstico; não é tutorial funcional ou personagem pronto.

## Histórico — avaliação do incremento d7a3a2d

Inspecionados memória, matriz de cobertura, contrato v2, comparativo de conflito,
manifestos de placas e imagens de conversa/versus. O lote preservou fontes,
prompts e tentativas no Git. A revisão é estática; nenhuma animação nova foi
vista rodando e não foi aberta sessão de emulador nesta revisão documental.

| Área | Estado observado/documentado | Limite de aceite |
|---|---|---|
| Jab v8 | Seis desenhos existentes reutilizados; método e provas históricas próprios. | Não é nova integração do personagem completo. |
| Bengala / bota / rapieira | BC04/K04/RL05 são chaves isoladas; sem intervalos completos. | Não demonstram velocidade, arco, antecipação ou retorno. |
| Par em luta | Guarda/bengala nos controles 69/71 px falham; tentativa de guarda em três quartos não concretizou a hipótese e não foi medida. | Não existe proposta nova medida que resolva a composição; não baixar GDD automaticamente. |
| Conversa | Atenção/fala em placas indexadas com glifos e área de palco de diagnóstico. | Sem texto de runtime, alternância observada ou quatro expressões restantes. |
| Versus | Três placas candidatas: neutro, vitória, derrota; rival ainda é área vazia. | Estados estáticos não equivalem aos ciclos previstos nem à tela com dois personagens. |
| Restante do personagem | Matriz ainda registra muitos estados não iniciados e respostas visuais não desenhadas. | Sem pacote integral, arranjo compilado de todos os assets ou qualidade global aprovada. |

**Parecer artístico desta revisão, sem promoção:** as placas permitem reconhecer
Social, ler o texto e distinguir sorriso/abertura da boca. Nas imagens versus
ampliadas há pontos dispersos no casaco, grandes áreas com pouca separação de
volumes e alterações de enquadramento/rosto entre neutro, vitória e derrota.
Derrota permanece próxima do neutro. Isso orienta refino, não uma conclusão de
que a fonte/model sheet deva ser descartada. Comparar âncoras faciais, crop,
clusters e luz na mesma escala, em 1× e nearest ampliado; revisar a saída SMS
após quantização, sem tratar extração/maioria de bloco como acabamento final.

O personagem **não está terminado**. Não há base para dizer que todos os assets
foram compilados ou que a velocidade de suas animações foi aprovada. Não abrir
uma ROM antiga e apresentá-la como o novo pacote. Se houver nova evidência ao
retomar, conferir SHA, fontes e cobertura antes de atualizar esta conclusão.

## Intenção do padrão

O proprietário pede nome do golpe, demonstração com velocidade correta,
representação bem desenhada do controle do Master System e indicação de quais
botões/direções apertar e como executar. A referência a jogos Neo Geo orienta
clareza e apresentação; não autoriza copiar arte, comandos de quatro botões
ou criar outro sistema de luta. Possível desbloqueável futuro é uma ideia
registrada, sem regra/economia/save/desbloqueio decididos.

A cena 10, **Apresentação de golpes**, deve responder: qual ação estou vendo,
qual é sua intenção, como executá-la, quando ela acontece e quando volto ao
controle. Ela usa o personagem real. Retratos e estados sem comando ficam em
páginas de revisão apropriadas; não fingir que cada asset é um golpe executável.

## Contrato visual e de interação proposto

Fluxo proposto: selecionar ação → ler nome/comando → observar execução →
retorno à guarda → repetir ou experimentar → voltar/trocar ação. Navegação
exata depende do layout GD01; não roubar botões de luta enquanto o jogador
pratica. Sugestões de abas “Assistir”/“Praticar” são hipótese de UX da cena,
não modos extras de campanha já implementados.

| Elemento | Intenção e critérios observáveis |
|---|---|
| Nome | Nome legível e estável do movimento; ID interno apenas na revisão técnica. O nome final precisa aprovação, sem inventar título canônico. |
| Palco | Corpo e equipamento inteiros na escala de jogo; chão claro, rival quando necessário à consequência. Espaço de recuperação e objetos preservado. Não ampliar/encolher ator para parecer melhor nesta tela. |
| Controle | Ilustração autoral do controle SMS de dois botões, direcional à esquerda e 1/2 identificáveis. Referência de modelo físico registrada antes da arte. Sem botão Start obrigatório, AB/CD ou alavanca Neo Geo. |
| Sequência | Ícones de direção/botão ordenados, etapa atual destacada por forma/contorno além de cor. Distinguir apertar, manter, soltar, simultaneidade e sequência; só exibir operações usadas pelo comando real. |
| Resultado | Preparação, ação, consequência e recuperação visíveis. Demonstrar sucesso e, quando implementado, erro/guarda; sem explosão de acerto quando não houve contato. |
| Navegação | Ação selecionada e retorno claros. Input mantido ao trocar página não dispara golpe acidental; replay não duplica objeto/recurso. |

Proposta inicial de layout para storyboard, não budget fechado: nome na faixa
superior; palco no centro; controle e sequência na faixa inferior, fora da
silhueta dos lutadores. Medir conteúdo máximo, margens, golpes largos e texto
mais longo em 256×192 antes de fixar retângulos. Nome, comando e atuação são
prioritários; um portrait grande não deve expulsar a luta do espaço útil.

A arte do controle, botões, setas, marcadores e molduras exige identidade
visual comum, contorno/contraste legíveis e proveniência. Fonte com acentos e
hierarquia real em tamanho nativo. Sem peças genéricas provisórias promovidas
por estarem dentro da paleta. BG para UI é uma proposta a medir: não constitui
orçamento gratuito nem permite recolorir a P1 compartilhada dos lutadores.

O controle desenhado mantém sua orientação física quando o lutador troca de
lado. As setas demonstradas refletem a tradução real de frente/trás para o lado
atual. Não espelhar os rótulos 1/2. Se o comando muda durante troca de lado,
a apresentação deve seguir a mesma regra do reconhecedor do jogo.

## Comando e velocidade: uma fonte de verdade

A lista de movimentos de Social está aprovada em design; **o mapa competitivo
de dois botões e seus parâmetros ainda dependem GD01/GD02**. Não preencher a
interface com quarto de lua, carga ou combinação inventada para torná-la bonita.
Enquanto isso, a página de revisão deve declarar “comando em definição” e
reproduzir somente animação diagnóstica, sem alegar ensino/teste de execução.

Para cada movimento, contrato proposto, integrado aos dados existentes:

- ID da ação e nome exibido; fonte da decisão e revisão do comando.
- Entradas semânticas (direções relativas, press/hold/release, simultaneidade),
  limites temporais, contexto/postura, recursos e precedência do reconhecedor.
- Referências às poses/tracks reais, ordem e duração por pose; objetos e seus
  tempos de vida; começo, terminais de sucesso/erro e retorno.
- Versão de regra/arte/receita e evidência. Campos não decididos ficam pendentes;
  nunca herdar números de drafts, de outro personagem ou de animação diagnóstica.

UI, demonstração e prática consultam essa mesma definição. Na demonstração
funcional, entradas programadas passam pelo reconhecedor de comandos do motor;
não se chama uma animação diretamente e se apresenta isso como comando aceito.
No modo de prática, o destaque de input lê a entrada observada/consumida e o
resultado lógico, não um cursor que sempre completa a receita.

**Velocidade normal é a do runtime da luta.** A cena não tem tabela paralela de
holds “cinematográficos”, nem retarda o golpe para o jogador ler os botões. O
jogador lê a receita antes; depois assiste ao ritmo real e, se desejar, repete.
A duração do preparo antes de cada demonstração é UI, separada da preparação
do golpe. Marcador de fase e input devem estar sincronizados ao estado real;
latência de submissão/apresentação é registrada, não escondida.

Replay lento e avanço de quadro são facilidades de revisão **identificadas**;
não aprovam a velocidade normal, não alteram o arquivo aprovado nem o relógio
do combate. Não acelerar emulador. Preservar holds/timing aceitos dentro de
seu escopo; 2/1/1/1/1/3 do jab de estudo não vira frame-data competitivo.

Para Laudo Final, mostrar condição de barra cheia e alvo elegível; separar
attempt/hit/whiff sem criar três comandos. O roteiro da demonstração programa
o ataque adversário necessário; não “ganha” o counter por ativar diretamente
o ramo de sucesso. Reset de uma repetição restaura atores, relógios, recursos
e objetos de forma explícita. Em jogo normal esses resets não existem.

## Integração, evidência e completude

Um arranjo compilado pode carregar páginas/ações por demanda. “Todos os assets
integrados” significa que a ROM os referencia e os apresenta corretamente no
percurso de revisão, não que todos estejam residentes simultaneamente em VRAM.
Usar banking/residência/loader existentes, sem motor paralelo ou build no jogo.
Manifesto lista cada asset e a rota para encontrá-lo, com estados ausentes
explicitamente pendentes. Catálogo incompleto serve a diagnóstico, não a aceite
integral. Animação de um único ator não aprova composição do duelo com rival.

Primeiro piloto: jab atual, se reaproveitável no escopo diagnóstico, para
verificar UI/timeline/reentrada. Esse piloto não resolve o par a 66–72 px nem
aprova Social completo. A demonstração funcional com comandos só se torna
aceitável quando o reconhecedor e o mapeamento estiverem decididos/integrados.
A implementação da cena é trabalho posterior ao contrato; neste lote não há
nova ROM ou arte do controle sendo apresentada como pronta.

Aceite futuro por ação e pelo pacote:

1. Mesmo ID, poses, durações e regra no duelo e na cena; prova no mesmo SHA,
   sem comparar somente GIFs ou screenshots. Observar todo ciclo normal e retorno.
2. Entrada correta executa o golpe; errada/incompleta não produz falso sucesso;
   hold, simultaneidade, lado oposto e falta de recurso obedecem à regra real.
3. Nome/ícones correspondem à ação. Corpo, arma, FX, rival e UI continuam legíveis
   no pior frame, cantos e casos de maior simultaneidade.
4. Repetição/skip/troca de ação/saída não deixam hitbox, projétil, áudio, estado
   ou input residual. Não confundir controle de navegação com comando de ataque.
5. Instrumentos com self-check, recursos/scanline/paletas/VRAM/RAM e VBlank
   medidos; FPS funcional alvo60/piso58 por janela, sem arredondar, com input e
   lógica reais. Áudio/captura e cleanup da sessão privada conforme pipeline.
6. Revisão humana de qualidade e compreensão: jogador identifica nome/comando,
   distingue demonstração de prática e consegue reproduzir a ação. Não declarar
   playtest humano apenas porque um script acionou a tecla.

Futuro item desbloqueável: reaproveitar conteúdo e cena, deixando ponto de
entrada/condição separado dos movimentos. Não implementar moeda, save,
conquista ou esconder instruções essenciais sem decisão do dono. É possibilidade,
não requisito imediato nem permissão para ampliar conteúdo por inferência.

## Prompt de continuidade — copiar daqui até o fim

Atue como artista responsável por completar o Dr. Ferdinand Social em Master
of Fighters, integrado ao SMSForge. Diga [Contexto SMS Carregado]. Trabalhe
na raiz única `/home/misael/Projects/SMSForge`, consumidor
`SMS_projects/master_of_fighters`. Não comece outro personagem. O objetivo é
um pacote completo e revisável; a revisão do designer e do proprietário vem
antes de sua aprovação e das próximas tarefas de elenco.

**Contexto obrigatório.** Leia AGENTS da coleção e da raiz, continuidade,
`doc/10-memory-bank.md`, GDD, roteiro, spec e TDD do consumidor. Leia também:

- `doc/dr_social_complete_character_artist_prompt_v1.md`;
- `doc/dr_social_animation_contract_v2.json` e `doc/dr_social_coverage_matrix_v1.json`;
- `doc/dr_social_combat_design_proposal_v1.md`;
- `doc/dr_social_cps2_sample_v1.md`, revisão v8 e decisão do método em
  `doc/curation_candidates/2026-10-29_dr_social_cps2_source_to_rom_method.json`;
- este padrão `doc/character_move_showcase_standard_v1.md`, especialmente a
  revisão vigente de 07e4bce; checkpoints mais antigos são históricos;
- `doc/dr_social_two_button_proposal_v2.json`, proposta ainda não aprovada.

**Identidade e referências.** Social é humano, investigador/psicólogo, esguio,
cabelo grisalho, óculos de latão, casaco azul/ciano, colete separado, gravata
vinho, luvas claras e botas marrons. Preserve o model sheet aprovado
`data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v4.png`
e sua decisão por hash; preserve integralmente a fonte do jab v8 em
`data/source_art/sprite_studies/dr_social/review_drafts/cps2_sample_v1/jab_revision_v8/`.
Model sheet define identidade; jab v8 orienta atuação/qualidade; estudos técnicos
não viram referências de anatomia. Registre quais imagens entram na geração
e o papel de cada uma; não alimente o processo com todo o histórico de testes.
Bengala é romba, rapieira é lâmina rígida de estocada, bumerangue é de aço
com rastro violeta. Sem poderes mentais, vampirismo ou arsenal adicional.

**Estado real.** GQ03 é candidata autoral de guarda; no mesmo Ken, 69×25 px,
32 sprites e pico 8. Fonte: `cps2_keys_v1/logical/GQ03_authored_guard.png`,
SHA `44c64bc957d24127d056ce0437c270814838616e8b0e04357d9c1ede5cb7819b`.
Fonte, prompts, receita e medição estão sob
`data/source_art/sprite_studies/dr_social/review_drafts/cps2_keys_v1/`.
Base, espelho e packing x=1/4/7 passaram no simulador; não há aceite artístico
ou ROM. GQ02 permanece estudo procedural. Bengala, bota e rapieira continuam
chaves; portraits são candidatos; cena 10 não ensina um comando decidido.

1. **Mantenha o método aprovado.** Preserve GQ02 e os scripts como diagnóstico
   com proveniência explícita. Não os use para produzir anatomia, expressão ou
   intervalos finais. Produza o desenho por autoria visual e derive a versão
   SMS com a receita oficial. Código pode converter, medir, organizar e montar
   pranchas; não deve inventar tornozelos, deformar cauda por linha ou pintar
   expressão para simular trabalho artístico. Não altere a fábrica nem promova
   curadoria global. Se a ferramenta autoral estiver indisponível, registre a
   limitação concreta e avance contratos/medição/integração reaproveitável.
2. **Consolide GQ03 antes de animar a partir dela.** Compare em mesma escala
   com J01 e referências aprovadas: cabelo/rosto/idade, colete/fechos, comprimentos,
   proporções e equipamento. Use recortes identificados de identidade se o model
   sheet inteiro trouxer inventário que não pertence à cena. Não transforme
   diferenças de identidade em morph com um quadro intermediário. Se forem
   diferenças gestuais legítimas, demonstre continuidade; se forem deriva de
   geração, corrija a fonte autoral. Preserve J01–J06. Não recomece o pacote nem
   faça outra guarda apenas por variação estética. Corrija a leitura das botas
   e materiais na saída SMS pelo método autorizado, sem deformação procedural.
   Mantenha 66–72 px de corpo em pé e a receita oficial declarada, comum às poses:
   encaixe 2/3×6/7 seguido de extra 7/9 neste candidato. O estudo 35/52 é distinto.
3. **Use as medições existentes e valide o que mudar.** Não repita translações
   horizontais como novos orçamentos: os intervalos Y permanecem iguais. Retenha
   os controles base/espelho/packing; reexecute nos pixels/poses novos. Conferir
   1× e nearest ampliado, self-check prévio, hashes, par/face/posição, SAT, pico
   e linhas excedidas. Pico 8 não oferece folga nas linhas saturadas; efeitos,
   rival real e contato mudam o orçamento. Cantos precisam de prova de clipping,
   wrap e corpo/arma completos no runtime. Ken continua controle de construção.
4. **Resolva o toque pela função.** Use as linhas/células excedidas para separar
   contribuição dos pés, corpo, braço, haste e rival. Explore gesto, apoio e
   organização corporal preservando controle frontal, ponta romba, alcance e
   altura lógica. Duas solas plantadas e casaco atrás da haste são hipóteses de
   pose, não exigências de todos os quadros: permita peso e ação secundária.
   Não simplesmente eleve a arma, encurte-a, apague células,
   oculte rival ou divida em objeto supondo ganhar limite por linha. Uma nova
   chave é candidata até medida. Mudança de função/alcance/identidade exige
   alternativa concreta e decisão registrada do dono; continue peças independentes.
5. **Feche uma ação inteira assim que viável.** Preparação → ameaça/contato →
   consequência → recolha → retorno à guarda, com pivô estável, peso e equipamento
   contínuos. Meça também os intervalos. Preserve J01–J06 do jab v8; GQ03 não
   aprova automaticamente esse ciclo. Se a nova guarda não conecta com o jab,
   resolva primeiro identidade/figurino; só então apresente a transição gestual
   necessária e seu custo. Não fixe um único quadro como solução antes de ver o
   ciclo, não substitua os aprovados nem acrescente atraso competitivo oculto.
   Hipóteses de duração ficam rotuladas;
   exposição de estudo não define startup, hitstop ou recuperação de combate.
6. **Continue até cobrir o personagem.** Siga os IDs do contrato v2 e as lacunas da matriz:
   locomoção, guarda/respostas a impacto, queda/levantar, entradas, provocações,
   vitórias, derrota/empate, três normais, dois especiais e Laudo Final com
   attempt/hit/whiff. Complete tracks de corpo/arma/projétil/FX e os portraits
   de seleção, versus e conversa previstos. Não crie terceiro especial. Priorize
   uma ação completa em vez de outra coleção de contatos isolados; bloqueio da
   bengala não impede estados independentes.
7. **Refine portraits com atuação.** Reutilize fontes autorais e enquadramento
   coerente; alinhe âncoras faciais e idade, dê volume ao casaco e clareza a olhos,
   sobrancelhas, boca e postura. Não trocar expressão por sete pixels pintados
   por script. Complete suspeita, determinação, surpresa e alívio além de atenção/
   fala, conferindo o contrato vigente. Boca aberta isolada não é animação de
   fala. Texto fica fora do rosto, com acentos e leitura em 256×192 após paleta.
8. **Prepare a cena 10 de forma verificável.** Use o storyboard como planta,
   coloque candidatos reais do personagem, rival e golpe de maior envelope para
   testar espaço. Nome, controle SMS com D-pad/1/2, sequência e feedback devem
   ter acabamento coerente; o controle físico não se espelha ao trocar o lutador
   de lado. Pressionar/manter/soltar/simultaneidade devem coincidir com a receita.
   UI autoral, sem promover retângulos diagnósticos a acabamento final. O artista
   não decide GD01/GD02: entregue ao designer a v2 e os conflitos apontados na
   revisão vigente: baixo-trás, guarda temporal,
   Super de uma leitura, bordas versus hold, cancelamento de dash e quarto de
   lua+1+2 sem barra. Frente-frente para dash é hipótese, não decisão registrada.
   Não trate a ausência de resposta como aprovação. Até decisão, mostre “comando em definição”; nunca ensine um comando inventado.
9. **Integre pela rota oficial.** Coordene as necessidades de engenharia no
   consumidor existente. Construa catálogo navegável dos assets realmente prontos,
   carregados por demanda, sem motor paralelo. Piloto parcial deve indicar sua
   cobertura. Demonstração funcional usa reconhecedor, poses e tempos da luta;
   leitura antes/depois é UI, não lentidão adicionada ao golpe. Quando houver
   comandos aprovados, mostrar input consumido → ação → resultado → retorno,
   incluindo erro, block/whiff e Super sem recurso. Velocidade normal é a real;
   lento/step servem somente à revisão identificada. Desbloqueável futuro fica
   registrado, sem implementar economia/save/recompensas agora.
10. **Entregue evidência e continuidade.** ROM por SHA, vínculo fonte→derivado→
    símbolo→ROM, rota de revisão por ação, vídeo do ciclo em velocidade normal,
    orçamento real, pior frame, áudio e input em sessão privada do emulador.
    Alvo60/piso58 FPS funcional por janela válida, sem arredondar; boot ou contador
    isolado não aprovam. Preserve matriz/lineage, fontes/receitas e pendências com
    próxima ação concreta. Sem ROM, declare exatamente quais desenhos/sequências
    existem e o bloqueio; nunca alegue personagem completo ou AAA. Não autoaprove.

Use RTK/run_host e revise somente arquivos próprios ao commitar. Preserve WIP
alheio. Antes do push confira registro e remoto; use o nome completo da branch
registrada, não um alias `HEAD` se o gancho exige a referência ou SHA. Não
contorne o gancho, crie outra branch ou mude o registro para publicar. Confirme
SHA remoto uma vez. O bloqueio de publicação não substitui a conclusão artística.

Próximo checkpoint: uma ação/estado previsto com ciclo completo e retorno,
medido e observado temporalmente. Se o toque seguir bloqueado, conclua uma
sequência independente já prevista, mantendo o objetivo integral. Não encerre
o objetivo ao conseguir outra pose estática. Prossiga pelos ramos
viáveis até o pacote revisável; decisões ainda não experimentadas permanecem
explicitamente pendentes, com experimento e responsável definidos.
