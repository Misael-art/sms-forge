# sms-fight-input-proof — prova de golpe de luta contra IA (L060)

Skill do SMSForge. Vale para qualquer projeto de jogo de luta (MSSF2T é o
molde). "O golpe às vezes conecta" é um sintoma, não um diagnóstico — e a
leitura de código da caixa de colisão NÃO é resposta.

## A regra em três cláusulas executáveis

1. **O estado do oponente entra na prova.** Toda tentativa de golpe registra
   o byte de estado/guarda do defensor junto do resultado (no molde MSSF2T:
   `P[1].state` em 0xC027, `P[1].guard` em 0xC02F — derivados de `_P` no
   `.map` do linker + `sizeof(Fighter)`). Whiff sem estado do defensor não
   tem causa atribuível.
2. **Cronometragem é por tempo de relógio, com o emulador RODANDO contínuo.**
   Polling DAP pausado tem granularidade de 2-4 frames por ciclo; janela de
   frames fixa erra por ±8 px (medido no MSSF2T, 2026-09-08). O polling só
   acha o GATILHO (ex.: `P[1].state == ST_PUNCH`); as respostas (recuar X ms,
   entrar Y ms, apertar) são `sleep` de relógio sobre teclas seguradas.
3. **Atribuição de dano exige dano compatível com o golpe.** Tabela do
   projeto (molde MSSF2T: soco 7, chute 10, projétil 12, chip de guarda 2).
   Queda de 10 com "pose de soco por perto" é CHUTE — janela de associação
   de pose apertada (±2 amostras) e dano checado.

## Armadilhas já pagas (não repetir)

- **Teoria de leitura de código não é medição**: a "janela de 4 px"
  (PUSH_W=20 vs caixa gap<24) parecia a causa e era falsa — a IA recua
  andando com guarda quando o jogador ataca em `(g_frame & 8)`.
- **Guardar não é parar** neste molde de motor: segurar tras ANDA
  (ST_WALK_B, 2 px/frame) — "guarda parada" abriu gap 30/42 na janela ativa.
- **Agachar esquenta o soco mas o chute pega**: box alta whiffa em agachado
  (18..32 vs 34..60) e chute acerta (40..58 vs 34..60) — agachado não é
  posição segura, é meia imunidade.
- **A resposta mais rápida perde a troca**: com startups iguais, quem começa
  primeiro vence — reagir ao soco da IA socando junto é perder; o que vence é
  whiff-punish (sair do alcance no startup dela, entrar na recovery dela).
- **Round acaba no meio da prova**: a prova de input precisa de
  `_wait_fight` entre tentativas (KO/RESULT/TÍTULO matam input de jogo) e
  re-aproximação depois de reset de round.
- **Foco por teclado custa 1-2 s**: `ensure_focus` entre o gatilho e a tecla
  arruína a janela — garantir foco ANTES da espera, nunca entre gatilho e
  aperto.
- **CLI do usuário**: o canal é kdotool (foco KWin/DBus) + ydotool (uinput)
  — L039. xdotool/XTEST não atravessa Wayland/KWin.
- **Refoco entre teclas de um QCF** (L065): `press_spec` default reativa a
  janela a cada passo (~300 ms no Wayland = ~18 frames). Hist de 8 ticks
  (~133 ms) perde o Down. Usar `refocus=False` no gesto. Não alargar o
  buffer do jogo (L067).
- **Amostra do hist depois da janela** (L066): 0,9 s depois só há neutro.
  Ler hist/qcf no máximo alguns frames após o A.
- **B1 só na borda** (L067): `qcf==1` com especial ainda idle — o botão
  chegou em HOLD. Aceitar hold na janela de 8; não crescer o hist.

## Molde vivo

`SMS_projects/MSSF2T/tools/prove_input_memory.py` — `punch_window`,
`linha_tempo_b1`, `P1_STATES`, `_wait_fight`, whiff-punish por tempo de
relógio. O self-check dele (26 fixtures) é a regressão da lógica de
veredito.
