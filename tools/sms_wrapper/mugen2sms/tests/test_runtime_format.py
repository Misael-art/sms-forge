"""S4.5b — formato de runtime SMS: metasprite 3B (dx,dy,tile + 0x80, provado em ROM
por MSSF2T fight.c:1095-1129), tiles TALL 8x16 pareados com espelho como OUTRO padrao
(SMS nao tem flip de sprite), P2 por shift de indice na MESMA sprite palette.

Expectativas calculadas a mao sobre o formato de `sms_tiles._encode_tile`:
linha de tile = 4 bytes (planos 0..3), bit 7 = pixel 0; espelho H = inverter bits
de cada byte (0x00,0x01,0x02,0x03 -> 0x00,0x80,0x40,0xC0).
"""
from __future__ import annotations

from mugen2sms.converters.sms_tiles import Pose, Placement
from mugen2sms.generators import runtime_format as rf


def _mini_pose():
    # 8x16 = 1 coluna x 1 par TALL: topo = tile 1 (range(32)), base = tile 0 (zeros)
    return Pose(width=8, height=16, tiles=[bytes(32), bytes(range(32))],
                placements=[Placement(1, False, False, 0, 0),
                            Placement(0, False, False, 0, 8)],
                palette=[0] * 16, unique_tiles=2, flips_used=0)


def _pose_2rows():
    # 8x32 = 2 pares TALL de mesmo conteudo (zeros) -> pool com 1 entrada
    return Pose(width=8, height=32, tiles=[bytes(32)],
                placements=[Placement(0, False, False, 0, y) for y in (0, 8, 16, 24)],
                palette=[0] * 16, unique_tiles=1, flips_used=0)


def test_pack_pareia_tall_e_espelho_e_outro_padrao():
    blob, mirrors = rf.pack_tiles_tall(_mini_pose())
    assert blob[:64] == bytes(range(32)) + bytes(32)          # par normal: topo+base
    m = mirrors[0]
    assert m != 0
    assert blob[m * 64:m * 64 + 4] == bytes([0x00, 0x80, 0x40, 0xC0])   # linha 0 espelhada
    assert blob[m * 64 + 32:m * 64 + 64] == bytes(32)         # base em branco nao muda
    assert len(blob) == 128


def test_dedup_por_conteudo_do_par():
    blob, mirrors = rf.pack_tiles_tall(_pose_2rows())
    assert len(blob) == 64                                    # 1 par unico, espelho = ele mesmo
    assert mirrors == {0: 0}


def test_triples_origem_topo_convencao_mssf2t():
    # convencao provada em ROM (ken_idle_meta): dy = linha*16 para baixo, origem no topo
    b = rf.build_frames(_pose_2rows(), tile_base=0x20)
    assert b == bytes([0x00, 0x00, 0x20,               # linha de cima
                       0x00, 0x10, 0x20,               # linha de baixo: dy=16
                       0x80])


def test_facing_esquerda_troca_tile_pelo_espelho():
    assert rf.build_frames(_mini_pose(), tile_base=0x20) == bytes([0, 0, 0x20, 0x80])
    assert rf.build_frames(_mini_pose(), tile_base=0x20, facing=1) == bytes([0, 0, 0x22, 0x80])


def test_omite_par_tall_completamente_transparente():
    assert rf.build_frames(_pose_2rows(), omit_blank_cells=True) == bytes([0x80])
    assert rf.build_frames(_mini_pose(), omit_blank_cells=True) == bytes([0, 0, 0, 0x80])


def test_facing_inverte_ordem_das_colunas():
    # MSSF2T: dx' = lo+hi-dx -> coluna tx vira (tw-1-tx)*8
    pose = Pose(width=16, height=16, tiles=[bytes(32), bytes(range(32))],
                placements=[Placement(1, False, False, 0, 0), Placement(0, False, False, 8, 0),
                            Placement(0, False, False, 0, 8), Placement(0, False, False, 8, 8)],
                palette=[0] * 16, unique_tiles=2, flips_used=0)
    r = rf.build_frames(pose, tile_base=0x00, facing=0)
    l = rf.build_frames(pose, tile_base=0x00, facing=1)
    assert r[0:3] == bytes([0x00, 0x00, r[2]])                # tx=0 abre na R
    assert l[0:3] == bytes([0x08, 0x00, l[2]])                # e na L
    assert l[2] != r[2]                                       # e usa o padrao espelhado


def test_shift_palette_indices_preserva_transparencia():
    # linha 0 = planos (0x00,0x01,0x02,0x03): x=6 idx 12 na pos 6, x=7 idx 10 na pos 7
    tile = bytes([0x00, 0x01, 0x02, 0x03]) + bytes(28)
    assert rf.decode_indices(tile)[:16] == [0] * 6 + [12, 10] + [0] * 8
    shifted = rf.shift_palette_indices(tile, 1)
    assert rf.decode_indices(shifted)[:16] == [0] * 6 + [13, 11] + [0] * 8
    assert rf.shift_palette_indices(tile, 0) == tile
    assert set(rf.decode_indices(shifted)[16:]) == {0}        # resto do tile intocado
