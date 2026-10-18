# 13-spec-cenas — MSSF2T

> Autoridade #3. "estimado" é proibido depois da primeira ROM. Até lá, números
> abaixo são **declarados** (não `validado_budget`) e o degrau seguinte é medir.

## Contrato de hardware
| Recurso | Limite |
|---------|--------|
| Tela | 256×192 |
| Sprites/scanline | 8 |
| SAT | 64 |
| Subpaletas | 2×16 |
| VBlank | ~4.5 ms, sem DMA |
| ROM linear | 48 KB |

## Cena 01 — golden_fight (Ken vs Guile, cais)
### Layout de VRAM declarado
| Região | Faixa | Uso |
|--------|-------|-----|
| BG 0–95 | palco + HUD |
| SPR 128–199 | lutadores + projéteis |
| name table | 32×24 |
| SAT | ≤48 entradas típicas (tiles vazios omitidos) |

### Orçamento worst-frame (MEDIDO em ROM — 2026-09-08, L061)
| Item | Bytes/frame | Método |
|------|-------------|--------|
| Stream de frame (só na troca) | ≤1024 | 32 tiles × 32 B, um lutador |
| SAT copy | 256 | SMSlib |
| Name table HUD (3 linhas) | 192 | SMS_setTileatXY |

- **Total worst-frame: MEDIDO** — `probe_vline`/`probe_vovf` no probe SMRT,
  gate `measure_worst_frame.py` no pior caso real (modo atração):
  **247/~2.700 frames derramam no VBlank (vline_max 251/262 NTSC)** com fps
  60 constante. O derrame espreme o streaming de VRAM (o banco duplo segura
  o rasgo); não derruba fps.
- **Degrau seguinte**: reduzir o stream de troca de pose (ou DMA, fora do
  MVP). Banco duplo atual já absorve o rasgo; orçamento NÃO tem folga.

### Sprites por scanline
Contrato: ≤4 por lutador na mesma linha; no clash descarta coluna de trás.
Manifest: `doc/sprite_scene_golden.json`. Gate: `audit_sprite_line_sim.py`.

### fps
MEDIDO: emulador 59.9–60 (gate `measure_fps.py`); contador da ROM via DAP
60 com derrame de VBlank em ~9% dos frames sob carga de atração
(`runtime_probe.json` + `worst_frame.json`, 2026-09-08).
