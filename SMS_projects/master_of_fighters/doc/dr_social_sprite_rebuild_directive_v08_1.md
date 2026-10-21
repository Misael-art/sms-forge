# Dr. Social — diretriz de reconstrução da sprite sheet v08.1

**Estado:** candidata de revisão; ainda reprovada pelo gate de clusters.
**Base:** geometria v07 congelada, 61 poses, grade 8×9 de células 80×80.
**Referência de identidade:** model sheet aprovado CPS2-Alpha-Cel v4.
**Contrato:** `doc/dr_social_sprite_mask_contract_v08_1.json`.

## Delta autorizado pelo dono

- Índice amarelo 12 (`#FFFF00`) é permitido nos óculos de latão/monóculo, além do pomo/empunhadura da bengala e dos detalhes amarelos já ancorados. Preservar os **85 pixels** identificados na máscara facial.
- Conformar sombras dentro das máscaras explícitas de cabelo, casaco e pele a clusters de no mínimo 2×2. Quando um cluster menor tiver uma cor vizinha predominante, reassociá-lo a um tom já existente da rampa do mesmo material, usando uma fotografia fixa dos pixels para impedir alternância durante o passe.
- A haste da bengala é exceção geométrica: linha branca contínua de 1 px, com o contorno escuro original mantido. Não aplicar a regra 2×2 à haste.
- Classificar os pixels sem material, branco fora de zona e cinza residual; não apagar nem tornar transparente qualquer pixel.

## Invariantes

- Preservar o PNG indexado, a paleta fechada, os 61 IDs/ordem, canvas 640×720, alpha binário, silhueta e fronteiras das células.
- Alterar cor somente dentro de máscara explícita de material/região e somente para um índice permitido naquela máscara.
- Proibidos ImageGen/difusão, blur, antialias, média de cor, distância RGB, filtros de luminância, quantização automática ou edição fora das máscaras.
- Não compilar ROM nem copiar para `res/` antes da aprovação visual do dono.

## Execução observada

A ferramenta `tools/build_dr_social_61f_v08_1_masks.py` gerou a candidata em
`data/source_art/sprite_studies/dr_social/review_drafts/basic_sequences_61f_candidate_v08_1_masks_candidate/`.
Ela preservou alpha, grade, paleta e poseamento; não fez nenhuma mudança fora
das máscaras. O relatório registra 85/85 pixels na máscara dos óculos, zero
vazamentos branco/amarelo/bordô/cinza, zero pixels sem classificação final e
1.245 pixels de haste branca sem pixels não brancos.

A máscara do cabelo foi ampliada conservadoramente para recuperar componentes
avermelhados da franja quando tocam a âncora grisalha e estão na região superior
do cabelo. A inspeção 12× do idle confirmou a troca da mancha vermelha da franja
por cinza; o relatório mede 1.014 pixels avermelhados recuperados e zero cores
não cinzas dentro da máscara de cabelo em 61/61 poses.

## Resultado do gate de clusters

**Falha, não promover.** Depois do passe ainda restam 73 componentes 1×1 de
cabelo, 96 de casaco e 341 de pele. Pela regra 2×2, os componentes abaixo do
limite são 102/139/553, respectivamente. O restante está separado de qualquer
tom alternativo dentro da máscara autorizada; fundi-los exigiria reclassificar
material ou alterar contorno/geometria, ações que não foram autorizadas neste
delta. O passe não pode declarar conformidade até que esses fragmentos sejam
resolvidos ou o dono ajuste o escopo de correção.

As amostras 1×/4× são apenas para avaliação visual; o status numérico de cluster
é bloqueador mesmo que a composição pareça aceitável. A candidata continua fora
de `res/` e de ROM.
