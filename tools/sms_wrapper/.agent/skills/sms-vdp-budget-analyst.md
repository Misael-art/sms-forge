# skill: sms-vdp-budget-analyst

## Verdades
- VRAM 16KB (0x0000–0x3FFF), compartilhada entre patterns, name table e SAT.
  O layout é declarado por cena e registradores. Com PNT em 0x3800, a região
  anterior comporta 448 patterns de 32B; isso não garante 448 tiles BG mais
  um pool independente de sprites. BG e sprites podem compartilhar patterns.
- Em Mode 4/192 linhas, name table 32×28 entradas de 2B (1792B), com 24 linhas
  visíveis. SAT: 64 bytes Y em base+0x00 e 128 bytes X/tile em base+0x80;
  a área entre base+0x40 e base+0x7F não é um quarto byte por sprite.
  Reservar uma região de 256B não significa transferir 64×4B de atributos.
- Sem DMA: transferências em massa no VBlank, com custo medido na ROM;
  estimativa de duração do VBlank não é orçamento aprovado de transferência.
- Orçamento por cena = contrato (13-spec-cenas.md), medido não estimado.

## Tétas
- Tiles BG únicos ≤448 (entrada de name table é 16-bit; índices 0–447 — §6, L069).
- Sprites ≤64 na SAT; ≤8 por scanline. O 8 conta entradas da SAT na linha,
  visíveis ou não, em ordem de SAT; esconder com tile vazio não devolve
  orçamento (§119, L129).
- Worst-frame: contabilizar cada transferência; folga não medida = timidez (§18).
