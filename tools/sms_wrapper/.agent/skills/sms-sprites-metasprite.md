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

## Composição de dois atores (L137, §129)

Reserve o orçamento compartilhado para ambos os atores e os FX/HUD que
realmente coexistem. Revise ataque de P1 contra idle/pain de P2 **e o inverso**,
com aproximação, sobreposição, espelhamento e extremos verticais do GDD.
Priorizar SAT ou cortar células precisa preservar cabeça/tronco, identidade
e leitura do golpe; trocar partes inteiras por FPS legal reprova apresentação.

`audit_silhouette_integrity.py` lê as tabelas O3 e mede seu perfil de células
críticas. Os pisos 2/linha e o cap5 são específicos desse layout OpenBOR; não
são limites de anatomia, tamanho ou uma receita universal para MUGEN/SMS.
Outro layout exige contrato próprio e simulador compatível. O limite físico
continua 8 sprites/linha e 64 na SAT. Célula transparente também ocupa entrada.

Depois da análise estática, QA em sessão privada confere SAT/ec e framebuffer
no SHA atual: presença de células não prova pixels úteis ou contato. Veja
`workflows/subagent-emulator-qa.md` e `product-quality-checkpoint.md`.
