# 08-bible-artistica — arena_nocturna

> Direção estética VINCULANTE. Adjetivo de direção precisa de piso numérico (§36).

## Doutrina
Dark Deco adaptado ao SMS: contraste alto, luz como recurso escasso, silhueta
legível a 256×192. Pixel art autoral obrigatória; pixel nascido de código como
personagem/cenário é bloqueado pelo gate de proveniência.

## Regras de cor
- Somente códigos 6-bit (contrato canal×85). Sem "gradiente suave" — não existe.
- ≤15 cores úteis por subpaleta (índice 0 = transparente).
- Contraste fg/bg ≥ piso de luma medido (audit_luma_floor.py).

## Model sheets antes de assets finais
(personagem, inimigo, cenário: folha de modelo com viradas e paleta atribuída)
# 08-bible-artistica — arena_nocturna

## Direção

Dark Deco orbital: navy quase preto, cobalt, brass, cyan e magenta como luz
escassa. Silhuetas compactas, contornos firmes e clusters legíveis em 1×.

## Regra nativa

As fontes em `rascunho/` são visuais de origem. Os PNGs em `res/` são
derivados indexados no grid SMS, com paleta 6-bit, índice 0 transparente e
tiles deduplicados. A fidelidade visual precisa ser conferida no Emulicious;
conformidade técnica não substitui leitura humana.
