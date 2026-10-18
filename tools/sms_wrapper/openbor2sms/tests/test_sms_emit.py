"""Testes focados dos helpers O3 de sms_emit (a emissao integral e conferida por gates)."""
import unittest

from openbor2sms import sms_emit as se


class RowModelTest(unittest.TestCase):
    def test_contagem_por_linha(self):
        cells = [{"row": 4, "col": c, "dens": 1} for c in range(9)]
        self.assertEqual(se.o3_row_counts(cells), {4: 9})

    def test_sobreposicao_visivel(self):
        rows = list(range(3))
        self.assertEqual(se.o3_overlap_rows(1, -80, -72, 152, 152, rows),
                         [1, 2])
        self.assertEqual(se.o3_overlap_rows(0, -80, -72, 152, 152, rows),
                         [0, 1])
        self.assertEqual(se.o3_overlap_rows(3, -80, -72, 152, 152, rows), [])

    def test_sobreposicao_fora_da_tela(self):
        # topo < 1 nao desenha; topo >= 192 desenha mas nao conta
        self.assertEqual(se.o3_overlap_rows(0, -80, -72, 60, 60, [0]), [])
        self.assertEqual(se.o3_overlap_rows(7, -80, -72, 152, 152, [0]), [])

    def test_solo_9_em_linha_derruba_uma(self):
        line = [{"row": 4, "col": c, "dens": 9 - c} for c in range(9)]
        ec, drops, peak = se.o3_compose_rows({}, line, -80, -72, 152, 152)
        self.assertEqual(len(drops), 1)
        self.assertEqual(drops[0]["col"], 8)
        self.assertEqual(ec, {4: 8})
        self.assertEqual(peak, se.O3_PER_LINE)

    def test_jogador_sobreposto_derruba_inimigo(self):
        ax_row = {2: 8}
        enemy = [{"row": 1, "col": 0, "dens": 5}]
        _ec, drops, peak = se.o3_compose_rows(ax_row, enemy, -80, -72,
                                              152, 152)
        self.assertEqual(len(drops), 1)
        self.assertEqual(peak, 8)

    def test_jogador_sem_sobreposicao_nao_derruba(self):
        ax_row = {0: 8}
        enemy = [{"row": 1, "col": 0, "dens": 5}]
        _ec, drops, peak = se.o3_compose_rows(ax_row, enemy, -80, -72,
                                              152, 152)
        self.assertEqual(drops, [])
        self.assertEqual(peak, 8)

    def test_invisivel_e_fora_da_linha_visivel(self):
        low = [{"row": 0, "col": 0, "dens": 5}]
        ec, _drops, _peak = se.o3_compose_rows({}, low, -80, -72, 60, 60)
        self.assertEqual(ec, {})
        high = [{"row": 7, "col": c, "dens": 1} for c in range(9)]
        ec, drops, peak = se.o3_compose_rows({}, high, -80, -72, 152, 152)
        self.assertEqual(len(ec), 1)
        self.assertEqual(drops, [])
        self.assertEqual(peak, 0)

    def test_brute_force_concorda_com_a_politica(self):
        line = [{"row": 4, "col": c, "dens": 9 - c} for c in range(9)]
        cases, bad = se.o3_policy_crosscheck([
            ({}, line, -80, -72, 152, 152),
            ({2: 8}, [{"row": 1, "col": 0, "dens": 5}], -80, -72, 152, 152),
            ({1: 5, 2: 5, 3: 5}, [{"row": i % 6, "col": i, "dens": 1}
                                  for i in range(7)], -80, -72, 176, 152)])
        self.assertEqual(cases, 3)
        self.assertEqual(bad, 0)


class ArcSimTest(unittest.TestCase):
    def test_pulo_d5(self):
        y, x, _t = se.o3_sim_arc(3.3, 1.0)
        self.assertEqual(y[0], 0)
        self.assertEqual(len(y) - 1, 40)
        self.assertGreaterEqual(max(y), 53)
        self.assertLessEqual(max(y), 56)
        self.assertGreaterEqual(x[-1], 64)
        self.assertLessEqual(x[-1], 68)

    def test_arremesso_d5(self):
        y, x, _t = se.o3_sim_arc(3.0, 1.2)
        self.assertEqual(len(y) - 1, 36)
        self.assertGreaterEqual(max(y), 44)
        self.assertLessEqual(max(y), 47)
        self.assertGreaterEqual(x[-1], 70)
        self.assertLessEqual(x[-1], 74)

    def test_entrada_do_spawn(self):
        y, _t = se.o3_sim_fall(200)
        self.assertEqual(y[0], 200)
        self.assertEqual(y[-1], 0)
        self.assertGreaterEqual(len(y) - 1, 36)
        self.assertLessEqual(len(y) - 1, 40)


class PolicyTest(unittest.TestCase):
    def test_prioridade_esparsa_cai_primeiro(self):
        cells = [{"row": 0, "col": 0, "dens": 9},
                 {"row": 0, "col": 1, "dens": 3},
                 {"row": 0, "col": 2, "dens": 7}]
        order = se.o3_priority_order(cells)
        self.assertEqual([c["dens"] for c in order], [9, 7, 3])


class BlocksTest(unittest.TestCase):
    def test_bloco_de_uma_celula(self):
        rows16 = [bytes([1] * 8) for _ in range(8)] + [bytes([8]) * 8 for _ in range(8)]
        blob = se.o3_blocks_for_cells([{"rows16": rows16}])
        self.assertEqual(len(blob), 64)
        self.assertEqual(blob[0], 0xFF)
        self.assertEqual(blob[32], 0)
        self.assertEqual(blob[35], 0xFF)

    def test_pack_sequencial_nos_bancos(self):
        m = se.o3_pack_banks([1856] * 40)
        self.assertEqual(len(m), 40)
        self.assertEqual(m[0], (se.O3_BANK_FIRST, 0))
        self.assertEqual(m[-1][0], se.O3_BANK_FIRST + se.O3_BANK_COUNT - 1)

    def test_pack_reprova_estouro(self):
        with self.assertRaises(SystemExit):
            se.o3_pack_banks([se.O3_BANK_BYTES + 1])
        with self.assertRaises(SystemExit):
            se.o3_pack_banks([se.O3_BANK_BYTES] * (se.O3_BANK_COUNT + 1))


class PosePackingTest(unittest.TestCase):
    def test_dx_dy_slot(self):
        canvas = {"ax": {"dx0": -32, "dy0": -80}}
        cells = [{"row": 1, "col": 2, "dens": 5, "rows16": []}]
        packed = se._o3_pose_cells(cells, canvas, "ax", lambda cs: cs)
        self.assertEqual(packed[0]["dx"], -32 + 16)
        self.assertEqual(packed[0]["dy"], -80 + 16)
        self.assertEqual(packed[0]["slot"], 0)


class AnimHeaderTest(unittest.TestCase):
    """Regressao: o inicializador de o3_*_anims ja saiu com chaves erradas
    (2o elemento em diante sem '{'), inviabilizando o build. O teste compila
    o header emitido com um C compiler de host."""

    PLAN = {
        "ax": [
            {"id": 0, "name": "idle", "frames": [[0, 5]], "loop": 1, "land": 255},
            {"id": 1, "name": "walk", "frames": [[1, 7], [2, 7]], "loop": 1, "land": 255},
            {"id": 2, "name": "fall2", "frames": [[3, 255], [4, 5]], "loop": 0, "land": 1},
        ],
        "long": [
            {"id": 0, "name": "idle", "frames": [[0, 5]], "loop": 1, "land": 255},
            {"id": 1, "name": "death", "frames": [[1, 5], [2, 1]], "loop": 1, "land": 255},
        ],
    }
    ATTACKS = {
        "ax": {"rel": [0, -62, 44, 62], "damage": 7, "pause": 15, "depth": 15,
               "first": 1, "last": 3},
        "long": {"rel": [0, -46, 40, 46], "damage": 5, "pause": 10, "depth": 15,
                 "first": 1, "last": 2},
    }

    def test_header_anim_compila_no_host(self):
        import os
        import shutil
        import subprocess
        import tempfile
        gcc = shutil.which("gcc")
        if not gcc:
            self.skipTest("gcc ausente no host")
        text = se._o3_header_anim(self.PLAN, self.ATTACKS)
        src = (text + "\n"
               "int main(void){return (int)(o3_ax_anims[0].count"
               " + o3_ax_anims[2].land + o3_long_anims[1].frames[1].delay"
               " + o3_ax_attack.dmg + o3_long_attack.last);}\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "anim.c")
            with open(path, "w") as fh:
                fh.write(src)
            r = subprocess.run([gcc, "-fsyntax-only", path],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)

    def test_header_anim_contagens(self):
        text = se._o3_header_anim(self.PLAN, self.ATTACKS)
        self.assertIn("o3_ax_anims[3]", text)
        self.assertIn("o3_long_anims[2]", text)


class RecordPathTest(unittest.TestCase):
    def test_sufixo_de_revisao_nao_sobrescreve(self):
        from pathlib import Path
        base = Path("/proj")
        self.assertEqual(se.o3_record_path(base, "20261017").name,
                         "o3_emission_20261017.json")
        self.assertEqual(se.o3_record_path(base, "20261017", "_r2").name,
                         "o3_emission_20261017_r2.json")


if __name__ == "__main__":
    unittest.main()
