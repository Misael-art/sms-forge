#!/usr/bin/env python3
"""audit_specialization.py — valida especializacao de genero (porta do SGDK Forge).

--slice-plan verifica a cobertura declarada no roteiro da primeira cena.
O modo padrão procura eixos da especialização no GDD. Ambos são documentais.
Exit: 0 cobertura satisfeita ou perfil opcional ausente | 1 falha no documento
"""
import sys, os, json, argparse, re
from pathlib import Path

SLICE_FAMILIES = ("Ciclo central", "Repouso", "Locomoção", "Projétil", "Golpe",
                  "Efeito", "Troca de cenário", "Cutscene")
SECTION = "## Casos do primeiro trecho jogável"
BEAT_SECTION = "### Beats do primeiro trecho jogável"
HEADER = ["Família", "Escopo", "Beat ou motivo", "Resposta esperada", "Caso negativo", "Retomada"]


def filled(value):
    return value.casefold() not in {"", "-", "—", "…", "...", "n/a", "pendente", "a definir", "todo"} and not value.startswith("_(")


def slice_cases(script):
    """Read the template's beat definitions and coverage table from the same script."""
    # Examples in fenced blocks are not authored beats or executable cases.
    lines, fence = [], ""
    for line in script.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if line.strip().startswith(fence) and not line.strip().strip(fence[0]):
                fence = ""
        elif marker:
            fence = marker.group(1)
        else:
            lines.append(line)
    for heading in (BEAT_SECTION, SECTION):
        if lines.count(heading) != 1:
            return ["roteiro precisa de uma seção única: " + heading]
    errors, beats = [], {}
    for line in lines[lines.index(BEAT_SECTION) + 1:]:
        if line.startswith("#"):
            break
        beat = re.fullmatch(r"\s*[-*] \*\*(B[0-9]+)\*\*\s+(.+)", line)
        if beat:
            key, description = beat.groups()
            if key in beats:
                errors.append("beat duplicado: " + key)
            beats[key] = description.strip()
        elif line.strip():
            errors.append(f"beat deve usar o formato '- **B01** descrição': {line}")
    table = []
    for line in lines[lines.index(SECTION) + 1:]:
        if line.startswith("#"):
            break
        if line.strip().startswith("|"):
            table.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    if len(table) < 3 or table[0] != HEADER or len(table[1]) != len(HEADER) or not all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in table[1]):
        return errors + ["cabeçalho ou separador inválido na tabela de casos"]
    seen, included, covered = set(), set(), set()
    for index, row in enumerate(table[2:], 1):
        if len(row) != len(HEADER):
            errors.append(f"linha {index}: são necessárias seis colunas")
            continue
        family, scope, target, response, negative, recovery = row
        seen.add(family)
        if scope == "agora":
            included.add(family)
            if target not in beats or not filled(beats[target]):
                errors.append(f"{family}: beat {target!r} ausente ou por preencher")
            covered.add(target)
            for label, value in zip(HEADER[3:], (response, negative, recovery)):
                if not filled(value):
                    errors.append(f"{family}: preencher {label}")
        elif scope in ("depois", "fora"):
            if not filled(target) or re.fullmatch(r"B[0-9]+", target):
                errors.append(f"{family}: justificar {scope} pelo escopo do GDD")
        else:
            errors.append(f"{family}: escolher agora, depois ou fora")
    errors.extend("família ausente: " + name for name in SLICE_FAMILIES if name not in seen)
    errors.extend("beat sem caso no trecho: " + beat for beat in beats if beat not in covered)
    if "" in seen:
        errors.append("família sem nome")
    if "Ciclo central" not in included:
        errors.append("ciclo central precisa de um caso agora")
    return errors


def audit_slice_plan(project):
    try:
        return slice_cases((Path(project) / "doc/12-roteiro.md").read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        return [f"roteiro ilegível: {exc}"]

def read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (ValueError, OSError):
        return None

def audit(project):
    gen_mat = read_json(os.path.join(os.path.dirname(__file__), "..", "..",
                                     "doc", "game-design", "matriz_genero.json"))
    if not gen_mat or not isinstance(gen_mat.get("familias"), dict):
        return ["matriz ausente ou ilegível"], "sem matriz de genero"
    proj = read_json(os.path.join(project, ".mddev", "project.json"))
    if proj is None:
        return ["manifesto ausente ou ilegível"], "sem project.json"
    gen = proj.get("specialization") or proj.get("genre")
    if not gen:
        return [], "sem genero declarado (sem requisitos — ok)"
    if not isinstance(gen, str):
        return ["specialization deve ser textual"], "perfil inválido"
    fam = gen_mat["familias"].get(gen)
    if not fam:
        return [], f"genero '{gen}' fora da matriz"
    gaps = []
    # busca por presença dos eixos no GDD do projeto (indicador de cumprimento)
    gdd = os.path.join(project, "doc", "11-gdd.md")
    gdd_txt = open(gdd).read().lower() if os.path.exists(gdd) else ""
    for eixo in fam.get("eixos", []):
        if eixo not in gdd_txt:
            gaps.append(f"eixo '{eixo}' ausente no GDD")
    return gaps, f"genero '{gen}' — cobertura textual dos eixos no GDD"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--slice-plan", action="store_true", help="conferir casos no roteiro, antes do storyboard")
    args = ap.parse_args()
    if args.self_check:
        import tempfile
        with tempfile.TemporaryDirectory(prefix="smsspec_") as d:
            os.makedirs(os.path.join(d, ".mddev"), exist_ok=True)
            os.makedirs(os.path.join(d, "doc"), exist_ok=True)
            json.dump({"name": "t", "specialization": "puzzle"},
                      open(os.path.join(d, ".mddev", "project.json"), "w"))
            # puzzle exige 'logica_deterministica' etc no GDD; sem GDD -> gaps
            gaps, msg = audit(d)
            assert gaps, "sem GDD deveria acusar gaps"
            # declarar genero ausente -> passa sem requisitos
            json.dump({"name": "t"}, open(os.path.join(d, ".mddev", "project.json"), "w"))
            gaps2, _ = audit(d)
            assert not gaps2, "sem genero = sem requisitos"
            Path(d, ".mddev/project.json").write_text("{", encoding="utf-8")
            assert audit(d)[0], "manifesto ilegível precisa reprovar"
        script = (Path(__file__).parent / "modelo/doc/12-roteiro.md").read_text(encoding="utf-8")
        assert slice_cases(script), "o modelo pendente precisa reprovar"
        plan = [BEAT_SECTION, "- **B01** Selecionar a peça e confirmar a jogada.", SECTION,
                "| " + " | ".join(HEADER) + " |", "|---" * len(HEADER) + "|",
                "| Ciclo central | agora | B01 | A peça ocupa o destino | Casa ocupada recusa | Cursor livre |"]
        plan.extend(f"| {f} | fora | Só há peças nesta cena | — | — | — |" for f in SLICE_FAMILIES[1:])
        valid = "\n".join(plan)
        assert not slice_cases(valid)
        for bad in (valid.replace("| B01 |", "| B02 |"), valid.replace("Casa ocupada recusa", "—"),
                    valid.replace("Cursor livre", ""), valid.replace("Só há peças nesta cena", "pendente"),
                    "\n".join(plan[:-1]), valid.replace(SECTION, plan[1] + "\n" + SECTION),
                    valid.replace(SECTION, "- **B02** Jogar a próxima peça.\n" + SECTION),
                    "```md\n" + valid + "\n```"):
            assert slice_cases(bad)
        print("[SELF-CHECK OK] specialization and first-slice planning coverage")
        return 0
    if args.slice_plan:
        gaps = audit_slice_plan(args.project)
        for gap in gaps:
            print("   - " + gap)
        print("[FAIL] roteiro incompleto" if gaps else "[PASS] cobertura do plano no roteiro; execução e qualidade pendentes de ROM")
        return 1 if gaps else 0
    gaps, msg = audit(args.project)
    status = "FAIL" if gaps else "PASS" if "cobertura textual" in msg else "SEM PERFIL"
    print(f"[{status}] {msg}")
    for g in gaps:
        print(f"   - {g}")
    return 1 if gaps else 0

if __name__ == "__main__":
    sys.exit(main())
