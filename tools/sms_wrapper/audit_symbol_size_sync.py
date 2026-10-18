#!/usr/bin/env python3
"""audit_symbol_size_sync.py — tamanho de asset nao se escreve em dois lugares (L052).

O consumidor leu fight_gfx.h (1024) enquanto a folha ja tinha 832 B: o
streamer leu 192 B alem do array. Sem sintoma visivel. Este gate confere
#define NOME_SIZE contra o array e contra o mesmo define em outro header.

Uso:
  audit_symbol_size_sync.py --project DIR
  audit_symbol_size_sync.py --self-check
Exit: 0 ok/skip | 1 diverge | 3 uso
"""
import argparse, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEF_SIZE = re.compile(r"#define\s+([A-Z][A-Z0-9_]*_SIZE)\s+(\d+)")
# `const unsigned char KEN_IDLE_TILES[832]` (declarations only)
ARRAY_DECL = re.compile(
    r"\b(?:(?:static|extern)\s+)*(?:const\s+)?"
    r"(?:unsigned\s+|signed\s+)?(?:char|short|int|long|uint8_t|int8_t|"
    r"uint16_t|int16_t)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\[\s*(\d+)\s*\]"
)
ALIAS = re.compile(r"^#define\s+([A-Za-z_][A-Za-z0-9_]*)\s+"
                   r"([A-Za-z_][A-Za-z0-9_]*)\s*$", re.M)


def _sources(project):
    out = []
    for sub in ("src", "inc"):
        d = os.path.join(project, sub)
        if not os.path.isdir(d):
            continue
        for dirpath, _, files in os.walk(d):
            for fn in files:
                if fn.endswith((".c", ".h")):
                    out.append(os.path.join(dirpath, fn))
    return out


def _macro_to_array(macro):
    return macro[:-5] if macro.endswith("_SIZE") else macro


def audit_project(project):
    macros = {}   # name -> [(file, value)]
    arrays = {}   # name -> [(file, value)]
    aliases = {}  # symbol -> [(file, target)]
    problems = []
    files = _sources(project)
    if not files:
        return [], "skip: sem src/inc"
    for src in files:
        try:
            text = open(src, encoding="utf-8", errors="replace").read()
        except OSError as e:
            problems.append(f"{src}: ilegivel ({e})")
            continue
        rel = os.path.relpath(src, project)
        for m in DEF_SIZE.finditer(text):
            macros.setdefault(m.group(1), []).append((rel, int(m.group(2))))
        for m in ARRAY_DECL.finditer(text):
            name, n = m.group(1), int(m.group(2))
            arrays.setdefault(name, []).append((rel, n))
        for m in ALIAS.finditer(text):
            aliases.setdefault(m.group(1), []).append((rel, m.group(2)))
    for name, occs in macros.items():
        vals = {v for _, v in occs}
        if len(vals) > 1:
            detalhe = ", ".join(f"{f}={v}" for f, v in occs)
            problems.append(
                f"{name} diverge entre headers ({detalhe}) (L052)")
        want = next(iter(vals))
        arr = _macro_to_array(name)
        candidates = (arr, arr.lower())
        target = next((candidate for candidate in candidates
                       if candidate in aliases), None)
        if target is not None:
            targets = {value for _, value in aliases[target]}
            if len(targets) > 1:
                detail = ", ".join(f"{f}={value}" for f, value in aliases[target])
                problems.append(f"{target} alias diverge ({detail}) (L052)")
            target = next(iter(targets))
            seen = {arr}
            while target in aliases:
                if target in seen:
                    problems.append(f"{name} participa de ciclo de aliases (L052)")
                    target = None
                    break
                seen.add(target)
                target_values = {value for _, value in aliases[target]}
                if len(target_values) != 1:
                    problems.append(f"{target} alias diverge entre destinos (L052)")
                    target = None
                    break
                target = next(iter(target_values))
        if target is not None:
            arr = target
        elif arr not in arrays:
            # Legacy assets often use lower-case C names with upper-case macros.
            arr = arr.lower()
        if arr in arrays:
            for f, n in arrays[arr]:
                if n != want:
                    problems.append(
                        f"{name}={want} mas {arr}[{n}] em {f} (L052)")
    return problems, None


def _self_check():
    d = tempfile.mkdtemp(prefix="smssz_")
    try:
        inc = os.path.join(d, "inc")
        os.makedirs(inc)
        open(os.path.join(inc, "leaf.h"), "w").write(
            "#define KEN_IDLE_TILES_SIZE 832\n"
            "const unsigned char ken_idle_tiles[832] = {0};\n")
        open(os.path.join(inc, "gfx.h"), "w").write(
            "#define KEN_IDLE_TILES_SIZE 832\n")
        p, _ = audit_project(d)
        assert not p, f"match nao deveria reprovar: {p}"

        open(os.path.join(inc, "gfx.h"), "w").write(
            "#define KEN_IDLE_TILES_SIZE 1024\n")
        p, _ = audit_project(d)
        assert any("diverge" in x or "1024" in x for x in p), \
            f"faltou pegar 1024 vs 832: {p}"

        open(os.path.join(inc, "gfx.h"), "w").write(
            "#define KEN_IDLE_TILES_SIZE 832\n")
        open(os.path.join(inc, "alias.h"), "w").write(
            "#define KEN_IDLE_META_SIZE 4\n"
            "#define KEN_IDLE_META ken_idle_meta_canonical\n"
            "const unsigned char ken_idle_meta_canonical[4] = {0};\n")
        p, _ = audit_project(d)
        assert not p, f"alias exato deveria passar: {p}"
        open(os.path.join(inc, "alias.h"), "w").write(
            "#define KEN_IDLE_META_SIZE 5\n"
            "#define KEN_IDLE_META ken_idle_meta_canonical\n"
            "const unsigned char ken_idle_meta_canonical[4] = {0};\n")
        p, _ = audit_project(d)
        assert any("KEN_IDLE_META_SIZE=5" in x for x in p), \
            f"divergencia no alias deveria falhar: {p}"

        e = tempfile.mkdtemp(prefix="smssz2_")
        try:
            os.makedirs(os.path.join(e, "src"))
            p, skip = audit_project(e)
            assert not p
        finally:
            shutil.rmtree(e, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] symbol_size_sync (match passa, 1024 vs 832 reprova)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    if not a.project:
        print("[FAIL] --project obrigatorio (ou --self-check)", file=sys.stderr)
        return 3
    problems, skip = audit_project(os.path.abspath(a.project))
    if skip and not problems:
        print(f"[PASS] {skip}")
        return 0
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} tamanho(s) duplicado(s) divergente(s) (L052).")
        return 1
    print("[PASS] tamanhos de simbolo coerentes entre define e array")
    return 0


if __name__ == "__main__":
    sys.exit(main())
