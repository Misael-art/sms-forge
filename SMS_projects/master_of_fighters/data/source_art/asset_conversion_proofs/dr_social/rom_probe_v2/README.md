# Dr. Social — ROM conversion probe v2

Disposable diagnostic for indexed PNG → 4bpp tiles → SMS metasprite → ROM →
isolated Emulicious framebuffer. It uses the v4 idle/action key poses and
preserves their pixel indices. It is not a production asset, full animation,
roster P1 approval, gameplay, or delivery.

The v2 probe reserves tile 0 as a blank BG tile and clears the complete visible
name table before drawing. This addresses the v1 capture's garbage in
transparent areas; the v1 capture remains preserved as a failed diagnostic.
The fighter patterns are shared between poses and drawn as 8×8 SAT objects
through `SMS_addMetaSprite`. Button 1 selects idle; button 2 selects the static
action key pose. This tests rendering and pose selection, not timed animation.

The temporary project is written under
`SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v2/`.
The single-character study palette loads into P1 for this probe. The
roster-wide shared P1 allocation remains pending.

## Reproduce

```sh
rtk proxy python3 SMS_projects/master_of_fighters/data/source_art/asset_conversion_proofs/dr_social/rom_probe_v2/prepare_probe.py \
  --scratch SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v2/project
rtk proxy python3 tools/sms_wrapper/audit_validate_resources.py \
  --project SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v2/project \
  --kind sheet --character dr_ferdinand_social \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v2/project/res/sprites/dr_social_idle_keypose_v4.png \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v2/project/res/sprites/dr_social_action_keypose_v4.png
rtk proxy python3 tools/sms_wrapper/audit_sprite_line_sim.py \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v2/project/doc/sprite_scene_idle_v1.json
rtk proxy python3 tools/sms_wrapper/audit_sprite_line_sim.py \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v2/project/doc/sprite_scene_action_v1.json
rtk proxy python3 tools/sms_wrapper/build_inner.py \
  --project SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v2/project
```

Bind exact PNG/header/ROM hashes, run in a private Emulicious session, capture
idle and action separately, and close that session on every path. Require
`audit_render_fidelity.py` to pass both captures before claiming source-exact
rendering. Keep diagnostic resources outside the production project's `res/`.
