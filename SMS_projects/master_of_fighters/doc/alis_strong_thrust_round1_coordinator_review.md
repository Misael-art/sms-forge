# Parecer de coordenação — estocada forte de Alis, rodada 1

**Estado da entrega: parcial.** A tarefa do artista está ociosa após uma
resposta final que reconhece a interrupção. A entrega contém duas folhas
exploratórias e um README com prompts, hashes e limites. A etapa encerrou
na revisão dos estudos. A [missão](alis_strong_thrust_round1_agent_prompt.md)
pedia uma candidata acionada pelo botão 1 segurado, com Hayato na tela.

## O que foi produzido e aprovado para reaproveitamento

Inspeção visual de [study_01](../data/source_art/sprite_studies/alis/strong_thrust_round1/study_01.png)
e [study_02](../data/source_art/sprite_studies/alis/strong_thrust_round1/study_02.png).
A leitura estática da estocada é mais forte na terceira pose. O braço e a
lâmina formam uma direção clara, o tronco avança e o joelho dianteiro recebe
visualmente o peso. A guarda com escudo e as cores principais identificam
Alis. A sequência de cinco posições serve de rascunho de atuação. A segunda
tentativa retirou a linha de chão aparente. O
[registro do artista](../data/source_art/sprite_studies/alis/strong_thrust_round1/README.md)
preservou as duas tentativas e reconheceu as pendências.

## Correções em ordem de prioridade

1. **Escala e apoio.** O tórax e o escudo em guarda ainda abrem em
   três-quartos, mesmo com o rosto voltado para a luta. Faltam pivô e eixos
   marcados e comparação com a guarda de Hayato no mesmo chão. A altura
   de pé da régua v2 calibra o corpo em postura neutra. Compare os segmentos
   corporais quando a Alis flexiona, sem ajustar cada quadro pela borda
   do cabelo ou dos pés.
2. **Espada e escudo.** Na segunda pose, a espada cai para trás perto da
   perna de apoio. Teste a saída dessa posição até a linha horizontal da
   terceira pose pela trajetória de mão, base e ponta. A espada parece
   encurtar na preparação e alongar na guarda, sem âncoras para distinguir
   perspectiva de deriva. Na extensão, o escudo se fecha quase de perfil
   e o encaixe no antebraço perde leitura. Compare a arma com a katana em
   vista equivalente e faça o vínculo do escudo com o braço legível.
3. **Recorte.** Sobram franjas vermelhas junto às pernas e ao braço na
   preparação e ciano/azul perto da lâmina. Os dois PNGs são RGBA
   2172 × 724 com 256 níveis de alfa. Em `study_01`, 433.843 pixels são
   semitransparentes e 153 totalmente opacos. Em `study_02`, são 402.259
   e 649. A extração existente pode binarizar o alfa por um limiar
   declarado e o adaptador espera PNG indexado com índice 0 transparente.
   A correção deve se dar na fonte e ser revisada em 1× e 4× em fundos
   diferentes. Um limiar sozinho não resolve cor contaminada, desenho ou
   escala.
4. **Ritmo e retorno.** A mão retorna na quarta pose, mas a folha estática
   não permite julgar velocidade, leitura da recolha ou o assentamento
   em guarda. Cabelo e roupa conservam um desenho de movimento semelhante
   em várias chaves. Verificar a sequência temporizada antes de acrescentar
   desenhos. Separar efeito de exposição de salto anatômico.

## Conferência de implementação

O diff de [src/main.c](../src/main.c) traz a placa de fundo e HUD da Cena 01
para J.J./Social. No visualizador existente, a ação dispara pela borda de
pressão do botão 1 e também por autoplay. Nenhum seletor, contrato de
poses ou manifesto de build da Alis foi encontrado. No checkout, não há
fonte nativa da rodada, integração com Hayato, comando segurado, teste
de distâncias, ROM candidata ou evidência Emulicious da estocada. A
validação de fluidez, contato, recursos, pior quadro e FPS permanece pendente.

## Encaminhamento

Retomar a mesma rodada. Usar `study_02` como thumbnail do gesto e resolver
primeiro guarda e extensão máxima com uma fonte autoral limpa em vista
lateral. Conferir o par com Hayato e a rigidez dos equipamentos antes de
produzir o restante. A partir dessas duas chaves, continuar na mesma tarefa
até temporizar a sequência, integrar o comando segurado, compilar e
validar a ROM. O próximo marco de coordenação é o pacote do brief com
as evidências no mesmo SHA.

## Retomada — segunda revisão independente

**Entrega parcial, ainda sem candidata.** O produtor encerrou novamente
após trabalho exploratório. Nesta retomada deixou quatro PNGs adicionais
com prompts e hashes. A comparação do diff confirma que o delta de
runtime continua restrito à Cena 01 de J.J./Social. O produtor reportou
uma VM concorrente e CPU PSI avg10 de 34,83%. Adiar carga pesada
preservou o host. O comando, o contrato temporal e o registro de poses
também ficaram pendentes. Essas frentes ainda tinham passos leves
independentes da build e da sessão Emulicious.

### Implementação e qualidade artística

| Prova inspecionada | Acerto | Problema que define a próxima ação |
|---|---|---|
| [Duas chaves](../data/source_art/sprite_studies/alis/strong_thrust_round1/keyposes_01.png) | A leitura é mais lateral e a extensão mantém a linha do ataque. A diferença entre guarda e extensão aparece no apoio dianteiro. | Falta registro com Hayato na mesma escala. A mão do escudo fica encoberta na extensão, mas a oclusão por si é compatível com a pose. Falta demonstrar onde o escudo prende e como gira. |
| [Edição do escudo](../data/source_art/sprite_studies/alis/strong_thrust_round1/keyposes_02_shield.png) | A pega e a tira ficaram legíveis. | A edição virou o escudo para mostrar grande parte do interior e introduziu material marrom e ferragens que a referência ainda não justifica. A revisão também mudou pixels na área da guarda que o prompt pedia preservar. |
| [Sequência inicial](../data/source_art/sprite_studies/alis/strong_thrust_round1/sequence_01.png) e [sequência com edição](../data/source_art/sprite_studies/alis/strong_thrust_round1/sequence_02_shield.png) | O gesto principal continua legível quadro a quadro. A última tentativa leva a pega visível à extensão. | O interior marrom segue na terceira pose e o recorte continua contaminado de vermelho, cinza e azul. A guarda tem franja cinza entre rosto e lâmina, e a preparação tem azul além do fio. A preparação e a extensão também exigem trilha de mão/base/ponta para explicar a mudança aparente da lâmina. |
| Par lateral, sequência temporizada e ROM | Há referência de corpo e guarda de Hayato para a checagem. | Faltam a composição comparada no mesmo chão, fontes nativas, contrato e reprodução da sequência, comando segurado e rearme, três distâncias, duas faces, build, evidência Emulicious e medidas de pior frame e FPS. |

Os quatro PNGs mantêm 256 níveis de alfa e entre 322.388 e 442.130 pixels
semitransparentes. Na edição das chaves, contei 48.724 pixels com diferença
superior a 16 em pelo menos um canal RGB na área da guarda. Medição na
composição sobre cinza `#a6a6a6`, comparação no canvas original, área
`0 ≤ X < 750`. Para a extensão foram 76.667 pixels. As duas sequências
também têm diferença nos cinco intervalos horizontais. As contagens
capturam mudanças de cor, borda e deslocamento. A revisão de preservação
deve alinhar pelo pivô e observar a região fora da máscara da edição.

Para perseguir o nível de acabamento pedido, avaliar em tamanho nativo
a legibilidade da expressão, o peso do apoio, a nitidez da saída em
contraste com a recuperação, a continuidade de lâmina e o assentamento
de cabelo e roupa. Na folha atual, o cabelo mantém uma direção muito
semelhante na guarda e no esforço. É uma questão de revisão temporal
observar se o cabelo acompanha com atraso e se assenta no retorno. Uma
prancha estática permite levantar essa questão. O parecer de ritmo,
velocidade, resposta e fluidez requer reprodução contínua.

**Correção de eficiência para testar:** reaproveitar a direção do gesto
e trocar de método para arte localizada, com duas chaves registradas antes
da expansão. Corrigir desenho e máscara nas regiões afetadas e preservar o
restante. Usar a transparência, a leitura em 1× e a comparação com Hayato
para decidir se as chaves sustentam a sequência final. Testar a coreografia
em um esboço temporizado antes do pixel final. Medir o retrabalho em
tentativas por correção fechada, chaves reaproveitadas e deltas por pose.
O benefício desse método ainda precisa ser observado na próxima execução.

### Coordenação, auditoria e verificação

| Oportunidade do coordenador | Ajuste a experimentar |
|---|---|
| Pedi que o escudo ficasse legível na extensão. A formulação permitiu tratar a visão da mão e da tira como objetivo isolado, inclusive girando e redesenhando a peça. | Pedir uma vista de construção que demonstre fixação e materiais e uma pose que conserve essa construção. Aceitar oclusão coerente em ação. Fixar quais regiões e materiais devem ser preservados e conferir visualmente o antes/depois com a pose registrada. |
| Pedi duas chaves primeiro, mas não deixei explícito qual evidência permitiria liberar a folha. Também não apontei o teste de pixel alterado fora da região solicitada. | Para liberar a sequência, exigir como resultado do próprio trabalho o par em 1×/4× na mesma escala de Hayato, apoios marcados, leitura em fundos claro e escuro, comparativo de arma/escudo e uma checagem documentada das regiões preservadas. Se a mesma falha voltar, mudar o método de correção. |
| O comando final deixou a implementação do botão depois da arte. O bloqueio do host para build acabou acompanhado de uma entrega sem a parte leve de integração. | Informar no comando as dependências reais. Desenvolver contagem de pressão, ação única e rearme no consumidor candidato e preparar os casos de entrada enquanto a arte avança. Reavaliar recursos antes de build e QA. Uma parada exige identificar as ações independentes que ainda podem avançar. |
| A primeira auditoria já apontava perspectiva e recorte. Faltou conferir quantitativamente o delta de uma edição localizada e identificar como a recuperação seria julgada. | Na revisão seguinte, vincular por hash o material antes/depois, examinar a pose alinhada e as regiões que deveriam estar preservadas. Ver a sequência contínua normal antes do stepping, usar o lento para localizar o defeito e verificar a mesma passagem na ROM candidata. Declarar a modalidade de cada observação. |

Para a curadoria, estas propostas entram como aplicação de
`art-review.md` e `sms-sprite-animation.md` ao caso. Há regras existentes
de revisão por delta, continuidade de equipamento e checkpoint temporal.
A pergunta para a próxima rodada é se instruções mais operacionais e
provas no ponto de decisão reduzem retrabalho e melhoram o resultado.
Conservar no registro os dois eixos de aprendizado e a evidência que
confirmar ou contrariar cada hipótese.

### Próximo direcionamento

Corrigir localmente guarda e extensão com base nas chaves existentes.
Mostrar construção do escudo em estudo próprio e conservar material,
contorno e encaixe no movimento. Registrar o par à mesma escala de Hayato.
Quando as chaves passarem, testar o rascunho em velocidade normal e lenta,
com durações declaradas. Refinar peso, aceleração e recuperação antes de
expandir o acabamento. Em paralelo leve, implementar o comando do piloto
e preparar os casos que distinguem limiar, pressão longa e rearme.
Continuar até a candidata e as evidências do brief quando o host permitir,
mantendo o parecer artístico separado dos resultados técnicos.

## Retomada — terceira revisão independente

**Avanço no código e na prova de processo. Candidata ainda pendente.** A
tarefa encerrou com um ramo de entrada, roteiro de QA, duas versões de
esboço temporal e dois estudos de arte. O checkout continua sem fonte
nativa aprovada da Alis, par registrado com Hayato, configuração de build
da Alis, medições de contato, ROM ou evidência Emulicious. O produtor
preservou a VM concorrente e executou parte do trabalho leve que tinha
ficado pendente antes.

### Código do botão

Revisei o ramo experimental de [main.c](../src/main.c). Extraí o bloco
`MOF_ALIS_STRONG_HOLD` e a atualização de poses para um teste de bancada,
compilado em C99 no host com durações de fixture
`[0, 7, 3, 6, 12]`. Passaram guarda em repouso, toque breve, 11/12/13
leituras, pressão longa além da recuperação, soltura e reentrada, limiar
durante a recuperação e volta do contador de disparos de 255 para zero.
Conferi também a fronteira em que o limiar cai na última leitura da
recuperação. O código consome a pressão antes de voltar à guarda e exige
soltar outra vez. Esta é uma decisão de resposta do piloto a validar em
uso, com caso próprio no [roteiro de QA](alis_strong_thrust_round1_qa.md).

Há uma lacuna de observabilidade. No ramo normal, `C7F9` guarda o tempo
decorrido da pose. Com o seletor, passa a guardar o tempo de pressão. Após
o disparo, a sonda pode ficar em 12 enquanto a animação avança. Para
verificar comando e exposição no mesmo SHA, conservar as duas grandezas
em campos próprios, documentar o significado e verificar corredor e
`.map`. O seletor ainda pode acionar o pacote histórico escolhido pelo
manifesto. A build candidata precisa ligar os sprites da Alis e Hayato.

O limiar de 12 leituras equivale a cerca de 200 ms a 60 leituras/s. Se
forem mantidos os 7 ticks de preparação do esboço, o orçamento nominal
até a extensão fica perto de 0,3 s. Na candidata, medir e julgar
separadamente aperto → reconhecimento, reconhecimento → início visível
e início → extensão. O teste de bancada prova as transições do C com
entrada simulada. SDCC, render, controles, tempo de parede e FPS continuam
pendentes de build e sessão no alvo.

### Esboço temporal e arte

Decodifiquei o MP4 normal e conferi as cinco imagens do primeiro ciclo.
São 144 quadros de 150 × 180 a 60 quadros/s, quatro ciclos de 36. As
mudanças no primeiro ciclo ocorrem nos quadros 0, 8, 15, 18 e 24,
confirmando 8/7/3/6/12. O esboço lento tem 575 quadros e preserva a ordem
das imagens. Trata-se de inspeção quadro a quadro do esboço.

Na faixa dos 9 pixels inferiores do personagem, usando pixels com canal
RGB máximo ≥64 para localizar os extremos, estes foram os limites no
primeiro ciclo:

| Pose | Quadro | X esquerdo / X direito |
|---|---:|---:|
| Guarda | 0 | 40 / 112 |
| Preparação | 8 | 38 / 115 |
| Extensão | 15 | 11 / 101 |
| Recolha | 18 | 27 / 100 |
| Guarda final | 24 | 36 / 109 |

O Y inferior fica em 153 nas cinco poses. A preparação → extensão
desloca os dois limites dos apoios para a esquerda (−27 e −14 px no
vídeo), com a estocada voltada à direita. A guarda final → inicial
também salta 4 e 3 px nos respectivos extremos. Essa é a apresentação do
vídeo montado com recortes de larguras diferentes, centralizados sem
pivô. Registrar as poses pelo mesmo apoio/pivô, com deslocamento separado
e declarado, e usar a mesma guarda ao fechar o ciclo. Só depois julgar
deslizamento do desenho, velocidade percebida, alcance e recuperação.

Abri também a edição local e o estudo de construção. A edição manteve a
franja cinza entre rosto e espada e alterou áreas internas que o prompt
pedia preservar. O registro do produtor mede 46.399 e 44.991 pixels
alterados nas duas regiões do canvas sob o mesmo critério de composição
em cinza da revisão anterior. O estudo do escudo mostra face, borda e
tira em vistas próprias. A face e o contorno são úteis para a comparação.
O interior e a tira permanecem hipótese. A arte desta retomada ainda não
tem uma chave fechada para conversão.

### Próxima ação e lições para curadoria

- **Execução.** Trocar regeneração global por edição que restrinja a
  alteração à região, com pixels externos preservados, ou por redesenho
  autoral das chaves se o recorte contaminado dominar a fonte. Resolver
  duas chaves comparadas com Hayato e recompor o esboço com pivôs antes
  de alterar timing ou acrescentar poses. Separar as sondas de tempo de
  pose e de pressão. Ligar a build à Alis e avançar para a mesma ROM.
- **Coordenação.** Repeti a ordem «corrija localmente», mas deixei a
  escolha do mecanismo implícita depois de já ter visto a edição
  generativa alcançar a guarda. Na próxima atribuição, pedir máscara
  testável ou redesenho delimitado. Também pedi um esboço normal/lento
  sem dizer que registrar o pivô era precondição para julgar a passagem.
  Pedir primeiro um recorte comum ancorado, depois a reprodução e
  os tempos por pose. A checagem de comando deve pedir também a fronteira
  no último tick de recuperação e distinguir início da pressão, disparo
  e apresentação.
- **Auditoria.** Antes de dar parecer de fluidez, verificar se o próprio
  instrumento de prévia preserva referências espaciais. Medir primeiro
  a continuidade do enquadramento, depois observar o movimento normal.
  Validar a semântica de cada sonda e exercitar a lógica em bancada cedo
  quando não houver ROM. Manter identificado o limite da prova de bancada.

## Retomada — quarta revisão e direcionamento de produção

**Resultado parcial: o registro do esboço melhorou e as sondas foram
separadas; a arte e a candidata permanecem pendentes.** Revistos o código,
receitas, recibo de máscara, pranchas e quadros extraídos do esboço. A
inspeção de quadros não equivale a assistir ao movimento contínuo.

### O que mudou e o que a prova sustenta

- **Máscara.** A fonte `keyposes_01` é reaproveitada; a edição altera 2.224
  pixels com alpha 1–24, sem mudança fora da máscara declarada. Isso sustenta
  preservação de bytes externos, não qualidade do contorno. Nesta auditoria,
  binarizei o alpha antes e depois nos limiares 25, 64, 128 e 224: em todos,
  a diferença foi zero. Portanto, se a extração escolher um desses limiares,
  essa edição não muda sua máscara binária. Em composição sobre preto ou cinza
  `#a6a6a6`, nenhum pixel mudou mais de 16 por canal; sobre branco, dez pixels
  mudaram mais de 16. Não está demonstrada a correção visual do defeito na
  fonte convertida. Avaliar com a receita efetivamente escolhida, em 1×/4× e
  fundos distintos; corrigir contaminação que sobreviva à conversão usando
  máscara material específica ou redesenho delimitado. Preservar antes/depois.
- **Registro do movimento.** O esboço normal usa a mesma guarda no início e
  fim e as exposições 8/7/3/6/12. A âncora é o centro estimado do apoio
  traseiro, não um pivô anatômico medido. Pelos extremos inferiores reportados,
  a transição preparação→extensão passou de −27/−14 para −1/+12 px. Isso
  mostra que o enquadramento deixou de deslocar ambos os apoios para trás;
  não autentica a física do pé nem prova fluidez. O avanço do pivô foi fixado
  em zero para diagnóstico; não concluir que esse seja o deslocamento final.
  A sequência continua a de `sequence_01`, não as chaves mascaradas.
- **Comparação de escala.** As pranchas 1×/4× compartilham o chão e usam a
  guarda convertida v7 de Hayato. Alis foi reduzida por um fator provisório
  de 1/10 e os apoios são estimativas. Na comparação, a cabeça de Alis
  aparece mais alta, mas o fator e a diferença de postura impedem concluir
  que a proporção corporal 1:1 esteja correta ou incorreta. Calibrar por
  segmentos e referência neutra de 68 px, sem normalizar cada pose pelo
  contorno equipado; então reaplicar um único fator a toda a sequência.
- **Entrada.** `C7F9` volta a guardar `elapsed` e `C7FC` a pressão;
  `C7FA/FB` mantêm latch/contador. O gate de marcadores `volatile` passou
  estaticamente. A bancada relatada anteriormente exercitou o ramo antes da
  separação; não comprova compilação SDCC, endereços no `.map`, sincronismo
  da imagem ou o comportamento da nova ROM. Há uma decisão de resposta a
  medir: o limiar na última leitura da recuperação é consumido atualmente.
  Medir em alvo e registrar a escolha sem alterar silenciosamente o normal
  fraco. Expor pressão, pose e contador simultaneamente e observar a latência
  aperto→disparo→primeira pose apresentada→extensão.

### Direcionamento para a implementação

1. Estabelecer a escala em corpo neutro por referências e segmentos
   registrados; corrigir guarda e extensão com máscara verificável ou
   redesenho delimitado. Comparar com Hayato no mesmo chão, 1×/4×, com
   apoios, pivô, mão, base/ponta e escudo; conferir antes/depois em fundos
   claro e escuro e na saída que será convertida. A vista de construção do
   escudo é hipótese e a mão pode estar naturalmente encoberta.
2. Reaplicar essa escala e o registro por pose. Assistir ao esboço normal;
   usar o lento e trilhas de mão/base/ponta para localizar saltos. Refinar
   desenhos ou exposições conforme o defeito observado; manter a mesma
   guarda na volta. Não tratar o recuo reduzido do enquadramento como aceite
   da atuação. Conferir as provas no framebuffer da candidata.
3. Integrar as fontes nativas e a guarda v7 ao conversor e consumidor
   existentes. Implementar seleção das três distâncias e duas faces, janela
   ativa e leitura de alcance; medir projeção à altura do tronco e distinguir
   colisão real de diagnóstico geométrico. Auditar P1, SAT, scanline, VRAM,
   corredor e pior frame, inclusive degrau seguinte.
4. Reavaliar o host antes de build/QA. A VM de outro trabalho continuava
   ativa na auditoria, e a tentativa anterior do wrapper recebeu conexão de
   áudio recusada e ausência de `pulseaudio`. Não encerrar processos alheios,
   nem usar o desktop como fallback; investigar a rota oficial e continuar
   o trabalho leve independente. Quando o ambiente permitir, usar Emulicious
   privado com SHA e sessão, cobrir as fronteiras e latências, três distâncias,
   duas faces, FPS funcional §133 e cleanup. Entregar fontes, configuração,
   ROM, SHA, instruções e evidências, sem promover resultado pendente.

### Oportunidade para coordenação e auditoria

Pedir uma máscara preservada foi útil, mas faltou exigir que a operação
alterasse o resultado observado no domínio de consumo. Daqui em diante,
comparar simultaneamente delta fora da área e efeito na saída convertida,
sem tratar contagem de pixels como aprovação de arte. A âncora deve distinguir
apoio, pivô e avanço; o ponto de aceitação do timing é a sequência em execução,
não a estabilidade de um extremo. Um bloqueio de host não encerra o trabalho
leve: integrar e preparar evidências onde for seguro, sem chamar uma ROM
inexistente de candidata. Essas são hipóteses de processo para este caso,
não promoção de doutrina ou de ferramenta global.

## Quinta revisão — redesenho, composição e integração (2026-11-16)

**Entrega parcial com integração diagnóstica preparada.** Conferi o
[manifesto](../.mddev/alis_strong_round1_diagnostic_build.json), o
[consumidor](../src/main.c), as novas chaves em 4×, o antes/depois da
franja e a projeção de distâncias. Não há ROM da Alis no checkout. O
registro do produtor e a inspeção desta rodada concordam sobre a ausência
de build e QA. As cópias incrementais locais de redesenho, alcance e
reprodução do split conferem com os três SHA-256 informados na memória.

### Parecer de arte e escala

- **O redesenho tem mérito.** Há uma expressão mais decidida na guarda,
  esforço no rosto na extensão, apoio traseiro legível e uma linha de
  ataque clara. O escudo mantém a face reconhecível e aceita a oclusão
  natural. O registro pelo chão já permite cotejar as figuras. É um par
  de chaves, ainda sem antecipação e recolha desse mesmo desenho.
- **A proporção do elenco continua aberta.** Na prancha convertida,
  Alis ainda lê pequena ao lado de Hayato, sobretudo pelo corpo estreito
  e pelo peso das pernas na extensão. Medi o PNG: 51 px de silhueta da
  Alis em guarda e 46 em extensão, ambos até a mesma linha de chão do
  rival. A referência de Hayato chega a 66 px com a katana e 58 até a
  coroa em guarda. São alturas visíveis de poses equipadas, com flexões
  diferentes. Os 68 px da régua pertencem à referência neutra do corpo.
  Antes de redimensionar, feche os pontos de ombro, quadril, joelho e
  tornozelo no neutro e confira seu reaproveitamento nas chaves. As
  estimativas de segmentos e lâmina dão uma pista útil de onde olhar.
  Elas pertencem a `sequence_01` e a marcações visuais, não ao redesenho.
  Compare também mão, base e ponta em vistas compatíveis com a katana.
- **A limpeza localizada agora fez diferença na conversão.** Com a
  paleta de materiais fixa, o antes/depois registra um pixel cinza
  removido na guarda, com extensão e Hayato idênticos. A comparação do
  detalhe mostra o espaço entre rosto e lâmina. A paleta automática
  anterior tinha mudado cores fora da área. Guardar a receita fixa como
  controle e limitar a conclusão ao pixel e às chaves dessa comparação.
  O cabeçalho do piloto vem de outra sequência. Esse ganho não a corrige.

### Verificações independentes e seus limites

| Eixo | Resultado |
|---|---|
| Identidade da build | `MOF_ALIS_ROUND1` inclui o cabeçalho de `grounded_faces_assets_probe`, derivado de `sequence_01`. O redesenho, o comparativo de franja e o piloto são três conjuntos distintos. |
| Dados do piloto | Self-checks do simulador e do verificador de dados passaram. Reexecutei a reconstrução do cabeçalho e a checagem das 24 cenas: dez metasprites, quatro mapas BG, 246 padrões de sprite, 14 BG e um de HUD, pico 53 na SAT e 8 por linha. É uma prova estática. |
| Redesenho só em sprites | Reexecutei o gate de scanline. Extensão com 51 objetos, pico 9 e oito linhas em overflow. As linhas 104–108 já têm descarte visível. O relatório da busca das fases registra zero soluções na posição/orientação testada. Encerra essa hipótese nessa configuração. |
| Redesenho com fragmento em BG | Separei a avaliação do orçamento da visibilidade. O gate repete 50 objetos, pico 8, zero overflow para a extensão nessa posição. O recibo registra 12 pixels da ponta transferidos e reconstrução de índices exata antes de considerar a camada do rival. |
| Alcance e prioridade | Recalculei a composição à direita com o fundo atrás de Hayato. Na linha do ataque, a ponta geométrica do piloto é X=119 e se vê até X=116/118/119 perto, no limite e fora. Para o redesenho é X=115 e se vê até X=111/114/115. São perdas previstas de 3/1/0 e 4/1/0 px. No redesenho só há espelho offline à esquerda. Os indicadores de alcance calculam o contorno inteiro. O contato real continua pendente. |
| Entrada | Reexecutei o teste do coletor com ponte simulada. Passou checagem de offsets e amostras inválidas, ordem, soltura e interrupção. O código mantém sondas próprias para pressão e exposição de pose. Ainda faltam link, corredor, estados da ROM, fronteira do último tick e latências percebidas. |
| PNT e tempo de quadro | Os mapas atuais de preparação e extensão têm 5 e 2 células por face. A transição preparação → extensão, com mudança de HUD, executa 13 escritas na PNT pelo fluxo atual (5 limpezas, 2 novas células, 6 do HUD), além da SAT. Esta contagem deriva do C e do cabeçalho. Limites de entradas dinâmicas, pior quadro e FPS não foram pagos. |
| Host | A CPU ainda tinha PSI some avg60 de 11,24% na amostra de revisão. É uma fotografia atual, não prova de quando haverá margem. O desvio de áudio foi resolvido pelo produtor na rota já existente; reavaliar condições antes de cada operação pesada. |

**Decisão.** Conservar o piloto para investigação técnica e o redesenho
para continuidade artística. A técnica da lâmina em BG tem ganho real de
ocupação estática e uma perda de apresentação mensurável no modelo de
camadas. Continua candidata apenas como experimento. O critério para
escolher representação é a lâmina e o rival completos ou uma oclusão
artisticamente coerente durante o contato, nas duas faces e três
distâncias, no framebuffer da ROM. O pico de oito não resolve isso.

### Execução, coordenação e auditoria

- **Execução.** Reaproveitar a integração, o registro de chão e a receita
  de correção com paleta fixa. Fechar a escala neutra e as quatro fases
  artísticas com o mesmo desenho. Concentrar a análise de ocupação nas
  linhas que descartam pixels e testar uma intervenção com ganho
  verificável. Classificar as 32 configurações e os 19 auxiliares atuais
  como evidência ou caminho ativo. Destacar uma rota reproduzível para
  o piloto e outra para a arte em revisão, preservando o histórico.
- **Coordenação.** O comando anterior deixou ambíguo quais fontes
  comprovavam cada avanço. Isso permitiu que o teste da máscara, o
  redesenho e o código parecessem etapas de uma mesma entrega. Pedir uma
  cadeia de identidade fonte → conversão → cabeçalho → manifesto → ROM,
  com a fonte dessa build no próprio roteiro de QA. Também faltou tornar
  explícito o que é oclusão aceitável no contato. Pedir na mesma
  checklist contagem por linha e integridade visível de lâmina e rival,
  com comparação de camada nas transições.
- **Auditoria.** Verificar o que a build realmente inclui antes de
  generalizar um bom resultado local. Separar alcance medido a partir do
  pivô de cena de deslocamento do pé de apoio, e contorno de alvo de
  resposta de combate. Conferir geometria de camada nos pixels da janela
  ativa, depois medir os mapas escritos e as apresentações no alvo.
  Fazer os testes baratos de entrada, animação registrada e composição
  cedo. O fechamento continua sendo a mesma ROM observada, com prova de
  input, três distâncias, duas faces, retorno, pior quadro e cada janela
  válida ≥58 FPS. Depois cabe o julgamento artístico na velocidade normal.
