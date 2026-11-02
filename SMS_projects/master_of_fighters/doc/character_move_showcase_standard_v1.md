# Apresentação de golpes — padrão de projeto e continuidade do Dr. Social

Versão 1, direção do proprietário em 2026-11-01. **Documentado; implementação,
arte, comandos finais e validação pendentes.** Este é um padrão de Master of
Fighters, não uma técnica homologada globalmente no SMSForge. Ver
[registro de direção](decisions/character-move-showcase_owner_direction_20261101.json),
[GDD](11-gdd.md), [roteiro](12-roteiro.md), [cenas](13-spec-cenas.md) e [TDD](15-tdd.md).

## Revisão vigente — incremento f4c5043 e QA do designer, 2026-11-01

**A provocação chegou ao viewer; a arte e o pacote continuam sem aceite.**
O agente cumpriu a etapa de integração e distinguiu corretamente diagnóstico
de comando competitivo. Minha recomendação não é abrir outra ação como prioridade:
resolver a continuidade visual desta provocação e completar o aceite do trecho.
Portraits independentes podem avançar durante dependência real de engenharia.

### Evidência conferida e nova observação

ROM preservada, 32768 bytes, SHA
`8f7687b85d68db923f9f3e36f4e1363c9be7136bc5438f880be7e0562e4f3f5d`.
Conferidos hashes da ROM/vídeo, recibo v2, receita de registro, inclusão do header
no viewer e fontes. Inspecionadas pranchas e quadros ordenados extraídos da captura.
Não alterei pixels, código ou ROM. O hash do vídeo confere com o do produtor.

**Correção de interpretação do vídeo:** ffprobe identifica 228 quadros em
3,804899 s de reprodução. O recibo da captura registra 5,157165914 s de coleta,
com codificação a aproximadamente 59,9227 Hz. É apresentação nominal dos quadros
capturados; não comprova que o usuário viu a ação nessa velocidade de relógio.
Não houve prova de emulador acelerado ou fraude: é uma distinção entre coleta e
reprodução. Preservar os dois tempos e as falhas de FPS, sem rebatizar esse vídeo
como prova de cinco segundos de fluidez em tempo real.

Como a carga havia diminuído, abri uma sessão privada própria, sem outra JVM de
emulador privado ativa, **com a mesma ROM**. Self-check do medidor passou.

| Sessão / condições | Janelas de FPS sem arredondamento | Escopo |
|---|---|---|
| Produtor f23c4ec… | 58.58830865506254 / 44.267676665832944 | Falhou; preservado. |
| Produtor ccc69901… | 49.33468997130153 / 45.14083899479978 | Falhou; preservado. |
| Designer e6c6db7a… | 59.652563933294665 / 59.67934459451107 | Passou o componente de taxa nas duas janelas de 8 s, mesma ROM. |

Carga registrada na sessão nova: 2.0244 / 8.6714 / 18.6270 (1/5/15 min), contra
cerca de 34 na primeira anterior. Isso sustenta investigar influência do ambiente;
não demonstra causalidade exclusiva nem permite descartar amostras lentas.
Não há justificativa para remover arte ou alterar os tempos para “consertar FPS”
com base apenas nos resultados anteriores. Pior frame, pacing, áudio e composição
de combate continuam pendentes; estas janelas não aprovam o personagem.

Na mesma sessão, sequências atômicas oficiais com pressões de seis frames
confirmaram `keys=16`, estados 0→1→4→0 e uma segunda execução 0→1→0. Isso prova
acionamento de revisão e retorno, não latência competitiva. Uma tentativa anterior
com input/step separados e pressão de um frame não estabeleceu a precondição
esperada; foi preservada, não transformada em aprovação de entrada de um frame.
Framebuffers publicados, bundle verificado e sessão encerrada. Recibo completo:
`out/diagnostics/social_taunt01_cycle_v2_review_20261101/review_receipt.json`.
FPS em `out/evidence/sessions/e6c6db7a8d0d4708adf4e5ee41e64116/runtime/taunt_designer_review.json`.

### Defeitos visuais que orientam o próximo lote

1. **TA07 muda direção e aparência.** O rosto olha para o lado oposto ao rival
   deste arranjo; a saída SMS escurece amplamente casaco/corpo, depois volta ao
   ciano da guarda. Ambos aparecem na captura. Não é apenas preferência por uma
   pose: há quebra de continuidade de orientação e luz/material. Corrigir a
   fonte/atribuição de cores pelo método autoral, sem repintura procedural.
2. **Altura/identidade precisam de causa.** TA05/TA06 têm 72 px e TA07 73,
   contra 69 da guarda. A razão comum na conversão evita a antiga normalização
   por pose, mas não garante escala coerente entre imagens geradas. Verificar
   crânio, ombros, tronco e proporções: separar extensão corporal legítima de
   crescimento/deriva de geração. Não esmagar TA07 nem conceder exceção ao GDD.
3. **Retorno ainda precisa leitura temporal.** TA07 põe o punho na cintura e a
   guarda o traz de volta ao peito. Conferir trajetória e continuidade da cabeça/
   mão/tecido no ciclo; não impor “um quadro a mais” antes de demonstrar o problema.
   TA05 separa melhor o exame do ajuste, mas essa melhora não paga os demais eixos.

Os 68 ticks são uma hipótese diagnóstica completa. São cerca de 1,13 s a 60 Hz,
sem incluir espera da UI; não substituem os 22 ticks propostos no contrato e não
são frame-data competitivo. O gesto deve parecer uma avaliação confiante do
adversário, com assentamento corporal, não troca de modelo/iluminação no final.
O problema dominante agora é essa continuidade, com validação técnica ainda
incompleta. A nova medição não converte GQ03 ou os controles em aprovados.

## Histórico — revisão do incremento 2075484, 2026-11-01

**A provocação 1 tem chaves candidatas e um percurso de retorno; ainda não tem
animação completa validada.** O agente avançou além de outra guarda e manteve
proveniência, jab e limites de claim. GQ03 r2/tuck não resolveram a composição;
continuam estudos, sem tornar a GQ03 original aprovada por exclusão.

Inspecionei as duas pranchas lógica/SMS, prompts, receita, adaptador e contrato
v2. Self-checks passaram; os 15 manifests existentes — cinco poses em base,
espelho e packing x=4 — foram reavaliados, todos pico 8/zero overflow, SAT de
32 a 35. Os hashes das quatro fontes novas conferem. Sem reconversão, ROM,
playback observado, FPS ou sessão de emulador nesta revisão. Recibo:
`out/diagnostics/social_taunt01_review_20261101/review_receipt.json`.

### Leitura artística e aderência ao contrato

- TA02–TA04 comunicam aproximação da mão e ajuste dos óculos na prancha lógica.
  No SMS a redução comprime a informação facial. TA05 continua semelhante ao
  ajuste; a diferença de 415 pixels não prova o olhar avaliativo para o rival.
- O significado a preservar é uma provocação perspicaz: percebe o adversário,
  ajusta os óculos, examina-o com confiança e recompõe a guarda. Cabeça, direção
  do olhar, separação mão/rosto e pausa legível devem trabalhar juntos. Não
  exigir que um detalhe minúsculo dos olhos carregue sozinho a atuação.
- Todos os prompts novos mandam manter pés, bengala e barra do casaco exatamente
  iguais. Isso explica uma restrição de produção que conflita com a ação
  secundária planejada; não prova impossibilidade de movimento no hardware.
  Pés podem servir de apoio e a bengala pode permanecer plantada sem congelar
  quadril, ombros, tecido e mão ativa. Não exigir deslocamento onde não ajuda.
- TA06 (`casaco_lag`) não foi desenhada nem medida; TA07 reutiliza TA05. O retorno
  passa por TA04→TA03→TA02→GQ03. Reuso e holds são legítimos se a sequência tiver
  continuidade e intenção; não é obrigatório redesenhar todos. Porém, reprodução
  invertida não prova recuperação natural, atraso do tecido ou sustentação do
  olhar. TA08 igual à guarda prova o terminal, não o percurso.
- O contrato v2 propõe oito funções e exposições 2/2/2/2/3/2/5/4 (22 ticks).
  O adapter de chaves leva apenas 2/2/2/3 para TA02–TA05; o percurso de revisão
  tem nove entradas sem duração completa declarada. Não existe ainda uma timeline
  integral para avaliar velocidade. Contagem de desenhos e ticks são propostas;
  reuso deve ser declarado, sem fabricar poses distintas para fechar números.

### Direção de design para este gesto — sem alterar moveset

Concluir a intenção já prevista: preparar → alcançar/ajustar → olhar avaliativo
legível → sustentar → soltar/recolher → assentamento/guarda. O tecido responde
à ação do corpo e termina depois dela, com amplitude subordinada ao gesto.
TA06 não precisa de cauda espetacular fora da silhueta: desenhar atuação plausível
e medir, sem presumir overflow. Tampouco remover essa função sem registrar a
proposta e o impacto na atuação. Não adicionar invulnerabilidade, ganho de barra,
dano, fala ou equipamento como recompensa pelo trabalho artístico.

A faixa 66–72 px descreve a altura anatômica de referência em pé. Não normalizar
cada inclinação para a mesma altura opaca: isso pode anular o movimento ou fazer
o corpo mudar de tamanho. Conferir escala comum e âncoras no ciclo; mesma célula
ou mesmo pivô, sozinhos, não demonstram estabilidade anatômica. É critério de
verificação, não afirmação de que o ciclo atual já apresentou esse defeito.

### Próximo checkpoint e responsabilidade dos controles

**Fechar esta provocação e vê-la rodando**, antes de outra ação nova. Reutilizar
chaves aproveitáveis; resolver TA05, ação secundária, recuperação e timing total.
GD01/GD02 não bloqueiam reprodução diagnóstica em viewer oficial. Um acionador
de revisão deve estar identificado como tal, sem ensinar comando competitivo.
A galeria parcial pode usar estes candidatos com seus limites declarados;
compilar/observar não os promove a arte final nem aprova GQ03 ou o elenco.

O handoff `dr_social_gd01_open_conflicts_for_designer_v1.json` foi recebido.
Mantém a lista de conflitos já apontada; não é nova decisão nem implementação.
Designer/engenharia/proprietário continuam responsáveis pelos comandos; o
artista não precisa reenviar a mesma lista nem aguardar para finalizar este
experimento temporal. Cena 10 continua “comando em definição”. Depois desse
checkpoint, retomar o pacote completo com os bloqueios restantes explícitos.

## Histórico — revisão do incremento 07e4bce, 2026-11-01

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
foram o direcionamento daquele checkpoint; ver a revisão vigente de 2075484.

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
  revisão vigente de f4c5043 e a QA do designer; checkpoints anteriores são históricos;
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

**Estado real.** A provocação v2 está integrada em `MOF_CPS2_SAMPLE=9`,
com ROM de 32 KiB, SHA
`8f7687b85d68db923f9f3e36f4e1363c9be7136bc5438f880be7e0562e4f3f5d`.
O designer repetiu a QA nesse mesmo binário: duas janelas 59.652563933294665 /
59.67934459451107 FPS, acionamento de revisão e retorno observados. As duas
sessões anteriores falharam e continuam registradas. Sem aceite de pior frame,
áudio, arte, GQ03, comandos competitivos ou pacote. **Não abrir outra ação como
prioridade: corrigir a continuidade da provocação e fechar sua validação.**

Consulte `proposals/TA01_cycle_v2.json`, configs de conversão e registro, originais,
lineage e prompts sob
`data/source_art/sprite_studies/dr_social/review_drafts/cps2_keys_v1/`.
Build oficial: `.mddev/dr_social_taunt01_cycle_v2_build.json`.
A evidência nova está em `out/diagnostics/social_taunt01_cycle_v2_review_20261101/`.
Use esses dados para avançar; não refaça o que já foi observado sem necessidade.

1. **Preserve baselines e método.** Mantenha fontes, tentativas rejeitadas,
   recibos e ROM v2 intactos. Reutilize GQ03/TA02–TA04 como candidatos do teste,
   sem promovê-los; jab v8 permanece preservado. Novos desenhos seguem a autoria
   visual aprovada. Código recorta/converte/mede; não cria anatomia, expressões
   ou poses. Diferenças de identidade não se resolvem com morph/interpolação.
2. **Corrija TA07 com uma intenção clara.** Social continua atento ao adversário
   do mesmo lado, solta/recolhe a mão e recompõe a guarda. O rosto não deve virar
   para o lado oposto por ambiguidade de “três quartos”. Preserve a luz e os
   materiais do casaco/rosto; não escurecer todo o personagem durante assentamento.
   Compare fonte, materiais e PNG SMS para localizar onde nasce a mudança de cor.
   Corrija na etapa responsável e reavalie 1×/ampliado. Não disfarce o salto com
   flash, corte de cena, hold longo ou efeitos novos.
3. **Verifique escala anatômica, não só bbox.** TA07 tem 73 px; não a esprema
   para 69 nem trate o excesso como aprovado. Use solo e âncoras de crânio,
   ombro/quadril para distinguir extensão legítima de deriva entre gerações.
   A razão de redução comum não corrige automaticamente imagens geradas em
   escalas corporais diferentes. Preserve a faixa de referência GDD 66–72 px,
   proporções e identidade; registre a causa e a correção observáveis.
4. **Revise a recuperação completa.** Veja TA05→TA06→TA07→GQ03 continuamente:
   direção do olhar, mão ativa, bengala, tecido e apoio. Preserve a melhora do
   exame e a ação secundária; desenhe só os intervalos necessários à continuidade.
   Não congele o corpo para satisfazer uma contagem de células nem abra outra
   provocação. Manter o terminal igual à guarda não dispensa a qualidade do trajeto.
5. **Mantenha timing como hipótese explícita.** O teste usa 8/8/10/20/10/12,
   68 ticks, separados das esperas da UI. Não os transforme em frame-data nem
   altere o contrato de 22 ticks como se tivesse aprovação. Teste a leitura e
   registre se percepção, ajuste, exame, pausa e retorno são compreendidos.
   Não alongue exposição para esconder falta de desenho; não acelere o emulador.
6. **Trate desempenho com evidência.** A mesma ROM já passou nas duas janelas
   da revisão; não reduzir conteúdo ou tempos com base numa hipótese não isolada
   de gargalo. Preserve as falhas anteriores e a carga do host. Ao integrar arte
   nova, refaça os checks pertinentes no novo SHA, com self-check, par, scanline,
   paleta/VRAM, input e pior frame efetivamente medido. Uma sessão por vez, sem
   encerrar tarefas alheias. Se houver regressão, comparar ao binário v2 sob
   condições registradas; corrigir causa, nunca baixar o piso58 nem escolher
   apenas janelas favoráveis. Janelas aprovadas não pagam pacing/pior frame.
7. **Distinga os relógios da captura.** O MP4 v2 reproduz 228 quadros em 3,804899 s;
   a coleta durou 5,157165914 s. Identifique essa reprodução nominal. Preserve
   timestamps/contagem e FPS funcional separadamente; vídeo nominal não prova
   fluidez em tempo real. Nova captura deve apontar o SHA novo, conter ciclo e
   retorno e declarar claramente o que seu relógio demonstra. Não editar ou
   sobrescrever a evidência antiga para parecer mais rápida/estável.
8. **Valide o trecho no viewer oficial.** Botões 1/2 seguem acionadores de revisão,
   não comandos de combate. Confirmar input consumido → início → exame → retorno
   → nova execução, além de lados/cantos pertinentes e integridade do personagem.
   Registrar máscaras, duração das pressões e frames observados; não inferir
   latência competitiva de uma pressão longa. Usar sessões privadas, captures
   vinculadas a ROM, áudio conforme escopo e cleanup. Se silêncio é intencional
   no viewer, declarar; isso não aprova o áudio do personagem ou da luta.
9. **Entregue um incremento fechado e honesto.** Fonte corrigida, receita,
   timeline, ROM por SHA, vídeo/capturas, medição aplicável e revisão de TA07→
   guarda. Separar taxa de janelas, pior frame, arte, input diagnóstico e aceite
   do pacote. GD01/GD02 seguem com designer/engenharia/proprietário; não reenviar
   a mesma lista de conflitos como trabalho novo nem usar isso para bloquear o
   viewer. Enquanto aguarda dependência concreta, portraits previstos podem
   avançar, mas outra ação não substitui a correção dominante deste trecho.

Atualize matriz/lineage/memória; não declare provocação, GQ03, conexão ao jab ou
personagem aprovados por inferência. Não abrir outro personagem ou desbloqueáveis.
Use RTK/run_host, checkout único e pipeline oficial, sem motor paralelo. Preserve
WIP alheio. Faça commit/push só dos arquivos próprios revisados na branch
registrada, confirme SHA remoto e encerre apenas sua sessão temporária.
