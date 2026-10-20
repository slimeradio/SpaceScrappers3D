"""No Blender/UI dependencies. All paths are confined to the selected style."""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

VERSION = '1.0.0'
ROLES = ('Color1', 'Color2', 'Emissive', 'Fixed')
MAPS = ('albedo', 'material-mask', 'emission', 'normal', 'height', 'surface')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    path.write_bytes(text.replace('\n', '\r\n').encode('utf-8'))


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', value) or value in ('.', '..'):
        raise ValueError('Invalid identifier: ' + repr(value))
    return value


def confined(root, relative, exists=True):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('Path escapes selected style: ' + str(relative))
    if exists and not path.is_file():
        raise FileNotFoundError(path)
    return path


def load_profile(workspace, project, style):
    root = Path(workspace) / 'Projects' / safe_name(project) / safe_name(style)
    root = root.resolve()
    profile_path = confined(root, 'SpriteBake/profile.json')
    profile = read_json(profile_path)
    if profile.get('schema') != 'SpriteBake.Profile/1':
        raise ValueError('Unsupported sprite bake profile schema')
    if not profile.get('blocks'):
        raise ValueError('Empty profile')
    if any(role not in ROLES for role in profile.get('material_roles', {}).values()):
        raise ValueError('Unknown material role')
    if not (1 <= profile.get('samples', 0) <= 256):
        raise ValueError('samples must be in 1..256')
    if profile.get('axes') != {'up': '+Z', 'forward': '-Y'}:
        raise ValueError('SpriteBake v1 requires +Z up, -Y forward')
    return root, profile_path, profile


def block_inputs(root, bid, spec):
    safe_name(bid)
    assembly_path = confined(root, spec['assembly'])
    assembly = read_json(assembly_path)
    if assembly['id'] != bid:
        raise ValueError('Assembly ID mismatch: ' + bid)
    source = confined(root, spec['source'])
    dependencies = {assembly_path, source}
    ids = set()
    for item in assembly['instances']:
        iid = item['id']
        if iid in ids:
            raise ValueError('Duplicate instance: ' + iid)
        ids.add(iid)
        path = confined(root, assembly_path.parent / item['source'])
        metadata_path = confined(root, path.parent / 'part.json')
        metadata = read_json(metadata_path)
        if metadata['id'] != item['part_id']:
            raise ValueError('Part ID mismatch: ' + str(path))
        dependencies.update((path, metadata_path))
    scale = spec['bu_per_cell']
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError('Invalid bu_per_cell: ' + bid)
    footprint = spec['footprint_bu']
    if len(footprint) != 4 or not all(math.isfinite(x) for x in footprint):
        raise ValueError('Invalid footprint: ' + bid)
    x0, y0, x1, y1 = footprint
    if x1 <= x0 or y1 <= y0:
        raise ValueError('Empty footprint: ' + bid)
    if any(abs(actual - expected) > 1e-5 for actual, expected in zip(((x1-x0)/scale, (y1-y0)/scale), assembly['catalog_grid'])):
        raise ValueError('Footprint differs from catalog grid: ' + bid)
    layers = spec['layers']
    if not layers or len({safe_name(x['id']) for x in layers}) != len(layers):
        raise ValueError('Invalid layers: ' + bid)
    membership = [iid for layer in layers for iid in layer['instances']]
    if set(membership) != ids or len(membership) != len(ids):
        raise ValueError('Every instance must occur in exactly one layer: ' + bid)
    states = spec['states']
    for state in ('damage0', 'damage33', 'damage66', 'destroyed'):
        if state not in states:
            raise ValueError('Missing state: ' + state)
    for state, value in states.items():
        safe_name(state)
        if 'alias' in value:
            if value['alias'] not in states or 'alias' in states[value['alias']]:
                raise ValueError('State aliases must point to a concrete state')
        elif 'frame' not in value:
            raise ValueError('State needs a frame or alias')
    for name, clip in spec.get('clips', {}).items():
        safe_name(name)
        if 'alias' in clip:
            if clip['alias'] not in states:
                raise ValueError('Unknown clip replacement')
        elif not clip.get('frames') or clip.get('fps', 0) <= 0:
            raise ValueError('Clip needs explicit frames and fps')
    return assembly_path, assembly, sorted(dependencies)


def catalog_entry(workspace, assembly):
    path = Path(workspace) / 'Projects' / 'SS' / 'Catalog' / 'blocks.csv'
    # Catalog access is the explicit shared-data exception for SS only.
    if not path.is_file():
        return {'id': assembly['catalog_id'], 'status': 'catalog unavailable'}
    with path.open(encoding='utf-8-sig', newline='') as stream:
        for row in csv.DictReader(stream):
            if next(iter(row.values())) == assembly['catalog_id']:
                grid = [int(row['Ширина_клеток']), int(row['Высота_клеток'])]
                if any(v < 1 or v > 99 for v in grid) or grid != assembly['catalog_grid']:
                    raise ValueError('Catalog grid mismatch: ' + assembly['catalog_id'])
                return {'id': assembly['catalog_id'], 'status': row.get('Статус', ''),
                        'grid': grid}
    raise ValueError('Unknown catalog ID: ' + assembly['catalog_id'])


def render_settings(profile, bid):
    settings = {k: v for k, v in profile.items() if k not in ('blocks', 'pilot')}
    settings['block'] = profile['blocks'][bid]
    return settings


def fingerprint(root, profile, bid, deps, quality, engine):
    # Only selected block settings and actual file dependencies affect its cache.
    settings = render_settings(profile, bid)
    inputs = {str(p.relative_to(root)).replace('\\', '/'): digest(p) for p in deps}
    payload = {'version': VERSION, 'settings': settings, 'inputs': inputs,
               'quality': quality, 'engine': engine,
               'tool': {p.name: digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(), inputs


def inventory(folder):
    return {p.relative_to(folder).as_posix(): digest(p) for p in sorted(Path(folder).rglob('*.png'))}


def cache_valid(folder, key):
    report_path = Path(folder) / 'Reports' / 'report.json'
    if not report_path.is_file():
        return False
    try:
        report = read_json(report_path)
        return report['fingerprint'] == key and bool(report['outputs']) and report['outputs'] == inventory(folder)
    except (ValueError, KeyError, OSError):
        return False


def publish(stage, target):
    """Same-volume rename, with restoration on failure; caller owns exclusive lock."""
    stage, target = Path(stage), Path(target)
    old = target.with_name(target.name + '.previous')
    if old.exists():
        raise RuntimeError('Interrupted publication requires recovery: ' + str(old))
    if target.exists():
        target.rename(old)
    try:
        stage.rename(target)
    except BaseException:
        if old.exists():
            old.rename(target)
        raise
    if old.exists():
        import shutil
        shutil.rmtree(old)
