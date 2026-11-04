# skill: game-design-core-loop

Use para desenhar ou revisar interação, fases/encontros e progressão do GDD.
Composição visual usa `sms-visual-excellence.md`; diagnóstico de CPU usa
`sms-runtime-optimization.md`. Esta skill não impõe gênero nem amplia escopo.

## 5 Leis Fundamentais (checar no GDD)
1. **Agência** — input visivelmente afeta estado.
2. **Feedback** — toda ação tem resposta perceptível (visual+áudio).
3. **Fluxo** — desafio acompanha habilidade; sem paredes de frustração.
4. **Consistência** — mesma regra, mesma resposta, sempre.
5. **Recompensa** — progressão sentida, não só narrada.

## Golden Path
Caminho principal desenhado em 3–5 beats ANTES de conteúdo extra.

Para cada beat, registrar no roteiro/spec existentes: o que o jogador aprende,
decide, arrisca e recebe; ameaça, pista visível/sonora, saída e recuperação.
Introduzir uma regra em situação legível, permitir prática e depois combiná-la
com pressão. Alternar tensão e respiro é uma hipótese de ritmo, não uma curva
universal que todo gênero precisa seguir.

## Métricas de movimento e câmera

Em plataforma/ação, derivar gaps, alcance e espaço de reação do controlador
real: aceleração, frenagem, salto variável, largura de colisão e câmera.
Medir a trajetória discreta na ROM; fórmula contínua de gravidade é somente
previsão. Conferir bordas, mudança de altura, retorno da câmera e ameaça fora
da tela. Em puzzle/RPG, usar o equivalente do gênero: informação disponível,
custo da decisão e condições de bloqueio/retorno. Não introduzir salto em luta
nem labirinto em puzzle só para preencher uma tabela.

Buffer de input, coyote time, aceleração, deadzone/look-ahead e checkpoints
são opções do GDD. Se adotados, definir frames/unidades/limites e exercitar
limiar−1, limiar e limiar+1, neutralização e reentrada. No SMS, câmera e shake
disputam scroll, HUD, streaming de colunas e VBlank: medir o conjunto.

## IA de inimigos
Matriz archetype × comportamento no GDD; FSM por inimigo no TDD;
pool estático. Nada de IA "emergente" sem medição.

Cada ataque/encontro explicita antecipação, janela ativa, resposta possível,
recovery e retorno. Conferir se a pista chega ao jogador antes da consequência,
inclusive durante upload. Dificuldade pode mudar decisão, cadência e combinação;
aumentar HP sozinho não demonstra IA melhor. Repetição máxima, invulnerabilidade
e contra-ataque são escolhas do jogo, não regras universais importadas de bosses 3D.

## Game feel no SMS
hitstop curto (frames), knockback fixo, screen shake = offset de scroll global.
Tudo medido em frames — nunca "um tiquinho".

Construir uma hierarquia de feedback por evento: ação comum, impacto relevante,
conclusão. Escolher o menor conjunto que comunica a consequência. Partículas,
flash e números competem com a silhueta e com SAT/paleta; mais camadas podem
piorar a leitura. Hitstop tem owner, relógio de saída e duração finita; input,
áudio e retorno precisam de comportamento declarado. Não usar atraso de upload
como hitstop nem copiar time-scale, tweens float ou buses de engines modernas.

## Teste de experiência

Aplicar `workflows/first-playable-slice.md` e
`workflows/product-quality-checkpoint.md` antes de ampliar conteúdo.
Em teste humano, registrar tarefa sem ensinar a solução, familiaridade com o
gênero, versão/ROM, tentativas, pontos de dúvida, mortes e recuperação. Separar
observação, fala do jogador e interpretação. Uma amostra pequena ajuda a achar
problemas; não prova diversão universal. Comparação A/B usa a mesma tarefa e
registra ordem/familiaridade, porque aprendizado pode explicar a melhora.
Usar os casos observados e o reviewer existentes; não criar um score de diversão.

## Física por condição, não por rótulo
Integração de `y`/gravidade vale enquanto a **altura** pede, em qualquer
estado da FSM. Amarração a `ST_JUMP` deixa o ator pendurado quando um
golpe o tira do estado — e de lá ele anda, agacha e soca no ar (L050).
`airborne()` é altura, não enum.
