# conftest.py — escopo de consumidor para a suíte mugen2sms.
# `--project rev2` roda apenas testes que NÃO leem SMS_projects/luta_mugen
# (cujo doc/ retorna EIO na mídia); `--project donor` restringe ao pino
# histórico do fork; o default `all` preserva o comportamento anterior.
# Deseleção por escopo é seleção, não capacidade: um teste removido do
# escopo rev2 não conta como pronto nem como passado.
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
WORKSPACE = Path(__file__).resolve().parents[4]


def pytest_addoption(parser):
    parser.addoption(
        "--project", default="all", choices=("all", "donor", "rev2"),
        help="escopo de consumidor dos testes de integração (donor=luta_mugen, rev2=luta_mugem_rev2)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "donor: pino ao consumidor legado luta_mugen (manifestos/binding/integrada)")
    config.addinivalue_line("markers", "rev2: integração do consumidor luta_mugem_rev2")


def pytest_collection_modifyitems(config, items):
    scope = config.getoption("--project")
    if scope == "all":
        return
    dropped = []
    for item in items:
        marked_donor = item.get_closest_marker("donor") is not None
        marked_rev2 = item.get_closest_marker("rev2") is not None
        if scope == "rev2" and marked_donor:
            dropped.append(item)
        elif scope == "donor" and marked_rev2:
            dropped.append(item)
    if dropped:
        kept = [i for i in items if i not in dropped]
        items[:] = kept
        config.hook.pytest_deselected(items=dropped)


@pytest.fixture(scope="session")
def rev2_project() -> Path:
    return WORKSPACE / "SMS_projects" / "luta_mugem_rev2"
