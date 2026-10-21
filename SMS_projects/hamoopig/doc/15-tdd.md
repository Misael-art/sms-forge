# 15-tdd — HAMOOPIG SMS

> Autoridade #7. API = `SMSlib.h` / `PSGlib.h`.

## Restrições
Sem float, sem malloc, sem DMA, ≤8 sprites/scanline, SAT 64, 8 KB RAM.
Números de Mega Drive (320×224, DMA, XGM2, 6 botões) não entram.

## Arquitetura
Fronteiras: `main` (loop/VBlank/probe), `scene`, `input`, `fighter`+`FighterDef`,
`combat` (eventos), `hud`, `gfx`/`title`, `probe`.
Dois `Fighter` estáticos 0-based. FSM numérica do subset HAMOOPIG.
Dispatch de personagem por tabela `fighter_def(id)`, não por `switch` de regras.

## Input
Uma leitura `SMS_getKeysStatus()` por tick. PORT_A = P1, PORT_B = P2.
Pressed/hold/released por comparação em 16 bits. Dummy não herda CPU.
Pause = `SMS_queryPauseRequested` (NMI).

## Pools
| Pool | Máx | Notas |
|------|-----|-------|
| Fighter | 2 | ~40 B cada |
| Contact | 4 | snapshot do tick |
| Input hist | 2×8 | QCF |
| scratch VRAM | 256 B | espelho de tiles no boot |

## VRAM (molde MSSF2T)
| Tiles | Uso |
|-------|-----|
| 1–41 | fonte 1bpp autoral |
| 48–51 | chão + barras |
| 96–127 / 128–159 | P1 — dois bancos de pose 32×64 |
| 160–191 / 192–223 | P2 — dois bancos de pose 32×64 |
| 224–227 / 228–231 | Hadouken direita / espelhado |

`SMS_useFirstHalfTilesforSprites(1)`, `SPRITEMODE_TALL`, metasprite 32×64
(até 16 sprites 8×16/lutador; 8 na scanline quando 4 colunas se sobrepõem).
HUD é tile, nunca sprite. Stream 96 B/VBlank no banco ocioso (L052).
O banco ocioso **prefetch** o próximo quadro; `stream_present` só troca o
display quando o `anim_t` cumpre a duração (idle 12, walk 10). `set_state`
igual não zera o timer — senão o ciclo nunca anda.

## Timing
NTSC 60 Hz: relógio 99 s, 1 tick de segundo = 60 frames. Não copiar
`ROUND_CLOCK_TICKS=38` da origem sem unidade.

## Áudio
PSGlib: `music_battle` na luta; `sfx_hurt` ch3 / `sfx_shot` ch2. Mix do título ainda abaixo do piso 90% (BGM só entra em `fight_enter`).

## Banking
Tiles de animação em `BANK2`/`BANK3`/`BANK4` (slot 2, 0x8000), ROM 128 KB
(`makesms -pm -mbank`). Código em 0x0000–0x7FFF. `SMS_mapROMBank` só em
`stream_prepare` / `rebuild_meta` / `load_now` — o VBlank sobe tiles já
copiados para RAM. Ryo e Musgo usam o mesmo `AnimDef` (n/loop/dur).

## Probe SMRT schema 1
Mesmo mapa MSSF2T (0xC7E0..) para reusar `measure_runtime_probe.py`.
`volatile` obrigatório (L009).
