"""Pack three selectable Palma stages into the existing 64-bank SMS cartridge."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from alis_arena import arena
from make_duel_scene02_assets import PROJECT, array, planar
from pack_alis_magic import decode_stage, glyph_stamps
from pack_alis_matchup import PAGE, score, versus_page
from pack_alis_scenes import PORT_ART, native

ARENA_BANKS = (47, 36, 48)


def definitions(path):
    return {k:int(v) for k,v in re.findall(r'#define MOF_(\w+) (\d+)u',path.read_text())}


def stamp_rows(glyph, half):
    # flight(): ordinary Fire and Slash start at Y111; the twin arc is Y97..123.
    # Myau stays at Y137 with the nut, rises to Y81, and dives to at most Y133.
    # glyph() centers 8/16px artwork and crops to rows 3..19. Actor-bound
    # effects keep that whole window for any jump, hit or grounded pose.
    if glyph == 0:
        return 11,14
    if glyph == 1:
        return 13,13
    if glyph == 3:
        return 16+half,16+half
    if glyph in (4,5):
        return 9+half,16+half
    return 3,19


def spell_art(stage, limits, fighters):
    entries, mapping, patterns, palette = decode_stage(stage,limits,fighters)
    stamps = list(glyph_stamps(palette))
    spans = [stamp_rows(g,y) for g,_,y,_,_ in stamps]
    first_stamps = {}
    for idx,(glyph,mirrored,_,_,_) in enumerate(stamps):
        first_stamps.setdefault((glyph,mirrored),idx)
    cuts = sorted({3,20,*(lo for lo,_ in spans),*(hi+1 for _,hi in spans)})
    # A row band has its own dictionary. Within each legal stamp window
    # the indices are contiguous, so the duel keeps its one lookup per cell.
    cells = [0]*768
    dictionary = []
    for lo,hi in zip(cuts,cuts[1:]):
        band = mapping[lo*32:hi*32]
        first = len(dictionary)
        group = list(dict.fromkeys(band))
        index = {entry:first+i for i,entry in enumerate(group)}
        cells[lo*32:hi*32] = [index[t] for t in band]
        dictionary.extend(group)
    if len(dictionary)>256:
        raise ValueError('Spell background index exceeds one byte')
    strips = []
    for (_,_,_,alpha,ink),(lo,hi) in zip(stamps,spans):
        used = cells[lo*32:(hi+1)*32]
        start,stop = min(used),max(used)+1
        pieces = [planar([c if a>=100 else b for c,a,b in zip(ink,alpha,patterns[t])])
                  for t in dictionary[start:stop]]
        strips.append((start,b''.join(pieces)))
    return cells,[entries[t] for t in dictionary],strips,list(first_stamps.values())


def assign(banks, ends, blocks):
    """Best-fit immutable streams into measured page tails or empty banks."""
    address = {}
    for block in sorted(set(blocks),key=lambda b:(-len(b),b)):
        fits=[i for i,end in ends.items() if end+len(block)<=PAGE]
        if not fits:
            raise ValueError(f'No contiguous mapper space for {len(block)} bytes; free={ends}')
        bank=max(fits,key=ends.get)
        off=ends[bank]
        assert banks[bank][off:off+len(block)]==b'\xff'*len(block)
        banks[bank][off:off+len(block)]=block
        ends[bank]+=len(block)
        address[block]=(bank,0x8000+off)
    return address


def words(name,values):
    return 'static const uint16_t '+name+'[] = {'+','.join(map(str,values))+'};'


def pack(base,cast,archives,out):
    out.mkdir(parents=True,exist_ok=True)
    chapter=json.loads((base/'chapter.json').read_text())
    tc=chapter['toolchain']
    pan=PROJECT/tc['include_dirs'][1]
    cast_tc=json.loads((cast/'chapter.json').read_text())['toolchain']
    fighters,_,magic,_=[PROJECT/v for v in cast_tc['include_dirs']]
    if cast_tc['defines']['MOF_GUARDIANS_PAGE']!=tc['defines']['MOF_GUARDIANS_PAGE']:
        raise ValueError('Guardian banks differ between chapter and roster')
    tc['include_dirs'][0]=cast_tc['include_dirs'][0]
    original=(pan/'panels.bin').read_bytes()
    limits=definitions(pan/'alis_pages.h')
    assert limits['ARENA_BANK']==36 and tc['defines']['MOF_GUARDIANS_PAGE']==39
    banks={i:bytearray(b'\xff'*PAGE) for i in (*range(24,37),*range(39,63))}
    ends={}
    for i in range(24,37):
        banks[i][:]=original[(i-24)*PAGE:(i-23)*PAGE]
        if i!=36:
            ends[i]=18+struct.unpack_from('<H',banks[i])[0]+1536
    guardians=(magic/'magic.bin').read_bytes()
    for i in range(39,47):
        banks[i][:]=guardians[(i-39)*PAGE:(i-38)*PAGE]
    fm,loop,_=score(archives,'FM')
    psg,_,_=score(archives,'PSG')
    banks[52][:len(fm)+len(psg)]=fm+psg
    ends[52]=len(fm)+len(psg)
    ends.update({i:0 for i in range(53,63)})
    versions=[]
    glyph_index=None
    for index,bank in enumerate(ARENA_BANKS):
        folder=out/f'v{index+1}'
        folder.mkdir(exist_ok=True)
        if index==1:
            data=bytes(banks[36]); cfg=limits
        else:
            data,cfg=arena(fighters,PORT_ART,native,True,index==2,index==2)
            banks[bank][:len(data)]=data
            ends[bank]=len(data)
        for name in ('ARENA_FIRST','ARENA_BYTES','ARENA_SPARE_ADDR','ARENA_SPARE_FIRST',
                     'ARENA_SPARE_WIDTH','ARENA_SPARE_COUNT','PORT_PALETTE','BANNER_DATA',
                     'SIGN_TILE','PORT_SCANNER','PORT_SKY','DIGIT_TILE','BANNER_TILE'):
            if cfg[name]!=limits[name]:raise ValueError(f'V{index+1} layout mismatch: {name}')
        (folder/'panels.bin').write_bytes(data.ljust(PAGE,b'\xff'))
        (folder/'alis_pages.h').write_text(''.join(f'#define MOF_{k} {v}u\n' for k,v in cfg.items()))
        page,pan_strip,_=versus_page(folder,horizon=index!=0,version=index+1)
        banks[49+index][:]=page
        cells,restore,spells,offsets=spell_art(data,cfg,fighters)
        if glyph_index is not None and offsets!=glyph_index:
            raise ValueError('Spell topology differs across stage variants')
        glyph_index=offsets
        versions.append((cells,restore,spells,bytes(pan_strip),cfg))
    blocks=[strip for _,_,spells,pan_strip,_ in versions for strip in [pan_strip,*(s for _,s in spells)]]
    locations=assign(banks,ends,blocks)
    header=[line for line in (magic/'magic_art.h').read_text().splitlines() if line.startswith('#define MOF_MIRROR_')]
    header.append(array('magic_glyph',glyph_index))
    camera=[]
    for i,(cells,restore,spells,strip,cfg) in enumerate(versions):
        where=[locations[s] for _,s in spells]
        header.extend([array(f'cells_{i}',cells),words(f'restore_{i}',restore),
                       array(f'banks_{i}',[b for b,_ in where]),
                       words(f'base_{i}',[addr-offset*32 for (offset,_),(_,addr) in zip(spells,where)])])
        camera.append(locations[strip])
    for name,ctype,tbl in [('magic_map','uint8_t','cells'),('magic_restore','uint16_t','restore'),
                           ('magic_base','uint16_t','base'),('magic_bank','uint8_t','banks')]:
        header+= [f'static const {ctype} *{name};',
                  f'static const {ctype} *const {name}_versions[] = {{'+','.join(f'{tbl}_{i}' for i in range(3))+'};']
    (out/'magic_art.h').write_text('\n'.join(header)+'\n')
    (out/'magic_cine.h').write_bytes((magic/'magic_cine.h').read_bytes())
    (out/'matchup_pan.h').write_text(array('mof_strip_banks',[b for b,_ in camera])+'\n'+
                                     words('mof_strip_addresses',[a for _,a in camera])+'\n')
    meta={k:[v[-1][k] for v in versions] for k in ('SIGN_X','SIGN_Y','PORT_SCAN_X','PORT_SCAN_Y')}
    constants={'MOF_VERSUS_PAGE':49,'MOF_PAN_BANK':63,'MOF_PAN_STEPS':20,'MOF_BATTLE_BANK':52,
               'MOF_BATTLE_LOOP':0x8000+loop,'MOF_BATTLE_PSG':0x8000+len(fm)}
    (out/'matchup.h').write_text(''.join(f'#define {k} {v}u\n' for k,v in constants.items())+
        '#define STAGE_CLASSIC_BANK '+str(ARENA_BANKS[0])+'u\n'+
        '#define STAGE_ARENA_BANKS {'+','.join(map(str,ARENA_BANKS))+'}\n'+
        ''.join('#define STAGE_'+k+' {'+','.join(map(str,vals))+'}\n' for k,vals in meta.items()))
    rel=out.relative_to(PROJECT).as_posix()
    tc['include_dirs']=tc['include_dirs'][:2]+[rel]
    tc['mapper_code_banks']['SMSBANK_CAMERA']=63
    tc['defines']['MOF_PALMA_VERSIONS']=1
    tc['makesms_extra']=cast_tc['makesms_extra'][:3]
    for start,stop in ((24,37),(39,63)):
        name=f'palma-{start}.bin'
        (out/name).write_bytes(b''.join(banks[i] for i in range(start,stop)))
        tc['makesms_extra']+=['-mbank',f'{rel}/{name}:0:{stop-start}:{start}']
    (out/'chapter.json').write_text(json.dumps(chapter,indent=2)+'\n')
    receipt={'arena_banks':ARENA_BANKS,'cards':[49,50,51],'camera':camera,'stamp_streams':len(locations)-3,
             'remaining_tail_bytes':sum(PAGE-v for v in ends.values()),
             'stage_sha256':[hashlib.sha256((out/f'v{i}/panels.bin').read_bytes()).hexdigest() for i in (1,2,3)]}
    (out/'versions.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('base','cast','archives','out'):parser.add_argument(arg,type=Path)
    args=parser.parse_args()
    pack(args.base.resolve(),args.cast.resolve(),args.archives.resolve(),args.out.resolve())
