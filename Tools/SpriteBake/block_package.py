"""Portable lossless authoring export: maps, evaluated semantics and definition source snapshots."""
import csv
import re
from pathlib import Path
import shutil
import uuid

from common import confined, digest, inventory, publish, read_json, render_settings, write_json
from definition_bridge import definitions


def image_settings_match(previous, current, material_slots):
    """An unused new role name cannot change an unchanged image producer.

    Preserve the original report verbatim. Never accept a changed or removed
    mapping, a used new mapping, or any other changed render setting.
    """
    if previous == current:
        return True
    if not material_slots:
        return False
    if not isinstance(previous, dict):
        return False
    old, new = dict(previous), dict(current)
    old_roles, new_roles = old.pop('material_roles', {}), new.pop('material_roles', {})
    if old != new or any(new_roles.get(k) != v for k, v in old_roles.items()):
        return False
    used = {name for instance in material_slots.values() for slots in instance.values() for slot in slots
            for name in (slot['id'], re.sub(r'\.\d{3}$', '', slot['id']))}
    return not (set(new_roles) - set(old_roles)) & used


def package_inventory(folder):
    return {p.relative_to(folder).as_posix(): digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}


def verify_package(folder):
    folder = Path(folder)
    manifest = read_json(folder / 'package.json')
    if manifest.get('schema') != 'SpriteBake.BlockPackage/1':
        raise ValueError('Unsupported block package schema')
    actual = package_inventory(folder)
    actual.pop('package.json')
    if actual != manifest['files']:
        raise ValueError('Package file inventory/hash mismatch')
    blocks = manifest['blocks']
    if len({b['id'] for b in blocks}) != len(blocks) or len({b['catalog_id'] for b in blocks}) != len(blocks):
        raise ValueError('Duplicate package block identity')
    points, maps = 0, 0
    for entry in blocks:
        model = read_json(confined(folder, entry['model']))
        images_path = confined(folder, entry['images'])
        images = read_json(images_path)
        if model['id'] != entry['id'] or model['catalog_id'] != entry['catalog_id']:
            raise ValueError('Package model identity mismatch')
        if set(images['frames']) != set(model['frames']):
            raise ValueError('Package frame mismatch')
        if len(images['outputs']) != len(model['frames']) * len(model['layers']) * 6:
            raise ValueError('Incomplete six-map frame/layer export')
        for path, expected in images['outputs'].items():
            if digest(confined(images_path.parent, path)) != expected:
                raise ValueError('Package image hash mismatch')
        for path in entry['definition_sources']:
            confined(folder, path)
        points += len(model['frames']['damage0']['points'])
        maps += len(images['outputs'])
    return {'blocks': len(blocks), 'files': len(actual), 'maps': maps, 'rest_semantics': points}


def export_package(workspace, root, profile, metadata, game_root, quality):
    content, index = definitions(game_root)
    output = root / 'Exports/Packages'
    output.mkdir(parents=True, exist_ok=True)
    stage = output / ('.staging-' + str(quality) + '-' + uuid.uuid4().hex)
    stage.mkdir()
    blocks = []
    selected = {b['catalog_id'] for b in metadata}
    if len(selected) != len(metadata):
        raise ValueError('Multiple models claim the same catalog ID')
    for block in metadata:
        bid = block['id']
        source = root / 'Exports/Sprites' / str(quality) / bid
        report = read_json(source / 'Reports/report.json')
        if not image_settings_match(report.get('render_settings'), render_settings(profile, bid), block.get('material_slots', {})):
            raise ValueError('Missing or stale image settings provenance; bake required: ' + bid)
        # Image provenance stays with the image producer, independent of metadata tool changes.
        # Never reinterpret an old render after source/settings changes.
        if (report['bu_per_cell'] != block['bu_per_cell'] or
                report['footprint_bu'] != block['footprint_bu'] or
                report['layers'] != block['layers']):
            raise ValueError('Bake geometry settings differ from metadata: ' + bid)
        for name, expected in report['inputs'].items():
            if digest(confined(root, name)) != expected:
                raise ValueError('Stale image source: ' + bid + '/' + name)
        if report['clips'] != block['clips']:
            raise ValueError('Bake clips differ from metadata: ' + bid)
        if set(report['frames']) != set(block['frames']):
            raise ValueError('Bake frames differ from metadata: ' + bid)
        actual = {k: v for k, v in inventory(source).items() if k.startswith('PNG/')}
        expected = {k: v for k, v in report['outputs'].items() if k.startswith('PNG/')}
        if not expected or actual != expected:
            raise ValueError('Missing or corrupt image output: ' + bid)
        target = stage / 'Blocks' / bid
        shutil.copytree(source / 'PNG', target / 'PNG')
        # Raw local metadata and evaluated frame poses are both retained.
        write_json(target / 'model.json', block)
        write_json(target / 'images.json', dict(report, outputs=expected))
        key = next((k for k in (('Block', block['catalog_id']), ('ReactorBlock', block['catalog_id'])) if k in index), None)
        sources = []
        if key is not None:
            pending, visited = [key], set()
            while pending:
                current = pending.pop()
                if current in visited:
                    continue
                visited.add(current)
                path, element = index[current]
                relative = path.relative_to(content)
                snapshot = stage / 'DefinitionSources' / relative
                snapshot.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, snapshot)
                sources.append(snapshot.relative_to(stage).as_posix())
                for tag, kind in (('Turret', 'Turret'), ('WeaponDefinition', 'Weapon')):
                    node = element.find(tag)
                    if node is not None:
                        pending.append((kind, node.attrib['Ref']))
                for node in element.findall('Barrels/Barrel'):
                    pending.append(('Barrel', node.attrib['Ref']))
        blocks.append({'id': bid, 'catalog_id': block['catalog_id'],
                       'model': (target / 'model.json').relative_to(stage).as_posix(),
                       'images': (target / 'images.json').relative_to(stage).as_posix(),
                       'definition_status': 'present' if key else 'missing-definition',
                       'definition_sources': sorted(sources)})
    catalog_path = Path(workspace) / 'Projects/SS/Catalog/blocks.csv'
    catalog_ids = []
    if catalog_path.is_file():
        with catalog_path.open(encoding='utf-8-sig', newline='') as stream:
            catalog_ids = [row['ID'] for row in csv.DictReader(stream)]
    game_ids = {name for kind, name in index if kind in ('Block', 'ReactorBlock')}
    discovered = {read_json(p)['id'] for p in (root / 'Blocks').glob('*/assembly.json')}
    manifest = {'schema': 'SpriteBake.BlockPackage/1', 'quality': quality,
                'purpose': 'portable-block-export',
                'definition_sources_are_snapshots': True,
                'runtime_format': 'requires-game-import',
                'blocks': blocks,
                'coverage': {'models_without_definition': sorted(selected-game_ids),
                             'definitions_without_model': sorted(game_ids-selected),
                             'catalog_without_model': sorted(set(catalog_ids)-selected),
                             'assemblies_without_profile': sorted(discovered-set(profile['blocks']))}}
    manifest['files'] = package_inventory(stage)
    write_json(stage / 'package.json', manifest)
    verify_package(stage)
    for block in metadata:
        for name, expected_hash in block['inputs'].items():
            if digest(confined(root, name)) != expected_hash:
                raise RuntimeError('Source changed during package export: ' + block['id'])
    publish(stage, output / str(quality))
    return {'path': str(output / str(quality)), 'blocks': len(blocks), 'files': len(manifest['files']),
            'coverage': manifest['coverage']}
