"""Explicit game-root bridge. Preserve XML bytes outside geometry attributes."""
from collections import defaultdict
from pathlib import Path
import re
import math
import uuid
import xml.etree.ElementTree as ET

from common import digest, read_json, write_json


def definitions(game_root):
    root = Path(game_root).resolve() / 'Assets/Definitions'
    if not root.is_dir():
        raise ValueError('Game root must contain Assets/Definitions')
    entries = {}
    for path in sorted(root.rglob('*.definition.xml')):
        element = ET.fromstring(path.read_bytes())
        key = (element.tag, element.attrib['Name'])
        if key in entries:
            raise ValueError('Duplicate definition: ' + repr(key))
        entries[key] = (path, element)
    return root, entries


def muzzle_points(block):
    return [p for p in block['frames']['damage0']['points']
            if p['category'] == 'functional_points' and
            (p['local_id'] in ('muzzle', 'shoot', 'launch', 'continuous-emitter') or
             p.get('role') in ('muzzle', 'projectile-muzzle'))]


def patch_repeated(data, tag, transform):
    text=data.decode('utf-8')
    pattern=r'<'+re.escape(tag)+r'\b[^>]*(?:/>|>[\s\S]*?</'+re.escape(tag)+r'>)'
    matches=list(re.finditer(pattern,text));result=[];end=0
    for i,match in enumerate(matches):
        result.extend((text[end:match.start()],transform(i,match[0].encode('utf-8')).decode('utf-8')));end=match.end()
    result.append(text[end:]);return ''.join(result).encode('utf-8'),len(matches)


def patch_coordinates(data, element, coordinates, attributes=('X', 'Y')):
    # Decode/re-encode retains UTF-8 BOM, comments, whitespace and line endings.
    text = data.decode('utf-8')
    matches = list(re.finditer(r'<' + re.escape(element) + r'\b[^>]*>', text))
    if len(matches) != 1:
        raise ValueError('Expected one XML element: ' + element)
    match = matches[0]
    node = match.group()
    for name, value in zip(attributes, coordinates):
        if abs(value) < .0000005:
            value = 0
        number = format(value, '.6f').rstrip('0').rstrip('.')
        pattern = r'(\b' + name + r'\s*=\s*[\"\x27])[^\"\x27]*([\"\x27])'
        node, count = re.subn(pattern, lambda m: m[1] + number + m[2], node)
        if count != 1:
            raise ValueError('Expected one coordinate attribute: ' + element + '.' + name)
    return (text[:match.start()] + node + text[match.end():]).encode('utf-8')


def patch_attribute(data, tag, attribute, old, new):
    text = data.decode('utf-8')
    pattern = r'(<' + re.escape(tag) + r'\b[^>]*\b' + re.escape(attribute) + r'\s*=\s*[\"\x27])' + re.escape(old) + r'([\"\x27])'
    text, count = re.subn(pattern, lambda m: m[1] + new + m[2], text)
    if count != 1:
        raise ValueError('Expected one reference: ' + tag + '.' + attribute + '=' + old)
    return text.encode('utf-8')


def sync_plan(game_root, blocks):
    root, index = definitions(game_root)
    consumers = defaultdict(set)
    for (kind, name), (_, item) in index.items():
        if kind in ('Block', 'ReactorBlock'):
            for tag in ('Turret', 'WeaponDefinition'):
                ref = item.find(tag)
                if ref is not None:
                    consumers[(tag, ref.attrib['Ref'])].add(name)
        elif kind == 'Weapon':
            for barrel in item.findall('Barrels/Barrel'):
                consumers[('Barrel', barrel.attrib['Ref'])].add(name)
    edits, coverage = {}, []
    def propose(path, tag, xy, model, attributes=('X', 'Y')):
        original = edits[path]['after'] if path in edits else path.read_bytes()
        changed = patch_coordinates(original, tag, xy, attributes)
        before = edits[path]['before'] if path in edits else original
        edits[path] = {'before': before, 'after': changed, 'model': model}
    def isolate(owner_path, owner_element, tag, kind, consumer_kind, consumer, model, reference=None):
        node = next(n for n in owner_element.findall(tag) if reference is None or n.attrib['Ref'] == reference)
        name = node.attrib['Ref']
        if not (consumers[(consumer_kind, name)] - {consumer}):
            return name
        source_path, source_element = index[(kind, name)]
        new_name = name + '-' + consumer + '-model'
        target = source_path.with_name(new_name + '.definition.xml')
        if target.exists() or (kind, new_name) in index:
            raise ValueError('Derived definition already exists without expected binding: ' + new_name)
        original = edits[owner_path]['after'] if owner_path in edits else owner_path.read_bytes()
        owner_before = edits[owner_path]['before'] if owner_path in edits else original
        edits[owner_path] = {'before': owner_before,
                             'after': patch_attribute(original, tag, 'Ref', name, new_name), 'model': model}
        cloned = patch_attribute(source_path.read_bytes(), kind, 'Name', name, new_name)
        edits[target] = {'before': None, 'after': cloned, 'model': model}
        clone = ET.fromstring(cloned)
        index[(kind, new_name)] = (target, clone)
        node.set('Ref', new_name)
        consumers[(consumer_kind, name)].discard(consumer)
        consumers[(consumer_kind, new_name)].add(consumer)
        if kind == 'Weapon':
            for barrel in clone.findall('Barrels/Barrel'):
                consumers[('Barrel', barrel.attrib['Ref'])].add(new_name)
        meta = target.with_name(target.name + '.meta')
        guid = uuid.uuid5(uuid.NAMESPACE_URL, 'SpaceScrappers/Definitions/' + target.relative_to(root).as_posix()).hex
        edits[meta] = {'before': None, 'after': ('fileFormatVersion: 2\r\nguid: ' + guid + '\r\nDefaultImporter:\r\n  externalObjects: {}\r\n  userData: \r\n  assetBundleName: \r\n  assetBundleVariant: \r\n').encode(), 'model': model}
        return new_name
    for block in blocks:
        key = next((k for k in (('Block', block['catalog_id']), ('ReactorBlock', block['catalog_id'])) if k in index), None)
        if key is None:
            coverage.append({'id': block['id'], 'catalog_id': block['catalog_id'], 'status': 'missing-definition'})
            continue
        block_path, definition = index[key]
        size = definition.find('Size')
        fx0, fy0, fx1, fy1 = block['footprint_bu']
        scale = block['bu_per_cell']
        if abs((fx1-fx0)/scale-float(size.attrib['X'])) > 1e-5 or abs((fy1-fy0)/scale-float(size.attrib['Y'])) > 1e-5:
            raise ValueError('Model/definition footprint mismatch: ' + block['id'])
        if definition.find('MiningLaser') is not None:
            points = [p for p in block['frames']['damage0']['points'] if p['category'] == 'functional_points'
                      and p.get('role') in ('mining-beam-origin', 'mining-laser-emission')]
            if len(points) != 1:
                raise ValueError('MiningLaser requires one explicit model emitter: ' + block['id'])
            point = points[0]
            direction = point.get('direction_block', point.get('forward_block'))
            if direction is None or abs(direction[0]) > 1e-5 or direction[1] >= -1e-5:
                raise ValueError('Current 2D mining laser requires emitter pointing forward: ' + point['id'])
            xy = point['position_cells'][:2]
            propose(block_path, 'MiningLaser', xy, block['id'], ('MuzzleX', 'MuzzleY'))
            coverage.append({'id': block['id'], 'catalog_id': block['catalog_id'],
                             'status': 'mining-geometry-synced', 'point': point['id'], 'muzzle': xy})
            continue
        fit=block.get('assembly',{}).get('floor_fit',{})
        if definition.find('Drill') is not None and fit:
            order=fit['drill_head_order'];radii=fit['drill_radii_cells']
            points={p['id']:p for p in block['frames']['damage0']['points']}
            if len(order)!=len(definition.findall('Drill/Head')):raise ValueError('Drill head count mismatch: '+block['id'])
            def head(i,data):
                point=points[order[i]];radius=radii[order[i]]
                if not math.isfinite(radius) or radius<=0:raise ValueError('Invalid model drill radius')
                return patch_coordinates(data,'Head',point['position_cells'][:2]+[radius],('X','Y','Radius'))
            before=block_path.read_bytes();after,count=patch_repeated(before,'Head',head)
            if count!=len(order):raise ValueError('Drill XML head count mismatch')
            edits[block_path]={'before':before,'after':after,'model':block['id']}
            coverage.append({'id':block['id'],'catalog_id':block['catalog_id'],'status':'drill-geometry-synced','points':order})
            continue
        if definition.find('Thrusters') is not None and fit:
            order=fit['thruster_point_order'];points={p['id']:p for p in block['frames']['damage0']['points']}
            if len(order)!=len(definition.findall('Thrusters/Thruster')):raise ValueError('Thruster count mismatch: '+block['id'])
            def thruster(i,data):
                point=points[order[i]];exhaust=points[order[i][:-len('thrust')]+'exhaust']
                dx=point['position_bu'][0]-exhaust['position_bu'][0];dy=exhaust['position_bu'][1]-point['position_bu'][1]
                length=math.hypot(dx,dy)
                if not math.isfinite(length) or length<=1e-9:raise ValueError('Invalid projected model thrust direction')
                return patch_coordinates(patch_coordinates(data,'Position',point['position_cells'][:2]),'Direction',[dx/length,dy/length])
            before=block_path.read_bytes();after,count=patch_repeated(before,'Thruster',thruster)
            if count!=len(order):raise ValueError('Thruster XML count mismatch')
            edits[block_path]={'before':before,'after':after,'model':block['id']}
            coverage.append({'id':block['id'],'catalog_id':block['catalog_id'],'status':'thrust-geometry-synced','points':order})
            continue
        weapon_ref = definition.find('WeaponDefinition')
        if weapon_ref is None:
            coverage.append({'id': block['id'], 'catalog_id': block['catalog_id'], 'status': 'definition-present'})
            continue
        turret_ref = definition.find('Turret')
        if turret_ref is None:
            raise ValueError('Weapon has no supported mount: ' + block['id'])
        layers = [layer for layer in block['layers'] if layer['rotates']]
        original_turret = index[('Turret', turret_ref.attrib['Ref'])][1]
        fixed = (not layers and float(original_turret.attrib['FiringArcDegrees']) == 0 and
                 float(original_turret.attrib['RotateSpeedDegreesPerSecond']) == 0)
        turret_name = (turret_ref.attrib['Ref'] if fixed else
                       isolate(block_path, definition, 'Turret', 'Turret', 'Turret', block['catalog_id'], block['id']))
        weapon_name = isolate(block_path, definition, 'WeaponDefinition', 'Weapon', 'WeaponDefinition', block['catalog_id'], block['id'])
        turret_path, _ = index[('Turret', turret_name)]
        weapon_path, weapon = index[('Weapon', weapon_name)]
        for barrel in list(weapon.findall('Barrels/Barrel')):
            name = barrel.attrib['Ref']
            if consumers[('Barrel', name)] - {weapon_name}:
                # Barrel lives below Barrels; isolate uses Element.find so pass its parent.
                isolate(weapon_path, weapon.find('Barrels'), 'Barrel', 'Barrel', 'Barrel', weapon_name, block['id'], name)
        if len(layers) != 1 and not fixed:
            raise ValueError('Expected exactly one weapon layer: ' + block['id'])
        if fixed:
            # A fixed mount has no model rotation pivot. Keep the existing reference
            # and express the model muzzle relative to it; its absolute position is exact.
            pivot = original_turret.find('RotationPivot')
            px, py = fx0+float(pivot.attrib['X'])*scale, fy0+float(pivot.attrib['Y'])*scale
        else:
            px, py = layers[0]['pivot_bu']
            propose(turret_path, 'RotationPivot', [(px-fx0)/scale, (py-fy0)/scale], block['id'])
        points = muzzle_points(block)
        barrels = [index[('Barrel', b.attrib['Ref'])] for b in weapon.findall('Barrels/Barrel')]
        if len(points) != len(barrels) or not points:
            raise ValueError('Model muzzle count differs from weapon barrels: ' + block['id'])
        points.sort(key=lambda p: (p['position_bu'][0], p['position_bu'][1], p['id']))
        barrels.sort(key=lambda entry: (float(entry[1].find('ShootPosition').attrib['X']),
                                         float(entry[1].find('ShootPosition').attrib['Y']), entry[1].attrib['Name']))
        mappings = []
        for point, (path, barrel) in zip(points, barrels):
            if not fixed and point['layer'] != layers[0]['id']:
                raise ValueError('Muzzle is outside the weapon layer: ' + point['id'])
            direction = point.get('direction_block', point.get('forward_block'))
            if direction is None or abs(direction[0]) > 1e-5 or direction[1] >= -1e-5:
                raise ValueError('Current 2D weapon requires muzzle pointing forward: ' + point['id'])
            if consumers[('Barrel', barrel.attrib['Name'])] - {weapon_name}:
                raise ValueError('Shared barrel must be separated before syncing: ' + barrel.attrib['Name'])
            x, y, _ = point['position_bu']
            xy = [(x-px)/scale, -(y-py)/scale]
            propose(path, 'ShootPosition', xy, block['id'])
            mappings.append({'point': point['id'], 'barrel': barrel.attrib['Name'], 'shoot_position': xy})
        coverage.append({'id': block['id'], 'catalog_id': block['catalog_id'],
                         'status': 'weapon-geometry-synced', 'barrels': mappings})
    return root, edits, coverage


def synchronize(game_root, blocks, backup_root):
    root, edits, coverage = sync_plan(game_root, blocks)
    changed = {p: e for p, e in edits.items() if e['before'] != e['after']}
    backup = Path(backup_root) / ('definitions-' + uuid.uuid4().hex)
    backup.mkdir(parents=True)
    report = {'schema': 'SpriteBake.DefinitionSync/1', 'coverage': coverage,
              'changes': [{'file': p.relative_to(root).as_posix(), 'model': e['model'],
                           'before_sha256': digest(p) if e['before'] is not None else None} for p, e in changed.items()]}
    write_json(backup / 'plan.json', report)
    for path, entry in changed.items():
        target = backup / path.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry['before'] is not None:
            target.write_bytes(entry['before'])
    installed = []
    try:
        for path, entry in changed.items():
            if (path.read_bytes() if path.exists() else None) != entry['before']:
                raise RuntimeError('XML changed while preparing synchronization: ' + str(path))
        for path, entry in changed.items():
            temp = path.with_name(path.name + '.sprite-sync-' + uuid.uuid4().hex)
            temp.write_bytes(entry['after'])
            temp.replace(path)
            installed.append(path)
    except BaseException:
        for path in reversed(installed):
            if changed[path]['before'] is None:
                path.unlink()
            else:
                path.write_bytes(changed[path]['before'])
        raise
    report['backup'] = str(backup)
    write_json(backup / 'result.json', report)
    return report
