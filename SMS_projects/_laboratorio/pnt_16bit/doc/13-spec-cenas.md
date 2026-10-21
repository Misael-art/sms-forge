# 13-spec-cenas — pnt_16bit

> Budget REAL por cena. **Autoridade #3.**
> Regra: **"estimado" é proibido neste arquivo.** Todo número aqui é medido,
> com o método da medição citado. Folga não medida é timidez (§18).

## Contrato de hardware (fixo, não negociável)
| Recurso | Limite físico |
|---------|---------------|
| Tela | 256×192 |
| VRAM | 16 KB |
| RAM | 8 KB |
| Sprites por scanline | 8 |
| Sprites na SAT | 64 |
| Subpaletas | 2 × 16 (índice 0 transparente nas duas) |
| Cores úteis simultâneas | 30 |
| Janela VBlank | ~4.5 ms (NTSC) — **não existe DMA** |
| ROM sem mapper | 48 KB |

## Cena 01 — _(nome)_
### Layout de VRAM declarado
| Região | Faixa | Tiles | Uso |
|--------|-------|-------|-----|
| patterns BG | — | — | — |
| patterns sprite | — | — | — |
| name table | — | — | — |
| SAT | — | — | — |

### Orçamento worst-frame (MEDIDO)
| Item | Bytes/frame | Método da medição |
|------|-------------|-------------------|
| — | — | — |

- **Total worst-frame**: _(medido)_ bytes
- **Headroom**: _(medido)_ %
- **Método**: _(como foi contado — contagem instrumentada, não estimativa)_
- **Degrau seguinte medido**: _(§18: qual o próximo incremento e ele cabe?)_

### Sprites por scanline (pico)
_(rodar `audit_sprite_line_sim.py` sobre o manifesto da cena e citar o pico real)_

### fps observado
_(rodar `measure_fps.py`; ≥5 amostras, todas 50–60. Citar o JSON.)_
