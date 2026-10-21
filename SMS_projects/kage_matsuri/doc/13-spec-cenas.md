# 13-spec-cenas — kage_matsuri

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

## Cena 01 — rua_matsuri
### Layout de VRAM declarado
| Região | Faixa | Tiles | Uso |
|--------|-------|-------|-----|
| patterns BG | 0–127 | 128 | palco 256×192 |
| patterns sprite Kage base | 128–191 | 64 | Kage 4 poses × 8 × 2 direções (dir/esq) |
| patterns sprite Samurai | 192–223 | 32 | Samurai 2 poses × 8 × 2 direções (dir/esq) |
| patterns sprite Kage ext | 224–255 | 32 | Kage slash2 + jump × 8 × 2 direções (dir/esq) |
| name table | 32×24 | — | stage_map |
| SAT | 0–21 | — | 12 corpos (4+4+4) + 10 HUD (6 pips HP + 4 ícones objetivo), modo 8×16 |

### Orçamento worst-frame (MEDIDO)
| Item | Bytes/frame | Método da medição |
|------|-------------|-------------------|
| SAT copy | 92 (23 blocos de 4 B: 22 entradas ativas + terminador) | contagem de entradas na cópia do VBlank |

- **Total worst-frame passivo**: 92 B — `worst_frame_final6.json` mediu `vline_max=4`, `vovf_delta=0` em 37 amostras/45 s no estado ROUND. O runtime NTSC passou com 59.34/59.60 quadros/s (`runtime_probe_final5.json`).
- **HUD dinâmica**: custo extra 0 B/frame fora a cópia SAT (ícones entram/saem só na montagem da tabela em RAM)
- **Método**: contagem de entradas SAT e probe VCounter/VBlank em sessão Emulicious DAP, com ROM pausada apenas durante leitura.
- **Limitação medida**: a ferramenta padrão percorre ROUND sem input; combo, SFX e transição de vitória ainda precisam de um degrau de budget dedicado antes de qualquer margem ser promovida.
- **Degrau causal medido**: `worst_frame_cycle.json` percorreu ROUND, combo, aproximação do torii e reset, alcançou `state=1`, mas registrou `vline_max=244` e `vovf_delta=67`; o budget de ação/transição está bloqueado.
- **Fora do escopo desta fatia**: dano ao jogador, projéteis/ataque do samurai e nova cena após torii não entram sem decisão no GDD.

### Sprites por scanline (pico)
Pico medido por `audit_sprite_line_sim.py doc/sprite_scene_rua_matsuri.json`:
- Sprites ativos: 22 (12 corpos 8×16 + 10 HUD 8×16)
- Pico por scanline: 6 sprites/linha (teto físico é 8). 0 violações.
- Linhas do HUD: 6 sprites/linha (y 8–23) e 4/linha (y 24–39), sem interseção com o salto (ápice y≈100).

### fps observado
Amostrado via runtime DAP: NTSC 59.34/59.60 quadros/s, avanço de 964 frames e veredito PASS.
Validação PAL real com `SMSPAL=true`: 49.37/49.42 quadros/s, avanço PASS mas `fps_constante` FAIL
porque o contrato do medidor exige a faixa regional; esse resultado não foi mascarado nem usado
para promover a entrega.

### Atualização pós-build final7

Os artefatos renovados mediram NTSC em 58.51/57.53 quadros/s e PAL em
48.99/48.22 quadros/s. O PAL continua fora da faixa regional exigida. O
medidor de ação/transição registrou `vline_max=243` e `vovf_delta=66`; não há
folga medida para promover esse degrau.

## Medição da continuidade — 2026-09-19

ROM medida: `1e6c4e9bb9e91b0b5649d8877a5a5b78bdb10c4930146f5b9bea9e5bb74a77a3`.
O degrau causal foi repetido com 7 amostras em combo/torii e registrou
`vline_max=246`, `vovf_delta=66`; permanece FAIL. O ciclo de gameplay foi
provado separadamente por RAM, portanto não se mistura gameplay PASS com
budget PASS. NTSC/PAL não têm medição fresca aceita para este SHA nesta sessão;
os números final7 permanecem históricos.
Captura nativa atual: `cycle_video_current.mp4.mp4`, 256×192, 283 frames,
4,72 s, 4/4 frames informativos; `audio_current_retry.wav.wav` isolado,
327.680 amostras, peak 3518, `audit_audio` PASS. `render_fidelity_current.json`
confirmou `kage_idle_full.png` em [206,70], 65,3% de coincidência estrutural.
