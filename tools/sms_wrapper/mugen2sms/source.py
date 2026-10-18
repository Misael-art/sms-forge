"""Acesso somente-leitura a pasta, ZIP ou RAR MUGEN, com resolução case-insensitive."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def _rar_member_names(listing: str) -> list[str]:
    """Extrai nomes do formato `7z l -slt` e bloqueia caminhos externos."""
    members, in_entries = [], False
    for line in listing.splitlines():
        if line.strip() == "----------":
            in_entries = True
            continue
        if in_entries and line.startswith(("Symbolic Link = ", "Hard Link = ")):
            raise ValueError("RAR contem link, recusado antes da extração")
        if not in_entries or not line.startswith("Path = "):
            continue
        name = line[7:]
        normalized = name.replace("\\", "/")
        path = PurePosixPath(normalized)
        if (not name or not path.parts or path.is_absolute() or ".." in path.parts
                or ":" in path.parts[0] or any(ord(ch) < 32 for ch in name)):
            raise ValueError(f"caminho inseguro no RAR: {name!r}")
        members.append(name)
    if not in_entries:
        raise ValueError("7z nao retornou a lista de membros do RAR")
    return members


class Source:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._temporary = None
        self._root = self.path
        suffix = self.path.suffix.lower()
        self._zip = zipfile.ZipFile(self.path) if suffix == ".zip" else None
        if suffix == ".rar":
            tool = shutil.which("7z") or shutil.which("7zz")
            if tool is None:
                raise FileNotFoundError("abrir .rar requer 7z/7zz no PATH")
            resolved = str(self.path.resolve())
            listing = subprocess.run(
                [tool, "l", "-slt", "-sccUTF-8", resolved], check=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if listing.returncode != 0:
                detail = listing.stderr.decode("utf-8", errors="replace").strip()
                raise ValueError(f"7z nao conseguiu listar {self.path.name}: {detail}")
            _rar_member_names(listing.stdout.decode("utf-8", errors="replace"))
            self._temporary = tempfile.TemporaryDirectory(prefix="mugen2sms_rar_")
            self._root = Path(self._temporary.name)
            try:
                result = subprocess.run(
                    [tool, "x", "-y", f"-o{self._root}", resolved],
                    check=False, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    detail = result.stderr.decode("utf-8", errors="replace").strip()
                    raise ValueError(f"7z nao conseguiu ler {self.path.name}: {detail}")
                root = self._root.resolve()
                for item in self._root.rglob("*"):
                    if item.is_symlink():
                        raise ValueError(f"RAR contem link, recusado: {item.relative_to(self._root)}")
                    try:
                        item.resolve().relative_to(root)
                    except ValueError as exc:
                        raise ValueError(f"RAR escapou da pasta temporaria: {item}") from exc
            except Exception:
                self._temporary.cleanup()
                self._temporary = None
                raise
        if self._zip:
            names = [n for n in self._zip.namelist() if not n.endswith("/")]
        else:
            names = [p.relative_to(self._root).as_posix() for p in sorted(self._root.rglob("*"))
                     if p.is_file()]
        self._names = {n.lower(): n for n in names}
        self.files = sorted(names)

    def sha256(self) -> str:
        h = hashlib.sha256()
        if self._zip or self.path.suffix.lower() == ".rar":
            h.update(self.path.read_bytes())
        else:
            for n in self.files:
                h.update(n.encode())
                h.update(self.read(n))
        return h.hexdigest()

    def find(self, rel: str, base: str = "") -> str | None:
        """Resolve 'rel' relativo a 'base' (pasta do .def), ignorando caixa e barras invertidas."""
        rel = rel.strip().strip('"').replace("\\", "/")
        cands = [str(PurePosixPath(base) / rel) if base else rel, rel]
        for c in cands:
            n = self._names.get(str(PurePosixPath(c)).lower())
            if n:
                return n
        # MUGEN tambem procura pelo nome do arquivo em qualquer pasta do pacote
        leaf = PurePosixPath(rel).name.lower()
        hits = [v for k, v in self._names.items() if PurePosixPath(k).name == leaf]
        return hits[0] if len(hits) == 1 else None

    def read(self, name: str) -> bytes:
        if self._zip:
            return self._zip.read(name)
        return (self._root / name).read_bytes()

    def read_prefix(self, name: str, length: int) -> bytes:
        if self._zip:
            with self._zip.open(name) as stream:
                return stream.read(length)
        with (self._root / name).open("rb") as stream:
            return stream.read(length)

    def size(self, name: str) -> int:
        if self._zip:
            return self._zip.getinfo(name).file_size
        return (self._root / name).stat().st_size

    def defs(self) -> list[str]:
        return [n for n in self.files if n.lower().endswith(".def")]

    def close(self) -> None:
        if self._zip is not None:
            self._zip.close()
            self._zip = None
        if self._temporary is not None:
            self._temporary.cleanup()
            self._temporary = None

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
