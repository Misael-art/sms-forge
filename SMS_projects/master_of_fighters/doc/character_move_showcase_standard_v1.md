# Apresentação de golpes — padrão de projeto e continuidade do Dr. Social

Versão 1, direção do proprietário em 2026-11-01. **Documentado; implementação,
arte, comandos finais e validação pendentes.** Este é um padrão de Master of
Fighters, não uma técnica homologada globalmente no SMSForge. Ver
[registro de direção](decisions/character-move-showcase_owner_direction_20261101.json),
[GDD](11-gdd.md), [roteiro](12-roteiro.md), [cenas](13-spec-cenas.md) e [TDD](15-tdd.md).

## Parecer vigente — terminal 587763c e troca de agente, 2026-11-02

**Provocação v3: candidata tecnicamente demonstrada no viewer, disponível para
julgamento artístico; personagem completo ainda distante de encerramento.**
O commit `587763cf1e192ada7bfbed4510d27fde240017b5`, posterior ao último parecer,
acrescentou medição/prancha do terminal, sem pose nova, build ou mudança da ROM.
HEAD e remoto conferidos nesta revisão. O sucessor não precisa acessar a conversa
ou a sessão do produtor para retomar o pacote.

Inspecionei a prancha 1×/8× atual e o recibo terminal, matriz e continuidade.
Conferi hashes da prancha, ROM, vídeo, model sheet e jab v8. Os passes já
registrados de taxa e VBlank da ROM v3 continuam no seu escopo; não executei
outra sessão ou repeti medições porque não houve alteração do binário.

### Parecer de game design e arte

- **Correções atendidas:** TA07 olha para o rival, o colapso para azul escuro
  foi removido e há uma pose de subida da mão. Preservar esses resultados.
- **Mão livre:** o recibo descreve o último deslocamento de 3 px para cima e
  2,5 px para o rival; caixas se tocam. Isso não obriga outro desenho. Também
  não é um critério universal de fluidez: exposição, arco e corpo participam.
- **Continuidade global:** ainda há diferença visível de configuração de cabeça,
  largura e iluminação entre TA06–TA08 e GQ03. Avaliar o bloco na sequência e
  em tamanho nativo; corrigir apenas TA08 pode deslocar a descontinuidade.
  O quadro final isolado não deve ditar uma nova identidade para o personagem.
- **Limite das medidas:** o recibo usa limiar de branco, caixas e larguras por
  porcentagem da altura. Não equivale a medição de articulações/perspectiva nem
  gate artístico homologado. A luva da bengala quase mantém Y, mas o próprio
  recibo mostra mudança em X; não chamar de âncora totalmente imóvel.
- **Decisão de continuidade:** não encomendar mais frames por rotina. Apresentar
  a candidata atual para julgamento artístico, indicando a diferença de corpo/
  material. Se houver correção necessária, harmonizar só o conjunto afetado,
  respeitando fontes de identidade. Não declarar aprovação do dono por inferência.

O pacote mantém 20 linhas `not_started` e sete lacunas visuais na matriz.
Bengala/bota/rapieira permanecem chaves; GQ03 candidata; portraits incompletos;
comandos competitivos em aberto. Os resultados da provocação não aprovam o jab,
a relação entre guardas, a cena 10 ou o duelo. Há produção independente autorizada
para o sucessor continuar enquanto aguarda decisão específica.

### Handoff integral consolidado

O documento [Prompt integral do Dr. Social](dr_social_complete_character_artist_prompt_v1.md)
foi atualizado para substituir o contexto disperso dos prompts de checkpoint.
Contém missão, autoridade, identidade, referências por hash e papel, método,
matriz/ações completas, baseline ROM/vídeo, testes pagos, falhas históricas,
controles pendentes, cena 10, receitas e proteção do WIP.

Há uma dependência real a tratar na retomada: scripts de registro citam imagens
na sessão pessoal `.grok` do produtor. Os originais estão preservados; o agente
novo deve usar esses arquivos/hash e tornar a ingestão reproduzível no helper
existente se necessário. Não depender dos créditos/conta do anterior, criar um
conversor concorrente ou usar geração procedural de anatomia como substituto.

Recibo desta revisão documental/visual:
`out/diagnostics/social_new_agent_handoff_20261102/review_receipt.json`.

## Histórico — revisão dab0181 e pior frame medido, 2026-11-02

**As correções de orientação e azul escuro foram atendidas nas imagens
inspecionadas. A provocação continua candidata; seu passe técnico agora inclui
o VBlank selado deste viewer.** Não tratar tudo como não realizado: separar
esses resultados do aceite artístico, do comando e do personagem completo.

Conferidos SHA da ROM v3 e vídeo, registro de conversão, diff e fonte do build.
ROM `47ab46634198563cdf8788187c5472475c39cc5c310b37dbcdabdcb7cb52bd07`,
32768 bytes. Inspecionei a prancha de retorno e quadros ordenados extraídos do
framebuffer, inclusive o trecho final. TA07 nova olha para o rival e retorna à
família ciano; a TA07 antiga escura/virada permanece apenas no comparativo.
Não confundir a presença da antiga na prancha com sua participação na ROM v3.
TA08 acrescenta uma etapa de recolha da mão, sem ainda aprovar o encaixe final.

### Pendência técnica que esta revisão resolveu

Nova sessão privada do designer `dddf8c438ced42aba3f83c1434664419`, mesma ROM
v3, sem rebuild, sem edição de pixels/código. Self-checks do medidor de pior
frame e do auditor de corredor passaram. O snapshot da fonte em `dab0181`
coincide com o hash registrado no build; o mapa desse candidato passou no
corredor `0xC7D2..0xC7F9`, com folga de 1784 bytes.

`measure_worst_frame.py` rodou 90 s em tempo real sem leituras intermediárias.
Resultado: **PASS**, selo de **3000 frames**, `vline_min=207`, `vovf_delta=0`.
A leitura pós-selo encontrou `done=1` e frame 5424. O único snapshot lê um mínimo
acumulado pela ROM; não significa que só um frame foi medido. Mede o fim do
trabalho VDP instrumentado neste viewer residente; não aprova streaming futuro,
duelo completo, input competitivo ou toda a CPU por frame.

Bundle de framebuffer verificado e sessão encerrada. Recibo:
`out/diagnostics/social_taunt01_cycle_v3_review_20261102/review_receipt.json`.
Relatório:
`out/evidence/sessions/dddf8c438ced42aba3f83c1434664419/worst_frame/taunt_v3_designer_worst.json`.
O rótulo genérico `TITLE` do relatório corresponde ao estado numérico 0; neste
viewer é a guarda. O relatório não contém uma série de estados, e não deve ser
citado como prova de que houve tela de título ou de cobertura individual de poses.

As janelas de taxa do produtor, ligadas a esta ROM, são
59.64763127522857 / 59.62493848380926; conferidas, não repetidas nesta revisão.
Os dois relógios do vídeo estão corretamente separados: 360 quadros, 6.007736 s
codificados, 6.019422882 s de coleta. Não há motivo novo para retestar todas as
janelas ou reabrir o desempenho enquanto não houver mudança/regressão relevante.
Falhas históricas da v2 permanecem. Áudio, pacing percebido e arte seguem separados.

### Próximo julgamento artístico: o terminal, não outra rodada inteira

Nos quadros finais, a passagem TA08→GQ03 ainda troca a configuração de mão,
cabeça e corpo. Verificar a continuidade em tamanho nativo e reprodução normal
antes de pedir outro desenho. Não concluir que falta obrigatoriamente mais um
quadro: pode ser a pose terminal da recolha, sua trajetória, proporção ou exposição.
Aproximar uma dessas causas não autoriza mudar a guarda/jab aprovados por escopo.

A entrada de TA07/TA08 na faixa 72 px resolve a ultrapassagem declarada de 73;
**não demonstra sozinha a constância anatômica entre poses**. O novo original
continua com corpo de 877 px contra 836 da guarda (cerca de 4,9%); a explicação
anterior de deriva uniforme não passa a ser resolvida só por ficar dentro da
faixa. Registrar âncoras comparáveis e distinguir escala/ângulo/postura. Mesma
sola não prova mesma anatomia. Não esmagar poses nem inventar novo limite de
altura por quadro para eliminar movimentos naturais.

Códigos 56/57 pertencem à família de cor usada, mas pertencimento à mesma família
não é aceite automático de luz/material. A mudança grave de azul escuro foi
corrigida; avaliar apenas se resta uma troca perceptível de material no terminal,
sem impor que toda dobra ou área iluminada tenha o mesmo índice. O acabamento
precisa permanecer fiel ao método/model sheet e ser legível no SMS.

Recomendação: fechar essa comparação localizada e apresentar a provocação como
candidata para julgamento artístico com o proprietário. Se não houver defeito
observável no trecho, não gerar frames adicionais por rotina. Se houver, corrigir
só a causa, medir o delta e recapturar no novo SHA. O pacote continua incompleto;
portraits independentes podem avançar sem chamar este checkpoint de aprovação.

## Histórico — revisão do incremento f4c5043 e QA do designer, 2026-11-01

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

## Prompt vigente para agente substituto

Use o [prompt integral atualizado](dr_social_complete_character_artist_prompt_v1.md),
da seção **Prompt** até o fim. Ele reúne o contexto necessário para um agente
novo e substitui os prompts incrementais desta página. O contrato da cena 10
acima continua vigente; os pareceres anteriores ficam como histórico e evidência.
