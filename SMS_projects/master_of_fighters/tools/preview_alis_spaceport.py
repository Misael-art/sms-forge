"""Compose the Palma spaceport art study using the C5r cartridge poses as scale guides."""
import hashlib
import json
import math
from bisect import bisect_left
from pathlib import Path

from PIL import Image, ImageDraw

from make_duel_scene02_assets import PROJECT, c_values, pixels
from stage_alis_postures import rgb

ART = PROJECT / 'data/source_art/scenes/alis_espacoporto'
OUT = PROJECT / 'out/diagnostics/alis_espacoporto_proposta'
FIGHTERS = PROJECT / 'out/diagnostics/alis_camineet_c5/fighters'
CARTRIDGE = PROJECT / 'out/candidates/alis_capitulo_01_c5r/rom/master_of_fighters.sms'
C5R = '2112971df3eb08339e93a2892a43fc38fd144b2df7c4a6134ec13640e20af9ea'
COLORS = (52, 32, 0, 63, 42, 37, 3, 1, 2, 58, 60, 16, 11, 21, 56, 15)
WIDTH, HEIGHT, RAIL, FLOOR = 288, 192, 102, 120
FRAMES, FRAME_MS = 128, 80
NEAREST = Image.Resampling.NEAREST
MASTER = bytes(v for code in range(64) for v in rgb(code)).ljust(768, b'\0')


def native(image, colors):
    """Map pixels to the chosen 6-bit SMS colors, keeping the hardware color as index."""
    table = [
        min(colors, key=lambda code: sum((a - b) ** 2 for a, b in zip(rgb(raw), rgb(code))))
        for raw in range(64)
    ]
    result = Image.new('L', image.size)
    indices = []
    for color in image.convert('RGB').get_flattened_data():
        raw = sum(min(3, (value + 42) // 85) << (2 * i) for i, value in enumerate(color))
        indices.append(table[raw])
    result.putdata(indices)
    return result


def plates():
    with Image.open(ART/'pista.png') as source:
        art = native(source.resize((WIDTH,HEIGHT),NEAREST),COLORS)
    # Key the open blue sky/hills outside the distant domed terminal.
    # Flooding from the sky preserves enclosed blue details on both shuttles.
    edge = Image.new('L',(WIDTH,RAIL))
    for y in range(RAIL):
        for x in range(WIDTH):
            terminal = 133 <= x <= 195 and y >= 83
            if not terminal and art.getpixel((x,y)) not in (32,52):
                edge.putpixel((x,y),255)
    ImageDraw.floodfill(edge,(0,0),90)
    mask = edge.point(lambda c: 0 if c==90 else 255)
    apron = Image.new('L',(WIDTH,FLOOR))
    apron.paste(mask,(0,0))
    apron.paste(255,(0,RAIL,WIDTH,FLOOR))
    far = art.crop((0,0,WIDTH,RAIL))
    # Extend only the hidden part of the painted sky/ridge, sampling the
    # nearest original horizon pixels. The terminal keeps its own silhouette.
    for y in range(RAIL):
        visible = [x for x in range(WIDTH) if not mask.getpixel((x,y))
                   and art.getpixel((x,y)) in (32,52)]
        for x in range(WIDTH):
            if not mask.getpixel((x,y)):
                continue
            i = bisect_left(visible,x)
            donor = min(visible[max(0,i-1):i+1],key=lambda other:abs(x-other))
            far.putpixel((x,y),art.getpixel((donor,y)))
    return art,far,apron


def terns():
    frames = []
    with Image.open(ART/'aves.png') as sheet:
        for i in range(3):
            cell = sheet.crop((sheet.width*i//3,0,sheet.width*(i+1)//3,sheet.height))
            # Register to the body, keeping the three wing angles around
            # the same axis. All poses use the same scale and transparent box.
            body_x = (385,365,364)[i]
            cell = cell.crop((body_x-270,145,body_x+270,605)).resize((15,13),NEAREST)
            alpha = cell.getchannel('A').point(lambda v:255 if v>=160 else 0)
            frames.append((native(cell,(16,37,63)),alpha))
    return frames


def actors():
    rom = CARTRIDGE.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=C5R:
        raise ValueError('The scale reference must be the Camineet C5r cartridge')
    plan = json.loads((FIGHTERS/'repertoire-pages.json').read_text())
    header = (FIGHTERS/'duel_mirror_assets.h').read_text()
    palette = c_values(header,'mof_duel_sprite_palette')
    result = {}
    for row in plan['frames']:
        if row['right']!=(row['player']==0) or row['name'] not in ('idle','breathe_1','breathe_2','breathe_3','breathe_4'):
            continue
        base = row['bank']*0x4000+row['address']-0x8000
        count = rom[base]
        if count!=len(row['sprite_cells']) or row['background_pixels']:
            raise ValueError('Unsupported scale pose')
        art = Image.new('L',(64,72))
        alpha = Image.new('L',art.size)
        for i,(left,top,expected) in enumerate(row['sprite_cells']):
            xy = rom[base+17+2*i:base+19+2*i]
            offset = base+17+2*count+32*i
            packet = rom[offset:offset+32]
            if xy!=bytes((left&255,top)) or packet.hex()!=expected:
                raise ValueError('Cartridge and sprite plan differ')
            for j,color in enumerate(pixels(packet)):
                if color:
                    at = (left+32+j%8,top-80+j//8)
                    art.putpixel(at,palette[color])
                    alpha.putpixel(at,255)
        result[row['player'],row['name']] = art,alpha
    return result


def colored(indexed):
    image = Image.frombytes('P',indexed.size,indexed.tobytes())
    image.putpalette(MASTER)
    return image


def camera_view(plane, offset):
    # Keep the full silhouettes of both ships in the center view. At the
    # travel limits, repeat only the outermost column of sky or runway.
    width, height = plane.size
    view = plane.crop((offset, 0, offset + WIDTH, height))
    if offset < 0:
        left_edge = plane.crop((0, 0, 1, height)).resize((-offset, height), NEAREST)
        view.paste(left_edge, (0, 0))
    if offset + WIDTH > width:
        right = offset + WIDTH - width
        right_edge = plane.crop((width - 1, 0, width, height)).resize((right, height), NEAREST)
        view.paste(right_edge, (WIDTH - right, 0))
    return view.resize((256, height), NEAREST)


def compose():
    OUT.mkdir(parents=True,exist_ok=True)
    art,far,mask = plates()
    birds,cast = terns(),actors()
    wing_cycle=(0,1,2,1)
    still_names=('idle','breathe_1','breathe_2','breathe_3','breathe_4','breathe_3','breathe_2','breathe_1')
    floor=art.crop((0,FLOOR,WIDTH,HEIGHT))
    apron=art.crop((0,0,WIDTH,FLOOR))
    exposures = []
    for tick in range(FRAMES):
        # A round trip from left to right. One pixel step on the ground
        # needs twice as much camera motion to appear on the apron.
        camera = round(16*(1-math.cos(2*math.pi*tick/FRAMES)))
        distant, middle = camera//4-4, camera//2-8
        frame = Image.new('L',(256,HEIGHT))
        frame.paste(camera_view(far,distant),(0,0))
        for lag,altitude in ((0,31),(22,24)):
            bx = -22+((tick*3+lag*16)%384)-distant
            by = altitude+round(2*math.sin((tick+lag)*math.pi/32))
            bird,alpha = birds[wing_cycle[((tick+lag)//3)%4]]
            frame.paste(bird,(bx,by),alpha)
        stage = apron.copy()
        # Pulse only the original glass pixels. The metal housing is steady.
        for rect,lit in (((217,40,235,47),tick%32 in (1,2,5,6)),
                         ((116,95,125,101),tick%48 in (20,21,22,23))):
            if lit:
                x,y,r,b=rect
                patch=art.crop(rect).point(lambda c:63 if c in (56,60) else c)
                stage.paste(patch,(x,y))
        frame.paste(camera_view(stage,middle),(0,0),camera_view(mask,middle))
        frame.paste(camera_view(floor,camera-16),(0,FLOOR))
        if tick==32:
            colored(frame).save(OUT/'pista_256x192.png')
        for player,pivot in enumerate((148,209)):
            pose = still_names[((tick//4)+player*3)%len(still_names)]
            cel,alpha = cast[player,pose]
            frame.paste(cel,((pivot-camera+16)*256//WIDTH-32,88),alpha)
        output=colored(frame)
        if tick==32:
            output.save(OUT/'duelo_256x192.png')
        exposures.append(output.resize((512,384),NEAREST))
    exposures[0].save(OUT/'pista_em_movimento.gif',save_all=True,append_images=exposures[1:],
                      duration=FRAME_MS,loop=0,optimize=False,disposal=1)
    with Image.open(OUT/'pista_em_movimento.gif') as gif:
        # GIF coalesces identical adjacent exposures. Expand each stored
        # duration back to the authored clock before comparing pixels.
        t=0
        for i in range(gif.n_frames):
            gif.seek(i)
            dwell=gif.info['duration']
            if dwell<=0 or dwell%FRAME_MS:
                raise ValueError(f'Invalid dwell time in GIF frame {i}')
            actual=gif.convert('RGB').tobytes()
            for _ in range(dwell//FRAME_MS):
                if t>=FRAMES or actual!=exposures[t].convert('RGB').tobytes():
                    raise ValueError(f'GIF differs from authored exposure {t}')
                t+=1
        if t!=FRAMES or gif.info['loop']!=0:
            raise ValueError('Unexpected preview timing')


if __name__=='__main__':
    compose()
