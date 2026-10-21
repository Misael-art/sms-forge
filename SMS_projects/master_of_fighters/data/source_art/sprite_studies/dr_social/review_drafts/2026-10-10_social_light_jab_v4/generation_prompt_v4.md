# Dr. Social — Jab leve — rascunho v4

**Status:** candidato visual para revisão do movimento; não aprovado para conversão.

## Referências

1. `social_light_jab_candidate_v3.png` — composição e progressão dos seis quadros.
2. `data/source_art/concept_art/dr_social/dr_social_model_sheet_cps2_alpha_cel_v2.png` — identidade aprovada e óculos redondos.
3. `data/source_art/sprite_studies/dr_social/dr_social_basic_sequences_61f_owner_source_v1.png` — morfologia, roupa e equipamento.
4. `out/diagnostics/dr_social_61_pose_review_v10/dr_social_61_pose_converted_preview_4x.png` — tratamento de clusters e sombras.

## Instrução aplicada

Preservar a composição 3×2 e os seis quadros J01–J06 do jab leve; manter proporção adulta esguia, casaca azul, cabelo cinza, óculos redondos de aro dourado, bengala de apoio e paleta. Tornar os óculos legíveis no perfil, sem alterar outras partes. Fundo solicitado: RGB preto uniforme. Estilo pedido: clusters quadrados, contornos azul-marinho, cel shading de blocos, sem desfoque, gradiente, dithering, brilho, ruído, pixels soltos ou texto.

## Resultado da checagem do arquivo gerado

- PNG RGB, 1536×1024.
- Layout visual: 3 colunas × 2 linhas, seis quadros de 512×512.
- 83.402 cores RGB únicas; 706.581 pixels exatamente pretos; 1.076.331 pixels com canais ≤32.
- Sem canal alpha; o fundo é quase preto, mas não é uma cor uniforme para recorte.
- Não há conversão para canvas lógico 80×80, quantização à paleta SMS ou inspeção por quadro em tamanho nativo.

O fundo em preto permite uma leitura visual preliminar da sequência, mas os dados medidos bloqueiam o uso como fonte convertível. O candidato permanece em `review_drafts`; não copiar para `res/`, não quantizar e não produzir ROM a partir dele antes da revisão visual do dono e dos gates de arte.

## Tentativa subsequente

Uma edição solicitando fundo transparente e alpha binário foi rejeitada como fonte candidata: retornou 219.818 cores RGBA, alpha 0–254 e halo luminoso. Foi mantida apenas como evidência da falha de obediência do gerador; não substitui v4.
