# 13-spec-cenas — __PROJECT_NAME__

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
| janela de sprite (reg6) | `$FB`→$0000..$1FFF (256) / `$FF`→$2000..$37FF (192) | — | — |
| sobras reclamadas | `$3F40-$3F7F` / `$3E00-$3EFF` / `$3F20-$3F3F`+`$3FC0-$3FFF` | 2 / 8 / 3 | guardar a condição do corpus (§124/L133) |
| name table extra (reg2) | — | linhas×64 B | motivo obrigatório: duplo buffer / menu / split HBlank |

Escrever a tabela como plano JSON (`sms_vram_plan_v1`) e rodar
`measure_vram_map.py --plan <plano.json> --snapshots <sessão>` — veredito e
cross-check de reg5/reg6 citados aqui (L133, §124).

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
