"""Positive and negative controls for embedded figures and published pages."""
import hashlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_character_sheet import NS, check_word, compare_pdf


def word(path, with_alternate):
    ns = " ".join(f'xmlns:{key}="{value}"' for key, value in NS.items())
    alt = '<a:extLst><a:ext><svg:svgBlip r:embed="old"/></a:ext></a:extLst>' if with_alternate else ""
    doc = (f'<w:document {ns}><w:body><w:p><w:r><w:t>Alis R8</w:t><w:drawing>'
           f'<wp:inline><wp:docPr id="26"/><a:graphic><a:blip r:embed="new">{alt}</a:blip>'
           '</a:graphic></wp:inline></w:drawing></w:r></w:p></w:body></w:document>')
    with ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", doc)
        archive.writestr("word/_rels/document.xml.rels",
                         f'<Relationships xmlns="{NS["rel"]}">'
                         f'<Relationship Id="new" Type="{NS["r"]}/image" Target="media/new.png"/>'
                         f'<Relationship Id="old" Type="{NS["r"]}/image" Target="media/old.svg"/>'
                         '</Relationships>')
        archive.writestr("word/media/new.png", b"new")
        archive.writestr("word/media/old.svg", b"old")


def pdf(path, shade=0, label="Alis R8"):
    # A single page with editable text and an independently variable square.
    stream = f"BT /F1 12 Tf 20 70 Td ({label}) Tj ET\n{shade} g 30 22 18 18 re f\n".encode()
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] "
               b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"endstream"]
    content = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, obj in enumerate(objects, 1):
        offsets.append(len(content))
        content.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(content)
    content.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets:
        content.extend(f"{offset:010d} 00000 n \n".encode())
    content.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode())
    path.write_bytes(content)


class Sheet(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.doc = Path(temp.name) / "character.docx"
        self.fresh = Path(temp.name) / "export.pdf"
        self.published = Path(temp.name) / "published.pdf"
        self.figures = {"26": {"blip": hashlib.sha256(b"new").hexdigest()}}
        self.terms = ["Alis", "R8"]

    def test_active_images(self):
        word(self.doc, False)
        check_word(self.doc, self.figures, self.terms)  # unreferenced SVG is harmless
        word(self.doc, True)
        self.figures["26"]["svgBlip"] = hashlib.sha256(b"old").hexdigest()
        check_word(self.doc, self.figures, self.terms)

    def test_stale_svg(self):
        word(self.doc, True)
        with self.assertRaisesRegex(ValueError, "figura 26"):
            check_word(self.doc, self.figures, self.terms)

    def test_missing_figure(self):
        word(self.doc, False)
        with self.assertRaisesRegex(ValueError, "ausentes"):
            check_word(self.doc, {"99": self.figures["26"]}, self.terms)

    def test_matching_export(self):
        pdf(self.fresh)
        pdf(self.published)
        self.assertEqual(compare_pdf(self.fresh, self.published, self.terms), 1)

    def test_same_text_wrong_illustration(self):
        pdf(self.fresh)
        pdf(self.published, shade=0.5)
        with self.assertRaisesRegex(ValueError, "imagem divergente na página 1"):
            compare_pdf(self.fresh, self.published, self.terms)

    def test_old_edition(self):
        pdf(self.fresh)
        pdf(self.published, label="Alis R6b")
        with self.assertRaisesRegex(ValueError, "texto divergente"):
            compare_pdf(self.fresh, self.published, self.terms)
        pdf(self.fresh, label="Alis R80")
        pdf(self.published, label="Alis R80")
        with self.assertRaisesRegex(ValueError, "edição sem"):
            compare_pdf(self.fresh, self.published, self.terms)


if __name__ == "__main__":
    unittest.main()
