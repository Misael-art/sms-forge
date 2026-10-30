# skill: sms-asset-to-rom

Use after pixel art exists and the task is to convert, prove or integrate that
asset into a Sega Master System ROM. This skill handles data and rendering;
`art-review.md`, the concept sheet and the animation contract still own visual
identity, anatomy and motion.

The complete promotion flow, including roster harmony and human review between
conversion proof, diagnostic ROM and production, is in
`workflows/artwork-to-rom-lifecycle.md`.

## Promotion states

```text
approved concept
  → indexed pixel candidate
  → exact source/resource pass
  → diagnostic ROM render pass
  → human review + project palette/budget approval
  → production resource and ROM binding
  → release evidence
```

Each arrow needs its own evidence. A concept approval does not approve its
pixel translation. A diagnostic ROM does not by itself approve a production
asset, animation, gameplay, FPS, audio or delivery.

## 1. Freeze the source pixels

- Keep the source, concept lineage, manifest role and SHA-256 in the project's
  `data/source_art/` or `rascunho/` tree.
- Bind the **role** of each source before conversion. A concept sheet defines
  identity; the mandatory idle+action technical proof tests conversion; an
  owner-approved full animation sheet is the input for production sequences.
  Never substitute the two-pose proof for a separately approved animation
  source. Match its SHA, sequence IDs and pose counts to the animation contract.
- Make the converter fail closed when the selected path or SHA differs from
  the approved lineage. Add a self-check that accepts the approved source and
  rejects the technical proof when it is passed as animation input. In the
  Dr. Social pilot, `prepare_dr_social_61_pose_probe.py --self-check` enforces
  this source-role boundary before the converter writes output.
- Use an indexed PNG with index 0 transparent, no partial alpha, at most 15
  useful colors, and every RGB channel in `{0,85,170,255}`. For roster art,
  validate the character color profile, then separately map it to the one P1
  palette shared by active sprites. A local palette study is not a runtime
  palette allocation.
- If the approved source is indexed at 4 bits but the resource contract needs
  PNG type 3 at 8 bits, normalize the bit depth losslessly. Preserve index
  matrix, PLTE ordering, transparency and dimensions; compare the indices
  before and after. Do not downscale, recolor or clean pixels in this step.
- Run `audit_asset_proof_sheet.py` on the technical proof, then
  `audit_validate_resources.py --kind sheet --character <id> <pngs>` for each
  larger pose canvas. `res/sprites/` routes 8×8, 8×16 and 16×16 assets as
  physical sprite resources; a larger 8-aligned canvas is a sheet containing
  many physical objects. `build_inner.py --self-check` covers this routing and
  off-grid rejection.

## 2. Pack a pose as SMS hardware objects

`png_to_sms_tiles.py` encodes an individual 8×8 or 16×16 image. For a full
pose canvas made from multiple 8×8 objects, use
`pack_sms_metasprite.py`; do not pass an 80×80 pose to the single-sprite CLI.
Example:

```sh
rtk proxy python3 tools/sms_wrapper/pack_sms_metasprite.py \
  --pose idle=out/diagnostics/source/actor_idle.png \
  --pose action=out/diagnostics/source/actor_action.png \
  --prefix actor --tile-base 0 --reserve-blank \
  --header out/diagnostics/assets/actor_tiles.h \
  --manifest-dir out/diagnostics/assets/scene_manifests
```

The packer requires identical indexed palettes and pose canvases, 8×8
alignment, SMS legal colors, at most 128 px per axis for signed metasprite
offsets, no more than 64 SAT objects, no more than 8 objects on any scanline,
and patterns inside the selected 256-index sprite window. That index limit is
not automatically a safe resident VRAM budget: the sprite pattern half can
overlap the active BG name table. When a scene layout is known, pass
`--sprite-pattern-base 0x2000 --name-table-base 0x3800` (and the real
`--tile-base`) so the packer derives the safe capacity and rejects a pool that
would overwrite the name table. With that layout and `--tile-base 1`, the safe
resident pool is 191 patterns. The capacity formula is
`min(256 - tile_base, (name_table_base - (sprite_pattern_base + tile_base*32)) // 32)`.
If a sequence-wide pool exceeds the measured capacity, load a single pose at a
time or redesign the scene layout; never write pattern bytes through the PNT
or SAT. `pack_sms_metasprite.py --self-check` covers the 191/192 boundary. It deduplicates
identical 4bpp patterns across the input poses (4 planes, 32 bytes per tile)
and emits a C header plus `sprite_scene_manifest_v1` JSON for the line
simulator. `--reserve-blank` assigns the declared base tile as an all-zero
pattern. Only use that slot as a blank BG tile if the scene's name table also
references it; otherwise initialize the table with the actual stage map.

The CLI example above emits 8×8 objects in `SPRITEMODE_NORMAL`. For authored
samples, `prepare_authored_sprite_sample.py` uses the existing tall encoder by
default and this canonical normal packer through explicit v2 `sprite_size`.
Match runtime mode, tile base, generated geometry and scene manifests; never
infer hardware geometry from the artist's canvas.

Choose geometry from the whole pair in both orientations: 8×16 can reduce SAT
while increasing resident patterns or scanline overlap. Transparent packing
phase compensated in META can change interval overlap without changing PNGs;
it is not permission to omit cells, narrow the blade or resize the wide pose.
Measure SAT, scanlines and residency again after registration or reflection.
Check actual opaque sole after nearest rounding (`expected_opaque_bottom_px`
where applicable), not only nominal pivot. Airborne/authored travel needs its
own registration contract; do not force all poses to a single foot location.

Bind material-index remaps to the exact source SHA and shared P1. Inspect every
region using the index: an entry shared by cloth and skin affects both. Record
affected indices/materials and reinspect all affected poses. Neither palette
membership nor pixel-exact framebuffer proves material placement.

When adding an actor to shared P1, freeze the existing actor's index-to-code
mapping first. Recomputing nearest colors can recolor the preserved actor.
Inspect all used indices/RGBA in both facings; unused PLTE slots may change
under an explicit allocation contract without changing visible pixels. Whole
PLTE equality and visible identity are different assertions. J.J./Social is
one measured example, not a universal free-slot allocation or spare FX budget.

A failed conversion may preserve diagnostic PNGs, a partial header and a
report. Only a successful invocation with complete pose/duration tables and
all legal compositions is a candidate. Do not build from leftover files merely
because they exist. Tests in `tests/test_authored_sprite_sample.py` exercise
scale preservation, material remaps, grid compensation and both orientations.

## 3. Initialize the display and measure hardware use

Before enabling display, load the declared sprite palette and patterns and
write every visible name-table entry. A diagnostic solid background can
reserve a blank tile 0 and clear the 32×24 visible map while display is off.
In a real stage, write the stage's valid name table instead. Sprite index 0 is
transparent; BG index 0 is a visible color. Uninitialized VRAM is never a
valid background.

Run the independent gates:

- `audit_validate_resources.py` for indexed image, palette and grid;
- `audit_provenance.py` for the source/res relationship;
- `audit_sprite_mode.py` for SMS sprite geometry and selected pattern half;
- `audit_sprite_line_sim.py <scene_manifest>` for SAT, Y terminator and
  per-scanline object counts;
- `pack_sms_metasprite.py` with the scene's sprite-pattern and name-table bases
  for the physical resident pattern window;
- `build_inner.py --project <diagnostic_project>` for the real SDCC/devkitSMS
  build and included pre-gates.

These gates establish indexed-resource compliance and hardware geometry, not
the artistic placement of each material tone. Require the separate art-review
axes `material_shadow_flow_coherence` and `semantic_palette_role_confinement`:
follow shadow/base/highlight across cloth planes and folds in every pose, at 1×
and nearest-neighbor 4×, and verify that white/yellow accents remain inside
their declared character/material regions. A framebuffer exact-pixel pass
proves that the ROM rendered the converted image; it does not prove that its
light/shadow clusters or color-role placement read coherently.

Tile inventory is not a full scene budget. Count background/name table/SAT,
other sprites, shared patterns, VRAM residency, RAM/ROM and worst VBlank in the
project's scene budget. Hardware permits 16 KB VRAM, 64 SAT entries and 8
objects/scanline; the game's actual concurrent allocation can be lower.

## 4. Bind and inspect the ROM output

Create `doc/rom_asset_binding.json` for the exact source, indexed resource,
generated tile/metasprite symbol, generated header and ROM SHA/size. Require
`audit_rom_asset_binding.py --project <project> --require` after the build.
Rebuilds change the binding until hashes are refreshed.

Use an isolated Emulicious session pinned to that ROM. Capture each static
pose as its own published evidence session, or capture a frame-paced video for
continuous motion. An input ACK is not proof that the ROM changed pose: apply
input over enough VDP frames and inspect the resulting framebuffer. Close every
private session.

For a static 1:1 conversion on a uniform diagnostic BG, run:

```sh
rtk proxy python3 tools/sms_wrapper/audit_render_fidelity.py \
  --shot out/evidence/idle.png --art res/sprites/actor_idle.png \
  --at 88,48 --exact-indexed --transparent-rgb 000000
```

`--exact-indexed` checks every opaque pixel against the indexed RGB. When
`--transparent-rgb` is supplied, it also checks every source index-0 pixel
against that background, catching stale tilemap/VRAM noise. Use the structural
comparison mode for an actual scene with variable BG; that mode confirms pixel
class structure, not palette-exact color. A native screenshot plus an audit
report remains tied to its capture session and ROM SHA.

## 5. Promote only after the remaining gates

Before copying a candidate into production `res/`, require owner/independent
art review, the character's fixed palette mapping into shared P1, scene
resource budgets, asset binding and current project acceptance gates. For
animation, use `sms-sprite-animation.md` and `audit_animation_contract.py`;
static idle/action proof does not show timing, transitions, motion principles
or gameplay. Keep diagnostic PNGs/ROMs under ignored `out/diagnostics/` and
preserve their failed attempts beside the verification record.

## Proven example

`SMS_projects/master_of_fighters/data/source_art/asset_conversion_proofs/dr_social/rom_probe_v3/`
uses this route for Dr. Social's two v4 key poses. Its 16 KiB diagnostic ROM
renders both poses with zero opaque-pixel or declared transparent-background
mismatches; it remains a conversion proof, not the source for the 61-pose
animation. The owner-approved animation source is recorded separately at
`SMS_projects/master_of_fighters/data/source_art/sprite_studies/dr_social/dr_social_basic_sequences_61f_owner_source_v1.png`.
The 61-pose review ROM is generated from that exact SHA and remains diagnostic
until animation timing, scene palette/residency, VBlank, gameplay and production
asset binding pass their own gates.
