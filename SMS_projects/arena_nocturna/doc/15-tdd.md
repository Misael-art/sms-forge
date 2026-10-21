# 15-tdd — arena_nocturna

> Arquitetura técnica. Autoridade #7.
> A API definitiva é o header (`sdk/devkitSMS/SMSlib/SMSlib.h`, autoridade #8) —
> este documento NUNCA inventa assinatura. Em dúvida: leia o header.

## Restrições assumidas (herdadas, sempre ativas)
```
❌ float/double em runtime quente  — SDCC Z80 faz float em software; use int16/Q8.8
❌ malloc / free                   — buffers estáticos; RAM = 8 KB
❌ VRAM em massa fora do VBlank    — sem DMA
❌ >8 sprites/scanline, >64 na SAT
```

## Armadilhas Z80/SDCC vigiadas neste projeto
- `int` é 16-bit signed; `char` é unsigned por padrão (SDCC z80).
- Multiplicação/divisão são caras (sem HW mul) → tabelas lookup / Q8.8.
- ISR curta: trabalho pesado fica no loop principal. Pause = NMI.

## Módulos (`src/*.c`)
| Arquivo | Responsabilidade | Não pode |
|---|---|---|
| `main.c` | init de VDP/VRAM, leitura de teclas, FSM, **ordem do frame** | conter regra de entidade |
| `player.c` | movimento, disparo, invulnerabilidade | ler teclas por conta própria |
| `boss.c` | FSM do guardião, fases, telegrafo | escrever em VRAM |
| `entities.c` | pools de contra-ataque e FX, colisão com o hero | alocar |
| `hud.c` | HUD por marcação suja | desenhar fora de `y<=3` |
| `audio.c` | PSGlib + driver de SFX | escrever no PSG antes de `PSGFrame()` |
| `game.h` | contrato único: tipos, tetos, tiles | conter código |

**Invariantes de módulo** (verificáveis por leitura, não por prosa):
- Teclas só em `main.c`; VRAM só na janela pós-`SMS_waitForVBlank`.
- Todo teto é `#define` em `game.h`; nada de número mágico em pool.

## Mapa de memória (RAM)
| Símbolo | Bytes | Conteúdo |
|---|---|---|
| `g_player` | 17 | pos, HP, invuln, facing, cooldown, tiro + `shot_prev_x` |
| `g_boss` | 14 | pos, `vy`, HP, estado, timer, fase, flash |
| `g_counter[3]` | 24 | pool de contra-ataque com velocidade por eixo |
| `g_fx[2]` | 12 | pool de FX de impacto |
| globais de partida | ~8 | `g_state`, `g_frame`, `g_score`, `g_hitstop`, `g_wave` |
| `probe_*` (0xC7F0..) | 8 | marcadores `volatile __at` lidos por instrumentos |

## Entidades e pools (estáticos)
| Pool | Máx | Motivo do teto |
|---|---|---|
| boss | 1 | ocupa 4 colunas de sprite por scanline |
| jogador | 1 | 2 colunas |
| tiro do jogador | 1 | 1 coluna |
| contra-ataque | 3 | 4 (boss) + 2 (hero) + 1 (tiro) + 3 = 10 > 8 **só** se colidirem na mesma scanline; o leque nasce separado em 16px |
| FX de impacto | 2 | efêmeros, ≤12 frames |

Pool cheio **descarta** o spawn; nunca recicla o mais antigo. Reciclar faz o
projétil sumir na cara do jogador — dano injusto e invisível.

## Máquina de estados
`ST_TITLE → ST_PLAY → ST_OVER → ST_PLAY`, com `ST_PAUSE` como desvio de
`ST_PLAY`. Todas as transições consomem a **borda de subida** do botão 1;
o nível seguraria a transição 60 vezes por segundo.

`g_hitstop` é subestado de `ST_PLAY`: congela a **simulação**, nunca o frame.
`g_frame` e o VBlank continuam, senão o instrumento de fps mediria uma queda
que o hardware não teve.

### FSM do guardião
`IDLE → TELEGRAPH → FIRE → RECOIL → IDLE`. O telegrafo é estado próprio com
pose própria — antes a pose de carga era escolhida por "existe contra-ataque
na tela", que é consequência, não aviso. A fase (0/1/2, ligada a 2/3 e 1/3 do
núcleo) muda cadência e abre o leque de 1 para 3 projéteis.

### Dificuldade progressiva
`g_wave` sobe a cada 600 frames (~10 s), teto 9. É eixo congelado no GDD e
até esta revisão não existia no código.

## Banking
- Alvo inicial: **48 KB linear sem mapper** (B01); a ROM atual é 32 KB e usa
  header linear de 32 KB porque as poses vivem na ROM.
- Se exceder: mapper Sega (páginas 16 KB, regs 0xFFFE/0xFFFF), código restrito
  a 32 KB, dados bancados a partir do bank 2.
- Status atual: linear, ROM alvo ≤48 KB.

## Áudio
- Driver: PSGlib (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Arbitração de canais SFX vs música (só 4 canais), explícita: a música é da
  PSGlib e ocupa os 4 canais; o driver de SFX de `audio.c` roda **depois** de
  `PSGFrame()` e toma os canais 2 (tom) e 3 (ruído) pela duração do envelope.
  Nada precisa ser restaurado — o `PSGFrame()` seguinte reescreve os canais.
- **Defeito corrigido**: escrever na porta 0x7F durante o update não produz
  som. O `PSGFrame()` do mesmo frame reescreve os quatro canais logo depois,
  e o valor morre antes de soar. Ordem é o contrato.
- SFX PSGlib real implementado via `PSGSFXPlay()`; os streams autorais ficam
  em `res/audio/*.psg`, com headers gerados em `inc/` e hashes em
  `doc/audio_provenance_manifest.json`. A captura isolada do emulador passou
  `audit_audio.py` com `peak=7340` e 90% de atividade.
- YM2413/FM é **opcional**: o jogo tem que funcionar sem ele.

## Orçamento de frame
O carregamento de 128 tiles, os frames/FX dos sprites e o mapa ocorre com display
off. A implementação `SMS_loadTileMapArea` recebe entradas de tile de 16 bits
little-endian, portanto `arena_bg_map` ocupa 1.536 bytes para 768 células,
embora a name table física tenha 32×24 células. No loop, HUD e SAT são
atualizados imediatamente após `SMS_waitForVBlank`; não há DMA nem carga de
tiles durante a ação.

A HUD é **por marcação suja**: só o contador de frames (instrumento de
medição) é reescrito todo frame; o resto espera `hud_mark()`. A versão
anterior reescrevia ~60 caracteres na name table todo frame com o display
ligado — escrita de VRAM fora da janela segura, custo puro e tearing.

### Orçamento de VRAM de tiles (esgotado)
| faixa | tiles | ocupante |
|---|---|---|
| 0–63 | 64 | fonte do text renderer |
| 64–191 | 128 | `arena_bg` |
| 192–239 | 48 | sprites |
| 240–255 | 16 | **livre** |

Sobram 16 tiles no mapa reservado. Toda pose nova entra por **streaming** na
faixa ativa: `SMS_loadTiles()` depois do `SMS_waitForVBlank`, custo em ROM e
não em uma segunda cópia de VRAM. O hero alterna quatro poses de caminhada e
uma pose esquerda no slot 192; o boss alterna normal/telegraph/hurt/dead nos
slots 208–223; impacto usa 204. Isso obriga cada pose a ter a mesma contagem de
tiles da pose base; o pior custo de VBlank ainda é provisório.
