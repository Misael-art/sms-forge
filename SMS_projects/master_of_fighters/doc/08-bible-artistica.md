# 08-bible-artistica — master_of_fighters

> Direção estética VINCULANTE. Adjetivo de direção precisa de piso numérico (§36).

## Doutrina
Dark Deco adaptado ao SMS: contraste alto, luz como recurso escasso, silhueta
legível a 256×192. Pixel art autoral obrigatória; pixel nascido de código como
personagem/cenário é bloqueado pelo gate de proveniência.

## Regras de cor
- Somente códigos 6-bit (contrato canal×85). Sem "gradiente suave" — não existe.
- Arquivos indexados de personagem usam índice 0 transparente e até 15 cores
  úteis para a conversão; isso é paleta de autoria, não uma CRAM por lutador.
- Em runtime, P1 é a tabela compartilhada por todos os sprites (índice 0
  transparente, entradas 1–15 comuns ao elenco ativo). P0 atende cenário/HUD;
  P0 índice 0 é uma cor visível de backdrop, não transparência. Pixels BG no
  índice 0 sempre mostram a cor da tabela escolhida, inclusive quando usam P1.
- Tiles de fundo podem selecionar P1 para reutilizar cores já carregadas; isso
  não cria paleta nem muda as cores dos sprites. Mapa global ainda pendente em
  `doc/palette_runtime_contract_v1.json`.
- Contraste fg/bg ≥ piso de luma medido (audit_luma_floor.py).

## Model sheets antes de assets finais
(personagem, inimigo, cenário: folha de modelo com viradas e paleta atribuída)
