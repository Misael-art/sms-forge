#!/usr/bin/env python3
"""audit_reference_boundary.py — testa a declaração de papéis entre fontes.

Para concepts de personagem baseados em jogo e material de outra mídia, o jogo
deve continuar como autoridade de identidade, paleta e comportamento. Referência
suplementar precisa de escopo autorizado, hash e limites registrados no
asset_contract e no lineage. O gate mede completude e consistência dos registros;
não julga fidelidade visual, que continua sob revisão humana.

Uso:
  audit_reference_boundary.py --project <projeto> [--json saida]
  audit_reference_boundary.py --self-check
Exit: 0 consistente | 1 deriva | 3 uso
"""
import argparse
import glob
import json
import os
import re
import shutil
import sys
import tempfile

SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
PRIMARY_ROLES = {"identity", "sms_palette", "gameplay_behavior"}
SUPPLEMENTARY_ROLES = {"costume_construction", "costume_color_mapping"}
LIMIT_FIELDS = (
    "defines_identity",
    "defines_palette",
    "defines_gameplay",
    "defines_lore",
    "copies_pixels",
    "copies_poses",
)


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)


def _audit_contract(project, path):
    errors = []
    contract, err = _load(path)
    rel = os.path.relpath(path, project).replace(os.sep, "/")
    if err:
        return [f"{rel}: contrato ilegivel: {err}"]
    boundary = contract.get("reference_boundary") or {}
    primary = boundary.get("primary_source") or {}
    roles = set(primary.get("roles") or [])
    missing_roles = PRIMARY_ROLES - roles
    if primary.get("medium") != "game_sms" or not primary.get("source"):
        errors.append(f"{rel}: primary_source deve identificar a fonte game_sms")
    if missing_roles:
        errors.append(f"{rel}: primary_source sem papeis {sorted(missing_roles)}")
    if boundary.get("anime_reference_used_for_costume_only") is not True:
        errors.append(f"{rel}: anime_reference_used_for_costume_only deve ser true")
    if boundary.get("anime_reference_used_for_palette_or_moveset") is not False:
        errors.append(f"{rel}: anime nao pode definir palette ou moveset")
    if boundary.get("external_pixels_copied") is not False:
        errors.append(f"{rel}: external_pixels_copied deve ser false")
    if boundary.get("poses_or_composition_copied") is not False:
        errors.append(f"{rel}: poses_or_composition_copied deve ser false")

    supplements = boundary.get("supplementary_sources") or []
    if not isinstance(supplements, list) or not supplements:
        errors.append(f"{rel}: supplementary_sources ausente ou vazio")
        supplements = []
    for i, source in enumerate(supplements):
        prefix = f"{rel}: supplementary_sources[{i}]"
        if source.get("medium") != "anime":
            errors.append(f"{prefix}: medium deve ser anime")
        if source.get("owner_requested") is not True:
            errors.append(f"{prefix}: owner_requested deve ser true")
        if source.get("role") not in SUPPLEMENTARY_ROLES:
            errors.append(f"{prefix}: role deve limitar-se a construcao/mapeamento de figurino")
        for field in LIMIT_FIELDS:
            if source.get(field) is not False:
                errors.append(f"{prefix}: {field} deve ser false")
        if not source.get("source") or not source.get("url"):
            errors.append(f"{prefix}: source e url sao obrigatorios")

    lineage_rel = contract.get("lineage_record") or ""
    if not lineage_rel:
        errors.append(f"{rel}: lineage_record ausente")
        return errors
    lineage_path = os.path.normpath(os.path.join(project, lineage_rel))
    lineage, lineage_err = _load(lineage_path)
    if lineage_err:
        errors.append(f"{rel}: lineage_record '{lineage_rel}' ilegivel: {lineage_err}")
        return errors
    refs = lineage.get("references") or []
    if not isinstance(refs, list) or not refs:
        errors.append(f"{rel}: lineage sem references")
        return errors
    game_refs = []
    anime_refs = []
    for i, ref in enumerate(refs):
        prefix = f"{rel}: lineage.references[{i}]"
        if ref.get("medium") not in {"game_sms", "anime"}:
            errors.append(f"{prefix}: medium deve ser game_sms ou anime")
        role = ref.get("role") or ""
        if not role.strip():
            errors.append(f"{prefix}: role ausente")
        if not SHA256.fullmatch(str(ref.get("sha256") or "")):
            errors.append(f"{prefix}: sha256 deve ter 64 caracteres hexadecimais")
        if ref.get("external_pixels_copied") is not False:
            errors.append(f"{prefix}: external_pixels_copied deve ser false")
        if ref.get("medium") == "game_sms":
            game_refs.append(ref)
        elif ref.get("medium") == "anime":
            anime_refs.append(ref)
            if not any(word in role.lower() for word in ("costume", "garment", "figurino")):
                errors.append(f"{prefix}: anime role deve dizer explicitamente que e figurino")

    if len(game_refs) != 1:
        errors.append(f"{rel}: lineage deve ter exatamente uma referencia game_sms")
    if len(anime_refs) != len(supplements):
        errors.append(f"{rel}: contagem de referencias anime diverge do contrato")
    if game_refs:
        game_role = game_refs[0].get("role", "").lower()
        if not all(word in game_role for word in ("identity", "palette", "gameplay")):
            errors.append(f"{rel}: role da referencia game_sms deve cobrir identity, palette e gameplay")
    return errors


def audit(project):
    root = os.path.join(project, "data", "source_art", "concept_art")
    problems = []
    if not os.path.isdir(root):
        return [f"concept_art ausente: {root}"]
    candidates = sorted(glob.glob(os.path.join(root, "**", "*contract*.json"), recursive=True))
    for path in candidates:
        data, err = _load(path)
        if err:
            continue
        status = str(data.get("status") or "").lower()
        if status.startswith("superseded"):
            continue
        if data.get("schema") == "asset_contract_v1" and "reference_boundary" in data:
            problems.extend(_audit_contract(project, path))
    return problems


def _self_check():
    root = tempfile.mkdtemp(prefix="smsrefboundary_")
    try:
        d = os.path.join(root, "data", "source_art", "concept_art", "demo")
        os.makedirs(d)
        contract_path = os.path.join(d, "demo_asset_contract_v1.json")
        lineage_path = os.path.join(d, "demo_lineage_v1.json")
        rel_lineage = os.path.relpath(lineage_path, root).replace(os.sep, "/")
        contract = {
            "schema": "asset_contract_v1",
            "source_game": "Demo (Master System)",
            "lineage_record": rel_lineage,
            "reference_boundary": {
                "primary_source": {
                    "medium": "game_sms", "source": "Demo - Standing",
                    "roles": sorted(PRIMARY_ROLES),
                },
                "anime_reference_used_for_costume_only": True,
                "anime_reference_used_for_palette_or_moveset": False,
                "external_pixels_copied": False,
                "poses_or_composition_copied": False,
                "supplementary_sources": [{
                    "medium": "anime", "source": "official model sheet",
                    "url": "https://example.invalid/model-sheet",
                    "role": "costume_construction", "owner_requested": True,
                    **{field: False for field in LIMIT_FIELDS},
                }],
            },
        }
        lineage = {"references": [
            {"medium": "game_sms", "role": "game identity, palette and gameplay source",
             "sha256": "a" * 64, "external_pixels_copied": False},
            {"medium": "anime", "role": "costume construction only",
             "sha256": "b" * 64, "external_pixels_copied": False},
        ]}
        with open(contract_path, "w", encoding="utf-8") as f:
            json.dump(contract, f)
        with open(lineage_path, "w", encoding="utf-8") as f:
            json.dump(lineage, f)
        assert not audit(root), audit(root)

        contract["reference_boundary"]["supplementary_sources"][0]["defines_palette"] = True
        with open(contract_path, "w", encoding="utf-8") as f:
            json.dump(contract, f)
        problems = audit(root)
        assert any("defines_palette deve ser false" in p for p in problems), problems

        contract["reference_boundary"]["supplementary_sources"][0]["defines_palette"] = False
        lineage["references"][1]["sha256"] = "bad"
        with open(contract_path, "w", encoding="utf-8") as f:
            json.dump(contract, f)
        with open(lineage_path, "w", encoding="utf-8") as f:
            json.dump(lineage, f)
        problems = audit(root)
        assert any("sha256 deve ter 64" in p for p in problems), problems
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("[SELF-CHECK OK] reference_boundary (authority, scope, copy limits, lineage hashes)")
    return 0


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=os.path.normpath(os.path.join(here, "..", "..")))
    ap.add_argument("--json")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args()
    if args.self_check:
        return _self_check()
    problems = audit(args.project)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"problems": problems, "clean": not problems}, f, indent=2)
    if problems:
        for problem in problems:
            print(f"[FAIL] {problem}")
        return 1
    print("[PASS] fronteiras de referencia declaradas e consistentes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
