"""`cmd_sources()` da receita de build: a fonte dos padroes de golpe vem do
manifesto de binding, nunca de caminho chumbado, e o hash e conferido.

Por que isto e testado: o handoff do Lote D (doc/23, secao 6.B) muda o blob
`_CMD_` da ROM. Se a receita lesse um zip por caminho fixo, trocar de elenco
mudaria a ROM sem que nenhuma medicao provasse qual fonte entrou. Falhar
fechado em fonte ausente ou divergente e o que mantem o vinculo asset->ROM
pago. As provas negativas (3, 4, 5) sao o criterio discriminante: uma receita
que apenas abrisse o caminho passaria nelas.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
RECIPE = ROOT / "tools" / "sms_wrapper" / "build_luta_integrada.py"
BINDING = ROOT / "SMS_projects" / "luta_mugen" / "doc" / "rom_asset_binding.json"


def _load(tmp_binding: Path, monkeypatch):
    spec = importlib.util.spec_from_file_location("build_luta_integrada_test", RECIPE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, "BINDING", tmp_binding)
    return mod


def _write_binding(tmp_path: Path, payload: dict) -> Path:
    p = tmp_path / "rom_asset_binding.json"
    p.write_text(json.dumps(payload))
    return p


def test_fontes_reais_do_manifesto_com_hash_confurado():
    """O manifesto vigente aponta os dois zips do corte e os hashes batem."""
    spec = importlib.util.spec_from_file_location("build_luta_integrada_real", RECIPE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    p1, p2 = mod.cmd_sources()
    declared = json.loads(BINDING.read_text())["source_sha256"]
    assert p1.name.endswith(".zip") and p2.name.endswith(".zip")
    assert p1 != p2
    for path, key in ((p1, "p1_ken"), (p2, "p2_ryu")):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == declared[key]


def test_sha256_divergente_falha_fechado(tmp_path, monkeypatch):
    char = tmp_path / "char.zip"
    char.write_bytes(b"conteudo de personagem")
    binding = _write_binding(tmp_path, {
        "source_def": {"p1_ken": "a", "p2_ryu": "b"},
        "source_sha256": {"p1_ken": hashlib.sha256(char.read_bytes()).hexdigest(),
                          "p2_ryu": "0" * 64},
        "entries": [{"source": str(char), "source_sha256":
                     hashlib.sha256(char.read_bytes()).hexdigest()},
                    {"source": str(tmp_path / "ryu.zip"), "source_sha256": "0" * 64}],
    })
    mod = _load(binding, monkeypatch)
    (tmp_path / "ryu.zip").write_bytes(b"ryu verdadeiro")
    with pytest.raises(SystemExit) as e:
        mod.cmd_sources()
    assert "p2_ryu" in str(e.value)


def test_fonte_ausente_no_disco_falha_fechado(tmp_path, monkeypatch):
    char = tmp_path / "ken.zip"
    char.write_bytes(b"ken")
    sha = hashlib.sha256(char.read_bytes()).hexdigest()
    missing = tmp_path / "nao-existe.zip"
    binding = _write_binding(tmp_path, {
        "source_def": {"p1_ken": "a", "p2_ryu": "b"},
        "source_sha256": {"p1_ken": sha, "p2_ryu": "b" * 64},
        "entries": [{"source": str(char), "source_sha256": sha},
                    {"source": str(missing), "source_sha256": "b" * 64}],
    })
    mod = _load(binding, monkeypatch)
    with pytest.raises(SystemExit) as e:
        mod.cmd_sources()
    assert "ausente" in str(e.value)


def test_manifesto_sem_entrada_para_a_fonte_falha_fechado(tmp_path, monkeypatch):
    char = tmp_path / "ken.zip"
    char.write_bytes(b"ken")
    sha = hashlib.sha256(char.read_bytes()).hexdigest()
    binding = _write_binding(tmp_path, {
        "source_def": {"p1_ken": "a", "p2_ryu": "b"},
        "source_sha256": {"p1_ken": sha, "p2_ryu": "b" * 64},
        # so o ken tem entry: o ryu esta declarado mas nao e vinculado a banco
        "entries": [{"source": str(char), "source_sha256": sha}],
    })
    mod = _load(binding, monkeypatch)
    with pytest.raises(SystemExit) as e:
        mod.cmd_sources()
    assert "p2_ryu" in str(e.value)


def test_manifesto_com_tres_fontes_falha_fechado(tmp_path, monkeypatch):
    binding = _write_binding(tmp_path, {
        "source_def": {"p1_ken": "a", "p2_ryu": "b", "p3_chunli": "c"},
        "source_sha256": {"p1_ken": "1" * 64, "p2_ryu": "2" * 64, "p3_chunli": "3" * 64},
        "entries": [],
    })
    mod = _load(binding, monkeypatch)
    with pytest.raises(SystemExit):
        mod.cmd_sources()


def test_sync_copia_header_do_controlador_cpu(tmp_path, monkeypatch):
    """cpu_controller.c e compilado da canonica e precisa do header no scratch."""
    spec = importlib.util.spec_from_file_location("build_luta_integrada_sync_test", RECIPE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    canon = tmp_path / "integrada"
    study = tmp_path / "study"
    (canon / "src").mkdir(parents=True)
    (canon / "inc").mkdir()
    (canon / "tools").mkdir()
    (canon / ".mddev").mkdir()
    (study / "inc").mkdir(parents=True)
    (study / "src").mkdir()
    (study / ".mddev").mkdir()
    for name in mod.HAND_HEADERS:
        (canon / "inc" / name).write_text("/* header */\n")
    (canon / "inc" / "cpu_controller.h").write_text("/* CPU header */\n")
    (canon / "src" / "cpu_controller.c").write_text('#include "cpu_controller.h"\n')
    (canon / "tools" / "placeholder.py").write_text("# tool\n")
    (canon / ".mddev" / "project.json").write_text("{}\n")
    (study / "inc" / "versus_scene_runtime_full_generated.h").write_text("/* generated */\n")
    monkeypatch.setattr(mod, "CANON", canon)
    monkeypatch.setattr(mod, "STUDY", study)

    mod.sync()

    assert (study / "src" / "cpu_controller.c").is_file()
    assert (study / "inc" / "cpu_controller.h").read_text() == "/* CPU header */\n"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))


# Escopo donor: a prova do manifesto VIGENTE le luga_mugen/doc/rom_asset_binding.json (EIO);
# as provas negativas acima usam fixtures temporarias e continuam em todos os escopos.
test_fontes_reais_do_manifesto_com_hash_confurado = pytest.mark.donor(
    test_fontes_reais_do_manifesto_com_hash_confurado)
