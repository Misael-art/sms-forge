#!/usr/bin/env python3
"""Audita contrato de engenharia MUGEN→SMS; não aprova arte nem substitui gates de ROM.

--delivery exige provas por capacidade vinculadas ao binário, além do contrato.
Um PASS significa contrato completo, nunca promoção AAA automática.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile

CAPABILITIES = (
    "data_only_character_swap", "fighter_scale", "sprite_schedule",
    "rom_banking_capacity", "ram_vram_layout", "worst_frame",
    "combat_round_match", "input_latency_animation", "stage_hud",
    "psg_music_sfx", "visual_delivery", "source_fidelity",
)
TECHNIQUES = (
    "bank_switching", "tall_metasprites", "intelligent_flicker",
    "raster_palette", "hud_bg", "psg_channel_priority", "hscroll_bands",
    "display_window", "pcm_frozen", "software_flip", "bg_fx",
    "prefetch", "fm_fallback", "pcm_line_irq", "fm_custom_patch",
    "psg_arpeggio", "palette_cycle", "tile_animation", "left_mask",
    "raster_vertical_stretch", "cross_actor_pattern_dedup",
)
STATUSES = {"planned", "implemented", "measured", "accepted"}
DECISIONS = {"baseline", "candidate", "rejected_as_described"}
SCHEMA = "sms_mugen_engine_contract_v1"
MAKESMS_MAX_MERGES = 8

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def local_file(root, rel):
    if not isinstance(rel, str) or Path(rel).is_absolute():
        raise ValueError("referência deve ser relativa ao projeto")
    path = (root / rel).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("referência ausente/fora do projeto: " + rel)
    return path


def mapper_merge_count(project):
    """None when no build manifest is supplied; otherwise validate merge arity."""
    manifest_path = Path(project) / ".mddev/project.json"
    if not manifest_path.is_file():
        return None, []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [".mddev/project.json ilegível: " + str(exc)]
    extra = manifest.get("toolchain", {}).get("makesms_extra", [])
    if not isinstance(extra, list):
        return None, ["toolchain.makesms_extra deve ser lista"]
    count = sum(value == "-mbank" for value in extra)
    errors = []
    for index, value in enumerate(extra):
        if value == "-mbank" and (index + 1 >= len(extra) or
                                   not isinstance(extra[index + 1], str) or
                                   ":" not in extra[index + 1]):
            errors.append("-mbank sem argumento file:src:banks:dst")
    if count > MAKESMS_MAX_MERGES:
        errors.append(f"{count} mapas -mbank excedem MAX_MERGES={MAKESMS_MAX_MERGES}; "
                      "makesms pode descartar mapas excedentes")
    return count, errors

def audit(project, contract, delivery=False):
    problems = []
    if not isinstance(contract, dict):
        return {"status": "blocked", "problems": ["contrato deve ser objeto JSON"]}
    target = contract.get("target", {})
    if not isinstance(target, dict):
        target = {}
    if contract.get("schema") != SCHEMA:
        problems.append("schema de contrato incompatível")
    expected = {"console": "SMS", "canvas": [256, 192], "sprite_mode": "8x16",
                "sat_entries": 64, "sprites_per_line": 8, "ram_bytes": 8192,
                "vram_bytes": 16384, "bank_bytes": 16384, "mapper": "sega",
                "fighter_height_ratio": [0.45, 0.55], "rom_capacity_target_bytes": 1048576}
    for key, value in expected.items():
        if target.get(key) != value:
            problems.append("target divergente/ausente: " + key)
    useful = target.get("combat_height_px")
    if type(useful) is not int or not 128 <= useful <= 192:
        problems.append("combat_height_px deve declarar área útil entre 128 e 192")
        height = None
    else:
        height = [math.ceil(useful * .45), math.floor(useful * .55)]
    if contract.get("scale_policy") != "uniform_per_character_scene_contract":
        problems.append("escala exige contrato uniforme por personagem/cena")
    if contract.get("legacy_profile_delivery_allowed") is not False:
        problems.append("perfil histórico não pode autorizar delivery")
    merge_count, merge_problems = mapper_merge_count(project)
    problems.extend(merge_problems)
    rows = contract.get("capabilities", [])
    rows = rows if isinstance(rows, list) else []
    caps = {c.get("id"): c for c in rows if isinstance(c, dict)}
    if len(caps) != len(rows) or set(caps) != set(CAPABILITIES):
        problems.append("capacidades obrigatórias ausentes, duplicadas ou desconhecidas")
    for key, cap in caps.items():
        if cap.get("status") not in STATUSES or not cap.get("owner") or not cap.get("acceptance"):
            problems.append("capacidade sem estado/owner/critério: " + str(key))
    rows = contract.get("techniques", [])
    rows = rows if isinstance(rows, list) else []
    techniques = {c.get("id"): c for c in rows if isinstance(c, dict)}
    if len(techniques) != len(rows) or set(techniques) != set(TECHNIQUES):
        problems.append("portfólio técnico incompleto/duplicado")
    for key, tech in techniques.items():
        if tech.get("decision") not in DECISIONS or not tech.get("proof") or not tech.get("fallback"):
            problems.append("técnica sem decisão/prova/fallback: " + str(key))
    if techniques.get("raster_vertical_stretch", {}).get("decision") != "rejected_as_described":
        problems.append("Y-scroll por linha não implementa o stretching proposto no SMS")
    if delivery:
        if contract.get("runtime_profile") == "legacy_probe_quarter":
            problems.append("runtime ainda usa perfil técnico 1:4/48px")
        rom_sha = None
        try:
            rom_sha = sha(local_file(project, contract.get("rom")))
        except (OSError, ValueError) as exc:
            problems.append(str(exc))
        primary_seen = set()
        for key in CAPABILITIES:
            cap = caps.get(key, {})
            if cap.get("status") != "accepted":
                problems.append("capacidade sem aceite comprovado: " + key)
                continue
            try:
                ref = cap.get("evidence", {})
                proof_path = local_file(project, ref.get("path"))
                if sha(proof_path) != ref.get("sha256"):
                    raise ValueError("hash da prova divergente")
                proof = json.loads(proof_path.read_text())
                if (proof.get("schema") != "sms_mugen_capability_evidence_v1"
                        or proof.get("capability_id") != key or proof.get("status") != "passed"
                        or proof.get("rom_sha256") != rom_sha):
                    raise ValueError("prova sem schema/capacidade/PASS/ROM correspondente")
                artifacts = proof.get("artifacts", [])
                if not artifacts:
                    raise ValueError("prova sem artefatos de medição")
                for index, item in enumerate(artifacts):
                    artifact = local_file(project, item.get("path"))
                    digest = sha(artifact)
                    if digest != item.get("sha256"):
                        raise ValueError("hash de artefato divergente")
                    if index == 0:
                        if digest in primary_seen:
                            raise ValueError("mesmo artefato primário reutilizado para outra capacidade")
                        primary_seen.add(digest)
            except (OSError, ValueError, TypeError, AttributeError) as exc:
                problems.append(key + ": " + str(exc))
    return {"schema": "sms_mugen_engine_contract_audit_v1",
            "status": "blocked" if problems else "contract_pass",
            "mode": "delivery_contract" if delivery else "planning",
            "fighter_idle_opaque_height_target_px": height,
            "makesms_bank_merges": merge_count,
            "makesms_bank_merge_limit": MAKESMS_MAX_MERGES,
            "problems": problems, "aaa_approved": False,
            "scope": "contrato e vínculos; gates runtime/visual e revisão independente continuam obrigatórios"}

def self_check():
    c = json.loads((Path(__file__).parent / "mugen_engine_contract_v1.json").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert not audit(root, c)["problems"]
        assert audit(root, c, True)["problems"]
        for field, bad in (("sprites_per_line", 20), ("ram_bytes", 65536), ("combat_height_px", True)):
            m = copy.deepcopy(c); m["target"][field] = bad
            assert audit(root, m)["problems"], field
        m = copy.deepcopy(c); m["capabilities"] = []
        assert audit(root, m)["problems"]
        m = copy.deepcopy(c); m["legacy_profile_delivery_allowed"] = True
        assert audit(root, m)["problems"]
        (root / ".mddev").mkdir()
        project_manifest = root / ".mddev/project.json"
        project_manifest.write_text(json.dumps({"toolchain": {
            "makesms_extra": sum((["-mbank", f"bank{i}.bin:0:1:{i}"]
                                   for i in range(9)), [])}}))
        assert any("MAX_MERGES=8" in problem for problem in audit(root, c)["problems"])
        project_manifest.write_text(json.dumps({"toolchain": {
            "makesms_extra": ["-mbank", "combined.bin:0:35:2"]}}))
        assert not audit(root, c)["problems"]
        c["runtime_profile"] = "scene_authored"; c["rom"] = "fixture.sms"
        (root / c["rom"]).write_bytes(b"synthetic ROM fixture, not emulator evidence")
        for i, cap in enumerate(c["capabilities"]):
            artifact = root / (str(i) + ".trace"); artifact.write_text(cap["id"])
            proof = root / (str(i) + ".json")
            proof.write_text(json.dumps({"schema": "sms_mugen_capability_evidence_v1",
                "capability_id": cap["id"], "status": "passed", "rom_sha256": sha(root / c["rom"]),
                "artifacts": [{"path": artifact.name, "sha256": sha(artifact)}]}))
            cap.update(status="accepted", evidence={"path": proof.name, "sha256": sha(proof)})
        assert not audit(root, c, True)["problems"]
        (root / "0.trace").write_text("tampered")
        assert audit(root, c, True)["problems"]
        (root / c["rom"]).write_bytes(b"new ROM")
        assert audit(root, c, True)["problems"]
        try:
            local_file(root, "../escape")
            raise AssertionError("escape accepted")
        except ValueError:
            pass
    print("[PASS] MUGEN contract self-check: planning, incomplete delivery, hardware, hashes, ROM, path")
    return 0

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--delivery", action="store_true")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    if args.project is None:
        parser.error("--project obrigatório")
    source = args.contract or args.project / "doc/engine_quality_contract.json"
    try:
        report = audit(args.project.resolve(), json.loads(source.read_text()), args.delivery)
    except (OSError, ValueError) as exc:
        report = {"status": "blocked", "problems": [str(exc)], "aaa_approved": False}
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(payload)
    print(payload, end="")
    return 0 if report["status"] == "contract_pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
