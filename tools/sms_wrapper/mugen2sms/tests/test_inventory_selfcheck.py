# S1 — inventory precisa de --self-check com caso-limite embutido (§19: ferramenta de
# medicao sem self-check passando nao gera numero confiavel).
import subprocess, sys
from pathlib import Path
PKG_ROOT = Path(__file__).resolve().parents[1]          # .../mugen2sms
sys.path.insert(0, str(PKG_ROOT.parent))
from mugen2sms.inventory import parse_def_info  # noqa: E402


def test_selfcheck_passes():
    r = subprocess.run([sys.executable, "-m", "mugen2sms.inventory", "--self-check"],
                       cwd=PKG_ROOT.parent, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "SELF-CHECK OK" in r.stdout + r.stderr


def test_selfcheck_fails_when_summarize_is_corrupted():
    # um self-check que so "roda" nao vale: corromper summarize tem que derruba-lo.
    code = (
        "import sys, mugen2sms.inventory as I\n"
        "I.summarize = lambda entries: {'archives': 999}\n"
        "rc = I.main(['--self-check'])\n"
        "sys.exit(42 if rc == 0 else 0)\n"   # 42 = self-check mentiu (passou com saida errada)
    )
    r = subprocess.run([sys.executable, "-c", code], cwd=PKG_ROOT.parent,
                       capture_output=True, text=True)
    assert r.returncode == 0, "self-check passou com summarize corrompido"


def test_def_inventory_preserves_legacy_author_colon():
    info = parse_def_info("[Info]\nname = Terry\nAuthor: Falchion22\n[Files]\n")
    assert info == {"name": "Terry", "author": "Falchion22"}
