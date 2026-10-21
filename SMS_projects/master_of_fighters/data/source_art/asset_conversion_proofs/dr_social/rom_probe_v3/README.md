# Dr. Social — ROM conversion probe v3

This diagnostic exercises the reusable `tools/sms_wrapper/pack_sms_metasprite.py`
path with the v4 idle/action source poses. It normalizes PNG bit depth without
resampling, packs/deduplicates 4bpp patterns, reserves tile 0 as blank, clears
the 32×24 visible name table, then renders each pose through SMSlib in a
disposable ROM. It is not a production asset, full animation, roster P1
approval, gameplay, or delivery.

The background cleanup was required after v1 exposed reset-state VRAM as noise
behind transparent sprite pixels. The single-frame edge-triggered input did
not reliably change pose at the capture boundary; the verified capture uses a
frame-paced input sequence and observes the action pose in the framebuffer.
Each pose capture is a separate private Emulicious session so the evidence
publisher does not reuse a session bundle.

The temporary project is written under
`SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v3/`.
The Dr. Social study palette is loaded alone into P1 for this probe. The
roster-wide shared P1 mapping and full scene budget remain pending.

## Reproduce

```sh
rtk proxy python3 SMS_projects/master_of_fighters/data/source_art/asset_conversion_proofs/dr_social/rom_probe_v3/prepare_probe.py \
  --scratch SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v3/project
rtk proxy python3 tools/sms_wrapper/audit_validate_resources.py \
  --project SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v3/project \
  --kind sheet --character dr_ferdinand_social \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v3/project/res/sprites/dr_social_idle_keypose_v4.png \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v3/project/res/sprites/dr_social_action_keypose_v4.png
rtk proxy python3 tools/sms_wrapper/audit_sprite_line_sim.py \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v3/project/doc/sprite_scene_idle_v1.json
rtk proxy python3 tools/sms_wrapper/audit_sprite_line_sim.py \
  SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v3/project/doc/sprite_scene_action_v1.json
rtk proxy python3 tools/sms_wrapper/build_inner.py \
  --project SMS_projects/master_of_fighters/out/diagnostics/dr_social_asset_probe_v3/project
```

Bind source/resource/header/ROM hashes. Capture idle and action in separate
private sessions (or use frame-paced video), inspect the pixels, and run
`audit_render_fidelity.py --exact-indexed --at X,Y --transparent-rgb RRGGBB`
for a uniform diagnostic background. Keep all proof resources outside
production `res/`; promotion still requires human art review, a shared roster
P1 allocation, scene budgets and release gates.
