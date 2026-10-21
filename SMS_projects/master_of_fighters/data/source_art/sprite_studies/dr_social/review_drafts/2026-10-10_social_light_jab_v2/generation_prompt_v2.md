# Social light jab — geração v2

## Referências e papéis

- `dr_social_basic_sequences_61f_owner_source_v1.png`: identidade, silhueta,
  traje, equipamento e morfologia aprovados.
- `dr_social_61_pose_converted_preview_4x.png`: agrupamento de cor/sombra limpa
  da v10, somente como referência de acabamento.
- A candidata v1 foi substituída como referência visual; sua composição
  ilustrada estava puxando o acabamento para fora do pixel art.

## Prompt enviado

> Author a fresh Dr. Social six-frame LIGHT JAB pixel sprite sheet. The only
> references are already-approved pixel sprite frames: use them for identity,
> exact costume, morphology, palette, outlines and color grouping. Do not turn
> the art into an anime illustration or add cinematic lighting. Output exactly
> 6 full-body sprites in a clean 3 columns × 2 rows grid, equal cells, no text,
> no labels, no separators. Each cell represents an 80×80 Master System logical
> sprite and is enlarged with strict nearest-neighbor square pixels for viewing.
> Create clear deliberate 8-bit/16-bit pixel clusters, hard stepped dark-navy
> outline, flat contiguous cel-shaded blocks, no more than 3 tones per material,
> no dithering or anti-aliasing. Adult human, slim long-limbed morphology
> matching source; gray swept hair; small round brass spectacles visibly framing
> both eyes; teal-blue long coat, deep-blue vest, burgundy cravat, white gloves,
> brown shoes; same source palette and color roles. One straight silver cane with
> rounded gold knob, full tip visible, constantly held in the same support hand,
> near-vertical in every frame. The other closed gloved fist performs the jab
> with visible continuous shoulder/upper-arm/elbow/forearm/wrist chain. Pose
> sequence, left to right top row then bottom row: J01 balanced guard, J02 short
> shoulder/elbow anticipation, J03 halfway extension, J04 full extension and
> sole contact pose, J05 recoil, J06 exact return to J01 guard. Preserve the same
> body scale and ground baseline; J01 and J06 intentionally match while J02–J05
> clearly differ. Every non-character pixel must have alpha 0, every character
> pixel alpha 255 only. Do not draw background, floor, cast shadow, atmosphere,
> glow, halo, colored fringe, gradient, vignette, backdrop, texture, fog, blur,
> shine, lens effect, or any semi-transparent edge. No crop: full hair, both
> shoes, both hands, entire cane and rounded pommel fit inside every cell. Keep
> all pixels crisp and square; output is sprite pixel art, not a poster or
> concept painting.

## Resultado medido

O arquivo é uma candidata visual de movimento, não pixel art técnica. A geração
retornou 1536×1024 RGBA, 184.429 cores RGBA distintas e alpha de 0 a 254, sem
nenhum pixel alpha 255; 601.980 pixels têm alpha parcial. O fundo contém halo
azul escuro semitransparente. A imagem ainda não foi reduzida para seis canvases
80×80 nem indexada à paleta SMS. A falha de alpha/paleta bloqueia conversão e
promoção.
