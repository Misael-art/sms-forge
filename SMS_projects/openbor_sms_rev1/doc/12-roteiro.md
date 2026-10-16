# 12-roteiro — openbor_sms_rev1

> Roteiro e diálogos. Autoridade #6.
> Primeiro degrau da ordem de trabalho de cena: **roteiro vem antes do
> storyboard, que vem antes da arte cara.**

## Premissa
O produto é um recorte técnico-jogável do módulo externo Golden Axe Legend
(fase TOWN1). O roteiro/story do módulo é **fonte externa, não publicável**:
este projeto não reescreve narrativa — ele importa, adapta e mede o que a fonte
declara, preservando origem de cada texto e evento.

## Cena 01 — TOWN1 (recorte)
### Beats (do mais barato ao mais caro; nenhum número inventado)
1. Entrada da fase com **card de texto** do módulo (no doador: evento TEXT na
   linha 49 do `DATA\LEVELS\TOWN1.txt`, owner ainda não implementado,
   fail-closed). Se o owner de TEXT não existir quando o recorte chegar nele, o
   lote para ali — não pula.
2. Movimento do jogador pela primeira tela do cenário (mundo + profundidade),
   com scroll conforme a fonte.
3. Primeiro obstáculo/cenário com colisão (no doador: evidência isolada de
   obstáculos civ02/civ03 — sem dano/morte).
4. Primeiro confronto com inimigo (no doador: evidência de bizzar1 **apenas
   visual**, sem pickup/equip; semântica de combate ainda a portar).

### Diálogos
> Custo real: cada caractere vira tile na VRAM. Texto longo é orçamento gasto.

Nenhum diálogo é reescrito neste recorte. O texto do card de TOWN1 pertence à
fonte externa; sua transcrição/owner entra em O5 (TEXT), com hash da linha de
origem, e **não** é pré-requisito de O1–O3 (o recorte pode começar depois do
card, ou bloquear nele — decisão do lote O4, com contrato).

### Intenção emocional
Pendente (O2+): virá da leitura do cenário/paleta da fonte — sem inventar
direção de arte antes da medição. Mudança visual que altere identidade exige
decisão e revisão próprias.
