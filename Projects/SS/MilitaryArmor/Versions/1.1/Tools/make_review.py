from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json

root=Path(__file__).resolve().parents[1]
block=root/'Blocks/MA-T01'
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
names=['Foundation','Azimuth bearing','Armored hull','Twin mantlet','Heavy barrel','Service hatch','Optics','Deck handle']
sheet=Image.new('RGB',(1600,900),(25,31,39));draw=ImageDraw.Draw(sheet)
draw.text((28,20),'MILITARY ARMOR / MA-T01 / PART LIBRARY',font=font,fill=(230,231,220))
for i,name in enumerate(names):
    pid=f'MA-P{i+1:02}'
    img=Image.open(root/f'Parts/{pid}/Previews/{pid}.png').convert('RGB');img.thumbnail((380,350))
    x=10+(i%4)*400;y=70+(i//4)*410
    sheet.paste(img,(x+(380-img.width)//2,y))
    draw.text((x+12,y+352),f'{pid}  /  {name}',font=small,fill=(228,229,218))
sheet.save(block/'Previews/MA-T01-parts.png')
poses=['top','rear','elevation-max','elevation-min','combined']
sheet=Image.new('RGB',(1500,1040),(25,31,39));draw=ImageDraw.Draw(sheet)
for i,name in enumerate(poses):
    img=Image.open(block/f'Previews/MA-T01-{name}.png').convert('RGB');img.thumbnail((490,470))
    x=(i%3)*500;y=(i//3)*520
    sheet.paste(img,(x,y));draw.text((x+15,y+475),name,font=font,fill=(228,229,218))
sheet.save(block/'Previews/MA-T01-review.png')
comparison=Image.new('RGB',(1600,850),(25,31,39));draw=ImageDraw.Draw(comparison)
for i,(path,title) in enumerate([(root/'Versions/1.0/Blocks/MA-T01/Previews/MA-T01-hero.png','1.0 / BEFORE'),(block/'Previews/MA-T01-hero.png','1.1 / MORE DETAIL')]):
    img=Image.open(path).convert('RGB');img.thumbnail((800,800));comparison.paste(img,(i*800,50));draw.text((i*800+24,14),title,font=font,fill=(230,231,220))
comparison.save(block/'Previews/MA-T01-comparison.png')
bad=[]
for p in root.rglob('*'):
    if p.suffix in ('.py','.md','.json'):
        data=p.read_bytes()
        if b'\n' in data.replace(b'\r\n',b''):bad.append(str(p))
print(json.dumps({'text_files_without_CRLF':bad,'parts_sheet':str(block/'Previews/MA-T01-parts.png')},indent=2))
