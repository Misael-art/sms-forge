"""Header de padroes de comando para a ROM (doc/23, secao 6.B).

O blob `_CMD_` que o anel le (`integrada/src/input.c`) precisa do formato
versionado com tier. Este gerador e a unica fonte desses bytes: ele le os
`.cmd` reais dos dois personagens pelos conversores do pipeline e escreve
simbolos estaveis `P<slot>_CMD_<alias>` — assim o C nao depende do slug de
nenhum personagem e trocar de elenco nao troca uma linha de fight.c.

Negativo do handoff coberto aqui: forte e fraco NAO podem ser o mesmo blob
(a variante que ignora o tier tem que reprovar depois).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mugen2sms.generators import cmd_patterns                                # noqa: E402
from mugen2sms.inventory import sha256_file                                  # noqa: E402

CORPUS = Path("/mnt/sdcard/Projects/Mugenesis/Base de Estudo/chars/street-fighter")
KEN = CORPUS / "ken_masters_adv.zip"
RYU = CORPUS / "ryu_kang.zip"
DATA = ROOT / "SMS_projects" / "luta_mugen" / "data"
KEN_CFG = DATA / "ken_scale_pilot_80px.json"
RYU_CFG = DATA / "ryu_scale_pilot_80px.json"

pytestmark = pytest.mark.skipif(not (KEN.exists() and RYU.exists()),
                                reason=f"acervo local ausente: {CORPUS}")

ARRAY = re.compile(r"const unsigned char (\w+)\[(\d+)\] = \{(.*?)\};", re.S)


def _arrays(text: str) -> dict[str, bytes]:
    out = {}
    for name, size, body in ARRAY.findall(text):
        data = bytes(int(v, 0) for v in re.findall(r"0x[0-9A-Fa-f]+|\d+", body))
        assert len(data) == int(size), f"{name}: SIZE diz {size}, tem {len(data)}"
        out[name] = data
    return out


def _generate(tmp_path: Path, ken_cfg: Path = KEN_CFG,
              ryu_cfg: Path = RYU_CFG) -> tuple[str, dict]:
    header = tmp_path / "attack_cmds.h"
    report = tmp_path / "attack_cmds.json"
    rc = cmd_patterns.main([
        "--p1-source", str(KEN), "--p1-config", str(ken_cfg),
        "--p2-source", str(RYU), "--p2-config", str(ryu_cfg),
        "--out-header", str(header), "--out-report", str(report)])
    assert rc == 0
    return header.read_text(encoding="utf-8"), json.loads(report.read_text(encoding="utf-8"))


def test_quatro_golpes_de_cada_lado_sao_emitidos_no_formato_versionado(tmp_path):
    text, _ = _generate(tmp_path)
    arrays = _arrays(text)
    for slot in (0, 1):
        for alias in ("LP", "HP", "LK", "HK"):
            blob = arrays[f"P{slot}_CMD_{alias}"]
            assert blob[0] == cmd_patterns.BLOB_FMT_VERSION, alias
            assert blob[1] == 1, f"P{slot}_{alias}: esperado um passo"


def test_fraco_e_forte_sao_bytes_diferentes_na_mesma_familia(tmp_path):
    """O contrato anti 'forte == fraco': o campo de tier (bits 2-3) decide."""
    text, _ = _generate(tmp_path)
    arrays = _arrays(text)
    for slot in (0, 1):
        lp, hp = arrays[f"P{slot}_CMD_LP"], arrays[f"P{slot}_CMD_HP"]
        lk, hk = arrays[f"P{slot}_CMD_LK"], arrays[f"P{slot}_CMD_HK"]
        assert lp != hp and lk != hk
        assert ((lp[5] >> 2) & 3) == 1 and ((hp[5] >> 2) & 3) == 2
        assert ((lk[5] >> 2) & 3) == 1 and ((hk[5] >> 2) & 3) == 2
        # familia fisica: soco = tecla 1, chute = tecla 2 (nibble de botoes)
        assert lp[4] >> 4 == hp[4] >> 4 == 1
        assert lk[4] >> 4 == hk[4] >> 4 == 2


def test_alias_apontando_para_comando_inexistente_falha_fechado(tmp_path):
    cfg = json.loads(KEN_CFG.read_text(encoding="utf-8"))
    cfg["commands"]["hp"] = "nao_existe_no_cmd"
    broken = tmp_path / "ken_broken.json"
    broken.write_text(json.dumps(cfg), encoding="utf-8")
    with pytest.raises(ValueError, match="nao_existe"):
        _generate(tmp_path, ken_cfg=broken)


def test_header_sozinho_contem_os_quatro_alias_de_golpo(tmp_path):
    """Alias de arte (button1/FF) nao e lido pelo anel: nao vira byte morto na ROM."""
    text, _ = _generate(tmp_path)
    assert sorted(_arrays(text)) == sorted(
        f"P{slot}_CMD_{alias}" for slot in (0, 1) for alias in ("LP", "HP", "LK", "HK"))


def test_a_mesma_entrada_produz_o_mesmo_header(tmp_path):
    first, _ = _generate(tmp_path)
    second, _ = _generate(tmp_path)
    assert first == second


def test_relatorio_registra_procedencia_e_os_bytes_dos_quatro_padroes(tmp_path):
    _, report = _generate(tmp_path)
    assert report["schema"] == "attack_cmds_v1"
    assert report["sources"] == {"p1": str(KEN), "p2": str(RYU)}
    assert report["source_sha256"] == {"p1": sha256_file(KEN), "p2": sha256_file(RYU)}
    for slot in ("p1", "p2"):
        for alias in ("lp", "hp", "lk", "hk"):
            assert re.fullmatch(r"[0-9a-f]+", report["patterns"][slot][alias])
    assert json.loads(json.dumps(report)) == report


def test_self_check_nao_depende_do_acervo():
    assert cmd_patterns.main(["--self-check"]) == 0


# Escopo donor: le SMS_projects/luta_mugen (doc/ EIO na midia). Deselecionado por --project rev2.
pytestmark = pytest.mark.donor
