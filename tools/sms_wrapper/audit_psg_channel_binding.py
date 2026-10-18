#!/usr/bin/env python3
"""audit_psg_channel_binding.py — SFX toca no canal autorado (L041/§12).

make_psg_assets declara o canal no manifesto. PSGSFXPlay/psg_sfx com literal
de canal diferente derruba o mix; cooldown nao recupera.

Sem manifesto o projeto e SKIP (nao ha o que amarrar). Simbolo tocado com
canal em variavel nao e aprovado em silencio: vira 'nao provado'.

Uso:
  audit_psg_channel_binding.py --project DIR
  audit_psg_channel_binding.py --self-check
Exit: 0 ok/skip | 1 mismatch | 3 uso
"""
import argparse, json, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ANY_PLAY = re.compile(
    r"(?:PSGSFXPlay(?:Loop)?|psg_sfx)\s*\(\s*(?:\(void\s*\*\)\s*)?(\w+)\s*,\s*"
    r"([^()]*)\)"
)


def _norm_mask(ch):
    return "|".join(sorted(t.strip() for t in str(ch).split("|")))


def _literal_mask(arg):
    toks = [t.strip() for t in arg.split("|")]
    return bool(arg) and all(
        re.fullmatch(r"SFX_CHANNEL[A-Z0-9]+", t) for t in toks if t)


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


def _manifest_channels(project):
    path = os.path.join(project, "doc", "audio_provenance_manifest.json")
    if not os.path.isfile(path):
        return None, path
    d = json.load(open(path, encoding="utf-8"))
    mapping = {}
    for a in d.get("assets") or []:
        ch = a.get("channels") or ""
        if not str(ch).startswith("SFX_"):
            continue
        ident = os.path.splitext(os.path.basename(a.get("file") or ""))[0]
        if ident:
            mapping[ident] = ch
    return mapping, path


def audit_project(project):
    problems = []
    mapping, path = _manifest_channels(project)
    if mapping is None:
        return [], f"skip: sem {os.path.relpath(path, project)}"
    if not mapping:
        return [], "skip: manifesto sem SFX com canal"
    for src in _sources(project):
        try:
            text = open(src, encoding="utf-8", errors="replace").read()
        except OSError as e:
            problems.append(f"{src}: ilegivel ({e})")
            continue
        rel = os.path.relpath(src, project)
        for m in ANY_PLAY.finditer(text):
            symbol, arg = m.group(1), m.group(2).strip()
            want = mapping.get(symbol)
            if not want:
                continue
            if _literal_mask(arg):
                if _norm_mask(arg) != _norm_mask(want):
                    problems.append(
                        f"{rel}: {symbol} tocado em {_norm_mask(arg)}, "
                        f"manifesto autorou {_norm_mask(want)} (L041)")
            else:
                problems.append(
                    f"{rel}: {symbol} tocado com canal nao literal "
                    f"('{arg}') — nao provado (L041)")
    return problems, None


def _self_check():
    d = tempfile.mkdtemp(prefix="smspsgch_")
    try:
        os.makedirs(os.path.join(d, "doc"))
        os.makedirs(os.path.join(d, "src"))
        json.dump({"assets": [
            {"file": "res/audio/sfx_shot.psg", "channels": "SFX_CHANNEL2"},
            {"file": "res/audio/sfx_hit.psg", "channels": "SFX_CHANNELS2AND3"},
            {"file": "res/audio/sfx_fight.psg",
             "channels": "SFX_CHANNEL1|SFX_CHANNEL2|SFX_CHANNEL3"},
        ]}, open(os.path.join(d, "doc", "audio_provenance_manifest.json"), "w"))
        open(os.path.join(d, "src", "ok.c"), "w").write(
            "PSGSFXPlay((void *)sfx_shot, SFX_CHANNEL2);\n"
            "PSGSFXPlay((void *)sfx_hit, SFX_CHANNELS2AND3);\n"
            "PSGSFXPlay((void *)sfx_fight,\n"
            "           SFX_CHANNEL3 | SFX_CHANNEL1 | SFX_CHANNEL2);\n")
        p, _ = audit_project(d)
        assert not p, f"match nao deveria reprovar: {p}"

        open(os.path.join(d, "src", "bad.c"), "w").write(
            "PSGSFXPlay((void *)sfx_shot, SFX_CHANNEL3);\n"
            "PSGSFXPlay((void *)sfx_fight, SFX_CHANNEL1 | chan);\n"
            "psg_sfx(sfx_hit, SFX_CHANNEL2);\n")
        p, _ = audit_project(d)
        assert any("sfx_shot" in x and "SFX_CHANNEL3" in x for x in p), \
            f"faltou mismatch L041: {p}"
        assert any("sfx_fight" in x and "nao literal" in x for x in p), \
            f"faltou escape mascara+variavel: {p}"
        assert any("sfx_hit" in x and "SFX_CHANNEL2" in x for x in p), \
            f"faltou mismatch contra composto: {p}"

        e = tempfile.mkdtemp(prefix="smspsgch2_")
        try:
            os.makedirs(os.path.join(e, "src"))
            p, skip = audit_project(e)
            assert skip and skip.startswith("skip:"), f"sem manifesto deveria skip: {skip}"
            assert not p
        finally:
            shutil.rmtree(e, ignore_errors=True)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] psg_channel_binding (match passa, canal errado reprova, "
          "sem manifesto skip)")
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
        print(f"[FAIL] {len(problems)} SFX fora do canal autorado (L041).")
        return 1
    print("[PASS] SFX no canal autorado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
