# Dr. Social — ROM conversion probe v1

This is a disposable diagnostic slice for checking indexed PNG → 4bpp tiles →
SMS metasprite → ROM → isolated Emulicious framebuffer. It uses the two v4
key poses and preserves their pixel indices. It is **not** an approved runtime
asset, a full animation, roster P1 palette approval, gameplay, or delivery.

The probe converts the 4-bit indexed source PNGs to 8-bit indexed PNGs without
changing pixels or palette colors, packs shared 8×8 patterns, and places them
as 8×8 SAT objects through `SMS_addMetaSprite`. Button 1 selects idle; button 2
selects the static action key pose. This tests rendering and pose selection;
it does not claim a timed animation.

The temporary build project and ROM are written under
`SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v1/`.
The runtime palette is the Dr. Social study palette loaded alone into P1 for
this probe. The roster-wide shared P1 allocation remains pending.

## Reproduce

```sh
rtk proxy python3 SMS_projects/master_of_fighters/data/source_art/asset_conversion_proofs/dr_social/rom_probe_v1/prepare_probe.py \
  --scratch SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v1/project
rtk proxy python3 tools/sms_wrapper/audit_validate_resources.py \
  --project SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v1/project \
  --kind sprite --character dr_ferdinand_social \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v1/project/res/sprites/dr_social_idle_keypose_v4.png \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v1/project/res/sprites/dr_social_action_keypose_v4.png
rtk proxy python3 tools/sms_wrapper/audit_sprite_line_sim.py \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v1/project/doc/sprite_scene_idle_v1.json
rtk proxy python3 tools/sms_wrapper/audit_sprite_line_sim.py \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v1/project/doc/sprite_scene_action_v1.json
rtk proxy python3 tools/sms_wrapper/build_inner.py \
  --project SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v1/project
```

Then bind the exact PNG/header/ROM hashes, start a private Emulicious session,
capture the idle and action states separately, and close that session in a
`finally` path. Do not copy the probe PNGs into the production project's
`res/` or mark this diagnostic ROM as a release build.
