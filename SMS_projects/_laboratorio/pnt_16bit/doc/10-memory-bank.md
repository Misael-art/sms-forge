# 10-memory-bank — pnt_16bit

> ESTADO OPERACIONAL REAL. **Autoridade #1** — vence qualquer outra fonte.
> Registre o que FOI OBSERVADO, nunca o que se pretende. Estado de sessão
> não substitui este arquivo.

## Última atualização
2026-09-24 — probe executado e lido mecanicamente. Veredito: **CONFIRMADO**
(name table de 16 bits com flags X/Y/sprite-paleta/priority; tile index 300
renderiza). Refuta `SMS_GLOBAL §6` na parte "1 byte por tile / sem flip /
máx 256 tiles BG".

## Eixos de entrega (7) — probe de laboratório não entrega jogo
| Eixo | Status | Prova |
|------|--------|-------|
| build | buildado | `out/rom/pnt_16bit.sms` 16384 B, SHA-256 `eaa8e8305086b06bcae2b07b05cd756ba635fc5acea9846a4c511f019799b12b` |
| validation_report | testado_em_emulador | `out/evidence/pnt_16bit_verdict.json` (8/8 predicados PASS em 4 frames) |
| boot no emulador | testado_em_emulador | `out/evidence/pnt_capture2.mp4` SHA-256 `2542169750c4dc3b82c9ed3afb5eb88f55b58507592a79ed36d1217f6eb00127`, h264 256×192, 298 frames; `screenshot_semantic_gate --claim visual` PASS |
| gameplay | não aplicável | probe não vira jogo |
| 60/50 fps | não aplicável | não é o objeto medido |
| áudio | não aplicável | ROM muda por design |
| memory bank atualizado | documentado | este arquivo |

## Decisões registradas
- **Entrada da PNT = 16 bits** (stride 2 via `XYtoADDR`, `SMSlib.h:112`), com
  `TILE_FLIPPED_X` 0x0200 / `TILE_FLIPPED_Y` 0x0400 /
  `TILE_USE_SPRITE_PALETTE` 0x0800 / `TILE_PRIORITY` 0x1000
  (`SMSlib.h:124-127`) — **PROVADO no framebuffer nativo do Emulicious**:
  B=espelhoX(A), C=espelhoY(A), D=forma de A com cor da subpaleta de sprite,
  F/G=tile 300 (índice >255) renderiza listras. Leitura: `probe_read.py`.
- **`TILE_PRIORITY` é inócuo no render do BG isolado** (célula H ≡ A): só tem
  efeito com sprite sobreposto — não promovido, fica `mapped` até teste com
  sprite.
- **`SMS_init` NÃO limpa VRAM** (achado colateral da 1ª captura,
  `pnt_capture.mp4`): tile 0 com lixo de power-on apareceu como ruído
  colorido no fundo. Todo probe/cena que usa "fundo = tile 0" precisa
  carregar tile 0 explícito.
- Limitação honesta: provado no Emulicious deste host. Revisões de VDP
  (SMS1 vs SMS2 vs GG) permanecem `mapped` — §7/§23 continuam valendo para
  comportamento revision-dependente de SPRITE; para BG, flip é função do
  próprio formato da entrada (16 bits), não registrador opcional.

## Blocker dominante atual
Nenhum para o probe (fechado). Para a curadoria: reescrever §6/§14 e as
demais 5 ocorrências da doutrina vencida + gate header↔doutrina.

## Lições abertas
- L069 (proposta): "doutrina descreveu SG-1000 como lei do SMS; sobreviveu a
  59/59 testes de host porque nenhum gate casa claims de hardware da doutrina
  com os defines do header" → vira JSON em `doc/curation/` + seção em
  SMS_GLOBAL + gate `audit_header_claims.py` (em execução na curadoria
  2026-09-24).

## Handoff
ROM e evidência seladas acima. Próximo passo (fora do probe): aplicar §6 novo
nos 7 pontos listados no plano de curadoria e rodar o gate novo sobre o repo.
