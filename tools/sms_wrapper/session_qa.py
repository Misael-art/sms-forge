#!/usr/bin/env python3
"""Prepare native subagent QA requests and collect evidence in an owned session.

This CLI does not spawn agents or make perceptual judgments. Coordinator uses
native spawn_agent, workers inspect collected media/probes and finish reports.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import uuid
import shlex
from audit_subagent_session import SCHEMA, CONTEXT_CONTRACT, CONTEXT_ROLES, ref, validate_request
from session_bridge import isolated as iso

def script_video(session, steps, name):
    """Capture within the input timeline, never after releasing the gesture."""
    root, meta = iso.load(session)
    count = sum(s["frames"] for s in steps)
    if count < 2 or count > 1800: raise ValueError("script video requires 2..1800 frames")
    directory = root/"evidence"/name; directory.mkdir()
    first = iso.request(session,"status")["frame"]; index = 0; trace = []
    try:
        for step in steps:
            iso.request(session,"input",step.get("p1",0),step.get("p2",0),step.get("console",0))
            begin = iso.request(session,"status")["frame"]
            for _ in range(step["frames"]):
                iso.request(session,"step",1)
                record = iso.capture(session,f"{name}_frame_{index:06d}.png")
                shutil.copy2(record["path"],directory/f"{index:06d}.png");index += 1
            trace.append({"begin":begin,"end":record["frame"],"p1":step.get("p1",0),"p2":step.get("p2",0)})
    finally: iso.request(session,"input",0,0,0)
    status = iso.request(session,"status"); target = root/"evidence"/(name+".mp4")
    iso.checked(["ffmpeg","-nostdin","-v","error","-framerate",status["nominal_hz"],
                 "-i",directory/"%06d.png","-c:v","libx264","-crf","0","-pix_fmt","yuv444p",target],timeout=60)
    hashes = [iso.sha(p) for p in sorted(directory.glob('*.png'))]
    if status["frame"]-first != count: raise RuntimeError("script/video VDP frame mismatch")
    record = {"session_id":root.name,"rom_sha256":meta["rom_sha256"],"first_frame":first,
              "last_frame":status["frame"],"frames":count,"frame_sha256":hashes,
              "canvas":[256,192],"path":str(target),"sha256":iso.sha(target),
              "method":"native framebuffer per VDP frame during assigned input script",
              "input_trace":trace,"performance":"not_measured","audio":"not_recorded"}
    from capture_video import timeline_motion
    record["motion_timeline"]=timeline_motion(target)
    iso.atomic(target.with_suffix('.json'),record)
    return record

def prepare(project, rom, producer, worker, lane, cases, out, scope, case_relation="independent", context_mode="production", diagnostic_reason=None):
    project = Path(project).resolve(); rom = Path(rom).resolve()
    if not project.is_dir() or not rom.is_file(): raise ValueError("project and ROM must exist")
    if context_mode not in {"production","diagnostic"}:raise ValueError("unknown context mode")
    if context_mode=="diagnostic" and not diagnostic_reason:raise ValueError("diagnostic mode requires explicit reason")
    documents=[]
    for name in CONTEXT_ROLES:
        path=project/name
        try:
            path.lstat()  # Only actual ENOENT can become a declared diagnostic omission.
        except FileNotFoundError:
            if context_mode=="production":raise ValueError("production context missing:"+name)
            documents.append({"role":name,"status":"missing","reason":diagnostic_reason})
            continue
        content=path.read_bytes().decode("utf-8")  # EIO/EACCES/broken symlink/empty/invalid UTF8 fail closed.
        if not content.strip():raise ValueError("empty project context:"+name)
        documents.append({"role":name,"status":"snapshot"})
    target = Path(out).resolve(); target.mkdir(parents=True, exist_ok=False)
    def snapshot(source, destination, role):
        data = source.read_bytes()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        item = dict(ref(destination),origin=str(source),role=role)
        if ref(source)["sha256"] != item["sha256"]:
            raise ValueError("input changed while snapshotting:"+str(source))
        destination.chmod(0o444)
        return item
    inputs = [snapshot(rom,target/"rom.sms","rom")]
    for doc in documents:
        name=doc["role"]
        if doc["status"]=="snapshot":inputs.append(snapshot(project/name,target/"inputs"/name,name))
    for item in inputs:
        if ref(item["origin"])["sha256"] != item["sha256"]:
            raise ValueError("input epoch changed during preparation:"+item["origin"])
    for doc in documents:
        if doc["status"]=="missing":
            try:(project/doc["role"]).lstat()
            except FileNotFoundError:continue
            raise ValueError("missing context appeared during preparation:"+doc["role"])
    req = {"schema":SCHEMA,"artifact_kind":"session_qa_request","task_id":uuid.uuid4().hex,
           "project":str(project),"producer_id":producer,"worker_id":worker,"lane":lane,
           "scope":scope,"rom":ref(target/"rom.sms"),"inputs":inputs,"cases":cases,
           "input_binding":"frozen_snapshot_v1","input_root":str(target),"case_relation":case_relation}
    req.update(context_contract=CONTEXT_CONTRACT,context_mode=context_mode,
               context_documents=documents,diagnostic_reason=diagnostic_reason)
    errors = validate_request(req)
    if errors: raise ValueError("; ".join(errors))
    iso.atomic(target/"request.json",req)
    wrapper = Path(__file__).resolve().parent
    prompt = f'''Você é o subagente {worker}, faixa {lane}, independente do produtor {producer}.
Leia AGENTS.md da raiz, SMS_GLOBAL central atual §§93–99 e workflows/subagent-emulator-qa.md.
Projeto: {project}
Escopo atribuído: {scope}
Pedido confiável do coordenador: {target/'request.json'}
ROM congelada: {target/'rom.sms'} (SHA {req['rom']['sha256']})
Inputs do contexto: snapshots listados no pedido; origin é proveniência, não input mutável.
Contexto: {context_mode}; ausências diagnósticas constam no pedido. Nunca promover diagnóstico a entrega.
Relação dos casos: {case_relation}. independent tem um caso em sessão nova;
chained é uma única timeline cumulativa e não prova causalidade isolada de cada gesto.

Execute com sua identidade nativa, somente seu output e sua sessão:
rtk proxy python3 {shlex.quote(str(wrapper/'session_qa.py'))} collect --request {shlex.quote(str(target/'request.json'))}

Inspecione PNG no tamanho nativo, quadros do vídeo, áudio e/ou dados internos
conforme os casos. Não transforme sucesso da coleta em aprovação dos casos.
Complete coverage, findings e status em report.json a partir de draft.json.
passed exige todos os testes atribuídos aplicáveis; not_run exige motivo.
ACK não prova ação/colisão; vídeo por stepping não prova FPS; áudio de sinal
não prova música correta. Não aprovar gameplay/AAA com boot ou fixture.
Não altere fontes, assets, memória, ROM, pedido, git nem .agent local. Não use
desktop/foco/teclado do host. Não feche sessões alheias. Não invente agentes.
Se o coletor falhar, registre blocked/failed e diagnóstico; TTL é fallback,
não prova de limpeza. Cada sessão pertence a um único worker.

Valide report.json pelo audit_subagent_session.py com --request original.
Devolva nativamente: Resultado / Bloqueio / Próxima ação, caminhos do pedido,
relatório e artefatos, ROM SHA, ID da sessão, testes executados/não executados,
observações concretas (frame, estado ou amostra), teto assigned_checks_only.
'''
    (target/"worker-prompt.md").write_text(prompt)
    return target/"request.json"

def context_self_check():
    """Offline fault injection; does not touch host sessions or damaged disks."""
    import copy
    import errno
    import tempfile
    from unittest.mock import patch
    from audit_subagent_session import fixture
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);project=root/"project";(project/"doc").mkdir(parents=True)
        rom=project/"rom.sms";rom.write_bytes(b"offline fixture; not runnable")
        cases=fixture(root/"legacy")[0]["cases"]
        for role in CONTEXT_ROLES:(project/role).write_text("readable "+role)
        def make(name,mode="production"):
            return prepare(project,rom,"producer","worker","runtime",cases,root/name,"context fixture",context_mode=mode,diagnostic_reason="explicit offline diagnostic" if mode=="diagnostic" else None)
        def must_fail(call,exc):
            try:call()
            except exc:return
            raise AssertionError("invalid context was accepted")
        request_path=make("good");req=json.loads(request_path.read_text());assert not validate_request(req)
        missing=project/CONTEXT_ROLES[2];missing.unlink()
        must_fail(lambda:make("production_missing"),ValueError)
        assert not (root/"production_missing").exists()
        diag=json.loads(make("diagnostic_missing","diagnostic").read_text());assert not validate_request(diag)
        bad=copy.deepcopy(diag);bad["context_mode"]="production";assert validate_request(bad)
        missing.write_text("restored")
        original_read=Path.read_bytes
        for code in (errno.EIO,errno.EACCES):
            def failing_read(path):
                if path==missing:raise OSError(code,"injected context read fault")
                return original_read(path)
            with patch.object(Path,"read_bytes",failing_read):
                must_fail(lambda:make("fault_"+str(code),"diagnostic"),OSError)
            assert not (root/("fault_"+str(code))).exists()
        for content in (b" \n",b"\xff"):
            missing.write_bytes(content);must_fail(lambda:make("bad_text","diagnostic"),ValueError)
        missing.write_text("restored")
        # Historical snapshots remain auditable even when origin metadata fails.
        original_is_file=Path.is_file
        origins={Path(i["origin"]) for i in req["inputs"]}
        def origin_fault(path):
            if path in origins:raise OSError(errno.EIO,"injected origin metadata fault")
            return original_is_file(path)
        with patch.object(Path,"is_file",origin_fault):assert not validate_request(req)
        historical=copy.deepcopy(req)
        for key in ("context_contract","context_mode","context_documents","diagnostic_reason"):historical.pop(key)
        assert not validate_request(historical)
        hp=root/"historical.json";hp.write_text(json.dumps(historical))
        with patch.object(iso,"start",side_effect=AssertionError("must not open emulator")):
            must_fail(lambda:collect(hp),ValueError)
        bad=copy.deepcopy(req);bad["context_documents"][0]["status"]="unreadable";assert validate_request(bad)
    return True

def collect(request_path):
    request_path = Path(request_path).resolve()
    req = json.loads(request_path.read_text()); errors = validate_request(req)
    if errors: raise ValueError("; ".join(errors))
    if req.get("schema") != SCHEMA:
        raise ValueError("legacy v1 is historical audit only; prepare a new v2 request without rewriting the old request")
    if req.get("context_contract") != CONTEXT_CONTRACT:
        raise ValueError("historical context unverified; prepare new request with readable context before collecting")
    out = request_path.parent/("run_"+uuid.uuid4().hex); out.mkdir()
    artifacts = []
    def artifact(aid, kind, path, metadata=None):
        item = {"id":aid,"kind":kind,**ref(path)}
        if metadata: item["metadata"] = ref(metadata)
        artifacts.append(item)
    session = None; error = None; bundle = None; closed = None
    try:
        session = iso.start(req["rom"]["path"])
        root, meta = iso.load(session)
        for n, case in enumerate(req["cases"]):
            if case.get("applicable", True) is False: continue
            name = f"case_{n}"
            iso.capture(session,name+"_baseline.png")
            src=root/"evidence"/(name+"_baseline.png");dst=out/src.name
            shutil.copy2(src,dst);shutil.copy2(src.with_suffix('.json'),dst.with_suffix('.json'))
            artifact(case["id"]+"_baseline","framebuffer",dst,dst.with_suffix('.json'))
            if case.get("precondition"):
                pre=case["precondition"]
                ack=iso.request(session,"read",int(str(pre["address"]),0),pre["length"])
                path=out/(name+"_precondition.json")
                iso.atomic(path,{"session_id":root.name,"rom_sha256":meta["rom_sha256"],
                                 "origin":"read_only_bridge","samples":[ack],"expected":pre})
                artifact(case["id"]+"_precondition","rom_observation",path,path)
                if bytes(ack["ram"])!=bytes.fromhex(pre["equals_hex"]):
                    raise RuntimeError("ROM initial precondition failed:"+case["id"])
            if case.get("sequence") and case["proof"] != "video": iso.sequence(session,case["sequence"])
            iso.capture(session,name+"_frame.png")
            src = root/"evidence"/(name+"_frame.png"); dst = out/src.name
            shutil.copy2(src,dst);shutil.copy2(src.with_suffix('.json'),dst.with_suffix('.json'))
            artifact(case["id"]+"_frame", "framebuffer",dst,dst.with_suffix('.json'))
            proof = case["proof"]
            if proof == "video":
                rec = script_video(session,case["sequence"],name) if case.get("sequence") else iso.video(session,case.get("video_frames",30),name)
                if not case.get("sequence"):
                    from capture_video import timeline_motion
                    rec["motion_timeline"]=timeline_motion(rec["path"])
                    iso.atomic(Path(rec["path"]).with_suffix('.json'),rec)
                src = Path(rec["path"]);dst = out/src.name
                shutil.copy2(src,dst);shutil.copy2(src.with_suffix('.json'),dst.with_suffix('.json'))
                artifact(case["id"]+"_video","video",dst,dst.with_suffix('.json'))
                # Native reviewer can inspect exact framebuffers without decoding video.
                shutil.copytree(root/"evidence"/name,out/name)
            elif proof == "rom_observation":
                probe = case.get("probe")
                if not probe: raise ValueError("ROM observation requires assigned address/length")
                ack = iso.request(session,"read",int(str(probe["address"]),0),probe["length"])
                path = out/(name+"_probe.json")
                iso.atomic(path,{"session_id":root.name,"rom_sha256":meta["rom_sha256"],
                                 "origin":"read_only_bridge","samples":[ack],"probe":probe})
                artifact(case["id"]+"_probe","rom_observation",path,path)
            elif proof == "audio":
                from capture_audio import capture_session
                code = capture_session(session,case.get("seconds",6),name)
                src = root/(name+".wav");dst = out/src.name
                if not src.is_file(): raise RuntimeError("audio collection unavailable")
                shutil.copy2(src,dst);shutil.copy2(root/(name+".audio.json"),out/(name+".audio.json"))
                artifact(case["id"]+"_audio","audio",dst,out/(name+".audio.json"))
                # Silence is a result for native review, not a collector approval.
            elif proof == "runtime_probe":
                iso.checked([sys.executable,iso.HERE.parent/'measure_runtime_probe.py',"--session",root,
                             "--project",out,"--seconds",case.get("seconds",4),"--janelas","2"])
                path=out/'out/evidence/sessions'/root.name/'runtime/runtime_probe.json'
                artifact(case["id"]+"_runtime","runtime_probe",path,path)
        iso.capture(session,"final.png")
        bundle = iso.publish(session,"final.png",out/"bundles")
        shutil.copy2(root/"commands.jsonl",out/"commands.jsonl")
        artifact("commands","input_trace",out/"commands.jsonl")
    except Exception as e:
        error = str(e)
        # Preserve partial captures/bindings; failure must not erase its evidence.
        if session is not None:
            try:
                root, _ = iso.load(session)
                if (root/"commands.jsonl").is_file():
                    shutil.copy2(root/"commands.jsonl",out/"commands.jsonl")
                    artifact("commands","input_trace",out/"commands.jsonl")
            except Exception: pass
    finally:
        if session is not None:
            try:
                iso.close_session(session)
                closed = out/"closed_session.json";shutil.copy2(session/"session.json",closed)
            except Exception as e: error = (error or "") + "; cleanup failed:" + str(e)
    draft = {"schema":SCHEMA,"artifact_kind":"harness_worker_result",
             **{k:req[k] for k in ["task_id","project","producer_id","worker_id","lane"]},
             "request":ref(request_path),"case_relation":req["case_relation"],"status":"blocked" if error else "needs_review",
             "claim_ceiling":"assigned_checks_only","promoted":False,"findings":[],"artifacts":artifacts,
             "session": {"id":session.name,"owner":req["worker_id"],"bundle":str(bundle) if bundle else None,
                         "metadata":ref(closed),"closed":ref(closed)} if session and closed else None,
             "coverage":[{"id":c["id"],"status":"not_run" if c.get("applicable",True) else "not_applicable",
                          "note":error or ("native worker inspection pending" if c.get("applicable",True) else c["reason"]),"evidence":[]} for c in req["cases"]]}
    iso.atomic(out/"draft.json",draft)
    if error: (out/"collection_error.txt").write_text(error)
    print(json.dumps({"run":str(out),"draft":str(out/"draft.json"),"collected":not error,"error":error}))
    return 1 if error else 0

def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest="op",required=True)
    q = sub.add_parser("prepare")
    for name in ("project","rom","producer","worker","lane","cases","out","scope"):q.add_argument("--"+name,required=True)
    q.add_argument("--case-relation",choices=["independent","chained"],default="independent",
                   help="independent: one applicable case in a fresh session; chained: cumulative timeline")
    q.add_argument("--context-mode",choices=["production","diagnostic"],default="production")
    q.add_argument("--diagnostic-reason",help="explicit fixture/diagnostic scope, required in diagnostic mode")
    q = sub.add_parser("collect");q.add_argument("--request",required=True)
    a = p.parse_args()
    try:
        if a.op == "collect": return collect(a.request)
        print(prepare(a.project,a.rom,a.producer,a.worker,a.lane,json.loads(Path(a.cases).read_text()),a.out,a.scope,a.case_relation,a.context_mode,a.diagnostic_reason));return 0
    except (ValueError,OSError,RuntimeError) as e: print("[FAIL]",e);return 1

if __name__ == "__main__": raise SystemExit(main())
