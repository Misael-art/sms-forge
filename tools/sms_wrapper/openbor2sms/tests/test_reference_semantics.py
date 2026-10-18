# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/tests/test_reference_semantics.py
#   donor sha256: ca9a7f8a283a6debd369cdb79d41c1a55fee813929823108829439755a19dd14
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms front-end O1)
# Adaptation: only import paths changed from openbor2sgdk_forge.* to
# openbor2sms.*; assertions are unchanged from the donor test.
"""Fixtures for the narrow pinned-source event-capacity preflight."""

import unittest
from collections import Counter

from openbor2sms.model_text import parse_level, parse_model
from openbor2sms.reference_semantics import (
    REFERENCE_PROFILE,
    build_reference_event_preflight,
    compile_level_event_ir,
    compile_spawn_queue,
    default_next_hit_frames,
    lower_makeinv,
    simulate_reference_dispatch_step,
)


class ReferenceSemanticsTests(unittest.TestCase):
    def test_makeinv_uses_seconds_and_signed_blink_flag_from_pinned_engine(self):
        self.assertEqual(REFERENCE_PROFILE["semantics"]["game_speed_default"], 200)
        self.assertEqual(REFERENCE_PROFILE["engine_locations"]["makeinv_parse"], "engine/openbor.c:16045-16054")
        blinking = lower_makeinv(["5", "0"])
        self.assertEqual(blinking["logical_ticks_signed"], 1000)
        self.assertEqual((blinking["ntsc_frames"], blinking["pal_frames"]), (300, 250))
        self.assertTrue(blinking["blink"])
        suppressed = lower_makeinv(["5", "1"])
        self.assertEqual(suppressed["logical_ticks_signed"], -1000)
        self.assertFalse(suppressed["blink"])

    def test_next_hit_lockout_uses_separate_strict_deadline(self):
        self.assertEqual(REFERENCE_PROFILE["semantics"]["default_next_hit_ticks"], 40)
        self.assertEqual(default_next_hit_frames(60), 13)
        self.assertEqual(default_next_hit_frames(50), 11)
        with self.assertRaises(ValueError):
            default_next_hit_frames(0)

    def test_malformed_makeinv_fails_closed(self):
        with self.assertRaises(ValueError):
            lower_makeinv(["not-a-duration", "0"])

    def test_wait_and_group_queue_closes_at_positions(self):
        level = parse_level(
            """group 4 4
at 900
wait
at 900
spawn thief1
at 900
spawn thief2
at 900
"""
        )
        queue, issues = compile_spawn_queue(level)
        self.assertEqual(issues, [])
        self.assertEqual(
            [(event["kind"], event["at"]) for event in queue],
            [("group", 900), ("wait", 900), ("spawn", 900), ("spawn", 900)],
        )

    def test_level_event_ir_preserves_source_order_and_blocks_unclosed_spawn(self):
        level = parse_level(
            """spawn first
coords 12 180
at 100
spawn second
""",
            "data/levels/test.txt",
        )
        event_ir = compile_level_event_ir(level)
        self.assertEqual(event_ir["ir_version"], "openbor-level-event-ir/1")
        self.assertEqual(event_ir["source_path"], "data/levels/test.txt")
        self.assertEqual(event_ir["status"], "blocked")
        self.assertEqual(event_ir["events"][0]["at"], 100)
        self.assertEqual(event_ir["events"][0]["directives"][0]["command"], "coords")
        self.assertEqual(
            [item["command"] for item in event_ir["source_directives"]],
            ["spawn", "coords", "at", "spawn"],
        )
        self.assertFalse(event_ir["runtime_binding"]["connected"])
        self.assertTrue(event_ir["diagnostics"])
        report = build_reference_event_preflight(
            level, {}, Counter(), REFERENCE_PROFILE["files"]
        )
        self.assertTrue(any(item.startswith("level_parse_issue:") for item in report["blockers"]))

    def test_same_position_enemy_batch_is_limited_by_pinned_group_max(self):
        level = parse_level(
            """group 4 4
at 900
wait
at 900
spawn thief1
at 900
spawn thief2
at 900
spawn thief1
at 900
spawn thief2
at 900
"""
        )
        aliases = Counter({"thief1": 1, "thief2": 1})
        models = {
            "thief1": parse_model("name Thief1\ntype enemy\n"),
            "thief2": parse_model("name Thief2\ntype enemy\n"),
        }
        report = build_reference_event_preflight(level, models, aliases, REFERENCE_PROFILE["files"])
        self.assertEqual(report["maximum_enemy_slots_requested_by_same_position_batch"], 4)
        batch = report["group_segments"][0]["enemy_batches"][0]
        self.assertEqual(batch["at"], 900)
        self.assertEqual(batch["enemy_spawn_count"], 4)
        self.assertEqual(batch["reference_profile_batch_capacity"], 4)
        self.assertFalse(report["original_module_version_verified"])
        self.assertIn("original_module_openbor_version_unverified", report["blockers"])

    def test_group_cap_limits_static_batch_and_non_enemies_are_excluded(self):
        level = parse_level(
            """group 3 3
at 1100
spawn civilian
at 1100
spawn pickup
at 1100
spawn long
at 1100
spawn henin
at 1100
spawn amaz
at 1100
spawn long
at 1100
"""
        )
        aliases = Counter({"civilian": 1, "pickup": 1, "long": 1, "henin": 1, "amaz": 1})
        models = {
            "civilian": parse_model("name Civilian\ntype obstacle\n"),
            "pickup": parse_model("name Pickup\ntype item\n"),
            "long": parse_model("name Long\ntype enemy\n"),
            "henin": parse_model("name Henin\ntype enemy\n"),
            "amaz": parse_model("name Amaz\ntype enemy\n"),
        }
        report = build_reference_event_preflight(level, models, aliases, REFERENCE_PROFILE["files"])
        self.assertEqual(report["maximum_enemy_slots_requested_by_same_position_batch"], 3)
        self.assertEqual(report["spawn_directive_counts_by_model_type"], {"enemy": 4, "item": 1, "obstacle": 1})
        self.assertEqual(report["typed_non_enemy_spawn_directive_count"], 2)
        self.assertTrue(report["spawn_counts_are_level_wide_directives_not_live_concurrency"])
        batch = report["group_segments"][0]["enemy_batches"][0]
        self.assertEqual(batch["enemy_spawn_count"], 4)
        self.assertEqual(batch["reference_profile_batch_capacity"], 3)

    def test_gal_town1_group_three_wait_continues_same_eligible_queue_pass(self):
        # The typed records and lines are from the hash-bound GAL TOWN1 queue.
        # The three pre-group spawns are TEXT, ITEM, and obstacles, so they do
        # not satisfy Group 3 3's TYPE_ENEMY count.
        self.assertEqual(
            REFERENCE_PROFILE["engine_locations"]["group_parse"],
            "engine/openbor.c:24855-24868",
        )
        self.assertEqual(
            REFERENCE_PROFILE["engine_locations"]["group_dispatch"],
            "engine/openbor.c:50037-50144",
        )
        self.assertEqual(
            REFERENCE_PROFILE["engine_locations"]["wait_release"],
            "engine/openbor.c:50170-50175",
        )
        self.assertIn("continues", REFERENCE_PROFILE["semantics"]["group_wait_same_pass"])
        queue = [
            {"kind": "spawn", "line": 49, "at": 0, "name": "intro", "model_type": "text", "model_script_blocks": 0},
            {"kind": "spawn", "line": 58, "at": 0, "name": "bizzar1", "model_type": "item", "model_script_blocks": 0},
            {"kind": "spawn", "line": 66, "at": 0, "name": "civ02", "model_type": "obstacle", "model_script_blocks": 0},
            {"kind": "spawn", "line": 73, "at": 0, "name": "civ03", "model_type": "obstacle", "model_script_blocks": 0},
            {"kind": "group", "line": 83, "at": 0, "group_min": 3, "group_max": 3},
            {"kind": "spawn", "line": 86, "at": 0, "name": "long", "model_type": "enemy", "model_script_blocks": 0},
            {"kind": "spawn", "line": 92, "at": 0, "name": "henin", "model_type": "enemy", "model_script_blocks": 0},
            {"kind": "wait", "line": 98, "at": 300},
            {"kind": "spawn", "line": 101, "at": 300, "name": "amaz", "model_type": "enemy", "model_script_blocks": 0},
            {"kind": "spawn", "line": 107, "at": 300, "name": "henin", "model_type": "enemy", "model_script_blocks": 0},
        ]

        at_zero = simulate_reference_dispatch_step(
            queue, cursor=0, level_position=0, enemy_count=0
        )
        self.assertEqual(
            [event["source_line"] for event in at_zero["processed"]],
            [49, 58, 66, 73, 83, 86, 92],
        )
        self.assertEqual(at_zero["enemy_count_after"], 2)
        self.assertEqual((at_zero["group_min"], at_zero["group_max"]), (3, 3))
        self.assertEqual(at_zero["cursor_after"], 7)
        self.assertFalse(at_zero["waiting"])
        self.assertEqual(at_zero["stop_reason"], "position_blocked")

        before_at_300 = simulate_reference_dispatch_step(
            queue,
            cursor=at_zero["cursor_after"],
            level_position=299,
            enemy_count=at_zero["enemy_count_after"],
            group_min=at_zero["group_min"],
            group_max=at_zero["group_max"],
        )
        self.assertEqual(before_at_300["cursor_after"], 7)
        self.assertFalse(before_at_300["waiting"])
        self.assertEqual(before_at_300["stop_reason"], "position_blocked")

        at_300 = simulate_reference_dispatch_step(
            queue,
            cursor=before_at_300["cursor_after"],
            level_position=300,
            enemy_count=before_at_300["enemy_count_after"],
            group_min=before_at_300["group_min"],
            group_max=before_at_300["group_max"],
            wait_has_enemy=True,
        )
        self.assertEqual(
            [event["source_line"] for event in at_300["processed"]],
            [98, 101],
        )
        self.assertEqual(at_300["processed"][0]["action"], "wait_set_continue_queue_pass")
        self.assertEqual(at_300["enemy_count_after"], 3)
        self.assertEqual(at_300["cursor_after"], 9)
        self.assertTrue(at_300["waiting"])
        self.assertFalse(at_300["wait_released_after_dispatch"])
        self.assertEqual(at_300["stop_reason"], "group_max_blocked")
        self.assertEqual(at_300["reference_commit"], REFERENCE_PROFILE["commit"])


if __name__ == "__main__":
    unittest.main()
