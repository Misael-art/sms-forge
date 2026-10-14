# skill: sms-sprite-geometry-modes

> Skill nascida do **L006** (laboratorio_01, 2026-08-25..30): dias perdidos com
> sprite invisível porque a doutrina afirmava que `SPRITEMODE_TALL` era 16×16.
> Lei: SMS_GLOBAL §25. Gate: `audit_sprite_mode.py`.

## A verdade dura (VDP reg 1: bit1 = tamanho, bit0 = zoom)

| Modo (`SMS_setSpriteMode`) | Geometria REAL | Observação |
|---|---|---|
| `SPRITEMODE_NORMAL` | 8×8 | default do hardware |
| `SPRITEMODE_TALL` | **8×16** | "tall" = mais ALTO, nunca mais largo |
| `SPRITEMODE_ZOOMED` | 16×16 na tela | 8×8 com pixel dobrado — **a arte continua 8×8** |
| `SPRITEMODE_TALL_ZOOMED` | 16×32 na tela | arte 8×16 com pixel dobrado |

**Nenhum modo desenha um tile mais largo que 8 pixels.** O tamanho é GLOBAL:
não existe misturar 8×8 com 8×16 na mesma tela.

## A armadilha que custou o L006

Zoom parece resolver "quero 16×16", mas dobra o pixel — o resultado é a mesma
arte de 8×8 em blocos 2×2, com metade da resolução aparente. Quem quer detalhe
16×16 quer **arte** 16×16, e isso o zoom não dá.

## Regra canônica

```
entidade com arte MAIS LARGA que 8px  →  metasprite, sempre
```
`SMS_addMetaSprite(x, y, metasprite)` compõe a entidade a partir de tiles 8×8
(4 tiles para 16×16). Confira a assinatura no header — autoridade #8.

## Sintoma → causa

| Sintoma | Causa provável |
|---|---|
| Sprite não aparece, `SMS_addSprite` retorna ≥0 | arte mais larga que o modo; tile base desalinhado |
| Só o quadrante superior-esquerdo aparece | arte 16×16 desenhada como tile único 8×8 |
| Metade de baixo some | arte 8×16 com modo `NORMAL` |
| Lixo gráfico ao lado do sprite | tiles vizinhos interpretados como parte da entidade |

## Diagnóstico antes de chutar

Ler a VRAM em vez de adivinhar: variável em endereço fixo
(`volatile __at(0xC700) unsigned char rb[4];`, endereço conferido no mapa) + `SMS_readVRAM`, e inspecionar pelo
depurador do Emulicious (DAP `evaluate`, contexto **repl**). Foi assim que o
L006 fechou — comparando o que estava na VRAM com o que a arte deveria ter posto lá.

## Custo antes de escolher

Metasprite 16×16 = **4 tiles** de VRAM e 4 entradas na SAT por entidade.
A SAT tem 64 entradas e a scanline aceita 8 sprites: 16 entidades 16×16 já
esgotam a SAT; duas entidades lado a lado usam 8 entradas totais, mas apenas
4 objetos por scanline comum (2 colunas por ator), em modo 8×8 sem zoom.
Tile 16×16 artístico não é `sprite_size:16x16` no manifesto: declare modo
físico 8×8/8×16, objetos emitidos em ordem de SAT e entradas hidden. Y do
manifesto é o passado à SMSlib; armazenado `(y-1)&255`. O perfil atual não
qualifica wrap/posicionamento negativo nem diferenças do zoom SMS1.
Rodar `audit_sprite_line_sim.py` ANTES de fechar o design.

Ver também: [`sms-sprites-metasprite.md`](sms-sprites-metasprite.md).
