#!/usr/bin/env python3
"""validate_measurement_tools.py — nenhuma ferramenta de medicao sem --self-check.

Fecha a ultima restricao nao-negociavel do AGENTS.md que nao tinha gate:
  "Usar leitura de ferramenta de medicao cujo --self-check nao passa"

Regra §19 (SMS_GLOBAL): ferramenta de medicao sem self-check NAO E FONTE.
Este gate audita o proprio wrapper: toda ferramenta que mede/audita precisa
(a) expor --self-check e (b) ter o self-check passando AGORA.

Uso: validate_measurement_tools.py [--dir <wrapper>] [--json <saida>] [--self-check]
Exit: 0 todas provadas | 1 ha ferramenta sem self-check ou reprovando | 3 uso
"""
import sys, os, json, argparse, subprocess

# Ferramentas que MEDEM/AUDITAM => self-check obrigatorio.
PREFIXES = ("audit_", "validate_", "measure_", "capture_", "seal_", "reconcile_")
SUFFIX_GATES = ("_gate.py",)
# Oráculos de autonomia (L036): decisão/plano com --self-check obrigatório.
DOCTRINE_ALWAYS = {"harness_orchestration.py", "quality_review_router.py",
                   "emulator_input.py", "prepare_sms_pixel_art.py",
                   "blastem_sms.py",
                   "blastem_diagnostics.py", "blastem_maintenance.py",
                   "blastem_dump_diff.py",
                   "artifact_registry.py", "mugen2sms/analysis/trace_compare.py",
                   "mugen2sms/analysis/scale_pilot.py",
                   "mugen2sms/runtime/vram_plan.py",
                   "mugen2sms/runtime/commit_budget.py"}

# Nao sao ferramentas de medicao: constroem, geram ou orquestram.
EXEMPT = {
    "build_inner.py",      # constroi (o gate dele e o proprio build falhar)
    "gen_fixtures.py",     # gera fixtures para o selftest
    "selftest.py",         # e o orquestrador da bateria
    "png_io.py",           # biblioteca de I/O, sem leitura de veredito
    "sms_palette.py",      # tabela de dados
    "png_to_sms_tiles.py", # conversor
    "validate_measurement_tools.py",  # este arquivo (evita recursao)
}

def discover(wrapper_dir):
    """Retorna ferramentas de medição na raiz e em subdiretórios do wrapper."""
    out = []
    for current, dirs, files in os.walk(wrapper_dir):
        dirs[:] = sorted(d for d in dirs if d not in {"__pycache__", ".pytest_cache"})
        for fn in sorted(files):
            rel = os.path.relpath(os.path.join(current, fn), wrapper_dir)
            if not fn.endswith(".py") or (current == wrapper_dir and fn in EXEMPT):
                continue
            if (fn.startswith(PREFIXES) or fn.endswith(SUFFIX_GATES) or
                    fn in DOCTRINE_ALWAYS or rel in DOCTRINE_ALWAYS):
                out.append(rel)
    return sorted(out)

def audit(wrapper_dir, timeout=120):
    tools = discover(wrapper_dir)
    problems, report = [], []
    if not tools:
        problems.append("nenhuma ferramenta de medicao encontrada — descoberta quebrada?")
    py = sys.executable or "python3"
    for fn in tools:
        path = os.path.join(wrapper_dir, fn)
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except OSError as e:
            problems.append(f"{fn}: ilegivel ({e})")
            report.append({"tool": fn, "declares_self_check": False, "passes": False})
            continue
        declares = "--self-check" in src or "self_check" in src
        if not declares:
            problems.append(f"{fn}: NAO expoe --self-check (§19: nao e fonte)")
            report.append({"tool": fn, "declares_self_check": False, "passes": False})
            continue
        try:
            r = subprocess.run([py, path, "--self-check"], capture_output=True,
                               text=True, timeout=timeout, cwd=wrapper_dir)
            ok = (r.returncode == 0)
            tail = (r.stdout + r.stderr).strip().splitlines()
            if not ok:
                problems.append(f"{fn}: --self-check REPROVOU (exit {r.returncode}) "
                                f"{tail[-1][:70] if tail else ''}")
        except subprocess.TimeoutExpired:
            ok = False
            problems.append(f"{fn}: --self-check estourou timeout ({timeout}s)")
        report.append({"tool": fn, "declares_self_check": True, "passes": ok})
    return problems, report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--json", help="grava relatorio machine-readable")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()

    if args.self_check:
        import tempfile
        d = tempfile.mkdtemp(prefix="smsvmt_")
        # ferramenta boa: expoe --self-check e passa
        with open(os.path.join(d, "audit_bom.py"), "w") as f:
            f.write("import sys\nif '--self-check' in sys.argv:\n"
                    "    print('[SELF-CHECK OK] bom'); sys.exit(0)\nsys.exit(0)\n")
        p, _ = audit(d)
        assert not p, f"ferramenta com self-check valido nao deveria reprovar: {p}"
        nested = os.path.join(d, "mugen2sms", "analysis")
        os.makedirs(nested)
        with open(os.path.join(nested, "scale_pilot.py"), "w") as f:
            f.write("import sys\nif '--self-check' in sys.argv:\n"
                    "    print('[SELF-CHECK OK] nested'); sys.exit(0)\n"
                    "sys.exit(0)\n")
        p, report = audit(d)
        assert not p, f"medidor nested com self-check valido reprovou: {p}"
        assert any(row["tool"] == "mugen2sms/analysis/scale_pilot.py" and row["passes"]
                   for row in report), "descoberta não alcançou a ferramenta nested"
        # ferramenta que NAO expoe self-check
        with open(os.path.join(d, "audit_sem_selfcheck.py"), "w") as f:
            f.write("print('meço coisas mas nao me provo')\n")
        p, _ = audit(d)
        assert any("NAO expoe" in x for x in p), "faltou reprovar ferramenta sem self-check"
        os.remove(os.path.join(d, "audit_sem_selfcheck.py"))
        # ferramenta que expoe mas REPROVA
        with open(os.path.join(d, "audit_quebrada.py"), "w") as f:
            f.write("import sys\nif '--self-check' in sys.argv:\n"
                    "    print('quebrei'); sys.exit(1)\n")
        p, _ = audit(d)
        assert any("REPROVOU" in x for x in p), "faltou reprovar self-check que falha"
        print("[SELF-CHECK OK] validate_measurement_tools "
              "(descobre nested e detecta ausência/self-check falhando)")
        return 0

    problems, report = audit(args.dir)
    if args.json:
        with open(args.json, "w") as f:
            json.dump({"tools": report,
                       "problems": problems,
                       "all_proven": not problems}, f, indent=2)
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        print(f"[FAIL] {len(problems)} problema(s): ha ferramenta de medicao nao provada. "
              "Leitura dela NAO pode ser citada como evidencia (§19).")
        return 1
    print(f"[PASS] {len(report)} ferramentas de medicao com --self-check passando")
    return 0

if __name__ == "__main__":
    sys.exit(main())
