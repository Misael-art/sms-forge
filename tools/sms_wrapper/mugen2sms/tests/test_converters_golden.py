"""S4 golden tests: saida de tiles/clsn/cmd/gerador com bytes exatos conhecidos."""
from __future__ import annotations

import re
import struct

from mugen2sms.converters.sms_tiles import to_sms_pose
from mugen2sms.converters.sms_clsn import to_clsn_tables
from mugen2sms.converters.sms_cmd import to_patterns
from mugen2sms.parsers import air, sff, cmd as cmdmod


def sprite(w, h, pixels, palette=None):
    return sff.Sprite(1, 0, 0, 0, w, h, pixels, palette or [(0, 0, 0)] * 256, False, None, 0)


RED = (255, 0, 0)
GREEN = (0, 255, 0)
PAL = [(0, 0, 0), RED, GREEN] + [(255, 255, 255)] * 253


def test_solid_tile_encodes_4planes_msb():
    # 8x8 inteiro na cor 1 (vermelho) -> plano0=0xFF, planos 1-3 zerados por linha
    sp = sprite(8, 8, bytes([1] * 64), PAL)
    pose = to_sms_pose(sp)
    assert pose.tiles == [bytes([0xFF, 0, 0, 0] * 8)]
    assert len(pose.tiles[0]) == 32
    assert pose.unique_tiles == 1 and pose.flips_used == 0


def test_checkerboard_dedups_with_flips():
    # 16x8: tile direito e o espelho H do esquerdo -> 1 tile unico + 1 flip
    row = bytes([1] * 4 + [2] * 4 + [2] * 4 + [1] * 4)
    sp = sprite(16, 8, row * 8, PAL)
    pose = to_sms_pose(sp)
    assert pose.unique_tiles == 1
    assert pose.flips_used == 1
    assert [p.hflip for p in pose.placements] == [False, True]


def test_palette_word_is_header_rgb_macro():
    # SMSlib.h: RGB(r,g,b) = r | g<<2 | b<<4 com canais 0..3
    sp = sprite(8, 8, bytes([1] * 64), PAL)
    pose = to_sms_pose(sp)
    assert pose.palette[1] == 3                 # vermelho puro -> (3,0,0) -> 0b000011
    assert pose.palette[0] == 0                 # indice 0 transparente


def test_edge_padded_with_transparent():
    sp = sprite(9, 1, bytes([1] * 9), PAL)          # 9 px: tile0 cheio, tile1 = 1 px + 7 transparentes
    pose = to_sms_pose(sp)
    # canone lexicografico entre os 4 flips: a linha visivel vira a ULTIMA (vflip),
    # e as duas posicoes apontam para os tiles deduplicados com flags de flip
    assert pose.tiles[0][-4:] == bytes([0xFF, 0, 0, 0])
    assert pose.tiles[1][-4:] == bytes([0x01, 0, 0, 0])   # canone lexicografico poe o px em x7 com flips
    assert all(p.vflip for p in pose.placements)


def test_clsn_tables_are_flat_int16():
    action = air.Action(0, [air.Frame(1, 0, 0, 0, 1, clsn1=[(0, -14, 12, -8)], clsn2=[(-8, -16, 8, 0)])])
    tables = to_clsn_tables({0: action})
    hit, hurt = tables[0][0]                           # anim 0, frame 0
    assert hit == [0, -14, 12, -8]
    assert hurt == [-8, -16, 8, 0]
    struct.pack("<4h", *hit)                    # coube em int16


def test_cmd_patterns_map_four_way_direction_modifier():
    def command(name, keys, hold=False):
        return cmdmod.Command(name, [cmdmod.Step([cmdmod.Key(k, hold=hold) for k in keys])], 1, 0, 1, name)
    patterns, skipped = to_patterns([
        command("punch", ["a"]),
        command("holdF", ["F"], hold=True),
        command("diag", ["DF"]),
        cmdmod.Command("loose", [cmdmod.Step([cmdmod.Key("F", four_way=True)])], 1, 0, 1, "loose"),
        command("kick", ["b"]),
        command("charge", ["B"]),
    ])
    assert {p.name for p in patterns} == {"punch", "holdF", "charge", "diag", "loose"}
    # Diagonal e uniao de duas direcoes; `$F` conserva a direcao flexivel no blob.
    assert next(p for p in patterns if p.name == "diag").steps[0].dir == 0x0A      # D|F
    assert skipped == {"kick": "botao>pad"}
    punch = next(p for p in patterns if p.name == "punch")
    assert punch.steps[0].keys == 0x01                    # A
    holdf = next(p for p in patterns if p.name == "holdF")
    assert holdf.steps[0].dir == 0x08                     # R (F mapeia p/ direita-para-frente no runtime)
    assert holdf.steps[0].hold is True
    assert next(p for p in patterns if p.name == "loose").steps[0].four_way is True


def test_define_size_matches_array_len():
    from mugen2sms.generators.smsdev import Artifact, render_header
    hdr = render_header([Artifact("FOO_TILES", b"\x01\x02\x03", "sff")], "foo")
    size = re.search(r"#define FOO_TILES_SIZE (\d+)", hdr).group(1)
    decl = re.search(r"const unsigned char FOO_TILES\[(\d+)\]", hdr).group(1)
    n = hdr.split("FOO_TILES[3]")[1].count("0x")
    assert size == decl == str(n) == "3"


def test_generate_synthetic_character_roundtrip(tmp_path):
    from mugen2sms.analysis.fidelity import classify_character
    from mugen2sms.analysis.sms_budget import SmsLimits
    from mugen2sms.character import load
    from mugen2sms.generators.smsdev import generate
    from mugen2sms.source import Source
    from mugen2sms.tests.make_fixtures import build
    root = build(tmp_path / "mini")
    ch = load(Source(root))
    fid = classify_character(ch, SmsLimits())
    man = generate(ch, fid, tmp_path / "gen")
    assert man.entries and man.stats["bytes"] > 0
    hdr = (tmp_path / "gen" / "mini_art.h").read_text(encoding="ascii")
    for e in man.entries:
        assert f"#define {e['symbol']}_SIZE {e['size_bytes']}" in hdr
        assert f"const unsigned char {e['symbol']}[{e['size_bytes']}]" in hdr
    import json
    m = json.loads((tmp_path / "gen" / "mini_manifest.json").read_text())
    assert m["generated_sha256"] == man.generated_sha256


def test_synthetic_cut_passes_scanline_gate(tmp_path):
    """Gate do harness sobre saida gerada commitavel: cena pior-frame do mini passa."""
    import json
    import audit_sprite_line_sim as sim
    from mugen2sms.analysis.fidelity import classify_character
    from mugen2sms.analysis.sms_budget import SmsLimits
    from mugen2sms.character import load
    from mugen2sms.generators.smsdev import _worst_scene, generate
    from mugen2sms.source import Source
    from mugen2sms.tests.make_fixtures import build
    ch = load(Source(build(tmp_path / "mini")))
    fid = classify_character(ch, SmsLimits())
    man = generate(ch, fid, tmp_path / "gen")
    scene = _worst_scene(ch, fid)
    assert scene is not None
    report = sim.simulate(scene)
    assert report["violations"] == [], report
    assert report["peak_per_line"] <= 8


def _load_mini(tmp_path):
    from mugen2sms.analysis.fidelity import classify_character
    from mugen2sms.analysis.sms_budget import SmsLimits
    from mugen2sms.character import load
    from mugen2sms.source import Source
    from mugen2sms.tests.make_fixtures import build
    ch = load(Source(build(tmp_path / "mini")))
    return ch, classify_character(ch, SmsLimits())


def test_generate_banked_tiles(tmp_path):
    """banked=True: TILES viram (BANK,OFF,SIZE) + bin 16 KB; resto inline."""
    import json
    from mugen2sms.generators.smsdev import generate
    ch, fid = _load_mini(tmp_path)
    man = generate(ch, fid, tmp_path / "gen", banked=True)
    hdr = (tmp_path / "gen" / "mini_art.h").read_text(encoding="ascii")
    binp = (tmp_path / "gen" / "mini_bank2.bin").read_bytes()
    assert len(binp) == 16384, "bin de banco e pagina de 16 KB exata"
    tiles = [e for e in man.entries if e["symbol"].endswith("_TILES")]
    others = [e for e in man.entries if not e["symbol"].endswith("_TILES")]
    assert tiles and others
    for e in tiles:
        sym = e["symbol"]
        assert e["bank"] == 2 and e["off"] % 32 == 0
        assert f"#define {sym}_BANK 2" in hdr
        assert f"#define {sym}_OFF {e['off']}" in hdr
        assert f"#define {sym}_SIZE {e['size_bytes']}" in hdr
        assert f"const unsigned char {sym}[" not in hdr
        assert binp[e["off"]:e["off"] + e["size_bytes"]] == e["blob"]
    for e in others:
        assert "bank" not in e
        assert f"const unsigned char {e['symbol']}[{e['size_bytes']}]" in hdr
    m = json.loads((tmp_path / "gen" / "mini_manifest.json").read_text())
    assert [x["symbol"] for x in m["entries"]] == [e["symbol"] for e in man.entries]
    assert all("blob" not in x for x in m["entries"]), "manifest nao duplica bytes"


def test_generate_banked_offsets_match_inline_blobs(tmp_path):
    """O bin bancado e a concatenacao deterministica dos mesmos blobs do modo inline."""
    from mugen2sms.generators.smsdev import generate
    ch, fid = _load_mini(tmp_path)
    lin = generate(ch, fid, tmp_path / "lin")
    banked = generate(ch, fid, tmp_path / "bnk", banked=True)
    inline = {e["symbol"]: e["blob"] for e in lin.entries
              if e["symbol"].endswith("_TILES")}
    binp = (tmp_path / "bnk" / "mini_bank2.bin").read_bytes()
    for e in banked.entries:
        if e["symbol"].endswith("_TILES"):
            assert binp[e["off"]:e["off"] + e["size_bytes"]] == inline[e["symbol"]]


def test_generate_banked_overflow_exits(tmp_path, monkeypatch):
    """Estouro da pagina de 16 KB e FAIL ruidoso, nunca truncamento silencioso."""
    import pytest
    from mugen2sms.generators import smsdev
    ch, fid = _load_mini(tmp_path)
    monkeypatch.setattr(smsdev, "BANK_PAGE", 128)
    with pytest.raises(SystemExit) as e:
        smsdev.generate(ch, fid, tmp_path / "ovf", banked=True)
    assert "bank" in str(e.value).lower() or "banco" in str(e.value).lower()
