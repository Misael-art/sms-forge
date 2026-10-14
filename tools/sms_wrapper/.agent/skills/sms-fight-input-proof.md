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
2. **QA atual usa frames VDP em sessão privada (§93).** `emulator_input.py
   --session ID --script` recebe P1/P2/console e duração inteira. Não usar
   sleep/foco de host entre passos, nem ampliar hist da ROM para compensar
   o instrumento. Baseline/precondição precedem o gesto; cauda neutra explícita
   permite reação/recovery. Um caso independente usa sessão nova; chained
   declara uma timeline cumulativa (§96). ACK da ponte não paga eco/ação/dano.
   DAP pausado serve diagnóstico/dump posterior, não amostra tick a tick
   (L097). Gravador ROM e vídeo durante o gesto preservam estados curtos.
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
- **Atraso do harness não é defeito do comando** (L065–L067): o legado
  kdotool+ydotool/refocus é supersedido para QA automatizada. Janela CMD e anel
  vêm do personagem; sessão privada elimina disputa de foco. Registre hist/qcf
  durante a janela do gesto; leitura tardia pode mostrar apenas neutro.
- **B1 só na borda** (L067): `qcf==1` com especial ainda idle — o botão
  chegou em HOLD. Aceitar hold na janela de 8; não crescer o hist.

## Molde histórico e prova nova

`SMS_projects/MSSF2T/tools/prove_input_memory.py` — `punch_window`,
`linha_tempo_b1`, `P1_STATES`, `_wait_fight`, whiff-punish por tempo de
relógio. O self-check dele (26 fixtures) é a regressão da lógica de
veredito.

O molde conserva o alcance da ROM/SHA e do instrumento histórico. Para nova
build, preparar pedido V2 com contexto legível (§99), identificação dos atores,
casos de whiff/hit/guard e oponente móvel/IA conforme GDD. Endereços do exemplo
não são API do SMS; derivar mapa/schema da ROM atual. Dano atribuível exige
contact state e identidade do ataque/defensor, não só pose próxima. Fonte
estática ou defensor imóvel não aprova invalidação dinâmica (§98).
