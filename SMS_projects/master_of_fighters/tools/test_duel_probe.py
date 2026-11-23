"""Host checks for the GD05 probe serializer and decoder."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from duel_probe import RECORD_BYTES, decode


PROJECT = Path(__file__).resolve().parents[1]
FIXTURE = """
#include <stdio.h>
#include "duel_probe.h"
int main(int argc, char **argv)
{
    uint8_t record[MOF_DUEL_PROBE_BYTES] = {0};
    MofDuelProbeActor actors[2] = {0};
    FILE *file;
    if (argc != 2) return 1;
    actors[0].fighter = 3;
    actors[0].keys = 0x14;
    actors[0].state = 9;
    actors[0].action_tick = 11;
    actors[0].pose_requested = 4;
    actors[0].pose_resident = 3;
    actors[0].pose_presented = 2;
    actors[0].tested_pose = 5;
    actors[0].contact = 1;
    actors[0].life = 100;
    actors[0].flags = MOF_DUEL_PROBE_FACES_RIGHT | MOF_DUEL_PROBE_HAS_ATTACK;
    actors[0].pivot_x = 9;
    actors[0].pivot_y = 144;
    actors[0].attack = (MofDuelProbeBox){-4, 30, 17, 40};
    actors[1].fighter = 7;
    actors[1].keys = 8;
    actors[1].flags = MOF_DUEL_PROBE_CAN_ACT | MOF_DUEL_PROBE_HAS_HURT;
    actors[1].life = 88;
    actors[1].free_since = 0xF013u;
    actors[1].hurt = (MofDuelProbeBox){20, 30, 45, 50};
    record[4] = 254;
    mof_duel_probe_publish(record, 0xF015u, actors);
    file = fopen(argv[1], "wb");
    if (!file) return 2;
    if (fwrite(record, 1, sizeof(record), file) != sizeof(record)) return 3;
    return fclose(file) != 0;
}
"""


class ProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("gcc") or shutil.which("cc")
        if compiler is None:
            raise RuntimeError("A native C compiler is required to verify the wire format")
        staging = PROJECT / "out"
        staging.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="duel-probe-", dir=staging) as tmp:
            root = Path(tmp)
            source = root / "probe.c"
            binary = root / "fixture.exe"
            snapshot = root / "capture.bin"
            source.write_text(FIXTURE, encoding="ascii")
            subprocess.run(
                [compiler, "-std=c99", "-Wall", "-Wextra", "-Werror",
                 "-I", str(PROJECT / "inc"), str(source), "-o", str(binary)],
                check=True,
            )
            subprocess.run([str(binary), str(snapshot)], check=True)
            cls.record = snapshot.read_bytes()

    def test_real_c_bytes_keep_logic_and_presentation_distinct(self):
        self.assertEqual(len(self.record), 74)
        observed = decode(self.record)
        self.assertEqual(observed["stamp"], 0)
        self.assertEqual(observed["logic_tick"], 0xF015)
        p1, p2 = observed["p1"], observed["p2"]
        self.assertEqual([p1[key] for key in ("pose_requested", "pose_resident", "pose_presented")], [4, 3, 2])
        self.assertEqual(p1["pose_used_for_contact"], 5)
        self.assertEqual((p1["fighter"], p1["keys_consumed"], p1["contact"]), (3, 0x14, 1))
        self.assertEqual(p1["boxes"]["attack"]["left"], -4)
        self.assertIsNone(p1["boxes"]["hurt"])
        self.assertEqual((p2["fighter"], p2["keys_consumed"], p2["life"], p2["free_since"]),
                         (7, 8, 88, 0xF013))
        self.assertTrue(p2["can_act"])
        self.assertFalse(p2["facing_right"])

    def test_rejects_incomplete_and_unpublished_records(self):
        self.assertEqual(RECORD_BYTES, 74)
        for invalid in (self.record[:-1], bytes(RECORD_BYTES),
                        self.record[:4] + b"\x01" + self.record[5:]):
            with self.subTest(length=len(invalid)):
                with self.assertRaises(ValueError):
                    decode(invalid)

    def test_rejects_inverted_attack_box(self):
        modified = bytearray(self.record)
        modified[22:24] = (17).to_bytes(2, "little")
        with self.assertRaisesRegex(ValueError, "attack box"):
            decode(modified)


if __name__ == "__main__":
    unittest.main()
