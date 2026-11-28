"""Focused tests for the standing-normal round evidence."""
import unittest

from record_duel_repertoire import observe_normal


def sample(tick, life, *, contact=0, state=1, action_tick=0, requested=7, local=None):
    return {"logic_tick": tick, "frame": tick + 50, "p2": {"life": life},
            "p1": {"state": state, "action_tick": action_tick, "contact": contact,
                   "pose_used_for_contact": requested - 6 if local is None else local,
                   "pose_requested": requested, "pose_resident": requested, "pose_presented": 7}}


class RoundEvidenceTests(unittest.TestCase):
    def test_hit_and_late_picture_are_both_preserved(self):
        result = observe_normal([sample(20, 100), sample(21, 94, contact=1,
                                action_tick=1, requested=8)], 0, 0, 100)
        self.assertEqual((result["hit_tick"], result["hit_vdp_frame"],
                          result["opponent_life_before"], result["opponent_life"],
                          result["local_pose_at_hit"], result["requested_at_hit"],
                          result["resident_at_hit"], result["presented_at_hit"]),
                         (21, 71, 100, 94, 2, 8, 8, 7))

    def test_alis_on_port_one_uses_her_pose_ids(self):
        result = observe_normal([sample(20, 100, requested=17),
                                 sample(21, 90, contact=1, action_tick=5, requested=18, local=2)],
                                0, 1, 100, fighter=1)
        self.assertEqual((result["player"], result["first_pose"], result["requested_at_hit"]),
                         ("p1", 17, 18))

    def test_ambiguous_or_unpaid_hit_is_rejected(self):
        start = sample(20, 100)
        hit = sample(21, 94, contact=1, action_tick=1)
        for rows in ([start], [start, sample(21, 94, action_tick=1)],
                     [start, sample(21, 100, contact=1, action_tick=1)],
                     [start, hit, sample(22, 88, contact=1, action_tick=2)],
                     [start, sample(21, 94, contact=1, action_tick=1, requested=8, local=1)],
                     [sample(19, 94, contact=1, state=0), sample(20, 94)]):
            with self.subTest(rows=rows), self.assertRaises(RuntimeError):
                observe_normal(rows, 0, 0, 100)


if __name__ == "__main__":
    unittest.main()
