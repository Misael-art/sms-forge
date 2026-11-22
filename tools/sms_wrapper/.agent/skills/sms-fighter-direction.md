# Direção de personagem jogável e balanceamento de elenco

Use para transformar identidade e lore em movimento reconhecível e decisões
de combate testáveis no Master System. Combine com [animação de sprites](sms-sprite-animation.md)
para desenhar e com o [fluxo de produção de lutador](../workflows/playable-fighter.md)
para executar. Registre as escolhas nos documentos do consumidor.

## Construir a ficha a partir do model sheet

| Parâmetro | Como extrair e usar | O que comparar na revisão |
|---|---|---|
| Identidade | Fixar a fonte do jogo, versão do sheet, vista de luta e três sinais visíveis a 1×. Escolher ao menos um que sobreviva ao espelhamento. Documentar a mão que empunha a arma ou a convenção de troca de mão. | Neutro, pose mais fechada e extensão, de ambos os lados. Um revisor localiza cada sinal na imagem. |
| Construção | Medir sola→topo anatômico na pose de calibração. Registrar à parte cabelo, arma e roupa. Marcar chão, quadril, ombro, cotovelo, joelho, punho e ponta do equipamento na vista de luta. | Sobrepor guias ao desenho autoral. Comparar comprimentos aparentes na mesma vista e justificar encurtamento por perspectiva. |
| Estilo comum | Fixar baseline, escala do grupo, direção da luz, convenção de contorno, rampa por material, tratamento de mãos/rosto e densidade de detalhes. Usar um par aprovado como régua. | Prancha lado a lado com o oponente e fundo real, em 1× e nearest-neighbor. Medir proporção segundo o GDD e rever agrupamentos de pixels na região problemática. |
| Atuação própria | Extrair um verbo da lore, uma intenção de jogo e uma oposição visível. Exemplo de estudo: alguém que mede a distância mantém o tronco contido na guarda e avança o quadril na decisão. | Exibir os dois lutadores em silhueta durante o mesmo verbo. Pedir que o revisor indique onde muda a intenção e qual gesto distingue cada um. |
| Função no duelo | Descrever a distância confortável, como entra e sai dela, qual ameaça cria e qual escolha do rival a vence. Associar ao GDD a limitação escolhida. | O rival consegue executar a resposta na tela e no tempo disponíveis? Registrar a tentativa, a distância e o resultado. |

Guarde uma pose de referência aceita e o mesmo fundo para comparar revisões.
Quando uma pose larga estourar o orçamento, localize a linha e os dois atores
envolvidos. Explore redistribuição de formas, composição ou residência na mesma
escala. Se uma alternativa mudar a arma, alcance, anatomia ou papel prometidos,
volte ao contrato correspondente.

## Do concept ao sprite que aguenta movimento

Quando a personagem parece encolher, compare a guarda, o ataque em voo,
a queda diagonal, o repouso e a levantada à mesma escala. Marque quadril,
cabeça, mão que empunha e linha do chão. Meça corpo e equipamento também
depois da conversão. Se a largura máxima de um quadro comprimir toda a
anatomia, ajuste a composição do metasprite e volte a medir o par na
scanline mais carregada. Reavalie o alcance da caixa após mover a lâmina.

Se o traje clarear ou a mão sumir, localize a primeira divergência entre
arte autoral, imagem indexada, padrões empacotados e pixels no emulador.
Amostre as regiões de tecido, pele, bracelete e metal em cada traje e face.
Uma paleta física idêntica ainda permite quantizar tecido no índice branco
do metal. Preserve o contorno pintado ao reduzir a imagem e reveja a mão
no tick ativo. Compare a cabeça apoiada no chão, a primeira elevação e
o apoio do joelho em sequência, com o mesmo referencial de chão.

Antes de reutilizar um desenho, associe o hash do model sheet aprovado
à pose e registre o papel da referência intermediária. Para confirmar a
presença de um material, delimite uma região na pose e calibre o piso com
um exemplo correto e outro com o defeito. Em `audit_sprite_cutout.py`,
uma região pode declarar `"minimum_pixels_by_rgb": {"#000055": 9}` além
de `allowed_rgb`. O exemplo do peitoral de Alis usa índigo e uma janela
registrada no tronco. Aplique um contrato por pose ou grupo com a mesma
janela anatômica. O teste conta pixels opacos da cor declarada no PNG
indexado. Quando parte do punho ou equipamento vier do fundo, faça a medida
na imagem composta com os sprites. Confira a separação da arma, a anatomia
e o recolhimento a 1× no framebuffer. O caso de calibração e o limite
da medição estão na [curadoria de pouso e materiais](../../../../doc/curation/2026-11-22_alis_pouso_e_puxada.json).

1. Recorte a vista de referência autorizada e fixe o fator de escala para a
   sequência inteira. Na grade de trabalho, desenhe chão e eixo local. Reserve
   margem para a maior extensão e guarde as guias em camada separada.
2. Bloqueie cabeça, caixa torácica, pelve, extremidades e equipamento em
   massas legíveis. Compare a sombra plana da guarda e da ação. Se punho,
   lâmina e tronco se fundirem, abra o espaço negativo ou mude a sobreposição
   na chave; observe a solução no tamanho nativo e junto ao rival.
3. Atribua a cada material a rampa que lhe cabe na paleta compartilhada.
   Confira luz e sombra em grupos de pixels contíguos. Teste o rosto e a mão
   contra o torso, oponente e fundo da cena. No SMS, P1 usa índice 0
   transparente e comporta até 15 cores úteis; a paleta usa códigos de 6 bits.
4. Sobreponha a pose anterior e a seguinte em camadas de estudo. Confira
   arco da mão, comprimento da arma, posição da sola e continuidade de cada
   grupo de luz. Um brilho que salta entre poses pode parecer um objeto
   separado durante a reprodução. Corrija na camada autoral e reveja o loop.
5. Exporte a fonte aprovada com IDs, ordem, pivôs e transparência explícitos.
   Preserve a versão editável, o PNG indexado e a tabela de conversão com
   seus papéis. Guias, texto e onion skin ficam fora do raster final. Use o
   conversor para representar o desenho aprovado; toda correção de identidade
   ou gesto retorna à fonte autoral. Código pode gerar diagramas e medir
   pixels; personagens e cenários finais exigem a proveniência artística da fábrica.

## Animar a movimentação que liga os golpes

- **Guarda e respiração.** Defina o apoio dominante, o que sobe, o que atrasa
  e o que permanece legível na silhueta. Veja a emenda da última exposição à
  primeira e a saída da guarda em diferentes pontos do ciclo.
- **Avanço, recuo e parada.** Na folha de trabalho marque contato, absorção,
  passagem e próxima colocação do pé. Durante apoio, some posição do ator e
  posição local do pé. Deriva sem deslocamento autorizado denuncia patinação.
  Compare o avanço no mundo com o comprimento do passo. No recuo, desenhe a
  proteção e a redistribuição de peso que o personagem usaria para se afastar.
- **Abaixar, saltar e pousar.** Marque compressão, saída do chão, ápice,
  primeiro contato e absorção. Ligue a trajetória desenhada à trajetória
  inteira/Q8.8 da lógica. Em interrupção por golpe, teste a altura e o
  novo estado; na aterrissagem, observe o primeiro tick de controle.
- **Executar e reagir.** Desenhe primeiro as chaves em silhueta no tamanho
  final. Marque quem conduz, o apoio, o arco do punho ou arma e o ponto em
  que o defensor entende a ameaça. Acrescente o desenho de passagem onde
  a trajetória se perde. Faça o acabamento de rosto, volumes, luz e material
  só após ver a sequência correr. Faça o defensor responder ao lado e à
  direção do contato previstos. Desenhe bloqueio, dano e recuperação como
  decisões corporais distintas.

Reproduza em velocidade normal, depois em câmera lenta e quadro a quadro.
Uma pausa desenhada pode vender peso enquanto o jogo continua lendo comandos.
Anote separadamente exposição, hitstop, interrupção e próximo tick de controle.
Conserve como controle a combinação aceita de desenhos **e exposições**.

## Comparar golpes sem homogeneizar o elenco

Compare movimentos de **função equivalente** na mesma situação: interrupção
curta, controle de espaço, punição, aproximação ou defesa antiaérea conforme o
GDD. Em cada ficha use o mesmo relógio e a mesma origem espacial.

| Registrar para A e B | Convenção operacional |
|---|---|
| Comando e intenção | Lado, botão/direção, toque/carga, repetição, prioridade, buffer ou cancel permitido. Separar tick de input consumido, entrada na ação e primeira mudança visível. |
| Startup, atividade, recuperação | Tick zero é a entrada lógica no golpe. Usar intervalos com início incluído e fim excluído. Quatro ticks de preparo dão primeira atividade no tick 4, quinto tick quando contado desde 1. Identificar cada janela e eventual reutilização do mesmo desenho. |
| Distância e compromisso | Anotar posição inicial dos atores, deslocamento da raiz, extensão da hitbox a partir da raiz e distância entre as hurtboxes. Medir também a região vulnerável oferecida e a posição final após repelir. |
| Resultado | Registrar dano, recurso, hitstop de cada lado, hitstun/blockstun, primeiro tick em que cada lado volta a agir e condição de cancel. **Vantagem do atacante = primeiro tick livre do defensor − primeiro tick livre do atacante**, no mesmo relógio e no mesmo caso. |
| Contrapartida | Formular uma hipótese falsificável. Exemplo: maior alcance permite ameaçar de fora, mas errar deixa tempo e distância para uma punição específica. Testar se o contra-ataque chega fisicamente antes da guarda. |

Troque P1/P2 e face, mantenha a mesma medida inicial, teste perto, no último
alcance e um pixel além quando a geometria permitir. Varie acerto no início
e no fim da atividade, defesa, erro, interrupção e canto. Faça também o
espelho contra si para isolar viés de lado/ordem. Se um golpe domina em
alcance, tempo e recompensa nos casos comparáveis, procure a resposta
prevista. Se ela falhar, ajuste uma variável justificada, repita o par e
reteste os confrontos que dependem dela. Registre exceções intencionais.

**Exemplo de mesa, com valores fictícios.** A estocada de A alcança 24 px.
Após bloqueá-la, B volta a agir no tick 16 e A pode guardar no 19: vantagem
de A = −3. B inicia uma resposta no 16, com dois ticks de preparo; sua
primeira atividade ocorre no 18. Se a distância após o recuo é 18 px e a
resposta alcança só 16 px, a punição falha mesmo chegando a tempo. No canto,
repita com o recuo efetivamente observado. A correção pode estar na distância
final, na recuperação ou em outra resposta já prevista para B. Escolha a
hipótese compatível com a personalidade dos dois e mude uma coisa por ensaio.

Para ampliar o elenco, mantenha no GDD uma matriz **atacante × defensor ×
situação**. Registre a ameaça, a resposta disponível, a evidência da tentativa
e a próxima hipótese. Uma linha verde por piloto cobre aquele caso. Partidas
com lados alternados e jogadores de experiência identificada ajudam a
descobrir respostas impraticáveis. Resultados de poucas partidas orientam
reteste; paridade estatística exige amostra e desenho de teste próprios.

## Usar as referências pedidas com uma pergunta observável

| Referência | Exercício de observação |
|---|---|
| Aladdin do Master System e animação Disney | Escolher um gesto contínuo e identificar a preparação, a mudança de apoio e o atraso de uma massa secundária. Traduzir essa relação para a silhueta do personagem do GDD. |
| Street Fighter Zero 2 | Observar quando a guarda se abre, quando a ameaça fica legível e como a pose retorna ao neutro. Comparar com a janela lógica na própria ROM. |
| Darkstalkers | Estudar a distância entre silhuetas extremas e a recuperação da forma. Escolher quais exageros ainda preservam identidade, volume e regiões vulneráveis do lutador. |
| Fatal Fury Special e Samurai Shodown do Game Gear | Observar a leitura simultânea do par, o espaço à frente do golpe, o uso dos dois botões e a clareza de defesa/erro no recorte selecionado. Refazer a medida de tela, paleta e VDP no SMS. |

Para cada estudo anote edição/plataforma, trecho, papel autorizado, caminho
e SHA da mídia realmente examinada, observação e decisão de tradução. Uma
obra indicada como referência inicia a pesquisa; só registre o que foi visto.
A fonte de identidade do personagem continua sendo a indicada pelo GDD.

Material primário para a análise de poses, preparação e sobreposição.
[Disney Educational Productions, guia de animação](https://a.dolimg.com/media/en-US/disneyeducationalproductions/noma/pdf/DE1775_NOMA_TG.pdf).
Convenções de contagem de startup, atividade e vantagem.
[Capcom, composição do ataque](https://game.capcom.com/cfn/sfv/column/131432?lang=en) e
[Capcom, vantagem e desvantagem](https://game.capcom.com/cfn/sfv/column/131611?lang=en).
Identificação das versões portáteis.
[Catálogo Game Gear da Sega](https://www.sega.jp/fb/segahard/gg/soft_licensee.html).
