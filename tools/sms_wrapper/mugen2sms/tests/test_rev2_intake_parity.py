# tests/test_rev2_intake_parity.py — paridade de intake do consumidor rev2.
# Prova o que existe HOJE: ZIPs congelados = intake hasheado, membros extraídos
# = registry com bytes+SHA, DEF selecionado = intake, e a fronteira common1
# declarada (ausência real, sem common inventado). Não finge doação/binding do
# projeto legado: enquanto a ROM rev2 não existir, não há teste de binding.
import hashlib
import json

import pytest

pytestmark = pytest.mark.rev2


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def intake(rev2_project):
    return json.loads((rev2_project / "doc" / "22-intake-doador.json").read_text())


@pytest.fixture(scope="module")
def members(rev2_project):
    return json.loads((rev2_project / "data" / "derived" / "members.json").read_text())


def test_pacotes_congelados_batem_com_intake(rev2_project, intake):
    assert len(intake["packages"]) == 2
    for pkg in intake["packages"]:
        p = rev2_project / pkg["path"]
        assert _sha(p) == pkg["sha256"], f"{pkg['fighter_id']}: zip diverge do intake"
        assert p.stat().st_size == pkg["bytes"]


def test_def_selecionado_bate_com_intake(rev2_project, intake):
    for pkg in intake["packages"]:
        p = rev2_project / "data" / "derived" / pkg["fighter_id"] / pkg["selected_def"]
        assert _sha(p) == pkg["selected_def_sha256"], f"{pkg['fighter_id']}: DEF diverge do intake"


def test_registry_de_membros_confere_no_disco(rev2_project, members):
    assert members["member_count"] == len(members["members"]) == 33
    for m in members["members"]:
        p = rev2_project / m["path"]
        data = p.read_bytes()
        assert len(data) == m["bytes"], f"{m['member']}: bytes divergem"
        assert hashlib.sha256(data).hexdigest() == m["sha256"], f"{m['member']}: sha diverge"


def test_source_sha_do_registry_bate_com_os_zips(rev2_project, members, intake):
    by_path = {pkg["path"]: pkg["sha256"] for pkg in intake["packages"]}
    for rel, sha in members["source_sha256"].items():
        assert by_path[f"data/source_mugen/{rel}"] == sha


def test_fronteira_common1_declarada_sem_invencao(rev2_project, intake):
    for pkg in intake["packages"]:
        assert pkg["common1_in_archive"] is False
    # nenhum common1.cns foi fabricado dentro do projeto
    fabricados = [p for p in rev2_project.rglob("common1.cns") if "out" not in p.parts]
    assert fabricados == [], f"common1 inventado apareceu em {fabricados}"
    assert "common1 missing" in intake["common_policy"]
