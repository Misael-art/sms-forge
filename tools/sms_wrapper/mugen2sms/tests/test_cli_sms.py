"""A entrada pública deve funcionar sem conversores/runtime de outro console."""
import os
from pathlib import Path
import subprocess
import sys
import pytest

WRAPPER = Path(__file__).resolve().parents[2]

@pytest.mark.parametrize("command", [None, "inventory", "parse-char", "generate", "scene-cut", "versus-cut", "quality-check"])
def test_sms_public_routes_help(command):
    env = dict(os.environ, PYTHONPATH=str(WRAPPER))
    args = [sys.executable, "-m", "mugen2sms"]
    if command:
        args.append(command)
    result = subprocess.run(args + ["--help"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()

def test_missing_backend_rejected():
    env = dict(os.environ, PYTHONPATH=str(WRAPPER))
    result = subprocess.run([sys.executable, "-m", "mugen2sms", "install-runtime"], env=env, capture_output=True, text=True)
    assert result.returncode == 2
    assert "não implementado" in result.stderr
