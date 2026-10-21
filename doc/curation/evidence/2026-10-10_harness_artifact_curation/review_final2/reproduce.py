#!/usr/bin/env python3
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import copy, json, os, tempfile
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base if "--live" not in sys.argv else Path.cwd()/"tools/sms_wrapper"))
import artifact_registry as a, harness_orchestration as h
results=[]
with tempfile.TemporaryDirectory(prefix="reproduce-",dir=base) as temporary:
 root=Path(temporary)
 def case(name, mutate):
  project=root/name/"game";project.mkdir(parents=True)
  d=a.fixture(project);mutate(project,d)
  results.append({"case":name,"audit":a.audit(project,d,False)})
 def alias(project,d):
  (project/"alias").symlink_to(project/"data/source_art",target_is_directory=True)
  d["locations"]["alias"]={"path":"alias","purpose":"same destination","mode":"managed"}
 case("location_alias",alias)
 def escape(project,d):
  foreign=project/"elsewhere";foreign.mkdir();f=foreign/"image.png";f.write_bytes(b"outside kind destination")
  (project/"data/source_art/foreign").symlink_to(foreign,target_is_directory=True)
  d["artifacts"][0]["files"][0].update(path="data/source_art/foreign/image.png",sha256=a.digest(f))
 case("file_destination_escape",escape)
 def hardlink(project,d):
  src=project/d["artifacts"][0]["files"][0]["path"];dst=project/"data/source_art/weapon.png";os.link(src,dst)
  d["kinds"]["weapon"]={**d["kinds"]["concept"],"purpose":"weapon review"}
  r=copy.deepcopy(d["artifacts"][0]);r.update(id="weapon-v01",asset_id="weapon",kind="weapon");r["files"][0]["path"]="data/source_art/weapon.png"
  d["artifacts"].append(r);d["heads"].append({"asset_id":"weapon","kind":"weapon","variant":"main","candidate":r["id"],"approved":None})
 case("hardlink_ownership",hardlink)
 for tasks in ({},False,0,""):
  try:result=h.plan({"tasks":tasks})
  except Exception as e:result={"exception":type(e).__name__,"message":str(e)}
  results.append({"case":"malformed_tasks_"+repr(tasks),"result":result})
 for tid in (0,False,[],{}):
  try:result=h.plan({"tasks":[{"id":tid,"kind":"inventory"}]})
  except Exception as e:result={"exception":type(e).__name__,"message":str(e)}
  results.append({"case":"malformed_ID_"+repr(tid),"result":result})
print(json.dumps(results,indent=2,ensure_ascii=False))
