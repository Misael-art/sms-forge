# 15-tdd — kage_matsuri

> Autoridade #7. API = `SMSlib.h` / `PSGlib.h`.

## Restrições
Sem float, sem malloc, sem DMA. ≤8 sprites/scanline, SAT 64, RAM 8 KB.
H-scroll (débito) exigirá `VDPFEATURE_LEFTCOLBLANK` (L043). Esta fatia
não liga LEFTCOLBLANK: palco 256×192, câmera fixa.

## Entidades
Dois `Actor` estáticos: player e até 2 samurais. Pools sem malloc.

## Poses (Kage)
idle (0), walk0 (1), walk1 (2), slash1 (3), slash2 (4), jump (5).
Facing direito empacotado; esquerdo = tiles espelhados offline (bitrev),
não flip em runtime (L045).

## Gravidade
`apply_gravity` em qualquer estado. `airborne` = `y < GROUND_Y` (L050).

## Combo
B1 → SLASH1 (12 frames, pose 3, hitbox à frente). Se B1 de novo nos frames 6–12 →
SLASH2 (14 frames, pose 4, hitbox mais larga, alcance extra de 18 px). Cada golpe tem um `attack_id`
próprio e acerta cada samurai no máximo uma vez; o segundo golpe pode
completar a derrota sem dano repetido do mesmo frame. O feedback de
recuo/piscar usa `hit_cd=4`. Sem terceiro hit. No ar sem golpe → jump (pose 5).

## VRAM
| Tiles | Uso |
|-------|-----|
| 0–127 | palco (128 tiles após merge RGB) |
| 128–159 | Kage base 4 poses × 8 tiles (direita, ordem 8×16) |
| 160–191 | Kage base 4 poses × 8 tiles (esquerda, bitrev offline L045) |
| 192–207 | Samurai 2 poses × 8 tiles (direita) |
| 208–223 | Samurai 2 poses × 8 tiles (esquerda) |
| 224–239 | Kage ext (slash2 + jump) × 8 tiles (direita) |
| 240–255 | Kage ext (slash2 + jump) × 8 tiles (esquerda) |

`SMS_setSpriteMode(SPRITEMODE_TALL)`. `SMS_useFirstHalfTilesforSprites(1)`.

## RAM probe (L035/L054)
| Addr | Campo |
|------|-------|
| 0xC7F0 | probe_frame (word) |
| 0xC7F2 | probe_hp |
| 0xC7F4 | probe_kills |
| 0xC7F6 | probe_state |
| 0xC7F8 | probe_keys |
| 0xC7F9 | probe_pose |
| 0xC7FA | probe_px |
| 0xC7FB | probe_py |
| 0xC7FC | probe_s0_hp |
| 0xC7FD | probe_s0_alive |
| 0xC7FE | probe_s1_hp |
| 0xC7FF | probe_s1_alive |
| 0xC7EA | probe_vline (VCounter no fim do trabalho do frame) |
| 0xC7EB | probe_vovf (contador saturante de derrame no VBlank) |
| 0xC7EC | probe_s0_x |
| 0xC7ED | probe_s1_x |

## Probes
`probe_frame` é zerado em todo `reset_game()` e incrementado uma vez por
frame. O cabeçalho `SMRT`/schema é escrito antes do display on. `probe_vline`
é amostrado depois da montagem/cópia da SAT e antes do próximo VBlank;
`probe_vovf` conta saturadamente amostras com `VCounter >= 0xC0`. Isso permite
medir o worst-frame com `measure_worst_frame.py`, sem inferir tempo a partir de
FPS ou de pixels.

## HUD
Camada de sprite, **sem tile novo** (recursos de cena): pips de vida = tiles
128/130 (cabeça do Kage idle) em y=8, x=8/24/40 (contrato `player_hp`);
samurais restantes = tiles 192/194 (samurai idle) em y=24, x=200/216 (contrato
`goal_torii`). Ícones encolhem da esquerda para a direita conforme `hp`/`kills`.
Redesenho por frame é só montagem de SAT em RAM — custo extra de VRAM = 0 B
fora a cópia. SAT pior caso: 22 entradas (teto 64); pico 6 sprites/linha
(`audit_sprite_line_sim.py doc/sprite_scene_rua_matsuri.json`).

## Áudio
PSGlib. Ostinato curto + SFX slash no canal autorado (L041).

## Input
`SMS_getKeysStatus()`. Prova neste host: `emulator_input.py` (L039).

## Estado de integração provado — 2026-09-09
`full_cycle_memory.json` é a prova RAM da ROM SHA `283e250a…`: dois edges de
B1 no combo, cada golpe acerta no máximo um samurai por `attack_id`, os dois
samurais chegam a `alive=0`, o torii é `state=1` com B1 ainda segurado e um
novo edge reinicia `state=0`, `kills=0`, `alive=1/1`. `runtime_probe_final5.json`
passou em NTSC (59.34/59.60 quadros/s; 964 frames). `runtime_probe_pal_final5.json`
confirma boot/avanço PAL, mas mede 49.37/49.42 quadros/s e falha honestamente na
faixa regional exigida.

Atualização pós-build final7: `runtime_probe_final7.json.json` confirma avanço
NTSC em 58.51/57.53 quadros/s; `runtime_probe_pal_final7.json.json` confirma
avanço PAL, mas 48.99/48.22 quadros/s e FAIL regional. A prova RAM renovada
continua separada do budget: gameplay PASS, budget de ação FAIL.

`worst_frame_final6.json` passou com `vline_max=4` e `vovf_delta=0` em 37
amostras de 45 s. Como o medidor padrão não injeta input, esse número cobre
ROUND sem input; `worst_frame_cycle.json` alcançou combo/torii mas falhou com
`vline_max=244`/`vovf_delta=67`, portanto não há promoção para budget fechado.

## Continuidade de integração — 2026-09-19

ROM canônico atual: `1e6c4e9bb9e91b0b5649d8877a5a5b78bdb10c4930146f5b9bea9e5bb74a77a3`.
O probe de gameplay confirmou por RAM `combo_1`, `combo_2`, `state=1/px=202`
e reset `state=0/kills=0/alive=1/1`. O probe de budget confirmou o derrame
causal em `vline_max=246`, `vovf_delta=66`; o contrato continua sem folga
promovível.

Os instrumentos locais passaram a aguardar a janela do Emulicious antes de
`initialize/attach` e a iniciar com `-set Update=0`, após NPE de debugger nas
tentativas de renovação. Isso não altera o protocolo central nem o ROM. A
evidência NTSC/PAL, áudio/vídeo e review ainda precisam ser renovados após uma
sessão DAP estável; não são atuais por hash apenas por serem final7.
Captura visual e áudio foram renovados separadamente após o build: vídeo nativo
256×192 com 283 frames e áudio isolado com 327.680 amostras; ambos estão no
bundle fresco parcial. A captura estática branca foi descartada, não usada como
prova de boot.
