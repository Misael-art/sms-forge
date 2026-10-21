# 16-storyboard — pulso_de_cristal

> Planta baixa em pixel por cena (ordem de trabalho de cena: roteiro →
> **storyboard** → coreografia → medição → orçamento → contrato de asset).
> Coordenadas em pixels de tela 256×192; grade de tiles 8×8 (32×24 células).
> Nenhum número aqui é budget fechado: budget só existe medido (13-spec-cenas).

## Cena 01 — título "o vale congelado"

### Planta baixa (name table, 32×24 tiles)
| Zona | Linhas (tiles) | Pixels | Conteúdo | Subpaleta |
|------|----------------|--------|----------|-----------|
| céu/montanha distante | 0–5 | y 0–47 | fundo profundo + silhueta de montanha em 2 degraus | BG0 (azuis) |
| planície de gelo | 6–13 | y 48–111 | campo de gelo com fissuras; cristais altos em silhueta | BG0 |
| wordmark | 4–6 | x 40–215 (col. 5–26) | "PULSO DE CRISTAL" — 12 tiles de arte autoral, ~144×16 px | BG1 (branco+ciano) |
| cristais frontais | 14–19 | x variável, âncora y 112–159 | 5 agregados de cristal em 2 tamanhos (props do tileset) | BG1 nos toques de luz |
| prompt START | 20–21 | x 104–151 (col. 13–18) | "START" em 6 tiles de arte autoral | BG1 |
| medidor de compasso (HUD) | 22 | col. 2–5 (x 16–39) | 4 células de 8 px; célula k acende no pulso k do pulso-base da faixa | BG1 |
| vinheta frontal | 22–23 | — | gelo escuro de moldura | BG0 |

- Sprites na cena 01: **nenhum** até prova de necessidade (declare; spec-cenas
  §cena01 já exige essa prova).
- Contraste: wordmark START/células do medidor sobre suas zonas —
  `audit_luma_floor.py` mede depois da arte, não aqui.

### Coreografia (beats do roteiro → tempo em frames a 60 fps)
| t (frames) | Evento | Dono |
|------------|--------|------|
| 0 | tela preta; `sfx_chime` isolado em SFX_CHANNEL2 (literal já auditado) | AUDIO_FSM |
| 40 | rampa de atenuação do lead inicia (att 12→4 ao longo de 120 f, 1 att/20 f por incremento) | AUDIO_FSM |
| 45 | `PSGPlay(music_title)` entra em loop | AUDIO_FSM |
| 46–286 | name table revelada 1 linha/2 frames (24 linhas × 2 f = 48 f de escrita, escalonada; MEÇAO: 12 writes/linha por VBlank cabem? medir antes de subir para 2 linhas — degrau seguinte) | VDP_FSM |
| 130–170 | wordmark (linhas 4–6) entra com a revelação (mesmo motor, sem mecanismo próprio) | VDP_FSM |
| ~960 (compasso 31) | primeiro loop point: `frame % 1536 == 0` e frame>0 → prompt START aparece + medidor pulsa | GAME_FSM |
| todo compasso (fp=8 f) | célula k do medidor acende (k = compasso % 4) — incremento, sem divisão | HUD_FSM |
| START pressionado (borda de subida) | transição TITLE→FADE_DAWN | GAME_FSM |

Revelação: escrita linha a linha **dentro do VBlank**, com contagem
instrumentada (probe_vline/vovf); N linhas/frame é número MEDIDO, não aqui.

## Cena 02 — aurora

| Zona | Linhas | Conteúdo | Subpaleta |
|------|--------|----------|-----------|
| céu da aurora | 0–8 | horizonte que clareja por troca de paleta em degraus (rampa declarada: 6 passos de BG0, 30 f entre passos, disparada por compasso) | BG0 |
| vale + cristais | 9–20 | os mesmos agregados da 01 + 8 cristais de primeiro plano; cada cristal é prop autoral com 2 variantes de tile (apagado/aceso) trocadas em VBlank quando o lead ataca | BG1 |
| letreiro AURORA | 2–3 (só 60 primeiros frames) | 6 tiles de arte autoral, some após 4 s | BG1 |

- Pool de cristais (TDD): 8 × 8 B; foco = índice do cristal aceso mais recente.
- SELECT (borda de subida) → `sfx_crystal` em SFX_CHANNEL1 + cristal em foco
  acende imediatamente (mesmo frame do handler; GDD "Feedback").
- `music_dawn` em loop; nenhuma sprite (cristais acesos são swap de tile BG).

## Cena 03 — tempestade

| Camada | Conteúdo | Mecanismo |
|--------|----------|-----------|
| plano 1 (BG) | céu de nuvens em faixas; scroll lento (VCounter/HScroll por linha dentro do budget medido) | name table 0 |
| plano 2 (sprites) | estilhaços: pool de 24 × 4 B; metasprite 8×16; velocidade cresce com a intensidade do compasso (tabela de passo, sem divisão) | SAT |
| flash | relâmpago = troca da subpaleta BG1 inteira para branco em 2 frames, em sinc com hits de ch3 da partitura (tabela de frames de hit derivada da partitura no build — dado, não runtime) | CRAM |

- Pico SAT declarado: 24 estilhaços → 24 entradas (limite físico 64 ok);
  pico por scanline: **rodar `audit_sprite_line_sim.py`** com manifesto
  `tools/scene_manifest_cena03.json` ANTES de qualquer claim.
- `sfx_crack` em SFX_CHANNEL1 quando estilhaço cruza a zona frontal —
  worst-frame com `music_storm` + SFX simultâneos é medição obrigatória
  (fome do ruído: medir, não temer — roteiro).
- Letreiro TEMPESTADE: 10 tiles, linhas 2–3, primeiros 90 frames.

## Cena 04 — eco + créditos

- Fundo: vale com cristais APAGADOS na ordem inversa do acendimento (memória
  de estado em 1 byte de máscara + ponteiro); `music_eco` em
  **PSGPlayNoRepeat** (única não-loop do corpus — gatilho de créditos via
  `PSGGetStatus()==PSG_STOPPED`, TDD §Áudio).
- HUD: contagem de compassos tocados no ciclo (uint16 incrementado por
  tabela fp — não divide).
- Créditos: 6 linhas ≤20 chars em tiles de fonte autoral; rolagem vertical de
  1 linha a cada 30 frames dentro do VBlank (~32 tiles de escrita por passo +
  rolagem da name table = orçamento MEDIDO).
- Fim: `PSGSilenceChannels()` → 2 s de preto (120 f, framebuffer vivo) →
  volta a TITLE.

## Estado visual entre cenas (persistência declarada)
- Persistem: contagem de ciclo (compassos totais), máscara de cristais.
- Resetam por cena: name table inteira, subpaletas, SAT, scroll, timers de
  rampa. Nada cruza borda de cena implicitamente.
