# 11-gdd — arena_nocturna

> Design e escopo. **Autoridade #2 — "se não está no GDD, não entra."**

## Pitch (1 frase)
VANTA-9 atravessa uma arena orbital deco, encara um guardião gordo e abre
caminho com disparos de energia em uma única tela de ação.

## Gênero declarado
action_shooter — arena top-down de uma tela, com movimento livre, tiro,
colisão, hitstop, invulnerabilidade e progressão de pontuação.

Eixos congelados: agencia, feedback_de_dano, sprites_8x8 (tiles-base dos
metasprites), scroll, dificuldade_progressiva e hitstop.

## Loop central
Mover no d-pad → posicionar o courier → disparar → o guardião perde um ponto
de núcleo ou devolve um contra-ataque → sobreviver e manter a pontuação viva.

## 5 Leis Fundamentais — como este jogo atende
- **Agência**: d-pad desloca VANTA-9 e o botão 2 cria um projétil visível.
- **Feedback**: acerto gera pontuação, som e reduz o núcleo do guardião;
  contra-ataque gera hitstop, flash e perda de HP.
- **Fluxo**: o guardião anuncia cada disparo com um estado de telegrafo
  visível e devolve projéteis em pulsos previsíveis; a fase (ligada ao
  núcleo) e a onda (ligada ao tempo) apertam a cadência sem saturar a linha
  de sprites.
- **Consistência**: boot, posições, velocidade inteira e colisões são
  determinísticos; o contador de frames é exposto no HUD.
- **Recompensa**: cada núcleo atingido vale 10 pontos e preserva o ritmo.

## Cenas planejadas
| # | Nome | Escopo em 1 linha | Status |
|---|------|-------------------|--------|
| 00 | título | atração, instrução de controle e partida por botão 1 | implementado (arte encomendada) |
| 01 | arena orbital | sobreviver, mover, atirar e pontuar na sala deco | implementado |
| 02 | pausa | congela a partida sem perder estado | implementado |
| 03 | desfecho | queda do guardião ou brecha no núcleo, com reinício | implementado (poses encomendadas) |

## Fora de escopo (explícito)
> Escrever o que NÃO entra é o que torna o escopo travável.
- campanha, múltiplas salas, loja e save;
- paralaxe multicamada (o VDP tem um plano de BG; exigiria interrupção de
  linha, que não está implementada);
- sprite espelhado por atributo — o VDP não oferece flip em sprites, virar o
  hero custa tiles novos na ROM;
- YM2413/FM e modo Game Gear;
- marketing comercial, publicação ou fidelidade perfeita sem gates adicionais.

## Teto de claims aprovado
vertical slice gráfico jogável para Master System; sem superlativo comercial.
