#!/usr/bin/env python3
"""audit_probe_corridor.py — o corredor de sondas __at() está LIVRE no map?

L089 é recorrente por uma razão estrutural: o corredor de probes vive no topo
da RAM de 8 K e o _DATA/_BSS da biblioteca sobe exatamente até encostar nele.
Quando a margem é zero, o linker pousa `_PSGMusicStatus`, `_PSGChan1Volume` e
`_PSGSFXPointer` DENTRO do corredor (medido no map de 2026-10-14: C7A9/C7BC/
C7D1 sobre endereços de probe). A escrita do probe corrompe o stream e a
leitura vira lixo plausível — o pior tipo de evidência, porque parece número.

O gate fecha isso ANTES de qualquer medição:

  1. deriva o corredor do FONTE declarado (measure_worst_frame.declared_probes,
     único dono do parser) — nada de tabela copiada;
  2. lê o `.map` do sdcc-link e reprova qualquer símbolo NÃO-probe caindo
     dentro de [lo, hi] — inclusive os de área (`s__BSS`, `s__HEAP`), que são
     justamente os que invadem;
  3. reprova sonda declarada que SUMIU do map (não-`volatile` → SDCC apaga a
     escrita, L009; ou morte por dead-code);
  4. exige folga `--margin` entre o fim dos dados alheios e o início do
     corredor — corredor colado em _DATA é o estado que produziu a colisão;
  5. confina o corredor em 0xC000..0xDFFF (RAM real do SMS).

Uso:
  audit_probe_corridor.py --project SMS_projects/pulso_de_cristal \
      [--map out/obj/X.map] [--margin 16] [--self-check]

Exit: 0 corredor livre | 1 invasão/sonda sumida/margem | 2 map ausente | 3 uso
"""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import measure_worst_frame as MWF                                   # noqa: E402

SYMBOL_RX = re.compile(r"^\s+([0-9A-F]{8})\s+(\S+)")
RAM_LO, RAM_HI = 0xC000, 0xDFFF
DEFAULT_MARGIN = 16


def map_symbols(map_path):
    """[(endereco, nome)] da tabela de símbolos do map (sdcc/asxxxx)."""
    out = []
    with open(map_path, errors="replace") as fh:
        for line in fh:
            m = SYMBOL_RX.match(line)
            if m:
                out.append((int(m.group(1), 16), m.group(2)))
    return out


def probe_names(probes):
    """Nomes de símbolos (sem índice de array) que TÊM direito ao corredor."""
    return {"_" + base for base in
            {name.split("[")[0] for name, _, _ in probes}}


def audit(src, map_path, margin=DEFAULT_MARGIN):
    """Veredito do corredor: fonte declarado x símbolos reais do map."""
    probes = MWF.declared_probes(src)
    res = {"fonte": os.path.abspath(src), "map": os.path.abspath(map_path),
           "map_sha256": hashlib.sha256(open(map_path, "rb").read()).hexdigest(),
           "sondas": len(probes), "margin_min": margin,
           "invasoes": [], "sondas_sumidas": [], "verdicto": None}
    if not probes:
        res["verdicto"] = "sem_corredor"
        return res
    lo = min(a for _, a, _ in probes)
    hi = max(a + w - 1 for _, a, w in probes)
    res["corredor"] = "0x%04X..0x%04X" % (lo, hi)
    res["corredor_lo"], res["corredor_hi"] = lo, hi
    if lo < RAM_LO or hi > RAM_HI:
        res["invasoes"].append("corredor fora da RAM do SMS: %s"
                               % res["corredor"])
    owned = probe_names(probes)
    syms = map_symbols(map_path)
    by_name = {n: a for a, n in syms}
    for addr, name in syms:
        if lo <= addr <= hi and name not in owned:
            res["invasoes"].append("%s@0x%04X dentro do corredor" % (name, addr))
    for name in sorted(owned):
        if name not in by_name:
            res["sondas_sumidas"].append(
                "%s declarado no fonte e ausente do map" % name[1:])
    estranhos = [a for a, n in syms if a < lo and n not in owned
                 and RAM_LO <= a <= RAM_HI]
    res["folga_bytes"] = (lo - max(estranhos)) if estranhos else None
    if res["folga_bytes"] is not None and res["folga_bytes"] < margin:
        res["invasoes"].append(
            "folga de %d B abaixo do corredor (< %d B): outro _DATA encosta "
            "e a proxima sonda é esmagada" % (res["folga_bytes"], margin))
    if res["invasoes"] or res["sondas_sumidas"]:
        res["verdicto"] = "invasao" if res["invasoes"] else "sonda_sumida"
        if res["invasoes"] and res["sondas_sumidas"]:
            res["verdicto"] = "invasao_e_sonda_sumida"
    else:
        res["verdicto"] = "pass"
    return res


def find_map(project, explicit=None):
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    obj = os.path.join(project, "out", "obj")
    if not os.path.isdir(obj):
        return None
    maps = [os.path.join(obj, f) for f in sorted(os.listdir(obj))
            if f.endswith(".map")]
    if not maps:
        return None
    return max(maps, key=os.path.getmtime)


def self_check():
    ok = []
    src = os.path.join(tempfile.mkdtemp(), "p.c")
    mp = os.path.join(os.path.dirname(src), "p.map")
    with open(src, "w") as f:
        f.write("volatile unsigned char __at(0xC900) probe_a;\n"
                "volatile unsigned int  __at(0xC901) probe_b;\n")

    def _map(lines):
        with open(mp, "w") as f:
            f.write("\n".join(lines) + "\n")
        return audit(src, mp, margin=4)

    r = _map(["     0000C800  _PSGMusicStatus              PSGlib",
              "     0000C8DF  s__BSS                      ",
              "     0000C900  _probe_a                   main",
              "     0000C901  _probe_b                   main"])
    ok.append(("corredor livre com dados abaixo passa",
               r["verdicto"] == "pass" and r["corredor"] == "0xC900..0xC902"
               and r["folga_bytes"] == 33))
    r = _map(["     0000C900  _probe_a                   main",
              "     0000C901  _probe_b                   main",
              "     0000C902  _PSGSFXPointer             PSGlib"])
    ok.append(("simbolo de biblioteca dentro do corredor reprova",
               r["verdicto"] == "invasao"
               and any("_PSGSFXPointer@0xC902" in v for v in r["invasoes"])))
    r = _map(["     0000C900  s__BSS                      ",
              "     0000C900  _probe_a                   main",
              "     0000C901  _probe_b                   main"])
    ok.append(("area comecando no corredor reprova",
               r["verdicto"] == "invasao"
               and any("s__BSS" in v for v in r["invasoes"])))
    r = _map(["     0000C900  _probe_a                   main"])
    ok.append(("sonda declarada sumida do map reprova",
               r["verdicto"] == "sonda_sumida"
               and any("probe_b" in v for v in r["sondas_sumidas"])))
    r = _map(["     0000C8FD  _PSGChan1Volume            PSGlib",
              "     0000C900  _probe_a                   main",
              "     0000C901  _probe_b                   main"])
    ok.append(("folga menor que o minimo reprova",
               r["verdicto"] == "invasao" and r["folga_bytes"] == 3))
    with open(src, "w") as f:
        f.write("volatile unsigned char __at(0x0900) probe_a;\n")
    r = _map(["     00000900  _probe_a                   main"])
    ok.append(("corredor fora da RAM do SMS reprova",
               r["verdicto"] == "invasao"))
    with open(src, "w") as f:
        f.write("int main(void){return 0;}\n")
    r = _map(["     0000C900  _probe_a                   main"])
    ok.append(("fonte sem sonda = sem corredor", r["verdicto"] == "sem_corredor"))
    for nome, bom in ok:
        print("  %-46s %s" % (nome, "ok" if bom else "FALHOU"))
    if not all(b for _, b in ok):
        print("[SELF-CHECK FAIL] audit_probe_corridor")
        return 1
    print("[SELF-CHECK OK] audit_probe_corridor")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--src", help="fonte ou diretório de fonte (default <project>/src)")
    ap.add_argument("--map", help="map do linker (default: mais novo em out/obj)")
    ap.add_argument("--margin", type=int, default=DEFAULT_MARGIN)
    ap.add_argument("--out", default="probe_corridor_report")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return self_check()
    src = args.src or os.path.join(args.project, "src")
    if not os.path.exists(src):
        print("[FAIL_USO] fonte inexistente: %s" % src)
        return 3
    mp = find_map(args.project, args.map)
    if not mp:
        print("[FAIL_AMBIENTE] map do linker ausente (projeto buildado? "
              "out/obj/*.map). Sem map, corredor é suposição.")
        return 2
    res = audit(src, mp, args.margin)
    out_dir = os.path.join(args.project, "out", "logs")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, args.out + ".json"), "w") as f:
        json.dump(res, f, indent=1)
    print("[corredor] %s sondas=%d folga=%s veredito=%s"
          % (res.get("corredor", "-"), res["sondas"],
             res.get("folga_bytes"), res["verdicto"]))
    for v in res["invasoes"] + res["sondas_sumidas"]:
        print("   - %s" % v)
    if res["verdicto"] != "pass":
        print("               %s" % ("reprove o probe-base/realoque o corredor "
                                     "antes de medir: a escrita e a leitura "
                                     "pisam em dados da biblioteca"
                                     if res["verdicto"] != "sem_corredor"
                                     else "nada declarado para auditar"))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
