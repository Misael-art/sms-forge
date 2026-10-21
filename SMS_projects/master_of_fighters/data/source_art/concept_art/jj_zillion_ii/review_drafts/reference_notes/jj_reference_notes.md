# Referência de J.J. — pesquisa visual inicial v1 (Zillion II / SMS)

> Registro histórico da primeira direção, criada antes da correção do dono sobre o figurino. Para a direção ativa, consulte `jj_reference_notes_v2.md`, que acrescenta o model sheet do anime somente como referência de roupa.

## Escopo

Fonte visual exclusiva: versão Sega Master System de *Zillion II: The Tri Formation*, não o anime nem uma ilustração promocional do anime. A imagem serve para cor e leitura geral do sprite. Nenhum pixel extraído será usado no model sheet.

## Fontes verificadas

1. [SMS Power — arquivo de sprites de Zillion II](https://www.smspower.org/Sprites/ZillionII-SMS), que lista `J.J - Standing`, `J.J - Running`, `J.J - Jumping`, `J.J - Crouching`, `J.J - Hit` e sprites do Tri-Formation sob o cabeçalho de *Zillion II: The Tri Formation*.
2. [Arquivo direto do sprite `J.J - Standing`](https://www.smspower.org/uploads/Sprites/ZillionII-SMS-J.J-Standing.png), baixado apenas para inspeção temporária. SHA-256: `102b797311b5790272bf2ef63bb5a568b972fe1d74961d46e85163be2e4495b6`.
3. [SMS Power — embalagem japonesa de Tri Formation](https://www.smspower.org/Scans/ZillionII-SMS-JP-TriFormation), cuja descrição informa que o buggy de J.J. pode mudar para Armorater. Essa fonte sustenta somente a proposta de mecânica em `doc/jj/jj_moveset_concept_v1.json`.

## Sprite e conversão de cor

- Dimensão do sprite de pé: 13×40 px.
- PNG arquivado: 8 entradas de paleta incluindo índice transparente 0; 7 cores RGB opacas.
- RGB observados: preto `#000000` (contorno), azul `#0000AC`, azul-lavanda `#ACAAFF`, magenta `#FF0052`, laranja `#FF5500`, rosa-claro `#FFAAAC`, branco `#FFFFFF` e alpha transparente.
- Mapeamento para a grade SMS canal×85: `#0000AC` → `#0000AA`; `#ACAAFF` → `#AAAAFF`; `#FF0052` → `#FF0055`; `#FFAAAC` → `#FFAAAA`; laranja e branco permanecem. Preto opaco será substituído por navy `#000055`, pois RGB preto também é o índice 0 transparente.
- Sombras adicionais são variações legais da mesma família de matiz, para completar o shading em três tons. Paleta resultante: 13 cores úteis, validada pelo gerador.

## Limite de interpretação

O sprite é pequeno demais para resolver cabelo versus acessório no topo da cabeça ou separar todos os painéis da roupa. A concept art usa cabelo curto azul-violeta e uniforme magenta como leitura de trabalho, sem declarar isso como lore literal. Idade exata e detalhes não visíveis ficam em aberto para o dono.

**Uso:** design e papéis cromáticos. **Pixels copiados:** não. **Anime consultado:** não.
