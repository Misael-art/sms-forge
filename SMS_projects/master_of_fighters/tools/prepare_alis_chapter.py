"""Prepare the stage and both costumes from the preserved B08 layer plan."""
import argparse
import json
from pathlib import Path

from PIL import Image

from make_duel_scene02_assets import PROJECT, array, blocks, c_values, digest, pixels, planar
from plan_scene02_repertoire import extend_actions
from revise_scene02_alis import raster, revise
from stage_alis_mirror import NEUTRAL_COLORS, POSTURE_SHEET, SECOND_COSTUME, SOURCE, build, import_cel, read_cell
from stage_alis_postures import rgb, stage as stage_postures
from stage_scene02_walk import stage as stage_walk, stage_specials

ART = PROJECT / 'data/source_art/scenes/alis_palma'
BASE_SHA = '297a9b7c9c5002f2019cbd6b2fb77ce0a9886a20856c8645dfd7cfb645d33613'


def stage_backdrop(plan, path):
    header = (PROJECT / 'data/source_art/scenes/cena01_duel_read/cena01_bg.h').read_text('ascii')
    palette = c_values(header, 'cena01_bg_palette')
    table = c_values(header, 'cena01_map')
    rows = [0, 0]
    for row in range(2, 24):
        strip = table[row*32:(row+1)*32]
        if len(set(strip)) != 1:
            raise ValueError('Scene 02 needs a row-uniform base for ground overlays')
        rows.append(strip[0] - 256)
    used = set(rows) | {5}
    patterns = [planar([plan['background_palette'].index(palette[i]) for i in pixels(pattern)])
                if index in used else bytes(32)
                for index, pattern in enumerate(blocks(c_values(header, 'cena01_tiles')))]
    path.write_text(array('mof_duel_bg_stage', b''.join(patterns)) + '\n' +
                    array('mof_duel_bg_rows', rows), encoding='ascii')


def stage_acting(sprite):
    palette = [c for c in sprite if c not in NEUTRAL_COLORS] + list(SECOND_COSTUME.values())
    # Pelvis in each authored cell relative to the cropped left edge.
    hips = (100, 100, 97, 86, 59, 86, 115, 145, 110)
    result = {}
    with Image.open(ART / 'acting.png') as sheet:
        for i, hip in enumerate(hips):
            cell = read_cell(sheet, 3, 3, i)
            box = cell.getchannel('A').point(lambda a: 255 if a >= 200 else 0).getbbox()
            if not box:
                raise ValueError(f'Empty acting cel {i}')
            cel = cell.crop(box)
            # All nine use the same scale, including the bowed victory.
            cel.putalpha(cel.getchannel('A').point(lambda a: 255 if a >= 200 else 0))
            family = ('listen', 'bow', 'palma')[i // 3]
            result[f'{family}_{1+i%3}'] = import_cel(cel, 5.9, 144, palette,
                12 - round(hip / 5.9), 0, concept_materials=True)
    with Image.open(ART / 'guard.png') as sheet:
        # The rear boot of the counter-cut crosses the nominal second grid line.
        for row, edges in enumerate(((0,384,768,1152,1536), (0,376,737,1142,1536))):
            for i in range(4):
                cell = sheet.crop((edges[i], row*512, edges[i+1], (row+1)*512))
                alpha = cell.getchannel('A').point(lambda a: 255 if a >= 200 else 0)
                box = alpha.getbbox()
                if not box or box[0]==0 or box[2]==cell.width:
                    raise ValueError('Guard or weapon touches crop boundary')
                cell.putalpha(alpha)
                hip = ((199,573,957,1330),(192,549,898,1327))[row][i]
                key = ('breathe','riposte')[row]
                result[f'{key}_{i+1}'] = import_cel(cell,8.45,144,palette,
                    12-round((hip-edges[i]-box[0])/8.45),0,concept_materials=True)
    return result


def pack_fighters(control, backdrop, output, spaceport=False, model_palette=False):
    plan=json.loads(control.read_bytes())
    from pack_alis_scenes import native
    # The spill packet contains backdrop pixels around each sword. Sample a
    # narrow repeating course of the authored sidewalk for these five rows
    # and pass that same picture through the sprite and background converters.
    header=backdrop.read_text('ascii')
    patterns=bytearray(c_values(header,'mof_duel_bg_stage'))
    rows=c_values(header,'mof_duel_bg_rows')
    palette=plan['background_palette']
    if spaceport:
        from pack_alis_scenes import PORT_ART
        with Image.open(PORT_ART/'pista.png') as plate:
            slab = plate.crop((plate.width//2,plate.height*119//192,
                               plate.width*5//8,plate.height*151//192))
            strip = slab.resize((1,40),Image.Resampling.BOX).resize((8,40),Image.Resampling.NEAREST)
            samples = native(strip, (8,40), palette)
        dim = list(range(len(palette)))
    else:
        with Image.open(ART/'camineet_capsulas.png') as plate:
            slab=plate.crop((round(plate.width*.086),round(plate.height*.901),
                             round(plate.width*.143),plate.height))
            strip=slab.resize((1,40),Image.Resampling.BOX).resize((8,40),Image.Resampling.NEAREST)
            samples=native(strip,(8,40),palette)
        dim=[palette.index(21) if sum(rgb(c))>=340 else palette.index(16) for c in palette]
    for i,tile in enumerate((2,3,4,6,7)):
        pixels8=[dim[v] for v in samples.crop((0,i*8,8,i*8+8)).getdata()]
        patterns[tile*32:(tile+1)*32]=planar(pixels8)
        rows[13+i]=tile
    output.parent.mkdir(parents=True,exist_ok=True)
    street=output.parent/('spaceport-runway.h' if spaceport else 'camineet-street.h')
    street.write_text(array('mof_duel_bg_stage',patterns)+'\n'+array('mof_duel_bg_rows',rows),encoding='ascii')
    build(control, SOURCE, output, extra_drawings=stage_acting(plan['sprite_palette']),
          stage_header=street, review_sheet=SOURCE.parent / "alis_revisao_ficha", model_palette=model_palette)


def prepare(base, out, spaceport=False, model_palette=False):
    if digest(base) != BASE_SHA:
        raise ValueError('Expected the preserved B08 scene02-repertoire-layer-plan-b03.json')
    plan = json.loads(base.read_bytes())
    colors = [rgb(code) for code in plan['sprite_palette']]
    heights = {}
    for frame in plan['frames']:
        if frame['direction'] == 'right' and frame['pose'] == 'idle':
            ys = [y for x, y in raster(frame, plan['sprite_palette'])]
            heights[frame['actor']] = max(ys) - min(ys) + 1
    out.mkdir(parents=True, exist_ok=False)
    stage_backdrop(plan, out / 'backdrop.h')
    stage_walk(out / 'walk', True, colors=colors, heights=heights)
    stage_specials(out / 'special', colors=colors, heights=heights)
    receipts = [out / 'walk/walk-staging.json', out / 'special/special-staging.json']
    if not extend_actions(base, receipts, out / 'actions.json'):
        raise ValueError('The authored action plan failed composition')
    revise(out / 'actions.json', out / 'revised.json')
    stage_postures(POSTURE_SHEET, out / 'revised.json', out / 'postures')
    pack_fighters(out / 'postures/postures-plan.json', out / 'backdrop.h', out / 'fighters', spaceport, model_palette)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('out', type=Path)
    parser.add_argument('--resume-postures',action='store_true',
                        help='Reuse the preserved pre-mirror pose plan and backdrop in BASE')
    parser.add_argument('--spaceport', action='store_true', help='Composite ground weapon pixels on the Palma runway')
    parser.add_argument('--model-palette',action='store_true',help='Use the Alis v4 cloth and armor swatches')
    args = parser.parse_args()
    base,out=args.base.resolve(),args.out.resolve()
    if args.resume_postures:
        control=base/'postures/postures-plan.json'
        backdrop=base/'backdrop.h'
        if (digest(control)!='f729663f7f9725263a757a25d1d363bdb51612a600818c5eda4c242d2382fe73'
                or digest(backdrop)!='3a408688d7765adc1fd82f1f43098a3e8fa14ad7b64de6ff060b66dd1c6c4723'):
            raise ValueError('The recovered chapter staging does not match the preserved B inputs')
        pack_fighters(control,backdrop,out/'fighters',args.spaceport,args.model_palette)
    else:
        prepare(base,out,args.spaceport,args.model_palette)
