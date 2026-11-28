#!/usr/bin/env python3
"""Verify the illustrated Word/PDF edition of a character sheet (SMS_GLOBAL §136)."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zipfile import BadZipFile, ZipFile

from artifact_registry import digest, file_ref

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "svg": "http://schemas.microsoft.com/office/drawing/2016/SVG/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
DPI = 100


def check_edition(text, terms):
    words = " ".join(text.split())
    for term in terms:
        if not re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", words):
            raise ValueError(f"edição sem {term!r}")


def check_word(path, figures, terms):
    if not isinstance(figures, dict) or not figures:
        raise ValueError("declare as figuras revistas por wp:docPr/@id")
    with ZipFile(path) as archive:
        doc = ET.fromstring(archive.read("word/document.xml"))
        paragraphs = ("".join(t.text or "" for t in p.iterfind(".//w:t", NS))
                      for p in doc.iterfind(".//w:p", NS))
        check_edition(" ".join(paragraphs), terms)
        relationships = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        rels = {r.get("Id"): r for r in relationships.findall("rel:Relationship", NS)}
        seen = set()
        for drawing in doc.findall(".//w:drawing", NS):
            props = drawing.find("./*/wp:docPr", NS)
            if props is None or props.get("id") not in figures:
                continue
            key = props.get("id")
            if key in seen:
                raise ValueError(f"figura {key} ambígua")
            seen.add(key)
            expected = figures[key]
            if not isinstance(expected, dict) or "blip" not in expected:
                raise ValueError(f"figura {key} sem imagem principal")
            actual = {}
            for kind, tag in (("blip", "a:blip"), ("svgBlip", "svg:svgBlip")):
                for item in drawing.findall(f".//{tag}", NS):
                    rel = rels.get(item.get(f"{{{NS['r']}}}embed"))
                    if (kind in actual or rel is None or item.get(f"{{{NS['r']}}}link")
                            or rel.get("TargetMode", "Internal") != "Internal"
                            or rel.get("Type") != NS["r"] + "/image"):
                        raise ValueError(f"figura {key} com vínculo {kind} ambíguo ou externo")
                    target = PurePosixPath(rel.get("Target", ""))
                    if target.parts[:1] != ("media",) or ".." in target.parts:
                        raise ValueError(f"figura {key} fora de word/media")
                    actual[kind] = hashlib.sha256(archive.read(f"word/{target}")).hexdigest()
            if actual != expected:
                raise ValueError(f"figura {key}: imagens ativas divergem do contrato {actual}")
        if seen != set(figures):
            raise ValueError(f"figuras ausentes: {sorted(set(figures) - seen)}")


def output(args, timeout=60):
    result = subprocess.run(args, capture_output=True, timeout=timeout,
                            env={**os.environ, "LC_ALL": "C"})
    if result.returncode:
        raise ValueError(f"{args[0]}: {result.stderr.decode(errors='replace')[-400:]}")
    return result.stdout


def pages(pdf):
    info = output(["pdfinfo", pdf])
    match = re.search(rb"(?m)^Pages:\s+(\d+)\s*$", info)
    if not match or int(match[1]) < 1:
        raise ValueError("PDF sem contagem de páginas válida")
    return int(match[1])


def page_text(pdf, number):
    return output(["pdftotext", "-enc", "UTF-8", "-layout", "-f", str(number),
                   "-l", str(number), pdf, "-"]).decode()


def page_pixels(pdf, number):
    data = output(["pdftoppm", "-r", str(DPI), "-singlefile", "-f", str(number),
                   "-l", str(number), pdf])
    if not data.startswith(b"P6"):
        raise ValueError(f"rasterização PPM vazia ou inválida na página {number}")
    return hashlib.sha256(data).digest()


def compare_pdf(fresh, published, terms):
    count = pages(fresh)
    if count != pages(published):
        raise ValueError("quantidade de páginas divergente da exportação atual")
    for i in range(1, count + 1):
        text = page_text(published, i)
        if text != page_text(fresh, i):
            raise ValueError(f"texto divergente na página {i}")
        if i == 1:
            check_edition(text, terms)
        if page_pixels(fresh, i) != page_pixels(published, i):
            raise ValueError(f"imagem divergente na página {i}")
    return count


def audit(project, contract, temp):
    if not isinstance(contract, dict) or contract.get("schema") != "character_sheet_v1":
        raise ValueError("schema deve ser character_sheet_v1")
    terms = [contract.get(k) for k in ("character", "edition")]
    if not all(isinstance(term, str) and term.strip() == term and term for term in terms):
        raise ValueError("nome e edição obrigatórios")
    source = file_ref(project, contract["docx"])
    published = file_ref(project, contract["pdf"])
    if source.suffix.lower() != ".docx" or published.suffix.lower() != ".pdf":
        raise ValueError("esperados DOCX e PDF")
    # Freeze the exact bytes used by both the parser and the private export.
    source_copy = temp / source.name
    pdf_copy = temp / "published.pdf"
    for src, dst, ref in [(source, source_copy, "docx"), (published, pdf_copy, "pdf")]:
        shutil.copyfile(src, dst)
        if digest(dst) != contract[ref]["sha256"]:
            raise ValueError(f"{ref} alterado durante a leitura")
    check_word(source_copy, contract["figures"], terms)
    export = temp / "export"
    export.mkdir()
    profile = (temp / "profile").resolve().as_uri()
    output(["soffice", f"-env:UserInstallation={profile}", "--headless", "--norestore",
            "--convert-to", "pdf", "--outdir", export, source_copy], timeout=180)
    fresh = export / source_copy.with_suffix(".pdf").name
    if not fresh.is_file():
        raise ValueError("o editor não produziu PDF no diretório privado")
    return compare_pdf(fresh, pdf_copy, terms)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--project", type=Path)
    parser.add_argument("--contract", type=Path)
    args = parser.parse_args()
    if args.self_check:
        test = Path(__file__).with_name("tests") / "test_character_sheet.py"
        return subprocess.run([sys.executable, str(test)]).returncode
    if not args.project or not args.contract:
        parser.error("informe --project e --contract")
    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="sms-ficha-") as temp:
            count = audit(args.project, contract, Path(temp))
        print(f"{contract['character']} {contract['edition']}: {count} páginas idênticas "
              f"a {DPI} dpi, texto e {len(contract['figures'])} figuras conferidos")
    except (OSError, ValueError, TypeError, KeyError, BadZipFile, ET.ParseError,
            subprocess.TimeoutExpired) as error:
        print(f"REPROVADO: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
