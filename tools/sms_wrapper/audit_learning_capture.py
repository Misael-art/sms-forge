#!/usr/bin/env python3
"""audit_learning_capture.py — lição sem JSON/lei/ferramenta não é captura (§21/§43).

O ledger virou caderno de sessão (L038–L049 só em prosa). Este gate mede o
pipeline canônico: JSON em doc/curation + ID contínuo ou furo declarado +
ferramenta existente quando o status exige + persona/skill sem doutrina morta.

Uso:
  audit_learning_capture.py [--root DIR] [--json saida]
  audit_learning_capture.py --self-check
Exit: 0 coerente | 1 deriva | 3 uso
"""
import argparse, glob, hashlib, json, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LID = re.compile(r"\bL(\d{3})\b")
TOOL_PY = re.compile(r"(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_]+\.py")
NEED_TOOL = (
    "fechada_com_ferramenta",
    "fechada_com_ferramenta_e_correcao",
    "fechada_com_ferramenta_e_refutacao_parcial",
)
STALE = (
    (r"X f[ií]sico armazenado\s*=\s*X\s*\+\s*32",
     "X+32 como lei vigente (L003 refutou)"),
    (r"Tamanho global 8\s*[x×]\s*8\s*OU\s*16\s*[x×]\s*16",
     "TALL=16x16 como lei vigente (L006)"),
    (r"Sprite 8\s*[x×]\s*8/16\s*[x×]\s*16 \(modo global\)",
     "pixel-strict ensinando 16x16 como modo VDP (L006)"),
    (r"gravar o monitor do sink default",
     "audio no sink default como captura vigente (L017/§31)"),
    (r"readbyte/readword do DAP retorna\s*\$0",
     "DAP condenado como lei vigente (L035 reabriu o canal)"),
    (r"Boot no emulador \(openmsx/Emulicious\)",
     "openMSX como gate SMS vigente (L005)"),
    (r"(?:o canal [eé]|[Nn]este host:)\s*(?:`?emulator_input\.py`?\s*\()?[^\n]*kdotool\s*\+\s*ydotool",
     "desktop como canal padrão de QA (§93)"),
    (r"Cronometragem [eé] por tempo de rel[oó]gio",
     "sleep de host como regra única de input; sessão privada usa frames VDP (§93)"),
    (r"motion_fraction.*primeiro e o [uú]ltimo.*congelad",
     "endpoints como oráculo de freeze; usar timeline completa (§97)"),
    (r"Cada estado precisa de delta vis[ií]vel entre frames",
     "delta RGB obrigatório confunde elemento AIR com pixels (§100)"),
)
HISTORICAL = (
    "refutad", "dizia", "herança", "heranca", "corrigido", "supersed",
    "não existe", "nao existe", "era expressão", "era expressao",
    "reabriu", "falso", "nunca foram emitidos", "furo declarado",
    "número do mega drive", "numero do mega drive",
)


def _load_json(path):
    try:
        return json.load(open(path, encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as e:
        return None, str(e)


def expand_holes(registry):
    holes = {}
    for lid, reason in (registry.get("holes") or {}).items():
        holes[lid] = reason
    for row in registry.get("hole_ranges") or []:
        if len(row) < 2:
            continue
        a, b = int(str(row[0])[1:]), int(str(row[1])[1:])
        reason = row[2] if len(row) > 2 else "furo declarado"
        for n in range(a, b + 1):
            holes[f"L{n:03d}"] = reason
    return holes


def lessons_from_curation(root):
    problems, by_id = [], {}
    for f in sorted(glob.glob(os.path.join(root, "doc", "curation", "*.json"))):
        base = os.path.basename(f)
        if base == "id_registry.json":
            continue
        d, err = _load_json(f)
        if err:
            problems.append(f"curadoria ilegivel {base}: {err}")
            continue
        for l in d.get("lessons") or []:
            lid = l.get("id")
            if not lid:
                problems.append(f"{base}: licao sem id")
                continue
            if lid in by_id:
                problems.append(f"licao '{lid}' duplicada entre "
                                f"{by_id[lid][0]} e {base}")
                continue
            by_id[lid] = (base, l)
    return by_id, problems


def ledger_ids(root):
    path = os.path.join(root, "doc", "agent_learning", "learning_ledger.json")
    if not os.path.isfile(path):
        return [], [f"ledger ausente: {path}"]
    d, err = _load_json(path)
    if err:
        return [], [f"ledger ilegivel: {err}"]
    found = []
    for e in d.get("entries") or []:
        text = " ".join(str(e.get(k) or "") for k in ("summary", "dedup_key"))
        for m in LID.finditer(text):
            found.append(f"L{m.group(1)}")
    return found, []


def _stale_in(text):
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        # A pasted global-kill command stays unsafe even on a line calling it
        # 'corrigido' or 'falso'. Plain prohibitions without the command pass.
        if re.search(r"(?:pkill|killall)\s+(?:-[\w]+\s+)*[^\n]*[Ee]mulicious", line):
            hits.append((i,"comando de encerramento global de Emulicious (§93)",line.strip()[:80]))
        if any(w in low for w in HISTORICAL):
            continue
        for rx, why in STALE:
            if re.search(rx, line, re.I):
                hits.append((i, why, line.strip()[:80]))
    return hits


def audit_routes(root, by_id):
    """Every emitted lesson has a current, hash-bound application entrypoint.

    This measures coverage and freshness, not whether the prose teaches well.
    Historical/refuted lessons route to the current corrective procedure.
    """
    path = os.path.join(root, "doc", "agent_learning", "lesson_routes.json")
    data, error = _load_json(path)
    if error:
        return [f"lesson_routes ilegivel/ausente: {error}"]
    if not isinstance(data, dict) or data.get("schema") != "sms_lesson_routes_v1" or not isinstance(data.get("routes"), list):
        return ["lesson_routes schema/routes invalidos"]
    problems, seen = [], set()
    for row in data["routes"]:
        if not isinstance(row, dict):
            problems.append("lesson_routes entrada nao objeto")
            continue
        lid = row.get("lesson_id")
        if not isinstance(lid, str) or lid not in by_id or lid in seen:
            problems.append(f"lesson_routes ID desconhecido/duplicado: {lid}")
            continue
        seen.add(lid)
        expected = "doc/curation/" + by_id[lid][0]
        if row.get("sources") != [expected]:
            problems.append(f"{lid}: lesson_routes fonte canonica divergente")
        entries = row.get("application_entrypoints")
        if not isinstance(entries, list) or not entries or row.get("application_gap"):
            problems.append(f"{lid}: sem rota de aplicacao resolvida")
            continue
        paths = set()
        for entry in entries:
            try:
                from pathlib import Path, PurePosixPath
                rel = entry["path"]
                pure = PurePosixPath(rel)
                if (str(pure) != rel or pure.is_absolute() or ".." in pure.parts or
                    not any(rel.startswith("tools/sms_wrapper/.agent/" + folder + "/") for folder in ("skills", "workflows")) or rel in paths):
                    raise ValueError("entrypoint deve ser skill/workflow canonico unico")
                paths.add(rel)
                target = Path(root) / rel
                resolved = target.resolve()
                if (target.suffix != ".md" or not any(resolved.is_relative_to(
                        (Path(root) / "tools/sms_wrapper/.agent" / folder).resolve())
                        for folder in ("skills", "workflows"))):
                    raise ValueError("entrypoint resolvido fora de skills/workflows")
                sha = hashlib.sha256(target.read_bytes()).hexdigest()
                if entry.get("sha256") != sha:
                    raise ValueError("entrypoint stale por SHA")
                if not isinstance(entry.get("selection_basis"), str) or not entry["selection_basis"].strip():
                    raise ValueError("selection_basis ausente")
            except (OSError, ValueError, TypeError, KeyError) as error:
                problems.append(f"{lid}: {error}")
    for lid in sorted(set(by_id) - seen):
        problems.append(f"{lid}: ausente do mapa lesson_routes")
    return problems


def audit(root, wrapper=None):
    problems = []
    wrapper = wrapper or os.path.join(root, "tools", "sms_wrapper")
    reg_path = os.path.join(root, "doc", "curation", "id_registry.json")
    if not os.path.isfile(reg_path):
        return [f"id_registry ausente: {reg_path}"]
    registry, err = _load_json(reg_path)
    if err:
        return [f"id_registry ilegivel: {err}"]
    holes = expand_holes(registry)
    by_id, problems = lessons_from_curation(root)
    problems += audit_routes(root, by_id)

    nums = []
    for lid in by_id:
        m = LID.fullmatch(lid)
        if not m:
            problems.append(f"id de licao nao canonico: {lid}")
            continue
        nums.append(int(m.group(1)))
    for lid in holes:
        m = LID.fullmatch(lid)
        if m:
            nums.append(int(m.group(1)))
    if nums:
        for n in range(1, max(nums) + 1):
            lid = f"L{n:03d}"
            if lid not in by_id and lid not in holes:
                problems.append(
                    f"{lid} nao esta em curadoria nem em id_registry "
                    "(furo nao declarado — §43)")

    for lid, (base, lesson) in by_id.items():
        status = (lesson.get("status") or "").strip()
        rule = lesson.get("rule_section") or ""
        if not rule:
            problems.append(f"{base}:{lid} sem rule_section")
        field = lesson.get("tool_that_measures") or ""
        tools = set(TOOL_PY.findall(field))
        for m in re.finditer(r"\b([A-Za-z0-9_]+)\.[A-Za-z_]", field):
            fn = m.group(1) + ".py"
            if os.path.isfile(os.path.join(wrapper, fn)):
                tools.add(fn)
        if any(status.startswith(s) for s in NEED_TOOL) or status in NEED_TOOL:
            if not tools:
                problems.append(f"{base}:{lid} status '{status}' sem ferramenta")
            for fn in tools:
                if not os.path.isfile(os.path.join(wrapper, fn)):
                    problems.append(
                        f"{base}:{lid} ferramenta '{fn}' nao existe no wrapper")
        skill = lesson.get("skill_that_teaches") or ""
        if status == "absorvida_em_skill":
            if not skill:
                problems.append(f"{base}:{lid} absorvida_em_skill sem skill_that_teaches")
            else:
                candidates = [
                    os.path.join(wrapper, ".agent", skill),
                    os.path.join(wrapper, ".agent", "skills", os.path.basename(skill)),
                    os.path.join(wrapper, ".agent", "workflows", os.path.basename(skill)),
                ]
                if not any(os.path.isfile(p) for p in candidates):
                    problems.append(f"{base}:{lid} skill '{skill}' nao encontrada")

    led_ids, led_err = ledger_ids(root)
    problems += led_err
    known = set(by_id) | set(holes)
    for lid in led_ids:
        if lid not in known:
            problems.append(
                f"ledger cita {lid} sem JSON de curadoria nem furo declarado")

    agent_root = os.path.join(wrapper, ".agent")
    scan = []
    for folder in ("agents", "skills", "workflows"):
        d = os.path.join(agent_root, folder)
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if fn.endswith(".md"):
                    scan.append(os.path.join(d, fn))
    for path in scan:
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError as e:
            problems.append(f"{path}: ilegivel ({e})")
            continue
        rel = os.path.relpath(path, wrapper)
        for line_n, why, snippet in _stale_in(text):
            problems.append(f"{rel}:{line_n}: doutrina supersedida ({why}): {snippet}")
    return problems


def _self_check():
    d = tempfile.mkdtemp(prefix="smslearn_")
    try:
        w = os.path.join(d, "tools", "sms_wrapper")
        os.makedirs(os.path.join(w, ".agent", "skills"))
        os.makedirs(os.path.join(d, "doc", "curation"))
        os.makedirs(os.path.join(d, "doc", "agent_learning"))
        open(os.path.join(w, "audit_x.py"), "w").write("# --self-check\n")
        json.dump({
            "schema": "lesson_id_registry_v1",
            "holes": {"L002": "furo de teste"},
            "hole_ranges": [],
        }, open(os.path.join(d, "doc", "curation", "id_registry.json"), "w"))
        json.dump({"lessons": [{
            "id": "L001",
            "status": "fechada_com_ferramenta",
            "tool_that_measures": "audit_x.py",
            "rule_section": "SMS_GLOBAL §1",
        }]}, open(os.path.join(d, "doc", "curation", "a.json"), "w"))
        json.dump({"entries": [{"summary": "L001 ok", "dedup_key": "l001"}]},
                  open(os.path.join(d, "doc", "agent_learning",
                                    "learning_ledger.json"), "w"))
        open(os.path.join(w, ".agent", "skills", "ok.md"), "w").write(
            "X armazenado sem offset.\n")
        route_path = os.path.join(d, "doc", "agent_learning", "lesson_routes.json")
        routes = {"schema": "sms_lesson_routes_v1", "routes": [{"lesson_id": "L001",
            "sources": ["doc/curation/a.json"], "application_gap": None,
            "application_entrypoints": [{"path": "tools/sms_wrapper/.agent/skills/ok.md",
                "sha256": hashlib.sha256(b"X armazenado sem offset.\n").hexdigest(),
                "selection_basis": "synthetic corrective procedure"}]}]}
        json.dump(routes, open(route_path, "w"))
        p = audit(d, wrapper=w)
        assert not p, f"repo coerente nao deveria reprovar: {p}"
        empty = {"schema": "sms_lesson_routes_v1", "routes": []}
        json.dump(empty, open(route_path, "w"))
        assert any("mapa lesson_routes" in x for x in audit(d, wrapper=w))
        routes["routes"][0]["application_entrypoints"][0]["sha256"] = "0" * 64
        json.dump(routes, open(route_path, "w"))
        assert any("stale por SHA" in x for x in audit(d, wrapper=w))
        routes["routes"][0]["application_entrypoints"][0]["sha256"] = hashlib.sha256(b"X armazenado sem offset.\n").hexdigest()
        json.dump(routes, open(route_path, "w"))
        rules = os.path.join(w, ".agent", "rules")
        os.makedirs(rules)
        rule = os.path.join(rules, "SMS_GLOBAL.md")
        open(rule, "w").write("rule only")
        alias = os.path.join(w, ".agent", "skills", "alias.md")
        os.symlink(rule, alias)
        alias_routes = json.loads(json.dumps(routes))
        alias_routes["routes"][0]["application_entrypoints"][0].update(
            path="tools/sms_wrapper/.agent/skills/alias.md", sha256=hashlib.sha256(b"rule only").hexdigest())
        json.dump(alias_routes, open(route_path, "w"))
        assert any("resolvido fora" in x for x in audit(d, wrapper=w))
        os.unlink(alias)
        json.dump(routes, open(route_path, "w"))

        nested = os.path.join(w, "mugen2sms", "analysis")
        os.makedirs(nested)
        nested_tool = os.path.join(nested, "scale_pilot.py")
        open(nested_tool, "w").write("# --self-check\n")
        json.dump({"lessons": [{
            "id": "L001",
            "status": "fechada_com_ferramenta",
            "tool_that_measures": "mugen2sms/analysis/scale_pilot.py",
            "rule_section": "SMS_GLOBAL §1",
        }]}, open(os.path.join(d, "doc", "curation", "a.json"), "w"))
        p = audit(d, wrapper=w)
        assert not p, f"ferramenta nested existente deveria ser aceita: {p}"
        os.remove(nested_tool)
        p = audit(d, wrapper=w)
        assert any("mugen2sms/analysis/scale_pilot.py" in x for x in p), \
            f"ferramenta nested ausente deveria reprovar: {p}"

        json.dump({"entries": [{"summary": "L009 so no ledger"}]},
                  open(os.path.join(d, "doc", "agent_learning",
                                    "learning_ledger.json"), "w"))
        p = audit(d, wrapper=w)
        assert any("ledger cita L009" in x for x in p), f"faltou ledger orfao: {p}"

        json.dump({"entries": [{"summary": "L001 ok"}]},
                  open(os.path.join(d, "doc", "agent_learning",
                                    "learning_ledger.json"), "w"))
        json.dump({"lessons": [{
            "id": "L001",
            "status": "fechada_com_ferramenta",
            "tool_that_measures": "audit_fantasma.py",
            "rule_section": "§1",
        }]}, open(os.path.join(d, "doc", "curation", "a.json"), "w"))
        p = audit(d, wrapper=w)
        assert any("audit_fantasma.py" in x for x in p), f"faltou ferramenta: {p}"

        json.dump({"lessons": [{
            "id": "L001",
            "status": "fechada_com_ferramenta",
            "tool_that_measures": "audit_x.py",
            "rule_section": "§1",
        }]}, open(os.path.join(d, "doc", "curation", "a.json"), "w"))
        open(os.path.join(w, ".agent", "skills", "bad.md"), "w").write(
            "Tamanho global 8×8 OU 16×16 (+ zoom).\n")
        p = audit(d, wrapper=w)
        assert any("TALL=16x16" in x for x in p), f"faltou doutrina stale: {p}"

        for bad_line in (
            "pkill -f Emulicious.jar antes da captura",
            "corrigido: `killall Emulicious` antes do teste",
            "o canal é kdotool+ydotool",
            "Neste host: emulator_input.py (kdotool+ydotool).",
            "Cronometragem é por tempo de relógio, use sleep",
            "motion_fraction: primeiro e o último => tela congelada",
            "Cada estado precisa de delta visível entre frames",
        ):
            assert _stale_in(bad_line), f"faltou doutrina de QA obsoleta: {bad_line}"
        for valid_line in (
            "Use sessão privada e frames VDP; encerre somente por ID próprio.",
            "Nunca usar pkill ou killall; não encerrar sessões alheias.",
            "Rota histórica supersedida: o canal é kdotool+ydotool.",
            "motion_fraction usa timeline completa; endpoints iguais não provam freeze.",
            "Elementos AIR distintos podem mostrar o mesmo RGB; medir IDs e stamps.",
        ):
            assert not _stale_in(valid_line), f"falso positivo de doutrina: {valid_line}"

        os.remove(os.path.join(w, ".agent", "skills", "bad.md"))
        json.dump({"schema": "lesson_id_registry_v1", "holes": {}},
                  open(os.path.join(d, "doc", "curation", "id_registry.json"), "w"))
        json.dump({"lessons": [{
            "id": "L001",
            "status": "fechada_com_ferramenta",
            "tool_that_measures": "audit_x.py",
            "rule_section": "§1",
        }, {
            "id": "L003",
            "status": "fechada_com_evidencia",
            "rule_section": "§1",
        }]}, open(os.path.join(d, "doc", "curation", "a.json"), "w"))
        p = audit(d, wrapper=w)
        assert any("L002 nao esta" in x for x in p), f"faltou furo L002 apos L003: {p}"
        json.dump({
            "schema": "lesson_id_registry_v1",
            "holes": {"L002": "furo de teste"},
        }, open(os.path.join(d, "doc", "curation", "id_registry.json"), "w"))
        p = audit(d, wrapper=w)
        assert not any("L002 nao esta" in x for x in p), f"furo declarado reprovou: {p}"
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("[SELF-CHECK OK] learning_capture (ledger orfao, ferramenta fantasma, "
          "doutrina supersedida, furo nao declarado)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.normpath(os.path.join(HERE, "..", "..")))
    ap.add_argument("--json", "--report-out", dest="json", help="new report destination; existing files are refused")
    ap.add_argument("--self-check", action="store_true")
    a = ap.parse_args()
    if a.self_check:
        return _self_check()
    problems = audit(a.root)
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
        print(f"[FAIL] {len(problems)} deriva(s) de captura de licao (§21/§43).")
        return 1
    print("[PASS] captura de licao sincronizada (JSON, furos, ferramentas, doutrina)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
