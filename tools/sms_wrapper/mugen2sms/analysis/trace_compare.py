"""Comparacao de trilhas por tick antes/depois de uma mudanca (doc/21, item 3).

Tecnica assimilada de `runtime_trace.compare` do forge MD, com o defeito do doador corrigido: o doador usa `zip`,
que descarta a cauda mais longa — uma trilha que perde (ou ganha) ticks no fim aparece como "sem divergencia".
Aqui o comprimento, o conjunto de cenarios e o conjunto de chaves por tick sao parte do veredito.

Formato: {"cenario": [ {"tick": 0, "p1_x": 96, ...}, ... ]} — um dict de inteiros por tick (sem float, como o
runtime). Quem PRODUZ a trilha (host, DAP, emulador) e outro assunto: este modulo so julga duas trilhas dadas.
Equivalencia aqui prova que o ESTADO REGISTRADO nao mudou; nao prova render, tempo de Z80 nem campos nao gravados.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def compare(before: dict, after: dict) -> dict:
    scenarios = []
    problems: list[str] = []
    only_b, only_a = sorted(set(before) - set(after)), sorted(set(after) - set(before))
    problems += [f"cenario so no antes: {n}" for n in only_b] + [f"cenario so no depois: {n}" for n in only_a]
    for name in sorted(set(before) & set(after)):
        b, a = before[name], after[name]
        n = min(len(b), len(a))
        first = next((i for i in range(n) if b[i] != a[i]), None)
        diffs = sum(1 for i in range(n) if b[i] != a[i])
        keys_b = {k for t in b for k in t}
        keys_a = {k for t in a for k in t}
        row = {"scenario": name, "ticks_before": len(b), "ticks_after": len(a), "compared_ticks": n,
               "diverging_ticks": diffs, "first_divergent_tick": first,
               "length_mismatch": len(b) != len(a), "missing_keys": sorted(keys_b - keys_a),
               "new_keys": sorted(keys_a - keys_b), "empty": len(b) == 0 or len(a) == 0}
        if first is not None:
            row["before"], row["after"] = b[first], a[first]
        if row["length_mismatch"]:
            problems.append(f"{name}: comprimento {len(b)} -> {len(a)} (cauda {abs(len(b) - len(a))} tick(s))")
        if row["missing_keys"] or row["new_keys"]:
            problems.append(f"{name}: chaves divergentes -{row['missing_keys']} +{row['new_keys']}")
        if row["empty"]:
            problems.append(f"{name}: trilha vazia (nada foi comparado)")
        if diffs:
            problems.append(f"{name}: {diffs} tick(s) divergentes, primeiro em {first}")
        scenarios.append(row)
    return {"equivalent": not problems, "problems": problems, "scenarios": scenarios}


def self_check() -> int:
    base = {"soco": [{"tick": i, "x": 96 + i, "life": 1000} for i in range(10)]}

    def mut(f):
        return {"soco": f([dict(t) for t in base["soco"]])}
    cases = {
        "igual": (mut(lambda t: t), True),
        "tick_diferente": (mut(lambda t: (t.__setitem__(4, {**t[4], "x": 0}), t)[1]), False),
        "cauda_perdida": (mut(lambda t: t[:-3]), False),               # o `zip` do doador diria "equivalente"
        "cauda_ganha": (mut(lambda t: t + [dict(t[-1], tick=10)]), False),
        "chave_perdida": (mut(lambda t: [{k: v for k, v in x.items() if k != "life"} for x in t]), False),
        "vazia": ({"soco": []}, False),
    }
    ok = True
    for name, (after, want) in cases.items():
        got = compare(base, after)["equivalent"]
        if got != want:
            print(f"  [FAIL] {name}: equivalent={got}, esperado {want}")
            ok = False
    # prova de que o doador erraria: zip ignora a cauda
    b, a = base["soco"], base["soco"][:-3]
    donor_would_pass = all(x == y for x, y in zip(b, a))
    ok = ok and donor_would_pass and compare(base, {"soco": a})["scenarios"][0]["length_mismatch"]
    ok = ok and not compare(base, {})["equivalent"]                                   # cenario ausente
    print("self-check trace_compare:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("before", type=Path, nargs="?")
    ap.add_argument("after", type=Path, nargs="?")
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args(argv)
    if a.self_check:
        return self_check()
    if not (a.before and a.after):
        ap.error("before e after obrigatorios sem --self-check")
    rep = compare(json.loads(a.before.read_text()), json.loads(a.after.read_text()))
    if a.out_json:
        a.out_json.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    for p in rep["problems"]:
        print("[DIFF]", p)
    print("[PASS] trilhas equivalentes" if rep["equivalent"] else f"[FAIL] {len(rep['problems'])} divergencia(s)")
    return 0 if rep["equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
