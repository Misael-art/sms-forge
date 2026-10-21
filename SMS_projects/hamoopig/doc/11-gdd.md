# 11-gdd — HAMOOPIG SMS

> Autoridade #2. Se não está aqui, não entra.

## Princípio de jogo (trava de agente)
Régua **AAA de luta**, não de probe. Personagem sem ciclo da origem (idle/walk
≥4, golpe ≥3 quando a folha tiver) **não entra e não se declara pronto**.
Vale para **todos** os lutadores do roster (Ryo e Musgo). Evidência = ciclo
visto no emulador (vídeo ou stills com pose distinta). O selo de fábrica
`ready_for_aaa` é outro gate (7 eixos + `delivery`); não rebaixa esta régua.
Ver `doc/00-diretrizes-agente.md`.

## Pitch (1 frase)
Engine de luta 1v1 HAMOOPIG reimplementada para Sega Master System: abertura, título, seleção, combate com FSM, caixas, rounds e HUD, dentro dos limites reais do VDP/Z80.

## Gênero declarado
fighting

## Loop central
Escolher lutadores → aproximar/afastar → normal ou especial → guarda ou hitstop → barra cai → KO/tempo → round → revanche ou título.

## 5 Leis
- **Agência**: D-pad move, B1 soco, B2 chute, recuar guarda, cima pulo; o sprite controlado desloca na direção comandada.
- **Feedback**: hitstop, barra, banner ROUND/FIGHT/K.O./DRAW/TIME, **ciclo** idle/walk e pose de golpe distinta da idle (não silhueta parada).
- **Fluxo**: P2 começa DUMMY; CPU e 2P humano existem no contrato de controle.
- **Consistência**: mesmo comando no mesmo estado produz o mesmo startup/active/recovery.
- **Recompensa**: round ganho, melhor de 3, pose de vitória, revanche.

## Cenas
| # | Nome | Escopo | Status |
|---|------|--------|--------|
| 0 | OPENING | Crédito HAMOOPIG/GameDevBoss + porta SMSForge | implementado |
| 1 | TITLE | B1 inicia | implementado |
| 2 | SELECT | P1 troca ID, B1 confirma; P2 opcional | implementado (stub visual) |
| 10 | FIGHT | Arena técnica, dois lutadores, rounds | implementado (arte técnica) |
| 11 | AFTER_MATCH | Resultado, B1 revanche, Pause título | implementado |

## Roster previsto (origem HAMOOPIG)
| ID | Nome | Papel | Arte no SMS |
|----|------|-------|-------------|
| 1 | Ryo | lutador originário da engine | tradução SMS 32×64 das folhas da origem (molde MSSF2T; fan / pessoal) |
| 2 | Ken | presente na origem; pixels Capcom **não** entram | reservado; sem sprite comercial |
| 3 | Musgo | grappler autoral da origem | mesmos ciclos que Ryo (idle/walk/golpe), tradução 32×64 |
| — | Kensaiden | protagonista próprio, **depois** do núcleo estável | não iniciado |

## Adaptação de input (recuo declarado)
Mega Drive: 6 botões. SMS: D-pad + 2 botões + Pause/NMI.
- B1 = soco / confirma / especial (QCF+B1). Especial aceita B1 **hold** enquanto o QCF ainda está nos 8 ticks de direção (não alarga o buffer).
- B2 = chute. **Down+B1** = chute se B2 não existir no teclado.
- Throw: B1+B2 **ou** frente+B1 a gap ≤ 24 (dano 10, ignora guarda).
- Recuar = guarda (chip 2). Select **Down** = P2 dummy BLOCK (parado).
- Pause = sair da luta para o título
Forças L/M/H colapsam em um normal por botão; distância ainda escolhe o move da tabela.

## Fora de escopo (desta fase)
- Copiar pixels/áudio comercial da origem (Ken arcade, MIDI/VGM de terceiros)
- YM2413/FM, 6 botões, SRAM, netplay
- Personagem Kensaiden antes do ciclo completo da engine
- Pose estátua / silhueta de retângulo como personagem

## Animação (contrato — os dois lutadores)
Idle e walk: ≥4 quadros distintos, loop, duração ≥10 ticks (teto do stream 96 B).
Golpes: 3 quadros quando a folha tiver (startup/active/recovery visuais).
Musgo não fica com ciclo menor que o teto da própria folha. O estado de ataque
espera o último quadro; a hitbox continua no timer do MoveDef.
ROM 64–128 KB, tiles em banks 2+ (slot 2).

## Teto de claims aprovado
`protótipo jogável de engine de luta 1v1` com ciclos de animação na luta.
Não é paridade de pixels com Mega Drive. `ready_for_aaa` false até os 7 eixos
+ época visual `delivery` (a fábrica não carimba AAA nesta ROM).

## Contrato de engine
Núcleo não conhece nomes de golpes no tick: `FighterDef` / `MoveDef` compilados.
Contatos em snapshot; HUD/render só consomem o evento. Reset de round zera timers, hist, projéteis, hitstop e resultado.
