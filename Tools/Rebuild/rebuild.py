"""Reconstruct authored resources in an isolated workspace, then publish approved outputs."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2).replace('\n', '\r\n') + '\r\n').encode())


def prepare(work, style):
    if work.exists():
        raise RuntimeError('Use a fresh --work directory; existing outputs are not proof of reconstruction')
    work.mkdir(parents=True)
    for base in [ROOT/'Projects/SS'/style, ROOT/'Projects/SS/Catalog']:
        for source in base.rglob('*'):
            if not source.is_file():
                continue
            rel = source.relative_to(ROOT)
            if any(p in {'__pycache__', 'Exports', 'Previews', 'SharedTexturesPreview', 'Revisions'} for p in rel.parts):
                continue
            if source.suffix.lower() not in {'.py', '.json', '.csv', '.md', '.txt', '.xml'}:
                continue
            dest = work/rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
    if style == 'CorporateHiTech':
        # These are generated parameter sources; prove generation without seeds.
        for pattern in ('Parts/*/part.json', 'Blocks/*/assembly.json'):
            for path in (work/'Projects/SS'/style).glob(pattern):
                path.unlink()
        shutil.copytree(ROOT/'Viewer', work/'Viewer', ignore=shutil.ignore_patterns('__pycache__'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--style', required=True, choices=['ChunkyModular', 'MilitaryArmor', 'CorporateHiTech'])
    p.add_argument('--blender', default=os.environ.get('BLENDER_PATH') or shutil.which('blender'))
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--resume', action='store_true')
    p.add_argument('--publish', action='store_true')
    args = p.parse_args()
    if not args.blender:
        p.error('Set BLENDER_PATH or pass --blender')
    work = args.work.resolve()
    if work == ROOT or ROOT in work.parents and '.generated' not in work.relative_to(ROOT).parts:
        p.error('Use .generated/<unique-name> or a separate temporary directory')
    config = json.loads((HERE/'recipes.json').read_text('utf-8'))[args.style]
    if not args.resume:
        prepare(work, args.style)
    logs = work/'logs'
    logs.mkdir(exist_ok=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
    temp = work/'temp'; temp.mkdir(exist_ok=True)
    env.update(TEMP=str(temp), TMP=str(temp))
    records = []
    for i, recipe in enumerate(config):
        script, *params = recipe
        result = logs/f'{i:03d}.json'
        if args.resume and result.exists() and json.loads(result.read_text('utf-8')).get('ok'):
            records.append(json.loads(result.read_text('utf-8')))
            continue
        print(f'[{i+1}/{len(config)}] {script}', flush=True)
        with (logs/f'{i:03d}.log').open('wb') as log:
            command = [args.blender, '--background', '--factory-startup', '--threads', '4',
                       '--python-exit-code', '1', '--python', str(HERE/'blender_runner.py'),
                       '--', str(work/script), str(result), *params]
            if args.style == 'CorporateHiTech':
                command = [sys.executable, str(work/script), *params]
            try:
                process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                         cwd=work, env=env, timeout=600)
                code = process.returncode
            except subprocess.TimeoutExpired:
                code = -1
        record = json.loads(result.read_text('utf-8')) if result.exists() else {'recipe': script, 'ok': False}
        if args.style == 'CorporateHiTech':
            record['ok'] = code == 0
            write_json(result, record)
        record['exit_code'] = code
        records.append(record)
        write_json(work/'build-report.json', records)
        print('  '+('OK' if record['ok'] and code == 0 else 'FAILED (see log)'), flush=True)
    outputs = [str(p.relative_to(work)).replace('\\', '/') for p in (work/'Projects').rglob('*.blend')]
    write_json(work/'generated-blends.json', outputs)
    if args.publish:
        approved = json.loads((HERE/'reproducible.json').read_text('utf-8'))
        for rel in approved.get(args.style, []):
            source = work/rel
            if not source.is_file():
                raise RuntimeError(f'Approved output missing: {rel}')
            dest = ROOT/rel
            if dest.exists():
                # .blend is a generated preview. Leave an existing local file;
                # a fresh --work directory is the reconstruction.
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
    print(f'Generated {len(outputs)} Blender sources. Report: {work / "build-report.json"}', flush=True)


if __name__ == '__main__':
    main()
