from PIL import Image,ImageDraw
from pathlib import Path
r=Path(__file__).resolve().parents[1]
out=Image.new('RGB',(1400,800),'#0d1c28');d=ImageDraw.Draw(out)
for n in range(1,8):
    x=((n-1)%4)*350;y=((n-1)//4)*380
    img=Image.open(r/'Parts'/f'CHT-P{n:02}'/'Previews/perspective.png')
    out.paste(img.crop((270,180,1190,910)).resize((350,278)),(x,y+45))
    d.text((x+15,y+20),f'CHT-P{n:02} / 1.1.0',fill='#72dfff')
out.save(r/'Blocks/CHT-T01/Previews/parts-catalog.png')
