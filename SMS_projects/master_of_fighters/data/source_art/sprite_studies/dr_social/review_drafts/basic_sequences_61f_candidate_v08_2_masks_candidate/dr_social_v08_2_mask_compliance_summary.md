# Dr. Social - auditoria v08.1 por mascaras

**Status: fail_closed_candidate_needs_mask_review**

Esta saída é uma candidata de revisão, não um asset aprovado nem uma conversão para ROM.

- Fonte v07 SHA-256: `f5c41fb2204e3b2fff9a6e824fc55a767c2456dcdd9c62d17351f76696c95dc8`
- Candidata SHA-256: `48e9786550ae0a076c5659ff893a7dad0c12e38409ec5b816e11bfd36407dbc8`
- Canvas indexado: 640×720, grade 8×9, células 80×80, 61 poses; 11 células vazias preservadas.
- Paleta: 11 cores úteis, transparência no índice 0.
- Geometria alfa: preservada; alterações fora das máscaras: 0.
- Pixels alterados dentro das máscaras: 23373; pixels ambíguos sem classificação: 0.
- Cabelo grisalho: 61/61 frames; tons não cinza dentro da máscara: 0.

## Confinamento semântico

- Branco fora das zonas permitidas: 0.
- Amarelo fora das zonas autorizadas: 0; óculos na máscara dourada: 85; pixels pendentes: 0.
- Bordô fora da gravata/botas: 0.
- Cinza fora de cabelo/bengala: 0.

## Ruído de clusters

Componentes abaixo de 2×2 depois do passe: cabelo 0, casaco 0, pele 4.
Pixels alterados pelo passe de cluster: 10714.
Passe fixo: até 512 iterações por frame; componentes sem vizinho elegível: 0.
Casaco restrito aos índices 5/6, sem tons adicionais no mapa material: 0.

## Bloqueios para conformidade

- A política v08.1 autoriza óculos de latão na zona amarela; pixels preservados nessa máscara: 85.
- A haste da bengala é exceção de 1 px: cor clara contínua, com contorno escuro original preservado.
- Resíduos finais, se houver, bloqueiam a conformidade e aparecem com coordenadas no CSV.
- Nenhuma ROM foi compilada.

Detalhes por frame, coordenadas e proveniência estão no JSON, no CSV de alterações e no CSV de pixels não resolvidos deste pacote.
