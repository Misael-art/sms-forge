# 15-tdd — pulso_de_cristal

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
- Multiplicação/divisão são caras → tabelas lookup / Q8.8 (HUD: contador de
  compasso usa incremento, não divisão).
- ISR curta: trabalho pesado no loop principal. Pause = NMI.
- Escrita de name table cena a cena: **sem DMA**; VBlank só, com contagem
  instrumentada (cruzar com 13-spec-cenas).

## Mapa de memória (RAM)
| Faixa | Tamanho | Conteúdo |
|-------|---------|----------|
| ws_core (definida pelo crt0) | até ~2 KB | stack, variáveis SMSlib |
| estado da FSM + timer de transição | ~32 B | `uint8_t state, sub, fade_att[4]` |
| foco de cristal + contadores HUD | ~64 B | compassos/frames tocados (uint16) |
| buffers de entrada (PAUSE/START/SELECT) | ~16 B | máscaras debounce |
| resto | — | reservado; **nenhum buffer de áudio em RAM** (streams vivem em ROM) |

Total estático declarado: < 2 KB fora do core SMSlib. (RAM = 8 KB — autoridade #8/contrato.)

## Entidades e pools (estáticos)
| Pool | Máx | Bytes/entidade | Total |
|------|-----|----------------|-------|
| cristais (cena) | 8 | 8 (x,y,fase,estado) | 64 B |
| sprites SAT de estilhaço (storm) | 24 | 4 | 96 B |
| SFX ativos | 1 | — | PSGlib serializa SFX; só 1 por vez por design |

## Máquina de estados
```
BOOT → TITLE ─Start→ FADE_OUT(dawn) → DAWN ─Start→ CUT(storm) → STORM
TITLE ←(fim eco) CREDITS ←Start ECHO ←Start
Pause em qualquer ato: SILENT — reprise do mesmo stream
```
- `FADE_OUT`: rampa de atenuação via
  `PSGSetMusicVolumeChannelsAttenuation(a0,a1,a2,a3)` (define do header,
  PSGlib.h:51) até 15/15/15/15 → `PSGStop()`.
- `CUT`: mudança abrupta (tempestade não pede licença) — `PSGPlay` no frame
  seguinte.
- `SILENT`: `PSGSilenceChannels()` (PSGlib.h:63); retomada com
  `PSGRestoreVolumes()` (PSGlib.h:64). Reprendida, não re-iniciada.
- Transições START→ato seguem `sms-state-transitions.md` (entradas/saídas/owners
  por estado persistem aqui; estados que coexistem: só HUD + stream).

## Áudio
- Driver: **PSGlib** (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Pump por frame no loop principal, após `SMS_waitForVBlank()`:
  `PSGFrame()` (retorna 0 quando o stream terminou — tratado por estado) +
  `PSGSFXFrame()`.
- Reprodução: `PSGPlay(stream)` para as 4 faixas — verificado na fonte
  (`devkitSMS-upstream/PSGlib/src/PSGPlay` define `PSGLoopFlag=1`: loop
  infinito no marcador `0x01`). Créditos/final usam `PSGPlayNoRepeat` (para no
  loop) com `PSGGetStatus()==PSG_STOPPED` como gatilho da transição ao título.
- **Arbitração SFX × música (4 canais, declarada)**:
  - ch0 lead, ch1 arpejo/contraponto, ch2 baixo, ch3 percussão (ruído branco).
  - SFX **nunca** tocam no ch3 (matariam a percussão — risco registrado no
    plano). Declaração literal por SFX no manifesto de proveniência, exigida
    por `audit_psg_channel_binding.py`:
    - `sfx_crystal` → `SFX_CHANNEL1` (0x08 — arpejo cede; é a camada mais
      redundante em uníssono)
    - `sfx_crack`   → `SFX_CHANNEL1` (0x08, idem)
    - `sfx_chime`   → `SFX_CHANNEL2` (0x04 — só na cena 01, onde o ch2 ainda
      não entrou com o baixo)
  - Política de recuperação: após `PSGSFXGetStatus()` voltar a 0, nenhum
    resgate é necessário — PSGlib retoma a música no canal excluído.
- Volume mestre musical por cena via `PSGSetMusicVolumeChannelsAttenuation`
  (piano-forte da cena 01 é rampa de atenuação, não camada nova).
- YM2413/FM: **opcional e fora de escopo** (GDD). O jogo funciona sem ele.

## Pipeline de assets de áudio (composição autoral)
```
tools/partitura/<faixa>.json  →  tools/gen_pulso_music.py --self-check / --in ... --out res/audio/<faixa>.psg
                                      ↓ (emissor determinístico, valida M1–M7 por construção)
                       audit_psg_quality.py mede o BINÁRIO independentemente (L079)
                                      ↓
                       doc/audio_provenance_manifest.json (sha256+bytes, origin "autoral_composicao")
                                      ↓
                       inc/psg_blobs.h ou .psg linkado — precedente luta_mugen_gen_psg_blobs.py
```
- Serialização: `WAIT|n-1` (0x38), hold 0x39+, latch só do que mudou (economia
  L080), `0x01` loop, `0x00` end; periods `0x10–0x3FF` (grave real, piso
  ~219 Hz — precedente `make_psg_assets.py`).
- **Ajuste musical pós-escuta entra só no JSON da partitura**; o emissor não é
  tocado para "consertar som".

## Orçamento de frame
- VBlank callback: writes de name table limitados a N tiles/frame — **N é
  medido, não estimado** (13-spec-cenas, método: contagem instrumentada +
  `measure_worst_frame.py`).
- Custo de `PSGFrame`+`PSGSFXFrame` com música+SFX simultâneos: medido em M1
  (risco registrado no plano: não deixar para M3).
- Cenas: ver `doc/13-spec-cenas.md` (autoridade #3) — cada número ali exige
  método de medição citado.

## Banking
- Alvo inicial: **48 KB linear sem mapper** (B01). Streams ~1,5–4 kB cada +
  código + tiles: folga esperada > 50%; se estourar: mapper Sega (páginas
  16 KB, regs 0xFFFE/0xFFFF) com decisão registrada + aprovação humana.
- Status atual: linear (não medido ainda — primeiro build).
