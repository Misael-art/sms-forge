"""Background map, round lettering and original two-voice PSG score."""
from collections import Counter
import struct

from PIL import Image
from alis_lettering import lettering
from make_duel_scene02_assets import c_values, planar

# Durations in NTSC frames. The title's dotted descent and pickup answer
# come from the PSG Title, with a new bass line and a shorter cadence.
CALL = ((86,36),(84,36),(82,24),(84,36),(81,60))
ANSWER = ((79,36),(82,36),(79,12),(86,36),(84,24),(82,12),(84,36))
THEMES = {
    'OPEN': (CALL + ANSWER, (58,53,55,57,51,55,58,53), 24),
    'BATTLE': (((74,18),(72,18),(70,12),(72,18),(69,30),
                (67,12),(70,12),(74,12),(77,12),(76,18),(72,18),(74,12),
                (77,18),(75,18),(74,12),(72,18),(70,30),
                (67,12),(69,12),(70,12),(72,12),(74,24),(72,12),(69,12)),
               (58,53,55,57,51,55,58,53),12),
    'WIN': (((74,12),(77,12),(82,24),(81,12),(79,12),(82,48),(0,24)),
            (58,53,55,58,51,53),24),
}

def score(melody,bass,pulse):
    song=bytearray()
    def note(channel,pitch,attenuation):
        if not pitch:
            song.append(0x9f | channel<<5)
            return
        period=round(3579545/(32*440*2**((pitch-69)/12)))
        if not 1<=period<=1023:
            raise ValueError(f'Pitch exceeds NTSC PSG range: {pitch}')
        song.extend((0x80 | channel<<5 | period&15, 0x40 | period>>4,
                     0x90 | channel<<5 | attenuation))
    events={}
    time=0
    for pitch,duration in melody:
        events[time]=(pitch,duration)
        time+=duration
    age=0
    waiting=0
    for tick in range(time):
        before=len(song)
        if tick in events:
            pitch,length=events[tick]
            note(0,pitch,2)
            age=0
        elif pitch and age==4:
            song.append(0x95)
        elif pitch and age==length-2:
            song.append(0x9b)
        if tick%pulse==0:
            slot=tick//pulse
            root=bass[(slot//2)%len(bass)]
            note(1,root+(7 if slot%2 else 0),7 if slot%2 else 5)
        elif tick%pulse==pulse-3:
            song.append(0xbd)
        if before!=len(song) and waiting:
            song[before:before]=bytes([0x37+waiting])
            waiting=0
        waiting+=1
        if waiting==8:
            song.append(0x3f)
            waiting=0
        age+=1
    if waiting: song.append(0x37+waiting)
    song.extend((0x9f,0xbf,0))
    return song


def arena(fighters, art, native, spaceport=False, horizon=False):
    import json
    from stage_alis_postures import rgb
    page=json.loads((fighters/'repertoire-pages.json').read_bytes())
    header=(fighters/'duel_mirror_assets.h').read_text()
    palette=c_values(header,'mof_duel_bg_palette')
    if spaceport:
        # The precomposed swords and the health/ground patterns still use
        # their original CRAM indices. Only repurpose scenery-only colors.
        used = {color for frame in page['frames'] for _, _, color in frame['background_pixels']}
        substitutions = {7: 52, 10: 32, 20: 60}
        if horizon:
            substitutions[8] = 53  # Periwinkle is one CRAM red step above the blue sky.
        if used.intersection(substitutions):
            raise ValueError('Spaceport palette would recolor a weapon')
        palette = [substitutions.get(c, c) for c in palette]
    rows=c_values(header,'mof_duel_bg_rows')
    # Packed weapons contain precomposed backdrop pixels. Leave every reachable
    # row at its canonical pattern; they can be placed at any horizontal phase.
    protected={y//8 for row in page['frames'] for _,y,_ in row['background_pixels']} | {1}
    start=288+4*max(1,page['max_spill'])
    from alis_lettering import stamp_word
    # A 16-tile scratch strip is filled over four VBlanks while hidden.
    # Keep names, meters and animated glass out of the streamed weapon rows.
    dark,white,gold=map(palette.index,(16,63,11))
    source=Image.new('L',(256,192),dark)
    if spaceport:
        sky = palette.index(52)
        source.paste(sky, (0,24,256,96))
        with Image.open(art/('palma_horizonte.png' if horizon else 'pista.png')) as plate:
            original = native(plate, (256,192), palette)
            if horizon:
                # Separate authored bands at areas of clear sky. Leave rows 4–5
                # for clouds; both birds follow the clear band above them.
                # Each authored cloud occupies one tile row, with clean sky on
                # either side. Tiles stay resident as the raster wraps at X=256.
                for bounds, width, position in (
                        ((68,40,812,116),104,(8,40)),
                        ((826,55,1234,124),64,(136,32)),
                        ((1266,57,1466,111),32,(216,40))):
                    source.paste(native(plate.crop(bounds), (width,8), palette),position)
                source.paste(native(plate.crop((0,190,1536,389)), (248,14), palette),(8,48))
                source.paste(native(plate.crop((0,389,1536,634)), (248,34), palette),(8,62))
            else:
                apron = original.crop((0,35,256,119)).resize((248,56), Image.Resampling.NEAREST)
                source.paste(apron, (8,40))
        paving = original.crop((0,132,256,192)).resize((256,48), Image.Resampling.NEAREST)
        source.paste(paving, (0,144))
        source.paste(original.crop((0,120,256,128)), (0,96))
    else:
        with Image.open(art/'camineet_capsulas.png') as plate:
            # Move the eye line into town. The original panorama has tall sky for
            # the title portrait; the fight camera gives those rows to the shops.
            street=plate.crop((0,round(plate.height*.37),plate.width,plate.height))
            source.paste(native(street,(256,80),palette),(0,24))
            # Camineet repeats one cylindrical shop three times in its original
            # map. Align the illustrated middle facade to the tile grid so its
            # curved roof, awning and glass can share all of their patterns.
            left,right=round(street.width*.378),round(street.width*.527)
            storefront=native(street.crop((left,0,right,street.height)),(40,80),palette)
            for shop_x in (56,96,136):
                source.paste(storefront,(shop_x,24))
            # One broad course of the painted walkway fills the foreground.
            # Keep mortar in stone tones to leave the highest contrast to Alis.
            paving=plate.crop((0,round(plate.height*.88),plate.width,round(plate.height*.952)))
            court=native(paving,(256,48),palette)
            shade=[palette.index(42) if sum(rgb(code))>370 else palette.index(21)
                   for code in palette]
            court=court.point(shade+[0]*(256-len(shade)))
            source.paste(court,(0,144))
    lettering(source,'ALIS',16,0,white)
    lettering(source,'ECO',218,0,gold)
    # Preserve the gate by picking its cyan glass tile, strictly within the
    # authored round disk. Its two exposures use the same shutter silhouette.
    glass=palette.index(56)
    def tile_at(x,y):
        return bytes(source.crop((8*x,8*y,8*x+8,8*y+8)).getdata())
    def light_cell(xs, ys, glass_colors):
        candidates = [(x,y) for y in ys for x in xs]
        x,y = max(candidates, key=lambda p: sum(tile_at(*p).count(c) for c in glass_colors))
        steady = tile_at(x,y)
        bright = bytes(white if v in glass_colors else v for v in steady)
        if steady == bright:
            raise ValueError('Missing animated glass in the stage art')
        return x,y,planar(steady)+planar(bright)
    glass_colors = {glass, palette.index(60)} if spaceport else {glass}
    if spaceport:
        lights = [light_cell(range(24,27), range(6,8) if horizon else range(5,7), glass_colors),
                  light_cell(range(13,15), range(9,11) if horizon else range(10,12), glass_colors)]
    else:
        lights = [light_cell(range(28,31), range(9,12), glass_colors)]
    motion = bytearray()
    if spaceport:
        from preview_alis_spaceport import terns
        wings = terns()
        motion.extend(planar([sky]*64))
        for offset, pose in enumerate((0,1,2,1)):
            bird, alpha = wings[pose]
            bird = bird.point([palette.index(v) if v in palette else dark for v in range(256)])
            cell = Image.new('L',(16,8),sky)
            size = (9,8)
            cell.paste(bird.resize(size,Image.Resampling.NEAREST),(offset*2,0),
                       alpha.resize(size,Image.Resampling.NEAREST))
            for x in (0,8):
                motion.extend(planar(list(cell.crop((x,0,x+8,8)).getdata())))
    capacity=448-start-16-12-2*len(lights)-len(motion)//32
    slot_size=32
    largest=max(f['count'] for f in page['frames'])
    if largest!=page['max_count'] or not 0<largest<=slot_size:
        raise ValueError('Sprite packet size differs from the allocated slot')
    spare=slot_size-largest
    vram_ids=list(range(start,start+capacity))
    for slot in range(8):
        vram_ids.extend(range(slot*slot_size+largest,(slot+1)*slot_size))
    if capacity<24: raise ValueError('Missing scenery tile budget')
    visible={(x,y):tile_at(x,y) for y in range(24) if y not in protected for x in range(32)}
    counts=Counter(visible.values())
    colors=[rgb(c) for c in palette]
    errors=[[sum((a-b)**2 for a,b in zip(left,right)) for right in colors] for left in colors]
    def distance(a,b):
        return sum(errors[p][q] for p,q in zip(a,b))
    # Match repeats first, then choose the worst represented weighted motif.
    pool=list(dict.fromkeys([bytes([dark]*64),*(tile_at(x,0) for x in (*range(2,5),*range(27,31)))]))
    if spaceport:
        # One-pixel expansion joints are the near-plane motion cue. Their
        # low area would otherwise lose to the parked ships in tile fitting.
        near = (tile_at(x,y) for y in range(18,24) for x in range(32))
        officer = (tile_at(x,y) for y in range(8 if horizon else 9,12) for x in range(12,15))
        pool = list(dict.fromkeys([*pool, *near, *officer]))
        if horizon:
            clouds = (tile_at(x,y) for y in (4,5) for x in range(32))
            tower_cap = (tile_at(x,6) for x in range(24,27))
            landing_gear = (tile_at(x,y) for x in (4,8,24,30) for y in (10,11))
            hangars = (tile_at(x,y) for x in (17,18,21,22) for y in (9,10))
            pool = list(dict.fromkeys([*pool, *clouds, *tower_cap, *landing_gear,
                                       *hangars, tile_at(10,9), tile_at(31,9)]))
        if len(pool)>len(vram_ids):
            raise ValueError('Runway and checkpoint exceed the scenery allocation')
    if horizon:
        from palma_panorama import fit_apron
        # Three sets of 32-byte spell composites must fit a 16 KiB bank.
        # Reserve the HUD rows and both beacons before spending orientation IDs.
        view_limit = 16384//(3*32) - len(protected) - len(lights)
        pool,entries = fit_apron(counts,pool,vram_ids,colors,sky,palette.index(53),view_limit)
    else:
        best={t:min(distance(t,k) for k in pool) for t in counts}
        while len(pool)<len(vram_ids):
            t=max(best,key=lambda k:best[k]*counts[k]**0.5)
            if not best[t]: break
            pool.append(t)
            for k in best: best[k]=min(best[k],distance(k,t))
        index={t:min(range(len(pool)),key=lambda i:distance(t,pool[i])) for t in counts}
        entries = {raw:vram_ids[i] for raw,i in index.items()}
    mapping=[entries[visible[x,y]] if (x,y) in visible else 256+rows[y]
             for y in range(24) for x in range(32)]
    patterns=bytearray(b''.join(planar(list(p)) for p in pool[:capacity]))
    light_tiles = []
    for x,y,pair in lights:
        tile = start+len(patterns)//32
        light_tiles.append(tile)
        patterns.extend(pair)
        mapping[y*32+x] = tile
    motion_tile = start+len(patterns)//32
    patterns.extend(motion)
    sx,sy,_ = lights[0]
    light = light_tiles[0]
    digit=start+len(patterns)//32
    for label in '0123456789-*':
        strip=Image.new('L',(8,8),dark)
        if label=='*': strip.paste(gold,(1,3,7,6))
        elif label!='-': lettering(strip,label,1,0,white)
        patterns.extend(planar(list(strip.getdata())))
    banner=start+len(patterns)//32
    blob=bytearray(patterns)+struct.pack('<768H',*mapping)
    extras=pool[capacity:]
    extra_address=0x8000+len(blob)
    blob.extend(b''.join(planar(list(tile)) for tile in extras))
    defs={'ARENA_SPARE_ADDR':extra_address,'ARENA_SPARE_FIRST':largest,
          'ARENA_SPARE_WIDTH':spare,'ARENA_SPARE_COUNT':len(extras),'ARENA_FIRST':start,'ARENA_BYTES':len(patterns),'BANNER_TILE':banner,'DIGIT_TILE':digit,
          'SIGN_X':sx,'SIGN_Y':sy,'SIGN_TILE':light,'BANNER_DATA':0x8000+len(blob)}
    if spaceport:
        defs.update(PORT_SKY=motion_tile, PORT_SCANNER=light_tiles[1],
                    PORT_SCAN_X=lights[1][0], PORT_SCAN_Y=lights[1][1],
                    PORT_PALETTE=0x8000+len(blob))
        if horizon:
            defs['PORT_CLOUDS'] = 1
        blob.extend(palette)
        defs['BANNER_DATA']=0x8000+len(blob)
    # The stage name table is restored from its ROM copy under each announcement.
    for word,height,face,slant in [('ROUND 1',11,white,1),('ROUND 2',11,white,1),
            ('ROUND 3',11,white,1),('FIGHT!',15,gold,6),('K.O.',16,white,0),
            ('TEMPO',12,gold,2),('EMPATE',11,gold,2)]:
        strip=Image.new('L',(64,16),dark)
        stamp_word(strip,word,32,(16-height)//2,height,(white,face,palette.index(2) if 2 in palette else 2),slant)
        for y in (0,8):
            for x in range(0,64,8):
                blob.extend(planar(list(strip.crop((x,y,x+8,y+8)).getdata())))
    for name,theme in THEMES.items():
        defs['SONG_'+name]=0x8000+len(blob)
        blob.extend(score(*theme))
    if len(blob)>16384 or banner+16>448: raise ValueError('Chapter exceeds video or mapper budget')
    return bytes(blob),defs
