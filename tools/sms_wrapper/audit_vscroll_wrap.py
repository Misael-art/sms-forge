#!/usr/bin/env python3
"""audit_vscroll_wrap.py — wrap do scroll Y no modo 192 (L131, SMS_GLOBAL §122).

Lei (corpus smspower.org/Development/Tilemap, hasheado): o registrador de
scroll vertical e lido uma unica vez por frame, antes da tilemap ser desenhada
— split vertical por reg9 nao existe. E: em modo 192 linhas a tilemap tem 224
px (28 linhas); valores escritos no reg de scroll Y maiores que 223 dao wrap
tratados como 0..31 — "setting the vertical scroll register to 240 is
equivalent to setting it to 16"; variaveis de scroll devem dar wrap em 224
"to avoid discontinuities". Em 224/240 a tilemap tem 256 px e valores
0..255 sao todos validos (o truncamento natural para 8 bits ja e o wrap).

O gate le o codigo-fonte do projeto contra o modo de tela DECLARADO
(--screen-h) e reprova a classe de defeito silenciosa: acumulador de scroll Y
em modo 192 sem wrap visivel em 224, ou literal >223 em modo 192 (o valor
pedido nao e o valor obtido).

Disciplina de medição (mesma de audit_tilemap_mirror.py / audit_tilemap_bounds.py):
  - literal decidido; acumulador com mutacao no mesmo arquivo sem token de
    wrap em 224 (modo 192) -> reprovado;
  - variavel sem mutacao no arquivo, expressao composta ou chamada de funcao
    -> NAO PROVADO, nunca aprovado;
  - o gate checa presenca de token de wrap (224/223) no arquivo, nao fluxo de
    dados: ausencia e reprovacao na classe-alvo; presenca nao prova correcao
    posicao-por-posicao. Runtime e telemetria do projeto.

Uso: audit_vscroll_wrap.py --screen-h 192|224|240 --source P [P..]
     [--json OUT] [--self-check]
Exit: 0 aprovado/nao_provado_estatico | 1 reprovado | 2 uso
"""
import sys, os, re, json, argparse, tempfile

WRAP_TOKENS_192 = re.compile(r"(%\s*224\b)|(>=\s*224\b)|(>\s*223\b)|(-=\s*224\b)|(==\s*224\b)")
CALL_RX = re.compile(r"SMS_setBGScrollY\s*\(\s*([^)]*)\s*\)")


def expand_source_paths(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += [os.path.join(r, f) for r, _, fs in os.walk(p)
                      for f in fs if f.endswith((".c", ".h"))]
        elif os.path.isfile(p):
            files.append(p)
        else:
            raise OSError("caminho inexistente: %s" % p)
    return sorted(files)


def parse_int(token):
    t = token.strip()
    try:
        return int(t, 16) if t.lower().startswith("0x") else int(t, 10)
    except ValueError:
        return None


def audit_file(path, screen_h):
    """Retorna (findings, unproven) para um arquivo-fonte."""
    findings, unproven = [], []
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return findings, unproven
    wrap_present = bool(WRAP_TOKENS_192.search(src)) if screen_h == 192 else False
    for m in CALL_RX.finditer(src):
        arg = m.group(1).strip()
        line = src.count("\n", 0, m.start()) + 1
        lit = parse_int(arg)
        if lit is not None:
            eff = lit & 0xFF            # truncamento para 8 bits na chamada
            if screen_h == 192 and eff > 223:
                eff = eff - 224          # wrap do hardware: tratado como 0..31
            if lit > 255 or (screen_h == 192 and (lit & 0xFF) > 223) \
                    or (screen_h != 192 and lit > 255):
                findings.append({"arquivo": path, "linha": line,
                                 "modo": "literal", "valor": lit,
                                 "erro": "valor %d: o registrador recebe %d — "
                                 "em modo 192 valores >223 da wrap tratado "
                                 "como 0..31; o pedido nao e o obtido"
                                 % (lit, eff)})
            continue
        if re.fullmatch(r"[A-Za-z_]\w*", arg):
            mutated = re.search(r"\b%s\s*(\+=|-=|=)" % re.escape(arg), src)
            if not mutated:
                unproven.append({"arquivo": path, "linha": line,
                                 "expressao": arg,
                                 "motivo": "variavel sem mutacao neste "
                                 "arquivo — outro TU ou runtime decide"})
                continue
            if screen_h == 192 and not wrap_present:
                findings.append({"arquivo": path, "linha": line,
                                 "modo": "acumulador", "variavel": arg,
                                 "erro": "acumulador de scroll Y em modo 192 "
                                 "sem token de wrap em 224 no arquivo — "
                                 "descontinuidade a cada volta da tilemap"})
            continue
        unproven.append({"arquivo": path, "linha": line, "expressao": arg,
                         "motivo": "argumento nao decidivel estaticamente "
                         "(expressao ou chamada)"})
    return findings, unproven


def audit(source, screen_h):
    report = {"screen_h": screen_h, "findings": [], "unproven": [],
              "verdict": "aprovado"}
    for p in expand_source_paths(source):
        f, u = audit_file(p, screen_h)
        report["findings"] += f
        report["unproven"] += u
    if report["findings"]:
        report["verdict"] = "reprovado_scroll_y_sem_wrap"
    elif report["unproven"]:
        report["verdict"] = "nao_provado_estatico"
    return report


def self_check():
    ok = True
    def check(label, cond):
        nonlocal ok
        print(("  [OK] " if cond else "  [XX] ") + label)
        ok = ok and cond
    with tempfile.TemporaryDirectory(prefix="vscroll_selfcheck_") as tmp:
        def w(name, text):
            p = os.path.join(tmp, name)
            open(p, "w").write(text)
            return p
        bad = w("bad.c",
                "unsigned char scY;\n"
                "void scroll(void){ scY += 4; SMS_setBGScrollY(scY); }\n")
        check("192: acumulador sem wrap reprovado",
              audit([bad], 192)["verdict"] == "reprovado_scroll_y_sem_wrap")
        good = w("good.c",
                 "unsigned char scY;\n"
                 "void scroll(void){ scY += 4; if (scY >= 224) scY -= 224;"
                 " SMS_setBGScrollY(scY); }\n")
        check("192: wrap em 224 aprovado",
              audit([good], 192)["verdict"] == "aprovado")
        lit_bad = w("litbad.c", "void f(void){ SMS_setBGScrollY(240); }\n")
        r = audit([lit_bad], 192)
        check("192: literal 240 reprovado (trata como 16)",
              r["verdict"] == "reprovado_scroll_y_sem_wrap" and r["findings"])
        r224 = audit([lit_bad], 224)
        check("224: literal 240 aprovado (tilemap de 256 px)",
              r224["verdict"] == "aprovado")
        expr = w("expr.c",
                 "unsigned char GetY(void);\n"
                 "void f(void){ SMS_setBGScrollY(GetY()); }\n")
        r = audit([expr], 192)
        check("192: chamada de funcao = nao_provado_estatico, nunca aprovado",
              r["verdict"] == "nao_provado_estatico" and r["unproven"]
              and not r["findings"])
        extern = w("ext.c", "extern unsigned char cam_y;\n"
                   "void f(void){ SMS_setBGScrollY(cam_y); }\n")
        r = audit([extern], 192)
        check("192: variavel sem mutacao no arquivo = nao provado",
              r["verdict"] == "nao_provado_estatico" and r["unproven"])
        trunc = w("tr.c", "void f(void){ SMS_setBGScrollY(300); }\n")
        check("literal >255 reprovado em qualquer modo",
              audit([trunc], 224)["verdict"] == "reprovado_scroll_y_sem_wrap")
        none = w("none.c", "int main(void){ return 0; }\n")
        check("arquivo sem call = aprovado vazio (silencio nao e prova)",
              audit([none], 192)["verdict"] == "aprovado")
    print("SELFCHECK audit_vscroll_wrap.py: " + ("VERDE" if ok else "VERMELHO"))
    return 0 if ok else 1


def main():
    if "--self-check" in sys.argv:
        sys.exit(self_check())
    ap = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]))
    ap.add_argument("--screen-h", type=int, required=True,
                    choices=[192, 224, 240])
    ap.add_argument("--source", nargs="+", required=True, metavar="P")
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args()
    try:
        report = audit(args.source, args.screen_h)
    except OSError as e:
        print("erro: %s" % e, file=sys.stderr)
        sys.exit(2)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json:
        open(args.json, "w", encoding="utf-8").write(text + "\n")
    print(text)
    sys.exit(1 if report["verdict"] == "reprovado_scroll_y_sem_wrap" else 0)


if __name__ == "__main__":
    main()
