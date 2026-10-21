#!/usr/bin/env python3
"""gen_scene_tables.py — tabelas de cena DERIVADAS das partituras (dado, nao
runtime, roteiro cena03). Emite inc/scene_tables.h com:
  - frames de loop e de compasso por faixa (revelacao/prompt/medidor/flash);
  - frames de ataque do lead de dawn (ressonancia de cristal, cena 02);
  - frames de hit de ch3 de storm (flash de reampa sinc, cena 03).

Regra do projeto: composicao mora na partitura JSON; o que a cena le do
"quando" vem desta deriva deterministica, com sha256 da fonte no cabeecalho.
Byte-exact entre execucoes: nenhum relogio, nenhuma aleatoriedade.

Uso:
  python3 tools/gen_scene_tables.py            # escreve inc/scene_tables.h
  python3 tools/gen_scene_tables.py --self-check
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gen_pulso_music as g  # noqa: E402  (mesma aritmetica de frames do emissor)

FAIXAS = ("music_title", "music_dawn", "music_storm", "music_eco")


def load(nome):
    path = os.path.join(HERE, "partitura", nome + ".json")
    with open(path, "rb") as fh:
        raw = fh.read()
    return json.loads(raw.decode("utf-8")), hashlib.sha256(raw).hexdigest()


def frames_loop(part):
    fp = g.frames_por_passo(part["meta"])
    return fp, len(part["compassos"]) * 16 * fp


def dawn_attacks(part):
    fp, total = frames_loop(part)
    atks = []
    for bi, bar in enumerate(part["compassos"]):
        for mel in bar.get("melodia", ()):
            f = bi * 16 * fp + mel[0] * fp
            if f not in atks:
                atks.append(f)
    return sorted(atks), total


def storm_hits(part):
    fp, total = frames_loop(part)
    hits = []
    for bi, bar in enumerate(part["compassos"]):
        for pos, _tipo in bar.get("percussao", ()):
            hits.append(bi * 16 * fp + pos * fp)
    return sorted(hits), total


def render():
    metas, sha = {}, {}
    for n in FAIXAS:
        part, digest = load(n)
        sha[n] = digest
        fp, loop = frames_loop(part)
        metas[n] = {"fp": fp, "loop": loop, "part": part}
    da, dl = dawn_attacks(metas["music_dawn"]["part"])
    sh, sl = storm_hits(metas["music_storm"]["part"])
    out = []
    out.append("/* gerado por tools/gen_scene_tables.py — NAO EDITAR. Edite a")
    out.append(" * partitura JSON e regenere. Composicao mora na partitura;")
    out.append(" * isto so expoe o QUANDO (frames) que a cena consome. */")
    out.append("/* fontes (sha256): */")
    for n in FAIXAS:
        out.append("/*   %s.json %s */" % (n, sha[n]))
    for n in FAIXAS:
        tag = n.split("_")[1].upper()
        out.append("#define LOOP_%s %u    /* compasso=%u f */"
                   % (tag, metas[n]["loop"], metas[n]["fp"] * 4))
    out.append("")
    out.append("/* cena 02 — ataques do lead de dawn (ressonancia em ordem) */")
    out.append("#define DAWN_ATTACKS_N %d" % len(da))
    out.append("static const unsigned int dawn_attacks[DAWN_ATTACKS_N] = {")
    out.append(",".join(str(f) for f in da))
    out.append("};")
    out.append("")
    out.append("/* cena 03 — hits de ch3 (flash de paleta sinc; ruido branco) */")
    out.append("#define STORM_HITS_N %d" % len(sh))
    out.append("static const unsigned int storm_hits[STORM_HITS_N] = {")
    out.append(",".join(str(f) for f in sh))
    out.append("};")
    out.append("")
    return "\n".join(out) + "\n", {
        "loops": {n: metas[n]["loop"] for n in FAIXAS},
        "dawn_attacks": len(da), "storm_hits": len(sh),
    }


def self_check():
    fails = []
    a, info = render()
    b, _ = render()
    if a != b:
        fails.append("render nao deterministico")
    # valores reconfirmados contra o auditor M2 (audit_psg_quality, 2026-10-12)
    exp = {"music_title": 1536, "music_dawn": 1920,
           "music_storm": 896, "music_eco": 1728}
    for n, v in exp.items():
        if info["loops"][n] != v:
            fails.append("loop %s=%d esperado %d" % (n, info["loops"][n], v))
    if info["dawn_attacks"] < 8 or info["storm_hits"] < 32:
        fails.append("tabela degenerada (cobertura < 8/32)")
    # conteo de hits = soma de eventos de percussao das 8 bars de storm
    part, _ = load("music_storm")
    n_manual = sum(len(bar.get("percussao", ())) for bar in part["compassos"])
    if n_manual != info["storm_hits"]:
        fails.append("storm_hits %d != %d eventos na partitura"
                     % (info["storm_hits"], n_manual))
    if fails:
        for f in fails:
            print("[SELF_CHECK_FAIL]", f)
        return 1
    print("[SELF_CHECK_PASS] determinismo + loops M2 + cobertura de tabelas")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="o arquivo em disco bate com o render atual?")
    args = ap.parse_args()
    if args.self_check:
        sys.exit(self_check())
    text, _ = render()
    dst = os.path.join(PROJ, "inc", "scene_tables.h")
    if args.check:
        with open(dst, "rb") as fh:
            same = fh.read() == text.encode("utf-8")
        print("[CHECK_%s] %s" % ("OK" if same else "STALE", dst))
        sys.exit(0 if same else 1)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("[EMIT]", dst, "(%d B)" % len(text))


if __name__ == "__main__":
    main()
