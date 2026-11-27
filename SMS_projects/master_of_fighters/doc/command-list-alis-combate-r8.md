# Alis Landale · Command List e contrato de combate R8

Esta é a ficha de jogabilidade da R8. Frente e trás acompanham a orientação de Alis. Solte o direcional entre dois toques iguais e aperte os dois botões na mesma leitura para os acordes. No perfil SMSForge do Steam Deck, A é o botão 1 e B é o botão 2. No teclado de P1, use A e S. Os tempos abaixo são quadros de lógica, com alvo de 60 Hz. Hiperpausa e hitstop suspendem a ação. [Ficha técnica](ficha_tecnica_alis_g6e_v1.docx) · [Command List e metodologia](padrao_moveset_especiais.md) · [Mapeamento do controle](scene02-comandos.md)

## Movimento e golpes normais

Ande com frente ou trás, agache com ↓ e salte com ↑, sozinho ou combinado com frente ou trás. Solte ↑ durante a compressão para o salto curto. Toque ↓ e logo ↑ para o salto longo. Mantenha trás para a guarda em pé e ↓ + trás para a guarda baixa.

| Postura | Toque em 1 | Segure 1 | Toque em 2 | Segure 2 |
| --- | --- | --- | --- | --- |
| Em pé | Soco de guarda com escudo · 6 HP | Estocada forte de espada · 10 HP | Chute de distância · 8 HP | Chute de avanço · 12 HP |
| Abaixada | Soco rente ao escudo · 5 HP | Estocada ascendente · 11 HP | Chute baixo curto · 6 HP | Rasteira lateral · 10 HP e queda |
| No ar | Soco aéreo de encontro · 5 HP | Estocada em descida · 11 HP | Chute de interceptação · 7 HP | Chute em mergulho · 12 HP |

O toque sai na soltura antes da sexta leitura no chão ou da quarta no ar. A pressão sustentada dispara na leitura do limiar.

## Outros especiais e recuperação

| Golpe | Comando | Custo e resposta |
| --- | --- | --- |
| Fire | ↓↓ + 1 | Sem custo. Toque para 6 HP, sustente para 10 HP. O rival pode defender, saltar ou devolver com Mirror Counter. |
| Fire duplo | ↓↘→ + 1+2 | 4 MP. Oito apresentações de hiperpausa, seguidas por duas chamas de até 7 HP cada. |
| Rising Saber | →↓↘ + 1 | Sem custo. Toque para a subida simples de 12 HP. Sustente para o arco à frente de 5 + 10 HP, com queda no segundo contato limpo. |
| Mirror Counter | ↓↙← + 1 | Reflete projéteis entre f3 e f12. A devolução troca o dono e o sentido. O corte ancorado do Laconian Slash segue a regra de contato direto. |
| Passo de Escudo | ↓, depois → + 1 | Entrada física de 13 HP com centelha e recuo no acerto. O atalho ↓→ do Laconian concorre pela mesma entrada. |
| Puxada com Escudo | → + 1+2 | Agarra o rival terrestre ao alcance, causa 16 HP e o derruba. |
| Defesa com contra-ataque | ↓, depois ← + 1 | A janela de contra-ataque aceita um golpe médio do f2 ao f7. A resposta confirmada causa 15 HP. O atalho ↓← do Mirror Counter concorre pela mesma entrada. |
| Heal / Rest | ↓↓ + 2 | 2 MP por até 6 HP no f21, limitado à vida que falta. O ganho confirmado mostra a quantidade e toca o arpejo de HP. |
| Chat | ←← + 2 | Ganha 1 MP no f20 quando a barra tem espaço. Intervalo de 100 quadros e som próprio. |
| Atordoar | →←→ + 1 | Requer 1–25 HP, 8 MP e alvo livre no chão. Até 84 quadros com estrelas. Uma vez por lutador no round. Preserva o MP para os Guardiões. |

O leitor da R8 avalia as magias antes dos comandos físicos. Confira no emulador qual ação sai com ↓→ + 1 e ↓← + 1 e se Passo de Escudo e Defesa com contra-ataque continuam acessíveis pela tabela.

## Sequências revisadas

| Golpe | Comando | Ordem de animação | Acerto limpo | Guarda e saída |
| --- | --- | --- | --- | --- |
| Investida de Myau | ↓↙← + 2, com 4 MP | Pequeno com a noz em oito apresentações de hiperpausa. Corrida ao voltar o relógio. Salto e crescimento intermediário. Mergulho alado e pouso. | Pequeno 4 HP, transição 6 HP e mergulho 10 HP. Cada fase registra até um hit e inicia recuo. O mergulho derruba e encerra a sequência. A bancada confirmou 3, 2, 1 e 0 hits a 24, 60, 90 e 134 px. | Bloqueio por fase, com recuo e chip quantizado. O cancelamento da estocada forte confirmada entra uma vez por golpe. |
| Laconian Slash | ↓↘→ + 1 | Base baixa, perna de trás estendida e joelho da frente flexionado. Rotação com escudo em contrapeso. A lâmina corta de baixo para cima e produz meia-lua azul, ciano e branca à frente. | Primeiro contato entre f8 e f12. Até 48 px em altura média e até 32 px no trecho alto do arco. Um hit de 17 HP, 11 f de impacto e queda comum para trás. Funciona no solo e intercepta o salto na frente da Alis. | 2 HP de chip fora da guarda precisa, recuo e 9 f de blockstun. Alis fica comprometida até f34. Conferir punição à queima-roupa e defesa agachada. |
| Investida de Palma | ↓→↓→ + 1, com 8 MP | Dez apresentações de hiperpausa. Depois da investida, volta à guarda, arma a espada acima da cabeça e corta para baixo no chão, 19 f depois do primeiro contato. Volta à guarda. Aos 36 f dispara para frente e para cima com arco dourado. | 5 → 7 → 15 HP, total de 27 HP. O golpe dourado acerta aos 38 f e leva o alvo durante a subida até f47. A partir daí o alvo cai para trás e Alis termina o arco recuando até o chão. | Primeiro contato defendido ou errado encerra a progressão. O golpe vertical precisa confirmar para liberar o salto. Se o dourado for defendido ou errar, o defensor fica livre do arrasto. |
| Guardiões de Algol | ↓↘→↓↘→ + 2, com 8 MP, Alis com 1–25 HP e rival atordoado com 1–24 HP. Exige uma vitória que feche a luta. | Doze apresentações de hiperpausa e um corte de confirmação. Mantém seis planos dos aliados e um plano de reação escolhido pelo lutador adversário. Volta à arena com o oponente real em queda, 29 px acima do chão. | O adversário cai para trás até tocar o chão. O resultado da rodada entra depois da aterrissagem e usa o mesmo placar. | O corte precisa alcançar o rival para iniciar a cinemática. O oponente da arena usa seus próprios sprites de queda e deitado. |

A referência de meia-lua orienta a função antiaérea, a transferência de peso e a leitura do arco. A arte, a paleta e os quadros pertencem à Alis deste projeto. [Conceptual Model Sheet v4](../data/source_art/concept_art/alis_landale/alis_concept_sheet_v4.png) · [Prancha fonte dos quatro cortes](../data/source_art/scenes/alis_cortes_r8/cortes.png)

## Regras compartilhadas por Alis e Hayato

| Regra | Contrato |
| --- | --- |
| Impacto fraco | 4 f de hitstop e 10 f de hitstun, faísca curta, som curto e empurrão inicial leve. Mantém distância para encadeamento. |
| Impacto forte | 11 f de hitstop e 20 f de hitstun, faísca maior, tremor do defensor, som de impacto e recuo por atrito. Passo de Escudo recebe o recuo próprio de uma colisão de maior peso. |
| Queda comum | Arco por impulso e gravidade, deriva para trás e um pequeno quique de cerca de 4–6 f. Após o quique, 28 f no chão antes de levantar. Nova entrada junto ao pouso pode acionar ukemi se houver vida. Os estados de queda, chão e levantar impedem contato comum. |
| Queda abrupta | Agarrão pesado, rasteiras marcadas ou finalizador forte derrubam sem quique ou ukemi. Tremor vertical, efeito no piso e baque grave sincronizados com o impacto. Duração no chão de 38 f. Rachadura transitória é um recurso opcional para impactos extremos. |
| Guarda | Trás em pé protege de médios e overheads. Baixo-trás protege de médios, baixos e projéteis horizontais. Antiaéreos marcados vencem guarda aérea. Blockstun leve 5 f e forte 9 f, com recuo. |
| Chip e quebra | Normais defendidos tiram 0 HP. Quatro normais fortes bloqueados dentro de uma mesma pressão provocam quebra e deixam 20 f de vulnerabilidade. Especiais aplicam chip aproximado de 12,5%, arredondado em HP inteiros, e podem finalizar. Guarda precisa na janela de 2 f protege do chip. |
| Contagem e defesa no canto | O HUD conta acertos limpos. Guarda, escape ou fim da sequência quebram o elo. A partir do quinto acerto de uma cadeia, um golpe físico comum deixa 8 f de hitstun. A partir do oitavo, um novo contato físico derruba e libera a recuperação. O canto absorve recuo sem empurrar o alvo para fora da arena. Testar com guarda ou resposta programada no primeiro frame legal. |
| Buffer | Guarda um normal reconhecido por 4 quadros de lógica durante a recuperação. Captura botão novo durante hitstop. Não repete o comando consumido. Movimento e defesa mantêm prioridade de postura e estado. |
| Tolerância e prioridade | Aceitar baixo → frente ou baixo → trás sem diagonal intermediária para gestos de um quarto de círculo e a sequência baixo-frente, frente, baixo-frente para Rising Saber. Magia e Super confirmados precedem comandos de agarrão e normais, e força precede os ataques leves na mesma amostra. Colisões físicas simultâneas resolvem o trade a partir do mesmo par de caixas. O repertório atual não usa um estado separado de clash. |
| SOCD | Esquerda + direita e cima + baixo dão neutro antes da leitura de defesa, movimento e golpes. |
| Salto | Três quadros de compressão no chão com imunidade a agarrão, vulnerabilidade a golpes e custo normal de recuperação. Arco sob gravidade. Soltar cima antes da saída gera hop. Baixo seguido de cima dentro da janela de carga dá salto mais longo; com direção escolhida no comando, há mais velocidade horizontal. |

## Revisão de arte para produção

Compare o Model Sheet v4 antes de desenhar ou importar. Confirme tiara dourada, rosto sem cinza, peitoral índigo, ombreiras cinza com borda dourada, saia assimétrica de dois rosas, meia branca contínua com contorno escuro, joelheiras e escudo em cunhas. Normalize a altura anatômica pelo quadril, cabeça e solas sem usar a espada como referência. Revise as quatro poses na saída CRAM nos dois lados e nas duas paletas. Faça a leitura a 1× e por vizinho mais próximo. Confira recorte, vazamento e estabilidade do pivô também no movimento publicado. [Fluxo de curadoria](curadoria_capitulo_alis.md) · [Receita e procedência](../data/source_art/scenes/alis_cortes_r8/source-receipt.json) · [Comparação na paleta nativa](decisions/2026-11-27_alis_cortes_r8.png)

## Aceite da candidata

Execute uma sessão privada do Emulicious por vez após a liberação do host. Preserve os quadros nativos, as entradas em quadros VDP, o SHA da ROM e o recibo da sessão. A bancada cobriu danos, recuo, queda, guarda e controle. A apresentação, o áudio e a cadência precisam da ROM em execução.

| Sequência | O que a gravação e a sonda devem mostrar |
| --- | --- |
| Myau | Noz na hiperpausa, três formas, recuo em cada acerto, queda no mergulho e pouso sem acerto fora do alcance. Registrar os danos a 24, 60, 90 e 134 px. |
| Laconian Slash | Saída de baixo para cima, arco e contato no chão e no salto. Guardar também bloqueio com chip e tentativa fora do alcance. |
| Palma | Estocada, guarda, corte descendente ainda no chão, guarda e arco dourado. Registrar 5 + 7 + 15 HP, elevação conjunta, soltura e queda do rival. |
| Guardiões de Algol | Uma gravação contínua dos sete planos até o resultado. No retorno à arena, acompanhar o mesmo adversário em queda, comparar a direção do recuo e registrar o primeiro quadro no chão antes do resultado. |
| Cadência | Três janelas NTSC com controles e combate ativos, avanço da lógica, taxa das apresentações da ROM e pior quadro de VBlank. A sonda SMRT também mede três janelas contínuas em guarda. O alvo é 60 FPS e o piso é 58 FPS em cada janela, sem arredondamento. A gravação quadro a quadro prova a ordem da ação. A taxa vem da sonda da ROM. |

### Resultados no Emulicious

A R8 tem SHA-256 `c81a9497c420ee5458201d81cac03cfb26fd6a3cc1b1a6b1fb6561c253c70ab0`. A prova dos Guardiões passou nos cinco critérios de retorno à arena. O adversário recuou 15 px desde a primeira amostra visível, tocou o chão no quadro VDP 2653 e entrou no estado deitado no 2655. A tela de resultado apareceu no 2661. Do retorno à queda, a amostra curta registrou 6 apresentações em 12 quadros VDP (29,961371702156155 FPS). [Vídeo dos Guardiões](../out/qa/alis_combate_r8/guardioes/guardioes.mp4) · [Recibo dos Guardiões](../out/qa/alis_combate_r8/guardioes/observations.json)

O combate misto registrou 36,95235843265925, 39,449139407838935 e 43,943345163162356 FPS. As três janelas ficaram abaixo do piso de 58 FPS. A janela selada de 3.000 apresentações registrou zero estouros de VBlank. [Medição por janela](../out/qa/alis_combate_r8/worst/observations.json) · [Estado da compilação e da validação](10-memory-bank.md)

Em guarda baixa contínua, as três janelas em tempo real mediram entre 58,28580742200693 e 59,32853298546355 FPS. [Sonda SMRT](../out/qa/alis_combate_r8/cadencia-tempo-real/fps.json)
