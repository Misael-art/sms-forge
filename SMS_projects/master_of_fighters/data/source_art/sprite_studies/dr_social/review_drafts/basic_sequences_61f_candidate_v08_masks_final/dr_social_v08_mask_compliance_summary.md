# Dr. Social — auditoria v08 por máscaras

**Status: fail_closed_candidate_needs_mask_review**

Esta saída é uma candidata de revisão, não um asset aprovado nem uma conversão para ROM.

- Fonte v07 SHA-256: `f5c41fb2204e3b2fff9a6e824fc55a767c2456dcdd9c62d17351f76696c95dc8`
- Candidata SHA-256: `f3788d6aac41fd3d85753a764e809b2d8bc859b6286d55daa21d3cfbf37ef670`
- Canvas indexado: 640×720, grade 8×9, células 80×80, 61 poses; 11 células vazias preservadas.
- Paleta: 12 cores úteis, transparência no índice 0.
- Geometria alfa: preservada; alterações fora das máscaras: 0.
- Pixels alterados dentro das máscaras: 6611; pixels ambíguos sem classificação: 36.

## Confinamento semântico

- Branco fora das zonas permitidas: 1.
- Amarelo fora da bengala: 85; preservado para decidir a política dos óculos: 85; fora da bengala e dos óculos pendentes: 0.
- Bordô fora da gravata/botas: 0.
- Cinza fora de cabelo/bengala: 7.

## Ruído de clusters

Componentes 1×1 ainda encontrados: cabelo 88, casaco 98, pele 311.

## Bloqueios para conformidade

- A ficha conceitual aprovada mostra óculos de latão, mas a regra v08 não inclui os óculos entre as zonas amarelas. Os 85 pixels amarelos ancorados na face foram preservados sem repintura; a decisão semântica continua pendente.
- Os pixels 1×1 listados acima e os pixels ambíguos precisam de revisão das máscaras antes de qualquer promoção.
- Nenhuma ROM foi compilada.

Detalhes por frame, coordenadas e proveniência estão no JSON, no CSV de alterações e no CSV de pixels não resolvidos deste pacote.
