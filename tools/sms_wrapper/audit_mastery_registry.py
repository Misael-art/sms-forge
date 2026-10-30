#!/usr/bin/env python3
"""audit_mastery_registry.py — valida a matriz de maestria SMS (registry JSON).

Regras: escada válida; acima de mapped exige arquivos com SHA, papel e escopo.
Níveis de emulador exigem também ROM, mídia e relatório JSON com ROM/session_id.
Valida custódia declarada, não autentica execução, conteúdo ou qualidade.
Não altera o registry: uma reprovação precisa de reconciliação explícita.

Uso: audit_mastery_registry.py --registry <json> [--self-check]
Exit: 0 pro | 1 overclaim/rebaixado | 3 uso
"""
import sys, os, json, argparse, hashlib
from pathlib import Path

VALID_LEVELS = {"mapped", "incorporada", "reproduzivel",
                "emulador_provado", "default_senior"}

def cross_check(registry_path, matrix_path):
    """Toda tecnica citada na matriz HUMANA existe no registry?

    L003: o registry mantinha S05/S06 honestamente em `mapped` ("provar em
    emulador"), mas a matriz .md afirmava os numeros como NOTA DURA. Como
    nenhum gate lia o .md, dois fatos do Mega Drive circularam como lei do SMS
    ate serem refutados em emulador. Fato afirmado na matriz sem entrada no
    registry e claim invisivel.
    """
    import re
    if not os.path.exists(matrix_path):
        return []
    try:
        d = json.load(open(registry_path))
    except (ValueError, OSError):
        return []          # audit() ja reporta registry ilegivel
    if not isinstance(d, dict) or not isinstance(d.get("tracks", d), dict):
        return []          # audit() reporta schema invalido
    ids = set()
    for _, m in (d.get("tracks", d)).items():
        for tech in (m if isinstance(m, dict) else {}):
            mm = re.match(r"([A-Z]\d{2})", tech)
            if mm:
                ids.add(mm.group(1))
    texto = open(matrix_path, encoding="utf-8", errors="replace").read()
    citadas = set(re.findall(r"^\|\s*([A-Z]\d{2})\s*\|", texto, re.M))
    # So cobra as FAMILIAS que o registry conhece (V/S/P/M/Z/B/A/I...). As secoes
    # de processo da matriz (E = estetica, Q = verificacao) nao sao tecnicas de
    # hardware, nao tem escada de proficiencia e sao governadas por outros gates.
    familias = {t[0] for t in ids}
    faltando = {t for t in citadas - ids if t[0] in familias}
    return [f"matriz cita '{t}' que NAO existe no registry "
            "(fato afirmado sem escada de proficiencia = claim invisivel)"
            for t in sorted(faltando)]

def evidence_problems(evidence, level, root):
    """Custódia dos arquivos; não julga o conteúdo nem promove a técnica."""
    if not isinstance(evidence, dict):
        return ["evidence precisa de scope e artifacts com path/kind/sha256; prosa nao e custodia"]
    if not isinstance(evidence.get("scope"), str) or not evidence["scope"].strip():
        return ["evidence.scope ausente"]
    refs = evidence.get("artifacts")
    if not isinstance(refs, list) or not refs:
        return ["evidence.artifacts ausente/vazio"]
    root = Path(root).resolve()
    problems, kinds, paths, rom_hashes, reports = [], set(), set(), set(), []
    for ref in refs:
        try:
            if not isinstance(ref, dict):
                raise ValueError("artifact nao objeto")
            rel, kind, sha = ref.get("path"), ref.get("kind"), ref.get("sha256")
            if not isinstance(rel, str) or not rel.strip():
                raise ValueError("path ausente")
            path = Path(rel)
            if path.is_absolute() or ".." in path.parts or str(path) != rel:
                raise ValueError("path deve ser relativo canonico ao root")
            target = (root / path).resolve()
            if not target.is_relative_to(root) or target in paths:
                raise ValueError("path externo/duplicado")
            paths.add(target)
            if kind not in {"source", "build", "recipe", "rom", "media", "report"}:
                raise ValueError("kind invalido")
            if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                raise ValueError("sha256 invalido")
            if not target.is_file() or target.stat().st_size == 0:
                raise ValueError("artefato ausente/vazio/nao arquivo")
            with target.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != sha:
                raise ValueError("sha256 divergente")
            kinds.add(kind)
            if kind == "rom":
                rom_hashes.add(sha)
            if kind == "report":
                reports.append(json.loads(target.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError) as error:
            problems.append(f"artifact: {error}")
    required = {"source", "build"}
    if level == "reproduzivel":
        required.add("recipe")
    if level in {"emulador_provado", "default_senior"}:
        required |= {"rom", "media", "report"}
        if len(rom_hashes) != 1:
            problems.append("prova requer exatamente uma identidade ROM")
        for report in reports:
            if (not isinstance(report, dict) or
                    not isinstance(report.get("rom_sha256"), str) or
                    report.get("rom_sha256") not in rom_hashes or
                    not isinstance(report.get("session_id"), str) or
                    not report["session_id"].strip()):
                problems.append("report sem rom_sha256 correspondente/session_id")
    if required - kinds:
        problems.append("artifacts faltando: " + ", ".join(sorted(required - kinds)))
    return problems


def audit(registry_path, root=None):
    try:
        d = json.load(open(registry_path))
    except (ValueError, OSError) as e:
        return [f"registry ilegivel: {e}"]
    if not isinstance(d, dict) or not d:
        return ["registry precisa ser objeto nao vazio"]
    # suporta {"tracks": {...}} (estrutura SMSForge) ou {track: {...}} direto
    tracks = d.get("tracks", d)
    if not isinstance(tracks, dict) or not tracks:
        return ["tracks precisa ser objeto nao vazio"]
    root = root or Path(__file__).resolve().parents[2]
    problems = []
    for track, m in tracks.items():
        if not isinstance(m, dict) or not m:
            problems.append(f"{track}: trilha invalida/vazia")
            continue
        for tech, meta in m.items():
            if not isinstance(meta, dict):
                problems.append(f"{track}/{tech}: entrada nao objeto")
                continue
            lvl = meta.get("level", "")
            if not isinstance(lvl, str) or lvl not in VALID_LEVELS:
                problems.append(f"{track}/{tech}: nivel invalido '{lvl}'")
                continue
            if lvl != "mapped":
                problems.extend(f"{track}/{tech}: {p}" for p in
                                evidence_problems(meta.get("evidence"), lvl, root))
    return problems

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", default=os.path.join(
        os.path.dirname(__file__), "..", "..", "doc", "05_technical", "01_registry_maestria_sms.json"))
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]),
                    help="raiz dos paths de evidence (default: checkout)")
    args = ap.parse_args()
    if args.self_check:
        import tempfile
        d = tempfile.mkdtemp(prefix="smsmr_")
        # mapped nao promete prova; os casos de custodia ficam abaixo.
        okp = os.path.join(d, "ok.json")
        json.dump({"trilhaA": {"T1": {"level": "mapped"}}}, open(okp, "w"))
        assert not audit(okp)
        # caso overclaim (sem evidence)
        bp = os.path.join(d, "bad.json")
        json.dump({"trilhaA": {"T1": {"level": "default_senior"}}}, open(bp, "w"))
        assert audit(bp), "default_senior sem evidence deveria reprovar"
        # cross-check: tecnica citada na matriz sem entrada no registry reprova
        import tempfile as _tf
        d2 = _tf.mkdtemp(prefix="smsmx_")
        reg = os.path.join(d2, "01_registry_maestria_sms.json")
        mtx = os.path.join(d2, "00_matriz_maestria_sms.md")
        json.dump({"sprites": {"S01 x": {"level": "mapped", "evidence": "e"}}},
                  open(reg, "w"))
        open(mtx, "w").write("| S01 | ok |\n")
        assert not cross_check(reg, mtx), "tecnica presente nos dois nao reprova"
        open(mtx, "w").write("| S01 | ok |\n| S09 | fato duro sem registry |\n")
        assert cross_check(reg, mtx), "faltou pegar tecnica citada fora do registry"
        import copy
        with _tf.TemporaryDirectory(prefix="sms_custody_") as tmp:
            root = Path(tmp)
            refs = []
            for kind in ("source", "build", "recipe", "rom", "media"):
                p = root / kind
                p.write_bytes(("synthetic fixture " + kind).encode())
                refs.append({"path": kind, "kind": kind,
                             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
            rom_sha = next(r["sha256"] for r in refs if r["kind"] == "rom")
            p = root / "report.json"
            p.write_text(json.dumps({"rom_sha256": rom_sha, "session_id": "fixture"}))
            refs.append({"path": p.name, "kind": "report",
                         "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
            ev = {"scope": "fixture de custodia, nao prova de jogo", "artifacts": refs}
            for lvl in VALID_LEVELS - {"mapped"}:
                assert not evidence_problems(ev, lvl, root)
                assert evidence_problems("gate passou", lvl, root)
            for field, value in (("path", "missing"), ("path", "../outside"),
                                 ("path", str(root / "source")), ("sha256", "0" * 64),
                                 ("kind", "unknown")):
                bad = copy.deepcopy(ev); bad["artifacts"][0][field] = value
                assert evidence_problems(bad, "emulador_provado", root)
            for bad in ({}, {"scope": "x", "artifacts": []},
                        {"scope": "x", "artifacts": [None]},
                        {"scope": "x", "artifacts": refs + refs[:1]}):
                assert evidence_problems(bad, "emulador_provado", root)
            p.write_text(json.dumps({"rom_sha256": "0" * 64, "session_id": "fixture"}))
            bad = copy.deepcopy(ev)
            bad["artifacts"][-1]["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
            assert evidence_problems(bad, "emulador_provado", root)
            for payload in ([], {}, {"tracks": []}, {"tracks": {"x": {"T1": None}}},
                            {"tracks": {"x": {"T1": {"level": []}}}}):
                p.write_text(json.dumps(payload))
                assert audit(p, root)
        print("[SELF-CHECK OK] mastery_registry (overclaim + tecnica citada na "
              "matriz sem entrada no registry)")
        return 0
    problems = audit(args.registry, args.root)
    problems += cross_check(args.registry, os.path.join(
        os.path.dirname(args.registry), "00_matriz_maestria_sms.md"))
    if problems:
        for p in problems:
            print(f"[FAIL] {p}")
        return 1
    print("[PASS] estrutura/custodia da matriz; nao certifica dominio, qualidade ou ROM atual")
    return 0

if __name__ == "__main__":
    sys.exit(main())
