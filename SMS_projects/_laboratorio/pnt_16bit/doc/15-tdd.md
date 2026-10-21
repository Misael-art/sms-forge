# 15-tdd — pnt_16bit

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

## Mapa de memória (RAM)
| Faixa | Tamanho | Conteúdo |
|-------|---------|----------|
| — | — | — |

## Entidades e pools (estáticos)
| Pool | Máx | Bytes/entidade | Total |
|------|-----|----------------|-------|
| — | — | — | — |

## Máquina de estados
_(estados do jogo e transições permitidas)_

## Banking
- Alvo inicial: **48 KB linear sem mapper** (B01).
- Se exceder: mapper Sega (páginas 16 KB, regs 0xFFFE/0xFFFF), código restrito
  a 32 KB, dados bancados a partir do bank 2.
- Status atual: _(linear / bancado)_

## Áudio
- Driver: PSGlib (`sdk/devkitSMS/PSGlib/PSGlib.h` é a autoridade).
- Arbitração de canais SFX vs música (só 4 canais) — declarar explicitamente:
  _(qual canal cede para qual, e quando)_
- YM2413/FM é **opcional**: o jogo tem que funcionar sem ele.

## Orçamento de frame
_(quem escreve na VRAM, quanto, e dentro de qual janela. Cruzar com 13-spec-cenas.)_
