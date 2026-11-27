"""Original five-column capitals for the cartridge, including Portuguese accents."""
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FIGHTER_NAME_FONT = Path(__file__).resolve().parents[1] / "data/source_art/type/barlow/Barlow-SemiBold.ttf"


def fighter_nameplates(names, max_width, max_height=21):
    """Use one proportional face and size for every fighter in the matchup."""
    for size in range(29, 11, -1):
        font = ImageFont.truetype(str(FIGHTER_NAME_FONT), size, layout_engine=ImageFont.Layout.BASIC)
        boxes = [font.getbbox(name, anchor="ls") for name in names]
        top = min(box[1] for box in boxes)
        bottom = max(box[3] for box in boxes)
        if bottom-top <= max_height and all(right-left <= max_width for left, _, right, _ in boxes):
            break
    else:
        raise ValueError(f"Fighter names exceed the available width: {names}")
    names_in_ink = []
    for name, (left, _, right, _) in zip(names, boxes):
        mask = Image.new("L", (right-left, bottom-top))
        ImageDraw.Draw(mask).text((-left,-top), name, font=font, fill=255, anchor="ls")
        # Navy background with two edge tones from the existing SMS palette.
        names_in_ink.append(mask.point(lambda v: 0 if v < 42 else 13 if v < 116 else 14 if v < 189 else 8))
    return names_in_ink

# Seven rows per glyph. In display lettering the broad edge catches a second ink.
ROWS = {
    'A':'0e11111f111111','B':'1e11111e11111e','C':'0f10101010100f','D':'1e11111111111e',
    'E':'1f10101e10101f','F':'1f10101e101010','G':'0f10101711110f','H':'1111111f111111',
    'I':'0e04040404040e','J':'0702020212120c','K':'11121418141211','L':'1010101010101f',
    'M':'111b1515111111','N':'11191915131311','O':'0e11111111110e','P':'1e11111e101010',
    'Q':'0e11111115120d','R':'1e11111e141211','S':'0f10100e01011e','T':'1f040404040404',
    'U':'1111111111110e','V':'11111111110a04','W':'11111115151b11','X':'11110a040a1111',
    'Y':'11110a04040404','Z':'1f01020408101f','0':'0e11131519110e','1':'040c040404040e',
    '2':'0e11010204081f','3':'1e01010e01011e','4':'02060a121f0202','5':'1f10101e01011e',
    '6':'0e10101e11110e','7':'1f010204080808','8':'0e11110e11110e','9':'0e11110f01010e',
    '.':'00000000000004',',':'00000000000408','!':'04040404040004','?':'0e110102040004',
    '-':'0000000e000000','/':'01010204081010',' ':'00000000000000'
}
# Text cut: broad top terminals, angled shoulders and a squared open bowl.
ROWS.update({
    'A':'070d19191f1919','B':'1e19191e19191e','C':'0f18181818180f',
    'D':'1c1a1919191a1c','E':'1f18181e18181f','F':'1f18181e181818',
    'G':'0f18101b19190f','H':'1919191f191919','I':'0e04040404040e',
    'J':'0703030313130e','K':'191a1c181c1a19','L':'1818181818181f',
    'N':'191d1d1b1b1919','O':'0e19191919190e','P':'1e1919191e1818',
    'Q':'0e1919191d1a0d','R':'1e1919191e1a19','S':'0f18180e03031e',
    'T':'1f0c0c0c0c0c0c','U':'1919191919190e','V':'191919190a0a04',
    'Z':'1f03060c18101f',
})
ACCENTS={'\u0301':((3,-2),(2,-1)), '\u0302':((2,-2),(1,-1),(3,-1)),
         '\u0303':((0,-1),(1,-2),(2,-2),(3,-1),(4,-2)), '\u0327':((2,7),(1,8))}


def lettering(canvas, text, x, y, ink, scale=1, shade=None, tracking=1):
    if x < 0 or x + (len(text) * (5*scale+tracking) - tracking) > canvas.width:
        raise ValueError(f'Text exceeds canvas: {text}')
    for char in text.upper():
        letter, *marks = unicodedata.normalize('NFD', char)
        rows = bytes.fromhex(ROWS[letter])
        dots = [(cx,cy) for cy,row in enumerate(rows) for cx in range(5) if row & (16>>cx)]
        for mark in marks:
            dots.extend(ACCENTS[mark])
        for cx,cy in dots:
            for dy in range(scale):
                for dx in range(scale):
                    canvas.putpixel((x+cx*scale+dx,y+cy*scale+dy),
                                    shade if shade is not None and cy>=4 else ink)
        x += 5*scale+tracking

# Engraved display capitals. Coordinates are in a 10 by 14 cap-height grid.
# A pen lifts between contours at '/'. Narrow I, wide M and clipped O are
# optical choices that also survive the single-row round caption.
STROKES = {
    'X': ('0,0 10,14/10,0 0,14',11),
    'A': ('0,14 2,3 5,0 8,0 9,14/2,8 8,8', 10),
    'B': ('1,14 1,0 7,0 9,2 9,4 6,7 1,7/6,7 9,9 9,11 6,14 1,14',10),
    'C': ('9,1 7,0 3,0 0,3 0,11 3,14 8,14',10),
    'D': ('1,14 1,0 6,0 9,3 9,10 5,14 1,14',10),
    'E': ('9,0 1,0 1,14 8,14/1,6 7,6',10),
    'F': ('1,14 1,0 10,0/1,6 7,6',10),
    'G': ('9,1 7,0 3,0 0,3 0,11 3,14 9,14 9,7 5,7',10),
    'H': ('1,0 1,14/9,0 9,14/1,7 9,6',10),
    'I': ('1,0 1,14',3),
    'K': ('1,0 1,14/9,0 2,8/5,6 9,14',10),
    'M': ('1,14 1,0 6,6 12,0 12,14',13),
    'N': ('1,14 1,0 9,11 9,0',10),
    'O': ('3,0 8,0 10,2 10,10 6,14 2,14 0,12 0,4 3,0',11),
    'P': ('1,14 1,0 8,0 10,2 10,5 7,8 1,8',11),
    'R': ('1,14 1,0 8,0 10,2 10,5 7,8 1,8/5,8 10,14',11),
    'S': ('10,0 3,0 0,3 0,5 8,8 9,10 9,11 6,14 0,14',11),
    'T': ('0,0 11,0/6,0 6,14',12),
    'U': ('1,0 1,11 3,14 7,14 9,11 9,0',10),
    'V': ('0,0 3,14 6,14 10,0',11),
    '1': ('0,3 4,0 4,14',5), '2': ('0,2 3,0 7,0 9,2 9,5 0,14 9,14',10),
    '3': ('0,0 9,0 5,6 9,8 9,11 6,14 0,14/2,6 5,6',10),
    ' ': ('',4), '.': ('1,13 1,14',3), '!': ('2,0 1,9/1,13 1,14',4),
}
def display_word(text, height, inks, slant=4):
    from PIL import Image, ImageDraw
    cap, face, edge = inks
    contours=[]
    pen=2
    for char in text:
        letter,*marks=unicodedata.normalize('NFD',char)
        paths,width=STROKES[letter]
        for line in paths.split('/'):
            if line:
                pts=[tuple(map(int,p.split(','))) for p in line.split()]
                contours.append([(pen+x+slant*(14-y)//14,4+y) for x,y in pts])
        if marks:
            if marks!=['\u0301']: raise ValueError(f'Unsupported display accent {char}')
            contours.append([(pen+4+slant,1),(pen+7+slant,-1)])
        pen+=width+4
    im=Image.new('LA',(pen+slant+3,22))
    draw=ImageDraw.Draw(im)
    for line in contours:
        draw.line([(x+1,y+2) for x,y in line],fill=(edge,255),width=5)
    for line in contours:
        draw.line(line,fill=(face,255),width=4)
        if len(line)>1 and line[0][1]==line[1][1]:
            draw.line(line[:2],fill=(cap,255),width=1)
    box=im.getchannel('A').getbbox()
    im=im.crop(box)
    return im.resize((max(1,round(im.width*height/im.height)),height),Image.Resampling.NEAREST)

def stamp_word(canvas,text,center,y,height,inks,slant=4):
    word=display_word(text,height,inks,slant)
    left=center-word.width//2
    if left<0 or left+word.width>canvas.width or y+height>canvas.height:
        raise ValueError(f'Display inscription exceeds panel: {text}')
    canvas.paste(word.getchannel('L'),(left,y),word.getchannel('A'))
