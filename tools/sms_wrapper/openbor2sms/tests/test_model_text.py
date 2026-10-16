# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/tests/test_model_text.py
#   donor sha256: 15f9d2a730d71ed582a0affe9793bc72192f33561f73a4c9aae06049baafc3d2
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms front-end O1)
# Adaptation: only import paths changed from openbor2sgdk_forge.* to
# openbor2sms.*; assertions are unchanged from the donor test.
"""Synthetic model and level fixtures. No module text from the archive."""

import unittest

from openbor2sms.analyze import anim_unknowns, delay_to_frames, summarize_level
from openbor2sms.level_inventory import build_level_inventory
from openbor2sms.model_text import parse_level, parse_model


class ModelTextTests(unittest.TestCase):
    def test_attack_persists_until_cleared_and_delay_changes(self):
        model = parse_model(
            """
anim attack1
offset 10 20
bbox 1 2 3 4
delay 4
frame data/a.gif
attack1 2 3 4 5 6 0 0 0 8 9
frame data/b.gif
frame data/c.gif
attack1 0 0 0 0 0
delay 15
frame data/d.gif
"""
        )
        anim = model.anim("attack1")
        self.assertEqual([frame.path for frame in anim.frames], ["data/a.gif", "data/b.gif", "data/c.gif", "data/d.gif"])
        self.assertEqual(anim.frames[0].attacks, [])
        self.assertEqual(anim.frames[1].attacks[0].damage, 6)
        self.assertEqual(anim.frames[1].attacks[0].depth, 9)
        self.assertEqual(anim.frames[2].attacks[0].damage, 6)
        self.assertEqual(anim.frames[3].attacks, [])
        self.assertEqual(anim.frames[2].delay, 4)
        self.assertEqual(anim.frames[3].delay, 15)
        self.assertEqual(model.issues, [])

    def test_unknown_directive_keeps_its_line(self):
        model = parse_model(
            """
anim idle
offset 1 1
frobnicate 3
delay 2
bbox 0 0 1 1
frame data/idle.gif
"""
        )
        unknown = anim_unknowns(model.anim("idle"))
        self.assertEqual(unknown[0]["command"], "frobnicate")
        self.assertEqual(unknown[0]["line"], 4)

    def test_script_is_bound_to_the_next_frame(self):
        model = parse_model(
            """
anim spawn
@script
if(frame==1){
}
@end_script
offset 1 1
bbox 0 0 1 1
delay 1
frame data/idle.gif
"""
        )
        anim = model.anim("spawn")
        self.assertEqual(len(anim.scripts), 1)
        self.assertIn("if(frame==1){", anim.scripts[0].body[0])
        self.assertTrue(anim.frames[0].script_bound)
        self.assertEqual(model.issues, [])

    def test_new_anim_does_not_inherit_boxes(self):
        model = parse_model(
            """
anim idle
offset 8 8
bbox 1 1 2 2
delay 3
attack1 1 1 2 2 4 0 0 0 1 2
frame data/a.gif
anim walk
offset 8 8
delay 3
bbox 1 1 2 2
frame data/b.gif
"""
        )
        self.assertEqual(model.anim("walk").frames[0].attacks, [])

    def test_hash_starts_a_comment_even_without_a_space(self):
        model = parse_model("palette data/ax.gif #1\nname Hero\n#anim fake\n")
        self.assertEqual(model.header[0].args, ["data/ax.gif"])
        self.assertIsNone(model.anim("fake"))

    def test_level_spawn_groups_and_music(self):
        level = parse_level(
            """
music data/music/STAGE1.BOR
panel data/bgs/panel.gif
spawn long
health 50
coords 500 180
at 0
spawn henin
coords 550 190
at 0
"""
        )
        summary = summarize_level(level, 512, 0)
        self.assertEqual(summary["music_claim"], "unsupported_reachable")
        self.assertEqual(len(summary["spawns_in_slice"]), 1)
        self.assertEqual(summary["spawns_in_slice"][0]["name"], "long")
        self.assertEqual(summary["spawns_outside_slice"], 1)

    def test_level_event_projects_negative_screen_spawn_into_world(self):
        level = parse_level(
            """panel data/bgs/panel.gif
spawn amaz
health 75
coords -20 190
at 300
"""
        )
        summary = summarize_level(level, 320, 300)
        self.assertEqual(len(summary["spawns_in_slice"]), 1)
        self.assertEqual(summary["spawns_in_slice"][0]["coords"], (-20, 190))
        self.assertEqual(summary["spawns_in_slice"][0]["world_x"], 280)
        self.assertEqual(summary["spawns_outside_slice"], 0)

    def test_spawn_without_its_own_at_does_not_reuse_previous_event_position(self):
        level = parse_level(
            """spawn first
at 100
spawn second
health 25
"""
        )
        self.assertEqual(level.spawns[0].at, 100)
        self.assertIsNone(level.spawns[1].at)
        self.assertTrue(any("spawn second is not followed by its own at" in issue for issue in level.issues))

    def test_player_start_tuples_are_typed_and_source_ordered(self):
        level = parse_level(
            "spawn1 50 20 200\nspawn2 40 30 200\nspawn3 60 40 200\nspawn4 50 50 200\n"
        )
        self.assertEqual(
            [(item.slot, item.line, item.x, item.z, item.y) for item in level.player_starts],
            [(1, 1, 50, 20, 200), (2, 2, 40, 30, 200), (3, 3, 60, 40, 200), (4, 4, 50, 50, 200)],
        )
        self.assertEqual([item.command for item in level.header], ["spawn1", "spawn2", "spawn3", "spawn4"])
        self.assertEqual(level.issues, [])

    def test_player_start_malformed_and_duplicate_slots_are_diagnostics(self):
        level = parse_level("spawn1 50 20\nspawn2 40 30 200\nspawn2 41 30 200\n")
        self.assertEqual([(item.slot, item.x) for item in level.player_starts], [(2, 40), (2, 41)])
        self.assertTrue(any("player-start spawn1 needs exactly three integers" in issue for issue in level.issues))
        self.assertTrue(any("duplicate player-start slot 2" in issue for issue in level.issues))

    def test_level_inventory_preserves_control_order_without_concurrency_claim(self):
        level = parse_level(
            """music data/music/stage.bor
spawn long
at 0
group 3
wait 30
spawn henin
at 300
wall 100 200
"""
        )
        inventory = build_level_inventory(level, [("long", "data/models/long.txt", 2)])
        self.assertEqual(
            [row["command"] for row in inventory["timeline"]],
            ["music", "spawn", "at", "group", "wait", "spawn", "at", "wall"],
        )
        self.assertFalse(inventory["concurrency_claim"])
        self.assertEqual(inventory["counts"]["group_directives"], 1)
        self.assertEqual(inventory["counts"]["wait_directives"], 1)
        self.assertEqual(inventory["dynamic_spawns"][0]["alias_match"]["path"], "data/models/long.txt")
        self.assertEqual(inventory["unresolved_spawn_aliases"], [{"line": 6, "name": "henin"}])
        ambiguous = build_level_inventory(level, [
            ("long", "data/models/long.txt", 2),
            ("LONG", "data/models/another_long.txt", 9),
        ])
        self.assertEqual(ambiguous["ambiguous_spawn_aliases"], [{"line": 2, "name": "long"}])
        self.assertIsNone(ambiguous["dynamic_spawns"][0]["alias_match"])

    def test_delay_conversion_is_explicit(self):
        self.assertEqual(delay_to_frames(12, 60), 7)
        self.assertEqual(delay_to_frames(8, 60), 4)
        self.assertEqual(delay_to_frames(12, 50), 6)
        self.assertIsNone(delay_to_frames(999, 60))

    def test_truncated_attack_is_an_issue_not_a_zero_box(self):
        model = parse_model(
            """
anim attack1
offset 1 1
bbox 0 0 1 1
delay 1
attack1 1 2
frame data/a.gif
"""
        )
        self.assertTrue(any("five integers" in issue for issue in model.issues))
        self.assertEqual(model.anim("attack1").frames[0].attacks, [])

    def test_short_zero_attack_clears_without_becoming_a_box(self):
        model = parse_model(
            """
anim attack1
offset 10 10
bbox 0 0 4 4
delay 1
attack 4 4 6 6 3
frame data/a.gif
attack 0 0 0 0
frame data/b.gif
"""
        )
        self.assertEqual(model.issues, [])
        frames = model.anim("attack1").frames
        self.assertEqual(frames[0].attacks[0].damage, 3)
        self.assertEqual(frames[1].attacks, [])

    def test_shock_box_is_stored_as_attack_damage(self):
        model = parse_model(
            """
anim grabattack
offset 10 10
bbox 0 0 4 4
delay 1
shock 92 140 30 25 2
frame data/a.gif
"""
        )
        self.assertEqual(model.issues, [])
        attack = model.anim("grabattack").frames[0].attacks[0]
        self.assertEqual(attack.damage, 2)
        self.assertEqual(attack.right, 30)


if __name__ == "__main__":
    unittest.main()
