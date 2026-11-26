"""Translate authored Alis chapter panels and lettering into SMS background banks."""
import argparse
import json
import struct
from pathlib import Path

from PIL import Image, ImageDraw
from alis_lettering import lettering, stamp_word
from alis_arena import arena
from make_duel_scene02_assets import PROJECT, digest, planar
from stage_alis_postures import rgb

ART = PROJECT / 'data/source_art/scenes/alis_palma'
PORT_ART = PROJECT / 'data/source_art/scenes/alis_espacoporto'
# Shared native CRAM. Position 0 is opaque on the background.
PALETTE = [16, 0, 1, 2, 6, 11, 15, 47, 63, 22, 27, 35, 21, 37, 42, 56]
WHITE, GOLD, PEACH, CYAN = 8, 6, 10, 15
DIALOGUE = [
    ('CAMINEET / PALMA', 'MYAU', 2, ('ALIS... NA CASA DE NEKISE.', 'AQUELA LUZ SE MEXEU.')),
    ('A CASA DE NEKISE', 'ALIS', 0, ('ESTOU AQUI, MYAU.', 'DÊ A PATA. VAMOS JUNTOS.')),
    ('DO OUTRO LADO', 'MYAU', 2, ('MAS... SE VOCÊ ESTÁ AQUI,', 'QUEM ESTÁ COM SEU ESCUDO?')),
    ('DO OUTRO LADO', 'ALIS', 1, ('FIQUE PERTO DE MIM.', 'VOU ABRIR CAMINHO.')),
    ('DEPOIS DO ECO', 'ALIS', 0, ('VOCÊ TAMBÉM TEVE MEDO?', 'ENTÃO VENHA COM A GENTE.')),
    ('DEPOIS DO ECO', 'MYAU', 2, ('OUVIU ISSO, ALIS?', 'AS LOJAS VÃO ABRIR.')),
]
PORT_DIALOGUE = [
    ('ESPAÇOPORTO DE PALMA', 'MYAU', 2, ('ALIS! O GUARDA QUER VER', 'SEU PASSAPORTE.')),
    ('EMBARQUE PARA PASEO', 'ALIS', 0, ('ESTÁ AQUI. FIQUE PERTO,', 'MYAU. NOSSA NAVE ESPERA.')),
    ('NA PISTA', 'MYAU', 2, ('MAS... AQUELA NA PISTA', 'TAMBÉM TEM O SEU ESCUDO!')),
    ('NA PISTA', 'ALIS', 1, ('ATRÁS DE MIM, MYAU.', 'EU VOU FALAR COM ELA.')),
    ('DEPOIS DO ECO', 'ALIS', 0, ('VOCÊ TAMBÉM TEVE MEDO?', 'ENTÃO VENHA COM A GENTE.')),
    ('EMBARQUE PARA PASEO', 'MYAU', 2, ('A TORRE DEU O SINAL!', 'VAMOS, ALIS!')),
]


def native(image, size, colors):
    sample = image.convert('RGB').resize(size, Image.Resampling.NEAREST)
    table = bytes(min(range(len(colors)), key=lambda k: sum((a-b)**2 for a,b in zip(rgb(code),rgb(colors[k]))))
                  for code in range(64))
    dest = Image.new('L', size)
    dest.putdata([table[sum(min(3,(v+42)//85) << (2*i) for i,v in enumerate(c))] for c in sample.getdata()])
    return dest


def make_pages(backdrop, colors, spaceport):
    with Image.open(backdrop) as source:
        if spaceport:
            source = source.crop((0, source.height*32//192, source.width, source.height*123//192))
        view = native(source, (224,72), colors)
    with Image.open(ART / 'portraits.png') as source:
        w,h = source.size
        portraits = [native(source.crop((i*w//3,0,(i+1)*w//3,h)),(80,80),colors) for i in range(3)]
    def panel():
        return Image.new('L',(256,192),0)
    def rule(im, y):
        draw=ImageDraw.Draw(im)
        draw.line((16,y,239,y), fill=13)
        draw.line((16,y,35,y),fill=GOLD)
    pages={}
    title=panel()
    stamp_word(title,'MASTER OF',91,10,22,(WHITE,GOLD,3))
    stamp_word(title,'FIGHTERS',127,39,35,(WHITE,WHITE,5))
    rule(title,84)
    title.paste(view,(16,94))
    title.paste(portraits[1],(160,86))
    lettering(title,'APERTE 1',104,177,WHITE)
    pages['title']=title
    menu=panel()
    menu.paste(view,(16,12))
    stamp_word(menu,'FIGHTERS',95,88,20,(WHITE,GOLD,3))
    rule(menu,115)
    for i,label in enumerate(('HISTÓRIA DE ALIS','VERSUS LOCAL','OPÇÕES')):
        lettering(menu,label,40,132+i*16,WHITE)
    pages['menu']=menu
    opts=panel()
    lettering(opts,'OPÇÕES',16,18,WHITE,tracking=2)
    rule(opts,42)
    lettering(opts,'MÚSICA',32,62,GOLD)
    lettering(opts,'LIGADA',48,80,WHITE)
    lettering(opts,'MUTADA',152,80,WHITE)
    lettering(opts,'VITÓRIAS POR DUELO',32,110,GOLD)
    lettering(opts,'UMA',48,128,WHITE)
    lettering(opts,'DUAS',152,128,WHITE)
    rule(opts,151)
    lettering(opts,'DIRECIONAL ALTERA',24,159,WHITE)
    lettering(opts,'2 VOLTA',24,175,PEACH)
    pages['options']=opts
    for i,(place,who,face,lines) in enumerate(PORT_DIALOGUE if spaceport else DIALOGUE):
        im=panel()
        lettering(im,place,16,10,GOLD,tracking=2)
        rule(im,23)
        im.paste(view,(16,32))
        # Portrait anchored to the speaker; both eyes remain above dialogue.
        im.paste(portraits[face],(160 if face==2 else 16,24))
        rule(im,105)
        lettering(im,who,16,116,GOLD,tracking=2)
        for j,line in enumerate(lines):
            lettering(im,line,16,134+14*j,WHITE)
        lettering(im,'1 SEGUE',16,177,PEACH)
        lettering(im,'2 PULA',200,177,PEACH)
        pages['story'+str(i)]=im
    for name,title_text,subtitle,face in [('win1','VITÓRIA P1','ALIS DO MANTO ROSA',1),
                                         ('win2','VITÓRIA P2','ALIS DO MANTO VERDE',1),
                                         ('retry','OUTRA VEZ?','AINDA ESTOU COM VOCÊ.',2)]:
        im=panel()
        im.paste(portraits[face],(88,12))
        rule(im,96)
        if name=='retry':
            lettering(im,title_text,72,107,WHITE,2,GOLD)
        else:
            stamp_word(im,'VITÓRIA',128,102,25,(WHITE,GOLD,3),slant=1)
        lettering(im,subtitle,(256-(len(subtitle)*6-1))//2,133,PEACH)
        lettering(im,'1 REVANCHE',24,173,WHITE)
        lettering(im,'2 MENU',193,173,WHITE)
        pages[name]=im
    return pages


def encode(im, colors=PALETTE):
    arrow=Image.new('L',(8,8))
    ImageDraw.Draw(arrow).polygon([(1,0),(5,3),(1,6)],fill=GOLD)
    dot=Image.new('L',(8,8))
    ImageDraw.Draw(dot).rectangle((2,2,5,5),fill=CYAN)
    tiles={bytes(32):0, planar(list(arrow.getdata())):1, planar(list(dot.getdata())):2}
    tilemap=bytearray()
    for y in range(0,192,8):
        for x in range(0,256,8):
            tile=planar(list(im.crop((x,y,x+8,y+8)).getdata()))
            tilemap.extend(struct.pack('<H',tiles.setdefault(tile,len(tiles))))
    if len(tiles)>448:
        raise ValueError(f'{len(tiles)} patterns overlap the name table')
    return struct.pack('<H',len(tiles)*32)+bytes(colors)+b''.join(tiles)+tilemap


def pack(fighters, out, spaceport=False):
    out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((fighters/'mirror_build.json').read_bytes())
    tc=manifest['toolchain']
    backdrop = PORT_ART/'pista.png' if spaceport else ART/'camineet_capsulas.png'
    colors = PALETTE.copy()
    if spaceport:
        colors[7], colors[9] = 52, 32
    pages=make_pages(backdrop, colors, spaceport)
    banks=bytearray()
    declarations=[]
    records={}
    first=2+len((fighters/'mirror-banks.bin').read_bytes())//16384
    for name,im in pages.items():
        page_colors=[44 if code==35 and name=="win2" else code for code in colors]
        data=encode(im,page_colors)
        if len(data)>16384: raise ValueError(f'{name} exceeds mapper window')
        bank=first+len(banks)//16384
        declarations.append(f'#define MOF_PAGE_{name.upper()} {bank}u')
        banks.extend(data.ljust(16384,b'\xff'))
        im=im.convert('P')
        im.putpalette(bytes(c for code in page_colors for c in rgb(code)).ljust(768,b'\0'))
        im.save(out/(name+'.png'))
        records[name]={'bank': bank, 'tiles': int.from_bytes(data[:2],'little')//32}
    stage, limits=arena(fighters, PORT_ART if spaceport else ART, native, spaceport)
    declarations.append(f'#define MOF_ARENA_BANK {first+len(pages)}u')
    declarations.extend(f'#define MOF_{k} {v}u' for k,v in limits.items())
    banks.extend(stage.ljust(16384,b'\xff'))
    (out/'panels.bin').write_bytes(banks)
    (out/'alis_pages.h').write_text('\n'.join(declarations)+'\n',encoding='ascii')
    tc['defines']['MOF_ALIS_CHAPTER']=1
    if 'MOF_MIRROR_RIPOSTE_1' in (fighters/'duel_mirror_assets.h').read_text():
        tc['defines']['MOF_ALIS_RIPOSTE']=1
    tc['defines']['MOF_RULE_BANK']=first+len(pages)+1
    tc['mapper_code_banks']={'SMSBANK_RULES':first+len(pages)+1}
    tc['include_dirs'].append(out.relative_to(PROJECT).as_posix())
    tc['makesms_extra']+=['-mbank',f'{(out/"panels.bin").relative_to(PROJECT).as_posix()}:0:{len(pages)+1}:{first}']
    (out/'chapter.json').write_text(json.dumps(manifest,indent=2)+'\n')
    sources = [ART/'portraits.png', backdrop]
    if spaceport:
        sources.append(PORT_ART/'aves.png')
    (out/'pages.json').write_text(json.dumps({'palette':colors, 'pages':records,
        'sources':{path.name:digest(path) for path in sources},
        'psg_reference':{'game':'Phantasy Star (Master System)','track':'01 Title',
                         'author':'Tokuhiko Uwabo','variant':'PSG','use':'contour and phrasing',
                         'reference_url':'https://www.smspower.org/uploads/Music/PhantasyStar-SMS-PSG.zip',
                         'uncompressed_vgm_sha256':'0506ee3dfb98c69a30b09b0d456560990660998ce32a0827134a0f37abdfd849'}},indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fighters',type=Path)
    parser.add_argument('out',type=Path)
    parser.add_argument('--spaceport', action='store_true', help='Palma passport checkpoint in both game modes')
    args=parser.parse_args()
    pack(args.fighters.resolve(),args.out.resolve(),args.spaceport)
