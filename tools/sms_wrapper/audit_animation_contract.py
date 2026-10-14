#!/usr/bin/env python3
"""Validate authored animation contracts before sprite production.

This gate checks sequence coverage, pose endpoints, frame counts, animated
entity tracks, the required seven applied principles, and explicit hardware
budget status. It does not inspect pixels, judge artistic quality, or prove
that a proposal is balanced in a running game.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PRINCIPLES = {
    "squash_and_stretch",
    "anticipation",
    "staging",
    "straight_ahead_pose_to_pose",
    "follow_through_overlap",
    "slow_in_slow_out",
    "arcs",
    "secondary_action",
    "timing",
    "exaggeration",
    "solid_drawing",
    "appeal",
}


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def audit(manifest):
    problems = []
    if manifest.get("schema") != "sms_animation_contract_v1":
        problems.append("schema: esperado sms_animation_contract_v1")
    if not _nonempty(manifest.get("project")) or not _nonempty(manifest.get("character_id")):
        problems.append("project/character_id: identidade ausente")
    hardware = manifest.get("timing_and_hardware")
    if not isinstance(hardware, dict) or not _nonempty(hardware.get("tick_definition")):
        problems.append("timing_and_hardware.tick_definition ausente")
    elif str(hardware.get("max_frames_status", "")).lower().startswith("pending") and hardware.get("max_frames_per_sheet") is not None:
        problems.append("max_frames_per_sheet deve ser null quando pending")
    catalog = manifest.get("principles_catalog")
    if not isinstance(catalog, list) or {x.get("id") for x in catalog if isinstance(x, dict)} != PRINCIPLES:
        problems.append("principles_catalog deve enumerar exatamente os 12 princípios")

    sequences = manifest.get("sequences")
    if not isinstance(sequences, list) or not sequences:
        return problems + ["sequences: lista ausente ou vazia"]

    by_id = {}
    for seq in sequences:
        sid = seq.get("id", "?") if isinstance(seq, dict) else "?"
        if sid in by_id:
            problems.append(f"duplicate_sequence_id: {sid}")
        by_id[sid] = seq

    for required in manifest.get("required_sequence_ids", []):
        if required not in by_id:
            problems.append(f"required_sequence_missing: {required}")

    for seq in sequences:
        if not isinstance(seq, dict):
            problems.append("sequence: entrada precisa ser objeto")
            continue
        sid = seq.get("id", "?")
        for key in ("title", "category", "status", "motion_contract"):
            if not _nonempty(seq.get(key)):
                problems.append(f"{sid}: {key} ausente")
        frame_ids = seq.get("frame_ids")
        if not isinstance(frame_ids, list) or not frame_ids or any(
                not _nonempty(fid) for fid in frame_ids):
            problems.append(f"{sid}: frame_ids ausente/vazio/inválido")
            frame_ids = []
        if len(set(frame_ids)) != len(frame_ids):
            problems.append(f"{sid}: frame_ids duplicados")
        if seq.get("source_pose_count") != len(frame_ids):
            problems.append(f"{sid}: source_pose_count diverge de frame_ids")
        if seq.get("source_pose_count_status") not in {"proposal", "measured"}:
            problems.append(f"{sid}: source_pose_count_status inválido")
        if seq.get("timing_status") not in {"proposal_unmeasured", "measured"}:
            problems.append(f"{sid}: timing_status inválido")
        durations = seq.get("duration_ticks")
        if not isinstance(durations, list) or len(durations) != len(frame_ids) or any(
                not isinstance(tick, int) or tick < 1 for tick in (durations or [])):
            problems.append(f"{sid}: duration_ticks deve ter um inteiro positivo por pose")
        if not _nonempty(seq.get("initial_state")):
            problems.append(f"{sid}: initial_state ausente")
        if not _nonempty(seq.get("final_state")):
            problems.append(f"{sid}: final_state ausente")
        if not isinstance(seq.get("loop"), bool):
            problems.append(f"{sid}: loop deve ser booleano")

        entities = seq.get("entities")
        if not isinstance(entities, list) or not entities:
            problems.append(f"{sid}: entities ausente/vazio")
            entities = []
        entity_ids = set()
        for entity in entities:
            if not isinstance(entity, dict):
                problems.append(f"{sid}: entidade precisa ser objeto")
                continue
            eid = entity.get("id", "?")
            if eid in entity_ids:
                problems.append(f"{sid}: entidade duplicada {eid}")
            entity_ids.add(eid)
            if entity.get("kind") not in {"character", "object", "effect"}:
                problems.append(f"{sid}/{eid}: kind inválido")
            pose_count = entity.get("source_pose_count")
            if not isinstance(pose_count, int) or pose_count < 1 or pose_count > len(frame_ids):
                problems.append(f"{sid}/{eid}: source_pose_count inválido")
            elif entity.get("kind") == "character" and pose_count != len(frame_ids):
                problems.append(f"{sid}/{eid}: contagem do personagem deve cobrir cada pose da sequência")
            if not _nonempty(entity.get("initial_state")) or not _nonempty(
                    entity.get("final_state")):
                problems.append(f"{sid}/{eid}: estado inicial/final ausente")
            track = entity.get("track")
            if not isinstance(track, list) or len(track) != len(frame_ids) or any(
                    not _nonempty(state) for state in (track or [])):
                problems.append(f"{sid}/{eid}: track deve descrever cada frame")
            elif track and (entity.get("initial_state") != track[0] or
                            entity.get("final_state") != track[-1]):
                problems.append(f"{sid}/{eid}: endpoints divergem do track")
            timing = entity.get("time_contract")
            if not isinstance(timing, dict) or timing.get("mode") not in {
                    "sequence_frames", "independent_projectile", "event_effect"}:
                problems.append(f"{sid}/{eid}: time_contract/mode ausente ou inválido")
            elif timing.get("mode") == "sequence_frames":
                if timing.get("duration_ticks") != sum(durations or []):
                    problems.append(f"{sid}/{eid}: duração da entidade deve fechar com a timeline da sequência")
            else:
                lifetime = timing.get("total_lifetime_ticks")
                phases = timing.get("phases")
                if (not _nonempty(timing.get("start_event")) or
                        not isinstance(lifetime, int) or lifetime < 1 or
                        not isinstance(phases, list) or not phases):
                    problems.append(f"{sid}/{eid}: timeline independente requer evento, lifetime e fases")
                elif any(not isinstance(p, dict) or
                         not isinstance(p.get("duration_ticks"), int) or
                         p.get("duration_ticks", 0) < 1 for p in phases):
                    problems.append(f"{sid}/{eid}: cada fase requer duration_ticks positivo")
                elif sum(p["duration_ticks"] for p in phases) != lifetime:
                    problems.append(f"{sid}/{eid}: fases não somam total_lifetime_ticks")
            entity_hardware = entity.get("hardware_sprite_objects")
            if (not isinstance(entity_hardware, dict) or
                    entity_hardware.get("status") not in {"pending", "measured"}):
                problems.append(f"{sid}/{eid}: hardware_sprite_objects precisa declarar pending/measured")
            elif entity_hardware.get("status") == "pending" and entity_hardware.get("count") is not None:
                problems.append(f"{sid}/{eid}: contagem hardware pending não pode parecer definitiva")
            elif entity_hardware.get("status") == "measured" and (
                    not isinstance(entity_hardware.get("count"), int) or
                    entity_hardware["count"] < 1 or
                    not _nonempty(entity_hardware.get("evidence"))):
                problems.append(f"{sid}/{eid}: contagem hardware medida requer count e evidence")
        if not any(e.get("kind") == "character" for e in entities if isinstance(e, dict)):
            problems.append(f"{sid}: track do personagem ausente")

        applied = seq.get("principles_applied")
        excluded = seq.get("principles_not_applied")
        if not isinstance(applied, list):
            applied = []
            problems.append(f"{sid}: principles_applied ausente")
        if not isinstance(excluded, list):
            excluded = []
            problems.append(f"{sid}: principles_not_applied ausente")
        applied_ids = []
        for item in applied:
            if not isinstance(item, dict):
                problems.append(f"{sid}: princípio aplicado precisa ser objeto")
                continue
            pid = item.get("id")
            applied_ids.append(pid)
            if pid not in PRINCIPLES:
                problems.append(f"{sid}: princípio desconhecido {pid}")
            if not _nonempty(item.get("planned_visual_cue")):
                problems.append(f"{sid}/{pid}: pista visual planejada ausente")
            evidence = item.get("frame_ids")
            if not isinstance(evidence, list) or not evidence or any(
                    fid not in frame_ids for fid in (evidence or [])):
                problems.append(f"{sid}/{pid}: evidência deve apontar para frame_ids")
        if len(set(applied_ids)) != len(applied_ids):
            problems.append(f"{sid}: princípios aplicados duplicados")
        if len(set(applied_ids)) < 7:
            problems.append(f"{sid}: apenas {len(set(applied_ids))} princípios aplicados; mínimo=7")

        excluded_ids = []
        for item in excluded:
            if not isinstance(item, dict):
                problems.append(f"{sid}: princípio não aplicado precisa ser objeto")
                continue
            pid = item.get("id")
            excluded_ids.append(pid)
            if pid not in PRINCIPLES:
                problems.append(f"{sid}: princípio excluído desconhecido {pid}")
            if not _nonempty(item.get("reason")):
                problems.append(f"{sid}/{pid}: motivo da não aplicação ausente")
        if len(set(excluded_ids)) != len(excluded_ids):
            problems.append(f"{sid}: princípios não aplicados duplicados")
        if set(applied_ids) & set(excluded_ids):
            problems.append(f"{sid}: princípio está aplicado e excluído")
        if set(applied_ids) | set(excluded_ids) != PRINCIPLES:
            missing = sorted(PRINCIPLES - set(applied_ids) - set(excluded_ids))
            extra = sorted((set(applied_ids) | set(excluded_ids)) - PRINCIPLES)
            problems.append(f"{sid}: revisão dos 12 incompleta; ausentes={missing} extras={extra}")

        parts = seq.get("hardware_sprite_objects")
        if not isinstance(parts, dict) or parts.get("status") not in {"pending", "measured"}:
            problems.append(f"{sid}: hardware_sprite_objects precisa declarar pending/measured")
        elif parts.get("status") == "pending" and parts.get("count") is not None:
            problems.append(f"{sid}: contagem de objetos não medida não pode parecer definitiva")
        elif parts.get("status") == "measured" and (
                not isinstance(parts.get("count"), int) or parts["count"] < 1 or
                not _nonempty(parts.get("evidence"))):
            problems.append(f"{sid}: contagem medida requer count e evidence")
        tiles = seq.get("unique_tile_count")
        if not isinstance(tiles, dict) or tiles.get("status") not in {"pending", "measured"}:
            problems.append(f"{sid}: unique_tile_count precisa declarar pending/measured")
        elif tiles.get("status") == "pending" and tiles.get("count") is not None:
            problems.append(f"{sid}: unique_tile_count pending não pode parecer definitivo")
        elif tiles.get("status") == "measured" and (
                not isinstance(tiles.get("count"), int) or tiles["count"] < 0 or
                not _nonempty(tiles.get("evidence"))):
            problems.append(f"{sid}: unique_tile_count medida requer count e evidence")
        if seq.get("palette_and_vblank_status") not in {"pending", "measured"}:
            problems.append(f"{sid}: palette_and_vblank_status inválido")

    moves = manifest.get("combat_proposals", [])
    if not isinstance(moves, list):
        problems.append("combat_proposals: deve ser lista")
        moves = []
    for move in moves:
        mid = move.get("id", "?") if isinstance(move, dict) else "?"
        if not isinstance(move, dict):
            problems.append("combat_proposals: entrada precisa ser objeto")
            continue
        if move.get("animation_id") not in by_id:
            problems.append(f"{mid}: animation_id não existe")
        for key in ("source_relation", "balance_rationale", "risk_and_counterplay",
                    "status", "test_plan"):
            if not _nonempty(move.get(key)):
                problems.append(f"{mid}: {key} ausente")
        frame_data = move.get("frame_data_candidate")
        required_numbers = ("startup_ticks", "active_ticks", "recovery_ticks",
                            "reach_px", "damage_points")
        if not isinstance(frame_data, dict) or any(
                not isinstance(frame_data.get(key), int) or frame_data[key] < 0
                for key in required_numbers):
            problems.append(f"{mid}: frame_data_candidate incompleto/inválido")
        elif not frame_data.get("is_approved", False) and frame_data.get("status") != "proposal_unmeasured":
            problems.append(f"{mid}: números não aprovados devem ser proposal_unmeasured")

    return problems


def _minimal_valid():
    applied_ids = sorted(PRINCIPLES)[:7]
    excluded_ids = sorted(PRINCIPLES - set(applied_ids))
    frames = ["A", "B"]
    return {
        "schema": "sms_animation_contract_v1",
        "project": "demo", "character_id": "hero",
        "principles_catalog": [{"id": pid} for pid in PRINCIPLES],
        "timing_and_hardware": {"tick_definition": "tick lógico", "max_frames_status": "pending",
                                "max_frames_per_sheet": None},
        "required_sequence_ids": ["demo"],
        "sequences": [{
            "id": "demo", "title": "Demo", "category": "test", "status": "proposal",
            "motion_contract": "Movimento de fixture.", "source_pose_count_status": "proposal",
            "timing_status": "proposal_unmeasured", "palette_and_vblank_status": "pending",
            "unique_tile_count": {"status": "pending", "count": None},
            "source_pose_count": 2, "frame_ids": frames,
            "duration_ticks": [2, 2], "initial_state": "start", "final_state": "end",
            "loop": False,
            "entities": [{"id": "hero", "kind": "character", "initial_state": "start",
                          "final_state": "end", "source_pose_count": 2,
                          "track": ["start", "end"],
                          "time_contract": {"mode": "sequence_frames", "duration_ticks": 4},
                          "hardware_sprite_objects": {"status": "pending", "count": None}}],
            "principles_applied": [
                {"id": pid, "planned_visual_cue": "planejada para o frame B", "frame_ids": ["B"]}
                for pid in applied_ids],
            "principles_not_applied": [
                {"id": pid, "reason": "não necessário neste exemplo"}
                for pid in excluded_ids],
            "hardware_sprite_objects": {"status": "pending", "count": None},
        }],
        "combat_proposals": [],
    }


def self_check():
    good = _minimal_valid()
    assert audit(good) == [], audit(good)
    bad = json.loads(json.dumps(good))
    bad["sequences"][0]["principles_applied"] = bad["sequences"][0]["principles_applied"][:6]
    result = audit(bad)
    assert any("mínimo=7" in item for item in result), result
    bad = json.loads(json.dumps(good))
    bad["sequences"][0]["source_pose_count"] = 3
    assert any("source_pose_count diverge" in item for item in audit(bad))
    bad = json.loads(json.dumps(good))
    bad["sequences"][0]["entities"][0]["track"] = ["start"]
    assert any("track deve descrever cada frame" in item for item in audit(bad))
    bad = json.loads(json.dumps(good))
    bad["sequences"][0]["entities"][0]["time_contract"] = {
        "mode": "independent_projectile", "start_event": "release",
        "total_lifetime_ticks": 5, "phases": [{"duration_ticks": 2}]}
    assert any("fases não somam" in item for item in audit(bad))
    print("[SELF-CHECK OK] animation_contract (endpoints, contagem, tracks, "
          "timelines de entidade, 12 princípios, mínimo de 7 e hardware pending)")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        return self_check()
    if not args.manifest:
        print("uso: audit_animation_contract.py --manifest <json> | --self-check",
              file=sys.stderr)
        return 3
    try:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] manifest ilegível: {exc}", file=sys.stderr)
        return 1
    problems = audit(manifest)
    if problems:
        for problem in problems:
            print(f"[FAIL] {problem}")
        return 1
    print(f"[OK] animation_contract: {len(manifest['sequences'])} sequências, "
          f"{sum(s['source_pose_count'] for s in manifest['sequences'])} poses propostas; "
          "contagens metasprite/runtime continuam separadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
