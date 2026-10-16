"""Assemble Blender-rendered motion proof. Requires Pillow."""
from PIL import Image, ImageDraw
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
frames=[]
for p in sorted((ROOT/'Previews/Frames').glob('*.png')):
    f=int(p.stem)
    label='WALK' if f<41 else ('BOW / DRAW - RELEASE' if f<97 else 'SWORD / ATTACK')
    im=Image.open(p).convert('RGB'); d=ImageDraw.Draw(im)
    d.rounded_rectangle((12,12,285,42),radius=10,fill=(36,74,75))
    d.text((25,22),label,fill=(255,238,195))
    frames.append(im)
assert len(frames)==39,len(frames)
frames[0].save(ROOT/'Previews/animations.gif',save_all=True,append_images=frames[1:],duration=125,loop=0,optimize=False)
print('GIF_OK',len(frames))
