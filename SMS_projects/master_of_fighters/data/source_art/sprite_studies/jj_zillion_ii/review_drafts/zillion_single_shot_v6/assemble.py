"""Source-only single-point repair from the existing generated transparency."""
from pathlib import Path
import hashlib
import json
from PIL import Image

root=Path(__file__).resolve().parent
previous=root.parent/'zillion_single_shot_v5'
recipe=json.loads((previous/'extraction_recipe.json').read_text())
frame=recipe['frames'][0]
raw=Image.open(previous/'raw_generated.png').convert('RGBA').crop(frame['rect'])
raw.putalpha(raw.getchannel('A').point(lambda n:255 if n>=recipe['alpha_threshold'] else 0))
size=(round(raw.width*7/30),round(raw.height*7/30))
raw=raw.resize(size,Image.Resampling.NEAREST)
x0,y0,_,_=frame['rect'];ox,oy=frame['cell_origin'];px,py=frame['raw_pivot']
left=72+round((x0-ox-px)*7/30);top=132+round((y0-oy-py)*7/30)
position=(105,99);sample=(position[0]-left,position[1]-top)
assert raw.getpixel(sample)[3]==0,'The generated repair must already be transparent'
old=Image.open(previous/'native/I00.png');new=old.copy()
assert new.getpixel(position)==2
new.putpixel(position,0)  # Index0 is the observed transparent generated sample.
new.save(root/'native/I00.png',transparency=0,bits=8)
changed=[i for i,(a,b) in enumerate(zip(old.tobytes(),new.tobytes())) if a!=b]
assert changed==[position[1]*160+position[0]]
sheet=Image.open(previous/'shot_source.png').copy();sheet.paste(new,(0,0))
sheet.save(root/'shot_source.png',transparency=0,bits=8)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'schema':'sms_source_single_sample_repair_v1','parent_source':'jj-zillion-single-shot-source-v05',
 'producer':'root','new_ImageGen_calls':0,'raw_generated':{'path':str((previous/'raw_generated.png').relative_to(root.parents[5])),
 'sha256':sha(previous/'raw_generated.png')},'source_pixel':list(position),'generated_resized_sample':list(sample),
 'generated_sample_alpha':0,'before_index':2,'after_index':0,'changed_source_indices':1,
 'all_other_source_indices_palette_canvas_exact':True,'other5native_poses':'reuse parentv5 exactpaths',
 'sheet':{'path':'shot_source.png','sha256':sha(root/'shot_source.png')},
 'idle':{'path':'native/I00.png','sha256':sha(root/'native/I00.png')},
 'scope':'Only orphan caught by independent sourcecutout. No new body/weapon pixels, pose/timing/effects changes.'}
(root/'source_assembly.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,indent=2))
