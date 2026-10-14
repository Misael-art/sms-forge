# skill: sms-input-pause

## Input
- Joypad: portas 0xDC/0xDD (2 pads), d-pad + 2 botões.
- Ler uma vez por frame no loop principal; debouncing por frame counter.
- Prova de agência = eco real na ROM (`probe_keys`) + consequência do ator
  identificado na direção do comando. QA automatizada usa
  `emulator_input.py --session ID --script roteiro.json`: P1/P2, console e
  frames VDP inteiros, sem foco/teclado/joystick físico do host (§93).
  ACK recebido/aplicado pela ponte não prova consumo nem golpe da ROM.
  Sequência libera controles ao concluir/falhar; baseline/precondição precedem
  o gesto. Teste neutro e outro pad distinguem agência de demo/IA (L038).
  A rota histórica kdotool+ydotool é supersedida para QA automatizada;
  `input_memory.json` histórico não aprova build nova.
- Tempo de QCF/tiers vem do contrato CMD do personagem e do anel de frames.
  Não aumentar a janela do jogo para compensar atraso do instrumento
  (L065–L067); testar acordes não mapeados, hold/edge e facing conforme GDD.
- Libs opcionais (raphnet inlib) para light phaser/paddle — só com necessidade real.

## Pause
- Botão pause do console dispara NMI (`SMS_nmi_isr` do crt0).
- Tratamento: flag + retorno rápido; lógica pesada no loop principal.
- Estado PAUSE declarado na FSM global do TDD.
- Pause do console, estado PAUSE da ROM e pausa técnica do emulador são
  distintos. Roteiro usa o campo `console`; stepping não mede FPS contínuo.
  Endereços e masks de fixture são dados de teste, não constantes de outro jogo.
