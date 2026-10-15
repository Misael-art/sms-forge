# vscroll_wrap224 — probe: o reg9 do VDP trata >223 como 0..31 no modo 192?

## Pergunta (falsificável, escrita antes do código)

**No modo 192 linhas, o scroll vertical lido do VDP (reg9) com valor >223 é
tratado como se valesse `valor-224` (240 ≡ 16, 224 ≡ 0, 255 ≡ 31) — render
pixel a pixel idêntico ao valor equivalente — e valores ≤223 são todos
distintos (em particular 240 NÃO equivale a 192 nem a 0)?**

Se NÃO, a lei Tier-1 do corpus SMSPower (`Tilemap.txt`, selo em `SMS_GLOBAL §6`,
lição L131/§122) não se reproduz no emulador-alvo e o gate
`audit_vscroll_wrap.py` continua sendo prosa sobre aritmética não medida.

## Motivo

L131 entrou como `documentado_com_gate_novo; sem medição em emulador ou
console`. A verificação futura declarada no ledger é exatamente esta: medir
reg9 no emulador. É o andar 3 da campanha de curadoria SMSPower (2026-10-14).

## Desenho

ROM em modo 192: tilemap de 28 linhas preenchida com código de linhas em 4
tiles geométricos (bit0=paridade de linha em listras, bit1=aceso/apagado,
bit2=meia-altura, bit3=topo-vs-base) — a grade 24×32 na tela decodifica o
índice da linha superior da tilemap. O jogo clica o botão **B** (máscara 16 no
roteiro BlastEm) para avançar por `PHASES = {0,16,31,192,223,224,240,255}` e
escreve o valor ao vivo em `SMS_setBGScrollY(v)` todo VBlank. Marcador
`volatile __at(0xC7D0)` com magic `SIV1`, fase e valor. Uma sessão BlastEm por
valor (injeção de botão pelo debugger, determinística); o screenshot nativo
256×192 é do estado final; `vdp_regs.bin` de cada fronteira prova o byte do
reg9 escrito; `ram.bin` prova a fase viva.

## Previsão registrada ANTES de rodar

- **Confirmado** (comportamento igual à lei do corpus, no emulador):
  - screenshot(v=240) idêntico pixel a pixel a screenshot(v=16);
  - screenshot(v=224) idêntico a screenshot(v=0);
  - screenshot(v=255) idêntico a screenshot(v=31);
  - screenshot(v=240) DIFERENTE de screenshot(v=192) (o envoltório é 224,
    não truncamento em 192 nem módulo 256);
  - byte 9 de `vdp_regs.bin` == o valor cru escrito (240 fica 240 no
    registrador; o envoltório é do VDP, não da CPU).
- **Refutado** se v=240 renderizar como v=0 (mascaramento &31), como v=240
  real (furo de 16 linhas), ou diferente de v=16 de qualquer forma estável.
- **Inconclusivo** se o screenshot vier monocromático/congelado, o baseline
  de precondição falhar, ou o decoder de linhas não identificar a linha
  superior com confiança.

Marcador de wrap explícito na ROM: esta ROM **não** aplica `%224` na
variável — é o probe da lei do VDP, não o acumulador do jogo. O gate
`audit_vscroll_wrap.py` decide este arquivo como `não provado` (expressão
não-literal), o que é o comportamento declarado dele, não uma falha.
