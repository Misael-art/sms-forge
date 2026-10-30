"""Preserve six existing poses; copy ImageGen weapon edits only within ROIs."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageDraw

root=Path(__file__).resolve().parent
r=json.loads((root/'assembly_recipe.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=(root/r['base']).resolve();generated=root/r['generated']
assert sha(base)==r['base_sha256'] and sha(generated)==r['generated_sha256']
old=Image.open(base).convert('RGBA');new=Image.open(generated).convert('RGBA')
assert old.size==new.size==tuple(r['raw_size'])
mask=Image.new('1',old.size);draw=ImageDraw.Draw(mask)
for entry in r['polygons']:draw.polygon([tuple(p) for p in entry['points']],fill=1)
before=list(old.getdata());result=[];allowed=list(mask.getdata())
for enabled,previous,pixel in zip(allowed,before,new.getdata()):
    result.append(((pixel[0],pixel[1],pixel[2],255) if pixel[3]>=r['alpha_threshold'] else (0,0,0,0))
                  if enabled else previous)
output=Image.new('RGBA',old.size);output.putdata(result);output.save(root/'raw_registered.png')
assert all(enabled or a==b for enabled,a,b in zip(allowed,before,result))
recipe=json.loads((root/'extraction_recipe.json').read_text())
recipe['source_sha256']=sha(root/'raw_registered.png')
(root/'extraction_recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'outside_weapon_grip_ROIs_RGBA_exact':True,'frame_slots_preserved':6,
 'raw_registered_sha256':sha(root/'raw_registered.png'),
 'body_pose_redrawing_by_code':False,'whole_source_rerender_claimed':False},indent=2))
