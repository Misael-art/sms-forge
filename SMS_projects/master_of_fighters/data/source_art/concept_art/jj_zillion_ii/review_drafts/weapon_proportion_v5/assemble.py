"""Bounded copy of generated gun/grip pixels; preserve approved body indices."""
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
assert old.size==new.size==tuple(r['size'])
mask=Image.new('1',old.size);draw=ImageDraw.Draw(mask)
for entry in r['polygons']:draw.polygon([tuple(p) for p in entry['points']],fill=1)
mask_values=list(mask.getdata());before=list(old.getdata());result=[]
for enabled,previous,pixel in zip(mask_values,before,new.getdata()):
    result.append(((pixel[0],pixel[1],pixel[2],255) if pixel[3]>=r['alpha_threshold'] else (0,0,0,0))
                  if enabled else previous)
out=Image.new('RGBA',old.size);out.putdata(result);out.save(root/'concept_source.png')
assert all(enabled or a==b for enabled,a,b in zip(mask_values,before,result))
print(json.dumps({'outside_ROI_RGBA_exact':True,
 'changed_RGBA_pixels':sum(a!=b for a,b in zip(before,result)),
 'sha256':sha(root/'concept_source.png'),'medium':'truecolor concept only, not SMS resource',
 'no_FX': 'requires independent semantic review'},indent=2))
