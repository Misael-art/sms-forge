# 13-spec-cenas — master_of_fighters

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
| Paletas CRAM | 2 × 16: P0 para BG/HUD, P1 para todos os sprites; índice 0 transparente só para pixels de sprite; BG índice 0 sempre visível; P0 índice 0 é backdrop |
| Cores úteis simultâneas | 30 |
| Janela VBlank | ~4.5 ms (NTSC) — **não existe DMA** |
| ROM sem mapper | 48 KB |
| Padrão gráfico 4bpp | 8×8 px; 32 B; 512 padrões no total da VRAM |
| Janela de padrões para sprites | 256 padrões, selecionados pela base do reg. 6 |
| Objeto sprite | 8 px de largura; 8 ou 16 px de altura |
| CRAM | 32 entradas; até 15 cores comuns de sprite em P1; P0 usa 16 slots de BG/HUD, com índice 0 visível e reservado como backdrop no projeto |

Não existe limite físico universal de quadros por folha. O máximo por asset é
decisão de projeto, derivada de padrões residentes, compartilhamento, pools,
ROM/banking e upload por VBlank. O valor fica pendente no TDD até haver layout,
alocação e medição reais. Contagem de patterns da imagem não substitui
metasprite, SAT, sprites/scanline ou orçamento por cena.

### Prova de duas poses — Dr. Social (inventário, não orçamento de cena)
O padrão de escala está no GDD/TDD: *Fatal Fury Special* Game Gear, altura
proporcional ao viewport SMS e faixa-alvo do roster 66–72 px; canvas por pose
fica tile-alinhado e é dimensionado pelo conteúdo, não fixado em 96×96.

O candidato atual é
`data/source_art/asset_conversion_proofs/dr_social/dr_social_sms_keypose_proof_v4.json`.
Registra duas imagens 80×80 (10×10 tiles): idle com 42 padrões únicos; ação
com 47; união do par 89 (2.848 B brutos 4bpp). A v3 foi superada porque a
reamostragem achatava a terminação da bengala; a v4 usa o frame-fonte 06, em
que a ponta arredondada permanece legível. As duas são poses estáticas, não
quadros de animação, e mantêm pelo menos 1 px transparente em cada borda. A
contagem de padrões é inventário da arte, não alocação residente nem contagem
de objetos SAT. Metasprite, pico de scanline, pool VRAM/RAM, banking e carga
VBlank permanecem pendentes; não usar esses números para fechar o budget de
uma cena. O scan não encontrou ilhas opacas menores que 2 px; regiões por
material, anatomia, identidade visual do terminal da bengala e review artístico
seguem pendentes. A alocação de paleta runtime está em
`doc/palette_runtime_contract_v1.json`; não há 14 paletas de sprite separadas.

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
