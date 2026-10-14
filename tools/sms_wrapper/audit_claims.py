#!/usr/bin/env python3
"""Gate CLAIMS — teto de promocao executavel.

Reprova docs do projeto que contenham tokens de claim (ex.: "AAA", "60fps",
"pixel perfect") sem arquivo de teto aprovado correspondente em
doc/promotion_claims/<token>.json.

Teto aprovado precisa declarar: token, scope, ceiling_texto, approved_by, date.
Vocabulario de status e a unica linguagem livre: documentado != implementado !=
buildado != testado_em_emulador != validado_budget.

Uso: audit_claims.py --project <dir> [--self-check]
Exit: 0 | 1 reprova | 3 uso
"""
import sys, os, json, re, argparse

CLAIM_TOKENS = {
    "aaa": re.compile(r"\bAAA\b", re.NOFLAG),
    "60fps": re.compile(r"\b60\s?fps\b", re.IGNORECASE),
    "50fps": re.compile(r"\b50\s?fps\b", re.IGNORECASE),
    "pixel_perfect": re.compile(r"pixel[- ]perfect", re.IGNORECASE),
    "release": re.compile(r"\b(release|lan[çc]amento)\b", re.IGNORECASE),
}
DOC_DIRS = ("doc", "rascunho")
SKIP_BASENAMES = {"promotion_claims"}

def load_ceilings(project):
    cdir = os.path.join(project, "doc", "promotion_claims")
    approved = set()
    if os.path.isdir(cdir):
        for fn in os.listdir(cdir):
            if fn.endswith(".json"):
                try:
                    d = json.load(open(os.path.join(cdir, fn)))
                    if (isinstance(d, dict) and all(isinstance(d.get(k), str) and d[k].strip()
                            for k in ("token", "scope", "approved_by", "date")) and
                            isinstance(d.get("ceiling_texto", d.get("ceiling")), str) and
                            d.get("ceiling_texto", d.get("ceiling")).strip()):
                        approved.add(d["token"].lower())
                except (OSError, UnicodeError, json.JSONDecodeError, AttributeError, TypeError):
                    pass
    return approved

def scan(project):
    errors = []
    approved = load_ceilings(project)
    hits = {}
    for sub in DOC_DIRS:
        base = os.path.join(project, sub)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIP_BASENAMES]
            for fn in files:
                if not fn.endswith((".md", ".txt")):
                    continue
                p = os.path.join(root, fn)
                try:
                    text = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                rel = os.path.relpath(p, project).replace("\\", "/")
                for tok, rx in CLAIM_TOKENS.items():
                    if tok in approved:
                        continue
                    for m in rx.finditer(text):
                        line = text.count("\n", 0, m.start()) + 1
                        hits.setdefault(tok, []).append(f"{rel}:{line}")
    for tok, locs in sorted(hits.items()):
        for loc in locs[:5]:
            errors.append(f"claim '{tok}' sem teto aprovado em {loc}")
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        import tempfile, shutil
        d = tempfile.mkdtemp(prefix="smsclaims_")
        os.makedirs(os.path.join(d, "doc"), exist_ok=True)
        open(os.path.join(d, "doc", "a.md"), "w").write("Nosso jogo e AAA total.\n")
        assert any("aaa" in e for e in scan(d)), "deveria reprovar AAA"
        cd = os.path.join(d, "doc", "promotion_claims"); os.makedirs(cd, exist_ok=True)
        json.dump({"token": "aaa", "scope": "demo", "approved_by": "humano",
                   "date": "2026-08-25", "ceiling": "apenas demo"},
                  open(os.path.join(cd, "aaa.json"), "w"))
        assert not scan(d), scan(d)
        for invalid in ({"token": "aaa", "scope": "", "approved_by": "", "date": None, "ceiling": ""},
                        {"token": "aaa", "scope": "demo", "approved_by": "owner", "date": "2026-08-25"}):
            json.dump(invalid, open(os.path.join(cd, "aaa.json"), "w"))
            assert scan(d), "empty/missing approval ceiling cannot waive claims"
        with open(os.path.join(cd, "aaa.json"), "wb") as stream:
            stream.write(b"\xff\xfe")
        assert scan(d), "unreadable approval cannot waive claims"
        shutil.rmtree(d)
        print("[SELF-CHECK OK] claims")
        return 0
    errors = scan(args.project)
    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        return 1
    print("[PASS] nenhum claim acima do teto")
    return 0

if __name__ == "__main__":
    sys.exit(main())
