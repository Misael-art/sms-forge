# skill: sms-palette-codes

## Contrato
- Cor = código 6-bit (canais 0..3). Assets usam canal×85 = {0,85,170,255}.
- CRAM: P0 (BG) e P1 (sprites), 16 entradas cada. Sprite index 0 em P1 é
  transparente; BG index 0 em P0 é cor visível, não alpha. Todos os sprites
  compartilham P1; BG pode selecionar P1 por tile para reutilizar cores, e
  pixels BG no índice 0 continuam visíveis na tabela escolhida.
- Arquivos indexados de personagem usam índice 0 transparente e até 15 cores
  úteis. Paletas individuais de autoria não são bancos CRAM simultâneos; o
  projeto deve mapear o roster para uma única P1 comum.
- Fade = recarga de paleta no VBlank (`SMS_loadBGPaletteHalfBrightness` etc. — ver header).

## Regras
1. Nenhuma cor fora dos códigos (gate reprova).
2. Par fg/bg precisa Δluma ≥ piso (`audit_luma_floor.py`).
3. RGB físico exato varia por revisão — contratos usam CÓDIGOS, nunca adjetivos.
