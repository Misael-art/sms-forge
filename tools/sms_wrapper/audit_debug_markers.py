#!/usr/bin/env python3
"""audit_debug_markers.py — marcador de depuracao sem `volatile` mente (L009).

L009 pagou tres armadilhas de uma vez, e a mais cara foi esta: uma variavel em
endereco fixo (`__at(0xC900)`) existe para ser lida POR FORA (depurador, probe,
inspecao de RAM). Do ponto de vista do SDCC ela e escrita e nunca lida — logo a
atribuicao e otimizada para fora do binario. O marcador some, a leitura vem
zerada, e o diagnostico se INVERTE: parecia que `SMS_loadTiles` travava porque
o marcador seguinte "nunca era alcancado".

Refutado em 2026-09-01 (probe `_laboratorio/loadtiles_hang`): com marcadores
`volatile` impressos NA TELA, `SMS_loadTiles` completa nas duas condicoes
(display ligado e desligado). A funcao nunca travou — o instrumento mentia.

Regra: toda variavel declarada com `__at(...)` precisa ser `volatile`.
Ela so existe para observacao externa; sem `volatile` o compilador tem
permissao para apaga-la.

Uso: audit_debug_markers.py --project <dir> [--json <out>] [--self-check]
Exit: 0 ok | 1 marcador sem volatile | 3 uso
"""
import sys, os, re, json, glob, argparse

# Declaracao com endereco fixo: captura a linha inteira para checar `volatile`.
AT_DECL = re.compile(r"^[^/\n]*\b__at\s*\(", re.M)

def check_source(texto, origem="<src>"):
    problems = []
    for n, linha in enumerate(texto.splitlines(), 1):
        s = linha.strip()
        if s.startswith("//") or s.startswith("*") or s.startswith("/*"):
            continue
        if not re.search(r"\b__at\s*\(", s):
            continue
        if re.search(r"\bvolatile\b", s):
            continue
        # __sfr __at(0x7F) e porta de I/O: o acesso nao e elidivel como memoria
        if "__sfr" in s:
            continue
        nome = re.search(r"__at\s*\([^)]*\)\s*(\w+)", s)
        nome = nome.group(1) if nome else s[:40]
        problems.append(
            f"{os.path.basename(origem)}:{n}: '{nome}' usa __at() sem volatile — "
            "o SDCC pode eliminar a escrita (marcador some e o diagnostico se "
            "inverte, L009)")
    return problems

def audit(project):
    problems = []
    for f in sorted(glob.glob(os.path.join(project, "src", "*.c")) +
                    glob.glob(os.path.join(project, "probes", "*.c"))):
        try:
            problems += check_source(open(f, encoding="utf-8",
                                          errors="replace").read(), f)
        except OSError as e:
            problems.append(f"{f}: ilegivel ({e})")
    return problems

def _self_check():
    # REPROVA marcador sem volatile
    p = check_source("unsigned char __at(0xC900) marcador;")
    assert p, "marcador sem volatile deveria reprovar"
    assert "volatile" in p[0]
    # APROVA com volatile
    assert not check_source("volatile unsigned char __at(0xC900) marcador;")
    # APROVA porta de I/O (__sfr nao e memoria elidivel)
    assert not check_source("__sfr __at(0x7F) PSGPort;")
    # comentario citando __at nao e declaracao
    assert not check_source("/* use __at(0xC900) para sondas */")
    assert not check_source("// marcador __at(0xC901) explicado aqui")
    print("[SELF-CHECK OK] debug_markers (reprova __at sem volatile; aceita "
          "volatile, __sfr e comentarios)")
    return 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--json", "--report-out", dest="json", help="new report destination; existing files are refused")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    problems = audit(a.project)
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
        print(f"[FAIL] {len(problems)} marcador(es) que o compilador pode apagar. "
              "Leitura deles nao e evidencia (L009).")
        return 1
    print("[PASS] marcadores de endereco fixo declarados como volatile")
    return 0

if __name__ == "__main__":
    sys.exit(main())
