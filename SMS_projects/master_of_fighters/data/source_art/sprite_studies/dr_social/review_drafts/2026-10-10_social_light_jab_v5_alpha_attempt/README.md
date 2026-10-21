# Jab leve v5 — tentativa de fundo transparente

**Status:** descartada no preflight; preservada apenas como evidência de geração.

A ferramenta ignorou o pedido de fundo transparente limpo e devolveu brilho/halo em torno das figuras. Medição do PNG: 1536×1024 RGBA, 219.818 valores RGBA únicos, alpha entre 0 e 254. Não existe máscara binária. Não usar para recorte, conversão, `res/` ou ROM.

SHA-256: `86e775de042f7aff5f60df2ef7b272be14f2eb80950b5c1be2061c90848d0f2b`

Lição: `transparent_background: true` e instruções textuais de alpha binário não garantem fundo transparente nem pixels binários; medir o arquivo retornado antes de qualquer promoção.
