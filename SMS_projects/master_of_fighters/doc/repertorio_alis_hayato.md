# Registro de golpes e ações · Alis Landale e Hayato

**Versão de design para decisão individual e produção.** O objetivo é que os dois lutadores possam disputar um round inteiro, controlar distância, ameaçar por baixo e pelo alto, defender no salto, sofrer e punir um erro. Cada ação listada tem uma função e uma situação em que o adversário pode responder. O repertório usa a configuração fixa de Versus. A progressão de Alis em História tem contrato próprio.

**Como ler o registro.** “Piloto” indica os dois golpes presentes nas candidatas de 6 e 8 leituras. O aceite de combate no emulador permanece pendente na matriz atual. Os demais nomes, comandos novos, alturas, propriedades e valores de ensaio abaixo são **propostas de design**. A direção já documentada de toque/pressão continua vigente. O dono fecha GD01/GD02 e o repertório individual GD03. O executor atualiza cada linha com a decisão e o vínculo com arte, código e evidência. [GDD](11-gdd.md) · [Régua dos dois personagens e botões](duel_reach_reference_v2.md) · [Decisão das duas variantes](decisions/hayato-alis-scene02_owner-comparison_20261119.json) · [Matriz inicial e ROMs](scene02_hayato_alis_qa.md).

**Decisão da primeira família.** Produzir os quatro normais em pé por
lutador. O toque sai na soltura antes do limiar, sem buffer ou
cancelamento. Ensaiar as três guardas da tabela defensiva. O ensaio
do acorde compara simultaneidade estrita e uma leitura de tolerância.
Abaixados, ataques aéreos, especiais, Super e agarrão continuam no
inventário de propostas. [Decisão do dono](decisions/alis-hayato-standing-normals_owner_20261119.json)
· [Lista e índice de provas da primeira família](repertorio_alis_hayato_provas.md).

## Produção do espelho de Alis

A autorização atual cobre os doze normais de Alis e a Puxada com Escudo
no duelo local de dois controles. A tabela prevalece para Alis onde o
inventário histórico ainda marca uma proposta. O ensaio com Hayato
continua como referência das quatro entradas em pé. O limiar do espelho
é de seis leituras no chão e quatro no ar. No ar, a preparação comum a
cada botão começa no toque. Uma pressão nova junto ao salto é carregada
durante a compressão. O leve se define na soltura anterior ao limiar e
o forte ao completá-lo. Uma pressão mantida durante o pouso exige
soltura para rearmar.

| Comando | Postura | Ação e função | Resposta | Poses e caixa ativa | Som | Caso a provar |
|---|---|---|---|---|---|---|
| 1 toque | Em pé | Soco de guarda, interrompe aproximação | Guarda ou ficar fora do escudo | Recolhe, projeta, volta. Médio, ticks 4–5, dano 6, livre 14. | Escudo | P1 e P2, acerto e erro no limite |
| 1 forte | Em pé | Estocada forte de espada, pune à distância | Guarda, saída do alcance ou punição na volta | Prepara, estende, recupera. Médio, 5–6, dano 10, livre 18. | Espada | Primeiro acerto após boot e lâminas nas duas faces |
| 2 toque | Em pé | Chute de distância, sonda o recuo | Guarda ou recuo | Carrega, toca, recolhe. Médio, 5–6, dano 8, livre 17. | Impacto corporal | Primeiro pixel fora da bota |
| 2 forte | Em pé | Chute de avanço, compromete o corpo no médio alcance | Bloquear e responder na longa recuperação | Apoia, estende, assenta. Médio, 10–11, dano 12, livre 27. | Impacto corporal | Figura inteira e punição no erro |
| 1 toque | Abaixada | Soco rente ao escudo, curto e rápido | Defender médio ou sair da mão | Escudo recolhido, projeção baixa, volta. Médio, 4–5, dano 5, livre 14. | Escudo | Alvo em pé e abaixado |
| 1 forte | Abaixada | Estocada ascendente, intercepta a aproximação aérea | Sair da faixa ascendente ou punir o vazio | Recolhe, lâmina sobe, volta à base. Médio antiaéreo, 7–8, dano 11, livre 22. | Espada | Alvo no ar e erro de frente |
| 2 toque | Abaixada | Chute baixo curto, testa a guarda alta | Baixo + trás | Joelho apoia, bota toca baixo, recolhe. Baixo, 4–5, dano 6, livre 15. | Impacto corporal | Acerto contra guarda em pé e defesa baixa |
| 2 forte | Abaixada | Rasteira lateral, derruba no alcance baixo | Baixo + trás ou sair do alcance | Carga lateral, varredura, volta. Baixo, 8–10, dano 10, livre 25. | Impacto corporal | Queda, chão e comando após levantar |
| 1 toque | No ar | Soco aéreo de encontro, intercepta | Guarda aérea ou afastar-se | Prepara o ombro, projeta o escudo, recolhe. Alto, ticks 2–3 do golpe, dano 5, livre 11. | Escudo | Encontro no ar |
| 1 forte | No ar | Estocada em descida, abre defesa baixa | Guarda em pé ou no ar | Prepara a mão, desce a lâmina à frente, recolhe. Alto, 2–4 do golpe, dano 11, livre 15. | Espada | Descida contra um tronco em pé, pouso e botão mantido |
| 2 toque | No ar | Chute de interceptação, impede aproximação no ar | Guarda aérea ou variar a altura | Joelho recolhido, bota horizontal, recolhe. Alto, 2–4 do golpe, dano 7, livre 12. | Impacto corporal | Duas jogadoras no ar, com troca de lado |
| 2 forte | No ar | Chute em mergulho, força recuo no impacto | Guarda alta ou sair da trajetória | Dobra, projeta para baixo, recompõe. Alto, 2–4 do golpe, dano 12, livre 15. | Impacto corporal | Reação de 12 ticks e recuo de até 7 px, com queda reservada ao KO |

O teste da **Puxada com Escudo** usa frente + novas pressões de 1 e 2
na mesma leitura. O acorde vem antes dos normais. A pega é tentada no
tick 8 em alvo terrestre livre ou bloqueando, entre a separação mínima
e 32 pixels. O escudo aplica 16 de dano uma vez no tick 22. A
atacante volta a agir no tick 42. A rival cambaleia por 10 ticks antes
de cair, fica no chão por 18 ticks e levanta ao longo de 7. A parede
limita o recuo. A tentativa inelegível compromete a atacante até a
mesma retomada.

| Ticks da atacante | Trilha da atacante | Trilha da vítima |
|---|---|---|
| 0–9 | Estende a mão e fecha a pega no tick 8 | Braço alcançado no tick 8 |
| 10–16 | Flexiona os joelhos e puxa com o braço livre | Aproxima o apoio, ainda no chão |
| 17–21 | Coloca o escudo à frente e firma a base | Inclina-se perto da atacante |
| 22–27 | Projeta o escudo e transfere o peso para a frente | Recebe o impacto e começa o primeiro passo para trás |
| 28–41 | Recolhe o escudo e volta à guarda | Segundo passo, desequilíbrio, queda e repouso |

As linhas de reação do espelho são cabeça, abdômen, base baixa,
impacto de guarda em pé, impacto baixo, impacto aéreo, queda, chão
e levantada. Se a interseção alcançar a linha acima do pescoço,
prevalece a zona da cabeça. Um alvo abaixado usa a reação baixa.
O bloqueio conserva a vida e guarda a postura do escudo no impacto.
O aceite final exige repetir essas linhas na mesma ROM do espelho.

### Geometria do espelho em pixels

Os intervalos são semiabertos. A tabela usa a face direita e o pivô
em Y144 no chão. A outra face reflete o eixo horizontal. No ar, cada
atriz soma seu próprio deslocamento vertical. A caixa ofensiva só existe
nos ticks ativos de cada linha acima e termina no pouso. Preparação e recuperação mantêm
áreas vulneráveis e separação física.

| Ação | X da caixa de ataque | Y da caixa de ataque |
|---|---|---|
| Soco de guarda | [-3, 18) | [-40, -25) |
| Estocada forte | [5, 43) | [-37, -34) |
| Chute de distância | [-1, 23) | [-30, -16) |
| Chute de avanço | [-1, 27) | [-46, -31) |
| Soco rente | [-3, 19) | [-31, -18) |
| Estocada ascendente | [3, 29) | [-51, -15) |
| Chute baixo curto | [-1, 24) | [-20, -5) |
| Rasteira lateral | [-3, 28) | [-14, -2) |
| Soco aéreo | [10, 19) | [-45, -31) |
| Estocada em descida | [7, 19) | [-28, -17) |
| Chute de interceptação | [8, 22) | [-30, -22) |
| Chute em mergulho | [6, 19) | [-16, 0) |

O perfil vulnerável em pé usa X[-11, 13) e Y[-53, -3). Na flexão
de transição usa X[-13, 11) e Y[-40, -2). A base baixa usa X[-11, 11)
e Y[-33, -2). No ar usa X[-12, 11) e Y[-46, -4), com a borda inferior
recolhida a -15 na guarda ou no bloqueio. A separação da base é de
24 px e a margem atual da arena é de 43 px. A passagem pelo ar usa a
folga vertical relativa e a área de pouso entre as paredes.

Na pega, a atacante mantém o pivô, e a vítima acompanha a interpolação
entre o gap de captura e o ponto de soltura. Em cada tick preso a
vítima sobe um pixel. O tick 27 é o último preso. O 28 define o novo
arco, o dano e a coordenada de saída a 24 px da atacante. Quando a
parede impede a troca, a saída fica do lado original. A correspondência
pixel a pixel entre a mão de pega e o tronco da vítima em cada quadro
segue como uma linha de revisão do par de sprites.

## Controle com dois botões

Frente e trás acompanham o adversário. **1 curto** é soco fraco, **1 longo** é soco forte, **2 curto** é chute fraco e **2 longo** é chute forte. Curto é toque e longo é pressão sustentada. Em pé, o normal forte de Alis é uma espadada direta na vaga `alis_landale/pe_1_longo`. A classificação orienta comando e lógica. O gesto e o equipamento caracterizam o lutador. O marco de 6 ou 8 leituras pertence à comparação dos pilotos. [Decisão do proprietário](decisions/scene02-normais-dois-botoes_owner_20261121.json).

| Entrada proposta | Reconhecimento e consequência |
|---|---|
| Frente / trás / baixo | Andar, recuar ou abaixar. Trás mantém a intenção de guarda e, estando livre, permite recuar. Baixo + trás assume guarda abaixada. Baixo puro abaixa. |
| Cima, cima + frente, cima + trás | Salto vertical, à frente e para trás. Uma decolagem por nova pressão. Após decolar, trás relativo autoriza guarda aérea quando o ator estiver livre. No ápice, soltar e reaplicar trás também precisa funcionar. |
| Frente, neutro, frente | Iniciar dash. Soltar o segundo toque resulta no avanço curto. Mantê-lo além do fim do avanço engata corrida. Medir a transição pelo deslocamento do corpo. Trás, neutro, trás produz recuo rápido, seguido de parada. |
| Toque ou pressão em postura livre | Proposta para comparar com o piloto: toque dispara na soltura anterior ao limiar; forte dispara ao atingir o limiar e consome o botão até soltá-lo. No forte aéreo, aterrissar antes do disparo limpa a tentativa. Medir a latência do fraco e o que acontece quando ataque e aterrissagem coincidem. |
| **Baixo puro + 1 + 2** | Proposta universal de provocação para os dois lutadores, em luta ativa, no chão e livres. Os botões começam soltos. Baixo precisa estar amostrado quando chega a primeira borda. Testar tolerância de **uma leitura** entre as duas pressões, aceitando ambas as ordens; comparar com simultaneidade estrita. Ao reconhecer, consumir os dois eventos até soltar. |

**Precedência proposta.** Resolver primeiro fim de round, impacto e bloqueios da máquina de estados. Entre ações legais, interpretar provocação válida em baixo puro; depois Super completo, especial completo e normal da postura. Os comandos direcionais para especiais usam frente/trás relativos e uma borda nova de botão. Guardar a face das amostras e testar o cruzamento de lado durante o comando. Em baixo + trás, a defesa prevalece no contato. Um botão adicional durante bloqueio não dispara golpe nem provocação ao sair. O botão Pause do console fica fora da gramática dos lutadores.

**Casos que decidem a provocação.** Fazer o acorde com 1 primeiro, 2 primeiro, no mesmo tick, com um tick de diferença e fora da tolerância. Ao expirar a janela de um botão sozinho, preservar seu tempo de pressão e despachá-lo pela regra normal; um toque breve de chute abaixado precisa sobreviver. Em pressão desencontrada, o primeiro normal legal consome sua entrada e o segundo segue as regras de buffer/estado. Tentar ainda em baixo + trás sob ataque, em salto, dash, queda, hitstun e durante outra provocação. Conferir que soltar em qualquer ordem e trocar de lado não deixa ataque pendurado. Medir latência do toque antes/depois. Se o acorde prejudicar os normais abaixados em controle físico, comparar, em candidata separada, **baixo, baixo, 1+2** com direcional neutro na confirmação. O primeiro comando é a recomendação para ensaio; o segundo é alternativa se o conflito se confirmar.

## Normais individuais

Cada linha representa um golpe de **cada** lutador (12 por personagem). Os nomes servem para a direção de arte e para a lista de comandos. “Médio”, “baixo” e “por cima” indicam a guarda que resolve o ataque na matriz defensiva. Um golpe vindo de cima ou desenhado perto do chão só recebe a propriedade escolhida na ficha. A coluna final fixa um teste de utilidade ou de contrajogo.

| Postura e entrada | Hayato · ação e pista visual | Alis · ação e pista visual | Propriedade proposta e prova |
|---|---|---|---|
| Em pé · 1 curto (`pe_1_curto`) | **Soco da guarda**. Mão livre parte da guarda e volta junto ao corpo; katana identificável na outra mão. | **Soco de guarda**. Investida curta do punho que sustenta o escudo; borda e braço avançam juntos. | Médio, curto. Interrompe uma preparação lenta a distância de punho, erra antes do alcance das lâminas. |
| Em pé · 1 longo (`pe_1_longo`) | **Corte curto** (piloto). Preservar R01–R06, trajetória da katana e exposições v7. | **Estocada forte** (piloto). Ombro, mão e ponta avançam em linha; escudo permanece identificável. | Reproduzir primeiro o contato e a defesa do piloto. Proposta de classe média para a expansão; comparar os dois limiares e a punição após o recuo. |
| Em pé · 2 curto (`pe_2_curto`) | **Chute de sondagem**. Pé dianteiro sai pouco do chão, tronco permanece em guarda. | **Chute de distância**. Perna dianteira abre espaço enquanto o escudo protege o torso na silhueta. | Médio rápido. Medir a diferença de alcance em relação ao soco e a vulnerabilidade da perna no erro. |
| Em pé · 2 longo (`pe_2_longo`) | **Chute de giro**. Quadril anuncia a volta e o hakama abre antes da extensão. | **Chute de avanço**. Peso passa para a frente e a bota empurra em linha, com escudo recolhido. | Médio forte. Maior compromisso. O rival consegue defender e punir de perto se o atacante exagerar a distância. |
| Abaixado · 1 curto (`baixo_1_curto`) | **Soco de base**. Punho curto diante do joelho, lâmina recolhida. | **Soco rente ao escudo**. Punho sai de trás do escudo baixo, sem perder a forma da mão. | Médio curto. Testar contra rival de pé e agachado e na fronteira do acorde de provocação. |
| Abaixado · 1 longo (`baixo_1_longo`) | **Corte ascendente**. Quadril sobe antes da katana, arco curto à frente do rosto. | **Estocada ascendente**. Base firme, ponta elevada pela mão, escudo cobre o lado oposto. | Candidato a antiaéreo. Precisa interceptar um salto bem previsto, errar contra salto fora do arco e permitir punição no chão. |
| Abaixado · 2 curto (`baixo_2_curto`) | **Chute baixo de marcação**. Pé dianteiro alcança o tornozelo e recolhe. | **Chute baixo curto**. Estende a bota por baixo da linha do escudo. | Baixo. Guarda em pé perde e abaixada defende. Testar o último pixel e um pixel além. |
| Abaixado · 2 longo (`baixo_2_longo`) | **Rasteira em arco**. Apoio abaixa e a perna traseira varre antes de recompor a base. | **Rasteira lateral**. Uma perna sustenta o corpo, a outra estende enquanto o escudo equilibra a pose. | Baixo, candidato a derrubar. Uma queda por acerto; erro deixa recuperação maior que a do chute curto. |
| No ar · 1 curto (`ar_1_curto`) | **Soco de passagem**. Mão livre adiante, arma junto ao tronco. | **Soco aéreo de encontro**. Punho e guarda compactos diante do peito. | Médio ar–ar. Testar encontro de duas subidas e passagem por cima de rival abaixado. |
| No ar · 1 longo (`ar_1_longo`) | **Corte descendente**. Ombro guia a diagonal da katana com pés ainda suspensos. | **Estocada em descida**. Ponta inclina para baixo; o escudo acompanha o corpo em contrapeso. | Por cima contra alvo no chão. Fixar quando arma e caixa deixam de atuar no pouso. O rival pode defender em pé ou sair da trajetória. |
| No ar · 2 curto (`ar_2_curto`) | **Chute frontal suspenso**. Joelho abre e o pé cobre a frente do corpo. | **Chute de interceptação**. Perna estende horizontalmente à frente do escudo. | Médio ar–ar de alcance distinto do punho. Testar subida, ápice e golpe durante cruzamento. |
| No ar · 2 longo (`ar_2_longo`) | **Chute de queda**. Perna dianteira conduz a descida, outra recolhe sob o hakama. | **Chute em mergulho**. Bota desenha diagonal longa, escudo fica rente ao ombro. | Por cima contra alvo no chão. Preservar o arco de salto de controle no primeiro ensaio; medir risco de aterrissagem, face e contato único. |

**Base numérica que o executor deve preservar.** Nas duas candidatas, Hayato tem atividade nos ticks [9,11), dano 12 e volta a agir no tick 25 sem interrupção. Alis tem atividade em [5,7), dano 10 e volta no 18. Os relógios são relativos ao início da própria ação. O contrato comum usa 100 de vida, chip zero, 3 ticks de bloqueio e 8 de reação a acerto, com recuos de 3 e 4 px. A comparação de 6/8 altera quando o comando dispara. No caso de resposta após a defesa, a matriz prevê a primeira atividade de Alis no tick 22 ou 24 do relógio do corte. Conferir em ROM se alcança após o recuo.

**Chave do registro.** Use a identidade do lutador mais a chave da entrada da tabela, por exemplo `hayato/pe_1_longo` e `alis_landale/ar_2_curto`. Essas chaves organizam o inventário no documento; a ficha aponta para os IDs de origem já existentes no contrato, na animação e no motor. A provocação e os dois lutadores usam a mesma gramática. A atuação e os estados de cada lutador têm referências próprias.

## Especiais, Super e agarrão para decisão individual

O comando baixo → frente + 1 da primeira linha pertence ao ensaio direcional da b11-r2. Os resultados desse ensaio documentam Saque em passada e Passo de escudo. A prova da espadada direta de Alis pertence à linha do normal em pé com 1 longo. [Delimitação do ensaio](decisions/scene02-normais-dois-botoes_owner_20261121.json).

Estas seis ações de assinatura e os dois agarrões completam a **proposta** de repertório ofensivo. Para cada especial, coreografar antes de fixar janelas de comando, custos e frame data. “Baixo → frente” abaixo significa sequência direcional concluída, com tolerância de diagonal a definir no leitor. O botão confirma uma única ação; a gramática precisa distinguir sequência longa e curta. O GDD deixa poderes de pergaminho e magia em aberto. As propostas físicas abaixo permitem avaliar o conjunto sem fechar antecipadamente a magia de nenhum dos dois.

| Entrada candidata | Hayato | Alis | Contrajogo e condição de aceite |
|---|---|---|---|
| Baixo → frente + 1 | **Saque em passada**. Mão aproxima-se da bainha e a passada termina em um corte horizontal. | **Passo de escudo**. Escudo conduz um avanço curto e o apoio termina numa pancada única. | Especial de aproximação. Definir deslocamento, instante vulnerável e distância que fica após bloqueio. A animação mantém a lâmina ou escudo ligados à mão. |
| Baixo → trás + 1 | **Corte de retorno**. Retira o pé dianteiro, deixa passar a ameaça e devolve um arco curto. | **Resposta de escudo**. Firma o escudo e, apenas se receber ataque elegível na janela, responde com a espada. | Hayato depende de distância e pode ser alcançado. Para Alis, definir ataques elegíveis e reação no vazio. Testar baixo, agarrão e golpe atrasado contra ambos. |
| Baixo → frente, baixo → frente + 1, com barra cheia | **Corte do juramento**. Preparação concentrada, passada e golpe único de katana. | **Investida de Palma** (nome de trabalho). Alinha escudo e espada, compromete o corpo e finaliza em estocada única. | Fixar custo, evento de consumo e retorno no erro. Comparar com especial simples de mesmo sufixo em barra cheia/vazia. Definir fallback explicitamente e exibi-lo na lista de comandos. |
| Frente + 1+2, nova pressão em solo e dentro do alcance | **Desequilíbrio pela manga**. Conduz o corpo do rival com a mão livre mantendo a katana afastada do par. | **Giro com o escudo**. Alis entra pelo lado, usa o ombro e vira o rival para a queda. | Aceite GD03 da família e do comando. Alvo no chão e capturável, falha visível fora de alcance, destino e face após queda definidos. Testar colisão de comandos com provocação, corrida e normais. |

**Rastreio do rascunho histórico.** Revisar individualmente os oito IDs do [draft](movesets_draft.json). Para Hayato, comparar `katana_cut` com o corte do piloto e `diagonal_slash` com os cortes propostos; decidir se há função própria ou duplicação. `iai_dash` é antecedente para discutir o saque, separado do dash universal. `scroll_fire` exige decisão sobre o pergaminho, custo, objeto e contrajogo. Para Alis, `dagger` conflita com a espada curta do sheet; `kick` é genérico e precisa ser conciliado com os chutes desta tabela. `energy_wave` e `dodge_counter` requerem decisão específica sobre magia e esquiva. Se o dono preferir um poder, registrar que especial ele substitui e o seu comportamento. O histórico e seu frame data ficam fora dos valores de produção até a decisão.

| Personagem e ID histórico | Destino no recorte aprovado |
|---|---|
| Hayato `katana_cut` | Referência histórica para `hayato/pe_1_longo`. O corte v4/v7 do piloto rege atuação e dados. |
| Hayato `diagonal_slash` | Adiado. Candidato a ancestral de `hayato/baixo_1_longo` se o corte ascendente for aprovado; a função terrestre antiaérea precisa de prova própria. |
| Hayato `scroll_fire` | Adiado, sem sucessor aprovado. A decisão de pergaminho, recurso, objeto e contrajogo permanece aberta. |
| Hayato `iai_dash` | Adiado para a decisão sobre o saque em passada. Mantido fora da implementação do dash de locomoção. |
| Alis `dagger` | Substituído pela família da espada curta. Para o forte de arma em pé, o vínculo passa a `alis_landale/pe_1_longo`. Preservar o escudo e a estocada do piloto. |
| Alis `kick` | Entrada genérica substituída por chutes individuais; neste recorte, `alis_landale/pe_2_curto` é a referência de sondagem e `alis_landale/pe_2_longo` a de avanço comprometido. |
| Alis `energy_wave` | Adiado, sem sucessor aprovado. Magia e projétil aguardam decisão e ficha. |
| Alis `dodge_counter` | Adiado. A resposta de escudo é alternativa de design para o futuro, com janela definida e sem herdar invulnerabilidade. |

## Movimento, agilidade e defesa

| Estado/ação | Controle, desenho e prova no duelo |
|---|---|
| Posição inicial, guarda ociosa e virada | Cena de posição: entrar no enquadramento, assentar os pés na mesma linha e assumir guarda antes de liberar ambos no mesmo tick. Hayato distribui o peso sob a katana; Alis alinha ombro, escudo e espada. O idle precisa respirar e fechar o ciclo sem deslizar. Ao trocar de lado, conservar posição, mão e equipamento corretos. |
| Andar para a frente e para trás | Ciclos próprios de aproximação e recuo, com passo, transferência de peso e apoio. Medir avanço por tick, distância por ciclo e primeiro tick disponível para atacar/defender. A frente da guarda continua apontada ao rival no recuo. |
| Abaixar e levantar | Baixo afunda o quadril; os pés mantêm a base. Soltar inicia a subida. Registrar exatamente quando mudam a altura vulnerável e a guarda. Testar baixo puro e baixo + trás no mesmo golpe. |
| Dash, corrida, freio e recuo rápido | Ensaiar janela de duplo toque de 8 ticks e comparar com 10 se o controle falhar em uso real. Medir distância do dash, aceleração, velocidade sustentada, frenagem e tick livre para defender. O recuo rápido tem começo/fim visíveis e vulnerabilidade definida. Testar toque simples repetido, inversão de lado entre toques, corrida contra canto e tentativa de atacar/defender durante a frenagem. |
| Salto neutro, à frente e para trás; pouso | Registrar saída do solo, subida, ápice, descida e primeiro tick de chão. Hayato compacta a arma; Alis resguarda o corpo atrás do escudo. Medir duração, altura e alcance horizontal. Testar salto curto junto ao rival, travessia, golpe na descida, pouso livre e pouso vindo de bloqueio. |
| Guarda em pé | Segurar trás em solo e livre. Proposta: bloqueia médio e ataque por cima, perde para baixo e agarrão. Hayato intercepta com a katana; Alis expõe a face do escudo. Medir contato visual, chip, recuo e primeiro tick livre. |
| Guarda abaixada | Segurar baixo + trás. Bloqueia baixo e médio, perde para ataque por cima e agarrão. Conferir que a espada descendente alcança o corpo onde aparenta e que baixo puro continua vulnerável. |
| Guarda aérea, inclusive no alto do salto | Trás relativo após decolar. Proposta: bloqueia golpes ar–ar enquanto livre; o antiaéreo terrestre marcado como tal vence a guarda aérea. Demais normais de solo só bloqueiam no ar se a ficha os marcar como defendíveis no ar e houver interseção. Não conceder imunidade a um projétil futuro por padrão. Testar subida, **ápice**, descida e primeiro tick de pouso, inclusive salto vertical seguido de trás e salto para trás com direção mantida. |
| Reações, queda e retomada | Desenhar reação alta/baixa e aérea, bloqueio nas três posturas, queda, chão e levantada. Fixar para cada uma quais entradas são aceitas e o primeiro tick livre. Colisão no pouso resolve uma vez. No canto e em troca de lado, dois controles continuam independentes. |

**Como calibrar agilidade.** No mesmo piso e distância, cronometrar cada lutador caminhando 32 px para frente e para trás, alcançando a mesma marca em dash/corrida e retornando à guarda. Medir também o primeiro comando aceito após freio, salto e erro de golpe. Hipótese para ensaio: Hayato ganha terreno com uma passada mais comprometida; Alis muda de direção mais cedo, mas precisa chegar mais perto para usar o escudo. Se um personagem dominar aproximação, alcance, defesa e recuperação no mesmo exercício, rever um parâmetro por vez e repetir com P1/P2 invertidos. Registrar velocidade em px/tick, distância em px e tempo em ticks lógicos.

**Teste de prioridade e troca de lado.** Antes de ampliar o catálogo, registrar na tabela do leitor de comandos o que acontece com direções opostas na mesma leitura, duas bordas de ataque simultâneas sem acorde válido, input no último tick de recuperação e mudança de face no ápice. Como hipótese, aceitar a guarda conforme a posição relativa no tick de contato, manter a orientação do golpe já iniciado até o retorno e deixar o defensor virado para o adversário ao sair do bloqueio. Repetir os mesmos inputs espelhados; guardar os testes de cruzamento, troca de controle e canto. Para cada cancelamento autorizado declarar origem, destino e janela em hit, block e whiff. Medir o primeiro tick em que o novo comando modifica o estado.

## Atuação e provocação contextual

| Momento | Hayato | Alis | Regra de jogo proposta |
|---|---|---|---|
| Apresentação e tomada de posição | Em Kenseiden, observa a aproximação do visitante, firma o pé e traz a katana para a guarda. | Reconhece a ameaça, volta o escudo para o rival e firma a espada junto ao corpo. | Evento de abertura da arena. Se houver skip, ambos chegam aos mesmos pivôs, face e tick livre. |
| Provocação normal | Baixa a ponta, convida o avanço com a mão livre, retoma a guarda. | Toca a borda do escudo com a espada, encara o adversário e volta a cobrir o peito. | Comando universal em solo livre. Janela punível, sem dano, ganho de barra ou alteração da resposta do rival. Se sofrer acerto, passar à reação no tick de contato. |
| Provocação contextual | Depois de defender um golpe forte, recompõe a lâmina com um gesto contido de respeito. | Depois de bloquear com o escudo, baixa-o por um instante e aponta a espada para o espaço que acabou de defender. | O jogador ainda precisa pedir a provocação. Proposta de seleção determinística: se a última interação foi bloqueio próprio de forte no round, usar a variante uma vez, consumir a marca e limpar no próximo contato ou reset. Mesma duração e vulnerabilidade da base. |
| Vitória e derrota | Hayato recolhe a katana após o fim da ameaça; derrotado, perde a base e interrompe o gesto. | Alis abaixa a espada, mantém o escudo próximo e recupera o fôlego; derrotada, cede o apoio. | Encerramento após resultado único. Registrar destino distinto para KO e tempo conforme GDD. A chamada manual da provocação fica restrita ao round ativo. |

## Ficha que acompanha cada ação até a ROM

Dar a cada ação um ID estável no contrato individual e referenciá-lo na lista de comandos e na [Cena 10](character_move_showcase_standard_v1.md). Para cada linha registrar:

1. **Design** — personagem, nome exibido, origem da proposta, decisão do dono, função, comando nas duas faces, postura, recurso, precedência e situações proibidas. Ações rejeitadas/substituídas conservam a decisão e o motivo.
2. **Movimento e arte** — sheet e SHA, chave de preparação, contato, absorção e retorno, exposições, pé de apoio, mão/ponta ou escudo, atitude do adversário. Em corrida, salto e guarda, registrar emenda de ciclo, interrupção e pouso. Rever a 1× e em velocidade normal.
3. **Regra** — relógio de início, startup, intervalos ativos [início,fim), recuperação, primeiro tick livre, caixas por pose, classe de guarda, alcance, dano/chip, recuo, hitstop/hitstun/blockstun e vantagem após contato. Para vantagem, registrar o tick livre do defensor menos o do atacante. Indicar quais cancelamentos são legais e repetir no erro. Nas ações sem contato registrar deslocamento e janelas de controle aplicáveis.
4. **Implementação e evidência** — ID lógico, pose de contato, solicitada/residente/apresentada, origem e símbolo na ROM, lado/P1/P2, input consumido, SHA, sessão, quadro ou instante de vídeo, resultado observado, ciclo medido e revisão. Manter o estado por ação: proposta → decisão individual → arte aprovada → implementada → buildada → observada na ROM → aceita ou devolvida com causa.

**Matriz de encerramento.** Por normal/especial, testar acerto próximo, no último pixel e erro um pixel além; guarda correta e incorreta, recuperação, punição, canto e lados invertidos. Incluir golpes simultâneos, virada no ar, aterrissagem no tick ativo, reação interrompendo provocação e contato entre as poses de maior custo com cenário/HUD/áudio. Para Super/agarrão testar também falta de recurso/alvo inelegível. Para locomoção e atuação testar entrada, manutenção, interrupção, soltura e retorno. A decisão artística sobre a cena de posição, a provocação e os golpes precisa de vídeo real e revisão com o par em quadro.

O registro fica completo quando as **24 entradas de normais**, os **quatro especiais, dois Supers e dois agarrões propostos**, os **oito IDs históricos** e as ações de movimento, defesa e atuação tiverem destino explícito por personagem. Toda ação aprovada deve ter prova de execução; uma substituição aponta para o ID sucessor. [Prompt de produção para o agente](../../../doc/continuity/20261119-prompt-repertorio-alis-hayato.md).

## Alis · decisões vigentes e cobertura de produção

A matriz abaixo usa o [aceite dos normais em pé de 19/11](decisions/alis-hayato-standing-normals_owner_20261119.json), a [correção de 21/11](decisions/scene02-normais-dois-botoes_owner_20261121.json), o [ensaio dos especiais de 19/11](decisions/scene02-first-specials_owner-trial_20261119.json) e o [índice do round de controle](repertorio_alis_hayato_provas.md#round-contínuo-b11-r2). B11-r2 significa a candidata de seis leituras com SHA `f76fe86f5b3d874a7317c7727f350aa8e750af7a1dba9d85b8d71722c3a126b7`. O termo aprovado na coluna de design se refere ao escopo autorizado pelo dono. A coluna de prova registra a cobertura observada.

| Ação de Alis | Design e fonte | Produção e prova |
|---|---|---|
| `pe_1_curto` Soco de guarda | Aprovado em 19/11, confirmado em 21/11 | IDs 20–22. B21 recompõe rosto, torso e escudo pela guarda. #21 conferida no framebuffer, com dano 6 no vídeo quando alcança. Guarda, borda, espelho ao vivo e cadência seguem abertos. |
| `pe_1_longo` Estocada forte | Aprovado em 19/11. Espadada direta de botão 1 sustentado em 21/11 | IDs 17–19. B21 registra o rosto nas poses originais e preserva a ponta da espada. #18 conferida no framebuffer, com dano 10 no vídeo. Borda e guarda com resposta passaram no stepping. Espelho ao vivo e cadência seguem abertos. |
| `pe_2_curto` Chute de distância | Aprovado em 19/11, confirmado em 21/11 | IDs 23–25. B17, acerto no contato 6, #24 submetida e 8 de dano. Casos de limite e retomada pendentes. |
| `pe_2_longo` Chute de avanço | Aprovado em 19/11, confirmado em 21/11 | IDs 26–28. B17, acerto no contato 8, #27 submetida e 12 de dano. Punição no erro, canto e retomada pendentes. |
| `baixo_1_curto` Soco rente ao escudo | Decisão necessária em GD03. Proposta deste registro | Ficha de ideia. Sem ação correspondente na b11-r2. |
| `baixo_1_longo` Estocada ascendente | Decisão necessária em GD02/GD03, inclusive antiaéreo | Ficha de ideia. Sem prova de interceptação ou erro. |
| `baixo_2_curto` Chute baixo curto | Decisão necessária em GD02/GD03, inclusive classe baixa | Ficha de ideia. Sem prova de alcance ou guarda. |
| `baixo_2_longo` Rasteira lateral | Decisão necessária em GD02/GD03, inclusive queda | Ficha de ideia. Sem prova de queda ou recuperação. |
| `ar_1_curto` Soco aéreo de encontro | Decisão necessária em GD03. Proposta deste registro | Ficha de ideia. Sem prova ar–ar. |
| `ar_1_longo` Estocada em descida | Decisão necessária em GD02/GD03, inclusive ataque por cima | Ficha de ideia. Sem regra de pouso provada. |
| `ar_2_curto` Chute de interceptação | Decisão necessária em GD03. Proposta deste registro | Ficha de ideia. Sem prova de cruzamento. |
| `ar_2_longo` Chute em mergulho | Decisão necessária em GD02/GD03, inclusive ataque por cima | Ficha de ideia. Sem prova de pouso ou contato único. |
| Passo de escudo | Em ensaio desde 19/11, delimitado em 21/11 | B11-r2, IDs 48–50 no comando direcional, contato 10. Uso em produção depende de decisão e prova própria. |
| Resposta de escudo | Decisão necessária em GD03. Proposta de guarda seguida de resposta elegível | Ficha de ideia. Janela, reação no vazio e contrajogo pendentes. |
| `energy_wave` | Decisão necessária. Adiado no rastreio do rascunho e no GDD, sem sucessor aprovado | Sem objeto, custo, trajetória ou colisão de produção. |
| Super Investida de Palma | Decisão necessária em GD01–GD03 | Proposta de sequência dupla + 1. Medidor, consumo, fallback e arte pendentes. |
| Agarrão Giro com o escudo | Decisão necessária em GD01–GD03 | Proposta de frente + 1+2. Captura, coreografia do par e posição após queda pendentes. |
| `dodge_counter` | Decisão necessária. Adiado no rastreio do rascunho | Sem esquiva invulnerável na b11-r2. |
| `dagger` | Aprovado o sucessor `pe_1_longo`, conforme decisão de 21/11 e concept v4 | O ID antigo é histórico. A prova pertence à espadada direta. |
| `kick` | Aprovados os sucessores em pé `pe_2_curto` e `pe_2_longo` em 19/11 | O ID genérico é histórico. As provas pertencem aos chutes individuais. |
| Guarda ociosa | Em ensaio na Cena 02. Identidade segue concept v4 | B11-r2 publicou #16 estática no neutro. A respiração precisa de revisão temporal. |
| Assentar na guarda | Em ensaio na Cena 02 | O retorno ao quadro #16 existe. A emenda entre marcha, postura e repouso precisa de prova visual. |
| Sair do repouso | Em ensaio na Cena 02 | A b12 aceita a marcha ou botão 1. Nas retomadas observadas, a pose de movimento pode chegar depois do pivô. |
| Virada | Em ensaio na Cena 02 | Variante de lado de boot prevista no piloto. Virada em luta ativa precisa de prova de cruzamento. |
| Andar à frente | Em ensaio no comparativo da Cena 02 | B11-r2 percorreu 32 px com quatro poses. Revisão da rampa magenta e retomada ainda abertas. |
| Recuar | Em ensaio no comparativo da Cena 02 | B11-r2 percorreu 32 px com quatro poses. Medir a saída para guarda e para ataque. |
| Abaixar | Solicitado pelo dono para Alis em 21/11 | B26 confirmou pivô X fixo, pose #52 e hurtbox mais baixa. |
| Levantar do agachamento | Integra a saída do agachamento | B26 aplicou a flexão #51 e voltou à guarda na soltura. |
| Salto neutro | Solicitado pelo dono para Alis em 21/11 | B29 confirmou dois ticks de compressão, subida de 78 px e 20 ticks no ar com X fixo. |
| Salto à frente | Diagonal e cruzamento solicitados pelo dono para Alis em 21/11 | B29 cruzou Hayato nos dois sentidos, virou junto ao rival e pousou fora da faixa de colisão. |
| Salto para trás | Diagonal solicitada pelo dono para Alis em 21/11 | B29 conserva o vetor de 6 px/tick da decolagem até o pouso e respeita a borda. |
| Pouso | Integra o retorno ao chão das três trajetórias | B26 confirmou retorno ao Y144 e a flexão de aterrissagem. |
| Dash | Decisão necessária em GD01/GD02. Janelas de duplo toque de 8 e 10 são propostas | Módulo de movimento em bancada. Distância e saída sem prova em ROM. |
| Corrida | Decisão necessária em GD01/GD02. Proposta deste registro | Módulo de movimento em bancada. Transição do dash e deslocamento sem prova em ROM. |
| Freio da corrida | Decisão necessária em GD02. Proposta deste registro | Módulo de movimento em bancada. Leitura do apoio e primeiro comando livre sem prova em ROM. |
| Recuo rápido | Decisão necessária em GD01/GD02. Proposta deste registro | Módulo de movimento em bancada. Distância, vulnerabilidade e resposta sem prova em ROM. |
| Guarda em pé | Solicitada pelo dono para Alis em 21/11 | B26 bloqueou o soco de Hayato com #54 e vida preservada. |
| Guarda abaixada | Solicitada pelo dono para Alis em 21/11 | B26 bloqueou o chute de sondagem com #53, pose e consequência conferidas. |
| Guarda aérea | Solicitada pelo dono para Alis em 21/11 | B26 verificou entrada, soltura e reaplicação no mesmo voo. A pose #59 bloqueou o soco de Hayato quando houve interseção com a hurtbox. |
| Reação em pé a acerto | Em ensaio com tempos comuns de 19/11 | O piloto registra vida, recuo, estado e retorno. Falta atuação distinta. |
| Reação em pé ao bloquear | Em ensaio com tempos comuns de 19/11 | Sem pose de bloqueio distinguível na b12. Falta prova em velocidade normal. |
| Reação abaixada a acerto | Decisão necessária em GD02. Proposta deste registro | Faltam pose, altura vulnerável e saída em ROM. |
| Reação abaixada ao bloquear | Em ensaio pela matriz das três guardas. Resposta visual e regra final pendentes em GD02 | Sem estado visual próprio em ROM. |
| Reação aérea a acerto | Decisão necessária em GD02. Proposta deste registro | Sem prova de trajetória, pose ou pouso após impacto. |
| Reação aérea ao bloquear | Em ensaio pela matriz das três guardas. Resposta visual e regra final pendentes em GD02 | Sem prova de bloqueio no ápice e na descida. |
| Queda | Decisão necessária em GD02. Proposta ligada à rasteira e ao agarrão | Faltam regra de vulnerabilidade, pose e relógio de lançamento. |
| Estado no chão | Decisão necessária em GD02. Proposta deste registro | Faltam pose, interação com ataques e limite de duração. |
| Levantada após queda | Decisão necessária em GD02. Proposta deste registro | Faltam pose, instante vulnerável e teste de primeiro comando. |
| Provocação base | Em ensaio de comando somente, conforme 19/11 | Acorde estrito/uma leitura existe em bancada. Sem provocação integrada na ROM do round. |
| Provocação contextual | Decisão necessária em GD01/GD03. Proposta após a defesa de um forte | Sem regra da marca ou atuação em ROM. |
| Entrada em cena | Direção aprovada para produção em 01/11. Atuação específica aguarda ficha de cena | Enquadramento inicial existe. Falta encenação até a tomada de posição. |
| Tomada de posição | Em ensaio na Cena 02 | B11-r2 começa com os lutadores voltados um para o outro. Falta a transição animada desde a entrada. |
| Entrega do controle e skip | Direção aprovada em 01/11. Gatilho de skip depende de GD01/FC02 | Falta prova da sequência completa, com botão mantido e input novo. |
| Vitória | Direção aprovada no GDD. Pose e anúncio de Alis pendentes | Knockout do adversário não tem encenação de vitória aprovada em ROM. |
| Derrota | Direção aprovada no GDD. Pose de derrota pendente | KO de Alis observado na b11-r2. Falta atuação própria. |
| Transição após Versus | Decisão necessária em GD04 para timeout, desempate e destino | Falta prova de anúncio, reinício e retorno. |
| Cena 04, abertura | Direção aprovada em [01/11](decisions/fan-campaign-and-character-expression_owner_direction_20261101.json). Beats individuais aguardam ficha | Sem prova da aparição de Alis na montagem completa. |
| Cena 07, diálogo e duelo | Direção aprovada em 01/11. Atuação do visitante e prioridade de skip aguardam ficha | Sem trecho narrativo de Alis ligado ao primeiro comando da Cena 02. |
| Cena 08, vitória e evolução | Direção aprovada em 01/11. Níveis, pontos e efeitos dependem de FC01 | Sem prova de pose, cue ou escolha de atributos na ROM. |
| Cena 09, encerramento | Direção aprovada em 01/11. Epílogo individual depende de FC04 | Sem sequência de Alis e retorno observados. |
| Cena 10, consulta de comandos | Direção aprovada em [01/11](decisions/character-move-showcase_owner_direction_20261101.json). Navegação e acesso de produto pendentes | A [lista fora da ROM](scene02-comandos.md) cobre a b11-r2. Interface e demonstração na própria ROM pendentes. |

Na documentação vigente, nenhum item aberto deste quadro foi excluído explicitamente pelo dono. Adiamentos e substituições têm destino próprio nas decisões e no rastreio histórico.

Os ensaios de identidade visual, marcha e golpes do botão 1 estão na [matriz da b21](scene02_hayato_alis_qa.md#b21--revisão-dos-pontos-relatados).
