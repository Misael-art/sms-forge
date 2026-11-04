"""E1 - Inventário somente-leitura de acervos MUGEN ZIP/RAR.

Nunca altera os arquivos de origem. ZIP é lido em memória; RAR usa Source/7z
em uma pasta temporária isolada. Saída determinística e sem timestamps.

Uso:
    python -m mugen2sms.inventory <acervo_dir> --out <inventario.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

from .source import Source

SCHEMA = "mugen2sms.inventory/v1"

# Classificacao inicial de suporte por extensao. Revisar a cada etapa do ROADMAP.
FORMAT_SUPPORT = {
    ".def": "planned",       # personagem/stage/fight/select - E2
    ".air": "planned",       # animacoes + caixas Clsn - E2
    ".sff": "planned",       # sprites/paletas v1 (PCX) e v2 - E2
    ".act": "planned",       # paleta 768 bytes - E2
    ".cmd": "planned",       # comandos - E3
    ".cns": "partial",       # estados - E3, traducao parcial por natureza
    ".st": "partial",        # estados auxiliares - E3
    ".snd": "planned",       # sons WAV -> XGM2 - E3
    ".fnt": "decision",      # fontes - depende de decisao manual
    ".mp3": "decision",      # musica: exige recomposicao/conversao para XGM2/VGM
    ".ogg": "decision",
    ".mid": "decision",
    ".xm": "decision",
    ".mod": "decision",
    ".it": "decision",
    ".s3m": "decision",
    ".wav": "planned",
    ".txt": "doc",
    ".pcx": "planned",
    ".png": "planned",
}
LICENSE_HINT = re.compile(r"(licen|readme|leia|copying|terms|permission|author)", re.I)
TEXT_EXT = {".def", ".txt"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sff_version(head: bytes) -> str | None:
    # Assinatura "ElecbyteSpr\0" + versao em bytes 12..15 (lo3, lo2, lo1, hi)
    if not head.startswith(b"ElecbyteSpr"):
        return None
    return f"{head[15]}.{head[14]}.{head[13]}.{head[12]}"


def parse_def_info(text: str) -> dict:
    """Extrai apenas campos de identificacao de [Info]; parser completo vem na E2."""
    info, section = {}, None
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and "]" in line:
            section = line[1 : line.index("]")].strip().lower()
            continue
        if section == "info":
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip().lower()
                if k in {"name", "displayname", "author", "versiondate", "mugenversion"}:
                    info[k] = v.strip().strip('"')
            else:
                # Legacy DEFs may record attribution as `Author: name`.
                match = re.match(r"^author\s*:\s*(.*?)\s*$", line, re.I)
                if match and match.group(1) and "author" not in info:
                    info["author"] = match.group(1).strip().strip('"')
    return info


def classify_def(text: str) -> str:
    low = text.lower()
    if "[bgdef" in low or "[stageinfo" in low:
        return "stage"
    if "[files]" in low and ("cmd" in low or "cns" in low):
        return "character"
    if "[files]" in low:
        return "system_or_other"
    return "unknown"


def inspect_archive(path: Path, root: Path) -> dict:
    entry = {
        "path": path.relative_to(root).as_posix(),
        "category": path.relative_to(root).parts[0],
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "ext_counts": {},
        "sff_versions": [],
        "defs": [],
        "license_candidates": [],
        "license_status": "unknown",  # so muda com evidencia humana registrada
        "errors": [],
    }
    try:
        with Source(path) as src:
            exts = Counter()
            for filename in src.files:
                name = PurePosixPath(filename)
                ext = name.suffix.lower()
                exts[ext or "<none>"] += 1
                if LICENSE_HINT.search(name.name):
                    entry["license_candidates"].append(filename)
                if ext == ".sff":
                    entry["sff_versions"].append(
                        {"file": filename, "version": sff_version(src.read_prefix(filename, 16))}
                    )
                elif ext == ".def" and src.size(filename) < 256 * 1024:
                    text = src.read(filename).decode("latin-1")
                    entry["defs"].append(
                        {"file": filename, "kind": classify_def(text), "info": parse_def_info(text)}
                    )
            entry["ext_counts"] = dict(sorted(exts.items()))
    except (zipfile.BadZipFile, OSError, NotImplementedError, ValueError) as e:
        entry["errors"].append(f"{type(e).__name__}: {e}")
    return entry


# Compatibilidade para consumidores do nome anterior.
inspect_zip = inspect_archive


def summarize(entries: list[dict]) -> dict:
    exts, sff, kinds = Counter(), Counter(), Counter()
    for e in entries:
        exts.update(e["ext_counts"])
        sff.update(s["version"] or "invalid" for s in e["sff_versions"])
        kinds.update(d["kind"] for d in e["defs"])
    return {
        "archives": len(entries),
        "archives_with_errors": sum(1 for e in entries if e["errors"]),
        "archives_with_license_candidates": sum(1 for e in entries if e["license_candidates"]),
        "archives_license_confirmed": sum(1 for e in entries if e["license_status"] == "confirmed"),
        "ext_counts": dict(sorted(exts.items())),
        "sff_versions": dict(sorted(sff.items())),
        "def_kinds": dict(sorted(kinds.items())),
        "format_support": {k: FORMAT_SUPPORT.get(k, "unclassified") for k in sorted(exts)},
    }


def _build_self_check_root(tmp: Path) -> Path:
    """Acervo sintetico: 1 zip com .def de personagem, .sff v1 e um readme."""
    (tmp / "chars").mkdir(parents=True)
    def_text = ('; fixture\n[Info]\nname = "Mini"\nauthor = "fixture"\n'
                '[Files]\ncns = mini.cns\ncmd = mini.cmd\n')
    sff_head = b"ElecbyteSpr\x00" + bytes([0, 1, 0, 1])   # 12 B de assinatura + versao "1.0.1.0"
    with zipfile.ZipFile(tmp / "chars" / "mini.zip", "w", zipfile.ZIP_STORED) as z:
        z.writestr("mini.def", def_text)
        z.writestr("data.sff", sff_head + b"\x00" * 496)  # 512 B de header
        z.writestr("readme.txt", "fixture sintetic - nao e arte real")
    return tmp


def self_check() -> int:
    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp(prefix="mugen2sms_inv_"))
    fails: list[str] = []
    try:
        root = _build_self_check_root(tmp)
        archives = sorted(p for p in root.rglob("*") if p.suffix.lower() in {".zip", ".rar"})
        if len(archives) != 1:
            fails.append(f"esperava 1 arquivo sintetico, veio {len(archives)}")
        entries = [inspect_archive(p, root) for p in archives]
        s = summarize(entries)
        e = entries[0]
        if s.get("archives") != 1:
            fails.append(f"archives != 1: {s.get('archives')}")
        if s.get("archives_with_errors") != 0:
            fails.append(f"archives_with_errors != 0: {e['errors']}")
        if e["defs"] != [{"file": "mini.def", "kind": "character",
                          "info": {"name": "Mini", "author": "fixture"}}]:
            fails.append(f"defs divergem: {e['defs']}")
        if not any(v["version"] == "1.0.1.0" for v in e["sff_versions"]):
            fails.append(f"sff v1 nao detectado: {e['sff_versions']}")
        if not e["license_candidates"]:
            fails.append("readme nao virou license candidate")
        if s.get("ext_counts") != {".def": 1, ".sff": 1, ".txt": 1}:
            fails.append(f"ext_counts divergem: {s.get('ext_counts')}")
        # determinismo: mesma entrada, mesma saida serializada
        again = summarize([inspect_archive(p, root) for p in archives])
        if json.dumps(s, sort_keys=True) != json.dumps(again, sort_keys=True):
            fails.append("saida nao deterministica entre leituras")
        # o self-check nao pode passar com summarize corrompido:
        if summarize([]).get("archives") != 0:
            fails.append("summarize([]) com archives != 0")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fails:
        for f in fails:
            print(f"[SELF-CHECK FAIL] {f}", file=sys.stderr)
        return 1
    print("[SELF-CHECK OK] inventory")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path, nargs="?")
    ap.add_argument("--out", type=Path, required=False)
    ap.add_argument("--skip", action="append", default=["fullgames"],
                    help="categorias de topo a ignorar (default: fullgames)")
    ap.add_argument("--self-check", action="store_true",
                    help="valida o pipeline com um acervo sintetico embutido (§19)")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    if not a.root or not a.out:
        print("[FAIL] uso: inventory <acervo_dir> --out <json> (ou --self-check)", file=sys.stderr)
        return 3
    root = a.root.resolve()
    archives = sorted(p for p in root.rglob("*")
                      if p.suffix.lower() in {".zip", ".rar"}
                      and p.relative_to(root).parts[0] not in a.skip)
    entries = []
    for i, p in enumerate(archives, 1):
        print(f"[{i}/{len(archives)}] {p.relative_to(root)}", file=sys.stderr)
        entries.append(inspect_archive(p, root))
    doc = {"schema": SCHEMA, "root_label": root.name, "skipped": sorted(a.skip),
           "summary": summarize(entries), "archives": entries}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(doc["summary"], indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
