# skill: sms-sprite-animation

Use quando houver idle, walk, golpe, hit, KO ou qualquer ciclo de frames.
Metasprite e SAT: `sms-sprites-metasprite.md`. Esta skill é **semântica**.

## 12 princípios (ênfase SMS)

staging, anticipation, timing/spacing, arcs, follow-through, exaggeration,
solid drawing, appeal — mais pose-to-pose consciente do budget de tiles e
do teto de 8 sprites/scanline.

## Moveset mínimo (quando o GDD for fighting / action)

idle, walk/advance, retreat, crouch, jump, landing, guard, hit, knockdown,
get-up, light, medium, heavy, special, throw, victory, defeat — mais ações
específicas do GDD. Não invente frame fora do GDD.

## Reprovação permanente

- frames apenas reordenados
- ações semanticamente iguais com nomes diferentes
- fragmentos da célula vizinha
- fundo incorporado / contato transparente
- pivot inconsistente
- preview diferente do strip
- vista frontal usada como corrida lateral
- silhueta preenchida chamada de lineart
- derivação mecânica chamada de autoria nativa
- smear que parece sujeira ou ilha

## Medição

Cada estado precisa de delta visível entre frames (não só rename).
Hitstop/recovery são frames, não adjetivos. Scanline: `audit_sprite_line_sim.py`
antes de animar um elenco inteiro na mesma linha.
Gate: `audit_animation_semantics.py` (permutação, clone, ciclo idêntico, pivot, roster).

Review independente: `quality_review_router.py` domínio `animation`.
Não simule aprovação humana da incumbente.
