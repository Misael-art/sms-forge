# Ported from SGDK-Forge (donor), read-only source.
#   donor path : tools/openbor2sgdk_forge/tests/test_level_event_table.py
#   donor sha256: b154d2492f033ae365e1a4cd5c2f94f18906edca7f127f8955d8d8a4f25146a6
#   license    : MIT (SGDK-Forge LICENSE, sha256 0b685fab1e0d2e0a9f85a4356a91c7bb16126be7b06e899f6cfed155cad2cf24)
#   port date  : 2026-10-15 (SMSForge openbor2sms front-end O1)
# Adaptation: only import paths changed from openbor2sgdk_forge.* to
# openbor2sms.*; assertions are unchanged from the donor test.
import unittest

from openbor2sms.level_event_table import compile_level_event_table, render_level_event_header


def _preflight(events):
    typed = []
    referenced = {}
    for event in events:
        row = {
            "kind": event["kind"],
            "line": event["line"],
            "at": event["at"],
            "directives": event.get("directives", []),
        }
        if event["kind"] == "spawn":
            row.update({"name": event["name"], "model_type": "enemy", "model_script_blocks": 0})
            referenced[event["name"].casefold()] = {
                "name": event["name"], "type": "enemy", "script_blocks": 0
            }
        elif event["kind"] == "group":
            row.update({"group_min": event.get("group_min"), "group_max": event.get("group_max")})
        typed.append(row)
    return {
        "status": "reference_profile_complete_module_version_unverified",
        "artifact_kind": "openbor_reference_event_capacity_preflight",
        "fidelity_claim": False,
        "runtime_playback_claim": False,
        "blockers": [
            "original_module_openbor_version_unverified",
            "reference_profile_is_not_openbor_runtime_playback",
        ],
        "spawn_model_type_unknown_count": 0,
        "referenced_spawn_models": list(referenced.values()),
        "spawn_queue_entry_count": len(events),
        "event_ir": {
            "ir_version": "openbor-level-event-ir/1",
            "status": "analysis_only",
            "diagnostics": [],
            "reference_profile": {"id": "openbor_test_pin", "commit": "7" * 40},
            "events": events,
        },
        "source": {
            "pak_sha256": "a" * 64,
            "level_sha256": "b" * 64,
            "level_member": "data/levels/test.txt",
        },
        "spawn_queue": typed,
    }


class LevelEventTableTests(unittest.TestCase):
    def test_emits_deterministic_typed_c_with_stable_alias_ids(self):
        events = [
            {
                "kind": "spawn", "line": 10, "name": "Grunt", "at": 120,
                "directives": [
                    {"command": "coords", "args": ["-20", "180"]},
                    {"command": "health", "args": ["45"]},
                    {"command": "map", "args": ["1"]},
                    {"command": "flip", "args": ["1"]},
                    {"command": "item", "args": ["Book"]},
                ],
            },
            {"kind": "group", "line": 20, "group_min": 0, "group_max": 4, "at": 120, "directives": []},
            {"kind": "wait", "line": 30, "at": 180, "directives": []},
        ]
        source1, report1 = compile_level_event_table(_preflight(events), "fixture_events")
        source2, report2 = compile_level_event_table(_preflight(events), "fixture_events")
        self.assertEqual(report1["status"], "ready_static_table")
        self.assertEqual(report1["runtime_binding"]["connected"], False)
        self.assertEqual(report1["table_version"], "openbor-level-event-table/1")
        self.assertEqual(report1["event_count"], 3)
        self.assertEqual(source1, source2)
        self.assertEqual(report1, report2)
        self.assertIn("-20, 180, 45", source1)
        self.assertIn("OB_LEVEL_EVENT_HAS_COORDS | OB_LEVEL_EVENT_HAS_HEALTH", source1)
        self.assertIn("OB_LEVEL_EVENT_GROUP, OB_LEVEL_ENTITY_UNRESOLVED", source1)
        self.assertIn("100u, 4u", source1)
        self.assertIn('"Book"', source1)
        self.assertIn('"Grunt"', source1)
        header = render_level_event_header(report1)
        self.assertIn("extern const ObLevelEvent fixture_events[];", header)
        self.assertIn("extern const char fixture_events_reference_commit[];", header)

    def test_unknown_directive_and_queue_mismatch_fail_closed(self):
        event = {
            "kind": "spawn", "line": 4, "name": "Grunt", "at": 0,
            "directives": [{"command": "spawnscript", "args": ["dynamic"]}],
        }
        preflight = _preflight([event])
        source, report = compile_level_event_table(preflight)
        self.assertIsNone(source)
        self.assertEqual(report["status"], "blocked")
        self.assertIn("event_0_unsupported_directive:spawnscript", report["diagnostics"])

        preflight = _preflight([event])
        preflight["spawn_queue"][0]["line"] = 5
        source, report = compile_level_event_table(preflight)
        self.assertIsNone(source)
        self.assertIn("event_0_typed_record_mismatch", report["diagnostics"])

    def test_rejects_invalid_alias_and_missing_source_identity(self):
        event = {"kind": "spawn", "line": 4, "name": "Grunt\nBAD", "at": 0, "directives": []}
        preflight = _preflight([event])
        preflight["source"]["pak_sha256"] = "short"
        source, report = compile_level_event_table(preflight)
        self.assertIsNone(source)
        self.assertIn("source_pak_sha256_invalid", report["diagnostics"])
        self.assertTrue(any("control character" in item for item in report["diagnostics"]))

    def test_preflight_blocker_cannot_be_hidden_by_table_lowering(self):
        event = {"kind": "spawn", "line": 4, "name": "Grunt", "at": 0, "directives": []}
        preflight = _preflight([event])
        preflight["blockers"].append("level_spawn_scripts_not_analyzed")
        source, report = compile_level_event_table(preflight)
        self.assertIsNone(source)
        self.assertIn("preflight_has_unresolved_blockers", report["diagnostics"])

    def test_model_type_from_event_queue_must_match_resolved_registry(self):
        event = {"kind": "spawn", "line": 4, "name": "Grunt", "at": 0, "directives": []}
        preflight = _preflight([event])
        preflight["spawn_queue"][0]["model_type"] = "item"
        source, report = compile_level_event_table(preflight)
        self.assertIsNone(source)
        self.assertIn("event_0_spawn_model_registry_mismatch", report["diagnostics"])


if __name__ == "__main__":
    unittest.main()
