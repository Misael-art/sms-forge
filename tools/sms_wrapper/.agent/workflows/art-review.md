# workflow: art-review

Use this flow for every character concept/model sheet and for the first roster
sprite board, then again when a material art revision changes identity, pose,
equipment, palette, scale, or silhouette. The author prepares the evidence; the
independent reviewer reviews read-only; the owner approves promotion. A producer
never approves their own art.

O encadeamento de status entre este review e prova técnica, conversão, ROM
diagnóstica e produção está em `workflows/artwork-to-rom-lifecycle.md`.

## 1. Freeze the review target

- Save the exact candidate as a versioned asset. Record its path, SHA-256,
  dimensions, medium (concept illustration or pixel sprite), and the source
  image being reviewed.
- For every character, list the canonical game reference and accepted concept
  by role and SHA-256. Record a secondary reference only for the detail it is
  authorized to clarify. For J.J., Zillion II SMS remains authority for game
  identity, palette, and behavior; the approved v4 concept guides this board's
  costume/equipment silhouette. Do not add series text or logos unless the
  accepted design calls for them.
- Record the actual requested defects before revising. Do not overwrite the
  rejected source or its review notes.
- Convert owner feedback into a revision table before generation: observed
  defect → exact visual change → evidence/axis that closes it. Freeze the
  accepted identity reference and SHA, then list non-regression invariants
  (face, age, body type, palette, scale, costume, named props, view layout and
  selected style). Each new revision must preserve the prior candidate and
  state its real parents; a review should not silently redesign unrelated
  features.

## 2. Inspect each character in a fixed order

Inspect every character individually, then the full roster board:

1. **Identity and face:** accepted face, hair, mask, eyes, expression, and
   canonical costume remain legible; no floating pixels or color marks in the
   eye/face region.
2. **Hands and anatomy:** both hands have plausible left/right orientation;
   open hands have readable fingers and thumb; fists have a clear knuckle mass;
   wrists connect to forearms; elbows and knees follow the pose.
3. **Grip and weapon continuity:** trace hand → grip → guard → blade/barrel.
   The weapon must visibly sit in the hand, align through the guard and shaft,
   and terminate without crossing a foot or the shared ground line. The chosen
   hand and grip must match the approved pose.
4. **Equipment attachment:** shields show a plausible forearm grip or strap;
   bows have two coherent limbs and a string; quivers/arrows, scabbards, canes,
   straps, armor, and holsters remain distinct and attach to the correct body
   part with consistent perspective.
5. **Silhouette and proportion:** compare head, torso, limbs, apparent mass,
   baseline, and height against the roster contract and approved concepts.
   Scale measurements never replace this visual check.
6. **Grounding and edges:** boots meet the common baseline intentionally;
   blades and equipment do not pierce feet or floor. Inspect the full contour
   for broken outline, halos, loose marks, specks, and accidental crop damage.
7. **Color and rendering:** compare each material to its character palette;
   keep highlights, shadows, and weapon lighting consistent with the body and
   shared light direction. Use coherent color clusters without decorative
   dithering or scattered high-contrast pixels. Assign each accent a semantic
   region before conversion; white and yellow may not leak into cloth, hair, or
   contour pixels. Preserve a white/yellow cluster only where the approved
   design names that use, such as a glove, collar, eye, or cane pommel.
8. **Roster harmony:** compare line weight, edge treatment, anatomy, color
   grouping, finish, relative scale, and baseline across the complete lineup.

9. **Artist reference and scope (concept sheets):** identify the catalog index,
   selected work, named artist/studio, verified role, and source. Separate an
   illustrator's promotional art from game sprite authorship. If no individual
   credit is confirmed, record that status instead of guessing.
10. **Distinctive style signature (concept sheets):** list visible, transferable
    traits for line, shape, anatomy, color grouping, and finish. Compare with
    neighboring catalog directions and state what distinguishes them. For
    example, Eisuke Ogura and Toshiaki Mori (Shinkiro) are separate references;
    do not collapse their different drawing/rendering approaches into one
    generic “SNK style.” Treat the traits as visual analysis, not a credit claim.
11. **Pose anatomy and joint continuity (concept sheets):** trace every posed
    limb from torso/shoulder through upper arm, elbow, forearm, wrist, and hand.
    Confirm the shoulder is seated beneath the garment seam, the elbow follows
    the action, clothing folds explain overlaps, and the hand/grip is supported
    by the arm in perspective. Check both action pose and orthographic views.
12. **Visual cohesion and distinction (concept sheets):** confirm all five views
    retain one identity, silhouette, costume, and rendering language, while the
    chosen artist reference remains distinguishable from other catalog styles.
13. **Page composition (concept sheets):** inspect the final composed image, not
    only the raw generation. The source art must not contain baked titles,
    rulers, baselines, or view labels; the compositor adds each once. Confirm
    ruler and baseline alignment, label/card clearance, no overlap with body or
    equipment, and no clipped text or art.

## 3. Inspect at the right scale for the medium

- Concept/model illustration: review the whole image at native view, then
  inspect enlarged crops of face, both hands, each weapon/equipment junction,
  knees, feet, and outline. Do not claim SMS palette or pixel-cleanliness from
  a truecolor concept image.
- Pixel sprite: inspect every relevant frame at native size and nearest-neighbor
  4× (or greater) over light and dark backgrounds. Keep hard pixel edges;
  antialiasing is not a cleanup method for pixel art. Run the applicable
  palette/resource, cutout/material, animation, and roster-scale gates.
- Pixel sprite polish pass: explicitly review `pixel_clusters`,
  `face_detail_readability`, `outline_and_cutout`, `material_shading`,
  `material_shadow_flow_coherence`, `semantic_palette_role_confinement`,
  `hand_weapon_attachment`,
  `equipment_geometry`, `frame_pose_integrity`, and `native_size_readability`
  for every character. Look at eyes and mouth at 1×; require deliberate square
  clusters rather than softened paint or stray single-pixel noise; group each
  material into a small base/shadow/highlight ramp from that character's exact
  palette. Confirm that each tone follows a coherent material plane and fold
  direction across the whole garment and every frame: permitted colors alone
  do not prove coherent shading. A brighter blue isolated inside a shadowed
  cloth plane is a fail until its placement is visually justified. Keep shadow,
  base, and highlight as contiguous hard-edged planes; do not interleave tones
  to simulate texture. Scan white/yellow pixels against their declared semantic
  regions and flag isolated points at the face, garment, or outline; do not
  erase an approved eye, glove, collar, or equipment cluster while cleaning
  nearby leakage. A connected-component test that only catches pixels fully
  surrounded by cloth is insufficient: it misses leaks on material boundaries.
  Use feature-anchored masks where practical (for example, hair/face for glasses
  and glove-plus-shaft intersection for a cane pommel). For white, preserve the
  glove shape and long straight cane segments; check isolated singles/pairs
  outside those masks against the design before recoloring. Geometry can locate
  a candidate region but does not prove its semantic role. Independently inspect
  every retained/reassigned accent at 1× and nearest-neighbor 4×. Do not add dithering, blur,
  antialiasing, glows, or unplanned colors to hide a weak cluster. Check metal
  shields and blades for flat highlights, hands against grips/guards, bow limbs
  and string, coat/cape hems, boot contours, and the common baseline.
   For a multi-pass repair, freeze the source SHA and pose IDs, change one defect
   family per version, and emit a per-frame delta. A pixel edit invalidates the
   prior preview, ROM and captures: rebuild in a fresh versioned diagnostic
   directory and compare every frame before asking for review. Preserve rejected
   candidates with their reason; do not promote a promising partial pass.
- Conversion proof: show exactly one idle pose and one action pose. Keep the
  8×8 occupancy map separate. No grid, baseline, ruler, label, border, or note
  may cross a sprite preview. Run `audit_asset_proof_sheet.py` to compare each
  displayed crop against its indexed source pixel by pixel; any difference
  rejects the proof. The gate catches compositing/resampling changes, not
  anatomy, style, or concept fidelity.
- A two-pose proof is not a two-frame animation. It cannot prove frame count,
  timing, cycle, scanline load, SAT use, VRAM residency, or VBlank cost. The SMS
  has no universal physical frame-count limit per sheet; set the project limit
  only after pools, banking, resident states, and VBlank costs are in the TDD
  and scene budget.
- If a generative image tool returns a sprite sheet, treat it as a new art
  proposal, not a pixel-precise edit. Verify canvas dimensions and cell grid,
  compare every pose to the declared animation semantics, then run palette,
  cutout, resource, and animation gates. A changed action, repeated pose,
  broken cell layout, or palette mismatch rejects that output before it enters
  the source-art lineage. The generator's stated intent is not evidence that
  pose or pixel invariants were preserved.
- A single frame can review identity and construction, but cannot approve
  animation, a full sheet, runtime integration, or a ROM.
- Before sprite generation, inspect the sequence contract: trigger, loop or
  transition, initial/final state, ordered pose IDs/count and durations, and a
  separate track for every animated character, weapon, projectile, or effect.
  Confirm the object has its own initial/final state and declared source-pose
  count; a prop moving in sync with the actor is not automatically reviewed.
  A projectile/effect that outlives the actor sequence also needs a separate
  launch/termination event and lifetime in ticks.
- For locomotion/combat, trace support points, center-of-mass path, acceleration,
  weapon grip and hitbox through time. Check that reach follows the shown body
  and equipment, contact/recovery are distinct, and the opponent has readable
  counterplay. Mark unmeasured physics/frame data as pending; do not infer
  balance from a still or from copied numbers.
- Every animation reviews all 12 principles—squash/stretch, anticipation,
  staging, straight ahead/pose to pose, follow-through/overlap, slow in/out,
  arcs, secondary action, timing, exaggeration, solid drawing, and appeal. At
  least seven must be applied with a planned effect tied to frame IDs; each
  remaining principle gets a contextual reason. A planning cue is not evidence
  until pixels are drawn and reviewed in motion. Static poses do not prove
  movement or timing. The list measures review coverage, not artistic truth.
- Keep source pose count separate from hardware object/tiles count. Review a
  proposal manifest with `audit_animation_contract.py`; after PNGs exist, run
  `audit_animation_semantics.py` and review actual playback. Independent review
  and owner approval remain required.

## 4. Record and gate the decision

- Fill every required axis for every character as `pass`, `fail`, `pending`, or
  `not_applicable` with a concrete note. A `not_applicable` needs a reason.
- Every `character_concept_model_sheet` checklist must declare and cover
  `document_and_layout`, `artist_reference_and_scope`, `distinctive_style_signature`,
  `pose_anatomy_and_joint_continuity`, and
  `visual_cohesion_and_distinction`, in addition to its other axes. These axes
  make review coverage explicit; their presence does not make artistic truth
  machine-verifiable.
- Recheck the composed candidate after layout changes (§104); an intact raw
  image does not approve labels/rulers/cards. Historical checklists remain
  archived; missing layout coverage needs a new review, not retroactive approval.
  `document_and_layout` cannot be not_applicable for a concept model sheet:
  even an unlabelled sheet requires checking its final view arrangement/crops.
- For asset kinds `pixel_sprite_sheet` and `pixel_sprite_roster_board`, the
  checklist gate requires the eight pixel-specific micro-axes above; broad
  notes such as “looks clean” do not cover them.
- Run `audit_art_review_checklist.py --manifest <checklist.json>
  --project-root <project> --verify-hashes`. This checks coverage, statuses,
  and freshness; it does not decide whether a hand or face is artistically
  correct.
- Any `fail` blocks the candidate. Any `pending` or missing owner approval also
  blocks promotion. Revise the source art, update its hash and notes, then repeat
  all affected character axes and the full roster comparison.
- At a quality checkpoint, submit a hash-bound art request through
  `quality_review_router.py`; the reviewer is read-only and distinct from the
  producer. The owner gives final approval. No automatic or producer approval.
- After a correction, repeat the full checklist, with a second focused pass over
  the defect and its neighboring anatomy/equipment junctions. A locally fixed
  arm can still detach at the shoulder, merge with another arm, obscure a grip,
  or change the identity of a prop. Confirm the repaired image against its
  frozen source and every unchanged invariant before the independent review.
- Only after those reviews pass may pixel conversion proceed. Palette/resource
  conformance, animation semantics, integration, and emulator validation remain
  separate gates; an art review never implies a delivery claim.

## Current Master of Fighters review

The user-supplied 2026-10-04 board had reported defects on all seven characters.
The corrected v2 illustration is a review candidate only. Its checklist remains
owner-pending; it is not a pixel sprite sheet, not palette-validated, and not
approved for integration. See `doc/roster_harmony_candidate_review_v1.json` and
the versioned study in `data/source_art/roster_harmony_review/`.

The owner's 2026-10-05 post-treatment feedback says the critical construction
defects are mostly corrected and lists remaining pixel-art polish by character.
Keep that status separate from the RGB v2 illustration above. Record the new
feedback against the exact sprite board and its source-sheet hashes before
changing or promoting any of the seven 12-frame sheets. See
`doc/roster_harmony_refinement_review_v1.json`; its known failures and pending
axes continue to block promotion.
# Emendas de material e limites das métricas (L124)

Antes de corrigir cores/contorno, conferir a autorização vigente da revisão:
edição dentro de máscara, transferência entre materiais e acrescentar contorno
são escopos distintos. Preserve a decisão inicial e suas emendas por hash;
proibição/aceite de uma revisão não vira permissão universal para o algoritmo.

Quando o contrato pedir bloco sólido 2×2, área e bbox não bastam: um L de quatro
pixels pode não conter quadrado. Verifique o predicado exato e declare exceções
semânticas autorizadas (olho, detalhe metálico ou haste 1px). Esse requisito é
do asset, não lei do SMS. Paleta válida dentro da máscara não comprova cobertura
da região: revisar franjas/fronteiras contra a fonte aprovada.

Relate separadamente alpha/silhueta, cores, ownership de material e pixels de
contorno acrescentados. Registrar ordem de mudanças, recomputação, desempate,
limite de iterações e critério de parada se houver cleanup iterativo. Ponto
fixo/zero ilhas não prova luz, anatomia ou qualidade; revisar em 1× e NN ampliado.
Parecer independente declarado precisa apontar seu relatório preservado por SHA.
