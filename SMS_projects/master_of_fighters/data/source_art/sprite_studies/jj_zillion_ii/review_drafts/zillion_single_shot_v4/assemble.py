"""Copy existing authored bodies and compose one generated emission element.

No character, weapon or effect pixels are synthesized. The effect alone is
nearest-resampled to its declared short-emission size. All inputs are hashed.
"""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parent
recipe = json.loads((ROOT / 'assembly_recipe.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for record in recipe['inputs']:
    path = (ROOT / record['path']).resolve()
    if sha(path) != record['sha256']:
        raise ValueError(f'Input changed: {path}')
destination = ROOT / 'native'
destination.mkdir(exist_ok=False)
for target, original in recipe['body_inputs'].items():
    path = (ROOT / original).resolve()
    if target != 'A02':
        shutil.copy2(path, destination / f'{target}.png')
        continue
    body = Image.open(path).copy()
    effect = recipe['emission']
    pulse = Image.open(ROOT / effect['source']).crop(effect['rect_px'])
    pulse = pulse.resize(tuple(effect['size_px']), Image.Resampling.NEAREST)
    x,y = effect['position_px']
    region = (x,y,x+pulse.width,y+pulse.height)
    if body.crop(region).getbbox() is not None:
        raise ValueError('Emission would overwrite body/weapon pixels')
    before = body.tobytes()
    body.paste(pulse,(x,y))
    for old,new in zip(before,body.tobytes()):
        if old and old != new:
            raise AssertionError('Authored body pixel changed')
    body.save(destination / 'A02.png', transparency=0, bits=8)

poses = [Image.open(destination/f'{name}.png') for name in recipe['frame_ids']]
sheet = Image.new('P',(320,320))
sheet.putpalette(poses[0].getpalette())
for i,image in enumerate(poses):
    sheet.paste(image,((i%2)*160,(i//2)*160))
sheet.save(ROOT/'shot_source.png',transparency=0,bits=8)
print(json.dumps({'sheet_sha256':sha(ROOT/'shot_source.png'),
    'body_drawings_including_guard':4,'action_body_drawings':3,
    'ImageGen_calls_this_revision':0,'body_weapon_pixels_changed':0,
    'effect_scope':'one generated glyph nearest-resampled and copied into empty emission ROI'},indent=2))
