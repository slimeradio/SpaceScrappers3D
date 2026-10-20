"""Compose existing Blender renders; requires Pillow, does not generate geometry."""
from pathlib import Path
import json, sys
from PIL import Image, ImageOps, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
STYLE=HERE.parent.parent
OUT=STYLE/'Exports'/'CM-T01'
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',21)
title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',34)
parts=sorted((STYLE/'Parts').glob('*/preview.png'))
assert len(parts)==24
canvas=Image.new('RGB',(1440,2350),'#e6e8eb')
draw=ImageDraw.Draw(canvas)
draw.rectangle((0,0,1440,90),fill='#242a31')
draw.text((26,22),'CM-T01 / CHUNKY MODULAR / 24 PARTS',font=title,fill='#f3f1e9')
for i,path in enumerate(parts):
    x=(i%4)*360; y=100+(i//4)*375
    im=ImageOps.contain(Image.open(path).convert('RGB'),(350,330))
    canvas.paste(im,(x+(360-im.width)//2,y))
    draw.text((x+16,y+337),path.parent.name,font=font,fill='#242a31')
canvas.save(OUT/'parts-sheet.png')
focus=Image.new('RGB',(1680,630),'#e6e8eb')
fd=ImageDraw.Draw(focus)
for i,pid in enumerate(['cm-handle','cm-barrel','cm-receiver']):
    focus.paste(Image.open(STYLE/'Parts'/pid/'preview.png').convert('RGB'),(i*560,0))
    fd.text((i*560+24,582),pid,font=title,fill='#242a31')
focus.save(OUT/'parts-focus.png')
if '--parts-only' in sys.argv: raise SystemExit(0)
data=json.loads((OUT/'animation-frames.json').read_text(encoding='utf-8'))
frames=data['frames']
images=[Image.open(OUT/'animation-frames'/f'{frame:03d}.png').convert('RGB').quantize(colors=192) for frame in frames]
durations=[max(30,round((b-a)/data['fps']*100)*10) for a,b in zip(frames,frames[1:])]+[400]
images[0].save(OUT/'motion.gif',save_all=True,append_images=images[1:],duration=durations,loop=0,disposal=2,optimize=False)
print('Created parts-sheet.png and motion.gif')
