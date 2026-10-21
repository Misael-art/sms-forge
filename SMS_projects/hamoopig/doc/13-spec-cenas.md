# 13-spec-cenas — hamoopig

> Autoridade #3. "estimado" é proibido. Números abaixo sem método = **não medidos**.

## Contrato de hardware (fixo)
| Recurso | Limite físico | Fonte |
|---------|---------------|-------|
| Tela | 256×192 | SMS_GLOBAL §6 / VDP |
| VRAM | 16 KB | SMS_GLOBAL |
| RAM | 8 KB | `--data-loc 0xC000` |
| Sprites/scanline | 8 | SMS_GLOBAL §7 |
| SAT | 64 | SMS_GLOBAL §7 |
| Subpaletas | 2×16, índice 0 transparente | §8 |
| VBlank | ~4.5 ms NTSC, sem DMA | §9 |
| ROM | 128 KB (mapper Sega, banks 2–4) | v014; código em 0x0000–0x7FFF |

## Cena TITLE / OPENING
### Layout de VRAM declarado
| Região | Faixa | Uso |
|--------|-------|-----|
| BG | 1–41 | fonte |
| SAT | vazia | sem sprites |

### Orçamento worst-frame
Ainda **não medido**. Método previsto: `measure_worst_frame.py` + probe `vline`.

## Cena FIGHT (arena 32×64, molde MSSF2T)
### Layout de VRAM
| Região | Faixa | Uso |
|--------|-------|-----|
| BG fonte/HUD | 1–51 | texto, chão, barras |
| sprites P1 | 96–159 | dual-bank pose |
| sprites P2 | 160–223 | dual-bank pose |
| projétil | 224–231 | hadouken + espelho |
| SAT | até ~36 | metasprite 32×64 + 2 sprites de projétil |

### Sprites por scanline (pico declarado, não simulado ainda)
8 quando os dois lutadores compartilham linhas. Manifesto de simulação pendente.

### fps / worst-frame
fps do loop (probe, SHA `7a8951ee…`): janela 1 = 58.2; janela 2 = 28.12 (não constante).
Worst-frame (`worst_frame.json`, 20 s): **derramou**, vovf_delta=597, vline_max=255. Folga zero.
