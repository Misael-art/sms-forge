"""Testes focados dos helpers O3 de sms_art (a conversao integral e conferida por gates)."""
import unittest

from openbor2sms import sms_art


class OccupiedCellsTest(unittest.TestCase):
    def test_uma_celula_8x16_opaca(self):
        grid = [bytes([1] * 8) for _ in range(16)]
        self.assertEqual(sms_art.occupied_cells(grid), 1)

    def test_duas_celulas_empilhadas(self):
        grid = [bytes([1] * 8) for _ in range(32)]
        self.assertEqual(sms_art.occupied_cells(grid), 2)

    def test_transparente_nao_conta(self):
        grid = [bytes([0] * 8) for _ in range(32)]
        self.assertEqual(sms_art.occupied_cells(grid), 0)

    def test_celulas_na_mesma_banda_somam_uma(self):
        grid = [bytes([0] * 8) for _ in range(16)]
        grid[3] = bytes([1, 0, 0, 0, 0, 0, 0, 0])
        grid[5] = bytes([0, 1, 0, 0, 0, 0, 0, 0])
        self.assertEqual(sms_art.occupied_cells(grid), 1)  # mesma celula 8x16


class PaletteFitTest(unittest.TestCase):
    def test_cores_exatas_erro_zero(self):
        stats, mapping = sms_art.palette_fit({(0, 0, 0): 4, (255, 255, 255): 3},
                                             [(0, 0, 0), (255, 255, 255)])
        self.assertEqual(stats["err_rms_channel"], 0.0)
        self.assertEqual(stats["err_mean_abs_channel"], 0.0)
        self.assertEqual(stats["source_colors"], 2)
        self.assertEqual(mapping["(0, 0, 0)"], [[0, 0, 0], 0])

    def test_quantizacao_aproxima(self):
        stats, mapping = sms_art.palette_fit({(250, 250, 250): 1},
                                             [(0, 0, 0), (255, 255, 255)])
        self.assertEqual(mapping["(250, 250, 250)"][1], 1)
        self.assertGreater(stats["err_rms_channel"], 0.0)


class FrameGridTest(unittest.TestCase):
    key = (0, 253, 255)

    def test_janela_do_canvas_e_transparencia(self):
        rows = [[self.key] * 8 for _ in range(8)]
        rows[5][5] = (0, 0, 0)
        grid = sms_art.frame_grid(rows, self.key, 0, 0, 8, 16, 4, 4, [(0, 0, 0)], {})
        self.assertEqual(len(grid), 16)
        self.assertEqual(sum(sum(1 for v in r if v) for r in grid), 1)
        self.assertEqual(grid[1][1], 1)

    def test_fora_do_quadro_e_transparente(self):
        rows = [[self.key] * 8 for _ in range(8)]
        grid = sms_art.frame_grid(rows, self.key, 0, 0, 8, 8, 0, 0, [(0, 0, 0)], {})
        self.assertEqual(sum(sum(1 for v in r if v) for r in grid), 0)


if __name__ == "__main__":
    unittest.main()
