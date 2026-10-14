# skill: sms-sprites-metasprite

## Verdades duras
- Máx 64 na SAT; terminador Y=0xD0 **só no modo 192 linhas** (em 224/240 é Y
  comum e a SAT não trunca — §118, L128); máx **8 por scanline**: buffer de
  parsing em ordem de SAT, entrada transparente/fora da tela conta, da 9ª em
  diante some; `SMS_addSprite` grava `y − 1`, o Y proibido é 0xD1 (§119, L129).
- Tamanho GLOBAL **8×8 ou 8×16** (+ zoom ×2, que dobra o PIXEL e não a arte).
  Nenhum modo é mais largo que 8px → entidade larga = metasprite. **Sempre.**
  Detalhe e armadilhas: [`sms-sprite-geometry-modes.md`](sms-sprite-geometry-modes.md) (§25, L006).
- X armazenado **sem offset**: `SMS_addSprite(0, …)` desenha na borda
  esquerda. Early clock (`VDPFEATURE_SHIFTSPRITES`) desloca 8 px, não 32.
  Flips são revisão-dependentes → §23 (provar).
- API confirmada: `SMS_initSprites`, `SMS_addMetaSprite_f`, `SMS_copySpritestoSAT` (ver header).

## Fluxo obrigatório
coreografia → `audit_sprite_line_sim.py` (manifest sprite_scene_manifest_v1)
→ só depois runtime. Pico/linha entra no orçamento da cena.

## Truque canônico
Ordenar sprites na SAT para priorizar os importantes quando >8 ameaça uma linha
(flicker controlado > corrupção).
