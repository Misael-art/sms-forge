# Dr. Social - auditoria v08.1 por mascaras

**Status: fail_closed_candidate_needs_mask_review**

Esta saída é uma candidata de revisão, não um asset aprovado nem uma conversão para ROM.

- Fonte v07 SHA-256: `f5c41fb2204e3b2fff9a6e824fc55a767c2456dcdd9c62d17351f76696c95dc8`
- Candidata SHA-256: `c533542455566ab237c41b6395dd1fccf6bf95d7d3abfe44ce95ad10ddfc096a`
- Canvas indexado: 640×720, grade 8×9, células 80×80, 61 poses; 11 células vazias preservadas.
- Paleta: 12 cores úteis, transparência no índice 0.
- Geometria alfa: preservada; alterações fora das máscaras: 0.
- Pixels alterados dentro das máscaras: 7983; pixels ambíguos sem classificação: 0.
- Cabelo grisalho: 61/61 frames; tons não cinza dentro da máscara: 0.

## Confinamento semântico

- Branco fora das zonas permitidas: 0.
- Amarelo fora das zonas autorizadas: 0; óculos na máscara dourada: 85; pixels pendentes: 0.
- Bordô fora da gravata/botas: 0.
- Cinza fora de cabelo/bengala: 0.

## Ruído de clusters

Componentes abaixo de 2×2 depois do passe: cabelo 102, casaco 139, pele 553.
Pixels alterados pelo passe de cluster: 804.

## Bloqueios para conformidade

- A política v08.1 autoriza óculos de latão na zona amarela; pixels preservados nessa máscara: 85.
- A haste da bengala é exceção de 1 px: cor clara contínua, com contorno escuro original preservado.
- Resíduos finais, se houver, bloqueiam a conformidade e aparecem com coordenadas no CSV.
- Nenhuma ROM foi compilada.

Detalhes por frame, coordenadas e proveniência estão no JSON, no CSV de alterações e no CSV de pixels não resolvidos deste pacote.
