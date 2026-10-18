"""Gate de regresso do IR real: ken_masters_adv deve parsear inteiro.

O acervo nao vai ao Git (politica de licenca do GDD); sem ele o teste pula com aviso.
"""
from __future__ import annotations

from pathlib import Path

import pytest

KEN = Path("/mnt/sdcard/Projects/Mugenesis/Base de Estudo/chars/street-fighter/ken_masters_adv.zip")


@pytest.mark.skipif(not KEN.exists(), reason=f"acervo local ausente: {KEN}")
def test_ken_full_parse_ok(tmp_path):
    from mugen2sms.ken_full_parse import main
    out = tmp_path / "ken_ir.json"
    assert main([str(KEN), "--out", str(out)]) == 0
    import json
    s = json.loads(out.read_text(encoding="utf-8"))
    assert s["parse_erros"] == []
    assert s["missing_refs_reais"] == []
    assert s["n_sprites"] == 463
    assert s["n_animations"] == 161
    assert s["n_frames"] == 934
    assert s["n_clsn_entries"] == 1526
    assert s["n_commands"] == 91
    assert s["n_states"] == 126
