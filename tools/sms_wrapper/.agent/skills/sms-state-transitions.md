# skill: sms-state-transitions

Use ao projetar ou revisar FSMs com telas/estados que transferem ou preservam
estado mutável: menu, opções, treino, luta, intro/fim de round, KO, pausa,
resultado, revanche e retorno ao título. A lista real vem do GDD; exemplos não
autorizam incluir telas ou modos ausentes.

Esta skill adapta o método de ownership/teardown do SGDKForge ao SMS. Não copie
APIs nem premissas de Mega Drive. Para SMS, os headers do devkitSMS definem a
API e `sms-vram-vblank-budget.md` define as regras de VRAM/VBlank.

## Contrato de transição

Registre no TDD ou em `doc/state-transition-contract.md` cada aresta prevista:

| Campo | Pergunta que precisa de resposta |
|---|---|
| `from → to`, gatilho | Que evento permite esta mudança? |
| política de input | Que botões/edges são aceitos, descartados ou reamostrados durante a troca? |
| saída | Que ataques, hitboxes, projéteis, hitstop, shake e temporizadores são encerrados? |
| entrada | Que FSM, HUD, timer, posição e estado de round são inicializados? |
| persistente / resetado | O que atravessa a transição e o que volta ao valor contratado? |
| owners | Quem é o único dono do estado de jogo, input, SAT, padrões, name table, paletas, scroll e canal PSG? |
| trabalho VDP | Que tiles/name table mudam, em quantos bytes e em que janela segura? |
| recuperação | Se a transição for repetida, reiniciada ou interrompida, qual estado válido é restaurado? |

Estados globais têm um owner. A transição deve encerrar explicitamente o que
pertencia ao estado anterior e inicializar o destino sem deixar evento de input,
ataque, animação, timer ou FX pendente. O que permanece entre rounds — por
exemplo, placar e configuração de treino — deve ser declarado; não deixar
persistência implícita.

Não presumir fade, limpeza total ou carregamento em um único VBlank. Dimensione
transferências pelo conteúdo real e pelo pior quadro; para reescrita grande da
name table, seguir SMS_GLOBAL §6. Não transportar termos/regras de SGDK como
DMA, CRAM, WINDOW, VSRAM ou H-Int para o SMS.

## Prova na ROM

- Para animação importada, o contrato §100 associa IDs dos elementos fonte e
  ROM a N+1 fronteiras, inclusive terminal. `audit_import_semantics.py
  --require-air-identity` rejeita duração sem identidade e permutação com
  durações iguais. Revisar export e instrumentação; PASS offline não é prova
  de runtime. IDs de elementos distintos podem produzir o mesmo RGB.

- Exercitar cada transição permitida com entrada reproduzível no emulador; rodar
  também retorno, revanche e reinício quando previstos no GDD.
- Capturar vídeo para provar a mudança visível e usar probe/trilha da ROM para
  estado interno. Selar ambos contra a SHA da ROM testada.
- Medir o pior quadro da troca, incluindo uploads, HUD, sprites e efeitos; um
  estado estável não prova que a transição cabe.
- Repetir um ciclo de saída e reentrada. Confirmar que não há tecla presa,
  personagem/efeito duplicado, timer antigo, HUD desincronizado ou dados do
  round anterior vazando para o seguinte.
- Marcar como fora de escopo as arestas que o GDD não prevê; não tratá-las como
  aprovadas.

Owners relacionados: `sms-input-pause.md`, `sms-vram-vblank-budget.md`,
`sms-video-evidence.md`, `../workflows/first-playable-slice.md` e o pipeline
de cena.
