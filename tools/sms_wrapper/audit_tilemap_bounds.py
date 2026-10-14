#!/usr/bin/env python3
"""audit_tilemap_bounds.py — escrita na name table fora da area RENDERIZADA.

Licao L011: "VITORIA!" escrito na linha 26 nunca apareceu. Nao era bug de
fonte nem de paleta: XYtoADDR e aritmetica pura, sem checagem de limite.

    #define SMS_PNTAddress  0x3800
    #define XYtoADDR(x,y)   (SMS_PNTAddress|((((y)<<5)+(x))<<1))

A PNT ocupa 28 linhas x 32 colunas x 2 bytes = 0x700 -> 0x3800..0x3EFF.
O modo 192 linhas renderiza apenas as linhas 0..23. Daí duas falhas
diferentes que a lição tratava como uma:

  y em 24..27  -> INVISIVEL. Escreve na cauda nao renderizada da PNT.
                  Nada quebra, nada aparece. Foi este o caso da L011.
  y >= 28      -> CORROMPE. Ultrapassa 0x3EFF e cai em 0x3F00, que e a
                  SAT. Escrever "texto" ali reposiciona sprites.
  x >= 32      -> VAZA PARA A LINHA SEGUINTE. O <<5 nao satura; x=33 na
                  linha 3 e o mesmo endereco que x=1 na linha 4.

So julga coordenada LITERAL (ou #define que resolve para literal). Coordenada
vinda de variavel nao e decidivel estaticamente e e reportada como nao provada,
nunca como aprovada.

Segundo eixo (L132): a ENTRADA de tilemap e uma palavra de 16 bits — bits 0-8
indice, 9-12 flip X/Y, subpaleta de sprite e prioridade. Bits 13-15 sao
"Unused" para o VDP: "Some games use these bits as flags for collision and
damage zones" (smspower.org/Development/Tilemap, hasheado no corpus). O gate
reprova literal de entrada com bits 13-15 ($2000/$4000/$8000) armados, porque
o padrao do canon e vedado; uso intencional exige --allow-tilemap-flags com
motivo, declarado no TDD/spec-cenas do projeto. Tile vinda de variavel ou
expressao e nao provada, nunca aprovada. So checa as chamadas diretas
(SMS_setTileatXY / SMS_setNextTileatXY); wrapper de projeto e arrays do
conversor de mapa ficam fora deste eixo.

Uso: audit_tilemap_bounds.py <arquivo.c|dir> [...] [--self-check]
     [--allow-tilemap-flags "motivo"]
Exit: 0 aprovado | 1 reprovado | 2 erro de uso
"""
import sys, os, re, argparse

VISIBLE_ROWS_192 = 24   # modo padrao: 192 linhas / 8 = 24
VISIBLE_ROWS_224 = 28   # SMS II, com VDPFEATURE_EXTRAHEIGHT + 224LINES
PNT_ROWS = 28           # capacidade fisica da name table (0x3800..0x3EFF)
COLS = 32

# macro -> indice do argumento que carrega a altura (None = 1 linha so)
XY_MACROS = {
    "SMS_setTileatXY": None,
    "SMS_setNextTileatXY": None,
    "SMS_printatXY": None,
    "SMS_loadTileMapArea": 4,     # (x,y,src,width,height)
    "SMS_loadTileMapColumn": 3,   # (x,y,src,height)
}

def _split_args(s):
    """Divide argumentos no nivel 0 de parenteses/colchetes."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([": depth += 1
        elif ch in ")]": depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip()); cur = ""
        else:
            cur += ch
    if cur.strip(): out.append(cur.strip())
    return out

def _calls(src, macro):
    """Extrai a lista de argumentos de cada chamada da macro, com o offset."""
    for m in re.finditer(r"\b" + re.escape(macro) + r"\s*\(", src):
        i, depth = m.end() - 1, 0
        for j in range(i, len(src)):
            if src[j] in "([": depth += 1
            elif src[j] in ")]":
                depth -= 1
                if depth == 0:
                    yield m.start(), _split_args(src[i + 1:j])
                    break

def defines(src):
    """#define NAME <inteiro literal> — unica substituicao que arriscamos."""
    d = {}
    for name, val in re.findall(r"^\s*#\s*define\s+(\w+)\s+(.+?)\s*$", src, re.M):
        v = val.split("//")[0].split("/*")[0].strip()
        try:
            d[name] = int(v, 0)
        except ValueError:
            pass
    return d

def literal(expr, defs):
    """Resolve expr para int se for literal puro ou #define; senao None."""
    e = expr.strip().strip("()").strip()
    try:
        return int(e, 0)
    except ValueError:
        pass
    if e in defs:
        return defs[e]
    # soma/subtracao de literais e defines: "BASE+2"
    m = re.fullmatch(r"([\w]+|\d+)\s*([+-])\s*(\d+)", e)
    if m:
        left = literal(m.group(1), defs)
        if left is not None:
            return left + int(m.group(3)) if m.group(2) == "+" else left - int(m.group(3))
    return None

def wrappers(src, base):
    """Macros do projeto que so repassam coordenadas para uma macro XY.

    O laboratorio define `putat(x,y,s) SMS_printatXY((x),(y),...)`. Sem seguir
    isso o gate ve `y='(y)'` e declara tudo indecidivel — cego exatamente no
    codigo que a L011 quebrou. So segue repasse POSICIONAL direto: se a coord
    passada adiante nao for um parametro nu, nao inventa.
    """
    found = {}
    for name, params, body in re.findall(
            r"^\s*#\s*define\s+(\w+)\s*\(([^)]*)\)\s*(.+?)\s*$", src, re.M):
        plist = [p.strip() for p in params.split(",") if p.strip()]
        for macro, hidx in base.items():
            for _, args in _calls(body, macro):
                if len(args) < 2:
                    continue
                xi = _param_index(args[0], plist)
                yi = _param_index(args[1], plist)
                if xi is None or yi is None:
                    continue
                hi = None
                if hidx is not None and len(args) > hidx:
                    hi = _param_index(args[hidx], plist)
                    if hi is None:
                        continue
                found[name] = (xi, yi, hi)
    return found

def _param_index(expr, plist):
    e = expr.strip()
    while e.startswith("(") and e.endswith(")"):
        e = e[1:-1].strip()
    return plist.index(e) if e in plist else None

def visible_rows(src):
    """224 linhas so conta se o codigo LIGA o modo; caso contrario 192."""
    if re.search(r"VDPFEATURE_224LINES|VDPFEATURE_EXTRAHEIGHT", src):
        return VISIBLE_ROWS_224
    return VISIBLE_ROWS_192

# --- segundo eixo (L132/§123): VALOR da entrada de tilemap, não coordenada ---
# smspower.org/Development/Tilemap: bits 13-15 "Unused" — "Some games use these
# bits as flags for collision and damage zones". O VDP os ignora; o canon veda
# por padrão para não colidir com metasprites/pools/conversores.
TILE_WORD_ARGS = {"SMS_setTileatXY": 2}   # macro -> arg com a palavra de 16 bits
FLAG_MASK_13_15 = 0xE000
FLAG_BIT_NAMES = (0x2000, 0x4000, 0x8000)

def check_tile_values(src, path="<mem>", allow_flags=False):
    """Funcao PURA. Entrada de tilemap literal com bits 13-15 armados.

    Mesma disciplina do eixo de coordenadas: so literal decide; expressao ou
    variavel e indecidivel estatico, reportada como nao provada. Com
    allow_flags o achado vira excecao declarada — aprovacao com lastro.
    """
    defs = defines(src)
    body = re.sub(r"^[ \t]*#[ \t]*define[ \t]+\w+(?:\([^)\n]*\))?",
                  lambda m: " " * len(m.group(0)), src, flags=re.M)
    fails, unknown, declared = [], [], []
    for macro, tix in TILE_WORD_ARGS.items():
        for off, args in _calls(body, macro):
            if len(args) <= tix:
                continue
            ln = body.count("\n", 0, off) + 1
            tv = literal(args[tix], defs)
            if tv is None:
                unknown.append((path, ln, macro,
                                f"tile='{args[tix]}' nao literal: entrada de "
                                f"16 bits nao decidivel estaticamente"))
                continue
            if tv & FLAG_MASK_13_15:
                bits = "/".join(f"${b:04X}" for b in FLAG_BIT_NAMES if tv & b)
                fails_or_decl = ((path, ln, macro,
                                  f"entrada 0x{tv:04X} arma bits 13-15 ({bits}): "
                                  f"o VDP ignora esses bits e o canon os veda por "
                                  f"padrao — uso intencional exige declaracao no "
                                  f"TDD + --allow-tilemap-flags (L132/§123)"))
                (declared if allow_flags else fails).append(fails_or_decl)
    return fails, unknown, declared

def line_of(src, off):
    return src.count("\n", 0, off) + 1

def check_source(src, path="<mem>"):
    """Funcao PURA. Retorna (falhas, indecidiveis) — testavel sem projeto."""
    defs = defines(src)
    rows = visible_rows(src)
    # tabela unificada: nome -> (indice de x, indice de y, indice da altura)
    table = {m: (0, 1, h) for m, h in XY_MACROS.items()}
    table.update(wrappers(src, XY_MACROS))
    # Apaga so o CABECALHO `#define NOME(params)` — `putat(x,y,s)` nao e uma
    # chamada. O CORPO continua sob analise: coordenada literal cravada dentro
    # de uma macro erra igual, e nao pode escapar por morar num #define.
    macro_lines = set()
    def _blank(m):
        macro_lines.add(src.count("\n", 0, m.start()) + 1)
        return " " * len(m.group(0))
    body = re.sub(r"^[ \t]*#[ \t]*define[ \t]+\w+(?:\([^)\n]*\))?", _blank,
                  src, flags=re.M)
    fails, unknown = [], []
    for macro, (xi, yi, hidx) in table.items():
        for off, args in _calls(body, macro):
            if len(args) <= max(xi, yi):
                continue
            ln = line_of(body, off)
            x = literal(args[xi], defs)
            y = literal(args[yi], defs)
            h = 1
            if hidx is not None and len(args) > hidx:
                hv = literal(args[hidx], defs)
                if hv is None:
                    unknown.append((path, ln, macro, "altura nao literal"))
                    continue
                h = hv
            if y is None:
                # dentro do corpo de uma macro a coordenada e do CHAMADOR;
                # reportar aqui seria contar o mesmo caso duas vezes
                if ln not in macro_lines:
                    unknown.append((path, ln, macro, f"y='{args[yi]}' nao literal"))
                continue
            last = y + h - 1
            if last >= PNT_ROWS:
                fails.append((path, ln, macro,
                              f"y={y}..{last} passa de {PNT_ROWS - 1}: sai da PNT "
                              f"e escreve em 0x3F00 (SAT) — corrompe sprites"))
            elif last >= rows:
                fails.append((path, ln, macro,
                              f"y={y}..{last} fora das {rows} linhas renderizadas: "
                              f"escreve na cauda da PNT — INVISIVEL (L011)"))
            if x is None:
                unknown.append((path, ln, macro, f"x='{args[xi]}' nao literal"))
            elif x >= COLS:
                fails.append((path, ln, macro,
                              f"x={x} >= {COLS}: XYtoADDR nao satura, vaza para "
                              f"a linha seguinte"))
            elif x < 0 or y < 0:
                fails.append((path, ln, macro, f"coordenada negativa ({x},{y})"))
    return fails, unknown

SC_OK = """
#define ROW_STATUS 3
void f(void){
  SMS_printatXY(2, ROW_STATUS, "VITORIA");
  SMS_setTileatXY(31, 23, 5);
  SMS_loadTileMapArea(0, 0, map, 32, 24);
}
"""
SC_INVISIBLE = """
void f(void){ SMS_printatXY(2, 26, "VITORIA! 1:REINICIA"); }
"""
SC_SAT = """
void f(void){ SMS_setTileatXY(0, 29, 7); }
"""
SC_COL = """
void f(void){ SMS_setTileatXY(33, 3, 7); }
"""
SC_AREA = """
void f(void){ SMS_loadTileMapArea(0, 20, map, 32, 6); }
"""
SC_224 = """
void g(void){ SMS_VDPturnOnFeature(VDPFEATURE_224LINES); }
void f(void){ SMS_printatXY(2, 26, "ok em 224"); }
"""
SC_VAR = """
void f(unsigned char r){ SMS_printatXY(2, r, "?"); }
"""
# o caso real do laboratorio: a coordenada literal esta no CALLER do wrapper
SC_WRAPPER = """
#define putat(x,y,s)  SMS_printatXY((x),(y),(const unsigned char *)(s))
void f(void){ putat(2, 26, "VITORIA!"); }
"""
SC_WRAPPER_OK = """
#define putat(x,y,s)  SMS_printatXY((x),(y),(const unsigned char *)(s))
void f(void){ putat(2, 3, "VITORIA!"); }
"""
# wrapper que NAO repassa posicionalmente: nao inventar mapeamento
SC_WRAPPER_FIXED = """
#define status(s)  SMS_printatXY(2, 26, (s))
void f(void){ status("x"); }
"""

# --- eixo de VALOR da entrada (L132) ---
SC_FLAG_ON = """
void f(void){ SMS_setTileatXY(2, 3, 0x2041); }
"""
# 0x1E41 = flip X|Y + subpaleta sprite + prioridade + indice 0x41: todos os
# flags CANONICOS (bits 9-12) ligados — nao e flag custom, nao pode reprovar
SC_FLAG_CANON = """
void f(void){ SMS_setTileatXY(2, 3, 0x1E41); SMS_setTileatXY(1, 1, 42); }
"""
SC_FLAG_EXPR = """
void f(unsigned int t){ SMS_setTileatXY(2, 3, t | 0x8000); }
"""

def self_check():
    f, u = check_source(SC_OK)
    assert not f, f"codigo dentro dos limites nao pode reprovar: {f}"
    assert not u, f"tudo literal, nao deveria haver indecidivel: {u}"

    f, _ = check_source(SC_INVISIBLE)
    assert len(f) == 1 and "INVISIVEL" in f[0][3], f"linha 26 tem de reprovar: {f}"

    f, _ = check_source(SC_SAT)
    assert len(f) == 1 and "SAT" in f[0][3], f"y=29 tem de acusar SAT: {f}"

    f, _ = check_source(SC_COL)
    assert len(f) == 1 and "x=33" in f[0][3], f"x=33 tem de reprovar: {f}"

    # area que COMECA valida e TERMINA fora: y=20 + altura 6 -> ultima linha 25
    f, _ = check_source(SC_AREA)
    assert len(f) == 1 and "y=20..25" in f[0][3], f"altura tem de entrar na conta: {f}"

    # 224 linhas: a MESMA linha 26 passa a ser legitima
    f, _ = check_source(SC_224)
    assert not f, f"em 224 linhas a linha 26 e visivel: {f}"

    # coordenada em variavel: nao provada, nunca aprovada em silencio
    f, u = check_source(SC_VAR)
    assert not f and len(u) == 1, f"y variavel deve virar indecidivel, nao falha: {f} {u}"

    # o caso real: a coordenada mora no CALLER do wrapper do projeto
    f, u = check_source(SC_WRAPPER)
    assert len(f) == 1 and "INVISIVEL" in f[0][3], f"wrapper tem de ser seguido: {f} {u}"
    assert not u, f"wrapper resolvido nao pode deixar residuo indecidivel: {u}"
    f, _ = check_source(SC_WRAPPER_OK)
    assert not f, f"wrapper com linha valida nao pode reprovar: {f}"

    # coordenada literal cravada DENTRO da macro nao escapa por morar num #define
    f, _ = check_source(SC_WRAPPER_FIXED)
    assert len(f) == 1 and "INVISIVEL" in f[0][3], f"literal dentro do #define escapou: {f}"

    # --- eixo de VALOR da entrada de tilemap (bits 13-15, L132) ---
    vf, vu, vd = check_tile_values(SC_FLAG_ON)
    assert len(vf) == 1 and "bits 13-15" in vf[0][3], f"bit 13 armado deve reprovar: {vf}"
    assert not vu and not vd, f"literal sem excecao nao deixa residuo: {vu} {vd}"

    # excecao declarada: mesmo achado vira approved-com-lastro, nunca silencio
    vf, _, vd = check_tile_values(SC_FLAG_ON, allow_flags=True)
    assert not vf and len(vd) == 1, f"com --allow-tilemap-flags o achado vira excecao: {vf} {vd}"

    # flags CANONICOS (bits 9-12) nao sao flags custom: nao podem reprovar
    vf, vu, vd = check_tile_values(SC_FLAG_CANON)
    assert not vf and not vu and not vd, f"0x1E41 so usa bits 0-12, deve passar limpo: {vf}{vu}{vd}"

    # tile vinda de expressao/variavel: nao provada, nunca aprovada em silencio
    vf, vu, vd = check_tile_values(SC_FLAG_EXPR)
    assert not vf and len(vu) == 1, f"tile='t|0x8000' nao literal deve ser indecidivel: {vf} {vu}"

    print("[SELF-CHECK OK] audit_tilemap_bounds (reprova linha invisivel, "
          "escrita na SAT, coluna >=32 e altura que estoura; aprova 224 linhas; "
          "segue macro-wrapper do projeto; coordenada variavel vira indecidivel; "
          "bits 13-15 da entrada reprovam sem declaracao, viram excecao com "
          "--allow-tilemap-flags, flags canonicos 9-12 passam, tile nao literal "
          "e indecidivel)")
    return 0

def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                out += [os.path.join(root, f) for f in files if f.endswith((".c", ".h"))]
        elif p.endswith((".c", ".h")):
            out.append(p)
    return sorted(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--allow-tilemap-flags", metavar="MOTIVO",
                    help=("projeto declara uso intencional dos bits 13-15 da "
                          "tilemap como flags proprios (deve constar no TDD)"))
    a = ap.parse_args()
    if a.self_check:
        return self_check()
    if a.allow_tilemap_flags is not None and not a.allow_tilemap_flags.strip():
        print("[ERRO] --allow-tilemap-flags exige MOTIVO nao vazio", file=sys.stderr)
        return 2
    allow = a.allow_tilemap_flags is not None
    files = collect(a.paths)
    if not files:
        print("[ERRO] nenhum .c/.h informado", file=sys.stderr)
        return 2
    fails, unknown, declared = [], [], []
    for f in files:
        try:
            src = open(f, encoding="utf-8", errors="replace").read()
        except OSError as e:
            print(f"[ERRO] {f}: {e}", file=sys.stderr)
            return 2
        a_, b_ = check_source(src, f)
        c_, d_, e_ = check_tile_values(src, f, allow)
        fails += a_ + c_; unknown += b_ + d_; declared += e_
    for path, ln, macro, why in unknown:
        print(f"  [nao provado] {path}:{ln} {macro} — {why}")
    for path, ln, macro, why in declared:
        print(f"  [excecao declarada] {path}:{ln} {macro} — {why}")
    for path, ln, macro, why in fails:
        print(f"  [REPROVA] {path}:{ln} {macro} — {why}")
    if fails:
        print(f"[FAIL] {len(fails)} escrita(s) ilegal na name table "
              f"(coordenada fora da area util L011 ou bits 13-15 L132)")
        return 1
    print(f"[OK] audit_tilemap_bounds: {len(files)} arquivo(s), nenhuma escrita "
          f"ilegal na name table ({len(unknown)} coordenada(s)/entrada(s) "
          f"nao provada(s), {len(declared)} entrada(s) sob excecao declarada)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
