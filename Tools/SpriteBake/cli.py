"""Sprite baking and explicit block export/Definition synchronization."""
import argparse
import contextlib
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from common import (VERSION, block_inputs, cache_valid, catalog_entry, fingerprint,
                    inventory, load_profile, publish, read_json, render_settings, write_json)

ROOT = Path(__file__).resolve().parents[2]


def find_blender(explicit):
    candidates = [explicit, os.environ.get('BLENDER_PATH'), shutil.which('blender'),
                  r'D:\SteamLibrary\steamapps\common\Blender\blender.exe']
    for base in (Path(os.environ.get('PROGRAMFILES', r'C:\Program Files')) / 'Blender Foundation',
                 Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Blender Foundation'):
        if base.is_dir():
            candidates += [str(p) for p in sorted(base.glob('*/blender.exe'), reverse=True)]
    for path in candidates:
        if path and Path(path).is_file():
            return str(Path(path).resolve())
    raise FileNotFoundError('Blender not found. Supply -BlenderPath or BLENDER_PATH.')


@contextlib.contextmanager
def exclusive(folder):
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / '.sprite-bake.lock'
    # OS byte lock is released even after a killed process; stale files are harmless.
    with lock.open('a+b') as stream:
        stream.seek(0)
        if not stream.read(1):
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError('Another SpriteBake command is running for this style') from exc
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def worker(blender, request, run, label):
    request_path = run / (label + '-request.json')
    response_path = run / (label + '-response.json')
    write_json(request_path, dict(request, response=str(response_path)))
    log = run / (label + '.log')
    with log.open('wb') as stream:
        result = subprocess.run([blender, '--background', '--factory-startup', '--disable-autoexec',
            '--threads', str(request['profile'].get('threads', 8)), '--python-exit-code', '1',
            '--python', str(Path(__file__).with_name('blender_worker.py')), '--', str(request_path)],
            stdout=stream, stderr=subprocess.STDOUT)
    if result.returncode or not response_path.is_file():
        raise RuntimeError('Blender failed. Log: ' + str(log))
    return read_json(response_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'validate', 'bake', 'preview', 'metadata', 'sync-definitions', 'export', 'verify-export'))
    parser.add_argument('--project', required=True)
    parser.add_argument('--style', required=True)
    parser.add_argument('--blocks', default='')
    parser.add_argument('--quality', choices=('128', '256', 'all'), default='all')
    parser.add_argument('--blender')
    parser.add_argument('--write-roles', action='store_true')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--game-root')
    parser.add_argument('--backup-root')
    args = parser.parse_args(argv)
    if args.write_roles and args.command != 'validate':
        parser.error('--write-roles is only allowed with validate')
    if args.command == 'sync-definitions' and (not args.game_root or not args.backup_root):
        parser.error('sync-definitions requires explicit --game-root and --backup-root')
    if args.command == 'export' and not args.game_root:
        parser.error('export requires explicit --game-root')
    root, profile_path, profile = load_profile(ROOT, args.project, args.style)
    if args.command == 'export' and not args.blocks:
        registered = {str((root / spec['assembly']).resolve()) for spec in profile['blocks'].values()}
        missing = [str(p) for p in (root / 'Blocks').glob('*/assembly.json') if str(p.resolve()) not in registered]
        if missing:
            raise ValueError('Unregistered assemblies; add explicit bake settings before full export: ' + ', '.join(missing))
    if args.command == 'verify-export':
        from block_package import verify_package
        qualities = (128, 256) if args.quality == 'all' else (int(args.quality),)
        for quality in qualities:
            print('VERIFIED', quality, json.dumps(verify_package(root / 'Exports/Packages' / str(quality))))
        return 0
    bids = args.blocks.split(',') if args.blocks else list(profile['blocks'])
    if len(bids) != len(set(bids)) or any(b not in profile['blocks'] for b in bids):
        raise ValueError('Unknown or duplicate blocks: ' + args.blocks)
    records = []
    for bid in bids:
        path, assembly, deps = block_inputs(root, bid, profile['blocks'][bid])
        catalog = catalog_entry(ROOT, assembly) if args.project == 'SS' else {'id': assembly['catalog_id']}
        records.append({'id': bid, 'assembly': str(path), 'dependencies': [str(p) for p in deps], 'catalog': catalog})
    if args.command == 'inspect':
        print(json.dumps({'version': VERSION, 'profile': str(profile_path), 'blocks': records}, ensure_ascii=False, indent=2))
        return 0
    blender = find_blender(args.blender)
    engine = subprocess.check_output([blender, '--version'], text=True).splitlines()[0]
    output = root / 'Exports' / 'Sprites'
    with exclusive(output):
        run = output / 'Diagnostics' / (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
        run.mkdir(parents=True)
        request = {'root': str(root), 'profile': profile, 'records': records, 'run': str(run),
                   'mode': 'validate', 'write_roles': args.write_roles}
        # Validate every selected dependency before constructing any dependent block.
        validation = worker(blender, request, run, 'validate')
        assets_by_part = {p['source']: p.get('external_assets', {}) for p in validation['parts']}
        for record in records:
            extra = set()
            for dependency in record['dependencies']:
                key = Path(dependency).relative_to(root).as_posix()
                extra.update(root/name for name in assets_by_part.get(key, {}))
            record['dependencies'] = sorted(set(record['dependencies']) | {str(p) for p in extra})
        print('VALIDATED', len(validation['parts']), 'parts;', len(records), 'blocks', flush=True)
        if args.command == 'validate':
            print('Report:', run / 'validate-response.json')
            return 0
        if args.command in ('metadata', 'sync-definitions', 'export'):
            result = worker(blender, dict(request, mode='metadata', write_roles=False), run, 'metadata')
            stage = output / ('.staging-metadata-' + uuid.uuid4().hex[:8])
            stage.mkdir()
            if args.blocks and (output / 'Metadata').is_dir():
                shutil.copytree(output / 'Metadata', stage, dirs_exist_ok=True)
            for block in result['blocks']:
                for name, expected in block['inputs'].items():
                    from common import digest
                    if digest(root / name) != expected:
                        raise RuntimeError('Inputs changed during metadata export: ' + block['id'])
                write_json(stage / (block['id'] + '.json'), block)
            publish(stage, output / 'Metadata')
            if args.command == 'sync-definitions':
                from definition_bridge import synchronize
                sync = synchronize(args.game_root, result['blocks'], args.backup_root)
                write_json(run / 'definition-sync.json', sync)
                print('XML_UPDATED', len(sync['changes']), 'files; backup:', sync['backup'])
            elif args.command == 'export':
                from block_package import export_package
                qualities = (128, 256) if args.quality == 'all' else (int(args.quality),)
                packages = [export_package(ROOT, root, profile, result['blocks'], args.game_root, quality)
                            for quality in qualities]
                write_json(run / 'packages.json', packages)
                for package in packages:
                    print('EXPORTED', package['blocks'], 'blocks ->', package['path'])
            print('Report:', run / 'metadata-response.json')
            return 0
        from preview import build_preview, compare_qualities, verify_images
        qualities = (128, 256) if args.quality == 'all' else (int(args.quality),)
        results = []
        for record in records:
            bid = record['id']
            deps = [Path(p) for p in record['dependencies']]
            for quality in qualities:
                key, hashes = fingerprint(root, profile, bid, deps, quality, engine)
                target = output / str(quality) / bid
                if args.command == 'preview':
                    report_file = target / 'Reports/report.json'
                    report = read_json(report_file)
                    png_inventory = {k: v for k, v in inventory(target).items() if k.startswith('PNG/')}
                    expected = {k: v for k, v in report['outputs'].items() if k.startswith('PNG/')}
                    if report['fingerprint'] != key or not expected or png_inventory != expected:
                        raise RuntimeError('Missing or stale bake; run bake first: ' + bid)
                    stage = target.with_name('.staging-preview-' + bid + '-' + uuid.uuid4().hex[:8])
                    shutil.copytree(target, stage)
                    verify_images(stage, report)
                    build_preview(stage, report)
                    report['outputs'] = inventory(stage)
                    write_json(stage / 'Reports/report.json', report)
                    publish(stage, target)
                    print('PREVIEW', bid, quality, flush=True)
                    results.append({'id': bid, 'quality': quality, 'status': 'preview'})
                    continue
                if not args.force and cache_valid(target, key):
                    print('CACHED', bid, quality, flush=True)
                    results.append({'id': bid, 'quality': quality, 'status': 'cached'})
                    continue
                stage = output / str(quality) / ('.staging-' + bid + '-' + uuid.uuid4().hex[:8])
                stage.mkdir(parents=True)
                result = worker(blender, dict(request, mode='bake', write_roles=False,
                    records=[record], quality=quality, output=str(stage)), run, bid + '-' + str(quality))
                result.update(fingerprint=key, inputs=hashes, blender=engine, version=VERSION,
                              catalog=record['catalog'], source_geometry_changed=False,
                              render_settings=render_settings(profile, bid))
                verify_images(stage, result)
                build_preview(stage, result)
                # Source edits during a long render invalidate the result, never publish it.
                after, _ = fingerprint(root, profile, bid, deps, quality, engine)
                if after != key:
                    raise RuntimeError('Inputs changed during bake: ' + bid)
                result['outputs'] = inventory(stage)
                write_json(stage / 'Reports' / 'report.json', result)
                publish(stage, target)
                print('BAKED', bid, quality, '->', target, flush=True)
                results.append({'id': bid, 'quality': quality, 'status': 'baked'})
            compare_qualities(output, bid)
        write_json(run / 'summary.json', {'results': results, 'validation': validation})
        print('Report:', run / 'summary.json')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('ERROR:', error, file=sys.stderr)
        sys.exit(1)
