# tests/test_donation_parity.py — a copia SMS deve ser o doador MD + apenas o rename de pacote.
# Any divergence beyond the package rename must be a conscious, separately committed change.
import json, hashlib
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]          # .../mugen2sms
MANIFEST = ROOT.parents[2] / "SMS_projects/luta_mugen/doc/doacao_md_mugen2sms.json"
DONOR_TOKEN = "mugen2sgdk_forge"


def _norm(text: str) -> str:
    return text.replace(DONOR_TOKEN, "mugen2sms")


def _files():
    return sorted(p for p in ROOT.rglob("*.py")
                  if "tests" not in p.parts and "__pycache__" not in p.parts)


def _manifest():
    return json.loads(MANIFEST.read_text())


def test_manifest_exists_with_sha():
    assert MANIFEST.exists(), "rode o passo de registro da doacao"
    entries = _manifest()["files"]
    assert len(entries) >= 20


@pytest.mark.parametrize("local", _files())
def test_local_file_is_donor_plus_rename(local):
    rel = str(local.relative_to(ROOT))
    entry = next((e for e in _manifest()["files"] if e["local"] == rel), None)
    assert entry, f"{rel} sem registro no manifest"
    if entry.get("origin") == "local_original":     # modulo criado no fork SMS, pino por hash
        assert "donor_abspath_at_copy_time" not in entry, f"{rel} nao pode ter doador e origin local"
        assert hashlib.sha256(local.read_bytes()).hexdigest() == entry["local_sha256_after_deviation"], \
            f"{rel} mudou apos o pino: atualizar manifest conscientemente"
        return
    if "donor_abspath_at_copy_time" not in entry:   # modulo novo do fork SMS
        assert local.read_text() == "", f"{rel} novo deve comecar vazio"
        return
    donor = Path(entry["donor_abspath_at_copy_time"])
    if "local_sha256_after_deviation" in entry:  # desvio intencional pino no hash local
        assert hashlib.sha256(local.read_bytes()).hexdigest() == entry["local_sha256_after_deviation"], \
            f"{rel} mudou apos o pino: atualizar manifest conscientemente"
        return
    if not donor.exists():
        pytest.skip("doador ausente neste host — SHA do manifest basta")
    assert hashlib.sha256(donor.read_bytes()).hexdigest() == entry["donor_sha256"], \
        "doador mudou pos-copia: re-verificar na mao"
    assert _norm(donor.read_text()) == local.read_text(), f"{rel} diverge do doador alem do rename"


def test_no_donor_imports_remain():
    for f in _files():
        assert DONOR_TOKEN not in f.read_text(), f"{f} ainda referencia o pacote doador"
