# 08-bible-artistica — kage_matsuri

> Direção estética VINCULANTE. Adjetivo de direção precisa de piso numérico (§36).

## Doutrina
Festival Goemon no Master System, régua visual Asterix-SMS: cor saturada,
palco denso em vista lateral, silhueta de personagem legível a 16×32.
Pixel art autoral (Imagine → tradução paleta mestra). Pixel nascido de
código como personagem/cenário é bloqueado pelo gate de proveniência.

## Regras de cor
- Somente códigos 6-bit (contrato canal×85). Sem "gradiente suave" — não existe.
- ≤15 cores úteis por subpaleta de sprite (índice 0 = magenta/transparente).
- Palco usa até 16 cores úteis; índice 0 é a cor mais frequente (céu).
- Contraste fg/bg ≥ piso de luma medido (audit_luma_floor.py).
- Gi preto do Kage é cor opaca (índice ≠ 0). Magenta nunca é preto.

## Personagens
- Kage: perfil direito, gi preto, cachecol teal, faixa vermelha, tabi branca.
- Samurai de festival: jingasa amarelo, armadura vermelha, calça azul, bastão.
- Escala locked 16×32. Modo VDP `SPRITEMODE_TALL` (8×16) + metasprite 2×2.

## Palco
Rua de matsuri em vista lateral: céu ciano, lanternas, barracas, torii à
direita, canal/ponte à esquerda, calçamento. Sem texto. Sem personagem
assado no fundo.
