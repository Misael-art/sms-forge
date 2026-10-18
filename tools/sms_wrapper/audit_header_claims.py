#!/usr/bin/env python3
"""audit_header_claims.py — a doutrina nao pode contradizer o header (L069).

Lacuna paga em 2026-09-24: SMS_GLOBAL §6 ensinava "name table = 1 byte por
tile, sem flip nem paleta por tile, max 256 tiles BG" — lei do **SG-1000**
passada por SMS. `SMSlib.h:112` calcula stride de 2 bytes e `:124-127` define
TILE_FLIPPED_X/Y, TILE_USE_SPRITE_PALETTE, TILE_PRIORITY. 59/59 testes de host
passavam com a doutrina errada porque NENHUM gate lia o header contra a prosa.

Este gate fecha isso de forma mecanica, nao por prosa:
  1. PARSA o header real (define por nome + valor; stride deduzido de
     XYtoADDR) — a fonte de autoridade #8 vira dado, nao comentario.
  2. REPROVA na doutrina as formas erradas (1 byte/tile, sem flip por tile,
     256 tiles BG, index 0-255, tile de 16 bytes) — com a mesma politica de
     contexto de audit_hardware_constants (nota de correcao e fixture
     reprovada podem citar o errado).
  3. EXIGE que o §6 da SMS_GLOBAL cite os quatro defines com os VALORES DO
     HEADER — se o SDK mudar, a doutrina e pega em flagrante.

Uso: audit_header_claims.py [--root <ws>] [--header <SMSlib.h>] [--json out]
                            [--self-check]
Exit: 0 coerente | 1 doutrina contradiz header | 2 header ausente | 3 uso
"""
import sys, os, re, json, glob, argparse

HERE = os.path.dirname(os.path.abspath(__file__))

FLAG_DEFINES = ["TILE_FLIPPED_X", "TILE_FLIPPED_Y",
                "TILE_USE_SPRITE_PALETTE", "TILE_PRIORITY"]

# Formas erradas que existiram no repo ate 2026-09-24 (casos de regressao).
BAD_FORMS = [
    (re.compile(r"1\s*byte\s*(?:por|/)\s*tile", re.I),
     "name table de '1 byte por tile' e lei do SG-1000; a entrada SMS e 16-bit"),
    (re.compile(r"name\s+table[^\n]{0,40}?\b1\s*byte\b", re.I),
     "name table afirmada como 1 byte"),
    (re.compile(r"\bsem\s+(?:flip|paleta)\b", re.I),
     "'sem flip/paleta' no BG — flags existem na entrada da name table (L069)"),
    (re.compile(r"n[ãa]o\s+existe(?:m)?\s+(?:flip|paleta)", re.I),
     "'nao existe flip/paleta no BG' refutado pelo probe pnt_16bit (L069)"),
    (re.compile(r"m[áa]x(?:imo)?\s*(?:de\s*)?256\s+tiles", re.I),
     "teto de 256 tiles BG — o espaco de pattern do BG e 448 (0-447)"),
    (re.compile(r"256\s+tiles\s+BG", re.I),
     "teto de 256 tiles BG — o espaco de pattern do BG e 448 (0-447)"),
    (re.compile(r"tiles\s+BG[^\n]{0,15}?[≤<]=?\s*256", re.I),
     "orcamento 'tiles BG <=256' — teto correto e 448"),
    (re.compile(r"index\s+0\s*[-–]\s*255", re.I),
     "indice 0-255 — com entrada 16-bit o campo de nome e 9 bits (0-447 utile)"),
    (re.compile(r"padr[ãa]o\s+tile\s*[=:]\s*16\s*bytes", re.I),
     "tile SMS e 4bpp = 32 bytes; 16 bytes e 2bpp (SG-1000/NES)"),
]

# Uma linha que cita a forma errada para NEGAR/REFUTAR/HISTORIZAR e legitima
# (mesma politica de audit_hardware_constants).
CONTEXT_OK = ("sg-1000", "sg1000", "sg 1000", "refut", "dizia", "diziam",
              "errado", "corrigido", "heranç", "heranca", "supersed",
              "invertido", "nao e lei", "não é lei", "nao e sms", "não do sms",
              "reprov", "rejeit", "fixture", "selftest", "invalid",
              "caso de teste", "historico", "histórico")


def parse_header(path):
    """Le o SMSlib.h real: defines por nome e stride da PNT em XYtoADDR."""
    text = open(path, encoding="utf-8", errors="replace").read()
    defines = {}
    for name in FLAG_DEFINES + ["SMS_PNTAddress"]:
        m = re.search(r"#define\s+%s\s+\(?0x([0-9A-Fa-f]+)\)?" % name, text)
        if m:
            defines[name] = int(m.group(1), 16)
    stride = None
    m = re.search(r"#define\s+XYtoADDR[^\n]*", text)
    if m and re.search(r"\)\s*<<\s*1", m.group(0)):
        stride = 2
    return defines, stride


def _docs(root):
    pats = [os.path.join(root, "doc", "**", "*.md"),
            os.path.join(root, "tools", "sms_wrapper", ".agent", "**", "*.md"),
            os.path.join(root, "AGENTS.md"),
            os.path.join(root, "README.md")]
    out = []
    for p in pats:
        out += glob.glob(p, recursive=True)
    return sorted(set(out))


def check_text(texto, origem, defines=None, stride=None):
    problems = []
    linhas = texto.splitlines()
    for n, linha in enumerate(linhas, 1):
        # Contexto nas DUAS direcoes: a frase que nega ("...é lei do SG-1000")
        # pode quebrar linha para baixo — o gate pegou a propria nota de
        # correcao partida em duas linhas no primeiro run real.
        ctx = " ".join(linhas[max(0, n - 3):n + 2]).lower()
        low = linha.lower()
        for rx, msg in BAD_FORMS:
            if rx.search(linha) and not any(w in low or w in ctx for w in CONTEXT_OK):
                problems.append(f"{os.path.basename(origem)}:{n}: {msg}")
    if defines is not None:
        problems += check_section6(texto, origem, defines, stride)
    return problems


def check_section6(texto, origem, defines, stride):
    """O §6 da SMS_GLOBAL deve citar os defines COM os valores do header."""
    if os.path.basename(origem) != "SMS_GLOBAL.md":
        return []
    m = re.search(r"^## 6\..*?(?=^## \d)", texto, re.M | re.S)
    if not m:
        return ["SMS_GLOBAL: secao 6 ausente — a lei da name table sumiu"]
    sec = m.group(0).lower()
    problems = []
    for name, val in defines.items():
        if name in FLAG_DEFINES and f"0x{val:04x}".lower() not in sec:
            problems.append(
                f"SMS_GLOBAL §6 nao cita {name}=0x{val:04X} — ou o header mudou "
                "(re-derive a lei) ou a doutrina regrediu para a prosa antiga")
    if stride == 2 and "16-bit" not in sec and "16 bits" not in sec:
        problems.append("SMS_GLOBAL §6 nao afirma entrada de 16 bits, "
                        "mas XYtoADDR do header tem stride 2")
    return problems


def audit(root, header_path):
    if not os.path.exists(header_path):
        return None, f"header ausente: {header_path}"
    defines, stride = parse_header(header_path)
    missing = [d for d in FLAG_DEFINES if d not in defines]
    if missing:
        return None, ("header sem defines %s — SDK divergente do esperado; "
                      "re-derive antes de confiar no gate" % missing)
    problems = []
    for f in _docs(root):
        try:
            problems += check_text(
                open(f, encoding="utf-8", errors="replace").read(),
                f, defines, stride)
        except OSError as e:
            problems.append(f"{f}: ilegivel ({e})")
    return problems, None


GOOD_SECTION6 = """## 6. Lei do VDP (tiles BG)
- Name table = entrada de 16 bits por tile; flags `TILE_FLIPPED_X` 0x0200,
  `TILE_FLIPPED_Y` 0x0400, `TILE_USE_SPRITE_PALETTE` 0x0800,
  `TILE_PRIORITY` 0x1000.

## 7. fim do trecho
"""

OLD_LAW_LINES = [
    "- Name table = **1 byte por tile** (índice 0–255). Não existe flip nem paleta\n  por tile no BG — variação vem de tiles distintos ou metatiles.",
    "- Grid 8×8; pattern table 32 bytes/tile; **máx 256 tiles BG** (name table é 1 byte/tile).",
    "- Tiles BG únicos ≤256 (name table 1 byte → index 0-255).",
    "- Sem flip/paleta por tile no BG. Variação visual = tiles distintos, metatiles, ou paleta trocada.",
    "- Grid 8×8 imutável; padrão tile = 16 bytes (8 linhas × 2 planos).",
]


def _self_check():
    fake = {n: v for n, v in zip(FLAG_DEFINES, (0x0200, 0x0400, 0x0800, 0x1000))}
    # REPROVA cada uma das cinco formas que o acervo carregou como lei (L069)
    for linha in OLD_LAW_LINES:
        p = check_text(linha, "skill.md")
        assert p, f"forma errada nao reprovada: {linha[:60]}"
    # APROVA a lei nova
    assert not check_text(GOOD_SECTION6, "SMS_GLOBAL.md", fake, 2), \
        "secao6 nova reprovada: %s" % check_text(GOOD_SECTION6, "SMS_GLOBAL.md", fake, 2)
    # APROVA nota de correcao que cita o numero errado de proposito
    assert not check_text("A doutrina dizia \"1 byte por tile, sem flip\" — "
                          "lei do SG-1000, refutada pelo probe (L069).", "x.md")
    # REGRESSAO DO PRIMEIRO RUN: a frase de correcao quebrada em duas linhas
    # (o contexto negativo cai na linha de baixo)
    assert not check_text("Name table era \"1 byte por tile, sem flip\" —\n"
                          "lei do SG-1000, nao do SMS (L069).", "x.md"), \
        "nota de correcao quebrada em linha nao pode reprovar"
    # DIVERGENCIA header↔doutrina: header mudou o valor, §6 nao acompanhou
    p = check_text(GOOD_SECTION6, "SMS_GLOBAL.md", dict(fake, TILE_FLIPPED_X=0x0100), 2)
    assert any("TILE_FLIPPED_X" in x for x in p), "faltou pegar define divergente"
    # REGRESSAO: §6 sem "16 bits" com header stride-2
    p = check_text("## 6. Lei do VDP (tiles BG)\n- Name table com flags.\n\n## 7. x\n",
                   "SMS_GLOBAL.md", fake, 2)
    assert any("16 bits" in x for x in p), "faltou exigir a entrada 16-bit no §6"
    # parse real do header deste workspace
    here = HERE
    hp = os.path.join(here, "..", "..", "sdk", "devkitSMS", "SMSlib", "SMSlib.h")
    if os.path.exists(hp):
        d, s = parse_header(hp)
        assert s == 2 and d["TILE_FLIPPED_X"] == 0x0200, \
            f"parse do header real divergiu: {d} stride={s}"
    print("[SELF-CHECK OK] header_claims (reprova a lei SG-1000 como lei SMS, "
          "exige defines do header no §6, aceita notas de correcao)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.normpath(os.path.join(HERE, "..", "..")))
    ap.add_argument("--header")
    ap.add_argument("--json", "--report-out", dest="json", help="new report destination; existing files are refused")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    header = a.header or os.path.join(a.root, "sdk", "devkitSMS", "SMSlib", "SMSlib.h")
    problems, err = audit(a.root, header)
    if err:
        print(f"[FAIL] {err}")
        return 2
    if a.json:
        from report_output import write_new_report
        try:
            write_new_report(a.json, {"problems": problems, "clean": not problems})
        except OSError as exc:
            print(f"[FAIL] report destination refused: {exc}; choose a new --report-out path")
            return 3
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} claim(s) da doutrina contra o header. "
              "O header decide (autoridade #8); a captura prova (L069).")
        return 1
    print("[PASS] doutrina coerente com os defines do SMSlib.h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
