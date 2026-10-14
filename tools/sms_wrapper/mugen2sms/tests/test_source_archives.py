import hashlib
import subprocess
from pathlib import Path

import pytest

from mugen2sms import source as source_module
from mugen2sms.source import Source


def test_rar_source_uses_isolated_extraction_and_keeps_archive_sha(monkeypatch, tmp_path):
    archive = tmp_path / "mini.rar"
    raw = b"fixture rar bytes"
    archive.write_bytes(raw)
    extracted = {}

    def fake_which(name):
        return "/usr/bin/7z" if name == "7z" else None

    def fake_run(args, **kwargs):
        if args[1] == "l":
            output = b"Listing archive: mini.rar\n----------\nPath = Nested/Mini.def\nFolder = -\n"
            return subprocess.CompletedProcess(args, 0, stdout=output, stderr=b"")
        root = Path(next(arg[2:] for arg in args if arg.startswith("-o")))
        (root / "Nested").mkdir()
        (root / "Nested" / "Mini.def").write_text("[Info]\nname=Mini\n", encoding="ascii")
        extracted["root"] = root
        return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(source_module.shutil, "which", fake_which)
    monkeypatch.setattr(source_module.subprocess, "run", fake_run)

    with Source(archive) as src:
        assert src.find("mini.def") == "Nested/Mini.def"
        assert src.read("Nested/Mini.def").startswith(b"[Info]")
        assert src.sha256() == hashlib.sha256(raw).hexdigest()
        temp_root = extracted["root"]
        assert temp_root.exists()

    assert not temp_root.exists()


def test_rar_source_rejects_symlink_members(monkeypatch, tmp_path):
    archive = tmp_path / "unsafe.rar"
    archive.write_bytes(b"fixture rar bytes")

    def fake_run(args, **kwargs):
        if args[1] == "l":
            output = b"Listing archive: unsafe.rar\n----------\nPath = escape\nFolder = -\n"
            return subprocess.CompletedProcess(args, 0, stdout=output, stderr=b"")
        root = Path(next(arg[2:] for arg in args if arg.startswith("-o")))
        (root / "escape").symlink_to(tmp_path, target_is_directory=True)
        return subprocess.CompletedProcess(args, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(source_module.shutil, "which", lambda name: "/usr/bin/7z")
    monkeypatch.setattr(source_module.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="link"):
        Source(archive)


def test_rar_source_rejects_path_traversal_before_extract(monkeypatch, tmp_path):
    archive = tmp_path / "unsafe.rar"
    archive.write_bytes(b"fixture rar bytes")
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args[1])
        output = b"Listing archive: unsafe.rar\n----------\nPath = ../escape\nFolder = -\n"
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr=b"")

    monkeypatch.setattr(source_module.shutil, "which", lambda name: "/usr/bin/7z")
    monkeypatch.setattr(source_module.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="caminho inseguro"):
        Source(archive)
    assert calls == ["l"]


def test_rar_source_rejects_link_metadata_before_extract(monkeypatch, tmp_path):
    archive = tmp_path / "linked.rar"
    archive.write_bytes(b"fixture rar bytes")
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args[1])
        output = (b"Listing archive: linked.rar\n----------\nPath = link\n"
                  b"Symbolic Link = ../outside\nFolder = -\n")
        return subprocess.CompletedProcess(args, 0, stdout=output, stderr=b"")

    monkeypatch.setattr(source_module.shutil, "which", lambda name: "/usr/bin/7z")
    monkeypatch.setattr(source_module.subprocess, "run", fake_run)

    with pytest.raises(ValueError, match="link"):
        Source(archive)
    assert calls == ["l"]


def test_rar_source_requires_7z_or_7zz(monkeypatch, tmp_path):
    archive = tmp_path / "mini.rar"
    archive.write_bytes(b"fixture rar bytes")
    monkeypatch.setattr(source_module.shutil, "which", lambda _name: None)

    with pytest.raises(FileNotFoundError, match="7z/7zz"):
        Source(archive)
