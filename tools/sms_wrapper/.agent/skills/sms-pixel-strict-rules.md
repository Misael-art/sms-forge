# skill: sms-pixel-strict-rules

## Regras de pixel SMS (VDP)
- Grid 8×8 imutável; padrão tile = 32 bytes (8 linhas × 4 bytes, 4bpp).
- Cor = código 6-bit (2 bits por canal). Paleta mestra fixa; sprite PNGs usam
  índice 0 transparente e até 15 cores úteis.
- CRAM SMS: P0 serve ao BG; P1 é usada por todos os sprites. P1 índice 0 é
  transparente para pixels de sprite. BG índice 0 é sempre uma cor visível,
  não alpha, inclusive quando o tile seleciona P1.
  Tiles BG podem selecionar P0 ou P1; nunca inferir transparência geral do
  índice 0 nem uma subpaleta CRAM independente por personagem.
- Sprite 8×8/8×16 (modo global). 16×16 na tela = zoom (pixel dobrado) ou
  metasprite (4 tiles 8×8). Nenhum modo VDP é mais largo que 8 px (L006).
- Flip e seleção de tabela de paleta por tile EXISTEM no BG (entrada de name
  table 16-bit; §6, L069, probe `pnt_16bit`). A regra de transparência por
  índice 0 se aplica aos sprites, não aos pixels BG.

## Antes de gerar
- Paleta do asset deve estar contida na paleta mestra (audit_validate_resources)
  e o contraste medido (audit_luma_floor).
- Foto/truecolor: `prepare_sms_pixel_art.py` (skill `sms-pixel-translate.md`).
  Sem preset NES/SNES/PICO-8 (L055).
