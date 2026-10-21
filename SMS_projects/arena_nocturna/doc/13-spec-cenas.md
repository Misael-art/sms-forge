# 13-spec-cenas — arena_nocturna

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

## Cena 01 — arena orbital
### Layout de VRAM declarado
| Região | Faixa | Tiles | Uso |
|--------|-------|-------|-----|
| patterns BG | 0x0800–0x17FF | tiles 64–191 | 128 tiles deduplicados |
| patterns sprite | 0x1800–0x1DFF | tiles 192–239 | hero idle 4, hero walk 4, boss idle 16, boss charge 16, tiro 1, impacto 1, counter 1 |
| name table | 0x3800 | 32×24 | arena_bg_map |
| SAT | 0x3F00 | 64 entradas | 22 entradas máximas nesta cena |

### Orçamento worst-frame (MEDIDO)
| Item | Bytes/frame | Método da medição |
|------|-------------|-------------------|
| carga inicial de tiles e mapa | 4.352 | display off, antes do loop |
| HUD + SAT por frame | 96 | após SMS_waitForVBlank; contar chamadas e SAT |

- **Total worst-frame**: medição instrumentada de bytes ainda pendente; o
  contrato provisório acima não fecha o eixo de budget de VBlank.
- **Headroom**: pendente da medição instrumentada.
- **Método**: contar `SMS_printatXY`/writes e validar SAT com o manifest; a
  medição não deve ser inferida do tamanho da ROM.
- **Degrau seguinte medido**: adicionar um segundo counterattack somente após
  uma nova medição de sobreposição; o contrato atual mantém um projétil ativo.

### Sprites por scanline (pico)
Manifesto: `doc/sprite_scene_arena.json`; o pior arranjo contém 16 células do
boss zoomado, 4 do hero zoomado, um counterattack e um tiro ou impacto (o FX
substitui o tiro no acerto), pico 8/8 no simulador (22 entradas na SAT). O
limite está fechado por medição do manifest.

### fps observado
`out/evidence/fps.json`: 6 amostras a 60, média 60,0; contador interno em
`out/evidence/frame_advance.json`: 7 transições, ritmo medido 59,7 (célula
28,1, troca observada em 256 frames, sobreamostragem 35,0×).
