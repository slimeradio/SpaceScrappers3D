"""Verify published files and current input hashes; make a pilot contact sheet."""
from pathlib import Path
import sys
import datetime
import numpy as np
from PIL import Image, ImageDraw

STYLE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(STYLE.parents[2]/'Tools/SpriteBake'))
from common import digest, fingerprint, inventory, read_json, write_json

profile = read_json(STYLE/'SpriteBake/profile.json')
output = STYLE/'Exports/Sprites'
pilot_only = '--pilot' in sys.argv
bids = profile['pilot'] if pilot_only else list(profile['blocks'])
results = []
source_hashes = {}
for quality in (128, 256):
    for bid in bids:
        folder = output/str(quality)/bid
        report = read_json(folder/'Reports/report.json')
        for name, sha in report['inputs'].items():
            if name not in source_hashes:
                source_hashes[name] = digest(STYLE/name)
            assert source_hashes[name] == sha, ('Source changed after bake', name)
        actual_key, _ = fingerprint(STYLE, profile, bid,
            sorted(STYLE/name for name in report['inputs']), quality, report['blender'])
        assert actual_key == report['fingerprint'], ('Stale code or settings', bid, quality)
        actual = inventory(folder)
        assert actual == report['outputs'], ('Output changed', bid, quality)
        assert all(p.suffix == '.png' for p in (folder/'PNG').rglob('*') if p.is_file())
        assert len(report['image_checks']) == len(report['frames'])*len(report['layers'])
        results.append({'id':bid, 'quality':quality, 'png_count':len(actual),
                        'temporary_replacements':len(report['temporary_replacements'])})

# One compact overview, preserving equal 128 pixels/cell for all pilot models.
tiles = []
for bid in profile['pilot']:
    image = Image.open(output/'128'/bid/'Previews/grid-footprint-pivot.png').convert('RGB')
    tile = Image.new('RGB', (max(200,image.width+16), image.height+45), '#151921')
    tile.paste(image, ((tile.width-image.width)//2, 35))
    ImageDraw.Draw(tile).text((8,8), bid+' / 128 px per cell', fill='white')
    tiles.append(tile)
sheet = Image.new('RGB', (sum(t.width for t in tiles), max(t.height for t in tiles)), '#151921')
x = 0
for tile in tiles:
    sheet.paste(tile,(x,0)); x += tile.width
preview = output/'Previews/pilot.png'
preview.parent.mkdir(exist_ok=True)
sheet.save(preview)

if not pilot_only:
    columns, tw, th = 8, 180, 190
    catalog = Image.new('RGB', (columns*tw, ((len(bids)+columns-1)//columns)*th), '#151921')
    draw = ImageDraw.Draw(catalog)
    for i,bid in enumerate(bids):
        image = Image.open(output/'128'/bid/'Previews/paint-slate-a.png').convert('RGB')
        image.thumbnail((tw-16,th-30),Image.Resampling.LANCZOS)
        x,y = (i%columns)*tw,(i//columns)*th
        catalog.paste(image,(x+(tw-image.width)//2,y+25))
        draw.text((x+8,y+5),bid,fill='white')
    catalog.save(output/'Previews/catalog-overview.png')

repairs = read_json(STYLE/'SpriteBake/bevel-repairs.json')
report = {'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'block_count':len(bids), 'quality_count':2, 'results':results,
    'png_count':sum(r['png_count'] for r in results),
    'source_dependency_count':len(source_hashes),
    'repaired_parts':[r['part'] for r in repairs],
    'geometry_and_image_checks':'passed; see per-part and per-block reports',
    'artistic_acceptance':'pending user review', 'unity_changed':False,
    'glb_generated':False, 'pilot_preview':str(preview)}
write_json(STYLE/'SpriteBake'/('pilot-verification.json' if pilot_only else 'delivery-verification.json'),report)
print('VERIFIED',len(results),'block/quality outputs;',report['png_count'],'PNGs')
print(preview)
