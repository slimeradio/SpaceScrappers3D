"""PNG contract validation and diagnostic previews. Requires Pillow and numpy."""
import struct
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from common import MAPS, read_json


def read_pixels(path):
    """Read our filter-0 RGBA8/16 PNGs without losing 16-bit normal/height data."""
    raw = Path(path).read_bytes()
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Invalid PNG signature: ' + str(path))
    offset, payload, header = 8, bytearray(), None
    while offset < len(raw):
        length = struct.unpack_from('>I', raw, offset)[0]
        kind, content = raw[offset+4:offset+8], raw[offset+8:offset+8+length]
        if len(content) != length or offset+12+length > len(raw):
            raise ValueError('Truncated PNG')
        expected = struct.unpack_from('>I', raw, offset+8+length)[0]
        if zlib.crc32(kind+content) & 0xffffffff != expected:
            raise ValueError('PNG CRC mismatch: ' + str(path))
        if kind == b'IHDR':
            header = struct.unpack('>IIBBBBB', content)
        if kind == b'IDAT':
            payload.extend(content)
        offset += length+12
        if kind == b'IEND':
            break
    w, h, bits, color, comp, filt, interlace = header
    if bits not in (8, 16) or color != 6 or comp or filt or interlace:
        raise ValueError('Unexpected PNG encoding')
    rows = np.frombuffer(zlib.decompress(payload), np.uint8).reshape(h, 1+w*4*(bits//8))
    if np.any(rows[:, 0]):
        raise ValueError('Expected filter-0 PNG')
    values = rows[:, 1:].copy().view(np.uint8 if bits == 8 else '>u2').reshape(h, w, 4)
    return values.astype(np.float32) / ((1 << bits)-1)


def verify_images(folder, report):
    w, h = report['size']
    checks = []
    for frame in report['frames']:
        for layer in report['layers']:
            path = Path(folder) / 'PNG' / frame / layer['id']
            if {p.stem for p in path.glob('*.png')} != set(MAPS):
                raise ValueError('Incomplete frame maps: ' + str(path))
            maps = {name: read_pixels(path / (name+'.png')) for name in MAPS}
            if any(a.shape != (h, w, 4) for a in maps.values()):
                raise ValueError('Canvas mismatch: ' + str(path))
            alpha = maps['albedo'][:, :, 3]
            if alpha.max() < .1:
                raise ValueError('Empty PNG layer')
            if np.max(np.abs(maps['material-mask'].sum(axis=2)-alpha)) > 4/255:
                raise ValueError('Material weights differ from coverage: ' + str(path))
            for name in ('normal', 'height', 'surface', 'emission'):
                if np.max(np.abs(maps[name][:, :, 3]-alpha)) > 2/255:
                    raise ValueError('Map alpha mismatch: ' + name)
            inside = alpha > .99
            normals = maps['normal'][:, :, :3]*2-1
            if inside.any() and np.max(np.abs(np.linalg.norm(normals[inside], axis=1)-1)) > .12:
                raise ValueError('Non-unit normals: ' + str(path))
            # Padding must protect the entire rendered silhouette from clipping.
            if max(alpha[0].max(), alpha[-1].max(), alpha[:, 0].max(), alpha[:, -1].max()) > .01:
                raise ValueError('Silhouette touches canvas boundary: ' + str(path))
            checks.append({'frame': frame, 'layer': layer['id'], 'pixels': int((alpha > 0).sum())})
    report['image_checks'] = checks


def srgb_to_linear(rgb):
    return np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)


def linear_to_srgb(rgb):
    return np.where(rgb <= .0031308, rgb*12.92, 1.055*np.maximum(rgb, 0)**(1/2.4)-.055)


def shaded(folder, report, variant=0):
    w, h = report['size']
    yy, xx = np.mgrid[:h, :w]
    cell = report['quality']
    # A reproducible procedural demonstration, not an imported style texture.
    stripe = np.sin((xx+yy*.27)/cell*58 + np.sin(xx/cell*13)*1.8)
    slate = (.73 + .18*stripe + .09*np.sin(yy/cell*173))[:, :, None]
    colors = ((np.array([.18, .54, .80]), np.array([.85, .31, .12])) if variant == 0
              else (np.array([.62, .25, .76]), np.array([.25, .70, .33])))
    background = np.full((h, w, 3), .035, dtype=np.float32)
    for layer in sorted(report['layers'], key=lambda x: x['draw_order']):
        path = Path(folder) / 'PNG' / 'damage0' / layer['id']
        base = read_pixels(path/'albedo.png')
        masks = read_pixels(path/'material-mask.png')
        coverage = base[:, :, 3:4]
        weights = masks / np.maximum(coverage, 1e-6)
        rgb = srgb_to_linear(base[:, :, :3])
        # Composite material contributions, Fixed remains unchanged by color selection.
        rgb *= (weights[:, :, 0:1]*colors[0]*slate +
                weights[:, :, 1:2]*colors[1]*(slate if variant else 1) +
                weights[:, :, 2:3]*.03 + weights[:, :, 3:4])
        normals = read_pixels(path/'normal.png')[:, :, :3]*2-1
        light = np.array([-.5, .35, .8]); light /= np.linalg.norm(light)
        diffuse = np.maximum((normals*light).sum(axis=2, keepdims=True), 0)
        surface = read_pixels(path/'surface.png')[:, :, :3]
        rgb *= (.4+.6*diffuse)*surface[:, :, 2:3]
        emission = read_pixels(path/'emission.png')[:, :, :3]*report['emission_max']
        rgb += emission*np.array([.03, .7, 1])
        background = rgb*coverage + background*(1-coverage)
    return Image.fromarray(np.rint(np.clip(linear_to_srgb(background), 0, 1)*255).astype(np.uint8))


def build_preview(folder, report):
    folder = Path(folder)
    dest = folder/'Previews'
    dest.mkdir(exist_ok=True)
    images = [shaded(folder, report, i) for i in (0, 1)]
    w, h = images[0].size
    annotated = images[0].copy()
    draw = ImageDraw.Draw(annotated)
    x0, y0, _, _ = report['canvas_bu']
    fx0, fy0, fx1, fy1 = report['footprint_bu']
    unit = report['quality']/report['bu_per_cell']
    cell = report['bu_per_cell']
    for x in np.arange(fx0, fx1+cell*.1, cell):
        px = (x-x0)*unit
        draw.line((px, 0, px, h), fill=(90, 100, 115))
    for y in np.arange(fy0, fy1+cell*.1, cell):
        py = (y-y0)*unit
        draw.line((0, py, w, py), fill=(90, 100, 115))
    draw.rectangle(((fx0-x0)*unit, (fy0-y0)*unit, (fx1-x0)*unit, (fy1-y0)*unit), outline=(255, 210, 40), width=2)
    for layer in report['layers']:
        pivot = layer.get('pivot_bu', [0, 0])
        px, py = (pivot[0]-x0)*unit, (pivot[1]-y0)*unit
        draw.line((px-7, py, px+7, py), fill=(255, 65, 100), width=2)
        draw.line((px, py-7, px, py+7), fill=(255, 65, 100), width=2)
    annotated.save(dest/'grid-footprint-pivot.png')
    images[0].save(dest/'paint-slate-a.png')
    images[1].save(dest/'paint-slate-b.png')
    # Show Fixed (alpha data channel) as a fourth independent grayscale mask.
    tiles = []
    for layer in report['layers']:
        mask = read_pixels(folder/'PNG/damage0'/layer['id']/'material-mask.png')
        for i, role in enumerate(('Color1', 'Color2', 'Emissive', 'Fixed')):
            tile = Image.fromarray(np.rint(mask[:, :, i]*255).astype(np.uint8)).convert('RGB')
            ImageDraw.Draw(tile).text((5, 5), layer['id']+' / '+role, fill='white', stroke_width=1, stroke_fill='black')
            tiles.append(tile)
    sheet = Image.new('RGB', (w*4, h*len(report['layers'])), '#10131a')
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i%4)*w, (i//4)*h))
    sheet.save(dest/'material-masks.png')


def compare_qualities(output, bid):
    outputs = [Path(output)/str(q)/bid for q in (128, 256)]
    paths = [p/'Previews/paint-slate-a.png' for p in outputs]
    if not all(p.is_file() for p in paths):
        return
    images = [Image.open(p).convert('RGB') for p in paths]
    # Display each profile at 128 pixels/cell for a same-size visual comparison.
    images[1] = images[1].resize((round(images[1].width/2), round(images[1].height/2)), Image.Resampling.LANCZOS)
    w, h = max(i.width for i in images), max(i.height for i in images)
    sheet = Image.new('RGB', (w*2, h+25), '#10131a')
    draw = ImageDraw.Draw(sheet)
    for i, image in enumerate(images):
        sheet.paste(image, (i*w, 25))
        draw.text((i*w+5, 5), ('128 px/cell', '256 px/cell -> 128 display')[i], fill='white')
    dest = Path(output)/'Previews'
    dest.mkdir(exist_ok=True)
    sheet.save(dest/(bid+'-128-vs-256.png'))
