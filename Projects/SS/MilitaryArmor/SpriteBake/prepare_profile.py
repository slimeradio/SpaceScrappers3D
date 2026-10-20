"""Explicit MilitaryArmor adapter, never imported by the universal baker.

Initialise a new profile or explicitly append missing assemblies; preserve artist settings.
Scale policy: explicit floor-normalized assemblies, 1 BU/cell; native parts sit under ModelFit.
"""
import json
import argparse
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[2]
sys.path.insert(0, str(WORKSPACE/'Tools/SpriteBake'))
from common import read_json, write_json
import numpy as np


def matrix(item):
    x, y, z = item.get('rotation_euler_xyz', [0, 0, 0])
    cx, cy, cz, sx, sy, sz = math.cos(x), math.cos(y), math.cos(z), math.sin(x), math.sin(y), math.sin(z)
    m = np.eye(4)
    m[:3, :3] = np.array([[cz*cy, cz*sy*sx-sz*cx, cz*sy*cx+sz*sx],
        [sz*cy, sz*sy*sx+cz*cx, sz*sy*cx-cz*sx], [-sy, cy*sx, cy*cx]]) @ np.diag(item.get('scale', [1, 1, 1]))
    m[:3, 3] = item.get('translation', [0, 0, 0])
    return m


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--append-missing', action='store_true', help='Register new assemblies; preserve every existing block setting')
    args = parser.parse_args()
    target = ROOT/'SpriteBake/profile.json'
    existing = read_json(target) if target.exists() and args.append_missing else None
    if target.exists() and not args.append_missing:
        raise FileExistsError('Profile already exists; edit it explicitly: '+str(target))
    blocks = {}
    for path in sorted(ROOT.glob('Blocks/*/assembly.json')):
        a = read_json(path)
        bid = a['id']
        if existing is not None and bid in existing['blocks']:
            continue
        definitions = {n['id']: n for n in a.get('nodes', [])}
        definitions.setdefault(bid, {'id': bid})
        for item in a['instances']:
            definitions.setdefault(item['id'], item)
        def world(name):
            n = definitions[name]
            return (world(n['parent']) if n.get('parent') else np.eye(4)) @ matrix(n)
        bounds = []
        for item in a['instances']:
            meta = read_json((path.parent/item['source']).resolve().parent/'part.json')
            lo, hi = meta['bounds_local']['min'], meta['bounds_local']['max']
            for x in (lo[0], hi[0]):
                for y in (lo[1], hi[1]):
                    for z in (lo[2], hi[2]):
                        bounds.append(world(item['id']) @ np.array([x, y, z, 1]))
        points = np.array(bounds)
        if not a.get('floor_fit') or not any(i['id']=='Floor' and i.get('parent') is None for i in a['instances']):
            raise ValueError('Assembly needs an explicit floor-fit contract before SpriteBake: '+bid)
        scale = 1.0
        w, h = a['catalog_grid']
        layers = [{'id': 'body', 'draw_order': 0, 'rotates': False, 'pivot_bu': [0, 0],
                   'instances': [i['id'] for i in a['instances']]}]
        # Only this authoring rig is explicitly assigned a rotating layer here.
        # Other weapons are added below by explicit rig identity, not by object color.
        pivot_node = next((n for n in ('Azimuth', 'Yaw') if n in definitions), None)
        if pivot_node:
            def rotating(name):
                return name == pivot_node or (bool(definitions[name].get('parent')) and rotating(definitions[name]['parent']))
            fixed = [i['id'] for i in a['instances'] if not rotating(i['id'])]
            mobile = [i['id'] for i in a['instances'] if rotating(i['id'])]
            pivot = world(pivot_node)[:2, 3].tolist()
            layers = [{'id': 'base', 'draw_order': 0, 'rotates': False, 'pivot_bu': [0, 0], 'instances': fixed},
                      {'id': 'turret', 'draw_order': 1, 'rotates': True, 'pivot_bu': pivot, 'instances': mobile}]
        for layer in layers:
            layer['instances']=[iid for iid in layer['instances'] if iid!='Floor']
            layer['draw_order']+=1
        layers.insert(0,{'id':'floor','draw_order':0,'rotates':False,'pivot_bu':[0,0],'instances':['Floor']})
        reason = 'Temporary static replacement; no approved authored damage state or gameplay clip.'
        clips = {}
        if bid == 'MA-T01' or bid.startswith('MA-W'):
            clips = {'fire': {'alias': 'damage0', 'reason': reason}}
        elif bid.startswith('MA-E'):
            clips = {'work': {'alias': 'damage0', 'reason': reason}}
        blocks[bid] = {'assembly': path.relative_to(ROOT).as_posix(),
            'source': (path.parent/(bid+'.blend')).relative_to(ROOT).as_posix(),
            'bu_per_cell': scale, 'footprint_bu': [-w*scale/2, -h*scale/2, w*scale/2, h*scale/2],
            'height_range_bu': [math.floor((points[:, 2].min()-.02)*10)/10,
                                math.ceil((points[:, 2].max()+.02)*10)/10],
            'layers': layers, 'states': {'damage0': {'frame': 1},
                **{s: {'alias': 'damage0', 'reason': reason} for s in ('damage33', 'damage66', 'destroyed')}},
            'clips': clips, 'use_author_animation': False}
    if existing is not None:
        existing['blocks'].update(blocks)
        write_json(target, existing)
        print(target, len(blocks), 'new blocks;', len(existing['blocks']), 'total')
        return
    write_json(target, {'schema': 'SpriteBake.Profile/1', 'axes': {'up': '+Z', 'forward': '-Y'},
        'pilot': ['MA-A01', 'MA-T01', 'MA-E01'], 'samples': 16, 'threads': 8,
        'ao_samples': 8, 'ao_distance_bu': .15, 'padding_pixels': 4, 'emission_max': 4,
        'max_image_size': 4096,
        'material_roles': {'Armor': 'Color2', 'Ceramic': 'Color1', 'Titanium': 'Fixed',
            'Steel': 'Fixed', 'Dark': 'Fixed', 'Mark': 'Fixed', 'Warning': 'Fixed',
            'Photovoltaic': 'Fixed', 'Thermal':'Fixed', 'FloorSurface':'Color1','FloorArmor':'Color2',
            'Signal': 'Emissive', 'Optic': 'Emissive'}, 'blocks': blocks})
    print(target, len(blocks), 'blocks')


if __name__ == '__main__':
    main()
