import sys, json, hashlib, copy, subprocess
from pathlib import Path
ROOT=Path('/tmp/smsforge-harness-forward-20261010')
WS=Path('/mnt/sdcard/Projects/SMSForge')
sys.path.insert(0,str(WS/'tools/sms_wrapper'))
import artifact_registry as ar
import harness_orchestration as harness
P=ROOT/'fixture_game'
P.mkdir(exist_ok=True)
def put(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n' if isinstance(data,(dict,list)) else data)
    return ar.digest(path)
def save(label,data):
    put(ROOT/(label+'.json'),data)
    return data
def cli(label,args):
    p=subprocess.run([sys.executable,*map(str,args)],cwd=WS,text=True,capture_output=True)
    data={'argv':list(map(str,args)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
    save(label,data)
    return data
location='data/source_art/fighter_ash'
d={'schema':ar.SCHEMA,'project_id':P.name,
   'fixture_only':True,
   'locations':{'source':{'path':location,'mode':'managed','purpose':'All authored fighter sources, requests, hypotheses, and technical derivatives; fixture only'}},
   'kinds':{},'artifacts':[],'heads':[]}
def kind(k,purpose):
    d['kinds'][k]={'purpose':purpose,'introduced_for':'Independent forward-test fixture scenario',
        'procedure':'Fixture textual artifact; preserve exact sources, reference roles, hypothesis and hash; no visual or runtime claims',
        'location':'source','required_file_roles':['document','metadata','lineage']}
for k,purpose in [('model_sheet','Identity and equipment approved by fixture owner'),
                   ('animation_source','Complete 61-pose source approved only for production conversion'),
                   ('conversion_proof','Two-pose route proof, not final animation source'),
                   ('converted_candidate','Converted visual reviewed separately')]:kind(k,purpose)
def row(aid,k,status,parents,variant='main',revision=1,reserve=False,reason='Fixture scenario baseline'):
    a={'id':aid,'asset_id':'fighter_ash','kind':k,'variant':variant,'revision':revision,'status':status,'parents':parents,'reason':reason,'files':[]}
    sub=f'{location}/{k}/{variant}/v{revision:02d}'
    for role,filename in [('document','document.fixture.txt'),('metadata','metadata.json'),('lineage','lineage.json')]:
        ref={'role':role,'path':f'{sub}/{filename}'}
        if not reserve:
            data={'fixture_only':True,'id':aid,'role':role,'parents':parents,'pose_ids':list(range(1,62)) if k=='animation_source' else ([1,19] if k=='conversion_proof' else []),
                'scope': 'source_only_conversion' if k=='animation_source' else k,'no_final_art':True}
            ref['sha256']=put(P/ref['path'],data if filename.endswith('json') else json.dumps(data)+'\n')
        a['files'].append(ref)
    if status in ('approved','rejected'):
        dp=f'doc/decisions/{aid}.json'
        a['approval_scope']='source_only_conversion' if k=='animation_source' else k
        decision={'schema':'sms_artifact_decision_v1','artifact_id':aid,'scope':k,'decision':status,
                  'actor_role':'owner','actor':'SYNTHETIC fixture owner; not the real user',
                  'source_note':'Synthetic fixture decision required to exercise structural gate; no real artwork approved',
                  'files':a['files']}
        a['decision']={'path':dp,'sha256':put(P/dp,decision)}
    d['artifacts'].append(a)
    d['heads'].append({'asset_id':'fighter_ash','kind':k,'variant':variant,'candidate':aid if status in ('approved','candidate','reserved') else None,'approved':aid if status=='approved' else None})
    return a
concept=row('ash.model.main.r1','model_sheet','approved',[])
source=row('ash.animation.main.r1','animation_source','approved',[concept['id']])
proof=row('ash.proof.main.r1','conversion_proof','candidate',[concept['id']])
rejected=row('ash.converted.main.r1','converted_candidate','rejected',[source['id'],proof['id']])
reg=P/'doc/artifact_registry.json'
put(reg,d)
put(P/'doc/10-memory-bank.md','FIXTURE ONLY\nCurrent identity: ash.model.main.r1 approved.\nAnimation61 source: ash.animation.main.r1 approved ONLY for conversion.\nTwo-pose proof: ash.proof.main.r1 technical route candidate, not full source.\nConverted candidate: ash.converted.main.r1 rejected. No converted approved head.\n')
initial=cli('session1.locate.animation',[WS/'tools/sms_wrapper/artifact_registry.py','locate','--project',P,'--asset','fighter_ash','--kind','animation_source'])
assert initial['exit']==0
# Extend the existing namespace and location, not a second character root.
kind('equipment_detail','Owner-requested close-up of weapon grip; identity unchanged')
kind('shadow_comparison','Owner-requested comparison of two shadow hypotheses over exactly poses 7,19,42')
grip=row('ash.grip.weapon.r1','equipment_detail','reserved',[concept['id']],variant='weapon_grip',reserve=True,reason='New request: inspect hand-to-grip attachment; no identity redesign')
shadow=row('ash.shadow.pose07_19_42.r1','shadow_comparison','reserved',[source['id'],rejected['id']],variant='ramp_a_vs_b_pose07_19_42',reserve=True,reason='New request: spatial shadow progression comparison, not 61-pose regeneration')
put(reg,d)
request={'fixture_only':True,'asset':'fighter_ash','registry':'doc/artifact_registry.json','delta':['weapon_grip','shadow_poses_07_19_42'],
         'read_only_inputs':{'identity':concept['id'],'animation':source['id'],'negative_reference_only':rejected['id']},
         'forbidden_source_substitution':proof['id'],'hypotheses':{'A':'preserve approved source ramp placement','B':'adjust shadow continuity only'},
         'next_gate':'Independent visual review then owner; no production integration or ROM claim'}
put(P/'doc/new-request.fixture.json',request)
ref={'project':str(P),'path':str(reg),'sha256':ar.digest(reg)}
def task(rid):
    a=next(a for a in d['artifacts'] if a['id']==rid)
    return {'id':rid,'kind':'visual_production','artifact_ids':[rid],
            'write_paths':[str(P/f['path']) for f in a['files']],
            'context_file':str(P/'doc/new-request.fixture.json')}
taskset={'artifact_registry':ref,'tasks':[task(grip['id']),task(shadow['id']),{'id':'review_sources','kind':'source_audit','write_paths':[]},
           {'id':'update_memory','kind':'canonical_memory_update','write_paths':[str(P/'doc/10-memory-bank.md')]}]}
save('session1.taskset',taskset)
valid=cli('session1.plan',[WS/'tools/sms_wrapper/harness_orchestration.py','plan','--taskset',ROOT/'session1.taskset.json'])
assert valid['exit']==0
scan=cli('session1.scan.reserved',[WS/'tools/sms_wrapper/artifact_registry.py','check','--project',P,'--scan'])
assert scan['exit']==0
save('session1.registry.snapshot',d)
put(P/'doc/10-memory-bank.md',f'FIXTURE ONLY — SESSION 1 checkpoint\nRegistry doc/artifact_registry.json SHA {ar.digest(reg)}\nIdentity={concept["id"]}; source61={source["id"]} approved source-only.\nProof2={proof["id"]} technical only; converted={rejected["id"]} rejected; no converted approved head.\nReserved grip={grip["id"]}; shadow={shadow["id"]}.\nResume by locate+check; do not regenerate intact approved inputs. Pending: fill reserved fixture outputs, seal, review.\n')
# SESSION 2 reload everything from disk, without relying on Session 1 variables.
d=json.loads(reg.read_text())
checkpoint=(P/'doc/10-memory-bank.md').read_text()
assert 'source-only' in checkpoint
for role in ('model_sheet','animation_source','equipment_detail','shadow_comparison'):
    variant={'equipment_detail':'weapon_grip','shadow_comparison':'ramp_a_vs_b_pose07_19_42'}.get(role,'main')
    assert cli('session2.locate.'+role,[WS/'tools/sms_wrapper/artifact_registry.py','locate','--project',P,'--asset','fighter_ash','--kind',role,'--variant',variant])['exit']==0
assert cli('session2.preflight.reloaded',[WS/'tools/sms_wrapper/harness_orchestration.py','plan','--taskset',ROOT/'session1.taskset.json'])['exit']==0
before={r['id']:[f['sha256'] for f in r['files']] for r in d['artifacts'] if r['status']!='reserved'}
# Simulated producer only writes the exact reserved fixture files. Coordinator seals.
for a in d['artifacts']:
    if a['status']!='reserved':continue
    for f in a['files']:
        f['sha256']=put(P/f['path'],{'fixture_only':True,'id':a['id'],'role':f['role'],'parents':a['parents'],
            'generation_tool':'none; synthetic forward-test text','source_roles':request['read_only_inputs'],
            'pose_ids':[7,19,42] if a['kind']=='shadow_comparison' else [],'status':'pending_real_visual_review',
            'hypotheses':request['hypotheses'] if a['kind']=='shadow_comparison' else {'identity':'unchanged'},
            'claim_ceiling':'organization_and_reference_consistency_only'})
    a['status']='candidate'
put(reg,d)
assert cli('session2.scan.sealed',[WS/'tools/sms_wrapper/artifact_registry.py','check','--project',P,'--scan'])['exit']==0
assert before=={r['id']:[ar.digest(P/f['path']) for f in r['files']] for r in d['artifacts'] if r['id'] in before}
save('session2.registry.snapshot',d)
put(P/'doc/10-memory-bank.md','FIXTURE ONLY — SESSION 2 checkpoint\nRegistry doc/artifact_registry.json SHA '+ar.digest(reg)+'\nApproved source/identity unchanged. New grip/shadow artifacts are candidates only.\nNo new approval, conversion, image generation or ROM validation.\nNext: real image creation with reserved next revision if needed, visual review+owner decision.\n')
# Negatives: reject known invalid user/worker plans and registry states.
negative=[]
def check_bad(name,t):
    out=harness.plan(t)
    save('negative.'+name,out)
    negative.append({'case':name,'rejected':not out['ok'],'details':out['rejected'] or out['artifact_registry_problem']})
    assert not out['ok'],name
check_bad('old_session_preflight',json.loads((ROOT/'session1.taskset.json').read_text()))
res=json.loads((ROOT/'session1.registry.snapshot.json').read_text())
# Restore reserved snapshot for static preflight tests: use separate sandbox project clone to preserve sealed originals.
import shutil
Q=ROOT/'negative_fixture_game'
shutil.copytree(P,Q,dirs_exist_ok=True)
res['project_id']=Q.name
for a in res['artifacts']:
    if a['status']=='reserved':
        for f in a['files']:(Q/f['path']).unlink()
qreg=Q/'doc/artifact_registry.json'
put(qreg,res)
qref={'project':str(Q),'path':str(qreg),'sha256':ar.digest(qreg)}
qt={'id':'grip','kind':'visual_production','artifact_ids':[grip['id']],
    'write_paths':[str(Q/f['path']) for f in grip['files']]}
check_bad('missing_registry',{'tasks':[qt]})
check_bad('broad_directory',{'artifact_registry':qref,'tasks':[{**qt,'write_paths':[str(Q/location)]}]})
check_bad('overwrite_approved_input',{'artifact_registry':qref,'tasks':[{**qt,'write_paths':[str(Q/concept['files'][0]['path'])]}]})
check_bad('sealed_parent_as_output',{'artifact_registry':qref,'tasks':[{**qt,'artifact_ids':[source['id']]}]})
check_bad('unreserved_extra_file',{'artifact_registry':qref,'tasks':[{**qt,'write_paths':qt['write_paths']+[str(Q/location/'extra.png')]}]})
def bad_registry(name,x):
    out=ar.audit(Q,x,scan=True);save('negative.'+name,out);negative.append({'case':name,'rejected':not out['ok'],'details':out['problems']});assert not out['ok'],name
x=copy.deepcopy(res);x['heads'][2]['approved']=proof['id'];bad_registry('technical_candidate_promoted_without_owner',x)
x=copy.deepcopy(res);x['artifacts'][-1]['files'][0]['path']=x['artifacts'][-2]['files'][0]['path'];bad_registry('two_artifact_owners_one_output',x)
x=copy.deepcopy(res);x['artifacts'][0]['files'][0]['sha256']='0'*64;bad_registry('stale_approved_hash',x)
result={'artifact_kind':'harness_worker_result','status':'passed','claim_ceiling':'ready_for_aaa','promoted':True}
errs=harness.validate_result(result);save('negative.worker_promotion',{'problems':errs});assert len(errs)==2
negative.append({'case':'worker_promotion','rejected':True,'details':errs})
put(Q/location/'orphan.fixture.txt','unregistered fixture output')
bad_registry('unregistered_managed_output',res)
(Q/location/'orphan.fixture.txt').unlink()
# Explicit scope limit: structural gate does not determine semantic source choice.
x=copy.deepcopy(res)
x['artifacts'][-1]['parents']=[proof['id']]
semantic=ar.audit(Q,x,scan=True)
save('limit.wrong_semantic_parent',semantic)
assert semantic['ok'] # workflow review must catch 2-pose proof used for 61-pose conversion.
plan_no_context=harness.plan({'artifact_registry':qref,'tasks':[qt]})
save('limit.plan_no_visual_context',plan_no_context)
# Full artifact hashes and source tool versions used in this independent test.
files=[{'path':str(p),'sha256':ar.digest(p),'bytes':p.stat().st_size} for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='result.json']
sources=[WS/'tools/sms_wrapper'/p for p in ['artifact_registry.py','harness_orchestration.py','.agent/skills/sms-harness-orchestration.md','.agent/workflows/artifact-organization.md','.agent/workflows/original-artwork.md','.agent/workflows/artwork-to-rom-lifecycle.md']]
summary={'status':'passed_organization_forward_test_with_declared_limits','fixture_only':True,'project':str(P),
  'two_sessions':True,'final_audit':ar.audit(P,d,scan=True),'negative_cases':negative,
  'semantic_parent_limit':'Gate accepts sealed proof parent structurally; coordinator must enforce source61 role, not infer from PASS',
  'plan_context_limit':'Registry preflight checks destinations; does not validate artistic source context or GDD approval',
  'approvals':'Only synthetic fixture decisions. New requested artifacts remain candidates. No real owner approval fabricated.',
  'no_art_generation_no_emulation_no_saas':True,'source_hashes':{str(p):ar.digest(p) for p in sources},'artifacts':files}
save('result',summary)
print(json.dumps({'status':summary['status'],'negative_cases':len(negative),'files':len(files),'final_audit':summary['final_audit'],'result':str(ROOT/'result.json')},indent=2))
