# skill: sms-vdp-tiles

## Verdades duras
- Grid 8×8; pattern table 32 bytes/tile (4bpp); **448 tiles BG (índices 0–447)**
  — name table é entrada de 16 bits por tile (§6 SMS_GLOBAL).
- **Existem** flip e subpaleta por tile no BG: `TILE_FLIPPED_X/Y`,
  `TILE_USE_SPRITE_PALETTE`, `TILE_PRIORITY` — provado no framebuffer
  (probe `_laboratorio/pnt_16bit`, L069). Variação visual = tiles distintos,
  flip, subpaleta, metatiles, ou paleta trocada.
- Name table 32 colunas; linhas visíveis por modo (192/224/240).
- **`SMS_init` NÃO limpa VRAM** (L070, probe `pnt_16bit`): "fundo = tile 0"
  só é preto se você carregar o padrão zero no tile 0; senão o power-on
  vira ruído colorido na tela.
- Scroll global X/Y. H-scroll ao vivo (`SMS_setBGScrollX` ≠ 0) **exige**
  `VDPFEATURE_LEFTCOLBLANK` (L043). Gate: `audit_hscroll_blank.py`.
- Split exige line interrupt (técnica medida). O contador dispara na
  linha N depois de recarregar no VBlank; banda vazia não prova a quebra
  (L046).

## Checklist de cena
1. Storyboard em grid 8×8 ANTES de arte.
2. Contagem de tiles únicos ≤448 (índices 0–447; metatile 16×16 quando passar).
3. Layout VRAM fixo declarado no TDD antes do primeiro asset.

## Ferramentas
- `audit_validate_resources.py --kind bg` (grid/cor/índice0)
