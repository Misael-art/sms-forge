#!/usr/bin/env python3
"""Six independent regression families; all fixture writes confined to /tmp."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse, copy, hashlib, json, os, tempfile
ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path.cwd()));ap.add_argument('--output');args=ap.parse_args()
repo=Path(args.root).resolve();sys.path.insert(0,str(repo/'tools/sms_wrapper'))
import artifact_registry as a,harness_orchestration as h,audit_learning_capture as l
results=[]
def record(case,good,actual):
 results.append({'case':case,'pass':bool(good),'actual':actual})
with tempfile.TemporaryDirectory(prefix='six-regression-',dir=Path(__file__).parent) as temporary:
 root=Path(temporary)
 def fixture(name):
  p=root/name/'game';p.mkdir(parents=True);return p,a.fixture(p)
 p,d=fixture('baseline');v=a.audit(p,d,False);record('positive_baseline',v['ok'],v)
 p,d=fixture('R1');(p/'alias').symlink_to(p/'data/source_art',target_is_directory=True);d['locations']['alias']={'path':'alias','purpose':'alias','mode':'managed'};v=a.audit(p,d);record('R1_location_alias_rejected',not v['ok'],v)
 p,d=fixture('R2');foreign=p/'elsewhere';foreign.mkdir();f=foreign/'image.png';f.write_bytes(b'out of kind destination');(p/'data/source_art/foreign').symlink_to(foreign,target_is_directory=True);d['artifacts'][0]['files'][0].update(path='data/source_art/foreign/image.png',sha256=a.digest(f));v=a.audit(p,d);record('R2_file_destination_escape_rejected',not v['ok'],v)
 p,d=fixture('R3');src=p/d['artifacts'][0]['files'][0]['path'];dst=p/'data/source_art/weapon.png';os.link(src,dst);d['kinds']['weapon']={**d['kinds']['concept'],'purpose':'weapon review'};r=copy.deepcopy(d['artifacts'][0]);r.update(id='weapon-v01',asset_id='weapon',kind='weapon');r['files'][0]['path']='data/source_art/weapon.png';d['artifacts'].append(r);d['heads'].append({'asset_id':'weapon','kind':'weapon','variant':'main','candidate':r['id'],'approved':None});v=a.audit(p,d);record('R3_hardlink_ownership_rejected',not v['ok'],v)
 for tasks in ({},False,0,''):
  try:v=h.plan({'tasks':tasks});good=not v.get('ok')
  except h.ContractError as e:v=str(e);good=True
  record('R4_tasks_'+repr(tasks),good,v)
 for tid in (0,False,[],{}):
  try:v=h.plan({'tasks':[{'id':tid,'kind':'inventory'}]});good=not v.get('ok')
  except h.ContractError as e:v=str(e);good=True
  record('R4_ID_'+repr(tid),good,v)
 p,d=fixture('R5');d['kinds']['animation_source']=d['kinds'].pop('concept');row=d['artifacts'][0];row.update(kind='animation_source',status='approved');d['heads'][0].update(kind='animation_source',approved=row['id']);src=p/row['files'][0]['path'];decision=src.parent/'lineage.json';original={'schema':'sms_animation_source_lineage_v1','character_id':'hero','status':'owner_approved_art_source_for_production_conversion','approval_scope':'visual source atlas; conversion still requires review','source':{'file':'source.png','sha256':row['files'][0]['sha256']}};row['approval_scope']=original['approval_scope']
 for name,changes,expected in [('valid',{},True),('wrong_character',{'character_id':'terry'},False),('wrong_scope',{'approval_scope':'concept only; no sprite approval'},False),('pending',{'status':'candidate_pending_owner_review'},False),('wrong_sha',{'source':{'file':'source.png','sha256':'0'*64}},False)]:
  value=copy.deepcopy(original);value.update(changes);decision.write_text(json.dumps(value));row['decision']={'path':str(decision.relative_to(p)),'sha256':a.digest(decision)};v=a.audit(p,d);record('R5_adapter_'+name,v['ok']==expected,v)
 p=root/'R6';(p/'doc/agent_learning').mkdir(parents=True);(p/'tools/sms_wrapper/.agent/skills').mkdir(parents=True);(p/'tools/sms_wrapper/.agent/rules').mkdir();rule=p/'tools/sms_wrapper/.agent/rules/SMS_GLOBAL.md';rule.write_text('LAW ONLY');skill=p/'tools/sms_wrapper/.agent/skills/fake.md';skill.symlink_to(rule);routes={'schema':'sms_lesson_routes_v1','routes':[{'lesson_id':'L001','sources':['doc/curation/a.json'],'application_entrypoints':[{'path':str(skill.relative_to(p)),'sha256':hashlib.sha256(rule.read_bytes()).hexdigest(),'selection_basis':'law only via alias'}]}]};(p/'doc/agent_learning/lesson_routes.json').write_text(json.dumps(routes));v=l.audit_routes(p,{'L001':('a.json',{})});record('R6_skill_alias_to_rule_rejected',bool(v),v)
 qa=h.plan({'tasks':[{'id':'qa','kind':'test_execution','write_paths':[str(root/'out/qa/session-owned')]}]});record('positive_QA_directory_contract_without_duplicate_art_tree',qa['ok'],qa)
 asset=h.plan({'tasks':[{'id':'asset','kind':'test_execution','write_paths':[str(root/'data/source_art/new.png')]}]});record('asset_destination_protected_even_QA_kind',not asset['ok'],asset)
actual_project=repo/'SMS_projects/master_of_fighters';lineage=actual_project/'data/source_art/sprite_studies/dr_social/dr_social_basic_sequences_61f_owner_source_v1.json';decl=json.loads(lineage.read_text());image=lineage.parent/decl['source']['file'];row={'id':'dr-social-basic61-owner-source-v1','asset_id':'dr_social','kind':'animation_source','variant':'basic61','revision':1,'status':'approved','parents':[],'reason':'preserve original source-only approval','approval_scope':decl['approval_scope'],'files':[{'role':'source_animation','path':str(image.relative_to(actual_project)),'sha256':a.digest(image)}],'decision':{'path':str(lineage.relative_to(actual_project)),'sha256':a.digest(lineage)}};data={'schema':a.SCHEMA,'project_id':actual_project.name,'locations':{'source':{'path':'data/source_art','purpose':'existing sources','mode':'legacy'}},'kinds':{'animation_source':{'purpose':'source atlas','introduced_for':'adoption','procedure':'artwork-to-rom-lifecycle.md','location':'source','required_file_roles':['source_animation']}},'artifacts':[row],'heads':[{'asset_id':'dr_social','kind':'animation_source','variant':'basic61','candidate':row['id'],'approved':row['id']}]};v=a.audit(actual_project,data);record('positive_actual_dr_social_61_pose_source',v['ok'],v)
report={'schema':'sms_independent_focused_regression_v1','review_status':'pass_focused_scope_only' if all(x['pass'] for x in results) else 'needs_revision','tool_sha256':{n:hashlib.sha256((repo/'tools/sms_wrapper'/n).read_bytes()).hexdigest() for n in ['artifact_registry.py','harness_orchestration.py','audit_learning_capture.py','audit_source_raster.py']},'results':results,'actual_source_record':{'path':str(lineage),'sha256':a.digest(lineage),'image_sha256':a.digest(image)},'limits':['No emulator/full suite executed.','Approval checks declared identity/hash/scope consistency, not actor authenticity or semantics of arbitrary prose.','Actual source control is an in-memory read-only registry, not production approval.']}
if args.output:Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if all(x['pass'] for x in results) else 1)
