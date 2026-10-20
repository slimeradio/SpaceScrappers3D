"""Local root viewer. Model and texture sources stay in their style directories."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

parser = argparse.ArgumentParser()
parser.add_argument('--port', type=int, default=8769)
parser.add_argument('--blender', help='Path to Blender executable (or set BLENDER_PATH)')
args = parser.parse_args()
root = Path(__file__).resolve().parent
SimpleHTTPRequestHandler.extensions_map.update({'.js': 'text/javascript', '.json': 'application/json', '.gltf': 'model/gltf+json'})
cache = Path(tempfile.gettempdir()) / 'SpaceScrappers3D-viewer-imports'
cache.mkdir(exist_ok=True)
conversion = threading.Semaphore(1)
military = root / 'Projects/SS/MilitaryArmor'

def live_catalog():
    data = json.loads((root / 'Viewer/catalog.json').read_text(encoding='utf-8'))
    data['blocks'] = [b for b in data['blocks'] if not b['id'].startswith('SS/MilitaryArmor/')]
    for path in sorted((military / 'Blocks').glob('*/assembly.json')):
        block = path.parent.name
        if not (path.parent / (block + '.blend')).is_file():
            continue
        a = json.loads(path.read_text(encoding='utf-8'))
        data['blocks'].append({'id': 'SS/MilitaryArmor/' + block, 'title': block + ' · ' + (a.get('title') or block),
            'project': 'SS', 'style': 'SS / MilitaryArmor', 'styleName': 'MilitaryArmor', 'blend': block,
            'textures': 'SharedTextures/Preview/catalog.json'})
    return data

def snapshot(source, target):
    executable = blender_path()
    if not executable:
        raise ValueError('Blender не найден. Укажите путь через --blender.')
    pending = target.with_name(uuid.uuid4().hex + '.pending.json')
    result = subprocess.run([executable, '--background', '--factory-startup', '--disable-autoexec',
        '--python', str(root / 'Viewer/blend_snapshot.py'), '--', str(source), str(pending)],
        capture_output=True, timeout=240, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    target.with_suffix('.log').write_bytes(result.stdout + result.stderr)
    if result.returncode or not pending.is_file():
        raise ValueError('Не удалось прочитать Blender-исходник. Подробности в журнале подготовки модели.')
    pending.replace(target)

def blender_path():
    candidates = [args.blender, os.environ.get('BLENDER_PATH'), shutil.which('blender'),
        r'D:\SteamLibrary\steamapps\common\Blender\blender.exe']
    for base in [Path(os.environ.get('PROGRAMFILES', r'C:\Program Files')) / 'Blender Foundation',
                 Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Blender Foundation']:
        if base.is_dir():
            candidates.extend(str(p) for p in sorted(base.glob('*/blender.exe'), reverse=True))
    return next((str(Path(p)) for p in candidates if p and Path(p).is_file()), None)

class ViewerHandler(SimpleHTTPRequestHandler):
    def application_file(self, route):
        if route != '/viewer.html' and not (route.startswith('/Viewer/') and route.count('/') == 2 and route.endswith('.js')):
            return False
        # Version the whole local module graph so already-open browsers cannot
        # combine an updated entry point with modules from an older viewer.
        modules = sorted((root / 'Viewer').glob('*.js'))
        names = {p.name for p in modules}
        revision = hashlib.sha256(b''.join(p.read_bytes() for p in modules)).hexdigest()[:16]
        if route == '/viewer.html':
            content = (root / 'viewer.html').read_text(encoding='utf-8').replace(
                'src="Viewer/viewer.js"', f'src="Viewer/viewer.js?rev={revision}"')
            mime = 'text/html; charset=utf-8'
        elif route.startswith('/Viewer/') and route.count('/') == 2 and route[8:] in names:
            content = (root / 'Viewer' / route[8:]).read_text(encoding='utf-8')
            content = re.sub(r"(['\"])(\./([^/'\"]+\.js))\1",
                lambda m: m[1] + m[2] + '?rev=' + revision + m[1] if m[3] in names else m[0], content)
            mime = 'text/javascript; charset=utf-8'
        else:
            return False
        payload = content.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(payload)
        return True

    def reply(self, status, value):
        data = json.dumps(value, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = urlsplit(self.path).path
        if self.application_file(route):
            return
        if route == '/api/catalog':
            self.reply(200, live_catalog())
            return
        blend = re.fullmatch(r'/api/blend/(MA-[A-Z]+[0-9]+)', route)
        if blend:
            try:
                folder = military / 'Blocks' / blend[1]
                source = folder / (blend[1] + '.blend')
                if not source.is_file():
                    self.reply(404, {'error': 'Blender-исходник блока не найден.'})
                    return
                digest = hashlib.sha256()
                for file in [source, folder / 'assembly.json', folder / 'state-authoring.json', root / 'Viewer/blend_snapshot.py']:
                    if file.is_file(): digest.update(file.read_bytes())
                key = digest.hexdigest()
                output = military / 'Exports/ViewerStates' / blend[1]
                output.mkdir(parents=True, exist_ok=True)
                target = output / 'scene.json'
                with conversion:
                    if not target.exists() or not (output / 'fingerprint.txt').exists() or (output / 'fingerprint.txt').read_text() != key:
                        snapshot(source, target)
                        (output / 'fingerprint.txt').write_text(key, encoding='utf-8')
                payload = target.read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(payload)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(payload)
            except (ValueError, OSError, subprocess.TimeoutExpired) as error:
                self.reply(400, {'error': str(error)})
            return
        match = re.fullmatch(r'/api/imports/([a-f0-9]{32})(/model\.(glb|json))?', route)
        if match:
            folder = cache / match[1]
            if not (folder / 'meta.json').is_file():
                self.reply(404, {'error': 'Импорт не найден. Откройте файл заново.'})
            elif match[2]:
                file = folder / ('model.' + match[3])
                if not file.is_file():
                    self.reply(404, {'error': 'Модель не найдена.'})
                    return
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8' if match[3] == 'json' else 'model/gltf-binary')
                self.send_header('Content-Length', str(file.stat().st_size))
                self.end_headers()
                with file.open('rb') as stream:
                    shutil.copyfileobj(stream, self.wfile)
            else:
                self.reply(200, json.loads((folder / 'meta.json').read_text(encoding='utf-8')))
            return
        super().do_GET()

    def do_POST(self):
        # Only the local viewer may initiate file conversion.
        origin = self.headers.get('Origin')
        if origin and origin != f'http://{self.headers.get("Host")}':
            self.reply(403, {'error': 'Открывайте файл из локального просмотрщика.'})
            return
        if urlsplit(self.path).path != '/api/import':
            self.reply(404, {'error': 'Неизвестная команда'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 512 * 1024 * 1024:
                raise ValueError('Выберите непустой GLB или blend размером до 512 МБ.')
            name = Path(unquote(self.headers.get('X-File-Name', 'model'))).name
            suffix = Path(name).suffix.lower()
            if suffix not in {'.glb', '.blend'}:
                raise ValueError('Поддерживаются файлы .glb и .blend.')
            executable = blender_path() if suffix == '.blend' else None
            if suffix == '.blend' and not executable:
                raise ValueError('Blender не найден. Запустите serve.ps1 --blender "путь к blender.exe".')
            if not conversion.acquire(blocking=False):
                self.reply(429, {'error': 'Другой файл ещё обрабатывается. Повторите открытие после завершения.'})
                return
            try:
                token = uuid.uuid4().hex
                folder = cache / token
                folder.mkdir()
                source = folder / ('source' + suffix)
                with source.open('wb') as stream:
                    remaining = length
                    while remaining:
                        chunk = self.rfile.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError('Передача файла прервана.')
                        stream.write(chunk)
                        remaining -= len(chunk)
                target = folder / ('model.glb' if suffix == '.glb' else 'model.json')
                if suffix == '.glb':
                    with source.open('rb') as stream:
                        if stream.read(4) != b'glTF':
                            raise ValueError('Файл не является GLB.')
                    source.replace(target)
                else:
                    known = military / 'Blocks' / Path(name).stem
                    known_source = known / (Path(name).stem + '.blend')
                    prepared = military / 'Exports/ViewerStates' / Path(name).stem
                    reused = False
                    if known_source.is_file() and (prepared / 'scene.json').is_file() and (prepared / 'fingerprint.txt').is_file():
                        uploaded_hash = hashlib.sha256(source.read_bytes()).digest()
                        if uploaded_hash == hashlib.sha256(known_source.read_bytes()).digest():
                            digest = hashlib.sha256()
                            for file in [known_source, known / 'assembly.json', known / 'state-authoring.json', root / 'Viewer/blend_snapshot.py']:
                                if file.is_file(): digest.update(file.read_bytes())
                            if (prepared / 'fingerprint.txt').read_text() == digest.hexdigest():
                                shutil.copyfile(prepared / 'scene.json', target)
                                reused = True
                    if not reused:
                        snapshot(source, target)
                metadata = {'id': token, 'name': name, 'format': suffix[1:],
                    'url': f'/api/imports/{token}/model.' + ('glb' if suffix == '.glb' else 'json'), 'scene': suffix == '.blend'}
                (folder / 'meta.json').write_text(json.dumps(metadata, ensure_ascii=False), encoding='utf-8')
                self.reply(200, metadata)
            finally:
                conversion.release()
        except subprocess.TimeoutExpired:
            self.reply(400, {'error': 'Blender не завершил преобразование за 4 минуты.'})
        except (ValueError, OSError) as error:
            self.reply(400, {'error': str(error)})

print(f'SpaceScrappers3D: http://127.0.0.1:{args.port}/viewer.html', flush=True)
ThreadingHTTPServer(('127.0.0.1', args.port), partial(ViewerHandler, directory=str(root))).serve_forever()
