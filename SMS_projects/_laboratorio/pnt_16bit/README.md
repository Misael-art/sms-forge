# pnt_16bit — probe: a name table do SMS é de 16 bits com flags?

## Pergunta (falsificável, escrita antes do código)

**As entradas da PNT do Master System são palavras de 16 bits (stride 2, via
`XYtoADDR`), o VDP aplica `TILE_FLIPPED_X`/`TILE_FLIPPED_Y` na renderização do
BG, o bit `TILE_USE_SPRITE_PALETTE` seleciona a subpaleta de sprite por tile, e
índices de tile acima de 255 (ex.: 300) são endereçáveis?**

Se NÃO, a doutrina atual (`SMS_GLOBAL §6`: "name table = 1 byte por tile, não
existe flip nem paleta por tile, máx 256 tiles BG") está certa e o header
(`SMSlib.h:112-127`) é decorativo.

## Motivo

L0xx (curadoria 2026-09-24): §6 descreve a name table do **SG-1000** (1 byte,
sem flags) como se fosse lei do SMS. `audit_hardware_constants.py` não cobre
claims de PNT/flip — lacuna de gate. Hierarquia #8 manda o header decidir API,
mas "se não foi visto rodando no emulador, não existe" manda ver o pixel.

## Previsão registrada ANTES de rodar

- **Confirmado** se a captura do framebuffer (256×192 nativo) mostrar:
  - célula B = imagem espelhada em X da célula A (coluna sólida à direita);
  - célula C = imagem espelhada em Y de A (banda sólida no TOPO da célula);
  - célula D = tile A com COR DIFERENTE de A (subpaleta de sprite viva);
  - célula E = listras horizontais (tile 300 — índice >255 renderizado);
  - células de controle (F, G) idênticas a A, exceto cor em G.
- **Refutado** se flip não aparecer (B≡A, C≡A), D≡A em cor, ou E não renderizar
  (VRAM wrap em 256) — nesse caso §6 permanece e o header ganha um errata.
- VDP SMS1 tem relatos de flip ignorado em revisão antiga? Não conto "revisão":
  provado só no Emulicious deste host; revisão de hardware fica `mapped`, não
  `proven`, até medida em console/outra engine.

## Leitura mecânica

`probe_read.py` (neste diretório) recorta as 8 células da captura 256×192 e
compara com a imagem esperada CALCULADA do próprio `tile_a[32]` definido no
`src/main.c` — sem depender de doc externa de cor/planar. Veredito do probe é
o JSON que ela imprime + memória no `doc/10-memory-bank.md`.
