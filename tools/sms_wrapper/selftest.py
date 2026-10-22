#!/usr/bin/env python3
"""selftest.py — prova que os gates funcionam ANTES de medir qualquer projeto.

Regra §19/§20 (SMS_GLOBAL): ferramenta de medicao sem self-check nao e fonte;
gate precisa reprovar em teste conhecido e passar em fixture valida.

Bateria: cada gate roda --self-check, depois e desafiado com fixtures
validas (deve PASSAR) e invalidas (deve REPROVAR). Exit 0 so se TUDO verde.
"""
import sys, os, subprocess, tempfile, shutil, hashlib, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

PY = sys.executable or "python3"

def run(args, expect_code, label):
    r = subprocess.run([PY] + args, capture_output=True, text=True, cwd=HERE)
    ok = r.returncode == expect_code
    detail = (r.stdout + r.stderr).strip().splitlines()
    tail = detail[-1][:90] if detail else ""
    print(f"  {'[OK ]' if ok else '[XX ]'} {label}  ({tail})")
    return ok

BOOTSTRAP_REQUIRED = (
    ".mddev/project.json", "doc/00-diretrizes-agente.md", "doc/10-memory-bank.md",
    "doc/11-gdd.md", "doc/12-roteiro.md", "doc/13-spec-cenas.md",
    "doc/15-tdd.md", "doc/artifact_registry.json", "src/main.c", "build.sh",
)

def _check_bootstrap():
    """Cria um projeto descartavel e prova que a hierarquia de verdade materializa."""
    name = "_selftest_bootstrap_tmp"
    dest = os.path.normpath(os.path.join(HERE, "..", "..", "SMS_projects", name))
    script = os.path.join(HERE, "new_project.sh")
    if os.path.exists(dest):
        shutil.rmtree(dest, ignore_errors=True)
    try:
        r = subprocess.run(["bash", script, name], capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stdout + r.stderr).strip().splitlines()
            print(f"  [XX ] bootstrap new_project.sh falhou  ({tail[-1][:80] if tail else ''})")
            return False
        # ausente OU vazio conta como nao materializado
        bad = [f for f in BOOTSTRAP_REQUIRED
               if not (os.path.isfile(os.path.join(dest, f))
                       and os.path.getsize(os.path.join(dest, f)) > 0)]
        if bad:
            print(f"  [XX ] bootstrap sem hierarquia de verdade  (falta: {', '.join(bad[:3])})")
            return False
        from artifact_registry import audit as audit_registry
        registry = json.load(open(os.path.join(dest, "doc/artifact_registry.json")))
        report = audit_registry(dest, registry, scan=True)
        if not report["ok"]:
            print(f"  [XX ] bootstrap artifact registry invalid: {report['problems']}")
            return False
        leftover = subprocess.run(["grep", "-rl", "__PROJECT_NAME__", dest],
                                  capture_output=True, text=True)
        if leftover.returncode == 0:
            print("  [XX ] bootstrap deixou placeholder __PROJECT_NAME__ sem substituir")
            return False
        print(f"  [OK ] bootstrap materializa hierarquia de verdade  "
              f"({len(BOOTSTRAP_REQUIRED)} arquivos, sem placeholder)")
        return True
    finally:
        shutil.rmtree(dest, ignore_errors=True)

def _art_review_manifest(root, asset_kind="concept", required_axes=None):
    """Create a hash-bound, structurally complete art-review fixture."""
    os.makedirs(root, exist_ok=True)
    for name in ("asset.png", "source.png", "reference.png", "review.json"):
        with open(os.path.join(root, name), "wb") as stream:
            stream.write(name.encode("ascii"))

    def ref(name):
        path = os.path.join(root, name)
        digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
        return {"path": name, "sha256": digest}

    axes = required_axes or ["face_detail"]
    manifest = {
        "schema": "sms_art_review_checklist_v1",
        "asset_id": "selftest_art_review",
        "producer": "artist",
        "asset": dict(ref("asset.png"), kind=asset_kind),
        "source_evidence": ref("source.png"),
        "required_characters": ["alpha"],
        "required_axes": axes,
        "characters": [{
            "id": "alpha",
            "references": [ref("reference.png")],
            "observed_defects": [],
            "revision_notes": ["fixture review"],
            "review_axes": {
                axis: {"status": "pass", "note": "fixture inspected"}
                for axis in axes
            },
        }],
        "independent_review": {
            "status": "passed",
            "reviewer": "independent_reviewer",
            "report": ref("review.json"),
        },
        "owner_approval": {
            "approved": True,
            "reviewer": "owner",
            "date": "2026-01-01",
            "scope": "selftest fixture",
        },
    }
    path = os.path.join(root, "checklist.json")
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(manifest, stream)
    return path

def main():
    import gen_fixtures
    results = []
    print("== Fase 1: self-check de cada gate ==")
    for g in ("build_inner.py", "audit_validate_resources.py", "audit_sprite_line_sim.py",
              "audit_luma_floor.py", "audit_provenance.py", "audit_claims.py",
              "capture_evidence.py",
              "audit_meaningful_change.py", "audit_placeholder_quarantine.py",
              "audit_deterministic_boot.py", "canonical_fixture_gate.py",
              "audit_mastery_registry.py",
              "audit_specialization.py",
              "audit_audio.py",
              "measure_fps.py",
              "validate_measurement_tools.py",
              "audit_doc_sync.py",
              "screenshot_semantic_gate.py",
              "seal_fresh_evidence_bundle.py",
              "reconcile_claims.py",
              "axis_projection.py", "audit_silhouette_integrity.py",
              "audit_sprite_mode.py",
              "capture_audio.py",
              "audit_render_fidelity.py",
              "audit_hardware_constants.py",
              "audit_debug_markers.py",
              "audit_observed_cases.py",
              "audit_tilemap_bounds.py",
              "audit_tilemap_mirror.py",
              "audit_vscroll_wrap.py",
              "measure_frame_advance.py",
              "measure_runtime_probe.py",
              "audit_causal_persistence.py",
              "audit_visual_delivery.py",
              "audit_rom_asset_binding.py",
              "harness_orchestration.py",
              "artifact_registry.py", "audit_source_raster.py",
              "audit_subagent_session.py",
              "blastem_sms.py", "audit_blastem_sms.py",
              "blastem_diagnostics.py", "blastem_maintenance.py",
              "blastem_dump_diff.py",
              "audit_counter_window.py",
              "audit_stage_attribution.py",
              "audit_import_semantics.py",
              "quality_review_router.py",
              "audit_animation_semantics.py",
              "audit_learning_capture.py",
              "audit_psg_channel_binding.py",
              "audit_hscroll_blank.py",
              "audit_symbol_size_sync.py",
              "audit_psg_redundancy.py",
              "emulator_input.py",
              "emulator_session.py",
              "capture_video.py",
              "make_psg_assets.py",
              "png_to_sms_tiles.py",
              "pack_sms_metasprite.py",
              "prepare_sms_pixel_art.py",
              "audit_audio_provenance.py",
              "measure_worst_frame.py",
              "audit_header_claims.py", "audit_mugen_engine_contract.py",
              "audit_art_review_checklist.py",
              "mugen2sms/runtime/vram_plan.py",
              "mugen2sms/runtime/commit_budget.py"):
        results.append(run([os.path.join(HERE, g), "--self-check"], 0,
                           f"selfcheck:{g}"))
    print("== Fase 2: fixtures geradas ==")
    tmp = tempfile.mkdtemp(prefix="smsforge_selftest_")
    from artifact_registry import fixture as artifact_fixture, audit as audit_artifacts
    artifact_project = os.path.join(tmp, "artifact_game")
    registry = artifact_fixture(artifact_project)
    ok = audit_artifacts(artifact_project, registry, scan=True)["ok"]
    results.append(ok); print(f"  [{'OK ' if ok else 'XX '}] unique artifact registry accepted")
    registry["heads"].append(dict(registry["heads"][0]))
    rejected = not audit_artifacts(artifact_project, registry)["ok"]
    results.append(rejected); print(f"  [{'OK ' if rejected else 'XX '}] competing artifact heads rejected")
    from audit_blastem_sms import fixture as blastem_fixture,audit as audit_blastem
    blastem_root,blastem_record=blastem_fixture(tmp)
    ok=audit_blastem(blastem_root)["ok"]
    results.append(ok);print(f"  [{'OK ' if ok else 'XX '}] synthetic BlastEm SMS contract accepted")
    blastem_record["fps_claim"]=True
    with open(os.path.join(blastem_root,"session.json"),"w") as f:json.dump(blastem_record,f)
    reject=not audit_blastem(blastem_root)["ok"]
    results.append(reject);print(f"  [{'OK ' if reject else 'XX '}] BlastEm stepping promoted to FPS rejected")
    from audit_counter_window import fixture as counter_fixture,evaluate as evaluate_counter
    counter=counter_fixture(tmp);ok=evaluate_counter(counter,True)["ok"]
    results.append(ok);print(f"  [{'OK ' if ok else 'XX '}] counter rollover bounded exact accepted")
    counter.update(before=155,after=184,max_events=358)
    reject=not evaluate_counter(counter,True)["ok"]
    results.append(reject);print(f"  [{'OK ' if reject else 'XX '}] 8-bit counter ambiguous 29/285 exact claim rejected")
    from audit_art_review_checklist import CONCEPT_SHEET_REQUIRED_AXES,audit as audit_art
    art_root=os.path.join(tmp,"concept_layout");os.makedirs(art_root)
    art_path=_art_review_manifest(art_root,"character_concept_model_sheet",sorted(CONCEPT_SHEET_REQUIRED_AXES))
    art=json.load(open(art_path));ok=audit_art(art,art_root,True)["exit_code"]==0
    results.append(ok);print(f"  [{'OK ' if ok else 'XX '}] complete concept final-layout review accepted")
    art["required_axes"].remove("document_and_layout")
    del art["characters"][0]["review_axes"]["document_and_layout"]
    reject=audit_art(art,art_root,True)["exit_code"]==1
    results.append(reject);print(f"  [{'OK ' if reject else 'XX '}] concept final-layout omission rejected")
    from audit_learning_capture import _stale_in
    ok=not _stale_in("Sessão privada por ID; vídeo usa timeline completa; legado supersedido: o canal é kdotool+ydotool")
    results.append(ok);print(f"  [{'OK ' if ok else 'XX '}] skill QA vigente e menção histórica aceita")
    reject=bool(_stale_in("pkill -f Emulicious.jar antes da captura"))
    results.append(reject);print(f"  [{'OK ' if reject else 'XX '}] skill com encerramento global de emulador rejeitada")
    from audit_subagent_session import fixture as worker_fixture, validate_report as validate_worker
    qa_req, qa_report = worker_fixture(os.path.join(tmp,"native_qa"))
    results.append(validate_worker(qa_report,qa_req,False)["tests_passed"])
    print("  [OK ] subagent QA: valid binding/coverage fixture")
    import copy
    qa_bad = copy.deepcopy(qa_report);qa_bad["coverage"][0]["status"]="not_run"
    rejected = not validate_worker(qa_bad,qa_req,False)["ok"]
    results.append(rejected)
    print(f"  [{'OK ' if rejected else 'XX '}] subagent QA: passed with not_run rejected")
    from session_qa import prepare
    from audit_subagent_session import validate_request,current_eligibility,CONTEXT_ROLES
    from pathlib import Path
    qa_origin=Path(tmp)/"qa_origin";(qa_origin/"doc").mkdir(parents=True)
    (qa_origin/"rom.sms").write_bytes(b"offline fixture not runnable")
    for role in CONTEXT_ROLES:(qa_origin/role).write_text("old context: "+role)
    request_path=prepare(qa_origin,qa_origin/"rom.sms","producer","worker","runtime",
                         qa_req["cases"],Path(tmp)/"prepared","snapshot test")
    request=json.loads(request_path.read_text())
    (qa_origin/"rom.sms").write_bytes(b"new active build")
    (qa_origin/"doc/10-memory-bank.md").write_text("new context")
    snapshots_ok=not validate_request(request) and not current_eligibility(request,qa_origin/"rom.sms")["eligible"]
    results.append(snapshots_ok);print(f"  [{'OK ' if snapshots_ok else 'XX '}] historical snapshots survive active evolution; current ROM ineligible")
    bad=copy.deepcopy(request);bad["cases"].append(dict(bad["cases"][0],id="second"))
    reject=bool(validate_request(bad));results.append(reject)
    print(f"  [{'OK ' if reject else 'XX '}] independent multi-case reset assumption rejected")
    bad["case_relation"]="chained";ok=not validate_request(bad);results.append(ok)
    print(f"  [{'OK ' if ok else 'XX '}] explicitly chained timeline accepted")
    from session_qa import context_self_check
    results.append(context_self_check())
    print("  [OK ] readable context: production/diagnostic, EIO/EACCES, historical collection refusal")
    from audit_stage_attribution import fixture as stage_fixture,evaluate as evaluate_stage
    stage=stage_fixture();ok=evaluate_stage(stage)["ok"];results.append(ok)
    print(f"  [{'OK ' if ok else 'XX '}] sealed stage attribution accepted within claim ceiling")
    stage["stage_spill_counts"].pop("before_stream");reject=not evaluate_stage(stage)["ok"];results.append(reject)
    print(f"  [{'OK ' if reject else 'XX '}] attribution without pre-stage baseline rejected")
    from audit_import_semantics import fixture as semantic_fixture,evaluate as evaluate_semantics
    semantic=semantic_fixture(Path(tmp)/"semantic");ok=evaluate_semantics(semantic)["ok"];results.append(ok)
    print(f"  [{'OK ' if ok else 'XX '}] source front-distance boundary accepted")
    semantic["source_front_widths"]=[0,0];reject=not evaluate_semantics(semantic)["ok"];results.append(reject)
    print(f"  [{'OK ' if reject else 'XX '}] axis-only distance substitution rejected")
    identity=semantic_fixture(Path(tmp)/"air_identity","air_identity_timing")
    ok=evaluate_semantics(identity,True)["ok"];results.append(ok)
    print(f"  [{'OK ' if ok else 'XX '}] AIR N+1 identity/timing including rollover accepted")
    identity["kind"]="air_timing";reject=not evaluate_semantics(identity,True)["ok"];results.append(reject)
    print(f"  [{'OK ' if reject else 'XX '}] duration-only record cannot prove AIR identity")
    from audit_observed_cases import fixture as observed_fixture, evaluate as evaluate_observed
    observed = observed_fixture(Path(tmp)/"observed_cases")
    ok = evaluate_observed(observed)["ok"]; results.append(ok)
    print(f"  [{'OK ' if ok else 'XX '}] RAM assertions and input ACK deadline rederived from journal")
    observed["cases"][0]["conditions"][1]["value"] = 0
    reject = not evaluate_observed(observed)["ok"]; results.append(reject)
    print(f"  [{'OK ' if reject else 'XX '}] claimed whiff rejected when raw reads show damage")
    from report_output import self_check as report_output_self_check, cli_self_check
    results.append(report_output_self_check() == 0)
    results.append(cli_self_check() == 0)
    from capture_video import image_timeline_motion
    from PIL import Image
    a=Image.new('L',(256,192),0);b=Image.new('L',(256,192),255)
    cycle=image_timeline_motion([a,b,a]);ok=cycle["motion_fraction"]>0 and cycle["endpoint_fraction"]==0
    results.append(ok);print(f"  [{'OK ' if ok else 'XX '}] cyclic video with equal endpoints retains motion")
    freeze=image_timeline_motion([a,a,a]);reject=freeze["motion_fraction"]==0
    results.append(reject);print(f"  [{'OK ' if reject else 'XX '}] unchanged video has no motion proof")
    # §93/L057: offline binding fixtures complement (never replace) the two
    # live-ROM acceptance sessions. ROM mismatch and blank frames fail closed.
    from pathlib import Path
    from session_bridge.isolated import atomic,sha,SUPPORTED_JAR
    from png_io import write_indexed_png
    bundle=Path(tmp)/"isolated_bundle";bundle.mkdir()
    (bundle/"rom.sms").write_bytes(b"diagnostic fixture, not a runnable ROM")
    (bundle/"Emulicious.ini").write_text("Update=0\n")
    (bundle/"effective-config.ini").write_text("Frameskip=0\n")
    (bundle/"bridge.jar").write_bytes(b"fixture bridge")
    (bundle/"ForgeSMS.java").write_text("// fixture source\n")
    write_indexed_png(str(bundle/"frame.png"),256,192,[(0,0,0),(255,255,255)],
                      [bytes([(x+y)&1 for x in range(256)]) for y in range(192)])
    meta={"session_id":"fixture", "rom_sha256":sha(bundle/"rom.sms"),"display":":73",
          "host_display":":0","emulator_process":{"pid":123,"start_ticks":"1"},
          "created_at":1,"emulator_sha256":SUPPORTED_JAR,"bridge_sha256":sha(bundle/"bridge.jar"),
          "bridge_source_sha256":sha(bundle/"ForgeSMS.java")}
    record={**meta,"captured_at":2,"canvas":[256,192],"path":"/private/frame.png", "sha256":sha(bundle/"frame.png"),
            "config_sha256":sha(bundle/"Emulicious.ini"),"effective_config_sha256":sha(bundle/"effective-config.ini")}
    atomic(bundle/"session.json",meta);atomic(bundle/"capture.json",record)
    command=[os.path.join(HERE,"emulator_session.py"),"isolated","check-bundle",str(bundle)]
    results.append(run(command,0,"sessao: bundle com vinculos validos"))
    (bundle/"rom.sms").write_bytes(b"different fixture ROM")
    results.append(run(command,1,"sessao: ROM trocada rejeitada"))
    meta["rom_sha256"]=record["rom_sha256"]=sha(bundle/"rom.sms")
    write_indexed_png(str(bundle/"frame.png"),256,192,[(0,0,0)],[bytes(256)]*192)
    record["sha256"]=sha(bundle/"frame.png")
    atomic(bundle/"session.json",meta);atomic(bundle/"capture.json",record)
    results.append(run(command,1,"sessao: captura preta rejeitada apesar dos hashes validos"))
    fx = gen_fixtures.generate(tmp)
    R = os.path.join(HERE, "audit_validate_resources.py")
    S = os.path.join(HERE, "audit_sprite_line_sim.py")
    L = os.path.join(HERE, "audit_luma_floor.py")

    cases = [
        ([R, fx["valid_bg"]], 0, "bg valido aprovado"),
        ([R, fx["bad_grid"]], 1, "gate reprovou grid fora de 8x8"),
        ([R, fx["bad_color"]], 1, "gate reprovou cor fora dos codigos 6-bit"),
        ([R, fx["opaque_idx0"]], 1, "gate reprovou indice 0 opaco"),
        ([R, "--kind", "sprite", fx["valid_sprite"]], 0, "sprite 16x16 aprovado"),
        ([R, "--kind", "sprite", fx["bad_sprite"]], 1, "gate reprovou sprite 12x12"),
        ([S, fx["scene_ok"]], 0, "cena com 10 sprites dispersos aprovada"),
        ([S, fx["scene_bad_line"]], 1, "gate reprovou 9 sprites numa scanline"),
        ([S, fx["scene_bad_sat"]], 1, "gate reprovou SAT >64"),
        ([S, fx["scene_bad_d0"]], 1, "gate reprovou colisao com terminador 0xD0"),
        ([S, fx["scene_ok_y207"]], 0, "y=207 grava 0xCE: nao colide com o terminador (L129)"),
        ([S, fx["scene_bad_hidden_overflow"]], 1, "gate reprovou 8 sprites hidden + 1 visivel na linha (L129)"),
        ([S, fx["scene_ok_d0_224"]], 0, "Y 0xD0 em 224 linhas aprovado: sem terminador (L128)"),
        ([S, fx["scene_bad_trunc_224"]], 1, "gate reprovou SAT truncada declarada em 224 linhas"),
        ([S, fx["scene_bad_screen_h"]], 1, "gate reprovou screen_h fora de 192/224/240"),
        ([L, "--scene", fx["luma_ok"]], 0, "contraste branco/preto aprovado"),
        ([L, "--scene", fx["luma_bad"]], 1, "gate reprovou cinza sobre branco"),
    ]
    print("== Fase 3: bateria valida/reprova ==")
    for args, exp, label in cases:
        results.append(run(args, exp, label))

    # Contrato MUGEN: planejamento válido e hardware adulterado precisam divergir.
    contract_path = os.path.join(tmp, "engine_contract.json")
    template = json.load(open(os.path.join(HERE, "mugen_engine_contract_v1.json")))
    with open(contract_path, "w") as fh:
        json.dump(template, fh)
    args = [os.path.join(HERE, "audit_mugen_engine_contract.py"),
            "--project", tmp, "--contract", contract_path]
    results.append(run(args, 0, "MUGEN contrato válido planning"))
    results.append(run(args + ["--delivery"], 1, "MUGEN probe não vira delivery"))
    template["target"]["sprites_per_line"] = 20
    with open(contract_path, "w") as fh:
        json.dump(template, fh)
    results.append(run(args, 1, "MUGEN número MD rejeitado no SMS"))

    art_gate = os.path.join(HERE, "audit_art_review_checklist.py")
    art_valid_root = os.path.join(tmp, "art_review_valid")
    art_valid = _art_review_manifest(art_valid_root)
    results.append(run([art_gate, "--manifest", art_valid,
                        "--project-root", art_valid_root, "--verify-hashes"],
                       0, "checklist artístico válido e hash-bound aprovado"))
    art_pixel_root = os.path.join(tmp, "art_review_missing_micro_axes")
    art_pixel = _art_review_manifest(
        art_pixel_root, asset_kind="pixel_sprite_sheet", required_axes=["face_detail"])
    results.append(run([art_gate, "--manifest", art_pixel,
                        "--project-root", art_pixel_root, "--verify-hashes"],
                       1, "gate artístico reprova sprite sheet sem micro-eixos L107"))
    art_unknown_root = os.path.join(tmp, "art_review_unknown_pixel_kind")
    art_unknown = _art_review_manifest(
        art_unknown_root, asset_kind="pixel_sprite_roster_baord")
    results.append(run([art_gate, "--manifest", art_unknown,
                        "--project-root", art_unknown_root, "--verify-hashes"],
                       1, "gate artístico reprova tipo pixel_sprite desconhecido"))

    print("== Fase 4: bootstrap materializa a hierarquia de verdade ==")
    # O contrato do new_project.sh: projeto novo nasce com os niveis 1-7 do
    # AGENTS.md e capaz de buildar. Provado criando um projeto DESCARTAVEL.
    results.append(_check_bootstrap())

    print("== Fase 5: build honesto (ambiente sem toolchain) ==")
    proj = os.environ.get("SMSFORGE_PROBE_PROJECT")
    proj_added = False
    if proj and os.path.isdir(proj):
        r = subprocess.run([PY, os.path.join(HERE, "build_inner.py"), "--project", proj],
                           capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip().splitlines()
        tail = out[-1][:90] if out else ""
        honest = (r.returncode == 2) or (r.returncode == 0)
        print(f"  [{'OK ' if honest else 'XX '}] probe build_inner (exit {r.returncode})  ({tail})")
        results.append(honest)
        proj_added = True
    else:
        print("  [--] probe de projeto ausente (SMSFORGE_PROBE_PROJECT); pulado")
    shutil.rmtree(tmp, ignore_errors=True)

    n_ok = sum(results)
    total = len(results)
    base = total - (1 if proj_added else 0)
    print(f"\nSELFTEST: {n_ok}/{total} verdes ({base} base + "
          f"{'1 probe de build' if proj_added else 'probe opcional nao rodado'})")
    for i, ok in enumerate(results):
        if not ok:
            pass
    if n_ok != total:
        print("[SELFTEST FAIL] ha gate mentindo. Corrigir antes de qualquer uso.")
        return 1
    print("[SELFTEST OK] todos os gates provados: aprovam o valido, reprovam o invalido.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
