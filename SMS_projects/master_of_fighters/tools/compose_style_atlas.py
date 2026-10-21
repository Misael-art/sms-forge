#!/usr/bin/env python3
import json, math, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
MAN=ROOT/'doc/dr_social_style_series_manifest_v1.json'
ANCHOR=ROOT/'data/source_art/concept_art/dr_social/historical_approved/model_sheet_cps2_alpha_cel_v1/dr_social_model_sheet_cps2_alpha_cel_v1.png'
OUT=ROOT/'data/source_art/concept_art/dr_social/review_drafts/concept_direction_explorations/dr_social_48_style_atlas_v1.png'
FONT=Path('/usr/share/fonts/liberation')
def f(name,size): return ImageFont.truetype(str(FONT/name),size)
def wrap(draw, text, ft, width):
    words=text.split(); lines=[]; line=''
    for word in words:
        test=(line+' '+word).strip()
        if draw.textbbox((0,0),test,font=ft)[2] <= width: line=test
        else:
            if line: lines.append(line)
            line=word
    if line: lines.append(line)
    return lines
def main():
    data=json.loads(MAN.read_text()); styles=data['styles'][1:]
    assert len(styles)==48
    anchor=Image.open(ANCHOR).convert('RGB')
    W=2200; header=580; row_h=250; H=header+len(styles)*row_h+100
    im=Image.new('RGB',(W,H),(247,244,237)); d=ImageDraw.Draw(im)
    navy=(5,12,67); muted=(80,96,110); border=(210,207,198); card=(252,250,246)
    d.text((56,30),'DR. FERDINAND SOCIAL · STYLE ATLAS',font=f('LiberationSans-Bold.ttf',42),fill=navy)
    d.text((58,86),'48 CANDIDATE STYLES · sequential catalog · one-page selection index',font=f('LiberationSans-Regular.ttf',24),fill=(49,103,134))
    d.text((58,126),'Approved identity/model sheet remains the fixed reference; entries below are style specifications, not 48 generated paintings.',font=f('LiberationSans-Regular.ttf',19),fill=muted)
    # compact anchor strip: original approved page is shown scaled proportionally and marked as reference
    thumb=anchor.copy(); thumb.thumbnail((575,344),Image.Resampling.LANCZOS); im.paste(thumb,(54,178))
    d.rounded_rectangle((650,178,2145,522),radius=18,fill=card,outline=border,width=2)
    d.text((680,198),'FIXED CHARACTER IDENTITY · APPROVED BASELINE',font=f('LiberationSans-Bold.ttf',23),fill=navy)
    fixed=['Dr. Ferdinand Social · Master of Darkness','Gray swept-back hair · round brass spectacles · lean adult ectomorph','Blue/cyan tailcoat, white shirt, burgundy accents, dark trousers and shoes','Cane, rapier, occult steel boomerang · violet effect only on boomerang','Fully human · no fangs, wings, claws, monster traits or costume redesign','Reference scale: about 7.5H · clean neutral background · five-view model-sheet form']
    y=242
    for line in fixed:
        d.ellipse((684,y+7,695,y+18),fill=(49,103,134)); d.text((710,y),line,font=f('LiberationSans-Regular.ttf',19),fill=(62,68,78)); y+=42
    d.text((58,540),'CATALOG · 48 CANDIDATES · each row carries all registered style descriptors',font=f('LiberationSans-Bold.ttf',23),fill=navy)
    title=f('LiberationSans-Bold.ttf',23); body=f('LiberationSans-Regular.ttf',17); small=f('LiberationSans-Regular.ttf',15); status=f('LiberationSans-Bold.ttf',14)
    for idx,s in enumerate(styles):
        y0=header+idx*row_h; y1=y0+row_h-12
        d.rounded_rectangle((48,y0,W-48,y1),radius=14,fill=card,outline=border,width=2)
        d.rounded_rectangle((68,y0+18,130,y0+72),radius=10,fill=(230,236,239),outline=border,width=1)
        d.text((81,y0+30),f"{s['sequence']:02d}",font=f('LiberationSans-Bold.ttf',26),fill=navy)
        d.text((152,y0+16),s['style_id'],font=title,fill=navy)
        ref=s['reference']; d.text((154,y0+52),ref['game_or_franchise']+' · '+ref['platform_and_era'],font=body,fill=(49,103,134))
        st='EXISTING CANDIDATE · REVIEW PENDING' if s.get('status')=='candidate_pending_owner_review' else 'NOT GENERATED · STYLE CANDIDATE'
        bbox=d.textbbox((0,0),st,font=status); sw=bbox[2]-bbox[0]
        d.rounded_rectangle((W-72-sw-25,y0+20,W-72,y0+52),radius=8,fill=(238,234,225),outline=border,width=1)
        d.text((W-84-sw,y0+28),st,font=status,fill=(105,74,41))
        # descriptors in two columns, no truncation
        labels=[('BASE STYLE',ref['base_art_style']),('LINEART',ref['lineart']),('MORPHOLOGY',ref['body_morphology']),('PALETTE / LIGHT',ref['palette_and_lighting'])]
        coords=[(154,y0+91),(1130,y0+91),(154,y0+161),(1130,y0+161)]
        for (lab,val),(x,yy) in zip(labels,coords):
            d.text((x,yy),lab,font=f('LiberationSans-Bold.ttf',13),fill=muted)
            lines=wrap(d,val,body,900)
            for j,line in enumerate(lines[:2]): d.text((x,yy+21+j*22),line,font=body,fill=(62,68,78))
        d.text((W-75,y1-25),'STYLE STUDY ONLY · identity and palette roles remain fixed',font=small,fill=muted,anchor='ra')
    d.text((54,H-55),'Selection atlas only. Candidate miniatures/full concept sheets are not implied. Each selected style proceeds to a complete 5-view sheet and review.',font=f('LiberationSans-Regular.ttf',18),fill=muted)
    OUT.parent.mkdir(parents=True,exist_ok=True); im.save(OUT,optimize=True); print(f'{OUT} {im.size}')
if __name__=='__main__': main()
